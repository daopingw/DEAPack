from __future__ import annotations

import builtins
from typing import Any

import pandas as pd
import pytest

from deapack import (
    BiennialMalmquistDEA,
    DEAData,
    DEAResult,
    GlobalMalmquistDEA,
    GlobalMalmquistLuenbergerDEA,
    HicksMoorsteenDEA,
    LuenbergerDEA,
    MalmquistDEA,
    MalmquistLuenbergerDEA,
    load_dataset,
)
from deapack.solvers import SciPyHiGHSSolver
from deapack.visualization import prepare_performance_data


@pytest.fixture(scope="module")
def productivity_data() -> DEAData:
    frame = load_dataset("productivity_panel")
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs=("capital", "labor"),
        outputs="output",
    )


@pytest.fixture(scope="module")
def environmental_data() -> DEAData:
    frame = load_dataset("environmental_panel")
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs=("energy", "labor"),
        outputs="electricity",
        bad_outputs="co2",
    )


@pytest.fixture(scope="module")
def common_reference_results(
    productivity_data: DEAData,
    environmental_data: DEAData,
) -> dict[str, DEAResult]:
    return {
        "productivity.global_malmquist": GlobalMalmquistDEA().fit(productivity_data),
        "productivity.biennial_malmquist": BiennialMalmquistDEA().fit(
            productivity_data
        ),
        "productivity.global_malmquist_luenberger.oh_2010": (
            GlobalMalmquistLuenbergerDEA().fit(environmental_data)
        ),
    }


@pytest.mark.parametrize(
    ("method_id", "alias_metadata_key", "alias_metadata_value"),
    [
        (
            "productivity.global_malmquist",
            "technical_change_field",
            "best_practice_change",
        ),
        (
            "productivity.biennial_malmquist",
            "technical_change_field",
            "best_practice_change",
        ),
        (
            "productivity.global_malmquist_luenberger.oh_2010",
            "technical_change_alias",
            "best_practice_change_for_common_result_schema_not_cfg_technical_change",
        ),
    ],
)
def test_common_reference_discovery_prefers_source_native_best_practice_change(
    method_id: str,
    alias_metadata_key: str,
    alias_metadata_value: str,
    common_reference_results: dict[str, DEAResult],
) -> None:
    result = common_reference_results[method_id]
    before = result.summary(copy=True)

    performance = result.available_plots()[0]
    measures = {measure.column: measure for measure in performance.measures}

    assert result.metadata["method_id"] == method_id
    assert result.metadata[alias_metadata_key] == alias_metadata_value
    pd.testing.assert_series_equal(
        before["technical_change"],
        before["best_practice_change"],
        check_names=False,
    )
    assert performance.kind == "performance"
    assert performance.default_metric == "productivity_change"
    assert "best_practice_change" in measures
    assert measures["best_practice_change"].label == "Best-Practice Change"
    assert "technical_change" not in measures
    pd.testing.assert_frame_equal(result.summary(), before)


@pytest.mark.parametrize(
    "method_id",
    [
        "productivity.global_malmquist",
        "productivity.biennial_malmquist",
        "productivity.global_malmquist_luenberger.oh_2010",
    ],
)
def test_common_reference_technical_alias_remains_explicitly_plottable(
    method_id: str,
    common_reference_results: dict[str, DEAResult],
) -> None:
    result = common_reference_results[method_id]
    summary = result.summary(copy=True)
    period = summary["comparison_period"].iloc[0]

    alias = prepare_performance_data(
        result,
        metric="technical_change",
        period=period,
        view="points",
    )
    canonical = prepare_performance_data(
        result,
        metric="best_practice_change",
        period=period,
        view="points",
    )

    assert alias.metric == "technical_change"
    assert canonical.metric == "best_practice_change"
    assert alias.measure.label == "Best-Practice Change"
    assert canonical.measure.label == "Best-Practice Change"
    assert alias.measure.preferred_direction == canonical.measure.preferred_direction
    assert alias.measure.benchmark_value == canonical.measure.benchmark_value == 1.0
    alias_frame = alias.facets[0].frame.set_index("dmu_id")
    canonical_frame = canonical.facets[0].frame.set_index("dmu_id")
    assert alias_frame.index.tolist() == canonical_frame.index.tolist()
    pd.testing.assert_series_equal(
        alias_frame["technical_change"],
        canonical_frame["best_practice_change"],
        check_names=False,
    )
    pd.testing.assert_frame_equal(result.summary(), summary)


