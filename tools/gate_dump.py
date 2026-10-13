#!/usr/bin/env python3
"""Dump the 3 sakuhin001 records (32B stride) + entry payloads they point to."""
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

a = cpk.load(str(C.ORIG))
by = {f.full_path: f for f in a.files}
d = a.file_bytes(by["DATA/sakuhin/sakuhin001.pac"].toc_index)
print(f"len={len(d)}")
for r in range(3):
    o = 16 + r * 32
    rec = d[o:o+32]
    print(f"== record {r} @{o:#06x} hex={rec.hex()} ==")
    print(f"   u32le: {[struct.unpack('<I', rec[i:i+4])[0] for i in range(0, 32, 4)]}")
    print(f"   u16le: {[struct.unpack('<H', rec[i:i+2])[0] for i in range(0, 32, 2)]}")
# what follows the 3 records? dump next 128B
print(f"after records @{16+96:#06x}: {d[16+96:16+96+128].hex()}")
# entry payloads: first u32 of each record as offset?
for r in range(3):
    o = 16 + r * 32
    rec = d[o:o+32]
    vals = [struct.unpack("<I", rec[i:i+4])[0] for i in range(0, 32, 4)]
    for v in vals:
        if 0 < v < len(d):
            print(f"  rec{r} val {v:#x} -> bytes: {d[v:v+48].hex()}")
            break
