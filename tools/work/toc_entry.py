#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Disassemble e_entry (0x2d8ba0) to extract the r2/TOC setup, then dump a few
following instructions. Prints TOC base once found (the ori/addi into r2).
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF


def main():
    img = Image(ELF)
    d = img.d
    start = 0x2d8ba0
    off = img.vaddr_to_off(start)
    print("entry vaddr=0x%x file=0x%x" % (start, off))
    n = 0
    toc = None
    for ins in img.md.disasm(d[off:off + 0x180], start):
        note = ""
        if ins.mnemonic in ("addis", "lis", "ori", "addi") and ins.op_str.startswith("r2"):
            note = "   <<< r2 setup"
        print("  0x%08x  %-8s %s%s" % (ins.address, ins.mnemonic, ins.op_str, note))
        n += 1
        if n >= 48:
            break

    # The classic GCC ELFv1 preamble at entry:
    #   addis r2, rX, .TOC.@ha ; ori r2, rX, .TOC.@l  -> compute directly:
    # We recompute: scan first 12 insns for 'addis r2, rA, imm' then 'ori r2, r2, imm'
    insns = list(img.md.disasm(d[off:off + 0x60], start))
    for i, ins in enumerate(insns):
        if ins.mnemonic == "addis" and ins.op_str.startswith("r2,"):
            p = [x.strip() for x in ins.op_str.split(",")]
            try:
                hi = int(p[2], 0)
            except Exception:
                continue
            base = p[1]
            for j in range(i + 1, min(i + 5, len(insns))):
                i2 = insns[j]
                if i2.mnemonic in ("ori", "addi") and i2.op_str.startswith("r2,"):
                    q = [x.strip() for x in i2.op_str.split(",")]
                    lo = int(q[2], 0)
                    if base == "r0":
                        toc = ((hi << 16) | lo) & 0xffffffff
                    else:
                        # relative to rX which itself may be loaded; print raw
                        toc = ((hi << 16) + lo) & 0xffffffff
                    print("\n** TOC candidate: %s + hi=0x%x lo=0x%x -> 0x%x"
                          % (base, hi, lo, toc))
                    break
            break
    if toc:
        print("TOC base = 0x%x" % toc)


if __name__ == "__main__":
    main()
