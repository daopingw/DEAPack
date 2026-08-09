from __future__ import annotations

import re
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK_TITLE = "Data Envelopment Analysis"
BOOK_SUBTITLE = "Efficiency, Productivity, and Environmental Performance with Python"
BOOK_STRAPLINE = "A Unified Handbook of Theory, Methods, and Practice"
BOOK_METADATA_TITLE = f"{BOOK_TITLE}: {BOOK_SUBTITLE}"


def _top_level_scalar(text: str, key: str) -> str:
    match = re.search(
        rf"^{re.escape(key)}:\s*(?P<value>[^\n]+)$",
        text,
        flags=re.MULTILINE,
    )
    assert match is not None, f"missing top-level {key!r}"
    return match.group("value").strip().strip("\"'")


def _toml_scalar(text: str, key: str) -> str:
    match = re.search(
        rf"^{re.escape(key)}\s*=\s*(?P<value>[^\n]+)$",
        text,
        flags=re.MULTILINE,
    )
    assert match is not None, f"missing TOML {key!r}"
    return match.group("value").strip().strip("\"'")


def test_software_citation_metadata_is_complete_and_version_aligned() -> None:
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert _top_level_scalar(citation, "cff-version") == "1.2.0"
    assert _top_level_scalar(citation, "title") == "DEAPack"
    assert _top_level_scalar(citation, "type") == "software"
    assert _top_level_scalar(citation, "license") == "GPL-3.0-only"
    assert _top_level_scalar(citation, "repository-code") == (
        "https://github.com/daopingw/DEAPack"
    )
    assert _top_level_scalar(citation, "version") == _toml_scalar(
        pyproject,
        "version",
    )
    assert _top_level_scalar(citation, "version") == "2.0.0rc1"
    assert _toml_scalar(pyproject, "requires-python") == ">=3.10,<3.14"
    assert '"Development Status :: 4 - Beta"' in pyproject
    assert "Pre-Alpha" not in pyproject
    assert "family-names: Wang" in citation
    assert "given-names: Daoping" in citation
    assert BOOK_METADATA_TITLE in " ".join(citation.split())


def test_distribution_uses_supported_pep639_license_metadata() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    build_system, project = pyproject.split("[project]", maxsplit=1)

    assert 'requires = ["setuptools==84.0.0"]' in build_system
    assert re.search(
        r'^license = "GPL-3.0-only AND CC-BY-4.0 AND MIT"$',
        project,
        re.MULTILINE,
    )
    for license_file in (
        '"LICENSE"',
        '"NOTICE"',
        '"DATA_LICENSES.md"',
        '"LICENSES/CC-BY-4.0.txt"',
        '"LICENSES/MIT-DataEnvelopmentAnalysis.jl.txt"',
        '"LICENSES/MIT-BenchmarkingEconomicEfficiency.jl.txt"',
    ):
        assert license_file in project
    assert "include-package-data = false" in project
    assert "License ::" not in project

    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "GNU GENERAL PUBLIC LICENSE" in license_text
    assert "Version 3, 29 June 2007" in license_text
    assert license_text == (ROOT / "LICENSES" / "GPL-3.0-only.txt").read_text(
        encoding="utf-8"
    )


def test_component_licenses_are_scoped_and_data_mapping_fails_closed() -> None:
    component_map = (ROOT / "COMPONENT_LICENSES.md").read_text(encoding="utf-8")
    data_map = (ROOT / "DATA_LICENSES.md").read_text(encoding="utf-8")
    notice = (ROOT / "NOTICE").read_text(encoding="utf-8")

    for marker in (
        "GPL-3.0-only",
        "CC-BY-NC-SA-4.0",
        "CC-BY-4.0",
        "All Rights Reserved",
        "Copyright © 2026 Daoping Wang",
        "confirmed that no DEAPack 2.0 copy was delivered",
    ):
        assert marker in component_map
    for dataset_id in (
        "ren_cas_directional_scale",
        "revenue_5x2",
        "revenue_8x2",
    ):
        assert f"`{dataset_id}`" in data_map
    assert "These mappings clear all 33 exact current content fingerprints" in data_map
    assert "All 33 current dataset fingerprints have item-level mappings" in notice


def test_pypi_description_is_release_candidate_specific_and_portable() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    description = (ROOT / "PYPI_README.md").read_text(encoding="utf-8")

    assert 'readme = "PYPI_README.md"' in pyproject
    assert "2.0.0rc1" in description
    assert "DEAPack==2.0.0rc1" in description
    assert "https://github.com/daopingw/DEAPack/" in description
    assert "](docs/" not in description
    assert "](book/" not in description


