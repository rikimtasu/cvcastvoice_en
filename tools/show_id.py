#!/usr/bin/env python3
"""Show one order entry (JP + budget + count) for review."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C


def main():
    order = json.loads((C.WORK / "order.json")
                       .read_bytes().decode("utf-8-sig", "surrogatepass"))
    for k in sys.argv[1:]:
        v = order[k]
        print(f"[{k}] b={v['b']} c={v['c']} JP={v['jp']!r}")


if __name__ == "__main__":
    main()
