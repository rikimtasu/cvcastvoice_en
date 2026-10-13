#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract the COMPLETE type-switch table from func 0xef4e4 by following the
comparison chain across the whole function (not just 0x600B). We disassemble
until the epilogue blr, track cmpwi/beq pairs, and also record the bgt/bge range
guards to infer the full type-id range.
"""
import re
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

START = 0xef4e4
MAXBYTES = 0x2000


def main():
    img = Image(ELF)
    off = img.vaddr_to_off(START)
    insns = list(img.md.disasm(img.d[off:off + MAXBYTES], START))

    table = {}
    guards = []
    last = None
    for ins in insns:
        mn = ins.mnemonic
        if mn == "cmpwi":
            m = re.search(r"r(\d+),\s*(-?0x[0-9a-fA-F]+|-?\d+)", ins.op_str)
            if m:
                last = (m.group(1), int(m.group(2), 0))
        elif mn in ("cmpwi", "cmplwi"):
            pass
        elif mn in ("beq", "bne", "bgt", "blt", "bge", "ble") and last is not None:
            try:
                tgt = int(ins.op_str.split(",")[-1].strip(), 0)
            except Exception:
                last = None
                continue
            reg, val = last
            if mn == "beq":
                table[val] = tgt
            else:
                guards.append((mn, val, tgt))
            last = None
        elif mn == "blr":
            # end of first function (the switch prologue/handler body)
            break

    print("equality cases:", len(table))
    print("range guards:", len(guards))
    ids = sorted(table)
    print("type-id range: 0x%x .. 0x%x" % (ids[0], ids[-1]))
    for tid in ids:
        print("  type 0x%02x (%3d) -> 0x%x" % (tid & 0xffff, tid, table[tid]))
    print("\n-- range guards (beq excluded) --")
    for mn, val, tgt in guards:
        print("  %s %d -> 0x%x" % (mn, val, tgt))


if __name__ == "__main__":
    main()
