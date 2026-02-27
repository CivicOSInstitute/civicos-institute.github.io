#!/usr/bin/env python3
"""Quick efficiency calculator for routing architecture.

Usage:
  python scripts/efficiency/api_efficiency_calculator.py \
    --requests-per-day 400 \
    --avg-in 2200 --avg-out 500 \
    --price-in 1.75 --price-out 7.00 \
    --tier0 0.60 --tier1 0.25 --compression 0.15

Prices are USD per 1M tokens.
"""

import argparse


def cost(tokens_in, tokens_out, price_in, price_out):
    return (tokens_in / 1_000_000) * price_in + (tokens_out / 1_000_000) * price_out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--requests-per-day", type=float, required=True)
    p.add_argument("--avg-in", type=float, required=True)
    p.add_argument("--avg-out", type=float, required=True)
    p.add_argument("--price-in", type=float, required=True)
    p.add_argument("--price-out", type=float, required=True)
    p.add_argument("--tier0", type=float, default=0.60, help="local route share")
    p.add_argument("--tier1", type=float, default=0.25, help="cache-hit share")
    p.add_argument("--compression", type=float, default=0.15, help="remaining input ratio after compression (0.15=85%% reduction)")
    p.add_argument("--days", type=float, default=14)
    args = p.parse_args()

    req = args.requests_per_day
    base_in = req * args.avg_in
    base_out = req * args.avg_out
    baseline = cost(base_in, base_out, args.price_in, args.price_out) * args.days

    tier2_share = max(0.0, 1.0 - args.tier0 - args.tier1)
    opt_in = req * tier2_share * args.avg_in * args.compression
    opt_out = req * tier2_share * args.avg_out
    optimized = cost(opt_in, opt_out, args.price_in, args.price_out) * args.days

    savings = baseline - optimized
    pct = (savings / baseline * 100.0) if baseline else 0.0
    eff = (baseline / optimized) if optimized else float("inf")

    print("=== API Efficiency Estimate ===")
    print(f"Baseline (days={args.days:g}): ${baseline:,.2f}")
    print(f"Optimized (days={args.days:g}): ${optimized:,.2f}")
    print(f"Savings: ${savings:,.2f} ({pct:.1f}%)")
    print(f"Efficiency multiplier (work per $): {eff:.2f}x")
    print(f"Tier split: T0={args.tier0:.0%} T1={args.tier1:.0%} T2={tier2_share:.0%}")


if __name__ == "__main__":
    main()
