from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

import deapack.analysis.productivity as productivity_module
from deapack import (
    DEAData,
    FGNZMalmquistProductivityIndex,
    MalmquistProductivityIndex,
    RayDesliMalmquist,
    RayDesliMalmquistProductivityIndex,
)
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.solvers import SciPyHiGHSSolver

_ORACLE_PATH = Path(__file__).with_name("test_ray_desli_1997_source_reproduction.py")
_ORACLE_SPEC = importlib.util.spec_from_file_location(
    "_ray_desli_source_oracle_for_public_test",
    _ORACLE_PATH,
)
assert _ORACLE_SPEC is not None and _ORACLE_SPEC.loader is not None
source_oracle = importlib.util.module_from_spec(_ORACLE_SPEC)
sys.modules[_ORACLE_SPEC.name] = source_oracle
_ORACLE_SPEC.loader.exec_module(source_oracle)

_ROLES = (
    "base_on_base",
    "comparison_on_base",
    "base_on_comparison",
    "comparison_on_comparison",
)


def _source_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "dmu": ["A", "B", "C", "D", "A", "B", "C", "D"],
            "period": [0, 0, 0, 0, 1, 1, 1, 1],
            "x": np.concatenate(
                [source_oracle._X_BASE[:, 0], source_oracle._X_COMPARISON[:, 0]]
            ),
            "y": np.concatenate(
                [source_oracle._Y_BASE[:, 0], source_oracle._Y_COMPARISON[:, 0]]
            ),
        }
    )


def _data(
    frame: pd.DataFrame,
    *,
    inputs: str | tuple[str, ...] = "x",
    outputs: str | tuple[str, ...] = "y",
    bad_outputs: str | None = None,
    period_order: tuple[int, ...] | None = None,
) -> DEAData:
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        period_order=period_order,
        inputs=inputs,
        outputs=outputs,
        bad_outputs=bad_outputs,
    )


def test_public_ray_desli_matches_independent_eight_task_source_oracle() -> None:
    data = _data(_source_frame())
    result = RayDesliMalmquistProductivityIndex().fit(data)
    summary = result.summary().set_index("dmu_id")
    diagnostics = result.diagnostics.set_index(
        ["dmu_id", "returns_to_scale", "distance_role"]
    )
    tasks = source_oracle._compile_eight_tasks(
        source_oracle._X_BASE,
        source_oracle._Y_BASE,
        source_oracle._X_COMPARISON,
        source_oracle._Y_COMPARISON,
    )
    accounts = source_oracle._ray_desli_accounts(tasks)

    for dmu_position, (dmu_id, account) in enumerate(
        zip(("A", "B", "C", "D"), accounts, strict=True)
    ):
        row = summary.loc[dmu_id]
        for role, (reference_period, target_period) in source_oracle._ROLES.items():
            for rts, values in (("crs", tasks.crs), ("vrs", tasks.vrs)):
                expected = values[dmu_position, reference_period, target_period]
                assert row[f"{rts}_distance_{role}"] == pytest.approx(
                    expected,
                    abs=1e-11,
                )
                assert diagnostics.loc[
                    (dmu_id, rts, role), "farrell_efficiency"
                ] == pytest.approx(expected, abs=1e-11)
            assert row[f"scale_efficiency_{role}"] == pytest.approx(
                tasks.crs[dmu_position, reference_period, target_period]
                / tasks.vrs[dmu_position, reference_period, target_period],
                abs=1e-11,
            )

        assert row["productivity_change"] == pytest.approx(
            account.productivity_change,
            abs=1e-11,
        )
        assert row["pure_efficiency_change"] == pytest.approx(
            account.pure_efficiency_change,
            abs=1e-11,
        )
        assert row["vrs_technical_change"] == pytest.approx(
            account.technical_change_vrs,
            abs=1e-11,
        )
        assert row["ray_desli_scale_change"] == pytest.approx(
            account.scale_efficiency_change_vrs,
            abs=1e-11,
        )
        assert row["ray_desli_decomposition_residual"] == pytest.approx(
            0.0,
            abs=1e-11,
        )
        assert row["decomposition_defined"]
        assert row["decomposition_status"] == "optimal"

    assert (summary["solver_status"] == "optimal").all()
    assert summary["score_valid"].all()
    assert summary["score_status"].eq("defined").all()
    assert summary["peer_valid"].all()
    assert summary["peer_status"].eq("certified_transition_distances").all()
    assert set(result.diagnostics["returns_to_scale"]) == {"crs", "vrs"}
    assert result.diagnostics["backend_solver_status"].eq("optimal").all()
    assert result.diagnostics["raw_solver_status"].eq("optimal").all()
    assert result.diagnostics["score_valid"].all()
    assert set(result.intensities["returns_to_scale"]) == {"crs", "vrs"}
    for forbidden in ("efficiency_change", "technical_change", "scale_change"):
        assert forbidden not in summary


