from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from deapack.data import DEAData
from deapack.enums import SolverStatus
from deapack.evaluation.super_efficiency import (
    AndersenPetersenSuperEfficiency,
    APSuperEfficiency,
)
from deapack.exceptions import ModelSpecificationError
from deapack.models.radial import RadialDEA
from deapack.solvers import LPSolution
from deapack.specs import ReferenceSpec, SolverOptions


class _AlwaysLimitSolver:
    name = "always-limit"

    def solve(self, problem):  # type: ignore[no-untyped-def]
        del problem
        return LPSolution(
            status=SolverStatus.LIMIT_REACHED,
            objective=None,
            primal=None,
            message="injected limit",
            iterations=3,
        )


class _MalformedOptimalSolver:
    name = "malformed-optimal"

    def solve(self, problem):  # type: ignore[no-untyped-def]
        return LPSolution(
            status=SolverStatus.OPTIMAL,
            objective=0.0,
            primal=np.zeros(problem.c.size - 1),
            message="wrong-length incumbent",
            iterations=0,
        )


def _two_dmu_data(
    *,
    input_scale: float = 1.0,
    output_scale: float = 1.0,
) -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": np.asarray([1.0, 2.0]) * input_scale,
                "y": np.asarray([1.0, 1.0]) * output_scale,
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )


def test_derived_crs_ratio_check_and_ordinary_efficiency_relationship() -> None:
    """Keep a derived exact check without claiming a source reproduction."""

    assert APSuperEfficiency is AndersenPetersenSuperEfficiency
    data = _two_dmu_data()
    super_result = APSuperEfficiency(
        orientation="input",
        returns_to_scale="crs",
    ).fit(data)
    ordinary = RadialDEA(
        orientation="input",
        returns_to_scale="crs",
        compute_slacks=False,
    ).fit(data)

    super_summary = super_result.summary().set_index("dmu_id")
    ordinary_summary = ordinary.summary().set_index("dmu_id")
    assert super_summary.loc["A", "score"] == pytest.approx(2.0)
    assert super_summary.loc["B", "score"] == pytest.approx(0.5)
    assert ordinary_summary.loc["A", "efficiency"] == pytest.approx(1.0)
    assert ordinary_summary.loc["B", "efficiency"] == pytest.approx(0.5)
    assert bool(super_summary.loc["A", "is_super_efficient"])
    assert not bool(super_summary.loc["B", "is_radially_efficient"])
    assert super_summary["is_efficient"].isna().all()
    assert super_summary["reference_size_before_exclusion"].tolist() == [2, 2]
    assert super_summary["reference_size"].tolist() == [1, 1]
    assert super_summary["self_excluded"].tolist() == [True, True]

    assert super_result.metadata["method_id"] == "evaluation.super.ap_radial"
    assert super_result.metadata["production_technology_changed"] is False
    assert super_result.metadata["base_reference_sets"] == 1
    assert super_result.metadata["effective_reference_compilations"] == 2
    assert super_result.metadata["effective_reference_reuses"] == 0
    assert super_result.metadata["score_direction"] == "higher_is_better"
    assert super_result.metadata["implementation_status"] == "prototype_internal_only"
    assert super_result.metadata["release_disposition"] == "deferred_to_next_version"
    candidate_source = super_result.metadata["candidate_source"]
    assert candidate_source["doi"] == ("https://doi.org/10.1287/mnsc.39.10.1261")
    assert candidate_source["evidence_status"] == ("defining_full_text_not_obtained")
    protocol = super_result.metadata["expanded_spec"]["evaluation_protocol"]
    assert protocol["kind"] == "radial_leave_one_out_prototype"
    assert protocol["source_evidence"] == "defining_full_text_not_obtained"
    assert protocol["release_disposition"] == "deferred_to_next_version"
    assert protocol["infeasibility_policy"] == (
        "deapack_prototype_report_solver_status_without_repair"
    )


