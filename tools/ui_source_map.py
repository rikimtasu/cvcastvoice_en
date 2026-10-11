#!/usr/bin/env python3
"""
Pin down where the ON-SCREEN UI name/credit text actually comes from, so we
know what is pixel-editable vs text-patchable.

Questions:
  1. Short speaker name 春香 / full 天海春香  -> where stored (pac text? srt? pix?)
  2. CV credit 西宮寺　美礼 / 西宮寺 美礼     -> where stored
  3. Are the .pac name strings offset-indexed (absolute offsets elsewhere) or
     walked as null-terminated (=> same-length padding is safe)?

Decompresses each .pac via cricodecs.file_bytes() (already returns extracted).
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

ORIG = C.ORIG

STRINGS = {
    "haruka_short": "春香",
    "haruka_full": "天海春香",
    "nishinomiya_wide": "西宮寺　美礼",
    "nishinomiya_narrow": "西宮寺 美礼",
    "mirei": "美礼",
    "skip": "スキップ",
    "auto": "オート",
    "window": "ウィンドウ",
    "ff": "早送り",
}


def main():
    a = cpk.load(str(ORIG))
    files = {f.full_path: f for f in a.files}

    # preload all file bytes once (decompressed)
    cache = {}
    for p, f in files.items():
        cache[p] = a.file_bytes(f.toc_index)

    print("=== where does each on-screen UI string occur? ===")
    for key, s in STRINGS.items():
        b = s.encode("utf-8")
        locs = []
        for p, d in cache.items():
            i = d.find(b)
            if i >= 0:
                ext = Path(p).suffix.lower()
                locs.append((ext, p, i))
        by_ext = {}
        for ext, p, i in locs:
            by_ext[ext] = by_ext.get(ext, 0) + 1
        print(f"\n  {key:18s} {s!r}")
        print(f"    by ext: {dict(sorted(by_ext.items(), key=lambda kv:-kv[1]))}")
        # show non-srt/info locations (the interesting UI ones)
        interesting = [(e, p, i) for e, p, i in locs if e in (".pac", ".spr", ".pix", ".fon", ".txt", ".mcl", ".png")]
        for e, p, i in interesting[:12]:
            print(f"      [{e}] {p} @{i:#x}")

    # .pac internal structure: is there offset-indexing to name strings?
    print("\n\n=== .pac name-record structure (daihonbase.pac) ===")
    d = cache.get("DATA/daihon/daihonbase.pac")
    if d:
        for needle in (b"\xe6\x98\xa5\xe9\xa6\x99",          # 春香
                       b"\xe5\xa4\xa9\xe6\xb5\xb7\xe6\x98\xa5\xe9\xa6\x99"):  # 天海春香
            i = d.find(needle)
            print(f"  find {needle.decode('utf-8')}: @{i:#x}")
        # dump record around 天海春香 with u32 annotations
        i = d.find(b"\xe5\xa4\xa9\xe6\xb5\xb7\xe6\x98\xa5\xe9\xa6\x99")
        if i >= 0:
            lo = max(0, i - 32)
            seg = d[lo:i + 48]
            print(f"  record bytes @ {lo:#x}:")
            for off in range(lo, i + 48, 4):
                v = int.from_bytes(d[off:off + 4], "little")
                print(f"    {off:#08x}  u32LE={v:<12d} 0x{v:08x}")

    print("\n=== header offset fields (daihonbase.pac, first 64B as u32) ===")
    if d:
        for off in range(0, 64, 4):
            v = int.from_bytes(d[off:off + 4], "little")
            print(f"    {off:#04x}  u32LE={v:<12d} 0x{v:08x}")
        print(f"    file len = {len(d)}")

    # does any absolute offset in the pac header point at the name string?
    if d:
        i = d.find(b"\xe5\xa4\xa9\xe6\xb5\xb7\xe6\x98\xa5\xe9\xa6\x99")
        print(f"\n=== scan for absolute offset == {i:#x} anywhere in pac ===")
        tgt = i.to_bytes(4, "little")
        j = d.find(tgt)
        cnt = 0
        pos = []
        s = 0
        while True:
            j = d.find(tgt, s)
            if j < 0:
                break
            pos.append(hex(j))
            s = j + 1
            cnt += 1
        print(f"  LE u32 == {i:#x}: {cnt} occurrence(s) at {pos[:10]}")


if __name__ == "__main__":
    main()
