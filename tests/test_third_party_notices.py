from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_consolidated_notice_covers_every_audited_publication_component() -> None:
    notice = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")

    for marker in (
        "Sphinx | 9.1.0",
        "PyData Sphinx Theme | 0.19.0",
        "Bootstrap | 5.3.3",
        "Font Awesome Free | 7.2.0",
        "Pygments | 2.20.0",
        "MathJax | 4.0.0",
        "`fncychap` | 1.34",
        "Noto Sans/Serif CJK SC",
        "TeX Gyre Termes and Heros",
        "DejaVu Sans and Sans Mono",
        "GUST Font License 1.0",
        "LPPL Version 1.3c  2008-05-04",
        "Bitstream Vera Fonts Copyright",
    ):
        assert marker in notice

    assert "neither select nor grant a license for DEAPack's" in notice
    assert "subject to the release sign-off record" in notice
    assert "complete `pdffonts` table" in notice


def test_notice_preserves_required_upstream_license_clauses() -> None:
    notice = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")

    assert notice.count("Redistribution and use in source and binary forms") == 3
    assert "Neither the name of the copyright holder nor the names of its" in notice
    assert "The above copyright notice and this permission notice shall be" in notice
    assert "SIL OPEN FONT LICENSE Version 1.1 - 26 February 2007" in notice
    assert "This is version 1.0, dated 22 June 2009, of the GUST Font License" in notice
    assert "preliminary version (2006-09-30)" not in notice
    assert "Copyright 2007\nUlf Lindgren" in notice
    assert "alter the upstream icon data" in notice
    assert "This work may be distributed and/or modified under the conditions" in notice
    assert "Everyone is allowed to distribute verbatim copies of this" in notice
    assert "DejaVu changes are in public domain" in notice


def test_every_publication_route_includes_the_single_notice_source() -> None:
    documentation_route = ROOT / "docs" / "legal" / "third-party-notices.md"
    handbook_route = ROOT / "book" / "legal-notices.md"
    assert documentation_route.read_text(encoding="utf-8") == (
        "```{include} ../../THIRD_PARTY_NOTICES.md\n```\n"
    )
    assert handbook_route.read_text(encoding="utf-8") == (
        "```{include} ../THIRD_PARTY_NOTICES.md\n```\n"
    )
    assert "legal/third-party-notices" in (ROOT / "docs" / "index.md").read_text(
        encoding="utf-8"
    )
    assert "legal-notices" in (ROOT / "book" / "index.md").read_text(encoding="utf-8")


def test_adapted_latex_fragments_carry_source_and_change_notices() -> None:
    configuration = (ROOT / "book" / "conf.py").read_text(encoding="utf-8")

    for marker in (
        "Modified excerpt from fncychap 1.34's Bjarne style",
        "Copyright 2007 Ulf Lindgren",
        "this modified excerpt is distributed under LPPL 1.3c",
        "Partial adaptation of Sphinx 9.1.0 sphinxlatexstylepage.sty",
        "distributed under BSD-2-Clause",
        'chapter "Third-Party Notices"',
    ):
        assert marker in configuration
