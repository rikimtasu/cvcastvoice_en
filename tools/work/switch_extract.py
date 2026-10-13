#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract the serializer type-switch table from func 0xef4e4.

The function switches on a type id (r30) via 'cmpwi r30, N ; beq handler'.
We parse the linear disassembly, track the compare value and its branch target,
and build {type_id: handler_addr}. Then we disassemble each handler's first ~20
insns to see what tag byte it writes (stb 0x00/0x01/0xff) and what it calls.
"""
import re
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

START = 0xef4e4
SCAN = 0x600  # bytes to scan for the switch


def main():
    img = Image(ELF)
    off = img.vaddr_to_off(START)
    insns = list(img.md.disasm(img.d[off:off + SCAN], START))

    table = {}  # type_id -> handler
    last_cmp = None  # (val, creg)
    for ins in insns:
        mn = ins.mnemonic
        if mn == "cmpwi":
            m = re.search(r"r(\d+),\s*(-?0x[0-9a-fA-F]+|-?\d+)", ins.op_str)
            if m:
                reg = m.group(1)
                val = int(m.group(2), 0)
                last_cmp = (reg, val)
        elif mn in ("beq", "bne", "bgt", "blt", "bge", "ble") and last_cmp is not None:
            try:
                tgt = int(ins.op_str.split(",")[-1].strip(), 0)
            except Exception:
                last_cmp = None
                continue
            reg, val = last_cmp
            # only equality branches define a case
            if mn == "beq":
                table[val] = tgt
            last_cmp = None

    print("switch cases extracted:", len(table))
    for tid in sorted(table):
        print("  type 0x%02x (%3d) -> handler 0x%x" % (tid & 0xffff, tid, table[tid]))

    # For each handler, disassemble and look for tag writes
    print("\n== handler tag behavior ==")
    for tid in sorted(table):
        h = table[tid]
        hins = img.disasm_range(h, 40 * 4)
        tags = []
        calls = []
        strs = []
        # track li reg,imm then stb reg
        li = {}
        for ins in hins:
            if ins.mnemonic == "li" or (ins.mnemonic == "addi" and ", r0," in ins.op_str):
                m = re.search(r"r(\d+),\s*(-?0x[0-9a-fA-F]+|-?\d+)", ins.op_str)
                if m:
                    li[m.group(1)] = int(m.group(2), 0)
            elif ins.mnemonic == "stb":
                m = re.search(r"r(\d+),", ins.op_str)
                if m and m.group(1) in li and li[m.group(1)] in (0x00, 0x01, 0xff):
                    tags.append(li[m.group(1)])
            elif ins.mnemonic == "bl":
                try:
                    calls.append(int(ins.op_str, 0))
                except Exception:
                    pass
        print("  type 0x%02x @0x%x: tagbytes=%s calls=%s"
              % (tid & 0xffff, h, [hex(t) for t in tags[:4]],
                 [hex(c) for c in calls[:4]]))


if __name__ == "__main__":
    main()
