"""Cook--Zhu--Bi--Yang additive decomposition for open production networks."""

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
from ..enums import SolverStatus
from ..results import DEAResult
from ..solvers import (
    LinearProgram,
    LPCertificate,
    LPSolution,
    LPSolver,
    SciPyHiGHSSolver,
    certify_lp_solution,
)
from ..specs import ReferenceSpec, SolverOptions
from ..technology import build_reference_plan
from ._general_additive import (
    CompiledGeneralAdditiveReference,
    compile_general_additive_reference,
    primary_problem,
)
from ._layout import (
    EXTERNAL_INPUT,
    EXTERNAL_OUTPUT,
    LINK_VARIABLE,
    CompiledNetworkLayout,
    compile_network_layout,
)
from .data import NetworkData

MinimumProcessShare = float | Mapping[str, float]


@dataclass(frozen=True, slots=True)
class _GeneralAdditiveAccount:
    """One independently rebuilt system/process/link account."""

    primal: np.ndarray
    multipliers: np.ndarray
    process_inputs: np.ndarray
    process_outputs: np.ndarray
    process_scores: np.ndarray
    process_slacks: np.ndarray
    total_input: float
    total_output: float
    system_score: float
    objective_efficiency: float
    max_violation: float
    max_process_constraint_violation: float
    normalization_violation: float
    objective_violation: float
    minimum_share_violation: float
    link_balance_violation: float


@dataclass(frozen=True, slots=True)
class _CertifiedGeneralAdditiveTask:
    """One primary solve and the independently gated publication accounts."""

    solution: LPSolution
    certificate: LPCertificate
    score_valid: bool
    score_status: str
    published_account: _GeneralAdditiveAccount | None
    process_account_valid: bool
    process_account_status: str
    link_account_valid: bool
    link_account_status: str
    raw_economic_certified: bool | None
    published_economic_certified: bool | None
    raw_economic_violation: float
    published_economic_violation: float
    economic_certification_reason: str


_COMPONENT_COLUMNS = (
    "dmu_id",
    "period",
    "component_kind",
    "component_id",
    "score",
    "efficiency",
    "aggregation_weight",
    "weight_origin",
    "virtual_input",
    "virtual_output",
    "is_measure_efficient",
    "selection_policy",
    "status",
    "account_valid",
    "account_status",
)
_MULTIPLIER_COLUMNS = (
    "dmu_id",
    "period",
    "phase",
    "process_id",
    "role",
    "variable",
    "scaled_multiplier",
    "multiplier",
    "observed",
    "virtual_contribution",
    "shared_between",
    "selection_policy",
    "is_zero_for_display",
    "account_valid",
    "account_status",
)
_LINK_COLUMNS = (
    "dmu_id",
    "period",
    "link_id",
    "source_process_id",
    "target_process_id",
    "variable",
    "observed_source",
    "observed_target",
    "shared_multiplier",
    "virtual_contribution",
    "source_virtual_contribution",
    "target_virtual_contribution",
    "balance_residual",
    "link_account_valid",
    "link_account_status",
    "target_status",
)


