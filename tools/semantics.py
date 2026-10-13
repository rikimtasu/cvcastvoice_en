#!/usr/bin/env python3
"""Settle plaintext-vs-ciphertext hashing against Sony's 0x3C original.

Extracts Sony's stored block-0 hash (0x20 metadata + xor rule) and tests
HMAC-SHA1-20 over BOTH plaintext and ciphertext. The winner is Sony's
semantics (and what RPCS3 checks).
"""
import hmac
import struct
import sys
from hashlib import sha1
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from Crypto.Cipher import AES

EDAT_KEY_1 = bytes.fromhex("4CA9C14B01C95309969BEC68AA0BC081")
ZERO_IV = bytes(16)
RIFKEY = bytes.fromhex("4B057314ABDBB407206AECB35C8A5E41")


def main():
    b = Path(sys.argv[1]).read_bytes()
    npd = b[:0x80]
    digest, dev = npd[0x40:0x50], npd[0x60:0x70]
    flags, bsize, fsize = struct.unpack(">iiQ", b[0x80:0x90])
    print(f"flags={flags:#x}")
    # 0x20 interleaved: metadata at 0x100 + i*(0x20+bsize)
    meta = b[0x100:0x120]
    stored14 = bytearray(meta[:0x14])
    for j in range(0x10):
        stored14[j] ^= meta[j + 0x10]
    print(f"stored test_hash={bytes(stored14).hex()}")
    enc = b[0x120:0x120 + bsize]
    # keys (same as sim_trial)
    b_key = dev[:0xC] + (0).to_bytes(4, "big")
    key_result = AES.new(RIFKEY, AES.MODE_ECB).encrypt(b_key)
    h = AES.new(RIFKEY, AES.MODE_ECB).encrypt(key_result)  # FLAG 0x10
    key_final = AES.new(EDAT_KEY_1, AES.MODE_CBC, iv=ZERO_IV).decrypt(key_result)
    dec = AES.new(key_final, AES.MODE_CBC, iv=digest).decrypt(enc)
    print(f"dec[0:16]={dec[:16].hex()} ascii={dec[:48]!r}")
    hf14 = AES.new(EDAT_KEY_1, AES.MODE_CBC, iv=ZERO_IV).decrypt(h) + bytes(4)
    print(f"hash_final_14={hf14.hex()}")
    m_dec = hmac.new(hf14, dec, sha1).digest()
    m_enc = hmac.new(hf14, enc, sha1).digest()
    print(f"HMAC(plaintext)==stored? {m_dec.hex() == bytes(stored14).hex()}")
    print(f"  {m_dec.hex()}")
    print(f"HMAC(ciphertext)==stored? {m_enc.hex() == bytes(stored14).hex()}")
    print(f"  {m_enc.hex()}")


if __name__ == "__main__":
    main()
