from pathlib import Path

import pytest

import deapack

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "specs" / "M10_MAINSTREAM_COVERAGE_AUDIT.md"


def _audit_text() -> str:
    return AUDIT.read_text(encoding="utf-8")


def test_m10_audit_covers_the_disputed_cross_cutting_topics() -> None:
    text = _audit_text()

    for required in (
        "Assurance regions, weight restrictions, and production trade-offs",
        "Nondiscretionary quantities",
        "Categorical variables and admissible peers",
        "Congestion, MPSS, and physical capacity",
        "Window and sequential reference policies",
        "Frontier bootstrap and statistical tests",
        "Partial and conditional frontiers",
        "Contextual second-stage procedures",
        "Ordinary cross-efficiency and super-efficiency",
        "Färe--Primont productivity",
        "Parallel and general network topology",
        "Large-$n$ and parallel execution",
    ):
        assert required in text

    assert "No new Handbook chapter is authorized by this M10 audit" in text
    assert text.count("### Priority ") == 2


@pytest.mark.parametrize(
    "method_id",
    (
        "static.radial.nondiscretionary.banker_morey_1986",
        "static.radial.categorical.banker_morey_1986",
        "analysis.window_efficiency",
        "productivity.fare_primont.odonnell_2012",
        "evaluation.cross.crs",
        "evaluation.super.ap_radial",
    ),
)
def test_m10_audit_does_not_overstate_deferred_public_methods(method_id: str) -> None:
    with pytest.raises(KeyError, match="unknown DEAPack canonical method ID"):
        deapack.method_info(method_id)


def test_m10_audit_matches_current_reference_and_appraisal_boundaries() -> None:
    cone_ratio = deapack.method_info(
        "valuation.weight_restriction.cone_ratio.polyhedral_crs.charnes_etal_1990"
    )
    assert cone_ratio.api_symbols == ("PolyhedralConeRatioDEA",)
    assert cone_ratio.documentation == ("api",)

    sequential = deapack.ReferenceSpec("sequential")
    window = deapack.ReferenceSpec("window", window_before=1, window_after=0)

    assert sequential.kind.value == "sequential"
    assert window.kind.value == "window"

    for method_id in (
        "evaluation.cross.game_nash.liang_wu_cook_zhu_2008",
        "evaluation.super.directional.ray_2008",
        "evaluation.super.sbm.tone_2002",
    ):
        assert deapack.method_info(method_id).publication_scope == "documentation_only"
