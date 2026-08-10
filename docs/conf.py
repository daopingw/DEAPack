"""Sphinx configuration for versioned DEAPack package documentation."""

from __future__ import annotations

import deapack

project = "DEAPack Documentation"
author = "Dr Daoping Wang"
copyright = "2026, Daoping Wang / DEAPack"
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
exclude_patterns = [
    "_build",
    # Local release operations are intentionally outside the public reader
    # documentation tree.
    "developer/releasing.md",
    "Thumbs.db",
    ".DS_Store",
]

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
    # Keep the header at the level of the five reader-facing sections.  Their
    # children belong in the primary (left) sidebar, not in a giant ``More``
    # menu in the navbar.
    "header_links_before_dropdown": 5,
    "navigation_depth": 3,
    # Open the active branch only; expanding every model family would merely
    # move the former navbar overload into the left sidebar.
    "show_nav_level": 1,
    "collapse_navigation": False,
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
