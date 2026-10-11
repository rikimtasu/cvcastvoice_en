#!/usr/bin/env python3
"""
Determine how the ON-SCREEN dialogue speaker name is sourced.

The .srt text runs are all translated, yet the name box still shows 春香.
So the name is either:
  (a) a separate data field inside the .srt we did NOT touch (referenced by id),
  (b) looked up from daihonbase.pac by character id, or
  (c) baked pixels.

Dump the raw structure of a .srt that mentions 天海春香, showing the bytes
around each dialogue run and any nearby id/length fields, plus how @n and the
U+22BF terminator frame the text. Also list the .srt's non-text header region.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

ORIG = C.ORIG


def hexdump(data: bytes, start: int, length: int) -> str:
    b = data[start:start + length]
    out = []
    for i in range(0, len(b), 16):
        chunk = b[i:i + 16]
        hexs = " ".join(f"{x:02x}" for x in chunk)
        asc = "".join(chr(x) if 0x20 <= x <= 0x7E else "." for x in chunk)
        out.append(f"  {start + i:06x}  {hexs:<47s}  |{asc}|")
    return "\n".join(out)


def main():
    a = cpk.load(str(ORIG))
    files = {f.full_path: f for f in a.files}
    target = "DATA/srt_dh/P015_01.srt"
    f = files.get(target)
    if not f:
        # fall back to any srt containing 天海春香
        for p, ff in files.items():
            if p.endswith(".srt") and b"\xe5\xa4\xa9\xe6\xb5\xb7\xe6\x98\xa5\xe9\xa6\x99" in a.file_bytes(ff.toc_index):
                target, f = p, ff
                break
    d = a.file_bytes(f.toc_index)
    print(f"file: {target}  extract={f.extract_size} stored={f.file_size} "
          f"len={len(d)}")
    print(f"  head magic: {d[:8]!r}")
    print("\n=== first 160 bytes (FSRT/XSRT headers) ===")
    print(hexdump(d, 0, 160))

    # find 天海春香 and 春香 and dump surroundings
    for needle, label in ((b"\xe5\xa4\xa9\xe6\xb5\xb7\xe6\x98\xa5\xe9\xa6\x99", "天海春香"),
                          (b"\xe6\x98\xa5\xe9\xa6\x99", "春香")):
        i = d.find(needle)
        print(f"\n=== {label} @ {i:#x} ===")
        if i >= 0:
            print(hexdump(d, max(0, i - 40), 120))

    # Show how dialogue runs are framed: locate all U+22BF terminators
    term = b"\xe2\x8a\xbf"
    pos = []
    s = 0
    while True:
        j = d.find(term, s)
        if j < 0:
            break
        pos.append(j)
        s = j + 1
    print(f"\n=== U+22BF terminators: {len(pos)} ===")
    print(f"  first few offsets: {[hex(x) for x in pos[:10]]}")

    # Show a full framed dialogue run: from a terminator to the next
    if len(pos) >= 2:
        # find the run containing 春香
        i = d.find(b"\xe6\x98\xa5\xe9\xa6\x99")
        # walk back to preceding terminator pair and forward
        start = 0
        for p in pos:
            if p <= i:
                start = p
            else:
                end = p
                break
        else:
            end = len(d)
        print(f"\n=== framed run around 春香: [{start:#x}, {end:#x}) ===")
        seg = d[start:end + 3]
        print(f"  bytes ({len(seg)}): {seg!r}")
        print(f"  decoded: {seg.decode('utf-8','replace')!r}")


if __name__ == "__main__":
    main()
