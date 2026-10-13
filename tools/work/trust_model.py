#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Write the trust model + character schema + blood-type table to a UTF-8 file
(clean, bypassing the console). Includes:
 - trust-reward table 0x2e1f14 (信頼度1..10 -> オーブン)
 - blood types 0x23db44 (A/B/O/AB/??)
 - character record field names (n_nml..n_ter, va, category, ...)
 - cast id scheme ca%03d
 - We also scan for the number of distinct 'ca%03d' cast ids and profile indices
   by looking at how many n_* / secret / profile entries exist in nearby tables.
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

OUT = __file__.rsplit("\\", 1)[0] + "\\_trust_model.txt"


def cstr(img, va, maxlen=80):
    raw = img.read_at_v(va, maxlen)
    if not raw:
        return None
    if b"\x00" in raw:
        raw = raw[:raw.index(b"\x00")]
    if not raw:
        return None
    best = None
    for enc in ("cp932", "shift_jis", "euc_jp"):
        try:
            s = raw.decode(enc)
        except Exception:
            continue
        cjk = sum(1 for c in s if 0x3000 <= ord(c) <= 0x9fff)
        if best is None or cjk > best[1]:
            best = (s, cjk)
    return best[0] if best else raw.decode("latin-1", "replace")


def dump_array(f, img, base, count, label):
    f.write("\n== %s (char* @0x%x, %d) ==\n" % (label, base, count))
    off = img.vaddr_to_off(base)
    for i in range(count):
        p = struct.unpack_from(">I", img.d, off + i * 4)[0]
        f.write("  [%2d] 0x%06x: %s\n" % (i, p, cstr(img, p)))


def main():
    img = Image(ELF)
    with open(OUT, "w", encoding="utf-8") as f:
        dump_array(f, img, 0x2e1f14, 15, "TRUST-REWARD table (信頼度N)")
        f.write("\n== character record fields ==\n")
        for va in (0x23da80, 0x23da88, 0x23da90, 0x23da98, 0x23daa0, 0x23daa8,
                   0x23dab0, 0x23dab8, 0x23dac0, 0x23dac4, 0x23dad4, 0x23dae4,
                   0x23daec, 0x23daf4, 0x23dafc, 0x23db2c, 0x23db3c,
                   0x23db44, 0x23db4c, 0x23db54, 0x23db5c, 0x23db6c,
                   0x23db78, 0x23db88):
            f.write("  0x%06x: %s\n" % (va, cstr(img, va)))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
