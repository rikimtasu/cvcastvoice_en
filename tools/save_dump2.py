#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Full dumps of CASTDATA.DAT (40B casting table) and OPTION (2560B).
Read-only. Avoids PowerShell quoting by living in a file."""
import glob
import struct
import sys

SD = r"D:\Video_Game\Emulator\RPCS3\dev_hdd0\home\00000001\savedata"


def dump_castdata():
    files = glob.glob(SD + r"\*CASTLIST*\CASTDATA.DAT")
    print("== CASTDATA.DAT ==")
    print("FILES:", files)
    if not files:
        print("  (none found)")
        return
    d = open(files[0], "rb").read()
    print("len", len(d))
    print("hex", d.hex())
    print("bytes", list(d))
    print("u32le", [struct.unpack_from("<I", d, i)[0] for i in range(0, len(d) - 3, 4)])
    print("u16le", [struct.unpack_from("<H", d, i)[0] for i in range(0, len(d) - 1, 2)])
    # ascii preview
    print("ascii", "".join(chr(b) if 32 <= b < 127 else "." for b in d))


def dump_option():
    print("== OPTION (full) ==")
    try:
        d = open(SD + r"\NPJB00558-GAMEDATA-\OPTION", "rb").read()
    except OSError as e:
        print("  open failed:", e)
        return
    print("len", len(d))
    for i in range(0, len(d), 16):
        chunk = d[i:i + 16]
        hx = chunk.hex(" ")
        asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        print("%04x  %-47s  %s" % (i, hx, asc))


if __name__ == "__main__":
    dump_castdata()
    print()
    dump_option()
