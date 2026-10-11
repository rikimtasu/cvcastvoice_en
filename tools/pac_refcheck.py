#!/usr/bin/env python3
"""
Decide the SAFE replacement strategy for .pac strings.

The surgical patcher relays the WHOLE modified file uncompressed into the tail,
so absolute file length is free. The risk is INTERNAL references:
  * Are string offsets referenced by (a) absolute offset fields, (b) a
    per-record length/count, or (c) nothing (walked sequentially)?
If (b) or (c), changing a string's length is safe as long as we keep the file
internally consistent. If (a), we must keep 1:1 length.

We test empirically: locate a name record, read its declared length fields,
and scan the whole .pac for any absolute offset that points at a string start.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

ORIG = C.ORIG


def u16(d, o): return int.from_bytes(d[o:o + 2], "little")
def u32(d, o): return int.from_bytes(d[o:o + 4], "little")


def scan_abs_refs(d: bytes, target: int):
    """Find every u32/u16 (LE/BE) in the file whose value == target."""
    hits = []
    for o in range(0, len(d) - 4):
        if u32(d, o) == target:
            hits.append((o, "u32le"))
    return hits


def main():
    a = cpk.load(str(ORIG))
    files = {f.full_path: f for f in a.files}
    for p, nameoff in (("DATA/daihon/daihonbase.pac", 0x3a29),
                       ("DATA/daihon/seiyubase.pac", 0xc9d2)):
        f = files[p]
        d = a.file_bytes(f.toc_index)
        print(f"\n========== {p} ({len(d)} B) ==========")
        # dump 40 bytes before the name to see the record header
        s = max(0, nameoff - 32)
        print("  record header region:")
        for o in range(s, nameoff + 16, 4):
            print(f"    @{o:#07x}  u32={u32(d,o):>8d}  u16=({u16(d,o)},{u16(d,o+2)})")
        # name declared length: find the null terminator
        z = d.find(b"\x00", nameoff)
        raw = d[nameoff:z]
        print(f"  name bytes: {raw!r}  ({len(raw)} B, ends @{z:#x})")
        # the u16 pair before looked like 0x4a=74. Check bytes right before
        cap_candidates = []
        for back in range(2, 12):
            o = nameoff - back
            if o >= 0:
                cap_candidates.append((o, u16(d, o)))
        print(f"  u16s leading up to name: {cap_candidates}")
        # scan for absolute refs to this string start anywhere
        hits = scan_abs_refs(d, nameoff)
        print(f"  absolute u32-LE refs to {nameoff:#x}: {len(hits)} {hits[:8]}")
        # Also: is there an index/count near the header pointing here?
        # check small u32s whose value == nameoff
        small = [(o, u32(d, o)) for o in range(0, min(len(d), 0x400), 4)
                 if u32(d, o) == nameoff]
        print(f"  u32-LE in header(0..0x400) == {nameoff:#x}: {small}")

        # The real question: does the .pac store a table of (offset,len,name)?
        # If so there will be many u16 == raw length. Count occurrences of len.
        n = len(raw)
        eq = sum(1 for o in range(0, len(d) - 1) if u16(d, o) == n)
        print(f"  u16 == name_len({n}) anywhere: {eq} occurrences")


if __name__ == "__main__":
    main()
