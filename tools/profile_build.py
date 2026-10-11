#!/usr/bin/env python3
"""Measure where `cvpatch.py build` actually spends time, on samples."""
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

ORIG = C.ORIG
SAMPLE = 60            # files sampled for the per-file costs
HDR_PATCH = 200        # placements sampled for the header-patch cost


def t():
    return time.perf_counter()


def main():
    r = {}
    t0 = t()
    a = cpk.load(str(ORIG))
    r["cpk.load (TOC only)"] = t() - t0

    t0 = t()
    buf = bytearray(ORIG.read_bytes())
    r["ORIG.read_bytes (326MB -> bytearray)"] = t() - t0
    N = len(buf)

    ov = json.loads((C.WORK / "overlay.json")
                    .read_text(encoding="utf-8"))
    root = ov["files"] if "files" in ov else ov
    bytoc = {f.full_path: f for f in a.files}
    paths = [p for p in root if p in bytoc][:SAMPLE]

    # (1) per-file: decompress
    t0 = t()
    datas = []
    for p in paths:
        datas.append(a.file_bytes(bytoc[p].toc_index))
    d_decomp = t() - t0

    # (2) per-file: re-parse spans in pure Python
    t0 = t()
    nspans = 0
    for p, d in zip(paths, datas):
        nspans += len(C.parse_dialogue(d) if root[p].get("kind", "srt") == "srt"
                      else C.parse_info_segments(d))
    d_parse = t() - t0

    # (3) quadratic header surgery, as the current code does it
    hdr0 = bytes(buf[:0x13706000])
    o4 = 0x900
    t0 = t()
    h = hdr0
    for k in range(HDR_PATCH):
        o = o4 + k * 16
        h = h[:o] + (k).to_bytes(4, "big") + h[o + 4:]
    d_immutable = t() - t0

    # same number of patches done in place on a bytearray
    t0 = t()
    ba = bytearray(hdr0)
    for k in range(HDR_PATCH):
        o = o4 + k * 16
        ba[o:o + 4] = k.to_bytes(4, "big")
    d_mutable = t() - t0

    # (4) out = bytearray(hdr) copy
    t0 = t()
    _ = bytearray(hdr0)
    d_copy = t() - t0

    n_files = len(root)
    n_pl = len(root) * 3          # 3 patched fields per relocated file

    rows = [
        (f"cpk.load (TOC only)", r["cpk.load (TOC only)"], 1, "always"),
        (f"ORIG.read_bytes -> bytearray", r["ORIG.read_bytes (326MB -> bytearray)"], 1, "always"),
        (f"file_bytes() decompress x{SAMPLE}", d_decomp, n_files / SAMPLE,
         f"projected for {n_files} overlay files"),
        (f"parse_dialogue/parse_info x{SAMPLE}", d_parse, n_files / SAMPLE,
         f"projected for {n_files} overlay files"),
        (f"header surgery, immutable bytes x{HDR_PATCH}", d_immutable, n_pl / HDR_PATCH,
         f"projected for {n_pl} field patches  <-- QUADRATIC"),
        (f"header surgery, bytearray x{HDR_PATCH}", d_mutable, n_pl / HDR_PATCH,
         "same work, done in place"),
        (f"out = bytearray(hdr) copy", d_copy, 1, "once"),
    ]
    out = ["phase", "-" * 78]
    tot_imm = tot_fix = 0.0
    for name, dt, mult, note in rows:
        proj = dt * mult
        tot_imm += proj if "immutable" in name or "copy" in name else 0
        tot_fix += proj if "bytearray x" in name or "copy" in name else 0
        out.append(f"{name:46s} {dt*1000:9.1f} ms  x{mult:7.1f} = {proj:8.2f} s   {note}")
    out.append("-" * 78)
    out.append(f"quadratic header phase as written : {tot_imm:8.2f} s")
    out.append(f"same phase in-place               : {tot_fix:8.2f} s")
    out.append(f"speed-up just from that fix       : {tot_imm/max(1e-6,tot_fix):8.0f}x")
    out.append(f"segment bytes touched by sample   : "
               f"{sum(len(d) for d in datas)} bytes / {SAMPLE} files")
    txt = "\n".join(out)
    print(txt)
    (C.WORK / "profile.txt").write_text(txt, encoding="utf-8")


if __name__ == "__main__":
    main()
