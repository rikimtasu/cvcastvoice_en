#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Function-level string XREF (definitive).

For every 'lis rX, imm' (== addis rX, r0, imm) or 'addis rX, rA, imm', follow the
register forward; when an 'addi rY, rX, imm2' or 'ori rY, rX, imm2' completes it,
compute the full 32-bit address. If that address lands in the string range and
resolves to a printable C-string, record (function, string).

We also detect function boundaries (prologue 'stdu r1, -N(r1)' / 'mflr r0') so we
can group string references by the routine that uses them. The function that
references GAMEDATA / CASTDATA.DAT / rank keys is the save-I/O routine.

This removes the field-offset noise because we only emit addresses that actually
resolve to real strings.
"""
import struct
import sys
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ppc_disasm import Image, ELF

STR_LO, STR_HI = 0x230000, 0x2a0000
FWD = 20


def s16(x):
    return x - 0x10000 if x >= 0x8000 else x


def imm_of(op):
    try:
        return int(op.split(",")[-1].strip(), 0)
    except Exception:
        return None


def reg_of(op, idx):
    p = [x.strip() for x in op.split(",")]
    return p[idx] if len(p) > idx else None


def exec_sections(d):
    e_shoff = struct.unpack_from(">Q", d, 0x28)[0]
    e_shentsize = struct.unpack_from(">H", d, 0x3A)[0]
    e_shnum = struct.unpack_from(">H", d, 0x3C)[0]
    out = []
    for i in range(e_shnum):
        o = e_shoff + i * e_shentsize
        name, typ, flags, addr, offset, size = struct.unpack_from(">IIQQQQ", d, o)
        if flags & 0x4 and size:
            out.append((addr, offset, size))
    return out


def decode_str(img, vaddr, maxlen=48):
    raw = img.read_at_v(vaddr, maxlen)
    if not raw:
        return None
    if b"\x00" in raw:
        raw = raw[:raw.index(b"\x00")]
    if not raw:
        return None
    # require mostly printable
    printable = sum(1 for c in raw if 32 <= c < 127)
    if printable < len(raw) * 0.6:
        return None
    try:
        return raw.decode("shift_jis")
    except Exception:
        return raw.decode("latin-1", "replace")


def main():
    img = Image(ELF)
    d = img.d
    insns = []
    for addr, offset, size in exec_sections(d):
        code = d[offset:offset + size]
        for ins in img.md.disasm(code, addr):
            insns.append(ins)
    print("decoded:", len(insns))
    N = len(insns)

    # function start detection: 'stdu r1, -N(r1)' or 'mflr r0'
    func_start = [False] * N
    for i, ins in enumerate(insns):
        if ins.mnemonic == "mflr" and ins.op_str.startswith("r0"):
            func_start[i] = True
        elif ins.mnemonic == "stdu" and ins.op_str.startswith("r1,"):
            func_start[i] = True

    def enclosing_func(i):
        j = i
        while j >= 0 and not func_start[j]:
            j -= 1
        return insns[j].address if j >= 0 else 0

    # string cache
    scache = {}
    def str_at(v):
        if v not in scache:
            scache[v] = decode_str(img, v) if STR_LO <= v < STR_HI else None
        return scache[v]

    # Track last 'lis/addis' per register within a forward window.
    func_refs = defaultdict(set)  # func_addr -> set of (string)
    ref_sites = []  # (func, insn_addr, string)
    last_hi = {}  # reg -> (hi_value, insn_index)
    for i, ins in enumerate(insns):
        m = ins.mnemonic
        # expire old hi entries
        for r in list(last_hi):
            if i - last_hi[r][1] > FWD:
                del last_hi[r]
        if m in ("lis", "addis"):
            imm = imm_of(ins.op_str)
            dst = reg_of(ins.op_str, 0)
            if imm is not None and dst:
                # lis == addis rX, r0 -> base contributes 0
                base = 0 if m == "lis" else None  # addis base unknown (rA); we
                # only trust lis (r0-based) for absolute resolution.
                if m == "lis":
                    last_hi[dst] = ((imm << 16) & 0xffffffff, i)
                else:
                    # for addis rX, rA: if rA is r0 treat like lis; else skip
                    # (rA-relative base unknown statically) unless rA had a hi.
                    ra = reg_of(ins.op_str, 1)
                    if ra == "r0":
                        last_hi[dst] = ((imm << 16) & 0xffffffff, i)
                    elif ra in last_hi:
                        base_hi = (last_hi[ra][0] + (imm << 16)) & 0xffffffff
                        last_hi[dst] = (base_hi, i)
        elif m in ("addi", "ori"):
            dst = reg_of(ins.op_str, 0)
            src = reg_of(ins.op_str, 1)
            imm2 = imm_of(ins.op_str)
            if imm2 is None:
                continue
            if src in last_hi:
                full = (last_hi[src][0] + (s16(imm2) & 0xffffffff)) & 0xffffffff
                s = str_at(full)
                if s is not None:
                    f = enclosing_func(i)
                    func_refs[f].add(s)
                    ref_sites.append((f, ins.address, s))

    print("distinct funcs referencing strings:", len(func_refs))
    print("total string ref sites:", len(ref_sites))

    # Show functions referencing our key strings.
    keys = ("GAMEDATA", "CASTDATA", "-GAMEDATA-", "rank", "scenario",
            "save", "SAVE", "clear", "prank", "trust")
    print("\n== functions referencing KEY strings ==")
    for f, strs in sorted(func_refs.items()):
        interesting = [s for s in strs if any(k in s for k in keys)]
        if interesting:
            print("  func 0x%08x:" % f)
            for s in sorted(interesting)[:12]:
                print("      %r" % s)


if __name__ == "__main__":
    main()
