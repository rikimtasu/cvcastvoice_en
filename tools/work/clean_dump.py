#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Decode the scenario/character key regions as clean Shift-JIS into a UTF-8 file,
and dump readable strings from the live save. This finishes the key-list mapping.

Regions:
  0x23D560  scenario/character/unlock keys (save schema top-level)
  0x23da00  per-character record schema (cha, n_*, va, profile, secret, ca%03d...)
  0x2e1f14  trust-reward labels (信頼度1..10 -> orb)
Also scans the EBOOT for 'ca%03d'-style and scenario index arrays, and greps the
save for any embedded ASCII/JP keys.
"""
import os
import re
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_keys.txt")
SAVE = r"D:\Video_Game\Emulator\RPCS3\dev_hdd0\home\00000001\savedata\NPJB00558-GAMEDATA-\GAMEDATA"


def decode_region(img, lo, hi, minlen=1, maxlen=64):
    off = img.vaddr_to_off(lo)
    raw = img.d[off:off + (hi - lo)]
    va = lo
    rows = []
    while va < hi and b"\x00" in raw:
        n = raw.index(b"\x00")
        chunk = raw[:n]
        if chunk and minlen <= len(chunk) <= maxlen:
            try:
                s = chunk.decode("cp932")
            except Exception:
                s = chunk.decode("latin-1", "replace")
            printable = sum(1 for c in s if c.isprintable())
            if printable >= len(s) * 0.7:
                rows.append((va, s))
        raw = raw[n + 1:]
        va += n + 1
    return rows


def save_strings(data, minlen=3):
    """Extract printable ASCII + Shift-JIS JP runs from the save."""
    out = []
    # ASCII
    for m in re.finditer(rb"[\x20-\x7e]{%d,}" % minlen, data):
        out.append((m.start(), m.group().decode("latin-1")))
    return out


def main():
    img = Image(ELF)
    with open(OUT, "w", encoding="utf-8") as f:
        def w(*a):
            f.write(" ".join(str(x) for x in a) + "\n")

        w("=== TOP-LEVEL SAVE KEYS 0x23D560 ===")
        for va, s in decode_region(img, 0x23D560, 0x23D820, 2):
            w("  0x%08x  %s" % (va, s))

        w("\n=== CHARACTER RECORD SCHEMA 0x23da00-0x23dc00 ===")
        for va, s in decode_region(img, 0x23da00, 0x23dc00, 1):
            w("  0x%08x  %s" % (va, s))

        w("\n=== TRUST-REWARD LABELS 0x2e1f14 table ===")
        # these are pointers; decode each slot's string
        for slot in range(15):
            p = struct.unpack_from(">I", img.d, img.vaddr_to_off(0x2e1f14 + slot * 8))[0]
            if 0x230000 <= p < 0x2a0000:
                s = decode_region(img, p, p + 48, 1)
                if s:
                    w("  slot[%d] 0x%08x -> %s" % (slot, p, s[0][1]))

        w("\n=== ca%03d / index pattern strings in EBOOT ===")
        d = img.d
        for m in re.finditer(rb"ca%0\dd[\x00]", d):
            o = m.start()
            va = img.off_to_vaddr(o)
            w("  0x%08x  %s" % (va if va else -1, m.group()[:-1].decode()))
        for pat in (b"scenario", b"sc%d", b"st%03d", b"ch%03d", b"no%03d"):
            o = d.find(pat + b"\x00")
            if o >= 0:
                va = img.off_to_vaddr(o)
                w("  pat %r at 0x%08x" % (pat, va if va else -1))

        w("\n=== SAVE FILE readable strings ===")
        if os.path.exists(SAVE):
            data = open(SAVE, "rb").read()
            w("save length:", len(data))
            for off, s in save_strings(data, 3)[:120]:
                w("  save+0x%04x  %s" % (off, s))
        else:
            w("SAVE not found")

    print("wrote", OUT)


if __name__ == "__main__":
    main()
