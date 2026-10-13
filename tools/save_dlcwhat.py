#!/usr/bin/env python3
"""What does each DLC actually contain? Names, scenarios, profile fields."""
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

ROOT = C.ROOT
for p in sorted((ROOT / "dlc" / "dec").glob("DLC_*.cpk")):
    a = cpk.load(str(p))
    print(f"===== {p.stem} ({len(a.files)} files) =====")
    for f in a.files:
        lp = f.full_path.lower()
        if lp.endswith(".srt") or lp.endswith(".info") or lp.endswith(".pac"):
            d = a.file_bytes(f.toc_index)
            # first bytes + JP strings preview
            strs = []
            for part in d.split(b"\x00"):
                try:
                    t = part.decode("utf-8")
                except UnicodeDecodeError:
                    continue
                if len(t) >= 2 and any("\u3040" <= c <= "\u30ff" or
                                       "\u4e00" <= c <= "\u9fff" for c in t):
                    strs.append(t)
            tag = "SRT" if lp.endswith(".srt") else ("VINFO" if "vc" in lp else ("INFO" if lp.endswith(".info") else "PAC"))
            print(f"  [{tag}] {f.full_path} size={len(d)} jpfields={len(strs)}")
            for t in strs[:6]:
                print(f"      {t[:70]!r}")
