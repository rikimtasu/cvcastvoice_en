#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fast, correct XREF finder (raw PPC64 word scan).

Key fix vs the naive version: track the most-recent 'lis/addis' per destination
register with an instruction-age stamp, and only treat a completion (addi/ori)
as valid if its source register's hi was set within a small window (<=16 words)
AND not clobbered since. This survives the many intervening 'lis' between a
load-pair. PPC64 I-form opcodes: lis/addis=15, addi=14, ori=24, oris=25.
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
WINDOW = 16


def main():
    img = Image(ELF)
    str_vaddr = {}
    for t in TARGETS:
        va = img.find_string(t)
        if va is not None:
            str_vaddr[t] = va
    by_vaddr = defaultdict(list)
    for t, va in str_vaddr.items():
        by_vaddr[va].append(t)

    seg = max(img.segs, key=lambda s: s[2])
    vaddr0, off0, size0, _ = seg
    skip = 0x200 if off0 == 0 else 0
    base_off = off0 + skip
    base_v = vaddr0 + skip
    nwords = (size0 - skip) // 4
    words = struct.unpack(">%dI" % nwords, img.d[base_off:base_off + nwords * 4])

    MASK = 0xFFFFFFFF
    hi = {}          # reg -> (hi_value, age_index)
    xrefs = defaultdict(list)

    for i in range(nwords):
        w = words[i]
        op = w >> 26
        D = (w >> 21) & 31
        A = (w >> 16) & 31

        if op == 15:  # lis (A==0) / addis
            imm = w & 0xFFFF
            if A == 0:
                hi[D] = ((imm << 16) & MASK, i)
            elif A in hi:
                h, _ = hi[A]
                hi[D] = ((h + ((imm << 16) & MASK)) & MASK, i)
        elif op == 25:  # oris rD,rA,uimm
            uimm = w & 0xFFFF
            if A in hi:
                h, _ = hi[A]
                hi[D] = ((h | (uimm << 16)) & MASK, i)
        elif op == 14:  # addi rD,rA,simm
            simm = w & 0xFFFF
            if simm & 0x8000:
                simm -= 0x10000
            if A in hi:
                h, age = hi[A]
                if i - age <= WINDOW:
                    addr = (h + simm) & MASK
                    if addr in by_vaddr:
                        xrefs[addr].append((base_v + i * 4, D, "addi"))
        elif op == 24:  # ori rD,rA,uimm
            if A in hi:
                h, age = hi[A]
                if i - age <= WINDOW:
                    addr = (h | (w & 0xFFFF)) & MASK
                    if addr in by_vaddr:
                        xrefs[addr].append((base_v + i * 4, D, "ori"))

        if len(hi) > 60:
            hi = {r: v for r, v in hi.items() if i - v[1] <= WINDOW}

    print("scanned %d words" % nwords)
    print("== XREFs to save strings ==")
    tot = 0
    for va, names in sorted(by_vaddr.items()):
        sites = xrefs.get(va, [])
        tot += len(sites)
        if sites:
            print("  0x%x %-18s : %d" % (va, "/".join(names), len(sites)))
            for site, reg, m in sites[:20]:
                print("       @0x%08x (%s r%d)" % (site, m, reg))
    print("total:", tot)


if __name__ == "__main__":
    main()
