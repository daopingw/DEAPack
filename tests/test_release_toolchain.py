from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import release_toolchain

ROOT = Path(__file__).resolve().parents[1]


def _inventory_payload() -> dict[str, object]:
    notice_sha256 = "2" * 64

    def site_record(path: str) -> dict[str, object]:
        html_count, notice_path = release_toolchain.SITE_CONTRACTS[path]
        html_paths = [notice_path, "index.html"]
        html_paths.extend(
            f"page-{index:03d}.html" for index in range(html_count - len(html_paths))
        )
        files = [{"path": name, "size": 1, "sha256": "3" * 64} for name in html_paths]
        for name in (
            "bootstrap.js.LICENSE.txt",
            "fontawesome.js.LICENSE.txt",
        ):
            files.append(
                {
                    "path": f"_static/scripts/{name}",
                    "size": 1,
                    "sha256": "4" * 64,
                }
            )
        files.sort(key=lambda item: str(item["path"]))
        return {
            "path": path,
            "html_file_count": html_count,
            "mathjax_reference_count": 1,
            "mathjax_urls": [release_toolchain.MATHJAX_URL],
            "copied_notice_sha256": {
                "bootstrap.js.LICENSE.txt": "4" * 64,
                "fontawesome.js.LICENSE.txt": "4" * 64,
            },
            "consolidated_notice_path": notice_path,
            "consolidated_notice_sha256": "3" * 64,
            "site_files": files,
            "site_tree_sha256": release_toolchain._canonical_sha256({"files": files}),
        }

    value: dict[str, object] = {
        "schema": release_toolchain.SCHEMA,
        "state": "verified",
        "scope": release_toolchain.INVENTORY_SCOPE,
        "constraint": {
            "path": "constraints/release-python312.txt",
            "sha256": "1" * 64,
            "direct_pins": [
                {"name": name, "version": version}
                for name, version in sorted(release_toolchain.EXPECTED_PINS.items())
            ],
        },
        "profile": "release",
        "runtime": {
            "python_implementation": "CPython",
            "python_version": "3.12.9",
            "platform_system": "Linux",
            "platform_release": "6.8.0",
            "platform_machine": "x86_64",
        },
        "python_distributions": [
            {
                "name": name,
                "normalised_name": name,
                "version": version,
                "direct_constraint": True,
                "license_expression": "MIT",
                "license_classifiers": [],
                "license_text_sha256": None,
                "license_files": [],
            }
            for name, version in sorted(release_toolchain.EXPECTED_PINS.items())
        ],
        "rendered_components": [
            {
                "name": "Sphinx generated HTML assets",
                "version": "9.1.0",
                "license": "BSD-2-Clause",
                "source_distribution": "Sphinx",
                "source_license_files": [
                    {"path": "LICENSE", "sha256": "9" * 64, "size": 1}
                ],
            },
            {
                "name": "PyData Sphinx Theme",
                "version": "0.19.0",
                "license": "BSD-3-Clause",
                "source_distribution": "pydata-sphinx-theme",
                "source_license_files": [
                    {"path": "LICENSE", "sha256": "9" * 64, "size": 1}
                ],
            },
            {
                "name": "Bootstrap",
                "version": "5.3.3",
                "license": "MIT",
                "source_distribution": "pydata-sphinx-theme",
                "source_notice_path": "static/bootstrap.LICENSE.txt",
                "source_notice_sha256": "a" * 64,
            },
            {
                "name": "Font Awesome Free",
                "version": "7.2.0",
                "license": "MIT AND CC-BY-4.0 AND OFL-1.1",
                "source_distribution": "pydata-sphinx-theme",
                "source_notice_path": "static/fontawesome.LICENSE.txt",
                "source_notice_sha256": "b" * 64,
            },
            {
                "name": "Pygments generated stylesheet",
                "version": "2.20.0",
                "license": "BSD-2-Clause",
                "source_distribution": "Pygments",
                "source_license_files": [
                    {"path": "LICENSE", "sha256": "c" * 64, "size": 1}
                ],
            },
            {
                "name": "MathJax",
                "version": release_toolchain.MATHJAX_VERSION,
                "license": "Apache-2.0",
                "delivery": "exact-version CDN reference; not copied into the site",
                "url": release_toolchain.MATHJAX_URL,
            },
        ],
        "consolidated_notice_source": {
            "path": "THIRD_PARTY_NOTICES.md",
            "sha256": notice_sha256,
        },
        "mathjax_configuration": [
            {"path": path, "sha256": "d" * 64}
            for path in release_toolchain.EXPECTED_MATHJAX_CONFIGURATION
        ],
        "rendered_sites": [
            site_record(path) for path in release_toolchain.SITE_CONTRACTS
        ],
        "system_toolchain": {
            "state": release_toolchain.SYSTEM_TOOLCHAIN_STATE,
            "packages": [],
            "tools": [],
            "font_sources": [],
        },
        "pdf_font_inventories": [],
        "limitations": list(release_toolchain.INVENTORY_LIMITATIONS),
        "generator": {
            "path": "scripts/release_toolchain.py",
            "sha256": "a" * 64,
        },
    }
    value["inventory_sha256"] = release_toolchain._canonical_sha256(value)
    return value


