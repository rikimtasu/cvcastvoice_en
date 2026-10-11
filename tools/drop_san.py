#!/usr/bin/env python3
"""Drop -san suffixes to match house style (bare names). Reports changes."""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C

SAN = re.compile(r"\b([A-Z][a-z]+)-san\b")


def main():
    order = json.loads((C.WORK / "order.json")
                       .read_bytes().decode("utf-8-sig", "surrogatepass"))
    n_fix = 0
    for name in sys.argv[1:]:
        p = C.WORK / name
        tr = json.loads(p.read_bytes().decode("utf-8-sig", "surrogatepass"))
        for k, v in tr.items():
            nv = SAN.sub(r"\1", v)
            if nv != v:
                if len(nv.encode()) > order[k]["b"]:
                    print(f"  SKIP {name}/{k}: would exceed after drop?!")
                    continue
                print(f"  {name}/{k}: {v!r} -> {nv!r}")
                tr[k] = nv
                n_fix += 1
        p.write_bytes(json.dumps(tr, ensure_ascii=False).encode("utf-8"))
    print(f"dropped {n_fix} -san suffixes")


if __name__ == "__main__":
    main()
