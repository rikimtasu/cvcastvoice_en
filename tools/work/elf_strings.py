#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse the DECRYPTED EBOOT ELF (PPC64) manually (lief chokes on it) and
extract strings. Manual ELF64 header + section header + program header parsing,
then keyword-grep the whole image for save/trust strings.
"""
import os
import re
import struct
import sys

ELF = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "EBOOT.elf")

KEYWORDS = [
    "GAMEDATA", "gamedata", "GameData", "save", "Save", "SAVE", "savedata",
    "trust", "Trust", "shinrai", "信頼", "meikan", "名鑑", "seiyu", "声優",
    "scenario", "Scenario", "clear", "Clear", "fans", "money", "affection",
    "rank", "Rank", "level", "Level", "actor", "Actor", "cast", "Cast",
    "cellSave", "cellFsOpen", "cellFsWrite", "cellFsRead", "sys_save",
    ".dat", "OPTION", "CASTDATA",
]


def main():
    d = open(ELF, "rb").read()
    print("size:", len(d), "magic:", d[:4], "class:", d[4], "data:", d[5])

    e_phoff = struct.unpack_from(">Q", d, 0x20)[0]
    e_shoff = struct.unpack_from(">Q", d, 0x28)[0]
    e_phentsize = struct.unpack_from(">H", d, 0x36)[0]
    e_phnum = struct.unpack_from(">H", d, 0x38)[0]
    e_shentsize = struct.unpack_from(">H", d, 0x3A)[0]
    e_shnum = struct.unpack_from(">H", d, 0x3C)[0]
    e_shstrndx = struct.unpack_from(">H", d, 0x3E)[0]
    print("phoff=0x%x phnum=%d shoff=0x%x shnum=%d shstrndx=%d"
          % (e_phoff, e_phnum, e_shoff, e_shnum, e_shstrndx))

    # program headers
    print("\n== program headers ==")
    for i in range(e_phnum):
        o = e_phoff + i * e_phentsize
        p_type, p_flags = struct.unpack_from(">II", d, o)
        p_offset, p_vaddr, p_paddr, p_filesz, p_memsz = struct.unpack_from(
            ">QQQQQ", d, o + 8)
        print("  [%d] type=0x%x flags=0x%x off=0x%x vaddr=0x%x filesz=0x%x memsz=0x%x"
              % (i, p_type, p_flags, p_offset, p_vaddr, p_filesz, p_memsz))

    # section headers
    print("\n== section headers ==")
    secs = []
    for i in range(e_shnum):
        o = e_shoff + i * e_shentsize
        sh_name, sh_type, sh_flags, sh_addr, sh_offset, sh_size = struct.unpack_from(
            ">IIQQQQ", d, o)
        secs.append((sh_name, sh_type, sh_addr, sh_offset, sh_size))
        print("  [%d] name_off=0x%x type=0x%x addr=0x%x off=0x%x size=0x%x"
              % (i, sh_name, sh_type, sh_addr, sh_offset, sh_size))

    # section name string table
    if e_shstrndx < len(secs):
        _, _, _, stroff, strsize = secs[e_shstrndx]
        strtab = d[stroff:stroff + strsize]

        def secname(name_off):
            end = strtab.find(b"\x00", name_off)
            return strtab[name_off:end].decode("ascii", "ignore")
        print("\n== named sections ==")
        for i, (nm, ty, addr, off, size) in enumerate(secs):
            print("  [%d] %-16s type=0x%x addr=0x%x off=0x%x size=0x%x"
                  % (i, secname(nm), ty, addr, off, size))

    # keyword strings across whole image
    print("\n== keyword string hits ==")
    hits = []
    for m in re.finditer(rb"[\x20-\x7e]{4,}", d):
        s = m.group().decode("ascii", "ignore")
        if any(k in s for k in KEYWORDS):
            hits.append((m.start(), s))
    print("total:", len(hits))
    for off, s in hits[:400]:
        print("  0x%08x  %s" % (off, s[:140]))


if __name__ == "__main__":
    sys.exit(main())

