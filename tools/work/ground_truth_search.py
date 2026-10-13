#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ground-truth search: the live save shows 八尾 伊月 = 信頼度 4/10, 台本 20%.
If per-actor trust/scripts is STORED, the values 4/40 (trust) and 20/200 (20%)
must appear as her slot. We hunt for:
  * a per-actor array with a REGULAR stride (try every stride, report the best)
  * occurrences of the pair (trust, scripts) plausibly encoding (4,20)/(40,20)/
    (4,200) etc. at a consistent spacing
  * any region with exactly ~50 entries (actor count) of small values
Also re-derive the actor list from seiyubase to know how many CVs exist.
Read-only.
"""
import json
import os

SNAP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "work", "snaps")
PAC = os.path.join(SNAP, "..", "pac_names_detail.json")


def load(tag):
    return open(os.path.join(SNAP, tag, "GAMEDATA.bin"), "rb").read()


def u32be(d, o):
    return (d[o] << 24) | (d[o + 1] << 16) | (d[o + 2] << 8) | d[o + 3]


def main():
    live = open(os.path.join(SNAP, "BASE", "GAMEDATA.bin"), "rb").read()
    T2 = load("T2")
    n = len(live)

    # 1. Actor count from seiyubase (kanji 2-4 char names + kana readings).
    try:
        det = json.load(open(PAC, encoding="utf-8"))
        sy = det["DATA/daihon/seiyubase.pac"]
        # CV records look like short names (kanji) followed by kana reading.
        names = [r["str"] for r in sy if 2 <= len(r["str"]) <= 8]
        print("seiyubase short-string slots:", len(names))
    except Exception as ex:
        print("pac parse failed:", ex)

    # 2. Search for the literal trust/scripts values as u32 BE and u8.
    print("\n== literal value occurrences in live save ==")
    for label, val in (("trust=4(u8)", 4), ("scripts=20(u8)", 20),
                       ("trust=4(u32be)", None)):
        if val is None:
            continue
        offs = [hex(o) for o in range(n) if live[o] == val]
        print("  %-16s count=%d  first=%s" % (label, len(offs), offs[:12]))

    # 3. Best regular stride for a small-value per-actor array: for each stride
    #    and phase, count entries in 1..100; pick strides with a clean run.
    print("\n== stride scan: windows with >=30 small(1..100) values ==  ")
    best = []
    for stride in range(4, 80):
        for phase in range(0, stride):
            vals = [live[o] for o in range(phase, n - stride, stride)]
            small = sum(1 for v in vals if 1 <= v <= 100)
            if small >= 30:
                best.append((small, stride, phase, len(vals)))
    best.sort(reverse=True)
    for small, stride, phase, tot in best[:15]:
        print("  stride=%2d phase=%2d  small=%d / %d" % (stride, phase, small, tot))
    if not best:
        print("  (none)")

    # 4. Look for a run of consecutive small bytes (a packed per-actor block).
    print("\n== consecutive small(0..100) runs >= 20 bytes in live ==")
    i = 0
    while i < n:
        if 0 <= live[i] <= 100:
            j = i
            while j < n and 0 <= live[j] <= 100:
                j += 1
            if j - i >= 20:
                nz = sum(1 for o in range(i, j) if live[o] != 0)
                print("  0x%04x-0x%04x len=%d nonzero=%d  %s"
                      % (i, j - 1, j - i, nz, live[i:j].hex(" ")))
            i = j
        else:
            i += 1


if __name__ == "__main__":
    main()
