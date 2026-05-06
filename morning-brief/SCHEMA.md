# データスキーマ定義

メグル買取 経営インテリジェンスシステム v2 で永続化される JSON のスキーマ定義です。

すべての日付は **JST（Asia/Tokyo）固定**。数値は `number`、欠損は `null`（空文字や 0 は禁止）。

---

## 1. 日次スナップショット（Phase 1, schema_version 1.2）

**保存先**: `morning-brief/data/YYYY/MM/DD.json`
**生成タイミング**: 毎朝 08:00 JST の朝刊配信ワークフロー終了時

### 変更履歴

| バージョン | 内容 |
|---|---|
| 1.0 | 初版（Phase 1 立ち上げ時） |
| 1.1 | 福祉・介護・終活独立、ブランド情報 / メルカリ・ヤフオク TOP5 / 規制動向追加。`agent_society_status` → `agent_welfare_status` |
| 1.2 | 5 並列 Subagent 化。海外指数 / 暗号資産 / コモディティを `market` に追加。`reuse_market`（骨董・楽器カメラ・中古車・越境 EC）、`tech_news`（半導体・量子・ロボ）、`lifestyle_trends`（社会トレンド）の 3 配列を新設。`subagent_meta.agent_lifestyle_status` 追加 |

### スキーマ

