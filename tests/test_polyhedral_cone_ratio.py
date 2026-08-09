from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_series_equal
from test_polyhedral_cone_ratio_source_oracle import (
    _example_two,
    _independent_multiplier,
)

from deapack import (
    CCRInput,
    ConeRestrictionProvenance,
    DEAData,
    PolyhedralConeRatioDEA,
    PolyhedralConeRatioResult,
)
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.solvers import SciPyHiGHSSolver


def _provenance(
    *,
    input_units: tuple[str, ...] = ("staff-hours", "GBP-capital"),
    output_units: tuple[str, ...] = ("service-cases",),
) -> ConeRestrictionProvenance:
    return ConeRestrictionProvenance(
        elicitation_source="1990 Example 2 declared generator matrix",
        stakeholder="source study analyst",
        comparison_population="17 source organizations",
        validity_period="source study cross section",
        input_quantity_units=input_units,
        output_quantity_units=output_units,
    )


def _example_data() -> DEAData:
    inputs, outputs, _a, _b = _example_two()
    frame = pd.DataFrame(
        {
            "dmu": [f"DMU{position}" for position in range(1, 18)],
            "x1": inputs[:, 0],
            "x2": inputs[:, 1],
            "y": outputs[:, 0],
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=("x1", "x2"),
        outputs="y",
    )


class _CountingSolver:
    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self.delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        return self.delegate.solve(problem)


class _MissingDualSolver(_CountingSolver):
    name = "missing-dual"

    def solve(self, problem):  # type: ignore[no-untyped-def]
        solution = super().solve(problem)
        return replace(
            solution,
            inequality_marginals=None,
            equality_marginals=None,
            lower_bound_marginals=None,
            upper_bound_marginals=None,
        )


class _TamperedPrimalSolver(_CountingSolver):
    name = "tampered-primal"

    def solve(self, problem):  # type: ignore[no-untyped-def]
        solution = super().solve(problem)
        assert solution.primal is not None
        primal = solution.primal.copy()
        primal[-1] = -1.0
        return replace(solution, primal=primal)


class _MalformedDualSolver(_CountingSolver):
    name = "malformed-dual"

    def __init__(self, mode: str) -> None:
        super().__init__()
        self.mode = mode

    def solve(self, problem):  # type: ignore[no-untyped-def]
        solution = super().solve(problem)
        assert solution.inequality_marginals is not None
        marginals = solution.inequality_marginals.copy()
        if self.mode == "wrong_shape":
            marginals = marginals[:-1]
        elif self.mode == "nonfinite":
            marginals[0] = np.nan
        elif self.mode == "negative_coefficient":
            marginals[0] = 1.0
        else:  # pragma: no cover - test constructor controls the mode
            raise AssertionError(self.mode)
        return replace(solution, inequality_marginals=marginals)


def test_public_example_two_preserves_source_specific_accounts() -> None:
    result = PolyhedralConeRatioDEA(
        [[1.0, 0.01], [0.01, 1.0]],
        [[1.0]],
        restriction_provenance=_provenance(),
    ).fit(_example_data())

    assert isinstance(result, PolyhedralConeRatioResult)
    summary = result.summary().set_index("dmu_id")
    assert summary.loc["DMU3", "theta"] == pytest.approx(85.0 / 86.0)
    assert summary.loc["DMU10", "theta"] == pytest.approx(42.0 / 43.0)
    assert summary["score_valid"].all()
    assert summary["multiplier_valid"].all()
    assert summary["source_efficiency_valid"].eq(False).all()
    assert summary["source_efficient"].isna().all()
    assert result.peers("DMU3").set_index("peer_id").loc["DMU12", "lambda"] == (
        pytest.approx(1.0)
    )
    assert result.peers("DMU10").set_index("peer_id").loc["DMU7", "lambda"] == (
        pytest.approx(1.0)
    )
    assert not result.original_composites.empty
    assert not result.cone_residuals.empty
    assert not result.generator_coefficients.empty
    assert not result.multipliers.empty
    assert "slack" not in result.original_composites.columns
    assert "target" not in result.original_composites.columns
    assert (
        result.original_composites["difference_semantics"]
        .eq("original_coordinate_difference_not_slack")
        .all()
    )
    assert (
        result.cone_residuals["residual_semantics"]
        .eq("transformed_cone_inequality_not_componentwise_slack")
        .all()
    )
    assert result.diagnostics["cross_form_objective_gap"].max() <= 1e-7


def test_public_scores_match_independently_compiled_multiplier_form() -> None:
    inputs, outputs, input_generators, output_generators = _example_two()
    expected = _independent_multiplier(
        inputs,
        outputs,
        input_generators,
        output_generators,
    )
    result = PolyhedralConeRatioDEA(
        input_generators,
        output_generators,
        restriction_provenance=_provenance(),
    ).fit(_example_data())
    np.testing.assert_allclose(result.summary()["theta"], expected, atol=2e-10, rtol=0)


def test_identity_cones_reduce_to_score_only_ccr_input() -> None:
    rng = np.random.default_rng(20260803)
    frame = pd.DataFrame(
        {
            "dmu": [f"R{position}" for position in range(9)],
            "x1": rng.uniform(1.0, 8.0, 9),
            "x2": rng.uniform(1.0, 8.0, 9),
            "y1": rng.uniform(1.0, 8.0, 9),
            "y2": rng.uniform(1.0, 8.0, 9),
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=("x1", "x2"),
        outputs=("y1", "y2"),
    )
    cone = PolyhedralConeRatioDEA(
        np.eye(2),
        np.eye(2),
        restriction_provenance=_provenance(output_units=("case-a", "case-b")),
    ).fit(data)
    ccr = CCRInput().fit(data)
    assert_series_equal(
        cone.summary()["theta"],
        ccr.summary()["score"],
        check_names=False,
        atol=1e-9,
        rtol=0,
    )


def test_unit_covariance_requires_generator_cotransformation() -> None:
    data = _example_data()
    original = PolyhedralConeRatioDEA(
        [[1.0, 0.01], [0.01, 1.0]],
        [[1.0]],
        restriction_provenance=_provenance(),
    ).fit(data)
    frame = pd.DataFrame(
        {
            "dmu": data.dmu_ids,
            "x1": data.inputs[:, 0] * 100.0,
            "x2": data.inputs[:, 1],
            "y": data.outputs[:, 0],
        }
    )
    recoded = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=("x1", "x2"),
        outputs="y",
    )
    fixed_generators = PolyhedralConeRatioDEA(
        [[1.0, 0.01], [0.01, 1.0]],
        [[1.0]],
        restriction_provenance=_provenance(),
    ).fit(recoded)
    covariant = PolyhedralConeRatioDEA(
        [[0.01, 0.01], [0.0001, 1.0]],
        [[1.0]],
        restriction_provenance=_provenance(),
    ).fit(recoded)
    original_score = original.summary().set_index("dmu_id").loc["DMU3", "theta"]
    fixed_score = fixed_generators.summary().set_index("dmu_id").loc["DMU3", "theta"]
    covariant_score = covariant.summary().set_index("dmu_id").loc["DMU3", "theta"]
    assert original_score == pytest.approx(85.0 / 86.0)
    assert fixed_score == pytest.approx(10.0 / 17.0)
    assert covariant_score == pytest.approx(original_score)


def test_positive_generator_ray_rescaling_preserves_scores_and_multipliers() -> None:
    input_generators = np.array([[1.0, 0.01], [0.01, 1.0]])
    output_generators = np.array([[1.0]])
    input_ray_scales = np.array([1.0e10, 1.0e-10])
    output_ray_scales = np.array([1.0e10])
    baseline = PolyhedralConeRatioDEA(
        input_generators,
        output_generators,
        restriction_provenance=_provenance(),
    ).fit(_example_data())
    rescaled = PolyhedralConeRatioDEA(
        input_ray_scales[:, None] * input_generators,
        output_ray_scales[:, None] * output_generators,
        restriction_provenance=_provenance(),
    ).fit(_example_data())

    assert baseline.summary()["multiplier_valid"].all()
    assert rescaled.summary()["multiplier_valid"].all()
    np.testing.assert_allclose(
        rescaled.summary()["theta"],
        baseline.summary()["theta"],
        atol=2e-10,
        rtol=0,
    )
    baseline_multipliers = baseline.multipliers.sort_values(
        ["dmu_id", "side", "variable"]
    )["multiplier"].to_numpy()
    rescaled_multipliers = rescaled.multipliers.sort_values(
        ["dmu_id", "side", "variable"]
    )["multiplier"].to_numpy()
    np.testing.assert_allclose(
        rescaled_multipliers,
        baseline_multipliers,
        atol=2e-10,
        rtol=2e-10,
    )

    baseline_coefficients = baseline.generator_coefficients.sort_values(
        ["dmu_id", "side", "generator"]
    ).reset_index(drop=True)
    rescaled_coefficients = rescaled.generator_coefficients.sort_values(
        ["dmu_id", "side", "generator"]
    ).reset_index(drop=True)
    reciprocal_scales = np.where(
        baseline_coefficients["side"].eq("input"),
        baseline_coefficients["generator"].map(dict(enumerate(input_ray_scales))),
        baseline_coefficients["generator"].map(dict(enumerate(output_ray_scales))),
    )
    np.testing.assert_allclose(
        rescaled_coefficients["coefficient"],
        baseline_coefficients["coefficient"] / reciprocal_scales,
        atol=1e-18,
        rtol=2e-10,
    )


@pytest.mark.parametrize(
    "input_generators, output_generators, message",
    (
        ([[1.0]], [[1.0]], "shape"),
        ([[1.0, -0.1]], [[1.0]], "nonnegative"),
        ([[0.0, 0.0]], [[1.0]], "all-zero"),
        ([[1.0, np.nan]], [[1.0]], "finite"),
        ([[1.0, 0.0]], [[0.0]], "all-zero"),
    ),
)
def test_malformed_generator_matrices_fail_closed(
    input_generators: object,
    output_generators: object,
    message: str,
) -> None:
    with pytest.raises(ModelSpecificationError, match=message):
        PolyhedralConeRatioDEA(
            input_generators,
            output_generators,
            restriction_provenance=_provenance(),
        ).fit(_example_data())


def test_strict_transformed_positivity_and_provenance_alignment_are_required() -> None:
    frame = pd.DataFrame(
        {"dmu": ["A", "B"], "x1": [0.0, 1.0], "x2": [1.0, 1.0], "y": [1.0, 1.0]}
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=("x1", "x2"),
        outputs="y",
    )
    with pytest.raises(DataValidationError, match="strictly positive"):
        PolyhedralConeRatioDEA(
            [[1.0, 0.0]],
            [[1.0]],
            restriction_provenance=_provenance(),
        ).fit(data)
    with pytest.raises(ModelSpecificationError, match="unit count"):
        PolyhedralConeRatioDEA(
            np.eye(2),
            [[1.0]],
            restriction_provenance=_provenance(input_units=("one",)),
        ).fit(data)
    with pytest.raises(ValueError, match="stakeholder"):
        ConeRestrictionProvenance(
            elicitation_source="source",
            stakeholder=" ",
            comparison_population="population",
            validity_period="period",
            input_quantity_units=("unit",),
            output_quantity_units=("unit",),
        )


def test_nonfinite_transformed_accounts_fail_before_solver_compilation() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": [1.0e308, 1.0e308],
                "y": [1.0, 2.0],
            }
        ),
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    with pytest.raises(DataValidationError, match=r"transformed A x_j account.*finite"):
        PolyhedralConeRatioDEA(
            [[2.0]],
            [[1.0]],
            restriction_provenance=_provenance(
                input_units=("quantity",),
                output_units=("service",),
            ),
        ).fit(data)


