# MODEL_ROUTING_MATRIX.md

CivicOS Institute — Council Seat Routing Addendum  
Version: 1.2  
Last updated: 2026-02-27

## Council Seat Model Map

| Seat | Advisor | Role | Primary Model | Fallback | Notes |
|------|---------|------|--------------|----------|-------|
| 1 | Magnus | Execution realism | mistral-small3.2:24b | qwen2.5:14b | Low-hallucination, grounded pushback. Resists plausible-but-false plans. |
| 2 | Vera | Systems effects | qwen3:14b | Kimi | Hybrid thinking mode handles dependency tracing well. Kimi fallback for high-context load. |
| 3 | Dante | Adversarial challenge | GPT-4o *(API)* | Groq-Llama | Requires willingness to construct a coherent counter-case, not just flag uncertainty. Local models soften this seat. |
| 4 | Eleanor | Ethics/values | GPT-4o *(API)* | Codex | Needs to hold competing frameworks without collapsing. Local models soften this seat. |
| 5 | Ray | Historical patterns | qwen3:14b | Gemini | Broad pattern retrieval. Qwen 3 upgrade from 2.5 for better instruction following. Gemini fallback for deep historical synthesis. |
| 6 | Mira | Simplification/scope discipline | mistral-small3.2:24b | qwen2.5:14b | Mira's job is to cut. Leaner model with strong instruction-following. Do NOT use Qwen 3 here without pinning `thinking: false` — elaboration defeats the seat. |
| 7 | Burt | Synthesis / final authority | Codex | GPT-4o | Highest reasoning ceiling in stack. Receives full six-seat outputs uncompressed. |

### Privacy override for fully sensitive sessions

If session content is privacy-sensitive, substitute:
- Seat 3 (Dante): qwen3:14b
- Seat 4 (Eleanor): qwen3:14b

Note in session record: *"Adversarial and ethics coverage degraded — local privacy override applied."*

---

## Installed Local Models (reference)

| Model | Alias | Best fit |
|-------|-------|----------|
| qwen3:14b | Qwen3 | General reasoning, systems analysis, pattern retrieval, formatting |
| qwen2.5:14b | Qwen | Reliable fallback, brevity-biased tasks |
| qwen2.5-coder:32b-instruct-q3_K_L | Qwen-Coder | Code generation, debugging, refactors |
| mistral-small3.2:24b-instruct-2506-q4_K_M | Mistral | Grounded realism, summarization, scope-reduction tasks |

---

## API Model Aliases (reference)

| Alias | Model string |
|-------|-------------|
| Codex | openai-codex/gpt-5.3-codex |
| Gemini | google/gemini-2.0-flash |
| GPT-3.5 | openai/gpt-3.5-turbo |
| GPT-4-Turbo | openai/gpt-4-turbo |
| GPT-4o | openai/gpt-4o |
| GPT-4o-Mini | openai/gpt-4o-mini |
| Groq-Fast | groq/llama-3.1-8b-instant |
| Groq-Llama | groq/llama-3.3-70b-versatile |
| Groq-Mixtral | groq/mixtral-8x7b-32768 |
| Kimi | moonshot/kimi-k2.5 |

---

## Policy Control

Router should consume this file as **read-only policy**.  
Changes to routing policy go through document edit with timestamp — not config tweaks in code.
