#!/usr/bin/env python3
"""sakuhin PAC record layout: find fixed-size entries + small-int gates.

sakuhin001.pac head shows repeating 0x?? patterns; entries look fixed-size.
Goal: record size, field map, any rank/trust/category/threshold ints.
"""
import struct
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

a = cpk.load(str(C.ORIG))
by = {f.full_path: f for f in a.files}
d = a.file_bytes(by["DATA/sakuhin/sakuhin001.pac"].toc_index)
print(f"sakuhin001 len={len(d)}")

# header: PACK + u32s
print("head u32le:", [struct.unpack("<I", d[i:i+4])[0] for i in range(0, 32, 4)])
print("head u32be:", [struct.unpack(">I", d[i:i+4])[0] for i in range(0, 32, 4)])

# find repeating marker: the head had 2a804000 d0124100 ... try record stride via autocorr
# Look for the most common 4B pattern (record separator?)
c4 = Counter()
for i in range(0, len(d) - 4, 1):
    c4[d[i:i+4]] += 1
print("-- top byte-4grams --")
for k, n in c4.most_common(12):
    print(f"  {k.hex()} x{n}")

# u16le histogram: small values = ids/thresholds/ranks?
cu = Counter(struct.unpack("<%dH" % (len(d)//2), d[:len(d)//2*2]))
small = sorted((v, n) for v, n in cu.items() if v < 300)
print(f"-- u16le values <300: {len(small)} distinct --")
print("  ", small[:60])
