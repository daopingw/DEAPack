from __future__ import annotations

import importlib
import math
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest
from scipy.sparse import issparse

import deapack
from deapack import (
    BCC,
    CCR,
    FCH,
    FDH,
    FRH,
    DEAData,
    FreeCoordinationHullDEA,
    FreeReplicabilityHullDEA,
    ReferenceSpec,
    SolverOptions,
    SolverStatus,
    method_info,
)
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.solvers import MIPSolution, SciPyHiGHSMILPSolver


def _data(
    frame: pd.DataFrame,
    *,
    inputs: str | list[str] = "x",
    outputs: str | list[str] = "y",
    period: str | None = None,
) -> DEAData:
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=inputs,
        outputs=outputs,
        period=period,
    )


def _public_result_vocabulary(result) -> str:
    frames = {
        "summary": result.summary().to_dict(orient="list"),
        "intensities": result.intensities.to_dict(orient="list"),
        "targets": result.targets.to_dict(orient="list"),
        "slacks": result.slacks.to_dict(orient="list"),
        "diagnostics": result.diagnostics.to_dict(orient="list"),
    }
    return repr({"frames": frames, "metadata": result.metadata}).lower()


def _coordination_hulls_distinguishing_oracle(
    *,
    input_scale: float = 1.0,
    output_scale: float = 1.0,
) -> DEAData:
    return _data(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C", "E"],
                "x": np.asarray([3.0, 4.0, 12.0, 10.0]) * input_scale,
                "y": np.asarray([6.0, 5.0, 14.0, 10.0]) * output_scale,
            }
        )
    )


class _AuditingSolver:
    name = "fch_sparse_binary_auditing_fixture"

    def __init__(self) -> None:
        self.calls = 0
        self.problems = []
        self._delegate = SciPyHiGHSMILPSolver()

    def solve(self, problem):
        self.calls += 1
        self.problems.append(problem)
        assert problem.a is not None
        assert issparse(problem.a)
        binary_positions = np.flatnonzero(problem.integrality)
        assert binary_positions.size > 0
        assert np.array_equal(
            binary_positions,
            np.arange(binary_positions.size),
        )
        assert all(
            problem.bounds[position] == (0.0, 1.0) for position in binary_positions
        )
        nonempty = problem.a.getrow(problem.a.shape[0] - 1).toarray().reshape(-1)
        assert np.all(nonempty[binary_positions] == 1.0)
        assert np.all(nonempty[binary_positions.size :] == 0.0)
        assert problem.constraint_lower is not None
        assert problem.constraint_upper is not None
        assert problem.constraint_lower[-1] == pytest.approx(1.0)
        assert math.isinf(problem.constraint_upper[-1])
        return self._delegate.solve(problem)


class _FailingSolver:
    name = "fch_failure_fixture"

    def __init__(self, suffix: str) -> None:
        self._suffix = suffix
        self._delegate = SciPyHiGHSMILPSolver()

    def solve(self, problem):
        if problem.name.endswith(self._suffix):
            return MIPSolution(
                status=SolverStatus.LIMIT_REACHED,
                objective=None,
                primal=None,
                message="injected limit",
                mip_gap=0.25,
                mip_node_count=0,
                mip_dual_bound=None,
                max_primal_violation=None,
                max_integrality_violation=None,
            )
        return self._delegate.solve(problem)


class _InvalidBinarySolver:
    name = "fch_invalid_binary_fixture"

    def __init__(self, invalid_value: float) -> None:
        self._invalid_value = invalid_value
        self._delegate = SciPyHiGHSMILPSolver()

    def solve(self, problem):
        solution = self._delegate.solve(problem)
        if problem.name.endswith(":radial") and solution.primal is not None:
            primal = solution.primal.copy()
            primal[0] = self._invalid_value
            return replace(
                solution,
                primal=primal,
                max_integrality_violation=0.0,
                max_primal_violation=0.0,
                message="injected fractional binary incumbent",
            )
        return solution


