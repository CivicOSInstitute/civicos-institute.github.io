#!/usr/bin/env python3
from flask import Flask, render_template, request, abort, redirect, url_for, send_from_directory
from flask_cors import CORS
from pathlib import Path
import json, os, re
from datetime import datetime

app = Flask(__name__)
CORS(app)

ROOT = Path('/app') if Path('/app').exists() else Path(__file__).parent
DATA = ROOT / 'data'  # mission-control shared data (finance/incidents)
BOARD_DATA = Path('/app/board-data') if Path('/app/board-data').exists() else ROOT / 'data'  # board-dashboard managed data
DOCS_DIR = ROOT / 'documents'
RECORDINGS_DIR = ROOT / 'recordings'

ROLE_KEYS = {
    'provisional': os.getenv('BOARD_KEY_PROVISIONAL', 'provisional-demo-key'),
    'advisory': os.getenv('BOARD_KEY_ADVISORY', 'advisory-demo-key'),
    'board': os.getenv('BOARD_KEY_BOARD', 'board-demo-key'),
}

ROLE_PERMS = {
    'provisional': {'finance': 'summary', 'grants': 'summary', 'news': True, 'incidents': False, 'agenda_submit': False},
    'advisory': {'finance': 'standard', 'grants': 'standard', 'news': True, 'incidents': True, 'agenda_submit': True},
    'board': {'finance': 'full', 'grants': 'full', 'news': True, 'incidents': True, 'agenda_submit': True},
}


def auth_role():
    role = request.args.get('role', '').lower()
    key = request.args.get('key', '')
    if role in ROLE_KEYS and key and key == ROLE_KEYS[role]:
        return role
    return None


