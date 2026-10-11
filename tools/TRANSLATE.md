# Batch translator instructions (CV Casting Voice PS3 → English patch)

You translate ONE batch file. Read everything below before starting.

## Inputs (all under D:\Documents\CVCastingVoice\tools\work\)
- `batches/batch_NNNN.json` — `{id: {"jp": japanese, "b": byte_budget, "c": occurrences}}`
- `glossary.json` — READ IT FIRST. `characters` gives the locked English name
  for every person; `terms` the locked renderings; `labels` must NOT be
  romanized (use the given English); `do_not_translate` is absolute.

## Output
- `tr_bNNNN.json` — `{id: "english"}` for every id you could fit. Return to
  the caller ONLY a short summary: translated count, skipped list, doubts.

## Hard rules (violations break the build or the game)
1. **Byte budget**: `len(english.encode("utf-8")) <= b`. Shorten, never exceed.
   English averages ~1 byte/char; the budget column already accounts for this.
2. **ASCII only**: no macrons, no curly quotes, no fullwidth. `...` and `!!`
   are fine. Keep `(...)` parenthesised asides as `(...)`.
3. **Never emit `@n`** (it's the engine's line break) or raw newlines.
   One segment = one screen line = single-line string.
4. **Keep `@i<0>` tags inline exactly** (player-name variable).
5. Convert `\u3000` (ideographic space) to a regular space. Leading spaces
   are significant (continued narration) — preserve them.
6. Trust messages use the template **`Trust with <Name> has risen!!`**
   with the glossary name, family-first.
7. Names are **family-first** (Kagamihara Masaaki), matching in-game order.
8. Register: this is a voice-acting workplace dramedy. Protagonist = a rookie
   producer (referred to as Producer). 演技=c/w performance, 指導=direction,
   収録=recording, 台本=script, 信頼度=Trust. Lines ending 、/…… trail off;
   keep `...`. Exclamations stay exclamatory.
9. Short kana interjections: はい→Yes, えっ→Huh, くっ→Ugh, あれ→Huh,
   よし→Yes/All right (context), 了解→Roger, すみません→Sorry/Excuse me.
10. If a string is untranslatable garbage or already English, copy it through
    unchanged (counts as translated, note it).
11. Standalone name plates that don't fit the full name: use the FAMILY name
    only (Uchiyama, Sato, Taki, Narimiya). Never use initials (no "Sakura M.",
    no "T. Reika"). Bare given names in dialogue stay as-is (Akira, Hana).
12. Industry slang stays: Pさん (P = producer) -> "Mr. P"; moe, fujoshi kept
    as loanwords; gag readings like 腐(ふ) -> "Fu (fu)".
13. Drop honorifics: さん/くん/ちゃん/様 -> bare names ("Kagamihara",
    never "Kagamihara-san"). -chan/-san forms never appear in English.
14. Gag readings from game furigana: 日日日 reads あきら -> render "Akira"
    (never "Hihihi"); 腐(ふ) -> "Fu (fu)".

## Budget failures
If even a tight translation can't fit `b`, SKIP the id and list it in your
summary as `id b=NN min_len=MM`. Do not pad, do not truncate mid-word.
