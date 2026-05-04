# データスキーマ定義

メグル買取 経営インテリジェンスシステム v2 で永続化される JSON のスキーマ定義です。

すべての日付は **JST（Asia/Tokyo）固定**。数値は `number`、欠損は `null`（空文字や 0 は禁止）。

---

## 1. 日次スナップショット（Phase 1 で利用）

**保存先**: `morning-brief/data/YYYY/MM/DD.json`
**生成タイミング**: 毎朝 08:00 JST の朝刊配信ワークフロー終了時

### スキーマ

```jsonc
{
  "schema_version": "1.0",
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
    "geo_2681":       number | null      // ゲオ HD（買取大手）
  },

  // 大阪の天気（朝の出張ルート判断用）
  "weather_osaka": {
    "main":      string | null,          // 例: "晴のち曇"
    "temp_high": number | null,          // ℃
    "temp_low":  number | null,
    "rain_prob": number | null           // 0-100 (%)
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
      "title":  string,
      "impact": "high" | "medium" | "low",
      "source": string,                  // ソース URL
      "summary": string                  // 1-2 行
    }
  ],

  // ⚠️マーク付きの注意・警告
  "alerts": [
    {
      "title":     string,
      "severity":  "critical" | "warning" | "info",
      "source":    string,
      "summary":   string
    }
  ],

  // AI / テクノロジー業界ニュース
  "ai_news": [
    {
      "title":   string,
      "source":  string,
      "summary": string
    }
  ],

  // 競合動向（バイセル / 福ちゃん / なんぼや 等）
  "competitor_moves": [
    {
      "vendor":  string,                 // "バイセル" 等
      "title":   string,
      "source":  string,
      "summary": string
    }
  ],

  // 主要オークション結果トップ3（古物市場・宝飾系）
  "auctions_top3": [
    {
      "name":   string,
      "price":  number | null,
      "source": string
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
    "agent_society_status":  "ok" | "partial" | "failed",
    "notes": string | null
  }
}
```

### 必須フィールド

- `schema_version`, `date`, `weekday`, `captured_at`
- `market`, `weather_osaka`, `kpi`, `subagent_meta`

配列フィールド（`highlights` 等）は要素 0 でも `[]` を必須。

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
