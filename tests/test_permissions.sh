#!/usr/bin/env bash
# test if read and write permissions are restricted correctly:
# 1. setup: swap config to a template
# 2. run: run read and write tests
# 3. teardown: restore previous status

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# replace config file
CONFIG_FILE="${PROJECT_DIR}/.agentic_peer_project.json"
CONFIG_BACKUP="${CONFIG_FILE}.bak"
TEMPLATE="${SCRIPT_DIR}/assets/.agentic_peer_project_template.json"

# test directories
export PATH_READONLY_DIR="${SCRIPT_DIR}/.test_dangerous_readonly"
export PATH_EXTRA_WRITE_DIR="${HOME}/.test_dangerous_claude"
export PATH_LOCALSCRATCH_WRITE="/localscratch/.test_dangerous_claude_write"
export PATH_LOCALSCRATCH_READ="/localscratch/.test_dangerous_claude_read"
export PATH_LOCALSCRATCH_NOREAD="/localscratch/.test_dangerous_claude_noread"

echo ""
echo "=== dangerous_claude permissions tests ==="
echo ""

# swap config file
setup() {
    # backup config
    if [[ -e "${CONFIG_FILE}" ]]; then
        mv "${CONFIG_FILE}" "${CONFIG_BACKUP}"
    fi

    # substitute placeholders and use template
    sed -e "s#<HOME>#${HOME}#g" -e "s#<TESTS_DIR>#${SCRIPT_DIR}#g" "${TEMPLATE}" > "${CONFIG_FILE}"

    # create paths
    mkdir -p "${PATH_EXTRA_WRITE_DIR}" "${PATH_READONLY_DIR}" "${PATH_LOCALSCRATCH_WRITE}" "${PATH_LOCALSCRATCH_READ}" "${PATH_LOCALSCRATCH_NOREAD}"
}

# restore previous status
teardown() {
    # remove test directories
    rm -rf "${PATH_EXTRA_WRITE_DIR}" "${PATH_READONLY_DIR}" "${PATH_LOCALSCRATCH_WRITE}" "${PATH_LOCALSCRATCH_READ}" "${PATH_LOCALSCRATCH_NOREAD}"

    # restore config
    rm -f "${CONFIG_FILE}"
    if [[ -e "${CONFIG_BACKUP}" ]]; then
        cp "${CONFIG_BACKUP}" "${CONFIG_FILE}"
    fi
}

# register teardown on exit
trap teardown EXIT

setup

# test permissions
"${PROJECT_DIR}/dangerous_claude" bash "${PROJECT_DIR}/tests/.test_permissions_inner.sh"