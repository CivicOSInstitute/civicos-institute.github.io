#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PRIORITY_RANK = {"normal": 0, "high": 1, "urgent": 2}
MODEL_MAP = {
    "local/qwen-coder-32b": "qwen2.5-coder:32b",
    "local/qwen-14b": "qwen2.5:14b",
    "local/mistral-small": "mistral:latest",
}
MODEL_TIMEOUTS = {
    "local/mistral-small": 120,
    "local/qwen-14b": 240,
    "local/qwen-coder-32b": 480,
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_iso(ts: str) -> Optional[datetime]:
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def age_seconds(ts: str) -> Optional[float]:
    dt = parse_iso(ts)
    if not dt:
        return None
    return (datetime.now(timezone.utc) - dt).total_seconds()


@dataclass
class QueuePaths:
    root: Path
    queue_file: Path
    lock_file: Path
    results_dir: Path
    logs_dir: Path
    alerts_file: Path


class QueueManager:
    def __init__(self, root: Optional[Path] = None):
        skill_root = Path(__file__).resolve().parents[1]
        base = root or Path(os.environ.get("OAQ_ROOT", skill_root / "data" / "agent-queue"))
        self.paths = QueuePaths(
            root=base,
            queue_file=base / "queue.json",
            lock_file=base / "queue.lock",
            results_dir=base / "results",
            logs_dir=base / "logs",
            alerts_file=base / "alerts.jsonl",
        )
        self.paths.root.mkdir(parents=True, exist_ok=True)
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
            "consecutive_resource_failures": 0,
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

    def _daily_perf_log_path(self) -> Path:
        d = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self.paths.root / f"queue-log-{d}.json"

    def _append_perf_log(self, entry: Dict[str, Any]) -> None:
        p = self._daily_perf_log_path()
        arr = []
        if p.exists():
            try:
                arr = json.loads(p.read_text(encoding="utf-8"))
                if not isinstance(arr, list):
                    arr = []
            except Exception:
                arr = []
        arr.append(entry)
        p.write_text(json.dumps(arr, indent=2, ensure_ascii=False), encoding="utf-8")

    def _avg_duration_by_model(self) -> Dict[str, float]:
        p = self._daily_perf_log_path()
        out = {"local/mistral-small": 0.0, "local/qwen-14b": 0.0, "local/qwen-coder-32b": 0.0}
        if not p.exists():
            return out
        try:
            rows = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return out
        buckets: Dict[str, List[float]] = {k: [] for k in out}
        for r in rows if isinstance(rows, list) else []:
            m = str(r.get("model", ""))
            d = r.get("duration_seconds")
            if m in buckets and isinstance(d, (int, float)) and d >= 0:
                buckets[m].append(float(d))
        for k, vals in buckets.items():
            if vals:
                out[k] = round(sum(vals) / len(vals), 2)
        return out

    def _log(self, msg: str) -> None:
        with (self.paths.logs_dir / "queue.log").open("a", encoding="utf-8") as f:
            f.write(f"[{now_iso()}] {msg}\n")

    def _emit_alert(self, channel: str, text: str) -> None:
        event = {"ts": now_iso(), "channel": channel, "message": text}
        with self.paths.alerts_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        self._log(f"ALERT[{channel}] {text}")

    def _is_ollama_process_active(self) -> bool:
        try:
            out = subprocess.run(["pgrep", "-f", "ollama"], capture_output=True, text=True, check=False)
            return out.returncode == 0 and bool(out.stdout.strip())
        except Exception:
            return False

    def _write_result(self, req: Dict[str, Any], payload: Dict[str, Any]) -> None:
        cb = Path(req.get("callback") or self.paths.results_dir / f"{req.get('agent_id', 'unknown')}.json")
        cb.parent.mkdir(parents=True, exist_ok=True)
        with cb.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    def _resolve_model(self, model_input: str) -> str:
        return MODEL_MAP.get(model_input, model_input)

    def _fetch_available_models(self, timeout: int = 10) -> List[str]:
        req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return [m.get("name", "") for m in data.get("models", []) if m.get("name")]

    def _ollama_generate(
        self,
        model_name: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        timeout_seconds: int,
    ) -> Tuple[bool, Dict[str, Any]]:
        body = {
            "model": model_name,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0.7},
        }
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                parsed = json.loads(resp.read().decode("utf-8"))
            return True, parsed
        except urllib.error.HTTPError as e:
            try:
                detail = e.read().decode("utf-8", errors="replace")
            except Exception:
                detail = str(e)
            return False, {"kind": "http", "status": e.code, "error": detail}
        except urllib.error.URLError as e:
            return False, {"kind": "connection", "error": str(e)}
        except TimeoutError:
            return False, {"kind": "timeout", "error": f"timeout_after_{timeout_seconds}s"}
        except Exception as e:
            return False, {"kind": "other", "error": str(e)}

    def _is_resource_error(self, err_payload: Dict[str, Any]) -> bool:
        text = json.dumps(err_payload, ensure_ascii=False).lower()
        return ("503" in text) or ("out of memory" in text) or ("resource exhausted" in text)

    def enqueue(self, payload: Dict[str, Any]) -> None:
        required = ["calling_skill", "agent_id", "model", "system_prompt", "user_prompt", "max_tokens"]
        missing = [k for k in required if k not in payload]
        if missing:
            raise ValueError(f"missing required keys: {', '.join(missing)}")

        payload.setdefault("priority", "normal")
        payload["priority"] = str(payload["priority"]).lower()
        if payload["priority"] not in PRIORITY_RANK:
            payload["priority"] = "normal"

        payload.setdefault("callback", str((self.paths.results_dir / f"{payload['agent_id']}.json").resolve()))
        payload["queued_at"] = now_iso()

        state = self._read_state()
        if any(p.get("agent_id") == payload["agent_id"] for p in state.get("pending", [])):
            raise ValueError(f"agent_id already queued: {payload['agent_id']}")
        cur = state.get("current_agent")
        if cur and cur.get("agent_id") == payload["agent_id"]:
            raise ValueError(f"agent_id already running: {payload['agent_id']}")

        state.setdefault("pending", []).append(payload)
        if state.get("status") == "idle":
            state["status"] = "running"
        self._write_state(state)
        self._log(f"ENQUEUE {payload['agent_id']} ({payload['priority']}) from {payload['calling_skill']}")

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

    def clear(self) -> int:
        state = self._read_state()
        pending = list(state.get("pending", []))
        state["pending"] = []
        self._write_state(state)
        for req in pending:
            self._write_result(
                req,
                {
                    "agent_id": req.get("agent_id"),
                    "calling_skill": req.get("calling_skill"),
                    "model": req.get("model"),
                    "status": "cancelled",
                    "error": "Cancelled by CLEAR QUEUE",
                    "result": None,
                    "completed_at": now_iso(),
                },
            )
        self._log(f"QUEUE cleared; cancelled={len(pending)}")
        return len(pending)

    def skip_current(self) -> bool:
        state = self._read_state()
        cur = state.get("current_agent")
        if not cur:
            return False
        try:
            subprocess.run(["pkill", "-f", "ollama"], check=False)
        except Exception:
            pass
        self._write_result(
            cur,
            {
                "agent_id": cur.get("agent_id"),
                "calling_skill": cur.get("calling_skill"),
                "model": cur.get("model"),
                "status": "timeout",
                "error": "Skipped by SKIP CURRENT",
                "result": None,
                "completed_at": now_iso(),
            },
        )
        state["current_agent"] = None
        state["failed_today"] = int(state.get("failed_today", 0)) + 1
        self._write_state(state)
        try:
            self.paths.lock_file.unlink(missing_ok=True)
        except Exception:
            pass
        self._emit_alert("architecture", "⚠️ SKIP CURRENT executed — queue moved to next item")
        return True

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
        return indexed[0][1]

    def _maybe_alert_wait_time(self, req: Dict[str, Any]) -> None:
        pr = str(req.get("priority", "normal")).lower()
        wait = age_seconds(str(req.get("queued_at", "")))
        if wait is None:
            return
        if pr == "urgent" and wait > 30:
            self._emit_alert("architecture", f"⚠️ Queue backlog: urgent item {req.get('agent_id')} waited {int(wait)}s (>30s)")
        elif pr == "high" and wait > 120:
            self._emit_alert("architecture", f"⚠️ Queue backlog: high item {req.get('agent_id')} waited {int(wait)}s (>120s)")

    def _pause_offline_and_fail_pending(self, reason: str) -> None:
        state = self._read_state()
        state["status"] = "paused_ollama_offline"
        pending = list(state.get("pending", []))
        state["pending"] = []
        self._write_state(state)
        for req in pending:
            self._write_result(req, {
                "agent_id": req.get("agent_id"),
                "calling_skill": req.get("calling_skill"),
                "model": req.get("model"),
                "status": "error",
                "error": reason,
                "result": None,
                "completed_at": now_iso(),
            })
            s = self._read_state()
            s["failed_today"] = int(s.get("failed_today", 0)) + 1
            self._write_state(s)
        self._emit_alert("direct", "🔴 Ollama server unreachable — agent queue paused. Restart Ollama and send RESUME QUEUE.")

    def _handle_stale_lock_if_needed(self) -> bool:
        if not self.paths.lock_file.exists():
            return False
        mtime_age = time.time() - self.paths.lock_file.stat().st_mtime
        if mtime_age <= 600:
            return True
        if self._is_ollama_process_active():
            return True

        state = self._read_state()
        cur = state.get("current_agent")
        if cur:
            self._write_result(cur, {
                "agent_id": cur.get("agent_id"),
                "calling_skill": cur.get("calling_skill"),
                "model": cur.get("model"),
                "status": "timeout",
                "error": "Agent exceeded timeout due to stale lock recovery",
                "result": None,
                "completed_at": now_iso(),
            })
            state["failed_today"] = int(state.get("failed_today", 0)) + 1
            state["current_agent"] = None
            state["status"] = "running"
            self._write_state(state)

        try:
            self.paths.lock_file.unlink(missing_ok=True)
        except Exception:
            pass
        self._emit_alert("architecture", "⚠️ Stale lock file cleared — queue resumed")
        self._log("STALE_LOCK cleared and queue resumed")
        return False

    def process_once(self) -> Dict[str, Any]:
        if self._handle_stale_lock_if_needed():
            return {"ok": True, "message": "locked"}

        state = self._read_state()
        status = state.get("status")
        if status in {"paused", "paused_ollama_offline"}:
            return {"ok": True, "message": status}

        pending = state.get("pending", [])
        if not pending:
            if status != "idle":
                state["status"] = "idle"
                self._write_state(state)
            return {"ok": True, "message": "queue_empty"}

        nxt = self._select_next(pending)
        if not nxt:
            return {"ok": True, "message": "queue_empty"}

        self._maybe_alert_wait_time(nxt)
        self.paths.lock_file.write_text(now_iso(), encoding="utf-8")
        started_at = now_iso()

        try:
            state = self._read_state()
            state["pending"] = [p for p in state.get("pending", []) if p.get("agent_id") != nxt.get("agent_id")]
            cur = dict(nxt)
            cur["started_at"] = started_at
            state["current_agent"] = cur
            state["status"] = "running"
            self._write_state(state)

            requested_model = str(nxt.get("model", ""))
            resolved_model = self._resolve_model(requested_model)

            models, tags_ok, last_err = [], False, ""
            for i in range(3):
                try:
                    models = self._fetch_available_models(timeout=10)
                    tags_ok = True
                    break
                except Exception as e:
                    last_err = str(e)
                    if i < 2:
                        time.sleep(10)

            if not tags_ok:
                self._pause_offline_and_fail_pending(f"ollama_unreachable_after_retries: {last_err}")
                self._write_result(nxt, {
                    "agent_id": nxt.get("agent_id"),
                    "calling_skill": nxt.get("calling_skill"),
                    "model": requested_model,
                    "status": "error",
                    "error": f"ollama_unreachable_after_retries: {last_err}",
                    "result": None,
                    "completed_at": now_iso(),
                })
                state = self._read_state()
                state["failed_today"] = int(state.get("failed_today", 0)) + 1
                state["current_agent"] = None
                self._write_state(state)
                return {"ok": False, "message": "ollama_unreachable", "agent_id": nxt.get("agent_id")}

            if resolved_model not in models:
                self._write_result(nxt, {
                    "agent_id": nxt.get("agent_id"),
                    "calling_skill": nxt.get("calling_skill"),
                    "model": requested_model,
                    "status": "error",
                    "error": f"model_not_available: {resolved_model}",
                    "result": None,
                    "completed_at": now_iso(),
                })
                state = self._read_state()
                state["failed_today"] = int(state.get("failed_today", 0)) + 1
                state["consecutive_resource_failures"] = 0
                state["current_agent"] = None
                if not state.get("pending") and state.get("status") == "running":
                    state["status"] = "idle"
                self._write_state(state)
                return {"ok": False, "message": "model_not_available", "agent_id": nxt.get("agent_id")}

            timeout_seconds = int(MODEL_TIMEOUTS.get(requested_model, 240))
            t0 = time.time()
            ok, payload = self._ollama_generate(
                model_name=resolved_model,
                system_prompt=str(nxt.get("system_prompt", "")),
                user_prompt=str(nxt.get("user_prompt", "")),
                max_tokens=int(nxt.get("max_tokens", 500)),
                timeout_seconds=timeout_seconds,
            )
            duration = round(time.time() - t0, 2)

            if (not ok) and self._is_resource_error(payload):
                time.sleep(30)
                t1 = time.time()
                ok2, payload2 = self._ollama_generate(
                    model_name=resolved_model,
                    system_prompt=str(nxt.get("system_prompt", "")),
                    user_prompt=str(nxt.get("user_prompt", "")),
                    max_tokens=int(nxt.get("max_tokens", 500)),
                    timeout_seconds=timeout_seconds,
                )
                duration = round(duration + (time.time() - t1), 2)
                ok, payload = ok2, payload2

            state = self._read_state()
            ended = now_iso()
            wait = age_seconds(str(nxt.get("queued_at", "")))
            wait = None if wait is None else round(wait, 2)

            if not ok:
                if payload.get("kind") == "timeout" or "timeout_after_" in str(payload.get("error", "")):
                    result = {
                        "agent_id": nxt.get("agent_id"),
                        "calling_skill": nxt.get("calling_skill"),
                        "model": requested_model,
                        "status": "timeout",
                        "error": f"Agent exceeded {timeout_seconds} second timeout",
                        "result": None,
                        "duration_seconds": duration,
                        "completed_at": ended,
                    }
                    state["consecutive_resource_failures"] = 0
                    self._emit_alert("architecture", f"⏱ Agent timeout: {nxt.get('agent_id')} ({requested_model}) exceeded {timeout_seconds}s — queue continuing")
                else:
                    result = {
                        "agent_id": nxt.get("agent_id"),
                        "calling_skill": nxt.get("calling_skill"),
                        "model": requested_model,
                        "status": "error",
                        "error": str(payload.get("error", "ollama_generate_failed")),
                        "result": None,
                        "duration_seconds": duration,
                        "completed_at": ended,
                    }
                    if self._is_resource_error(payload):
                        state["consecutive_resource_failures"] = int(state.get("consecutive_resource_failures", 0)) + 1
                        self._emit_alert("architecture", f"⚠️ Ollama resource error: {nxt.get('agent_id')} ({requested_model}) — queue continuing")
                    else:
                        state["consecutive_resource_failures"] = 0

                self._write_result(nxt, result)
                state["failed_today"] = int(state.get("failed_today", 0)) + 1
                state["current_agent"] = None
                if int(state.get("consecutive_resource_failures", 0)) >= 3:
                    state["status"] = "paused"
                    self._emit_alert("direct", "🔴 Queue paused after 3 consecutive Ollama resource failures. Investigate VRAM/load, then RESUME QUEUE.")
                elif not state.get("pending") and state.get("status") == "running":
                    state["status"] = "idle"
                self._write_state(state)

                self._append_perf_log({
                    "agent_id": nxt.get("agent_id"),
                    "calling_skill": nxt.get("calling_skill"),
                    "model": requested_model,
                    "priority": nxt.get("priority", "normal"),
                    "queued_at": nxt.get("queued_at"),
                    "started_at": started_at,
                    "completed_at": ended,
                    "wait_time_seconds": wait,
                    "duration_seconds": duration,
                    "tokens_used": None,
                    "status": result["status"],
                })
                return {"ok": False, "message": result["status"], "agent_id": nxt.get("agent_id")}

            result = {
                "agent_id": nxt.get("agent_id"),
                "calling_skill": nxt.get("calling_skill"),
                "model": requested_model,
                "status": "complete",
                "result": payload.get("response", ""),
                "tokens_used": payload.get("eval_count"),
                "duration_seconds": duration,
                "completed_at": ended,
            }
            self._write_result(nxt, result)
            state["completed_today"] = int(state.get("completed_today", 0)) + 1
            state["consecutive_resource_failures"] = 0
            state["current_agent"] = None
            if not state.get("pending") and state.get("status") == "running":
                state["status"] = "idle"
            self._write_state(state)

            self._append_perf_log({
                "agent_id": nxt.get("agent_id"),
                "calling_skill": nxt.get("calling_skill"),
                "model": requested_model,
                "priority": nxt.get("priority", "normal"),
                "queued_at": nxt.get("queued_at"),
                "started_at": started_at,
                "completed_at": ended,
                "wait_time_seconds": wait,
                "duration_seconds": duration,
                "tokens_used": payload.get("eval_count"),
                "status": "complete",
            })
            return {"ok": True, "message": "complete", "agent_id": nxt.get("agent_id")}

        finally:
            try:
                if self.paths.lock_file.exists():
                    self.paths.lock_file.unlink()
            except Exception:
                pass

    def status_json(self) -> Dict[str, Any]:
        s = self._read_state()
        s["lock_exists"] = self.paths.lock_file.exists()
        return s

    def status_block(self) -> str:
        s = self.status_json()
        cur = s.get("current_agent") or {}
        pending = s.get("pending", [])
        next1 = pending[0] if pending else None
        next2 = pending[1] if len(pending) > 1 else None
        elapsed = int(age_seconds(str(cur.get("started_at", ""))) or 0)
        cur_model = cur.get("model")
        cur_timeout = MODEL_TIMEOUTS.get(cur_model, 240)
        av = self._avg_duration_by_model()
        pending_pickup = len(list(self.paths.results_dir.glob("*.json")))

        lines = [
            "OLLAMA AGENT QUEUE STATUS",
            "=========================",
            f"Status: {s.get('status', 'unknown')}",
            f"Currently running: {cur.get('agent_id', 'none')} ({cur_model or 'n/a'}) — {elapsed}s / {cur_timeout}s",
            f"Pending: {len(pending)} agents",
            f"Next up: {next1.get('agent_id')} ({next1.get('model')}) — {next1.get('priority', 'normal')}" if next1 else "Next up: none",
            f"Then: {next2.get('agent_id')} ({next2.get('model')}) — {next2.get('priority', 'normal')}" if next2 else "Then: none",
            f"Completed today: {s.get('completed_today', 0)}",
            f"Failed today: {s.get('failed_today', 0)}",
            f"Avg duration: {av['local/mistral-small']}s (Mistral) | {av['local/qwen-14b']}s (Qwen14B) | {av['local/qwen-coder-32b']}s (QwenCoder32B)",
            f"Queue file: {self.paths.queue_file}",
            f"Results folder: {self.paths.results_dir} ({pending_pickup} pending pickup)",
            "Manual commands:",
            "- PAUSE QUEUE",
            "- RESUME QUEUE",
            "- CLEAR QUEUE",
            "- QUEUE STATUS",
            "- SKIP CURRENT",
        ]
        return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sequential local Ollama agent queue manager")
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("enqueue")
    e.add_argument("--payload-json", required=True, help="JSON payload string")
    sub.add_parser("status")
    sub.add_parser("status-block")
    sub.add_parser("pause")
    sub.add_parser("resume")
    sub.add_parser("clear")
    sub.add_parser("skip-current")
    sub.add_parser("process-once")
    w = sub.add_parser("worker")
    w.add_argument("--poll-seconds", type=float, default=2.0)
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
            print(json.dumps(q.status_json(), indent=2, ensure_ascii=False))
            return 0
        if args.cmd == "status-block":
            print(q.status_block())
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
            n = q.clear()
            print(json.dumps({"ok": True, "cleared": True, "cancelled": n}))
            return 0
        if args.cmd == "skip-current":
            did = q.skip_current()
            print(json.dumps({"ok": True, "skipped": did}))
            return 0
        if args.cmd == "process-once":
            print(json.dumps(q.process_once(), ensure_ascii=False))
            return 0
        if args.cmd == "worker":
            while True:
                out = q.process_once()
                if out.get("message") not in {"queue_empty", "locked", "paused", "paused_ollama_offline"}:
                    print(json.dumps(out, ensure_ascii=False), flush=True)
                time.sleep(args.poll_seconds)
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