def test_development_metadata_does_not_invent_publication_identifiers() -> None:
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    prohibited_top_level = (
        "doi",
        "date-released",
        "commit",
        "preferred-citation",
    )

    for key in prohibited_top_level:
        assert re.search(rf"^{re.escape(key)}:", citation, re.MULTILINE) is None
    assert re.search(r"^\s+orcid:", citation, re.MULTILINE) is None
    assert not (ROOT / ".zenodo.json").exists()


def test_read_the_docs_projects_are_separate_strict_sphinx_builds() -> None:
    expected = {
        ROOT / "book" / ".readthedocs.yaml": "book/conf.py",
        ROOT / "book" / ".readthedocs-zh.yaml": "book/conf_zh.py",
        ROOT / "docs" / ".readthedocs.yaml": "docs/conf.py",
    }

    for path, configuration in expected.items():
        text = path.read_text(encoding="utf-8")
        assert _top_level_scalar(text, "version") == "2"
        assert f"configuration: {configuration}" in text
        assert "fail_on_warning: true" in text
        assert 'python: "3.12"' in text


def test_book_build_metadata_is_deterministic_and_explicitly_preview() -> None:
    configuration = (ROOT / "book" / "conf.py").read_text(encoding="utf-8")
    index = (ROOT / "book" / "index.md").read_text(encoding="utf-8")
    citing = (ROOT / "book" / "citing.md").read_text(encoding="utf-8")

    assert "date.today" not in configuration
    assert 'copyright = f"2026, {author}"' in configuration
    assert 'version = "Preview 1"' in configuration
    assert 'release = "Preview 1"' in configuration
    assert "html_title = project" in configuration
    assert index.startswith(f"# {BOOK_TITLE}\n")
    assert f"*{BOOK_SUBTITLE}*" in index
    assert BOOK_STRAPLINE in index
    normalized_citing = " ".join(re.sub(r"(?m)^>\s?", "", citing).split())
    assert BOOK_METADATA_TITLE in normalized_citing
    assert "Bilingual Handbook Preview 1" in citing
    assert "one development manuscript" in citing
    assert "English development manuscript" not in index


def test_book_title_does_not_replace_the_package_documentation_identity() -> None:
    documentation = (ROOT / "docs" / "conf.py").read_text(encoding="utf-8")

    assert 'project = "DEAPack Documentation"' in documentation
    assert BOOK_METADATA_TITLE not in documentation


def test_book_pdf_keeps_full_metadata_title_and_a_concise_running_title() -> None:
    configuration = runpy.run_path(str(ROOT / "book" / "conf.py"))

    assert configuration["book_title"] == BOOK_TITLE
    assert configuration["book_subtitle"] == BOOK_SUBTITLE
    assert configuration["book_strapline"] == BOOK_STRAPLINE
    assert configuration["project"] == BOOK_METADATA_TITLE
    assert configuration["latex_cover_title"] == BOOK_TITLE
    assert configuration["latex_cover_subtitle"] == BOOK_SUBTITLE
    assert configuration["latex_cover_subtitle_lines"] == (
        "Efficiency, Productivity, and",
        "Environmental Performance with Python",
    )
    assert configuration["latex_cover_strapline"] == BOOK_STRAPLINE
    assert configuration["latex_metadata_title"] == BOOK_METADATA_TITLE
    assert configuration["latex_running_title"] == "DEAPack Handbook"
    assert configuration["latex_documents"] == [
        (
            "index",
            "deapack-handbook.tex",
            "DEAPack Handbook",
            "Daoping Wang",
            "manual",
        )
    ]

    make_title = configuration["latex_elements"]["maketitle"]
    assert BOOK_TITLE in make_title
    assert "Efficiency, Productivity, and\\\\[0.35ex]" in make_title
    assert "Environmental Performance with Python" in make_title
    assert BOOK_STRAPLINE in make_title
    assert rf"\hypersetup{{pdftitle={{{BOOK_METADATA_TITLE}}}}}" in make_title
    assert "\\texorpdfstring" in make_title
    assert "\\sphinxmaketitle" in make_title
    assert "\\let\\@title\\deapackrunningtitle" in make_title

    preamble = configuration["latex_elements"]["preamble"]
    assert "\\fancyfoot[LO]" in preamble
    assert "\\fancyfoot[RE]" in preamble
    assert "\\footnotesize\\py@HeaderFamily" in preamble

    # MiKTeX fncychap 1.34's Bjarne style prints TWENTYONE by default.
    # The handbook keeps TWENTY for 20 and inserts the standard hyphen only
    # when a non-zero units name remains (TWENTY-ONE, TWENTY-TWO, ...).
    assert "\\renewcommand{\\TheAlphaChapter}" in preamble
    assert "\\AlphaDecNo" in preamble
    assert "\\ifnum\\number\\theAlphaCnt>0" in preamble
    assert "-\\AlphaNo" in preamble

    assert configuration["latex_elements"]["printindex"] == (
        r"\renewcommand{\indexname}{Glossary Index}\printindex"
    )
