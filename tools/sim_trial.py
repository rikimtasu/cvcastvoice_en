#!/usr/bin/env python3
"""Simulate RPCS3's EDATADecrypter block-0 trial exactly (unedat.cpp) on our
sealed file, using the RAP-derived RIF key. Shows precisely which check fails.
"""
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from Crypto.Cipher import AES
from Crypto.Hash import CMAC

EDAT_KEY_1 = bytes.fromhex("4CA9C14B01C95309969BEC68AA0BC081")
ZERO_IV = bytes(16)
RIFKEY = bytes.fromhex("4B057314ABDBB407206AECB35C8A5E41")


def aes_ecb_enc(k, d):
    return AES.new(k, AES.MODE_ECB).encrypt(d)


def aes_cbc_dec(k, iv, d):
    return AES.new(k, AES.MODE_CBC, iv=iv).decrypt(d)


def main():
    p = Path(sys.argv[1])
    b = p.read_bytes()
    npd = b[:0x80]
    digest, title, dev = npd[0x40:0x50], npd[0x50:0x60], npd[0x60:0x70]
    flags, bsize, fsize = struct.unpack(">iiQ", b[0x80:0x90])
    print(f"flags={flags:#x} block={bsize:#x} filesize={fsize}")
    total = (fsize + bsize - 1) // bsize
    print(f"total_blocks={total}")
    print(f"dev_hash={dev.hex()}")
    print(f"digest  ={digest.hex()}")

    # 0xC path: metadata 0x10/section at 0x100+i*0x10
    hash_result = b[0x100:0x110]
    data_off = 0x100 + total * 0x10
    enc = b[data_off:data_off + bsize]
    print(f"hash_result={hash_result.hex()}")
    print(f"data_off={data_off:#x} enc_len={len(enc)}")

    # block key (identical in both implementations)
    b_key = dev[:0xC] + (0).to_bytes(4, "big")
    key_result = aes_ecb_enc(RIFKEY, b_key)
    print(f"key_result={key_result.hex()}")
    h = key_result  # no FLAG 0x10
    # generate_key 0x10000000, version=1 (v4)
    key_final = aes_cbc_dec(EDAT_KEY_1, ZERO_IV, key_result)
    iv_final = digest
    dec = aes_cbc_dec(key_final, iv_final, enc)
    print(f"dec[0:32]={dec[:32].hex()}")
    print(f"dec ascii: {dec[:64]!r}")
    # generate_hash 0x10000000
    hash_final = aes_cbc_dec(EDAT_KEY_1, ZERO_IV, h)
    # trial A: CMAC(hash_final, decrypted) == hash_result ?
    c = CMAC.new(hash_final, ciphermod=AES)
    c.update(dec)
    print(f"CMAC(dec)==stored? {c.digest().hex() == hash_result.hex()} "
          f"({c.digest().hex()})")
    # trial B: CMAC(hash_final, encrypted) == hash_result ?
    c2 = CMAC.new(hash_final, ciphermod=AES)
    c2.update(enc)
    print(f"CMAC(enc)==stored? {c2.digest().hex() == hash_result.hex()} "
          f"({c2.digest().hex()})")


if __name__ == "__main__":
    main()
