#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Locate C++ vtables (arrays of code pointers in .data.rel.ro) near the save
system and dump their method slots. The serializer is a C++ object with virtual
methods; the tag-emitting logic lives in those methods. We:
  - identify .data.rel.ro / .data segments (writable+? or relro) holding pointers
    into the code range (0x10230..0x290000)
  - for each cluster of >=3 consecutive code pointers, treat as a vtable and dump
    slots with their addresses so we can then disassemble the serialize method.
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

CODE_LO, CODE_HI = 0x10230, 0x2a0000


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
    # candidate data sections: type 1 (PROGBITS) with SHT_NOBITS excluded, and
    # containing pointers to code. Also NOBITS(.bss) won't have file content.
    cand = [s for s in secs if s["type"] == 1 and s["size"] >= 16]
    print("== candidate data sections ==")
    for s in cand:
        print("  %-16s addr=0x%06x off=0x%06x size=0x%06x" %
              (s["name"], s["addr"], s["off"], s["size"]))

    # scan each for runs of >=3 code pointers
    print("\n== vtable candidates (>=3 consecutive code ptrs) ==")
    vtables = []
    for s in cand:
        off, size, addr = s["off"], s["size"], s["addr"]
        run = []
        for o in range(off, off + size, 4):
            w = struct.unpack_from(">I", d, o)[0]
            if CODE_LO <= w < CODE_HI:
                run.append((addr + (o - off), w))
            else:
                if len(run) >= 3:
                    vtables.append((s["name"], run))
                run = []
        if len(run) >= 3:
            vtables.append((s["name"], run))
    print("vtables found:", len(vtables))
    for name, run in vtables[:40]:
        base = run[0][0]
        print("  [%s] @0x%06x  %d slots: %s" %
              (name, base, len(run),
               ", ".join("0x%x" % w for _, w in run[:10])))


if __name__ == "__main__":
    main()
