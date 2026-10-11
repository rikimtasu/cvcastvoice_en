#!/usr/bin/env python3
"""
Diagnose the 2 deep-verify non-text diffs in the .pac files.

For each .pac, load original (decompressed) and patched (decompressed),
locate every differing byte, and show the surrounding context so we can tell
whether the diff is exactly our string edits (good) or something else (bug).
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

ORIG = C.ORIG


def load(path):
    a = cpk.load(str(path))
    return {f.full_path: f for f in a.files}, a


def ctx(b, i, k=28):
    seg = b[max(0, i - k):i + k]
    return " ".join(f"{x:02x}" for x in seg), \
        "".join(chr(x) if 0x20 <= x <= 0x7E else "." for x in seg)


def diffs_of(orig, new, ov):
    spans = []
    for r in ov.get("runs", []):
        spans.append((r["span"][0], r["span"][1]))
    covered = bytearray(len(orig))
    for s, e in spans:
        for i in range(max(0, s), min(len(orig), e)):
            covered[i] = 1
    out = []
    n = min(len(orig), len(new))
    i = 0
    while i < n:
        if orig[i] != new[i]:
            j = i
            while j < n and orig[j] != new[j]:
                j += 1
            out.append((i, j, covered[i]))
            i = j
        else:
            i += 1
    return out, covered


def main():
    overlay_path = C.WORK / "pac_overlay.json"
    ov = json.loads(overlay_path.read_bytes().decode("utf-8-sig"))
    files = ov["files"] if "files" in ov else ov

    of, oa = load(ORIG)
    nf, na = load(C.WORK.parent.parent / "out" / "GameData_en.cpk")

    for path in ("DATA/daihon/daihonbase.pac", "DATA/daihon/seiyubase.pac"):
        if path not in files:
            print(f"{path}: NOT in overlay")
            continue
        o = oa.file_bytes(of[path].toc_index)
        n = na.file_bytes(nf[path].toc_index)
        print(f"\n=== {path} ===")
        print(f"  orig len {len(o)}  new len {len(n)}  "
              f"{'equal len' if len(o)==len(n) else 'LEN CHANGED'}")
        ovp = files[path]
        dfr, covered = diffs_of(o, n, ovp)
        inside = [d for d in dfr if d[2]]
        outside = [d for d in dfr if not d[2]]
        print(f"  diff ranges total {len(dfr)}  inside overlay spans {len(inside)}  "
              f"OUTSIDE spans {len(outside)}")
        for s, e, cov in dfr[:20]:
            hx, asc = ctx(o, s)
            hx2, asc2 = ctx(n, s)
            tag = "IN-SPAN " if cov else "OUT-SPAN"
            print(f"    {tag} [{s:#x},{e:#x}) len {e-s}")
            print(f"        orig: ...{asc}...")
            print(f"        new : ...{asc2}...")
        # Verify: are ALL diffs inside overlay spans?
        if not outside:
            print("  RESULT: all diffs are inside declared overlay spans ✓")
        else:
            print(f"  RESULT: {len(outside)} diff range(s) OUTSIDE spans ✗")


if __name__ == "__main__":
    import traceback
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
