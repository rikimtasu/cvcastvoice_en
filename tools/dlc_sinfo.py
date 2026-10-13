#!/usr/bin/env python3
"""Extract NUL-separated Japanese strings from S-pack vc*_base.info files."""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

DLC = C.ROOT / "dlc" / "dec"
JP = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff\uff01-\uff60\u3005-\u3006]+")


def main():
    for cpk_path in sorted(DLC.glob("DLC_S*.cpk")):
        a = cpk.load(str(cpk_path))
        for f in a.files:
            if not f.full_path.lower().endswith(".info"):
                continue
            d = a.file_bytes(f.toc_index)
            parts = d.split(b"\x00")
            strs = []
            for p in parts:
                try:
                    t = p.decode("utf-8")
                except UnicodeDecodeError:
                    continue
                if len(t) >= 2 and JP.search(t):
                    strs.append(t)
            print(f"== {cpk_path.name} {f.full_path}: "
                  f"{len(strs)} JP strings ==")
            for t in strs[:20]:
                print(f"  {t[:70]!r}")


if __name__ == "__main__":
    main()
