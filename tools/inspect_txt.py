#!/usr/bin/env python3
"""Decode the 2 UTF-16LE scenario .txt files and show their structure:
are they scripts with display text + speaker tags?"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk


def main():
    a = cpk.load(str(C.ORIG))
    fa = a.files
    by = {f.full_path: f for f in fa}
    for p in ["DATA/srt_ev/pl268/up268_00.txt",
              "DATA/srt_ev/pl268/up268_01.txt"]:
        f = by.get(p)
        d = a.file_bytes(f.toc_index)
        t = d.decode("utf-16-le", "replace")
        lines = t.splitlines()
        print("=" * 30)
        print(p, f"chars={len(t)} lines={len(lines)}")
        # structure: first 60 lines, then any line with JP text sample
        for ln in lines[:60]:
            print("  " + ln[:100])
        print("  ...")
        jp = [ln for ln in lines if any("\u3040" <= c <= "\u30ff" or
                                        "\u4e00" <= c <= "\u9fff" for c in ln)]
        print(f"  lines containing JP: {len(jp)}")
        for ln in jp[:30]:
            print("  JP: " + ln[:100])


if __name__ == "__main__":
    main()
