# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

sys.path.insert(0, os.path.abspath("../../src"))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "xnetcdf"
copyright = "2026, xnetcdf Development Team"
author = "xnetcdf Development Team"
version = "0.1.0"
release = "0.1.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.extlinks",
    #   "sphinx.ext.napoleon",  # <-- Add this for Google/NumPy docstring style
]

# Tell Intersphinx where to find the documentation mappings for other libraries
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    # "netCDF4": ("https://unidata.github.io/netcdf4-python/", None),
    # "fsspec": ("https://filesystem-spec.readthedocs.io/", None),
}

# Create a shortcut alias named 'netcdf'
extlinks = {
    "netCDF4": ("https://unidata.github.io/netcdf4-python/%s", "%s"),
}

templates_path = ["_templates"]
exclude_patterns = []

# Force all code blocks to wrap long lines cleanly
pygments_style = "sphinx"
sphinx_elements = {
    "preamble": r"\usepackage{fvextra}\fvset{breaklines=true}",
}

# The modern standard way to do this for HTML builds:
html_codeblock_linenos_style = "inline"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"

html_static_path = ["_static"]

# Tell Sphinx to parse internal page headers down to the level you
# want (h2/h3)
html_toc_object_entries_type = "domain"

# If your theme options block exists, add/check this:
html_theme_options = {
    "sidebar_hide_name": False,
    #    "light_logo": "xnetcdf_logo_light.png",
    #    "dark_logo": "xnetcdf_logo_dark.png",
    # This prevents Furo from aggressively hiding collapsed child components
    "navigation_with_keys": True,
}
# Force single backticks to automatically link to Python documentation
# objects
default_role = "py:obj"


def setup(app):
    """Inject the custom.css file into the build."""
    app.add_css_file("custom.css")
