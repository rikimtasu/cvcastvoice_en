#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump raw context around every instruction whose immediate == 0x2a14 / 0x2a24
(the referenced GAMEDATA / OPTION low halves). Shows the real addressing pattern.
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

EXEC_OFF, EXEC_ADDR, EXEC_SIZE = 0x230, 0x10230, 0x22a714
WANT = {0x2a14, 0x2a24, 0x2a2c, 0x2a3c, 0x29a4}


def main():
    img = Image(ELF)
    code = img.d[EXEC_OFF:EXEC_OFF + EXEC_SIZE]
    insns = list(img.md.disasm(code, EXEC_ADDR))
    print("decoded:", len(insns))
    for i, ins in enumerate(insns):
        # crude: does op_str contain the hex immediate?
        ops = ins.op_str
        hit = False
        for w in WANT:
            if ("0x%x" % w) in ops or ("0x%X" % w) in ops:
                hit = True
                break
        if not hit:
            continue
        print("\n---- @0x%08x: %s %s ----" % (ins.address, ins.mnemonic, ops))
        for j in range(max(0, i - 6), min(len(insns), i + 5)):
            mark = ">>" if j == i else "  "
            print("  %s 0x%08x  %-7s %s" % (mark, insns[j].address,
                  insns[j].mnemonic, insns[j].op_str))


if __name__ == "__main__":
    main()
