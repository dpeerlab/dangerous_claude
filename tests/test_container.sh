#!/usr/bin/env bash
# Usage: bash run_tests.sh (runs inside the container)
# ok/fail/skip and PASS/FAIL counters come from run_tests.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "=== dangerous_claude container tests ==="
echo ""

# check other tools
TOOLS=(
    nvidia-smi
    claude
    sbatch
    git
    jq
    node
    rg
    module
)
for TOOL in "${TOOLS[@]}"; do
    ${TOOL} --version >/dev/null 2>&1 && ok "${TOOL} works" || fail "${TOOL} works"
done

TOOLS_NEGATIVE=(
    unknown_tool
)
for TOOL in "${TOOLS_NEGATIVE[@]}"; do
    ${TOOL} --version >/dev/null 2>&1 && fail "${TOOL} should not exist" || ok "${TOOL} correctly not found"
done

# return
echo ""
echo "=== results: ${PASS} passed, ${FAIL} failed ==="
[[ ${FAIL} -eq 0 ]]

