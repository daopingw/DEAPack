"""Sphinx configuration for versioned DEAPack package documentation."""

from __future__ import annotations

import deapack

project = "DEAPack Documentation"
author = "DEAPack contributors"
copyright = "2026, DEAPack contributors"
release = deapack.__version__

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
]

# Sphinx's default follows the floating ``mathjax@4`` CDN tag.  Release builds
# use an exact upstream version so already-reviewed HTML cannot silently change.
mathjax_path = "https://cdn.jsdelivr.net/npm/mathjax@4.0.0/tex-mml-chtml.js"

source_suffix = {".md": "markdown", ".rst": "restructuredtext"}
root_doc = "index"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

language = "en"
locale_dirs = ["locale/"]
gettext_compact = False
gettext_uuid = True

myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "fieldlist",
    "substitution",
]
myst_heading_anchors = 4
numfig = True

autosummary_generate = True
autodoc_typehints = "description"
autodoc_class_signature = "separated"
napoleon_google_docstring = True
napoleon_numpy_docstring = True

html_theme = "pydata_sphinx_theme"
html_title = f"DEAPack {release}"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_theme_options = {
    "logo": {"text": "DEAPack Documentation"},
    "show_toc_level": 2,
    "navigation_with_keys": True,
    "use_edit_page_button": True,
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/daopingw/DEAPack",
            "icon": "fa-brands fa-github",
        }
    ],
}
html_context = {
    "github_user": "daopingw",
    "github_repo": "DEAPack",
    "github_version": "main",
    "doc_path": "docs",
}
