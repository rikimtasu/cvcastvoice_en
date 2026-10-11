#!/usr/bin/env python3
"""Byte-check 内山紗彩 (WP) vs 内山沙彩 (Fandom): which is in the game?"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk


def main():
    a = cpk.load(str(C.ORIG))
    fa = a.files
    needles = {"内山紗彩": "内山紗彩".encode("utf-8"),
               "内山沙彩": "内山沙彩".encode("utf-8")}
    found = {k: [] for k in needles}
    for f in fa:
        try:
            d = a.file_bytes(f.toc_index)
        except Exception:
            continue
        if not d:
            continue
        for k, b in needles.items():
            if b in d and len(found[k]) < 3:
                found[k].append(f.full_path)
    for k, v in found.items():
        print(f"  {k}: {len(v)}+ files {v[:2]}")


if __name__ == "__main__":
    main()
