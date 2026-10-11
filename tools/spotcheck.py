#!/usr/bin/env python3
"""Random spot-check: print N random JP->EN pairs from given tr files."""
import json
import random
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C


def main():
    order = json.loads((C.WORK / "order.json")
                       .read_bytes().decode("utf-8-sig", "surrogatepass"))
    rng = random.Random(42)
    for name in sys.argv[1:]:
        tr = json.loads((C.WORK / name).read_bytes()
                        .decode("utf-8-sig", "surrogatepass"))
        print(f"== {name} ==")
        for k in rng.sample(sorted(tr), 3):
            print(f"  [{k}] b={order[k]['b']} JP={order[k]['jp'][:50]!r}")
            print(f"       EN={tr[k]!r}")


if __name__ == "__main__":
    main()
