#!/usr/bin/env python3
"""Deep-dive OPTION (2560B): full hexdump + candidate Full-Open flag bytes.

OPTION layout from earlier scan:
  0x00-0x5F mostly zero except @0x1C,@0x20 (save markers?)
  0x60-0x9F settings block (audio/volumes etc.)
  0xA0-0x1CF sparse flags?
  0x1D0-0x24F more settings?
  0x880-0x95F progress-ish values (mirrors GAMEDATA tail?)
We need: which bytes change when Full-Open + Option Save happens.
Without a before/after pair, map every nonzero byte + zero gaps that
look like flag arrays (runs of 00/01 or FF-padded slots).
"""
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

O = Path(r"D:\Video_Game\Emulator\RPCS3\dev_hdd0\home\00000001\savedata\NPJB00558-GAMEDATA-\OPTION").read_bytes()
print(f"OPTION len={len(O)}")
print("== full 32B-row hexdump (nonzero rows only) ==")
for off in range(0, len(O), 32):
    chunk = O[off:off+32]
    if any(chunk):
        h = " ".join(f"{b:02x}" for b in chunk)
        a = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        print(f"@{off:04x}: {h}  |{a}|")
print()
print("== byte-value histogram ==")
from collections import Counter
c = Counter(O)
for v, n in c.most_common(20):
    print(f"  {v:#04x} ({v:3d}) x{n}")
print()
print("== runs of 0x01 bytes (typical flag-set) ==")
i = 0
while i < len(O):
    if O[i] == 1:
        j = i
        while j < len(O) and O[j] == 1:
            j += 1
        print(f"  0x{i:04x}-0x{j-1:04x} len={j-i}")
        i = j
    else:
        i += 1
print("== runs of 0xFF bytes ==")
i = 0
while i < len(O):
    if O[i] == 0xFF:
        j = i
        while j < len(O) and O[j] == 0xFF:
            j += 1
        print(f"  0x{i:04x}-0x{j-1:04x} len={j-i}")
        i = j
    else:
        i += 1
