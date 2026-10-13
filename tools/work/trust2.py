#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Decode trust-reward and character-schema strings with a robust JP decoder.

The earlier cp932/shift_jis attempts mangled because some strings start with a
half-width katakana lead byte. We decode leniently (errors=replace) and also try
to interpret the leading byte. Goal: read the 信頼度N->報酬 (trust level -> reward)
labels and the ca%03d character id scheme, and count distinct cast members.
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF


def cstr(img, va, maxlen=80):
    raw = img.read_at_v(va, maxlen)
    if not raw:
        return None
    if b"\x00" in raw:
        raw = raw[:raw.index(b"\x00")]
    if not raw:
        return None
    # try decoders in order; prefer one that yields CJK for high bytes
    best = None
    for enc in ("cp932", "shift_jis", "euc_jp"):
        try:
            s = raw.decode(enc)
        except Exception:
            continue
        cjk = sum(1 for c in s if 0x3000 <= ord(c) <= 0x9fff)
        if best is None or cjk > best[1]:
            best = (s, cjk)
    return best[0] if best else raw.decode("latin-1", "replace")


def dump_array(img, base, count, label):
    print("\n== %s (char* @0x%x, %d) ==" % (label, base, count))
    off = img.vaddr_to_off(base)
    for i in range(count):
        p = struct.unpack_from(">I", img.d, off + i * 4)[0]
        print("  [%2d] 0x%06x: %s" % (i, p, cstr(img, p)))


def main():
    img = Image(ELF)
    dump_array(img, 0x2e1f14, 15, "TRUST-REWARD table")
    # the n_* name-field labels and category
    for va in (0x23da80, 0x23da88, 0x23da90, 0x23da98, 0x23daa0, 0x23daa8,
               0x23dab0, 0x23dab8, 0x23dad4, 0x23db2c, 0x23db3c,
               0x23db44, 0x23db4c, 0x23db54, 0x23db5c, 0x23db6c,
               0x23db78, 0x23db88):
        print("  0x%06x: %s" % (va, cstr(img, va)))


if __name__ == "__main__":
    main()
