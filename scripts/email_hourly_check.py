#!/usr/bin/env python3
import json, subprocess
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path('/Users/AI-OPS/.openclaw/workspace')
OUTDIR = ROOT / 'generated' / 'email'
OUTDIR.mkdir(parents=True, exist_ok=True)
POLICY_PATH = ROOT / 'config' / 'email_policy.json'

NOISE_DOMAINS = {
    'linkedin.com','mail.squarespace.com','accounts.google.com','google.com','x.com','stripe.com'
}
GITHUB_SENDERS = {'support@github.com','no-reply@github.com'}


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or p.stdout.strip())
    return p.stdout.strip()


def unread(account):
    out = run(['himalaya','envelope','list','-a',account,'-f','INBOX','-s','300','--output','json','not','flag','seen'])
    return json.loads(out) if out else []


def all_mail(account):
    out = run(['himalaya','envelope','list','-a',account,'-f','[Gmail]/All Mail','-s','300','--output','json'])
    return json.loads(out) if out else []


def domain(addr):
    return (addr or '').split('@')[-1].lower() if '@' in (addr or '') else ''


def parse_dt(s):
    # himalaya format like "2026-02-11 19:54-08:00"
    try:
        return datetime.fromisoformat(s.replace(' ', 'T'))
    except Exception:
        return None


def load_policy():
    if POLICY_PATH.exists():
        return json.loads(POLICY_PATH.read_text())
    return {
        'gmail': {
            'github_ci_archive_after_days': 7,
            'system_mail_mode': 'summarize_only',
            'deletions_require_confirmation': True,
            'autonomous_cleanup_enabled': False,
            'test_run': {'enabled': False, 'mode': 'dry_run', 'duration_hours': 24}
        }
    }


now = datetime.now(timezone.utc)
policy = load_policy().get('gmail', {})
report = {
    'generated_at': now.isoformat(),
    'policy': policy,
    'accounts': {}
}

for acct in ['nick','burt']:
    try:
        rows = unread(acct)
    except Exception as e:
        report['accounts'][acct] = {'error': str(e), 'unread_total': 0, 'actionable_total': 0, 'actionable': [], 'would_archive': []}
        continue

    actionable, system_mail = [], []
    for r in rows:
        addr = (r.get('from') or {}).get('addr', '').lower()
        dom = domain(addr)
        item = {
            'id': r.get('id'),
            'date': r.get('date'),
            'from': addr,
            'subject': r.get('subject')
        }
        if dom in NOISE_DOMAINS:
            system_mail.append(item)
        else:
            actionable.append(item)

    # dry-run candidate detection: github/ci older than X days from all-mail
    would_archive = []
    try:
        older_than = int(policy.get('github_ci_archive_after_days', 7))
        for r in all_mail(acct):
            addr = (r.get('from') or {}).get('addr', '').lower()
            subj = (r.get('subject') or '').lower()
            dt = parse_dt(r.get('date',''))
            if not dt:
                continue
            age_days = (now - dt.astimezone(timezone.utc)).days
            ci_term = (' ci ' in f' {subj} ') or ('[ci]' in subj) or ('continuous integration' in subj)
            githubish = (addr in GITHUB_SENDERS) or ('github' in addr) or ci_term
            if githubish and age_days > older_than:
                would_archive.append({
                    'id': r.get('id'),
                    'date': r.get('date'),
                    'from': addr,
                    'subject': r.get('subject'),
                    'age_days': age_days
                })
    except Exception:
        pass

    report['accounts'][acct] = {
        'unread_total': len(rows),
        'actionable_total': len(actionable),
        'actionable': actionable[:25],
        'system_mail_summary_count': len(system_mail),
        'system_mail_sample': system_mail[:10],
        'would_archive_count': len(would_archive),
        'would_archive': sorted(would_archive, key=lambda x: -x['age_days'])[:50],
        'cleanup_executed': False,
        'mode': 'dry_run'
    }

json_path = OUTDIR / 'email_hourly_latest.json'
md_path = OUTDIR / 'email_hourly_latest.md'
log_path = OUTDIR / 'email_hourly_log.jsonl'

json_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
with log_path.open('a', encoding='utf-8') as f:
    f.write(json.dumps(report) + '\n')

lines = [f"# Email Hourly Check (Dry Run)", f"Generated: {report['generated_at']}", ""]
for acct, data in report['accounts'].items():
    lines.append(f"## {acct}")
    if 'error' in data:
        lines.append(f"- error: {data['error']}")
        continue
    lines.append(f"- unread_total: {data['unread_total']}")
    lines.append(f"- actionable_total: {data['actionable_total']}")
    lines.append(f"- system_mail_summary_count: {data['system_mail_summary_count']}")
    lines.append(f"- would_archive_count (older github/ci): {data['would_archive_count']}")
    for a in data['actionable'][:10]:
        lines.append(f"  - ACTIONABLE [{a['id']}] {a['subject']} — {a['from']} ({a['date']})")
    for a in data['would_archive'][:5]:
        lines.append(f"  - WOULD_ARCHIVE [{a['id']}] {a['subject']} — {a['from']} ({a['age_days']}d)")
    lines.append("")

md_path.write_text('\n'.join(lines), encoding='utf-8')
print(str(md_path))
