#!/usr/bin/env python3
"""Audit pilot translations: budget re-check + normalize name-plate
abbreviations to family-name-only + show flagged ids for review."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C

# subagent initial-abbreviations -> house rule (family name only)
FIX = {"242": "Sakura", "248": "Taki", "270": "Nakamikado",
       "287": "Kosaka", "288": "Minamino"}
SHOW = ["242", "247", "248", "270", "287", "288", "289", "290",
        "349", "350", "359", "384", "447", "452"]


def main():
    order = json.loads((C.WORK / "order.json")
                       .read_bytes().decode("utf-8-sig", "surrogatepass"))
    for name in ("tr_b0002.json", "tr_b0003.json", "tr_mine060_239.json",
                 "tr_batch0.json"):
        p = C.WORK / name
        tr = json.loads(p.read_bytes().decode("utf-8-sig", "surrogatepass"))
        n_over = 0
        for k, v in tr.items():
            b = order[k]["b"]
            if len(v.encode("utf-8")) > b:
                print(f"  OVER {name}/{k}: {len(v.encode())}>{b} {v!r}")
                n_over += 1
        print(f"{name}: {len(tr)} entries, {n_over} over budget")
    # normalize b0002
    p = C.WORK / "tr_b0002.json"
    tr = json.loads(p.read_bytes().decode("utf-8-sig", "surrogatepass"))
    for k, v in FIX.items():
        if k in tr:
            tr[k] = v
    p.write_bytes(json.dumps(tr, ensure_ascii=False).encode("utf-8"))
    print("normalized 5 abbreviations to family-name-only")
    # show flagged
    all_tr = {}
    for name in ("tr_b0002.json", "tr_b0003.json"):
        all_tr.update(json.loads((C.WORK / name).read_bytes()
                                 .decode("utf-8-sig", "surrogatepass")))
    for k in SHOW:
        if k in all_tr:
            jp = order[k]["jp"]
            print(f"  [{k}] b={order[k]['b']} JP={jp!r} EN={all_tr[k]!r}")


if __name__ == "__main__":
    main()
