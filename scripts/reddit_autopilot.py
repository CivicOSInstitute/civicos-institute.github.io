#!/usr/bin/env python3
"""
Reddit Autopilot (compliant, challenge-aware)

- Uses official Reddit OAuth + API endpoints.
- Runs queued actions (submit post/comment) from JSON.
- Pauses safely on auth/challenge/rate-limit errors.
- Never attempts CAPTCHA bypass.
"""

import argparse
import datetime as dt
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from typing import Dict, Any, Tuple

BASE = pathlib.Path('/Users/AI-OPS/.openclaw/workspace')
DEFAULT_CFG = BASE / 'social_media' / 'reddit_automation_config.json'
DEFAULT_QUEUE = BASE / 'social_media' / 'queue' / 'reddit_queue.json'
LOG_DIR = BASE / 'social_media' / 'analytics'
STATE_PATH = BASE / 'social_media' / 'queue' / 'reddit_state.json'

LOG_DIR.mkdir(parents=True, exist_ok=True)
STATE_PATH.parent.mkdir(parents=True, exist_ok=True)


class PauseRun(Exception):
    pass


def read_json(path: pathlib.Path) -> Dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: pathlib.Path, data: Dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2))


def now_iso() -> str:
    return dt.datetime.now().isoformat(timespec='seconds')


def http_post(url: str, data: Dict[str, Any], headers: Dict[str, str]) -> Tuple[int, Dict[str, Any], str]:
    body = urllib.parse.urlencode(data).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            status = r.getcode()
            text = r.read().decode('utf-8', errors='replace')
            try:
                parsed = json.loads(text)
            except Exception:
                parsed = {}
            return status, parsed, text
    except urllib.error.HTTPError as e:
        raw = e.read().decode('utf-8', errors='replace') if hasattr(e, 'read') else ''
        try:
            parsed = json.loads(raw) if raw else {}
        except Exception:
            parsed = {}
        return e.code, parsed, raw


def get_access_token(cfg: Dict[str, Any]) -> str:
    creds = f"{cfg['client_id']}:{cfg['client_secret']}"
    basic = __import__('base64').b64encode(creds.encode()).decode()
    headers = {
        'Authorization': f'Basic {basic}',
        'User-Agent': cfg['user_agent'],
    }
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': cfg['refresh_token'],
    }
    status, parsed, raw = http_post('https://www.reddit.com/api/v1/access_token', data, headers)
    if status != 200 or 'access_token' not in parsed:
        raise RuntimeError(f'auth_failed status={status} body={raw[:300]}')
    return parsed['access_token']


def reddit_api_post(access_token: str, cfg: Dict[str, Any], endpoint: str, data: Dict[str, Any]):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'User-Agent': cfg['user_agent'],
    }
    return http_post(f'https://oauth.reddit.com{endpoint}', data, headers)


def classify_error(status: int, parsed: Dict[str, Any], raw: str) -> str:
    t = raw.lower()
    if status in (401, 403):
        return 'auth_or_permission'
    if status == 429 or 'ratelimit' in t or 'too many requests' in t:
        return 'rate_limit'
    if 'captcha' in t or 'human verification' in t:
        return 'challenge_required'

    jquery = parsed.get('json', {}) if isinstance(parsed, dict) else {}
    errs = jquery.get('errors', []) if isinstance(jquery, dict) else []
    for e in errs:
        joined = ' '.join(str(x).lower() for x in e)
        if 'captcha' in joined or 'verification' in joined:
            return 'challenge_required'
        if 'ratelimit' in joined:
            return 'rate_limit'

    return 'other'


def submit_post(access_token: str, cfg: Dict[str, Any], item: Dict[str, Any]):
    payload = {
        'api_type': 'json',
        'sr': item['subreddit'],
        'kind': 'self',
        'title': item['title'],
        'text': item['text'],
        'resubmit': item.get('resubmit', False),
        'sendreplies': item.get('sendreplies', True),
    }
    return reddit_api_post(access_token, cfg, '/api/submit', payload)


def submit_comment(access_token: str, cfg: Dict[str, Any], item: Dict[str, Any]):
    payload = {
        'api_type': 'json',
        'thing_id': item['thing_id'],
        'text': item['text'],
    }
    return reddit_api_post(access_token, cfg, '/api/comment', payload)


def load_state() -> Dict[str, Any]:
    if STATE_PATH.exists():
        return read_json(STATE_PATH)
    return {'paused': False, 'reason': '', 'updated_at': now_iso()}


