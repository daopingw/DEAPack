from __future__ import annotations

import builtins
import re
import time
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from deapack import (
    ChungFareGrosskopfDDF,
    CommonFactorWeakDisposalDDF,
    DEAData,
    DEAResult,
    ReferenceSpec,
    load_dataset,
)
from deapack.solvers import SciPyHiGHSSolver
from deapack.visualization import (
    EnvironmentalDDFImprovementPlotData,
    PlotNotAvailableError,
    environmental_ddf_improvement_plot_applicable,
    prepare_environmental_ddf_improvement_data,
)
from deapack.visualization.environmental_improvement import (
    _role_direction_matrices,
)


def _environmental_panel_data() -> DEAData:
    frame = load_dataset("environmental_panel")
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs=["energy", "labor"],
        outputs="electricity",
        bad_outputs="co2",
    )


@pytest.fixture(scope="module")
def ddf_result() -> DEAResult:
    return CommonFactorWeakDisposalDDF(
        input_direction="zeros",
        output_direction="observed",
        bad_output_direction="observed",
        reference="contemporaneous",
    ).fit(_environmental_panel_data())


@pytest.fixture(scope="module")
def cfg_result() -> DEAResult:
    return ChungFareGrosskopfDDF(reference="contemporaneous").fit(
        _environmental_panel_data()
    )


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_thaw(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return {_thaw(item) for item in value}
    return value


def _replace_nested(mapping: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    selected = mapping
    for key in path[:-1]:
        selected = selected[key]
    selected[path[-1]] = value


def _metadata_mutation(
    result: DEAResult,
    path: tuple[str, ...],
    value: Any,
) -> DEAResult:
    metadata = _thaw(result.metadata)
    _replace_nested(metadata, path, value)
    return replace(result, metadata=metadata)


def _central_mask(frame: pd.DataFrame) -> pd.Series:
    return frame["dmu_id"].eq("Central") & frame["period"].eq(2020)


def test_common_factor_central_2020_reconstructs_exact_public_plan_without_mutation(
    ddf_result: DEAResult,
) -> None:
    before_summary = ddf_result.summary()
    before_targets = ddf_result.targets.copy(deep=True)
    before_slacks = ddf_result.slacks.copy(deep=True)
    before_diagnostics = ddf_result.diagnostics.copy(deep=True)

    prepared = prepare_environmental_ddf_improvement_data(
        ddf_result,
        dmu_id="Central",
        period=2020,
    )

    assert isinstance(prepared, EnvironmentalDDFImprovementPlotData)
    assert prepared.beta == pytest.approx(0.08381502890173406)
    assert prepared.efficiency == pytest.approx(0.9226666666666666)
    assert prepared.returns_to_scale == "crs"
    assert prepared.reference_kind == "contemporaneous"
    assert prepared.target_status == "certified_slack_completion"
    assert prepared.variable_count == 4
    assert prepared.slack_completed_variable_count == 0
    assert prepared.max_reconstruction_residual <= 1e-12
    assert prepared.variables[["role", "variable"]].apply(tuple, axis=1).tolist() == [
        ("input", "energy"),
        ("input", "labor"),
        ("output", "electricity"),
        ("bad_output", "co2"),
    ]
    assert prepared.variables["observed"].tolist() == pytest.approx(
        [110.0, 55.0, 79.376, 285.12]
    )
    assert prepared.variables["directional_change"].tolist() == pytest.approx(
        [0.0, 0.0, 6.652901734104043, 23.897341040462415]
    )
    assert prepared.variables["slack_completion"].tolist() == pytest.approx(
        [0.0, 0.0, 0.0, 0.0]
    )
    assert prepared.variables["target"].tolist() == pytest.approx(
        [110.0, 55.0, 86.02890173410405, 261.22265895953757]
    )
    assert prepared.variables["slack_allowed"].tolist() == [True, True, True, False]
    assert prepared.variables["variable_label"].tolist()[-1] == "CO2"

    assert_frame_equal(ddf_result.summary(), before_summary)
    assert_frame_equal(ddf_result.targets, before_targets)
    assert_frame_equal(ddf_result.slacks, before_slacks)
    assert_frame_equal(ddf_result.diagnostics, before_diagnostics)


def test_prepared_environmental_ledger_is_detached(ddf_result: DEAResult) -> None:
    prepared = prepare_environmental_ddf_improvement_data(
        ddf_result,
        dmu_id="Central",
        period=2020,
    )
    original = ddf_result.targets.loc[
        _central_mask(ddf_result.targets), "target"
    ].tolist()

    prepared.variables.loc[:, "target"] = -999.0

    assert (
        ddf_result.targets.loc[_central_mask(ddf_result.targets), "target"].tolist()
        == original
    )


def test_exact_cfg_source_preset_uses_the_same_payload_and_renderer_route(
    cfg_result: DEAResult,
) -> None:
    prepared = prepare_environmental_ddf_improvement_data(
        cfg_result,
        dmu_id="Central",
        period=2020,
    )

    assert prepared.beta == pytest.approx(0.08381502890173406)
    assert prepared.variables["target"].tolist() == pytest.approx(
        [110.0, 55.0, 86.02890173410405, 261.22265895953757]
    )
    assert prepared.provenance[-1] == (
        "Equivalent source preset",
        "environmental.ddf.output.chung_fare_grosskopf_1997",
    )
    assert environmental_ddf_improvement_plot_applicable(cfg_result)
    assert "improvement" in {plot.kind for plot in cfg_result.available_plots()}


@pytest.mark.parametrize(
    "method_id",
    [
        "environmental.ddf.legacy",
        "environmental.ddf.strong_disposal",
        "environmental.ddf.weak_disposal.activity_specific",
        "environmental.by_production",
        "environmental.network.ddf",
        "environmental.dynamic.ddf",
    ],
)
def test_noncore_method_identities_cannot_reuse_the_improvement_account(
    ddf_result: DEAResult,
    method_id: str,
) -> None:
    result = _metadata_mutation(ddf_result, ("method_id",), method_id)

    assert not environmental_ddf_improvement_plot_applicable(result)
    with pytest.raises(PlotNotAvailableError, match="only for the core CRS"):
        prepare_environmental_ddf_improvement_data(
            result,
            dmu_id="Central",
            period=2020,
        )


@pytest.mark.parametrize(
    "field",
    ["specialization_id", "method_specialization"],
)
def test_method_specialization_is_not_promoted_to_the_core_route(
    ddf_result: DEAResult,
    field: str,
) -> None:
    result = _metadata_mutation(
        ddf_result,
        (field,),
        "paper_specific_variant",
    )

    with pytest.raises(PlotNotAvailableError, match="specialization"):
        prepare_environmental_ddf_improvement_data(
            result,
            dmu_id="Central",
            period=2020,
        )


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        (("preset_id",), "wrong.source.preset", "source-preset identity"),
        (
            ("expanded_spec", "graph", "kind"),
            "network",
            "joint black-box",
        ),
        (
            ("expanded_spec", "technology", "returns_to_scale"),
            "vrs",
            "CRS common-factor",
        ),
        (
            ("expanded_spec", "technology", "bad_output_treatment"),
            "strong_disposal",
            "CRS common-factor",
        ),
        (
            ("expanded_spec", "performance", "family"),
            "slacks_based_measure",
            "directional performance",
        ),
        (
            ("expanded_spec", "performance", "output_direction", "kind"),
            "ones",
            "direction declarations",
        ),
        (
            ("expanded_spec", "data_roles", "outputs"),
            "generic_outputs",
            "resource, service, and residual roles",
        ),
        (
            ("expanded_spec", "reference", "kind"),
            "global",
            "reference declarations",
        ),
    ],
)
def test_corrupt_expanded_identity_fails_closed(
    cfg_result: DEAResult,
    path: tuple[str, ...],
    value: Any,
    message: str,
) -> None:
    result = _metadata_mutation(cfg_result, path, value)

    with pytest.raises(PlotNotAvailableError, match=message):
        prepare_environmental_ddf_improvement_data(
            result,
            dmu_id="Central",
            period=2020,
        )


