#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse the PS3 SELF/EBOOT header to determine type + encryption so we know
whether it can be decrypted with standard (bundled) keys.

SELF layout (big-endian):
  0x00 u32 magic 'SCE\x00'
  0x04 u32 version (0x02/0x03/0x04)
  0x08 u16 key_revision
  0x0A u16 header_type
  0x0C u16 metadata_info
  0x0E u64 self_filesize (v2+)
  0x16 u64 self_offset
  0x1E u64 header_len? ... (varies)
Program headers (segment table) live in the SELF header / extended info.
Read-only.
"""
import struct

EBOOT = (r"D:\Video_Game\Emulator\RPCS3\games\CV Casting Voice [BLJS10259]"
         r"\PS3_GAME\USRDIR\EBOOT.BIN")

SELF_TYPE = {
    0x01: "LV0", 0x02: "LV1", 0x03: "LV2", 0x04: "APP",
    0x05: "ISO", 0x06: "LDR", 0x07: "UNK7", 0x08: "NPDRM_APP",
    0x09: "NPDRM_ISO", 0x0A: "NPDRM_LDR",
}


def u64(b, o):
    return struct.unpack_from(">Q", b, o)[0]


def u32(b, o):
    return struct.unpack_from(">I", b, o)[0]


def u16(b, o):
    return struct.unpack_from(">H", b, o)[0]


def main():
    d = open(EBOOT, "rb").read()
    print("size:", len(d))
    print("magic:", d[:4])
    ver = u32(d, 0x04)
    key_rev = u16(d, 0x08)
    htype = u16(d, 0x0A)
    meta = u16(d, 0x0C)
    print("version: 0x%x  key_revision: 0x%x  header_type: 0x%x  meta_info: 0x%x"
          % (ver, key_rev, htype, meta))
    print("header_type -> %s" % SELF_TYPE.get(htype, "?"))

    # Extended header (for app/npdrm) has an info offset table at 0x10.
    # segment/section ext header layout differs by version. Print the
    # extended-header pointer fields we can see.
    print("\n== first 0x100 bytes ==")
    for o in range(0, 0x100, 16):
        print("  %04x  %s" % (o, d[o:o + 16].hex(" ")))

    # APP/NPDRM header: at 0x10 there's a table of u64 offsets to ext headers.
    # Try to read the 6 program-header offset slots (common layout).
    print("\n== candidate ext-header offset table @0x10 (u64 each) ==")
    for i in range(8):
        o = 0x10 + i * 8
        v = u64(d, o)
        print("  slot %d @0x%02x -> 0x%x %s" % (i, o, v, "(in-file)" if v < len(d) else ""))

    # NPDRM content id (if present) sits in the NPDRM ext header.
    # Look for 'NPD' magic anywhere in first 0x400.
    idx = d.find(b"NPD")
    print("\n'NPD' magic at:", hex(idx) if idx >= 0 else "not found")
    if idx >= 0:
        print("  context:", d[idx:idx + 0x50].hex(" "))


if __name__ == "__main__":
    main()
