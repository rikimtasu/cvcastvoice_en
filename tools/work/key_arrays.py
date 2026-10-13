#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find static char* arrays pointing into the save-vocab string range.

The hashmap keys (scenario ids, character ids) are C-strings; a container usually
holds a static array of char* pointers to them. We scan all data sections for
runs of >=3 consecutive u32 values that each point into 0x23c000-0x244000 (the
vocab/string range), decode the pointed strings, and print the arrays. Arrays
whose members are scenario/character-ish names are the key lists.
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

LO, HI = 0x23c000, 0x244000


def cstr(img, va, maxlen=48):
    raw = img.read_at_v(va, maxlen)
    if not raw:
        return None
    if b"\x00" in raw:
        raw = raw[:raw.index(b"\x00")]
    if not raw:
        return None
    printable = sum(1 for c in raw if 32 <= c < 127 or c >= 0x80)
    if printable < len(raw) * 0.6:
        return None
    try:
        return raw.decode("shift_jis")
    except Exception:
        return raw.decode("latin-1", "replace")


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
        out.append(dict(name=nm(no), type=typ, flags=flags, addr=addr, off=off, size=size))
    return out


def main():
    img = Image(ELF)
    d = img.d
    secs = all_sections(d)
    data_secs = [s for s in secs if s["type"] == 1 and s["size"] >= 8]
    print("== char* arrays into vocab range ==")
    found = 0
    for s in data_secs:
        off, size, addr = s["off"], s["size"], s["addr"]
        run = []
        for o in range(off, off + size, 4):
            w = struct.unpack_from(">I", d, o)[0]
            if LO <= w < HI:
                run.append((addr + (o - off), w))
            else:
                if len(run) >= 4:
                    dump_run(img, run, s["name"])
                    found += 1
                run = []
        if len(run) >= 4:
            dump_run(img, run, s["name"])
            found += 1
    print("\ntotal arrays:", found)


def dump_run(img, run, secname):
    base = run[0][0]
    # decode first few strings
    samples = []
    for _, w in run[:6]:
        st = cstr(img, w)
        samples.append(st if st is not None else "0x%x" % w)
    print("  [%s] @0x%06x len=%d : %s" % (secname, base, len(run), samples))


if __name__ == "__main__":
    main()
