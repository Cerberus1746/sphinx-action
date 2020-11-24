import os
import sys
sys.path.insert(0, os.path.abspath('..'))


project = "sphinx_action"
copyright = "2020, Ammar Askar"
author = "Ammar Askar"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.doctest",
    "sphinx_autodoc_typehints",
]


templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "nature"
html_static_path = ["_static"]
