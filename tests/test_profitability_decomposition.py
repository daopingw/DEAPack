from __future__ import annotations

import json
import math
from dataclasses import asdict

import numpy as np
import pandas as pd
import pytest

import deapack
from deapack import (
    DEAData,
    GDFProfitabilityDecomposition,
    PriceData,
    ProfitabilityDecomposition,
    ReferenceSpec,
    SolverOptions,
    SolverStatus,
    list_methods,
    method_info,
)
from deapack.solvers import LPSolution, SciPyHiGHSSolver

_DMUS = ["1", "2", "3", "4", "5"]
_METHOD_ID = "analysis.allocative_decomposition.profitability_gdf.zofio_prieto_2006"
_COMPONENTS = {
    "profitability_maximizing_activity",
    "crs_gdf",
    "vrs_gdf",
}
_GDF_COMPONENTS = {"crs_gdf", "vrs_gdf"}
_SCORE_ATOL = 5e-7


def _zofio_prieto_data() -> tuple[DEAData, PriceData]:
    frame = pd.DataFrame(
        {
            "dmu": _DMUS,
            "x1": [5.0, 2.0, 4.0, 4.0, 7.0],
            "x2": [3.0, 4.0, 2.0, 8.0, 9.0],
            "y1": [7.0, 10.0, 8.0, 5.0, 3.0],
            "y2": [4.0, 8.0, 10.0, 4.0, 6.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs=["y1", "y2"],
    )
    prices = PriceData.common(
        input_prices={"x1": 2.0, "x2": 1.0},
        output_prices={"y1": 3.0, "y2": 2.0},
    )
    return data, prices


class _FailingPhaseTwoSolver:
    name = "profitability_decomposition_phase_two_failure_fixture"

    def __init__(self) -> None:
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        if problem.name.endswith(":gdf-slacks"):
            return LPSolution(
                status=SolverStatus.LIMIT_REACHED,
                objective=None,
                primal=None,
                message="injected GDF phase-two failure",
                iterations=0,
            )
        return self._delegate.solve(problem)


class _AlwaysFailingSolver:
    name = "profitability_decomposition_phase_one_failure_fixture"

    def solve(self, problem):
        return LPSolution(
            status=SolverStatus.LIMIT_REACHED,
            objective=None,
            primal=None,
            message="injected GDF phase-one failure",
            iterations=0,
        )


def test_five_dmu_oracle_reconstructs_both_profitability_identities() -> None:
    data, prices = _zofio_prieto_data()
    result = GDFProfitabilityDecomposition(alpha=0.5).fit(data, prices)
    summary = result.summary().set_index("dmu_id").loc[_DMUS]

    expected_profitability = np.array([116 / 299, 1.0, 88 / 115, 1 / 4, 84 / 529])
    expected_crs = np.array([7 / 11, 1.0, 1.0, 1 / 4, 6 / 23])
    expected_vrs = np.array([(13 - 2 * math.sqrt(30)) / 3, 1.0, 1.0, 1 / 4, 9 / 25])
    expected_scale = expected_crs / expected_vrs
    expected_allocative = expected_profitability / expected_crs

    np.testing.assert_allclose(
        summary["profitability_efficiency"],
        expected_profitability,
        atol=_SCORE_ATOL,
        rtol=0,
    )
    np.testing.assert_allclose(
        summary["crs_technical_efficiency"],
        expected_crs,
        atol=_SCORE_ATOL,
        rtol=0,
    )
    np.testing.assert_allclose(
        summary["vrs_technical_efficiency"],
        expected_vrs,
        atol=_SCORE_ATOL,
        rtol=0,
    )
    np.testing.assert_allclose(
        summary["scale_efficiency"],
        expected_scale,
        atol=1e-6,
        rtol=0,
    )
    np.testing.assert_allclose(
        summary["allocative_efficiency"],
        expected_allocative,
        atol=1e-6,
        rtol=0,
    )
    np.testing.assert_allclose(summary["score"], expected_allocative)
    np.testing.assert_allclose(summary["efficiency"], expected_allocative)
    assert summary["distance"].isna().all()

    np.testing.assert_allclose(
        summary["profitability_efficiency"],
        summary["crs_technical_efficiency"] * summary["allocative_efficiency"],
        atol=1e-12,
        rtol=0,
    )
    np.testing.assert_allclose(
        summary["profitability_efficiency"],
        summary["vrs_technical_efficiency"]
        * summary["scale_efficiency"]
        * summary["allocative_efficiency"],
        atol=1e-12,
        rtol=0,
    )
    np.testing.assert_allclose(
        summary["crs_reconstruction_residual"],
        0.0,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        summary["vrs_reconstruction_residual"],
        0.0,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        summary["crs_vrs_ordering_residual"],
        0.0,
        atol=1e-12,
    )
    assert summary["decomposition_defined"].all()
    assert summary["is_efficient"].isna().all()


def test_component_labels_keep_value_crs_and_vrs_plans_separate() -> None:
    data, prices = _zofio_prieto_data()
    result = GDFProfitabilityDecomposition(alpha=0.5).fit(data, prices)

    assert set(result.targets["component"]) == _COMPONENTS
    assert set(result.intensities["component"]) == _COMPONENTS
    assert set(result.slacks["component"]) == _GDF_COMPONENTS
    assert set(result.diagnostics["component"]) == {
        "profitability_efficiency",
        "crs_gdf",
        "vrs_gdf",
        "decomposition_identity",
    }
    target_counts = result.targets.groupby("component").size().to_dict()
    assert target_counts == {
        "crs_gdf": 20,
        "profitability_maximizing_activity": 20,
        "vrs_gdf": 20,
    }

    value_targets = result.targets.query(
        "component == 'profitability_maximizing_activity'"
    )
    assert set(value_targets["target_kind"]) == {"profitability_maximizing_activity"}
    for component in _GDF_COMPONENTS:
        component_intensities = result.intensities.loc[
            result.intensities["component"] == component
        ]
        assert set(component_intensities["stage"]) == {
            "phase_one_reference_activity",
            "slack_completed_target",
        }
    value_intensities = result.intensities.query(
        "component == 'profitability_maximizing_activity'"
    )
    assert value_intensities["stage"].isna().all()

    dmu_one_vrs_targets = result.targets.query(
        "dmu_id == '1' and component == 'vrs_gdf'"
    )
    output_two = dmu_one_vrs_targets.query(
        "role == 'output' and variable == 'y2'"
    ).iloc[0]
    assert output_two["path_target"] != pytest.approx(
        output_two["phase_one_reference_activity"]
    )
    assert output_two["target"] == pytest.approx(
        output_two["phase_one_reference_activity"]
    )


def test_alpha_changes_the_vrs_scale_account_but_not_pe_crs_or_ae() -> None:
    data, prices = _zofio_prieto_data()
    input_contract = GDFProfitabilityDecomposition(alpha=0.0).fit(data, prices)
    output_contract = GDFProfitabilityDecomposition(alpha=1.0).fit(data, prices)
    input_summary = input_contract.summary().set_index("dmu_id").loc[_DMUS]
    output_summary = output_contract.summary().set_index("dmu_id").loc[_DMUS]

    expected_input_vrs = np.array([3 / 4, 1.0, 1.0, 1 / 2, 3 / 8])
    expected_output_vrs = np.array([7 / 9, 1.0, 1.0, 1 / 2, 3 / 5])
    np.testing.assert_allclose(
        input_summary["vrs_technical_efficiency"],
        expected_input_vrs,
        atol=_SCORE_ATOL,
        rtol=0,
    )
    np.testing.assert_allclose(
        output_summary["vrs_technical_efficiency"],
        expected_output_vrs,
        atol=_SCORE_ATOL,
        rtol=0,
    )

    for column in (
        "profitability_efficiency",
        "crs_technical_efficiency",
        "allocative_efficiency",
    ):
        np.testing.assert_allclose(
            input_summary[column],
            output_summary[column],
            atol=_SCORE_ATOL,
            rtol=0,
        )
    assert not np.allclose(
        input_summary["vrs_technical_efficiency"],
        output_summary["vrs_technical_efficiency"],
    )
    assert not np.allclose(
        input_summary["scale_efficiency"],
        output_summary["scale_efficiency"],
    )
    np.testing.assert_allclose(
        input_summary["profitability_efficiency"],
        input_summary["vrs_technical_efficiency"]
        * input_summary["scale_efficiency"]
        * input_summary["allocative_efficiency"],
        atol=1e-12,
        rtol=0,
    )
    np.testing.assert_allclose(
        output_summary["profitability_efficiency"],
        output_summary["vrs_technical_efficiency"]
        * output_summary["scale_efficiency"]
        * output_summary["allocative_efficiency"],
        atol=1e-12,
        rtol=0,
    )


def test_alias_catalog_and_metadata_are_public_and_json_safe() -> None:
    data, prices = _zofio_prieto_data()
    result = ProfitabilityDecomposition(alpha=0.5).fit(data, prices)
    catalog_entry = method_info(_METHOD_ID)

    assert ProfitabilityDecomposition is GDFProfitabilityDecomposition
    assert deapack.ProfitabilityDecomposition is deapack.GDFProfitabilityDecomposition
    assert _METHOD_ID in {entry.method_id for entry in list_methods()}
    assert catalog_entry.kind == "operator"
    assert catalog_entry.api_symbols == (
        "GDFProfitabilityDecomposition",
        "ProfitabilityDecomposition",
    )
    json.dumps(asdict(catalog_entry), allow_nan=False)
    json.dumps(dict(result.metadata), allow_nan=False)

    assert result.metadata["method_id"] == _METHOD_ID
    assert result.metadata["native_score"] == "allocative_efficiency"
    assert result.metadata["alpha_interpretation"] == ("performance_contract_balance")
    assert result.metadata["target_components"] == (
        "profitability_maximizing_activity",
        "crs_gdf",
        "vrs_gdf",
    )
    evaluation_protocol = result.metadata["expanded_spec"]["evaluation_protocol"]
    assert evaluation_protocol["components"] == (
        "economic.profitability.return_to_dollar",
        "static.generalized_distance.chavas_cox",
    )
    assert evaluation_protocol["component_configurations"] == (
        {
            "method_id": "economic.profitability.return_to_dollar",
            "role": "profitability_benchmark",
        },
        {
            "method_id": "static.generalized_distance.chavas_cox",
            "returns_to_scale": "crs",
            "role": "crs_gdf",
        },
        {
            "method_id": "static.generalized_distance.chavas_cox",
            "returns_to_scale": "vrs",
            "role": "vrs_gdf",
        },
    )
    assert result.metadata["identities"] == (
        "PE = TE_CRS_GDF * AE_GDF",
        "PE = TE_VRS_GDF * SE_GDF * AE_GDF",
        "SE_GDF = TE_CRS_GDF / TE_VRS_GDF",
    )
    assert result.metadata["duals_available"] is False
    assert result.duals.empty


def test_external_reference_retains_unclipped_components_and_nullable_flags() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["reference", "evaluated"],
                "input": [2.0, 1.0],
                "output": [2.0, 5.0],
            }
        ),
        dmu="dmu",
        inputs="input",
        outputs="output",
    )
    prices = PriceData.common(
        input_prices={"input": 1.0},
        output_prices={"output": 1.0},
    )
    result = GDFProfitabilityDecomposition(
        alpha=0.5,
        reference=ReferenceSpec("custom", custom_rows=[0]),
    ).fit(data, prices)
    evaluated = result.summary().set_index("dmu_id").loc["evaluated"]

    assert evaluated["profitability_efficiency"] == pytest.approx(5.0)
    assert evaluated["crs_technical_efficiency"] == pytest.approx(5.0)
    assert evaluated["vrs_technical_efficiency"] == pytest.approx(6.25)
    assert evaluated["scale_efficiency"] == pytest.approx(0.8)
    assert evaluated["allocative_efficiency"] == pytest.approx(1.0)
    assert bool(evaluated["decomposition_defined"])
    assert evaluated["score_status"] == "defined_external_comparison"
    assert not bool(evaluated["self_in_reference"])
    assert not bool(evaluated["crs_is_within_reference_technology"])
    assert not bool(evaluated["vrs_is_within_reference_technology"])
    assert pd.isna(evaluated["is_allocatively_efficient"])
    assert pd.isna(evaluated["is_efficient"])
    assert evaluated["profitability_efficiency"] == pytest.approx(
        evaluated["vrs_technical_efficiency"]
        * evaluated["scale_efficiency"]
        * evaluated["allocative_efficiency"]
    )
    evaluated_peers = result.peers("evaluated")
    assert set(evaluated_peers["component"]) == _COMPONENTS
    assert set(evaluated_peers["reference_dmu_id"]) == {"reference"}


