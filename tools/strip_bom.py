#!/usr/bin/env python3
"""Strip BOMs from work JSON files (PowerShell Set-Content adds them)."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C


def main():
    n = 0
    for p in sorted(C.WORK.glob("tr_*.json")):
        b = p.read_bytes()
        if b[:3] == b"\xef\xbb\xbf":
            p.write_bytes(b[3:])
            print(f"stripped BOM: {p.name}")
            n += 1
    print(f"done, {n} files fixed")


if __name__ == "__main__":
    main()