def test_vrs_cross_infeasibility_keeps_source_defined_partial_account() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [0, 0, 1, 1],
            "x": [1.0, 2.0, 0.5, 1.5],
            "y": [1.0, 2.0, 1.1, 2.5],
        }
    )
    result = RayDesliMalmquist().fit(_data(frame))
    row = result.summary().set_index("dmu_id").loc["A"]

    assert row["score"] == pytest.approx(2.2, abs=1e-11)
    assert row["productivity_change"] == pytest.approx(2.2, abs=1e-11)
    assert row["pure_efficiency_change"] == pytest.approx(1.0, abs=1e-11)
    assert row["solver_status"] == "optimal"
    assert bool(row["score_valid"])
    assert row["score_status"] == "defined"
    assert row["decomposition_status"] == "vrs_cross_infeasible"
    assert not row["decomposition_defined"]
    assert not bool(row["peer_valid"])
    assert row["peer_status"] == (
        "not_available_without_complete_certified_distance_set"
    )
    assert pd.isna(row["vrs_technical_change"])
    assert pd.isna(row["ray_desli_scale_change"])
    assert pd.isna(row["ray_desli_decomposition_residual"])
    assert pd.isna(row["vrs_distance_comparison_on_base"])
    assert pd.isna(row["scale_efficiency_comparison_on_base"])
    assert np.isfinite(row["vrs_distance_base_on_base"])
    assert np.isfinite(row["vrs_distance_comparison_on_comparison"])
    assert np.isfinite(row["crs_distance_comparison_on_base"])
    assert result.intensities.loc[result.intensities["dmu_id"] == "A"].empty

    failed = result.diagnostics.loc[
        (result.diagnostics["dmu_id"] == "A")
        & (result.diagnostics["returns_to_scale"] == "vrs")
        & (result.diagnostics["distance_role"] == "comparison_on_base")
    ].iloc[0]
    assert failed["solver_status"] == "infeasible"
    assert pd.isna(failed["farrell_efficiency"])


@pytest.mark.parametrize("column", ["x", "y"])
def test_ray_desli_requires_strictly_positive_quantities(column: str) -> None:
    frame = _source_frame()
    frame.loc[0, column] = 0.0
    with pytest.raises(DataValidationError, match="strictly positive"):
        RayDesliMalmquist().fit(_data(frame))


def test_ray_desli_rejects_multiple_or_undesirable_outputs_explicitly() -> None:
    frame = _source_frame().assign(y2=lambda value: 2.0 * value["y"], bad=1.0)
    with pytest.raises(ModelSpecificationError, match="exactly one desirable output"):
        RayDesliMalmquist().fit(_data(frame, outputs=("y", "y2")))
    with pytest.raises(ModelSpecificationError, match="desirable outputs only"):
        RayDesliMalmquist().fit(_data(frame, bad_outputs="bad"))


def test_ray_desli_requires_a_balanced_adjacent_panel() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C", "A", "B", "D"],
            "period": [0, 0, 0, 1, 1, 1],
            "x": [1.0, 2.0, 3.0, 1.0, 2.0, 4.0],
            "y": [1.0, 2.0, 3.0, 1.1, 2.2, 4.4],
        }
    )

    with pytest.raises(DataValidationError, match="unbalanced adjacent periods"):
        RayDesliMalmquist().fit(_data(frame))
    with pytest.raises(TypeError, match="unbalanced"):
        RayDesliMalmquist(unbalanced="drop")  # type: ignore[call-arg]


