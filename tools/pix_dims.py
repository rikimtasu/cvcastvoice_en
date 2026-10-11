#!/usr/bin/env python3
"""
Cross-correlate .pix XPIX header fields with the paired .spr to identify the
(width,height) encoding, and confirm the pixel payload is raw 16bpp.

XPIX header layout hypothesis (from w_option.pix @0x4c):
  +0  'XPIX'
  +4  u32 0x000080a0  (32928)   <-- maybe header size / data end offset
  +8  u32 0x00000001  (1)       count?
  +0xc u32 0
  +0x10 u32 0
  +0x14 u32 0
  +0x18 u32 0
  +0x1c u16 0x0202   (514)      <-- maybe height<<8|? or 2 u8
  +0x1e u16 0xff00   <-- pixel data begins? looks like 0x00ff/0xff00 sample
  ...
We instead brute force: try interpreting payload as several 16bpp formats,
scan for the dominant uniform run, and check whether header integer fields
encode w/h consistent with (filesize-headerlen)/bpp.
"""
import sys
import collections
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

ORIG = C.ORIG


def xpix_header_fields(d: bytes):
    """Read the first XPIX header and return candidate integer fields."""
    i = d.find(b"XPIX")
    if i < 0:
        return None
    import struct
    fields = {}
    base = i
    fields["magic_at"] = i
    # read a bunch of LE ints following
    vals = []
    for off in range(base + 4, base + 0x40, 4):
        vals.append((off, int.from_bytes(d[off:off + 4], "little")))
    fields["u32s_after"] = vals
    # u16s in the pixel-ish region
    u16s = []
    for off in range(base + 0x18, base + 0x30, 2):
        u16s.append((off, int.from_bytes(d[off:off + 2], "little")))
    fields["u16s"] = u16s
    return fields


def main():
    a = cpk.load(str(ORIG))
    files = {f.full_path: f for f in a.files}
    pix = {p: a.file_bytes(files[p].toc_index)
           for p in files if p.lower().endswith(".pix")}

    # 1) header fields for a few representative files
    for p in ("DATA/spr/w_option.pix", "DATA/spr/cas_sce.pix",
              "DATA/spr/caution.pix", "DATA/spr/cas.pix"):
        if p not in pix:
            continue
        d = pix[p]
        f = xpix_header_fields(d)
        print(f"\n=== {p} ({len(d)} B) ===")
        print(f"  XPIX @ {f['magic_at']:#x}")
        print("  u32 LE after magic:",
              ", ".join(f"{o:#x}={v}" for o, v in f["u32s_after"]))
        print("  u16 LE @ +0x18..:", ", ".join(f"{v}" for o, v in f["u16s"]))

    # 2) dominant uniform 16-bit value + run length in each payload
    print("\n=== payload 16-bit analysis ===")
    for p in sorted(pix)[:6]:
        d = pix[p]
        xi = d.find(b"XPIX")
        payload = d[xi + 0x1c:]  # rough start
        # count u16 LE and BE frequencies in a sample window
        win = payload[:8192]
        le = collections.Counter(
            int.from_bytes(win[j:j + 2], "little") for j in range(0, len(win) - 1, 2))
        be = collections.Counter(
            int.from_bytes(win[j:j + 2], "big") for j in range(0, len(win) - 1, 2))
        le_top = le.most_common(3)
        be_top = be.most_common(3)
        print(f"  {p}")
        print(f"    XPIX@{xi:#x} payload_len~{len(payload)}")
        print(f"    u16LE top: {[(hex(k), v) for k, v in le_top]}")
        print(f"    u16BE top: {[(hex(k), v) for k, v in be_top]}")

    # 3) paired .spr dimension cross-check for w_option
    print("\n=== paired .spr cross-check ===")
    for p in ("DATA/spr/w_option.spr", "DATA/spr/cas_sce.spr"):
        if p not in files:
            continue
        sd = a.file_bytes(files[p].toc_index)
        # look for w,h-ish small int pairs
        import struct
        pairs = []
        for off in range(0, min(len(sd), 0x400), 4):
            v = int.from_bytes(sd[off:off + 4], "little")
            if 0 < v < 4096:
                pairs.append((off, v))
        print(f"  {p} ({len(sd)} B) small-int u32s: {pairs[:20]}")


if __name__ == "__main__":
    main()
