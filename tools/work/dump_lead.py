#!/usr/bin/env python3
"""Dump a batch with an explicit leading-space (U+3000) flag.

Line format:  L|id|budget|jp
  L = ' '  -> source does NOT start with U+3000 (English must NOT start with space)
  L = '#'  -> source STARTS with U+3000 (English MUST start with one ASCII space)
Usage: dump_lead.py NNNN [lo] [hi]
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
WORK = Path(__file__).resolve().parent


def main(argv):
    b = int(argv[1])
    src = json.loads((WORK / "batches" / f"batch_{b:04d}.json")
                     .read_bytes().decode("utf-8", "surrogatepass"))
    lo = int(argv[2]) if len(argv) > 2 else None
    hi = int(argv[3]) if len(argv) > 3 else None
    for k in sorted(src, key=int):
        i = int(k)
        if lo is not None and i < lo:
            continue
        if hi is not None and i > hi:
            continue
        rec = src[k]
        flag = "#" if rec["jp"].startswith(chr(0x3000)) else " "
        print(f"{flag}|{k}|{rec['b']}|{rec['jp']}")
    print(f"# batch {b}: {len(src)} entries")


if __name__ == "__main__":
    main(sys.argv)
