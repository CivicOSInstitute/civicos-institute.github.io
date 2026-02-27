#!/usr/bin/env python3
"""Workflow sandbox replay executor (safe checks, no destructive actions)."""
from __future__ import annotations
import argparse, json
from datetime import datetime
from pathlib import Path

WS = Path('/Users/AI-OPS/.openclaw/workspace')
GEN = WS / 'generated'
QSTATE = WS / 'skills' / 'ollama-agent-queue' / 'data' / 'agent-queue' / 'queue.json'

SCENARIOS = ['queue_congestion','provider_outage','cloud_auth_failure','cron_drift']


def run(name: str) -> dict:
    ts = datetime.now().isoformat(timespec='seconds')
    out = {'scenario': name, 'timestamp': ts, 'checks': [], 'pass': True}

    if name == 'queue_congestion':
        p = GEN / 'workflow_slo_rollup_latest.json'
        if p.exists():
            j = json.loads(p.read_text())
            p95 = j.get('queue',{}).get('wait_p95_seconds',0)
            out['checks'].append({'name':'p95_wait_observed','value':p95})
            out['pass'] = bool(p95 and p95 >= 120)
        else:
            out['checks'].append({'name':'missing_slo_rollup','value':True})
            out['pass'] = False

    elif name == 'provider_outage':
        out['checks'].append({'name':'queue_state_exists','value':QSTATE.exists()})
        out['pass'] = QSTATE.exists()

    elif name == 'cloud_auth_failure':
        # detection artifact from recent unauthorized tests/logs
        cand = list(GEN.glob('**/*slo_alert*.txt'))
        out['checks'].append({'name':'alert_artifacts_present','value':len(cand)})
        out['pass'] = len(cand) > 0

    elif name == 'cron_drift':
        expected = [
            GEN / 'workflow_slo_rollup_latest.json',
            GEN / 'workflow_slo_alert_20260226_165156.txt',
        ]
        miss = [str(p) for p in expected if not p.exists()]
        out['checks'].append({'name':'expected_artifacts_missing','value':miss})
        out['pass'] = len(miss) == 0

    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--scenario', choices=SCENARIOS + ['all'], default='all')
    args = ap.parse_args()

    scenarios = SCENARIOS if args.scenario == 'all' else [args.scenario]
    rows = [run(s) for s in scenarios]
    summary = {'generated_at': datetime.now().isoformat(timespec='seconds'), 'workflow':'workflow_sandbox_replay', 'lane':'experimental', 'results': rows}

    GEN.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out = GEN / f'workflow_sandbox_replay_{ts}.json'
    out.write_text(json.dumps(summary, indent=2))
    latest = GEN / 'workflow_sandbox_replay_latest.json'
    tmp = GEN / 'workflow_sandbox_replay_latest.tmp.json'
    tmp.write_text(json.dumps(summary, indent=2)); tmp.replace(latest)
    print(str(out))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
