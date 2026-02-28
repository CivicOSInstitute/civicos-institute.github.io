#!/usr/bin/env python3
"""Block direct local model calls outside the queue skill."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

FORBIDDEN_PATTERNS = [
    re.compile(r"\bollama\s+run\b", re.IGNORECASE),
    re.compile(r"127\.0\.0\.1:11434/api/generate", re.IGNORECASE),
    re.compile(r"localhost:11434/api/generate", re.IGNORECASE),
    re.compile(r"/api/generate", re.IGNORECASE),
]

REQUIRED_HINTS = [
    "skills/ollama-agent-queue/scripts/integration_helper.py",
    "skills/ollama-agent-queue/scripts/queue_manager.py",
]

ROOT = Path(__file__).resolve().parents[1]
VIOLATION_LOG = ROOT / "generated" / "queue_guard_violations.jsonl"


def _log_violation(context: str, command: str) -> None:
    VIOLATION_LOG.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "context": context,
        "command": command,
        "action": "blocked",
        "exit_code": 42,
    }
    with VIOLATION_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def main() -> int:
    p = argparse.ArgumentParser(description="Guard against direct local model execution.")
    p.add_argument("--command", required=True, help="Command string to validate before execution")
    p.add_argument("--context", default="subagent", help="Execution context label for logs")
    args = p.parse_args()

    command = args.command.strip()
    normalized = command.lower()

    # Allow explicit queue usage
    if any(hint in normalized for hint in [h.lower() for h in REQUIRED_HINTS]):
        print("QUEUE_GUARD_OK: queue path detected")
        return 0

    for pat in FORBIDDEN_PATTERNS:
        if pat.search(command):
            _log_violation(args.context, command)
            print(
                "QUEUE_GUARD_BLOCKED: direct local model invocation detected. "
                "Route through skills/ollama-agent-queue/scripts/integration_helper.py",
                file=sys.stderr,
            )
            print(f"Context: {args.context}", file=sys.stderr)
            print(f"Command: {command}", file=sys.stderr)
            print(f"Violation log: {VIOLATION_LOG}", file=sys.stderr)
            return 42

    print("QUEUE_GUARD_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