def test_missing_duals_preserve_primal_accounts_but_withhold_multiplier_claims() -> (
    None
):
    solver = _MissingDualSolver()
    result = PolyhedralConeRatioDEA(
        [[1.0, 0.01], [0.01, 1.0]],
        [[1.0]],
        restriction_provenance=_provenance(),
        solver=solver,
    ).fit(_example_data())

    assert solver.calls == 17
    assert result.summary()["score_valid"].all()
    assert result.summary()["peer_valid"].all()
    assert result.summary()["composite_valid"].all()
    assert result.summary()["multiplier_valid"].eq(False).all()
    assert result.diagnostics["lp_postsolve_certified"].eq(False).all()
    assert result.diagnostics["primal_account_valid"].all()
    assert result.diagnostics["dual_account_valid"].eq(False).all()
    assert not result.intensities.empty
    assert not result.original_composites.empty
    assert result.generator_coefficients.empty
    assert result.multipliers.empty
    assert tuple(result.generator_coefficients.columns) == (
        "dmu_id",
        "period",
        "side",
        "generator",
        "coefficient",
        "selection",
    )
    assert tuple(result.multipliers.columns) == (
        "dmu_id",
        "period",
        "side",
        "variable",
        "multiplier",
        "multiplier_unit",
        "interpretation",
        "selection",
    )


