"""Radial group-frontier and metafrontier decomposition.

This module implements the DEA construction and multiplicative identity in
O'Donnell, Rao, and Battese (2008).  Group labels are declared before fitting.
They are never inferred from the fitted scores.
"""

from __future__ import annotations

import math
from collections.abc import Hashable
from typing import Any

import numpy as np
import pandas as pd

from .._registry import data_role_schema, registry_metadata
from ..data import DEAData
from ..enums import Orientation, ReturnsToScale, parse_enum
from ..exceptions import DataValidationError, ModelSpecificationError
from ..models.radial import RadialDEA
from ..results import DEAResult
from ..solvers import LPSolver, SciPyHiGHSSolver
from ..specs import SolverOptions

_METHOD_ID = "heterogeneity.metafrontier.radial.odonnell_rao_battese_2008"


def _readonly_slice(
    values: np.ndarray | None,
    positions: np.ndarray,
) -> np.ndarray | None:
    if values is None:
        return None
    sliced = np.asarray(values[positions]).copy()
    if sliced.ndim == 2 and np.issubdtype(sliced.dtype, np.number):
        sliced = np.ascontiguousarray(sliced)
    sliced.setflags(write=False)
    return sliced


def _group_view(data: DEAData, positions: np.ndarray) -> DEAData:
    """Create a solver-ready immutable view for one declared group."""

    return DEAData(
        dmu_ids=_readonly_slice(data.dmu_ids, positions),
        inputs=_readonly_slice(data.inputs, positions),
        outputs=_readonly_slice(data.outputs, positions),
        bad_outputs=_readonly_slice(data.bad_outputs, positions),
        input_names=data.input_names,
        output_names=data.output_names,
        bad_output_names=data.bad_output_names,
        polluting_input_names=data.polluting_input_names,
        periods=_readonly_slice(data.periods, positions),
        period_order=data.period_order,
        groups=_readonly_slice(data.groups, positions),
        row_labels=_readonly_slice(data.row_labels, positions),
    )


def _observation_key(
    dmu_id: Hashable,
    period: Hashable | None,
    *,
    is_panel: bool,
) -> Hashable:
    return (dmu_id, period) if is_panel else dmu_id


def _validated_group_layout(
    data: DEAData,
) -> tuple[tuple[Hashable, np.ndarray], ...]:
    if data.groups is None:
        raise ModelSpecificationError(
            "RadialMetafrontierDEA requires ex ante group labels; pass "
            "group=... when constructing DEAData"
        )

    # Python dictionaries preserve first-observed order, so one pass is enough
    # to retain the public group order and collect row positions.  The former
    # implementation rescanned all n observations for every one of K groups.
    buckets: dict[Hashable, list[int]] = {}
    for position, raw_label in enumerate(data.groups):
        try:
            hash(raw_label)
        except TypeError as error:
            raise DataValidationError(
                "metafrontier group labels must be hashable; "
                f"row position {position} has {type(raw_label).__name__}"
            ) from error
        label = raw_label
        buckets.setdefault(label, []).append(position)

    if len(buckets) < 2:
        raise ModelSpecificationError(
            "metafrontier analysis requires at least two declared technology groups"
        )

    layout: list[tuple[Hashable, np.ndarray]] = []
    for label, members in buckets.items():
        positions = np.asarray(members, dtype=np.int64)
        positions.setflags(write=False)
        layout.append((label, positions))
    return tuple(layout)


