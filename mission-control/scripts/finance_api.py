#!/usr/bin/env python3
from flask import Flask, request, jsonify, send_from_directory
from pathlib import Path
import sqlite3
from werkzeug.utils import secure_filename
from datetime import datetime
import subprocess
import json
import re

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data' / 'finance.db'
ATTACH = ROOT / 'data' / 'attachments'
ATTACH.mkdir(parents=True, exist_ok=True)
SCAN_STATUS = ROOT / 'data' / 'scan-status.json'

ALLOWED = {'.jpg', '.jpeg', '.png', '.webp', '.pdf'}

app = Flask(__name__)

@app.after_request
def add_cors(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    resp.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
    return resp


def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_category(conn, name, type_):
    row = conn.execute("SELECT id FROM categories WHERE lower(name)=lower(?) LIMIT 1", (name,)).fetchone()
    if row:
        return row['id']
    cur = conn.execute("INSERT INTO categories(name,type,description) VALUES(?,?,?)", (name, type_, 'manual entry'))
    return cur.lastrowid


@app.get('/api/finance/entries')
def list_entries():
    conn = get_conn()
    rows = conn.execute("""
        SELECT t.id,t.date,t.description,t.amount,t.type,t.vendor,t.notes,t.receipt_path,
               c.name as category_name
        FROM transactions t
        LEFT JOIN categories c ON c.id=t.category_id
        ORDER BY t.date DESC, t.id DESC
        LIMIT 100
    """).fetchall()
    items = []
    for r in rows:
        d = dict(r)
        if d.get('receipt_path'):
            d['attachment_url'] = f"http://localhost:8876/api/finance/attachment/{Path(d['receipt_path']).name}"
        items.append(d)
    return jsonify({"items": items})


@app.route('/api/finance/manual-entry', methods=['POST', 'OPTIONS'])
def manual_entry():
    if request.method == 'OPTIONS':
        return ('', 204)
    form = request.form
    date = form.get('date')
    type_ = form.get('type', 'expense')
    amount = float(form.get('amount', '0') or 0)
    category = form.get('category', 'Other')
    vendor = form.get('vendor', '')
    description = form.get('description', '')
    notes = form.get('notes', '')

    if not date or type_ not in ('income', 'expense') or amount < 0 or not description:
        return ('invalid payload', 400)

    receipt_path = None
    f = request.files.get('attachment')
    if f and f.filename:
        ext = Path(f.filename).suffix.lower()
        if ext not in ALLOWED:
            return ('invalid attachment type', 400)
        fname = secure_filename(f"{datetime.now().strftime('%Y%m%d-%H%M%S')}_{f.filename}")
        out = ATTACH / fname
        f.save(out)
        receipt_path = str(out)

    conn = get_conn()
    cat_id = ensure_category(conn, category, type_)
    cur = conn.execute(
        """INSERT INTO transactions(date,description,amount,type,category_id,vendor,notes,receipt_path)
           VALUES(?,?,?,?,?,?,?,?)""",
        (date, description, amount, type_, cat_id, vendor, notes, receipt_path)
    )
    conn.commit()
    return jsonify({"ok": True, "id": cur.lastrowid})


@app.route('/api/finance/entry/<int:entry_id>', methods=['PUT', 'DELETE', 'OPTIONS'])
def entry_update_delete(entry_id):
    if request.method == 'OPTIONS':
        return ('', 204)
    conn = get_conn()
    if request.method == 'DELETE':
        conn.execute('DELETE FROM transactions WHERE id=?', (entry_id,))
        conn.commit()
        return jsonify({'ok': True})

    form = request.form
    date = form.get('date')
    type_ = form.get('type', 'expense')
    amount = float(form.get('amount', '0') or 0)
    category = form.get('category', 'Other')
    vendor = form.get('vendor', '')
    description = form.get('description', '')
    notes = form.get('notes', '')

    if not date or type_ not in ('income', 'expense') or amount < 0 or not description:
        return ('invalid payload', 400)

    row = conn.execute('SELECT receipt_path FROM transactions WHERE id=?', (entry_id,)).fetchone()
    receipt_path = row['receipt_path'] if row else None

    f = request.files.get('attachment')
    if f and f.filename:
        ext = Path(f.filename).suffix.lower()
        if ext not in ALLOWED:
            return ('invalid attachment type', 400)
        fname = secure_filename(f"{datetime.now().strftime('%Y%m%d-%H%M%S')}_{f.filename}")
        out = ATTACH / fname
        f.save(out)
        receipt_path = str(out)

    cat_id = ensure_category(conn, category, type_)
    conn.execute("""
        UPDATE transactions
        SET date=?, description=?, amount=?, type=?, category_id=?, vendor=?, notes=?, receipt_path=?
        WHERE id=?
    """, (date, description, amount, type_, cat_id, vendor, notes, receipt_path, entry_id))
    conn.commit()
    return jsonify({'ok': True, 'id': entry_id})


@app.post('/api/finance/invoice/<int:invoice_id>/paid')
def invoice_mark_paid(invoice_id):
    conn = get_conn()
    conn.execute("UPDATE invoices SET status='paid' WHERE id=?", (invoice_id,))
    conn.commit()
    return jsonify({'ok': True})


@app.delete('/api/finance/invoice/<int:invoice_id>')
def invoice_delete(invoice_id):
    conn = get_conn()
    conn.execute('DELETE FROM invoices WHERE id=?', (invoice_id,))
    conn.commit()
    return jsonify({'ok': True})


@app.get('/api/finance/attachment/<name>')
def attachment(name):
    return send_from_directory(ATTACH, name, as_attachment=False)


@app.post('/api/finance/scan-email')
def scan_email_start():
    try:
        payload = request.get_json(silent=True) or {}
        scope = payload.get('scope', 'unread')
        account = payload.get('account', 'nick')
        SCAN_STATUS.write_text(json.dumps({"state": "starting", "current": "launching scanner", "progress": 0, "scope": scope, "account": account}))
        logf = open(ROOT / 'scan_email.log', 'a')
        env = dict(**__import__('os').environ)
        env['SCAN_SCOPE'] = scope
        env['SCAN_ACCOUNT'] = account
        proc = subprocess.Popen([
            str(ROOT / '.venv' / 'bin' / 'python') if (ROOT / '.venv' / 'bin' / 'python').exists() else 'python3',
            str(ROOT / 'scripts' / 'invoice_scanner.py')
        ], cwd=str(ROOT), stdout=logf, stderr=logf, env=env)
        return jsonify({"ok": True, "pid": proc.pid, "scope": scope, "account": account})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.get('/api/finance/scan-status')
def scan_status():
    if SCAN_STATUS.exists():
        try:
            return jsonify(json.loads(SCAN_STATUS.read_text()))
        except Exception:
            pass
    return jsonify({"state": "idle", "current": "Scan idle", "progress": 0})


@app.post('/api/council/send')
def council_send():
    payload = request.get_json(silent=True) or {}
    prompt = (payload.get('prompt') or '').strip()
    if not prompt:
        return jsonify({'ok': False, 'error': 'prompt required'}), 400
    try:
        council_msg = (
            "Convene the council-of-advisors skill now. "
            "This must go through the full council process with seat perspectives and Burt synthesis. "
            "Do not answer as a single main-model response.\n\n"
            f"{prompt}"
        )

        logf = open(ROOT / 'council_send.log', 'a')
        proc = subprocess.Popen(
            ['openclaw', 'agent', '--agent', 'main', '--message', council_msg, '--json'],
            stdout=logf,
            stderr=logf,
            cwd=str(ROOT)
        )
        return jsonify({'ok': True, 'queued': True, 'pid': proc.pid, 'mode': 'full_council'})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.get('/api/router/last10')
def router_last10():
    def classify(reason: str) -> str:
        r = (reason or '').lower()
        if any(k in r for k in ['email', 'inbox', 'gmail']): return 'Email'
        if any(k in r for k in ['coding', 'code', 'engineer', 'debug']): return 'Coding'
        if any(k in r for k in ['writing', 'narrative', 'content']): return 'Writing'
        if any(k in r for k in ['strategy', 'business', 'executive']): return 'Strategy'
        if any(k in r for k in ['analysis', 'q&a', 'philosopher', 'reasoning']): return 'Analysis/Q&A'
        if any(k in r for k in ['multimodal', 'vision', 'ocr']): return 'Vision/OCR'
        if any(k in r for k in ['triage', 'status', 'summary', 'rapid']): return 'Triage/Status'
        if any(k in r for k in ['contrarian', 'challenge']): return 'Contrarian Review'
        return 'General'

    logs = [Path('/Users/AI-OPS/.openclaw/logs/autonomous-agent.log'), Path('/Users/AI-OPS/.openclaw/logs/router-queue.log')]
    telemetry = Path('/Users/AI-OPS/.openclaw/workspace/data/telemetry/router_telemetry.jsonl')
    entries = []

    # Prefer structured telemetry first
    if telemetry.exists():
        for line in telemetry.read_text(errors='ignore').splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            ts = r.get('timestamp') or ''
            route = (r.get('route') or '').lower()
            model = r.get('model') or r.get('model_used') or ''
            reason = r.get('reason') or r.get('category') or ''
            if ts and model:
                entries.append({
                    'time': ts,
                    'request_type': classify(reason),
                    'model': model,
                    'route': route or ('local' if ':' in model else 'escalate'),
                    'reason': reason
                })

    # Backfill from legacy logs
    for p in logs:
        if not p.exists():
            continue
        for line in p.read_text(errors='ignore').splitlines():
            m = re.search(r'\[(.*?)\].*?\[ROUTING\].*?(Decision: (\w+) \| Model: ([^|]+) \| Reason: (.*)|→ (local|escalate) \| ([^|]+) \| (.*))', line)
            if m:
                ts = m.group(1)
                route = m.group(3) or m.group(6) or ''
                model = (m.group(4) or m.group(7) or '').strip()
                reason = (m.group(5) or m.group(8) or '').strip()
                entries.append({
                    'time': ts,
                    'request_type': classify(reason),
                    'model': model,
                    'route': route.lower() if route else ('local' if ':' in model else 'escalate'),
                    'reason': reason
                })

    seen = set()
    uniq = []
    for e in sorted(entries, key=lambda x: x.get('time', '')):
        k = (e.get('time'), e.get('model'), e.get('route'), e.get('reason'))
        if k in seen:
            continue
        seen.add(k)
        uniq.append(e)

    return jsonify({'items': uniq[-10:]})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8876, debug=False)
