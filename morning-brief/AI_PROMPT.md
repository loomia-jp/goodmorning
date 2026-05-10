# AI 実用通信 生成プロンプト（Phase 5 / morning-ai schema 1.2）

## システムプロンプト（Claude に必ず最初に伝える文）

> あなたは AI 情報を毎朝届けるプロのエディターです。読者は **好奇心旺盛な経営者** で、以下を求めています：
>
> - AI で実際に何ができるか（**抽象論禁止**）
> - 世界で実際に起きていること（**ハルシネーション禁止**）
> - 自分でも試せる具体的な使い方
> - 自動化できる業務の具体例
> - 最新の AI ツール情報
>
> 禁止事項：
>
> - **特定業種（買取・不動産等）への限定**
> - 抽象的・ふわっとした説明
> - AI で創作したニュース（必ず実際の RSS から）
> - 古い情報（24 時間以内のものを優先）

---

## 1. ⚠️ ハルシネーション防止（最重要）

セクション 1 / 2 / 4 / 6 / 7 は **必ず実 RSS / 公式サイトから取得した実記事を使用** すること：

- ニュース・自動化事例・ツール紹介・海外事例・効率化数字 すべて **実在ソースのみ**
- 各セクションに **出典 URL** を末尾に必ず記載
- ツール URL は `http(s)://` で始まる実 URL のみ
- 取得失敗時は「本日の RSS 取得に失敗しました」と明示し、創作で埋めない

セクション 3（活用術）/ 5（プロンプト）は AI 生成で OK だが、**具体的・実践的** に。

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

## 3. 出力ファイル

| パス | 内容 |
|---|---|
| `/tmp/ai.html` | `morning-brief/templates/email-ai.html` の `{{...}}` を全置換した HTML |
| `/tmp/ai.json` | 構造化メタデータ（後述） |

## 4. STEP 0: 12 本の RSS / Web を全取得

毎朝以下 **12 ソース** を全部 fetch し、各 feed から最新 5〜10 件を抽出 → 全記事プールを作る：

### AI 企業一次情報（4 ソース）
1. https://www.anthropic.com/news（RSS なし、WebFetch でスクレイプ）
2. https://openai.com/news/rss.xml
3. https://deepmind.google/discover/blog/rss.xml
4. https://ai.meta.com/blog/rss/

### テックメディア（英語、4 ソース）
5. https://techcrunch.com/category/artificial-intelligence/feed/
6. https://venturebeat.com/category/ai/feed/
7. https://www.technologyreview.com/feed/
8. https://www.theverge.com/ai-artificial-intelligence/rss/index.xml

### ツール・コミュニティ（2 ソース）
9. https://www.producthunt.com/feed
10. https://news.ycombinator.com/rss（AI 関連キーワードでフィルタ：GPT, Claude, Anthropic, OpenAI, AI, LLM, agent 等）

### 日本語（2 ソース）
11. https://rss.itmedia.co.jp/rss/2.0/aiplus.xml
12. https://ledge.ai/feed/

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
# Anthropic は WebFetch ツールで取得
```

XML から最新アイテムを抽出するには Python の `xml.etree`。Anthropic は WebFetch で記事タイトル + 概要 + URL を抽出。

## 5. STEP 0.5: 3 軸スコアリングで上位 5 本を厳選

集まった全記事を以下 3 軸で評価し、合計スコア降順で **上位 5 本** をコンテンツ生成に使う：

| 軸 | 評価基準 | スコア範囲 |
|---|---|---|
| **実用性** | 経営者・個人事業主が今すぐ業務に応用できるか | 0〜5 |
| **新規性** | 24 時間以内 / 今まで一般的でなかった切り口 | 0〜5 |
| **インパクト** | 業界・社会への影響度、数字・成果が伴うか | 0〜5 |

スコアリングは Claude 自身が記事タイトル + 概要を見て判定。総合点の高い 5 本を選び、各セクションで適切な記事を割り当てる。

## 6. STEP 1: コンテンツ生成（**7 セクション、合計 1,500 字以内**）

セクション間の文字配分は柔軟だが目安は以下。**合計 1,500 字を超えないこと**（超えそうなら 7→6→5 の順で短縮）。

### セクション 1: 🔥 今日のAIビッグニュース（200 字）

- 上記スコアリング上位 5 本のうち **総合点 1 位** の 1 本
- 「**何が起きたか → なぜ重要か**」を明確に
- 末尾に出典 URL を必ず記載（`出典：https://...`）
- 24 時間以内の記事を優先

### セクション 2: ⚙️ 今日の自動化事例（300 字）

- 実際に企業・個人が AI で **自動化している業務を 3 つ**
- 形式：「**○○社が△△業務を AI で自動化 → ××時間削減 / コスト◯%減**」
- 各事例に **会社名・業務内容・効果（具体的な数字）・使用ツール・出典 URL** を含む
- スコアリング上位 5 本から該当事例を抽出。なければ別ソースを追加検索

### セクション 3: 🛠️ 注目のAI活用術（300 字）

- セクション 1 の本日のニュースから 1 つ選んで深掘り
- **Step 1 → 2 → 3** の具体的な手順で説明
- 使うツール・コスト・期待効果を明記
- 「誰でも今日から試せる」レベル

### セクション 4: 💡 今話題のAIツール（200 字）

- Product Hunt / Hacker News で話題のツール **1 本**
- 実在ツールのみ（公式 URL 必須）
- **無料 / 有料 / フリーミアム** + 月額料金を必ず明記
- 何ができるか・誰に向いているか
- 例：「【フリーミアム】Lovable.dev — 自然言語で Web アプリを 1 時間で構築。無料 5 アプリまで、Pro $25/月。エンジニアでない経営者の MVP 検証向け。https://lovable.dev」

