# track_git_project

## Enabling

Add it to `tools` in your project's `.agentic_peer_project.json` (a list; add other tool names
to enable more than one):

```json
{"tools": ["track_git_project"]}
```

Adds two hooks:
- A `PostToolUse` hook (`mark_dirty.sh`, matcher `Edit|Write|MultiEdit|NotebookEdit`) that
  drops a marker file (`/tmp/track_git_project/<session_id>.dirty`) whenever a file is
  edited or created.
- A `Stop` hook (`hook.sh`) that runs at the end of every request. It only does anything if
  the marker file exists (i.e. a file actually changed since the last Stop check) — this
  avoids running `git status` on every turn. If it does run and finds uncommitted changes,
  it blocks (exit 2) and tells Claude to either add the files to `.gitignore` or commit them.
  Large files should never be committed — add them to `.gitignore` instead.

## Files
- `hook.sh` — the `Stop` hook itself.
- `mark_dirty.sh` — the `PostToolUse` hook that sets the dirty marker.
- `include.sh` — wires both hooks into the container's `settings.json` (calls `add_hook.py`).
- `add_hook.py` — merges the hook entries into `settings.json` without clobbering existing hooks.
