Permissions
============

Helps ensure that Claude can only read and write files that are important for your project.
Controlled by ``.dangerous_claude.json`` in your project directory (the filename is
configurable, see `Global defaults`_ — this also keeps old ``.agentic_peer_project.json``
projects working).

Default access
----------------

- Your project directory: read-write.
- Generic OS/tool paths (``/etc``, ``/lib``, ``/usr/share/lmod``, ``/run/munge``, ...): read-only
  — needed for host tools like ``module``/``sbatch`` to work, not lab-specific.
- ``$HOME``: read-write, unless ``writeable_home: false``
- ``/tmp``: always read-write
- ``~/.claude``: always read-write, so Claude can save its own state.
- Anything else: not visible at all, not even read-only. This repo ships with no
  cluster/lab storage paths bound by default — set ``default_ro_paths`` in your global config
  (below) for your own cluster.

``extra_write_paths``
---------------------

Makes specific paths writable even though they'd otherwise be read-only, for example a tool in 
another directory.

.. code-block:: json

   {"extra_write_paths": ["/home/you/.some_tool_cache"]}

``readable_paths``
------------------

Restricts a folder (and its subfolders) to read-only. Use it for example for a subfolder of your project
that should stay read-only even though the project itself is writable — e.g. sensitive raw data:

.. code-block:: json

   {"readable_paths": ["/data1/collab002/myproject/raw_data"]}

Global defaults
------------------

``~/.dangerous_claude/config.json`` sets defaults for every project, so you don't repeat
yourself. ``extra_write_paths``/``readable_paths`` there are added to whatever a project sets.
``writeable_home``/``always_use_dangerous_skip_permissions`` still prompt per project even with
a global value set. That global value is only a suggested default; confirm it explicitly rather
than inheriting it silently. A few settings only make sense globally:

- ``default_ro_paths`` — your cluster's storage paths that ``readable_paths`` can restrict
  (empty by default; see the "anything else" note above)
- ``project_config_filename`` — use a different project-file name than
  ``.dangerous_claude.json``, e.g. to keep existing ``.agentic_peer_project.json`` projects
  working unchanged
- ``system_prompt_note`` — an extra sentence appended to the sandbox's system prompt, e.g. a
  pointer to your own docs

``tools`` folders live in this repo's ``tools/`` directory for now — not yet configurable.

.. code-block:: json

   {
     "default_ro_paths": ["/data1/collab002", "/scratch"],
     "project_config_filename": ".agentic_peer_project.json"
   }

Migration reminders
----------------------

When ``~/.dangerous_claude/.version_last_migrated`` doesn't match this repo's ``.version``, the
session's system prompt tells Claude to read ``CHANGELOG.md`` first and help you migrate before
answering anything else. After that migration, update ``.version_last_migrated`` yourself; the
tool doesn't yet write it back automatically (see
`#9 <https://github.com/dpeerlab/dangerous_claude/issues/9>`_).

``env`` sets extra environment variables inside the container, e.g. ``AWS_PROFILE``. Global and
project ``env`` dicts merge key-by-key, and the project's value wins on collision:

.. code-block:: json

   {"env": {"AWS_PROFILE": "readonly"}}

This is not a perfect security boundary against a compromised agent
------------------------------------------------------------------------

This only limits filesystem writes. It doesn't block network access, and ``~/.claude``
credentials are always readable. A prompt-injected or otherwise compromised agent can still read
and exfiltrate anything it has access to.

See `Hijacking Claude Code via injected marketplace plugins
<https://www.promptarmor.com/resources/hijacking-claude-code-via-injected-marketplace-plugins>`_
for a real example of this kind of attack — ``dangerous_claude`` does not yet protect against it.
