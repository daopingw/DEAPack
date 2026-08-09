import numpy as np
import pandas as pd
import pytest

from deapack import (
    BCC,
    CCR,
    BCCInput,
    BCCOutput,
    CCRInput,
    CCROutput,
    DEAData,
    RadialDEA,
    ReferenceSpec,
    ReturnsToScale,
    SolverStatus,
)
from deapack.exceptions import ModelSpecificationError
from deapack.solvers import LPSolution, SciPyHiGHSSolver


class _FailingPhaseTwoSolver:
    name = "phase_two_failure_fixture"

    def __init__(self) -> None:
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        if problem.name.endswith(":slacks"):
            return LPSolution(
                status=SolverStatus.LIMIT_REACHED,
                objective=None,
                primal=None,
                message="injected phase-two failure",
                iterations=0,
            )
        return self._delegate.solve(problem)


def _cross_section() -> DEAData:
    frame = pd.DataFrame(
        {
            "unit": ["A", "B", "C"],
            "input": [1.0, 2.0, 1.0],
            "output": [1.0, 1.0, 0.5],
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="unit",
        inputs="input",
        outputs="output",
    )


def test_input_crs_radial_efficiency_and_peers() -> None:
    result = CCR(orientation="input").fit(_cross_section())
    summary = result.summary().set_index("dmu_id")

    assert np.isclose(summary.loc["A", "score"], 1.0)
    assert np.isclose(summary.loc["B", "efficiency"], 0.5)
    assert np.isclose(summary.loc["C", "efficiency"], 0.5)
    assert bool(summary.loc["A", "is_efficient"])
    assert bool(summary.loc["A", "is_within_reference_technology"])
    assert result.metadata["native_score"] == "theta"
    assert result.peers("B")["reference_dmu_id"].tolist() == ["A"]


def test_output_crs_reports_phi_and_reciprocal_efficiency() -> None:
    result = RadialDEA(orientation="output", returns_to_scale="crs").fit(
        _cross_section()
    )
    summary = result.summary().set_index("dmu_id")

    assert np.isclose(summary.loc["B", "score"], 2.0)
    assert np.isclose(summary.loc["B", "efficiency"], 0.5)
    assert result.metadata["native_score"] == "phi"
    assert result.metadata["efficiency_transform"] == "reciprocal"


def test_vrs_phase_two_identifies_nonzero_output_slack() -> None:
    result = BCC(orientation="input").fit(_cross_section())
    summary = result.summary().set_index("dmu_id")

    assert np.isclose(summary.loc["C", "efficiency"], 1.0)
    assert not bool(summary.loc["C", "is_efficient"])
    c_output_slack = result.slacks.query("dmu_id == 'C' and role == 'output'")[
        "slack"
    ].iloc[0]
    assert np.isclose(c_output_slack, 0.5)
    assert result.metadata["phase_one_solver_calls"] == 3
    assert result.metadata["phase_two_solver_calls"] == 3
    assert result.metadata["solver_calls"] == 6


def test_vrs_strong_efficiency_is_invariant_to_output_units() -> None:
    for scale in (1.0, 1e-12):
        data = DEAData.from_frame(
            pd.DataFrame(
                {
                    "unit": ["A", "B"],
                    "input": [1.0, 1.0],
                    "y1": [1.0, 1.0],
                    "y2": [scale, 2.0 * scale],
                }
            ),
            dmu="unit",
            inputs="input",
            outputs=["y1", "y2"],
        )
        result = BCC(orientation="input").fit(data)
        row = result.summary().set_index("dmu_id").loc["A"]
        y2_target = result.targets.query(
            "dmu_id == 'A' and role == 'output' and variable == 'y2'"
        ).iloc[0]

        assert np.isclose(row["score"], 1.0)
        assert bool(row["is_radially_efficient"])
        assert not bool(row["is_efficient"])
        assert np.isclose(row["max_scaled_slack"], 0.5)
        assert np.isclose(y2_target["target"], 2.0 * scale)


def test_panel_reference_rule_is_independent_of_measure() -> None:
    frame = pd.DataFrame(
        {
            "unit": ["A", "A"],
            "year": [2020, 2021],
            "input": [1.0, 2.0],
            "output": [1.0, 1.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="unit",
        period="year",
        inputs="input",
        outputs="output",
    )

    current = CCR(reference=ReferenceSpec("contemporaneous")).fit(data)
    global_result = CCR(reference=ReferenceSpec("global")).fit(data)

    assert np.isclose(current.summary().loc[1, "efficiency"], 1.0)
    assert np.isclose(global_result.summary().loc[1, "efficiency"], 0.5)


def test_score_only_mode_skips_phase_two_without_claiming_strong_efficiency() -> None:
    result = BCC(compute_slacks=False).fit(_cross_section())
    summary = result.summary().set_index("dmu_id")

    assert np.isclose(summary.loc["C", "efficiency"], 1.0)
    assert bool(summary.loc["C", "is_radially_efficient"])
    assert pd.isna(summary.loc["C", "is_efficient"])
    assert result.slacks.empty
    assert result.targets.empty
    assert set(result.diagnostics["phase"]) == {1}
    assert result.metadata["phase_one_solver_calls"] == 3
    assert result.metadata["phase_two_solver_calls"] == 0
    assert result.metadata["solver_calls"] == 3


def test_phase_two_failure_does_not_claim_strong_efficiency() -> None:
    result = BCC(solver=_FailingPhaseTwoSolver()).fit(_cross_section())
    summary = result.summary().set_index("dmu_id")

    assert bool(summary.loc["A", "is_radially_efficient"])
    assert pd.isna(summary.loc["A", "is_efficient"])
    assert summary.loc["A", "solver_status"] == "limit_reached"
    assert summary.loc["A", "backend_solver_status"] == "limit_reached"
    assert summary.loc["A", "raw_solver_status"] == "limit_reached"
    assert summary.loc["A", "primary_solver_status"] == "optimal"
    assert summary.loc["A", "primary_semantic_solver_status"] == "optimal"
    assert summary.loc["A", "primary_backend_solver_status"] == "optimal"
    assert summary.loc["A", "primary_raw_solver_status"] == "optimal"
    assert summary.loc["A", "completion_solver_status"] == "limit_reached"
    assert summary.loc["A", "completion_semantic_solver_status"] == "limit_reached"
    assert summary.loc["A", "completion_backend_solver_status"] == "limit_reached"
    assert summary.loc["A", "completion_raw_solver_status"] == "limit_reached"
    assert set(result.diagnostics["phase"]) == {1, 2}


def test_radial_dea_uses_explicit_custom_reference_rows() -> None:
    result = BCC(
        orientation="input",
        reference=ReferenceSpec("custom", custom_rows=[0]),
    ).fit(_cross_section())
    summary = result.summary().set_index("dmu_id")

    assert np.isclose(summary.loc["B", "efficiency"], 0.5)
    assert result.metadata["reference_kind"] == "custom"
    assert result.peers("B")["reference_dmu_id"].tolist() == ["A"]


def test_external_reference_scores_outside_technology_have_nullable_flags() -> None:
    cases = (
        (
            "input",
            pd.DataFrame(
                {
                    "unit": ["reference", "evaluated"],
                    "input": [2.0, 1.0],
                    "output": [2.0, 2.0],
                }
            ),
            2.0,
        ),
        (
            "output",
            pd.DataFrame(
                {
                    "unit": ["reference", "evaluated"],
                    "input": [1.0, 1.0],
                    "output": [1.0, 2.0],
                }
            ),
            0.5,
        ),
    )

    for orientation, frame, expected_score in cases:
        data = DEAData.from_frame(
            frame,
            dmu="unit",
            inputs="input",
            outputs="output",
        )
        result = BCC(
            orientation=orientation,
            reference=ReferenceSpec("custom", custom_rows=[0]),
        ).fit(data)
        row = result.summary().set_index("dmu_id").loc["evaluated"]

        assert np.isclose(row["score"], expected_score)
        assert np.isclose(row["efficiency"], 2.0)
        assert not bool(row["is_within_reference_technology"])
        assert pd.isna(row["is_radially_efficient"])
        assert pd.isna(row["is_efficient"])


def test_infeasible_external_reference_is_outside_technology() -> None:
    frame = pd.DataFrame(
        {
            "unit": ["reference", "evaluated"],
            "input": [1.0, 1.0],
            "output": [1.0, 2.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="unit",
        inputs="input",
        outputs="output",
    )
    result = BCC(
        orientation="input",
        reference=ReferenceSpec("custom", custom_rows=[0]),
    ).fit(data)
    row = result.summary().set_index("dmu_id").loc["evaluated"]

    assert row["solver_status"] == "infeasible"
    assert row["backend_solver_status"] == "infeasible"
    assert row["raw_solver_status"] == "infeasible"
    assert row["primary_solver_status"] == "infeasible"
    assert row["primary_semantic_solver_status"] == "infeasible"
    assert row["primary_backend_solver_status"] == "infeasible"
    assert row["primary_raw_solver_status"] == "infeasible"
    assert not bool(row["is_within_reference_technology"])
    assert pd.isna(row["is_radially_efficient"])
    assert pd.isna(row["is_efficient"])


@pytest.mark.parametrize(
    ("preset_type", "orientation", "returns_to_scale"),
    [
        (CCRInput, "input", "crs"),
        (CCROutput, "output", "crs"),
        (BCCInput, "input", "vrs"),
        (BCCOutput, "output", "vrs"),
    ],
)
def test_named_radial_presets_match_the_shared_kernel(
    preset_type,
    orientation: str,
    returns_to_scale: str,
) -> None:
    data = _cross_section()
    preset = preset_type().fit(data)
    generic = RadialDEA(
        orientation=orientation,
        returns_to_scale=returns_to_scale,
        compute_slacks=True,
    ).fit(data)

    pd.testing.assert_frame_equal(preset.summary(), generic.summary())
    pd.testing.assert_frame_equal(preset.slacks, generic.slacks)
    pd.testing.assert_frame_equal(preset.targets, generic.targets)
    pd.testing.assert_frame_equal(preset.intensities, generic.intensities)
    assert preset_type().orientation.value == orientation
    assert preset_type().returns_to_scale.value == returns_to_scale
    assert preset_type().compute_slacks is True


@pytest.mark.parametrize("preset_type", [CCRInput, CCROutput, BCCInput, BCCOutput])
@pytest.mark.parametrize(
    ("argument", "value"),
    [
        ("orientation", "input"),
        ("returns_to_scale", "crs"),
        ("compute_slacks", False),
    ],
)
def test_named_radial_presets_reject_identity_overrides(
    preset_type,
    argument: str,
    value,
) -> None:
    with pytest.raises(TypeError):
        preset_type(**{argument: value})


@pytest.mark.parametrize("preset_type", [CCRInput, CCROutput, BCCInput, BCCOutput])
def test_named_radial_presets_fail_closed_after_identity_mutation(
    preset_type,
) -> None:
    base = preset_type()
    mutations = (
        (
            "orientation",
            ("output" if base.orientation.value == "input" else "input"),
        ),
        ("orientation", base.orientation.value),
        (
            "returns_to_scale",
            (
                ReturnsToScale.VRS
                if base.returns_to_scale is ReturnsToScale.CRS
                else ReturnsToScale.CRS
            ),
        ),
        ("returns_to_scale", base.returns_to_scale.value),
        ("compute_slacks", False),
        ("compute_slacks", 1),
    )

    for attribute, value in mutations:
        model = preset_type()
        setattr(model, attribute, value)
        with pytest.raises(ModelSpecificationError, match="fixed registry identity"):
            model.fit(_cross_section())


@pytest.mark.parametrize(
    ("model", "changed_returns_to_scale"),
    [
        (CCR(), ReturnsToScale.VRS),
        (CCR(), "crs"),
        (BCC(), ReturnsToScale.CRS),
        (BCC(), "vrs"),
    ],
)
def test_rts_specializations_fail_closed_after_identity_mutation(
    model,
    changed_returns_to_scale,
) -> None:
    model.returns_to_scale = changed_returns_to_scale

    with pytest.raises(ModelSpecificationError, match="fixed registry identity"):
        model.fit(_cross_section())
