# dangerous_claude

Run the Claude Code CLI on the lab HPC cluster inside a Singularity sandbox, with write access limited to the project folder and permission prompts skipped for autonomous agentic work.

> **Alpha — v0.0.1.** Interfaces and defaults may change.

## What's here

- `dangerous_claude` — entry point: `dangerous_claude CMD [ARGS...]` runs `CMD` (e.g. `claude`, `bash`, `sbatch --version`) inside the sandbox, scoped to the current working directory.
- `lib.sh` — the shared setup/launch logic (config resolution, binds, container exec), as a sourceable function, `dangerous_claude_run`.
- `setup/setup.py` — resolve/persist per-project config (`.agentic_peer_project.json`) and derive the container's bind mounts and CLI args.
- `setup/add_tools.py` — enable configured tools into the session's `settings.json`.
- `setup/Singularity.def` + `setup/build.sh` — build the container image (Rocky Linux 8 + latest Claude Code, Node, ripgrep, SLURM client).
- `builds/` — built `.sif` images land here (gitignored).
- `start.sh` / `start_bash.sh` — **backwards-compatible** wrappers for `dangerous_claude claude` / `dangerous_claude bash`. Only kept because some existing setups (e.g. the `claude()` shell function in `sail_force`) call `start.sh` directly; prefer `dangerous_claude` for anything new.

## Usage

```bash
# Build the container (once, and to update Claude Code)
bash setup/build.sh

# Start a sandboxed session in the current directory
cd /abs/path/to/project
./dangerous_claude claude

# Drop into a shell, or run any other command, in the same sandbox
./dangerous_claude bash
./dangerous_claude sbatch --version
```

There is no work-directory argument — the sandbox always scopes to the
current working directory; `cd` there first.

On first run per project, `setup.py` prompts for two settings (skip permission
prompts, writeable home) and writes `.agentic_peer_project.json`.

## Sandbox model

- Write access is limited to the project directory (plus any `extra_write_paths`).
- `$HOME` is bound read-only or read-write per `writeable_home`; `~/.claude`
  is always writable so Claude persists its own state to the real home.
- Cluster storage paths are bound read-only; no build toolchain is present, so
  the agent cannot install software inside the container.
