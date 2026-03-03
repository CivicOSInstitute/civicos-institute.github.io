#!/usr/bin/env python3
"""
Invoice Scanner - Automatically detect and extract invoices from email
Integrates with Himalaya email client and Mission Control Finance
"""

import subprocess
import re
import json
import os
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))
from finance_engine import FinanceEngine, DATA_DIR

STATUS_FILE = DATA_DIR / "scan-status.json"

# Invoice detection patterns
INVOICE_KEYWORDS = [
    'invoice', 'bill', 'payment due', 'amount due', 'please pay',
    'outstanding balance', 'payment request', 'billing statement',
    'subscription renewal', 'receipt', 'order confirmation'
]

VENDOR_PATTERNS = [
    r'from:\s*([^\n<]+)',
    r'vendor:\s*([^\n]+)',
    r'billed by:\s*([^\n]+)',
]

AMOUNT_PATTERNS = [
    r'\$([0-9,]+\.\d{2})',
    r'total:\s*\$?([0-9,]+\.\d{2})',
    r'amount:\s*\$?([0-9,]+\.\d{2})',
    r'balance:\s*\$?([0-9,]+\.\d{2})',
]

DATE_PATTERNS = [
    r'due date:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
    r'payment due:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
    r'due:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
]

INVOICE_NUMBER_PATTERNS = [
    r'invoice\s*#?:?\s*([A-Z0-9-]+)',
    r'invoice\s*number:?\s*([A-Z0-9-]+)',
    r'reference:?\s*([A-Z0-9-]{3,})',
]


