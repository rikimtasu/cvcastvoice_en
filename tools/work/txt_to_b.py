#!/usr/bin/env python3
"""Convert an existing tr_bNNNN.json into work/tr/bNNNN.txt (id|english).

Usage: txt_to_b.py NNNN
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
WORK = Path(__file__).resolve().parent

b = int(sys.argv[1])
d = json.loads((WORK / f"tr_b{b:04d}.json")
               .read_bytes().decode("utf-8", "surrogatepass"))
(WORK / "tr").mkdir(exist_ok=True)
out = WORK / "tr" / f"b{b:04d}.txt"
with out.open("w", encoding="utf-8", newline="\n") as fh:
    for k in sorted(d, key=int):
        fh.write(f"{k}|{d[k].replace('|', chr(92) + 'u007c')}\n")
print("wrote", out, len(d), "entries")
