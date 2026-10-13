#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump the save-key string region (~0x23D580-0x23D800) as clean C-strings, then
search the live GAMEDATA save for each key. If keys appear in the save, the save
is a serialized keyed structure and we finally know the field vocabulary.
"""
import os
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

SAVE = r"D:\Video_Game\Emulator\RPCS3\dev_hdd0\home\00000001\savedata\NPJB00558-GAMEDATA-\GAMEDATA"


def dump_strings(img, lo, hi):
    off = img.vaddr_to_off(lo)
    raw = img.d[off:off + (hi - lo)]
    va = lo
    out = []
    while va < hi and b"\x00" in raw:
        n = raw.index(b"\x00")
        chunk = raw[:n]
        if chunk:
            try:
                s = chunk.decode("shift_jis")
            except Exception:
                s = repr(chunk)
            if len(chunk) <= 40:
                out.append((va, s))
        raw = raw[n + 1:]
        va += n + 1
    return out


def main():
    img = Image(ELF)
    keys = dump_strings(img, 0x23D560, 0x23D820)
    print("== save-key strings @0x23D560-0x23D820 ==")
    for va, s in keys:
        print("  0x%08x: %r" % (va, s))

    if not os.path.exists(SAVE):
        print("\nSAVE not found at", SAVE)
        return
    data = open(SAVE, "rb").read()
    print("\n== search save (%d bytes) for keys ==" % len(data))
    for va, s in keys:
        # only search ASCII-ish keys
        try:
            pat = s.encode("latin-1")
        except Exception:
            continue
        if len(pat) < 3:
            continue
        i = data.find(pat)
        while i >= 0:
            print("  %r found @ save offset 0x%x" % (s, i))
            i = data.find(pat, i + 1)


if __name__ == "__main__":
    main()
