# Memory Hardening Upgrades (Phase 1)

Implemented:
1. Pre-switch checkpoint: `scripts/memory_checkpoint.py`
2. Structured decision log: `scripts/decision_log.py`
3. Local query fallback: `scripts/memory_query.py`
4. Task-state journal: `scripts/state_journal.py`

Quick use:
```bash
python3 scripts/memory_checkpoint.py --objective "Finish KDP" --next-step "Set pricing" --state "on pricing tab"
python3 scripts/decision_log.py --context "KDP format" --chosen "Use EPUB" --why "Portability + current assets"
python3 scripts/state_journal.py --project kdp_founders --status pricing_pending --next "Set to 179 and save"
python3 scripts/memory_query.py "KDP pricing founders"
```
