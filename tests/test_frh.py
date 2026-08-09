from __future__ import annotations

import importlib
import math
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from deapack import (
    CCR,
    FDH,
    FRH,
    DEAData,
    FreeReplicabilityHullDEA,
    ReferenceSpec,
    SolverOptions,
    SolverStatus,
    dataset_info,
    load_dataset,
)
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.solvers import (
    MIPSolution,
    SciPyHiGHSMILPSolver,
)


def _data(frame: pd.DataFrame, *, period: str | None = None) -> DEAData:
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        period=period,
        inputs=[column for column in frame if column.startswith("x")],
        outputs=[column for column in frame if column.startswith("y")],
    )


def _integer_replication_illustration(*, full: bool) -> DEAData:
    """Analytic one-input/one-output integer-replication illustration."""

    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C", "D", "E"],
            "x": [6.0, 2.0, 5.0, 3.0, 8.0],
            "y": [12.0, 3.0, 4.0, 5.0, 7.0],
        }
    )
    return _data(frame if full else frame.iloc[:3].copy())


def _benchmarking_additive_example() -> DEAData:
    """Project-created integer-coordination example."""

    frame = load_dataset("integer_coordination_hulls")
    roles = dataset_info("integer_coordination_hulls").roles
    return DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )


def _replication_portfolios(result) -> dict[str, dict[str, int]]:
    portfolios: dict[str, dict[str, int]] = {}
    for dmu_id, rows in result.intensities.groupby("dmu_id", sort=False):
        portfolios[str(dmu_id)] = {
            str(row.reference_dmu_id): int(row.replication_count)
            for row in rows.itertuples()
        }
    return portfolios


class _CountingSolver:
    name = "frh_counting_fixture"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSMILPSolver()

    def solve(self, problem):
        self.calls += 1
        return self._delegate.solve(problem)


class _FailingSolver:
    name = "frh_failure_fixture"

    def __init__(self, suffix: str) -> None:
        self._suffix = suffix
        self._delegate = SciPyHiGHSMILPSolver()

    def solve(self, problem):
        if problem.name.endswith(self._suffix):
            return MIPSolution(
                status=SolverStatus.LIMIT_REACHED,
                objective=None,
                primal=None,
                message="injected FRH solver limit",
                mip_gap=0.25,
                mip_node_count=3,
            )
        return self._delegate.solve(problem)


class _FractionalOptimalSolver:
    name = "frh_fractional_optimal_fixture"

    def __init__(self) -> None:
        self._delegate = SciPyHiGHSMILPSolver()

    def solve(self, problem):
        solution = self._delegate.solve(problem)
        if problem.name.endswith(":radial") and solution.primal is not None:
            primal = solution.primal.copy()
            primal[0] += 0.25
            return MIPSolution(
                status=SolverStatus.OPTIMAL,
                objective=solution.objective,
                primal=primal,
                message="injected noninteger incumbent",
                mip_gap=0.0,
                max_integrality_violation=0.25,
            )
        return solution


class _InvalidCertificateDiagnosticSolver:
    name = "frh_invalid_certificate_diagnostic_fixture"

    def __init__(self, field: str, value: float | None) -> None:
        self._field = field
        self._value = value
        self._delegate = SciPyHiGHSMILPSolver()

    def solve(self, problem):
        solution = self._delegate.solve(problem)
        if problem.name.endswith(":radial"):
            return replace(
                solution,
                **{
                    self._field: self._value,
                    "message": "injected invalid certificate diagnostic",
                },
            )
        return solution


def test_frh_is_an_exact_public_alias() -> None:
    assert FRH is FreeReplicabilityHullDEA
    assert FRH._registry_method_id == "static.radial.frh"


