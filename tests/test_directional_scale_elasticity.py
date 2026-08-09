from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest
from scipy.sparse import issparse

from deapack import (
    DEAData,
    RadialDEA,
    ReferenceSpec,
    SolverStatus,
    load_dataset,
    method_info,
    relative_directional_scale_elasticity,
    scale_elasticity,
)
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.solvers import LPSolution, SciPyHiGHSSolver


class _AuditingSolver:
    name = "directional_scale_elasticity_auditing_fixture"

    def __init__(self) -> None:
        self.calls = 0
        self.problems = []
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        self.calls += 1
        self.problems.append(problem)
        if problem.a_ub is not None:
            assert issparse(problem.a_ub)
        if problem.a_eq is not None:
            assert issparse(problem.a_eq)
        return self._delegate.solve(problem)


class _FailingSolver:
    name = "directional_scale_elasticity_failure_fixture"

    def __init__(self, suffix: str) -> None:
        self._suffix = suffix
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        if problem.name.endswith(self._suffix):
            return LPSolution(
                status=SolverStatus.NUMERICAL_ERROR,
                objective=None,
                primal=None,
                message="injected failure",
                iterations=0,
            )
        return self._delegate.solve(problem)


class _UnexpectedSupportSolver:
    name = "unexpected-directional-support"

    def __init__(self) -> None:
        self.calls = 0

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        raise AssertionError(f"unexpected directional support solve: {problem.name}")


def _ren_data(
    *,
    input_scales: tuple[float, float] = (1.0, 1.0),
    output_scales: tuple[float, float, float] = (1.0, 1.0, 1.0),
) -> DEAData:
    frame = load_dataset("ren_cas_directional_scale")
    frame["staff"] *= input_scales[0]
    frame["research_expenditure"] *= input_scales[1]
    frame["external_funding"] *= output_scales[0]
    frame["high_sci_publications"] *= output_scales[1]
    frame["granted_patents"] *= output_scales[2]
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["staff", "research_expenditure"],
        outputs=[
            "external_funding",
            "high_sci_publications",
            "granted_patents",
        ],
    )


def _banker_data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "unit": ["A", "B", "C", "D", "E"],
                "input": [1.0, 1.5, 3.0, 4.0, 4.0],
                "output": [1.0, 2.0, 4.0, 5.0, 4.5],
            }
        ),
        dmu="unit",
        inputs="input",
        outputs="output",
    )


@pytest.mark.parametrize(
    ("output_direction", "expected_right", "expected_left"),
    [
        (
            (0.75, 0.75, 1.5),
            1.4126676223611883,
            1.4591568377065969,
        ),
        (
            (1.0, 1.0, 1.0),
            1.2345593240452046,
            1.2523585496355631,
        ),
        (
            (1.25, 1.25, 0.5),
            1.0948068628016792,
            1.1142558463197305,
        ),
    ],
)
def test_ren_table_4_dmu2_matches_primary_literature_oracle(
    output_direction: tuple[float, float, float],
    expected_right: float,
    expected_left: float,
) -> None:
    summary = relative_directional_scale_elasticity(
        _ren_data(),
        input_relative_direction={"research_expenditure": 1.0, "staff": 1.0},
        output_relative_direction=output_direction,
    ).summary()
    row = summary.set_index("dmu_id").loc["DMU 2"]

    assert row["scale_elasticity_right"] == pytest.approx(
        expected_right,
        abs=2e-12,
    )
    assert row["scale_elasticity_left"] == pytest.approx(
        expected_left,
        abs=2e-12,
    )
    assert row["directional_rts_right"] == "increasing"
    assert row["directional_rts_left"] == "increasing"
    assert row["scale_elasticity_status"] == "identified"


