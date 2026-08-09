"""Governed A/B experiment for HiGHS presolve in Dynamic SBM.

This script is deliberately outside ``benchmarks/cases.json``.  It studies a
solver setting without changing the release workload or the public/default
``SolverOptions(presolve=True)`` behavior.

Run the frozen small matrix from the repository root with::

    python benchmarks/experiments/dynamic_sbm_presolve_ab.py

Use ``--format json`` when a machine-readable experiment record is required.
Each A and B fit runs in a fresh process so elapsed time and sampled peak RSS
are attributable to one presolve setting rather than to cumulative allocator
state.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from importlib import metadata, util
from pathlib import Path

import numpy as np
import pandas as pd
import psutil
import scipy
from pandas.api.types import is_bool_dtype, is_numeric_dtype

from deapack import (
    CarryOverSpec,
    DynamicData,
    DynamicSBM,
    DynamicSBMSpec,
    PeriodProductionSpec,
    SolverOptions,
    load_dataset,
)

PROFILES = ("oracle", "realistic", "extreme")
ORIENTATIONS = ("input", "output", "non-oriented")
RETURNS_TO_SCALE = ("crs", "vrs")
ALL_CARRYOVER_ROLES = ("bad", "fixed", "free", "good")
DEFAULT_ATOL = 2.0e-8
DEFAULT_RTOL = 2.0e-8
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_SPEC = (
    REPOSITORY_ROOT / "specs" / "experiments" / ("M10_F_DYNAMIC_SBM_PRESOLVE_AB.md")
)

_FRAME_KEYS = {
    "summary": ("dmu_id",),
    "diagnostics": ("dmu_id", "period", "phase"),
    "targets": ("dmu_id", "period", "role", "variable"),
    "peers": (
        "dmu_id",
        "period",
        "reference_dmu_id",
        "reference_period",
    ),
    "slacks": ("dmu_id", "period", "role", "variable"),
    "links": ("dmu_id", "period", "carryover"),
    "components": ("dmu_id", "period", "component_type", "component_id"),
}
_IGNORED_COLUMNS = {
    # These describe HiGHS' execution path, not the fitted economic result or
    # its certificates.  Status fields and every residual/certificate remain.
    "diagnostics": frozenset({"message", "iterations"}),
}


@dataclass(frozen=True, slots=True)
class ExperimentCase:
    """One frozen data-profile/model pair in the presolve experiment."""

    profile: str
    orientation: str
    returns_to_scale: str

    @property
    def case_id(self) -> str:
        return f"{self.profile}:{self.orientation}:{self.returns_to_scale}"


def _benchmark_runner_module():  # type: ignore[no-untyped-def]
    """Load the release runner so this experiment reuses its source ledger."""
    module_name = "_deapack_m10f_benchmark_runner"
    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing
    runner_path = REPOSITORY_ROOT / "scripts" / "run_benchmarks.py"
    specification = util.spec_from_file_location(module_name, runner_path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load benchmark runner from {runner_path}")
    module = util.module_from_spec(specification)
    sys.modules[module_name] = module
    specification.loader.exec_module(module)
    return module


def _source_tree_ledger() -> dict[str, object]:
    """Freeze executable/governance bytes with the M10-A ledger algorithm."""
    runner = _benchmark_runner_module()
    paths = runner._discover_source_paths(REPOSITORY_ROOT)
    paths.extend(
        (
            Path(__file__).resolve().relative_to(REPOSITORY_ROOT).as_posix(),
            EXPERIMENT_SPEC.relative_to(REPOSITORY_ROOT).as_posix(),
        )
    )
    ledger = runner._source_tree_ledger(paths, repository_root=REPOSITORY_ROOT)
    runner.verify_source_tree_ledger(ledger, repository_root=REPOSITORY_ROOT)
    import deapack

    expected_init = (REPOSITORY_ROOT / "src" / "deapack" / "__init__.py").resolve()
    resolved_init = Path(deapack.__file__).resolve()
    runtime_verified = resolved_init == expected_init
    ledger["runtime_import"] = {
        "expected_package_init": str(expected_init),
        "resolved_package_init": str(resolved_init),
        "verified": runtime_verified,
    }
    ledger["scope"]["included"].append(
        "M10-F Dynamic-SBM presolve experiment script and specification record"
    )
    return ledger


def _verify_unchanged_source_tree(initial: dict[str, object]) -> None:
    """Close the start-to-finish ledger gate in place."""
    final = _source_tree_ledger()
    stable_fields = (
        "format_version",
        "hash_algorithm",
        "aggregate_format",
        "sha256",
        "file_count",
        "total_bytes",
        "files",
    )
    changed = any(initial[field] != final[field] for field in stable_fields)
    initial["observed_after_run_sha256"] = final["sha256"]
    initial["source_changed_during_run"] = changed
    initial["verified_unchanged_after_run"] = not changed


def experiment_cases(
    *,
    profiles: tuple[str, ...] = PROFILES,
    orientations: tuple[str, ...] = ORIENTATIONS,
    returns_to_scale: tuple[str, ...] = RETURNS_TO_SCALE,
) -> tuple[ExperimentCase, ...]:
    """Return the deterministic Cartesian experiment matrix."""
    return tuple(
        ExperimentCase(profile, orientation, rts)
        for profile in profiles
        for orientation in orientations
        for rts in returns_to_scale
    )


def _all_role_data(n_dmus: int, n_periods: int) -> DynamicData:
    """Construct a deterministic management panel with all carry-over roles."""
    if n_dmus < 2:
        raise ValueError("n_dmus must be at least two")
    if n_periods < 2:
        raise ValueError("n_periods must be at least two")
    rows: list[dict[str, object]] = []
    for period in range(n_periods):
        progress = 1.0 + 0.025 * period
        for position in range(n_dmus):
            scale = 1.0 + position / max(n_dmus - 1, 1)
            management = 0.76 + 0.22 * ((position * 17 + period * 7) % 23) / 22
            rows.append(
                {
                    "dmu": f"D{position:05d}",
                    "period": period,
                    "labor": 70.0 * scale * (1.0 + 0.01 * period),
                    "capital": 95.0 * scale,
                    "regulated_input": 12.0 * scale,
                    "service": 120.0 * scale * management * progress,
                    "mandated_output": 9.0 * scale,
                    "capacity": 28.0 * scale * progress,
                    "backlog": 16.0 * scale / progress,
                    "inventory": 18.0 * scale * (0.9 + 0.2 * management),
                    "fixed_commitment": 11.0 * scale,
                }
            )
    return DynamicData.from_frame(
        pd.DataFrame(rows),
        spec=DynamicSBMSpec(
            production=PeriodProductionSpec(
                inputs=("labor", "capital"),
                outputs="service",
                nondiscretionary_inputs="regulated_input",
                nondiscretionary_outputs="mandated_output",
            ),
            carryovers=(
                CarryOverSpec("capacity", "good"),
                CarryOverSpec("backlog", "bad"),
                CarryOverSpec("inventory", "free"),
                CarryOverSpec("fixed_commitment", "fixed"),
            ),
        ),
        dmu="dmu",
        period="period",
    )


def _oracle_data() -> DynamicData:
    """Load the independently certified good/bad carry-over teaching case."""
    return DynamicData.from_frame(
        load_dataset("dynamic_capacity_backlog"),
        spec=DynamicSBMSpec(
            production=PeriodProductionSpec(inputs="resource", outputs="service"),
            carryovers=(
                CarryOverSpec("capacity", "good"),
                CarryOverSpec("backlog", "bad"),
            ),
        ),
        dmu="organization",
        period="period",
    )


def _scaled_data(data: DynamicData) -> DynamicData:
    """Apply valid heterogeneous unit scales spanning twenty-four orders."""
    exponents = (12, -12, 9, -9, 6, -6, 3, -3, 10)
    scales = {
        variable: 10.0 ** exponents[index]
        for index, variable in enumerate(data.variable_names)
    }
    rows: list[dict[str, object]] = []
    for period_index, period in enumerate(data.periods):
        for dmu_index, dmu_id in enumerate(data.dmu_ids):
            row: dict[str, object] = {"dmu": dmu_id, "period": period}
            for variable_index, variable in enumerate(data.variable_names):
                row[variable] = (
                    float(data.values[period_index, dmu_index, variable_index])
                    * scales[variable]
                )
            rows.append(row)
    return DynamicData.from_frame(
        pd.DataFrame(rows),
        spec=data.dynamic_spec,
        dmu="dmu",
        period="period",
        period_order=tuple(data.periods.tolist()),
    )


def make_profile_data(profile: str, n_dmus: int, n_periods: int) -> DynamicData:
    """Build one declared experiment profile."""
    if profile == "oracle":
        return _oracle_data()
    realistic = _all_role_data(n_dmus, n_periods)
    if profile == "realistic":
        return realistic
    if profile == "extreme":
        return _scaled_data(realistic)
    raise ValueError(f"unknown experiment profile: {profile!r}")


def _json_value(value: object) -> object:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return value
    if isinstance(value, (str, int, bool)):
        return value
    return str(value)


def _frame_snapshot(name: str, frame: pd.DataFrame) -> dict[str, object]:
    ignored = _IGNORED_COLUMNS.get(name, frozenset())
    columns = tuple(column for column in frame.columns if column not in ignored)
    keys = _FRAME_KEYS[name]
    missing_keys = set(keys).difference(columns)
    if missing_keys:
        raise AssertionError(f"{name} missing comparison keys: {sorted(missing_keys)}")
    numeric = tuple(
        column
        for column in columns
        if column not in keys
        and is_numeric_dtype(frame[column].dtype)
        and not is_bool_dtype(frame[column].dtype)
    )
    exact = tuple(
        column for column in columns if column not in keys and column not in numeric
    )
    positions = {column: index for index, column in enumerate(columns)}
    records = [
        [_json_value(value) for value in row]
        for row in frame.loc[:, columns].itertuples(index=False, name=None)
    ]
    records.sort(
        key=lambda record: tuple(
            (type(record[positions[key]]).__name__, str(record[positions[key]]))
            for key in keys
        )
    )
    return {
        "keys": keys,
        "columns": columns,
        "numeric": numeric,
        "exact": exact,
        "records": records,
    }


def fit_snapshot(
    case: ExperimentCase,
    *,
    presolve: bool,
    n_dmus: int,
    n_periods: int,
) -> dict[str, object]:
    """Fit one isolated A/B arm and return its governed result contract."""
    data = make_profile_data(case.profile, n_dmus, n_periods)
    started = time.perf_counter()
    result = DynamicSBM(
        orientation=case.orientation,
        returns_to_scale=case.returns_to_scale,
        score_variant="base",
        solver_options=SolverOptions(presolve=presolve),
    ).fit(data)
    elapsed = time.perf_counter() - started
    frames = {
        "summary": result.summary(),
        "diagnostics": result.diagnostics,
        "targets": result.targets,
        "peers": result.intensities,
        "slacks": result.slacks,
        "links": result.links,
        "components": result.components,
    }
    summary = frames["summary"]
    roles = tuple(sorted({item.kind.value for item in data.dynamic_spec.carryovers}))
    return {
        "case_id": case.case_id,
        "presolve": presolve,
        "elapsed_seconds": elapsed,
        "n_dmus": data.n_dmus,
        "n_periods": data.n_periods,
        "carryover_roles": roles,
        "optimal": int(summary["solver_status"].eq("optimal").sum()),
        "score_certified": int(summary["score_valid"].fillna(False).sum()),
        "target_certified": int(summary["target_valid"].fillna(False).sum()),
        "peer_certified": int(summary["peer_valid"].fillna(False).sum()),
        "dual_certified": int(summary["dual_valid"].fillna(False).sum()),
        "carryover_certified": int(summary["carryover_valid"].fillna(False).sum()),
        "frames": {
            name: _frame_snapshot(name, frame) for name, frame in frames.items()
        },
    }


def _records_by_key(snapshot: dict[str, object]) -> dict[tuple[object, ...], list]:
    columns = list(snapshot["columns"])
    positions = {column: index for index, column in enumerate(columns)}
    keys = list(snapshot["keys"])
    records = snapshot["records"]
    return {tuple(record[positions[key]] for key in keys): record for record in records}


def compare_snapshots(
    presolve_true: dict[str, object],
    presolve_false: dict[str, object],
    *,
    atol: float = DEFAULT_ATOL,
    rtol: float = DEFAULT_RTOL,
) -> dict[str, object]:
    """Compare all fitted tables and certificate fields in two A/B arms."""
    differences: list[str] = []
    table_metrics = {
        name: {
            "material_difference_count": 0,
            "row_keys_equal": True,
            "max_absolute_delta": 0.0,
            "max_relative_delta": 0.0,
        }
        for name in _FRAME_KEYS
    }
    score_columns = {
        "score",
        "efficiency",
        "distance",
        "optimization_efficiency",
        "free_adjusted_efficiency",
    }
    score_max_absolute_delta = 0.0
    target_max_absolute_delta = 0.0
    peer_max_absolute_delta = 0.0
    certificate_max_absolute_delta = 0.0
    max_absolute_delta = 0.0
    max_relative_delta = 0.0
    true_frames = presolve_true["frames"]
    false_frames = presolve_false["frames"]

    def record_difference(name: str, message: str) -> None:
        differences.append(message)
        table_metrics[name]["material_difference_count"] += 1

    for name in _FRAME_KEYS:
        left = true_frames[name]
        right = false_frames[name]
        for schema_field in ("keys", "columns", "numeric", "exact"):
            if left[schema_field] != right[schema_field]:
                record_difference(
                    name,
                    f"{name}: schema differs for {schema_field}",
                )
                continue
        columns = list(left["columns"])
        positions = {column: index for index, column in enumerate(columns)}
        left_records = _records_by_key(left)
        right_records = _records_by_key(right)
        left_keys = set(left_records)
        right_keys = set(right_records)
        if left_keys != right_keys:
            table_metrics[name]["row_keys_equal"] = False
            only_true = sorted(map(str, left_keys.difference(right_keys)))[:3]
            only_false = sorted(map(str, right_keys.difference(left_keys)))[:3]
            record_difference(
                name,
                f"{name}: row keys differ; presolve_true_only={only_true}, "
                f"presolve_false_only={only_false}",
            )
        for key in sorted(left_keys.intersection(right_keys), key=str):
            left_record = left_records[key]
            right_record = right_records[key]
            for column in left["exact"]:
                position = positions[column]
                if left_record[position] != right_record[position]:
                    record_difference(
                        name,
                        f"{name}{key!r}.{column}: "
                        f"{left_record[position]!r} != {right_record[position]!r}",
                    )
            for column in left["numeric"]:
                position = positions[column]
                left_value = left_record[position]
                right_value = right_record[position]
                if left_value is None or right_value is None:
                    if left_value != right_value:
                        record_difference(
                            name,
                            f"{name}{key!r}.{column}: "
                            f"{left_value!r} != {right_value!r}",
                        )
                    continue
                absolute_delta = abs(float(left_value) - float(right_value))
                scale = max(abs(float(left_value)), abs(float(right_value)))
                relative_delta = 0.0 if scale == 0.0 else absolute_delta / scale
                max_absolute_delta = max(max_absolute_delta, absolute_delta)
                max_relative_delta = max(max_relative_delta, relative_delta)
                table_metrics[name]["max_absolute_delta"] = max(
                    table_metrics[name]["max_absolute_delta"], absolute_delta
                )
                table_metrics[name]["max_relative_delta"] = max(
                    table_metrics[name]["max_relative_delta"], relative_delta
                )
                if name == "summary" and column in score_columns:
                    score_max_absolute_delta = max(
                        score_max_absolute_delta,
                        absolute_delta,
                    )
                if name == "targets" and column in {"target", "adjustment"}:
                    target_max_absolute_delta = max(
                        target_max_absolute_delta,
                        absolute_delta,
                    )
                if name == "peers" and column == "intensity":
                    peer_max_absolute_delta = max(
                        peer_max_absolute_delta,
                        absolute_delta,
                    )
                if name == "diagnostics":
                    certificate_max_absolute_delta = max(
                        certificate_max_absolute_delta,
                        absolute_delta,
                    )
                if not math.isclose(
                    float(left_value),
                    float(right_value),
                    abs_tol=atol,
                    rel_tol=rtol,
                ):
                    record_difference(
                        name,
                        f"{name}{key!r}.{column}: {left_value!r} != {right_value!r}",
                    )
    return {
        "equivalent": not differences,
        "difference_count": len(differences),
        "differences": differences[:50],
        "differences_truncated": len(differences) > 50,
        "max_absolute_delta": max_absolute_delta,
        "max_relative_delta": max_relative_delta,
        "score_max_absolute_delta": score_max_absolute_delta,
        "target_max_absolute_delta": target_max_absolute_delta,
        "peer_max_absolute_delta_on_shared_rows": peer_max_absolute_delta,
        "certificate_max_absolute_delta": certificate_max_absolute_delta,
        "table_metrics": table_metrics,
        "atol": atol,
        "rtol": rtol,
    }


def arm_completeness(arm: dict[str, object]) -> dict[str, object]:
    """Require every expected trajectory and publication certificate."""
    expected = int(arm["n_dmus"])
    required_counts = {
        "optimal": int(arm["optimal"]),
        "score_certified": int(arm["score_certified"]),
        "target_certified": int(arm["target_certified"]),
        "peer_certified": int(arm["peer_certified"]),
        "dual_certified": int(arm["dual_certified"]),
        "carryover_certified": int(arm["carryover_certified"]),
    }
    failures = {
        field: {"observed": observed, "expected": expected}
        for field, observed in required_counts.items()
        if observed != expected
    }
    return {
        "complete": not failures,
        "expected_trajectories": expected,
        "required_counts": required_counts,
        "failures": failures,
    }


def case_record(
    case: ExperimentCase,
    arm_true: dict[str, object],
    arm_false: dict[str, object],
    *,
    atol: float,
    rtol: float,
) -> dict[str, object]:
    """Evaluate one A/B pair without allowing identical failures to pass."""
    comparison = compare_snapshots(arm_true, arm_false, atol=atol, rtol=rtol)
    completeness_true = arm_completeness(arm_true)
    completeness_false = arm_completeness(arm_false)
    correctness_complete = bool(
        completeness_true["complete"] and completeness_false["complete"]
    )
    return {
        "case_id": case.case_id,
        "profile": case.profile,
        "orientation": case.orientation,
        "returns_to_scale": case.returns_to_scale,
        "carryover_roles": arm_true["carryover_roles"],
        "presolve_true": {
            key: arm_true[key]
            for key in (
                "elapsed_seconds",
                "wall_seconds",
                "peak_rss_bytes",
                "n_dmus",
                "n_periods",
                "optimal",
                "score_certified",
                "target_certified",
                "peer_certified",
                "dual_certified",
                "carryover_certified",
            )
        },
        "presolve_false": {
            key: arm_false[key]
            for key in (
                "elapsed_seconds",
                "wall_seconds",
                "peak_rss_bytes",
                "n_dmus",
                "n_periods",
                "optimal",
                "score_certified",
                "target_certified",
                "peer_certified",
                "dual_certified",
                "carryover_certified",
            )
        },
        "presolve_true_completeness": completeness_true,
        "presolve_false_completeness": completeness_false,
        "correctness_complete": correctness_complete,
        "comparison": comparison,
        "case_passed": correctness_complete and bool(comparison["equivalent"]),
    }


def experiment_outcome(
    records: list[dict[str, object]],
    *,
    source_integrity_verified: bool,
) -> dict[str, object]:
    """Resolve the fail-closed experiment outcome and conservative advice."""
    all_complete = all(record["correctness_complete"] for record in records)
    all_equivalent = all(record["comparison"]["equivalent"] for record in records)
    passed = source_integrity_verified and all_complete and all_equivalent
    if not source_integrity_verified:
        recommendation = "no_default_change_due_to_source_integrity_failure"
    elif not all_complete:
        recommendation = "no_default_change_due_to_incomplete_correctness_gates"
    elif not all_equivalent:
        recommendation = "no_default_change_due_to_observed_divergence"
    else:
        recommendation = "retain_existing_presolve_true_default_conservatively"
    return {
        "all_correctness_complete": all_complete,
        "all_equivalent": all_equivalent,
        "source_integrity_verified": source_integrity_verified,
        "experiment_passed": passed,
        "recommendation": recommendation,
    }


def _worker_command(
    case: ExperimentCase,
    *,
    presolve: bool,
    n_dmus: int,
    n_periods: int,
) -> list[str]:
    return [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker",
        "--profile",
        case.profile,
        "--orientation",
        case.orientation,
        "--returns-to-scale",
        case.returns_to_scale,
        "--presolve",
        "true" if presolve else "false",
        "--n-dmus",
        str(n_dmus),
        "--periods",
        str(n_periods),
    ]


def run_isolated_arm(
    case: ExperimentCase,
    *,
    presolve: bool,
    n_dmus: int,
    n_periods: int,
) -> dict[str, object]:
    """Run one arm in a fresh process and sample that process's peak RSS."""
    environment = os.environ.copy()
    environment.update(
        {
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "VECLIB_MAXIMUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
        }
    )
    command = _worker_command(
        case,
        presolve=presolve,
        n_dmus=n_dmus,
        n_periods=n_periods,
    )
    with tempfile.TemporaryDirectory(prefix="deapack-dynamic-sbm-presolve-") as tmp:
        stdout_path = Path(tmp) / "stdout.json"
        stderr_path = Path(tmp) / "stderr.log"
        started = time.perf_counter()
        with (
            stdout_path.open("w", encoding="utf-8") as stdout_file,
            stderr_path.open("w", encoding="utf-8") as stderr_file,
        ):
            process = subprocess.Popen(
                command,
                stdout=stdout_file,
                stderr=stderr_file,
                text=True,
                env=environment,
            )
            monitored = psutil.Process(process.pid)
            peak_rss = 0
            while True:
                with contextlib.suppress(psutil.AccessDenied, psutil.NoSuchProcess):
                    peak_rss = max(peak_rss, monitored.memory_info().rss)
                if process.poll() is not None:
                    break
                time.sleep(0.01)
        wall = time.perf_counter() - started
        stderr = stderr_path.read_text(encoding="utf-8")
        if process.returncode != 0:
            raise RuntimeError(
                f"experiment worker failed ({process.returncode}): "
                f"{' '.join(command)}\n{stderr}"
            )
        output = json.loads(stdout_path.read_text(encoding="utf-8"))
    output["wall_seconds"] = wall
    output["peak_rss_bytes"] = peak_rss
    return output