def test_release_constraint_is_exact_complete_and_direct_only() -> None:
    pins = release_toolchain.parse_constraint()
    assert pins == release_toolchain.EXPECTED_PINS
    assert pins["setuptools"] == "84.0.0"
    assert pins["sphinx"] == "9.1.0"
    assert pins["pydata-sphinx-theme"] == "0.19.0"
    assert pins["pygments"] == "2.20.0"


@pytest.mark.parametrize(
    ("original", "replacement"),
    (
        ("build==1.5.0", "build>=1.5.0"),
        ("Sphinx==9.1.0", "Sphinx==9.2.0"),
        ("twine==7.0.0", "twine==7.0.0; python_version >= '3.12'"),
    ),
)
def test_release_constraint_rejects_ranges_markers_and_version_drift(
    tmp_path: Path,
    original: str,
    replacement: str,
) -> None:
    source = release_toolchain.DEFAULT_CONSTRAINT.read_text(encoding="utf-8")
    candidate = tmp_path / "candidate.txt"
    candidate.write_text(source.replace(original, replacement), encoding="utf-8")
    with pytest.raises(ValueError):
        release_toolchain.parse_constraint(candidate)


def test_profile_verifier_fails_on_installed_direct_pin_drift(monkeypatch) -> None:
    installed = {
        name: SimpleNamespace(version=version)
        for name, version in release_toolchain.EXPECTED_PINS.items()
    }
    monkeypatch.setattr(
        release_toolchain,
        "_installed_distributions",
        lambda: installed,
    )
    release_toolchain.verify_installed(profile="release")
    installed["build"] = SimpleNamespace(version="1.5.1")
    with pytest.raises(ValueError, match=r"build==1\.5\.1"):
        release_toolchain.verify_installed(profile="release")


def test_inventory_digest_binds_direct_pins_and_rendered_component_versions() -> None:
    value = _inventory_payload()
    assert release_toolchain.validate_inventory_payload(value) == value

    tampered = _inventory_payload()
    tampered["rendered_components"][2]["version"] = "5.3.4"  # type: ignore[index]
    core = dict(tampered)
    core.pop("inventory_sha256")
    tampered["inventory_sha256"] = release_toolchain._canonical_sha256(core)
    with pytest.raises(ValueError, match="rendered-component versions"):
        release_toolchain.validate_inventory_payload(tampered)


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    (
        ("runtime", {}, "runtime"),
        ("mathjax_configuration", [], "MathJax"),
        ("rendered_sites", [], "rendered-site"),
        ("system_toolchain", {}, "system inventory"),
        ("limitations", [], "limitations"),
        ("generator", {}, "generator"),
    ),
)
def test_inventory_cannot_self_resign_empty_required_evidence(
    field: str,
    replacement: object,
    message: str,
) -> None:
    value = _inventory_payload()
    value[field] = replacement
    core = dict(value)
    core.pop("inventory_sha256")
    value["inventory_sha256"] = release_toolchain._canonical_sha256(core)
    with pytest.raises(ValueError, match=message):
        release_toolchain.validate_inventory_payload(value)


