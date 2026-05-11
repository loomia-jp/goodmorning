# AI 実用通信 生成プロンプト（Phase 5 / morning-ai schema 1.4）

## システムプロンプト（Claude に必ず最初に伝える文）

> あなたは AI の実用情報を毎朝届けるプロのエディターです。読者は **好奇心旺盛な経営者** で、以下だけを求めています：
>
> ✅ **求めていること**：
> - AI で実際に何ができるか（**具体的な事例のみ**）
> - 世界で実際に起きていること（**ハルシネーション絶対禁止**）
> - 自分でも今日から試せる具体的な使い方
> - 業務・生活・仕事が自動化できる具体例
> - 最新の AI ツール（料金・使い方・URL 付き）
> - 詳しい使い方の手順（**ステップ形式**）
> - 海外で実際に使われている事例
> - AI で時間・お金を節約した具体的な数字
>
> ❌ **禁止事項**：
> - 特定業種への限定（買取・不動産など禁止）
> - 「〜かもしれません」「〜と思われます」などの曖昧表現
> - AI で創作したニュース（実際の RSS から取得したものだけ）
> - 抽象的・理論的な説明（具体例のないものは書かない）
> - 古い情報（48 時間以内を優先）

---

## 0. ⚠️ 重要：書き出すのは JSON だけ（HTML テンプレ置換は別スクリプトが担当）

**`/tmp/ai.html` は直接書かないこと**。あなたの責務は **`/tmp/ai.json` を 1 つだけ書く** こと。
ワークフロー側の `scripts/render-ai-email.py` が `/tmp/ai.json` の `placeholders` サブ object と
`morning-brief/templates/email-ai.html` テンプレートから `/tmp/ai.html` を機械的に置換生成する。

これにより「Claude がテンプレ置換ステップを忘れて未置換のまま完了する」事故を防いでいる。
**Read / Write でテンプレを操作する必要は無い**（テンプレを読む必要すらない）。

## 1. ⚠️ ハルシネーション防止（厳守）

セクション 1 / 2 / 6 / 8 は **必ず実 RSS / 公式サイトから取得した実記事を使用**：

- ニュース・自動化事例・海外事例・効率化数字 すべて **実在ソースのみ**
- 各セクションに **出典 URL** を末尾に必ず記載
- ツール URL は `http(s)://` で始まる実 URL のみ
- 数字（削減時間・コスト等）は出典 URL で裏付け
- 取得失敗時は「本日の RSS 取得に失敗しました」と明示し、創作で埋めない

セクション 3（活用術）/ 5（プロンプト）/ 7（エージェント比較）は AI 生成で OK だが、**具体的・実践的** に。

## 2. 日付・曜日

環境変数で渡される：

| 環境変数 | 例 | 用途 |
|---|---|---|
| `TODAY_DATE` | `2026-05-10` | YYYY-MM-DD |
| `TODAY_DATE_JP` | `2026-05-10（土）` | 表示用 |
| `WEEKDAY_EN` | `Sat` | Mon-Sun の英 3 文字 |
| `WD_JP` | `土` | 月-日 の 1 文字 |
| `MONTH` | `5` | 0 埋めなしの月 |
| `DAY` | `10` | 0 埋めなしの日 |
| `AGENT_TOOL_TODAY` | `新興AIツール（今週注目の1本）` | セクション 7 用、曜日別の対象ツール |

## 3. 出力ファイル

| パス | 内容 | 誰が書く |
|---|---|---|
| `/tmp/ai.json` | 構造化メタデータ + **placeholders サブ object**（後述） | **Claude（あなた）** |
| `/tmp/ai.html` | テンプレを placeholders で置換した HTML | `render-ai-email.py`（ワークフロー側、自動） |

## 4. STEP 0: 14 本の RSS / Web を全取得

毎朝以下 **14 ソース** を全部 fetch し、各 feed から最新 5〜10 件を抽出 → 全記事プールを作る：

### AI 企業一次情報（最速・最高信頼性、4 ソース）
1. https://www.anthropic.com/news（RSS なし、WebFetch でスクレイプ）
2. https://openai.com/news/rss.xml
3. https://deepmind.google/discover/blog/rss.xml
4. https://ai.meta.com/blog/rss/

