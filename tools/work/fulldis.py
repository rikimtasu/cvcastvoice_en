#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fully disassemble a function (bounded by blr / stack frame), no early stop on
plain 'b'. Annotate bl targets. Used to read the serializer at 0xef4e4.
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF


def main():
    img = Image(ELF)
    starts = [int(a, 0) for a in sys.argv[1:]] or [0xef4e4]
    cap = int(sys.argv[0]) if False else 600
    for start in starts:
        print("\n==== full function @0x%08x ====" % start)
        off = img.vaddr_to_off(start)
        addr = start
        count = 0
        blrs = 0
        while count < cap:
            ins = next(iter(img.md.disasm(img.d[off:off + 4], addr)), None)
            if ins is None:
                print("  0x%08x  .byte %08x" % (addr, struct.unpack_from(">I", img.d, off)[0]))
                off += 4
                addr += 4
                count += 1
                continue
            note = ""
            if ins.mnemonic == "bl":
                try:
                    note = "  ; -> 0x%x" % int(ins.op_str, 0)
                except Exception:
                    pass
            print("  0x%08x  %-8s %s%s" % (addr, ins.mnemonic, ins.op_str, note))
            off += 4
            addr += 4
            count += 1
            if ins.mnemonic == "blr":
                blrs += 1
                # a function often has multiple blr; stop after 2 consecutive-ish
                if blrs >= 1:
                    # peek next few for epilogue
                    break


if __name__ == "__main__":
    main()
