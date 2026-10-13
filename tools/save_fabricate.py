#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fabricate full Produce progress into GAMEDATA (EXPERIMENTAL / RISKY).

SAFETY MODEL (do not skip):
  * `fabricate` writes a SEPARATE GAMEDATA.fabricated file. It never touches
    the live save. Your real progress stays intact until you run `install`.
  * `install` auto-backups first, then applies the fabricated file.
  * `restore` rolls the live save back to any backup in one command.
  So worst case = the game dislikes the fabricated save; you `restore` and
  you're exactly where you are now.

Basis (two real scenario-clear diffs T0->T1->T2, no checksum anywhere):
  * record bank: 8-byte [counter][done-field]; done-field -> 0xFFFFFFFF on clear
        bank A @0x00c0..   mirror bank B @0x02a0..
  * cleared counter @0x0140 (mirror @0x0320); base total @0x0148 = 125
  * trust meters @0x1117, @0x117b  mirror +0x2a8 (@0x13bf, @0x1423)

Usage:
  python tools/save_fabricate.py backup
  python tools/save_fabricate.py fabricate [--level max|high] [--out PATH]
  python tools/save_fabricate.py verify
  python tools/save_fabricate.py install
  python tools/save_fabricate.py restore [--from TS]
  python tools/save_fabricate.py list
