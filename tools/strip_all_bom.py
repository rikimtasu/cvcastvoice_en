#!/usr/bin/env python3
"""Strip BOMs from all work data files ( defence in depth )."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C


def main():
    n = 0
    files = list(C.WORK.glob("*.json")) + list(C.WORK.glob("*.txt")) + \
        list(C.WORK.glob("*.md")) + list((C.WORK / "batches").glob("*.json"))
    for p in files:
        try:
            b = p.read_bytes()
        except Exception:
            continue
        if b[:3] == b"\xef\xbb\xbf":
            p.write_bytes(b[3:])
            print(f"stripped BOM: {p.relative_to(C.WORK)}")
            n += 1
    print(f"done, {n} files fixed of {len(files)} scanned")


if __name__ == "__main__":
    main()
