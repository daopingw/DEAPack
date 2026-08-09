from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest
from scipy.sparse import issparse

import deapack
import deapack.models as model_api
from deapack import (
    DEAData,
    NonCHPEnergyCarbonDEA,
    SolverOptions,
    ZhouAngWangNonCHPEnergyCarbonDEA,
    load_dataset,
)
from deapack.enums import SolverStatus
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.solvers import LPSolution, SciPyHiGHSSolver

_ACCOUNTS = ("energy", "carbon", "integrated_energy_carbon")
_ACCOUNT_WEIGHTS = {
    "energy": np.asarray([0.5, 0.5, 0.0]),
    "carbon": np.asarray([0.0, 0.5, 0.5]),
    "integrated_energy_carbon": np.asarray([1.0 / 3.0] * 3),
}
_O_EXPECTED = {
    "energy": {
        "beta": (0.0, 3.0 / 5.0, 0.0),
        "distance": 3.0 / 10.0,
        "index": 5.0 / 8.0,
        "index_name": "epi_1",
        "target": (2.0, 8.0 / 5.0, 4.0),
        "intensities": {"A": 4.0 / 5.0, "D": 4.0 / 5.0},
    },
    "carbon": {
        "beta": (0.0, 1.0, 1.0 / 2.0),
        "distance": 3.0 / 4.0,
        "index": 1.0 / 4.0,
        "index_name": "cpi_1",
        "target": (2.0, 2.0, 2.0),
        "intensities": {"A": 2.0},
    },
    "integrated_energy_carbon": {
        "beta": (0.0, 1.0, 1.0 / 2.0),
        "distance": 1.0 / 2.0,
        "index": 3.0 / 8.0,
        "index_name": "ecpi_1",
        "target": (2.0, 2.0, 2.0),
        "intensities": {"A": 2.0},
    },
}


def _source_data(
    *,
    fossil_scale: float = 1.0,
    electricity_scale: float = 1.0,
    carbon_scale: float = 1.0,
) -> DEAData:
    frame = load_dataset("zhou_ang_wang_non_chp_3")
    frame["fossil_energy"] *= fossil_scale
    frame["electricity"] *= electricity_scale
    frame["co2"] *= carbon_scale
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs="fossil_energy",
        outputs="electricity",
        bad_outputs="co2",
    )


def _multiplicity_data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "O"],
                "fossil_energy": [1.0, 1.0, 1.0],
                "electricity": [3.0, 5.0, 1.0],
                "co2": [1.0, 2.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="fossil_energy",
        outputs="electricity",
        bad_outputs="co2",
    )


class _AuditingSolver:
    name = "zhou-ang-wang-non-chp-auditing-fixture"

    def __init__(self) -> None:
        self.calls = 0
        self.problems = []
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        self.problems.append(problem)
        assert problem.a_ub is not None
        assert problem.a_eq is not None
        assert issparse(problem.a_ub)
        assert issparse(problem.a_eq)
        return self._delegate.solve(problem)


class _AlwaysLimitSolver:
    name = "zhou-ang-wang-non-chp-limit-fixture"

    def solve(self, problem):  # type: ignore[no-untyped-def]
        del problem
        return LPSolution(
            status=SolverStatus.LIMIT_REACHED,
            objective=None,
            primal=None,
            message="injected limit",
            iterations=3,
        )


class _MissingDualCertificateSolver:
    name = "zhou-ang-wang-non-chp-missing-dual-fixture"

    def __init__(self) -> None:
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        solution = self._delegate.solve(problem)
        return replace(
            solution,
            inequality_marginals=None,
            equality_marginals=None,
            message="injected missing dual certificate",
        )


def _does_not_claim_unique(value: object) -> bool:
    return bool(pd.isna(value) or value is False or value == 0)


