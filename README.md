# メグル買取 経営インテリジェンスシステム v2

代表 偉吹（Ibuki）向けに、毎朝の経営判断を支える情報を自動配信する社内システムです。

GitHub Actions（cron） + Claude Code CLI + Resend で構成されています。

---

## 配信物（最終形）

| 配信物 | 配信時刻(JST) | チャネル | ステータス |
|---|---|---|---|
| 話のネタ便 | 毎朝 07:00 | Email | **Phase 3（実装済）** |
| 朝刊 Brief | 毎朝 08:00 | Email | **Phase 1（実装済）** |
| 週報 | 日曜 09:00 | Email | **Phase 4（実装済）** |
| 月報 | 月初 10:00 | Email | **Phase 4（実装済）** |
| 緊急速報 | 随時 | Email | Phase 6 |

> Phase 5 で LINE / Slack / 音声(TTS) 連携を追加予定。

---

## ディレクトリ構成

```
.
├── README.md
├── .gitignore
├── scripts/
│   ├── send-resend.py             # Resend 経由のメール送信（User-Agent 設定済 / 403/1010 対策）
│   ├── memory-saver.py            # 日次 JSON をスキーマ検証付きで保存（v1.0/1.1/1.2 対応）
│   └── validate-bundle.py         # 出力 JSON / HTML の妥当性チェック
├── morning-brief/
│   ├── SCHEMA.md                  # 日次・週次・月次・話のネタ便スキーマ
│   ├── PROMPT.md                  # 朝刊プロンプト（5 Subagent 並列）
│   ├── TOPICS_PROMPT.md           # 話のネタ便プロンプト（3 Subagent 並列）
│   ├── WEEKLY_PROMPT.md           # 週報プロンプト（4 Subagent 並列）
│   ├── MONTHLY_PROMPT.md          # 月報プロンプト（4 Subagent 並列）
│   ├── templates/
│   │   ├── email-brief.html       # 朝刊 HTML テンプレート
│   │   ├── email-topics.html      # 話のネタ便 HTML テンプレート
│   │   ├── email-weekly.html      # 週報 HTML テンプレート
│   │   └── email-monthly.html     # 月報 HTML テンプレート
│   └── data/
│       ├── README.md
│       └── YYYY/MM/DD.json        # 朝刊が自動生成・自動コミット
└── .github/workflows/
    ├── morning-brief.yml          # 毎朝 08:00 JST
    ├── morning-topics.yml         # 毎朝 07:00 JST
    ├── weekly-report.yml          # 毎週日曜 09:00 JST
    └── monthly-report.yml         # 毎月 1 日 10:00 JST
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

Actions タブから配信物ごとのワークフローを **Run workflow** で手動実行できます：

| ワークフロー | スケジュール（JST） | cron（UTC） | 手動入力 |
|---|---|---|---|
| `morning-topics` | 毎朝 07:00 | `0 22 * * *` | 対象日 |
| `morning-brief` | 毎朝 08:00 | `0 23 * * *` | 対象日 |
| `weekly-report` | 毎週日曜 09:00 | `0 0 * * 0` | 週末日 / 訪問件数・成約件数・売上・代表メモ |
| `monthly-report` | 毎月 1 日 10:00 | `0 1 1 * *` | 対象月（YYYY-MM） |

> ⚠️ Resend の `onboarding@resend.dev` から送信する場合、Cloudflare WAF が User-Agent 不在のリクエストを `403 / code 1010` で拒否するため、`scripts/send-resend.py` は明示的な User-Agent を必ずセットしています。fork 等で別実装に置き換える場合は同等の対応を忘れないでください。

成功すると：
- `loomia.jp@gmail.com` に HTML メールが届く
- 朝刊は `morning-brief/data/YYYY/MM/DD.json` が自動コミットされる（話のネタ便・週報・月報はメール送信のみ）

### 4. 本番運用

> 🔴 **重要：cron 自動実行はリポジトリの「デフォルトブランチ」のワークフローしか発火しません。**
> Settings → Branches → Default branch を `main` に変更してください（GitHub の API 経由では変更不可、UI 操作のみ）。
> 切り替え後は Actions タブで各ワークフローの **Last run** に scheduled が出るようになります。

`main` がデフォルトブランチである限り、上記スケジュールで自動配信されます。週報・月報は実行頻度が低いため各ワークフローに **keep-alive ステップ** を組み込み、リポジトリが 50 日以上停滞した場合は空コミットで触って GitHub の自動停止（60 日無活動でスケジュールが無効化される仕様）を回避します。

---

## 開発・運用ルール

- **タイムゾーンは JST 固定**：すべてのワークフローで `TZ=Asia/Tokyo` を設定
- **数値は推測禁止**：相場・天気・KPI はソース取得が必須
- **24 時間以内優先**：Subagent は当日〜直近 24 時間のソースを最優先で収集
- **失敗時の動作**：朝刊配信が失敗した場合、件名 `[ALERT] morning-brief failed` で `TO_EMAIL` に通知
- **Subagent 並列実行**：
  - 朝刊：**5 Subagent**（相場・経済 / 買取・リユース業界 / AI・テック / 福祉・介護・終活 / 社会トレンド・ライフスタイル）
  - 話のネタ便：**3 Subagent**（顧客向け / 経営者向け / スタッフ向け）
  - 週報：**4 Subagent**（相場推移 / 競合総括 / 来週予測 / KPI レビュー）
  - 月報：**4 Subagent**（月次相場 / 業界トレンド / 中長期戦略 / 福祉・社会トレンド）
- **データ保存**：日次 JSON は `morning-brief/data/YYYY/MM/DD.json` に保存し、Git 管理（追加 DB なし方針）

---

## ロードマップ

| Phase | 内容 | ステータス |
|---|---|---|
| 1 | 朝刊メール | **実装済（v1.2 / 5 Subagent）** |
| 2 | メモリ機能（前日比 / 30日 Hi-Lo） | 部分着手（簡易メモリのみ） |
| 3 | 話のネタ便 | **実装済（3 Subagent）** |
| 4 | 週報・月報 | **実装済（4 Subagent / keep-alive 付き）** |
| 5 | LINE / Slack / 音声(TTS) 連携 | 未着手 |
| 6 | 緊急速報 | 未着手 |
| 7 | KPI 自動取得（Google Sheets） | 未着手 |
| 8 | 競合監視（Playwright） | 未着手 |
| 9 | ダッシュボード（Next.js） | 未着手 |
| 10 | テスト・CI | 未着手 |

---

## ライセンス

内製システム。社外公開なし。
