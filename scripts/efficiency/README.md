# Efficiency Telemetry Toolkit

## Log one routing event
```bash
python3 scripts/efficiency/router_telemetry_logger.py \
  --task-id task-001 --tier T2 --classifier-score 0.74 --cache-hit false \
  --compression-ratio 0.18 --input-tokens 3200 --output-tokens 640 \
  --cost-usd 0.0081 --latency-ms 1430 --quality-flag pass
```

## Build rolling 24h report
```bash
python3 scripts/efficiency/build_efficiency_report.py --hours 24
```

Outputs:
- `generated/efficiency/router_efficiency_latest.json`
- `generated/efficiency/router_efficiency_latest.md`
