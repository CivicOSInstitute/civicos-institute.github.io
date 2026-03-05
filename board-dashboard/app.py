#!/usr/bin/env python3
from flask import Flask, render_template, request, abort, redirect, url_for, send_from_directory, make_response
from flask_cors import CORS
from pathlib import Path
import json, os, re
from datetime import datetime
from io import BytesIO
from urllib.parse import urlparse

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

app = Flask(__name__)
CORS(app)

ROOT = Path('/app') if Path('/app').exists() else Path(__file__).parent
DATA = ROOT / 'data'  # mission-control shared data (finance/incidents)
BOARD_DATA = Path('/app/board-data') if Path('/app/board-data').exists() else ROOT / 'data'  # board-dashboard managed data
DOCS_DIR = ROOT / 'documents'
RECORDINGS_DIR = ROOT / 'recordings'

STANDARD_AGENDA_ITEMS = [
    'Call to Order',
    'Approval of Prior Minutes',
    'Financial Update',
    'Program Update',
    'Risk/Security Update',
    'New Business',
    'Action Items',
    'Adjournment',
]

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


def _news_date_label(item):
    for key in ('date', 'published', 'publishedAt', 'pubDate'):
        value = item.get(key)
        if value:
            try:
                iso_value = str(value).replace('Z', '+00:00')
                return datetime.fromisoformat(iso_value).strftime('%Y-%m-%d')
            except Exception:
                return str(value)[:10]

    url = item.get('url') or ''
    m = re.search(r'/(20\d{2})/(\d{2})/(\d{2})/', url)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return 'Date unavailable'


def news_items():
    p = Path('/app/website-news/news.json') if Path('/app/website-news/news.json').exists() else Path('/Users/AI-OPS/.openclaw/workspace/website-news/news.json')
    j = read_json(p, {'stories': []})
    raw_items = j.get('stories') or j.get('news') or []

    cleaned = []
    for item in raw_items:
        title = (item.get('title') or item.get('headline') or '').strip()
        url = (item.get('url') or '').strip()
        source = (item.get('source') or '').strip()
        if not source and url:
            source = urlparse(url).netloc.replace('www.', '')
        if not title or not url:
            continue

        cleaned.append({
            'headline': title,
            'source': source or 'Unknown source',
            'date': _news_date_label(item),
            'url': url,
        })

    return cleaned[:12]


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


def build_agenda_pdf(role, custom_items):
    buffer = BytesIO()
    filename_stamp = datetime.now().strftime('%Y%m%d-%H%M%S')

    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title='CivicOS Next Meeting Agenda',
    )

    styles = getSampleStyleSheet()
    story = [
        Paragraph('CivicOS Institute — Next Meeting Agenda', styles['Title']),
        Paragraph(f'Generated: {datetime.now().strftime("%Y-%m-%d %I:%M %p")}', styles['Normal']),
        Paragraph(f'Requested by role: {role}', styles['Normal']),
        Spacer(1, 0.25 * inch),
        Paragraph('Standard Agenda Items', styles['Heading2']),
    ]

    for idx, item in enumerate(STANDARD_AGENDA_ITEMS, start=1):
        story.append(Paragraph(f'{idx}. {item}', styles['Normal']))

    story.extend([
        Spacer(1, 0.2 * inch),
        Paragraph('Submitted Agenda Items', styles['Heading2']),
    ])

    if custom_items:
        for idx, item in enumerate(custom_items, start=1):
            line = f"{idx}. {item.get('title', 'Untitled')} (Owner: {item.get('owner', 'TBD')}, Priority: {item.get('priority', 'Medium')})"
            story.append(Paragraph(line, styles['Normal']))
            notes = (item.get('notes') or '').strip()
            meta = f"Submitted by: {item.get('submitted_by', 'unknown')} • Created: {item.get('created_at', 'n/a')}"
            story.append(Paragraph(meta, styles['Italic']))
            if notes:
                story.append(Paragraph(f'Notes: {notes}', styles['Normal']))
            story.append(Spacer(1, 0.1 * inch))
    else:
        story.append(Paragraph('No submitted agenda items.', styles['Normal']))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename="civicos-next-meeting-agenda-{filename_stamp}.pdf"'
    return response


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
        standard_agenda_items=STANDARD_AGENDA_ITEMS,
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


@app.get('/agenda/export.pdf')
def export_agenda_pdf():
    role = auth_role()
    if not role:
        abort(401)
    return build_agenda_pdf(role=role, custom_items=agenda_items())


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
