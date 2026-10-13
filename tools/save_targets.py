#!/usr/bin/env python3
"""Count unlock targets: chars/scenarios in base + DLC CPKs, profile count."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

ROOT = C.ROOT
for label, path in [("BASE", C.ORIG)] + [
    (p.stem, p) for p in sorted((ROOT / "dlc" / "dec").glob("DLC_*.cpk"))
]:
    a = cpk.load(str(path))
    srt = [f for f in a.files if f.full_path.lower().endswith(".srt")]
    info = [f for f in a.files if f.full_path.lower().endswith(".info")]
    pac = [f for f in a.files if f.full_path.lower().endswith(".pac")]
    print(f"{label}: srt={len(srt)} info={len(info)} pac={len(pac)} total={len(a.files)}")
    for f in info:
        if "vc" in f.full_path.lower():
            d = a.file_bytes(f.toc_index)
            n = d.count(b"\x00")
            print(f"   vinfo {f.full_path} size={len(d)} nulfields={n}")
