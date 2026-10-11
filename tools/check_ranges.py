#!/usr/bin/env python3
"""Verify tr_bNNNN.json files contain exactly batch NNNN's id range."""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C


def main():
    bad = 0
    for p in sorted(C.WORK.glob("tr_b????.json")):
        m = re.match(r"tr_b(\d{4})\.json", p.name)
        n = int(m.group(1))
        tr = json.loads(p.read_bytes().decode("utf-8-sig", "surrogatepass"))
        want = {str(i) for i in range(n * 120, n * 120 + 120)}
        got = set(tr)
        if got != want:
            bad += 1
            print(f"{p.name}: MISMATCH ids {len(got)} "
                  f"missing {len(want-got)} extra {len(got-want)}")
    print("mismatch files:", bad)


if __name__ == "__main__":
    main()
