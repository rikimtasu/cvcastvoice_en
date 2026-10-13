#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Focus on the only tail bits that changed across trials: 0x3f5b and 0x2123.
Dump 32-byte context for each trial to see the surrounding structure and how the
value flips. 0x3f5b sat between two 0xff runs; 0x2123 in the flag block.
"""
import os
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SNAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snaps")


def load(tag):
    with open(os.path.join(SNAP, tag, "GAMEDATA.bin"), "rb") as f:
        return f.read()


def ctx(T, off, n=32):
    base = off - (off % 16)
    print("  around 0x%04x:" % off)
    for r in range(base - 16, base + n, 16):
        row = " ".join("%02x" % T[r + k] for k in range(16))
        print("    0x%04x: %s" % (r, row))


def main():
    T = {t: load(t) for t in ("BASE", "T0", "T1", "T2")}
    for off in (0x3f5b, 0x2123, 0x21bf, 0x11c7):
        print("\n==== offset 0x%04x ====" % off)
        for t in ("BASE", "T0", "T1", "T2"):
            v = T[t][off]
            print("  %-5s = 0x%02x (%3d)" % (t, v, v))
        ctx(T["BASE"], off)

    # 0x3f5b region decode: it's between 0xff runs. Show bytes 0x3f40-0x3f80 all trials
    print("\n==== 0x3f40-0x3f80 (BASE vs T0) ====")
    for r in range(0x3f40, 0x3f80, 16):
        b = " ".join("%02x" % T["BASE"][r + k] for k in range(16))
        t0 = " ".join("%02x" % T["T0"][r + k] for k in range(16))
        print("  0x%04x BASE: %s" % (r, b))
        print("          T0  : %s" % t0)


if __name__ == "__main__":
    main()
