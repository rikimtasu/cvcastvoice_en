#!/usr/bin/env python3
"""
Parse a paired .spr (SPRF header -> OBJT records) to recover the texture
dimensions / source rect that the engine uses to draw each .pix.

We already saw .spr has:
  'SPRF' + u32 size + counts, then 'OBJT' + u32 size + record fields.
In test2.spr the OBJT carried fields like 0x30,0x40,0x50,0xb0,0x110,0x117,...
which look like x,y,w,h coordinates in some fixed-point (>>? ) scale.

Approach:
  * For w_option, dump the .spr fully (small) and annotate every u32/u16/float.
  * Identify repeated 4-tuples that look like (x,y,w,h) rectangles.
  * Cross-check against .pix header field 0x78 (which held 0x80 for w_option,
    0x800 for cas, 0x400 for cas_sce, 0x101000 for caution) -> that may be the
    AREA in pixels (w*h) or the texture stride.
"""
import sys
import struct
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

ORIG = C.ORIG


def u32(d, o): return int.from_bytes(d[o:o + 4], "little")
def u16(d, o): return int.from_bytes(d[o:o + 2], "little")
def f32(d, o):
    try:
        return struct.unpack("<f", d[o:o + 4])[0]
    except Exception:
        return float("nan")


def annot_spr(sd: bytes, name: str, maxoff: int):
    print(f"\n=== {name} ({len(sd)} B) ===")
    n = min(len(sd), maxoff)
    for o in range(0, n, 16):
        chunk = sd[o:o + 16]
        hexs = " ".join(f"{x:02x}" for x in chunk)
        asc = "".join(chr(x) if 0x20 <= x <= 0x7E else "." for x in chunk)
        u32s = " ".join(f"{u32(sd, o+4*k):>8d}" for k in range(4))
        fl = " ".join(f"{f32(sd, o+4*k):8.2f}" for k in range(4))
        print(f"  {o:05x}  {hexs:<47s} |{asc}|")
        print(f"          u32: {u32s}")
        print(f"          f32: {fl}")


def main():
    a = cpk.load(str(ORIG))
    files = {f.full_path: f for f in a.files}
    spr = {p: a.file_bytes(files[p].toc_index)
           for p in files if p.lower().endswith(".spr")}
    pix = {p: a.file_bytes(files[p].toc_index)
           for p in files if p.lower().endswith(".pix")}

    # annotate the smallest spr fully
    sp = min(spr, key=lambda p: len(spr[p]))
    annot_spr(spr[sp], sp, len(spr[sp]))

    # For w_option, show spr + pix header field@0x78 region
    for base in ("DATA/spr/w_option", "DATA/spr/cas_sce", "DATA/spr/caution"):
        sp = base + ".spr"
        pp = base + ".pix"
        print(f"\n########## pair {base} ##########")
        if pp in pix:
            d = pix[pp]
            xi = d.find(b"XPIX")
            print(f"  .pix {len(d)}B XPIX@{xi:#x}")
            for o in range(xi + 4, xi + 0x60, 4):
                print(f"    pix u32 @{o:#x} = {u32(d, o)}")
        if sp in spr:
            sd = spr[sp]
            print(f"  .spr {len(sd)}B  first 160B u32s:")
            for o in range(0, min(len(sd), 160), 4):
                v = u32(sd, o)
                if v or True:
                    print(f"    spr u32 @{o:#04x} = {v}   (f32 {f32(sd,o):.3f})")


if __name__ == "__main__":
    main()
