#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find the save serialization routine and the key->offset mapping.

The schema keys (scenario/character/unlock/skil/cas_top, obi*) live at
~0x23D5C4-0x23D618. We find every code site that computes an address into that
range (via 'lis rX,0x23 ; addic/addi rY,rX,-0x2aXX' patterns, and also via
'lis rX,0x24 ; addic -0x2aXX'), then dump the enclosing function. The routine
that indexes these keys is the save read/write core; by reading how it pairs a
key name with a length/count we learn the save layout.
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

EXEC_OFF, EXEC_ADDR, EXEC_SIZE = 0x230, 0x10230, 0x22a714
# key-region: 0x23D560-0x23D620. We look for immediate magnitudes that select it.
# Sites reference it via lis rX,0x23 + addic -0x2aXX, or lis rX,0x24 + addic -0x2aXX.
# So collect completions whose LOW16 == (0x10000 - (keyaddr & 0xffff)) for base 0x24
# i.e. addr = 0x240000 - X  ->  X = 0x240000 - keyaddr.
KEY_LO, KEY_HI = 0x23D560, 0x23D620


def main():
    img = Image(ELF)
    d = img.d

    def cstr_at(va, maxlen=48):
        raw = img.read_at_v(va, maxlen)
        if not raw:
            return None
        if b"\x00" in raw:
            raw = raw[:raw.index(b"\x00")]
        if not raw:
            return None
        try:
            return raw.decode("shift_jis")
        except Exception:
            return raw.decode("latin-1", "replace")

    code = d[EXEC_OFF:EXEC_OFF + EXEC_SIZE]
    insns = list(img.md.disasm(code, EXEC_ADDR))
    print("decoded:", len(insns))

    def rawword(va):
        return struct.unpack_from(">I", d, EXEC_OFF + (va - EXEC_ADDR))[0]

    # candidate immediates that select the key region from base 0x240000 or 0x230000
    want_imm = set()
    for ka in range(KEY_LO, KEY_HI):
        # base 0x240000, negative: imm = ka - 0x240000 -> low16 = (ka - 0x240000)&0xffff
        want_imm.add((ka - 0x240000) & 0xffff)
        # base 0x230000, positive: imm = ka - 0x230000
        want_imm.add((ka - 0x230000) & 0xffff)

    # find all lis sites into registers
    lis_by_reg = {}
    for i, ins in enumerate(insns):
        if ins.mnemonic in ("lis", "addis"):
            p = [x.strip() for x in ins.op_str.split(",")]
            if len(p) == 3 and p[1] == "r0":
                try:
                    base = int(p[2], 0) << 16
                except Exception:
                    continue
                if base in (0x230000, 0x240000):
                    lis_by_reg.setdefault(p[0], []).append((i, base))

    hits = []
    for i, ins in enumerate(insns):
        w = rawword(ins.address)
        opc = w >> 26
        if opc not in (12, 13, 14, 24, 25, 32, 34, 36, 37, 38):
            continue
        imm = w & 0xffff
        ra = (w >> 16) & 0x1f
        p = [x.strip() for x in ins.op_str.split(",")]
        if len(p) < 3:
            continue
        srcname = p[1]
        if srcname not in lis_by_reg:
            continue
        # nearest preceding compatible lis
        cand = [x for x in lis_by_reg[srcname] if x[0] < i]
        if not cand:
            continue
        li, base = cand[-1]
        if i - li > 30:
            continue
        # compute resolved low-region address
        if opc in (12, 13, 14, 32, 34, 36, 37, 38):  # signed disp
            simm = imm - 0x10000 if imm >= 0x8000 else imm
            resolved = base + simm
        else:  # ori/oris unsigned
            resolved = base + imm
        if KEY_LO <= resolved < KEY_HI:
            hits.append((resolved, insns[li].address, ins.address, opc, simm if opc not in (24,25) else imm))

    print("\n== code sites selecting key-region addresses ==")
    seen_addr = set()
    for resolved, la, aa, opc, imm in hits:
        if aa in seen_addr:
            continue
        seen_addr.add(aa)
        s = cstr_at(resolved)
        print("  -> 0x%08x %r : lis@0x%08x complete@0x%08x opc=%d imm=%d"
              % (resolved, s, la, aa, opc, imm))

    # dump enclosing functions (unique)
    def func_start(idx):
        s = idx
        while s > 0 and insns[s].mnemonic not in ("stdu", "mflr"):
            s -= 1
        return s

    addr2i = {ins.address: k for k, ins in enumerate(insns)}
    seen_f = set()
    print("\n== enclosing functions (first ref each) ==")
    for resolved, la, aa, opc, imm in hits:
        if aa not in addr2i:
            continue
        fs = func_start(addr2i[aa])
        faddr = insns[fs].address
        if faddr in seen_f:
            continue
        seen_f.add(faddr)
        print("\n---- func 0x%08x (refs 0x%08x %r) ----" % (faddr, resolved, cstr_at(resolved)))
        for j in range(fs, min(fs + 100, len(insns))):
            print("  0x%08x  %-8s %s" % (insns[j].address, insns[j].mnemonic, insns[j].op_str))


if __name__ == "__main__":
    main()
