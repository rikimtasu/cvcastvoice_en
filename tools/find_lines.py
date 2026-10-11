#!/usr/bin/env python3
"""Find which file(s) contain the dialogue shown in the screenshot, and prove
that our patched file (DATA/srt_dh/P001_01.srt) is reachable at its new offset."""
import os
import sys
from pathlib import Path

from cricodecs import cpk

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C

# Built archive to inspect (default: the current EN build; CVC_BUILT overrides).
INSTALLED = Path(os.environ["CVC_BUILT"]).expanduser() \
    if os.environ.get("CVC_BUILT") else C.ROOT / "out" / "GameData_en.cpk"
ORIG = C.ORIG
NEEDLES = [
    "\u5e72\u3093\u306a\u3080",                      # ばんなむ (speaker)
    "\u3064\u308f\u3041",                                     # ふわぁ
    "\u65e9\u8d77\u304d\u3092\u3057\u3066\u304a\u304b\u306a\u3044\u3068",       # 早起きをしておかないと
    "\u751f\u6d3b\u306e\u30ea\u30ba\u30e0",                       # 生活のリズム
]
a = cpk.load(str(ORIG))          # pristine -> search corpus
b = cpk.load(str(INSTALLED))     # patched -> check patched file resolves

log = []


def p(*x):
    log.append(" ".join(str(v) for v in x))


hits = {n: [] for n in NEEDLES}
for f in a.files:
    lp = f.full_path.lower()
    if not (lp.endswith(".srt") or lp.endswith(".info")):
        continue
    try:
        d = a.file_bytes(f.toc_index)
    except Exception:
        continue
    txt = d.decode("utf-8", "replace")
    for n in NEEDLES:
        if n in txt:
            hits[n].append(f.full_path)

for n, v in hits.items():
    p(f"{n!r}: {len(v)} file(s)")
    for path in v[:8]:
        p(f"    {path}")

p()
p("=== is the patched file's dialogue still resolvable in the patched archive? ===")
bytoc_b = {f.full_path: f for f in b.files}
tgt = "DATA/srt_dh/P001_01.srt"
fb = bytoc_b[tgt]
p(f"{tgt}: patched offset={fb.file_offset:#x} size={fb.file_size} "
  f"extract={fb.extract_size} compressed={fb.is_compressed}")
d = b.file_bytes(fb.toc_index)
p(f"  extracted {len(d)} bytes; first run bytes now: {d[278:311]!r}")
p(f"  contains FSRT magic: {d[:4] == b'FSRT'}")
p(f"  contains our [000] filler: {b'[000]' in d}")

p()
p("=== offsets of the two files around the patched one (proves col0 chain intact) ===")
o_by = {f.toc_index: f for f in b.files}
n_by = {f.toc_index: f for f in a.files}
for ti in (308, 309, 310, 311, 312):
    f1, f0 = o_by[ti], n_by[ti]
    flag = "  <== PATCHED (relocated)" if ti == 310 else ""
    p(f"  toc[{ti}] {f1.full_path}")
    p(f"      patched offset={f1.file_offset:#x}  orig={f0.file_offset:#x}{flag}")

Path(Path(__file__).resolve().parent / "work" / "probe_lines.txt").write_text(
    "\n".join(log), encoding="utf-8")
print("\n".join(log))
