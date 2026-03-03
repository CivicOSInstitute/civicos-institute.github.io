#!/usr/bin/env python3
from pathlib import Path
import json, re

LOGS = [
    Path('/Users/AI-OPS/.openclaw/logs/autonomous-agent.log'),
    Path('/Users/AI-OPS/.openclaw/logs/router-queue.log')
]
OUT = Path('/Users/AI-OPS/.openclaw/workspace/mission-control/data/router-last10.json')


def classify(reason: str) -> str:
    r = (reason or '').lower()
    if any(k in r for k in ['email', 'inbox', 'gmail']): return 'Email'
    if any(k in r for k in ['coding', 'code', 'engineer', 'debug']): return 'Coding'
    if any(k in r for k in ['writing', 'narrative', 'content']): return 'Writing'
    if any(k in r for k in ['strategy', 'business', 'executive']): return 'Strategy'
    if any(k in r for k in ['analysis', 'q&a', 'philosopher', 'reasoning']): return 'Analysis/Q&A'
    if any(k in r for k in ['multimodal', 'vision', 'ocr']): return 'Vision/OCR'
    if any(k in r for k in ['triage', 'status', 'summary', 'rapid']): return 'Triage/Status'
    if any(k in r for k in ['contrarian', 'challenge']): return 'Contrarian Review'
    return 'General'

entries = []
for p in LOGS:
    if not p.exists():
        continue
    for line in p.read_text(errors='ignore').splitlines():
        m = re.search(r'\[(.*?)\].*?\[ROUTING\].*?(Decision: (\w+) \| Model: ([^|]+) \| Reason: (.*)|→ (local|escalate) \| ([^|]+) \| (.*))', line)
        if m:
            ts = m.group(1)
            route = m.group(3) or m.group(6) or ''
            model = (m.group(4) or m.group(7) or '').strip()
            reason = (m.group(5) or m.group(8) or '').strip()
            entries.append({
                'time': ts,
                'request_type': classify(reason),
                'model': model,
                'route': route.lower() if route else ('local' if ':' in model else 'escalate'),
                'reason': reason
            })

# keep order and tail 10
items = entries[-10:]
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({'items': items}, indent=2))
print(f'wrote {OUT} with {len(items)} items')
