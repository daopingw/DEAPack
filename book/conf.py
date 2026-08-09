"""Sphinx configuration for both editions of the DEAPack companion book."""

from __future__ import annotations

import os

language = os.environ.get("DEAPACK_BOOK_LANGUAGE", "en")
if language not in {"en", "zh_CN"}:
    raise ValueError(f"unsupported DEAPack Handbook language: {language!r}")

if language == "zh_CN":
    book_title = "数据包络分析"
    book_subtitle = "基于 Python 的效率、生产率与环境绩效分析"
    book_strapline = "理论、方法与实践的统一手册"
    project = f"{book_title}：{book_subtitle}"
else:
    book_title = "Data Envelopment Analysis"
    book_subtitle = (
        "Efficiency, Productivity, and Environmental Performance with Python"
    )
    book_strapline = "A Unified Handbook of Theory, Methods, and Practice"
    project = f"{book_title}: {book_subtitle}"
author = "Daoping Wang"
copyright = f"2026, {author}"
version = "Preview 1"
release = "Preview 1"

extensions = [
    "myst_parser",
    "sphinx.ext.mathjax",
    "sphinxcontrib.bibtex",
]

# Sphinx's default follows the floating ``mathjax@4`` CDN tag.  Release builds
# use an exact upstream version so already-reviewed HTML cannot silently change.
mathjax_path = "https://cdn.jsdelivr.net/npm/mathjax@4.0.0/tex-mml-chtml.js"

source_suffix = {".md": "markdown", ".rst": "restructuredtext"}
root_doc = "index"
exclude_patterns = [
    "_build",
    "_archive",
    "README.md",
    "CONTRIBUTING.md",
    "HANDBOOK_CONTRIBUTION_POLICY.md",
    "figures/FIGURE_WORKFLOW.md",
    "Thumbs.db",
    ".DS_Store",
]

locale_dirs = ["locale/"]
gettext_compact = False
gettext_uuid = True
if language == "zh_CN":
    # Use a reviewed localized SVG when one exists and fall back to the shared
    # technical figure otherwise. The source labels and localized variants are
    # kept aligned by the fail-closed figure catalog.
    figure_language_filename = "{path}{language}/{basename}{ext}"

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

bibtex_bibfiles = ["references.bib"]
bibtex_reference_style = "author_year"

