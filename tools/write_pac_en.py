#!/usr/bin/env python3
"""Write the filled Track-A translation map (work/pac_en.json) as UTF-8."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C

EN = {
    "はじまり": "Beginning",
    "正規軍": "Regular Army",
    "剣と剣": "Sword and Sword",
    "宇宙へ": "To Space",
    "仲間": "Comrades",
    "再殺部隊": "Reaper Unit",
    "楽園": "Paradise",
    "決戦": "Decisive Battle",
    "新たな扉": "A New Door",
    "天海春香": "Haruka",
    "秋月律子": "Ritsuko",
    "如月千早": "Chihaya",
    "菊地真": "Makoto",
    "萩原雪歩": "Yukiho",
    "星井美希": "Miki",
    "四条貴音": "Takane",
    "我那覇響": "Hibiki",
    "出会い": "The Meeting",
    "記者会見": "Press Conf",
    "前編": "Part 1",
    "事件発生": "The Incident",
    "後編": "Part 2",
    "追跡": "Chase",
    "桃太郎伝": "Momotaro",
    "旅立ち": "Departure",
    "鬼ヶ島": "Onigashima",
    "水瀬伊織": "Iori",
    "吹替台本": "Dub Script",
    "童話朗読": "Fairy Tale",
    "パテオ": "Pateo",
    "健康食品": "Health Food",
    "内山　紗彩": "Uchiyama Saaya",
    "神崎　史之": "Kanzaki Fumio",
    "鷺洲　玲子": "Sagisu Reiko",
    "鴫野　巴菜": "Shigino Tomona",
    "遠野　健吾": "Tono Kengo",
    "道場　崇": "Dojo Takashi",
    "佐々木　崇": "Sasaki Takashi",
    "荻原　さおり": "Hagiwara Saori",
    "成宮　隼": "Narimiya Jun",
    "戸山　愛": "Toyama Ai",
    "クレーデン　瑠仁": "Clayden Ruito",
    "大貫　篤夫": "Onuki Atsuo",
    "太田　公一郎": "Ota Koichiro",
    "十条　玖美子": "Jujo Kumiko",
    "中嶋　由希也": "Nakajima Yukiya",
    "眞田　大樹": "Sanada Daiki",
    "若杉　奈々子": "Wakasugi Nanako",
    "菅原　よしあき": "Sugawara Yoshiaki",
    "獅之谷　クリス": "Shishinoya Chris",
    "相葉　健": "Aiba Ken",
    "各務原　昌秋": "Kagamihara Masaaki",
    "平沢　亜美": "Hirasawa Ami",
    "瀧　玲華": "Taki Reika",
    "西宮寺　美礼": "Nishinomiya Mirei",
    "咲良　瑞樹": "Sakura Mizuki",
    "早乙女　透": "Saotome Toru",
    "瀬羽　優": "Seba Yu",
    "波野　あきら": "Namino Akira",
    "壱式　琴音": "Ichishiki Koto",
    "静稀　香奈": "Shizumaki Kana",
    "狐神　寧々": "Kogami Nene",
    "久保園　敦史": "Kubozono Atsushi",
    "鷹城　好一": "Takajo Koichi",
    "香坂　真冬": "Kosaka Mafuyu",
    "南野　蝶子": "Namino Choko",
    "藤之宮　小夜花": "Fujinomiya Sayaka",
    "卯月　陽奈": "Uzuki Hina",
    "時任　千歳": "Tokito Chitose",
    "佐藤　博一": "Sato Hirokazu",
    "星　冥子": "Hoshi Meiko",
    "伴　勇次": "Tomoro Yuji",
    "牙龍院　鏡夜": "Garyuin Kyoya",
    "小野坂　秋": "Onosaka Aki",
    "響　耕輔": "Hibiki Koso",
    "姫乃　雪彦": "Himeno Yukihiko",
    "古川　瑠璃": "Furukawa Ruri",
    "東堂　エレナ": "Todo Elena",
    "中御門　大介": "Nakamikado Daisuke",
    "代官　奈津美": "Daikan Natsumi",
    "八尾　伊月": "Yao Izuki",
}


def main():
    p = C.WORK / "pac_en.json"
    p.write_text(json.dumps(EN, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {len(EN)} translations -> {p}")


if __name__ == "__main__":
    main()
