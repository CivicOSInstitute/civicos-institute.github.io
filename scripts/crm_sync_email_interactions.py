#!/usr/bin/env python3
import json
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path('/Users/AI-OPS/.openclaw/workspace')
EMAIL_JSON = ROOT / 'generated' / 'email' / 'email_hourly_latest.json'
STATE_PATH = ROOT / 'generated' / 'crm' / 'email_synced_ids.json'
REVIEW_PATH = ROOT / 'generated' / 'crm' / 'manual_review_contacts.jsonl'
REPORT_JSON = ROOT / 'generated' / 'crm' / 'crm_email_sync_latest.json'
REPORT_MD = ROOT / 'generated' / 'crm' / 'crm_email_sync_latest.md'
DB_PATH = '/data/crm.db'
CONTAINER = 'civic-crm'

for p in [STATE_PATH.parent, REVIEW_PATH.parent]:
    p.mkdir(parents=True, exist_ok=True)

if not EMAIL_JSON.exists():
    raise SystemExit('missing email report')

payload = json.loads(EMAIL_JSON.read_text())
synced_ids = set(json.loads(STATE_PATH.read_text()) if STATE_PATH.exists() else [])
now = datetime.now(timezone.utc)

rows = []
for acct, block in payload.get('accounts', {}).items():
    for a in block.get('actionable', []):
        mid = str(a.get('id') or '')
        if not mid or mid in synced_ids:
            continue
        rows.append({
            'message_id': mid,
            'account': acct,
            'from': (a.get('from') or '').strip().lower(),
            'subject': (a.get('subject') or '').strip(),
            'date': a.get('date') or ''
        })

# run inside container to update sqlite reliably
script = r'''
import sqlite3, json, sys
from datetime import datetime

db_path = sys.argv[1]
rows = json.loads(sys.argv[2])
con = sqlite3.connect(db_path)
cur = con.cursor()

result = {
  'processed': 0,
  'matched': 0,
  'logged': 0,
  'manual_review': 0,
  'board_ready': 0,
  'manual': [],
  'synced_ids': []
}

def parse_date(s):
    # formats like 2026-02-27 14:22-08:00
    if not s:
        return datetime.utcnow().date().isoformat()
    try:
        return datetime.fromisoformat(s.replace(' ', 'T')).date().isoformat()
    except Exception:
        return datetime.utcnow().date().isoformat()

for r in rows:
    result['processed'] += 1
    sender = r.get('from','').lower()
    msg_id = r.get('message_id')
    subj = r.get('subject','(no subject)')
    msg_date = parse_date(r.get('date',''))

    if not sender or '@' not in sender:
        result['manual_review'] += 1
        result['manual'].append({**r, 'reason':'missing_or_invalid_email'})
        continue

    # dedupe key is email
    c = cur.execute(
        """SELECT id,name,email,capacity_giving,grant_program
           FROM contact
           WHERE lower(email)=? OR lower(work_email)=? OR lower(home_email)=?
           LIMIT 1""",
        (sender,sender,sender)
    ).fetchone()

    if not c:
        result['manual_review'] += 1
        result['manual'].append({**r, 'reason':'contact_not_found'})
        continue

    contact_id, name, email, cap, grant = c
    result['matched'] += 1

    board_ready = bool((cap or '').strip()) or bool((grant or '').strip())
    if board_ready:
        result['board_ready'] += 1

    summary_prefix = '[Board-ready] ' if board_ready else ''
    summary = f"{summary_prefix}Inbound email from {sender}: {subj}"
    outcome = 'Logged from automated hourly email sync'

    # update last contact
    cur.execute("UPDATE contact SET last_contact_date=?, updated_date=? WHERE id=?", (msg_date, msg_date, contact_id))

    # insert interaction
    cur.execute(
        """INSERT INTO interaction(contact_id,date,type,summary,outcome,follow_up_needed,created_by)
           VALUES(?,?,?,?,?,?,?)""",
        (contact_id, msg_date, 'email', summary, outcome, 0, 'openclaw:auto')
    )
    result['logged'] += 1
    result['synced_ids'].append(msg_id)

con.commit()
con.close()
print(json.dumps(result))
'''

cmd = [
    'docker','exec',CONTAINER,'python3','-c',script,DB_PATH,json.dumps(rows)
]
proc = subprocess.run(cmd, capture_output=True, text=True)
if proc.returncode != 0:
    raise SystemExit(proc.stderr.strip() or proc.stdout.strip())

res = json.loads(proc.stdout.strip() or '{}')

# persist manual review queue
with REVIEW_PATH.open('a', encoding='utf-8') as f:
    for m in res.get('manual', []):
        f.write(json.dumps({'ts': now.isoformat(), **m}) + '\n')

# update state with only successfully synced ids
synced_ids.update(res.get('synced_ids', []))
STATE_PATH.write_text(json.dumps(sorted(synced_ids), indent=2), encoding='utf-8')

report = {
  'generated_at': now.isoformat(),
  'input_actionable_count': len(rows),
  **res,
  'state_size': len(synced_ids),
  'manual_review_file': str(REVIEW_PATH)
}
REPORT_JSON.write_text(json.dumps(report, indent=2), encoding='utf-8')

md = [
    '# CRM Email Sync',
    f"Generated: {report['generated_at']}",
    '',
    f"- input_actionable_count: {report['input_actionable_count']}",
    f"- processed: {report.get('processed',0)}",
    f"- matched: {report.get('matched',0)}",
    f"- logged: {report.get('logged',0)}",
    f"- manual_review: {report.get('manual_review',0)}",
    f"- board_ready_flagged: {report.get('board_ready',0)}",
    f"- state_size: {report.get('state_size',0)}",
    f"- manual_review_file: {report['manual_review_file']}",
]
REPORT_MD.write_text('\n'.join(md), encoding='utf-8')
print(REPORT_MD)
