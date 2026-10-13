#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diff the controlled-experiment trial snapshots to find completion-tracking
bytes. BASE->T0->T1->T2 each add cleared scenarios (counter 99->117->125)."""
import os
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SNAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snaps")


def load(tag):
    p = os.path.join(SNAP, tag, "GAMEDATA.bin")
    if not os.path.exists(p):
        return None
    with open(p, "rb") as f:
        return f.read()


def diff(a, b, na, nb):
    da, db = T[a], T[b]
    n = min(len(da), len(db))
    ds = [i for i in range(n) if da[i] != db[i]]
    print("\n== %s -> %s : %d byte diffs ==" % (na, nb, len(ds)))
    for i in ds[:80]:
        print("  0x%04x: %02x -> %02x" % (i, da[i], db[i]))
    return set(ds)


def main():
    global T
    T = {}
    for t in ("BASE", "T0", "T1", "T2"):
        d = load(t)
        if d:
            T[t] = d
        print(t, len(d) if d else None)
    acc = None
    for a, b in (("BASE", "T0"), ("T0", "T1"), ("T1", "T2")):
        if a in T and b in T:
            ds = diff(a, b, a, b)
            if acc is None:
                acc = ds
            else:
                acc |= ds
    if acc:
        print("\n== union of all changed offsets: %d ==" % len(acc))
        print(" ", " ".join("0x%x" % o for o in sorted(acc)))


if __name__ == "__main__":
    main()
