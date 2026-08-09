"""Profit efficiency on the shared convex DEA technology."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix

from .._registry import data_role_schema, registry_metadata
from .._registry import reference_spec as registry_reference_spec
from ..data import DEAData
from ..enums import ReturnsToScale, SolverStatus, parse_enum
from ..exceptions import DataValidationError, ModelSpecificationError
from ..models._common import (
    CompiledReference,
    compile_reference,
    get_or_compile_reference,
)
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
from ._lp import (
    EconomicLPTemplate,
    compile_economic_template,
    reference_self_coverage,
)
from ._postsolve import (
    lp_diagnostic_fields,
    maximum_violation,
    scaled_array_residual,
    scaled_lower_violation,
    scaled_nonnegative_violation,
    scaled_residual,
)
from .prices import PriceData, ResolvedPrices


@dataclass(frozen=True, slots=True)
class _ProfitTargetCertificate:
    """Reconstruction checks shared by consumers of one cached profit task."""

    certified: bool
    reason: str
    target_input_residual: float
    target_output_residual: float
    objective_profit_residual: float
    target_profit_identity_residual: float
    convexity_residual: float
    target_nonnegative_violation: float
    max_economic_violation: float


@dataclass(frozen=True, slots=True)
class _ProfitObservationCertificate:
    """Price-account checks that remain specific to one evaluated activity."""

    certified: bool
    reason: str
    observed_cost_residual: float
    observed_revenue_residual: float
    observed_profit_residual: float
    profit_gap_residual: float
    self_appraisal_bound_residual: float
    max_economic_violation: float


@dataclass(frozen=True, slots=True)
class _ProfitTaskResult:
    """One solved and certified price/reference task reusable across DMUs."""

    solution: LPSolution
    lp_certificate: LPCertificate
    lambdas: np.ndarray | None
    target_inputs: np.ndarray | None
    target_outputs: np.ndarray | None
    target_cost: float | None
    target_revenue: float | None
    maximum_profit: float | None
    target_certificate: _ProfitTargetCertificate | None
    peer_positions: tuple[int, ...]
    peer_account_certified: bool
    peer_account_residual: float


def _certify_profit_target_account(
    *,
    reference: CompiledReference,
    objective: np.ndarray,
    solution: LPSolution,
    lambdas: np.ndarray,
    target_inputs: np.ndarray,
    target_outputs: np.ndarray,
    input_prices: np.ndarray,
    output_prices: np.ndarray,
    target_cost: float,
    target_revenue: float,
    maximum_profit: float,
    tolerance: float,
) -> _ProfitTargetCertificate:
    """Independently reconstruct a cached maximum-profit activity account."""

    reconstructed_inputs = np.asarray(reference.inputs @ lambdas).reshape(-1)
    reconstructed_outputs = np.asarray(reference.outputs @ lambdas).reshape(-1)
    target_input_residual = scaled_array_residual(
        target_inputs,
        reconstructed_inputs,
    )
    target_output_residual = scaled_array_residual(
        target_outputs,
        reconstructed_outputs,
    )
    target_cost_residual = scaled_residual(
        target_cost,
        float(input_prices @ target_inputs),
    )
    target_revenue_residual = scaled_residual(
        target_revenue,
        float(output_prices @ target_outputs),
    )
    minimized_value = target_cost - target_revenue
    objective_vector_residual = scaled_residual(
        minimized_value,
        float(objective @ lambdas),
    )
    reported_objective_residual = (
        math.inf
        if solution.objective is None
        else scaled_residual(minimized_value, float(solution.objective))
    )
    objective_profit_residual = max(
        objective_vector_residual,
        reported_objective_residual,
        scaled_residual(maximum_profit, -minimized_value),
    )
    target_profit_identity_residual = scaled_residual(
        maximum_profit,
        target_revenue - target_cost,
    )
    convexity_residual = scaled_residual(float(lambdas.sum()), 1.0)
    target_nonnegative_violation = max(
        scaled_lower_violation(target_inputs, np.zeros_like(target_inputs)),
        scaled_lower_violation(target_outputs, np.zeros_like(target_outputs)),
    )
    max_economic_violation = maximum_violation(
        (
            target_input_residual,
            target_output_residual,
            target_cost_residual,
            target_revenue_residual,
            objective_profit_residual,
            target_profit_identity_residual,
            convexity_residual,
            target_nonnegative_violation,
        )
    )
    certified = bool(max_economic_violation <= 10.0 * tolerance)
    return _ProfitTargetCertificate(
        certified=certified,
        reason=("certified" if certified else "profit_target_account_failed"),
        target_input_residual=target_input_residual,
        target_output_residual=target_output_residual,
        objective_profit_residual=objective_profit_residual,
        target_profit_identity_residual=target_profit_identity_residual,
        convexity_residual=convexity_residual,
        target_nonnegative_violation=target_nonnegative_violation,
        max_economic_violation=max_economic_violation,
    )


def _certify_profit_observation_account(
    *,
    observed_inputs: np.ndarray,
    observed_outputs: np.ndarray,
    input_prices: np.ndarray,
    output_prices: np.ndarray,
    observed_cost: float,
    observed_revenue: float,
    observed_profit: float,
    maximum_profit: float,
    profit_gap: float,
    self_in_reference: bool,
    tolerance: float,
) -> _ProfitObservationCertificate:
    """Reconstruct the signed observed-profit and opportunity-gap account."""

    observed_cost_residual = scaled_residual(
        observed_cost,
        float(input_prices @ observed_inputs),
    )
    observed_revenue_residual = scaled_residual(
        observed_revenue,
        float(output_prices @ observed_outputs),
    )
    observed_profit_residual = scaled_residual(
        observed_profit,
        observed_revenue - observed_cost,
    )
    profit_gap_residual = scaled_residual(
        profit_gap,
        maximum_profit - observed_profit,
    )
    self_appraisal_bound_residual = (
        scaled_nonnegative_violation(profit_gap) if self_in_reference else 0.0
    )
    max_economic_violation = maximum_violation(
        (
            observed_cost_residual,
            observed_revenue_residual,
            observed_profit_residual,
            profit_gap_residual,
            self_appraisal_bound_residual,
        )
    )
    certified = bool(max_economic_violation <= 10.0 * tolerance)
    return _ProfitObservationCertificate(
        certified=certified,
        reason=("certified" if certified else "profit_observation_account_failed"),
        observed_cost_residual=observed_cost_residual,
        observed_revenue_residual=observed_revenue_residual,
        observed_profit_residual=observed_profit_residual,
        profit_gap_residual=profit_gap_residual,
        self_appraisal_bound_residual=self_appraisal_bound_residual,
        max_economic_violation=max_economic_violation,
    )


class ProfitEfficiency:
    """Maximum-profit analysis when both inputs and outputs may adjust.

    The native performance value is the attainable profit gap, not a ratio.
    The initial public formulation is deliberately VRS-only: the convexity
    equality makes the value problem finite without silently adding a shutdown
    option or accepting the positive-profit rays possible under CRS.
    """

    _registry_method_id = "economic.profit.maximum"

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
            returns_to_scale, ReturnsToScale, "returns_to_scale"
        )
        if self.returns_to_scale is not ReturnsToScale.VRS:
            raise ModelSpecificationError(
                "ProfitEfficiency currently supports only VRS. CRS can contain "
                "unbounded positive-profit production rays, and alternative "
                "shutdown/scale policies require separately validated methods."
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
        if not np.isfinite(tolerance) or tolerance <= 0:
            raise ValueError("tolerance must be a positive finite number")
        self.tolerance = float(tolerance)
        self.peer_tolerance = (
            self.tolerance if peer_tolerance is None else float(peer_tolerance)
        )
        if not np.isfinite(self.peer_tolerance) or self.peer_tolerance <= 0:
            raise ValueError("peer_tolerance must be a positive finite number")

    def _validate_data(self, data: DEAData) -> None:
        data.ensure_nonnegative()
        if data.bad_outputs is not None:
            raise ModelSpecificationError(
                "ProfitEfficiency does not infer an environmental profit "
                "technology for undesirable outputs. Use a separately "
                "registered environmental-economic model."
            )
        if np.any(data.inputs.sum(axis=1) <= 0):
            raise DataValidationError(
                "each observation needs at least one strictly positive input"
            )
        if np.any(data.outputs.sum(axis=1) <= 0):
            raise DataValidationError(
                "each observation needs at least one strictly positive output"
            )

    def _compile_template(
        self,
        reference: CompiledReference,
    ) -> EconomicLPTemplate:
        # Profit changes inputs and outputs jointly, so there is no
        # observation-specific capacity or commitment row.
        quantity_rows = csc_matrix((0, reference.size), dtype=np.float64)
        return compile_economic_template(
            reference,
            self.returns_to_scale,
            quantity_rows,
        )

    @staticmethod
    def _problem(
        template: EconomicLPTemplate,
        objective: np.ndarray,
        name: str,
    ) -> LinearProgram:
        return template.problem(
            objective=objective,
            quantity_rhs=np.empty(0, dtype=np.float64),
            name=f"{name}:profit",
        )

    def _dual_rows(
        self,
        data: DEAData,
        observation: int,
        solution: LPSolution,
    ) -> list[dict[str, Any]]:
        if solution.equality_marginals is None:
            return []
        period = None if data.periods is None else data.periods[observation]
        return [
            {
                "dmu_id": data.dmu_ids[observation],
                "period": period,
                "source": "model_derived",
                "value_type": "shadow_value",
                "constraint_role": "convexity",
                "variable": "sum_lambda",
                "solver_marginal": float(solution.equality_marginals[0]),
                "economic_marginal": np.nan,
            }
        ]

    def _solve_profit_task(
        self,
        *,
        reference: CompiledReference,
        problem: LinearProgram,
        objective: np.ndarray,
        input_prices: np.ndarray,
        output_prices: np.ndarray,
    ) -> _ProfitTaskResult:
        """Solve and certify one unique reference-and-price task."""

        solution = self.solver.solve(problem)
        lp_certificate = certify_lp_solution(
            problem,
            solution,
            tolerance=self.tolerance,
        )
        if not lp_certificate.certified or solution.primal is None:
            return _ProfitTaskResult(
                solution=solution,
                lp_certificate=lp_certificate,
                lambdas=None,
                target_inputs=None,
                target_outputs=None,
                target_cost=None,
                target_revenue=None,
                maximum_profit=None,
                target_certificate=None,
                peer_positions=(),
                peer_account_certified=False,
                peer_account_residual=math.inf,
            )

        lambdas = np.asarray(solution.primal, dtype=np.float64)
        target_inputs = np.asarray(reference.inputs @ lambdas).reshape(-1)
        target_outputs = np.asarray(reference.outputs @ lambdas).reshape(-1)
        target_cost = float(input_prices @ target_inputs)
        target_revenue = float(output_prices @ target_outputs)
        maximum_profit = target_revenue - target_cost
        target_certificate = _certify_profit_target_account(
            reference=reference,
            objective=objective,
            solution=solution,
            lambdas=lambdas,
            target_inputs=target_inputs,
            target_outputs=target_outputs,
            input_prices=input_prices,
            output_prices=output_prices,
            target_cost=target_cost,
            target_revenue=target_revenue,
            maximum_profit=maximum_profit,
            tolerance=self.tolerance,
        )

        peer_positions = tuple(
            int(position) for position in np.flatnonzero(lambdas > self.peer_tolerance)
        )
        published_lambdas = np.zeros_like(lambdas)
        if peer_positions:
            published_lambdas[np.asarray(peer_positions, dtype=np.int64)] = lambdas[
                np.asarray(peer_positions, dtype=np.int64)
            ]
        peer_account_residual = max(
            scaled_array_residual(
                np.asarray(reference.inputs @ published_lambdas).reshape(-1),
                target_inputs,
            ),
            scaled_array_residual(
                np.asarray(reference.outputs @ published_lambdas).reshape(-1),
                target_outputs,
            ),
        )
        peer_account_certified = bool(
            target_certificate.certified
            and peer_account_residual <= 10.0 * self.tolerance
        )
        return _ProfitTaskResult(
            solution=solution,
            lp_certificate=lp_certificate,
            lambdas=lambdas,
            target_inputs=target_inputs,
            target_outputs=target_outputs,
            target_cost=target_cost,
            target_revenue=target_revenue,
            maximum_profit=maximum_profit,
            target_certificate=target_certificate,
            peer_positions=peer_positions,
            peer_account_certified=peer_account_certified,
            peer_account_residual=peer_account_residual,
        )

    def fit(self, data: DEAData, prices: PriceData) -> DEAResult:
        """Estimate observed and maximum attainable profit for every observation."""
        return self._fit(data, prices)

    def _fit(
        self,
        data: DEAData,
        prices: PriceData,
        *,
        compiled_references: dict[int, CompiledReference] | None = None,
    ) -> DEAResult:
        """Private execution path that may share compiled references."""
        if not isinstance(prices, PriceData):
            raise TypeError("prices must be a PriceData instance")
        self._validate_data(data)
        resolved: ResolvedPrices = prices.resolve(
            data,
            require_inputs=True,
            require_outputs=True,
        )
        assert resolved.input_prices is not None
        assert resolved.output_prices is not None
        input_prices = resolved.input_prices
        output_prices = resolved.output_prices

        with np.errstate(over="ignore", invalid="ignore"):
            observed_costs = np.einsum("ij,ij->i", input_prices, data.inputs)
            observed_revenues = np.einsum("ij,ij->i", output_prices, data.outputs)
            observed_profits = observed_revenues - observed_costs
        if not (
            np.isfinite(observed_costs).all()
            and np.isfinite(observed_revenues).all()
            and np.isfinite(observed_profits).all()
        ):
            invalid = np.flatnonzero(
                ~(
                    np.isfinite(observed_costs)
                    & np.isfinite(observed_revenues)
                    & np.isfinite(observed_profits)
                )
            )[:5].tolist()
            raise DataValidationError(
                "observed monetary values must be finite after applying prices; "
                f"invalid row positions include {invalid}"
            )

        reference_plan = build_reference_plan(data, self.reference)
        compiled = {} if compiled_references is None else compiled_references
        templates: dict[int, EconomicLPTemplate] = {}
        objective_cache: dict[tuple[int, bytes, bytes], np.ndarray] = {}
        task_cache: dict[tuple[int, bytes, bytes], _ProfitTaskResult] = {}
        target_account_computations = 0

        summary_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []
        dual_rows: list[dict[str, Any]] = []

        for observation in range(data.n_dmus):
            set_id = reference_plan.set_id_for(observation)
            reference_rows = reference_plan.rows_for(observation)
            reference = get_or_compile_reference(
                data,
                reference_rows,
                set_id,
                compiled,
                compiler=compile_reference,
            )
            template = templates.get(set_id)
            if template is None:
                template = self._compile_template(reference)
                templates[set_id] = template

            dmu_id = data.dmu_ids[observation]
            period = None if data.periods is None else data.periods[observation]
            name = f"{dmu_id}@{period}" if period is not None else str(dmu_id)
            w_o = input_prices[observation]
            p_o = output_prices[observation]
            input_price_key = np.ascontiguousarray(
                w_o,
                dtype=np.dtype("<f8"),
            ).tobytes()
            output_price_key = np.ascontiguousarray(
                p_o,
                dtype=np.dtype("<f8"),
            ).tobytes()
            task_key = (set_id, input_price_key, output_price_key)

            objective = objective_cache.get(task_key)
            if objective is None:
                with np.errstate(over="ignore", invalid="ignore"):
                    objective = np.asarray(reference.inputs.T @ w_o).reshape(
                        -1
                    ) - np.asarray(reference.outputs.T @ p_o).reshape(-1)
                if not np.isfinite(objective).all():
                    raise DataValidationError(
                        "profit objective coefficients must be finite after "
                        f"applying prices; affected observation is {dmu_id!r}"
                    )
                objective = np.ascontiguousarray(objective, dtype=np.float64)
                objective.setflags(write=False)
                objective_cache[task_key] = objective

            task = task_cache.get(task_key)
            solution_reused = task is not None
            if task is None:
                problem = self._problem(template, objective, name)
                task = self._solve_profit_task(
                    reference=reference,
                    problem=problem,
                    objective=objective,
                    input_prices=w_o,
                    output_prices=p_o,
                )
                task_cache[task_key] = task
                if task.target_certificate is not None:
                    target_account_computations += 1
            solution = task.solution

            observed_cost = float(observed_costs[observation])
            observed_revenue = float(observed_revenues[observation])
            observed_profit = float(observed_profits[observation])
            self_in_reference = bool(observation in reference.rows)
            target_certificate = task.target_certificate
            diagnostic = {
                "dmu_id": dmu_id,
                "period": period,
                "phase": 1,
                "solver_status": solution.status.value,
                "message": solution.message,
                "iterations": solution.iterations,
                "max_primal_violation": solution.max_primal_violation,
                "solver_objective": solution.objective,
                "reconstructed_objective": (
                    np.nan if task.maximum_profit is None else task.maximum_profit
                ),
                "objective_reconstruction_residual": (
                    np.nan
                    if task.maximum_profit is None or solution.objective is None
                    else task.maximum_profit + float(solution.objective)
                ),
                "target_cost": (
                    np.nan if task.target_cost is None else task.target_cost
                ),
                "target_revenue": (
                    np.nan if task.target_revenue is None else task.target_revenue
                ),
                "convexity_residual": (
                    np.nan
                    if task.lambdas is None
                    else abs(float(task.lambdas.sum()) - 1.0)
                ),
                "finite_profit_optimum": False,
                "solution_reused": solution_reused,
                "certificate_reused": solution_reused,
                "target_account_reused": bool(
                    solution_reused and target_certificate is not None
                ),
                "self_in_reference": self_in_reference,
                "task_economic_postsolve_certified": bool(
                    target_certificate is not None and target_certificate.certified
                ),
                "target_input_residual": (
                    np.nan
                    if target_certificate is None
                    else target_certificate.target_input_residual
                ),
                "target_output_residual": (
                    np.nan
                    if target_certificate is None
                    else target_certificate.target_output_residual
                ),
                "objective_profit_residual": (
                    np.nan
                    if target_certificate is None
                    else target_certificate.objective_profit_residual
                ),
                "target_profit_identity_residual": (
                    np.nan
                    if target_certificate is None
                    else target_certificate.target_profit_identity_residual
                ),
                "target_nonnegative_violation": (
                    np.nan
                    if target_certificate is None
                    else target_certificate.target_nonnegative_violation
                ),
                "observed_cost_residual": np.nan,
                "observed_revenue_residual": np.nan,
                "observed_profit_residual": np.nan,
                "profit_gap_residual": np.nan,
                "self_appraisal_bound_residual": np.nan,
                "published_peer_account_certified": (task.peer_account_certified),
                "published_peer_account_residual": task.peer_account_residual,
                "published_dual_account_certified": False,
                "published_dual_row_count": 0,
                **lp_diagnostic_fields(task.lp_certificate),
            }

            common_summary = {
                "dmu_id": dmu_id,
                "period": period,
                "efficiency": np.nan,
                "distance": np.nan,
                "solver_status": solution.status.value,
                "model_family": "profit",
                "returns_to_scale": self.returns_to_scale.value,
                "reference_size": reference.size,
                "self_in_reference": self_in_reference,
                "observed_cost": observed_cost,
                "observed_revenue": observed_revenue,
                "observed_profit": observed_profit,
                "score_direction": "lower_is_better",
            }

            if not task.lp_certificate.certified or target_certificate is None:
                score_status = (
                    "solver_failed"
                    if solution.status is not SolverStatus.OPTIMAL
                    else "unavailable_uncertified_source_program"
                )
                diagnostic_rows.append(diagnostic)
                summary_rows.append(
                    {
                        **common_summary,
                        "score": np.nan,
                        "score_valid": False,
                        "score_status": score_status,
                        "is_efficient": pd.NA,
                        "is_profit_efficient": pd.NA,
                        "target_cost": np.nan,
                        "target_revenue": np.nan,
                        "maximum_profit": np.nan,
                        "profit_gap": np.nan,
                        "lp_postsolve_certified": False,
                        "postsolve_certified": False,
                        "economic_postsolve_certified": False,
                        "lp_certification_reason": task.lp_certificate.reason,
                        "certification_reason": task.lp_certificate.reason,
                        "economic_certification_reason": diagnostic[
                            "economic_certification_reason"
                        ],
                        "max_economic_violation": math.inf,
                        "target_valid": False,
                        "target_status": score_status,
                        "peer_valid": False,
                        "peer_status": score_status,
                        "dual_valid": False,
                        "dual_status": score_status,
                    }
                )
                continue

            if not target_certificate.certified:
                diagnostic.update(
                    {
                        "postsolve_certified": False,
                        "certification_reason": target_certificate.reason,
                        "economic_postsolve_certified": False,
                        "economic_certification_reason": target_certificate.reason,
                        "max_economic_violation": (
                            target_certificate.max_economic_violation
                        ),
                    }
                )
                diagnostic_rows.append(diagnostic)
                summary_rows.append(
                    {
                        **common_summary,
                        "score": np.nan,
                        "score_valid": False,
                        "score_status": "unavailable_uncertified_profit_account",
                        "is_efficient": pd.NA,
                        "is_profit_efficient": pd.NA,
                        "target_cost": np.nan,
                        "target_revenue": np.nan,
                        "maximum_profit": np.nan,
                        "profit_gap": np.nan,
                        "lp_postsolve_certified": True,
                        "postsolve_certified": False,
                        "economic_postsolve_certified": False,
                        "lp_certification_reason": task.lp_certificate.reason,
                        "certification_reason": target_certificate.reason,
                        "economic_certification_reason": target_certificate.reason,
                        "max_economic_violation": (
                            target_certificate.max_economic_violation
                        ),
                        "target_valid": False,
                        "target_status": "unavailable_uncertified_profit_account",
                        "peer_valid": False,
                        "peer_status": "unavailable_uncertified_profit_account",
                        "dual_valid": False,
                        "dual_status": "unavailable_uncertified_profit_account",
                    }
                )
                continue

            assert task.lambdas is not None
            assert task.target_inputs is not None
            assert task.target_outputs is not None
            assert task.target_cost is not None
            assert task.target_revenue is not None
            assert task.maximum_profit is not None
            raw_profit_gap = task.maximum_profit - observed_profit
            observation_certificate = _certify_profit_observation_account(
                observed_inputs=data.inputs[observation],
                observed_outputs=data.outputs[observation],
                input_prices=w_o,
                output_prices=p_o,
                observed_cost=observed_cost,
                observed_revenue=observed_revenue,
                observed_profit=observed_profit,
                maximum_profit=task.maximum_profit,
                profit_gap=raw_profit_gap,
                self_in_reference=self_in_reference,
                tolerance=self.tolerance,
            )
            max_economic_violation = max(
                target_certificate.max_economic_violation,
                observation_certificate.max_economic_violation,
            )
            diagnostic.update(
                {
                    "observed_cost_residual": (
                        observation_certificate.observed_cost_residual
                    ),
                    "observed_revenue_residual": (
                        observation_certificate.observed_revenue_residual
                    ),
                    "observed_profit_residual": (
                        observation_certificate.observed_profit_residual
                    ),
                    "profit_gap_residual": (
                        observation_certificate.profit_gap_residual
                    ),
                    "self_appraisal_bound_residual": (
                        observation_certificate.self_appraisal_bound_residual
                    ),
                    "economic_postsolve_certified": (observation_certificate.certified),
                    "economic_certification_reason": (observation_certificate.reason),
                    "postsolve_certified": observation_certificate.certified,
                    "certification_reason": observation_certificate.reason,
                    "max_economic_violation": max_economic_violation,
                    "finite_profit_optimum": observation_certificate.certified,
                }
            )
            if not observation_certificate.certified:
                diagnostic_rows.append(diagnostic)
                summary_rows.append(
                    {
                        **common_summary,
                        "score": np.nan,
                        "score_valid": False,
                        "score_status": "unavailable_uncertified_profit_account",
                        "is_efficient": pd.NA,
                        "is_profit_efficient": pd.NA,
                        "target_cost": np.nan,
                        "target_revenue": np.nan,
                        "maximum_profit": np.nan,
                        "profit_gap": np.nan,
                        "lp_postsolve_certified": True,
                        "postsolve_certified": False,
                        "economic_postsolve_certified": False,
                        "lp_certification_reason": task.lp_certificate.reason,
                        "certification_reason": observation_certificate.reason,
                        "economic_certification_reason": (
                            observation_certificate.reason
                        ),
                        "max_economic_violation": max_economic_violation,
                        "target_valid": False,
                        "target_status": "unavailable_uncertified_profit_account",
                        "peer_valid": False,
                        "peer_status": "unavailable_uncertified_profit_account",
                        "dual_valid": False,
                        "dual_status": "unavailable_uncertified_profit_account",
                    }
                )
                continue

            # Publish the exact monetary account certified above.  Numerical
            # tolerances classify efficiency; they must not manufacture a
            # different maximum-profit identity after certification.
            maximum_profit = task.maximum_profit
            profit_gap = raw_profit_gap

            if self_in_reference:
                score = profit_gap
                score_valid = True
                is_profit_efficient: bool | Any = bool(
                    abs(profit_gap) <= resolved.spec.monetary_tolerance
                )
                # With complete strictly positive prices, an observed activity
                # that maximizes profit over a technology containing itself
                # cannot be Pareto dominated. Profit inefficiency alone does
                # not establish technical inefficiency.
                is_efficient: bool | Any = True if is_profit_efficient else pd.NA
                score_status = "defined"
            else:
                score = np.nan
                score_valid = False
                is_profit_efficient = pd.NA
                is_efficient = pd.NA
                score_status = "undefined_external_reference"

            target_valid = True
            peer_valid = task.peer_account_certified
            candidate_dual_rows = self._dual_rows(data, observation, solution)
            dual_valid = len(candidate_dual_rows) == 1
            diagnostic.update(
                {
                    "peer_valid": peer_valid,
                    "max_published_peer_account_violation": (
                        task.peer_account_residual
                    ),
                    "published_dual_account_certified": dual_valid,
                    "published_dual_row_count": len(candidate_dual_rows),
                }
            )
            diagnostic_rows.append(diagnostic)
            if dual_valid:
                dual_rows.extend(candidate_dual_rows)

            if peer_valid:
                for local_position in task.peer_positions:
                    reference_position = reference.rows[local_position]
                    intensity_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "reference_dmu_id": data.dmu_ids[reference_position],
                            "reference_period": (
                                None
                                if data.periods is None
                                else data.periods[reference_position]
                            ),
                            "lambda": float(task.lambdas[local_position]),
                            "target_kind": "profit_maximizing_activity",
                            "selection_status": ("solver_selected_primary_optimum"),
                        }
                    )

            for role, names, observed, targets in (
                (
                    "input",
                    data.input_names,
                    data.inputs[observation],
                    task.target_inputs,
                ),
                (
                    "output",
                    data.output_names,
                    data.outputs[observation],
                    task.target_outputs,
                ),
            ):
                for variable, value, target in zip(
                    names,
                    observed,
                    targets,
                    strict=True,
                ):
                    target_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "role": role,
                            "variable": variable,
                            "observed": float(value),
                            "target": float(target),
                            "target_kind": "profit_maximizing_activity",
                            "selection_status": ("solver_selected_primary_optimum"),
                        }
                    )

            summary_rows.append(
                {
                    **common_summary,
                    "score": score,
                    "score_valid": score_valid,
                    "score_status": score_status,
                    "is_efficient": is_efficient,
                    "is_profit_efficient": is_profit_efficient,
                    "target_cost": task.target_cost,
                    "target_revenue": task.target_revenue,
                    "maximum_profit": maximum_profit,
                    "profit_gap": profit_gap,
                    "lp_postsolve_certified": True,
                    "postsolve_certified": True,
                    "economic_postsolve_certified": True,
                    "lp_certification_reason": task.lp_certificate.reason,
                    "certification_reason": observation_certificate.reason,
                    "economic_certification_reason": (observation_certificate.reason),
                    "max_economic_violation": max_economic_violation,
                    "target_valid": target_valid,
                    "target_status": "defined",
                    "peer_valid": peer_valid,
                    "peer_status": (
                        "defined"
                        if peer_valid
                        else "unavailable_thresholded_peer_account"
                    ),
                    "dual_valid": dual_valid,
                    "dual_status": (
                        "defined"
                        if dual_valid
                        else "unavailable_incomplete_dual_account"
                    ),
                }
            )

        price_metadata = dict(prices.metadata())
        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
            targets=pd.DataFrame(target_rows),
            intensities=pd.DataFrame(intensity_rows),
            duals=pd.DataFrame(dual_rows),
            diagnostics=pd.DataFrame(diagnostic_rows),
            metadata={
                **registry_metadata(
                    self._registry_method_id,
                    {
                        "context": {
                            "purpose": "maximum_profit_when_inputs_outputs_adjust",
                            "sample": "panel" if data.is_panel else "cross_section",
                        },
                        "graph": {"kind": "black_box"},
                        "data_roles": {
                            "inputs": "priced_adjustable_resources",
                            "outputs": "priced_adjustable_desirable_outputs",
                            "bad_outputs": "excluded",
                            **data_role_schema(data),
                        },
                        "technology": {
                            "family": "convex_envelopment",
                            "returns_to_scale": self.returns_to_scale.value,
                            "disposal": "ordinary_free",
                            "shutdown_option": "excluded_under_vrs_convex_hull",
                            "finite_value_policy": "vrs_simplex",
                        },
                        "estimator": {
                            "estimator_id": "estimator.full.dea",
                            "kind": "full_frontier",
                            "family": "dea_envelopment",
                        },
                        "reference": registry_reference_spec(
                            self.reference,
                            reference_plan.kind,
                        ),
                        "performance": {
                            "family": "economic_value",
                            "measure": "profit_gap",
                            "input_choice": "adjustable",
                            "output_choice": "adjustable",
                            "score_direction": "lower_is_better",
                            "ratio_score": "not_defined",
                        },
                        "valuation": {
                            "kind": "supplied_input_and_output_prices",
                            **price_metadata,
                        },
                        "evaluation_protocol": {
                            "kind": "self_appraisal",
                            "target_uniqueness": "unknown",
                            "self_in_reference": reference_self_coverage(
                                reference_plan.rows_by_observation
                            ),
                            "external_reference_score_policy": "fail_closed",
                        },
                        "analysis": {"kind": "direct_model_fit"},
                        "uncertainty": {"kind": "deterministic"},
                    },
                ),
                "model_family": "profit",
                "returns_to_scale": self.returns_to_scale.value,
                "reference_kind": reference_plan.kind.value,
                "native_score": "profit_gap",
                "score_direction": "lower_is_better",
                "efficiency_ratio": "not_defined",
                "target_kind": "profit_maximizing_activity",
                "target_uniqueness": "unknown",
                "finite_value_policy": "vrs_simplex",
                "shutdown_option": "excluded_under_vrs_convex_hull",
                "external_reference_score_policy": "fail_closed",
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "compiled_reference_sets": reference_plan.unique_reference_sets,
                "cached_objective_vectors": len(objective_cache),
                "cached_solutions": len(task_cache),
                "solver_calls": len(task_cache),
                "additional_solver_calls": 0,
                "postsolve_certificate": {
                    "kind": "solver_neutral_lp_and_profit_account",
                    "lp_checks": (
                        "primal_rows",
                        "variable_bounds",
                        "objective_reconstruction",
                        "dual_feasibility",
                        "complementarity",
                        "strong_duality",
                    ),
                    "economic_checks": (
                        "target_quantity_reconstruction",
                        "target_cost_and_revenue",
                        "maximum_profit_identity",
                        "observed_profit_identity",
                        "profit_gap_identity",
                        "self_appraisal_nonnegative_gap",
                    ),
                    "release_policy": (
                        "certified_external_targets_are_auditable_but_only_"
                        "certified_self_appraisal_has_a_score"
                    ),
                    "dual_release_policy": (
                        "complete_expected_published_dual_account_required"
                    ),
                    "published_account_policy": (
                        "certified_raw_monetary_values_are_not_postprocessed"
                    ),
                    "failure_isolation": (
                        "per_unique_profit_task_and_per_observation_account"
                    ),
                    "additional_solver_calls": 0,
                    "certificate_computations": len(task_cache),
                    "target_account_computations": target_account_computations,
                },
            },
        )


__all__ = ["ProfitEfficiency"]
