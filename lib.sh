#!/usr/bin/env bash
# Sandboxes the current working directory. Project config filename defaults to
# .dangerous_claude.json, resolved dynamically by setup.py (see its docstring
# for the global-config project_config_filename override).
#
# Shared container launch logic for dangerous_claude. Not to be meant to run directly.

DANGEROUS_CLAUDE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

dangerous_claude_run() {
    if [[ $# -eq 0 ]]; then
        echo "Usage: dangerous_claude_run CMD [ARGS...]" >&2
        return 1
    fi
    local cmd="$1"; shift
    local -a cmd_args=("$@")

    local work_dir="$(pwd)"

    # fail if no write permission in the project dir. The project config's
    # filename is resolved dynamically by setup.py (global config can repoint
    # it), so we can't check a specific file here — just the directory itself.
    if [[ ! -w "${work_dir}" ]]; then
        echo "No write permission for ${work_dir}." >&2
        return 1
    fi

    # resolve config: binds, claude args, tools using setup/setup.py
    # TODO: this could use the same singularity container to remove python dependency
    local setup_json
    if [[ "${cmd}" == "claude" ]]; then
        setup_json=$(python3 "${DANGEROUS_CLAUDE_ROOT}/setup/setup.py" "${work_dir}" -- "${cmd_args[@]}") || return 1
    else
        setup_json=$(python3 "${DANGEROUS_CLAUDE_ROOT}/setup/setup.py" "${work_dir}") || return 1
    fi

    local -a binds
    mapfile -t binds < <(jq -r '.binds[]' <<< "${setup_json}")
    local tools
    tools=$(jq -r '.tools' <<< "${setup_json}")
    local tools_root
    tools_root=$(jq -r '.tools_root' <<< "${setup_json}")
    local bind_str
    bind_str=$(IFS=,; echo "${binds[*]}")

    # get container (built by setup/build.sh into builds/, claude_code.sif is a symlink to the latest version)
    local claude_container="${DANGEROUS_CLAUDE_ROOT}/builds/claude_code.sif"

    local home_dir="${HOME}"
    local claude_config="${home_dir}/.claude"    # must be read-write

    # enable configured tools (no-op if tools_root isn't set in the global config)
    python3 "${DANGEROUS_CLAUDE_ROOT}/setup/add_tools.py" "${work_dir}" "${tools}" "${tools_root}"

    local -a run_cmd
    if [[ "${cmd}" == "claude" ]]; then
        local -a claude_args
        mapfile -t claude_args < <(jq -r '.claude_args[]' <<< "${setup_json}")
        run_cmd=(claude "${claude_args[@]}")
    else
        run_cmd=("${cmd}" "${cmd_args[@]}")
    fi

    echo "=== Entering container ==="
    echo "Container image: ${claude_container}"
    echo "Command: ${run_cmd[*]}"
    echo "HOME: ${home_dir} (read-write iff writeable_home=true in the project/global config; ~/.claude always read-write)"
    echo "TMP: real /tmp (read-write, bound directly)"

    singularity exec \
        --nv \
        --contain \
        --bind   "${bind_str}" \
        --pwd    "${work_dir}" \
        --env    "AWS_PROFILE=readonly" \
        --env    "_USES_CLAUDE_SINGULARITY=1" \
        --env    "USER=${USER}" \
        --env    "REPO=${work_dir}" \
        --env    "TMPDIR=/tmp" \
        --env    "PIXI_CACHE_DIR=${work_dir}/.pixi/cache" \
        --env    "CLAUDE_CONFIG_DIR=${claude_config}" \
        --env    "AGENTIC_TOOLS=${tools// /,}" \
        "${claude_container}" \
        "${run_cmd[@]}"
}
