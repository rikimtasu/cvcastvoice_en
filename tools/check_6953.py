#!/usr/bin/env python3
"""Check segment 6953 raw bytes: does it really read ふみゆき?"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk


def main():
    order = json.loads((C.WORK / "order.json")
                       .read_bytes().decode("utf-8-sig", "surrogatepass"))
    v = order["6953"]
    print(f"b={v['b']} c={v['c']}")
    print("order jp:", " ".join(f"U+{ord(c):04X}" for c in v["jp"][:40]))
    # find the segment in the archive and dump raw bytes
    seg = json.loads((C.WORK / "segments.json")
                     .read_bytes().decode("utf-8-sig", "surrogatepass"))
    a = cpk.load(str(C.ORIG))
    by = {f.full_path: f for f in a.files}
    for path, rec in seg.items():
        for s in rec["seg"]:
            if s["jp"] == v["jp"]:
                d = a.file_bytes(by[path].toc_index)
                raw = d[s["s"]:s["e"]]
                print(path, s["s"], s["e"])
                print("raw:", raw.hex(" "))
                print("decoded:", raw.decode("utf-8", "replace"))
                return


if __name__ == "__main__":
    main()
