#!/usr/bin/env python3
"""Validate a daily snapshot JSON and save it under morning-brief/data/YYYY/MM/DD.json.

Usage:
    python3 scripts/memory-saver.py --input /tmp/today.json [--dry-run]

The input JSON must conform to the daily schema in morning-brief/SCHEMA.md.
Validation errors abort with non-zero exit so a broken bundle is never committed.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from datetime import datetime

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_ROOT = REPO_ROOT / "morning-brief" / "data"

REQUIRED_TOP = ["schema_version", "date", "weekday", "captured_at",
                "market", "weather_osaka", "kpi", "subagent_meta"]
REQUIRED_LIST_FIELDS = ["highlights", "alerts", "ai_news",
                        "competitor_moves", "auctions_top3",
                        "subsidies_deadline_within_30d"]
MARKET_KEYS = ["gold_jpy_g", "platinum_jpy_g", "silver_jpy_g",
               "usdjpy", "eurjpy", "nikkei", "topix",
               "valuence_9270", "komehyo_2780", "geo_2681"]
WEATHER_KEYS = ["main", "temp_high", "temp_low", "rain_prob"]
KPI_KEYS = ["visits", "deals", "revenue_jpy"]
SUBAGENT_KEYS = ["agent_market_status", "agent_industry_status",
                 "agent_ai_status", "agent_society_status", "notes"]
SUBAGENT_STATUSES = {"ok", "partial", "failed"}


class ValidationError(Exception):
    pass


def _require_keys(obj: dict, keys: list[str], path: str) -> None:
    missing = [k for k in keys if k not in obj]
    if missing:
        raise ValidationError(f"{path}: missing keys {missing}")


def _require_number_or_null(obj: dict, key: str, path: str) -> None:
    v = obj.get(key)
    if v is None:
        return
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValidationError(f"{path}.{key}: must be number or null, got {type(v).__name__}")


def _require_str_or_null(obj: dict, key: str, path: str) -> None:
    v = obj.get(key)
    if v is not None and not isinstance(v, str):
        raise ValidationError(f"{path}.{key}: must be string or null")


def validate(bundle: dict) -> None:
    if not isinstance(bundle, dict):
        raise ValidationError("root: must be object")

    _require_keys(bundle, REQUIRED_TOP, "root")

    # date / weekday
    try:
        datetime.strptime(bundle["date"], "%Y-%m-%d")
    except (ValueError, TypeError):
        raise ValidationError(f"date: invalid format, expected YYYY-MM-DD, got {bundle['date']!r}")
    if bundle["weekday"] not in {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}:
        raise ValidationError(f"weekday: invalid value {bundle['weekday']!r}")

    # market
    market = bundle["market"]
    if not isinstance(market, dict):
        raise ValidationError("market: must be object")
    _require_keys(market, MARKET_KEYS, "market")
    for k in MARKET_KEYS:
        _require_number_or_null(market, k, "market")

    # weather
    weather = bundle["weather_osaka"]
    if not isinstance(weather, dict):
        raise ValidationError("weather_osaka: must be object")
    _require_keys(weather, WEATHER_KEYS, "weather_osaka")
    _require_str_or_null(weather, "main", "weather_osaka")
    for k in ("temp_high", "temp_low", "rain_prob"):
        _require_number_or_null(weather, k, "weather_osaka")

    # kpi
    kpi = bundle["kpi"]
    if not isinstance(kpi, dict):
        raise ValidationError("kpi: must be object")
    _require_keys(kpi, KPI_KEYS, "kpi")
    for k in KPI_KEYS:
        _require_number_or_null(kpi, k, "kpi")

    # list fields (allowed to be empty arrays but key must exist)
    for k in REQUIRED_LIST_FIELDS:
        if k not in bundle:
            raise ValidationError(f"root.{k}: required (use [] when empty)")
        if not isinstance(bundle[k], list):
            raise ValidationError(f"root.{k}: must be array")

    # subagent_meta
    meta = bundle["subagent_meta"]
    if not isinstance(meta, dict):
        raise ValidationError("subagent_meta: must be object")
    _require_keys(meta, SUBAGENT_KEYS, "subagent_meta")
    for k in ("agent_market_status", "agent_industry_status",
              "agent_ai_status", "agent_society_status"):
        if meta[k] not in SUBAGENT_STATUSES:
            raise ValidationError(f"subagent_meta.{k}: invalid status {meta[k]!r}")
    _require_str_or_null(meta, "notes", "subagent_meta")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and save a daily snapshot JSON.")
    parser.add_argument("--input", required=True, help="Path to candidate JSON")
    parser.add_argument("--dry-run", action="store_true", help="Validate only; do not write")
    args = parser.parse_args()

    in_path = pathlib.Path(args.input)
    if not in_path.exists():
        print(f"[memory-saver] ERROR: input not found: {in_path}", file=sys.stderr)
        return 1

    try:
        bundle = json.loads(in_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[memory-saver] ERROR: invalid JSON: {e}", file=sys.stderr)
        return 1

    try:
        validate(bundle)
    except ValidationError as e:
        print(f"[memory-saver] VALIDATION FAILED: {e}", file=sys.stderr)
        return 2

    if args.dry_run:
        print(f"[memory-saver] OK (dry-run) — date={bundle['date']}")
        return 0

    date_str = bundle["date"]  # YYYY-MM-DD
    yyyy, mm, dd = date_str.split("-")
    out_dir = DATA_ROOT / yyyy / mm
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{dd}.json"
    out_path.write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    print(f"[memory-saver] wrote {out_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
