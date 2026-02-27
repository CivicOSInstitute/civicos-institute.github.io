#!/usr/bin/env python3
import json, subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path('/Users/AI-OPS/.openclaw/workspace')
EMAIL_JSON = ROOT / 'generated' / 'email' / 'email_hourly_latest.json'
STATE = ROOT / 'generated' / 'notion' / 'email_synced_ids.json'
CREATE = ROOT / 'notion-ops' / 'notion_task_create.sh'

STATE.parent.mkdir(parents=True, exist_ok=True)

if not EMAIL_JSON.exists():
    raise SystemExit('email report missing')

data = json.loads(EMAIL_JSON.read_text())
synced = set(json.loads(STATE.read_text()) if STATE.exists() else [])
new_ids = set(synced)

for acct, block in data.get('accounts', {}).items():
    for a in block.get('actionable', []):
        mid = str(a.get('id'))
        if not mid or mid in synced:
            continue
        title = f"Email action ({acct}) [{mid}]: {a.get('subject','(no subject)')[:80]}"
        cmd = [str(CREATE), '--title', title, '--status', 'Not started', '--priority', 'P2', '--channel', 'Email']
        p = subprocess.run(cmd, cwd=str(ROOT / 'notion-ops'), capture_output=True, text=True)
        if p.returncode == 0:
            new_ids.add(mid)
            print(f"created: {mid}")
        else:
            print(f"skip/fail: {mid} :: {p.stderr.strip()[:200]}")

STATE.write_text(json.dumps(sorted(new_ids)))
print(f"synced_count={len(new_ids)}")
