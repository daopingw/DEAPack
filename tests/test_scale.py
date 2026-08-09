import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

import deapack.models.radial as radial_module
from deapack import DEAData, ReferenceSpec, scale_efficiency
from deapack.models.radial import RadialDEA
from deapack.solvers import SciPyHiGHSSolver


class _CountingSolver:
    name = "counting-scipy-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        return self._delegate.solve(problem)


def test_scale_efficiency_composes_crs_and_vrs_results() -> None:
    frame = pd.DataFrame(
        {
            "unit": ["A", "B", "C"],
            "input": [1.0, 2.0, 1.0],
            "output": [1.0, 1.0, 0.5],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="unit",
        inputs="input",
        outputs="output",
    )

    result = scale_efficiency(data)
    summary = result.summary().set_index("dmu_id")

    assert np.isclose(summary.loc["A", "scale_efficiency"], 1.0)
    assert np.isclose(summary.loc["B", "scale_efficiency"], 1.0)
    assert np.isclose(summary.loc["C", "crs_efficiency"], 0.5)
    assert np.isclose(summary.loc["C", "vrs_efficiency"], 1.0)
    assert np.isclose(summary.loc["C", "scale_efficiency"], 0.5)
    assert bool(summary.loc["B", "is_scale_efficient"])
    assert pd.isna(summary.loc["B", "is_efficient"])
    assert not bool(summary.loc["C", "is_scale_efficient"])
    assert pd.isna(summary.loc["C", "is_efficient"])
    assert result.metadata["definition"] == "crs_efficiency / vrs_efficiency"


def test_external_scale_ratio_does_not_claim_self_inclusive_classification() -> None:
    frame = pd.DataFrame(
        {
            "unit": ["reference", "evaluated"],
            "input": [2.0, 1.0],
            "output": [2.0, 2.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="unit",
        inputs="input",
        outputs="output",
    )

    result = scale_efficiency(
        data,
        reference=ReferenceSpec("custom", custom_rows=[0]),
    )
    row = result.summary().set_index("dmu_id").loc["evaluated"]

    assert row["crs_efficiency"] == 2.0
    assert row["vrs_efficiency"] == 2.0
    assert row["scale_efficiency"] == 1.0
    assert bool(row["score_valid"])
    assert not bool(row["is_within_reference_technology"])
    assert pd.isna(row["is_scale_efficient"])
    assert result.metadata["classification_domain"] == (
        "evaluated_plan_within_both_reference_technologies"
    )


def test_scale_efficiency_shares_one_compiled_matched_reference(
    monkeypatch,
) -> None:
    frame = pd.DataFrame(
        {
            "unit": ["A", "B", "C", "D"],
            "input": [1.0, 2.0, 1.0, 3.0],
            "output": [1.0, 1.0, 0.5, 2.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="unit",
        inputs="input",
        outputs="output",
    )
    solver = _CountingSolver()
    compilation_calls = 0
    original_compile = radial_module.compile_reference

    def counted_compile(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal compilation_calls
        compilation_calls += 1
        return original_compile(*args, **kwargs)

    monkeypatch.setattr(radial_module, "compile_reference", counted_compile)
    result = scale_efficiency(data, reference="global", solver=solver)

    assert compilation_calls == 1
    assert solver.calls == 2 * data.n_dmus
    assert result.metadata["component_solver_calls"] == {
        "crs_efficiency": data.n_dmus,
        "vrs_efficiency": data.n_dmus,
    }
    assert result.metadata["solver_calls"] == 2 * data.n_dmus
    assert result.metadata["component_reference_sets"] == {
        "crs": 1,
        "vrs": 1,
    }
    assert result.metadata["compiled_reference_sets"] == 1


def test_scale_efficiency_compiles_each_contemporaneous_population_once(
    monkeypatch,
) -> None:
    frame = pd.DataFrame(
        {
            "unit": ["A", "B", "A", "B", "A", "B"],
            "period": [2020, 2020, 2021, 2021, 2022, 2022],
            "input": [1.0, 2.0, 1.1, 2.1, 1.2, 2.2],
            "output": [1.0, 1.4, 1.1, 1.5, 1.2, 1.6],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="unit",
        period="period",
        inputs="input",
        outputs="output",
    )
    solver = _CountingSolver()
    compilation_calls = 0
    original_compile = radial_module.compile_reference

    def counted_compile(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal compilation_calls
        compilation_calls += 1
        return original_compile(*args, **kwargs)

    monkeypatch.setattr(radial_module, "compile_reference", counted_compile)
    result = scale_efficiency(data, solver=solver)

    assert compilation_calls == len(data.period_order) == 3
    assert solver.calls == 2 * data.n_dmus
    assert result.metadata["component_reference_sets"] == {
        "crs": 3,
        "vrs": 3,
    }
    assert result.metadata["compiled_reference_sets"] == 3


def test_shared_compilation_preserves_component_scores_and_diagnostics() -> None:
    frame = pd.DataFrame(
        {
            "unit": ["A", "B", "C", "D"],
            "input": [1.0, 2.0, 1.0, 3.0],
            "output": [1.0, 1.0, 0.5, 2.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="unit",
        inputs="input",
        outputs="output",
    )
    actual = scale_efficiency(data, reference="global")
    crs = RadialDEA(
        returns_to_scale="crs",
        reference="global",
        compute_slacks=False,
    ).fit(data)
    vrs = RadialDEA(
        returns_to_scale="vrs",
        reference="global",
        compute_slacks=False,
    ).fit(data)

    expected_summary = pd.DataFrame(
        {
            "dmu_id": crs.summary()["dmu_id"],
            "crs_efficiency": crs.summary()["efficiency"],
            "vrs_efficiency": vrs.summary()["efficiency"],
        }
    )
    actual_summary = actual.summary()[["dmu_id", "crs_efficiency", "vrs_efficiency"]]
    assert_frame_equal(actual_summary, expected_summary)
    expected_diagnostics = pd.concat(
        [
            crs.diagnostics.assign(component="crs"),
            vrs.diagnostics.assign(component="vrs"),
        ],
        ignore_index=True,
    )
    assert_frame_equal(actual.diagnostics, expected_diagnostics)