def test_alias_and_machine_method_metadata_identity_are_source_specific() -> None:
    result = RayDesliMalmquist().fit(_data(_source_frame()))

    assert RayDesliMalmquist is RayDesliMalmquistProductivityIndex
    assert result.metadata["method_id"] == (
        "productivity.malmquist.decomposition.ray_desli"
    )
    assert "preset_id" not in result.metadata
    assert result.metadata["decomposition_id"] == (
        "productivity.malmquist.decomposition.ray_desli"
    )
    assert result.metadata["parent_operator_id"] == (
        "productivity.malmquist.adjacent_geometric"
    )
    assert result.metadata["orientation"] == "output"
    assert result.metadata["headline_returns_to_scale"] == "crs"
    assert result.metadata["auxiliary_returns_to_scale"] == "vrs"


class _CountingSolver:
    name = "counting-highs"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem: Any):
        self.calls += 1
        return self._delegate.solve(problem)


def test_three_period_task_cache_and_template_counts_are_exact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"] * 3,
            "period": [0, 0, 1, 1, 2, 2],
            "x": [1.0, 2.0, 1.0, 2.0, 1.0, 2.0],
            "y": [1.0, 2.0, 1.1, 2.2, 1.25, 2.5],
        }
    )
    solver = _CountingSolver()
    reference_compilations = 0
    template_compilations = {"crs": 0, "vrs": 0}
    original_reference = productivity_module.compile_reference
    original_template = productivity_module.compile_radial_phase_one_template

    def counted_reference(*args, **kwargs):
        nonlocal reference_compilations
        reference_compilations += 1
        return original_reference(*args, **kwargs)

    def counted_template(reference, orientation, returns_to_scale):
        template_compilations[returns_to_scale.value] += 1
        return original_template(reference, orientation, returns_to_scale)

    monkeypatch.setattr(productivity_module, "compile_reference", counted_reference)
    monkeypatch.setattr(
        productivity_module,
        "compile_radial_phase_one_template",
        counted_template,
    )
    result = RayDesliMalmquist(solver=solver).fit(_data(frame))
    metadata = result.metadata

    assert len(result.summary()) == 4
    assert len(result.diagnostics) == 32
    assert int(result.diagnostics["task_reused"].sum()) == 4
    assert reference_compilations == 3
    assert template_compilations == {"crs": 3, "vrs": 3}
    assert solver.calls == 28
    assert metadata["reference_plan_unique_sets"] == 3
    assert metadata["compiled_reference_sets"] == 3
    assert metadata["requested_distance_tasks"] == 32
    assert metadata["requested_distance_tasks_by_rts"] == {"crs": 16, "vrs": 16}
    assert metadata["unique_distance_solves"] == 28
    assert metadata["unique_distance_solves_by_rts"] == {"crs": 14, "vrs": 14}
    assert metadata["phase_one_template_compilations"] == 6
    assert metadata["phase_one_template_compilations_by_rts"] == {
        "crs": 3,
        "vrs": 3,
    }
    assert metadata["phase_one_task_bindings"] == 28
    assert metadata["phase_one_task_bindings_by_rts"] == {"crs": 14, "vrs": 14}
    assert metadata["solver_calls"] == 28
    assert metadata["solver_calls_by_rts"] == {"crs": 14, "vrs": 14}


def test_ray_desli_is_row_and_unit_invariant_and_supports_multiple_inputs() -> None:
    frame = _source_frame().assign(capital=lambda value: 3.0 * value["x"] + 1.0)
    scaled = frame.copy()
    scaled["x"] *= 7.0
    scaled["capital"] *= 11.0
    scaled["y"] *= 13.0
    scaled = scaled.iloc[[6, 0, 5, 3, 7, 2, 4, 1]].reset_index(drop=True)

    base = RayDesliMalmquist().fit(
        _data(frame, inputs=("x", "capital"), period_order=(0, 1))
    )
    transformed = RayDesliMalmquist().fit(
        _data(scaled, inputs=("x", "capital"), period_order=(0, 1))
    )
    columns = [
        "productivity_change",
        "pure_efficiency_change",
        "vrs_technical_change",
        "ray_desli_scale_change",
        *(f"crs_distance_{role}" for role in _ROLES),
        *(f"vrs_distance_{role}" for role in _ROLES),
    ]
    base_summary = base.summary().sort_values("dmu_id").reset_index(drop=True)
    transformed_summary = (
        transformed.summary().sort_values("dmu_id").reset_index(drop=True)
    )

    np.testing.assert_allclose(
        base_summary[columns],
        transformed_summary[columns],
        atol=1e-10,
        rtol=0.0,
    )