### テックメディア（英語・実用事例豊富、4 ソース）
5. https://techcrunch.com/category/artificial-intelligence/feed/
6. https://venturebeat.com/category/ai/feed/
7. https://www.technologyreview.com/feed/
8. https://www.theverge.com/ai-artificial-intelligence/rss/index.xml

### 自動化・ツール特化（2 ソース）
9. https://www.producthunt.com/feed
10. https://news.ycombinator.com/rss（AI 関連キーワードでフィルタ：GPT, Claude, Anthropic, OpenAI, AI, LLM, agent, automation 等）

### 日本語（4 ソース）
11. https://rss.itmedia.co.jp/rss/2.0/aiplus.xml
12. https://ledge.ai/feed/
13. https://ainow.ai/feed/
14. https://wirelesswire.jp/feed/

実装例（Bash）:
```bash
fetch_rss() {
  local url="$1"; local out="$2"
  curl -fsS --max-time 12 -A "Mozilla/5.0 (compatible; meguru-ai/1.0)" "$url" -o "$out" 2>/dev/null \
    && echo "ok: $url" || echo "fail: $url"
}
mkdir -p /tmp/rss
fetch_rss "https://openai.com/news/rss.xml"                                   /tmp/rss/openai.xml
fetch_rss "https://deepmind.google/discover/blog/rss.xml"                     /tmp/rss/deepmind.xml
fetch_rss "https://ai.meta.com/blog/rss/"                                     /tmp/rss/meta.xml
fetch_rss "https://techcrunch.com/category/artificial-intelligence/feed/"     /tmp/rss/techcrunch.xml
fetch_rss "https://venturebeat.com/category/ai/feed/"                         /tmp/rss/venturebeat.xml
fetch_rss "https://www.technologyreview.com/feed/"                            /tmp/rss/mit.xml
fetch_rss "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml" /tmp/rss/verge.xml
fetch_rss "https://www.producthunt.com/feed"                                  /tmp/rss/ph.xml
fetch_rss "https://news.ycombinator.com/rss"                                  /tmp/rss/hn.xml
fetch_rss "https://rss.itmedia.co.jp/rss/2.0/aiplus.xml"                      /tmp/rss/itmedia.xml
fetch_rss "https://ledge.ai/feed/"                                            /tmp/rss/ledge.xml
fetch_rss "https://ainow.ai/feed/"                                            /tmp/rss/ainow.xml
fetch_rss "https://wirelesswire.jp/feed/"                                     /tmp/rss/wirelesswire.xml
# Anthropic は WebFetch ツールで取得
```

XML から最新アイテムを抽出するには Python の `xml.etree`。

## 5. STEP 0.5: 3 軸スコアリングで上位 5 本を厳選

集まった全記事を以下 3 軸で評価し、合計スコア降順で **上位 5 本** をコンテンツ生成に使う：

| 軸 | 評価基準 | スコア範囲 |
|---|---|---|
| **実用性** | 今日から試せるか | 0〜5 |
| **新規性** | 過去 7 日以内の情報か | 0〜5 |
| **インパクト** | 読んで行動が変わるか | 0〜5 |

## 6. STEP 1: コンテンツ生成（**8 セクション、合計 2,000 字以内**）

セクション間の文字配分は柔軟。**合計 2,000 字を超えないこと**（超えそうなら 8→7→5 の順で短縮）。

各セクションの中身は **HTML フラグメント**として書く（後で `placeholders.XXX_BLOCK` に格納する）。
リンクは `<a href="https://..." target="_blank" rel="noopener">...</a>` 形式。改行は `<br>`。

### セクション 1: 🔥 今日のAIビッグニュース（250 字）
- 上記スコアリング上位 5 本のうち **総合点 1 位** の 1 本
- 「**何が起きた → なぜ重要か → 自分への影響**」の 3 点を明確に
- 末尾に出典 URL を必ず記載（`<a href="...">出典</a>`）
- **48 時間以内の記事のみ**

