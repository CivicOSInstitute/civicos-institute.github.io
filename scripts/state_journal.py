#!/usr/bin/env python3
import argparse, json, datetime as dt
from pathlib import Path

BASE = Path('/Users/AI-OPS/.openclaw/workspace')
S = BASE / 'data' / 'state'
S.mkdir(parents=True, exist_ok=True)

ap = argparse.ArgumentParser()
ap.add_argument('--project', required=True, help='slug e.g. kdp_founders')
ap.add_argument('--status', required=True)
ap.add_argument('--next', required=True)
ap.add_argument('--notes', default='')
args = ap.parse_args()

path = S / f"{args.project}.json"
obj = {'project': args.project, 'history': []}
if path.exists():
    try: obj = json.loads(path.read_text())
    except: pass

entry = {
  'timestamp': dt.datetime.now().isoformat(timespec='seconds'),
  'status': args.status,
  'next_step': args.next,
  'notes': args.notes
}
obj.setdefault('history', []).append(entry)
obj['current'] = entry
path.write_text(json.dumps(obj, indent=2))
(BASE/'generated'/'state_latest.json').write_text(json.dumps({'project':args.project, **entry}, indent=2))
print(str(path))
