#!/usr/bin/env python3
"""Decrypt the 8 DLC EDATs with make_npdata (klic=2 local license + RAP).

Reads EDAT/RAP from the RPCS3 install (read-only), writes decrypted
outputs to dlc/dec/ in the workspace. Never touches the install.
"""
import os
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C

RPCS3 = Path(os.environ["CVC_RPCS3"]).expanduser() \
    if os.environ.get("CVC_RPCS3") else Path(r"D:\Video_Game\Emulator\RPCS3")
DLCDATA = RPCS3 / "dev_hdd0" / "game" / "NPJB00558" / "USRDIR" / "DATA"
EXDATA = RPCS3 / "dev_hdd0" / "home" / "00000001" / "exdata"
NP = (Path(__file__).resolve().parent / "npdata_src" / "make_npdata.exe")
OUT = C.ROOT / "dlc" / "dec"

PAIRS = [
    ("DLC_S276_cpk.EDAT", "JP0700-NPJB00558_00-DRMCONTENTCVS276.rap"),
    ("DLC_S287_cpk.EDAT", "JP0700-NPJB00558_00-DRMCONTENTCVS287.rap"),
    ("DLC_S295_cpk.EDAT", "JP0700-NPJB00558_00-DRMCONTENTCVS295.rap"),
    ("DLC_S297_cpk.EDAT", "JP0700-NPJB00558_00-DRMCONTENTCVS297.rap"),
    ("DLC_S305_cpk.EDAT", "JP0700-NPJB00558_00-DRMCONTENTCVS305.rap"),
    ("DLC_D009_cpk.EDAT", "JP0700-NPJB00558_00-DRMCONTENTCVD009.rap"),
    ("DLC_D012_cpk.EDAT", "JP0700-NPJB00558_00-DRMCONTENTCVD012.rap"),
    ("DLC_D015_cpk.EDAT", "JP0700-NPJB00558_00-DRMCONTENTCVD015.rap"),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ok = True
    for edat, rap in PAIRS:
        src = DLCDATA / edat
        rf = EXDATA / rap
        dst = OUT / (edat.replace(".EDAT", "").replace("_cpk", "") + ".cpk")
        if dst.exists() and dst.stat().st_size > 0:
            print(f"SKIP (exists) {dst.name} {dst.stat().st_size}")
            continue
        if not src.exists():
            print(f"MISSING EDAT {src}")
            ok = False
            continue
        if not rf.exists():
            print(f"MISSING RAP {rf}")
            ok = False
            continue
        r = subprocess.run([str(NP), "-d", str(src), str(dst), "2", str(rf)],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        tail = (r.stdout + r.stderr)[-600:]
        if r.returncode or not dst.exists():
            print(f"FAIL {edat} rc={r.returncode}\n{tail}")
            ok = False
        else:
            print(f"OK {edat} -> {dst.name} {dst.stat().st_size}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
