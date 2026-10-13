#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Exhaustive pointer search + TOC-base discovery.

(1) Scan the ENTIRE file (every byte offset, not just program segments) for any
    u32 BE or u64 BE equal to a target string vaddr. Catches pointers living in
    section-header area, relocation pools, or tables my segment scan skipped.

(2) Find how r2 (the PPC64 TOC / small-data base) is established. For ELF PPC64,
    string refs are often 'addis rX,r2,sym@ha ; addi rX,rX,sym@l' where the imm
    is relative to r2. If we learn r2's base we can resolve them.
"""
import struct
import sys
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

EXEC_OFF, EXEC_ADDR, EXEC_SIZE = 0x230, 0x10230, 0x22a714


def scan_all_pointers(d, targets):
    print("== exhaustive whole-file pointer scan ==")
    total = 0
    for label, V in targets.items():
        if V is None:
            continue
        b4 = struct.pack(">I", V)
        b8 = struct.pack(">Q", V)
        # u32
        i = d.find(b4)
        u32_hits = []
        while i >= 0:
            u32_hits.append(i)
            i = d.find(b4, i + 1)
        # u64
        i = d.find(b8)
        u64_hits = []
        while i >= 0:
            u64_hits.append(i)
            i = d.find(b8, i + 1)
        print("  %-14s V=0x%x : u32 ptrs=%d %s | u64 ptrs=%d %s"
              % (label, V, len(u32_hits), [hex(x) for x in u32_hits[:8]],
                 len(u64_hits), [hex(x) for x in u64_hits[:8]]))
        total += len(u32_hits) + len(u64_hits)
    print("  total:", total)


def find_r2_setup(img):
    print("\n== r2 (TOC base) setup near entry ==")
    d = img.d
    code = d[EXEC_OFF:EXEC_OFF + 0x400]
    for ins in img.md.disasm(code, EXEC_ADDR):
        # addis r2, rX, imm  or  lis r2, imm  or  ld r2, off(rX)
        if "r2" in ins.op_str and ins.mnemonic in ("addis", "lis", "ld", "lwz", "addi", "ori"):
            print("  0x%08x: %-6s %s" % (ins.address, ins.mnemonic, ins.op_str))

    # Histogram: which registers are addis bases with SMALL immediates (@ha relocs)?
    code = d[EXEC_OFF:EXEC_OFF + EXEC_SIZE]
    n = len(code) // 4
    words = struct.unpack_from(">%dI" % n, code, 0)
    base_hist = Counter()
    for i, w in enumerate(words):
        opc = w >> 26
        if opc == 15:  # addi/lis
            ra = (w >> 16) & 0x1f
            if ra != 0:
                base_hist["r%d" % ra] += 1
    print("  addis-with-base histogram (top):", base_hist.most_common(8))


def main():
    img = Image(ELF)
    d = img.d
    targets = {
        "GAMEDATA": img.find_string("GAMEDATA"),
        "CASTDATA.DAT": img.find_string("CASTDATA.DAT"),
        "%s-GAMEDATA-": img.find_string("%s-GAMEDATA-"),
        "rank": img.find_string("rank"),
    }
    for k, v in targets.items():
        print("%-14s = 0x%x" % (k, v if v else -1))
    scan_all_pointers(d, targets)
    find_r2_setup(img)


if __name__ == "__main__":
    main()
