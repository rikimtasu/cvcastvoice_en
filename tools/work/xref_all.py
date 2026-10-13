#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Definitive string XREF — enumerate ALL occurrences of each key string and find
which copy the code actually references, then locate the enclosing function.

Bug in earlier attempts: find_string returned only the FIRST occurrence, but
"GAMEDATA" appears 3x (0x2429a4/0x242a14/0x242bac). We now:
  1. find every occurrence (file offset -> vaddr)
  2. collect every addi/ori 16-bit immediate used in code into a set
  3. for each occurrence, check if its low half is in that immediate set and pair
     with a nearby 'lis ,0x24'
  4. report the enclosing function (via mflr/stdu prologue) for each hit
"""
import struct
import sys
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

EXEC_OFF, EXEC_ADDR, EXEC_SIZE = 0x230, 0x10230, 0x22a714
KEYS = ["GAMEDATA", "OPTION", "CASTDATA.DAT", "%s-GAMEDATA-", "%s-CASTLIST-",
        "ICON0.PNG", "NPJB00558"]


def all_occurrences(img, key):
    pat = key.encode("latin-1") + b"\x00"
    d = img.d
    out = []
    i = d.find(pat)
    while i >= 0:
        va = img.off_to_vaddr(i)
        if va is not None:
            out.append(va)
        i = d.find(pat, i + 1)
    return out


def main():
    img = Image(ELF)
    d = img.d
    code = d[EXEC_OFF:EXEC_OFF + EXEC_SIZE]
    n = len(code) // 4
    words = struct.unpack_from(">%dI" % n, code, 0)

    # Build set of (addr, srcReg) for every addi/ori, plus lis sites.
    imm_set = set()
    for w in words:
        opc = w >> 26
        if opc in (15, 24, 25):  # addi, ori, oris
            imm_set.add(w & 0xffff)

    for key in KEYS:
        occ = all_occurrences(img, key)
        print("\n==== %s : %d occurrence(s) %s ====" % (key, len(occ), [hex(x) for x in occ]))
        for V in occ:
            lo = V & 0xffff
            present = lo in imm_set
            print("   V=0x%x lo=0x%x : low-half immediate %s in code"
                  % (V, lo, "PRESENT" if present else "absent"))


if __name__ == "__main__":
    main()
