#!/usr/bin/env python3
"""
Donor Stewardship Runtime Scaffold (safe mode)
- Follows skills/donor-stewardship contract
- Reads config and mock CRM data
- Writes queue/test artifacts
- NEVER performs CRM writes (dry-run only)

Usage:
  python3 scripts/donor_stewardship_runner.py --mode ack --dry-run
  python3 scripts/donor_stewardship_runner.py --mode lapse --dry-run
  python3 scripts/donor_stewardship_runner.py --mode portfolio --dry-run
  python3 scripts/donor_stewardship_runner.py --mode major --donor "Jane Doe" --dry-run
"""

import argparse
import datetime as dt
import json
from pathlib import Path

BASE = Path('/Users/AI-OPS/.openclaw/workspace')
DATA = BASE / 'data'
QUEUE = DATA / 'queue' / 'pending'
CRM_LOG = DATA / 'crm'
GEN = BASE / 'generated'

QUEUE.mkdir(parents=True, exist_ok=True)
CRM_LOG.mkdir(parents=True, exist_ok=True)
GEN.mkdir(parents=True, exist_ok=True)

MOCK_CRM = DATA / 'crm' / 'mock_donors.json'


def now_iso():
    return dt.datetime.now().isoformat(timespec='seconds')


def log_query(mode, query_name, records):
    p = CRM_LOG / f"query-log-{dt.date.today().isoformat()}.json"
    rows = []
    if p.exists():
        try:
            rows = json.loads(p.read_text())
        except Exception:
            rows = []
    rows.append({
        'timestamp': now_iso(),
        'mode': mode,
        'query': query_name,
        'record_count': records,
    })
    p.write_text(json.dumps(rows, indent=2))


def load_mock():
    if MOCK_CRM.exists():
        return json.loads(MOCK_CRM.read_text())
    sample = {
        'donors': [
            {
                'id': 'd-1001',
                'first_name': 'Alex',
                'preferred_name': 'Alex',
                'email': 'alex@example.org',
                'last_gift_date': '2025-03-20',
                'lifetime_giving': 1400,
                'largest_gift': 750,
                'recurring_overdue_days': 0,
            }
        ],
        'gifts': [
            {
                'crm_gift_id': 'g-5001',
                'donor_id': 'd-1001',
                'amount': 300,
                'gift_date': dt.date.today().isoformat(),
                'acknowledgment_sent': False,
            }
        ]
    }
    MOCK_CRM.write_text(json.dumps(sample, indent=2))
    return sample


def gift_tier(donor, gift):
    if donor.get('lifetime_giving', 0) <= gift['amount']:
        return 1
    if gift['amount'] > donor.get('largest_gift', 0):
        return 2
    # scaffold heuristic for tiers 3/4
    return 4


def write_ack_queue(donor, gift, tier):
    gift_date = gift['gift_date']
    fid = f"ack-{donor['id']}-{gift_date}"
    priority = 'urgent' if gift['amount'] > 2500 else ('high' if gift['amount'] > 500 else 'standard')
    f = QUEUE / f"ack-{donor['id']}-{gift_date}.md"
    header = {
        'id': fid,
        'type': 'acknowledgment_letter',
        'destination_type': 'email',
        'destination': donor.get('email', ''),
        'donor_first_name': donor.get('preferred_name') or donor.get('first_name') or 'Friend',
        'gift_amount': gift['amount'],
        'gift_date': gift_date,
        'gift_tier': tier,
        'priority': priority,
        'crm_gift_id': gift['crm_gift_id'],
        'status': 'pending',
        'created': now_iso(),
        'model': 'local/qwen-14b'
    }
    # minimal body scaffold, no banned phrases
    body = (
        f"Hi {header['donor_first_name']},\n\n"
        f"Thank you for your ${gift['amount']:.2f} gift on {gift_date}. "
        "Your support directly advances CivicOS AI literacy work for students and educators.\n\n"
        "This contribution helps us expand practical, privacy-first learning infrastructure this quarter.\n\n"
        "With appreciation,\n"
        "Nick Cerbone\n"
        "CivicOS Institute\n"
    )
    yaml = "\n".join([f"{k}: {v}" for k, v in header.items()])
    f.write_text(f"---\n{yaml}\n---\n\n{body}")
    return str(f), fid, priority


