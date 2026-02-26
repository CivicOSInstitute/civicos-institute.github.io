---
name: token-saver
description: Model selection with Kimi K2.5 as primary default. Uses K2.5 for all tasks unless context limits exceeded, quotas exhausted, or specific capability gaps. Falls back to other APIs only when necessary, local models as last resort. Use when you want consistent K2.5 usage with intelligent fallback handling.
---

# Token Saver — K2.5 Primary Mode

**Primary Model**: Kimi K2.5 (moonshot/kimi-k2.5) — used for ALL tasks by default.

**Fallback Strategy**:
1. **Kimi K2.5** — Always try first (256K context, strong at everything)
2. **Other APIs** — Only if K2.5 can't handle (context >256K, quota exhausted)
3. **Local models** — Last resort when all APIs unavailable

## Philosophy

**K2.5 First**: This is the designated primary model. Use it unless there's a specific reason not to.
**Minimal Fallback**: Only switch models when K2.5 genuinely can't handle the task.
**Local Last**: Free local models are contingency only, not primary strategy.

## Quick Start

```bash
# Select model (will return K2.5 unless context/quotas exceeded)
token-saver select "Summarize this email"
token-saver select "Debug this code" --tokens 5000

# Long context task (may trigger fallback)
token-saver select "Analyze this 500-page document" --tokens 300000
```

## How It Works

### Selection Priority

```python
SCORING:
- kimi-k2.5: +5000 (dominant priority)
- other APIs: +100 (only if K2.5 fails)
- local models: +50 (last resort)
```

### When Fallback Occurs

K2.5 is NOT used only when:
1. **Context exceeded**: Task needs >256K tokens
2. **Quota exhausted**: Daily/monthly token limit hit
3. **Provider down**: Moonshot API unavailable
4. **Specific gap**: Task requires capability K2.5 lacks (rare)

### Fallback Order

If K2.5 can't handle:
1. **Claude 3.5 Sonnet** — Best all-rounder, 200K context
2. **GPT-4o** — Fast, good at code/vision
3. **Gemini 1.5 Pro** — 2M context for ultra-long docs
4. **Local models** — Only if all APIs fail

## Commands

### Select Model

```bash
token-saver select "<task>" [--tokens <n>] [--background]
```

**Flags:**
- `--tokens <n>`: Estimated token count for context window checking
- `--background`: Allow slow models (Qwen 2.5 Coder 32B) for background tasks

**K2.5 selected** (normal case):
```
🎯 Selected: kimi-k2.5
   Provider: moonshot
   Why: Primary model (K2.5); Strong at code; Can handle MODERATE complexity
```

**Fallback triggered** (rare):
```
🎯 Selected: gemini-1.5-pro
   Provider: google
   Why: Fallback - Gemini 1.5 Pro; K2.5 context limit exceeded (256,000 tokens)
```

### Check Available Models

```bash
token-saver models
```

Shows which models are available and why K2.5 would/wouldn't be selected.

### List Available Models

```bash
token-saver models
```

## Model Registry

### Primary
| Model | Context | Strengths | Fallback Trigger |
|-------|---------|-----------|------------------|
| **kimi-k2.5** | 256K | Everything | Context >256K, quota exhausted |

### Fallback APIs (use only if K2.5 fails)
| Model | Context | Best For |
|-------|---------|----------|
| claude-3-sonnet | 200K | Complex analysis, code |
| gpt-4o | 128K | Speed, vision tasks |
| gemini-1.5-pro | 2M | Ultra-long documents |
| claude-3-opus | 200K | Hardest reasoning tasks |

### Emergency Fallback (local)
| Model | Use When | Speed |
|-------|----------|-------|
| qwen3:14b | All APIs down | fast |
| mistral-small3.2:24b | All APIs down | fast |
| qwen2.5-coder:32b | **Off-peak hours only** | **very slow** |

⚠️ **Qwen 2.5 Coder 32B**: This 32B parameter model runs very slow on MacBook. **Only available during off-peak hours (10 PM - 8 AM)** when more system resources are available. Use `--background` flag to allow selection during these hours.

## Configuration

Stored in `~/.openclaw/token-saver/config.json`:

```json
{
  "primary_model": "kimi-k2.5",
  "fallback_order": ["claude-3-sonnet", "gpt-4o", "gemini-1.5-pro"],
  "local_fallback": true
}
```

## Integration

When using with token-tracker:

```bash
# 1. Select (returns K2.5 99% of time)
MODEL=$(token-saver select "$TASK" --json | jq -r .selected_model)
# → "kimi-k2.5"

# 2. Execute...

# 3. Log usage
token-tracker log moonshot kimi-k2.5 2000 800
```

## Why K2.5 as Primary?

- **256K context**: Handles most documents
- **Fast**: Good throughput
- **Capable**: Strong at code, analysis, chat, research
- **Cost-effective**: $0.002/1K input, $0.008/1K output
- **Reliable**: 91% reliability score

## When NOT to Use This Mode

Use the original local-first token-saver if:
- Budget is extremely constrained (local = $0)
- Running on battery/low power (local = no network)
- Privacy-critical (data can't leave machine)

## Comparison: K2.5 Primary vs Local First

| Scenario | K2.5 Primary | Local First |
|----------|-------------|-------------|
| Simple Q&A | K2.5 | Qwen (local, free) |
| Code review | K2.5 | Qwen/Mistral (local, free) |
| 200K doc analysis | K2.5 | GPT-4o (API, needed for context) |
| Cost/month | ~$10-30 | ~$0-5 |
| Consistency | High (always K2.5) | Variable (depends on task) |
