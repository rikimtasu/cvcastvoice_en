#!/usr/bin/env python3
"""Survey the archive for where proper nouns / names / system terms live.

Single pass: each file is decompressed at most ONCE. Expensive UTF-8
decode + regex runs only on files that contain a trust-marker byte string
(section 3) or are .srt/.info (section 4). Progress goes to stderr so a
stalled run is visible.
"""
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

KNOWN = ["西宮寺美礼", "牙龍院鏡夜", "各務原昌秋", "波野あきら", "プロデューサー"]
TRUST_WORDS = ["との信頼度", "信頼度が上昇", "との信頼度が上昇した",
               "の好感度", "信頼度が増加"]


def main():
    t0 = time.perf_counter()
    a = cpk.load(str(C.ORIG))
    fa = a.files  # bind once: .files rebuilds the list per access
    n = len(fa)
    print(f"files: {n}", file=sys.stderr, flush=True)

    # ---- 1. inventory (TOC only, no I/O) ----------------------------------
    ext = Counter()
    dirs = Counter()
    nameish = []
    for f in fa:
        p = f.full_path
        name = p.rsplit("/", 1)[-1]
        dot = name.rfind(".")
        ext[name[dot:] if dot > 0 else "(no ext)"] += 1
        if "/" in p:
            dirs[p.split("/")[1]] += 1
        lp = p.lower()
        if any(k in lp for k in ("name", "speaker", "chara", "cast", "seiy",
                                 "actor", "person", "jinmei", "namae")):
            nameish.append(p)

    out = ["== extensions =="]
    for e, c in ext.most_common():
        out.append(f"  {c:6d}  {e}")
    out.append("")
    out.append("== top-level dirs under DATA ==")
    for d, c in dirs.most_common(40):
        out.append(f"  {c:6d}  {d}")
    out.append("")
    out.append(f"== name-ish paths ({len(nameish)}) ==")
    for p in nameish[:40]:
        out.append(f"  {p}")

    # ---- 2+3+4 single pass ------------------------------------------------
    kb = []
    for nm in KNOWN:
        kb.append((nm, nm.encode("utf-8")))
        try:
            kb.append((nm, nm.encode("utf-16-le")))
        except Exception:
            pass
    trust_b = [w.encode("utf-8") for w in TRUST_WORDS]
    pat = re.compile(r"([^\s、。@]{2,14}?)\s*[　 ]?(との信頼度|の好感度|信頼度)")
    SEG = re.compile(r"[぀-ヿ一-鿿]{2,4}")

    hits = defaultdict(list)
    mined = Counter()
    ctx = []
    grams = Counter()
    n_bytes = 0
    n_dec_trust = 0
    n_dec_seg = 0

    for idx, f in enumerate(fa):
        if idx % 500 == 0:
            print(f"  {idx}/{n}  {time.perf_counter()-t0:.1f}s",
                  file=sys.stderr, flush=True)
        try:
            d = a.file_bytes(f.toc_index)
        except Exception:
            continue
        if not d:
            continue
        n_bytes += len(d)
        p = f.full_path
        lp = p.lower()

        for nm, b in kb:
            if b in d:
                enc = "utf-16-le" if len(b) > len(nm.encode("utf-8", "ignore")) else "utf-8"
                # utf-16le encodings are ~2x the utf-8 length; good enough as a tag
                if b == nm.encode("utf-8"):
                    enc = "utf-8"
                hits[nm].append((p, enc))
                break  # one hit per name per file is enough for the survey

        if any(tb in d for tb in trust_b):
            n_dec_trust += 1
            try:
                t = d.decode("utf-8", "replace")
            except Exception:
                t = ""
            if t:
                for m in pat.finditer(t):
                    mined[m.group(1)] += 1
                    if len(ctx) < 25:
                        s = max(0, m.start() - 30)
                        ctx.append(f"    {p}  ...{t[s:m.end()+30]!r}")

        if lp.endswith(".srt") or lp.endswith(".info"):
            n_dec_seg += 1
            try:
                t2 = d.decode("utf-8", "replace")
            except Exception:
                continue
            for s in SEG.findall(t2):
                if len(s) == 2:
                    grams[s] += 1

    out.append("")
    out.append(f"== pass stats: {n_bytes} decompressed bytes, "
               f"{n_dec_trust} trust-decodes, {n_dec_seg} srt/info-decodes, "
               f"{time.perf_counter()-t0:.1f}s ==")
    out.append("")
    out.append("== known-name hits (files) ==")
    for nm in KNOWN:
        out.append(f"  {nm}: {len(hits[nm])} files")
        for p, enc in hits[nm][:8]:
            out.append(f"      [{enc}] {p}")

    out.append("")
    out.append("== mined name prefixes (before trust words) ==")
    for nm_, c in mined.most_common(40):
        out.append(f"  x{c:<5} {nm_}")
    if ctx:
        out.append("  -- contexts --")
        out.extend(ctx[:25])

    out.append("")
    out.append("== frequent 2-char kanji/kana grams in srt/info ==")
    for g, c in grams.most_common(60):
        out.append(f"  x{c:<6} {g}")

    txt = "\n".join(out)
    print(txt)
    (C.WORK / "survey_names.txt").write_bytes(txt.encode("utf-8", "replace"))


if __name__ == "__main__":
    main()
