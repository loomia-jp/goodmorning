# データスキーマ定義

メグル買取 経営インテリジェンスシステム v2 で永続化される JSON のスキーマ定義です。

すべての日付は **JST（Asia/Tokyo）固定**。数値は `number`、欠損は `null`（空文字や 0 は禁止）。

---

## 1. 日次スナップショット（Phase 1, schema_version 1.1）

**保存先**: `morning-brief/data/YYYY/MM/DD.json`
**生成タイミング**: 毎朝 08:00 JST の朝刊配信ワークフロー終了時

### 変更履歴

| バージョン | 内容 |
|---|---|
| 1.0 | 初版（Phase 1 立ち上げ時） |
| 1.1 | 福祉・介護・終活セクション独立、ブランド情報 / メルカリ・ヤフオク TOP5 / 規制動向の追加。`subagent_meta.agent_society_status` を `agent_welfare_status` に改名 |

### スキーマ

```jsonc
{
  "schema_version": "1.1",
  "date": "YYYY-MM-DD",                  // JST 日付（必須）
  "weekday": "Mon|Tue|Wed|Thu|Fri|Sat|Sun",
  "captured_at": "YYYY-MM-DDTHH:MM:SS+09:00",  // ISO 8601 JST

  // 相場（取得不能な項目は null）
  "market": {
    "gold_jpy_g":     number | null,     // 田中貴金属 店頭買取価格 円/g
    "platinum_jpy_g": number | null,     // 同上 プラチナ
    "silver_jpy_g":   number | null,     // 同上 銀
    "usdjpy":         number | null,
    "eurjpy":         number | null,
    "nikkei":         number | null,     // 日経平均終値（前営業日）
    "topix":          number | null,
    "valuence_9270":  number | null,     // バリュエンス HD 株価終値
    "komehyo_2780":   number | null,
    "geo_2681":       number | null,     // ゲオ HD（買取大手）
    "gold_dod_pct":      number | null,  // 金 前日比 %（v1.1 追加 / 任意 null 可）
    "platinum_dod_pct":  number | null,
    "silver_dod_pct":    number | null,
    "gold_wow_trend":    string | null,  // 金 週次トレンド: "上昇" | "横ばい" | "下落"（任意）
    "platinum_wow_trend": string | null,
    "silver_wow_trend":  string | null
  },

  // 大阪の天気（朝の出張ルート判断用）
  "weather_osaka": {
    "main":      string | null,          // 例: "晴のち曇"
    "temp_high": number | null,          // ℃
    "temp_low":  number | null,
    "rain_prob": number | null,          // 0-100 (%)
    "am_pm_note": string | null          // 例: "午前曇り → 午後晴れ"（v1.1 追加 / 任意）
  },

  // KPI（Phase 7 で Sheets 自動取得。Phase 1 では null）
  "kpi": {
    "visits":       number | null,       // 訪問件数
    "deals":        number | null,       // 成約件数
    "revenue_jpy":  number | null
  },

  // 朝刊本文に載った主要トピック（メール本文と同期）
  "highlights": [
    {
      "title":      string,
      "impact":     "high" | "medium" | "low",
      "source":     string,              // ソース URL
      "summary":    string,              // 1-2 行
      "sales_hook": string | null        // 営業への活用ポイント（v1.1 追加）
    }
  ],

  // ⚠️マーク付きの注意・警告（終活サービス領域での競合参入は必ずここへ）
  "alerts": [
    {
      "title":     string,
      "severity":  "critical" | "warning" | "info",
      "source":    string,
      "summary":   string
    }
  ],

  // AI / テクノロジー業界ニュース（5 件以上推奨。規制・研究も含む）
  "ai_news": [
    {
      "title":   string,
      "source":  string,
      "summary": string,
      "category": "company" | "regulation" | "research" | "tool" | null,
      "relevance": "high" | "medium" | "low" | null   // 買取・査定業務との関連度
    }
  ],

  // 競合動向（バイセル / 福ちゃん / なんぼや 等。3〜5 件）
  "competitor_moves": [
    {
      "vendor":  string,                 // "バイセル" 等
      "title":   string,
      "source":  string,
      "summary": string,
      "action_today": string | null      // 当日とるべきアクション（v1.1 追加）
    }
  ],

  // メルカリ・ヤフオク高額落札 TOP5（v1.1 追加）
  "secondhand_top5": [
    {
      "platform": "mercari" | "yahoo_auction" | "other",
      "category": string | null,         // "宝飾" / "時計" / "ブランドバッグ" 等
      "title":    string,
      "price":    number | null,         // 落札金額 (JPY)
      "source":   string,
      "note":     string | null          // メグル買取の再現可能な査定上限の参考値など
    }
  ],

  // 主要オークション結果トップ3（古物市場・宝飾系）
  "auctions_top3": [
    {
      "name":   string,
      "price":  number | null,
      "source": string,
      "summary": string | null           // v1.1 追加 / 任意
    }
  ],

  // ブランド情報（v1.1 追加 / 5 件以上推奨）
  // ロレックス・パテック・エルメス・シャネル等の新作 / 廃番 / 国際相場
  "brands_news": [
    {
      "brand":    string,                // "ロレックス" "エルメス" 等
      "title":    string,
      "kind":     "new_release" | "discontinued" | "international_price" | "other",
      "source":   string,
      "summary":  string,
      "impact":   "high" | "medium" | "low",
      "sns_worthy": true | false | null  // 今日 SNS で発信できるネタか
    }
  ],

  // 規制・法改正動向（v1.1 追加）
  "regulations": [
    {
      "title":    string,
      "domain":   "antiques" | "tax" | "consumer" | "ai" | "welfare" | "other",
      "source":   string,
      "summary":  string,
      "impact":   "high" | "medium" | "low"
    }
  ],

  // 福祉・介護・終活ニュース（v1.1 追加 / 6 件以上推奨）
  "welfare_news": [
    {
      "title":     string,
      "category":  "policy" | "market" | "research" | "product" | "ma" | "subsidy" | "other",
      "source":    string,
      "summary":   string,
      "impact":    "high" | "medium" | "low",
      "lead_opportunity": string | null  // 集客機会としての評価（v1.1 追加）
    }
  ],

  // 30日以内に締切の補助金・助成金
  "subsidies_deadline_within_30d": [
    {
      "name":     string,
      "deadline": "YYYY-MM-DD",
      "source":   string,
      "summary":  string
    }
  ],

  // Subagent 実行ステータス（運用監視用）
  "subagent_meta": {
    "agent_market_status":   "ok" | "partial" | "failed",
    "agent_industry_status": "ok" | "partial" | "failed",
    "agent_ai_status":       "ok" | "partial" | "failed",
    "agent_welfare_status":  "ok" | "partial" | "failed",  // v1.1 で agent_society_status から改名
    "notes": string | null
  }
}
```

