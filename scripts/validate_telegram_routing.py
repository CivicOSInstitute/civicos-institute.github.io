#!/usr/bin/env python3
"""
Validation check: enforce routed Telegram messaging.

Rules:
- No direct usage of send-telegram.sh in workspace scripts (except telegram_router.py).
- No hardcoded Nick DM chat id 8334496229 for outbound sends.
- All outbound sends must go through telegram_router.send_route_message().

Exit codes:
- 0: pass
- 1: violations found
"""

from __future__ import annotations

from pathlib import Path
import re
import sys

SCRIPTS = Path('/Users/AI-OPS/.openclaw/workspace/scripts')
ALLOW = {
    'telegram_router.py',
    'auto_task_from_telegram.py',  # inbound listener, not outbound router
    'validate_telegram_routing.py',
}

PATTERNS = [
    re.compile(r'send-telegram\.sh'),
    re.compile(r"['\"]8334496229['\"]"),
]


def main() -> int:
    violations: list[str] = []
    for p in sorted(SCRIPTS.glob('*.py')):
        if p.name in ALLOW:
            continue
        txt = p.read_text(errors='ignore')
        for pat in PATTERNS:
            if pat.search(txt):
                violations.append(f"{p.name}: prohibited pattern `{pat.pattern}`")

    if violations:
        print('ROUTING_VALIDATION_FAIL')
        for v in violations:
            print(f'- {v}')
        return 1

    print('ROUTING_VALIDATION_OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
