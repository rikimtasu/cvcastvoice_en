#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find true executable sections (SHF_EXECINSTR) and test capstone on .text."""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF


def sections(d):
    e_shoff = struct.unpack_from(">Q", d, 0x28)[0]
    e_shentsize = struct.unpack_from(">H", d, 0x3A)[0]
    e_shnum = struct.unpack_from(">H", d, 0x3C)[0]
    e_shstrndx = struct.unpack_from(">H", d, 0x3E)[0]
    out = []
    def sh(i):
        o = e_shoff + i * e_shentsize
        name, typ, flags, addr, offset, size = struct.unpack_from(">IIQQQQ", d, o)
        return name, typ, flags, addr, offset, size
    _, _, _, _, str_off, str_size = sh(e_shstrndx)
    strtab = d[str_off:str_off + str_size]
    def nm(x):
        e = strtab.index(b"\x00", x)
        return strtab[x:e].decode("latin-1", "replace")
    for i in range(e_shnum):
        nameoff, typ, flags, addr, offset, size = sh(i)
        out.append((nm(nameoff), typ, flags, addr, offset, size))
    return out


def main():
    img = Image(ELF)
    d = img.d
    secs = sections(d)
    execs = [s for s in secs if s[2] & 0x4]  # SHF_EXECINSTR
    print("== executable sections ==")
    for name, typ, flags, addr, offset, size in execs:
        print("  %-16s addr=0x%x off=0x%x size=0x%x" % (name, addr, offset, size))

    name, typ, flags, addr, offset, size = execs[0]
    code = d[offset:offset + min(size, 0x1000)]
    insns = list(img.md.disasm(code, addr))
    print("\ncapstone on %s @0x%x -> %d insns in first 4KB" % (name, addr, len(insns)))
    for ins in insns[:12]:
        print("  0x%08x  %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))


if __name__ == "__main__":
    main()