def read_json(path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


def finance_snapshot():
    j = read_json(DATA / 'finance-status.json', {})
    monthly = j.get('monthly', {})
    invoices = j.get('invoices', {})
    return {
        'income': float(monthly.get('income', 0) or 0),
        'expenses': float(monthly.get('expenses', 0) or 0),
        'net': float(monthly.get('net', 0) or 0),
        'unpaid_count': int(invoices.get('unpaid_count', 0) or 0),
        'unpaid_total': float(invoices.get('unpaid_total', 0) or 0),
        'updated': j.get('updatedAt')
    }


def grants_snapshot():
    latest = Path('/app/generated/grants/grant-scan-latest.md') if Path('/app/generated/grants/grant-scan-latest.md').exists() else Path('/Users/AI-OPS/.openclaw/workspace/generated/grants/grant-scan-latest.md')
    if not latest.exists():
        return []

    text = latest.read_text(errors='ignore')
    raw = [l.strip('- ').strip() for l in text.splitlines() if l.strip().startswith('- ')]

    cleaned = []
    seen = set()
    for item in raw:
        item = ' '.join(item.split())
        item = re.sub(r'\*\*', '', item)
        if len(item) < 20:
            continue
        key = item.lower().rstrip('.;:')
        if key in seen:
            continue
        if key in {
            'training and exercises',
            'planning and preparedness',
            'public education and outreach',
            'community outreach and education',
            'emergency planning and preparedness'
        }:
            continue
        seen.add(key)
        cleaned.append(item)

    return cleaned[:6]


def news_items():
    p = Path('/app/website-news/news.json') if Path('/app/website-news/news.json').exists() else Path('/Users/AI-OPS/.openclaw/workspace/website-news/news.json')
    j = read_json(p, {'news': []})
    items = j.get('news', [])
    return items[:10]


def incidents():
    p = DATA / 'scan-status.json'
    j = read_json(p, {})
    return [j] if j else []


def governance_index():
    default = {
        'governance': [
            {'title': 'Bylaws', 'summary': 'Current governing bylaws and amendment history.', 'url': '/documents/bylaws.pdf'},
            {'title': 'Charter', 'summary': 'Organizational charter and mission authority.', 'url': '/documents/charter.pdf'},
            {'title': 'Board roster', 'summary': 'Current board members, terms, and officer roles.', 'url': '/documents/board-roster.pdf'},
            {'title': 'Committee structure', 'summary': 'Standing committees, chairs, and responsibilities.', 'url': '/documents/committee-structure.pdf'},
            {'title': 'Conflict-of-interest policy', 'summary': 'Disclosure, recusal, and annual attestation policy.', 'url': '/documents/conflict-of-interest-policy.pdf'}
        ],
        'meetings': [
            {
                'date': '2026-02-21',
                'title': 'Quarterly Governance Review',
                'minutes_url': '/recordings/2026-02-21/minutes.pdf',
                'transcript_url': '/recordings/2026-02-21/transcript.txt',
                'audio_url': '/recordings/2026-02-21/audio.mp3',
                'video_url': '/recordings/2026-02-21/video.mp4'
            },
            {
                'date': '2026-01-17',
                'title': 'Board Operations Sync',
                'minutes_url': '/recordings/2026-01-17/minutes.pdf',
                'transcript_url': '/recordings/2026-01-17/transcript.txt',
                'audio_url': '/recordings/2026-01-17/audio.mp3',
                'video_url': '/recordings/2026-01-17/video.mp4'
            }
        ]
    }
    path = BOARD_DATA / 'governance_index.json'
    if not path.exists():
        write_json(path, default)
        return default
    return read_json(path, default)


def agenda_items():
    path = BOARD_DATA / 'next_agenda.json'
    default = {'items': []}
    if not path.exists():
        write_json(path, default)
        return []
    data = read_json(path, default)
    items = data.get('items', [])
    return sorted(items, key=lambda i: i.get('created_at', ''), reverse=True)


def add_agenda_item(title, owner, priority, notes, submitted_by):
    path = BOARD_DATA / 'next_agenda.json'
    data = read_json(path, {'items': []})
    data.setdefault('items', [])
    data['items'].append({
        'title': title,
        'owner': owner,
        'priority': priority,
        'notes': notes,
        'submitted_by': submitted_by,
        'created_at': datetime.now().isoformat(timespec='seconds')
    })
    write_json(path, data)


@app.route('/')
def home():
    role = auth_role()
    if not role:
        abort(401)

    perms = ROLE_PERMS[role]
    incident_list = incidents()
    incident_latest = incident_list[0] if incident_list else {}
    gov = governance_index()
    agenda = agenda_items()

    return render_template(
        'index.html',
        role=role,
        perms=perms,
        finance=finance_snapshot(),
        grants=grants_snapshot(),
        news=news_items(),
        incidents=incident_list,
        incident_latest=incident_latest,
        governance_links=gov.get('governance', []),
        meetings=gov.get('meetings', []),
        agenda_items=agenda,
        role_key=ROLE_KEYS[role],
        now=datetime.now().isoformat(timespec='seconds')
    )


@app.post('/agenda/submit')
def submit_agenda():
    role = auth_role()
    if not role:
        abort(401)
    perms = ROLE_PERMS[role]
    if not perms.get('agenda_submit'):
        abort(403)

    title = (request.form.get('title') or '').strip()
    owner = (request.form.get('owner') or '').strip()
    priority = (request.form.get('priority') or 'Medium').strip()
    notes = (request.form.get('notes') or '').strip()

    if not title or not owner:
        abort(400)

    if priority not in {'Low', 'Medium', 'High', 'Critical'}:
        priority = 'Medium'

    add_agenda_item(title=title, owner=owner, priority=priority, notes=notes, submitted_by=role)

    return redirect(url_for('home', role=role, key=ROLE_KEYS[role], tab='meetings'))


@app.route('/documents/<path:filename>')
def documents(filename):
    return send_from_directory(DOCS_DIR, filename)


@app.route('/recordings/<path:filename>')
def recordings(filename):
    return send_from_directory(RECORDINGS_DIR, filename)


@app.route('/health')
def health():
    return {'status': 'ok', 'time': datetime.now().isoformat()}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '8788')))