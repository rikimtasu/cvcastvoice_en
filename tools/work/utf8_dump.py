#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Decode, as clean UTF-8 to a file, (1) the trust-reward table @0x2e1f14, (2) all
'f%03d_*' and trust/scenario-related format keys, (3) the per-actor field-name
arrays. Also resolve the string-pointer arrays fully so we see the real JP text.
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

OUT = []
def emit(s=""):
    OUT.append(s)


def cstr(img, va, maxlen=64):
    raw = img.read_at_v(va, maxlen)
    if not raw:
        return None
    if b"\x00" in raw:
        raw = raw[:raw.index(b"\x00")]
    if not raw:
        return None
    # Shift-JIS decode (game is JP, cp932)
    for enc in ("cp932", "shift_jis"):
        try:
            return raw.decode(enc)
        except Exception:
            continue
    return raw.decode("latin-1", "replace")


def u32(img, va):
    return struct.unpack_from(">I", img.d, img.vaddr_to_off(va))[0]


def dump_ptr_array(img, base, n):
    emit("\n== pointer array @0x%x (%d entries) ==" % (base, n))
    for k in range(n):
        p = u32(img, base + k * 4)
        s = cstr(img, p)
        emit("  [%2d] 0x%08x: %r" % (k, p, s))


def scan_format_keys(img, lo, hi):
    """Dump all format keys containing f%03d or trust-ish tokens as UTF-8."""
    off = img.vaddr_to_off(lo)
    raw = img.d[off:off + (hi - lo)]
    va = lo
    emit("\n== format/id keys 0x%x-0x%x ==" % (lo, hi))
    while va < hi and b"\x00" in raw:
        n = raw.index(b"\x00")
        chunk = raw[:n]
        if chunk:
            try:
                s = chunk.decode("cp932")
            except Exception:
                s = None
            if s and any(tok in s for tok in ("f%03d", "tr", "trust", "scenario",
                                               "obi", "cha", "ca%", "prank",
                                               "rank", "clear")):
                emit("  0x%08x: %r" % (va, s))
        raw = raw[n + 1:]
        va += n + 1


def main():
    img = Image(ELF)
    # trust-reward table
    dump_ptr_array(img, 0x2e1f14, 15)
    # casting labels (0x2e1f78) - for context
    dump_ptr_array(img, 0x2f22d8, 15)
    # per-actor name-field arrays
    dump_ptr_array(img, 0x2f3be0, 7)
    dump_ptr_array(img, 0x308f50, 8)
    dump_ptr_array(img, 0x308f88, 5)
    # scan for f%03d family and trust keys
    scan_format_keys(img, 0x240000, 0x241000)
    scan_format_keys(img, 0x23d000, 0x23e000)
    scan_format_keys(img, 0x23e000, 0x23f000)

    with open("tools/work/_utf8_dump.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(emit.__self__ if False else OUT))
    print("wrote tools/work/_utf8_dump.txt (%d lines)" % len(OUT))


if __name__ == "__main__":
    main()
