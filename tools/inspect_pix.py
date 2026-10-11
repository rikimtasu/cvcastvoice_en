#!/usr/bin/env python3
"""
Inspect image-ish files in GameData.cpk to learn the .pix format before we try
to decode / edit / re-encode them.

Dumps: extension histogram, .pix size stats, header hex of the first few .pix,
and whether numpy / PIL are importable in this interpreter.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

ORIG = C.ORIG


def hexdump(data: bytes, n: int = 64) -> str:
    b = data[:n]
    out = []
    for i in range(0, len(b), 16):
        chunk = b[i:i + 16]
        hexs = " ".join(f"{x:02x}" for x in chunk)
        asc = "".join(chr(x) if 0x20 <= x <= 0x7E else "." for x in chunk)
        out.append(f"    {i:04x}  {hexs:<47s}  {asc}")
    return "\n".join(out)


def main():
    # library availability
    libs = {}
    for name in ("numpy", "PIL", "cv2"):
        try:
            __import__(name)
            libs[name] = "OK"
        except Exception as ex:
            libs[name] = f"MISSING ({ex.__class__.__name__})"
    print("=== libraries ===")
    for k, v in libs.items():
        print(f"  {k:6s} {v}")

    a = cpk.load(str(ORIG))
    exts = {}
    allpaths = []
    for f in a.files:
        allpaths.append(f.full_path)
        ext = Path(f.full_path).suffix.lower()
        exts[ext] = exts.get(ext, 0) + 1
    print("\n=== extension histogram (all 8400) ===")
    for ext, cnt in sorted(exts.items(), key=lambda kv: -kv[1]):
        print(f"  {ext or '(none)':10s} {cnt}")

    # image candidates
    img_exts = {".pix", ".png", ".dds", ".tga", ".gtx", ".gxt", ".bmp",
                ".jpg", ".jpeg", ".gim", ".gif", ".tex", ".vram"}
    pix = [(f, a.file_bytes(f.toc_index)) for f in a.files
           if Path(f.full_path).suffix.lower() in img_exts]
    print(f"\n=== image-candidate files: {len(pix)} ===")
    by_ext = {}
    for f, d in pix:
        by_ext.setdefault(Path(f.full_path).suffix.lower(), []).append((f, d))
    for ext, lst in sorted(by_ext.items()):
        sizes = sorted(len(d) for _, d in lst)
        print(f"  {ext:8s} count={len(lst):4d}  min={sizes[0]}  "
              f"median={sizes[len(sizes)//2]}  max={sizes[-1]}")

    # .pix specifics
    pixonly = by_ext.get(".pix", [])
    print(f"\n=== .pix paths (first 40) ===")
    for f, _ in pixonly[:40]:
        print(f"  {f.full_path}")
    if len(pixonly) > 40:
        print(f"  ... ({len(pixonly)-40} more)")

    print("\n=== .pix header hex (first 8) ===")
    for f, d in pixonly[:8]:
        print(f"\n  {f.full_path}  ({len(d)} bytes)")
        print(hexdump(d, 96))

    # distinct leading 4-byte magics among .pix
    magics = {}
    for f, d in pixonly:
        m = d[:4]
        magics[m] = magics.get(m, 0) + 1
    print("\n=== .pix leading 4-byte magics ===")
    for m, cnt in sorted(magics.items(), key=lambda kv: -kv[1]):
        asc = "".join(chr(x) if 0x20 <= x <= 0x7E else "." for x in m)
        print(f"  {m.hex()}  '{asc}'  x{cnt}")


if __name__ == "__main__":
    main()
