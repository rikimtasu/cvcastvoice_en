#!/usr/bin/env python3
"""Cross-check Wikipedia readings against actual game bytes:
1. Suites 鷺洲 vs 鷺州 - which kanji is really in the archive?
2. Is 一心耀子 (staff, no WP reading) present?
3. Does the game use 東堂エレナ (short) or the full クリュチェフスキー form?
4. Which glossary names have no Wikipedia match (and vice versa)?"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

WIKI = ["内山紗彩", "十条玖美子", "姫乃雪彦", "道場崇", "遠野健吾",
        "荻原さおり", "クレーデン瑠仁", "大貫篤夫", "若杉奈々子",
        "藤之宮小夜花", "古川瑠璃", "ＭＯＭＯ", "響耕輔", "中御門大介",
        "鴫野巴菜", "菅原よしあき", "神崎史之", "中嶋由希也", "平沢亜美",
        "波野あきら", "壱式琴音", "鷹城好一", "時任千歳", "佐藤博一",
        "東堂・エレナ・クリュチェフスキー", "八尾伊月", "瀬羽優", "成宮隼",
        "各務原昌秋", "早乙女透", "小野坂秋", "鷺州玲子", "戸山愛",
        "代官奈津美", "卯月陽奈", "狐神寧々", "眞田大樹", "獅之谷クリス",
        "相葉健", "伴勇次", "星冥子", "咲良瑞樹", "南野蝶子", "静稀香奈",
        "瀧玲華", "牙龍院鏡夜", "西宮寺美礼", "香坂真冬", "久保園敦史",
        "太田公一郎", "一心耀子"]


def main():
    a = cpk.load(str(C.ORIG))
    fa = a.files
    g = json.loads((C.WORK / "glossary.json")
                   .read_bytes().decode("utf-8", "surrogatepass"))
    mine = set(g["characters"])

    # 1+2+3: byte-level presence over the whole archive (single pass)
    needles = {"鷺洲玲子": "鷺洲玲子".encode("utf-8"),
               "鷺州玲子": "鷺州玲子".encode("utf-8"),
               "一心耀子": "一心耀子".encode("utf-8"),
               "東堂エレナ": "東堂エレナ".encode("utf-8"),
               "クリュチェフスキー": "クリュチェフスキー".encode("utf-8"),
               "東堂・エレナ": "東堂・エレナ".encode("utf-8")}
    found = {k: [] for k in needles}
    for idx, f in enumerate(fa):
        try:
            d = a.file_bytes(f.toc_index)
        except Exception:
            continue
        if not d:
            continue
        for k, b in needles.items():
            if b in d and len(found[k]) < 4:
                found[k].append(f.full_path)
    print("--- byte presence ---")
    for k, v in found.items():
        print(f"  {k}: {len(v)}+ files, e.g. {v[:2]}")

    # 4: set differences
    wiki_nospace = {w.replace("・", "").replace("　", "").
                    replace(" ", "") for w in WIKI}
    mine_nospace = {m.replace("\u3000", "") for m in mine}
    print("--- in game but NOT on wikipedia ---")
    for m in sorted(mine_nospace - wiki_nospace -
                    {"東堂エレナ", "鷺洲玲子"}):
        print(f"  {m}")
    print("--- on wikipedia but NOT in game glossary ---")
    for w in sorted(wiki_nospace - mine_nospace -
                    {"東堂・エレナ・クリュチェフスキー", "鷺州玲子"}):
        print(f"  {w}")


if __name__ == "__main__":
    main()
