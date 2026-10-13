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


---

## 7. UI text: what's baked pixels vs. what's a data string (VERIFIED, 2026-10-12)

Earlier assumption "UI/menu text is baked pixels (323 `.pix`)" was too broad.
The remaining Japanese UI is in fact split into two independent sources.

### 7a. Name box + CV credit = TEXT (not pixels) -- SOLVED (Track A)

The on-screen speaker name and the CV credit are NOT baked. The game renders
them with its runtime font, so they are ordinary text we can swap as bytes.
They live in two compressed `PACK`-magic name DBs:

* `DATA/daihon/daihonbase.pac`  (stored 7160 -> extract 23311, COMPRESSED)
  -- speaker-name box, scene titles, bios.
* `DATA/daihon/seiyubase.pac`   (stored 51612 -> extract 114501, COMPRESSED)
  -- CV (voice-actor) credit table; each record = kanji name + kana reading.

Verified layout: `PACK` magic, u32 count, then concatenated **NUL-terminated
UTF-8** strings. No absolute offset points at them (0 hits for the string
offset), and the game walks them. So we overwrite **only the name bytes plus the
contiguous NUL padding immediately after** (`[off, nul_end)`), never the trailing
per-name control/font bytes — keeping the file the same extract length (cricodecs
transparently decompresses; our surgical patcher then stores it uncompressed).

Pipeline: `tools\pac_analyze.py` (structure -> `work\pac_names_detail.json`) ->
`tools\write_pac_en.py` (map -> `work\pac_en.json`) -> `tools\pac_trackA.py build`
(merges the 2 `.pac` into `work\overlay.json` -> `work\pac_overlay.json`, builds
`out\GameData_en.cpk`, verifies). Deep check: `tools\pac_verify_deep.py` proves
every changed byte is inside a name slot (**661 changed bytes, 0 outside** in
daihonbase; 50 CV names in seiyubase). 111 UI slots translated, 0 over budget.

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

---

## 8. GAMEDATA save structure (NPJB00558) — 名鑑 trust/scripts mapping

File: `dev_hdd0/home/00000001/savedata/NPJB00558-GAMEDATA-/GAMEDATA`, **19904 B**.
Snapshots: `tools/work/snaps/{T0,T1,T2}/GAMEDATA.bin` (real scenario-clear diffs).

### 8.1 What is PROVEN (from live-load behaviour)

* **No checksum anywhere.** A hand-edited save loads and is *displayed as-is* —
  the game does NOT rewrite or reject it (`fab->live` diff = 0 changed bytes
  after booting the 名鑑). So byte edits are safe from rejection; the risk is
  only "the displayed number won't be what you wanted".
* **Most of the file is byte-mirrored at +0x2a8** (90.9% of bytes match their
  +0x2a8 partner; the 0x1100 stats block is mirrored *exactly*). Any per-field
  edit must be applied to BOTH the primary and the +0x2a8 copy.
* Scalar values are **big-endian u32** at 4-byte-aligned bases.

### 8.2 CORRECTION — the earlier "trust meter" model was WRONG

`tools/save_fabricate.py` originally set `0x1117` and `0x117b` to `0xFF` and
called them "trust meters". **They are not.** They are the **low byte of two
big-endian u32 stats** at base `0x1114` (value 60->70) and `0x1178` (0->120).
Setting the low byte to 0xFF just made those two unrelated stats = 255. Result:
八尾 伊月 (a 新人/newcomer) still showed 信頼度 **4/10** and 演じられる台本 **20%**
after install. Do not trust those two offsets.

### 8.3 名鑑 trust is PER-ACTOR and (almost certainly) DERIVED

Screenshot proof: with the cleared counter forced to **125/125**, 八尾 伊月 still
read 4/10 stars and 20% scripts. Therefore:

* The global cleared counter `0x0140` (u32 BE, mirror `0x0320`) does **NOT**
  drive 名鑑 trust. Total scenarios = 125 (`0x0148`, constant). Counter went
  99 -> 117 across T0->T2 (i.e. +18), matching ~18 cleared in that span.
