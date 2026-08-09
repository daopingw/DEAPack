from __future__ import annotations

import subprocess
import sys
import textwrap
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from deapack import (
    DEAResult,
    FareGrosskopfNetworkRadialDEA,
    LinkSpec,
    NetworkData,
    NetworkSBM,
    NetworkSpec,
    ProcessSpec,
    TwoStageSeriesSpec,
    load_dataset,
)
from deapack.visualization import (
    PlotNotAvailableError,
    prepare_process_attribution_data,
    process_attribution_plot_applicable,
)

_PROCESS_IDS = ("stage_1", "stage_2", "stage_3")
_WEIGHTS = {"stage_1": 0.4, "stage_2": 0.2, "stage_3": 0.4}


def _spec() -> NetworkSpec:
    return NetworkSpec(
        processes=(
            ProcessSpec(
                "stage_1",
                inputs="intake_hours",
                outputs="verified_requests",
            ),
            ProcessSpec(
                "stage_2",
                inputs=("verified_requests", "resolution_hours"),
                outputs=("same_day_resolutions", "scheduled_cases"),
            ),
            ProcessSpec(
                "stage_3",
                inputs=("scheduled_cases", "delivery_hours"),
                outputs="completed_services",
            ),
        ),
        links=(
            LinkSpec(
                "handoff_1_2",
                source="stage_1",
                target="stage_2",
                variables="verified_requests",
            ),
            LinkSpec(
                "handoff_2_3",
                source="stage_2",
                target="stage_3",
                variables="scheduled_cases",
            ),
        ),
    )


def _data(
    *,
    frame: pd.DataFrame | None = None,
    period: str | None = None,
) -> NetworkData:
    source = load_dataset("three_process_service_chain") if frame is None else frame
    return NetworkData.from_frame(
        source,
        dmu="unit",
        period=period,
        spec=_spec(),
    )


def _fit(
    *,
    link_control: str = "free",
    weights: Mapping[str, float] = _WEIGHTS,
    frame: pd.DataFrame | None = None,
    period: str | None = None,
) -> DEAResult:
    return NetworkSBM(
        orientation="input",
        returns_to_scale="vrs",
        link_control=link_control,
        division_weights=weights,
    ).fit(_data(frame=frame, period=period))


@pytest.fixture(scope="module")
def network_result() -> DEAResult:
    return _fit()


