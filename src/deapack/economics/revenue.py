"""Revenue efficiency on the shared convex DEA technology."""

from __future__ import annotations

import math
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


def _revenue_account_residuals(
    *,
    reference: CompiledReference,
    returns_to_scale: ReturnsToScale,
    x_o: np.ndarray,
    y_o: np.ndarray,
    p_o: np.ndarray,
    lambdas: np.ndarray,
    target_inputs: np.ndarray,
    target_outputs: np.ndarray,
    observed_revenue: float,
    maximum_revenue: float,
    revenue_gap: float,
    revenue_expansion_ratio: float,
    revenue_efficiency: float,
    denominator_valid: bool,
    denominator_tolerance: float,
    self_in_reference: bool,
    solver_objective: float,
) -> dict[str, float]:
    """Reconstruct one maximum-revenue account from the raw LP incumbent."""

    represented_inputs = np.asarray(reference.inputs @ lambdas).reshape(-1)
    represented_outputs = np.asarray(reference.outputs @ lambdas).reshape(-1)
    expected_observed_revenue = float(p_o @ y_o)
    expected_maximum_revenue = float(p_o @ target_outputs)
    expected_gap = maximum_revenue - observed_revenue
    expected_expansion = maximum_revenue / observed_revenue
    expected_denominator_valid = maximum_revenue > denominator_tolerance
    expected_efficiency = (
        observed_revenue / maximum_revenue if expected_denominator_valid else math.nan
    )
    if returns_to_scale is ReturnsToScale.VRS:
        returns_to_scale_residual = scaled_residual(float(lambdas.sum()), 1.0)
    else:
        returns_to_scale_residual = 0.0

    efficiency_residual = (
        scaled_residual(revenue_efficiency, expected_efficiency)
        if expected_denominator_valid
        else 0.0
        if math.isnan(revenue_efficiency)
        else math.inf
    )
    reciprocal_residual = (
        scaled_residual(
            revenue_efficiency * revenue_expansion_ratio,
            1.0,
        )
        if expected_denominator_valid
        else 0.0
    )
    self_appraisal_bound_residual = (
        scaled_lower_violation(
            np.asarray([maximum_revenue]),
            np.asarray([observed_revenue]),
        )
        if self_in_reference
        else 0.0
    )
    self_efficiency_bound_residual = (
        scaled_upper_violation(
            np.asarray([revenue_efficiency]),
            np.asarray([1.0]),
        )
        if self_in_reference and expected_denominator_valid
        else 0.0
    )
    denominator_classification_residual = (
        0.0 if denominator_valid is expected_denominator_valid else math.inf
    )
    return {
        "lambda_nonnegative_violation": scaled_lower_violation(
            lambdas,
            np.zeros_like(lambdas),
        ),
        "target_input_reconstruction_residual": scaled_array_residual(
            target_inputs,
            represented_inputs,
        ),
        "target_output_reconstruction_residual": scaled_array_residual(
            target_outputs,
            represented_outputs,
        ),
        "target_input_nonnegative_violation": scaled_lower_violation(
            target_inputs,
            np.zeros_like(target_inputs),
        ),
        "target_output_nonnegative_violation": scaled_lower_violation(
            target_outputs,
            np.zeros_like(target_outputs),
        ),
        "input_capacity_residual": scaled_upper_violation(target_inputs, x_o),
        "returns_to_scale_residual": returns_to_scale_residual,
        "observed_revenue_residual": scaled_residual(
            observed_revenue,
            expected_observed_revenue,
        ),
        "maximum_revenue_residual": scaled_residual(
            maximum_revenue,
            expected_maximum_revenue,
        ),
        "objective_revenue_residual": scaled_residual(
            solver_objective,
            -maximum_revenue,
        ),
        "revenue_gap_residual": scaled_residual(revenue_gap, expected_gap),
        "revenue_expansion_residual": scaled_residual(
            revenue_expansion_ratio,
            expected_expansion,
        ),
        "revenue_efficiency_residual": efficiency_residual,
        "reciprocal_identity_residual": reciprocal_residual,
        "maximum_revenue_nonnegative_violation": scaled_nonnegative_violation(
            maximum_revenue
        ),
        "denominator_classification_residual": (denominator_classification_residual),
        "self_appraisal_bound_residual": self_appraisal_bound_residual,
        "self_efficiency_bound_residual": self_efficiency_bound_residual,
    }


