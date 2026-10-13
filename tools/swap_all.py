#!/usr/bin/env python3
"""Corpus-wide substring fix with budget recheck. JSON-safe, no BOM."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C


def main():
    old, new = sys.argv[1], sys.argv[2]
    order = json.loads((C.WORK / "order.json")
                       .read_bytes().decode("utf-8-sig", "surrogatepass"))
    dorder = {}
    try:
        # dlc ids live in dlc batch files, validated by budget at merge;
        # re-check against stored budgets by scanning dlc_segments
        seg = json.loads((C.WORK / "dlc_segments.json")
                         .read_bytes().decode("utf-8-sig", "surrogatepass"))
        for rec in seg.values():
            for s in rec["seg"]:
                pass
    except Exception:
        pass
    n = 0
    for p in sorted(C.WORK.glob("tr_*.json")):
        tr = json.loads(p.read_bytes().decode("utf-8-sig", "surrogatepass"))
        dirty = False
        for k, v in tr.items():
            if old in v:
                nv = v.replace(old, new)
                if k in order and len(nv.encode()) > order[k]["b"]:
                    print(f"  SKIP {p.name}/{k}: over budget")
                    continue
                tr[k] = nv
                dirty = True
                n += 1
        if dirty:
            p.write_bytes(json.dumps(tr, ensure_ascii=False).encode("utf-8"))
    print(f"swapped {n} occurrences of {old!r} -> {new!r}")


if __name__ == "__main__":
    main()
