#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract the cast-name list from seiyubase.pac and bind it to index/ctva ids.

seiyubase.pac = voice-actor base: expect NUL-separated JP name records, one per
cast member, possibly in fixed-size slots. We dump all JP strings with offsets and
probe for a fixed stride so index i -> name.
"""
import re
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import cvpatch as C
from cricodecs import cpk

JP = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")


def main():
    a = cpk.load(str(C.ORIG))
    by = {f.full_path: f for f in a.files}
    d = a.file_bytes(by["DATA/daihon/seiyubase.pac"].toc_index)
    print("seiyubase.pac len=%d" % len(d))
    print("head hex:")
    for i in range(0, min(len(d), 96), 16):
        print("  %04x: %s" % (i, d[i:i + 16].hex(" ")))

    # collect NUL-separated JP strings with offsets
    strs = []
    start = 0
    while True:
        i = d.find(b"\x00", start)
        chunk = d[start:i] if i >= 0 else d[start:]
        if chunk:
            try:
                t = chunk.decode("utf-8")
                if JP.search(t):
                    strs.append((start, t))
            except UnicodeDecodeError:
                pass
        if i < 0:
            break
        start = i + 1
    print("\nJP strings: %d" % len(strs))
    for o, t in strs:
        print("  [%6d] %r" % (o, t))

    # stride detection: diffs between offsets of consecutive names
    if len(strs) >= 3:
        offs = [o for o, _ in strs]
        diffs = [b - a_ for a_, b in zip(offs, offs[1:])]
        print("\noffset diffs:", diffs[:40])

    with open("tools/work/_seiyu.txt", "w", encoding="utf-8") as f:
        for o, t in strs:
            f.write("[%6d] %r\n" % (o, t))
    print("wrote tools/work/_seiyu.txt")


if __name__ == "__main__":
    main()
