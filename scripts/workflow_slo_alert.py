#!/usr/bin/env python3
"""
Workflow SLO alerting.
Reads latest SLO rollup and emits alert when targets fail.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path

WORKSPACE = Path('/Users/AI-OPS/.openclaw/workspace')
GEN = WORKSPACE / 'generated'
SLO_PATH = GEN / 'workflow_slo_rollup_latest.json'
QUEUE_PATH = WORKSPACE / 'skills' / 'ollama-agent-queue' / 'data' / 'agent-queue' / f"queue-log-{datetime.now().strftime('%Y-%m-%d')}.json"


def top_causes() -> list[str]:
    causes = []
    if not QUEUE_PATH.exists():
        return ["No queue-log file found for today."]
    try:
        rows = json.loads(QUEUE_PATH.read_text())
    except Exception:
        return ["Queue log unreadable."]

    if not isinstance(rows, list) or not rows:
        return ["No queue rows for today yet."]

    # Cause 1: long waits
    waits = [r.get('wait_time_seconds', 0) for r in rows if isinstance(r.get('wait_time_seconds'), (int, float))]
    long_wait = len([w for w in waits if w and w > 60])
    if long_wait:
        causes.append(f"{long_wait} jobs waited >60s (queue congestion).")

    # Cause 2: model mix slow lanes
    by_model = {}
    for r in rows:
        m = r.get('model', 'unknown')
        by_model[m] = by_model.get(m, 0) + 1
    if by_model:
        top_model = sorted(by_model.items(), key=lambda x: x[1], reverse=True)[0]
        causes.append(f"Top workload model today: {top_model[0]} ({top_model[1]} jobs).")

    # Cause 3: non-complete statuses
    failures = [r for r in rows if r.get('status') != 'complete']
    if failures:
        ftypes = {}
        for f in failures:
            st = f.get('status', 'unknown')
            ftypes[st] = ftypes.get(st, 0) + 1
        summary = ', '.join(f"{k}:{v}" for k, v in sorted(ftypes.items(), key=lambda x: x[0]))
        causes.append(f"Non-complete jobs detected ({summary}).")

    return causes[:3] if causes else ["No obvious queue-level cause detected."]


def send_telegram(text: str) -> None:
    """Optional notifier hook.
    If ~/.openclaw/scripts/send-telegram.sh is compatible, it will be attempted.
    Failures are non-fatal (alert file is still written).
    """
    send_script = Path('/Users/AI-OPS/.openclaw/scripts/send-telegram.sh')
    if not send_script.exists():
        return
    try:
        subprocess.run(['bash', str(send_script), '8334496229', text], check=False, capture_output=True, text=True)
    except Exception:
        pass


def main() -> int:
    if not SLO_PATH.exists():
        print('no_slo_file')
        return 0

    try:
        slo = json.loads(SLO_PATH.read_text())
    except Exception:
        print('bad_slo_file')
        return 0

    q = slo.get('queue', {})
    success = float(q.get('success_rate_percent', 0) or 0)
    p95 = float(q.get('wait_p95_seconds', 0) or 0)

    fail_success = success < 98
    fail_wait = p95 >= 30 if p95 else True

    if not (fail_success or fail_wait):
        print('slo_ok')
        return 0

    causes = top_causes()

    msg = [
        f"🚨 Workflow SLO Alert ({slo.get('date','today')})",
        f"- Queue success: {success}% (target >=98%)",
        f"- Queue p95 wait: {p95}s (target <30s)",
        "- Top likely causes:",
    ]
    for c in causes:
        msg.append(f"  • {c}")

    text = '\n'.join(msg)
    alert_path = GEN / f"workflow_slo_alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    alert_path.write_text(text)

    send_telegram(text)
    print(str(alert_path))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
