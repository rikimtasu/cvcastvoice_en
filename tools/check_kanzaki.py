#!/usr/bin/env python3
"""Dump codepoints of every segment containing 神崎+furigana to settle
ふみのり vs ふみゆき at the byte level."""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C

FURI = re.compile(r"神崎\s*[　 ]史之[（(]([^）)]+)[）)]")


def main():
    seg = json.loads((C.WORK / "segments.json")
                     .read_bytes().decode("utf-8-sig", "surrogatepass"))
    n = 0
    for path, rec in seg.items():
        for s in rec["seg"]:
            m = FURI.search(s["jp"])
            if m:
                n += 1
                rd = m.group(1)
                cps = " ".join(f"U+{ord(c):04X}" for c in rd)
                print(f"{path} [{s['s']},{s['e']}) reading=[{cps}]")
    print(f"total Kanzaki-furigana segments: {n}")


if __name__ == "__main__":
    main()
