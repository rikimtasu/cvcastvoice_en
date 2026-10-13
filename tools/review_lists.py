#!/usr/bin/env python3
"""Dump every honorific / western-order / retired hit for review + fixing."""
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C

HONOR = re.compile(r"\b([A-Za-z]+-(?:san|chan|sama|kun|dono|chin|sensei))\b")
RETIRED = ["Saionji", "Kyouya", "Fuminori", "Kreden", "Chris Shinotani",
           "Shinotani Chris", "Sho Kurimane", "Hihihi", "Sakito",
           "Jun Narimiya", "Erina Todo", "Todo Erina"]


def main():
    g = json.loads((C.WORK / "glossary.json")
                   .read_bytes().decode("utf-8-sig", "surrogatepass"))
    west = {}
    for jp, c in g["characters"].items():
        parts = (c.get("en") or "").split()
        if len(parts) == 2 and all(p[0].isupper() for p in parts):
            west[parts[1] + " " + parts[0]] = parts[0] + " " + parts[1]
    hon = Counter()
    hon_ex = {}
    wst = Counter()
    wst_ex = {}
    ret = []
    for p in sorted(C.WORK.glob("tr_*.json")):
        tr = json.loads(p.read_bytes().decode("utf-8-sig", "surrogatepass"))
        for k, v in tr.items():
            for m in HONOR.finditer(v):
                hon[m.group(1)] += 1
                hon_ex.setdefault(m.group(1), (p.name, k, v[:90]))
            for w, fix in west.items():
                if w in v:
                    wst[w] += 1
                    wst_ex.setdefault(w, (p.name, k, v[:90]))
            for r in RETIRED:
                if r in v:
                    ret.append((p.name, k, r, v[:90]))
    out = ["== honorific forms (398 total) =="]
    for h, n in hon.most_common():
        f, k, v = hon_ex[h]
        out.append(f"  x{n:<4} {h:<18} e.g. {f}/{k} {v!r}"[:150])
    out.append("== western-order (22 total) ==")
    for w, n in wst.most_common():
        f, k, v = wst_ex[w]
        out.append(f"  x{n:<4} {w:<24} -> {west[w]:<24} e.g. {f}/{k}")
    out.append("== retired (3) ==")
    for f, k, r, v in ret:
        out.append(f"  {f}/{k} [{r}] {v!r}"[:150])
    txt = "\n".join(out)
    print(txt)
    (C.WORK / "review_lists.txt").write_bytes(txt.encode("utf-8"))


if __name__ == "__main__":
    main()
