#!/usr/bin/env python3
"""
Extract the highest-value UI name strings for Track A into a ready-to-edit
translation skeleton (work/pac_en.json), so a human/translator fills English.

We pull:
  * daihonbase.pac: the short name-buffer strings (the speaker-name box). These
    are the ~<=16-byte CJK strings that look like person names / short labels.
  * seiyubase.pac: the CV credit name(s) near the top (the on-screen VA credit).
Everything is left with an empty English value ("") for the translator to fill.
Existing entries in pac_en.json are preserved (never clobbered).
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C

CJK = re.compile(r"[\u3000-\u30ff\u4e00-\u9fff\uff01-\uff60]")


def main():
    detail = json.loads((C.WORK / "pac_names_detail.json")
                        .read_bytes().decode("utf-8"))
    enmap = {}
    p = C.WORK / "pac_en.json"
    if p.exists():
        enmap = json.loads(p.read_bytes().decode("utf-8-sig"))

    # daihonbase: short strings (name-box candidates). Keep blen <= 24 and
    # contains a name-space or is 2-5 kanji/kana tokens.
    dh = detail.get("DATA/daihon/daihonbase.pac", [])
    names = []
    for r in dh:
        s = r["str"]
        if r["blen"] <= 24 and CJK.search(s) and "\n" not in s \
                and "　" in s or (r["blen"] <= 12 and re.fullmatch(
                    r"[\u3040-\u30ff\u4e00-\u9fff]{2,6}", s)):
            names.append(s)
    # seiyubase: the VA credit names (records that are a person full name with a
    # wide/narrow space, near a kana reading). Keep blen<=30, no newline.
    sv = detail.get("DATA/daihon/seiyubase.pac", [])
    cvs = [r["str"] for r in sv if r["blen"] <= 30 and "\n" not in r["str"]
           and ("　" in r["str"] or " " in r["str"])
           and re.search(r"[\u4e00-\u9fff]", r["str"])]

    print(f"daihonbase name candidates : {len(names)}")
    for s in names[:40]:
        print(f"   {s}")
    print(f"\nseiyubase CV-name candidates : {len(cvs)}")
    for s in cvs[:20]:
        print(f"   {s}")

    added = 0
    for s in names + cvs:
        if s not in enmap:
            enmap[s] = ""
            added += 1
    p.write_text(json.dumps(enmap, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nadded {added} skeleton entries; pac_en.json now has {len(enmap)}")
    print(f"-> {p}")


if __name__ == "__main__":
    main()
