#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Full non-zero structure map of GAMEDATA (T2), to locate the per-actor
trust (信頼度, 10 stars) / 台本 (scripts %) record array.

The声優名鑑 shows, per actor: affiliation, trust (10 stars), skills, and
"演じられる台本" (performable scripts, e.g. 20%). There are ~50 CVs. If trust is
STORED per actor we expect a contiguous block of small values (0..100 or 0..10).
This prints every non-zero run in the file so we can eyeball array-like regions,
then decodes the promising ones as u32 BE / LE. Read-only.
"""
import os

SNAP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "work", "snaps")


def load(tag):
    return open(os.path.join(SNAP, tag, "GAMEDATA.bin"), "rb").read()


def main():
    T0, T1, T2 = load("T0"), load("T1"), load("T2")
    n = len(T2)

    print("== every non-zero run in T2 (offset, len, bytes) ==")
    i = 0
    while i < n:
        if T2[i] != 0:
            j = i
            while j < n and T2[j] != 0:
                j += 1
            length = j - i
            # only show runs that are plausibly data (len<=64) or note long ones
            tag = ""
            if length <= 96:
                tag = T2[i:j].hex(" ")
            else:
                tag = "...(%d bytes)..." % length
            print("  0x%04x len=%3d  %s" % (i, length, tag))
            i = j
        else:
            i += 1

    # Decode candidate per-actor arrays: look for contiguous blocks (>=32 bytes,
    # <= 0x100) where a good fraction of bytes are in 1..100. Report as u8 and
    # as u32 BE/LE.
    print("\n== blocks with many small(1..100) bytes (candidate trust arrays) ==")
    i = 0
    while i < n:
        # extend a window while bytes are "small-ish" (<=100) or zero
        if 1 <= T2[i] <= 100:
            j = i
            small = 0
            zero = 0
            while j < n and j - i < 0x200:
                v = T2[j]
                if 1 <= v <= 100:
                    small += 1
                elif v == 0:
                    zero += 1
                else:
                    break
                j += 1
            if small >= 24 and (small + zero) >= 32:
                print("  block 0x%04x-0x%04x  small=%d zero=%d" % (i, j - 1, small, zero))
                print("     u8 : %s" % T2[i:j].hex(" "))
                i = j
                continue
        i += 1


if __name__ == "__main__":
    main()
