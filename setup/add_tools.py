#!/usr/bin/env python3
"""Enable dangerous_claude tools by running each tool's include.sh.

Usage: add_tools.py WORK_DIR TOOLS_SPEC

TOOLS_SPEC is a space-separated list of tool folder names under TOOLS_ROOT, or "*" for all.
Each tool's include.sh is called as: include.sh SETTINGS_JSON_PATH
"""
import os
import subprocess
import sys

TOOLS_ROOT = "/data1/collab002/sail/projects/tools/sail_force/agents/dangerous_claude/tools"


def resolve_tools(tools_spec):
    if tools_spec.strip() == "*":
        return sorted(
            name for name in os.listdir(TOOLS_ROOT)
            if os.path.isdir(os.path.join(TOOLS_ROOT, name))
        )
    return tools_spec.split()


def main():
    if len(sys.argv) != 3:
        print("usage: add_tools.py WORK_DIR TOOLS_SPEC", file=sys.stderr)
        sys.exit(1)

    work_dir, tools_spec = sys.argv[1:3]
    settings_path = os.path.join(os.environ["HOME"], ".claude", "settings.json")

    for name in resolve_tools(tools_spec):
        include_sh = os.path.join(TOOLS_ROOT, name, "include.sh")
        if not os.path.isfile(include_sh):
            print(f"warning: tool '{name}' has no include.sh, skipping", file=sys.stderr)
            continue
        subprocess.run(["bash", include_sh, settings_path], check=True)


if __name__ == "__main__":
    main()