def test_cfg_label_without_exact_preset_identity_is_rejected(
    ddf_result: DEAResult,
) -> None:
    metadata = _thaw(ddf_result.metadata)
    metadata["method_id"] = "environmental.ddf.output.chung_fare_grosskopf_1997"
    metadata["preset_id"] = "environmental.ddf.output.not_cfg"
    result = replace(ddf_result, metadata=metadata)

    with pytest.raises(PlotNotAvailableError, match="source-preset identity"):
        prepare_environmental_ddf_improvement_data(
            result,
            dmu_id="Central",
            period=2020,
        )


def test_mixed_reference_discovers_nonnegative_row_and_rejects_negative_row() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "organization": ["Old", "New"],
                "resource": [1.0, 1.0],
                "service": [1.0, 2.0],
                "residual": [2.0, 1.0],
            }
        ),
        dmu="organization",
        inputs="resource",
        outputs="service",
        bad_outputs="residual",
    )
    result = ChungFareGrosskopfDDF(
        reference=ReferenceSpec(kind="custom", custom_rows=[0])
    ).fit(data)

    assert result.metadata["expanded_spec"]["evaluation_protocol"]["kind"] == (
        "mixed_self_and_external_reference_appraisal"
    )
    assert environmental_ddf_improvement_plot_applicable(result)
    assert "improvement" in {plot.kind for plot in result.available_plots()}
    assert prepare_environmental_ddf_improvement_data(
        result,
        dmu_id="Old",
    ).beta == pytest.approx(0.0)
    with pytest.raises(PlotNotAvailableError, match="negative beta"):
        prepare_environmental_ddf_improvement_data(result, dmu_id="New")