* 信頼度 (10 stars) and 演じられる台本 (a %) are computed **per actor** from how
  many of *that actor's* scenarios are cleared. 八尾 伊月 is a newcomer with few
  appearances, so she sits at 20% / 4 stars regardless of the global counter.

### 8.4 Structures located so far

* **Record bank** `0x00c0` (mirror `0x02a0`): 32-byte records
  `[u32 BE count][u32 BE done][28B pad]`. done-field -> `0xFFFFFFFF` on clear.
  Only ~3-4 records are populated here; NOT the full 125-scenario store.
* **0x1100-0x11d0**: sparse global-stats blob (money/fans/etc.), values at
  irregular spacing, mirrored exactly at +0x2a8. NOT per-actor.
* **0x3dc0-0x3fc0**: 512-byte block, 506/512 bytes = 0xFF (a large all-set
  bitfield / flags region). Constant across tags except a couple bytes.
* **0x0190-0x02a0**: mixed small-value region (part of the same stats area).

### 8.5 What is STILL UNKNOWN / next step

The **125-entry per-scenario completion store** (and the actor->scenario mapping)
has NOT been isolated yet — a popcount scan for a +18-growing, ~125-capacity
bitfield found no single clean window. To map 名鑑 trust we need a **controlled
single-actor experiment**: snapshot, clear exactly ONE scenario that features a
known 名鑑 actor, snapshot again, diff — the bytes that move are that actor's
completion/trust drivers. Tools: `tools/save_castdiff.py snapshot --tag X` /
`diff --a X --b Y`; analysis helpers in `tools/work/{analyze_trust,probe_offsets,
scan_structure,map_nonzero,verify_struct,decode_completion,find_scenario_flags,
diff_live}.py`.

### 8.6 DEFINITIVE NEGATIVE RESULT (static, no gameplay) — 2026-10-13

Exhausted the "reconstruct from 3 snapshots" idea. All three independent methods
agree that 名鑑 trust/scripts% **cannot be rebuilt from GAMEDATA bytes** with the
data on hand:

1. **Ground-truth search** (`ground_truth_search.py`): live save shows 八尾 伊月
   = trust 4, scripts 20%. Literal byte `4` occurs 13x, `20` (0x14) occurs 1x —
   both as scattered noise. **No regular-stride per-actor array exists** (best
   stride hit 66/4975 = random). File is mostly zeros + sparse records.
2. **Byte/bitfield hunt** (`find_by_count.py`, `bitfield_hunt.py`): NO window
   anywhere (any byte offset, any bit offset, MSB or LSB order) has a 125-bit
   popcount matching the cleared counter 99(T0)/117(T2). The only +big cluster
   is the 0x00c0 record bank (sliding-window artifact of done-fields -> 0xFF).
3. **EBOOT is encrypted**: `EBOOT.BIN` is an SCE SELF (key_rev 0x1c, LV0), the
   ELF at +0x90 is PPC64 but the code segments are high-entropy/encrypted (entry
   `0x2d8ba0` disassembles to garbage). No readable strings. So the save-write
   routine can't be inspected without SELF decryption (erk/riv keys, per
   PkgLens). RPCS3 cache holds only PPU shader/program fragments, not a
   decrypted EBOOT.

**Conclusion:** trust is per-actor and derived from a completion representation
we can't decode from 3 non-clean snapshots, and the binary that defines it is
encrypted. Two viable paths remain, both out of current scope:
* **Controlled experiment** (fastest, reliable): 1 clean scenario clear + diff.
* **SELF decrypt + PPC64 disasm + trace save-write** (slow, uncertain).

Do NOT re-attempt a blind byte edit — the previous "trust meter" model was wrong
and cost a full install/restore cycle.

---

## 9. Decrypted EBOOT (RPCS3 dump) — save system located

