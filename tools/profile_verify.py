#!/usr/bin/env python3
"""Time the individual costs inside cmd_verify."""
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

t = time.perf_counter
r = []

ROOT = C.ROOT

t0 = t()
a = cpk.load(str(ROOT / "out" / "GameData_en.cpk"))
b = cpk.load(str(C.ORIG))
r.append(("cpk.load x2", t() - t0))

t0 = t()
na = (ROOT / "out" / "GameData_en.cpk").read_bytes()
nb = C.ORIG.read_bytes()
r.append(("read_bytes x2 (340+326 MB)", t() - t0))

N = len(a.files)
t0 = t()
_ = [(f.file_offset, f.file_size, f.extract_size, f.full_path, f.toc_index)
     for f in a.files]
_ = [(f.file_offset, f.file_size, f.extract_size, f.full_path, f.toc_index)
     for f in b.files]
r.append((f"attribute access x{2*N}", t() - t0))

t0 = t()
s = 0
for f in a.files:
    s += len(na[f.file_offset:f.file_offset + f.file_size])
r.append((f"raw slice-compare x{N}", t() - t0))

# what does one file_bytes() cost, on relocated (raw-stored) vs original?
t0 = t()
for f in a.files[:400]:
    a.file_bytes(f.toc_index)
r.append(("a.file_bytes x400 (patched, raw-stored)", t() - t0))

t0 = t()
for f in b.files[:400]:
    b.file_bytes(f.toc_index)
r.append(("b.file_bytes x400 (original, compressed)", t() - t0))

out = []
for n, dt in r:
    out.append(f"{n:52s} {dt*1000:10.1f} ms")
txt = "\n".join(out)
print(txt)
(C.WORK / "profile_verify.txt").write_text(txt, encoding="utf-8")
