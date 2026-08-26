Integration
============

Shell alias
-------------

Wrap the real ``claude`` binary so it transparently runs sandboxed. For example, add to ``~/.bashrc``:

.. code-block:: bash

   export USE_AGENTIC_PROJECT=true
   claude() {
       if [[ "${USE_AGENTIC_PROJECT}" == "true" ]]; then
           /path/to/dangerous_claude claude "$@"
       else
           command claude "$@"
       fi
   }

Plain ``claude`` now launches sandboxed from wherever you are. Bypass it for one call with
``USE_AGENTIC_PROJECT=false claude``, or ``command claude``.
