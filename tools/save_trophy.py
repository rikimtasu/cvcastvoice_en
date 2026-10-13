#!/usr/bin/env python3
"""Dump trophy names/descriptions (unlock target list)."""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

T = Path(r"D:\Video_Game\Emulator\RPCS3\dev_hdd0\home\00000001\trophy\NPWR05654_00\TROPCONF.SFM")
d = T.read_bytes()
print(f"TROPCONF {len(d)} bytes")
# it's XML-ish
txt = d.decode("utf-8", "replace")
print(txt[:6000])
