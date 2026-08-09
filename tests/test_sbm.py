import numpy as np
import pandas as pd
import pytest

import deapack.models.sbm as sbm_module
from deapack import (
    SBM,
    DEAData,
    InputOrientedSlacksBasedDEA,
    InputRussell,
    InputSBM,
    OutputOrientedSlacksBasedDEA,
    OutputRussell,
    OutputSBM,
    ReferenceSpec,
    SlacksBasedDEA,
    dataset_info,
    load_dataset,
)
from deapack.exceptions import DataValidationError
from deapack.solvers import SciPyHiGHSSolver


def _joint_slack_example(
    *, input_scale: float = 1.0, output_scale: float = 1.0
) -> DEAData:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "C"],
            "x": np.asarray([1.0, 2.0]) * input_scale,
            "y": np.asarray([2.0, 1.0]) * output_scale,
        }
    )
    return DEAData.from_frame(frame, dmu="dmu", inputs="x", outputs="y")


def test_sbm_fractional_score_and_components() -> None:
    result = SlacksBasedDEA().fit(_joint_slack_example())
    summary = result.summary().set_index("dmu_id")

    assert SBM is SlacksBasedDEA
    assert np.isclose(summary.loc["A", "efficiency"], 1.0)
    assert np.isclose(summary.loc["C", "input_inefficiency"], 0.5)
    assert np.isclose(summary.loc["C", "output_inefficiency"], 1.0)
    assert np.isclose(summary.loc["C", "score"], 0.25)
    assert np.isclose(summary.loc["C", "distance"], 0.75)
    assert not bool(summary.loc["C", "is_efficient"])

    targets = result.targets_for("C").set_index(["role", "variable"])
    assert np.isclose(targets.loc[("input", "x"), "target"], 1.0)
    assert np.isclose(targets.loc[("output", "y"), "target"], 2.0)
    assert result.peers("C")["reference_dmu_id"].tolist() == ["A"]


def test_sbm_is_units_invariant() -> None:
    baseline = SBM().fit(_joint_slack_example()).summary()["efficiency"]
    rescaled = (
        SBM()
        .fit(_joint_slack_example(input_scale=100.0, output_scale=0.01))
        .summary()["efficiency"]
    )

    assert np.allclose(rescaled, baseline)


def test_sbm_transforms_returns_to_scale_restrictions() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "x": [1.0, 2.0],
            "y": [1.0, 3.0],
        }
    )
    data = DEAData.from_frame(frame, dmu="dmu", inputs="x", outputs="y")

    vrs = SBM(returns_to_scale="vrs").fit(data).summary().set_index("dmu_id")
    crs = SBM(returns_to_scale="crs").fit(data).summary().set_index("dmu_id")

    assert np.isclose(vrs.loc["A", "efficiency"], 1.0)
    assert np.isclose(crs.loc["A", "efficiency"], 2.0 / 3.0)


def test_sbm_uses_the_shared_panel_reference_plan() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "A"],
            "year": [2020, 2021],
            "x": [1.0, 2.0],
            "y": [1.0, 1.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        period="year",
        inputs="x",
        outputs="y",
    )

    current = SBM(reference="contemporaneous").fit(data)
    global_result = SBM(reference="global").fit(data)

    assert np.isclose(current.summary().loc[1, "efficiency"], 1.0)
    assert np.isclose(global_result.summary().loc[1, "efficiency"], 0.5)


def test_sbm_rejects_zero_denominators() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "x": [1.0, 0.0],
            "y": [1.0, 1.0],
        }
    )
    data = DEAData.from_frame(frame, dmu="dmu", inputs="x", outputs="y")

    with pytest.raises(DataValidationError, match="strictly positive input"):
        SBM().fit(data)


@pytest.mark.parametrize("model", [InputSBM, OutputSBM, SBM])
def test_standard_tone_leaves_reject_zero_outputs_on_the_inactive_side(
    model,  # type: ignore[no-untyped-def]
) -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "x": [1.0, 2.0],
            "y": [1.0, 0.0],
        }
    )
    data = DEAData.from_frame(frame, dmu="dmu", inputs="x", outputs="y")

    with pytest.raises(DataValidationError, match="strictly positive output"):
        model().fit(data)


