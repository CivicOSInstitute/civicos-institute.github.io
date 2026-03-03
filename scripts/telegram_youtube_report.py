#!/usr/bin/env python3
"""Send YouTube monitoring report to Telegram group."""
import json
import pathlib
import subprocess
import os

BASE = pathlib.Path('/Users/AI-OPS/.openclaw/workspace')
DATA = BASE / 'generated' / 'youtube_dashboard' / 'videos.json'

def send_telegram(message):
    """Send message via OpenClaw message tool."""
    try:
        # Use openclaw CLI to send message to the YouTube group
        subprocess.run([
            'openclaw', 'message', 'send',
            '--channel', 'telegram',
            '--target', '-5232457391',
            '--message', message
        ], capture_output=True, timeout=30)
        return True
    except Exception:
        return False

def main():
    if not DATA.exists():
        print("No dashboard data found")
        return
    
    data = json.loads(DATA.read_text())
    new_count = data.get('new_count', 0)
    channel_count = data.get('channel_count', 0)
    updated_at = data.get('updated_at', 'unknown')
    
    # Build report
    lines = [
        "📺 *YouTube Monitor Report*",
        f"🕐 {updated_at}",
        f"📊 {channel_count} channels monitored",
        ""
    ]
    
    if new_count > 0:
        lines.append(f"🆕 *{new_count} new videos detected*")
        lines.append("")
        
        # Show new videos with summaries
        for v in data.get('videos', [])[:5]:
            if v.get('is_new'):
                title = v.get('title', 'Untitled')[:60]
                channel = v.get('channel', 'Unknown')
                excerpt = v.get('summary_excerpt', '')
                url = v.get('url', '')
                
                lines.append(f"• *{channel}*: {title}")
                if excerpt:
                    lines.append(f"  _{excerpt[:100]}..._")
                lines.append(f"  [Watch]({url})")
                lines.append("")
    else:
        lines.append("✅ No new videos since last check")
    
    # Channel status summary
    lines.append("")
    lines.append("*Channel Health:*")
    ok_count = sum(1 for c in data.get('channels', []) if c.get('status') == 'ok')
    err_count = len(data.get('channels', [])) - ok_count
    lines.append(f"✅ {ok_count} OK" + (f" | ⚠️ {err_count} errors" if err_count else ""))
    
    message = "\n".join(lines)
    
    if send_telegram(message):
        print("Report sent to Telegram")
    else:
        print("Failed to send Telegram report")

if __name__ == '__main__':
    main()
