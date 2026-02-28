#!/usr/bin/env python3
import json
import re
import os
import shutil
import tempfile
import subprocess
import httpx
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path('/Users/AI-OPS/.openclaw/workspace')
SIGNALS_MD = ROOT / 'generated' / 'signals' / 'decision_log_board_ready.md'
GA4_MD = ROOT / 'generated' / 'analytics' / 'ga4_daily_latest.md'
CRM_JSON = ROOT / 'generated' / 'crm' / 'crm_email_sync_latest.json'
CRM_REVIEW = ROOT / 'generated' / 'crm' / 'manual_review_contacts.jsonl'
TEMPLATE_JS = ROOT / 'scripts' / 'board_brief_template.js'
OUT_DIR = ROOT / 'generated' / 'board'
OUT_DIR.mkdir(parents=True, exist_ok=True)
ACCOUNT = 'ncerbone@civicos-institute.org'
LLAMA_URL = 'http://localhost:18080/v1/chat/completions'
OLLAMA_URL = 'http://localhost:11434/api/chat'
TIMEOUT = 180.0
TEMPLATE_OUTPUT = Path('/sessions/serene-zealous-fermat/mnt/outputs/board_brief_2026-02-27.docx')


def run(args, env=None):
    p = subprocess.run(args, capture_output=True, text=True, env=env)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout).strip())
    return p.stdout.strip()


def drive_ls(parent='root'):
    out = run(['gog', 'drive', 'ls', '--account', ACCOUNT, '--parent', parent, '--max', '200', '--json'])
    return json.loads(out).get('files', []) if out else []


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
        h = lines[0].strip()
        d = {'headline': h, 'source': '', 'url': '', 'video': '', 'why': '', 'risk': '', 'nextStep': ''}
        for ln in lines[1:]:
            if ln.startswith('Source: '):
                src = ln.replace('Source: ', '').strip()
                if ' — ' in src:
                    pub, url = src.split(' — ', 1)
                    d['source'] = pub.strip()
                    d['url'] = url.strip()
                else:
                    d['source'] = src
            elif ln.startswith('Related video: '):
                d['video'] = ln.replace('Related video: ', '').strip()
            elif ln.startswith('Why it matters: '):
                d['why'] = ln.replace('Why it matters: ', '').strip()
            elif ln.startswith('Risk/Opportunity: '):
                d['risk'] = ln.replace('Risk/Opportunity: ', '').strip()
            elif ln.startswith('Next step: '):
                d['nextStep'] = ln.replace('Next step: ', '').strip()
        items.append(d)
    return items


def crm_summary_bullets():
    now = datetime.now()
    since = now - timedelta(days=7)
    flagged = 0
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
                flagged += 1
    latest = {}
    if CRM_JSON.exists():
        try:
            latest = json.loads(CRM_JSON.read_text())
        except Exception:
            latest = {}
    return [
        f"CRM flagged grant/capacity_giving interactions in past 7 days: {flagged}",
        f"CRM sync stats: processed={latest.get('processed',0)}, matched={latest.get('matched',0)}, manual_review={latest.get('manual_review',0)}",
    ]


def ga4_summary_bullets():
    if not GA4_MD.exists():
        return ["GA4 summary unavailable"]
    lines = [x.strip() for x in GA4_MD.read_text(encoding='utf-8', errors='ignore').splitlines() if x.strip().startswith('- ')]
    return [x[2:] for x in lines[:8]]


def actions_rows(signals):
    rows = []
    seen = set()
    for s in signals:
        nxt = s.get('nextStep', '').strip()
        if nxt and nxt not in seen:
            seen.add(nxt)
            rows.append([nxt, s.get('headline', '')[:60], 'HIGH'])
    if not rows:
        rows.append(["Assign owner to review current board-ready signals.", "Board-ready queue", "MEDIUM"])
    return rows