@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        ({"alpha": True}, TypeError),
        ({"alpha": -0.01}, ValueError),
        ({"alpha": 1.01}, ValueError),
        ({"tolerance": 0.0}, ValueError),
        ({"tolerance": math.inf}, ValueError),
        ({"peer_tolerance": math.nan}, ValueError),
        ({"search_tolerance": -1.0}, ValueError),
        ({"max_search_iterations": 0}, ValueError),
        ({"max_search_iterations": 1.5}, TypeError),
        ({"max_bracket_expansions": 0}, ValueError),
    ],
)
def test_numerical_parameters_fail_closed(
    kwargs: dict[str, object],
    error: type[Exception],
) -> None:
    with pytest.raises(error):
        GDFProfitabilityDecomposition(**kwargs)


def test_solver_and_solver_options_cannot_both_be_supplied() -> None:
    with pytest.raises(ValueError, match="solver or solver_options"):
        GDFProfitabilityDecomposition(
            solver=SciPyHiGHSSolver(),
            solver_options=SolverOptions(),
        )


def test_phase_two_failure_preserves_scores_and_decomposition() -> None:
    data, prices = _zofio_prieto_data()
    expected = GDFProfitabilityDecomposition(
        alpha=0.5,
        compute_slacks=False,
    ).fit(data, prices)
    result = GDFProfitabilityDecomposition(
        alpha=0.5,
        solver=_FailingPhaseTwoSolver(),
    ).fit(data, prices)
    expected_summary = expected.summary().set_index("dmu_id").loc[_DMUS]
    summary = result.summary().set_index("dmu_id").loc[_DMUS]

    for column in (
        "profitability_efficiency",
        "crs_technical_efficiency",
        "vrs_technical_efficiency",
        "scale_efficiency",
        "allocative_efficiency",
    ):
        np.testing.assert_allclose(
            summary[column],
            expected_summary[column],
            atol=_SCORE_ATOL,
            rtol=0,
        )
    assert summary["decomposition_defined"].all()
    assert set(summary["solver_status"]) == {"optimal"}
    assert set(summary["crs_target_status"]) == {"failed:limit_reached"}
    assert set(summary["vrs_target_status"]) == {"failed:limit_reached"}

    gdf_targets = result.targets.query("component in @_GDF_COMPONENTS")
    assert gdf_targets["target"].isna().all()
    gdf_slacks = result.slacks.query("component in @_GDF_COMPONENTS")
    assert gdf_slacks["slack"].isna().all()
    gdf_intensities = result.intensities.query("component in @_GDF_COMPONENTS")
    assert set(gdf_intensities["stage"]) == {"phase_one_reference_activity"}
    phase_two = result.diagnostics.query("component in @_GDF_COMPONENTS and phase == 2")
    assert set(phase_two["solver_status"]) == {"limit_reached"}


def test_phase_one_failure_makes_the_composition_undefined() -> None:
    data, prices = _zofio_prieto_data()
    result = GDFProfitabilityDecomposition(
        alpha=0.5,
        solver=_AlwaysFailingSolver(),
    ).fit(data, prices)
    summary = result.summary().set_index("dmu_id").loc[_DMUS]

    assert summary["profitability_efficiency"].notna().all()
    assert summary["crs_technical_efficiency"].isna().all()
    assert summary["vrs_technical_efficiency"].isna().all()
    assert summary["scale_efficiency"].isna().all()
    assert summary["allocative_efficiency"].isna().all()
    assert summary["score"].isna().all()
    assert not summary["decomposition_defined"].any()
    assert set(summary["solver_status"]) == {"limit_reached"}
    assert set(summary["score_status"]) == {"undefined_crs_gdf_component"}
    assert summary["is_allocatively_efficient"].isna().all()
    assert summary["is_efficient"].isna().all()
    assert set(result.targets["component"]) == {"profitability_maximizing_activity"}
    assert set(result.intensities["component"]) == {"profitability_maximizing_activity"}
    assert result.slacks.empty
