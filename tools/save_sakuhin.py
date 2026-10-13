#!/usr/bin/env python3
"""Parse sakuhin PAC: which scenarios exist, what unlocks them (rank? char? DLC?).

sakuhin.pac (32B) = index; sakuhin001.pac (499KB) etc = entries.
Find per-scenario record: title JP, category, unlock condition.
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
idx = a.file_bytes(by["DATA/sakuhin/sakuhin.pac"].toc_index)
print(f"sakuhin.pac len={len(idx)} hex={idx.hex()}")
# entries: try each sakuhin0NN.pac header
import re
pacs = sorted(f.full_path for f in a.files if re.match(r".*sakuhin\d+\.pac", f.full_path))
print(f"sakuhinNNN count: {len(pacs)}")
for p in pacs[:4]:
    d = a.file_bytes(by[p].toc_index)
    print(f"== {p} len={len(d)} ==")
    print(f"   head128 hex: {d[:128].hex()}")
    # strings
    strs = []
    for part in d.split(b"\x00"):
        try:
            t = part.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if len(t) >= 2 and any("\u3040" <= c <= "\u30ff" or "\u4e00" <= c <= "\u9fff" for c in t):
            strs.append(t)
    print(f"   jp strings: {len(strs)}")
    for t in strs[:12]:
        print(f"     {t[:80]!r}")
