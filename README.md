# dangerous_claude

Run the Claude Code CLI on the lab HPC cluster inside a Singularity sandbox, with write access limited to the project folder and permission prompts skipped for autonomous agentic work.

> **Alpha — v0.0.1.** Interfaces and defaults may change.

## What's here

- `start.sh` — launch a sandboxed Claude Code session for a project directory.
- `start_bash.sh` — same sandbox, but drop into an interactive shell instead of Claude.
- `setup/setup.py` — resolve/persist per-project config (`.agentic_peer_project.json`) and derive the container's bind mounts and CLI args.
- `setup/add_tools.py` — enable configured tools into the session's `settings.json`.
- `setup/Singularity.def` + `setup/build.sh` — build the container image (Rocky Linux 8 + latest Claude Code, Node, ripgrep, SLURM client).
- `builds/` — built `.sif` images land here (gitignored).

## Usage

```bash
# Build the container (once, and to update Claude Code)
bash setup/build.sh

# Start a sandboxed session in a project directory
bash start.sh /abs/path/to/project
```

On first run per project, `setup.py` prompts for two settings (skip permission
prompts, writeable home) and writes `.agentic_peer_project.json`.

## Sandbox model

- Write access is limited to the project directory (plus any `extra_write_paths`).
- `$HOME` is bound read-only or read-write per `writeable_home`; `~/.claude`
  is always writable so Claude persists its own state to the real home.
- Cluster storage paths are bound read-only; no build toolchain is present, so
  the agent cannot install software inside the container.
