#!/usr/bin/env python3
"""
AI Request Router - Routes all requests through lightweight model first
Uses Llama 3.1 8B to decide: local handling vs API escalation
"""
import json
import os
import subprocess
import sys
from typing import Dict

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

# Economy policy: keep paid usage for final QA and truly complex tasks only.
QA_ONLY_GATE = os.getenv("ROUTER_QA_ONLY_GATE", "1") == "1"
FORCE_ESCALATE_TAGS = ["use codex", "use kimi", "api override", "premium model"]
HIGH_PRIORITY_TAGS = ["high priority", "urgent", "critical", "ship today", "final check"]


def wants_force_escalation(prompt: str) -> bool:
    p = (prompt or "").lower()
    return any(tag in p for tag in FORCE_ESCALATE_TAGS)


def is_high_priority(prompt: str) -> bool:
    p = (prompt or "").lower()
    return any(tag in p for tag in HIGH_PRIORITY_TAGS)


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

def classify_request(prompt: str) -> Dict:
    """Classify request with lightweight guards before model-based routing."""
    p = (prompt or "").strip()
    p_lower = p.lower()

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
        priority_ok = is_high_priority(prompt)

        # Allow paid escalation only for explicit override, extreme complexity,
        # or high-priority final QA style tasks.
        if not (force_escalate or complex_ok or priority_ok):
            routing = {
                "route": "local",
                "model": LOCAL_SPECIALISTS["qa"],
                "reason": f"QA-only gate held escalation ({routing.get('reason', 'policy')})",
                "qa_review_recommended": True,
            }

    # Step 3: Execute
    if routing["route"] == "local":
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
