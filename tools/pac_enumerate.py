#!/usr/bin/env python3
"""
Enumerate ALL character/CV name strings in daihonbase.pac and seiyubase.pac,
with their byte offsets, the declared capacity field that precedes each, and
current byte length. This is the input for building a Track-A translation map
(same-or-shorter in-place replacement inside each fixed-width buffer).

Layout hypothesis (verified on 天海春香):
    <lenfield:u16> 00 00 <lenfield:u16> 00 00  <UTF-8 name> 00 <pad to cap>
where lenfield == the buffer capacity in bytes (74, 75, ...). We don't assume
this is exact; we print enough context to confirm per record.
"""
import sys
import re
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

ORIG = C.ORIG
CJK = re.compile(
    r"[\u3000-\u303f\u3040-\u30ff\u4e00-\u9fff\uff00-\uffef]+")


def u16(d, o): return int.from_bytes(d[o:o + 2], "little")
def u32(d, o): return int.from_bytes(d[o:o + 4], "little")


def scan_names(d: bytes):
    """Yield (offset, name_str, declared_cap_or_None)."""
    out = []
    for m in re.finditer(
            rb"(?:[\x00-\x7f]|[\xc2-\xf4][\x80-\xbf]+){2,}", d):
        # decode candidate
        try:
            s = m.group().decode("utf-8")
        except Exception:
            continue
        # find CJK-containing printable tokens separated by nulls
    # simpler: split on 0x00, decode each non-empty piece, keep CJK pieces
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
                # look back for a declared capacity: scan previous 8 bytes for
                # two equal u16 == some cap >= len(seg)
                cap = None
                for back in range(2, 9):
                    o = start - back
                    if o >= 0 and u16(d, o) == u16(d, o + 2) and u16(d, o) >= len(seg):
                        # heuristic: equal u16 pair, value >= this seg length
                        cap = u16(d, o)
                        cap_off = o
                        break
                out.append((start, s, cap, cap_off if cap else None))
        start = z + 1
    return out


def main():
    a = cpk.load(str(ORIG))
    files = {f.full_path: f for f in a.files}
    for p in ("DATA/daihon/daihonbase.pac", "DATA/daihon/seiyubase.pac"):
        f = files[p]
        d = a.file_bytes(f.toc_index)
        print(f"\n========== {p} ({len(d)} B) ==========")
        names = scan_names(d)
        # dedupe by string, keep first offset + cap
        seen = {}
        for off, s, cap, coff in names:
            if s not in seen:
                seen[s] = (off, len(s.encode("utf-8")), cap, coff)
        print(f"  unique CJK name strings: {len(seen)}")
        for s, (off, blen, cap, coff) in seen.items():
            caps = f" cap={cap}@{coff:#x}" if cap else ""
            print(f"    @{off:#07x} len={blen:3d}{caps}  {s}")
        # save full list
        outp = C.WORK / (Path(p).stem + "_names.txt")
        with outp.open("w", encoding="utf-8") as fh:
            for s, (off, blen, cap, coff) in seen.items():
                fh.write(f"{off}\t{blen}\t{cap}\t{s}\n")
        print(f"  -> {outp}")


if __name__ == "__main__":
    main()