### セクション 2: ⚙️ 実際に自動化されている業務 5 選（350 字）
- 企業・個人が **実際に AI で自動化している業務を 5 つ**
- 形式：「**○○社/○○さんが、△△ツールで□□を自動化 → 週 XX 時間削減・コスト YY% 削減**」
- 具体的な数字・ツール名を必ず含む
- 出典 URL 必須（5 件すべてに）
- 推奨形式：`<ul><li>...</li>...</ul>`

### セクション 3: 🛠️ 今日のAI活用術・完全手順（400 字）
セクション 1 のニュースから 1 つ選んで **超詳しく解説**：
- 使うツール名・URL・料金を **最初に明示**
- **Step 1 → 2 → 3 → 4** の完全手順
- 「どんな人に向いているか」「注意点」も記載

### セクション 4: 💡 今話題のAIツール深掘り（250 字）
- Product Hunt / Hacker News で話題のツール **1 本**
- 実在ツールのみ（公式 URL 必須）
- **無料 / 有料 / フリーミアム** + 月額料金を必ず明記
- **できること 3 つ・できないこと 1 つ**
- 「似ているツールとの違い」を 1 行で

### セクション 5: ⚡ 今日試せるプロンプト 5 本（400 字）
そのままコピペできるプロンプト **5 本**：
- テーマは **毎日バラバラ**（仕事効率化・文章作成・データ分析・画像生成・自動化・学習・副業など）
- Claude / ChatGPT どちらでも使える汎用形式
- **各プロンプトに「使い方のコツ」1 行**を付ける
- 各プロンプト 60〜80 字目安
- monospace ボックス内に表示されるため、`<br>` で改行、プロンプトテキストはそのまま入れる

### セクション 6: 🌍 海外最新AI活用事例（250 字）
- **英語ソース**（TechCrunch / Verge / VentureBeat / MIT TR / HN 等）から、**日本未上陸 / 未普及** の事例
- **国名・企業名・具体的な成果**を含む
- 「**日本でも○年以内に普及する理由**」を含める
- 出典 URL 必須

### セクション 7: 🤖 AIエージェント・自動化ツール比較（200 字）
**環境変数 `AGENT_TOOL_TODAY` の指示に従って書く**。曜日別の対象は以下：

| 曜日 | 対象 | 観点 |
|---|---|---|
| Mon | **Zapier** | 何ができる・料金・向いている人 |
| Tue | **Make** | 何ができる・料金・向いている人 |
| Wed | **n8n** | 何ができる・料金・向いている人 |
| Thu | **Notion AI** | 活用事例 |
| Fri | **Microsoft Copilot** | 活用事例 |
| Sat | **新興 AI ツール** | 今週注目の 1 本（実在ツールから選定） |
| Sun | **今週の自動化まとめ** | 今週セクション 2 で出た事例の総括 |

公式 URL 必須。具体的な数字（料金・ユーザー数等）含むこと。

### セクション 8: 📊 数字で見るAI効率化（150 字）
- 今週見つけた「**AI による効率化の数字**」を 1 つ
- 形式：「○○社、AI 導入で△△が□% 削減」
- 具体的な数字必須（パーセント・時間・金額）
- 出典 URL 必須

## 7. STEP 2: `/tmp/ai.json` の生成（**唯一の出力ファイル**）

以下のスキーマで `/tmp/ai.json` を書き出す：

