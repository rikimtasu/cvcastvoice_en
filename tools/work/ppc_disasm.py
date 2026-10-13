#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Disassembly harness for the decrypted PPC64 EBOOT.

Identity map: file_offset == vaddr for the main code segment (segment[0] off=0
vaddr=0x10000 ... but note vaddr 0x10000 maps to file 0x0? Actually off=0 ->
vaddr=0x10000, so vaddr = file_off + 0x10000 for that segment). We build a
vaddr<->offset mapper from program headers, then:
  * locate a string by content, get its vaddr
  * find every 'lis+addi' (addis/addi) pair or 'lis+ori' that loads that vaddr
    into a register => cross-reference (XREF) sites in code
This is how we find the save-write routine that references "GAMEDATA" etc.
"""
import os
import re
import struct

from capstone import Cs, CS_ARCH_PPC, CS_MODE_64, CS_MODE_BIG_ENDIAN
from capstone.ppc import (PPC_INS_ADDIS, PPC_INS_ADDI, PPC_INS_ORI,
                          PPC_INS_LIS, PPC_INS_ORIS, PPC_INS_ADD,
                          PPC_INS_MTCTR, PPC_INS_BCTRL, PPC_INS_BL)

ELF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "EBOOT.elf")


class Image:
    def __init__(self, path):
        self.d = open(path, "rb").read()
        d = self.d
        self.phoff = struct.unpack_from(">Q", d, 0x20)[0]
        self.phentsize = struct.unpack_from(">H", d, 0x36)[0]
        self.phnum = struct.unpack_from(">H", d, 0x38)[0]
        self.segs = []  # (vaddr, offset, filesz, flags)
        for i in range(self.phnum):
            o = self.phoff + i * self.phentsize
            p_type, p_flags = struct.unpack_from(">II", d, o)
            p_offset, p_vaddr, p_paddr, p_filesz, p_memsz = struct.unpack_from(
                ">QQQQQ", d, o + 8)
            if p_type == 1 and p_filesz:
                self.segs.append((p_vaddr, p_offset, p_filesz, p_flags))
        self.md = Cs(CS_ARCH_PPC, CS_MODE_64 | CS_MODE_BIG_ENDIAN)
        self.md.detail = True
        # Resilience: skip over data-in-code / padding instead of stalling the
        # linear sweep. Without this, capstone stops at the first bad word.
        self.md.skipdata = True
        self.md.skipdata_setup = (".byte", None, None)

    def off_to_vaddr(self, off):
        for vaddr, foff, fsz, fl in self.segs:
            if foff <= off < foff + fsz:
                return vaddr + (off - foff)
        return None

    def vaddr_to_off(self, vaddr):
        for va, foff, fsz, fl in self.segs:
            if va <= vaddr < va + fsz:
                return foff + (vaddr - va)
        return None

    def read_at_v(self, vaddr, n):
        off = self.vaddr_to_off(vaddr)
        if off is None:
            return b""
        return self.d[off:off + n]

    def find_string(self, s):
        """Return vaddr of first occurrence of exact string s (NUL-terminated)."""
        pat = s.encode("latin-1") + b"\x00"
        idx = self.d.find(pat)
        if idx < 0:
            # try without NUL
            idx = self.d.find(s.encode("latin-1"))
            if idx < 0:
                return None
        return self.off_to_vaddr(idx)

    def disasm_range(self, vaddr, n):
        off = self.vaddr_to_off(vaddr)
        code = self.d[off:off + n]
        return list(self.md.disasm(code, vaddr))


def main():
    img = Image(ELF)
    print("segments:", [(hex(v), hex(o), hex(s)) for v, o, s, f in img.segs])

    entry = struct.unpack_from(">Q", img.d, 0x18)[0]
    print("entry: 0x%x" % entry)
    off = img.vaddr_to_off(entry)
    print("entry file off: %s" % hex(off) if off is not None else "None")
    raw = img.read_at_v(entry, 32)
    print("entry raw bytes:", raw.hex(" "))

    insns = img.disasm_range(entry, 48)
    print("decoded:", len(insns))
    for ins in insns[:8]:
        print("  0x%08x  %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))

    # Try the start of the big code segment (vaddr 0x10000 = file 0x0).
    print("\n== disasm @0x10200 (start of .text-ish) ==")
    insns = img.disasm_range(0x10200, 48)
    for ins in insns[:8]:
        print("  0x%08x  %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))



if __name__ == "__main__":
    main()
