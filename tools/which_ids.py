#!/usr/bin/env python3
"""Diagnose which ids a file actually covers (first/last + sample)."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C


def main():
    for name in sys.argv[1:]:
        p = C.WORK / name
        if not p.exists():
            print(f"{name}: MISSING")
            continue
        tr = json.loads(p.read_bytes().decode("utf-8-sig", "surrogatepass"))
        ks = sorted(int(k) for k in tr)
        print(f"{name}: {len(ks)} ids, range {ks[0]}..{ks[-1]}, "
              f"contiguous={ks == list(range(ks[0], ks[-1] + 1))}")


if __name__ == "__main__":
    main()
