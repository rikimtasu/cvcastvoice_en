#!/usr/bin/env python3
"""Force the leading-space rule on tr_bNNNN.json directly from batch source.

Usage: fixlead_json.py NNNN
Deterministic rule: EN starts with exactly one ASCII space iff the JP source
starts with U+3000. Operates on the already-written JSON (source txt may be gone).
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
WORK = Path(__file__).resolve().parent


def main(argv):
    n = int(argv[1])
    batch = json.loads((WORK / f"batches/batch_{n:04d}.json")
                       .read_bytes().decode("utf-8", "surrogatepass"))
    tp = WORK / f"tr_b{n:04d}.json"
    t = json.loads(tp.read_bytes().decode("utf-8", "surrogatepass"))
    changed = 0
    for k, rec in batch.items():
        en = t[k]
        fixed = (" " + en.lstrip(" ")) if rec["jp"].startswith(chr(0x3000)) \
            else en.lstrip(" ")
        if fixed != en:
            t[k] = fixed
            changed += 1
    tp.write_bytes(json.dumps(t, ensure_ascii=True).encode("utf-8"))
    print(f"batch {n:04d}: fixed {changed} leading-space id(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
