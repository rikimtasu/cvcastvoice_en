#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Decode the scenario-COMPLETION structure that likely drives the声優名鑑
trust (信頼度) and 演じられる台本 (scripts %).

Hypothesis B: trust/scripts% are DERIVED from a per-scenario completion bitfield.
If so, filling that bitfield maxes every actor with no per-actor mapping needed.
This dumps: the 0x0140-0x02a0 completion/mirror region, the exact non-FF bytes
in the 512-byte 0x3dc0 block, and tests whether 0x3dc0 is a bitfield. Read-only.
"""
import os

SNAP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "work", "snaps")


def load(tag):
    return open(os.path.join(SNAP, tag, "GAMEDATA.bin"), "rb").read()


def main():
    T0, T1, T2 = load("T0"), load("T1"), load("T2")

    # 1. 0x0140-0x02a0 region, all tags.
    print("== 0x0140-0x02a0 (completion + toward mirror bank) ==")
    for tag, d in (("T0", T0), ("T1", T1), ("T2", T2)):
        print("  %s" % tag)
        for o in range(0x0140, 0x02a0, 16):
            print("    %04x  %s" % (o, d[o:o + 16].hex(" ")))
        print()

    # 2. Non-FF bytes in 0x3dc0-0x3fc0, all tags (this block is mostly 0xFF).
    print("== non-FF bytes in 0x3dc0-0x3fc0 ==")
    for tag, d in (("T0", T0), ("T1", T1), ("T2", T2)):
        nz = [(o, d[o]) for o in range(0x3dc0, 0x3fc0) if d[o] != 0xFF]
        print("  %s : %d non-FF bytes" % (tag, len(nz)))
        for o, v in nz:
            print("     0x%04x = %02x" % (o, v))
        print()

    # 3. Is 0x3dc0 a bitfield? count set bits per tag.
    for tag, d in (("T0", T0), ("T1", T1), ("T2", T2)):
        setbits = sum(bin(d[o]).count("1") for o in range(0x3dc0, 0x3fc0))
        ffbytes = sum(1 for o in range(0x3dc0, 0x3fc0) if d[o] == 0xFF)
        print("  %s 0x3dc0: setbits=%d  FFbytes=%d/512" % (tag, setbits, ffbytes))

    # 4. Where is the cleared counter and does a per-scenario bitfield exist
    #    near 0x0180? Dump 0x0170-0x01a0 all tags.
    print("\n== 0x0170-0x01a0 (possible small bitfield near counter) ==")
    for tag, d in (("T0", T0), ("T1", T1), ("T2", T2)):
        print("  %s  %s" % (tag, d[0x0170:0x01a0].hex(" ")))


if __name__ == "__main__":
    main()
