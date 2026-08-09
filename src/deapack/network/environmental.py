"""General-network environmental DEA with activity-specific weak disposal."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix, diags, hstack, lil_matrix

from .._registry import reference_spec as registry_reference_spec
from .._registry import registry_metadata
from ..enums import ReturnsToScale, SolverStatus, parse_enum
from ..exceptions import ModelSpecificationError
from ..results import DEAResult
from ..solvers import LinearProgram, LPSolver, SciPyHiGHSSolver
from ..specs import ReferenceSpec, SolverOptions
from ..technology import build_reference_plan
from .environmental_data import (
    EnvironmentalNetworkData,
    EnvironmentalNetworkSpec,
)
from .fare_grosskopf import _certify_lp_solution, _diagnostic


@dataclass(frozen=True, slots=True)
class _EnvironmentalNetworkLayout:
    process_ids: tuple[str, ...]
    process_index: dict[str, int]
    bad_processes: frozenset[str]
    alpha_slices: tuple[slice, ...]
    beta_slices: tuple[slice | None, ...]
    h_index: int

    @property
    def n_processes(self) -> int:
        return len(self.process_ids)

    @property
    def size_without_h(self) -> int:
        return self.h_index

    @property
    def size(self) -> int:
        return self.h_index + 1


@dataclass(frozen=True, slots=True)
class _IntermediateRow:
    account_id: str
    producer_process: str
    variables: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _CompiledEnvironmentalNetworkReference:
    rows: np.ndarray
    layout: _EnvironmentalNetworkLayout
    a_ub_without_h: csc_matrix
    a_eq_without_h: csc_matrix | None
    ub_reference_scales: np.ndarray
    eq_reference_scales: np.ndarray
    intermediate_rows: tuple[_IntermediateRow, ...]
    rts_ub_count: int
    rts_eq_count: int

    @property
    def size(self) -> int:
        return int(self.rows.size)


def _layout(
    spec: EnvironmentalNetworkSpec,
    n_reference: int,
) -> _EnvironmentalNetworkLayout:
    process_ids = tuple(
        sorted(process.process_id for process in spec.network_spec.processes)
    )
    process_index = {
        process_id: position for position, process_id in enumerate(process_ids)
    }
    bad_processes = frozenset(
        owner.producer_process
        for owner in spec.ownership
        if owner.semantic_role == "undesirable_output"
        and owner.producer_process is not None
    )

    cursor = 0
    alpha_slices: list[slice] = []
    for _ in process_ids:
        alpha_slices.append(slice(cursor, cursor + n_reference))
        cursor += n_reference

    beta_slices: list[slice | None] = []
    for process_id in process_ids:
        if process_id in bad_processes:
            beta_slices.append(slice(cursor, cursor + n_reference))
            cursor += n_reference
        else:
            beta_slices.append(None)

    return _EnvironmentalNetworkLayout(
        process_ids=process_ids,
        process_index=process_index,
        bad_processes=bad_processes,
        alpha_slices=tuple(alpha_slices),
        beta_slices=tuple(beta_slices),
        h_index=cursor,
    )


def _column_positions(data: EnvironmentalNetworkData) -> dict[str, int]:
    return {name: position for position, name in enumerate(data.variable_names)}


def _reference_values(
    data: EnvironmentalNetworkData,
    rows: np.ndarray,
    positions: dict[str, int],
    variables: tuple[str, ...],
) -> np.ndarray:
    columns = [positions[variable] for variable in variables]
    if not columns:
        return np.zeros(rows.size, dtype=np.float64)
    return np.asarray(data.values[np.ix_(rows, columns)].sum(axis=1), dtype=float)


def _variables_owned_by(
    spec: EnvironmentalNetworkSpec,
    variables: tuple[str, ...],
    process_id: str,
) -> tuple[str, ...]:
    return tuple(
        variable
        for variable in variables
        if spec.variable_owner(variable).producer_process == process_id
        or (
            spec.variable_owner(variable).semantic_role == "input"
            and spec.variable_owner(variable).consumer_process == process_id
        )
    )


def _external_variables(
    spec: EnvironmentalNetworkSpec,
    variables: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(
        variable
        for variable in variables
        if spec.variable_owner(variable).occurrence_kind != "link"
    )


def _positive_scale(*values: np.ndarray | float) -> float:
    scale = 0.0
    for value in values:
        array = np.asarray(value, dtype=np.float64)
        scale = max(scale, float(np.abs(array).max(initial=0.0)))
    return max(scale, np.finfo(np.float64).tiny)


def _add_slice(
    matrix: lil_matrix,
    row: int,
    column_slice: slice,
    values: np.ndarray,
    *,
    sign: float = 1.0,
) -> None:
    matrix[row, column_slice] = (
        np.asarray(matrix[row, column_slice].toarray()).reshape(-1) + sign * values
    )


def _intermediate_rows(
    spec: EnvironmentalNetworkSpec,
) -> tuple[_IntermediateRow, ...]:
    result: list[_IntermediateRow] = []
    for account_id, variables in spec.intermediate_accounts:
        by_producer: dict[str, list[str]] = {}
        for variable in variables:
            producer = spec.variable_owner(variable).producer_process
            if producer is None:
                raise RuntimeError("validated intermediate lacks a producer")
            by_producer.setdefault(producer, []).append(variable)
        for producer in sorted(by_producer):
            result.append(
                _IntermediateRow(
                    account_id=account_id,
                    producer_process=producer,
                    variables=tuple(sorted(by_producer[producer])),
                )
            )
    return tuple(result)


def _compile_reference(
    data: EnvironmentalNetworkData,
    rows: np.ndarray,
    returns_to_scale: ReturnsToScale,
) -> _CompiledEnvironmentalNetworkReference:
    spec = data.spec
    layout = _layout(spec, int(rows.size))
    positions = _column_positions(data)
    intermediate_rows = _intermediate_rows(spec)

    n_input = len(spec.input_accounts)
    n_good = len(spec.desirable_output_accounts)
    n_intermediate = len(intermediate_rows)
    rts_ub_count = (
        layout.n_processes
        if returns_to_scale in {ReturnsToScale.NIRS, ReturnsToScale.NDRS}
        else 0
    )
    rts_eq_count = layout.n_processes if returns_to_scale is ReturnsToScale.VRS else 0
    n_ub = n_input + n_good + n_intermediate + rts_ub_count
    n_eq = len(spec.undesirable_output_accounts) + rts_eq_count

    a_ub = lil_matrix((n_ub, layout.size_without_h), dtype=np.float64)
    a_eq = lil_matrix((n_eq, layout.size_without_h), dtype=np.float64)
    ub_scales: list[float] = []
    eq_scales: list[float] = []

    row = 0
    for _, variables in spec.input_accounts:
        scale_parts: list[np.ndarray] = []
        for process_id in layout.process_ids:
            owned = _variables_owned_by(spec, variables, process_id)
            values = _reference_values(data, rows, positions, owned)
            if not owned:
                continue
            scale_parts.append(values)
            process = layout.process_index[process_id]
            _add_slice(a_ub, row, layout.alpha_slices[process], values)
            beta_slice = layout.beta_slices[process]
            if beta_slice is not None:
                _add_slice(a_ub, row, beta_slice, values)
        ub_scales.append(_positive_scale(*scale_parts))
        row += 1

    for _, variables in spec.desirable_output_accounts:
        scale_parts = []
        for variable in variables:
            owner = spec.variable_owner(variable)
            producer = owner.producer_process
            if producer is None:
                raise RuntimeError("validated desirable output lacks a producer")
            values = _reference_values(data, rows, positions, (variable,))
            scale_parts.append(values)
            producer_index = layout.process_index[producer]
            _add_slice(
                a_ub,
                row,
                layout.alpha_slices[producer_index],
                values,
                sign=-1.0,
            )
            if owner.consumer_process is not None:
                consumer_index = layout.process_index[owner.consumer_process]
                _add_slice(
                    a_ub,
                    row,
                    layout.alpha_slices[consumer_index],
                    values,
                )
        ub_scales.append(_positive_scale(*scale_parts))
        row += 1

    for intermediate in intermediate_rows:
        scale_parts = []
        producer_index = layout.process_index[intermediate.producer_process]
        producer_values = _reference_values(
            data,
            rows,
            positions,
            intermediate.variables,
        )
        scale_parts.append(producer_values)
        _add_slice(
            a_ub,
            row,
            layout.alpha_slices[producer_index],
            producer_values,
            sign=-1.0,
        )
        for variable in intermediate.variables:
            owner = spec.variable_owner(variable)
            consumer = owner.consumer_process
            if consumer is None:
                raise RuntimeError("validated intermediate lacks a consumer")
            values = _reference_values(data, rows, positions, (variable,))
            scale_parts.append(values)
            consumer_index = layout.process_index[consumer]
            _add_slice(
                a_ub,
                row,
                layout.alpha_slices[consumer_index],
                values,
            )
            beta_slice = layout.beta_slices[consumer_index]
            if beta_slice is not None:
                _add_slice(a_ub, row, beta_slice, values)
        ub_scales.append(_positive_scale(*scale_parts))
        row += 1

    if rts_ub_count:
        sign = 1.0 if returns_to_scale is ReturnsToScale.NIRS else -1.0
        for process in range(layout.n_processes):
            values = np.ones(rows.size, dtype=np.float64)
            _add_slice(
                a_ub,
                row,
                layout.alpha_slices[process],
                values,
                sign=sign,
            )
            beta_slice = layout.beta_slices[process]
            if beta_slice is not None:
                _add_slice(a_ub, row, beta_slice, values, sign=sign)
            ub_scales.append(1.0)
            row += 1

    eq_row = 0
    for _, variables in spec.undesirable_output_accounts:
        scale_parts = []
        for variable in variables:
            owner = spec.variable_owner(variable)
            producer = owner.producer_process
            if producer is None:
                raise RuntimeError("validated undesirable output lacks a producer")
            values = _reference_values(data, rows, positions, (variable,))
            scale_parts.append(values)
            producer_index = layout.process_index[producer]
            _add_slice(
                a_eq,
                eq_row,
                layout.alpha_slices[producer_index],
                values,
            )
            if owner.consumer_process is not None:
                consumer_index = layout.process_index[owner.consumer_process]
                _add_slice(
                    a_eq,
                    eq_row,
                    layout.alpha_slices[consumer_index],
                    values,
                    sign=-1.0,
                )
        eq_scales.append(_positive_scale(*scale_parts))
        eq_row += 1

    if rts_eq_count:
        for process in range(layout.n_processes):
            values = np.ones(rows.size, dtype=np.float64)
            _add_slice(
                a_eq,
                eq_row,
                layout.alpha_slices[process],
                values,
            )
            beta_slice = layout.beta_slices[process]
            if beta_slice is not None:
                _add_slice(a_eq, eq_row, beta_slice, values)
            eq_scales.append(1.0)
            eq_row += 1

    readonly_rows = np.asarray(rows, dtype=np.int64)
    readonly_rows.setflags(write=False)
    ub_scale_array = np.asarray(ub_scales, dtype=np.float64)
    ub_scale_array.setflags(write=False)
    eq_scale_array = np.asarray(eq_scales, dtype=np.float64)
    eq_scale_array.setflags(write=False)
    return _CompiledEnvironmentalNetworkReference(
        rows=readonly_rows,
        layout=layout,
        a_ub_without_h=a_ub.tocsc(),
        a_eq_without_h=(None if n_eq == 0 else a_eq.tocsc()),
        ub_reference_scales=ub_scale_array,
        eq_reference_scales=eq_scale_array,
        intermediate_rows=intermediate_rows,
        rts_ub_count=rts_ub_count,
        rts_eq_count=rts_eq_count,
    )


def _observed_account(
    data: EnvironmentalNetworkData,
    observation: int,
    variables: tuple[str, ...],
    *,
    external_only: bool,
) -> float:
    selected = _external_variables(data.spec, variables) if external_only else variables
    if not selected:
        return 0.0
    return float(data.matrix(selected)[observation].sum())


def _problem(
    data: EnvironmentalNetworkData,
    reference: _CompiledEnvironmentalNetworkReference,
    observation: int,
    returns_to_scale: ReturnsToScale,
    *,
    name: str,
) -> LinearProgram:
    spec = data.spec
    n_intermediate = len(reference.intermediate_rows)
    n_bad = len(spec.undesirable_output_accounts)

    h_column = np.zeros(reference.a_ub_without_h.shape[0], dtype=np.float64)
    b_ub = np.zeros(reference.a_ub_without_h.shape[0], dtype=np.float64)
    ub_scales = reference.ub_reference_scales.copy()

    row = 0
    for _, variables in spec.input_accounts:
        observed = _observed_account(
            data,
            observation,
            variables,
            external_only=False,
        )
        h_column[row] = -observed
        ub_scales[row] = max(ub_scales[row], _positive_scale(observed))
        row += 1

    for _, variables in spec.desirable_output_accounts:
        observed = _observed_account(
            data,
            observation,
            variables,
            external_only=True,
        )
        b_ub[row] = -observed
        ub_scales[row] = max(ub_scales[row], _positive_scale(observed))
        row += 1

    row += n_intermediate
    if returns_to_scale is ReturnsToScale.NIRS:
        b_ub[row : row + reference.rts_ub_count] = 1.0
    elif returns_to_scale is ReturnsToScale.NDRS:
        b_ub[row : row + reference.rts_ub_count] = -1.0

    raw_a_ub = hstack(
        [
            reference.a_ub_without_h,
            csc_matrix(h_column.reshape(-1, 1)),
        ],
        format="csc",
    )
    a_ub = diags(1.0 / ub_scales, format="csc") @ raw_a_ub
    scaled_b_ub = b_ub / ub_scales

    a_eq: csc_matrix | None = None
    b_eq: np.ndarray | None = None
    if reference.a_eq_without_h is not None:
        b_eq = np.zeros(reference.a_eq_without_h.shape[0], dtype=np.float64)
        eq_scales = reference.eq_reference_scales.copy()
        for eq_row, (_, variables) in enumerate(spec.undesirable_output_accounts):
            observed = _observed_account(
                data,
                observation,
                variables,
                external_only=True,
            )
            b_eq[eq_row] = observed
            eq_scales[eq_row] = max(eq_scales[eq_row], _positive_scale(observed))
        if returns_to_scale is ReturnsToScale.VRS:
            b_eq[n_bad : n_bad + reference.rts_eq_count] = 1.0
        raw_a_eq = hstack(
            [
                reference.a_eq_without_h,
                csc_matrix((reference.a_eq_without_h.shape[0], 1)),
            ],
            format="csc",
        )
        a_eq = diags(1.0 / eq_scales, format="csc") @ raw_a_eq
        b_eq = b_eq / eq_scales

    objective = np.zeros(reference.layout.size, dtype=np.float64)
    objective[-1] = 1.0
    return LinearProgram(
        c=objective,
        a_ub=a_ub,
        b_ub=scaled_b_ub,
        a_eq=a_eq,
        b_eq=b_eq,
        bounds=((0.0, None),) * reference.layout.size,
        name=f"{name}:kalhor_kazemi_matin_environmental_network",
    )


def _intensity_arrays(
    reference: _CompiledEnvironmentalNetworkReference,
    primal: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    layout = reference.layout
    alpha = np.zeros((layout.n_processes, reference.size), dtype=np.float64)
    beta = np.zeros_like(alpha)
    for process in range(layout.n_processes):
        alpha[process] = primal[layout.alpha_slices[process]]
        beta_slice = layout.beta_slices[process]
        if beta_slice is not None:
            beta[process] = primal[beta_slice]
    return alpha, beta


def _reference_account_plan(
    data: EnvironmentalNetworkData,
    reference: _CompiledEnvironmentalNetworkReference,
    variables: tuple[str, ...],
    alpha: np.ndarray,
    beta: np.ndarray,
    *,
    role: str,
) -> tuple[float, float, float]:
    spec = data.spec
    positions = _column_positions(data)
    generation = 0.0
    internal_use = 0.0
    abatement_supported_use = 0.0
    for variable in variables:
        owner = spec.variable_owner(variable)
        values = _reference_values(
            data,
            reference.rows,
            positions,
            (variable,),
        )
        process_id = (
            owner.consumer_process if role == "input" else owner.producer_process
        )
        if process_id is None:
            raise RuntimeError("validated account variable lacks process ownership")
        process = reference.layout.process_index[process_id]
        if role == "input":
            generation += float((alpha[process] + beta[process]) @ values)
            continue
        generation += float(alpha[process] @ values)
        if owner.consumer_process is not None:
            consumer = reference.layout.process_index[owner.consumer_process]
            internal_use += float(alpha[consumer] @ values)
            abatement_supported_use += float(beta[consumer] @ values)
    return generation, internal_use, abatement_supported_use


def _intermediate_plan(
    data: EnvironmentalNetworkData,
    reference: _CompiledEnvironmentalNetworkReference,
    intermediate: _IntermediateRow,
    alpha: np.ndarray,
    beta: np.ndarray,
) -> tuple[float, float]:
    spec = data.spec
    positions = _column_positions(data)
    producer = reference.layout.process_index[intermediate.producer_process]
    supply_values = _reference_values(
        data,
        reference.rows,
        positions,
        intermediate.variables,
    )
    supply = float(alpha[producer] @ supply_values)
    requirement = 0.0
    for variable in intermediate.variables:
        owner = spec.variable_owner(variable)
        consumer_id = owner.consumer_process
        if consumer_id is None:
            raise RuntimeError("validated intermediate lacks a consumer")
        consumer = reference.layout.process_index[consumer_id]
        values = _reference_values(
            data,
            reference.rows,
            positions,
            (variable,),
        )
        requirement += float((alpha[consumer] + beta[consumer]) @ values)
    return supply, requirement


def _rts_violation(
    alpha: np.ndarray,
    beta: np.ndarray,
    returns_to_scale: ReturnsToScale,
) -> float:
    totals = (alpha + beta).sum(axis=1)
    if returns_to_scale is ReturnsToScale.VRS:
        return float(np.abs(totals - 1.0).max(initial=0.0))
    if returns_to_scale is ReturnsToScale.NIRS:
        return float(np.maximum(totals - 1.0, 0.0).max(initial=0.0))
    if returns_to_scale is ReturnsToScale.NDRS:
        return float(np.maximum(1.0 - totals, 0.0).max(initial=0.0))
    return 0.0


def _economic_violation(
    data: EnvironmentalNetworkData,
    reference: _CompiledEnvironmentalNetworkReference,
    observation: int,
    h: float,
    alpha: np.ndarray,
    beta: np.ndarray,
    returns_to_scale: ReturnsToScale,
) -> float:
    violations = [max(-h, 0.0), _rts_violation(alpha, beta, returns_to_scale)]
    for _, variables in data.spec.input_accounts:
        target, _, _ = _reference_account_plan(
            data,
            reference,
            variables,
            alpha,
            beta,
            role="input",
        )
        observed = _observed_account(
            data,
            observation,
            variables,
            external_only=False,
        )
        scale = _positive_scale(target, observed)
        violations.append(max(target - h * observed, 0.0) / scale)
    for _, variables in data.spec.desirable_output_accounts:
        generation, internal_use, _ = _reference_account_plan(
            data,
            reference,
            variables,
            alpha,
            beta,
            role="desirable_output",
        )
        observed = _observed_account(
            data,
            observation,
            variables,
            external_only=True,
        )
        scale = _positive_scale(generation, internal_use, observed)
        violations.append(max(observed - (generation - internal_use), 0.0) / scale)
    for _, variables in data.spec.undesirable_output_accounts:
        generation, internal_use, _ = _reference_account_plan(
            data,
            reference,
            variables,
            alpha,
            beta,
            role="undesirable_output",
        )
        observed = _observed_account(
            data,
            observation,
            variables,
            external_only=True,
        )
        scale = _positive_scale(generation, internal_use, observed)
        violations.append(abs(generation - internal_use - observed) / scale)
    for intermediate in reference.intermediate_rows:
        supply, requirement = _intermediate_plan(
            data,
            reference,
            intermediate,
            alpha,
            beta,
        )
        scale = _positive_scale(supply, requirement)
        violations.append(max(requirement - supply, 0.0) / scale)
    return max(violations, default=0.0)


class KalhorKazemiMatinNetworkDEA:
    """Estimate source-qualified environmental efficiency in a general network.

    The model implements the corrected technology and input-radial programme
    introduced by Kalhor and Kazemi Matin (2018). Every process has an active
    intensity ``alpha``. A process that produces at least one declared
    undesirable output additionally has a complementary weak-disposal
    intensity ``beta``. External inputs and ordinary-intermediate requirements
    use ``alpha + beta``; desirable and undesirable output production uses
    ``alpha``. Returns-to-scale constraints apply separately to every process.

    The result contains one system score. The source model does not define
    process efficiencies or a secondary slack-completion objective.
    """

    _registry_method_id = (
        "network.environmental.weak_activity_specific.kalhor_kazemi_matin_2018"
    )

    def __init__(
        self,
        *,
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.VRS,
        reference: ReferenceSpec | str | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.returns_to_scale = parse_enum(
            returns_to_scale,
            ReturnsToScale,
            "returns_to_scale",
        )
        self.reference = (
            ReferenceSpec()
            if reference is None
            else reference
            if isinstance(reference, ReferenceSpec)
            else ReferenceSpec(kind=reference)
        )
        if solver is not None and solver_options is not None:
            raise ValueError("pass solver or solver_options, not both")
        self.solver = SciPyHiGHSSolver(solver_options) if solver is None else solver
        if not math.isfinite(tolerance) or tolerance <= 0:
            raise ValueError("tolerance must be positive and finite")
        self.tolerance = float(tolerance)
        self.peer_tolerance = (
            self.tolerance if peer_tolerance is None else float(peer_tolerance)
        )
        if not math.isfinite(self.peer_tolerance) or self.peer_tolerance <= 0:
            raise ValueError("peer_tolerance must be positive and finite")

    def _validate_data(self, data: EnvironmentalNetworkData) -> None:
        data.ensure_nonnegative(
            model_name="Kalhor--Kazemi Matin environmental network DEA"
        )
        total_inputs = data.matrix(data.spec.external_inputs).sum(axis=1)
        invalid_inputs = np.flatnonzero(total_inputs <= 0)
        if invalid_inputs.size:
            raise ModelSpecificationError(
                "input-radial environmental network DEA requires positive "
                "aggregate external input for every observation; row positions="
                f"{invalid_inputs[:5].tolist()!r}"
            )
        for role, accounts in (
            ("desirable", data.spec.desirable_output_accounts),
            ("undesirable", data.spec.undesirable_output_accounts),
        ):
            for account_id, variables in accounts:
                variables_by_producer: dict[str, list[str]] = {}
                for variable in variables:
                    producer = data.spec.variable_owner(variable).producer_process
                    if producer is None:
                        raise RuntimeError(
                            "validated environmental output lacks a producer"
                        )
                    variables_by_producer.setdefault(producer, []).append(variable)
                for producer, produced_variables in sorted(
                    variables_by_producer.items()
                ):
                    external = tuple(
                        variable
                        for variable in produced_variables
                        if data.spec.variable_owner(variable).occurrence_kind
                        == "external_output"
                    )
                    if not external:
                        raise ModelSpecificationError(
                            f"{role} output account {account_id!r} for producer "
                            f"process {producer!r} has no final output leaving "
                            "the network; every process producing an "
                            "environmental account must contribute a final "
                            "output to that same account; classify a purely "
                            "internal product as an ordinary intermediate"
                        )
                    if not np.any(data.matrix(external) > 0):
                        raise ModelSpecificationError(
                            f"{role} output account {account_id!r} for producer "
                            f"process {producer!r} has no positive final "
                            "observation"
                        )

    def _failure_row(
        self,
        *,
        dmu_id: object,
        period: object | None,
        reference_size: int,
        solution_status: SolverStatus,
        score_status: str,
    ) -> dict[str, Any]:
        return {
            "dmu_id": dmu_id,
            "period": period,
            "score": np.nan,
            "efficiency": np.nan,
            "distance": np.nan,
            "system_score": np.nan,
            "system_efficiency": np.nan,
            "is_efficient": pd.NA,
            "is_system_radially_efficient": pd.NA,
            "is_within_reference_technology": (
                False if solution_status is SolverStatus.INFEASIBLE else pd.NA
            ),
            "solver_status": solution_status.value,
            "score_status": score_status,
            "target_status": "not_computed",
            "model_family": "environmental_network_radial",
            "orientation": "input",
            "returns_to_scale": self.returns_to_scale.value,
            "reference_size": reference_size,
            "process_efficiencies_defined": False,
            "bad_output_disposability": "weak_activity_specific",
            "projection_policy": "not_computed",
            "max_scaled_account_residual": np.nan,
            "max_omitted_total_intensity": np.nan,
        }

    def fit(self, data: EnvironmentalNetworkData) -> DEAResult:
        """Estimate one system input-radial score per observation."""

        if not isinstance(data, EnvironmentalNetworkData):
            raise TypeError(
                "KalhorKazemiMatinNetworkDEA.fit expects EnvironmentalNetworkData"
            )
        self._validate_data(data)
        reference_plan = build_reference_plan(data, self.reference)
        compiled: dict[int, _CompiledEnvironmentalNetworkReference] = {}

        summary_rows: list[dict[str, Any]] = []
        component_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        link_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []

        for observation in range(data.n_dmus):
            set_id = reference_plan.set_id_for(observation)
            reference = compiled.get(set_id)
            if reference is None:
                reference = _compile_reference(
                    data,
                    reference_plan.rows_for(observation),
                    self.returns_to_scale,
                )
                compiled[set_id] = reference

            dmu_id = data.dmu_ids[observation]
            period = None if data.periods is None else data.periods[observation]
            name = f"{dmu_id}@{period}" if period is not None else str(dmu_id)
            problem = _problem(
                data,
                reference,
                observation,
                self.returns_to_scale,
                name=name,
            )
            solution = self.solver.solve(problem)
            certificate = _certify_lp_solution(
                problem,
                solution,
                tolerance=self.tolerance,
            )

            h = math.nan
            alpha: np.ndarray | None = None
            beta: np.ndarray | None = None
            economic_violation = math.inf
            accepted = False
            if certificate.certified and solution.primal is not None:
                primal = np.maximum(
                    np.asarray(solution.primal, dtype=np.float64),
                    0.0,
                )
                h = float(primal[-1])
                alpha, beta = _intensity_arrays(reference, primal)
                economic_violation = _economic_violation(
                    data,
                    reference,
                    observation,
                    h,
                    alpha,
                    beta,
                    self.returns_to_scale,
                )
                self_in_reference = bool(np.any(reference.rows == observation))
                accepted = bool(
                    math.isfinite(h)
                    and h >= 0.0
                    and economic_violation <= self.tolerance
                    and (not self_in_reference or h <= 1.0 + self.tolerance)
                )

            diagnostic_rows.append(
                _diagnostic(
                    dmu_id=dmu_id,
                    period=period,
                    solution=solution,
                    certificate=certificate,
                    economic_violation=economic_violation,
                    accepted=accepted,
                )
            )
            if not accepted or alpha is None or beta is None:
                summary_rows.append(
                    self._failure_row(
                        dmu_id=dmu_id,
                        period=period,
                        reference_size=reference.size,
                        solution_status=solution.status,
                        score_status=(
                            "solver_failed"
                            if solution.status is not SolverStatus.OPTIMAL
                            else "certificate_failed"
                        ),
                    )
                )
                continue

            omitted_totals: list[float] = []
            for process, process_id in enumerate(reference.layout.process_ids):
                totals = alpha[process] + beta[process]
                omitted_totals.append(
                    float(totals[totals <= self.peer_tolerance].sum())
                )
                for local_position, total in enumerate(totals):
                    if total <= self.peer_tolerance:
                        continue
                    reference_position = reference.rows[local_position]
                    retained_rate = (
                        float(alpha[process, local_position] / total)
                        if total > 0
                        else np.nan
                    )
                    intensity_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "process_id": process_id,
                            "reference_dmu_id": data.dmu_ids[reference_position],
                            "reference_period": (
                                None
                                if data.periods is None
                                else data.periods[reference_position]
                            ),
                            "intensity": float(total),
                            "total_intensity": float(total),
                            "alpha": float(alpha[process, local_position]),
                            "beta": float(beta[process, local_position]),
                            "retained_operating_rate": retained_rate,
                            "process_produces_undesirable_output": (
                                process_id in reference.layout.bad_processes
                            ),
                        }
                    )

            scaled_account_residuals: list[float] = []
            for account_id, variables in data.spec.input_accounts:
                target, _, _ = _reference_account_plan(
                    data,
                    reference,
                    variables,
                    alpha,
                    beta,
                    role="input",
                )
                observed = _observed_account(
                    data,
                    observation,
                    variables,
                    external_only=False,
                )
                bound = h * observed
                residual = bound - target
                scaled = residual / _positive_scale(bound, target, observed)
                if abs(scaled) <= self.tolerance:
                    residual = 0.0
                    scaled = 0.0
                scaled_account_residuals.append(max(scaled, 0.0))
                target_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "process_id": pd.NA,
                        "role": "external_input_account",
                        "account_id": account_id,
                        "variable": account_id,
                        "account_variables": variables,
                        "observed": observed,
                        "target": target,
                        "constraint_bound": bound,
                        "constraint_residual": residual,
                        "scaled_constraint_residual": scaled,
                        "projection_policy": "solver_selected_primary_optimum",
                    }
                )

            for role, accounts in (
                ("desirable_output", data.spec.desirable_output_accounts),
                ("undesirable_output", data.spec.undesirable_output_accounts),
            ):
                for account_id, variables in accounts:
                    generation, internal_use, _ = _reference_account_plan(
                        data,
                        reference,
                        variables,
                        alpha,
                        beta,
                        role=role,
                    )
                    target = generation - internal_use
                    observed = _observed_account(
                        data,
                        observation,
                        variables,
                        external_only=True,
                    )
                    residual = (
                        target - observed
                        if role == "desirable_output"
                        else abs(target - observed)
                    )
                    scaled = residual / _positive_scale(
                        generation,
                        internal_use,
                        observed,
                    )
                    if abs(scaled) <= self.tolerance:
                        residual = 0.0
                        scaled = 0.0
                    scaled_account_residuals.append(max(scaled, 0.0))
                    target_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "process_id": pd.NA,
                            "role": f"final_{role}_account",
                            "account_id": account_id,
                            "variable": account_id,
                            "account_variables": variables,
                            "observed": observed,
                            "target": target,
                            "gross_active_generation": generation,
                            "internal_active_use": internal_use,
                            "constraint_bound": observed,
                            "constraint_residual": residual,
                            "scaled_constraint_residual": scaled,
                            "projection_policy": "solver_selected_primary_optimum",
                        }
                    )

            for intermediate in reference.intermediate_rows:
                supply, requirement = _intermediate_plan(
                    data,
                    reference,
                    intermediate,
                    alpha,
                    beta,
                )
                surplus = supply - requirement
                scaled = surplus / _positive_scale(supply, requirement)
                if abs(scaled) <= self.tolerance:
                    surplus = 0.0
                    scaled = 0.0
                scaled_account_residuals.append(max(scaled, 0.0))
                target_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "process_id": intermediate.producer_process,
                        "role": "ordinary_intermediate_account",
                        "account_id": intermediate.account_id,
                        "variable": intermediate.account_id,
                        "account_variables": intermediate.variables,
                        "observed": _observed_account(
                            data,
                            observation,
                            intermediate.variables,
                            external_only=False,
                        ),
                        "target": supply,
                        "downstream_requirement": requirement,
                        "constraint_bound": requirement,
                        "constraint_residual": surplus,
                        "scaled_constraint_residual": scaled,
                        "projection_policy": "solver_selected_primary_optimum",
                    }
                )

            positions = _column_positions(data)
            intermediate_by_account_producer = {
                (intermediate.account_id, intermediate.producer_process): (intermediate)
                for intermediate in reference.intermediate_rows
            }
            for variable in data.spec.link_variables:
                owner = data.spec.variable_owner(variable)
                producer_id = owner.producer_process
                consumer_id = owner.consumer_process
                if producer_id is None or consumer_id is None:
                    raise RuntimeError("validated link lacks endpoints")
                producer = reference.layout.process_index[producer_id]
                consumer = reference.layout.process_index[consumer_id]
                values = _reference_values(
                    data,
                    reference.rows,
                    positions,
                    (variable,),
                )
                active_supply = float(alpha[producer] @ values)
                active_use = float(alpha[consumer] @ values)
                beta_use = (
                    float(beta[consumer] @ values)
                    if owner.semantic_role == "intermediate"
                    else 0.0
                )
                required = active_use + beta_use
                account_supply = np.nan
                account_requirement = np.nan
                account_surplus = np.nan
                balance_scope = "system_product_account"
                balance_is_link_specific = False
                if owner.semantic_role == "intermediate":
                    intermediate = intermediate_by_account_producer[
                        (owner.account_id, producer_id)
                    ]
                    account_supply, account_requirement = _intermediate_plan(
                        data,
                        reference,
                        intermediate,
                        alpha,
                        beta,
                    )
                    account_surplus = account_supply - account_requirement
                    balance_is_link_specific = len(intermediate.variables) == 1
                    balance_scope = (
                        "link"
                        if balance_is_link_specific
                        else "producer_product_account"
                    )
                link_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "link_id": owner.link_id,
                        "source_process": producer_id,
                        "target_process": consumer_id,
                        "account_id": owner.account_id,
                        "flow_kind": owner.semantic_role,
                        "variable": variable,
                        "observed": float(
                            data.values[observation, positions[variable]]
                        ),
                        "active_source_supply": active_supply,
                        "active_target_use": active_use,
                        "abatement_supported_target_use": beta_use,
                        "downstream_requirement": required,
                        "source_minus_requirement": active_supply - required,
                        "account_source_supply": account_supply,
                        "account_downstream_requirement": account_requirement,
                        "account_balance_surplus": account_surplus,
                        "balance_scope": balance_scope,
                        "balance_is_link_specific": balance_is_link_specific,
                        "projection_policy": "solver_selected_primary_optimum",
                    }
                )

            within_reference = bool(h <= 1.0 + self.tolerance)
            radial_efficiency: bool | Any = (
                bool(abs(h - 1.0) <= self.tolerance) if within_reference else pd.NA
            )
            max_residual = max(scaled_account_residuals, default=0.0)
            component_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "component_kind": "system",
                    "component_id": "system",
                    "score": h,
                    "efficiency": h,
                    "is_measure_efficient": radial_efficiency,
                    "status": "defined",
                }
            )
            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "score": h,
                    "efficiency": h,
                    "distance": np.nan,
                    "system_score": h,
                    "system_efficiency": h,
                    "is_efficient": pd.NA,
                    "is_system_radially_efficient": radial_efficiency,
                    "is_within_reference_technology": within_reference,
                    "solver_status": SolverStatus.OPTIMAL.value,
                    "score_status": "defined",
                    "target_status": "defined_primary_optimum",
                    "model_family": "environmental_network_radial",
                    "orientation": "input",
                    "returns_to_scale": self.returns_to_scale.value,
                    "reference_size": reference.size,
                    "process_efficiencies_defined": False,
                    "bad_output_disposability": "weak_activity_specific",
                    "projection_policy": "solver_selected_primary_optimum",
                    "max_scaled_account_residual": max_residual,
                    "max_omitted_total_intensity": max(
                        omitted_totals,
                        default=0.0,
                    ),
                }
            )

        effective_reference = reference_plan.kind
        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
            targets=pd.DataFrame(target_rows),
            intensities=pd.DataFrame(intensity_rows),
            components=pd.DataFrame(component_rows),
            links=pd.DataFrame(link_rows),
            diagnostics=pd.DataFrame(diagnostic_rows),
            metadata={
                **registry_metadata(
                    self._registry_method_id,
                    {
                        "context": {
                            "purpose": (
                                "system_resource_performance_with_internal_"
                                "production_and_undesirable_outputs"
                            ),
                            "sample": ("panel" if data.is_panel else "cross_section"),
                        },
                        "graph": {
                            "kind": "general_network",
                            "processes": list(
                                sorted(
                                    process.process_id
                                    for process in data.network_spec.processes
                                )
                            ),
                            "links": [
                                link.link_id
                                for link in sorted(
                                    data.network_spec.links,
                                    key=lambda item: item.link_id,
                                )
                            ],
                            "cycles_permitted": True,
                        },
                        "data_roles": {
                            "input_accounts": {
                                key: list(values)
                                for key, values in data.spec.input_accounts
                            },
                            "desirable_output_accounts": {
                                key: list(values)
                                for key, values in (data.spec.desirable_output_accounts)
                            },
                            "undesirable_output_accounts": {
                                key: list(values)
                                for key, values in (
                                    data.spec.undesirable_output_accounts
                                )
                            },
                            "intermediate_accounts": {
                                key: list(values)
                                for key, values in data.spec.intermediate_accounts
                            },
                            "panel": data.is_panel,
                            "grouped": data.groups is not None,
                        },
                        "technology": {
                            "family": (
                                "general_network_activity_specific_weak_disposal"
                            ),
                            "returns_to_scale": self.returns_to_scale.value,
                            "process_intensity_restriction": {
                                ReturnsToScale.CRS: "none",
                                ReturnsToScale.VRS: (
                                    "sum_alpha_plus_beta_equals_one_by_process"
                                ),
                                ReturnsToScale.NIRS: (
                                    "sum_alpha_plus_beta_at_most_one_by_process"
                                ),
                                ReturnsToScale.NDRS: (
                                    "sum_alpha_plus_beta_at_least_one_by_process"
                                ),
                            }[self.returns_to_scale],
                            "active_component": "alpha",
                            "weak_disposal_component": "beta",
                            "ordinary_intermediate_balance": (
                                "active_source_supply_greater_than_or_equal_to_"
                                "active_plus_abatement_target_requirement"
                            ),
                        },
                        "estimator": {
                            "estimator_id": "estimator.full.dea",
                            "kind": "full_frontier",
                            "family": "network_envelopment",
                        },
                        "reference": registry_reference_spec(
                            self.reference,
                            effective_reference,
                        ),
                        "performance": {
                            "family": "input_radial_system_efficiency",
                            "orientation": "input",
                            "system_score": "h",
                            "process_efficiencies": "not_defined",
                        },
                        "valuation": {"kind": "none"},
                        "evaluation_protocol": {
                            "kind": "joint_system_self_appraisal",
                            "primary_programmes_per_observation": 1,
                            "secondary_slack_completion": False,
                            "projection_policy": ("solver_selected_primary_optimum"),
                            "targets_use_unthresholded_intensities": True,
                        },
                        "analysis": {"kind": "direct_network_fit"},
                        "uncertainty": {
                            "sampling": {"kind": "none"},
                            "data": {"kind": "none"},
                        },
                    },
                ),
                "solver": getattr(self.solver, "name", type(self.solver).__name__),
                "compiled_reference_sets": len(compiled),
                "primary_programmes_solved": len(diagnostic_rows),
                "semantic_fingerprint": data.semantic_fingerprint,
                "score_semantics": {
                    "native": "h",
                    "direction": "higher_is_better",
                    "efficient_value": 1.0,
                    "generic_efficiency_flag": (
                        "undefined_without_strong_slack_completion"
                    ),
                },
                "source_boundary": {
                    "technology": "Kalhor_Kazemi_Matin_2018_equation_3_2",
                    "measure": "input_radial_equations_3_3_to_3_4",
                    "directional_distance_variant": "deferred_to_next_version",
                    "process_efficiencies": "not_defined",
                },
            },
        )


__all__ = ["KalhorKazemiMatinNetworkDEA"]
