#!/usr/bin/env python3
"""Bitmask hunt: find flag arrays holding ~33 set entries (your Album count).

Checks every window as: bytes==01 count, u32==1 count, bits-set count,
u16!=FFFF/0 count. Reports windows where count is 25-45.
"""
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(r"D:\Video_Game\Emulator\RPCS3\dev_hdd0\home\00000001\savedata\NPJB00558-GAMEDATA-")
G = (BASE / "GAMEDATA").read_bytes()
print(f"GAMEDATA len={len(G)}")

def popcnt(b):
    return bin(b).count("1")

# 1) global bit popcount per 256B block
print("== popcount per 256B block ==")
for off in range(0, len(G), 256):
    chunk = G[off:off+256]
    bits = sum(popcnt(b) for b in chunk)
    nz = sum(1 for b in chunk if b)
    if bits:
        print(f"  @{off:#06x} bits_set={bits:4d} nz_bytes={nz:3d}")

# 2) byte==0x01 count per 256B block
print("== byte==0x01 count per 256B block ==")
for off in range(0, len(G), 256):
    chunk = G[off:off+256]
    c = sum(1 for b in chunk if b == 1)
    if c >= 10:
        print(f"  @{off:#06x} ones={c}")

# 3) u32==1 count per 512B block
print("== u32be==1 count per 512B block ==")
for off in range(0, len(G), 512):
    c = 0
    for i in range(off, min(off+512, len(G)-4), 4):
        if struct.unpack(">I", G[i:i+4])[0] == 1:
            c += 1
    if c >= 5:
        print(f"  @{off:#06x} u32==1 x{c}")

# 4) detailed: 0x1300-0x1500 region (0x1380 block + 0x1340 counter 0x7d=125?)
print("== 0x1300-0x1500 u32be dump ==")
for off in range(0x1300, 0x1500, 16):
    vals = [struct.unpack(">I", G[i:i+4])[0] for i in range(off, off+16, 4)]
    if any(vals):
        print(f"  @{off:#06x} {' '.join(f'{v:#010x}' for v in vals)}")
