#!/usr/bin/env python3
"""Which D-scenarios are your 33? Intersect save progress vs D headers.

GAMEDATA @0x140-0x1FF region holds Japanese text echo + small ints
(0x63=99? 0x01? 0x7d=125?). Dump 0x140-0x200 as u32 + text to see
if open-scenario IDs are listed there.
"""
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

G = Path(r"D:\Video_Game\Emulator\RPCS3\dev_hdd0\home\00000001\savedata\NPJB00558-GAMEDATA-\GAMEDATA").read_bytes()
print("== 0x140-0x200 u32be ==")
for o in range(0x140, 0x200, 16):
    vals = [struct.unpack(">I", G[i:i+4])[0] for i in range(o, o+16, 4)]
    print(f"  @{o:#06x} {' '.join(f'{v:#010x}({v})' for v in vals)}")
print("== 0x140-0x200 u32le ==")
for o in range(0x140, 0x200, 16):
    vals = [struct.unpack("<I", G[i:i+4])[0] for i in range(o, o+16, 4)]
    print(f"  @{o:#06x} {' '.join(f'{v}' for v in vals)}")
print("== text in 0x140-0x200 ==")
seg = G[0x140:0x200]
print(f"  repr: {seg!r}")
