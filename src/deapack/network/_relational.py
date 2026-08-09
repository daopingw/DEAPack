"""Sparse compiler for relational multiplier networks."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.sparse import csc_matrix, diags, hstack, vstack

from ..enums import Orientation, ReturnsToScale
from ..exceptions import ModelSpecificationError
from ..solvers import LinearProgram


@dataclass(frozen=True, slots=True)
class CompiledTwoStageQuantities:
    """Scaled quantities shared by two-stage series envelopment models."""

    rows: np.ndarray
    inputs: np.ndarray
    intermediates: np.ndarray
    outputs: np.ndarray
    input_scales: np.ndarray
    intermediate_scales: np.ndarray
    output_scales: np.ndarray
    scaled_inputs: np.ndarray
    scaled_intermediates: np.ndarray
    scaled_outputs: np.ndarray
    envelopment_constraint_template: csc_matrix
    separate_convexity_constraints: csc_matrix

    @property
    def size(self) -> int:
        return int(self.rows.size)


@dataclass(frozen=True, slots=True)
class CompiledTwoStageReference(CompiledTwoStageQuantities):
    """One scaled two-stage CRS relational reference technology."""

    multiplier_constraints: csc_matrix
    stage_1_row_scales: np.ndarray
    stage_2_row_scales: np.ndarray

    @property
    def n_multiplier_variables(self) -> int:
        return int(
            self.inputs.shape[1] + self.intermediates.shape[1] + self.outputs.shape[1]
        )


@dataclass(frozen=True, slots=True)
class RelationalMultiplierAccount:
    """Economic account rebuilt from one relational multiplier solution.

    The virtual values below are computed from the original quantities and
    unscaled multipliers.  They therefore provide a second implementation of
    the economic identities, separate from the scaled LP compiler.
    """

    input_multipliers: np.ndarray | None
    intermediate_multipliers: np.ndarray | None
    output_multipliers: np.ndarray | None
    input_virtual_value: float
    intermediate_virtual_value: float
    output_virtual_value: float
    system_efficiency: float
    stage_1_efficiency: float
    stage_2_efficiency: float
    reconstruction_residual: float
    max_violation: float


@dataclass(frozen=True, slots=True)
class RelationalProjectionAccount:
    """Original-quantity target and link account for one dual projection."""

    input_targets: np.ndarray | None
    upstream_supply: np.ndarray | None
    downstream_requirement: np.ndarray | None
    output_targets: np.ndarray | None
    max_violation: float


def _positive_column_scales(values: np.ndarray, role: str) -> np.ndarray:
    scales = np.max(values, axis=0)
    unsupported = np.flatnonzero(scales <= 0)
    if unsupported.size:
        raise ModelSpecificationError(
            f"the network reference set has no positive support for {role} "
            f"columns at positions {unsupported.tolist()}; remove the variable "
            "or choose a reference population with observed support"
        )
    scales = np.asarray(scales, dtype=np.float64)
    scales.setflags(write=False)
    return scales


def compile_two_stage_quantities(
    inputs: np.ndarray,
    intermediates: np.ndarray,
    outputs: np.ndarray,
    rows: np.ndarray,
) -> CompiledTwoStageQuantities:
    """Compile and scale one reusable two-stage quantity reference set."""

    x = np.ascontiguousarray(inputs[rows], dtype=np.float64)
    z = np.ascontiguousarray(intermediates[rows], dtype=np.float64)
    y = np.ascontiguousarray(outputs[rows], dtype=np.float64)
    x_scale = _positive_column_scales(x, "external-input")
    z_scale = _positive_column_scales(z, "intermediate")
    y_scale = _positive_column_scales(y, "final-output")
    x_bar = np.ascontiguousarray(x / x_scale)
    z_bar = np.ascontiguousarray(z / z_scale)
    y_bar = np.ascontiguousarray(y / y_scale)
    n = rows.size
    m = x.shape[1]
    q = z.shape[1]
    s = y.shape[1]

    # Only the radial-factor column and right-hand side change from one network
    # task to the next.  Reserve factor positions in both external-input and
    # final-output rows so either orientation can bind the same compiled sparse
    # reference blocks without rebuilding them for every evaluated DMU.
    input_rows = hstack(
        [
            csc_matrix(x_bar.T),
            csc_matrix((m, n)),
            csc_matrix(np.ones((m, 1), dtype=np.float64)),
        ],
        format="csc",
    )
    link_rows = hstack(
        [
            -csc_matrix(z_bar.T),
            csc_matrix(z_bar.T),
            csc_matrix((q, 1)),
        ],
        format="csc",
    )
    output_rows = hstack(
        [
            csc_matrix((s, n)),
            -csc_matrix(y_bar.T),
            csc_matrix(np.ones((s, 1), dtype=np.float64)),
        ],
        format="csc",
    )
    envelopment_template = vstack(
        [input_rows, link_rows, output_rows],
        format="csc",
    )
    convexity = np.zeros((2, 2 * n + 1), dtype=np.float64)
    convexity[0, :n] = 1.0
    convexity[1, n : 2 * n] = 1.0
    separate_convexity = csc_matrix(convexity)
    for array in (x, z, y, x_bar, z_bar, y_bar):
        array.setflags(write=False)
    return CompiledTwoStageQuantities(
        rows=rows,
        inputs=x,
        intermediates=z,
        outputs=y,
        input_scales=x_scale,
        intermediate_scales=z_scale,
        output_scales=y_scale,
        scaled_inputs=x_bar,
        scaled_intermediates=z_bar,
        scaled_outputs=y_bar,
        envelopment_constraint_template=envelopment_template,
        separate_convexity_constraints=separate_convexity,
    )


def compile_two_stage_reference(
    inputs: np.ndarray,
    intermediates: np.ndarray,
    outputs: np.ndarray,
    rows: np.ndarray,
) -> CompiledTwoStageReference:
    """Compile reusable multiplier inequalities for one reference set."""
    quantities = compile_two_stage_quantities(
        inputs,
        intermediates,
        outputs,
        rows,
    )
    x = quantities.inputs
    z = quantities.intermediates
    y = quantities.outputs
    if np.any(x.sum(axis=1) <= 0):
        raise ModelSpecificationError(
            "every relational reference observation needs a positive aggregate "
            "external-input normalizer"
        )
    if np.any(z.sum(axis=1) <= 0):
        raise ModelSpecificationError(
            "every relational reference observation needs a positive aggregate "
            "intermediate normalizer"
        )
    x_bar = quantities.scaled_inputs
    z_bar = quantities.scaled_intermediates
    y_bar = quantities.scaled_outputs

    n = rows.size
    m = x.shape[1]
    s = y.shape[1]
    stage_1 = hstack(
        [
            -csc_matrix(x_bar),
            csc_matrix(z_bar),
            csc_matrix((n, s)),
        ],
        format="csc",
    )
    stage_2 = hstack(
        [
            csc_matrix((n, m)),
            -csc_matrix(z_bar),
            csc_matrix(y_bar),
        ],
        format="csc",
    )
    stage_1_scales = np.maximum(
        np.max(x_bar, axis=1),
        np.max(z_bar, axis=1),
    )
    stage_2_scales = np.maximum(
        np.max(z_bar, axis=1),
        np.max(y_bar, axis=1),
    )
    if np.any(stage_1_scales <= 0) or np.any(stage_2_scales <= 0):
        raise ModelSpecificationError(
            "each reference observation needs positive activity in both stages"
        )
    constraints = vstack(
        [
            diags(1.0 / stage_1_scales, format="csc") @ stage_1,
            diags(1.0 / stage_2_scales, format="csc") @ stage_2,
        ],
        format="csc",
    )

    for array in (stage_1_scales, stage_2_scales):
        array.setflags(write=False)
    return CompiledTwoStageReference(
        rows=rows,
        inputs=x,
        intermediates=z,
        outputs=y,
        input_scales=quantities.input_scales,
        intermediate_scales=quantities.intermediate_scales,
        output_scales=quantities.output_scales,
        scaled_inputs=x_bar,
        scaled_intermediates=z_bar,
        scaled_outputs=y_bar,
        envelopment_constraint_template=(quantities.envelopment_constraint_template),
        separate_convexity_constraints=(quantities.separate_convexity_constraints),
        multiplier_constraints=constraints,
        stage_1_row_scales=stage_1_scales,
        stage_2_row_scales=stage_2_scales,
    )


def relational_multiplier_account(
    reference: CompiledTwoStageReference,
    x_o: np.ndarray,
    z_o: np.ndarray,
    y_o: np.ndarray,
    primal: np.ndarray,
    *,
    reported_objective: float,
    stage_objective: str | None,
    fixed_system_score: float | None,
    self_in_reference: bool,
) -> RelationalMultiplierAccount:
    """Reconstruct a complete relational account in original units.

    This routine deliberately does not reuse the scaled LP rows.  It converts
    the solver variables back to multipliers on the supplied quantities and
    independently checks normalization, both process inequalities, the active
    objective, an optional fixed-system equality, and the multiplicative
    system/process identity.
    """

    values = np.asarray(primal, dtype=np.float64).reshape(-1)
    m = reference.inputs.shape[1]
    q = reference.intermediates.shape[1]
    s = reference.outputs.shape[1]
    expected_size = m + q + s
    unavailable = RelationalMultiplierAccount(
        input_multipliers=None,
        intermediate_multipliers=None,
        output_multipliers=None,
        input_virtual_value=math.nan,
        intermediate_virtual_value=math.nan,
        output_virtual_value=math.nan,
        system_efficiency=math.nan,
        stage_1_efficiency=math.nan,
        stage_2_efficiency=math.nan,
        reconstruction_residual=math.nan,
        max_violation=math.inf,
    )
    if (
        values.shape != (expected_size,)
        or not np.isfinite(values).all()
        or not math.isfinite(reported_objective)
    ):
        return unavailable

    input_multipliers = values[:m] / reference.input_scales
    intermediate_multipliers = values[m : m + q] / reference.intermediate_scales
    output_multipliers = values[m + q :] / reference.output_scales
    if not all(
        np.isfinite(array).all()
        for array in (
            input_multipliers,
            intermediate_multipliers,
            output_multipliers,
        )
    ):
        return unavailable

    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        input_value = float(np.asarray(x_o, dtype=np.float64) @ input_multipliers)
        link_value = float(np.asarray(z_o, dtype=np.float64) @ intermediate_multipliers)
        output_value = float(np.asarray(y_o, dtype=np.float64) @ output_multipliers)
        reference_input_values = reference.inputs @ input_multipliers
        reference_link_values = reference.intermediates @ intermediate_multipliers
        reference_output_values = reference.outputs @ output_multipliers
    if not (
        math.isfinite(input_value)
        and math.isfinite(link_value)
        and math.isfinite(output_value)
        and np.isfinite(reference_input_values).all()
        and np.isfinite(reference_link_values).all()
        and np.isfinite(reference_output_values).all()
    ):
        return unavailable

    system_efficiency = output_value / input_value if input_value > 0.0 else math.nan
    stage_1_efficiency = link_value / input_value if input_value > 0.0 else math.nan
    stage_2_efficiency = output_value / link_value if link_value > 0.0 else math.nan
    stage_product = stage_1_efficiency * stage_2_efficiency
    reconstruction_residual = (
        system_efficiency - stage_product
        if math.isfinite(system_efficiency) and math.isfinite(stage_product)
        else math.nan
    )

    if stage_objective is None:
        expected_objective = -output_value
    elif stage_objective == "maximize_stage_1":
        expected_objective = -link_value
    elif stage_objective == "minimize_stage_1":
        expected_objective = link_value
    else:
        raise ValueError(f"unknown stage objective: {stage_objective!r}")
    objective_residual = abs(reported_objective - expected_objective) / max(
        1.0,
        abs(reported_objective),
        abs(expected_objective),
    )
    fixed_score_residual = (
        0.0
        if fixed_system_score is None
        else abs(output_value - fixed_system_score)
        / max(1.0, abs(output_value), abs(fixed_system_score))
    )
    identity_residual = (
        abs(reconstruction_residual) if math.isfinite(reconstruction_residual) else 0.0
    )
    self_reference_violation = (
        max(output_value - 1.0, 0.0) if self_in_reference else 0.0
    )
    max_violation = float(
        max(
            np.maximum(-values, 0.0).max(initial=0.0),
            abs(input_value - 1.0),
            np.maximum(
                reference_link_values - reference_input_values,
                0.0,
            ).max(initial=0.0),
            np.maximum(
                reference_output_values - reference_link_values,
                0.0,
            ).max(initial=0.0),
            objective_residual,
            fixed_score_residual,
            identity_residual,
            self_reference_violation,
        )
    )
    return RelationalMultiplierAccount(
        input_multipliers=np.asarray(input_multipliers, dtype=np.float64),
        intermediate_multipliers=np.asarray(
            intermediate_multipliers,
            dtype=np.float64,
        ),
        output_multipliers=np.asarray(output_multipliers, dtype=np.float64),
        input_virtual_value=input_value,
        intermediate_virtual_value=link_value,
        output_virtual_value=output_value,
        system_efficiency=system_efficiency,
        stage_1_efficiency=stage_1_efficiency,
        stage_2_efficiency=stage_2_efficiency,
        reconstruction_residual=reconstruction_residual,
        max_violation=max_violation,
    )


def relational_projection_account(
    reference: CompiledTwoStageReference,
    x_o: np.ndarray,
    y_o: np.ndarray,
    system_score: float,
    lambdas: np.ndarray,
    mus: np.ndarray,
) -> RelationalProjectionAccount:
    """Rebuild projection targets and process-link balances in original units."""

    lambda_values = np.asarray(lambdas, dtype=np.float64).reshape(-1)
    mu_values = np.asarray(mus, dtype=np.float64).reshape(-1)
    unavailable = RelationalProjectionAccount(
        input_targets=None,
        upstream_supply=None,
        downstream_requirement=None,
        output_targets=None,
        max_violation=math.inf,
    )
    if (
        lambda_values.shape != (reference.size,)
        or mu_values.shape != (reference.size,)
        or not np.isfinite(lambda_values).all()
        or not np.isfinite(mu_values).all()
        or not math.isfinite(system_score)
    ):
        return unavailable

    with np.errstate(over="ignore", invalid="ignore"):
        input_targets = reference.inputs.T @ lambda_values
        upstream_supply = reference.intermediates.T @ lambda_values
        downstream_requirement = reference.intermediates.T @ mu_values
        output_targets = reference.outputs.T @ mu_values
    if not all(
        np.isfinite(array).all()
        for array in (
            input_targets,
            upstream_supply,
            downstream_requirement,
            output_targets,
        )
    ):
        return unavailable

    input_violation = np.maximum(
        (input_targets - system_score * np.asarray(x_o, dtype=np.float64))
        / reference.input_scales,
        0.0,
    )
    link_violation = np.maximum(
        (downstream_requirement - upstream_supply) / reference.intermediate_scales,
        0.0,
    )
    output_violation = np.maximum(
        (np.asarray(y_o, dtype=np.float64) - output_targets) / reference.output_scales,
        0.0,
    )
    max_violation = float(
        max(
            np.maximum(-lambda_values, 0.0).max(initial=0.0),
            np.maximum(-mu_values, 0.0).max(initial=0.0),
            input_violation.max(initial=0.0),
            link_violation.max(initial=0.0),
            output_violation.max(initial=0.0),
        )
    )
    return RelationalProjectionAccount(
        input_targets=np.asarray(input_targets, dtype=np.float64),
        upstream_supply=np.asarray(upstream_supply, dtype=np.float64),
        downstream_requirement=np.asarray(
            downstream_requirement,
            dtype=np.float64,
        ),
        output_targets=np.asarray(output_targets, dtype=np.float64),
        max_violation=max_violation,
    )


def relational_projection_reconstruction_violation(
    reference: CompiledTwoStageReference,
    published: RelationalProjectionAccount,
    thresholded: RelationalProjectionAccount,
) -> float:
    """Measure whether displayed peers reproduce the published target account."""

    pairs = (
        (published.input_targets, thresholded.input_targets, reference.input_scales),
        (
            published.upstream_supply,
            thresholded.upstream_supply,
            reference.intermediate_scales,
        ),
        (
            published.downstream_requirement,
            thresholded.downstream_requirement,
            reference.intermediate_scales,
        ),
        (
            published.output_targets,
            thresholded.output_targets,
            reference.output_scales,
        ),
    )
    if any(left is None or right is None for left, right, _ in pairs):
        return math.inf
    deviations = []
    for left, right, scale in pairs:
        assert left is not None
        assert right is not None
        with np.errstate(over="ignore", invalid="ignore"):
            deviation = np.abs(left - right) / scale
        if not np.isfinite(deviation).all():
            return math.inf
        deviations.append(float(deviation.max(initial=0.0)))
    return max(deviations, default=0.0)


def multiplier_problem(
    reference: CompiledTwoStageReference,
    x_o: np.ndarray,
    z_o: np.ndarray,
    y_o: np.ndarray,
    *,
    system_score: float | None,
    stage_objective: str | None,
    name: str,
) -> LinearProgram:
    """Build the primary or a fixed-system secondary multiplier LP."""
    x_bar = x_o / reference.input_scales
    z_bar = z_o / reference.intermediate_scales
    y_bar = y_o / reference.output_scales
    m = x_bar.size
    q = z_bar.size
    s = y_bar.size
    n_variables = m + q + s

    objective = np.zeros(n_variables, dtype=np.float64)
    if stage_objective is None:
        objective[m + q :] = -y_bar
    elif stage_objective == "maximize_stage_1":
        objective[m : m + q] = -z_bar
    elif stage_objective == "minimize_stage_1":
        objective[m : m + q] = z_bar
    else:
        raise ValueError(f"unknown stage objective: {stage_objective!r}")

    normalization = np.zeros(n_variables, dtype=np.float64)
    normalization[:m] = x_bar
    equality_rows = [normalization]
    equality_values = [1.0]
    if system_score is not None:
        fixed_system = np.zeros(n_variables, dtype=np.float64)
        fixed_system[m + q :] = y_bar
        equality_rows.append(fixed_system)
        equality_values.append(system_score)

    return LinearProgram(
        c=objective,
        a_ub=reference.multiplier_constraints,
        b_ub=np.zeros(2 * reference.size, dtype=np.float64),
        a_eq=csc_matrix(np.vstack(equality_rows)),
        b_eq=np.asarray(equality_values, dtype=np.float64),
        bounds=((0.0, None),) * n_variables,
        name=name,
    )


def envelopment_problem(
    reference: CompiledTwoStageQuantities,
    x_o: np.ndarray,
    y_o: np.ndarray,
    *,
    orientation: Orientation = Orientation.INPUT,
    returns_to_scale: ReturnsToScale = ReturnsToScale.CRS,
    name: str,
) -> LinearProgram:
    """Bind an input- or output-radial two-stage envelopment programme."""
    x_bar_o = x_o / reference.input_scales
    y_bar_o = y_o / reference.output_scales
    n = reference.size
    m = reference.inputs.shape[1]
    q = reference.intermediates.shape[1]
    s = reference.outputs.shape[1]

    constraints = reference.envelopment_constraint_template.copy()
    factor_start = constraints.indptr[-2]
    factor_end = constraints.indptr[-1]
    factor_rows = constraints.indices[factor_start:factor_end]
    expected_factor_rows = np.concatenate(
        [
            np.arange(m, dtype=np.int64),
            m + q + np.arange(s, dtype=np.int64),
        ]
    )
    if not np.array_equal(factor_rows, expected_factor_rows):
        raise RuntimeError("invalid compiled two-stage radial factor column")
    objective = np.zeros(2 * n + 1, dtype=np.float64)
    if orientation is Orientation.INPUT:
        constraints.data[factor_start:factor_end] = np.concatenate(
            [-x_bar_o, np.zeros(s, dtype=np.float64)]
        )
        objective[-1] = 1.0
        b_ub = np.concatenate(
            [
                np.zeros(m + q, dtype=np.float64),
                -y_bar_o,
            ]
        )
    elif orientation is Orientation.OUTPUT:
        constraints.data[factor_start:factor_end] = np.concatenate(
            [np.zeros(m, dtype=np.float64), y_bar_o]
        )
        objective[-1] = -1.0
        b_ub = np.concatenate(
            [
                x_bar_o,
                np.zeros(q + s, dtype=np.float64),
            ]
        )
    else:
        raise ValueError("two-stage radial orientation must be input or output")
    constraints.eliminate_zeros()

    a_eq: csc_matrix | None = None
    b_eq: np.ndarray | None = None
    if returns_to_scale is ReturnsToScale.VRS:
        a_eq = reference.separate_convexity_constraints
        b_eq = np.ones(2, dtype=np.float64)
    elif returns_to_scale is not ReturnsToScale.CRS:
        raise ValueError("two-stage radial envelopment supports only CRS or VRS")

    return LinearProgram(
        c=objective,
        a_ub=constraints,
        b_ub=b_ub,
        a_eq=a_eq,
        b_eq=b_eq,
        bounds=((0.0, None),) * (2 * n + 1),
        name=name,
    )


__all__ = [
    "CompiledTwoStageQuantities",
    "CompiledTwoStageReference",
    "RelationalMultiplierAccount",
    "RelationalProjectionAccount",
    "compile_two_stage_quantities",
    "compile_two_stage_reference",
    "envelopment_problem",
    "multiplier_problem",
    "relational_multiplier_account",
    "relational_projection_account",
    "relational_projection_reconstruction_violation",
]
