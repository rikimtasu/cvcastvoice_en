#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find all '01 <count>' group records and test whether their counts sum to the
cleared counter @0x143. This tells us if 0x143 is a derived total or independent.

We scan the primary buffer (0x00-0x1400) for the pattern [.., 01, NN, ..] at the
0xc2/0x102/0x2a2 style positions (tag 01 at even offsets followed by a count).
"""
import os
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SNAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snaps")


def load(tag):
    with open(os.path.join(SNAP, tag, "GAMEDATA.bin"), "rb") as f:
        return f.read()


def find_groups(d, lo, hi):
    """Find tag-01 records: byte==1 followed by a count that is not 0/1 and is
    followed by a plausible field. Heuristic: 01 NN where NN in 2..250."""
    out = []
    for o in range(lo, hi):
        if d[o] == 0x01:
            nn = d[o + 1] if o + 1 < hi else None
            if nn is not None and 2 <= nn <= 250:
                out.append((o, nn))
    return out


def main():
    T = {t: load(t) for t in ("BASE", "T0", "T1", "T2")}
    for t in ("BASE", "T0"):
        d = T[t]
        g = find_groups(d, 0x00, 0x1400)
        s = sum(nn for _, nn in g)
        print("%s: counter@0x143=%d  #01-records=%d  sum(counts)=%d"
              % (t, d[0x143], len(g), s))
        print("   records:", [(hex(o), nn) for o, nn in g][:20])

    # Is 0x143 the SUM of 0xc3-style group counts? Those are at 0xc2,0x102,0x2a2,0x2e2
    print("\n== known group-count bytes (tag01 at 0xc2/0x102/0x2a2/0x2e2) ==")
    for t in ("BASE", "T0", "T1", "T2"):
        d = T[t]
        vals = [(hex(o), d[o + 1]) for o in (0xc2, 0xe2, 0x102, 0x2a2, 0x2c2, 0x2e2)]
        print("  %-5s %s  sum=%d  counter=%d"
              % (t, vals, sum(v for _, v in vals), d[0x143]))


if __name__ == "__main__":
    main()
