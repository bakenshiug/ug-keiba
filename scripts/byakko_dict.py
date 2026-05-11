"""
🐅 白虎加点辞書 v0.2（2026-05-11更新 / 5/17本番運用）
「変」を司る西方金の神 ─ 陣営の物理的・意志的な変化を検出

データソース合議:
  Layer 1: JRDB n_live ─ 公式申告（初B/再B/B外）
  Layer 2: keibabook 出馬表 ─ CSS class .kigou.blink で初B検出
  Layer 3: keibabook 短評   ─ 装具・条件「変」キーワード
  Layer 4: 陣営フィルター   ─ 関西→関東遠征／戦略家厩舎／外国人騎手

スコア階層:
  >= 5.0 : ⚡⚡⚡ 白虎降臨（穴絶対採用）
  >= 3.0 : ⚡⚡ 強白虎（穴候補上位）
  >= 1.5 : ⚡ 軽白虎（穴候補）
  <  1.5 : 無印（穴は言霊4位で埋める）
"""

# ─── Layer 2: keibabook 出馬表 CSS class 抽出 ───
# 出馬表で「初B」は <span class="kigou blink">B</span> として描画される
# 「継続B」は <td>B</td> のみ（spanなし）
KEIBABOOK_CSS = {
    "blink_B_selector": "span.kigou.blink",  # 初B検出セレクタ
    "plain_B_td":       "td",                # 継続B（spanなし）
    # 区別：blink付き → 初B、なし → 継続
}


def detect_init_b_from_keibabook(html_or_soup):
    """
    keibabook 出馬表のHTMLから初B馬の馬名リストを返す。
    Beautifulsoup4 で .kigou.blink を含む馬名を抽出。

    Args:
        html_or_soup: BeautifulSoup object か HTML文字列
    Returns:
        list[str]: 初B確認馬名リスト
    """
    try:
        from bs4 import BeautifulSoup
        soup = html_or_soup if hasattr(html_or_soup, "select") else BeautifulSoup(html_or_soup, "html.parser")
    except ImportError:
        return []

    init_b_horses = []
    # blink spanを持つtrを探す
    for span in soup.select("span.kigou.blink"):
        tr = span.find_parent("tr")
        if not tr:
            continue
        # 同じ行から馬名抽出
        name_link = tr.find("a", href=lambda h: h and "/uma/" in h)
        if name_link:
            init_b_horses.append(name_link.get_text(strip=True))
    return init_b_horses


# ─── Layer 4: 陣営フィルター（勝負気配シグナル） ───

# 戦略家厩舎（初B装着・遠征の意味合いが特に重い）
STRATEGIC_TRAINERS = {
    "矢作":   1.0,   # 矢作芳人 ─ 世界戦略家・適性探索の名手
    "国枝":   0.5,   # 国枝栄
    "木村":   0.5,   # 木村哲也
    "藤原":   0.5,   # 藤原英昭
    "友道":   0.5,   # 友道康夫
    "中内田": 0.5,   # 中内田充正
    "高野":   0.5,   # 高野友和
}

# 外国人騎手（騎乗依頼自体に陣営の本気度）
FOREIGN_JOCKEYS = {
    "ルメー":   0.8, "ルメール": 0.8,  # クリストフ・ルメール
    "ディー":   0.8,                   # ミルコ・デムーロ系
    "Ｍ．ディー": 0.8,
    "デムー":   0.8, "デムーロ": 0.8,
    "レーン":   0.8,                   # ダミアン・レーン
    "モレ":     0.8, "モレイラ": 0.8,  # ジョアン・モレイラ
    "ボー":     0.8, "ボウマン": 0.8,
    "ベリー":   0.8, "ベル":   0.5,
    "シュタル": 0.5, "シュタルケ": 0.5,
    "ホー":     0.5, "ホール":   0.5,
    "ゴンサ":   0.5, "ゴンザル": 0.5,  # ゴンザルベス（直近好調）
    "ディー":   0.8,
}


