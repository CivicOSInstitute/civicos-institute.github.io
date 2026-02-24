#!/usr/bin/env python3
import json, os, sqlite3, sys
from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_DB_ID = os.getenv("NOTION_DB_ID", "")
TASK_DB_ENV = os.getenv("TASK_DB", "")
WORKSPACE = Path(os.getenv("WORKSPACE", "/Users/AI-OPS/.openclaw/workspace"))
STATE_PATH = WORKSPACE / "notion-ops" / ".notion_task_links.json"

CANDIDATE_DBS = [
    Path(TASK_DB_ENV) if TASK_DB_ENV else None,
    Path.home() / ".openclaw" / "task-tracker" / "tasks.db",
    WORKSPACE / "task-tracker" / "tasks.db",
]

STATUS_MAP = {
    "not started": "Not started",
    "not_started": "Not started",
    "in progress": "In progress",
    "in_progress": "In progress",
    "completed": "Done",
    "done": "Done",
    "blocked": "Blocked",
}


def jreq(method, url, body=None):
    hdr = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = Request(url, data=data, headers=hdr, method=method)
    try:
        with urlopen(req) as r:
            return json.loads(r.read().decode("utf-8"))
    except HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"error": raw}
        raise RuntimeError(f"Notion API {e.code}: {payload}")


def pick_task_db():
    for p in CANDIDATE_DBS:
        if p and p.exists() and p.stat().st_size > 0:
            return p
    raise RuntimeError("No task dashboard DB found. Set TASK_DB env var to tasks.db path.")


def table_has(conn, table):
    c = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return c.fetchone() is not None


def load_tasks(conn):
    if not table_has(conn, "task"):
        return []
    cols = [r[1] for r in conn.execute("PRAGMA table_info(task)").fetchall()]
    wanted = ["id", "title", "status", "priority", "notes", "due_date", "project", "assigned_to"]
    pick = [c for c in wanted if c in cols]
    q = f"SELECT {', '.join(pick)} FROM task"
    rows = []
    for row in conn.execute(q).fetchall():
        d = dict(zip(pick, row))
        rows.append(d)
    return rows


def normalize_status(s):
    if not s:
        return "Not started"
    k = str(s).strip().lower()
    return STATUS_MAP.get(k, s)


def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"links": {}}


def save_state(state):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2))


def db_properties():
    db = jreq("GET", f"https://api.notion.com/v1/databases/{NOTION_DB_ID}")
    return db.get("properties", {})


def build_properties(schema, t):
    props = {}
    # title property (required)
    title_name = next((k for k, v in schema.items() if v.get("type") == "title"), "Name")
    props[title_name] = {"title": [{"text": {"content": str(t.get("title") or f"Task {t.get('id')}")}}]}

    status_name = next((k for k, v in schema.items() if v.get("type") == "status"), None)
    if status_name:
        props[status_name] = {"status": {"name": normalize_status(t.get("status"))}}

    # heuristic selects
    for name, cfg in schema.items():
        if cfg.get("type") != "select":
            continue
        low = name.lower()
        if "priority" in low and t.get("priority"):
            props[name] = {"select": {"name": str(t.get("priority"))}}
        elif "channel" in low:
            props[name] = {"select": {"name": "Architecture"}}

    # due date heuristic
    due_name = next((k for k, v in schema.items() if v.get("type") == "date" and "due" in k.lower()), None)
    if due_name and t.get("due_date"):
        props[due_name] = {"date": {"start": str(t.get("due_date"))}}

    return props


def create_page(schema, t):
    body = {"parent": {"database_id": NOTION_DB_ID}, "properties": build_properties(schema, t)}
    return jreq("POST", "https://api.notion.com/v1/pages", body)


def patch_page(schema, notion_page_id, t):
    body = {"properties": build_properties(schema, t)}
    return jreq("PATCH", f"https://api.notion.com/v1/pages/{notion_page_id}", body)


def main():
    if not NOTION_TOKEN or not NOTION_DB_ID:
        print("NOTION_TOKEN and NOTION_DB_ID are required", file=sys.stderr)
        sys.exit(1)

    db_path = pick_task_db()
    conn = sqlite3.connect(str(db_path))
    tasks = load_tasks(conn)
    conn.close()

    schema = db_properties()
    state = load_state()
    links = state.setdefault("links", {})

    created = 0
    updated = 0

    for t in tasks:
        tid = str(t.get("id"))
        if not tid:
            continue
        snap = {
            "status": t.get("status"),
            "priority": t.get("priority"),
            "due_date": t.get("due_date"),
            "title": t.get("title"),
        }
        if tid not in links:
            p = create_page(schema, t)
            links[tid] = {
                "notion_page_id": p["id"],
                "notion_url": p.get("url"),
                "last_snapshot": snap,
            }
            created += 1
            continue

        last = links[tid].get("last_snapshot", {})
        if last != snap:
            patch_page(schema, links[tid]["notion_page_id"], t)
            links[tid]["last_snapshot"] = snap
            updated += 1

    state["last_run"] = date.today().isoformat()
    save_state(state)
    print(json.dumps({
        "task_db": str(db_path),
        "total_tasks": len(tasks),
        "created": created,
        "updated": updated,
        "linked": len(links),
        "state_path": str(STATE_PATH),
    }, indent=2))


if __name__ == "__main__":
    main()
