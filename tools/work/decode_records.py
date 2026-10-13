#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Decode the 0x20-stride 5-byte records (per-actor/scenario completion).

Diffs at 0x00c3/0x00e3/0x02a3/0x02c3 (type A: 0e ff ff ff ff -> 0d 00 00 01 0c)
and 0x0103/0x02e3 (type B: cd ff ff ff ff -> 9f 00 00 00 a0) show a repeating
record structure at 0x20 stride. We:
  - locate the array base (first record start) and stride
  - decode each record for BASE and T0, print side by side
  - infer field meanings: byte0 = count/tag?, bytes1-2 sub-flags, byte4 = trust?
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
    base = T["BASE"]

    # The record fields that moved:
    # type A at 0xc3,0xe3,0x2a3,0x2c3  ; type B at 0x103,0x2e3
    # scan 0x00c0..0x0300 at 0x20 stride to map the full array
    print("== candidate record fields (0x20 stride) in 0xc0..0x300 ==")
    print("off      BASE[0:6]                 T0[0:6]")
    for o in range(0xc0, 0x300, 0x20):
        b = tuple(base[o:o + 6])
        if any(b):  # skip all-zero
            print("0x%04x   %-26s %s" % (o, b, tuple(T["T0"][o:o + 6])))

    # Dump the first full 0x20 record at 0xc0 for BASE to see all fields
    print("\n== full record at 0xc0 (0x20 bytes), BASE vs T0 ==")
    for o in range(0xc0, 0xc0 + 0x20):
        b, t0 = base[o], T["T0"][o]
        mark = " <--" if b != t0 else ""
        print("  0x%04x: BASE=%02x  T0=%02x%s" % (o, b, t0, mark))


if __name__ == "__main__":
    main()
