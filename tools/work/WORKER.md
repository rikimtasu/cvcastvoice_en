# Batch translator worker spec (CV Casting Voice PS3 -> English patch)

You translate JP -> EN scenario strings for the *CV: Casting Voice* PS3 English
patch. Another model set up this exact pipeline; follow it precisely.

## Absolute paths (Windows)

- Work dir: `D:\Documents\CVCastingVoice\tools\work`
- Python:  `C:\Users\User\AppData\Local\WhisperJAV\python.exe`
- Always run python with `$env:PYTHONIOENCODING='utf-8'` first.

## The three tools you use (already written, do not modify)

1. `dump_batch.py NNNN [lo] [hi]` - print `id|budget|jp` lines for a batch.
   Use it to read the Japanese. You can restrict with lo/hi to read in chunks.
2. `mktr.py NNNN` - **check** your text file against the batch.
3. `mktr.py NNNN write` - write `tr_bNNNN.json` (only run when check is clean).

## Where your translations go

`D:\Documents\CVCastingVoice\tools\work\tr\bNNNN.txt`

One entry per line:

```
<id>|<english>
```

- No spaces around the `|`.
- Blank lines and `#` comment lines are ignored.
- If the English itself must contain a literal `|`, write `\u007c`.
- One segment = one line. NEVER emit `@n` or a raw newline.

## Workflow for each batch NNNN

```powershell
$env:PYTHONIOENCODING='utf-8'
$py='C:\Users\User\AppData\Local\WhisperJAV\python.exe'
& $py 'D:\Documents\CVCastingVoice\tools\work\dump_batch.py' NNNN
# write tr\bNNNN.txt with ALL ids from the batch
& $py 'D:\Documents\CVCastingVoice\tools\work\mktr.py' NNNN          # must be clean
& $py 'D:\Documents\CVCastingVoice\tools\work\mktr.py' NNNN write    # only if clean
& $py 'D:\Documents\CVCastingVoice\tools\work\validate_tr.py' NNNN NNNN
```

If `mktr.py NNNN` reports OVER BUDGET, shorten those strings and re-check.
Do not run `write` until the check passes.

## Hard rules (breaking these breaks the game build)

1. **Byte budget**: `len(english.encode("utf-8")) <= b`. `b` is per-string and
   printed by `dump_batch.py`. English is ~1 byte/char, so treat `b` as a
   character limit. Shorten, never exceed.
2. **ASCII only**: no macrons (no O with macron), no curly quotes, no
   fullwidth punctuation. `...` and `!!` are fine.
3. **Keep `@i<0>` inline exactly** (player-name variable). Do not translate it.
4. Convert `\u3000` (ideographic space) to one regular space. **Leading spaces
   are significant** (continued narration) - preserve them.
5. **Names are family-first**: `Kagamihara Masaaki`, not `Masaaki Kagamihara`.
   Drop honorifics entirely (never `-san` / `-kun` / `-chan` / `-sama`).
   Use `-kun`-addressed characters as bare names in English.
6. Trust messages: `Trust with <Name> has risen!!` with the glossary name.
7. `「」` -> `"` ; `（）` -> `( )` (keep the parenthesised aside as `(...)`).
   `……` -> `...`. Lines ending `、` or `……` trail off -> keep `...`.
8. Register: voice-acting workplace dramedy. The player character is a rookie
   **Producer** (`プロデューサー` -> `Producer`). Keep industry terms:
   演技 = acting/performance, 指導 = direction/coaching, 収録 = recording,
   台本 = script, 信頼度 = Trust, 授賞式 = awards ceremony,
   ボイスグランプリ = Voice Grand Prix.
9. Short interjections: はい -> Yes, えっ -> Huh, くっ -> Ugh, あれ -> Huh,
   よし -> All right / Yes, 了解 -> Roger, すみません -> Sorry.
10. Untranslatable garbage or already-English -> copy through unchanged.

## Glossary (authoritative)

Read `D:\Documents\CVCastingVoice\tools\work\glossary.json` - use the locked
`en` for every character and term. `glossary.md` is the same data in prose.

Agencies seen so far: 翔クリエイティブ = Sho Creative, オフィスすがわら =
Office Sugawara, 相葉プロダクション = Aiba Production, ホットビジョン =
Hot Vision.

## Reporting

Report back: number of batches completed, batch numbers, any ids you had to
skip (with `id b=NN min_len=MM`), and any translation doubts. Keep it short.
