#!/usr/bin/env python3
"""Autonomous phase rollout manager for API-load prevention architecture.

Promotes rollout phases based on telemetry gates and raises a council flag when
signals are ambiguous or quality risk is detected.
"""

from __future__ import annotations
import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import Counter

TELEMETRY = Path("/Users/AI-OPS/.openclaw/workspace/data/telemetry/router_telemetry.jsonl")
STATE = Path("/Users/AI-OPS/.openclaw/workspace/data/state/api_rollout_state.json")
OUT_DIR = Path("/Users/AI-OPS/.openclaw/workspace/generated/efficiency")

DEFAULT_STATE = {
    "phase": 0,
    "phase_name": "Instrumentation",
    "updated_at": None,
    "history": [],
}

PHASES = {
    0: "Instrumentation",
    1: "Shadow Mode",
    2: "Controlled Enforcement",
    3: "Full Enforcement",
}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(DEFAULT_STATE, indent=2))
    return dict(DEFAULT_STATE)


def save_state(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2))


def load_events(hours: int):
    if not TELEMETRY.exists():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    rows = []
    for line in TELEMETRY.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
            ts = datetime.fromisoformat(r["ts"])
            if ts >= cutoff:
                rows.append(r)
        except Exception:
            continue
    return rows


def summarize(rows):
    total = len(rows)
    tiers = Counter(r.get("route_tier", "?") for r in rows)
    cache_hits = sum(1 for r in rows if r.get("cache_hit"))
    q_pass = sum(1 for r in rows if str(r.get("quality_flag", "")).lower() == "pass")
    avg_lat = (sum(int(r.get("latency_ms", 0)) for r in rows) / total) if total else 0
    return {
        "events": total,
        "tier_distribution": dict(tiers),
        "cache_hit_rate_pct": round((cache_hits / total * 100), 2) if total else 0.0,
        "quality_pass_rate_pct": round((q_pass / total * 100), 2) if total else 0.0,
        "avg_latency_ms": round(avg_lat, 2),
    }


def evaluate(state, s):
    phase = int(state.get("phase", 0))
    reasons = []
    escalate_council = False
    promote = False

    if s["events"] < 40:
        reasons.append("insufficient_data")
        return promote, escalate_council, reasons

    # universal safety
    if s["quality_pass_rate_pct"] < 95:
        reasons.append("quality_below_threshold")
        escalate_council = True
        return promote, escalate_council, reasons

    if phase == 0:
        if s["events"] >= 80:
            promote = True
            reasons.append("phase0_exit_met")
        else:
            reasons.append("collect_more_baseline")
    elif phase == 1:
        if s["events"] >= 120 and s["quality_pass_rate_pct"] >= 96:
            promote = True
            reasons.append("phase1_exit_met")
        else:
            reasons.append("shadow_validation_incomplete")
    elif phase == 2:
        t2 = s["tier_distribution"].get("T2", 0)
        t2_share = (t2 / s["events"] * 100) if s["events"] else 100
        if s["events"] >= 160 and t2_share <= 35 and s["quality_pass_rate_pct"] >= 97:
            promote = True
            reasons.append("phase2_exit_met")
        else:
            reasons.append("controlled_window_not_ready")
            if t2_share > 45:
                reasons.append("api_dependency_too_high")
                escalate_council = True
    else:
        reasons.append("already_full_enforcement")

    return promote, escalate_council, reasons


def write_outputs(state, summary, recommend, council, reasons):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = {
        "generated_at": now_iso(),
        "state": state,
        "summary_24h": summary,
        "recommend_promote": recommend,
        "council_review_needed": council,
        "reasons": reasons,
    }
    (OUT_DIR / "phase_rollout_status.json").write_text(json.dumps(out, indent=2))

    md = [
        f"# Phase Rollout Status",
        f"- Generated: {out['generated_at']}",
        f"- Current phase: **{state['phase']} — {state['phase_name']}**",
        f"- Events (24h): **{summary['events']}**",
        f"- Quality pass: **{summary['quality_pass_rate_pct']}%**",
        f"- Cache hit: **{summary['cache_hit_rate_pct']}%**",
        f"- Avg latency: **{summary['avg_latency_ms']} ms**",
        f"- Recommend promote: **{recommend}**",
        f"- Council needed: **{council}**",
        f"- Reasons: {', '.join(reasons) if reasons else 'none'}",
    ]
    (OUT_DIR / "phase_rollout_status.md").write_text("\n".join(md))

    if council:
        brief = "\n".join([
            "# Council Brief Request — API Rollout",
            f"Time: {out['generated_at']}",
            f"Current phase: {state['phase_name']}",
            f"Signals: {', '.join(reasons)}",
            "Ask: validate go/no-go and risk mitigations before automatic promotion.",
        ])
        (OUT_DIR / "council_brief_needed.md").write_text(brief)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=24)
    ap.add_argument("--auto-advance", action="store_true")
    args = ap.parse_args()

    state = load_state()
    summary = summarize(load_events(args.hours))
    promote, council, reasons = evaluate(state, summary)

    if args.auto_advance and promote and state["phase"] < 3:
        state["phase"] += 1
        state["phase_name"] = PHASES[state["phase"]]
        state["updated_at"] = now_iso()
        state["history"].append({
            "at": state["updated_at"],
            "event": "auto_promote",
            "new_phase": state["phase"],
            "reason": reasons,
        })
        save_state(state)

    write_outputs(state, summary, promote, council, reasons)
    print(json.dumps({
        "phase": state["phase"],
        "phase_name": state["phase_name"],
        "recommend_promote": promote,
        "council_review_needed": council,
        "reasons": reasons,
    }, indent=2))


if __name__ == "__main__":
    main()
