#!/usr/bin/env python3
"""Merge the track_git_project hooks into a Claude settings.json.

Usage: add_hook.py SETTINGS_JSON_PATH
"""
import json
import os
import sys

TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
STOP_HOOK_SCRIPT = os.path.join(TOOL_DIR, "hook.sh")
MARK_DIRTY_SCRIPT = os.path.join(TOOL_DIR, "mark_dirty.sh")


def add_hook(settings, event, matcher, command, timeout):
    entries = settings.setdefault("hooks", {}).setdefault(event, [])
    for matcher_entry in entries:
        for hook in matcher_entry.get("hooks", []):
            if hook.get("command") == command:
                return  # already present

    entries.append({
        "matcher": matcher,
        "hooks": [{"type": "command", "command": command, "timeout": timeout}],
    })


def main():
    if len(sys.argv) != 2:
        print("usage: add_hook.py SETTINGS_JSON_PATH", file=sys.stderr)
        sys.exit(1)

    settings_path = sys.argv[1]
    os.makedirs(os.path.dirname(settings_path), exist_ok=True)

    if os.path.exists(settings_path):
        with open(settings_path) as f:
            settings = json.load(f)
    else:
        settings = {}

    add_hook(settings, "PostToolUse", "Edit|Write|MultiEdit|NotebookEdit", MARK_DIRTY_SCRIPT, 10)
    add_hook(settings, "Stop", "", STOP_HOOK_SCRIPT, 30)

    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
