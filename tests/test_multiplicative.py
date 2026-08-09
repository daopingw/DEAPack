"""Production boundary tests for multiplicative DEA."""

from __future__ import annotations

import math
import warnings

import numpy as np
import pandas as pd
import pytest

from deapack import DEAData, MultiplicativeDEA, MultiplicativeVariant
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.models.multiplicative import _CompiledMultiplicativeReference
from deapack.solvers import LinearProgram, LPSolution, SciPyHiGHSSolver
from deapack.specs import ReferenceSpec
from deapack.visualization import prepare_performance_data


def _fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "x": [2.0, 4.0],
            "y": [4.0, 4.0],
        }
    )


def _data(frame: pd.DataFrame, *, period: str | None = None) -> DEAData:
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs="x",
        outputs="y",
        period=period,
    )


@pytest.mark.parametrize(
    ("delta", "underflows"),
    [(1.0e-12, False), (1.0e12, True)],
    ids=["tiny-delta", "large-delta"],
)
def test_extreme_finite_exponent_floors_preserve_the_normalized_peer_plan(
    delta: float,
    underflows: bool,
) -> None:
    result = MultiplicativeDEA(exponent_floor=delta).fit(_data(_fixture()))
    summary = result.summary().set_index("dmu_id").loc["B"]
    expected_log_inefficiency = delta * math.log(2.0)

    assert summary["solver_status"] == "optimal"
    assert float(summary["distance"]) == pytest.approx(
        expected_log_inefficiency,
        rel=1.0e-12,
        abs=1.0e-24,
    )
    assert float(summary["log_efficiency"]) == pytest.approx(
        -expected_log_inefficiency,
        rel=1.0e-12,
        abs=1.0e-24,
    )
    assert float(summary["efficiency"]) == pytest.approx(
        math.exp(-expected_log_inefficiency),
        rel=1.0e-12,
        abs=1.0e-15,
    )
    assert float(summary["max_log_slack"]) == pytest.approx(math.log(2.0))
    assert not bool(summary["is_efficient"])

    peers = result.peers("B")
    assert peers["reference_dmu_id"].tolist() == ["A"]
    assert peers["lambda"].to_numpy() == pytest.approx([1.0])
    targets = result.targets_for("B").set_index(["role", "variable"])
    assert float(targets.loc[("input", "x"), "target"]) == pytest.approx(2.0)
    assert float(targets.loc[("output", "y"), "target"]) == pytest.approx(4.0)

    multipliers = result.multipliers_for("B").set_index("role")
    exponent_rows = multipliers.loc[
        ["input_exponent", "output_exponent"], "multiplier"
    ].to_numpy()
    assert exponent_rows == pytest.approx(
        [delta, delta],
        rel=1.0e-10,
        abs=delta * 1.0e-12,
    )
    assert float(multipliers.loc["log_intercept", "multiplier"]) == pytest.approx(
        -expected_log_inefficiency,
        rel=1.0e-10,
        abs=delta * 1.0e-12,
    )
    assert multipliers.loc[
        ["input_exponent", "output_exponent"], "lower_bound"
    ].to_numpy() == pytest.approx([delta, delta])

    diagnostic = result.diagnostics.set_index("dmu_id").loc["B"]
    assert bool(diagnostic["postsolve_certified"])
    assert bool(diagnostic["multiplier_certified"])
    assert bool(diagnostic["efficiency_underflowed"]) is underflows


@pytest.mark.parametrize(
    ("delta", "input_b", "reason"),
    [
        (
            np.nextafter(0.0, 1.0),
            2.0 * math.exp(0.25),
            "scaled_log_inefficiency_underflow",
        ),
        (
            np.finfo(np.float64).max,
            2.0 * math.exp(2.0),
            "scaled_log_inefficiency_overflow",
        ),
    ],
    ids=["positive-gap-underflow", "positive-gap-overflow"],
)
def test_unrepresentable_delta_scaled_log_gap_fails_closed(
    delta: float,
    input_b: float,
    reason: str,
) -> None:
    frame = _fixture()
    frame.loc[1, "x"] = input_b

    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        result = MultiplicativeDEA(exponent_floor=delta).fit(_data(frame))

    summary = result.summary().set_index("dmu_id").loc["B"]
    diagnostic = result.diagnostics.set_index("dmu_id").loc["B"]
    assert summary["solver_status"] == "failed"
    assert summary["failure_reason"] == reason
    assert math.isnan(float(summary["score"]))
    assert math.isnan(float(summary["distance"]))
    assert not bool(diagnostic["postsolve_certified"])
    assert diagnostic["certification_reason"] == reason
    assert result.targets_for("B").empty
    assert result.peers("B").empty
    assert result.slacks.loc[result.slacks["dmu_id"] == "B"].empty


