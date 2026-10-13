#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify the save-slot descriptor struct at 0x23D5C4.

The four 'addic r4,r4,-0x2a3c/-0x2a2c/-0x2a24/-0x2a14' from base 0x240000 land
on 0x23D5C4/0x23D5D4/0x23D5DC/0x23D5EC - a data struct. If those slots hold
pointers to PIC1.PNG/ICON0.PNG/OPTION/GAMEDATA (0x242a3c/0x242a2c/0x242a24/
0x242a14), the save-slot descriptor is a char* struct and code dereferences it.
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF


def cstr(img, va, maxlen=48):
    raw = img.read_at_v(va, maxlen)
    if not raw:
        return None
    if b"\x00" in raw:
        raw = raw[:raw.index(b"\x00")]
    if not raw:
        return None
    try:
        return raw.decode("shift_jis")
    except Exception:
        return raw.decode("latin-1", "replace")


def main():
    img = Image(ELF)
    d = img.d
    base = 0x23D5C4
    print("== struct around 0x%x ==" % base)
    for off in range(-0x20, 0x60, 4):
        va = base + off
        o = img.vaddr_to_off(va)
        w = struct.unpack_from(">I", d, o)[0]
        note = ""
        if 0x230000 <= w < 0x2a0000:
            s = cstr(img, w)
            if s is not None:
                note = '-> "%s"' % s
        mark = "<<" if off in (0, 0x10, 0x18, 0x28) else "  "
        print("  %s 0x%08x: %08x  %s" % (mark, va, w, note))


if __name__ == "__main__":
    main()
