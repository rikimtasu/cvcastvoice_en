#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scan the live GAMEDATA save for candidate per-VA arrays (50 elements).

Ground truth: 八尾伊月 = VA index 49 (id 314), trust = 4, 台本 = 20%.
A candidate trust array: 50 consecutive bytes (or u16/u32 LE/BE) with values
in 0..10 where element[49] == 4 (or element[46] == 4 if the DLC-less VA at
index 46 is excluded / order differs). Also candidate percent array: element
20-ish at [49] in 0..100.

Print all windows where element[49] lands on plausible values AND all elements
fit the range (0..10 for trust; 0..100 step-ish for percent).
"""
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load():
    p = r"D:\Video_Game\Emulator\RPCS3\dev_hdd0\home\00000001\savedata\NPJB00558-GAMEDATA-\GAMEDATA"
    return Path(p).read_bytes()


def scan(d, width, fmt, vmax, want49, label):
    """width: bytes per element; fmt '<'/'>'; returns windows where all elems
    <= vmax and elem[49] == want49 (and report elem[46] too)."""
    hits = []
    esz = width
    n = len(d) // esz
    for off in range(0, len(d) - 50 * esz + 1):
        ok = True
        vals = []
        for k in range(50):
            o = off + k * esz
            if esz == 1:
                v = d[o]
            elif esz == 2:
                v = struct.unpack_from(fmt + "H", d, o)[0]
            else:
                v = struct.unpack_from(fmt + "I", d, o)[0]
            vals.append(v)
            if v > vmax:
                ok = False
                break
        if not ok:
            continue
        if vals[49] == want49:
            hits.append((off, vals))
    print("\n== %s  elem=1..%d fmt=%s vmax=%d : windows with elem[49]==%d = %d"
          % (label, width, "<" if fmt == "<" else ">", vmax, want49, len(hits)))
    for off, vals in hits[:14]:
        nonzero = sum(1 for v in vals if v)
        print("  off=0x%04x nonzero=%d/50 elem46=%d elem49=%d vals=%s"
              % (off, nonzero, vals[46], vals[49], vals[:20]))
    return hits


def main():
    d = load()
    print("save len:", len(d))
    # trust: byte array 0..10, elem49==4
    scan(d, 1, "<", 10, 4, "trust-bytes(BE-irrelevant)")
    # u16 LE / BE
    scan(d, 2, "<", 10, 4, "trust-u16LE")
    scan(d, 2, ">", 10, 4, "trust-u16BE")
    # percent candidates: elem49 == 20
    scan(d, 1, "<", 100, 20, "pct-bytes")
    # also try elem46==4 (index shift possibilities)
    scan(d, 1, "<", 10, 4, "trust (check46 shown)")


if __name__ == "__main__":
    main()
