#!/usr/bin/env python3
"""Mine furigana readings from clean segments (NAME（reading） patterns)."""
import json
import re
import sys
from collections import Counter
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
    hits = Counter()
    for rec in seg.values():
        for s in rec["seg"]:
            for m in FURI.finditer(s["jp"]):
                hits[(m.group(1), m.group(2).strip())] += 1
    print(f"furigana pairs in segments: {len(hits)}")
    for (kj, rd), c in hits.most_common(40):
        print(f"  x{c:<4} {kj} -> {rd}")


if __name__ == "__main__":
    main()