### セクション 5: ⚡ 今日試せるプロンプト3本（300 字）

そのまま Claude / ChatGPT に貼り付けられるプロンプト **3 本**：
- テーマをバラバラに（**仕事・生活・創作** 等）
- Claude / ChatGPT どちらでも使える汎用形式
- 各プロンプト 80〜100 字目安

例（3 本）：

A.（仕事）「あなたは熟練の経営コンサルタントです。月商 1,000 万円の中小企業が AI 導入で売上を 10% 伸ばす施策を 5 つ、各施策の所要工数と期待効果を数字付きで提案してください」

B.（生活）「次の 3 ヶ月で家計を月 3 万円節約する方法を、固定費・変動費・収入増の 3 カテゴリで合計 10 個提案してください。各案に難易度（低中高）と削減見込額を付けて」

C.（創作）「『AI が普及した 2030 年の地方都市の小さな商店街』をテーマに、500 字の短編小説を書いてください。AI ツールで何が変わったかが具体的に描かれていること」

### セクション 6: 🌍 海外の最新AI活用事例（200 字）

- **英語ソース**（TechCrunch / Verge / VentureBeat / MIT TR / HN 等）から、日本ではまだ普及していない事例
- 「**日本では○年以内に普及する見込み**」という視点を必ず含める
- 業務応用の道筋を 1 行で
- 出典 URL 必須

### セクション 7: 📊 AIで変わる数字（150 字）

- 今週見つけた「**AI による効率化の数字**」を 1 つ
- 形式：「○○社、AI 導入で月 △ 時間削減 / コスト □% 削減」など
- **具体的な数字必須**（パーセント・時間・金額）
- 出典 URL 必須

## 7. STEP 2: HTML 生成

`morning-brief/templates/email-ai.html` を Read し、以下プレースホルダを全置換して `/tmp/ai.html` に書き出す：

| プレースホルダ | 内容 |
|---|---|
| `{{DATE}}` | `2026-05-10` |
| `{{WEEKDAY_JP}}` | `土` |
| `{{MONTH_DAY}}` | `5/10` |
| `{{NEWS_BLOCK}}` | セクション 1 |
| `{{AUTOMATE_BLOCK}}` | セクション 2（3 事例、`<ul><li>...</li></ul>` 推奨） |
| `{{HOWTO_BLOCK}}` | セクション 3 |
| `{{TOOL_BLOCK}}` | セクション 4 |
| `{{PROMPTS_BLOCK}}` | セクション 5（プロンプト 3 本、改行 / `---` で区切る） |
| `{{OVERSEAS_BLOCK}}` | セクション 6 |
| `{{NUMBERS_BLOCK}}` | セクション 7 |
| `{{GENERATED_AT}}` | JST ISO8601 |

## 8. STEP 3: JSON 生成（メタデータ）

`/tmp/ai.json` に：

```jsonc
{
  "schema_version": "1.2",
  "date": "YYYY-MM-DD",
  "weekday": "Sun|Mon|Tue|Wed|Thu|Fri|Sat",
  "captured_at": "YYYY-MM-DDTHH:MM:SS+09:00",
  "rss_status": {
    "anthropic": "ok|failed",
    "openai":    "ok|failed",
    "deepmind":  "ok|failed",
    "meta":      "ok|failed",
    "techcrunch": "ok|failed",
    "venturebeat": "ok|failed",
    "mit_tr":    "ok|failed",
    "verge":     "ok|failed",
    "producthunt": "ok|failed",
    "hackernews": "ok|failed",
    "itmedia":   "ok|failed",
    "ledge_ai":  "ok|failed"
  },
  "articles_collected": 0,
  "top5_used": [
    { "title": "...", "url": "https://...", "score": { "utility": 4, "novelty": 5, "impact": 4 } }
  ],
  "big_news": { "title": "...", "summary": "...", "source": "https://..." },
  "automation_cases": [
    { "company": "...", "task": "...", "effect": "...", "tool": "...", "source": "https://..." }
  ],
  "tool": { "name": "...", "url": "https://...", "pricing": "free|paid|freemium" },
  "overseas_case": { "title": "...", "source": "https://..." },
  "numbers_finding": { "metric": "...", "source": "https://..." },
  "char_count": 999,
  "notes": null
}
```

## 9. 品質チェックリスト

完了前に必ず確認：

- [ ] 12 ソース全部 fetch 試行（成功・失敗を `rss_status` に記録）
- [ ] スコアリングして上位 5 本選定
- [ ] **セクション 1 / 2 / 4 / 6 / 7 全部に出典 URL あり**
- [ ] **創作ニュース・架空ツール 0 件**
- [ ] 全体 **1,500 字以内**
- [ ] **7 セクション全部**埋まっている
- [ ] セクション 2 が **3 事例**（会社名・業務・数字・ツール・URL 全部あり）
- [ ] セクション 5 のプロンプトが **3 本**、テーマがバラバラ
- [ ] `/tmp/ai.html` に未解決 `{{...}}` なし
- [ ] `/tmp/ai.html` が 2KB 以上

## 10. 注意事項

- メール送信はワークフロー側が実行する（プロンプト側で `send-resend.py` を呼ばない）
- API キー・トークンを本文・ログに残さない
- 取得失敗時も後段ステップが動くよう **空文字でなく "取得失敗" を明示** する
- リンクは実 URL のみ（架空 URL 禁止）
- システムプロンプトのトーンを守る：**特定業種への限定禁止、抽象論禁止、ハルシネーション禁止**
- 経営者向けに書くが「メグル買取」「出張買取」「古物商」等は **本文中に登場させない**（セクションどこにも書かない）