def test_indirectly_reprinted_five_unit_candidate_table() -> None:
    """Reproduce a later reprint without calling it a 1993 source oracle."""

    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": list("ABCDE"),
                "x1": [2.0, 2.0, 5.0, 10.0, 10.0],
                "x2": [12.0, 8.0, 5.0, 4.0, 6.0],
                "y": [1.0] * 5,
            }
        ),
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs="y",
    )
    result = APSuperEfficiency(
        orientation="input",
        returns_to_scale="crs",
    ).fit(data)
    summary = result.summary().set_index("dmu_id")

    np.testing.assert_allclose(
        summary.loc[list("ABCDE"), "score"],
        [1.0, 25.0 / 19.0, 6.0 / 5.0, 5.0 / 4.0, 3.0 / 4.0],
        atol=1e-10,
        rtol=0.0,
    )
    peer_frame = result.intensities[["dmu_id", "reference_dmu_id", "lambda"]]
    actual_peers = {
        (dmu_id, reference_dmu_id): float(intensity)
        for dmu_id, reference_dmu_id, intensity in peer_frame.itertuples(
            index=False,
            name=None,
        )
    }
    assert actual_peers == pytest.approx(
        {
            ("A", "B"): 1.0,
            ("B", "A"): 15.0 / 19.0,
            ("B", "C"): 4.0 / 19.0,
            ("C", "B"): 1.0 / 2.0,
            ("C", "D"): 1.0 / 2.0,
            ("D", "C"): 1.0,
            ("E", "C"): 1.0 / 2.0,
            ("E", "D"): 1.0 / 2.0,
        }
    )