def test_positive_external_beta_is_not_plotted_without_membership() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "organization": ["Reference", "Assessed"],
                "resource": [10.0, 5.0],
                "service": [100.0, 1.0],
                "residual": [10.0, 10.0],
            }
        ),
        dmu="organization",
        inputs="resource",
        outputs="service",
        bad_outputs="residual",
    )
    result = ChungFareGrosskopfDDF(
        reference=ReferenceSpec(kind="custom", custom_rows=[0])
    ).fit(data)

    assessed = result.summary().set_index("dmu_id").loc["Assessed"]
    assert assessed["distance"] > 0.0
    assert not bool(assessed["is_within_reference_technology"])
    with pytest.raises(PlotNotAvailableError, match="reference technology"):
        prepare_environmental_ddf_improvement_data(result, dmu_id="Assessed")


@pytest.mark.parametrize(
    ("input_direction", "output_direction", "bad_output_direction", "kind"),
    [
        ("mean", "mean", "mean", "mean"),
        ([0.0], [1.0], [1.0], "custom_global"),
        (
            [[0.0], [0.2], [0.1]],
            [[1.0], [2.0], [1.5]],
            [[1.0], [1.0], [2.0]],
            "custom_by_observation",
        ),
    ],
)
def test_full_family_direction_policies_are_reconstructed_from_public_ledgers(
    input_direction: Any,
    output_direction: Any,
    bad_output_direction: Any,
    kind: str,
) -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C"],
                "resource": [1.0, 1.5, 2.0],
                "service": [2.0, 2.5, 1.0],
                "residual": [1.0, 1.2, 2.0],
            }
        ),
        dmu="dmu",
        inputs="resource",
        outputs="service",
        bad_outputs="residual",
    )
    result = CommonFactorWeakDisposalDDF(
        input_direction=input_direction,
        output_direction=output_direction,
        bad_output_direction=bad_output_direction,
    ).fit(data)

    performance = result.metadata["expanded_spec"]["performance"]
    assert {
        performance[field]["kind"]
        for field in (
            "input_direction",
            "output_direction",
            "bad_output_direction",
        )
    } == {kind}
    assert environmental_ddf_improvement_plot_applicable(result)
    prepared = prepare_environmental_ddf_improvement_data(result, dmu_id="A")
    assert prepared.variable_count == 3
    assert prepared.max_reconstruction_residual <= 1e-6


def test_custom_direction_fingerprint_tamper_is_rejected() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "resource": [1.0, 2.0],
                "service": [2.0, 1.0],
                "residual": [1.0, 2.0],
            }
        ),
        dmu="dmu",
        inputs="resource",
        outputs="service",
        bad_outputs="residual",
    )
    fitted = CommonFactorWeakDisposalDDF(
        input_direction=[0.0],
        output_direction=[1.0],
        bad_output_direction=[1.0],
    ).fit(data)
    result = _metadata_mutation(
        fitted,
        (
            "expanded_spec",
            "performance",
            "output_direction",
            "parameter",
            "sha256",
        ),
        "0" * 64,
    )

    with pytest.raises(PlotNotAvailableError, match="numeric fingerprint"):
        prepare_environmental_ddf_improvement_data(result, dmu_id="A")


