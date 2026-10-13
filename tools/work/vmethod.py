#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Disassemble specific vtable method slots to find the tag-emitting serializer.

We take a vtable base, read N code-pointer slots, and disassemble each method
(up to ~40 insns), printing those that write byte immediates 0x00/0x01/0xff to a
buffer (the serialize-write pattern) or that read the save-key strings.
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF


def method_str(img, addr, cap=48):
    insns = img.disasm_range(addr, cap * 4)
    return insns[:cap]


def writes_tag(insns):
    """Heuristic: does this method store a byte imm 0x00/0x01/0xff?"""
    tags = []
    for ins in insns:
        if ins.mnemonic in ("stb",):
            ops = ins.op_str
            for t in ("0xff", "0x1", "0x0"):
                if ops.endswith(t) or ("," + t) in ops:
                    tags.append(t)
    return tags


def main():
    img = Image(ELF)
    d = img.d
    # vtable bases of interest (from vtables.py)
    bases = {
        "0x2e1f14 (near save keys 0x23D560)": 0x2e1f14,
        "0x2d00a8 (194 slots)": 0x2d00a8,
        "0x2e1f78": 0x2e1f78,
    }
    for label, base in bases.items():
        off = img.vaddr_to_off(base)
        print("\n############ vtable %s @0x%x ############" % (label, base))
        for slot in range(8):
            w = struct.unpack_from(">I", d, off + slot * 4)[0]
            if not (0x10230 <= w < 0x2a0000):
                print("  slot[%d] = 0x%x (not code, stop)" % (slot, w))
                break
            insns = method_str(img, w)
            tags = writes_tag(insns)
            calls = [ins for ins in insns if ins.mnemonic in ("bl",)]
            print("  -- slot[%d] method @0x%x  tagstores=%s  calls=%s"
                  % (slot, w, tags, [hex(int(c.op_str, 0)) for c in calls][:6]))
            # print first 20 insns of methods that store tags
            if tags:
                for ins in insns[:28]:
                    print("       0x%08x  %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))


if __name__ == "__main__":
    main()
