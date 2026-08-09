import numpy as np
import pandas as pd
import pytest

from deapack import (
    ByProductionDDF,
    ByProductionDirectionalDistanceDEA,
    DEAData,
    ReferenceSpec,
    SolverStatus,
)
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.solvers import LPSolution


def _by_production_example(
    *,
    input_scale: float = 1.0,
    output_scale: float = 1.0,
    bad_output_scale: float = 1.0,
) -> DEAData:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "C"],
            "energy": np.asarray([1.0, 1.0]) * input_scale,
            "labor": [1.0, 1.0],
            "electricity": np.asarray([2.0, 1.0]) * output_scale,
            "co2": np.asarray([1.0, 2.0]) * bad_output_scale,
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["energy", "labor"],
        polluting_inputs="energy",
        outputs="electricity",
        bad_outputs="co2",
    )


def _observed_vrs_model(**kwargs) -> ByProductionDirectionalDistanceDEA:
    """Return the earlier observation-scaled VRS package extension."""
    return ByProductionDDF(
        output_direction="observed",
        bad_output_direction="observed",
        intended_returns_to_scale="vrs",
        residual_returns_to_scale="vrs",
        **kwargs,
    )


def test_by_production_ddf_decomposes_two_subtechnologies() -> None:
    result = _observed_vrs_model().fit(_by_production_example())
    summary = result.summary().set_index("dmu_id")

    assert ByProductionDDF is ByProductionDirectionalDistanceDEA
    assert np.isclose(summary.loc["C", "intended_distance"], 1.0)
    assert np.isclose(summary.loc["C", "environmental_distance"], 0.5)
    assert np.isclose(summary.loc["C", "distance"], 0.5)
    assert np.isclose(summary.loc["C", "efficiency"], 2.0 / 3.0)
    assert summary.loc["C", "limiting_subtechnology"] == "residual_generation"
    assert pd.isna(summary.loc["C", "is_efficient"])
    assert not bool(summary.loc["C", "is_directionally_efficient"])

    targets = result.targets_for("C").set_index(["role", "variable"])
    assert np.isclose(targets.loc[("output", "electricity"), "target"], 1.5)
    assert np.isclose(targets.loc[("output", "electricity"), "component_target"], 2.0)
    assert np.isclose(targets.loc[("bad_output", "co2"), "target"], 1.0)
    assert set(result.peers("C")["subtechnology"]) == {
        "intended_production",
        "residual_generation",
    }
    assert result.metadata["score_direction"] == "higher_is_farther"
    assert result.metadata["score_ordering"] == "lower_is_better"


def test_by_production_reports_external_reference_membership_and_appraisal() -> None:
    data = _by_production_example()
    feasible = ByProductionDDF(
        reference=ReferenceSpec(kind="custom", custom_rows=[0])
    ).fit(data)
    c = feasible.summary().set_index("dmu_id").loc["C"]

    assert not bool(c["self_in_reference"])
    assert bool(c["is_within_reference_technology"])
    assert c["membership_status"] == ("certified_by_componentwise_directional_accounts")
    assert feasible.metadata["expanded_spec"]["evaluation_protocol"]["kind"] == (
        "componentwise_mixed_self_and_external_reference_appraisal"
    )

    infeasible = ByProductionDDF(
        reference=ReferenceSpec(kind="custom", custom_rows=[1])
    ).fit(data)
    a = infeasible.summary().set_index("dmu_id").loc["A"]
    assert not bool(a["self_in_reference"])
    assert not bool(a["is_within_reference_technology"])
    assert a["membership_status"] == "outside_reference_technology"
    assert pd.isna(a["is_directionally_efficient"])


def test_by_production_ddf_distinguishes_weak_and_component_efficiency() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "C"],
            "energy": [1.0, 2.0],
            "electricity": [2.0, 1.0],
            "co2": [1.0, 4.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs="energy",
        polluting_inputs="energy",
        outputs="electricity",
        bad_outputs="co2",
    )

    c = _observed_vrs_model().fit(data).summary().set_index("dmu_id").loc["C"]

    assert np.isclose(c["intended_distance"], 1.0)
    assert np.isclose(c["environmental_distance"], 0.0)
    assert np.isclose(c["distance"], 0.0)
    assert bool(c["is_directionally_efficient"])
    assert pd.isna(c["is_efficient"])


