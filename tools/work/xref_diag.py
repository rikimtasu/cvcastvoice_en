#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sanity-check the raw-word XREF scanner and detect addressing mode.

1) Confirm the scanner materializes addresses in the string range at all
   (print a histogram of hi16 values seen in 'lis' and any addi completions
   landing in 0x230000..0x280000).
2) Detect TOC-relative refs: count 'addi rD, r2, simm' (opcode 14, A==2) which
   is the classic PPC64 ELF way to reach .rodata/.data via the TOC.
3) Dump the TOC if present (section type 8 = SHT_NOBYITS? actually .toc is
   PROGBITS). We look for a pointer table whose entries point at our strings.
"""
import struct
from collections import Counter

from ppc_disasm import Image, ELF


def main():
    img = Image(ELF)
    # locate a few strings
    gd = img.find_string("GAMEDATA")
    print("GAMEDATA vaddr: 0x%x" % gd)

    seg = max(img.segs, key=lambda s: s[2])
    vaddr0, off0, size0, _ = seg
    skip = 0x200 if off0 == 0 else 0
    base_off = off0 + skip
    base_v = vaddr0 + skip
    nwords = (size0 - skip) // 4
    words = struct.unpack(">%dI" % nwords, img.d[base_off:base_off + nwords * 4])

    # 1. histogram of 'lis' immediates (opcode 15, A==0)
    lis_imm = Counter()
    addi_r2 = 0
    completions_in_strrange = 0
    hi = {}
    for i in range(nwords):
        w = words[i]
        op = w >> 26
        if op == 15:
            D = (w >> 21) & 31
            A = (w >> 16) & 31
            imm = w & 0xFFFF
            if A == 0:
                hi[D] = (imm << 16) & 0xFFFFFFFF
                lis_imm[imm] += 1
            elif A in hi:
                hi[D] = (hi[A] + ((imm << 16) & 0xFFFFFFFF)) & 0xFFFFFFFF
        elif op == 14:
            D = (w >> 21) & 31
            A = (w >> 16) & 31
            simm = w & 0xFFFF
            if simm & 0x8000:
                simm -= 0x10000
            if A == 2:
                addi_r2 += 1
            if A in hi:
                addr = (hi[A] + simm) & 0xFFFFFFFF
                if 0x230000 <= addr < 0x280000:
                    completions_in_strrange += 1
        elif op == 24:
            D = (w >> 21) & 31
            A = (w >> 16) & 31
            if A in hi:
                addr = (hi[A] | (w & 0xFFFF)) & 0xFFFFFFFF
                if 0x230000 <= addr < 0x280000:
                    completions_in_strrange += 1
        if len(hi) > 40:
            hi.clear()

    print("\ntop 'lis' immediates (hi16):")
    for imm, c in lis_imm.most_common(15):
        print("  0x%04x -> base 0x%04x0000  x%d" % (imm, imm, c))
    print("\naddi rD,r2,simm (TOC-relative) count:", addi_r2)
    print("addi/ori completions landing in 0x230000-0x280000:",
          completions_in_strrange)

    # Is 0x24 (hi for 0x24xxxx strings) among the lis imms?
    print("\n0x0024 present in lis imms:", 0x24 in lis_imm, " count:",
          lis_imm.get(0x24, 0))
    print("0x0023 present:", 0x23 in lis_imm, " count:", lis_imm.get(0x23, 0))


if __name__ == "__main__":
    main()
