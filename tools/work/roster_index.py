#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse the seiyubase.pac header index (32-byte entries: u32 size, u32 offset)
to get authoritative record boundaries (expect 50), extract each record's name,
and emit the final roster with index -> vic-id (265+idx) mapping.
"""
import re
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import cvpatch as C
from cricodecs import cpk


def main():
    a = cpk.load(str(C.ORIG))
    by = {f.full_path: f for f in a.files}
    d = a.file_bytes(by["DATA/daihon/seiyubase.pac"].toc_index)

    # header index: find (size,offset) pairs where offset lands in record range
    # and offsets are strictly increasing -> record starts
    cand = []
    for o in range(0x20, 0x7b0, 4):
        v = struct.unpack_from("<I", d, o)[0]
        cand.append((o, v))
    # find the subsequence of increasing offsets > 0x700
    offs = [(o, v) for o, v in cand if 0x700 <= v <= len(d)]
    # greedily take increasing values that match record starts (name off - 16..-64?)
    starts = []
    last = -1
    for o, v in offs:
        if v > last:
            starts.append((o, v))
            last = v
    lines = []
    lines.append("increasing offset candidates: %d" % len(starts))
    for o, v in starts:
        lines.append("  hdr@0x%03x -> 0x%06x (%d)" % (o, v, v))

    # names at starts+something: try each candidate as record start, name = first
    # NUL-terminated utf-8 field within +0x80
    lines.append("")
    lines.append("== resolved roster ==")
    names = []
    for i, (o, v) in enumerate(starts):
        seg = d[v:v + 0x100]
        j = seg.find(b"\x00")
        if j <= 0:
            names.append("?")
            continue
        try:
            nm = seg[:j].decode("utf-8")
        except UnicodeDecodeError:
            nm = "?"
        names.append(nm)
        lines.append("  %2d  vic=%3d  @0x%06x  %s" % (i, 265 + i, v, nm))

    # find 八尾
    for i, nm in enumerate(names):
        if "伊月" in nm:
            lines.append("")
            lines.append("八尾伊月 index=%d vic=%d" % (i, 265 + i))

    Path("tools/work/_roster2.txt").write_text("\n".join(lines), encoding="utf-8")
    print("records:", len(starts), " -> wrote tools/work/_roster2.txt")


if __name__ == "__main__":
    main()
