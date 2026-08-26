# dangerous_claude

Claude can easily go rogue and read or write files that have nothing to do with the project it's
working on, which makes it risky to run with permission prompts skipped
(`--dangerously-skip-permissions`). `dangerous_claude` runs Claude Code inside a Singularity
container that restricts filesystem access at the system level, so even a rogue session stays
contained to the project it was started in.

## Installation

```bash
git clone https://github.com/dpeerlab/dangerous_claude.git
cd dangerous_claude
bash setup/build.sh
```

## Launch

```bash
cd /abs/path/to/your/project
./dangerous_claude claude
```

Sandboxes the current directory — there's no work-dir argument, `cd` there first. First run in a
project prompts for two settings and writes `.dangerous_claude.json`, e.g.:

```json
{
  "always_use_dangerous_skip_permissions": true,
  "writeable_home": true,
  "extra_write_paths": ["/home/you/.some_tool_cache"]
}
```

See `docs/` for the full sandbox model and configuration reference.