class _InvalidGapSolver:
    name = "fch_invalid_gap_fixture"

    def __init__(self, gap: float | None) -> None:
        self._gap = gap
        self._delegate = SciPyHiGHSMILPSolver()

    def solve(self, problem):
        solution = self._delegate.solve(problem)
        if problem.name.endswith(":radial"):
            return replace(
                solution,
                mip_gap=self._gap,
                message="injected uncertified MIP gap",
            )
        return solution


@pytest.mark.parametrize(
    ("orientation", "expected_native", "expected_standard"),
    [
        (
            "input",
            {
                "FDH": 1.0,
                "FCH": 0.7,
                "FRH": 0.6,
                "CCR": 0.5,
                "VRS": 0.75,
            },
            {
                "FDH": 1.0,
                "FCH": 0.7,
                "FRH": 0.6,
                "CCR": 0.5,
                "VRS": 0.75,
            },
        ),
        (
            "output",
            {
                "FDH": 1.0,
                "FCH": 1.1,
                "FRH": 1.8,
                "CCR": 2.0,
                "VRS": 11.0 / 9.0,
            },
            {
                "FDH": 1.0,
                "FCH": 10.0 / 11.0,
                "FRH": 5.0 / 9.0,
                "CCR": 0.5,
                "VRS": 9.0 / 11.0,
            },
        ),
    ],
)
def test_coordination_hulls_distinguishing_oracle(
    orientation: str,
    expected_native: dict[str, float],
    expected_standard: dict[str, float],
) -> None:
    data = _coordination_hulls_distinguishing_oracle()
    models = {
        "FDH": FDH(orientation=orientation, compute_slacks=False),
        "FCH": FCH(orientation=orientation, compute_slacks=False),
        "FRH": FRH(orientation=orientation, compute_slacks=False),
        "CCR": CCR(orientation=orientation, compute_slacks=False),
        "VRS": BCC(orientation=orientation, compute_slacks=False),
    }

    for name, model in models.items():
        row = model.fit(data).summary().set_index("dmu_id").loc["E"]
        assert row["score"] == pytest.approx(expected_native[name])
        assert row["efficiency"] == pytest.approx(expected_standard[name])


def test_e_is_benchmarked_by_binary_coalition_a_plus_b() -> None:
    result = FCH(orientation="input").fit(_coordination_hulls_distinguishing_oracle())
    row = result.summary().set_index("dmu_id").loc["E"]
    peers = result.peers("E")

    assert row["coalition_size"] == 2
    assert bool(row["binary_solution_certified"])
    assert bool(row["strong_completion_certified"])
    assert peers["reference_dmu_id"].tolist() == ["A", "B"]
    assert peers["selection_indicator"].tolist() == [1, 1]
    assert peers["lambda"].tolist() == [1.0, 1.0]
    assert set(peers["intensity_kind"]) == {"binary_reference_selection"}
    assert set(peers["reference_activity_kind"]) == {"binary_subset_reference_activity"}
    assert "total_replications" not in result.summary()
    assert "replication_count" not in result.intensities
    assert result.duals.empty
    assert result.multipliers.empty


def test_phase_two_reports_binary_activity_and_free_disposal_residuals() -> None:
    result = FCH(orientation="input").fit(_coordination_hulls_distinguishing_oracle())
    targets = result.targets_for("E")
    slacks = result.slacks.query("dmu_id == 'E'").set_index("role")

    assert set(targets["target_kind"]) == {
        "radial_target",
        "binary_subset_reference_activity",
    }
    assert slacks.loc["input", "slack"] == pytest.approx(0.0)
    assert slacks.loc["output", "slack"] == pytest.approx(1.0)
    assert slacks.loc["output", "binary_subset_reference_activity"] == pytest.approx(
        11.0
    )
    assert set(slacks["residual_kind"]) == {"free_disposal_residual"}


