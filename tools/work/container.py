#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Understand the container->file serialization.

The dispatcher writes schema keys into an in-memory struct (r26+0x1c0..). We
need the code that flattens that struct into the on-disk GAMEDATA. Look at:
  - 0x29a24 : callee called right after each key lookup (likely value getter)
  - 0x29674 : callee that stores into r26+0x1c0.. (likely field setter)
Also disassemble the region just BEFORE the key dispatcher (0x4c100-0x4c260)
where the container struct r26 is likely allocated and its size set — the size
and first fields reveal the on-disk layout start.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF


def show(img, lo, hi, label):
    print("\n== %s (0x%x-0x%x) ==" % (label, lo, hi))
    for ins in img.disasm_range(lo, hi - lo):
        print("  0x%08x  %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))


def main():
    img = Image(ELF)
    show(img, 0x29a24, 0x29a24 + 0x80, "callee 0x29a24 (value getter?)")
    show(img, 0x29674, 0x29674 + 0x60, "callee 0x29674 (field setter?)")
    # region before dispatcher - container setup
    show(img, 0x4c100, 0x4c260, "container setup before dispatcher")


if __name__ == "__main__":
    main()
