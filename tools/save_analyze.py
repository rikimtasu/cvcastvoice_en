#!/usr/bin/env python3
"""Analyze CV Casting Voice savedata structure (RPCS3, decrypted)."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(r"D:\Video_Game\Emulator\RPCS3\dev_hdd0\home\00000001\savedata")

def dump(path):
    d = Path(path).read_bytes()
    print(f"== {path} len={len(d)} ==")
    # nonzero map: 64-byte rows, mark * if any nonzero
    for off in range(0, len(d), 64):
        chunk = d[off:off+64]
        if any(chunk):
            nz = sum(1 for b in chunk if b)
            print(f"  @{off:05d} (0x{off:04x}) nz={nz:2d} hex={chunk.hex()}")
            # ascii preview
            txt = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            print(f"    |{txt}|")

for p in sorted((BASE / "NPJB00558-GAMEDATA-").glob("*")):
    if p.suffix.upper() in (".PNG",):
        print(f"== {p.name} (image, {p.stat().st_size} bytes, skipped) ==")
        continue
    if p.name == "PARAM.SFO":
        print(f"== {p.name} ({p.stat().st_size} bytes) ==")
        d = p.read_bytes()
        print(f"   hex[0:128]={d[:128].hex()}")
        try:
            print(f"   ascii scrub: {d.decode('utf-8', 'replace')[:600]!r}")
        except Exception as e:
            print(e)
        continue
    dump(str(p))

for p in sorted((BASE / "NPJB00558-CASTLIST-0").glob("*")):
    if p.suffix.upper() in (".PNG",):
        print(f"== {p.name} (image skipped) ==")
        continue
    if p.name == "PARAM.SFO":
        d = p.read_bytes()
        print(f"== CASTLIST PARAM.SFO hex[0:128]={d[:128].hex()}")
        continue
    dump(str(p))
