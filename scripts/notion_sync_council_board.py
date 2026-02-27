#!/usr/bin/env python3
import json, subprocess, re
from pathlib import Path

ROOT = Path('/Users/AI-OPS/.openclaw/workspace')
COUNCIL_DIR = ROOT / 'data' / 'council'
STATE = ROOT / 'generated' / 'notion' / 'council_synced.json'
CREATE = ROOT / 'notion-ops' / 'notion_task_create.sh'

STATE.parent.mkdir(parents=True, exist_ok=True)
synced = set(json.loads(STATE.read_text()) if STATE.exists() else [])
new_synced = set(synced)

files = sorted([p for p in COUNCIL_DIR.glob('*.md') if 'TEMPLATE' not in p.name and 'MODEL_ROUTING' not in p.name])
for f in files:
    key = f.name
    if key in synced:
        continue
    txt = f.read_text(errors='ignore')
    topic = re.search(r'^Topic:\s*(.+)$', txt, re.M)
    topic = topic.group(1).strip() if topic else f.stem
    title = f"[Board-ready] Council decision: {topic[:90]}"
    cmd = [str(CREATE), '--title', title, '--status', 'Not started', '--priority', 'P1', '--channel', 'Architecture']
    p = subprocess.run(cmd, cwd=str(ROOT / 'notion-ops'), capture_output=True, text=True)
    if p.returncode == 0:
        new_synced.add(key)
        print(f"created: {key}")
    else:
        print(f"failed: {key} :: {p.stderr.strip()[:200]}")

STATE.write_text(json.dumps(sorted(new_synced), indent=2))
print(f"synced_count={len(new_synced)}")
