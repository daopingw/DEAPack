"""Tone's input-, output-, and non-oriented slacks-based measures (SBM)."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix, diags, eye, hstack, vstack

from .._registry import (
    data_role_schema,
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
)


def _transformed_rts_matrices(
    n_variables: int,
    n_lambda: int,
    returns_to_scale: ReturnsToScale,
) -> tuple[csc_matrix | None, np.ndarray | None, csc_matrix | None, np.ndarray | None]:
    row = np.zeros(n_variables, dtype=np.float64)
    row[:n_lambda] = 1.0
    row[-1] = -1.0

    if returns_to_scale is ReturnsToScale.VRS:
        return None, None, csc_matrix(row.reshape(1, -1)), np.asarray([0.0])
    if returns_to_scale is ReturnsToScale.NIRS:
        return csc_matrix(row.reshape(1, -1)), np.asarray([0.0]), None, None
    if returns_to_scale is ReturnsToScale.NDRS:
        return csc_matrix((-row).reshape(1, -1)), np.asarray([0.0]), None, None
    return None, None, None, None


def _diagnostic(
    *,
    dmu_id: object,
    period: object | None,
    solution: LPSolution,
    certificate: LPCertificate,
) -> dict[str, Any]:
    """Return raw solver evidence plus the independent LP certificate."""

    return {
        "dmu_id": dmu_id,
        "period": period,
        "phase": 1,
        "solver_status": solution.status.value,
        "message": solution.message,
        "iterations": solution.iterations,
        "max_primal_violation": solution.max_primal_violation,
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
        "max_published_peer_account_violation": np.nan,
        "dual_valid": False,
        "dual_status": "not_available_without_certified_primary",
        "published_dual_row_count": 0,
        "expected_dual_row_count": 0,
        "max_published_dual_account_violation": np.nan,
    }


def _scaled_equality_violation(
    actual: np.ndarray,
    required: np.ndarray,
) -> float:
    """Return a finite, unit-robust equality residual or infinity."""

    left = np.asarray(actual, dtype=np.float64).reshape(-1)
    right = np.asarray(required, dtype=np.float64).reshape(-1)
    if (
        left.shape != right.shape
        or not np.isfinite(left).all()
        or not np.isfinite(right).all()
    ):
        return math.inf
    scale = np.maximum(1.0, np.maximum(np.abs(left), np.abs(right)))
    return float((np.abs(left - right) / scale).max(initial=0.0))


def _scaled_nonnegative_violation(values: np.ndarray) -> float:
    """Return the largest scale-free violation of a nonnegative account."""

    array = np.asarray(values, dtype=np.float64).reshape(-1)
    if not np.isfinite(array).all():
        return math.inf
    return float(
        (np.maximum(-array, 0.0) / np.maximum(1.0, np.abs(array))).max(initial=0.0)
    )


def _sbm_economic_postsolve_violation(
    *,
    reference: CompiledReference,
    returns_to_scale: ReturnsToScale,
    orientation: str,
    x_o: np.ndarray,
    y_o: np.ndarray,
    b_o: np.ndarray | None,
    lambdas: np.ndarray,
    input_slacks: np.ndarray,
    output_slacks: np.ndarray,
    bad_output_slacks: np.ndarray,
    input_inefficiency: float,
    output_inefficiency: float,
    output_account_factor: float,
    transform_scale: float,
    efficiency: float,
    solver_objective: float,
) -> float:
    """Certify dehomogenized SBM balances and economic score accounts."""

    input_targets = np.asarray(x_o, dtype=np.float64) - input_slacks
    output_targets = np.asarray(y_o, dtype=np.float64) + output_slacks
    finite_blocks = [
        np.asarray(lambdas, dtype=np.float64),
        np.asarray(input_slacks, dtype=np.float64),
        np.asarray(output_slacks, dtype=np.float64),
        np.asarray(bad_output_slacks, dtype=np.float64),
        input_targets,
        output_targets,
        np.asarray(
            [
                input_inefficiency,
                output_inefficiency,
                output_account_factor,
                transform_scale,
                efficiency,
                solver_objective,
            ],
            dtype=np.float64,
        ),
    ]
    if not all(np.isfinite(values).all() for values in finite_blocks):
        return math.inf

    input_benchmark = np.asarray(reference.inputs @ lambdas).reshape(-1)
    output_benchmark = np.asarray(reference.outputs @ lambdas).reshape(-1)
    violations = [
        _scaled_nonnegative_violation(lambdas),
        _scaled_nonnegative_violation(input_slacks),
        _scaled_nonnegative_violation(output_slacks),
        _scaled_nonnegative_violation(bad_output_slacks),
        _scaled_nonnegative_violation(input_targets),
        _scaled_nonnegative_violation(output_targets),
        _scaled_equality_violation(input_benchmark, input_targets),
        _scaled_equality_violation(output_benchmark, output_targets),
        max(-efficiency, efficiency - 1.0, 0.0),
        max(input_inefficiency - 1.0, -input_inefficiency, 0.0),
        max(-output_inefficiency, 0.0),
        max(-output_account_factor, 0.0),
    ]

    if b_o is not None:
        if reference.bad_outputs is None:
            return math.inf
        bad_targets = np.asarray(b_o, dtype=np.float64) - bad_output_slacks
        bad_benchmark = np.asarray(reference.bad_outputs @ lambdas).reshape(-1)
        violations.extend(
            [
                _scaled_nonnegative_violation(bad_targets),
                _scaled_equality_violation(bad_benchmark, bad_targets),
            ]
        )

    intensity_sum = float(np.sum(lambdas))
    if returns_to_scale is ReturnsToScale.VRS:
        violations.append(abs(intensity_sum - 1.0) / max(1.0, abs(intensity_sum)))
    elif returns_to_scale is ReturnsToScale.NIRS:
        violations.append(max(intensity_sum - 1.0, 0.0) / max(1.0, abs(intensity_sum)))
    elif returns_to_scale is ReturnsToScale.NDRS:
        violations.append(max(1.0 - intensity_sum, 0.0) / max(1.0, abs(intensity_sum)))

    if orientation == "input":
        expected_objective = 1.0 - input_inefficiency
        score_identity = efficiency - expected_objective
        scale_identity = transform_scale - 1.0
    elif orientation == "output":
        expected_objective = -output_account_factor
        score_identity = efficiency * output_account_factor - 1.0
        scale_identity = transform_scale - 1.0
    else:
        expected_objective = efficiency
        score_identity = efficiency * output_account_factor - (1.0 - input_inefficiency)
        scale_identity = transform_scale * output_account_factor - 1.0
    objective_scale = max(1.0, abs(expected_objective), abs(solver_objective))
    violations.extend(
        [
            abs(solver_objective - expected_objective) / objective_scale,
            abs(score_identity),
            abs(scale_identity),
        ]
    )
    return max(violations, default=0.0)


def _sbm_public_peer_violation(
    *,
    reference: CompiledReference,
    returns_to_scale: ReturnsToScale,
    lambdas: np.ndarray,
    input_targets: np.ndarray,
    output_targets: np.ndarray,
    bad_output_targets: np.ndarray | None,
) -> float:
    """Certify the thresholded public peer account in physical units."""

    public_lambdas = np.asarray(lambdas, dtype=np.float64).reshape(-1)
    if public_lambdas.size != reference.size or not np.isfinite(public_lambdas).all():
        return math.inf
    violations = [
        _scaled_nonnegative_violation(public_lambdas),
        _scaled_equality_violation(
            np.asarray(reference.inputs @ public_lambdas).reshape(-1),
            input_targets,
        ),
        _scaled_equality_violation(
            np.asarray(reference.outputs @ public_lambdas).reshape(-1),
            output_targets,
        ),
    ]
    if bad_output_targets is not None:
        if reference.bad_outputs is None:
            return math.inf
        violations.append(
            _scaled_equality_violation(
                np.asarray(reference.bad_outputs @ public_lambdas).reshape(-1),
                bad_output_targets,
            )
        )

    intensity_sum = float(np.sum(public_lambdas))
    if returns_to_scale is ReturnsToScale.VRS:
        violations.append(abs(intensity_sum - 1.0) / max(1.0, abs(intensity_sum)))
    elif returns_to_scale is ReturnsToScale.NIRS:
        violations.append(max(intensity_sum - 1.0, 0.0) / max(1.0, abs(intensity_sum)))
    elif returns_to_scale is ReturnsToScale.NDRS:
        violations.append(max(1.0 - intensity_sum, 0.0) / max(1.0, abs(intensity_sum)))
    return max(violations, default=0.0)


def _sbm_public_dual_violation(
    rows: list[dict[str, Any]],
    canonical_rows: list[dict[str, Any]],
) -> float:
    """Certify a complete public dual table against original-unit mapping."""

    if len(rows) != len(canonical_rows):
        return math.inf
    published: list[float] = []
    canonical: list[float] = []
    for row, expected in zip(rows, canonical_rows, strict=True):
        if row.get("constraint_role") != expected.get("constraint_role") or row.get(
            "variable"
        ) != expected.get("variable"):
            return math.inf
        try:
            published.append(float(row["marginal"]))
            canonical.append(float(expected["marginal"]))
        except (KeyError, TypeError, ValueError):
            return math.inf
    return _scaled_equality_violation(
        np.asarray(published, dtype=np.float64),
        np.asarray(canonical, dtype=np.float64),
    )


class SlacksBasedDEA:
    """Estimate the non-oriented slacks-based measure (SBM).

    The fractional Tone (2001) objective is solved as one sparse linear
    program using the Charnes--Cooper transformation. Inputs and outputs must
    be strictly positive because the native score normalizes every slack by
    the evaluated DMU's observed value.
    """

    _include_bad_outputs = False
    _model_family = "slacks_based"
    _variant = "non_oriented_sbm"
    _registry_method_id = "static.sbm.nonoriented.tone2001"
    _orientation = "non-oriented"
    _native_score = "rho"

    def __init__(
        self,
        *,
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.VRS,
        reference: ReferenceSpec | str | None = None,
        peer_eligibility: PeerEligibility | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
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
        if not math.isfinite(tolerance) or tolerance <= 0:
            raise ValueError("tolerance must be finite and positive")
        self.tolerance = float(tolerance)
        self.peer_tolerance = (
            self.tolerance if peer_tolerance is None else float(peer_tolerance)
        )
        if not math.isfinite(self.peer_tolerance) or self.peer_tolerance <= 0:
            raise ValueError("peer_tolerance must be finite and positive")

    def _validate_data(self, data: DEAData) -> None:
        data.ensure_nonnegative(allow_zero=False)
        if data.bad_outputs is not None:
            raise ModelSpecificationError(
                "SlacksBasedDEA does not infer how undesirable outputs are "
                "disposed. Use the explicit undesirable-output SBM model."
            )

    def _summary_extras(self) -> dict[str, Any]:
        return {}

    def _metadata_extras(self) -> dict[str, Any]:
        return {}

    def _undefined_summary(
        self,
        *,
        dmu_id: object,
        period: object | None,
        reference_size: int,
        solver_status: SolverStatus,
        score_status: str,
        self_in_reference: bool,
    ) -> dict[str, Any]:
        """Return the common fail-closed row for one uncertified programme."""

        if self_in_reference:
            within_reference: bool | Any = True
            membership_status = "certified_by_self_inclusion"
        elif solver_status is SolverStatus.INFEASIBLE:
            within_reference = False
            membership_status = "outside_reference_technology"
        else:
            within_reference = pd.NA
            membership_status = "unavailable_uncertified_sbm_balance"

        return {
            "dmu_id": dmu_id,
            "period": period,
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
            "distance": np.nan,
            "is_efficient": pd.NA,
            "is_sbm_efficient": pd.NA,
            "is_within_reference_technology": within_reference,
            "self_in_reference": self_in_reference,
            "membership_status": membership_status,
            "solver_status": solver_status.value,
            "model_family": self._model_family,
            "orientation": self._orientation,
            "returns_to_scale": self.returns_to_scale.value,
            "reference_size": reference_size,
            "max_slack": np.nan,
            "max_normalized_slack": np.nan,
            "max_objective_slack": np.nan,
            "max_objective_normalized_slack": np.nan,
            "max_unoptimized_side_slack": np.nan,
            "max_unoptimized_side_normalized_slack": np.nan,
            "input_inefficiency": np.nan,
            "desirable_output_inefficiency": np.nan,
            "bad_output_inefficiency": np.nan,
            "output_inefficiency": np.nan,
            "output_account_factor": np.nan,
            "output_expansion_factor": np.nan,
            "transform_scale": np.nan,
            **self._summary_extras(),
        }

    def _problem(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        name: str,
        b_o: np.ndarray | None = None,
    ) -> LinearProgram:
        n_lambda = reference.size
        m = x_o.size
        s = y_o.size
        q = 0 if b_o is None else b_o.size
        n_variables = n_lambda + m + s + q + 1

        input_rows = hstack(
            [
                diags(1.0 / x_o, format="csc") @ reference.inputs,
                eye(m, format="csc"),
                csc_matrix((m, s + q)),
                csc_matrix(-np.ones((m, 1), dtype=np.float64)),
            ],
            format="csc",
        )
        output_rows = hstack(
            [
                diags(1.0 / y_o, format="csc") @ reference.outputs,
                csc_matrix((s, m)),
                -eye(s, format="csc"),
                csc_matrix((s, q)),
                csc_matrix(-np.ones((s, 1), dtype=np.float64)),
            ],
            format="csc",
        )
        balance_rows: list[csc_matrix] = [input_rows, output_rows]
        if b_o is not None:
            if reference.bad_outputs is None:
                raise RuntimeError("compiled SBM reference lacks bad outputs")
            bad_rows = hstack(
                [
                    diags(1.0 / b_o, format="csc") @ reference.bad_outputs,
                    csc_matrix((q, m + s)),
                    eye(q, format="csc"),
                    csc_matrix(-np.ones((q, 1), dtype=np.float64)),
                ],
                format="csc",
            )
            balance_rows.append(bad_rows)

        output_dimension = s + q
        normalization = np.zeros(n_variables, dtype=np.float64)
        normalization[-1] = 1.0
        if self._orientation == "non-oriented":
            normalization[n_lambda + m : n_lambda + m + s] = 1.0 / output_dimension
            if b_o is not None:
                normalization[n_lambda + m + s : -1] = 1.0 / output_dimension

        a_eq = vstack(
            [*balance_rows, csc_matrix(normalization.reshape(1, -1))],
            format="csc",
        )
        b_eq = np.concatenate([np.zeros(m + s + q), np.asarray([1.0])])

        rts_ub, rts_b_ub, rts_eq, rts_b_eq = _transformed_rts_matrices(
            n_variables, n_lambda, self.returns_to_scale
        )
        a_eq = join_optional_rows(a_eq, rts_eq)
        b_eq = join_optional_values(b_eq, rts_b_eq)

        objective = np.zeros(n_variables, dtype=np.float64)
        if self._orientation == "output":
            objective[n_lambda + m : n_lambda + m + s] = -1.0 / output_dimension
            if b_o is not None:
                objective[n_lambda + m + s : -1] = -1.0 / output_dimension
            objective[-1] = -1.0
        else:
            objective[n_lambda : n_lambda + m] = -1.0 / m
            objective[-1] = 1.0
        return LinearProgram(
            c=objective,
            a_ub=rts_ub,
            b_ub=rts_b_ub,
            a_eq=a_eq,
            b_eq=b_eq,
            bounds=((0.0, None),) * n_variables,
            name=f"{name}:{self._variant}",
        )

    def _dual_rows(
        self,
        data: DEAData,
        observation: int,
        solution: LPSolution,
    ) -> list[dict[str, Any]]:
        period = None if data.periods is None else data.periods[observation]
        common = {"dmu_id": data.dmu_ids[observation], "period": period, "phase": 1}
        rows: list[dict[str, Any]] = []
        coordinate_label = (
            "transformed" if self._orientation == "non-oriented" else "direct"
        )
        balance_count = (
            data.n_inputs
            + data.n_outputs
            + (data.n_bad_outputs if self._include_bad_outputs else 0)
        )
        expected_equalities = (
            balance_count + 1 + int(self.returns_to_scale is ReturnsToScale.VRS)
        )
        equality_marginals = (
            None
            if solution.equality_marginals is None
            else np.asarray(solution.equality_marginals, dtype=np.float64).reshape(-1)
        )
        if (
            equality_marginals is None
            or equality_marginals.size != expected_equalities
            or not np.isfinite(equality_marginals).all()
        ):
            return []
        if self.returns_to_scale in {ReturnsToScale.NIRS, ReturnsToScale.NDRS}:
            inequality_marginals = (
                None
                if solution.inequality_marginals is None
                else np.asarray(
                    solution.inequality_marginals,
                    dtype=np.float64,
                ).reshape(-1)
            )
            if (
                inequality_marginals is None
                or inequality_marginals.size != 1
                or not np.isfinite(inequality_marginals).all()
            ):
                return []
        else:
            inequality_marginals = None

        if equality_marginals is not None:
            offset = 0
            for variable, quantity in zip(
                data.input_names,
                data.inputs[observation],
                strict=True,
            ):
                rows.append(
                    {
                        **common,
                        "constraint_role": f"input_balance_{coordinate_label}",
                        "variable": variable,
                        "marginal": equality_marginals[offset] / quantity,
                    }
                )
                offset += 1
            for variable, quantity in zip(
                data.output_names,
                data.outputs[observation],
                strict=True,
            ):
                rows.append(
                    {
                        **common,
                        "constraint_role": f"output_balance_{coordinate_label}",
                        "variable": variable,
                        "marginal": equality_marginals[offset] / quantity,
                    }
                )
                offset += 1
            if self._include_bad_outputs:
                if data.bad_outputs is None:
                    return []
                for variable, quantity in zip(
                    data.bad_output_names,
                    data.bad_outputs[observation],
                    strict=True,
                ):
                    rows.append(
                        {
                            **common,
                            "constraint_role": (
                                f"bad_output_balance_{coordinate_label}"
                            ),
                            "variable": variable,
                            "marginal": equality_marginals[offset] / quantity,
                        }
                    )
                    offset += 1
            rows.append(
                {
                    **common,
                    "constraint_role": (
                        "identity_normalization"
                        if self._orientation != "non-oriented"
                        else "fractional_normalization"
                    ),
                    "variable": "tau",
                    "marginal": equality_marginals[offset],
                }
            )
            offset += 1
            if self.returns_to_scale is ReturnsToScale.VRS:
                rows.append(
                    {
                        **common,
                        "constraint_role": (f"returns_to_scale_{coordinate_label}"),
                        "variable": self.returns_to_scale.value,
                        "marginal": equality_marginals[offset],
                    }
                )

        if (
            self.returns_to_scale in {ReturnsToScale.NIRS, ReturnsToScale.NDRS}
            and inequality_marginals is not None
        ):
            rows.append(
                {
                    **common,
                    "constraint_role": f"returns_to_scale_{coordinate_label}",
                    "variable": self.returns_to_scale.value,
                    "marginal": inequality_marginals[0],
                }
            )
        return rows

    def _expected_dual_rows(self, data: DEAData) -> int:
        """Return the complete public primary-dual row count."""

        return (
            data.n_inputs
            + data.n_outputs
            + (data.n_bad_outputs if self._include_bad_outputs else 0)
            + 1
            + int(self.returns_to_scale is not ReturnsToScale.CRS)
        )

    def fit(self, data: DEAData) -> DEAResult:
        """Estimate this SBM orientation for all observations."""
        self._validate_data(data)
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
        primary_solver_calls = 0

        for observation in range(data.n_dmus):
            set_id = reference_plan.set_id_for(observation)
            reference_rows = reference_plan.rows_for(observation)
            reference = compiled.get(set_id)
            if reference is None:
                reference = compile_reference(data, reference_rows)
                compiled[set_id] = reference
            dmu_id = data.dmu_ids[observation]
            period = None if data.periods is None else data.periods[observation]
            self_in_reference = self_membership[observation]
            name = f"{dmu_id}@{period}" if period is not None else str(dmu_id)
            x_o = data.inputs[observation]
            y_o = data.outputs[observation]
            b_o = (
                data.bad_outputs[observation]
                if self._include_bad_outputs and data.bad_outputs is not None
                else None
            )
            primary_solver_calls += 1
            problem = self._problem(reference, x_o, y_o, name, b_o)
            solution = self.solver.solve(problem)
            certificate = certify_lp_solution(
                problem,
                solution,
                tolerance=self.tolerance,
            )
            diagnostic_rows.append(
                _diagnostic(
                    dmu_id=dmu_id,
                    period=period,
                    solution=solution,
                    certificate=certificate,
                )
            )
            diagnostic_rows[-1]["expected_dual_row_count"] = self._expected_dual_rows(
                data
            )

            if not certificate.certified or solution.primal is None:
                score_status = (
                    "outside_reference_technology"
                    if (
                        solution.status is SolverStatus.INFEASIBLE
                        and not self_in_reference
                    )
                    else "solver_failed"
                    if solution.status is not SolverStatus.OPTIMAL
                    else "unavailable_uncertified_source_program"
                )
                diagnostic_rows[-1]["score_status"] = score_status
                summary_rows.append(
                    self._undefined_summary(
                        dmu_id=dmu_id,
                        period=period,
                        reference_size=reference.size,
                        solver_status=solution.status,
                        score_status=score_status,
                        self_in_reference=self_in_reference,
                    )
                )
                continue

            transform_scale = float(solution.primal[-1])
            if not math.isfinite(transform_scale) or transform_scale <= self.tolerance:
                diagnostic_rows[-1].update(
                    {
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
                        period=period,
                        reference_size=reference.size,
                        solver_status=solution.status,
                        score_status="unavailable_uncertified_source_program",
                        self_in_reference=self_in_reference,
                    )
                )
                continue

            n_lambda = reference.size
            recovered_lambdas = np.asarray(
                solution.primal[:n_lambda] / transform_scale,
                dtype=np.float64,
            )
            lambdas = clean_small(recovered_lambdas, self.tolerance)
            input_normalized_slacks = clean_small(
                np.maximum(
                    solution.primal[n_lambda : n_lambda + data.n_inputs]
                    / transform_scale,
                    0.0,
                ),
                self.tolerance,
            )
            input_slacks = input_normalized_slacks * x_o
            output_start = n_lambda + data.n_inputs
            output_stop = output_start + data.n_outputs
            output_normalized_slacks = clean_small(
                np.maximum(
                    solution.primal[output_start:output_stop] / transform_scale,
                    0.0,
                ),
                self.tolerance,
            )
            output_slacks = output_normalized_slacks * y_o
            bad_output_normalized_slacks = (
                np.empty(0, dtype=np.float64)
                if b_o is None
                else clean_small(
                    np.maximum(
                        solution.primal[output_stop:-1] / transform_scale,
                        0.0,
                    ),
                    self.tolerance,
                )
            )
            bad_output_slacks = (
                np.empty(0, dtype=np.float64)
                if b_o is None
                else bad_output_normalized_slacks * b_o
            )
            input_targets = x_o - input_slacks
            output_targets = y_o + output_slacks
            bad_output_targets = None if b_o is None else b_o - bad_output_slacks
            input_inefficiency = float(np.mean(input_normalized_slacks))
            desirable_output_inefficiency = float(np.mean(output_normalized_slacks))
            bad_output_inefficiency = (
                np.nan if b_o is None else float(np.mean(bad_output_normalized_slacks))
            )
            output_dimension = data.n_outputs + bad_output_slacks.size
            output_inefficiency = float(
                (
                    np.sum(output_normalized_slacks)
                    + (0.0 if b_o is None else np.sum(bad_output_normalized_slacks))
                )
                / output_dimension
            )
            output_account_factor = 1.0 + output_inefficiency
            output_expansion_factor = (
                output_account_factor
                if self._orientation == "output" and b_o is None
                else np.nan
            )
            if self._orientation == "input":
                efficiency = 1.0 - input_inefficiency
            elif self._orientation == "output":
                efficiency = 1.0 / output_account_factor
            else:
                efficiency = (1.0 - input_inefficiency) / (1.0 + output_inefficiency)
            if (
                not math.isfinite(efficiency)
                or not -self.tolerance <= efficiency <= 1.0 + self.tolerance
            ):
                diagnostic_rows[-1].update(
                    {
                        "postsolve_certified": False,
                        "certification_reason": "invalid_efficiency_account",
                        "economic_postsolve_certified": False,
                        "economic_certification_reason": "invalid_efficiency_account",
                        "max_economic_violation": math.inf,
                        "score_status": "unavailable_uncertified_source_program",
                    }
                )
                summary_rows.append(
                    self._undefined_summary(
                        dmu_id=dmu_id,
                        period=period,
                        reference_size=reference.size,
                        solver_status=solution.status,
                        score_status="unavailable_uncertified_source_program",
                        self_in_reference=self_in_reference,
                    )
                )
                continue
            efficiency = float(np.clip(efficiency, 0.0, 1.0))
            distance = 1.0 - efficiency
            input_max_slack = float(input_slacks.max(initial=0.0))
            output_max_slack = float(
                max(
                    output_slacks.max(initial=0.0),
                    bad_output_slacks.max(initial=0.0),
                )
            )
            input_max_normalized_slack = float(
                np.max(input_normalized_slacks, initial=0.0)
            )
            output_max_normalized_slack = float(
                max(
                    np.max(output_normalized_slacks, initial=0.0),
                    (
                        0.0
                        if b_o is None
                        else np.max(
                            bad_output_normalized_slacks,
                            initial=0.0,
                        )
                    ),
                )
            )
            max_slack = max(input_max_slack, output_max_slack)
            max_normalized_slack = max(
                input_max_normalized_slack, output_max_normalized_slack
            )
            if self._orientation == "input":
                max_objective_slack = input_max_slack
                max_unoptimized_side_slack = output_max_slack
                max_objective_normalized_slack = input_max_normalized_slack
                max_unoptimized_side_normalized_slack = output_max_normalized_slack
            elif self._orientation == "output":
                max_objective_slack = output_max_slack
                max_unoptimized_side_slack = input_max_slack
                max_objective_normalized_slack = output_max_normalized_slack
                max_unoptimized_side_normalized_slack = input_max_normalized_slack
            else:
                max_objective_slack = max_slack
                max_unoptimized_side_slack = 0.0
                max_objective_normalized_slack = max_normalized_slack
                max_unoptimized_side_normalized_slack = 0.0
            max_economic_violation = _sbm_economic_postsolve_violation(
                reference=reference,
                returns_to_scale=self.returns_to_scale,
                orientation=self._orientation,
                x_o=x_o,
                y_o=y_o,
                b_o=b_o,
                lambdas=recovered_lambdas,
                input_slacks=input_slacks,
                output_slacks=output_slacks,
                bad_output_slacks=bad_output_slacks,
                input_inefficiency=input_inefficiency,
                output_inefficiency=output_inefficiency,
                output_account_factor=output_account_factor,
                transform_scale=transform_scale,
                efficiency=efficiency,
                solver_objective=float(solution.objective),
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
            if not economic_certified:
                diagnostic_rows[-1]["postsolve_certified"] = False
                diagnostic_rows[-1]["certification_reason"] = (
                    "source_account_reconstruction_failed"
                )
                diagnostic_rows[-1]["score_status"] = (
                    "unavailable_uncertified_source_program"
                )
                summary_rows.append(
                    self._undefined_summary(
                        dmu_id=dmu_id,
                        period=period,
                        reference_size=reference.size,
                        solver_status=solution.status,
                        score_status="unavailable_uncertified_source_program",
                        self_in_reference=self_in_reference,
                    )
                )
                continue

            score_valid = True
            target_valid = True
            target_status = "certified_primary_program"
            within_reference = True
            membership_status = (
                "certified_by_self_inclusion"
                if self_in_reference
                else "certified_by_sbm_balance_account"
            )
            classification_available = score_valid and within_reference
            is_sbm_efficient: bool | Any = (
                bool(max_objective_normalized_slack <= self.tolerance)
                if classification_available
                else pd.NA
            )
            is_efficient: bool | Any = (
                bool(max_normalized_slack <= self.tolerance)
                if self._orientation == "non-oriented" and classification_available
                else pd.NA
            )

            public_lambdas = np.where(lambdas > self.peer_tolerance, lambdas, 0.0)
            max_public_peer_violation = _sbm_public_peer_violation(
                reference=reference,
                returns_to_scale=self.returns_to_scale,
                lambdas=public_lambdas,
                input_targets=input_targets,
                output_targets=output_targets,
                bad_output_targets=bad_output_targets,
            )
            peer_valid = bool(
                math.isfinite(max_public_peer_violation)
                and max_public_peer_violation <= 10.0 * self.tolerance
            )
            peer_status = (
                "certified_thresholded_peer_account"
                if peer_valid
                else "unavailable_after_peer_reporting_threshold"
            )

            candidate_dual_rows = self._dual_rows(data, observation, solution)
            canonical_dual_rows = SlacksBasedDEA._dual_rows(
                self,
                data,
                observation,
                solution,
            )
            expected_dual_rows = self._expected_dual_rows(data)
            max_public_dual_violation = _sbm_public_dual_violation(
                candidate_dual_rows,
                canonical_dual_rows,
            )
            dual_valid = bool(
                len(candidate_dual_rows) == expected_dual_rows
                and len(canonical_dual_rows) == expected_dual_rows
                and math.isfinite(max_public_dual_violation)
                and max_public_dual_violation <= 10.0 * self.tolerance
            )
            dual_status = (
                "certified_complete_original_unit_dual_account"
                if dual_valid
                else "unavailable_incomplete_or_nonfinite_dual_account"
            )
            diagnostic_rows[-1].update(
                {
                    "score_valid": score_valid,
                    "score_status": "defined",
                    "target_valid": target_valid,
                    "target_status": target_status,
                    "peer_valid": peer_valid,
                    "peer_status": peer_status,
                    "max_published_peer_account_violation": (max_public_peer_violation),
                    "dual_valid": dual_valid,
                    "dual_status": dual_status,
                    "published_dual_row_count": len(candidate_dual_rows),
                    "expected_dual_row_count": expected_dual_rows,
                    "max_published_dual_account_violation": (max_public_dual_violation),
                }
            )
            if dual_valid:
                dual_rows.extend(candidate_dual_rows)

            if peer_valid:
                for local_position, intensity in enumerate(public_lambdas):
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
                                "certified_thresholded_primary_optimum"
                            ),
                        }
                    )

            variable_blocks: list[
                tuple[
                    str,
                    tuple[str, ...],
                    np.ndarray,
                    np.ndarray,
                    np.ndarray,
                    int,
                ]
            ] = [
                (
                    "input",
                    data.input_names,
                    x_o,
                    input_targets,
                    input_slacks,
                    data.n_inputs,
                ),
                (
                    "output",
                    data.output_names,
                    y_o,
                    output_targets,
                    output_slacks,
                    output_dimension,
                ),
            ]
            if b_o is not None and bad_output_targets is not None:
                variable_blocks.append(
                    (
                        "bad_output",
                        data.bad_output_names,
                        b_o,
                        bad_output_targets,
                        bad_output_slacks,
                        output_dimension,
                    )
                )

            for role, names, observed, targets, slacks, dimension in variable_blocks:
                for variable, value, target, slack in zip(
                    names, observed, targets, slacks, strict=True
                ):
                    target_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "role": role,
                            "variable": variable,
                            "observed": float(value),
                            "target": float(target),
                            "selection_status": "solver_selected_primary_optimum",
                        }
                    )
                    slack_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "role": role,
                            "variable": variable,
                            "slack": float(slack),
                            "normalizer": float(value),
                            "normalized_slack": float(slack / value),
                            "average_weight": float(1.0 / dimension),
                            "included_in_objective": (
                                self._orientation == "non-oriented"
                                or (self._orientation == "input" and role == "input")
                                or (self._orientation == "output" and role != "input")
                            ),
                        }
                    )

            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "score": efficiency,
                    "efficiency": efficiency,
                    "score_valid": score_valid,
                    "score_status": "defined",
                    "target_valid": target_valid,
                    "target_status": target_status,
                    "peer_valid": peer_valid,
                    "peer_status": peer_status,
                    "dual_valid": dual_valid,
                    "dual_status": dual_status,
                    "distance": distance,
                    "is_efficient": is_efficient,
                    "is_sbm_efficient": is_sbm_efficient,
                    "is_within_reference_technology": within_reference,
                    "self_in_reference": self_in_reference,
                    "membership_status": membership_status,
                    "solver_status": SolverStatus.OPTIMAL.value,
                    "model_family": self._model_family,
                    "orientation": self._orientation,
                    "returns_to_scale": self.returns_to_scale.value,
                    "reference_size": reference.size,
                    "max_slack": max_slack,
                    "max_normalized_slack": max_normalized_slack,
                    "max_objective_slack": max_objective_slack,
                    "max_objective_normalized_slack": (max_objective_normalized_slack),
                    "max_unoptimized_side_slack": max_unoptimized_side_slack,
                    "max_unoptimized_side_normalized_slack": (
                        max_unoptimized_side_normalized_slack
                    ),
                    "input_inefficiency": input_inefficiency,
                    "desirable_output_inefficiency": (desirable_output_inefficiency),
                    "bad_output_inefficiency": bad_output_inefficiency,
                    "output_inefficiency": output_inefficiency,
                    "output_account_factor": output_account_factor,
                    "output_expansion_factor": output_expansion_factor,
                    "transform_scale": transform_scale,
                    **self._summary_extras(),
                }
            )

        if self._include_bad_outputs:
            context = {
                "purpose": "nonradial_operating_and_environmental_benchmarking",
                "managerial_plan": (
                    "resource_saving_service_expansion_and_reference_supported_"
                    "separable_residual_contraction"
                ),
                "sample": "panel" if data.is_panel else "cross_section",
            }
            graph = {"kind": "black_box_joint_production"}
            roles = {
                "inputs": "controllable_resources",
                "outputs": "desirable_services",
                "bad_outputs": "strongly_disposable_undesirable_residuals",
            }
            performance = {
                "family": "slacks_based_measure",
                "orientation": "non_oriented_environmental",
                "normalization": "evaluated_dmu_values",
                "output_aggregation": "equal_weight_over_good_and_bad_dimensions",
            }
            valuation = {"kind": "equal_dimension_weights"}
            evaluation_protocol = {
                "kind": appraisal_kind,
                "fractional_transformation": "charnes_cooper",
                "alternate_target_policy": "solver_selected",
                "efficiency_certification_boundary": (
                    "certified_reference_technology_membership"
                ),
            }
        elif self._orientation == "input":
            context = {
                "purpose": "resource_conservation_benchmarking",
                "managerial_plan": ("reduce_input_excess_while_maintaining_outputs"),
                "sample": "panel" if data.is_panel else "cross_section",
            }
            graph = {"kind": "black_box"}
            roles = {
                "inputs": "controllable_resources",
                "outputs": "maintained_desirable_services",
                "bad_outputs": "excluded",
            }
            performance = {
                "family": "slacks_based_measure",
                "orientation": "input",
                "normalization": "evaluated_dmu_input_values",
            }
            valuation = {"kind": "equal_input_dimension_weights"}
            evaluation_protocol = {
                "kind": appraisal_kind,
                "objective_form": "direct_input_conservation_linear_program",
                "unoptimized_side": "feasible_output_slacks",
                "alternate_target_policy": "solver_selected",
                "efficiency_certification_boundary": (
                    "certified_reference_technology_membership"
                ),
            }
        elif self._orientation == "output":
            context = {
                "purpose": "service_expansion_benchmarking",
                "managerial_plan": "expand_outputs_without_increasing_inputs",
                "sample": "panel" if data.is_panel else "cross_section",
            }
            graph = {"kind": "black_box"}
            roles = {
                "inputs": "maintained_controllable_resources",
                "outputs": "expandable_desirable_services",
                "bad_outputs": "excluded",
            }
            performance = {
                "family": "slacks_based_measure",
                "orientation": "output",
                "normalization": "evaluated_dmu_output_values",
            }
            valuation = {"kind": "equal_output_dimension_weights"}
            evaluation_protocol = {
                "kind": appraisal_kind,
                "objective_form": "direct_output_expansion_linear_program",
                "unoptimized_side": "feasible_input_slacks",
                "alternate_target_policy": "solver_selected",
                "efficiency_certification_boundary": (
                    "certified_reference_technology_membership"
                ),
            }
        else:
            context = {
                "purpose": "variable_specific_operating_performance_benchmarking",
                "managerial_plan": "joint_resource_and_service_improvement",
                "sample": "panel" if data.is_panel else "cross_section",
            }
            graph = {"kind": "black_box"}
            roles = {
                "inputs": "controllable_resources",
                "outputs": "desirable_services",
                "bad_outputs": "excluded",
            }
            performance = {
                "family": "slacks_based_measure",
                "orientation": "non_oriented",
                "normalization": "evaluated_dmu_values",
            }
            valuation = {"kind": "equal_dimension_weights"}
            evaluation_protocol = {
                "kind": appraisal_kind,
                "fractional_transformation": "charnes_cooper",
                "alternate_target_policy": "solver_selected",
                "efficiency_certification_boundary": (
                    "certified_reference_technology_membership"
                ),
            }

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
                        "context": context,
                        "graph": graph,
                        "data_roles": {
                            **roles,
                            **data_role_schema(data),
                        },
                        "technology": {
                            "family": "convex_envelopment",
                            "returns_to_scale": self.returns_to_scale.value,
                            "returns_to_scale_provenance": (
                                "tone_2001_explicit"
                                if self.returns_to_scale
                                in {ReturnsToScale.CRS, ReturnsToScale.VRS}
                                else "deapack_convex_envelopment_variant"
                            ),
                            "bad_output_disposal": (
                                "strong_separable"
                                if self._include_bad_outputs
                                else "not_applicable"
                            ),
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
                        "performance": performance,
                        "valuation": valuation,
                        "evaluation_protocol": evaluation_protocol,
                        "analysis": {"kind": "direct_model_fit"},
                        "uncertainty": {"kind": "deterministic"},
                    },
                ),
                "model_family": self._model_family,
                "variant": self._variant,
                "orientation": self._orientation,
                "returns_to_scale": self.returns_to_scale.value,
                "returns_to_scale_provenance": (
                    "tone_2001_explicit"
                    if self.returns_to_scale in {ReturnsToScale.CRS, ReturnsToScale.VRS}
                    else "deapack_convex_envelopment_variant"
                ),
                "reference_kind": reference_plan.kind.value,
                **(
                    {}
                    if peer_eligibility_metadata is None
                    else {"peer_eligibility": peer_eligibility_metadata}
                ),
                "native_score": self._native_score,
                "direct_objective_account": (
                    "tau_O" if self._orientation == "output" else self._native_score
                ),
                "reported_efficiency": self._native_score,
                "score_direction": "higher_is_better",
                "distance_transform": "one_minus_efficiency",
                "classification_domain": ("evaluated_plan_within_reference_technology"),
                "membership_policy": (
                    "self_inclusion_or_certified_sbm_balance_account"
                ),
                "normalization": (
                    "evaluated_input_values"
                    if self._orientation == "input"
                    else "evaluated_output_values"
                    if self._orientation == "output"
                    else "evaluated_dmu_values"
                ),
                "data_requirement": "strictly_positive",
                "linearization": (
                    "charnes_cooper"
                    if self._orientation == "non-oriented"
                    else "identity_scale"
                ),
                "numerical_formulation": (
                    "row_scaled_quantity_balances_with_normalized_transformed_"
                    "slack_coordinates"
                ),
                "target_selection": "solver_selected_primary_optimum",
                "peer_release": (
                    "thresholded_lambdas_after_original_quantity_account_"
                    "recertification"
                ),
                "dual_release": "complete_finite_original_unit_row_marginals",
                "generic_efficiency_certification": (
                    "all_normalized_slacks"
                    if self._orientation == "non-oriented"
                    else "not_certified_by_single_orientation"
                ),
                "strong_efficiency_certification": (
                    "native_non_oriented_score"
                    if self._orientation == "non-oriented"
                    else "not_performed"
                ),
                "postsolve_certificate": {
                    "kind": "solver_neutral_lp_and_sbm_account",
                    "lp_checks": (
                        "primal_rows",
                        "variable_bounds",
                        "objective_reconstruction",
                        "dual_feasibility",
                        "complementarity",
                        "strong_duality",
                    ),
                    "economic_checks": (
                        "dehomogenized_targets",
                        "benchmark_balances",
                        "returns_to_scale_account",
                        "fractional_normalization",
                        "score_reconstruction",
                    ),
                    "release_policy": (
                        "claim_specific_fail_closed_score_target_peer_and_dual"
                    ),
                    "target_release": (
                        "certified_lp_and_dehomogenized_sbm_quantity_account"
                    ),
                    "peer_release": ("certified_thresholded_original_quantity_account"),
                    "dual_release": "complete_finite_original_unit_row_marginals",
                    "semantic_tables": {
                        "slacks": "target_valid",
                        "targets": "target_valid",
                        "intensities": "peer_valid",
                        "duals": "dual_valid",
                    },
                    "failure_scope": "per_observation",
                    "additional_solver_calls": 0,
                },
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "primary_solver_calls": primary_solver_calls,
                "solver_calls": primary_solver_calls,
                "compiled_reference_sets": len(compiled),
                **self._metadata_extras(),
            },
        )


SBM = SlacksBasedDEA
"""Historical discoverability alias for :class:`SlacksBasedDEA`."""

ERG = SlacksBasedDEA
"""Enhanced Russell graph alias on the standard positive-data domain."""


class InputOrientedSlacksBasedDEA(SlacksBasedDEA):
    """Estimate Tone's input-oriented SBM.

    The reported score is the average share of observed inputs retained after
    removing input excess while maintaining observed outputs. The removable
    average share is reported separately as ``input_inefficiency``. Output
    slacks remain feasible accounting variables, but are not part of this
    orientation's objective.
    """

    _variant = "input_oriented_sbm"
    _registry_method_id = "static.sbm.input.tone2001"
    _orientation = "input"
    _native_score = "rho_I"


InputSBM = InputOrientedSlacksBasedDEA
"""Short alias for :class:`InputOrientedSlacksBasedDEA`."""

InputRussell = InputOrientedSlacksBasedDEA
"""Input Russell alias on the matched strictly positive Tone domain."""


class OutputOrientedSlacksBasedDEA(SlacksBasedDEA):
    """Estimate Tone's output-oriented SBM.

    The reported higher-is-better score is the reciprocal of the average
    proportional output-expansion factor. Input slacks remain feasible
    accounting variables, but are not part of this orientation's objective.
    """

    _variant = "output_oriented_sbm"
    _registry_method_id = "static.sbm.output.tone2001"
    _orientation = "output"
    _native_score = "rho_O"


OutputSBM = OutputOrientedSlacksBasedDEA
"""Short alias for :class:`OutputOrientedSlacksBasedDEA`."""

OutputRussell = OutputOrientedSlacksBasedDEA
"""Output Russell alias using the reciprocal higher-is-better score."""


class UndesirableSlacksBasedDEA(SlacksBasedDEA):
    """Estimate Tone's separable SBM with undesirable outputs.

    The model contracts inputs and undesirable outputs while expanding
    desirable outputs. Its bad-output balance is
    ``b_o = B lambda + s^b``, which makes bad outputs strongly disposable.
    Weak disposal requires a different production technology rather than a
    sign change inside this formulation. Tone's nonseparable hybrid instead
    changes the variable partition and measure/estimator contract.
    """

    _include_bad_outputs = True
    _model_family = "undesirable_slacks_based"
    _variant = "separable_undesirable_sbm"
    _registry_method_id = "environmental.sbm.separable_strong"
    _native_score = "rho_B"

    def __init__(
        self,
        *,
        disposability: BadOutputDisposability | str = (BadOutputDisposability.STRONG),
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.VRS,
        reference: ReferenceSpec | str | None = None,
        peer_eligibility: PeerEligibility | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        parsed_disposability = parse_enum(
            disposability, BadOutputDisposability, "bad-output disposability"
        )
        if parsed_disposability is not BadOutputDisposability.STRONG:
            raise ModelSpecificationError(
                "UndesirableSlacksBasedDEA implements the separable strong-"
                "disposability SBM. Weak disposal requires an explicit weak-"
                "disposability technology."
            )
        self.disposability = parsed_disposability
        super().__init__(
            returns_to_scale=returns_to_scale,
            reference=reference,
            peer_eligibility=peer_eligibility,
            solver=solver,
            solver_options=solver_options,
            tolerance=tolerance,
            peer_tolerance=peer_tolerance,
        )

    def _validate_data(self, data: DEAData) -> None:
        data.ensure_nonnegative(allow_zero=False)
        if data.bad_outputs is None:
            raise ModelSpecificationError(
                "UndesirableSlacksBasedDEA requires declared bad_outputs in DEAData"
            )

    def _summary_extras(self) -> dict[str, Any]:
        return {
            "bad_output_disposability": self.disposability.value,
            "null_jointness": False,
        }

    def _metadata_extras(self) -> dict[str, Any]:
        return {
            "bad_output_disposability": self.disposability.value,
            "null_jointness": False,
            "bad_output_constraint": "B lambda + s_b = b_o",
            "bad_output_slack": "contraction_excess",
            "output_aggregation": "equal_weight_over_good_and_bad_dimensions",
            "separability": "separable_good_and_bad_outputs",
        }

    def fit(self, data: DEAData) -> DEAResult:
        """Estimate undesirable-output SBM efficiency for all observations."""
        return super().fit(data)


UndesirableSBM = UndesirableSlacksBasedDEA
"""Discoverability alias for :class:`UndesirableSlacksBasedDEA`."""