def test_xue_harker_2002_vrs_candidate_table_and_infeasibility() -> None:
    """Freeze a later primary VRS table without extending the 1993 identity."""

    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": list("ABCDEF"),
                "x": [2.0, 3.0, 5.0, 7.0, 7.0, 3.0],
                "y": [2.0, 5.0, 9.0, 11.0, 9.0, 2.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    result = APSuperEfficiency(
        orientation="input",
        returns_to_scale="vrs",
    ).fit(data)
    summary = result.summary().set_index("dmu_id")

    np.testing.assert_allclose(
        summary.loc[["A", "B", "C", "E", "F"], "score"],
        [3.0 / 2.0, 23.0 / 21.0, 17.0 / 15.0, 5.0 / 7.0, 2.0 / 3.0],
        atol=1e-10,
        rtol=0.0,
    )
    assert np.isnan(summary.loc["D", "score"])
    assert summary.loc["D", "solver_status"] == SolverStatus.INFEASIBLE.value
    assert summary.loc["D", "failure_reason"] == "solver_status_infeasible"


def test_output_orientation_reports_reciprocal_phi_and_peer_activity() -> None:
    result = APSuperEfficiency(
        orientation="output",
        returns_to_scale="crs",
    ).fit(_two_dmu_data())
    summary = result.summary().set_index("dmu_id")

    assert summary.loc["A", "radial_factor"] == pytest.approx(0.5)
    assert summary.loc["A", "score"] == pytest.approx(2.0)
    assert summary.loc["B", "radial_factor"] == pytest.approx(2.0)
    assert summary.loc["B", "score"] == pytest.approx(0.5)
    assert result.metadata["native_factor"] == "phi"
    assert result.metadata["reported_score"] == "reciprocal_phi"

    a_peers = result.peers("A")
    assert a_peers["reference_dmu_id"].tolist() == ["B"]
    assert a_peers["lambda"].iloc[0] == pytest.approx(0.5)
    a_targets = result.targets_for("A").set_index(["role", "variable"])
    assert a_targets.loc[("input", "x"), "target"] == pytest.approx(1.0)
    assert a_targets.loc[("output", "y"), "target"] == pytest.approx(0.5)
    assert a_targets.loc[("output", "y"), "radial_bound"] == pytest.approx(0.5)


@pytest.mark.parametrize(
    ("orientation", "returns_to_scale", "expected_a", "expected_b"),
    [
        ("input", "crs", 2.0, 0.5),
        ("input", "vrs", 2.0, 0.5),
        ("input", "nirs", 2.0, 0.5),
        ("input", "ndrs", 2.0, 0.5),
        ("output", "crs", 2.0, 0.5),
        ("output", "nirs", 2.0, 1.0),
        ("output", "vrs", None, 1.0),
        ("output", "ndrs", None, 0.5),
    ],
)
def test_orientation_and_returns_to_scale_contract(
    orientation: str,
    returns_to_scale: str,
    expected_a: float | None,
    expected_b: float,
) -> None:
    result = APSuperEfficiency(
        orientation=orientation,
        returns_to_scale=returns_to_scale,
    ).fit(_two_dmu_data())
    summary = result.summary().set_index("dmu_id")

    if expected_a is None:
        assert np.isnan(summary.loc["A", "score"])
        assert summary.loc["A", "solver_status"] == SolverStatus.INFEASIBLE.value
    else:
        assert summary.loc["A", "score"] == pytest.approx(expected_a)
        assert summary.loc["A", "solver_status"] == SolverStatus.OPTIMAL.value
    assert summary.loc["B", "score"] == pytest.approx(expected_b)


def test_vrs_infeasibility_is_reported_without_automatic_repair() -> None:
    result = APSuperEfficiency(
        orientation="output",
        returns_to_scale="vrs",
    ).fit(_two_dmu_data())
    summary = result.summary().set_index("dmu_id")
    a_diagnostic = result.diagnostics.set_index("dmu_id").loc["A"]

    assert summary.loc["A", "solver_status"] == SolverStatus.INFEASIBLE.value
    assert summary.loc["A", "failure_reason"] == "solver_status_infeasible"
    assert np.isnan(summary.loc["A", "score"])
    assert pd.isna(summary.loc["A", "is_efficient"])
    assert a_diagnostic["solver_status"] == SolverStatus.INFEASIBLE.value
    assert not bool(a_diagnostic["postsolve_certified"])
    assert result.targets.query("dmu_id == 'A'").empty
    assert result.intensities.query("dmu_id == 'A'").empty
    assert result.metadata["infeasibility_policy"] == (
        "deapack_prototype_report_solver_status_without_repair"
    )


@pytest.mark.parametrize("orientation", ["input", "output"])
def test_scores_and_targets_are_unit_invariant(orientation: str) -> None:
    baseline = APSuperEfficiency(orientation=orientation).fit(_two_dmu_data())
    rescaled = APSuperEfficiency(orientation=orientation).fit(
        _two_dmu_data(input_scale=1.0e9, output_scale=1.0e-8)
    )

    np.testing.assert_allclose(
        baseline.summary()["score"],
        rescaled.summary()["score"],
        atol=1e-10,
        rtol=0.0,
    )
    baseline_targets = baseline.targets.sort_values(
        ["dmu_id", "role", "variable"]
    ).reset_index(drop=True)
    scaled_targets = rescaled.targets.sort_values(
        ["dmu_id", "role", "variable"]
    ).reset_index(drop=True)
    input_mask = baseline_targets["role"] == "input"
    output_mask = baseline_targets["role"] == "output"
    np.testing.assert_allclose(
        scaled_targets.loc[input_mask, "target"],
        baseline_targets.loc[input_mask, "target"] * 1.0e9,
    )
    np.testing.assert_allclose(
        scaled_targets.loc[output_mask, "target"],
        baseline_targets.loc[output_mask, "target"] * 1.0e-8,
    )


def test_custom_reference_excludes_self_only_when_present() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C", "D"],
                "x": [1.0, 2.0, 3.0, 4.0],
                "y": [1.0, 1.0, 1.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    result = APSuperEfficiency(
        reference=ReferenceSpec(kind="custom", custom_rows=(0, 1))
    ).fit(data)
    summary = result.summary().set_index("dmu_id")

    assert summary.loc["A", "reference_size"] == 1
    assert bool(summary.loc["A", "self_excluded"])
    assert summary.loc["B", "reference_size"] == 1
    assert bool(summary.loc["B", "self_excluded"])
    assert summary.loc["C", "reference_size_before_exclusion"] == 2
    assert summary.loc["C", "reference_size"] == 2
    assert not bool(summary.loc["C", "self_excluded"])
    assert "C" not in result.peers("C")["reference_dmu_id"].tolist()
    assert summary.loc["D", "reference_size"] == 2
    assert not bool(summary.loc["D", "self_excluded"])
    assert result.metadata["effective_reference_compilations"] == 3
    assert result.metadata["effective_reference_reuses"] == 1


def test_thresholded_peer_disclosure_does_not_change_targets() -> None:
    result = APSuperEfficiency(
        orientation="output",
        peer_tolerance=0.75,
    ).fit(_two_dmu_data())
    summary = result.summary().set_index("dmu_id")

    assert result.peers("A").empty
    assert summary.loc["A", "reported_peer_count"] == 0
    assert summary.loc["A", "omitted_intensity_sum"] == pytest.approx(0.5)
    a_target = result.targets_for("A").query("role == 'output' and variable == 'y'")
    assert a_target["target"].iloc[0] == pytest.approx(0.5)
    assert result.metadata["targets_use_unthresholded_intensities"] is True


def test_nonpositive_output_factor_fails_closed() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x1": [0.0, 1.0],
                "x2": [1.0, 0.0],
                "y": [1.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs="y",
    )
    result = APSuperEfficiency(orientation="output").fit(data)

    assert result.summary()["radial_factor"].tolist() == [0.0, 0.0]
    assert result.summary()["score"].isna().all()
    assert result.summary()["solver_status"].tolist() == [
        SolverStatus.FAILED.value,
        SolverStatus.FAILED.value,
    ]
    assert result.summary()["failure_reason"].tolist() == [
        "nonpositive_radial_factor",
        "nonpositive_radial_factor",
    ]
    assert result.diagnostics["solver_status"].tolist() == [
        SolverStatus.OPTIMAL.value,
        SolverStatus.OPTIMAL.value,
    ]
    assert result.diagnostics["postsolve_certified"].all()
    assert not result.diagnostics["factor_valid"].any()
    assert result.targets.empty
    assert result.intensities.empty


def test_solver_status_and_malformed_optimum_fail_closed() -> None:
    limited = APSuperEfficiency(solver=_AlwaysLimitSolver()).fit(_two_dmu_data())
    malformed = APSuperEfficiency(solver=_MalformedOptimalSolver()).fit(_two_dmu_data())

    assert limited.summary()["solver_status"].tolist() == [
        SolverStatus.LIMIT_REACHED.value,
        SolverStatus.LIMIT_REACHED.value,
    ]
    assert limited.summary()["score"].isna().all()
    assert limited.diagnostics["iterations"].tolist() == [3, 3]
    assert malformed.summary()["solver_status"].tolist() == [
        SolverStatus.FAILED.value,
        SolverStatus.FAILED.value,
    ]
    assert malformed.summary()["failure_reason"].tolist() == [
        "wrong_primal_length",
        "wrong_primal_length",
    ]
    assert malformed.summary()["score"].isna().all()


def test_bad_outputs_one_dmu_and_empty_leave_one_out_reference_are_rejected() -> None:
    bad_output_data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": [1.0, 2.0],
                "y": [1.0, 1.0],
                "b": [2.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs="b",
    )
    with pytest.raises(
        ModelSpecificationError,
        match="does not infer undesirable-output disposal",
    ):
        APSuperEfficiency().fit(bad_output_data)

    one_dmu = DEAData.from_frame(
        pd.DataFrame({"dmu": ["A"], "x": [1.0], "y": [1.0]}),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    with pytest.raises(ModelSpecificationError, match="at least two observations"):
        APSuperEfficiency().fit(one_dmu)

    with pytest.raises(
        ModelSpecificationError,
        match="leaves no eligible peer",
    ):
        APSuperEfficiency(reference=ReferenceSpec(kind="custom", custom_rows=(0,))).fit(
            _two_dmu_data()
        )


def test_invalid_configuration_is_rejected() -> None:
    with pytest.raises(ValueError, match="pass solver or solver_options"):
        APSuperEfficiency(
            solver=_AlwaysLimitSolver(),
            solver_options=SolverOptions(),
        )
    with pytest.raises(ValueError, match="tolerance must be positive"):
        APSuperEfficiency(tolerance=0.0)
    with pytest.raises(ValueError, match="peer_tolerance must be positive"):
        APSuperEfficiency(peer_tolerance=np.inf)
    with pytest.raises(ValueError, match="orientation must be one of"):
        APSuperEfficiency(orientation="sideways")
