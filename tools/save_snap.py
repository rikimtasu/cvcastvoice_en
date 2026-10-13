#!/usr/bin/env python3
"""Snapshot + diff RPCS3 savedata for the 1-script evidence run.

Stores snapshots BESIDE the live save (outside the repo, never committed):
  <savedir>/GAMEDATA.snap.<TAG> / OPTION.snap.<TAG>

Usage:
  python tools/save_snap.py snapshot --tag BEFORE   # close game+RPCS3 first
  ... play: clear exactly 1 script, Option -> Save, close game+RPCS3 ...
  python tools/save_snap.py snapshot --tag AFTER
  python tools/save_snap.py diff --a BEFORE --b AFTER
  python tools/save_snap.py list
"""
import argparse
import os
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C

RPCS3 = Path(os.environ["CVC_RPCS3"]).expanduser() \
    if os.environ.get("CVC_RPCS3") else Path(r"D:\Video_Game\Emulator\RPCS3")
SAVEDIR = RPCS3 / "dev_hdd0" / "home" / "00000001" / "savedata" / "NPJB00558-GAMEDATA-"
LEN_G, LEN_O = 19904, 2560


def _snap_path(name, tag):
    return SAVEDIR / f"{name}.snap.{tag}"


def cmd_snapshot(tag):
    for name, ln in (("GAMEDATA", LEN_G), ("OPTION", LEN_O)):
        src = SAVEDIR / name
        d = src.read_bytes()
        assert len(d) == ln, f"{name} len {len(d)} != {ln}"
        dst = _snap_path(name, tag)
        dst.write_bytes(d)
        print(f"snapshot {name} ({len(d)} B) -> {dst.name}")


def cmd_list():
    print(f"saves @ {SAVEDIR}")
    for p in sorted(SAVEDIR.glob("*.snap.*")):
        print(f"  {p.name} {p.stat().st_size} B")


def _diff_bytes(a: bytes, b: bytes, label: str):
    assert len(a) == len(b), f"{label} len {len(a)} != {len(b)}"
    # group into changed ranges
    ranges = []
    i = 0
    n = len(a)
    while i < n:
        if a[i] != b[i]:
            j = i
            while j < n and a[j] != b[j]:
                j += 1
            ranges.append((i, j))
            i = j
        else:
            i += 1
    print(f"== {label} len={n} changed_ranges={len(ranges)} ==")
    if not ranges:
        print("  identical")
        return
    for s, e in ranges[:40]:
        ln = e - s
        # u32be view at aligned start
        a0 = s - (s % 4)
        print(f"  @{s:#06x}-@{e-1:#06x} len={ln}")
        # dump 4B-aligned u32be before->after for the range (+1 word context)
        for o in range(a0 - 4, e + 4, 4):
            if o < 0 or o + 4 > n:
                continue
            wa = struct.unpack(">I", a[o:o+4])[0]
            wb = struct.unpack(">I", b[o:o+4])[0]
            if wa != wb:
                print(f"    u32 @{o:#06x}: {wa:#010x} ({wa}) -> {wb:#010x} ({wb})")
        # raw hex (first 64B of range)
        seg = e - s
        show = min(seg, 64)
        print(f"    A: {a[s:s+show].hex()}")
        print(f"    B: {b[s:s+show].hex()}")
    if len(ranges) > 40:
        print(f"  ... and {len(ranges)-40} more ranges")
    # totals
    print(f"  total changed bytes: {sum(e-s for s, e in ranges)}")


def cmd_diff(tag_a, tag_b):
    for name in ("GAMEDATA", "OPTION"):
        pa, pb = _snap_path(name, tag_a), _snap_path(name, tag_b)
        if not pa.exists() or not pb.exists():
            print(f"missing snapshot for {name}: {pa.name} / {pb.name}")
            continue
        _diff_bytes(pa.read_bytes(), pb.read_bytes(), f"{name} {tag_a} -> {tag_b}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot")
    s.add_argument("--tag", required=True)
    d = sub.add_parser("diff")
    d.add_argument("--a", required=True)
    d.add_argument("--b", required=True)
    sub.add_parser("list")
    args = ap.parse_args()
    if not (SAVEDIR / "GAMEDATA").exists():
        print(f"missing {SAVEDIR / 'GAMEDATA'} (set CVC_RPCS3?)")
        return 1
    if args.cmd == "snapshot":
        cmd_snapshot(args.tag)
    elif args.cmd == "list":
        cmd_list()
    elif args.cmd == "diff":
        cmd_diff(args.a, args.b)
    return 0


if __name__ == "__main__":
    sys.exit(main())