def test_complex_direction_requires_complete_public_observation_ledgers() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "resource": [1.0, 2.0],
                "service": [2.0, 1.0],
                "residual": [1.0, 2.0],
            }
        ),
        dmu="dmu",
        inputs="resource",
        outputs="service",
        bad_outputs="residual",
    )
    fitted = CommonFactorWeakDisposalDDF(
        input_direction=[0.0],
        output_direction=[1.0],
        bad_output_direction=[1.0],
    ).fit(data)
    targets = fitted.targets.loc[
        ~(fitted.targets["dmu_id"].eq("B") & fitted.targets["role"].eq("output"))
    ].copy(deep=True)
    result = replace(fitted, targets=targets)

    with pytest.raises(PlotNotAvailableError, match="ledger is incomplete"):
        prepare_environmental_ddf_improvement_data(result, dmu_id="A")


def test_direction_matrix_reconstruction_scales_linearly_with_public_rows() -> None:
    n_observations = 2_000
    summary = pd.DataFrame(
        {
            "dmu_id": [f"D{position:04d}" for position in range(n_observations)],
            "period": [None] * n_observations,
        }
    )
    targets = pd.DataFrame(
        {
            "dmu_id": np.repeat(summary["dmu_id"].to_numpy(), 2),
            "period": [None] * (2 * n_observations),
            "role": ["output"] * (2 * n_observations),
            "variable": np.tile(["service_a", "service_b"], n_observations),
            "observed": np.arange(2 * n_observations, dtype=float) + 1.0,
            "direction": np.tile([1.0, 2.0], n_observations),
        }
    )

    started = time.perf_counter()
    observed, directions = _role_direction_matrices(
        summary=summary,
        targets=targets,
        role="output",
        variables=("service_a", "service_b"),
    )
    elapsed = time.perf_counter() - started

    assert observed.shape == (n_observations, 2)
    assert directions.shape == (n_observations, 2)
    assert directions[0].tolist() == [1.0, 2.0]
    assert directions[-1].tolist() == [1.0, 2.0]
    assert elapsed < 3.0


def test_coherent_target_forgery_cannot_override_declared_direction_policy(
    ddf_result: DEAResult,
) -> None:
    targets = ddf_result.targets.copy(deep=True)
    mask = _central_mask(targets) & targets["variable"].eq("electricity")
    beta = float(
        ddf_result.summary().loc[_central_mask(ddf_result.summary()), "score"].iloc[0]
    )
    observed = float(targets.loc[mask, "observed"].iloc[0])
    targets.loc[mask, "direction"] = 1.0
    targets.loc[mask, "directional_change"] = beta
    targets.loc[mask, "target"] = observed + beta
    result = replace(ddf_result, targets=targets)

    with pytest.raises(PlotNotAvailableError, match="fitted direction policy"):
        prepare_environmental_ddf_improvement_data(
            result,
            dmu_id="Central",
            period=2020,
        )


def test_coherent_all_zero_direction_forgery_is_rejected(
    ddf_result: DEAResult,
) -> None:
    targets = ddf_result.targets.copy(deep=True)
    selected = _central_mask(targets)
    directional_roles = selected & targets["role"].isin(["output", "bad_output"])
    targets.loc[directional_roles, "observed"] = 0.0
    targets.loc[directional_roles, "target"] = 0.0
    targets.loc[selected, "direction"] = 0.0
    targets.loc[selected, "directional_change"] = 0.0
    result = replace(ddf_result, targets=targets)

    with pytest.raises(PlotNotAvailableError, match="positive direction component"):
        prepare_environmental_ddf_improvement_data(
            result,
            dmu_id="Central",
            period=2020,
        )


@pytest.mark.parametrize(
    "path",
    [
        ("compatibility_alias",),
        ("expanded_spec", "technology", "compatibility_alias"),
    ],
)
def test_legacy_compatibility_alias_cannot_enter_exact_family_route(
    ddf_result: DEAResult,
    path: tuple[str, ...],
) -> None:
    result = _metadata_mutation(ddf_result, path, "weak")

    with pytest.raises(PlotNotAvailableError, match="compatibility alias"):
        prepare_environmental_ddf_improvement_data(
            result,
            dmu_id="Central",
            period=2020,
        )


