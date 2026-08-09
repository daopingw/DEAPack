"""Radial efficiency on a non-convex free-disposal hull."""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Integral
from typing import Any

import numpy as np
import pandas as pd

from .._registry import (
    data_role_schema,
    registry_metadata,
)
from .._registry import (
    reference_spec as registry_reference_spec,
)
from ..data import DEAData
from ..enums import Orientation, SolverStatus, parse_enum
from ..exceptions import DataValidationError, ModelSpecificationError
from ..results import DEAResult
from ..specs import ReferenceSpec
from ..technology import build_reference_plan
from ._common import clean_small


@dataclass(frozen=True, slots=True)
class _FDHScan:
    """Direct-scan outcome for one evaluated observation."""

    scores: np.ndarray
    best: float
    candidate_count: int
    tied_local_rows: np.ndarray


class FreeDisposalHullDEA:
    """Input- or output-oriented radial free-disposal-hull efficiency.

    The empirical technology contains observed activities and the plans
    obtained from them by using more inputs or producing fewer desirable
    outputs. It does not convexify, average, or rescale observed activities.
    The model therefore has no returns-to-scale parameter.

    Parameters
    ----------
    orientation:
        ``"input"`` finds the smallest common input factor ``theta`` while
        maintaining the evaluated output vector. ``"output"`` finds the
        largest common output factor ``phi`` without using more inputs.
    reference:
        Reference-set policy shared with the other DEAPack models.
    compute_slacks:
        If true, choose one observed peer lexicographically from the radial
        optima by maximizing the unweighted sum of residual input and output
        improvements. All radial ties remain available in ``result.peers``.
    tolerance:
        Absolute numerical tolerance used for efficiency and slack
        classification.
    tie_tolerance:
        Absolute and relative tolerance used to identify alternate radial
        optima for reporting. It does not widen the candidates admitted to
        strong slack completion, which always uses ``tolerance``. Defaults to
        ``tolerance``.
    chunk_size:
        Maximum number of reference observations processed in one vectorized
        dominance block. This bounds temporary-array memory without changing
        the exact scan.
    """

    _registry_method_id = "static.radial.fdh"

    def __init__(
        self,
        *,
        orientation: Orientation | str = Orientation.INPUT,
        reference: ReferenceSpec | str | None = None,
        compute_slacks: bool = True,
        tolerance: float = 1e-7,
        tie_tolerance: float | None = None,
        chunk_size: int = 4096,
    ) -> None:
        self.orientation = parse_enum(orientation, Orientation, "orientation")
        self.reference = (
            ReferenceSpec()
            if reference is None
            else reference
            if isinstance(reference, ReferenceSpec)
            else ReferenceSpec(kind=reference)
        )
        self.compute_slacks = bool(compute_slacks)
        if tolerance <= 0:
            raise ValueError("tolerance must be positive")
        self.tolerance = float(tolerance)
        self.tie_tolerance = (
            self.tolerance if tie_tolerance is None else float(tie_tolerance)
        )
        if self.tie_tolerance <= 0:
            raise ValueError("tie_tolerance must be positive")
        if isinstance(chunk_size, bool) or not isinstance(chunk_size, Integral):
            raise TypeError("chunk_size must be a positive integer")
        if chunk_size <= 0:
            raise ValueError("chunk_size must be a positive integer")
        self.chunk_size = int(chunk_size)

    def _validate_data(self, data: DEAData) -> None:
        data.ensure_nonnegative()
        if data.bad_outputs is not None:
            raise ModelSpecificationError(
                "FreeDisposalHullDEA does not infer how undesirable outputs "
                "are disposed. Use an explicit environmental technology."
            )
        if np.any(data.inputs.sum(axis=1) <= 0):
            raise DataValidationError(
                "each observation needs at least one strictly positive input"
            )
        if np.any(data.outputs.sum(axis=1) <= 0):
            raise DataValidationError(
                "each observation needs at least one strictly positive output"
            )

    def _scan(
        self,
        reference_inputs: np.ndarray,
        reference_outputs: np.ndarray,
        x_o: np.ndarray,
        y_o: np.ndarray,
    ) -> _FDHScan | None:
        """Evaluate all single-observation FDH comparators in bounded memory."""
        n_reference = reference_inputs.shape[0]
        scores = np.full(n_reference, np.nan, dtype=np.float64)

        if self.orientation is Orientation.INPUT:
            positive_denominators = x_o > 0
            zero_denominators = ~positive_denominators
            for start in range(0, n_reference, self.chunk_size):
                stop = min(start + self.chunk_size, n_reference)
                x_block = reference_inputs[start:stop]
                y_block = reference_outputs[start:stop]
                eligible = np.all(y_block >= y_o, axis=1)
                if np.any(zero_denominators):
                    eligible &= np.all(
                        x_block[:, zero_denominators] == 0.0,
                        axis=1,
                    )
                local_scores = np.full(stop - start, np.nan, dtype=np.float64)
                if np.any(eligible):
                    ratios = (
                        x_block[eligible][:, positive_denominators]
                        / x_o[positive_denominators]
                    )
                    local_scores[eligible] = np.max(ratios, axis=1)
                scores[start:stop] = local_scores
        else:
            positive_denominators = y_o > 0
            for start in range(0, n_reference, self.chunk_size):
                stop = min(start + self.chunk_size, n_reference)
                x_block = reference_inputs[start:stop]
                y_block = reference_outputs[start:stop]
                eligible = np.all(x_block <= x_o, axis=1)
                local_scores = np.full(stop - start, np.nan, dtype=np.float64)
                if np.any(eligible):
                    ratios = (
                        y_block[eligible][:, positive_denominators]
                        / y_o[positive_denominators]
                    )
                    local_scores[eligible] = np.min(ratios, axis=1)
                scores[start:stop] = local_scores

        candidate_count = int(np.count_nonzero(np.isfinite(scores)))
        if candidate_count == 0:
            return None
        if self.orientation is Orientation.INPUT:
            best = float(np.nanmin(scores))
        else:
            best = float(np.nanmax(scores))
        tied = np.flatnonzero(
            np.isfinite(scores)
            & np.isclose(
                scores,
                best,
                rtol=self.tie_tolerance,
                atol=self.tie_tolerance,
            )
        ).astype(np.int64, copy=False)
        tied.setflags(write=False)
        return _FDHScan(scores, best, candidate_count, tied)

    def _slacks_for_peers(
        self,
        reference_inputs: np.ndarray,
        reference_outputs: np.ndarray,
        candidate_local_rows: np.ndarray,
        x_o: np.ndarray,
        y_o: np.ndarray,
        factor: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        peer_inputs = reference_inputs[candidate_local_rows]
        peer_outputs = reference_outputs[candidate_local_rows]
        if self.orientation is Orientation.INPUT:
            input_slacks = factor * x_o - peer_inputs
            output_slacks = peer_outputs - y_o
        else:
            input_slacks = x_o - peer_inputs
            output_slacks = peer_outputs - factor * y_o
        input_slacks = clean_small(input_slacks, self.tolerance)
        output_slacks = clean_small(output_slacks, self.tolerance)
        return np.maximum(input_slacks, 0.0), np.maximum(output_slacks, 0.0)

    def _reference_self_inclusion(
        self,
        rows_by_observation: tuple[np.ndarray, ...],
    ) -> str:
        included = np.fromiter(
            (
                bool(np.any(rows == observation))
                for observation, rows in enumerate(rows_by_observation)
            ),
            dtype=bool,
            count=len(rows_by_observation),
        )
        if np.all(included):
            return "all"
        if np.any(included):
            return "some"
        return "none"

    def fit(self, data: DEAData) -> DEAResult:
        """Estimate radial efficiency against a free-disposal hull."""
        self._validate_data(data)
        reference_plan = build_reference_plan(data, self.reference)

        summary_rows: list[dict[str, Any]] = []
        slack_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []

        compiled: dict[int, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}

        for observation in range(data.n_dmus):
            set_id = reference_plan.set_id_for(observation)
            reference_rows = reference_plan.rows_for(observation)
            reference = compiled.get(set_id)
            if reference is None:
                reference = (
                    reference_rows,
                    data.inputs[reference_rows],
                    data.outputs[reference_rows],
                )
                compiled[set_id] = reference
            rows, reference_inputs, reference_outputs = reference
            dmu_id = data.dmu_ids[observation]
            period = None if data.periods is None else data.periods[observation]
            x_o = data.inputs[observation]
            y_o = data.outputs[observation]
            scan = self._scan(reference_inputs, reference_outputs, x_o, y_o)

            if scan is None:
                diagnostic_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "phase": 1,
                        "solver_status": SolverStatus.INFEASIBLE.value,
                        "message": (
                            "no single reference activity satisfies the "
                            f"{self.orientation.value}-oriented dominance "
                            "conditions"
                        ),
                        "iterations": 0,
                        "max_primal_violation": np.nan,
                        "algorithm": "chunked_dominance_ratio_scan",
                        "candidate_count": 0,
                        "tied_peer_count": 0,
                    }
                )
                summary_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "score": np.nan,
                        "efficiency": np.nan,
                        "distance": np.nan,
                        "is_efficient": pd.NA,
                        "is_radially_efficient": pd.NA,
                        "is_within_reference_technology": False,
                        "solver_status": SolverStatus.INFEASIBLE.value,
                        "model_family": "fdh_radial",
                        "orientation": self.orientation.value,
                        "returns_to_scale": "not_imposed",
                        "reference_size": int(rows.size),
                        "candidate_count": 0,
                        "tied_peer_count": 0,
                        "max_slack": np.nan,
                    }
                )
                continue

            factor = scan.best
            if self.orientation is Orientation.INPUT:
                efficiency = factor
                within_reference = bool(factor <= 1.0 + self.tolerance)
            else:
                efficiency = np.nan if factor <= 0.0 else 1.0 / factor
                within_reference = bool(factor >= 1.0 - self.tolerance)

            is_radially_efficient: bool | Any
            if within_reference:
                is_radially_efficient = bool(
                    np.isfinite(efficiency) and abs(efficiency - 1.0) <= self.tolerance
                )
            else:
                is_radially_efficient = pd.NA

            if self.compute_slacks:
                completion_local_rows = np.flatnonzero(
                    np.isfinite(scan.scores)
                    & np.isclose(
                        scan.scores,
                        factor,
                        rtol=self.tolerance,
                        atol=self.tolerance,
                    )
                ).astype(np.int64, copy=False)
                completion_input_slacks, completion_output_slacks = (
                    self._slacks_for_peers(
                        reference_inputs,
                        reference_outputs,
                        completion_local_rows,
                        x_o,
                        y_o,
                        factor,
                    )
                )
                slack_totals = completion_input_slacks.sum(
                    axis=1
                ) + completion_output_slacks.sum(axis=1)
                primary_completion_position = int(np.argmax(slack_totals))
                primary_local_row = int(
                    completion_local_rows[primary_completion_position]
                )
            else:
                primary_local_row = int(scan.tied_local_rows[0])

            for alternative_rank, local_row in enumerate(
                scan.tied_local_rows,
                start=1,
            ):
                reference_position = int(rows[local_row])
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
                        "lambda": 1.0,
                        "alternative_rank": alternative_rank,
                        "is_primary": bool(local_row == primary_local_row),
                        "peer_score": float(scan.scores[local_row]),
                    }
                )

            diagnostic_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "phase": 1,
                    "solver_status": SolverStatus.OPTIMAL.value,
                    "message": (
                        "direct dominance scan completed; peer rows are "
                        "alternate single-activity optima"
                    ),
                    "iterations": 0,
                    "max_primal_violation": 0.0,
                    "algorithm": "chunked_dominance_ratio_scan",
                    "candidate_count": scan.candidate_count,
                    "tied_peer_count": int(scan.tied_local_rows.size),
                }
            )

            max_slack = np.nan
            is_efficient: bool | Any = pd.NA
            if self.compute_slacks:
                input_slacks = completion_input_slacks[primary_completion_position]
                output_slacks = completion_output_slacks[primary_completion_position]
                max_slack = float(
                    max(
                        input_slacks.max(initial=0.0),
                        output_slacks.max(initial=0.0),
                    )
                )
                if within_reference:
                    is_efficient = bool(
                        is_radially_efficient and max_slack <= self.tolerance
                    )

                primary_reference_position = int(rows[primary_local_row])
                input_targets = data.inputs[primary_reference_position]
                output_targets = data.outputs[primary_reference_position]
                for role, names, observed, targets, slacks in (
                    (
                        "input",
                        data.input_names,
                        x_o,
                        input_targets,
                        input_slacks,
                    ),
                    (
                        "output",
                        data.output_names,
                        y_o,
                        output_targets,
                        output_slacks,
                    ),
                ):
                    for variable, value, target, slack in zip(
                        names,
                        observed,
                        targets,
                        slacks,
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
                            }
                        )
                        slack_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": period,
                                "role": role,
                                "variable": variable,
                                "slack": float(slack),
                            }
                        )
                diagnostic_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "phase": 2,
                        "solver_status": SolverStatus.OPTIMAL.value,
                        "message": (
                            "selected one radial peer by maximum unweighted "
                            "residual improvement"
                        ),
                        "iterations": 0,
                        "max_primal_violation": 0.0,
                        "algorithm": "lexicographic_peer_scan",
                        "candidate_count": int(completion_local_rows.size),
                        "tied_peer_count": int(
                            np.count_nonzero(
                                np.isclose(
                                    slack_totals,
                                    slack_totals[primary_completion_position],
                                    rtol=self.tolerance,
                                    atol=self.tolerance,
                                )
                            )
                        ),
                    }
                )

            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "score": factor,
                    "efficiency": efficiency,
                    "distance": np.nan,
                    "is_efficient": is_efficient,
                    "is_radially_efficient": is_radially_efficient,
                    "is_within_reference_technology": within_reference,
                    "solver_status": SolverStatus.OPTIMAL.value,
                    "model_family": "fdh_radial",
                    "orientation": self.orientation.value,
                    "returns_to_scale": "not_imposed",
                    "reference_size": int(rows.size),
                    "candidate_count": scan.candidate_count,
                    "tied_peer_count": int(scan.tied_local_rows.size),
                    "max_slack": max_slack,
                }
            )

        self_inclusion = self._reference_self_inclusion(
            reference_plan.rows_by_observation
        )
        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
            slacks=pd.DataFrame(slack_rows),
            targets=pd.DataFrame(target_rows),
            intensities=pd.DataFrame(intensity_rows),
            diagnostics=pd.DataFrame(diagnostic_rows),
            metadata={
                **registry_metadata(
                    self._registry_method_id,
                    {
                        "context": {
                            "purpose": "operating_performance_benchmarking",
                            "sample": "panel" if data.is_panel else "cross_section",
                        },
                        "graph": {"kind": "black_box"},
                        "data_roles": {
                            "inputs": "controllable_resources",
                            "outputs": "desirable_services",
                            "bad_outputs": "excluded",
                            **data_role_schema(data),
                        },
                        "technology": {
                            "family": "free_disposal_hull",
                            "convex": False,
                            "activity_aggregation": "single_observed_activity",
                            "scale_replication": "not_imposed",
                            "disposal": "ordinary_free",
                        },
                        "estimator": {
                            "estimator_id": "estimator.full.fdh",
                            "kind": "full_frontier",
                            "family": "fdh",
                        },
                        "reference": {
                            **registry_reference_spec(
                                self.reference, reference_plan.kind
                            ),
                            "self_inclusion": self_inclusion,
                        },
                        "performance": {
                            "family": "radial",
                            "orientation": self.orientation.value,
                            "slack_refinement": self.compute_slacks,
                        },
                        "valuation": {"kind": "none"},
                        "evaluation_protocol": {
                            "kind": (
                                "fixed_reference_appraisal"
                                if reference_plan.kind.value == "custom"
                                else "self_appraisal"
                            ),
                            "alternate_radial_optima": "report_all_single_peers",
                            "secondary_objective": (
                                "maximize_unweighted_slacks"
                                if self.compute_slacks
                                else "none"
                            ),
                        },
                        "analysis": {"kind": "direct_model_fit"},
                        "uncertainty": {"kind": "deterministic"},
                    },
                ),
                "model_family": "fdh_radial",
                "orientation": self.orientation.value,
                "technology": "free_disposal_hull",
                "convex": False,
                "returns_to_scale": "not_imposed",
                "reference_kind": reference_plan.kind.value,
                "reference_self_inclusion": self_inclusion,
                "native_score": (
                    "theta" if self.orientation is Orientation.INPUT else "phi"
                ),
                "efficiency_transform": (
                    "identity"
                    if self.orientation is Orientation.INPUT
                    else "reciprocal_positive_factor"
                ),
                "slack_phase": (
                    "maximize_unweighted_sum" if self.compute_slacks else "not_computed"
                ),
                "compute_slacks": self.compute_slacks,
                "solver": "none_direct_dominance_scan",
                "algorithm": "chunked_dominance_ratio_scan",
                "intensity_semantics": (
                    "each row is an alternative binary activation; tied FDH "
                    "peers are not a convex combination"
                ),
                "tolerance": self.tolerance,
                "tie_tolerance": self.tie_tolerance,
                "chunk_size": self.chunk_size,
                "compiled_reference_sets": reference_plan.unique_reference_sets,
            },
        )


class FDH(FreeDisposalHullDEA):
    """Discoverability alias for :class:`FreeDisposalHullDEA`."""


__all__ = ["FDH", "FreeDisposalHullDEA"]
