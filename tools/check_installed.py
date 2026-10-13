#!/usr/bin/env python3
"""Check what the INSTALLED S297 EDAT actually contains (EN or JP?)
and hunt the profile strings across base + DLC sources."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

NEEDLES = ["帰り道に酔", "繁華街で", "飲み屋", "信頼度8でオープン"]


def scan(label, get_bytes, files):
    print(f"== {label} ==")
    for f in files:
        try:
            d = get_bytes(f)
        except Exception:
            continue
        for n in NEEDLES:
            nb = n.encode("utf-8")
            if nb in d:
                i = d.find(nb)
                print(f"  {f.full_path} has {n!r}")
                print(f"    ...{d[max(0,i-40):i+80]!r}")


def main():
    a = cpk.load(str(C.ROOT / "dlc" / "installed_check.cpk"))
    fa = a.files
    scan("INSTALLED S297", lambda f: a.file_bytes(f.toc_index), fa)
    # profile file specifically: dump its text fields
    for f in fa:
        if f.full_path.lower().endswith(".info"):
            d = a.file_bytes(f.toc_index)
            print(f"--- {f.full_path} ({len(d)} bytes) text fields ---")
            for part in d.split(b"\x00"):
                try:
                    t = part.decode("utf-8")
                except UnicodeDecodeError:
                    continue
                if len(t) >= 2 and any("\u3040" <= c <= "\u30ff" or
                                       "\u4e00" <= c <= "\u9fff" for c in t):
                    print(f"  {t[:80]!r}")


if __name__ == "__main__":
    main()