def _annotate_component_frame(
    frame: pd.DataFrame,
    *,
    data: DEAData,
    group_by_key: dict[Hashable, Hashable],
    benchmark_level: str,
) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    annotated = frame.copy()
    periods = (
        annotated["period"]
        if data.is_panel and "period" in annotated
        else pd.Series([None] * len(annotated), index=annotated.index)
    )
    annotated["group"] = [
        group_by_key[
            _observation_key(
                dmu_id,
                period,
                is_panel=data.is_panel,
            )
        ]
        for dmu_id, period in zip(
            annotated["dmu_id"],
            periods,
            strict=True,
        )
    ]
    annotated["frontier_level"] = benchmark_level
    annotated["benchmark_level"] = benchmark_level
    if "solver_status" in annotated:
        # New radial diagnostics already separate the semantic release status
        # from backend termination.  Retain a compatibility fallback for a
        # third-party radial child that predates those explicit columns.
        if "backend_solver_status" not in annotated:
            annotated["backend_solver_status"] = annotated["solver_status"]
        if "raw_solver_status" not in annotated:
            annotated["raw_solver_status"] = annotated["backend_solver_status"]

    if "reference_dmu_id" in annotated:
        reference_periods = (
            annotated["reference_period"]
            if data.is_panel and "reference_period" in annotated
            else pd.Series([None] * len(annotated), index=annotated.index)
        )
        annotated["reference_group"] = [
            group_by_key[
                _observation_key(
                    dmu_id,
                    period,
                    is_panel=data.is_panel,
                )
            ]
            for dmu_id, period in zip(
                annotated["reference_dmu_id"],
                reference_periods,
                strict=True,
            )
        ]
    return annotated


def _concat_frames(frames: list[pd.DataFrame]) -> pd.DataFrame:
    materialized = [frame for frame in frames if not frame.empty]
    if not materialized:
        return pd.DataFrame()
    return pd.concat(materialized, ignore_index=True, sort=False)


def _validity_markers(
    summary: pd.DataFrame,
    column: str,
    expected_rows: int,
) -> np.ndarray:
    """Normalize one radial validity column without promoting truthy values."""

    if len(summary) != expected_rows:
        raise RuntimeError(
            "radial component summary does not match the evaluated observations"
        )
    if column not in summary:
        return np.full(expected_rows, False, dtype=object)

    markers = np.full(expected_rows, False, dtype=object)
    for position, value in enumerate(summary[column].to_numpy(dtype=object)):
        if isinstance(value, (bool, np.bool_)):
            markers[position] = bool(value)
            continue
        try:
            if bool(pd.isna(value)):
                markers[position] = pd.NA
        except (TypeError, ValueError):
            pass
    return markers


def _status_markers(
    summary: pd.DataFrame,
    column: str,
    expected_rows: int,
) -> np.ndarray:
    """Return one component status column with an explicit missing fallback."""

    if len(summary) != expected_rows:
        raise RuntimeError(
            "radial component summary does not match the evaluated observations"
        )
    if column not in summary:
        return np.full(expected_rows, "status_not_reported", dtype=object)

    statuses = summary[column].to_numpy(dtype=object, copy=True)
    for position, value in enumerate(statuses):
        try:
            if bool(pd.isna(value)):
                statuses[position] = "status_not_reported"
        except (TypeError, ValueError):
            statuses[position] = "status_not_reported"
    return statuses


def _solver_counters(result: DEAResult) -> tuple[int, int, int]:
    """Read and validate exact solve counters from one radial child result."""

    counters: list[int] = []
    for key in ("phase_one_solver_calls", "phase_two_solver_calls", "solver_calls"):
        value = result.metadata.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
            raise RuntimeError(f"radial component metadata is missing integer {key!r}")
        normalized = int(value)
        if normalized < 0:
            raise RuntimeError(f"radial component metadata has negative {key!r}")
        counters.append(normalized)

    phase_one, phase_two, total = counters
    if total != phase_one + phase_two:
        raise RuntimeError("radial component solver-call metadata is inconsistent")
    return phase_one, phase_two, total


