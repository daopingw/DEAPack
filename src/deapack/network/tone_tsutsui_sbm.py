"""Tone--Tsutsui network slacks-based measures."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd

from .._registry import reference_spec as registry_reference_spec
from .._registry import registry_metadata
from ..enums import ReturnsToScale, SolverStatus, parse_enum
from ..exceptions import DataValidationError, ModelSpecificationError
from ..results import DEAResult
from ..solvers import (
    LPCertificate,
    LPSolution,
    LPSolver,
    SciPyHiGHSSolver,
    certify_lp_solution,
)
from ..specs import ReferenceSpec, SolverOptions
from ..technology import build_reference_plan
from ._network_sbm import (
    CompiledNetworkSBMLayout,
    CompiledNetworkSBMReference,
    LinkControl,
    LinkKind,
    SBMOrientation,
    compile_network_sbm_layout,
    compile_network_sbm_reference,
    network_sbm_problem,
    parse_link_kind,
)
from .data import NetworkData


def _orientation(value: str) -> SBMOrientation:
    if not isinstance(value, str):
        raise TypeError("orientation must be a string")
    normalized = value.strip().lower().replace("_", "-")
    aliases = {
        "input": "input",
        "output": "output",
        "non-oriented": "non-oriented",
        "nonoriented": "non-oriented",
    }
    try:
        return aliases[normalized]  # type: ignore[return-value]
    except KeyError as error:
        raise ValueError(
            "orientation must be 'input', 'output', or 'non-oriented'"
        ) from error


def _link_control(value: str) -> LinkControl:
    if not isinstance(value, str):
        raise TypeError("link_control must be a string")
    normalized = value.strip().lower().replace("_", "-")
    aliases = {
        "fixed": "fixed",
        "non-discretionary": "fixed",
        "nondiscretionary": "fixed",
        "free": "free",
        "discretionary": "free",
    }
    try:
        return aliases[normalized]  # type: ignore[return-value]
    except KeyError as error:
        raise ValueError(
            "link_control must be 'fixed'/'non-discretionary' or 'free'/'discretionary'"
        ) from error


def _diagnostic(
    *,
    dmu_id: object,
    period: object | None,
    solution: LPSolution,
    certificate: LPCertificate,
) -> dict[str, Any]:
    semantic_status = (
        SolverStatus.NUMERICAL_ERROR.value
        if solution.status is SolverStatus.OPTIMAL and not certificate.certified
        else solution.status.value
    )
    return {
        "dmu_id": dmu_id,
        "period": period,
        "phase": "primary",
        "solver_status": semantic_status,
        "backend_solver_status": solution.status.value,
        "raw_solver_status": solution.status.value,
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
        "original_unit_economic_postsolve_certified": pd.NA,
        "max_original_unit_normalized_violation": np.nan,
        "published_target_account_certified": False,
        "published_link_account_certified": False,
        "published_peer_account_certified": False,
        "published_dual_account_certified": False,
        "max_thresholded_peer_account_violation": np.nan,
        "omitted_intensity_mass": np.nan,
    }


def _economic_postsolve_violation(
    *,
    reference: CompiledNetworkSBMReference,
    scaled_observation: np.ndarray,
    process_accounts: dict[str, dict[str, Any]],
    recovered_lambdas: dict[str, np.ndarray],
    scaled_link_slacks: dict[str, np.ndarray],
    reconstruction_residual: float,
) -> float:
    """Rebuild source balances after reversing the fractional transform."""

    violations = [abs(reconstruction_residual)]
    for process in reference.layout.processes:
        account = process_accounts[process.process_id]
        lambdas = recovered_lambdas[process.process_id]
        if process.input_columns:
            columns = np.asarray(process.input_columns, dtype=np.int64)
            benchmark = reference.scaled_values[:, columns].T @ lambdas
            target = scaled_observation[columns] - account["scaled_input_slacks"]
            violations.append(float(np.abs(benchmark - target).max(initial=0.0)))
        if process.output_columns:
            columns = np.asarray(process.output_columns, dtype=np.int64)
            benchmark = reference.scaled_values[:, columns].T @ lambdas
            target = scaled_observation[columns] + account["scaled_output_slacks"]
            violations.append(float(np.abs(benchmark - target).max(initial=0.0)))

    for link, kind in zip(
        reference.layout.links,
        reference.link_kinds,
        strict=True,
    ):
        columns = np.asarray(link.columns, dtype=np.int64)
        source = reference.scaled_values[:, columns].T @ recovered_lambdas[link.source]
        recipient = (
            reference.scaled_values[:, columns].T @ recovered_lambdas[link.target]
        )
        observed = scaled_observation[columns]
        if kind == "fixed":
            violations.append(float(np.abs(source - observed).max(initial=0.0)))
            violations.append(float(np.abs(recipient - observed).max(initial=0.0)))
        else:
            violations.append(float(np.abs(source - recipient).max(initial=0.0)))
        if kind == "as_input":
            target = observed - scaled_link_slacks[link.link_id]
            violations.append(float(np.abs(recipient - target).max(initial=0.0)))
        elif kind == "as_output":
            target = observed + scaled_link_slacks[link.link_id]
            violations.append(float(np.abs(source - target).max(initial=0.0)))

    values = np.asarray(violations, dtype=np.float64)
    return math.inf if not np.isfinite(values).all() else float(values.max(initial=0.0))


def _original_unit_normalized_economic_violation(
    *,
    reference: CompiledNetworkSBMReference,
    scaled_observation: np.ndarray,
    process_accounts: dict[str, dict[str, Any]],
    recovered_lambdas: dict[str, np.ndarray],
    scaled_link_slacks: dict[str, np.ndarray],
    reconstruction_residual: float,
) -> float:
    """Certify balances after returning every economic account to source units."""

    violations = [abs(reconstruction_residual)]

    def append_normalized(
        left: np.ndarray,
        right: np.ndarray,
        scales: np.ndarray,
    ) -> None:
        left_original = np.asarray(left, dtype=np.float64) * scales
        right_original = np.asarray(right, dtype=np.float64) * scales
        denominator = np.maximum(
            1.0,
            np.maximum(np.abs(left_original), np.abs(right_original)),
        )
        violations.append(
            float(
                np.max(
                    np.abs(left_original - right_original) / denominator,
                    initial=0.0,
                )
            )
        )

    for process in reference.layout.processes:
        account = process_accounts[process.process_id]
        lambdas = recovered_lambdas[process.process_id]
        if process.input_columns:
            columns = np.asarray(process.input_columns, dtype=np.int64)
            benchmark = reference.scaled_values[:, columns].T @ lambdas
            target = scaled_observation[columns] - account["scaled_input_slacks"]
            append_normalized(benchmark, target, reference.scales[columns])
        if process.output_columns:
            columns = np.asarray(process.output_columns, dtype=np.int64)
            benchmark = reference.scaled_values[:, columns].T @ lambdas
            target = scaled_observation[columns] + account["scaled_output_slacks"]
            append_normalized(benchmark, target, reference.scales[columns])

    for link, kind in zip(
        reference.layout.links,
        reference.link_kinds,
        strict=True,
    ):
        columns = np.asarray(link.columns, dtype=np.int64)
        scales = reference.scales[columns]
        source = reference.scaled_values[:, columns].T @ recovered_lambdas[link.source]
        recipient = (
            reference.scaled_values[:, columns].T @ recovered_lambdas[link.target]
        )
        observed = scaled_observation[columns]
        if kind == "fixed":
            append_normalized(source, observed, scales)
            append_normalized(recipient, observed, scales)
        else:
            append_normalized(source, recipient, scales)
        if kind == "as_input":
            append_normalized(
                recipient,
                observed - scaled_link_slacks[link.link_id],
                scales,
            )
        elif kind == "as_output":
            append_normalized(
                source,
                observed + scaled_link_slacks[link.link_id],
                scales,
            )

    values = np.asarray(violations, dtype=np.float64)
    return math.inf if not np.isfinite(values).all() else float(values.max(initial=0.0))


class ToneTsutsuiNetworkSBM:
    """Estimate source-faithful input, output, or non-oriented network SBM.

    Each process has its own reference-intensity vector. Fixed links reproduce
    the assessed organization's observed handoff; free links choose one
    coordinated supplier-recipient target. Tone--Tsutsui's accountable-link
    extensions can additionally score an incoming link in its recipient's
    input account or an outgoing link in its supplier's output account while
    retaining bilateral continuity. Division weights are exogenous
    responsibility shares, not fitted DEA multipliers.
    """

    _registry_method_id = "network.sbm.tone_tsutsui_2009"

    def __init__(
        self,
        *,
        orientation: str = "non-oriented",
        returns_to_scale: ReturnsToScale | str = ReturnsToScale.VRS,
        link_control: str = "free",
        link_kinds: Mapping[str, str] | None = None,
        division_weights: Mapping[str, float] | None = None,
        reference: ReferenceSpec | str | None = None,
        solver: LPSolver | None = None,
        solver_options: SolverOptions | None = None,
        tolerance: float = 1e-7,
        peer_tolerance: float | None = None,
    ) -> None:
        self.orientation = _orientation(orientation)
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
                "ToneTsutsuiNetworkSBM supports the source CRS and VRS "
                "specifications only"
            )
        self.link_control = _link_control(link_control)
        if link_kinds is not None and not isinstance(link_kinds, Mapping):
            raise TypeError("link_kinds must be a link-ID-to-kind mapping")
        if link_kinds is not None and self.link_control != "free":
            raise ValueError(
                "pass either non-default link_control or link_kinds, not both"
            )
        declared_link_kinds: dict[str, LinkKind] | None = None
        if link_kinds is not None:
            if not all(
                isinstance(link_id, str) and link_id.strip() for link_id in link_kinds
            ):
                raise TypeError("link_kinds keys must be non-empty link IDs")
            declared_link_kinds = {
                link_id: parse_link_kind(kind) for link_id, kind in link_kinds.items()
            }
            kinds = set(declared_link_kinds.values())
            if self.orientation == "non-oriented" and kinds.intersection(
                {"as_input", "as_output"}
            ):
                raise ModelSpecificationError(
                    "Tone--Tsutsui equations (26)--(27) do not define a "
                    "non-oriented accountable-link score"
                )
            if self.orientation == "input" and "as_output" in kinds:
                raise ModelSpecificationError(
                    "as_output/LG links belong to the output-oriented equation (27)"
                )
            if self.orientation == "output" and "as_input" in kinds:
                raise ModelSpecificationError(
                    "as_input/LB links belong to the input-oriented equation (26)"
                )
        self.link_kinds = declared_link_kinds
        self.link_policy = "per-link" if link_kinds is not None else self.link_control
        if division_weights is not None and not isinstance(division_weights, Mapping):
            raise TypeError("division_weights must be a process-to-weight mapping")
        self.division_weights = division_weights
        self.reference = (
            ReferenceSpec()
            if reference is None
            else reference
            if isinstance(reference, ReferenceSpec)
            else ReferenceSpec(kind=reference)
        )
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

    def _resolved_link_kinds(
        self,
        layout: CompiledNetworkSBMLayout,
    ) -> dict[str, LinkKind]:
        if self.link_kinds is None:
            return {link_id: self.link_control for link_id in layout.link_ids}
        expected = set(layout.link_ids)
        actual = set(self.link_kinds)
        missing = expected.difference(actual)
        extra = actual.difference(expected)
        if missing or extra:
            raise ModelSpecificationError(
                "link_kinds must classify every network link exactly once; "
                f"missing={sorted(missing)!r}, extra={sorted(extra)!r}"
            )
        return {link_id: self.link_kinds[link_id] for link_id in layout.link_ids}

    def _weights(self, layout: CompiledNetworkSBMLayout) -> dict[str, float]:
        if self.division_weights is None:
            equal = 1.0 / len(layout.process_ids)
            return {process_id: equal for process_id in layout.process_ids}

        supplied = dict(self.division_weights)
        if not all(
            isinstance(process_id, str) and process_id.strip()
            for process_id in supplied
        ):
            raise TypeError("division weight keys must be process IDs")
        expected = set(layout.process_ids)
        actual = set(supplied)
        missing = expected.difference(actual)
        extra = actual.difference(expected)
        if missing or extra:
            raise ValueError(
                "division weights must contain every process exactly once; "
                f"missing={sorted(missing)!r}, extra={sorted(extra)!r}"
            )

        resolved: dict[str, float] = {}
        for process_id in layout.process_ids:
            value = supplied[process_id]
            if isinstance(value, bool) or not isinstance(
                value, (int, float, np.integer, np.floating)
            ):
                raise TypeError("division weight values must be real numbers")
            numeric = float(value)
            if not math.isfinite(numeric) or numeric < 0:
                raise ValueError("division weights must be finite and nonnegative")
            resolved[process_id] = numeric
        if not math.isclose(
            sum(resolved.values()),
            1.0,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ValueError("division weights must sum to one")
        return resolved

    def _validate_data(
        self,
        data: NetworkData,
        layout: CompiledNetworkSBMLayout,
        link_kinds: Mapping[str, LinkKind],
    ) -> None:
        if np.any(data.values <= 0):
            raise DataValidationError(
                "Tone--Tsutsui network SBM requires strictly positive "
                "external and link quantities; zero/signed variants need a "
                "separate source-qualified model"
            )
        for process in layout.processes:
            accountable_inputs = sum(
                len(link.columns)
                for link in layout.links
                if link_kinds[link.link_id] == "as_input"
                and link.target_index == process.index
            )
            accountable_outputs = sum(
                len(link.columns)
                for link in layout.links
                if link_kinds[link.link_id] == "as_output"
                and link.source_index == process.index
            )
            if self.orientation in {"input", "non-oriented"} and not (
                process.external_inputs or accountable_inputs
            ):
                raise ModelSpecificationError(
                    f"process {process.process_id!r} has no external input or "
                    "accountable incoming link "
                    f"for {self.orientation} network SBM"
                )
            if self.orientation in {"output", "non-oriented"} and not (
                process.external_outputs or accountable_outputs
            ):
                raise ModelSpecificationError(
                    f"process {process.process_id!r} has no external output or "
                    "accountable outgoing link "
                    f"for {self.orientation} network SBM"
                )

    def _undefined_summary(
        self,
        *,
        dmu_id: object,
        period: object | None,
        reference_size: int,
        solver_status: SolverStatus,
        score_status: str,
    ) -> dict[str, Any]:
        semantic_status = (
            SolverStatus.NUMERICAL_ERROR.value
            if solver_status is SolverStatus.OPTIMAL
            else solver_status.value
        )
        return {
            "dmu_id": dmu_id,
            "period": period,
            "score": np.nan,
            "efficiency": np.nan,
            "system_efficiency": np.nan,
            "score_valid": False,
            "score_status": score_status,
            "target_valid": False,
            "target_status": "not_available_without_certified_primary",
            "link_valid": False,
            "link_status": "not_available_without_certified_primary",
            "peer_valid": False,
            "peer_status": "not_available_without_certified_target",
            "dual_valid": False,
            "dual_status": "not_available_without_certified_primary",
            "distance": np.nan,
            "is_efficient": pd.NA,
            "is_network_sbm_efficient": pd.NA,
            "all_positive_weight_divisions_efficient": pd.NA,
            "all_divisions_efficient": pd.NA,
            "solver_status": semantic_status,
            "backend_solver_status": solver_status.value,
            "raw_solver_status": solver_status.value,
            "failure_reason": score_status,
            "model_family": "network_slacks_based",
            "orientation": self.orientation,
            "returns_to_scale": self.returns_to_scale.value,
            "link_control": self.link_policy,
            "reference_size": reference_size,
            "input_account": np.nan,
            "output_expansion_account": np.nan,
            "output_expansion_factor": np.nan,
            "transform_scale": np.nan,
            "reconstruction_residual": np.nan,
            "max_link_continuity_residual": np.nan,
            "max_fixed_link_residual": np.nan,
            "decomposition_status": ("solver_selected_not_uniqueness_certified"),
        }

    def fit(self, data: NetworkData) -> DEAResult:
        """Fit the connected source programme to every network observation."""
        if not isinstance(data, NetworkData):
            raise TypeError("ToneTsutsuiNetworkSBM.fit expects NetworkData")
        layout = compile_network_sbm_layout(data.network_spec)
        resolved_link_kinds = self._resolved_link_kinds(layout)
        self._validate_data(data, layout, resolved_link_kinds)
        accountable_link_specialization = (
            "network.sbm.tone_tsutsui_2009.accountable_input_link"
            if "as_input" in resolved_link_kinds.values()
            else "network.sbm.tone_tsutsui_2009.accountable_output_link"
            if "as_output" in resolved_link_kinds.values()
            else None
        )
        weights = self._weights(layout)
        all_positive_weights = all(value > 0 for value in weights.values())
        data_positions = {
            variable: position for position, variable in enumerate(data.variable_names)
        }
        reference_plan = build_reference_plan(data, self.reference)
        compiled: dict[int, CompiledNetworkSBMReference] = {}

        summary_rows: list[dict[str, Any]] = []
        component_rows: list[dict[str, Any]] = []
        slack_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        intensity_rows: list[dict[str, Any]] = []
        link_rows: list[dict[str, Any]] = []
        dual_rows: list[dict[str, Any]] = []
        diagnostic_rows: list[dict[str, Any]] = []
        primary_solves = 0

        for observation_index in range(data.n_dmus):
            set_id = reference_plan.set_id_for(observation_index)
            reference = compiled.get(set_id)
            if reference is None:
                reference = compile_network_sbm_reference(
                    data.values,
                    data.variable_names,
                    layout,
                    reference_plan.rows_for(observation_index),
                    returns_to_scale=self.returns_to_scale,
                    link_control=(
                        self.link_control if self.link_kinds is None else None
                    ),
                    link_kinds=(
                        None if self.link_kinds is None else resolved_link_kinds
                    ),
                )
                compiled[set_id] = reference

            dmu_id = data.dmu_ids[observation_index]
            period = None if data.periods is None else data.periods[observation_index]
            label = str(dmu_id) if period is None else f"{dmu_id}@{period}"
            observed = data.values[observation_index]
            problem = network_sbm_problem(
                reference,
                observed,
                np.asarray(
                    [weights[process_id] for process_id in layout.process_ids],
                    dtype=np.float64,
                ),
                orientation=self.orientation,
                name=f"{label}:three_process_service_chain_sbm",
            )
            solution = self.solver.solve(problem)
            primary_solves += 1
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
            if not certificate.certified or solution.primal is None:
                summary_rows.append(
                    self._undefined_summary(
                        dmu_id=dmu_id,
                        period=period,
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

            tau = float(solution.primal[reference.tau_index])
            # Charnes--Cooper only requires a finite, strictly positive scale.
            # Comparing tau with the model tolerance would incorrectly discard
            # valid programmes whose economic score is itself very small.
            if not math.isfinite(tau) or tau <= 0.0:
                diagnostic_rows[-1]["solver_status"] = (
                    SolverStatus.NUMERICAL_ERROR.value
                )
                diagnostic_rows[-1]["postsolve_certified"] = False
                diagnostic_rows[-1]["certification_reason"] = "invalid_transform_scale"
                diagnostic_rows[-1]["economic_postsolve_certified"] = False
                diagnostic_rows[-1]["economic_certification_reason"] = (
                    "invalid_transform_scale"
                )
                diagnostic_rows[-1]["max_economic_violation"] = math.inf
                summary_rows.append(
                    self._undefined_summary(
                        dmu_id=dmu_id,
                        period=period,
                        reference_size=reference.size,
                        solver_status=solution.status,
                        score_status="unavailable_uncertified_source_program",
                    )
                )
                continue
            scaled_observation = reference.canonical_observation(observed)

            process_accounts: dict[str, dict[str, Any]] = {}
            recovered_lambdas: dict[str, np.ndarray] = {}
            max_normalized_input_slack = 0.0
            max_normalized_output_slack = 0.0
            scaled_link_slacks: dict[str, np.ndarray] = {}
            normalized_link_slacks: dict[str, np.ndarray] = {}
            for link, kind, slack_slice in zip(
                reference.layout.links,
                reference.link_kinds,
                reference.link_slack_slices,
                strict=True,
            ):
                if kind not in {"as_input", "as_output"}:
                    continue
                scaled_slacks = np.asarray(
                    solution.primal[slack_slice] / tau,
                    dtype=np.float64,
                )
                scaled_slacks[np.abs(scaled_slacks) <= self.tolerance] = 0.0
                scaled_link_slacks[link.link_id] = scaled_slacks
                normalized_link_slacks[link.link_id] = np.asarray(
                    [
                        scaled_slacks[local] / scaled_observation[column]
                        for local, column in enumerate(link.columns)
                    ],
                    dtype=np.float64,
                )

            for process in reference.layout.processes:
                lambda_slice = reference.lambda_slices[process.index]
                input_slack_slice = reference.input_slack_slices[process.index]
                output_slack_slice = reference.output_slack_slices[process.index]
                lambdas = np.asarray(
                    solution.primal[lambda_slice] / tau,
                    dtype=np.float64,
                )
                lambdas[np.abs(lambdas) <= self.tolerance] = 0.0
                recovered_lambdas[process.process_id] = lambdas

                scaled_input_slacks = np.asarray(
                    solution.primal[input_slack_slice] / tau,
                    dtype=np.float64,
                )
                scaled_output_slacks = np.asarray(
                    solution.primal[output_slack_slice] / tau,
                    dtype=np.float64,
                )
                scaled_input_slacks[np.abs(scaled_input_slacks) <= self.tolerance] = 0.0
                scaled_output_slacks[np.abs(scaled_output_slacks) <= self.tolerance] = (
                    0.0
                )

                external_input_normalized = np.asarray(
                    [
                        scaled_input_slacks[local] / scaled_observation[column]
                        for local, column in enumerate(process.input_columns)
                    ],
                    dtype=np.float64,
                )
                external_output_normalized = np.asarray(
                    [
                        scaled_output_slacks[local] / scaled_observation[column]
                        for local, column in enumerate(process.output_columns)
                    ],
                    dtype=np.float64,
                )
                input_link_ids = tuple(
                    link.link_id
                    for link, kind in zip(
                        reference.layout.links,
                        reference.link_kinds,
                        strict=True,
                    )
                    if kind == "as_input" and link.target_index == process.index
                )
                output_link_ids = tuple(
                    link.link_id
                    for link, kind in zip(
                        reference.layout.links,
                        reference.link_kinds,
                        strict=True,
                    )
                    if kind == "as_output" and link.source_index == process.index
                )
                input_normalized = np.concatenate(
                    [
                        external_input_normalized,
                        *(
                            normalized_link_slacks[link_id]
                            for link_id in input_link_ids
                        ),
                    ]
                )
                output_normalized = np.concatenate(
                    [
                        external_output_normalized,
                        *(
                            normalized_link_slacks[link_id]
                            for link_id in output_link_ids
                        ),
                    ]
                )
                input_account = (
                    np.nan
                    if input_normalized.size == 0
                    else 1.0 - float(np.mean(input_normalized))
                )
                output_account = (
                    np.nan
                    if output_normalized.size == 0
                    else 1.0 + float(np.mean(output_normalized))
                )
                if self.orientation == "input":
                    process_efficiency = input_account
                elif self.orientation == "output":
                    process_efficiency = (
                        np.nan
                        if not math.isfinite(output_account)
                        or output_account <= self.tolerance
                        else 1.0 / output_account
                    )
                else:
                    process_efficiency = (
                        np.nan
                        if not math.isfinite(output_account)
                        or output_account <= self.tolerance
                        else input_account / output_account
                    )

                max_normalized_input_slack = max(
                    max_normalized_input_slack,
                    float(input_normalized.max(initial=0.0)),
                )
                max_normalized_output_slack = max(
                    max_normalized_output_slack,
                    float(output_normalized.max(initial=0.0)),
                )
                process_accounts[process.process_id] = {
                    "efficiency": float(process_efficiency),
                    "input_account": float(input_account),
                    "output_expansion_account": float(output_account),
                    "max_input_normalized_slack": float(
                        input_normalized.max(initial=0.0)
                    ),
                    "max_output_normalized_slack": float(
                        output_normalized.max(initial=0.0)
                    ),
                    "input_normalized_slacks": external_input_normalized,
                    "output_normalized_slacks": external_output_normalized,
                    "account_input_normalized_slacks": input_normalized,
                    "account_output_normalized_slacks": output_normalized,
                    "input_dimension": int(input_normalized.size),
                    "output_dimension": int(output_normalized.size),
                    "input_link_ids": input_link_ids,
                    "output_link_ids": output_link_ids,
                    "scaled_input_slacks": scaled_input_slacks,
                    "scaled_output_slacks": scaled_output_slacks,
                }

            weighted_input = (
                float(
                    sum(
                        weights[process_id]
                        * process_accounts[process_id]["input_account"]
                        for process_id in layout.process_ids
                    )
                )
                if all(
                    math.isfinite(process_accounts[process_id]["input_account"])
                    for process_id in layout.process_ids
                )
                else np.nan
            )
            weighted_output = (
                float(
                    sum(
                        weights[process_id]
                        * process_accounts[process_id]["output_expansion_account"]
                        for process_id in layout.process_ids
                    )
                )
                if all(
                    math.isfinite(
                        process_accounts[process_id]["output_expansion_account"]
                    )
                    for process_id in layout.process_ids
                )
                else np.nan
            )
            objective_value = float(solution.objective)
            denominators_valid = bool(
                math.isfinite(weighted_output)
                and weighted_output > self.tolerance
                and (self.orientation != "output" or objective_value < -self.tolerance)
            )
            if self.orientation == "input":
                efficiency = weighted_input
                objective_efficiency = objective_value
            elif self.orientation == "output" and denominators_valid:
                efficiency = 1.0 / weighted_output
                objective_efficiency = -1.0 / objective_value
            elif self.orientation == "non-oriented" and denominators_valid:
                efficiency = weighted_input / weighted_output
                objective_efficiency = objective_value
            else:
                efficiency = np.nan
                objective_efficiency = np.nan
            if (
                not math.isfinite(efficiency)
                or efficiency < -10.0 * self.tolerance
                or efficiency > 1.0 + 10.0 * self.tolerance
            ):
                diagnostic_rows[-1]["solver_status"] = (
                    SolverStatus.NUMERICAL_ERROR.value
                )
                diagnostic_rows[-1]["postsolve_certified"] = False
                diagnostic_rows[-1]["certification_reason"] = (
                    "invalid_source_efficiency"
                )
                diagnostic_rows[-1]["economic_postsolve_certified"] = False
                diagnostic_rows[-1]["economic_certification_reason"] = (
                    "invalid_source_efficiency"
                )
                diagnostic_rows[-1]["max_economic_violation"] = math.inf
                summary_rows.append(
                    self._undefined_summary(
                        dmu_id=dmu_id,
                        period=period,
                        reference_size=reference.size,
                        solver_status=solution.status,
                        score_status="unavailable_uncertified_source_program",
                    )
                )
                continue
            efficiency = float(np.clip(efficiency, 0.0, 1.0))
            reconstruction_residual = efficiency - objective_efficiency
            max_economic_violation = _economic_postsolve_violation(
                reference=reference,
                scaled_observation=scaled_observation,
                process_accounts=process_accounts,
                recovered_lambdas=recovered_lambdas,
                scaled_link_slacks=scaled_link_slacks,
                reconstruction_residual=reconstruction_residual,
            )
            max_original_unit_normalized_violation = (
                _original_unit_normalized_economic_violation(
                    reference=reference,
                    scaled_observation=scaled_observation,
                    process_accounts=process_accounts,
                    recovered_lambdas=recovered_lambdas,
                    scaled_link_slacks=scaled_link_slacks,
                    reconstruction_residual=reconstruction_residual,
                )
            )
            original_unit_certified = bool(
                math.isfinite(max_original_unit_normalized_violation)
                and max_original_unit_normalized_violation <= 10.0 * self.tolerance
            )
            economic_certified = bool(
                math.isfinite(max_economic_violation)
                and max_economic_violation <= 10.0 * self.tolerance
                and original_unit_certified
            )
            diagnostic_rows[-1]["economic_postsolve_certified"] = economic_certified
            diagnostic_rows[-1]["economic_certification_reason"] = (
                "certified"
                if economic_certified
                else "source_account_reconstruction_failed"
            )
            diagnostic_rows[-1]["max_economic_violation"] = max_economic_violation
            diagnostic_rows[-1]["original_unit_economic_postsolve_certified"] = (
                original_unit_certified
            )
            diagnostic_rows[-1]["max_original_unit_normalized_violation"] = (
                max_original_unit_normalized_violation
            )
            if not economic_certified:
                diagnostic_rows[-1]["solver_status"] = (
                    SolverStatus.NUMERICAL_ERROR.value
                )
                diagnostic_rows[-1]["postsolve_certified"] = False
                diagnostic_rows[-1]["certification_reason"] = (
                    "source_account_reconstruction_failed"
                )
                summary_rows.append(
                    self._undefined_summary(
                        dmu_id=dmu_id,
                        period=period,
                        reference_size=reference.size,
                        solver_status=solution.status,
                        score_status="unavailable_uncertified_source_program",
                    )
                )
                continue

            # Reporting thresholds are a presentation choice.  Rebuild the
            # complete process/link account after thresholding so that a
            # convenient sparse peer table can never be mistaken for a
            # certified representation of the published targets.
            thresholded_lambdas = {
                process_id: np.where(
                    values > self.peer_tolerance,
                    values,
                    0.0,
                )
                for process_id, values in recovered_lambdas.items()
            }
            omitted_intensity_mass = float(
                sum(
                    np.sum(np.abs(recovered_lambdas[process_id] - values))
                    for process_id, values in thresholded_lambdas.items()
                )
            )
            max_thresholded_peer_account_violation = _economic_postsolve_violation(
                reference=reference,
                scaled_observation=scaled_observation,
                process_accounts=process_accounts,
                recovered_lambdas=thresholded_lambdas,
                scaled_link_slacks=scaled_link_slacks,
                reconstruction_residual=0.0,
            )
            max_thresholded_peer_original_unit_violation = (
                _original_unit_normalized_economic_violation(
                    reference=reference,
                    scaled_observation=scaled_observation,
                    process_accounts=process_accounts,
                    recovered_lambdas=thresholded_lambdas,
                    scaled_link_slacks=scaled_link_slacks,
                    reconstruction_residual=0.0,
                )
            )
            peer_rts_violation = (
                max(
                    (
                        abs(float(values.sum()) - 1.0)
                        for values in thresholded_lambdas.values()
                    ),
                    default=0.0,
                )
                if self.returns_to_scale is ReturnsToScale.VRS
                else 0.0
            )
            max_thresholded_peer_account_violation = max(
                max_thresholded_peer_account_violation,
                max_thresholded_peer_original_unit_violation,
                peer_rts_violation,
            )
            peer_valid = bool(
                math.isfinite(max_thresholded_peer_account_violation)
                and max_thresholded_peer_account_violation <= 10.0 * self.tolerance
            )
            target_valid = original_unit_certified
            link_valid = original_unit_certified
            diagnostic_rows[-1].update(
                {
                    "published_target_account_certified": target_valid,
                    "published_link_account_certified": link_valid,
                    "published_peer_account_certified": peer_valid,
                    "max_thresholded_peer_account_violation": (
                        max_thresholded_peer_account_violation
                    ),
                    "max_thresholded_peer_original_unit_violation": (
                        max_thresholded_peer_original_unit_violation
                    ),
                    "thresholded_peer_rts_violation": peer_rts_violation,
                    "omitted_intensity_mass": omitted_intensity_mass,
                }
            )

            effective_weights: dict[str, float] = {}
            for process_id in layout.process_ids:
                if self.orientation in {"output", "non-oriented"}:
                    effective_weights[process_id] = (
                        weights[process_id]
                        * process_accounts[process_id]["output_expansion_account"]
                        / weighted_output
                    )
                else:
                    effective_weights[process_id] = weights[process_id]

            common_component = {
                "dmu_id": dmu_id,
                "period": period,
                "attribution_status": "solver_selected_primary_optimum",
            }
            component_rows.append(
                {
                    **common_component,
                    "component_kind": "system",
                    "component_id": "system",
                    "process_id": None,
                    "efficiency": efficiency,
                    "division_weight": 1.0,
                    "effective_reconstruction_weight": 1.0,
                    "input_account": weighted_input,
                    "output_expansion_account": weighted_output,
                    "input_inefficiency": (
                        np.nan
                        if not math.isfinite(weighted_input)
                        else 1.0 - weighted_input
                    ),
                    "output_inefficiency": (
                        np.nan
                        if not math.isfinite(weighted_output)
                        else weighted_output - 1.0
                    ),
                }
            )
            for process_id in layout.process_ids:
                account = process_accounts[process_id]
                component_rows.append(
                    {
                        **common_component,
                        "component_kind": "process",
                        "component_id": process_id,
                        "process_id": process_id,
                        "efficiency": account["efficiency"],
                        "division_weight": weights[process_id],
                        "effective_reconstruction_weight": (
                            effective_weights[process_id]
                        ),
                        "input_account": account["input_account"],
                        "output_expansion_account": account["output_expansion_account"],
                        "input_inefficiency": (
                            np.nan
                            if not math.isfinite(account["input_account"])
                            else 1.0 - account["input_account"]
                        ),
                        "output_inefficiency": (
                            np.nan
                            if not math.isfinite(account["output_expansion_account"])
                            else account["output_expansion_account"] - 1.0
                        ),
                    }
                )

            for process in reference.layout.processes:
                account = process_accounts[process.process_id]
                lambdas = recovered_lambdas[process.process_id]
                if peer_valid:
                    for local_position, intensity in enumerate(
                        thresholded_lambdas[process.process_id]
                    ):
                        if intensity <= 0.0:
                            continue
                        reference_position = int(reference.rows[local_position])
                        intensity_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": period,
                                "process_id": process.process_id,
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

                for (
                    role,
                    variables,
                    columns,
                    slack_key,
                    normalized_key,
                    matrix,
                ) in (
                    (
                        "external_input",
                        process.external_inputs,
                        process.input_columns,
                        "scaled_input_slacks",
                        "input_normalized_slacks",
                        reference.scaled_values[:, process.input_columns],
                    ),
                    (
                        "external_output",
                        process.external_outputs,
                        process.output_columns,
                        "scaled_output_slacks",
                        "output_normalized_slacks",
                        reference.scaled_values[:, process.output_columns],
                    ),
                ):
                    scaled_slacks = account[slack_key]
                    normalized_slacks = account[normalized_key]
                    dimension = (
                        account["input_dimension"]
                        if role == "external_input"
                        else account["output_dimension"]
                    )
                    for local, variable in enumerate(variables):
                        canonical_column = columns[local]
                        observed_value = float(observed[data_positions[variable]])
                        raw_slack = float(
                            scaled_slacks[local] * reference.scales[canonical_column]
                        )
                        target = (
                            observed_value - raw_slack
                            if role == "external_input"
                            else observed_value + raw_slack
                        )
                        reference_target = float(
                            matrix[:, local]
                            @ lambdas
                            * reference.scales[canonical_column]
                        )
                        balance_residual = target - reference_target
                        included = weights[process.process_id] > 0 and (
                            self.orientation == "non-oriented"
                            or (
                                self.orientation == "input" and role == "external_input"
                            )
                            or (
                                self.orientation == "output"
                                and role == "external_output"
                            )
                        )
                        target_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": period,
                                "process_id": process.process_id,
                                "role": role,
                                "variable": variable,
                                "observed": observed_value,
                                "target": target,
                                "balance_residual": balance_residual,
                                "selection_status": ("solver_selected_primary_optimum"),
                            }
                        )
                        slack_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": period,
                                "process_id": process.process_id,
                                "role": role,
                                "variable": variable,
                                "slack": raw_slack,
                                "normalizer": observed_value,
                                "normalized_slack": float(normalized_slacks[local]),
                                "average_weight": (
                                    np.nan if dimension == 0 else 1.0 / dimension
                                ),
                                "division_weight": weights[process.process_id],
                                "included_in_objective": included,
                            }
                        )

            max_link_continuity_residual = 0.0
            max_fixed_link_residual = 0.0
            max_accountable_link_balance_residual = 0.0
            for link, kind in zip(
                reference.layout.links,
                reference.link_kinds,
                strict=True,
            ):
                source_lambda = recovered_lambdas[link.source]
                target_lambda = recovered_lambdas[link.target]
                for local, variable in enumerate(link.variables):
                    canonical_column = link.columns[local]
                    scale = reference.scales[canonical_column]
                    source_target = float(
                        reference.scaled_values[:, canonical_column]
                        @ source_lambda
                        * scale
                    )
                    recipient_target = float(
                        reference.scaled_values[:, canonical_column]
                        @ target_lambda
                        * scale
                    )
                    common_target = 0.5 * (source_target + recipient_target)
                    continuity_residual = source_target - recipient_target
                    observed_value = float(observed[data_positions[variable]])
                    fixed_residual = (
                        common_target - observed_value if kind == "fixed" else np.nan
                    )
                    source_fixed_residual = (
                        source_target - observed_value if kind == "fixed" else np.nan
                    )
                    recipient_fixed_residual = (
                        recipient_target - observed_value if kind == "fixed" else np.nan
                    )
                    responsibility_owner: str | None = None
                    responsibility_role: str | None = None
                    raw_link_slack = np.nan
                    normalized_link_slack = np.nan
                    accountability_target = np.nan
                    accountability_balance_residual = np.nan
                    if kind in {"as_input", "as_output"}:
                        raw_link_slack = float(
                            scaled_link_slacks[link.link_id][local] * scale
                        )
                        normalized_link_slack = float(
                            normalized_link_slacks[link.link_id][local]
                        )
                        if kind == "as_input":
                            responsibility_owner = link.target
                            responsibility_role = "link_input"
                            accountability_target = observed_value - raw_link_slack
                            accountability_balance_residual = (
                                accountability_target - recipient_target
                            )
                        else:
                            responsibility_owner = link.source
                            responsibility_role = "link_output"
                            accountability_target = observed_value + raw_link_slack
                            accountability_balance_residual = (
                                accountability_target - source_target
                            )
                        max_accountable_link_balance_residual = max(
                            max_accountable_link_balance_residual,
                            abs(accountability_balance_residual),
                        )
                        owner_account = process_accounts[responsibility_owner]
                        dimension = (
                            owner_account["input_dimension"]
                            if kind == "as_input"
                            else owner_account["output_dimension"]
                        )
                        included = weights[responsibility_owner] > 0
                        target_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": period,
                                "process_id": responsibility_owner,
                                "role": responsibility_role,
                                "variable": variable,
                                "observed": observed_value,
                                "target": accountability_target,
                                "balance_residual": (accountability_balance_residual),
                                "link_id": link.link_id,
                                "selection_status": ("solver_selected_primary_optimum"),
                            }
                        )
                        slack_rows.append(
                            {
                                "dmu_id": dmu_id,
                                "period": period,
                                "process_id": responsibility_owner,
                                "role": responsibility_role,
                                "variable": variable,
                                "slack": raw_link_slack,
                                "normalizer": observed_value,
                                "normalized_slack": normalized_link_slack,
                                "average_weight": 1.0 / dimension,
                                "division_weight": weights[responsibility_owner],
                                "included_in_objective": included,
                                "link_id": link.link_id,
                            }
                        )
                    max_link_continuity_residual = max(
                        max_link_continuity_residual,
                        abs(continuity_residual),
                    )
                    if math.isfinite(source_fixed_residual):
                        max_fixed_link_residual = max(
                            max_fixed_link_residual,
                            abs(source_fixed_residual),
                            abs(recipient_fixed_residual),
                        )
                    link_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "link_id": link.link_id,
                            "source_process_id": link.source,
                            "recipient_process_id": link.target,
                            "variable": variable,
                            "link_control": kind,
                            "link_kind": kind,
                            "responsibility_owner_process_id": (responsibility_owner),
                            "responsibility_role": responsibility_role,
                            "observed": observed_value,
                            "source_target": source_target,
                            "recipient_target": recipient_target,
                            "target": common_target,
                            "accountability_target": accountability_target,
                            "link_slack": raw_link_slack,
                            "normalized_link_slack": normalized_link_slack,
                            "included_in_objective": (
                                kind in {"as_input", "as_output"}
                                and responsibility_owner is not None
                                and weights[responsibility_owner] > 0
                            ),
                            "accountability_balance_residual": (
                                accountability_balance_residual
                            ),
                            "continuity_residual": continuity_residual,
                            "source_residual": (source_target - common_target),
                            "recipient_residual": (recipient_target - common_target),
                            "fixed_observation_residual": fixed_residual,
                            "source_fixed_observation_residual": (
                                source_fixed_residual
                            ),
                            "recipient_fixed_observation_residual": (
                                recipient_fixed_residual
                            ),
                            "selection_status": ("solver_selected_primary_optimum"),
                        }
                    )

            candidate_dual_rows: list[dict[str, Any]] = []
            if solution.equality_marginals is not None:
                for row_index, descriptor in enumerate(reference.row_descriptors):
                    role, process_id, link_id, variable = descriptor
                    candidate_dual_rows.append(
                        {
                            "dmu_id": dmu_id,
                            "period": period,
                            "phase": "primary",
                            "constraint_role": role,
                            "process_id": process_id,
                            "link_id": link_id,
                            "variable": variable,
                            "marginal": float(solution.equality_marginals[row_index]),
                        }
                    )
                candidate_dual_rows.append(
                    {
                        "dmu_id": dmu_id,
                        "period": period,
                        "phase": "primary",
                        "constraint_role": (
                            "fractional_normalization"
                            if self.orientation == "non-oriented"
                            else "identity_normalization"
                        ),
                        "process_id": None,
                        "link_id": None,
                        "variable": "tau",
                        "marginal": float(solution.equality_marginals[-1]),
                    }
                )
            expected_dual_rows = len(reference.row_descriptors) + 1
            dual_valid = bool(
                len(candidate_dual_rows) == expected_dual_rows
                and all(
                    math.isfinite(float(row["marginal"])) for row in candidate_dual_rows
                )
            )
            diagnostic_rows[-1]["published_dual_account_certified"] = dual_valid
            diagnostic_rows[-1]["published_dual_row_count"] = len(candidate_dual_rows)
            diagnostic_rows[-1]["expected_dual_row_count"] = expected_dual_rows
            if dual_valid:
                dual_rows.extend(candidate_dual_rows)

            positive_weight_processes = tuple(
                process_id
                for process_id in layout.process_ids
                if weights[process_id] > 0
            )
            if self.orientation == "input":
                max_objective_normalized_slack = max(
                    process_accounts[process_id]["max_input_normalized_slack"]
                    for process_id in positive_weight_processes
                )
            elif self.orientation == "output":
                max_objective_normalized_slack = max(
                    process_accounts[process_id]["max_output_normalized_slack"]
                    for process_id in positive_weight_processes
                )
            else:
                max_objective_normalized_slack = max(
                    max(
                        process_accounts[process_id]["max_input_normalized_slack"],
                        process_accounts[process_id]["max_output_normalized_slack"],
                    )
                    for process_id in positive_weight_processes
                )
            is_network_sbm_efficient = bool(abs(efficiency - 1.0) <= self.tolerance)
            all_positive_weight_divisions_efficient = bool(
                all(
                    abs(process_accounts[process_id]["efficiency"] - 1.0)
                    <= self.tolerance
                    for process_id in positive_weight_processes
                )
            )
            all_divisions_efficient: bool | Any = (
                all_positive_weight_divisions_efficient
                if all_positive_weights
                else pd.NA
            )
            is_efficient: bool | Any = (
                all_divisions_efficient if self.orientation == "non-oriented" else pd.NA
            )
            summary_rows.append(
                {
                    "dmu_id": dmu_id,
                    "period": period,
                    "score": efficiency,
                    "efficiency": efficiency,
                    "system_efficiency": efficiency,
                    "score_valid": True,
                    "score_status": "defined",
                    "target_valid": target_valid,
                    "target_status": "certified_original_unit_target_account",
                    "link_valid": link_valid,
                    "link_status": "certified_original_unit_link_account",
                    "peer_valid": peer_valid,
                    "peer_status": (
                        "certified_thresholded_peer_account"
                        if peer_valid
                        else "unavailable_after_peer_reporting_threshold"
                    ),
                    "dual_valid": dual_valid,
                    "dual_status": (
                        "certified_complete_solver_dual_account"
                        if dual_valid
                        else "unavailable_incomplete_or_nonfinite_dual_account"
                    ),
                    "distance": 1.0 - efficiency,
                    "is_efficient": is_efficient,
                    "is_network_sbm_efficient": (is_network_sbm_efficient),
                    "all_positive_weight_divisions_efficient": (
                        all_positive_weight_divisions_efficient
                    ),
                    "all_divisions_efficient": all_divisions_efficient,
                    "solver_status": SolverStatus.OPTIMAL.value,
                    "backend_solver_status": solution.status.value,
                    "raw_solver_status": solution.status.value,
                    "failure_reason": pd.NA,
                    "model_family": "network_slacks_based",
                    "orientation": self.orientation,
                    "returns_to_scale": self.returns_to_scale.value,
                    "link_control": self.link_policy,
                    "reference_size": reference.size,
                    "input_account": weighted_input,
                    "output_expansion_account": weighted_output,
                    "output_expansion_factor": (
                        weighted_output if self.orientation == "output" else np.nan
                    ),
                    "transform_scale": tau,
                    "reconstruction_residual": reconstruction_residual,
                    "max_original_unit_normalized_violation": (
                        max_original_unit_normalized_violation
                    ),
                    "max_thresholded_peer_account_violation": (
                        max_thresholded_peer_account_violation
                    ),
                    "omitted_intensity_mass": omitted_intensity_mass,
                    "max_link_continuity_residual": (max_link_continuity_residual),
                    "max_fixed_link_residual": (
                        max_fixed_link_residual
                        if "fixed" in resolved_link_kinds.values()
                        else np.nan
                    ),
                    "max_accountable_link_balance_residual": (
                        max_accountable_link_balance_residual
                        if {"as_input", "as_output"}.intersection(
                            resolved_link_kinds.values()
                        )
                        else np.nan
                    ),
                    "max_objective_normalized_slack": (max_objective_normalized_slack),
                    "max_input_normalized_slack": (max_normalized_input_slack),
                    "max_output_normalized_slack": (max_normalized_output_slack),
                    "decomposition_status": (
                        "solver_selected_not_uniqueness_certified"
                    ),
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
            metadata={
                **registry_metadata(
                    self._registry_method_id,
                    {
                        "context": {
                            "purpose": (
                                "joint_system_and_process_performance_accountability"
                            ),
                            "sample": ("panel" if data.is_panel else "cross_section"),
                        },
                        "graph": {
                            "kind": "general_network",
                            "fingerprint": data.graph_fingerprint,
                            "processes": list(layout.process_ids),
                            "links": list(layout.link_ids),
                            "link_topology": {
                                link.link_id: {
                                    "source": link.source,
                                    "recipient": link.target,
                                    "variables": list(link.variables),
                                }
                                for link in layout.links
                            },
                        },
                        "data_roles": {
                            "external_inputs": {
                                process.process_id: list(process.external_inputs)
                                for process in layout.processes
                            },
                            "external_outputs": {
                                process.process_id: list(process.external_outputs)
                                for process in layout.processes
                            },
                            "intermediates": {
                                link.link_id: list(link.variables)
                                for link in layout.links
                            },
                        },
                        "technology": {
                            "family": "network_envelopment",
                            "returns_to_scale": (self.returns_to_scale.value),
                            "returns_to_scale_provenance": (
                                "tone_tsutsui_2009_explicit"
                            ),
                            "link_control": self.link_policy,
                            "link_kinds": dict(resolved_link_kinds),
                            "division_specific_intensities": True,
                        },
                        "estimator": {
                            "estimator_id": "estimator.full.dea",
                            "kind": "full_frontier",
                        },
                        "reference": registry_reference_spec(
                            self.reference,
                            reference_plan.kind,
                        ),
                        "performance": {
                            "family": "network_slacks_based_measure",
                            "orientation": self.orientation.replace("-", "_"),
                            "normalization": (
                                "evaluated_external_and_accountable_link_values"
                                if {"as_input", "as_output"}.intersection(
                                    resolved_link_kinds.values()
                                )
                                else "evaluated_external_variable_values"
                            ),
                        },
                        "valuation": {
                            "kind": ("exogenous_division_importance_weights"),
                            "division_weights": weights,
                        },
                        "evaluation_protocol": {
                            "kind": "self_appraisal",
                            "target_selection": ("solver_selected_primary_optimum"),
                        },
                        "analysis": {"kind": "joint_network_fit_with_process_account"},
                        "uncertainty": {"kind": "deterministic"},
                    },
                    specialization_id=accountable_link_specialization,
                ),
                "model_family": "network_slacks_based",
                "orientation": self.orientation,
                "returns_to_scale": self.returns_to_scale.value,
                "returns_to_scale_provenance": ("tone_tsutsui_2009_explicit"),
                "link_control": self.link_policy,
                "link_kinds": dict(resolved_link_kinds),
                "division_weights": dict(weights),
                "division_weight_source": (
                    "equal_default"
                    if self.division_weights is None
                    else "user_declared"
                ),
                "all_divisions_positive_weight": all_positive_weights,
                "all_division_efficiency_identified_by_system_one": (
                    all_positive_weights
                ),
                "graph_fingerprint": data.graph_fingerprint,
                "process_ids": layout.process_ids,
                "link_ids": layout.link_ids,
                "reference_kind": reference_plan.kind.value,
                "score_direction": "higher_is_better",
                "distance_transform": "one_minus_efficiency",
                "native_score": "system_efficiency",
                "transform_scale_column": "transform_scale",
                "linearization": (
                    "charnes_cooper"
                    if self.orientation == "non-oriented"
                    else "identity_scale"
                ),
                "base_objective_includes_link_slacks": bool(
                    {"as_input", "as_output"}.intersection(resolved_link_kinds.values())
                ),
                "attribution_status": ("solver_selected_not_uniqueness_certified"),
                "target_selection": ("solver_selected_primary_optimum"),
                "generic_efficiency_certification": (
                    "all_external_normalized_slacks"
                    if self.orientation == "non-oriented"
                    else "not_certified_by_single_orientation"
                ),
                "data_requirement": "strictly_positive",
                "solver": self.solver.name,
                "tolerance": self.tolerance,
                "peer_tolerance": self.peer_tolerance,
                "compiled_reference_sets": len(compiled),
                "primary_solves": primary_solves,
                "primary_solver_calls": primary_solves,
                "secondary_solver_calls": 0,
                "solver_calls": primary_solves,
                "additional_solver_calls": 0,
                "certificate_extra_solver_calls": 0,
                "source_oracle": (
                    "tone_tsutsui_dp07_08_eq_26_27_exact_synthetic"
                    if {"as_input", "as_output"}.intersection(
                        resolved_link_kinds.values()
                    )
                    else "tone_tsutsui_dp07_08_tables_3_4_6"
                ),
                "postsolve_certificate": {
                    "lp": "solver_neutral_primal_dual_kkt_and_strong_duality",
                    "economic": (
                        "transform_scale_score_canonical_and_original_unit_"
                        "process_link_reconstruction"
                    ),
                    "claim_gates": (
                        "score",
                        "target",
                        "link",
                        "thresholded_peer",
                        "dual_row_account",
                    ),
                    "failure_policy": (
                        "fail_closed_without_score_or_semantic_result_tables"
                    ),
                    "failure_scope": "per_observation_and_per_claim",
                    "additional_solver_calls": 0,
                },
            },
        )


NetworkSBM = ToneTsutsuiNetworkSBM
"""Short alias for :class:`ToneTsutsuiNetworkSBM`."""


__all__ = ["NetworkSBM", "ToneTsutsuiNetworkSBM"]
