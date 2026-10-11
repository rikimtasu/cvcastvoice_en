#!/usr/bin/env python3
"""Make a control overlay: replace the dialogue of ONE file with dummy English
that occupies exactly the same byte spans (so no .srt internal field changes).
This isolates "archive surgery" as the single variable vs. the original."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C

dup = C.WORK / "master.json"
if not dup.exists():
    print("run cvpatch.py scan first")
    sys.exit(2)
master = json.loads(dup.read_text(encoding="utf-8"))

path = sys.argv[1] if len(sys.argv) > 1 else "DATA/srt_dh/P001_01.srt"
m = master[path]

out = {path: {"runs": []}}
for i, (s, e) in enumerate([[r["start"], r["end"]] for r in m["runs"]] if
                         isinstance(m["runs"][0], dict) else m["runs"]):
    span = e - s
    # ASCII filler that exactly fills the span: 1 byte per char.
    prefix = f"[{i:03d}] "
    fill = "A" * max(1, span - len(prefix))
    out[path]["runs"].append(
        {"span": [s, e], "text": (prefix + fill)[:span]})

dest = Path(__file__).with_name("ov_ctrl.json")
dest.write_text(json.dumps({"files": out}, ensure_ascii=False, indent=1), encoding="utf-8")
tot = sum(e - s for s, e in m["runs"])
print(f"{path}: {len(m['runs'])} runs, {tot} bytes to fill")
print(f"wrote {dest}")
