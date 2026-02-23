#!/usr/bin/env python3
from pathlib import Path
import json,re,datetime as dt,subprocess

BASE=Path('/Users/AI-OPS/.openclaw/workspace')
SEND=Path('/Users/AI-OPS/.openclaw/scripts/send-telegram.sh')
out=BASE/'generated'/'routing_compliance_latest.json'

checks=[]
viol=[]

# Rule: social queue should not include donor-identifying fields
sq=BASE/'social_media'/'queue'/'latest.md'
if sq.exists():
    txt=sq.read_text(errors='ignore')
    bad=re.findall(r'\b(donor|donation amount|bank account|routing number|ssn)\b', txt, flags=re.I)
    checks.append({'name':'social_sensitive_scan','status':'ok' if not bad else 'error','matches':len(bad)})
    if bad:
        viol.append('Sensitive donor/financial terms detected in social queue draft.')

# Rule: architecture health errors should be explicit in health file
ah=BASE/'generated'/'automation_health.json'
if ah.exists():
    j=json.loads(ah.read_text())
    errs=[s for s in j.get('steps',[]) if s.get('status')!='ok']
    checks.append({'name':'automation_health_errors_present','status':'ok','errors':len(errs)})

res={'generated_at':dt.datetime.now().isoformat(timespec='seconds'),'checks':checks,'violations':viol}
out.write_text(json.dumps(res,indent=2))
print(out)

if viol and SEND.exists():
    msg='⚠️ Routing compliance warning:\n' + '\n'.join('- '+v for v in viol)
    subprocess.run([str(SEND),'8334496229',msg],check=False)
