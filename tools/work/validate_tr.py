#!/usr/bin/env python3
"""Validate all tools/work/tr_bNNNN.json against their batch sources.

Checks, per batch: key set matches, and every translation is within the
UTF-8 byte budget recorded in the batch file. Prints a compact report and
exits non-zero if any problem is found.
"""
import glob
import json
import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
WORK = Path(__file__).resolve().parent


def main(argv):
    if len(argv) > 1:
        lo = hi = int(argv[1])
        if len(argv) > 2:
            hi = int(argv[2])
        batches = range(lo, hi + 1)
    else:
        batches = None

    problems = []
    files = sorted(glob.glob(str(WORK / "tr_b*.json")))
    nbat = nent = 0
    worst = {}
    for p in files:
        name = os.path.basename(p)
        m = re.match(r"^tr_b(\d+)\.json$", name)
        if not m:
            continue
        b = int(m.group(1))
        if batches is not None and b not in batches:
            continue
        src_p = WORK / "batches" / f"batch_{b:04d}.json"
        if not src_p.exists():
            problems.append((b, "no source batch", 0, 0, 0))
            continue
        d = json.loads(Path(p).read_bytes().decode("utf-8", "surrogatepass"))
        src = json.loads(src_p.read_bytes().decode("utf-8", "surrogatepass"))
        miss = set(src) - set(d)
        extra = set(d) - set(src)
        over = []
        used = 0
        for k in set(d) & set(src):
            n = len(d[k].encode("utf-8"))
            used = max(used, n)
            if n > src[k]["b"]:
                over.append((k, src[k]["b"], n, d[k]))
        nbat += 1
        nent += len(d)
        bud = max(v["b"] for v in src.values())
        worst[b] = (used, bud)
        if miss or extra or over:
            problems.append((b, f"miss={len(miss)} extra={len(extra)} over={len(over)}",
                             sorted(int(x) for x in miss)[:8], sorted(int(x) for x in extra)[:8],
                             [(k, bb, n) for k, bb, n, _ in over[:8]]))

    print(f"batches checked: {nbat}  entries: {nent}")
    if problems:
        print("PROBLEMS:")
        for pr in problems:
            print("  ", pr)
        return 1
    print("OK - all keys match, all within budget")
    tight = sorted(worst.items(), key=lambda kv: kv[1][0] - kv[1][1])[:5]
    print("tightest batches (used/budget):",
          ", ".join(f"{b}:{u}/{bb}" for b, (u, bb) in tight))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
