"""Sphinx configuration for the dangerous_claude docs."""

project = "dangerous_claude"
author = "Tobias Krause, Nick Markov"

extensions = []

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_show_copyright = False
