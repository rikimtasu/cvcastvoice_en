#!/usr/bin/env python3
"""Where are scenario titles? Check D*_serif.info heads + list all title-like strings."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

a = cpk.load(str(C.ORIG))
by = {f.full_path: f for f in a.files}
for name in ["DATA/daihon/D000_serif.info", "DATA/daihon/D047_serif.info"]:
    d = a.file_bytes(by[name].toc_index)
    print(f"== {name} len={len(d)} ==")
    print(f"   head256 hex: {d[:256].hex()}")
    print(f"   head256 repr: {d[:256]!r}")
    strs = []
    for part in d.split(b"\x00"):
        try:
            t = part.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if len(t) >= 2:
            strs.append(t)
    print(f"   nul fields: {len(strs)}")
    for t in strs[:10]:
        print(f"     {t[:90]!r}")
