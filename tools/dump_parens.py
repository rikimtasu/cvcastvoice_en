#!/usr/bin/env python3
"""Dump every line containing （ or ( from the scenario txt files, raw."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk


def main():
    a = cpk.load(str(C.ORIG))
    by = {f.full_path: f for f in a.files}
    out = []
    for p in ["DATA/srt_ev/pl268/up268_00.txt",
              "DATA/srt_ev/pl268/up268_01.txt"]:
        t = a.file_bytes(by[p].toc_index).decode("utf-16-le", "replace")
        for ln in t.splitlines():
            if "（" in ln or "(" in ln:
                out.append(f"{p}: {ln.strip()[:160]}")
    (C.WORK / "paren_lines.txt").write_bytes(
        "\n".join(out).encode("utf-8", "replace"))
    print(f"{len(out)} paren lines -> work/paren_lines.txt")


if __name__ == "__main__":
    main()
