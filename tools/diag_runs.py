#!/usr/bin/env python3
"""Diagnose what run forms exist across all .srt/.info text files."""
import re, sys
from pathlib import Path
from cricodecs import cpk

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
a = cpk.load(str(C.ORIG))

tag = re.compile(rb"<~([^>]*)>")
atn = re.compile(rb"@n")
ansi = re.compile(rb"\x0D\x0A")

stats = {"srt": 0, "info": 0, "pac": 0, "other": 0}
fsrt = taghits = atnhits = crlf = 0
bytaglen = {}
run_forms = {"tag+atn": 0, "tag_only": 0, "atn_only": 0}
samples = []
nfiles = 0
runs_found = 0
bytes_found = 0

for f in a.files:
    lp = f.full_path.lower()
    ext = lp.rsplit(".", 1)[-1]
    if ext == "srt":
        stats["srt"] += 1
    elif ext == "info":
        stats["info"] += 1
    elif ext == "pac":
        stats["pac"] += 1
    else:
        stats["other"] += 1
        continue
    if ext == "pac":
        continue
    nfiles += 1
    d = a.file_bytes(f.toc_index)
    if d[:4] == b"FSRT":
        fsrt += 1
        for m in tag.finditer(d):
            atnhits += 0
        tl = tag.findall(d)
        taghits += len(tl)
        for t in tl:
            bytaglen[len(t)] = bytaglen.get(len(t), 0) + 1
        an = len(atn.findall(d))
        atnhits += an
        # run detection
        n = 0
        for m in tag.finditer(d):
            p = m.end()
            if d[p:p + 2] == b"@n":
                e = d.find(b"@n", p + 2)
                if e > p + 2:
                    n += 1
                    bytes_found += e - (p + 2)
        run_forms["tag+atn"] += n
        runs_found += n
    else:
        samples.append((f.full_path, len(d), d[:16].hex()))

print("stats", stats, "fsrt", fsrt, "tags", taghits, "@n", atnhits)
print("runs_found", runs_found, "bytes", bytes_found, bytes_found / 1048576, "MiB")
print("tag name length histogram (top):", sorted(bytaglen.items())[:12])
print("non-FSRT samples:", samples[:12])
