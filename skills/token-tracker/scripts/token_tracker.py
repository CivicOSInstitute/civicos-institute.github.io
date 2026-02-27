#!/usr/bin/env python3
"""
token-tracker (reconfigured): Router efficiency + API-load prevention tracker.

This replaces legacy per-provider token logging with router-centric telemetry:
- Tier routing (T0/T1/T2)
- Cache hit rate
- Compression ratio
- Quality pass rate
- Effective API cost

Usage:
  token-tracker log --task-id <id> --tier T0|T1|T2 --classifier-score <0..1> \
    --cache-hit <true|false> --compression-ratio <float> --input-tokens <int> \
    --output-tokens <int> --cost-usd <float> --latency-ms <int> --quality-flag <pass|fail>

  token-tracker status [--hours 24]
  token-tracker report [--days 14] [--json]
  token-tracker budget --set-daily-cap <tokens> --set-monthly-cap <tokens> --set-alert-at <percent>
  token-tracker budget --show
  token-tracker forecast [--days 14]
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_TELEMETRY_PATH = Path("/Users/AI-OPS/.openclaw/workspace/data/telemetry/router_telemetry.jsonl")
CONFIG_DIR = Path(os.path.expanduser("~/.openclaw/token-tracker"))
CONFIG_FILE = CONFIG_DIR / "router_config.json"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _load_events(path: Path, cutoff: datetime | None = None) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.exists():
        return rows

    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
            ts = datetime.fromisoformat(r["ts"])
            if cutoff is None or ts >= cutoff:
                rows.append(r)
        except Exception:
            continue
    return rows


def _pct(n: float, d: float) -> float:
    return round((n / d * 100.0), 2) if d else 0.0


def _summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(rows)
    tiers = Counter(r.get("route_tier", "?") for r in rows)
    cache_hits = sum(1 for r in rows if r.get("cache_hit"))
    input_tokens = sum(int(r.get("input_tokens", 0)) for r in rows)
    output_tokens = sum(int(r.get("output_tokens", 0)) for r in rows)
    total_tokens = input_tokens + output_tokens
    cost_usd = round(sum(float(r.get("cost_usd", 0.0)) for r in rows), 6)
    avg_latency = round(
        sum(int(r.get("latency_ms", 0)) for r in rows) / total, 2
    ) if total else 0.0
    avg_comp = round(
        sum(float(r.get("compression_ratio", 1.0)) for r in rows) / total, 4
    ) if total else 1.0
    q_pass = sum(1 for r in rows if str(r.get("quality_flag", "")).lower() == "pass")

    return {
        "events": total,
        "tier_distribution": dict(tiers),
        "cache_hit_rate_pct": _pct(cache_hits, total),
        "quality_pass_rate_pct": _pct(q_pass, total),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cost_usd": cost_usd,
        "avg_latency_ms": avg_latency,
        "avg_compression_ratio": avg_comp,
    }


def _load_config() -> Dict[str, Any]:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    cfg = {
        "budget": {
            "daily_token_cap": None,
            "monthly_token_cap": None,
            "alert_at_percent": 80,
        }
    }
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    return cfg


def _save_config(cfg: Dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def cmd_log(args: argparse.Namespace) -> None:
    event = {
        "ts": _now().isoformat(),
        "task_id": args.task_id,
        "route_tier": args.tier,
        "classifier_score": args.classifier_score,
        "cache_hit": str(args.cache_hit).lower() in {"1", "true", "yes", "y", "on"},
        "compression_ratio": args.compression_ratio,
        "input_tokens": args.input_tokens,
        "output_tokens": args.output_tokens,
        "cost_usd": args.cost_usd,
        "latency_ms": args.latency_ms,
        "quality_flag": args.quality_flag,
    }
    args.path.parent.mkdir(parents=True, exist_ok=True)
    with args.path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    print(f"✓ Logged routing event {args.task_id} -> {args.path}")


def cmd_status(args: argparse.Namespace) -> None:
    cutoff = _now() - timedelta(hours=args.hours)
    rows = _load_events(args.path, cutoff)
    s = _summarize(rows)

    print(f"\n📈 Router Efficiency Status (last {args.hours}h)")
    print(f"   Events: {s['events']}")
    td = s["tier_distribution"]
    print(f"   Tier split: T0={td.get('T0', 0)} T1={td.get('T1', 0)} T2={td.get('T2', 0)}")
    print(f"   Cache hit rate: {s['cache_hit_rate_pct']}%")
    print(f"   Quality pass rate: {s['quality_pass_rate_pct']}%")
    print(f"   Tokens in/out: {s['input_tokens']:,} / {s['output_tokens']:,}")
    print(f"   API cost: ${s['cost_usd']:.6f}")
    print(f"   Avg latency: {s['avg_latency_ms']} ms")
    print(f"   Avg compression ratio: {s['avg_compression_ratio']}")

    cfg = _load_config()
    b = cfg.get("budget", {})
    if b.get("daily_token_cap"):
        used_pct = _pct(s["total_tokens"], b["daily_token_cap"])
        print(f"   Daily cap usage: {s['total_tokens']:,}/{b['daily_token_cap']:,} ({used_pct}%)")
        if used_pct >= b.get("alert_at_percent", 80):
            print("   ⚠️  Alert threshold exceeded")


def cmd_report(args: argparse.Namespace) -> None:
    cutoff = _now() - timedelta(days=args.days)
    rows = _load_events(args.path, cutoff)
    s = _summarize(rows)
    payload = {
        "window_days": args.days,
        "generated_at": _now().isoformat(),
        **s,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
        return

    print(f"\n📊 Router Efficiency Report ({args.days}d)")
    print(f"   Events: {payload['events']}")
    print(f"   Tier distribution: {payload['tier_distribution']}")
    print(f"   Cache hit rate: {payload['cache_hit_rate_pct']}%")
    print(f"   Quality pass rate: {payload['quality_pass_rate_pct']}%")
    print(f"   Total tokens: {payload['total_tokens']:,}")
    print(f"   Total cost: ${payload['cost_usd']:.6f}")
    print(f"   Avg latency: {payload['avg_latency_ms']} ms")


def cmd_budget(args: argparse.Namespace) -> None:
    cfg = _load_config()
    b = cfg.setdefault("budget", {})

    changed = False
    if args.set_daily_cap is not None:
        b["daily_token_cap"] = args.set_daily_cap
        changed = True
    if args.set_monthly_cap is not None:
        b["monthly_token_cap"] = args.set_monthly_cap
        changed = True
    if args.set_alert_at is not None:
        b["alert_at_percent"] = args.set_alert_at
        changed = True

    if changed:
        _save_config(cfg)
        print("✓ Router budget config updated")

    print(json.dumps(cfg, indent=2))


def cmd_forecast(args: argparse.Namespace) -> None:
    rows = _load_events(args.path)
    if not rows:
        print("No telemetry events yet.")
        return

    by_day: Dict[str, Dict[str, float]] = {}
    cutoff = _now() - timedelta(days=args.days)
    for r in rows:
        try:
            ts = datetime.fromisoformat(r["ts"])
        except Exception:
            continue
        if ts < cutoff:
            continue
        d = ts.strftime("%Y-%m-%d")
        by_day.setdefault(d, {"tokens": 0.0, "cost": 0.0})
        by_day[d]["tokens"] += float(r.get("input_tokens", 0)) + float(r.get("output_tokens", 0))
        by_day[d]["cost"] += float(r.get("cost_usd", 0))

    if not by_day:
        print("Insufficient data in selected window.")
        return

    avg_daily_tokens = sum(v["tokens"] for v in by_day.values()) / len(by_day)
    avg_daily_cost = sum(v["cost"] for v in by_day.values()) / len(by_day)

    now = _now()
    if now.month == 12:
        next_month = now.replace(year=now.year + 1, month=1, day=1)
    else:
        next_month = now.replace(month=now.month + 1, day=1)
    days_in_month = (next_month - now.replace(day=1)).days
    days_remaining = days_in_month - now.day + 1

    projected_tokens = avg_daily_tokens * days_in_month
    projected_cost = avg_daily_cost * days_in_month

    cfg = _load_config().get("budget", {})
    cap = cfg.get("monthly_token_cap")
    alert = cfg.get("alert_at_percent", 80)

    print(f"\n🔮 Router Forecast ({args.days}d history)")
    print(f"   Avg daily tokens: {avg_daily_tokens:,.0f}")
    print(f"   Avg daily cost: ${avg_daily_cost:.4f}")
    print(f"   Days remaining this month: {days_remaining}")
    print(f"   Projected monthly tokens: {projected_tokens:,.0f}")
    print(f"   Projected monthly cost: ${projected_cost:.2f}")

    if cap:
        pct = _pct(projected_tokens, cap)
        print(f"   Monthly token cap: {cap:,} (projected {pct}%)")
        if pct >= alert:
            print("   ⚠️  Overshoot risk vs budget threshold")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Router Efficiency Token Tracker")
    sub = parser.add_subparsers(dest="command", required=True)

    # log
    p_log = sub.add_parser("log", help="Log one router telemetry event")
    p_log.add_argument("--task-id", required=True)
    p_log.add_argument("--tier", choices=["T0", "T1", "T2"], required=True)
    p_log.add_argument("--classifier-score", type=float, required=True)
    p_log.add_argument("--cache-hit", default="false")
    p_log.add_argument("--compression-ratio", type=float, default=1.0)
    p_log.add_argument("--input-tokens", type=int, required=True)
    p_log.add_argument("--output-tokens", type=int, required=True)
    p_log.add_argument("--cost-usd", type=float, required=True)
    p_log.add_argument("--latency-ms", type=int, required=True)
    p_log.add_argument("--quality-flag", default="unknown")
    p_log.add_argument("--path", type=Path, default=DEFAULT_TELEMETRY_PATH)

    # status
    p_status = sub.add_parser("status", help="Show current efficiency status")
    p_status.add_argument("--hours", type=int, default=24)
    p_status.add_argument("--path", type=Path, default=DEFAULT_TELEMETRY_PATH)

    # report
    p_report = sub.add_parser("report", help="Generate efficiency report")
    p_report.add_argument("--days", type=int, default=14)
    p_report.add_argument("--json", action="store_true")
    p_report.add_argument("--path", type=Path, default=DEFAULT_TELEMETRY_PATH)

    # budget
    p_budget = sub.add_parser("budget", help="Set/show router budget caps")
    p_budget.add_argument("--set-daily-cap", type=int)
    p_budget.add_argument("--set-monthly-cap", type=int)
    p_budget.add_argument("--set-alert-at", type=int)
    p_budget.add_argument("--show", action="store_true")

    # forecast
    p_forecast = sub.add_parser("forecast", help="Forecast monthly usage from telemetry")
    p_forecast.add_argument("--days", type=int, default=14)
    p_forecast.add_argument("--path", type=Path, default=DEFAULT_TELEMETRY_PATH)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "log":
        cmd_log(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "report":
        cmd_report(args)
    elif args.command == "budget":
        cmd_budget(args)
    elif args.command == "forecast":
        cmd_forecast(args)


if __name__ == "__main__":
    main()