def test_inventory_rejects_resigned_site_tree_drift() -> None:
    value = _inventory_payload()
    sites = value["rendered_sites"]
    assert isinstance(sites, list)
    sites[0]["site_tree_sha256"] = "0" * 64
    core = dict(value)
    core.pop("inventory_sha256")
    value["inventory_sha256"] = release_toolchain._canonical_sha256(core)
    with pytest.raises(ValueError, match="tree digest"):
        release_toolchain.validate_inventory_payload(value)


def test_inventory_rejects_retired_pdf_evidence() -> None:
    value = _inventory_payload()
    value["pdf_font_inventories"] = [{"path": "retired.pdf"}]
    core = dict(value)
    core.pop("inventory_sha256")
    value["inventory_sha256"] = release_toolchain._canonical_sha256(core)
    with pytest.raises(ValueError, match="PDF inventory must be empty"):
        release_toolchain.validate_inventory_payload(value)


@pytest.mark.parametrize("option", ("--pdf", "--require-system-tools"))
def test_emit_parser_rejects_retired_book_build_options(option: str) -> None:
    with pytest.raises(SystemExit):
        release_toolchain._parser().parse_args(
            ["emit-inventory", "--output", "inventory.json", option]
        )


def test_inventory_rejects_retired_system_font_evidence() -> None:
    value = _inventory_payload()
    system = value["system_toolchain"]
    assert isinstance(system, dict)
    system["packages"] = [{"name": "fonts-noto-cjk"}]
    core = dict(value)
    core.pop("inventory_sha256")
    value["inventory_sha256"] = release_toolchain._canonical_sha256(core)
    with pytest.raises(ValueError, match="system inventory must be empty"):
        release_toolchain.validate_inventory_payload(value)


def test_protected_release_and_documentation_workflows_use_the_constraint() -> None:
    workflow_names = (
        "publish-pypi.yml",
        "documentation.yml",
    )
    for name in workflow_names:
        source = (ROOT / ".github/workflows" / name).read_text(encoding="utf-8")
        assert "constraints/release-python312.txt" in source
        assert '--constraint "$PIP_CONSTRAINT"' in source
        assert "scripts/release_toolchain.py verify-installed" in source
        assert "--require-ci-platform" in source
        assert "python -m pip install build packaging twine" not in source

    pypi = (ROOT / ".github/workflows/publish-pypi.yml").read_text(encoding="utf-8")
    assert "python -m build --no-isolation" in pypi
    assert "python -m twine check --strict dist/*" in pypi
    assert "scripts/smoke_installed_distribution.py" in pypi
    assert "if-no-files-found: error" in pypi

    readthedocs = (ROOT / ".readthedocs.yaml").read_text(encoding="utf-8")
    assert "    install:\n" in readthedocs
    assert "    post_install:\n" in readthedocs
    assert "post_create_environment" not in readthedocs
    assert readthedocs.index("--no-build-isolation") < readthedocs.index(
        "verify-installed"
    )


def test_mathjax_and_copied_asset_versions_are_exact_and_auditable() -> None:
    expected = f'mathjax_path = "{release_toolchain.MATHJAX_URL}"'
    for relative in release_toolchain.EXPECTED_MATHJAX_CONFIGURATION:
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert source.count(expected) == 1
        assert "mathjax@4/tex-mml-chtml.js" not in source

    constraint = release_toolchain.DEFAULT_CONSTRAINT.read_text(encoding="utf-8")
    assert "not a frozen\n# Linux wheel lock" in constraint
    script = (ROOT / "scripts/release_toolchain.py").read_text(encoding="utf-8")
    for value in ("Bootstrap v5.3.3", "Font Awesome Free 7.2.0", "OFL-1.1"):
        assert value in script
    for retired_path in ("book/conf.py", "_site/book", "DEAPack-Handbook"):
        assert retired_path not in script
