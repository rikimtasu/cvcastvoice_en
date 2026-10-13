#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hand-decode raw words around the save-slot descriptor references to remove all
capstone linear-sweep ambiguity. We print raw hex + manual field extraction for
opcode, rt/dst, ra/src, and immediate at each site found in _ctx.txt.
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

EXEC_OFF, EXEC_ADDR = 0x230, 0x10230
SITES = [0x4c538, 0x4c540, 0x4c544, 0x4c548,
         0x4c578, 0x4c580, 0x4c5b8, 0x4c5c0, 0x4c5f8, 0x4c600,
         0x19ede4, 0x19ede8, 0x19ee3c, 0x19ee40]


def decode(w):
    opc = w >> 26
    rt = (w >> 21) & 0x1f
    ra = (w >> 16) & 0x1f
    imm = w & 0xffff
    simm = imm - 0x10000 if imm >= 0x8000 else imm
    names = {14: "addi", 15: "addis/lis", 13: "addic", 24: "ori", 25: "oris",
             32: "lwz", 34: "lbz", 36: "stw", 37: "stwu", 38: "stb",
             12: "addic.", 7: "mulli", 11: "cmpwi", 10: "cmpli", 24: "ori"}
    mn = names.get(opc, "opc%d" % opc)
    return mn, opc, rt, ra, imm, simm


def main():
    img = Image(ELF)
    d = img.d
    print("addr      raw      mnem      rt ra  imm     simm    note")
    for va in SITES:
        off = EXEC_OFF + (va - EXEC_ADDR)
        w = struct.unpack_from(">I", d, off)[0]
        mn, opc, rt, ra, imm, simm = decode(w)
        note = ""
        # if this is a completion from a 0x24 base:
        if mn in ("addic", "addi", "ori", "oris"):
            resolved = (0x240000 + simm) & 0xffffffff
            note = "base0x24+simm=0x%x" % resolved
            resolved2 = (0x240000 + imm) & 0xffffffff
            note += " | +imm=0x%x" % resolved2
        print("0x%08x %08x  %-8s  r%d r%d 0x%04x %6d  %s"
              % (va, w, mn, rt, ra, imm, simm, note))


if __name__ == "__main__":
    main()
