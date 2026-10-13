#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Structure dump of sakuhin PACs: index + one entry, to find the scenario record
layout (title, unlock condition, cast list of ca%03d characters).
"""
import re
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import cvpatch as C
from cricodecs import cpk

OUT = []
def emit(s=""):
    OUT.append(s)


def main():
    a = cpk.load(str(C.ORIG))
    by = {f.full_path: f for f in a.files}
    pacs = sorted(p for p in by if re.match(r"DATA/sakuhin/sakuhin\d+\.pac$", p))
    emit("sakuhinNNN count: %d" % len(pacs))

    # index file
    idx = a.file_bytes(by["DATA/sakuhin/sakuhin.pac"].toc_index)
    emit("\n== sakuhin.pac (index) len=%d ==" % len(idx))
    emit("hex: " + idx.hex())
    # as u32 array
    for i in range(0, min(len(idx), 128), 4):
        v = struct.unpack_from("<I", idx, i)[0]
        emit("  +0x%03x: %08x (%d)" % (i, v, v))

    # first entry full header
    d = a.file_bytes(by[pacs[0]].toc_index)
    emit("\n== %s len=%d ==" % (pacs[0], len(d)))
    emit("first 256 hex:")
    for i in range(0, min(len(d), 256), 16):
        emit("  %04x: %s" % (i, d[i:i + 16].hex(" ")))
    # u32 array of first 128 bytes
    emit("\nas <I words:")
    for i in range(0, min(len(d), 256), 4):
        v = struct.unpack_from("<I", d, i)[0]
        emit("  +0x%03x: %08x  %d" % (i, v, v))

    # strings with offsets
    emit("\nNUL-separated strings (utf-8 ok, len>=2):")
    start = 0
    while True:
        i = d.find(b"\x00", start)
        chunk = d[start:i] if i >= 0 else d[start:]
        if len(chunk) >= 2:
            try:
                t = chunk.decode("utf-8")
                emit("  [%d..%d] %r" % (start, i if i >= 0 else len(d), t[:70]))
            except UnicodeDecodeError:
                pass
        if i < 0:
            break
        start = i + 1

    with open("tools/work/_pac_dump.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(OUT))
    print("wrote tools/work/_pac_dump.txt (%d lines)" % len(OUT))


if __name__ == "__main__":
    main()