def test_nonnegative_zero_components_preserve_hard_input_budgets() -> None:
    data = _data(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "E"],
                "x1": [1.0, 0.0, 2.0],
                "x2": [0.0, 1.0, 2.0],
                "y1": [1.0, 2.0, 2.0],
                "y2": [2.0, 1.0, 2.0],
            }
        ),
        inputs=["x1", "x2"],
        outputs=["y1", "y2"],
    )
    result = FCH(orientation="input").fit(data)
    row = result.summary().set_index("dmu_id").loc["E"]
    peers = result.peers("E")

    assert row["score"] == pytest.approx(0.5)
    assert row["coalition_size"] == 2
    assert peers["reference_dmu_id"].tolist() == ["A", "B"]
    assert peers["selection_indicator"].tolist() == [1, 1]
    assert result.metadata["zero_component_policy"]["allowed"] is True
    assert (
        result.metadata["zero_component_policy"]["evaluated_zero_input"]
        == "hard_zero_resource_budget"
    )


def test_evaluated_zero_output_retains_reference_activity_and_slack() -> None:
    data = _data(
        pd.DataFrame(
            {
                "dmu": ["A", "E"],
                "x": [1.0, 2.0],
                "y1": [2.0, 2.0],
                "y2": [3.0, 0.0],
            }
        ),
        inputs=["x"],
        outputs=["y1", "y2"],
    )
    result = FCH(orientation="output").fit(data)
    row = result.summary().set_index("dmu_id").loc["E"]
    targets = result.targets_for("E").set_index(["role", "variable", "target_kind"])
    slacks = (
        result.slacks.query("dmu_id == 'E'")
        .set_index(["role", "variable"])
        .sort_index()
    )

    assert row["score"] == pytest.approx(1.0)
    assert bool(row["is_radially_efficient"])
    assert not bool(row["is_efficient"])
    assert targets.loc[("output", "y2", "radial_target"), "target"] == pytest.approx(
        0.0
    )
    assert targets.loc[
        ("output", "y2", "binary_subset_reference_activity"), "target"
    ] == pytest.approx(3.0)
    assert slacks.loc[("output", "y2"), "slack"] == pytest.approx(3.0)
    assert slacks.loc[
        ("output", "y2"), "binary_subset_reference_activity"
    ] == pytest.approx(3.0)
    assert result.metadata["zero_component_policy"]["evaluated_zero_output"] == (
        "no_proportional_expansion_requirement_but_retained_"
        "in_reference_activity_and_slack_accounts"
    )


@pytest.mark.parametrize("orientation", ["input", "output"])
def test_fdh_fch_frh_ccr_nesting(orientation: str) -> None:
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
    data = _data(
        frame,
        inputs=["x1", "x2"],
        outputs=["y1", "y2"],
    )

    fdh = FDH(orientation=orientation, compute_slacks=False).fit(data)
    fch = FCH(orientation=orientation, compute_slacks=False).fit(data)
    frh = FRH(orientation=orientation, compute_slacks=False).fit(data)
    ccr = CCR(orientation=orientation, compute_slacks=False).fit(data)

    fdh_efficiency = fdh.summary()["efficiency"]
    fch_efficiency = fch.summary()["efficiency"]
    frh_efficiency = frh.summary()["efficiency"]
    ccr_efficiency = ccr.summary()["efficiency"]
    assert np.all(fch_efficiency <= fdh_efficiency + 1e-7)
    assert np.all(frh_efficiency <= fch_efficiency + 1e-7)
    assert np.all(ccr_efficiency <= frh_efficiency + 1e-7)


def test_fch_and_vrs_are_not_nested() -> None:
    data = _data(
        pd.DataFrame(
            {
                "dmu": list("ABCDE"),
                "x": [8.0, 2.0, 6.0, 9.0, 13.0],
                "y": [5.0, 13.0, 15.0, 18.0, 4.0],
            }
        )
    )
    fch = FCH(compute_slacks=False).fit(data).summary().set_index("dmu_id")
    vrs = BCC(compute_slacks=False).fit(data).summary().set_index("dmu_id")

    assert fch.loc["C", "efficiency"] > vrs.loc["C", "efficiency"]
    assert fch.loc["D", "efficiency"] < vrs.loc["D", "efficiency"]


