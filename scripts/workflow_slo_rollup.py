#!/usr/bin/env python3
"""
Daily workflow SLO rollup.
Outputs JSON + Markdown summary for Workflow V2 metrics:
- queue wait p50/p95
- queue success rate
- fallback rate (best-effort heuristic from generated artifacts)
- latest ops-cycle health
"""

from __future__ import annotations

import json
import statistics
from datetime import datetime
from pathlib import Path

WORKSPACE = Path('/Users/AI-OPS/.openclaw/workspace')
GEN = WORKSPACE / 'generated'
QUEUE_LOG_DIR = WORKSPACE / 'skills' / 'ollama-agent-queue' / 'data' / 'agent-queue'


def pct(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    vals = sorted(values)
    i = int(round((len(vals) - 1) * p))
    return round(vals[i], 2)


def load_queue_rows(day: str) -> list[dict]:
    p = QUEUE_LOG_DIR / f'queue-log-{day}.json'
    if not p.exists():
        return []
    try:
        rows = json.loads(p.read_text())
        return rows if isinstance(rows, list) else []
    except Exception:
        return []


def fallback_rate(day: str) -> tuple[int, int, float]:
    # Heuristic: count generated markdown/json files for the day containing
    # routing fallback markers.
    files = list((GEN).glob(f'**/*{day.replace("-", "")}*.md')) + list((GEN).glob(f'**/*{day.replace("-", "")}*.json'))
    if not files:
        files = list((GEN).glob('**/*latest*.md')) + list((GEN).glob('**/*latest*.json'))

    fallback_hits = 0
    checked = 0
    markers = [
        'Fallback: API model succeeded',
        'api fallback',
        'route": "api_fallback"',
        'Primary: local queue',
    ]

    for fp in files[:400]:
        try:
            text = fp.read_text(errors='ignore')
        except Exception:
            continue
        checked += 1
        low = text.lower()
        if any(m.lower() in low for m in markers):
            fallback_hits += 1

    rate = round((fallback_hits / checked) * 100, 2) if checked else 0.0
    return fallback_hits, checked, rate


def load_ops_health() -> dict:
    p = GEN / 'automation_health.json'
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


def main() -> int:
    now = datetime.now().astimezone()
    day = now.strftime('%Y-%m-%d')

    rows = load_queue_rows(day)
    waits = [float(r.get('wait_time_seconds', 0) or 0) for r in rows if isinstance(r.get('wait_time_seconds', None), (int, float))]
    total = len(rows)
    complete = len([r for r in rows if r.get('status') == 'complete'])
    success_rate = round((complete / total) * 100, 2) if total else 0.0

    p50_wait = pct(waits, 0.50)
    p95_wait = pct(waits, 0.95)

    fb_hits, fb_checked, fb_rate = fallback_rate(day)
    health = load_ops_health()
    bad_steps = [s for s in health.get('steps', []) if s.get('status') != 'ok'] if isinstance(health, dict) else []

    slo = {
        'generated_at': now.isoformat(timespec='seconds'),
        'date': day,
        'workflow': 'workflow_slo_rollup',
        'lane': 'prod-critical',
        'queue': {
            'jobs_total': total,
            'jobs_complete': complete,
            'success_rate_percent': success_rate,
            'wait_p50_seconds': p50_wait,
            'wait_p95_seconds': p95_wait,
        },
        'fallback': {
            'hits': fb_hits,
            'artifacts_checked': fb_checked,
            'estimated_rate_percent': fb_rate,
        },
        'ops_cycle': {
            'last_total_seconds': health.get('total_seconds') if isinstance(health, dict) else None,
            'failing_steps': len(bad_steps),
        },
        'targets': {
            'queue_success_rate_percent': '>=98',
            'queue_wait_p95_seconds': '<30',
        },
    }

    GEN.mkdir(parents=True, exist_ok=True)
    ts = now.strftime('%Y%m%d_%H%M%S')
    out_json = GEN / f'workflow_slo_rollup_{ts}.json'
    latest_json = GEN / 'workflow_slo_rollup_latest.json'
    out_json.write_text(json.dumps(slo, indent=2))
    tmp = GEN / 'workflow_slo_rollup_latest.tmp.json'
    tmp.write_text(json.dumps(slo, indent=2))
    tmp.replace(latest_json)

    md = []
    md.append(f"# Workflow SLO Rollup — {day}")
    md.append("")
    md.append("## Queue")
    md.append(f"- Jobs total: {total}")
    md.append(f"- Success rate: {success_rate}%")
    md.append(f"- Wait p50: {p50_wait}s")
    md.append(f"- Wait p95: {p95_wait}s")
    md.append("")
    md.append("## Fallback (Estimated)")
    md.append(f"- Hits: {fb_hits}")
    md.append(f"- Artifacts checked: {fb_checked}")
    md.append(f"- Estimated fallback rate: {fb_rate}%")
    md.append("")
    md.append("## Ops Cycle")
    md.append(f"- Last total seconds: {slo['ops_cycle']['last_total_seconds']}")
    md.append(f"- Failing steps: {slo['ops_cycle']['failing_steps']}")
    md.append("")
    md.append("## Target Check")
    md.append(f"- Queue success target (>=98%): {'PASS' if success_rate >= 98 else 'FAIL'}")
    md.append(f"- Queue p95 wait target (<30s): {'PASS' if (p95_wait and p95_wait < 30) else 'FAIL'}")

    out_md = GEN / f'workflow_slo_rollup_{ts}.md'
    latest_md = GEN / 'workflow_slo_rollup_latest.md'
    out_md.write_text('\n'.join(md))
    tmp_md = GEN / 'workflow_slo_rollup_latest.tmp.md'
    tmp_md.write_text('\n'.join(md))
    tmp_md.replace(latest_md)

    print(str(out_json))
    print(str(out_md))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
