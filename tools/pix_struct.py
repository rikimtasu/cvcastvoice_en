#!/usr/bin/env python3
"""
Deep structural analysis of the FPIX container + correlate .spr/.fon.

Goal: crack the header so we can locate (width, height, pixel-format, payload
offset) of the baked texture in each .pix, which is the prerequisite for
decode -> edit -> re-encode -> in-place swap.

Strategy:
  * find every FPIX/DPIX/XPIX magic offset in the file
  * hex-dump the region around each, annotating LE ints of several widths
  * fully hex-dump the smallest .pix (fits easily)
  * dump a couple .spr and all .fon for correlation
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

ORIG = C.ORIG
MAGICS = (b"FPIX", b"DPIX", b"XPIX", b"PPIX", b"NPIX", b"CPIX", b"GPIX")


def annot(data: bytes, base: int, n: int) -> str:
    """Hex + ASCII + LE integer reads for n bytes."""
    b = data[:n]
    lines = []
    for i in range(0, len(b), 16):
        chunk = b[i:i + 16]
        hexs = " ".join(f"{x:02x}" for x in chunk)
        asc = "".join(chr(x) if 0x20 <= x <= 0x7E else "." for x in chunk)
        off = base + i
        u16 = " ".join(
            f"{int.from_bytes(chunk[j:j+2],'little'):5d}"
            for j in range(0, len(chunk) - 1, 2))
        lines.append(f"    {off:06x}  {hexs:<47s}  |{asc}|")
        lines.append(f"              u16LE: {u16}")
    return "\n".join(lines)


def find_magics(data: bytes):
    hits = []
    for m in MAGICS:
        start = 0
        while True:
            i = data.find(m, start)
            if i < 0:
                break
            hits.append((i, m))
            start = i + 1
    return sorted(hits)


def main():
    a = cpk.load(str(ORIG))
    files = {f.full_path: f for f in a.files}
    pix = {p: a.file_bytes(files[p].toc_index)
           for p in files if p.lower().endswith(".pix")}
    spr = {p: a.file_bytes(files[p].toc_index)
           for p in files if p.lower().endswith(".spr")}
    fon = {p: a.file_bytes(files[p].toc_index)
           for p in files if p.lower().endswith(".fon")}

    smallest = min(pix, key=lambda p: len(pix[p]))
    print(f"=== smallest .pix: {smallest} ({len(pix[smallest])} bytes) ===")
    d = pix[smallest]
    print(annot(d, 0, min(len(d), 256)))

    # magic map for a few representative pix
    print("\n=== magic offsets (representative) ===")
    for p in ("DATA/spr/caution.pix", "DATA/spr/cas.pix", "DATA/spr/cas_menu.pix"):
        if p not in pix:
            # try alternatives
            continue
        d = pix[p]
        hits = find_magics(d)
        print(f"\n  {p}  ({len(d)} bytes)  magics={len(hits)}")
        for off, m in hits[:20]:
            print(f"    @{off:#08x} {m.decode('ascii','replace')}")

    # list .spr and .fon names
    print("\n=== .spr files (all) ===")
    for p in sorted(spr):
        print(f"  {p}  ({len(spr[p])} B)")
    print("\n=== .fon files (all) ===")
    for p in sorted(fon):
        print(f"  {p}  ({len(fon[p])} B)")
    if fon:
        fp = sorted(fon)[0]
        print(f"\n=== .fon dump: {fp} ({len(fon[fp])} B) ===")
        print(annot(fon[fp], 0, min(len(fon[fp]), 200)))

    # a small .spr dump
    if spr:
        sp = min(spr, key=lambda p: len(spr[p]))
        print(f"\n=== smallest .spr: {sp} ({len(spr[sp])} B) ===")
        print(annot(spr[sp], 0, min(len(spr[sp]), 200)))


if __name__ == "__main__":
    main()
