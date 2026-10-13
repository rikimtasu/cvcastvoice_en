#!/usr/bin/env python3
"""Extract DLC segments into work/dlc_segments.json + dlc batches.

Kinds: srt / info (same as base game) + vinfo (NUL-separated S-pack
profile fields; embedded \\n line breaks are PRESERVED, not spaced).
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

DLC = C.ROOT / "dlc" / "dec"
TAG_ONLY = re.compile(r"^<~[0-9A-Za-z_]+>$")
JP = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff\uff01-\uff60\u3005-\u3006]")
MAXLEN = 400
BATCH = 120


def keep_text(t: str) -> bool:
    if TAG_ONLY.match(t):
        return False
    if len(t) < 2 or len(t) > MAXLEN:
        return False
    if not JP.search(t):
        return False
    if "\x00" in t:
        return False
    return True


def vinfo_spans(d: bytes):
    """NUL-separated fields that decode as Japanese text."""
    spans = []
    start = 0
    while True:
        i = d.find(b"\x00", start)
        if i < 0:
            chunk = d[start:]
            off = start
        else:
            chunk = d[start:i]
            off = start
        if chunk:
            try:
                t = chunk.decode("utf-8")
            except UnicodeDecodeError:
                t = None
            if t is not None and keep_text(t):
                spans.append((off, off + len(chunk)))
        if i < 0:
            break
        start = i + 1
    return spans


def main():
    order = json.loads((C.WORK / "order.json")
                       .read_bytes().decode("utf-8-sig", "surrogatepass"))
    known = {v["jp"] for v in order.values()}
    files = {}
    n_seg = n_new = 0
    freq = Counter()
    for cpk_path in sorted(DLC.glob("DLC_*.cpk")):
        a = cpk.load(str(cpk_path))
        for f in a.files:
            lp = f.full_path.lower()
            if lp.endswith(".srt"):
                kind = "srt"
            elif "vc" in lp and lp.endswith(".info"):
                kind = "vinfo"
            elif lp.endswith(".info"):
                kind = "info"
            else:
                continue
            try:
                d = a.file_bytes(f.toc_index)
            except Exception:
                continue
            if kind == "srt":
                if d[:4] != b"FSRT":
                    continue
                spans = C.parse_dialogue(d)
            elif kind == "vinfo":
                spans = vinfo_spans(d)
            else:
                spans = C.parse_info_segments(d)
            recs = []
            for idx, (s, e) in enumerate(spans):
                raw = d[s:e]
                try:
                    txt = raw.decode("utf-8")
                except UnicodeDecodeError:
                    continue
                if not keep_text(txt):
                    continue
                n_seg += 1
                is_new = txt not in known
                if is_new:
                    n_new += 1
                    freq[txt] += 1
                recs.append({"i": idx, "s": s, "e": e, "b": e - s,
                             "jp": txt, "new": is_new})
            if recs:
                files[f"{cpk_path.name}::{f.full_path}"] = {
                    "cpk": cpk_path.name, "path": f.full_path,
                    "toc": f.toc_index, "kind": kind, "seg": recs}
    (C.WORK / "dlc_segments.json").write_bytes(
        json.dumps(files, ensure_ascii=False).encode("utf-8", "surrogatepass"))

    # batch ONLY the new strings, frequency-ordered
    items = sorted(freq, key=lambda t: (-freq[t], -len(t)))
    bdir = C.WORK / "dlc_batches"
    bdir.mkdir(exist_ok=True)
    for old in bdir.glob("dlc_batch_*.json"):
        old.unlink()
    nb = 0
    for bi in range(0, len(items), BATCH):
        chunk = items[bi:bi + BATCH]
        pack = {}
        for j, t in enumerate(chunk):
            i = bi + j
            # largest budget among occurrences
            bmax = 0
            for rec in files.values():
                for s in rec["seg"]:
                    if s["jp"] == t:
                        bmax = max(bmax, s["b"])
            pack[f"D{i}"] = {"jp": t, "b": bmax, "c": freq[t]}
        (bdir / f"dlc_batch_{nb:04d}.json").write_bytes(
            json.dumps(pack, ensure_ascii=False).encode("utf-8"))
        nb += 1
    rep = [f"dlc files with text : {len(files)}",
           f"dlc segments       : {n_seg}",
           f"new unique strings: {len(items)} in {nb} batches",
           f"already translated: {n_seg - sum(freq.values())} segments "
           f"(covered by base patch)"]
    (C.WORK / "dlc_segments.txt").write_bytes(
        "\n".join(rep).encode("utf-8"))
    print("\n".join(rep))


if __name__ == "__main__":
    main()
