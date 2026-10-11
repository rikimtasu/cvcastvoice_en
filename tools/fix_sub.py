#!/usr/bin/env python3
"""Apply small translation fixes by id. JSON-safe (no BOM)."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C

FIX = [
    # file, id, old_sub, new_sub  (substring swap, budget re-checked)
    ("tr_b0085.json", "10219", "Sho Kuri", "Shokuri"),
]


def main():
    order = json.loads((C.WORK / "order.json")
                       .read_bytes().decode("utf-8-sig", "surrogatepass"))
    for name, k, old_sub, new_sub in FIX:
        p = C.WORK / name
        tr = json.loads(p.read_bytes().decode("utf-8-sig", "surrogatepass"))
        old = tr[k]
        assert old_sub in old, (k, old)
        en = old.replace(old_sub, new_sub)
        b = order[k]["b"]
        assert len(en.encode()) <= b, (k, len(en.encode()), b)
        tr[k] = en
        p.write_bytes(json.dumps(tr, ensure_ascii=False).encode("utf-8"))
        print(f"{name}/{k}: {old!r} -> {en!r}")


if __name__ == "__main__":
    main()