def mode_ack(data, dry):
    gifts = [g for g in data['gifts'] if not g.get('acknowledgment_sent')]
    log_query('ack', 'new_unack_gifts', len(gifts))
    out = []
    for g in gifts:
        donor = next((d for d in data['donors'] if d['id'] == g['donor_id']), None)
        if not donor:
            continue
        tier = gift_tier(donor, g)
        if not dry:
            qf, qid, pr = write_ack_queue(donor, g, tier)
        else:
            qf, qid, pr = '(dry-run)', f"ack-{donor['id']}-{g['gift_date']}", ('high' if g['amount'] > 500 else 'standard')
        out.append({'queue_file': qf, 'id': qid, 'tier': tier, 'priority': pr, 'first_name': donor.get('first_name'), 'amount': g['amount']})
    return {'mode': 'ack', 'count': len(out), 'items': out}


def months_since(date_str):
    d = dt.date.fromisoformat(date_str)
    today = dt.date.today()
    return (today.year - d.year) * 12 + (today.month - d.month)


def mode_lapse(data):
    donors = data['donors']
    imminent = []
    window = []
    recurring = []
    for d in donors:
        m = months_since(d['last_gift_date'])
        if 11 <= m <= 13:
            imminent.append(d['id'])
        elif 9 <= m <= 11:
            window.append(d['id'])
        if (d.get('recurring_overdue_days') or 0) > 14:
            recurring.append(d['id'])
    log_query('lapse', 'lapse_scan', len(donors))
    return {
        'mode': 'lapse',
        'imminent_count': len(imminent),
        'window_count': len(window),
        'recurring_issues': len(recurring)
    }


def mode_portfolio(data):
    donors = data['donors']
    gifts = data['gifts']
    active = len([d for d in donors if months_since(d['last_gift_date']) <= 12])
    rev_mtd = sum(g['amount'] for g in gifts if g['gift_date'][:7] == dt.date.today().isoformat()[:7])
    log_query('portfolio', 'portfolio_aggregate', len(donors) + len(gifts))
    return {
        'mode': 'portfolio',
        'active_donors_12mo': active,
        'revenue_mtd': rev_mtd,
        'new_donors_mtd': 0,
        'major_donor_count': len([d for d in donors if d.get('lifetime_giving', 0) > 500])
    }


def mode_major(data, donor_name):
    d = next((x for x in data['donors'] if donor_name.lower() in (x.get('first_name','').lower() + ' ' + x.get('preferred_name','').lower())), None)
    log_query('major', 'major_brief_lookup', 1 if d else 0)
    if not d:
        return {'mode': 'major', 'found': False}
    return {
        'mode': 'major',
        'found': True,
        'donor_id': d['id'],
        'snapshot': {
            'lifetime_giving': d.get('lifetime_giving', 0),
            'largest_gift': d.get('largest_gift', 0),
            'months_since_last_gift': months_since(d['last_gift_date'])
        },
        'note': 'Scaffold brief only. Full high-stakes synthesis intentionally not performed in scaffold mode.'
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', choices=['ack', 'lapse', 'major', 'portfolio'], required=True)
    ap.add_argument('--donor', default='')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    data = load_mock()

    if args.mode == 'ack':
        res = mode_ack(data, args.dry_run)
    elif args.mode == 'lapse':
        res = mode_lapse(data)
    elif args.mode == 'major':
        res = mode_major(data, args.donor)
    else:
        res = mode_portfolio(data)

    out = GEN / f"donor_stewardship_{args.mode}_latest.json"
    out.write_text(json.dumps({'generated_at': now_iso(), **res}, indent=2))
    print(out)
    print(json.dumps(res, indent=2))


if __name__ == '__main__':
    main()
