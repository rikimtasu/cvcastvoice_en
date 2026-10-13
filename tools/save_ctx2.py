#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Context dump for T1->T2 (second scenario clear). Shows structure around the
changed regions in GAMEDATA and OPTION, side by side, with '^' marking changed
bytes. Read-only; snapshots in tools/work/snaps/."""
import os

SNAP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "tools", "work", "snaps")

GD = [0x63, 0x73, 0xa7, 0xc3, 0xe3, 0x103, 0x143, 0x147, 0x188, 0x198, 0x1ab,
      0x206, 0x273, 0x27b, 0x2a3, 0x2c3, 0x2e3, 0x323, 0xfc3, 0xfcf, 0x1117,
      0x117b, 0x11a6, 0x11c6, 0x13bf, 0x1423, 0x144e, 0x146e, 0x2011, 0x2013,
      0x20fd, 0x21b9, 0x21bf, 0x21c9, 0x2811, 0x2813, 0x28fd, 0x29b9, 0x29bf,
      0x29c9, 0x3f5b]
OP = [0x6f, 0xd1, 0xd3, 0x27f, 0x289, 0x897, 0x8fb, 0x927, 0x947, 0x95a]

# regions to dump in full (start,end inclusive)
REGIONS = [
    ("counter/record bank A", 0x00c0, 0x0150),
    ("counter/record bank B", 0x02a0, 0x0330),
    ("trust region A", 0x1100, 0x1180),
    ("trust region B(mirror)", 0x1400, 0x1480),
    ("flag region 0x2000", 0x2000, 0x21d0),
    ("flag mirror 0x2800", 0x2800, 0x29d0),
    ("tail 0x3f40", 0x3f40, 0x3fc0),
]


def load(tag, name):
    return open(os.path.join(SNAP, tag, name + ".bin"), "rb").read()


def asc(x):
    return "".join(chr(c) if 32 <= c < 127 else "." for c in x)


def region(d1, d2, lo, hi, name):
    print("==== %s  0x%04x-0x%04x ====" % (name, lo, hi))
    for o in range(lo, hi + 1, 16):
        end = min(o + 16, hi + 1)
        a, b = d1[o:end], d2[o:end]
        mark = "".join("^" if a[i] != b[i] else " " for i in range(len(a)))
        if a != b:
            print("  %04x  T1 %s" % (o, a.hex(" ")))
            print("        ^^ %s" % mark)
            print("        T2 %s   |%s|" % (b.hex(" "), asc(b)))
        else:
            print("  %04x  == %s   |%s|" % (o, a.hex(" "), asc(a)))
    print()


if __name__ == "__main__":
    g1, g2 = load("T1", "GAMEDATA"), load("T2", "GAMEDATA")
    for name, lo, hi in REGIONS:
        region(g1, g2, lo, hi, name)

    # focused 5-byte records: counter + trailing u32 that went to 0xffffffff
    print("==== [counter][u32->FF] record values ====")
    for off in (0xc3, 0xe3, 0x103, 0x2a3, 0x2c3, 0x2e3):
        def rec(d):
            return d[off - 3:off + 5]  # show a byte before + counter + 4 bytes
        print("  0x%04x  T1 %s   T2 %s" % (off, rec(g1).hex(" "), rec(g2).hex(" ")))
    print()
    print("==== changed value bytes & mirror pairs (offset, mirror@+0x2a8) ====")
    for off in GD:
        mir = off + 0x2a8
        if mir < len(g1) and g1[off] != g2[off]:
            mm = "(mirror 0x%04x also changed)" % mir if (mir < len(g1) and g1[mir] != g2[mir]) else ""
            print("  0x%04x: %02x->%02x  %s" % (off, g1[off], g2[off], mm))