@pytest.mark.parametrize("orientation", ["input", "output"])
def test_scores_and_coalitions_are_unit_invariant(orientation: str) -> None:
    baseline = FCH(orientation=orientation).fit(
        _coordination_hulls_distinguishing_oracle()
    )
    rescaled = FCH(orientation=orientation).fit(
        _coordination_hulls_distinguishing_oracle(
            input_scale=1e-11,
            output_scale=1e9,
        )
    )

    np.testing.assert_allclose(
        baseline.summary()["score"],
        rescaled.summary()["score"],
    )
    columns = ["dmu_id", "reference_dmu_id", "selection_indicator"]
    pd.testing.assert_frame_equal(
        baseline.intensities[columns].reset_index(drop=True),
        rescaled.intensities[columns].reset_index(drop=True),
    )


def test_external_reference_preserves_outside_technology_semantics() -> None:
    result = FCH(
        orientation="input",
        reference=ReferenceSpec(kind="custom", custom_rows=[2]),
    ).fit(_coordination_hulls_distinguishing_oracle())
    row = result.summary().set_index("dmu_id").loc["E"]

    assert row["score"] == pytest.approx(1.2)
    assert row["efficiency"] == pytest.approx(1.2)
    assert not bool(row["is_within_reference_technology"])
    assert pd.isna(row["is_radially_efficient"])
    assert pd.isna(row["is_efficient"])
    assert row["coalition_size"] == 1
    assert result.peers("E")["reference_dmu_id"].tolist() == ["C"]


def test_infeasible_external_output_reference_fails_closed() -> None:
    result = FCH(
        orientation="output",
        reference=ReferenceSpec(kind="custom", custom_rows=[2]),
    ).fit(_coordination_hulls_distinguishing_oracle())
    row = result.summary().set_index("dmu_id").loc["E"]

    assert row["solver_status"] == "infeasible"
    assert math.isnan(row["score"])
    assert math.isnan(row["efficiency"])
    assert not bool(row["binary_solution_certified"])
    assert pd.isna(row["coalition_size"])
    assert result.peers("E").empty


def test_nonempty_subset_makes_empty_only_output_appraisal_infeasible() -> None:
    data = _data(
        pd.DataFrame(
            {
                "dmu": ["reference", "evaluated"],
                "x": [2.0, 1.0],
                "y": [1.0, 2.0],
            }
        )
    )
    result = FCH(
        orientation="output",
        reference=ReferenceSpec(kind="custom", custom_rows=[0]),
        compute_slacks=False,
    ).fit(data)
    row = result.summary().set_index("dmu_id").loc["evaluated"]

    assert row["solver_status"] == "infeasible"
    assert math.isnan(row["score"])
    assert math.isnan(row["efficiency"])
    assert not bool(row["is_within_reference_technology"])
    assert pd.isna(row["coalition_size"])
    assert result.peers("evaluated").empty


def test_sparse_binary_milps_nonempty_constraint_budget_and_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frh_module = importlib.import_module("deapack.models.frh")
    real_compile = frh_module.compile_reference
    real_build_reference_plan = frh_module.build_reference_plan
    compile_calls = 0
    reference_plan_calls = 0

    def _counting_compile(data, rows):
        nonlocal compile_calls
        compile_calls += 1
        return real_compile(data, rows)

    def _counting_build_reference_plan(data, spec):
        nonlocal reference_plan_calls
        reference_plan_calls += 1
        return real_build_reference_plan(data, spec)

    monkeypatch.setattr(frh_module, "compile_reference", _counting_compile)
    monkeypatch.setattr(
        frh_module,
        "build_reference_plan",
        _counting_build_reference_plan,
    )
    solver = _AuditingSolver()
    data = _coordination_hulls_distinguishing_oracle()
    result = FCH(solver=solver).fit(data)

    assert solver.calls == 2 * data.n_dmus
    assert compile_calls == 1
    assert reference_plan_calls == 1
    assert result.metadata["compiled_reference_sets"] == 1
    assert result.metadata["solver_calls_per_observation"] == 2
    assert result.summary()["coalition_size"].ge(1).all()
    assert result.diagnostics["nonempty_formulation_certified"].all()
    assert result.diagnostics["nonempty_subset_certified"].all()