def test_existing_fgnz_and_generic_crs_contracts_remain_numerically_identical() -> None:
    data = _data(_source_frame())
    generic = MalmquistProductivityIndex(
        orientation="output",
        returns_to_scale="crs",
    ).fit(data)
    fgnz = FGNZMalmquistProductivityIndex().fit(data)
    ray_desli = RayDesliMalmquist().fit(data)
    fields = [
        "productivity_change",
        "efficiency_change",
        "technical_change",
        *(f"distance_{role}" for role in _ROLES),
    ]

    np.testing.assert_allclose(generic.summary()[fields], fgnz.summary()[fields])
    np.testing.assert_allclose(
        ray_desli.summary()["productivity_change"],
        fgnz.summary()["productivity_change"],
        atol=1e-11,
    )
    assert generic.metadata["unique_distance_solves"] == 16
    assert fgnz.metadata["unique_distance_solves"] == 16
    assert generic.metadata["compiled_reference_sets"] == 2
    assert fgnz.metadata["compiled_reference_sets"] == 2


@pytest.mark.parametrize("scale", [1e7, 1e8])
def test_strictly_positive_small_cross_period_factor_is_not_a_tolerance_failure(
    scale: float,
) -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "period": [0, 0, 1, 1],
            "x": [1.0, 2.0, 1.0, 2.0],
            "y": [1.0, 2.0, scale, 2.0 * scale],
        }
    )

    result = RayDesliMalmquist().fit(_data(frame))
    summary = result.summary()
    diagnostics = result.diagnostics

    np.testing.assert_allclose(
        summary["crs_distance_comparison_on_base"],
        scale,
        rtol=1e-10,
    )
    np.testing.assert_allclose(
        summary["crs_distance_base_on_comparison"],
        1.0 / scale,
        rtol=1e-10,
    )
    np.testing.assert_allclose(summary["productivity_change"], scale, rtol=1e-10)
    np.testing.assert_allclose(summary["pure_efficiency_change"], 1.0, rtol=1e-10)
    np.testing.assert_allclose(summary["vrs_technical_change"], scale, rtol=1e-10)
    np.testing.assert_allclose(summary["ray_desli_scale_change"], 1.0, rtol=1e-10)
    assert (summary["solver_status"] == "optimal").all()
    assert (summary["decomposition_status"] == "optimal").all()
    assert summary["decomposition_defined"].all()

    small_factor_rows = diagnostics.loc[
        (diagnostics["returns_to_scale"] == "crs")
        & (diagnostics["distance_role"] == "comparison_on_base")
    ]
    np.testing.assert_allclose(
        small_factor_rows["radial_factor"],
        1.0 / scale,
        rtol=1e-10,
    )
    assert (small_factor_rows["solver_status"] == "optimal").all()


@pytest.mark.parametrize("invalid_factor", [0.0, np.nan, np.inf])
def test_nonpositive_or_nonfinite_radial_factor_fails_closed(
    invalid_factor: float,
) -> None:
    class _CorruptFirstFactorSolver:
        name = "corrupt-first-factor"

        def __init__(self) -> None:
            self.calls = 0
            self._delegate = SciPyHiGHSSolver()

        def solve(self, problem):
            self.calls += 1
            solution = self._delegate.solve(problem)
            if self.calls != 1 or solution.primal is None:
                return solution
            primal = solution.primal.copy()
            primal[-1] = invalid_factor
            return replace(solution, primal=primal)

    result = RayDesliMalmquist(solver=_CorruptFirstFactorSolver()).fit(
        _data(_source_frame())
    )
    row = result.summary().iloc[0]
    diagnostic = result.diagnostics.iloc[0]

    assert row["solver_status"] == "numerical_error"
    assert not bool(row["score_valid"])
    assert row["score_status"] == "unavailable_uncertified_distance_program"
    assert not bool(row["peer_valid"])
    assert row["peer_status"] == "not_available_without_certified_crs_headline"
    assert row["decomposition_status"] == "crs_numerical_error"
    assert pd.isna(row["productivity_change"])
    assert pd.isna(row["crs_distance_base_on_base"])
    assert diagnostic["solver_status"] == "numerical_error"
    assert diagnostic["backend_solver_status"] == "optimal"
    assert diagnostic["raw_solver_status"] == "optimal"
    assert not bool(diagnostic["score_valid"])
    assert pd.isna(diagnostic["farrell_efficiency"])
    assert result.intensities.loc[result.intensities["dmu_id"] == "A"].empty
