#!/usr/bin/env python3
"""Survey all 52 base .pac files: structure + Japanese text volume.

PACK layout (from seiyubase.pac bytes): 'PACK' ver/count + u32 table,
then NUL-separated UTF-8 fields. Split on NUL, keep JP segments with spans.
"""
import re
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

JP = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff\uff01-\uff60\u3005-\u3006]")


def main():
    a = cpk.load(str(C.ORIG))
    fa = a.files
    pacs = [f for f in fa if f.full_path.lower().endswith(".pac")]
    print(f".pac files: {len(pacs)}")
    tot_seg = 0
    for f in pacs:
        d = a.file_bytes(f.toc_index)
        magic = d[:4]
        n = struct.unpack("<I", d[8:12])[0] if len(d) >= 12 else -1
        # NUL-split JP segments with spans
        segs = []
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
                    segs.append((start, t))
            if i < 0:
                break
            start = i + 1
        tot_seg += len(segs)
        nb = sum(len(t.encode("utf-8")) for _, t in segs)
        print(f"  {f.full_path} magic={magic} n={n} size={len(d)} "
              f"jp_segs={len(segs)} jp_bytes={nb}")
        for s, t in segs[:3]:
            print(f"    [{s}] {t[:60]!r}")
    print(f"TOTAL pac jp segments: {tot_seg}")


if __name__ == "__main__":
    main()
