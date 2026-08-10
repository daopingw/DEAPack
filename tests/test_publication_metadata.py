from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
    assert _top_level_scalar(citation, "version") == "2.0.1"
    assert _top_level_scalar(citation, "date-released") == "2026-08-10"
    assert _toml_scalar(pyproject, "requires-python") == ">=3.10,<3.14"
    assert '"Development Status :: 5 - Production/Stable"' in pyproject
    assert '"Development Status :: 4 - Beta"' not in pyproject
    assert "Pre-Alpha" not in pyproject
    assert "family-names: Wang" in citation
    assert "given-names: Daoping" in citation


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


def test_minimum_dependency_job_exercises_the_declared_scipy_floor() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "tests.yml").read_text(
        encoding="utf-8"
    )

    assert '"scipy>=1.15"' in pyproject
    assert "'scipy==1.15.0'" in workflow


def test_component_licenses_are_scoped_and_data_mapping_fails_closed() -> None:
    component_map = (ROOT / "COMPONENT_LICENSES.md").read_text(encoding="utf-8")
    data_map = (ROOT / "DATA_LICENSES.md").read_text(encoding="utf-8")
    notice = (ROOT / "NOTICE").read_text(encoding="utf-8")

    for marker in (
        "GPL-3.0-only",
        "CC-BY-NC-SA-4.0",
        "CC-BY-4.0",
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


def test_pypi_description_is_stable_release_specific_and_portable() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    description = (ROOT / "PYPI_README.md").read_text(encoding="utf-8")

    assert 'readme = "PYPI_README.md"' in pyproject
    assert "2.0.1" in description
    assert "DEAPack==2.0.1" in description
    assert "release candidate" not in description.lower()
    assert "https://github.com/daopingw/DEAPack/" in description
    assert "](docs/" not in description
    assert "](book/" not in description


def test_development_metadata_does_not_invent_publication_identifiers() -> None:
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    prohibited_top_level = (
        "doi",
        "commit",
        "preferred-citation",
    )

    for key in prohibited_top_level:
        assert re.search(rf"^{re.escape(key)}:", citation, re.MULTILINE) is None
    assert _top_level_scalar(citation, "date-released") == "2026-08-10"
    assert re.search(r"^\s+orcid:", citation, re.MULTILINE) is None
    assert not (ROOT / ".zenodo.json").exists()


def test_read_the_docs_uses_the_strict_package_documentation_build() -> None:
    configuration = (ROOT / ".readthedocs.yaml").read_text(encoding="utf-8")

    assert _top_level_scalar(configuration, "version") == "2"
    assert "configuration: docs/conf.py" in configuration
    assert "fail_on_warning: true" in configuration
    assert 'python: "3.12"' in configuration


def test_package_documentation_keeps_its_public_identity() -> None:
    documentation = (ROOT / "docs" / "conf.py").read_text(encoding="utf-8")

    assert 'project = "DEAPack Documentation"' in documentation
    assert 'author = "Dr Daoping Wang"' in documentation
    assert 'copyright = "2026, Daoping Wang / DEAPack"' in documentation
