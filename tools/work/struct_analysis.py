#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analyze the completion-tracking structure from the trial diffs.

Observed:
  - offset 0x0063 : small counter (5->6->7)
  - offset 0x0143 : cleared counter (75/117 -> 63/99 -> 75/117)
  - mirror spacing ~0x100 (0x0103<->0x02e3? no, 0x0118x<->0x0142x) and ~0x2a0
    (0x1117<->0x13bf, 0x117b<->0x1423), and ~0x700 (0x2123<->0x2923)
We dump the 0x1100-0x1180 and 0x1420-0x1440 record region for each trial to see
how a single clear changes a per-actor/per-scenario record. Also decode the
counter at 0x63 and the 4-byte LE/BE interpretations.
"""
import os
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SNAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snaps")


def load(tag):
    p = os.path.join(SNAP, tag, "GAMEDATA.bin")
    with open(p, "rb") as f:
        return f.read()


def dump_region(tag, lo, hi):
    d = load(tag)
    row = d[lo:hi]
    print("%-5s 0x%04x: %s" % (tag, lo, row.hex(" ")))


def main():
    # T0->T1 single clear touched: 0x63,0x73,0x27b,0x1187,0x11c7,0x142f,0x146f,0x2123,0x2923
    print("== T0->T1 single-clear touched offsets, with 16-byte context ==")
    d0 = load("T0")
    d1 = load("T1")
    for off in (0x60, 0x70, 0x278, 0x1180, 0x11c0, 0x1428, 0x1468, 0x2120, 0x2920):
        lo = off
        hi = off + 16
        print("  T0 0x%04x: %s" % (lo, d0[lo:hi].hex(" ")))
        print("  T1 0x%04x: %s" % (lo, d1[lo:hi].hex(" ")))
        print()

    # full comparison of the per-record block 0x1117 region across all trials
    print("== 0x1100-0x1200 across trials (per-record block A) ==")
    for t in ("BASE", "T0", "T1", "T2"):
        d = load(t)
        print("  %-5s 0x1110: %s" % (t, d[0x1110:0x1130].hex(" ")))
        print("  %-5s 0x1180: %s" % (t, d[0x1180:0x11a0].hex(" ")))
        print("  %-5s 0x11c0: %s" % (t, d[0x11c0:0x11e0].hex(" ")))

    # decode counter at 0x63 and cleared at 0x143
    print("== counters ==")
    for t in ("BASE", "T0", "T1", "T2"):
        d = load(t)
        print("  %-5s 0x63=%02x 0x143=%02x 0x147=%02x | LE32@0x140=%d"
              % (t, d[0x63], d[0x143], d[0x147],
                 int.from_bytes(d[0x140:0x144], "little")))


if __name__ == "__main__":
    main()
