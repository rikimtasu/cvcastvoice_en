#!/usr/bin/env python3
"""Force the leading-space rule on tr/bNNNN.txt from batches/batch_NNNN.json.

Usage: fixlead.py NNNN
Strips any leading ASCII space from the EN half, then re-adds exactly one
iff the JP source line starts with U+3000.
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
WORK = Path(__file__).resolve().parent


def main(argv):
    b = int(argv[1])
    batch = json.loads((WORK / "batches" / f"batch_{b:04d}.json")
                       .read_bytes().decode("utf-8", "surrogatepass"))
    p = WORK / "tr" / f"b{b:04d}.txt"
    out, seen = [], set()
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip("\r")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        i, en = line.split("|", 1)
        i = i.strip()
        if i not in batch:
            print("UNKNOWN id", i)
            return 1
        en = en.lstrip(" ")
        if batch[i]["jp"].startswith(chr(0x3000)):
            en = " " + en
        if i in seen:
            print("DUPE", i)
            return 1
        seen.add(i)
        out.append(i + "|" + en)
    miss = sorted(set(batch) - seen, key=int)
    if miss:
        print("MISSING:", miss)
        return 1
    p.write_bytes(("\r\n".join(out) + "\r\n").encode("utf-8"))
    print(f"fixed {p.name}: {len(out)} lines")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
