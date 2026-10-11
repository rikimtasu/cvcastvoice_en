#!/usr/bin/env python3
"""
Generic text-extent finder for the two .srt layouts found in GameData.cpk.

Layout A ("tag runs"):   <~TAG> @n ...text... @n (U+22BF) @n
Layout B ("text block"): header/table, then one or more contiguous text regions
                         delimited by NUL padding, with '\n' as the line
                         separator and 'L@n' / 'UP@n' as block terminators.

For patching we only need the *byte extents* that carry dialogue; the translator
then replaces text 1:1 with the same byte length, so nothing else in the file
has to change.
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

ORIG = C.ORIG

SEP_BLOCK = (b"\x0a\xe2\x8a\xbf@n", b"\x0a\xe2\x8a\xa5@n")
ATN = b"@n"


def _is_text_char(cp: int) -> bool:
    """Characters that appear inside dialogue text (kana/kanji/CJK/ASCII)."""
    return (0x20 <= cp <= 0x7E
            or 0x3000 <= cp <= 0x30FF     # CJK punct + kana
            or 0x4E00 <= cp <= 0x9FFF     # CJK unified
            or 0xFF01 <= cp <= 0xFF60     # fullwidth forms
            or cp in (0x22A5, 0x22BF, 0x2015, 0x2026, 0x00B7))


def text_extents(data: bytes, minlen: int = 8):
    """Maximal byte spans that decode as plain dialogue text (separators kept)."""
    spans = []
    i = 0
    n = len(data)
    while i < n:
        b = data[i]
        start = i
        ok = False
        # try to begin a text run here
        if b == 0x0A or 0x20 <= b <= 0x7E or 0xE3 <= b <= 0xE9 or b == 0xEF:
            # decode forward greedily
            j = i
            good = 0
            while j < n:
                b = data[j]
                if b == 0x0A:
                    j += 1
                    good += 1
                    continue
                if b == 0x40 and data[j:j + 2] == ATN:
                    j += 2
                    good += 1
                    continue
                try:
                    ch = data[j:j + 1]
                    # attempt utf-8 char
                    if b < 0x80:
                        if 0x20 <= b <= 0x7E:
                            j += 1
                            good += 1
                            continue
                        break
                    ln = {0xC2: 2, 0xC3: 2, 0xE3: 3, 0xE4: 3, 0xE5: 3,
                          0xE6: 3, 0xE7: 3, 0xE8: 3, 0xE9: 3, 0xEF: 3}.get(b)
                    if ln is None:
                        break
                    s = data[j:j + ln]
                    c = s.decode("utf-8")
                    if len(c) != 1:
                        break
                    if _is_text_char(ord(c)):
                        j += ln
                        good += 1
                        continue
                    break
                except Exception:
                    break
            if good >= max(2, minlen // 4):
                # strip trailing '@n'/separator noise off both ends
                spans.append((i, j))
                i = j
                continue
        i += 1
    return spans


def main():
    a = cpk.load(str(ORIG))
    lay = {"A": 0, "B": 0, "none": 0}
    totA = totB = 0
    bA = bB = 0
    examples = []
    for f in a.files:
        lp = f.full_path.lower()
        if not lp.endswith(".srt"):
            continue
        d = a.file_bytes(f.toc_index)
        if d[:4] != b"FSRT":
            continue
        runs = C.parse_dialogue(d)
        if runs:
            lay["A"] += 1
            totA += len(runs)
            bA += sum(e - s for s, e in runs)
        else:
            ex = text_extents(d)
            if ex:
                lay["B"] += 1
                totB += len(ex)
                bB += sum(e - s for s, e in ex)
                if len(examples) < 6:
                    examples.append((f.full_path, ex, d))
            else:
                lay["none"] += 1
    # .info
    nI = sI = byI = 0
    for f in a.files:
        if f.full_path.lower().endswith(".info"):
            d = a.file_bytes(f.toc_index)
            seg = C.parse_info_segments(d)
            if seg:
                nI += 1
                sI += len(seg)
                byI += sum(e - s for s, e in seg)

    out = [f"layout A (<~TAG>@n) files : {lay['A']}  runs={totA}  text={bA} B",
           f"layout B (text block) files : {lay['B']}  extents={totB}  text={bB} B",
           f"neither                    : {lay['none']}",
           f".info files                : {nI}  segments={sI}  text={byI} B",
           f"TOTAL dialogue segments    : {totA + totB + sI}",
           f"TOTAL text bytes           : {bA + bB + byI} "
           f"({(bA+bB+byI)/1048576:.2f} MiB)",
           "",
           "=== layout B examples ==="]
    for path, ex, d in examples:
        out.append(f"  {path}  {len(ex)} extents")
        for s, e in ex:
            out.append(f"      {s:5d}..{e:5d} ({e-s:3d}b) "
                       + repr(d[s:e].decode("utf-8", "replace"))[:120])
    txt = "\n".join(out)
    (C.WORK / "layouts.txt").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