def test_by_production_native_efficiency_does_not_claim_strong_efficiency() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "energy": [1.0, 1.0],
            "labor": [1.0, 2.0],
            "electricity": [1.0, 1.0],
            "co2": [1.0, 1.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["energy", "labor"],
        polluting_inputs="energy",
        outputs="electricity",
        bad_outputs="co2",
    )

    b = ByProductionDDF().fit(data).summary().set_index("dmu_id").loc["B"]

    assert bool(b["is_directionally_efficient"])
    assert pd.isna(b["is_efficient"])


def test_by_production_ddf_is_units_invariant_with_observed_directions() -> None:
    baseline = _observed_vrs_model().fit(_by_production_example()).summary()["distance"]
    rescaled = (
        _observed_vrs_model()
        .fit(
            _by_production_example(
                input_scale=100.0,
                output_scale=0.01,
                bad_output_scale=1_000.0,
            )
        )
        .summary()["distance"]
    )

    assert np.allclose(rescaled, baseline)


def test_by_production_ddf_uses_shared_panel_references() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "A"],
            "year": [2020, 2021],
            "energy": [1.0, 1.0],
            "electricity": [1.0, 2.0],
            "co2": [2.0, 1.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        period="year",
        inputs="energy",
        polluting_inputs="energy",
        outputs="electricity",
        bad_outputs="co2",
    )

    current = _observed_vrs_model(reference="contemporaneous").fit(data)
    global_result = _observed_vrs_model(reference="global").fit(data)

    assert np.allclose(current.summary()["distance"], 0.0)
    assert np.isclose(global_result.summary().loc[0, "distance"], 0.5)


def test_by_production_requires_explicit_data_roles_and_directions() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A"],
            "energy": [1.0],
            "electricity": [1.0],
            "co2": [1.0],
        }
    )
    missing_polluting = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs="energy",
        outputs="electricity",
        bad_outputs="co2",
    )
    with pytest.raises(ModelSpecificationError, match="polluting_inputs"):
        ByProductionDDF().fit(missing_polluting)

    with pytest.raises(DataValidationError, match="must also be declared as inputs"):
        DEAData.from_frame(
            frame,
            dmu="dmu",
            inputs="energy",
            polluting_inputs="electricity",
            outputs="electricity",
            bad_outputs="co2",
        )

    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs="energy",
        polluting_inputs="energy",
        outputs="electricity",
        bad_outputs="co2",
    )
    with pytest.raises(ModelSpecificationError, match="positive good-output"):
        ByProductionDDF(output_direction="zeros").fit(data)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"tolerance": np.nan},
        {"tolerance": np.inf},
        {"peer_tolerance": np.nan},
        {"peer_tolerance": np.inf},
    ],
)
def test_by_production_requires_finite_tolerances(kwargs: dict[str, float]) -> None:
    with pytest.raises(ValueError, match="positive and finite"):
        ByProductionDDF(**kwargs)


class _MarginalFailureSolver:
    name = "by_production_marginal_failure_fixture"

    def solve(self, problem):
        return LPSolution(
            status=SolverStatus.LIMIT_REACHED,
            objective=None,
            primal=None,
            message="injected BP-DDF failure",
            iterations=0,
            equality_marginals=(
                None
                if problem.a_eq is None
                else np.zeros(problem.a_eq.shape[0], dtype=np.float64)
            ),
            inequality_marginals=(
                None
                if problem.a_ub is None
                else np.zeros(problem.a_ub.shape[0], dtype=np.float64)
            ),
        )


def test_by_production_nonoptimal_solve_cannot_publish_duals() -> None:
    result = ByProductionDDF(solver=_MarginalFailureSolver()).fit(
        _by_production_example()
    )

    assert result.summary()["score"].isna().all()
    assert result.duals.empty
    assert set(result.diagnostics["message"]) == {
        "injected BP-DDF failure",
    }
