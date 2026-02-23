#!/usr/bin/env python3
"""
CivicOS Main Command Center Dashboard
Aggregates data from all sub-systems
"""

from flask import Flask, render_template, jsonify, request
import sqlite3
import json
from datetime import datetime, date
import csv
from pathlib import Path
import urllib.request
import urllib.error

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Service URLs
SERVICES = {
    'task_tracker': {'url': 'http://localhost:8082', 'port': 8082},
    'crm': {'url': 'http://localhost:8083', 'port': 8083},
    'token_tracker': {'url': 'http://localhost:8081', 'port': 8081},
    'website': {'url': 'https://civicos-institute.org', 'external': True},
    'news_widget': {'url': 'http://localhost:8080', 'port': 8080},
    'searxng': {'url': 'http://100.81.239.69:8080', 'external': True}
}

EBOOK_SCRIPTS = Path('/root/.openclaw/workspace/the_open_source_student_distribution/scripts')
EBOOK_OUTPUT = Path('/root/Desktop/the_open_source_student/launch-output')
REVENUE_CSV = Path('/root/.openclaw/workspace/civicos-revenue-tracker.csv')
EXPENSES_CSV = Path('/root/.openclaw/workspace/civicos-financial-tracker.csv')
DIST_METRICS_JSON = Path('/root/.openclaw/workspace/the_open_source_student_distribution/output/distribution_metrics.json')
YT_SKILL_DIR = Path('/root/.openclaw/workspace/skills/youtube-summarizer')
YT_ARTIFACTS_DIR = YT_SKILL_DIR / 'artifacts'

def check_service(name, config):
    """Check if a service is online."""
    try:
        if config.get('external'):
            response = urllib.request.urlopen(config['url'], timeout=5)
            return 'online' if response.status == 200 else 'offline'
        else:
            response = urllib.request.urlopen(config['url'], timeout=2)
            return 'online' if response.status == 200 else 'offline'
    except:
        return 'offline'

def get_task_stats():
    """Get task statistics from task tracker DB."""
    try:
        db_path = Path("/root/.openclaw/task-tracker/tasks.db")
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT status, COUNT(*) FROM task GROUP BY status")
        stats = dict(cursor.fetchall())
        conn.close()
        
        return {
            'total': sum(stats.values()),
            'in_progress': stats.get('In Progress', 0),
            'blocked': stats.get('Blocked', 0),
            'completed': stats.get('Completed', 0),
            'not_started': stats.get('Not Started', 0)
        }
    except Exception as e:
        print(f"Error getting task stats: {e}")
        return {}

def get_crm_stats():
    """Get CRM statistics."""
    try:
        db_path = Path("/root/.openclaw/civic-crm/crm.db")
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM contact")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM contact WHERE engagement_level IN ('Hot', 'Very Hot')")
        hot = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM contact WHERE contact_type = 'Board Candidate'")
        board = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM contact WHERE contact_type = 'Foundation Contact'")
        foundation = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total': total,
            'hot': hot,
            'board': board,
            'foundation': foundation
        }
    except Exception as e:
        print(f"Error getting CRM stats: {e}")
        return {}

def get_token_stats():
    """Get token usage statistics."""
    try:
        db_path = Path("/root/.openclaw/token-tracker/token_tracker.db")
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Today's spend
        today = date.today().isoformat()
        cursor.execute("SELECT SUM(cost) FROM token_usage WHERE date(timestamp) = ?", (today,))
        today_spend = cursor.fetchone()[0] or 0
        
        # This week
        cursor.execute("SELECT SUM(cost) FROM token_usage WHERE timestamp >= datetime('now', '-7 days')")
        week_spend = cursor.fetchone()[0] or 0
        
        # This month
        cursor.execute("SELECT SUM(cost) FROM token_usage WHERE timestamp >= datetime('now', '-30 days')")
        month_spend = cursor.fetchone()[0] or 0
        
        # Active APIs
        cursor.execute("SELECT COUNT(DISTINCT provider) FROM token_usage WHERE timestamp >= datetime('now', '-7 days')")
        apis = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'today': round(today_spend, 2),
            'week': round(week_spend, 2),
            'month': round(month_spend, 2),
            'apis': apis
        }
    except Exception as e:
        print(f"Error getting token stats: {e}")
        return {'today': 0, 'week': 0, 'month': 0, 'apis': 0}

