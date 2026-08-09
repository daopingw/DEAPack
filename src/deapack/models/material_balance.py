"""Materials-balance environmental efficiency on a convex DEA technology."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix, hstack, vstack

from .._registry import (
    data_role_schema,
    registry_metadata,
)
from .._registry import (
    reference_spec as registry_reference_spec,
)
from ..data import DEAData
from ..enums import ReturnsToScale, SolverStatus, parse_enum
from ..exceptions import DataValidationError, ModelSpecificationError
from ..results import DEAResult
from ..solvers import LinearProgram, LPSolver, SciPyHiGHSSolver
from ..specs import ReferenceSpec, SolverOptions
from ..technology import build_reference_plan
from ._common import (
    CompiledReference,
    clean_small,
    compile_reference,
    join_optional_rows,
    join_optional_values,
    rts_matrices,
)


def _freeze_coefficients(
    values: Mapping[str, Mapping[str, float]],
    role: str,
) -> Mapping[str, Mapping[str, float]]:
    if not values:
        raise ValueError(f"{role} coefficients must declare at least one material")
    frozen: dict[str, Mapping[str, float]] = {}
    for material, coefficients in values.items():
        if not isinstance(material, str) or not material.strip():
            raise ValueError("material names must be non-empty strings")
        if not coefficients:
            raise ValueError(
                f"{role} coefficients for material {material!r} cannot be empty"
            )
        normalized: dict[str, float] = {}
        for variable, coefficient in coefficients.items():
            if not isinstance(variable, str) or not variable.strip():
                raise ValueError("variable names must be non-empty strings")
            numeric = float(coefficient)
            if not np.isfinite(numeric) or numeric < 0:
                raise ValueError(
                    f"{role} coefficient for {material!r}/{variable!r} must be "
                    "finite and nonnegative"
                )
            normalized[variable] = numeric
        frozen[material] = MappingProxyType(normalized)
    return MappingProxyType(frozen)


@dataclass(frozen=True, slots=True)
class MaterialBalanceCoefficients:
    """Named material contents for every input and desirable output.

    The outer mapping is keyed by material or pollutant name. Each inner
    mapping must explicitly cover every input/output variable, including
    zero coefficients. More than one material requires positive aggregation
    weights because unlike units cannot be combined implicitly.
    """

    inputs: Mapping[str, Mapping[str, float]]
    outputs: Mapping[str, Mapping[str, float]]
    weights: Mapping[str, float] | None = None

    def __post_init__(self) -> None:
        inputs = _freeze_coefficients(self.inputs, "input")
        outputs = _freeze_coefficients(self.outputs, "output")
        if set(inputs) != set(outputs):
            raise ValueError(
                "input and output coefficients must declare identical materials"
            )

        materials = tuple(inputs)
        if self.weights is None:
            if len(materials) != 1:
                raise ValueError(
                    "multiple materials require explicit positive aggregation weights"
                )
            weights: Mapping[str, float] = MappingProxyType({materials[0]: 1.0})
        else:
            if set(self.weights) != set(materials):
                raise ValueError(
                    "weight names must exactly match the declared materials"
                )
            normalized_weights: dict[str, float] = {}
            for material in materials:
                weight = float(self.weights[material])
                if not np.isfinite(weight) or weight <= 0:
                    raise ValueError("material weights must be finite and positive")
                normalized_weights[material] = weight
            weights = MappingProxyType(normalized_weights)

        object.__setattr__(self, "inputs", inputs)
        object.__setattr__(self, "outputs", outputs)
        object.__setattr__(self, "weights", weights)

    @property
    def material_names(self) -> tuple[str, ...]:
        """Return materials in their deterministic declaration order."""
        return tuple(self.inputs)

    def align(
        self,
        data: DEAData,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Align named coefficients to the validated DEA variable order."""
        input_rows: list[list[float]] = []
        output_rows: list[list[float]] = []
        for material in self.material_names:
            input_coefficients = self.inputs[material]
            output_coefficients = self.outputs[material]
            self._validate_variables(
                material,
                "input",
                input_coefficients,
                data.input_names,
            )
            self._validate_variables(
                material,
                "output",
                output_coefficients,
                data.output_names,
            )
            input_rows.append(
                [float(input_coefficients[name]) for name in data.input_names]
            )
            output_rows.append(
                [float(output_coefficients[name]) for name in data.output_names]
            )

        input_array = np.asarray(input_rows, dtype=np.float64)
        output_array = np.asarray(output_rows, dtype=np.float64)
        weight_array = np.asarray(
            [self.weights[name] for name in self.material_names],
            dtype=np.float64,
        )
        for array in (input_array, output_array, weight_array):
            array.setflags(write=False)
        return input_array, output_array, weight_array

    @staticmethod
    def _validate_variables(
        material: str,
        role: str,
        coefficients: Mapping[str, float],
        expected: tuple[str, ...],
    ) -> None:
        missing = set(expected).difference(coefficients)
        extra = set(coefficients).difference(expected)
        if missing or extra:
            raise ModelSpecificationError(
                f"{role} coefficients for material {material!r} must explicitly "
                f"match DEA variables; missing={sorted(missing)!r}, "
                f"extra={sorted(extra)!r}"
            )


