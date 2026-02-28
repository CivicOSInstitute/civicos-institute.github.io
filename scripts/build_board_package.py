#!/usr/bin/env python3
import json
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path('/Users/AI-OPS/.openclaw/workspace')
SIGNALS_MD = ROOT / 'generated' / 'signals' / 'decision_log_board_ready.md'
GA4_MD = ROOT / 'generated' / 'analytics' / 'ga4_daily_latest.md'
CRM_JSON = ROOT / 'generated' / 'crm' / 'crm_email_sync_latest.json'
CRM_REVIEW = ROOT / 'generated' / 'crm' / 'manual_review_contacts.jsonl'
OUT_DIR = ROOT / 'generated' / 'board'
OUT_DIR.mkdir(parents=True, exist_ok=True)

ACCOUNT = 'ncerbone@civicos-institute.org'


def run(args):
    p = subprocess.run(args, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout).strip())
    return p.stdout.strip()


def drive_ls(parent='root'):
    out = run(['gog', 'drive', 'ls', '--account', ACCOUNT, '--parent', parent, '--max', '200', '--json'])
    if not out:
        return []
    return json.loads(out).get('files', [])


def ensure_folder(name, parent='root'):
    for f in drive_ls(parent):
        if f.get('name') == name and f.get('mimeType') == 'application/vnd.google-apps.folder':
            return f['id']
    out = run(['gog', 'drive', 'mkdir', name, '--account', ACCOUNT, '--parent', parent, '--json'])
    j = json.loads(out)
    return j.get('folder', {}).get('id') or j.get('id')


def drive_upload(path, parent, name=None):
    cmd = ['gog', 'drive', 'upload', str(path), '--account', ACCOUNT, '--parent', parent, '--json']
    if name:
        cmd.extend(['--name', name])
    out = run(cmd)
    j = json.loads(out)
    return j.get('file', j)


def parse_board_ready(md_text):
    items = []
    parts = re.split(r'\n## \[Board-ready\] ', md_text)
    for p in parts[1:]:
        lines = p.strip().splitlines()
        headline = lines[0].strip()
        data = {
            'headline': headline,
            'source': '',
            'related_video': '',
            'why': '',
            'risk': '',
            'next_step': ''
        }
        for ln in lines[1:]:
            if ln.startswith('Source: '):
                data['source'] = ln.replace('Source: ', '').strip()
            elif ln.startswith('Related video: '):
                data['related_video'] = ln.replace('Related video: ', '').strip()
            elif ln.startswith('Why it matters: '):
                data['why'] = ln.replace('Why it matters: ', '').strip()
            elif ln.startswith('Risk/Opportunity: '):
                data['risk'] = ln.replace('Risk/Opportunity: ', '').strip()
            elif ln.startswith('Next step: '):
                data['next_step'] = ln.replace('Next step: ', '').strip()
        items.append(data)
    return items


def crm_summary():
    now = datetime.now()
    since = now - timedelta(days=7)
    matched = []

    if CRM_REVIEW.exists() and CRM_REVIEW.stat().st_size > 0:
        for raw in CRM_REVIEW.read_text(encoding='utf-8', errors='ignore').splitlines():
            try:
                obj = json.loads(raw)
            except Exception:
                continue
            t = obj.get('timestamp') or obj.get('date')
            try:
                dt = datetime.fromisoformat(t.replace('Z', '+00:00')).replace(tzinfo=None) if t else now
            except Exception:
                dt = now
            blob = json.dumps(obj).lower()
            if dt >= since and ('grant' in blob or 'capacity_giving' in blob):
                matched.append(obj)

    latest = {}
    if CRM_JSON.exists():
        try:
            latest = json.loads(CRM_JSON.read_text())
        except Exception:
            latest = {}

    return {
        'count': len(matched),
        'items': matched[:10],
        'latest': latest
    }


def read_ga4_summary():
    if not GA4_MD.exists():
        return 'GA4 summary unavailable.'
    return GA4_MD.read_text(encoding='utf-8', errors='ignore').strip()


def build_brief(report_date):
    src = SIGNALS_MD.read_text(encoding='utf-8', errors='ignore') if SIGNALS_MD.exists() else ''
    signals = parse_board_ready(src)
    crm = crm_summary()
    ga4 = read_ga4_summary()

    exec_bullets = []
    exec_bullets.append(f"{len(signals)} board-ready governance signals identified this cycle.")
    exec_bullets.append(f"CRM flagged interactions (grant/capacity_giving) in past 7 days: {crm['count']}.")
    exec_bullets.append("Website analytics snapshot included from latest GA4 daily pull.")

    lines = [
        f"# CivicOS Board Brief — {report_date}",
        "",
        "## Executive Summary",
    ]
    for b in exec_bullets[:3]:
        lines.append(f"- {b}")

    lines += ["", "## Signal Intelligence"]
    if not signals:
        lines.append("- No board-ready items found.")
    else:
        for s in signals:
            lines += [
                f"### {s['headline']}",
                f"- Source: {s['source']}",
                f"- Related video: {s['related_video']}",
                f"- Why it matters: {s['why']}",
                f"- Risk/Opportunity: {s['risk']}",
                f"- Next step: {s['next_step']}",
                ""
            ]

    lines += ["## Stakeholder Activity (past 7 days)"]
    if crm['count'] == 0:
        lines.append("- No grant/capacity_giving flagged CRM interactions recorded in the past 7 days.")
    else:
        for i, item in enumerate(crm['items'], 1):
            lines.append(f"- {i}. {json.dumps(item, ensure_ascii=False)}")
    lines.append(f"- CRM sync stats: processed={crm['latest'].get('processed', 0)}, matched={crm['latest'].get('matched', 0)}, manual_review={crm['latest'].get('manual_review', 0)}")

    lines += ["", "## Website & Reach (GA4 summary)", ga4, "", "## Recommended Actions"]

    consolidated = []
    for s in signals:
        nxt = s.get('next_step', '').strip()
        if nxt:
            consolidated.append(nxt)
    if not consolidated:
        consolidated = ["Assign owner to review latest signals and confirm action plan before next board check-in."]

    for c in dict.fromkeys(consolidated):
        lines.append(f"- {c}")

    out_path = OUT_DIR / f"board_brief_{report_date}.md"
    out_path.write_text('\n'.join(lines), encoding='utf-8')
    return out_path


def main():
    report_date = datetime.now().strftime('%Y-%m-%d')
    out_path = build_brief(report_date)

    board_root = ensure_folder('Board-Packages')
    month_folder = ensure_folder('2026-02', board_root)
    up = drive_upload(out_path, month_folder, name=out_path.name)

    link = f"https://drive.google.com/file/d/{up.get('id')}/view"
    result = {
        'brief_path': str(out_path),
        'drive_file_id': up.get('id'),
        'drive_name': up.get('name'),
        'drive_link': link,
    }
    print(json.dumps(result))


if __name__ == '__main__':
    main()