def test_summary_compatibility_alias_is_rejected(ddf_result: DEAResult) -> None:
    summary = ddf_result.summary()
    summary.loc[_central_mask(summary), "compatibility_alias"] = "weak"
    result = replace(ddf_result, summary_frame=summary)

    with pytest.raises(PlotNotAvailableError, match="compatibility alias"):
        prepare_environmental_ddf_improvement_data(
            result,
            dmu_id="Central",
            period=2020,
        )


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("solver_status", "failed", "optimal primary"),
        ("score_valid", False, "defined valid beta"),
        ("score_status", "unavailable", "defined valid beta"),
        ("completion_solver_status", "failed", "slack-completion"),
        ("completion_valid", False, "slack-completion"),
        ("completion_status", "unavailable", "slack-completion"),
        ("target_valid", False, "completed targets"),
        ("target_status", "uncertified", "completed targets"),
    ],
)
def test_summary_release_claims_are_all_required(
    ddf_result: DEAResult,
    column: str,
    value: Any,
    message: str,
) -> None:
    summary = ddf_result.summary()
    summary.loc[_central_mask(summary), column] = value
    result = replace(ddf_result, summary_frame=summary)

    with pytest.raises(PlotNotAvailableError, match=message):
        prepare_environmental_ddf_improvement_data(
            result,
            dmu_id="Central",
            period=2020,
        )


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("max_slack", np.inf),
        ("max_slack", -0.1),
        ("max_scaled_slack", np.nan),
        ("max_scaled_slack", -0.1),
    ],
)
def test_summary_aggregate_slack_accounts_must_be_finite_and_nonnegative(
    ddf_result: DEAResult,
    column: str,
    value: float,
) -> None:
    summary = ddf_result.summary()
    summary.loc[_central_mask(summary), column] = value
    result = replace(ddf_result, summary_frame=summary)

    with pytest.raises(PlotNotAvailableError, match="aggregate slack accounts"):
        prepare_environmental_ddf_improvement_data(
            result,
            dmu_id="Central",
            period=2020,
        )


def test_negative_beta_is_never_drawn_as_an_improvement(ddf_result: DEAResult) -> None:
    summary = ddf_result.summary()
    mask = _central_mask(summary)
    summary.loc[mask, ["score", "distance"]] = -0.01
    summary.loc[mask, "efficiency"] = 1.0 / 0.99
    result = replace(ddf_result, summary_frame=summary)

    with pytest.raises(PlotNotAvailableError, match="negative beta"):
        prepare_environmental_ddf_improvement_data(
            result,
            dmu_id="Central",
            period=2020,
        )


@pytest.mark.parametrize(
    "certificate",
    [
        "lp_postsolve_certified",
        "postsolve_certified",
        "economic_postsolve_certified",
        "raw_economic_postsolve_certified",
        "published_output_account_certified",
    ],
)
@pytest.mark.parametrize("phase", [1, 2])
def test_both_phases_require_every_output_certificate(
    ddf_result: DEAResult,
    certificate: str,
    phase: int,
) -> None:
    diagnostics = ddf_result.diagnostics.copy(deep=True)
    mask = _central_mask(diagnostics) & diagnostics["phase"].eq(phase)
    diagnostics.loc[mask, certificate] = False
    result = replace(ddf_result, diagnostics=diagnostics)

    with pytest.raises(PlotNotAvailableError, match="both phases"):
        prepare_environmental_ddf_improvement_data(
            result,
            dmu_id="Central",
            period=2020,
        )


