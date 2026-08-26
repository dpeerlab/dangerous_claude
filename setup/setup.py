#!/usr/bin/env python3
"""Resolve/persist dangerous_claude project config and print the container setup as JSON.

Usage: setup.py WORK_DIR [-- extra claude args...]

Reads/creates WORK_DIR/.agentic_peer_project.json, prompting interactively for any
missing keys (defaults shown in brackets). Prints a JSON object on stdout:
  {
    "binds": [...],                 # singularity --bind entries, "src:dst:mode"
    "claude_args": [...],           # args to pass to claude inside the container
    "tools": "a,b,c",               # AGENTIC_TOOLS env value
    "env": {"KEY": "value"},        # extra --env entries, global+project merged
    "always_use_dangerous_skip_permissions": true,
  }
  
Two concepts govern $HOME inside the sandbox:
  - writeable_home (bool, default true, one of the two interactive questions):
    false binds all of $HOME read-only; true binds all of it read-write.
  - ~/.claude is always bound read-write regardless of writeable_home, so
    Claude Code can persist its own state (transcripts, settings, credentials,
    skills/agents/commands/plugins) directly to the real home — no
    project-local copy/state dir. This means Claude's state (including
    session transcripts and memory) is shared across every project using
    dangerous_claude, not isolated per project.

tools defaults to empty (no tools enabled) and is not prompted for — edit
"tools" in .agentic_peer_project.json by hand to enable any.

extra_write_paths is an unrelated advanced override, also not prompted for —
see its definition below.

readable_paths is another advanced override, also not prompted for — see
default_ro_paths below.

Global config, read from ~/.dangerous_claude/config.json if present, supplies
defaults so you don't have to repeat yourself in every project:
  - scalars (writeable_home, project_readonly,
    always_use_dangerous_skip_permissions, tools, project_config_filename):
    project value wins if set, else the global value, else the builtin
    default. CONFIG_FIELDS is still prompted for per project if missing from
    the project config, even when the global config already has it — the
    global value is just the suggested default shown in the prompt, so a
    project explicitly opts in rather than silently inheriting it.
  - lists (extra_write_paths, readable_paths): global entries + project
    entries, concatenated. readable_paths is the exception when the project
    sets it to "*" (the default) — that keeps meaning "all of
    default_ro_paths", ignoring any global readable_paths list.
  - project_config_filename lets the global config point at a different
    project-file name than .agentic_peer_project.json, so a rename doesn't
    break existing per-project config files.
  - default_ro_paths, system_prompt_note: see their definitions below — none
    of this repo's own cluster paths are baked in, they're entirely a
    global-config concern.
  - env (dict of str: str) is forwarded as extra --env KEY=VALUE entries to
    the container; global and project dicts merge key-by-key, project wins
    on collision.
"""
import json
import os
import sys


CONFIG_FIELDS = [
    ("always_use_dangerous_skip_permissions", True, "Always skip permission prompts?"),
    (
        "writeable_home",
        True,
        "Bind your real $HOME read-write, not read-only?",
    ),
]

# Advanced overrides, not prompted for interactively — edit .agentic_peer_project.json
# (project) or ~/.dangerous_claude/config.json (global, see module docstring) by hand
# if you need them:
#   tools             — space-separated tool names to enable (default: none)
#   env               — dict of extra --env KEY: VALUE entries for the container
#   extra_write_paths — extra absolute paths to bind read-write (list of str)
#   readable_paths    — restrict which non-standard paths get bound read-only.
#                        "*" (default) binds all of default_ro_paths (global
#                        config, empty unless set); a list of absolute paths
#                        binds only those (each must be one of
#                        default_ro_paths itself, or nested inside one). A
#                        path nested inside home_dir/work_dir is layered on
#                        top of that (otherwise writable) bind as a read-only
#                        carve-out — order in the binds list matters for that
#                        case, see below. SYSTEM_RO_BINDS below is never
#                        restrictable.
#   project_readonly  - mount working directory (project) as read-only (default: False)
#                        useful if you want full control over rw/ro permissions
#                        via `readable_paths` and `extra_write_paths`
#
# Global-only (~/.dangerous_claude/config.json):
#   default_ro_paths     — cluster/lab storage paths readable_paths can restrict
#                          (list of str, default: none — this repo ships with no
#                          cluster paths baked in)
#   system_prompt_note   — extra sentence appended to the sandbox system prompt,
#                          e.g. a pointer to your own docs/wiki
#
# tools' folders live in this repo's tools/ directory for now (see
# setup/add_tools.py) — not yet configurable.

# Generic OS/tool paths needed for host binaries reached via the inherited PATH
# (module, slurm, gpu tooling) to work — always bound read-only, never
# restrictable, and not lab-specific so they stay hardcoded.
SYSTEM_RO_BINDS = [
    "/etc",
    "/lib",
    "/lib64",
    "/usr/lib",
    "/usr/lib64",
    "/usr/share/lmod",
    # munge auth socket — live host state, can't be baked into the image.
    "/run/munge",
]