`tools/work/EBOOT.elf` (decrypted EBOOT supplied by user). Capstone PPC64 with
`skipdata` decodes **567,749** instructions (was 5,071 without it). Identity
map: file offset == vaddr for the exec segment (off 0x230, vaddr 0x10230,
size 0x22a714).

### 9.1 Save I/O routine FOUND (string XREF, raw-word verified)

The filename/save-slot strings live in the blob 0x242900–0x242c00:
`NPJB00558-GAMEDATA-`, `GAMEDATA`, `OPTION`, `CASTDATA.DAT`, `ICON0.PNG`.
The **save schema key names** live at 0x23D560–0x23D820 and are the real
vocabulary of the save model:

```
obicas_top  obiscenario  obiappre  obiappre2  obichara  obicast  obiunlock
cas_top  scenario  character  unlock  skil
rookie  young  mainstay  veteran          (rank ladder)
```

None appear as literal text in the save file — the save is a **serialized keyed
tree**, not string-keyed on disk. The serializer lives in the big dispatcher at
**0x4b8fc** (switch on category r4 = 0..6) whose case-5/6 handler at
**0x4c5c0–0x4c718** writes each key with the pattern:

```
key   = <key string>            ; lis r4,0x24 ; addic r4,r4,-0x2aXX
node  = 0x1268b8(key, 0)        ; strbuf append key name (string builder)
val   = 0x29a24(node, ctr)      ; value getter
ctr   = 0x29674(ctr, r26+off, val) ; store into in-memory struct r26+0x1c0+4*i
```

`0x1268b8` = string-buffer writer (appends key to buffer at r30+0x108, tracks
len at r30+0x110). Key→struct-slot map (r26+offset):
`obiunlock`→0x1c0, `cas_top`→0x1c4, `scenario`→0x1c8, `character`→0x1cc,
`unlock`→0x1d0, `skil`→0x1d4.

**Key structural insight:** the save is a nested key→value map (like a JSON
tree) built at runtime and flattened to file by a generic map serializer. The
`scenario`/`character`/`unlock` keys are the top-level categories the 名鑑 reads.

### 9.2 Structural map from the REAL trial diffs (BASE→T0→T1→T2)

Cleared counter went 99(T0)→117(T2) across real in-game clears. Full byte-diff
(75 changed offsets) shows the file is **double-buffered / mirrored**:

* block `0x1100–0x1200` mirrors to `0x13a8–0x14a8` (**+0x2a8**)
* block `0x2000–0x2a00` mirrors to `0x2800–0x3200` (**+0x800**)

Field semantics decoded from transitions:

| offset | behavior | meaning |
|--------|----------|---------|
| `0x0063` | 5→6→7 (BASE=7) | a small index/counter |
| `0x0143` | 0x63(99)→0x75(117) | **cleared-scenario counter** (mirror `0x0323`) |
| `0x11c7` | 0x9e→0xc2→0xe0 (+0x24 each) | **cumulative clear count** (mirror `0x146f`) |
| `0x1187` | 0xdc→0x96→0xdc | toggled stat (mirror `0x142f`) |
| `0x1117` | 0x46→0x3c→0x46 | low byte of BE u32 stat (mirror `0x13bf`) |
| `0x117b` | 0x78→0x00→0x78 | low byte of BE u32 stat (mirror `0x1423`) |
| `0x2123` | 0x20→0x00→0x20 | **flag bit** (mirror `0x2923`, +0x800) |
| `0x21bf` | 0xfe→0xfa→0xfe | flag byte (mirror `0x29bf`) |
| `0x3f00` | `01 0c ff ff…` | **bitfield of cleared markers** (0xff runs) |

The `0x3f00` region (long 0xff runs after a `01 0c` header) and the `0x2123`
flag bit are the strongest candidates for **per-scenario completion flags** that
the 名鑑 aggregates into per-actor trust. Still need one more clean single-clear
diff keyed to a *known* 名鑑 actor to pin which flag → which actor's trust.

