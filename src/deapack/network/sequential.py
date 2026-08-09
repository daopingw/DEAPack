"""Lewis--Sexton sequential radial DEA for acyclic production networks.

This module implements the linear, forward-quantity part of Lewis and Sexton
(2004).  Reverse quantities, mixed forward/reverse accounts, and site
characteristic adjustments are deliberately outside this method identity.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

import numpy as np
import pandas as pd

from .._registry import reference_spec as registry_reference_spec
from .._registry import registry_metadata
from ..enums import (
    Orientation,
    ReturnsToScale,
    SolverStatus,
    parse_enum,
)
from ..exceptions import DataValidationError, ModelSpecificationError
from ..models._common import CompiledReference, as_sparse_rows
from ..models._radial_lp import radial_phase_one_problem, radial_row_scales
from ..results import DEAResult
from ..solvers import LPSolution, LPSolver, SciPyHiGHSSolver
from ..specs import ReferenceSpec, SolverOptions
from ..technology import build_reference_plan
from ._layout import (
    CompiledNetworkLayout,
    CompiledProcessLayout,
    compile_network_layout,
)
from .data import NetworkData
from .fare_grosskopf import _certify_lp_solution

ProcessReturnsToScale = ReturnsToScale | str | Mapping[str, ReturnsToScale | str]

_TARGET_SELECTION = "solver_selected_primary_optimum_nonunique_possible"


@dataclass(frozen=True, slots=True)
class _ProcessReference:
    process_id: str
    input_columns: tuple[int, ...]
    output_columns: tuple[int, ...]
    input_names: tuple[str, ...]
    output_names: tuple[str, ...]
    technology: CompiledReference


@dataclass(frozen=True, slots=True)
class _ProcessSolve:
    factor: float
    efficiency: float
    lambdas: np.ndarray
    input_evaluation: np.ndarray
    output_evaluation: np.ndarray
    input_targets: np.ndarray
    output_targets: np.ndarray
    omitted_intensity_sum: float
    solution: LPSolution
    max_economic_violation: float


def _normalize_rts(
    value: ProcessReturnsToScale,
) -> ReturnsToScale | MappingProxyType[str, ReturnsToScale]:
    if not isinstance(value, Mapping):
        return parse_enum(value, ReturnsToScale, "returns_to_scale")

    normalized: dict[str, ReturnsToScale] = {}
    for raw_process_id, raw_rts in value.items():
        if not isinstance(raw_process_id, str) or not raw_process_id.strip():
            raise ValueError("returns_to_scale mapping keys must be process IDs")
        process_id = raw_process_id.strip()
        if process_id in normalized:
            raise ValueError(
                "returns_to_scale mapping contains duplicate normalized process IDs"
            )
        normalized[process_id] = parse_enum(
            raw_rts,
            ReturnsToScale,
            f"returns_to_scale[{process_id!r}]",
        )
    if not normalized:
        raise ValueError("returns_to_scale mapping cannot be empty")
    return MappingProxyType(normalized)


def _resolved_rts(
    value: ReturnsToScale | Mapping[str, ReturnsToScale],
    process_ids: tuple[str, ...],
) -> MappingProxyType[str, ReturnsToScale]:
    if isinstance(value, ReturnsToScale):
        return MappingProxyType(dict.fromkeys(process_ids, value))

    unknown = set(value).difference(process_ids)
    missing = set(process_ids).difference(value)
    if unknown or missing:
        raise ValueError(
            "a process-specific returns_to_scale mapping must contain every "
            "network process exactly once; "
            f"missing={sorted(missing)!r}, unknown={sorted(unknown)!r}"
        )
    return MappingProxyType(
        {process_id: value[process_id] for process_id in process_ids}
    )


def _compile_process_references(
    values: np.ndarray,
    layout: CompiledNetworkLayout,
    rows: np.ndarray,
) -> dict[str, _ProcessReference]:
    references: dict[str, _ProcessReference] = {}
    for process in layout.processes:
        input_columns = process.input_columns
        output_columns = process.output_columns
        references[process.process_id] = _ProcessReference(
            process_id=process.process_id,
            input_columns=input_columns,
            output_columns=output_columns,
            input_names=tuple(
                layout.variable_names[column] for column in input_columns
            ),
            output_names=tuple(
                layout.variable_names[column] for column in output_columns
            ),
            technology=CompiledReference(
                rows=rows,
                inputs=as_sparse_rows(values[rows][:, input_columns]),
                outputs=as_sparse_rows(values[rows][:, output_columns]),
            ),
        )
    return references


def _rts_violation(
    lambdas: np.ndarray,
    returns_to_scale: ReturnsToScale,
) -> float:
    intensity_sum = float(lambdas.sum())
    if returns_to_scale is ReturnsToScale.VRS:
        return abs(intensity_sum - 1.0)
    if returns_to_scale is ReturnsToScale.NIRS:
        return max(intensity_sum - 1.0, 0.0)
    if returns_to_scale is ReturnsToScale.NDRS:
        return max(1.0 - intensity_sum, 0.0)
    return 0.0


def _economic_violation(
    reference: _ProcessReference,
    orientation: Orientation,
    returns_to_scale: ReturnsToScale,
    factor: float,
    lambdas: np.ndarray,
    input_evaluation: np.ndarray,
    output_evaluation: np.ndarray,
) -> tuple[float, np.ndarray, np.ndarray]:
    input_targets = np.asarray(
        reference.technology.inputs @ lambdas,
        dtype=np.float64,
    ).reshape(-1)
    output_targets = np.asarray(
        reference.technology.outputs @ lambdas,
        dtype=np.float64,
    ).reshape(-1)
    input_scales, output_scales = radial_row_scales(
        reference.technology,
        input_evaluation,
        output_evaluation,
    )
    if orientation is Orientation.INPUT:
        input_violation = (
            np.maximum(
                input_targets - factor * input_evaluation,
                0.0,
            )
            / input_scales
        )
        output_violation = (
            np.maximum(
                output_evaluation - output_targets,
                0.0,
            )
            / output_scales
        )
    else:
        input_violation = (
            np.maximum(
                input_targets - input_evaluation,
                0.0,
            )
            / input_scales
        )
        output_violation = (
            np.maximum(
                factor * output_evaluation - output_targets,
                0.0,
            )
            / output_scales
        )
    violation = max(
        float(input_violation.max(initial=0.0)),
        float(output_violation.max(initial=0.0)),
        _rts_violation(lambdas, returns_to_scale),
    )
    return violation, input_targets, output_targets


def _diagnostic_row(
    *,
    dmu_id: object,
    period: object | None,
    process_id: str,
    phase: str,
    solution: LPSolution,
    certificate_reason: str,
    certificate_status: str,
    max_economic_violation: float,
    solve_reused: bool,
) -> dict[str, Any]:
    return {
        "dmu_id": dmu_id,
        "period": period,
        "process_id": process_id,
        "phase": phase,
        "solver_status": solution.status.value,
        "message": solution.message,
        "iterations": solution.iterations,
        "max_primal_violation": solution.max_primal_violation,
        "certification_status": certificate_status,
        "certificate_reason": certificate_reason,
        "max_economic_constraint_violation": max_economic_violation,
        "solve_reused": solve_reused,
    }


def _role_for_column(
    process: CompiledProcessLayout,
    column: int,
    *,
    is_input: bool,
) -> str:
    if is_input:
        return (
            "external_input"
            if column in process.external_input_columns
            else "incoming_link"
        )
    return (
        "external_output"
        if column in process.external_output_columns
        else "outgoing_link"
    )


class LewisSextonSequentialNetworkDEA:
    """Sequential radial evaluation of a forward-quantity production DAG.

    Each process first receives an ordinary radial appraisal.  The model then
    propagates solver-selected efficient quantities through the organization:
    forward under output orientation and backward under input orientation.
    The resulting organizational account need not identify an efficient DMU,
    and process targets can be non-unique.

    Parameters
    ----------
    orientation:
        One global input or output orientation.  Mixed process orientations
        belong to a separate method identity.
    returns_to_scale:
        One RTS assumption for every process, or a complete mapping from
        process IDs to ``crs``, ``vrs``, ``nirs``, or ``ndrs``.
    """

    _registry_method_id = "network.sequential.lewis_sexton_2004.forward_radial"

    def __init__(
        self,
        *,
        orientation: Orientation | str = Orientation.OUTPUT,
        returns_to_scale: ProcessReturnsToScale = ReturnsToScale.CRS,
        reference: ReferenceSpec | str | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.orientation = parse_enum(orientation, Orientation, "orientation")
        self.returns_to_scale = _normalize_rts(returns_to_scale)
        self.reference = (
            ReferenceSpec()
            if reference is None
            else reference
            if isinstance(reference, ReferenceSpec)
            else ReferenceSpec(kind=reference)
        )
        if solver is not None and solver_options is not None:
            raise ValueError("pass solver or solver_options, not both")
        if not math.isfinite(tolerance) or tolerance <= 0:
            raise ValueError("tolerance must be positive and finite")
        resolved_peer_tolerance = (
            tolerance if peer_tolerance is None else peer_tolerance
        )
        if not math.isfinite(resolved_peer_tolerance) or resolved_peer_tolerance <= 0:
            raise ValueError("peer_tolerance must be positive and finite")
        self.solver = SciPyHiGHSSolver(solver_options) if solver is None else solver
        self.tolerance = float(tolerance)
        self.peer_tolerance = float(resolved_peer_tolerance)

    def _validate_data(
        self,
        data: NetworkData,
        values: np.ndarray,
        layout: CompiledNetworkLayout,
    ) -> None:
        data.ensure_nonnegative(model_name="Lewis--Sexton sequential network DEA")
        if not layout.external_inputs or not layout.external_outputs:
            raise ModelSpecificationError(
                "Lewis--Sexton sequential DEA requires at least one external "
                "system input and one external system output"
            )
        for link in data.network_spec.links:
            if link.intensity_policy != "process_specific":
                raise ModelSpecificationError(
                    "Lewis--Sexton sequential DEA requires process-specific "
                    "reference intensities"
                )
            if link.envelopment_balance not in {
                "upstream_supply_greater_than_or_equal_to_downstream_requirement",
                "source_defined",
            }:
                raise ModelSpecificationError(
                    "Lewis--Sexton forward quantities require upstream supply "
                    "to cover downstream requirement"
                )

        if np.any(values[:, layout.external_input_slice].sum(axis=1) <= 0.0):
            raise DataValidationError(
                "every organization needs positive aggregate external input"
            )
        if np.any(values[:, layout.external_output_slice].sum(axis=1) <= 0.0):
            raise DataValidationError(
                "every organization needs positive aggregate external output"
            )
        for process in layout.processes:
            if np.any(values[:, process.input_columns].sum(axis=1) <= 0.0):
                raise DataValidationError(
                    f"process {process.process_id!r} needs positive aggregate "
                    "input for every organization"
                )
            if np.any(values[:, process.output_columns].sum(axis=1) <= 0.0):
                raise DataValidationError(
                    f"process {process.process_id!r} needs positive aggregate "
                    "output for every organization"
                )

    def _solve_process(
        self,
        *,
        reference: _ProcessReference,
        returns_to_scale: ReturnsToScale,
        input_evaluation: np.ndarray,
        output_evaluation: np.ndarray,
        name: str,
    ) -> tuple[_ProcessSolve | None, LPSolution, str, float]:
        problem = radial_phase_one_problem(
            reference.technology,
            input_evaluation,
            output_evaluation,
            self.orientation,
            returns_to_scale,
            name,
        )
        solution = self.solver.solve(problem)
        certificate = _certify_lp_solution(
            problem,
            solution,
            tolerance=self.tolerance,
        )
        if not certificate.certified or solution.primal is None:
            return None, solution, certificate.reason, math.inf

        lambdas = np.asarray(
            solution.primal[: reference.technology.size],
            dtype=np.float64,
        ).copy()
        lambdas[np.abs(lambdas) <= self.tolerance] = 0.0
        factor = float(solution.primal[-1])
        if abs(factor) <= self.tolerance:
            factor = 0.0
        max_economic_violation, input_targets, output_targets = _economic_violation(
            reference,
            self.orientation,
            returns_to_scale,
            factor,
            lambdas,
            input_evaluation,
            output_evaluation,
        )
        factor_valid = (
            factor >= -self.tolerance
            if self.orientation is Orientation.INPUT
            else factor > self.tolerance
        )
        if (
            np.any(lambdas < -self.tolerance)
            or not factor_valid
            or not math.isfinite(factor)
            or max_economic_violation > self.tolerance
        ):
            return (
                None,
                solution,
                "postprocessed_quantity_certificate_failed",
                max_economic_violation,
            )

        efficiency = factor if self.orientation is Orientation.INPUT else 1.0 / factor
        disclosed = lambdas > self.peer_tolerance
        omitted_intensity_sum = float(lambdas[~disclosed].sum())
        return (
            _ProcessSolve(
                factor=factor,
                efficiency=efficiency,
                lambdas=lambdas,
                input_evaluation=np.asarray(
                    input_evaluation,
                    dtype=np.float64,
                ).copy(),
                output_evaluation=np.asarray(
                    output_evaluation,
                    dtype=np.float64,
                ).copy(),
                input_targets=input_targets,
                output_targets=output_targets,
                omitted_intensity_sum=omitted_intensity_sum,
                solution=solution,
                max_economic_violation=max_economic_violation,
            ),
            solution,
            "certified",
            max_economic_violation,
        )

    def _component_row(
        self,
        *,
        dmu_id: object,
        period: object | None,
        process_id: str,
        phase: str,
        record: _ProcessSolve,
        returns_to_scale: ReturnsToScale,
        solve_reused: bool,
    ) -> dict[str, Any]:
        return {
            "dmu_id": dmu_id,
            "period": period,
            "component_kind": "process",
            "component_id": process_id,
            "process_id": process_id,
            "phase": phase,
            "score": record.efficiency,
            "efficiency": record.efficiency,
            "radial_factor": record.factor,
            "factor_interpretation": (
                "input_efficiency"
                if self.orientation is Orientation.INPUT
                else "output_inverse_efficiency"
            ),
            "is_measure_efficient": bool(
                abs(record.efficiency - 1.0) <= self.tolerance
            ),
            "status": "defined",
            "orientation": self.orientation.value,
            "returns_to_scale": returns_to_scale.value,
            "solve_reused": solve_reused,
            "omitted_intensity_sum": record.omitted_intensity_sum,
            "target_selection": _TARGET_SELECTION,
            "target_uniqueness": "not_tested",
        }

    def _target_rows(
        self,
        *,
        dmu_id: object,
        period: object | None,
        process: CompiledProcessLayout,
        reference: _ProcessReference,
        record: _ProcessSolve,
        observed: np.ndarray,
        phase: str,
        link_id_by_column: Mapping[int, str],
        solve_reused: bool,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for column, variable, evaluation, target in zip(
            reference.input_columns,
            reference.input_names,
            record.input_evaluation,
            record.input_targets,
            strict=True,
        ):
            radial_bound = (
                record.factor * float(evaluation)
                if self.orientation is Orientation.INPUT
                else float(evaluation)
            )
            rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "process_id": process.process_id,
                    "phase": phase,
                    "role": _role_for_column(
                        process,
                        column,
                        is_input=True,
                    ),
                    "link_id": link_id_by_column.get(column),
                    "variable": variable,
                    "observed": float(observed[column]),
                    "conditioning_value": float(evaluation),
                    "target": float(target),
                    "radial_bound": radial_bound,
                    "constraint_sense": "less_than_or_equal",
                    "solve_reused": solve_reused,
                    "projection_policy": _TARGET_SELECTION,
                    "target_uniqueness": "not_tested",
                }
            )
        for column, variable, evaluation, target in zip(
            reference.output_columns,
            reference.output_names,
            record.output_evaluation,
            record.output_targets,
            strict=True,
        ):
            radial_bound = (
                float(evaluation)
                if self.orientation is Orientation.INPUT
                else record.factor * float(evaluation)
            )
            rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "process_id": process.process_id,
                    "phase": phase,
                    "role": _role_for_column(
                        process,
                        column,
                        is_input=False,
                    ),
                    "link_id": link_id_by_column.get(column),
                    "variable": variable,
                    "observed": float(observed[column]),
                    "conditioning_value": float(evaluation),
                    "target": float(target),
                    "radial_bound": radial_bound,
                    "constraint_sense": "greater_than_or_equal",
                    "solve_reused": solve_reused,
                    "projection_policy": _TARGET_SELECTION,
                    "target_uniqueness": "not_tested",
                }
            )
        return rows

    def _intensity_rows(
        self,
        *,
        data: NetworkData,
        dmu_id: object,
        period: object | None,
        process_id: str,
        phase: str,
        reference: _ProcessReference,
        record: _ProcessSolve,
        solve_reused: bool,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for local_position, intensity in enumerate(record.lambdas):
            if intensity <= self.peer_tolerance:
                continue
            reference_row = int(reference.technology.rows[local_position])
            rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "process_id": process_id,
                    "phase": phase,
                    "reference_dmu_id": data.dmu_ids[reference_row],
                    "reference_period": (
                        None if data.periods is None else data.periods[reference_row]
                    ),
                    "reference_row": reference_row,
                    "intensity": float(intensity),
                    "lambda": float(intensity),
                    "solve_reused": solve_reused,
                    "target_selection": _TARGET_SELECTION,
                }
            )
        return rows

    def _failure_summary(
        self,
        *,
        dmu_id: object,
        period: object | None,
        status: str,
        solver_status: SolverStatus,
        process_count: int,
        reference_size: int,
        primary_programmes: int,
    ) -> dict[str, Any]:
        reported_solver_status = (
            SolverStatus.NUMERICAL_ERROR
            if solver_status is SolverStatus.OPTIMAL
            else solver_status
        )
        return {
            "dmu_id": dmu_id,
            "period": period,
            "score": np.nan,
            "efficiency": np.nan,
            "distance": np.nan,
            "system_score": np.nan,
            "system_efficiency": np.nan,
            "organizational_factor": np.nan,
            "factor_interpretation": (
                "input_efficiency"
                if self.orientation is Orientation.INPUT
                else "output_inverse_efficiency"
            ),
            "is_efficient": pd.NA,
            "is_measure_efficient": pd.NA,
            "is_sequentially_efficient": pd.NA,
            "solver_status": reported_solver_status.value,
            "score_status": status,
            "target_status": "not_computed",
            "model_family": "network_sequential_radial",
            "orientation": self.orientation.value,
            "process_count": process_count,
            "reference_size": reference_size,
            "initial_processes_defined": False,
            "propagated_processes_defined": False,
            "primary_programmes": primary_programmes,
            "targets_may_be_nonunique": True,
            "target_selection": _TARGET_SELECTION,
        }

    def fit(self, data: NetworkData) -> DEAResult:
        """Evaluate every organization and propagate process improvements."""
        if not isinstance(data, NetworkData):
            raise TypeError("LewisSextonSequentialNetworkDEA.fit expects NetworkData")
        layout = compile_network_layout(data.network_spec)
        values = data.matrix(layout.variable_names)
        self._validate_data(data, values, layout)
        rts_by_process = _resolved_rts(
            self.returns_to_scale,
            layout.process_ids,
        )
        reference_plan = build_reference_plan(data, self.reference)
        compiled: dict[int, dict[str, _ProcessReference]] = {}
        link_id_by_column = {
            column: link.link_id for link in layout.links for column in link.columns
        }
        process_by_id = {process.process_id: process for process in layout.processes}

        summary_rows: list[dict[str, Any]] = []
        component_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        link_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []
        total_primary_programmes = 0

        for observation in range(data.n_dmus):
            set_id = reference_plan.set_id_for(observation)
            references = compiled.get(set_id)
            if references is None:
                references = _compile_process_references(
                    values,
                    layout,
                    reference_plan.rows_for(observation),
                )
                compiled[set_id] = references

            observed = values[observation]
            dmu_id = data.dmu_ids[observation]
            period = None if data.periods is None else data.periods[observation]
            label = f"{dmu_id}@{period}" if period is not None else str(dmu_id)
            local_components: list[dict[str, Any]] = []
            local_targets: list[dict[str, Any]] = []
            local_intensities: list[dict[str, Any]] = []
            local_links: list[dict[str, Any]] = []
            initial: dict[str, _ProcessSolve] = {}
            propagated: dict[str, _ProcessSolve] = {}
            failed_status: str | None = None
            failed_solver_status = SolverStatus.OPTIMAL
            primary_programmes = 0

            for process in layout.processes:
                reference = references[process.process_id]
                record, solution, reason, economic_violation = self._solve_process(
                    reference=reference,
                    returns_to_scale=rts_by_process[process.process_id],
                    input_evaluation=observed[list(reference.input_columns)],
                    output_evaluation=observed[list(reference.output_columns)],
                    name=f"{label}:{process.process_id}:initial",
                )
                primary_programmes += 1
                total_primary_programmes += 1
                diagnostic_rows.append(
                    _diagnostic_row(
                        dmu_id=dmu_id,
                        period=period,
                        process_id=process.process_id,
                        phase="initial",
                        solution=solution,
                        certificate_reason=reason,
                        certificate_status=(
                            "certified" if record is not None else "failed"
                        ),
                        max_economic_violation=economic_violation,
                        solve_reused=False,
                    )
                )
                if record is None:
                    failed_status = (
                        "solver_failed"
                        if solution.status is not SolverStatus.OPTIMAL
                        else "certificate_failed"
                    )
                    failed_solver_status = solution.status
                    break
                initial[process.process_id] = record
                local_components.append(
                    self._component_row(
                        dmu_id=dmu_id,
                        period=period,
                        process_id=process.process_id,
                        phase="initial",
                        record=record,
                        returns_to_scale=rts_by_process[process.process_id],
                        solve_reused=False,
                    )
                )
                local_targets.extend(
                    self._target_rows(
                        dmu_id=dmu_id,
                        period=period,
                        process=process,
                        reference=reference,
                        record=record,
                        observed=observed,
                        phase="initial",
                        link_id_by_column=link_id_by_column,
                        solve_reused=False,
                    )
                )
                local_intensities.extend(
                    self._intensity_rows(
                        data=data,
                        dmu_id=dmu_id,
                        period=period,
                        process_id=process.process_id,
                        phase="initial",
                        reference=reference,
                        record=record,
                        solve_reused=False,
                    )
                )

            propagation_order = (
                layout.processes
                if self.orientation is Orientation.OUTPUT
                else tuple(reversed(layout.processes))
            )
            link_state: dict[int, float] = {}
            if failed_status is None:
                for process in propagation_order:
                    reference = references[process.process_id]
                    reuse_initial = (
                        not process.incoming_links
                        if self.orientation is Orientation.OUTPUT
                        else not process.outgoing_links
                    )
                    if reuse_initial:
                        record = initial[process.process_id]
                        solution = record.solution
                        reason = "initial_solution_reused_no_affected_links"
                        economic_violation = record.max_economic_violation
                    else:
                        evaluation = observed.copy()
                        changed_columns = (
                            process.incoming_link_columns
                            if self.orientation is Orientation.OUTPUT
                            else process.outgoing_link_columns
                        )
                        for column in changed_columns:
                            try:
                                evaluation[column] = link_state[column]
                            except KeyError as error:
                                raise RuntimeError(
                                    "canonical propagation order did not provide "
                                    "network variable "
                                    f"{layout.variable_names[column]!r}"
                                ) from error
                        record, solution, reason, economic_violation = (
                            self._solve_process(
                                reference=reference,
                                returns_to_scale=rts_by_process[process.process_id],
                                input_evaluation=evaluation[
                                    list(reference.input_columns)
                                ],
                                output_evaluation=evaluation[
                                    list(reference.output_columns)
                                ],
                                name=(f"{label}:{process.process_id}:propagated"),
                            )
                        )
                        primary_programmes += 1
                        total_primary_programmes += 1

                    diagnostic_rows.append(
                        _diagnostic_row(
                            dmu_id=dmu_id,
                            period=period,
                            process_id=process.process_id,
                            phase="propagated",
                            solution=solution,
                            certificate_reason=reason,
                            certificate_status=(
                                "certified" if record is not None else "failed"
                            ),
                            max_economic_violation=economic_violation,
                            solve_reused=reuse_initial,
                        )
                    )
                    if record is None:
                        failed_status = (
                            "solver_failed"
                            if solution.status is not SolverStatus.OPTIMAL
                            else "certificate_failed"
                        )
                        failed_solver_status = solution.status
                        break
                    propagated[process.process_id] = record
                    if self.orientation is Orientation.OUTPUT:
                        produced = dict(
                            zip(
                                reference.output_columns,
                                record.output_targets,
                                strict=True,
                            )
                        )
                        for column in process.outgoing_link_columns:
                            link_state[column] = float(produced[column])
                    else:
                        consumed = dict(
                            zip(
                                reference.input_columns,
                                record.input_targets,
                                strict=True,
                            )
                        )
                        for column in process.incoming_link_columns:
                            link_state[column] = float(consumed[column])

                    local_components.append(
                        self._component_row(
                            dmu_id=dmu_id,
                            period=period,
                            process_id=process.process_id,
                            phase="propagated",
                            record=record,
                            returns_to_scale=rts_by_process[process.process_id],
                            solve_reused=reuse_initial,
                        )
                    )
                    local_targets.extend(
                        self._target_rows(
                            dmu_id=dmu_id,
                            period=period,
                            process=process,
                            reference=reference,
                            record=record,
                            observed=observed,
                            phase="propagated",
                            link_id_by_column=link_id_by_column,
                            solve_reused=reuse_initial,
                        )
                    )
                    local_intensities.extend(
                        self._intensity_rows(
                            data=data,
                            dmu_id=dmu_id,
                            period=period,
                            process_id=process.process_id,
                            phase="propagated",
                            reference=reference,
                            record=record,
                            solve_reused=reuse_initial,
                        )
                    )

            if failed_status is None:
                for link in layout.links:
                    source_record = propagated[link.source]
                    target_record = propagated[link.target]
                    source_reference = references[link.source]
                    target_reference = references[link.target]
                    source_targets = dict(
                        zip(
                            source_reference.output_columns,
                            source_record.output_targets,
                            strict=True,
                        )
                    )
                    target_targets = dict(
                        zip(
                            target_reference.input_columns,
                            target_record.input_targets,
                            strict=True,
                        )
                    )
                    for column in link.columns:
                        supply = float(source_targets[column])
                        requirement = float(target_targets[column])
                        scale = max(
                            1.0,
                            abs(float(observed[column])),
                            abs(supply),
                            abs(requirement),
                        )
                        residual = supply - requirement
                        if residual < -self.tolerance * scale:
                            failed_status = "propagation_balance_failed"
                            failed_solver_status = SolverStatus.NUMERICAL_ERROR
                            diagnostic_rows.append(
                                {
                                    "dmu_id": dmu_id,
                                    "period": period,
                                    "process_id": None,
                                    "phase": "organizational",
                                    "solver_status": (
                                        SolverStatus.NUMERICAL_ERROR.value
                                    ),
                                    "message": (
                                        "propagated upstream supply is below "
                                        "downstream requirement"
                                    ),
                                    "iterations": None,
                                    "max_primal_violation": None,
                                    "certification_status": "failed",
                                    "certificate_reason": (
                                        "link_balance_certificate_failed"
                                    ),
                                    "max_economic_constraint_violation": (
                                        -residual / scale
                                    ),
                                    "solve_reused": False,
                                }
                            )
                            break
                        if abs(residual) <= self.tolerance * scale:
                            residual = 0.0
                        transmitted = (
                            supply
                            if self.orientation is Orientation.OUTPUT
                            else requirement
                        )
                        local_links.append(
                            {
                                "dmu_id": dmu_id,
                                "period": period,
                                "link_id": link.link_id,
                                "source_process_id": link.source,
                                "target_process_id": link.target,
                                "variable": layout.variable_names[column],
                                "observed": float(observed[column]),
                                "transmitted_quantity": transmitted,
                                "upstream_supply_target": supply,
                                "downstream_requirement_target": requirement,
                                "disposable_surplus": residual,
                                "balance_residual": residual,
                                "propagation_direction": (
                                    "forward"
                                    if self.orientation is Orientation.OUTPUT
                                    else "backward"
                                ),
                                "target_selection": _TARGET_SELECTION,
                                "target_uniqueness": "not_tested",
                            }
                        )
                    if failed_status is not None:
                        break

            if failed_status is not None:
                summary_rows.append(
                    self._failure_summary(
                        dmu_id=dmu_id,
                        period=period,
                        status=failed_status,
                        solver_status=failed_solver_status,
                        process_count=layout.n_processes,
                        reference_size=int(reference_plan.rows_for(observation).size),
                        primary_programmes=primary_programmes,
                    )
                )
                continue

            external_targets: dict[int, float] = {}
            for process_id, record in propagated.items():
                process = process_by_id[process_id]
                reference = references[process_id]
                input_targets = dict(
                    zip(
                        reference.input_columns,
                        record.input_targets,
                        strict=True,
                    )
                )
                output_targets = dict(
                    zip(
                        reference.output_columns,
                        record.output_targets,
                        strict=True,
                    )
                )
                for column in process.external_input_columns:
                    external_targets[column] = float(input_targets[column])
                for column in process.external_output_columns:
                    external_targets[column] = float(output_targets[column])

            account_columns = (
                range(
                    layout.external_input_slice.start,
                    layout.external_input_slice.stop,
                )
                if self.orientation is Orientation.INPUT
                else range(
                    layout.external_output_slice.start,
                    layout.external_output_slice.stop,
                )
            )
            ratios = [
                external_targets[column] / float(observed[column])
                for column in account_columns
                if observed[column] > self.tolerance
            ]
            organizational_factor = (
                max(ratios) if self.orientation is Orientation.INPUT else min(ratios)
            )
            if abs(organizational_factor - 1.0) <= self.tolerance:
                organizational_factor = 1.0
            system_efficiency = (
                organizational_factor
                if self.orientation is Orientation.INPUT
                else 1.0 / organizational_factor
            )
            is_efficient = bool(abs(system_efficiency - 1.0) <= self.tolerance)
            local_components.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "component_kind": "system",
                    "component_id": "organization",
                    "process_id": None,
                    "phase": "organizational",
                    "score": system_efficiency,
                    "efficiency": system_efficiency,
                    "radial_factor": organizational_factor,
                    "factor_interpretation": (
                        "input_efficiency"
                        if self.orientation is Orientation.INPUT
                        else "output_inverse_efficiency"
                    ),
                    "is_measure_efficient": is_efficient,
                    "status": "defined",
                    "orientation": self.orientation.value,
                    "returns_to_scale": "process_specific",
                    "solve_reused": False,
                    "omitted_intensity_sum": np.nan,
                    "target_selection": _TARGET_SELECTION,
                    "target_uniqueness": "not_tested",
                }
            )
            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "score": system_efficiency,
                    "efficiency": system_efficiency,
                    "distance": np.nan,
                    "system_score": system_efficiency,
                    "system_efficiency": system_efficiency,
                    "organizational_factor": organizational_factor,
                    "factor_interpretation": (
                        "input_efficiency"
                        if self.orientation is Orientation.INPUT
                        else "output_inverse_efficiency"
                    ),
                    "is_efficient": pd.NA,
                    "is_measure_efficient": is_efficient,
                    "is_sequentially_efficient": is_efficient,
                    "solver_status": SolverStatus.OPTIMAL.value,
                    "score_status": "defined",
                    "target_status": "defined_solver_selected",
                    "model_family": "network_sequential_radial",
                    "orientation": self.orientation.value,
                    "process_count": layout.n_processes,
                    "reference_size": int(reference_plan.rows_for(observation).size),
                    "initial_processes_defined": True,
                    "propagated_processes_defined": True,
                    "primary_programmes": primary_programmes,
                    "targets_may_be_nonunique": True,
                    "target_selection": _TARGET_SELECTION,
                }
            )
            component_rows.extend(local_components)
            target_rows.extend(local_targets)
            intensity_rows.extend(local_intensities)
            link_rows.extend(local_links)

        propagation_order_ids = (
            layout.process_ids
            if self.orientation is Orientation.OUTPUT
            else tuple(reversed(layout.process_ids))
        )
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
                                "organizational_performance_with_propagated_"
                                "process_improvements"
                            ),
                            "sample": ("panel" if data.is_panel else "cross_section"),
                            "decision_scope": "centralized_internal_sequence",
                        },
                        "graph": {
                            "kind": "directed_acyclic",
                            "processes": list(layout.process_ids),
                            "links": [
                                {
                                    "id": link.link_id,
                                    "source": link.source,
                                    "target": link.target,
                                    "variables": list(link.variables),
                                    "intensity_policy": "process_specific",
                                    "balance": (
                                        "upstream_supply_greater_than_or_"
                                        "equal_to_downstream_requirement"
                                    ),
                                }
                                for link in layout.links
                            ],
                            "propagation_order": list(propagation_order_ids),
                            "propagation_direction": (
                                "forward"
                                if self.orientation is Orientation.OUTPUT
                                else "backward"
                            ),
                        },
                        "data_roles": {
                            "variables": {
                                "external_inputs": list(layout.external_inputs),
                                "intermediate_links": list(layout.link_variables),
                                "external_outputs": list(layout.external_outputs),
                            },
                            "counts": {
                                "external_inputs": len(layout.external_inputs),
                                "intermediate_links": len(layout.link_variables),
                                "external_outputs": len(layout.external_outputs),
                            },
                            "representation": {
                                "measurement_scale": "quantity",
                                "sign_domain": "nonnegative",
                                "flow_type": "forward_only",
                                "endpoint_identity": (
                                    "one_unambiguous_column_per_system_"
                                    "input_or_output_type"
                                ),
                            },
                            "panel": data.is_panel,
                            "grouped": data.groups is not None,
                        },
                        "technology": {
                            "family": "sequential_process_envelopment",
                            "returns_to_scale_by_process": {
                                process_id: (rts_by_process[process_id].value)
                                for process_id in layout.process_ids
                            },
                            "intensity_coupling": "process_specific",
                            "link_disposal": ("upstream_surplus_freely_disposable"),
                            "convexity": "selected_separately_by_process",
                        },
                        "estimator": {
                            "estimator_id": "estimator.full.dea",
                            "kind": "full_frontier",
                            "family": "dea_sequential_network_envelopment",
                        },
                        "reference": registry_reference_spec(
                            self.reference,
                            reference_plan.kind,
                        ),
                        "performance": {
                            "family": "lewis_sexton_sequential_radial",
                            "orientation": self.orientation.value,
                            "process_factor": (
                                "input_efficiency"
                                if self.orientation is Orientation.INPUT
                                else "output_inverse_efficiency"
                            ),
                            "organizational_factor_formula": (
                                "max_i_sum_s_target_input_over_sum_s_observed_input"
                                if self.orientation is Orientation.INPUT
                                else "min_r_sum_s_target_output_over_sum_s_"
                                "observed_output"
                            ),
                            "endpoint_aggregation_contract": (
                                "paper_sum_over_processes_collapses_to_one_"
                                "declared_owner_per_endpoint_type"
                            ),
                        },
                        "valuation": {"kind": "none"},
                        "evaluation_protocol": {
                            "kind": "self_appraisal_then_sequential_reappraisal",
                            "initial_programmes_per_observation": (layout.n_processes),
                            "propagated_source_or_sink_programmes": (
                                "reuse_initial_when_unaffected"
                            ),
                            "secondary_objective": "none",
                            "target_selection": _TARGET_SELECTION,
                        },
                        "analysis": {
                            "kind": "direct_network_fit",
                            "process_accounts": [
                                "initial",
                                "propagated",
                                "organizational",
                            ],
                        },
                        "uncertainty": {
                            "sampling": {"kind": "none"},
                            "data": {"kind": "none"},
                        },
                    },
                ),
                "model_family": "network_sequential_radial",
                "source": {
                    "authors": ["Herbert F. Lewis", "Thomas R. Sexton"],
                    "year": 2004,
                    "doi": "10.1016/S0305-0548(03)00095-9",
                    "implemented_scope": "linear_forward_quantities",
                },
                "scope": {
                    "included": [
                        "nonnegative_forward_quantities",
                        "global_input_or_output_orientation",
                        "process_specific_crs_vrs_nirs_ndrs",
                        "acyclic_networks",
                        "multiple_distinct_system_input_and_output_types",
                        "one_declared_owner_per_system_endpoint_type",
                    ],
                    "excluded": [
                        "reverse_quantities",
                        "mixed_forward_reverse_quantities",
                        "site_characteristic_adjustments",
                        "mixed_process_orientations",
                        "cross_process_shared_endpoint_type_aggregation",
                    ],
                },
                "orientation": self.orientation.value,
                "returns_to_scale_by_process": {
                    process_id: rts_by_process[process_id].value
                    for process_id in layout.process_ids
                },
                "process_order": list(layout.process_ids),
                "propagation_order": list(propagation_order_ids),
                "propagation_direction": (
                    "forward" if self.orientation is Orientation.OUTPUT else "backward"
                ),
                "graph_fingerprint": data.graph_fingerprint,
                "reference_kind": reference_plan.kind.value,
                "compiled_reference_sets": (reference_plan.unique_reference_sets),
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "target_selection": {
                    "policy": _TARGET_SELECTION,
                    "uniqueness": "not_tested",
                    "targets_use_unthresholded_intensities": True,
                    "interpretation": (
                        "one optimal organizational improvement account, "
                        "not a unique managerial prescription"
                    ),
                },
                "intensity_reporting": {
                    "rule": "strictly_above_peer_tolerance",
                    "omitted_sums_reported_in_components": True,
                },
                "total_primary_programmes": total_primary_programmes,
            },
        )


__all__ = ["LewisSextonSequentialNetworkDEA"]
