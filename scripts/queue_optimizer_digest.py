#!/usr/bin/env python3
import sqlite3
from pathlib import Path
import subprocess
from datetime import datetime

DB = Path('/Users/AI-OPS/.openclaw/task-tracker/tasks.db')
SEND = Path('/Users/AI-OPS/.openclaw/scripts/send-telegram.sh')

if not DB.exists():
    print('no task db')
    raise SystemExit(0)

conn=sqlite3.connect(str(DB))
cur=conn.cursor()
cur.execute("""
SELECT id,title,priority,due_date,created_date
FROM task
WHERE status='Not Started' AND (
  lower(title) LIKE '%approve%' OR lower(notes) LIKE '%pending approval%'
)
ORDER BY CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END, id DESC
""")
rows=cur.fetchall()
conn.close()

if len(rows) <= 5:
    print('queue depth normal')
    raise SystemExit(0)

oldest = rows[-1]
msg=[
  f"📬 Approval queue digest: {len(rows)} pending",
  f"Oldest item: #{oldest[0]} {oldest[1][:60]}",
  "Top 5:"
]
for r in rows[:5]:
  msg.append(f"- #{r[0]} [{r[2]}] {r[1][:70]}")
text='\n'.join(msg)
print(text)
if SEND.exists():
  subprocess.run([str(SEND),'8334496229',text],check=False)
