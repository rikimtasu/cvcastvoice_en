#!/usr/bin/env python3
"""Dump scenario/char ID lists: GAMEDATA blocks + sakuhin PAC headers."""
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

G = Path(r"D:\Video_Game\Emulator\RPCS3\dev_hdd0\home\00000001\savedata\NPJB00558-GAMEDATA-\GAMEDATA").read_bytes()

def dump_ids(label, off, nwords=16):
    print(f"== {label} @{off:#06x} ==")
    for i in range(nwords):
        w = struct.unpack(">I", G[off+i*4:off+i*4+4])[0]
        print(f"  +{i*4:03d} @{off+i*4:#06x} {w:#010x} ({w})")

dump_ids("GAMEDATA blk1", 0xC0, 20)
dump_ids("GAMEDATA blk1b", 0x100, 20)
dump_ids("GAMEDATA blk2 (copy)", 0x2C0, 20)
dump_ids("GAMEDATA blk3", 0x1380, 16)
dump_ids("GAMEDATA tail-FF head", 0x3DC0, 8)

# sakuhin pac headers (DLC scenario metadata?)
ROOT = C.ROOT
for p in sorted((ROOT / "dlc" / "dec").glob("DLC_D*.cpk"))[:1]:
    a = cpk.load(str(p))
    for f in a.files:
        if "sakuhin" in f.full_path.lower():
            d = a.file_bytes(f.toc_index)
            print(f"== {p.stem} {f.full_path} len={len(d)} head hex ==")
            print(f"   {d[:64].hex()}")
            # try u32le/be
            print("   u32be:", [struct.unpack('>I', d[i:i+4])[0] for i in range(0, 32, 4)])
            print("   u32le:", [struct.unpack('<I', d[i:i+4])[0] for i in range(0, 32, 4)])
            break
    break

# base sakuhin?
a = cpk.load(str(C.ORIG))
saks = [f for f in a.files if "sakuhin" in f.full_path.lower()]
print(f"base sakuhin files: {len(saks)}")
for f in saks[:3]:
    d = a.file_bytes(f.toc_index)
    print(f"  {f.full_path} len={len(d)} head={d[:48].hex()}")
