"""Regression tests for the public GitHub source and artifact boundary."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
ORDINARY_WORKFLOWS = (
    "tests.yml",
    "documentation.yml",
    "benchmarks.yml",
)
NODE24_ACTION_WORKFLOWS = (*ORDINARY_WORKFLOWS, "dco.yml")


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


def test_historical_release_and_manuscript_paths_stay_private() -> None:
    private_paths = (
        ".github/workflows/publish-github-release.yml",
        ".github/workflows/publish-testpypi.yml",
        "RELEASE_REVIEW_2.0.0rc1.md",
        "RELEASE_NOTES_2.0.0rc1.md",
        "ROADMAP.md",
        "paper/paper.md",
        "scripts/release_candidates/audit.py",
        "specs/PUBLIC_SOURCE_AND_CI_ARTIFACT_BOUNDARY_RC1.md",
        "specs/CORE_FAMILY_DELIVERY_MATRIX.md",
        "specs/RELEASE_SCOPE_2_0_RC1.md",
        "specs/dataset_candidates/README.md",
        "specs/dataset_promotions/2.0.0rc1.json",
        "tests/release_candidates/test_candidate_audit.py",
        "tests/test_release_signoff_record.py",
    )

    for path in private_paths:
        ignored = subprocess.run(
            ["git", "check-ignore", "--no-index", "--quiet", path],
            cwd=ROOT,
            check=False,
        )
        assert ignored.returncode == 0, path

        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", path],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert tracked.returncode != 0, path


def test_active_release_toolchain_keeps_its_public_regression_suite() -> None:
    script = ROOT / "scripts" / "release_toolchain.py"
    regression = ROOT / "tests" / "test_release_toolchain.py"

    assert script.is_file()
    assert regression.is_file()
    assert (
        subprocess.run(
            [
                "git",
                "check-ignore",
                "--no-index",
                "--quiet",
                regression.relative_to(ROOT),
            ],
            cwd=ROOT,
            check=False,
        ).returncode
        != 0
    )


def test_public_markdown_does_not_link_missing_or_private_local_files() -> None:
    tracked = subprocess.check_output(
        ["git", "ls-files", "*.md"], cwd=ROOT, text=True
    ).splitlines()
    current_release_notes = "RELEASE_NOTES_2.0.1.md"
    if current_release_notes not in tracked:
        tracked.append(current_release_notes)

    link_pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    for relative in tracked:
        source = ROOT / relative
        if not source.is_file():
            continue
        text = source.read_text(encoding="utf-8")
        for match in link_pattern.finditer(text):
            raw_target = match.group(1).strip()
            if raw_target.startswith("<") and raw_target.endswith(">"):
                raw_target = raw_target[1:-1]
            if raw_target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            raw_target = raw_target.split("#", maxsplit=1)[0]
            raw_target = raw_target.split("?", maxsplit=1)[0]
            if not raw_target:
                continue

            target = (source.parent / unquote(raw_target)).resolve()
            assert target.exists(), f"{relative} links missing {match.group(1)!r}"
            try:
                repository_relative = target.relative_to(ROOT)
            except ValueError:
                continue
            ignored = subprocess.run(
                [
                    "git",
                    "check-ignore",
                    "--no-index",
                    "--quiet",
                    repository_relative,
                ],
                cwd=ROOT,
                check=False,
            )
            assert ignored.returncode != 0, (
                f"{relative} links private {match.group(1)!r}"
            )


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
    assert "exclude RELEASE_NOTES_2.0.0rc1.md\n" in manifest


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


def test_active_validation_workflows_use_node24_action_generations() -> None:
    obsolete_pins = (
        "actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683",
        "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
        "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    )

    for name in NODE24_ACTION_WORKFLOWS:
        source = _workflow(name)
        assert all(pin not in source for pin in obsolete_pins), name


def test_public_contribution_and_spec_indexes_do_not_link_private_reviews() -> None:
    contribution = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    specifications = (ROOT / "specs" / "README.md").read_text(encoding="utf-8")

    for private_path in (
        "specs/dataset_candidates/",
        "specs/RELEASE_RIGHTS_REVIEW_2_0_RC1.md",
    ):
        assert private_path not in contribution
    assert "BOOK_ARCHITECTURE.md" not in specifications
