#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Decode the record-table layout.

From trial diffs we identified a record region ~0x1100-0x1200 (block A) that
mirrors to ~0x13a8-0x14a8 (+0x2a8). The 0x2123 region mirrors to 0x2923 (+0x800).

We now map record stride by scanning 0x1000-0x2200 for the first file (BASE) and
printing nonzero bytes with offsets, to see record boundaries. Also print the
0x2000-0x2a00 flag/bitfield region as a bit grid.
"""
import os
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SNAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snaps")


def load(tag):
    with open(os.path.join(SNAP, tag, "GAMEDATA.bin"), "rb") as f:
        return f.read()


def nonzero_map(d, lo, hi):
    print("== nonzero bytes %s 0x%04x-0x%04x ==" % ("", lo, hi))
    run = None
    for o in range(lo, hi):
        if d[o] != 0:
            if run is None:
                run = [o, o]
            else:
                run[1] = o
        else:
            if run is not None and o - run[1] > 8:
                s, e = run
                print("  0x%04x-0x%04x: %s" % (s, e, d[s:e + 1].hex(" ")))
                run = None
    if run is not None:
        s, e = run
        print("  0x%04x-0x%04x: %s" % (s, e, d[s:e + 1].hex(" ")))


def main():
    BASE = load("BASE")
    # record region A
    nonzero_map(BASE, 0x1100, 0x1300)
    print()
    # flag region
    nonzero_map(BASE, 0x2000, 0x2a00)
    # tail region around 0x3f00
    print()
    nonzero_map(BASE, 0x3f00, 0x3f80)


if __name__ == "__main__":
    main()
