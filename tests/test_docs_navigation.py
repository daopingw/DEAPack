from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_documentation_header_uses_five_section_landings() -> None:
    index_text = (ROOT / "docs" / "index.md").read_text(encoding="utf-8")
    root_tree = index_text.split("```{toctree}", maxsplit=1)[1].split(
        "```", maxsplit=1
    )[0]
    entries = [
        line.strip()
        for line in root_tree.splitlines()
        if line.strip() and not line.strip().startswith(":")
    ]

    assert entries == [
        "getting-started/index",
        "user-guide/index",
        "reference/index",
        "api/index",
        "developer/index",
    ]


def test_documentation_theme_keeps_section_and_page_navigation_separate() -> None:
    conf_text = (ROOT / "docs" / "conf.py").read_text(encoding="utf-8")

    assert '"header_links_before_dropdown": 5' in conf_text
    assert '"navigation_depth": 3' in conf_text
    assert '"show_nav_level": 1' in conf_text
    assert '"collapse_navigation": False' in conf_text
    assert '"show_toc_level": 2' in conf_text

    for landing in (
        "getting-started/index.md",
        "user-guide/index.md",
        "reference/index.md",
        "api/index.md",
        "developer/index.md",
    ):
        assert "```{toctree}" in (ROOT / "docs" / landing).read_text(encoding="utf-8")


def test_documentation_code_blocks_enable_one_click_copying() -> None:
    conf_text = (ROOT / "docs" / "conf.py").read_text(encoding="utf-8")

    assert '"sphinx_copybutton"' in conf_text
    assert 'copybutton_exclude = ".linenos, .gp"' in conf_text

    project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    constraint = (ROOT / "constraints" / "release-python312.txt").read_text(
        encoding="utf-8"
    )
    assert '"sphinx-copybutton>=0.5.2"' in project
    assert "sphinx-copybutton==0.5.2" in constraint
