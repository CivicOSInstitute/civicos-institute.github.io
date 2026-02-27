#!/usr/bin/env python3
import json, subprocess
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path('/Users/AI-OPS/.openclaw/workspace')
OUT = ROOT / 'generated' / 'integration'
OUT.mkdir(parents=True, exist_ok=True)

status = {
  'generated_at': datetime.now(timezone.utc).isoformat(),
  'checks': {}
}

def sh(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout or '').strip(), (p.stderr or '').strip()

# Gmail/Himalaya hourly checker artifact
email_json = ROOT / 'generated' / 'email' / 'email_hourly_latest.json'
status['checks']['gmail_himalaya'] = {'ok': email_json.exists(), 'artifact': str(email_json)}

# Notion token env
notion_env = Path.home() / '.openclaw' / '.env.notion'
status['checks']['notion_env'] = {'ok': notion_env.exists(), 'artifact': str(notion_env)}

# Notion auth ping
rc,out,err = sh(['python3','-c',
"import os,re,json,urllib.request,pathlib; p=pathlib.Path.home()/'.openclaw'/'.env.notion'; t=p.read_text(); m=re.search(r'NOTION_TOKEN=(.+)',t); tok=m.group(1).strip() if m else ''; req=urllib.request.Request('https://api.notion.com/v1/users/me',headers={'Authorization':f'Bearer {tok}','Notion-Version':'2022-06-28'});\nimport urllib.error;\n\ntry:\n r=urllib.request.urlopen(req,timeout=15); print('ok')\nexcept Exception as e:\n print('fail')"])
status['checks']['notion_api'] = {'ok': 'ok' in out.lower(), 'detail': out or err}

# Google Workspace quick checks (both accounts)
for acct in ['burt@civicos-institute.org','ncerbone@civicos-institute.org']:
    rc_g,out_g,err_g = sh(['gog','gmail','search','--account',acct,'--max','1','in:inbox','--json'])
    status['checks'][f'google_gmail_api[{acct}]'] = {'ok': rc_g==0}
    rc_d,out_d,err_d = sh(['gog','drive','ls','--account',acct,'--json'])
    status['checks'][f'google_drive_api[{acct}]'] = {'ok': rc_d==0}
    rc_c,out_c,err_c = sh(['gog','calendar','calendars','--account',acct,'--max','1','--json'])
    status['checks'][f'google_calendar_api[{acct}]'] = {'ok': rc_c==0, 'detail': '' if rc_c==0 else (err_c or out_c)[:180]}

# write reports
j = OUT / 'integration_health_latest.json'
m = OUT / 'integration_health_latest.md'
j.write_text(json.dumps(status, indent=2), encoding='utf-8')
lines=["# Integration Health",f"Generated: {status['generated_at']}",""]
for k,v in status['checks'].items():
    icon='✅' if v.get('ok') else '⚠️'
    lines.append(f"- {icon} {k}: {'OK' if v.get('ok') else 'ISSUE'}")
    if v.get('detail'): lines.append(f"  - detail: {v['detail']}")
    if v.get('artifact'): lines.append(f"  - artifact: {v['artifact']}")
m.write_text('\n'.join(lines), encoding='utf-8')
print(m)