@pytest.mark.parametrize("account", _ACCOUNTS)
def test_three_source_accounts_api_exact_values_and_sparse_crs_program(
    account: str,
) -> None:
    assert NonCHPEnergyCarbonDEA is ZhouAngWangNonCHPEnergyCarbonDEA
    assert deapack.NonCHPEnergyCarbonDEA is ZhouAngWangNonCHPEnergyCarbonDEA
    assert deapack.ZhouAngWangNonCHPEnergyCarbonDEA is ZhouAngWangNonCHPEnergyCarbonDEA
    assert model_api.NonCHPEnergyCarbonDEA is ZhouAngWangNonCHPEnergyCarbonDEA
    assert (
        model_api.ZhouAngWangNonCHPEnergyCarbonDEA is ZhouAngWangNonCHPEnergyCarbonDEA
    )

    solver = _AuditingSolver()
    data = _source_data()
    result = ZhouAngWangNonCHPEnergyCarbonDEA(
        account=account,
        solver=solver,
    ).fit(data)
    summary = result.summary().set_index("dmu_id")
    row = summary.loc["O"]
    expected = _O_EXPECTED[account]

    assert row["directional_nonradial_distance"] == pytest.approx(expected["distance"])
    assert row["distance"] == pytest.approx(expected["distance"])
    assert row["performance_index"] == pytest.approx(expected["index"])
    assert row["score"] == pytest.approx(expected["index"])
    assert row["efficiency"] == pytest.approx(expected["index"])
    assert row["performance_index_name"] == expected["index_name"]
    np.testing.assert_allclose(
        row[["beta_fossil", "beta_electricity", "beta_carbon"]].astype(float),
        expected["beta"],
        atol=1e-12,
        rtol=0.0,
    )
    assert row["score_direction"] == "higher_is_better"
    assert row["distance_direction"] == "higher_is_more_unrealized_opportunity"
    assert bool(row["ranking_value_valid"])

    inactive = _ACCOUNT_WEIGHTS[account] == 0.0
    beta_columns = ["beta_fossil", "beta_electricity", "beta_carbon"]
    for component, is_inactive in zip(beta_columns, inactive, strict=True):
        if is_inactive:
            assert (summary[component] == 0.0).all()

    assert solver.calls == data.n_dmus
    assert len(solver.problems) == data.n_dmus
    expected_objective = -_ACCOUNT_WEIGHTS[account]
    for problem in solver.problems:
        assert problem.c.shape == (data.n_dmus + 3,)
        assert problem.a_ub.shape == (2, data.n_dmus + 3)
        assert problem.a_eq.shape == (1, data.n_dmus + 3)
        np.testing.assert_array_equal(problem.c[-3:], expected_objective)
        assert problem.bounds[: data.n_dmus] == ((0.0, None),) * data.n_dmus
        for component, is_inactive in enumerate(inactive):
            expected_bound = (0.0, 0.0) if is_inactive else (0.0, None)
            assert problem.bounds[data.n_dmus + component] == expected_bound

    assert result.metadata["method_id"] == (
        "environmental.directional_nonradial.energy_carbon.zhou_ang_wang_2012_non_chp"
    )
    assert result.metadata["source_preset"] == account
    assert result.metadata["returns_to_scale"] == "crs"
    assert result.metadata["reference_kind"] == "global_cross_section"
    assert result.metadata["self_inclusive"] is True
    assert result.metadata["compiled_reference_sets"] == 1
    assert result.metadata["solver_calls"] == data.n_dmus
    assert result.metadata["bad_output_constraint"] == "equality"
    assert result.metadata["null_jointness"] is True