def test_project_slack_contrast_non_oriented_crs_oracle() -> None:
    frame = load_dataset("sbm_slack_contrast")
    roles = dataset_info("sbm_slack_contrast").roles
    data = DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )

    result = SBM(returns_to_scale="crs").fit(data)
    scores = result.summary().set_index("dmu_id")["efficiency"]
    assert scores.between(0.0, 1.0 + 1e-9).all()
    assert result.slacks["slack"].ge(-1e-9).all()

    input_scores = (
        InputSBM(returns_to_scale="crs")
        .fit(data)
        .summary()
        .set_index("dmu_id")["efficiency"]
    )
    output_scores = (
        OutputSBM(returns_to_scale="crs")
        .fit(data)
        .summary()
        .set_index("dmu_id")["efficiency"]
    )
    assert np.all(scores <= input_scores + 1e-10)
    assert np.all(scores <= output_scores + 1e-10)


def test_oriented_sbm_scores_and_public_aliases() -> None:
    data = _joint_slack_example()
    input_result = InputSBM().fit(data)
    output_result = OutputSBM().fit(data)
    joint_result = SBM().fit(data)

    assert InputSBM is InputOrientedSlacksBasedDEA
    assert InputRussell is InputOrientedSlacksBasedDEA
    assert OutputSBM is OutputOrientedSlacksBasedDEA
    assert OutputRussell is OutputOrientedSlacksBasedDEA

    input_summary = input_result.summary().set_index("dmu_id")
    output_summary = output_result.summary().set_index("dmu_id")
    joint_summary = joint_result.summary().set_index("dmu_id")
    assert np.isclose(input_summary.loc["C", "efficiency"], 0.5)
    assert np.isclose(output_summary.loc["C", "efficiency"], 0.5)
    assert np.isclose(output_summary.loc["C", "output_expansion_factor"], 2.0)
    assert np.isclose(output_summary.loc["C", "transform_scale"], 1.0)
    assert np.isclose(joint_summary.loc["C", "efficiency"], 0.25)
    assert joint_summary.loc["C", "efficiency"] <= input_summary.loc["C", "efficiency"]
    assert joint_summary.loc["C", "efficiency"] <= output_summary.loc["C", "efficiency"]

    assert input_result.metadata["method_id"] == "static.sbm.input.tone2001"
    assert output_result.metadata["method_id"] == "static.sbm.output.tone2001"
    assert input_result.metadata["orientation"] == "input"
    assert output_result.metadata["orientation"] == "output"
    assert input_result.metadata["native_score"] == "rho_I"
    assert output_result.metadata["native_score"] == "rho_O"
    assert input_result.metadata["linearization"] == "identity_scale"
    assert output_result.metadata["linearization"] == "identity_scale"
    assert input_result.metadata["strong_efficiency_certification"] == "not_performed"

    input_slacks = input_result.slacks.groupby("role")["included_in_objective"].first()
    output_slacks = output_result.slacks.groupby("role")[
        "included_in_objective"
    ].first()
    assert bool(input_slacks["input"])
    assert not bool(input_slacks["output"])
    assert not bool(output_slacks["input"])
    assert bool(output_slacks["output"])
    assert "input_balance_direct" in set(input_result.duals["constraint_role"])
    assert "output_balance_direct" in set(output_result.duals["constraint_role"])
    assert "input_balance_transformed" in set(joint_result.duals["constraint_role"])


def test_oriented_russell_aliases_preserve_tone_scores_and_contracts() -> None:
    data = _joint_slack_example()

    input_result = InputRussell().fit(data)
    output_result = OutputRussell().fit(data)
    input_summary = input_result.summary().set_index("dmu_id")
    output_summary = output_result.summary().set_index("dmu_id")

    assert input_result.metadata["method_id"] == "static.sbm.input.tone2001"
    assert output_result.metadata["method_id"] == "static.sbm.output.tone2001"
    assert np.isclose(input_summary.loc["C", "score"], 0.5)
    assert np.isclose(output_summary.loc["C", "output_expansion_factor"], 2.0)
    assert np.isclose(output_summary.loc["C", "score"], 0.5)

    input_slacks = input_result.slacks.query("dmu_id == 'C' and role == 'input'")
    input_factors = 1.0 - (input_slacks["slack"] / input_slacks["normalizer"])
    assert np.isclose(input_summary.loc["C", "score"], input_factors.mean())

    output_slacks = output_result.slacks.query("dmu_id == 'C' and role == 'output'")
    output_factors = 1.0 + (output_slacks["slack"] / output_slacks["normalizer"])
    assert np.isclose(
        output_summary.loc["C", "output_expansion_factor"],
        output_factors.mean(),
    )
    assert np.isclose(
        output_summary.loc["C", "score"],
        1.0 / output_factors.mean(),
    )


