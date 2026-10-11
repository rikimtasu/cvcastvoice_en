#!/usr/bin/env python3
"""Report which batch ids are NOT yet covered by any work/tr_*.json.

Usage: coverage.py            -> summary + missing batch numbers
       coverage.py NNNN NNNN  -> only that batch range
"""
import glob
import json
import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
WORK = Path(__file__).resolve().parent

have = set()
for p in sorted(glob.glob(str(WORK / "tr_*.json"))):
    try:
        d = json.loads(Path(p).read_bytes().decode("utf-8", "surrogatepass"))
    except Exception as e:
        print("WARN unreadable:", os.path.basename(p), e)
        continue
    have |= set(d)
print("tr files:", len(glob.glob(str(WORK / "tr_*.json"))),
      " unique translated ids:", len(have))

todo = []
n_str = n_left = 0
for p in sorted(glob.glob(str(WORK / "batches" / "batch_*.json"))):
    b = int(os.path.basename(p)[6:10])
    if len(sys.argv) > 1 and not (int(sys.argv[1]) <= b <= int(sys.argv[2])):
        continue
    src = json.loads(Path(p).read_bytes().decode("utf-8", "surrogatepass"))
    left = [k for k in src if k not in have]
    n_str += len(src)
    n_left += len(left)
    if left:
        todo.append((b, len(left)))

print(f"batches in scope: {len(todo) + 0 if not todo else ''}", end="")
print(f"strings in scope: {n_str}  untranslated: {n_left}")
print(f"batches fully/partly outstanding: {len(todo)}")
if todo:
    print("outstanding (batch:untranslated):",
          ", ".join(f"{b}:{n}" for b, n in todo[:40]),
          "..." if len(todo) > 40 else "")