@pytest.mark.parametrize("account", _ACCOUNTS)
def test_source_targets_and_peer_activity_reconstruct_equations_4_and_7(
    account: str,
) -> None:
    source_frame = load_dataset("zhou_ang_wang_non_chp_3").set_index("dmu")
    result = ZhouAngWangNonCHPEnergyCarbonDEA(
        account=account,
        peer_tolerance=1.0e-12,
    ).fit(_source_data())
    row = result.summary().set_index("dmu_id").loc["O"]
    expected = _O_EXPECTED[account]
    targets = result.targets_for("O").set_index(["role", "variable"])
    peers = result.peers("O")

    assert set(targets["target_kind"]) == {"source_component_directional_target"}
    assert set(targets.index.get_level_values("role")) == {
        "input",
        "output",
        "bad_output",
    }
    expected_directions = {
        ("input", "fossil_energy"): (
            -2.0 if _ACCOUNT_WEIGHTS[account][0] > 0.0 else 0.0
        ),
        ("output", "electricity"): 1.0,
        ("bad_output", "co2"): (-4.0 if _ACCOUNT_WEIGHTS[account][2] > 0.0 else 0.0),
    }
    expected_targets = dict(zip(expected_directions, expected["target"], strict=True))
    beta_by_role = {
        "input": float(row["beta_fossil"]),
        "output": float(row["beta_electricity"]),
        "bad_output": float(row["beta_carbon"]),
    }
    for key, direction in expected_directions.items():
        target = targets.loc[key]
        assert target["direction"] == pytest.approx(direction)
        assert target["directional_change"] == pytest.approx(
            beta_by_role[key[0]] * direction
        )
        assert target["target"] == pytest.approx(expected_targets[key])
        assert _does_not_claim_unique(target["target_unique"])

    actual_intensities = dict(
        peers[["reference_dmu_id", "lambda"]].itertuples(index=False, name=None)
    )
    assert actual_intensities == pytest.approx(expected["intensities"])
    assert "O" not in actual_intensities
    variable_by_role = {
        "input": "fossil_energy",
        "output": "electricity",
        "bad_output": "co2",
    }
    for role, variable in variable_by_role.items():
        peer_activity = sum(
            intensity * float(source_frame.loc[peer, variable])
            for peer, intensity in actual_intensities.items()
        )
        assert targets.loc[(role, variable), "peer_activity"] == pytest.approx(
            peer_activity
        )
    assert targets.loc[("input", "fossil_energy"), "peer_activity"] <= (
        targets.loc[("input", "fossil_energy"), "target"] + 1e-10
    )
    assert targets.loc[("output", "electricity"), "peer_activity"] >= (
        targets.loc[("output", "electricity"), "target"] - 1e-10
    )
    assert targets.loc[("bad_output", "co2"), "peer_activity"] == pytest.approx(
        targets.loc[("bad_output", "co2"), "target"],
        abs=1e-10,
    )


@pytest.mark.parametrize("account", _ACCOUNTS)
def test_non_chp_source_accounts_are_unit_invariant(
    account: str,
) -> None:
    scales = {
        "fossil_energy": 1.0e4,
        "electricity": 2.5e-4,
        "co2": 3.7,
    }
    baseline = ZhouAngWangNonCHPEnergyCarbonDEA(account=account).fit(_source_data())
    rescaled = ZhouAngWangNonCHPEnergyCarbonDEA(account=account).fit(
        _source_data(
            fossil_scale=scales["fossil_energy"],
            electricity_scale=scales["electricity"],
            carbon_scale=scales["co2"],
        )
    )
    invariant_columns = [
        "directional_nonradial_distance",
        "performance_index",
        "beta_fossil",
        "beta_electricity",
        "beta_carbon",
    ]
    np.testing.assert_allclose(
        rescaled.summary()[invariant_columns],
        baseline.summary()[invariant_columns],
        atol=1e-10,
        rtol=0.0,
    )

    base_targets = baseline.targets.sort_values(
        ["dmu_id", "role", "variable"]
    ).reset_index(drop=True)
    scaled_targets = rescaled.targets.sort_values(
        ["dmu_id", "role", "variable"]
    ).reset_index(drop=True)
    target_scales = scaled_targets["variable"].map(scales).to_numpy()
    for column in (
        "observed",
        "direction",
        "directional_change",
        "target",
        "peer_activity",
    ):
        np.testing.assert_allclose(
            scaled_targets[column] / target_scales,
            base_targets[column],
            atol=1e-9,
            rtol=1e-10,
        )