class InvoiceScanner:
    def __init__(self):
        self.engine = FinanceEngine()
        self.invoices_dir = DATA_DIR / "invoices"
        self.invoices_dir.mkdir(exist_ok=True)
    
    def get_himalaya_emails(self, account: str = "nick", scope: str = "unread", folder: str = "INBOX", limit: int = 50) -> List[Dict]:
        """Fetch emails from Himalaya with account/scope filters."""
        try:
            cmd = ["himalaya", "envelope", "list", "-a", account, "-f", folder, "-s", str(limit), "--output", "json"]
            if scope == "unread":
                cmd += ["not", "flag", "seen"]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            if result.returncode != 0:
                print(f"Himalaya error: {result.stderr}")
                return []

            rows = json.loads(result.stdout or "[]")
            emails = []
            for r in rows:
                emails.append({
                    'id': r.get('id'),
                    'flags': r.get('flags', []),
                    'subject': r.get('subject', ''),
                    'sender': (r.get('from') or {}).get('addr', ''),
                    'date': r.get('date', '')
                })
            return emails
        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []
    
    def get_email_body(self, email_id: str, account: str = "nick", folder: str = "INBOX") -> str:
        """Get full email body by ID."""
        try:
            result = subprocess.run(
                ["himalaya", "message", "read", "-a", account, email_id, "-f", folder],
                capture_output=True, text=True, timeout=45
            )
            return result.stdout if result.returncode == 0 else ""
        except Exception as e:
            print(f"Error reading email {email_id}: {e}")
            return ""
    
    def is_likely_invoice(self, subject: str, body: str) -> bool:
        """Check if email is likely an invoice."""
        text = (subject + " " + body).lower()
        score = sum(1 for kw in INVOICE_KEYWORDS if kw in text)
        return score >= 2  # Need at least 2 keywords
    
    def extract_amount(self, text: str) -> Optional[float]:
        """Extract dollar amount from text."""
        # Look for $X,XXX.XX patterns
        matches = re.findall(r'\$([0-9,]+\.\d{2})', text)
        if matches:
            # Return largest amount (likely total)
            amounts = [float(m.replace(',', '')) for m in matches]
            return max(amounts)
        return None
    
    def extract_vendor(self, sender: str, body: str) -> str:
        """Extract vendor name."""
        # Use sender email display name
        if '<' in sender:
            vendor = sender.split('<')[0].strip()
            return vendor.strip('"')
        return sender
    
    def extract_due_date(self, text: str) -> Optional[str]:
        """Extract due date from text."""
        for pattern in DATE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    # Try to parse various date formats
                    date_str = match.group(1)
                    # Normalize to ISO format
                    for fmt in ['%m/%d/%Y', '%m-%d-%Y', '%d/%m/%Y', '%Y-%m-%d']:
                        try:
                            dt = datetime.strptime(date_str, fmt)
                            return dt.strftime('%Y-%m-%d')
                        except:
                            continue
                except:
                    pass
        return None
    
    def extract_invoice_number(self, text: str) -> Optional[str]:
        """Extract invoice number."""
        for pattern in INVOICE_NUMBER_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def scan_for_invoices(self, limit: int = 50) -> List[Dict]:
        """Scan recent emails for invoices."""
        account = os.getenv('SCAN_ACCOUNT', 'nick')
        scope = os.getenv('SCAN_SCOPE', 'unread')
        print(f"🔍 Scanning last {limit} emails for invoices... account={account} scope={scope}")
        STATUS_FILE.write_text(json.dumps({"state":"running","current":"starting","progress":0,"account":account,"scope":scope}))

        emails = self.get_himalaya_emails(account=account, scope=scope, limit=limit)
        found_invoices = []
        
        # Check which emails we've already processed
        cursor = self.engine.conn.execute(
            "SELECT email_id FROM email_scan_log"
        )
        processed_ids = {row[0] for row in cursor.fetchall()}
        
        total = max(len(emails), 1)
        for idx, email in enumerate(emails, start=1):
            email_id = email['id']
            STATUS_FILE.write_text(json.dumps({
                "state": "running",
                "current": f"{email.get('subject','(no subject)')[:120]}",
                "email_id": email_id,
                "progress": round((idx/total)*100,1),
                "index": idx,
                "total": total
            }))
            
            # Skip if already processed
            if email_id in processed_ids:
                continue
            
            # Get full body
            body = self.get_email_body(email_id, account=account)
            
            # Check if invoice
            if self.is_likely_invoice(email['subject'], body):
                print(f"  📄 Invoice detected: {email['subject'][:50]}...")
                
                # Extract details
                amount = self.extract_amount(body) or self.extract_amount(email['subject'])
                vendor = self.extract_vendor(email['sender'], body)
                due_date = self.extract_due_date(body)
                invoice_num = self.extract_invoice_number(body)
                
                invoice_data = {
                    'email_id': email_id,
                    'subject': email['subject'],
                    'vendor': vendor,
                    'amount': amount,
                    'due_date': due_date,
                    'invoice_number': invoice_num,
                    'date_found': datetime.now().isoformat()
                }
                
                # Add to database if amount found
                if amount:
                    inv_id = self.engine.add_invoice(
                        vendor=vendor,
                        amount=amount,
                        invoice_number=invoice_num,
                        due_date=due_date,
                        email_message_id=email_id,
                        auto_detected=True
                    )
                    invoice_data['invoice_id'] = inv_id
                    print(f"    ✅ Added invoice #{inv_id}: ${amount:.2f} from {vendor}")
                
                found_invoices.append(invoice_data)
            
            # Mark as scanned
            self.engine.conn.execute(
                "INSERT OR IGNORE INTO email_scan_log (email_id, invoices_found) VALUES (?, ?)",
                (email_id, 1 if invoice_data in found_invoices else 0)
            )
        
        self.engine.conn.commit()
        
        print(f"\n📊 Scan complete: {len(found_invoices)} invoices found")
        STATUS_FILE.write_text(json.dumps({"state":"done","current":"complete","found":len(found_invoices),"total":len(emails),"account":account,"scope":scope,"progress":100}))
        return found_invoices
    
    def get_unpaid_invoices_summary(self) -> Dict:
        """Get summary of unpaid/overdue invoices."""
        # Update overdue status
        overdue_count = self.engine.update_overdue_invoices()
        
        # Get summary
        unpaid = self.engine.get_invoices(status='unpaid')
        overdue = self.engine.get_invoices(status='overdue')
        
        total_unpaid = sum(inv['amount'] for inv in unpaid)
        total_overdue = sum(inv['amount'] for inv in overdue)
        
        return {
            'unpaid_count': len(unpaid),
            'unpaid_total': total_unpaid,
            'overdue_count': len(overdue),
            'overdue_total': total_overdue,
            'overdue_invoices': overdue[:5],  # Top 5
            'upcoming_invoices': [inv for inv in unpaid if inv not in overdue][:5]
        }

if __name__ == "__main__":
    scanner = InvoiceScanner()
    try:
        # Scan for new invoices
        invoices = scanner.scan_for_invoices(limit=100)

        # Get summary
        summary = scanner.get_unpaid_invoices_summary()
        print("\n💰 Unpaid Invoices Summary:")
        print(f"  Unpaid: {summary['unpaid_count']} (${summary['unpaid_total']:.2f})")
        print(f"  Overdue: {summary['overdue_count']} (${summary['overdue_total']:.2f})")
        STATUS_FILE.write_text(json.dumps({"state":"done","current":"complete","found":len(invoices),"unpaid":summary['unpaid_count'],"overdue":summary['overdue_count'],"progress":100,"account":os.getenv('SCAN_ACCOUNT','nick'),"scope":os.getenv('SCAN_SCOPE','unread')}))
    except Exception as e:
        STATUS_FILE.write_text(json.dumps({"state":"error","current":str(e),"progress":100,"account":os.getenv('SCAN_ACCOUNT','nick'),"scope":os.getenv('SCAN_SCOPE','unread')}))
        raise
    finally:
        scanner.engine.close()
