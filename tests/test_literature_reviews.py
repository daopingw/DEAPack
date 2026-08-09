import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REVIEW_ROOT = REPOSITORY_ROOT / "specs" / "reviews"
REVIEW_FILES = (
    "STATIC_ECONOMIC.md",
    "ENVIRONMENTAL.md",
    "PRODUCTIVITY.md",
    "NETWORK_DYNAMIC.md",
    "NETWORK_ADDITIVE.md",
    "NETWORK_SBM.md",
    "WEIGHTS_SPECIAL_DATA_HETEROGENEITY.md",
    "STATISTICS_UNCERTAINTY.md",
    "DECISION_SUPPORT.md",
)
EVIDENCE_FIELDS = (
    "**economic question",
    "**technology / estimator",
    "**measure",
    "**rts",
    "**data / time",
    "**native score",
    "**exact aliases",
    "**distinct variants",
    "**domain",
    "**failures",
    "**solver form",
    "**defining source",
    "**evidence status",
    "**oracle",
    "**package recipe",
    "**book location",
)
ORACLE_STATUSES = (
    "not located",
    "candidate",
    "analytically derived",
    "reproduced",
    "cross-implemented",
)
CANONICAL_PREFIXES = (
    "analysis.",
    "composite.",
    "context.",
    "data.",
    "decision.",
    "diagnostics.",
    "dynamic.",
    "economic.",
    "environmental.",
    "estimator.",
    "evaluation.",
    "graph.",
    "heterogeneity.",
    "inference.",
    "network.",
    "productivity.",
    "reference.",
    "static.",
    "study_design.",
    "technology.",
    "uncertainty.",
    "valuation.",
)


def _evidence_records(content: str) -> list[str]:
    return [
        section
        for section in re.split(r"(?m)^### ", content)[1:]
        if "**economic question" in section.lower()
    ]


def test_review_programme_lists_every_stream() -> None:
    assert (REVIEW_ROOT / "INDEX.md").is_file()
    assert {path.name for path in REVIEW_ROOT.glob("*.md")} == {
        "INDEX.md",
        *REVIEW_FILES,
    }


def test_each_review_uses_the_common_evidence_contract() -> None:
    record_count = 0
    for filename in REVIEW_FILES:
        content = (REVIEW_ROOT / filename).read_text(encoding="utf-8")
        records = _evidence_records(content)
        assert records, f"{filename} contains no evidence records"
        record_count += len(records)

        for record in records:
            normalized = record.lower()
            title = record.splitlines()[0].strip()
            missing = [field for field in EVIDENCE_FIELDS if field not in normalized]
            assert not missing, f"{filename} / {title} is missing fields: {missing}"
            has_source = "https://doi.org/" in normalized
            declares_source_gap = (
                "**evidence status" in normalized
                and "registry-provisional" in normalized
                and (
                    "no single canonical formulation" in normalized
                    or "no single generic source" in normalized
                    or "no canonical executable dea formulation" in normalized
                    or "no generic procedure is selected" in normalized
                    or "defining formulation has not" in normalized
                    or "source audit" in normalized
                )
            )
            assert has_source or declares_source_gap, (
                f"{filename} / {title} has neither a DOI-linked defining source "
                "nor an explicit registry-provisional source gap"
            )

            oracle_text = normalized.split("**oracle", maxsplit=1)[1]
            assert any(status in oracle_text[:250] for status in ORACLE_STATUSES), (
                f"{filename} / {title} does not declare a controlled oracle status"
            )

    assert record_count >= 70


def test_review_index_links_every_stream() -> None:
    index = (REVIEW_ROOT / "INDEX.md").read_text(encoding="utf-8")
    for filename in REVIEW_FILES:
        assert f"]({filename})" in index


def test_review_index_inventory_matches_the_evidence_cards() -> None:
    index = (REVIEW_ROOT / "INDEX.md").read_text(encoding="utf-8")
    expected_total = 0

    for filename in REVIEW_FILES:
        content = (REVIEW_ROOT / filename).read_text(encoding="utf-8")
        record_count = len(_evidence_records(content))
        expected_total += record_count
        escaped_filename = re.escape(filename)
        row = (
            rf"\| \[`{escaped_filename}`\]\({escaped_filename}\)"
            rf" \| {record_count} \|"
        )
        assert re.search(row, index), (
            f"INDEX.md inventory is stale for {filename}: expected {record_count}"
        )

    assert f"| **Total** | **{expected_total}** |" in index


