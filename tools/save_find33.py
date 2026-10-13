#!/usr/bin/env python3
"""Search GAMEDATA+OPTION for the value 33 (your Album count) in all encodings."""
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(r"D:\Video_Game\Emulator\RPCS3\dev_hdd0\home\00000001\savedata\NPJB00558-GAMEDATA-")
G = (BASE / "GAMEDATA").read_bytes()
O = (BASE / "OPTION").read_bytes()

for label, d in (("GAMEDATA", G), ("OPTION", O)):
    print(f"== {label} len={len(d)} ==")
    for off in range(len(d) - 4):
        u32be = struct.unpack(">I", d[off:off+4])[0]
        u32le = struct.unpack("<I", d[off:off+4])[0]
        u16be = struct.unpack(">H", d[off:off+2])[0]
        u16le = struct.unpack("<H", d[off:off+2])[0]
        hits = []
        if u32be == 33:
            hits.append("u32be=33")
        if u32le == 33:
            hits.append("u32le=33")
        if u16be == 33:
            hits.append("u16be=33")
        if u16le == 33:
            hits.append("u16le=33")
        if hits and (off % 4 == 0 or "16" in hits[0]):
            # only report aligned u32 + any u16 to keep noise down
            if "u32" in hits[0] and off % 4 != 0:
                continue
            ctx = d[max(0, off-8):off+12].hex()
            print(f"  @{off:#06x} ({off:5d}) {'/'.join(hits)} ctx=...{ctx}...")
