#!/usr/bin/env python3
"""Validate router telemetry and produce a clean dataset for downstream analysis."""
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path

REQUIRED={"ts","task_id","route_tier","classifier_score","cache_hit","compression_ratio","input_tokens","output_tokens","cost_usd","latency_ms","quality_flag"}
TIERS={"T0","T1","T2"}


def is_valid(r):
    try:
        if not REQUIRED.issubset(r.keys()): return False, 'missing_fields'
        if r["route_tier"] not in TIERS: return False, 'bad_tier'
        datetime.fromisoformat(r["ts"])
        cs=float(r["classifier_score"])
        cr=float(r["compression_ratio"])
        it=int(r["input_tokens"]); ot=int(r["output_tokens"]); lat=int(r["latency_ms"])
        cost=float(r["cost_usd"])
        if not (0 <= cs <= 1): return False, 'bad_classifier_score'
        if not (0 < cr <= 1.2): return False, 'bad_compression_ratio'
        if min(it,ot,lat,cost) < 0: return False, 'negative_values'
        if it+ot == 0: return False, 'zero_tokens'
        if lat > 120000: return False, 'latency_outlier'
        return True, 'ok'
    except Exception:
        return False, 'parse_error'


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',default='data/telemetry/router_telemetry.jsonl')
    ap.add_argument('--clean-out',default='data/telemetry/router_telemetry.clean.jsonl')
    ap.add_argument('--reject-out',default='data/telemetry/router_telemetry.rejects.jsonl')
    ap.add_argument('--summary-out',default='generated/efficiency/telemetry_quality_latest.json')
    args=ap.parse_args()

    inp=Path(args.input); clean=Path(args.clean_out); rej=Path(args.reject_out); summary=Path(args.summary_out)
    clean.parent.mkdir(parents=True,exist_ok=True); rej.parent.mkdir(parents=True,exist_ok=True); summary.parent.mkdir(parents=True,exist_ok=True)

    total=valid=invalid=0
    reasons={}
    if inp.exists():
        with inp.open('r',encoding='utf-8') as fi, clean.open('w',encoding='utf-8') as fc, rej.open('w',encoding='utf-8') as fr:
            for line in fi:
                if not line.strip():
                    continue
                total+=1
                try:
                    r=json.loads(line)
                except Exception:
                    invalid+=1
                    reasons['parse_error']=reasons.get('parse_error',0)+1
                    fr.write(json.dumps({'reason':'parse_error','raw':line.strip()})+'\n')
                    continue
                ok,reason=is_valid(r)
                if ok:
                    valid+=1
                    fc.write(json.dumps(r,ensure_ascii=False)+'\n')
                else:
                    invalid+=1
                    reasons[reason]=reasons.get(reason,0)+1
                    fr.write(json.dumps({'reason':reason,'record':r},ensure_ascii=False)+'\n')

    quality_pct=(valid/total*100) if total else 0
    out={
        'generated_at':datetime.now(timezone.utc).isoformat(),
        'input_file':str(inp),
        'total_rows':total,
        'valid_rows':valid,
        'invalid_rows':invalid,
        'quality_pass_rate_pct':round(quality_pct,2),
        'rejection_reasons':reasons,
        'clean_file':str(clean),
        'reject_file':str(rej)
    }
    summary.write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(json.dumps(out,indent=2))

if __name__=='__main__':
    main()
