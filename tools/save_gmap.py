#!/usr/bin/env python3
"""GAMEDATA structure map: find scenario-unlock flag arrays.

19,904 B. Known: header-ish 0x00-0xBF, flag blocks with
01 31 00 00 01 29 + FF runs at 0xC0/0x280/0x2C0, text .info
echo around 0x140-0x1FF, second block copy at 0x6xx-0x7xx,
progress counters 0xFC0+, tail mirror of OPTION 0x880-0x95F.
Goal: locate per-scenario open bits (expect ~100+ scenario slots
for Produce + Casting/Album lists).
"""
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

G = Path(r"D:\Video_Game\Emulator\RPCS3\dev_hdd0\home\00000001\savedata\NPJB00558-GAMEDATA-\GAMEDATA").read_bytes()
print(f"GAMEDATA len={len(G)}")

print("== 64B rows: nonzero count + first 32B hex ==")
for off in range(0, len(G), 64):
    chunk = G[off:off+64]
    nz = sum(1 for b in chunk if b)
    if nz == 0:
        continue
    print(f"@{off:05d} 0x{off:04x} nz={nz:2d} {chunk[:32].hex()}")
    if nz <= 64:
        print(f"         {' '.join(f'{b:02x}' for b in chunk[:32])}")

print()
print("== FF-run map (FF = unlocked/open in flag blocks?) ==")
i = 0
while i < len(G):
    if G[i] == 0xFF:
        j = i
        while j < len(G) and G[j] == 0xFF:
            j += 1
        print(f"  FF 0x{i:04x}-0x{j-1:04x} len={j-i}")
        i = j
    else:
        i += 1

print()
print("== 00-gap map (gaps >= 64 = unfilled flag/progress slots?) ==")
i = 0
while i < len(G):
    if G[i] == 0:
        j = i
        while j < len(G) and G[j] == 0:
            j += 1
        if j - i >= 64:
            print(f"  00 0x{i:04x}-0x{j-1:04x} len={j-i}")
        i = j
    else:
        i += 1
