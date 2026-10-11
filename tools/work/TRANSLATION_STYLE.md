# Translation Style Guide — CV: Casting Voice (JP→EN)

Single source of truth for translating `batches/batch_NNNN.json` → `tr/bNNNN.txt`.
The tooling enforces the **hard rules** (byte budget, ASCII, id coverage). This guide
covers **quality** (tone, names, conventions) so every batch reads like one hand.

## The pipeline (per batch)

```
# 1. Dump the source (id | byte-budget | japanese)
& 'C:\Users\User\AppData\Local\WhisperJAV\python.exe' dump_batch.py NNNN

# 2. Write tools/work/tr/bNNNN.txt  (one line per id: <id>|<english>)

# 3. Validate + write tr_bNNNN.json (fails loudly if any rule is broken)
& 'C:\Users\User\AppData\Local\WhisperJAV\python.exe' mktr.py NNNN write

# 4. Deep audit (keys, budget, ASCII, tags, leading-space, brackets)
& 'C:\Users\User\AppData\Local\WhisperJAV\python.exe' audit_tr.py NNNN
```

Set `$env:PYTHONIOENCODING='utf-8'` in the shell first. Work from `tools/work/`.
`mktr.py NNNN write` is the gate — it must print `WROTE ... OK`. Do not move on
until it does; if it prints OVER BUDGET / MISSING / EXTRA / NON-ASCII, fix and re-run.

## HARD RULES (enforced by tooling — violations fail the build)

1. **ASCII-only.** No CJK, no curly quotes `‘’“”`, no `…`, no `—`, no macrons `Ō ū`.
   Use straight `'` and `"`, three ASCII dots `...`, and `--` for a dash.
2. **Byte budget.** Each `english` must be `len(en.encode('utf-8')) <= budget`.
   Because output is pure ASCII, **budget ≈ max character count**. `@i<0>` is 5 bytes.
   Count carefully — budgets are often tight (see table below).
3. **Exact id coverage.** One line per id in the batch; no missing, no extra, no dupes.
4. **`@i<0>` stays inline**, spelled exactly. It is the player-name variable
   (the Producer / protagonist). Never translate or remove it.
5. **Leading-space rule.** If the Japanese source line starts with U+3000 (　),
   the English MUST start with a normal ASCII space ` `. If it does not, do NOT
   add one. (This preserves the game's indentation/continuation layout.)
6. **Trailing U+3000 (　) is a page-continuation marker** — the parser already
   handled page breaks. Do NOT add a trailing space to the English.

## Quotes, brackets, ellipsis

- `「」` → `"` (straight double quotes). Match open/close where the source does.
- `（）` (full-width parens) → `(...)`.
- `……` → `...`
- Interjections: keep the game's energy (`フハハハ！` → `Fwahaha!`; `うわーっ` → `Waaah!`).

## Names (Hepburn, family-first — from glossary.md)

Use these spellings exactly (ASCII, no macron):
- 紗彩 / 内山紗彩 → **Saaya** (Uchiyama Saaya; called "Saaya")
- 巴菜 / 鴫野巴菜 → **Hana** (Shigino Hana)
- 玲子 / 鷺洲玲子 → **Reiko** (Sagisu Reiko)
- 神崎史之 → **Kanzaki** (Fumiyuki)
- 菅原 → **Sugawara**  ·  道場 → **Dojo**  ·  平沢 → **Hirasawa**  ·  久保園 → **Kubozono**
- 好一 → **Koichi**  ·  プロデューサー / @i<0> → **Producer** (or keep `@i<0>` inline)
- 師匠 → **Master** (addressed as "Sensei" in furigana)

Key terms: 信頼度→Trust · 台本→script · 演技→acting · 収録→recording ·
授賞式→awards ceremony · 声優→voice actor · 演技指導→direction.

## Tone & brevity

- Spoken, natural, in-character English. This is a voice-acting studio drama.
- **Be terse.** Japanese is compact; English inflates. Prefer short words.
- Tight budgets (how many characters you have, roughly):
  | budget | meaning | e.g. |
  |---|---|---|
  | 6B  | ~6 chars  | `よし`→`Okay.` / `Got it` |
  | 9B  | ~9 chars  | short reactions |
  | 12–18B | ~1 short clause | `Yes.` / `No way...` |
  | 21–36B | a full spoken line | normal dialogue |
  | 39B+ | longer lines / narration |
- When over budget, cut filler ("you know", "well", honorifics, redundant words)
  BEFORE cutting meaning. Never leave a placeholder.

## Do NOT translate

`@i<0>`, `@n`, page terminators (U+22A5/U+22BF), `<~NNNNNN>` voice tags, and
scenario commands. These do not appear as content in the dumped lines except `@i<0>`.
