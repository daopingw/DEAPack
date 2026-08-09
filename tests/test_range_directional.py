from __future__ import annotations

from dataclasses import replace
from inspect import signature

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import linprog

import deapack.models.range_directional as range_directional_module
from deapack import (
    RDM,
    DEAData,
    RadialDEA,
    RangeDirectionalDEA,
    ReferenceSpec,
    SolverOptions,
    SolverStatus,
    load_dataset,
)
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.solvers import LPSolution, SciPyHiGHSSolver


class _CountingSolver:
    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self.problems = []
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        self.problems.append(problem)
        return self._delegate.solve(problem)


class _FailingSolver:
    name = "failing-rdm-fixture"

    def __init__(self) -> None:
        self.calls = 0

    def solve(self, problem):  # type: ignore[no-untyped-def]
        del problem
        self.calls += 1
        return LPSolution(
            status=SolverStatus.LIMIT_REACHED,
            objective=None,
            primal=None,
            message="injected phase-one failure",
            iterations=0,
        )


class _OutOfRangeBetaSolver:
    name = "out-of-range-beta-fixture"

    def __init__(self) -> None:
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        solution = self._delegate.solve(problem)
        assert solution.primal is not None
        primal = np.array(solution.primal, copy=True)
        primal[-1] = 1.25
        primal.setflags(write=False)
        return replace(solution, primal=primal)


def _oracle_data(frame: pd.DataFrame | None = None) -> DEAData:
    source = load_dataset("range_directional_signed") if frame is None else frame
    return DEAData.from_frame(
        source,
        dmu="dmu",
        inputs="input",
        outputs="output",
    )


def _direct_equation_beta(
    data: DEAData,
    observation: int,
    orientation: str,
) -> tuple[int, float | None]:
    """Compile the source equation directly, independently of DEAPack."""

    x_o = data.inputs[observation]
    y_o = data.outputs[observation]
    input_direction = x_o - np.min(data.inputs, axis=0)
    output_direction = np.max(data.outputs, axis=0) - y_o
    if orientation == "input":
        output_direction = np.zeros_like(output_direction)
    elif orientation == "output":
        input_direction = np.zeros_like(input_direction)

    n = data.n_dmus
    objective = np.zeros(n + 1)
    objective[-1] = -1.0
    input_rows = np.column_stack([data.inputs.T, input_direction])
    output_rows = np.column_stack([-data.outputs.T, output_direction])
    result = linprog(
        objective,
        A_ub=np.vstack([input_rows, output_rows]),
        b_ub=np.concatenate([x_o, -y_o]),
        A_eq=np.asarray([[*np.ones(n), 0.0]]),
        b_eq=np.asarray([1.0]),
        bounds=[(0.0, None)] * (n + 1),
        method="highs",
    )
    beta = None if result.x is None else float(result.x[-1])
    return int(result.status), beta


def test_exact_signed_rational_oracle_and_phase_one_accounts() -> None:
    result = RangeDirectionalDEA().fit(_oracle_data())
    summary = result.summary().set_index("dmu_id")

    assert RDM is RangeDirectionalDEA
    assert summary.loc["C", "beta"] == pytest.approx(2.0 / 3.0)
    assert summary.loc["C", "score"] == pytest.approx(2.0 / 3.0)
    assert summary.loc["C", "distance"] == pytest.approx(2.0 / 3.0)
    assert summary.loc["C", "rdm_efficiency"] == pytest.approx(1.0 / 3.0)
    assert summary.loc["C", "efficiency"] == pytest.approx(1.0 / 3.0)
    assert summary.loc["C", "is_efficient"] is False
    assert not bool(summary.loc["C", "is_directionally_efficient"])
    assert pd.isna(summary.loc["A", "is_efficient"])
    assert bool(summary.loc["A", "is_directionally_efficient"])

    targets = result.targets_for("C").set_index(["role", "variable"])
    assert targets.loc[("input", "input"), "target"] == pytest.approx(-2.0 / 3.0)
    assert targets.loc[("output", "output"), "target"] == pytest.approx(10.0 / 3.0)
    assert targets.loc[("input", "input"), "peer_activity"] == pytest.approx(-2.0 / 3.0)
    assert targets.loc[("output", "output"), "peer_activity"] == pytest.approx(
        10.0 / 3.0
    )
    assert not targets["target_pareto_certified"].any()

    peers = result.peers("C").set_index("reference_dmu_id")
    assert peers.loc["A", "lambda"] == pytest.approx(2.0 / 3.0)
    assert peers.loc["B", "lambda"] == pytest.approx(1.0 / 3.0)
    assert "C" not in peers.index
    assert np.allclose(result.slacks.query("dmu_id == 'C'")["slack"], 0.0)
    assert set(result.duals["constraint_role"]) == {
        "input",
        "output",
        "returns_to_scale",
    }
    assert set(result.diagnostics["phase"]) == {1}
    assert set(result.diagnostics["certificate_status"]) == {"certified"}