def _phase_one_statuses(
    result: DEAResult,
    expected_rows: int,
    *,
    component: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return semantic, backend, and raw phase-one component statuses."""

    phase_one = result.diagnostics.loc[result.diagnostics["phase"] == 1]
    if len(phase_one) != expected_rows or "solver_status" not in phase_one:
        raise RuntimeError(
            f"{component} radial diagnostics do not contain exactly one "
            "phase-one status per observation"
        )

    semantic = phase_one["solver_status"].to_numpy(dtype=object, copy=True)
    backend_column = (
        "backend_solver_status"
        if "backend_solver_status" in phase_one
        else "solver_status"
    )
    raw_column = (
        "raw_solver_status" if "raw_solver_status" in phase_one else backend_column
    )
    backend = phase_one[backend_column].to_numpy(dtype=object, copy=True)
    raw = phase_one[raw_column].to_numpy(dtype=object, copy=True)
    return semantic, backend, raw


def _explicit_true(markers: np.ndarray) -> np.ndarray:
    """Return a strict Boolean mask for an explicit validity marker array."""

    return np.fromiter(
        (isinstance(value, (bool, np.bool_)) and bool(value) for value in markers),
        dtype=bool,
        count=len(markers),
    )


class RadialMetafrontierDEA:
    """Decompose meta-efficiency into group efficiency and opportunity proximity.

    The source protocol estimates one radial frontier for every declared group
    and one pooled convex (VRS) or conic (CRS) metafrontier using all declared
    groups. With matched orientation and returns to scale,

    ``metafrontier_efficiency = group_efficiency * metatechnology_ratio``.

    ``metatechnology_ratio`` is also known historically as the technology-gap
    ratio.  A larger value means that the group's attainable frontier is closer
    to the pooled meta opportunity set; it is not a second managerial-efficiency
    score and it does not identify the cause of a group difference.

    For panel data, the source leaf pools all study periods at both levels.  It
    therefore estimates one time-invariant group frontier per group and one
    time-invariant metafrontier.  Time-varying and productivity metafrontiers
    are separate methods.
    """

    _registry_method_id = _METHOD_ID

    def __init__(
        self,
        *,
        orientation: Orientation | str = Orientation.OUTPUT,
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.VRS,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        compute_slacks: bool = False,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.orientation = parse_enum(orientation, Orientation, "orientation")
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
                "the O'Donnell--Rao--Battese radial metafrontier leaf supports "
                "CRS or VRS; NIRS and NDRS require separate source protocols"
            )
        if solver is not None and solver_options is not None:
            raise ValueError("pass solver or solver_options, not both")
        if not math.isfinite(tolerance) or tolerance <= 0.0:
            raise ValueError("tolerance must be positive and finite")
        if peer_tolerance is not None and (
            not math.isfinite(peer_tolerance) or peer_tolerance <= 0.0
        ):
            raise ValueError("peer_tolerance must be positive and finite")

        self.solver = SciPyHiGHSSolver(solver_options) if solver is None else solver
        self.compute_slacks = bool(compute_slacks)
        self.tolerance = float(tolerance)
        self.peer_tolerance = (
            self.tolerance if peer_tolerance is None else float(peer_tolerance)
        )

    def _radial_model(self) -> RadialDEA:
        return RadialDEA(
            orientation=self.orientation,
            returns_to_scale=self.returns_to_scale,
            reference="global",
            solver=self.solver,
            compute_slacks=self.compute_slacks,
            tolerance=self.tolerance,
            peer_tolerance=self.peer_tolerance,
        )

    def fit(self, data: DEAData) -> DEAResult:
        """Fit matched declared-group frontiers and the pooled metafrontier."""

        layout = _validated_group_layout(data)
        group_by_key = {
            _observation_key(
                dmu_id,
                None if data.periods is None else data.periods[position],
                is_panel=data.is_panel,
            ): data.groups[position]
            for position, dmu_id in enumerate(data.dmu_ids)
        }

        metafrontier = self._radial_model().fit(data)
        meta_summary = metafrontier.summary().reset_index(drop=True)
        n_observations = data.n_dmus
        meta_score_valid = _validity_markers(
            meta_summary,
            "score_valid",
            n_observations,
        )
        meta_score_status = _status_markers(
            meta_summary,
            "score_status",
            n_observations,
        )
        meta_completion_valid = _validity_markers(
            meta_summary,
            "completion_valid",
            n_observations,
        )
        meta_completion_status = _status_markers(
            meta_summary,
            "completion_status",
            n_observations,
        )
        meta_target_valid = _validity_markers(
            meta_summary,
            "target_valid",
            n_observations,
        )
        meta_target_status = _status_markers(
            meta_summary,
            "target_status",
            n_observations,
        )
        meta_peer_valid = _validity_markers(
            meta_summary,
            "peer_valid",
            n_observations,
        )
        meta_peer_status = _status_markers(
            meta_summary,
            "peer_status",
            n_observations,
        )
        meta_dual_valid = _validity_markers(
            meta_summary,
            "dual_valid",
            n_observations,
        )
        meta_dual_status = _status_markers(
            meta_summary,
            "dual_status",
            n_observations,
        )
        meta_phase_one, meta_phase_one_backend, meta_phase_one_raw = (
            _phase_one_statuses(
                metafrontier,
                n_observations,
                component="metafrontier",
            )
        )
        phase_one_solves, phase_two_solves, solver_calls = _solver_counters(
            metafrontier
        )

        group_efficiency = np.full(n_observations, np.nan, dtype=np.float64)
        group_factor = np.full(n_observations, np.nan, dtype=np.float64)
        group_status = np.full(n_observations, "not_solved", dtype=object)
        group_backend_status = np.full(
            n_observations,
            "not_solved",
            dtype=object,
        )
        group_raw_status = np.full(n_observations, "not_solved", dtype=object)
        group_reference_size = np.zeros(n_observations, dtype=np.int64)
        group_score_valid = np.full(n_observations, False, dtype=object)
        group_score_status = np.full(n_observations, "not_solved", dtype=object)
        group_completion_valid = np.full(n_observations, False, dtype=object)
        group_completion_status = np.full(
            n_observations,
            "not_solved",
            dtype=object,
        )
        group_target_valid = np.full(n_observations, False, dtype=object)
        group_target_status = np.full(n_observations, "not_solved", dtype=object)
        group_peer_valid = np.full(n_observations, False, dtype=object)
        group_peer_status = np.full(n_observations, "not_solved", dtype=object)
        group_dual_valid = np.full(n_observations, False, dtype=object)
        group_dual_status = np.full(n_observations, "not_solved", dtype=object)

        group_slacks: list[pd.DataFrame] = []
        group_targets: list[pd.DataFrame] = []
        group_intensities: list[pd.DataFrame] = []
        group_duals: list[pd.DataFrame] = []
        group_diagnostics: list[pd.DataFrame] = []

        for group_label, positions in layout:
            group_data = _group_view(data, positions)
            fitted = self._radial_model().fit(group_data)
            fitted_summary = fitted.summary().reset_index(drop=True)
            group_efficiency[positions] = fitted_summary["efficiency"].to_numpy(
                dtype=np.float64
            )
            group_factor[positions] = fitted_summary["score"].to_numpy(dtype=np.float64)
            group_score_valid[positions] = _validity_markers(
                fitted_summary,
                "score_valid",
                len(positions),
            )
            group_score_status[positions] = _status_markers(
                fitted_summary,
                "score_status",
                len(positions),
            )
            group_completion_valid[positions] = _validity_markers(
                fitted_summary,
                "completion_valid",
                len(positions),
            )
            group_completion_status[positions] = _status_markers(
                fitted_summary,
                "completion_status",
                len(positions),
            )
            group_target_valid[positions] = _validity_markers(
                fitted_summary,
                "target_valid",
                len(positions),
            )
            group_target_status[positions] = _status_markers(
                fitted_summary,
                "target_status",
                len(positions),
            )
            group_peer_valid[positions] = _validity_markers(
                fitted_summary,
                "peer_valid",
                len(positions),
            )
            group_peer_status[positions] = _status_markers(
                fitted_summary,
                "peer_status",
                len(positions),
            )
            group_dual_valid[positions] = _validity_markers(
                fitted_summary,
                "dual_valid",
                len(positions),
            )
            group_dual_status[positions] = _status_markers(
                fitted_summary,
                "dual_status",
                len(positions),
            )
            fitted_phase_one, fitted_phase_one_backend, fitted_phase_one_raw = (
                _phase_one_statuses(
                    fitted,
                    len(positions),
                    component="group",
                )
            )
            group_status[positions] = fitted_phase_one
            group_backend_status[positions] = fitted_phase_one_backend
            group_raw_status[positions] = fitted_phase_one_raw
            group_reference_size[positions] = len(positions)
            child_phase_one, child_phase_two, child_total = _solver_counters(fitted)
            phase_one_solves += child_phase_one
            phase_two_solves += child_phase_two
            solver_calls += child_total

            for source, destination in (
                (fitted.slacks, group_slacks),
                (fitted.targets, group_targets),
                (fitted.intensities, group_intensities),
                (fitted.duals, group_duals),
                (fitted.diagnostics, group_diagnostics),
            ):
                annotated = _annotate_component_frame(
                    source,
                    data=data,
                    group_by_key=group_by_key,
                    benchmark_level="group",
                )
                if not annotated.empty:
                    annotated["group"] = group_label
                destination.append(annotated)

        meta_efficiency = meta_summary["efficiency"].to_numpy(dtype=np.float64)
        meta_factor = meta_summary["score"].to_numpy(dtype=np.float64)
        meta_status = meta_phase_one

        component_optimal = (group_status == "optimal") & (meta_status == "optimal")
        component_score_valid = _explicit_true(group_score_valid) & _explicit_true(
            meta_score_valid
        )
        component_values_valid = (
            component_score_valid
            & np.isfinite(group_efficiency)
            & np.isfinite(meta_efficiency)
            & np.isfinite(group_factor)
            & np.isfinite(meta_factor)
            & (group_factor > 0.0)
            & (meta_factor > 0.0)
            & (group_efficiency >= 0.0)
            & (meta_efficiency >= 0.0)
        )
        # A radial efficiency is a multiplicative economic quantity, not a
        # residual.  Any finite, strictly positive group efficiency is a
        # mathematically valid denominator, even when its magnitude is below
        # the feasibility tolerance used by the underlying LP certificates.
        denominator_valid = component_values_valid & (group_efficiency > 0.0)
        nesting_violation = np.where(
            component_values_valid,
            np.maximum(meta_efficiency - group_efficiency, 0.0),
            np.nan,
        )
        certificate_tolerance = max(10.0 * self.tolerance, 1.0e-9)

        raw_ratio = np.full(n_observations, np.nan, dtype=np.float64)
        raw_ratio[denominator_valid] = (
            meta_efficiency[denominator_valid] / group_efficiency[denominator_valid]
        )
        ratio = raw_ratio.copy()
        ratio[
            np.isclose(
                ratio,
                1.0,
                rtol=0.0,
                atol=certificate_tolerance,
            )
        ] = 1.0

        ratio_bound_violation = np.where(
            denominator_valid,
            np.maximum.reduce(
                (
                    np.maximum(-raw_ratio, 0.0),
                    np.maximum(raw_ratio - 1.0, 0.0),
                    np.zeros(n_observations, dtype=np.float64),
                )
            ),
            np.nan,
        )
        reconstruction_residual = np.where(
            denominator_valid,
            np.abs(meta_efficiency - group_efficiency * raw_ratio),
            np.nan,
        )
        decomposition_certified = (
            denominator_valid
            & (raw_ratio > 0.0)
            & (nesting_violation <= certificate_tolerance)
            & (ratio_bound_violation <= certificate_tolerance)
            & (reconstruction_residual <= certificate_tolerance)
        )

        ratio[~decomposition_certified] = np.nan
        solver_status = np.full(n_observations, "component_failure", dtype=object)
        solver_status[component_optimal & ~component_values_valid] = "invalid_component"
        solver_status[component_values_valid & ~denominator_valid] = "undefined_ratio"
        solver_status[denominator_valid & ~decomposition_certified] = (
            "certificate_failure"
        )
        solver_status[decomposition_certified] = "optimal"
        score_status = np.full(
            n_observations,
            "unavailable_component_solver_failure",
            dtype=object,
        )
        score_status[component_optimal & ~component_values_valid] = (
            "unavailable_uncertified_component_score"
        )
        score_status[component_values_valid & ~denominator_valid] = (
            "undefined_nonpositive_group_efficiency"
        )
        score_status[denominator_valid & ~decomposition_certified] = (
            "unavailable_failed_decomposition_certificate"
        )
        score_status[decomposition_certified] = "defined"

        is_group_efficient = pd.array(
            [
                (
                    pd.NA
                    if not optimal or not math.isfinite(value)
                    else bool(abs(value - 1.0) <= self.tolerance)
                )
                for optimal, value in zip(
                    _explicit_true(group_score_valid),
                    group_efficiency,
                    strict=True,
                )
            ],
            dtype="boolean",
        )
        is_meta_efficient = pd.array(
            [
                (
                    pd.NA
                    if not optimal or not math.isfinite(value)
                    else bool(abs(value - 1.0) <= self.tolerance)
                )
                for optimal, value in zip(
                    _explicit_true(meta_score_valid),
                    meta_efficiency,
                    strict=True,
                )
            ],
            dtype="boolean",
        )
        is_meta_strongly_efficient = pd.array(
            meta_summary["is_efficient"],
            dtype="boolean",
        )

        summary = pd.DataFrame(
            {
                "dmu_id": data.dmu_ids,
                "period": (
                    np.full(n_observations, None, dtype=object)
                    if data.periods is None
                    else data.periods
                ),
                "group": data.groups,
                "score": ratio,
                "score_valid": pd.array(
                    decomposition_certified,
                    dtype="boolean",
                ),
                "score_status": score_status,
                "efficiency": meta_efficiency,
                "distance": np.nan,
                "is_efficient": is_meta_strongly_efficient,
                "is_group_efficient": is_group_efficient,
                "is_metafrontier_efficient": is_meta_efficient,
                "solver_status": solver_status,
                "model_family": "radial_metafrontier",
                "orientation": self.orientation.value,
                "returns_to_scale": self.returns_to_scale.value,
                "group_efficiency": group_efficiency,
                "metafrontier_efficiency": meta_efficiency,
                "meta_efficiency": meta_efficiency,
                "metatechnology_ratio": ratio,
                "technology_gap_ratio": ratio,
                "raw_metatechnology_ratio": raw_ratio,
                "group_radial_factor": group_factor,
                "metafrontier_radial_factor": meta_factor,
                "group_theta": (
                    group_factor
                    if self.orientation is Orientation.INPUT
                    else np.full(n_observations, np.nan)
                ),
                "meta_theta": (
                    meta_factor
                    if self.orientation is Orientation.INPUT
                    else np.full(n_observations, np.nan)
                ),
                "group_phi": (
                    group_factor
                    if self.orientation is Orientation.OUTPUT
                    else np.full(n_observations, np.nan)
                ),
                "meta_phi": (
                    meta_factor
                    if self.orientation is Orientation.OUTPUT
                    else np.full(n_observations, np.nan)
                ),
                "group_solver_status": group_status,
                "metafrontier_solver_status": meta_status,
                "group_backend_solver_status": group_backend_status,
                "group_raw_solver_status": group_raw_status,
                "metafrontier_backend_solver_status": meta_phase_one_backend,
                "metafrontier_raw_solver_status": meta_phase_one_raw,
                "meta_backend_solver_status": meta_phase_one_backend,
                "meta_raw_solver_status": meta_phase_one_raw,
                "group_score_valid": pd.array(
                    group_score_valid,
                    dtype="boolean",
                ),
                "group_score_status": group_score_status,
                "metafrontier_score_valid": pd.array(
                    meta_score_valid,
                    dtype="boolean",
                ),
                "metafrontier_score_status": meta_score_status,
                "meta_score_valid": pd.array(meta_score_valid, dtype="boolean"),
                "meta_score_status": meta_score_status,
                "group_completion_valid": pd.array(
                    group_completion_valid,
                    dtype="boolean",
                ),
                "group_completion_status": group_completion_status,
                "metafrontier_completion_valid": pd.array(
                    meta_completion_valid,
                    dtype="boolean",
                ),
                "metafrontier_completion_status": meta_completion_status,
                "meta_completion_valid": pd.array(
                    meta_completion_valid,
                    dtype="boolean",
                ),
                "meta_completion_status": meta_completion_status,
                "group_target_valid": pd.array(
                    group_target_valid,
                    dtype="boolean",
                ),
                "group_target_status": group_target_status,
                "metafrontier_target_valid": pd.array(
                    meta_target_valid,
                    dtype="boolean",
                ),
                "metafrontier_target_status": meta_target_status,
                "meta_target_valid": pd.array(
                    meta_target_valid,
                    dtype="boolean",
                ),
                "meta_target_status": meta_target_status,
                "group_peer_valid": pd.array(group_peer_valid, dtype="boolean"),
                "group_peer_status": group_peer_status,
                "metafrontier_peer_valid": pd.array(
                    meta_peer_valid,
                    dtype="boolean",
                ),
                "metafrontier_peer_status": meta_peer_status,
                "meta_peer_valid": pd.array(meta_peer_valid, dtype="boolean"),
                "meta_peer_status": meta_peer_status,
                "group_dual_valid": pd.array(group_dual_valid, dtype="boolean"),
                "group_dual_status": group_dual_status,
                "metafrontier_dual_valid": pd.array(
                    meta_dual_valid,
                    dtype="boolean",
                ),
                "metafrontier_dual_status": meta_dual_status,
                "meta_dual_valid": pd.array(meta_dual_valid, dtype="boolean"),
                "meta_dual_status": meta_dual_status,
                "group_reference_size": group_reference_size,
                "metafrontier_reference_size": n_observations,
                "ratio_denominator_valid": denominator_valid,
                "component_values_valid": component_values_valid,
                "nesting_violation": nesting_violation,
                "ratio_bound_violation": ratio_bound_violation,
                "reconstruction_residual": reconstruction_residual,
                "decomposition_certified": decomposition_certified,
            }
        )

        component_rows: list[dict[str, Any]] = []
        for position in range(n_observations):
            common = {
                "dmu_id": data.dmu_ids[position],
                "period": (None if data.periods is None else data.periods[position]),
                "group": data.groups[position],
            }
            component_rows.extend(
                [
                    {
                        **common,
                        "component": "group_efficiency",
                        "value": group_efficiency[position],
                        "identity_role": "within_group_performance",
                    },
                    {
                        **common,
                        "component": "metatechnology_ratio",
                        "value": ratio[position],
                        "identity_role": "group_opportunity_proximity",
                    },
                    {
                        **common,
                        "component": "metafrontier_efficiency",
                        "value": meta_efficiency[position],
                        "identity_role": "reconstructed_overall_performance",
                    },
                ]
            )

        meta_frames = {
            "slacks": _annotate_component_frame(
                metafrontier.slacks,
                data=data,
                group_by_key=group_by_key,
                benchmark_level="metafrontier",
            ),
            "targets": _annotate_component_frame(
                metafrontier.targets,
                data=data,
                group_by_key=group_by_key,
                benchmark_level="metafrontier",
            ),
            "intensities": _annotate_component_frame(
                metafrontier.intensities,
                data=data,
                group_by_key=group_by_key,
                benchmark_level="metafrontier",
            ),
            "duals": _annotate_component_frame(
                metafrontier.duals,
                data=data,
                group_by_key=group_by_key,
                benchmark_level="metafrontier",
            ),
            "diagnostics": _annotate_component_frame(
                metafrontier.diagnostics,
                data=data,
                group_by_key=group_by_key,
                benchmark_level="metafrontier",
            ),
        }

        diagnostics = _concat_frames([*group_diagnostics, meta_frames["diagnostics"]])

        group_sizes = [
            {"group": str(label), "observations": len(positions)}
            for label, positions in layout
        ]
        metafrontier_construction = (
            "pooled_conic"
            if self.returns_to_scale is ReturnsToScale.CRS
            else "pooled_convex"
        )
        group_frontier_construction = (
            "separate_conic_envelopment_by_declared_group"
            if self.returns_to_scale is ReturnsToScale.CRS
            else "separate_convex_envelopment_by_declared_group"
        )
        temporal_information = (
            "all_study_periods_pooled"
            if data.is_panel
            else "cross_section_not_applicable"
        )

        return DEAResult(
            summary_frame=summary,
            slacks=_concat_frames([*group_slacks, meta_frames["slacks"]]),
            targets=_concat_frames([*group_targets, meta_frames["targets"]]),
            intensities=_concat_frames(
                [*group_intensities, meta_frames["intensities"]]
            ),
            duals=_concat_frames([*group_duals, meta_frames["duals"]]),
            components=pd.DataFrame(component_rows),
            diagnostics=diagnostics,
            metadata={
                **registry_metadata(
                    self._registry_method_id,
                    {
                        "context": {
                            "purpose": (
                                "separate_within_group_performance_from_"
                                "between_group_opportunity_proximity"
                            ),
                            "sample": ("panel" if data.is_panel else "cross_section"),
                            "group_labels": "declared_ex_ante",
                        },
                        "graph": {"kind": "black_box"},
                        "data_roles": {
                            "inputs": "productive_resources",
                            "outputs": "desirable_services",
                            "bad_outputs": "excluded",
                            "group": "declared_technology_group",
                            **data_role_schema(data),
                        },
                        "technology": {
                            "family": "radial_dea_metafrontier",
                            "group_frontiers": group_frontier_construction,
                            "metafrontier": metafrontier_construction,
                            "returns_to_scale": self.returns_to_scale.value,
                            "disposal": "ordinary_free",
                        },
                        "estimator": {
                            "estimator_id": "estimator.full.dea",
                            "kind": "full_frontier",
                            "family": "dea_envelopment",
                        },
                        "reference": {
                            "comparison_population": {
                                "group_frontier": "same_declared_group",
                                "metafrontier": "all_declared_groups",
                            },
                            "temporal_information_set": temporal_information,
                            "self_membership": "included",
                            "evaluation_exclusions": "none",
                        },
                        "performance": {
                            "family": "radial_farrell_efficiency",
                            "orientation": self.orientation.value,
                            "slack_refinement": self.compute_slacks,
                        },
                        "valuation": {"kind": "none"},
                        "evaluation_protocol": {
                            "kind": "matched_group_meta_appraisal",
                            "group_assignment": "fixed_before_fit",
                            "secondary_objective": (
                                "maximize_row_scaled_slacks"
                                if self.compute_slacks
                                else "none"
                            ),
                        },
                        "analysis": {
                            "kind": "radial_metafrontier_decomposition",
                            "identity": (
                                "metafrontier_efficiency = group_efficiency "
                                "* metatechnology_ratio"
                            ),
                            "ratio_alias": "technology_gap_ratio",
                            "interpretation": "accounting_not_causal",
                            "causal_effects": "not_identified",
                            "transition_feasibility": "not_inferred",
                        },
                        "uncertainty": {"kind": "deterministic"},
                    },
                ),
                "model_family": "radial_metafrontier",
                "orientation": self.orientation.value,
                "returns_to_scale": self.returns_to_scale.value,
                "native_score": "metatechnology_ratio",
                "score_direction": "higher_means_group_frontier_closer_to_meta",
                "efficiency_column": "metafrontier_efficiency",
                "identity": (
                    "metafrontier_efficiency = group_efficiency * metatechnology_ratio"
                ),
                "historical_aliases": {
                    "technology_gap_ratio": "metatechnology_ratio",
                    "TGR": "metatechnology_ratio",
                    "MTR": "metatechnology_ratio",
                },
                "metafrontier_construction": metafrontier_construction,
                "group_assignment": "declared_ex_ante",
                "temporal_information_set": temporal_information,
                "group_count": len(layout),
                "group_sizes": group_sizes,
                "compute_slacks": self.compute_slacks,
                "solver": self.solver.name,
                "primary_solver_calls": phase_one_solves,
                "secondary_solver_calls": phase_two_solves,
                "phase_one_solver_calls": phase_one_solves,
                "phase_two_solver_calls": phase_two_solves,
                "solver_calls": solver_calls,
                "phase_one_solves": phase_one_solves,
                "phase_two_solves": phase_two_solves,
                "additional_solver_calls": 0,
                "certificate_extra_solver_calls": 0,
                "compiled_reference_sets": len(layout) + 1,
                "tolerance": self.tolerance,
                "certificate_tolerance": certificate_tolerance,
                "peer_tolerance": self.peer_tolerance,
                "targets_use_unthresholded_intensities": True,
                "peer_threshold_scope": "reporting_only",
                "postsolve_certificate": {
                    "component_certificate": (
                        "delegated_to_certified_radial_group_and_meta_programs"
                    ),
                    "decomposition_certificate": (
                        "nesting_ratio_bounds_and_multiplicative_identity"
                    ),
                    "score_release_policy": (
                        "requires_both_component_scores_and_decomposition_certificate"
                    ),
                    "failure_scope": "per_observation_and_component",
                    "additional_solver_calls": 0,
                    "certificate_extra_solver_calls": 0,
                },
                "source": {
                    "authors": "O'Donnell, Rao, and Battese",
                    "year": 2008,
                    "doi": "10.1007/s00181-007-0119-4",
                    "equations": [7, 8, 9, 10, 31, 33],
                    "published_application_reproduced": False,
                    "validation_basis": (
                        "analytic_oracle_and_independent_equation_compiler"
                    ),
                },
            },
        )


MetafrontierDEA = RadialMetafrontierDEA

__all__ = ["MetafrontierDEA", "RadialMetafrontierDEA"]
