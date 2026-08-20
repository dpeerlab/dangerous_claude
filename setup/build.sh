#!/usr/bin/env bash
# Build the dangerous_claude Singularity container with the latest Claude Code CLI.
# Usage: bash container/dangerous_claude/setup/build.sh
#
# Produces claude_code_<version>.sif (named after the version baked in during build)
# and points claude_code.sif — the name start.sh always runs — at it as a symlink.
# Both land in container/dangerous_claude/builds/ (gitignored — built .sif files aren't checked in).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="${SCRIPT_DIR}/../builds"
mkdir -p "${OUT_DIR}"
BUILD_SIF="${OUT_DIR}/.claude_code_build.sif"

# Stage the SLURM RPM locally before handing off to `singularity build`. The
# source lives under /admin, an autofs-mounted path — Singularity's build
# process can run in a mount namespace where that automount never fires.
# Copying it here, in the normal interactive shell where autofs is guaranteed
# to resolve, sidesteps that.
SLURM_RPM_SRC="/admin/software/slurm/x86_64/slurm-25.11.3-1.el8.x86_64.rpm"
STAGE_DIR="${SCRIPT_DIR}/.build_staging"
trap 'rm -rf "${STAGE_DIR}"' EXIT
mkdir -p "${STAGE_DIR}"
cp "${SLURM_RPM_SRC}" "${STAGE_DIR}/slurm-client.rpm"
[ -s "${STAGE_DIR}/slurm-client.rpm" ] || { echo "Failed to stage SLURM RPM from ${SLURM_RPM_SRC}" >&2; exit 1; }

# The staged RPM is handed to the build via --bind rather than the def file's
# %files directive: %files' copy-in silently no-ops under --fakeroot on this
# host (confirmed — dnf reports /tmp/slurm-client.rpm missing at install time
# even with an absolute source path), while a bind mount works since it
# doesn't go through that copy engine at all. Bound onto /mnt itself (mirrors
# Singularity.def's %post) since a bind destination that doesn't already
# exist in the image is silently skipped, and /mnt is FHS-guaranteed to exist.
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
