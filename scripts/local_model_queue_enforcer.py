#!/usr/bin/env python3
"""
Enforce hard rule: any local model invocation must go through ollama-agent-queue.
Scans executable scripts for direct Ollama usage and exits non-zero on violations.
"""

from pathlib import Path
import re
import sys

ROOT = Path('/Users/AI-OPS/.openclaw/workspace')
SCAN_DIRS = [ROOT / 'scripts', ROOT / 'skills']
ALLOWED_PATH_SNIPPETS = [
    'skills/ollama-agent-queue/scripts/queue_manager.py',
    'skills/ollama-agent-queue/scripts/integration_helper.py',
    'scripts/local_model_queue_enforcer.py',
]
PATTERNS = [
    re.compile(r"\bollama\s+run\b"),
    re.compile(r"localhost:11434"),
    re.compile(r"/api/generate"),
    re.compile(r"['\"]ollama['\"]\s*,\s*['\"]run['\"]"),
]

violations = []
for base in SCAN_DIRS:
    if not base.exists():
        continue
    for p in base.rglob('*'):
        if not p.is_file() or p.suffix not in {'.py', '.sh'}:
            continue
        rel = str(p.relative_to(ROOT))
        if any(x in rel for x in ALLOWED_PATH_SNIPPETS):
            continue
        txt = p.read_text(encoding='utf-8', errors='ignore')
        for pat in PATTERNS:
            if pat.search(txt):
                violations.append(rel)
                break

if violations:
    print('LOCAL_MODEL_QUEUE_ENFORCER: FAIL')
    for v in sorted(set(violations)):
        print(v)
    sys.exit(1)

print('LOCAL_MODEL_QUEUE_ENFORCER: PASS')
