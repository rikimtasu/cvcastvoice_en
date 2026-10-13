#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find callers of the serializer dispatcher (0xef4e4) and the map-iteration loop,
to extract the fixed field-write order (schema) that maps to on-disk offsets.

Also locate the top-level save-object serialize method and the hashmap put/get so
we can see the sequence of (type,key) pairs written => field order.
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

EXEC_OFF, EXEC_ADDR, EXEC_SIZE = 0x230, 0x10230, 0x22a714
TARGETS = [0xef4e4, 0xe45f4, 0xf51ac, 0xd8dbc, 0xd8f44, 0xd8a44, 0x86f9c]


def find_callers(img, target):
    """Scan exec words for 'bl target' (opcode 18) and return call site addrs."""
    code = img.d[EXEC_OFF:EXEC_OFF + EXEC_SIZE]
    n = len(code) // 4
    words = struct.unpack_from(">%dI" % n, code, 0)
    # bl: 0x48000001 | (li << 2); effective target = addr + sext(li<<2)
    sites = []
    for i in range(n):
        w = words[i]
        if (w >> 26) == 18 and (w & 3) == 1 and (w & 1) == 1:  # bl
            li = w & 0x03fffffc
            if li & 0x02000000:
                li -= 0x04000000
            tgt = (EXEC_ADDR + i * 4 + li) & 0xffffffff
            if tgt == target:
                sites.append(EXEC_ADDR + i * 4)
    return sites


def enclosing_func(img, addr):
    off = img.vaddr_to_off(addr)
    # walk back up to 0x400 bytes for a prologue
    lo = max(EXEC_ADDR, addr - 0x400)
    cur = lo
    insns = list(img.md.disasm(img.d[img.vaddr_to_off(lo):off], lo))
    last_prologue = None
    for ins in insns:
        if ins.mnemonic in ("stdu", "mflr"):
            last_prologue = ins.address
        if ins.address >= addr:
            break
    return last_prologue


def main():
    img = Image(ELF)
    for t in TARGETS:
        callers = find_callers(img, t)
        print("\n== callers of 0x%x: %d sites ==" % (t, len(callers)))
        for c in callers[:12]:
            f = enclosing_func(img, c)
            print("   bl@0x%08x  (in func %s)" % (c, hex(f) if f else "?"))


if __name__ == "__main__":
    main()
