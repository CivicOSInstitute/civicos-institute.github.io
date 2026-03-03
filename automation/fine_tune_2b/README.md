# 2B Specialist Adapter Factory (Qwen 3.5-2B)

Goal: run 4 narrow local specialists with shared automation for data prep, LoRA fine-tuning, eval gates, and deployment routing.

## Specialists
1. outreach_writer_2b
2. grant_analyst_2b
3. ops_formatter_2b
4. policy_qa_guard_2b

## Pipeline
1. Build dataset from approved examples (`data/<specialist>/raw/*.jsonl`)
2. Normalize to instruction format (`datasets/<specialist>_train.jsonl`)
3. Fine-tune LoRA adapter (`adapters/<specialist>/`)
4. Evaluate against holdout + rubric (`eval/<specialist>_report.json`)
5. Promote only if gate passes (`quality >= threshold`)
6. Export runtime manifest (`deploy/manifests/<specialist>.json`)
7. Update router map (`deploy/router_map.json`)

## Success Gates (default)
- format_valid_rate >= 0.97
- task_score >= 0.85
- hallucination_rate <= 0.08
- latency_p95 <= 4.0s (local target)

## Run
```bash
cd /Users/AI-OPS/.openclaw/workspace
python3 automation/fine_tune_2b/scripts/orchestrate.py --all
# or
python3 automation/fine_tune_2b/scripts/orchestrate.py --specialist outreach_writer_2b
```

## Notes
- Uses LoRA/QLoRA approach (not full retrain).
- Keeps base model fixed, swaps adapters per task.
- Designed for local-first routing + low token burn.