def test_exact_vrs_orientation_oracle_distinguishes_all_three_scores() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "O"],
            "x1": [2.0, 4.0, 4.0],
            "x2": [4.0, 2.0, 4.0],
            "y1": [1.0, 2.0, 1.0],
            "y2": [2.0, 1.0, 1.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs=["y1", "y2"],
    )

    input_summary = InputSBM(returns_to_scale="vrs").fit(data).summary()
    output_summary = OutputSBM(returns_to_scale="vrs").fit(data).summary()
    joint_summary = SBM(returns_to_scale="vrs").fit(data).summary()
    input_o = input_summary.set_index("dmu_id").loc["O"]
    output_o = output_summary.set_index("dmu_id").loc["O"]
    joint_o = joint_summary.set_index("dmu_id").loc["O"]

    assert np.isclose(input_o["efficiency"], 3.0 / 4.0)
    assert np.isclose(output_o["output_expansion_factor"], 3.0 / 2.0)
    assert np.isclose(output_o["efficiency"], 2.0 / 3.0)
    assert np.isclose(joint_o["efficiency"], 1.0 / 2.0)
    assert np.isclose(output_o["efficiency"] * output_o["output_expansion_factor"], 1.0)

    source = frame.set_index("dmu")
    for result in (
        InputSBM(returns_to_scale="vrs").fit(data),
        OutputSBM(returns_to_scale="vrs").fit(data),
        SBM(returns_to_scale="vrs").fit(data),
    ):
        peers = result.peers("O").set_index("reference_dmu_id")["lambda"]
        targets = result.targets_for("O").set_index(["role", "variable"])
        for role, variables in (
            ("input", ("x1", "x2")),
            ("output", ("y1", "y2")),
        ):
            for variable in variables:
                reconstructed = sum(
                    peers.loc[peer] * source.loc[peer, variable] for peer in peers.index
                )
                assert np.isclose(
                    targets.loc[(role, variable), "target"], reconstructed
                )


@pytest.mark.parametrize("model", [InputSBM, OutputSBM, SBM])
def test_each_sbm_orientation_is_units_invariant(model) -> None:  # type: ignore[no-untyped-def]
    baseline = model().fit(_joint_slack_example()).summary()
    rescaled = (
        model()
        .fit(_joint_slack_example(input_scale=100.0, output_scale=0.01))
        .summary()
    )
    assert np.allclose(rescaled["efficiency"], baseline["efficiency"])
    assert (
        rescaled["is_sbm_efficient"].tolist() == baseline["is_sbm_efficient"].tolist()
    )
    assert np.allclose(
        rescaled["max_objective_normalized_slack"],
        baseline["max_objective_normalized_slack"],
    )


@pytest.mark.parametrize(
    ("model", "frame", "scaled_column"),
    [
        (
            InputSBM,
            pd.DataFrame(
                {
                    "dmu": ["A", "B"],
                    "x": [0.001, 0.00100005],
                    "y": [1.0, 1.0],
                }
            ),
            "x",
        ),
        (
            OutputSBM,
            pd.DataFrame(
                {
                    "dmu": ["A", "B"],
                    "x": [1.0, 1.0],
                    "y": [0.00100005, 0.001],
                }
            ),
            "y",
        ),
    ],
)
def test_oriented_sbm_unit_invariance_at_the_numerical_cleanup_boundary(
    model,  # type: ignore[no-untyped-def]
    frame: pd.DataFrame,
    scaled_column: str,
) -> None:
    original = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs="x",
        outputs="y",
    )
    scaled_frame = frame.copy()
    scaled_frame[scaled_column] *= 1000.0
    rescaled = DEAData.from_frame(
        scaled_frame,
        dmu="dmu",
        inputs="x",
        outputs="y",
    )

    baseline = model(returns_to_scale="vrs").fit(original)
    converted = model(returns_to_scale="vrs").fit(rescaled)
    baseline_summary = baseline.summary().set_index("dmu_id")
    converted_summary = converted.summary().set_index("dmu_id")

    assert baseline_summary.loc["B", "efficiency"] < 1.0
    assert not bool(baseline_summary.loc["B", "is_sbm_efficient"])
    assert converted_summary["efficiency"].to_numpy() == pytest.approx(
        baseline_summary["efficiency"].to_numpy(),
        abs=1e-12,
    )
    assert converted_summary["is_sbm_efficient"].tolist() == (
        baseline_summary["is_sbm_efficient"].tolist()
    )
    baseline_active = baseline.slacks.loc[
        baseline.slacks["included_in_objective"], "normalized_slack"
    ]
    converted_active = converted.slacks.loc[
        converted.slacks["included_in_objective"], "normalized_slack"
    ]
    assert converted_active.to_numpy() == pytest.approx(
        baseline_active.to_numpy(),
        abs=1e-12,
    )


@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf])
def test_sbm_rejects_nonfinite_tolerances(value: float) -> None:
    with pytest.raises(ValueError, match="tolerance must be finite and positive"):
        SBM(tolerance=value)
    with pytest.raises(ValueError, match="peer_tolerance must be finite and positive"):
        SBM(peer_tolerance=value)


