#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Decode the file tail as a per-scenario completion bitfield and correlate.

Cleared counter @0x143 went 99(T0)->117(T2). If the 0x3e00-0x4d80 tail is a
scenario-cleared bitmap, its set-bit count should track the counter. We:
  - dump the tail header for each trial
  - count set bits in 256-byte windows across the tail for each trial
  - report which window's popcount best matches (counter) and how it changes.
"""
import os
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SNAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snaps")


def load(tag):
    with open(os.path.join(SNAP, tag, "GAMEDATA.bin"), "rb") as f:
        return f.read()


def popcount(b):
    return sum(bin(x).count("1") for x in b)


def main():
    T = {t: load(t) for t in ("BASE", "T0", "T1", "T2")}
    d = T["BASE"]
    L = len(d)
    print("file length:", L, "= 0x%x" % L)
    for t, dd in T.items():
        print("  %-5s 0x143=%02x(0x%04x)  0x323=%02x" %
              (t, dd[0x143], dd[0x143] * 1, dd[0x323]))

    # window popcounts across tail
    print("\n== set-bit counts, 256B windows from 0x3c00 to end ==")
    print("     offset   BASE   T0    T1    T2")
    for base in range(0x3c00, L, 256):
        row = [popcount(T[t][base:base + 256]) for t in ("BASE", "T0", "T1", "T2")]
        if any(row):
            print("  0x%04x   %4d  %4d  %4d  %4d" % (base, row[0], row[1], row[2], row[3]))

    # find byte runs of 0xff and 0x00 in tail for BASE
    print("\n== BASE tail runs (0x3e00-0x4d80) ==")
    lo = 0x3e00
    i = lo
    while i < L:
        v = d[i]
        j = i
        while j < L and d[j] == v:
            j += 1
        if j - i >= 4:
            print("  0x%04x-0x%04x len=%d val=%02x" % (i, j - 1, j - i, v))
        i = j


if __name__ == "__main__":
    main()
