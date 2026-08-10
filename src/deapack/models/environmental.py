"""Environmental directional distance functions with explicit bad-output technology."""

from __future__ import annotations

import math
import warnings
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix, diags, eye, hstack, vstack

from .._registry import (
    data_role_schema,
    direction_spec,
    registry_metadata,
)
from .._registry import (
    reference_spec as registry_reference_spec,
)
from ..data import DEAData
from ..enums import (
    BadOutputDisposability,
    ReturnsToScale,
    SolverStatus,
    parse_enum,
)
from ..exceptions import ModelSpecificationError
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
from ..technology import PeerEligibility, build_reference_plan
from ._common import (
    CompiledReference,
    clean_small,
    compile_reference,
    join_optional_rows,
    join_optional_values,
    rts_matrices,
)
from ._radial_lp import radial_row_scales
from .directional import DirectionInput, _resolve_direction


def _environmental_row_scales(
    reference: CompiledReference,
    x_o: np.ndarray,
    y_o: np.ndarray,
    b_o: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return positive account scales for unit-stable slack completion."""
    input_scales, output_scales = radial_row_scales(reference, x_o, y_o)
    bad_output_scales = np.maximum(reference.bad_output_row_max, np.abs(b_o))
    bad_output_scales[bad_output_scales <= 0] = 1.0
    return input_scales, output_scales, bad_output_scales


def _certificate_diagnostic(
    *,
    dmu_id: object,
    period: object | None,
    phase: int,
    solution: LPSolution,
    certificate: LPCertificate,
) -> dict[str, Any]:
    """Return one auditable solver and postsolve-certificate record."""
    return {
        "dmu_id": dmu_id,
        "period": period,
        "phase": phase,
        "solver_status": solution.status.value,
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
        "raw_economic_postsolve_certified": pd.NA,
        "max_raw_economic_violation": np.nan,
        "published_output_account_certified": pd.NA,
        "max_published_account_violation": np.nan,
        "published_peer_account_certified": pd.NA,
        "max_published_peer_account_violation": np.nan,
        "published_dual_account_certified": pd.NA,
        "published_dual_row_count": np.nan,
    }


def _scaled_maximum(
    residual: np.ndarray,
    scale: np.ndarray,
) -> float:
    values = np.asarray(residual, dtype=np.float64).reshape(-1)
    account_scale = np.asarray(scale, dtype=np.float64).reshape(-1)
    if (
        values.shape != account_scale.shape
        or not np.isfinite(values).all()
        or not np.isfinite(account_scale).all()
        or np.any(account_scale <= 0.0)
    ):
        return math.inf
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        ratios = np.abs(values) / account_scale
    if not np.isfinite(ratios).all():
        return math.inf
    return float(ratios.max(initial=0.0))


def _scaled_nonnegative_violation(values: np.ndarray) -> float:
    array = np.asarray(values, dtype=np.float64).reshape(-1)
    if not np.isfinite(array).all():
        return math.inf
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        violation = np.maximum(-array, 0.0) / np.maximum(1.0, np.abs(array))
    if not np.isfinite(violation).all():
        return math.inf
    return float(violation.max(initial=0.0))


def _rts_violation(lambdas: np.ndarray, returns_to_scale: ReturnsToScale) -> float:
    total = float(lambdas.sum())
    if not math.isfinite(total):
        return math.inf
    scale = max(1.0, abs(total))
    if returns_to_scale is ReturnsToScale.VRS:
        return abs(total - 1.0) / scale
    if returns_to_scale is ReturnsToScale.NIRS:
        return max(total - 1.0, 0.0) / scale
    if returns_to_scale is ReturnsToScale.NDRS:
        return max(1.0 - total, 0.0) / scale
    return 0.0


@dataclass(frozen=True, slots=True)
class _CertifiedEnvironmentalDistanceTask:
    """One primary environmental DDF solve and its release decisions."""

    solution: LPSolution
    certificate: LPCertificate
    distance: float | None
    published_primal: np.ndarray | None
    peer_lambdas: np.ndarray | None
    score_valid: bool
    score_status: str
    peer_valid: bool
    peer_status: str
    raw_economic_certified: bool | None
    published_economic_certified: bool | None
    raw_economic_violation: float
    published_economic_violation: float
    peer_economic_violation: float
    economic_certification_reason: str


def _certify_environmental_distance_task(
    *,
    problem: LinearProgram,
    solution: LPSolution,
    n_lambdas: int,
    account_violation: Callable[[np.ndarray | None], float],
    tolerance: float,
    peer_tolerance: float,
    beta_nonnegative: bool,
) -> _CertifiedEnvironmentalDistanceTask:
    """Certify one already-solved environmental distance without another solve.

    ``account_violation`` receives ``None`` for the raw solver vector and a
    full primal override for the publication and peer-cleanup accounts.
    """

    certificate = certify_lp_solution(problem, solution, tolerance=tolerance)
    unavailable = "not_available_without_certified_primary"
    if not certificate.certified or solution.primal is None:
        return _CertifiedEnvironmentalDistanceTask(
            solution=solution,
            certificate=certificate,
            distance=None,
            published_primal=None,
            peer_lambdas=None,
            score_valid=False,
            score_status=(
                "solver_failed"
                if solution.status is not SolverStatus.OPTIMAL
                else "unavailable_uncertified_primary_program"
            ),
            peer_valid=False,
            peer_status=unavailable,
            raw_economic_certified=None,
            published_economic_certified=None,
            raw_economic_violation=math.nan,
            published_economic_violation=math.nan,
            peer_economic_violation=math.nan,
            economic_certification_reason="not_checked_uncertified_source_program",
        )

    raw_violation = float(account_violation(None))
    raw_certified = bool(
        math.isfinite(raw_violation) and raw_violation <= 10.0 * tolerance
    )
    if not raw_certified:
        return _CertifiedEnvironmentalDistanceTask(
            solution=solution,
            certificate=certificate,
            distance=None,
            published_primal=None,
            peer_lambdas=None,
            score_valid=False,
            score_status="unavailable_uncertified_primary_program",
            peer_valid=False,
            peer_status=unavailable,
            raw_economic_certified=False,
            published_economic_certified=None,
            raw_economic_violation=raw_violation,
            published_economic_violation=math.nan,
            peer_economic_violation=math.nan,
            economic_certification_reason=(
                "environmental_program_reconstruction_failed"
            ),
        )

    published_primal = clean_small(
        np.asarray(solution.primal, dtype=np.float64),
        tolerance,
    )
    published_primal[:n_lambdas] = np.maximum(
        published_primal[:n_lambdas],
        0.0,
    )
    if beta_nonnegative:
        published_primal[-1] = max(float(published_primal[-1]), 0.0)
    published_violation = float(account_violation(published_primal))
    published_certified = bool(
        math.isfinite(published_violation) and published_violation <= 10.0 * tolerance
    )
    if not published_certified:
        return _CertifiedEnvironmentalDistanceTask(
            solution=solution,
            certificate=certificate,
            distance=None,
            published_primal=None,
            peer_lambdas=None,
            score_valid=False,
            score_status="unavailable_uncertified_primary_program",
            peer_valid=False,
            peer_status=unavailable,
            raw_economic_certified=True,
            published_economic_certified=False,
            raw_economic_violation=raw_violation,
            published_economic_violation=published_violation,
            peer_economic_violation=math.nan,
            economic_certification_reason=(
                "published_environmental_program_reconstruction_failed"
            ),
        )

    peer_primal = published_primal.copy()
    peer_primal[:n_lambdas][peer_primal[:n_lambdas] <= peer_tolerance] = 0.0
    peer_violation = float(account_violation(peer_primal))
    peer_valid = bool(
        math.isfinite(peer_violation) and peer_violation <= 10.0 * tolerance
    )
    return _CertifiedEnvironmentalDistanceTask(
        solution=solution,
        certificate=certificate,
        distance=float(published_primal[-1]),
        published_primal=published_primal,
        peer_lambdas=(peer_primal[:n_lambdas].copy() if peer_valid else None),
        score_valid=True,
        score_status="defined",
        peer_valid=peer_valid,
        peer_status=(
            "certified_primary_program"
            if peer_valid
            else "unavailable_after_peer_reporting_threshold"
        ),
        raw_economic_certified=True,
        published_economic_certified=True,
        raw_economic_violation=raw_violation,
        published_economic_violation=published_violation,
        peer_economic_violation=peer_violation,
        economic_certification_reason="certified",
    )


class EnvironmentalDirectionalDistanceDEA:
    """Expand good outputs and contract bad outputs along explicit directions.

    The deprecated compatibility selector ``disposability="weak"`` uses only
    a bad-output equality. Under general returns to scale this equality does
    not identify a complete named weak-disposal technology. Use
    :class:`CommonFactorWeakDisposalDDF` or
    :class:`ActivitySpecificWeakDisposalDDF` when that production assumption
    is intended. ``"strong"`` uses an inequality and permits residual
    bad-output slack. Null jointness is checked independently when requested.
    """

    _registry_method_id = "environmental.ddf.joint_production"
    _registry_preset_id: str | None = None
    _weak_technology_id: str | None = None
    _warn_legacy_weak = True

    def __init__(
        self,
        *,
        input_direction: DirectionInput = "zeros",
        output_direction: DirectionInput = "observed",
        bad_output_direction: DirectionInput = "observed",
        disposability: BadOutputDisposability | str = BadOutputDisposability.WEAK,
        null_jointness: bool | None = None,
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.VRS,
        reference: ReferenceSpec | str | None = None,
        peer_eligibility: PeerEligibility | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        compute_slacks: bool = True,
        allow_negative_distance: bool = False,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.input_direction = input_direction
        self.output_direction = output_direction
        self.bad_output_direction = bad_output_direction
        legacy_weak_spelling = (
            isinstance(disposability, str)
            and not isinstance(disposability, BadOutputDisposability)
            and disposability.strip().lower() == BadOutputDisposability.WEAK.value
        )
        self.disposability = parse_enum(
            disposability, BadOutputDisposability, "bad-output disposability"
        )
        if legacy_weak_spelling and self._warn_legacy_weak:
            warnings.warn(
                "disposability='weak' is a deprecated compatibility spelling "
                "for the bad-output directional equality only; it does not "
                "identify a complete weak-disposal technology under general "
                "returns to scale. Choose CommonFactorWeakDisposalDDF, "
                "ActivitySpecificWeakDisposalDDF, or disposability='strong'.",
                FutureWarning,
                stacklevel=2,
            )
        self.null_jointness = (
            self.disposability is BadOutputDisposability.WEAK
            if null_jointness is None
            else bool(null_jointness)
        )
        if self.disposability is BadOutputDisposability.STRONG and self.null_jointness:
            raise ModelSpecificationError(
                "strong disposability is incompatible with null_jointness=True: "
                "free contraction to zero would retain desirable output"
            )
        self.returns_to_scale = parse_enum(
            returns_to_scale, ReturnsToScale, "returns_to_scale"
        )
        self.reference = (
            ReferenceSpec()
            if reference is None
            else reference
            if isinstance(reference, ReferenceSpec)
            else ReferenceSpec(kind=reference)
        )
        if peer_eligibility is not None and not isinstance(
            peer_eligibility, PeerEligibility
        ):
            raise TypeError("peer_eligibility must be a PeerEligibility")
        self.peer_eligibility = peer_eligibility
        if solver is not None and solver_options is not None:
            raise ValueError("pass solver or solver_options, not both")
        self.solver = SciPyHiGHSSolver(solver_options) if solver is None else solver
        self.compute_slacks = bool(compute_slacks)
        self.allow_negative_distance = bool(allow_negative_distance)
        if not math.isfinite(tolerance) or tolerance <= 0:
            raise ValueError("tolerance must be positive and finite")
        self.tolerance = float(tolerance)
        self.peer_tolerance = (
            self.tolerance if peer_tolerance is None else float(peer_tolerance)
        )
        if not math.isfinite(self.peer_tolerance) or self.peer_tolerance <= 0:
            raise ValueError("peer_tolerance must be positive and finite")

    def _bad_output_identity(self) -> dict[str, str | None]:
        if self.disposability is BadOutputDisposability.STRONG:
            return {
                "technology_id": "environmental.joint_production.envelopment",
                "formulation_id": (
                    "environmental.formulation.bad_output_strong_disposal_inequality"
                ),
                "disposability_id": "environmental.disposal.strong",
                "treatment": "strong_disposal_inequality",
                "summary_label": "strong",
                "compatibility_alias": None,
                "named_equivalence": "not_applicable",
            }
        if self._weak_technology_id is not None:
            return {
                "technology_id": self._weak_technology_id,
                "formulation_id": (
                    "environmental.formulation.bad_output_directional_equality"
                ),
                "disposability_id": self._weak_technology_id,
                "treatment": "common_factor_weak_disposal",
                "summary_label": "weak_common_factor",
                "compatibility_alias": None,
                "named_equivalence": "source_exact_under_crs",
            }
        return {
            "technology_id": "environmental.joint_production.envelopment",
            "formulation_id": (
                "environmental.formulation.bad_output_directional_equality"
            ),
            "disposability_id": "not_identified",
            "treatment": "directional_equality_legacy",
            "summary_label": "not_identified",
            "compatibility_alias": "weak",
            "named_equivalence": "not_claimed",
        }

    def _validate_data(self, data: DEAData) -> None:
        data.ensure_nonnegative()
        if data.bad_outputs is None:
            raise ModelSpecificationError(
                "EnvironmentalDirectionalDistanceDEA requires declared "
                "bad_outputs in DEAData"
            )
        if self.null_jointness:
            positive_good = data.outputs.sum(axis=1) > 0.0
            zero_bad = data.bad_outputs.sum(axis=1) == 0.0
            invalid = positive_good & zero_bad
            if invalid.any():
                positions = np.flatnonzero(invalid)[:5].tolist()
                raise ModelSpecificationError(
                    "null jointness requires zero bad output to imply zero "
                    "desirable output; invalid row positions include "
                    f"{positions}"
                )

    def _unscaled_phase_one_problem(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        b_o: np.ndarray,
        g_x: np.ndarray,
        g_y: np.ndarray,
        g_b: np.ndarray,
        name: str,
    ) -> LinearProgram:
        if reference.bad_outputs is None:
            raise RuntimeError("compiled environmental reference lacks bad outputs")
        n_lambda = reference.size
        n_variables = n_lambda + 1
        input_rows = hstack(
            [reference.inputs, csc_matrix(g_x.reshape(-1, 1))], format="csc"
        )
        output_rows = hstack(
            [-reference.outputs, csc_matrix(g_y.reshape(-1, 1))], format="csc"
        )
        bad_rows = hstack(
            [reference.bad_outputs, csc_matrix(g_b.reshape(-1, 1))],
            format="csc",
        )

        a_ub = vstack([input_rows, output_rows], format="csc")
        b_ub = np.concatenate([x_o, -y_o])
        a_eq: csc_matrix | None = None
        b_eq: np.ndarray | None = None
        if self.disposability is BadOutputDisposability.STRONG:
            a_ub = vstack([a_ub, bad_rows], format="csc")
            b_ub = np.concatenate([b_ub, b_o])
        else:
            a_eq = bad_rows
            b_eq = b_o.copy()

        rts_ub, rts_b_ub, rts_eq, rts_b_eq = rts_matrices(
            n_variables, n_lambda, self.returns_to_scale
        )
        a_ub = join_optional_rows(a_ub, rts_ub)
        b_ub = join_optional_values(b_ub, rts_b_ub)
        if a_eq is None:
            a_eq = rts_eq
            b_eq = rts_b_eq
        elif rts_eq is not None:
            a_eq = join_optional_rows(a_eq, rts_eq)
            b_eq = join_optional_values(b_eq, rts_b_eq)

        objective = np.zeros(n_variables, dtype=np.float64)
        objective[-1] = -1.0
        beta_bounds = (None, None) if self.allow_negative_distance else (0.0, None)
        return LinearProgram(
            c=objective,
            a_ub=a_ub,
            b_ub=b_ub,
            a_eq=a_eq,
            b_eq=b_eq,
            bounds=((0.0, None),) * n_lambda + (beta_bounds,),
            name=f"{name}:environmental_directional",
        )

    def _phase_one_problem(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        b_o: np.ndarray,
        g_x: np.ndarray,
        g_y: np.ndarray,
        g_b: np.ndarray,
        name: str,
    ) -> LinearProgram:
        """Build a unit-stable environmental directional programme."""

        problem = self._unscaled_phase_one_problem(
            reference,
            x_o,
            y_o,
            b_o,
            g_x,
            g_y,
            g_b,
            name,
        )
        input_scales, output_scales, bad_scales = _environmental_row_scales(
            reference,
            x_o,
            y_o,
            b_o,
        )
        inequality_quantity_scales = [input_scales, output_scales]
        equality_quantity_scales: list[np.ndarray] = []
        if self.disposability is BadOutputDisposability.STRONG:
            inequality_quantity_scales.append(bad_scales)
        else:
            equality_quantity_scales.append(bad_scales)

        a_ub = problem.a_ub
        b_ub = problem.b_ub
        if a_ub is not None and b_ub is not None:
            quantity_scales = np.concatenate(inequality_quantity_scales)
            extra_rows = a_ub.shape[0] - quantity_scales.size
            if extra_rows < 0:
                raise RuntimeError("environmental inequality row layout is invalid")
            row_scales = (
                quantity_scales
                if extra_rows == 0
                else np.concatenate(
                    [quantity_scales, np.ones(extra_rows, dtype=np.float64)]
                )
            )
            a_ub = diags(1.0 / row_scales, format="csc") @ a_ub
            b_ub = np.asarray(b_ub, dtype=np.float64) / row_scales

        a_eq = problem.a_eq
        b_eq = problem.b_eq
        if a_eq is not None and b_eq is not None:
            quantity_scales = (
                np.concatenate(equality_quantity_scales)
                if equality_quantity_scales
                else np.zeros(0, dtype=np.float64)
            )
            extra_rows = a_eq.shape[0] - quantity_scales.size
            if extra_rows < 0:
                raise RuntimeError("environmental equality row layout is invalid")
            row_scales = (
                quantity_scales
                if extra_rows == 0
                else np.concatenate(
                    [quantity_scales, np.ones(extra_rows, dtype=np.float64)]
                )
            )
            a_eq = diags(1.0 / row_scales, format="csc") @ a_eq
            b_eq = np.asarray(b_eq, dtype=np.float64) / row_scales

        return LinearProgram(
            c=problem.c,
            a_ub=a_ub,
            b_ub=b_ub,
            a_eq=a_eq,
            b_eq=b_eq,
            bounds=problem.bounds,
            name=problem.name,
        )

    @staticmethod
    def _reference_membership_problem(
        phase_one_problem: LinearProgram,
    ) -> LinearProgram:
        """Fix beta at zero to test the assessed plan itself.

        A nonnegative optimal environmental DDF is sufficient for membership
        under strong disposal, but not under a bad-output equality.  The
        latter can admit a positive interval of directional steps even when
        beta zero is infeasible.  Reusing the scaled primary rows gives that
        external-reference boundary one explicit, auditable feasibility LP.
        """

        if not phase_one_problem.bounds:
            raise RuntimeError("environmental membership requires beta bounds")
        return LinearProgram(
            c=np.zeros_like(phase_one_problem.c),
            a_ub=phase_one_problem.a_ub,
            b_ub=phase_one_problem.b_ub,
            a_eq=phase_one_problem.a_eq,
            b_eq=phase_one_problem.b_eq,
            bounds=(*phase_one_problem.bounds[:-1], (0.0, 0.0)),
            name=f"{phase_one_problem.name}:reference_membership",
        )

    def _phase_two_problem(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        b_o: np.ndarray,
        g_x: np.ndarray,
        g_y: np.ndarray,
        g_b: np.ndarray,
        beta: float,
        name: str,
    ) -> LinearProgram:
        if reference.bad_outputs is None:
            raise RuntimeError("compiled environmental reference lacks bad outputs")
        n_lambda = reference.size
        m = x_o.size
        s = y_o.size
        q = b_o.size
        has_bad_slack = self.disposability is BadOutputDisposability.STRONG
        n_bad_slack = q if has_bad_slack else 0
        n_variables = n_lambda + m + s + n_bad_slack
        input_scales, output_scales, bad_output_scales = _environmental_row_scales(
            reference, x_o, y_o, b_o
        )

        input_rows = hstack(
            [
                diags(1.0 / input_scales, format="csc") @ reference.inputs,
                eye(m, format="csc"),
                csc_matrix((m, s + n_bad_slack)),
            ],
            format="csc",
        )
        output_rows = hstack(
            [
                diags(1.0 / output_scales, format="csc") @ reference.outputs,
                csc_matrix((s, m)),
                -eye(s, format="csc"),
                csc_matrix((s, n_bad_slack)),
            ],
            format="csc",
        )
        if has_bad_slack:
            bad_rows = hstack(
                [
                    diags(1.0 / bad_output_scales, format="csc")
                    @ reference.bad_outputs,
                    csc_matrix((q, m + s)),
                    eye(q, format="csc"),
                ],
                format="csc",
            )
        else:
            bad_rows = hstack(
                [
                    diags(1.0 / bad_output_scales, format="csc")
                    @ reference.bad_outputs,
                    csc_matrix((q, m + s)),
                ],
                format="csc",
            )
        a_eq = vstack([input_rows, output_rows, bad_rows], format="csc")
        b_eq = np.concatenate(
            [
                (x_o - beta * g_x) / input_scales,
                (y_o + beta * g_y) / output_scales,
                (b_o - beta * g_b) / bad_output_scales,
            ]
        )

        rts_ub, rts_b_ub, rts_eq, rts_b_eq = rts_matrices(
            n_variables, n_lambda, self.returns_to_scale
        )
        a_eq = join_optional_rows(a_eq, rts_eq)
        b_eq = join_optional_values(b_eq, rts_b_eq)

        objective = np.zeros(n_variables, dtype=np.float64)
        objective[n_lambda:] = -1.0
        return LinearProgram(
            c=objective,
            a_ub=rts_ub,
            b_ub=rts_b_ub,
            a_eq=a_eq,
            b_eq=b_eq,
            bounds=((0.0, None),) * n_variables,
            name=f"{name}:environmental_slacks",
        )

    def _primary_economic_violation(
        self,
        *,
        reference: CompiledReference,
        solution: LPSolution,
        x_o: np.ndarray,
        y_o: np.ndarray,
        b_o: np.ndarray,
        g_x: np.ndarray,
        g_y: np.ndarray,
        g_b: np.ndarray,
        primal_override: np.ndarray | None = None,
    ) -> float:
        """Reconstruct the declared environmental programme from a primal."""
        primal_source = solution.primal if primal_override is None else primal_override
        if (
            primal_source is None
            or solution.objective is None
            or not math.isfinite(solution.objective)
        ):
            return math.inf
        primal = np.asarray(primal_source, dtype=np.float64).reshape(-1)
        if primal.shape != (reference.size + 1,) or not np.isfinite(primal).all():
            return math.inf
        lambdas = primal[: reference.size]
        beta = float(primal[-1])
        if not math.isfinite(beta):
            return math.inf

        if reference.bad_outputs is None:
            return math.inf
        with np.errstate(over="ignore", invalid="ignore"):
            represented_inputs = np.asarray(reference.inputs @ lambdas).reshape(-1)
            represented_outputs = np.asarray(reference.outputs @ lambdas).reshape(-1)
            represented_bad = np.asarray(reference.bad_outputs @ lambdas).reshape(-1)
            declared_inputs = np.asarray(x_o, dtype=np.float64) - beta * np.asarray(
                g_x,
                dtype=np.float64,
            )
            declared_outputs = np.asarray(y_o, dtype=np.float64) + beta * np.asarray(
                g_y,
                dtype=np.float64,
            )
            declared_bad = np.asarray(b_o, dtype=np.float64) - beta * np.asarray(
                g_b,
                dtype=np.float64,
            )
        if not all(
            np.isfinite(values).all()
            for values in (
                represented_inputs,
                represented_outputs,
                represented_bad,
                declared_inputs,
                declared_outputs,
                declared_bad,
            )
        ):
            return math.inf
        input_scales, output_scales, bad_scales = _environmental_row_scales(
            reference,
            x_o,
            y_o,
            b_o,
        )
        violations = [
            _scaled_nonnegative_violation(lambdas),
            _scaled_nonnegative_violation(represented_inputs),
            _scaled_nonnegative_violation(represented_outputs),
            _scaled_nonnegative_violation(represented_bad),
            _scaled_maximum(
                np.maximum(represented_inputs - declared_inputs, 0.0),
                input_scales,
            ),
            _scaled_maximum(
                np.maximum(declared_outputs - represented_outputs, 0.0),
                output_scales,
            ),
            _rts_violation(lambdas, self.returns_to_scale),
            abs(float(solution.objective) + beta)
            / max(1.0, abs(float(solution.objective)), abs(beta)),
        ]
        if self.disposability is BadOutputDisposability.STRONG:
            violations.append(
                _scaled_maximum(
                    np.maximum(represented_bad - declared_bad, 0.0),
                    bad_scales,
                )
            )
        else:
            violations.append(
                _scaled_maximum(represented_bad - declared_bad, bad_scales)
            )
        if not self.allow_negative_distance:
            violations.append(max(-beta, 0.0) / max(1.0, abs(beta)))
        return (
            float(max(violations)) if all(map(math.isfinite, violations)) else math.inf
        )

    def _completion_economic_violation(
        self,
        *,
        reference: CompiledReference,
        solution: LPSolution,
        beta: float,
        x_o: np.ndarray,
        y_o: np.ndarray,
        b_o: np.ndarray,
        g_x: np.ndarray,
        g_y: np.ndarray,
        g_b: np.ndarray,
        primal_override: np.ndarray | None = None,
    ) -> float:
        """Reconstruct the optional row-scaled slack-completion account."""
        if solution.primal is None or solution.objective is None:
            return math.inf
        primal = np.asarray(
            solution.primal if primal_override is None else primal_override,
            dtype=np.float64,
        )
        n_lambda = reference.size
        offset = n_lambda
        lambdas = primal[:n_lambda]
        scaled_input_slacks = primal[offset : offset + x_o.size]
        offset += x_o.size
        scaled_output_slacks = primal[offset : offset + y_o.size]
        offset += y_o.size
        scaled_bad_slacks = (
            primal[offset : offset + b_o.size]
            if self.disposability is BadOutputDisposability.STRONG
            else None
        )
        arrays = [lambdas, scaled_input_slacks, scaled_output_slacks]
        if scaled_bad_slacks is not None:
            arrays.append(scaled_bad_slacks)
        if not all(np.isfinite(values).all() for values in arrays):
            return math.inf
        if not math.isfinite(beta) or not math.isfinite(solution.objective):
            return math.inf

        input_scales, output_scales, bad_scales = _environmental_row_scales(
            reference,
            x_o,
            y_o,
            b_o,
        )
        input_slacks = scaled_input_slacks * input_scales
        output_slacks = scaled_output_slacks * output_scales
        bad_slacks = (
            None if scaled_bad_slacks is None else scaled_bad_slacks * bad_scales
        )
        if reference.bad_outputs is None:
            return math.inf
        represented_inputs = np.asarray(reference.inputs @ lambdas).reshape(-1)
        represented_outputs = np.asarray(reference.outputs @ lambdas).reshape(-1)
        represented_bad = np.asarray(reference.bad_outputs @ lambdas).reshape(-1)
        declared_inputs = x_o - beta * g_x
        declared_outputs = y_o + beta * g_y
        declared_bad = b_o - beta * g_b
        violations = [
            _scaled_maximum(
                represented_inputs + input_slacks - declared_inputs,
                input_scales,
            ),
            _scaled_maximum(
                represented_outputs - output_slacks - declared_outputs,
                output_scales,
            ),
            _rts_violation(lambdas, self.returns_to_scale),
        ]
        if bad_slacks is None:
            violations.append(
                _scaled_maximum(represented_bad - declared_bad, bad_scales)
            )
        else:
            violations.append(
                _scaled_maximum(
                    represented_bad + bad_slacks - declared_bad,
                    bad_scales,
                )
            )
        reconstructed_objective = -float(
            scaled_input_slacks.sum()
            + scaled_output_slacks.sum()
            + (0.0 if scaled_bad_slacks is None else scaled_bad_slacks.sum())
        )
        violations.append(
            abs(reconstructed_objective - float(solution.objective))
            / max(
                1.0,
                abs(reconstructed_objective),
                abs(float(solution.objective)),
            )
        )
        return (
            float(max(violations)) if all(map(math.isfinite, violations)) else math.inf
        )

    def _undefined_summary(
        self,
        *,
        dmu_id: object,
        period: object | None,
        reference_size: int,
        bad_output_identity: dict[str, str | None],
        solver_status: SolverStatus,
        score_status: str,
        self_in_reference: bool,
    ) -> dict[str, Any]:
        within_reference: bool | Any = (
            True
            if self_in_reference
            else False
            if solver_status is SolverStatus.INFEASIBLE
            else pd.NA
        )
        membership_status = (
            "certified_by_self_inclusion"
            if self_in_reference
            else "outside_reference_technology"
            if solver_status is SolverStatus.INFEASIBLE
            else "not_available_without_certified_primary"
        )
        return {
            "dmu_id": dmu_id,
            "period": period,
            "score": np.nan,
            "efficiency": np.nan,
            "score_valid": False,
            "score_status": score_status,
            "distance": np.nan,
            "is_efficient": pd.NA,
            "is_directionally_efficient": pd.NA,
            "is_within_reference_technology": within_reference,
            "self_in_reference": self_in_reference,
            "membership_status": membership_status,
            "solver_status": solver_status.value,
            "completion_solver_status": pd.NA,
            "completion_valid": False,
            "completion_status": "not_available_without_certified_primary",
            "target_valid": False,
            "target_status": "not_available_without_certified_primary",
            "peer_valid": False,
            "peer_status": "not_available_without_certified_primary",
            "dual_valid": False,
            "dual_status": "not_available_without_certified_primary",
            "model_family": "environmental_directional_distance",
            "orientation": "environmental_directional",
            "returns_to_scale": self.returns_to_scale.value,
            "bad_output_disposability": bad_output_identity["summary_label"],
            "compatibility_alias": bad_output_identity["compatibility_alias"],
            "null_jointness": self.null_jointness,
            "reference_size": reference_size,
            "max_slack": np.nan,
            "max_scaled_slack": np.nan,
            "efficiency_denominator_valid": (
                within_reference if isinstance(within_reference, bool) else pd.NA
            ),
        }

    def _dual_rows(
        self,
        data: DEAData,
        observation: int,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        b_o: np.ndarray,
        solution: LPSolution,
    ) -> list[dict[str, Any]]:
        expected_inequalities = (
            data.n_inputs
            + data.n_outputs
            + (
                data.n_bad_outputs
                if self.disposability is BadOutputDisposability.STRONG
                else 0
            )
            + int(self.returns_to_scale in {ReturnsToScale.NIRS, ReturnsToScale.NDRS})
        )
        expected_equalities = (
            data.n_bad_outputs
            if self.disposability is BadOutputDisposability.WEAK
            else 0
        ) + int(self.returns_to_scale is ReturnsToScale.VRS)
        if solution.inequality_marginals is None:
            return []
        inequality_marginals = np.asarray(
            solution.inequality_marginals,
            dtype=np.float64,
        )
        if (
            inequality_marginals.shape != (expected_inequalities,)
            or not np.isfinite(inequality_marginals).all()
        ):
            return []
        equality_marginals = (
            np.zeros(0, dtype=np.float64)
            if solution.equality_marginals is None and expected_equalities == 0
            else (
                None
                if solution.equality_marginals is None
                else np.asarray(solution.equality_marginals, dtype=np.float64)
            )
        )
        if (
            equality_marginals is None
            or equality_marginals.shape != (expected_equalities,)
            or not np.isfinite(equality_marginals).all()
        ):
            return []

        period = None if data.periods is None else data.periods[observation]
        common = {"dmu_id": data.dmu_ids[observation], "period": period, "phase": 1}
        input_scales, output_scales, bad_scales = _environmental_row_scales(
            reference,
            x_o,
            y_o,
            b_o,
        )
        rows: list[dict[str, Any]] = []
        inequality_offset = 0
        for role, names, scales in (
            ("input", data.input_names, input_scales),
            ("output", data.output_names, output_scales),
        ):
            for variable, scale in zip(names, scales, strict=True):
                rows.append(
                    {
                        **common,
                        "constraint_role": role,
                        "variable": variable,
                        "marginal": float(
                            inequality_marginals[inequality_offset] / scale
                        ),
                    }
                )
                inequality_offset += 1
        equality_offset = 0
        if self.disposability is BadOutputDisposability.STRONG:
            for variable, scale in zip(
                data.bad_output_names,
                bad_scales,
                strict=True,
            ):
                rows.append(
                    {
                        **common,
                        "constraint_role": "bad_output",
                        "variable": variable,
                        "marginal": float(
                            inequality_marginals[inequality_offset] / scale
                        ),
                    }
                )
                inequality_offset += 1
        else:
            for variable, scale in zip(
                data.bad_output_names,
                bad_scales,
                strict=True,
            ):
                rows.append(
                    {
                        **common,
                        "constraint_role": "bad_output",
                        "variable": variable,
                        "marginal": float(equality_marginals[equality_offset] / scale),
                    }
                )
                equality_offset += 1
        if self.returns_to_scale is ReturnsToScale.VRS:
            rows.append(
                {
                    **common,
                    "constraint_role": "returns_to_scale",
                    "variable": self.returns_to_scale.value,
                    "marginal": float(equality_marginals[equality_offset]),
                }
            )
        elif self.returns_to_scale in {ReturnsToScale.NIRS, ReturnsToScale.NDRS}:
            rows.append(
                {
                    **common,
                    "constraint_role": "returns_to_scale",
                    "variable": self.returns_to_scale.value,
                    "marginal": float(inequality_marginals[inequality_offset]),
                }
            )
        return rows

    def fit(self, data: DEAData) -> DEAResult:
        """Estimate environmental directional distances for all observations."""
        self._validate_data(data)
        if data.bad_outputs is None:
            raise RuntimeError("validated environmental data lost bad outputs")
        bad_output_identity = self._bad_output_identity()

        input_directions, input_direction_kind = _resolve_direction(
            self.input_direction, data.inputs, data.input_names, "input"
        )
        output_directions, output_direction_kind = _resolve_direction(
            self.output_direction, data.outputs, data.output_names, "output"
        )
        bad_directions, bad_direction_kind = _resolve_direction(
            self.bad_output_direction,
            data.bad_outputs,
            data.bad_output_names,
            "bad_output",
        )
        zero_direction = (
            input_directions.sum(axis=1)
            + output_directions.sum(axis=1)
            + bad_directions.sum(axis=1)
        ) <= 0
        if zero_direction.any():
            positions = np.flatnonzero(zero_direction)[:5].tolist()
            raise ModelSpecificationError(
                "each evaluated observation needs at least one positive direction "
                f"component; zero-direction row positions include {positions}"
            )

        reference_plan = build_reference_plan(
            data,
            self.reference,
            peer_eligibility=self.peer_eligibility,
        )
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
        phase_one_solver_calls = 0
        phase_two_solver_calls = 0
        membership_solver_calls = 0

        for observation in range(data.n_dmus):
            set_id = reference_plan.set_id_for(observation)
            reference_rows = reference_plan.rows_for(observation)
            reference = compiled.get(set_id)
            if reference is None:
                reference = compile_reference(data, reference_rows)
                compiled[set_id] = reference
            dmu_id = data.dmu_ids[observation]
            period = None if data.periods is None else data.periods[observation]
            name = f"{dmu_id}@{period}" if period is not None else str(dmu_id)
            x_o = data.inputs[observation]
            y_o = data.outputs[observation]
            b_o = data.bad_outputs[observation]
            g_x = input_directions[observation]
            g_y = output_directions[observation]
            g_b = bad_directions[observation]
            phase_one_problem = self._phase_one_problem(
                reference,
                x_o,
                y_o,
                b_o,
                g_x,
                g_y,
                g_b,
                name,
            )
            phase_one = self.solver.solve(phase_one_problem)
            phase_one_solver_calls += 1

            def primary_account(
                primal_override: np.ndarray | None,
                reference_account: CompiledReference = reference,
                solution_account: LPSolution = phase_one,
                input_account: np.ndarray = x_o,
                output_account: np.ndarray = y_o,
                bad_account: np.ndarray = b_o,
                input_direction_account: np.ndarray = g_x,
                output_direction_account: np.ndarray = g_y,
                bad_direction_account: np.ndarray = g_b,
            ) -> float:
                return self._primary_economic_violation(
                    reference=reference_account,
                    solution=solution_account,
                    x_o=input_account,
                    y_o=output_account,
                    b_o=bad_account,
                    g_x=input_direction_account,
                    g_y=output_direction_account,
                    g_b=bad_direction_account,
                    primal_override=primal_override,
                )

            primary_task = _certify_environmental_distance_task(
                problem=phase_one_problem,
                solution=phase_one,
                n_lambdas=reference.size,
                account_violation=primary_account,
                tolerance=self.tolerance,
                peer_tolerance=self.peer_tolerance,
                beta_nonnegative=not self.allow_negative_distance,
            )
            diagnostic_rows.append(
                _certificate_diagnostic(
                    dmu_id=dmu_id,
                    period=period,
                    phase=1,
                    solution=phase_one,
                    certificate=primary_task.certificate,
                )
            )
            if primary_task.raw_economic_certified is not None:
                diagnostic_rows[-1]["raw_economic_postsolve_certified"] = (
                    primary_task.raw_economic_certified
                )
                diagnostic_rows[-1]["max_raw_economic_violation"] = (
                    primary_task.raw_economic_violation
                )
                diagnostic_rows[-1]["economic_postsolve_certified"] = (
                    primary_task.score_valid
                )
                diagnostic_rows[-1]["economic_certification_reason"] = (
                    primary_task.economic_certification_reason
                )
                diagnostic_rows[-1]["max_economic_violation"] = (
                    primary_task.published_economic_violation
                    if primary_task.published_economic_certified is not None
                    else primary_task.raw_economic_violation
                )
                diagnostic_rows[-1]["postsolve_certified"] = primary_task.score_valid
            if primary_task.published_economic_certified is not None:
                diagnostic_rows[-1]["published_output_account_certified"] = (
                    primary_task.published_economic_certified
                )
                diagnostic_rows[-1]["max_published_account_violation"] = (
                    primary_task.published_economic_violation
                )
            if primary_task.score_valid:
                diagnostic_rows[-1]["published_peer_account_certified"] = (
                    primary_task.peer_valid
                )
                diagnostic_rows[-1]["max_published_peer_account_violation"] = (
                    primary_task.peer_economic_violation
                )
            elif primary_task.certificate.certified:
                diagnostic_rows[-1]["certification_reason"] = (
                    primary_task.economic_certification_reason
                )
            if not primary_task.score_valid:
                score_status = (
                    "outside_reference_technology"
                    if (
                        phase_one.status is SolverStatus.INFEASIBLE
                        and not self_membership[observation]
                    )
                    else primary_task.score_status
                )
                diagnostic_rows[-1]["score_status"] = score_status
                summary_rows.append(
                    self._undefined_summary(
                        dmu_id=dmu_id,
                        period=period,
                        reference_size=reference.size,
                        bad_output_identity=bad_output_identity,
                        solver_status=phase_one.status,
                        score_status=score_status,
                        self_in_reference=self_membership[observation],
                    )
                )
                continue

            assert primary_task.distance is not None
            assert primary_task.published_primal is not None
            diagnostic_rows[-1]["certification_reason"] = "certified"
            beta = primary_task.distance
            primary_peer_valid = primary_task.peer_valid
            phase_one_peer_lambdas = primary_task.peer_lambdas

            primary_dual_rows = self._dual_rows(
                data,
                observation,
                reference,
                x_o,
                y_o,
                b_o,
                phase_one,
            )
            expected_dual_rows = (
                data.n_inputs
                + data.n_outputs
                + data.n_bad_outputs
                + int(self.returns_to_scale is not ReturnsToScale.CRS)
            )
            primary_dual_valid = len(primary_dual_rows) == expected_dual_rows
            primary_dual_status = (
                "certified_primary_program"
                if primary_dual_valid
                else "unavailable_incomplete_primary_dual_account"
            )
            diagnostic_rows[-1]["published_dual_account_certified"] = primary_dual_valid
            diagnostic_rows[-1]["published_dual_row_count"] = len(primary_dual_rows)
            if primary_dual_valid:
                dual_rows.extend(primary_dual_rows)

            self_in_reference = self_membership[observation]
            within_reference: bool | Any
            membership_status: str
            if self_in_reference:
                within_reference = True
                membership_status = "certified_by_self_inclusion"
            elif beta < 0.0:
                within_reference = False
                membership_status = "outside_reference_technology"
            elif self.disposability is BadOutputDisposability.STRONG:
                # The certified beta plan uses no more inputs or bad outputs
                # and supplies no less desirable output.  Strong disposal
                # therefore makes the assessed beta-zero plan attainable.
                within_reference = True
                membership_status = "certified_by_strong_disposal_monotonicity"
            else:
                membership_problem = self._reference_membership_problem(
                    phase_one_problem
                )
                membership_solution = self.solver.solve(membership_problem)
                membership_solver_calls += 1
                membership_certificate = certify_lp_solution(
                    membership_problem,
                    membership_solution,
                    tolerance=self.tolerance,
                )
                membership_diagnostic = _certificate_diagnostic(
                    dmu_id=dmu_id,
                    period=period,
                    phase=0,
                    solution=membership_solution,
                    certificate=membership_certificate,
                )
                membership_diagnostic["diagnostic_kind"] = "reference_membership"
                membership_economic_violation = math.nan
                if membership_solution.status is SolverStatus.INFEASIBLE:
                    within_reference = False
                    membership_status = "outside_reference_technology"
                    membership_diagnostic["certification_reason"] = (
                        "infeasible_reference_membership_program"
                    )
                elif (
                    membership_certificate.certified
                    and membership_solution.primal is not None
                ):
                    membership_primal = clean_small(
                        np.asarray(membership_solution.primal, dtype=np.float64),
                        self.tolerance,
                    )
                    membership_primal[: reference.size] = np.maximum(
                        membership_primal[: reference.size],
                        0.0,
                    )
                    membership_primal[-1] = 0.0
                    membership_economic_violation = self._primary_economic_violation(
                        reference=reference,
                        solution=membership_solution,
                        x_o=x_o,
                        y_o=y_o,
                        b_o=b_o,
                        g_x=g_x,
                        g_y=g_y,
                        g_b=g_b,
                        primal_override=membership_primal,
                    )
                    membership_certified = bool(
                        math.isfinite(membership_economic_violation)
                        and membership_economic_violation <= 10.0 * self.tolerance
                    )
                    within_reference = True if membership_certified else pd.NA
                    membership_status = (
                        "certified_by_reference_membership_program"
                        if membership_certified
                        else "unavailable_uncertified_reference_membership"
                    )
                    membership_diagnostic["economic_postsolve_certified"] = (
                        membership_certified
                    )
                    membership_diagnostic["postsolve_certified"] = membership_certified
                    membership_diagnostic["certification_reason"] = (
                        "certified"
                        if membership_certified
                        else "reference_membership_account_reconstruction_failed"
                    )
                else:
                    within_reference = pd.NA
                    membership_status = "unavailable_uncertified_reference_membership"
                membership_diagnostic["max_economic_violation"] = (
                    membership_economic_violation
                )
                diagnostic_rows.append(membership_diagnostic)

            efficiency_denominator_valid: bool | Any = (
                within_reference if isinstance(within_reference, bool) else pd.NA
            )
            efficiency = 1.0 / (1.0 + beta) if within_reference is True else np.nan
            is_directionally_efficient: bool | Any = (
                bool(beta == 0.0) if within_reference is True else pd.NA
            )

            phase_two: LPSolution | None = None
            completion_solver_status: object = pd.NA
            completion_valid: bool | Any = pd.NA
            completion_status = "not_requested"
            target_valid: bool | Any = pd.NA
            target_status = "not_requested"
            peer_valid = primary_peer_valid
            peer_status = primary_task.peer_status
            dual_valid = primary_dual_valid
            dual_status = primary_dual_status
            phase_two_publish_primal: np.ndarray | None = None
            phase_two_peer_primal: np.ndarray | None = None
            if self.compute_slacks:
                phase_two_problem = self._phase_two_problem(
                    reference,
                    x_o,
                    y_o,
                    b_o,
                    g_x,
                    g_y,
                    g_b,
                    beta,
                    name,
                )
                phase_two = self.solver.solve(phase_two_problem)
                phase_two_solver_calls += 1
                phase_two_certificate = certify_lp_solution(
                    phase_two_problem,
                    phase_two,
                    tolerance=self.tolerance,
                )
                diagnostic_rows.append(
                    _certificate_diagnostic(
                        dmu_id=dmu_id,
                        period=period,
                        phase=2,
                        solution=phase_two,
                        certificate=phase_two_certificate,
                    )
                )
                completion_solver_status = phase_two.status.value
                completion_valid = False
                target_valid = False
                peer_valid = False
                completion_status = (
                    "completion_solver_failed"
                    if phase_two.status is not SolverStatus.OPTIMAL
                    else "unavailable_uncertified_slack_completion"
                )
                target_status = completion_status
                peer_status = completion_status
                if phase_two_certificate.certified and phase_two.primal is not None:
                    raw_completion_economic_violation = (
                        self._completion_economic_violation(
                            reference=reference,
                            solution=phase_two,
                            beta=beta,
                            x_o=x_o,
                            y_o=y_o,
                            b_o=b_o,
                            g_x=g_x,
                            g_y=g_y,
                            g_b=g_b,
                        )
                    )
                    raw_completion_economic_certified = bool(
                        math.isfinite(raw_completion_economic_violation)
                        and raw_completion_economic_violation <= 10.0 * self.tolerance
                    )
                    diagnostic_rows[-1]["raw_economic_postsolve_certified"] = (
                        raw_completion_economic_certified
                    )
                    diagnostic_rows[-1]["max_raw_economic_violation"] = (
                        raw_completion_economic_violation
                    )
                    if raw_completion_economic_certified:
                        phase_two_publish_primal = clean_small(
                            np.asarray(phase_two.primal, dtype=np.float64),
                            self.tolerance,
                        )
                        phase_two_publish_primal = np.maximum(
                            phase_two_publish_primal,
                            0.0,
                        )
                        published_completion_economic_violation = (
                            self._completion_economic_violation(
                                reference=reference,
                                solution=phase_two,
                                beta=beta,
                                x_o=x_o,
                                y_o=y_o,
                                b_o=b_o,
                                g_x=g_x,
                                g_y=g_y,
                                g_b=g_b,
                                primal_override=phase_two_publish_primal,
                            )
                        )
                    else:
                        published_completion_economic_violation = math.inf
                    completion_economic_certified = bool(
                        math.isfinite(published_completion_economic_violation)
                        and published_completion_economic_violation
                        <= 10.0 * self.tolerance
                    )
                    diagnostic_rows[-1]["published_output_account_certified"] = (
                        completion_economic_certified
                    )
                    diagnostic_rows[-1]["published_peer_account_certified"] = False
                    diagnostic_rows[-1]["max_published_account_violation"] = (
                        published_completion_economic_violation
                    )
                    diagnostic_rows[-1]["economic_postsolve_certified"] = (
                        completion_economic_certified
                    )
                    diagnostic_rows[-1]["economic_certification_reason"] = (
                        "certified"
                        if completion_economic_certified
                        else (
                            "published_environmental_account_reconstruction_failed"
                            if raw_completion_economic_certified
                            else "environmental_slack_account_reconstruction_failed"
                        )
                    )
                    diagnostic_rows[-1]["max_economic_violation"] = (
                        published_completion_economic_violation
                        if raw_completion_economic_certified
                        else raw_completion_economic_violation
                    )
                    diagnostic_rows[-1]["postsolve_certified"] = (
                        completion_economic_certified
                    )
                    if completion_economic_certified:
                        completion_valid = True
                        target_valid = True
                        completion_status = "certified"
                        target_status = "certified_slack_completion"
                        phase_two_peer_primal = phase_two_publish_primal.copy()
                        phase_two_peer_primal[: reference.size][
                            phase_two_peer_primal[: reference.size]
                            <= self.peer_tolerance
                        ] = 0.0
                        published_completion_peer_violation = (
                            self._completion_economic_violation(
                                reference=reference,
                                solution=phase_two,
                                beta=beta,
                                x_o=x_o,
                                y_o=y_o,
                                b_o=b_o,
                                g_x=g_x,
                                g_y=g_y,
                                g_b=g_b,
                                primal_override=phase_two_peer_primal,
                            )
                        )
                        peer_valid = bool(
                            math.isfinite(published_completion_peer_violation)
                            and published_completion_peer_violation
                            <= 10.0 * self.tolerance
                        )
                        peer_status = (
                            "certified_slack_completion"
                            if peer_valid
                            else "unavailable_after_peer_reporting_threshold"
                        )
                        diagnostic_rows[-1]["published_peer_account_certified"] = (
                            peer_valid
                        )
                        diagnostic_rows[-1]["max_published_peer_account_violation"] = (
                            published_completion_peer_violation
                        )
                    else:
                        diagnostic_rows[-1]["certification_reason"] = diagnostic_rows[
                            -1
                        ]["economic_certification_reason"]

            has_slack_solution = bool(completion_valid is True)
            if has_slack_solution:
                assert phase_two_publish_primal is not None
                n_lambda = reference.size
                input_scales, output_scales, bad_output_scales = (
                    _environmental_row_scales(reference, x_o, y_o, b_o)
                )
                offset = n_lambda
                lambdas = (
                    phase_two_peer_primal[:n_lambda]
                    if peer_valid and phase_two_peer_primal is not None
                    else np.zeros(n_lambda, dtype=np.float64)
                )
                scaled_input_slacks = clean_small(
                    phase_two_publish_primal[offset : offset + data.n_inputs],
                    self.tolerance,
                )
                offset += data.n_inputs
                scaled_output_slacks = clean_small(
                    phase_two_publish_primal[offset : offset + data.n_outputs],
                    self.tolerance,
                )
                offset += data.n_outputs
                if self.disposability is BadOutputDisposability.STRONG:
                    scaled_bad_slacks = clean_small(
                        phase_two_publish_primal[offset : offset + data.n_bad_outputs],
                        self.tolerance,
                    )
                else:
                    scaled_bad_slacks = None
                input_slacks = scaled_input_slacks * input_scales
                output_slacks = scaled_output_slacks * output_scales
                bad_slacks = (
                    None
                    if scaled_bad_slacks is None
                    else scaled_bad_slacks * bad_output_scales
                )
                input_targets = x_o - beta * g_x - input_slacks
                output_targets = y_o + beta * g_y + output_slacks
                bad_targets = (
                    b_o - beta * g_b
                    if bad_slacks is None
                    else b_o - beta * g_b - bad_slacks
                )
                slack_maxima = [
                    input_slacks.max(initial=0.0),
                    output_slacks.max(initial=0.0),
                ]
                if bad_slacks is not None:
                    slack_maxima.append(bad_slacks.max(initial=0.0))
                max_slack = float(max(slack_maxima))
                scaled_slack_maxima = [
                    scaled_input_slacks.max(initial=0.0),
                    scaled_output_slacks.max(initial=0.0),
                ]
                if scaled_bad_slacks is not None:
                    scaled_slack_maxima.append(scaled_bad_slacks.max(initial=0.0))
                max_scaled_slack = float(max(scaled_slack_maxima))
                if within_reference is not True:
                    is_efficient: bool | Any = pd.NA
                elif beta != 0.0 or max_scaled_slack > self.tolerance:
                    is_efficient = False
                elif bad_slacks is None:
                    is_efficient = pd.NA
                else:
                    is_efficient = True
            else:
                lambdas = (
                    phase_one_peer_lambdas
                    if (
                        not self.compute_slacks
                        and peer_valid
                        and phase_one_peer_lambdas is not None
                    )
                    else np.zeros(reference.size, dtype=np.float64)
                )
                input_targets = np.full(data.n_inputs, np.nan)
                output_targets = np.full(data.n_outputs, np.nan)
                bad_targets = np.full(data.n_bad_outputs, np.nan)
                input_slacks = np.full(data.n_inputs, np.nan)
                output_slacks = np.full(data.n_outputs, np.nan)
                bad_slacks = (
                    np.full(data.n_bad_outputs, np.nan)
                    if self.disposability is BadOutputDisposability.STRONG
                    else None
                )
                max_slack = np.nan
                max_scaled_slack = np.nan
                is_efficient = pd.NA

            if peer_valid:
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
                            }
                        )

            if has_slack_solution:
                input_scales, output_scales, bad_output_scales = (
                    _environmental_row_scales(reference, x_o, y_o, b_o)
                )
                role_blocks = [
                    (
                        "input",
                        data.input_names,
                        x_o,
                        input_targets,
                        g_x,
                        input_slacks,
                        input_scales,
                        True,
                    ),
                    (
                        "output",
                        data.output_names,
                        y_o,
                        output_targets,
                        g_y,
                        output_slacks,
                        output_scales,
                        True,
                    ),
                    (
                        "bad_output",
                        data.bad_output_names,
                        b_o,
                        bad_targets,
                        g_b,
                        bad_slacks,
                        bad_output_scales,
                        bad_slacks is not None,
                    ),
                ]
                for (
                    role,
                    names,
                    observed,
                    targets,
                    directions,
                    slacks,
                    scales,
                    slack_allowed,
                ) in role_blocks:
                    for position, (
                        variable,
                        value,
                        target,
                        direction,
                        scale,
                    ) in enumerate(
                        zip(
                            names,
                            observed,
                            targets,
                            directions,
                            scales,
                            strict=True,
                        )
                    ):
                        target_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": period,
                                "role": role,
                                "variable": variable,
                                "observed": float(value),
                                "target": float(target),
                                "direction": float(direction),
                                "directional_change": float(beta * direction),
                                "slack_allowed": slack_allowed,
                            }
                        )
                        if slacks is not None:
                            slack_rows.append(
                                {
                                    "dmu_id": dmu_id,
                                    "period": period,
                                    "role": role,
                                    "variable": variable,
                                    "slack": float(slacks[position]),
                                    "scaled_slack": float(slacks[position] / scale),
                                }
                            )

            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "score": beta,
                    "efficiency": efficiency,
                    "score_valid": True,
                    "score_status": "defined",
                    "distance": beta,
                    "is_efficient": is_efficient,
                    "is_directionally_efficient": is_directionally_efficient,
                    "is_within_reference_technology": within_reference,
                    "self_in_reference": self_in_reference,
                    "membership_status": membership_status,
                    "solver_status": phase_one.status.value,
                    "completion_solver_status": completion_solver_status,
                    "completion_valid": completion_valid,
                    "completion_status": completion_status,
                    "target_valid": target_valid,
                    "target_status": target_status,
                    "peer_valid": peer_valid,
                    "peer_status": peer_status,
                    "dual_valid": dual_valid,
                    "dual_status": dual_status,
                    "model_family": "environmental_directional_distance",
                    "orientation": "environmental_directional",
                    "returns_to_scale": self.returns_to_scale.value,
                    "bad_output_disposability": bad_output_identity["summary_label"],
                    "compatibility_alias": bad_output_identity["compatibility_alias"],
                    "null_jointness": self.null_jointness,
                    "reference_size": reference.size,
                    "max_slack": max_slack,
                    "max_scaled_slack": max_scaled_slack,
                    "efficiency_denominator_valid": (efficiency_denominator_valid),
                }
            )

        summary_frame = pd.DataFrame(summary_rows)
        summary_frame["base_reference_size"] = reference_plan.base_size_by_observation
        peer_eligibility_metadata = reference_plan.peer_eligibility_metadata()

        return DEAResult(
            summary_frame=summary_frame,
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
                            "purpose": "joint_operating_and_environmental_improvement",
                            "sample": "panel" if data.is_panel else "cross_section",
                        },
                        "graph": {"kind": "black_box_joint_production"},
                        "data_roles": {
                            "inputs": "resources_to_contract",
                            "outputs": "desirable_services_to_expand",
                            "bad_outputs": "undesirable_residuals_to_contract",
                            **data_role_schema(data),
                        },
                        "technology": {
                            "technology_id": bad_output_identity["technology_id"],
                            "family": "environmental_envelopment",
                            "returns_to_scale": self.returns_to_scale.value,
                            "bad_output_formulation_id": bad_output_identity[
                                "formulation_id"
                            ],
                            "bad_output_disposability_id": bad_output_identity[
                                "disposability_id"
                            ],
                            "bad_output_treatment": bad_output_identity["treatment"],
                            "compatibility_alias": bad_output_identity[
                                "compatibility_alias"
                            ],
                            "named_weak_disposal_equivalence": bad_output_identity[
                                "named_equivalence"
                            ],
                            "null_jointness": self.null_jointness,
                        },
                        "estimator": {
                            "estimator_id": "estimator.full.dea",
                            "kind": "full_frontier",
                            "family": "dea_envelopment",
                        },
                        "reference": registry_reference_spec(
                            self.reference,
                            reference_plan.kind,
                            peer_eligibility=peer_eligibility_metadata,
                        ),
                        "performance": {
                            "family": "environmental_directional_distance",
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
                            "bad_output_direction": direction_spec(
                                bad_direction_kind,
                                bad_directions,
                                data.bad_output_names,
                            ),
                            "negative_distance": self.allow_negative_distance,
                        },
                        "valuation": {"kind": "none"},
                        "evaluation_protocol": {
                            "kind": appraisal_kind,
                            "secondary_objective": (
                                "maximize_row_scaled_slacks"
                                if self.compute_slacks
                                else "none"
                            ),
                        },
                        "analysis": {"kind": "direct_model_fit"},
                        "uncertainty": {"kind": "deterministic"},
                    },
                    preset_id=self._registry_preset_id,
                ),
                "model_family": "environmental_directional_distance",
                "orientation": "input_and_bad_contraction_good_expansion",
                "returns_to_scale": self.returns_to_scale.value,
                "reference_kind": reference_plan.kind.value,
                **(
                    {}
                    if peer_eligibility_metadata is None
                    else {"peer_eligibility": peer_eligibility_metadata}
                ),
                "bad_output_disposability": bad_output_identity["summary_label"],
                "compatibility_alias": bad_output_identity["compatibility_alias"],
                "null_jointness": self.null_jointness,
                "bad_output_constraint": (
                    "equality"
                    if self.disposability is BadOutputDisposability.WEAK
                    else "less_than_or_equal"
                ),
                "environmental_technology": bad_output_identity["technology_id"],
                "bad_output_formulation": bad_output_identity["treatment"],
                "named_weak_disposal_equivalence": bad_output_identity[
                    "named_equivalence"
                ],
                "native_score": "beta",
                "score_direction": (
                    "signed_zero_frontier"
                    if self.allow_negative_distance
                    else "higher_is_farther"
                ),
                "efficiency_transform": (
                    "one_over_one_plus_beta_when_reference_membership_is_certified"
                ),
                "classification_domain": ("evaluated_plan_within_reference_technology"),
                "membership_policy": (
                    "self_inclusion_or_disposal_implication_or_negative_beta_"
                    "exclusion_or_beta_zero_feasibility_program"
                ),
                "input_direction": input_direction_kind,
                "output_direction": output_direction_kind,
                "bad_output_direction": bad_direction_kind,
                "direction_sign_convention": {
                    "input": "contract",
                    "output": "expand",
                    "bad_output": "contract",
                },
                "compute_slacks": self.compute_slacks,
                "slack_phase": "maximize_row_scaled_sum",
                "slack_target_unit_invariant": True,
                "allow_negative_distance": self.allow_negative_distance,
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "planned_reference_sets": reference_plan.unique_reference_sets,
                "compiled_reference_sets": len(compiled),
                "phase_one_solver_calls": phase_one_solver_calls,
                "phase_two_solver_calls": phase_two_solver_calls,
                "membership_solver_calls": membership_solver_calls,
                "solver_calls": (
                    phase_one_solver_calls
                    + phase_two_solver_calls
                    + membership_solver_calls
                ),
                "additional_solver_calls": 0,
                "certificate_extra_solver_calls": 0,
                "postsolve_certificate": {
                    "primary_lp": ("solver_neutral_primal_dual_kkt_and_strong_duality"),
                    "primary_economic": (
                        "raw_and_published_direction_objective_environmental_"
                        "balances_and_rts"
                    ),
                    "primary_row_scaling": (
                        "input_output_and_bad_output_quantity_accounts"
                    ),
                    "peer_release": ("independent_thresholded_environmental_account"),
                    "dual_release": ("complete_finite_original_unit_row_marginals"),
                    "slack_completion_lp": (
                        "solver_neutral_primal_dual_kkt_and_strong_duality"
                    ),
                    "slack_completion_economic": (
                        "row_scaled_slack_objective_and_target_balances"
                    ),
                    "reference_membership_lp": (
                        "solver_neutral_beta_zero_feasibility_certificate_when_needed"
                    ),
                    "reference_membership_economic": (
                        "original_quantity_environmental_account_reconstruction"
                    ),
                    "membership_solver_calls": membership_solver_calls,
                    "failure_policy": (
                        "withhold_uncertified_score_or_projection_accounts"
                    ),
                    "additional_solver_calls": 0,
                    "certificate_extra_solver_calls": 0,
                },
            },
        )


EnvironmentalDDF = EnvironmentalDirectionalDistanceDEA
"""Discoverability alias for :class:`EnvironmentalDirectionalDistanceDEA`."""


class CommonFactorWeakDisposalDDF(EnvironmentalDirectionalDistanceDEA):
    """Directional distance on the CRS common-factor weak-disposal technology.

    The empirical technology is

    ``X lambda <= x, Y lambda >= y, B lambda = b, lambda >= 0``.

    Under CRS, scaling the activity vector establishes common proportional
    weak disposal of desirable and undesirable outputs. Adding a VRS
    convexity equation would invalidate that construction, so this class
    deliberately fixes returns to scale at CRS.
    """

    _registry_method_id = "environmental.ddf.weak_disposal.common_factor"
    _weak_technology_id = (
        "environmental.weak_disposal.common_factor.crs.chung_fare_grosskopf_1997"
    )
    _warn_legacy_weak = False

    def __init__(
        self,
        *,
        input_direction: DirectionInput = "zeros",
        output_direction: DirectionInput = "observed",
        bad_output_direction: DirectionInput = "observed",
        null_jointness: bool = True,
        reference: ReferenceSpec | str | None = None,
        peer_eligibility: PeerEligibility | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        compute_slacks: bool = True,
        allow_negative_distance: bool = False,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        super().__init__(
            input_direction=input_direction,
            output_direction=output_direction,
            bad_output_direction=bad_output_direction,
            disposability=BadOutputDisposability.WEAK,
            null_jointness=null_jointness,
            returns_to_scale=ReturnsToScale.CRS,
            reference=reference,
            peer_eligibility=peer_eligibility,
            solver=solver,
            solver_options=solver_options,
            compute_slacks=compute_slacks,
            allow_negative_distance=allow_negative_distance,
            tolerance=tolerance,
            peer_tolerance=peer_tolerance,
        )


class ChungFareGrosskopfDDF(CommonFactorWeakDisposalDDF):
    """Chung--Färe--Grosskopf (1997) output environmental DDF preset.

    The preset fixes CRS and the observed direction
    ``g=(0, y_o, b_o)``: inputs are held fixed, desirable outputs expand, and
    undesirable outputs contract in their observed proportions. This follows
    the formal output-distance definition and equation (2.14) of the authors'
    1995 working paper. The journal version's equation (3.14) prints an input
    contraction term that is inconsistent with that definition.
    """

    _registry_method_id = "environmental.ddf.output.chung_fare_grosskopf_1997"
    _registry_preset_id = "environmental.ddf.output.chung_fare_grosskopf_1997"

    def __init__(
        self,
        *,
        reference: ReferenceSpec | str | None = None,
        peer_eligibility: PeerEligibility | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        compute_slacks: bool = True,
        allow_negative_distance: bool = True,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        super().__init__(
            input_direction="zeros",
            output_direction="observed",
            bad_output_direction="observed",
            null_jointness=True,
            reference=reference,
            peer_eligibility=peer_eligibility,
            solver=solver,
            solver_options=solver_options,
            compute_slacks=compute_slacks,
            allow_negative_distance=allow_negative_distance,
            tolerance=tolerance,
            peer_tolerance=peer_tolerance,
        )


# Compatibility re-exports keep paper-specific environmental presets
# discoverable from the long-standing ``deapack.models.environmental`` module.
from .zhou_ang_wang import (  # noqa: E402, F401
    NonCHPEnergyCarbonDEA,
    ZhouAngWangNonCHPEnergyCarbonDEA,
)
