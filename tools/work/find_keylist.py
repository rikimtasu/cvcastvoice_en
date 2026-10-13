#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find the concrete scenario/character hashmap KEY list.

The save is name-keyed (§11.3). Top-level keys are scenario/character/unlock/
skil. But each scenario/character entry is keyed by an ID. We search the EBOOT
for:
  - format strings building keys: 'sc%d', 'ch%d', 'ca%03d', 's%03d', digit keys
  - any static array of consecutive short string pointers (the key table)
  - the '%03d'-style id schemes and surrounding vocabulary
Dump clean (utf-8 file) so JP renders.
"""
import os
import re
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_keylist.txt")


def dec(b):
    for enc in ("utf-8", "cp932"):
        try:
            return b.decode(enc)
        except Exception:
            continue
    return b.decode("latin-1", "replace")


def main():
    img = Image(ELF)
    d = img.d
    with open(OUT, "w", encoding="utf-8") as f:
        def w(*a):
            f.write(" ".join(str(x) for x in a) + "\n")

        # 1. all short format/id strings in the schema data range 0x23d000-0x244000
        w("=== id/format strings in 0x23d000-0x244000 ===")
        off0 = img.vaddr_to_off(0x23d000)
        seg = d[off0:off0 + (0x244000 - 0x23d000)]
        for m in re.finditer(rb"[\x20-\x7e]{2,40}\x00", seg):
            s = m.group()[:-1]
            if re.search(rb"%0?\d*d|%s|sc|ch|ca|no|id|%03d", s):
                va = 0x23d000 + m.start()
                w("  0x%08x  %s" % (va, s.decode("latin-1")))

        # 2. static arrays of >=4 consecutive pointers into the string range
        #    (0x230000-0x290000) -> candidate key/index tables
        w("\n=== consecutive string-pointer arrays (key tables) ===")
        STR_LO, STR_HI = 0x230000, 0x2a0000
        # scan data sections only
        e_shoff = struct.unpack_from(">Q", d, 0x28)[0]
        e_shentsize = struct.unpack_from(">H", d, 0x3A)[0]
        e_shnum = struct.unpack_from(">H", d, 0x3C)[0]
        for i in range(e_shnum):
            o = e_shoff + i * e_shentsize
            no, typ, flags, addr, off, size, *_ = struct.unpack_from(">IIQQQQ", d, o)
            if typ != 1 or addr == 0 or size < 16:
                continue
            run = []
            runs = []
            for p in range(off, off + size, 4):
                v = struct.unpack_from(">I", d, p)[0]
                if STR_LO <= v < STR_HI:
                    run.append((addr + (p - off), v))
                else:
                    if len(run) >= 5:
                        runs.append(run)
                    run = []
            if len(run) >= 5:
                runs.append(run)
            for run in runs:
                # decode each pointer's string
                strs = []
                ok = True
                for va, ptr in run[:40]:
                    raw = img.read_at_v(ptr, 24).split(b"\x00")[0]
                    if not raw:
                        ok = False
                        break
                    strs.append(dec(raw))
                if ok:
                    w("  array @0x%08x (%d ptrs): %s"
                      % (run[0][0], len(run), " | ".join(strs[:20])))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
