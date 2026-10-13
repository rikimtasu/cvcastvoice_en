#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find the actual tag-writing sites: 'stb rX, disp(reg)' where rX was just set to
0xff / 0x01 / 0x00 via 'li rX, imm'. Group by enclosing function. The function(s)
that write 0xff (bool-true) and 0x01 (int tag) into the output buffer ARE the
serializer core. Then dump those functions fully with call annotation.
"""
import struct
import sys
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

EXEC_OFF, EXEC_ADDR, EXEC_SIZE = 0x230, 0x10230, 0x22a714


def fields(w):
    return (w >> 26, (w >> 21) & 0x1f, (w >> 16) & 0x1f, (w >> 11) & 0x1f, w & 0xffff)


def main():
    img = Image(ELF)
    d = img.d
    code = d[EXEC_OFF:EXEC_OFF + EXEC_SIZE]
    n = len(code) // 4
    words = struct.unpack_from(">%dI" % n, code, 0)
    insns = list(img.md.disasm(code, EXEC_ADDR))
    addr2i = {ins.address: i for i, ins in enumerate(insns)}

    # track last 'li rX, imm' (addi rX,r0,imm opcode14 ra=0) per reg in a window
    tagval = {}  # reg -> (imm, idx)
    # results: func -> counts of stb of 0xff / 0x01 / 0x00
    func_counts = defaultdict(lambda: [0, 0, 0])
    func_example = {}
    for i in range(n):
        w = words[i]
        opc, rt, ra, rb, imm = fields(w)
        # expire
        for r in list(tagval):
            if i - tagval[r][1] > 8:
                del tagval[r]
        if opc == 14 and ra == 0:  # addi rX, r0, imm  (li)
            tagval[rt] = (imm, i)
        elif opc == 38:  # stb rt, disp(ra)
            if rt in tagval:
                v = tagval[rt][0]
                if v in (0xff, 0x01, 0x00):
                    addr = EXEC_ADDR + i * 4
                    k = addr2i.get(addr)
                    if k is None:
                        continue
                    s = k
                    while s > 0 and insns[s].mnemonic not in ("stdu", "mflr"):
                        s -= 1
                    f = insns[s].address
                    idx = {0xff: 0, 0x01: 1, 0x00: 2}[v]
                    func_counts[f][idx] += 1
                    if f not in func_example:
                        func_example[f] = (v, addr)

    # functions that write 0xff AND 0x01 (serializer emits both bool and int tags)
    strong = []
    for f, (cff, c01, c00) in func_counts.items():
        if cff >= 1 and c01 >= 2:
            strong.append((f, cff, c01, c00))
    strong.sort(key=lambda x: -(x[1] + x[2]))
    print("== functions writing 0xff(bool) + >=2x 0x01(int) stores ==")
    for f, cff, c01, c00 in strong[:30]:
        v, addr = func_example[f]
        print("  func 0x%08x: 0xff x%d, 0x01 x%d, 0x00 x%d  (first @0x%x=%02x)"
              % (f, cff, c01, c00, addr, v))


if __name__ == "__main__":
    main()
