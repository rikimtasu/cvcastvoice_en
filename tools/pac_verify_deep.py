#!/usr/bin/env python3
"""
Track-A integrity proof: decompress the two .pac name DBs from the ORIGINAL and
from the PATCHED cpk, and show that every changed byte lies inside one of the
covered name slots (i.e. we only overwrote CJK name strings + their trailing
NUL padding, nothing structural). Also prints each changed slot's before/after.
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

ORIG = C.ORIG
PATCHED = Path(__file__).resolve().parents[1] / "out" / "GameData_en.cpk"
PACS = ["DATA/daihon/daihonbase.pac", "DATA/daihon/seiyubase.pac"]


def load(pac_name):
    """Return (orig_bytes, patched_bytes) for a .pac from both archives."""
    orig = cpk.load(str(ORIG))
    of = {f.full_path: f for f in orig.files}
    ob = orig.file_bytes(of[pac_name].toc_index)
    new = cpk.load(str(PATCHED))
    nf = {f.full_path: f for f in new.files}
    nb = new.file_bytes(nf[pac_name].toc_index)
    return ob, nb


def covered_slots(pac_name):
    ov = json.loads((C.WORK / "pac_overlay.json").read_bytes()
                    .decode("utf-8-sig"))
    slots = [tuple(r["span"]) for r in ov["files"][pac_name]["runs"]]
    return slots


def in_slot(pos, slots):
    return any(s <= pos < e for s, e in slots)


def main():
    all_ok = True
    for pac in PACS:
        ob, nb = load(pac)
        print(f"\n=== {pac} ===")
        print(f"  orig extract len : {len(ob)}")
        print(f"  patched extract len: {len(nb)}  "
              f"{'OK (same length)' if len(ob)==len(nb) else 'LENGTH CHANGED!'}")
        if len(ob) != len(nb):
            all_ok = False
            continue
        slots = covered_slots(pac)
        diff_positions = [i for i in range(len(ob)) if ob[i] != nb[i]]
        outside = [i for i in diff_positions if not in_slot(i, slots)]
        print(f"  changed bytes    : {len(diff_positions)}")
        print(f"  changed inside covered slots : {len(diff_positions)-len(outside)}")
        print(f"  changed OUTSIDE slots        : {len(outside)}")
        if outside:
            all_ok = False
            print("  !! OUTSIDE diffs at:", [hex(x) for x in outside[:20]])

        # per-slot before/after (only slots that actually changed)
        ov = json.loads((C.WORK / "pac_overlay.json").read_bytes()
                        .decode("utf-8-sig"))
        changed = 0
        for r in ov["files"][pac]["runs"]:
            s, e = r["span"]
            old = ob[s:e].decode("utf-8", "replace")
            new = nb[s:e].decode("utf-8", "replace")
            if ob[s:e] != nb[s:e]:
                changed += 1
                o = old.replace("\x00", "_")
                n = new.replace("\x00", "_")
                print(f"    @{s:#08x} [{s},{e}) {o!r} -> {n!r}")
        print(f"  slots changed: {changed}")
    print("\n" + ("ALL PACS: OK (only name slots changed)" if all_ok
                  else "PACS: PROBLEM DETECTED"))


if __name__ == "__main__":
    main()
