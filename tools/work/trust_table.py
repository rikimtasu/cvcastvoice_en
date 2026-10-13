#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Decode the trust-reward table @0x2e1f14 as Shift-JIS (the correct encoding for
this JP PS3 game; utf-8 mislabels it). Also decode the trust-region strings
0x23d900-0x23dc00 fully to see trust-level -> unlock relationships, and the
casting/rank tables. This is the 名鑑 trust model.
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF


def cstr_sjis(img, va, maxlen=80):
    raw = img.read_at_v(va, maxlen)
    if not raw:
        return None
    if b"\x00" in raw:
        raw = raw[:raw.index(b"\x00")]
    if not raw:
        return None
    for enc in ("shift_jis", "cp932", "euc_jp"):
        try:
            return raw.decode(enc)
        except Exception:
            continue
    return raw.decode("shift_jis", "replace")


def dump_array(img, base, count, label):
    print("\n== %s (char* @0x%x, %d) ==" % (label, base, count))
    off = img.vaddr_to_off(base)
    for i in range(count):
        p = struct.unpack_from(">I", img.d, off + i * 4)[0]
        print("  [%2d] 0x%06x: %s" % (i, p, cstr_sjis(img, p)))


def dump_region(img, lo, hi, label):
    print("\n== %s (0x%x-0x%x) ==" % (label, lo, hi))
    off = img.vaddr_to_off(lo)
    raw = img.d[off:off + (hi - lo)]
    va = lo
    while va < hi and b"\x00" in raw:
        z = raw.index(b"\x00")
        chunk = raw[:z]
        if chunk and len(chunk) >= 2:
            s = cstr_sjis(img, va)
            if s and any(ord(c) > 0x2000 or c.isalnum() for c in s):
                print("  0x%06x: %s" % (va, s))
        raw = raw[z + 1:]
        va += z + 1


def main():
    img = Image(ELF)
    dump_array(img, 0x2e1f14, 15, "TRUST-REWARD table")
    dump_region(img, 0x23d900, 0x23dc00, "trust region strings")


if __name__ == "__main__":
    main()