@pytest.fixture(scope="module")
def fixed_network_result() -> DEAResult:
    return _fit(link_control="fixed")


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_thaw(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return {_thaw(item) for item in value}
    return value


def _replace_metadata(result: DEAResult, metadata: dict[str, Any]) -> DEAResult:
    return replace(result, metadata=metadata)


def test_process_discovery_is_backend_independent() -> None:
    command = textwrap.dedent(
        """
        import sys
        from deapack import (
            LinkSpec, NetworkData, NetworkSBM, NetworkSpec, ProcessSpec,
            load_dataset,
        )

        spec = NetworkSpec(
            processes=(
                ProcessSpec(
                    'stage_1', inputs='intake_hours', outputs='verified_requests'
                ),
                ProcessSpec(
                    'stage_2',
                    inputs=('verified_requests', 'resolution_hours'),
                    outputs=('same_day_resolutions', 'scheduled_cases'),
                ),
                ProcessSpec(
                    'stage_3',
                    inputs=('scheduled_cases', 'delivery_hours'),
                    outputs='completed_services',
                ),
            ),
            links=(
                LinkSpec(
                    'handoff_1_2', source='stage_1', target='stage_2',
                    variables='verified_requests',
                ),
                LinkSpec(
                    'handoff_2_3', source='stage_2', target='stage_3',
                    variables='scheduled_cases',
                ),
            ),
        )
        data = NetworkData.from_frame(
            load_dataset('three_process_service_chain'), dmu='unit', spec=spec,
        )
        result = NetworkSBM(
            orientation='input', returns_to_scale='vrs', link_control='free',
            division_weights={'stage_1': .4, 'stage_2': .2, 'stage_3': .4},
        ).fit(data)
        assert [plot.kind for plot in result.available_plots()] == [
            'performance', 'process',
        ]
        assert not any(
            name == 'matplotlib' or name.startswith('matplotlib.')
            for name in sys.modules
        )
        """
    )
    subprocess.run([sys.executable, "-c", command], check=True)


def test_project_process_and_handoff_accounts_are_reconstructed(
    network_result: DEAResult,
) -> None:
    before_summary = network_result.summary()
    before_components = network_result.components.copy(deep=True)
    before_links = network_result.links.copy(deep=True)
    before_diagnostics = network_result.diagnostics.copy(deep=True)

    prepared = prepare_process_attribution_data(network_result, dmu_id="balanced")

    assert prepared.system_efficiency == pytest.approx(
        prepared.processes["weighted_contribution"].sum()
    )
    assert prepared.system_gap == pytest.approx(1.0 - prepared.system_efficiency)
    assert prepared.process_count == 3
    assert prepared.link_variable_count == 2
    assert prepared.orientation == "input"
    assert prepared.returns_to_scale == "vrs"
    assert prepared.link_policy == "free"
    assert prepared.processes["process_id"].tolist() == list(_PROCESS_IDS)
    assert prepared.processes["efficiency"].between(0.0, 1.0).all()
    assert prepared.processes["declared_weight"].tolist() == [0.4, 0.2, 0.4]
    assert prepared.processes["weighted_contribution"].sum() == pytest.approx(
        prepared.system_efficiency
    )
    assert prepared.processes["attributed_gap"].sum() == pytest.approx(
        prepared.system_gap
    )
    assert prepared.links["link_id"].tolist() == [
        "handoff_1_2",
        "handoff_2_3",
    ]
    assert prepared.links["observed"].tolist() == pytest.approx([8.0, 6.0])
    assert (prepared.links["target"] > 0.0).all()
    assert prepared.max_link_continuity_residual <= 2e-15

    assert_frame_equal(network_result.summary(), before_summary)
    assert_frame_equal(network_result.components, before_components)
    assert_frame_equal(network_result.links, before_links)
    assert_frame_equal(network_result.diagnostics, before_diagnostics)


def test_prepared_frames_are_detached(network_result: DEAResult) -> None:
    prepared = prepare_process_attribution_data(network_result, dmu_id="balanced")
    original_process = network_result.components.loc[
        network_result.components["dmu_id"].eq("balanced")
        & network_result.components["process_id"].eq("stage_1"),
        "efficiency",
    ].iloc[0]
    original_target = network_result.links.loc[
        network_result.links["dmu_id"].eq("balanced")
        & network_result.links["link_id"].eq("handoff_1_2"),
        "target",
    ].iloc[0]

    prepared.processes.loc[0, "efficiency"] = -999.0
    prepared.links.loc[0, "target"] = -999.0

    assert (
        network_result.components.loc[
            network_result.components["dmu_id"].eq("balanced")
            & network_result.components["process_id"].eq("stage_1"),
            "efficiency",
        ].iloc[0]
        == original_process
    )
    assert (
        network_result.links.loc[
            network_result.links["dmu_id"].eq("balanced")
            & network_result.links["link_id"].eq("handoff_1_2"),
            "target",
        ].iloc[0]
        == original_target
    )


def test_process_plot_argument_contract(network_result: DEAResult) -> None:
    with pytest.raises(PlotNotAvailableError, match="requires dmu_id"):
        network_result.plot(kind="process")
    with pytest.raises(PlotNotAvailableError, match="metric and variable"):
        network_result.plot(kind="process", dmu_id="balanced", metric="efficiency")
    with pytest.raises(PlotNotAvailableError, match="metric and variable"):
        network_result.plot(kind="process", dmu_id="balanced", variable="link_1_2")
    with pytest.raises(PlotNotAvailableError, match="view='auto'"):
        network_result.plot(kind="process", dmu_id="balanced", view="points")
    with pytest.raises(PlotNotAvailableError, match="unknown"):
        prepare_process_attribution_data(network_result, dmu_id="missing")


def test_system_only_network_result_is_a_different_reporting_institution() -> None:
    frame = load_dataset("two_stage_public_service")
    data = NetworkData.from_frame(
        frame,
        dmu="unit",
        spec=TwoStageSeriesSpec(
            inputs=("staff_hours", "platform_cost_units"),
            intermediates=("screened_cases", "verified_value"),
            outputs=("timely_closures", "public_value"),
            stage_names=("screening", "outcome"),
            link_id="service_handoff",
        ),
    )
    result = FareGrosskopfNetworkRadialDEA().fit(data)

    assert "process" not in {plot.kind for plot in result.available_plots()}
    with pytest.raises(PlotNotAvailableError, match="system-only, relational"):
        prepare_process_attribution_data(result, dmu_id="balanced")


@pytest.mark.parametrize("orientation", ["output", "non-oriented"])
def test_other_network_sbm_orientation_is_not_silently_translated(
    network_result: DEAResult,
    orientation: str,
) -> None:
    metadata = _thaw(network_result.metadata)
    metadata["orientation"] = orientation
    metadata["expanded_spec"]["performance"]["orientation"] = orientation.replace(
        "-", "_"
    )
    summary = network_result.summary()
    summary["orientation"] = orientation
    result = replace(
        network_result,
        summary_frame=summary,
        metadata=metadata,
    )

    assert not process_attribution_plot_applicable(result)
    with pytest.raises(PlotNotAvailableError, match="input-oriented"):
        prepare_process_attribution_data(result, dmu_id="balanced")


def test_accountable_link_specialization_is_not_the_base_process_account(
    network_result: DEAResult,
) -> None:
    metadata = _thaw(network_result.metadata)
    metadata["specialization_id"] = (
        "network.sbm.tone_tsutsui_2009.accountable_input_link"
    )
    result = _replace_metadata(network_result, metadata)

    assert not process_attribution_plot_applicable(result)
    with pytest.raises(PlotNotAvailableError, match="accountable-link"):
        prepare_process_attribution_data(result, dmu_id="balanced")


def test_fixed_handoffs_preserve_observed_commitments(
    fixed_network_result: DEAResult,
) -> None:
    prepared = prepare_process_attribution_data(fixed_network_result, dmu_id="balanced")

    assert prepared.link_policy == "fixed"
    assert prepared.system_efficiency == pytest.approx(
        prepared.processes["weighted_contribution"].sum()
    )
    assert prepared.processes["efficiency"].between(0.0, 1.0).all()
    assert prepared.links["target"].tolist() == pytest.approx(
        prepared.links["observed"].tolist()
    )


def test_link_checks_are_stable_to_large_and_small_units() -> None:
    frame = load_dataset("three_process_service_chain").copy(deep=True)
    frame["verified_requests"] *= 1e12
    frame["scheduled_cases"] *= 1e-12
    result = _fit(frame=frame)

    prepared = prepare_process_attribution_data(result, dmu_id="balanced")

    assert prepared.system_efficiency == pytest.approx(
        _fit().summary().set_index("dmu_id").loc["balanced", "efficiency"]
    )
    assert prepared.links.loc[0, "observed"] == pytest.approx(8.0e12)
    assert prepared.links.loc[1, "observed"] == pytest.approx(6.0e-12)
    assert (
        prepared.max_link_continuity_residual
        <= 1e-12 * (prepared.links.loc[0, "target"])
    )


def test_connected_cycle_does_not_require_a_dag() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["balanced", "scale_2", "C"],
            "p1_x": [2.0, 1.0, 1.5],
            "p1_y": [1.0, 2.0, 1.5],
            "forward": [1.0, 2.0, 1.5],
            "p2_x": [2.0, 1.0, 1.5],
            "p2_y": [1.0, 2.0, 1.5],
            "return": [1.0, 2.0, 1.5],
        }
    )
    spec = NetworkSpec(
        processes=(
            ProcessSpec(
                "p1",
                inputs=("p1_x", "return"),
                outputs=("p1_y", "forward"),
            ),
            ProcessSpec(
                "p2",
                inputs=("p2_x", "forward"),
                outputs=("p2_y", "return"),
            ),
        ),
        links=(
            LinkSpec("forward_link", source="p1", target="p2", variables="forward"),
            LinkSpec("return_link", source="p2", target="p1", variables="return"),
        ),
    )
    result = NetworkSBM(
        orientation="input",
        returns_to_scale="vrs",
        link_control="free",
    ).fit(NetworkData.from_frame(frame, dmu="dmu", spec=spec))

    prepared = prepare_process_attribution_data(result, dmu_id="balanced")

    assert prepared.processes["process_id"].tolist() == ["p1", "p2"]
    assert prepared.links[["source_process_id", "recipient_process_id"]].to_records(
        index=False
    ).tolist() == [("p1", "p2"), ("p2", "p1")]


