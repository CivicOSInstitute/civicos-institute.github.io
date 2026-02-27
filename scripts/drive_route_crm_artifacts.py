#!/usr/bin/env python3
import json, subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path('/Users/AI-OPS/.openclaw/workspace')
CRM_JSON = ROOT / 'generated' / 'crm' / 'crm_email_sync_latest.json'
CRM_MD = ROOT / 'generated' / 'crm' / 'crm_email_sync_latest.md'
DRIVE_STATE = ROOT / 'generated' / 'drive' / 'routing_state.json'
BOARD_NOTE = ROOT / 'generated' / 'crm' / 'board_ready_decision_log.md'
ACCOUNT = 'ncerbone@civicos-institute.org'

DRIVE_STATE.parent.mkdir(parents=True, exist_ok=True)


def run(args):
    p = subprocess.run(args, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout).strip())
    return p.stdout.strip()


def ls(parent='root'):
    out = run(['gog','drive','ls','--account',ACCOUNT,'--parent',parent,'--max','200','--json'])
    if not out:
        return []
    j = json.loads(out)
    return j.get('files', [])


def ensure_folder(name, parent='root'):
    for f in ls(parent):
        if f.get('name') == name and f.get('mimeType') == 'application/vnd.google-apps.folder':
            return f['id']
    out = run(['gog','drive','mkdir',name,'--account',ACCOUNT,'--parent',parent,'--json'])
    j = json.loads(out)
    if 'folder' in j:
        return j['folder']['id']
    if 'id' in j:
        return j['id']
    raise KeyError('folder id not found in mkdir response')


def upload(path, parent, name=None):
    cmd=['gog','drive','upload',str(path),'--account',ACCOUNT,'--parent',parent,'--json']
    if name:
        cmd.extend(['--name',name])
    out=run(cmd)
    j=json.loads(out)
    return j.get('file', j)

# Ensure schema
root_board = ensure_folder('Board-Packages')
month = datetime.now().strftime('%Y-%m')
month_id = ensure_folder(month, root_board)
ops_id = ensure_folder('Ops-Reports')
dec_id = ensure_folder('Decision-Logs')

uploads=[]
ts = datetime.now().strftime('%Y%m%d-%H%M%S')

# Route crm sync artifacts to Ops-Reports
for p in [CRM_JSON, CRM_MD]:
    if p.exists():
        up = upload(p, ops_id, name=f"{p.stem}_{ts}{p.suffix}")
        uploads.append({'type':'ops_report','name':up.get('name'),'id':up.get('id')})

# Board-ready flag handling to Decision-Logs
board_count = 0
if CRM_JSON.exists():
    data = json.loads(CRM_JSON.read_text())
    board_count = int(data.get('board_ready',0))

if board_count > 0:
    note = f"""# [Board-ready] CRM interaction flag summary\n\nDate: {datetime.now().isoformat()}\n\n- Source: crm_email_sync_latest.json\n- board_ready_flagged: {board_count}\n- Rule: interaction flagged when capacity_giving or grant_program present\n\nAction: Review interactions in CRM and include in next board package digest.\n"""
    BOARD_NOTE.write_text(note, encoding='utf-8')
    up = upload(BOARD_NOTE, dec_id, name=f"board_ready_crm_flags_{ts}.md")
    uploads.append({'type':'decision_log','name':up.get('name'),'id':up.get('id')})

state={
  'generated_at': datetime.now().isoformat(),
  'folders': {
    'Board-Packages': root_board,
    f'Board-Packages/{month}': month_id,
    'Ops-Reports': ops_id,
    'Decision-Logs': dec_id,
  },
  'board_ready_count': board_count,
  'uploads': uploads,
}
DRIVE_STATE.write_text(json.dumps(state, indent=2), encoding='utf-8')
print(DRIVE_STATE)
