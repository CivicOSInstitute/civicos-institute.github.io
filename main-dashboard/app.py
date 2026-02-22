#!/usr/bin/env python3
"""
CivicOS Main Command Center Dashboard
Aggregates data from all sub-systems
"""

from flask import Flask, render_template, jsonify, request
import sqlite3
import json
from datetime import datetime, date
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
                         grant_deadlines=grant_deadlines,
                         now=datetime.now())

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
            return jsonify({'status': 'success', 'message': 'Message sent to Nick'})
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