```jsonc
{
  "schema_version": "1.2",
  "date": "YYYY-MM-DD",                  // JST 日付（必須）
  "weekday": "Mon|Tue|Wed|Thu|Fri|Sat|Sun",
  "captured_at": "YYYY-MM-DDTHH:MM:SS+09:00",  // ISO 8601 JST

  // 相場（取得不能な項目は null）
  "market": {
    // --- v1.0 から ---
    "gold_jpy_g":     number | null,     // 田中貴金属 店頭買取価格 円/g
    "platinum_jpy_g": number | null,
    "silver_jpy_g":   number | null,
    "usdjpy":         number | null,
    "eurjpy":         number | null,
    "nikkei":         number | null,     // 日経平均終値（前営業日）
    "topix":          number | null,
    "valuence_9270":  number | null,     // バリュエンス HD 株価終値
    "komehyo_2780":   number | null,
    "geo_2681":       number | null,     // ゲオ HD（買取大手）

    // --- v1.1 追加 / 任意 null 可 ---
    "gold_dod_pct":      number | null,  // 金 前日比 %
    "platinum_dod_pct":  number | null,
    "silver_dod_pct":    number | null,
    "gold_wow_trend":    string | null,  // 金 週次トレンド: "上昇" | "横ばい" | "下落"
    "platinum_wow_trend": string | null,
    "silver_wow_trend":  string | null,

    // --- v1.2 追加 / 任意 null 可 ---
    "nydow":            number | null,   // NY ダウ終値
    "nasdaq":           number | null,   // ナスダック終値
    "sp500":            number | null,   // S&P 500 終値
    "nydow_dod_pct":    number | null,
    "nasdaq_dod_pct":   number | null,
    "sp500_dod_pct":    number | null,
    "btc_jpy":          number | null,   // ビットコイン (円)
    "eth_jpy":          number | null,   // イーサリアム (円)
    "btc_dod_pct":      number | null,
    "eth_dod_pct":      number | null,
    "wti_usd_bbl":      number | null,   // WTI 原油 USD/bbl
    "copper_usd_lb":    number | null,   // 銅 USD/lb
    "wheat_usd_bu":     number | null    // 小麦 USD/bu
  },

  // 大阪の天気（朝の出張ルート判断用）
  "weather_osaka": {
    "main":      string | null,          // 例: "晴のち曇"
    "temp_high": number | null,          // ℃
    "temp_low":  number | null,
    "rain_prob": number | null,          // 0-100 (%)
    "am_pm_note": string | null          // 例: "午前曇り → 午後晴れ"（v1.1 追加）
  },

  // KPI（Phase 7 で Sheets 自動取得。Phase 1 では null）
  "kpi": {
    "visits":       number | null,
    "deals":        number | null,
    "revenue_jpy":  number | null
  },

  // 朝刊本文に載った主要トピック（メール本文と同期、5 件以上推奨）
  "highlights": [
    {
      "title":      string,
      "impact":     "high" | "medium" | "low",
      "source":     string,
      "summary":    string,              // 1-2 行
      "sales_hook": string | null        // 営業への活用ポイント
    }
  ],

  // ⚠️ マーク付きの注意・警告（終活サービス領域での競合参入は必ずここへ）
  "alerts": [
    {
      "title":     string,
      "severity":  "critical" | "warning" | "info",
      "source":    string,
      "summary":   string
    }
  ],

  // AI ニュース（5 件以上推奨）
  "ai_news": [
    {
      "title":   string,
      "source":  string,
      "summary": string,
      "category":  "company" | "regulation" | "research" | "tool" | "benchmark" | "industry_case" | null,
      "relevance": "high" | "medium" | "low" | null   // 買取・査定業務との関連度
    }
  ],

  // テクノロジーニュース（v1.2 追加 / 半導体・量子・ロボ等）
  "tech_news": [
    {
      "title":    string,
      "category": "semiconductor" | "quantum_space" | "robotics_av" | "other",
      "source":   string,
      "summary":  string,
      "impact":   "high" | "medium" | "low"
    }
  ],

  // 競合動向（5 件以上推奨）
  "competitor_moves": [
    {
      "vendor":  string,                 // "バイセル" 等
      "title":   string,
      "source":  string,
      "summary": string,
      "action_today": string | null      // 当日とるべきアクション
    }
  ],

  // メルカリ・ヤフオク高額落札 TOP5
  "secondhand_top5": [
    {
      "platform": "mercari" | "yahoo_auction" | "other",
      "category": string | null,         // "宝飾" / "時計" / "ブランドバッグ" 等
      "title":    string,
      "price":    number | null,
      "source":   string,
      "note":     string | null
    }
  ],

  // 業者間オークション結果トップ3（古物市場・宝飾系）
  "auctions_top3": [
    {
      "name":   string,
      "price":  number | null,
      "source": string,
      "summary": string | null
    }
  ],

  // ブランド情報（5 件以上推奨）
  "brands_news": [
    {
      "brand":    string,
      "title":    string,
      "kind":     "new_release" | "discontinued" | "international_price" | "other",
      "source":   string,
      "summary":  string,
      "impact":   "high" | "medium" | "low",
      "sns_worthy": true | false | null
    }
  ],

  // リユース市場サマリー（v1.2 追加）
  // 骨董・美術品 / 楽器・カメラ・時計 / 中古車・バイク / 越境 EC
  "reuse_market": [
    {
      "title":    string,
      "category": "antiques_art" | "instruments_camera_watches" | "vehicles" | "cross_border_ec" | "other",
      "source":   string,
      "summary":  string,
      "impact":   "high" | "medium" | "low"
    }
  ],

  // 規制・法改正動向
  "regulations": [
    {
      "title":    string,
      "domain":   "antiques" | "tax" | "consumer" | "ai" | "welfare" | "other",
      "source":   string,
      "summary":  string,
      "impact":   "high" | "medium" | "low"
    }
  ],

  // 福祉・介護・終活ニュース（7 件以上推奨）
  "welfare_news": [
    {
      "title":     string,
      "category":  "policy" | "facility" | "home_care" | "research" | "estate" | "inheritance" | "product" | "ma" | "subsidy" | "other",
      "source":    string,
      "summary":   string,
      "impact":    "high" | "medium" | "low",
      "lead_opportunity": string | null  // 集客機会としての評価
    }
  ],

  // 社会トレンド・ライフスタイル（v1.2 追加 / 5 件以上推奨）
  "lifestyle_trends": [
    {
      "title":     string,
      "category":  "senior_consumer" | "gen_z" | "family_community" | "health_medical" | "local_kansai" | "other",
      "source":   string,
      "summary":  string,
      "impact":   "high" | "medium" | "low",
      "scene":    "field_visit" | "exec_meeting" | "staff_morning" | "general" | null
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
    "agent_market_status":    "ok" | "partial" | "failed",
    "agent_industry_status":  "ok" | "partial" | "failed",
    "agent_ai_status":        "ok" | "partial" | "failed",
    "agent_welfare_status":   "ok" | "partial" | "failed",
    "agent_lifestyle_status": "ok" | "partial" | "failed",  // v1.2 追加
    "notes": string | null
  }
}
```

