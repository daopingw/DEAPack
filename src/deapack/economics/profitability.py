"""Return-to-dollar profitability efficiency on a convex DEA technology."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from .._registry import data_role_schema, registry_metadata
from .._registry import reference_spec as registry_reference_spec
from ..data import DEAData
from ..enums import ReturnsToScale, SolverStatus, parse_enum
from ..exceptions import DataValidationError, ModelSpecificationError
from ..results import DEAResult
from ..specs import ReferenceSpec
from ..technology import build_reference_plan
from ._lp import reference_self_coverage
from .prices import PriceData, ResolvedPrices


@dataclass(frozen=True, slots=True)
class _RatioBenchmark:
    """Cached maximum-profitability calculation for one reference and price set."""

    reference_costs: np.ndarray
    reference_revenues: np.ndarray
    reference_profitabilities: np.ndarray
    maximum_profitability: float
    selected_local_position: int
    maximizer_count: int


class ReturnToDollarEfficiency:
    """Revenue-per-unit-cost efficiency under supplied input and output prices.

    For strictly positive reference costs, a profitability ratio over a convex
    combination is a cost-weighted average of the reference activities' own
    ratios. The maximum is therefore attained by a reference activity with the
    largest output revenue per unit of input expenditure. The implementation
    uses this exact reduction instead of a nonlinear solver.
    """

    _registry_method_id = "economic.profitability.return_to_dollar"

    def __init__(
        self,
        *,
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.CRS,
        reference: ReferenceSpec | str | None = None,
        tolerance: float = 1e-7,
    ) -> None:
        self.returns_to_scale = parse_enum(
            returns_to_scale,
            ReturnsToScale,
            "returns_to_scale",
        )
        if self.returns_to_scale not in {
            ReturnsToScale.CRS,
            ReturnsToScale.VRS,
        }:
            raise ModelSpecificationError(
                "ReturnToDollarEfficiency supports only CRS and VRS. "
                "Restricted-returns and bounded-scale fractional technologies "
                "require separately validated methods."
            )
        self.reference = (
            ReferenceSpec()
            if reference is None
            else reference
            if isinstance(reference, ReferenceSpec)
            else ReferenceSpec(kind=reference)
        )
        if not np.isfinite(tolerance) or tolerance <= 0:
            raise ValueError("tolerance must be a positive finite number")
        self.tolerance = float(tolerance)

    def _validate_data(self, data: DEAData) -> None:
        data.ensure_nonnegative()
        if data.bad_outputs is not None:
            raise ModelSpecificationError(
                "ReturnToDollarEfficiency does not infer environmental "
                "profitability from undesirable outputs. Use a separately "
                "registered environmental-economic model."
            )
        if np.any(data.inputs.sum(axis=1) <= 0):
            raise DataValidationError(
                "each observation needs at least one strictly positive input; "
                "zero-cost activities make return-to-dollar undefined or unbounded"
            )
        if np.any(data.outputs.sum(axis=1) <= 0):
            raise DataValidationError(
                "each observation needs at least one strictly positive desirable "
                "output for the source-qualified return-to-dollar model"
            )

    @staticmethod
    def _price_key(values: np.ndarray) -> bytes:
        return np.ascontiguousarray(values, dtype=np.dtype("<f8")).tobytes()

    def _benchmark(
        self,
        data: DEAData,
        reference_rows: np.ndarray,
        input_prices: np.ndarray,
        output_prices: np.ndarray,
        denominator_tolerance: float,
        dmu_id: object,
    ) -> _RatioBenchmark:
        with np.errstate(over="ignore", invalid="ignore"):
            reference_costs = np.asarray(
                data.inputs[reference_rows] @ input_prices,
                dtype=np.float64,
            )
            reference_revenues = np.asarray(
                data.outputs[reference_rows] @ output_prices,
                dtype=np.float64,
            )
        finite = np.isfinite(reference_costs) & np.isfinite(reference_revenues)
        positive = (reference_costs > denominator_tolerance) & (
            reference_revenues > denominator_tolerance
        )
        valid = finite & positive
        if not valid.all():
            local_positions = np.flatnonzero(~valid)[:5]
            row_positions = reference_rows[local_positions].tolist()
            raise DataValidationError(
                "every profitability candidate must have finite input cost and "
                "output revenue above the price denominator tolerance under the "
                f"evaluated prices; evaluated DMU={dmu_id!r}, invalid reference "
                f"row positions include {row_positions}"
            )

        reference_profitabilities = reference_revenues / reference_costs
        selected_local_position = int(np.argmax(reference_profitabilities))
        maximum_profitability = float(
            reference_profitabilities[selected_local_position]
        )
        maximizers = np.isclose(
            reference_profitabilities,
            maximum_profitability,
            rtol=self.tolerance,
            atol=self.tolerance,
        )
        for values in (
            reference_costs,
            reference_revenues,
            reference_profitabilities,
        ):
            values.setflags(write=False)
        return _RatioBenchmark(
            reference_costs=reference_costs,
            reference_revenues=reference_revenues,
            reference_profitabilities=reference_profitabilities,
            maximum_profitability=maximum_profitability,
            selected_local_position=selected_local_position,
            maximizer_count=int(maximizers.sum()),
        )

    def fit(self, data: DEAData, prices: PriceData) -> DEAResult:
        """Estimate observed, maximum, and relative profitability."""
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
        finite = np.isfinite(observed_costs) & np.isfinite(observed_revenues)
        positive = (observed_costs > resolved.spec.denominator_tolerance) & (
            observed_revenues > resolved.spec.denominator_tolerance
        )
        valid = finite & positive
        if not valid.all():
            positions = np.flatnonzero(~valid)[:5].tolist()
            raise DataValidationError(
                "observed input cost and output revenue must be finite and exceed "
                "the price denominator tolerance; invalid row positions include "
                f"{positions}"
            )
        observed_profitabilities = observed_revenues / observed_costs

        reference_plan = build_reference_plan(data, self.reference)
        task_keys = tuple(
            (
                reference_plan.set_id_for(observation),
                self._price_key(input_prices[observation]),
                self._price_key(output_prices[observation]),
            )
            for observation in range(data.n_dmus)
        )
        task_counts = Counter(task_keys)
        cache: dict[tuple[int, bytes, bytes], _RatioBenchmark] = {}
        ratio_kernel_calls = 0
        summary_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []

        for observation, task_key in enumerate(task_keys):
            reference_rows = reference_plan.rows_for(observation)
            dmu_id = data.dmu_ids[observation]
            period = None if data.periods is None else data.periods[observation]
            w_o = input_prices[observation]
            p_o = output_prices[observation]
            benchmark = cache.get(task_key)
            solution_reused = benchmark is not None
            if benchmark is None:
                ratio_kernel_calls += 1
                benchmark = self._benchmark(
                    data,
                    reference_rows,
                    w_o,
                    p_o,
                    resolved.spec.denominator_tolerance,
                    dmu_id,
                )
                if task_counts[task_key] > 1:
                    cache[task_key] = benchmark

            selected_local = benchmark.selected_local_position
            selected_position = int(reference_rows[selected_local])
            selected_cost = float(benchmark.reference_costs[selected_local])
            selected_revenue = float(benchmark.reference_revenues[selected_local])
            maximum_profitability = benchmark.maximum_profitability
            observed_cost = float(observed_costs[observation])
            observed_revenue = float(observed_revenues[observation])
            observed_profitability = float(observed_profitabilities[observation])
            profitability_efficiency = observed_profitability / maximum_profitability
            self_in_reference = bool(observation in reference_rows)

            if abs(profitability_efficiency - 1.0) <= self.tolerance:
                profitability_efficiency = 1.0
            profitability_gap = maximum_profitability - observed_profitability
            if abs(profitability_gap) <= self.tolerance:
                profitability_gap = 0.0

            invalid_self_appraisal = bool(
                self_in_reference and profitability_efficiency > 1.0 + self.tolerance
            )
            if invalid_self_appraisal:
                score = np.nan
                efficiency = np.nan
                is_profitability_efficient: bool | Any = pd.NA
                is_efficient: bool | Any = pd.NA
                score_status = "invalid_above_one_under_self_appraisal"
            elif self_in_reference:
                score = profitability_efficiency
                efficiency = profitability_efficiency
                is_profitability_efficient = bool(profitability_efficiency == 1.0)
                is_efficient = True if is_profitability_efficient else pd.NA
                score_status = "defined_self_appraisal"
            else:
                score = profitability_efficiency
                efficiency = profitability_efficiency
                is_profitability_efficient = pd.NA
                is_efficient = pd.NA
                score_status = "defined_external_comparison"

            if self.returns_to_scale is ReturnsToScale.CRS:
                selected_intensity = observed_cost / selected_cost
                target_scale_policy = "observed_cost"
            else:
                selected_intensity = 1.0
                target_scale_policy = "vrs_reference_plan"
            transform_scale = 1.0 / (selected_cost * selected_intensity)
            transformed_intensity = transform_scale * selected_intensity
            target_inputs = data.inputs[selected_position] * selected_intensity
            target_outputs = data.outputs[selected_position] * selected_intensity
            target_cost = float(w_o @ target_inputs)
            target_revenue = float(p_o @ target_outputs)
            target_profitability = target_revenue / target_cost
            target_uniqueness = (
                "nonunique_reference_ratio_maximizer"
                if benchmark.maximizer_count > 1
                else (
                    "scale_nonunique_single_ratio_maximizer"
                    if self.returns_to_scale is ReturnsToScale.CRS
                    else "unique_reference_ratio_maximizer"
                )
            )

            intensity_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "reference_dmu_id": data.dmu_ids[selected_position],
                    "reference_period": (
                        None
                        if data.periods is None
                        else data.periods[selected_position]
                    ),
                    "lambda": float(selected_intensity),
                    "transformed_intensity": float(transformed_intensity),
                    "transform_scale": float(transform_scale),
                    "is_selected_maximizer": True,
                    "maximizer_count": benchmark.maximizer_count,
                    "target_kind": "profitability_maximizing_activity",
                }
            )

            for role, names, observed, targets in (
                (
                    "input",
                    data.input_names,
                    data.inputs[observation],
                    target_inputs,
                ),
                (
                    "output",
                    data.output_names,
                    data.outputs[observation],
                    target_outputs,
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
                            "target_kind": "profitability_maximizing_activity",
                            "target_scale_policy": target_scale_policy,
                        }
                    )

            diagnostic_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "phase": 1,
                    "solver_status": SolverStatus.OPTIMAL.value,
                    "message": "exact extreme-reference-ratio reduction",
                    "iterations": 0,
                    "max_primal_violation": 0.0,
                    "algorithm": "closed_form_extreme_ratio",
                    "solution_reused": solution_reused,
                    "candidate_count": len(reference_rows),
                    "maximizer_count": benchmark.maximizer_count,
                    "selected_reference_position": selected_position,
                    "selected_reference_dmu_id": data.dmu_ids[selected_position],
                    "selected_reference_cost": selected_cost,
                    "selected_reference_revenue": selected_revenue,
                    "selected_reference_profitability": target_profitability,
                    "ratio_reconstruction_residual": (
                        target_profitability - maximum_profitability
                    ),
                    "transform_scale": transform_scale,
                    "target_scale_policy": target_scale_policy,
                    "target_uniqueness": target_uniqueness,
                    "self_in_reference": self_in_reference,
                }
            )

            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "score": score,
                    "efficiency": efficiency,
                    "distance": np.nan,
                    "is_efficient": is_efficient,
                    "is_profitability_efficient": is_profitability_efficient,
                    "solver_status": SolverStatus.OPTIMAL.value,
                    "model_family": "profitability",
                    "returns_to_scale": self.returns_to_scale.value,
                    "reference_size": len(reference_rows),
                    "self_in_reference": self_in_reference,
                    "observed_cost": observed_cost,
                    "observed_revenue": observed_revenue,
                    "return_to_dollar": observed_profitability,
                    "observed_profitability": observed_profitability,
                    "maximum_profitability": maximum_profitability,
                    "profitability_gap": profitability_gap,
                    "profitability_efficiency": profitability_efficiency,
                    "target_cost": target_cost,
                    "target_revenue": target_revenue,
                    "target_profitability": target_profitability,
                    "transform_scale": transform_scale,
                    "maximizer_count": benchmark.maximizer_count,
                    "target_scale_policy": target_scale_policy,
                    "target_uniqueness": target_uniqueness,
                    "score_direction": "higher_is_better",
                    "score_status": score_status,
                }
            )

        price_metadata = dict(prices.metadata())
        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
            targets=pd.DataFrame(target_rows),
            intensities=pd.DataFrame(intensity_rows),
            diagnostics=pd.DataFrame(diagnostic_rows),
            metadata={
                **registry_metadata(
                    self._registry_method_id,
                    {
                        "context": {
                            "purpose": "maximum_output_value_per_unit_expenditure",
                            "sample": "panel" if data.is_panel else "cross_section",
                        },
                        "graph": {"kind": "black_box"},
                        "data_roles": {
                            "inputs": "priced_resource_expenditure",
                            "outputs": "priced_desirable_output_value",
                            "bad_outputs": "excluded",
                            **data_role_schema(data),
                        },
                        "technology": {
                            "family": "convex_envelopment",
                            "returns_to_scale": self.returns_to_scale.value,
                            "disposal": "ordinary_free",
                            "shutdown_option": "excluded_undefined_zero_over_zero",
                            "ratio_value_invariance": "crs_equals_vrs",
                        },
                        "estimator": {
                            "estimator_id": "estimator.full.dea",
                            "kind": "full_frontier",
                            "family": "dea_extreme_ratio",
                            "algorithm": "closed_form_extreme_ratio",
                        },
                        "reference": registry_reference_spec(
                            self.reference,
                            reference_plan.kind,
                        ),
                        "performance": {
                            "family": "economic_ratio",
                            "measure": "profitability_efficiency",
                            "observed_measure": "revenue_over_input_cost",
                            "score_direction": "higher_is_better",
                            "profit_ratio": "not_used",
                            "orientation": "not_applicable",
                        },
                        "valuation": {
                            "kind": "supplied_input_and_output_prices",
                            **price_metadata,
                        },
                        "evaluation_protocol": {
                            "kind": "self_appraisal",
                            "target_uniqueness": "reported_per_observation",
                            "target_selection": ("first_maximizer_by_reference_order"),
                            "self_in_reference": reference_self_coverage(
                                reference_plan.rows_by_observation
                            ),
                            "external_reference_score_policy": (
                                "retain_unclipped_benchmark_relative_ratio"
                            ),
                        },
                        "analysis": {"kind": "direct_model_fit"},
                        "uncertainty": {"kind": "deterministic"},
                    },
                ),
                "model_family": "profitability",
                "returns_to_scale": self.returns_to_scale.value,
                "reference_kind": reference_plan.kind.value,
                "native_score": "profitability_efficiency",
                "score_direction": "higher_is_better",
                "observed_measure": "return_to_dollar",
                "algorithm": "closed_form_extreme_ratio",
                "optimization_backend": "closed_form_extreme_ratio",
                "solver": "not_required",
                "solver_calls": 0,
                "duals_available": False,
                "duals_unavailable_reason": ("closed_form_extreme_ratio_backend"),
                "target_kind": "profitability_maximizing_activity",
                "target_scale_policy": (
                    "observed_cost"
                    if self.returns_to_scale is ReturnsToScale.CRS
                    else "vrs_reference_plan"
                ),
                "target_selection": "first_maximizer_by_reference_order",
                "rts_value_invariant_crs_vrs": True,
                "external_reference_score_policy": (
                    "retain_unclipped_benchmark_relative_ratio"
                ),
                "tolerance": self.tolerance,
                "compiled_reference_sets": reference_plan.unique_reference_sets,
                "cached_ratio_benchmarks": len(cache),
                "ratio_kernel_calls": ratio_kernel_calls,
                "ratio_cache_policy": "retain_reused_tasks_only",
            },
        )


# Profitability and return-to-dollar are exact aliases for this ratio model.
ProfitabilityEfficiency = ReturnToDollarEfficiency


__all__ = ["ProfitabilityEfficiency", "ReturnToDollarEfficiency"]
