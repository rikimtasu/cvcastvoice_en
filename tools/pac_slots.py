#!/usr/bin/env python3
"""
Precisely locate each name/title buffer in the two .pac name DBs and its true
byte capacity, so a Track-A overlay can replace the buffer contents with an
English string padded with NULs (byte-length preserved, engine-safe).

Record model (daihonbase.pac, verified on 天海春香 @0x3a29):
    ... <cap:u16> 00 00 <cap:u16> 00 00  [some tag u8s]  <name:UTF-8> 00 <NUL pad>
  The two equal u16 == capacity in bytes; the name is null-terminated and the
  slot is padded with NULs out to `cap`. Replacing [name_start, name_start+cap)
  with English + NUL pad keeps every later record at its original offset.

For seiyubase.pac the CV names sit after a u16 id table; capacities differ, so
we detect the slot width per record as: (next_record_start - name_start) OR the
repeated-u16 capacity when present, whichever is smaller and >= len(name)+1.
"""
import sys
import re
import json
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

ORIG = C.ORIG
CJK = re.compile(r"[\u3000-\u30ff\u4e00-\u9fff\uff01-\uff60]")


def u16(d, o): return int.from_bytes(d[o:o + 2], "little")


def capacity_for(d: bytes, name_start: int, name_len: int):
    """Return (capacity, cap_field_offset_or_None)."""
    # Look back up to 12 bytes for a repeated equal u16 == value >= name_len+1
    for back in range(2, 13):
        o = name_start - back
        if o < 0:
            break
        a = u16(d, o)
        b = u16(d, o + 2)
        if a == b and name_len + 1 <= a <= 4096 and a % 2 == 0:
            return a, o
    return None, None


def all_cjk_segments(d: bytes):
    """Split on NUL, return [(start, str, byte_len)] for CJK-containing segs."""
    out = []
    start = 0
    n = len(d)
    while start < n:
        z = d.find(b"\x00", start)
        if z < 0:
            z = n
        seg = d[start:z]
        if seg:
            try:
                s = seg.decode("utf-8")
            except Exception:
                s = None
            if s and CJK.search(s):
                out.append((start, s, len(seg)))
        start = z + 1
    return out


def main():
    a = cpk.load(str(ORIG))
    files = {f.full_path: f for f in a.files}
    report = {}
    for p in ("DATA/daihon/daihonbase.pac", "DATA/daihon/seiyubase.pac"):
        f = files[p]
        d = a.file_bytes(f.toc_index)
        segs = all_cjk_segments(d)
        rows = []
        for i, (off, s, blen) in enumerate(segs):
            cap, coff = capacity_for(d, off, blen)
            # slot width to next segment (fallback when no capacity field)
            nxt = segs[i + 1][0] if i + 1 < len(segs) else len(d)
            slot = nxt - off
            rows.append({
                "off": off, "str": s, "blen": blen,
                "cap": cap, "cap_off": coff, "slot_to_next": slot,
            })
        report[p] = rows
        ncap = sum(1 for r in rows if r["cap"])
        print(f"\n== {p}: {len(rows)} CJK strings, {ncap} with detected capacity ==")
        for r in rows[:12]:
            print(f"  @{r['off']:#07x} blen={r['blen']:3d} cap={r['cap']} "
                  f"slot={r['slot_to_next']:3d}  {r['str']}")
    (C.WORK / "pac_names_detail.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n-> {C.WORK / 'pac_names_detail.json'}")


if __name__ == "__main__":
    main()
