#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""For each rank/trust key vaddr, determine HOW it is referenced:
1. Is its lo16 present as any ori/addi/addic/addis immediate in code? (absolute)
2. Does a u32 pointer to the vaddr exist anywhere in the file? (pointer table)
3. If pointer table found: which data array, and who xrefs that array?
Prints definitive per-key answer.
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

EXEC_OFF, EXEC_ADDR, EXEC_SIZE = 0x230, 0x10230, 0x22a714

TARGETS = {
    0x240098: "rankup",
    0x2400a0: "prank",
    0x2400a8: "rank",
    0x240238: "rankon",
    0x23d940: "shinrai1",
    0x23d5f4: "scenario_key",
    0x23d604: "character_key",
}


def main():
    img = Image(ELF)
    d = img.d
    code = d[EXEC_OFF:EXEC_OFF + EXEC_SIZE]
    n = len(code) // 4
    words = struct.unpack_from(">%dI" % n, code, 0)

    # set of all 16-bit immediates used by ori/addi/addic/addis
    imms = set()
    imms_by_opc = {}
    for w in words:
        opc = w >> 26
        if opc in (13, 14, 15, 24, 25):
            imms.add(w & 0xffff)
            imms_by_opc.setdefault(opc, set()).add(w & 0xffff)

    print("== per-key reference check ==")
    for V, name in sorted(TARGETS.items()):
        lo = V & 0xffff
        hi = V >> 16
        in_imm = lo in imms
        # pointer scan (whole file)
        b4 = struct.pack(">I", V)
        ptr_offs = []
        i = d.find(b4)
        while i >= 0:
            ptr_offs.append(i)
            i = d.find(b4, i + 1)
        print("\n  %-16s vaddr=0x%06x lo=0x%04x" % (name, V, lo))
        print("     lo as code imm: %s" % ("YES" if in_imm else "no"))
        print("     u32 ptrs in file: %s" % ([hex(x) for x in ptr_offs] or "none"))

    # also: search for addis (opc15) with imm==hi targeting ANY reg (TOC style)
    print("\n== addis/lis with imm == each target hi ==")
    for V, name in sorted(TARGETS.items()):
        hi = V >> 16
        cnt = sum(1 for w in words
                  if (w >> 26) == 15 and (w & 0xffff) == hi)
        cnt_signed = sum(1 for w in words
                         if (w >> 26) == 15 and ((w & 0xffff) == ((V + 0x8000) >> 16)))
        print("  %-16s lis hi=0x%02x sites=%d   (signed-hi 0x%02x sites=%d)"
              % (name, hi, cnt, (V + 0x8000) >> 16, cnt_signed))


if __name__ == "__main__":
    main()
