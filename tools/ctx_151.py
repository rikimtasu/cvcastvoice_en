#!/usr/bin/env python3
"""Show where id 151 (翔クリマネ) occurs and its neighbors."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C


def main():
    order = json.loads((C.WORK / "order.json")
                       .read_bytes().decode("utf-8-sig", "surrogatepass"))
    jp = order["151"]["jp"]
    seg = json.loads((C.WORK / "segments.json")
                     .read_bytes().decode("utf-8-sig", "surrogatepass"))
    n = 0
    for path, rec in seg.items():
        for idx, s in enumerate(rec["seg"]):
            if s["jp"] == jp:
                n += 1
                if n > 3:
                    continue
                print(f"== {path} ==")
                for s2 in rec["seg"][max(0, idx - 2):idx + 3]:
                    mark = ">>>" if s2["jp"] == jp else "   "
                    print(f"  {mark} {s2['jp'][:60]!r}")
    print(f"total occurrences: {n}")


if __name__ == "__main__":
    main()
