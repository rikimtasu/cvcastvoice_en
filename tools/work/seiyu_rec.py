#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump one seiyubase record (default 48 = 八尾伊月) as ALL NUL-separated fields
with offsets, so we can see every field: ids, appearance lists, trust, etc.
Also print the raw hex of the record head (first 256 bytes).
"""
import re
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import cvpatch as C
from cricodecs import cpk

# record boundaries from _roster.txt (offsets)
STARTS = [0x7b0, 0x10dc, 0x1a88, 0x230c, 0x2c5e, 0x3454, 0x3d7c, 0x4682, 0x4fc4,
          0x57fc, 0x6178, 0x6982, 0x71b4, 0x7ad6, 0x83de, 0x8c68, 0x95ac, 0x9e50,
          0xa74c, 0xaf6c, 0xb7b2, 0xc090, 0xc9d2, 0xd30e, 0xdb20, 0xe418, 0xece6,
          0xf602, 0xff34, 0x1085a, 0x10f9c, 0x1183c, 0x12122, 0x12a1e, 0x13268,
          0x13b40, 0x1440e, 0x14c2a, 0x15472, 0x15d74, 0x16658, 0x16fb6, 0x17892,
          0x18124, 0x1896c, 0x19240, 0x1a4e6, 0x1ae9e, 0x1b7b0, 0x1c000]


def main():
    which = int(sys.argv[1]) if len(sys.argv) > 1 else 48
    a = cpk.load(str(C.ORIG))
    by = {f.full_path: f for f in a.files}
    d = a.file_bytes(by["DATA/daihon/seiyubase.pac"].toc_index)

    s = STARTS[which]
    e = STARTS[which + 1] if which + 1 < len(STARTS) else len(d)
    rec = d[s:e]
    print("record %d  0x%06x..0x%06x  len=%d" % (which, s, e, e - s))
    print("\nhead hex (first 256):")
    for i in range(0, min(len(rec), 256), 16):
        print("  %04x: %s" % (i, rec[i:i + 16].hex(" ")))

    print("\nfields:")
    start = 0
    while True:
        i = rec.find(b"\x00", start)
        chunk = rec[start:i] if i >= 0 else rec[start:]
        if chunk:
            try:
                t = chunk.decode("utf-8")
                disp = t if all(ord(c) == 9 or 32 <= ord(c) < 127 or ord(c) > 127
                                for c in t) else repr(t)
                print("  +%04x (%6d..%6d) len=%-4d %s" %
                      (start, s + start, s + (i if i >= 0 else len(rec)),
                       len(chunk), disp[:80]))
            except UnicodeDecodeError:
                print("  +%04x len=%-4d <bin> %s" % (start, len(chunk), chunk[:32].hex()))
        if i < 0:
            break
        start = i + 1

    # any u16/u32 arrays that look like ids (< 300) after last string
    print("\ntrailing u16 words (last 128 bytes):")
    tail = rec[-128:]
    words = struct.unpack("<%dH" % (len(tail) // 2), tail[:len(tail) // 2 * 2])
    print("  " + " ".join("%d" % w for w in words))


if __name__ == "__main__":
    main()
