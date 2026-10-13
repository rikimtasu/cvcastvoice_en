#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""XREF the rank/trust key strings in the EBOOT: find the code that references
'rankup' (0x240098), 'prank' (0x2400a0), 'rank' (0x2400a8), 'rankon' (0x240238)
and the trust-reward table (0x2e1f14) / first trust string (0x23d940).

Pattern for absolute addressing: lis rX, hi16 ; addi/ori/addic rY, rX, lo16
(lo16 may be sign-extended). We accept both raw-imm and sign-extended matches,
and verify the computed address == target. Emits enclosing function per hit.
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

EXEC_OFF, EXEC_ADDR, EXEC_SIZE = 0x230, 0x10230, 0x22a714

TARGETS = {
    0x240098: "rankup",
    0x2400a0: "prank",
    0x2400a8: "rank",
    0x240238: "rankon",
    0x23d940: "shinrai1(str)",
    0x2e1f14: "trust_table",
    0x23d5f4: "scenario_key",
    0x23d604: "character_key",
}


def s16(x):
    return x - 0x10000 if x >= 0x8000 else x


def main():
    img = Image(ELF)
    d = img.d
    code = d[EXEC_OFF:EXEC_OFF + EXEC_SIZE]
    n = len(code) // 4
    words = struct.unpack_from(">%dI" % n, code, 0)
    insns = list(img.md.disasm(code, EXEC_ADDR))
    addr2i = {ins.address: i for i, ins in enumerate(insns)}

    # group targets by hi16 (as they'd appear in lis)
    by_hi = {}
    for V in TARGETS:
        # a reference may use lis hi=V>>16 + lo, or lis (V>>16)+1 + (lo-0x10000)
        by_hi.setdefault(V >> 16, []).append(V)
        by_hi.setdefault((V + 0x8000) >> 16, []).append(V)

    # find lis rX, imm  (opc15 ra==0) per register -> list of indices
    lis = {}
    for i, w in enumerate(words):
        if (w >> 26) == 15 and ((w >> 16) & 0x1f) == 0:
            lis.setdefault((w >> 21) & 0x1f, []).append((i, w & 0xffff))

    results = {}
    for i, w in enumerate(words):
        opc = w >> 26
        if opc not in (13, 14, 24, 25):  # addic, addi, ori, oris
            continue
        ra = (w >> 16) & 0x1f
        imm = w & 0xffff
        # candidate bases for ra within a 30-insn window
        for li, lhi in lis.get(ra, ()):
            if not (0 <= i - li <= 30):
                continue
            full = ((lhi << 16) + s16(imm)) & 0xffffffff   # sign-extended
            full2 = ((lhi << 16) + imm) & 0xffffffff        # raw
            for V, name in TARGETS.items():
                if full == V or full2 == V:
                    key = (name, EXEC_ADDR + li * 4, EXEC_ADDR + i * 4)
                    if key not in results:
                        results[key] = None
                        k = addr2i.get(EXEC_ADDR + i * 4)
                        f = None
                        if k is not None:
                            s = k
                            while s > 0 and insns[s].mnemonic not in ("stdu", "mflr"):
                                s -= 1
                            f = insns[s].address
                        results[key] = f
                    break
            else:
                continue
            break

    print("== verified key/table XREFs ==")
    for (name, la, aa), f in sorted(results.items(), key=lambda x: x[0][2]):
        print("  %-16s lis@0x%08x  add@0x%08x   func=%s"
              % (name, la, aa, ("0x%x" % f) if f else "?"))


if __name__ == "__main__":
    main()
