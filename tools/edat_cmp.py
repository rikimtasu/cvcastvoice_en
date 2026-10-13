#!/usr/bin/env python3
"""Compare NPD+EDAT headers and block layout: original vs re-encrypted-pristine.
Reveals exactly what make_npdata -e forges differently."""
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

NPD_FMT = ">4siii48s16s16s16sQQ"


def parse_npd(b):
    magic, ver, lic, typ, cid, digest, thash, dhash, u1, u2 = \
        struct.unpack(NPD_FMT, b[:0x80])
    return {"magic": magic, "ver": ver, "lic": lic, "typ": typ,
            "cid": cid.split(b"\x00")[0],
            "digest": digest.hex(), "title_hash": thash.hex(),
            "dev_hash": dhash.hex(), "unk1": u1, "unk2": u2}


def parse_edat(b):
    flags, bsize, fsize = struct.unpack(">iiQ", b[0x80:0x90])
    return {"flags": flags, "block_size": bsize, "file_size": fsize}


def main():
    a = Path(sys.argv[1]).read_bytes()
    c = Path(sys.argv[2]).read_bytes()
    na, nc = parse_npd(a), parse_npd(c)
    ea, ec = parse_edat(a), parse_edat(c)
    print(f"sizes: orig={len(a)} reenc={len(c)}")
    for k in na:
        mark = "  <-- DIFF" if na[k] != nc[k] else ""
        print(f"  NPD.{k}: {na[k]!r} vs {nc[k]!r}{mark}")
    for k in ea:
        mark = "  <-- DIFF" if ea[k] != ec[k] else ""
        print(f"  EDAT.{k}: {ea[k]!r} vs {ec[k]!r}{mark}")
    # block layout: count 0x4000 blocks after 0x90 header
    for tag, b in (("orig", a), ("reenc", c)):
        nblocks = (len(b) - 0x90) // 0x4000
        tail = (len(b) - 0x90) % 0x4000
        print(f"  {tag}: blocks={nblocks} tail={tail}")
    # first block ciphertext compare (same plaintext => same bytes?)
    n = min(len(a), len(c))
    diff_at = next((i for i in range(n) if a[i] != c[i]), None)
    print(f"  first byte diff at: {hex(diff_at) if diff_at else 'none'}")


if __name__ == "__main__":
    main()
