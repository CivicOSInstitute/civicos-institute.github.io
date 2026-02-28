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


def format_source_link(source_line):
    # Expected: Publication — URL
    if ' — ' in source_line:
        pub, url = source_line.split(' — ', 1)
        pub = pub.strip()
        url = url.strip()
        if url.startswith('http'):
            return f"[{pub}]({url})"
    return source_line


def format_related_video(video_line):
    # Expected: Channel — Title — URL
    if video_line.lower().startswith('none found'):
        return video_line
    if ' — ' in video_line:
        parts = [p.strip() for p in video_line.split(' — ')]
        if len(parts) >= 3 and parts[-1].startswith('http'):
            channel = parts[0]
            title = ' — '.join(parts[1:-1])
            url = parts[-1]
            return f"{channel} — [{title}]({url})"
    return video_line


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


def render_docx(md_path, docx_path):
    run([
        'pandoc', str(md_path),
        '-o', str(docx_path),
        '--from', 'markdown',
        '--to', 'docx'
    ])


def build_brief(report_date):
    src = SIGNALS_MD.read_text(encoding='utf-8', errors='ignore') if SIGNALS_MD.exists() else ''
    signals = parse_board_ready(src)
    crm = crm_summary()
    ga4 = read_ga4_summary()

    exec_bullets = [
        f"{len(signals)} board-ready governance signals identified this cycle.",
        f"CRM flagged interactions (grant/capacity_giving) in past 7 days: {crm['count']}.",
        "Website analytics snapshot included from latest GA4 daily pull."
    ]

    lines = [
        "# CivicOS Institute",
        "### Board Briefing Packet",
        f"**Date:** {report_date}",
        "",
        "---",
        "",
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
                f"- Source: {format_source_link(s['source'])}",
                f"- Related video: {format_related_video(s['related_video'])}",
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
    lines.append(
        f"- CRM sync stats: processed={crm['latest'].get('processed', 0)}, matched={crm['latest'].get('matched', 0)}, manual_review={crm['latest'].get('manual_review', 0)}"
    )

    lines += ["", "## Website & Reach (GA4 summary)", ga4, "", "## Recommended Actions"]

    consolidated = []
    for s in signals:
        nxt = s.get('next_step', '').strip()
        if nxt:
            consolidated.append(nxt)
    if not consolidated:
        consolidated = ["Assign owner to review latest signals and confirm action plan before next board check-in."]

    unique_actions = list(dict.fromkeys(consolidated))
    lines += [
        "",
        "| Action | Owner | Due Date | Status |",
        "|---|---|---|---|"
    ]
    for a in unique_actions:
        lines.append(f"| {a} | TBD | TBD | Not started |")

    md_path = OUT_DIR / f"board_brief_{report_date}.md"
    docx_path = OUT_DIR / f"board_brief_{report_date}.docx"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    render_docx(md_path, docx_path)
    return md_path, docx_path


def main():
    report_date = datetime.now().strftime('%Y-%m-%d')
    md_path, docx_path = build_brief(report_date)

    board_root = ensure_folder('Board-Packages')
    month_folder = ensure_folder(report_date[:7], board_root)

    up_docx = drive_upload(docx_path, month_folder, name=docx_path.name)
    up_md = drive_upload(md_path, month_folder, name=md_path.name)

    result = {
        'brief_md_path': str(md_path),
        'brief_docx_path': str(docx_path),
        'drive_docx_file_id': up_docx.get('id'),
        'drive_docx_link': f"https://drive.google.com/file/d/{up_docx.get('id')}/view",
        'drive_md_file_id': up_md.get('id'),
        'drive_md_link': f"https://drive.google.com/file/d/{up_md.get('id')}/view",
    }
    print(json.dumps(result))


if __name__ == '__main__':
    main()
