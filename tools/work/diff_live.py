#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compare the CURRENT live GAMEDATA against the pre-install backups.

When the game loaded the fabricated save and the user browsed the声優名鑑,
the game (if it re-saved) wrote the TRUE trust/名鑑 state. Diffing current-live
vs the pre-install backup reveals exactly which bytes the engine treats as live
per-actor trust vs. static. Read-only.
"""
import os
import glob

SNAP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "work", "snaps")
RPCS3 = os.environ.get("CVC_RPCS3", r"D:\Video_Game\Emulator\RPCS3")
LIVE = os.path.join(RPCS3, "dev_hdd0", "home", "00000001", "savedata",
                    "NPJB00558-GAMEDATA-", "GAMEDATA")
FAB = os.path.join(SNAP, "GAMEDATA.fabricated")


def runs(a, b, label):
    out = []
    n = min(len(a), len(b))
    i = 0
    while i < n:
        if a[i] != b[i]:
            j = i
            while j < n and a[j] != b[j]:
                j += 1
            out.append((i, j))
            i = j
        else:
            i += 1
    print("== %s : %d changed runs ==" % (label, len(out)))
    for s, e in out:
        print("  0x%04x-0x%04x  A=%s  B=%s" % (s, e - 1, a[s:e].hex(" "), b[s:e].hex(" ")))
    return out


def main():
    if not os.path.exists(LIVE):
        print("live GAMEDATA not found:", LIVE)
        return
    live = open(LIVE, "rb").read()
    print("live len:", len(live))

    baks = sorted(glob.glob(os.path.join(SNAP, "fab_backups", "*", "GAMEDATA")))
    if baks:
        bak = open(baks[-1], "rb").read()
        print("\n#### LIVE  vs  LATEST BACKUP (%s) ####"
              % os.path.basename(os.path.dirname(baks[-1])))
        runs(bak, live, "backup->live")

    if os.path.exists(FAB):
        fab = open(FAB, "rb").read()
        print("\n#### FABRICATED  vs  LIVE (what the game rewrote) ####")
        runs(fab, live, "fab->live")

        # Focus on the trust region and the record bank.
        print("\n== trust region 0x1100-0x1200  fab vs live (u32 BE) ==")
        for o in range(0x1100, 0x1200, 4):
            fb = (fab[o] << 24) | (fab[o + 1] << 16) | (fab[o + 2] << 8) | fab[o + 3]
            lv = (live[o] << 24) | (live[o + 1] << 16) | (live[o + 2] << 8) | live[o + 3]
            if fb or lv:
                mark = "  <-- changed" if fb != lv else ""
                print("  0x%04x  fab=%3d  live=%3d%s" % (o, fb, lv, mark))


if __name__ == "__main__":
    main()