def test_zero_weight_process_is_explicitly_unscored() -> None:
    result = _fit(weights={"stage_1": 0.5, "stage_2": 0.0, "stage_3": 0.5})
    prepared = prepare_process_attribution_data(result, dmu_id="balanced")

    assert not prepared.all_process_weights_positive
    assert prepared.processes["scored"].tolist() == [True, False, True]
    assert prepared.processes.loc[1, "weighted_contribution"] == 0.0
    assert prepared.processes["weighted_contribution"].sum() == pytest.approx(
        prepared.system_efficiency
    )


def test_panel_account_requires_an_explicit_period() -> None:
    frame = load_dataset("three_process_service_chain")
    panel = pd.concat(
        [frame.assign(period=1), frame.assign(period=2)],
        ignore_index=True,
    )
    result = _fit(frame=panel, period="period")

    with pytest.raises(PlotNotAvailableError, match="requires period"):
        prepare_process_attribution_data(result, dmu_id="balanced")
    prepared = prepare_process_attribution_data(result, dmu_id="balanced", period=1)
    assert prepared.period == 1


@pytest.mark.parametrize(
    ("column", "forged"),
    [
        ("score_valid", False),
        ("score_valid", 1),
        ("score_valid", "True"),
        ("score_status", "undefined"),
        ("score", 0.99),
        ("efficiency", 0.99),
        ("input_account", 0.99),
        ("distance", 0.0),
        ("max_accountable_link_balance_residual", 0.0),
    ],
)
def test_summary_forgery_fails_closed(
    network_result: DEAResult,
    column: str,
    forged: object,
) -> None:
    summary = network_result.summary()
    summary[column] = summary[column].astype(object)
    summary.loc[summary["dmu_id"].eq("balanced"), column] = forged
    result = replace(network_result, summary_frame=summary)

    with pytest.raises(PlotNotAvailableError):
        prepare_process_attribution_data(result, dmu_id="balanced")


