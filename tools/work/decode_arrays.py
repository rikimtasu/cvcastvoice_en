#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Decode specific key arrays with correct encoding. The strings render as UTF-8
mojibake, so try utf-8 first, then shift_jis. Focus on 0x2e1f14 (trust levels),
0x2e1f78 (casting), 0x2f3be0 (name fragments) - the actor/scenario metadata.
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF


def cstr_at(img, va, maxlen=64):
    raw = img.read_at_v(va, maxlen)
    if not raw:
        return None, None
    if b"\x00" in raw:
        raw = raw[:raw.index(b"\x00")]
    if not raw:
        return None, None
    for enc in ("utf-8", "shift_jis", "euc_jp"):
        try:
            return raw.decode(enc), enc
        except Exception:
            continue
    return raw.decode("latin-1", "replace"), "latin1"


def dump_array(img, base, count, label):
    print("\n== %s  (char* array @0x%x, %d entries) ==" % (label, base, count))
    off = img.vaddr_to_off(base)
    for i in range(count):
        p = struct.unpack_from(">I", img.d, off + i * 4)[0]
        s, enc = cstr_at(img, p)
        print("  [%2d] 0x%08x (%s): %r" % (i, p, enc, s))


def main():
    img = Image(ELF)
    dump_array(img, 0x2e1f14, 15, "trust-level / 信頼度 labels")
    dump_array(img, 0x2e1f78, 19, "casting-related labels")
    dump_array(img, 0x2f3be0, 7, "name fragments")
    dump_array(img, 0x2e1c10, 37, "vtable 0x2e1c10 (37)")


if __name__ == "__main__":
    main()