@pytest.mark.parametrize("projection_orientation", ["input", "output"])
def test_all_ones_exactly_reduces_to_existing_radial_scale_elasticity(
    projection_orientation: str,
) -> None:
    data = _banker_data()
    directional = relative_directional_scale_elasticity(
        data,
        input_relative_direction={"input": 1.0},
        output_relative_direction={"output": 1.0},
        projection_orientation=projection_orientation,
    ).summary()
    radial = scale_elasticity(
        data,
        orientation=projection_orientation,
    ).summary()

    assert np.allclose(
        directional["scale_elasticity_right"],
        radial["scale_elasticity_right"],
        rtol=2e-12,
        atol=2e-12,
    )
    finite_left = np.isfinite(radial["scale_elasticity_left"])
    assert np.allclose(
        directional.loc[finite_left, "scale_elasticity_left"],
        radial.loc[finite_left, "scale_elasticity_left"],
        rtol=2e-12,
        atol=2e-12,
    )
    assert np.array_equal(
        np.isinf(directional["scale_elasticity_left"]),
        np.isinf(radial["scale_elasticity_left"]),
    )


def test_name_mapping_is_order_independent_and_retained_as_declared() -> None:
    data = _ren_data()
    mapped = relative_directional_scale_elasticity(
        data,
        input_relative_direction={
            "research_expenditure": 0.5,
            "staff": 1.5,
        },
        output_relative_direction={
            "granted_patents": 1.5,
            "external_funding": 0.75,
            "high_sci_publications": 0.75,
        },
    )
    positional = relative_directional_scale_elasticity(
        data,
        input_relative_direction=(1.5, 0.5),
        output_relative_direction=(0.75, 0.75, 1.5),
    )

    assert np.allclose(
        mapped.summary()["scale_elasticity_right"],
        positional.summary()["scale_elasticity_right"],
    )
    assert mapped.metadata["input_relative_direction"] == {
        "staff": 1.5,
        "research_expenditure": 0.5,
    }
    assert mapped.metadata["direction_contract"]["normalization_action"] == (
        "validate_only"
    )
    assert (
        mapped.metadata["expanded_spec"]["analysis"]["direction_semantics"]
        == "declared_operating_counterfactual"
    )


@pytest.mark.parametrize(
    ("input_direction", "output_direction", "message"),
    [
        (
            {"staff": 1.0},
            {
                "external_funding": 1.0,
                "high_sci_publications": 1.0,
                "granted_patents": 1.0,
            },
            "must name every input exactly once",
        ),
        (
            {"staff": 1.0, "research_expenditure": 1.0, "ghost": 0.0},
            {
                "external_funding": 1.0,
                "high_sci_publications": 1.0,
                "granted_patents": 1.0,
            },
            "must name every input exactly once",
        ),
        (
            (1.2, 1.2),
            (1.0, 1.0, 1.0),
            "arithmetic mean one",
        ),
        (
            (1.0, 1.0),
            (0.5, 0.5, 0.5),
            "arithmetic mean one",
        ),
        (
            (-1.0, 3.0),
            (1.0, 1.0, 1.0),
            "finite and nonnegative",
        ),
    ],
)
def test_invalid_direction_contract_fails_before_any_lp(
    input_direction,
    output_direction,
    message: str,
) -> None:
    solver = _AuditingSolver()

    with pytest.raises(ModelSpecificationError, match=message):
        relative_directional_scale_elasticity(
            _ren_data(),
            input_relative_direction=input_direction,
            output_relative_direction=output_direction,
            solver=solver,
        )

    assert solver.calls == 0


def test_zero_target_component_is_inactive_without_excluding_dmu13() -> None:
    result = relative_directional_scale_elasticity(
        _ren_data(),
        input_relative_direction=(1.0, 1.0),
        output_relative_direction=(1.0, 1.0, 1.0),
    )
    row = result.summary().set_index("dmu_id").loc["DMU 13"]
    targets = result.targets_for("DMU 13").set_index("variable")

    assert row["scale_elasticity_right"] == pytest.approx(1.0203465758090182)
    assert math.isinf(row["scale_elasticity_left"])
    assert row["scale_elasticity_status"] == "identified_extended_boundary"
    assert row["inactive_output_direction_components"] == "granted_patents"
    assert targets.loc["granted_patents", "target"] == pytest.approx(0.0)
    assert targets.loc["granted_patents", "directional_rate_base"] == pytest.approx(0.0)
    assert not bool(targets.loc["granted_patents", "direction_component_active"])


