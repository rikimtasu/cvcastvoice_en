#!/usr/bin/env python3
"""Build the translation glossary from evidence in the archive.

Sources (all inside the archive, no guessing):
  * work/segments.json ...... clean on-screen strings (trust-message names,
    short location/system strings, direction verbs)
  * 2 UTF-16LE scenario .txt ... speaker roster (@...) + furigana readings
    in (...) + 地の文 locations + engine commands (do-not-translate)
  * name_sel.srt ............ name-entry prompt (protagonist is player-named)

Writes work/glossary.json + work/glossary.md
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C
from cricodecs import cpk

TXT_FILES = ["DATA/srt_ev/pl268/up268_00.txt",
             "DATA/srt_ev/pl268/up268_01.txt"]
JP_RUN = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]{2,}")
FURI = re.compile(r"([\u4e00-\u9fff]{1,6}(?:[　 ][\u4e00-\u9fff]{1,6})?)"
                  r"\s*(?:[\u3040-\u30ff]{1,10})?"
                  r"\s*[（(]([\u3040-\u30ff・ー 　]+)[）)]")
TRUST = re.compile(r"^(.+?)\s*\u3000?との信頼度が上昇した")
LOC_CAND = re.compile(r"^[\u4e00-\u9fff・ー]{2,8}$")
# speaker-slot values that are labels, not person names
LABELS = {"なし": "(no speaker frame)",
          "自分": "(protagonist; player-named - keep as-is)",
          "男性:汎用": "Generic Male",
          "女性:汎用": "Generic Female"}


def _norm(jp):
    return jp.replace("　", "").replace(" ", "").replace("・", "")


# Japanese Wikipedia ("CV 〜キャスティングボイス〜", VA-credited character
# list) gives a published reading for every name. Game bytes win on kanji
# choice: the archive has 鷺洲玲子 (洲, byte-proven) where WP prints 鷺州.
WIKI = {
 "内山紗彩": ("うちやま さあや", "Uchiyama Saaya", "竹達彩奈"),
 "十条玖美子": ("とうじょう くみこ", "Tojo Kumiko", "井上喜久子"),
 "姫乃雪彦": ("ひめの ゆきひこ", "Himeno Yukihiko", "代永翼"),
 "道場崇": ("みちば たかし", "Michiba Takashi", "千葉繁"),
 "遠野健吾": ("とおの けんご", "Tono Kengo", "小野賢章"),
 "荻原さおり": ("おぎわら さおり", "Ogiwara Saori", "沢城みゆき"),
 "クレーデン瑠仁": ("クレーデン りゅうじん", "Kreden Ryujin", "柿原徹也"),
 "大貫篤夫": ("おおぬき あつお", "Onuki Atsuo", "大塚芳忠"),
 "若杉奈々子": ("わかすぎ ななこ", "Wakasugi Nanako", "西原久美子"),
 "藤之宮小夜花": ("ふじのみや さやか", "Fujinomiya Sayaka", "名塚佳織"),
 "古川瑠璃": ("ふるかわ るり", "Furukawa Ruri", "伊瀬茉莉也"),
 "ＭＯＭＯ": ("もも", "MOMO", "伊藤かな恵"),
 "響耕輔": ("ひびき こうすけ", "Hibiki Kosuke", "近藤隆"),
 "中御門大介": ("なかみかど だいすけ", "Nakamikado Daisuke", "野島健児"),
 "鴫野巴菜": ("しぎの はな", "Shigino Hana", "日高のり子"),
 "菅原よしあき": ("すがわら よしあき", "Sugawara Yoshiaki", "三ツ矢雄二"),
 "神崎史之": ("かんざき ふみゆき", "Kanzaki Fumiyuki", "羽多野渉"),
 "中嶋由希也": ("なかじま ゆきや", "Nakajima Yukiya", "伊藤健太郎"),
 "平沢亜美": ("ひらさわ あみ", "Hirasawa Ami", "久川綾"),
 "波野あきら": ("なみの あきら", "Namino Akira", "野中藍"),
 "壱式琴音": ("いっしき ことね", "Isshiki Kotone", "三上枝織"),
 "鷹城好一": ("ようじょう こういち", "Yojo Koichi", "緑川光"),
 "時任千歳": ("ときとう ちとせ", "Tokito Chitose", "津田健次郎"),
 "佐藤博一": ("さとう ひろかず", "Sato Hirokazu", "松風雅也"),
 "東堂エレナ": ("とうどう エレナ", "Todo Elena", "白石涼子"),
 "東堂エレナクリュチェフスキー": ("とうどう・エレナ・クリュチェフスキー",
    "Todo Elena Klyuchefsky", "白石涼子"),
 "八尾伊月": ("やお いづき", "Yao Izuki", "相沢舞"),
 "瀬羽優": ("せば すぐる", "Seba Suguru", "前野智昭"),
 "成宮隼": ("なりみや しゅん", "Narimiya Shun", "興津和幸"),
 "各務原昌秋": ("かがみはら まさあき", "Kagamihara Masaaki", "私市淳"),
 "早乙女透": ("さおとめ とおる", "Saotome Toru", "阪口大助"),
 "小野坂秋": ("おのさか あき", "Onosaka Aki", "松野太紀"),
 "鷺洲玲子": ("さぎす れいこ", "Sagisu Reiko", "今井麻美"),
 "戸山愛": ("とやま めぐみ", "Toyama Megumi", "折笠愛"),
 "代官奈津美": ("だいかん なつみ", "Daikan Natsumi", "明坂聡美"),
 "卯月陽奈": ("うづき ひな", "Uzuki Hina", "金元寿子"),
 "狐神寧々": ("こがみ ねね", "Kogami Nene", "雪野五月"),
 "眞田大樹": ("さなだ だいき", "Sanada Daiki", "上田燿司"),
 "獅之谷クリス": ("しのたに クリス", "Shinotani Chris", "置鮎龍太郎"),
 "相葉健": ("あいば けん", "Aiba Ken", "石川英郎"),
 "伴勇次": ("ばん ゆうじ", "Ban Yuji", "赤羽根健治"),
 "星冥子": ("ほし めいこ", "Hoshi Meiko", "後藤沙緒里"),
 "咲良瑞樹": ("さくら みずき", "Sakura Mizuki", "斎賀みつき"),
 "南野蝶子": ("みなみの ちょうこ", "Minamino Choko", "小林ゆう"),
 "静稀香奈": ("しずき かな", "Shizuki Kana", "大本眞基子"),
 "瀧玲華": ("たき れいか", "Taki Reika", "浅川悠"),
 "牙龍院鏡夜": ("がりゅういん きょうや", "Garyuin Kyoya", "島崎信長"),
 "西宮寺美礼": ("さいぐうじ みれい", "Saiguji Mirei", "田中理恵"),
 "香坂真冬": ("こうさか まふゆ", "Kosaka Mafuyu", "たかはし智秋"),
 "久保園敦史": ("くぼぞの あつし", "Kubozono Atsushi", "森田成一"),
 "太田公一郎": ("おおた こういちろう", "Ota Koichiro", "小山力也"),
}


def main():
    a = cpk.load(str(C.ORIG))
    by = {f.full_path: f for f in a.files}
    glo = {"characters": {}, "locations": {}, "terms": {},
           "labels": {}, "do_not_translate": [], "notes": []}

    def char(jp, en=None, ev=None, reading=None, status=None):
        if jp in LABELS or not JP_RUN.search(jp):
            return
        c = glo["characters"].setdefault(jp, {"en": None, "reading": None,
                                              "status": "unverified",
                                              "evidence": []})
        if en and not c["en"]:
            c["en"] = en
        if reading:
            c["reading"] = reading
        if status:
            c["status"] = status
        if ev and ev not in c["evidence"]:
            c["evidence"].append(ev)

    # ---- 1. scenario scripts ------------------------------------------------
    speakers = Counter()
    commands = Counter()
    furigana = {}
    txt_lines = 0
    for p in TXT_FILES:
        f = by.get(p)
        if f is None:
            glo["notes"].append(f"missing {p}")
            continue
        t = a.file_bytes(f.toc_index).decode("utf-16-le", "replace")
        for raw in t.splitlines():
            ln = raw.strip()
            if not ln:
                continue
            txt_lines += 1
            if ln.startswith(";"):
                continue
            if ln.startswith("@"):
                cmd, _, rest = ln[1:].partition("\t")
                cmd = cmd.strip()
                commands[cmd] += 1
                sp = rest.split("\t")[0].strip() if rest else ""
                if sp:
                    speakers[sp] += 1
                continue
            if ln.startswith("/") or ln.startswith("[") or \
                    ln.startswith("<") or ln.startswith("$"):
                commands[ln.split("\t")[0][:24]] += 1
                continue
            if ln.startswith("地の文") or ln.startswith("女性名前変更") or \
                    ln.startswith("キャラロード") or ln.startswith("ボイスロード"):
                parts = ln.split()
                if parts:
                    commands[parts[0]] += 1
                    for tok in parts[1:]:
                        if JP_RUN.fullmatch(tok):
                            speakers[tok] += 1
                continue
            for m in FURI.finditer(ln):
                furigana[m.group(1)] = m.group(2).strip().strip("　 ")
            for m in JP_RUN.finditer(ln):
                pass
    glo["notes"].append(f"scenario txt lines scanned: {txt_lines}")
    for sp, c in speakers.most_common():
        char(sp, ev=f"scenario-speaker x{c}")

    # corresponding compiled .srt?
    sibs = [f.full_path for f in by.values()
            if "up268" in f.full_path]
    glo["notes"].append(f"up268 siblings in archive: {sorted(sibs)}")

    # ---- 2. trust names from clean segments ---------------------------------
    seg = json.loads((C.WORK / "segments.json")
                     .read_bytes().decode("utf-8-sig", "surrogatepass"))
    trust_names = Counter()
    for rec in seg.values():
        for s in rec["seg"]:
            m = TRUST.match(s["jp"].strip())
            if m:
                nm = m.group(1).strip().strip("\u3000 ")
                if 2 <= len(nm) <= 10:
                    trust_names[nm] += 1
    for nm, c in trust_names.most_common():
        char(nm, ev=f"trust-message x{c}")

    # ---- 3. short location candidates ----------------------------------------
    locs = Counter()
    for rec in seg.values():
        for s in rec["seg"]:
            t = s["jp"].strip().strip("\u3000 ")
            if LOC_CAND.match(t) and len(t.encode("utf-8",
                                                  "surrogateescape")) <= 30:
                locs[t] += 1
    for loc, c in locs.most_common(80):
        glo["locations"][loc] = {"count": c}

    # ---- 4. apply furigana readings ------------------------------------------
    # only to bare names (kj optionally + honorific), never to phrases like
    # 巴菜の友達 which merely contain the kanji
    import re as _re
    for kj, rd in furigana.items():
        kj_norm = kj.replace("\u3000", "").replace(" ", "")
        pat = _re.compile(rf"^{_re.escape(kj_norm)}(ちゃん|さん|くん|様)?$")
        for jp in list(glo["characters"]):
            norm = jp.replace("\u3000", "").replace(" ", "")
            if pat.match(norm):
                glo["characters"][jp]["reading"] = rd
                glo["characters"][jp]["status"] = \
                    "furigana (shipped scenario file)"

    # verified / kana-grounded entries (evidence, not guesses)
    if "鴫野巴菜" in glo["characters"]:
        glo["characters"]["鴫野巴菜"]["en"] = "Shigino Hana"
        glo["characters"]["鴫野巴菜"]["status"] = \
            "furigana (shipped scenario file)"
    if "波野あきら" in glo["characters"]:
        # given name is written in kana in-game; family has one standard reading
        glo["characters"]["波野あきら"]["reading"] = "なみの あきら"
        glo["characters"]["波野あきら"]["en"] = "Namino Akira"
        glo["characters"]["波野あきら"]["status"] = \
            "kana-given; standard family reading"
    if "巴菜の友達" in glo["characters"]:
        glo["characters"]["巴菜の友達"]["en"] = "Hana's friend"
        glo["characters"]["巴菜の友達"]["status"] = \
            "dynamic speaker label (scenario rename command)"
    # in-game furigana cheval: 矢神京磨 (fictional-work character, x4)
    glo["characters"]["矢神京磨"] = {
        "en": "Yagami Kyoma", "reading": "やがみ きょうま",
        "status": "in-game furigana (segment x4)",
        "evidence": ["segment 矢神京磨（やがみ きょうま） x4"]}
    # minor/related names from batch translation (unverified readings)
    for _jp, _rd, _en, _ev in [
            ("壱式静音", "しずね", "Isshiki Shizune",
             "batch tr: Isshiki family, distinct from Kotone"),
            ("十条曜一郎", "よういちろう", "Tojo Yoichiro",
             "batch tr: Tojo family name plate"),
            ("三村曜一郎", "よういちろう", "Mimura Yoichiro",
             "batch tr: name plate"),
            ("遠野謙", "けん", "Tono Ken",
             "batch tr: Tono Kengo's father, mentioned as 遠野 謙の息子"),
            ("芹沢かすみ", "かすみ", "Serizawa Kasumi",
             "batch tr: kana-given; class 2, distinct from Shion"),
            ("名張螢", "ほたる", "Nabari Hotaru",
             "batch tr: Hareo Osaka PR lady"),
            ("押田", "おしだ", "Oshida",
             "batch tr: script-wrecking-movie director"),
            ("優希", "ゆうき", "Yuki", "batch tr: power-type VA"),
            ("かなえ", "かなえ", "Kanae", "batch tr: kana-given"),
            ("真美", "まみ", "Mami",
             "batch tr: Hirasawa Ami's twin"),
            ("ミミ", "ミミ", "Mimi", "batch tr: kana-given"),
            ("生野", "せいの", "Seino", "batch tr: recurring minor name"),
            ("神崎美奈", "かんざき みな", "Kanzaki Mina",
             "batch tr: self-introduction; family reading per Fumiyuki"),
    ]:
        if _jp not in glo["characters"]:
            glo["characters"][_jp] = {
                "en": _en, "reading": _rd, "status": "unverified",
                "evidence": [_ev]}
    # GAME BYTES on Kanzaki: 4/4 furigana segments read ふみゆき
    # (U+3075 U+307F U+3086 U+304D, codepoint-verified). WP's ふみのり stands
    # alone against game bytes + IMDb. FLIPPED to Fumiyuki per user
    # re-confirmation; all tr files sedded (same length, budgets unaffected).
    if "神崎史之" in glo["characters"]:
        glo["characters"]["神崎史之"]["evidence"].append(
            "GAME BYTES: 4/4 furigana segments read かんざき ふみゆき "
            "(codepoint-verified); conflicts with WP ふみのり")
    # codepoint-verified roster addition: 芹沢詩音 (せりざわ しおん)
    if "芹沢詩音" not in glo["characters"]:
        glo["characters"]["芹沢詩音"] = {
            "en": "Serizawa Shion", "reading": "せりざわ しおん",
            "status": "in-game furigana (codepoint-verified)",
            "evidence": ["segment furigana, codepoint-verified"]}
    for jp, en in LABELS.items():
        glo["labels"][jp] = en
    # ASCII MOMO is the halfwidth twin of fullwidth ＭＯＭＯ (x88 trust msgs)
    if "MOMO" in glo["characters"]:
        glo["characters"].pop("MOMO")
        glo["notes"].append("ASCII 'MOMO' (x2) folded into ＭＯＭＯ")

    # ---- 4b. Wikipedia readings (VA-credited, published) ----------------------
    # Furigana/kana-grounded entries keep their (agreeing) status; everything
    # else takes the WP reading + romanization. WP-only names (DLC trio,
    # full-form Elena, staff 一心耀子) are added with a wikipedia-only note.
    for jp in list(glo["characters"]):
        key = _norm(jp)
        if key in WIKI:
            rd, en, va = WIKI[key]
            c = glo["characters"][jp]
            c["reading"] = rd
            c["en"] = en
            if c["status"] == "unverified":
                c["status"] = "ja.wikipedia (VA-credited)"
            c["evidence"].append(f"ja.wikipedia (VA: {va})")
    for key, (rd, en, va) in WIKI.items():
        if key in ("東堂エレナクリュチェフスキー",):
            jp = "東堂・エレナ・クリュチェフスキー"
        else:
            jp = key
        if jp not in glo["characters"] and _norm(jp) not in \
                {_norm(k) for k in glo["characters"]}:
            glo["characters"][jp] = {"en": en, "reading": rd,
                                     "status": "ja.wikipedia (VA-credited)",
                                     "evidence": [f"ja.wikipedia (VA: {va}); "
                                                  "not in GameData text"]}
    # ---- 4c. Fandom English-name suggestions -------------------------------
    # (japanese-voiceover.fandom.com, "CV: Casting Voice (2014)", read via
    # the MediaWiki API - the HTML pages are Cloudflare-walled).
    # Fandom uses Western order + macrons; we keep family-first ASCII
    # (game presents names family-first; macrons dropped for font safety).
    # Where Fandom conflicts with WP's explicit furigana, WP wins (flagged).
    FANDOM_FIX = {
        # Fandom "Kleden" adopted for クレーデン (katakana surname)
        "クレーデン瑠仁": ("クレーデン りゅうじん", "Kleden Ryujin"),
        # Fandom keeps katakana クリス as "Kurisu", not "Chris"
        "獅之谷クリス": ("しのたに クリス", "Shinotani Kurisu"),
        # WP gives no reading; Fandom does
        "一心耀子": ("いっしん ようこ", "Isshin Yoko"),
    }
    for jp, (rd, en) in FANDOM_FIX.items():
        c = glo["characters"].get(jp)
        if c is None:
            glo["characters"][jp] = {
                "en": en, "reading": rd,
                "status": "fandom wiki (no WP reading)",
                "evidence": ["fandom: staff/voice role; absent from "
                             "GameData text"]}
        else:
            c["reading"] = rd
            c["en"] = en
            c["status"] = "fandom wiki"
            c["evidence"].append("fandom English spelling adopted")
    # agreement sweep: WP + Fandom concur on everything else
    AGREE_SKIP = {_norm(k) for k in
                  ("時任千歳", "成宮隼", "東堂エレナ", "クレーデン瑠仁",
                   "獅之谷クリス", "一心耀子", "内山紗彩", "鷺洲玲子",
                   "東堂・エレナ・クリュチェフスキー")}
    for jp, c in glo["characters"].items():
        if _norm(jp) not in AGREE_SKIP and \
                c["status"] in ("ja.wikipedia (VA-credited)",
                                "furigana (shipped scenario file)",
                                "kana-given; standard family reading"):
            c["evidence"].append("fandom spells it the same")
            if c["status"] == "ja.wikipedia (VA-credited)":
                c["status"] = "wikipedia + fandom agree"
    glo["notes"].append(
        "Fandom conflicts, WP furigana kept: 時任千歳 ときとう (Fandom "
        "'Sakito'); 成宮隼 しゅん (Fandom 'Jun'); 東堂エレナ Elena "
        "(Fandom 'Erina'; Elena matches katakana エレナ + Russian Елена)")
    glo["notes"].append(
        "kanji kept from game bytes, both wikis differ: 鷺洲玲子 (game) vs "
        "鷺州玲子 (WP+Fandom); 内山紗彩 (game, WP) vs 内山沙彩 (Fandom)")
    # ---- 4d. IMDb full cast (tt34966594, pasted by user) --------------------
    # Western order + macrons normalized to our convention for comparison.
    # Result: 45 full agreements; 4 same-reading system variants (Hepburn
    # kept); 1 real conflict (神崎史之); 3 absent (IMDb silent).
    IMDB_SAME = {_norm(k) for k in
                 ("八尾伊月", "伴勇次", "代官奈津美", "瀧玲華", "道場崇",
                  "星冥子", "鴫野巴菜", "平沢亜美", "鷺洲玲子", "十条玖美子",
                  "古川瑠璃", "相葉健", "ＭＯＭＯ", "中嶋由希也",
                  "クレーデン瑠仁", "卯月陽奈", "各務原昌秋", "響耕輔",
                  "太田公一郎", "瀬羽優", "佐藤博一", "小野坂秋", "鷹城好一",
                  "壱式琴音", "菅原よしあき", "久保園敦史", "藤之宮小夜花",
                  "若杉奈々子", "中御門大介", "波野あきら", "獅之谷クリス",
                  "成宮隼", "戸山愛", "大貫篤夫", "咲良瑞樹", "早乙女透",
                  "荻原さおり", "牙龍院鏡夜", "東堂エレナ", "香坂真冬",
                  "内山紗彩", "西宮寺美礼", "時任千歳", "眞田大樹",
                  "姫乃雪彦", "南野蝶子", "遠野健吾", "静稀香奈",
                  "狐神寧々")}
    for jp, c in glo["characters"].items():
        if _norm(jp) in IMDB_SAME:
            c["evidence"].append("imdb cast list agrees")
            if c["status"] == "wikipedia + fandom agree":
                c["status"] = "wikipedia + fandom + imdb agree"
            elif c["status"] == "fandom wiki":
                c["status"] = "fandom + imdb agree"
    glo["notes"].append(
        "RESOLVED (user re-confirmed after byte proof): 神崎史之 = Fumiyuki. "
        "Codepoint audit proved all 4 in-game furigana read ふみゆき; the "
        "earlier 'Fuminori' came from console mojibake (ゆ misrendered). "
        "IMDb agreed; only WP's ふみのり dissents. Lesson: verify readings "
        "by codepoint, never console rendering.")
    glo["notes"].append(
        "IMDb same-reading variants (Hepburn kept): 南野蝶子 Choko "
        "(IMDb 'Tyouko', Kunrei); 静稀香奈 Shizuki (IMDb 'Sizuki', Kunrei); "
        "遠野健吾 Tono (IMDb 'Tohno'); 大貫篤夫 Onuki (IMDb 'Ohnuki')")
    glo["notes"].append(
        "IMDb confirms Fandom adoptions: Kleden, Kurisu Shinotani, Elena "
        "(over Fandom's 'Erina'); confirms Tokito (over 'Sakito') and Shun "
        "(over 'Jun'). Silent on 一心耀子 + full-form Elena.")
    glo["notes"].append(
        "name order: family-first (as the game presents names); Fandom/IMDb "
        "use Western order. Macrons (Ō, ū) normalized to ASCII for font "
        "safety")

    # ---- 5. fixed terms (read directly off high-frequency strings) -----------
    glo["terms"] = {
        "プロデューサー": {"en": "Producer",
                        "evidence": "3104 files; @i<0> tag kept inline"},
        "演技": {"en": "acting / performance",
               "evidence": "core direction noun (演技指導 = direction)"},
        "信頼度": {"en": "Trust",
                "evidence": "X との信頼度が上昇した = Trust with X has risen"},
        "ボイスグランプリ": {"en": "Voice Grand Prix",
                        "evidence": "awards-ceremony event strings"},
        "グランプリ": {"en": "Grand Prix", "evidence": "グランプリ！？"},
        "授賞式": {"en": "awards ceremony",
                "evidence": "ボイスグランプリ授賞式を閉会させて頂きます"},
        "収録": {"en": "recording (session)", "evidence": "大作の収録"},
        "台本": {"en": "script", "evidence": "台本に書いてる / 今度のお仕事の台本"},
        "インタビュー": {"en": "interview", "evidence": "撮影とインタビュー"},
        "撮影": {"en": "shoot / filming", "evidence": "撮影とインタビューがあるなら"},
        "指導": {"en": "direction / coaching",
               "evidence": "演技指導ありがとう / 特に指導はなし"},
        "指示出し": {"en": "giving directions",
                  "evidence": "どう指示出しをしようかな"},
        "声優": {"en": "voice actor", "evidence": "声優さんを信じよう"},
        "自分": {"en": "(self / protagonist speaker label)",
               "evidence": "@メッセージ speaker; player-named, keep as-is"},
        "名前を入力してください": {"en": "Please enter a name.",
                            "evidence": "name_sel.srt (name-entry screen)"},
        "師匠": {"en": "Master (addressed Sensei)",
               "evidence": "in-game furigana せんせい x25"},
        "翔クリエイティブ": {"en": "Sho Creative",
                      "evidence": "talent agency (Kleden Ryujin affiliation line)"},
        "翔クリ": {"en": "Shokuri",
                 "evidence": "short for Sho Creative agency"},
    }
    glo["do_not_translate"] = [
        "@i<0> (player-name variable tag; keep inline)",
        "@n (line break), U+22A5 / U+22BF page terminators",
        "<~NNNNNN> voice-playback tags",
        "@メッセージ / @フェイスメッセージ / 地の文 / キャラロード / "
        "ボイスロード / 女性名前変更 (scenario commands, .txt only)",
        "/背景2 / /バストアップ / [...] / <...> / $start "
        "(scenario commands, .txt only)",
        "srtbgNNN, haikeisita, FSRT, XSRT and other ASCII resource keys",
    ]

    (C.WORK / "glossary.json").write_bytes(
        json.dumps(glo, ensure_ascii=False, indent=1)
        .encode("utf-8", "surrogatepass"))

    md = ["# CV Casting Voice - translation glossary",
          "",
          "> Sources: game bytes (trust messages, scenario scripts, furigana) "
          "+ ja.wikipedia VA-credited readings + Fandom English spellings "
          "+ IMDb full cast (user-supplied). Game bytes win on kanji; WP "
          "furigana wins on readings; Fandom wins on katakana-name spellings. "
          "Anything still `unverified` must be confirmed before it ships "
          "in-game.",
          "",
          f"## Characters ({len(glo['characters'])})",
          "",
          "| Japanese | Reading | Status | English | Evidence |",
          "|---|---|---|---|"]
    for jp, c in sorted(glo["characters"].items(), key=lambda kv: kv[0]):
        rd = c["reading"] or "-"
        ev = "; ".join(c["evidence"])
        md.append(f"| {jp} | {rd} | {c['status']} | {c['en'] or '-'} | {ev} |")
    md += ["",
           "## Speaker labels (not person names - do not romanize)",
           "",
           "| Label | Meaning |",
           "|---|---|"]
    for jp, en in glo["labels"].items():
        md.append(f"| {jp} | {en} |")
    md += ["",
           f"## Short strings ({len(glo['locations'])}) - locations AND name plates",
           "",
           "Short kanji strings appear both as location cards and as bare ",
           "name plates, so both live here. Resolve per context when translating.",
           "",
           "| Japanese | Segments |",
           "|---|---|"]
    for loc, v in sorted(glo["locations"].items(), key=lambda kv: -kv[1]["count"])[:60]:
        md.append(f"| {loc} | {v['count']} |")
    md += ["",
           "## Terms",
           "",
           "| Japanese | English | Evidence |",
           "|---|---|---|"]
    for jp, v in glo["terms"].items():
        md.append(f"| {jp} | {v['en']} | {v['evidence']} |")
    md += ["", "## Do not translate", ""]
    for d in glo["do_not_translate"]:
        md.append(f"- {d}")
    md += ["", "## Notes", ""]
    for nt in glo["notes"]:
        md.append(f"- {nt}")
    (C.WORK / "glossary.md").write_bytes(
        "\n".join(md).encode("utf-8", "surrogatepass"))

    rep = [f"characters : {len(glo['characters'])}",
           f"locations  : {len(glo['locations'])}",
           f"terms      : {len(glo['terms'])}",
           f"speakers in scenario txt: {len(speakers)}",
           f"furigana readings mined : {len(furigana)}",
           "top scenario speakers:"]
    for sp, c in speakers.most_common(12):
        rep.append(f"  x{c:<4} {sp}")
    if furigana:
        rep.append("furigana:")
        for k, v in list(furigana.items())[:20]:
            rep.append(f"  {k} -> {v}")
    rep.append("up268 siblings: " + ", ".join(sorted(sibs)))
    txt = "\n".join(rep)
    print(txt)
    (C.WORK / "glossary.txt").write_bytes(txt.encode("utf-8", "replace"))


if __name__ == "__main__":
    main()
