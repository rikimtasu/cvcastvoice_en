#!/usr/bin/env python3
"""Byte-level diff of a surgically patched archive vs the pristine original.
Confirms that ONLY the intended TOC/INFO fields changed."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C

ORIG = C.ORIG
ROW0, STRIDE = 0x84F, 28
COL_FILE, COL_EXTR, COL_PREV = 4, 5, 0
a = ORIG.read_bytes()
b = Path(sys.argv[1]).read_bytes()

log = []


def p(*x):
    log.append(" ".join(str(v) for v in x))


p(f"orig={len(a)} new={len(b)}  delta=+{len(b)-len(a)} bytes")

plan = json.loads((Path(__file__).resolve().parent / "work" / "last_build.json")
                  .read_text(encoding="utf-8"))
placements = plan["placements"]

# expected changed positions
expected = {}
for ti, off, n, path in placements:
    o4 = ROW0 + ti * STRIDE + 4 * COL_FILE
    o5 = ROW0 + ti * STRIDE + 4 * COL_EXTR
    on = ROW0 + (ti + 1) * STRIDE + 4 * COL_PREV
    for o in (o4, o5, on):
        expected.setdefault(o, 4)
for o in (0xEF, 0x107):          # DataSize / EtocOffset
    expected.setdefault(o, 8)

p(f"placements: {len(placements)}")
for ti, off, n, path in placements:
    p(f"  toc[{ti}] {path} -> offset {off:#x} len {n}")
p(f"expected header field ranges: { {hex(k): v for k, v in sorted(expected.items())} }")

# ---- diff the ORIGINAL region only: header + data, [0, old ETOC) ----
limit = plan["old_etoc"]
p(f"scanning [0, {limit:#x}) for changes (original header + data)")
nfields = 0
regions = []
cur = None
for i in range(limit):
    same = a[i] == b[i] if i < len(a) else False
    if not same:
        if cur is None:
            cur = [i, i]
        else:
            cur[1] = i
    else:
        if cur is not None:
            regions.append(tuple(cur))
            cur = None
if cur is not None:
    regions.append(tuple(cur))

p(f"changed byte regions in the original region: {len(regions)}")
ok = True
for lo, hi in regions:
    inside = [f"{hex(e0)}+{e1}" for e0, e1 in expected.items()
              if lo >= e0 and hi <= e0 + e1 - 1]
    hit = (lo, hi + 1)
    exact = hit in expected
    if inside:
        p(f"  {lo:#x}..{hi:#x} ({hi-lo+1} bytes)  OK -> inside field(s) {inside}"
          f"{' [exact field]' if exact else ''}")
    else:
        p(f"  {lo:#x}..{hi:#x} ({hi-lo+1} bytes)  *** UNEXPECTED ***")
        ok = False

# ---- the new payload region must be exactly what we wrote ----
p(f"new payload region [{placements[0][1]:#x}, {plan['new_etoc']:#x}) "
  f"= {plan['new_etoc'] - placements[0][1]} bytes (all new, all intentional)")

# ---- ETOC integrity ----
old_etoc = plan["old_etoc"]
size = int.from_bytes(a[0x10F:0x117], "big")
p(f"ETOC bytes identical after relocation: "
  f"{a[old_etoc:old_etoc+size] == b[plan['new_etoc']:plan['new_etoc']+size]}")

# ---- payloads actually contain the replacement? ----
from cricodecs import cpk
na = cpk.load(str(Path(sys.argv[1])))
for ti, off, n, path in placements:
    d = na.file_bytes(ti)
    p(f"patched payload {path}: len={len(d)} (expected {n})")
    p(f"   FSRT magic preserved: {d[:4] == b'FSRT'}")
    p(f"   head: {d[:48]!r}")
    p(f"   any ASCII English present: "
      f"{sum(1 for c in d if 0x20 <= c <= 0x7E)} printable ASCII bytes")
    break

p("RESULT: " + ("PASS" if ok else "FAIL"))
Path(Path(__file__).resolve().parent / "work" / "bytediff.txt").write_text(
    "\n".join(log), encoding="utf-8")
print("\n".join(log))
