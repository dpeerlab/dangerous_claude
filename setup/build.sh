#!/usr/bin/env bash
# Usage: bash container/dangerous_claude/setup/build.sh
# Builds claude_code_<version>.sif and symlinks claude_code.sif to it; both land in builds/.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="${SCRIPT_DIR}/../builds"
mkdir -p "${OUT_DIR}"
BUILD_SIF="${OUT_DIR}/.claude_code_build.sif"

# /admin is autofs-mounted; singularity build's mount namespace can prevent that
# automount from firing, so stage the RPM locally first.
SLURM_RPM_SRC="/admin/software/slurm/x86_64/slurm-25.11.3-1.el8.x86_64.rpm"
STAGE_DIR="${SCRIPT_DIR}/.build_staging"
trap 'rm -rf "${STAGE_DIR}"' EXIT
mkdir -p "${STAGE_DIR}"
cp "${SLURM_RPM_SRC}" "${STAGE_DIR}/slurm-client.rpm"
[ -s "${STAGE_DIR}/slurm-client.rpm" ] || { echo "Failed to stage SLURM RPM from ${SLURM_RPM_SRC}" >&2; exit 1; }

# --bind, not %files: %files' copy-in silently no-ops under --fakeroot here. /mnt
# is used since it's FHS-guaranteed to exist (an absent bind target is skipped).
(cd "${SCRIPT_DIR}" && singularity build --fakeroot --force \
    --bind "${STAGE_DIR}:/mnt" \
    "${BUILD_SIF}" "Singularity.def")

VERSION=$(singularity exec "${BUILD_SIF}" cat /opt/claude/VERSION)
VERSIONED_SIF="${OUT_DIR}/claude_code_${VERSION}.sif"
LATEST_SIF="${OUT_DIR}/claude_code.sif"

mv "${BUILD_SIF}" "${VERSIONED_SIF}"
ln -sf "$(basename "${VERSIONED_SIF}")" "${LATEST_SIF}"

echo "Built ${VERSIONED_SIF}"
echo "Symlinked ${LATEST_SIF} -> $(basename "${VERSIONED_SIF}")"
