#!/usr/bin/env python3
"""What does the scenario list actually cost? Count entries per category.

Screenshot (Album scenario list): Tales Abyss Type B 8/9/10,
Symphonia 1, CM x2, Anime x1 -- i.e. list is OPEN but SHORT.
Count: total scenarios in base + DLC, per sakuhin pack, to size the
flag array the save must hold.
"""
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

def count_info(path):
    a = cpk.load(str(path))
    infos = [(f.full_path, len(a.file_bytes(f.toc_index)))
             for f in a.files if f.full_path.lower().endswith(".info")]
    return a, infos

a, infos = count_info(C.ORIG)
print(f"BASE: {len(infos)} .info files")
# D-range = scenario infos? list names
dnames = sorted(p for p, _ in infos if "/D" in p.upper())
print(f"  D*.info scenario files: {len(dnames)}")
print(f"  first: {dnames[:5]}")
print(f"  last: {dnames[-5:]}")
# number the D range
import re
nums = []
for p in dnames:
    m = re.search(r"D(\d+)_", p)
    if m:
        nums.append(int(m.group(1)))
if nums:
    print(f"  D range: {min(nums)}-{max(nums)} ({len(nums)} files)")

ROOT = C.ROOT
for p in sorted((ROOT / "dlc" / "dec").glob("DLC_D*.cpk")):
    _, di = count_info(p)
    print(f"{p.stem}: {len(di)} .info: {[n for n, _ in di]}")
