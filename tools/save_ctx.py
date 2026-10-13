#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump hex context around every changed offset from the T0->T1 scenario-clear
diff, for GAMEDATA and OPTION. Read-only. Snapshots live in tools/work/snaps/."""
import os

SNAP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "tools", "work", "snaps")

GD_OFF = [0x63, 0x73, 0x27b, 0x1187, 0x11c7, 0x142f, 0x146f, 0x2123, 0x2923]
OP_OFF = [0x1e3, 0x906, 0x946]


def load(tag, name):
    p = os.path.join(SNAP, tag, name + ".bin")
    return open(p, "rb").read()


def ctx(d, off, back=20, fwd=20):
    lo = max(0, off - back)
    hi = min(len(d), off + fwd + 1)
    return lo, hi, d[lo:hi]


def show(name, offs, t0, t1):
    print("==== %s  (T0 -> T1) ====" % name)
    for off in offs:
        lo, hi, a = ctx(t0, off)
        _, _, b = ctx(t1, off)
        # ascii
        def asc(x):
            return "".join(chr(c) if 32 <= c < 127 else "." for c in x)
        mark = off - lo
        print("@0x%04x  T0[%04x-%04x] %s" % (off, lo, hi - 1, a.hex(" ")))
        print("            marker        %s^" % (" " * (mark * 3)))
        print("            T1            %s   |%s|" % (b.hex(" "), asc(b)))
        print()


if __name__ == "__main__":
    g0, g1 = load("T0", "GAMEDATA"), load("T1", "GAMEDATA")
    o0, o1 = load("T0", "OPTION"), load("T1", "OPTION")
    show("GAMEDATA", GD_OFF, g0, g1)
    show("OPTION", OP_OFF, o0, o1)

    # structural check: is 0x2100 block a bitfield? show 0x2100-0x2140 both tags
    print("==== GAMEDATA 0x2100-0x2140 (flag region?) ====")
    for tag, d in (("T0", g0), ("T1", g1)):
        print("%s  %s" % (tag, d[0x2100:0x2140].hex(" ")))
    print("==== GAMEDATA 0x2900-0x2940 (mirror) ====")
    for tag, d in (("T0", g0), ("T1", g1)):
        print("%s  %s" % (tag, d[0x2900:0x2940].hex(" ")))
