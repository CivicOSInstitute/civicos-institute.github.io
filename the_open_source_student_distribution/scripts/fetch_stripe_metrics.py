#!/usr/bin/env python3
import base64
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path(os.path.expanduser('~/.openclaw/workspace/the_open_source_student_distribution/output/distribution_metrics.json'))
KEY = os.getenv('STRIPE_SECRET_KEY', '').strip()


def stripe_get(path, params=None):
    if params:
        path = f"{path}?{urllib.parse.urlencode(params)}"
    url = f"https://api.stripe.com{path}"
    token = base64.b64encode(f"{KEY}:".encode()).decode()
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {token}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def load_metrics():
    if OUT.exists():
        try:
            return json.loads(OUT.read_text())
        except Exception:
            pass
    return {
        "last_updated": "",
        "units_sold": 0,
        "channels": [
            {"name": "Gumroad", "revenue": 0, "units": 0, "conversion": "0%"},
            {"name": "Stripe Checkout", "revenue": 0, "units": 0, "conversion": "0%"},
            {"name": "Direct/Manual", "revenue": 0, "units": 0, "conversion": "0%"}
        ]
    }


def main():
    if not KEY:
        print('ERROR: STRIPE_SECRET_KEY not set')
        raise SystemExit(1)

    now = int(time.time())
    since = now - 30 * 24 * 3600

    # Charges are simplest for immediate revenue tracking.
    data = stripe_get('/v1/charges', {'limit': 100, 'created[gte]': since})
    charges = data.get('data', [])

    revenue_cents = 0
    units = 0
    for c in charges:
        if c.get('paid') and not c.get('refunded') and c.get('status') == 'succeeded':
            revenue_cents += int(c.get('amount', 0))
            units += 1

    revenue = round(revenue_cents / 100.0, 2)

    metrics = load_metrics()
    metrics['last_updated'] = time.strftime('%Y-%m-%dT%H:%M:%S%z')

    channels = metrics.get('channels', [])
    found = False
    for ch in channels:
        if (ch.get('name') or '').lower().startswith('stripe'):
            ch['revenue'] = revenue
            ch['units'] = units
            ch['conversion'] = ch.get('conversion', 'n/a')
            found = True
    if not found:
        channels.append({'name': 'Stripe Checkout', 'revenue': revenue, 'units': units, 'conversion': 'n/a'})

    # Optional aggregate units sold from channels
    total_units = 0
    for ch in channels:
        try:
            total_units += int(ch.get('units', 0))
        except Exception:
            pass
    metrics['units_sold'] = total_units
    metrics['channels'] = channels

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(metrics, indent=2) + '\n')
    print(f'OK: Stripe metrics updated. revenue=${revenue} units={units}')


if __name__ == '__main__':
    main()