### 9.3 Tooling added

`tools/work/`: `raw_xref.py` (raw-encoding XREF), `hand_decode.py` (raw word
decode), `raw_serializer.py` (raw-word key-region XREF — capstone-independent),
`find_serializer.py`, `dispatch.py`, `container.py`, `trial_diff.py`,
`struct_analysis.py`, `bitfield_map.py`, `record_layout.py`, `save_keys.py`.


## 10. Static decode from the decrypted EBOOT (session 4)

**Tooling:** `tools/work/{ppc_disasm,elf_strings,raw_xref,hand_decode,ctx_2a14,
save_xref_verified,save_keys,imports,tail_bits,tail_change,tail_records,
decode_records,sum_groups,mirror_check,find_block,tag_emit}.py`.

### 10.1 Capstone fix (was silently wrong)
The earlier sweep only decoded ~5k instructions. Root cause: data bytes in the
`.text` break capstone's linear sweep. Fix in `ppc_disasm.py`: build the
disassembler with `skipdata=True` so `.byte` pads are tolerated.
Result: **567,749 instructions** decoded. With skipdata on, capstone's
`is_...`/register checks became unreliable, so all XREF now uses **raw 4-byte
word decoding** (`opcode<<26`, rt/ra/imm16) with a per-register absolute base
tracked from `lis`/`addis(ra=0)` and sign-correct `addic/addi` completions.

### 10.2 Addressing mode (resolved)
No `PT_DYNAMIC`: this is a statically-linked PS3 EBOOT (cellFs*/cellSave* are internal,
not GOT imports), so import-XREF (`imports.py`) is a dead end. **Global/string
addressing is ABSOLUTE**: `lis rX, hi` ; `addic rX, rX, lo16_signed`. Confirmed
against raw words (e.g. `3c800024` / `3084d5c4`).

### 10.3 Save schema vocabulary (found as inline strings @0x23D560)
`scenario`, `character`, `unlock`, `skil`, `cas_top`, `cast_top`, and the rank
ladder `rookie / young / mainstay / veteran`. The save-file header block
(`NPJB00558-GAMEDATA-` dir; `GAMEDATA`/`OPTION`/`ICON0.PNG`/`PIC1.PNG`) is a
`char*` descriptor struct; the dispatcher writes each key via
`lookup(0x1268b8) -> get(0x29a24) -> store(0x29674)`.

### 10.4 On-disk format (definitive)
The file is **variable-length serialized TLV, NOT a fixed bitfield**:
- `0xff` = bool-true element (a cleared scenario).
- `01 <count>` = integer record (group header + count).
- Layout is **double-buffered**: two complete copies at stride **0x800**
  (e.g. `0x2123`->`0x2923`, `0x21b9`->`0x29bf`), with header sub-mirrors at
  +0x180 (`0x143`->`0x323`) and a wider progress block mirrored at ~+0x2a8
  (`0x1117`->`0x13bf`, `0x117b`->`0x1423`, `0x11c7`->`0x146f`).

Verified group records (0x20 stride): `[0xc2]=14, [0xe2]=14, [0x102]=205,
[0x2a2]=14, [0x2c2]=14, [0x2e2]=205` at BASE; the `14`s drop to `13` and the
`205`s to `159` after the trial clears. The cleared counter `0x143`
(117->99) is an **independent aggregate**, not the sum of these group counts
(which are cumulative totals that also move).

### 10.5 Why per-actor trust is not a flat offset
Because the tail is serialized TLV with `0xff`-as-true and `01 <count>` headers,
"which scenario belongs to trust" is the **ordinal position in the flattened
tree**, gated by the serializer's tag table -> not a fixed byte. My earlier
`0x1117`/`0x117b` guesses were low bytes of unrelated BE-u32 stats.

**Remaining link:** which ordinal trust flag feeds a specific actor's trust requires either
(a) decoding the serializer tag table fully, or (b) one controlled experiment:
clear a single scenario with a *known* actor, snapshot, and read which
ordinal flips. The static work has now localized exactly where to look.


