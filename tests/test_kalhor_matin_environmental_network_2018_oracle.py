"""Independent numerical oracles for Kalhor and Kazemi Matin (2018).

Primary source: https://doi.org/10.1051/ro/2017022
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import linprog
from scipy.sparse import issparse

from deapack import ReferenceSpec, SolverStatus, load_dataset
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.network.environmental import KalhorKazemiMatinNetworkDEA
from deapack.network.environmental_data import (
    EnvironmentalNetworkData,
    EnvironmentalNetworkSpec,
)
from deapack.network.specs import LinkSpec, NetworkSpec, ProcessSpec, TwoStageSeriesSpec
from deapack.solvers import LPSolution, SciPyHiGHSSolver


@dataclass(frozen=True)
class _OracleSolution:
    score: float
    process_ids: tuple[str, ...]
    reference_rows: np.ndarray
    alpha: np.ndarray
    beta: np.ndarray
    input_targets: dict[str, float]
    desirable_targets: dict[str, float]
    undesirable_targets: dict[str, float]
    intermediate_targets: dict[tuple[str, str], float]


class _AuditingSolver:
    name = "kalhor-matin-environmental-network-auditing-fixture"

    def __init__(self) -> None:
        self.calls = 0
        self.problems = []
        self._delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        self.problems.append(problem)
        return self._delegate.solve(problem)


def _recovery_frame() -> pd.DataFrame:
    return load_dataset("environmental_recovery_chain").rename(
        columns={
            "unit": "dmu",
            "resource_input": "input",
            "sorted_material": "intermediate",
            "recovered_service": "desirable_output",
            "residual_load": "undesirable_output",
        }
    )


def _circular_frame() -> pd.DataFrame:
    return load_dataset("environmental_circular_chain").rename(
        columns={
            "unit": "dmu",
            "energy_units": "input_1",
            "labor_units": "input_2",
            "material_12": "intermediate_1_12",
            "material_23": "intermediate_1_23",
            "material_34": "intermediate_1_34",
            "support_12": "intermediate_2_12",
            "support_23": "intermediate_2_23",
            "support_34": "intermediate_2_34",
            "circular_service": "desirable_output",
            "residual_load": "undesirable_output",
        }
    )


def _two_stage_data(frame: pd.DataFrame) -> EnvironmentalNetworkData:
    graph = TwoStageSeriesSpec(
        inputs="input",
        intermediates="intermediate",
        outputs=("desirable_output", "undesirable_output"),
    )
    spec = EnvironmentalNetworkSpec(
        network_spec=graph,
        input_accounts="input",
        desirable_output_accounts="desirable_output",
        undesirable_output_accounts="undesirable_output",
    )
    return EnvironmentalNetworkData.from_frame(
        frame,
        spec=spec,
        dmu="dmu",
    )


def _four_process_data(frame: pd.DataFrame) -> EnvironmentalNetworkData:
    chain_1 = (
        "intermediate_1_12",
        "intermediate_1_23",
        "intermediate_1_34",
    )
    chain_2 = (
        "intermediate_2_12",
        "intermediate_2_23",
        "intermediate_2_34",
    )
    graph = NetworkSpec(
        processes=(
            ProcessSpec(
                "process_1",
                inputs=("input_1", "input_2"),
                outputs=(chain_1[0], chain_2[0]),
            ),
            ProcessSpec(
                "process_2",
                inputs=(chain_1[0], chain_2[0]),
                outputs=(chain_1[1], chain_2[1]),
            ),
            ProcessSpec(
                "process_3",
                inputs=(chain_1[1], chain_2[1]),
                outputs=(chain_1[2], chain_2[2]),
            ),
            ProcessSpec(
                "process_4",
                inputs=(chain_1[2], chain_2[2]),
                outputs=("desirable_output", "undesirable_output"),
            ),
        ),
        links=(
            LinkSpec(
                "process_1_to_process_2",
                source="process_1",
                target="process_2",
                variables=(chain_1[0], chain_2[0]),
            ),
            LinkSpec(
                "process_2_to_process_3",
                source="process_2",
                target="process_3",
                variables=(chain_1[1], chain_2[1]),
            ),
            LinkSpec(
                "process_3_to_process_4",
                source="process_3",
                target="process_4",
                variables=(chain_1[2], chain_2[2]),
            ),
        ),
    )
    spec = EnvironmentalNetworkSpec(
        network_spec=graph,
        input_accounts=("input_1", "input_2"),
        desirable_output_accounts="desirable_output",
        undesirable_output_accounts="undesirable_output",
        intermediate_accounts={
            "intermediate_1": chain_1,
            "intermediate_2": chain_2,
        },
    )
    return EnvironmentalNetworkData.from_frame(
        frame,
        spec=spec,
        dmu="dmu",
    )


def _cyclic_internal_output_data() -> EnvironmentalNetworkData:
    frame = pd.DataFrame(
        {
            "dmu": list("ABC"),
            "input": [4.0, 2.0, 3.0],
            "treatment": [1.2, 1.0, 1.4],
            "forward_material": [2.0, 1.0, 1.6],
            "direct_material": [0.5, 0.4, 0.6],
            "internal_service": [3.0, 2.0, 2.4],
            "internal_residual": [1.0, 1.4, 1.1],
            "conversion_final_service": [0.6, 0.5, 0.7],
            "conversion_final_residual": [0.3, 0.4, 0.35],
            "final_service": [4.0, 2.5, 3.2],
            "final_residual": [1.5, 1.0, 1.2],
            "returned_material": [0.8, 0.5, 0.7],
        }
    )
    graph = NetworkSpec(
        processes=(
            ProcessSpec(
                "production",
                inputs=("input", "returned_material"),
                outputs=("forward_material", "direct_material"),
            ),
            ProcessSpec(
                "conversion",
                inputs="forward_material",
                outputs=(
                    "internal_service",
                    "internal_residual",
                    "conversion_final_service",
                    "conversion_final_residual",
                ),
            ),
            ProcessSpec(
                "delivery_and_treatment",
                inputs=(
                    "internal_service",
                    "internal_residual",
                    "direct_material",
                    "treatment",
                ),
                outputs=(
                    "final_service",
                    "final_residual",
                    "returned_material",
                ),
            ),
        ),
        links=(
            LinkSpec(
                "forward_material",
                "production",
                "conversion",
                "forward_material",
            ),
            LinkSpec(
                "direct_material",
                "production",
                "delivery_and_treatment",
                "direct_material",
            ),
            LinkSpec(
                "internal_service",
                "conversion",
                "delivery_and_treatment",
                "internal_service",
            ),
            LinkSpec(
                "internal_residual",
                "conversion",
                "delivery_and_treatment",
                "internal_residual",
            ),
            LinkSpec(
                "returned_material",
                "delivery_and_treatment",
                "production",
                "returned_material",
            ),
        ),
    )
    specification = EnvironmentalNetworkSpec(
        network_spec=graph,
        input_accounts=("input", "treatment"),
        desirable_output_accounts={
            "service": (
                "internal_service",
                "conversion_final_service",
                "final_service",
            )
        },
        undesirable_output_accounts={
            "residual": (
                "internal_residual",
                "conversion_final_residual",
                "final_residual",
            )
        },
        intermediate_accounts={
            "material": (
                "forward_material",
                "direct_material",
                "returned_material",
            )
        },
    )
    return EnvironmentalNetworkData.from_frame(
        frame,
        spec=specification,
        dmu="dmu",
    )


def _dense_equation_oracle(
    data: EnvironmentalNetworkData,
    *,
    returns_to_scale: str,
    reference_rows: tuple[int, ...] | None = None,
) -> list[_OracleSolution]:
    """Compile Kalhor--Kazemi Matin (2018), equations (3.2)--(3.4).

    This oracle deliberately builds ordinary dense NumPy matrices and calls
    SciPy's public ``linprog`` directly. It does not use the production model's
    private layout, reference compiler, LP builder, or result helpers.
    """

    rows = np.asarray(
        tuple(range(data.n_dmus)) if reference_rows is None else reference_rows,
        dtype=np.int64,
    )
    process_ids = tuple(
        sorted(process.process_id for process in data.network_spec.processes)
    )
    process_position = {
        process_id: position for position, process_id in enumerate(process_ids)
    }
    bad_processes = {
        owner.producer_process
        for owner in data.spec.ownership
        if owner.semantic_role == "undesirable_output"
        and owner.producer_process is not None
    }
    n_reference = len(rows)

    alpha_index: dict[tuple[str, int], int] = {}
    beta_index: dict[tuple[str, int], int] = {}
    cursor = 0
    for process_id in process_ids:
        for local_reference in range(n_reference):
            alpha_index[process_id, local_reference] = cursor
            cursor += 1
    for process_id in process_ids:
        if process_id not in bad_processes:
            continue
        for local_reference in range(n_reference):
            beta_index[process_id, local_reference] = cursor
            cursor += 1
    h_index = cursor
    n_variables = h_index + 1

    positions = {
        variable: position for position, variable in enumerate(data.variable_names)
    }

    def reference_values(variable: str) -> np.ndarray:
        return data.values[rows, positions[variable]]

    def observed_account(
        observation: int,
        variables: tuple[str, ...],
        *,
        external_only: bool,
    ) -> float:
        selected = (
            tuple(
                variable
                for variable in variables
                if data.spec.variable_owner(variable).occurrence_kind
                == "external_output"
            )
            if external_only
            else variables
        )
        return float(
            sum(data.values[observation, positions[variable]] for variable in selected)
        )

    def add_activity(
        row: np.ndarray,
        process_id: str,
        local_reference: int,
        coefficient: float,
        *,
        include_beta: bool,
    ) -> None:
        row[alpha_index[process_id, local_reference]] += coefficient
        if include_beta and (process_id, local_reference) in beta_index:
            row[beta_index[process_id, local_reference]] += coefficient

    inequality_template_rows: list[np.ndarray] = []
    inequality_template_bounds: list[float] = []
    equality_template_rows: list[np.ndarray] = []
    equality_template_bounds: list[float] = []

    for _, variables in data.spec.input_accounts:
        row = np.zeros(n_variables, dtype=np.float64)
        for variable in variables:
            owner = data.spec.variable_owner(variable)
            assert owner.consumer_process is not None
            values = reference_values(variable)
            for local_reference, value in enumerate(values):
                add_activity(
                    row,
                    owner.consumer_process,
                    local_reference,
                    float(value),
                    include_beta=True,
                )
        inequality_template_rows.append(row)
        inequality_template_bounds.append(0.0)

    for _, variables in data.spec.desirable_output_accounts:
        row = np.zeros(n_variables, dtype=np.float64)
        for variable in variables:
            owner = data.spec.variable_owner(variable)
            values = reference_values(variable)
            assert owner.producer_process is not None
            for local_reference, value in enumerate(values):
                add_activity(
                    row,
                    owner.producer_process,
                    local_reference,
                    -float(value),
                    include_beta=False,
                )
                if owner.consumer_process is not None:
                    add_activity(
                        row,
                        owner.consumer_process,
                        local_reference,
                        float(value),
                        include_beta=False,
                    )
        inequality_template_rows.append(row)
        inequality_template_bounds.append(np.nan)

    for _, variables in data.spec.undesirable_output_accounts:
        row = np.zeros(n_variables, dtype=np.float64)
        for variable in variables:
            owner = data.spec.variable_owner(variable)
            values = reference_values(variable)
            assert owner.producer_process is not None
            for local_reference, value in enumerate(values):
                add_activity(
                    row,
                    owner.producer_process,
                    local_reference,
                    float(value),
                    include_beta=False,
                )
                if owner.consumer_process is not None:
                    add_activity(
                        row,
                        owner.consumer_process,
                        local_reference,
                        -float(value),
                        include_beta=False,
                    )
        equality_template_rows.append(row)
        equality_template_bounds.append(np.nan)

    intermediate_groups: list[tuple[str, str, tuple[str, ...]]] = []
    for account_id, variables in data.spec.intermediate_accounts:
        variables_by_producer: dict[str, list[str]] = {}
        for variable in variables:
            owner = data.spec.variable_owner(variable)
            assert owner.producer_process is not None
            variables_by_producer.setdefault(owner.producer_process, []).append(
                variable
            )
        for producer_process, grouped_variables in sorted(
            variables_by_producer.items()
        ):
            resolved_variables = tuple(sorted(grouped_variables))
            intermediate_groups.append(
                (account_id, producer_process, resolved_variables)
            )
            row = np.zeros(n_variables, dtype=np.float64)
            for variable in resolved_variables:
                owner = data.spec.variable_owner(variable)
                assert owner.consumer_process is not None
                values = reference_values(variable)
                for local_reference, value in enumerate(values):
                    add_activity(
                        row,
                        producer_process,
                        local_reference,
                        -float(value),
                        include_beta=False,
                    )
                    add_activity(
                        row,
                        owner.consumer_process,
                        local_reference,
                        float(value),
                        include_beta=True,
                    )
            inequality_template_rows.append(row)
            inequality_template_bounds.append(0.0)

    for process_id in process_ids:
        row = np.zeros(n_variables, dtype=np.float64)
        for local_reference in range(n_reference):
            add_activity(
                row,
                process_id,
                local_reference,
                1.0,
                include_beta=True,
            )
        if returns_to_scale == "vrs":
            equality_template_rows.append(row)
            equality_template_bounds.append(1.0)
        elif returns_to_scale == "nirs":
            inequality_template_rows.append(row)
            inequality_template_bounds.append(1.0)
        elif returns_to_scale == "ndrs":
            inequality_template_rows.append(-row)
            inequality_template_bounds.append(-1.0)
        elif returns_to_scale != "crs":
            raise ValueError(f"unsupported oracle RTS: {returns_to_scale!r}")

    objective = np.zeros(n_variables, dtype=np.float64)
    objective[h_index] = 1.0
    bounds = [(0.0, None)] * n_variables
    solutions: list[_OracleSolution] = []

    n_input_accounts = len(data.spec.input_accounts)
    for observation in range(data.n_dmus):
        inequality_rows = [row.copy() for row in inequality_template_rows]
        inequality_bounds = list(inequality_template_bounds)
        equality_rows = [row.copy() for row in equality_template_rows]
        equality_bounds = list(equality_template_bounds)

        for account_position, (_, variables) in enumerate(data.spec.input_accounts):
            inequality_rows[account_position][h_index] = -observed_account(
                observation,
                variables,
                external_only=False,
            )

        desirable_offset = n_input_accounts
        for account_position, (_, variables) in enumerate(
            data.spec.desirable_output_accounts
        ):
            inequality_bounds[desirable_offset + account_position] = -observed_account(
                observation,
                variables,
                external_only=True,
            )

        for account_position, (_, variables) in enumerate(
            data.spec.undesirable_output_accounts
        ):
            equality_bounds[account_position] = observed_account(
                observation,
                variables,
                external_only=True,
            )

        result = linprog(
            c=objective,
            A_ub=(np.vstack(inequality_rows) if inequality_rows else None),
            b_ub=(
                np.asarray(inequality_bounds, dtype=np.float64)
                if inequality_rows
                else None
            ),
            A_eq=(np.vstack(equality_rows) if equality_rows else None),
            b_eq=(
                np.asarray(equality_bounds, dtype=np.float64) if equality_rows else None
            ),
            bounds=bounds,
            method="highs",
        )
        assert result.success, result.message
        assert result.x is not None
        primal = np.asarray(result.x, dtype=np.float64)

        alpha = np.zeros(
            (len(process_ids), n_reference),
            dtype=np.float64,
        )
        beta = np.zeros_like(alpha)
        for process_id in process_ids:
            process = process_position[process_id]
            for local_reference in range(n_reference):
                alpha[process, local_reference] = primal[
                    alpha_index[process_id, local_reference]
                ]
                beta_position = beta_index.get((process_id, local_reference))
                if beta_position is not None:
                    beta[process, local_reference] = primal[beta_position]

        input_targets: dict[str, float] = {}
        for account_id, variables in data.spec.input_accounts:
            target = 0.0
            for variable in variables:
                owner = data.spec.variable_owner(variable)
                assert owner.consumer_process is not None
                process = process_position[owner.consumer_process]
                target += float(
                    (alpha[process] + beta[process]) @ reference_values(variable)
                )
            input_targets[account_id] = target

        desirable_targets: dict[str, float] = {}
        for account_id, variables in data.spec.desirable_output_accounts:
            target = 0.0
            for variable in variables:
                owner = data.spec.variable_owner(variable)
                assert owner.producer_process is not None
                target += float(
                    alpha[process_position[owner.producer_process]]
                    @ reference_values(variable)
                )
                if owner.consumer_process is not None:
                    target -= float(
                        alpha[process_position[owner.consumer_process]]
                        @ reference_values(variable)
                    )
            desirable_targets[account_id] = target

        undesirable_targets: dict[str, float] = {}
        for account_id, variables in data.spec.undesirable_output_accounts:
            target = 0.0
            for variable in variables:
                owner = data.spec.variable_owner(variable)
                assert owner.producer_process is not None
                target += float(
                    alpha[process_position[owner.producer_process]]
                    @ reference_values(variable)
                )
                if owner.consumer_process is not None:
                    target -= float(
                        alpha[process_position[owner.consumer_process]]
                        @ reference_values(variable)
                    )
            undesirable_targets[account_id] = target

        intermediate_targets: dict[tuple[str, str], float] = {}
        for account_id, producer_process, variables in intermediate_groups:
            process = process_position[producer_process]
            intermediate_targets[account_id, producer_process] = float(
                sum(
                    alpha[process] @ reference_values(variable)
                    for variable in variables
                )
            )

        solutions.append(
            _OracleSolution(
                score=float(primal[h_index]),
                process_ids=process_ids,
                reference_rows=rows.copy(),
                alpha=alpha,
                beta=beta,
                input_targets=input_targets,
                desirable_targets=desirable_targets,
                undesirable_targets=undesirable_targets,
                intermediate_targets=intermediate_targets,
            )
        )

    return solutions


def _public_scores(result) -> np.ndarray:  # type: ignore[no-untyped-def]
    return result.summary()["score"].to_numpy(dtype=np.float64)


def _public_intensity_vector(
    result,  # type: ignore[no-untyped-def]
    *,
    dmu_id: str,
    process_id: str,
    field: str,
    reference_ids: tuple[str, ...],
) -> np.ndarray:
    rows = result.intensities[
        (result.intensities["dmu_id"] == dmu_id)
        & (result.intensities["process_id"] == process_id)
    ]
    by_reference = rows.set_index("reference_dmu_id")[field].to_dict()
    return np.asarray(
        [float(by_reference.get(reference_id, 0.0)) for reference_id in reference_ids]
    )


def test_project_recovery_vrs_matches_dense_oracle_and_sparse_model() -> None:
    frame = _recovery_frame()
    data = _two_stage_data(frame)
    oracle = _dense_equation_oracle(data, returns_to_scale="vrs")
    expected_scores = np.asarray([solution.score for solution in oracle])

    solver = _AuditingSolver()
    result = KalhorKazemiMatinNetworkDEA(
        returns_to_scale="vrs",
        solver=solver,
    ).fit(data)

    assert _public_scores(result) == pytest.approx(expected_scores, abs=1e-10)
    assert result.targets["target"].notna().all()
    assert result.intensities[["alpha", "beta"]].notna().all().all()

    assert solver.calls == data.n_dmus
    assert result.metadata["primary_programmes_solved"] == data.n_dmus
    assert result.metadata["compiled_reference_sets"] == 1
    assert all(
        issparse(matrix)
        for problem in solver.problems
        for matrix in (problem.a_ub, problem.a_eq)
        if matrix is not None
    )


def test_project_circular_crs_scores_match_independent_oracle() -> None:
    frame = _circular_frame()
    data = _four_process_data(frame)
    oracle = _dense_equation_oracle(data, returns_to_scale="crs")
    expected = np.asarray([solution.score for solution in oracle])
    result = KalhorKazemiMatinNetworkDEA(returns_to_scale="crs").fit(data)
    assert _public_scores(result) == pytest.approx(expected, abs=1e-10)


def test_whole_account_unit_changes_leave_scores_unchanged() -> None:
    frame = _circular_frame()
    baseline_data = _four_process_data(frame)
    scaled = frame.copy()
    account_factors = {
        "input_1": 7.0,
        "input_2": 0.25,
        "intermediate_1": 3.0,
        "intermediate_2": 11.0,
        "desirable_output": 0.1,
        "undesirable_output": 17.0,
    }
    for account_id, factor in account_factors.items():
        for variable in baseline_data.spec.variables_for_account(account_id):
            scaled[variable] *= factor
    scaled_data = _four_process_data(scaled)

    baseline_oracle = _dense_equation_oracle(
        baseline_data,
        returns_to_scale="crs",
    )
    scaled_oracle = _dense_equation_oracle(
        scaled_data,
        returns_to_scale="crs",
    )
    baseline_expected = [solution.score for solution in baseline_oracle]
    scaled_expected = [solution.score for solution in scaled_oracle]
    assert scaled_expected == pytest.approx(baseline_expected, abs=1e-11)

    baseline_public = KalhorKazemiMatinNetworkDEA(returns_to_scale="crs").fit(
        baseline_data
    )
    scaled_public = KalhorKazemiMatinNetworkDEA(returns_to_scale="crs").fit(scaled_data)
    assert _public_scores(scaled_public) == pytest.approx(
        _public_scores(baseline_public),
        abs=1e-10,
    )
    assert _public_scores(scaled_public) == pytest.approx(
        scaled_expected,
        abs=1e-10,
    )


@pytest.mark.parametrize("returns_to_scale", ["vrs", "crs", "nirs", "ndrs"])
def test_all_public_returns_to_scale_contracts_match_dense_oracle(
    returns_to_scale: str,
) -> None:
    data = _two_stage_data(_recovery_frame())
    oracle = _dense_equation_oracle(
        data,
        returns_to_scale=returns_to_scale,
    )
    result = KalhorKazemiMatinNetworkDEA(returns_to_scale=returns_to_scale).fit(data)
    summary = result.summary()

    assert set(summary["solver_status"]) == {"optimal"}
    assert np.isfinite(summary["score"]).all()
    assert set(summary["returns_to_scale"]) == {returns_to_scale}
    assert summary["score"].to_numpy() == pytest.approx(
        [solution.score for solution in oracle],
        abs=1e-10,
    )


def test_cyclic_internal_good_bad_and_intermediate_accounts_match_oracle() -> None:
    data = _cyclic_internal_output_data()
    oracle = _dense_equation_oracle(data, returns_to_scale="vrs")
    result = KalhorKazemiMatinNetworkDEA(returns_to_scale="vrs").fit(data)

    assert _public_scores(result) == pytest.approx(
        [solution.score for solution in oracle],
        abs=1e-10,
    )
    assert set(result.links["flow_kind"]) == {
        "desirable_output",
        "intermediate",
        "undesirable_output",
    }
    environmental_links = result.links[
        result.links["flow_kind"].isin(("desirable_output", "undesirable_output"))
    ]
    assert not environmental_links["balance_is_link_specific"].any()
    pooled_material = result.links[
        (result.links["flow_kind"] == "intermediate")
        & (result.links["source_process"] == "production")
    ]
    assert set(pooled_material["balance_scope"]) == {"producer_product_account"}
    assert not pooled_material["balance_is_link_specific"].any()
    assert (pooled_material["account_balance_surplus"] >= -1e-10).all()
    assert result.metadata["expanded_spec"]["graph"]["cycles_permitted"] is True
    assert set(result.summary()["solver_status"]) == {"optimal"}


def test_custom_reference_excludes_c_without_silent_peer_reentry() -> None:
    data = _two_stage_data(_recovery_frame())
    reference_rows = (0, 1)
    oracle = _dense_equation_oracle(
        data,
        returns_to_scale="vrs",
        reference_rows=reference_rows,
    )
    result = KalhorKazemiMatinNetworkDEA(
        returns_to_scale="vrs",
        reference=ReferenceSpec(
            kind="custom",
            custom_rows=reference_rows,
        ),
    ).fit(data)
    summary = result.summary().set_index("dmu_id")

    assert summary["reference_size"].tolist() == [2] * data.n_dmus
    assert summary["score"].to_numpy() == pytest.approx(
        [solution.score for solution in oracle],
        abs=1e-10,
    )
    assert summary.loc["input_drag", "score"] == pytest.approx(
        oracle[2].score,
        abs=1e-10,
    )
    c_intensities = result.intensities[result.intensities["dmu_id"] == "input_drag"]
    assert set(c_intensities["reference_dmu_id"]) <= {"base", "scale_2"}
    assert "input_drag" not in set(c_intensities["reference_dmu_id"])
    assert result.metadata["expanded_spec"]["reference"]["kind"] == "custom"
    assert result.metadata["expanded_spec"]["reference"]["custom_rows"]["count"] == 2


class _AlwaysFailSolver:
    name = "always-fail"

    def solve(self, problem):  # type: ignore[no-untyped-def]
        del problem
        return LPSolution(
            status=SolverStatus.FAILED,
            objective=None,
            primal=None,
            message="injected failure",
            iterations=None,
        )


def test_solver_failure_withholds_all_canonical_outputs() -> None:
    data = _two_stage_data(_recovery_frame())
    result = KalhorKazemiMatinNetworkDEA(solver=_AlwaysFailSolver()).fit(data)

    assert result.summary()["system_efficiency"].isna().all()
    assert result.summary()["is_efficient"].isna().all()
    assert result.targets.empty
    assert result.intensities.empty
    assert result.links.empty
    assert result.components.empty
    assert result.diagnostics["certification_status"].eq("failed").all()


def test_model_enforces_source_output_and_nonnegative_domain() -> None:
    negative = _recovery_frame()
    negative.loc[0, "input"] = -1.0
    with pytest.raises(DataValidationError, match="nonnegative quantities"):
        KalhorKazemiMatinNetworkDEA().fit(_two_stage_data(negative))

    no_positive_final_good = _recovery_frame()
    no_positive_final_good["desirable_output"] = 0.0
    with pytest.raises(
        ModelSpecificationError,
        match=r"desirable output account.*no positive final observation",
    ):
        KalhorKazemiMatinNetworkDEA().fit(_two_stage_data(no_positive_final_good))

    graph = NetworkSpec(
        processes=(
            ProcessSpec("first", "input", "internal_good"),
            ProcessSpec("second", "internal_good", "final_bad"),
        ),
        links=(LinkSpec("good", "first", "second", "internal_good"),),
    )
    specification = EnvironmentalNetworkSpec(
        network_spec=graph,
        input_accounts="input",
        desirable_output_accounts="internal_good",
        undesirable_output_accounts="final_bad",
    )
    purely_internal_good = EnvironmentalNetworkData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "input": [1.0, 2.0],
                "internal_good": [1.0, 1.5],
                "final_bad": [1.0, 0.5],
            }
        ),
        spec=specification,
        dmu="dmu",
    )
    with pytest.raises(
        ModelSpecificationError,
        match=r"desirable output account.*no final output leaving the network",
    ):
        KalhorKazemiMatinNetworkDEA().fit(purely_internal_good)


@pytest.mark.parametrize("role", ("desirable", "undesirable"))
@pytest.mark.parametrize(
    ("include_zero_final", "expected_reason"),
    (
        (False, "has no final output leaving the network"),
        (True, "has no positive final observation"),
    ),
)
def test_source_gate_rejects_mixed_account_final_output_loophole(
    role: str,
    include_zero_final: bool,
    expected_reason: str,
) -> None:
    upstream_outputs = ("internal_target", "upstream_control")
    target_members = ("internal_target", "final_target")
    if include_zero_final:
        upstream_outputs += ("upstream_final_target",)
        target_members += ("upstream_final_target",)
    graph = NetworkSpec(
        processes=(
            ProcessSpec(
                "upstream",
                "input",
                upstream_outputs,
            ),
            ProcessSpec(
                "downstream",
                ("internal_target", "treatment"),
                ("final_target", "downstream_control"),
            ),
        ),
        links=(
            LinkSpec(
                "target_handoff",
                "upstream",
                "downstream",
                "internal_target",
            ),
        ),
    )
    target_account = {"target": target_members}
    control_account = {"control": ("upstream_control", "downstream_control")}
    specification = EnvironmentalNetworkSpec(
        network_spec=graph,
        input_accounts=("input", "treatment"),
        desirable_output_accounts=(
            target_account if role == "desirable" else control_account
        ),
        undesirable_output_accounts=(
            target_account if role == "undesirable" else control_account
        ),
    )
    observations = {
        "dmu": ["A", "B"],
        "input": [2.0, 3.0],
        "treatment": [0.5, 0.7],
        "internal_target": [1.0, 1.4],
        "final_target": [0.8, 1.1],
        "upstream_control": [0.3, 0.4],
        "downstream_control": [0.2, 0.25],
    }
    if include_zero_final:
        observations["upstream_final_target"] = [0.0, 0.0]
    data = EnvironmentalNetworkData.from_frame(
        pd.DataFrame(observations),
        spec=specification,
        dmu="dmu",
    )

    with pytest.raises(
        ModelSpecificationError,
        match=(
            rf"{role} output account 'target' for producer process "
            rf"'upstream' {expected_reason}"
        ),
    ):
        KalhorKazemiMatinNetworkDEA().fit(data)


def test_metadata_preserves_method_identity_and_source_boundary() -> None:
    data = _two_stage_data(_recovery_frame())
    result = KalhorKazemiMatinNetworkDEA().fit(data)

    assert result.metadata["method_id"] == (
        "network.environmental.weak_activity_specific.kalhor_kazemi_matin_2018"
    )
    assert result.metadata["semantic_fingerprint"] == data.semantic_fingerprint
    assert result.metadata["source_boundary"] == {
        "technology": "Kalhor_Kazemi_Matin_2018_equation_3_2",
        "measure": "input_radial_equations_3_3_to_3_4",
        "directional_distance_variant": "deferred_to_next_version",
        "process_efficiencies": "not_defined",
    }
    assert result.metadata["score_semantics"]["native"] == "h"
    assert (
        result.metadata["expanded_spec"]["technology"]["family"]
        == "general_network_activity_specific_weak_disposal"
    )
