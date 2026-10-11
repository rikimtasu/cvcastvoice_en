#!/usr/bin/env python3
"""Append the Track-A findings to analysis_notes.md as a UTF-8 section."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent  # tools/ -> project root

NOTE = r"""

---

## 7. UPDATE (2026-10-12) -- UI text split into TWO sources

Earlier assumption "UI/menu text is baked pixels (323 `.pix`)" was too broad.
The remaining Japanese UI is in fact split into two independent sources.

### 7a. Name box + CV credit = TEXT (not pixels) -- SOLVED (Track A)

The on-screen speaker name and the CV credit are NOT baked. They are text in
two `PACK`-container files:

* `DATA/daihon/daihonbase.pac`  (stored 7160 -> extract 23311, COMPRESSED)
  -- speaker-name / chapter-title string table.
* `DATA/daihon/seiyubase.pac`   (stored 51612 -> extract 114501, COMPRESSED)
  -- CV (voice-actor) credit table; each record = kanji name + kana reading.

Structure: `PACK` magic + u32LE, then concatenated NUL-terminated UTF-8
strings. No absolute offset points at the name strings (verified: 0 LE-u32
occurrences of a name offset anywhere in the file), so slots are addressed by
walking -- which means **same-length or shorter, NUL-padded, in-place** edit is
safe and no internal pointer needs rewriting.

Tooling:
* `tools/pac_names.py`         -- locate + list name strings, dump detail json.
* `tools/pac_extract_names.py` -- build the translator skeleton.
* `tools/pac_trackA.py report|build` -- budget-check + write merged overlay
  (dialogue 7729 files **+** 2 `.pac`) and drive cvpatch build/verify.
* `tools/write_pac_en.py`      -- the English map (81 entries, 111 slots).
* `tools/pac_pac_diff.py`      -- proves the edit is surgical (see below).

Result: 111 name/CV slots translated, 0 over budget. Speaker name 天海春香 ->
`Haruka` (daihonbase @0x3a29), 如月千早 -> `Chihaya`; CV credit 西宮寺 美礼 ->
`Nishinomiya Mirei` (seiyubase @0xc9d2). The `.pac` is stored uncompressed in
the tail (cricodecs decompresses transparently; the surgical patcher stores raw).

The deep verify flags the 2 `.pac` as "non-text diff" ONLY because the
verifier's span model covers `.srt`/`.info`, not `.pac`. `tools/pac_pac_diff.py`
proves every changed byte is inside a declared overlay span (600 in daihonbase,
50 in seiyubase; 0 outside). So the edit is genuinely surgical.

### 7b. Menu button glyphs = BAKED PIXELS -- STILL OPEN (needs image edit)

These have ZERO text occurrences anywhere (confirmed by `tools/ui_source_map.py`):
`スキップ` (skip), `オート` (auto), `ウィンドウ` (window), `早送り`
(fast-forward). They live as glyphs inside `.pix` sprite atlases.

`.pix` container (cracked): root magic `FPIX` + u32LE filesize, then sub-chunks
`DPIX` (palette?) and `XPIX` (texture). NOT raw DDS/BC3 as first guessed.
numpy / PIL / cv2 are all importable in the WhisperJAV interpreter. Next step is
to decode one `XPIX` to (width, height, format, payload_offset) and identify the
exact sub-image + bytes for each button before OCR -> inpaint -> re-render ->
swap. `DATA/font/*.fon` (`FFON`) and the paired `.spr` (`SPRF`/`OBJT`) hold the
font + sprite placement and are the likely key to mapping a baked glyph region
back to its on-screen button.
"""


def main():
    p = ROOT / "analysis_notes.md"
    with p.open("a", encoding="utf-8") as fh:
        fh.write(NOTE)
    print(f"appended update -> {p} ({p.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
