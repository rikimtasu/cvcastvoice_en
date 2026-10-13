#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify the double-buffer mirror stride and the exact set of live fields.

From diffs: 0x1117<->0x13bf, 0x117b<->0x1423, 0x1187<->0x142f (stride 0x2a8)
and 0x2123<->0x2923, 0x21b9<->0x29b9 (stride 0x800). Test which stride makes the
two copies byte-identical across the whole file, and report the authoritative
region. The two candidate strides imply different layouts.
"""
import os
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SNAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snaps")


def load(tag):
    with open(os.path.join(SNAP, tag, "GAMEDATA.bin"), "rb") as f:
        return f.read()


def main():
    d = load("BASE")
    L = len(d)
    print("length 0x%x" % L)
    # test mirrors at several strides
    for stride in (0x2a8, 0x800, 0x1000, 0x1400, 0x1100):
        # compare [0, half) with [stride, stride+half) where half fits
        mism = 0
        total = 0
        for o in range(0, L - stride):
            total += 1
            if d[o] != d[o + stride]:
                mism += 1
        print("stride 0x%04x: %d mismatches / %d" % (stride, mism, total))

    # The real structure: dump the diff between the two copies at stride 0x800
    # for the 0x2000-0x2a00 window to see if they're identical there.
    print("\n== 0x2000 vs 0x2800 (stride 0x800) sample ==")
    for o in range(0x2000, 0x2100, 16):
        a = " ".join("%02x" % d[o + k] for k in range(16))
        b = " ".join("%02x" % d[o + 0x800 + k] for k in range(16))
        same = "OK" if a == b else "DIFF"
        print("  0x%04x %s\n         %s" % (o, same, a))
        if a != b:
            print("         %s" % b)


if __name__ == "__main__":
    main()
