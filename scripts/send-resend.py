#!/usr/bin/env python3
"""Send HTML email via the Resend API.

Usage:
    python3 scripts/send-resend.py \
        --subject "朝刊 Brief 2026-05-05" \
        --html-file /tmp/brief.html \
        --to "loomia.jp@gmail.com" \
        [--from "brief@example.com"]

Reads RESEND_API_KEY from env. Exits non-zero on failure with a stderr message
suitable for surfacing in GitHub Actions logs.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

RESEND_ENDPOINT = "https://api.resend.com/emails"
DEFAULT_FROM = "Meguru Brief <onboarding@resend.dev>"


def build_payload(args: argparse.Namespace, html: str) -> dict:
    payload = {
        "from": args.from_addr or os.environ.get("FROM_EMAIL") or DEFAULT_FROM,
        "to": [a.strip() for a in args.to.split(",") if a.strip()],
        "subject": args.subject,
        "html": html,
    }
    if args.reply_to:
        payload["reply_to"] = args.reply_to
    return payload


def send(payload: dict, api_key: str) -> dict:
    req = urllib.request.Request(
        RESEND_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"[send-resend] HTTP {e.code}: {detail}") from None
    except urllib.error.URLError as e:
        raise SystemExit(f"[send-resend] network error: {e.reason}") from None


def main() -> int:
    parser = argparse.ArgumentParser(description="Send HTML email via Resend.")
    parser.add_argument("--subject", required=True)
    parser.add_argument("--html-file", required=True, help="Path to HTML body file")
    parser.add_argument("--to", required=True, help="Comma-separated recipient list")
    parser.add_argument("--from", dest="from_addr", default=None)
    parser.add_argument("--reply-to", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key and not args.dry_run:
        print("[send-resend] ERROR: RESEND_API_KEY not set", file=sys.stderr)
        return 1

    html_path = pathlib.Path(args.html_file)
    if not html_path.exists():
        print(f"[send-resend] ERROR: html file not found: {html_path}", file=sys.stderr)
        return 1
    html = html_path.read_text(encoding="utf-8")

    payload = build_payload(args, html)

    if args.dry_run:
        preview = {**payload, "html": f"<{len(html)} chars omitted>"}
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        return 0

    result = send(payload, api_key)
    print(f"[send-resend] sent: id={result.get('id')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
