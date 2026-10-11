#!/usr/bin/env python3
"""Inspect name-related files: name_sel.srt, rename.bat, seiyubase.pac,
plus the 2 .txt files and any name/table-ish srt_dh files."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

WANT = ["DATA/srt_ev/b_flow/name_sel.srt",
        "DATA/srt_ev/pl266/b_flow/name_sel.srt",
        "DATA/srt_ev/rename.bat",
        "DATA/daihon/seiyubase.pac"]


def main():
    a = cpk.load(str(C.ORIG))
    fa = a.files
    by = {f.full_path: f for f in fa}
    for p in WANT:
        f = by.get(p)
        if f is None:
            print("MISSING", p)
            continue
        d = a.file_bytes(f.toc_index)
        print("=" * 30)
        print(p, "stored", f.file_size, "extract", f.extract_size)
        print(repr(d[:1200]))
        print("... tail:", repr(d[-300:]))
    print("=" * 30)
    print("all .txt files:")
    for f in fa:
        if f.full_path.lower().endswith(".txt"):
            d = a.file_bytes(f.toc_index)
            print(f.full_path, len(d))
            print(repr(d[:800]))


if __name__ == "__main__":
    main()
