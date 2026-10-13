#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Checksum hypothesis tester for GAMEDATA.

The T0->T1 scenario-clear diff changed 4 "value" bytes that appear in MIRRORED
pairs (0x1187/0x142f, 0x11c7/0x146f). Before any hand-edit we must know whether
GAMEDATA carries a checksum the game validates on load -- otherwise the edit is
rejected / the save resets.

Read-only. Tests cumulative sum8 / xor8 checksum schemes: a checksum byte at
offset X satisfies  data[X] == f(data[0:X]). We scan both T0 and T1 and keep
only offsets valid in BOTH (robust positions).
"""
import os

SNAP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "tools", "work", "snaps")


def load(tag, name):
    return open(os.path.join(SNAP, tag, name + ".bin"), "rb").read()


def find_sum(data):
    """offsets X where data[X] == (sum(data[0:X]) & 0xff)"""
    hits = []
    s = 0
    for i in range(len(data)):
        if data[i] == (s & 0xff):
            hits.append(i)
        s += data[i]
    return set(hits)


def find_xor(data):
    hits = []
    x = 0
    for i in range(len(data)):
        if data[i] == x:
            hits.append(i)
        x ^= data[i]
    return set(hits)


def find_sum16(data):
    """offsets X (2-aligned) where u16le at X == (sum(data[0:X]) & 0xffff)"""
    hits = []
    s = 0
    for i in range(0, len(data) - 1, 2):
        v = data[i] | (data[i + 1] << 8)
        if v == (s & 0xffff):
            hits.append(i)
        s += data[i] + data[i + 1]
    return set(hits)


def crc32_scan(data):
    """offsets X where u32le at X == zlib.crc32(data[0:X]) (checksum-before style)."""
    import zlib
    import struct
    hits = []
    run = 0
    for i in range(0, len(data) - 3, 4):
        run = zlib.crc32(data[i:i + 4], run)
        v = struct.unpack_from("<I", data, i + 4)[0] if i + 8 <= len(data) else None
        # check crc of everything BEFORE this stored dword equals the dword at i
    # simpler: incremental crc of prefix, compare to dword at each offset
    hits = []
    c = 0
    for i in range(0, len(data) - 3):
        # dword at i vs crc of prefix [0:i]
        if struct.unpack_from("<I", data, i)[0] == (c & 0xffffffff):
            hits.append(i)
        c = zlib.crc32(data[i:i + 1], c)
    return set(hits)


if __name__ == "__main__":
    g0, g1 = load("T0", "GAMEDATA"), load("T1", "GAMEDATA")
    print("GAMEDATA len:", len(g0))

    for label, fn in (("sum8", find_sum), ("xor8", find_xor), ("sum16", find_sum16),
                      ("crc32", crc32_scan)):
        both = fn(g0) & fn(g1)
        # ignore trivially-common low offsets
        interesting = sorted(x for x in both if x > 0x40)
        print("\n== %s: offsets valid in BOTH T0&T1 (count=%d) ==" % (label, len(interesting)))
        # show a compact view
        print("   ", [hex(x) for x in interesting[:60]])

    # Also: are the 4 changed value-bytes reproducible as sum of the OTHER copy?
    # mirror deltas
    print("\n== changed value bytes & their mirrors ==")
    for off, mir in ((0x1187, 0x142f), (0x11c7, 0x146f), (0x2123, 0x2923)):
        print("  0x%04x: %02x->%02x   mirror 0x%04x: %02x->%02x" %
              (off, g0[off], g1[off], mir, g0[mir], g1[mir]))