def test_duplicate_phase_certificate_is_rejected(ddf_result: DEAResult) -> None:
    diagnostics = ddf_result.diagnostics.copy(deep=True)
    duplicate = diagnostics.loc[_central_mask(diagnostics) & diagnostics["phase"].eq(1)]
    result = replace(
        ddf_result,
        diagnostics=pd.concat([diagnostics, duplicate], ignore_index=True),
    )

    with pytest.raises(PlotNotAvailableError, match="one phase-one and one phase-two"):
        prepare_environmental_ddf_improvement_data(
            result,
            dmu_id="Central",
            period=2020,
        )


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("direction", -1.0, "directions and declared moves"),
        ("directional_change", -1.0, "directions and declared moves"),
        ("directional_change", 1.0, "does not reconstruct"),
        ("target", 999.0, "does not reconstruct"),
        ("target", np.inf, "must be finite"),
        ("direction", np.nan, "must be finite"),
    ],
)
def test_corrupt_target_account_is_rejected(
    ddf_result: DEAResult,
    column: str,
    value: float,
    message: str,
) -> None:
    targets = ddf_result.targets.copy(deep=True)
    mask = _central_mask(targets) & targets["variable"].eq("electricity")
    targets.loc[mask, column] = value
    result = replace(ddf_result, targets=targets)

    with pytest.raises(PlotNotAvailableError, match=message):
        prepare_environmental_ddf_improvement_data(
            result,
            dmu_id="Central",
            period=2020,
        )


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("slack", -1.0, "must be nonnegative"),
        ("slack", 1.0, "does not reconstruct"),
        ("slack", np.inf, "must be finite"),
        ("scaled_slack", np.nan, "must be finite"),
    ],
)
def test_corrupt_slack_completion_is_rejected(
    ddf_result: DEAResult,
    column: str,
    value: float,
    message: str,
) -> None:
    slacks = ddf_result.slacks.copy(deep=True)
    mask = _central_mask(slacks) & slacks["variable"].eq("electricity")
    slacks.loc[mask, column] = value
    result = replace(ddf_result, slacks=slacks)

    with pytest.raises(PlotNotAvailableError, match=message):
        prepare_environmental_ddf_improvement_data(
            result,
            dmu_id="Central",
            period=2020,
        )


def test_linked_slack_and_target_tamper_fails_the_aggregate_ledger(
    ddf_result: DEAResult,
) -> None:
    targets = ddf_result.targets.copy(deep=True)
    target_mask = _central_mask(targets) & targets["variable"].eq("electricity")
    targets.loc[target_mask, "target"] += 1.0
    slacks = ddf_result.slacks.copy(deep=True)
    slack_mask = _central_mask(slacks) & slacks["variable"].eq("electricity")
    slacks.loc[slack_mask, "slack"] = 1.0
    slacks.loc[slack_mask, "scaled_slack"] = 0.01
    result = replace(ddf_result, targets=targets, slacks=slacks)

    with pytest.raises(PlotNotAvailableError, match="aggregate slack ledger"):
        prepare_environmental_ddf_improvement_data(
            result,
            dmu_id="Central",
            period=2020,
        )


@pytest.mark.parametrize("table_name", ["targets", "slacks"])
def test_duplicate_public_variable_row_is_rejected(
    ddf_result: DEAResult,
    table_name: str,
) -> None:
    table = getattr(ddf_result, table_name).copy(deep=True)
    duplicate = table.loc[_central_mask(table) & table["variable"].eq("electricity")]
    corrupted = pd.concat([table, duplicate], ignore_index=True)
    result = replace(ddf_result, **{table_name: corrupted})

    with pytest.raises(PlotNotAvailableError, match="do not match"):
        prepare_environmental_ddf_improvement_data(
            result,
            dmu_id="Central",
            period=2020,
        )


def test_bad_output_cannot_acquire_a_slack_row_or_permission(
    ddf_result: DEAResult,
) -> None:
    targets = ddf_result.targets.copy(deep=True)
    target_mask = _central_mask(targets) & targets["role"].eq("bad_output")
    targets.loc[target_mask, "slack_allowed"] = True
    result = replace(ddf_result, targets=targets)

    with pytest.raises(PlotNotAvailableError, match="slack permissions"):
        prepare_environmental_ddf_improvement_data(
            result,
            dmu_id="Central",
            period=2020,
        )


def test_role_and_metadata_variable_sets_must_match(ddf_result: DEAResult) -> None:
    result = _metadata_mutation(
        ddf_result,
        ("expanded_spec", "data_roles", "variables", "outputs"),
        ["renamed_service"],
    )

    with pytest.raises(PlotNotAvailableError, match="targets do not match"):
        prepare_environmental_ddf_improvement_data(
            result,
            dmu_id="Central",
            period=2020,
        )


