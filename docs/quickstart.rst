Quickstart
==========

Build the container
---------------------

.. code-block:: bash

   bash setup/build.sh

Builds a ``.sif`` into ``builds/`` with Claude Code, Node, ripgrep, and the SLURM client. Rebuild
periodically to pick up new Claude Code releases.

Run
----

.. code-block:: bash

   cd /abs/path/to/your/project
   ./dangerous_claude claude

Sandboxes the current directory — no work-dir argument, ``cd`` there first. Works with any
command, not just ``claude``:

.. code-block:: bash

   ./dangerous_claude bash
   ./dangerous_claude sbatch --version

First run in a project prompts for two settings and writes ``.dangerous_claude.json`` —
see :doc:`permissions`.