def boost_for_camp(jockey: str = "", trainer: str = "", venue: str = "",
                   trainer_loc: str = "") -> tuple[float, list[str]]:
    """
    陣営フィルターによる加点。
    Args:
        jockey: 騎手名
        trainer: 調教師名
        venue: 競馬場（東京/京都/新潟など）
        trainer_loc: 厩舎所属（美=美浦/栗=栗東）
    Returns:
        (score, hits): スコア加点と発火シグナルリスト
    """
    score = 0.0
    hits = []

    # 戦略家厩舎
    for name, pt in STRATEGIC_TRAINERS.items():
        if name in (trainer or ""):
            score += pt
            hits.append(f"戦略厩舎:{name}(+{pt})")
            break

    # 外国人騎手
    for key, pt in FOREIGN_JOCKEYS.items():
        if key in (jockey or ""):
            score += pt
            hits.append(f"外国人騎手:{key}(+{pt})")
            break

    # 関西→関東遠征（栗東所属厩舎 × 関東開催）
    KANTO_VENUES = {"東京", "中山", "新潟", "福島"}
    if trainer_loc == "栗" and venue in KANTO_VENUES:
        score += 0.7
        hits.append(f"西高東低:栗東→{venue}(+0.7)")

    # 関東→関西遠征（逆パターンも陣営の意志）
    KANSAI_VENUES = {"京都", "阪神", "中京", "小倉"}
    if trainer_loc == "美" and venue in KANSAI_VENUES:
        score += 0.5
        hits.append(f"東上り:美浦→{venue}(+0.5)")

    return score, hits

# ─── Layer 1: JRDB n_live 物理シグナル ───
# ⚠ ニック哲学：継続は「変」ではない。初装着 or 外す or 再装着のみ「変」
JRDB_BURI = {
    "初B":  3.0,   # 初ブリンカー（穴の温床）
    "再B":  2.5,   # 再ブリンカー（一度外して再装着＝陣営の試行錯誤シグナル）
    "B外": 2.0,   # ブリンカー外し（前走Bから外し＝矯正卒業 or 別アプローチ）
    "B":   0.0,   # 継続ブリンカー（変ではない・加点ゼロ）
}

JRDB_BAGU = {
    "＊": 0.5,    # 何らかの馬具装着
}

# ─── Layer 2: keibabook 短評「変」キーワード辞書 ───
HENKEY = {
    # ── 装具変（最高加点） ──
    "遮眼革":   2.5,
    "ブリンカ": 2.5,
    "目先替":   2.5,
    "メンコ":   1.5,
    "シャドー": 1.5,
    "舌縛":     1.5,
    "ハミ替":   1.0,

    # ── 距離変 ──
    "距離詰": 2.0,
    "距離延": 2.0,
    "短縮":   1.5,
    "延長":   1.5,
    "マイル替": 2.0,

    # ── サーフェス変（Phase2拡張枠を一部前倒し） ──
    "ダート替": 2.5,
    "芝替":     2.5,
    "ダ替":     2.5,

    # ── 脚質/気合変 ──
    "気合入":         1.5,
    "粘り込み注意":   1.5,
    "先行策":         1.5,
    "逃げ":           1.0,
    "出していく":     1.0,

    # ── 一変系（陣営の「化けた」宣言） ──
    "一変":   2.0,
    "化けた": 2.0,
    "変身":   2.0,
    "見違え": 1.5,
    "別馬":   2.0,

    # ── クラス変 ──
    "自己条件戻": 1.0,
    "降級":       1.0,
    "格下":       0.8,

    # ── 騎手変（朱雀領域だが穴シグナルとして軽加点） ──
    "乗り替わり": 0.5,
    "テン乗り":   0.5,
}


