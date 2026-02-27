#!/usr/bin/env python3
from datetime import datetime
from pathlib import Path
import subprocess

ROOT = Path('/Users/AI-OPS/.openclaw/workspace')
CREATE = ROOT / 'notion-ops' / 'notion_task_create.sh'
stamp = datetime.now().strftime('%Y-%m-%d')
title = f"[Board-ready] Weekly governance summary draft ({stamp})"
cmd = [str(CREATE), '--title', title, '--status', 'Not started', '--priority', 'P1', '--channel', 'Architecture']
p = subprocess.run(cmd, cwd=str(ROOT / 'notion-ops'), capture_output=True, text=True)
if p.returncode != 0:
    raise SystemExit(p.stderr)
print(p.stdout.strip())
