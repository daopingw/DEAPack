"""Tone--Tsutsui (2014) dynamic network slacks-based measure."""

from __future__ import annotations

import math
from collections.abc import Hashable, Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd

from .._registry import registry_metadata
from ..enums import ReturnsToScale, SolverStatus, parse_enum
from ..exceptions import ModelSpecificationError
from ..results import DEAResult
from ..solvers import (
    LPCertificate,
    LPSolution,
    LPSolver,
    SciPyHiGHSSolver,
    certify_lp_solution,
)
from ..specs import SolverOptions
from ._dynamic_network_sbm import (
    CompiledDynamicNetworkSBMReference,
    DynamicNetworkSBMOrientation,
    compile_dynamic_network_sbm_reference,
    dynamic_network_sbm_problem,
    parse_dynamic_network_sbm_orientation,
)
from ._layout import (
    CompiledDynamicNetworkProcess,
    CompiledDynamicNetworkSBMLayout,
    compile_dynamic_network_sbm_layout,
)
from .data import DynamicNetworkData
from .specs import NetworkSBMLinkKind

_SLACK_ROLES = (
    "external_input",
    "external_output",
    "as_input",
    "as_output",
    "good_carryover",
    "bad_carryover",
    "free_carryover",
)
_TARGET_ROLES = (*_SLACK_ROLES, "fixed_carryover")
_INPUT_ROLES = frozenset({"external_input", "as_input", "bad_carryover"})
_OUTPUT_ROLES = frozenset({"external_output", "as_output", "good_carryover"})
_SELECTION_STATUS = "solver_selected_not_uniqueness_certified"


def _clean(values: np.ndarray, tolerance: float) -> np.ndarray:
    result = np.asarray(values, dtype=np.float64).copy()
    result[np.abs(result) <= tolerance] = 0.0
    return result


def _normalized_named_weights(
    supplied: Mapping[Hashable, float] | None,
    labels: Sequence[Hashable],
    *,
    field: str,
) -> tuple[np.ndarray, str]:
    ordered = tuple(labels)
    if supplied is None:
        values = np.ones(len(ordered), dtype=np.float64)
        source = "equal_default"
    else:
        if not isinstance(supplied, Mapping):
            raise TypeError(f"{field} must be a label-to-weight mapping")
        expected = set(ordered)
        actual = set(supplied)
        missing = expected.difference(actual)
        extra = actual.difference(expected)
        if missing or extra:
            raise ValueError(
                f"{field} must contain every label exactly once; "
                f"missing={list(missing)!r}, extra={list(extra)!r}"
            )
        resolved: list[float] = []
        for label in ordered:
            value = supplied[label]
            if isinstance(value, bool) or not isinstance(
                value,
                (int, float, np.integer, np.floating),
            ):
                raise TypeError(f"{field} values must be real numbers")
            numeric = float(value)
            if not math.isfinite(numeric) or numeric < 0:
                raise ValueError(f"{field} values must be finite and nonnegative")
            resolved.append(numeric)
        values = np.asarray(resolved, dtype=np.float64)
        if not np.any(values > 0):
            raise ValueError(f"{field} must contain at least one positive value")
        source = "user_relative_normalized"
    values /= float(np.sum(values))
    values.setflags(write=False)
    return values, source


