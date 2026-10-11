#!/usr/bin/env python3
"""Dump a batch as compact 'id | budget | jp' lines for translation work.

Usage: dump_batch.py NNNN [start_id] [end_id]
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
        print(f"{k}|{src[k]['b']}|{src[k]['jp']}")
    print(f"# batch {b}: {len(src)} entries")


if __name__ == "__main__":
    main(sys.argv)
