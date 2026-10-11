#!/usr/bin/env python3
"""Dump the dialogue runs of the day-101/111 opening narration files so they can
be translated. Includes the route variants (pl266) so whichever the game reads
will show English."""
import json
import sys
from pathlib import Path
from cricodecs import cpk

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C

ORIG = C.ORIG
a = cpk.load(str(ORIG))
FILES = ["DATA/srt_ev/b_flow/day101.srt",
         "DATA/srt_ev/b_flow/day111.srt",
         "DATA/srt_ev/pl266/b_flow/day101.srt",
         "DATA/srt_ev/pl266/b_flow/day111.srt"]

out = {}
lines = []
for path in FILES:
    f = next((x for x in a.files if x.full_path == path), None)
    if f is None:
        lines.append(f"MISSING {path}")
        continue
    d = a.file_bytes(f.toc_index)
    spans = C.parse_dialogue(d)
    lines.append("=" * 90)
    lines.append(f"{path}  toc={f.toc_index} extract={f.extract_size} runs={len(spans)}")
    runs = []
    for i, (s, e) in enumerate(spans):
        txt = d[s:e].decode("utf-8", "replace")
        runs.append({"span": [s, e], "jp": txt})
        lines.append(f"  [{i:02d}] {s:5d}..{e:5d} ({e-s:3d}b) {txt}")
    out[path] = {"toc_index": f.toc_index, "extract_size": f.extract_size,
                 "runs": runs}

d = C.WORK / "day101_runs.json"
d.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
(C.WORK / "day101_runs.txt").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
