#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump the key-pointer table around vaddr 0x2f2360-0x2f23c0 (rankup/prank/rank
pointers) with resolved strings, then XREF its address(es) in code to find the
function that reads/writes rank (the trust logic).
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

EXEC_OFF, EXEC_ADDR, EXEC_SIZE = 0x230, 0x10230, 0x22a714
# file offsets found: 0x2e2384 -> try vaddr = off + 0x10000 (data segment shift)
# but verify: earlier trust table vaddr 0x2e1f14 == file 0x2d1f14, shift 0x10000


def s16(x):
    return x - 0x10000 if x >= 0x8000 else x


def cstr(img, va, maxlen=48):
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
    return raw.decode("latin-1", "replace")


def main():
    img = Image(ELF)
    d = img.d

    # confirm shift by checking trust table: vaddr 0x2e1f14 should be file 0x2d1f14
    print("check: file[0x2d1f14] = %08x (expect ptr 0x23d940)"
          % struct.unpack_from(">I", d, 0x2d1f14)[0])

    base_file = 0x2e2360
    print("\n== pointer table (file 0x%x .. ) ==" % base_file)
    for fo in range(base_file, base_file + 0x60, 4):
        w = struct.unpack_from(">I", d, fo)[0]
        s = cstr(img, w + 0x10000) if 0x20000 < w < 0x30000 else None
        mark = ""
        if s:
            mark = '  -> "%s"' % s
        print("  file 0x%06x (vaddr 0x%06x): %08x%s" % (fo, fo + 0x10000, w, mark))

    # XREF: find code refs to vaddr 0x2f2384 / 0x2f2380 / 0x2f2394 / 0x2f2398
    targets = {0x2f2380: "tbl+0x18?", 0x2f2384: "rankup_ptr",
               0x2f2388: "rankup_ptr2", 0x2f2394: "prank_ptr",
               0x2f2398: "rank_ptr", 0x2f2360: "tbl_base"}
    code = d[EXEC_OFF:EXEC_OFF + EXEC_SIZE]
    n = len(code) // 4
    words = struct.unpack_from(">%dI" % n, code, 0)
    lis = {}
    for i, w in enumerate(words):
        if (w >> 26) == 15 and ((w >> 16) & 0x1f) == 0:
            lis.setdefault((w >> 21) & 0x1f, []).append((i, w & 0xffff))

    insns = list(img.md.disasm(code, EXEC_ADDR))
    addr2i = {ins.address: i for i, ins in enumerate(insns)}
    print("\n== code XREF to table slots ==")
    hits = []
    for i, w in enumerate(words):
        opc = w >> 26
        if opc not in (13, 14, 24, 25):
            continue
        ra = (w >> 16) & 0x1f
        imm = w & 0xffff
        for li, lhi in lis.get(ra, ()):
            if not (0 <= i - li <= 30):
                continue
            full = ((lhi << 16) + s16(imm)) & 0xffffffff
            full2 = ((lhi << 16) + imm) & 0xffffffff
            hit = None
            for T, nm in targets.items():
                if full == T or full2 == T:
                    hit = (T, nm)
                    break
            if hit:
                k = addr2i.get(EXEC_ADDR + i * 4)
                f = None
                if k is not None:
                    s = k
                    while s > 0 and insns[s].mnemonic not in ("stdu", "mflr"):
                        s -= 1
                    f = insns[s].address
                hits.append((hit[1], EXEC_ADDR + li * 4, EXEC_ADDR + i * 4, f))
                break
    for nm, la, aa, f in hits:
        print("  %-12s lis@0x%08x add@0x%08x func=%s"
              % (nm, la, aa, ("0x%x" % f) if f else "?"))
    if not hits:
        print("  (none via lis+addi; check TOC/addis-r2 style separately)")


if __name__ == "__main__":
    main()
