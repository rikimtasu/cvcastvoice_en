# CV Casting Voice — English Patch

A code-only repository for building an **English text patch** for the PS3 visual
novel **CV Casting Voice** `[BLJS10259]` (Japanese). The patch is produced by
byte-surgical edits to the game's `GameData.cpk` archive — no recompression, no
rebuild — so the original archive layout is preserved and the game boots.

> **Copyright.** This repo contains **no game assets**. `*.cpk` and `_backup/`
> are git-ignored, as is all extracted/translation data under `tools/work/`.
> Only the tooling (`tools/*.py`), notes, and this README are tracked.

---

## Status

| Track | Scope | State |
|---|---|---|
| **Dialogue / info** | 7,646 `.srt` + 101 `.info` (52,347 runs, 3.81 MiB JP) | ✅ Translated — 0% Japanese remaining |
| **Speaker name + CV credit** (Track A) | `daihonbase.pac`, `seiyubase.pac` | ✅ Translated — 111 name/CV slots |
| **Menu buttons** (Track B) | スキップ / オート / ウィンドウ / 早送り | 🚧 Open — baked `.pix` pixels, needs image edit |
| **DLC** | 8 `.EDAT` (NPDRM-encrypted) | 🚧 Open — decryption path identified, not run |
| **VWF / variable-width font** | Latin text wrapping | 🚧 Open — needs in-game advance-width probe |

The patched archive `out/GameData_en.cpk` (335.5 MiB) is **built and verified**:
7,731 files relocated into the tail, 669 left at original offsets, **0 changed
bytes outside declared text spans**.

---

## Why surgical (not `cpk.save()`)

`cricodecs`' `cpk.load` -> `replace_bytes` -> `save()` **re-lays-out the
archive** (re-sorts the TOC, shrinks the ETOC). A control build that changed
*no translation text at all* still hung on boot — proving the re-layout, not the
text, is the bug. `move_file()` does not survive `save()`, and calling
`replace_bytes` (even byte-identical) triggers the reorder.

So `tools/cvpatch.py build` never calls `save()`. Instead it:

1. Copies the pristine original byte-for-byte.
2. Relays each modified file **uncompressed** into a tail block starting at the
   current `EtocOffset` (150 files in the original are already stored raw, so
   raw storage is supported).
3. Moves the ETOC to `align2048(insert_base + payload_bytes)`, touching only
   `EtocOffset` and `DataSize` in INFO so `filesize == EtocOffset + EtocSize`
   still holds.
4. Per relocated file: patches TOC `col4`/`col5` (sizes) and `col0 = new_offset
   - 2048` on the **next** row. Never relocates row 0 or the last row.

Every other byte of the original is copied verbatim.


---

## Game data formats (cracked)

### Archive (`GameData.cpk`)
CPK with `ContentOffset = 0x68800`, `Align = 2048`, 8400 files, an ETOC with
per-file timestamps, and a single real header pointer into the ETOC
(`EtocOffset` @ `0x107`). The **TOC column**, not a linear offset-walk, is
authoritative (the walk fails at 12 points where blocks are stored out of order).
See `analysis_notes.md` section 2 for the full field map.

### Dialogue (`.srt` = `FSRT`->`XSRT`; `.info`)
A dialogue run is `<~TAG>@n ...text... @n<U+22BF>@n`. `@n` also appears inside
Japanese UTF-8, so the **only reliable terminator** is `b"@n\xe2\x8a\xbf@n"`
(`@n` + U+22BF + `@n`). All 7,646 `.srt` parse with 0 failures. Text is replaced

---

## Repository layout

```
tools/
  cvpatch.py            build / verify / restore the patched CPK
  apply_translations.py build via overlay; coverage/budget report
  pac_trackA.py         Track A (.pac name/CV) budget-check + build+verify
  write_pac_en.py       the English map for .pac names/CVs (81 entries)
  pac_names.py          locate/list .pac name strings
  pac_extract_names.py  build the translator skeleton
  pac_pac_diff.py       prove the .pac edit is surgical (diffs in-span)
  ui_source_map.py      where each on-screen UI string lives (text vs pixels)
  inspect_pix.py        .pix / image-file survey (extensions, sizes, magic)
  pix_struct.py         FPIX/DPIX/XPIX structure + .spr/.fon dumps
  pix_probe.py          locate + characterize the .pix pixel payload
  ... + many analysis/audit helpers (audit_*, check_*, dump_*, diag_*)
  work/                 scratch: batches, per-batch EN text, scan output (git-ignored)
analysis_notes.md       detailed format notes + status (see section 7 for the UI split)
```

