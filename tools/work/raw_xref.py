#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Foolproof raw-encoding XREF + save-string vocabulary dump.

Instead of trusting capstone mnemonics, search raw code bytes for the exact PPC
instruction encodings:
  lis  rX, imm   == addis rX, r0, imm : 0x3C00_0000 | (X<<21) | imm
  addi rY, rX, d : 0x3800_0000 | (Y<<21) | (X<<16) | (d & 0xFFFF)
  ori  rY, rX, d : 0x6000_0000 | (Y<<21) | (X<<16) | (d & 0xFFFF)

We find every 'lis ,0x24' and every 'addi/ori ,0x29a4' (GAMEDATA low half) and
report co-located pairs. Also dump the string blob around GAMEDATA to reveal the
save-path / filename vocabulary.
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

EXEC_ADDR = 0x10230
EXEC_OFF = 0x230
EXEC_SIZE = 0x22a714


def find_all(hay, needle):
    out = []
    i = hay.find(needle)
    while i >= 0:
        out.append(i)
        i = hay.find(needle, i + 1)
    return out


def dump_blob(img, lo, hi):
    off = img.vaddr_to_off(lo)
    raw = img.d[off:off + (hi - lo)]
    va = lo
    print("== string blob 0x%x-0x%x ==" % (lo, hi))
    while va < hi and b"\x00" in raw:
        n = raw.index(b"\x00")
        chunk = raw[:n]
        if chunk:
            try:
                s = chunk.decode("shift_jis")
            except Exception:
                s = repr(chunk)
            if len(chunk) <= 48:
                print("  0x%08x: %r" % (va, s))
        raw = raw[n + 1:]
        va += n + 1


def raw_xref(d, hi, lo, label):
    code = d[EXEC_OFF:EXEC_OFF + EXEC_SIZE]
    base = EXEC_ADDR
    n = len(code) // 4
    words = struct.unpack_from(">%dI" % n, code, 0)
    lis_sites = []
    add_sites = []  # (addr, srcReg) for addi OR ori with imm==lo
    for i, w in enumerate(words):
        opc = w >> 26
        addr = base + i * 4
        if opc == 15:  # addi / lis
            ra = (w >> 16) & 0x1f
            imm = w & 0xffff
            dst = (w >> 21) & 0x1f
            if ra == 0 and imm == hi:
                lis_sites.append((addr, dst))
            if imm == lo:
                add_sites.append((addr, ra))
        elif opc == 24:  # ori (nop-safe); also ori rX,rX,lo completes address
            ra = (w >> 16) & 0x1f
            imm = w & 0xffff
            if imm == lo:
                add_sites.append((addr, ra))
    print("\n== raw XREF %s (hi=0x%x lo=0x%x) ==" % (label, hi, lo))
    print("  lis/addis imm==hi sites:", len(lis_sites))
    print("  addi/ori imm==lo sites:", len(add_sites))
    pairs = []
    for la, ldst in lis_sites:
        for aa, ara in add_sites:
            if 0 < aa - la <= 40 and ara == ldst:
                pairs.append((la, ldst, aa))
                break
    print("  PAIRS (lis rX,hi ; addi/ori r?,rX,lo):", len(pairs))
    for la, ldst, aa in pairs[:24]:
        print("    lis r%d,0x%x @0x%08x  ->  addi/ori r?,r%d,0x%x @0x%08x"
              % (ldst, hi, la, ldst, lo, aa))


def main():
    img = Image(ELF)
    d = img.d
    gd = img.find_string("GAMEDATA")
    cd = img.find_string("CASTDATA.DAT")
    print("GAMEDATA=0x%x  CASTDATA.DAT=0x%x" % (gd, cd))

    dump_blob(img, 0x242900, 0x242c00)
    raw_xref(d, gd >> 16, gd & 0xffff, "GAMEDATA")
    raw_xref(d, cd >> 16, cd & 0xffff, "CASTDATA.DAT")


if __name__ == "__main__":
    main()
