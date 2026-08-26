Permissions
============

Helps ensure that Claude can only read and write files that are important for your project.
Controlled by ``.agentic_peer_project.json`` in your project directory.

Default access
----------------

- Your project directory: read-write.
- Some default paths (``/data1``, ``/scratch``, ``/ifs``, ``/usersoftware``, ``/admin``,
  ``/localscratch``, and some others...): read-only
- ``$HOME``: read-write, unless ``writeable_home: false``
- ``/tmp``: always read-write
- ``~/.claude``: always read-write, so Claude can save its own state.
- Anything else: not visible at all, not even read-only.

``extra_write_paths``
--------------------

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


This is not a perfect security boundary against a compromised agent
--------------------------------------------------------

This only limits filesystem writes. It doesn't block network access, and ``~/.claude``
credentials are always readable. A prompt-injected or otherwise compromised agent can still read
and exfiltrate anything it has access to.

See `Hijacking Claude Code via injected marketplace plugins
<https://www.promptarmor.com/resources/hijacking-claude-code-via-injected-marketplace-plugins>`_
for a real example of this kind of attack — ``dangerous_claude`` does not yet protect against it.
