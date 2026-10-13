#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract ASCII/UTF-8 strings from the game EBOOT (SCE SELF) and grep for
anything that reveals the GAMEDATA save layout or the 名鑑 trust formula
(e.g. field names, format strings, actor/trust keywords). Read-only.
"""
import os
import re
import sys

EBOOT = (r"D:\Video_Game\Emulator\RPCS3\games\CV Casting Voice [BLJS10259]"
         r"\PS3_GAME\USRDIR\EBOOT.BIN")

KEYWORDS = [
    "GAMEDATA", "save", "Save", "SAVE", "trust", "Trust", "信頼", "shinrai",
    "meikan", "名鑑", "seiyu", "声優", "scenario", "Scenario", "clear", "Clear",
    "fans", "money", "affection", "love", "rank", "Rank", "level", "Level",
    ".dat", ".bin", "savedata", "cellSave", "cellFsOpen", "sys_save",
]


def extract_strings(data, minlen=4):
    # ASCII runs
    for m in re.finditer(rb"[\x20-\x7e]{%d,}" % minlen, data):
        yield m.start(), m.group().decode("ascii", "ignore")


def main():
    if not os.path.exists(EBOOT):
        print("EBOOT not found:", EBOOT)
        return
    data = open(EBOOT, "rb").read()
    print("EBOOT size:", len(data), "magic:", data[:4])

    hits = []
    for off, s in extract_strings(data):
        low = s
        if any(k in low for k in KEYWORDS):
            hits.append((off, s))
    print("keyword string hits:", len(hits))
    for off, s in hits[:200]:
        print("  0x%08x  %s" % (off, s[:120]))


if __name__ == "__main__":
    sys.exit(main())
