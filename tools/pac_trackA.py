#!/usr/bin/env python3
"""
Build a Track-A overlay for the two .pac name DBs from a translation map, then
build the patched CPK via the proven surgical patcher.

Replacement model (verified safe):
  * Each name/title occupies [off, off+slot) where slot is the distance to the
    next NUL-separated segment (== byte length of the JP string + 1 for the
    single NUL terminator, for variable-length slots).
  * We replace that whole slot with `English + NUL` padding to EXACTLY slot
    bytes, so every later record stays at its original offset and the file's
    internal length fields never change.
  * Zero absolute offsets reference these strings (verified), so nothing else
    needs patching.

Input: work/pac_en.json  = { "jp string": "english", ... }   (optional per file)
If a jp string is missing or the english is too long, it is skipped + reported.

Usage:
  pac_trackA.py report              # show coverage/budget, no build
  pac_trackA.py build --out FILE    # write overlay + build + verify
"""
import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C

PACS = ("DATA/daihon/daihonbase.pac", "DATA/daihon/seiyubase.pac")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["report", "build"])
    ap.add_argument("--out")
    ap.add_argument("--deep", action="store_true")
    a = ap.parse_args()

    detail = json.loads((C.WORK / "pac_names_detail.json")
                        .read_bytes().decode("utf-8"))
    enmap_path = C.WORK / "pac_en.json"
    enmap = {}
    if enmap_path.exists():
        enmap = json.loads(enmap_path.read_bytes().decode("utf-8-sig"))

    overlay_files = {}
    n_hit = n_miss = n_long = 0
    long_report = []
    for p in PACS:
        runs = []
        for r in detail.get(p, []):
            jp = r["str"]
            if jp not in enmap:
                n_miss += 1
                continue
            en = enmap[jp]
            if en is None:
                n_miss += 1
                continue
            # keep newlines for multi-line bios but strip @n collisions
            en = en.replace("@n", " ")
            off = r["off"]
            # Writable region = the name bytes [off, off+blen) plus the
            # contiguous NUL padding that ends at nul_end. We NEVER write past
            # nul_end, so any following control bytes (font/width metadata)
            # are preserved byte-for-byte.
            end = r["nul_end"]
            slot = end - off            # == blen + (#trailing NUL bytes)
            eb = en.encode("utf-8")
            if len(eb) > slot:
                n_long += 1
                long_report.append((slot, len(eb), jp[:24], en[:30]))
                continue
            n_hit += 1
            runs.append({"span": [off, end], "text": en, "pad": "\x00"})
        if runs:
            overlay_files[p] = {"kind": "pac", "runs": runs}

    msg = [
        "=== Track A: .pac name/CV translation ===",
        f"translation map entries : {len(enmap)}",
        f"slots covered           : {n_hit}",
        f"strings w/o translation : {n_miss} (left Japanese)",
        f"over budget (skipped)   : {n_long}",
        f"files touched           : {len(overlay_files)}",
    ]
    if long_report:
        msg.append("  over-budget (need shorter EN):")
        for slot, need, jp, en in long_report[:20]:
            msg.append(f"    {need}>{slot}B  {jp!r} -> {en!r}")
    print("\n".join(msg))

    if a.mode == "report" or not a.out:
        (C.WORK / "pac_trackA_report.txt").write_text("\n".join(msg), encoding="utf-8")
        return 0

    ov = C.WORK / "pac_overlay.json"
    # Merge with the existing dialogue overlay so one build carries BOTH.
    merged = dict(overlay_files)
    base_path = C.WORK / "overlay.json"
    if base_path.exists():
        base = json.loads(base_path.read_bytes().decode("utf-8-sig", "surrogatepass"))
        base_files = base.get("files", base) if isinstance(base, dict) else {}
        for k, v in base_files.items():
            merged.setdefault(k, v)
    ov.write_bytes(json.dumps({"files": merged}, ensure_ascii=False)
                   .encode("utf-8", "surrogatepass"))
    print(f"merged overlay -> {ov}  (total files: {len(merged)})")
    import subprocess
    r = subprocess.run([sys.executable, str(Path(__file__).with_name("cvpatch.py")),
                        "build", "--overlay", str(ov), "--out", a.out],
                       capture_output=True, text=True, encoding="utf-8")
    print(r.stdout); print(r.stderr)
    if r.returncode:
        sys.exit(r.returncode)
    v = subprocess.run([sys.executable, str(Path(__file__).with_name("cvpatch.py")),
                        "verify", "--file", a.out] + (["--deep"] if a.deep else []),
                       capture_output=True, text=True, encoding="utf-8")
    print(v.stdout)
    sys.exit(v.returncode)


if __name__ == "__main__":
    sys.exit(main())
