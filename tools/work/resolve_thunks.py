#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resolve the serializer dispatch thunks to their real target methods.

The array at 0x2d00a8 holds thunks: 'r12 = *(0x2d0000 + 0xa8 + k*4); call it'.
So the concrete target is the function pointer stored at object 0x2d0000's vtable
slot 0xa8+4k. We:
  - read the object header at 0x2d0000 to find its vtable pointer (offset 0)
  - for k in 0..N, target = *(vtable + 0xa8 + 4k)
  - disassemble each target method and report tag-stores + string refs + calls
This gives the ordered list of per-type serialize routines => the tag table.
"""
import struct
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

OBJ = 0x2d0000
THUNK_BASE = 0x2d00a8
N = 194


def u32(img, va):
    return struct.unpack_from(">I", img.d, img.vaddr_to_off(va))[0]


def cstr(img, va, maxlen=40):
    raw = img.read_at_v(va, maxlen)
    if not raw:
        return None
    if b"\x00" in raw:
        raw = raw[:raw.index(b"\x00")]
    if not raw:
        return None
    try:
        return raw.decode("shift_jis")
    except Exception:
        return raw.decode("latin-1", "replace")


def analyze(img, addr):
    insns = img.disasm_range(addr, 60 * 4)
    tags = []
    refs = []
    calls = []
    for ins in insns:
        if ins.mnemonic == "stb":
            for t in ("0xff", "0x1", "0x0"):
                if ins.op_str.rstrip().endswith(t):
                    tags.append(t)
        # string refs: lis hi + addi/ori lo resolving to 0x23xxxx
        if ins.mnemonic in ("lis", "addi", "ori", "addic"):
            refs.append(ins)
        if ins.mnemonic == "bl":
            try:
                calls.append(int(ins.op_str, 0))
            except Exception:
                pass
    return insns, tags, calls


def main():
    img = Image(ELF)
    # The thunks load lwz r12, 0xa8(r12) where r12=0x2d0000 => slot at 0x2d00a8+...
    # Actually each thunk k uses offset 0xa8+4k on obj 0x2d0000. Read those slots.
    print("object @0x%x header words:" % OBJ)
    for o in range(0, 0x20, 4):
        print("  0x%x: %08x" % (OBJ + o, u32(img, OBJ + o)))

    print("\n== resolve thunks -> target methods ==")
    targets = []
    for k in range(N):
        slot_va = THUNK_BASE + k * 4
        # thunk reads *(0x2d0000 + 0xa8 + 4k); verify slot offset by decoding thunk
        insns = img.disasm_range(slot_va, 6 * 4)
        off = None
        for ins in insns:
            if ins.mnemonic == "lwz" and "r12" in ins.op_str:
                try:
                    off = int(ins.op_str.split(",")[-1].strip().rstrip(")").lstrip("("), 0)
                except Exception:
                    # pattern 'lwz r12, 0xa8(r12)'
                    part = ins.op_str.split(",")[-1]  # ' 0xa8(r12)'
                    off = int(part.split("(")[0].strip(), 0)
                break
        if off is None:
            continue
        # object vtable slot at OBJ+off holds {fnptr, toc}
        method = u32(img, OBJ + off)
        targets.append((k, slot_va, off, method))

    # show unique methods and their first occurrences
    seen = {}
    for k, slot, off, method in targets:
        if method not in seen:
            seen[method] = (k, off)
    print("distinct target methods:", len(seen))
    for method, (k, off) in sorted(seen.items())[:40]:
        insns, tags, calls = analyze(img, method)
        print("  method 0x%x (first thunk k=%d off=0x%x) tags=%s calls=%s"
              % (method, k, off, tags, [hex(c) for c in calls][:5]))


if __name__ == "__main__":
    main()
