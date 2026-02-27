#!/usr/bin/env python3
"""Daily workflow cost visibility rollup (model + workflow lens)."""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path

WS = Path('/Users/AI-OPS/.openclaw/workspace')
GEN = WS / 'generated'
QLOG = WS / 'skills' / 'ollama-agent-queue' / 'data' / 'agent-queue' / f"queue-log-{datetime.now().strftime('%Y-%m-%d')}.json"

# Best-effort workflow mapping by calling skill
WF_MAP = {
    'grant-daily-scan': 'grant_daily_local_scan',
    'model-toolcall-probe': 'local_model_toolcall_probe',
    'architecture': 'architecture_planning',
    'council-of-advisors': 'council_session',
    'smoke': 'platform_smoke_test',
}


def main() -> int:
    rows = []
    if QLOG.exists():
        try:
            arr = json.loads(QLOG.read_text())
            if isinstance(arr, list):
                rows = arr
        except Exception:
            pass

    by_workflow = {}
    by_model = {}
    for r in rows:
        w = WF_MAP.get(r.get('calling_skill'), r.get('calling_skill', 'unknown'))
        m = r.get('model', 'unknown')
        toks = r.get('tokens_used') or 0
        dur = r.get('duration_seconds') or 0
        st = r.get('status')

        bw = by_workflow.setdefault(w, {'jobs': 0, 'tokens': 0, 'duration_s': 0.0, 'non_complete': 0})
        bw['jobs'] += 1
        bw['tokens'] += int(toks) if isinstance(toks, (int, float)) else 0
        bw['duration_s'] += float(dur) if isinstance(dur, (int, float)) else 0.0
        if st != 'complete':
            bw['non_complete'] += 1

        bm = by_model.setdefault(m, {'jobs': 0, 'tokens': 0, 'duration_s': 0.0})
        bm['jobs'] += 1
        bm['tokens'] += int(toks) if isinstance(toks, (int, float)) else 0
        bm['duration_s'] += float(dur) if isinstance(dur, (int, float)) else 0.0

    payload = {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'workflow': 'workflow_cost_visibility',
        'lane': 'prod-critical',
        'date': datetime.now().strftime('%Y-%m-%d'),
        'note': 'Local model spend is estimated via token/duration intensity (USD direct cost usually 0 for local).',
        'by_workflow': by_workflow,
        'by_model': by_model,
    }

    GEN.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    outj = GEN / f'workflow_cost_visibility_{ts}.json'
    latestj = GEN / 'workflow_cost_visibility_latest.json'
    outj.write_text(json.dumps(payload, indent=2))
    tmp = GEN / 'workflow_cost_visibility_latest.tmp.json'
    tmp.write_text(json.dumps(payload, indent=2))
    tmp.replace(latestj)

    lines = [f"# Workflow Cost Visibility — {payload['date']}", '', '## By Workflow']
    if by_workflow:
        for w,v in sorted(by_workflow.items(), key=lambda kv: kv[1]['tokens'], reverse=True):
            lines.append(f"- {w}: jobs={v['jobs']}, tokens={v['tokens']}, duration={round(v['duration_s'],2)}s, non-complete={v['non_complete']}")
    else:
        lines.append('- No queue rows today.')
    lines += ['', '## By Model']
    if by_model:
        for m,v in sorted(by_model.items(), key=lambda kv: kv[1]['tokens'], reverse=True):
            lines.append(f"- {m}: jobs={v['jobs']}, tokens={v['tokens']}, duration={round(v['duration_s'],2)}s")
    else:
        lines.append('- No model activity rows today.')

    outm = GEN / f'workflow_cost_visibility_{ts}.md'
    latestm = GEN / 'workflow_cost_visibility_latest.md'
    outm.write_text('\n'.join(lines))
    tmpm = GEN / 'workflow_cost_visibility_latest.tmp.md'
    tmpm.write_text('\n'.join(lines))
    tmpm.replace(latestm)

    print(str(outj))
    print(str(outm))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
