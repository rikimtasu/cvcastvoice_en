#!/usr/bin/env python3
"""Apply review fixes across the whole corpus. JSON-safe, budget re-checked.

Order: explicit spelling fixes -> western-order swaps -> generic
honorific strip (with skips). Every change is length-neutral or shorter.
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C

# (old, new) substring fixes, in application order
FIXES = [
    ("Yukihiko Hime-no-kun's", "Himeno Yukihiko's"),
    ("Hime-no-kun", "Himeno"),
    ("Narumiya", "Narimiya"),
    ("Shishitani", "Shinotani"),
    ("Chris Shinotani", "Shinotani Kurisu"),
    ("Sayoka", "Sayaka"),
    ("Sayo-chan", "Sayaka"),
    ("Ogihara", "Ogiwara"),
    ("Kuru-kun", "Kurusu"),
    ("Kagurai Kyouya", "Kagurai Kyoya"),
    ("P-san", "Mr. P"),
    ("Nee-san", "sis"),
    ("nee-san", "sis"),
    ("Onee-san", "sis"),
    ("onee-chan", "sis"),
    ("Nee-sama", "sis"),
    ("Onii-chan", "bro"),
    # western-order -> family-first (same length)
    ("Meiko Hoshi", "Hoshi Meiko"),
    ("Koichiro Ota", "Ota Koichiro"),
    ("Elena Todo", "Todo Elena"),
    ("Daisuke Nakamikado", "Nakamikado Daisuke"),
    ("Nanako Wakasugi", "Wakasugi Nanako"),
    ("Toru Saotome", "Saotome Toru"),
    ("Kana Shizuki", "Shizuki Kana"),
    ("Saaya Uchiyama", "Uchiyama Saaya"),
    ("Kyoma Yagami", "Yagami Kyoma"),
    ("Shion Serizawa", "Serizawa Shion"),
    ("Choko Minamino", "Minamino Choko"),
    ("Mizuki Sakura", "Sakura Mizuki"),
    ("Kosuke Hibiki", "Hibiki Kosuke"),
    ("Kengo Tono", "Tono Kengo"),
]
HONOR = re.compile(r"\b([A-Za-z]+)-(san|chan|sama|kun|dono|chin|sensei)\b")
SKIP_HONOR = ("hito-san",)   # gag nickname, leave intact


def main():
    order = json.loads((C.WORK / "order.json")
                       .read_bytes().decode("utf-8-sig", "surrogatepass"))
    n_fix = n_files = 0
    over = []
    for p in sorted(C.WORK.glob("tr_*.json")):
        tr = json.loads(p.read_bytes().decode("utf-8-sig", "surrogatepass"))
        dirty = False
        for k, v in tr.items():
            nv = v
            for old, new in FIXES:
                if old in nv:
                    nv = nv.replace(old, new)
            def sub(m):
                return m.group(0) if m.group(0) in SKIP_HONOR else m.group(1)
            nv = HONOR.sub(sub, nv)
            if nv != v:
                b = order[k]["b"]
                if len(nv.encode()) > b:
                    over.append((p.name, k, b, nv[:70]))
                    continue
                tr[k] = nv
                dirty = True
                n_fix += 1
        if dirty:
            p.write_bytes(json.dumps(tr, ensure_ascii=False).encode("utf-8"))
            n_files += 1
    print(f"fixed {n_fix} entries in {n_files} files")
    for f, k, b, v in over:
        print(f"  OVER {f}/{k} b={b} {v!r}")


if __name__ == "__main__":
    main()