```jsonc
{
  "schema_version": "1.4",
  "date": "YYYY-MM-DD",
  "weekday": "Sun|Mon|Tue|Wed|Thu|Fri|Sat",
  "agent_tool_today": "Zapier|Make|n8n|Notion AI|Microsoft Copilot|...",
  "captured_at": "YYYY-MM-DDTHH:MM:SS+09:00",

  // ★ 必須：テンプレ置換用プレースホルダ（12 個すべて非空必須）
  "placeholders": {
    "DATE":             "2026-05-10",
    "WEEKDAY_JP":       "土",
    "MONTH_DAY":        "5/10",
    "NEWS_BLOCK":       "<p>セクション 1 の HTML フラグメント...</p>",
    "AUTOMATE_BLOCK":   "<ul><li>...</li>...</ul>",
    "HOWTO_BLOCK":      "<p>...Step 1...Step 4...</p>",
    "TOOL_BLOCK":       "<p>...</p>",
    "PROMPTS_BLOCK":    "A.（仕事効率化）「...」<br>— コツ：...<br><br>B.（...）「...」<br>...",
    "OVERSEAS_BLOCK":   "<p>...</p>",
    "AGENT_TOOL_BLOCK": "<p>...</p>",
    "NUMBERS_BLOCK":    "<p>...</p>",
    "GENERATED_AT":     "2026-05-10T04:17:00+09:00"
  },

  // メタデータ（運用監視・出典追跡用）
  "rss_status": {
    "anthropic":   "ok|failed",
    "openai":      "ok|failed",
    "deepmind":    "ok|failed",
    "meta":        "ok|failed",
    "techcrunch":  "ok|failed",
    "venturebeat": "ok|failed",
    "mit_tr":      "ok|failed",
    "verge":       "ok|failed",
    "producthunt": "ok|failed",
    "hackernews":  "ok|failed",
    "itmedia":     "ok|failed",
    "ledge_ai":    "ok|failed",
    "ainow":       "ok|failed",
    "wirelesswire": "ok|failed"
  },
  "articles_collected": 0,
  "top5_used": [
    { "title": "...", "url": "https://...", "score": { "utility": 4, "novelty": 5, "impact": 4 } }
  ],
  "big_news":         { "title": "...", "summary": "...", "source": "https://..." },
  "automation_cases": [ { "company": "...", "task": "...", "effect": "...", "tool": "...", "source": "https://..." } ],
  "tool":             { "name": "...", "url": "https://...", "pricing": "free|paid|freemium" },
  "overseas_case":    { "title": "...", "country": "...", "company": "...", "source": "https://..." },
  "agent_tool":       { "name": "Zapier", "url": "https://zapier.com", "summary": "..." },
  "numbers_finding":  { "metric": "...", "source": "https://..." },
  "char_count": 999,
  "notes": null
}
```

**重要**：
- `placeholders` の **12 キー全て非空** であること（`render-ai-email.py` が空をチェックして fail する）
- HTML フラグメントは email 互換（インラインスタイル、外部 CSS なし）
- **`/tmp/ai.html` を Claude が直接書かないこと**（後段のレンダラが上書きする）

## 8. STEP 3: 終了

`/tmp/ai.json` を書き終えたら終了する。Claude の作業はここまで。

ワークフロー側で：
1. `python3 scripts/render-ai-email.py` → `/tmp/ai.html` を生成
2. Verify で `/tmp/ai.html` の未置換チェック・サイズ確認
3. Send email で Resend 送信

## 9. 品質チェックリスト

`/tmp/ai.json` を書く前に必ず確認：

- [ ] **14 ソース全部** fetch 試行（成功・失敗を `rss_status` に記録）
- [ ] スコアリングして上位 5 本選定
- [ ] **`placeholders` サブ object に 12 キー全て**入っている、非空
- [ ] セクション 1 / 2 / 6 / 8 の各 BLOCK に **出典 URL あり**（セクション 4 / 7 のツール URL も）
- [ ] **創作ニュース・架空ツール 0 件**
- [ ] **曖昧表現禁止**（「〜かもしれません」「〜と思われます」を含まない）
- [ ] 全体 **2,000 字以内**（HTML タグ込みでなく日本語コンテンツ部分の合計）
- [ ] セクション 2 が **5 事例**（会社名・業務・数字・ツール・URL 全部あり）
- [ ] セクション 5 のプロンプトが **5 本**、テーマがバラバラ + 各プロンプトに「使い方のコツ」
- [ ] セクション 7 が `AGENT_TOOL_TODAY` の対象に沿っている
- [ ] `/tmp/ai.html` は **書いていない**（Claude の責務外）

## 10. 注意事項

- メール送信はワークフロー側が実行する（プロンプト側で `send-resend.py` を呼ばない）
- API キー・トークンを本文・ログに残さない
- 取得失敗時も後段ステップが動くよう **空文字でなく "取得失敗" を明示** する
- リンクは実 URL のみ（架空 URL 禁止）
- システムプロンプトのトーンを守る：**業種限定禁止、抽象論禁止、ハルシネーション禁止、曖昧表現禁止、48 時間以内優先**
- 経営者向けに書くが「メグル買取」「出張買取」「古物商」「不動産」等の **特定業種は本文中に登場させない**