def test_three_unit_analytic_check_and_integer_portfolio() -> None:
    result = FRH(orientation="input").fit(_integer_replication_illustration(full=False))
    row = result.summary().set_index("dmu_id").loc["C"]
    peers = result.peers("C")

    assert row["score"] == pytest.approx(0.8)
    assert row["efficiency"] == pytest.approx(0.8)
    assert row["total_replications"] == 2
    assert bool(row["integer_solution_certified"])
    assert row["mip_gap"] == pytest.approx(0.0)
    assert peers["reference_dmu_id"].tolist() == ["B"]
    assert peers["replication_count"].tolist() == [2]
    assert peers["lambda"].tolist() == [2.0]
    assert set(peers["intensity_kind"]) == {"integer_replication_count"}


def test_expanded_analytic_reference_admits_unit_d() -> None:
    result = FRH(orientation="input").fit(_integer_replication_illustration(full=True))
    row = result.summary().set_index("dmu_id").loc["C"]
    peers = result.peers("C")

    assert row["score"] == pytest.approx(0.6)
    assert row["total_replications"] == 1
    assert peers["reference_dmu_id"].tolist() == ["D"]
    assert peers["replication_count"].tolist() == [1]


def test_analytic_check_orders_ccr_frh_and_fdh() -> None:
    data = _integer_replication_illustration(full=False)
    ccr = CCR(orientation="input", compute_slacks=False).fit(data)
    frh = FRH(orientation="input", compute_slacks=False).fit(data)
    fdh = FDH(orientation="input", compute_slacks=False).fit(data)

    ccr_c = ccr.summary().set_index("dmu_id").loc["C", "efficiency"]
    frh_c = frh.summary().set_index("dmu_id").loc["C", "efficiency"]
    fdh_c = fdh.summary().set_index("dmu_id").loc["C", "efficiency"]

    assert ccr_c == pytest.approx(0.4)
    assert frh_c == pytest.approx(0.8)
    assert fdh_c == pytest.approx(1.0)
    assert ccr_c < frh_c < fdh_c


def test_project_integer_coordination_input_oracle() -> None:
    result = FRH(
        orientation="input",
        compute_slacks=False,
    ).fit(_benchmarking_additive_example())

    np.testing.assert_allclose(
        result.summary()["score"],
        [1.0, 0.9, 0.6],
        rtol=1e-7,
        atol=1e-7,
    )
    assert _replication_portfolios(result) == {
        "Micro": {"Micro": 1},
        "Large": {"Micro": 3},
        "Focal": {"Micro": 4},
    }


def test_project_integer_coordination_output_oracle_and_score_convention() -> None:
    result = FRH(
        orientation="output",
        compute_slacks=False,
    ).fit(_benchmarking_additive_example())
    factors = np.asarray([1.0, 1.2, 24.0 / 13.0])

    np.testing.assert_allclose(result.summary()["score"], factors)
    np.testing.assert_allclose(result.summary()["efficiency"], 1.0 / factors)
    assert _replication_portfolios(result) == {
        "Micro": {"Micro": 1},
        "Large": {"Micro": 3},
        "Focal": {"Micro": 6},
    }
    assert result.metadata["native_score"] == "phi"
    assert result.metadata["efficiency_transform"] == ("reciprocal_positive_factor")


def test_input_completion_distinguishes_output_disposal_residual() -> None:
    result = FRH(orientation="input").fit(_integer_replication_illustration(full=False))
    c_slacks = result.slacks.query("dmu_id == 'C'").set_index("role")
    c_targets = result.targets_for("C")

    assert c_slacks.loc["input", "slack"] == pytest.approx(0.0)
    assert c_slacks.loc["output", "slack"] == pytest.approx(2.0)
    assert set(c_slacks["residual_kind"]) == {"free_disposal_residual"}
    assert set(c_targets["target_kind"]) == {
        "radial_target",
        "integer_reference_activity",
    }
    output_targets = c_targets.query("role == 'output'").set_index("target_kind")
    assert output_targets.loc["radial_target", "target"] == pytest.approx(4.0)
    assert output_targets.loc["integer_reference_activity", "target"] == pytest.approx(
        6.0
    )


