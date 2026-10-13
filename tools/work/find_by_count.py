#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-examine the completion/record structures with fresh eyes.

The cleared counter 0x0140 goes 99->117 (+18) T0->T2, total=125 (0x0148). The
record bank at 0x00c0 has 32-byte records [u32 BE count][u32 BE done][pad].
Only ~3 records populated. But maybe the per-scenario store is elsewhere and
the 0x0180 region (ff ff.. 03 05 .. -> 00) is a real flag that flips.

Goal: find a region whose *number of set entries* equals the cleared count
(99 at T0, 117 at T2) — that region IS the scenario-completion store, and the
名鑑 trust is derived from it. Read-only.
"""
import os

SNAP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "work", "snaps")


def load(tag):
    return open(os.path.join(SNAP, tag, "GAMEDATA.bin"), "rb").read()


def main():
    T0, T1, T2 = load("T0"), load("T1"), load("T2")
    n = len(T0)

    # For every byte offset, classify each tag's byte as "set" by several rules
    # and look for an offset where the COUNT of set bytes in a 128..160-byte
    # window starting there equals 99 (T0) / 117 (T2). Try rule: byte != 0.
    print("== windows where nonzero-byte-count == 99(T0) and 117(T2) ==")
    for W in range(120, 170, 4):
        for lo in range(0, n - W, 4):
            c0 = sum(1 for o in range(lo, lo + W) if T0[o] != 0)
            c2 = sum(1 for o in range(lo, lo + W) if T2[o] != 0)
            if c0 == 99 and c2 == 117:
                print("  W=%d win 0x%04x-0x%04x  nonzero T0=%d T2=%d"
                      % (W, lo, lo + W - 1, c0, c2))

    # Rule: byte == 0xFF (cleared marker). Count FF bytes; find window where
    # FF-count grows by ~18 T0->T2 with capacity near 125.
    print("\n== windows where FF-byte-count grows +15..+21 T0->T2 ==")
    for W in range(120, 170, 4):
        for lo in range(0, n - W, 4):
            c0 = sum(1 for o in range(lo, lo + W) if T0[o] == 0xFF)
            c2 = sum(1 for o in range(lo, lo + W) if T2[o] == 0xFF)
            if 15 <= (c2 - c0) <= 21:
                print("  W=%d win 0x%04x-0x%04x  FF T0=%d T2=%d (+%d)"
                      % (W, lo, lo + W - 1, c0, c2, c2 - c0))

    # Dump 0x0180-0x01a0 region with a note on the flipping byte 0x0188.
    print("\n== 0x0180-0x01a0 all tags ==")
    for tag, d in (("T0", T0), ("T1", T1), ("T2", T2)):
        print("  %s  %s" % (tag, d[0x0180:0x01a0].hex(" ")))

    # How many total 0xFF bytes in the whole file per tag? (a cleared-count proxy)
    for tag, d in (("T0", T0), ("T1", T1), ("T2", T2)):
        print("  %s total FF bytes=%d  total nonzero=%d"
              % (tag, sum(1 for x in d if x == 0xFF),
                 sum(1 for x in d if x != 0)))


if __name__ == "__main__":
    main()
