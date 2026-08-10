"""M13 evidence, registry, and package-Documentation synchronization."""

from __future__ import annotations

import json
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_ROOT = REPOSITORY_ROOT / "specs" / "registry" / "methods" / "productivity"

_RECORDS = (
    "productivity.global_malmquist.json",
    "productivity.global_malmquist_luenberger.oh_2010.json",
)
_DOCS = (
    "docs/analysis/global-malmquist.md",
    "docs/analysis/global-malmquist-luenberger.md",
)


def _text(relative: str) -> str:
    return (REPOSITORY_ROOT / relative).read_text(encoding="utf-8")


def test_both_registry_records_publish_one_fixed_vintage_pair_contract() -> None:
    for filename in _RECORDS:
        record = json.loads((REGISTRY_ROOT / filename).read_text(encoding="utf-8"))
        protocol = record["composition"]["evaluation_protocol"]

        assert protocol["defaults"]["comparison_pairs"] == "adjacent"
        assert protocol["exposed"] == ["unbalanced", "comparison_pairs"]
        assert protocol["fixed"]["comparison_pair_contract"] == {
            "adjacent": "default_consecutive_pairs_in_declared_period_order",
            "all": ("opt_in_all_forward_i_less_than_j_pairs_in_declared_period_order"),
            "custom": (
                "ordered_nonempty_sequence_of_unique_forward_base_and_comparison_"
                "period_pairs"
            ),
        }
        assert protocol["fixed"]["output_size"] == {
            "adjacent": "O(D_times_P)",
            "all": "O(D_times_P_squared)",
            "custom": "O(D_times_K_selected_pairs)",
        }
        assert "O(D_times_P)" in protocol["fixed"]["distance_solve_cache"]
        assert (
            "all_pairs_quadratic_output_with_linear_distance_solve_cache"
            in (record["implementation"]["backend_capabilities"])
        )
        assert {
            "comparison_pair_mode_and_selected_period_pairs",
            "comparison_pair_output_size_complexity",
            "unmatched_comparison_pairs",
        } <= set(record["result_contract"]["components"])
        assert {
            "default_adjacent_backward_compatibility",
            "source_faithful_all_forward_and_explicit_pair_enumeration",
            "comparison_pair_validation_and_per_pair_unbalanced_policy",
            "all_pairs_quadratic_output_with_linear_solve_cache",
        } <= set(record["validation"]["tests"]["coverage"])


def test_source_protocols_release_endpoints_without_changing_the_vintage() -> None:
    pastor = _text("specs/source_protocols/pastor_lovell_2005_global_malmquist.md")
    oh = _text("specs/source_protocols/oh_2010_global_malmquist_luenberger.md")

    for protocol in (pastor, oh):
        assert '`comparison_pairs="adjacent"`' in protocol
        assert '`comparison_pairs="all"`' in protocol
        assert "unique forward" in protocol
        assert "O(DP^2)" in protocol
        assert "O(DP)" in protocol
        assert "without an additional optimization" in protocol or (
            "without another LP" in protocol
        )
    assert "arbitrary_nonadjacent_transition_api" not in oh


def test_docs_explain_pair_matching_cost_and_unambiguous_plotting() -> None:
    for relative in _DOCS:
        document = _text(relative)
        assert '`comparison_pairs="adjacent"`' in document
        assert 'comparison_pairs="all"' in document
        assert "nonempty ordered sequence" in document
        assert '`unbalanced="drop"`' in document
        assert "O(DP^2)" in document
        assert "O(DP)" in document
        assert "fit the one pair" in document
        assert "base_period" in document
        assert "comparison_period" in document