def test_output_completion_distinguishes_input_disposal_residual() -> None:
    result = FRH(orientation="output").fit(
        _integer_replication_illustration(full=False)
    )
    row = result.summary().set_index("dmu_id").loc["C"]
    c_slacks = result.slacks.query("dmu_id == 'C'").set_index("role")
    input_targets = (
        result.targets_for("C").query("role == 'input'").set_index("target_kind")
    )

    assert row["score"] == pytest.approx(1.5)
    assert row["efficiency"] == pytest.approx(2.0 / 3.0)
    assert c_slacks.loc["input", "slack"] == pytest.approx(1.0)
    assert c_slacks.loc["output", "slack"] == pytest.approx(0.0)
    assert input_targets.loc["radial_target", "target"] == pytest.approx(5.0)
    assert input_targets.loc["integer_reference_activity", "target"] == pytest.approx(
        4.0
    )


def test_slack_completion_certifies_strong_efficiency_and_no_duals() -> None:
    result = FRH(orientation="input").fit(_integer_replication_illustration(full=False))
    summary = result.summary().set_index("dmu_id")

    assert bool(summary.loc["A", "is_efficient"])
    assert bool(summary.loc["B", "is_efficient"])
    assert not bool(summary.loc["C", "is_efficient"])
    assert summary["strong_completion_certified"].all()
    assert set(summary["peer_uniqueness"]) == {"not_assessed"}
    assert set(summary["portfolio_uniqueness"]) == {"not_assessed"}
    assert set(summary["peer_portfolio_uniqueness"]) == {"not_assessed"}
    assert set(summary["target_uniqueness"]) == {"not_assessed"}
    assert result.duals.empty
    assert result.metadata["dual_information"] == (
        "not_available_for_mixed_integer_program"
    )


def test_score_only_mode_does_not_claim_strong_efficiency() -> None:
    result = FRH(compute_slacks=False).fit(
        _integer_replication_illustration(full=False)
    )

    assert result.summary()["is_efficient"].isna().all()
    assert not result.summary()["strong_completion_certified"].any()
    assert result.slacks.empty
    assert result.targets.empty
    assert set(result.diagnostics["phase"]) == {1}


@pytest.mark.parametrize("orientation", ["input", "output"])
def test_scores_and_portfolios_are_invariant_to_variable_units(
    orientation: str,
) -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C", "D", "E"],
            "x1": [2.0, 3.0, 7.0, 4.0, 8.0],
            "x2": [6.0, 2.0, 5.0, 3.0, 7.0],
            "y1": [3.0, 2.0, 5.0, 4.0, 6.0],
            "y2": [2.0, 5.0, 4.0, 3.0, 8.0],
        }
    )
    scaled = frame.copy()
    scaled["x1"] *= 1e6
    scaled["x2"] *= 1e-4
    scaled["y1"] *= 1e3
    scaled["y2"] *= 1e-2

    baseline_result = FRH(orientation=orientation).fit(_data(frame))
    scaled_result = FRH(orientation=orientation).fit(_data(scaled))

    np.testing.assert_allclose(
        baseline_result.summary()["score"],
        scaled_result.summary()["score"],
    )
    portfolio_columns = [
        "dmu_id",
        "reference_dmu_id",
        "replication_count",
    ]
    pd.testing.assert_frame_equal(
        baseline_result.intensities[portfolio_columns].reset_index(drop=True),
        scaled_result.intensities[portfolio_columns].reset_index(drop=True),
    )


@pytest.mark.parametrize("orientation", ["input", "output"])
def test_fdh_frh_ccr_efficiency_nesting(orientation: str) -> None:
    rng = np.random.default_rng(20260730)
    frame = pd.DataFrame(
        np.column_stack(
            [
                rng.uniform(0.5, 5.0, size=(18, 2)),
                rng.uniform(0.5, 6.0, size=(18, 2)),
            ]
        ),
        columns=["x1", "x2", "y1", "y2"],
    )
    frame.insert(0, "dmu", [f"D{row}" for row in range(len(frame))])
    data = _data(frame)

    ccr = CCR(orientation=orientation, compute_slacks=False).fit(data)
    frh = FRH(orientation=orientation, compute_slacks=False).fit(data)
    fdh = FDH(orientation=orientation, compute_slacks=False).fit(data)

    assert np.all(ccr.summary()["efficiency"] <= frh.summary()["efficiency"] + 1e-7)
    assert np.all(frh.summary()["efficiency"] <= fdh.summary()["efficiency"] + 1e-7)


