#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump the wide region around the rank key-pointer table as records, resolving
key strings, to reconstruct the SAVE FIELD SCHEMA. Then hunt references:
  - u32 pointers to any address in the table region (anywhere in file)
  - code pairs addis rX, r2/r13/r12 + addi (TOC/SDA style, base != r0)
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

EXEC_OFF, EXEC_ADDR, EXEC_SIZE = 0x230, 0x10230, 0x22a714
REG = {0: "r0", 2: "r2", 13: "r13", 12: "r12", 11: "r11", 10: "r10", 9: "r9"}


def s16(x):
    return x - 0x10000 if x >= 0x8000 else x


def cstr(img, va, maxlen=48):
    if not (0x20000 < va < 0x2b0000):
        return None
    raw = img.read_at_v(va, maxlen)
    if not raw:
        return None
    if b"\x00" in raw:
        raw = raw[:raw.index(b"\x00")]
    if not raw:
        return None
    for enc in ("cp932", "utf-8"):
        try:
            return raw.decode(enc)
        except Exception:
            continue
    return None


def main():
    img = Image(ELF)
    d = img.d

    # 1) wide dump: file 0x2e21c0 .. 0x2e24c0 (vaddr +0x10000)
    print("== wide table dump (file 0x2e21c0..0x2e24c0) ==")
    for fo in range(0x2e21c0, 0x2e24c0, 4):
        w = struct.unpack_from(">I", d, fo)[0]
        s = cstr(img, w)
        txt = '  "%s"' % s if s else ""
        print("  v%06x: %08x%s" % (fo + 0x10000, w, txt))

    # 2) whole-file pointers into table region 0x2f2300-0x2f23c0
    print("\n== pointers into table region ==")
    for T in range(0x2f2300, 0x2f23c0, 4):
        b = struct.pack(">I", T)
        i = d.find(b)
        while i >= 0:
            print("  ptr to 0x%06x at file 0x%06x" % (T, i))
            i = d.find(b, i + 1)

    # 3) code: addis with base r2/r13/r12 + addi completing into region
    code = d[EXEC_OFF:EXEC_OFF + EXEC_SIZE]
    n = len(code) // 4
    words = struct.unpack_from(">%dI" % n, code, 0)
    addis = {}  # (reg, base) -> list of (idx, imm)
    for i, w in enumerate(words):
        if (w >> 26) == 15:
            ra = (w >> 16) & 0x1f
            if ra != 0:
                addis.setdefault(((w >> 21) & 0x1f, ra), []).append((i, w & 0xffff))
    insns = list(img.md.disasm(code, EXEC_ADDR))
    addr2i = {ins.address: i for i, ins in enumerate(insns)}
    print("\n== TOC/SDA-style refs into 0x2f2300-0x2f23c0 (need known toc base; "
          "print all addis+addi pairs landing 0x2f2000-0x2f2600) ==")
    hits = 0
    for i, w in enumerate(words):
        opc = w >> 26
        if opc not in (13, 14, 24, 25):
            continue
        ra = (w >> 16) & 0x1f
        imm = w & 0xffff
        for (dst, base), lst in addis.items():
            if base != ra:
                continue
            for ai, aimm in lst:
                if not (0 <= i - ai <= 30):
                    continue
                # (aimm<<16 + 0 if base==0 else assume TOC-relative value) + s16(imm)
                # without knowing TOC we just print candidates where result in range
                for toc in (0,):
                    full = (((aimm << 16) + s16(imm)) + toc) & 0xffffffff
                    if 0x2f2000 <= full <= 0x2f2600:
                        k = addr2i.get(EXEC_ADDR + i * 4)
                        f = None
                        if k is not None:
                            s = k
                            while s > 0 and insns[s].mnemonic not in ("stdu", "mflr"):
                                s -= 1
                            f = insns[s].address
                        print("  addis r%d,%s,0x%x @0x%08x + %s 0x%x -> 0x%x  func=%s"
                              % (dst, REG.get(base, "r%d" % base), aimm,
                                 EXEC_ADDR + ai * 4, insns[k].mnemonic if k else "?",
                                 s16(imm), full, ("0x%x" % f) if f else "?"))
                        hits += 1
                        break
            if hits > 30:
                break
        if hits > 30:
            break
    print("  candidate hits: %d" % hits)


if __name__ == "__main__":
    main()
