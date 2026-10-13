#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find pointers to save strings in DATA segments (TOC / char* tables).

If code reaches "GAMEDATA" via a pointer stored in a table (TOC or a struct of
char*), then somewhere in the image there is an 8-byte (or 4-byte) value equal
to the string's vaddr. We scan ALL segments for u64/u32 == target vaddr, and
report the site. Then any code that loads that table slot is the user.
"""
import struct
from collections import defaultdict

from ppc_disasm import Image, ELF

TARGETS = [
    "GAMEDATA", "OPTION", "CASTDATA.DAT", "%s-GAMEDATA-",
    "/DATA/GameData.cpk", "SAVE DATA", "obiscenario", "obicast", "obisave",
    "cassave", "noscenario", "nocast", "rankup", "prank", "nextrank",
    "prorank", "rankon", "clear", "casting",
]


def main():
    img = Image(ELF)
    d = img.d
    str_vaddr = {}
    for t in TARGETS:
        va = img.find_string(t)
        if va is not None:
            str_vaddr[t] = va
    by_vaddr = defaultdict(list)
    for t, va in str_vaddr.items():
        by_vaddr[va].append(t)
    vset = set(by_vaddr)

    # Scan every segment for u64 BE == target, and u32 BE == target.
    print("== pointer slots referencing target strings ==")
    total = 0
    for vaddr0, off0, size0, fl in img.segs:
        # u64 scan
        n8 = size0 // 8
        for k in range(n8):
            o = off0 + k * 8
            v = struct.unpack_from(">Q", d, o)[0]
            if v in vset:
                site = vaddr0 + (o - off0)
                print("  u64 @vaddr 0x%x (file 0x%x) -> 0x%x %s"
                      % (site, o, v, "/".join(by_vaddr[v])))
                total += 1
        # u32 scan
        n4 = size0 // 4
        for k in range(n4):
            o = off0 + k * 4
            v = struct.unpack_from(">I", d, o)[0]
            if v in vset:
                site = vaddr0 + (o - off0)
                print("  u32 @vaddr 0x%x (file 0x%x) -> 0x%x %s"
                      % (site, o, v, "/".join(by_vaddr[v])))
                total += 1
    print("total pointer slots:", total)


if __name__ == "__main__":
    main()