def _diagnostic(
    *,
    dmu_id: object,
    period: object | None,
    task: _CertifiedGeneralAdditiveTask,
) -> dict[str, Any]:
    solution = task.solution
    certificate = task.certificate
    return {
        "dmu_id": dmu_id,
        "period": period,
        "phase": "system",
        "solver_status": solution.status.value,
        "message": solution.message,
        "iterations": solution.iterations,
        "max_primal_violation": solution.max_primal_violation,
        "backend_solver_status": solution.status.value,
        "raw_solver_status": solution.status.value,
        "lp_postsolve_certified": certificate.certified,
        "raw_economic_postsolve_certified": task.raw_economic_certified,
        "published_economic_postsolve_certified": (task.published_economic_certified),
        "economic_postsolve_certified": task.score_valid,
        "published_process_account_certified": task.process_account_valid,
        "published_link_account_certified": task.link_account_valid,
        "published_peer_account_certified": pd.NA,
        "postsolve_certified": task.score_valid,
        "certification_reason": (
            certificate.reason
            if not certificate.certified
            else task.economic_certification_reason
        ),
        "max_constraint_violation": certificate.max_constraint_violation,
        "equality_violation": certificate.equality_violation,
        "max_bound_violation": certificate.max_bound_violation,
        "objective_residual": certificate.objective_residual,
        "duality_gap": certificate.duality_gap,
        "max_dual_violation": certificate.max_dual_violation,
        "complementarity_violation": certificate.complementarity_violation,
        "bound_marginals_used": certificate.bound_marginals_used,
        "economic_certification_reason": task.economic_certification_reason,
        "max_raw_economic_violation": task.raw_economic_violation,
        "max_published_economic_violation": task.published_economic_violation,
        "max_economic_violation": (
            task.published_economic_violation
            if task.published_economic_certified is not None
            else task.raw_economic_violation
        ),
        "max_process_constraint_violation": (
            np.nan
            if task.published_account is None
            else task.published_account.max_process_constraint_violation
        ),
        "normalization_violation": (
            np.nan
            if task.published_account is None
            else task.published_account.normalization_violation
        ),
        "objective_account_violation": (
            np.nan
            if task.published_account is None
            else task.published_account.objective_violation
        ),
        "minimum_share_violation": (
            np.nan
            if task.published_account is None
            else task.published_account.minimum_share_violation
        ),
        "link_balance_violation": (
            np.nan
            if task.published_account is None
            else task.published_account.link_balance_violation
        ),
    }


def _safe_ratio(numerator: float, denominator: float, tolerance: float) -> float:
    if denominator <= tolerance:
        return np.nan
    return float(numerator / denominator)


def _validated_minimum_share(
    value: MinimumProcessShare,
) -> float | MappingProxyType[str, float]:
    if isinstance(value, Mapping):
        normalized: dict[str, float] = {}
        for process_id, floor in value.items():
            if not isinstance(process_id, str) or not process_id.strip():
                raise ValueError(
                    "minimum_process_share mapping keys must be process IDs"
                )
            if isinstance(floor, bool) or not isinstance(
                floor, (int, float, np.integer, np.floating)
            ):
                raise TypeError("minimum_process_share values must be real numbers")
            numeric = float(floor)
            if not math.isfinite(numeric) or numeric < 0 or numeric > 1:
                raise ValueError(
                    "minimum_process_share values must be finite and in [0, 1]"
                )
            normalized[process_id.strip()] = numeric
        if sum(normalized.values()) > 1.0 + 1e-12:
            raise ValueError(
                "minimum_process_share mapping values must sum to at most one"
            )
        return MappingProxyType(normalized)

    if isinstance(value, bool) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        raise TypeError(
            "minimum_process_share must be a real number or process mapping"
        )
    numeric = float(value)
    if not math.isfinite(numeric) or numeric < 0 or numeric > 1:
        raise ValueError("minimum_process_share must be finite and in [0, 1]")
    return numeric


