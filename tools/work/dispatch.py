#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Disassemble the key-dispatch region (0x4c5c0-0x4c720) and the lookup callee
0x1268b8, to learn how the schema keys (scenario/character/unlock/skil) map to
save storage. We print each key site with its surrounding call and args.
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF


def main():
    img = Image(ELF)
    # key-dispatch region
    print("== key-dispatch region 0x4c5b0-0x4c720 ==")
    for ins in img.disasm_range(0x4c5b0, 0x4c720 - 0x4c5b0):
        print("  0x%08x  %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))

    print("\n== lookup callee 0x1268b8 (first 120 insns) ==")
    for k, ins in enumerate(img.disasm_range(0x1268b8, 0x1268b8 + 0x200)):
        if k > 120:
            break
        print("  0x%08x  %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))


if __name__ == "__main__":
    main()
