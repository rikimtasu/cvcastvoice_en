#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump the full save vocabulary: all C-strings in 0x23C000-0x244000, grouped.
We want the scenario/character key names that feed the hashmap (0xd8dbc), which
is what maps record ordinal -> actor/scenario. Print with vaddr so we can XREF.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

LO, HI = 0x23c980, 0x244000


def main():
    img = Image(ELF)
    d = img.d
    off = img.vaddr_to_off(LO)
    raw = d[off:off + (HI - LO)]
    va = LO
    n = 0
    while va < HI and b"\x00" in raw:
        z = raw.index(b"\x00")
        chunk = raw[:z]
        if chunk:
            printable = sum(1 for c in chunk if 32 <= c < 127 or c >= 0x80)
            if len(chunk) >= 3 and printable >= len(chunk) * 0.7:
                try:
                    s = chunk.decode("shift_jis")
                except Exception:
                    s = repr(chunk)
                print("0x%08x: %r" % (va, s))
                n += 1
        raw = raw[z + 1:]
        va += z + 1
    print("total strings:", n)


if __name__ == "__main__":
    main()
