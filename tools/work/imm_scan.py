#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Broad immediate scan: find ANY instruction carrying an immediate equal to the
lo16 or hi16 (+/-1) of a target vaddr, regardless of base register. This catches
TOC-relative (addis rX, r2, hi) and r13/SDA-relative addressing that the strict
r0-based XREF missed. Dump context around each hit.
"""
import re
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF


def imm_list(op):
    out = []
    for tok in re.findall(r"-?0x[0-9a-fA-F]+|-?\b\d+\b", op):
        try:
            out.append(int(tok, 0))
        except Exception:
            pass
    return out


def main():
    img = Image(ELF)
    d = img.d
    e_shoff = struct.unpack_from(">Q", d, 0x28)[0]
    e_shentsize = struct.unpack_from(">H", d, 0x3A)[0]
    e_shnum = struct.unpack_from(">H", d, 0x3C)[0]
    secs = []
    for i in range(e_shnum):
        o = e_shoff + i * e_shentsize
        name, typ, flags, addr, offset, size = struct.unpack_from(">IIQQQQ", d, o)
        if flags & 0x4 and size:
            secs.append((addr, offset, size))

    targets = {
        "GAMEDATA": img.find_string("GAMEDATA"),
        "CASTDATA.DAT": img.find_string("CASTDATA.DAT"),
        "%s-GAMEDATA-": img.find_string("%s-GAMEDATA-"),
    }
    want = {}
    for k, V in targets.items():
        if V:
            want[k] = (V >> 16, V & 0xffff)

    # Sweep once, keep list.
    insns = []
    for addr, offset, size in secs:
        code = d[offset:offset + size]
        for ins in img.md.disasm(code, addr):
            insns.append(ins)
    print("decoded:", len(insns))

    for k, (hi, lo) in want.items():
        print("\n==== %s  hi=0x%x lo=0x%x ====" % (k, hi, lo))
        found = 0
        for i, ins in enumerate(insns):
            if ins.mnemonic in (".byte",):
                continue
            imms = imm_list(ins.op_str)
            hit = (lo in imms) or (hi in imms) or ((hi + 1) in imms)
            if not hit:
                continue
            # context
            print("  @0x%08x: %-7s %s" % (ins.address, ins.mnemonic, ins.op_str))
            for j in range(max(0, i - 2), min(len(insns), i + 3)):
                mark = ">>" if j == i else "  "
                print("     %s 0x%08x  %-7s %s" % (mark, insns[j].address,
                      insns[j].mnemonic, insns[j].op_str))
            found += 1
            if found >= 12:
                print("  ... (truncated)")
                break
        if found == 0:
            print("  (no immediate match)")


if __name__ == "__main__":
    main()
