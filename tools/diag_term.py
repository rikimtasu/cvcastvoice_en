#!/usr/bin/env python3
"""Find the true run terminator pattern and count runs correctly."""
import re, sys
from cricodecs import cpk

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
a = cpk.load(r"D:\Documents\CVCastingVoice\_backup\GameData.original.cpk")
tag = re.compile(rb"<~[0-9A-Za-z_]+>")
TERM = b"@n\xe2\x8a\xbf@n"     # @n + U+22BF + @n
ATN = b"@n"

stats = dict(files=0, runs=0, text_bytes=0, spilt_runs=0)
bad = []
info_runs = 0
samples = []
for f in a.files:
    lp = f.full_path.lower()
    if lp.endswith(".srt"):
        d = a.file_bytes(f.toc_index)
        if d[:4] != b"FSRT":
            continue
        stats["files"] += 1
        for m in tag.finditer(d):
            p = m.end()
            if d[p:p + 2] != ATN:
                stats["spilt_runs"] += 1
                continue
            t = d.find(TERM, p + 2)
            if t < 0:
                bad.append((f.full_path, m.group(), hex(m.start())))
                continue
            e = t + 2                      # end of the trailing @n before the token
            s = p + 2
            stats["runs"] += 1
            stats["text_bytes"] += e - s
            if len(samples) < 3:
                samples.append((f.full_path, m.group().decode(), s, e,
                                d[s:e].decode("utf-8", "replace")))
    elif lp.endswith(".info"):
        d = a.file_bytes(f.toc_index)
        n = d.count(b"\x0d\x0a")
        info_runs += n

print(stats)
print("info files CRLF total:", info_runs)
print("no-terminator runs:", len(bad), bad[:8])
for s in samples:
    print(f"  {s[0]} {s[1]} [{s[2]},{s[3]}) len={s[3]-s[2]} :: {s[4][:70]!r}")

# where the 0d0a lives
d = a.file_bytes(next(f.toc_index for f in a.files if f.full_path.endswith("D000_serif.info")))
print("\nD000_serif.info len", len(d), "CRLF", d.count(b"\x0d\x0a"))
i = d.find(b"\r\n".replace(b"\r\n", b"\x0d\x0a"))
print("first CRLF at", hex(i) if i >= 0 else None)
# print a window around it
if i >= 0:
    w = d[i - 40:i + 60]
    print(w.hex())
    print(repr(w))
