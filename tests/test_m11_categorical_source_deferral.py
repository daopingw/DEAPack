from pathlib import Path

import pytest

import deapack

ROOT = Path(__file__).resolve().parents[1]
METHOD_ID = "static.radial.categorical.banker_morey_1986"
PROTOCOL = ROOT / "specs" / "source_protocols" / "banker_morey_1986_categorical.md"
METHODS = ROOT / "specs" / "METHODS.md"
COVERAGE = ROOT / "specs" / "METHOD_COVERAGE_AUDIT.md"
MAINSTREAM = ROOT / "specs" / "M10_MAINSTREAM_COVERAGE_AUDIT.md"
REVIEW = ROOT / "specs" / "reviews" / "WEIGHTS_SPECIAL_DATA_HETEROGENEITY.md"
PROTOCOL_INDEX = ROOT / "specs" / "source_protocols" / "README.md"
REGISTRY = ROOT / "specs" / "registry" / "methods"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _markdown_section(text: str, heading: str, next_heading: str) -> str:
    return text.split(heading, maxsplit=1)[1].split(next_heading, maxsplit=1)[0]


def test_categorical_protocol_freezes_the_deferred_readiness_state() -> None:
    text = _read(PROTOCOL)
    prose = " ".join(text.split())

    required_rows = (
        (
            "| Candidate identifier | `static.radial.categorical."
            "banker_morey_1986` (provisional umbrella; final leaf split unresolved) |"
        ),
        (
            "| Source status | "
            "`primary_metadata_and_abstract_located_full_text_not_obtained` |"
        ),
        "| Implementation status | `deferred_source_audit` |",
        "| Equation-freeze status | `not_frozen` |",
        (
            "| Dataset status | "
            "`or_library_dea3_located_raw_69x6_unlabelled_requires_source_tables` |"
        ),
        "| Numerical-oracle status | `not_located` |",
        "| Release disposition | `deferred_to_next_version` |",
        "| Public API | none |",
        "| Registry status | do not register |",
    )

    for row in required_rows:
        assert row in text

    assert "69 rows and six unlabelled numeric fields" in prose
    assert "not a numerical oracle" in prose
    assert "No threshold, ordering, or categorical role may be guessed" in prose


def test_categorical_candidate_is_not_exposed_as_a_public_method_or_api() -> None:
    assert METHOD_ID not in {method.method_id for method in deapack.list_methods()}

    with pytest.raises(KeyError, match="unknown DEAPack canonical method ID"):
        deapack.method_info(METHOD_ID)

    leaked_symbols = {
        name
        for name in dir(deapack)
        if "banker" in name.casefold()
        and "morey" in name.casefold()
        and "categor" in name.casefold()
    }
    assert not leaked_symbols

    registered_files = [
        path
        for path in REGISTRY.rglob("*.json")
        if METHOD_ID in path.read_text(encoding="utf-8")
    ]
    assert not registered_files


def test_categorical_specs_are_synchronized_without_stale_overclaims() -> None:
    protocol = _read(PROTOCOL)
    methods = _read(METHODS)
    coverage = _read(COVERAGE)
    mainstream = _read(MAINSTREAM)
    review = _read(REVIEW)
    protocol_index = _read(PROTOCOL_INDEX)

    assert "banker_morey_1986_categorical.md" in protocol_index
    assert (
        f"| `{METHOD_ID}` | provisional umbrella for the source's categorical "
        "formulations; final controllable/uncontrollable leaf split remains "
        "unresolved | deferred candidate;"
    ) in methods
    assert "Both provisional Banker--Morey static leaves" in coverage
    assert "source_protocols/banker_morey_1986_categorical.md" in coverage
    assert "The 69-by-6 unlabelled file is not an oracle." in mainstream

    categorical_review = _markdown_section(
        review,
        f"### `{METHOD_ID}`",
        "### Ordinal, ratio, integer, flexible-role, negative, and missing data",
    )
    assert "`deferred_to_next_version`" in categorical_review
    assert "primary-checked" not in categorical_review.casefold()

    categorical_evidence = "\n".join(
        (protocol, methods, coverage, mainstream, categorical_review)
    ).casefold()
    stale_overclaims = (
        "defining categorical article is primary-checked",
        "the defining article has been primary-checked",
        "the defining source's example has been identified",
        "its numerical example is identified",
        "making a page-frozen source protocol and independent reproduction a bounded",
        "two evidence-bounded scientific gaps above",
        "two**, not three, immediate package priorities",
    )
    for overclaim in stale_overclaims:
        assert overclaim not in categorical_evidence
