#!/usr/bin/env python3
"""
AI Router Queue Integration - Phi-3 Mini classifier with 24/7 operation
Integrates with existing ollama-agent-queue for seamless routing
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime

# Configuration
ROUTER_MODEL = "phi3:mini"  # 3.8B, 3s classification, minimal resources
GLOBAL_FALLBACK_MODEL = "moonshot/kimi-k2.5"
QUEUE_DIR = Path.home() / ".openclaw" / "agents" / "main" / "queue"
LOG_FILE = Path.home() / ".openclaw" / "logs" / "router-queue.log"

def log(msg):
    timestamp = datetime.now().isoformat()
    entry = f"[{timestamp}] {msg}"
    print(entry)
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")

def classify_with_phi3(prompt: str) -> dict:
    """Use Phi-3 Mini to classify request (3s, minimal resources)"""
    classification_prompt = f"""Classify this request in ONE word:
"{prompt[:300]}"

Choose: local_chat | local_writing | local_coding | local_qa | escalate_coding | escalate_reasoning | escalate_creative | escalate_long | escalate_qwen_cloud

Respond ONLY with the classification code:"""

    try:
        result = subprocess.run(
            ["ollama", "run", ROUTER_MODEL],
            input=classification_prompt,
            capture_output=True,
            text=True,
            timeout=10  # 10s max for classification
        )
        classification = result.stdout.strip().lower().split()[0]  # First word only
        
        # Parse to route
        if "escalate_coding" in classification:
            return {"route": "escalate", "model": "openai-codex/gpt-5.3-codex", "reason": "Complex coding"}
        elif "escalate_reasoning" in classification:
            return {"route": "escalate", "model": "moonshot/kimi-k2.5", "reason": "Complex reasoning"}
        elif "escalate_creative" in classification:
            return {"route": "escalate", "model": "openai/gpt-4o", "reason": "Premium creative"}
        elif "escalate_long" in classification:
            return {"route": "escalate", "model": "moonshot/kimi-k2.5", "reason": "Long context"}
        elif "escalate_qwen_cloud" in classification:
            return {"route": "escalate", "model": "qwen3.5:cloud", "reason": "Qwen Cloud"}
        elif "local_coding" in classification:
            return {"route": "local", "model": "deepseek-coder:6.7b", "reason": "Simple coding"}
        elif "local_writing" in classification:
            return {"route": "local", "model": "llama3.1:8b", "reason": "Writing"}
        elif "local_qa" in classification:
            return {"route": "local", "model": "qwen3:14b", "reason": "Q&A"}
        else:
            return {"route": "local", "model": "llama3.1:8b", "reason": "General chat"}
            
    except Exception as e:
        log(f"Classification error: {e}")
        return {"route": "escalate", "model": GLOBAL_FALLBACK_MODEL, "reason": "Router fallback"}

def process_queue():
    """Monitor queue and route incoming jobs"""
    log("Router daemon started - Phi-3 Mini classifier active")
    log(f"Queue directory: {QUEUE_DIR}")
    
    while True:
        try:
            # Check for new jobs in queue
            if QUEUE_DIR.exists():
                job_files = list(QUEUE_DIR.glob("*.json"))
                
                for job_file in job_files:
                    try:
                        with open(job_file) as f:
                            job = json.load(f)
                        
                        prompt = job.get("prompt", "")
                        job_id = job.get("id", job_file.stem)
                        
                        log(f"Processing job {job_id}: {prompt[:50]}...")
                        
                        # Classify with Phi-3 Mini (3s)
                        routing = classify_with_phi3(prompt)
                        log(f"  → {routing['route']} | {routing['model']} | {routing['reason']}")
                        
                        # Update job with routing info
                        job["routing"] = routing
                        job["classified_at"] = datetime.now().isoformat()
                        
                        # Write updated job back
                        with open(job_file, "w") as f:
                            json.dump(job, f, indent=2)
                        
                        # If local execution requested, process immediately
                        if routing["route"] == "local":
                            log(f"  → Executing locally with {routing['model']}")
                            # Local execution happens via existing queue workers
                        else:
                            log(f"  → Queued for API escalation")
                            
                    except Exception as e:
                        log(f"Error processing {job_file}: {e}")
            
            # Sleep to prevent CPU spinning
            time.sleep(2)
            
        except KeyboardInterrupt:
            log("Router daemon stopped")
            break
        except Exception as e:
            log(f"Daemon error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    process_queue()
