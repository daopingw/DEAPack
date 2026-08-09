"""Tone's non-separable undesirable-output slacks-based measure."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from numbers import Real
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix, eye, hstack, vstack

from .._registry import data_role_schema, registry_metadata
from .._registry import reference_spec as registry_reference_spec
from ..data import DEAData
from ..enums import ReturnsToScale, SolverStatus, parse_enum
from ..exceptions import ModelSpecificationError
from ..results import DEAResult
from ..solvers import LinearProgram, LPSolution, LPSolver, SciPyHiGHSSolver
from ..specs import ReferenceSpec, SolverOptions
from ..technology import build_reference_plan
from ._common import (
    CompiledReference,
    clean_small,
    compile_reference,
    get_or_compile_reference,
    join_optional_rows,
    join_optional_values,
)


def _declared_names(values: Sequence[str] | str, field: str) -> tuple[str, ...]:
    names = (values,) if isinstance(values, str) else tuple(values)
    if not names:
        raise ModelSpecificationError(f"{field} must declare at least one variable")
    if any(
        not isinstance(name, str) or not name or name != name.strip() for name in names
    ):
        raise ModelSpecificationError(
            f"{field} must contain non-empty exact variable names"
        )
    if len(set(names)) != len(names):
        raise ModelSpecificationError(f"{field} contains duplicate variables")
    return names


@dataclass(frozen=True, slots=True)
class _OutputPartition:
    """Column locations for Tone's declared separable/non-separable blocks."""

    separable_good: np.ndarray
    nonseparable_good: np.ndarray
    separable_bad: np.ndarray
    nonseparable_bad: np.ndarray

    @property
    def n_nonseparable(self) -> int:
        return int(self.nonseparable_good.size + self.nonseparable_bad.size)


@dataclass(frozen=True, slots=True)
class _LPLayout:
    """Stable transformed-variable locations."""

    n_lambda: int
    n_inputs: int
    n_separable_good: int
    n_separable_bad: int

    @property
    def lambda_slice(self) -> slice:
        return slice(0, self.n_lambda)

    @property
    def input_slack_slice(self) -> slice:
        start = self.n_lambda
        return slice(start, start + self.n_inputs)

    @property
    def good_slack_slice(self) -> slice:
        start = self.n_lambda + self.n_inputs
        return slice(start, start + self.n_separable_good)

    @property
    def bad_slack_slice(self) -> slice:
        start = self.n_lambda + self.n_inputs + self.n_separable_good
        return slice(start, start + self.n_separable_bad)

    @property
    def alpha_index(self) -> int:
        return (
            self.n_lambda + self.n_inputs + self.n_separable_good + self.n_separable_bad
        )

    @property
    def scale_index(self) -> int:
        return self.alpha_index + 1

    @property
    def size(self) -> int:
        return self.scale_index + 1


def _transformed_rts_rows(
    layout: _LPLayout,
    returns_to_scale: ReturnsToScale,
) -> tuple[csc_matrix | None, np.ndarray | None, csc_matrix | None, np.ndarray | None]:
    """Encode source Eq. (23) after the Charnes--Cooper transformation."""

    row = np.zeros(layout.size, dtype=np.float64)
    row[layout.lambda_slice] = 1.0
    row[layout.scale_index] = -1.0
    sparse_row = csc_matrix(row.reshape(1, -1))

    if returns_to_scale is ReturnsToScale.VRS:
        return None, None, sparse_row, np.asarray([0.0])
    if returns_to_scale is ReturnsToScale.NIRS:
        return sparse_row, np.asarray([0.0]), None, None
    if returns_to_scale is ReturnsToScale.NDRS:
        return -sparse_row, np.asarray([0.0]), None, None
    return None, None, None, None


