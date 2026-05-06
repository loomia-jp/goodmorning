#!/usr/bin/env python3
"""Validate a daily snapshot JSON and save it under morning-brief/data/YYYY/MM/DD.json.

Usage:
    python3 scripts/memory-saver.py --input /tmp/today.json [--dry-run]

The input JSON must conform to the daily schema (v1.0 / v1.1 / v1.2) in morning-brief/SCHEMA.md.
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

SUPPORTED_SCHEMA_VERSIONS = {"1.0", "1.1", "1.2"}

REQUIRED_TOP = ["schema_version", "date", "weekday", "captured_at",
                "market", "weather_osaka", "kpi", "subagent_meta"]

# v1.0 base list fields
REQUIRED_LIST_FIELDS_V10 = ["highlights", "alerts", "ai_news",
                            "competitor_moves", "auctions_top3",
                            "subsidies_deadline_within_30d"]
# v1.1 additions
REQUIRED_LIST_FIELDS_V11_ADD = ["secondhand_top5", "brands_news",
                                "regulations", "welfare_news"]
# v1.2 additions
REQUIRED_LIST_FIELDS_V12_ADD = ["tech_news", "reuse_market", "lifestyle_trends"]

# v1.0 market core
MARKET_CORE_KEYS = ["gold_jpy_g", "platinum_jpy_g", "silver_jpy_g",
                    "usdjpy", "eurjpy", "nikkei", "topix",
                    "valuence_9270", "komehyo_2780", "geo_2681"]
# v1.1 optional market additions
MARKET_OPT_NUM_V11 = ["gold_dod_pct", "platinum_dod_pct", "silver_dod_pct"]
MARKET_OPT_STR_V11 = ["gold_wow_trend", "platinum_wow_trend", "silver_wow_trend"]
# v1.2 optional market additions
MARKET_OPT_NUM_V12 = ["nydow", "nasdaq", "sp500",
                      "nydow_dod_pct", "nasdaq_dod_pct", "sp500_dod_pct",
                      "btc_jpy", "eth_jpy", "btc_dod_pct", "eth_dod_pct",
                      "wti_usd_bbl", "copper_usd_lb", "wheat_usd_bu"]

WEATHER_KEYS = ["main", "temp_high", "temp_low", "rain_prob"]
WEATHER_OPT_STR = ["am_pm_note"]

KPI_KEYS = ["visits", "deals", "revenue_jpy"]

# Subagent meta keys per version
SUBAGENT_KEYS_V10 = ["agent_market_status", "agent_industry_status",
                     "agent_ai_status", "agent_society_status", "notes"]
SUBAGENT_KEYS_V11 = ["agent_market_status", "agent_industry_status",
                     "agent_ai_status", "agent_welfare_status", "notes"]
SUBAGENT_KEYS_V12 = ["agent_market_status", "agent_industry_status",
                     "agent_ai_status", "agent_welfare_status",
                     "agent_lifestyle_status", "notes"]
SUBAGENT_STATUSES = {"ok", "partial", "failed"}

# Enum sets
IMPACT_SET = {"high", "medium", "low"}
SEVERITY_SET = {"critical", "warning", "info"}
PLATFORM_SET = {"mercari", "yahoo_auction", "other"}
BRAND_KIND_SET = {"new_release", "discontinued", "international_price", "other"}
REG_DOMAIN_SET = {"antiques", "tax", "consumer", "ai", "welfare", "other"}
WELFARE_CATEGORY_V11 = {"policy", "market", "research", "product", "ma", "subsidy", "other"}
WELFARE_CATEGORY_V12 = WELFARE_CATEGORY_V11 | {"facility", "home_care", "estate", "inheritance"}
TECH_CATEGORY_SET = {"semiconductor", "quantum_space", "robotics_av", "other"}
REUSE_CATEGORY_SET = {"antiques_art", "instruments_camera_watches", "vehicles",
                      "cross_border_ec", "other"}
LIFESTYLE_CATEGORY_SET = {"senior_consumer", "gen_z", "family_community",
                          "health_medical", "local_kansai", "other"}
LIFESTYLE_SCENE_SET = {"field_visit", "exec_meeting", "staff_morning", "general"}
AI_CATEGORY_SET = {"company", "regulation", "research", "tool",
                   "benchmark", "industry_case"}


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


def _require_strs(item: dict, keys: list[str], path: str) -> None:
    if not isinstance(item, dict):
        raise ValidationError(f"{path}: must be object")
    for k in keys:
        v = item.get(k)
        if not isinstance(v, str) or not v.strip():
            raise ValidationError(f"{path}.{k}: must be non-empty string")


def _require_enum(value, allowed: set, path: str, allow_null: bool = False) -> None:
    if value is None and allow_null:
        return
    if value not in allowed:
        raise ValidationError(f"{path}: invalid value {value!r}, expected one of {sorted(allowed)}")


def validate(bundle: dict) -> None:
    if not isinstance(bundle, dict):
        raise ValidationError("root: must be object")

    _require_keys(bundle, REQUIRED_TOP, "root")

    sv = bundle["schema_version"]
    if sv not in SUPPORTED_SCHEMA_VERSIONS:
        raise ValidationError(
            f"schema_version: unsupported {sv!r}, expected one of {sorted(SUPPORTED_SCHEMA_VERSIONS)}"
        )
    is_v11_or_later = sv in {"1.1", "1.2"}
    is_v12 = sv == "1.2"

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
    _require_keys(market, MARKET_CORE_KEYS, "market")
    for k in MARKET_CORE_KEYS:
        _require_number_or_null(market, k, "market")
    if is_v11_or_later:
        for k in MARKET_OPT_NUM_V11:
            _require_number_or_null(market, k, "market")
        for k in MARKET_OPT_STR_V11:
            _require_str_or_null(market, k, "market")
    if is_v12:
        for k in MARKET_OPT_NUM_V12:
            _require_number_or_null(market, k, "market")

    # weather
    weather = bundle["weather_osaka"]
    if not isinstance(weather, dict):
        raise ValidationError("weather_osaka: must be object")
    _require_keys(weather, WEATHER_KEYS, "weather_osaka")
    _require_str_or_null(weather, "main", "weather_osaka")
    for k in ("temp_high", "temp_low", "rain_prob"):
        _require_number_or_null(weather, k, "weather_osaka")
    if is_v11_or_later:
        for k in WEATHER_OPT_STR:
            _require_str_or_null(weather, k, "weather_osaka")

    # kpi
    kpi = bundle["kpi"]
    if not isinstance(kpi, dict):
        raise ValidationError("kpi: must be object")
    _require_keys(kpi, KPI_KEYS, "kpi")
    for k in KPI_KEYS:
        _require_number_or_null(kpi, k, "kpi")

    # required list fields
    required_lists = list(REQUIRED_LIST_FIELDS_V10)
    if is_v11_or_later:
        required_lists += REQUIRED_LIST_FIELDS_V11_ADD
    if is_v12:
        required_lists += REQUIRED_LIST_FIELDS_V12_ADD
    for k in required_lists:
        if k not in bundle:
            raise ValidationError(f"root.{k}: required (use [] when empty)")
        if not isinstance(bundle[k], list):
            raise ValidationError(f"root.{k}: must be array")

    # element-level validation
    for i, item in enumerate(bundle["highlights"]):
        _require_strs(item, ["title", "source", "summary"], f"highlights[{i}]")
        _require_enum(item.get("impact"), IMPACT_SET, f"highlights[{i}].impact")

    for i, item in enumerate(bundle["alerts"]):
        _require_strs(item, ["title", "source", "summary"], f"alerts[{i}]")
        _require_enum(item.get("severity"), SEVERITY_SET, f"alerts[{i}].severity")

    for i, item in enumerate(bundle["ai_news"]):
        _require_strs(item, ["title", "source", "summary"], f"ai_news[{i}]")
        if is_v12 and "category" in item:
            _require_enum(item.get("category"), AI_CATEGORY_SET,
                          f"ai_news[{i}].category", allow_null=True)

    for i, item in enumerate(bundle["competitor_moves"]):
        _require_strs(item, ["vendor", "title", "source", "summary"],
                      f"competitor_moves[{i}]")

    for i, item in enumerate(bundle["auctions_top3"]):
        _require_strs(item, ["name", "source"], f"auctions_top3[{i}]")
        _require_number_or_null(item, "price", f"auctions_top3[{i}]")

    for i, item in enumerate(bundle["subsidies_deadline_within_30d"]):
        _require_strs(item, ["name", "deadline", "source", "summary"],
                      f"subsidies_deadline_within_30d[{i}]")

    if is_v11_or_later:
        for i, item in enumerate(bundle["secondhand_top5"]):
            _require_strs(item, ["title", "source"], f"secondhand_top5[{i}]")
            _require_number_or_null(item, "price", f"secondhand_top5[{i}]")
            _require_enum(item.get("platform"), PLATFORM_SET,
                          f"secondhand_top5[{i}].platform")

        for i, item in enumerate(bundle["brands_news"]):
            _require_strs(item, ["brand", "title", "source", "summary"],
                          f"brands_news[{i}]")
            _require_enum(item.get("kind"), BRAND_KIND_SET,
                          f"brands_news[{i}].kind")
            _require_enum(item.get("impact"), IMPACT_SET, f"brands_news[{i}].impact")

        for i, item in enumerate(bundle["regulations"]):
            _require_strs(item, ["title", "source", "summary"], f"regulations[{i}]")
            _require_enum(item.get("domain"), REG_DOMAIN_SET,
                          f"regulations[{i}].domain")
            _require_enum(item.get("impact"), IMPACT_SET, f"regulations[{i}].impact")

        welfare_set = WELFARE_CATEGORY_V12 if is_v12 else WELFARE_CATEGORY_V11
        for i, item in enumerate(bundle["welfare_news"]):
            _require_strs(item, ["title", "source", "summary"], f"welfare_news[{i}]")
            _require_enum(item.get("category"), welfare_set,
                          f"welfare_news[{i}].category")
            _require_enum(item.get("impact"), IMPACT_SET, f"welfare_news[{i}].impact")

    if is_v12:
        for i, item in enumerate(bundle["tech_news"]):
            _require_strs(item, ["title", "source", "summary"], f"tech_news[{i}]")
            _require_enum(item.get("category"), TECH_CATEGORY_SET,
                          f"tech_news[{i}].category")
            _require_enum(item.get("impact"), IMPACT_SET, f"tech_news[{i}].impact")

        for i, item in enumerate(bundle["reuse_market"]):
            _require_strs(item, ["title", "source", "summary"], f"reuse_market[{i}]")
            _require_enum(item.get("category"), REUSE_CATEGORY_SET,
                          f"reuse_market[{i}].category")
            _require_enum(item.get("impact"), IMPACT_SET, f"reuse_market[{i}].impact")

        for i, item in enumerate(bundle["lifestyle_trends"]):
            _require_strs(item, ["title", "source", "summary"], f"lifestyle_trends[{i}]")
            _require_enum(item.get("category"), LIFESTYLE_CATEGORY_SET,
                          f"lifestyle_trends[{i}].category")
            _require_enum(item.get("impact"), IMPACT_SET, f"lifestyle_trends[{i}].impact")
            _require_enum(item.get("scene"), LIFESTYLE_SCENE_SET,
                          f"lifestyle_trends[{i}].scene", allow_null=True)

    # subagent_meta
    meta = bundle["subagent_meta"]
    if not isinstance(meta, dict):
        raise ValidationError("subagent_meta: must be object")
    if is_v12:
        expected_keys = SUBAGENT_KEYS_V12
    elif is_v11_or_later:
        expected_keys = SUBAGENT_KEYS_V11
    else:
        expected_keys = SUBAGENT_KEYS_V10
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

    date_str = bundle["date"]
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
