#!/usr/bin/env python3
"""Scan EBOOT for savedata field names + flag-related strings."""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EBOOT = Path(r"D:\Video_Game\Emulator\RPCS3\games\CV Casting Voice [BLJS10259]\PS3_GAME\USRDIR\EBOOT.BIN")
d = EBOOT.read_bytes()
print(f"EBOOT {len(d)} bytes")

# ascii runs
runs = []
cur = bytearray()
start = 0
for i, b in enumerate(d):
    if 32 <= b < 127:
        if not cur:
            start = i
        cur.append(b)
    else:
        if len(cur) >= 4:
            runs.append((start, bytes(cur).decode()))
        cur = bytearray()
print(f"ascii runs>=4: {len(runs)}")

KEYS = ["GAMEDATA", "CASTDATA", "OPTION", "OPEN", "CLEAR", "FULL",
        "SAVE", "LOAD", "DLC", "CHARA", "SCENARIO", "PRODUCE",
        "CASTING", "AFRECO", "RECORDING", "ALBUM", "FLAG",
        "NPJB00558", "CASTLIST"]
for k in KEYS:
    hits = [(o, s) for o, s in runs if k in s]
    print(f"== {k}: {len(hits)} ==")
    for o, s in hits[:15]:
        print(f"  @{o:#08x} {s[:110]!r}")

# savedata dir names look like *-0 / GAMEDATA- : find all *-like
print("== LIST-like / -0 / dir patterns ==")
for o, s in runs:
    if ("LIST" in s or "DATA-" in s or s.startswith("NPJB")) and len(s) < 60:
        print(f"  @{o:#08x} {s!r}")