def test_multiplicative_rejects_undesirable_outputs() -> None:
    frame = _fixture().assign(b=[1.0, 2.0])
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs="x",
        outputs="y",
        bad_outputs="b",
    )

    with pytest.raises(ModelSpecificationError, match="desirable outputs only"):
        MultiplicativeDEA().fit(data)


@pytest.mark.parametrize(
    ("column", "value"),
    [("x", 0.0), ("x", -1.0), ("y", 0.0), ("y", -1.0)],
    ids=["zero-input", "negative-input", "zero-output", "negative-output"],
)
def test_multiplicative_rejects_nonpositive_inputs_and_outputs(
    column: str,
    value: float,
) -> None:
    frame = _fixture()
    frame.loc[0, column] = value

    with pytest.raises(DataValidationError, match="strictly positive"):
        MultiplicativeDEA().fit(_data(frame))


def test_source_profile_marks_non_global_and_panel_extensions() -> None:
    cross_section = _data(_fixture())
    custom = MultiplicativeDEA(
        reference=ReferenceSpec(kind="custom", custom_rows=(0, 1))
    ).fit(cross_section)
    assert custom.metadata["source_profile_matches"] is False
    assert custom.metadata["source_profile_mismatches"] == (
        "reference_is_not_the_global_sample",
    )

    panel_frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [0, 0, 1, 1],
            "x": [2.0, 4.0, 2.2, 4.4],
            "y": [4.0, 4.0, 4.4, 4.4],
        }
    )
    panel = _data(panel_frame, period="period")

    global_panel = MultiplicativeDEA(reference="global").fit(panel)
    assert global_panel.metadata["source_profile_matches"] is False
    assert global_panel.metadata["source_profile_mismatches"] == (
        "data_are_not_one_cross_section",
    )

    contemporaneous_panel = MultiplicativeDEA(reference="contemporaneous").fit(panel)
    assert contemporaneous_panel.metadata["source_profile_matches"] is False
    assert contemporaneous_panel.metadata["source_profile_mismatches"] == (
        "data_are_not_one_cross_section",
        "reference_is_not_the_global_sample",
    )


def test_original_unit_output_overflow_preserves_log_score_and_log_target() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "x": np.exp([0.001, 10.0]),
            "y": np.exp([1.0, 1.0]),
        }
    )
    result = MultiplicativeDEA(variant="original_1982").fit(_data(frame))
    summary = result.summary().set_index("dmu_id").loc["B"]

    assert summary["solver_status"] == "optimal"
    assert float(summary["efficiency"]) == 0.0
    assert float(summary["distance"]) == pytest.approx(9_999.0, rel=1.0e-10)
    assert float(summary["log_efficiency"]) == pytest.approx(-9_999.0, rel=1.0e-10)

    output = (
        result.targets_for("B").set_index(["role", "variable"]).loc[("output", "y")]
    )
    assert math.isnan(float(output["target"]))
    assert float(output["log_target"]) == pytest.approx(10_000.0, rel=1.0e-10)
    assert not bool(output["original_unit_available"])
    assert not bool(output["factor_available"])
    assert output["transform_reason"] == "overflow"

    diagnostic = result.diagnostics.set_index("dmu_id").loc["B"]
    assert bool(diagnostic["postsolve_certified"])
    assert bool(diagnostic["efficiency_underflowed"])
    assert not bool(diagnostic["original_unit_targets_available"])
    assert diagnostic["target_transform_reasons"] == ("overflow",)


class _MalformedMarginalSolver:
    name = "malformed-multiplicative-marginals"

    def __init__(self, equality_marginals: np.ndarray) -> None:
        self._backend = SciPyHiGHSSolver()
        self._equality_marginals = equality_marginals

    def solve(self, problem: LinearProgram) -> LPSolution:
        solution = self._backend.solve(problem)
        return LPSolution(
            status=solution.status,
            objective=solution.objective,
            primal=solution.primal,
            message="injected malformed equality marginals",
            iterations=solution.iterations,
            inequality_marginals=solution.inequality_marginals,
            equality_marginals=self._equality_marginals,
            max_primal_violation=solution.max_primal_violation,
        )


