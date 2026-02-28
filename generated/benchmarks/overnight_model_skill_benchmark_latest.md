# Overnight Local Model Benchmark Report
Generated: 2026-02-28T08:31:15

## Summary by Model
### local/qwen-14b
- Toolcall exec pass rate: 1.0
- Toolcall avg seconds: 3.3
- Skill routing accuracy: 1.0
- Skill routing avg seconds: 3.29

### local/qwen2.5-14b
- Toolcall exec pass rate: 1.0
- Toolcall avg seconds: 7.67
- Skill routing accuracy: 1.0
- Skill routing avg seconds: 3.27

### local/mistral-small
- Toolcall exec pass rate: 0.0
- Toolcall avg seconds: 3.27
- Skill routing accuracy: 0.0
- Skill routing avg seconds: 3.29

### local/qwen-coder-32b
- Toolcall exec pass rate: 0.0
- Toolcall avg seconds: 3.25
- Skill routing accuracy: 0.0
- Skill routing avg seconds: 3.3

### qwen3.5:cloud
- Toolcall exec pass rate: 1.0
- Toolcall avg seconds: 3.9
- Skill routing accuracy: 1.0
- Skill routing avg seconds: 3.3

## Best model by skill (empirical)
- apple-notes: qwen3.5:cloud (acc=1.0, avg_sec=3.3)
- apple-reminders: local/qwen2.5-14b (acc=1.0, avg_sec=3.23)
- browser-automation: local/qwen2.5-14b (acc=1.0, avg_sec=3.28)
- github: local/qwen-14b (acc=1.0, avg_sec=3.31)
- openai-whisper: local/qwen-14b (acc=1.0, avg_sec=3.3)
- video-frames: local/qwen2.5-14b (acc=1.0, avg_sec=3.3)
- weather: local/qwen-14b (acc=1.0, avg_sec=3.23)
- youtube-summarizer: local/qwen-14b (acc=1.0, avg_sec=3.3)