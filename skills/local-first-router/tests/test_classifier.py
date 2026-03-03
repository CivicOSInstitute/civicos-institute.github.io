#!/usr/bin/env python3
"""Test suite for local-first router"""
import subprocess
import json

test_tasks = [
    ("Write a thank you email", "writing"),
    ("Debug this Python function", "coding"),
    ("Analyze the pros and cons of remote work", "analysis"),
    ("Summarize this article", "summarization"),
    ("Create a project plan", "planning"),
]

def test_classifier():
    script = "~/.openclaw/workspace/skills/local-first-router/scripts/local_router.py"
    results = []
    
    for task, expected_type in test_tasks:
        result = subprocess.run(
            ["python3", script, task],
            capture_output=True, text=True, timeout=30
        )
        
        try:
            data = json.loads(result.stdout)
            results.append({
                "task": task,
                "route": data.get("route"),
                "model": data.get("model"),
                "local": data.get("route") == "local"
            })
        except:
            results.append({"task": task, "error": result.stderr})
    
    # Summary
    local_count = sum(1 for r in results if r.get("local"))
    print(f"\n=== Test Results ===")
    print(f"Total: {len(results)}")
    print(f"Routed local: {local_count}")
    print(f"Routed API: {len(results) - local_count}")
    print(f"Local-first rate: {local_count/len(results)*100:.1f}%")
    
    for r in results:
        status = "✓ LOCAL" if r.get("local") else "⚠ API"
        print(f"{status}: {r['task'][:40]}... -> {r.get('model', 'ERROR')}")

if __name__ == "__main__":
    test_classifier()