def test_self_inclusion_is_visible_but_non_global_or_panel_use_is_unavailable() -> None:
    result = ZhouAngWangNonCHPEnergyCarbonDEA(account="energy").fit(_source_data())
    a_peers = result.peers("A")
    assert a_peers["reference_dmu_id"].tolist() == ["A"]
    assert a_peers["lambda"].iloc[0] == pytest.approx(1.0)

    panel_frame = load_dataset("zhou_ang_wang_non_chp_3")
    panel_frame["period"] = [1, 1, 2]
    panel = DEAData.from_frame(
        panel_frame,
        dmu="dmu",
        period="period",
        inputs="fossil_energy",
        outputs="electricity",
        bad_outputs="co2",
    )
    with pytest.raises(ModelSpecificationError, match="cross-section"):
        ZhouAngWangNonCHPEnergyCarbonDEA(account="energy").fit(panel)

    grouped_frame = load_dataset("zhou_ang_wang_non_chp_3")
    grouped_frame["technology_group"] = ["non_chp_a", "non_chp_a", "non_chp_b"]
    grouped = DEAData.from_frame(
        grouped_frame,
        dmu="dmu",
        group="technology_group",
        inputs="fossil_energy",
        outputs="electricity",
        bad_outputs="co2",
    )
    with pytest.raises(ModelSpecificationError, match="group comparison policy"):
        ZhouAngWangNonCHPEnergyCarbonDEA(account="energy").fit(grouped)

    with pytest.raises(TypeError, match="reference"):
        ZhouAngWangNonCHPEnergyCarbonDEA(  # type: ignore[call-arg]
            account="energy", reference="custom"
        )
    with pytest.raises(TypeError, match="returns_to_scale"):
        ZhouAngWangNonCHPEnergyCarbonDEA(  # type: ignore[call-arg]
            account="energy", returns_to_scale="vrs"
        )


def test_strict_one_by_one_by_one_positive_source_domain() -> None:
    base = load_dataset("zhou_ang_wang_non_chp_3")
    cases = (
        (
            DEAData.from_frame(
                base.assign(extra_input=1.0),
                dmu="dmu",
                inputs=("fossil_energy", "extra_input"),
                outputs="electricity",
                bad_outputs="co2",
            ),
            "exactly one input",
        ),
        (
            DEAData.from_frame(
                base.assign(extra_output=1.0),
                dmu="dmu",
                inputs="fossil_energy",
                outputs=("electricity", "extra_output"),
                bad_outputs="co2",
            ),
            "exactly one desirable output",
        ),
        (
            DEAData.from_frame(
                base.assign(extra_bad=1.0),
                dmu="dmu",
                inputs="fossil_energy",
                outputs="electricity",
                bad_outputs=("co2", "extra_bad"),
            ),
            "exactly one undesirable output",
        ),
        (
            DEAData.from_frame(
                base,
                dmu="dmu",
                inputs="fossil_energy",
                outputs="electricity",
            ),
            "exactly one undesirable output",
        ),
    )
    for data, message in cases:
        with pytest.raises(ModelSpecificationError, match=message):
            ZhouAngWangNonCHPEnergyCarbonDEA(account="energy").fit(data)

    for variable in ("fossil_energy", "electricity", "co2"):
        frame = base.copy()
        frame.loc[0, variable] = 0.0
        zero = DEAData.from_frame(
            frame,
            dmu="dmu",
            inputs="fossil_energy",
            outputs="electricity",
            bad_outputs="co2",
        )
        with pytest.raises(DataValidationError, match="strictly positive"):
            ZhouAngWangNonCHPEnergyCarbonDEA(account="energy").fit(zero)