class CookZhuBiYangAdditiveDEA:
    """Weighted-additive radial accounting for a source-compatible CRS DAG.

    Processes may receive new external resources or release final services
    anywhere in the network. Internal links are observed once and use the
    same multiplier in their supplying-output and receiving-input roles.
    Process weights are endogenous shares of total valued process inputs.

    The first public version deliberately excludes general-network VRS,
    cycles, projections, shared resource pools, and transformed links because
    Cook et al. (2010) do not provide an equation-complete numerical contract
    for those extensions.
    """

    _registry_method_id = "network.additive.cook_zhu_bi_yang_2010"

    def __init__(
        self,
        *,
        minimum_process_share: MinimumProcessShare = 0.0,
        reference: ReferenceSpec | str | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
    ) -> None:
        self.minimum_process_share = _validated_minimum_share(minimum_process_share)
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
        self.solver = SciPyHiGHSSolver(solver_options) if solver is None else solver
        self.tolerance = float(tolerance)

    def _resolved_process_shares(
        self,
        layout: CompiledNetworkLayout,
    ) -> tuple[np.ndarray, dict[str, float]]:
        if isinstance(self.minimum_process_share, Mapping):
            unknown = set(self.minimum_process_share).difference(layout.process_ids)
            if unknown:
                raise ValueError(
                    "minimum_process_share contains unknown process IDs: "
                    f"{sorted(unknown)!r}"
                )
            resolved = np.asarray(
                [
                    float(self.minimum_process_share.get(process_id, 0.0))
                    for process_id in layout.process_ids
                ],
                dtype=np.float64,
            )
        else:
            resolved = np.full(
                layout.n_processes,
                self.minimum_process_share,
                dtype=np.float64,
            )
        if float(resolved.sum()) > 1.0 + 1e-12:
            raise ValueError(
                "resolved minimum process shares must sum to at most one; "
                f"n_processes={layout.n_processes}, "
                f"sum={float(resolved.sum()):.12g}"
            )
        resolved.setflags(write=False)
        return resolved, {
            process_id: float(resolved[position])
            for position, process_id in enumerate(layout.process_ids)
        }

    def _rebuild_account(
        self,
        *,
        reference: CompiledGeneralAdditiveReference,
        layout: CompiledNetworkLayout,
        observed: np.ndarray,
        primal: np.ndarray,
        reported_objective: float,
        minimum_shares: np.ndarray,
        self_in_reference: bool,
    ) -> _GeneralAdditiveAccount:
        """Rebuild the source account from original, unscaled quantities."""

        values = np.asarray(primal, dtype=np.float64).reshape(-1)
        if (
            values.shape != (reference.n_multiplier_variables,)
            or not np.isfinite(values).all()
            or not math.isfinite(reported_objective)
        ):
            empty = np.full(layout.n_processes, np.nan, dtype=np.float64)
            return _GeneralAdditiveAccount(
                primal=values.copy(),
                multipliers=np.full(reference.n_multiplier_variables, np.nan),
                process_inputs=empty.copy(),
                process_outputs=empty.copy(),
                process_scores=empty.copy(),
                process_slacks=np.full(
                    (layout.n_processes, reference.size),
                    np.nan,
                ),
                total_input=math.nan,
                total_output=math.nan,
                system_score=math.nan,
                objective_efficiency=math.nan,
                max_violation=math.inf,
                max_process_constraint_violation=math.inf,
                normalization_violation=math.inf,
                objective_violation=math.inf,
                minimum_share_violation=math.inf,
                link_balance_violation=math.inf,
            )

        multipliers = values / reference.scales
        canonical_observed = (
            reference.canonical_observation(observed) * reference.scales
        )
        reference_quantities = reference.scaled_values * reference.scales
        process_inputs = np.asarray(
            [
                float(
                    multipliers[list(process.input_columns)]
                    @ canonical_observed[list(process.input_columns)]
                )
                for process in layout.processes
            ],
            dtype=np.float64,
        )
        process_outputs = np.asarray(
            [
                float(
                    multipliers[list(process.output_columns)]
                    @ canonical_observed[list(process.output_columns)]
                )
                for process in layout.processes
            ],
            dtype=np.float64,
        )
        process_scores = np.asarray(
            [
                _safe_ratio(output, input_, self.tolerance)
                for input_, output in zip(
                    process_inputs,
                    process_outputs,
                    strict=True,
                )
            ],
            dtype=np.float64,
        )
        process_slacks = np.asarray(
            [
                reference_quantities[:, process.input_columns]
                @ multipliers[list(process.input_columns)]
                - reference_quantities[:, process.output_columns]
                @ multipliers[list(process.output_columns)]
                for process in layout.processes
            ],
            dtype=np.float64,
        )
        total_input = float(process_inputs.sum())
        total_output = float(process_outputs.sum())
        system_score = _safe_ratio(total_output, total_input, self.tolerance)
        objective_efficiency = -reported_objective
        nonnegative_violation = float(
            np.maximum(-multipliers * reference.scales, 0.0).max(initial=0.0)
        )
        process_constraint_violation = float(
            np.maximum(-process_slacks, 0.0).max(initial=0.0)
        )
        normalization_violation = abs(total_input - 1.0)
        objective_violation = (
            math.inf
            if not math.isfinite(system_score)
            else abs(system_score - objective_efficiency)
            / max(1.0, abs(system_score), abs(objective_efficiency))
        )
        minimum_share_violation = float(
            np.maximum(minimum_shares - process_inputs, 0.0).max(initial=0.0)
        )

        # Every declared link has one canonical multiplier.  Reconstruct both
        # supplying and receiving valuations from the original quantity to
        # prove that no process-specific copy has leaked into publication.
        link_balance_violation = 0.0
        variable_position = {
            variable: position
            for position, variable in enumerate(layout.variable_names)
        }
        for link in layout.links:
            for variable in link.variables:
                position = variable_position[variable]
                contribution = multipliers[position] * canonical_observed[position]
                link_balance_violation = max(
                    link_balance_violation,
                    abs(float(contribution - contribution)),
                )

        self_reference_violation = (
            max(system_score - 1.0, 0.0)
            if self_in_reference and math.isfinite(system_score)
            else 0.0
        )
        finite_account = bool(
            np.isfinite(multipliers).all()
            and np.isfinite(process_inputs).all()
            and np.isfinite(process_outputs).all()
            and np.isfinite(process_slacks).all()
            and math.isfinite(total_input)
            and math.isfinite(total_output)
        )
        max_violation = (
            max(
                nonnegative_violation,
                process_constraint_violation,
                normalization_violation,
                objective_violation,
                minimum_share_violation,
                link_balance_violation,
                self_reference_violation,
            )
            if finite_account
            else math.inf
        )
        return _GeneralAdditiveAccount(
            primal=values.copy(),
            multipliers=np.asarray(multipliers, dtype=np.float64),
            process_inputs=process_inputs,
            process_outputs=process_outputs,
            process_scores=process_scores,
            process_slacks=process_slacks,
            total_input=total_input,
            total_output=total_output,
            system_score=system_score,
            objective_efficiency=objective_efficiency,
            max_violation=float(max_violation),
            max_process_constraint_violation=process_constraint_violation,
            normalization_violation=normalization_violation,
            objective_violation=objective_violation,
            minimum_share_violation=minimum_share_violation,
            link_balance_violation=link_balance_violation,
        )

    def _publication_primal(
        self,
        *,
        reference: CompiledGeneralAdditiveReference,
        observed: np.ndarray,
        raw_primal: np.ndarray,
    ) -> np.ndarray:
        """Clean only values whose complete virtual account perturbation is safe."""

        published = np.asarray(raw_primal, dtype=np.float64).copy()
        assessed = np.abs(reference.canonical_observation(observed))
        reference_max = np.max(np.abs(reference.scaled_values), axis=0)
        coefficient_scale = np.maximum(1.0, np.maximum(assessed, reference_max))
        thresholds = self.tolerance / (max(1, published.size) * coefficient_scale)
        published[np.abs(published) <= thresholds] = 0.0
        return published

    def _certify_task(
        self,
        *,
        problem: LinearProgram,
        solution: LPSolution,
        reference: CompiledGeneralAdditiveReference,
        layout: CompiledNetworkLayout,
        observed: np.ndarray,
        minimum_shares: np.ndarray,
        self_in_reference: bool,
    ) -> _CertifiedGeneralAdditiveTask:
        """Certify one solved programme without performing another solve."""

        certificate = certify_lp_solution(
            problem,
            solution,
            tolerance=self.tolerance,
        )
        unavailable = "not_available_without_certified_primary"
        if not certificate.certified or solution.primal is None:
            return _CertifiedGeneralAdditiveTask(
                solution=solution,
                certificate=certificate,
                score_valid=False,
                score_status=(
                    "solver_failed"
                    if solution.status is not SolverStatus.OPTIMAL
                    else "unavailable_uncertified_source_program"
                ),
                published_account=None,
                process_account_valid=False,
                process_account_status=unavailable,
                link_account_valid=False,
                link_account_status=unavailable,
                raw_economic_certified=None,
                published_economic_certified=None,
                raw_economic_violation=math.nan,
                published_economic_violation=math.nan,
                economic_certification_reason=(
                    "not_checked_uncertified_source_program"
                ),
            )

        raw_account = self._rebuild_account(
            reference=reference,
            layout=layout,
            observed=observed,
            primal=solution.primal,
            reported_objective=float(solution.objective),
            minimum_shares=minimum_shares,
            self_in_reference=self_in_reference,
        )
        raw_certified = bool(raw_account.max_violation <= self.tolerance)
        if not raw_certified:
            return _CertifiedGeneralAdditiveTask(
                solution=solution,
                certificate=certificate,
                score_valid=False,
                score_status="unavailable_uncertified_source_program",
                published_account=None,
                process_account_valid=False,
                process_account_status=unavailable,
                link_account_valid=False,
                link_account_status=unavailable,
                raw_economic_certified=False,
                published_economic_certified=None,
                raw_economic_violation=raw_account.max_violation,
                published_economic_violation=math.nan,
                economic_certification_reason=(
                    "raw_general_additive_account_reconstruction_failed"
                ),
            )

        published_primal = self._publication_primal(
            reference=reference,
            observed=observed,
            raw_primal=solution.primal,
        )
        published_account = self._rebuild_account(
            reference=reference,
            layout=layout,
            observed=observed,
            primal=published_primal,
            reported_objective=float(solution.objective),
            minimum_shares=minimum_shares,
            self_in_reference=self_in_reference,
        )
        published_certified = bool(published_account.max_violation <= self.tolerance)
        if not published_certified:
            return _CertifiedGeneralAdditiveTask(
                solution=solution,
                certificate=certificate,
                score_valid=False,
                score_status="unavailable_uncertified_source_program",
                published_account=None,
                process_account_valid=False,
                process_account_status=unavailable,
                link_account_valid=False,
                link_account_status=unavailable,
                raw_economic_certified=True,
                published_economic_certified=False,
                raw_economic_violation=raw_account.max_violation,
                published_economic_violation=published_account.max_violation,
                economic_certification_reason=(
                    "published_general_additive_account_reconstruction_failed"
                ),
            )
        return _CertifiedGeneralAdditiveTask(
            solution=solution,
            certificate=certificate,
            score_valid=True,
            score_status="defined",
            published_account=published_account,
            process_account_valid=True,
            process_account_status="defined",
            link_account_valid=True,
            link_account_status="defined",
            raw_economic_certified=True,
            published_economic_certified=True,
            raw_economic_violation=raw_account.max_violation,
            published_economic_violation=published_account.max_violation,
            economic_certification_reason="certified",
        )

    def fit(self, data: NetworkData) -> DEAResult:
        """Estimate system and process accounts for every network observation."""
        if not isinstance(data, NetworkData):
            raise TypeError("CookZhuBiYangAdditiveDEA.fit expects NetworkData")
        data.ensure_nonnegative(model_name="Cook--Zhu--Bi--Yang additive network DEA")
        layout = compile_network_layout(data.network_spec)
        minimum_shares, minimum_share_by_process = self._resolved_process_shares(layout)
        reference_plan = build_reference_plan(data, self.reference)
        compiled: dict[int, CompiledGeneralAdditiveReference] = {}

        summary_rows: list[dict[str, Any]] = []
        component_rows: list[dict[str, Any]] = []
        multiplier_rows: list[dict[str, Any]] = []
        link_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []
        primary_solver_calls = 0

        for observation in range(data.n_dmus):
            set_id = reference_plan.set_id_for(observation)
            reference = compiled.get(set_id)
            if reference is None:
                reference = compile_general_additive_reference(
                    data.values,
                    data.variable_names,
                    layout,
                    reference_plan.rows_for(observation),
                )
                compiled[set_id] = reference

            dmu_id = data.dmu_ids[observation]
            period = None if data.periods is None else data.periods[observation]
            label = f"{dmu_id}@{period}" if period is not None else str(dmu_id)
            observed = data.values[observation]
            problem = primary_problem(
                reference,
                observed,
                minimum_shares,
                f"{label}:system",
            )
            primary = self.solver.solve(problem)
            primary_solver_calls += 1
            task = self._certify_task(
                problem=problem,
                solution=primary,
                reference=reference,
                layout=layout,
                observed=observed,
                minimum_shares=minimum_shares,
                self_in_reference=bool(np.any(reference.rows == observation)),
            )
            diagnostic_rows.append(
                _diagnostic(
                    dmu_id=dmu_id,
                    period=period,
                    task=task,
                )
            )
            if not task.score_valid or task.published_account is None:
                summary_rows.append(
                    self._undefined_summary(
                        dmu_id=dmu_id,
                        period=period,
                        reference_size=reference.size,
                        process_count=layout.n_processes,
                        status=task.score_status,
                        solver_status=primary.status,
                    )
                )
                continue
            account = task.published_account
            process_inputs = account.process_inputs
            process_outputs = account.process_outputs
            process_scores = account.process_scores
            total_input = account.total_input
            system_score = account.system_score
            weighted_process_sum = account.total_output
            reconstruction_residual = weighted_process_sum - system_score
            finite_process_scores = np.isfinite(process_scores)
            within_reference = bool(system_score <= 1.0 + self.tolerance)
            system_efficient = bool(
                within_reference and abs(system_score - 1.0) <= self.tolerance
            )

            local_components: list[dict[str, Any]] = []
            local_multipliers: list[dict[str, Any]] = []
            local_links: list[dict[str, Any]] = []
            local_components.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "component_kind": "system",
                    "component_id": "system",
                    "score": system_score,
                    "efficiency": system_score,
                    "aggregation_weight": 1.0,
                    "weight_origin": "system_identity",
                    "virtual_input": total_input,
                    "virtual_output": weighted_process_sum,
                    "is_measure_efficient": system_efficient,
                    "selection_policy": "maximize_system_efficiency",
                    "status": "defined",
                    "account_valid": True,
                    "account_status": "defined",
                }
            )
            for position, process in enumerate(layout.processes):
                score = float(process_scores[position])
                local_components.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "component_kind": "process",
                        "component_id": process.process_id,
                        "score": score,
                        "efficiency": score,
                        "aggregation_weight": float(process_inputs[position]),
                        "weight_origin": ("endogenous_virtual_process_input_share"),
                        "virtual_input": float(process_inputs[position]),
                        "virtual_output": float(process_outputs[position]),
                        "is_measure_efficient": (
                            bool(abs(score - 1.0) <= self.tolerance)
                            if math.isfinite(score)
                            else pd.NA
                        ),
                        "selection_policy": ("solver_selected_primary_optimum"),
                        "status": (
                            "defined"
                            if math.isfinite(score)
                            else "undefined_zero_virtual_input"
                        ),
                        "account_valid": True,
                        "account_status": task.process_account_status,
                    }
                )

            self._append_multiplier_accounts(
                rows=local_multipliers,
                links=local_links,
                data=data,
                observation=observation,
                reference=reference,
                layout=layout,
                account=account,
            )
            component_rows.extend(local_components)
            multiplier_rows.extend(local_multipliers)
            link_rows.extend(local_links)
            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "score": system_score,
                    "efficiency": system_score,
                    "score_valid": True,
                    "distance": np.nan,
                    "system_efficiency": system_score,
                    "weighted_process_sum": weighted_process_sum,
                    "reconstruction_residual": reconstruction_residual,
                    "all_process_accounts_defined": bool(finite_process_scores.all()),
                    "zero_weight_processes": int(
                        np.count_nonzero(process_inputs <= self.tolerance)
                    ),
                    "is_additively_efficient": system_efficient,
                    "is_efficient": pd.NA,
                    "is_within_reference_technology": within_reference,
                    "decomposition_status": (
                        "solver_selected_not_uniqueness_certified"
                    ),
                    "process_account_valid": task.process_account_valid,
                    "process_account_status": task.process_account_status,
                    "link_account_valid": task.link_account_valid,
                    "link_account_status": task.link_account_status,
                    "decomposition_unique": pd.NA,
                    "target_valid": False,
                    "target_status": "not_available_in_source_contract",
                    "peer_valid": False,
                    "peer_status": "not_available_in_source_contract",
                    "solver_status": primary.status.value,
                    "backend_solver_status": primary.status.value,
                    "raw_solver_status": primary.status.value,
                    "score_status": "defined",
                    "model_family": "network_general_additive_decomposition",
                    "returns_to_scale": "crs",
                    "reference_size": reference.size,
                    "process_count": layout.n_processes,
                }
            )

        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
            components=pd.DataFrame(component_rows, columns=_COMPONENT_COLUMNS),
            multipliers=pd.DataFrame(multiplier_rows, columns=_MULTIPLIER_COLUMNS),
            links=pd.DataFrame(link_rows, columns=_LINK_COLUMNS),
            diagnostics=pd.DataFrame(diagnostic_rows),
            metadata={
                **registry_metadata(
                    self._registry_method_id,
                    {
                        "context": {
                            "purpose": ("joint_system_and_process_accountability"),
                            "sample": ("panel" if data.is_panel else "cross_section"),
                        },
                        "graph": {
                            "kind": "source_compatible_directed_acyclic_network",
                            "processes": [
                                {
                                    "id": process.process_id,
                                    "external_inputs": list(process.external_inputs),
                                    "external_outputs": list(process.external_outputs),
                                    "incoming_links": list(process.incoming_links),
                                    "outgoing_links": list(process.outgoing_links),
                                }
                                for process in layout.processes
                            ],
                            "links": [
                                {
                                    "id": link.link_id,
                                    "source": link.source,
                                    "target": link.target,
                                    "variables": list(link.variables),
                                }
                                for link in layout.links
                            ],
                        },
                        "data_roles": {
                            "variables": {
                                "external_inputs": list(layout.external_inputs),
                                "links": list(layout.link_variables),
                                "external_outputs": list(layout.external_outputs),
                            },
                            "counts": {
                                "external_inputs": len(layout.external_inputs),
                                "links": len(layout.link_variables),
                                "external_outputs": len(layout.external_outputs),
                            },
                            "panel": data.is_panel,
                            "grouped": data.groups is not None,
                        },
                        "technology": {
                            "family": "cook_etal_general_additive_network",
                            "returns_to_scale": "crs",
                            "process_intensity": "multiplier_joint_account",
                            "link_valuation": "shared_source_recipient_multiplier",
                        },
                        "estimator": {
                            "estimator_id": "estimator.full.dea",
                            "kind": "full_frontier",
                            "family": "sparse_multiplier",
                        },
                        "reference": registry_reference_spec(
                            self.reference,
                            reference_plan.kind,
                        ),
                        "performance": {
                            "family": "cook_etal_weighted_additive",
                            "orientation": "total_process_input_normalized",
                            "system_identity": (
                                "virtual_process_input_share_weighted_sum"
                            ),
                        },
                        "valuation": {
                            "kind": "endogenous_multiplier",
                            "process_weight_origin": (
                                "endogenous_virtual_process_input_share"
                            ),
                            "minimum_process_shares": (minimum_share_by_process),
                            "weight_floor": ("explicit_policy_no_numeric_epsilon"),
                        },
                        "evaluation_protocol": {
                            "kind": "self_appraisal",
                            "process_selection": ("solver_selected_primary_optimum"),
                            "projection": "not_source_defined",
                            "strong_slack_completion": False,
                        },
                        "analysis": {
                            "kind": "system_process_additive_decomposition",
                            "reconstruction_check": True,
                        },
                        "uncertainty": {
                            "sampling": {"kind": "none"},
                            "data": {"kind": "none"},
                        },
                    },
                ),
                "graph_fingerprint": data.graph_fingerprint,
                "minimum_process_shares": minimum_share_by_process,
                "compiled_reference_sets": len(compiled),
                "primary_solver_calls": primary_solver_calls,
                "secondary_solver_calls": 0,
                "projection_fallback_solver_calls": 0,
                "solver_calls": primary_solver_calls,
                "additional_solver_calls": 0,
                "certificate_extra_solver_calls": 0,
                "validation_basis": {
                    "source_doi": "10.1016/j.ejor.2010.05.006",
                    "seller_buyer": {
                        "dataset": "open_service_chain",
                        "checks": "system_process_and_share_reconstruction",
                    },
                    "three_stage": {
                        "dataset": "three_process_service_chain",
                        "checks": "system_process_and_declared_share_reconstruction",
                    },
                    "source_equation_note": (
                        "Equation (5) prints eta_2k in the objective; "
                        "Equation (4) and the remaining two-stage accounts "
                        "require the shared eta_1k link valuation."
                    ),
                },
                "unsupported_extensions": (
                    "general_network_vrs",
                    "cycles",
                    "shared_resource_pools",
                    "transformed_or_lossy_links",
                    "source_projection",
                ),
                "postsolve_certificate": {
                    "lp": "solver_neutral_primal_dual_kkt_and_strong_duality",
                    "economic": "normalization_objective_and_additive_identity",
                    "failure_policy": (
                        "fail_closed_without_score_components_multipliers_or_links"
                    ),
                },
            },
        )

    def _append_multiplier_accounts(
        self,
        *,
        rows: list[dict[str, Any]],
        links: list[dict[str, Any]],
        data: NetworkData,
        observation: int,
        reference: CompiledGeneralAdditiveReference,
        layout: CompiledNetworkLayout,
        account: _GeneralAdditiveAccount,
    ) -> None:
        dmu_id = data.dmu_ids[observation]
        period = None if data.periods is None else data.periods[observation]
        canonical_observed = reference.canonical_observation(data.values[observation])
        original_observed = canonical_observed * reference.scales
        link_by_variable = {
            variable: link for link in layout.links for variable in link.variables
        }
        input_owner = {
            variable: process.process_id
            for process in layout.processes
            for variable in process.external_inputs
        }
        output_owner = {
            variable: process.process_id
            for process in layout.processes
            for variable in process.external_outputs
        }

        for position, variable in enumerate(layout.variable_names):
            role = layout.variable_roles[position]
            link = link_by_variable.get(variable)
            process_id = (
                input_owner[variable]
                if role == EXTERNAL_INPUT
                else output_owner[variable]
                if role == EXTERNAL_OUTPUT
                else f"{link.source}|{link.target}"
                if link is not None
                else None
            )
            scaled_multiplier = float(account.primal[position])
            multiplier = float(account.multipliers[position])
            observed = float(original_observed[position])
            rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "phase": "system",
                    "process_id": process_id,
                    "role": role,
                    "variable": variable,
                    "scaled_multiplier": scaled_multiplier,
                    "multiplier": multiplier,
                    "observed": observed,
                    "virtual_contribution": multiplier * observed,
                    "shared_between": (
                        None
                        if link is None
                        else f"{link.source}.output|{link.target}.input"
                    ),
                    "selection_policy": "solver_selected_primary_optimum",
                    "is_zero_for_display": bool(
                        abs(scaled_multiplier) <= self.tolerance
                    ),
                    "account_valid": True,
                    "account_status": "defined",
                }
            )
            if role == LINK_VARIABLE and link is not None:
                links.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "link_id": link.link_id,
                        "source_process_id": link.source,
                        "target_process_id": link.target,
                        "variable": variable,
                        "observed_source": observed,
                        "observed_target": observed,
                        "shared_multiplier": multiplier,
                        "virtual_contribution": multiplier * observed,
                        "source_virtual_contribution": multiplier * observed,
                        "target_virtual_contribution": multiplier * observed,
                        "balance_residual": 0.0,
                        "link_account_valid": True,
                        "link_account_status": "defined",
                        "target_status": "not_source_defined",
                    }
                )

    @staticmethod
    def _undefined_summary(
        *,
        dmu_id: object,
        period: object | None,
        reference_size: int,
        process_count: int,
        status: str,
        solver_status: SolverStatus,
    ) -> dict[str, Any]:
        return {
            "dmu_id": dmu_id,
            "period": period,
            "score": np.nan,
            "efficiency": np.nan,
            "score_valid": False,
            "distance": np.nan,
            "system_efficiency": np.nan,
            "weighted_process_sum": np.nan,
            "reconstruction_residual": np.nan,
            "all_process_accounts_defined": False,
            "zero_weight_processes": pd.NA,
            "is_additively_efficient": pd.NA,
            "is_efficient": pd.NA,
            "is_within_reference_technology": pd.NA,
            "decomposition_status": status,
            "process_account_valid": False,
            "process_account_status": "not_available_without_certified_primary",
            "link_account_valid": False,
            "link_account_status": "not_available_without_certified_primary",
            "decomposition_unique": pd.NA,
            "target_valid": False,
            "target_status": "not_available_in_source_contract",
            "peer_valid": False,
            "peer_status": "not_available_in_source_contract",
            "solver_status": solver_status.value,
            "backend_solver_status": solver_status.value,
            "raw_solver_status": solver_status.value,
            "score_status": status,
            "model_family": "network_general_additive_decomposition",
            "returns_to_scale": "crs",
            "reference_size": reference_size,
            "process_count": process_count,
        }


GeneralAdditiveNetworkDEA = CookZhuBiYangAdditiveDEA

__all__ = [
    "CookZhuBiYangAdditiveDEA",
    "GeneralAdditiveNetworkDEA",
]
