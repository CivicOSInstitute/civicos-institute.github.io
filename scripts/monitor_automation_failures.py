#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime
from telegram_router import send_route_message, RoutingError

BASE = Path('/Users/AI-OPS/.openclaw/workspace')
GEN = BASE / 'generated'


def load_recent(n=3):
    files = sorted(GEN.glob('automation_health_*.json'))
    if not files:
        latest = GEN / 'automation_health.json'
        return [json.loads(latest.read_text())] if latest.exists() else []
    out = []
    for f in files[-n:]:
        try:
            out.append(json.loads(f.read_text()))
        except Exception:
            pass
    return out


def failed_steps(h):
    return {s.get('name') for s in h.get('steps', []) if s.get('status') != 'ok'}


def main():
    hs = load_recent(3)
    if len(hs) < 2:
        print('insufficient history')
        return

    f1 = failed_steps(hs[-1])
    f2 = failed_steps(hs[-2])
    persistent = sorted(f1.intersection(f2))
    if not persistent:
        print('no persistent failures')
        return

    msg = (
        f"🚨 Automation alert: persistent failures across 2 consecutive runs\n"
        f"Steps: {', '.join(persistent)}\n"
        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"Action: check generated/automation_health.json and ops_cycle log"
    )
    try:
        send_route_message('financial_ops', msg)
    except RoutingError as e:
        raise SystemExit(f'ROUTING_FAIL_CLOSED: {e}')
    print(msg)


if __name__ == '__main__':
    main()
