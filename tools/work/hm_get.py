#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Decode the hashmap container to find the ordered scenario/character key list.

From sec 11.3: func 0xd8dbc does 'keys = *(obj+0x18); if (idx < keys[idx]) ... ;
hashmap_get(0x86da4, container, key)'. This is a container object. We want the
key NAME array (the scenario/character identifiers) and its count, so the k-th
record ordinal maps to the k-th key.

Plan:
 1. Disassemble 0x86da4 (hashmap get) and 0xd8a44 (array accessor) precisely.
 2. Find where the key-name array is built: search code for a table of pointers
    into the save-vocab strings (0x23d5f4 'scenario', 0x23d604 'character', ...)
    and per-scenario keys.
 3. Locate count fields (lhz/li comparisons) that bound the record arrays.
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF


def show(img, addr, n=60):
    print("\n==== func @0x%08x ====" % addr)
    off = img.vaddr_to_off(addr)
    c = 0
    a = addr
    while c < n:
        ins = next(iter(img.md.disasm(img.d[off:off + 4], a)), None)
        if ins is None:
            print("  0x%08x  .byte %08x" % (a, struct.unpack_from(">I", img.d, off)[0]))
            off += 4; a += 4; c += 1; continue
        note = "  ; -> 0x%x" % int(ins.op_str, 0) if ins.mnemonic == "bl" and ins.op_str.strip().startswith("0x") else ""
        print("  0x%08x  %-8s %s%s" % (a, ins.mnemonic, ins.op_str, note))
        off += 4; a += 4; c += 1
        if ins.mnemonic == "blr":
            break


def main():
    img = Image(ELF)
    # core routines
    show(img, 0x86da4, 50)   # hashmap get
    show(img, 0xd8a44, 12)   # array accessor


if __name__ == "__main__":
    main()