@pytest.mark.parametrize("invalid_value", [0.5, 2.0])
def test_invalid_binary_incumbent_fails_closed_componentwise(
    invalid_value: float,
) -> None:
    result = FCH(
        solver=_InvalidBinarySolver(invalid_value),
        compute_slacks=False,
    ).fit(_coordination_hulls_distinguishing_oracle())
    summary = result.summary()

    assert set(summary["solver_status"]) == {"numerical_error"}
    assert summary["score"].isna().all()
    assert not summary["binary_solution_certified"].any()
    assert result.intensities.empty
    assert not result.diagnostics["binary_components_certified"].any()
    assert (
        result.diagnostics["binary_components_certified_count"]
        < result.diagnostics["binary_component_count"]
    ).all()


@pytest.mark.parametrize("gap", [1e-3, None])
def test_uncertified_mip_gap_fails_closed(gap: float | None) -> None:
    result = FCH(
        solver=_InvalidGapSolver(gap),
        compute_slacks=False,
    ).fit(_coordination_hulls_distinguishing_oracle())

    assert set(result.summary()["solver_status"]) == {"numerical_error"}
    assert result.summary()["score"].isna().all()
    assert not result.diagnostics["mip_gap_certified"].any()


def test_phase_one_solver_failure_discards_incumbent_and_score() -> None:
    result = FCH(
        solver=_FailingSolver(":radial"),
    ).fit(_coordination_hulls_distinguishing_oracle())

    assert set(result.summary()["solver_status"]) == {"limit_reached"}
    assert result.summary()["score"].isna().all()
    assert not result.summary()["binary_solution_certified"].any()
    assert result.intensities.empty
    assert result.targets.empty


def test_phase_two_failure_retains_certified_radial_score_only() -> None:
    result = FCH(
        solver=_FailingSolver(":slacks"),
    ).fit(_coordination_hulls_distinguishing_oracle())
    summary = result.summary().set_index("dmu_id")

    assert summary.loc["E", "score"] == pytest.approx(0.7)
    assert summary["binary_solution_certified"].all()
    assert not summary["strong_completion_certified"].any()
    assert summary["is_efficient"].isna().all()
    assert set(summary["solver_status"]) == {"limit_reached"}
    assert result.targets.empty
    assert result.slacks.empty
    assert result.peers("E")["selection_indicator"].tolist() == [1, 1]


def test_panel_is_rejected_before_any_milp() -> None:
    solver = _AuditingSolver()
    panel = _data(
        pd.DataFrame(
            {
                "dmu": ["A", "A", "B", "B"],
                "period": [2020, 2021, 2020, 2021],
                "x": [1.0, 2.0, 2.0, 3.0],
                "y": [1.0, 2.0, 1.5, 2.5],
            }
        ),
        period="period",
    )

    with pytest.raises(
        ModelSpecificationError,
        match="rejects panel data",
    ) as panel_error:
        FCH(solver=solver).fit(panel)

    assert solver.calls == 0
    panel_message = str(panel_error.value).lower()
    assert "frh" not in panel_message
    assert "replic" not in panel_message


def test_negative_bad_output_and_zero_domain_fail_closed() -> None:
    negative = _data(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": [1.0, -1.0],
                "y": [1.0, 2.0],
            }
        )
    )
    with pytest.raises(DataValidationError, match="nonnegative input"):
        FCH().fit(negative)

    bad = DEAData.from_frame(
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
        match=r"FreeCoordinationHullDEA.*undesirable outputs",
    ) as bad_error:
        FCH().fit(bad)
    bad_message = str(bad_error.value).lower()
    assert "frh" not in bad_message
    assert "replic" not in bad_message

    zero_input = _data(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": [0.0, 2.0],
                "y": [1.0, 2.0],
            }
        )
    )
    with pytest.raises(DataValidationError, match="strictly positive input"):
        FCH().fit(zero_input)

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
        FCH().fit(zero_output)