def test_zero_aggregate_rate_base_fails_only_the_affected_target() -> None:
    summary = relative_directional_scale_elasticity(
        _ren_data(),
        input_relative_direction=(1.0, 1.0),
        output_relative_direction={
            "external_funding": 0.0,
            "high_sci_publications": 0.0,
            "granted_patents": 3.0,
        },
    ).summary()
    row = summary.set_index("dmu_id").loc["DMU 13"]

    assert row["solver_status"] == "component_failure"
    assert row["scale_elasticity_status"] == "inactive_directional_rate_base"
    assert math.isnan(row["scale_elasticity_right"])
    assert row["right_endpoint_solver_status"] == "not_run"
    assert row["left_endpoint_solver_status"] == "not_run"


def test_inefficient_observation_uses_completed_strong_frontier_target() -> None:
    result = relative_directional_scale_elasticity(
        _banker_data(),
        input_relative_direction=(1.0,),
        output_relative_direction=(1.0,),
    )
    row = result.summary().set_index("dmu_id").loc["E"]
    target = result.targets_for("E").set_index("variable")

    assert target.loc["input", "target"] == pytest.approx(3.5)
    assert target.loc["output", "target"] == pytest.approx(4.5)
    assert bool(row["selected_target_is_pareto_efficient"])
    assert not bool(row["projection_is_observed"])
    assert row["projection_scope"] == "selected_projection"


def test_failed_slack_completion_does_not_run_directional_support() -> None:
    result = relative_directional_scale_elasticity(
        _banker_data(),
        input_relative_direction=(1.0,),
        output_relative_direction=(1.0,),
        solver=_FailingSolver(":slacks"),
    )
    summary = result.summary()

    assert set(summary["scale_elasticity_status"]) == {"projection_failure"}
    assert set(summary["right_endpoint_solver_status"]) == {"not_run"}
    assert set(summary["left_endpoint_solver_status"]) == {"not_run"}
    assert summary["scale_elasticity_right"].isna().all()


@pytest.mark.parametrize("validity_column", ["completion_valid", "target_valid"])
def test_stale_targets_cannot_bypass_projection_validity_contract(
    monkeypatch: pytest.MonkeyPatch,
    validity_column: str,
) -> None:
    data = _banker_data()
    projection = RadialDEA(
        orientation="input",
        returns_to_scale="vrs",
        compute_slacks=True,
    ).fit(data)
    assert not projection.targets.empty
    projection.summary_frame[validity_column] = False

    def return_projection(
        self,
        fitted_data,
        *,
        compiled_references=None,
    ):
        return projection

    monkeypatch.setattr(RadialDEA, "_fit", return_projection)
    solver = _UnexpectedSupportSolver()

    result = relative_directional_scale_elasticity(
        data,
        input_relative_direction=(1.0,),
        output_relative_direction=(1.0,),
        solver=solver,
    )
    summary = result.summary()

    assert solver.calls == 0
    assert summary[f"projection_{validity_column}"].eq(False).all()
    assert summary["solver_status"].eq("component_failure").all()
    assert summary["scale_elasticity_status"].eq("projection_failure").all()
    assert summary["right_endpoint_solver_status"].eq("not_run").all()
    assert summary["left_endpoint_solver_status"].eq("not_run").all()


def test_custom_external_reference_preserves_projection_failure_semantics() -> None:
    result = relative_directional_scale_elasticity(
        _banker_data(),
        input_relative_direction=(1.0,),
        output_relative_direction=(1.0,),
        reference=ReferenceSpec(kind="custom", custom_rows=[0, 1, 2]),
    )
    summary = result.summary().set_index("dmu_id")

    assert result.metadata["reference_kind"] == "custom"
    assert summary.loc["D", "scale_elasticity_status"] == "projection_failure"
    assert summary.loc["D", "right_endpoint_solver_status"] == "not_run"
    assert summary.loc["E", "scale_elasticity_status"] == "projection_failure"
    assert summary.loc["A", "scale_elasticity_status"].startswith("identified")


