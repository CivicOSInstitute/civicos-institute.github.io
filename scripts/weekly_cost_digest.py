#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime, timedelta
import subprocess

LOG = Path('/Users/AI-OPS/.openclaw/token-tracker/token_log.jsonl')
SEND = Path('/Users/AI-OPS/.openclaw/scripts/send-telegram.sh')


def parse_ts(v):
    try:
        return datetime.fromisoformat(v.replace('Z','+00:00'))
    except Exception:
        return None


cut = datetime.utcnow() - timedelta(days=7)
by_model = {}
count=0
if LOG.exists():
    for ln in LOG.read_text(errors='ignore').splitlines():
        try:
            j=json.loads(ln)
        except Exception:
            continue
        t=parse_ts(str(j.get('timestamp','')))
        if not t or t.replace(tzinfo=None) < cut: continue
        m=j.get('model','unknown')
        toks=int(j.get('total_tokens') or 0)
        by_model[m]=by_model.get(m,0)+toks
        count += 1

top = sorted(by_model.items(), key=lambda x:x[1], reverse=True)[:5]
msg = ['📊 Weekly Token Digest (7d)', f'Events: {count}', 'Top models by tokens:']
for m,t in top:
    msg.append(f'- {m}: {t:,}')
text='\n'.join(msg)
print(text)
if SEND.exists():
    subprocess.run([str(SEND), '8334496229', text], check=False)
