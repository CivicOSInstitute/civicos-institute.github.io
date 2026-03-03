#!/usr/bin/env python3
from pathlib import Path
import json, re

LOGS = [
    Path('/Users/AI-OPS/.openclaw/logs/autonomous-agent.log'),
    Path('/Users/AI-OPS/.openclaw/logs/router-queue.log')
]
TELEMETRY = Path('/Users/AI-OPS/.openclaw/workspace/data/telemetry/router_telemetry.jsonl')
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

# 1) Prefer structured telemetry (most accurate)
if TELEMETRY.exists():
    for line in TELEMETRY.read_text(errors='ignore').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        ts = r.get('timestamp') or ''
        route = (r.get('route') or '').lower()
        model = r.get('model') or r.get('model_used') or ''
        reason = r.get('reason') or r.get('category') or ''
        if ts and model:
            entries.append({
                'time': ts,
                'request_type': classify(reason),
                'model': model,
                'route': route or ('local' if ':' in model else 'escalate'),
                'reason': reason
            })

# 2) Backfill from legacy logs
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

# de-dup + sort + tail 10
seen = set()
uniq = []
for e in sorted(entries, key=lambda x: x.get('time', '')):
    k = (e.get('time'), e.get('model'), e.get('route'), e.get('reason'))
    if k in seen:
        continue
    seen.add(k)
    uniq.append(e)
items = uniq[-10:]
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({'items': items}, indent=2))
print(f'wrote {OUT} with {len(items)} items')