@pytest.mark.parametrize(
    ("column", "forged"),
    [
        ("postsolve_certified", False),
        ("postsolve_certified", "True"),
        ("economic_postsolve_certified", False),
        ("certification_reason", "forged"),
        ("economic_certification_reason", "forged"),
        ("objective_residual", 0.01),
        ("duality_gap", np.nan),
        ("max_economic_violation", 0.01),
    ],
)
def test_certificate_forgery_fails_closed(
    network_result: DEAResult,
    column: str,
    forged: object,
) -> None:
    diagnostics = network_result.diagnostics.copy(deep=True)
    diagnostics[column] = diagnostics[column].astype(object)
    diagnostics.loc[diagnostics["dmu_id"].eq("balanced"), column] = forged
    result = replace(network_result, diagnostics=diagnostics)

    with pytest.raises(PlotNotAvailableError, match="certified"):
        prepare_process_attribution_data(result, dmu_id="balanced")


def test_primary_certificate_must_be_unique(network_result: DEAResult) -> None:
    rows = network_result.diagnostics.copy(deep=True)
    duplicate = pd.concat(
        [rows, rows.loc[rows["dmu_id"].eq("balanced")]],
        ignore_index=True,
    )
    missing = rows.loc[~rows["dmu_id"].eq("balanced")].copy(deep=True)

    for diagnostics in (duplicate, missing):
        result = replace(network_result, diagnostics=diagnostics)
        with pytest.raises(PlotNotAvailableError, match="one primary"):
            prepare_process_attribution_data(result, dmu_id="balanced")


