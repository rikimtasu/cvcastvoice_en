#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a clean UTF-8 roster from seiyubase.pac: record index, offset, kanji name,
kana, agency, age. Record = starts at a name+kana pair (kana follows kanji within
~40 bytes). Also print the offset of 八尾 伊月 so we get its record index.
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import cvpatch as C
from cricodecs import cpk

JP = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")


def main():
    a = cpk.load(str(C.ORIG))
    by = {f.full_path: f for f in a.files}
    d = a.file_bytes(by["DATA/daihon/seiyubase.pac"].toc_index)

    # collect (offset, text) for valid utf-8 NUL-separated fields
    fields = []
    start = 0
    while True:
        i = d.find(b"\x00", start)
        chunk = d[start:i] if i >= 0 else d[start:]
        if chunk:
            try:
                t = chunk.decode("utf-8")
                fields.append((start, t))
            except UnicodeDecodeError:
                pass
        if i < 0:
            break
        start = i + 1

    # a NAME record: kanji-ish text (>=2 chars incl kanji) whose NEXT field is its
    # kana reading (all kana) and appears within 32 bytes
    recs = []
    for idx, (off, t) in enumerate(fields):
        if not (2 <= len(t) <= 16 and JP.search(t)):
            continue
        # must be mostly kanji (not kana itself) -> name
        if not re.search(r"[\u4e00-\u9fff]", t):
            continue
        if idx + 1 >= len(fields):
            continue
        noff, nt = fields[idx + 1]
        if not re.fullmatch(r"[\u3040-\u309f\u30a0-\u30ffー\s・]+", nt or ""):
            continue
        if not (2 <= len(nt) <= 24 and noff - off <= 48):
            continue
        # look ahead for agency (スタジオ…/…) and age (NN歳) within this record
        agency = age = None
        for j in range(idx + 2, min(idx + 14, len(fields))):
            _, x = fields[j]
            if agency is None and x.startswith(("スタジオ", "アーツ", "青二", "賢", "81", "Vi")):
                agency = x
            m = re.fullmatch(r"[０-９0-9]{1,3}歳", x or "")
            if m and age is None:
                age = x
        recs.append((off, t, nt, agency or "", age or ""))

    lines = []
    lines.append("total records: %d" % len(recs))
    lines.append("%-4s %-8s %-18s %-20s %-14s %s" % ("idx", "offset", "name", "kana", "agency", "age"))
    target = None
    for n, (off, name, kana, agency, age) in enumerate(recs):
        lines.append("%-4d 0x%06x %-18s %-20s %-14s %s"
                     % (n, off, name, kana, agency, age))
        if "伊月" in name:
            target = n
    lines.append("")
    lines.append("八尾伊月 record index: %s" % target)
    Path("tools/work/_roster.txt").write_text("\n".join(lines), encoding="utf-8")
    print("wrote tools/work/_roster.txt records=%d target_idx=%s" % (len(recs), target))


if __name__ == "__main__":
    main()
