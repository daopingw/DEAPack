"""Tone--Tsutsui dynamic slacks-based measures."""

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
from ._dynamic_sbm import (
    CompiledDynamicSBMReference,
    DynamicSBMOrientation,
    compile_dynamic_sbm_reference,
    dynamic_sbm_problem,
    parse_dynamic_sbm_orientation,
)
from ._layout import CompiledDynamicSBMLayout, compile_dynamic_sbm_layout
from .data import DynamicData

DynamicSBMScoreVariant = str


def _score_variant(value: str) -> DynamicSBMScoreVariant:
    if not isinstance(value, str):
        raise TypeError("score_variant must be a string")
    normalized = value.strip().lower().replace("-", "_")
    aliases = {
        "base": "base",
        "unscored_free": "base",
        "free_adjusted_post": "free_adjusted_post",
        "adjusted": "free_adjusted_post",
        "adjusted_post": "free_adjusted_post",
    }
    try:
        return aliases[normalized]
    except KeyError as error:
        raise ValueError(
            "score_variant must be 'base' or 'free_adjusted_post'; the "
            "source free-link MIP requires a separate MILP specialization"
        ) from error


def _clean(values: np.ndarray, tolerance: float) -> np.ndarray:
    result = np.asarray(values, dtype=np.float64).copy()
    result[np.abs(result) <= tolerance] = 0.0
    return result


def _semantic_solver_status(
    backend_status: SolverStatus,
    *,
    certified: bool,
) -> SolverStatus:
    """Separate a backend termination claim from the published result status."""

    if backend_status is not SolverStatus.OPTIMAL:
        return backend_status
    return SolverStatus.OPTIMAL if certified else SolverStatus.NUMERICAL_ERROR


def _max_abs(values: np.ndarray) -> float:
    array = np.asarray(values, dtype=np.float64)
    if not np.isfinite(array).all():
        return math.inf
    return float(np.max(np.abs(array), initial=0.0))


def _original_unit_residual_account(
    residual: np.ndarray,
    scales: np.ndarray,
) -> tuple[float, float]:
    """Return raw and economically normalized residuals in original units."""

    values = np.asarray(residual, dtype=np.float64)
    variable_scales = np.asarray(scales, dtype=np.float64)
    if (
        values.shape[-1:] != variable_scales.shape
        or not np.isfinite(values).all()
        or not np.isfinite(variable_scales).all()
        or np.any(variable_scales <= 0.0)
    ):
        return math.inf, math.inf
    original = values * variable_scales
    return _max_abs(original), _max_abs(original / variable_scales)


def _scaled_scalar_violation(
    actual: object,
    expected: float,
    economic_scale: float,
) -> float:
    """Compare one published original-unit value on its economic scale."""

    try:
        numeric = float(actual)
    except (TypeError, ValueError):
        return math.inf
    if not (
        math.isfinite(numeric)
        and math.isfinite(expected)
        and math.isfinite(economic_scale)
        and economic_scale > 0.0
    ):
        return math.inf
    denominator = max(economic_scale, abs(numeric), abs(expected))
    return abs(numeric - expected) / denominator


def _named_weights(
    supplied: Mapping[Hashable, float] | None,
    labels: Sequence[Hashable],
    *,
    target_sum: float,
    field: str,
) -> tuple[np.ndarray, str]:
    ordered = tuple(labels)
    if supplied is None:
        values = np.ones(len(ordered), dtype=np.float64)
        source = "equal"
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
            if not math.isfinite(numeric) or numeric <= 0:
                raise ValueError(f"{field} values must be finite and strictly positive")
            resolved.append(numeric)
        values = np.asarray(resolved, dtype=np.float64)
        source = "user_relative_normalized"
    values *= target_sum / float(np.sum(values))
    values.setflags(write=False)
    return values, source


def _role_columns(
    layout: CompiledDynamicSBMLayout,
) -> dict[str, np.ndarray]:
    positions = {name: index for index, name in enumerate(layout.variable_names)}
    roles = {
        "input": layout.inputs,
        "nondiscretionary_input": layout.nondiscretionary_inputs,
        "output": layout.outputs,
        "nondiscretionary_output": layout.nondiscretionary_outputs,
        "good_carryover": layout.good_carryovers,
        "bad_carryover": layout.bad_carryovers,
        "free_carryover": layout.free_carryovers,
        "fixed_carryover": layout.fixed_carryovers,
    }
    return {
        role: np.asarray([positions[name] for name in names], dtype=np.int64)
        for role, names in roles.items()
    }


def _extract_slacks(
    primal: np.ndarray,
    slices: tuple[slice, ...],
    *,
    transform_scale: float,
    tolerance: float,
) -> np.ndarray:
    width = 0 if not slices else slices[0].stop - slices[0].start
    if width == 0:
        return np.empty((len(slices), 0), dtype=np.float64)
    return _clean(
        np.vstack([primal[item] for item in slices]) / transform_scale,
        tolerance,
    )


def _weighted_accounts(
    *,
    observed: np.ndarray,
    slacks: dict[str, np.ndarray],
    columns: dict[str, np.ndarray],
    period_weights: np.ndarray,
    input_weights: np.ndarray,
    output_weights: np.ndarray,
    layout: CompiledDynamicSBMLayout,
) -> dict[str, np.ndarray | float]:
    n_periods = observed.shape[0]
    input_loss = np.sum(
        input_weights[None, :] * slacks["input"] / observed[:, columns["input"]],
        axis=1,
    )
    if layout.n_bad:
        input_loss += np.sum(
            slacks["bad_carryover"] / observed[:, columns["bad_carryover"]],
            axis=1,
        )
    input_loss /= layout.input_account_dimension
    input_accounts = 1.0 - input_loss

    output_gain = np.sum(
        output_weights[None, :] * slacks["output"] / observed[:, columns["output"]],
        axis=1,
    )
    if layout.n_good:
        output_gain += np.sum(
            slacks["good_carryover"] / observed[:, columns["good_carryover"]],
            axis=1,
        )
    output_gain /= layout.output_account_dimension
    output_accounts = 1.0 + output_gain

    effective_period_weights = period_weights / n_periods
    aggregate_input = float(np.dot(effective_period_weights, input_accounts))
    aggregate_output = float(np.dot(effective_period_weights, output_accounts))
    return {
        "input_loss": input_loss,
        "input_accounts": input_accounts,
        "output_gain": output_gain,
        "output_accounts": output_accounts,
        "aggregate_input": aggregate_input,
        "aggregate_output": aggregate_output,
    }


def _efficiencies(
    *,
    orientation: DynamicSBMOrientation,
    input_accounts: np.ndarray,
    output_accounts: np.ndarray,
    aggregate_input: float,
    aggregate_output: float,
) -> tuple[float, np.ndarray]:
    if orientation == "input":
        return aggregate_input, input_accounts
    if orientation == "output":
        return 1.0 / aggregate_output, 1.0 / output_accounts
    return (
        aggregate_input / aggregate_output,
        input_accounts / output_accounts,
    )


def _accounts_support_efficiency(
    accounts: dict[str, np.ndarray | float],
    orientation: DynamicSBMOrientation,
    period_weights: np.ndarray,
    tolerance: float,
) -> bool:
    input_accounts = np.asarray(accounts["input_accounts"], dtype=np.float64)
    output_accounts = np.asarray(accounts["output_accounts"], dtype=np.float64)
    scalars = np.asarray(
        [accounts["aggregate_input"], accounts["aggregate_output"]],
        dtype=np.float64,
    )
    if (
        input_accounts.shape != period_weights.shape
        or output_accounts.shape != period_weights.shape
    ):
        return False
    if not (
        np.isfinite(input_accounts).all()
        and np.isfinite(output_accounts).all()
        and np.isfinite(scalars).all()
    ):
        return False
    if (
        np.any(input_accounts < -tolerance)
        or np.any(input_accounts > 1.0 + tolerance)
        or np.any(output_accounts < 1.0 - tolerance)
    ):
        return False
    effective_weights = period_weights / period_weights.size
    reconstructed = np.asarray(
        [
            effective_weights @ input_accounts,
            effective_weights @ output_accounts,
        ],
        dtype=np.float64,
    )
    reconstruction_scale = np.maximum(
        1.0,
        np.maximum(np.abs(scalars), np.abs(reconstructed)),
    )
    if np.any(
        np.abs(scalars - reconstructed) > 10.0 * tolerance * reconstruction_scale
    ):
        return False
    if orientation in {"output", "non-oriented"}:
        return bool(
            float(scalars[1]) > tolerance and np.all(output_accounts > tolerance)
        )
    return True


