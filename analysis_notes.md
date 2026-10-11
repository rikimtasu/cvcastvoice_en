# CV Casting Voice — English patch: format notes & status

Game: *CV Casting Voice* [BLJS10259] (PS3), Japanese.
Target: English text patch incl. DLC, plus a VWF decision.
Pristine source: `_backup\GameData.original.cpk` (326,234,976 B,
SHA256 `C5E61F84…D8822`). **Never modified.** All builds read from it.

Python: `C:\Users\User\AppData\Local\WhisperJAV\python.exe` (3.10.18).
Set `$env:PYTHONIOENCODING="utf-8"`. Write scripts, never inline `-c`.

---

## 1. Why the tool must be surgical

`cricodecs`' `cpk.load` → `replace_bytes` → `save()` **re-lays-out the archive**:
it re-sorts the TOC and shrinks the ETOC. Two builds that differ only in content
(`GameData_padded.cpk`, and the text-independent control `GameData_ctrl.cpk`)
**both hung on boot**. Conclusion, from the control: *rebuild structure, not the
translation text, is the bug.*

Also proven:
* `move_file()` does not survive `save()`.
* Calling `replace_bytes` at all (even byte-identical) triggers the reorder.
* cricodecs exports no CRILAYLA encoder, and only 5.9% of Japanese runs survive
  verbatim in their CRILAYLA stream — so we cannot re-compress.

## 2. CPK layout (all figures independently verified)

| field | offset | value |
|---|---|---|
| ContentOffset | `0xE7` u64be | 0x68800 (428032) |
| DataSize | `0xEF` u64be | 0x1369D800 (= EtocOffset − ContentOffset) |
| TocOffset | `0xF7` u64be | 0x800 |
| TocSize | `0xFF` u64be | 0x4AD50 |
| **EtocOffset** | **`0x107` u64be** | 0x13706000 |
| EtocSize | `0x10F` u64be | 0x19360 (103264) |
| GtocOffset/Size | `0x117`/`0x11F` | 0x4B800 / 0x18BD0 |
| Crc / TocCrc | `0x127`/`0x12F` | 0x75FAD062 / 0x4DD76C13 |
| Files | `0x137` u32be | 8400 |

Invariants: `filesize == ContentOffset + DataSize == EtocOffset + EtocSize`.
`file_offset % 2048 == 0` for all 8400 files (Align = 2048).

### TOC
`@UTF` at `0x810`, rows start `0x84F`, **stride 28**, 7 × u32be.

* `col4` = file size (stored bytes) — 8400/8400
* `col5` = extract size — 8400/8400
* `col6` = 0 everywhere
* **`col0[i] + 2048 == file_offset[i-1]`** — 8399/8399

⇒ `file_offset[0] = ContentOffset`, and for i ≥ 1 the runtime derives the offset
from the TOC. The "walk" model (`offset[i+1] = align2048(offset[i]+size[i])`)
fails for 8187... in fact fails at 12 points (first: row 469→470, the
`del_srt.bat` block is stored out of order), which proves the TOC column, not a
linear walk, is authoritative. Verified against literal file content, not just
against cricodecs' own arithmetic.

### ETOC
`ETOC` magic at 0x13706000, self-contained `@UTF`, holds per-file timestamps
(07 DE 03 1B 10 18 29 …). **Zero self-pointers.** Full exhaustive pointer scan of
the header (u32/u64, LE/BE) found only **one** real pointer into the ETOC:
`EtocOffset` @ `0x107`. The other hits were false positives:
* `0x10B` is the low half of the same u64be field;
* `0x229AD` is a straddle across TOC `col1`/`col2` (col1 there = 0x1371 = 4977);
* `0x5A254 / 0x5A298 / 0x5A30C` sit inside the GTOC where u32be values step
  through an arithmetic sequence 0x135E0000…0x13850000 — several of which exceed
  the archive size, so they cannot be offsets. 0x13710000 is merely a member of
  that sequence.

## 3. Patch algorithm (`tools\cvpatch.py build`)

1. Copy the pristine original.
2. Relay the modified file **uncompressed** (150 files in the original are stored
   raw already, so raw storage is supported) into a tail block starting at the
   current `EtocOffset`.
3. Move the ETOC to `align2048(insert_base + payload_bytes)`, so
   `filesize == EtocOffset + EtocSize` still holds. Only `EtocOffset` and
   `DataSize` in INFO are touched.
4. Per relocated file: patch `col4` + `col5` (row) and
   `col0 = new_offset − 2048` (**row k+1**). Never relocate row 0 (its offset is
   `ContentOffset`) or row 8399 (no `col0[8400]` exists).
5. Every other byte of the original archive is copied verbatim.

**Run text is replaced 1:1 with the same UTF-8 byte length**, so no internal
`.srt` field (which caches offsets/lengths) ever needs to change. English is
typically ~2× shorter than Japanese UTF-8, so this is feasible.

### `.srt` / `.info` text format
* `.srt` = `FSRT` chunk (magic + u32le total) wrapping `XSRT` (magic + u32le size).
* A dialogue run is `<~TAG>@n …text… @n ⋀u+22BF@n`.
  `@n` also occurs inside Japanese UTF-8, so the **only** reliable terminator is
  `b"@n\xe2\x8a\xbf@n"` (`@n` + U+22BF + `@n`). 7646/7646 files parse with this
  and 0 failures.
* `.info` (`DATA/daihon/*`) = a different container: u32 header block, then a
  trailing string block with segments separated by CRLF (101 files, 14445 segs).

## 4. Corpus

| | files | runs | text bytes |
|---|---|---|---|
| `.srt` | 7,646 | 37,902 | 3,183,001 (3.04 MiB) |
| `.info` | 101 | 14,445 | 631,798 (0.60 MiB) |
| **total** | **7,747** | **52,347** | **3.81 MiB** |

Average `.srt` run is 84 bytes of Japanese UTF-8.

## 5. Open work

* **Control test in flight.** `out\GameData_surg_ctrl.cpk` — one file
  (`DATA/srt_dh/P001_01.srt`), dummy ASCII filling every run span exactly.
  Everything else byte-identical. If this boots, archive surgery is proven and
  translation is the only remaining variable.
* **VWF / variable-width font**: still undecided, needs an in-game advance-width
  measurement.
* **UI/menu text is baked pixels** (323 `.pix`), needs OCR → inpaint → re-render
  → BC3 → in-place payload swap.
* **DLC**: 8 `.EDAT`s, fully NPDRM-encrypted. Decryption path identified
  (`make_npdata` + the 8 `.rap` keys) but not yet executed.
* CRC of `Crc`/`TocCrc` could not be reproduced (tried 14 CRC-32 variants over
  16 regions). Likely tool-side only.

## 6. Restore

`python tools\cvpatch.py restore` copies the pristine original back over the
installed copy.
