#!/usr/bin/env python3
"""Verify glossary.json: list characters with status != unverified,
and any suspicious (short/non-kanji) entries."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C


def main():
    g = json.loads((C.WORK / "glossary.json")
                   .read_bytes().decode("utf-8-sig", "surrogatepass"))
    ch = g["characters"]
    print(f"characters: {len(ch)}  labels: {len(g['labels'])}  "
          f"locations: {len(g['locations'])}  terms: {len(g['terms'])}")
    print("--- non-unverified ---")
    for jp, c in ch.items():
        if c["status"] != "unverified":
            print(f"  {jp} | {c['reading']} | {c['status']} | {c['en']} | "
                  f"{c['evidence']}")
    print("--- suspicious (no kanji, or len<2, or ascii) ---")
    import re
    for jp, c in ch.items():
        if not re.search(r"[\u4e00-\u9fff]", jp) or len(jp) < 2 or \
                re.search(r"[A-Za-z0-9]", jp) and not re.search(
                    r"[ぁ-んァ-ン]", jp):
            print(f"  {jp!r} | {c['evidence']}")
    print("--- notes ---")
    for nt in g["notes"]:
        print(f"  {nt}")


if __name__ == "__main__":
    main()
