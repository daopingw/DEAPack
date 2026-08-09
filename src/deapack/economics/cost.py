"""Cost efficiency on the shared convex DEA technology."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

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
    scaled_upper_violation,
)
from .prices import PriceData, ResolvedPrices


@dataclass(frozen=True, slots=True)
class _CostAccountCertificate:
    """Independent reconstruction of one reported minimum-cost account."""

    certified: bool
    reason: str
    target_input_reconstruction_residual: float
    target_output_reconstruction_residual: float
    observed_cost_residual: float
    minimum_cost_reconstruction_residual: float
    solver_objective_reconstruction_residual: float
    output_commitment_violation: float
    cost_gap_identity_residual: float
    cost_efficiency_identity_residual: float
    minimum_cost_nonnegative_violation: float
    self_minimum_cost_upper_violation: float
    self_cost_gap_nonnegative_violation: float
    self_cost_efficiency_upper_violation: float
    max_violation: float


def _certify_cost_account(
    *,
    reference: CompiledReference,
    lambdas: np.ndarray,
    target_inputs: np.ndarray,
    target_outputs: np.ndarray,
    observed_inputs: np.ndarray,
    input_prices: np.ndarray,
    output_commitment: np.ndarray,
    observed_cost: float,
    minimum_cost: float,
    cost_gap: float,
    cost_efficiency: float,
    solver_objective: float | None,
    self_in_reference: bool,
    tolerance: float,
) -> _CostAccountCertificate:
    """Certify targets and value identities without another optimization."""

    raw_lambdas = np.asarray(lambdas, dtype=np.float64)
    reported_inputs = np.asarray(target_inputs, dtype=np.float64)
    reported_outputs = np.asarray(target_outputs, dtype=np.float64)
    reported_observed_inputs = np.asarray(observed_inputs, dtype=np.float64)
    prices = np.asarray(input_prices, dtype=np.float64)
    required_outputs = np.asarray(output_commitment, dtype=np.float64)

    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        reconstructed_inputs = np.asarray(
            reference.inputs @ raw_lambdas,
            dtype=np.float64,
        ).reshape(-1)
        reconstructed_outputs = np.asarray(
            reference.outputs @ raw_lambdas,
            dtype=np.float64,
        ).reshape(-1)
        price_reconstruction = float(prices @ reported_inputs)
        observed_cost_reconstruction = float(prices @ reported_observed_inputs)
        expected_gap = float(observed_cost - minimum_cost)
        expected_efficiency = float(minimum_cost / observed_cost)

    target_input_residual = scaled_array_residual(
        reported_inputs,
        reconstructed_inputs,
    )
    target_output_residual = scaled_array_residual(
        reported_outputs,
        reconstructed_outputs,
    )
    observed_cost_residual = scaled_residual(
        observed_cost,
        observed_cost_reconstruction,
    )
    minimum_cost_residual = scaled_residual(
        minimum_cost,
        price_reconstruction,
    )
    solver_objective_residual = scaled_residual(
        minimum_cost,
        math.nan if solver_objective is None else float(solver_objective),
    )
    output_commitment_violation = scaled_lower_violation(
        reported_outputs,
        required_outputs,
    )
    cost_gap_residual = scaled_residual(cost_gap, expected_gap)
    cost_efficiency_residual = scaled_residual(
        cost_efficiency,
        expected_efficiency,
    )
    minimum_cost_nonnegative = scaled_nonnegative_violation(minimum_cost)
    if self_in_reference:
        self_minimum_upper = scaled_upper_violation(
            np.asarray([minimum_cost]),
            np.asarray([observed_cost]),
        )
        self_gap_nonnegative = scaled_nonnegative_violation(cost_gap)
        self_efficiency_upper = scaled_upper_violation(
            np.asarray([cost_efficiency]),
            np.asarray([1.0]),
        )
    else:
        self_minimum_upper = 0.0
        self_gap_nonnegative = 0.0
        self_efficiency_upper = 0.0

    max_violation = maximum_violation(
        (
            target_input_residual,
            target_output_residual,
            observed_cost_residual,
            minimum_cost_residual,
            solver_objective_residual,
            output_commitment_violation,
            cost_gap_residual,
            cost_efficiency_residual,
            minimum_cost_nonnegative,
            self_minimum_upper,
            self_gap_nonnegative,
            self_efficiency_upper,
        )
    )
    certified = bool(math.isfinite(max_violation) and max_violation <= 10.0 * tolerance)
    return _CostAccountCertificate(
        certified=certified,
        reason="certified" if certified else "cost_account_reconstruction_failed",
        target_input_reconstruction_residual=target_input_residual,
        target_output_reconstruction_residual=target_output_residual,
        observed_cost_residual=observed_cost_residual,
        minimum_cost_reconstruction_residual=minimum_cost_residual,
        solver_objective_reconstruction_residual=solver_objective_residual,
        output_commitment_violation=output_commitment_violation,
        cost_gap_identity_residual=cost_gap_residual,
        cost_efficiency_identity_residual=cost_efficiency_residual,
        minimum_cost_nonnegative_violation=minimum_cost_nonnegative,
        self_minimum_cost_upper_violation=self_minimum_upper,
        self_cost_gap_nonnegative_violation=self_gap_nonnegative,
        self_cost_efficiency_upper_violation=self_efficiency_upper,
        max_violation=max_violation,
    )


def _cost_account_diagnostic_fields(
    certificate: _CostAccountCertificate,
) -> dict[str, Any]:
    """Expose stable residual names for one economic certificate."""

    return {
        "economic_postsolve_certified": certificate.certified,
        "economic_certification_reason": certificate.reason,
        "target_input_reconstruction_residual": (
            certificate.target_input_reconstruction_residual
        ),
        "target_output_reconstruction_residual": (
            certificate.target_output_reconstruction_residual
        ),
        "observed_cost_residual": certificate.observed_cost_residual,
        "minimum_cost_reconstruction_residual": (
            certificate.minimum_cost_reconstruction_residual
        ),
        "solver_objective_reconstruction_residual": (
            certificate.solver_objective_reconstruction_residual
        ),
        "scaled_output_commitment_violation": (certificate.output_commitment_violation),
        "cost_gap_identity_residual": certificate.cost_gap_identity_residual,
        "cost_efficiency_identity_residual": (
            certificate.cost_efficiency_identity_residual
        ),
        "minimum_cost_nonnegative_violation": (
            certificate.minimum_cost_nonnegative_violation
        ),
        "self_minimum_cost_upper_violation": (
            certificate.self_minimum_cost_upper_violation
        ),
        "self_cost_gap_nonnegative_violation": (
            certificate.self_cost_gap_nonnegative_violation
        ),
        "self_cost_efficiency_upper_violation": (
            certificate.self_cost_efficiency_upper_violation
        ),
        "max_economic_violation": certificate.max_violation,
    }


def _published_peer_account(
    *,
    reference: CompiledReference,
    lambdas: np.ndarray,
    target_inputs: np.ndarray,
    target_outputs: np.ndarray,
    peer_tolerance: float,
    certification_tolerance: float,
) -> tuple[np.ndarray, bool, float]:
    """Check whether displayed peers still reconstruct certified targets."""

    published = np.asarray(lambdas, dtype=np.float64).copy()
    published[published <= peer_tolerance] = 0.0
    with np.errstate(over="ignore", invalid="ignore"):
        peer_inputs = np.asarray(reference.inputs @ published).reshape(-1)
        peer_outputs = np.asarray(reference.outputs @ published).reshape(-1)
    max_violation = maximum_violation(
        (
            scaled_array_residual(peer_inputs, target_inputs),
            scaled_array_residual(peer_outputs, target_outputs),
        )
    )
    certified = bool(
        math.isfinite(max_violation) and max_violation <= 10.0 * certification_tolerance
    )
    return published, certified, max_violation


class CostEfficiency:
    """Minimum-cost efficiency for a required output commitment.

    The model selects an activity in the declared empirical technology that
    can deliver the evaluated observation's desirable outputs at minimum
    expenditure under its own supplied input prices.
    """

    _registry_method_id = "economic.cost"

    def __init__(
        self,
        *,
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.CRS,
        reference: ReferenceSpec | str | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.returns_to_scale = parse_enum(
            returns_to_scale, ReturnsToScale, "returns_to_scale"
        )
        if self.returns_to_scale not in {
            ReturnsToScale.CRS,
            ReturnsToScale.VRS,
        }:
            raise ModelSpecificationError(
                "CostEfficiency currently supports only CRS and VRS; "
                "restricted-returns economic models require a separate "
                "validated specification"
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
        if tolerance <= 0:
            raise ValueError("tolerance must be positive")
        self.tolerance = float(tolerance)
        self.peer_tolerance = (
            self.tolerance if peer_tolerance is None else float(peer_tolerance)
        )
        if self.peer_tolerance <= 0:
            raise ValueError("peer_tolerance must be positive")

    def _validate_data(self, data: DEAData) -> None:
        data.ensure_nonnegative()
        if data.bad_outputs is not None:
            raise ModelSpecificationError(
                "CostEfficiency does not infer an environmental production "
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
        return compile_economic_template(
            reference,
            self.returns_to_scale,
            -reference.outputs,
        )

    def _problem(
        self,
        template: EconomicLPTemplate,
        objective: np.ndarray,
        output_commitment: np.ndarray,
        name: str,
    ) -> LinearProgram:
        return template.problem(
            objective=objective,
            quantity_rhs=-output_commitment,
            name=f"{name}:cost",
        )

    def _dual_rows(
        self,
        data: DEAData,
        observation: int,
        solution: LPSolution,
    ) -> list[dict[str, Any]]:
        period = None if data.periods is None else data.periods[observation]
        common = {
            "dmu_id": data.dmu_ids[observation],
            "period": period,
            "source": "model_derived",
            "value_type": "shadow_value",
        }
        rows: list[dict[str, Any]] = []
        if solution.inequality_marginals is not None:
            for output, solver_marginal in zip(
                data.output_names,
                solution.inequality_marginals[: data.n_outputs],
                strict=True,
            ):
                rows.append(
                    {
                        **common,
                        "constraint_role": "output_commitment",
                        "variable": output,
                        "solver_marginal": float(solver_marginal),
                        "economic_marginal": float(-solver_marginal),
                    }
                )
        if (
            self.returns_to_scale is ReturnsToScale.VRS
            and solution.equality_marginals is not None
        ):
            rows.append(
                {
                    **common,
                    "constraint_role": "convexity",
                    "variable": "sum_lambda",
                    "solver_marginal": float(solution.equality_marginals[0]),
                    "economic_marginal": np.nan,
                }
            )
        return rows

    def fit(self, data: DEAData, prices: PriceData) -> DEAResult:
        """Estimate observed and minimum costs for every observation."""
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
        resolved: ResolvedPrices = prices.resolve(data, require_inputs=True)
        assert resolved.input_prices is not None
        input_prices = resolved.input_prices
        observed_costs = np.einsum("ij,ij->i", input_prices, data.inputs)
        if np.any(observed_costs <= resolved.spec.denominator_tolerance):
            positions = np.flatnonzero(
                observed_costs <= resolved.spec.denominator_tolerance
            )[:5].tolist()
            raise DataValidationError(
                "observed input cost must exceed the price denominator "
                f"tolerance; invalid row positions include {positions}"
            )

        reference_plan = build_reference_plan(data, self.reference)
        compiled = {} if compiled_references is None else compiled_references
        templates: dict[int, EconomicLPTemplate] = {}
        objective_cache: dict[tuple[int, bytes], np.ndarray] = {}
        solver_calls = 0

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
            y_o = data.outputs[observation]
            price_key = np.ascontiguousarray(w_o, dtype=np.float64).tobytes()
            objective_key = (set_id, price_key)
            objective = objective_cache.get(objective_key)
            if objective is None:
                objective = np.asarray(reference.inputs.T @ w_o).reshape(-1)
                objective.setflags(write=False)
                objective_cache[objective_key] = objective
            problem = self._problem(template, objective, y_o, name)
            solution = self.solver.solve(problem)
            solver_calls += 1
            lp_certificate = certify_lp_solution(
                problem,
                solution,
                tolerance=self.tolerance,
            )

            diagnostic = {
                "dmu_id": dmu_id,
                "period": period,
                "phase": 1,
                "solver_status": solution.status.value,
                "backend_solver_status": solution.status.value,
                "raw_solver_status": solution.status.value,
                "message": solution.message,
                "iterations": solution.iterations,
                "max_primal_violation": solution.max_primal_violation,
                "solver_objective": solution.objective,
                "raw_solver_objective": solution.objective,
                "reconstructed_objective": np.nan,
                "raw_minimum_cost": np.nan,
                "raw_cost_gap": np.nan,
                "raw_cost_efficiency": np.nan,
                "objective_reconstruction_residual": np.nan,
                "maximum_output_commitment_violation": np.nan,
                "target_input_reconstruction_residual": math.inf,
                "target_output_reconstruction_residual": math.inf,
                "observed_cost_residual": math.inf,
                "minimum_cost_reconstruction_residual": math.inf,
                "solver_objective_reconstruction_residual": math.inf,
                "scaled_output_commitment_violation": math.inf,
                "cost_gap_identity_residual": math.inf,
                "cost_efficiency_identity_residual": math.inf,
                "minimum_cost_nonnegative_violation": math.inf,
                "self_minimum_cost_upper_violation": math.inf,
                "self_cost_gap_nonnegative_violation": math.inf,
                "self_cost_efficiency_upper_violation": math.inf,
                "peer_valid": False,
                "published_peer_account_certified": False,
                "published_peer_certification_reason": (
                    "not_checked_uncertified_source_program"
                ),
                "max_published_peer_account_violation": math.inf,
                "published_dual_account_certified": False,
                "published_dual_row_count": 0,
                **lp_diagnostic_fields(lp_certificate),
            }

            observed_cost = float(observed_costs[observation])
            self_in_reference = bool(observation in reference.rows)
            summary_common = {
                "dmu_id": dmu_id,
                "period": period,
                "distance": np.nan,
                "is_efficient": pd.NA,
                "solver_status": solution.status.value,
                "model_family": "cost",
                "returns_to_scale": self.returns_to_scale.value,
                "reference_size": reference.size,
                "self_in_reference": self_in_reference,
                "observed_cost": observed_cost,
                "score_direction": "higher_is_better",
            }
            if not lp_certificate.certified:
                diagnostic_rows.append(diagnostic)
                summary_rows.append(
                    {
                        **summary_common,
                        "score": np.nan,
                        "efficiency": np.nan,
                        "score_valid": False,
                        "score_status": (
                            "solver_failed"
                            if solution.status is not SolverStatus.OPTIMAL
                            else "unavailable_uncertified_source_program"
                        ),
                        "is_cost_efficient": pd.NA,
                        "minimum_cost": np.nan,
                        "cost_gap": np.nan,
                        "cost_efficiency": np.nan,
                        "lp_postsolve_certified": False,
                        "postsolve_certified": False,
                        "economic_postsolve_certified": False,
                        "lp_certification_reason": lp_certificate.reason,
                        "certification_reason": lp_certificate.reason,
                        "economic_certification_reason": diagnostic[
                            "economic_certification_reason"
                        ],
                        "max_economic_violation": math.inf,
                        "target_valid": False,
                        "target_status": (
                            "solver_failed"
                            if solution.status is not SolverStatus.OPTIMAL
                            else "unavailable_uncertified_source_program"
                        ),
                        "peer_valid": False,
                        "peer_status": (
                            "solver_failed"
                            if solution.status is not SolverStatus.OPTIMAL
                            else "unavailable_uncertified_source_program"
                        ),
                        "published_peer_account_certified": False,
                        "max_published_peer_account_violation": math.inf,
                        "dual_valid": False,
                        "dual_status": (
                            "solver_failed"
                            if solution.status is not SolverStatus.OPTIMAL
                            else "unavailable_uncertified_source_program"
                        ),
                    }
                )
                continue

            assert solution.primal is not None
            lambdas = np.asarray(solution.primal, dtype=np.float64)
            target_inputs = np.asarray(reference.inputs @ lambdas).reshape(-1)
            target_outputs = np.asarray(reference.outputs @ lambdas).reshape(-1)
            minimum_cost = float(w_o @ target_inputs)
            cost_gap = observed_cost - minimum_cost
            cost_efficiency = minimum_cost / observed_cost
            is_cost_efficient: bool | Any = (
                bool(abs(cost_efficiency - 1.0) <= self.tolerance)
                if self_in_reference
                else pd.NA
            )
            objective_residual = (
                np.nan
                if solution.objective is None
                else minimum_cost - float(solution.objective)
            )
            output_violation = float(
                np.maximum(y_o - target_outputs, 0.0).max(initial=0.0)
            )
            cost_certificate = _certify_cost_account(
                reference=reference,
                lambdas=lambdas,
                target_inputs=target_inputs,
                target_outputs=target_outputs,
                observed_inputs=data.inputs[observation],
                input_prices=w_o,
                output_commitment=y_o,
                observed_cost=observed_cost,
                minimum_cost=minimum_cost,
                cost_gap=cost_gap,
                cost_efficiency=cost_efficiency,
                solver_objective=solution.objective,
                self_in_reference=self_in_reference,
                tolerance=self.tolerance,
            )
            diagnostic.update(
                {
                    "reconstructed_objective": minimum_cost,
                    "raw_minimum_cost": minimum_cost,
                    "raw_cost_gap": cost_gap,
                    "raw_cost_efficiency": cost_efficiency,
                    "objective_reconstruction_residual": objective_residual,
                    "maximum_output_commitment_violation": output_violation,
                    **_cost_account_diagnostic_fields(cost_certificate),
                    "postsolve_certified": cost_certificate.certified,
                    "certification_reason": cost_certificate.reason,
                }
            )
            if not cost_certificate.certified:
                diagnostic_rows.append(diagnostic)
                summary_rows.append(
                    {
                        **summary_common,
                        "score": np.nan,
                        "efficiency": np.nan,
                        "score_valid": False,
                        "score_status": "unavailable_uncertified_cost_account",
                        "is_cost_efficient": pd.NA,
                        "minimum_cost": np.nan,
                        "cost_gap": np.nan,
                        "cost_efficiency": np.nan,
                        "lp_postsolve_certified": True,
                        "postsolve_certified": False,
                        "economic_postsolve_certified": False,
                        "lp_certification_reason": lp_certificate.reason,
                        "certification_reason": cost_certificate.reason,
                        "economic_certification_reason": cost_certificate.reason,
                        "max_economic_violation": cost_certificate.max_violation,
                        "target_valid": False,
                        "target_status": "unavailable_uncertified_cost_account",
                        "peer_valid": False,
                        "peer_status": "unavailable_uncertified_cost_account",
                        "published_peer_account_certified": False,
                        "max_published_peer_account_violation": math.inf,
                        "dual_valid": False,
                        "dual_status": "unavailable_uncertified_cost_account",
                    }
                )
                continue

            published_lambdas, peer_valid, peer_violation = _published_peer_account(
                reference=reference,
                lambdas=lambdas,
                target_inputs=target_inputs,
                target_outputs=target_outputs,
                peer_tolerance=self.peer_tolerance,
                certification_tolerance=self.tolerance,
            )
            diagnostic.update(
                {
                    "peer_valid": peer_valid,
                    "published_peer_account_certified": peer_valid,
                    "published_peer_certification_reason": (
                        "certified"
                        if peer_valid
                        else "thresholded_peer_target_reconstruction_failed"
                    ),
                    "max_published_peer_account_violation": peer_violation,
                }
            )
            candidate_dual_rows = self._dual_rows(data, observation, solution)
            expected_dual_rows = data.n_outputs + int(
                self.returns_to_scale is ReturnsToScale.VRS
            )
            dual_valid = len(candidate_dual_rows) == expected_dual_rows
            diagnostic.update(
                {
                    "published_dual_account_certified": dual_valid,
                    "published_dual_row_count": len(candidate_dual_rows),
                }
            )
            diagnostic_rows.append(diagnostic)

            if dual_valid:
                dual_rows.extend(candidate_dual_rows)

            for local_position, intensity in enumerate(published_lambdas):
                if peer_valid and intensity > 0.0:
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
                            "lambda": float(intensity),
                            "selection_status": "solver_selected_primary_optimum",
                        }
                    )

            for role, names, observed, targets in (
                ("input", data.input_names, data.inputs[observation], target_inputs),
                ("output", data.output_names, y_o, target_outputs),
            ):
                for variable, value, target in zip(
                    names, observed, targets, strict=True
                ):
                    target_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "role": role,
                            "variable": variable,
                            "observed": float(value),
                            "target": float(target),
                            "target_kind": "cost_minimizing_activity",
                            "selection_status": "solver_selected_primary_optimum",
                        }
                    )

            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "score": cost_efficiency,
                    "efficiency": cost_efficiency,
                    "score_valid": True,
                    "score_status": "defined",
                    "distance": np.nan,
                    "is_efficient": pd.NA,
                    "is_cost_efficient": is_cost_efficient,
                    "solver_status": SolverStatus.OPTIMAL.value,
                    "model_family": "cost",
                    "returns_to_scale": self.returns_to_scale.value,
                    "reference_size": reference.size,
                    "self_in_reference": self_in_reference,
                    "observed_cost": observed_cost,
                    "minimum_cost": minimum_cost,
                    "cost_gap": cost_gap,
                    "cost_efficiency": cost_efficiency,
                    "score_direction": "higher_is_better",
                    "lp_postsolve_certified": True,
                    "postsolve_certified": True,
                    "economic_postsolve_certified": True,
                    "lp_certification_reason": lp_certificate.reason,
                    "certification_reason": "certified",
                    "economic_certification_reason": cost_certificate.reason,
                    "max_economic_violation": cost_certificate.max_violation,
                    "target_valid": True,
                    "target_status": "certified",
                    "peer_valid": peer_valid,
                    "peer_status": (
                        "certified"
                        if peer_valid
                        else "unavailable_after_peer_reporting_threshold"
                    ),
                    "published_peer_account_certified": peer_valid,
                    "max_published_peer_account_violation": peer_violation,
                    "dual_valid": dual_valid,
                    "dual_status": (
                        "certified"
                        if dual_valid
                        else "unavailable_incomplete_dual_account"
                    ),
                }
            )

        price_metadata = dict(prices.metadata(side="input"))
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
                            "purpose": "minimum_cost_for_output_commitment",
                            "sample": "panel" if data.is_panel else "cross_section",
                        },
                        "graph": {"kind": "black_box"},
                        "data_roles": {
                            "inputs": "priced_controllable_resources",
                            "outputs": "fixed_desirable_commitments",
                            "bad_outputs": "excluded",
                            **data_role_schema(data),
                        },
                        "technology": {
                            "family": "convex_envelopment",
                            "returns_to_scale": self.returns_to_scale.value,
                            "disposal": "ordinary_free",
                        },
                        "estimator": {
                            "estimator_id": "estimator.full.dea",
                            "kind": "full_frontier",
                            "family": "dea_envelopment",
                        },
                        "reference": registry_reference_spec(
                            self.reference, reference_plan.kind
                        ),
                        "performance": {
                            "family": "economic_value",
                            "measure": "cost_efficiency",
                            "orientation": "input_choice_for_fixed_output",
                            "score_direction": "higher_is_better",
                        },
                        "valuation": {
                            "kind": "supplied_input_prices",
                            **price_metadata,
                        },
                        "evaluation_protocol": {
                            "kind": "self_appraisal",
                            "target_uniqueness": "unknown",
                            "self_in_reference": reference_self_coverage(
                                reference_plan.rows_by_observation
                            ),
                        },
                        "analysis": {"kind": "direct_model_fit"},
                        "uncertainty": {"kind": "deterministic"},
                    },
                ),
                "model_family": "cost",
                "returns_to_scale": self.returns_to_scale.value,
                "reference_kind": reference_plan.kind.value,
                "native_score": "cost_efficiency",
                "score_direction": "higher_is_better",
                "target_kind": "cost_minimizing_activity",
                "target_uniqueness": "unknown",
                "postsolve_certificate": {
                    "kind": "solver_neutral_lp_and_cost_account",
                    "lp_checks": (
                        "primal_rows",
                        "variable_bounds",
                        "objective_reconstruction",
                        "dual_feasibility",
                        "complementarity",
                        "strong_duality",
                    ),
                    "economic_checks": (
                        "raw_lambda_target_reconstruction",
                        "observed_cost_reconstruction",
                        "price_objective_reconstruction",
                        "output_commitment",
                        "cost_gap_identity",
                        "cost_efficiency_ratio_identity",
                        "self_reference_cost_bound",
                    ),
                    "release_policy": (
                        "score_targets_duals_and_classification_require_lp_and_"
                        "economic_certificates"
                    ),
                    "semantic_tables": (
                        "targets",
                        "intensities",
                        "duals",
                    ),
                    "target_peer_account": (
                        "targets_use_unthresholded_certified_intensities_and_"
                        "reported_peers_are_rechecked_after_thresholding"
                    ),
                    "peer_release_policy": (
                        "thresholded_peer_failure_withholds_only_intensities"
                    ),
                    "dual_release_policy": (
                        "complete_expected_published_dual_account_required"
                    ),
                    "published_account_policy": (
                        "certified_raw_monetary_values_are_not_postprocessed"
                    ),
                    "external_reference_policy": (
                        "ratio_is_defined_without_clipping_and_efficiency_"
                        "classification_is_withheld"
                    ),
                    "failure_scope": "per_observation",
                    "additional_solver_calls": 0,
                },
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "compiled_reference_sets": reference_plan.unique_reference_sets,
                "cached_objective_vectors": len(objective_cache),
                "solver_calls": solver_calls,
                "additional_solver_calls": 0,
            },
        )


__all__ = ["CostEfficiency"]