## 11. Serializer internals — type dispatch, record writer, keyed hashmap (session 5)

The serializer is a C++ reflection/serialization engine reached through the
194-entry **lazy-thunk dispatch array at 0x2d00a8**. Each thunk `k` is
`r12 = *(0x2d0000 + 0xa8 + 4k)` then `bctr` (a virtual call). 0x2d00a8 is an
array of `{fnptr, toc}` pairs whose targets (`0x1feec4…`) are tiny field
accessors — this table is the **type-descriptor/vtable registry**, not the writer.

### 11.1 The type-switch writer (func 0xef4e4) — THE TAG TABLE
`0xef4e4` is a giant `switch (type_id)` (on r30). Binary-search style compares
(`cmpwi r30,N ; beq handler`) over type ids roughly `-0xa … 0x100`. Extracted
cases (handler 0x…):

```
type 0x00 -> 0xf2774   type 0x01 -> 0xef8f0   type 0x37 -> 0xf0a58
type 0x38 -> 0xf1710   type 0x39 -> 0xf0eb0   type 0x3a -> 0xf10f4
type 0x3b -> 0xf1364   type 0x40 -> 0xf1a88   type 0x85 -> 0xf25e8
type 0x87 -> 0xefa70   type 0x94 -> 0xf2350   type 0x95 -> 0xf26a4
type 0x96 -> 0xf1710   type 0x9a -> 0xf0fe0   type 0x9b -> 0xf1710
type 0xa3 -> 0xf0d50   (+ more; scan window was 0x600B — widen to capture all)
```

`type 0x01 -> 0xef8f0` is the **main recursive serializer** (calls the most
sub-routines, incl. `0xf51ac` which recurses back into this dispatcher). Handler
clusters call three write primitives:
* `0xd8a44` = array index accessor `if(i<len) return data[i]`
* `0xd8f44` = **record/field writer** (writes a C++ record struct)
* `0xd8dbc` = **keyed map lookup** (hashmap get)

### 11.2 The 0xff flag lives in a C++ record struct (func 0xd8f44)
`0xd8f44` builds a per-field record; the offsets and constant writes are:
```
0x00  = value (stw r7)        0x04 = r28 (state)     0x08 = -1
0x0c  = 0                     0x10 = stb 0xff   <-- THE cleared/true marker
0x14  = stw 0x3f80 (float 1.0) 0x18 = stw 0x3f80 (float 1.0)
```
So the on-disk `0xff` bytes are **struct field +0x10 = "present/true"** of a
record, and the `01 <count>` bytes are integer fields. This matches §10.4.

### 11.3 Fields are stored in a NAME-KEYED hashmap (func 0xd8dbc)
`0xd8dbc`: `keys = *(obj+0x18); if (idx < keys[idx])` then `hashmap_get(0x86da4,
container, key)`. Combined with §9.1/§10.3 the save model is:
`root -> {scenario, character, unlock, skil, cas_top, cast_top, obi*} -> hashmap`
keyed by the vocabulary strings at 0x23D560, each value a record from §11.2.

### 11.4 Next step to finish the trust link
The per-actor trust the 名鑑 shows is the **aggregation over the `scenario`
map** gated by each record's `+0x10` flag (§11.2). To name *which* record ->
*which* actor, decode the scenario map's key list (the string table feeding
`0xd8dbc`'s hashmap) — i.e. enumerate the scenario keys at 0x23D560 that map
into the record array, then the k-th cleared record = k-th scenario. That is a
pure table read (no gameplay). Fallback remains the controlled single-clear diff.

## 12. Key list decoded + serializer engine identified (session 6) — COMPLETE

Tooling: `clean_dump.py`, `final_dump.py`, `find_keylist.py` (output
`_keys.txt`, `_final.txt`, `_keylist.txt` — UTF-8 so JP renders).