def _revenue_economic_postsolve_violation(**kwargs: Any) -> float:
    """Return the largest independently reconstructed revenue-account residual."""

    return maximum_violation(_revenue_account_residuals(**kwargs).values())


def _revenue_peer_postsolve_violation(
    *,
    reference: CompiledReference,
    returns_to_scale: ReturnsToScale,
    lambdas: np.ndarray,
    target_inputs: np.ndarray,
    target_outputs: np.ndarray,
) -> float:
    """Check that thresholded, reported peers reproduce certified targets."""

    represented_inputs = np.asarray(reference.inputs @ lambdas).reshape(-1)
    represented_outputs = np.asarray(reference.outputs @ lambdas).reshape(-1)
    returns_to_scale_residual = (
        scaled_residual(float(lambdas.sum()), 1.0)
        if returns_to_scale is ReturnsToScale.VRS
        else 0.0
    )
    return maximum_violation(
        (
            scaled_lower_violation(lambdas, np.zeros_like(lambdas)),
            scaled_array_residual(represented_inputs, target_inputs),
            scaled_array_residual(represented_outputs, target_outputs),
            returns_to_scale_residual,
        )
    )


def _undefined_revenue_summary(
    *,
    dmu_id: object,
    period: object | None,
    returns_to_scale: ReturnsToScale,
    reference_size: int,
    self_in_reference: bool,
    observed_revenue: float,
    solver_status: SolverStatus,
    lp_postsolve_certified: bool,
    lp_certification_reason: str,
    certification_reason: str,
    economic_certification_reason: str,
    max_economic_violation: float,
    score_status: str,
) -> dict[str, Any]:
    """Withhold all derived claims from one uncertified revenue programme."""

    return {
        "dmu_id": dmu_id,
        "period": period,
        "score": np.nan,
        "efficiency": np.nan,
        "score_valid": False,
        "score_status": score_status,
        "distance": np.nan,
        "is_efficient": pd.NA,
        "is_revenue_efficient": pd.NA,
        "solver_status": solver_status.value,
        "model_family": "revenue",
        "returns_to_scale": returns_to_scale.value,
        "reference_size": reference_size,
        "self_in_reference": self_in_reference,
        "observed_revenue": observed_revenue,
        "maximum_revenue": np.nan,
        "revenue_gap": np.nan,
        "revenue_expansion_ratio": np.nan,
        "revenue_efficiency": np.nan,
        "score_direction": "higher_is_better",
        "lp_postsolve_certified": lp_postsolve_certified,
        "postsolve_certified": False,
        "economic_postsolve_certified": False,
        "lp_certification_reason": lp_certification_reason,
        "certification_reason": certification_reason,
        "economic_certification_reason": economic_certification_reason,
        "max_economic_violation": max_economic_violation,
        "target_valid": False,
        "target_status": score_status,
        "peer_valid": False,
        "peer_status": score_status,
        "dual_valid": False,
        "dual_status": score_status,
    }


