#!/usr/bin/env python3
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path(os.path.expanduser('~/.openclaw/workspace/the_open_source_student_distribution/output/distribution_metrics.json'))
API_KEY = os.getenv('LEMONSQUEEZY_API_KEY', '').strip()
STORE_ID = os.getenv('LEMONSQUEEZY_STORE_ID', '').strip()


def ls_get(path, params=None):
    if params:
        path = f"{path}?{urllib.parse.urlencode(params)}"
    url = f"https://api.lemonsqueezy.com/v1{path}"
    req = urllib.request.Request(
        url,
        headers={
            'Authorization': f'Bearer {API_KEY}',
            'Accept': 'application/vnd.api+json',
            'Content-Type': 'application/vnd.api+json',
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def load_metrics():
    if OUT.exists():
        try:
            return json.loads(OUT.read_text())
        except Exception:
            pass
    return {
        'last_updated': '',
        'units_sold': 0,
        'channels': [
            {'name': 'Lemon Squeezy', 'revenue': 0, 'units': 0, 'conversion': '0%'},
            {'name': 'Stripe Checkout', 'revenue': 0, 'units': 0, 'conversion': '0%'},
            {'name': 'Direct/Manual', 'revenue': 0, 'units': 0, 'conversion': '0%'},
        ],
    }


def parse_revenue_amount(order_attr):
    # LemonSqueezy often returns totals in integer cents as strings.
    for key in ('total', 'subtotal', 'grand_total'):
        v = order_attr.get(key)
        if v is not None:
            try:
                iv = int(str(v))
                return iv / 100.0
            except Exception:
                pass
    # fallback if already decimal string
    for key in ('total_usd', 'subtotal_usd'):
        v = order_attr.get(key)
        if v is not None:
            try:
                return float(str(v))
            except Exception:
                pass
    return 0.0


def main():
    if not API_KEY:
        print('ERROR: LEMONSQUEEZY_API_KEY not set')
        raise SystemExit(1)

    params = {'page[size]': 100}
    if STORE_ID:
        params['filter[store_id]'] = STORE_ID

    payload = ls_get('/orders', params)
    orders = payload.get('data', [])

    revenue = 0.0
    units = 0

    for o in orders:
        attr = o.get('attributes', {})
        status = (attr.get('status') or '').lower()
        if status and status not in ('paid', 'refunded', 'partially_refunded'):
            # ignore pending/failed
            continue

        rev = parse_revenue_amount(attr)
        # naive handling: refunded states still included if API already nets totals.
        revenue += rev
        units += 1

    revenue = round(revenue, 2)

    metrics = load_metrics()
    metrics['last_updated'] = time.strftime('%Y-%m-%dT%H:%M:%S%z')

    channels = metrics.get('channels', [])
    found = False
    for ch in channels:
        if (ch.get('name') or '').lower().startswith('lemon squeezy'):
            ch['revenue'] = revenue
            ch['units'] = units
            ch['conversion'] = ch.get('conversion', 'n/a')
            found = True
    if not found:
        channels.append({'name': 'Lemon Squeezy', 'revenue': revenue, 'units': units, 'conversion': 'n/a'})

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
    print(f'OK: Lemon Squeezy metrics updated. revenue=${revenue} units={units}')


if __name__ == '__main__':
    main()