### 12.1 The serializer engine is CRI Middleware (ADX) — type table @0x30def8
The `switch (type_id)` in `0xef4e4` (§11.1) dispatches on CRI serialization
types. The ordered type-name array at **0x30def8** (and CRI variant at 0x30e200):
```
Uint8 Sint8 Uint16 Sint16 Uint32 Sint32 Uint64 Sint64
Float32 Float64 String VLData CBNData
```
So on disk: each value is a tagged (type,data) pair. `0xff` bool-true / `01 <n>`
int (§10.4/§11.2) are the CRI `Uint8`/`Sint8` encodings of small values; `String`
values are length-prefixed. This is a **generic CRI key→value serializer**, not a
hand-rolled bitfield — which is exactly why flat-offset searches (§8.6) failed.

### 12.2 Concrete scenario / character KEYS (the hashmap key list)
Entries are keyed by **numeric IDs formatted into fixed asset names** (not by the
category strings themselves). The key builders found inline:

| entity | key format | example path |
|--------|-----------|--------------|
| scenario (work) | `sakuhin%03d` | `/DATA/sakuhin/sakuhin000.pac` |
| character | `ca%03d` (+ `ca%03d_2`) | char asset id |
| voice cast | `vic%03d` | `/DATA/vaIcon/ctva%03d.pix`, `vic%03d/M%03d.acb` |
| dialogue | `D%03d_serif` | `/DATA/daihon/D%03d_serif.info` |
| album bg | `alb_%03d` | `/DATA/spr_ab/alb_%03d.spr` |

So **scenario #k <-> `sakuhin%03d` with k**, and **character #c <-> `ca%03d`**.
The 名鑑's per-actor record (`cha, n_nml…n_ter, va, profile%d, secret%d,
category, voice, sankaku, chaback, ca%03d` @0x23da80) is the character entry;
its trust is aggregated from all `sakuhin` (scenario) records whose cast list
includes that `ca%03d` and whose `+0x10` cleared-flag is set (0xff).

### 12.3 Trust-reward table @0x2e1f14 (名鑑 UI)
```
信頼度１でオープン … 信頼度１０でオープン   (trust 1..10 each unlock an item)
Ａ型 Ｂ型 Ｏ型 ＡＢ型 ？？型                 (blood-type profile field)
```
Confirms 名鑑 trust is a **1..10 ladder**; each actor's `va`/profile record shows
the trust level and unlocked reward.

### 12.4 FINAL mapping (closes §11.4)
```
GAMEDATA file
 └─ CRI keyed tree (Uint8/Int/String TLVs, double-buffered @0x800)
     ├─ scenario : { sakuhin000..sakuhin%03d -> record{+0x10=cleared?} }
     ├─ character: { ca000..ca%03d          -> record{n_*,va,trust 1..10} }
     ├─ unlock / skil / cas_top / obi*      : flags & progress
     └─ cleared-counter @0x143 (aggregate)
