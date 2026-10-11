#!/usr/bin/env python3
"""Dump sample SoundData.cpk full paths to see the naming scheme."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

SOUND = C.SOUND


def main():
    a = cpk.load(str(SOUND))
    fa = a.files
    out = []
    for f in fa[:40]:
        out.append(f.full_path)
    out.append("...")
    # any paths with 2+ digit groups or alpha stems longer than 3?
    import re
    for f in fa:
        name = f.full_path.rsplit("/", 1)[-1]
        if re.match(r"[A-Za-z]{4,}", name):
            out.append(f.full_path)
            if len(out) > 70:
                break
    txt = "\n".join(out)
    print(txt)
    (C.WORK / "sound_paths.txt").write_bytes(
        txt.encode("utf-8", "replace"))


if __name__ == "__main__":
    main()
