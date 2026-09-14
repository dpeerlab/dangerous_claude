#!/bin/bash
# Stop hook: block if the current project has uncommitted changes.
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "default"')
MARKER="/tmp/track_git_project/${SESSION_ID}.dirty"

# prevent loops (at most one retry)
[ "$(echo "$INPUT" | jq -r '.stop_hook_active')" = "true" ] && exit 0

# no files were edited/created since the last check -> nothing to do
[ -f "$MARKER" ] || exit 0
rm -f "$MARKER"

# not a git repo -> nothing to check
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

STATUS=$(git status --porcelain)
[ -z "$STATUS" ] && exit 0

REASON="Uncommitted changes in the project:
${STATUS}

Either add these to .gitignore or commit them before finishing. Do not commit large files
(datasets, binaries, model weights, logs) — add those to .gitignore instead."

printf '{"decision":"block","reason":%s}' "$(jq -Rs . <<<"${REASON}")"
exit 2
