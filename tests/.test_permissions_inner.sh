# Usage: bash .test_permissions_inner.sh (runs inside the container)

set -euo pipefail

# read-only dir: read works, write blocked
[[ -r "${PATH_READONLY_DIR}" ]] && ok "READONLY_DIR read" || fail "READONLY_DIR read"
[[ -w "${PATH_READONLY_DIR}" ]] && fail "READONLY_DIR write not blocked" || ok "READONLY_DIR write blocked"

# extra_write_paths override: read and write both work
[[ -r "${PATH_EXTRA_WRITE_DIR}" ]] && ok "EXTRA_WRITE_DIR read" || fail "EXTRA_WRITE_DIR read blocked"
[[ -w "${PATH_EXTRA_WRITE_DIR}" ]] && ok "EXTRA_WRITE_DIR write" || fail "EXTRA_WRITE_DIR write blocked"
[[ -w $(dirname "${PATH_EXTRA_WRITE_DIR}") ]] && fail "EXTRA_WRITE_DIR write not blocked" || ok "EXTRA_WRITE_DIR write blocked"

# bound localscratch subpath: read and write both work
[[ -r "${PATH_LOCALSCRATCH_WRITE}" ]] && ok "LOCALSCRATCH_WRITE read" || fail "LOCALSCRATCH_WRITE read blocked"
[[ -w "${PATH_LOCALSCRATCH_WRITE}" ]] && ok "LOCALSCRATCH_WRITE write" || fail "LOCALSCRATCH_WRITE write blocked"

# bound read-only localscratch subpath: read works, write blocked
[[ -r "${PATH_LOCALSCRATCH_READ}" ]] && ok "LOCALSCRATCH_READ read" || fail "LOCALSCRATCH_READ read blocked"
[[ -w "${PATH_LOCALSCRATCH_READ}" ]] && fail "LOCALSCRATCH_READ write not blocked" || ok "LOCALSCRATCH_READ write blocked"

# unbound localscratch subpath: invisible entirely
[[ -e "${PATH_LOCALSCRATCH_NOREAD}" ]] && fail "LOCALSCRATCH_NOREAD not hidden" || ok "LOCALSCRATCH_NOREAD hidden"

# summary
echo ""
echo "=== results: ${PASS} passed, ${FAIL} failed ==="
[[ ${FAIL} -eq 0 ]]

