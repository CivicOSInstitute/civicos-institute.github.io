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
        self.paths.results_dir.mkdir(parents=True, exist_ok=True)
        self.paths.logs_dir.mkdir(parents=True, exist_ok=True)
        self.paths.root.mkdir(parents=True, exist_ok=True)
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

    def _emit_alert(self, channel: str, text: str) -> None:
        event = {"ts": now_iso(), "channel": channel, "message": text}
        with self.paths.alerts_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        self._log(f"ALERT[{channel}] {text}")

        # Optional external hook, e.g. OAQ_ALERT_CMD='python3 notify.py "{channel}" "{message}"'
        cmd_tpl = os.environ.get("OAQ_ALERT_CMD", "").strip()
        if cmd_tpl:
            cmd = cmd_tpl.format(channel=channel, message=text.replace('"', "'"))
            try:
                subprocess.run(cmd, shell=True, check=False)
            except Exception:
                pass

    def enqueue(self, payload: Dict[str, Any]) -> None:
        required = ["calling_skill", "agent_id", "model", "system_prompt", "user_prompt", "max_tokens"]
        missing = [k for k in required if k not in payload]
        if missing:
            raise ValueError(f"missing required keys: {', '.join(missing)}")

        payload.setdefault("priority", "normal")
        payload["priority"] = str(payload["priority"]).lower()
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
        if state.get("status") == "idle":
            state["status"] = "running"
        self._write_state(state)
        self._log(f"ENQUEUE {payload['agent_id']} ({payload['priority']}) from {payload['calling_skill']}")

    def status(self) -> Dict[str, Any]:
        s = self._read_state()
        s["lock_exists"] = self.paths.lock_file.exists()
        return s

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
        return indexed[0][1]

    def _write_result(self, req: Dict[str, Any], payload: Dict[str, Any]) -> None:
        cb = Path(req.get("callback") or self.paths.results_dir / f"{req['agent_id']}.json")
        cb.parent.mkdir(parents=True, exist_ok=True)
        with cb.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    def _update_done(self, result_status: str) -> None:
        state = self._read_state()
        state["current_agent"] = None
        if result_status == "complete":
            state["completed_today"] = int(state.get("completed_today", 0)) + 1
        else:
            state["failed_today"] = int(state.get("failed_today", 0)) + 1

        if not state.get("pending") and state.get("status") == "running":
            state["status"] = "idle"
        self._write_state(state)

    def _resolve_model(self, model_input: str) -> str:
        return MODEL_MAP.get(model_input, model_input)

    def _fetch_available_models(self, timeout: int = 10) -> List[str]:
        url = "http://localhost:11434/api/tags"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
        return models

    def _ollama_generate(
        self,
        model_name: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        timeout_seconds: int,
    ) -> Tuple[bool, Dict[str, Any]]:
        url = "http://localhost:11434/api/generate"
        body = {
            "model": model_name,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0.7},
        }
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                parsed = json.loads(resp.read().decode("utf-8"))
            return True, parsed
        except urllib.error.URLError as e:
            return False, {"error": f"connection_error: {e}"}
        except TimeoutError:
            return False, {"error": f"timeout_after_{timeout_seconds}s"}
        except Exception as e:
            return False, {"error": str(e)}

    def _pause_offline_and_fail_pending(self, reason: str) -> None:
        state = self._read_state()
        state["status"] = "paused_ollama_offline"
        pending = state.get("pending", [])
        state["pending"] = []
        self._write_state(state)

        for req in pending:
            fail = {
                "agent_id": req.get("agent_id"),
                "calling_skill": req.get("calling_skill"),
                "model": req.get("model"),
                "status": "error",
                "error": reason,
                "result": None,
                "completed_at": now_iso(),
            }
            self._write_result(req, fail)
            st = self._read_state()
            st["failed_today"] = int(st.get("failed_today", 0)) + 1
            self._write_state(st)

        self._emit_alert(
            "direct",
            "🔴 Ollama server unreachable — agent queue paused. Restart Ollama and send RESUME QUEUE.",
        )

    def process_once(self) -> Dict[str, Any]:
        # lock discipline: if lock exists, do nothing
        if self.paths.lock_file.exists():
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

        # create lock + move to current_agent
        self.paths.lock_file.write_text(now_iso(), encoding="utf-8")
        try:
            state = self._read_state()
            state["pending"] = [p for p in state.get("pending", []) if p.get("agent_id") != nxt.get("agent_id")]
            state["current_agent"] = {
                "agent_id": nxt["agent_id"],
                "model": nxt["model"],
                "calling_skill": nxt["calling_skill"],
                "started_at": now_iso(),
            }
            state["status"] = "running"
            self._write_state(state)
            self._log(f"START {nxt['agent_id']} model={nxt['model']}")

            requested_model = str(nxt.get("model", ""))
            resolved_model = self._resolve_model(requested_model)

            # Ollama reachability + available model list check (3 retries, 10s backoff)
            available: List[str] = []
            tags_ok = False
            tags_err = ""
            for i in range(3):
                try:
                    available = self._fetch_available_models(timeout=10)
                    tags_ok = True
                    break
                except Exception as e:
                    tags_err = str(e)
                    if i < 2:
                        time.sleep(10)

            if not tags_ok:
                self._pause_offline_and_fail_pending(f"ollama_unreachable_after_retries: {tags_err}")
                fail = {
                    "agent_id": nxt.get("agent_id"),
                    "calling_skill": nxt.get("calling_skill"),
                    "model": requested_model,
                    "status": "error",
                    "error": f"ollama_unreachable_after_retries: {tags_err}",
                    "result": None,
                    "completed_at": now_iso(),
                }
                self._write_result(nxt, fail)
                self._update_done("failed")
                return {"ok": False, "message": "ollama_unreachable", "agent_id": nxt.get("agent_id")}

            if resolved_model not in available:
                fail = {
                    "agent_id": nxt.get("agent_id"),
                    "calling_skill": nxt.get("calling_skill"),
                    "model": requested_model,
                    "status": "error",
                    "error": f"model_not_available: {resolved_model}",
                    "result": None,
                    "completed_at": now_iso(),
                }
                self._write_result(nxt, fail)
                self._update_done("failed")
                self._log(f"FAIL {nxt['agent_id']} model_not_available={resolved_model}")
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

            if not ok:
                err = payload.get("error", "ollama_generate_failed")
                if str(err).startswith("timeout_after_"):
                    result = {
                        "agent_id": nxt.get("agent_id"),
                        "calling_skill": nxt.get("calling_skill"),
                        "model": requested_model,
                        "status": "timeout",
                        "error": f"Agent exceeded {timeout_seconds} second timeout",
                        "result": None,
                        "duration_seconds": duration,
                        "completed_at": now_iso(),
                    }
                    self._emit_alert(
                        "architecture",
                        f"⏱ Agent timeout: {nxt.get('agent_id')} ({requested_model}) exceeded {timeout_seconds}s — queue continuing",
                    )
                else:
                    result = {
                        "agent_id": nxt.get("agent_id"),
                        "calling_skill": nxt.get("calling_skill"),
                        "model": requested_model,
                        "status": "error",
                        "error": str(err),
                        "result": None,
                        "duration_seconds": duration,
                        "completed_at": now_iso(),
                    }
                self._write_result(nxt, result)
                self._update_done("failed")
                self._log(f"FAIL {nxt['agent_id']} error={err}")
                return {"ok": False, "message": result["status"], "agent_id": nxt.get("agent_id")}

            result = {
                "agent_id": nxt.get("agent_id"),
                "calling_skill": nxt.get("calling_skill"),
                "model": requested_model,
                "status": "complete",
                "result": payload.get("response", ""),
                "tokens_used": payload.get("eval_count"),
                "duration_seconds": duration,
                "completed_at": now_iso(),
            }
            self._write_result(nxt, result)
            self._update_done("complete")
            self._log(f"DONE {nxt['agent_id']} complete")
            return {"ok": True, "message": "complete", "agent_id": nxt.get("agent_id")}

        finally:
            try:
                if self.paths.lock_file.exists():
                    self.paths.lock_file.unlink()
            except Exception:
                pass


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sequential local Ollama agent queue manager")
    sub = p.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("enqueue")
    e.add_argument("--payload-json", required=True, help="JSON payload string")

    sub.add_parser("status")
    sub.add_parser("pause")
    sub.add_parser("resume")
    sub.add_parser("clear")

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
            print(json.dumps(q.process_once(), ensure_ascii=False))
            return 0
        if args.cmd == "worker":
            while True:
                out = q.process_once()
                if out.get("message") not in {"queue_empty", "idle", "running", "locked", "paused", "paused_ollama_offline"}:
                    print(json.dumps(out, ensure_ascii=False), flush=True)
                time.sleep(args.poll_seconds)
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
