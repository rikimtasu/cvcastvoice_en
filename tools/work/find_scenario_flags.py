#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Locate the 125-entry per-scenario COMPLETION array that drives the声優名鑑
trust (信頼度) and 演じられる台本 (scripts %).

Evidence: total scenarios = 125 (0x0148 const), cleared counter 0x0140 = 99(T0)
-> 117(T2), i.e. +18 across the clear sequence. A per-scenario completion store
must therefore gain ~18 set entries from T0->T2 and have capacity ~125. We scan
for:
  * byte-windows whose non-zero popcount grows ~+18 from T0->T2 (1 byte/scenario)
  * bit-windows whose set-bit popcount grows ~+18 (1 bit/scenario)
Read-only.
"""
import os

SNAP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "work", "snaps")


def load(tag):
    return open(os.path.join(SNAP, tag, "GAMEDATA.bin"), "rb").read()


def popcount_window_bytes(d, lo, hi):
    return sum(1 for o in range(lo, hi) if d[o] != 0)


def popcount_window_bits(d, lo, hi):
    return sum(bin(d[o]).count("1") for o in range(lo, hi))


def main():
    T0, T1, T2 = load("T0"), load("T1"), load("T2")
    n = len(T0)

    # Reference: cleared counter low bytes at 0x0140.
    print("cleared counter 0x0140 (u32 BE): T0=%d T1=%d T2=%d"
          % (((T0[0x140] << 24) | (T0[0x141] << 16) | (T0[0x142] << 8) | T0[0x143]),
             ((T1[0x140] << 24) | (T1[0x141] << 16) | (T1[0x142] << 8) | T1[0x143]),
             ((T2[0x140] << 24) | (T2[0x141] << 16) | (T2[0x142] << 8) | T2[0x143])))

    # Slide a window and report where non-zero byte count grows by ~18 T0->T2,
    # with a plausible capacity (~125 bytes => 100..160 window).
    print("\n== byte-array candidates: nonzero-count grows ~+15..+21 T0->T2 ==")
    W = 128
    for lo in range(0, n - W, 4):
        c0 = popcount_window_bytes(T0, lo, lo + W)
        c2 = popcount_window_bytes(T2, lo, lo + W)
        if 15 <= (c2 - c0) <= 21 and c0 >= 80:
            print("  win 0x%04x-0x%04x  T0nz=%d T2nz=%d  (+%d)"
                  % (lo, lo + W - 1, c0, c2, c2 - c0))

    # Bit-window: 125 bits ~ 16 bytes; scan small windows.
    print("\n== bitfield candidates: setbits grows ~+15..+21 T0->T2 ==")
    for W in (16, 20, 24, 32):
        for lo in range(0, n - W, 4):
            b0 = popcount_window_bits(T0, lo, lo + W)
            b2 = popcount_window_bits(T2, lo, lo + W)
            if 15 <= (b2 - b0) <= 21 and 80 <= b0 <= 120:
                print("  win 0x%04x-0x%04x (W=%d)  T0bits=%d T2bits=%d (+%d)"
                      % (lo, lo + W - 1, W, b0, b2, b2 - b0))

    # Also: any window where the SET of non-zero indices strictly grows and
    # total capacity is near 125. Dump the 0x00c0 bank records decoded.
    print("\n== record bank A 0x00c0-0x0140 decoded (u32 BE pairs) ==")
    for o in range(0x00c0, 0x0140, 8):
        a = (T2[o] << 24) | (T2[o + 1] << 16) | (T2[o + 2] << 8) | T2[o + 3]
        b = (T2[o + 4] << 24) | (T2[o + 5] << 16) | (T2[o + 6] << 8) | T2[o + 7]
        print("  0x%04x  f0=%10d  f1=%10d" % (o, a, b))


if __name__ == "__main__":
    main()