@pytest.mark.parametrize(
    ("orientation", "zero_direction_dmu", "expected_input", "expected_output"),
    (
        ("input", "A", -2.0, -2.0),
        ("output", "B", 2.0, 6.0),
    ),
)
def test_source_orientations_zero_only_the_inactive_side(
    orientation: str,
    zero_direction_dmu: str,
    expected_input: float,
    expected_output: float,
) -> None:
    result = RDM(orientation=orientation).fit(_oracle_data())
    summary = result.summary().set_index("dmu_id")

    assert summary.loc["C", "beta"] == pytest.approx(1.0)
    assert summary.loc["C", "rdm_efficiency"] == pytest.approx(0.0)
    assert summary.loc[zero_direction_dmu, "solver_status"] == ("unbounded_direction")
    assert pd.isna(summary.loc[zero_direction_dmu, "efficiency"])

    targets = result.targets_for("C").set_index("role")
    assert targets.loc["input", "target"] == pytest.approx(expected_input)
    assert targets.loc["output", "target"] == pytest.approx(expected_output)
    inactive_role = "output" if orientation == "input" else "input"
    assert targets.loc[inactive_role, "direction"] == pytest.approx(0.0)
    assert targets.loc[inactive_role, "target"] == pytest.approx(
        targets.loc[inactive_role, "observed"]
    )


@pytest.mark.parametrize("orientation", ("non-oriented", "input", "output"))
def test_independent_direct_scipy_equation_compiler(orientation: str) -> None:
    data = _oracle_data()
    result = RDM(orientation=orientation).fit(data)
    summary = result.summary()

    for observation in range(data.n_dmus):
        direct_status, direct_beta = _direct_equation_beta(
            data,
            observation,
            orientation,
        )
        row = summary.iloc[observation]
        if direct_status == 3:
            assert row["solver_status"] == "unbounded_direction"
            assert np.isnan(row["beta"])
        else:
            assert direct_status == 0
            assert row["solver_status"] == "optimal"
            assert row["beta"] == pytest.approx(direct_beta)


