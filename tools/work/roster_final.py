#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final roster extraction from seiyubase.pac using the authoritative header index:
50 entries {u32 size @36+32k, u32 offset @40+32k}. Per record:
  - start u16 (id candidate)
  - sorted u16 list just before the name (ca%03d character ids)
  - name / kana
Emit roster.txt: idx, id, name, kana, n_ca, ca list.
Cross-check: id == 265+idx?  ca values <= 223?
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

    recs = []
    for k in range(64):
        base = 36 + 32 * k
        if base + 8 > 0x668:
            break
        size = struct.unpack_from("<I", d, base)[0]
        off = struct.unpack_from("<I", d, base + 4)[0]
        if not (0 < size < 8000 and 0x600 <= off < len(d)):
            break
        recs.append((off, size))
    print("index entries: %d" % len(recs))

    lines = ["idx  id    name                kana                n_ca  ca-list"]
    rows = []
    for idx, (start, size) in enumerate(recs):
        seg = d[start:start + size]
        # start u16 (LE)
        idu = struct.unpack_from("<H", seg, 0)[0]
        # name = first NUL-terminated field that contains kanji or kana
        fields = []
        p = 0
        while True:
            i = seg.find(b"\x00", p)
            if i < 0:
                break
            if i > p:
                fields.append((p, seg[p:i]))
            p = i + 1
        name = kana = None
        name_off = None
        for j, (o, b) in enumerate(fields):
            try:
                t = b.decode("utf-8")
            except UnicodeDecodeError:
                continue
            if name is None and re.search(r"[\u4e00-\u9fff]", t) and len(t) <= 16:
                name, name_off = t, o
            elif name is not None and kana is None and \
                    re.fullmatch(r"[\u3040-\u309f\u30a0-\u30ff\u3000]+", t):
                kana = t
                break
        # ca-list: u16 LE sequence immediately before name_off (walk back over
        # sorted u16 values), max 64
        cas = []
        if name_off and name_off >= 2:
            q = name_off
            prev = None
            while q >= 2:
                v = struct.unpack_from("<H", seg, q - 2)[0]
                if v > 223 or v == 0:
                    break
                if prev is not None and v >= prev:
                    break
                cas.append(v)
                prev = v
                q -= 2
            cas.reverse()
        ca_str = " ".join("ca%03d" % v for v in cas)
        rows.append((idx, idu, name or "?", kana or "", cas))
        lines.append("%3d  %3d  %-19s %-19s %4d  %s"
                     % (idx, idu, name or "?", kana or "", len(cas), ca_str))

    # cross-checks
    lines.append("")
    ok_id = sum(1 for i, idu, *_ in rows if idu == 265 + i)
    lines.append("id == 265+idx : %d/%d" % (ok_id, len(rows)))
    bad_ca = [(i, max(c)) for i, _, _, _, c in rows if c and max(c) > 223]
    lines.append("ca > 223 violations: %s" % (bad_ca or "none"))
    for i, idu, name, kana, cas in rows:
        if name and "伊月" in name:
            lines.append("")
            lines.append("TARGET 八尾伊月: idx=%d id=%d n_ca=%d ca=%s"
                         % (i, idu, len(cas), " ".join("ca%03d" % v for v in cas)))

    Path("tools/work/_roster3.txt").write_text("\n".join(lines), encoding="utf-8")
    print("wrote tools/work/_roster3.txt  rows=%d" % len(rows))


if __name__ == "__main__":
    main()
