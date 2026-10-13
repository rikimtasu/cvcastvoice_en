#!/usr/bin/env python3
"""GAMEDATA scenario-list writer (RPCS3 decrypted save) -- EVIDENCE-BASED.

Your Album count = 33 decimal = 0x21. Live save:
  @0x1358 u32be = 1        (list valid/generation?)
  @0x135C u32be = 125 (0x7D) (total slots?)
  @0x1360 u32be = 0
  @0x1364 u32be = 51 (0x33)  <- NOT your 33; 51 = ?? (chars? works?)
  @0x1368+ u32be = 7 x8      <- ?? (difficulties? categories?)
No field holds 33/0x21 -> the list is NOT a count I can bump.
This tool now: scan + set any u32 with backup/restore, so we test
candidates one at a time from YOUR feedback, not my guesses.
"""
import argparse
import os
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C

RPCS3 = Path(os.environ["CVC_RPCS3"]).expanduser() \
    if os.environ.get("CVC_RPCS3") else Path(r"D:\Video_Game\Emulator\RPCS3")
SAVEDIR = RPCS3 / "dev_hdd0" / "home" / "00000001" / "savedata" / "NPJB00558-GAMEDATA-"
OPTION = SAVEDIR / "OPTION"
EXPECT_LEN = 2560

# Hypothesis v1: 8-byte mode-unlock window at 0x1C-0x23.
# Current bytes: 00 00 00 01 | 00 01 00 00 (only 2 of 8 set).
# Full-Open should set the other 6 so all 8 modes read unlocked.
# Offsets to flip 00->01:
FULLOPEN_V1 = [0x1C, 0x1D, 0x1E, 0x20, 0x22, 0x23]


def backup() -> Path:
    d = OPTION.read_bytes()
    assert len(d) == EXPECT_LEN, f"OPTION len {len(d)} != {EXPECT_LEN}"
    stamp = time.strftime("%Y%m%d-%H%M%S")
    bak = SAVEDIR / f"OPTION.bak.{stamp}"
    bak.write_bytes(d)
    (SAVEDIR / "OPTION.bak.latest").write_bytes(d)
    print(f"backup {OPTION} ({len(d)} B) -> {bak.name} + OPTION.bak.latest")
    return bak


def scan():
    d = OPTION.read_bytes()
    print(f"OPTION {len(d)} B @ {OPTION}")
    print("header 0x00-0x2F:")
    for off in (0x00, 0x10, 0x20):
        chunk = d[off:off + 16]
        print(f"  @{off:04x}: {' '.join(f'{b:02x}' for b in chunk)}")
    cur = [(o, b) for o, b in enumerate(d[0x1C:0x24], start=0x1C)]
    print("flag window 0x1C-0x23 (v1 hypothesis):")
    for o, b in cur:
        mark = " <-- will set to 01" if o in FULLOPEN_V1 else " (already 01)"
        print(f"  @0x{o:04x} = {b:#04x}{mark if b != 1 or o in FULLOPEN_V1 else ''}")
    print("zero-gap summary (other candidate windows if v1 fails):")
    gaps = []
    i = 0
    while i < len(d):
        if d[i] == 0:
            j = i
            while j < len(d) and d[j] == 0:
                j += 1
            if j - i >= 16:
                gaps.append((i, j - i))
            i = j
        else:
            i += 1
    for s, n in gaps[:12]:
        print(f"  zero 0x{s:04x}-0x{s+n-1:04x} len={n}")


def apply(fullopen: bool, dry: bool, extra: list[str]):
    d = bytearray(OPTION.read_bytes())
    assert len(d) == EXPECT_LEN
    plan: dict[int, int] = {}
    if fullopen:
        for o in FULLOPEN_V1:
            plan[o] = 0x01
    for item in extra:
        o_s, v_s = item.split("=", 1)
        plan[int(o_s, 0)] = int(v_s, 0)
    print(f"plan: {len(plan)} byte(s)")
    for o in sorted(plan):
        print(f"  @0x{o:04x}: {d[o]:#04x} -> {plan[o]:#04x}")
    if dry:
        print("dry-run: no write")
        return 0
    backup()
    for o, v in plan.items():
        d[o] = v
    assert len(d) == EXPECT_LEN
    OPTION.write_bytes(bytes(d))
    v = OPTION.read_bytes()
    ok = all(v[o] == plan[o] for o in plan) and len(v) == EXPECT_LEN
    print(f"verify: {'OK' if ok else 'MISMATCH'} len={len(v)}")
    return 0 if ok else 1


def restore(bak: str | None):
    if bak:
        src = SAVEDIR / bak
    else:
        cands = sorted(SAVEDIR.glob("OPTION.bak.*"),
                       key=lambda p: p.stat().st_mtime)
        # prefer timestamped over .latest helper
        ts = [p for p in cands if "latest" not in p.name]
        src = ts[-1] if ts else (SAVEDIR / "OPTION.bak.latest")
    d = src.read_bytes()
    assert len(d) == EXPECT_LEN
    OPTION.write_bytes(d)
    print(f"restored {OPTION} from {src.name} ({len(d)} B)")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("scan")
    sub.add_parser("backup")
    a = sub.add_parser("apply")
    a.add_argument("--fullopen", action="store_true")
    a.add_argument("--dry-run", action="store_true")
    a.add_argument("--set", action="append", default=[],
                   help="extra OFFSET=VALUE (e.g. 0x1C=1), repeatable")
    r = sub.add_parser("restore")
    r.add_argument("--bak", default=None)
    args = ap.parse_args()
    if not OPTION.exists():
        print(f"missing {OPTION} (set CVC_RPCS3?)")
        return 1
    if args.cmd == "scan":
        scan()
    elif args.cmd == "backup":
        backup()
    elif args.cmd == "apply":
        if not args.fullopen and not args.set:
            print("nothing to do: pass --fullopen and/or --set OFF=VAL")
            return 2
        return apply(args.fullopen, args.dry_run, args.set)
    elif args.cmd == "restore":
        restore(args.bak)
    return 0


if __name__ == "__main__":
    sys.exit(main())
