#!/usr/bin/env python3
"""Build daily markdown/json summary from router telemetry JSONL."""

from __future__ import annotations
import argparse
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path


def pct(n, d):
    return (n / d * 100.0) if d else 0.0


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="data/telemetry/router_telemetry.jsonl")
    p.add_argument("--hours", type=int, default=24)
    p.add_argument("--out-json", default="generated/efficiency/router_efficiency_latest.json")
    p.add_argument("--out-md", default="generated/efficiency/router_efficiency_latest.md")
    args = p.parse_args()

    inp = Path(args.input)
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=args.hours)

    rows = []
    if inp.exists():
        for line in inp.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                ts = datetime.fromisoformat(r["ts"])
                if ts >= cutoff:
                    rows.append(r)
            except Exception:
                continue

    total = len(rows)
    tier_counts = Counter(r.get("route_tier", "?") for r in rows)
    cache_hits = sum(1 for r in rows if r.get("cache_hit"))
    tokens_in = sum(int(r.get("input_tokens", 0)) for r in rows)
    tokens_out = sum(int(r.get("output_tokens", 0)) for r in rows)
    cost = sum(float(r.get("cost_usd", 0.0)) for r in rows)
    avg_latency = sum(int(r.get("latency_ms", 0)) for r in rows) / total if total else 0
    avg_comp = sum(float(r.get("compression_ratio", 1.0)) for r in rows) / total if total else 1.0
    q_pass = sum(1 for r in rows if str(r.get("quality_flag", "")).lower() == "pass")

    report = {
        "window_hours": args.hours,
        "events": total,
        "tier_distribution": dict(tier_counts),
        "cache_hit_rate_pct": round(pct(cache_hits, total), 2),
        "quality_pass_rate_pct": round(pct(q_pass, total), 2),
        "input_tokens": tokens_in,
        "output_tokens": tokens_out,
        "cost_usd": round(cost, 6),
        "avg_latency_ms": round(avg_latency, 2),
        "avg_compression_ratio": round(avg_comp, 4),
        "generated_at": now.isoformat(),
    }

    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    md = f"""# Router Efficiency Report (last {args.hours}h)

- Events: **{total}**
- Tier split: **T0 {tier_counts.get('T0',0)} / T1 {tier_counts.get('T1',0)} / T2 {tier_counts.get('T2',0)}**
- Cache hit rate: **{report['cache_hit_rate_pct']}%**
- Quality pass rate: **{report['quality_pass_rate_pct']}%**
- Input tokens: **{tokens_in:,}**
- Output tokens: **{tokens_out:,}**
- API cost: **${report['cost_usd']:.4f}**
- Avg latency: **{report['avg_latency_ms']} ms**
- Avg compression ratio: **{report['avg_compression_ratio']}**

_Generated: {report['generated_at']}_
"""
    out_md.write_text(md, encoding="utf-8")
    print(f"wrote {out_json} and {out_md}")


if __name__ == "__main__":
    main()
