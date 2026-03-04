#!/usr/bin/env python3
"""
AI Request Router - Routes all requests through lightweight model first
Uses Llama 3.1 8B to decide: local handling vs API escalation
"""
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional

# Model definitions
LOCAL_MODEL = "phi3:mini"  # Lightweight classifier - 3x faster, 2x smaller
ESCALATION_MODELS = {
    "coding_complex": "openai-codex/gpt-5.3-codex",  # Complex architecture
    "reasoning_complex": "moonshot/kimi-k2.5",       # Multi-step reasoning
    "long_context": "moonshot/kimi-k2.5",            # >32K tokens
    "creative_polish": "openai/gpt-4o",              # Final polish
    "qwen_cloud": "qwen3.5:cloud",                   # Qwen 3.5 Cloud (limited use)
}
LOCAL_SPECIALISTS = {
    "coding_simple": "deepseek-coder:6.7b",
    "writing": "llama3.1:8b",
    "chat": "llama3.1:8b",
    "qa": "qwen3:14b",
}

SPECIALIST_CONFIG = Path("/Users/AI-OPS/.openclaw/workspace/skills/model-router/config/specialist_adapters.json")
MLX_PYTHON = "/Users/AI-OPS/.openclaw/workspace/.venv-finetune/bin/python"
MLX_BASE_MODEL = "mlx-community/Qwen2.5-1.5B-Instruct-4bit"

SPECIALIST_KEYWORDS = {
    "policy_qa_guard_2b": ["policy", "compliance", "guardrail", "risk", "tone review", "pass/fail", "review this"],
    "grant_analyst_2b": ["grant", "funder", "rfp", "eligibility", "deadline", "foundation"],
    "outreach_writer_2b": ["outreach", "subject line", "follow-up email", "cold email"],
    "ops_formatter_2b": ["format", "structured json", "normalize", "schema"],
}

# Economy policy: keep paid usage for final QA and truly complex tasks only.
QA_ONLY_GATE = os.getenv("ROUTER_QA_ONLY_GATE", "1") == "1"
FORCE_ESCALATE_TAGS = ["use codex", "use kimi", "api override", "premium model"]
MEDIUM_PRIORITY_TAGS = ["medium priority", "priority: medium", "[medium]", "med priority"]
URGENT_PRIORITY_TAGS = ["urgent", "priority: urgent", "[urgent]", "critical", "p0"]


def wants_force_escalation(prompt: str) -> bool:
    p = (prompt or "").lower()
    return any(tag in p for tag in FORCE_ESCALATE_TAGS)


def get_priority(prompt: str) -> str:
    p = (prompt or "").lower()
    if any(tag in p for tag in URGENT_PRIORITY_TAGS):
        return "urgent"
    if any(tag in p for tag in MEDIUM_PRIORITY_TAGS):
        return "medium"
    return "low"


def is_extremely_complex(prompt: str) -> bool:
    p = (prompt or "").lower()
    if len(p) > 8000:
        return True
    complexity_signals = [
        "multi-service architecture",
        "distributed system",
        "threat model",
        "formal verification",
        "incident postmortem",
        "deep debugging",
        "end-to-end migration plan",
    ]
    return any(sig in p for sig in complexity_signals)

def load_specialist_map() -> Dict[str, Dict]:
    try:
        if not SPECIALIST_CONFIG.exists():
            return {}
        data = json.loads(SPECIALIST_CONFIG.read_text())
        out = {}
        for s in data.get("specialists", []):
            if s.get("status") == "promoted":
                out[s["id"]] = s
        return out
    except Exception:
        return {}


def pick_specialist(prompt: str) -> Optional[str]:
    p = (prompt or "").lower()
    for sid, keys in SPECIALIST_KEYWORDS.items():
        if any(k in p for k in keys):
            return sid
    return None


def passes_specialist_guard(output: str, specialist_id: str) -> bool:
    t = (output or "").lower()
    if not t:
        return False
    if specialist_id == "policy_qa_guard_2b":
        return ("pass" in t or "fail" in t) and ("risk" in t or "fix" in t)
    if specialist_id == "grant_analyst_2b":
        return "fit score" in t or "30-day" in t or "deadline" in t
    return True


