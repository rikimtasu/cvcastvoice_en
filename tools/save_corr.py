#!/usr/bin/env python3
"""Correlate 33 vs scenario structure: categories, sakuhin packs, D-files.

33 seen in Album list. Base has 48 sakuhin packs + 100 D-infos.
Hypothesis: Album list counts sakuhin entries (works), not D-files.
Check: how many sakuhin entries per pack? Do locked ones hide?
Also check D-file count field at head (04 00 00 00 ...).
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

# D000 head: parse first u32s
d = a.file_bytes(by["DATA/daihon/D000_serif.info"].toc_index)
print("D000 head u32le:", [struct.unpack("<I", d[i:i+4])[0] for i in range(0, 32, 4)])
print("D000 head u32be:", [struct.unpack(">I", d[i:i+4])[0] for i in range(0, 32, 4)])

# sakuhin index: which packs exist
import re
pacs = sorted(f.full_path for f in a.files if re.match(r".*sakuhin\d+\.pac", f.full_path))
print(f"base sakuhin packs: {len(pacs)}")
for p in pacs:
    dd = a.file_bytes(by[p].toc_index)
    print(f"  {p.split('/')[-1]} len={dd[8:12].hex()}? size={len(dd)}")
