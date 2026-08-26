#!/usr/bin/env bash
# Usage: bash run_tests.sh
# Runs all dangerous_claude tests. Must run on the host, not from inside a
# dangerous_claude session

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SIF="${SCRIPT_DIR}/builds/claude_code.sif"

# count pass and fail
PASS=0
FAIL=0

ok()   { echo "  PASS: $1"; ((++PASS)); }
fail() { echo "  FAIL: $1"; ((++FAIL)); }
skip() { echo "  SKIP: $1"; }

export -f ok fail skip
export PASS FAIL

# check that singularity and the image exist
if ! command -v singularity >/dev/null 2>&1; then
    echo "ERROR: singularity not found on PATH — run this from the host, not from inside a dangerous_claude session." >&2
    exit 1
fi

if [[ ! -f "${SIF}" ]]; then
    echo "ERROR: image not found: ${SIF}" >&2
    echo "Build it first: bash ${SCRIPT_DIR}/setup/build.sh" >&2
    exit 1
fi

# test container tools
"${SCRIPT_DIR}/dangerous_claude" bash "${SCRIPT_DIR}/tests/test_container.sh"

# test permissions (container launched within test script)
bash "${SCRIPT_DIR}/tests/test_permissions.sh"