#!/usr/bin/env python3
import json, subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path('/Users/AI-OPS/.openclaw/workspace')
RSTATE = ROOT / 'generated' / 'drive' / 'routing_state.json'
GA_JSON = ROOT / 'generated' / 'analytics' / 'ga4_daily_latest.json'
GA_MD = ROOT / 'generated' / 'analytics' / 'ga4_daily_latest.md'
OUT = ROOT / 'generated' / 'analytics' / 'drive_route_latest.json'
ACCOUNT = 'ncerbone@civicos-institute.org'

if not RSTATE.exists():
    raise SystemExit('missing drive routing_state.json')
state = json.loads(RSTATE.read_text())
ops_id = state['folders']['Ops-Reports']
dec_id = state['folders']['Decision-Logs']

def run(args):
    p = subprocess.run(args, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout).strip())
    return json.loads(p.stdout)

uploads=[]
ts=datetime.now().strftime('%Y%m%d-%H%M%S')
for p in [GA_JSON, GA_MD]:
    if p.exists():
        j = run(['gog','drive','upload',str(p),'--account',ACCOUNT,'--parent',ops_id,'--name',f'{p.stem}_{ts}{p.suffix}','--json'])
        f=j.get('file',j)
        uploads.append({'type':'ops_report','name':f.get('name'),'id':f.get('id')})

# board-ready decision-log route if flags present
if GA_JSON.exists():
    ga = json.loads(GA_JSON.read_text())
    flags = ga.get('board_ready_flags',[])
    if flags:
        note = ROOT / 'generated' / 'analytics' / f'board_ready_analytics_flags_{ts}.md'
        lines=['# [Board-ready] Analytics swing flags','',f"Generated: {ga.get('generated_at')}"]
        for f in flags:
            lines.append(f"- {f.get('metric')}: {f.get('wow_pct')}% WoW")
        note.write_text('\n'.join(lines), encoding='utf-8')
        j = run(['gog','drive','upload',str(note),'--account',ACCOUNT,'--parent',dec_id,'--name',note.name,'--json'])
        ff=j.get('file',j)
        uploads.append({'type':'decision_log','name':ff.get('name'),'id':ff.get('id')})

result={'generated_at':datetime.now().isoformat(),'uploads':uploads}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(result,indent=2),encoding='utf-8')
print(OUT)
