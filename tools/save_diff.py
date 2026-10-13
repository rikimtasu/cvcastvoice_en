#!/usr/bin/env python3
"""Diff GAMEDATA structure: find menu-flag vs produce-progress regions."""
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(r"D:\Video_Game\Emulator\RPCS3\dev_hdd0\home\00000001\savedata")
G = (BASE / "NPJB00558-GAMEDATA-" / "GAMEDATA").read_bytes()
O = (BASE / "NPJB00558-GAMEDATA-" / "OPTION").read_bytes()
C = (BASE / "NPJB00558-CASTLIST-0" / "CASTDATA.DAT").read_bytes()
print(f"GAMEDATA={len(G)} OPTION={len(O)} CASTDATA={len(C)}")

# u32 histogram of GAMEDATA: which values appear
from collections import Counter
words = Counter()
for off in range(0, len(G) - 4, 4):
    w = struct.unpack(">I", G[off:off+4])[0]
    if w:
        words[w] += 1
print("-- top u32be values in GAMEDATA --")
for w, n in words.most_common(30):
    print(f"  {w:#010x} ({w:5d}) x{n}")

# strings inside GAMEDATA
print("-- ascii runs >=4 in GAMEDATA --")
cur = b""
for i, b in enumerate(G):
    if 32 <= b < 127:
        cur += bytes([b])
    else:
        if len(cur) >= 4:
            print(f"  @{i-len(cur):#06x}: {cur!r}")
        cur = b""
if len(cur) >= 4:
    print(f"  @tail: {cur!r}")

# OPTION nonzero map
print("-- OPTION nonzero u32be --")
for off in range(0, len(O), 4):
    w = struct.unpack(">I", O[off:off+4])[0]
    if w:
        print(f"  @{off:#06x} = {w:#010x} ({w})")
