#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Disassemble a function fully, annotate call targets, and detect type-dispatch.

For each target function we:
  - start at its vaddr, decode until we hit the epilogue (blr) or a cap
  - annotate 'bl' / 'b' targets
  - flag 'bctr' (computed jump => jump table) and the 'mtctr'/'extsh'/address
    computation feeding it, then dump the referenced pointer table from .rodata
This reveals the serializer's type->tag dispatch (the tag table).
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF


def segs(img):
    return img.segs


def disasm_func(img, start, cap=400):
    insns = []
    addr = start
    for _ in range(cap):
        raw = img.md.disasm(img.d[img.vaddr_to_off(addr):img.vaddr_to_off(addr) + 4], addr)
        ins = next(iter(raw), None)
        if ins is None:
            insns.append((addr, ".byte", ""))
            addr += 4
            continue
        insns.append((addr, ins.mnemonic, ins.op_str))
        addr += 4
        if ins.mnemonic in ("blr",):
            break
        # stop if we hit an unconditional branch to a far target (tail)
        if ins.mnemonic == "b":
            break
    return insns


def show(img, start, cap=400):
    print("\n==== function @0x%08x ====" % start)
    for addr, mn, ops in disasm_func(img, start, cap):
        note = ""
        if mn == "bl":
            try:
                tgt = int(ops, 0)
                note = "  ; -> func 0x%x" % tgt
            except Exception:
                pass
        if mn in ("bctr", "bctrl"):
            note = "  ; <<< COMPUTED JUMP (jump table)"
        print("  0x%08x  %-8s %s%s" % (addr, mn, ops, note))


def dump_word_table(img, vaddr, n):
    off = img.vaddr_to_off(vaddr)
    print("  table @0x%08x:" % vaddr)
    for k in range(n):
        o = off + k * 4
        w = struct.unpack_from(">I", img.d, o)[0]
        print("    [%2d] 0x%08x: %08x  -> 0x%08x" % (k, vaddr + k * 4, w, w))


def main():
    img = Image(ELF)
    targets = [int(a, 0) for a in sys.argv[1:]] or [0x3604c, 0x4375c]
    for t in targets:
        show(img, t)


if __name__ == "__main__":
    main()
