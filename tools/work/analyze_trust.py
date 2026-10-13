#!/usr/bin/env python3
import sys

# -*- coding: utf-8 -*-
"""Map the per-actor trust (信頼度) layout from the T0->T1->T2 clear diffs.

The声優名鑑 screen shows trust as 10 stars per actor, and there are 8+ actors.
The old fabrication set 2 single bytes which clearly was not per-actor trust.
This dumps every changed byte across the three clear-snapshots and shows the
full 0x1100-0x1500 region (where the diff tool already found value bytes) so we
can identify the real per-actor trust records. Read-only.
"""
import os

SNAP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "work", "snaps")


def load(tag):
    return open(os.path.join(SNAP, tag, "GAMEDATA.bin"), "rb").read()


def changed(a, b):
    return [(i, a[i], b[i]) for i in range(len(a)) if a[i] != b[i]]


def dump(d, lo, hi):
    for row in range(lo, hi, 16):
        chunk = d[row:row + 16]
        print("  %04x  %s  |%s|" % (
            row, chunk.hex(" "),
            "".join(chr(c) if 32 <= c < 127 else "." for c in chunk)))


def u32le(d, o):
    return d[o] | (d[o + 1] << 8) | (d[o + 2] << 16) | (d[o + 3] << 24)


def u32be(d, o):
    return (d[o] << 24) | (d[o + 1] << 16) | (d[o + 2] << 8) | d[o + 3]


def main():
    T0, T1, T2 = load("T0"), load("T1"), load("T2")

    # Focus: only bytes inside the 0x1100-0x1250 region (and +0x2a8 mirror).
    for la, a, lb, b in (("T0", T0, "T1", T1), ("T1", T1, "T2", T2),
                         ("T0", T0, "T2", T2)):
        print("==== %s -> %s : changed bytes in 0x1100-0x1250 ====" % (la, lb))
        for off, x, y in changed(a, b):
            if 0x1100 <= off < 0x1250 or 0x1100 <= off - 0x2a8 < 0x1250:
                mir = off - 0x2a8 if off >= 0x13a8 else off + 0x2a8
                print("  @0x%04x (mirror 0x%04x)  %02x -> %02x   (%3d -> %3d)"
                      % (off, mir, x, y, x, y))
        print()

    # Decode the trust region as 4-byte LE values at every 4-byte boundary.
    for tag, d in (("T0", T0), ("T1", T1), ("T2", T2)):
        print("==== %s  0x1100-0x1250 as u32 LE (per 4-byte slot) ====" % tag)
        for row in range(0x1100, 0x1250, 16):
            vals = []
            for o in range(row, row + 16, 4):
                vals.append("%08x" % u32le(d, o))
            print("  %04x  %s" % (row, " ".join(vals)))
        print()


if __name__ == "__main__":
    main()

