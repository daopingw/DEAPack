"""Nerlovian profit inefficiency and its directional decomposition."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .._registry import (
    data_role_schema,
    direction_spec,
    registry_metadata,
)
from .._registry import reference_spec as registry_reference_spec
from ..data import DEAData
from ..enums import ReturnsToScale, SolverStatus, parse_enum
from ..exceptions import DataValidationError, ModelSpecificationError
from ..models._common import CompiledReference
from ..models.directional import (
    DirectionalDistanceDEA,
    DirectionInput,
    _resolve_direction,
)
from ..results import DEAResult
from ..solvers import LPSolver, SciPyHiGHSSolver
from ..specs import ReferenceSpec, SolverOptions
from ..technology import build_reference_plan
from ._lp import reference_self_coverage
from .prices import PriceData, ResolvedPrices
from .profit import ProfitEfficiency


def _with_component(
    frame: pd.DataFrame,
    component: str,
    *,
    target_kind: str | None = None,
) -> pd.DataFrame:
    """Copy a result table and identify the generating component."""
    if frame.empty:
        return frame.copy()
    result = frame.copy()
    result["component"] = component
    if target_kind is not None:
        result["target_kind"] = target_kind
    return result


def _concat_frames(frames: list[pd.DataFrame]) -> pd.DataFrame:
    nonempty = [frame for frame in frames if not frame.empty]
    if not nonempty:
        return pd.DataFrame()
    return pd.concat(nonempty, ignore_index=True, sort=False)


class NerlovianProfitInefficiency:
    """Decompose a price-normalized profit shortfall using a matched DDF.

    For the package direction convention, inputs contract by ``beta * g_x``
    and desirable outputs expand by ``beta * g_y``.  The Nerlovian measure is
    the attainable profit gap divided by ``w @ g_x + p @ g_y``.  It is an
    inefficiency measure: zero is best, and larger values indicate a larger
    shortfall relative to the declared operating programme.
    """

    _registry_method_id = "economic.nerlovian.ccf1998"

    def __init__(
        self,
        *,
        input_direction: DirectionInput = "observed",
        output_direction: DirectionInput = "observed",
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.VRS,
        reference: ReferenceSpec | str | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        compute_slacks: bool = True,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.input_direction = input_direction
        self.output_direction = output_direction
        self.returns_to_scale = parse_enum(
            returns_to_scale,
            ReturnsToScale,
            "returns_to_scale",
        )
        if self.returns_to_scale is not ReturnsToScale.VRS:
            raise ModelSpecificationError(
                "NerlovianProfitInefficiency currently supports only VRS. "
                "The profit component can be unbounded under CRS, while "
                "alternative shutdown and scale policies change the matched "
                "technology and require separate validation."
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
        self.compute_slacks = bool(compute_slacks)
        if not np.isfinite(tolerance) or tolerance <= 0:
            raise ValueError("tolerance must be a positive finite number")
        self.tolerance = float(tolerance)
        self.peer_tolerance = (
            self.tolerance if peer_tolerance is None else float(peer_tolerance)
        )
        if not np.isfinite(self.peer_tolerance) or self.peer_tolerance <= 0:
            raise ValueError("peer_tolerance must be a positive finite number")

    def fit(self, data: DEAData, prices: PriceData) -> DEAResult:
        """Estimate Nerlovian, technical, and allocative inefficiency."""
        if not isinstance(prices, PriceData):
            raise TypeError("prices must be a PriceData instance")

        # Resolve the directions and their economic value before optimizing.
        # ProfitEfficiency and DirectionalDistanceDEA repeat their own public
        # validation so their standalone contracts remain independently safe.
        resolved: ResolvedPrices = prices.resolve(
            data,
            require_inputs=True,
            require_outputs=True,
        )
        assert resolved.input_prices is not None
        assert resolved.output_prices is not None
        input_directions, input_direction_kind = _resolve_direction(
            self.input_direction,
            data.inputs,
            data.input_names,
            "input",
        )
        output_directions, output_direction_kind = _resolve_direction(
            self.output_direction,
            data.outputs,
            data.output_names,
            "output",
        )
        zero_direction = (
            input_directions.sum(axis=1) + output_directions.sum(axis=1)
        ) <= 0
        if zero_direction.any():
            positions = np.flatnonzero(zero_direction)[:5].tolist()
            raise ModelSpecificationError(
                "each evaluated observation needs at least one positive direction "
                f"component; zero-direction row positions include {positions}"
            )

        with np.errstate(over="ignore", invalid="ignore"):
            direction_values = np.einsum(
                "ij,ij->i",
                resolved.input_prices,
                input_directions,
            ) + np.einsum(
                "ij,ij->i",
                resolved.output_prices,
                output_directions,
            )
        invalid_direction_value = ~np.isfinite(direction_values) | (
            direction_values <= resolved.spec.denominator_tolerance
        )
        if invalid_direction_value.any():
            positions = np.flatnonzero(invalid_direction_value)[:5].tolist()
            raise DataValidationError(
                "the economic value of each direction must be finite and exceed "
                "PriceSpec.denominator_tolerance; invalid row positions include "
                f"{positions}"
            )

        reference_plan = build_reference_plan(data, self.reference)
        compiled_references: dict[int, CompiledReference] = {}
        profit_model = ProfitEfficiency(
            returns_to_scale=self.returns_to_scale,
            reference=self.reference,
            solver=self.solver,
            tolerance=self.tolerance,
            peer_tolerance=self.peer_tolerance,
        )
        directional_model = DirectionalDistanceDEA(
            input_direction=self.input_direction,
            output_direction=self.output_direction,
            returns_to_scale=self.returns_to_scale,
            reference=self.reference,
            solver=self.solver,
            compute_slacks=self.compute_slacks,
            allow_negative_distance=False,
            tolerance=self.tolerance,
            peer_tolerance=self.peer_tolerance,
        )
        profit = profit_model._fit(
            data,
            prices,
            compiled_references=compiled_references,
        )
        directional = directional_model._fit(
            data,
            compiled_references=compiled_references,
        )

        profit_summary = profit.summary(copy=False).reset_index(drop=True)
        directional_summary = directional.summary(copy=False).reset_index(drop=True)
        if not (len(profit_summary) == len(directional_summary) == data.n_dmus):
            raise RuntimeError("internal Nerlovian component rows are not aligned")

        summary_rows: list[dict[str, Any]] = []
        direct_target_rows: list[dict[str, Any]] = []
        decomposition_diagnostic_rows: list[dict[str, Any]] = []
        directional_target_kind_by_row: list[str] = []

        for observation in range(data.n_dmus):
            profit_row = profit_summary.iloc[observation]
            directional_row = directional_summary.iloc[observation]
            phase_one_status = str(directional_row["primary_solver_status"])
            direction_value = float(direction_values[observation])
            profit_gap = float(profit_row["profit_gap"])
            beta = float(directional_row["distance"])
            profit_backend_optimal = (
                profit_row["solver_status"] == SolverStatus.OPTIMAL.value
            )
            profit_score_valid = bool(profit_row.get("score_valid", False))
            profit_optimal = bool(
                profit_backend_optimal
                and profit_score_valid
                and np.isfinite(profit_gap)
            )
            directional_score_valid = bool(directional_row.get("score_valid", False))
            directional_score_status = str(
                directional_row.get("score_status", "validity_not_reported")
            )
            directional_optimal = bool(
                phase_one_status == SolverStatus.OPTIMAL.value
                and directional_score_valid
                and np.isfinite(beta)
            )
            membership_certified = bool(
                directional_optimal
                and directional_row.get("is_within_reference_technology", False)
            )

            if not profit_optimal:
                nerlovian = np.nan
                allocative = np.nan
                decomposition_defined = False
                score_status = (
                    "profit_solver_failure"
                    if not profit_backend_optimal
                    else "unavailable_profit_score_certificate"
                )
                solver_status = str(profit_row["solver_status"])
            elif not directional_optimal:
                nerlovian = np.nan
                allocative = np.nan
                decomposition_defined = False
                score_status = (
                    "directional_solver_failure"
                    if phase_one_status != SolverStatus.OPTIMAL.value
                    else "unavailable_directional_score_certificate"
                )
                solver_status = phase_one_status
            elif not membership_certified:
                nerlovian = np.nan
                allocative = np.nan
                decomposition_defined = False
                score_status = "outside_reference_technology"
                solver_status = phase_one_status
            else:
                nerlovian = profit_gap / direction_value
                if abs(nerlovian) <= self.tolerance:
                    nerlovian = 0.0
                allocative = nerlovian - beta
                if abs(allocative) <= self.tolerance:
                    allocative = 0.0
                decomposition_defined = bool(allocative >= 0.0)
                score_status = (
                    "defined"
                    if decomposition_defined
                    else "invalid_negative_allocative_residual"
                )
                solver_status = SolverStatus.OPTIMAL.value

            if decomposition_defined:
                score = nerlovian
                technical = beta
                is_nerlovian_efficient: bool | Any = bool(nerlovian == 0.0)
                is_directionally_efficient = directional_row[
                    "is_directionally_efficient"
                ]
                if pd.notna(directional_row["is_efficient"]):
                    is_efficient: bool | Any = bool(directional_row["is_efficient"])
                elif is_nerlovian_efficient:
                    # Strictly positive input/output prices plus a feasible
                    # profit maximum rule out Pareto dominance.
                    is_efficient = True
                else:
                    is_efficient = pd.NA
                reconstruction_residual = nerlovian - technical - allocative
            else:
                score = np.nan
                technical = beta if directional_optimal else np.nan
                is_nerlovian_efficient = pd.NA
                is_directionally_efficient = (
                    directional_row["is_directionally_efficient"]
                    if directional_optimal
                    else pd.NA
                )
                is_efficient = pd.NA
                reconstruction_residual = np.nan

            max_slack = float(directional_row["max_slack"])
            if not self.compute_slacks:
                slack_status = "not_checked"
                directional_target_kind = "directional_programme"
            elif not bool(directional_row.get("completion_valid", False)):
                slack_status = "completion_solver_failure"
                directional_target_kind = "directional_programme"
            elif np.isfinite(max_slack) and max_slack <= self.tolerance:
                slack_status = "no_residual_slacks"
                directional_target_kind = "directional_slack_completed_activity"
            else:
                slack_status = "residual_slacks_present"
                directional_target_kind = "directional_slack_completed_activity"
            directional_target_kind_by_row.append(directional_target_kind)

            dmu_id = data.dmu_ids[observation]
            period = None if data.periods is None else data.periods[observation]
            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "score": score,
                    "score_valid": decomposition_defined,
                    "efficiency": np.nan,
                    "distance": score,
                    "is_efficient": is_efficient,
                    "is_profit_efficient": profit_row["is_profit_efficient"],
                    "is_nerlovian_efficient": is_nerlovian_efficient,
                    "is_directionally_efficient": is_directionally_efficient,
                    "solver_status": solver_status,
                    "profit_solver_status": profit_row["solver_status"],
                    "profit_score_valid": profit_score_valid,
                    "profit_score_status": profit_row["score_status"],
                    "directional_solver_status": phase_one_status,
                    "directional_score_valid": directional_score_valid,
                    "directional_score_status": directional_score_status,
                    "directional_completion_valid": directional_row.get(
                        "completion_valid",
                        pd.NA,
                    ),
                    "directional_completion_status": directional_row.get(
                        "completion_status",
                        "validity_not_reported",
                    ),
                    "directional_target_valid": directional_row.get(
                        "target_valid",
                        pd.NA,
                    ),
                    "directional_peer_valid": directional_row.get(
                        "peer_valid",
                        False,
                    ),
                    "directional_dual_valid": directional_row.get(
                        "dual_valid",
                        False,
                    ),
                    "model_family": "nerlovian_profit_inefficiency",
                    "returns_to_scale": self.returns_to_scale.value,
                    "reference_size": int(profit_row["reference_size"]),
                    "self_in_reference": bool(profit_row["self_in_reference"]),
                    "observed_cost": float(profit_row["observed_cost"]),
                    "observed_revenue": float(profit_row["observed_revenue"]),
                    "observed_profit": float(profit_row["observed_profit"]),
                    "maximum_profit": float(profit_row["maximum_profit"]),
                    "profit_gap": profit_gap,
                    "direction_value": direction_value,
                    "nerlovian_inefficiency": nerlovian,
                    "technical_inefficiency": technical,
                    "allocative_inefficiency": allocative,
                    "decomposition_defined": decomposition_defined,
                    "decomposition_slack_status": slack_status,
                    "max_slack": max_slack,
                    "reconstruction_residual": reconstruction_residual,
                    "score_direction": "lower_is_better",
                    "score_status": score_status,
                }
            )
            decomposition_diagnostic_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "component": "decomposition",
                    "phase": "identity",
                    "solver_status": solver_status,
                    "message": score_status,
                    "iterations": pd.NA,
                    "max_primal_violation": np.nan,
                    "direction_value": direction_value,
                    "profit_score_valid": profit_score_valid,
                    "profit_score_status": profit_row["score_status"],
                    "directional_score_valid": directional_score_valid,
                    "directional_score_status": directional_score_status,
                    "membership_certified": membership_certified,
                    "decomposition_defined": decomposition_defined,
                    "reconstruction_residual": reconstruction_residual,
                    "decomposition_slack_status": slack_status,
                }
            )

            if directional_optimal:
                for role, names, observed, directions, signs in (
                    (
                        "input",
                        data.input_names,
                        data.inputs[observation],
                        input_directions[observation],
                        -1.0,
                    ),
                    (
                        "output",
                        data.output_names,
                        data.outputs[observation],
                        output_directions[observation],
                        1.0,
                    ),
                ):
                    for variable, value, direction in zip(
                        names,
                        observed,
                        directions,
                        strict=True,
                    ):
                        direct_target_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": period,
                                "role": role,
                                "variable": variable,
                                "observed": float(value),
                                "target": float(value + signs * beta * direction),
                                "direction": float(direction),
                                "directional_change": float(beta * direction),
                                "target_kind": "directional_programme",
                                "component": "directional",
                            }
                        )

        target_kind_keys = pd.DataFrame(
            {
                "dmu_id": data.dmu_ids,
                "period": (
                    [None] * data.n_dmus if data.periods is None else data.periods
                ),
                "target_kind": directional_target_kind_by_row,
            }
        )
        directional_targets = directional.targets.copy()
        if not directional_targets.empty:
            directional_targets = directional_targets.merge(
                target_kind_keys,
                on=["dmu_id", "period"],
                how="left",
                validate="many_to_one",
            )
            directional_targets["component"] = "directional"

        profit_targets = _with_component(profit.targets, "profit")
        profit_intensities = _with_component(profit.intensities, "profit")
        directional_intensities = directional.intensities.copy()
        if not directional_intensities.empty:
            directional_intensities = directional_intensities.merge(
                target_kind_keys,
                on=["dmu_id", "period"],
                how="left",
                validate="many_to_one",
            )
            directional_intensities["component"] = "directional"

        directional_slacks = directional.slacks.copy()
        if not directional_slacks.empty:
            directional_slacks = directional_slacks.merge(
                target_kind_keys,
                on=["dmu_id", "period"],
                how="left",
                validate="many_to_one",
            )
            directional_slacks["component"] = "directional"

        profit_diagnostics = _with_component(profit.diagnostics, "profit")
        directional_diagnostics = _with_component(
            directional.diagnostics,
            "directional",
        )
        price_metadata = dict(prices.metadata())
        direction_scope = (
            "common"
            if input_direction_kind in {"ones", "mean", "custom_global", "zeros"}
            and output_direction_kind in {"ones", "mean", "custom_global", "zeros"}
            else "by_observation"
        )
        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
            slacks=directional_slacks,
            targets=_concat_frames(
                [
                    profit_targets,
                    pd.DataFrame(direct_target_rows),
                    directional_targets,
                ]
            ),
            intensities=_concat_frames([profit_intensities, directional_intensities]),
            duals=_concat_frames(
                [
                    _with_component(profit.duals, "profit"),
                    _with_component(directional.duals, "directional"),
                ]
            ),
            diagnostics=_concat_frames(
                [
                    profit_diagnostics,
                    directional_diagnostics,
                    pd.DataFrame(decomposition_diagnostic_rows),
                ]
            ),
            metadata={
                **registry_metadata(
                    self._registry_method_id,
                    {
                        "context": {
                            "purpose": "explain_foregone_profit",
                            "sample": "panel" if data.is_panel else "cross_section",
                        },
                        "graph": {"kind": "black_box"},
                        "data_roles": {
                            "inputs": "priced_resources_to_contract",
                            "outputs": "priced_services_to_expand",
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
                            "family": "nerlovian_profit_inefficiency",
                            "measure": "normalized_profit_gap",
                            "technical_measure": "directional_distance",
                            "input_direction": direction_spec(
                                input_direction_kind,
                                input_directions,
                                data.input_names,
                            ),
                            "output_direction": direction_spec(
                                output_direction_kind,
                                output_directions,
                                data.output_names,
                            ),
                            "normalizer": "input_price_value_plus_output_price_value",
                            "score_direction": "lower_is_better",
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
                            "secondary_objective": (
                                "maximize_unweighted_directional_slacks"
                                if self.compute_slacks
                                else "none"
                            ),
                        },
                        "analysis": {
                            "kind": "additive_decomposition",
                            "identity": (
                                "nerlovian_inefficiency="
                                "technical_inefficiency+allocative_inefficiency"
                            ),
                        },
                        "uncertainty": {"kind": "deterministic"},
                    },
                ),
                "model_family": "nerlovian_profit_inefficiency",
                "returns_to_scale": self.returns_to_scale.value,
                "reference_kind": reference_plan.kind.value,
                "native_score": "nerlovian_inefficiency",
                "score_direction": "lower_is_better",
                "efficiency_ratio": "not_defined",
                "decomposition_identity": (
                    "nerlovian_inefficiency="
                    "technical_inefficiency+allocative_inefficiency"
                ),
                "input_direction": input_direction_kind,
                "output_direction": output_direction_kind,
                "direction_scope": direction_scope,
                "cross_observation_comparability": (
                    "conditional_on_common_economic_units_and_direction"
                ),
                "compute_slacks": self.compute_slacks,
                "target_kinds": (
                    "profit_maximizing_activity",
                    "directional_programme",
                    "directional_slack_completed_activity",
                ),
                "finite_value_policy": "vrs_simplex",
                "shutdown_option": "excluded_under_vrs_convex_hull",
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "compiled_reference_sets": reference_plan.unique_reference_sets,
                "shared_compiled_reference_sets": len(compiled_references),
                "profit_solver_calls": profit.metadata["solver_calls"],
                "directional_solver_calls": directional.metadata["solver_calls"],
                "additional_solver_calls": 0,
                "postsolve_certificate": {
                    "profit_component": (
                        "requires_profit_score_valid_and_certified_price_account"
                    ),
                    "directional_component": (
                        "requires_directional_score_valid_and_certified_membership"
                    ),
                    "decomposition_account": (
                        "nerlovian_equals_technical_plus_allocative"
                    ),
                    "failure_scope": "per_observation",
                    "additional_solver_calls": 0,
                },
            },
        )


NerlovianEfficiency = NerlovianProfitInefficiency
"""Discoverability alias for :class:`NerlovianProfitInefficiency`."""


__all__ = ["NerlovianEfficiency", "NerlovianProfitInefficiency"]