def run_experiment(
    cases: tuple[ExperimentCase, ...],
    *,
    n_dmus: int,
    n_periods: int,
    atol: float,
    rtol: float,
) -> dict[str, object]:
    """Run the governed matrix and return its machine-readable record."""
    source_tree = _source_tree_ledger()
    records: list[dict[str, object]] = []
    for case in cases:
        arm_true = run_isolated_arm(
            case,
            presolve=True,
            n_dmus=n_dmus,
            n_periods=n_periods,
        )
        arm_false = run_isolated_arm(
            case,
            presolve=False,
            n_dmus=n_dmus,
            n_periods=n_periods,
        )
        records.append(
            case_record(
                case,
                arm_true,
                arm_false,
                atol=atol,
                rtol=rtol,
            )
        )
    _verify_unchanged_source_tree(source_tree)
    source_integrity_verified = bool(
        source_tree["runtime_import"]["verified"]
        and source_tree["verified_unchanged_after_run"]
    )
    outcome = experiment_outcome(
        records,
        source_integrity_verified=source_integrity_verified,
    )
    return {
        "schema_version": "1.0",
        "experiment_id": "dynamic-sbm-highs-presolve-ab",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "psutil": psutil.__version__,
            "deapack": metadata.version("deapack"),
            "solver_threads": 1,
        },
        "matrix": {
            "profiles": sorted({case.profile for case in cases}),
            "orientations": sorted({case.orientation for case in cases}),
            "returns_to_scale": sorted({case.returns_to_scale for case in cases}),
            "all_supported_carryover_roles": ALL_CARRYOVER_ROLES,
            "n_dmus_for_non_oracle_profiles": n_dmus,
            "n_periods_for_non_oracle_profiles": n_periods,
            "case_count": len(cases),
            "atol": atol,
            "rtol": rtol,
        },
        "performance_evidence": {
            "classification": "exploratory_order_sensitive_single_pass",
            "arm_order": ("presolve_true", "presolve_false"),
            "repetitions_per_arm": 1,
            "interpretation": (
                "elapsed time and sampled RSS are observations only; they do not "
                "support a speed claim or a default switch"
            ),
        },
        "source_tree": source_tree,
        **outcome,
        "default_behavior_changed": False,
        "cases": records,
    }


