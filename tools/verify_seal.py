#!/usr/bin/env python3
"""Verify a sealed EDAT under RPCS3's exact semantics: every block's stored
hash must equal HMAC/CMAC over the CIPHERTEXT (encrypt-then-MAC).

Handles 0xC layout (flat 0x10 metadata). Reports first failing block.
"""
import hmac
import struct
import sys
from hashlib import sha1
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from Crypto.Cipher import AES
from Crypto.Hash import CMAC

EDAT_KEY_1 = bytes.fromhex("4CA9C14B01C95309969BEC68AA0BC081")
ZERO_IV = bytes(16)
RAP_KEY = bytes.fromhex("869F7745C13FD890CCF29188E3CC3EDF")
RAP_PBOX = [0x0C, 0x03, 0x06, 0x04, 0x01, 0x0B, 0x0F, 0x08,
            0x02, 0x07, 0x00, 0x05, 0x0A, 0x0E, 0x0D, 0x09]
RAP_E1 = bytes.fromhex("A93E1FD67C55A329B75FDDA62A95C7A5")
RAP_E2 = bytes.fromhex("67D45DA3296D006A4E7C537BF5538C74")


def rap_to_rif(rap: bytes) -> bytes:
    key = AES.new(RAP_KEY, AES.MODE_CBC, iv=ZERO_IV).decrypt(rap)
    key = bytearray(key)
    for _ in range(5):
        for i in range(16):
            p = RAP_PBOX[i]
            key[p] ^= RAP_E1[p]
        for i in range(15, 0, -1):
            p = RAP_PBOX[i]
            pp = RAP_PBOX[i - 1]
            key[p] ^= key[pp]
        o = 0
        for i in range(16):
            p = RAP_PBOX[i]
            kc = key[p] - o
            ec2 = RAP_E2[p]
            if o != 1 or kc != 0xFF:
                o = 1 if kc < ec2 else 0
                key[p] = (kc - ec2) & 0xFF
            else:
                key[p] = kc & 0xFF
    return bytes(key)


def main():
    p = Path(sys.argv[1])
    rap = Path(sys.argv[2]).read_bytes()[:0x10]
    rifkey = rap_to_rif(rap)
    b = p.read_bytes()
    npd = b[:0x80]
    digest, dev = npd[0x40:0x50], npd[0x60:0x70]
    flags, bsize, fsize = struct.unpack(">iiQ", b[0x80:0x90])
    total = (fsize + bsize - 1) // bsize
    bad = 0
    checked = 0
    for i in range(total):
        stored = b[0x100 + i * 0x10:0x100 + i * 0x10 + 0x10]
        off = 0x100 + total * 0x10 + i * bsize
        length = bsize if i < total - 1 else (fsize % bsize or bsize)
        pad = (length + 15) & ~15
        enc = b[off:off + pad]
        if len(enc) < pad:
            print(f"block {i}: SHORT READ")
            bad += 1
            continue
        b_key = dev[:0xC] + i.to_bytes(4, "big")
        key_result = AES.new(rifkey, AES.MODE_ECB).encrypt(b_key)
        hf = AES.new(EDAT_KEY_1, AES.MODE_CBC, iv=ZERO_IV).decrypt(key_result)
        c = CMAC.new(hf, ciphermod=AES)
        c.update(enc[:pad])
        checked += 1
        if c.digest() != stored:
            if bad < 3:
                print(f"block {i}: MISMATCH")
            bad += 1
    print(f"{p.name}: {checked} blocks checked, {bad} bad "
          f"(flags={flags:#x})")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
