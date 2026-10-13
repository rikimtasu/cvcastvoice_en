#!/usr/bin/env python3
"""Locate every occurrence of suspect spellings with context."""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C

PATS = ["Sayoka", "Sayo-chan", "Narumiya", "Shishitani", "Ogihara",
        "Hime-no", "Kuru-kun", "Kyouya", "Fuminori", "Saionji", "Kreden",
        "Chris Shinotani", "Shinotani Chris", "Sho Kurimane"]


def main():
    order = json.loads((C.WORK / "order.json")
                       .read_bytes().decode("utf-8-sig", "surrogatepass"))
    for p in sorted(C.WORK.glob("tr_*.json")):
        tr = json.loads(p.read_bytes().decode("utf-8-sig", "surrogatepass"))
        for k, v in tr.items():
            for pat in PATS:
                if pat in v:
                    print(f"{p.name}/{k} [{pat}] b={order[k]['b']}")
                    print(f"   JP={order[k]['jp'][:60]!r}")
                    print(f"   EN={v[:90]!r}")


if __name__ == "__main__":
    main()