def score_jrdb(buri_text: str = "", bagu_text: str = "") -> tuple[float, list[str]]:
    """JRDB n_live の物理シグナルを採点"""
    score = 0.0
    hits = []
    for key, pt in JRDB_BURI.items():
        if key in (buri_text or ""):
            score += pt
            hits.append(f"JRDB:{key}(+{pt})")
            break  # 初B と B は排他
    for key, pt in JRDB_BAGU.items():
        if key in (bagu_text or ""):
            score += pt
            hits.append(f"JRDB:馬具{key}(+{pt})")
    return score, hits


def score_keibabook(tanpyou: str) -> tuple[float, list[str]]:
    """keibabook 短評の「変」キーワードを採点"""
    score = 0.0
    hits = []
    if not tanpyou:
        return score, hits
    for key, pt in HENKEY.items():
        if key in tanpyou:
            score += pt
            hits.append(f"BOOK:{key}(+{pt})")
    return score, hits


def byakko_score(buri="", bagu="", tanpyou="",
                 jockey="", trainer="", venue="", trainer_loc="",
                 init_b_keibabook=False) -> dict:
    """白虎総合スコア算出（4Layer合議）

    Args:
        buri: JRDB n_live ブリ列（"初B" / "再B" / "B外" / "B"）
        bagu: JRDB n_live 馬具列（"＊" 等）
        tanpyou: keibabook 短評テキスト
        jockey: 騎手名（外国人騎手フィルター用）
        trainer: 調教師名（戦略家厩舎フィルター用）
        venue: 競馬場名（遠征判定用）
        trainer_loc: 厩舎所属（"美" or "栗"）
        init_b_keibabook: keibabookで .kigou.blink 検出された場合True
    """
    s_jrdb, h_jrdb = score_jrdb(buri, bagu)
    s_book, h_book = score_keibabook(tanpyou)
    s_camp, h_camp = boost_for_camp(jockey, trainer, venue, trainer_loc)
    total = s_jrdb + s_book + s_camp

    # keibabook CSS 検出ボーナス（JRDB初Bと一致 or 単独でも+1.5）
    if init_b_keibabook:
        if "初B" in (buri or ""):
            total += 0.5
            h_jrdb.append("keibabook初B確認(+0.5)")
        else:
            total += 1.5
            h_jrdb.append("keibabook初B単独検出(+1.5)")

    # 両ソース合致ボーナス（JRDB物理 ＆ ブック意志 同時HIT）
    bonus = 0.0
    if s_jrdb > 0 and s_book > 0:
        bonus = 1.0
        h_jrdb.append("両ソース合致(+1.0)")

    total += bonus

    if total >= 5.0:
        tier, mark = "白虎降臨", "⚡⚡⚡"
    elif total >= 3.0:
        tier, mark = "強白虎", "⚡⚡"
    elif total >= 1.5:
        tier, mark = "軽白虎", "⚡"
    else:
        tier, mark = "無印", ""

    return {
        "score": round(total, 2),
        "tier": tier,
        "mark": mark,
        "hits": h_jrdb + h_book + h_camp,
        "jrdb_score": round(s_jrdb, 2),
        "book_score": round(s_book, 2),
        "camp_score": round(s_camp, 2),
        "bonus": bonus,
    }


if __name__ == "__main__":
    # 京都4R キボウホー実証（2026-05-10）
    res = byakko_score(buri="初B", bagu="", tanpyou="遮眼革を着用")
    print("【キボウホー13番】", res)
    assert res["score"] >= 5.0, "白虎降臨判定が出るはず"
    print("✅ 白虎降臨⚡⚡⚡ 判定OK")

    # ボンボンベイビー実証：矢作×ディー×初B＋＊×栗東→東京
    res2 = byakko_score(
        buri="初B", bagu="＊", tanpyou="適性を探って",
        jockey="ディー", trainer="矢作芳", venue="東京", trainer_loc="栗",
        init_b_keibabook=True,
    )
    print("\n【ボンボンベイビー3番】", res2)
    print(f"  → score={res2['score']} / tier={res2['tier']} / camp={res2['camp_score']}")
