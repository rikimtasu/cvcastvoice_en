#!/usr/bin/env python3
"""D-info headers: compare early (open) vs late (locked) scenarios.

Your 33 open vs 100 total. If D000-D032ish are open and the rest locked,
diff their headers for a rank/trust/category gate field.
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
names = sorted(p for p in by if "/D" in p and p.endswith("_serif.info") and "dummy" not in p)
print(f"D scenario files: {len(names)}")
for nm in names[:6] + names[30:36] + names[-4:]:
    d = a.file_bytes(by[nm].toc_index)
    h = [struct.unpack("<I", d[i:i+4])[0] for i in range(0, 32, 4)]
    print(f"{nm.split('/')[-1]:22s} len={len(d):5d} hdr8={h}")
