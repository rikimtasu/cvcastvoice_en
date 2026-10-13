#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump the contiguous short-identifier string blob these table pointers hit
(0x240060-0x240140) so we can see the whole key/enum vocabulary, and scan a
WIDE range of the pointer-table region for ALL 32-bit pointers into 0x230000+
so we don't miss identifiers not in the original TARGETS list.
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF


def read_cstr(img, vaddr, maxlen=64):
    raw = img.read_at_v(vaddr, maxlen)
    if b"\x00" in raw:
        raw = raw[:raw.index(b"\x00")]
    try:
        return raw.decode("shift_jis")
    except Exception:
        try:
            return raw.decode("latin-1")
        except Exception:
            return repr(raw)


def dump_string_blob(img, lo, hi):
    off = img.vaddr_to_off(lo)
    raw = img.d[off:off + (hi - lo)]
    va = lo
    print("== string blob 0x%x-0x%x ==" % (lo, hi))
    while va < hi and b"\x00" in raw:
        n = raw.index(b"\x00")
        chunk = raw[:n]
        try:
            s = chunk.decode("shift_jis")
        except Exception:
            s = repr(chunk)
        if len(chunk) and len(s) <= 40:
            print("  0x%08x: %r" % (va, s))
        raw = raw[n + 1:]
        va += n + 1


def scan_wide(img, lo, hi):
    print("\n== wide u32 pointer scan of table region 0x%x-0x%x ==" % (lo, hi))
    d = img.d
    off = img.vaddr_to_off(lo)
    for o in range(off, off + (hi - lo) - 3, 4):
        v = struct.unpack_from(">I", d, o)[0]
        if 0x230000 <= v < 0x2a0000:
            va = lo + (o - off)
            s = read_cstr(img, v)
            if len(s) <= 24:
                print("  0x%08x -> 0x%x %r" % (va, v, s))


def main():
    img = Image(ELF)
    dump_string_blob(img, 0x240060, 0x240140)
    scan_wide(img, 0x2f2300, 0x2f2480)


if __name__ == "__main__":
    main()
