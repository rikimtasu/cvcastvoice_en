#!/usr/bin/env python3
"""Find tr_b*.json files that fail json parsing, with byte-level detail."""
import glob
import json
import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
WORK = Path(__file__).resolve().parent

for p in sorted(glob.glob(str(WORK / "tr_b*.json"))):
    n = os.path.basename(p)
    if not re.match(r"^tr_b\d+\.json$", n):
        print("skip (name):", n)
        continue
    raw = Path(p).read_bytes()
    try:
        json.loads(raw.decode("utf-8"))
    except Exception as e:
        print("BAD:", n, "size=", len(raw), "head=", raw[:4], repr(e)[:120])
print("scan done")