### 必須フィールド

- `schema_version`, `date`, `weekday`, `captured_at`
- `market`, `weather_osaka`, `kpi`, `subagent_meta`

配列フィールド（`highlights`, `alerts`, `ai_news`, `competitor_moves`, `secondhand_top5`, `auctions_top3`, `brands_news`, `regulations`, `welfare_news`, `subsidies_deadline_within_30d`）は要素 0 でも `[]` を必須。

各要素の最小必須キー（`title`, `source`, `summary` など）はバリデータが厳格チェックします。任意フィールド（`sales_hook` 等）は欠損時 null か未設定で OK。

---

## 2. 週次サマリー（Phase 4 で追加予定）

**保存先**: `morning-brief/data/weekly/YYYY-WW.json`

```jsonc
{
  "schema_version": "1.0",
  "iso_week": "YYYY-WW",
  "from": "YYYY-MM-DD",
  "to":   "YYYY-MM-DD",
  "market_trend": { /* 7日平均・前週比 */ },
  "kpi_trend":    { /* 訪問・成約・売上の前週比 */ },
  "top_topics":   [ /* 注目トピック上位 */ ],
  "next_week_outlook": string
}
```

> 詳細は Phase 4 着手時に確定。

---

## 3. 月次サマリー（Phase 4 で追加予定）

**保存先**: `morning-brief/data/monthly/YYYY-MM.json`

> 詳細は Phase 4 着手時に確定。

---

## 4. 緊急速報ログ（Phase 6 で追加予定）

**保存先**: `morning-brief/data/alerts/YYYY-MM-DD-HHMMSS.json`

> 詳細は Phase 6 着手時に確定。

---

## バリデーション

すべての保存前に `scripts/validate-bundle.py` でスキーマ検証を行います。検証失敗時はジョブを失敗させ、`TO_EMAIL` にエラー通知します（破損 JSON のコミットを防ぐため）。
