"""
🐢 玄武辞書 v1.0（2026-05-11 / 5/17本番想定）
「出自」を司る北方水の神 ─ 馬主・生産者・厩舎・外厩を統括

データソース（4軸）:
  軸1: 馬主ランク    docs/data/genbu/banushi/banushi_rank_2026.json
  軸2: 生産者ランク  docs/data/genbu/seisan/seisan_rank_2026.json
  軸3: 厩舎ランク    docs/data/genbu/trainer/trainer_rank_2026.json
  軸4: 外厩フラグ    実行時に文字列照合（CH=チャンピオンヒルズ）

役割:
  ・白虎ヒット無し時の「穴枠」フォールバック
  ・馬の「出自による格」を数値化
  ・人気薄 × 質型出自 = 大穴シグナル
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GENBU_DIR = ROOT / "docs" / "data" / "genbu"


# ──────────────────────────────────────────────
# 軸1〜3：JSON DB ロード（モジュール起動時に1回だけ）
# ──────────────────────────────────────────────
def _load_json(path: Path) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


_BANUSHI = _load_json(GENBU_DIR / "banushi" / "banushi_rank_2026.json")
_SEISAN  = _load_json(GENBU_DIR / "seisan"  / "seisan_rank_2026.json")
_TRAINER = _load_json(GENBU_DIR / "trainer" / "trainer_rank_2026.json")

# 名前→エントリ の照合用 dict を構築（高速ルックアップ）
_BANUSHI_MAP = {o["name"]: o for o in _BANUSHI.get("owners",   [])}
_SEISAN_MAP  = {b["name"]: b for b in _SEISAN .get("breeders", [])}
_TRAINER_MAP = {t["name"]: t for t in _TRAINER.get("trainers", [])}


# ──────────────────────────────────────────────
# 軸別ティア取得関数
# ──────────────────────────────────────────────
def _fuzzy_lookup(name: str, db_map: dict) -> dict:
    """部分一致ルックアップ。完全一致 → 包含一致の順"""
    if not name:
        return {}
    if name in db_map:
        return db_map[name]
    # 包含一致（"矢作" → "矢作芳人" など）
    for key, val in db_map.items():
        if name in key or key in name:
            return val
    return {}


def get_owner_tier(name: str) -> str:
    return _fuzzy_lookup(name, _BANUSHI_MAP).get("tier", "?")


def get_seisan_tier(name: str) -> str:
    return _fuzzy_lookup(name, _SEISAN_MAP).get("tier", "?")


def get_trainer_tier(name: str) -> str:
    return _fuzzy_lookup(name, _TRAINER_MAP).get("tier", "?")


# ──────────────────────────────────────────────
# 玄武スコア（穴枠用）
# ──────────────────────────────────────────────
# ティア別加点
TIER_POINTS_OWNER = {"S": 2.5, "A": 1.5, "B": 0.5, "C": 0.0, "D": 0.0, "E": 0.0, "?": 0.0}
TIER_POINTS_SEISAN = {"S": 2.5, "A": 1.5, "B": 0.3, "C": 0.0, "D": 0.0, "E": 0.0, "?": 0.0}
TIER_POINTS_TRAINER = {"S": 1.5, "A": 1.0, "B": 0.3, "C": 0.0, "D": 0.0, "E": 0.0, "?": 0.0}

# 外厩シグナル
GAIKYU_BONUS = {
    "天栄":     1.0,   # ノーザンF天栄（NFパッケージ）
    "しがらき": 1.0,
    "鈴鹿":     0.8,
    "CH":              2.0,  # チャンピオンヒルズ＝非ノーザン本気判定
    "チャンピオン":    2.0,
    "ノーザンファーム": 1.0,
    "山元":     0.5,
}

# 人気薄ボーナス（穴ゾーン）
def _popularity_bonus(pop: int) -> float:
    if pop <= 0:
        return 0.0
    if pop >= 10:
        return 2.0
    if pop >= 6:
        return 1.0
    if pop >= 4:
        return 0.3
    return 0.0


def genbu_ana_score(owner: str = "", seisan: str = "", trainer: str = "",
                    gaikyu: str = "", popularity: int = 0) -> dict:
    """玄武 穴枠スコア算出

    Args:
        owner: 馬主名（例 "(株)ダノックス"）
        seisan: 生産者名（例 "ダーレー・ジャパン・ファーム"）
        trainer: 調教師名（例 "矢作芳人"）
        gaikyu: 外厩名（例 "ノーザンFしがらき"、"CH"、"天栄"）
        popularity: 想定人気（数字）

    Returns:
        {score, tier, mark, hits, breakdown}
    """
    s_owner   = TIER_POINTS_OWNER  .get(get_owner_tier(owner),    0.0)
    s_seisan  = TIER_POINTS_SEISAN .get(get_seisan_tier(seisan),  0.0)
    s_trainer = TIER_POINTS_TRAINER.get(get_trainer_tier(trainer), 0.0)

    # 外厩ボーナス
    s_gaikyu = 0.0
    g_hit = ""
    for key, pt in GAIKYU_BONUS.items():
        if key in (gaikyu or ""):
            s_gaikyu = max(s_gaikyu, pt)
            g_hit = key
            break

    # 非ノーザン × CH ボーナス（陣営本気判定）
    nf_kw = ("ノーザンファーム", "天栄", "しがらき")
    ch_kw = ("CH", "チャンピオン")
    bonus_ch = 0.0
    is_ch = any(k in (gaikyu or "") for k in ch_kw)
    is_nf_seisan = any(k in (seisan or "") for k in ("ノーザン",))
    if is_ch and not is_nf_seisan:
        bonus_ch = 1.5  # 非ノーザン×CH 追加加点

    # 人気薄ボーナス
    s_pop = _popularity_bonus(popularity)

    total = s_owner + s_seisan + s_trainer + s_gaikyu + bonus_ch + s_pop

    # ティア判定
    if total >= 5.0:
        tier, mark = "玄武降臨", "🐢🐢🐢"
    elif total >= 3.5:
        tier, mark = "強玄武",   "🐢🐢"
    elif total >= 2.0:
        tier, mark = "軽玄武",   "🐢"
    else:
        tier, mark = "無印",     ""

    hits = []
    if s_owner   > 0: hits.append(f"馬主{get_owner_tier(owner)}({owner})+{s_owner}")
    if s_seisan  > 0: hits.append(f"生産{get_seisan_tier(seisan)}({seisan})+{s_seisan}")
    if s_trainer > 0: hits.append(f"厩舎{get_trainer_tier(trainer)}({trainer})+{s_trainer}")
    if s_gaikyu  > 0: hits.append(f"外厩:{g_hit}+{s_gaikyu}")
    if bonus_ch  > 0: hits.append(f"非ノーザン×CH合議+{bonus_ch}")
    if s_pop     > 0: hits.append(f"穴ゾーン{popularity}人気+{s_pop}")

    return {
        "score": round(total, 2),
        "tier": tier,
        "mark": mark,
        "hits": hits,
        "breakdown": {
            "owner":   round(s_owner,   2),
            "seisan":  round(s_seisan,  2),
            "trainer": round(s_trainer, 2),
            "gaikyu":  round(s_gaikyu,  2),
            "ch_bonus":round(bonus_ch,  2),
            "pop":     round(s_pop,     2),
        },
    }


# ──────────────────────────────────────────────
# スモークテスト
# ──────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("🐢 玄武辞書 v1.0 スモークテスト")
    print("=" * 60)

    # DB ロード確認
    print(f"\n📁 DB ロード状況")
    print(f"   馬主    : {len(_BANUSHI_MAP):3}件")
    print(f"   生産者  : {len(_SEISAN_MAP):3}件")
    print(f"   厩舎    : {len(_TRAINER_MAP):3}件")

    # テスト1: ホールネス（VM〜新潟大賞典の警戒対象）
    print(f"\n🐎 テスト1: ホールネス想定（ゴドルフィン×ダーレー）")
    res = genbu_ana_score(
        owner="ゴドルフィン",
        seisan="ダーレー・ジャパン・ファーム",
        trainer="",
        gaikyu="",
        popularity=5,
    )
    print(f"   score={res['score']} / tier={res['tier']} / mark={res['mark']}")
    print(f"   hits: {res['hits']}")

    # テスト2: VM ラヴァンダ想定（非ノーザン×CH×9人気）
    print(f"\n🐎 テスト2: ラヴァンダ想定（非ノーザン×CH×9人気）")
    res = genbu_ana_score(
        owner="",
        seisan="",
        trainer="中村",
        gaikyu="CH",
        popularity=9,
    )
    print(f"   score={res['score']} / tier={res['tier']} / mark={res['mark']}")
    print(f"   hits: {res['hits']}")

    # テスト3: ダノックス×大穴
    print(f"\n🐎 テスト3: ダノックス×無名生産×12人気")
    res = genbu_ana_score(
        owner="(株)ダノックス",
        seisan="",
        trainer="",
        gaikyu="",
        popularity=12,
    )
    print(f"   score={res['score']} / tier={res['tier']} / mark={res['mark']}")
    print(f"   hits: {res['hits']}")

    print("\n" + "=" * 60)
    print("✅ 玄武辞書 v1.0 動作確認完了")
