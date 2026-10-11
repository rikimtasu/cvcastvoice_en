#!/usr/bin/env python3
"""Which translated strings live in un-relocatable rows (0 and 8399)?"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C


def main():
    seg = json.loads((C.WORK / "segments.json")
                     .read_bytes().decode("utf-8-sig", "surrogatepass"))
    tr = {}
    for p in sorted(C.WORK.glob("tr_*.json")):
        tr.update(json.loads(p.read_bytes().decode("utf-8-sig", "surrogatepass")))
    order = json.loads((C.WORK / "order.json")
                       .read_bytes().decode("utf-8-sig", "surrogatepass"))
    done = {order[k]["jp"] for k in tr if k in order}
    for path, rec in seg.items():
        if rec["toc"] in (0, C.NROWS - 1):
            n = len(rec["seg"])
            hit = sum(1 for s in rec["seg"] if s["jp"] in done)
            print(f"toc={rec['toc']} {path}: {n} segments, "
                  f"{hit} translated")
            for s in rec["seg"][:12]:
                mark = "EN" if s["jp"] in done else "JP"
                print(f"  [{mark}] {s['jp'][:70]!r}")


if __name__ == "__main__":
    main()
