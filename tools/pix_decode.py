#!/usr/bin/env python3
"""
Empirically decode the XPIX texture of a .pix by brute-forcing the
(payload_offset, width, height, 16bpp-format) combination that yields a
sensible image, and save a PNG so we can eyeball it.

Header facts established:
  * XPIX magic, then u32 = data-end offset (= filesize - ~120)
  * a field pair holds the texture area (e.g. w_option=0x80, cas=0x800,
    cas_sce=0x400, caution=0x101000)
  * pixel payload is raw 16bpp little-endian
We scan the whole file for the pixel run, try candidate formats, pick the
(w,h) that best matches a plausible UI/background aspect, and dump PNGs.
"""
import sys
import math
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk
import numpy as np
from PIL import Image

ORIG = C.ORIG
ROOT = C.ORIG.parent.parent
OUT = ROOT / "out" / "pix_preview"
OUT.mkdir(parents=True, exist_ok=True)

# 16bpp decode tables -> RGBA8
def decode_u16(img16: np.ndarray, fmt: str) -> np.ndarray:
    v = img16.astype(np.uint32)
    if fmt == "ARGB1555":
        a = ((v >> 15) & 1) * 255
        r = ((v >> 10) & 0x1F) * 255 // 31
        g = ((v >> 5) & 0x1F) * 255 // 31
        b = (v & 0x1F) * 255 // 31
    elif fmt == "RGB565":
        a = np.full_like(v, 255)
        r = ((v >> 11) & 0x1F) * 255 // 31
        g = ((v >> 5) & 0x3F) * 255 // 63
        b = (v & 0x1F) * 255 // 31
    elif fmt == "ARGB4444":
        a = ((v >> 12) & 0xF) * 17
        r = ((v >> 8) & 0xF) * 17
        g = ((v >> 4) & 0xF) * 17
        b = (v & 0xF) * 17
    else:
        raise ValueError(fmt)
    out = np.stack([r, g, b, a], axis=-1).astype(np.uint8)
    return out


def factor_pairs(area: int):
    """Return (w,h) factor pairs near-square first."""
    pairs = []
    for w in range(1, int(math.isqrt(area)) + 1):
        if area % w == 0:
            pairs.append((w, area // w))
            pairs.append((area // w, w))
    # sort by aspect ratio closeness to 16:9 then near-square
    pairs = list(dict.fromkeys(pairs))
    pairs.sort(key=lambda wh: abs(math.log((wh[0] + 1) / (wh[1] + 1))))
    return pairs


def main():
    a = cpk.load(str(ORIG))
    files = {f.full_path: f for f in a.files}
    targets = ["DATA/spr/w_option.pix", "DATA/spr/cas_sce.pix",
               "DATA/spr/alwaysCom.pix", "DATA/spr/caution.pix"]
    for p in targets:
        if p not in files:
            continue
        d = a.file_bytes(files[p].toc_index)
        xi = d.find(b"XPIX")
        if xi < 0:
            continue
        # data-end offset (u32 right after XPIX)
        data_end = int.from_bytes(d[xi + 4:xi + 8], "little")
        # area field: try the u32 that repeats (0x78-ish). Use filesize-128..160
        # The field with a value that cleanly factors is the area.
        # Grab candidate area fields.
        cand = []
        for off in range(xi + 4, xi + 0x40, 4):
            val = int.from_bytes(d[off:off + 4], "little")
            if 256 <= val <= len(d) and val % 2 == 0:
                cand.append((off, val))
        print(f"\n=== {p} ({len(d)} B) XPIX@{xi:#x} data_end={data_end} ===")
        print(f"  candidate area fields: {[(hex(o), v) for o, v in cand]}")

        # payload begins somewhere after the header; the fixed tail structure
        # (FF00FF00, 0x01000000, 0x80000000, area, 0x20188) is ~0x40 bytes.
        # Pixel run = from (xi+0x40) to data_end.
        payload = d[xi + 0x40:data_end]
        print(f"  payload bytes: {len(payload)}")
        area_guess = len(payload) // 2
        pairs = factor_pairs(area_guess)[:4]
        print(f"  area~{area_guess}  top factor pairs: {pairs[:4]}")

        saved = []
        for fmt in ("ARGB1555", "RGB565", "ARGB4444"):
            arr = np.frombuffer(payload, dtype="<u2")
            rgba = decode_u16(arr, fmt)
            for (w, h) in pairs[:2]:
                if w * h != len(arr):
                    continue
                img = rgba.reshape(h, w, 4)
                fn = OUT / f"{Path(p).stem}_{fmt}_{w}x{h}.png"
                Image.fromarray(img, "RGBA").save(fn)
                saved.append(fn.name)
        print(f"  saved: {saved}")


if __name__ == "__main__":
    main()
