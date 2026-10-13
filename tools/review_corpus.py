#!/usr/bin/env python3
"""Full review of the translation corpus (all work/tr_*.json).

Checks per entry:
  * ASCII-only (font safety)
  * no @n / newline leaks
  * no honorific leaks (-san/-chan/-sama/-kun/-dono)
  * no initialisms (X. Y. pattern, stutters excluded)
  * no retired/wrong names (Saionji, Kyouya, Fuminori, Kreden, ...)
  * no western-order full names for locked characters
  * budget compliance
Reports: missing batches, per-file problem counts, worst offenders.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C

HONOR = re.compile(r"\b[A-Za-z]+-(san|chan|sama|kun|dono|chin|sensei)\b")
INIT = re.compile(r"\b[A-Z]\. ?[A-Z][a-z]|\b[A-Z][a-z]+ [A-Z]\.")
NONASCII = re.compile(r"[^\x00-\x7F]")

# retired spellings that must not appear (flip history)
RETIRED = ["Saionji", "Kyouya", "Fuminori", "Kreden", "Chris Shinotani",
           "Shinotani Chris", "Sho Kurimane", "Hihihi", "Sakito",
           "Jun Narimiya", "Erina Todo", "Todo Erina"]

# western-order full names of locked characters (house rule: family-first).
# Built from glossary en names by swapping the two parts.
def western_forms():
    g = json.loads((C.WORK / "glossary.json")
                   .read_bytes().decode("utf-8-sig", "surrogatepass"))
    out = []
    for jp, c in g["characters"].items():
        en = c.get("en") or ""
        parts = en.split()
        if len(parts) == 2 and all(p[0].isupper() for p in parts):
            out.append(parts[1] + " " + parts[0])
    # single-token stage names that must stay exact
    return out


def main():
    order = json.loads((C.WORK / "order.json")
                       .read_bytes().decode("utf-8-sig", "surrogatepass"))
    west = western_forms()
    files = sorted(C.WORK.glob("tr_*.json"))
    cats = Counter()
    worst = []
    n_val = 0
    for p in files:
        try:
            tr = json.loads(p.read_bytes().decode("utf-8-sig", "surrogatepass"))
        except Exception as e:
            print(f"{p.name}: UNREADABLE ({e})")
            cats["unreadable"] += 1
            continue
        for k, v in tr.items():
            if k not in order:
                cats["unknown-id"] += 1
                worst.append((p.name, k, "unknown id", v[:60]))
                continue
            n_val += 1
            b = order[k]["b"]
            probs = []
            if len(v.encode()) > b:
                probs.append(f"OVER {len(v.encode())}>{b}")
            m = NONASCII.search(v)
            if m:
                probs.append(f"non-ascii {m.group()!r}")
            if "@n" in v or "\n" in v or "\r" in v:
                probs.append("newline leak")
            m = HONOR.search(v)
            if m:
                probs.append(f"honorific {m.group()!r}")
            else:
                m = INIT.search(v)
                if m and not re.search(r"\b(T\.O\.A|K\.O\.R|E\.D\.E\.N"
                                       r"|A\.K\.A)\b", v):
                    # allow stutter false positives only if explicit ...
                    if not re.match(r"^['\"( ]*([A-Za-z]-)+[A-Za-z]",
                                    v[max(0, m.start() - 4):]):
                        probs.append(f"initialism {m.group()!r}")
            for r in RETIRED:
                if r in v:
                    probs.append(f"retired {r!r}")
                    break
            for w in west:
                if w in v:
                    # make sure it is not part of the correct family-first
                    # form already counted (e.g. 'Mirei' inside longer ok)
                    probs.append(f"western-order {w!r}")
                    break
            for pr in probs:
                cats[pr.split()[0]] += 1
                if len(worst) < 60:
                    worst.append((p.name, k, pr, v[:80]))
    print(f"files: {len(files)}  entries checked: {n_val}")
    print("--- problem categories ---")
    for c, n in cats.most_common():
        print(f"  {n:6d}  {c}")
    print("--- first hits ---")
    for f, k, pr, v in worst[:40]:
        print(f"  {f}/{k} [{pr}] {v!r}"[:160])

    # missing batches
    have = set()
    for p in C.WORK.glob("tr_b????.json"):
        have.add(p.name)
    import os
    missing = []
    for bi in range(440):
        nm = f"tr_b{bi:04d}.json"
        if nm not in have:
            # batch 439 is short; check it separately
            missing.append(nm)
    # tr_batch0 + tr_mine cover 0000/0001
    missing = [m for m in missing
               if m not in ("tr_b0000.json", "tr_b0001.json")]
    print(f"--- missing batch files: {len(missing)} ---")
    print("  " + ", ".join(missing[:40]))
    if len(missing) > 40:
        print(f"  ... and {len(missing) - 40} more")


if __name__ == "__main__":
    main()