def test_peer_and_dual_release_are_not_plot_prerequisites(
    ddf_result: DEAResult,
) -> None:
    summary = ddf_result.summary()
    mask = _central_mask(summary)
    summary.loc[mask, ["peer_valid", "dual_valid"]] = False
    summary.loc[mask, "peer_status"] = "withheld_for_reporting_threshold"
    summary.loc[mask, "dual_status"] = "withheld"
    diagnostics = ddf_result.diagnostics.copy(deep=True)
    diagnostic_mask = _central_mask(diagnostics)
    diagnostics.loc[diagnostic_mask, "published_peer_account_certified"] = False
    diagnostics.loc[diagnostic_mask, "published_dual_account_certified"] = False
    result = replace(
        ddf_result,
        summary_frame=summary,
        diagnostics=diagnostics,
        intensities=pd.DataFrame(),
        duals=pd.DataFrame(),
    )

    prepared = prepare_environmental_ddf_improvement_data(
        result,
        dmu_id="Central",
        period=2020,
    )

    assert prepared.beta == pytest.approx(0.08381502890173406)
    assert prepared.variable_count == 4


def test_zero_observed_coordinate_is_safe_without_a_ratio_axis(
    ddf_result: DEAResult,
) -> None:
    targets = ddf_result.targets.copy(deep=True)
    target_mask = _central_mask(targets) & targets["variable"].eq("energy")
    targets.loc[
        target_mask,
        ["observed", "target", "direction", "directional_change"],
    ] = 0.0
    slacks = ddf_result.slacks.copy(deep=True)
    slack_mask = _central_mask(slacks) & slacks["variable"].eq("energy")
    slacks.loc[slack_mask, ["slack", "scaled_slack"]] = 0.0
    result = replace(ddf_result, targets=targets, slacks=slacks)

    prepared = prepare_environmental_ddf_improvement_data(
        result,
        dmu_id="Central",
        period=2020,
    )

    energy = prepared.variables.set_index("variable").loc["energy"]
    assert energy["observed"] == 0.0
    assert energy["target"] == 0.0
    assert not any("proportional" in column for column in prepared.variables.columns)


def test_zero_service_and_residual_directions_render_as_fixed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    result = CommonFactorWeakDisposalDDF(
        input_direction="observed",
        output_direction="observed",
        bad_output_direction="observed",
    ).fit(
        DEAData.from_frame(
            pd.DataFrame(
                {
                    "dmu": ["A", "B"],
                    "resource": [1.0, 2.0],
                    "service": [0.0, 0.0],
                    "residual": [1.0, 0.0],
                }
            ),
            dmu="dmu",
            inputs="resource",
            outputs="service",
            bad_outputs="residual",
        )
    )
    prepared = prepare_environmental_ddf_improvement_data(result, dmu_id="B")
    assert prepared.variables.set_index("role").loc["output", "direction"] == 0.0
    assert prepared.variables.set_index("role").loc["bad_output", "direction"] == 0.0

    monkeypatch.setenv("MPL_IGNORE_SYSTEM_FONTS", "1")
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "matplotlib"))
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    pyplot = pytest.importorskip("matplotlib.pyplot")
    figure = result.plot(kind="improvement", dmu_id="B")
    text = " ".join(item.get_text() for axis in figure.axes for item in axis.texts)

    assert "Fixed desirable services" in text
    assert "Fixed undesirable residuals" in text
    assert "Service held fixed\n(no declared change)" in text
    assert "Residual held fixed\n(no declared change)" in text
    assert "service expansion\n+0" not in text.casefold()
    assert "residual reduction\n\N{MINUS SIGN}0" not in text.casefold()
    pyplot.close(figure)


def test_discovery_advertises_only_a_reconstructable_plan(
    ddf_result: DEAResult,
) -> None:
    assert environmental_ddf_improvement_plot_applicable(ddf_result)
    assert "improvement" in {plot.kind for plot in ddf_result.available_plots()}

    summary = ddf_result.summary()
    summary["target_valid"] = False
    result = replace(ddf_result, summary_frame=summary)

    assert not environmental_ddf_improvement_plot_applicable(result)
    assert "improvement" not in {plot.kind for plot in result.available_plots()}


