from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from deapack import (
    DEAData,
    MetafrontierDEA,
    RadialDEA,
    dataset_info,
    load_dataset,
)
from deapack.visualization import (
    PlotNotAvailableError,
    metafrontier_plot_applicable,
    prepare_metafrontier_data,
)
from deapack.visualization.performance import prepare_performance_data


def _metafrontier_result(*, panel: bool = False):
    frame = load_dataset("metafrontier_groups")
    roles = dataset_info("metafrontier_groups").roles
    period = None
    if panel:
        first = frame.assign(period=2020)
        second = frame.assign(period=2021)
        frame = pd.concat([first, second], ignore_index=True)
        period = "period"
    data = DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        period=period,
        group=roles["group"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )
    return MetafrontierDEA(
        orientation="output",
        returns_to_scale="vrs",
        compute_slacks=False,
    ).fit(data)


def _scalar_radial_result():
    frame = load_dataset("frontier_1x1")
    roles = dataset_info("frontier_1x1").roles
    data = DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )
    return RadialDEA().fit(data)


def _tiny_positive_metafrontier_result():
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["evaluated", "group_best", "meta_best", "meta_peer"],
                "group": ["restricted", "restricted", "broader", "broader"],
                "resource": [1.0, 1.0, 1.0, 1.0],
                "service": [1.0, 1.0e7, 2.0e7, 1.5e7],
            }
        ),
        dmu="dmu",
        group="group",
        inputs="resource",
        outputs="service",
    )
    return MetafrontierDEA(
        orientation="output",
        returns_to_scale="vrs",
        compute_slacks=False,
    ).fit(data)


def _tiny_positive_ratio_result():
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["evaluated", "group_peer", "meta_best", "meta_peer"],
                "group": ["restricted", "restricted", "broader", "broader"],
                "resource": [1.0, 1.0, 1.0, 1.0],
                "service": [1.0, 1.0, 1.0e7, 5.0e6],
            }
        ),
        dmu="dmu",
        group="group",
        inputs="resource",
        outputs="service",
    )
    return MetafrontierDEA(
        orientation="output",
        returns_to_scale="vrs",
        compute_slacks=False,
    ).fit(data)


def _load_matplotlib_for_test(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> tuple[object, object]:
    monkeypatch.setenv("MPL_IGNORE_SYSTEM_FONTS", "1")
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "matplotlib"))
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    pyplot = pytest.importorskip("matplotlib.pyplot")
    return matplotlib, pyplot


def test_metafrontier_discovery_is_backend_independent() -> None:
    command = """
import sys
from deapack import DEAData, MetafrontierDEA, dataset_info, load_dataset
frame = load_dataset('metafrontier_groups')
roles = dataset_info('metafrontier_groups').roles
data = DEAData.from_frame(
    frame,
    dmu=roles['dmu'],
    group=roles['group'],
    inputs=roles['inputs'],
    outputs=roles['outputs'],
)
result = MetafrontierDEA(compute_slacks=False).fit(data)
assert [plot.kind for plot in result.available_plots()] == [
    'performance', 'metafrontier',
]
assert not any(
    name == 'matplotlib' or name.startswith('matplotlib.')
    for name in sys.modules
)
"""
    subprocess.run([sys.executable, "-c", command], check=True)


def test_exact_metafrontier_account_is_prepared_without_mutating_result() -> None:
    result = _metafrontier_result()
    before = result.summary()

    prepared = prepare_metafrontier_data(result)

    assert prepared.period_label == "Cross-section"
    assert prepared.orientation == "output"
    assert prepared.returns_to_scale == "vrs"
    assert prepared.observation_count == 6
    assert prepared.group_count == 2
    assert prepared.omitted_observation_count == 0
    assert prepared.observations["dmu_id"].tolist() == list("ABCDEF")
    assert prepared.observations["group_efficiency"].tolist() == pytest.approx(
        [1.0, 1.0, 0.5, 1.0, 1.0, 1.0]
    )
    assert prepared.observations["metafrontier_efficiency"].tolist() == (
        pytest.approx([0.5, 0.5, 0.25, 1.0, 1.0, 1.0])
    )
    assert prepared.observations["metatechnology_ratio"].tolist() == pytest.approx(
        [0.5, 0.5, 0.5, 1.0, 1.0, 1.0]
    )
    prepared.observations.loc[0, "group_efficiency"] = -999.0
    assert result.summary().loc[0, "group_efficiency"] == 1.0
    assert_frame_equal(result.summary(), before)


def test_tiny_positive_certified_account_remains_plot_applicable() -> None:
    result = _tiny_positive_metafrontier_result()

    assert metafrontier_plot_applicable(result)
    row = (
        prepare_metafrontier_data(result)
        .observations.set_index("dmu_id")
        .loc["evaluated"]
    )
    assert row["group_efficiency"] == pytest.approx(1.0e-7)
    assert row["metafrontier_efficiency"] == pytest.approx(5.0e-8)
    assert row["metatechnology_ratio"] == pytest.approx(0.5)