@pytest.mark.parametrize(
    ("marginals", "reason"),
    [
        (np.asarray([1.0]), "wrong_marginal_length"),
        (np.asarray([1.0, np.nan, 1.0]), "nonfinite_marginals"),
    ],
    ids=["wrong-length", "nonfinite"],
)
def test_malformed_equality_marginals_never_publish_multipliers(
    marginals: np.ndarray,
    reason: str,
) -> None:
    result = MultiplicativeDEA(solver=_MalformedMarginalSolver(marginals)).fit(
        _data(_fixture())
    )

    assert (result.summary()["solver_status"] == "optimal").all()
    assert np.isfinite(result.summary()["log_efficiency"]).all()
    assert result.multipliers.empty
    assert result.diagnostics["postsolve_certified"].astype(bool).all()
    assert not result.diagnostics["multiplier_certified"].astype(bool).any()
    assert set(result.diagnostics["multiplier_certification_reason"]) == {reason}


def test_multiplier_scaling_overflow_is_silent_and_withholds_only_multipliers() -> None:
    huge_marginals = np.full(3, np.finfo(np.float64).max)
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        result = MultiplicativeDEA(
            exponent_floor=2.0,
            solver=_MalformedMarginalSolver(huge_marginals),
        ).fit(_data(_fixture()))

    assert (result.summary()["solver_status"] == "optimal").all()
    assert result.diagnostics["postsolve_certified"].astype(bool).all()
    assert not result.diagnostics["multiplier_certified"].astype(bool).any()
    assert set(result.diagnostics["multiplier_certification_reason"]) == {
        "nonfinite_scaled_marginals"
    }
    assert result.multipliers.empty
    assert not result.targets_for("B").empty
    assert not result.peers("B").empty


def test_multiplier_coordinate_overflow_is_silent_and_preserves_primal_results() -> (
    None
):
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        result = MultiplicativeDEA(exponent_floor=np.finfo(np.float64).max).fit(
            _data(_fixture())
        )

    assert (result.summary()["solver_status"] == "optimal").all()
    assert result.diagnostics["postsolve_certified"].astype(bool).all()
    assert not result.diagnostics["multiplier_certified"].astype(bool).any()
    assert set(result.diagnostics["multiplier_certification_reason"]) == {
        "nonfinite_restored_intercept"
    }
    assert result.multipliers.empty
    targets = result.targets_for("B").set_index(["role", "variable"])
    assert float(targets.loc[("input", "x"), "target"]) == pytest.approx(2.0)
    assert float(targets.loc[("output", "y"), "target"]) == pytest.approx(4.0)


def test_compiled_reference_template_is_read_only_and_reused_without_copying() -> None:
    log_inputs = np.log(np.asarray([[2.0], [4.0]], dtype=np.float64))
    log_outputs = np.log(np.asarray([[4.0], [8.0]], dtype=np.float64))
    compiled = _CompiledMultiplicativeReference.compile(
        log_inputs,
        log_outputs,
        np.asarray([0, 1], dtype=np.int64),
        MultiplicativeVariant.INVARIANT_1983,
    )
    baseline = compiled.a_eq.toarray()

    for matrix in (compiled.log_inputs, compiled.log_outputs, compiled.a_eq):
        for storage in (matrix.data, matrix.indices, matrix.indptr):
            assert not storage.flags.writeable
            with pytest.raises(ValueError, match="read-only"):
                storage[0] = storage[0]

    for array in (compiled.rows, compiled.input_anchor, compiled.output_anchor):
        assert not array.flags.writeable
        with pytest.raises(ValueError, match="read-only"):
            array[0] = array[0]

    problem = compiled.problem(log_inputs[1], log_outputs[1], "B")
    assert problem.a_eq is compiled.a_eq
    assert problem.a_eq is not None
    with pytest.raises(ValueError, match="read-only"):
        problem.a_eq[0, 1] = problem.a_eq[0, 1]
    np.testing.assert_array_equal(compiled.a_eq.toarray(), baseline)


def test_result_has_one_click_performance_visualization_contract() -> None:
    result = MultiplicativeDEA().fit(_data(_fixture()))

    plots = result.available_plots()
    assert [(plot.kind, plot.default_metric) for plot in plots] == [
        ("performance", "multiplicative_efficiency")
    ]
    prepared = prepare_performance_data(result)
    assert prepared.metric == "multiplicative_efficiency"
    assert prepared.measure.preferred_direction == "higher"
    assert prepared.measure.benchmark_value == 1.0
    assert prepared.observation_count == 2
