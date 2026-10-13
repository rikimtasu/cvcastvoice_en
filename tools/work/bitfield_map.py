#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Map the completion bitfield regions and the per-record stats.

T0->T1 single clear toggled 0x2123 (00->20) and its mirror 0x2923. That's a bit
in a flag region. We scan the whole file for 8-byte-aligned words that differ
across trials and classify:
  - counters (monotonic within trials)
  - flag bits (toggle)
Also decode the 0x2100 and 0x2900 regions fully for each trial to see the
bitfield layout, and the 0x2000-0x2a00 span generally.
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
    # classify every differing offset across the FULL sequence
    offs = set()
    for a, b in (("BASE", "T0"), ("T0", "T1"), ("T1", "T2")):
        for i in range(len(T[a])):
            if T[a][i] != T[b][i]:
                offs.add(i)
    offs = sorted(offs)
    print("total differing offsets across all transitions:", len(offs))

    # group into contiguous-ish clusters (gap <= 4)
    clusters = []
    cur = [offs[0]]
    for o in offs[1:]:
        if o - cur[-1] <= 4:
            cur.append(o)
        else:
            clusters.append(cur)
            cur = [o]
    clusters.append(cur)
    print("clusters:", len(clusters))
    print("\n== clusters (start-end, per-trial bytes) ==")
    for c in clusters:
        s, e = c[0], c[-1]
        line = []
        for t in ("BASE", "T0", "T1", "T2"):
            seq = " ".join("%02x" % T[t][o] for o in c[:8])
            line.append("%s:[%s]" % (t, seq))
        print("  0x%04x-0x%04x (%d): %s" % (s, e, len(c), "  ".join(line)))


if __name__ == "__main__":
    main()
