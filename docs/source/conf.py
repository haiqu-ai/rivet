# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

import os
import sys
from typing import List

import sphinx_pdj_theme

sys.path.insert(0, os.path.abspath("../.."))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "QML Compiler"
copyright = "2024, Haiqu Inc."  # pylint: disable=redefined-builtin
author = "Haiqu Inc."

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "nbsphinx",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.mathjax",  # math rendering in html
    "sphinx.ext.napoleon",  # allows google- and numpy- style docstrings
    "IPython.sphinxext.ipython_console_highlighting",
    "matplotlib.sphinxext.plot_directive",
]

# since our notebooks can involve network I/O (or even costing $), we don't want them to be
# run every time we build the docs. Instead, just use the pre-executed outputs.
nbsphinx_execute = "never"

# In addition, we set the mathjax path to v3, which allows \ket{} (and other commands) to render
mathjax_path = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"
autosummary_generate = True

templates_path = ["_templates"]

# Using `modules` in index.rst gets the first package and ignores additional included packages.
# Listing out modules explicitly causes building docs to throw error looking for `modules.rst`,
# so add to excluded search patterns as per suggestion here: https://stackoverflow.com/a/15438962
exclude_patterns: List[str] = [
    "modules.rst",
    "setup.rst",
]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = "sphinx_rtd_theme"
html_theme_options = {
    # "logo_only": True,
    # "home_link": "hide"  # theme_home_link
}

# html_theme = "groundwork"

html_theme = "sphinx_pdj_theme"
html_theme_path = [sphinx_pdj_theme.get_html_theme_path()]

html_static_path = ["_static"]
html_logo = "_static/logos/haiquai_logo.jpeg"
html_css_files = [
    "css/docs-haiqu.css",
    # "css/rtd_dark.css",
]
html_favicon = "_static/logos/haiquai_logo.jpeg"