def _worker_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--profile", choices=PROFILES)
    parser.add_argument("--orientation", choices=ORIENTATIONS)
    parser.add_argument("--returns-to-scale", choices=RETURNS_TO_SCALE)
    parser.add_argument("--presolve", choices=("true", "false"))
    parser.add_argument("--n-dmus", type=int, default=12)
    parser.add_argument("--periods", type=int, default=3)
    return parser


def _main_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Governed Dynamic-SBM HiGHS presolve A/B experiment"
    )
    parser.add_argument("--profiles", nargs="+", choices=PROFILES, default=PROFILES)
    parser.add_argument(
        "--orientations",
        nargs="+",
        choices=ORIENTATIONS,
        default=ORIENTATIONS,
    )
    parser.add_argument(
        "--returns-to-scale",
        nargs="+",
        choices=RETURNS_TO_SCALE,
        default=RETURNS_TO_SCALE,
    )
    parser.add_argument("--n-dmus", type=int, default=12)
    parser.add_argument("--periods", type=int, default=3)
    parser.add_argument("--atol", type=float, default=DEFAULT_ATOL)
    parser.add_argument("--rtol", type=float, default=DEFAULT_RTOL)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def _print_text(record: dict[str, object]) -> None:
    for case in record["cases"]:
        arm_true = case["presolve_true"]
        arm_false = case["presolve_false"]
        comparison = case["comparison"]
        print(
            f"case={case['case_id']} equivalent={comparison['equivalent']} "
            f"complete={case['correctness_complete']} "
            f"presolve_true_elapsed={arm_true['elapsed_seconds']:.3f}s "
            f"presolve_false_elapsed={arm_false['elapsed_seconds']:.3f}s "
            f"presolve_true_peak_rss={arm_true['peak_rss_bytes'] / 1048576:.1f}MiB "
            f"presolve_false_peak_rss={arm_false['peak_rss_bytes'] / 1048576:.1f}MiB "
            f"score_max_abs_delta={comparison['score_max_absolute_delta']:.3e} "
            f"max_abs_delta={comparison['max_absolute_delta']:.3e} "
            f"max_rel_delta={comparison['max_relative_delta']:.3e} "
            f"differences={comparison['difference_count']}"
        )
        for difference in comparison["differences"][:3]:
            print(f"  difference: {difference}")
    print(
        f"experiment_passed={record['experiment_passed']} "
        f"all_correctness_complete={record['all_correctness_complete']} "
        f"all_equivalent={record['all_equivalent']} "
        f"source_integrity_verified={record['source_integrity_verified']} "
        f"default_behavior_changed={record['default_behavior_changed']} "
        f"recommendation={record['recommendation']}"
    )