@pytest.mark.parametrize("mode", ("wrong_shape", "nonfinite", "negative_coefficient"))
def test_malformed_duals_preserve_primal_accounts_and_withhold_dual_claims(
    mode: str,
) -> None:
    solver = _MalformedDualSolver(mode)
    result = PolyhedralConeRatioDEA(
        [[1.0, 0.01], [0.01, 1.0]],
        [[1.0]],
        restriction_provenance=_provenance(),
        solver=solver,
    ).fit(_example_data())

    assert solver.calls == 17
    assert result.summary()["score_valid"].all()
    assert result.summary()["peer_valid"].all()
    assert result.summary()["multiplier_valid"].eq(False).all()
    assert result.diagnostics["primal_account_valid"].all()
    assert result.diagnostics["dual_account_valid"].eq(False).all()
    assert not result.intensities.empty
    assert not result.original_composites.empty
    assert not result.cone_residuals.empty
    assert result.generator_coefficients.empty
    assert result.multipliers.empty


def test_tampered_primal_is_withheld_and_certification_adds_no_solve() -> None:
    solver = _TamperedPrimalSolver()
    result = PolyhedralConeRatioDEA(
        [[1.0, 0.01], [0.01, 1.0]],
        [[1.0]],
        restriction_provenance=_provenance(),
        solver=solver,
    ).fit(_example_data())

    assert solver.calls == 17
    assert result.summary()["score_valid"].eq(False).all()
    assert result.summary()["theta"].isna().all()
    assert result.intensities.empty
    assert result.original_composites.empty
    assert result.cone_residuals.empty
    assert tuple(result.intensities.columns) == (
        "dmu_id",
        "period",
        "peer_id",
        "lambda",
        "selection",
    )
    assert tuple(result.original_composites.columns) == (
        "dmu_id",
        "period",
        "side",
        "variable",
        "observed",
        "radial_account",
        "peer_composite",
        "difference",
        "difference_semantics",
    )
    assert tuple(result.cone_residuals.columns) == (
        "dmu_id",
        "period",
        "side",
        "generator",
        "transformed_observed",
        "transformed_bound",
        "transformed_peer_composite",
        "cone_residual",
        "residual_semantics",
    )
    assert result.metadata["primary_solver_calls"] == 17
    assert result.metadata["secondary_solver_calls"] == 0
    assert result.metadata["certificate_extra_solver_calls"] == 0


def test_metadata_freezes_generator_alignment_and_stable_provenance_fingerprint() -> (
    None
):
    model = PolyhedralConeRatioDEA(
        [[1.0, 0.01], [0.01, 1.0]],
        [[1.0]],
        restriction_provenance=_provenance(),
    )
    first = model.fit(_example_data())
    second = model.fit(_example_data())
    restriction = first.metadata["restriction"]
    assert restriction["input_variable_order"] == ["x1", "x2"]
    assert restriction["output_variable_order"] == ["y"]
    assert restriction["input_generator_order"] == [
        "input_generator_0",
        "input_generator_1",
    ]
    assert len(restriction["provenance_fingerprint"]) == 64
    assert (
        restriction["provenance_fingerprint"]
        == second.metadata["restriction"]["provenance_fingerprint"]
    )
    assert first.metadata["expanded_spec"]["context"]["purpose"] == (
        "valuation_restricted_operating_performance_self_appraisal"
    )
    with pytest.raises(TypeError):
        restriction["stakeholder"] = "changed"
