#!/usr/bin/env bash
# Usage: include.sh SETTINGS_JSON_PATH
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "${SCRIPT_DIR}/add_hook.py" "$1"
