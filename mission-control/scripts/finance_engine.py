#!/usr/bin/env python3
"""
CivicOS Finance Engine
Core accounting system for Mission Control
"""

import sqlite3
import json
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Optional

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "finance.db"

def init_database():
    """Initialize finance database with schema."""
    DATA_DIR.mkdir(exist_ok=True)
    first_time = not DB_PATH.exists()
    conn = sqlite3.connect(DB_PATH)
    schema_path = Path(__file__).parent.parent / "db" / "finance_schema.sql"
    if first_time and schema_path.exists():
        with open(schema_path) as f:
            conn.executescript(f.read())
    conn.close()

class FinanceEngine:
    def __init__(self):
        init_database()
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
    
    def close(self):
        self.conn.close()
    
    # Transactions
    def add_transaction(self, date_str: str, description: str, amount: float, 
                       type_: str, category_id: int = None, vendor: str = None,
                       payment_method: str = None) -> int:
        """Add a new transaction."""
        cursor = self.conn.execute(
            """INSERT INTO transactions (date, description, amount, type, 
                category_id, vendor, payment_method)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (date_str, description, amount, type_, category_id, vendor, payment_method)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def get_transactions(self, start_date: str = None, end_date: str = None,
                        category_id: int = None, type_: str = None) -> List[Dict]:
        """Get transactions with filters."""
        query = """
            SELECT t.*, c.name as category_name, c.color as category_color
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE 1=1
        """
        params = []
        
        if start_date:
            query += " AND t.date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND t.date <= ?"
            params.append(end_date)
        if category_id:
            query += " AND t.category_id = ?"
            params.append(category_id)
        if type_:
            query += " AND t.type = ?"
            params.append(type_)
        
        query += " ORDER BY t.date DESC"
        
        cursor = self.conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    # Monthly Summary
    def get_monthly_summary(self, year: int, month: int) -> Dict:
        """Get P&L summary for a month."""
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"
        
        # Income
        income = self.conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='income' AND date >= ? AND date < ?",
            (start_date, end_date)
        ).fetchone()[0]
        
        # Expenses
        expenses = self.conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='expense' AND date >= ? AND date < ?",
            (start_date, end_date)
        ).fetchone()[0]
        
        # By category
        by_category = self.conn.execute(
            """SELECT c.name, c.type, SUM(t.amount) as total
               FROM transactions t
               JOIN categories c ON t.category_id = c.id
               WHERE t.date >= ? AND t.date < ?
               GROUP BY c.id
               ORDER BY total DESC""",
            (start_date, end_date)
        ).fetchall()
        
        return {
            'year': year,
            'month': month,
            'income': income,
            'expenses': expenses,
            'net': income - expenses,
            'by_category': [dict(row) for row in by_category]
        }
    
    # Invoices
    def add_invoice(self, vendor: str, amount: float, invoice_number: str = None,
                   issue_date: str = None, due_date: str = None,
                   email_message_id: str = None, pdf_path: str = None,
                   auto_detected: bool = False) -> int:
        """Add a new invoice."""
        cursor = self.conn.execute(
            """INSERT INTO invoices (vendor, amount, invoice_number, issue_date, due_date,
                email_message_id, pdf_path, auto_detected, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (vendor, amount, invoice_number, issue_date, due_date,
             email_message_id, pdf_path, auto_detected, 'unpaid')
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def get_invoices(self, status: str = None, overdue_only: bool = False) -> List[Dict]:
        """Get invoices with filters."""
        query = "SELECT * FROM invoices WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if overdue_only:
            query += " AND due_date < ? AND status = 'unpaid'"
            params.append(date.today().isoformat())
        
        query += " ORDER BY due_date ASC"
        
        cursor = self.conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def mark_invoice_paid(self, invoice_id: int, transaction_id: int = None):
        """Mark invoice as paid and optionally link to transaction."""
        self.conn.execute(
            "UPDATE invoices SET status='paid', transaction_id=? WHERE id=?",
            (transaction_id, invoice_id)
        )
        self.conn.commit()
    
    # Check for overdue invoices
    def update_overdue_invoices(self) -> int:
        """Update status of overdue invoices. Returns count."""
        cursor = self.conn.execute(
            """UPDATE invoices SET status='overdue'
               WHERE due_date < ? AND status = 'unpaid'""",
            (date.today().isoformat(),)
        )
        self.conn.commit()
        return cursor.rowcount
    
    # Cash flow projection
    def get_cash_flow_projection(self, days: int = 90) -> List[Dict]:
        """Project cash flow including recurring charges and unpaid invoices."""
        projections = []
        today = date.today()
        
        # Get unpaid invoices with due dates
        invoices = self.conn.execute(
            "SELECT * FROM invoices WHERE status IN ('unpaid', 'overdue') ORDER BY due_date"
        ).fetchall()
        
        # Get recurring charges
        recurring = self.conn.execute(
            "SELECT * FROM recurring_charges WHERE active=1"
        ).fetchall()
        
        # Build day-by-day projection
        for i in range(days):
            proj_date = today + timedelta(days=i)
            day_outflows = 0
            day_items = []
            
            # Check invoices due on this day
            for inv in invoices:
                if inv['due_date'] == proj_date.isoformat():
                    day_outflows += inv['amount']
                    day_items.append(f"Invoice: {inv['vendor']}")
            
            # Check recurring charges
            for rec in recurring:
                if rec['next_due_date'] == proj_date.isoformat():
                    day_outflows += rec['amount']
                    day_items.append(f"Recurring: {rec['name']}")
            
            if day_outflows > 0:
                projections.append({
                    'date': proj_date.isoformat(),
                    'outflow': day_outflows,
                    'items': day_items
                })
        
        return projections

if __name__ == "__main__":
    # Test
    engine = FinanceEngine()
    print("Finance Engine initialized")
    
    # Add sample transaction
    # engine.add_transaction("2026-03-01", "Test donation", 100.00, "income", 1)
    
    # Get monthly summary
    summary = engine.get_monthly_summary(2026, 3)
    print(json.dumps(summary, indent=2))
    
    engine.close()
