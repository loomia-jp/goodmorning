#!/usr/bin/env python3
"""Sanity-check the artifacts produced by the morning-brief workflow before sending.

Validates:
  - JSON snapshot conforms to the daily schema (delegates to memory_saver.validate)
  - HTML body has no unresolved {{PLACEHOLDER}} tokens
  - HTML body is non-trivial in size (>2 KB)

Usage:
    python3 scripts/validate-bundle.py \
        --json /tmp/today.json \
        --html /tmp/brief.html
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PLACEHOLDER_RE = re.compile(r"\{\{\s*[A-Z0-9_]+\s*\}\}")
MIN_HTML_BYTES = 2048


def _load_validator():
    spec = importlib.util.spec_from_file_location(
        "memory_saver", REPO_ROOT / "scripts" / "memory-saver.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod.validate, mod.ValidationError


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate brief output bundle.")
    parser.add_argument("--json", required=True, help="Path to candidate snapshot JSON")
    parser.add_argument("--html", required=True, help="Path to rendered HTML body")
    args = parser.parse_args()

    failed = False

    # --- JSON ---
    json_path = pathlib.Path(args.json)
    if not json_path.exists():
        print(f"[validate-bundle] ERROR: json not found: {json_path}", file=sys.stderr)
        return 1
    try:
        bundle = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[validate-bundle] ERROR: invalid JSON: {e}", file=sys.stderr)
        return 1

    validate, ValidationError = _load_validator()
    try:
        validate(bundle)
        print(f"[validate-bundle] JSON OK ({json_path.name})")
    except ValidationError as e:
        print(f"[validate-bundle] JSON FAILED: {e}", file=sys.stderr)
        failed = True

    # --- HTML ---
    html_path = pathlib.Path(args.html)
    if not html_path.exists():
        print(f"[validate-bundle] ERROR: html not found: {html_path}", file=sys.stderr)
        return 1
    html = html_path.read_text(encoding="utf-8")
    size = len(html.encode("utf-8"))
    if size < MIN_HTML_BYTES:
        print(f"[validate-bundle] HTML FAILED: only {size} bytes (<{MIN_HTML_BYTES})", file=sys.stderr)
        failed = True

    leftovers = PLACEHOLDER_RE.findall(html)
    if leftovers:
        unique = sorted(set(leftovers))
        print(f"[validate-bundle] HTML FAILED: unresolved placeholders {unique}", file=sys.stderr)
        failed = True

    if not failed:
        print(f"[validate-bundle] HTML OK ({size} bytes)")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