def test_fch_scale_error_uses_only_coordination_hull_vocabulary() -> None:
    extreme = _data(
        pd.DataFrame(
            {
                "dmu": ["large", "small"],
                "x": [1e308, 1e-308],
                "y": [1.0, 1.0],
            }
        )
    )

    with pytest.raises(
        ModelSpecificationError,
        match="finite FCH input-factor bound",
    ) as scale_error:
        FCH(orientation="input", compute_slacks=False).fit(extreme)

    message = str(scale_error.value).lower()
    assert "frh" not in message
    assert "replic" not in message


def test_public_alias_catalog_and_source_qualified_metadata() -> None:
    assert FCH is FreeCoordinationHullDEA
    assert FRH is FreeReplicabilityHullDEA
    assert not issubclass(FreeCoordinationHullDEA, FRH)
    assert not issubclass(FreeReplicabilityHullDEA, FCH)
    assert FreeCoordinationHullDEA.__bases__ == (FreeReplicabilityHullDEA.__bases__[0],)
    assert not hasattr(deapack, "FAH")
    assert FCH._registry_method_id == "static.radial.fch.green_cook_2004"
    info = method_info("static.radial.fch.green_cook_2004")
    assert info.api_symbols == ("FreeCoordinationHullDEA", "FCH")
    assert info.verification == "primary_equations"

    result = FCH(compute_slacks=False).fit(_coordination_hulls_distinguishing_oracle())
    technology = result.metadata["expanded_spec"]["technology"]
    estimator = result.metadata["expanded_spec"]["estimator"]
    assert result.metadata["method_id"] == info.method_id
    assert technology["technology_id"] == ("technology.fch.binary_subset_aggregation")
    assert technology["activity_combination"] == "binary_subset_aggregation"
    assert technology["nonempty_subset"] is True
    assert technology["continuous_relaxation"]["family"] == (
        "koopmans_bounded_intensity"
    )
    assert technology["continuous_relaxation"]["nonempty_constraint_retained"] is True
    assert estimator["estimator_id"] == "estimator.full.fch"
    assert result.metadata["dual_information"] == (
        "not_available_for_mixed_integer_program"
    )
    assert result.metadata["binary_solution_certification"]["mip_gap_required"] is True
    assert "replication" not in str(result.metadata).lower()


def test_public_results_use_disjoint_fch_and_frh_vocabularies() -> None:
    data = _coordination_hulls_distinguishing_oracle()
    fch_text = _public_result_vocabulary(FCH().fit(data))
    frh_text = _public_result_vocabulary(FRH().fit(data))

    for leaked_term in ("frh", "replic"):
        assert leaked_term not in fch_text
    for leaked_term in ("fch", "coordination", "coalition", "binary", "select"):
        assert leaked_term not in frh_text


def test_fch_rejects_returns_to_scale_parameter() -> None:
    with pytest.raises(TypeError, match="returns_to_scale"):
        FCH(returns_to_scale="crs")  # type: ignore[call-arg]


def test_constructor_validation_matches_discrete_hull_contract() -> None:
    with pytest.raises(ValueError, match="pass solver or solver_options"):
        FCH(
            solver=SciPyHiGHSMILPSolver(),
            solver_options=SolverOptions(),
        )
    for tolerance in (0.0, -1.0, math.inf, math.nan):
        with pytest.raises(ValueError, match="positive and finite"):
            FCH(tolerance=tolerance)


def test_replacing_public_solver_changes_the_solver_used_by_fit() -> None:
    model = FCH(compute_slacks=False)
    replacement = _AuditingSolver()
    model.solver = replacement

    data = _coordination_hulls_distinguishing_oracle()
    model.fit(data)

    assert replacement.calls == data.n_dmus


def test_both_orientations_use_the_same_fch_technology() -> None:
    data = _coordination_hulls_distinguishing_oracle()
    input_result = FCH(
        orientation="input",
        compute_slacks=False,
    ).fit(data)
    output_result = FCH(
        orientation="output",
        compute_slacks=False,
    ).fit(data)

    assert (
        input_result.metadata["expanded_spec"]["technology"]
        == output_result.metadata["expanded_spec"]["technology"]
    )
    assert input_result.metadata["technology"] == (
        "technology.fch.binary_subset_aggregation"
    )
    assert output_result.metadata["technology"] == (
        "technology.fch.binary_subset_aggregation"
    )
