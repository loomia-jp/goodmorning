# 朝刊データアーカイブ

本ディレクトリは朝刊 Brief ワークフローが自動生成・自動コミットする日次スナップショット JSON の保存先です。

## 構成

```
data/
├── README.md                # このファイル
├── YYYY/MM/DD.json          # 日次スナップショット（Phase 1〜）
├── weekly/YYYY-WW.json      # 週次サマリー（Phase 4 以降）
├── monthly/YYYY-MM.json     # 月次サマリー（Phase 4 以降）
└── alerts/                  # 緊急速報ログ（Phase 6 以降）
```

スキーマ定義は `../SCHEMA.md` を参照してください。

## 運用ルール

- **手動編集は原則禁止**。誤った値を修正したい場合は新しい日次ジョブで上書き、または PR 経由でレビュー後に変更
- 過去 JSON は Phase 2 のメモリ機能（前日比 / 30 日 Hi-Lo）の入力になるため、**削除しないこと**
- ワークフローからのコミットメッセージは `chore(data): YYYY-MM-DD daily snapshot` で統一
