#!/usr/bin/env python3
"""Brute-force the NPD dev_hash formula against a pristine EDAT.

Target: dev_hash bytes from the pristine header. Try CMAC variants over
npd ranges with candidate keys. A hit reveals Sony's actual formula, which
make_npdata's dev check (wrong even on pristine files) gets wrong.
"""
import sys
from itertools import product
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from Crypto.Hash import CMAC
from Crypto.Cipher import AES

OMAC1 = bytes.fromhex("72F990788F9CFF745725F08E4C128387")
OMAC2 = bytes.fromhex("6BA52976EFDA16EF3C339FB2971E256B")
OMAC3 = bytes.fromhex("9B515FEACF75064981AA604D91A54E97")
# RIF KEY from verbose decrypt of DLC_D009 (rap-derived)
RIFKEY = bytes.fromhex("43CEC56E1154E1E9562EB94B4A3ADEB4")


def xor(a, b):
    return bytes(x ^ y for x, y in zip(a, b))


def main():
    edat = Path(sys.argv[1])
    npd = edat.read_bytes()[:0x80]
    target = npd[0x60:0x70]
    print(f"target dev_hash: {target.hex()}")
    klic_cands = {"rifkey": RIFKEY, "omac1": OMAC1, "omac2": OMAC2,
                  "omac3": OMAC3}
    cands = []
    for kn, kc in klic_cands.items():
        cands.append((f"klic={kn}", kc))
        for on, oc in (("omac1", OMAC1), ("omac2", OMAC2), ("omac3", OMAC3)):
            cands.append((f"klic={kn}^ {on}", xor(kc, oc)))
    ranges = [0x60, 0x70, 0x80, 0x50, 0x40]
    hit = 0
    for (knm, key), end in product(cands, ranges):
        c = CMAC.new(key, ciphermod=AES)
        c.update(npd[:end])
        if c.digest() == target:
            print(f"HIT: CMAC({knm}, npd[0:{end:#x}])")
            hit += 1
    # also: maybe dev_hash covers npd minus dev_hash field with zeroed tail?
    if not hit:
        print("no hit in basic grid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
