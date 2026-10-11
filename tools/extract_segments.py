#!/usr/bin/env python3
"""
Extract every TRANSLATABLE dialogue segment from the archive into
work/segments.json, plus a dedup/cost report.

Filters (all evidence-driven):
  * `<~TAG>` markers are not text
  * pure-ASCII spans are internal ids (srtbg000, haikeisita, FSRT, ...)
  * `.info` CRLF segments that are binary junk (the u32 table region) are dropped
"""
import hashlib
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

ORIG = C.ORIG
TAG_ONLY = re.compile(r"^<~[0-9A-Za-z_]+>$")
JP = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff\uff01-\uff60\u3005-\u3006]")
MAXLEN = 400


def keep_text(t: str) -> bool:
    if TAG_ONLY.match(t):
        return False
    if len(t) < 2:
        return False
    if len(t) > MAXLEN:
        return False
    if not JP.search(t):
        return False          # pure ASCII -> internal id, not on-screen text
    if "\x00" in t:
        return False
    return True


def main():
    a = cpk.load(str(ORIG))
    files = {}
    n_seg = 0
    n_drop = 0
    per_kind = {}
    for f in a.files:
        lp = f.full_path.lower()
        kind = "srt" if lp.endswith(".srt") else ("info" if lp.endswith(".info") else None)
        if kind is None:
            continue
        d = a.file_bytes(f.toc_index)
        if kind == "srt":
            if d[:4] != b"FSRT":
                continue
            spans = C.parse_dialogue(d)
        else:
            spans = C.parse_info_segments(d)
        if not spans:
            continue
        recs = []
        for i, (s, e) in enumerate(spans):
            raw = d[s:e]
            try:
                txt = raw.decode("utf-8")
            except UnicodeDecodeError:
                txt = raw.decode("utf-8", "surrogateescape")
            if not keep_text(txt):
                n_drop += 1
                continue
            recs.append({"i": i, "s": s, "e": e, "b": e - s, "jp": txt,
                         "h": hashlib.sha1(raw).hexdigest()[:12]})
            n_seg += 1
        if not recs:
            continue
        per_kind[kind] = per_kind.get(kind, 0) + len(recs)
        files[f.full_path] = {"toc": f.toc_index, "kind": kind, "seg": recs}

    by_text = {}
    for rec in files.values():
        for seg in rec["seg"]:
            by_text.setdefault(seg["jp"], 0)
            by_text[seg["jp"]] += 1
    lens = [len(t) for t in by_text]
    uniq_bytes = sum(len(t.encode("utf-8", "surrogateescape")) for t in by_text)

    rep = [
        f"files with text         : {len(files)}",
        f"  .srt / .info segments : {per_kind.get('srt',0)} / {per_kind.get('info',0)}",
        f"segments kept           : {n_seg}   (dropped {n_drop} as ids/binary/short)",
        f"unique Japanese strings : {len(by_text)}",
        f"  duplicates collapsed  : {n_seg - len(by_text)} ({100*(n_seg-len(by_text))/n_seg:.1f}%)",
        f"unique text             : {uniq_bytes} bytes ({uniq_bytes/1048576:.2f} MiB)",
        f"avg unique string       : {sum(lens)/max(1,len(lens)):.1f} chars",
        f"longest                 : {max(lens)} chars",
        "",
        "byte-budget headroom (unique strings by size bucket):",
    ]
    buckets = [(10, 20), (20, 40), (40, 60), (60, 100), (100, 200), (200, 999)]
    for lo, hi in buckets:
        sel = [t for t in by_text if lo <= len(t.encode("utf-8", "surrogateescape")) < hi]
        if sel:
            rep.append(f"  {lo:3d}-{hi:3d} B : {len(sel):6d} strings")
    rep.append("")
    rep.append("most-duplicated dialogue:")
    n = 0
    for t, c in sorted(by_text.items(), key=lambda kv: -kv[1]):
        if not TAG_ONLY.match(t):
            rep.append(f"  x{c:<5} {t[:58]}")
            n += 1
        if n >= 12:
            break

    (C.WORK / "segments.json").write_bytes(
        json.dumps(files, ensure_ascii=False).encode("utf-8", "surrogatepass"))
    (C.WORK / "extract.txt").write_bytes(
        "\n".join(rep).encode("utf-8", "surrogatepass"))
    print("\n".join(rep))


if __name__ == "__main__":
    main()
