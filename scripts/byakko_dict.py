"""
🐅 白虎加点辞書 v0.1（2026-05-11確定 / 5/17本番運用）
「変」を司る西方金の神 ─ 陣営の物理的・意志的な変化を検出

データソース合議:
  Layer 1: JRDB n_live ─ 物理的「変」（馬具・ブリンカー）
  Layer 2: keibabook 短評 ─ 陣営の意志「変」

スコア階層:
  >= 5.0 : ⚡⚡⚡ 白虎降臨（穴絶対採用）
  >= 3.0 : ⚡⚡ 強白虎（穴候補上位）
  >= 1.5 : ⚡ 軽白虎（穴候補）
  <  1.5 : 無印（穴は言霊4位で埋める）
"""

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


def byakko_score(buri="", bagu="", tanpyou="") -> dict:
    """白虎総合スコア算出（両ソース合議）"""
    s_jrdb, h_jrdb = score_jrdb(buri, bagu)
    s_book, h_book = score_keibabook(tanpyou)
    total = s_jrdb + s_book

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
        "hits": h_jrdb + h_book,
        "jrdb_score": round(s_jrdb, 2),
        "book_score": round(s_book, 2),
        "bonus": bonus,
    }


if __name__ == "__main__":
    # 京都4R キボウホー実証（2026-05-10）
    res = byakko_score(buri="初B", bagu="", tanpyou="遮眼革を着用")
    print("【キボウホー13番】", res)
    assert res["score"] >= 5.0, "白虎降臨判定が出るはず"
    print("✅ 白虎降臨⚡⚡⚡ 判定OK")
