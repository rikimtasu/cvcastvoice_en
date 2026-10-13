#!/usr/bin/env python3
"""Extract .pac text segments (seiyubase + daihonbase) into pac batches.

Same 1:1 byte-length rule: spans are exact, internal PACK offsets untouched.
\\n preserved (vinfo-style).
"""
import json
import re
import struct
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

JP = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff\uff01-\uff60\u3005-\u3006]")
BATCH = 120


def pac_spans(d: bytes):
    spans = []
    start = 0
    while True:
        i = d.find(b"\x00", start)
        chunk = d[start:i] if i >= 0 else d[start:]
        if chunk:
            try:
                t = chunk.decode("utf-8")
            except UnicodeDecodeError:
                t = None
            if t is not None and len(t) >= 2 and JP.search(t):
                spans.append((start, start + len(chunk), t))
        if i < 0:
            break
        start = i + 1
    return spans


def main():
    order = json.loads((C.WORK / "order.json")
                       .read_bytes().decode("utf-8-sig", "surrogatepass"))
    known = {v["jp"] for v in order.values()}
    # plus DLC batches
    for p in sorted((C.WORK / "dlc_batches").glob("dlc_batch_*.json")):
        for v in json.loads(p.read_bytes()
                            .decode("utf-8-sig", "surrogatepass")).values():
            known.add(v["jp"])
    a = cpk.load(str(C.ORIG))
    by = {f.full_path: f for f in a.files}
    files = {}
    freq = Counter()
    n_seg = 0
    for path in ("DATA/daihon/seiyubase.pac", "DATA/daihon/daihonbase.pac"):
        f = by[path]
        d = a.file_bytes(f.toc_index)
        recs = []
        for s, e, t in pac_spans(d):
            n_seg += 1
            is_new = t not in known
            if is_new:
                freq[t] += 1
            recs.append({"s": s, "e": e, "b": e - s, "jp": t,
                         "new": is_new})
        files[path] = {"toc": f.toc_index, "kind": "pac", "seg": recs}
    (C.WORK / "pac_segments.json").write_bytes(
        json.dumps(files, ensure_ascii=False).encode("utf-8", "surrogatepass"))
    items = sorted(freq, key=lambda t: (-freq[t], -len(t)))
    bdir = C.WORK / "pac_batches"
    bdir.mkdir(exist_ok=True)
    for old in bdir.glob("pac_batch_*.json"):
        old.unlink()
    nb = 0
    for bi in range(0, len(items), BATCH):
        pack = {}
        for j, t in enumerate(items[bi:bi + BATCH]):
            i = bi + j
            bmax = 0
            for rec in files.values():
                for s in rec["seg"]:
                    if s["jp"] == t:
                        bmax = max(bmax, s["b"])
            pack[f"P{i}"] = {"jp": t, "b": bmax, "c": freq[t]}
        (bdir / f"pac_batch_{nb:04d}.json").write_bytes(
            json.dumps(pack, ensure_ascii=False).encode("utf-8"))
        nb += 1
    print(f"pac segments: {n_seg}  new unique: {len(items)} in {nb} batches")


if __name__ == "__main__":
    main()
