#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The EBOOT SELF header is 0x90 bytes and an ELF magic follows immediately,
so the code is likely unencrypted (fake-signed). Parse the ELF program headers,
locate the executable segment, and disassemble the entry point with capstone to
confirm readable PPC64 code. Read-only.
"""
import struct

EBOOT = (r"D:\Video_Game\Emulator\RPCS3\games\CV Casting Voice [BLJS10259]"
         r"\PS3_GAME\USRDIR\EBOOT.BIN")
ELF_OFF = 0x90


def main():
    d = open(EBOOT, "rb").read()
    e = d[ELF_OFF:]

    ei_class = e[4]   # 2 = 64-bit
    ei_data = e[5]    # 2 = big-endian
    print("ELF class:", ei_class, "(2=64bit)  data:", ei_data, "(2=BE)")
    e_type = struct.unpack_from(">H", e, 0x10)[0]
    e_machine = struct.unpack_from(">H", e, 0x12)[0]
    e_entry = struct.unpack_from(">Q", e, 0x18)[0]
    e_phoff = struct.unpack_from(">Q", e, 0x20)[0]
    e_phentsize = struct.unpack_from(">H", e, 0x36)[0]
    e_phnum = struct.unpack_from(">H", e, 0x38)[0]
    print("e_type=0x%x e_machine=0x%x(0x15=PPC64) entry=0x%x phoff=0x%x phnum=%d"
          % (e_type, e_machine, e_entry, e_phoff, e_phnum))

    print("\n== program headers ==")
    segs = []
    for i in range(e_phnum):
        o = e_phoff + i * e_phentsize
        p_type, p_flags = struct.unpack_from(">II", e, o)
        p_offset, p_vaddr, p_paddr, p_filesz, p_memsz = struct.unpack_from(
            ">QQQQQ", e, o + 8)
        print("  [%d] type=0x%x flags=0x%x off=0x%x vaddr=0x%x filesz=0x%x memsz=0x%x"
              % (i, p_type, p_flags, p_offset, p_vaddr, p_filesz, p_memsz))
        if p_type == 1:  # PT_LOAD
            segs.append((p_vaddr, p_offset, p_filesz, p_flags))

    # Disassemble entry point.
    try:
        from capstone import Cs, CS_ARCH_PPC, CS_MODE_64, CS_MODE_BIG_ENDIAN
    except Exception as ex:
        print("capstone import failed:", ex)
        return

    # Find the segment containing entry.
    for vaddr, off, filesz, flags in segs:
        if vaddr <= e_entry < vaddr + filesz:
            delta = e_entry - vaddr
            code_off = ELF_OFF + off + delta
            code = d[code_off:code_off + 96]
            print("\n== disasm @entry 0x%x (file 0x%x, %d bytes) =="
                  % (e_entry, code_off, len(code)))
            md = Cs(CS_ARCH_PPC, CS_MODE_64 | CS_MODE_BIG_ENDIAN)
            md.detail = False
            got = 0
            for ins in md.disasm(code, e_entry):
                print("  0x%08x  %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))
                got += 1
                if got >= 16:
                    break
            if not got:
                print("  (no instructions decoded; first bytes: %s)" % code[:32].hex(" "))
            break
    else:
        print("entry not inside a PT_LOAD segment")



if __name__ == "__main__":
    main()
