#!/usr/bin/env python3
"""morning-ai のテンプレート置換を決定論的に実行するレンダラー。

Claude Code が /tmp/ai.json を生成した後、本スクリプトが
morning-brief/templates/email-ai.html の {{...}} プレースホルダを
JSON 内の placeholders から置換して /tmp/ai.html を書き出す。

これにより「Claude がテンプレ置換ステップを忘れて未置換のまま終わる」
事故を防ぐ。

Usage:
    python3 scripts/render-ai-email.py
    # 入力: /tmp/ai.json    （Claude Code が生成）
    # 入力: morning-brief/templates/email-ai.html （リポジトリ）
    # 出力: /tmp/ai.html

JSON 形式：
    {
      "placeholders": {
        "DATE": "2026-05-10",
        "WEEKDAY_JP": "土",
        "MONTH_DAY": "5/10",
        "NEWS_BLOCK": "<p>...</p>",
        "AUTOMATE_BLOCK": "<ul>...</ul>",
        "HOWTO_BLOCK": "...",
        "TOOL_BLOCK": "...",
        "PROMPTS_BLOCK": "...",
        "OVERSEAS_BLOCK": "...",
        "AGENT_TOOL_BLOCK": "...",
        "NUMBERS_BLOCK": "...",
        "GENERATED_AT": "2026-05-10T04:17:00+09:00"
      },
      ...metadata...
    }

未置換が残った場合 / 必須キーが欠けた場合は exit 1 で異常終了する
（後段の Verify ステップが拾えるよう ::error:: でログ出力）。
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE_PATH = REPO_ROOT / "morning-brief" / "templates" / "email-ai.html"
JSON_PATH = pathlib.Path("/tmp/ai.json")
OUT_PATH = pathlib.Path("/tmp/ai.html")

REQUIRED_PLACEHOLDERS = {
    "DATE",
    "WEEKDAY_JP",
    "MONTH_DAY",
    "NEWS_BLOCK",
    "AUTOMATE_BLOCK",
    "HOWTO_BLOCK",
    "TOOL_BLOCK",
    "PROMPTS_BLOCK",
    "OVERSEAS_BLOCK",
    "AGENT_TOOL_BLOCK",
    "NUMBERS_BLOCK",
    "GENERATED_AT",
}

PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Z_][A-Z_0-9]*)\s*\}\}")


def die(msg: str) -> None:
    print(f"::error::{msg}", file=sys.stderr)
    sys.exit(1)


def main() -> int:
    if not JSON_PATH.exists():
        die(f"input JSON not found: {JSON_PATH}")
    if not TEMPLATE_PATH.exists():
        die(f"template not found: {TEMPLATE_PATH}")

    try:
        data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        die(f"invalid JSON in {JSON_PATH}: {e}")
        return 1  # unreachable

    placeholders = data.get("placeholders") or {}
    if not isinstance(placeholders, dict):
        die(f"'placeholders' field must be an object in {JSON_PATH}")

    # 必須キーチェック
    missing = sorted(REQUIRED_PLACEHOLDERS - set(placeholders.keys()))
    if missing:
        die(f"missing required placeholders in /tmp/ai.json: {missing}")

    # 空文字チェック（全 12 プレースホルダ非空必須）
    empty = sorted(k for k in REQUIRED_PLACEHOLDERS if not str(placeholders.get(k, "")).strip())
    if empty:
        die(f"empty placeholders in /tmp/ai.json: {empty}")

    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    # テンプレに含まれるプレースホルダ集合と、JSON 側の集合が一致するか軽くチェック
    template_keys = set(PLACEHOLDER_RE.findall(template))
    extra_in_template = template_keys - REQUIRED_PLACEHOLDERS
    if extra_in_template:
        print(
            f"::warning::template has placeholders not in REQUIRED set: {sorted(extra_in_template)}",
            file=sys.stderr,
        )
    missing_in_template = REQUIRED_PLACEHOLDERS - template_keys
    if missing_in_template:
        print(
            f"::warning::template does not use these required placeholders: {sorted(missing_in_template)}",
            file=sys.stderr,
        )

    # 置換実行
    rendered = template
    for key in template_keys | REQUIRED_PLACEHOLDERS:
        if key in placeholders:
            rendered = rendered.replace("{{" + key + "}}", str(placeholders[key]))

    # 未置換チェック
    leftovers = PLACEHOLDER_RE.findall(rendered)
    if leftovers:
        unique = sorted(set(leftovers))
        die(f"unresolved placeholders after render: {unique}")

    OUT_PATH.write_text(rendered, encoding="utf-8")
    size = OUT_PATH.stat().st_size
    print(f"[render] wrote {OUT_PATH} ({size} bytes, {len(rendered)} chars)")
    print(f"[render] placeholders replaced: {len(REQUIRED_PLACEHOLDERS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
