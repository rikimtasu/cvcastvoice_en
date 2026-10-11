#!/usr/bin/env python3
"""
Examine the two .pac name databases that hold the speaker name and CV credit,
to decide whether the on-screen UI strings can be patched as clean TEXT.

  DATA/daihon/daihonbase.pac   -> holds 天海春香 (speaker full name)
  DATA/daihon/seiyubase.pac    -> holds 西宮寺　美礼 (CV credit) + kana reading

Dumps: container magics, the record layout around each hit, and every
null-terminated UTF-8 string in a window so we can see if records are
fixed-stride, offset-indexed, or length-prefixed (i.e. is same-length or
in-place-with-padding replacement viable?).
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

ORIG = C.ORIG


def hexdump(data: bytes, start: int, length: int) -> str:
    b = data[start:start + length]
    out = []
    for i in range(0, len(b), 16):
        chunk = b[i:i + 16]
        hexs = " ".join(f"{x:02x}" for x in chunk)
        asc = "".join(chr(x) if 0x20 <= x <= 0x7E else "." for x in chunk)
        out.append(f"  {start + i:06x}  {hexs:<47s}  |{asc}|")
    return "\n".join(out)


def find_magics(data: bytes, magics):
    hits = []
    for m in magics:
        s = 0
        while True:
            i = data.find(m, s)
            if i < 0:
                break
            hits.append((i, m))
            s = i + 1
    return sorted(hits)


def utf8_runs(data: bytes, minlen: int = 2):
    """Yield (offset, text) for printable UTF-8 runs."""
    import re
    out = []
    for m in re.finditer(rb"[\x20-\x7e\xc2-\xf4][\x20-\x7e\x80-\xbf\xc2-\xf4]+",
                         data):
        s = m.group()
        try:
            t = s.decode("utf-8")
        except Exception:
            continue
        # must contain at least one CJK or be clearly japanese name-ish
        if len(t) >= minlen and any("\u3000" <= c <= "\u9fff" or
                                    "\uff00" <= c <= "\uffef" for c in t):
            out.append((m.start(), t))
    return out


def main():
    a = cpk.load(str(ORIG))
    files = {f.full_path: f for f in a.files}

    for path in ("DATA/daihon/daihonbase.pac", "DATA/daihon/seiyubase.pac"):
        f = files.get(path)
        if not f:
            print(f"MISSING {path}")
            continue
        d = a.file_bytes(f.toc_index)
        print(f"\n========== {path}  ({len(d)} bytes) ==========")
        print(f"  extract_size={f.extract_size} file_size={f.file_size} "
              f"toc_index={f.toc_index}")
        # container magics
        magics = find_magics(d, [b"PAC", b"@UTF", b"CPK", b"TOC", b"ETOC",
                                 b"HCA", b"ADX", b"AIX", b"FPIX", b"SPRF"])
        print(f"  magics: {[(hex(o), m.decode('latin1')) for o, m in magics[:12]]}")
        print(f"  header:")
        print(hexdump(d, 0, 64))

        # locate the specific name strings
        for needle in (b"\xe5\xa4\xa9\xe6\xb5\xb7\xe6\x98\xa5\xe9\xa6\x99",  # 天海春香
                       b"\xe8\xa5\xbf\xe5\xae\xae\xe5\xaf\xba",  # 西宮寺
                       b"\xe7\xbe\x8e\xe7\xa4\xbc"):  # 美礼
            i = d.find(needle)
            if i >= 0:
                print(f"\n  --- context @ {i:#x} ({needle.decode('utf-8')}) ---")
                print(hexdump(d, max(0, i - 48), 128))

        # sample of name-like strings
        runs = utf8_runs(d)
        print(f"\n  CJK string runs: {len(runs)} (first 40)")
        for off, t in runs[:40]:
            print(f"    @{off:#07x}  {t!r}")


if __name__ == "__main__":
    main()
