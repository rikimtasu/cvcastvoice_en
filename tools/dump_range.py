#!/usr/bin/env python3
"""Dump order ids [LO,HI) to a readable UTF-8 file for translation."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C


def main():
    lo, hi, name = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    order = json.loads((C.WORK / "order.json")
                       .read_bytes().decode("utf-8-sig", "surrogatepass"))
    lines = []
    for i in range(lo, hi):
        v = order[str(i)]
        lines.append(f"{i:6d}  b={v['b']:3d}  c={v['c']:5d}  {v['jp']}")
    (C.WORK / name).write_bytes("\n".join(lines)
                                .encode("utf-8", "surrogatepass"))
    print(f"wrote {len(lines)} lines to work/{name}")


if __name__ == "__main__":
    main()
