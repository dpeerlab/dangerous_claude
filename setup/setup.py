#!/usr/bin/env python3
"""Resolve/persist dangerous_claude project config and print the container setup as JSON.

Usage: setup.py WORK_DIR [-- extra claude args...]

Reads/creates WORK_DIR/.agentic_peer_project.json, prompting interactively for any
missing keys (defaults shown in brackets). Prints a JSON object on stdout:
  {
    "binds": [...],                 # singularity --bind entries, "src:dst:mode"
    "claude_args": [...],           # args to pass to claude inside the container
    "tools": "a,b,c",               # AGENTIC_TOOLS env value
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
DEFAULT_RO_BINDS below.
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
# by hand if you need them:
#   tools             — space-separated tool names to enable (default: none)
#   extra_write_paths — extra absolute paths to bind read-write (list of str)
#   readable_paths    — restrict which non-standard paths get bound read-only.
#                        "*" (default) binds all of DEFAULT_RO_BINDS below;
#                        a list of absolute paths binds only those (each must
#                        be one of DEFAULT_RO_BINDS itself, or nested inside
#                        one). A path nested inside home_dir/work_dir is
#                        layered on top of that (otherwise writable) bind as
#                        a read-only carve-out — order in the binds list
#                        matters for that case, see below. Standard system
#                        paths (lmod, slurm, munge) are never restrictable.
#   project_readonly  - mount working directory (project) as read-only (default: False)
#                        useful if you want full control over rw/ro permissions
#                        via `readable_paths` and `extra_write_paths`

# Non-standard lab/cluster storage paths that readable_paths can restrict.
DEFAULT_RO_BINDS = [
    "/data1/peerd",
    "/data1/collab002",
    "/scratch",
    "/ifs",
    "/usersoftware",
    "/admin",
    "/localscratch",
]

# Standard system paths, always bound read-only regardless of readable_paths.
ALWAYS_RO_BINDS = [
    "/usersoftware/collab002/",
    "/usr/share/lmod",
    # SLURM client config + munge auth socket — the sbatch/squeue/etc binaries
    # themselves are baked into the image (see Singularity.def), but these two
    # are live host state that can't be baked in.
    "/etc/slurm",
    "/run/munge",
]


def load_config(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


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

    config_path = os.path.join(work_dir, ".agentic_peer_project.json")
    config = load_config(config_path)

    changed = False
    for name, default, desc in CONFIG_FIELDS:
        if name not in config:
            config[name] = prompt_for(name, default, desc)
            changed = True

    if changed:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
            f.write("\n")

    home_dir = os.environ["HOME"]

    readable_paths = config.get("readable_paths", "*")
    if readable_paths == "*":
        allowed_restrictable = DEFAULT_RO_BINDS
    else:
        unknown = []
        allowed_restrictable = []
        for p in readable_paths:
            found = False
            for base in DEFAULT_RO_BINDS:
                if os.path.commonpath([p, base]) == base:
                    found = True
                    allowed_restrictable.append(p)
                    break
            if not found:
                unknown.append(p)
        if unknown:
            print(
                f"warning: readable_paths entries not in DEFAULT_RO_BINDS, ignoring: {unknown}",
                file=sys.stderr,
            )

    # order or binds matter
    root_restrictions = [p for p in allowed_restrictable if p in DEFAULT_RO_BINDS]
    nested_restrictions = [p for p in allowed_restrictable if p not in DEFAULT_RO_BINDS]

    binds = [f"{p}:{p}:ro" for p in root_restrictions]
    binds += [f"{p}:{p}:ro" for p in ALWAYS_RO_BINDS]

    writeable_home = config.get("writeable_home", True)
    # Whole of $HOME, read-write or read-only depending on writeable_home —
    # so dotfiles/tool config behave as on the host either way. Must come
    # before the ~/.claude rw bind below (a bind nested under $HOME).
    binds.append(f"{home_dir}:{home_dir}:{'rw' if writeable_home else 'ro'}")

    project_readonly = config.get("project_readonly", False)
    binds.append(f"{work_dir}:{work_dir}:{'ro' if project_readonly else 'rw'}")

    binds.append("/tmp:/tmp:rw")

    binds += [f"{p}:{p}:ro" for p in nested_restrictions]

    for extra_path in config.get("extra_write_paths", []):
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
    claude_args = [
        "--append-system-prompt",
        "You are running in dangerous_claude, a sandboxed session with write access limited to "
        "this project folder (plus any extra_write_paths configured in .agentic_peer_project.json). "
        f"{home_desc}, and ~/.claude is always writable so Claude's own state persists there; see "
        "/data1/collab002/sail/projects/tools/sail_force/docs/dangerous_claude.md "
        "or run `/usersoftware/collab002/sail/tools/peer-wiki/query` for more details. "
        "Never install software, unless the user explicitely instructs you to. If the user "
        "wants to install software, it has to be into /usersoftware/peerd/<username>, never into ~",
    ]
    if config.get("always_use_dangerous_skip_permissions", True):
        skip_permissions = True
    else:
        skip_permissions = prompt_for("skip_permissions_this_session", False, "Skip permission prompts for this session")

    if skip_permissions:
        claude_args.append("--dangerously-skip-permissions")
    claude_args.extend(extra_args)

    print(json.dumps({
        "binds": binds,
        "claude_args": claude_args,
        "tools": config.get("tools", ""),
        "always_use_dangerous_skip_permissions": config.get("always_use_dangerous_skip_permissions", True),
    }))


if __name__ == "__main__":
    main()
