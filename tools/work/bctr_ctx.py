#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump context before each bctr to learn the actual switch/dispatch pattern.
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

EXEC_OFF, EXEC_ADDR, EXEC_SIZE = 0x230, 0x10230, 0x22a714


def fields(w):
    return (w >> 26, (w >> 21) & 0x1f, (w >> 16) & 0x1f, (w >> 11) & 0x1f,
            (w >> 1) & 0x3ff, w & 0xffff)


def main():
    img = Image(ELF)
    d = img.d
    code = d[EXEC_OFF:EXEC_OFF + EXEC_SIZE]
    n = len(code) // 4
    words = struct.unpack_from(">%dI" % n, code, 0)
    insns = list(img.md.disasm(code, EXEC_ADDR))
    addr2i = {ins.address: i for i, ins in enumerate(insns)}

    # find bctr (opcode19 xo=528) OR bctrl(19 xo=528 too) -> both bctr form
    for i in range(n):
        w = words[i]
        opc, rt, ra, rb, xo, imm = fields(w)
        if opc == 19 and xo == 528:  # bctr
            addr = EXEC_ADDR + i * 4
            k = addr2i.get(addr)
            print("\n---- bctr @0x%08x ----" % addr)
            if k is None:
                # dump raw backward
                lo = max(0, i - 14)
                for j in range(lo, i + 1):
                    a = EXEC_ADDR + j * 4
                    ins = next(iter(img.md.disasm(d[EXEC_OFF + j * 4:EXEC_OFF + j * 4 + 4], a)), None)
                    mn = ins.mnemonic if ins else "?"
                    op = ins.op_str if ins else ""
                    mark = ">>" if j == i else "  "
                    print("  %s 0x%08x  %-8s %s" % (mark, a, mn, op))
            else:
                for j in range(max(0, k - 14), k + 1):
                    mark = ">>" if j == k else "  "
                    print("  %s 0x%08x  %-8s %s" % (mark, insns[j].address,
                          insns[j].mnemonic, insns[j].op_str))


if __name__ == "__main__":
    main()