class MaterialBalanceDEA:
    """Coelli--Lauwers--Van Huylenbroeck environmental efficiency.

    The model minimizes material inflow for the observed desirable-output
    bundle on the same convex technology used to estimate input-oriented
    radial technical efficiency. Environmental efficiency is decomposed as
    ``EE = TE * EAE``. Observed bad-output columns are deliberately rejected:
    this model calculates material surplus from known physical coefficients.
    """

    _registry_method_id = "environmental.material_inflow.coelli2007"

    def __init__(
        self,
        coefficients: MaterialBalanceCoefficients,
        *,
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.CRS,
        reference: ReferenceSpec | str | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        if not isinstance(coefficients, MaterialBalanceCoefficients):
            raise TypeError("coefficients must be MaterialBalanceCoefficients")
        self.coefficients = coefficients
        self.returns_to_scale = parse_enum(
            returns_to_scale, ReturnsToScale, "returns_to_scale"
        )
        if self.returns_to_scale not in {
            ReturnsToScale.CRS,
            ReturnsToScale.VRS,
        }:
            raise ModelSpecificationError(
                "MaterialBalanceDEA currently supports only CRS and VRS; "
                "NIRS and NDRS material-inflow identities are deferred until "
                "their source and independent-oracle contracts are closed"
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
        if tolerance <= 0:
            raise ValueError("tolerance must be positive")
        self.tolerance = float(tolerance)
        self.peer_tolerance = (
            self.tolerance if peer_tolerance is None else float(peer_tolerance)
        )
        if self.peer_tolerance <= 0:
            raise ValueError("peer_tolerance must be positive")

    def _validate_data(
        self,
        data: DEAData,
        input_coefficients: np.ndarray,
        output_coefficients: np.ndarray,
        weights: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        data.ensure_nonnegative()
        if data.bad_outputs is not None:
            raise ModelSpecificationError(
                "MaterialBalanceDEA calculates surplus from physical "
                "coefficients and does not consume bad_outputs columns"
            )
        if np.any(data.inputs.sum(axis=1) <= 0):
            raise DataValidationError(
                "each observation needs at least one strictly positive input"
            )
        if np.any(data.outputs.sum(axis=1) <= 0):
            raise DataValidationError(
                "each observation needs at least one strictly positive output"
            )
        if np.any(input_coefficients.sum(axis=1) <= 0):
            raise ModelSpecificationError(
                "every material needs a positive coefficient on at least one input"
            )

        input_flows = data.inputs @ input_coefficients.T
        retained_flows = data.outputs @ output_coefficients.T
        surpluses = input_flows - retained_flows
        invalid = surpluses < -self.tolerance
        if invalid.any():
            examples = np.argwhere(invalid)[:5]
            labels = [
                (
                    data.dmu_ids[int(row)],
                    self.coefficients.material_names[int(column)],
                )
                for row, column in examples
            ]
            raise DataValidationError(
                "materials balance requires input content to cover material "
                f"retained in outputs; invalid (DMU, material) examples={labels!r}"
            )

        aggregate_input_coefficients = weights @ input_coefficients
        aggregate_output_coefficients = weights @ output_coefficients
        aggregate_inflows = data.inputs @ aggregate_input_coefficients
        if np.any(aggregate_inflows <= self.tolerance):
            positions = np.flatnonzero(aggregate_inflows <= self.tolerance)[:5]
            raise DataValidationError(
                "every observation needs positive weighted material inflow; "
                f"invalid row positions include {positions.tolist()}"
            )
        return (
            aggregate_input_coefficients,
            aggregate_output_coefficients,
            clean_small(surpluses, self.tolerance),
        )

    def _technical_problem(
        self,
        reference: CompiledReference,
        x_o: np.ndarray,
        y_o: np.ndarray,
        name: str,
    ) -> LinearProgram:
        n_lambda = reference.size
        n_variables = n_lambda + 1
        input_rows = hstack(
            [reference.inputs, csc_matrix((-x_o).reshape(-1, 1))],
            format="csc",
        )
        output_rows = hstack(
            [-reference.outputs, csc_matrix((y_o.size, 1))],
            format="csc",
        )
        a_ub = vstack([input_rows, output_rows], format="csc")
        b_ub = np.concatenate([np.zeros(x_o.size), -y_o])
        rts_ub, rts_b_ub, rts_eq, rts_b_eq = rts_matrices(
            n_variables, n_lambda, self.returns_to_scale
        )
        a_ub = join_optional_rows(a_ub, rts_ub)
        b_ub = join_optional_values(b_ub, rts_b_ub)
        objective = np.zeros(n_variables, dtype=np.float64)
        objective[-1] = 1.0
        return LinearProgram(
            c=objective,
            a_ub=a_ub,
            b_ub=b_ub,
            a_eq=rts_eq,
            b_eq=rts_b_eq,
            bounds=((0.0, None),) * n_variables,
            name=f"{name}:material_balance:technical",
        )

    def _material_problem(
        self,
        reference: CompiledReference,
        y_o: np.ndarray,
        aggregate_input_coefficients: np.ndarray,
        name: str,
    ) -> LinearProgram:
        n_lambda = reference.size
        a_ub = -reference.outputs
        b_ub = -y_o
        rts_ub, rts_b_ub, rts_eq, rts_b_eq = rts_matrices(
            n_lambda, n_lambda, self.returns_to_scale
        )
        a_ub = join_optional_rows(a_ub, rts_ub)
        b_ub = join_optional_values(b_ub, rts_b_ub)
        objective = np.asarray(aggregate_input_coefficients @ reference.inputs).reshape(
            -1
        )
        return LinearProgram(
            c=objective,
            a_ub=a_ub,
            b_ub=b_ub,
            a_eq=rts_eq,
            b_eq=rts_b_eq,
            bounds=((0.0, None),) * n_lambda,
            name=f"{name}:material_balance:minimum_inflow",
        )

    def fit(self, data: DEAData) -> DEAResult:
        """Estimate material, technical, and environmental allocative efficiency."""
        input_coefficients, output_coefficients, weights = self.coefficients.align(data)
        (
            aggregate_input_coefficients,
            aggregate_output_coefficients,
            observed_surpluses,
        ) = self._validate_data(
            data,
            input_coefficients,
            output_coefficients,
            weights,
        )
        reference_plan = build_reference_plan(data, self.reference)
        compiled: dict[int, CompiledReference] = {}

        summary_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []

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

            technical = self.solver.solve(
                self._technical_problem(reference, x_o, y_o, name)
            )
            material = self.solver.solve(
                self._material_problem(
                    reference,
                    y_o,
                    aggregate_input_coefficients,
                    name,
                )
            )
            for component, solution in (
                ("technical", technical),
                ("material_minimum", material),
            ):
                diagnostic_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "phase": 1,
                        "component": component,
                        "solver_status": solution.status.value,
                        "message": solution.message,
                        "iterations": solution.iterations,
                        "objective": solution.objective,
                        "max_primal_violation": solution.max_primal_violation,
                    }
                )

            if (
                not technical.is_optimal
                or technical.primal is None
                or technical.objective is None
                or not material.is_optimal
                or material.primal is None
                or material.objective is None
            ):
                status = (
                    technical.status if not technical.is_optimal else material.status
                )
                summary_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "score": np.nan,
                        "efficiency": np.nan,
                        "distance": np.nan,
                        "is_efficient": pd.NA,
                        "is_material_efficient": pd.NA,
                        "solver_status": status.value,
                        "model_family": "material_balance",
                        "orientation": "input",
                        "technical_efficiency": np.nan,
                        "environmental_allocative_efficiency": np.nan,
                        "observed_material_inflow": np.nan,
                        "minimum_material_inflow": np.nan,
                        "reference_size": reference.size,
                    }
                )
                continue

            technical_efficiency = float(technical.primal[-1])
            observed_inflow = float(aggregate_input_coefficients @ x_o)
            minimum_inflow = float(material.objective)
            environmental_efficiency = minimum_inflow / observed_inflow
            if abs(environmental_efficiency - 1.0) <= self.tolerance:
                environmental_efficiency = 1.0
            environmental_allocative_efficiency = (
                environmental_efficiency / technical_efficiency
            )
            if abs(environmental_allocative_efficiency - 1.0) <= self.tolerance:
                environmental_allocative_efficiency = 1.0

            technical_intensities = clean_small(
                technical.primal[: reference.size], self.tolerance
            )
            material_intensities = clean_small(material.primal, self.tolerance)
            for component, intensities in (
                ("technical", technical_intensities),
                ("material_minimum", material_intensities),
            ):
                for local_position, intensity in enumerate(intensities):
                    if intensity > self.peer_tolerance:
                        reference_position = reference.rows[local_position]
                        intensity_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": period,
                                "component": component,
                                "reference_dmu_id": data.dmu_ids[reference_position],
                                "reference_period": (
                                    None
                                    if data.periods is None
                                    else data.periods[reference_position]
                                ),
                                "lambda": float(intensity),
                            }
                        )

            technical_target = technical_efficiency * x_o
            material_target = np.asarray(
                reference.inputs @ material_intensities
            ).reshape(-1)
            for variable, observed, target in zip(
                data.input_names, x_o, technical_target, strict=True
            ):
                target_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "target_type": "technical_radial",
                        "role": "input",
                        "variable": variable,
                        "observed": float(observed),
                        "target": float(target),
                    }
                )
            for variable, observed, target in zip(
                data.input_names, x_o, material_target, strict=True
            ):
                target_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "target_type": "material_minimum",
                        "role": "input",
                        "variable": variable,
                        "observed": float(observed),
                        "target": float(target),
                    }
                )

            target_input_flows = input_coefficients @ material_target
            retained_flows = output_coefficients @ y_o
            target_surpluses = clean_small(
                target_input_flows - retained_flows,
                self.tolerance,
            )
            for material_index, (
                material_name,
                observed_surplus,
                target_inflow,
                target_surplus,
            ) in enumerate(
                zip(
                    self.coefficients.material_names,
                    observed_surpluses[observation],
                    target_input_flows,
                    target_surpluses,
                    strict=True,
                )
            ):
                target_rows.extend(
                    [
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "target_type": "material_minimum",
                            "role": "material_inflow",
                            "variable": material_name,
                            "observed": float(input_coefficients[material_index] @ x_o),
                            "target": float(target_inflow),
                        },
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "target_type": "material_minimum",
                            "role": "material_surplus",
                            "variable": material_name,
                            "observed": float(observed_surplus),
                            "target": float(target_surplus),
                        },
                    ]
                )

            observed_aggregate_surplus = float(
                observed_inflow - aggregate_output_coefficients @ y_o
            )
            minimum_aggregate_surplus = float(
                minimum_inflow - aggregate_output_coefficients @ y_o
            )
            is_material_efficient = bool(
                environmental_efficiency >= 1.0 - self.tolerance
            )
            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "score": environmental_efficiency,
                    "efficiency": environmental_efficiency,
                    "distance": 1.0 - environmental_efficiency,
                    "is_efficient": pd.NA,
                    "is_material_efficient": is_material_efficient,
                    "solver_status": SolverStatus.OPTIMAL.value,
                    "model_family": "material_balance",
                    "orientation": "input",
                    "technical_efficiency": technical_efficiency,
                    "environmental_allocative_efficiency": (
                        environmental_allocative_efficiency
                    ),
                    "observed_material_inflow": observed_inflow,
                    "minimum_material_inflow": minimum_inflow,
                    "observed_material_surplus": observed_aggregate_surplus,
                    "minimum_material_surplus": minimum_aggregate_surplus,
                    "reference_size": reference.size,
                }
            )

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
                            "purpose": "material_use_and_surplus_management",
                            "sample": "panel" if data.is_panel else "cross_section",
                        },
                        "graph": {"kind": "black_box_material_account"},
                        "data_roles": {
                            "inputs": "material_bearing_and_other_resources",
                            "outputs": "desirable_services_with_material_content",
                            "bad_outputs": "not_used_directly",
                            **data_role_schema(data),
                        },
                        "technology": {
                            "family": "convex_envelopment_with_material_account",
                            "returns_to_scale": self.returns_to_scale.value,
                            "balance_rule": "input_content_minus_output_content",
                        },
                        "estimator": {
                            "estimator_id": "estimator.full.dea",
                            "kind": "full_frontier",
                            "family": "dea_envelopment",
                        },
                        "reference": registry_reference_spec(
                            self.reference, reference_plan.kind
                        ),
                        "performance": {
                            "family": "minimum_material_inflow",
                            "orientation": "input",
                            "decomposition": (
                                "technical_times_environmental_allocative"
                            ),
                        },
                        "valuation": {
                            "kind": "declared_material_coefficients_and_weights",
                            "materials": list(self.coefficients.material_names),
                            "weights": {
                                material: float(self.coefficients.weights[material])
                                for material in self.coefficients.material_names
                            },
                            "input_coefficients": {
                                material: {
                                    name: float(value)
                                    for name, value in self.coefficients.inputs[
                                        material
                                    ].items()
                                }
                                for material in self.coefficients.material_names
                            },
                            "output_coefficients": {
                                material: {
                                    name: float(value)
                                    for name, value in self.coefficients.outputs[
                                        material
                                    ].items()
                                }
                                for material in self.coefficients.material_names
                            },
                        },
                        "evaluation_protocol": {"kind": "self_appraisal"},
                        "analysis": {"kind": "material_efficiency_decomposition"},
                        "uncertainty": {"kind": "deterministic"},
                    },
                ),
                "model_family": "material_balance",
                "variant": "coelli_lauwers_van_huylenbroeck",
                "orientation": "input",
                "returns_to_scale": self.returns_to_scale.value,
                "reference_kind": reference_plan.kind.value,
                "materials": self.coefficients.material_names,
                "material_weights": dict(self.coefficients.weights),
                "material_input_coefficients": {
                    material: dict(self.coefficients.inputs[material])
                    for material in self.coefficients.material_names
                },
                "material_output_coefficients": {
                    material: dict(self.coefficients.outputs[material])
                    for material in self.coefficients.material_names
                },
                "native_score": "environmental_efficiency",
                "score_direction": "higher_is_better",
                "decomposition": "EE = TE * EAE",
                "surplus_identity": "input_content_minus_output_content",
                "bad_outputs_used": False,
                "pollution_control": "not_explicit_unless_declared_as_good_output",
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "compiled_reference_sets": reference_plan.unique_reference_sets,
            },
        )


CoelliMaterialBalanceDEA = MaterialBalanceDEA
"""Discoverability alias for :class:`MaterialBalanceDEA`."""
