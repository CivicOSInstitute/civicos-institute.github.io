#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path

CFG = Path('/Users/AI-OPS/.openclaw/workspace/scripts/mc/commands.json')


def load():
    return json.loads(CFG.read_text())['commands']


def run(cmd):
    script = Path(cmd['script'])
    if not script.exists():
        print(f"Missing script: {script}")
        return
    if cmd.get('confirm', True):
        ok = input(f"Run '{cmd['name']}'? [y/N]: ").strip().lower()
        if ok != 'y':
            print('Cancelled.')
            return
    print(f"\n== Running: {cmd['name']} ==\n")
    subprocess.run([str(script)], check=False)


def main():
    cmds = load()
    while True:
        print('\nMission Control — Terminus Lite')
        for i, c in enumerate(cmds, 1):
            print(f"{i}. {c['name']}")
        print('0. Exit')
        choice = input('Select action: ').strip()
        if choice == '0':
            return
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(cmds):
            print('Invalid choice.')
            continue
        run(cmds[int(choice)-1])


if __name__ == '__main__':
    main()