class ToneNonSeparableSBM:
    """Estimate Tone's non-separable undesirable-output SBM.

    Parameters
    ----------
    nonseparable_outputs:
        Desirable-output names assigned to the common activity-adjustment
        block. Every remaining desirable output is separable.
    nonseparable_bad_outputs:
        Undesirable-output names assigned to that same common block. Every
        remaining undesirable output is separable.
    alpha_min:
        Lower bound on the common source-projection factor ``alpha``. The
        package default is zero. Under CRS or NIRS, an all-non-separable
        desirable-output account requires a positive lower bound so that
        complete shutdown cannot become the benchmark.

    Notes
    -----
    This class implements Tone (2003), Eqs. (29)--(32), as one sparse
    Charnes--Cooper LP. The non-separable source projection is
    ``(alpha * y_o, alpha * b_o)``. A peer activity may strictly exceed the
    projected non-separable good outputs or strictly improve on its bad
    outputs. Those source-to-reference residuals are returned, but Eqs.
    (38)--(39) do not include them in the native score.

    Non-separability is an estimator partition, not a declaration of weak
    disposability. Accordingly, this class does not expose a disposability
    switch and does not label its technology as weakly disposable.
    """

    _registry_method_id = "environmental.sbm.nonseparable_hybrid.tone_2003"

    def __init__(
        self,
        *,
        nonseparable_outputs: Sequence[str] | str,
        nonseparable_bad_outputs: Sequence[str] | str,
        alpha_min: float = 0.0,
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.VRS,
        reference: ReferenceSpec | str | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.nonseparable_outputs = _declared_names(
            nonseparable_outputs,
            "nonseparable_outputs",
        )
        self.nonseparable_bad_outputs = _declared_names(
            nonseparable_bad_outputs,
            "nonseparable_bad_outputs",
        )
        if isinstance(alpha_min, bool) or not isinstance(alpha_min, Real):
            raise TypeError("alpha_min must be a real number")
        if not math.isfinite(alpha_min) or not 0.0 <= alpha_min <= 1.0:
            raise ValueError("alpha_min must be finite and lie in [0, 1]")
        self.alpha_min = float(alpha_min)
        self.returns_to_scale = parse_enum(
            returns_to_scale,
            ReturnsToScale,
            "returns_to_scale",
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
        if not math.isfinite(tolerance) or tolerance <= 0:
            raise ValueError("tolerance must be finite and positive")
        self.tolerance = float(tolerance)
        self.peer_tolerance = (
            self.tolerance if peer_tolerance is None else float(peer_tolerance)
        )
        if not math.isfinite(self.peer_tolerance) or self.peer_tolerance <= 0:
            raise ValueError("peer_tolerance must be finite and positive")

    def _partition(self, data: DEAData) -> _OutputPartition:
        if data.bad_outputs is None or not data.bad_output_names:
            raise ModelSpecificationError(
                "ToneNonSeparableSBM requires declared bad_outputs in DEAData"
            )
        data.ensure_nonnegative(allow_zero=False)

        unknown_good = set(self.nonseparable_outputs).difference(data.output_names)
        unknown_bad = set(self.nonseparable_bad_outputs).difference(
            data.bad_output_names
        )
        if unknown_good or unknown_bad:
            raise ModelSpecificationError(
                "non-separable partition names must exactly match their DEAData "
                "roles; "
                f"unknown_outputs={sorted(unknown_good)!r}, "
                f"unknown_bad_outputs={sorted(unknown_bad)!r}"
            )

        good_positions = {
            name: position for position, name in enumerate(data.output_names)
        }
        bad_positions = {
            name: position for position, name in enumerate(data.bad_output_names)
        }
        nonseparable_good = np.asarray(
            [good_positions[name] for name in self.nonseparable_outputs],
            dtype=np.int64,
        )
        nonseparable_bad = np.asarray(
            [bad_positions[name] for name in self.nonseparable_bad_outputs],
            dtype=np.int64,
        )
        declared_good = set(self.nonseparable_outputs)
        declared_bad = set(self.nonseparable_bad_outputs)
        separable_good = np.asarray(
            [
                position
                for position, name in enumerate(data.output_names)
                if name not in declared_good
            ],
            dtype=np.int64,
        )
        separable_bad = np.asarray(
            [
                position
                for position, name in enumerate(data.bad_output_names)
                if name not in declared_bad
            ],
            dtype=np.int64,
        )
        if (
            self.returns_to_scale in {ReturnsToScale.CRS, ReturnsToScale.NIRS}
            and self.alpha_min == 0.0
            and separable_good.size == 0
        ):
            raise ModelSpecificationError(
                "CRS or NIRS with alpha_min=0 and no separable desirable "
                "output admits an unanchored zero-activity shutdown. Set "
                "alpha_min to a positive retained-activity share or keep at "
                "least one desirable output in the separable account."
            )
        for positions in (
            separable_good,
            nonseparable_good,
            separable_bad,
            nonseparable_bad,
        ):
            positions.setflags(write=False)
        return _OutputPartition(
            separable_good=separable_good,
            nonseparable_good=nonseparable_good,
            separable_bad=separable_bad,
            nonseparable_bad=nonseparable_bad,
        )

    def _problem(
        self,
        reference: CompiledReference,
        partition: _OutputPartition,
        x_o: np.ndarray,
        y_o: np.ndarray,
        b_o: np.ndarray,
        name: str,
    ) -> tuple[LinearProgram, _LPLayout]:
        if reference.bad_outputs is None:
            raise RuntimeError("compiled non-separable SBM reference lacks bad outputs")
        separable_y_o = y_o[partition.separable_good]
        nonseparable_y_o = y_o[partition.nonseparable_good]
        separable_b_o = b_o[partition.separable_bad]
        nonseparable_b_o = b_o[partition.nonseparable_bad]
        separable_y_reference = csc_matrix(
            reference.outputs[partition.separable_good, :]
        )
        nonseparable_y_reference = csc_matrix(
            reference.outputs[partition.nonseparable_good, :]
        )
        separable_b_reference = csc_matrix(
            reference.bad_outputs[partition.separable_bad, :]
        )
        nonseparable_b_reference = csc_matrix(
            reference.bad_outputs[partition.nonseparable_bad, :]
        )

        layout = _LPLayout(
            n_lambda=reference.size,
            n_inputs=x_o.size,
            n_separable_good=separable_y_o.size,
            n_separable_bad=separable_b_o.size,
        )
        m = layout.n_inputs
        p = layout.n_separable_good
        q = layout.n_separable_bad

        input_rows = hstack(
            [
                reference.inputs,
                eye(m, format="csc"),
                csc_matrix((m, p + q + 1)),
                csc_matrix((-x_o).reshape(-1, 1)),
            ],
            format="csc",
        )
        equality_rows: list[csc_matrix] = [input_rows]
        equality_rhs: list[np.ndarray] = [np.zeros(m, dtype=np.float64)]

        if p:
            good_rows = hstack(
                [
                    separable_y_reference,
                    csc_matrix((p, m)),
                    -eye(p, format="csc"),
                    csc_matrix((p, q + 1)),
                    csc_matrix((-separable_y_o).reshape(-1, 1)),
                ],
                format="csc",
            )
            equality_rows.append(good_rows)
            equality_rhs.append(np.zeros(p, dtype=np.float64))

        if q:
            bad_rows = hstack(
                [
                    separable_b_reference,
                    csc_matrix((q, m + p)),
                    eye(q, format="csc"),
                    csc_matrix((q, 1)),
                    csc_matrix((-separable_b_o).reshape(-1, 1)),
                ],
                format="csc",
            )
            equality_rows.append(bad_rows)
            equality_rhs.append(np.zeros(q, dtype=np.float64))

        output_dimension = y_o.size + b_o.size
        normalization = np.zeros(layout.size, dtype=np.float64)
        if p:
            normalization[layout.good_slack_slice] = 1.0 / (
                output_dimension * separable_y_o
            )
        if q:
            normalization[layout.bad_slack_slice] = 1.0 / (
                output_dimension * separable_b_o
            )
        nonseparable_weight = partition.n_nonseparable / output_dimension
        normalization[layout.alpha_index] = -nonseparable_weight
        normalization[layout.scale_index] = 1.0 + nonseparable_weight
        equality_rows.append(csc_matrix(normalization.reshape(1, -1)))
        equality_rhs.append(np.asarray([1.0]))

        a_eq = vstack(equality_rows, format="csc")
        b_eq = np.concatenate(equality_rhs)

        inequality_rows: list[csc_matrix] = []
        inequality_rhs: list[np.ndarray] = []
        # alpha_bar * y_o^NS <= Y^NS Lambda
        nonseparable_good_rows = hstack(
            [
                -nonseparable_y_reference,
                csc_matrix(
                    (
                        nonseparable_y_o.size,
                        m + p + q,
                    )
                ),
                csc_matrix(nonseparable_y_o.reshape(-1, 1)),
                csc_matrix((nonseparable_y_o.size, 1)),
            ],
            format="csc",
        )
        inequality_rows.append(nonseparable_good_rows)
        inequality_rhs.append(np.zeros(nonseparable_y_o.size, dtype=np.float64))

        # B^NS Lambda <= alpha_bar * b_o^NS
        nonseparable_bad_rows = hstack(
            [
                nonseparable_b_reference,
                csc_matrix(
                    (
                        nonseparable_b_o.size,
                        m + p + q,
                    )
                ),
                csc_matrix((-nonseparable_b_o).reshape(-1, 1)),
                csc_matrix((nonseparable_b_o.size, 1)),
            ],
            format="csc",
        )
        inequality_rows.append(nonseparable_bad_rows)
        inequality_rhs.append(np.zeros(nonseparable_b_o.size, dtype=np.float64))

        alpha_upper = np.zeros(layout.size, dtype=np.float64)
        alpha_upper[layout.alpha_index] = 1.0
        alpha_upper[layout.scale_index] = -1.0
        inequality_rows.append(csc_matrix(alpha_upper.reshape(1, -1)))
        inequality_rhs.append(np.asarray([0.0]))

        alpha_lower = np.zeros(layout.size, dtype=np.float64)
        alpha_lower[layout.alpha_index] = -1.0
        alpha_lower[layout.scale_index] = self.alpha_min
        inequality_rows.append(csc_matrix(alpha_lower.reshape(1, -1)))
        inequality_rhs.append(np.asarray([0.0]))

        a_ub = vstack(inequality_rows, format="csc")
        b_ub = np.concatenate(inequality_rhs)
        rts_ub, rts_b_ub, rts_eq, rts_b_eq = _transformed_rts_rows(
            layout,
            self.returns_to_scale,
        )
        a_ub = join_optional_rows(a_ub, rts_ub)
        b_ub = join_optional_values(b_ub, rts_b_ub)
        a_eq = join_optional_rows(a_eq, rts_eq)
        b_eq = join_optional_values(b_eq, rts_b_eq)

        objective = np.zeros(layout.size, dtype=np.float64)
        objective[layout.input_slack_slice] = -1.0 / (m * x_o)
        objective[layout.scale_index] = 1.0
        return (
            LinearProgram(
                c=objective,
                a_ub=a_ub,
                b_ub=b_ub,
                a_eq=a_eq,
                b_eq=b_eq,
                bounds=((0.0, None),) * layout.size,
                name=f"{name}:tone_nonseparable_sbm",
            ),
            layout,
        )

    def _dual_rows(
        self,
        data: DEAData,
        observation: int,
        partition: _OutputPartition,
        solution: LPSolution,
    ) -> list[dict[str, Any]]:
        period = None if data.periods is None else data.periods[observation]
        common = {
            "dmu_id": data.dmu_ids[observation],
            "period": period,
            "phase": 1,
            "coordinate_system": "charnes_cooper_transformed",
        }
        rows: list[dict[str, Any]] = []
        if solution.equality_marginals is not None:
            offset = 0
            for variable in data.input_names:
                rows.append(
                    {
                        **common,
                        "constraint_role": "input_balance",
                        "variable": variable,
                        "marginal": solution.equality_marginals[offset],
                    }
                )
                offset += 1
            for position in partition.separable_good:
                rows.append(
                    {
                        **common,
                        "constraint_role": "separable_good_output_balance",
                        "variable": data.output_names[position],
                        "marginal": solution.equality_marginals[offset],
                    }
                )
                offset += 1
            for position in partition.separable_bad:
                rows.append(
                    {
                        **common,
                        "constraint_role": "separable_bad_output_balance",
                        "variable": data.bad_output_names[position],
                        "marginal": solution.equality_marginals[offset],
                    }
                )
                offset += 1
            rows.append(
                {
                    **common,
                    "constraint_role": "fractional_normalization",
                    "variable": "t",
                    "marginal": solution.equality_marginals[offset],
                }
            )
            offset += 1
            if self.returns_to_scale is ReturnsToScale.VRS:
                rows.append(
                    {
                        **common,
                        "constraint_role": "returns_to_scale",
                        "variable": self.returns_to_scale.value,
                        "marginal": solution.equality_marginals[offset],
                    }
                )

        if solution.inequality_marginals is not None:
            offset = 0
            for position in partition.nonseparable_good:
                rows.append(
                    {
                        **common,
                        "constraint_role": (
                            "nonseparable_good_reference_at_least_source_projection"
                        ),
                        "variable": data.output_names[position],
                        "marginal": solution.inequality_marginals[offset],
                    }
                )
                offset += 1
            for position in partition.nonseparable_bad:
                rows.append(
                    {
                        **common,
                        "constraint_role": (
                            "nonseparable_bad_reference_at_most_source_projection"
                        ),
                        "variable": data.bad_output_names[position],
                        "marginal": solution.inequality_marginals[offset],
                    }
                )
                offset += 1
            for role in ("alpha_upper_bound", "alpha_lower_bound"):
                rows.append(
                    {
                        **common,
                        "constraint_role": role,
                        "variable": "alpha",
                        "marginal": solution.inequality_marginals[offset],
                    }
                )
                offset += 1
            if self.returns_to_scale in {
                ReturnsToScale.NIRS,
                ReturnsToScale.NDRS,
            }:
                rows.append(
                    {
                        **common,
                        "constraint_role": "returns_to_scale",
                        "variable": self.returns_to_scale.value,
                        "marginal": solution.inequality_marginals[offset],
                    }
                )
        return rows

    def fit(self, data: DEAData) -> DEAResult:
        """Estimate the non-separable hybrid for every observation."""

        partition = self._partition(data)
        if data.bad_outputs is None:
            raise RuntimeError("validated non-separable SBM data lost bad outputs")
        reference_plan = build_reference_plan(data, self.reference)
        self_membership = reference_plan.self_membership_mask()
        if all(self_membership):
            appraisal_kind = "self_appraisal"
        elif any(self_membership):
            appraisal_kind = "mixed_self_and_external_reference_appraisal"
        else:
            appraisal_kind = "external_reference_appraisal"

        compiled: dict[int, CompiledReference] = {}
        summary_rows: list[dict[str, Any]] = []
        slack_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []
        dual_rows: list[dict[str, Any]] = []
        primary_solver_calls = 0

        for observation in range(data.n_dmus):
            set_id = reference_plan.set_id_for(observation)
            reference = get_or_compile_reference(
                data,
                reference_plan.rows_for(observation),
                set_id,
                compiled,
                compiler=compile_reference,
            )
            dmu_id = data.dmu_ids[observation]
            period = None if data.periods is None else data.periods[observation]
            name = f"{dmu_id}@{period}" if period is not None else str(dmu_id)
            x_o = data.inputs[observation]
            y_o = data.outputs[observation]
            b_o = data.bad_outputs[observation]
            problem, layout = self._problem(
                reference,
                partition,
                x_o,
                y_o,
                b_o,
                name,
            )
            solution = self.solver.solve(problem)
            primary_solver_calls += 1
            self_in_reference = self_membership[observation]
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
                "normalization_residual": np.nan,
                "maximum_balance_residual": np.nan,
                "minimum_nonseparable_constraint_margin": np.nan,
                "self_in_reference": self_in_reference,
            }
            dual_rows.extend(self._dual_rows(data, observation, partition, solution))

            if not solution.is_optimal or solution.primal is None:
                diagnostic_rows.append(diagnostic)
                summary_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "score": np.nan,
                        "efficiency": np.nan,
                        "distance": np.nan,
                        "is_efficient": pd.NA,
                        "is_sbm_efficient": pd.NA,
                        "is_pareto_efficient": pd.NA,
                        "solver_status": solution.status.value,
                        "model_family": "nonseparable_undesirable_slacks_based",
                        "orientation": "non-oriented",
                        "returns_to_scale": self.returns_to_scale.value,
                        "reference_size": reference.size,
                        "self_in_reference": self_in_reference,
                        "score_status": "solver_failure",
                        "alpha": np.nan,
                        "alpha_min": self.alpha_min,
                        "input_inefficiency": np.nan,
                        "separable_good_output_inefficiency": np.nan,
                        "separable_bad_output_inefficiency": np.nan,
                        "nonseparable_output_inefficiency": np.nan,
                        "output_inefficiency": np.nan,
                        "output_account_factor": np.nan,
                        "max_slack": np.nan,
                        "max_normalized_slack": np.nan,
                        "max_reference_residual": np.nan,
                        "max_normalized_reference_residual": np.nan,
                        "transform_scale": np.nan,
                    }
                )
                continue

            transformed = np.asarray(solution.primal, dtype=np.float64)
            transform_scale = float(transformed[layout.scale_index])
            if not math.isfinite(transform_scale) or transform_scale <= 0.0:
                raise RuntimeError(
                    "Tone non-separable SBM Charnes--Cooper scale is not "
                    "positive; inspect solver diagnostics and data scaling"
                )

            alpha = float(transformed[layout.alpha_index] / transform_scale)
            if abs(alpha) <= self.tolerance:
                alpha = 0.0
            elif abs(alpha - 1.0) <= self.tolerance:
                alpha = 1.0
            if (
                alpha < self.alpha_min - 10.0 * self.tolerance
                or alpha > 1.0 + 10.0 * self.tolerance
            ):
                raise RuntimeError(
                    "recovered non-separable adjustment violates its declared "
                    "bounds; inspect solver diagnostics and data scaling"
                )

            lambdas = np.maximum(
                transformed[layout.lambda_slice] / transform_scale,
                0.0,
            )
            input_slacks = clean_small(
                np.maximum(
                    transformed[layout.input_slack_slice] / transform_scale,
                    0.0,
                ),
                self.tolerance,
            )
            separable_good_slacks = clean_small(
                np.maximum(
                    transformed[layout.good_slack_slice] / transform_scale,
                    0.0,
                ),
                self.tolerance,
            )
            separable_bad_slacks = clean_small(
                np.maximum(
                    transformed[layout.bad_slack_slice] / transform_scale,
                    0.0,
                ),
                self.tolerance,
            )

            input_normalized_slacks = input_slacks / x_o
            separable_good_o = y_o[partition.separable_good]
            separable_bad_o = b_o[partition.separable_bad]
            separable_good_normalized_slacks = separable_good_slacks / separable_good_o
            separable_bad_normalized_slacks = separable_bad_slacks / separable_bad_o
            activity_adjustment = max(1.0 - alpha, 0.0)
            nonseparable_good_o = y_o[partition.nonseparable_good]
            nonseparable_bad_o = b_o[partition.nonseparable_bad]
            nonseparable_good_gaps = activity_adjustment * nonseparable_good_o
            nonseparable_bad_gaps = activity_adjustment * nonseparable_bad_o

            reference_inputs = np.asarray(reference.inputs @ lambdas).reshape(-1)
            reference_outputs = np.asarray(reference.outputs @ lambdas).reshape(-1)
            reference_bad_outputs = np.asarray(reference.bad_outputs @ lambdas).reshape(
                -1
            )
            input_targets = x_o - input_slacks
            separable_good_targets = separable_good_o + separable_good_slacks
            separable_bad_targets = separable_bad_o - separable_bad_slacks
            nonseparable_good_targets = alpha * nonseparable_good_o
            nonseparable_bad_targets = alpha * nonseparable_bad_o

            good_reference_residuals_signed = (
                reference_outputs[partition.nonseparable_good]
                - nonseparable_good_targets
            )
            bad_reference_residuals_signed = (
                nonseparable_bad_targets
                - reference_bad_outputs[partition.nonseparable_bad]
            )
            good_reference_residuals = clean_small(
                np.maximum(good_reference_residuals_signed, 0.0),
                self.tolerance,
            )
            bad_reference_residuals = clean_small(
                np.maximum(bad_reference_residuals_signed, 0.0),
                self.tolerance,
            )

            input_inefficiency = float(np.mean(input_normalized_slacks))
            output_dimension = data.n_outputs + data.n_bad_outputs
            separable_good_inefficiency = float(
                np.sum(separable_good_normalized_slacks) / output_dimension
            )
            separable_bad_inefficiency = float(
                np.sum(separable_bad_normalized_slacks) / output_dimension
            )
            nonseparable_inefficiency = float(
                partition.n_nonseparable * activity_adjustment / output_dimension
            )
            output_inefficiency = (
                separable_good_inefficiency
                + separable_bad_inefficiency
                + nonseparable_inefficiency
            )
            output_account_factor = 1.0 + output_inefficiency
            efficiency = float((1.0 - input_inefficiency) / output_account_factor)
            distance = 1.0 - efficiency

            scored_slacks = np.concatenate(
                [
                    input_slacks,
                    separable_good_slacks,
                    separable_bad_slacks,
                    nonseparable_good_gaps,
                    nonseparable_bad_gaps,
                ]
            )
            scored_normalized_slacks = np.concatenate(
                [
                    input_normalized_slacks,
                    separable_good_normalized_slacks,
                    separable_bad_normalized_slacks,
                    np.full(
                        partition.n_nonseparable,
                        activity_adjustment,
                        dtype=np.float64,
                    ),
                ]
            )
            reference_residuals = np.concatenate(
                [good_reference_residuals, bad_reference_residuals]
            )
            normalized_reference_residuals = np.concatenate(
                [
                    good_reference_residuals / nonseparable_good_o,
                    bad_reference_residuals / nonseparable_bad_o,
                ]
            )
            max_slack = float(np.max(scored_slacks, initial=0.0))
            max_normalized_slack = float(np.max(scored_normalized_slacks, initial=0.0))
            max_reference_residual = float(np.max(reference_residuals, initial=0.0))
            max_normalized_reference_residual = float(
                np.max(normalized_reference_residuals, initial=0.0)
            )
            source_sbm_efficient: bool | Any = (
                bool(max_normalized_slack <= self.tolerance)
                if self_in_reference
                else pd.NA
            )
            is_efficient: bool | Any = source_sbm_efficient
            score_status = (
                "defined_self_appraisal"
                if self_in_reference
                else "descriptive_external_reference_not_efficiency_certified"
            )

            normalization_reconstructed = transform_scale * output_account_factor
            balance_residuals = np.concatenate(
                [
                    input_targets - reference_inputs,
                    (
                        separable_good_targets
                        - reference_outputs[partition.separable_good]
                    ),
                    (
                        separable_bad_targets
                        - reference_bad_outputs[partition.separable_bad]
                    ),
                ]
            )
            objective_residual = (
                np.nan
                if solution.objective is None
                else efficiency - float(solution.objective)
            )
            diagnostic.update(
                {
                    "reconstructed_objective": efficiency,
                    "objective_reconstruction_residual": objective_residual,
                    "normalization_residual": normalization_reconstructed - 1.0,
                    "maximum_balance_residual": float(
                        np.max(np.abs(balance_residuals), initial=0.0)
                    ),
                    "minimum_nonseparable_constraint_margin": float(
                        min(
                            np.min(
                                good_reference_residuals_signed,
                                initial=np.inf,
                            ),
                            np.min(
                                bad_reference_residuals_signed,
                                initial=np.inf,
                            ),
                        )
                    ),
                }
            )
            diagnostic_rows.append(diagnostic)

            for local_position, intensity in enumerate(lambdas):
                if intensity > self.peer_tolerance:
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
                            "selection_status": ("solver_selected_primary_optimum"),
                        }
                    )

            def append_target(
                *,
                role: str,
                variable: str,
                observed: float,
                target: float,
                reference_activity: float,
                partition_name: str,
                target_kind: str,
                residual: float = 0.0,
                result_dmu_id: object = dmu_id,
                result_period: object | None = period,
            ) -> None:
                target_rows.append(
                    {
                        "dmu_id": result_dmu_id,
                        "period": result_period,
                        "role": role,
                        "variable": variable,
                        "observed": float(observed),
                        "target": float(target),
                        "reference_activity": float(reference_activity),
                        "source_reference_residual": float(residual),
                        "partition": partition_name,
                        "target_kind": target_kind,
                        "selection_status": "solver_selected_primary_optimum",
                    }
                )

            def append_scored_slack(
                *,
                role: str,
                variable: str,
                slack: float,
                normalizer: float,
                average_weight: float,
                partition_name: str,
                direction: str,
                kind: str,
                result_dmu_id: object = dmu_id,
                result_period: object | None = period,
            ) -> None:
                slack_rows.append(
                    {
                        "dmu_id": result_dmu_id,
                        "period": result_period,
                        "role": role,
                        "variable": variable,
                        "slack": float(slack),
                        "normalizer": float(normalizer),
                        "normalized_slack": float(slack / normalizer),
                        "average_weight": float(average_weight),
                        "partition": partition_name,
                        "slack_kind": kind,
                        "slack_direction": direction,
                        "included_in_objective": True,
                        "scored": True,
                    }
                )

            for position, variable in enumerate(data.input_names):
                append_target(
                    role="input",
                    variable=variable,
                    observed=x_o[position],
                    target=input_targets[position],
                    reference_activity=reference_inputs[position],
                    partition_name="separable",
                    target_kind="input_slack_projection",
                )
                append_scored_slack(
                    role="input",
                    variable=variable,
                    slack=input_slacks[position],
                    normalizer=x_o[position],
                    average_weight=1.0 / data.n_inputs,
                    partition_name="separable",
                    direction="contraction",
                    kind="input_excess",
                )

            for local, position in enumerate(partition.separable_good):
                variable = data.output_names[position]
                append_target(
                    role="output",
                    variable=variable,
                    observed=y_o[position],
                    target=separable_good_targets[local],
                    reference_activity=reference_outputs[position],
                    partition_name="separable",
                    target_kind="separable_good_output_slack_projection",
                )
                append_scored_slack(
                    role="output",
                    variable=variable,
                    slack=separable_good_slacks[local],
                    normalizer=y_o[position],
                    average_weight=1.0 / output_dimension,
                    partition_name="separable",
                    direction="expansion",
                    kind="desirable_output_shortfall",
                )

            for local, position in enumerate(partition.separable_bad):
                variable = data.bad_output_names[position]
                append_target(
                    role="bad_output",
                    variable=variable,
                    observed=b_o[position],
                    target=separable_bad_targets[local],
                    reference_activity=reference_bad_outputs[position],
                    partition_name="separable",
                    target_kind="separable_bad_output_slack_projection",
                )
                append_scored_slack(
                    role="bad_output",
                    variable=variable,
                    slack=separable_bad_slacks[local],
                    normalizer=b_o[position],
                    average_weight=1.0 / output_dimension,
                    partition_name="separable",
                    direction="contraction",
                    kind="undesirable_output_excess",
                )

            for local, position in enumerate(partition.nonseparable_good):
                variable = data.output_names[position]
                append_target(
                    role="output",
                    variable=variable,
                    observed=y_o[position],
                    target=nonseparable_good_targets[local],
                    reference_activity=reference_outputs[position],
                    partition_name="nonseparable",
                    target_kind="alpha_times_source",
                    residual=good_reference_residuals[local],
                )
                append_scored_slack(
                    role="output",
                    variable=variable,
                    slack=nonseparable_good_gaps[local],
                    normalizer=y_o[position],
                    average_weight=1.0 / output_dimension,
                    partition_name="nonseparable",
                    direction="common_activity_contraction",
                    kind="one_minus_alpha_source_adjustment",
                )
                slack_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "role": ("nonseparable_good_output_reference_surplus"),
                        "variable": variable,
                        "slack": float(good_reference_residuals[local]),
                        "normalizer": float(y_o[position]),
                        "normalized_slack": float(
                            good_reference_residuals[local] / y_o[position]
                        ),
                        "average_weight": 0.0,
                        "partition": "nonseparable_residual",
                        "slack_kind": ("source_projection_vs_reference_activity"),
                        "slack_direction": "reference_above_source_projection",
                        "included_in_objective": False,
                        "scored": False,
                    }
                )

            for local, position in enumerate(partition.nonseparable_bad):
                variable = data.bad_output_names[position]
                append_target(
                    role="bad_output",
                    variable=variable,
                    observed=b_o[position],
                    target=nonseparable_bad_targets[local],
                    reference_activity=reference_bad_outputs[position],
                    partition_name="nonseparable",
                    target_kind="alpha_times_source",
                    residual=bad_reference_residuals[local],
                )
                append_scored_slack(
                    role="bad_output",
                    variable=variable,
                    slack=nonseparable_bad_gaps[local],
                    normalizer=b_o[position],
                    average_weight=1.0 / output_dimension,
                    partition_name="nonseparable",
                    direction="common_activity_contraction",
                    kind="one_minus_alpha_source_adjustment",
                )
                slack_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "role": ("nonseparable_bad_output_reference_shortfall"),
                        "variable": variable,
                        "slack": float(bad_reference_residuals[local]),
                        "normalizer": float(b_o[position]),
                        "normalized_slack": float(
                            bad_reference_residuals[local] / b_o[position]
                        ),
                        "average_weight": 0.0,
                        "partition": "nonseparable_residual",
                        "slack_kind": ("source_projection_vs_reference_activity"),
                        "slack_direction": "reference_below_source_projection",
                        "included_in_objective": False,
                        "scored": False,
                    }
                )

            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "score": efficiency,
                    "efficiency": efficiency,
                    "distance": distance,
                    "is_efficient": is_efficient,
                    "is_sbm_efficient": source_sbm_efficient,
                    "is_pareto_efficient": pd.NA,
                    "solver_status": SolverStatus.OPTIMAL.value,
                    "model_family": "nonseparable_undesirable_slacks_based",
                    "orientation": "non-oriented",
                    "returns_to_scale": self.returns_to_scale.value,
                    "reference_size": reference.size,
                    "self_in_reference": self_in_reference,
                    "score_status": score_status,
                    "alpha": alpha,
                    "alpha_min": self.alpha_min,
                    "input_inefficiency": input_inefficiency,
                    "separable_good_output_inefficiency": (separable_good_inefficiency),
                    "separable_bad_output_inefficiency": (separable_bad_inefficiency),
                    "nonseparable_output_inefficiency": (nonseparable_inefficiency),
                    "output_inefficiency": output_inefficiency,
                    "output_account_factor": output_account_factor,
                    "max_slack": max_slack,
                    "max_normalized_slack": max_normalized_slack,
                    "max_reference_residual": max_reference_residual,
                    "max_normalized_reference_residual": (
                        max_normalized_reference_residual
                    ),
                    "transform_scale": transform_scale,
                }
            )

        separable_outputs = tuple(
            data.output_names[position] for position in partition.separable_good
        )
        separable_bad_outputs = tuple(
            data.bad_output_names[position] for position in partition.separable_bad
        )
        return DEAResult(
            summary_frame=pd.DataFrame(summary_rows),
            slacks=pd.DataFrame(slack_rows),
            targets=pd.DataFrame(target_rows),
            intensities=pd.DataFrame(intensity_rows),
            duals=pd.DataFrame(dual_rows),
            diagnostics=pd.DataFrame(diagnostic_rows),
            metadata={
                **registry_metadata(
                    self._registry_method_id,
                    {
                        "context": {
                            "purpose": (
                                "joint_activity_environmental_performance_benchmarking"
                            ),
                            "managerial_plan": (
                                "combine_common_activity_adjustment_with_"
                                "variable_specific_resource_and_output_gaps"
                            ),
                            "sample": ("panel" if data.is_panel else "cross_section"),
                        },
                        "graph": {"kind": "black_box_joint_production"},
                        "data_roles": {
                            "inputs": (
                                "controllable_resources_with_input_slack_account"
                            ),
                            "outputs": (
                                "partitioned_separable_and_nonseparable_"
                                "desirable_services"
                            ),
                            "bad_outputs": (
                                "partitioned_separable_and_nonseparable_"
                                "undesirable_residuals"
                            ),
                            "separable_outputs": list(separable_outputs),
                            "nonseparable_outputs": list(self.nonseparable_outputs),
                            "separable_bad_outputs": list(separable_bad_outputs),
                            "nonseparable_bad_outputs": list(
                                self.nonseparable_bad_outputs
                            ),
                            **data_role_schema(data),
                        },
                        "technology": {
                            "family": "convex_envelopment",
                            "returns_to_scale": self.returns_to_scale.value,
                            "returns_to_scale_provenance": ("tone_2003_equation_23"),
                            "bad_output_disposability": "partition_specific",
                            "separable_bad_output_disposability": (
                                "strong_variable_specific_slack_balance"
                            ),
                            "nonseparable_bad_output_disposability": (
                                "joint_alpha_constraint_not_a_generic_weak_"
                                "disposal_axiom"
                            ),
                            "nonseparability": ("common_source_activity_adjustment"),
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
                            "family": ("tone_nonseparable_slacks_based_measure"),
                            "orientation": "non_oriented",
                            "normalization": "evaluated_dmu_values",
                            "nonseparable_projection": "alpha_times_source",
                            "nonseparable_reference_residuals": "unscored",
                        },
                        "valuation": {
                            "kind": "equal_dimension_weights",
                            "input_account": "equal_over_inputs",
                            "output_account": (
                                "equal_over_good_and_bad_output_dimensions"
                            ),
                        },
                        "evaluation_protocol": {
                            "kind": appraisal_kind,
                            "fractional_transformation": "charnes_cooper",
                            "alternate_target_policy": "solver_selected",
                            "efficiency_certification_boundary": (
                                "self_in_reference_only"
                            ),
                        },
                        "analysis": {"kind": "direct_model_fit"},
                        "uncertainty": {"kind": "deterministic"},
                    },
                ),
                "model_family": "nonseparable_undesirable_slacks_based",
                "variant": "tone_2003_nonseparable_hybrid",
                "orientation": "non-oriented",
                "returns_to_scale": self.returns_to_scale.value,
                "returns_to_scale_provenance": "tone_2003_equation_23",
                "reference_kind": reference_plan.kind.value,
                "native_score": "rho_NS",
                "reported_efficiency": "rho_NS",
                "score_direction": "higher_is_better",
                "distance_transform": "one_minus_efficiency",
                "normalization": "evaluated_dmu_values",
                "data_requirement": "strictly_positive",
                "linearization": "charnes_cooper",
                "alpha_min": self.alpha_min,
                "separability": "declared_good_and_bad_output_partition",
                "separable_outputs": separable_outputs,
                "nonseparable_outputs": self.nonseparable_outputs,
                "separable_bad_outputs": separable_bad_outputs,
                "nonseparable_bad_outputs": self.nonseparable_bad_outputs,
                "nonseparable_projection": "alpha_times_source",
                "nonseparable_residuals": (
                    "source_projection_vs_reference_activity_not_scored"
                ),
                "residual_nonseparable_slacks_scored": False,
                "bad_output_disposability": (
                    "partition_specific_separable_strong_and_"
                    "nonseparable_joint_adjustment"
                ),
                "source_equations": {
                    "fractional_program": "tone_2003_equations_29_to_32",
                    "nonseparable_residuals": "tone_2003_equations_38_to_39",
                    "linearization": ("deapack_charnes_cooper_analytical_derivation"),
                },
                "target_selection": "solver_selected_primary_optimum",
                "source_target_kind": "alpha_times_source",
                "reference_activity_reported_separately": True,
                "generic_efficiency_certification": (
                    "per_observation_self_in_reference_only"
                ),
                "pareto_efficiency_certification": (
                    "not_certified_unscored_nonseparable_residuals"
                ),
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "planned_reference_sets": (reference_plan.unique_reference_sets),
                "compiled_reference_sets": len(compiled),
                "primary_solver_calls": primary_solver_calls,
                "phase_one_solver_calls": primary_solver_calls,
                "phase_two_solver_calls": 0,
                "solver_calls": primary_solver_calls,
            },
        )


NonSeparableUndesirableSBM = ToneNonSeparableSBM
"""Descriptive alias for :class:`ToneNonSeparableSBM`."""

SBMNS = ToneNonSeparableSBM
"""Historical short alias for :class:`ToneNonSeparableSBM`."""
