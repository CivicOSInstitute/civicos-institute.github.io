#!/usr/bin/env python3
import json
import sqlite3
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data' / 'finance.db'
OUT = ROOT / 'data' / 'finance-status.json'


def q(cur, sql, params=()):
    cur.execute(sql, params)
    return cur.fetchall()


def main():
    if not DB.exists():
        OUT.write_text(json.dumps({"monthly": {"income": 0, "expenses": 0, "net": 0}, "invoices": {"unpaid_count": 0, "unpaid_total": 0, "overdue_count": 0, "list": []}, "transactions": []}, indent=2))
        print('finance db missing, wrote empty status')
        return

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    today = date.today()
    start = today.replace(day=1).isoformat()
    end = (today.replace(year=today.year + (1 if today.month == 12 else 0), month=(1 if today.month == 12 else today.month + 1), day=1)).isoformat()

    income = q(cur, "SELECT COALESCE(SUM(amount),0) s FROM transactions WHERE type='income' AND date>=? AND date<?", (start, end))[0]['s']
    expenses = q(cur, "SELECT COALESCE(SUM(amount),0) s FROM transactions WHERE type='expense' AND date>=? AND date<?", (start, end))[0]['s']

    tx = [dict(r) for r in q(cur, """
        SELECT t.date,t.description,t.amount,t.type,c.name as category_name
        FROM transactions t LEFT JOIN categories c ON c.id=t.category_id
        ORDER BY t.date DESC, t.id DESC LIMIT 25
    """)]

    inv_list = [dict(r) for r in q(cur, "SELECT id,invoice_number,vendor,amount,due_date,status FROM invoices WHERE status IN ('unpaid','overdue') ORDER BY CASE status WHEN 'overdue' THEN 0 ELSE 1 END, due_date ASC LIMIT 25")]
    unpaid_count = len(inv_list)
    unpaid_total = float(sum((r.get('amount') or 0) for r in inv_list))
    overdue_count = sum(1 for r in inv_list if r.get('status') == 'overdue')

    payload = {
        "monthly": {
            "income": float(income or 0),
            "expenses": float(expenses or 0),
            "net": float((income or 0) - (expenses or 0)),
            "period": f"{today.year}-{today.month:02d}"
        },
        "invoices": {
            "unpaid_count": unpaid_count,
            "unpaid_total": unpaid_total,
            "overdue_count": overdue_count,
            "list": inv_list
        },
        "transactions": tx,
        "updatedAt": today.isoformat()
    }

    OUT.write_text(json.dumps(payload, indent=2))
    print(f'wrote {OUT}')


if __name__ == '__main__':
    main()
