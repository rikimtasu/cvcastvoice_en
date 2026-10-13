#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RAW-WORD save-serializer XREF (capstone-independent).

We never trust capstone text. For every 4-byte code word we extract opcode, rt,
ra, imm directly. We track the most recent absolute base loaded into each
register via lis/addis (ra==0). When a signed-disp instruction (addic/addi/lwz/
lbz/stw/stwu/stb) or unsigned (ori/oris) references (base + disp) inside the
key-string region, we record it. Then dump enclosing functions.

Region selectors observed: base 0x230000 with +disp, and base 0x240000 with -disp.
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

EXEC_OFF, EXEC_ADDR, EXEC_SIZE = 0x230, 0x10230, 0x22a714
KEY_LO, KEY_HI = 0x23D560, 0x23D620
SIGNED = {12: "addic.", 13: "addic", 14: "addi", 32: "lwz", 34: "lbz",
          36: "stw", 37: "stwu", 38: "stb", 40: "lhz", 44: "sth", 7: "mulli"}
UNSIGNED = {24: "ori", 25: "oris"}


def cstr(img, va, maxlen=48):
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


def main():
    img = Image(ELF)
    d = img.d
    code = d[EXEC_OFF:EXEC_OFF + EXEC_SIZE]
    n = len(code) // 4
    words = struct.unpack_from(">%dI" % n, code, 0)

    # pass 1: absolute base per register (track last lis/addis-with-ra0 per reg)
    base_reg = {}  # reg -> base value
    hits = []      # (resolved, addr, mnem, reg_used)
    for i, w in enumerate(words):
        opc = w >> 26
        rt = (w >> 21) & 0x1f
        ra = (w >> 16) & 0x1f
        imm = w & 0xffff
        addr = EXEC_ADDR + i * 4
        if opc == 15:  # addi/lis
            if ra == 0:
                base_reg[rt] = (imm << 16) & 0xffffffff
            else:
                if ra in base_reg:
                    simm = imm - 0x10000 if imm >= 0x8000 else imm
                    base_reg[rt] = (base_reg[ra] + simm) & 0xffffffff
            continue
        # completion: compute candidate resolved addr from ra's base
        if ra not in base_reg:
            continue
        base = base_reg[ra]
        if opc in SIGNED:
            simm = imm - 0x10000 if imm >= 0x8000 else imm
            resolved = (base + simm) & 0xffffffff
            mn = SIGNED[opc]
        elif opc in UNSIGNED:
            resolved = (base + imm) & 0xffffffff
            mn = UNSIGNED[opc]
        else:
            continue
        if KEY_LO <= resolved < KEY_HI:
            hits.append((resolved, addr, mn, rt))

    print("key-region references:", len(hits))
    print("\n== sites selecting key-region addresses ==")
    for resolved, addr, mn, rt in hits:
        print("  0x%08x  %-6s r%d  -> 0x%08x %r"
              % (addr, mn, rt, resolved, cstr(img, resolved)))

    # pass 2: disassemble enclosing functions of hits (use capstone for pretty print)
    insns = list(img.md.disasm(code, EXEC_ADDR))
    addr2i = {ins.address: k for k, ins in enumerate(insns)}

    def func_start(idx):
        s = idx
        while s > 0 and insns[s].mnemonic not in ("stdu", "mflr"):
            s -= 1
        return s

    seen_f = set()
    print("\n== enclosing functions ==")
    for resolved, addr, mn, rt in hits:
        if addr not in addr2i:
            continue
        fs = func_start(addr2i[addr])
        faddr = insns[fs].address
        if faddr in seen_f:
            continue
        seen_f.add(faddr)
        print("\n---- func 0x%08x (refs 0x%08x %r) ----"
              % (faddr, resolved, cstr(img, resolved)))
        for j in range(fs, min(fs + 90, len(insns))):
            print("  0x%08x  %-8s %s" % (insns[j].address, insns[j].mnemonic, insns[j].op_str))


if __name__ == "__main__":
    main()
