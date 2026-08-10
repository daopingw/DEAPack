"""Regression tests for the public GitHub source and artifact boundary."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORDINARY_WORKFLOWS = (
    "tests.yml",
    "documentation.yml",
    "benchmarks.yml",
)


def _workflow(name: str) -> str:
    return (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")


def test_private_source_paths_are_ignored() -> None:
    private_paths = (
        "book/probe.md",
        "book/chapters/probe.md",
        "docs/locale/probe.po",
        "specs/archive/probe.md",
    )

    for path in private_paths:
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "--quiet", path],
            cwd=ROOT,
            check=False,
        )
        assert result.returncode == 0, path

    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "/book/\n" in ignore


def test_generated_and_private_release_outputs_are_ignored() -> None:
    generated_or_private_paths = (
        "book/_build/html/index.html",
        "docs/_build/html/index.html",
        "_site/index.html",
        "output/review/2.0.0rc1/dist/probe.whl",
        "benchmark-results/release-probe/report.json",
        "tmp/release-private/approval.key",
        "specs/reviews/source_oracle_notes.tmp",
    )

    for path in generated_or_private_paths:
        result = subprocess.run(
            ["git", "check-ignore", "--quiet", path],
            cwd=ROOT,
            check=False,
        )
        assert result.returncode == 0, path


def test_sdist_defensively_prunes_legacy_and_private_release_roots() -> None:
    manifest = (ROOT / "MANIFEST.in").read_text(encoding="utf-8")
    pruned_roots = (
        "DEAPack",
        "docs",
        "specs",
        "tmp",
        "output",
        "build",
        "dist",
        "_build",
        "_site",
        "benchmark-results",
    )

    for root in pruned_roots:
        assert f"prune {root}\n" in manifest


def test_every_ordinary_ci_upload_is_literal_false_guarded() -> None:
    for name in ORDINARY_WORKFLOWS:
        source = _workflow(name)
        upload_count = source.count("uses: actions/upload-artifact@")
        literal_false_count = source.count("if: ${{ false }}")
        literal_false_count += source.count("if: ${{ always() && false }}")

        assert upload_count > 0, name
        assert literal_false_count == upload_count, name


def test_ordinary_ci_keeps_build_and_test_feedback_enabled() -> None:
    tests = _workflow("tests.yml")
    documentation = _workflow("documentation.yml")
    benchmarks = _workflow("benchmarks.yml")

    assert "run: python -m pytest" in tests
    assert "python -m build" in tests
    assert "sphinx-build -E -a -W --keep-going" in documentation
    assert "python scripts/run_documentation_examples.py" in documentation
    assert "book" not in documentation.casefold()
    assert "python scripts/run_benchmarks.py" in benchmarks

    for source in (tests, documentation):
        assert "  pull_request:\n" in source
        assert "    branches: [main]\n" in source
