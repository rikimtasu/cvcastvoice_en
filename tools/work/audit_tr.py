#!/usr/bin/env python3
"""Audit tr_bNNNN.json against batches/batch_NNNN.json.

Usage: audit_tr.py [N ...]   # verify listed batches, exit 1 on any FAIL
       audit_tr.py           # full coverage sweep over 0..439
Checks: keys exactly equal; each EN <= byte budget b; ASCII-only;
no raw '@n'/'@i<'/'<~' tags; leading-space kept iff source starts U+3000;
bracket pairing for runs that open/close \" ( ) '.
Exit 0 iff every checked batch PASSes.
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
WORK = Path(__file__).resolve().parent

# The player-name variable tag @i<0> is on-screen text the engine substitutes;
# it ships verbatim in the original and in earlier tr files, so allow ONLY it.
ALLOW_TAG = "@i<0>"


def check(n):
    bpath = WORK / "batches" / f"batch_{n:04d}.json"
    tpath = WORK / ("tr_b%04d.json" % n)
    if not bpath.exists():
        return "NO-BATCH"
    if not tpath.exists():
        return "MISSING"
    try:
        b = json.loads(bpath.read_bytes().decode("utf-8", "surrogatepass"))
        t = json.loads(tpath.read_bytes().decode("utf-8", "surrogatepass"))
    except Exception as e:
        return f"BAD-JSON {e}"
    if set(t) != set(b):
        return f"KEYS {len(t)}vs{len(b)}"
    hard, warn = [], []
    for k, rec in b.items():
        en = t[k]
        bb = rec["b"]
        if len(en.encode("utf-8")) > bb:
            hard.append((k, "over"))
        probe = en.replace(ALLOW_TAG, "")
        if any(c in probe for c in ("@n", "@i<", "<~")):
            hard.append((k, "tag"))
        if any(ord(c) > 127 for c in en):
            hard.append((k, "non-ascii"))
        want_lead = rec["jp"].startswith(chr(0x3000))
        if want_lead != en.startswith(" "):
            hard.append((k, "lead"))
        # brackets are a judgment call (lone fragments, dropped furigana):
        # report only, never fail
        if ("「" in rec["jp"] or "」" in rec["jp"]) != ('"' in en):
            warn.append((k, "quote"))
        if ("（" in rec["jp"]) != ("(" in en):
            warn.append((k, "open-paren"))
        if ("）" in rec["jp"]) != (")" in en):
            warn.append((k, "close-paren"))
    if hard:
        return f"FAIL {hard[:6]}"
    if warn:
        return f"PASS-warn {warn[:6]}"
    return "PASS"


def main():
    if len(sys.argv) > 1:
        ns = [int(x) for x in sys.argv[1:]]
        ok = True
        for n in ns:
            r = check(n)
            print(f"batch_{n:04d}: {r}")
            ok = ok and r.startswith("PASS")
        sys.exit(0 if ok else 1)
    # full sweep: batch covered if tr_b PASSes, or ids covered by tr_batch0/mine
    mine = {}
    for f in ("tr_batch0.json", "tr_mine060_239.json"):
        p = WORK / f
        if p.exists():
            mine.update(json.loads(p.read_bytes().decode("utf-8", "surrogatepass")))
    missing, partial = [], []
    for n in range(440):
        r = check(n)
        if r == "PASS":
            continue
        b = json.loads((WORK / "batches" / f"batch_{n:04d}.json")
                       .read_bytes().decode("utf-8", "surrogatepass"))
        uncovered = [k for k in b if k not in mine]
        if not uncovered:
            continue  # fully covered via batch0/mine
        (partial if r not in ("MISSING", "NO-BATCH") else missing).append(n)
    print(f"MISSING tr_b (uncovered): {missing}")
    print(f"PARTIAL/FAIL tr_b: {partial}")


if __name__ == "__main__":
    main()
