#!/usr/bin/env python3
"""Validate a daily snapshot JSON and save it under morning-brief/data/YYYY/MM/DD.json.

Usage:
    python3 scripts/memory-saver.py --input /tmp/today.json [--dry-run]

The input JSON must conform to the daily schema (v1.1) in morning-brief/SCHEMA.md.
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

SUPPORTED_SCHEMA_VERSIONS = {"1.0", "1.1"}

REQUIRED_TOP = ["schema_version", "date", "weekday", "captured_at",
                "market", "weather_osaka", "kpi", "subagent_meta"]

# v1.0 fields (always required)
REQUIRED_LIST_FIELDS_V10 = ["highlights", "alerts", "ai_news",
                            "competitor_moves", "auctions_top3",
                            "subsidies_deadline_within_30d"]
# v1.1 additions
REQUIRED_LIST_FIELDS_V11_ADDITIONS = ["secondhand_top5", "brands_news",
                                      "regulations", "welfare_news"]

MARKET_CORE_KEYS = ["gold_jpy_g", "platinum_jpy_g", "silver_jpy_g",
                    "usdjpy", "eurjpy", "nikkei", "topix",
                    "valuence_9270", "komehyo_2780", "geo_2681"]
# v1.1 additions to market (optional fields, validated when present)
MARKET_OPTIONAL_NUMBER_KEYS = ["gold_dod_pct", "platinum_dod_pct", "silver_dod_pct"]
MARKET_OPTIONAL_STRING_KEYS = ["gold_wow_trend", "platinum_wow_trend", "silver_wow_trend"]

WEATHER_KEYS = ["main", "temp_high", "temp_low", "rain_prob"]
WEATHER_OPTIONAL_STRING_KEYS = ["am_pm_note"]

KPI_KEYS = ["visits", "deals", "revenue_jpy"]

# v1.0 keeps agent_society_status; v1.1 renames to agent_welfare_status.
SUBAGENT_KEYS_V10 = ["agent_market_status", "agent_industry_status",
                     "agent_ai_status", "agent_society_status", "notes"]
SUBAGENT_KEYS_V11 = ["agent_market_status", "agent_industry_status",
                     "agent_ai_status", "agent_welfare_status", "notes"]
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


def _validate_item_required_strings(item: dict, keys: list[str], path: str) -> None:
    if not isinstance(item, dict):
        raise ValidationError(f"{path}: must be object")
    for k in keys:
        v = item.get(k)
        if not isinstance(v, str) or not v.strip():
            raise ValidationError(f"{path}.{k}: must be non-empty string")


def _validate_enum(value, allowed: set, path: str, allow_null: bool = False) -> None:
    if value is None and allow_null:
        return
    if value not in allowed:
        raise ValidationError(f"{path}: invalid value {value!r}, expected one of {sorted(allowed)}")


def validate(bundle: dict) -> None:
    if not isinstance(bundle, dict):
        raise ValidationError("root: must be object")

    _require_keys(bundle, REQUIRED_TOP, "root")

    # --- schema_version ---
    sv = bundle["schema_version"]
    if sv not in SUPPORTED_SCHEMA_VERSIONS:
        raise ValidationError(
            f"schema_version: unsupported {sv!r}, expected one of {sorted(SUPPORTED_SCHEMA_VERSIONS)}"
        )
    is_v11 = sv == "1.1"

    # --- date / weekday ---
    try:
        datetime.strptime(bundle["date"], "%Y-%m-%d")
    except (ValueError, TypeError):
        raise ValidationError(f"date: invalid format, expected YYYY-MM-DD, got {bundle['date']!r}")
    if bundle["weekday"] not in {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}:
        raise ValidationError(f"weekday: invalid value {bundle['weekday']!r}")

    # --- market ---
    market = bundle["market"]
    if not isinstance(market, dict):
        raise ValidationError("market: must be object")
    _require_keys(market, MARKET_CORE_KEYS, "market")
    for k in MARKET_CORE_KEYS:
        _require_number_or_null(market, k, "market")
    if is_v11:
        for k in MARKET_OPTIONAL_NUMBER_KEYS:
            _require_number_or_null(market, k, "market")
        for k in MARKET_OPTIONAL_STRING_KEYS:
            _require_str_or_null(market, k, "market")

    # --- weather ---
    weather = bundle["weather_osaka"]
    if not isinstance(weather, dict):
        raise ValidationError("weather_osaka: must be object")
    _require_keys(weather, WEATHER_KEYS, "weather_osaka")
    _require_str_or_null(weather, "main", "weather_osaka")
    for k in ("temp_high", "temp_low", "rain_prob"):
        _require_number_or_null(weather, k, "weather_osaka")
    if is_v11:
        for k in WEATHER_OPTIONAL_STRING_KEYS:
            _require_str_or_null(weather, k, "weather_osaka")

    # --- kpi ---
    kpi = bundle["kpi"]
    if not isinstance(kpi, dict):
        raise ValidationError("kpi: must be object")
    _require_keys(kpi, KPI_KEYS, "kpi")
    for k in KPI_KEYS:
        _require_number_or_null(kpi, k, "kpi")

    # --- list fields (must exist, may be []) ---
    required_lists = list(REQUIRED_LIST_FIELDS_V10)
    if is_v11:
        required_lists += REQUIRED_LIST_FIELDS_V11_ADDITIONS
    for k in required_lists:
        if k not in bundle:
            raise ValidationError(f"root.{k}: required (use [] when empty)")
        if not isinstance(bundle[k], list):
            raise ValidationError(f"root.{k}: must be array")

    # --- per-array element validation ---
    for i, item in enumerate(bundle["highlights"]):
        _validate_item_required_strings(item, ["title", "source", "summary"], f"highlights[{i}]")
        _validate_enum(item.get("impact"), {"high", "medium", "low"}, f"highlights[{i}].impact")

    for i, item in enumerate(bundle["alerts"]):
        _validate_item_required_strings(item, ["title", "source", "summary"], f"alerts[{i}]")
        _validate_enum(item.get("severity"), {"critical", "warning", "info"}, f"alerts[{i}].severity")

    for i, item in enumerate(bundle["ai_news"]):
        _validate_item_required_strings(item, ["title", "source", "summary"], f"ai_news[{i}]")

    for i, item in enumerate(bundle["competitor_moves"]):
        _validate_item_required_strings(item, ["vendor", "title", "source", "summary"],
                                        f"competitor_moves[{i}]")

    for i, item in enumerate(bundle["auctions_top3"]):
        _validate_item_required_strings(item, ["name", "source"], f"auctions_top3[{i}]")
        _require_number_or_null(item, "price", f"auctions_top3[{i}]")

    for i, item in enumerate(bundle["subsidies_deadline_within_30d"]):
        _validate_item_required_strings(item, ["name", "deadline", "source", "summary"],
                                        f"subsidies_deadline_within_30d[{i}]")

    if is_v11:
        for i, item in enumerate(bundle["secondhand_top5"]):
            _validate_item_required_strings(item, ["title", "source"], f"secondhand_top5[{i}]")
            _require_number_or_null(item, "price", f"secondhand_top5[{i}]")
            _validate_enum(item.get("platform"), {"mercari", "yahoo_auction", "other"},
                           f"secondhand_top5[{i}].platform")
        for i, item in enumerate(bundle["brands_news"]):
            _validate_item_required_strings(item, ["brand", "title", "source", "summary"],
                                            f"brands_news[{i}]")
            _validate_enum(item.get("kind"),
                           {"new_release", "discontinued", "international_price", "other"},
                           f"brands_news[{i}].kind")
            _validate_enum(item.get("impact"), {"high", "medium", "low"}, f"brands_news[{i}].impact")
        for i, item in enumerate(bundle["regulations"]):
            _validate_item_required_strings(item, ["title", "source", "summary"], f"regulations[{i}]")
            _validate_enum(item.get("domain"),
                           {"antiques", "tax", "consumer", "ai", "welfare", "other"},
                           f"regulations[{i}].domain")
            _validate_enum(item.get("impact"), {"high", "medium", "low"}, f"regulations[{i}].impact")
        for i, item in enumerate(bundle["welfare_news"]):
            _validate_item_required_strings(item, ["title", "source", "summary"], f"welfare_news[{i}]")
            _validate_enum(item.get("category"),
                           {"policy", "market", "research", "product", "ma", "subsidy", "other"},
                           f"welfare_news[{i}].category")
            _validate_enum(item.get("impact"), {"high", "medium", "low"}, f"welfare_news[{i}].impact")

    # --- subagent_meta ---
    meta = bundle["subagent_meta"]
    if not isinstance(meta, dict):
        raise ValidationError("subagent_meta: must be object")
    expected_keys = SUBAGENT_KEYS_V11 if is_v11 else SUBAGENT_KEYS_V10
    _require_keys(meta, expected_keys, "subagent_meta")
    status_keys = [k for k in expected_keys if k.endswith("_status")]
    for k in status_keys:
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
        print(f"[memory-saver] OK (dry-run) — date={bundle['date']} schema_version={bundle['schema_version']}")
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