"""
import os
import shutil
import sys
import time
from collections import Counter

RPCS3 = os.environ.get("CVC_RPCS3", r"D:\Video_Game\Emulator\RPCS3")
SD = os.path.join(RPCS3, "dev_hdd0", "home", "00000001", "savedata")
GD_DIR = os.path.join(SD, "NPJB00558-GAMEDATA-")
LIVE_GD = os.path.join(GD_DIR, "GAMEDATA")
LIVE_OP = os.path.join(GD_DIR, "OPTION")
SNAP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "tools", "work", "snaps")
FAB_BAK = os.path.join(SNAP, "fab_backups")
FAB_GD = LIVE_GD + ".fabricated"
# prefer an external fabricated file (RPCS3 may clean unknown files in savedata)
FAB_GD_EXT = os.path.join(SNAP, "GAMEDATA.fabricated")
FAB_BAK = os.path.join(SNAP, "fab_backups")

LEN = 19904
TOTAL = 125  # 0x0148 base scenario total (constant, verified)

# done-field slots (4 bytes each) -> 0xFFFFFFFF, both banks
DONE = [0x00c4, 0x00e4, 0x0104, 0x02a4, 0x02c4, 0x02e4]
# cleared counter (u32 BE), both mirrors
CLEARED = [0x0140, 0x0320]
# trust-meter low bytes and their +0x2a8 mirrors -> 0xFF
TRUST = [0x1117, 0x117b]
TRUST_MIRROR = 0x2A8


def stamp():
    return time.strftime("%Y%m%d-%H%M%S")


def ensure_dirs():
    os.makedirs(FAB_BAK, exist_ok=True)


def read_live():
    if not os.path.exists(LIVE_GD):
        sys.exit("live GAMEDATA not found: %s" % LIVE_GD)
    return open(LIVE_GD, "rb").read()


def u32be(d, o):
    return (d[o] << 24) | (d[o + 1] << 16) | (d[o + 2] << 8) | d[o + 3]


def set_u32be(d, o, val):
    d[o] = (val >> 24) & 0xFF
    d[o + 1] = (val >> 16) & 0xFF
    d[o + 2] = (val >> 8) & 0xFF
    d[o + 3] = val & 0xFF


def fabricate(data, level="max"):
    d = bytearray(data)
    if len(d) != LEN:
        sys.exit("unexpected GAMEDATA length %d (expected %d)" % (len(d), LEN))
    changes = []
    cleared_val = TOTAL if level == "max" else max(1, TOTAL - 5)

    def wfill(off, val, n=1, why=""):
        for i in range(n):
            if d[off + i] != val:
                changes.append((off + i, d[off + i], val, why))
                d[off + i] = val

    # 1. mark every record-bank slot cleared (game's own done marker)
    for off in DONE:
        wfill(off, 0xFF, 4, "done-field")
    # 2. cleared counter -> total (both mirrors)
    for off in CLEARED:
        old = u32be(d, off)
        if old != cleared_val:
            for i in range(4):
                changes.append((off + i, d[off + i],
                                (cleared_val >> (24 - 8 * i)) & 0xFF, "cleared"))
            set_u32be(d, off, cleared_val)
    # 3. max trust meters (both mirrors)
    for off in TRUST:
        wfill(off, 0xFF, 1, "trust")
        m = off + TRUST_MIRROR
        wfill(m, 0xFF, 1, "trust-mirror")
    return bytes(d), changes


def cmd_backup():
    ensure_dirs()
    ts = stamp()
    dst = os.path.join(FAB_BAK, ts)
    os.makedirs(dst, exist_ok=True)
    for src in (LIVE_GD, LIVE_OP):
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dst, os.path.basename(src)))
    print("backup -> %s" % dst)
    return dst


def cmd_fabricate(level, out):
    data = read_live()
    fab, changes = fabricate(data, level)
    if out is None:
        out = FAB_GD_EXT
    with open(out, "wb") as f:
        f.write(fab)
    print("fabricated (level=%s) -> %s  (%d bytes, %d byte-changes)"
          % (level, out, len(fab), len(changes)))
    why = Counter(c[3] for c in changes)
    for k, v in sorted(why.items()):
        print("   %-14s %d bytes" % (k, v))
    return out


def fab_path():
    if os.path.exists(FAB_GD_EXT):
        return FAB_GD_EXT
    if os.path.exists(FAB_GD):
        return FAB_GD
    return None


def cmd_verify():
    fab_p = fab_path()
    if fab_p is None:
        sys.exit("no fabricated file yet; run `fabricate` first")
    live = read_live()
    fab = open(fab_p, "rb").read()
    if len(live) != len(fab):
        sys.exit("LENGTH MISMATCH live=%d fab=%d" % (len(live), len(fab)))
    diffs = [i for i in range(len(live)) if live[i] != fab[i]]
    print("verify: live=%d fab=%d changed_bytes=%d" % (len(live), len(fab), len(diffs)))
    for i in diffs:
        print("   @0x%04x  live=%02x  fab=%02x" % (i, live[i], fab[i]))


def cmd_install():
    fab_p = fab_path()
    if fab_p is None:
        sys.exit("no fabricated file yet; run `fabricate` first")
    cmd_backup()
    shutil.copy2(fab_p, LIVE_GD)
    print("INSTALLED fabricated (%s) -> %s" % (fab_p, LIVE_GD))
    print("restore with: python tools/save_fabricate.py restore --from <TS above>")


def cmd_restore(frm):
    ensure_dirs()
    if frm is None:
        subs = sorted(os.listdir(FAB_BAK))
        if not subs:
            sys.exit("no backups in %s" % FAB_BAK)
        frm = subs[-1]
    src = os.path.join(FAB_BAK, frm, "GAMEDATA")
    if not os.path.exists(src):
        sys.exit("backup GAMEDATA not found in %s" % frm)
    shutil.copy2(src, LIVE_GD)
    print("RESTORED live GAMEDATA from backup %s" % frm)


def cmd_list():
    ensure_dirs()
    subs = sorted(os.listdir(FAB_BAK))
    if not subs:
        print("(no backups)")
    for s in subs:
        p = os.path.join(FAB_BAK, s)
        files = sorted(os.listdir(p))
        print("%-20s %s" % (s, files))
    print("\nfabricated file present:", fab_path())


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd == "backup":
        cmd_backup()
    elif cmd == "fabricate":
        level = "max"
        out = None
        if "--level" in argv:
            level = argv[argv.index("--level") + 1]
        if "--out" in argv:
            out = argv[argv.index("--out") + 1]
        cmd_fabricate(level, out)
    elif cmd == "verify":
        cmd_verify()
    elif cmd == "install":
        cmd_install()
    elif cmd == "restore":
        frm = None
        if "--from" in argv:
            frm = argv[argv.index("--from") + 1]
        cmd_restore(frm)
    elif cmd == "list":
        cmd_list()
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