class RevenueEfficiency:
    """Maximum-revenue efficiency for a fixed input capacity.

    The model selects an activity in the declared empirical technology that
    respects the evaluated observation's input capacity and maximizes output
    value under its own supplied output prices.
    """

    _registry_method_id = "economic.revenue"

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
        if self.returns_to_scale not in {
            ReturnsToScale.CRS,
            ReturnsToScale.VRS,
        }:
            raise ModelSpecificationError(
                "RevenueEfficiency currently supports only CRS and VRS; "
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
                "RevenueEfficiency does not infer an environmental production "
                "technology for undesirable outputs. Use a separately "
                "registered environmental-economic model."
            )
        if np.any(data.inputs.sum(axis=1) <= 0):
            raise DataValidationError(
                "each observation needs at least one strictly positive input; "
                "this also excludes positive-value zero-input production rays"
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
            reference.inputs,
        )

    def _problem(
        self,
        template: EconomicLPTemplate,
        objective: np.ndarray,
        input_capacity: np.ndarray,
        name: str,
    ) -> LinearProgram:
        return template.problem(
            objective=objective,
            quantity_rhs=input_capacity,
            name=f"{name}:revenue",
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
            for input_name, solver_marginal in zip(
                data.input_names,
                solution.inequality_marginals[: data.n_inputs],
                strict=True,
            ):
                rows.append(
                    {
                        **common,
                        "constraint_role": "input_capacity",
                        "variable": input_name,
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
        """Estimate observed and maximum revenues for every observation."""
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
        resolved: ResolvedPrices = prices.resolve(data, require_outputs=True)
        assert resolved.output_prices is not None
        output_prices = resolved.output_prices
        observed_revenues = np.einsum("ij,ij->i", output_prices, data.outputs)
        if np.any(observed_revenues <= resolved.spec.denominator_tolerance):
            positions = np.flatnonzero(
                observed_revenues <= resolved.spec.denominator_tolerance
            )[:5].tolist()
            raise DataValidationError(
                "observed output revenue must exceed the price denominator "
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
            p_o = output_prices[observation]
            x_o = data.inputs[observation]
            price_key = np.ascontiguousarray(p_o, dtype=np.float64).tobytes()
            objective_key = (set_id, price_key)
            objective = objective_cache.get(objective_key)
            if objective is None:
                objective = -np.asarray(reference.outputs.T @ p_o).reshape(-1)
                objective.setflags(write=False)
                objective_cache[objective_key] = objective
            problem = self._problem(template, objective, x_o, name)
            solution = self.solver.solve(problem)
            solver_calls += 1
            certificate = certify_lp_solution(
                problem,
                solution,
                tolerance=self.tolerance,
            )

            diagnostic = {
                "dmu_id": dmu_id,
                "period": period,
                "phase": 1,
                "solver_status": solution.status.value,
                "message": solution.message,
                "iterations": solution.iterations,
                "max_primal_violation": solution.max_primal_violation,
                "solver_objective": solution.objective,
                "reconstructed_objective": np.nan,
                "objective_reconstruction_residual": np.nan,
                "maximum_input_capacity_violation": np.nan,
                "maximum_revenue_denominator_valid": pd.NA,
                "raw_maximum_revenue": np.nan,
                "raw_revenue_gap": np.nan,
                "raw_revenue_expansion_ratio": np.nan,
                "raw_revenue_efficiency": np.nan,
                "published_peer_account_certified": pd.NA,
                "max_published_peer_account_violation": np.nan,
                "published_dual_account_certified": pd.NA,
                "published_dual_row_count": np.nan,
                **lp_diagnostic_fields(certificate),
            }

            observed_revenue = float(observed_revenues[observation])
            self_in_reference = bool(observation in reference.rows)

            raw_lambdas: np.ndarray | None = None
            raw_target_inputs: np.ndarray | None = None
            raw_target_outputs: np.ndarray | None = None
            raw_maximum_revenue = math.nan
            raw_revenue_gap = math.nan
            raw_revenue_expansion_ratio = math.nan
            raw_denominator_valid: bool | Any = pd.NA
            raw_revenue_efficiency = math.nan
            if solution.primal is not None:
                candidate = np.asarray(solution.primal, dtype=np.float64)
                if (
                    candidate.shape == (reference.size,)
                    and np.isfinite(candidate).all()
                ):
                    raw_lambdas = candidate
                    raw_target_inputs = np.asarray(
                        reference.inputs @ raw_lambdas
                    ).reshape(-1)
                    raw_target_outputs = np.asarray(
                        reference.outputs @ raw_lambdas
                    ).reshape(-1)
                    raw_maximum_revenue = float(p_o @ raw_target_outputs)
                    raw_revenue_gap = raw_maximum_revenue - observed_revenue
                    raw_revenue_expansion_ratio = raw_maximum_revenue / observed_revenue
                    raw_denominator_valid = bool(
                        raw_maximum_revenue > resolved.spec.denominator_tolerance
                    )
                    raw_revenue_efficiency = (
                        observed_revenue / raw_maximum_revenue
                        if raw_denominator_valid
                        else math.nan
                    )
                    diagnostic.update(
                        {
                            "reconstructed_objective": raw_maximum_revenue,
                            "objective_reconstruction_residual": (
                                np.nan
                                if solution.objective is None
                                else raw_maximum_revenue + float(solution.objective)
                            ),
                            "maximum_input_capacity_violation": float(
                                np.maximum(
                                    raw_target_inputs - x_o,
                                    0.0,
                                ).max(initial=0.0)
                            ),
                            "maximum_revenue_denominator_valid": (
                                raw_denominator_valid
                            ),
                            "raw_maximum_revenue": raw_maximum_revenue,
                            "raw_revenue_gap": raw_revenue_gap,
                            "raw_revenue_expansion_ratio": (
                                raw_revenue_expansion_ratio
                            ),
                            "raw_revenue_efficiency": raw_revenue_efficiency,
                        }
                    )

            if not certificate.certified:
                diagnostic_rows.append(diagnostic)
                summary_rows.append(
                    _undefined_revenue_summary(
                        dmu_id=dmu_id,
                        period=period,
                        returns_to_scale=self.returns_to_scale,
                        reference_size=reference.size,
                        self_in_reference=self_in_reference,
                        observed_revenue=observed_revenue,
                        solver_status=solution.status,
                        lp_postsolve_certified=False,
                        lp_certification_reason=certificate.reason,
                        certification_reason=certificate.reason,
                        economic_certification_reason=diagnostic[
                            "economic_certification_reason"
                        ],
                        max_economic_violation=float(
                            diagnostic["max_economic_violation"]
                        ),
                        score_status=(
                            "solver_failed"
                            if solution.status is not SolverStatus.OPTIMAL
                            else "unavailable_uncertified_source_program"
                        ),
                    )
                )
                continue

            assert raw_lambdas is not None
            assert raw_target_inputs is not None
            assert raw_target_outputs is not None
            assert solution.objective is not None
            assert isinstance(raw_denominator_valid, bool)
            account_kwargs = {
                "reference": reference,
                "returns_to_scale": self.returns_to_scale,
                "x_o": x_o,
                "y_o": data.outputs[observation],
                "p_o": p_o,
                "lambdas": raw_lambdas,
                "target_inputs": raw_target_inputs,
                "target_outputs": raw_target_outputs,
                "observed_revenue": observed_revenue,
                "maximum_revenue": raw_maximum_revenue,
                "revenue_gap": raw_revenue_gap,
                "revenue_expansion_ratio": raw_revenue_expansion_ratio,
                "revenue_efficiency": raw_revenue_efficiency,
                "denominator_valid": raw_denominator_valid,
                "denominator_tolerance": resolved.spec.denominator_tolerance,
                "self_in_reference": self_in_reference,
                "solver_objective": float(solution.objective),
            }
            account_residuals = _revenue_account_residuals(**account_kwargs)
            max_economic_violation = _revenue_economic_postsolve_violation(
                **account_kwargs
            )
            economic_certified = bool(
                math.isfinite(max_economic_violation)
                and max_economic_violation <= 10.0 * self.tolerance
            )
            diagnostic.update(account_residuals)
            diagnostic.update(
                {
                    "economic_postsolve_certified": economic_certified,
                    "economic_certification_reason": (
                        "certified"
                        if economic_certified
                        else "revenue_account_reconstruction_failed"
                    ),
                    "max_economic_violation": max_economic_violation,
                    "postsolve_certified": economic_certified,
                    "certification_reason": (
                        "certified"
                        if economic_certified
                        else "revenue_account_reconstruction_failed"
                    ),
                }
            )
            if not economic_certified:
                diagnostic_rows.append(diagnostic)
                summary_rows.append(
                    _undefined_revenue_summary(
                        dmu_id=dmu_id,
                        period=period,
                        returns_to_scale=self.returns_to_scale,
                        reference_size=reference.size,
                        self_in_reference=self_in_reference,
                        observed_revenue=observed_revenue,
                        solver_status=solution.status,
                        lp_postsolve_certified=True,
                        lp_certification_reason=certificate.reason,
                        certification_reason=diagnostic["certification_reason"],
                        economic_certification_reason=diagnostic[
                            "economic_certification_reason"
                        ],
                        max_economic_violation=float(
                            diagnostic["max_economic_violation"]
                        ),
                        score_status=("unavailable_uncertified_revenue_account"),
                    )
                )
                continue

            # Publish the same raw monetary account that was certified above.
            # Independent display clean-up would break the public value and
            # ratio identities while leaving the certificate marked valid.
            maximum_revenue = raw_maximum_revenue
            revenue_gap = raw_revenue_gap
            revenue_expansion_ratio = raw_revenue_expansion_ratio
            revenue_efficiency = raw_revenue_efficiency
            denominator_valid = raw_denominator_valid
            is_revenue_efficient: bool | Any = (
                bool(abs(revenue_efficiency - 1.0) <= self.tolerance)
                if denominator_valid and self_in_reference
                else pd.NA
            )
            peer_lambdas = raw_lambdas.copy()
            peer_lambdas[peer_lambdas <= self.peer_tolerance] = 0.0
            peer_violation = _revenue_peer_postsolve_violation(
                reference=reference,
                returns_to_scale=self.returns_to_scale,
                lambdas=peer_lambdas,
                target_inputs=raw_target_inputs,
                target_outputs=raw_target_outputs,
            )
            peer_valid = bool(
                math.isfinite(peer_violation)
                and peer_violation <= 10.0 * self.tolerance
            )
            candidate_dual_rows = self._dual_rows(data, observation, solution)
            expected_dual_rows = data.n_inputs + int(
                self.returns_to_scale is ReturnsToScale.VRS
            )
            dual_valid = len(candidate_dual_rows) == expected_dual_rows
            diagnostic.update(
                {
                    "published_peer_account_certified": peer_valid,
                    "max_published_peer_account_violation": peer_violation,
                    "published_dual_account_certified": dual_valid,
                    "published_dual_row_count": len(candidate_dual_rows),
                }
            )
            diagnostic_rows.append(diagnostic)

            if peer_valid:
                for local_position, intensity in enumerate(peer_lambdas):
                    if intensity <= 0.0:
                        continue
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
                            "selection_status": (
                                "certified_revenue_maximizing_activity"
                            ),
                        }
                    )

            if dual_valid:
                dual_rows.extend(candidate_dual_rows)

            for role, names, observed, targets in (
                ("input", data.input_names, x_o, raw_target_inputs),
                (
                    "output",
                    data.output_names,
                    data.outputs[observation],
                    raw_target_outputs,
                ),
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
                            "target_kind": "revenue_maximizing_activity",
                            "selection_status": (
                                "certified_revenue_maximizing_activity"
                            ),
                        }
                    )

            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "score": revenue_efficiency,
                    "efficiency": revenue_efficiency,
                    "score_valid": denominator_valid,
                    "distance": np.nan,
                    "is_efficient": pd.NA,
                    "is_revenue_efficient": is_revenue_efficient,
                    "solver_status": SolverStatus.OPTIMAL.value,
                    "model_family": "revenue",
                    "returns_to_scale": self.returns_to_scale.value,
                    "reference_size": reference.size,
                    "self_in_reference": self_in_reference,
                    "observed_revenue": observed_revenue,
                    "maximum_revenue": maximum_revenue,
                    "revenue_gap": revenue_gap,
                    "revenue_expansion_ratio": revenue_expansion_ratio,
                    "revenue_efficiency": revenue_efficiency,
                    "score_direction": "higher_is_better",
                    "score_status": (
                        "defined"
                        if denominator_valid
                        else "undefined_zero_maximum_revenue"
                    ),
                    "lp_postsolve_certified": True,
                    "postsolve_certified": True,
                    "economic_postsolve_certified": True,
                    "lp_certification_reason": certificate.reason,
                    "certification_reason": "certified",
                    "economic_certification_reason": "certified",
                    "max_economic_violation": max_economic_violation,
                    "target_valid": True,
                    "target_status": "certified",
                    "peer_valid": peer_valid,
                    "peer_status": (
                        "certified"
                        if peer_valid
                        else "unavailable_after_peer_reporting_threshold"
                    ),
                    "dual_valid": dual_valid,
                    "dual_status": (
                        "certified"
                        if dual_valid
                        else "unavailable_incomplete_dual_account"
                    ),
                }
            )

        price_metadata = dict(prices.metadata(side="output"))
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
                            "purpose": "maximum_revenue_from_input_capacity",
                            "sample": "panel" if data.is_panel else "cross_section",
                        },
                        "graph": {"kind": "black_box"},
                        "data_roles": {
                            "inputs": "fixed_resource_capacity",
                            "outputs": "priced_desirable_choices",
                            "bad_outputs": "excluded",
                            **data_role_schema(data),
                        },
                        "technology": {
                            "family": "convex_envelopment",
                            "returns_to_scale": self.returns_to_scale.value,
                            "disposal": "ordinary_free",
                            "zero_input_ray_policy": (
                                "reject_zero_aggregate_input_activity"
                            ),
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
                            "measure": "revenue_efficiency",
                            "orientation": "output_choice_for_fixed_inputs",
                            "score_direction": "higher_is_better",
                            "native_expansion": "maximum_over_observed_revenue",
                        },
                        "valuation": {
                            "kind": "supplied_output_prices",
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
                "model_family": "revenue",
                "returns_to_scale": self.returns_to_scale.value,
                "reference_kind": reference_plan.kind.value,
                "native_score": "revenue_efficiency",
                "native_expansion": "revenue_expansion_ratio",
                "score_direction": "higher_is_better",
                "target_kind": "revenue_maximizing_activity",
                "target_uniqueness": "unknown",
                "postsolve_certificate": {
                    "lp": "solver_neutral_primal_dual_kkt_and_strong_duality",
                    "economic_account": (
                        "raw_intensity_targets_objective_capacity_revenue_gap_"
                        "expansion_efficiency_reciprocal_and_self_bound"
                    ),
                    "score_release_policy": (
                        "requires_certified_lp_and_revenue_account_plus_a_"
                        "strictly_positive_raw_maximum_revenue_denominator"
                    ),
                    "zero_denominator_policy": (
                        "retain_certified_maximum_gap_expansion_targets_peers_"
                        "and_duals_but_withhold_efficiency_score"
                    ),
                    "target_peer_account": (
                        "targets_use_raw_certified_intensities_and_reported_"
                        "peers_are_rechecked_after_thresholding"
                    ),
                    "dual_release_policy": (
                        "complete_expected_published_dual_account_required"
                    ),
                    "published_account_policy": (
                        "certified_raw_monetary_values_are_not_postprocessed"
                    ),
                    "semantic_tables": ("targets", "intensities", "duals"),
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


__all__ = ["RevenueEfficiency"]