def test_translation_unit_and_row_order_invariance() -> None:
    frame = load_dataset("range_directional_signed")
    baseline = RDM().fit(_oracle_data(frame))

    translated_frame = frame.assign(
        input=frame["input"] + 10.0,
        output=frame["output"] - 7.0,
    )
    translated = RDM().fit(_oracle_data(translated_frame))

    rescaled_frame = frame.assign(
        input=3.0 * frame["input"],
        output=2.0 * frame["output"],
    )
    rescaled = RDM().fit(_oracle_data(rescaled_frame))

    large_units_frame = frame.assign(
        input=1.0e12 * frame["input"],
        output=1.0e9 * frame["output"],
    )
    large_units = RDM().fit(_oracle_data(large_units_frame))

    reordered = RDM().fit(_oracle_data(frame.iloc[::-1].reset_index(drop=True)))

    baseline_summary = baseline.summary().set_index("dmu_id").sort_index()
    for changed in (translated, rescaled, large_units, reordered):
        changed_summary = changed.summary().set_index("dmu_id").sort_index()
        np.testing.assert_allclose(
            changed_summary["beta"],
            baseline_summary["beta"],
            atol=1e-10,
        )
        np.testing.assert_allclose(
            changed_summary["rdm_efficiency"],
            baseline_summary["rdm_efficiency"],
            atol=1e-10,
        )

    base_targets = baseline.targets_for("C").set_index("role")
    translated_targets = translated.targets_for("C").set_index("role")
    rescaled_targets = rescaled.targets_for("C").set_index("role")
    large_units_targets = large_units.targets_for("C").set_index("role")
    assert translated_targets.loc["input", "target"] == pytest.approx(
        base_targets.loc["input", "target"] + 10.0
    )
    assert translated_targets.loc["output", "target"] == pytest.approx(
        base_targets.loc["output", "target"] - 7.0
    )
    assert rescaled_targets.loc["input", "target"] == pytest.approx(
        3.0 * base_targets.loc["input", "target"]
    )
    assert rescaled_targets.loc["output", "target"] == pytest.approx(
        2.0 * base_targets.loc["output", "target"]
    )
    assert large_units_targets.loc["input", "target"] == pytest.approx(
        1.0e12 * base_targets.loc["input", "target"]
    )
    assert large_units_targets.loc["output", "target"] == pytest.approx(
        1.0e9 * base_targets.loc["output", "target"]
    )


def test_partial_zero_range_is_kept_but_all_zero_fails_per_observation() -> None:
    partial = RDM().fit(_oracle_data())
    input_row = partial.targets_for("A").query("role == 'input'").iloc[0]

    assert input_row["direction"] == pytest.approx(0.0)
    assert input_row["target"] == pytest.approx(input_row["observed"])
    assert partial.summary().set_index("dmu_id").loc["A", "solver_status"] == (
        "optimal"
    )

    one = pd.DataFrame({"dmu": ["only"], "input": [-3.0], "output": [-5.0]})
    solver = _CountingSolver()
    all_zero = RDM(solver=solver).fit(_oracle_data(one))
    row = all_zero.summary().iloc[0]

    assert row["solver_status"] == "unbounded_direction"
    assert np.isnan(row["beta"])
    assert np.isnan(row["efficiency"])
    assert pd.isna(row["is_efficient"])
    assert solver.calls == 0
    assert all_zero.metadata["solver_calls"] == 0
    assert all_zero.targets.empty
    assert all_zero.slacks.empty
    assert all_zero.intensities.empty
    assert all_zero.duals.empty


def test_reference_extrema_and_technology_share_a_self_inclusive_plan() -> None:
    data = _oracle_data()
    with pytest.raises(ModelSpecificationError, match="every focal observation"):
        RDM(reference=ReferenceSpec("custom", custom_rows=[0, 1])).fit(data)

    result = RDM(reference=ReferenceSpec("custom", custom_rows=[0, 1, 2])).fit(data)
    expanded_reference = result.metadata["expanded_spec"]["reference"]

    assert result.metadata["reference_kind"] == "custom"
    assert result.metadata["self_membership"] == "required"
    assert expanded_reference["extrema_population"] == (
        "identical_to_technology_population"
    )


def test_signed_data_is_local_to_rdm_and_bad_outputs_are_rejected() -> None:
    signed = _oracle_data()
    assert (RDM().fit(signed).summary()["solver_status"] == "optimal").all()
    with pytest.raises(DataValidationError, match="nonnegative"):
        RadialDEA().fit(signed)

    frame = load_dataset("range_directional_signed").assign(bad=[1.0, 2.0, 3.0])
    environmental = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs="input",
        outputs="output",
        bad_outputs="bad",
    )
    with pytest.raises(ModelSpecificationError, match="undesirable outputs"):
        RDM().fit(environmental)


