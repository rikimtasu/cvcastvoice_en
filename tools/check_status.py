#!/usr/bin/env python3
"""List glossary characters whose status is not triple-agree."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C


def main():
    g = json.loads((C.WORK / "glossary.json")
                   .read_bytes().decode("utf-8-sig", "surrogatepass"))
    for jp, c in sorted(g["characters"].items()):
        if c["status"] not in ("wikipedia + fandom + imdb agree",
                               "fandom + imdb agree"):
            print(f"  {jp} | {c['status']} | {c['en']}")


if __name__ == "__main__":
    main()
