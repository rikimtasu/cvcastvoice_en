#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract scenario->cast mapping from GameData.cpk:

1. Every sakuhinNNN.pac: all `caNNN` character ids (OBNT cast block + others),
   plus JP title-like strings.
2. Every DNNN_serif.info: parse header for small-int arrays (candidate speaker ids).

Writes UTF-8 JSON + a human-readable txt so we can cross-check the two sources.
"""
import json
import re
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import cvpatch as C
from cricodecs import cpk

CA = re.compile(rb"ca(\d{3})")
JP = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")


def utf8ish_strings(d, minlen=3):
    out = []
    start = 0
    while True:
        i = d.find(b"\x00", start)
        chunk = d[start:i] if i >= 0 else d[start:]
        if len(chunk) >= minlen:
            try:
                t = chunk.decode("utf-8")
                if JP.search(t):
                    out.append((start, t))
            except UnicodeDecodeError:
                pass
        if i < 0:
            break
        start = i + 1
    return out


def main():
    a = cpk.load(str(C.ORIG))
    by = {f.full_path: f for f in a.files}

    result = {"sakuhin": {}, "serif": {}}

    # --- sakuhin PACs ---
    sak = sorted((p for p in by if re.match(r"DATA/sakuhin/sakuhin\d+\.pac$", p)),
                 key=lambda p: int(re.search(r"(\d+)", p).group(1)))
    print("sakuhin PACs: %d" % len(sak))
    for p in sak:
        n = int(re.search(r"(\d+)", p).group(1))
        d = a.file_bytes(by[p].toc_index)
        ids = sorted({int(m.group(1)) for m in CA.finditer(d)})
        strs = utf8ish_strings(d)
        titles = [(o, t) for o, t in strs if 2 <= len(t) <= 40]
        result["sakuhin"][n] = {
            "size": len(d),
            "cast": ["ca%03d" % i for i in ids],
            "cast_n": len(ids),
            "strings": [[o, t] for o, t in titles[:12]],
        }

    # --- serif.info ---
    ser = sorted((p for p in by if re.match(r"DATA/daihon/D\d+_serif\.info$", p)),
                 key=lambda p: int(re.search(r"D(\d+)", p).group(1)))
    print("serif.info: %d" % len(ser))
    for p in ser:
        n = int(re.search(r"D(\d+)", p).group(1))
        d = a.file_bytes(by[p].toc_index)
        # header: first 5 LE u32, then word-aligned small-int pairs (speaker?, type?)
        hdr = struct.unpack_from("<5I", d, 0)
        # collect u16 pairs where both < 200 (candidate id arrays)
        pairs = []
        for off in range(0x20, min(len(d) - 4, 0x200), 4):
            lo, hi = struct.unpack_from("<HH", d, off)
            if lo < 256 and hi < 256:
                pairs.append((off, lo, hi))
        result["serif"][n] = {
            "size": len(d),
            "hdr": list(hdr),
            "pairs_head": [[o, l, h] for o, l, h in pairs[:40]],
        }

    (C.WORK / "sakuhin_cast.json").write_bytes(
        json.dumps(result, ensure_ascii=False, indent=1).encode("utf-8"))

    # human readable summary
    lines = []
    lines.append("== sakuhin cast summary ==")
    for n, v in result["sakuhin"].items():
        lines.append("  sakuhin%03d  size=%-7d cast(%d): %s"
                     % (n, v["size"], v["cast_n"], " ".join(v["cast"])))
        for o, t in v["strings"][:4]:
            lines.append("        [%d] %s" % (o, t))
    lines.append("")
    lines.append("== serif header/pairs (head) ==")
    for n, v in list(result["serif"].items())[:6]:
        lines.append("  D%03d size=%d hdr=%s" % (n, v["size"], v["hdr"]))
        lines.append("      pairs: %s" % v["pairs_head"][:16])
    (C.WORK / "_sakuhin_cast.txt").write_text("\n".join(lines), encoding="utf-8")
    print("wrote sakuhin_cast.json + _sakuhin_cast.txt")


if __name__ == "__main__":
    main()
