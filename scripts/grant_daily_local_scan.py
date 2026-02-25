#!/usr/bin/env python3
"""
Daily grant opportunity scan.
Primary path: local Ollama queue (serialized via ollama-agent-queue).
Fallback path: API model via `openclaw agent --local --agent main`.
Outputs a markdown brief to generated/grants/.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

WORKSPACE = Path('/Users/AI-OPS/.openclaw/workspace')
OUT_DIR = WORKSPACE / 'generated' / 'grants'
OUT_DIR.mkdir(parents=True, exist_ok=True)

SOURCES = [
    ("Grants.gov - Community Development", "https://www.grants.gov/web/grants/search-grants.html?keywords=community+development"),
    ("Grants.gov - Civic Engagement", "https://www.grants.gov/web/grants/search-grants.html?keywords=civic+engagement"),
    ("Candid RFP Bulletin", "https://philanthropynewsdigest.org/rfps"),
    ("Knight Foundation", "https://knightfoundation.org/grants/"),
    ("Craig Newmark Philanthropies", "https://craignewmarkphilanthropies.org/"),
    ("MacArthur - Grantmaking", "https://www.macfound.org/programs"),
    ("NEA Grants", "https://www.arts.gov/grants"),
    ("Florida Division of Emergency Management Grants", "https://www.floridadisaster.org/grants/"),
    ("Palm Beach County Grants", "https://discover.pbcgov.org/coextension/human-sciences/Pages/Grant-Opportunities.aspx"),
]


def fetch_text(url: str) -> str:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (GrantScanner/1.0)"})
    with urlopen(req, timeout=20) as r:
        raw = r.read().decode('utf-8', errors='ignore')

    # Remove script/style blocks and tags for a compact text snapshot
    raw = re.sub(r"<script[\\s\\S]*?</script>", " ", raw, flags=re.I)
    raw = re.sub(r"<style[\\s\\S]*?</style>", " ", raw, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:12000]


def build_prompt(snapshot: dict) -> str:
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    sources_blob = "\n\n".join(
        f"SOURCE: {name}\nURL: {url}\nTEXT:\n{text}"
        for name, url, text in snapshot["pages"]
    )

    return f"""
You are a grants analyst for CivicOS Institute (civic tech nonprofit in formation).
Timestamp: {now}

Task:
1) Extract likely active grant/funding opportunities from the source text.
2) Prioritize fit for civic technology, democracy, local government innovation, digital public infrastructure, community engagement, education, and nonprofit capacity building.
3) Ignore obvious duplicates and stale/closed opportunities when possible.
4) Produce concise markdown with this exact structure:

# Daily Grant Scan
## Top Opportunities (max 8)
- Opportunity Name
  - Source: <name>
  - URL: <url>
  - Why it fits CivicOS: <1 line>
  - Estimated deadline: <date or unknown>
  - Confidence: High/Medium/Low

## Watchlist (max 8)
- ...same fields...

## Fast Actions (next 24h)
- 3-6 bullets focused on practical actions.

## Notes
- Mention missing/uncertain data briefly.

Only use info grounded in provided source text.

SOURCE TEXT:
{sources_blob}
""".strip()


def run_local_model(prompt: str) -> str:
    helper = WORKSPACE / 'skills' / 'ollama-agent-queue' / 'scripts' / 'integration_helper.py'
    proc = subprocess.run(
        [
            'python3', str(helper),
            '--calling-skill', 'grant-daily-scan',
            '--model', 'local/qwen-14b',
            '--priority', 'high',
            '--system-prompt', 'You are a precise grants analyst. Return only the requested markdown report.',
            '--user-prompt', prompt,
            '--max-tokens', '1400',
            '--timeout-seconds', '420',
            '--poll-seconds', '3',
        ],
        text=True,
        capture_output=True,
        timeout=480,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or 'queue helper failed')

    try:
        payload = json.loads(proc.stdout.strip())
    except Exception as e:
        raise RuntimeError(f'queue result parse failed: {e}')

    status = payload.get('status')
    if status != 'complete':
        raise RuntimeError(f'local queue returned status={status}')

    result = (payload.get('result') or '').strip()
    if not result:
        raise RuntimeError('local queue returned empty result')
    return result


def run_api_fallback(prompt: str) -> str:
    api_prompt = (
        'Return only markdown using this exact structure: '\
        '# Daily Grant Scan, ## Top Opportunities (max 8), ## Watchlist (max 8), '\
        '## Fast Actions (next 24h), ## Notes.\\n\\n' + prompt
    )
    proc = subprocess.run(
        [
            'openclaw', 'agent', '--local', '--agent', 'main',
            '--message', api_prompt,
            '--json', '--timeout', '420'
        ],
        text=True,
        capture_output=True,
        timeout=500,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or 'api fallback failed')

    try:
        data = json.loads(proc.stdout)
        text = data['payloads'][0]['text'].strip()
    except Exception as e:
        raise RuntimeError(f'api fallback parse failed: {e}')

    if not text:
        raise RuntimeError('api fallback returned empty text')
    return text


def main() -> int:
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    pages = []
    errors = []

    for name, url in SOURCES:
        try:
            text = fetch_text(url)
            pages.append((name, url, text))
        except Exception as e:
            errors.append({"source": name, "url": url, "error": str(e)})

    snapshot = {"generated_at": ts, "pages": pages, "errors": errors}
    raw_path = OUT_DIR / f'grant-scan-raw-{ts}.json'
    raw_path.write_text(json.dumps(snapshot, indent=2))

    if not pages:
        report = "# Daily Grant Scan\n\nNo sources were fetched successfully."
    else:
        prompt = build_prompt(snapshot)
        try:
            report = run_local_model(prompt)
        except Exception as local_err:
            try:
                report = run_api_fallback(prompt)
                report += f"\n\n## Model Routing\n- Primary: local queue (local/qwen-14b) failed\n- Fallback: API model succeeded\n- Primary error: {local_err}"
            except Exception as api_err:
                report = (
                    "# Daily Grant Scan\n\n"
                    f"Primary local queue failed: {local_err}\n\n"
                    f"Fallback API model failed: {api_err}\n\n"
                    f"Fetched sources: {len(pages)}"
                )

    if errors:
        report += "\n\n## Fetch Errors\n" + "\n".join(
            f"- {e['source']}: {e['error']}" for e in errors
        )

    report_path = OUT_DIR / f'grant-scan-{ts}.md'
    latest_path = OUT_DIR / 'grant-scan-latest.md'
    report_path.write_text(report)
    latest_path.write_text(report)

    print(str(report_path))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
