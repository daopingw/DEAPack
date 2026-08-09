"""Charnes--Cooper--Huang--Sun finite polyhedral cone-ratio DEA.

This module implements only the input-oriented CRS sum-form programme in
Charnes, Cooper, Huang, and Sun (1990).  It is not a generic weight-
restriction interface and performs no ordinary slack or target completion.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix, hstack, vstack

from ...._registry import (
    data_role_schema,
    numeric_parameter_signature,
    registry_metadata,
)
from ....data import DEAData
from ....enums import SolverStatus
from ....exceptions import DataValidationError, ModelSpecificationError
from ....results import _freeze_result_metadata
from ....solvers import (
    LinearProgram,
    LPSolution,
    LPSolver,
    SciPyHiGHSSolver,
    certify_lp_solution,
)
from ....specs import SolverOptions

_METHOD_ID = "valuation.weight_restriction.cone_ratio.polyhedral_crs.charnes_etal_1990"
_SUMMARY_COLUMNS = (
    "dmu_id",
    "period",
    "theta",
    "score",
    "score_valid",
    "score_status",
    "solver_status",
    "backend_solver_status",
    "measure_efficient",
    "source_efficiency_valid",
    "source_efficient",
    "source_efficiency_status",
    "peer_valid",
    "composite_valid",
    "cone_residual_valid",
    "multiplier_valid",
    "model_family",
)
_INTENSITY_COLUMNS = ("dmu_id", "period", "peer_id", "lambda", "selection")
_COMPOSITE_COLUMNS = (
    "dmu_id",
    "period",
    "side",
    "variable",
    "observed",
    "radial_account",
    "peer_composite",
    "difference",
    "difference_semantics",
)
_CONE_RESIDUAL_COLUMNS = (
    "dmu_id",
    "period",
    "side",
    "generator",
    "transformed_observed",
    "transformed_bound",
    "transformed_peer_composite",
    "cone_residual",
    "residual_semantics",
)
_GENERATOR_COEFFICIENT_COLUMNS = (
    "dmu_id",
    "period",
    "side",
    "generator",
    "coefficient",
    "selection",
)
_MULTIPLIER_COLUMNS = (
    "dmu_id",
    "period",
    "side",
    "variable",
    "multiplier",
    "multiplier_unit",
    "interpretation",
    "selection",
)
_DIAGNOSTIC_COLUMNS = (
    "dmu_id",
    "period",
    "solver_status",
    "backend_solver_status",
    "message",
    "iterations",
    "raw_theta",
    "lp_postsolve_certified",
    "lp_certification_reason",
    "primal_account_valid",
    "dual_account_valid",
    "economic_account_valid",
    "certification_reason",
    "max_constraint_violation",
    "objective_residual",
    "duality_gap",
    "max_dual_violation",
    "max_transformed_input_violation",
    "max_transformed_output_violation",
    "normalization_violation",
    "max_multiplier_inequality_violation",
    "cross_form_objective_gap",
    "selected_generator_coefficients_strictly_positive",
)


def _nonempty_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


def _unit_tuple(values: Sequence[str], label: str) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise TypeError(f"{label} must be a tuple of non-empty unit strings")
    normalized = tuple(_nonempty_text(value, label) for value in values)
    if not normalized:
        raise ValueError(f"{label} must contain at least one declared unit")
    return normalized


@dataclass(frozen=True, slots=True)
class ConeRestrictionProvenance:
    """Declared origin and unit account for one pair of valuation cones.

    The quantity-unit order must match the input and output columns supplied
    to :class:`~deapack.DEAData`.  Generator coefficients inherit the
    corresponding reciprocal quantity units.
    """

    elicitation_source: str
    stakeholder: str
    comparison_population: str
    validity_period: str
    input_quantity_units: tuple[str, ...]
    output_quantity_units: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in (
            "elicitation_source",
            "stakeholder",
            "comparison_population",
            "validity_period",
        ):
            object.__setattr__(self, name, _nonempty_text(getattr(self, name), name))
        object.__setattr__(
            self,
            "input_quantity_units",
            _unit_tuple(self.input_quantity_units, "input_quantity_units"),
        )
        object.__setattr__(
            self,
            "output_quantity_units",
            _unit_tuple(self.output_quantity_units, "output_quantity_units"),
        )


@dataclass(frozen=True, slots=True)
class PolyhedralConeRatioResult:
    """Certified accounts for the narrow polyhedral cone-ratio programme.

    ``cone_residuals`` are inequalities in transformed valuation-cone space.
    They are deliberately separate from ordinary DEA slacks and targets.
    ``original_composites`` retains the radial and peer quantity accounts
    without claiming componentwise dominance in the original coordinates.
    """

    summary_frame: pd.DataFrame
    intensities: pd.DataFrame = field(default_factory=pd.DataFrame)
    original_composites: pd.DataFrame = field(default_factory=pd.DataFrame)
    cone_residuals: pd.DataFrame = field(default_factory=pd.DataFrame)
    generator_coefficients: pd.DataFrame = field(default_factory=pd.DataFrame)
    multipliers: pd.DataFrame = field(default_factory=pd.DataFrame)
    diagnostics: pd.DataFrame = field(default_factory=pd.DataFrame)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        required = {
            "dmu_id",
            "period",
            "theta",
            "score",
            "score_valid",
            "solver_status",
            "measure_efficient",
            "source_efficiency_valid",
            "source_efficient",
        }
        missing = required.difference(self.summary_frame.columns)
        if missing:
            raise ValueError(
                f"cone-ratio result summary is missing columns: {sorted(missing)}"
            )
        object.__setattr__(
            self,
            "metadata",
            _freeze_result_metadata(dict(self.metadata)),
        )

    def summary(self, *, copy: bool = True) -> pd.DataFrame:
        """Return one row per evaluated organization."""
        return self.summary_frame.copy() if copy else self.summary_frame

    def peers(self, dmu_id: object) -> pd.DataFrame:
        """Return the reported positive intensities in the selected optimum."""
        if self.intensities.empty:
            return self.intensities.copy()
        return self.intensities.loc[self.intensities["dmu_id"] == dmu_id].copy()

    def composites_for(self, dmu_id: object) -> pd.DataFrame:
        """Return original-coordinate radial and peer quantity accounts."""
        if self.original_composites.empty:
            return self.original_composites.copy()
        return self.original_composites.loc[
            self.original_composites["dmu_id"] == dmu_id
        ].copy()

    def cone_residuals_for(self, dmu_id: object) -> pd.DataFrame:
        """Return transformed cone inequalities without relabeling them slacks."""
        if self.cone_residuals.empty:
            return self.cone_residuals.copy()
        return self.cone_residuals.loc[self.cone_residuals["dmu_id"] == dmu_id].copy()

    def multipliers_for(self, dmu_id: object) -> pd.DataFrame:
        """Return reconstructed original-coordinate supporting valuations."""
        if self.multipliers.empty:
            return self.multipliers.copy()
        return self.multipliers.loc[self.multipliers["dmu_id"] == dmu_id].copy()


def _freeze_sparse(matrix: csc_matrix) -> csc_matrix:
    matrix.sum_duplicates()
    matrix.sort_indices()
    for values in (matrix.data, matrix.indices, matrix.indptr):
        values.setflags(write=False)
    return matrix


def _freeze_vector(values: np.ndarray) -> np.ndarray:
    result = np.asarray(values, dtype=np.float64).reshape(-1).copy()
    result.setflags(write=False)
    return result


@dataclass(frozen=True, slots=True)
class _CompiledConeRatioTemplate:
    transformed_inputs: np.ndarray
    transformed_outputs: np.ndarray
    input_scales: np.ndarray
    output_scales: np.ndarray
    a_ub_template: csc_matrix
    objective: np.ndarray
    bounds: tuple[tuple[float | None, float | None], ...]
    factor_positions: np.ndarray

    def bind(self, focal: int) -> LinearProgram:
        a_ub = self.a_ub_template.copy()
        a_ub.data[self.factor_positions] = -(
            self.transformed_inputs[focal] / self.input_scales
        )
        a_ub.eliminate_zeros()
        _freeze_sparse(a_ub)
        b_ub = _freeze_vector(
            np.concatenate(
                [
                    np.zeros(self.transformed_inputs.shape[1]),
                    -(self.transformed_outputs[focal] / self.output_scales),
                ]
            )
        )
        return LinearProgram(
            c=self.objective,
            a_ub=a_ub,
            b_ub=b_ub,
            bounds=self.bounds,
            name=f"polyhedral_cone_ratio:{focal}",
        )


def _compile_template(
    transformed_inputs: np.ndarray,
    transformed_outputs: np.ndarray,
) -> _CompiledConeRatioTemplate:
    n_dmus = transformed_inputs.shape[0]
    n_input_generators = transformed_inputs.shape[1]
    n_output_generators = transformed_outputs.shape[1]
    input_scales = np.max(transformed_inputs, axis=0)
    output_scales = np.max(transformed_outputs, axis=0)

    input_rows = csc_matrix((transformed_inputs / input_scales).T)
    output_rows = csc_matrix(-(transformed_outputs / output_scales).T)
    factor_column = csc_matrix(
        np.concatenate(
            [
                np.ones(n_input_generators, dtype=np.float64),
                np.zeros(n_output_generators, dtype=np.float64),
            ]
        ).reshape(-1, 1)
    )
    a_ub_template = hstack(
        [vstack([input_rows, output_rows], format="csc"), factor_column],
        format="csc",
    )
    a_ub_template.sum_duplicates()
    a_ub_template.sort_indices()
    factor_start = int(a_ub_template.indptr[-2])
    factor_stop = int(a_ub_template.indptr[-1])
    factor_rows = a_ub_template.indices[factor_start:factor_stop]
    expected_rows = np.arange(n_input_generators, dtype=np.int64)
    if not np.array_equal(factor_rows, expected_rows):
        raise RuntimeError("cone-ratio compiler produced an invalid factor column")
    factor_positions = np.arange(factor_start, factor_stop, dtype=np.int64)
    factor_positions.setflags(write=False)

    objective = np.zeros(n_dmus + 1, dtype=np.float64)
    objective[-1] = 1.0
    objective.setflags(write=False)
    for array in (
        transformed_inputs,
        transformed_outputs,
        input_scales,
        output_scales,
    ):
        array.setflags(write=False)
    _freeze_sparse(a_ub_template)
    return _CompiledConeRatioTemplate(
        transformed_inputs=transformed_inputs,
        transformed_outputs=transformed_outputs,
        input_scales=input_scales,
        output_scales=output_scales,
        a_ub_template=a_ub_template,
        objective=objective,
        bounds=((0.0, None),) * (n_dmus + 1),
        factor_positions=factor_positions,
    )


def _generator_matrix(
    values: object,
    *,
    expected_columns: int | None,
    label: str,
) -> np.ndarray:
    try:
        matrix = np.asarray(values, dtype=np.float64)
    except (TypeError, ValueError) as error:
        raise ModelSpecificationError(f"{label} must be a numeric matrix") from error
    if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[1] == 0:
        raise ModelSpecificationError(
            f"{label} must be a non-empty two-dimensional generator matrix"
        )
    if expected_columns is not None and matrix.shape[1] != expected_columns:
        raise ModelSpecificationError(
            f"{label} must have shape (n_generators, {expected_columns})"
        )
    if not np.isfinite(matrix).all():
        raise ModelSpecificationError(f"{label} must contain only finite values")
    if np.any(matrix < 0.0):
        raise ModelSpecificationError(f"{label} must be nonnegative sum-form rays")
    if np.any(np.sum(matrix, axis=1) <= 0.0):
        raise ModelSpecificationError(f"{label} cannot contain an all-zero generator")
    result = np.ascontiguousarray(matrix.copy())
    result.setflags(write=False)
    return result


def _semantic_status(solution: LPSolution, valid: bool) -> SolverStatus:
    if solution.status is not SolverStatus.OPTIMAL:
        return solution.status
    return SolverStatus.OPTIMAL if valid else SolverStatus.NUMERICAL_ERROR


class PolyhedralConeRatioDEA:
    """Input-oriented CRS DEA with finite sum-form valuation cones.

    ``input_generators`` is the source matrix :math:`A` with one generator per
    row; ``output_generators`` is :math:`B`.  The class accepts no orientation,
    returns-to-scale, reference-set, half-space, or target-completion switch.
    """

    _registry_method_id = _METHOD_ID

    def __init__(
        self,
        input_generators: object,
        output_generators: object,
        *,
        restriction_provenance: ConeRestrictionProvenance,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        if not isinstance(restriction_provenance, ConeRestrictionProvenance):
            raise TypeError("restriction_provenance must be ConeRestrictionProvenance")
        if solver is not None and solver_options is not None:
            raise ValueError("pass solver or solver_options, not both")
        if not math.isfinite(tolerance) or tolerance <= 0.0:
            raise ValueError("tolerance must be positive and finite")
        resolved_peer_tolerance = (
            tolerance if peer_tolerance is None else peer_tolerance
        )
        if not math.isfinite(resolved_peer_tolerance) or resolved_peer_tolerance <= 0:
            raise ValueError("peer_tolerance must be positive and finite")
        self._input_generators = _generator_matrix(
            input_generators,
            expected_columns=None,
            label="input_generators",
        )
        self._output_generators = _generator_matrix(
            output_generators,
            expected_columns=None,
            label="output_generators",
        )
        self.restriction_provenance = restriction_provenance
        self.solver = SciPyHiGHSSolver(solver_options) if solver is None else solver
        self.tolerance = float(tolerance)
        self.peer_tolerance = float(resolved_peer_tolerance)

    @property
    def input_generators(self) -> np.ndarray:
        """Return a detached copy of the declared input generator matrix."""
        return self._input_generators.copy()

    @property
    def output_generators(self) -> np.ndarray:
        """Return a detached copy of the declared output generator matrix."""
        return self._output_generators.copy()

    def _validate_data(self, data: DEAData) -> tuple[np.ndarray, np.ndarray]:
        if data.is_panel:
            raise ModelSpecificationError(
                "polyhedral cone-ratio DEA requires one self-contained cross section"
            )
        if data.bad_outputs is not None or data.polluting_input_names:
            raise ModelSpecificationError(
                "polyhedral cone-ratio DEA accepts ordinary inputs and desirable "
                "outputs only"
            )
        if data.groups is not None:
            raise ModelSpecificationError(
                "polyhedral cone-ratio DEA does not infer a grouped reference policy"
            )
        data.ensure_nonnegative()
        if len(self.restriction_provenance.input_quantity_units) != data.n_inputs:
            raise ModelSpecificationError(
                "input quantity-unit count must match the input column count"
            )
        if len(self.restriction_provenance.output_quantity_units) != data.n_outputs:
            raise ModelSpecificationError(
                "output quantity-unit count must match the output column count"
            )
        input_generators = _generator_matrix(
            self._input_generators,
            expected_columns=data.n_inputs,
            label="input_generators",
        )
        output_generators = _generator_matrix(
            self._output_generators,
            expected_columns=data.n_outputs,
            label="output_generators",
        )
        return input_generators, output_generators

    def fit(self, data: DEAData) -> PolyhedralConeRatioResult:
        """Fit one LP per organization and certify every released account."""
        input_generators, output_generators = self._validate_data(data)
        with np.errstate(over="ignore", invalid="ignore"):
            transformed_inputs = np.ascontiguousarray(
                data.inputs @ input_generators.T,
                dtype=np.float64,
            )
            transformed_outputs = np.ascontiguousarray(
                data.outputs @ output_generators.T,
                dtype=np.float64,
            )
        if not np.isfinite(transformed_inputs).all():
            raise DataValidationError("every transformed A x_j account must be finite")
        if not np.isfinite(transformed_outputs).all():
            raise DataValidationError("every transformed B y_j account must be finite")
        if np.any(transformed_inputs <= 0.0):
            raise DataValidationError("every A x_j account must be strictly positive")
        if np.any(transformed_outputs <= 0.0):
            raise DataValidationError("every B y_j account must be strictly positive")
        template = _compile_template(transformed_inputs, transformed_outputs)

        summary_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        composite_rows: list[dict[str, Any]] = []
        residual_rows: list[dict[str, Any]] = []
        coefficient_rows: list[dict[str, Any]] = []
        multiplier_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []

        for focal, dmu_id in enumerate(data.dmu_ids):
            problem = template.bind(focal)
            solution = self.solver.solve(problem)
            lp_certificate = certify_lp_solution(
                problem,
                solution,
                tolerance=self.tolerance,
            )
            account = self._certify_accounts(
                data,
                template,
                input_generators,
                output_generators,
                focal,
                solution,
            )
            score_valid = bool(account["primal_valid"])
            multiplier_valid = bool(account["all_valid"])
            semantic_status = _semantic_status(solution, score_valid)
            theta = float(account["theta"]) if score_valid else math.nan
            measure_efficient = (
                bool(abs(theta - 1.0) <= self.tolerance) if score_valid else pd.NA
            )
            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": None,
                    "theta": theta,
                    "score": theta,
                    "score_valid": score_valid,
                    "score_status": (
                        "certified_native_theta" if score_valid else "invalid"
                    ),
                    "solver_status": semantic_status.value,
                    "backend_solver_status": solution.status.value,
                    "measure_efficient": measure_efficient,
                    "source_efficiency_valid": False,
                    "source_efficient": pd.NA,
                    "source_efficiency_status": (
                        "not_certified_requires_interior_optimum"
                    ),
                    "peer_valid": score_valid,
                    "composite_valid": score_valid,
                    "cone_residual_valid": score_valid,
                    "multiplier_valid": multiplier_valid,
                    "model_family": "polyhedral_cone_ratio_crs_input",
                }
            )
            diagnostic_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": None,
                    "solver_status": semantic_status.value,
                    "backend_solver_status": solution.status.value,
                    "message": solution.message,
                    "iterations": solution.iterations,
                    "raw_theta": account["theta"],
                    "lp_postsolve_certified": lp_certificate.certified,
                    "lp_certification_reason": lp_certificate.reason,
                    "primal_account_valid": account["primal_valid"],
                    "dual_account_valid": account["dual_valid"],
                    "economic_account_valid": account["economic_valid"],
                    "certification_reason": account["reason"],
                    "max_constraint_violation": lp_certificate.max_constraint_violation,
                    "objective_residual": lp_certificate.objective_residual,
                    "duality_gap": lp_certificate.duality_gap,
                    "max_dual_violation": lp_certificate.max_dual_violation,
                    "max_transformed_input_violation": account["max_input_violation"],
                    "max_transformed_output_violation": account["max_output_violation"],
                    "normalization_violation": account["normalization_violation"],
                    "max_multiplier_inequality_violation": account[
                        "max_multiplier_violation"
                    ],
                    "cross_form_objective_gap": account["cross_form_gap"],
                    "selected_generator_coefficients_strictly_positive": account[
                        "selected_coefficients_strictly_positive"
                    ],
                }
            )
            if score_valid:
                self._append_accounts(
                    data,
                    input_generators,
                    output_generators,
                    focal,
                    dmu_id,
                    account,
                    intensity_rows,
                    composite_rows,
                    residual_rows,
                    coefficient_rows,
                    multiplier_rows,
                    publish_duals=multiplier_valid,
                )

        metadata = self._metadata(
            data,
            input_generators,
            output_generators,
            n_solver_calls=data.n_dmus,
        )
        return PolyhedralConeRatioResult(
            summary_frame=pd.DataFrame(summary_rows, columns=_SUMMARY_COLUMNS),
            intensities=pd.DataFrame(intensity_rows, columns=_INTENSITY_COLUMNS),
            original_composites=pd.DataFrame(
                composite_rows,
                columns=_COMPOSITE_COLUMNS,
            ),
            cone_residuals=pd.DataFrame(
                residual_rows,
                columns=_CONE_RESIDUAL_COLUMNS,
            ),
            generator_coefficients=pd.DataFrame(
                coefficient_rows,
                columns=_GENERATOR_COEFFICIENT_COLUMNS,
            ),
            multipliers=pd.DataFrame(
                multiplier_rows,
                columns=_MULTIPLIER_COLUMNS,
            ),
            diagnostics=pd.DataFrame(
                diagnostic_rows,
                columns=_DIAGNOSTIC_COLUMNS,
            ),
            metadata=metadata,
        )

    def _certify_accounts(
        self,
        data: DEAData,
        template: _CompiledConeRatioTemplate,
        input_generators: np.ndarray,
        output_generators: np.ndarray,
        focal: int,
        solution: LPSolution,
    ) -> dict[str, Any]:
        empty = {
            "theta": math.nan,
            "lambdas": None,
            "alpha": None,
            "gamma": None,
            "input_multiplier": None,
            "output_multiplier": None,
            "input_peer": None,
            "output_peer": None,
            "input_residual": None,
            "output_residual": None,
            "primal_valid": False,
            "dual_valid": False,
            "economic_valid": False,
            "all_valid": False,
            "reason": "missing_or_invalid_primal",
            "max_input_violation": math.inf,
            "max_output_violation": math.inf,
            "normalization_violation": math.inf,
            "max_multiplier_violation": math.inf,
            "cross_form_gap": math.inf,
            "selected_coefficients_strictly_positive": False,
        }
        if solution.status is not SolverStatus.OPTIMAL or solution.primal is None:
            empty["reason"] = f"solver_status_{solution.status.value}"
            return empty
        primal = np.asarray(solution.primal, dtype=np.float64)
        if primal.shape != (data.n_dmus + 1,) or not np.isfinite(primal).all():
            return empty
        lambdas = primal[:-1].copy()
        theta = float(primal[-1])
        if np.any(lambdas < -self.tolerance) or theta < -self.tolerance:
            empty["reason"] = "negative_primal_value"
            return empty
        lambdas[np.abs(lambdas) <= self.tolerance] = 0.0
        input_peer = lambdas @ template.transformed_inputs
        output_peer = lambdas @ template.transformed_outputs
        input_bound = theta * template.transformed_inputs[focal]
        output_bound = template.transformed_outputs[focal]
        input_residual = input_bound - input_peer
        output_residual = output_peer - output_bound
        max_input_violation = float(
            (np.maximum(-input_residual, 0.0) / template.input_scales).max(initial=0.0)
        )
        max_output_violation = float(
            (np.maximum(-output_residual, 0.0) / template.output_scales).max(
                initial=0.0
            )
        )
        objective_residual = (
            math.inf
            if solution.objective is None or not math.isfinite(solution.objective)
            else abs(theta - float(solution.objective))
        )
        primal_valid = bool(
            max_input_violation <= self.tolerance
            and max_output_violation <= self.tolerance
            and objective_residual <= self.tolerance * max(1.0, abs(theta))
            and theta <= 1.0 + self.tolerance
        )

        # Preserve a backend-optimal primal account even if row marginals are
        # unavailable or malformed. Such defects withdraw only multiplier and
        # primal--dual claims, not a directly reconstructed feasible score,
        # peer, composite, or cone-residual account.
        empty.update(
            theta=theta,
            lambdas=lambdas,
            input_peer=input_peer,
            output_peer=output_peer,
            input_residual=input_residual,
            output_residual=output_residual,
            primal_valid=primal_valid,
            reason="primal_certified_dual_not_checked",
            max_input_violation=max_input_violation,
            max_output_violation=max_output_violation,
        )

        marginals = solution.inequality_marginals
        expected_marginals = (
            template.transformed_inputs.shape[1] + template.transformed_outputs.shape[1]
        )
        if marginals is None:
            empty["reason"] = "missing_dual_marginals"
            return empty
        raw_marginals = np.asarray(marginals, dtype=np.float64)
        if (
            raw_marginals.shape != (expected_marginals,)
            or not np.isfinite(raw_marginals).all()
        ):
            empty["reason"] = "invalid_dual_marginals"
            return empty
        n_input_generators = template.transformed_inputs.shape[1]
        # HiGHS reports marginals for the scale-normalized constraint rows.
        # Their signs and economically relevant magnitudes are invariant when
        # a generator ray is multiplied by a positive constant.  Certify and
        # trim in that normalized coordinate system before mapping back to
        # the source's alpha/gamma coefficients; an absolute tolerance on the
        # latter would make an otherwise identical cone depend on ray units.
        normalized_alpha = -raw_marginals[:n_input_generators].copy()
        normalized_gamma = -raw_marginals[n_input_generators:].copy()
        if np.any(normalized_alpha < -self.tolerance) or np.any(
            normalized_gamma < -self.tolerance
        ):
            empty["reason"] = "negative_generator_coefficient"
            return empty
        normalized_alpha[np.abs(normalized_alpha) <= self.tolerance] = 0.0
        normalized_gamma[np.abs(normalized_gamma) <= self.tolerance] = 0.0
        alpha = normalized_alpha / template.input_scales
        gamma = normalized_gamma / template.output_scales
        normalized_inputs = template.transformed_inputs / template.input_scales
        normalized_outputs = template.transformed_outputs / template.output_scales
        normalization_violation = abs(
            float(normalized_alpha @ normalized_inputs[focal]) - 1.0
        )
        multiplier_rows = (
            normalized_outputs @ normalized_gamma - normalized_inputs @ normalized_alpha
        )
        max_multiplier_violation = float(
            np.maximum(multiplier_rows, 0.0).max(initial=0.0)
        )
        dual_objective = float(normalized_gamma @ normalized_outputs[focal])
        cross_form_gap = abs(theta - dual_objective)
        dual_valid = bool(
            normalization_violation <= self.tolerance
            and max_multiplier_violation <= self.tolerance
            and cross_form_gap <= self.tolerance * max(1.0, abs(theta))
        )
        input_multiplier = input_generators.T @ alpha
        output_multiplier = output_generators.T @ gamma
        economic_valid = bool(
            np.isfinite(input_multiplier).all()
            and np.isfinite(output_multiplier).all()
            and np.all(input_multiplier >= 0.0)
            and np.all(output_multiplier >= 0.0)
        )
        all_valid = bool(primal_valid and dual_valid and economic_valid)
        return {
            "theta": theta,
            "lambdas": lambdas,
            "alpha": alpha,
            "gamma": gamma,
            "input_multiplier": input_multiplier,
            "output_multiplier": output_multiplier,
            "input_peer": input_peer,
            "output_peer": output_peer,
            "input_residual": input_residual,
            "output_residual": output_residual,
            "primal_valid": primal_valid,
            "dual_valid": dual_valid,
            "economic_valid": economic_valid,
            "all_valid": all_valid,
            "reason": "certified" if all_valid else "cone_account_check_failed",
            "max_input_violation": max_input_violation,
            "max_output_violation": max_output_violation,
            "normalization_violation": normalization_violation,
            "max_multiplier_violation": max_multiplier_violation,
            "cross_form_gap": cross_form_gap,
            "selected_coefficients_strictly_positive": bool(
                np.all(normalized_alpha > self.tolerance)
                and np.all(normalized_gamma > self.tolerance)
            ),
        }

    def _append_accounts(
        self,
        data: DEAData,
        input_generators: np.ndarray,
        output_generators: np.ndarray,
        focal: int,
        dmu_id: object,
        account: Mapping[str, Any],
        intensity_rows: list[dict[str, Any]],
        composite_rows: list[dict[str, Any]],
        residual_rows: list[dict[str, Any]],
        coefficient_rows: list[dict[str, Any]],
        multiplier_rows: list[dict[str, Any]],
        *,
        publish_duals: bool,
    ) -> None:
        lambdas = np.asarray(account["lambdas"], dtype=np.float64)
        theta = float(account["theta"])
        for reference, value in enumerate(lambdas):
            if value > self.peer_tolerance:
                intensity_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": None,
                        "peer_id": data.dmu_ids[reference],
                        "lambda": float(value),
                        "selection": "solver_selected",
                    }
                )
        original_input_peer = lambdas @ data.inputs
        original_output_peer = lambdas @ data.outputs
        for variable, observed, peer in zip(
            data.input_names,
            data.inputs[focal],
            original_input_peer,
            strict=True,
        ):
            composite_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": None,
                    "side": "input",
                    "variable": variable,
                    "observed": float(observed),
                    "radial_account": theta * float(observed),
                    "peer_composite": float(peer),
                    "difference": theta * float(observed) - float(peer),
                    "difference_semantics": "original_coordinate_difference_not_slack",
                }
            )
        for variable, observed, peer in zip(
            data.output_names,
            data.outputs[focal],
            original_output_peer,
            strict=True,
        ):
            composite_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": None,
                    "side": "output",
                    "variable": variable,
                    "observed": float(observed),
                    "radial_account": float(observed),
                    "peer_composite": float(peer),
                    "difference": float(peer) - float(observed),
                    "difference_semantics": "original_coordinate_difference_not_slack",
                }
            )
        transformed_input_observed = data.inputs[focal] @ input_generators.T
        transformed_output_observed = data.outputs[focal] @ output_generators.T
        for position, value in enumerate(account["input_residual"]):
            residual_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": None,
                    "side": "input",
                    "generator": position,
                    "transformed_observed": float(transformed_input_observed[position]),
                    "transformed_bound": theta
                    * float(transformed_input_observed[position]),
                    "transformed_peer_composite": float(
                        account["input_peer"][position]
                    ),
                    "cone_residual": float(value),
                    "residual_semantics": (
                        "transformed_cone_inequality_not_componentwise_slack"
                    ),
                }
            )
        for position, value in enumerate(account["output_residual"]):
            residual_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": None,
                    "side": "output",
                    "generator": position,
                    "transformed_observed": float(
                        transformed_output_observed[position]
                    ),
                    "transformed_bound": float(transformed_output_observed[position]),
                    "transformed_peer_composite": float(
                        account["output_peer"][position]
                    ),
                    "cone_residual": float(value),
                    "residual_semantics": (
                        "transformed_cone_inequality_not_componentwise_slack"
                    ),
                }
            )
        if not publish_duals:
            return
        for side, coefficients in (
            ("input", account["alpha"]),
            ("output", account["gamma"]),
        ):
            for position, value in enumerate(coefficients):
                coefficient_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": None,
                        "side": side,
                        "generator": position,
                        "coefficient": float(value),
                        "selection": "solver_selected_dual",
                    }
                )
        for side, names, values, units in (
            (
                "input",
                data.input_names,
                account["input_multiplier"],
                self.restriction_provenance.input_quantity_units,
            ),
            (
                "output",
                data.output_names,
                account["output_multiplier"],
                self.restriction_provenance.output_quantity_units,
            ),
        ):
            for variable, value, unit in zip(names, values, units, strict=True):
                multiplier_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": None,
                        "side": side,
                        "variable": variable,
                        "multiplier": float(value),
                        "multiplier_unit": f"1/({unit})",
                        "interpretation": "supporting_valuation_not_market_price",
                        "selection": "solver_selected_dual",
                    }
                )

    def _metadata(
        self,
        data: DEAData,
        input_generators: np.ndarray,
        output_generators: np.ndarray,
        *,
        n_solver_calls: int,
    ) -> dict[str, Any]:
        provenance = self.restriction_provenance
        restriction = {
            "form": "finite_nonnegative_sum_generators",
            "input_generators": input_generators.tolist(),
            "output_generators": output_generators.tolist(),
            "input_generator_signature": numeric_parameter_signature(
                input_generators,
                labels=data.input_names,
            ),
            "output_generator_signature": numeric_parameter_signature(
                output_generators,
                labels=data.output_names,
            ),
            "elicitation_source": provenance.elicitation_source,
            "stakeholder": provenance.stakeholder,
            "comparison_population": provenance.comparison_population,
            "validity_period": provenance.validity_period,
            "input_quantity_units": list(provenance.input_quantity_units),
            "output_quantity_units": list(provenance.output_quantity_units),
            "unit_covariance_rule": "A_tilde=A_C_inverse;B_tilde=B_D_inverse",
            "input_variable_order": list(data.input_names),
            "output_variable_order": list(data.output_names),
            "input_generator_order": [
                f"input_generator_{position}"
                for position in range(input_generators.shape[0])
            ],
            "output_generator_order": [
                f"output_generator_{position}"
                for position in range(output_generators.shape[0])
            ],
        }
        fingerprint_payload = {
            key: restriction[key]
            for key in (
                "input_generator_signature",
                "output_generator_signature",
                "elicitation_source",
                "stakeholder",
                "comparison_population",
                "validity_period",
                "input_quantity_units",
                "output_quantity_units",
                "input_variable_order",
                "output_variable_order",
                "input_generator_order",
                "output_generator_order",
            )
        }
        restriction["provenance_fingerprint"] = hashlib.sha256(
            b"deapack.cone-restriction-provenance.v1\0"
            + json.dumps(
                fingerprint_payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        metadata = registry_metadata(
            self._registry_method_id,
            {
                "context": {
                    "purpose": (
                        "valuation_restricted_operating_performance_self_appraisal"
                    )
                },
                "graph": {"kind": "black_box"},
                "data_roles": data_role_schema(data),
                "technology": {
                    "returns_to_scale": "crs",
                    "dominance": "declared_polyhedral_cone_order",
                },
                "estimator": {"kind": "full_frontier"},
                "reference": {
                    "kind": "global_cross_section",
                    "self_membership": "required",
                },
                "performance": {
                    "orientation": "input",
                    "native_measure": "theta",
                },
                "valuation": {
                    "kind": "polyhedral_cone_ratio",
                    "input_generator_signature": restriction[
                        "input_generator_signature"
                    ],
                    "output_generator_signature": restriction[
                        "output_generator_signature"
                    ],
                },
                "evaluation_protocol": {
                    "kind": "self_appraisal",
                    "ordinary_slack_completion": "not_performed",
                },
                "analysis": {"kind": "direct_model_fit"},
                "uncertainty": {"sampling": "none", "data": "none"},
            },
        )
        metadata.update(
            {
                "restriction": restriction,
                "orientation": "input",
                "returns_to_scale": "crs",
                "reference_kind": "global_cross_section_self_inclusive",
                "target_completion": "none",
                "ordinary_slacks_defined": False,
                "original_coordinate_targets_defined": False,
                "peer_selection": "solver_selected_alternate_optima_possible",
                "source_efficiency": "not_certified_requires_interior_optimum",
                "compiled_reference_sets": 1,
                "primary_solver_calls": n_solver_calls,
                "secondary_solver_calls": 0,
                "solver_calls": n_solver_calls,
                "additional_solver_calls": 0,
                "certificate_extra_solver_calls": 0,
                "compiler": "dedicated_sparse_polyhedral_cone_ratio_crs",
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
            }
        )
        return metadata


__all__ = [
    "ConeRestrictionProvenance",
    "PolyhedralConeRatioDEA",
    "PolyhedralConeRatioResult",
]