def load_config(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


GLOBAL_CONFIG_PATH = os.path.join(os.environ["HOME"], ".dangerous_claude", "config.json")


YELLOW = "\033[33m"
RESET = "\033[0m"


def prompt_for(name, default, desc):
    default_str = default if isinstance(default, str) else " ".join(default) if isinstance(default, list) else str(default)
    print(f"{YELLOW}{desc} ({name}) [{default_str}]: {RESET}", end="", file=sys.stderr, flush=True)
    raw = input().strip()
    if not raw:
        return default
    if isinstance(default, bool):
        return raw.lower() in ("1", "true", "yes", "y")
    if isinstance(default, list):
        return raw.split()
    return raw


def main():
    if len(sys.argv) < 2:
        print("usage: setup.py WORK_DIR [-- extra claude args...]", file=sys.stderr)
        sys.exit(1)

    work_dir = os.path.abspath(sys.argv[1])
    extra_args = sys.argv[2:]
    if extra_args and extra_args[0] == "--":
        extra_args = extra_args[1:]

    global_config = load_config(GLOBAL_CONFIG_PATH)

    project_filename = global_config.get("project_config_filename", ".dangerous_claude.json")
    config_path = os.path.join(work_dir, project_filename)
    config = load_config(config_path)

    changed = False
    for name, default, desc in CONFIG_FIELDS:
        if name not in config:
            # global config supplies the suggested default, but this project
            # still gets asked explicitly rather than silently inheriting it
            config[name] = prompt_for(name, global_config.get(name, default), desc)
            changed = True

    if changed:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
            f.write("\n")

    home_dir = os.environ["HOME"]

    def merged(key, default):
        return config.get(key, global_config.get(key, default))

    default_ro_paths = global_config.get("default_ro_paths", [])

    readable_paths = config.get("readable_paths", "*")
    if readable_paths == "*":
        if "readable_paths" not in config and "readable_paths" in global_config:
            readable_paths = global_config["readable_paths"]
        else:
            readable_paths = default_ro_paths
    else:
        readable_paths = global_config.get("readable_paths", []) + readable_paths

    if readable_paths == default_ro_paths:
        allowed_restrictable = default_ro_paths
    else:
        unknown = []
        allowed_restrictable = []
        for p in readable_paths:
            found = False
            for base in default_ro_paths:
                if os.path.commonpath([p, base]) == base:
                    found = True
                    allowed_restrictable.append(p)
                    break
            if not found:
                unknown.append(p)
        if unknown:
            print(
                f"warning: readable_paths entries not in default_ro_paths, ignoring: {unknown}",
                file=sys.stderr,
            )

    # order or binds matter
    root_restrictions = [p for p in allowed_restrictable if p in default_ro_paths]
    nested_restrictions = [p for p in allowed_restrictable if p not in default_ro_paths]

    binds = [f"{p}:{p}:ro" for p in root_restrictions]
    binds += [f"{p}:{p}:ro" for p in SYSTEM_RO_BINDS]

    writeable_home = merged("writeable_home", True)
    # Whole of $HOME, read-write or read-only depending on writeable_home —
    # so dotfiles/tool config behave as on the host either way. Must come
    # before the ~/.claude rw bind below (a bind nested under $HOME).
    binds.append(f"{home_dir}:{home_dir}:{'rw' if writeable_home else 'ro'}")

    project_readonly = merged("project_readonly", False)
    binds.append(f"{work_dir}:{work_dir}:{'ro' if project_readonly else 'rw'}")

    binds.append("/tmp:/tmp:rw")

    binds += [f"{p}:{p}:ro" for p in nested_restrictions]

    extra_write_paths = global_config.get("extra_write_paths", []) + config.get("extra_write_paths", [])
    for extra_path in extra_write_paths:
        extra_path = os.path.abspath(extra_path)
        binds.append(f"{extra_path}:{extra_path}:rw")

    # ~/.claude is always writable regardless of writeable_home, so Claude Code
    # can persist its own state (transcripts, settings, credentials,
    # skills/agents/commands/plugins) directly to the real home. Must come
    # after the $HOME bind above (a nested rw bind layered on top of it).
    claude_dir = os.path.join(home_dir, ".claude")
    os.makedirs(claude_dir, exist_ok=True)
    binds.append(f"{claude_dir}:{claude_dir}:rw")

    if writeable_home:
        home_desc = "Your real home is mounted read-write (writeable_home=true), including credentials"
    else:
        home_desc = "Your real home is mounted read-only (writeable_home=false)"
    system_prompt = (
        "You are running in dangerous_claude, a sandboxed session with write access limited to "
        f"this project folder (plus any extra_write_paths configured in {project_filename}). "
        f"{home_desc}, and ~/.claude is always writable so Claude's own state persists there. "
        "Never install software unless the user explicitly instructs you to, and only into a "
        "location you've confirmed is writable (see extra_write_paths), never into ~."
    )
    system_prompt_note = global_config.get("system_prompt_note")
    if system_prompt_note:
        system_prompt += f" {system_prompt_note}"
    claude_args = [
        "--append-system-prompt",
        system_prompt,
    ]
    if merged("always_use_dangerous_skip_permissions", True):
        skip_permissions = True
    else:
        skip_permissions = prompt_for("skip_permissions_this_session", False, "Skip permission prompts for this session")

    if skip_permissions:
        claude_args.append("--dangerously-skip-permissions")
    claude_args.extend(extra_args)

    env = {**global_config.get("env", {}), **config.get("env", {})}

    print(json.dumps({
        "binds": binds,
        "claude_args": claude_args,
        "tools": merged("tools", ""),
        "env": env,
        "always_use_dangerous_skip_permissions": merged("always_use_dangerous_skip_permissions", True),
    }))


if __name__ == "__main__":
    main()
