# メグル買取 経営インテリジェンスシステム v2

代表 偉吹（Ibuki）向けに、毎朝の経営判断を支える情報を自動配信する社内システムです。

GitHub Actions（cron） + Claude Code CLI + Resend で構成されています。

---

## 配信物（最終形）

| 配信物 | 配信時刻(JST) | チャネル | ステータス |
|---|---|---|---|
| 朝刊 Brief | 毎朝 08:00 | Email | **Phase 1（実装中）** |
| 話のネタ便 | 毎朝 07:00 | Email | Phase 3 |
| 週報 | 日曜 09:00 | Email | Phase 4 |
| 月報 | 月初 10:00 | Email | Phase 4 |
| 緊急速報 | 随時 | Email | Phase 6 |

> Phase 1 では **朝刊 HTML メール** のみ配信します。音声（TTS）/ LINE / Slack 連携は Phase 5 以降で追加予定。

---

## ディレクトリ構成（Phase 1 時点）

```
.
├── README.md
├── .gitignore
├── scripts/
│   ├── send-resend.py        # Resend 経由のメール送信
│   ├── memory-saver.py       # 日次 JSON をスキーマ検証付きで保存（v1.0/1.1/1.2 対応）
│   └── validate-bundle.py    # 出力 JSON / HTML の妥当性チェック
├── morning-brief/
│   ├── SCHEMA.md             # 日次 JSON スキーマ（v1.2）
│   ├── PROMPT.md             # 朝刊プロンプト（5 Subagent 並列）
│   ├── templates/
│   │   └── email-brief.html  # 朝刊 HTML テンプレート（サブセクション + バッジ表示）
│   └── data/
│       ├── README.md
│       └── YYYY/MM/DD.json   # 自動生成・自動コミット
├── topics-brief/
│   ├── TOPICS_PROMPT.md      # 話のネタ便プロンプト（3 Subagent 並列 / 質強化版）
│   └── templates/
│       └── email-topics.html # 話のネタ便 HTML テンプレート
└── .github/workflows/
    └── morning-brief.yml     # 毎朝 08:00 JST
```

---

## セットアップ手順

### 1. GitHub Secrets の登録

リポジトリの **Settings → Secrets and variables → Actions → New repository secret** から以下を登録します。

| Key | 必須 | 用途 | 取得先 |
|---|---|---|---|
| `CLAUDE_CODE_OAUTH_TOKEN` | ✅ | Claude Code CLI 認証 | `claude setup-token` で発行 |
| `RESEND_API_KEY` | ✅ | メール送信 | https://resend.com/api-keys |
| `TO_EMAIL` | ✅ | 配信先メール | `loomia.jp@gmail.com` |
| `FROM_EMAIL` | 任意 | 送信元（未設定時は `onboarding@resend.dev`） | Resend で検証済みドメイン |

> Resend 側で送信元ドメインを未検証の場合、初期は `onboarding@resend.dev` から送信されます。

### 2. Actions の有効化

Settings → Actions → General → **Allow all actions and reusable workflows** を選択し、**Read and write permissions** を有効化（data/ への自動コミットに必要）。

### 3. 動作確認

Actions タブ → `morning-brief` → **Run workflow** → 動作させたいブランチ（最新の修正済みブランチ）を選択して手動実行。

> ⚠️ Resend の `onboarding@resend.dev` から送信する場合、Cloudflare WAF が User-Agent 不在のリクエストを `403 / code 1010` で拒否するため、`scripts/send-resend.py` は明示的な User-Agent を必ずセットしています。fork 等で別実装に置き換える場合は同等の対応を忘れないでください。

成功すると：
- `loomia.jp@gmail.com` に HTML メールが届く
- `morning-brief/data/YYYY/MM/DD.json` が自動コミットされる

### 4. 本番運用

`main` にマージ後、毎朝 08:00 JST（cron `0 23 * * *` UTC）に自動配信されます。

---

## 開発・運用ルール

- **タイムゾーンは JST 固定**：すべてのワークフローで `TZ=Asia/Tokyo` を設定
- **数値は推測禁止**：相場・天気・KPI はソース取得が必須
- **24 時間以内優先**：Subagent は当日〜直近 24 時間のソースを最優先で収集
- **失敗時の動作**：朝刊配信が失敗した場合、件名 `[ALERT] morning-brief failed` で `TO_EMAIL` に通知
- **Subagent 並列実行**：
  - 朝刊：**5 Subagent**（相場・経済 / 買取・リユース業界 / AI・テック / **福祉・介護・終活** / **社会トレンド・ライフスタイル**）を Task ツールで並列起動
  - 話のネタ便：3 Subagent（顧客向け / 経営者向け / スタッフ向け）を Task ツールで並列起動
- **データ保存**：日次 JSON は `morning-brief/data/YYYY/MM/DD.json` に保存し、Git 管理（追加 DB なし方針）

---

## ロードマップ

| Phase | 内容 | ステータス |
|---|---|---|
| 1 | 朝刊メール | 構築中 |
| 2 | メモリ機能（前日比 / 30日 Hi-Lo） | 未着手 |
| 3 | 話のネタ便 | 未着手 |
| 4 | 週報・月報 | 未着手 |
| 5 | LINE / Slack / 音声(TTS) 連携 | 未着手 |
| 6 | 緊急速報 | 未着手 |
| 7 | KPI 自動取得（Google Sheets） | 未着手 |
| 8 | 競合監視（Playwright） | 未着手 |
| 9 | ダッシュボード（Next.js） | 未着手 |
| 10 | テスト・CI | 未着手 |

---

## ライセンス

内製システム。社外公開なし。
