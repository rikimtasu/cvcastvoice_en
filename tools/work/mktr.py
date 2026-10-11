#!/usr/bin/env python3
"""Build tr_bNNNN.json from a plain-text translation file.

Input file: work/tr/bNNNN.txt
  one entry per line:  <id>|<english>
  Blank lines and lines starting with '#' are ignored.
  A trailing '|...' is not supported; if the English itself needs a literal
  '|' character, use '\\u007c'.

Usage: mktr.py NNNN [check|write]
  check (default) - validate only
  write           - write work/tr_bNNNN.json
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
WORK = Path(__file__).resolve().parent


def main(argv):
    b = int(argv[1])
    mode = argv[2] if len(argv) > 2 else "check"
    src_path = WORK / "batches" / f"batch_{b:04d}.json"
    txt_path = WORK / "tr" / f"b{b:04d}.txt"
    batch = json.loads(src_path.read_bytes().decode("utf-8", "surrogatepass"))

    if not txt_path.exists():
        print(f"NO INPUT: {txt_path}")
        return 2

    T = {}
    dupes = []
    for raw in txt_path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip("\r")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "|" not in line:
            print(f"BAD LINE (no |): {line[:60]!r}")
            return 1
        i, en = line.split("|", 1)
        i = i.strip()
        en = en.replace("\\u007c", "|")
        if i in T:
            dupes.append(i)
        T[i] = en

    if dupes:
        print("DUPLICATE ids:", sorted(dupes))
        return 1

    missing = sorted(set(batch) - set(T), key=int)
    extra = sorted(set(T) - set(batch), key=int)
    over = []
    nonascii = []
    for k, en in T.items():
        try:
            en.encode("ascii")
        except UnicodeEncodeError:
            nonascii.append(k)
        if k in batch:
            bb, n = batch[k]["b"], len(en.encode("utf-8"))
            if n > bb:
                over.append((k, bb, n, en))

    print(f"batch {b}: batch={len(batch)} txt={len(T)}")
    if missing:
        print("  MISSING ids:", missing)
    if extra:
        print("  EXTRA ids:", extra)
    if nonascii:
        print("  NON-ASCII ids:", nonascii)
    if over:
        print("  OVER BUDGET:")
        for k, bb, n, en in over:
            print(f"    {k}: {n} > {bb}  {en!r}")

    if missing or extra or over or nonascii:
        return 1

    if mode == "write":
        out_path = WORK / f"tr_b{b:04d}.json"
        out_path.write_bytes(json.dumps(T, ensure_ascii=False,
                                        separators=(",", ":"))
                             .encode("utf-8", "surrogatepass"))
        mx = max(len(v.encode("utf-8")) for v in T.values())
        bud = max(v["b"] for v in batch.values())
        print(f"  WROTE {out_path}  entries={len(T)}  max_used={mx}/{bud}")
    else:
        mx = max(len(v.encode("utf-8")) for v in T.values())
        bud = max(v["b"] for v in batch.values())
        print(f"  OK (check only)  max_used={mx}/{bud}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