def test_generic_performance_views_use_component_specific_validity_gates() -> None:
    result = _metafrontier_result()
    selected = result.summary_frame["dmu_id"].eq("A")
    result.summary_frame.loc[selected, "group_score_valid"] = False
    result.summary_frame.loc[selected, "decomposition_certified"] = False
    result.summary_frame.loc[selected, "solver_status"] = "certificate_failure"

    group = prepare_performance_data(result, metric="group_efficiency")
    meta = prepare_performance_data(result, metric="metafrontier_efficiency")
    ratio = prepare_performance_data(result, metric="metatechnology_ratio")

    assert group.measure.validity_column == "group_score_valid"
    assert "A" not in group.facets[0].frame["dmu_id"].tolist()
    assert meta.measure.validity_column == "metafrontier_score_valid"
    assert "A" in meta.facets[0].frame["dmu_id"].tolist()
    assert ratio.measure.validity_column == "decomposition_certified"
    assert "A" not in ratio.facets[0].frame["dmu_id"].tolist()


def test_plot_gate_rejects_a_forged_zero_for_a_tiny_positive_mtr() -> None:
    result = _tiny_positive_ratio_result()
    summary_row = result.summary_frame["dmu_id"].eq("evaluated")
    result.summary_frame.loc[
        summary_row,
        ["score", "metatechnology_ratio", "technology_gap_ratio"],
    ] = 0.0
    component_row = result.components["dmu_id"].eq("evaluated") & result.components[
        "component"
    ].eq("metatechnology_ratio")
    result.components.loc[component_row, "value"] = 0.0

    assert not metafrontier_plot_applicable(result)
    with pytest.raises(PlotNotAvailableError, match="does not reconstruct"):
        prepare_metafrontier_data(result)


def test_metafrontier_plot_argument_and_family_boundary() -> None:
    result = _metafrontier_result()
    with pytest.raises(PlotNotAvailableError, match="metric, dmu_id, and variable"):
        result.plot(kind="metafrontier", metric="metatechnology_ratio")
    with pytest.raises(PlotNotAvailableError, match="metric, dmu_id, and variable"):
        result.plot(kind="metafrontier", dmu_id="A")
    with pytest.raises(PlotNotAvailableError, match="view='auto'"):
        result.plot(kind="metafrontier", view="points")
    with pytest.raises(PlotNotAvailableError, match="core radial"):
        prepare_metafrontier_data(_scalar_radial_result())


def test_multiperiod_metafrontier_requires_an_explicit_period() -> None:
    result = _metafrontier_result(panel=True)

    assert metafrontier_plot_applicable(result)
    with pytest.raises(PlotNotAvailableError, match="requires period"):
        prepare_metafrontier_data(result)
    prepared = prepare_metafrontier_data(result, period=2021)
    assert prepared.period == 2021
    assert prepared.period_label == "Period 2021"
    assert prepared.observation_count == 6
    with pytest.raises(PlotNotAvailableError, match="unknown metafrontier period"):
        prepare_metafrontier_data(result, period=1999)


def test_period_rows_must_match_the_fitted_time_information_policy() -> None:
    cross_section = _metafrontier_result()
    cross_section.summary_frame["period"] = 2020
    assert not metafrontier_plot_applicable(cross_section)
    with pytest.raises(PlotNotAvailableError, match="cross-section"):
        prepare_metafrontier_data(cross_section, period=2020)

    panel = _metafrontier_result(panel=True)
    panel.summary_frame["period"] = None
    assert not metafrontier_plot_applicable(panel)
    with pytest.raises(PlotNotAvailableError, match="panel"):
        prepare_metafrontier_data(panel)


def test_uncertified_rows_are_omitted_but_forged_certificates_fail_closed() -> None:
    result = _metafrontier_result()
    result.summary_frame.loc[0, "decomposition_certified"] = False
    result.summary_frame.loc[0, "solver_status"] = "certificate_failure"

    prepared = prepare_metafrontier_data(result)
    assert prepared.omitted_observation_count == 1
    assert prepared.observations["dmu_id"].tolist() == list("BCDEF")

    forged = _metafrontier_result()
    forged.summary_frame.loc[0, "metafrontier_efficiency"] = 0.75
    assert not metafrontier_plot_applicable(forged)
    with pytest.raises(PlotNotAvailableError, match="does not reconstruct"):
        prepare_metafrontier_data(forged)


def test_claimed_certificate_requires_both_component_accounts() -> None:
    result = _metafrontier_result()
    result.summary_frame.loc[0, "metafrontier_score_valid"] = False

    assert not metafrontier_plot_applicable(result)
    with pytest.raises(PlotNotAvailableError, match="complete component evidence"):
        prepare_metafrontier_data(result)


