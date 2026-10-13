#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find all computed-jump (bctr) dispatch sites and resolve their jump tables.

A serializer's type->tag dispatch is usually a switch compiled to a jump table:
    extsh/extsw rX, <index>
    slwi rX, rX, 2
    <load table base into rY via lis/addis/addi>
    lwzx rX, rY, rX        ; rX = table[index]
    mtctr rX
    bctr
We scan raw words for 'mtctr rX' (opcode 31, XO=278) then find the preceding
lwzx/ldx that loaded rX from a base+index, resolve the base address, and dump the
table entries as candidate handler vaddrs.
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

EXEC_OFF, EXEC_ADDR, EXEC_SIZE = 0x230, 0x10230, 0x22a714


def fields(w):
    opc = w >> 26
    rt = (w >> 21) & 0x1f      # destination / source for loads
    ra = (w >> 16) & 0x1f
    rb = (w >> 11) & 0x1f
    xo = (w >> 1) & 0x3ff
    imm = w & 0xffff
    return opc, rt, ra, rb, xo, imm


def main():
    img = Image(ELF)
    d = img.d
    code = d[EXEC_OFF:EXEC_OFF + EXEC_SIZE]
    n = len(code) // 4
    words = struct.unpack_from(">%dI" % n, code, 0)

    # pass 1: find mtctr (opcode 31, xo 278) with target reg = rb field
    # opcode31: rt=0? mtctr rS: XO-form uses RS field (bits 6-10). Actually
    # mtctr rS => 31 << 26 | RS << 21 | 0 << 16 | 0 << 11 | 278 << 1 | 0
    bctr_sites = []
    for i in range(n):
        w = words[i]
        opc, rt, ra, rb, xo, imm = fields(w)
        if opc == 31 and xo == 278:  # mtctr
            reg = rt  # RS field
            addr = EXEC_ADDR + i * 4
            # scan backward up to 12 insns for the lwzx/ldx that set 'reg'
            # lwzx: opcode31 xo=23  rt,ra,rb ; ldx: xo=21
            tbl_base = None
            for j in range(i - 1, max(0, i - 14), -1):
                w2 = words[j]
                o2, rt2, ra2, rb2, xo2, imm2 = fields(w2)
                if o2 == 31 and xo2 in (23, 21) and rt2 == reg:
                    # rt2 = [ra2 + rb2]; find base set in ra2 via lis/addis
                    base = None
                    for k in range(j - 1, max(0, j - 8), -1):
                        w3 = words[k]
                        o3, rt3, ra3, rb3, xo3, imm3 = fields(w3)
                        if o3 == 15 and ra3 == 0 and rt3 == ra2:  # lis/addis into ra2
                            base = (imm3 << 16) & 0xffffffff
                            break
                        if o3 == 14 and rt3 == ra2:  # addi completing a base
                            # need preceding lis into ra3
                            for m in range(k - 1, max(0, k - 6), -1):
                                w4 = words[m]
                                o4, rt4, ra4, rb4, xo4, imm4 = fields(w4)
                                if o4 == 15 and ra4 == 0 and rt4 == ra3:
                                    s = imm3 - 0x10000 if imm3 >= 0x8000 else imm3
                                    base = ((imm4 << 16) + s) & 0xffffffff
                                    break
                            if base is not None:
                                break
                    if base is not None:
                        tbl_base = base
                        break
            bctr_sites.append((addr, reg, tbl_base))

    print("computed-jump (bctr) sites:", len(bctr_sites))
    with_base = [s for s in bctr_sites if s[2] is not None]
    print("with resolved table base:", len(with_base))
    for addr, reg, base in with_base[:60]:
        print("  mtctr r%d @0x%08x  table@0x%08x" % (reg, addr, base))


if __name__ == "__main__":
    main()