def _decomposition_policy(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("decomposition_policy must be a string")
    normalized = value.strip().lower().replace("-", "_")
    if normalized != "solver_selected":
        raise ValueError(
            "decomposition_policy currently supports only 'solver_selected'; "
            "the source reverse-chronological period-priority rule is a "
            "separate pending specialization"
        )
    return normalized


def _role_columns(
    process: CompiledDynamicNetworkProcess,
    role: str,
) -> tuple[int, ...]:
    roles = {
        "external_input": process.input_columns,
        "external_output": process.output_columns,
        "as_input": process.as_input_columns,
        "as_output": process.as_output_columns,
        "good_carryover": process.good_columns,
        "bad_carryover": process.bad_columns,
        "free_carryover": process.free_columns,
        "fixed_carryover": process.fixed_columns,
    }
    return roles[role]


def _role_variables(
    layout: CompiledDynamicNetworkSBMLayout,
    process: CompiledDynamicNetworkProcess,
    role: str,
) -> tuple[str, ...]:
    columns = _role_columns(process, role)
    return tuple(layout.variable_names[column] for column in columns)


def _included_in_objective(
    orientation: DynamicNetworkSBMOrientation,
    role: str,
) -> bool:
    if role in _INPUT_ROLES:
        return orientation in {"input", "non-oriented"}
    if role in _OUTPUT_ROLES:
        return orientation in {"output", "non-oriented"}
    return False


def _efficiency(
    orientation: DynamicNetworkSBMOrientation,
    input_account: float,
    output_account: float,
) -> float:
    if orientation == "input":
        return input_account
    if orientation == "output":
        return 1.0 / output_account
    return input_account / output_account


def _solver_efficiency(
    orientation: DynamicNetworkSBMOrientation,
    objective: float,
) -> float:
    if orientation == "output":
        return 1.0 / (-objective)
    return objective


def _diagnostic(
    *,
    dmu_id: object,
    solution: LPSolution,
    certificate: LPCertificate,
) -> dict[str, Any]:
    semantic_status = (
        solution.status.value
        if solution.status is not SolverStatus.OPTIMAL or certificate.certified
        else SolverStatus.NUMERICAL_ERROR.value
    )
    return {
        "dmu_id": dmu_id,
        "period": None,
        "phase": "primary",
        "solver_status": semantic_status,
        "backend_solver_status": solution.status.value,
        "raw_solver_status": solution.status.value,
        "message": solution.message,
        "iterations": solution.iterations,
        "max_primal_violation": solution.max_primal_violation,
        "postsolve_certified": certificate.certified,
        "certification_reason": certificate.reason,
        "max_constraint_violation": certificate.max_constraint_violation,
        "equality_violation": certificate.equality_violation,
        "max_bound_violation": certificate.max_bound_violation,
        "objective_residual": certificate.objective_residual,
        "duality_gap": certificate.duality_gap,
        "max_dual_violation": certificate.max_dual_violation,
        "complementarity_violation": certificate.complementarity_violation,
        "bound_marginals_used": certificate.bound_marginals_used,
        "economic_postsolve_certified": pd.NA,
        "economic_certification_reason": "not_checked",
        "max_economic_violation": np.nan,
    }


def _dynamic_network_economic_postsolve_violation(
    *,
    transform_scale: float,
    efficiency: float,
    solver_efficiency: float,
    reconstruction_residual: float,
    input_accounts: np.ndarray,
    output_accounts: np.ndarray,
    max_balance_residual: float,
    max_link_residual: float,
    max_carryover_residual: float,
    max_fixed_link_residual: float,
    max_fixed_carryover_residual: float,
    component_reconstruction_residual: float,
) -> float:
    """Return the largest source-account reconstruction violation.

    This certificate is deliberately independent of the backend's status and
    objective claim.  The LP certificate establishes KKT optimality; this
    second gate establishes that the accepted primal reconstructs the
    economic score and every published balance account.
    """
    scalars = np.asarray(
        [
            transform_scale,
            efficiency,
            solver_efficiency,
            reconstruction_residual,
            max_balance_residual,
            max_link_residual,
            max_carryover_residual,
            max_fixed_link_residual,
            max_fixed_carryover_residual,
            component_reconstruction_residual,
        ],
        dtype=np.float64,
    )
    inputs = np.asarray(input_accounts, dtype=np.float64)
    outputs = np.asarray(output_accounts, dtype=np.float64)
    if (
        transform_scale <= 0.0
        or not np.isfinite(scalars).all()
        or not np.isfinite(inputs).all()
        or not np.isfinite(outputs).all()
    ):
        return math.inf
    score_range_violation = max(-efficiency, efficiency - 1.0, 0.0)
    input_account_violation = float(
        max(
            np.maximum(-inputs, 0.0).max(initial=0.0),
            np.maximum(inputs - 1.0, 0.0).max(initial=0.0),
        )
    )
    output_account_violation = float(np.maximum(1.0 - outputs, 0.0).max(initial=0.0))
    return max(
        score_range_violation,
        input_account_violation,
        output_account_violation,
        abs(reconstruction_residual),
        abs(max_balance_residual),
        abs(max_link_residual),
        abs(max_carryover_residual),
        abs(max_fixed_link_residual),
        abs(max_fixed_carryover_residual),
        abs(component_reconstruction_residual),
    )


class ToneTsutsuiDynamicNetworkSBM:
    """Appraise a connected multi-process operating plan over time.

    The fitted score is the performance of the complete organization over the
    full planning horizon. Period, process, and period-by-process accounts are
    conditional explanations of one joint optimum; unless a secondary
    selection rule is requested by a future specialization, they are not
    claimed to be unique.

    ``as_input`` links belong to the receiving process's resource account,
    while ``as_output`` links belong to the supplying process's service
    account. Good and bad carry-overs enter output and input accounts,
    respectively. Free and fixed links or carry-overs constrain feasible plans
    but do not enter the base score.
    """

    _registry_method_id = "dynamic.network_sbm.tone_tsutsui_2014"

    def __init__(
        self,
        *,
        orientation: str = "non-oriented",
        returns_to_scale: (
            ReturnsToScale | str | Mapping[str, ReturnsToScale | str]
        ) = ReturnsToScale.VRS,
        period_weights: Mapping[Hashable, float] | None = None,
        division_weights: Mapping[str, float] | None = None,
        decomposition_policy: str = "solver_selected",
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.orientation = parse_dynamic_network_sbm_orientation(orientation)
        if isinstance(returns_to_scale, Mapping):
            self.returns_to_scale = dict(returns_to_scale)
        else:
            resolved = parse_enum(
                returns_to_scale,
                ReturnsToScale,
                "returns_to_scale",
            )
            self._validate_source_rts(resolved)
            self.returns_to_scale = resolved
        for supplied, field in (
            (period_weights, "period_weights"),
            (division_weights, "division_weights"),
        ):
            if supplied is not None and not isinstance(supplied, Mapping):
                raise TypeError(f"{field} must be a label-to-weight mapping")
        self.period_weights = period_weights
        self.division_weights = division_weights
        self.decomposition_policy = _decomposition_policy(decomposition_policy)
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

    @staticmethod
    def _validate_source_rts(value: ReturnsToScale) -> None:
        if value not in {ReturnsToScale.CRS, ReturnsToScale.VRS}:
            raise ValueError(
                "ToneTsutsuiDynamicNetworkSBM supports CRS or VRS for each process only"
            )

    def _resolved_rts(
        self,
        layout: CompiledDynamicNetworkSBMLayout,
    ) -> tuple[ReturnsToScale, ...]:
        if not isinstance(self.returns_to_scale, dict):
            return (self.returns_to_scale,) * layout.n_processes
        supplied = self.returns_to_scale
        expected = set(layout.process_ids)
        actual = set(supplied)
        missing = expected.difference(actual)
        extra = actual.difference(expected)
        if missing or extra:
            raise ValueError(
                "returns_to_scale mapping must contain every process exactly "
                f"once; missing={sorted(missing)!r}, extra={sorted(extra)!r}"
            )
        resolved: list[ReturnsToScale] = []
        for process_id in layout.process_ids:
            value = parse_enum(
                supplied[process_id],
                ReturnsToScale,
                f"returns_to_scale[{process_id!r}]",
            )
            self._validate_source_rts(value)
            resolved.append(value)
        return tuple(resolved)

    def _weights(
        self,
        data: DynamicNetworkData,
        layout: CompiledDynamicNetworkSBMLayout,
    ) -> tuple[np.ndarray, np.ndarray, dict[str, str]]:
        periods, period_source = _normalized_named_weights(
            self.period_weights,
            data.periods,
            field="period_weights",
        )
        divisions, division_source = _normalized_named_weights(
            self.division_weights,
            layout.process_ids,
            field="division_weights",
        )
        return (
            periods,
            divisions,
            {
                "period": period_source,
                "division": division_source,
            },
        )

    def _validate_data(
        self,
        data: DynamicNetworkData,
    ) -> None:
        data.ensure_strictly_positive(model_name="Tone--Tsutsui dynamic network SBM")
        if data.dynamic_network_spec.boundary_policy != "tone_tsutsui_2014_core":
            raise ModelSpecificationError(
                "unsupported dynamic-network SBM boundary policy"
            )

    def fit(self, data: DynamicNetworkData) -> DEAResult:
        """Estimate one joint dynamic-network programme per DMU trajectory."""
        if not isinstance(data, DynamicNetworkData):
            raise TypeError(
                "ToneTsutsuiDynamicNetworkSBM.fit expects DynamicNetworkData"
            )
        layout = compile_dynamic_network_sbm_layout(data.dynamic_network_spec)
        self._validate_data(data)
        returns_to_scale = self._resolved_rts(layout)
        period_weights, division_weights, weight_sources = self._weights(
            data,
            layout,
        )
        reference = compile_dynamic_network_sbm_reference(
            data.values,
            data.variable_names,
            layout,
            np.arange(data.n_dmus, dtype=np.int64),
            orientation=self.orientation,
            returns_to_scale=returns_to_scale,
        )

        summary_rows: list[dict[str, Any]] = []
        component_rows: list[dict[str, Any]] = []
        slack_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        link_rows: list[dict[str, Any]] = []
        dual_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []

        for observation in range(data.n_dmus):
            dmu_id = data.dmu_ids[observation]
            problem = dynamic_network_sbm_problem(
                reference,
                data.values[:, observation, :],
                period_weights=period_weights,
                division_weights=division_weights,
                name=str(dmu_id),
            )
            solution = self.solver.solve(problem)
            certificate = certify_lp_solution(
                problem,
                solution=solution,
                tolerance=self.tolerance,
            )
            diagnostic_rows.append(
                _diagnostic(
                    dmu_id=dmu_id,
                    solution=solution,
                    certificate=certificate,
                )
            )
            if not certificate.certified or solution.primal is None:
                summary_rows.append(
                    self._undefined_summary(
                        dmu_id=dmu_id,
                        data=data,
                        reference=reference,
                        semantic_solver_status=(
                            solution.status.value
                            if solution.status is not SolverStatus.OPTIMAL
                            else SolverStatus.NUMERICAL_ERROR.value
                        ),
                        backend_solver_status=solution.status,
                        score_status=(
                            "solver_failed"
                            if solution.status is not SolverStatus.OPTIMAL
                            else "unavailable_uncertified_source_program"
                        ),
                    )
                )
                continue

            primal = solution.primal
            tau = float(primal[reference.tau_index])
            # Charnes--Cooper requires only a finite, strictly positive scale.
            # Comparing tau with the numerical tolerance rejects valid very
            # small efficiencies and is therefore not a mathematical gate.
            if not math.isfinite(tau) or tau <= 0.0:
                diagnostic_rows[-1].update(
                    {
                        "solver_status": SolverStatus.NUMERICAL_ERROR.value,
                        "postsolve_certified": False,
                        "certification_reason": "invalid_transform_scale",
                        "economic_postsolve_certified": False,
                        "economic_certification_reason": "invalid_transform_scale",
                        "max_economic_violation": math.inf,
                    }
                )
                summary_rows.append(
                    self._undefined_summary(
                        dmu_id=dmu_id,
                        data=data,
                        reference=reference,
                        semantic_solver_status=SolverStatus.NUMERICAL_ERROR.value,
                        backend_solver_status=solution.status,
                        score_status="unavailable_uncertified_source_program",
                    )
                )
                continue
            lambdas = self._extract_lambdas(
                primal=primal,
                reference=reference,
                transform_scale=tau,
            )
            slacks = self._extract_slacks(
                primal=primal,
                reference=reference,
                transform_scale=tau,
            )
            observed = reference.canonical_observation(data.values[:, observation, :])
            normalized_slacks, input_accounts, output_accounts = self._accounts(
                observed=observed,
                slacks=slacks,
                layout=layout,
            )
            account_summary = self._aggregate_accounts(
                input_accounts=input_accounts,
                output_accounts=output_accounts,
                period_weights=period_weights,
                division_weights=division_weights,
            )
            system_input = float(account_summary["system_input"])
            system_output = float(account_summary["system_output"])
            objective_value = float(solution.objective)
            accounts_define_score = bool(
                math.isfinite(system_input)
                and math.isfinite(system_output)
                and math.isfinite(objective_value)
                and (self.orientation == "input" or system_output > 0.0)
                and (self.orientation != "output" or -objective_value > 0.0)
            )
            if not accounts_define_score:
                diagnostic_rows[-1].update(
                    {
                        "solver_status": SolverStatus.NUMERICAL_ERROR.value,
                        "postsolve_certified": False,
                        "certification_reason": "invalid_source_accounts",
                        "economic_postsolve_certified": False,
                        "economic_certification_reason": "invalid_source_accounts",
                        "max_economic_violation": math.inf,
                    }
                )
                summary_rows.append(
                    self._undefined_summary(
                        dmu_id=dmu_id,
                        data=data,
                        reference=reference,
                        semantic_solver_status=SolverStatus.NUMERICAL_ERROR.value,
                        backend_solver_status=solution.status,
                        score_status="unavailable_uncertified_source_program",
                    )
                )
                continue
            efficiency = _efficiency(
                self.orientation,
                system_input,
                system_output,
            )
            solver_efficiency = _solver_efficiency(
                self.orientation,
                objective_value,
            )
            reconstruction_residual = efficiency - solver_efficiency
            benchmarks = self._benchmarks(
                lambdas=lambdas,
                reference=reference,
            )

            # Build every semantic table transactionally.  Nothing from this
            # DMU is committed until both the LP and economic certificates
            # pass, preventing partial targets, links, peers, or components.
            local_component_rows: list[dict[str, Any]] = []
            local_slack_rows: list[dict[str, Any]] = []
            local_target_rows: list[dict[str, Any]] = []
            local_intensity_rows: list[dict[str, Any]] = []
            local_link_rows: list[dict[str, Any]] = []
            local_dual_rows: list[dict[str, Any]] = []
            max_balance_residual = self._append_targets_and_slacks(
                target_rows=local_target_rows,
                slack_rows=local_slack_rows,
                data=data,
                dmu_id=dmu_id,
                reference=reference,
                observed=observed,
                benchmarks=benchmarks,
                slacks=slacks,
                normalized_slacks=normalized_slacks,
                period_weights=period_weights,
                division_weights=division_weights,
            )
            (
                max_link_residual,
                max_fixed_link_residual,
            ) = self._append_within_period_links(
                rows=local_link_rows,
                data=data,
                dmu_id=dmu_id,
                reference=reference,
                observed=observed,
                benchmarks=benchmarks,
                slacks=slacks,
                period_weights=period_weights,
                division_weights=division_weights,
            )
            (
                max_carryover_residual,
                max_fixed_carryover_residual,
            ) = self._append_carryovers(
                rows=local_link_rows,
                data=data,
                dmu_id=dmu_id,
                reference=reference,
                observed=observed,
                benchmarks=benchmarks,
                lambdas=lambdas,
                slacks=slacks,
                period_weights=period_weights,
                division_weights=division_weights,
            )
            self._append_intensities(
                rows=local_intensity_rows,
                data=data,
                dmu_id=dmu_id,
                reference=reference,
                lambdas=lambdas,
            )
            component_reconstruction_residual = self._append_components(
                rows=local_component_rows,
                data=data,
                dmu_id=dmu_id,
                reference=reference,
                input_accounts=input_accounts,
                output_accounts=output_accounts,
                account_summary=account_summary,
                period_weights=period_weights,
                division_weights=division_weights,
                system_efficiency=efficiency,
            )

            max_economic_violation = _dynamic_network_economic_postsolve_violation(
                transform_scale=tau,
                efficiency=efficiency,
                solver_efficiency=solver_efficiency,
                reconstruction_residual=reconstruction_residual,
                input_accounts=input_accounts,
                output_accounts=output_accounts,
                max_balance_residual=max_balance_residual,
                max_link_residual=max_link_residual,
                max_carryover_residual=max_carryover_residual,
                max_fixed_link_residual=max_fixed_link_residual,
                max_fixed_carryover_residual=max_fixed_carryover_residual,
                component_reconstruction_residual=(component_reconstruction_residual),
            )
            economic_certified = bool(
                math.isfinite(max_economic_violation)
                and max_economic_violation <= 10.0 * self.tolerance
            )
            diagnostic_rows[-1].update(
                {
                    "economic_postsolve_certified": economic_certified,
                    "economic_certification_reason": (
                        "certified"
                        if economic_certified
                        else "source_account_reconstruction_failed"
                    ),
                    "max_economic_violation": max_economic_violation,
                }
            )
            if not economic_certified:
                diagnostic_rows[-1].update(
                    {
                        "solver_status": SolverStatus.NUMERICAL_ERROR.value,
                        "postsolve_certified": False,
                        "certification_reason": (
                            "source_account_reconstruction_failed"
                        ),
                    }
                )
                summary_rows.append(
                    self._undefined_summary(
                        dmu_id=dmu_id,
                        data=data,
                        reference=reference,
                        semantic_solver_status=SolverStatus.NUMERICAL_ERROR.value,
                        backend_solver_status=solution.status,
                        score_status="unavailable_uncertified_source_program",
                    )
                )
                continue

            # Equality marginals become economic duals only after every gate.
            self._append_duals(
                rows=local_dual_rows,
                data=data,
                dmu_id=dmu_id,
                reference=reference,
                solution=solution,
            )
            component_rows.extend(local_component_rows)
            slack_rows.extend(local_slack_rows)
            target_rows.extend(local_target_rows)
            intensity_rows.extend(local_intensity_rows)
            link_rows.extend(local_link_rows)
            dual_rows.extend(local_dual_rows)

            scored_values = [
                normalized_slacks[role][period][process.index]
                for role, periods in normalized_slacks.items()
                if _included_in_objective(self.orientation, role)
                for period, _ in enumerate(periods)
                if period_weights[period] > 0
                for process in layout.processes
                if division_weights[process.index] > 0
            ]
            all_slack_values = [
                values
                for periods in normalized_slacks.values()
                for processes in periods
                for values in processes
            ]
            max_scored_slack = max(
                (
                    float(np.max(np.abs(values), initial=0.0))
                    for values in scored_values
                ),
                default=0.0,
            )
            max_any_slack = max(
                (
                    float(np.max(np.abs(values), initial=0.0))
                    for values in all_slack_values
                ),
                default=0.0,
            )
            is_dynamic_network_sbm_efficient = bool(
                math.isclose(
                    efficiency,
                    1.0,
                    rel_tol=0.0,
                    abs_tol=self.tolerance,
                )
            )
            all_account_weights_positive = bool(
                np.all(period_weights > 0.0) and np.all(division_weights > 0.0)
            )
            is_efficient: bool | Any = (
                bool(
                    is_dynamic_network_sbm_efficient
                    and max_scored_slack <= self.tolerance
                )
                if (self.orientation == "non-oriented" and all_account_weights_positive)
                else pd.NA
            )
            mixed_rts = reference.has_mixed_returns_to_scale
            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": None,
                    "score": efficiency,
                    "efficiency": efficiency,
                    "system_efficiency": efficiency,
                    "score_valid": True,
                    "score_status": "defined",
                    "distance": 1.0 - efficiency,
                    "is_efficient": is_efficient,
                    "is_dynamic_network_sbm_efficient": (
                        is_dynamic_network_sbm_efficient
                    ),
                    "all_scored_slacks_zero": (max_scored_slack <= self.tolerance),
                    "all_slacks_zero": max_any_slack <= self.tolerance,
                    "solver_status": SolverStatus.OPTIMAL.value,
                    "backend_solver_status": solution.status.value,
                    "raw_solver_status": solution.status.value,
                    "model_family": "dynamic_network_slacks_based",
                    "orientation": self.orientation,
                    "returns_to_scale": (
                        "mixed" if mixed_rts else reference.returns_to_scale[0].value
                    ),
                    "overall_returns_to_scale_identified": (not mixed_rts),
                    "input_account": account_summary["system_input"],
                    "output_expansion_account": account_summary["system_output"],
                    "solver_objective": float(solution.objective),
                    "solver_efficiency": solver_efficiency,
                    "transform_scale": tau,
                    "reconstruction_residual": reconstruction_residual,
                    "max_balance_residual": max_balance_residual,
                    "max_link_continuity_residual": max_link_residual,
                    "max_carryover_continuity_residual": (max_carryover_residual),
                    "max_fixed_link_residual": max_fixed_link_residual,
                    "max_fixed_carryover_residual": (max_fixed_carryover_residual),
                    "max_scored_normalized_slack": max_scored_slack,
                    "max_normalized_slack": max_any_slack,
                    "residual_coordinate_system": ("scaled_reference_units"),
                    "horizon_start": data.periods[0],
                    "horizon_end": data.periods[-1],
                    "n_periods": data.n_periods,
                    "n_processes": layout.n_processes,
                    "reference_size": reference.size,
                    "boundary_policy": (data.dynamic_network_spec.boundary_policy),
                    "decomposition_policy": self.decomposition_policy,
                    "selection_status": _SELECTION_STATUS,
                }
            )

        metadata = self._metadata(
            data=data,
            reference=reference,
            period_weights=period_weights,
            division_weights=division_weights,
            weight_sources=weight_sources,
        )
        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
            slacks=pd.DataFrame(slack_rows),
            targets=pd.DataFrame(target_rows),
            intensities=pd.DataFrame(intensity_rows),
            duals=pd.DataFrame(dual_rows),
            components=pd.DataFrame(component_rows),
            links=pd.DataFrame(link_rows),
            diagnostics=pd.DataFrame(diagnostic_rows),
            metadata=metadata,
        )

    def _undefined_summary(
        self,
        *,
        dmu_id: object,
        data: DynamicNetworkData,
        reference: CompiledDynamicNetworkSBMReference,
        semantic_solver_status: str,
        backend_solver_status: SolverStatus,
        score_status: str,
    ) -> dict[str, Any]:
        mixed_rts = reference.has_mixed_returns_to_scale
        return {
            "dmu_id": dmu_id,
            "period": None,
            "score": np.nan,
            "efficiency": np.nan,
            "system_efficiency": np.nan,
            "score_valid": False,
            "score_status": score_status,
            "distance": np.nan,
            "is_efficient": pd.NA,
            "is_dynamic_network_sbm_efficient": pd.NA,
            "all_scored_slacks_zero": pd.NA,
            "all_slacks_zero": pd.NA,
            "solver_status": semantic_solver_status,
            "backend_solver_status": backend_solver_status.value,
            "raw_solver_status": backend_solver_status.value,
            "model_family": "dynamic_network_slacks_based",
            "orientation": self.orientation,
            "returns_to_scale": (
                "mixed" if mixed_rts else reference.returns_to_scale[0].value
            ),
            "overall_returns_to_scale_identified": not mixed_rts,
            "input_account": np.nan,
            "output_expansion_account": np.nan,
            "solver_objective": np.nan,
            "solver_efficiency": np.nan,
            "transform_scale": np.nan,
            "reconstruction_residual": np.nan,
            "max_balance_residual": np.nan,
            "max_link_continuity_residual": np.nan,
            "max_carryover_continuity_residual": np.nan,
            "max_fixed_link_residual": np.nan,
            "max_fixed_carryover_residual": np.nan,
            "max_scored_normalized_slack": np.nan,
            "max_normalized_slack": np.nan,
            "residual_coordinate_system": "scaled_reference_units",
            "horizon_start": data.periods[0],
            "horizon_end": data.periods[-1],
            "n_periods": data.n_periods,
            "n_processes": reference.layout.n_processes,
            "reference_size": reference.size,
            "boundary_policy": data.dynamic_network_spec.boundary_policy,
            "decomposition_policy": self.decomposition_policy,
            "selection_status": score_status,
        }

    def _extract_lambdas(
        self,
        *,
        primal: np.ndarray,
        reference: CompiledDynamicNetworkSBMReference,
        transform_scale: float,
    ) -> np.ndarray:
        result = np.empty(
            (
                reference.n_periods,
                reference.layout.n_processes,
                reference.size,
            ),
            dtype=np.float64,
        )
        for period in range(reference.n_periods):
            for process in reference.layout.processes:
                result[period, process.index] = _clean(
                    primal[reference.lambda_slices[period][process.index]]
                    / transform_scale,
                    self.tolerance,
                )
        return result

    def _extract_slacks(
        self,
        *,
        primal: np.ndarray,
        reference: CompiledDynamicNetworkSBMReference,
        transform_scale: float,
    ) -> dict[str, tuple[tuple[np.ndarray, ...], ...]]:
        result: dict[str, tuple[tuple[np.ndarray, ...], ...]] = {}
        for role in _SLACK_ROLES:
            slices = reference.slack_slices(role)
            result[role] = tuple(
                tuple(
                    _clean(
                        primal[slices[period][process.index]] / transform_scale,
                        self.tolerance,
                    )
                    for process in reference.layout.processes
                )
                for period in range(reference.n_periods)
            )
        return result

    def _accounts(
        self,
        *,
        observed: np.ndarray,
        slacks: dict[str, tuple[tuple[np.ndarray, ...], ...]],
        layout: CompiledDynamicNetworkSBMLayout,
    ) -> tuple[
        dict[str, tuple[tuple[np.ndarray, ...], ...]],
        np.ndarray,
        np.ndarray,
    ]:
        normalized: dict[str, tuple[tuple[np.ndarray, ...], ...]] = {}
        for role in _SLACK_ROLES:
            role_periods: list[tuple[np.ndarray, ...]] = []
            for period in range(observed.shape[0]):
                process_values: list[np.ndarray] = []
                for process in layout.processes:
                    columns = _role_columns(process, role)
                    values = slacks[role][period][process.index]
                    if not columns:
                        process_values.append(np.empty(0, dtype=np.float64))
                        continue
                    process_values.append(values / observed[period, list(columns)])
                role_periods.append(tuple(process_values))
            normalized[role] = tuple(role_periods)

        input_accounts = np.full(
            (observed.shape[0], layout.n_processes),
            np.nan,
            dtype=np.float64,
        )
        output_accounts = np.full_like(input_accounts, np.nan)
        for period in range(observed.shape[0]):
            for process in layout.processes:
                if process.input_account_dimension:
                    input_loss = sum(
                        float(np.sum(normalized[role][period][process.index]))
                        for role in _INPUT_ROLES
                    )
                    input_accounts[period, process.index] = (
                        1.0 - input_loss / process.input_account_dimension
                    )
                if process.output_account_dimension:
                    output_gain = sum(
                        float(np.sum(normalized[role][period][process.index]))
                        for role in _OUTPUT_ROLES
                    )
                    output_accounts[period, process.index] = (
                        1.0 + output_gain / process.output_account_dimension
                    )
        return normalized, input_accounts, output_accounts

    @staticmethod
    def _aggregate_accounts(
        *,
        input_accounts: np.ndarray,
        output_accounts: np.ndarray,
        period_weights: np.ndarray,
        division_weights: np.ndarray,
    ) -> dict[str, Any]:
        def aggregate(
            accounts: np.ndarray,
        ) -> tuple[np.ndarray, np.ndarray, float]:
            periods = np.asarray(
                [
                    (
                        float(accounts[period] @ division_weights)
                        if np.isfinite(accounts[period]).all()
                        else np.nan
                    )
                    for period in range(accounts.shape[0])
                ]
            )
            processes = np.asarray(
                [
                    (
                        float(period_weights @ accounts[:, process])
                        if np.isfinite(accounts[:, process]).all()
                        else np.nan
                    )
                    for process in range(accounts.shape[1])
                ]
            )
            system = (
                float(period_weights @ periods)
                if np.isfinite(periods).all()
                else np.nan
            )
            return periods, processes, system

        period_input, process_input, system_input = aggregate(input_accounts)
        period_output, process_output, system_output = aggregate(output_accounts)
        return {
            "period_input": period_input,
            "process_input": process_input,
            "system_input": system_input,
            "period_output": period_output,
            "process_output": process_output,
            "system_output": system_output,
        }

    @staticmethod
    def _benchmarks(
        *,
        lambdas: np.ndarray,
        reference: CompiledDynamicNetworkSBMReference,
    ) -> np.ndarray:
        result = np.empty(
            (
                reference.n_periods,
                reference.layout.n_processes,
                len(reference.layout.variable_names),
            ),
            dtype=np.float64,
        )
        for period in range(reference.n_periods):
            for process in reference.layout.processes:
                result[period, process.index] = (
                    lambdas[period, process.index] @ reference.scaled_values[period]
                )
        return result

    def _append_targets_and_slacks(
        self,
        *,
        target_rows: list[dict[str, Any]],
        slack_rows: list[dict[str, Any]],
        data: DynamicNetworkData,
        dmu_id: object,
        reference: CompiledDynamicNetworkSBMReference,
        observed: np.ndarray,
        benchmarks: np.ndarray,
        slacks: dict[str, tuple[tuple[np.ndarray, ...], ...]],
        normalized_slacks: dict[
            str,
            tuple[tuple[np.ndarray, ...], ...],
        ],
        period_weights: np.ndarray,
        division_weights: np.ndarray,
    ) -> float:
        layout = reference.layout
        variable_to_link = {
            variable: link.link_id
            for link in layout.links
            for variable in link.variables
        }
        max_residual = 0.0
        semantics = {
            "external_input": "external_resource_excess",
            "external_output": "external_desirable_output_shortfall",
            "as_input": "recipient_internal_resource_excess",
            "as_output": "supplier_internal_service_shortfall",
            "good_carryover": "valuable_state_shortfall",
            "bad_carryover": "harmful_state_excess",
            "free_carryover": "signed_unscored_state_deviation",
        }
        for period in range(reference.n_periods):
            for process in layout.processes:
                for role in _TARGET_ROLES:
                    columns = _role_columns(process, role)
                    variables = _role_variables(layout, process, role)
                    if not columns:
                        continue
                    column_array = np.asarray(columns, dtype=np.int64)
                    observed_values = observed[period, column_array]
                    benchmark_values = benchmarks[
                        period,
                        process.index,
                        column_array,
                    ]
                    if role == "fixed_carryover":
                        slack_values = np.zeros(
                            len(columns),
                            dtype=np.float64,
                        )
                    else:
                        slack_values = slacks[role][period][process.index]
                    if role in _INPUT_ROLES or role in {
                        "free_carryover",
                        "fixed_carryover",
                    }:
                        implied_targets = observed_values - slack_values
                    else:
                        implied_targets = observed_values + slack_values
                    if role == "fixed_carryover":
                        implied_targets = observed_values
                    residuals = benchmark_values - implied_targets
                    max_residual = max(
                        max_residual,
                        float(np.max(np.abs(residuals), initial=0.0)),
                    )
                    included = _included_in_objective(
                        self.orientation,
                        role,
                    ) and (
                        period_weights[period] > 0
                        and division_weights[process.index] > 0
                    )
                    dimension = (
                        process.input_account_dimension
                        if role in _INPUT_ROLES
                        else process.output_account_dimension
                        if role in _OUTPUT_ROLES
                        else 0
                    )
                    account_side = (
                        "input"
                        if role in _INPUT_ROLES
                        else "output"
                        if role in _OUTPUT_ROLES
                        else "feasibility_only"
                    )
                    for local, (column, variable) in enumerate(
                        zip(columns, variables, strict=True)
                    ):
                        scale = reference.scales[column]
                        observed_raw = float(observed_values[local] * scale)
                        benchmark_raw = float(benchmark_values[local] * scale)
                        target_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": data.periods[period],
                                "process_id": process.process_id,
                                "role": role,
                                "variable": variable,
                                "link_id": variable_to_link.get(variable),
                                "observed": observed_raw,
                                "target": benchmark_raw,
                                "adjustment": benchmark_raw - observed_raw,
                                "balance_residual": float(residuals[local] * scale),
                                "scaled_balance_residual": float(residuals[local]),
                                "account_side": account_side,
                                "included_in_objective": included,
                                "selection_status": _SELECTION_STATUS,
                            }
                        )
                        if role == "fixed_carryover":
                            continue
                        slack_raw = float(slack_values[local] * scale)
                        normalized = float(
                            normalized_slacks[role][period][process.index][local]
                        )
                        joint_weight = (
                            period_weights[period]
                            * division_weights[process.index]
                            / dimension
                            if included
                            else 0.0
                        )
                        slack_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": data.periods[period],
                                "process_id": process.process_id,
                                "role": role,
                                "variable": variable,
                                "link_id": variable_to_link.get(variable),
                                "slack": slack_raw,
                                "normalizer": observed_raw,
                                "normalized_slack": normalized,
                                "slack_semantics": semantics[role],
                                "account_side": account_side,
                                "included_in_objective": included,
                                "period_weight": period_weights[period],
                                "division_weight": division_weights[process.index],
                                "within_account_weight": (
                                    1.0 / dimension if dimension else 0.0
                                ),
                                "joint_objective_weight": joint_weight,
                                "account_contribution": (joint_weight * normalized),
                                "free_excess": (
                                    max(slack_raw, 0.0)
                                    if role == "free_carryover"
                                    else np.nan
                                ),
                                "free_shortage": (
                                    max(-slack_raw, 0.0)
                                    if role == "free_carryover"
                                    else np.nan
                                ),
                                "selection_status": _SELECTION_STATUS,
                            }
                        )
        return max_residual

    def _append_within_period_links(
        self,
        *,
        rows: list[dict[str, Any]],
        data: DynamicNetworkData,
        dmu_id: object,
        reference: CompiledDynamicNetworkSBMReference,
        observed: np.ndarray,
        benchmarks: np.ndarray,
        slacks: dict[str, tuple[tuple[np.ndarray, ...], ...]],
        period_weights: np.ndarray,
        division_weights: np.ndarray,
    ) -> tuple[float, float]:
        max_continuity_residual = 0.0
        max_fixed_residual = 0.0
        for period in range(reference.n_periods):
            as_input_slacks = {
                process.index: {
                    column: slacks["as_input"][period][process.index][local]
                    for local, column in enumerate(process.as_input_columns)
                }
                for process in reference.layout.processes
            }
            as_output_slacks = {
                process.index: {
                    column: slacks["as_output"][period][process.index][local]
                    for local, column in enumerate(process.as_output_columns)
                }
                for process in reference.layout.processes
            }
            for link in reference.layout.links:
                for variable, column in zip(
                    link.variables,
                    link.columns,
                    strict=True,
                ):
                    scale = reference.scales[column]
                    observed_scaled = float(observed[period, column])
                    source_projection = float(
                        benchmarks[period, link.source_index, column]
                    )
                    recipient_projection = float(
                        benchmarks[period, link.target_index, column]
                    )
                    source_scaled = source_projection
                    recipient_scaled = recipient_projection
                    continuity_scaled = source_projection - recipient_projection
                    max_continuity_residual = max(
                        max_continuity_residual,
                        abs(continuity_scaled),
                    )
                    if link.kind is NetworkSBMLinkKind.FREE:
                        target_scaled = 0.5 * (source_projection + recipient_projection)
                        endpoint_policy = "joint_source_recipient_continuity"
                        continuity_form = "explicit_endpoint_equality"
                    elif link.kind is NetworkSBMLinkKind.FIXED:
                        target_scaled = observed_scaled
                        endpoint_policy = "both_endpoints_reproduce_observed_link"
                        continuity_form = "implied_by_two_fixed_endpoint_balances"
                    elif link.kind is NetworkSBMLinkKind.AS_INPUT:
                        target_scaled = 0.5 * (source_projection + recipient_projection)
                        endpoint_policy = (
                            "recipient_input_balance_plus_endpoint_continuity"
                        )
                        continuity_form = "explicit_endpoint_equality"
                    else:
                        target_scaled = 0.5 * (source_projection + recipient_projection)
                        endpoint_policy = (
                            "supplier_output_balance_plus_endpoint_continuity"
                        )
                        continuity_form = "explicit_endpoint_equality"
                    if link.kind is NetworkSBMLinkKind.FIXED:
                        max_fixed_residual = max(
                            max_fixed_residual,
                            abs(source_projection - observed_scaled),
                            abs(recipient_projection - observed_scaled),
                        )
                    accountable_process: str | None = None
                    extracted_slack = np.nan
                    expected_slack = np.nan
                    slack_residual = np.nan
                    account_side = "feasibility_only"
                    included = False
                    if link.kind is NetworkSBMLinkKind.AS_INPUT:
                        accountable_process = link.target
                        extracted_slack = as_input_slacks[link.target_index][column]
                        expected_slack = observed_scaled - recipient_projection
                        slack_residual = extracted_slack - expected_slack
                        account_side = "input"
                        included = self.orientation in {
                            "input",
                            "non-oriented",
                        } and (
                            period_weights[period] > 0
                            and division_weights[link.target_index] > 0
                        )
                    elif link.kind is NetworkSBMLinkKind.AS_OUTPUT:
                        accountable_process = link.source
                        extracted_slack = as_output_slacks[link.source_index][column]
                        expected_slack = source_projection - observed_scaled
                        slack_residual = extracted_slack - expected_slack
                        account_side = "output"
                        included = self.orientation in {
                            "output",
                            "non-oriented",
                        } and (
                            period_weights[period] > 0
                            and division_weights[link.source_index] > 0
                        )
                    rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": data.periods[period],
                            "link_kind": "within_period",
                            "link_id": link.link_id,
                            "link_account_kind": link.kind.value,
                            "source_process_id": link.source,
                            "recipient_process_id": link.target,
                            "accountable_process_id": accountable_process,
                            "variable": variable,
                            "observed": observed_scaled * scale,
                            "source_target": (
                                source_scaled * scale
                                if math.isfinite(source_scaled)
                                else np.nan
                            ),
                            "recipient_target": (
                                recipient_scaled * scale
                                if math.isfinite(recipient_scaled)
                                else np.nan
                            ),
                            "target": target_scaled * scale,
                            "target_adjustment": (target_scaled - observed_scaled)
                            * scale,
                            "continuity_residual": (
                                continuity_scaled * scale
                                if math.isfinite(continuity_scaled)
                                else np.nan
                            ),
                            "scaled_continuity_residual": continuity_scaled,
                            "fixed_source_residual": (
                                (source_projection - observed_scaled) * scale
                                if link.kind is NetworkSBMLinkKind.FIXED
                                else np.nan
                            ),
                            "fixed_recipient_residual": (
                                (recipient_projection - observed_scaled) * scale
                                if link.kind is NetworkSBMLinkKind.FIXED
                                else np.nan
                            ),
                            "account_slack": (
                                extracted_slack * scale
                                if math.isfinite(extracted_slack)
                                else np.nan
                            ),
                            "slack_reconstruction_residual": (
                                slack_residual * scale
                                if math.isfinite(slack_residual)
                                else np.nan
                            ),
                            "account_side": account_side,
                            "included_in_objective": included,
                            "continuity_enforced": True,
                            "continuity_constraint_form": continuity_form,
                            "endpoint_balance_policy": endpoint_policy,
                            "free_signed_deviation": (
                                (target_scaled - observed_scaled) * scale
                                if link.kind is NetworkSBMLinkKind.FREE
                                else np.nan
                            ),
                            "boundary_status": "within_period",
                            "selection_status": _SELECTION_STATUS,
                        }
                    )
        return max_continuity_residual, max_fixed_residual

    def _append_carryovers(
        self,
        *,
        rows: list[dict[str, Any]],
        data: DynamicNetworkData,
        dmu_id: object,
        reference: CompiledDynamicNetworkSBMReference,
        observed: np.ndarray,
        benchmarks: np.ndarray,
        lambdas: np.ndarray,
        slacks: dict[str, tuple[tuple[np.ndarray, ...], ...]],
        period_weights: np.ndarray,
        division_weights: np.ndarray,
    ) -> tuple[float, float]:
        max_continuity_residual = 0.0
        max_fixed_residual = 0.0
        role_to_kind = {
            "good_carryover": "good",
            "bad_carryover": "bad",
            "free_carryover": "free",
            "fixed_carryover": "fixed",
        }
        for process in reference.layout.processes:
            for role, carryover_kind in role_to_kind.items():
                columns = _role_columns(process, role)
                variables = _role_variables(
                    reference.layout,
                    process,
                    role,
                )
                for local, (variable, column) in enumerate(
                    zip(variables, columns, strict=True)
                ):
                    scale = reference.scales[column]
                    for period in range(reference.n_periods):
                        observed_scaled = float(observed[period, column])
                        source_target_scaled = float(
                            benchmarks[period, process.index, column]
                        )
                        if period < reference.n_periods - 1:
                            next_target_scaled = float(
                                lambdas[period + 1, process.index]
                                @ reference.scaled_values[
                                    period,
                                    :,
                                    column,
                                ]
                            )
                            continuity_scaled = (
                                source_target_scaled - next_target_scaled
                            )
                            max_continuity_residual = max(
                                max_continuity_residual,
                                abs(continuity_scaled),
                            )
                            target_period: object | None = data.periods[period + 1]
                            boundary_status = "adjacent_period_continuity"
                        else:
                            next_target_scaled = np.nan
                            continuity_scaled = np.nan
                            target_period = None
                            boundary_status = "observed_terminal_no_outgoing_continuity"
                        if role == "fixed_carryover":
                            extracted_slack = np.nan
                            expected_slack = np.nan
                            slack_residual = np.nan
                            fixed_residual = source_target_scaled - observed_scaled
                            max_fixed_residual = max(
                                max_fixed_residual,
                                abs(fixed_residual),
                            )
                        else:
                            extracted_slack = float(
                                slacks[role][period][process.index][local]
                            )
                            if role in {
                                "bad_carryover",
                                "free_carryover",
                            }:
                                expected_slack = observed_scaled - source_target_scaled
                            else:
                                expected_slack = source_target_scaled - observed_scaled
                            slack_residual = extracted_slack - expected_slack
                            fixed_residual = np.nan
                        account_side = (
                            "input"
                            if role == "bad_carryover"
                            else "output"
                            if role == "good_carryover"
                            else "feasibility_only"
                        )
                        rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": data.periods[period],
                                "link_kind": "carryover",
                                "link_id": (
                                    f"carryover:{process.process_id}:{variable}"
                                ),
                                "link_account_kind": carryover_kind,
                                "source_process_id": process.process_id,
                                "recipient_process_id": process.process_id,
                                "accountable_process_id": (process.process_id),
                                "variable": variable,
                                "source_period": data.periods[period],
                                "target_period": target_period,
                                "observed": observed_scaled * scale,
                                "source_target": (source_target_scaled * scale),
                                "recipient_target": (
                                    next_target_scaled * scale
                                    if math.isfinite(next_target_scaled)
                                    else np.nan
                                ),
                                "target": source_target_scaled * scale,
                                "target_adjustment": (
                                    source_target_scaled - observed_scaled
                                )
                                * scale,
                                "continuity_residual": (
                                    continuity_scaled * scale
                                    if math.isfinite(continuity_scaled)
                                    else np.nan
                                ),
                                "scaled_continuity_residual": (continuity_scaled),
                                "fixed_source_residual": (
                                    fixed_residual * scale
                                    if math.isfinite(fixed_residual)
                                    else np.nan
                                ),
                                "fixed_recipient_residual": np.nan,
                                "account_slack": (
                                    extracted_slack * scale
                                    if math.isfinite(extracted_slack)
                                    else np.nan
                                ),
                                "slack_reconstruction_residual": (
                                    slack_residual * scale
                                    if math.isfinite(slack_residual)
                                    else np.nan
                                ),
                                "account_side": account_side,
                                "included_in_objective": (
                                    _included_in_objective(
                                        self.orientation,
                                        role,
                                    )
                                    and period_weights[period] > 0
                                    and division_weights[process.index] > 0
                                ),
                                "boundary_status": boundary_status,
                                "selection_status": _SELECTION_STATUS,
                            }
                        )
        return max_continuity_residual, max_fixed_residual

    def _append_intensities(
        self,
        *,
        rows: list[dict[str, Any]],
        data: DynamicNetworkData,
        dmu_id: object,
        reference: CompiledDynamicNetworkSBMReference,
        lambdas: np.ndarray,
    ) -> None:
        for period in range(reference.n_periods):
            for process in reference.layout.processes:
                for local, intensity in enumerate(lambdas[period, process.index]):
                    if intensity <= self.peer_tolerance:
                        continue
                    reference_row = int(reference.rows[local])
                    rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": data.periods[period],
                            "process_id": process.process_id,
                            "reference_dmu_id": data.dmu_ids[reference_row],
                            "reference_period": data.periods[period],
                            "intensity": float(intensity),
                            "lambda": float(intensity),
                            "returns_to_scale": reference.returns_to_scale[
                                process.index
                            ].value,
                            "selection_status": _SELECTION_STATUS,
                        }
                    )

    def _append_components(
        self,
        *,
        rows: list[dict[str, Any]],
        data: DynamicNetworkData,
        dmu_id: object,
        reference: CompiledDynamicNetworkSBMReference,
        input_accounts: np.ndarray,
        output_accounts: np.ndarray,
        account_summary: dict[str, Any],
        period_weights: np.ndarray,
        division_weights: np.ndarray,
        system_efficiency: float,
    ) -> float:
        system_output = float(account_summary["system_output"])
        first_row = len(rows)

        def append(
            *,
            component_kind: str,
            component_id: str,
            period_index: int | None,
            process_index: int | None,
            input_account: float,
            output_account: float,
            exogenous_weight: float,
        ) -> None:
            efficiency = _efficiency(
                self.orientation,
                input_account,
                output_account,
            )
            if component_kind == "system":
                effective_weight = 1.0
            elif self.orientation == "input":
                effective_weight = exogenous_weight
            else:
                effective_weight = exogenous_weight * output_account / system_output
            component_rts = (
                reference.returns_to_scale[process_index].value
                if process_index is not None
                else "mixed"
                if reference.has_mixed_returns_to_scale
                else reference.returns_to_scale[0].value
            )
            rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": (
                        None if period_index is None else data.periods[period_index]
                    ),
                    "component_kind": component_kind,
                    "component_type": component_kind,
                    "component_id": component_id,
                    "process_id": (
                        None
                        if process_index is None
                        else reference.layout.process_ids[process_index]
                    ),
                    "efficiency": efficiency,
                    "distance": 1.0 - efficiency,
                    "input_account": input_account,
                    "output_expansion_account": output_account,
                    "input_inefficiency": (
                        1.0 - input_account if math.isfinite(input_account) else np.nan
                    ),
                    "output_inefficiency": (
                        output_account - 1.0
                        if math.isfinite(output_account)
                        else np.nan
                    ),
                    "period_weight": (
                        period_weights[period_index]
                        if period_index is not None
                        else np.nan
                    ),
                    "division_weight": (
                        division_weights[process_index]
                        if process_index is not None
                        else np.nan
                    ),
                    "exogenous_reconstruction_weight": exogenous_weight,
                    "effective_reconstruction_weight": effective_weight,
                    "efficiency_contribution": (effective_weight * efficiency),
                    "returns_to_scale": component_rts,
                    "included_in_system_score": (
                        component_kind == "system" or exogenous_weight > 0
                    ),
                    "selection_status": (
                        "primary_system_optimal_value"
                        if component_kind == "system"
                        else _SELECTION_STATUS
                    ),
                    "uniqueness_status": (
                        "system_objective_value"
                        if component_kind == "system"
                        else "not_certified"
                    ),
                    "managerial_interpretation": (
                        "conditional_account_within_joint_system_plan"
                        if component_kind != "system"
                        else "complete_horizon_system_performance"
                    ),
                }
            )

        append(
            component_kind="system",
            component_id="system_horizon",
            period_index=None,
            process_index=None,
            input_account=float(account_summary["system_input"]),
            output_account=system_output,
            exogenous_weight=1.0,
        )
        for period in range(reference.n_periods):
            append(
                component_kind="period",
                component_id=f"period_{period + 1}",
                period_index=period,
                process_index=None,
                input_account=float(account_summary["period_input"][period]),
                output_account=float(account_summary["period_output"][period]),
                exogenous_weight=float(period_weights[period]),
            )
        for process in reference.layout.processes:
            append(
                component_kind="process",
                component_id=process.process_id,
                period_index=None,
                process_index=process.index,
                input_account=float(account_summary["process_input"][process.index]),
                output_account=float(account_summary["process_output"][process.index]),
                exogenous_weight=float(division_weights[process.index]),
            )
        for period in range(reference.n_periods):
            for process in reference.layout.processes:
                append(
                    component_kind="period_process",
                    component_id=(f"period_{period + 1}:{process.process_id}"),
                    period_index=period,
                    process_index=process.index,
                    input_account=float(input_accounts[period, process.index]),
                    output_account=float(output_accounts[period, process.index]),
                    exogenous_weight=float(
                        period_weights[period] * division_weights[process.index]
                    ),
                )
        reconstructed = sum(
            float(row["efficiency_contribution"])
            for row in rows[first_row:]
            if row["component_kind"] == "period_process"
        )
        return reconstructed - system_efficiency

    def _append_duals(
        self,
        *,
        rows: list[dict[str, Any]],
        data: DynamicNetworkData,
        dmu_id: object,
        reference: CompiledDynamicNetworkSBMReference,
        solution: LPSolution,
    ) -> None:
        if solution.equality_marginals is None:
            return
        coordinate_system = (
            "charnes_cooper_transformed"
            if self.orientation == "non-oriented"
            else "direct_tau_fixed_to_one"
        )
        for descriptor, marginal in zip(
            reference.row_descriptors,
            solution.equality_marginals,
            strict=True,
        ):
            (
                role,
                source_period,
                target_period,
                process_id,
                link_id,
                variable,
            ) = descriptor
            rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": (
                        None if source_period is None else data.periods[source_period]
                    ),
                    "phase": "primary",
                    "constraint_role": role,
                    "process_id": process_id,
                    "link_id": link_id,
                    "variable": variable,
                    "source_period": (
                        None if source_period is None else data.periods[source_period]
                    ),
                    "target_period": (
                        None if target_period is None else data.periods[target_period]
                    ),
                    "marginal": float(marginal),
                    "coordinate_system": coordinate_system,
                }
            )

    def _metadata(
        self,
        *,
        data: DynamicNetworkData,
        reference: CompiledDynamicNetworkSBMReference,
        period_weights: np.ndarray,
        division_weights: np.ndarray,
        weight_sources: dict[str, str],
    ) -> dict[str, Any]:
        layout = reference.layout
        mixed_rts = reference.has_mixed_returns_to_scale
        process_rts = {
            process.process_id: reference.returns_to_scale[process.index].value
            for process in layout.processes
        }
        rts_label = "mixed" if mixed_rts else reference.returns_to_scale[0].value
        carryovers = [
            {
                "process_id": item.process_id,
                "variable": item.variable,
                "kind": item.kind.value,
            }
            for item in data.dynamic_network_spec.carryovers
        ]
        links = [
            {
                "link_id": link.link_id,
                "source": link.source,
                "target": link.target,
                "kind": link.kind.value,
                "variables": list(link.variables),
            }
            for link in layout.links
        ]
        expanded_spec = {
            "context": {
                "purpose": ("joint_intertemporal_multi_process_performance"),
                "managerial_unit": "complete_dmu_trajectory",
            },
            "graph": {
                "kind": "time_expanded_dynamic_network",
                "periods": data.n_periods,
                "processes": list(layout.process_ids),
                "links": links,
                "carryovers": carryovers,
            },
            "data_roles": {
                "strictly_positive": True,
                "balanced_panel": True,
                "external_inputs": {
                    process.process_id: list(process.external_inputs)
                    for process in layout.processes
                },
                "external_outputs": {
                    process.process_id: list(process.external_outputs)
                    for process in layout.processes
                },
                "link_account_ownership": {
                    "as_input": "recipient_process",
                    "as_output": "supplier_process",
                },
            },
            "technology": {
                "family": "dynamic_carryover_portfolio_network_envelopment",
                "returns_to_scale": rts_label,
                "process_returns_to_scale": process_rts,
                "overall_returns_to_scale_identified": not mixed_rts,
                "within_period_link_rules": {
                    "free": "joint_source_recipient_continuity",
                    "fixed": "both_endpoints_reproduce_observed_link",
                    "as_input": ("recipient_input_balance_plus_endpoint_continuity"),
                    "as_output": ("supplier_output_balance_plus_endpoint_continuity"),
                },
                "all_link_endpoint_continuity": True,
                "adjacent_period_carryover_continuity": True,
                "boundary_policy": (data.dynamic_network_spec.boundary_policy),
                "equation_source_scope": (
                    "published_article_with_named_terminal_resolution"
                ),
                "published_equations_audited": True,
                "published_terminal_indexing_consistent": False,
                "terminal_resolution": ("T_observed_accounts_T_minus_1_continuity"),
                "terminal_observed_account": True,
                "continuity_periods": "T_minus_1",
                "boundary_contract": {
                    "implemented": (
                        "T_observed_accounts_with_T_minus_1_adjacent_period_"
                        "continuity_and_no_unobserved_T_plus_1_account"
                    ),
                    "published_version_terminal_index_status": (
                        "internal_indexing_conflict_confirmed"
                    ),
                },
            },
            "estimator": {
                "kind": "full_frontier",
                "family": "dynamic_network_dea_envelopment",
            },
            "reference": {
                "kind": "global_complete_trajectory_cohort",
                "cohort_size": data.n_dmus,
                "same_membership_every_period_and_process": True,
                "self_membership": "allowed",
            },
            "performance": {
                "family": "dynamic_network_slacks_based_measure",
                "orientation": self.orientation,
                "input_accounts": [
                    "external_input",
                    "recipient_as_input_link",
                    "bad_carryover",
                ],
                "output_accounts": [
                    "external_output",
                    "supplier_as_output_link",
                    "good_carryover",
                ],
                "unscored_feasibility_accounts": [
                    "free_link",
                    "fixed_link",
                    "free_carryover",
                    "fixed_carryover",
                ],
            },
            "valuation": {
                "kind": "exogenous_relative_importance_weights",
                "period_weights": [float(value) for value in period_weights],
                "division_weights": [float(value) for value in division_weights],
                "weight_domain": ("nonnegative_each_group_with_at_least_one_positive"),
                "zero_weight_accounts_enter_score": False,
                "within_account_item_weights": "source_equal",
            },
            "evaluation_protocol": {
                "kind": "joint_horizon_self_appraisal",
                "decomposition_policy": self.decomposition_policy,
                "alternate_optimum_policy": "solver_selected",
            },
            "analysis": {
                "kind": ("joint_system_period_process_and_period_process_accounts"),
            },
            "uncertainty": {
                "sampling": {"kind": "none"},
                "data": {"kind": "none"},
            },
        }
        metadata = registry_metadata(
            self._registry_method_id,
            expanded_spec,
        )
        metadata.update(
            {
                "model": type(self).__name__,
                "model_family": "dynamic_network_slacks_based",
                "source": {
                    "authors": ["Kaoru Tone", "Miki Tsutsui"],
                    "year": 2014,
                    "doi": "10.1016/j.omega.2013.04.002",
                    "equation_source_scope": (
                        "published_article_with_named_terminal_resolution"
                    ),
                    "implemented_equation_scope": (
                        "audited_published_equations_with_named_terminal_resolution"
                    ),
                    "published_equations_audited": True,
                    "published_terminal_indexing_consistent": False,
                    "terminal_resolution": ("T_observed_accounts_T_minus_1_continuity"),
                    "terminal_observed_account": True,
                    "continuity_periods": "T_minus_1",
                    "published_version_terminal_index_status": (
                        "internal_indexing_conflict_confirmed"
                    ),
                },
                "orientation": self.orientation,
                "returns_to_scale": rts_label,
                "process_returns_to_scale": process_rts,
                "overall_returns_to_scale_identified": not mixed_rts,
                "returns_to_scale_scope": (
                    "process_specific_mixed" if mixed_rts else "common_all_processes"
                ),
                "boundary_policy": (data.dynamic_network_spec.boundary_policy),
                "equation_source_scope": (
                    "published_article_with_named_terminal_resolution"
                ),
                "published_equations_audited": True,
                "published_terminal_indexing_consistent": False,
                "terminal_resolution": ("T_observed_accounts_T_minus_1_continuity"),
                "terminal_observed_account": True,
                "continuity_periods": "T_minus_1",
                "spec_fingerprint": data.spec_fingerprint,
                "period_order": tuple(data.periods.tolist()),
                "process_ids": layout.process_ids,
                "link_ids": layout.link_ids,
                "effective_weights": {
                    "period": {
                        str(label): float(value)
                        for label, value in zip(
                            data.periods,
                            period_weights,
                            strict=True,
                        )
                    },
                    "division": {
                        process_id: float(value)
                        for process_id, value in zip(
                            layout.process_ids,
                            division_weights,
                            strict=True,
                        )
                    },
                    "sources": weight_sources,
                    "zero_weight_periods": tuple(
                        str(data.periods[index])
                        for index, value in enumerate(period_weights)
                        if value == 0
                    ),
                    "zero_weight_processes": tuple(
                        layout.process_ids[index]
                        for index, value in enumerate(division_weights)
                        if value == 0
                    ),
                },
                "all_account_weights_positive": bool(
                    np.all(period_weights > 0.0) and np.all(division_weights > 0.0)
                ),
                "all_account_efficiency_identified_by_system_one": bool(
                    np.all(period_weights > 0.0) and np.all(division_weights > 0.0)
                ),
                "reference_policy": ("global_complete_trajectory_cohort"),
                "compiled_reference_sets": 1,
                "primary_solves": data.n_dmus,
                "secondary_solves": 0,
                "solver_calls": data.n_dmus,
                "additional_solver_calls": 0,
                "certificate_extra_solver_calls": 0,
                "matrix_shape": (
                    reference.n_equalities,
                    reference.n_variables,
                ),
                "matrix_nnz": reference.n_nonzero,
                "selection_status": _SELECTION_STATUS,
                "component_interpretation": (
                    "conditional_accounts_of_one_joint_system_optimum"
                ),
                "system_optimal_value_well_defined": True,
                "subsystem_component_uniqueness_certified": False,
                "base_objective_includes_free_or_fixed_accounts": False,
                "source_reverse_chronological_period_selection": ("not_implemented"),
                "source_fidelity_claim": (
                    "published_equations_audited_and_property_validated_"
                    "without_published_numerical_oracle_with_named_terminal_"
                    "resolution"
                ),
                "unsupported_source_extensions": (
                    "initial_boundary_condition",
                    "terminal_boundary_condition",
                    ("published_terminal_indexing_conflict_requires_named_policy"),
                    "free_link_and_free_carryover_objective_extension",
                    "source_reverse_chronological_period_priority",
                    "dynamic_malmquist_productivity_operator",
                ),
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "score_direction": "higher_is_better",
                "native_score": "system_efficiency",
                "distance_transform": "one_minus_efficiency",
                "data_requirement": "strictly_positive_balanced_panel",
                "postsolve_certificate": {
                    "lp": "solver_neutral_primal_dual_kkt_and_strong_duality",
                    "economic": (
                        "transform_scale_accounts_score_links_and_trajectory_"
                        "reconstruction"
                    ),
                    "failure_policy": (
                        "fail_closed_without_score_or_semantic_result_tables"
                    ),
                    "additional_solver_calls": 0,
                },
            }
        )
        return metadata


DynamicNetworkSBM = ToneTsutsuiDynamicNetworkSBM
"""Exact short alias for :class:`ToneTsutsuiDynamicNetworkSBM`."""


__all__ = [
    "DynamicNetworkSBM",
    "ToneTsutsuiDynamicNetworkSBM",
]
