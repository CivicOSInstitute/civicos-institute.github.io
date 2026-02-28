#!/usr/bin/env python3
"""Preflight audit: find direct local-model calls outside queue implementation."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCAN_DIRS = [
    ROOT / "scripts",
    ROOT / "skills",
    ROOT / "agents",
    ROOT / "runbooks",
    ROOT / "config",
]

EXCLUDE_DIR_NAMES = {
    ".git",
    "node_modules",
    "generated",
    "data",
    "logs",
    "artifacts",
    "__pycache__",
    ".venv",
    ".venv-analytics",
    ".venv-hf",
}

ALLOWLIST_PATH_FRAGMENTS = [
    "skills/ollama-agent-queue/scripts/queue_manager.py",
    "skills/ollama-agent-queue/scripts/integration_helper.py",
    "scripts/local_queue_guard.py",
    "scripts/audit_local_model_routing.py",
]

TEXT_EXTS = {".py", ".sh", ".zsh", ".bash", ".md", ".txt", ".json", ".yaml", ".yml"}

PATTERNS = [
    re.compile(r"\bollama\s+run\b", re.IGNORECASE),
    re.compile(r"127\.0\.0\.1:11434/api/generate", re.IGNORECASE),
    re.compile(r"localhost:11434/api/generate", re.IGNORECASE),
]


def is_allowed(path: Path) -> bool:
    p = str(path)
    return any(fragment in p for fragment in ALLOWLIST_PATH_FRAGMENTS)


def should_scan(path: Path) -> bool:
    if path.suffix.lower() not in TEXT_EXTS:
        return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="Emit JSON")
    args = ap.parse_args()

    findings = []

    for base in SCAN_DIRS:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or not should_scan(path):
                continue
            if any(part in EXCLUDE_DIR_NAMES for part in path.parts):
                continue
            if is_allowed(path):
                continue

            try:
                lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            except Exception:
                continue

            for i, line in enumerate(lines, start=1):
                for pat in PATTERNS:
                    if pat.search(line):
                        findings.append({
                            "path": str(path.relative_to(ROOT)),
                            "line": i,
                            "match": line.strip(),
                        })

    result = {
        "status": "ok" if not findings else "violations",
        "count": len(findings),
        "findings": findings,
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"status={result['status']} count={result['count']}")
        for f in findings:
            print(f"{f['path']}:{f['line']} :: {f['match']}")

    return 0 if not findings else 3


if __name__ == "__main__":
    raise SystemExit(main())
