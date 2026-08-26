#!/usr/bin/env python3
"""Enable dangerous_claude tools by running each tool's include.sh.

Usage: add_tools.py WORK_DIR TOOLS_SPEC [TOOLS_ROOT]

TOOLS_SPEC is a space-separated list of tool folder names under TOOLS_ROOT, or "*" for all.
TOOLS_ROOT (from the global config's "tools_root", see setup.py) is where tool folders live;
if empty/unset, the tools feature is disabled (a no-op, even if TOOLS_SPEC is set).
Each tool's include.sh is called as: include.sh SETTINGS_JSON_PATH
"""
import os
import subprocess
import sys


def resolve_tools(tools_spec, tools_root):
    if tools_spec.strip() == "*":
        return sorted(
            name for name in os.listdir(tools_root)
            if os.path.isdir(os.path.join(tools_root, name))
        )
    return tools_spec.split()


def main():
    if len(sys.argv) not in (3, 4):
        print("usage: add_tools.py WORK_DIR TOOLS_SPEC [TOOLS_ROOT]", file=sys.stderr)
        sys.exit(1)

    work_dir, tools_spec = sys.argv[1:3]
    tools_root = sys.argv[3] if len(sys.argv) == 4 else ""

    if not tools_spec.strip():
        return

    if not tools_root:
        print(
            "warning: tools configured but no tools_root set in the global config "
            "(~/.dangerous_claude/config.json) — skipping",
            file=sys.stderr,
        )
        return

    settings_path = os.path.join(os.environ["HOME"], ".claude", "settings.json")

    for name in resolve_tools(tools_spec, tools_root):
        include_sh = os.path.join(tools_root, name, "include.sh")
        if not os.path.isfile(include_sh):
            print(f"warning: tool '{name}' has no include.sh, skipping", file=sys.stderr)
            continue
        subprocess.run(["bash", include_sh, settings_path], check=True)


if __name__ == "__main__":
    main()
