from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_ROOT = REPOSITORY_ROOT / "benchmarks"
CHEN_PATH = BENCHMARK_ROOT / "benchmark_network_additive.py"
COOK_PATH = BENCHMARK_ROOT / "benchmark_network_general_additive.py"

if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))


def _load_module(name: str, path: Path):
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


chen = _load_module("benchmark_network_additive", CHEN_PATH)
cook = _load_module("benchmark_network_general_additive", COOK_PATH)


def test_additive_benchmarks_have_direct_registry_locators() -> None:
    records = (
        (
            "network.additive.chen_etal_2009.json",
            "benchmarks/benchmark_network_additive.py",
        ),
        (
            "network.additive.cook_zhu_bi_yang_2010.json",
            "benchmarks/benchmark_network_general_additive.py",
        ),
    )
    root = REPOSITORY_ROOT / "specs" / "registry" / "methods" / "network"
    for filename, locator in records:
        with (root / filename).open(encoding="utf-8") as stream:
            record = json.load(stream)
        assert record["validation"]["benchmarks"] == [locator]


@pytest.mark.parametrize(
    ("decomposition", "projection", "secondary_per_dmu"),
    [
        ("none", "none", 0),
        ("maximize_stage_1", "source", 1),
        ("both_priorities", "source", 2),
    ],
)
def test_chen_benchmark_enforces_certificate_and_solve_graph(
    decomposition: str,
    projection: str,
    secondary_per_dmu: int,
) -> None:
    observation = chen.run_case(
        4,
        decomposition=decomposition,
        projection=projection,
    )

    assert observation.compile_calls == 1
    assert observation.primary_solves == 4
    assert observation.secondary_solves == secondary_per_dmu * 4
    assert observation.projection_fallback_solves == 0
    assert observation.solver_calls == 4 + secondary_per_dmu * 4
    assert observation.max_lp_violation <= 1.0e-7
    assert observation.max_raw_economic_violation <= 1.0e-7
    assert observation.max_published_economic_violation <= 1.0e-7
    if projection == "source":
        assert observation.max_target_violation <= 1.0e-7
        assert observation.max_peer_violation <= 1.0e-7


def test_cook_benchmark_enforces_certificate_and_solve_graph() -> None:
    observation = cook.run_case(4)

    assert observation.compile_calls == 1
    assert observation.primary_solves == 4
    assert observation.secondary_solves == 0
    assert observation.projection_fallback_solves == 0
    assert observation.solver_calls == 4
    assert observation.max_lp_violation <= 1.0e-7
    assert observation.max_raw_economic_violation <= 1.0e-7
    assert observation.max_published_economic_violation <= 1.0e-7
    assert observation.max_process_constraint_violation <= 1.0e-7
    assert observation.max_link_balance_violation <= 1.0e-7


@pytest.mark.parametrize("family", ["chen", "cook"])
def test_benchmarks_fail_closed_when_certificate_field_is_missing(
    family: str,
) -> None:
    if family == "chen":
        result, observation = chen._fit_with_counts(
            3,
            returns_to_scale="crs",
            decomposition="both_priorities",
            projection="source",
        )
        validate = lambda candidate: chen._validate_result(  # noqa: E731
            candidate,
            observation,
            n_dmus=3,
            decomposition="both_priorities",
            projection="source",
        )
    else:
        data = cook.make_data(3)
        result, observation = cook._fit_with_counts(data)
        validate = lambda candidate: cook._validate_result(  # noqa: E731
            candidate,
            observation,
            n_dmus=3,
        )
    corrupted = replace(
        result,
        diagnostics=result.diagnostics.drop(
            columns=["published_economic_postsolve_certified"]
        ),
    )

    with pytest.raises(AssertionError, match="diagnostics is missing required fields"):
        validate(corrupted)


@pytest.mark.parametrize("family", ["chen", "cook"])
def test_benchmarks_reject_missing_execution_count(family: str) -> None:
    if family == "chen":
        result, observation = chen._fit_with_counts(
            3,
            returns_to_scale="crs",
            decomposition="none",
            projection="none",
        )
        validate = lambda candidate: chen._validate_result(  # noqa: E731
            candidate,
            observation,
            n_dmus=3,
            decomposition="none",
            projection="none",
        )
    else:
        result, observation = cook._fit_with_counts(cook.make_data(3))
        validate = lambda candidate: cook._validate_result(  # noqa: E731
            candidate,
            observation,
            n_dmus=3,
        )
    metadata = dict(result.metadata)
    metadata.pop("additional_solver_calls")
    corrupted = replace(result, metadata=metadata)

    with pytest.raises(AssertionError, match="metadata is missing required fields"):
        validate(corrupted)


def test_additive_benchmark_clis_cover_both_trust_contracts() -> None:
    chen_completed = subprocess.run(
        [
            sys.executable,
            str(CHEN_PATH),
            "--n-dmus",
            "4",
            "--decomposition",
            "both_priorities",
            "--projection",
            "source",
        ],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "score_certified=4/4" in chen_completed.stdout
    assert "process_certified=4/4" in chen_completed.stdout
    assert "target_certified=4/4" in chen_completed.stdout
    assert "peer_certified=4/4" in chen_completed.stdout
    assert "total_solves=12 additional_solves=0" in chen_completed.stdout

    cook_completed = subprocess.run(
        [sys.executable, str(COOK_PATH), "--n-dmus", "4"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "certified=4/4" in cook_completed.stdout
    assert "primary_solves=4" in cook_completed.stdout
    assert "total_solves=4 additional_solves=0" in cook_completed.stdout
