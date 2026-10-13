#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Exhaustive bit-level hunt for the 125-scenario completion bitfield.

If 名鑑 trust/scripts% is DERIVED from scenario completion, there must be a
125-bit field whose set-bit popcount == cleared counter: 99 (T0), 117 (T2),
delta +18. Earlier coarse scans (4-byte aligned, few window sizes) found none.
This checks EVERY bit offset (byte*8+bit) and both bit orders, reading exactly
125 consecutive bits, and reports any offset where popcount matches 99/117 (and
ideally 99/99/117 across T0/T1/T2). Definitive + cheap. Read-only.
"""
import os

SNAP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "work", "snaps")
NBITS = 125


def load(tag):
    return open(os.path.join(SNAP, tag, "GAMEDATA.bin"), "rb").read()


def bit(d, i):
    return (d[i >> 3] >> (7 - (i & 7))) & 1  # MSB-first


def bit_lsb(d, i):
    return (d[i >> 3] >> (i & 7)) & 1


def popcount_bits(d, start, count, lsb=False):
    fn = bit_lsb if lsb else bit
    c = 0
    for k in range(count):
        c += fn(d, start + k)
    return c


def main():
    T0, T1, T2 = load("T0"), load("T1"), load("T2")
    n = len(T0) * 8

    for lsb in (False, True):
        order = "LSB" if lsb else "MSB"
        print("== bit order %s : scan for popcount(125)==99(T0)&117(T2) ==" % order)
        found = 0
        for start in range(0, n - NBITS):
            c0 = popcount_bits(T0, start, NBITS, lsb)
            if c0 != 99:
                continue
            c1 = popcount_bits(T1, start, NBITS, lsb)
            c2 = popcount_bits(T2, start, NBITS, lsb)
            if c2 == 117:
                print("  bit-start %d (byte 0x%x bit %d)  T0=%d T1=%d T2=%d"
                      % (start, start >> 3, start & 7, c0, c1, c2))
                found += 1
        if not found:
            print("  (no exact 99/117 window)")

    # Relax: report any 125-bit window with popcount in [95..120] at T2 that
    # GREW by >=15 from T0 (MSB order) — near-misses worth eyeballing.
    print("\n== near-miss MSB: T2 popcount in [95..120] and grew >=12 from T0 ==")
    shown = 0
    for start in range(0, n - NBITS):
        c0 = popcount_bits(T0, start, NBITS, False)
        c2 = popcount_bits(T2, start, NBITS, False)
        if 95 <= c2 <= 120 and (c2 - c0) >= 12:
            print("  bit-start %d (byte 0x%x)  T0=%d T2=%d (+%d)"
                  % (start, start >> 3, c0, c2, c2 - c0))
            shown += 1
            if shown >= 30:
                print("  ...")
                break
    if not shown:
        print("  (none)")


if __name__ == "__main__":
    main()