def get_council_stats():
    """Get advisory council stats from latest report."""
    try:
        reports_dir = Path("/root/.openclaw/advisory-council/reports")
        if not reports_dir.exists():
            return {}
        
        # Get most recent report
        reports = sorted(reports_dir.glob("council_report_*.txt"), reverse=True)
        if not reports:
            return {}
        
        latest = reports[0]
        with open(latest) as f:
            content = f.read()
        
        # Parse counts
        critical = content.count('🚨') + content.count('CRITICAL')
        important = content.count('⚠️') + content.count('IMPORTANT')
        info = content.count('ℹ️') + content.count('INFORMATIONAL')
        
        # Get date from filename
        date_str = latest.stem.replace('council_report_', '')
        
        return {
            'critical': critical,
            'important': important,
            'info': info,
            'last_run': date_str
        }
    except Exception as e:
        print(f"Error getting council stats: {e}")
        return {}

def get_recent_activity():
    """Get recent activity from logs and databases."""
    activities = []
    
    # Recent CRM contacts
    try:
        db_path = Path("/root/.openclaw/civic-crm/crm.db")
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, contact_type, created_date 
            FROM contact 
            ORDER BY created_date DESC LIMIT 5
        """)
        for row in cursor.fetchall():
            activities.append({
                'message': f"Added {row[0]} ({row[1]})",
                'time': row[2]
            })
        conn.close()
    except:
        pass
    
    return activities

def get_gateway_stats():
    """Get OpenClaw Gateway statistics."""
    try:
        import subprocess
        import re
        
        # Try to get version
        result = subprocess.run(['openclaw', 'version'], capture_output=True, text=True, timeout=5)
        version = result.stdout.strip() if result.returncode == 0 else 'Unknown'
        
        # Try to get status
        result = subprocess.run(['openclaw', 'status'], capture_output=True, text=True, timeout=5)
        status_output = result.stdout
        
        # Parse uptime if available
        uptime = 'Unknown'
        if 'uptime' in status_output.lower():
            match = re.search(r'uptime[:\s]+(.+)', status_output, re.IGNORECASE)
            if match:
                uptime = match.group(1).strip()
        
        return {
            'version': version,
            'uptime': uptime,
            'status': 'Running' if result.returncode == 0 else 'Error'
        }
    except:
        return {
            'version': 'Unknown',
            'uptime': 'Unknown',
            'status': 'Unknown'
        }

def get_email_stats():
    """Get email statistics from Himalaya via bridge API."""
    try:
        def check_account(account):
            bridge_url = 'http://host.docker.internal:18080/email/check'
            payload = {
                'account': account
            }
            
            req = urllib.request.Request(
                bridge_url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            response = urllib.request.urlopen(req, timeout=15)
            result = json.loads(response.read().decode('utf-8'))
            
            if result.get('status') == 'success':
                return result.get('unread', 0)
            return 0
        
        nick_unread = check_account('nick')
        burt_unread = check_account('burt')
        
        return {
            'nick_unread': nick_unread,
            'burt_unread': burt_unread,
            'unread': nick_unread + burt_unread
        }
    except Exception as e:
        print(f"Error getting email stats: {e}")
        return {
            'nick_unread': 0,
            'burt_unread': 0,
            'unread': 0
        }

def get_ebook_stats():
    """Get ebook distribution automation stats."""
    try:
        latest_dir = None
        if EBOOK_OUTPUT.exists():
            candidates = [
                p for p in EBOOK_OUTPUT.iterdir()
                if p.is_dir() and p.name[:8].isdigit() and '-' in p.name
            ]
            if candidates:
                latest_dir = sorted(candidates, key=lambda p: p.name, reverse=True)[0]

        def file_size(path):
            return round(path.stat().st_size / 1024, 1) if path.exists() else 0

        data = {
            'pipeline_ready': (EBOOK_SCRIPTS / 'run_all.sh').exists(),
            'latest_build': latest_dir.name if latest_dir else 'None',
            'core_zip_kb': file_size(latest_dir / 'core.zip') if latest_dir else 0,
            'founder_zip_kb': file_size(latest_dir / 'founder.zip') if latest_dir else 0,
            'institution_zip_kb': file_size(latest_dir / 'institution.zip') if latest_dir else 0,
            'checkout_copy': (EBOOK_OUTPUT / 'checkout-copy.md').exists(),
            'launch_content': (EBOOK_OUTPUT / 'launch-content').exists(),
            'output_path': str(latest_dir) if latest_dir else ''
        }
        return data
    except Exception as e:
        print(f"Error getting ebook stats: {e}")
        return {
            'pipeline_ready': False,
            'latest_build': 'Error',
            'core_zip_kb': 0,
            'founder_zip_kb': 0,
            'institution_zip_kb': 0,
            'checkout_copy': False,
            'launch_content': False,
            'output_path': ''
        }

def get_distribution_stats():
    """Get distribution/revenue analytics for ebook operations."""
    stats = {
        'total_revenue': 0.0,
        'units_sold': 0,
        'orders': 0,
        'aov': 0.0,
        'channels': [],
        'last_updated': 'Unknown'
    }

    try:
        if REVENUE_CSV.exists():
            with open(REVENUE_CSV, newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    amount_raw = (row.get('Amount') or '0').replace('$', '').replace(',', '').strip()
                    try:
                        amount = float(amount_raw)
                    except Exception:
                        amount = 0.0
                    category = (row.get('Category') or '').strip().lower()
                    if category == 'revenue':
                        stats['total_revenue'] += amount
                        stats['orders'] += 1 if amount > 0 else 0

            if stats['orders'] > 0:
                stats['aov'] = round(stats['total_revenue'] / stats['orders'], 2)

        if DIST_METRICS_JSON.exists():
            extra = json.loads(DIST_METRICS_JSON.read_text())
            stats['units_sold'] = int(extra.get('units_sold', stats['units_sold']))
            stats['channels'] = extra.get('channels', [])
            stats['last_updated'] = extra.get('last_updated', stats['last_updated'])

        stats['total_revenue'] = round(stats['total_revenue'], 2)
        return stats
    except Exception as e:
        print(f"Error getting distribution stats: {e}")
        return stats


def _parse_amount(raw):
    try:
        s = str(raw or '').replace('$', '').replace(',', '').strip()
        return float(s)
    except Exception:
        return None


def get_finance_stats():
    stats = {
        'revenue_total': 0.0,
        'expense_paid_total': 0.0,
        'expense_pending_total': 0.0,
        'payment_failed_total': 0.0,
        'lemon_revenue': 0.0,
        'amazon_revenue': 0.0,
        'apple_revenue': 0.0,
        'net': 0.0,
        'revenue_rows': 0,
        'expense_rows': 0,
    }

    try:
        if REVENUE_CSV.exists():
            with open(REVENUE_CSV, newline='') as f:
                for row in csv.DictReader(f):
                    amount = _parse_amount(row.get('Amount'))
                    if amount is None:
                        continue
                    if (row.get('Category') or '').strip().lower() == 'revenue':
                        stats['revenue_total'] += amount
                        stats['revenue_rows'] += 1

        if EXPENSES_CSV.exists():
            with open(EXPENSES_CSV, newline='') as f:
                for row in csv.DictReader(f):
                    status = (row.get('Status') or '').strip().upper()
                    amount = _parse_amount(row.get('Amount'))
                    if amount is None:
                        continue
                    # ignore non-financial log rows
                    if (row.get('Type') or '').strip().upper() == 'SCAN_LOG':
                        continue

                    stats['expense_rows'] += 1
                    if status == 'PAID':
                        stats['expense_paid_total'] += amount
                    elif status == 'PENDING':
                        stats['expense_pending_total'] += amount
                    elif status == 'PAYMENT_FAILED':
                        stats['payment_failed_total'] += amount

        if DIST_METRICS_JSON.exists():
            dm = json.loads(DIST_METRICS_JSON.read_text())
            for ch in dm.get('channels', []):
                name = (ch.get('name') or '').lower()
                try:
                    rev = float(ch.get('revenue', 0) or 0)
                except Exception:
                    rev = 0.0
                if name.startswith('lemon squeezy'):
                    stats['lemon_revenue'] = rev
                elif name.startswith('amazon kdp'):
                    stats['amazon_revenue'] = rev
                elif name.startswith('apple books'):
                    stats['apple_revenue'] = rev

        for k in ('revenue_total', 'expense_paid_total', 'expense_pending_total', 'payment_failed_total', 'lemon_revenue', 'amazon_revenue', 'apple_revenue'):
            stats[k] = round(stats[k], 2)
        stats['net'] = round(stats['revenue_total'] - stats['expense_paid_total'], 2)
        return stats
    except Exception as e:
        print(f"Error getting finance stats: {e}")
        return stats


def get_alerts():
    """Generate alerts based on system state."""
    alerts = []
    
    # Check for blocked tasks
    task_stats = get_task_stats()
    if task_stats.get('blocked', 0) > 0:
        alerts.append({
            'type': 'warning',
            'icon': '⚠️',
            'message': f"{task_stats['blocked']} blocked tasks need attention"
        })
    
    # Check CRM for follow-ups
    try:
        db_path = Path("/root/.openclaw/civic-crm/crm.db")
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        today = date.today().isoformat()
        cursor.execute("SELECT COUNT(*) FROM contact WHERE next_follow_up <= ?", (today,))
        followups = cursor.fetchone()[0]
        if followups > 0:
            alerts.append({
                'type': 'warning',
                'icon': '📞',
                'message': f"{followups} follow-ups due today"
            })
        conn.close()
    except:
        pass
    
    return alerts

@app.route('/')
def index():
    """Main dashboard page."""
    # Check all services
    services = {}
    for name, config in SERVICES.items():
        services[name] = {'status': check_service(name, config)}
    
    # Gather stats
    task_stats = get_task_stats()
    crm_stats = get_crm_stats()
    token_stats = get_token_stats()
    council_stats = get_council_stats()
    recent_activity = get_recent_activity()
    alerts = get_alerts()
    gateway_stats = get_gateway_stats()
    email_stats = get_email_stats()
    ebook_stats = get_ebook_stats()
    distribution_stats = get_distribution_stats()
    
    # Calculate grant deadlines
    from datetime import datetime
    knight_deadline = datetime(2026, 3, 1)
    trust_deadline = datetime(2026, 3, 15)
    today = datetime.now()
    grant_deadlines = {
        'knight_days': (knight_deadline - today).days,
        'trust_days': (trust_deadline - today).days
    }
    
    return render_template('index.html',
                         services=services,
                         task_stats=task_stats,
                         crm_stats=crm_stats,
                         token_stats=token_stats,
                         council_stats=council_stats,
                         website_stats={'last_deploy': 'Unknown'},
                         recent_activity=recent_activity,
                         alerts=alerts,
                         gateway_stats=gateway_stats,
                         email_stats=email_stats,
                         ebook_stats=ebook_stats,
                         distribution_stats=distribution_stats,
                         grant_deadlines=grant_deadlines,
                         now=datetime.now())

@app.route('/distribution')
def distribution_dashboard():
    """Expanded ebook distribution analytics page."""
    return render_template('distribution.html',
                           dist=get_distribution_stats(),
                           ebook=get_ebook_stats(),
                           finance=get_finance_stats(),
                           now=datetime.now())

def get_publishing_ops_status():
    status_file = Path('/root/.openclaw/workspace/the_open_source_student_distribution/platforms/PUBLISHING_ACCOUNT_STATUS.json')
    imports_dir = Path('/root/.openclaw/workspace/the_open_source_student_distribution/output/imports')

    data = {
        'amazon': {'account_status': 'unknown', 'listing_status': 'unknown', 'asin': ''},
        'apple': {'account_status': 'unknown', 'listing_status': 'unknown', 'books_id': ''},
        'imports': {
            'amazon_report': (imports_dir / 'amazon_kdp_report.csv').exists(),
            'apple_report': (imports_dir / 'apple_books_report.csv').exists(),
        },
        'readiness_score': 0
    }

    try:
        if status_file.exists():
            raw = json.loads(status_file.read_text())
            a = raw.get('amazon_kdp', {})
            p = raw.get('apple_books', {})
            data['amazon'] = {
                'account_status': a.get('account_status', 'unknown'),
                'listing_status': a.get('listing_status', 'unknown'),
                'asin': a.get('asin', '')
            }
            data['apple'] = {
                'account_status': p.get('account_status', 'unknown'),
                'listing_status': p.get('listing_status', 'unknown'),
                'books_id': p.get('books_id', '')
            }

        score = 0
        if data['amazon']['account_status'] not in ('unknown', 'pending_owner_completion'): score += 25
        if data['apple']['account_status'] not in ('unknown', 'pending_owner_completion'): score += 25
        if data['imports']['amazon_report']: score += 25
        if data['imports']['apple_report']: score += 25
        data['readiness_score'] = score
        return data
    except Exception:
        return data

@app.route('/finance')
def finance_dashboard():
    """Revenue and expenses dashboard."""
    return render_template('finance.html',
                           finance=get_finance_stats(),
                           dist=get_distribution_stats(),
                           now=datetime.now())

@app.route('/publishing-ops')
def publishing_ops_dashboard():
    """Publishing operations status for Amazon/Apple channels."""
    return render_template('publishing_ops.html',
                           ops=get_publishing_ops_status(),
                           now=datetime.now())

@app.route('/api/distribution/stats')
def api_distribution_stats():
    return jsonify(get_distribution_stats())

@app.route('/api/finance/stats')
def api_finance_stats():
    return jsonify(get_finance_stats())

@app.route('/api/publishing-ops/stats')
def api_publishing_ops_stats():
    return jsonify(get_publishing_ops_status())

@app.route('/api/status')
def api_status():
    """API endpoint for service status."""
    services = {}
    for name, config in SERVICES.items():
        services[name] = {'status': check_service(name, config)}
    return jsonify(services)

@app.route('/api/run-council', methods=['POST'])
def run_council():
    """Trigger council analysis."""
    import subprocess
    try:
        subprocess.run(
            ['python3', '/Users/AI-OPS/.openclaw/workspace/advisory-council/council.py'],
            capture_output=True,
            timeout=30
        )
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/restart-gateway', methods=['POST'])
def restart_gateway():
    """Restart OpenClaw Gateway."""
    import subprocess
    import threading
    
    def do_restart():
        """Execute restart after a short delay to allow response to be sent."""
        import time
        time.sleep(2)
        try:
            # Use subprocess.Popen to avoid blocking
            subprocess.Popen(
                ['openclaw', 'gateway', 'restart'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            print(f"Gateway restart error: {e}")
    
    # Start restart in background thread
    restart_thread = threading.Thread(target=do_restart)
    restart_thread.daemon = True
    restart_thread.start()
    
    return jsonify({
        'status': 'success',
        'message': 'Gateway restart initiated. Service will be unavailable for 10-30 seconds.'
    })

@app.route('/api/check-email/<account>', methods=['POST'])
def check_email(account):
    """Check email for specified account via bridge API."""
    if account not in ['nick', 'burt']:
        return jsonify({'status': 'error', 'message': 'Invalid account'}), 400
    
    try:
        # Call bridge API on host
        bridge_url = 'http://host.docker.internal:18080/email/check'
        payload = {
            'account': account
        }
        
        req = urllib.request.Request(
            bridge_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        response = urllib.request.urlopen(req, timeout=20)
        result = json.loads(response.read().decode('utf-8'))
        
        if result.get('status') == 'success':
            return jsonify({
                'status': 'success',
                'unread': result.get('unread', 0),
                'emails': result.get('emails', []),
                'account': account
            })
        else:
            return jsonify({'status': 'error', 'message': result.get('message', 'Unknown error')}), 500
            
    except urllib.error.URLError as e:
        return jsonify({'status': 'error', 'message': f'Bridge API unreachable: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/ebook/run', methods=['POST'])
def run_ebook_pipeline():
    """Run ebook distribution automation pipeline."""
    import subprocess
    try:
        script = EBOOK_SCRIPTS / 'run_all.sh'
        if not script.exists():
            return jsonify({'status': 'error', 'message': 'run_all.sh not found'}), 404

        result = subprocess.run([str(script)], capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            stats = get_ebook_stats()
            return jsonify({
                'status': 'success',
                'message': 'Automation run complete',
                'latest_build': stats.get('latest_build'),
                'output_path': stats.get('output_path')
            })

        return jsonify({'status': 'error', 'message': result.stderr or result.stdout}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/youtube-summarize', methods=['POST'])
def youtube_summarize():
    """Run YouTube summarizer skill scripts for a given URL."""
    import subprocess
    data = request.get_json() or {}
    url = (data.get('url') or '').strip()

    if not url:
        return jsonify({'status': 'error', 'message': 'YouTube URL required'}), 400

    try:
        extract_script = YT_SKILL_DIR / 'scripts' / 'extract_transcript.py'
        summarize_script = YT_SKILL_DIR / 'scripts' / 'summarize_transcript.py'

        if not extract_script.exists() or not summarize_script.exists():
            return jsonify({'status': 'error', 'message': 'youtube-summarizer scripts missing'}), 404

        YT_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        transcript_path = YT_ARTIFACTS_DIR / 'transcript.json'
        summary_path = YT_ARTIFACTS_DIR / 'summary.md'

        p1 = subprocess.run(
            ['python3', str(extract_script), '--url', url, '--out-dir', str(YT_ARTIFACTS_DIR)],
            capture_output=True, text=True, timeout=240
        )
        if p1.returncode != 0:
            return jsonify({'status': 'error', 'message': p1.stderr or p1.stdout or 'Transcript extraction failed'}), 500

        p2 = subprocess.run(
            ['python3', str(summarize_script), '--transcript', str(transcript_path), '--out', str(summary_path)],
            capture_output=True, text=True, timeout=180
        )
        if p2.returncode != 0:
            return jsonify({'status': 'error', 'message': p2.stderr or p2.stdout or 'Summary generation failed'}), 500

        preview = ''
        if summary_path.exists():
            preview = summary_path.read_text()[:1400]

        return jsonify({
            'status': 'success',
            'summary_path': str(summary_path),
            'transcript_path': str(transcript_path),
            'preview': preview
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/read-email/<account>/<email_id>', methods=['POST'])
def read_email(account, email_id):
    """Read a specific email for account via bridge API."""
    if account not in ['nick', 'burt']:
        return jsonify({'status': 'error', 'message': 'Invalid account'}), 400

    try:
        bridge_url = 'http://host.docker.internal:18080/email/read'
        payload = {
            'account': account,
            'id': email_id
        }

        req = urllib.request.Request(
            bridge_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        response = urllib.request.urlopen(req, timeout=30)
        result = json.loads(response.read().decode('utf-8'))

        if result.get('status') == 'success':
            return jsonify(result)
        return jsonify({'status': 'error', 'message': result.get('message', 'Unknown error')}), 500

    except urllib.error.URLError as e:
        return jsonify({'status': 'error', 'message': f'Bridge API unreachable: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/telegram/chats', methods=['GET'])
def telegram_chats():
    """List Telegram chats from bridge API."""
    try:
        bridge_url = 'http://host.docker.internal:18080/telegram/chats'
        response = urllib.request.urlopen(bridge_url, timeout=20)
        result = json.loads(response.read().decode('utf-8'))
        if result.get('status') == 'success':
            return jsonify(result)
        return jsonify({'status': 'error', 'message': result.get('message', 'Unknown error')}), 500
    except urllib.error.URLError as e:
        return jsonify({'status': 'error', 'message': f'Bridge API unreachable: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/telegram/history', methods=['POST'])
def telegram_history():
    """Get recent Telegram messages for selected chat."""
    data = request.get_json() or {}
    chat_id = str(data.get('chat_id', '')).strip()
    limit = int(data.get('limit', 6))

    if not chat_id:
        return jsonify({'status': 'error', 'message': 'chat_id required'}), 400

    try:
        bridge_url = 'http://host.docker.internal:18080/telegram/history'
        payload = {'chat_id': chat_id, 'limit': limit}
        req = urllib.request.Request(
            bridge_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        response = urllib.request.urlopen(req, timeout=20)
        result = json.loads(response.read().decode('utf-8'))
        if result.get('status') == 'success':
            return jsonify(result)
        return jsonify({'status': 'error', 'message': result.get('message', 'Unknown error')}), 500
    except urllib.error.URLError as e:
        return jsonify({'status': 'error', 'message': f'Bridge API unreachable: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/telegram/send', methods=['POST'])
def telegram_send():
    """Send Telegram message via bridge API."""
    from flask import request
    data = request.get_json()
    chat_id = data.get('chat_id', '8334496229')  # Default to Nick
    message = data.get('message', '')
    
    if not message:
        return jsonify({'status': 'error', 'message': 'Message required'}), 400
    
    try:
        # Call bridge API on host
        bridge_url = 'http://host.docker.internal:18080/telegram/send'
        payload = {
            'chat_id': chat_id,
            'message': message
        }
        
        req = urllib.request.Request(
            bridge_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        response = urllib.request.urlopen(req, timeout=20)
        result = json.loads(response.read().decode('utf-8'))
        
        if result.get('status') == 'success':
            return jsonify({'status': 'success', 'message': 'Message sent'})
        else:
            return jsonify({'status': 'error', 'message': result.get('message', 'Unknown error')}), 500
            
    except urllib.error.URLError as e:
        return jsonify({'status': 'error', 'message': f'Bridge API unreachable: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/task/create', methods=['POST'])
def create_task():
    """Create new task."""
    import subprocess
    data = request.get_json()
    title = data.get('title', '')
    assigned_to = data.get('assigned_to', 'Nick')
    due_date = data.get('due_date', '')
    
    if not title:
        return jsonify({'status': 'error', 'message': 'Title required'}), 400
    
    try:
        # Insert into task tracker database
        db_path = Path("/root/.openclaw/task-tracker/tasks.db")
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO task (title, status, assigned_to, due_date, created_date)
            VALUES (?, 'Not Started', ?, ?, ?)
        """, (title, assigned_to, due_date, date.today().isoformat()))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Task created'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/crm/add-contact', methods=['POST'])
def add_contact():
    """Add new CRM contact."""
    import subprocess
    data = request.get_json()
    name = data.get('name', '')
    contact_type = data.get('contact_type', 'Other')
    organization = data.get('organization', '')
    
    if not name:
        return jsonify({'status': 'error', 'message': 'Name required'}), 400
    
    try:
        # Insert into CRM database
        db_path = Path("/root/.openclaw/civic-crm/crm.db")
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO contact (name, organization, contact_type, status, engagement_level, created_date, updated_date)
            VALUES (?, ?, ?, 'New Lead', 'Cold', ?, ?)
        """, (name, organization, contact_type, date.today().isoformat(), date.today().isoformat()))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Contact added'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    print("CivicOS Command Center starting...")
    print("Access: http://100.81.239.69:8090")
    app.run(host='0.0.0.0', port=8090, debug=False)
