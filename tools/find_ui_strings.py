#!/usr/bin/env python3
"""
Decisive test: are the UI strings (speaker name, CV credit, bottom buttons)
present as TEXT anywhere in the archive, or only baked into .pix pixels?

Searches every one of the 8400 files, in every container, for the target
strings in UTF-8 and Shift-JIS. Reports file, type, offset, and context.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

ORIG = C.ORIG

TARGETS = {
    "skip": "スキップ",
    "auto": "オート",
    "window": "ウィンドウ",
    "fastfwd": "早送り",
    "haruka_name": "春香",
    "nishinomiya": "西宮寺",
    "mirei": "美礼",
    "log": "ログ",
    "save": "セーブ",
    "load": "ロード",
    "config": "設定",
    "title_back": "タイトル",
}


def encodings(s: str):
    out = {"utf8": s.encode("utf-8")}
    try:
        out["sjis"] = s.encode("shift_jis")
    except Exception:
        pass
    return out


def main():
    a = cpk.load(str(ORIG))
    files = [(f.full_path, f.toc_index) for f in a.files]

    # build byte patterns
    pats = {}
    for key, s in TARGETS.items():
        for enc, b in encodings(s).items():
            pats[(key, enc)] = b

    # per-file: which targets hit, and where
    hit_summary = {}   # (key) -> set of file-types
    detailed = []      # (path, key, enc, offset, context)
    type_counts = {}

    for path, ti in files:
        try:
            data = a.file_bytes(ti)
        except Exception:
            continue
        ext = Path(path).suffix.lower()
        local_hits = set()
        for (key, enc), b in pats.items():
            start = 0
            first = True
            while True:
                i = data.find(b, start)
                if i < 0:
                    break
                if first:
                    hit_summary.setdefault(key, {}).setdefault(ext, 0)
                    hit_summary[key][ext] += 1
                    type_counts.setdefault(ext, 0)
                    local_hits.add(key)
                    if len(detailed) < 400:
                        ctx = data[max(0, i - 12):i + len(b) + 12]
                        ctxs = ctx.decode("utf-8", "replace")
                        detailed.append((path, key, enc, i, ext, ctxs))
                    first = False
                start = i + 1
                # keep scanning for count but only record first offset detail

    print("=== UI-string presence by target -> {file_ext: #files_with_hit} ===")
    for key in TARGETS:
        if key in hit_summary:
            exts = hit_summary[key]
            print(f"  {key:14s} {dict(sorted(exts.items(), key=lambda kv:-kv[1]))}")
        else:
            print(f"  {key:14s} (no text hit in any file)")

    print("\n=== detail (first occurrences) ===")
    # group by key
    seen = set()
    for path, key, enc, off, ext, ctxs in detailed:
        sig = (key, ext)
        if sig in seen and len([1 for x in seen]) > 200:
            continue
        seen.add(sig)
        print(f"  [{key}/{enc}] {path} @{off:#x}: ...{ctxs}...")

    # totals per extension
    print("\n=== files scanned per ext (context) ===")
    extc = {}
    for path, _ in files:
        extc[Path(path).suffix.lower()] = extc.get(Path(path).suffix.lower(), 0) + 1
    print("  " + str(dict(sorted(extc.items(), key=lambda kv: -kv[1]))))


if __name__ == "__main__":
    main()
