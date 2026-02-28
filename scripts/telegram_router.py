#!/usr/bin/env python3
"""
Hard-enforced Telegram routing helper.

All outbound Telegram messages must resolve a route key via:
  config/telegram_channel_map.json

Fail-closed behavior:
- Missing config file => error
- Missing route key => error
- Missing channel id => error
- Missing send script => error
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Dict

WORKSPACE = Path('/Users/AI-OPS/.openclaw/workspace')
MAP_PATH = WORKSPACE / 'config' / 'telegram_channel_map.json'


class RoutingError(RuntimeError):
    pass


def _load_map() -> Dict:
    if not MAP_PATH.exists():
        raise RoutingError(f"Routing map missing: {MAP_PATH}")
    try:
        data = json.loads(MAP_PATH.read_text())
    except Exception as e:
        raise RoutingError(f"Routing map unreadable: {MAP_PATH} ({e})")

    if not isinstance(data, dict) or 'channels' not in data:
        raise RoutingError('Routing map invalid: missing top-level channels object')
    return data


def resolve_channel_id(route_key: str) -> str:
    data = _load_map()
    channels = data.get('channels') or {}
    entry = channels.get(route_key)
    if not entry:
        raise RoutingError(f"Route key not found (fail-closed): {route_key}")
    chat_id = str((entry or {}).get('id', '')).strip()
    if not chat_id:
        raise RoutingError(f"Route key has no channel id (fail-closed): {route_key}")
    return chat_id


def send_route_message(route_key: str, text: str) -> None:
    chat_id = resolve_channel_id(route_key)
    result = subprocess.run(
        ['openclaw', 'message', 'send', '--channel', 'telegram', '--target', chat_id, '--message', text],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        stderr = (result.stderr or '').strip()
        stdout = (result.stdout or '').strip()
        raise RoutingError(
            f"Telegram send failed route={route_key} chat_id={chat_id} rc={result.returncode} "
            f"stderr={stderr} stdout={stdout}"
        )


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 4 or sys.argv[1] != 'send':
        print('Usage: telegram_router.py send <route_key> <message>')
        raise SystemExit(2)

    route = sys.argv[2]
    msg = ' '.join(sys.argv[3:])
    send_route_message(route, msg)
    print(f'sent:{route}')