```
Per-actor trust = count of cleared `sakuhin` records referencing that `ca%03d`,
mapped onto the 1..10 ladder of §12.3. This is now fully localized statically.
The only remaining unknown is the exact **cast list inside each scenario record**
(i.e. which `ca%03d` a given `sakuhin%03d` credits) — resolvable either by
reading the scenario PACs (`sakuhin%03d.pac`) or one controlled single-clear diff
keyed to a known actor. No blind edits.

## 13. Serializer core, statically traced (EBOOT disassembly)

The static trace of the save (de)serializer is now complete. Key results:

- **Serializer dispatcher @0xef4e4.** A large type-switch on a type id (r30,
  values 0x00,0x01,0x37-0xa3…). Each case writes a type tag byte into the output
  stream (0x00=null/false, 0x01=int, 0xff=bool-true) and dispatches to a helper.
  16 explicit cases were extracted; the value range implies ~100 serializable
  types. This is the **type-tag table** for the on-disk TLV stream.
- **Container evidence (Dinkumware STL).** Helper 0xd8a44 is `std::vector::at`
  (`sldi r3,r5,2; lwzx` with a bounds check); 0xf51ac tests a size/capacity bit
  at struct offset +0x60. The save object is built on `std::vector` + `std::map`.
  => per-actor state is a **keyed map**, not a fixed-offset array. This is why
  every fixed-offset/bitfield scan of the raw save came up empty.
- **Save I/O dispatcher @0x4b8fc** (case handler 0x4c5c0-0x4c718): per-key
  `lookup(0x1268b8) -> get(0x29a24) -> store(0x29674)`. Reached via C++ virtual
  call (loads vtable ptr, `mtctr/bctrl`), so no direct `bl` caller exists.
- **Save-slot descriptor** referenced at 0x4c538-0x4c718 via `lis r4,0x24;
  addic r4,r4,-0x2a14/-0x2a24/-0x2a2c/-0x2a3c` -> inline strings
  GAMEDATA/OPTION/ICON0.PNG/PIC1.PNG in the `NPJB00558-GAMEDATA-` save folder.

### 13.1 Save schema vocabulary (confirmed keys)

Per-actor 名鑑 record keys (all cp932 strings in the .rodata key list):
- `f%03d_nml`            — per-character name (indexed record, ca%03d family)
- `ca%03d` / `ca%03d_2`  — character asset id
- `cha` / `chara` / `character` — character map
- `rank`, `prank`, `rankup`, `rankon` — **trust/rank fields (per actor)**
- `scenario`, `obiscenario`, `sakuhin%03d` — scenario-completion map
- `obi*` (`obichara`,`obicast`,`obiunlock`,`obiappre`…) — progress/seen flags
- `unlock`, `skil`, `cas_top` — progression

### 13.2 Trust model (final)

- **Trust-reward table @0x2e1f14 (15 ptrs):** 信頼度①..信頼度⑩
  ("trust level 1..10"), each granting an オーブ (Orb) reward, + blood types
  A型/B型/O型/AB型/??型. So **trust is an integer 1..10 per actor.**
- Trust is **derived**: count of cleared `sakuhin` (scenario) records that
  reference the actor's `ca%03d`, clamped to the 1..10 ladder. Stored back as
  the per-actor `rank`/`prank` map value by the serializer.

### 13.3 What this means for the trust meter

The 名鑑 trust meter reads the per-actor `rank`/`prank` integer from the keyed
`character`/`f%03d_*` map — NOT a raw byte at a fixed offset. To raise one
actor's trust you must (a) set that actor's cleared-scenario sub-list, and
(b) let the game recompute `rank`. Blind byte edits at 0x1117/0x117b (my earlier
failed attempt) hit unrelated big-endian stats and cannot move trust.

**Remaining single unknown:** which `ca%03d` each `sakuhin%03d` scenario credits.
That cast list lives in the scenario PACs (`/DATA/sakuhin/sakuhin%03d.pac`) or is
observable from one controlled single-clear diff. With it, per-actor trust can be
set deterministically by writing the correct keyed map — no guessing.

## 14. Scenario ↔ Character ↔ VA triangle — FULLY DECODED (GameData.cpk)

All three sides extracted statically from `GameData.cpk` / `SoundData.cpk`
(loader: `cricodecs.cpk` via `cvpatch.C.ORIG`).

### 14.1 Scenario → character (48 sakuhin PACs)

Each `DATA/sakuhin/sakuhinNNN.pac` (48 files, NNN=001..054 with gaps) embeds its
cast twice (`OBNT` object block + per-object `caNNNn` entries) as `ca%03d`
character ids. Complete map extracted by `tools/work/sakuhin_cast.py`
(output `tools/work/_sakuhin_cast.txt`). Examples:

| sakuhin | cast |
|---|---|
| 001 | ca000–ca008 (9) |
| 002 | ca009–ca017, ca221 (10) |
| 003 | ca018–ca023, ca217, ca218, ca222 (9) |
| 039/041–045/051/054 | single ca199/ca202/ca203/ca204/ca205/ca206/ca212/ca215 |

Character-id space: **ca000..ca223** (224; recurring `ca217/218/221/222/223`
appear in many scenes = narrator/system cast).

### 14.2 VA roster (seiyubase.pac) — 50 records, authoritative index

Header index: 50 entries `{u32 size, u32 offset}` at 32-byte stride. Per record:
`u16 id`, sorted **u16 ca%03d character list**, name, kana, agency, bio.
Binding verified **50/50: `id == 265 + idx`** (`tools/work/roster_final.py`
→ `tools/work/_roster3.txt`). Same ids as `vaIcon/ctva%03d.pix` and voice dirs
`vic%03d` — one consistent VA id space **265..314**.

- **八尾伊月 = idx 49 = vic314 / ctva314**, 38 characters
  (ca011, ca016, ca018–022, ca038–043, ca060–066, ca096/097, ca160/162/163,
  ca170–172, ca190/192–195, ca201–204, ca212, ca215, ca217, ca218).
- idx 46 = 月宮 桃香 (only ca130; skipped by name-heuristic earlier — found only
  via the header index, which is why the count reconciled 49 → 50).
- DLC VAs = ids **276, 287, 295, 297, 305** (gaps in base voice dirs; exactly
  the `DLC_S276/S287/S295/S297/S305` manifest entries).

Cross-check with ground truth: her bio (*"デビューしたての新人声優…まだメインは
少ない"*) matches trust 4 / 台本 20% (fewest mains among the roster).

### 14.3 VA → scenario (SoundData.cpk voice paths, authoritative)

Path grammar `DATA/sound/Plip/vicNNN/DMMM_LLL_NNN.plip` =
`vic<VA>/D<scenario>_<line>_<VA>`. Matrix built by `tools/work/voice_cov.py`
(`tools/work/_voice_cov.txt`): **45 base VAs × 123 scenarios (D000..D128,
6 ids unused: 98/118/120/121/122/125)**, path-embedded id == dir id (0
mismatches). Per-scenario VA counts also emitted (D099/D124 = 42–44 VAs =
all-cast events).

八尾伊月/vic314 speaks in **34 scenarios**: 007 009 011 012–017 030–035
042–046 068–070 099 100 103 109 110 113–116 124 127.

### 14.4 Trust storage — negative result (matters)

Scan of the live save for any flat 50-element array (byte/u16 LE/BE, values
0..10 with `[49]==4`, and 0..100 with `[49]==20`) found **nothing**
(`tools/work/trust_scan.py`). Combined with §13 (Dinkumware `std::map`
serializer): **trust is not a raw offset array** — it is either a keyed/serialized
record or *derived at load* from completion state. So a "set byte X = 10" edit
cannot work for trust (consistent with the failed 0x1117/0x117b attempt).

### 14.5 What is still open, and the cheapest way to close it

Open: which save bytes represent (a) per-scenario cleared flags and (b) any
per-VA counters (信頼度 might be *earned by casting that VA*, not by scenario
clear — the trust→Orb reward table §13.2 hints at play-session progression).
The 48×50 cast matrix now makes any diff **computable**: given a known
cleared-set, expected trust per VA = f(her cleared scenes).

Cheapest decisive experiment (either):
1. **Cast 八尾伊月 once**, snapshot before/after → the byte(s) that move for
   *her specifically* = trust counter (her id = 314 / idx 49, so attribution
   is unambiguous); or
2. Send **2–3 more 名鑑 entries with trust values** (e.g. idx 0 内山紗彩,
   idx 5 道場崇) → correlate values against the cast matrix to identify the
   array by ordering.

Artifacts: `_sakuhin_cast.txt`, `_roster3.txt`, `_voice_cov.txt`,
`sakuhin_cast.json` (all under `tools/work/`, git-ignored scratch).





