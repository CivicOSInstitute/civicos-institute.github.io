#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

PRIORITY_RANK = {"normal": 0, "high": 1, "urgent": 2}
MODEL_MAP = {
    "local/qwen-coder-32b": "qwen2.5-coder:32b-instruct-q3_K_L",
    "local/qwen-14b": "qwen2.5:14b",
    "local/mistral-small": "mistral-small3.2:24b-instruct-2506-q4_K_M",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class QueuePaths:
    root: Path
    queue_file: Path
    results_dir: Path
    logs_dir: Path


class QueueManager:
    def __init__(self, root: Optional[Path] = None):
        skill_root = Path(__file__).resolve().parents[1]
        base = root or Path(os.environ.get("OAQ_ROOT", skill_root / "data" / "agent-queue"))
        self.paths = QueuePaths(
            root=base,
            queue_file=base / "queue.json",
            results_dir=base / "results",
            logs_dir=base / "logs",
        )
        self.paths.results_dir.mkdir(parents=True, exist_ok=True)
        self.paths.logs_dir.mkdir(parents=True, exist_ok=True)
        if not self.paths.queue_file.exists():
            self._write_state(self._default_state())

    def _default_state(self) -> Dict[str, Any]:
        return {
            "status": "running",
            "current_agent": None,
            "pending": [],
            "completed_today": 0,
            "failed_today": 0,
            "last_updated": now_iso(),
        }

    def _read_state(self) -> Dict[str, Any]:
        try:
            with self.paths.queue_file.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            state = self._default_state()
            self._write_state(state)
            return state

    def _write_state(self, state: Dict[str, Any]) -> None:
        state["last_updated"] = now_iso()
        tmp = self.paths.queue_file.with_suffix(".json.tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        os.replace(tmp, self.paths.queue_file)

    def _log(self, msg: str) -> None:
        line = f"[{now_iso()}] {msg}\n"
        with (self.paths.logs_dir / "queue.log").open("a", encoding="utf-8") as f:
            f.write(line)

    def enqueue(self, payload: Dict[str, Any]) -> None:
        required = ["calling_skill", "agent_id", "model", "system_prompt", "user_prompt", "max_tokens"]
        missing = [k for k in required if k not in payload]
        if missing:
            raise ValueError(f"missing required keys: {', '.join(missing)}")

        payload.setdefault("priority", "normal")
        payload["priority"] = payload["priority"].lower()
        if payload["priority"] not in PRIORITY_RANK:
            payload["priority"] = "normal"

        payload.setdefault(
            "callback",
            str((self.paths.results_dir / f"{payload['agent_id']}.json").resolve()),
        )
        payload["queued_at"] = now_iso()

        state = self._read_state()
        if any(p.get("agent_id") == payload["agent_id"] for p in state.get("pending", [])):
            raise ValueError(f"agent_id already queued: {payload['agent_id']}")
        cur = state.get("current_agent")
        if cur and cur.get("agent_id") == payload["agent_id"]:
            raise ValueError(f"agent_id already running: {payload['agent_id']}")

        state.setdefault("pending", []).append(payload)
        self._write_state(state)
        self._log(f"ENQUEUE {payload['agent_id']} ({payload['priority']}) from {payload['calling_skill']}")

    def status(self) -> Dict[str, Any]:
        return self._read_state()

    def pause(self) -> None:
        state = self._read_state()
        state["status"] = "paused"
        self._write_state(state)
        self._log("QUEUE paused")

    def resume(self) -> None:
        state = self._read_state()
        state["status"] = "running"
        self._write_state(state)
        self._log("QUEUE resumed")

    def clear(self) -> None:
        state = self._read_state()
        state["pending"] = []
        self._write_state(state)
        self._log("QUEUE cleared")

    def _select_next(self, pending: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not pending:
            return None
        indexed = list(enumerate(pending))
        indexed.sort(
            key=lambda x: (
                -PRIORITY_RANK.get(str(x[1].get("priority", "normal")).lower(), 0),
                x[1].get("queued_at", ""),
                x[0],
            )
        )
        _, item = indexed[0]
        return item

    def process_once(self, timeout_seconds: int = 1800) -> Dict[str, Any]:
        state = self._read_state()
        if state.get("status") != "running":
            return {"ok": True, "message": "queue_paused"}
        if state.get("current_agent"):
            return {"ok": True, "message": "agent_already_running"}

        pending = state.get("pending", [])
        nxt = self._select_next(pending)
        if not nxt:
            return {"ok": True, "message": "queue_empty"}

        # remove selected request
        state["pending"] = [p for p in pending if p.get("agent_id") != nxt.get("agent_id")]
        running = {
            "agent_id": nxt["agent_id"],
            "model": nxt["model"],
            "calling_skill": nxt["calling_skill"],
            "started_at": now_iso(),
        }
        state["current_agent"] = running
        self._write_state(state)
        self._log(f"START {nxt['agent_id']} model={nxt['model']}")

        result = self._run_agent(nxt, timeout_seconds)

        state = self._read_state()
        state["current_agent"] = None
        if result.get("status") == "complete":
            state["completed_today"] = int(state.get("completed_today", 0)) + 1
        else:
            state["failed_today"] = int(state.get("failed_today", 0)) + 1
        self._write_state(state)

        cb = Path(nxt.get("callback") or self.paths.results_dir / f"{nxt['agent_id']}.json")
        cb.parent.mkdir(parents=True, exist_ok=True)
        with cb.open("w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        self._log(f"DONE {nxt['agent_id']} status={result.get('status')}")
        return {"ok": True, "message": result.get("status"), "agent_id": nxt["agent_id"]}

    def _run_agent(self, req: Dict[str, Any], timeout_seconds: int) -> Dict[str, Any]:
        model_input = req.get("model", "")
        model_name = MODEL_MAP.get(model_input, model_input)
        prompt = f"SYSTEM:\n{req.get('system_prompt', '')}\n\nUSER:\n{req.get('user_prompt', '')}\n"

        t0 = time.time()
        try:
            proc = subprocess.run(
                ["ollama", "run", model_name],
                input=prompt,
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
            )
            duration = round(time.time() - t0, 2)
            if proc.returncode != 0:
                return {
                    "agent_id": req.get("agent_id"),
                    "calling_skill": req.get("calling_skill"),
                    "model": model_input,
                    "status": "failed",
                    "error": (proc.stderr or "ollama run failed").strip(),
                    "result": "",
                    "tokens_used": None,
                    "duration_seconds": duration,
                    "completed_at": now_iso(),
                }
            return {
                "agent_id": req.get("agent_id"),
                "calling_skill": req.get("calling_skill"),
                "model": model_input,
                "status": "complete",
                "result": (proc.stdout or "").strip(),
                "tokens_used": None,
                "duration_seconds": duration,
                "completed_at": now_iso(),
            }
        except subprocess.TimeoutExpired:
            duration = round(time.time() - t0, 2)
            return {
                "agent_id": req.get("agent_id"),
                "calling_skill": req.get("calling_skill"),
                "model": model_input,
                "status": "failed",
                "error": f"timeout_after_{timeout_seconds}s",
                "result": "",
                "tokens_used": None,
                "duration_seconds": duration,
                "completed_at": now_iso(),
            }
        except Exception as e:
            duration = round(time.time() - t0, 2)
            return {
                "agent_id": req.get("agent_id"),
                "calling_skill": req.get("calling_skill"),
                "model": model_input,
                "status": "failed",
                "error": str(e),
                "result": "",
                "tokens_used": None,
                "duration_seconds": duration,
                "completed_at": now_iso(),
            }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sequential local Ollama agent queue manager")
    sub = p.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("enqueue")
    e.add_argument("--payload-json", required=True, help="JSON payload string")

    sub.add_parser("status")
    sub.add_parser("pause")
    sub.add_parser("resume")
    sub.add_parser("clear")

    po = sub.add_parser("process-once")
    po.add_argument("--timeout-seconds", type=int, default=1800)

    w = sub.add_parser("worker")
    w.add_argument("--poll-seconds", type=float, default=2.0)
    w.add_argument("--timeout-seconds", type=int, default=1800)

    return p.parse_args()


def main() -> int:
    args = parse_args()
    q = QueueManager()

    try:
        if args.cmd == "enqueue":
            payload = json.loads(args.payload_json)
            q.enqueue(payload)
            print(json.dumps({"ok": True, "queued": payload.get("agent_id")}))
            return 0
        if args.cmd == "status":
            print(json.dumps(q.status(), indent=2, ensure_ascii=False))
            return 0
        if args.cmd == "pause":
            q.pause()
            print(json.dumps({"ok": True, "status": "paused"}))
            return 0
        if args.cmd == "resume":
            q.resume()
            print(json.dumps({"ok": True, "status": "running"}))
            return 0
        if args.cmd == "clear":
            q.clear()
            print(json.dumps({"ok": True, "cleared": True}))
            return 0
        if args.cmd == "process-once":
            print(json.dumps(q.process_once(timeout_seconds=args.timeout_seconds), ensure_ascii=False))
            return 0
        if args.cmd == "worker":
            while True:
                out = q.process_once(timeout_seconds=args.timeout_seconds)
                # quiet loop when empty/paused
                if out.get("message") not in {"queue_empty", "queue_paused", "agent_already_running"}:
                    print(json.dumps(out, ensure_ascii=False), flush=True)
                time.sleep(args.poll_seconds)
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
