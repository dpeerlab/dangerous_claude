# Changelog

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
