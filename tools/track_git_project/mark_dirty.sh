#!/bin/bash
# PostToolUse hook: mark this session dirty after a file edit/create, so the
# Stop hook (hook.sh) knows a git-status check is actually worth running.
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "default"')

MARKER_DIR="/tmp/track_git_project"
mkdir -p "$MARKER_DIR"
touch "${MARKER_DIR}/${SESSION_ID}.dirty"
