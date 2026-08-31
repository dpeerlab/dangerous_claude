# Changelog

## v0.3.0

- **Version-mismatch migration prompt** (#15): when `~/.dangerous_claude/.version_last_migrated`
  is stale, the sandbox's system prompt tells Claude to read this changelog and help you migrate
  first. Writing that file back automatically is still open (#9).
- **Fixed a bind-order bug that broke `sbatch`**: `SYSTEM_RO_BINDS` bound a blanket `/etc`, and on
  clusters where `/etc/slurm` is its own mount, nesting a bind inside another bind's destination
  broke silently — `sbatch`/`squeue` couldn't find `slurm.conf`. `/etc` is no longer hardcoded;
  put cluster-specific `/etc` subpaths in `default_ro_paths` instead.
- **`readable_paths` now validates**: an entry not covered by any `default_ro_paths` entry used to
  be dropped silently. Setup now fails with the exact `default_ro_paths` entry to add.

## v0.2.0

- **Global settings** (#6): `~/.dangerous_claude/config.json` supplies defaults —
  `extra_write_paths`/`readable_paths` merge with a project's own; `default_ro_paths`, `tools`,
  `env`, and others fall back to it too.
- **No more hardcoded lab paths** (#7): cluster paths (`/data1`, `/usersoftware`, ...) moved out
  of the code into `default_ro_paths`; project config defaults to `.dangerous_claude.json`.
  **To migrate**: set `"project_config_filename": ".agentic_peer_project.json"` in
  `~/.dangerous_claude/config.json` to keep using your existing config files.
- **Env passthrough** (#8): set any env var via `env` in global/project config. Replaces the
  hardcoded `AWS_PROFILE=readonly`.

## v0.1.0

First tagged release: the generic `dangerous_claude` entrypoint, shared `lib.sh`, sandbox
permission tests, and docs. See the
[GitHub release notes](https://github.com/dpeerlab/dangerous_claude/releases/tag/v0.1.0).