@pytest.mark.parametrize("forgery", ["missing", "duplicate", "extra"])
def test_process_component_identity_must_be_complete(
    network_result: DEAResult,
    forgery: str,
) -> None:
    components = network_result.components.copy(deep=True)
    selected = components["dmu_id"].eq("balanced") & components["process_id"].eq(
        "stage_2"
    )
    if forgery == "missing":
        components = components.loc[~selected].copy(deep=True)
    elif forgery == "duplicate":
        components = pd.concat(
            [components, components.loc[selected]],
            ignore_index=True,
        )
    else:
        rogue = components.loc[selected].copy(deep=True)
        rogue["component_id"] = "rogue"
        rogue["process_id"] = "rogue"
        components = pd.concat([components, rogue], ignore_index=True)
    result = replace(network_result, components=components)

    with pytest.raises(PlotNotAvailableError):
        prepare_process_attribution_data(result, dmu_id="balanced")


@pytest.mark.parametrize(
    ("column", "forged"),
    [
        ("efficiency", 0.99),
        ("input_account", 0.99),
        ("input_inefficiency", 0.99),
        ("division_weight", 0.5),
        ("effective_reconstruction_weight", 0.5),
    ],
)
def test_process_account_forgery_fails_closed(
    network_result: DEAResult,
    column: str,
    forged: object,
) -> None:
    components = network_result.components.copy(deep=True)
    selected = components["dmu_id"].eq("balanced") & components["process_id"].eq(
        "stage_2"
    )
    components.loc[selected, column] = forged
    result = replace(network_result, components=components)

    with pytest.raises(PlotNotAvailableError):
        prepare_process_attribution_data(result, dmu_id="balanced")


def test_process_rows_are_returned_in_fitted_order(network_result: DEAResult) -> None:
    components = network_result.components.sample(frac=1.0, random_state=7)
    result = replace(network_result, components=components)

    prepared = prepare_process_attribution_data(result, dmu_id="balanced")

    assert prepared.processes["process_id"].tolist() == list(_PROCESS_IDS)


@pytest.mark.parametrize("forgery", ["missing", "duplicate", "extra"])
def test_link_variable_identity_must_be_complete(
    network_result: DEAResult,
    forgery: str,
) -> None:
    links = network_result.links.copy(deep=True)
    selected = links["dmu_id"].eq("balanced") & links["link_id"].eq("handoff_1_2")
    if forgery == "missing":
        links = links.loc[~selected].copy(deep=True)
    elif forgery == "duplicate":
        links = pd.concat([links, links.loc[selected]], ignore_index=True)
    else:
        rogue = links.loc[selected].copy(deep=True)
        rogue["variable"] = "rogue"
        links = pd.concat([links, rogue], ignore_index=True)
    result = replace(network_result, links=links)

    with pytest.raises(PlotNotAvailableError):
        prepare_process_attribution_data(result, dmu_id="balanced")


@pytest.mark.parametrize(
    ("column", "forged"),
    [
        ("recipient_process_id", "stage_3"),
        ("link_kind", "fixed"),
        ("target", 0.99),
        ("source_target", 0.99),
        ("observed", np.inf),
        ("fixed_observation_residual", 0.0),
        ("included_in_objective", True),
        ("responsibility_role", "link_input"),
        ("selection_status", "forged"),
    ],
)
def test_link_account_forgery_fails_closed(
    network_result: DEAResult,
    column: str,
    forged: object,
) -> None:
    links = network_result.links.copy(deep=True)
    selected = links["dmu_id"].eq("balanced") & links["link_id"].eq("handoff_1_2")
    links.loc[selected, column] = forged
    result = replace(network_result, links=links)

    with pytest.raises(PlotNotAvailableError):
        prepare_process_attribution_data(result, dmu_id="balanced")


def test_fixed_residuals_are_reconstructed(
    fixed_network_result: DEAResult,
) -> None:
    links = fixed_network_result.links.copy(deep=True)
    selected = links["dmu_id"].eq("balanced") & links["link_id"].eq("handoff_1_2")
    links.loc[selected, "source_fixed_observation_residual"] = 0.1
    result = replace(fixed_network_result, links=links)

    with pytest.raises(PlotNotAvailableError, match="fixed handoff"):
        prepare_process_attribution_data(result, dmu_id="balanced")


