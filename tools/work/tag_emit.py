#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find the tag-emit code: where 0xff (bool-true) and 0x01 (int tag) are written
into the serialize buffer, to learn the TLV scheme and the scenario array layout.

The on-disk tail is a serialized tree: 0xff=bool-true element, 01 XX=int record.
We find code sites doing 'li rX, 0xff ; stb' and 'li rX, 1 ; stb' near the save
path, then map the surrounding logic. We scan the whole exec segment for the
byte-immediate 0xff and 0x01 stored via stb/sth/stw and cluster by function.
"""
import struct
import sys
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

EXEC_OFF, EXEC_ADDR, EXEC_SIZE = 0x230, 0x10230, 0x22a714


def main():
    img = Image(ELF)
    d = img.d
    code = d[EXEC_OFF:EXEC_OFF + EXEC_SIZE]
    n = len(code) // 4
    words = struct.unpack_from(">%dI" % n, code, 0)
    insns = list(img.md.disasm(code, EXEC_ADDR))
    addr2i = {ins.address: i for i, ins in enumerate(insns)}

    # find 'li rX, 0xff' (addi rX, r0, ... sign? 0xff as imm) and 'li rX,1'
    # li rX,0xff == addi rX, r0, 0xff (opcode 14, ra=0, imm=0xff)
    # then within a few insns an stb/sth/stw to a buffer.
    li_sites = []
    for i, w in enumerate(words):
        opc = w >> 26
        if opc == 14:  # addi
            ra = (w >> 16) & 0x1f
            imm = w & 0xffff
            rt = (w >> 21) & 0x1f
            if ra == 0 and imm in (0xff, 0x01, 0x00):
                li_sites.append((i, rt, imm))

    # for each li, find following store using that reg
    hits = defaultdict(int)  # func -> count
    examples = {}
    for i, rt, imm in li_sites:
        for j in range(i + 1, min(i + 5, n)):
            w2 = words[j]
            opc2 = w2 >> 26
            rs = (w2 >> 21) & 0x1f
            if rs != rt:
                continue
            if opc2 in (38, 44, 36, 37):  # stb, sth, stw, stwu
                addr = EXEC_ADDR + j * 4
                # enclosing function
                k = addr2i.get(addr)
                if k is None:
                    break
                s = k
                while s > 0 and insns[s].mnemonic not in ("stdu", "mflr"):
                    s -= 1
                f = insns[s].address
                hits[(f, imm)] += 1
                if (f, imm) not in examples:
                    examples[(f, imm)] = (EXEC_ADDR + i * 4, addr)
                break

    # show functions that emit BOTH 0xff and 0x01 stores (serializer candidates)
    byfunc = defaultdict(dict)
    for (f, imm), cnt in hits.items():
        byfunc[f][imm] = cnt
    cands = [f for f, m in byfunc.items() if 0xff in m and 0x01 in m]
    print("functions emitting both 0xff and 0x01 stores:", len(cands))
    for f in sorted(cands)[:20]:
        m = byfunc[f]
        print("  func 0x%08x: 0xff x%d, 0x01 x%d, 0x00 x%d"
              % (f, m.get(0xff, 0), m.get(0x01, 0), m.get(0x00, 0)))


if __name__ == "__main__":
    main()
