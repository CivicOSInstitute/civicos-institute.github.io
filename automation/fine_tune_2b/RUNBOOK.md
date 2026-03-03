# Fine-Tune Mission Runbook (2+2 Waves)

## Objective
Ship four Qwen3.5-2B specialist adapters with strict quality gates and local-first router integration.

## Wave Order
- Wave 1: outreach_writer_2b, ops_formatter_2b
- Wave 2: grant_analyst_2b, policy_qa_guard_2b

## Nightly Window
- 1:00 AM - 6:30 AM America/New_York

## Execution Steps (Nightly)
1. Read `config/mission_plan.json`.
2. Run only specialists in `active_wave`.
3. For each specialist:
   - dataset prep
   - LoRA train
   - eval
   - write manifest/report
4. Build `deploy/router_map.json`.
5. Sync to `skills/model-router/config/specialist_adapters.json`.
6. Log run summary to `logs/offhours_train.log`.

## Promotion Gate
Per specialist must pass:
- task_score >= threshold
- format_valid_rate >= 0.97
- hallucination_rate <= 0.08
- latency_p95 <= 4.0s

## Wave Advancement
Advance to next wave only when all specialists in current wave have `pass: true` in eval reports.

## Rollback
If any specialist fails gate:
- keep previous router map
- do not promote failing adapter
- retrain next off-hours window with targeted data fixes
