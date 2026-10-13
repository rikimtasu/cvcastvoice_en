#!/usr/bin/env python3
"""Check S-pack .info contents + parse EDAT NPD headers for re-encryption params."""
import os
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

DLC = C.ROOT / "dlc" / "dec"
RPCS3 = Path(os.environ["CVC_RPCS3"]).expanduser() \
    if os.environ.get("CVC_RPCS3") else Path(r"D:\Video_Game\Emulator\RPCS3")
EDATDIR = (RPCS3 / "dev_hdd0" / "game"
           / "NPJB00558" / "USRDIR" / "DATA")


def main():
    a = cpk.load(str(DLC / "DLC_S276.cpk"))
    for f in a.files:
        if f.full_path.lower().endswith(".info"):
            d = a.file_bytes(f.toc_index)
            print(f"== S276 {f.full_path} ({len(d)} bytes) ==")
            print(repr(d[:600]))
    print()
    print("== NPD headers (re-encryption params) ==")
    for ed in sorted(EDATDIR.glob("DLC_*.EDAT")):
        h = ed.read_bytes()[:0x80]
        magic = h[:4]
        ver = struct.unpack(">i", h[0x4:0x8])[0]
        license_ = struct.unpack(">i", h[0x8:0xC])[0]
        dtype = struct.unpack(">i", h[0xC:0x10])[0]
        cid = h[0x10:0x10 + 0x30].split(b"\x00")[0].decode("ascii")
        print(f"{ed.name}: magic={magic} version={ver} license={license_} "
              f"type={dtype} cid={cid}")


if __name__ == "__main__":
    main()
