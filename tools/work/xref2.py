#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""XREF v3: disassemble the TRUE .text section (found via SHF_EXECINSTR) and find
every site that materializes a target string vaddr via addis/lis + addi/ori.
Fixed the earlier bug where we swept from program-header offset 0 (the ELF
header) and decoded 0 instructions.
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

WINDOW = 16


def s16(x):
    return x - 0x10000 if x >= 0x8000 else x


def exec_sections(d):
    e_shoff = struct.unpack_from(">Q", d, 0x28)[0]
    e_shentsize = struct.unpack_from(">H", d, 0x3A)[0]
    e_shnum = struct.unpack_from(">H", d, 0x3C)[0]
    e_shstrndx = struct.unpack_from(">H", d, 0x3E)[0]
    def sh(i):
        o = e_shoff + i * e_shentsize
        return struct.unpack_from(">IIQQQQ", d, o)  # name,type,flags,addr,off,size
    _, _, _, _, str_off, str_size = sh(e_shstrndx)
    strtab = d[str_off:str_off + str_size]
    def nm(x):
        return strtab[x:strtab.index(b"\x00", x)].decode("latin-1", "replace")
    out = []
    for i in range(e_shnum):
        nameoff, typ, flags, addr, offset, size = sh(i)
        if flags & 0x4 and size:
            out.append((nm(nameoff), addr, offset, size))
    return out


def imm_of(op):
    try:
        return int(op.split(",")[-1].strip(), 0)
    except Exception:
        return None


def main():
    img = Image(ELF)
    d = img.d
    secs = exec_sections(d)
    print("== exec sections ==", [(n, hex(a), hex(s)) for n, a, o, s in secs])

    targets = {
        "GAMEDATA": img.find_string("GAMEDATA"),
        "CASTDATA.DAT": img.find_string("CASTDATA.DAT"),
        "%s-GAMEDATA-": img.find_string("%s-GAMEDATA-"),
    }
    for k, v in targets.items():
        print("  %-14s %s" % (k, hex(v) if v else "NOT FOUND"))

    # Precompute all instructions once (memory: ~500k insns is fine).
    all_insns = []  # (addr, mnem, op, insn_obj)
    for name, addr, offset, size in secs:
        code = d[offset:offset + size]
        for ins in img.md.disasm(code, addr):
            all_insns.append((ins.address, ins.mnemonic, ins.op_str, ins))
    print("\ntotal decoded insns:", len(all_insns))

    # Build a fast addr->index map for window lookups.
    idx_by_addr = {a: i for i, (a, m, o, x) in enumerate(all_insns)}

    for name, V in targets.items():
        if not V:
            continue
        hits = []
        for i, (a, m, o, ins) in enumerate(all_insns):
            if m not in ("addis", "lis"):
                continue
            imm = imm_of(o)
            if imm is None:
                continue
            base_hi = (imm << 16) & 0xffffffff
            dst = o.split(",")[0].strip()
            # look forward up to WINDOW instructions
            for j in range(i + 1, min(i + WINDOW, len(all_insns))):
                a2, m2, o2, _ = all_insns[j]
                if m2 in ("addi", "ori"):
                    p = [x.strip() for x in o2.split(",")]
                    if len(p) >= 3 and p[1] == dst:
                        imm2 = imm_of(o2)
                        if imm2 is None:
                            continue
                        val = (base_hi + (s16(imm2) & 0xffffffff)) & 0xffffffff
                        if val == V:
                            hits.append((a, m, o, a2, m2, o2))
                            break
        print("\n== XREF %s (0x%x): %d site(s) ==" % (name, V, len(hits)))
        for a1, m1, o1, a2, m2, o2 in hits[:30]:
            print("  0x%08x: %-6s %-18s | 0x%08x: %-5s %s" % (a1, m1, o1, a2, m2, o2))


if __name__ == "__main__":
    main()
