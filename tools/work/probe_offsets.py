#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pin down the EXACT byte offset of each per-actor trust value.

Earlier tooling disagreed by +3 on the trust offsets (0x1114 vs 0x1117), which
almost certainly means the value is a BIG-ENDIAN u32 whose only non-zero byte is
the low byte at base+3. This prints the raw bytes at the candidate bases and the
authoritative changed-index list so we stop guessing.
"""
import os

SNAP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "work", "snaps")


def load(tag):
    return open(os.path.join(SNAP, tag, "GAMEDATA.bin"), "rb").read()


def main():
    T0, T1, T2 = load("T0"), load("T1"), load("T2")

    # Authoritative changed indices in the trust region, recomputed here.
    print("== changed indices T1->T2 in [0x1100,0x1200] ==")
    for i in range(0x1100, 0x1200):
        if T1[i] != T2[i]:
            print("  idx 0x%04x  T1=%02x T2=%02x" % (i, T1[i], T2[i]))

    # Raw bytes at each candidate base (BE-implied bases = diff_off - 3).
    for base in (0x1114, 0x1178, 0x1184, 0x11a4, 0x11c4):
        print("== base 0x%04x .. +3 (BE) ==" % base)
        for tag, d in (("T0", T0), ("T1", T1), ("T2", T2)):
            b = d[base:base + 4]
            be = (b[0] << 24) | (b[1] << 16) | (b[2] << 8) | b[3]
            le = b[0] | (b[1] << 8) | (b[2] << 16) | (b[3] << 24)
            print("  %s  bytes=%s  BE=%d  LE=%d"
                  % (tag, b.hex(" "), be, le))

    # Whole region as BE u32, which is what the diff offsets imply.
    print("\n== 0x1100-0x1200 as u32 BE ==")
    for tag, d in (("T0", T0), ("T1", T1), ("T2", T2)):
        vals = []
        for o in range(0x1100, 0x1200, 4):
            v = (d[o] << 24) | (d[o + 1] << 16) | (d[o + 2] << 8) | d[o + 3]
            vals.append("%08x" % v)
        print("  %s" % tag)
        for r in range(0, len(vals), 4):
            print("    %04x  %s" % (0x1100 + r * 4, " ".join(vals[r:r + 4])))


if __name__ == "__main__":
    main()
