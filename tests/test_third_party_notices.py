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
    ):
        assert marker in notice

    assert "neither select nor grant a license for DEAPack's" in notice


def test_notice_preserves_required_upstream_license_clauses() -> None:
    notice = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")

    assert notice.count("Redistribution and use in source and binary forms") == 3
    assert "Neither the name of the copyright holder nor the names of its" in notice
    assert "The above copyright notice and this permission notice shall be" in notice
    assert "alter the upstream icon data" in notice


def test_documentation_route_includes_the_single_notice_source() -> None:
    documentation_route = ROOT / "docs" / "legal" / "third-party-notices.md"
    assert documentation_route.read_text(encoding="utf-8") == (
        "```{include} ../../THIRD_PARTY_NOTICES.md\n```\n"
    )
    legal_index = (ROOT / "docs" / "legal" / "index.md").read_text(encoding="utf-8")
    developer_index = (ROOT / "docs" / "developer" / "index.md").read_text(
        encoding="utf-8"
    )
    assert "third-party-notices" in legal_index
    assert "/legal/index" in developer_index
