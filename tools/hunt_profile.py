#!/usr/bin/env python3
"""Hunt the Mafuyu profile strings across EVERY archive (base + all DLC)."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

ROOT = C.ROOT
NEEDLES = ["帰り道に酔", "信頼度8でオープン", "香坂雪子", "まふまふ"]


def hunt(label, cpk_path):
    try:
        a = cpk.load(str(cpk_path))
    except Exception as e:
        print(f"{label}: cannot load ({e})")
        return
    fa = a.files
    for f in fa:
        try:
            d = a.file_bytes(f.toc_index)
        except Exception:
            continue
        for n in NEEDLES:
            nb = n.encode("utf-8")
            if nb in d:
                print(f"  [{label}] {f.full_path} :: {n!r}")


def main():
    hunt("BASE", C.ORIG)
    for p in sorted((ROOT / "dlc" / "dec").glob("DLC_*.cpk")):
        hunt(p.stem, p)


if __name__ == "__main__":
    main()