def test_discovery_prefilters_large_all_negative_summary_before_deep_preparation(
    cfg_result: DEAResult,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import deapack.visualization.environmental_improvement as module

    template = cfg_result.summary().iloc[[0]].copy(deep=True)
    summary = pd.concat([template] * 2_000, ignore_index=True)
    summary["dmu_id"] = [f"D{position:04d}" for position in range(len(summary))]
    summary["period"] = None
    summary["score"] = -0.1
    summary["distance"] = -0.1
    summary["efficiency"] = np.nan
    result = replace(cfg_result, summary_frame=summary)

    def _deep_preparation_is_forbidden(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise AssertionError("negative rows must be removed by the vector prefilter")

    monkeypatch.setattr(
        module,
        "prepare_environmental_ddf_improvement_data",
        _deep_preparation_is_forbidden,
    )

    assert not module.environmental_ddf_improvement_plot_applicable(result)


def test_environmental_ddf_discovery_is_matplotlib_lazy(
    ddf_result: DEAResult,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ordinary_import = builtins.__import__

    def _reject_matplotlib_import(
        name: str,
        globals: Any = None,
        locals: Any = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> Any:
        if name == "matplotlib" or name.startswith("matplotlib."):
            raise AssertionError("plot discovery must not import Matplotlib")
        return ordinary_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _reject_matplotlib_import)

    assert environmental_ddf_improvement_plot_applicable(ddf_result)
    assert "improvement" in {plot.kind for plot in ddf_result.available_plots()}


def test_environmental_ddf_renderer_uses_managerial_original_unit_ledger(
    ddf_result: DEAResult,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("MPL_IGNORE_SYSTEM_FONTS", "1")
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "matplotlib"))
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    pyplot = pytest.importorskip("matplotlib.pyplot")

    def _show_is_forbidden(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise AssertionError("plot() must not call pyplot.show()")

    monkeypatch.setattr(pyplot, "show", _show_is_forbidden)
    figure = ddf_result.plot(
        kind="improvement",
        dmu_id="Central",
        period=2020,
    )
    text = " ".join(
        item.get_text()
        for item in [
            *figure.texts,
            *(text for axis in figure.axes for text in axis.texts),
        ]
    )

    assert figure._suptitle.get_text() == (
        "Environmental directional improvement for Central · period 2020"
    )
    assert len(figure.axes) == 2
    assert all(not axis.axison for axis in figure.axes)
    for phrase in (
        "Certified common directional programme",
        "β = 0.083815",
        "Fixed resources",
        "Declared service expansion\n+6.652902",
        "Declared residual reduction\n\N{MINUS SIGN}23.897341",
        "Slack completion",
        "weak common-factor disposal",
        "no common quantity axis",
        "not an SBM score",
        "one selected feasible benchmark",
        "not a unique plan",
        "engineering implementation",
        "causal explanation",
        "cost conclusion",
        "CO2",
    ):
        assert phrase in text
    assert re.search(r"\bpeer\b", text.casefold()) is None
    assert re.search(r"\bdual\b", text.casefold()) is None
    pyplot.close(figure)


class _CountingSolver:
    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        self.calls += 1
        return self._delegate.solve(problem)


def test_discovery_preparation_and_rendering_cannot_add_solver_calls(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    solver = _CountingSolver()
    result = CommonFactorWeakDisposalDDF(
        compute_slacks=True,
        solver=solver,
    ).fit(
        DEAData.from_frame(
            pd.DataFrame(
                {
                    "dmu": ["A", "B"],
                    "resource": [1.0, 1.0],
                    "service": [2.0, 1.0],
                    "residual": [1.0, 2.0],
                }
            ),
            dmu="dmu",
            inputs="resource",
            outputs="service",
            bad_outputs="residual",
        )
    )
    calls_after_fit = solver.calls
    assert calls_after_fit == result.metadata["solver_calls"]

    assert environmental_ddf_improvement_plot_applicable(result)
    prepare_environmental_ddf_improvement_data(result, dmu_id="A")
    monkeypatch.setenv("MPL_IGNORE_SYSTEM_FONTS", "1")
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "matplotlib"))
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    pyplot = pytest.importorskip("matplotlib.pyplot")
    figure = result.plot(kind="improvement", dmu_id="A")

    assert solver.calls == calls_after_fit
    assert result.metadata["additional_solver_calls"] == 0
    pyplot.close(figure)