def main() -> None:
    if "--worker" in sys.argv[1:]:
        args = _worker_parser().parse_args()
        if not all(
            (args.profile, args.orientation, args.returns_to_scale, args.presolve)
        ):
            raise SystemExit("worker mode requires a complete experiment case")
        case = ExperimentCase(
            args.profile,
            args.orientation,
            args.returns_to_scale,
        )
        print(
            json.dumps(
                fit_snapshot(
                    case,
                    presolve=args.presolve == "true",
                    n_dmus=args.n_dmus,
                    n_periods=args.periods,
                ),
                separators=(",", ":"),
            )
        )
        return

    args = _main_parser().parse_args()
    if args.n_dmus < 2 or args.periods < 2:
        raise SystemExit("n_dmus and periods must both be at least two")
    if args.atol < 0 or args.rtol < 0:
        raise SystemExit("comparison tolerances cannot be negative")
    cases = experiment_cases(
        profiles=tuple(dict.fromkeys(args.profiles)),
        orientations=tuple(dict.fromkeys(args.orientations)),
        returns_to_scale=tuple(dict.fromkeys(args.returns_to_scale)),
    )
    record = run_experiment(
        cases,
        n_dmus=args.n_dmus,
        n_periods=args.periods,
        atol=args.atol,
        rtol=args.rtol,
    )
    if args.format == "json":
        print(json.dumps(record, indent=2, sort_keys=True))
    else:
        _print_text(record)
    if not record["experiment_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
