#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse ELF imports (PT_DYNAMIC -> .dynsym/.dynstr + JMPREL) and XREF them.

This EBOOT uses ABSOLUTE addressing for globals (lis rX,hi ; addic/ld rX,rX,-off),
so an imported function's GOT slot G is materialized as:
    lis  rX, hi16(G)
    ld/lwz rX, lo16_signed(rX)      ; or addi to just compute G then use as ptr
We find every such site for each import GOT slot => the callers of cellFs*/
cellSave* etc. The routine that opens/writes GAMEDATA is the save-file core.
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

EXEC_OFF, EXEC_ADDR, EXEC_SIZE = 0x230, 0x10230, 0x22a714
DT_NULL, DT_STRTAB, DT_SYMTAB, DT_RELA, DT_RELASZ, DT_RELAENT = 0, 5, 6, 7, 8, 9
DT_STRSZ, DT_SYMENT, DT_JMPREL, DT_PLTRELSZ, DT_SONAME, DT_NEEDED = 10, 11, 23, 2, 14, 1


def walk_dynamic(d, phoff, phentsize, phnum):
    dyn = None
    for i in range(phnum):
        o = phoff + i * phentsize
        p_type = struct.unpack_from(">I", d, o)[0]
        p_offset, p_vaddr = struct.unpack_from(">QQ", d, o + 8)
        if p_type == 2:  # PT_DYNAMIC
            dyn = (p_offset, p_vaddr)
            break
    if not dyn:
        return {}
    off, _ = dyn
    entries = {}
    while True:
        tag, val = struct.unpack_from(">QQ", d, off)
        off += 16
        if tag == DT_NULL:
            break
        entries.setdefault(tag, []).append(val)
    return entries


def cstr(d, off):
    end = d.index(b"\x00", off)
    return d[off:end].decode("latin-1", "replace")


def main():
    img = Image(ELF)
    d = img.d
    dyn = walk_dynamic(d, img.phoff, img.phentsize, img.phnum)
    if not dyn:
        print("no PT_DYNAMIC")
        return

    def v2o(v):
        return img.vaddr_to_off(v)

    strtab_v = dyn.get(DT_STRTAB, [0])[0]
    symtab_v = dyn.get(DT_SYMTAB, [0])[0]
    syment = dyn.get(DT_SYMENT, [24])[0]
    rela_v = dyn.get(DT_JMPREL, dyn.get(DT_RELA, [0]))[0]
    relasz = dyn.get(DT_PLTRELSZ, dyn.get(DT_RELASZ, [0]))[0]
    relaent = dyn.get(DT_RELAENT, [24])[0]
    strsz = dyn.get(DT_STRSZ, [0])[0]

    print("strtab=0x%x symtab=0x%x rela=0x%x relasz=%d syment=%d relaent=%d"
          % (strtab_v, symtab_v, rela_v, relasz, syment, relaent))

    strtab_o = v2o(strtab_v)
    symtab_o = v2o(symtab_v)
    rela_o = v2o(rela_v)

    def sym_name(idx):
        so = symtab_o + idx * syment
        st_name = struct.unpack_from(">I", d, so)[0]
        if st_name == 0:
            return ""
        return cstr(d, strtab_o + st_name)

    # parse JMPREL relocations -> GOT slot vaddr -> import name
    got2name = {}
    n = relasz // relaent if relaent else 0
    for i in range(n):
        o = rela_o + i * relaent
        r_offset, r_info, r_addend = struct.unpack_from(">QQQ", d, o)
        sym = r_info >> 32
        rtype = r_info & 0xffffffff
        name = sym_name(sym)
        if name:
            got2name[r_offset] = name
    print("imports (GOT slot -> name):", len(got2name))

    # print interesting imports
    interesting = [k for k, v in got2name.items()
                   if any(t in v for t in ("Fs", "Save", "save", "Fs", "Sysutil",
                                            "Png", "Spurs", "Gcm", "Sysmodule"))]
    print("\n== interesting imports ==")
    for g in sorted(interesting):
        print("  GOT 0x%08x -> %s" % (g, got2name[g]))

    # XREF: scan exec words for lis+ld/lwz/addi that materialize each GOT slot
    code = d[EXEC_OFF:EXEC_OFF + EXEC_SIZE]
    nwords = len(code) // 4
    words = struct.unpack_from(">%dI" % nwords, code, 0)
    want_hi = {}
    for g in got2name:
        want_hi.setdefault(g >> 16, []).append(g)

    # collect lis sites by (hi, reg)
    sites = []
    for i in range(nwords):
        w = words[i]
        opc = w >> 26
        if opc != 15:
            continue
        ra = (w >> 16) & 0x1f
        imm = w & 0xffff
        rt = (w >> 21) & 0x1f
        if ra != 0:
            continue
        if imm not in want_hi:
            continue
        # look ahead for ld(58)/lwz(32)/addi(14)/addic(13) completing to a GOT slot
        for j in range(i + 1, min(i + 6, nwords)):
            w2 = words[j]
            opc2 = w2 >> 26
            ra2 = (w2 >> 16) & 0x1f
            disp = w2 & 0xffff
            if ra2 != rt:
                continue
            if opc2 in (58, 32, 14, 13, 34, 40, 44):  # ld,lwz,addi,addic,lbz,lhz,sth
                sdisp = disp - 0x10000 if disp >= 0x8000 else disp
                resolved = ((imm << 16) + sdisp) & 0xffffffff
                if resolved in got2name:
                    sites.append((got2name[resolved], EXEC_ADDR + i * 4,
                                  EXEC_ADDR + j * 4))
                    break
                resolved2 = ((imm << 16) + disp) & 0xffffffff
                if resolved2 in got2name:
                    sites.append((got2name[resolved2], EXEC_ADDR + i * 4,
                                  EXEC_ADDR + j * 4))
                    break

    print("\n== import call/reference sites (first 60) ==")
    from collections import Counter
    byname = Counter(s[0] for s in sites)
    for name, cnt in byname.most_common(40):
        ex = [s for s in sites if s[0] == name][:3]
        print("  %-28s x%d  e.g. %s" % (name, cnt,
              ", ".join("lis@0x%x" % e[1] for e in ex)))


if __name__ == "__main__":
    main()
