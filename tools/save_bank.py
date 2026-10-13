#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump the GAMEDATA record-bank structure (T1 baseline) as u32-BE records so we
can see every [counter][field] slot and which fields are already 0xFFFFFFFF.
Read-only."""
import os
import struct

SNAP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "tools", "work", "snaps")


def load(tag, name):
    return open(os.path.join(SNAP, tag, name + ".bin"), "rb").read()


def u32be(d, o):
    return struct.unpack_from(">I", d, o)[0]


if __name__ == "__main__":
    g1, g2 = load("T1", "GAMEDATA"), load("T2", "GAMEDATA")
    print("GAMEDATA len", len(g1))
    print("\n== record bank A: 0x00c0-0x0330, u32 BE, 8-byte records ==")
    for o in range(0x00c0, 0x0330, 8):
        a0, a1 = u32be(g1, o), u32be(g1, o + 4)
        b0, b1 = u32be(g2, o), u32be(g2, o + 4)
        chg = "  <-- CHANGED" if (a0, a1) != (b0, b1) else ""
        print("  0x%04x  T1 [%10d %10d]  T2 [%10d %10d]%s" %
              (o, a0, a1, b0, b1, chg))

    # count how many 4-byte slots in the bank are NOT 0xffffffff in T1
    print("\n== field-slot census in bank A (0x00c0-0x0330), u32 BE ==")
    notff = []
    for o in range(0x00c0, 0x0330, 4):
        v = u32be(g1, o)
        if v != 0xffffffff:
            notff.append((o, v))
    print("  non-0xFFFFFFFF u32 slots (%d):" % len(notff))
    for o, v in notff:
        print("    0x%04x = %d (0x%08x)  T2=%d" % (o, v, v, u32be(g2, o)))
