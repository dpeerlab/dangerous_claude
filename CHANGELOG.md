# Changelog

## v0.2.0

- **Global settings** (#6, #10): `~/.dangerous_claude/config.json` supplies defaults for every
  project. `extra_write_paths`/`readable_paths` concatenate with whatever a project sets;
  `project_readonly`/`tools` fall back to the global value if a project doesn't set them.
  `always_use_dangerous_skip_permissions`/`writeable_home` still prompt per project (the global
  value is just the suggested default), since those are security-relevant enough to confirm
  explicitly rather than silently inherit.
- **No more hardcoded lab paths** (#7, #11): the project config file is now
  `.dangerous_claude.json` by default (set `project_config_filename` in the global config to keep
  the old `.agentic_peer_project.json` name — no mass rename needed). Cluster storage paths
  (`/data1`, `/usersoftware`, `/scratch`, `/ifs`, `/admin`, `/localscratch`) are no longer baked
  into the code — set `default_ro_paths` in your global config instead; a fresh clone binds none
  of it until you do. Generic OS/tool paths needed for `module`/`sbatch`/GPU tooling (`/etc`,
  `/lib`, `/usr/share/lmod`, `/run/munge`, ...) stay hardcoded, since those aren't lab-specific.
  The system prompt's lab-specific doc/wiki pointer is now configurable (`system_prompt_note`)
  instead of hardcoded. `tools` still ship as part of this repo (`tools/`) for now, not yet
  configurable.
- **Arbitrary env passthrough** (#8, #12): set any environment variable inside the sandbox via
  `env` in global/project config, merged (project wins on collision). Replaces the hardcoded
  `AWS_PROFILE=readonly`.

## v0.1.0

First tagged release: the generic `dangerous_claude` entrypoint (`claude`/`bash`/`sbatch`/...),
shared `lib.sh`, sandbox permission tests, and Sphinx/ReadTheDocs documentation. See the
[GitHub release notes](https://github.com/dpeerlab/dangerous_claude/releases/tag/v0.1.0).
