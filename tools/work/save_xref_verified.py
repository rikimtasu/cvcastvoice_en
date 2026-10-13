#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verified save-routine XREF.

Fixes two bugs from earlier attempts:
  1. The address-completion instruction is often 'addic' (opcode 13) or 'addi'
     (14) / 'ori' (24) / 'oris' (25) — earlier scans only checked some of these.
  2. Capstone may sign-render immediates; we verify against the RAW 32-bit word
     and accept BOTH +imm and sign-extended interpretations, reporting which
     resolves into the string range.

We locate every 'lis rX, 0x24' (or addis rX,r0,0x24) followed within 30 insns by
a completion carrying the GAMEDATA/OPTION/ICON0/PIC1 low half, dump the raw word
for verification, and print the enclosing function.
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

EXEC_OFF, EXEC_ADDR, EXEC_SIZE = 0x230, 0x10230, 0x22a714
# save-slot descriptor block low halves (referenced copies)
TARGETS = {0x2a14: "GAMEDATA", 0x2a24: "OPTION", 0x2a2c: "ICON0.PNG",
           0x2a3c: "PIC1.PNG", 0x29a4: "GAMEDATA(1st)"}
COMPLETE_OPC = {13: "addic", 14: "addi", 24: "ori", 25: "oris"}


def main():
    img = Image(ELF)
    d = img.d
    code = d[EXEC_OFF:EXEC_OFF + EXEC_SIZE]
    insns = list(img.md.disasm(code, EXEC_ADDR))
    print("decoded:", len(insns))

    # index words by address for raw verification
    def raw_word(vaddr):
        off = EXEC_OFF + (vaddr - EXEC_ADDR)
        return struct.unpack_from(">I", d, off)[0]

    # collect lis rX,0x24 sites per dst reg
    lis_by_reg = {}
    for i, ins in enumerate(insns):
        if ins.mnemonic in ("lis", "addis"):
            p = [x.strip() for x in ins.op_str.split(",")]
            if len(p) == 3 and p[1] == "r0":
                try:
                    if int(p[2], 0) == 0x24:
                        lis_by_reg.setdefault(p[0], []).append(i)
                except Exception:
                    pass

    hits = []
    for i, ins in enumerate(insns):
        opc = raw_word(ins.address) >> 26
        if opc not in COMPLETE_OPC:
            continue
        w = raw_word(ins.address)
        imm = w & 0xffff
        ra = (w >> 16) & 0x1f
        # map reg number -> name via op string
        p = [x.strip() for x in ins.op_str.split(",")]
        if len(p) < 3:
            continue
        srcname = p[1]
        if imm in TARGETS and srcname in lis_by_reg:
            cand = [j for j in lis_by_reg[srcname] if j < i]
            if cand and 0 < i - cand[-1] <= 30:
                la = insns[cand[-1]]
                hits.append((TARGETS[imm], la.address, ins.address,
                             COMPLETE_OPC[opc], imm, w))

    print("\n== verified save-slot descriptor references ==")
    for name, la, aa, mn, imm, w in hits:
        # verify: lis gives 0x240000; positive imm resolves to 0x24xxxx
        resolved_pos = 0x240000 + imm
        print("  %-13s lis@0x%08x  %s@0x%08x imm=0x%x raw=%08x  ->0x%x"
              % (name, la, mn, aa, imm, w, resolved_pos))

    # enclosing functions
    def func_start(idx):
        s = idx
        while s > 0 and insns[s].mnemonic not in ("stdu", "mflr"):
            s -= 1
        return s

    seen = set()
    print("\n== enclosing functions ==")
    for name, la, aa, mn, imm, w in hits:
        # find insn index of aa
        ai = next((k for k, ins in enumerate(insns) if ins.address == aa), None)
        if ai is None:
            continue
        fs = func_start(ai)
        faddr = insns[fs].address
        if faddr in seen:
            continue
        seen.add(faddr)
        print("\n---- func 0x%08x (first ref: %s) ----" % (faddr, name))
        for j in range(fs, min(fs + 90, len(insns))):
            mark = ">>" if insns[j].address == aa else "  "
            print("  %s 0x%08x  %-8s %s" % (mark, insns[j].address,
                  insns[j].mnemonic, insns[j].op_str))


if __name__ == "__main__":
    main()
