# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
# sys.path.insert(0, os.path.abspath('.'))
path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(path, '..', '..'))
sys.path.insert(0, os.path.join(path, '..', '..', 'bca_tool_code'))

# -- Project information -----------------------------------------------------

project = 'usepa-cti-bca'
copyright = '2019, OTAQ ASD'
author = 'OTAQ ASD'

# The full version, including alpha/beta/rc tags
release = "1.2.0"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.napoleon',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode',
    'sphinx.ext.todo'
]

autodoc_default_options = {
    'member-order': 'bysource',  # other option is 'alphabetical'
    'special-members': '__init__',
}

# autodoc_member_order = 'bysource'  # 'bysource' presents autodocs in the same order as they appear in the code, as opposed to alphabetical

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    '*setup*',
    '*exe_entry*'
]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
# html_theme = 'classic'
html_theme = 'sphinx_rtd_theme'
numfig = True
todo_include_todos = True

html_theme_options = {
    'navigation_depth': 5,
    'style_nav_header_background': '#0071BC',
    'collapse_navigation': False,
}

# EPA Palette
# html_theme_options = {
#     "stickysidebar": "true",
#     "sidebarwidth": "30em",
#     "sidebarbgcolor": "#0071BC",
#     "sidebartextcolor": "#FFFFFF",
#     "sidebarlinkcolor": "#FFFFFF",
#     "relbarbgcolor": "#205493",
#     "textcolor": "#205493",
#     "linkcolor": "#205493",
#     "visitedlinkcolor": "#205493",
#     "headtextcolor": "#205493",
#     "headlinkcolor": "#205493",
#     "footerbgcolor": "#112E51"
# }

# html_sidebars = {
#    '**': ['globaltoc.html', 'sourcelink.html', 'searchbox.html'],
#    'using/windows': ['windowssidebar.html', 'searchbox.html'],
# }

# -- Options for  LaTeX output -------------------------------------------------

latex_elements = {
  'extraclassoptions': 'openany,oneside'
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['_static']


# set top level document to index.rst:
master_doc = 'index'

add_module_names = False
