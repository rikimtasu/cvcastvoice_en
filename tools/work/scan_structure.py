#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hunt for the per-actor trust (信頼度) array in GAMEDATA.

The声優名鑑 shows trust as 10 stars per actor (screenshot: 八尾 伊月 = 4/10).
There are ~50 CVs (per seiyubase). If trust is STORED, we expect an array with a
regular record stride and small values (0..10, 0..100, or 0..1000). This scans
all three clear-snapshots for:
  * every 4-byte-aligned BE/LE value that changed across T0->T1->T2 (grouped)
  * candidate regular-stride byte arrays in the 0..100 range
  * regions that look like per-actor records
Read-only.
"""
import os

SNAP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "work", "snaps")


def load(tag):
    return open(os.path.join(SNAP, tag, "GAMEDATA.bin"), "rb").read()


def main():
    T0, T1, T2 = load("T0"), load("T1"), load("T2")
    n = len(T0)

    # 1. All changed byte indices across the full clear sequence, as runs.
    print("== all changed runs T0->T2 (context for what a clear touches) ==")
    i = 0
    while i < n:
        if T0[i] != T2[i]:
            j = i
            while j < n and T0[j] != T2[j]:
                j += 1
            print("  0x%04x-0x%04x (%d bytes)  T0=%s T2=%s"
                  % (i, j - 1, j - i, T0[i:j].hex(" "), T2[i:j].hex(" ")))
            i = j
        else:
            i += 1

    # 2. Candidate per-actor byte arrays: stride s in {8,12,16,20,24,32,40,48,64},
    #    sample the first byte of each record; count how many fall in 1..100 and
    #    are non-zero. A real trust array would have many small non-zero entries.
    print("\n== candidate regular-stride small-value byte arrays (T2) ==")
    for stride in (8, 12, 16, 20, 24, 32, 40, 48, 56, 64):
        for phase in range(0, min(stride, 16)):
            vals = [T2[o] for o in range(phase, n - stride, stride)]
            if not vals:
                continue
            nz = sum(1 for v in vals if v != 0)
            small = sum(1 for v in vals if 1 <= v <= 100)
            # want a decent count of small non-zero entries spread across file
            if 20 <= small and small >= 0.3 * len(vals):
                span = (len(vals))
                print("  stride=%2d phase=%2d  entries=%d nonzero=%d small(1..100)=%d"
                      % (stride, phase, span, nz, small))

    # 3. Show the record-bank region 0x00c0-0x0110 fully (per-scenario records?).
    print("\n== record bank 0x00c0-0x0110 (T0/T1/T2) ==")
    for tag, d in (("T0", T0), ("T1", T1), ("T2", T2)):
        print("  %s" % tag)
        for o in range(0x00c0, 0x0110, 16):
            print("    %04x  %s" % (o, d[o:o + 16].hex(" ")))


if __name__ == "__main__":
    main()
