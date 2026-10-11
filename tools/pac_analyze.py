#!/usr/bin/env python3
"""
Structural analysis of the two name/CV database .pac files
( DATA/daihon/daihonbase.pac , DATA/daihon/seiyubase.pac ).

Model discovered from bytes:
  * Magic "PACK" at offset 0, then a u32 record count, some header words, and a
    block of concatenated null-terminated UTF-8 strings (character names /
    titles / bios).  seiyubase.pac interleaves a kana-reading string before each
    name; daihonbase.pac pairs a short label with longer prose.
  * After each name there may be additional fixed-size per-name control fields
    (font metrics / layout).  We treat ONLY the name bytes plus the contiguous
    NUL padding immediately after them as writable, so those control fields are
    never disturbed.

Output: work/pac_names_detail.json  -> { pac_path: [ {off,blen,nul_end,
                                                       slot_to_next,str}, ... ] }
        work/pac_names.txt          -> human dump.
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

ORIG = C.ORIG
PACS = ("DATA/daihon/daihonbase.pac", "DATA/daihon/seiyubase.pac")

# NUL-terminated UTF-8 string that is >=2 chars and has a CJK/kana/fullwidth char
STR_RE = re.compile(rb"(?:[\xc2-\xf4][\x80-\xbf]+){2,}\x00")
CJK = re.compile(r"[\u3000-\u9fff\uff01-\uff60]")


def collect_string_spans(data: bytes):
    sps = []
    for m in STR_RE.finditer(data):
        s, e = m.start(), m.end() - 1          # drop the trailing NUL
        try:
            txt = data[s:e].decode("utf-8")
        except UnicodeDecodeError:
            continue
        if len(txt) >= 2 and CJK.search(txt):
            sps.append((s, e))
    return sps


def main():
    a = cpk.load(str(ORIG))
    fmap = {f.full_path: f for f in a.files}
    detail = {}
    lines = []
    for pac in PACS:
        f = fmap[pac]
        data = a.file_bytes(f.toc_index)
        lines.append(f"=== {pac} ===")
        lines.append(f"  extract={f.extract_size} stored={f.file_size} "
                     f"magic={data[:4]!r} count(u32@4)={int.from_bytes(data[4:8],'little')}")
        sps = collect_string_spans(data)
        recs = []
        for sp in sps:
            s, e = sp
            blen = e - s
            # precise end of the contiguous NUL padding right after the string.
            # Never cross into following non-NUL control bytes (font metrics, etc.).
            q = e
            nul_end = q
            while q < len(data) and data[q] == 0:
                nul_end = q + 1
                q += 1
            recs.append({
                "off": s, "blen": blen, "nul_end": nul_end,
                "slot_to_next": nul_end - s,
                "str": data[s:e].decode("utf-8", "replace"),
            })
        detail[pac] = recs
        lines.append(f"  CJK strings: {len(recs)}")
        for r in recs[:25]:
            lines.append(f"    @{r['off']:#08x} blen={r['blen']:3d} "
                         f"nul_end={r['nul_end']:#08x} {r['str'][:40]!r}")
        if len(recs) > 25:
            lines.append(f"    ... ({len(recs)-25} more)")
        lines.append("")

    (C.WORK / "pac_names_detail.json").write_text(
        json.dumps(detail, ensure_ascii=False), encoding="utf-8")
    (C.WORK / "pac_names.txt").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:6]))
    print(f"\nwrote {C.WORK / 'pac_names_detail.json'}")


if __name__ == "__main__":
    main()