def execute_mlx_specialist(prompt: str, specialist_id: str, specialist_map: Dict[str, Dict]) -> Optional[str]:
    spec = specialist_map.get(specialist_id)
    if not spec:
        return None
    adapter = spec.get("adapter_path")
    if not adapter or not Path(adapter).exists():
        return None
    if not Path(MLX_PYTHON).exists():
        return None

    try:
        cmd = [
            MLX_PYTHON,
            "-m",
            "mlx_lm",
            "generate",
            "--model",
            MLX_BASE_MODEL,
            "--adapter-path",
            adapter,
            "--prompt",
            prompt,
            "--max-tokens",
            "900",
            "--temp",
            "0.2",
            "--verbose",
            "false",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if res.returncode != 0:
            return None
        out = (res.stdout or "").strip()
        if "==========" in out:
            out = out.split("==========")[-1].strip()
        if not passes_specialist_guard(out, specialist_id):
            return None
        return out or None
    except Exception:
        return None


def classify_request(prompt: str) -> Dict:
    """Classify request with lightweight guards before model-based routing."""
    p = (prompt or "").strip()
    p_lower = p.lower()

    specialist_map = load_specialist_map()
    specialist_id = pick_specialist(p)
    if specialist_id and specialist_id in specialist_map:
        return {
            "route": "local_specialist",
            "model": specialist_id,
            "reason": f"Specialist keyword match -> {specialist_id}",
        }

    # Fast-path heuristics to avoid unnecessary classifier calls.
    if len(p) <= 120 and any(k in p_lower for k in ["weather", "time", "date", "what is", "who is", "explain"]):
        return {"route": "local", "model": LOCAL_SPECIALISTS["qa"], "reason": "Heuristic: short factual query"}

    if len(p) <= 220 and any(k in p_lower for k in ["write", "draft", "email", "rewrite", "summarize"]):
        return {"route": "local", "model": LOCAL_SPECIALISTS["writing"], "reason": "Heuristic: short writing task"}

    # Hard guardrail for long prompts: avoid classifier ambiguity and route directly.
    if len(p) > 4000:
        return {"route": "escalate", "model": ESCALATION_MODELS["long_context"], "reason": "Prompt length > 4k chars"}

    classification_prompt = f"""Analyze this request and classify it:

Request: "{p[:500]}"

Classify as ONE of:
- "local_chat" - General conversation, simple questions
- "local_writing" - Emails, copy, content creation  
- "local_coding" - Simple code, scripts, functions
- "local_qa" - Factual questions, explanations
- "escalate_coding" - Complex architecture, system design, debugging
- "escalate_reasoning" - Multi-step math, logic puzzles, analysis
- "escalate_creative" - Needs premium creative polish
- "escalate_long" - Will need >32K context
- "escalate_qwen_cloud" - Qwen 3.5 Cloud for specific high-quality needs (limited use)

Respond ONLY with the classification code."""

    try:
        result = subprocess.run(
            ["ollama", "run", LOCAL_MODEL],
            input=classification_prompt,
            capture_output=True,
            text=True,
            timeout=30
        )
        classification = result.stdout.strip().lower()
        
        # Parse classification
        if "escalate_coding" in classification:
            return {"route": "escalate", "model": ESCALATION_MODELS["coding_complex"], "reason": "Complex coding task"}
        elif "escalate_reasoning" in classification:
            return {"route": "escalate", "model": ESCALATION_MODELS["reasoning_complex"], "reason": "Complex reasoning required"}
        elif "escalate_creative" in classification:
            return {"route": "escalate", "model": ESCALATION_MODELS["creative_polish"], "reason": "Premium creative output needed"}
        elif "escalate_long" in classification:
            return {"route": "escalate", "model": ESCALATION_MODELS["long_context"], "reason": "Long context required"}
        elif "escalate_qwen_cloud" in classification:
            return {"route": "escalate", "model": ESCALATION_MODELS["qwen_cloud"], "reason": "Qwen 3.5 Cloud - limited use"}
        elif "local_coding" in classification:
            return {"route": "local", "model": LOCAL_SPECIALISTS["coding_simple"], "reason": "Simple coding - local OK"}
        elif "local_writing" in classification:
            return {"route": "local", "model": LOCAL_SPECIALISTS["writing"], "reason": "Writing task - local OK"}
        elif "local_qa" in classification:
            return {"route": "local", "model": LOCAL_SPECIALISTS["qa"], "reason": "Q&A - local OK"}
        else:
            return {"route": "local", "model": LOCAL_SPECIALISTS["chat"], "reason": "General chat - local OK"}
            
    except Exception as e:
        # Cost-safe fallback: stay local on classifier failure unless explicitly long-context.
        if len(p) > 4000:
            return {"route": "escalate", "model": ESCALATION_MODELS["long_context"], "reason": f"Classifier error + long input: {e}"}
        return {"route": "local", "model": LOCAL_SPECIALISTS["qa"], "reason": f"Classifier error -> local fallback: {e}"}

def execute_local(prompt: str, model: str) -> str:
    """Execute with local Ollama model"""
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        return "[Local model timeout - escalating to API]"
    except Exception as e:
        return f"[Local error: {e} - escalating to API]"

def route_request(prompt: str) -> Dict:
    """Main routing function."""
    # Step 1: Classify
    routing = classify_request(prompt)

    # Step 2: Economy policy gate before execution.
    if routing["route"] == "escalate" and QA_ONLY_GATE:
        force_escalate = wants_force_escalation(prompt)
        complex_ok = is_extremely_complex(prompt)
        priority = get_priority(prompt)

        # Hard rule: default LOW unless user tags MEDIUM/URGENT.
        # LOW blocks paid escalation unless explicit model override is requested.
        if priority == "low" and not force_escalate:
            routing = {
                "route": "local",
                "model": LOCAL_SPECIALISTS["qa"],
                "reason": f"Priority default LOW -> escalation blocked ({routing.get('reason', 'policy')})",
                "qa_review_recommended": False,
                "priority": priority,
            }
        # MEDIUM/URGENT may escalate for true complexity or explicit override.
        elif not (force_escalate or complex_ok or priority in {"medium", "urgent"}):
            routing = {
                "route": "local",
                "model": LOCAL_SPECIALISTS["qa"],
                "reason": f"QA-only gate held escalation ({routing.get('reason', 'policy')})",
                "qa_review_recommended": True,
                "priority": priority,
            }
        else:
            routing["priority"] = priority

    # Step 3: Execute
    if routing["route"] == "local_specialist":
        specialist_map = load_specialist_map()
        output = execute_mlx_specialist(prompt, routing["model"], specialist_map)
        if output:
            routing["output"] = output
            routing["cost"] = "$0.00"
        else:
            # Safe fallback to local QA model if adapter invocation fails.
            fallback_model = LOCAL_SPECIALISTS["qa"]
            routing["route"] = "local"
            routing["reason"] = f"Specialist unavailable/failed quality guard; fallback -> {fallback_model}"
            routing["model"] = fallback_model
            if routing.get("model") == "policy_qa_guard_2b" or "policy" in prompt.lower() or "pass/fail" in prompt.lower():
                guarded_prompt = (
                    "Review for policy/tone risks. Return exactly sections: RESULT (PASS or FAIL), "
                    "RISKS (bullets), FIXES (bullets), REWRITE (short).\n\n"
                    + prompt
                )
                routing["output"] = execute_local(guarded_prompt, fallback_model)
            else:
                routing["output"] = execute_local(prompt, fallback_model)
            routing["cost"] = "$0.00"
    elif routing["route"] == "local":
        output = execute_local(prompt, routing["model"])
        routing["output"] = output
        routing["cost"] = "$0.00"
    else:
        # Return escalation info - main agent/control plane handles paid model call.
        routing["output"] = f"[ESCALATE to {routing['model']}]"
        routing["cost"] = "API_CALL_REQUIRED"

    return routing

if __name__ == "__main__":
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = sys.stdin.read()
    
    result = route_request(prompt)
    print(json.dumps(result, indent=2))