def test_claimed_certificate_cannot_forge_a_zero_ratio_denominator() -> None:
    result = _metafrontier_result()
    for column in (
        "group_efficiency",
        "metafrontier_efficiency",
        "metatechnology_ratio",
        "raw_metatechnology_ratio",
        "group_radial_factor",
        "metafrontier_radial_factor",
        "nesting_violation",
        "ratio_bound_violation",
        "reconstruction_residual",
    ):
        result.summary_frame.loc[0, column] = 0.0

    assert not metafrontier_plot_applicable(result)
    with pytest.raises(PlotNotAvailableError, match="does not reconstruct"):
        prepare_metafrontier_data(result)


def test_ratio_is_recomputed_when_group_efficiency_is_near_tolerance() -> None:
    result = MetafrontierDEA(
        orientation="input",
        returns_to_scale="vrs",
        compute_slacks=False,
    ).fit(
        DEAData.from_frame(
            load_dataset("metafrontier_groups"),
            dmu="dmu",
            group="technology_group",
            inputs="resource",
            outputs="service",
        )
    )
    forged = {
        "group_efficiency": 2.0e-7,
        "metafrontier_efficiency": 0.0,
        "metatechnology_ratio": 1.0,
        "raw_metatechnology_ratio": 1.0,
        "group_radial_factor": 2.0e-7,
        "metafrontier_radial_factor": 1.0e-12,
        "nesting_violation": 0.0,
        "ratio_bound_violation": 0.0,
        "reconstruction_residual": 2.0e-7,
    }
    for column, value in forged.items():
        result.summary_frame.loc[0, column] = value

    assert not metafrontier_plot_applicable(result)
    with pytest.raises(PlotNotAvailableError, match="does not reconstruct"):
        prepare_metafrontier_data(result)


def test_summary_must_match_the_fitted_component_ledger() -> None:
    result = _metafrontier_result()
    selected = result.components["dmu_id"].eq("A") & result.components["component"].eq(
        "group_efficiency"
    )
    result.components.loc[selected, "value"] = 0.8

    assert not metafrontier_plot_applicable(result)
    with pytest.raises(PlotNotAvailableError, match="component ledger"):
        prepare_metafrontier_data(result)

    regrouped = _metafrontier_result()
    groups = regrouped.summary_frame["group"].astype(str).tolist()
    groups[0] = "group_2"
    regrouped.summary_frame["group"] = groups
    assert not metafrontier_plot_applicable(regrouped)
    with pytest.raises(PlotNotAvailableError, match="group labels disagree"):
        prepare_metafrontier_data(regrouped)


def test_summary_must_retain_both_primary_component_certificates() -> None:
    result = _metafrontier_result()
    selected = (
        result.diagnostics["dmu_id"].eq("A")
        & result.diagnostics["phase"].eq(1)
        & result.diagnostics["benchmark_level"].eq("metafrontier")
    )
    result.diagnostics.loc[selected, "economic_postsolve_certified"] = False

    assert not metafrontier_plot_applicable(result)
    with pytest.raises(PlotNotAvailableError, match="primary diagnostics"):
        prepare_metafrontier_data(result)


def test_metafrontier_long_roster_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import deapack.visualization.metafrontier as metafrontier_module

    result = _metafrontier_result()
    monkeypatch.setattr(metafrontier_module, "MAX_METAFRONTIER_OBSERVATIONS", 5)

    assert not metafrontier_plot_applicable(result)
    with pytest.raises(PlotNotAvailableError, match="limited to 5"):
        prepare_metafrontier_data(result)


def test_matplotlib_metafrontier_renders_economic_account_without_showing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    matplotlib, pyplot = _load_matplotlib_for_test(monkeypatch, tmp_path)
    monkeypatch.setattr(
        pyplot,
        "show",
        lambda *args, **kwargs: pytest.fail("plot() must not display the figure"),
    )
    before = matplotlib.rcParams.copy()

    figure = _metafrontier_result().plot(kind="metafrontier")

    assert len(figure.axes) == 1
    axis = figure.axes[0]
    assert axis.get_title() == (
        "Within-group performance and pooled-opportunity comparison"
    )
    labels = [label.get_text() for label in axis.get_yticklabels()]
    assert labels == [
        "A  ·  group_1",
        "B  ·  group_1",
        "C  ·  group_1",
        "D  ·  group_2",
        "E  ·  group_2",
        "F  ·  group_2",
    ]
    all_text = " ".join(
        [text.get_text() for text in axis.texts]
        + [text.get_text() for text in figure.texts]
    )
    assert "MTR 0.50" in all_text
    assert "Meta efficiency = group efficiency \N{MULTIPLICATION SIGN} MTR" in all_text
    assert "neither component identifies causes or assigns management blame" in all_text
    assert "MTR is their ratio" in all_text
    assert matplotlib.rcParams == before
    pyplot.close(figure)