def test_panel_auto_is_contemporaneous_and_compiles_each_population_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = _data(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "A", "B"],
                "period": [2020, 2020, 2021, 2021],
                "x": [1.0, 2.0, 2.0, 3.0],
                "y": [1.0, 1.5, 2.0, 2.0],
            }
        ),
        period="period",
    )
    frh_module = importlib.import_module("deapack.models.frh")
    real_compile = frh_module.compile_reference
    compiled_rows: list[tuple[int, ...]] = []

    def _counting_compile(data, rows):
        compiled_rows.append(tuple(int(row) for row in rows))
        return real_compile(data, rows)

    monkeypatch.setattr(frh_module, "compile_reference", _counting_compile)
    result = FRH().fit(data)

    assert result.metadata["reference_kind"] == "contemporaneous"
    assert result.metadata["compiled_reference_sets"] == 2
    assert compiled_rows == [(0, 1), (2, 3)]
    assert (
        result.intensities["period"] == result.intensities["reference_period"]
    ).all()


def test_input_phase_bounds_exclude_templates_using_a_zero_budget_input() -> None:
    data = _data(
        pd.DataFrame(
            {
                "dmu": ["ineligible", "eligible", "evaluated"],
                "x1": [1.0, 2.0, 5.0],
                "x2": [1.0, 0.0, 0.0],
                "y": [100.0, 3.0, 4.0],
            }
        )
    )
    result = FRH(orientation="input").fit(data)
    row = result.summary().set_index("dmu_id").loc["evaluated"]
    peers = result.peers("evaluated")

    assert row["score"] == pytest.approx(0.8)
    assert peers["reference_dmu_id"].tolist() == ["eligible"]
    assert peers["replication_count"].tolist() == [2]
    evaluated_diagnostics = result.diagnostics.query("dmu_id == 'evaluated'")
    assert evaluated_diagnostics["finite_replication_bounds"].all()
    assert set(evaluated_diagnostics["replication_bound_kind"]) == {
        "feasible_integer_output_cover_then_radial_input_limit",
        "fixed_radial_input_limit",
    }


def test_missing_zero_budget_eligible_supplier_is_infeasible() -> None:
    data = _data(
        pd.DataFrame(
            {
                "dmu": ["reference", "evaluated"],
                "x1": [1.0, 2.0],
                "x2": [1.0, 0.0],
                "y": [2.0, 1.0],
            }
        )
    )
    result = FRH(
        reference=ReferenceSpec("custom", custom_rows=[0]),
    ).fit(data)
    row = result.summary().set_index("dmu_id").loc["evaluated"]

    assert row["solver_status"] == "infeasible"
    assert np.isnan(row["score"])
    diagnostic = result.diagnostics.query("dmu_id == 'evaluated' and phase == 1").iloc[
        0
    ]
    assert bool(diagnostic["finite_replication_bounds"])
    assert diagnostic["max_replication_upper_bound"] == pytest.approx(0.0)


def test_global_panel_reference_can_assemble_earlier_templates() -> None:
    data = _data(
        pd.DataFrame(
            {
                "dmu": ["A", "A"],
                "period": [2020, 2021],
                "x": [1.0, 3.0],
                "y": [1.0, 2.0],
            }
        ),
        period="period",
    )
    current = FRH(
        reference=ReferenceSpec("contemporaneous"),
        compute_slacks=False,
    ).fit(data)
    global_result = FRH(
        reference=ReferenceSpec("global"),
        compute_slacks=False,
    ).fit(data)

    assert current.summary().loc[1, "score"] == pytest.approx(1.0)
    assert global_result.summary().loc[1, "score"] == pytest.approx(2.0 / 3.0)
    assert global_result.peers("A", period=2021)["replication_count"].tolist() == [2]