def test_adjacent_productivity_components_keep_technical_change_semantics(
    productivity_data: DEAData,
    environmental_data: DEAData,
) -> None:
    results = (
        MalmquistDEA().fit(productivity_data),
        LuenbergerDEA().fit(productivity_data),
        MalmquistLuenbergerDEA().fit(environmental_data),
    )

    for result in results:
        measures = {
            measure.column: measure for measure in result.available_plots()[0].measures
        }
        assert "best_practice_change" not in measures
        assert measures["technical_change"].label == "Technical Change"
        period = result.summary()["comparison_period"].iloc[0]
        prepared = prepare_performance_data(
            result,
            metric="technical_change",
            period=period,
        )
        assert prepared.metric == "technical_change"
        assert prepared.measure.label == "Technical Change"


def test_hicks_moorsteen_measure_discovery_is_unchanged(
    productivity_data: DEAData,
) -> None:
    result = HicksMoorsteenDEA(returns_to_scale="vrs").fit(productivity_data)
    measures = {
        measure.column: measure for measure in result.available_plots()[0].measures
    }

    assert set(measures) == {
        "score",
        "productivity_change",
        "output_quantity_index",
        "input_quantity_index",
    }
    assert "technical_change" not in result.summary()
    assert "best_practice_change" not in result.summary()


def test_similar_custom_method_id_does_not_inherit_common_reference_alias_rule(
    common_reference_results: dict[str, DEAResult],
) -> None:
    exact = common_reference_results["productivity.global_malmquist_luenberger.oh_2010"]
    custom = DEAResult(
        summary_frame=exact.summary(copy=True),
        metadata={
            **exact.metadata,
            "method_id": (
                "productivity.global_malmquist_luenberger.oh_2010.custom_variant"
            ),
        },
    )

    measures = {
        measure.column: measure for measure in custom.available_plots()[0].measures
    }
    explicit = prepare_performance_data(
        custom,
        metric="technical_change",
        period=custom.summary()["comparison_period"].iloc[0],
    )

    assert measures["technical_change"].label == "Technical Change"
    assert measures["best_practice_change"].label == "Best-Practice Change"
    assert explicit.measure.label == "Technical Change"


class _CountingSolver:
    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):
        self.calls += 1
        return self._delegate.solve(problem)


def test_alias_discovery_and_preparation_are_backend_lazy_and_add_no_solves(
    monkeypatch: pytest.MonkeyPatch,
    productivity_data: DEAData,
    environmental_data: DEAData,
) -> None:
    fitted: list[tuple[DEAResult, _CountingSolver]] = []
    for model, data in (
        (GlobalMalmquistDEA, productivity_data),
        (BiennialMalmquistDEA, productivity_data),
        (GlobalMalmquistLuenbergerDEA, environmental_data),
    ):
        solver = _CountingSolver()
        result = model(solver=solver).fit(data)
        assert solver.calls > 0
        fitted.append((result, solver))

    ordinary_import = builtins.__import__

    def _reject_matplotlib_import(
        name: str,
        globals: Any = None,
        locals: Any = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> Any:
        if name == "matplotlib" or name.startswith("matplotlib."):
            raise AssertionError("measure discovery must not import Matplotlib")
        return ordinary_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _reject_matplotlib_import)
    for result, solver in fitted:
        calls_after_fit = solver.calls
        period = result.summary()["comparison_period"].iloc[0]
        performance = result.available_plots()[0]
        prepare_performance_data(
            result,
            metric="technical_change",
            period=period,
        )
        prepare_performance_data(
            result,
            metric="best_practice_change",
            period=period,
        )

        assert "technical_change" not in {
            measure.column for measure in performance.measures
        }
        assert solver.calls == calls_after_fit
        assert result.metadata["additional_solver_calls"] == 0
