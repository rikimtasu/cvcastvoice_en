#!/usr/bin/env python3
"""
Locate the real pixel payload inside a .pix and characterize it, so we can
decode -> edit -> re-encode.

Emits, for the smallest .pix:
  * full hex dump to work/pix_woption.hex
  * zero-run map (header/padding vs payload)
  * byte-value histogram of the tail (is it compressed? palettized? raw RGBA?)
  * candidate (w,h) for several pixel formats given payload length
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

ORIG = C.ORIG


def zero_runs(data: bytes, minrun: int = 16):
    runs = []
    i = 0
    n = len(data)
    while i < n:
        if data[i] == 0:
            j = i
            while j < n and data[j] == 0:
                j += 1
            if j - i >= minrun:
                runs.append((i, j - i))
            i = j
        else:
            i += 1
    return runs


def hexdump(data: bytes) -> str:
    out = []
    for i in range(0, len(data), 16):
        chunk = data[i:i + 16]
        hexs = " ".join(f"{x:02x}" for x in chunk)
        asc = "".join(chr(x) if 0x20 <= x <= 0x7E else "." for x in chunk)
        out.append(f"{i:06x}  {hexs:<47s}  |{asc}|")
    return "\n".join(out)


def main():
    a = cpk.load(str(ORIG))
    files = {f.full_path: f for f in a.files}
    pix = {p: a.file_bytes(files[p].toc_index)
           for p in files if p.lower().endswith(".pix")}
    smallest = min(pix, key=lambda p: len(pix[p]))
    d = pix[smallest]
    print(f"file: {smallest}  {len(d)} bytes")

    (C.WORK / "pix_woption.hex").write_text(hexdump(d), encoding="utf-8")
    print(f"full hex -> {C.WORK / 'pix_woption.hex'}")

    zr = zero_runs(d, 16)
    print(f"\n=== zero runs >=16 B (first 30) — {len(zr)} total ===")
    for off, ln in zr[:30]:
        print(f"  @{off:#08x}  len {ln}")

    # tail histogram: how compressed / how raw?
    import collections
    tail = d[-4096:]
    hist = collections.Counter(tail)
    distinct = len(hist)
    top = hist.most_common(8)
    print(f"\n=== tail 4096B entropy proxy ===")
    print(f"  distinct byte values: {distinct}/256")
    print(f"  most common: {[(hex(k), v) for k, v in top]}")

    # candidate dimensions from payload length for common formats
    # guess payload starts after first big zero-run ends
    # find last zero-run that ends before the bulk data
    print(f"\n=== candidate dims (payload_len = {len(d)}) ===")
    fmts = {
        "RGBA8888 (4B/px)": 4, "RGB888 (3B/px)": 3, "RGBA4444 (2B/px)": 2,
        "RGB565 (2B/px)": 2, "ARGB1555 (2B/px)": 2, "A8/L8 (1B/px)": 1,
        "A4/L4 (0.5B/px)": 0.5, "BC1/DXT1 (0.5B/px)": 0.5,
        "BC2/DXT3 (1B/px)": 1, "BC3/DXT5 (1B/px)": 1,
    }
    import math
    for name, bpp in fmts.items():
        px = len(d) / bpp
        s = int(math.isqrt(px))
        print(f"  {name:20s} ~{px:9.0f} px  sqrt~{s}  "
              f"({s} x {len(d)//(bpp*s) if s else 0})")


if __name__ == "__main__":
    main()
