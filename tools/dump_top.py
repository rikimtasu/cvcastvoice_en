#!/usr/bin/env python3
"""Dump the first N batch entries to a readable UTF-8 file."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C

n = int(sys.argv[1]) if len(sys.argv) > 1 else 60
src = {}
for bi in range((n + BATCH - 1) // BATCH if (BATCH := 120) else 1):
    p = C.WORK / "batches" / f"batch_{bi:04d}.json"
    if p.exists():
        src.update(json.loads(p.read_bytes().decode("utf-8", "surrogatepass")))
lines = []
for k, v in sorted(src.items(), key=lambda kv: int(kv[0]))[:n]:
    lines.append(f"{int(k):5d}  b={v['b']:3d}  c={v['c']:5d}  {v['jp']}")
(C.WORK / "top.txt").write_bytes("\n".join(lines).encode("utf-8", "surrogatepass"))
print(f"wrote {len(lines)} lines to work/top.txt")
