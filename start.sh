#!/usr/bin/env bash
# Usage: bash start.sh [extra claude args...]
# Launch a sandboxed Claude Code session for the current working directory.
# Thin wrapper around `dangerous_claude claude` — see dangerous_claude/lib.sh.

echo "Starting dangerous claude with Singularity containers..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib.sh"

dangerous_claude_run claude "$@"
