#!/usr/bin/env python3
import json, subprocess
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path('/Users/AI-OPS/.openclaw/workspace')
OUTDIR = ROOT / 'generated' / 'email'
OUTDIR.mkdir(parents=True, exist_ok=True)

NOISE_DOMAINS = {
    'linkedin.com','mail.squarespace.com','accounts.google.com','google.com','x.com','stripe.com'
}

def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or p.stdout.strip())
    return p.stdout.strip()

def unread(account):
    out = run(['himalaya','envelope','list','-a',account,'-f','INBOX','-s','200','--output','json','not','flag','seen'])
    if not out:
        return []
    return json.loads(out)

def domain(addr):
    return (addr or '').split('@')[-1].lower() if '@' in (addr or '') else ''

now = datetime.now(timezone.utc).isoformat()
report = {'generated_at': now, 'accounts': {}}

for acct in ['nick','burt']:
    try:
        rows = unread(acct)
    except Exception as e:
        report['accounts'][acct] = {'error': str(e), 'unread_total': 0, 'actionable_total': 0, 'actionable': []}
        continue
    actionable = []
    for r in rows:
        d = domain((r.get('from') or {}).get('addr'))
        if d in NOISE_DOMAINS:
            continue
        actionable.append({
            'id': r.get('id'),
            'date': r.get('date'),
            'from': (r.get('from') or {}).get('addr'),
            'subject': r.get('subject')
        })
    report['accounts'][acct] = {
        'unread_total': len(rows),
        'actionable_total': len(actionable),
        'actionable': actionable[:25]
    }

json_path = OUTDIR / 'email_hourly_latest.json'
md_path = OUTDIR / 'email_hourly_latest.md'
log_path = OUTDIR / 'email_hourly_log.jsonl'

json_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
with log_path.open('a', encoding='utf-8') as f:
    f.write(json.dumps(report) + '\n')

lines = [f"# Email Hourly Check", f"Generated: {now}", ""]
for acct, data in report['accounts'].items():
    lines.append(f"## {acct}")
    if 'error' in data:
        lines.append(f"- error: {data['error']}")
        continue
    lines.append(f"- unread_total: {data['unread_total']}")
    lines.append(f"- actionable_total: {data['actionable_total']}")
    for a in data['actionable'][:10]:
        lines.append(f"  - [{a['id']}] {a['subject']} — {a['from']} ({a['date']})")
    lines.append("")

md_path.write_text('\n'.join(lines), encoding='utf-8')
print(str(md_path))
