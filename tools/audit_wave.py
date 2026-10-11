#!/usr/bin/env python3
"""Audit a translation wave: entry counts, budget re-check, abbreviation
normalization, and flagged-pattern scan."""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C

INITIALISM = re.compile(r"\b[A-Z]\. ?[A-Z][a-z]|\b[A-Z][a-z]+ [A-Z]\.")


def main():
    files = sorted(sys.argv[1:], key=lambda p: p)
    order = json.loads((C.WORK / "order.json")
                       .read_bytes().decode("utf-8-sig", "surrogatepass"))
    tot = over = 0
    for name in files:
        p = C.WORK / name
        if not p.exists():
            print(f"{name}: MISSING")
            continue
        tr = json.loads(p.read_bytes().decode("utf-8-sig", "surrogatepass"))
        n = len(tr)
        tot += n
        bad = []
        for k, v in tr.items():
            if k not in order:
                bad.append((k, "unknown id"))
                continue
            if len(v.encode("utf-8")) > order[k]["b"]:
                bad.append((k, f"over {len(v.encode())}>{order[k]['b']}"))
                over += 1
            if INITIALISM.search(v):
                bad.append((k, f"initialism {v!r}"))
            if "@n" in v or "\n" in v:
                bad.append((k, "newline leak"))
        print(f"{name}: {n} entries, {len(bad)} problems")
        for k, w in bad[:10]:
            en = tr.get(k, "")
            print(f"    [{k}] {w} b={order.get(k, {}).get('b')} {en!r}"[:150])
    print(f"wave total: {tot} entries, {over} over budget")


if __name__ == "__main__":
    main()
