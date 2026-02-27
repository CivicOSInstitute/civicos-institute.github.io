#!/usr/bin/env python3
"""Create a structured workflow KB write artifact."""
from __future__ import annotations
import argparse
from datetime import datetime
from pathlib import Path

WS = Path('/Users/AI-OPS/.openclaw/workspace')
OUT_DIR = WS / 'generated' / 'kb_writes'
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--workflow', required=True)
    ap.add_argument('--change', required=True)
    ap.add_argument('--why', required=True)
    ap.add_argument('--evidence', default='pending')
    ap.add_argument('--rollback', default='git revert <commit>')
    ap.add_argument('--owner', default='Burt Prime')
    args = ap.parse_args()

    now = datetime.now().astimezone()
    ts = now.strftime('%Y%m%d_%H%M%S')
    day = now.strftime('%Y-%m-%d')
    out = OUT_DIR / f'{day}_{args.workflow}_{ts}.md'

    content = f"""# Workflow Knowledge Write

- Date: {now.isoformat(timespec='seconds')}
- Workflow: {args.workflow}
- Change summary: {args.change}
- Why changed: {args.why}
- Evidence (metrics/logs): {args.evidence}
- Risk introduced: low
- Rollback command/path: {args.rollback}
- Owner: {args.owner}
- Approval needed?: no
"""
    out.write_text(content)
    latest = OUT_DIR / f'{args.workflow}_latest.md'
    tmp = OUT_DIR / f'{args.workflow}_latest.tmp.md'
    tmp.write_text(content)
    tmp.replace(latest)
    print(str(out))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