def build_executive_summary(signals, crm, ga4):
    prompt = (
        "You are preparing a board brief for CivicOS Institute. "
        "Return ONLY valid JSON as: {\"executiveSummary\":[\"bullet 1\",\"bullet 2\",\"bullet 3\"]}. "
        "Each bullet must be concise, operational, and grounded in provided inputs."
        f"\nSignals: {json.dumps(signals[:5], ensure_ascii=False)}"
        f"\nCRM: {json.dumps(crm, ensure_ascii=False)}"
        f"\nGA4: {json.dumps(ga4, ensure_ascii=False)}"
    )

    try:
        resp = httpx.post(
            LLAMA_URL,
            timeout=TIMEOUT,
            json={
                "model": "qwen",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 250,
                "temperature": 0.3,
            },
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.S).strip()
        parsed = json.loads(content)
        bullets = parsed.get('executiveSummary', [])
        if isinstance(bullets, list) and bullets:
            return [str(x).strip() for x in bullets[:5]], 'qwen3.5-local'
    except Exception:
        pass

    try:
        resp = httpx.post(
            OLLAMA_URL,
            timeout=TIMEOUT,
            json={
                "model": "qwen3:14b",
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
        )
        resp.raise_for_status()
        content = resp.json().get('message', {}).get('content', '').strip()
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.S).strip()
        parsed = json.loads(content)
        bullets = parsed.get('executiveSummary', [])
        if isinstance(bullets, list) and bullets:
            return [str(x).strip() for x in bullets[:5]], 'qwen3:14b'
    except Exception:
        pass

    return [
        "Board-ready signal review completed; prioritize the top governance-relevant developments.",
        "CRM and analytics pipelines are operational; monitor for fresh stakeholder and traffic deltas.",
        "Action queue should focus on highest-impact leadership decisions this cycle."
    ], 'fallback-static'


def inject_data_and_run(report_date):
    if not TEMPLATE_JS.exists():
        raise RuntimeError(f"Missing template: {TEMPLATE_JS}")

    md = SIGNALS_MD.read_text(encoding='utf-8', errors='ignore') if SIGNALS_MD.exists() else ''
    signals = parse_board_ready(md)
    crm = crm_summary_bullets()
    ga4 = ga4_summary_bullets()
    actions = actions_rows(signals)
    executive_summary, model_used = build_executive_summary(signals, crm, ga4)

    date_label = datetime.strptime(report_date, '%Y-%m-%d').strftime('%B %-d, %Y')
    out_docx = OUT_DIR / f'board_brief_{report_date}.docx'

    data_block = (
        f"const DATE = {json.dumps(date_label)};\n"
        f"const signals = {json.dumps(signals, ensure_ascii=False, indent=2)};\n"
        f"const crmSummary = {json.dumps(crm, ensure_ascii=False, indent=2)};\n"
        f"const ga4Summary = {json.dumps(ga4, ensure_ascii=False, indent=2)};\n"
        f"const actionsTable = {json.dumps(actions, ensure_ascii=False, indent=2)};\n"
        f"const executiveSummary = {json.dumps(executive_summary, ensure_ascii=False, indent=2)};\n"
        f"const MODEL_USED = {json.dumps(model_used)};\n"
    )

    original_template = TEMPLATE_JS.read_text(encoding='utf-8', errors='ignore')
    runtime_template = re.sub(r"const DATE\s*=\s*\"[^\"]*\";", data_block, original_template, count=1)

    TEMPLATE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as tf:
        tf.write(runtime_template)
        runtime_js = Path(tf.name)

    env = dict(os.environ)
    env['NODE_PATH'] = '/usr/local/lib/node_modules_global/lib/node_modules'
    try:
        run(['node', str(runtime_js)], env=env)
    finally:
        runtime_js.unlink(missing_ok=True)

    if not TEMPLATE_OUTPUT.exists():
        raise RuntimeError(f"Template output missing: {TEMPLATE_OUTPUT}")

    shutil.copy2(TEMPLATE_OUTPUT, out_docx)
    if not out_docx.exists():
        raise RuntimeError(f"Expected output not found: {out_docx}")
    return out_docx


def main():
    report_date = datetime.now().strftime('%Y-%m-%d')
    docx_path = inject_data_and_run(report_date)

    board_root = ensure_folder('Board-Packages')
    month_folder = ensure_folder(report_date[:7], board_root)
    up = drive_upload(docx_path, month_folder, name=docx_path.name)

    print(json.dumps({
        'brief_docx_path': str(docx_path),
        'drive_docx_file_id': up.get('id'),
        'drive_docx_link': f"https://drive.google.com/file/d/{up.get('id')}/view"
    }))


if __name__ == '__main__':
    main()
