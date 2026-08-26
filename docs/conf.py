"""Sphinx configuration for the dangerous_claude docs."""

import os

project = "dangerous_claude"
author = "Tobias Krause, Nick Markov"

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(_root, ".version")) as _f:
    release = _f.read().strip()
version = release

extensions = []

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_show_copyright = False