### 必須フィールド

- `schema_version`, `date`, `weekday`, `captured_at`
- `market`, `weather_osaka`, `kpi`, `subagent_meta`

配列フィールド（`highlights`, `alerts`, `ai_news`, `tech_news`, `competitor_moves`, `secondhand_top5`, `auctions_top3`, `brands_news`, `reuse_market`, `regulations`, `welfare_news`, `lifestyle_trends`, `subsidies_deadline_within_30d`）は要素 0 でも `[]` を必須。

各要素の最小必須キー（`title`, `source`, `summary` など）はバリデータが厳格チェックします。任意フィールド（`sales_hook` 等）は欠損時 null か未設定で OK。

---

## 2. 話のネタ便スナップショット（Phase 3 予定 / topics-brief schema 1.0）

**保存先**: `topics-brief/data/YYYY/MM/DD.json`（Phase 3 ワークフロー化時に自動生成）

```jsonc
{
  "schema_version": "1.0",
  "date": "YYYY-MM-DD",
  "weekday": "Mon|...|Sun",
  "captured_at": "YYYY-MM-DDTHH:MM:SS+09:00",

  "customer_topics": [    // 5 件以上必須
    {
      "title":     string,
      "category":  "health" | "lifestyle" | "tv_celebrity" | "season" | "local_osaka" | "nostalgia" | "family" | "money_savings",
      "summary":   string,
      "source":    string | null,
      "one_liner": string,            // 「○○、ご存じでした？」風の柔らかい1文
      "tone":      "soft_share"       // 必須：押し付けない柔らかい語尾
    }
  ],

  "executive_topics": [   // 5 件以上必須
    {
      "title":     string,
      "category":  "macro" | "case_study" | "investment" | "ai_dx" | "industry_cross" | "geopolitics" | "wealth_psychology" | "global_business",
      "summary":   string,            // 数字・出典を含む
      "source":    string,            // 必須
      "one_liner": string,            // 「○○の動き、興味深くないですか？」風
      "tone":      "peer_curious"
    }
  ],

  "staff_topics": [       // 5 件以上必須
    {
      "title":     string,
      "category":  "tech" | "trivia" | "money_tips" | "industry_inside" | "wellness" | "science_frontier" | "millionaire_habit",
      "summary":   string,
      "source":    string | null,
      "one_liner": string,            // 「○○知ってる？意外と面白いんだよ」風
      "tone":      "casual_share"
    }
  ],

  "subagent_meta": {
    "agent_customer_status":  "ok" | "partial" | "failed",
    "agent_executive_status": "ok" | "partial" | "failed",
    "agent_staff_status":     "ok" | "partial" | "failed",
    "notes": string | null
  }
}
```

> 朝刊側のバリデータ（`scripts/memory-saver.py`）はまだトピック JSON を検証しません。Phase 3 でワークフロー化する時に専用バリデータを追加予定。

---

## 3. 週次サマリー（Phase 4 で追加予定）

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

## 4. 月次サマリー（Phase 4 で追加予定）

**保存先**: `morning-brief/data/monthly/YYYY-MM.json`

> 詳細は Phase 4 着手時に確定。

---

## 5. 緊急速報ログ（Phase 6 で追加予定）

**保存先**: `morning-brief/data/alerts/YYYY-MM-DD-HHMMSS.json`

> 詳細は Phase 6 着手時に確定。

---

## バリデーション

すべての保存前に `scripts/validate-bundle.py` でスキーマ検証を行います。検証失敗時はジョブを失敗させ、`TO_EMAIL` にエラー通知します（破損 JSON のコミットを防ぐため）。
