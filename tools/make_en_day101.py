#!/usr/bin/env python3
"""Build an English overlay for the day-101 morning narration and turn it into a
patched archive. This is the first *real* translation test: it proves both that
the relocated raw payload renders and that English text works in the text box."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

ORIG = Path(r"D:\Documents\CVCastingVoice\_backup\GameData.original.cpk")
FILES = ["DATA/srt_ev/b_flow/day101.srt",
         "DATA/srt_ev/b_flow/day111.srt",
         "DATA/srt_ev/pl266/b_flow/day101.srt",
         "DATA/srt_ev/pl266/b_flow/day111.srt"]

# English translations, keyed by span length so they apply to all four files
# (the four are byte-identical in structure and content).
TRANSLATIONS = [
    (84, "Yaaawn... It's a day off, but I still have to get up early."),
    (48, "Otherwise my daily rhythm will fall apart."),
    (72, "Now then, it's a rare day off. What shall I do today?"),
    (90, "...Ah, it's already this late. I need to decide what to do this afternoon."),
]


def main():
    a = cpk.load(str(ORIG))
    bytoc = {f.full_path: f for f in a.files}
    overlay = {}
    report = []
    for path in FILES:
        f = bytoc[path]
        d = a.file_bytes(f.toc_index)
        spans = C.parse_dialogue(d)
        assert len(spans) == len(TRANSLATIONS), (path, len(spans))
        runs = []
        for (s, e), (n, en) in zip(spans, TRANSLATIONS):
            budget = e - s
            raw = en.encode("utf-8")
            report.append(f"  {path} [{s},{e}) budget={budget} "
                          f"en={len(raw)} -> "
                          f"{'PAD +' + str(budget - len(raw)) if len(raw) < budget else 'EXACT'}")
            if len(raw) > budget:
                raise SystemExit(f"TOO LONG {path} {s}: {len(raw)} > {budget}")
            runs.append({"span": [s, e], "text": en})
        overlay[path] = {"kind": "srt", "runs": runs}

    dest = Path(__file__).with_name("ov_en_day101.json")
    dest.write_text(json.dumps({"files": overlay}, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    print("\n".join(report))
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()
