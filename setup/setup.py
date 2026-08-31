#!/usr/bin/env python3
"""Resolve/persist dangerous_claude project config and print the container setup as JSON.

Usage: setup.py WORK_DIR [-- extra claude args...]

Reads/creates the project config file in WORK_DIR, prompting for any missing CONFIG_FIELDS
keys. Prints JSON: {"binds": [...], "claude_args": [...], "tools": "a,b,c", "env": {...},
"always_use_dangerous_skip_permissions": bool}.

writeable_home (bool, default true): if false, bind $HOME read-only, else read-write.
~/.claude is always read-write regardless, so Claude Code can persist its own state there,
shared across every project rather than isolated per project.

Global config (~/.dangerous_claude/config.json) supplies defaults, merged with the project
config: extra_write_paths/readable_paths concatenate; other scalars fall back to the global
value if the project doesn't set them — except the two CONFIG_FIELDS, which still prompt per
project (the global value is just the suggested default), since those are worth an explicit
per-project opt-in. See "Advanced overrides" below for individual fields.
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

# Advanced overrides: tools, env, extra_write_paths, readable_paths, project_readonly (project config); default_ro_paths, system_prompt_note (global-only) — see docs/permissions.rst.
# tools/ folders live in this repo (see add_tools.py) — not yet configurable.

# Generic OS/tool paths for host binaries (module, slurm, gpu) — not lab-specific, so hardcoded.
# Note: /etc/slurm is commonly its own mount (e.g. NFS/WekaFS), not part of the /etc filesystem —
# binding /etc alone doesn't pull in separately-mounted submounts. If sbatch/squeue can't find
# their config inside the container, add /etc/slurm to default_ro_paths in your global config
# (it's cluster-specific, so it doesn't belong hardcoded here) — see SETUP_PEERLAB_DANGEROUS.md.
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

# .version vs ~/.dangerous_claude/.version_last_migrated — mismatch triggers a migration prompt below, see #9.
VERSION_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".version")
LAST_MIGRATED_PATH = os.path.join(os.environ["HOME"], ".dangerous_claude", ".version_last_migrated")


def read_version(path):
    if os.path.exists(path):
        with open(path) as f:
            return f.read().strip()
    return None


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
            # global value is just the suggested default — still asked per project, not silently inherited
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

    # bind order matters (see readable_paths docs above): later binds shadow earlier ones on a parent path, so SYSTEM_RO_BINDS must precede root_restrictions in case one nests under it (e.g. /etc/slurm under /etc).
    root_restrictions = [p for p in allowed_restrictable if p in default_ro_paths]
    nested_restrictions = [p for p in allowed_restrictable if p not in default_ro_paths]

    binds = [f"{p}:{p}:ro" for p in SYSTEM_RO_BINDS]
    binds += [f"{p}:{p}:ro" for p in root_restrictions]

    writeable_home = merged("writeable_home", True)
    # Must come before the ~/.claude rw bind below (nested under $HOME) so that one can override it.
    binds.append(f"{home_dir}:{home_dir}:{'rw' if writeable_home else 'ro'}")

    project_readonly = merged("project_readonly", False)
    binds.append(f"{work_dir}:{work_dir}:{'ro' if project_readonly else 'rw'}")

    binds.append("/tmp:/tmp:rw")

    binds += [f"{p}:{p}:ro" for p in nested_restrictions]

    extra_write_paths = global_config.get("extra_write_paths", []) + config.get("extra_write_paths", [])
    for extra_path in extra_write_paths:
        extra_path = os.path.abspath(extra_path)
        binds.append(f"{extra_path}:{extra_path}:rw")

    # Always writable regardless of writeable_home, so Claude can persist its own state.
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

    # --append-system-prompt isn't repeatable (last one wins) — concatenate additions into this string.
    current_version = read_version(VERSION_PATH)
    last_migrated = read_version(LAST_MIGRATED_PATH)
    if current_version and current_version != last_migrated:
        system_prompt += (
            " Before anything else, read the change log. The last migrated version was "
            f"{last_migrated or 'none'} but the current version is {current_version}. Help "
            "the user migrate before answering questions."
        )

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