@pytest.mark.parametrize(
    ("orientation", "frame", "expected_score"),
    [
        (
            "input",
            pd.DataFrame(
                {
                    "dmu": ["reference", "evaluated"],
                    "x": [2.0, 1.0],
                    "y": [2.0, 2.0],
                }
            ),
            2.0,
        ),
        (
            "output",
            pd.DataFrame(
                {
                    "dmu": ["reference", "evaluated"],
                    "x": [1.0, 1.0],
                    "y": [1.0, 2.0],
                }
            ),
            0.5,
        ),
    ],
)
def test_external_custom_reference_has_nullable_efficiency_claims(
    orientation: str,
    frame: pd.DataFrame,
    expected_score: float,
) -> None:
    result = FRH(
        orientation=orientation,
        reference=ReferenceSpec("custom", custom_rows=[0]),
    ).fit(_data(frame))
    row = result.summary().set_index("dmu_id").loc["evaluated"]

    assert row["score"] == pytest.approx(expected_score)
    assert row["efficiency"] == pytest.approx(2.0)
    assert not bool(row["is_within_reference_technology"])
    assert pd.isna(row["is_radially_efficient"])
    assert pd.isna(row["is_efficient"])


def test_infeasible_custom_reference_fails_closed() -> None:
    data = _data(
        pd.DataFrame(
            {
                "dmu": ["reference", "evaluated"],
                "x": [1.0, 2.0],
                "y1": [1.0, 1.0],
                "y2": [0.0, 1.0],
            }
        )
    )
    result = FRH(
        orientation="input",
        reference=ReferenceSpec("custom", custom_rows=[0]),
    ).fit(data)
    row = result.summary().set_index("dmu_id").loc["evaluated"]

    assert row["solver_status"] == "infeasible"
    assert np.isnan(row["score"])
    assert not bool(row["is_within_reference_technology"])
    assert not bool(row["integer_solution_certified"])
    assert pd.isna(row["is_efficient"])


def test_phase_one_limit_discards_uncertified_incumbent() -> None:
    result = FRH(
        solver=_FailingSolver(":radial"),
    ).fit(_integer_replication_illustration(full=False))
    summary = result.summary()

    assert set(summary["solver_status"]) == {"limit_reached"}
    assert summary["score"].isna().all()
    assert not summary["integer_solution_certified"].any()
    assert result.intensities.empty
    assert result.targets.empty
    assert set(result.diagnostics["mip_gap"]) == {0.25}


def test_phase_two_limit_preserves_radial_score_but_not_strong_claims() -> None:
    result = FRH(
        solver=_FailingSolver(":slacks"),
    ).fit(_integer_replication_illustration(full=False))
    summary = result.summary().set_index("dmu_id")

    assert summary.loc["C", "score"] == pytest.approx(0.8)
    assert set(summary["solver_status"]) == {"limit_reached"}
    assert summary["integer_solution_certified"].all()
    assert not summary["strong_completion_certified"].any()
    assert summary["is_efficient"].isna().all()
    assert result.targets.empty
    assert result.slacks.empty
    assert set(result.diagnostics["phase"]) == {1, 2}


def test_optimal_status_with_fractional_counts_fails_closed() -> None:
    result = FRH(
        solver=_FractionalOptimalSolver(),
    ).fit(_integer_replication_illustration(full=False))

    assert set(result.summary()["solver_status"]) == {"numerical_error"}
    assert result.summary()["score"].isna().all()
    assert not result.summary()["integer_solution_certified"].any()
    assert result.intensities.empty


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("max_primal_violation", 1e-3),
        ("max_integrality_violation", math.nan),
        ("mip_gap", 1e-3),
        ("mip_gap", math.nan),
    ],
)
def test_invalid_optimal_certificate_diagnostics_fail_closed(
    field: str,
    value: float,
) -> None:
    result = FRH(
        solver=_InvalidCertificateDiagnosticSolver(field, value),
        compute_slacks=False,
    ).fit(_integer_replication_illustration(full=False))

    assert set(result.summary()["solver_status"]) == {"numerical_error"}
    assert result.summary()["score"].isna().all()
    assert not result.summary()["integer_solution_certified"].any()
    assert result.intensities.empty