html_theme = "pydata_sphinx_theme"
html_title = project
# Only theme assets are copied wholesale into the published site.  Figures live
# under ``_static/figures`` as source assets, but Sphinx publishes only those
# actually referenced by the admitted handbook route.
html_static_path = ["_theme"]
html_css_files = ["custom.css"]
html_theme_options = {
    "logo": {"text": "DEAPack 手册" if language == "zh_CN" else "DEAPack Handbook"},
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
if language == "zh_CN":
    html_theme_options["header_dropdown_text"] = "更多"
html_context = {
    "github_user": "daopingw",
    "github_repo": "DEAPack",
    "github_version": "main",
    "doc_path": "book",
}

# The cover separates the title, formal subtitle, and strapline.  The complete
# title belongs in PDF metadata, but it is too long for letter-sized running
# heads. Sphinx normally uses one LaTeX title for all three jobs, so keep the
# concise document title for running heads and restore the layered title only
# while the cover is made.
latex_cover_title = book_title
latex_cover_subtitle = book_subtitle
if language == "zh_CN":
    latex_cover_subtitle_lines = (
        "基于 Python 的效率、生产率",
        "与环境绩效分析",
    )
else:
    latex_cover_subtitle_lines = (
        "Efficiency, Productivity, and",
        "Environmental Performance with Python",
    )
latex_cover_strapline = book_strapline
latex_metadata_title = project
latex_running_title = "DEAPack 手册" if language == "zh_CN" else "DEAPack Handbook"
latex_documents = [
    (
        root_doc,
        "deapack-handbook-zh.tex" if language == "zh_CN" else "deapack-handbook.tex",
        latex_running_title,
        author,
        "manual",
    )
]
# Third-party provenance for the two adapted LaTeX fragments below is retained
# in both the generated TeX source and ``legal-notices.md``.  These notices do
# not set the license for unrelated Handbook or DEAPack material.
latex_elements = {
    "preamble": r"""
\makeatletter
% Modified excerpt from fncychap 1.34's Bjarne style.
% Copyright 2007 Ulf Lindgren. Upstream: LPPL 1.3 or (at your option)
% any later version; this modified excerpt is distributed under LPPL 1.3c.
% Change: preserve the appendix path and hyphenate English compounds 21--99.
% Complete attribution, modification record, source link, and unmodified LPPL
% text are included in the Handbook chapter "Third-Party Notices".
% fncychap's Bjarne style concatenates the tens and units names (TWENTYONE).
% Preserve its appendix path while using standard English compounds from 21 onward.
\renewcommand{\TheAlphaChapter}{%
  \ifinapp
    \thechapter
  \else
    \setcounter{AlphaCnt}{\c@chapter}%
    \ifnum\c@chapter<20
      \AlphaNo
    \else
      \AlphaDecNo
      \ifnum\number\theAlphaCnt>0
        -\AlphaNo
      \fi
    \fi
  \fi
}

% Partial adaptation of Sphinx 9.1.0 sphinxlatexstylepage.sty,
% copyright 2007--2025 the Sphinx team, distributed under BSD-2-Clause.
% Change: use footnotesize for the running section and chapter marks.
% The complete Sphinx notice and source link are included in the Handbook
% chapter "Third-Party Notices".
\fancypagestyle{normal}{%
  \fancyhf{}%
  \fancyfoot[RO]{{\py@HeaderFamily\thepage}}%
  \fancyfoot[LO]{{\footnotesize\py@HeaderFamily\nouppercase{\rightmark}}}%
  \fancyhead[RO]{{\py@HeaderFamily \@title\sphinxheadercomma\py@release}}%
  \if@twoside
    \fancyfoot[LE]{{\py@HeaderFamily\thepage}}%
    \fancyfoot[RE]{{\footnotesize\py@HeaderFamily\nouppercase{\leftmark}}}%
    \fancyhead[LE]{{\py@HeaderFamily \@title\sphinxheadercomma\py@release}}%
  \fi
  \renewcommand{\headrulewidth}{0.4pt}%
  \renewcommand{\footrulewidth}{0.4pt}%
}
\makeatother
""",
    # The only generated index entries currently come from the book's glossary.
    # Name that locator honestly; a subject index is a separate editorial project.
    "printindex": (
        r"\renewcommand{\indexname}{术语索引}\printindex"
        if language == "zh_CN"
        else r"\renewcommand{\indexname}{Glossary Index}\printindex"
    ),
    "maketitle": rf"""
\makeatletter
\let\deapackrunningtitle\@title
\def\@title{{%
\texorpdfstring{{%
{latex_cover_title}\\[1.25ex]
{{\Large {latex_cover_subtitle_lines[0]}\\[0.35ex]
{latex_cover_subtitle_lines[1]}}}\\[2ex]
{{\large\itshape {latex_cover_strapline}}}%
}}{{{latex_metadata_title}}}%
}}
\hypersetup{{pdftitle={{{latex_metadata_title}}}}}
\sphinxmaketitle
\let\@title\deapackrunningtitle
\makeatother
    """,
}

if language == "zh_CN":
    latex_engine = "xelatex"
    cjk_main_font = os.environ.get("DEAPACK_CJK_MAIN_FONT", "Noto Serif CJK SC")
    cjk_sans_font = os.environ.get("DEAPACK_CJK_SANS_FONT", "Noto Sans CJK SC")
    latex_elements["fontpkg"] = rf"""
\setmainfont{{TeX Gyre Termes}}
\setsansfont{{TeX Gyre Heros}}
\setmonofont{{DejaVu Sans Mono}}
\setCJKmainfont{{{cjk_main_font}}}
\setCJKsansfont{{{cjk_sans_font}}}
\setCJKmonofont{{{cjk_sans_font}}}
"""


def setup(app):  # type: ignore[no-untyped-def]
    """Keep the Chinese browser search stemmer aligned with Sphinx's JS asset."""

    if language != "zh_CN":
        return

    from sphinx.search.zh import SearchChinese

    if SearchChinese.js_stemmer_rawcode != "english-stemmer.js":
        return

    # Sphinx 9.1 embeds ``EnglishStemmer`` for Chinese Latin terms but aliases
    # the absent ``ChineseStemmer`` name in ``language_data.js``.  Registering
    # the same search implementation with the embedded stemmer's actual name
    # preserves Chinese tokenisation and makes browser-side search executable.
    class SearchChineseWithMatchingStemmer(SearchChinese):
        language_name = "English"

    app.add_search_language(SearchChineseWithMatchingStemmer)