def test_single_orientation_does_not_claim_strong_efficiency() -> None:
    input_frame = pd.DataFrame({"dmu": ["A", "C"], "x": [1.0, 1.0], "y": [2.0, 1.0]})
    input_data = DEAData.from_frame(input_frame, dmu="dmu", inputs="x", outputs="y")
    reference = ReferenceSpec(kind="custom", custom_rows=[0])
    input_result = InputSBM(reference=reference).fit(input_data)
    input_summary = input_result.summary().set_index("dmu_id")
    assert np.isclose(input_summary.loc["C", "efficiency"], 1.0)
    assert bool(input_summary.loc["C", "is_sbm_efficient"])
    assert pd.isna(input_summary.loc["C", "is_efficient"])
    assert np.isclose(input_summary.loc["C", "max_unoptimized_side_slack"], 1.0)

    output_frame = pd.DataFrame({"dmu": ["A", "C"], "x": [1.0, 2.0], "y": [1.0, 1.0]})
    output_data = DEAData.from_frame(output_frame, dmu="dmu", inputs="x", outputs="y")
    output_result = OutputSBM(reference=reference).fit(output_data)
    output_summary = output_result.summary().set_index("dmu_id")
    assert np.isclose(output_summary.loc["C", "efficiency"], 1.0)
    assert bool(output_summary.loc["C", "is_sbm_efficient"])
    assert pd.isna(output_summary.loc["C", "is_efficient"])
    assert np.isclose(output_summary.loc["C", "max_unoptimized_side_slack"], 1.0)

    targets = output_result.targets_for("C")
    assert set(targets["selection_status"]) == {"solver_selected_primary_optimum"}


@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs", "nirs", "ndrs"])
@pytest.mark.parametrize("model", [InputSBM, OutputSBM, SBM])
def test_sbm_common_compiler_supports_all_registered_rts(
    model,  # type: ignore[no-untyped-def]
    returns_to_scale: str,
) -> None:
    result = model(returns_to_scale=returns_to_scale).fit(_joint_slack_example())
    assert set(result.summary()["solver_status"]) == {"optimal"}
    assert result.metadata["returns_to_scale"] == returns_to_scale
    expected_provenance = (
        "tone_2001_explicit"
        if returns_to_scale in {"crs", "vrs"}
        else "deapack_convex_envelopment_variant"
    )
    assert result.metadata["returns_to_scale_provenance"] == expected_provenance


class _CountingSolver:
    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self.delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        return self.delegate.solve(problem)


@pytest.mark.parametrize("model", [InputSBM, OutputSBM, SBM])
def test_sbm_compiles_each_reference_set_once_and_solves_once_per_observation(
    model,  # type: ignore[no-untyped-def]
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    solver = _CountingSolver()
    compile_calls = 0
    original_compile = sbm_module.compile_reference

    def counted_compile(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal compile_calls
        compile_calls += 1
        return original_compile(*args, **kwargs)

    monkeypatch.setattr(sbm_module, "compile_reference", counted_compile)
    result = model(reference="global", solver=solver).fit(_joint_slack_example())

    assert solver.calls == 2
    assert compile_calls == 1
    assert result.metadata["primary_solver_calls"] == 2
    assert result.metadata["solver_calls"] == 2
    assert result.metadata["compiled_reference_sets"] == 1


def test_oriented_sbm_expanded_specs_match_the_managerial_question() -> None:
    data = _joint_slack_example()
    input_result = InputSBM().fit(data)
    output_result = OutputSBM().fit(data)

    input_spec = input_result.metadata["expanded_spec"]
    assert input_spec["context"]["purpose"] == "resource_conservation_benchmarking"
    assert input_spec["performance"]["normalization"] == ("evaluated_dmu_input_values")
    assert input_spec["valuation"]["kind"] == "equal_input_dimension_weights"
    assert input_spec["evaluation_protocol"]["unoptimized_side"] == (
        "feasible_output_slacks"
    )

    output_spec = output_result.metadata["expanded_spec"]
    assert output_spec["context"]["purpose"] == "service_expansion_benchmarking"
    assert output_spec["performance"]["normalization"] == (
        "evaluated_dmu_output_values"
    )
    assert output_spec["valuation"]["kind"] == "equal_output_dimension_weights"
    assert output_spec["evaluation_protocol"]["objective_form"] == (
        "direct_output_expansion_linear_program"
    )
    assert output_result.metadata["direct_objective_account"] == "tau_O"
    assert output_result.metadata["reported_efficiency"] == "rho_O"