---

## Setup

No machine-specific paths — everything resolves **relative to the repo root**
(`tools/../`), so the tooling works from any clone location.

Requires **Python 3.10+** with `cricodecs`, `numpy`, `Pillow`, and `opencv-python`:

```powershell
python -m pip install -r requirements.txt
```

(Verified on Python 3.10.18. Set `$env:PYTHONIOENCODING = "utf-8"` on Windows so
`print` and the JSON writers don't mangle the Japanese source strings.)

### Path configuration (env vars / flags)

| Purpose | Env var | Default | CLI override |
|---|---|---|---|
| Pristine `GameData.cpk` | `CVC_ORIG` | `<repo>/_backup/GameData.original.cpk` | `--orig PATH` |
| Pristine `SoundData.cpk` | `CVC_SOUND` | `<repo>/_backup/SoundData.cpk` | — |
| Deployed game archive | `CVC_INSTALL` | *(none — you must set it to restore)* | `--install PATH` |
| Built archive (analysis scripts) | `CVC_BUILT` | `<repo>/out/GameData_en.cpk` | — |
| Scratch/translation work dir | `CVC_CWD` | the `tools/work/` dir holding each script | — |

Put the pristine originals in `<repo>/_backup/` (git-ignored) and the tooling
finds them with **no configuration**. `_backup/GameData.original.cpk` is the
read-only source every build copies from; it is never modified.

---

## Build

Build, verify, and restore — paths auto-resolve from the repo root as above.

```powershell
# 1. Merge dialogue overlay + Track A .pac overlay, then build + auto-verify:
python tools/pac_trackA.py build --out out/GameData_en.cpk

# 2. Strongest integrity check — only text-span bytes may differ:
python tools/cvpatch.py verify --file out/GameData_en.cpk --deep

# 3. Restore the pristine original over an installed copy (set the target once):
python tools/cvpatch.py restore --install "<RPCS3 games>/CV Casting Voice [BLJS10259]/PS3_GAME/USRDIR/DATA/GameData.cpk"
# ...or set CVC_INSTALL to that path once and just run: python tools/cvpatch.py restore
```

The deep verify's "2 non-text diffs" for the `.pac` files are **expected** — the
verifier's span model covers `.srt`/`.info` only. Run
`python tools/pac_pac_diff.py` to confirm every `.pac` change is inside a
declared string span.

---

## Install

Copy `out/GameData_en.cpk` over the game's archive:

```
<RPCS3 games>\CV Casting Voice [BLJS10259]\PS3_GAME\USRDIR\DATA\GameData.cpk
```

---

## Known limitations

- `Crc` / `TocCrc` header CRCs are not reproduced (14 CRC-32 variants tried);
  the game does not appear to enforce them.
- Menu-button glyphs (Track B) still require an image
  OCR -> inpaint -> re-render -> swap pass on the `.pix` atlases.
- DLC (`.EDAT`) is fully NPDRM-encrypted; decryption path identified, not run.

1:1 at the **same UTF-8 byte length** (English is typically shorter), so no
internal `.srt` offset/length field ever changes.

### Name / CV tables (`.pac` = `PACK`) — Track A
Speaker names and voice-actor credits are **text**, not pixels:

- `DATA/daihon/daihonbase.pac` — speaker-name / chapter-title table (compressed
  7160 -> 23311 by cricodecs, decompressed transparently).
- `DATA/daihon/seiyubase.pac` — CV credit table, kanji name + kana reading
  (compressed 51612 -> 114501).

Layout is `PACK` + u32LE + concatenated **NUL-terminated UTF-8 strings**. No
absolute offset points at the name strings, so slots are found by walking and
edited **in place, NUL-padded, same-or-shorter** — no pointer rewrites.

### Sprite atlas (`.pix` = `FPIX`) — Track B (baked)
Menu-button glyphs (スキップ / オート / ウィンドウ / 早送り) have **zero** text
occurrences and live inside `.pix` atlases: root `FPIX` + u32LE filesize, then
`DPIX` (palette?) and `XPIX` (texture) sub-chunks — **not** raw DDS/BC3.
`numpy`, `PIL` and `cv2` are all available in the build interpreter. The paired
`.spr` (`SPRF`/`OBJT`, sprite placement) and `.fon` (`FFON`, font) map a baked
glyph region to its on-screen button.
