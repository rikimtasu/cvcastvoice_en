#!/usr/bin/env python3
"""Hunt u16 ID-lists: 0xFFFF=empty, valid IDs = unlocked scenarios/chars.

Your count is 33, so find every u16be/u16le array with ~33 valid entries.
Also maps all FF-desert sublists in GAMEDATA.
"""
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(r"D:\Video_Game\Emulator\RPCS3\dev_hdd0\home\00000001\savedata\NPJB00558-GAMEDATA-")
G = (BASE / "GAMEDATA").read_bytes()
print(f"GAMEDATA len={len(G)}")

def scan_u16(d, endian, label):
    print(f"== {label} ({endian}) valid-list hunt ==")
    # sliding 64-entry windows? Instead: find all FF runs then parse surroundings
    # Simpler: parse whole file as u16 array, then find contiguous runs of valid (!=0,!=FFFF)
    n = len(d) // 2
    fmt = ">H" if endian == "be" else "<H"
    vals = [struct.unpack(fmt, d[i*2:i*2+2])[0] for i in range(n)]
    # find runs of valid (not 0x0000, not 0xFFFF)
    i = 0
    runs = []
    while i < n:
        if vals[i] not in (0x0000, 0xFFFF):
            j = i
            while j < n and vals[j] not in (0x0000, 0xFFFF):
                j += 1
            # also include leading zeros? no, just valid run
            runs.append((i*2, j-i, vals[i:j][:12]))
            i = j
        else:
            i += 1
    # filter interesting: runs with 5+ entries (scenario/char lists)
    for off, ln, preview in runs:
        mark = " <-- 25-45 entries? candidate for 33" if 20 <= ln <= 50 else ""
        if ln >= 5:
            print(f"  @{off:#06x} len={ln:3d} {preview}{mark}")

scan_u16(G, "be", "GAMEDATA")
print()
# also OPTION tail 0x880-0x95F mirrors GAMEDATA?
O = (BASE / "OPTION").read_bytes()
print(f"OPTION len={len(O)}")
# dump OPTION 0x880+ as u16be valid runs
n = len(O) // 2
vals = [struct.unpack(">H", O[i*2:i*2+2])[0] for i in range(n)]
print("OPTION u16be valid runs >=3:")
i = 0
while i < n:
    if vals[i] not in (0, 0xFFFF):
        j = i
        while j < n and vals[j] not in (0, 0xFFFF):
            j += 1
        if j - i >= 3:
            print(f"  @{i*2:#06x} len={j-i} {vals[i:j][:16]}")
        i = j
    else:
        i += 1
