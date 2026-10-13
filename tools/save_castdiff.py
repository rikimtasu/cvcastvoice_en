#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CASTDATA.DAT before/after tool. Snapshots and diffs the LIVE casting file
(CASTDATA.DAT in CASTLIST-0/-1) plus GAMEDATA/OPTION for context.

Usage:
  python tools/save_castdiff.py snapshot --tag BEFORE
  python tools/save_castdiff.py snapshot --tag AFTER2
  python tools/save_castdiff.py diff --a BEFORE --b AFTER2
  python tools/save_castdiff.py list
"""
import glob
import os
import struct
import sys

SD = r"D:\Video_Game\Emulator\RPCS3\dev_hdd0\home\00000001\savedata"
GD = SD + r"\NPJB00558-GAMEDATA-"
# external store (survives RPCS3 cleanups of the savedata folder)
SNAPDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "tools", "work", "snaps")
TARGETS = {
    "GAMEDATA": GD + r"\GAMEDATA",
    "OPTION": GD + r"\OPTION",
    "CAST0": glob.glob(SD + r"\NPJB00558-CASTLIST-0\CASTDATA.DAT")[0],
    "CAST1": glob.glob(SD + r"\NPJB00558-CASTLIST-1\CASTDATA.DAT")[0],
}


def snap_path(name, tag):
    d = os.path.join(SNAPDIR, tag)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, name + ".bin")


def cmd_snapshot(tag):
    for name, path in TARGETS.items():
        if not os.path.exists(path):
            print("MISSING", name, path)
            continue
        data = open(path, "rb").read()
        sp = snap_path(name, tag)
        with open(sp, "wb") as f:
            f.write(data)
        print("snapshot %-8s (%5d B) -> %s" % (name, len(data), os.path.basename(sp)))


def ranges(a, b):
    out = []
    n = min(len(a), len(b))
    i = 0
    while i < n:
        if a[i] != b[i]:
            j = i
            while j < n and a[j] != b[j]:
                j += 1
            out.append((i, j))
            i = j
        else:
            i += 1
    return out


def hexdump(d, lo, hi):
    for o in range(lo, hi, 16):
        chunk = d[o:o + 16]
        print("   %04x  %s" % (o, chunk.hex(" ")))


def cmd_diff(a, b):
    for name in TARGETS:
        pa, pb = snap_path(name, a), snap_path(name, b)
        if not (os.path.exists(pa) and os.path.exists(pb)):
            print("== %s ==  (missing snapshot)" % name)
            continue
        da, db = open(pa, "rb").read(), open(pb, "rb").read()
        rr = ranges(da, db)
        print("== %s  %s->%s  changed_ranges=%d ==" % (name, a, b, len(rr)))
        if not rr:
            print("   identical")
            continue
        for (s, e) in rr:
            print("   @0x%04x-0x%04x  before=%s  after=%s" %
                  (s, e - 1, da[s:e].hex(" "), db[s:e].hex(" ")))
        if name.startswith("CAST"):
            print("   before u32le:", [struct.unpack_from("<I", da, i)[0]
                                       for i in range(0, len(da) - 3, 4)])
            print("   after  u32le:", [struct.unpack_from("<I", db, i)[0]
                                       for i in range(0, len(db) - 3, 4)])


def cmd_list():
    if not os.path.isdir(SNAPDIR):
        print("(no snapshots yet at %s)" % SNAPDIR)
        return
    for tag in sorted(os.listdir(SNAPDIR)):
        full = os.path.join(SNAPDIR, tag)
        if not os.path.isdir(full):
            continue  # skip stray files like GAMEDATA.fabricated
        files = sorted(os.listdir(full))
        print("%-8s %s" % (tag, files))


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd == "snapshot" and len(argv) >= 4 and argv[2] == "--tag":
        cmd_snapshot(argv[3])
    elif cmd == "diff" and len(argv) >= 6:
        cmd_diff(argv[3], argv[5])
    elif cmd == "list":
        cmd_list()
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
