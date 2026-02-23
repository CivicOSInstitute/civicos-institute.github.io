#!/usr/bin/env python3
import argparse, json, datetime as dt
from pathlib import Path

BASE = Path('/Users/AI-OPS/.openclaw/workspace')
GEN = BASE / 'generated'
MEM = BASE / 'memory' / f"{dt.date.today().isoformat()}.md"
GEN.mkdir(parents=True, exist_ok=True)
MEM.parent.mkdir(parents=True, exist_ok=True)

ap = argparse.ArgumentParser()
ap.add_argument('--objective', required=True)
ap.add_argument('--state', default='')
ap.add_argument('--blockers', default='')
ap.add_argument('--next-step', required=True)
ap.add_argument('--rationale', default='')
args = ap.parse_args()

payload = {
  'timestamp': dt.datetime.now().isoformat(timespec='seconds'),
  'objective': args.objective.strip(),
  'state': args.state.strip(),
  'blockers': args.blockers.strip(),
  'next_step': args.next_step.strip(),
  'rationale': args.rationale.strip()
}

(GEN / 'handoff_checkpoint_latest.json').write_text(json.dumps(payload, indent=2))

with MEM.open('a', encoding='utf-8') as f:
    f.write(f"- Checkpoint {payload['timestamp']}: objective={payload['objective']} | next={payload['next_step']}\n")

print(str(GEN / 'handoff_checkpoint_latest.json'))
