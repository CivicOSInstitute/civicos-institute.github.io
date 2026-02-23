#!/usr/bin/env python3
import csv
import json
import os
from pathlib import Path
from datetime import datetime

# Placeholder sync: reads CSV export dropped by user from KDP reports.
# Expected columns (flexible): earnings/revenue, units/orders
CSV_PATH = Path(os.path.expanduser('~/.openclaw/workspace/the_open_source_student_distribution/output/imports/amazon_kdp_report.csv'))
OUT = Path(os.path.expanduser('~/.openclaw/workspace/the_open_source_student_distribution/output/distribution_metrics.json'))


def load_metrics():
    if OUT.exists():
        try:
            return json.loads(OUT.read_text())
        except Exception:
            pass
    return {'last_updated': '', 'units_sold': 0, 'channels': []}


def to_float(v):
    try:
        return float(str(v).replace('$', '').replace(',', '').strip())
    except Exception:
        return 0.0


def to_int(v):
    try:
        return int(float(str(v).strip()))
    except Exception:
        return 0


def main():
    if not CSV_PATH.exists():
        print('INFO: amazon_kdp_report.csv not found, skipping')
        return

    revenue = 0.0
    units = 0
    with open(CSV_PATH, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            lower = {k.lower(): v for k, v in row.items()}
            revenue += to_float(lower.get('revenue') or lower.get('earnings') or lower.get('royalty') or 0)
            units += to_int(lower.get('units') or lower.get('orders') or lower.get('quantity') or 0)

    metrics = load_metrics()
    channels = metrics.get('channels', [])
    found = False
    for ch in channels:
        if (ch.get('name') or '').lower().startswith('amazon kdp'):
            ch['revenue'] = round(revenue, 2)
            ch['units'] = units
            ch['conversion'] = ch.get('conversion', 'n/a')
            found = True
    if not found:
        channels.append({'name': 'Amazon KDP', 'revenue': round(revenue, 2), 'units': units, 'conversion': 'n/a'})

    metrics['channels'] = channels
    metrics['units_sold'] = sum(int(c.get('units', 0) or 0) for c in channels)
    metrics['last_updated'] = datetime.now().astimezone().isoformat(timespec='seconds')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(metrics, indent=2) + '\n')
    print(f'OK: Amazon KDP metrics updated. revenue=${revenue:.2f} units={units}')


if __name__ == '__main__':
    main()
