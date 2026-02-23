#!/usr/bin/env python3
import argparse, json, datetime as dt
from pathlib import Path

BASE = Path('/Users/AI-OPS/.openclaw/workspace')
D = BASE / 'data' / 'decisions'
D.mkdir(parents=True, exist_ok=True)

ap = argparse.ArgumentParser()
ap.add_argument('--context', required=True)
ap.add_argument('--chosen', required=True)
ap.add_argument('--why', required=True)
ap.add_argument('--rejected', default='')
ap.add_argument('--impact', default='')
args = ap.parse_args()

stamp = dt.datetime.now().strftime('%Y%m%d_%H%M%S')
did = f"dec-{stamp}"
obj = {
  'decision_id': did,
  'timestamp': dt.datetime.now().isoformat(timespec='seconds'),
  'context': args.context,
  'chosen_option': args.chosen,
  'rejected_options': [x.strip() for x in args.rejected.split('|') if x.strip()],
  'rationale': args.why,
  'impact': args.impact
}
path = D / f"{did}.json"
path.write_text(json.dumps(obj, indent=2))
(BASE / 'generated' / 'decision_latest.json').write_text(json.dumps(obj, indent=2))
print(str(path))