def test_metadata_topology_and_governance_are_independent_gates(
    network_result: DEAResult,
) -> None:
    cases: list[dict[str, Any]] = []

    missing_tolerance = _thaw(network_result.metadata)
    del missing_tolerance["tolerance"]
    cases.append(missing_tolerance)

    near_method = _thaw(network_result.metadata)
    near_method["method_id"] = "network.sbm.tone_tsutsui_2009_variant"
    cases.append(near_method)

    topology = _thaw(network_result.metadata)
    topology["expanded_spec"]["graph"]["link_topology"]["handoff_1_2"]["recipient"] = (
        "stage_3"
    )
    cases.append(topology)

    weights = _thaw(network_result.metadata)
    weights["division_weights"]["stage_2"] = 0.3
    cases.append(weights)

    expanded_weights = _thaw(network_result.metadata)
    expanded_weights["expanded_spec"]["valuation"]["division_weights"]["stage_2"] = 0.3
    cases.append(expanded_weights)

    objective = _thaw(network_result.metadata)
    objective["base_objective_includes_link_slacks"] = True
    cases.append(objective)

    for metadata in cases:
        result = _replace_metadata(network_result, metadata)
        assert not process_attribution_plot_applicable(result)
        with pytest.raises(PlotNotAvailableError):
            prepare_process_attribution_data(result, dmu_id="balanced")


def test_one_corrupted_dmu_does_not_hide_another_valid_account(
    network_result: DEAResult,
) -> None:
    summary = network_result.summary()
    summary.loc[summary["dmu_id"].eq("balanced"), "score_valid"] = False
    result = replace(network_result, summary_frame=summary)

    assert process_attribution_plot_applicable(result)
    assert [plot.kind for plot in result.available_plots()] == [
        "performance",
        "process",
    ]
    with pytest.raises(PlotNotAvailableError):
        prepare_process_attribution_data(result, dmu_id="balanced")
    prepared = prepare_process_attribution_data(result, dmu_id="scale_2")
    assert prepared.dmu_id == "scale_2"


def test_process_roster_and_link_account_limits_fail_closed(
    network_result: DEAResult,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import deapack.visualization.network_process as process_module

    monkeypatch.setattr(process_module, "MAX_PROCESS_ACCOUNTS", 2)
    assert not process_attribution_plot_applicable(network_result)
    with pytest.raises(PlotNotAvailableError, match="limited to 2 process"):
        prepare_process_attribution_data(network_result, dmu_id="balanced")

    monkeypatch.setattr(process_module, "MAX_PROCESS_ACCOUNTS", 16)
    monkeypatch.setattr(process_module, "MAX_LINK_VARIABLE_ACCOUNTS", 1)
    assert not process_attribution_plot_applicable(network_result)
    with pytest.raises(PlotNotAvailableError, match="limited to 1 link-variable"):
        prepare_process_attribution_data(network_result, dmu_id="balanced")


def test_matplotlib_process_account_renders_without_showing_or_global_mutation(
    network_result: DEAResult,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("MPL_IGNORE_SYSTEM_FONTS", "1")
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "matplotlib"))
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    pyplot = pytest.importorskip("matplotlib.pyplot")
    figure_type = pytest.importorskip("matplotlib.figure").Figure
    before_rc = {
        key: matplotlib.rcParams[key]
        for key in ("axes.edgecolor", "font.size", "grid.color")
    }
    before_components = network_result.components.copy(deep=True)
    before_links = network_result.links.copy(deep=True)

    def _show_is_forbidden(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise AssertionError("plot() must not call pyplot.show()")

    monkeypatch.setattr(pyplot, "show", _show_is_forbidden)
    figure = network_result.plot(kind="process", dmu_id="balanced")

    assert isinstance(figure, figure_type)
    assert len(figure.axes) == 3
    assert figure._suptitle.get_text() == (
        "Certified connected-organization account for balanced"
    )
    assert "joint plan" in figure.axes[0].get_title(loc="left")
    assert "system score" in figure.axes[1].get_title(loc="left")
    assert "internal handoffs" in figure.axes[2].get_title(loc="left")
    assert any(
        "not independent departmental scores or causal contributions" in text.get_text()
        for text in figure.texts
    )
    assert any(
        "not unique management recommendations" in text.get_text()
        for text in figure.texts
    )
    assert {
        key: matplotlib.rcParams[key]
        for key in ("axes.edgecolor", "font.size", "grid.color")
    } == before_rc
    assert_frame_equal(network_result.components, before_components)
    assert_frame_equal(network_result.links, before_links)
    pyplot.close(figure)