def test_constructor_surface_and_validation_are_source_bounded() -> None:
    parameters = signature(RangeDirectionalDEA).parameters
    assert tuple(parameters) == (
        "orientation",
        "reference",
        "solver",
        "solver_options",
        "tolerance",
        "peer_tolerance",
    )
    assert parameters["orientation"].default == "non-oriented"

    with pytest.raises(ValueError, match="non-oriented"):
        RDM(orientation="directional")
    with pytest.raises(ValueError, match="finite"):
        RDM(tolerance=np.nan)
    with pytest.raises(ValueError, match="finite"):
        RDM(peer_tolerance=np.inf)
    with pytest.raises(ValueError, match="pass solver or solver_options"):
        RDM(solver=_CountingSolver(), solver_options=SolverOptions())


def test_solver_and_score_certificate_failures_withhold_outputs() -> None:
    failing = _FailingSolver()
    failed = RDM(solver=failing).fit(_oracle_data())

    assert failing.calls == 3
    assert set(failed.summary()["solver_status"]) == {"limit_reached"}
    assert failed.summary()["score"].isna().all()
    assert failed.targets.empty
    assert failed.slacks.empty
    assert failed.intensities.empty
    assert failed.duals.empty

    violated = RDM(solver=_OutOfRangeBetaSolver()).fit(_oracle_data())
    assert set(violated.summary()["solver_status"]) == {"score_domain_violation"}
    assert violated.summary()["beta"].isna().all()
    assert violated.targets.empty
    assert violated.slacks.empty
    assert violated.intensities.empty
    assert violated.duals.empty
    assert np.allclose(violated.diagnostics["raw_beta"], 1.25)
    assert np.allclose(violated.diagnostics["beta_range_violation"], 0.25)
    assert set(violated.diagnostics["certificate_status"]) == {"failed_beta_range"}


def test_one_lp_per_valid_observation_compilation_reuse_and_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    solver = _CountingSolver()
    compilations = 0
    original_compile = range_directional_module.compile_reference

    def counted_compile(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal compilations
        compilations += 1
        return original_compile(*args, **kwargs)

    monkeypatch.setattr(
        range_directional_module,
        "compile_reference",
        counted_compile,
    )
    result = RDM(solver=solver).fit(_oracle_data())

    assert solver.calls == 3
    assert all(problem.name.endswith(":directional") for problem in solver.problems)
    assert compilations == 1
    assert result.metadata["method_id"] == (
        "static.range_directional.portela_thanassoulis_simpson_2004"
    )
    assert result.metadata["orientation"] == "non-oriented"
    assert result.metadata["returns_to_scale"] == "vrs"
    assert result.metadata["native_score"] == "beta"
    assert result.metadata["score_direction"] == "higher_is_farther"
    assert result.metadata["rdm_efficiency_direction"] == "higher_is_better"
    assert result.metadata["efficiency_transform"] == "one_minus_beta"
    assert result.metadata["source_phase"] == 1
    assert result.metadata["secondary_target_phase"] == "not_implemented"
    assert result.metadata["compiled_reference_sets"] == 1
    assert result.metadata["phase_one_solves"] == 3
    assert result.metadata["solver_calls"] == 3
    assert result.metadata["targets_use_unthresholded_intensities"] is True
    assert result.metadata["solver_row_scaling"] == (
        "max_absolute_reference_focal_and_direction_by_account"
    )
    assert result.metadata["source"]["doi"] == ("10.1057/palgrave.jors.2601768")
    assert tuple(result.metadata["source"]["equations"]) == (1, 2, 3)
    assert result.metadata["source"]["published_bank_application_reproduced"] is (False)
    expanded = result.metadata["expanded_spec"]
    assert expanded["performance"]["direction_policy"] == (
        "focal_to_reference_coordinatewise_ideal"
    )
    assert expanded["evaluation_protocol"]["phase"] == "source_phase_one_only"
