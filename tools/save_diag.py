#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnostic: compare CASTLIST slots, show mtimes, confirm snapshot identity."""
import glob
import os
import struct

SD = r"D:\Video_Game\Emulator\RPCS3\dev_hdd0\home\00000001\savedata"
GD = SD + r"\NPJB00558-GAMEDATA-"


def cast_slots():
    print("== CASTDATA.DAT slot comparison ==")
    slots = sorted(glob.glob(SD + r"\*CASTLIST*\CASTDATA.DAT"))
    datas = []
    for s in slots:
        d = open(s, "rb").read()
        datas.append((s, d))
        u32 = [struct.unpack_from("<I", d, i)[0] for i in range(0, len(d) - 3, 4)]
        print(os.path.basename(os.path.dirname(s)), "u32:", u32)
    if len(datas) == 2 and datas[0][1] == datas[1][1]:
        print("  -> slot0 == slot1 (identical)")
    elif len(datas) == 2:
        print("  -> slots DIFFER")


def mtimes():
    print("\n== file mtimes (save activity) ==")
    for f in sorted(glob.glob(GD + r"\*") + glob.glob(SD + r"\*CASTLIST*\CASTDATA.DAT")):
        try:
            st = os.stat(f)
            import time
            ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime))
            print("%-14s %8d  %s" % (os.path.basename(f), st.st_size, ts))
        except OSError as e:
            print(f, "ERR", e)


def confirm_identity():
    print("\n== GAMEDATA vs snapshots ==")
    live = open(GD + r"\GAMEDATA", "rb").read()
    for tag in ("BEFORE", "AFTER2"):
        p = GD + ("\\GAMEDATA.snap." + tag)
        if os.path.exists(p):
            same = open(p, "rb").read() == live
            print("GAMEDATA == snap.%s : %s" % (tag, same))


if __name__ == "__main__":
    cast_slots()
    mtimes()
    confirm_identity()
