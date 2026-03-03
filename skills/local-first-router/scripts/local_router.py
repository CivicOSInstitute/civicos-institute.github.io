#!/usr/bin/env python3
"""Local-First Router - 100% local model consultation for every task"""
import subprocess
import json
import sys
import re

LOCAL_MODELS = {
    "phi3:mini": {"type": "classifier", "speed": "fast", "best_for": "routing_decisions"},
    "llama3.1:8b": {"type": "general", "speed": "medium", "best_for": "writing,chat,general"},
    "qwen3:14b": {"type": "reasoning", "speed": "slow", "best_for": "analysis,qa,complex"},
    "deepseek-coder:6.7b": {"type": "coding", "speed": "medium", "best_for": "code,technical"},
    "qwen3.5:4b": {"type": "multimodal", "speed": "fast", "best_for": "vision,ocr"},
    "qwen3.5:9b": {"type": "contrarian", "speed": "medium", "best_for": "edge_cases"}
}

def classify_with_phi3(task_desc):
    """Use phi3:mini for fast classification"""
    prompt = f"""Task: {task_desc}

Can this be handled by a local 8B-14B model? Consider:
- Coding/technical tasks → deepseek-coder
- Writing/chat → llama3.1:8b  
- Analysis/reasoning → qwen3:14b
- Vision/multimodal → qwen3.5:4b

Respond ONLY with JSON format:
{{"can_local": true/false, "model": "model_name", "confidence": 0.0-1.0, "reason": "brief"}}"""
    
    try:
        result = subprocess.run(
            ["ollama", "run", "phi3:mini", prompt],
            capture_output=True, text=True, timeout=15
        )
        
        # Extract JSON from response
        text = result.stdout.strip()
        json_match = re.search(r'\{[^}]+\}', text)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        print(f"Classification error: {e}", file=sys.stderr)
    
    # Default to local if classification fails
    return {"can_local": True, "model": "llama3.1:8b", "confidence": 0.7, "reason": "Default local fallback"}

def strict_local_route(task):
    """100% local-first routing with zero API escalation unless impossible"""
    classification = classify_with_phi3(task)
    
    if classification.get("can_local", True):
        model = classification.get("model", "llama3.1:8b")
        if model not in LOCAL_MODELS:
            model = "llama3.1:8b"  # Safe default
            
        return {
            "route": "local",
            "model": model,
            "confidence": classification.get("confidence", 0.8),
            "reason": classification.get("reason", "Local model suitable"),
            "escalation_required": False
        }
    else:
        return {
            "route": "local",  # STILL try local first
            "model": "qwen3:14b",  # Most capable local
            "confidence": 0.6,
            "reason": "Classification uncertain - trying strongest local model",
            "escalation_required": False,
            "note": "Explicit 'use API' keyword required for escalation"
        }

def should_escalate_to_api(task, local_result):
    """Strict API escalation criteria"""
    api_keywords = ["use api", "use kimi", "use gpt-4", "use codex", "requires gpt-4", "requires api"]
    
    task_lower = task.lower()
    if any(kw in task_lower for kw in api_keywords):
        return True, "Explicit API request detected"
    
    # Check if local truly failed after retry
    if local_result.get("failed_twice", False):
        return True, "Local models failed after retry"
    
    return False, "Local-first policy maintained"

if __name__ == "__main__":
    task = sys.argv[1] if len(sys.argv) > 1 else "General task"
    
    # 100% local-first consultation
    result = strict_local_route(task)
    
    # Check if API escalation truly needed
    should_api, api_reason = should_escalate_to_api(task, result)
    
    if should_api:
        result["route"] = "escalate"
        result["escalation_reason"] = api_reason
        result["requires_approval"] = True
    
    print(json.dumps(result, indent=2))
