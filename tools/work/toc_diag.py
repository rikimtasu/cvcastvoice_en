#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnose the dominant string-addressing mode and locate the TOC.

Count addis base registers. If r2 dominates, strings are TOC-relative and we
must know r2's base to resolve them. Also dump the .toc section and test whether
GAMEDATA's vaddr appears as a TOC entry (precomputed pointer).
"""
import struct
import sys
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF


def all_sections(d):
    e_shoff = struct.unpack_from(">Q", d, 0x28)[0]
    e_shentsize = struct.unpack_from(">H", d, 0x3A)[0]
    e_shnum = struct.unpack_from(">H", d, 0x3C)[0]
    e_shstrndx = struct.unpack_from(">H", d, 0x3E)[0]
    def sh(i):
        o = e_shoff + i * e_shentsize
        return struct.unpack_from(">IIQQQQIIQQ", d, o)
    _, _, _, _, str_off, str_size, *_ = sh(e_shstrndx)
    strtab = d[str_off:str_off + str_size]
    def nm(x):
        return strtab[x:strtab.index(b"\x00", x)].decode("latin-1", "replace")
    out = []
    for i in range(e_shnum):
        no, typ, flags, addr, off, size, link, info, align, ent = sh(i)
        out.append(dict(name=nm(no), type=typ, flags=flags, addr=addr,
                        off=off, size=size, ent=ent))
    return out


def main():
    img = Image(ELF)
    d = img.d
    secs = all_sections(d)
    print("== sections ==")
    for s in secs:
        print("  %-14s type=%2d flags=0x%02x addr=0x%06x off=0x%06x size=0x%06x ent=%d"
              % (s["name"], s["type"], s["flags"], s["addr"], s["off"],
                 s["size"], s["ent"]))

    # histogram of addis base registers across exec code
    execs = [s for s in secs if s["flags"] & 0x4 and s["size"]]
    base_hist = Counter()
    lis_count = 0
    for s in execs:
        code = d[s["off"]:s["off"] + s["size"]]
        for ins in img.md.disasm(code, s["addr"]):
            if ins.mnemonic == "lis":
                lis_count += 1
            elif ins.mnemonic == "addis":
                p = [x.strip() for x in ins.op_str.split(",")]
                if len(p) >= 2:
                    base_hist[p[1]] += 1
    print("\naddis base-register histogram:", base_hist.most_common(10))
    print("lis (==addis r0) count:", lis_count)

    # .toc entries: type 8 = SHT_NOBITS? No. Let's find any PROGBITS named .toc
    # or with small entsize (8). Dump entries pointing into string range.
    gd = img.find_string("GAMEDATA")
    print("\nGAMEDATA vaddr = 0x%x" % gd)
    for s in secs:
        if s["size"] and s["type"] == 1 and s["ent"] in (4, 8):
            off, size, ent, addr = s["off"], s["size"], s["ent"], s["addr"]
            n = size // ent
            hits = []
            for k in range(n):
                o = off + k * ent
                if ent == 8:
                    v = struct.unpack_from(">Q", d, o)[0]
                else:
                    v = struct.unpack_from(">I", d, o)[0]
                if v == gd:
                    hits.append(addr + k * ent)
            if hits:
                print("  section %-10s has GAMEDATA ptr at %s"
                      % (s["name"], [hex(h) for h in hits]))


if __name__ == "__main__":
    main()
