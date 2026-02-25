#!/usr/bin/env python3
import argparse
import json
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
QUEUE_MANAGER = SCRIPT_DIR / "queue_manager.py"
RESULTS_DIR = SKILL_ROOT / "data" / "agent-queue" / "results"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def enqueue(payload: Dict[str, Any]) -> None:
    payload_json = json.dumps(payload, ensure_ascii=False)
    proc = subprocess.run(
        ["python3", str(QUEUE_MANAGER), "enqueue", "--payload-json", payload_json],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"enqueue failed: {proc.stderr or proc.stdout}")


def wait_for_result(result_path: Path, timeout_seconds: int = 600, poll_seconds: int = 3) -> Dict[str, Any]:
    waited = 0
    while waited < timeout_seconds:
        if result_path.exists():
            data = json.loads(result_path.read_text(encoding="utf-8"))
            if data.get("status") in {"complete", "timeout", "error", "cancelled"}:
                return data
        time.sleep(poll_seconds)
        waited += poll_seconds
    raise TimeoutError(f"Queue result never arrived for {result_path.name} in {timeout_seconds}s")


def cleanup_result(result_path: Path) -> None:
    try:
        result_path.unlink(missing_ok=True)
    except Exception:
        pass


def main() -> int:
    p = argparse.ArgumentParser(description="Standard enqueue+poll+cleanup helper for ollama-agent-queue")
    p.add_argument("--calling-skill", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--system-prompt", required=True)
    p.add_argument("--user-prompt", required=True)
    p.add_argument("--priority", default="normal", choices=["normal", "high", "urgent"])
    p.add_argument("--max-tokens", type=int, default=500)
    p.add_argument("--agent-id", default="")
    p.add_argument("--timeout-seconds", type=int, default=600)
    p.add_argument("--poll-seconds", type=int, default=3)
    p.add_argument("--keep-result", action="store_true", help="Do not delete result file after read")
    args = p.parse_args()

    agent_id = args.agent_id.strip() or f"{args.calling_skill}-{uuid.uuid4().hex[:8]}"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    result_path = RESULTS_DIR / f"{agent_id}.json"

    payload = {
        "agent_id": agent_id,
        "model": args.model,
        "calling_skill": args.calling_skill,
        "priority": args.priority,
        "queued_at": now_iso(),
        "system_prompt": args.system_prompt,
        "user_prompt": args.user_prompt,
        "max_tokens": args.max_tokens,
        "callback": str(result_path),
    }

    enqueue(payload)
    result = wait_for_result(result_path, timeout_seconds=args.timeout_seconds, poll_seconds=args.poll_seconds)

    if not args.keep_result:
        cleanup_result(result_path)

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
