#!/usr/bin/env bash
# Usage: bash start_bash.sh [/abs/path/to/project] [-- extra claude args...]
# Same as start.sh, but drops into an interactive shell in the container instead of launching claude.
# Defaults to the current working directory if no path given.
#
# Project config lives in `.agentic_peer_project.json` in the project dir
# (created/prompted for by setup/setup.py on first run). See setup/setup.py for fields.

echo "Starting dangerous claude (bash shell) with Singularity containers..."

# setup workdir
WORK_DIR="${1:-$(pwd)}"
[[ $# -ge 1 ]] && shift
mkdir -p "${WORK_DIR}"
cd "${WORK_DIR}"

CONFIG_FILE="${WORK_DIR}/.agentic_peer_project.json"

# fall back to a plain local shell if we can't write to the project
# dir, or a config file already exists there but isn't writable
if [[ ! -w "${WORK_DIR}" ]] || { [[ -e "${CONFIG_FILE}" ]] && [[ ! -w "${CONFIG_FILE}" ]]; }; then
    echo "No write permission for ${WORK_DIR} (or its .agentic_peer_project.json) — starting a local shell instead of in the container."
    exec bash "$@"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# resolve project config + derived setup (binds, claude args, tools) via setup/setup.py
SETUP_JSON=$(python3 "${SCRIPT_DIR}/setup/setup.py" "${WORK_DIR}" -- "$@") || exit 1

mapfile -t BINDS < <(jq -r '.binds[]' <<< "${SETUP_JSON}")
TOOLS=$(jq -r '.tools' <<< "${SETUP_JSON}")

BIND_STR=$(IFS=,; echo "${BINDS[*]}")

# get container (built by setup/build.sh into builds/, claude_code.sif is a symlink to the latest version)
CLAUDE_CONTAINER="${SCRIPT_DIR}/builds/claude_code.sif"

# variables
HOME_DIR="${HOME}"                                   # already absolute
CLAUDE_CONFIG="${HOME_DIR}/.claude"                  # bound read-write directly by setup.py, regardless of writeable_home

# enable configured tools (agents/dangerous_claude/tools/<name>) into the session's settings.json
python3 "${SCRIPT_DIR}/setup/add_tools.py" "${WORK_DIR}" "${TOOLS}"

echo "=== Entering container (bash shell) ==="
echo "Container image: ${CLAUDE_CONTAINER}"
echo "HOME: ${HOME_DIR} (read-write iff writeable_home=true in .agentic_peer_project.json; ~/.claude always read-write)"
echo "TMP: real /tmp (read-write, bound directly)"

# $HOME is bind-mounted read-only or read-write (see writeable_home above) via
# the binds from setup.py — no --home remap; HOME stays the real path inside.
# /tmp is bound directly to the real host /tmp (see binds from setup.py).
singularity exec \
    --nv \
    --contain \
    --bind   "${BIND_STR}" \
    --pwd    "${WORK_DIR}" \
    --env    "AWS_PROFILE=readonly" \
    --env    "_USES_CLAUDE_SINGULARITY=1" \
    --env    "USER=${USER}" \
    --env    "REPO=${WORK_DIR}" \
    --env    "TMPDIR=/tmp" \
    --env    "PIXI_CACHE_DIR=${WORK_DIR}/.pixi/cache" \
    --env    "CLAUDE_CONFIG_DIR=${CLAUDE_CONFIG}" \
    --env    "AGENTIC_TOOLS=${TOOLS// /,}" \
    ${CLAUDE_CONTAINER} \
    bash
