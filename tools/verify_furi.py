#!/usr/bin/env python3
"""Codepoint-verify all person-name furigana pairs (no console mojibake)."""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C

FURI = re.compile(r"([\u4e00-\u9fff]{1,6}(?:[　 ][\u4e00-\u9fff]{1,6})?)"
                  r"\s*(?:[\u3040-\u30ff]{1,10})?"
                  r"\s*[（(]([\u3040-\u30ff・ー 　]+)[）)]")


def main():
    seg = json.loads((C.WORK / "segments.json")
                     .read_bytes().decode("utf-8-sig", "surrogatepass"))
    names = {}
    for rec in seg.values():
        for s in rec["seg"]:
            for m in FURI.finditer(s["jp"]):
                kj = m.group(1).replace("　", "").replace(" ", "")
                rd = m.group(2).strip()
                # person-name-like: 2+ kanji, reading has a space or length>=4
                if len(kj) >= 4 and (" " in rd or "　" in rd):
                    names.setdefault(kj, set()).add(rd)
    for kj in sorted(names):
        rds = names[kj]
        cps = [" ".join(f"U+{ord(c):04X}" for c in r) for r in rds]
        flag = "  <-- MULTIPLE" if len(rds) > 1 else ""
        print(f"{kj}:")
        for r, c in zip(sorted(rds), cps):
            print(f"    [{c}]{flag}")


if __name__ == "__main__":
    main()
