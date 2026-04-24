# 📋 出馬表スナップショット（internal-only）

**UG競馬ワイド神宮** の出馬表確定データ保存庫。
**WEB非公開**（`docs/` 外に配置しているため GitHub Pages には一切出ない）。
ギーニョが分析時に参照する **Single Source of Truth (SSoT)**。

---

## 🎯 目的

1. **出馬表確定時点のスナップショット**を不変の真実として記録
2. **タイダルロック問題の再発防止**：JSON（真実）→ final-display（仮想）の手動反映ズレを検知可能に
3. ギーニョが分析時に `Read` で即座にアクセスできる内部参照DB

---

## 📁 命名規則

`data/entries/{YYYY-MM-DD}-{place}-{race}r.json`

`docs/data/race-notes/` と完全に同じ命名規則なのでペア参照しやすい。

### 例
```
data/entries/2026-04-25-tokyo-11r.json   ← 青葉賞
data/entries/2026-04-26-kyoto-10r.json   ← センテニアル・パークS
data/entries/2026-04-26-tokyo-11r.json   ← フローラS
```

### 場所コード（`{place}`）
- `tokyo` 東京
- `kyoto` 京都
- `hanshin` 阪神
- `nakayama` 中山
- `fukushima` 福島
- `niigata` 新潟
- `chukyo` 中京
- `kokura` 小倉
- `sapporo` 札幌
- `hakodate` 函館

---

## 📐 JSON Schema v1（MVP）

```jsonc
{
  "meta": {
    "raceKey": "2026-04-26-kyoto-10r",     // ファイル名と一致
    "date": "2026-04-26",                   // YYYY-MM-DD
    "dayOfWeek": "sun",                     // sat | sun | (weekday)
    "course": "京都",                       // 日本語表記
    "raceNo": 10,                           // 数値
    "raceName": "センテニアル・パークS",    // 正式名称
    "grade": "3勝クラス",                   // 新馬/未勝利/1勝/2勝/3勝/L/OP/G3/G2/G1
    "surface": "芝",                        // 芝 | ダート
    "distance": 1800,                       // メートル（数値）
    "direction": "右・外",                  // 右 | 右・外 | 左 | 左・外 | 直線 等
    "headcount": 18,                        // 頭数
    "startTime": "14:50",                   // HH:MM
    "win5Leg": 1,                           // WIN5対象レースなら 1〜5、対象外なら null
    "confirmedAt": "2026-04-25T20:00:00+09:00"  // 確定日時（ISO 8601）
  },
  "horses": [
    {
      "gate": 1,                            // 枠番
      "num": 1,                             // 馬番
      "name": "○○○○",                      // 馬名（カタカナ）
      "sex": "牡",                          // 牡 | 牝 | セ
      "age": 5,                             // 年齢
      "weight": 57,                         // 斤量（kg）
      "jockey": "△△",                       // 騎手名
      "trainer": "栗東・××",                // 栗東・/美浦・+厩舎名
      "sire": "父馬名",
      "bms": "母父馬名",
      "prevRace": {
        "date": "2026-04-05",               // YYYY-MM-DD
        "course": "阪神",
        "distance": "芝1800",
        "raceName": "鳴尾記念",
        "finish": 3,                        // 着順（数値）。中止/除外なら "中" "除" 等
        "horseWeight": 488,                 // 馬体重（kg）
        "weightDiff": -6                    // 前走時との差
      },
      "notes": ""                           // 自由メモ欄
    }
  ],
  "source": {
    "url": "",                              // データ取得元URL（任意）
    "fetchedBy": "manual"                   // manual | scraper | api
  }
}
```

---

## 🔁 データフロー

```
[JRA公式で出馬表確定（木〜金）]
       ↓ （手入力 or スクレイプ）
[data/entries/{race}.json]  ← 確定スナップショット
       ↓ （ギーニョが Read で参照して分析）
[docs/data/race-notes/{race}.json]  ← 分析ノート（4神grade・picks・bets）
       ↓ （現状：手動反映／将来：自動生成）
[docs/final-display.html]   ← 公開
```

**このフローにより、タイダルロック級のデータ腐敗を構造的に防止。**

---

## ✍️ 運用ルール

### DO
- 出馬表確定後、**即座にJSON化**してここに保存
- 既存ファイルを編集する場合も `confirmedAt` は最初の確定時刻を維持
- 馬名はカタカナ（race-notes と統一）
- 任意フィールドは空文字 `""` または null

### DON'T
- `docs/` 配下に出馬表データを置かない（WEB公開されてしまう）
- 馬名・レース名を推測で埋めない（空欄にする）
- 予想・グレード・コメントはここに書かない（それは race-notes の役割）

---

## 🚧 今後の拡張候補（Phase 2+）

- [ ] 過去5走（`prevRace` → `recentRaces[]` 配列化）
- [ ] 獲得賞金・成績サマリ
- [ ] 生産者・馬主
- [ ] 外厩履歴
- [ ] 調教時計
- [ ] オッズ確定値のスナップショット（時系列）
- [ ] JRA or 競馬ブックからの自動スクレイピングスクリプト
- [ ] JSON → HTML自動生成（SSoT確立で手動反映を廃止）

---

## 📎 関連

- 分析ノート：`docs/data/race-notes/`
- 最終公開：`docs/final-display.html`
- テンプレ：`_template.json`（このディレクトリ）
- スキル：`kyusha_danwa_skill.md` / `yugomi_lap_skill.md` / `genbu_skill.md` / `suzaku_sp_skill.md`

---

🏛 **最終更新：2026-04-25（青葉賞当日、タイダルロック事件の教訓として着工）**