def _adjusted_accounts(
    *,
    observed: np.ndarray,
    slacks: dict[str, np.ndarray],
    columns: dict[str, np.ndarray],
    period_weights: np.ndarray,
    input_weights: np.ndarray,
    output_weights: np.ndarray,
    layout: CompiledDynamicSBMLayout,
) -> dict[str, np.ndarray | float] | None:
    if layout.n_free == 0:
        return None
    free_observed = observed[:, columns["free_carryover"]]
    free_signed = slacks["free_carryover"]
    free_excess = np.maximum(free_signed, 0.0)
    free_shortage = np.maximum(-free_signed, 0.0)

    input_loss = np.sum(
        input_weights[None, :] * slacks["input"] / observed[:, columns["input"]],
        axis=1,
    )
    if layout.n_bad:
        input_loss += np.sum(
            slacks["bad_carryover"] / observed[:, columns["bad_carryover"]],
            axis=1,
        )
    input_loss += np.sum(free_excess / free_observed, axis=1)
    input_loss /= layout.input_account_dimension + layout.n_free
    input_accounts = 1.0 - input_loss

    output_gain = np.sum(
        output_weights[None, :] * slacks["output"] / observed[:, columns["output"]],
        axis=1,
    )
    if layout.n_good:
        output_gain += np.sum(
            slacks["good_carryover"] / observed[:, columns["good_carryover"]],
            axis=1,
        )
    output_gain += np.sum(free_shortage / free_observed, axis=1)
    output_gain /= layout.output_account_dimension + layout.n_free
    output_accounts = 1.0 + output_gain

    effective_period_weights = period_weights / observed.shape[0]
    return {
        "free_excess": free_excess,
        "free_shortage": free_shortage,
        "input_accounts": input_accounts,
        "output_accounts": output_accounts,
        "aggregate_input": float(np.dot(effective_period_weights, input_accounts)),
        "aggregate_output": float(np.dot(effective_period_weights, output_accounts)),
    }


def _solver_base_efficiency(
    orientation: DynamicSBMOrientation,
    objective: float,
) -> float:
    if orientation == "output":
        expansion = -objective
        return 1.0 / expansion
    return objective


def _diagnostic(
    *,
    dmu_id: object,
    solution: LPSolution,
    certificate: LPCertificate,
) -> dict[str, Any]:
    semantic_status = _semantic_solver_status(
        solution.status,
        certified=certificate.certified,
    )
    return {
        "dmu_id": dmu_id,
        "period": None,
        "phase": "primary",
        "solver_status": semantic_status.value,
        "backend_solver_status": solution.status.value,
        "raw_solver_status": solution.status.value,
        "message": solution.message,
        "iterations": solution.iterations,
        "max_primal_violation": solution.max_primal_violation,
        "lp_postsolve_certified": certificate.certified,
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
        "score_valid": False,
        "score_status": "not_checked",
        "target_valid": False,
        "target_status": "not_available_without_certified_primary",
        "peer_valid": False,
        "peer_status": "not_available_without_certified_target",
        "dual_valid": False,
        "dual_status": "not_available_without_certified_primary",
        "carryover_valid": False,
        "carryover_status": "not_available_without_certified_primary",
        "published_dual_row_count": 0,
        "expected_dual_row_count": 0,
        "omitted_intensity_sum": np.nan,
        "max_period_omitted_intensity_sum": np.nan,
        "max_published_target_account_violation": np.nan,
        "max_published_peer_account_violation": np.nan,
        "max_published_dual_account_violation": np.nan,
        "max_published_carryover_account_violation": np.nan,
        "max_original_unit_balance_residual": np.nan,
        "max_original_unit_normalized_balance_violation": np.nan,
        "max_original_unit_continuity_residual": np.nan,
        "max_original_unit_normalized_continuity_violation": np.nan,
        "max_original_unit_fixed_residual": np.nan,
        "max_original_unit_normalized_fixed_violation": np.nan,
    }


def _dynamic_economic_postsolve_violation(
    *,
    transform_scale: float,
    base_accounts: dict[str, np.ndarray | float],
    adjusted_accounts: dict[str, np.ndarray | float] | None,
    base_efficiency: float,
    base_period_efficiencies: np.ndarray,
    reported_efficiency: float,
    reported_period_efficiencies: np.ndarray,
    solver_efficiency: float,
    optimization_residual: float,
    reconstruction_residual: float,
    max_balance_residual: float,
    max_continuity_residual: float,
    max_fixed_residual: float,
    max_original_unit_normalized_balance_violation: float,
    max_original_unit_normalized_continuity_violation: float,
    max_original_unit_normalized_fixed_violation: float,
) -> float:
    """Certify the recovered operating accounts in canonical data units."""

    input_accounts = np.asarray(base_accounts["input_accounts"], dtype=np.float64)
    output_accounts = np.asarray(base_accounts["output_accounts"], dtype=np.float64)
    finite_blocks = [
        input_accounts,
        output_accounts,
        np.asarray(base_period_efficiencies, dtype=np.float64),
        np.asarray(reported_period_efficiencies, dtype=np.float64),
        np.asarray(
            [
                transform_scale,
                float(base_accounts["aggregate_input"]),
                float(base_accounts["aggregate_output"]),
                base_efficiency,
                reported_efficiency,
                solver_efficiency,
                optimization_residual,
                reconstruction_residual,
                max_balance_residual,
                max_continuity_residual,
                max_fixed_residual,
                max_original_unit_normalized_balance_violation,
                max_original_unit_normalized_continuity_violation,
                max_original_unit_normalized_fixed_violation,
            ],
            dtype=np.float64,
        ),
    ]
    account_pairs = [(input_accounts, output_accounts)]
    if adjusted_accounts is not None:
        adjusted_inputs = np.asarray(
            adjusted_accounts["input_accounts"],
            dtype=np.float64,
        )
        adjusted_outputs = np.asarray(
            adjusted_accounts["output_accounts"],
            dtype=np.float64,
        )
        finite_blocks.extend(
            [
                adjusted_inputs,
                adjusted_outputs,
                np.asarray(
                    [
                        float(adjusted_accounts["aggregate_input"]),
                        float(adjusted_accounts["aggregate_output"]),
                    ],
                    dtype=np.float64,
                ),
            ]
        )
        account_pairs.append((adjusted_inputs, adjusted_outputs))
    if transform_scale <= 0.0 or any(
        not np.isfinite(block).all() for block in finite_blocks
    ):
        return math.inf

    violations = [
        abs(optimization_residual),
        abs(reconstruction_residual),
        abs(max_balance_residual),
        abs(max_continuity_residual),
        abs(max_fixed_residual),
        abs(max_original_unit_normalized_balance_violation),
        abs(max_original_unit_normalized_continuity_violation),
        abs(max_original_unit_normalized_fixed_violation),
    ]
    for input_values, output_values in account_pairs:
        violations.extend(
            [
                max(0.0, -float(input_values.min(initial=0.0))),
                max(0.0, float(input_values.max(initial=1.0)) - 1.0),
                max(0.0, 1.0 - float(output_values.min(initial=1.0))),
            ]
        )
    for values in (
        np.asarray([base_efficiency, reported_efficiency], dtype=np.float64),
        np.asarray(base_period_efficiencies, dtype=np.float64),
        np.asarray(reported_period_efficiencies, dtype=np.float64),
    ):
        violations.extend(
            [
                max(0.0, -float(values.min(initial=0.0))),
                max(0.0, float(values.max(initial=1.0)) - 1.0),
            ]
        )
    return float(np.asarray(violations, dtype=np.float64).max(initial=0.0))


