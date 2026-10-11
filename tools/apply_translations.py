#!/usr/bin/env python3
"""
Merge translations into an overlay and (optionally) build the patched archive.

  work/translated.json : {id: "english text"}     <- the translator's output
  work/order.json      : {id: {jp, b, c}}          <- from make_batches.py
  work/segments.json   : {path: {kind, seg:[...]}}

Writes work/overlay.json in the format cvpatch.py build expects, then can call
build directly. Byte budgets are enforced: a translation that does not fit is
reported and skipped rather than failing the whole build.

Usage:
  apply_translations.py                # report only (coverage + budget check)
  apply_translations.py --out FILE     # build the archive
"""
import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C


def clean(en: str) -> str:
    """Normalise a translation for the game's text engine.

    Leading/trailing spaces are preserved deliberately: several source lines
    begin with U+3000 (an indent for continued narration) and `@i<0>` is a
    variable tag the engine substitutes.
    """
    if en is None:
        return None
    en = en.replace("\u3000", " ")            # ideographic space -> ASCII
    en = en.replace("@n", " ")                 # would be eaten as a line break
    en = en.replace("\n", " ").replace("\r", " ")
    return en


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    ap.add_argument("--translated", default=str(C.WORK / "translated.json"))
    ap.add_argument("--dir", default=None,
                    help="merge every work/tr_*.json in this directory instead "
                         "of a single --translated file")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--deep", action="store_true",
                    help="also prove relocated files differ only inside text "
                         "spans (~10 s) instead of the fast structural check")
    a = ap.parse_args()

    order = json.loads((C.WORK / "order.json")
                       .read_bytes().decode("utf-8-sig", "surrogatepass"))
    if a.dir:
        tr = {}
        for p in sorted(Path(a.dir).glob("tr_*.json")):
            tr.update(json.loads(p.read_bytes()
                                 .decode("utf-8-sig", "surrogatepass")))
    else:
        tr = json.loads(Path(a.translated)
                        .read_bytes().decode("utf-8-sig", "surrogatepass"))
    seg = json.loads((C.WORK / "segments.json")
                     .read_bytes().decode("utf-8-sig", "surrogatepass"))
    en_by_jp = {}
    bad = []
    for k, v in tr.items():
        if k not in order:
            continue
        rec = order[k]
        e = clean(v)
        if not e:
            continue
        if len(e.encode("utf-8")) > rec["b"]:
            bad.append((rec["b"], len(e.encode("utf-8")), rec["jp"], e))
        en_by_jp[rec["jp"]] = e

    overlay = {}
    n_hit = n_miss = 0
    for path, rec in seg.items():
        runs = []
        for s in rec["seg"]:
            e = en_by_jp.get(s["jp"])
            if e is None:
                n_miss += 1
                continue
            if len(e.encode("utf-8")) > s["b"]:
                continue
            n_hit += 1
            runs.append({"span": [s["s"], s["e"]], "text": e})
        if runs:
            overlay[path] = {"kind": rec["kind"], "runs": runs}

    msg = [f"translations loaded : {len(en_by_jp)} unique strings",
           f"segments covered    : {n_hit}",
           f"segments still JP   : {n_miss} "
           f"({100*n_miss/max(1,n_hit+n_miss):.1f}% of on-screen text)",
           f"files touched       : {len(overlay)}",
           f"over budget         : {len(bad)} (skipped, originals kept)"]
    if bad:
        msg.append("  first few over-budget:")
        for b, n, jp, e in bad[:12]:
            msg.append(f"    {n}>{b}B  {jp[:26]!r} -> {e[:34]!r}")
    (C.WORK / "merge.txt").write_text("\n".join(msg), encoding="utf-8")

    out_path = a.out
    if out_path:
        ov = C.WORK / "overlay.json"
        ov.write_bytes(json.dumps({"files": overlay}, ensure_ascii=False)
                       .encode("utf-8", "surrogatepass"))
        (C.WORK / "merge.txt").write_text(
            "\n".join(msg) + f"\noverlay -> {ov}\ntarget  -> {out_path}",
            encoding="utf-8")
        import subprocess
        r = subprocess.run([sys.executable, str(Path(__file__).with_name("cvpatch.py")),
                            "build", "--overlay", str(ov), "--out", out_path],
                           capture_output=True, text=True, encoding="utf-8")
        print(r.stdout)
        print(r.stderr)
        if r.returncode:
            sys.exit(r.returncode)
        v = subprocess.run([sys.executable, str(Path(__file__).with_name("cvpatch.py")),
                            "verify", "--file", out_path]
                           + (["--deep"] if a.deep else []),
                           capture_output=True, text=True, encoding="utf-8")
        print(v.stdout)
        if v.returncode:
            sys.exit(v.returncode)
    else:
        print("\n".join(msg))
    return 0


if __name__ == "__main__":
    sys.exit(main())
