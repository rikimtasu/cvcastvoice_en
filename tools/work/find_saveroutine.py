#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find exact code sites referencing the save-slot descriptor block
(GAMEDATA@0x242a14, OPTION@0x242a24) and disassemble the enclosing function.

The referenced save block is the second copy: GAMEDATA/OPTION/ICON0.PNG/PIC1.PNG
clustered at 0x242a14..0x242a3c. We locate 'lis rX,0x24' followed by
'addi/ori rY,rX,0x2a14' (and 0x2a24) and dump ±40 instructions of context,
plus the whole enclosing function (bounded by prologue 'stdu r1,-N(r1)' / mflr
and the epilogue 'ld r1,*; blr' / 'mtlr').
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

EXEC_OFF, EXEC_ADDR, EXEC_SIZE = 0x230, 0x10230, 0x22a714


def decode_all(img):
    code = img.d[EXEC_OFF:EXEC_OFF + EXEC_SIZE]
    return list(img.md.disasm(code, EXEC_ADDR))


def main():
    img = Image(ELF)
    insns = decode_all(img)
    addr2i = {ins.address: i for i, ins in enumerate(insns)}
    print("decoded:", len(insns))

    # target low halves that were PRESENT in code
    targets = {0x2a14: "GAMEDATA", 0x2a24: "OPTION", 0x2a2c: "ICON0.PNG",
               0x2a3c: "PIC1.PNG"}

    # find lis rX,0x24 sites
    lis = {}  # dstreg -> list of (addr, idx)
    for i, ins in enumerate(insns):
        if ins.mnemonic in ("lis", "addis"):
            p = [x.strip() for x in ins.op_str.split(",")]
            if len(p) == 3 and p[1] == "r0" and p[2] in ("0x24", "36"):
                lis.setdefault(p[0], []).append((ins.address, i))

    # find addi/ori completing each target
    hits = []
    for i, ins in enumerate(insns):
        if ins.mnemonic in ("addi", "ori"):
            p = [x.strip() for x in ins.op_str.split(",")]
            if len(p) < 3:
                continue
            try:
                imm = int(p[2], 0)
            except Exception:
                continue
            if imm in targets and p[1] in lis:
                # nearest preceding lis on that reg
                cand = [x for x in lis[p[1]] if x[1] < i]
                if cand:
                    la, li = cand[-1]
                    if 0 < i - li <= 30:
                        hits.append((targets[imm], la, ins.address, i))

    print("\n== sites referencing save-slot descriptor block ==")
    for name, la, aa, i in hits:
        print("  %-10s lis@0x%08x  complete@0x%08x" % (name, la, aa))

    # For each hit, find enclosing function bounds and dump.
    def func_bounds(idx):
        # walk back to prologue
        s = idx
        while s > 0:
            m = insns[s].mnemonic
            if m in ("stdu", "mflr"):
                break
            s -= 1
        # walk forward to epilogue (blr preceded by mtlr/ld r1)
        e = idx
        while e < len(insns) - 1:
            if insns[e].mnemonic == "blr":
                break
            e += 1
        return s, e

    seen = set()
    for name, la, aa, i in hits:
        s, e = func_bounds(i)
        faddr = insns[s].address
        if faddr in seen:
            continue
        seen.add(faddr)
        print("\n---- enclosing function @0x%08x (refs %s) ----" % (faddr, name))
        for j in range(s, min(e + 1, s + 120)):
            mark = ">>" if j == i else "  "
            print("  %s 0x%08x  %-7s %s" % (mark, insns[j].address,
                  insns[j].mnemonic, insns[j].op_str))


if __name__ == "__main__":
    main()
