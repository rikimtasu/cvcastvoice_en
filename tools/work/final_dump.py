#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final: (1) correctly decode trust labels (they are UTF-8, not cp932), (2) hexdump
the save header + the changed regions so we can see whether the save is a TLV keyed
stream or positional. Prints to UTF-8 file for clean JP.
"""
import os
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_final.txt")
SAVE = r"D:\Video_Game\Emulator\RPCS3\dev_hdd0\home\00000001\savedata\NPJB00558-GAMEDATA-\GAMEDATA"


def dec_utf8_then_cp932(b):
    # try utf-8 first, then cp932
    for enc in ("utf-8", "cp932"):
        try:
            return b.decode(enc)
        except Exception:
            continue
    return b.decode("latin-1", "replace")


def main():
    img = Image(ELF)
    with open(OUT, "w", encoding="utf-8") as f:
        def w(*a):
            f.write(" ".join(str(x) for x in a) + "\n")

        w("=== TRUST-REWARD LABELS (correct decode) ===")
        for base in (0x23d940, 0x23d960, 0x23d980, 0x23da00, 0x23da20,
                     0x23da40, 0x23da60, 0x23db44, 0x23db54):
            raw = img.read_at_v(base, 32)
            raw = raw.split(b"\x00")[0]
            w("  0x%08x  %s" % (base, dec_utf8_then_cp932(raw)))

        w("\n=== SAVE hexdump (header 0x000-0x080) ===")
        if os.path.exists(SAVE):
            data = open(SAVE, "rb").read()
            for r in range(0, 0x80, 16):
                hexs = " ".join("%02x" % data[r + k] for k in range(16))
                asc = "".join(chr(data[r + k]) if 32 <= data[r + k] < 127 else "." for k in range(16))
                w("  0x%04x: %s  |%s|" % (r, hexs, asc))

            w("\n=== SAVE region 0x140-0x150 (cleared counter) ===")
            for r in range(0x140, 0x160, 16):
                hexs = " ".join("%02x" % data[r + k] for k in range(16))
                w("  0x%04x: %s" % (r, hexs))

            w("\n=== SAVE region 0x3e00-0x3fc0 (serialized tail) ===")
            for r in range(0x3e00, 0x3fc0, 16):
                hexs = " ".join("%02x" % data[r + k] for k in range(16))
                w("  0x%04x: %s" % (r, hexs))

            # entropy of each 512B block to find where structured data lives
            w("\n=== nonzero-byte ratio per 256B block ===")
            for base in range(0, len(data), 256):
                blk = data[base:base + 256]
                nz = sum(1 for x in blk if x != 0)
                if nz:
                    w("  0x%04x: %d/256 nonzero" % (base, nz))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
