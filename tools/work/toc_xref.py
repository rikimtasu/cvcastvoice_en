#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TOC-relative XREF with known TOC=0x2e97d8.

Pattern: addis rX, r2, (A-TOC)@ha ; addi/ori rY, rX, (A-TOC)@l
=> A = TOC + ((hi<<16) + s16(lo))
Find all sites materializing each target A; report enclosing functions.
Targets: rank table slots, trust table, key strings, serializer keys.
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

EXEC_OFF, EXEC_ADDR, EXEC_SIZE = 0x230, 0x10230, 0x22a714
TOC = 0x2e97d8

TARGETS = {
    0x2f2380: "rank_field_tbl",
    0x2f2384: "rankup_slot",
    0x2f2394: "prank_slot",
    0x2f2398: "rank_slot",
    0x2f2360: "tbl_region_a",
    0x2e1f14: "trust_reward_tbl",
    0x23d940: "shinrai_str1",
    0x240098: "rankup_str",
    0x2400a0: "prank_str",
    0x2400a8: "rank_str",
    0x2f2300: "tbl_base_2300",
}


def s16(x):
    return x - 0x10000 if x >= 0x8000 else x


def main():
    img = Image(ELF)
    d = img.d
    code = d[EXEC_OFF:EXEC_OFF + EXEC_SIZE]
    n = len(code) // 4
    words = struct.unpack_from(">%dI" % n, code, 0)
    insns = list(img.md.disasm(code, EXEC_ADDR))
    addr2i = {ins.address: i for i, ins in enumerate(insns)}

    # addis with base r2 (opc15, ra==2), per dst reg
    addis_r2 = {}
    for i, w in enumerate(words):
        if (w >> 26) == 15 and ((w >> 16) & 0x1f) == 2:
            addis_r2.setdefault((i, (w >> 21) & 0x1f), w & 0xffff)

    # build per-dst list
    per_dst = {}
    for (i, dst), hi in addis_r2.items():
        per_dst.setdefault(dst, []).append((i, hi))

    hits = []
    for i, w in enumerate(words):
        opc = w >> 26
        if opc not in (13, 14, 24, 25):
            continue
        ra = (w >> 16) & 0x1f
        imm = w & 0xffff
        for (li, hi) in per_dst.get(ra, ()):
            if not (0 <= i - li <= 25):
                continue
            A = (TOC + ((hi << 16) + s16(imm))) & 0xffffffff
            A2 = (TOC + ((hi << 16) + imm)) & 0xffffffff
            for T, nm in TARGETS.items():
                if A == T or A2 == T:
                    k = addr2i.get(EXEC_ADDR + i * 4)
                    f = None
                    if k is not None:
                        s = k
                        while s > 0 and insns[s].mnemonic not in ("stdu", "mflr"):
                            s -= 1
                        f = insns[s].address
                    hits.append((nm, T, EXEC_ADDR + li * 4, EXEC_ADDR + i * 4, f))
                    break
            else:
                continue
            break

    print("== TOC-relative XREFs ==")
    if not hits:
        print("  none")
    for nm, T, la, aa, f in sorted(hits, key=lambda x: x[3]):
        print("  %-16s(0x%06x) addis@0x%08x add@0x%08x  func=%s"
              % (nm, T, la, aa, ("0x%x" % f) if f else "?"))


if __name__ == "__main__":
    main()
