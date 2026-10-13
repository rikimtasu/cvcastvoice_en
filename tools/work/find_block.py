#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find code that accesses the per-character progress block (~file offset 0x11c0).

Across trials, 0x11c7 (cumulative clear count) changed and 0x2123 flag flipped.
Those offsets, when the in-memory struct is materialized via absolute addressing,
appear as immediates near stores. We scan for 'addic/addi rX, rX, -N' and
'stw/stb ... -N(reg)' where the magnitude matches interesting offsets (0x11c7,
0x2123, 0x143, 0x11c6) after a 'lis rX, base'. Since base is dynamic, instead we
scan for the immediate magnitude patterns that recur (struct field offsets).

Better approach: the block 0x1100-0x1200 is a repeating per-character record.
Find the record stride by locating fields that moved together, then find code
doing fixed-stride loops (slwi rX,rY,imm ; add) that index it.
"""
import os
import struct
import sys
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SNAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snaps")


def load(tag):
    with open(os.path.join(SNAP, tag, "GAMEDATA.bin"), "rb") as f:
        return f.read()


def main():
    T = {t: load(t) for t in ("BASE", "T0", "T1", "T2")}
    base = T["BASE"]
    # Find all offsets that differ between BASE and T0 (the controlled clears)
    diffs = [o for o in range(len(base)) if base[o] != T["T0"][o]]
    print("BASE vs T0 diff count:", len(diffs))
    # group diffs into clusters
    clusters = []
    for o in diffs:
        if clusters and o - clusters[-1][-1] <= 8:
            clusters[-1].append(o)
        else:
            clusters.append([o])
    print("diff clusters (0x%04x region):" % 0)
    for c in clusters:
        vals = {t: tuple(T[t][c[0]:c[-1] + 1]) for t in T}
        print("  0x%04x-0x%04x  " % (c[0], c[-1]), vals)


if __name__ == "__main__":
    main()