def test_readme_reports_the_current_review_and_card_inventory() -> None:
    readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
    expected_total = sum(
        len(_evidence_records((REVIEW_ROOT / filename).read_text(encoding="utf-8")))
        for filename in REVIEW_FILES
    )

    review_count_label = {9: "Nine"}.get(
        len(REVIEW_FILES),
        str(len(REVIEW_FILES)),
    )
    assert re.search(
        rf"\b{review_count_label} maintained\b",
        readme,
        flags=re.IGNORECASE,
    )
    assert f"containing {expected_total} evidence cards" in readme


def test_review_canonical_ids_resolve_to_the_method_registry() -> None:
    registry = (REPOSITORY_ROOT / "specs" / "METHODS.md").read_text(encoding="utf-8")
    registered_ids = set(re.findall(r"(?m)^\| `([^`]+)` \|", registry))

    for filename in REVIEW_FILES:
        content = (REVIEW_ROOT / filename).read_text(encoding="utf-8")
        referenced_ids = {
            value
            for value in re.findall(r"`([^`]+)`", content)
            if value.startswith(CANONICAL_PREFIXES) and "*" not in value
        }
        missing = sorted(referenced_ids.difference(registered_ids))
        assert not missing, f"{filename} references unregistered IDs: {missing}"


def test_m6_current_edition_scope_and_internal_components_are_unambiguous() -> None:
    methods = (REPOSITORY_ROOT / "specs" / "METHODS.md").read_text(encoding="utf-8")
    review = (REVIEW_ROOT / "STATISTICS_UNCERTAINTY.md").read_text(encoding="utf-8")
    roadmap = (REPOSITORY_ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    normalized_review = " ".join(review.split())
    normalized_roadmap = " ".join(roadmap.split())

    for component in ("technology.meta.pooled_convex", "reference.group"):
        row = next(
            line
            for line in methods.splitlines()
            if line.startswith(f"| `{component}` |")
        )
        assert "implemented internally" in row
        assert "not a standalone public" in row

    assert "`inference.productivity.mpi.zelenyuk_zhao_2025`" not in methods
    assert "the 2025 leaf remains unnamed" in normalized_review
    assert (
        "| `inference.subsampling` | non-executable procedure-family umbrella |"
        in methods
    )
    assert (
        "`inference.subsampling` is a non-executable namespace umbrella"
        in normalized_review
    )
    assert "no current-edition inferential API or Handbook route" in normalized_review
    assert "sole Milestone 6 Handbook route" in normalized_roadmap
    for gate in (
        "a source protocol freezing its estimator, DGP, and permitted claim",
        "an independent numerical oracle",
        "a typed result/failure contract",
    ):
        assert gate in normalized_roadmap


def test_metafrontier_public_docs_use_the_canonical_api_and_ratio_semantics() -> None:
    readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
    api = (REPOSITORY_ROOT / "docs" / "api" / "analysis.md").read_text(encoding="utf-8")
    guide = (REPOSITORY_ROOT / "docs" / "analysis" / "metafrontier.md").read_text(
        encoding="utf-8"
    )
    normalized_guide = " ".join(guide.split())

    assert "`RadialMetafrontierDEA` (concise exact alias `MetafrontierDEA`)" in readme
    assert "```{autoclass} deapack.RadialMetafrontierDEA" in api
    assert "`MetafrontierDEA` is the concise exact alias" in api
    assert "`RadialMetafrontierDEA` is the canonical API symbol" in normalized_guide
    assert "they are not a minimum economically meaningful efficiency or MTR" in (
        normalized_guide
    )
    assert "strictly positive MTR is preserved" in normalized_guide
    assert "a larger MTR means closer proximity" in normalized_guide
    for field in (
        "`score_valid`",
        "`score_status`",
        "`group_completion_valid` / `group_completion_status`",
        "`metafrontier_target_valid` / `metafrontier_target_status`",
        "`group_peer_valid` / `group_peer_status`",
        "`metafrontier_dual_valid` / `metafrontier_dual_status`",
        "`group_backend_solver_status` / `group_raw_solver_status`",
        "`primary_solver_calls`",
        "`secondary_solver_calls`",
        "`additional_solver_calls`",
        "`certificate_extra_solver_calls`",
    ):
        assert field in guide
    assert "counting diagnostic rows" in normalized_guide
    assert "are always zero" in normalized_guide
