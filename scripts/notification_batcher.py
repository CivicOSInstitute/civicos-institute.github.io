#!/usr/bin/env python3
"""Batch non-urgent alerts into a daily digest file.
Severity routing:
- critical/high -> immediate lane (kept separate)
- medium/low -> batched digest
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

WORKSPACE = Path('/Users/AI-OPS/.openclaw/workspace')
SRC = WORKSPACE / 'generated'
OUT = WORKSPACE / 'generated' / 'notifications'
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    day = datetime.now().strftime('%Y-%m-%d')
    digest_items = []

    # Pull from SLO alerts as initial source
    for fp in sorted(SRC.glob('workflow_slo_alert_*.txt'))[-20:]:
        try:
            txt = fp.read_text(errors='ignore').strip()
        except Exception:
            continue
        if txt:
            digest_items.append({
                'source': fp.name,
                'severity': 'medium',
                'message': txt.splitlines()[0][:180],
            })

    payload = {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'workflow': 'notification_batcher',
        'lane': 'prod-critical',
        'policy': {'critical': 'immediate', 'high': 'immediate', 'medium': 'batched', 'low': 'batched'},
        'items': digest_items,
    }

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_json = OUT / f'notification_digest_{ts}.json'
    latest_json = OUT / 'notification_digest_latest.json'
    out_json.write_text(json.dumps(payload, indent=2))
    tmp = OUT / 'notification_digest_latest.tmp.json'
    tmp.write_text(json.dumps(payload, indent=2))
    tmp.replace(latest_json)

    out_md = OUT / f'notification_digest_{ts}.md'
    latest_md = OUT / 'notification_digest_latest.md'
    lines = [f"# Notification Digest — {day}", "", f"Items: {len(digest_items)}", ""]
    for i, it in enumerate(digest_items, 1):
        lines.append(f"{i}. [{it['severity']}] {it['source']} — {it['message']}")
    out_md.write_text('\n'.join(lines))
    tmp_md = OUT / 'notification_digest_latest.tmp.md'
    tmp_md.write_text('\n'.join(lines))
    tmp_md.replace(latest_md)

    print(str(out_json))
    print(str(out_md))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