class ToneTsutsuiDynamicSBM:
    """Estimate the source dynamic SBM over complete DMU trajectories.

    The model appraises one organization's full multi-period operating plan.
    Period-specific reference intensities are linked by exact carry-over
    continuity, so period results are conditional components of one
    horizon-wide benchmark rather than independently fitted annual scores.
    """

    _registry_method_id = "dynamic.sbm.tone_tsutsui_2010"

    def __init__(
        self,
        *,
        orientation: str = "non-oriented",
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.VRS,
        period_weights: Mapping[Hashable, float] | None = None,
        input_weights: Mapping[str, float] | None = None,
        output_weights: Mapping[str, float] | None = None,
        score_variant: str = "base",
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.orientation = parse_dynamic_sbm_orientation(orientation)
        self.returns_to_scale = parse_enum(
            returns_to_scale,
            ReturnsToScale,
            "returns_to_scale",
        )
        if self.returns_to_scale not in {
            ReturnsToScale.CRS,
            ReturnsToScale.VRS,
        }:
            raise ValueError(
                "ToneTsutsuiDynamicSBM supports the source CRS and VRS "
                "specifications only"
            )
        for supplied, field in (
            (period_weights, "period_weights"),
            (input_weights, "input_weights"),
            (output_weights, "output_weights"),
        ):
            if supplied is not None and not isinstance(supplied, Mapping):
                raise TypeError(f"{field} must be a label-to-weight mapping")
        self.period_weights = period_weights
        self.input_weights = input_weights
        self.output_weights = output_weights
        self.score_variant = _score_variant(score_variant)
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
        data: DynamicData,
        layout: CompiledDynamicSBMLayout,
    ) -> None:
        data.ensure_strictly_positive(model_name="Tone--Tsutsui dynamic SBM")
        if data.dynamic_spec.boundary_policy != "tone_tsutsui_2010":
            raise ModelSpecificationError("unsupported dynamic SBM boundary policy")
        if self.score_variant == "free_adjusted_post" and layout.n_free == 0:
            raise ModelSpecificationError(
                "score_variant='free_adjusted_post' requires at least one "
                "free/discretionary carry-over"
            )

    def _weights(
        self,
        data: DynamicData,
        layout: CompiledDynamicSBMLayout,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, str]]:
        period_weights, period_source = _named_weights(
            self.period_weights,
            data.periods,
            target_sum=float(data.n_periods),
            field="period_weights",
        )
        input_weights, input_source = _named_weights(
            self.input_weights,
            layout.inputs,
            target_sum=float(layout.n_inputs),
            field="input_weights",
        )
        output_weights, output_source = _named_weights(
            self.output_weights,
            layout.outputs,
            target_sum=float(layout.n_outputs),
            field="output_weights",
        )
        return (
            period_weights,
            input_weights,
            output_weights,
            {
                "period": period_source,
                "input": input_source,
                "output": output_source,
            },
        )

    def _undefined_summary(
        self,
        *,
        dmu_id: object,
        data: DynamicData,
        reference_size: int,
        solver_status: SolverStatus,
        score_status: str,
    ) -> dict[str, Any]:
        semantic_status = _semantic_solver_status(
            solver_status,
            certified=False,
        )
        return {
            "dmu_id": dmu_id,
            "period": None,
            "score": np.nan,
            "efficiency": np.nan,
            "score_valid": False,
            "score_status": score_status,
            "target_valid": False,
            "target_status": "not_available_without_certified_primary",
            "peer_valid": False,
            "peer_status": "not_available_without_certified_target",
            "dual_valid": False,
            "dual_status": "not_available_without_certified_primary",
            "carryover_valid": False,
            "carryover_status": "not_available_without_certified_primary",
            "distance": np.nan,
            "is_efficient": pd.NA,
            "is_dynamic_sbm_efficient": pd.NA,
            "all_reported_score_slacks_zero": pd.NA,
            "all_slacks_zero": pd.NA,
            "solver_status": semantic_status.value,
            "backend_solver_status": solver_status.value,
            "raw_solver_status": solver_status.value,
            "model_family": "dynamic_slacks_based",
            "orientation": self.orientation,
            "returns_to_scale": self.returns_to_scale.value,
            "score_variant": self.score_variant,
            "optimization_efficiency": np.nan,
            "free_adjusted_efficiency": np.nan,
            "overall_input_account": np.nan,
            "overall_output_expansion_account": np.nan,
            "transform_scale": np.nan,
            "reconstruction_residual": np.nan,
            "optimization_reconstruction_residual": np.nan,
            "max_balance_residual": np.nan,
            "max_continuity_residual": np.nan,
            "max_fixed_account_residual": np.nan,
            "max_original_unit_balance_residual": np.nan,
            "max_original_unit_normalized_balance_violation": np.nan,
            "max_original_unit_continuity_residual": np.nan,
            "max_original_unit_normalized_continuity_violation": np.nan,
            "max_original_unit_fixed_residual": np.nan,
            "max_original_unit_normalized_fixed_violation": np.nan,
            "max_published_target_account_violation": np.nan,
            "max_published_peer_account_violation": np.nan,
            "max_published_dual_account_violation": np.nan,
            "max_published_carryover_account_violation": np.nan,
            "omitted_intensity_sum": np.nan,
            "max_period_omitted_intensity_sum": np.nan,
            "published_dual_row_count": 0,
            "expected_dual_row_count": 0,
            "horizon_start": data.periods[0],
            "horizon_end": data.periods[-1],
            "n_periods": data.n_periods,
            "reference_size": reference_size,
            "boundary_policy": data.dynamic_spec.boundary_policy,
            "selection_status": score_status,
        }

    def _registry_spec(
        self,
        *,
        data: DynamicData,
        layout: CompiledDynamicSBMLayout,
        period_weights: np.ndarray,
        input_weights: np.ndarray,
        output_weights: np.ndarray,
    ) -> dict[str, Any]:
        carryovers = [
            {
                "variable": item.variable,
                "kind": item.kind.value,
                "effect": item.effect,
                "control": item.control,
            }
            for item in sorted(
                data.dynamic_spec.carryovers,
                key=lambda item: item.variable,
            )
        ]
        return {
            "context": {
                "purpose": "intertemporal_operating_plan_performance",
                "managerial_unit": "complete_dmu_trajectory",
            },
            "graph": {
                "kind": "time_expanded_carryover_graph",
                "periods": data.n_periods,
                "carryovers": carryovers,
            },
            "data_roles": {
                "inputs": list(layout.inputs),
                "nondiscretionary_inputs": list(layout.nondiscretionary_inputs),
                "outputs": list(layout.outputs),
                "nondiscretionary_outputs": list(layout.nondiscretionary_outputs),
                "balanced_panel": True,
                "strictly_positive": True,
            },
            "technology": {
                "family": "dynamic_carryover_portfolio_envelopment",
                "returns_to_scale": self.returns_to_scale.value,
                "continuity": "same_Z_t_exact_adjacent_period_balance",
                "boundary_policy": data.dynamic_spec.boundary_policy,
                "period_specific_intensities": True,
            },
            "estimator": {
                "kind": "full_frontier",
                "family": "dynamic_dea_envelopment",
            },
            "reference": {
                "kind": "global_complete_trajectory_cohort",
                "cohort_size": data.n_dmus,
                "same_membership_every_period": True,
                "self_membership": "allowed",
            },
            "performance": {
                "family": "dynamic_slacks_based_measure",
                "orientation": self.orientation,
                "score_variant": self.score_variant,
                "period_decomposition": "solver_selected",
            },
            "valuation": {
                "kind": "exogenous_relative_importance_weights",
                "period_weights": [float(value) for value in period_weights],
                "input_weights": [float(value) for value in input_weights],
                "output_weights": [float(value) for value in output_weights],
                "carryover_item_weights": "source_implicit_unit_weights",
            },
            "evaluation_protocol": {
                "kind": "joint_horizon_self_appraisal",
                "alternate_optimum_policy": "solver_selected",
                "adjusted_score_policy": (
                    "post_optimal_selected_primary_solution"
                    if self.score_variant == "free_adjusted_post"
                    else "not_primary"
                ),
            },
            "analysis": {
                "kind": "direct_dynamic_fit_with_period_accounts",
            },
            "uncertainty": {
                "sampling": {"kind": "none"},
                "data": {"kind": "none"},
            },
        }

    def fit(self, data: DynamicData) -> DEAResult:
        """Estimate dynamic SBM for every complete DMU trajectory."""
        if not isinstance(data, DynamicData):
            raise TypeError("ToneTsutsuiDynamicSBM.fit expects DynamicData")
        layout = compile_dynamic_sbm_layout(data.dynamic_spec)
        self._validate_data(data, layout)
        (
            period_weights,
            input_weights,
            output_weights,
            weight_sources,
        ) = self._weights(data, layout)
        reference = compile_dynamic_sbm_reference(
            data.values,
            data.variable_names,
            layout,
            np.arange(data.n_dmus, dtype=np.int64),
            orientation=self.orientation,
            returns_to_scale=self.returns_to_scale,
        )
        columns = _role_columns(layout)

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
            problem = dynamic_sbm_problem(
                reference,
                data.values[:, observation, :],
                period_weights=period_weights,
                input_weights=input_weights,
                output_weights=output_weights,
                name=str(dmu_id),
            )
            solution = self.solver.solve(problem)
            certificate = certify_lp_solution(
                problem,
                solution,
                tolerance=self.tolerance,
            )
            diagnostic_rows.append(
                _diagnostic(
                    dmu_id=dmu_id,
                    solution=solution,
                    certificate=certificate,
                )
            )
            diagnostic_rows[-1]["expected_dual_row_count"] = len(
                reference.row_descriptors
            )
            if not certificate.certified or solution.primal is None:
                diagnostic_rows[-1]["score_status"] = (
                    "solver_failed"
                    if solution.status is not SolverStatus.OPTIMAL
                    else "unavailable_uncertified_source_program"
                )
                summary_rows.append(
                    self._undefined_summary(
                        dmu_id=dmu_id,
                        data=data,
                        reference_size=reference.size,
                        solver_status=solution.status,
                        score_status=(
                            "solver_failed"
                            if solution.status is not SolverStatus.OPTIMAL
                            else "unavailable_uncertified_source_program"
                        ),
                    )
                )
                continue

            primal = solution.primal
            transform_scale = float(primal[reference.tau_index])
            # Charnes--Cooper only requires a finite, strictly positive scale.
            # Comparing it with the model tolerance would incorrectly discard
            # valid trajectories whose economic score is itself very small.
            if not math.isfinite(transform_scale) or transform_scale <= 0.0:
                diagnostic_rows[-1].update(
                    {
                        "solver_status": SolverStatus.NUMERICAL_ERROR.value,
                        "postsolve_certified": False,
                        "certification_reason": "invalid_transform_scale",
                        "economic_postsolve_certified": False,
                        "economic_certification_reason": "invalid_transform_scale",
                        "max_economic_violation": math.inf,
                        "score_status": "unavailable_uncertified_source_program",
                    }
                )
                summary_rows.append(
                    self._undefined_summary(
                        dmu_id=dmu_id,
                        data=data,
                        reference_size=reference.size,
                        solver_status=solution.status,
                        score_status="unavailable_uncertified_source_program",
                    )
                )
                continue
            lambdas = np.asarray(
                np.vstack(
                    [primal[item] / transform_scale for item in reference.lambda_slices]
                ),
                dtype=np.float64,
            )
            lambdas[(lambdas < 0.0) & (np.abs(lambdas) <= self.tolerance)] = 0.0
            slacks = {
                role: _extract_slacks(
                    primal,
                    reference.slack_slices(role),
                    transform_scale=transform_scale,
                    tolerance=self.tolerance,
                )
                for role in (
                    "input",
                    "output",
                    "good_carryover",
                    "bad_carryover",
                    "free_carryover",
                )
            }
            observed = reference.canonical_observation(data.values[:, observation, :])
            base_accounts = _weighted_accounts(
                observed=observed,
                slacks=slacks,
                columns=columns,
                period_weights=period_weights,
                input_weights=input_weights,
                output_weights=output_weights,
                layout=layout,
            )
            if not _accounts_support_efficiency(
                base_accounts,
                self.orientation,
                period_weights,
                self.tolerance,
            ):
                diagnostic_rows[-1].update(
                    {
                        "solver_status": SolverStatus.NUMERICAL_ERROR.value,
                        "postsolve_certified": False,
                        "certification_reason": "invalid_source_accounts",
                        "economic_postsolve_certified": False,
                        "economic_certification_reason": "invalid_source_accounts",
                        "max_economic_violation": math.inf,
                        "score_status": "unavailable_uncertified_source_program",
                    }
                )
                summary_rows.append(
                    self._undefined_summary(
                        dmu_id=dmu_id,
                        data=data,
                        reference_size=reference.size,
                        solver_status=solution.status,
                        score_status="unavailable_uncertified_source_program",
                    )
                )
                continue
            base_efficiency, base_period_efficiencies = _efficiencies(
                orientation=self.orientation,
                input_accounts=base_accounts["input_accounts"],  # type: ignore[arg-type]
                output_accounts=base_accounts["output_accounts"],  # type: ignore[arg-type]
                aggregate_input=float(base_accounts["aggregate_input"]),
                aggregate_output=float(base_accounts["aggregate_output"]),
            )
            adjusted = _adjusted_accounts(
                observed=observed,
                slacks=slacks,
                columns=columns,
                period_weights=period_weights,
                input_weights=input_weights,
                output_weights=output_weights,
                layout=layout,
            )
            adjusted_efficiency = np.nan
            adjusted_period_efficiencies = np.full(
                data.n_periods,
                np.nan,
                dtype=np.float64,
            )
            if adjusted is not None:
                if not _accounts_support_efficiency(
                    adjusted,
                    self.orientation,
                    period_weights,
                    self.tolerance,
                ):
                    if self.score_variant == "free_adjusted_post":
                        diagnostic_rows[-1].update(
                            {
                                "solver_status": SolverStatus.NUMERICAL_ERROR.value,
                                "postsolve_certified": False,
                                "certification_reason": "invalid_adjusted_accounts",
                                "economic_postsolve_certified": False,
                                "economic_certification_reason": (
                                    "invalid_adjusted_accounts"
                                ),
                                "max_economic_violation": math.inf,
                                "score_status": (
                                    "unavailable_uncertified_source_program"
                                ),
                            }
                        )
                        summary_rows.append(
                            self._undefined_summary(
                                dmu_id=dmu_id,
                                data=data,
                                reference_size=reference.size,
                                solver_status=solution.status,
                                score_status=("unavailable_uncertified_source_program"),
                            )
                        )
                        continue
                    adjusted = None
                else:
                    (
                        adjusted_efficiency,
                        adjusted_period_efficiencies,
                    ) = _efficiencies(
                        orientation=self.orientation,
                        input_accounts=adjusted["input_accounts"],  # type: ignore[arg-type]
                        output_accounts=adjusted["output_accounts"],  # type: ignore[arg-type]
                        aggregate_input=float(adjusted["aggregate_input"]),
                        aggregate_output=float(adjusted["aggregate_output"]),
                    )
            reported_efficiency = (
                adjusted_efficiency
                if self.score_variant == "free_adjusted_post"
                else base_efficiency
            )
            reported_period_efficiencies = (
                adjusted_period_efficiencies
                if self.score_variant == "free_adjusted_post"
                else base_period_efficiencies
            )

            objective_value = float(solution.objective)
            if self.orientation == "output" and objective_value >= -self.tolerance:
                diagnostic_rows[-1].update(
                    {
                        "solver_status": SolverStatus.NUMERICAL_ERROR.value,
                        "postsolve_certified": False,
                        "certification_reason": "invalid_output_expansion",
                        "economic_postsolve_certified": False,
                        "economic_certification_reason": ("invalid_output_expansion"),
                        "max_economic_violation": math.inf,
                        "score_status": "unavailable_uncertified_source_program",
                    }
                )
                summary_rows.append(
                    self._undefined_summary(
                        dmu_id=dmu_id,
                        data=data,
                        reference_size=reference.size,
                        solver_status=solution.status,
                        score_status="unavailable_uncertified_source_program",
                    )
                )
                continue
            solver_efficiency = _solver_base_efficiency(
                self.orientation,
                objective_value,
            )
            optimization_residual = base_efficiency - solver_efficiency
            reconstructed_reported = self._aggregate_period_accounts(
                period_weights=period_weights,
                input_accounts=(
                    adjusted["input_accounts"]  # type: ignore[index]
                    if self.score_variant == "free_adjusted_post"
                    else base_accounts["input_accounts"]
                ),
                output_accounts=(
                    adjusted["output_accounts"]  # type: ignore[index]
                    if self.score_variant == "free_adjusted_post"
                    else base_accounts["output_accounts"]
                ),
            )
            reconstruction_residual = reported_efficiency - reconstructed_reported

            benchmark = np.einsum(
                "tn,tnv->tv",
                lambdas,
                reference.scaled_values,
            )
            target_from_slack = self._targets_from_slacks(
                observed=observed,
                slacks=slacks,
                columns=columns,
            )
            balance_residual = benchmark - target_from_slack
            max_balance_residual = float(np.max(np.abs(balance_residual), initial=0.0))
            continuity_residuals = self._continuity_residuals(
                lambdas=lambdas,
                reference=reference,
                columns=columns,
            )
            max_continuity_residual = float(
                np.max(np.abs(continuity_residuals), initial=0.0)
            )
            fixed_columns = np.concatenate(
                [
                    columns["nondiscretionary_input"],
                    columns["nondiscretionary_output"],
                    columns["fixed_carryover"],
                ]
            )
            fixed_residuals = (
                np.empty((data.n_periods, 0), dtype=np.float64)
                if fixed_columns.size == 0
                else benchmark[:, fixed_columns] - observed[:, fixed_columns]
            )
            max_fixed_residual = _max_abs(fixed_residuals)
            (
                max_original_unit_balance_residual,
                max_original_unit_normalized_balance_violation,
            ) = _original_unit_residual_account(
                balance_residual,
                reference.scales,
            )
            carryover_columns = np.concatenate(
                [
                    columns["good_carryover"],
                    columns["bad_carryover"],
                    columns["free_carryover"],
                    columns["fixed_carryover"],
                ]
            )
            (
                max_original_unit_continuity_residual,
                max_original_unit_normalized_continuity_violation,
            ) = _original_unit_residual_account(
                continuity_residuals,
                reference.scales[carryover_columns],
            )
            (
                max_original_unit_fixed_residual,
                max_original_unit_normalized_fixed_violation,
            ) = _original_unit_residual_account(
                fixed_residuals,
                reference.scales[fixed_columns],
            )
            max_economic_violation = _dynamic_economic_postsolve_violation(
                transform_scale=transform_scale,
                base_accounts=base_accounts,
                adjusted_accounts=adjusted,
                base_efficiency=base_efficiency,
                base_period_efficiencies=base_period_efficiencies,
                reported_efficiency=reported_efficiency,
                reported_period_efficiencies=reported_period_efficiencies,
                solver_efficiency=solver_efficiency,
                optimization_residual=optimization_residual,
                reconstruction_residual=reconstruction_residual,
                max_balance_residual=max_balance_residual,
                max_continuity_residual=max_continuity_residual,
                max_fixed_residual=max_fixed_residual,
                max_original_unit_normalized_balance_violation=(
                    max_original_unit_normalized_balance_violation
                ),
                max_original_unit_normalized_continuity_violation=(
                    max_original_unit_normalized_continuity_violation
                ),
                max_original_unit_normalized_fixed_violation=(
                    max_original_unit_normalized_fixed_violation
                ),
            )
            economic_certified = bool(
                math.isfinite(max_economic_violation)
                and max_economic_violation <= 10.0 * self.tolerance
            )
            diagnostic_rows[-1]["economic_postsolve_certified"] = economic_certified
            diagnostic_rows[-1]["economic_certification_reason"] = (
                "certified"
                if economic_certified
                else "source_account_reconstruction_failed"
            )
            diagnostic_rows[-1]["max_economic_violation"] = max_economic_violation
            diagnostic_rows[-1].update(
                {
                    "max_original_unit_balance_residual": (
                        max_original_unit_balance_residual
                    ),
                    "max_original_unit_normalized_balance_violation": (
                        max_original_unit_normalized_balance_violation
                    ),
                    "max_original_unit_continuity_residual": (
                        max_original_unit_continuity_residual
                    ),
                    "max_original_unit_normalized_continuity_violation": (
                        max_original_unit_normalized_continuity_violation
                    ),
                    "max_original_unit_fixed_residual": (
                        max_original_unit_fixed_residual
                    ),
                    "max_original_unit_normalized_fixed_violation": (
                        max_original_unit_normalized_fixed_violation
                    ),
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
                        "score_status": "unavailable_uncertified_source_program",
                    }
                )
                summary_rows.append(
                    self._undefined_summary(
                        dmu_id=dmu_id,
                        data=data,
                        reference_size=reference.size,
                        solver_status=solution.status,
                        score_status="unavailable_uncertified_source_program",
                    )
                )
                continue

            candidate_target_rows: list[dict[str, Any]] = []
            self._append_targets(
                rows=candidate_target_rows,
                data=data,
                dmu_id=dmu_id,
                layout=layout,
                reference=reference,
                observed=observed,
                benchmark=benchmark,
                balance_residual=balance_residual,
                columns=columns,
            )
            target_row_violation = self._target_row_account_violation(
                rows=candidate_target_rows,
                data=data,
                dmu_id=dmu_id,
                layout=layout,
                reference=reference,
                observed=observed,
                benchmark=benchmark,
                balance_residual=balance_residual,
                columns=columns,
            )
            max_target_violation = max(
                max_balance_residual,
                max_original_unit_normalized_balance_violation,
                target_row_violation,
            )
            target_valid = bool(
                math.isfinite(max_target_violation)
                and max_target_violation <= 10.0 * self.tolerance
            )
            target_status = (
                "certified_original_unit_trajectory_target_account"
                if target_valid
                else "unavailable_uncertified_target_account"
            )

            candidate_intensity_rows: list[dict[str, Any]] = []
            self._append_intensities(
                rows=candidate_intensity_rows,
                data=data,
                dmu_id=dmu_id,
                reference=reference,
                lambdas=lambdas,
            )
            peer_account = self._peer_account(
                rows=candidate_intensity_rows,
                data=data,
                dmu_id=dmu_id,
                reference=reference,
                lambdas=lambdas,
                target_from_slack=target_from_slack,
                columns=columns,
            )
            peer_valid = bool(peer_account["valid"])
            peer_status = str(peer_account["status"])
            max_peer_violation = float(peer_account["max_violation"])
            omitted_intensity_sum = float(peer_account["omitted_intensity_sum"])
            max_period_omitted_intensity_sum = float(
                peer_account["max_period_omitted_intensity_sum"]
            )

            candidate_link_rows: list[dict[str, Any]] = []
            self._append_links(
                rows=candidate_link_rows,
                data=data,
                dmu_id=dmu_id,
                layout=layout,
                reference=reference,
                observed=observed,
                benchmark=benchmark,
                lambdas=lambdas,
                columns=columns,
            )
            carryover_row_violation = self._carryover_row_account_violation(
                rows=candidate_link_rows,
                data=data,
                dmu_id=dmu_id,
                layout=layout,
                reference=reference,
                observed=observed,
                benchmark=benchmark,
                lambdas=lambdas,
                columns=columns,
            )
            max_carryover_violation = max(
                max_continuity_residual,
                max_original_unit_normalized_continuity_violation,
                carryover_row_violation,
            )
            carryover_valid = bool(
                math.isfinite(max_carryover_violation)
                and max_carryover_violation <= 10.0 * self.tolerance
            )
            carryover_status = (
                "not_applicable_no_carryovers"
                if carryover_columns.size == 0
                else (
                    "certified_original_unit_carryover_account"
                    if carryover_valid
                    else "unavailable_uncertified_carryover_account"
                )
            )

            candidate_dual_rows = self._dual_rows(
                data=data,
                dmu_id=dmu_id,
                reference=reference,
                solution=solution,
            )
            max_dual_violation = self._dual_account_violation(
                rows=candidate_dual_rows,
                data=data,
                dmu_id=dmu_id,
                reference=reference,
            )
            dual_valid = bool(math.isfinite(max_dual_violation))
            dual_status = (
                "certified_complete_finite_transformed_row_marginals"
                if dual_valid
                else "unavailable_incomplete_or_nonfinite_transformed_row_marginals"
            )
            published_dual_row_count = len(candidate_dual_rows) if dual_valid else 0
            expected_dual_row_count = len(reference.row_descriptors)
            diagnostic_rows[-1].update(
                {
                    "score_valid": True,
                    "score_status": "defined",
                    "target_valid": target_valid,
                    "target_status": target_status,
                    "peer_valid": peer_valid,
                    "peer_status": peer_status,
                    "dual_valid": dual_valid,
                    "dual_status": dual_status,
                    "carryover_valid": carryover_valid,
                    "carryover_status": carryover_status,
                    "published_dual_row_count": published_dual_row_count,
                    "expected_dual_row_count": expected_dual_row_count,
                    "omitted_intensity_sum": omitted_intensity_sum,
                    "max_period_omitted_intensity_sum": (
                        max_period_omitted_intensity_sum
                    ),
                    "max_published_target_account_violation": (max_target_violation),
                    "max_published_peer_account_violation": max_peer_violation,
                    "max_published_dual_account_violation": max_dual_violation,
                    "max_published_carryover_account_violation": (
                        max_carryover_violation
                    ),
                }
            )
            if target_valid:
                target_rows.extend(candidate_target_rows)
            if peer_valid:
                intensity_rows.extend(candidate_intensity_rows)
            if carryover_valid:
                link_rows.extend(candidate_link_rows)
            if dual_valid:
                dual_rows.extend(candidate_dual_rows)

            all_reported_zero = self._all_reported_slacks_zero(
                observed=observed,
                slacks=slacks,
                columns=columns,
            )
            all_slacks_zero = all(
                float(np.max(np.abs(values), initial=0.0)) <= self.tolerance
                for values in slacks.values()
            )
            efficient = bool(
                math.isclose(
                    reported_efficiency,
                    1.0,
                    rel_tol=0.0,
                    abs_tol=self.tolerance,
                )
            )
            is_efficient: bool | Any = (
                bool(efficient and all_reported_zero)
                if self.orientation == "non-oriented"
                else pd.NA
            )
            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": None,
                    "score": reported_efficiency,
                    "efficiency": reported_efficiency,
                    "score_valid": True,
                    "score_status": "defined",
                    "target_valid": target_valid,
                    "target_status": target_status,
                    "peer_valid": peer_valid,
                    "peer_status": peer_status,
                    "dual_valid": dual_valid,
                    "dual_status": dual_status,
                    "carryover_valid": carryover_valid,
                    "carryover_status": carryover_status,
                    "distance": 1.0 - reported_efficiency,
                    "is_efficient": is_efficient,
                    "is_dynamic_sbm_efficient": efficient,
                    "all_reported_score_slacks_zero": all_reported_zero,
                    "all_slacks_zero": all_slacks_zero,
                    "solver_status": solution.status.value,
                    "backend_solver_status": solution.status.value,
                    "raw_solver_status": solution.status.value,
                    "model_family": "dynamic_slacks_based",
                    "orientation": self.orientation,
                    "returns_to_scale": self.returns_to_scale.value,
                    "score_variant": self.score_variant,
                    "optimization_efficiency": base_efficiency,
                    "free_adjusted_efficiency": adjusted_efficiency,
                    "overall_input_account": (
                        float(adjusted["aggregate_input"])  # type: ignore[index]
                        if self.score_variant == "free_adjusted_post"
                        else float(base_accounts["aggregate_input"])
                    ),
                    "overall_output_expansion_account": (
                        float(adjusted["aggregate_output"])  # type: ignore[index]
                        if self.score_variant == "free_adjusted_post"
                        else float(base_accounts["aggregate_output"])
                    ),
                    "optimization_input_account": float(
                        base_accounts["aggregate_input"]
                    ),
                    "optimization_output_expansion_account": float(
                        base_accounts["aggregate_output"]
                    ),
                    "transform_scale": transform_scale,
                    "reconstruction_residual": reconstruction_residual,
                    "optimization_reconstruction_residual": (optimization_residual),
                    "max_balance_residual": max_balance_residual,
                    "max_continuity_residual": max_continuity_residual,
                    "max_fixed_account_residual": max_fixed_residual,
                    "max_original_unit_balance_residual": (
                        max_original_unit_balance_residual
                    ),
                    "max_original_unit_normalized_balance_violation": (
                        max_original_unit_normalized_balance_violation
                    ),
                    "max_original_unit_continuity_residual": (
                        max_original_unit_continuity_residual
                    ),
                    "max_original_unit_normalized_continuity_violation": (
                        max_original_unit_normalized_continuity_violation
                    ),
                    "max_original_unit_fixed_residual": (
                        max_original_unit_fixed_residual
                    ),
                    "max_original_unit_normalized_fixed_violation": (
                        max_original_unit_normalized_fixed_violation
                    ),
                    "max_published_target_account_violation": (max_target_violation),
                    "max_published_peer_account_violation": max_peer_violation,
                    "max_published_dual_account_violation": max_dual_violation,
                    "max_published_carryover_account_violation": (
                        max_carryover_violation
                    ),
                    "omitted_intensity_sum": omitted_intensity_sum,
                    "max_period_omitted_intensity_sum": (
                        max_period_omitted_intensity_sum
                    ),
                    "published_dual_row_count": published_dual_row_count,
                    "expected_dual_row_count": expected_dual_row_count,
                    "horizon_start": data.periods[0],
                    "horizon_end": data.periods[-1],
                    "n_periods": data.n_periods,
                    "reference_size": reference.size,
                    "boundary_policy": data.dynamic_spec.boundary_policy,
                    "selection_status": ("solver_selected_not_uniqueness_certified"),
                }
            )
            self._append_components(
                rows=component_rows,
                data=data,
                dmu_id=dmu_id,
                period_weights=period_weights,
                base_accounts=base_accounts,
                adjusted=adjusted,
                base_efficiency=base_efficiency,
                adjusted_efficiency=adjusted_efficiency,
                base_period_efficiencies=base_period_efficiencies,
                adjusted_period_efficiencies=(adjusted_period_efficiencies),
                reported_efficiency=reported_efficiency,
                reported_period_efficiencies=(reported_period_efficiencies),
            )
            self._append_slacks(
                rows=slack_rows,
                data=data,
                dmu_id=dmu_id,
                layout=layout,
                reference=reference,
                observed=observed,
                slacks=slacks,
                columns=columns,
                adjusted=adjusted,
            )
        specialization = (
            "dynamic.sbm.tone_tsutsui_2010.free_adjusted_post"
            if self.score_variant == "free_adjusted_post"
            else None
        )
        metadata = registry_metadata(
            self._registry_method_id,
            self._registry_spec(
                data=data,
                layout=layout,
                period_weights=period_weights,
                input_weights=input_weights,
                output_weights=output_weights,
            ),
            specialization_id=specialization,
        )
        metadata.update(
            {
                "model": type(self).__name__,
                "source": {
                    "authors": ["Kaoru Tone", "Miki Tsutsui"],
                    "year": 2010,
                    "doi": "10.1016/j.omega.2009.07.003",
                },
                "orientation": self.orientation,
                "returns_to_scale": self.returns_to_scale.value,
                "score_variant": self.score_variant,
                "boundary_policy": data.dynamic_spec.boundary_policy,
                "spec_fingerprint": data.spec_fingerprint,
                "period_order": tuple(data.periods.tolist()),
                "effective_weights": {
                    "period": {
                        str(label): float(value)
                        for label, value in zip(
                            data.periods,
                            period_weights,
                            strict=True,
                        )
                    },
                    "input": {
                        label: float(value)
                        for label, value in zip(
                            layout.inputs,
                            input_weights,
                            strict=True,
                        )
                    },
                    "output": {
                        label: float(value)
                        for label, value in zip(
                            layout.outputs,
                            output_weights,
                            strict=True,
                        )
                    },
                    "sources": weight_sources,
                },
                "reference_policy": "global_complete_trajectory_cohort",
                "compiled_reference_sets": 1,
                "primary_solves": data.n_dmus,
                "secondary_solves": 0,
                "primary_solver_calls": data.n_dmus,
                "solver_calls": data.n_dmus,
                "additional_solver_calls": 0,
                "certificate_extra_solver_calls": 0,
                "matrix_shape": (
                    reference.n_equalities,
                    reference.n_variables,
                ),
                "matrix_nnz": reference.n_nonzero,
                "selection_status": ("solver_selected_not_uniqueness_certified"),
                "unsupported_source_extensions": (
                    "initial_condition",
                    "shared_output_good_carryover_resource",
                    "free_carryover_mip",
                ),
                "score_direction": "higher_is_better",
                "native_score": "efficiency",
                "distance_transform": "one_minus_efficiency",
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "postsolve_certificate": {
                    "lp": ("solver_neutral_primal_dual_kkt_and_strong_duality"),
                    "economic": (
                        "transform_scale_score_canonical_and_original_unit_"
                        "normalized_trajectory_accounts"
                    ),
                    "failure_policy": (
                        "claim_specific_fail_closed_score_target_peer_dual_"
                        "and_carryover"
                    ),
                    "target_release": (
                        "complete_finite_original_unit_trajectory_target_account"
                    ),
                    "peer_release": (
                        "thresholded_canonical_and_original_unit_target_rts_"
                        "and_continuity_account"
                    ),
                    "dual_release": (
                        "bounded_complete_finite_transformed_row_marginals;_"
                        "no_original_unit_dual_claim"
                    ),
                    "carryover_release": (
                        "complete_original_unit_adjacent_period_account"
                    ),
                    "semantic_tables": {
                        "targets": "target_valid",
                        "intensities": "peer_valid",
                        "duals": "dual_valid",
                        "links": "carryover_valid",
                    },
                    "additional_solver_calls": 0,
                    "certificate_extra_solver_calls": 0,
                },
            }
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

    def _aggregate_period_accounts(
        self,
        *,
        period_weights: np.ndarray,
        input_accounts: np.ndarray,
        output_accounts: np.ndarray,
    ) -> float:
        effective = period_weights / period_weights.size
        aggregate_input = float(np.dot(effective, input_accounts))
        aggregate_output = float(np.dot(effective, output_accounts))
        if self.orientation == "input":
            return aggregate_input
        if self.orientation == "output":
            return 1.0 / aggregate_output
        return aggregate_input / aggregate_output

    def _targets_from_slacks(
        self,
        *,
        observed: np.ndarray,
        slacks: dict[str, np.ndarray],
        columns: dict[str, np.ndarray],
    ) -> np.ndarray:
        targets = observed.copy()
        targets[:, columns["input"]] -= slacks["input"]
        targets[:, columns["output"]] += slacks["output"]
        targets[:, columns["good_carryover"]] += slacks["good_carryover"]
        targets[:, columns["bad_carryover"]] -= slacks["bad_carryover"]
        targets[:, columns["free_carryover"]] -= slacks["free_carryover"]
        return targets

    def _continuity_residuals(
        self,
        *,
        lambdas: np.ndarray,
        reference: CompiledDynamicSBMReference,
        columns: dict[str, np.ndarray],
    ) -> np.ndarray:
        carryover_columns = np.concatenate(
            [
                columns["good_carryover"],
                columns["bad_carryover"],
                columns["free_carryover"],
                columns["fixed_carryover"],
            ]
        )
        residuals = np.empty(
            (reference.n_periods - 1, carryover_columns.size),
            dtype=np.float64,
        )
        for period in range(reference.n_periods - 1):
            transition_values = reference.scaled_values[
                period,
                :,
                :,
            ][:, carryover_columns]
            residuals[period] = (
                lambdas[period] @ transition_values
                - lambdas[period + 1] @ transition_values
            )
        return residuals

    def _target_row_account_violation(
        self,
        *,
        rows: list[dict[str, Any]],
        data: DynamicData,
        dmu_id: object,
        layout: CompiledDynamicSBMLayout,
        reference: CompiledDynamicSBMReference,
        observed: np.ndarray,
        benchmark: np.ndarray,
        balance_residual: np.ndarray,
        columns: dict[str, np.ndarray],
    ) -> float:
        """Audit candidate target rows in their published original units."""

        role_variables = {
            "input": layout.inputs,
            "nondiscretionary_input": layout.nondiscretionary_inputs,
            "output": layout.outputs,
            "nondiscretionary_output": layout.nondiscretionary_outputs,
            "good_carryover": layout.good_carryovers,
            "bad_carryover": layout.bad_carryovers,
            "free_carryover": layout.free_carryovers,
            "fixed_carryover": layout.fixed_carryovers,
        }
        expected_count = data.n_periods * len(layout.variable_names)
        if len(rows) != expected_count:
            return math.inf
        lookup: dict[tuple[object, str, str], dict[str, Any]] = {}
        for row in rows:
            if row.get("dmu_id") != dmu_id:
                return math.inf
            key = (row.get("period"), str(row.get("role")), str(row.get("variable")))
            if key in lookup:
                return math.inf
            lookup[key] = row

        violations: list[float] = []
        for role, variables in role_variables.items():
            for period in range(data.n_periods):
                for item, variable in enumerate(variables):
                    key = (data.periods[period], role, variable)
                    row = lookup.get(key)
                    if row is None:
                        return math.inf
                    column = int(columns[role][item])
                    scale = float(reference.scales[column])
                    observed_value = float(observed[period, column] * scale)
                    target = float(benchmark[period, column] * scale)
                    residual = float(balance_residual[period, column] * scale)
                    violations.extend(
                        [
                            _scaled_scalar_violation(
                                row.get("observed"),
                                observed_value,
                                scale,
                            ),
                            _scaled_scalar_violation(
                                row.get("target"),
                                target,
                                scale,
                            ),
                            _scaled_scalar_violation(
                                row.get("adjustment"),
                                target - observed_value,
                                scale,
                            ),
                            _scaled_scalar_violation(
                                row.get("balance_residual"),
                                residual,
                                scale,
                            ),
                        ]
                    )
        return float(np.max(violations, initial=0.0))

    def _peer_account(
        self,
        *,
        rows: list[dict[str, Any]],
        data: DynamicData,
        dmu_id: object,
        reference: CompiledDynamicSBMReference,
        lambdas: np.ndarray,
        target_from_slack: np.ndarray,
        columns: dict[str, np.ndarray],
    ) -> dict[str, float | bool | str]:
        """Audit the thresholded public peer account without changing the score."""

        intended = np.where(lambdas > self.peer_tolerance, lambdas, 0.0)
        omitted = np.maximum(lambdas - intended, 0.0)
        omitted_by_period = np.sum(omitted, axis=1)
        omitted_total = float(np.sum(omitted_by_period))
        max_period_omitted = float(np.max(omitted_by_period, initial=0.0))

        period_positions = {label: index for index, label in enumerate(data.periods)}
        reference_positions = {
            data.dmu_ids[int(reference_row)]: position
            for position, reference_row in enumerate(reference.rows)
        }
        recovered = np.zeros_like(lambdas)
        seen: set[tuple[int, int]] = set()
        rows_valid = True
        for row in rows:
            try:
                period = period_positions[row.get("period")]
                position = reference_positions[row.get("reference_dmu_id")]
                intensity = float(row.get("intensity"))
            except (KeyError, TypeError, ValueError):
                rows_valid = False
                break
            key = (period, position)
            if (
                key in seen
                or row.get("dmu_id") != dmu_id
                or row.get("reference_period") != data.periods[period]
                or not math.isfinite(intensity)
                or intensity <= 0.0
            ):
                rows_valid = False
                break
            seen.add(key)
            recovered[period, position] = intensity

        row_violation = _max_abs(recovered - intended) if rows_valid else math.inf
        benchmark = np.einsum("tn,tnv->tv", recovered, reference.scaled_values)
        canonical_target_violation = _max_abs(benchmark - target_from_slack)
        _, original_target_violation = _original_unit_residual_account(
            benchmark - target_from_slack,
            reference.scales,
        )
        if self.returns_to_scale is ReturnsToScale.VRS:
            rts_violation = _max_abs(np.sum(recovered, axis=1) - 1.0)
        else:
            rts_violation = max(
                0.0,
                -float(np.min(recovered, initial=0.0)),
            )
        continuity = self._continuity_residuals(
            lambdas=recovered,
            reference=reference,
            columns=columns,
        )
        canonical_continuity_violation = _max_abs(continuity)
        carryover_columns = np.concatenate(
            [
                columns["good_carryover"],
                columns["bad_carryover"],
                columns["free_carryover"],
                columns["fixed_carryover"],
            ]
        )
        _, original_continuity_violation = _original_unit_residual_account(
            continuity,
            reference.scales[carryover_columns],
        )
        max_violation = max(
            row_violation,
            canonical_target_violation,
            original_target_violation,
            rts_violation,
            canonical_continuity_violation,
            original_continuity_violation,
        )
        valid = bool(
            math.isfinite(max_violation) and max_violation <= 10.0 * self.tolerance
        )
        return {
            "valid": valid,
            "status": (
                "certified_thresholded_trajectory_peer_account"
                if valid
                else "unavailable_after_peer_reporting_threshold"
            ),
            "max_violation": max_violation,
            "omitted_intensity_sum": omitted_total,
            "max_period_omitted_intensity_sum": max_period_omitted,
        }

    def _carryover_row_account_violation(
        self,
        *,
        rows: list[dict[str, Any]],
        data: DynamicData,
        dmu_id: object,
        layout: CompiledDynamicSBMLayout,
        reference: CompiledDynamicSBMReference,
        observed: np.ndarray,
        benchmark: np.ndarray,
        lambdas: np.ndarray,
        columns: dict[str, np.ndarray],
    ) -> float:
        """Audit candidate carry-over rows in their published original units."""

        role_kind = {
            "good_carryover": "good",
            "bad_carryover": "bad",
            "free_carryover": "free",
            "fixed_carryover": "fixed",
        }
        role_variables = {
            "good_carryover": layout.good_carryovers,
            "bad_carryover": layout.bad_carryovers,
            "free_carryover": layout.free_carryovers,
            "fixed_carryover": layout.fixed_carryovers,
        }
        expected_count = data.n_periods * sum(
            len(variables) for variables in role_variables.values()
        )
        if len(rows) != expected_count:
            return math.inf
        lookup: dict[tuple[object, str], dict[str, Any]] = {}
        for row in rows:
            if row.get("dmu_id") != dmu_id:
                return math.inf
            key = (row.get("period"), str(row.get("carryover")))
            if key in lookup:
                return math.inf
            lookup[key] = row

        violations: list[float] = []
        for role, variables in role_variables.items():
            for item, variable in enumerate(variables):
                column = int(columns[role][item])
                scale = float(reference.scales[column])
                for period in range(data.n_periods):
                    row = lookup.get((data.periods[period], variable))
                    if row is None:
                        return math.inf
                    source_target = float(benchmark[period, column] * scale)
                    observed_value = float(observed[period, column] * scale)
                    violations.extend(
                        [
                            _scaled_scalar_violation(
                                row.get("observed"),
                                observed_value,
                                scale,
                            ),
                            _scaled_scalar_violation(
                                row.get("source_target"),
                                source_target,
                                scale,
                            ),
                        ]
                    )
                    if (
                        row.get("carryover_kind") != role_kind[role]
                        or row.get("source_period") != data.periods[period]
                    ):
                        return math.inf
                    if period == data.n_periods - 1:
                        if not (
                            pd.isna(row.get("next_period_target"))
                            and pd.isna(row.get("continuity_residual"))
                            and pd.isna(row.get("target_period"))
                        ):
                            return math.inf
                        continue
                    recipient_target = float(
                        lambdas[period + 1]
                        @ reference.scaled_values[period, :, column]
                        * scale
                    )
                    residual = source_target - recipient_target
                    if row.get("target_period") != data.periods[period + 1]:
                        return math.inf
                    violations.extend(
                        [
                            _scaled_scalar_violation(
                                row.get("next_period_target"),
                                recipient_target,
                                scale,
                            ),
                            _scaled_scalar_violation(
                                row.get("continuity_residual"),
                                residual,
                                scale,
                            ),
                        ]
                    )
        return float(np.max(violations, initial=0.0))

    def _dual_account_violation(
        self,
        *,
        rows: list[dict[str, Any]],
        data: DynamicData,
        dmu_id: object,
        reference: CompiledDynamicSBMReference,
    ) -> float:
        """Bound the dual release claim to complete finite transformed rows."""

        if len(rows) != len(reference.row_descriptors):
            return math.inf
        coordinate_system = (
            "charnes_cooper_transformed"
            if self.orientation == "non-oriented"
            else "direct_tau_fixed_to_one"
        )
        for row, descriptor in zip(rows, reference.row_descriptors, strict=True):
            role, source_index, target_index, variable = descriptor
            expected_period = (
                None if source_index is None else data.periods[source_index]
            )
            expected_target = (
                None if target_index is None else data.periods[target_index]
            )
            try:
                marginal = float(row.get("marginal"))
            except (TypeError, ValueError):
                return math.inf
            if (
                row.get("dmu_id") != dmu_id
                or row.get("period") != expected_period
                or row.get("constraint_role") != role
                or row.get("variable") != variable
                or row.get("source_period") != expected_period
                or row.get("target_period") != expected_target
                or row.get("coordinate_system") != coordinate_system
                or not math.isfinite(marginal)
            ):
                return math.inf
        return 0.0

    def _all_reported_slacks_zero(
        self,
        *,
        observed: np.ndarray,
        slacks: dict[str, np.ndarray],
        columns: dict[str, np.ndarray],
    ) -> bool:
        normalized: list[np.ndarray] = []
        if self.orientation in {"input", "non-oriented"}:
            normalized.append(slacks["input"] / observed[:, columns["input"]])
            if columns["bad_carryover"].size:
                normalized.append(
                    slacks["bad_carryover"] / observed[:, columns["bad_carryover"]]
                )
        if self.orientation in {"output", "non-oriented"}:
            normalized.append(slacks["output"] / observed[:, columns["output"]])
            if columns["good_carryover"].size:
                normalized.append(
                    slacks["good_carryover"] / observed[:, columns["good_carryover"]]
                )
        if (
            self.score_variant == "free_adjusted_post"
            and columns["free_carryover"].size
        ):
            signed = slacks["free_carryover"]
            free_observed = observed[:, columns["free_carryover"]]
            if self.orientation in {"input", "non-oriented"}:
                normalized.append(np.maximum(signed, 0.0) / free_observed)
            if self.orientation in {"output", "non-oriented"}:
                normalized.append(np.maximum(-signed, 0.0) / free_observed)
        return all(
            float(np.max(np.abs(values), initial=0.0)) <= self.tolerance
            for values in normalized
        )

    def _append_components(
        self,
        *,
        rows: list[dict[str, Any]],
        data: DynamicData,
        dmu_id: object,
        period_weights: np.ndarray,
        base_accounts: dict[str, np.ndarray | float],
        adjusted: dict[str, np.ndarray | float] | None,
        base_efficiency: float,
        adjusted_efficiency: float,
        base_period_efficiencies: np.ndarray,
        adjusted_period_efficiencies: np.ndarray,
        reported_efficiency: float,
        reported_period_efficiencies: np.ndarray,
    ) -> None:
        reported_inputs = (
            adjusted["input_accounts"]  # type: ignore[index]
            if self.score_variant == "free_adjusted_post"
            else base_accounts["input_accounts"]
        )
        reported_outputs = (
            adjusted["output_accounts"]  # type: ignore[index]
            if self.score_variant == "free_adjusted_post"
            else base_accounts["output_accounts"]
        )
        rows.append(
            {
                "dmu_id": dmu_id,
                "period": None,
                "component_type": "system",
                "component_id": "horizon",
                "efficiency": reported_efficiency,
                "base_efficiency": base_efficiency,
                "free_adjusted_efficiency": adjusted_efficiency,
                "input_account": self._weighted_value(
                    period_weights,
                    reported_inputs,  # type: ignore[arg-type]
                ),
                "output_expansion_account": self._weighted_value(
                    period_weights,
                    reported_outputs,  # type: ignore[arg-type]
                ),
                "period_weight": np.nan,
                "effective_period_weight": np.nan,
                "input_account_contribution": np.nan,
                "output_expansion_contribution": np.nan,
                "selection_status": ("solver_selected_not_uniqueness_certified"),
            }
        )
        for period in range(data.n_periods):
            effective_weight = period_weights[period] / data.n_periods
            rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": data.periods[period],
                    "component_type": "period",
                    "component_id": f"period_{period + 1}",
                    "efficiency": reported_period_efficiencies[period],
                    "base_efficiency": base_period_efficiencies[period],
                    "free_adjusted_efficiency": (adjusted_period_efficiencies[period]),
                    "input_account": reported_inputs[period],  # type: ignore[index]
                    "output_expansion_account": reported_outputs[period],  # type: ignore[index]
                    "period_weight": period_weights[period],
                    "effective_period_weight": effective_weight,
                    "input_account_contribution": (
                        effective_weight * reported_inputs[period]  # type: ignore[index]
                    ),
                    "output_expansion_contribution": (
                        effective_weight * reported_outputs[period]  # type: ignore[index]
                    ),
                    "selection_status": ("solver_selected_not_uniqueness_certified"),
                }
            )

    @staticmethod
    def _weighted_value(
        period_weights: np.ndarray,
        values: np.ndarray,
    ) -> float:
        return float(np.dot(period_weights / period_weights.size, values))

    def _append_slacks(
        self,
        *,
        rows: list[dict[str, Any]],
        data: DynamicData,
        dmu_id: object,
        layout: CompiledDynamicSBMLayout,
        reference: CompiledDynamicSBMReference,
        observed: np.ndarray,
        slacks: dict[str, np.ndarray],
        columns: dict[str, np.ndarray],
        adjusted: dict[str, np.ndarray | float] | None,
    ) -> None:
        role_variables = {
            "input": layout.inputs,
            "output": layout.outputs,
            "good_carryover": layout.good_carryovers,
            "bad_carryover": layout.bad_carryovers,
            "free_carryover": layout.free_carryovers,
        }
        semantics = {
            "input": "resource_excess",
            "output": "desirable_output_shortfall",
            "good_carryover": "valuable_carryover_shortfall",
            "bad_carryover": "harmful_carryover_excess",
            "free_carryover": "signed_discretionary_carryover_deviation",
        }
        for role, variables in role_variables.items():
            role_columns = columns[role]
            for period in range(data.n_periods):
                for item, variable in enumerate(variables):
                    value = float(slacks[role][period, item])
                    normalizer = float(observed[period, role_columns[item]])
                    original_slack = value * reference.scales[role_columns[item]]
                    free_excess = (
                        max(original_slack, 0.0) if role == "free_carryover" else np.nan
                    )
                    free_shortage = (
                        max(-original_slack, 0.0)
                        if role == "free_carryover"
                        else np.nan
                    )
                    rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": data.periods[period],
                            "role": role,
                            "variable": variable,
                            "slack": original_slack,
                            "normalized_slack": value / normalizer,
                            "free_excess": free_excess,
                            "free_shortage": free_shortage,
                            "slack_semantics": semantics[role],
                            "included_in_optimization_objective": (
                                self._included_in_base_objective(role)
                            ),
                            "included_in_reported_score": (
                                self._included_in_reported_score(
                                    role,
                                    original_slack,
                                )
                            ),
                            "score_variant": self.score_variant,
                            "selection_status": (
                                "solver_selected_not_uniqueness_certified"
                            ),
                            "adjusted_score_available": adjusted is not None,
                        }
                    )

    def _included_in_base_objective(self, role: str) -> bool:
        if role in {"input", "bad_carryover"}:
            return self.orientation in {"input", "non-oriented"}
        if role in {"output", "good_carryover"}:
            return self.orientation in {"output", "non-oriented"}
        return False

    def _included_in_reported_score(
        self,
        role: str,
        slack: float,
    ) -> bool:
        if self._included_in_base_objective(role):
            return True
        if role != "free_carryover" or self.score_variant != "free_adjusted_post":
            return False
        if slack > self.tolerance:
            return self.orientation in {"input", "non-oriented"}
        if slack < -self.tolerance:
            return self.orientation in {"output", "non-oriented"}
        return self.orientation in {"input", "output", "non-oriented"}

    def _append_targets(
        self,
        *,
        rows: list[dict[str, Any]],
        data: DynamicData,
        dmu_id: object,
        layout: CompiledDynamicSBMLayout,
        reference: CompiledDynamicSBMReference,
        observed: np.ndarray,
        benchmark: np.ndarray,
        balance_residual: np.ndarray,
        columns: dict[str, np.ndarray],
    ) -> None:
        role_variables = {
            "input": layout.inputs,
            "nondiscretionary_input": layout.nondiscretionary_inputs,
            "output": layout.outputs,
            "nondiscretionary_output": layout.nondiscretionary_outputs,
            "good_carryover": layout.good_carryovers,
            "bad_carryover": layout.bad_carryovers,
            "free_carryover": layout.free_carryovers,
            "fixed_carryover": layout.fixed_carryovers,
        }
        for role, variables in role_variables.items():
            for period in range(data.n_periods):
                for item, variable in enumerate(variables):
                    column = int(columns[role][item])
                    scale = reference.scales[column]
                    observed_value = observed[period, column] * scale
                    target = benchmark[period, column] * scale
                    rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": data.periods[period],
                            "role": role,
                            "variable": variable,
                            "observed": observed_value,
                            "target": target,
                            "adjustment": target - observed_value,
                            "balance_residual": (
                                balance_residual[period, column] * scale
                            ),
                            "selection_status": (
                                "solver_selected_not_uniqueness_certified"
                            ),
                        }
                    )

    def _append_intensities(
        self,
        *,
        rows: list[dict[str, Any]],
        data: DynamicData,
        dmu_id: object,
        reference: CompiledDynamicSBMReference,
        lambdas: np.ndarray,
    ) -> None:
        for period in range(data.n_periods):
            for position, intensity in enumerate(lambdas[period]):
                if intensity <= self.peer_tolerance:
                    continue
                reference_row = int(reference.rows[position])
                rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": data.periods[period],
                        "reference_dmu_id": data.dmu_ids[reference_row],
                        "reference_period": data.periods[period],
                        "intensity": intensity,
                    }
                )

    def _append_links(
        self,
        *,
        rows: list[dict[str, Any]],
        data: DynamicData,
        dmu_id: object,
        layout: CompiledDynamicSBMLayout,
        reference: CompiledDynamicSBMReference,
        observed: np.ndarray,
        benchmark: np.ndarray,
        lambdas: np.ndarray,
        columns: dict[str, np.ndarray],
    ) -> None:
        role_kind = {
            "good_carryover": "good",
            "bad_carryover": "bad",
            "free_carryover": "free",
            "fixed_carryover": "fixed",
        }
        role_variables = {
            "good_carryover": layout.good_carryovers,
            "bad_carryover": layout.bad_carryovers,
            "free_carryover": layout.free_carryovers,
            "fixed_carryover": layout.fixed_carryovers,
        }
        for role, variables in role_variables.items():
            for item, variable in enumerate(variables):
                column = int(columns[role][item])
                scale = reference.scales[column]
                for period in range(data.n_periods):
                    source_target = benchmark[period, column] * scale
                    if period < data.n_periods - 1:
                        recipient_target = float(
                            lambdas[period + 1]
                            @ reference.scaled_values[period, :, column]
                            * scale
                        )
                        residual = source_target - recipient_target
                        target_period: object | None = data.periods[period + 1]
                        boundary_status = "adjacent_period_continuity"
                    else:
                        recipient_target = np.nan
                        residual = np.nan
                        target_period = None
                        boundary_status = "observed_terminal_no_outgoing_continuity"
                    rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": data.periods[period],
                            "link_kind": "carryover",
                            "carryover": variable,
                            "carryover_kind": role_kind[role],
                            "source_period": data.periods[period],
                            "target_period": target_period,
                            "observed": (observed[period, column] * scale),
                            "source_target": source_target,
                            "next_period_target": recipient_target,
                            "continuity_residual": residual,
                            "boundary_status": boundary_status,
                            "selection_status": (
                                "solver_selected_not_uniqueness_certified"
                            ),
                        }
                    )

    def _dual_rows(
        self,
        *,
        data: DynamicData,
        dmu_id: object,
        reference: CompiledDynamicSBMReference,
        solution: LPSolution,
    ) -> list[dict[str, Any]]:
        if solution.equality_marginals is None:
            return []
        coordinate_system = (
            "charnes_cooper_transformed"
            if self.orientation == "non-oriented"
            else "direct_tau_fixed_to_one"
        )
        rows: list[dict[str, Any]] = []
        for descriptor, marginal in zip(
            reference.row_descriptors,
            solution.equality_marginals,
            strict=True,
        ):
            role, source_index, target_index, variable = descriptor
            rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": (
                        None if source_index is None else data.periods[source_index]
                    ),
                    "constraint_role": role,
                    "variable": variable,
                    "source_period": (
                        None if source_index is None else data.periods[source_index]
                    ),
                    "target_period": (
                        None if target_index is None else data.periods[target_index]
                    ),
                    "marginal": marginal,
                    "coordinate_system": coordinate_system,
                }
            )
        return rows


DynamicSBM = ToneTsutsuiDynamicSBM
"""Exact short alias for :class:`ToneTsutsuiDynamicSBM`."""


__all__ = [
    "DynamicSBM",
    "DynamicSBMScoreVariant",
    "ToneTsutsuiDynamicSBM",
]
