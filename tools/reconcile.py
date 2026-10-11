#!/usr/bin/env python3
"""Reconcile translation counts: entries per file, unique ids, unknown ids."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C


def main():
    order = json.loads((C.WORK / "order.json")
                       .read_bytes().decode("utf-8-sig", "surrogatepass"))
    files = sorted(C.WORK.glob("tr_*.json"))
    print(f"tr files: {len(files)}")
    seen = {}
    unknown = 0
    total = 0
    for p in files:
        tr = json.loads(p.read_bytes().decode("utf-8-sig", "surrogatepass"))
        total += len(tr)
        for k in tr:
            if k not in order:
                unknown += 1
                continue
            seen.setdefault(k, []).append(p.name)
    dup = {k: v for k, v in seen.items() if len(v) > 1}
    print(f"total entries: {total}, unique known ids: {len(seen)}, "
          f"unknown ids: {unknown}, dup ids: {len(dup)}")
    print(f"expected: batches 0000-0107 = 108x120 = 12960")
    if dup:
        for k, v in list(dup.items())[:10]:
            print(f"  dup {k}: {v}")


if __name__ == "__main__":
    main()
