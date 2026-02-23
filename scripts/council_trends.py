#!/usr/bin/env python3
import re, json
from pathlib import Path
from datetime import datetime

BASE = Path('/Users/AI-OPS/.openclaw/workspace')
COUNCIL = BASE / 'data' / 'council'
OUT = BASE / 'generated' / 'council_trends_latest.json'

SEATS = ['MAGNUS','VERA','DANTE','ELEANOR','RAY','MIRA']
counts = {s:0 for s in SEATS}
sessions = 0

if COUNCIL.exists():
    for f in sorted(COUNCIL.glob('20*.md')):
        txt = f.read_text(errors='ignore')
        sessions += 1
        m = re.search(r'Most valuable perspective:\s*(.+)', txt, flags=re.I)
        if m:
            v = m.group(1).upper()
            for s in SEATS:
                if s in v:
                    counts[s] += 1
                    break

payload = {
    'generated_at': datetime.now().isoformat(timespec='seconds'),
    'sessions_analyzed': sessions,
    'most_valuable_counts': counts,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2))
print(OUT)
