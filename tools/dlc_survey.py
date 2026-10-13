#!/usr/bin/env python3
"""Survey decrypted DLC CPKs: file inventory + translatable segments.

Reports per-DLC counts and, crucially, how many unique strings are NOT
already in the base-game order (i.e. genuinely new translation work).
"""
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

DEC = C.ROOT / "dlc" / "dec"
TAG_ONLY = re.compile(r"^<~[0-9A-Za-z_]+>$")
JP = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff\uff01-\uff60\u3005-\u3006]")
MAXLEN = 400


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


def main():
    order = json.loads((C.WORK / "order.json")
                       .read_bytes().decode("utf-8-sig", "surrogatepass"))
    known = {v["jp"] for v in order.values()}
    rep = []
    tot_seg = tot_new = 0
    new_by_dlc = {}
    for cpk_path in sorted(DEC.glob("DLC_*.cpk")):
        a = cpk.load(str(cpk_path))
        fa = a.files
        ext = Counter()
        n_seg = 0
        new = Counter()
        for f in fa:
            lp = f.full_path.lower()
            name = f.full_path.rsplit("/", 1)[-1]
            dot = name.rfind(".")
            ext[name[dot:] if dot > 0 else "(none)"] += 1
            kind = "srt" if lp.endswith(".srt") else (
                "info" if lp.endswith(".info") else None)
            if kind is None:
                continue
            try:
                d = a.file_bytes(f.toc_index)
            except Exception:
                continue
            if kind == "srt":
                if d[:4] != b"FSRT":
                    continue
                spans = C.parse_dialogue(d)
            else:
                spans = C.parse_info_segments(d)
            for s, e in spans:
                raw = d[s:e]
                try:
                    txt = raw.decode("utf-8")
                except UnicodeDecodeError:
                    txt = raw.decode("utf-8", "surrogateescape")
                if not keep_text(txt):
                    continue
                n_seg += 1
                if txt not in known:
                    new[txt] += 1
        tot_seg += n_seg
        tot_new += len(new)
        new_by_dlc[cpk_path.name] = new
        rep.append(f"== {cpk_path.name} ({len(fa)} files) ==")
        rep.append("  ext: " + ", ".join(
            f"{e}x{c}" for e, c in ext.most_common(12)))
        rep.append(f"  segments kept: {n_seg}   new unique strings: {len(new)}")
        for t, c in new.most_common(8):
            rep.append(f"    x{c:<4} {t[:60]!r}")
    rep.append("")
    rep.append(f"TOTAL dlc segments: {tot_seg}   new unique strings: {tot_new}")
    (C.WORK / "dlc_survey.txt").write_bytes(
        "\n".join(rep).encode("utf-8", "surrogatepass"))
    # save new strings for batching later
    all_new = {}
    for v in new_by_dlc.values():
        all_new.update(v)
    (C.WORK / "dlc_new.json").write_bytes(
        json.dumps(all_new, ensure_ascii=False).encode("utf-8", "surrogatepass"))
    print("\n".join(rep))


if __name__ == "__main__":
    main()