def set_pause(reason: str):
    state = {'paused': True, 'reason': reason, 'updated_at': now_iso()}
    write_json(STATE_PATH, state)


def clear_pause():
    state = {'paused': False, 'reason': '', 'updated_at': now_iso()}
    write_json(STATE_PATH, state)


def run(cfg_path: pathlib.Path, queue_path: pathlib.Path, dry_run: bool):
    cfg = read_json(cfg_path)
    queue = read_json(queue_path)
    state = load_state()

    if state.get('paused'):
        raise PauseRun(f"automation_paused reason={state.get('reason','unknown')}")

    actions = queue.get('actions', [])
    sleep_seconds = int(cfg.get('min_seconds_between_actions', 90))

    results = {
        'started_at': now_iso(),
        'dry_run': dry_run,
        'queue': str(queue_path),
        'processed': [],
        'summary': {'ok': 0, 'failed': 0, 'skipped': 0},
    }

    access_token = None
    if not dry_run:
        access_token = get_access_token(cfg)

    for idx, item in enumerate(actions):
        action_id = item.get('id', f'action-{idx+1}')
        action_type = item.get('type')

        if item.get('status') == 'done':
            results['summary']['skipped'] += 1
            results['processed'].append({'id': action_id, 'status': 'skipped_done'})
            continue

        if dry_run:
            results['summary']['ok'] += 1
            results['processed'].append({'id': action_id, 'status': 'dry_run_ok', 'type': action_type})
            continue

        if action_type == 'post':
            status, parsed, raw = submit_post(access_token, cfg, item)
        elif action_type == 'comment':
            status, parsed, raw = submit_comment(access_token, cfg, item)
        else:
            results['summary']['failed'] += 1
            results['processed'].append({'id': action_id, 'status': 'failed', 'reason': 'unknown_type'})
            continue

        if status == 200 and not parsed.get('json', {}).get('errors'):
            results['summary']['ok'] += 1
            item['status'] = 'done'
            item['completed_at'] = now_iso()
            results['processed'].append({'id': action_id, 'status': 'ok', 'type': action_type})
        else:
            classification = classify_error(status, parsed, raw)
            results['summary']['failed'] += 1
            results['processed'].append({
                'id': action_id,
                'status': 'failed',
                'type': action_type,
                'http_status': status,
                'classification': classification,
                'body_preview': raw[:240],
            })

            if classification in ('challenge_required', 'auth_or_permission'):
                set_pause(classification)
                raise PauseRun(f'paused_due_to={classification} action_id={action_id}')

        if idx < len(actions) - 1:
            time.sleep(sleep_seconds)

    write_json(queue_path, queue)
    clear_pause()
    results['finished_at'] = now_iso()
    return results


def write_log(result: Dict[str, Any]) -> pathlib.Path:
    ts = dt.datetime.now().strftime('%Y%m%d_%H%M%S')
    path = LOG_DIR / f'reddit_autopilot_{ts}.json'
    write_json(path, result)
    write_json(LOG_DIR / 'reddit_autopilot_latest.json', result)
    return path


def main():
    ap = argparse.ArgumentParser(description='Run Reddit automation queue with challenge-aware safety pauses.')
    ap.add_argument('--config', default=str(DEFAULT_CFG))
    ap.add_argument('--queue', default=str(DEFAULT_QUEUE))
    ap.add_argument('--dry-run', action='store_true', help='Validate queue and simulate submissions without API calls')
    args = ap.parse_args()

    cfg_path = pathlib.Path(args.config)
    queue_path = pathlib.Path(args.queue)

    if not cfg_path.exists():
        print(f'ERROR: missing config: {cfg_path}', file=sys.stderr)
        return 2
    if not queue_path.exists():
        print(f'ERROR: missing queue: {queue_path}', file=sys.stderr)
        return 2

    try:
        result = run(cfg_path, queue_path, args.dry_run)
        log_path = write_log(result)
        print(json.dumps({'ok': True, 'log': str(log_path), 'summary': result.get('summary', {})}, indent=2))
        return 0
    except PauseRun as e:
        result = {'ok': False, 'paused': True, 'reason': str(e), 'at': now_iso()}
        log_path = write_log(result)
        print(json.dumps({'ok': False, 'paused': True, 'reason': str(e), 'log': str(log_path)}, indent=2))
        return 3
    except Exception as e:
        result = {'ok': False, 'paused': False, 'error': str(e), 'at': now_iso()}
        log_path = write_log(result)
        print(json.dumps({'ok': False, 'error': str(e), 'log': str(log_path)}, indent=2))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
