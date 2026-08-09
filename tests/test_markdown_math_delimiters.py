from __future__ import annotations

import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
LEGACY_MATH_DELIMITER = re.compile(r"\\(?:\(|\)|\[|\])")
RST_MATH_DIRECTIVE = re.compile(r"^\s*\.\. math::\s*$")

# A literal example may be exempted only by naming its exact source line and
# recording why readers need to see the legacy spelling. Stale exemptions fail.
LEGACY_MATH_EXCLUSIONS: dict[tuple[str, int], str] = {}


def test_user_facing_markdown_uses_myst_dollar_math() -> None:
    unexplained: list[str] = []
    used_exclusions: set[tuple[str, int]] = set()

    for source_root in ("book", "docs", "specs"):
        for path in sorted((REPOSITORY_ROOT / source_root).rglob("*.md")):
            relative_path = path.relative_to(REPOSITORY_ROOT).as_posix()
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(),
                start=1,
            ):
                delimiters = sorted(set(LEGACY_MATH_DELIMITER.findall(line)))
                if not delimiters:
                    continue

                location = (relative_path, line_number)
                reason = LEGACY_MATH_EXCLUSIONS.get(location)
                if reason and reason.strip():
                    used_exclusions.add(location)
                    continue

                rendered = ", ".join(repr(delimiter) for delimiter in delimiters)
                unexplained.append(f"{relative_path}:{line_number}: {rendered}")

    empty_reasons = sorted(
        location
        for location, reason in LEGACY_MATH_EXCLUSIONS.items()
        if not reason.strip()
    )
    stale_exclusions = sorted(set(LEGACY_MATH_EXCLUSIONS) - used_exclusions)

    assert not empty_reasons, (
        "Legacy-math exclusions require a non-empty reader-facing justification: "
        f"{empty_reasons}"
    )
    assert not stale_exclusions, (
        "Remove stale legacy-math exclusions whose source line no longer matches: "
        f"{stale_exclusions}"
    )
    assert not unexplained, (
        "Use MyST dollarmath (`$...$` or `$$...$$`) in user-facing Markdown. "
        "Legacy LaTeX delimiters are emitted as raw text by the current Sphinx "
        "configuration. If a literal example is essential, add its exact line to "
        "`LEGACY_MATH_EXCLUSIONS` with a justification.\n" + "\n".join(unexplained)
    )


def test_autodoc_sources_do_not_embed_rest_math_directives() -> None:
    occurrences: list[str] = []
    for path in sorted((REPOSITORY_ROOT / "src" / "deapack").rglob("*.py")):
        relative_path = path.relative_to(REPOSITORY_ROOT).as_posix()
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            if RST_MATH_DIRECTIVE.match(line):
                occurrences.append(f"{relative_path}:{line_number}")

    assert not occurrences, (
        "Autoclass content is parsed by MyST in the current documentation build; "
        "reStructuredText `.. math::` directives are emitted as raw text. Use "
        "MyST `$$...$$` display math in public docstrings instead.\n"
        + "\n".join(occurrences)
    )
