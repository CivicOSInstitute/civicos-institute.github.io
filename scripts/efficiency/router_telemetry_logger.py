#!/usr/bin/env python3
"""Append router telemetry events to JSONL.

Usage:
  python scripts/efficiency/router_telemetry_logger.py \
    --task-id t123 --tier T1 --classifier-score 0.52 --cache-hit true \
    --compression-ratio 0.22 --input-tokens 1200 --output-tokens 280 \
    --cost-usd 0.0031 --latency-ms 820 --quality-flag pass
"""

from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def parse_bool(v: str) -> bool:
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--task-id", required=True)
    p.add_argument("--tier", choices=["T0", "T1", "T2"], required=True)
    p.add_argument("--classifier-score", type=float, required=True)
    p.add_argument("--cache-hit", default="false")
    p.add_argument("--compression-ratio", type=float, default=1.0)
    p.add_argument("--input-tokens", type=int, required=True)
    p.add_argument("--output-tokens", type=int, required=True)
    p.add_argument("--cost-usd", type=float, required=True)
    p.add_argument("--latency-ms", type=int, required=True)
    p.add_argument("--quality-flag", default="unknown")
    p.add_argument("--path", default="data/telemetry/router_telemetry.jsonl")
    args = p.parse_args()

    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "task_id": args.task_id,
        "route_tier": args.tier,
        "classifier_score": args.classifier_score,
        "cache_hit": parse_bool(args.cache_hit),
        "compression_ratio": args.compression_ratio,
        "input_tokens": args.input_tokens,
        "output_tokens": args.output_tokens,
        "cost_usd": args.cost_usd,
        "latency_ms": args.latency_ms,
        "quality_flag": args.quality_flag,
    }

    out = Path(args.path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    print(f"logged {args.task_id} -> {out}")


if __name__ == "__main__":
    main()
