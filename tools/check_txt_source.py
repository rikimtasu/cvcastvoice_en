#!/usr/bin/env python3
"""Are the .txt scenario files the SOURCE of the compiled .srt?
Check: does up268_00.txt dialogue appear inside up268_00.srt?"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk


def main():
    a = cpk.load(str(C.ORIG))
    by = {f.full_path: f for f in a.files}
    t = a.file_bytes(by["DATA/srt_ev/pl268/up268_00.txt"].toc_index
                     ).decode("utf-16-le", "replace")
    # first few dialogue lines (non-command, JP, len>=4)
    dlg = []
    for ln in t.splitlines():
        s = ln.strip()
        if not s or s[0] in ";@/[<$" or s.startswith(("地の文", "キャラ",
                                                      "ボイス", "女性")):
            continue
        if any("\u3040" <= c <= "\u30ff" or "\u4e00" <= c <= "\u9fff"
               for c in s) and len(s) >= 4:
            dlg.append(s[:48])
        if len(dlg) >= 6:
            break
    for p in ["DATA/srt_ev/pl268/up268_00.srt",
              "DATA/srt_ev/pl268/up268_00.srt"]:
        d = a.file_bytes(by[p].toc_index)
        print("=" * 20, p)
        for line in dlg:
            print(f"  [{'HIT' if line.encode('utf-8') in d else 'miss'}] {line}")


if __name__ == "__main__":
    main()
