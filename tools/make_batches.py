#!/usr/bin/env python3
"""
Emit translation batches from work/segments.json.

Batches are ordered by FREQUENCY (most-repeated Japanese first) so translating
the first few batches covers the largest share of on-screen text.

Each entry carries:
  id    stable index into work/order.json
  jp    the Japanese source (already the on-screen unit)
  b     its byte budget in the archive
  c     how many times it occurs in the game

Output: work/batches/batch_NNNN.json   {id: {"jp":..., "b":..., "c":...}}
        work/order.json                {id: {"jp":..., "b":..., "c":...}}
        work/to_translate.json         {id: {"jp":..., "b":..., "c":...}}  (input)
        work/translated.json           {id: "english"}                      (output)
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C

BATCH = 120


def build_order():
    seg = json.loads((C.WORK / "segments.json")
                     .read_bytes().decode("utf-8-sig", "surrogatepass"))
    freq = {}
    budget = {}
    for rec in seg.values():
        for s in rec["seg"]:
            jp = s["jp"]
            freq[jp] = freq.get(jp, 0) + 1
            # a string may appear with different budgets; keep the largest
            budget[jp] = max(budget.get(jp, 0), s["b"])
    order = sorted(freq, key=lambda t: (-freq[t], -len(t)))
    out = {}
    for i, jp in enumerate(order):
        out[i] = {"jp": jp, "b": budget[jp], "c": freq[jp]}
    return out


def main():
    order = build_order()
    (C.WORK / "order.json").write_bytes(
        json.dumps(order, ensure_ascii=False).encode("utf-8", "surrogatepass"))
    bdir = C.WORK / "batches"
    bdir.mkdir(exist_ok=True)
    for old in bdir.glob("batch_*.json"):
        old.unlink()
    ids = list(range(len(order)))
    nb = (len(ids) + BATCH - 1) // BATCH
    for bi in range(nb):
        chunk = ids[bi * BATCH:(bi + 1) * BATCH]
        (bdir / f"batch_{bi:04d}.json").write_bytes(json.dumps(
            {i: order[i] for i in chunk}, ensure_ascii=False, indent=0)
            .encode("utf-8", "surrogatepass"))
    # input file the translator fills in
    (C.WORK / "to_translate.json").write_bytes(json.dumps(
        {i: order[i] for i in ids}, ensure_ascii=False, indent=0)
        .encode("utf-8", "surrogatepass"))
    # cumulative coverage
    tot = sum(order[i]["c"] for i in ids)
    marks = []
    for bi in (10, 50, 100, 200, 439):
        if bi > nb:
            break
        cov = sum(order[i]["c"] for i in ids[:bi * BATCH])
        marks.append(f"  after batch {bi:4d} ({bi*BATCH:6d} strings): "
                     f"{100*cov/tot:5.1f}% of segments")
    msg = [f"unique strings : {len(order)}",
           f"batch size     : {BATCH}",
           f"batches        : {nb}",
           "",
           "coverage by batch:",
           *marks]
    (C.WORK / "batches.txt").write_text("\n".join(msg), encoding="utf-8")
    print("\n".join(msg))


if __name__ == "__main__":
    main()