def test_raw_optimum_is_identified_without_false_plan_uniqueness_claims() -> None:
    default = ZhouAngWangNonCHPEnergyCarbonDEA(account="integrated_energy_carbon").fit(
        _multiplicity_data()
    )
    row = default.summary().set_index("dmu_id").loc["O"]

    assert row["directional_nonradial_distance"] == pytest.approx(2.0 / 3.0)
    assert bool(row["ranking_value_valid"])
    assert _does_not_claim_unique(row["component_plan_unique"])
    assert _does_not_claim_unique(row["performance_index_identified"])
    assert _does_not_claim_unique(row["target_unique"])
    assert _does_not_claim_unique(row["peer_plan_unique"])
    assert default.targets_for("O")["target_unique"].map(_does_not_claim_unique).all()
    assert default.metadata["primary_solver_calls"] == 3
    assert default.metadata["multiplicity_solver_calls"] == 0
    assert default.metadata["solver_calls"] == 3

    diagnosed = ZhouAngWangNonCHPEnergyCarbonDEA(
        account="integrated_energy_carbon",
        diagnose_multiplicity=True,
    ).fit(_multiplicity_data())
    diagnosed_row = diagnosed.summary().set_index("dmu_id").loc["O"]
    assert diagnosed_row["directional_nonradial_distance"] == pytest.approx(2.0 / 3.0)
    assert not bool(diagnosed_row["component_plan_unique"])
    assert not bool(diagnosed_row["performance_index_identified"])
    assert not bool(diagnosed_row["target_unique"])
    assert _does_not_claim_unique(diagnosed_row["peer_plan_unique"])
    assert diagnosed_row["beta_fossil_lower"] == pytest.approx(0.0)
    assert diagnosed_row["beta_fossil_upper"] == pytest.approx(1.0 / 2.0)
    assert diagnosed_row["beta_electricity_lower"] == pytest.approx(3.0 / 2.0)
    assert diagnosed_row["beta_electricity_upper"] == pytest.approx(2.0)
    assert diagnosed_row["beta_carbon_lower"] == pytest.approx(0.0)
    assert diagnosed_row["beta_carbon_upper"] == pytest.approx(0.0)
    assert diagnosed_row["performance_index_lower"] == pytest.approx(3.0 / 10.0)
    assert diagnosed_row["performance_index_upper"] == pytest.approx(1.0 / 3.0)
    assert not diagnosed.targets_for("O")["target_unique"].any()
    assert diagnosed.metadata["primary_solver_calls"] == 3
    assert diagnosed.metadata["multiplicity_solver_calls"] == 18
    assert diagnosed.metadata["solver_calls"] == 21


def test_solver_limit_and_missing_dual_certificate_fail_closed() -> None:
    limited = ZhouAngWangNonCHPEnergyCarbonDEA(
        account="energy", solver=_AlwaysLimitSolver()
    ).fit(_source_data())
    missing_duals = ZhouAngWangNonCHPEnergyCarbonDEA(
        account="energy", solver=_MissingDualCertificateSolver()
    ).fit(_source_data())

    assert set(limited.summary()["solver_status"]) == {SolverStatus.LIMIT_REACHED.value}
    assert limited.summary()["score"].isna().all()
    assert limited.summary()["distance"].isna().all()
    assert set(limited.diagnostics["iterations"]) == {3}
    assert not limited.diagnostics["postsolve_certified"].any()

    assert set(missing_duals.summary()["solver_status"]) == {SolverStatus.FAILED.value}
    assert missing_duals.summary()["score"].isna().all()
    assert missing_duals.summary()["distance"].isna().all()
    assert set(missing_duals.diagnostics["solver_status"]) == {
        SolverStatus.OPTIMAL.value
    }
    assert not missing_duals.diagnostics["postsolve_certified"].any()
    assert limited.targets.empty and limited.intensities.empty
    assert missing_duals.targets.empty and missing_duals.intensities.empty


def test_invalid_account_and_numerical_configuration_are_rejected() -> None:
    with pytest.raises(TypeError, match="account"):
        ZhouAngWangNonCHPEnergyCarbonDEA()  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="account"):
        ZhouAngWangNonCHPEnergyCarbonDEA(account="custom")
    with pytest.raises(ValueError, match="pass solver or solver_options"):
        ZhouAngWangNonCHPEnergyCarbonDEA(
            account="energy",
            solver=_AlwaysLimitSolver(),
            solver_options=SolverOptions(),
        )
    for value in (0.0, -1.0, np.inf, np.nan):
        with pytest.raises(ValueError, match="tolerance must be positive"):
            ZhouAngWangNonCHPEnergyCarbonDEA(account="energy", tolerance=value)
        with pytest.raises(ValueError, match="peer_tolerance must be positive"):
            ZhouAngWangNonCHPEnergyCarbonDEA(
                account="energy",
                peer_tolerance=value,
            )