def test_missing_mip_gap_preserves_legacy_frh_certificate_contract() -> None:
    result = FRH(
        solver=_InvalidCertificateDiagnosticSolver("mip_gap", None),
        compute_slacks=False,
    ).fit(_integer_replication_illustration(full=False))

    assert result.summary()["integer_solution_certified"].all()
    assert set(result.summary()["solver_status"]) == {"optimal"}


def test_two_milps_are_solved_per_observation_when_completion_is_enabled() -> None:
    solver = _CountingSolver()
    result = FRH(solver=solver).fit(_integer_replication_illustration(full=False))

    assert solver.calls == 2 * 3
    assert result.metadata["compiled_reference_sets"] == 1
    assert set(result.diagnostics["phase"]) == {1, 2}


def test_frh_rejects_returns_to_scale_parameter() -> None:
    with pytest.raises(TypeError, match="returns_to_scale"):
        FRH(returns_to_scale="crs")  # type: ignore[call-arg]


def test_solver_and_solver_options_are_mutually_exclusive() -> None:
    with pytest.raises(ValueError, match="pass solver or solver_options"):
        FRH(
            solver=SciPyHiGHSMILPSolver(),
            solver_options=SolverOptions(),
        )


@pytest.mark.parametrize("tolerance", [0.0, -1.0, math.inf, math.nan])
def test_tolerance_must_be_positive_and_finite(tolerance: float) -> None:
    with pytest.raises(ValueError, match="positive and finite"):
        FRH(tolerance=tolerance)


def test_frh_rejects_unsupported_data() -> None:
    negative = _data(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": [1.0, -1.0],
                "y": [1.0, 2.0],
            }
        )
    )
    with pytest.raises(DataValidationError, match="nonnegative"):
        FRH().fit(negative)

    bad_outputs = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": [1.0, 2.0],
                "y": [1.0, 2.0],
                "bad": [2.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs="bad",
    )
    with pytest.raises(
        ModelSpecificationError,
        match="undesirable outputs",
    ) as bad_output_error:
        FRH().fit(bad_outputs)
    message = str(bad_output_error.value).lower()
    assert "fch" not in message
    assert "coordination" not in message
    assert "coalition" not in message
    assert "binary" not in message
    assert "selection" not in message

    zero_output = _data(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": [1.0, 2.0],
                "y": [0.0, 2.0],
            }
        )
    )
    with pytest.raises(DataValidationError, match="strictly positive output"):
        FRH().fit(zero_output)


def test_metadata_records_one_integer_replication_technology() -> None:
    result = FRH().fit(_integer_replication_illustration(full=False))
    technology = result.metadata["expanded_spec"]["technology"]

    assert result.metadata["method_id"] == "static.radial.frh"
    assert result.metadata["technology"] == "free_replicability_hull"
    assert technology["activity_combination"] == "integer_replication"
    assert technology["scale_extrapolation"] == "integer_additivity"
    assert result.metadata["returns_to_scale"] == "not_parameterized"
    assert (
        result.metadata["integer_solution_certification"][
            "mathematical_exactness_claimed"
        ]
        is False
    )
    assert result.metadata["integer_solution_certification"][
        "absolute_feasibility_and_integrality_threshold"
    ] == pytest.approx(1e-7)
    assert result.metadata["integer_solution_certification"][
        "relative_mip_gap_threshold"
    ] == pytest.approx(1e-7)
    assert (
        result.metadata["replication_bound_policy"]["economic_replication_cap"]
        == "none"
    )
