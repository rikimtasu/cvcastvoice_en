#!/usr/bin/env python3
"""Probe DLC CPK layout constants (do they match the base-game format?)."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

DLC = C.ROOT / "dlc" / "dec"


def main():
    for name in sorted(p.name for p in DLC.glob("DLC_*.cpk")):
        p = DLC / name
        b = p.read_bytes()
        a = cpk.load(str(p))
        n = len(a.files)
        utf = b[C.ROW0 - 0x3F:C.ROW0 + 8] if len(b) > C.ROW0 else b""
        etoc = int.from_bytes(b[C.INFO_ETOC_OFF:C.INFO_ETOC_OFF + 8], "big")
        etoc_size = int.from_bytes(b[C.INFO_ETOC_SIZE:C.INFO_ETOC_SIZE + 8],
                                   "big")
        data_size = int.from_bytes(b[C.INFO_DATA_SIZE:C.INFO_DATA_SIZE + 8],
                                   "big")
        content = int.from_bytes(
            b[C.INFO_CONTENT_OFF:C.INFO_CONTENT_OFF + 8], "big")
        # col0 chain check on first/last rows
        def col(buf, i, k):
            o = C.ROW0 + i * C.STRIDE + 4 * k
            return int.from_bytes(buf[o:o + 4], "big")
        ok0 = (col(b, 1, 0) + 2048 == a.files[0].file_offset)
        last = n - 1
        okl = (col(b, last, 0) + 2048 == a.files[last - 1].file_offset)
        inv = (len(b) == content + data_size + etoc_size and
               content + data_size == etoc and etoc + etoc_size == len(b))
        print(f"{name}: files={n} size={len(b)} etoc={etoc:#x} "
              f"col0chain[1]={ok0} col0chain[last]={okl} invariant={inv}")


if __name__ == "__main__":
    main()
