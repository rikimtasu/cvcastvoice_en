#!/usr/bin/env python3
"""sakuhin entries: split records, compare unlocked-vs-locked candidates.

sakuhin001: PACK(4) ver(4)=1 count(?) ... entries fixed-size?
Try: header 16B, then records. Find record stride by searching for
the repeating 8B marker seen in head128 (2a804000 d0124100 ...).
Then dump 2 records fully + diff them.
"""
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

# candidate marker from head
for m in (bytes.fromhex("2a804000d0124100"), bytes.fromhex("0e42a77000000000"),
          bytes.fromhex("18e1020080000000")):
    offs = []
    s = 0
    while True:
        i = d.find(m, s)
        if i < 0:
            break
        offs.append(i)
        s = i + 1
        if len(offs) > 12:
            break
    if offs:
        gaps = [b - a for a, b in zip(offs, offs[1:])]
        print(f"marker {m.hex()}: {len(offs)} hits first={offs[:8]} gaps={gaps[:8]}")

# header u32le full
print("hdr16 u32le:", [struct.unpack("<I", d[i:i+4])[0] for i in range(0, 16, 4)])
# try: count at +8? =3? then 3 entries? check sizes
for nm in ["DATA/sakuhin/sakuhin001.pac", "DATA/sakuhin/sakuhin039.pac",
           "DATA/sakuhin/sakuhin051.pac"]:
    dd = a.file_bytes(by[nm].toc_index)
    h = [struct.unpack("<I", dd[i:i+4])[0] for i in range(0, 16, 4)]
    print(f"{nm.split('/')[-1]} len={len(dd)} hdr={h}")
