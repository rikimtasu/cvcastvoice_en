#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Decode the 0x3e00-0x3fc0 region as records.

The all-0xff region with occasional '01 XX' markers looks like per-group
completion records: 0xff = cleared slot, 01 = group header, XX = count.
We dump the region and locate every non-0xff byte (the group headers) for each
trial, to see the record layout and which group-count moved (0x3f5a: 0e->32).
"""
import os
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SNAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snaps")


def load(tag):
    with open(os.path.join(SNAP, tag, "GAMEDATA.bin"), "rb") as f:
        return f.read()


def main():
    T = {t: load(t) for t in ("BASE", "T0", "T1", "T2")}
    d = T["BASE"]
    lo, hi = 0x3e00, 0x3fc0
    # find non-ff, non-00 bytes in BASE within region
    print("== BASE non-0xff bytes in 0x%04x-0x%04x ==" % (lo, hi))
    for o in range(lo, hi):
        if d[o] != 0xff:
            print("  0x%04x = %02x" % (o, d[o]))

    # 0x3e00 region: is it exactly 0xff to 0x3f5a? show boundary bytes
    print("\n== region boundaries ==")
    for o in range(0x3df0, 0x3e10):
        print("  0x%04x = %02x" % (o, d[o]))
    print("  ...")
    for o in range(0x3f50, 0x3f70):
        print("  0x%04x = %02x  (T0=%02x)" % (o, d[o], T["T0"][o]))


if __name__ == "__main__":
    main()
