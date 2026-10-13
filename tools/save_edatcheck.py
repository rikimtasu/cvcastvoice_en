#!/usr/bin/env python3
"""Check installed EDATs in NPJB00558 DATA: are they the patched ones? + list non-EDAT files."""
import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

INST = Path(r"D:\Video_Game\Emulator\RPCS3\dev_hdd0\game\NPJB00558\USRDIR\DATA")
WS = Path(r"D:\Documents\CVCastingVoice\dlc")
for f in sorted(INST.iterdir()):
    h = hashlib.sha256(f.read_bytes()).hexdigest()[:16]
    # compare to workspace patched + backup
    marks = []
    for tag, base in (("patched", WS / "patched"), ("backup", WS / "backup_edat"),
                      ("dec", WS / "dec")):
        c = base / f.name if tag != "dec" else base / (f.name.replace("_cpk.EDAT", ".cpk"))
        if c.exists():
            hh = hashlib.sha256(c.read_bytes()).hexdigest()[:16]
            if hh == h:
                marks.append(f"=={tag}")
    print(f"{f.name} {f.stat().st_size:>10d} sha16={h} {' '.join(marks)}")
