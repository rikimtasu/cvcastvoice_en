#!/usr/bin/env python3
"""Apply small translation fixes by id. JSON-safe (no BOM)."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C

FIX = {
    # file, id, new english
    ("tr_b0231.json", "27743", "Father Akira comes for Yuki..."),
    ("tr_b0231.json", "27745", "Akira smashes Yuki's phone..."),
}


def main():
    order = json.loads((C.WORK / "order.json")
                       .read_bytes().decode("utf-8-sig", "surrogatepass"))
    for name, k, en in FIX:
        p = C.WORK / name
        tr = json.loads(p.read_bytes().decode("utf-8-sig", "surrogatepass"))
        old = tr.get(k)
        b = order[k]["b"]
        assert len(en.encode()) <= b, (k, len(en.encode()), b)
        tr[k] = en
        p.write_bytes(json.dumps(tr, ensure_ascii=False).encode("utf-8"))
        print(f"{name}/{k} b={b}: {old!r} -> {en!r}")


if __name__ == "__main__":
    main()
