#!/usr/bin/env python3
"""Scan SoundData.cpk's TOC for romanized voice-file names that reveal
official readings of the character names (e.g. mirei_001 vs saionji_001)."""
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

SOUND = C.SOUND


def main():
    a = cpk.load(str(SOUND))
    fa = a.files
    print(f"files: {len(fa)}")
    stems = Counter()
    for f in fa:
        name = f.full_path.rsplit("/", 1)[-1]
        m = re.match(r"([A-Za-z_]+?)[0-9]*\.", name)
        if m:
            stems[m.group(1).lower()] += 1
    out = ["== voice-file stem inventory =="]
    for s, c in stems.most_common(120):
        out.append(f"  x{c:<6} {s}")
    # dirs one level
    dirs = Counter()
    for f in fa:
        p = f.full_path
        dirs[p.split("/")[0] if "/" in p else "(root)"] += 1
    out.append("== dirs ==")
    for d, c in dirs.most_common(20):
        out.append(f"  x{c:<6} {d}")
    # any full paths containing candidate romanizations?
    out.append("== paths matching candidate readings ==")
    cands = ["mirei", "saionji", "saig", "nishimiya", "kyoya", "garyu",
             "kagamihara", "kakamigahara", "masaaki", "akira", "namino",
             "hana", "shigino", "momo"]
    hit = 0
    for f in fa:
        lp = f.full_path.lower()
        for cd in cands:
            if cd in lp:
                out.append(f"  [{cd}] {f.full_path}")
                hit += 1
                break
        if hit > 60:
            break
    txt = "\n".join(out)
    print(txt)
    (C.WORK / "sound_names.txt").write_bytes(
        txt.encode("utf-8", "replace"))


if __name__ == "__main__":
    main()