def test_endpoint_solver_failure_fails_both_values_closed() -> None:
    result = relative_directional_scale_elasticity(
        _banker_data(),
        input_relative_direction=(1.0,),
        output_relative_direction=(1.0,),
        solver=_FailingSolver(":directional_scale_elasticity_left"),
    )
    summary = result.summary()

    assert set(summary["solver_status"]) == {"component_failure"}
    assert set(summary["scale_elasticity_status"]) == {"component_failure"}
    assert summary["scale_elasticity_right"].isna().all()
    assert summary["scale_elasticity_left"].isna().all()
    assert set(summary["right_endpoint_solver_status"]) == {"optimal"}
    assert set(summary["left_endpoint_solver_status"]) == {"numerical_error"}


def test_negative_data_fails_before_any_lp() -> None:
    frame = load_dataset("ren_cas_directional_scale")
    frame.loc[0, "staff"] = -1
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["staff", "research_expenditure"],
        outputs=[
            "external_funding",
            "high_sci_publications",
            "granted_patents",
        ],
    )
    solver = _AuditingSolver()

    with pytest.raises(DataValidationError, match="nonnegative input"):
        relative_directional_scale_elasticity(
            data,
            input_relative_direction=(1.0, 1.0),
            output_relative_direction=(1.0, 1.0, 1.0),
            solver=solver,
        )

    assert solver.calls == 0


def test_successful_kernel_uses_four_sparse_lps_per_observation() -> None:
    data = _ren_data()
    solver = _AuditingSolver()
    result = relative_directional_scale_elasticity(
        data,
        input_relative_direction=(1.0, 1.0),
        output_relative_direction=(1.0, 1.0, 1.0),
        solver=solver,
    )

    assert solver.calls == 4 * data.n_dmus
    assert len(solver.problems) == solver.calls
    assert result.metadata["solver_calls_per_resolved_observation"] == 4
    assert result.metadata["directional_support_calls_per_resolved_observation"] == 2


def test_relative_directional_elasticity_is_unit_invariant() -> None:
    baseline = relative_directional_scale_elasticity(
        _ren_data(),
        input_relative_direction=(1.5, 0.5),
        output_relative_direction=(0.75, 0.75, 1.5),
    ).summary()
    rescaled = relative_directional_scale_elasticity(
        _ren_data(
            input_scales=(1e6, 1e-12),
            output_scales=(1e-12, 1e3, 1e7),
        ),
        input_relative_direction=(1.5, 0.5),
        output_relative_direction=(0.75, 0.75, 1.5),
    ).summary()

    assert np.allclose(
        baseline["scale_elasticity_right"],
        rescaled["scale_elasticity_right"],
        rtol=2e-10,
        atol=2e-10,
    )
    finite_left = np.isfinite(baseline["scale_elasticity_left"])
    assert np.allclose(
        baseline.loc[finite_left, "scale_elasticity_left"],
        rescaled.loc[finite_left, "scale_elasticity_left"],
        rtol=2e-10,
        atol=2e-10,
    )
    assert np.array_equal(
        np.isinf(baseline["scale_elasticity_left"]),
        np.isinf(rescaled["scale_elasticity_left"]),
    )


def test_public_catalog_and_method_metadata_are_wired() -> None:
    info = method_info(
        "analysis.scale_elasticity.directional.relative_vrs.ren_etal_2021"
    )
    assert info.verification == "literature_oracle"
    assert "relative_directional_scale_elasticity" in info.api_symbols

    result = relative_directional_scale_elasticity(
        _banker_data(),
        input_relative_direction=(1.0,),
        output_relative_direction=(1.0,),
    )
    assert result.metadata["method_id"] == info.method_id
