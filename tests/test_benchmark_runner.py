from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from types import ModuleType

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "benchmarks" / "cases.json"
REPORT_SCHEMA = ROOT / "benchmarks" / "report-schema.json"


def _runner() -> ModuleType:
    name = "deapack_benchmark_runner_test"
    specification = importlib.util.spec_from_file_location(
        name,
        ROOT / "scripts" / "run_benchmarks.py",
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def _registry_records() -> tuple[dict[str, object], ...]:
    records = []
    for path in (ROOT / "specs" / "registry" / "methods").rglob("*.json"):
        records.append(json.loads(path.read_text(encoding="utf-8")))
    return tuple(records)


def _report_directory(tmp_path: Path) -> Path:
    directory = tmp_path / "report"
    (directory / "logs").mkdir(parents=True)
    (directory / "runtime").mkdir()
    return directory


def _probe_case(mode: str, *, blocking: bool = True, timeout: int = 10):
    task = {"args": ("--mode", mode), "timeout_seconds": timeout}
    return {
        "id": f"probe-{mode}",
        "script": "tests/fixtures/benchmark_probe.py",
        "blocking": blocking,
        "smoke": task,
        "release": task,
    }


def test_manifest_freezes_every_script_and_public_release_boundary() -> None:
    runner = _runner()
    manifest = runner.load_manifest(MANIFEST)
    cases = manifest["cases"]
    scripts = {case["script"] for case in cases}
    available = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "benchmarks").glob("benchmark_*.py")
    }
    assert scripts == available
    assert len(scripts) == 40
    # Local RTS/scale elasticity, ordinary/eligibility radial, and
    # ordinary/eligibility environmental foundations are separate runs;
    # declared-calibration EBM has its own blocking structural benchmark.
    assert len(cases) == 43
    assert len({case["script"] for case in cases if case["blocking"]}) == 37
    assert {case["script"] for case in cases if not case["blocking"]} == {
        "benchmarks/benchmark_mpss.py",
        "benchmarks/benchmark_physical_capacity.py",
        "benchmarks/benchmark_super_efficiency.py",
    }
    assert all(case["smoke"]["args"] for case in cases)
    assert all(case["release"]["args"] for case in cases)
    assert all(case["smoke"]["timeout_seconds"] > 0 for case in cases)
    assert all(case["release"]["timeout_seconds"] > 0 for case in cases)


def test_blocking_cases_cover_every_implemented_public_registry_locator() -> None:
    runner = _runner()
    cases = runner.load_manifest(MANIFEST)["cases"]
    blocking_scripts = {case["script"] for case in cases if case["blocking"]}
    public_scripts: set[str] = set()
    prototype_only_scripts: set[str] = set()
    by_script: dict[str, list[dict[str, object]]] = {}
    for record in _registry_records():
        for locator in record.get("validation", {}).get("benchmarks", []):
            by_script.setdefault(locator, []).append(record)
    for script, records in by_script.items():
        public = any(
            record["status"]["implementation"] == "implemented"
            and record["status"]["api"] == "public"
            for record in records
        )
        if public:
            public_scripts.add(script)
        else:
            assert all(
                record["status"]["implementation"] == "prototype"
                and record["status"]["api"] == "none"
                for record in records
            )
            prototype_only_scripts.add(script)
    assert blocking_scripts == public_scripts
    assert prototype_only_scripts == {
        "benchmarks/benchmark_mpss.py",
        "benchmarks/benchmark_physical_capacity.py",
        "benchmarks/benchmark_super_efficiency.py",
    }


def test_manifest_rejects_unknown_case_selection() -> None:
    runner = _runner()
    with pytest.raises(runner.ManifestError, match="unknown benchmark case IDs"):
        runner.run_suite(
            manifest_path=MANIFEST,
            tier="smoke",
            output_root=ROOT / "benchmark-results-test-never-created",
            selected_ids=("not-a-case",),
        )


def test_manifest_rejects_duplicate_json_object_keys(tmp_path: Path) -> None:
    runner = _runner()
    manifest = tmp_path / "duplicate.json"
    manifest.write_text(
        '{"schema_version": "1.0", "schema_version": "1.0"}',
        encoding="utf-8",
    )
    with pytest.raises(runner.ManifestError, match="duplicate JSON object key"):
        runner.load_manifest(manifest)


def test_source_tree_ledger_covers_runtime_and_governance_inputs() -> None:
    runner = _runner()
    ledger = runner._source_tree_ledger()
    paths = [record["path"] for record in ledger["files"]]
    assert paths == sorted(paths)
    assert len(paths) == len(set(paths)) == ledger["file_count"]
    assert ledger["total_bytes"] == sum(record["bytes"] for record in ledger["files"])
    assert "src/deapack/__init__.py" in paths
    assert "pyproject.toml" in paths
    assert "benchmarks/cases.json" in paths
    assert "benchmarks/report-schema.json" in paths
    assert "scripts/run_benchmarks.py" in paths
    assert "specs/registry/registry-manifest.json" in paths
    assert {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "benchmarks").glob("benchmark_*.py")
    }.issubset(paths)
    assert not any(
        "__pycache__" in Path(path).parts
        or path.startswith("build/")
        or path.startswith("benchmark-results/")
        or path.startswith(".git/")
        for path in paths
    )
    runner.verify_source_tree_ledger(ledger)


def test_source_tree_aggregate_is_order_independent_utf8_and_length_prefixed(
    tmp_path: Path,
) -> None:
    runner = _runner()
    (tmp_path / "src" / "deapack").mkdir(parents=True)
    (tmp_path / "src" / "deapack" / "empty.py").write_bytes(b"")
    (tmp_path / "src" / "deapack" / "模型.py").write_text(
        "VALUE = 1\n", encoding="utf-8"
    )
    paths = ("src/deapack/模型.py", "src/deapack/empty.py")
    forward = runner._source_tree_ledger(paths, repository_root=tmp_path)
    reverse = runner._source_tree_ledger(paths[::-1], repository_root=tmp_path)
    assert forward["files"] == reverse["files"]
    assert forward["sha256"] == reverse["sha256"]
    assert forward["files"][0]["bytes"] == 0

    other_root = tmp_path / "different" / "absolute" / "root"
    (other_root / "src" / "deapack").mkdir(parents=True)
    (other_root / "src" / "deapack" / "empty.py").write_bytes(b"")
    (other_root / "src" / "deapack" / "模型.py").write_text(
        "VALUE = 1\n", encoding="utf-8"
    )
    relocated = runner._source_tree_ledger(paths, repository_root=other_root)
    assert relocated["sha256"] == forward["sha256"]

    digest = hashlib.sha256()
    digest.update(b"deapack-source-tree-sha256-v1\0")
    for record in forward["files"]:
        encoded_path = record["path"].encode("utf-8")
        digest.update(len(encoded_path).to_bytes(8, "big"))
        digest.update(encoded_path)
        digest.update(record["bytes"].to_bytes(8, "big"))
        digest.update(bytes.fromhex(record["sha256"]))
    assert forward["sha256"] == digest.hexdigest()
    runner.verify_source_tree_ledger(forward, repository_root=tmp_path)


@pytest.mark.parametrize(
    "paths, message",
    (
        (("src/deapack/a.py", "src/deapack/a.py"), "duplicate"),
        (("src/deapack/a.py", "src/DEAPACK/a.py"), "case-insensitive"),
        (("../outside.py",), "escapes"),
        (("/absolute.py",), "repository-relative"),
        (("src\\deapack\\a.py",), "POSIX separators"),
        (("src/deapack/CON.py",), "reserved platform name"),
    ),
)
def test_source_tree_ledger_rejects_ambiguous_or_escaping_paths(
    tmp_path: Path,
    paths: tuple[str, ...],
    message: str,
) -> None:
    runner = _runner()
    with pytest.raises(runner.SourceSnapshotError, match=message):
        runner._source_tree_ledger(paths, repository_root=tmp_path)


def test_source_tree_ledger_rejects_symlinks_and_nonregular_files(
    tmp_path: Path,
) -> None:
    runner = _runner()
    target = tmp_path / "target.py"
    target.write_text("VALUE = 1\n", encoding="utf-8")
    link = tmp_path / "link.py"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symbolic links are unavailable in this environment")
    with pytest.raises(runner.SourceSnapshotError, match="symbolic link"):
        runner._source_tree_ledger(("link.py",), repository_root=tmp_path)

    directory = tmp_path / "directory.py"
    directory.mkdir()
    with pytest.raises(runner.SourceSnapshotError, match="regular file"):
        runner._source_tree_ledger(("directory.py",), repository_root=tmp_path)

    if hasattr(os, "mkfifo"):
        fifo = tmp_path / "source.py"
        os.mkfifo(fifo)
        with pytest.raises(runner.SourceSnapshotError, match="regular file"):
            runner._source_tree_ledger(("source.py",), repository_root=tmp_path)


def test_source_tree_verifier_detects_changed_bytes(tmp_path: Path) -> None:
    runner = _runner()
    source = tmp_path / "source.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    ledger = runner._source_tree_ledger(("source.py",), repository_root=tmp_path)
    source.write_text("VALUE = 2\n", encoding="utf-8")
    with pytest.raises(runner.SourceSnapshotError, match="does not match"):
        runner.verify_source_tree_ledger(ledger, repository_root=tmp_path)


def test_case_runner_retains_logs_hashes_resources_and_exit_status(
    tmp_path: Path,
) -> None:
    runner = _runner()
    psutil = runner._load_psutil()
    directory = _report_directory(tmp_path)
    result = runner.run_case(
        _probe_case("pass"),
        tier="smoke",
        report_directory=directory,
        psutil=psutil,
        sample_interval_seconds=0.01,
    )
    assert result["status"] == "passed"
    assert result["return_code"] == 0
    assert result["wall_seconds"] > 0
    assert result["peak_rss_bytes"] > 0
    assert result["script_sha256"] == runner._sha256(
        ROOT / "tests" / "fixtures" / "benchmark_probe.py"
    )
    assert result["stdout"]["sha256"] == runner._sha256(
        directory / result["stdout"]["path"]
    )
    assert result["stderr"]["sha256"] == runner._sha256(
        directory / result["stderr"]["path"]
    )
    assert "probe stdout mode=pass" in (directory / result["stdout"]["path"]).read_text(
        encoding="utf-8"
    )
    assert "probe stderr mode=pass" in (directory / result["stderr"]["path"]).read_text(
        encoding="utf-8"
    )


def test_case_runner_records_failure_without_losing_raw_logs(tmp_path: Path) -> None:
    runner = _runner()
    directory = _report_directory(tmp_path)
    result = runner.run_case(
        _probe_case("fail", blocking=False),
        tier="smoke",
        report_directory=directory,
        psutil=runner._load_psutil(),
        sample_interval_seconds=0.01,
    )
    assert result["status"] == "failed"
    assert result["return_code"] == 7
    summary = runner._summary((result,))
    assert summary["blocking_failures"] == 0
    assert summary["informational_failures"] == 1


def test_case_runner_enforces_timeout_and_terminates_process(tmp_path: Path) -> None:
    runner = _runner()
    directory = _report_directory(tmp_path)
    result = runner.run_case(
        _probe_case("sleep", timeout=1),
        tier="smoke",
        report_directory=directory,
        psutil=runner._load_psutil(),
        sample_interval_seconds=0.01,
    )
    assert result["status"] == "timeout"
    assert result["wall_seconds"] < 4.0
    assert result["peak_rss_bytes"] > 0


def test_selected_smoke_suite_writes_schema_valid_json_markdown_and_logs(
    tmp_path: Path,
) -> None:
    runner = _runner()
    report, directory = runner.run_suite(
        manifest_path=MANIFEST,
        tier="smoke",
        output_root=tmp_path,
        selected_ids=("radial",),
        sample_interval_seconds=0.01,
    )
    loaded = json.loads((directory / "report.json").read_text(encoding="utf-8"))
    schema = json.loads(REPORT_SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(loaded)
    assert loaded == report
    assert report["suite_status"] == "passed"
    assert report["summary"] == {
        "total": 1,
        "passed": 1,
        "failed": 0,
        "timed_out": 0,
        "runner_errors": 0,
        "blocking_failures": 0,
        "informational_failures": 0,
    }
    assert report["manifest"]["sha256"] == runner._sha256(MANIFEST)
    source_tree = report["source_tree"]
    assert source_tree["verified_unchanged_after_run"] is True
    assert source_tree["source_changed_during_run"] is False
    assert source_tree["observed_after_run_sha256"] == source_tree["sha256"]
    assert source_tree["runtime_import"] == {
        "expected_package_root": "src/deapack",
        "resolved_init_path": "src/deapack/__init__.py",
        "verified": True,
        "error": None,
    }
    runner.verify_source_tree_ledger(source_tree)
    assert set(report["environment"]["environment"]).issubset(runner._ENVIRONMENT_KEYS)
    assert report["cases"][0]["peak_rss_bytes"] > 0
    assert report["cases"][0]["script_sha256"] == runner._sha256(
        ROOT / "benchmarks" / "benchmark_radial.py"
    )
    markdown = (directory / "report.md").read_text(encoding="utf-8")
    assert "Absolute timings are observations" in markdown
    assert "## Source tree" in markdown
    assert source_tree["sha256"] in markdown
    assert "`src/deapack/__init__.py`" in markdown
    assert "`radial`" in markdown
    assert report["cases"][0]["script_sha256"] in markdown
    assert (directory / report["cases"][0]["stdout"]["path"]).is_file()

    legacy = copy.deepcopy(loaded)
    legacy["schema_version"] = "1.0"
    del legacy["source_tree"]
    jsonschema.Draft202012Validator(schema).validate(legacy)

    version_1_1_without_source = copy.deepcopy(loaded)
    del version_1_1_without_source["source_tree"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(version_1_1_without_source)

    version_1_0_with_source = copy.deepcopy(loaded)
    version_1_0_with_source["schema_version"] = "1.0"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(version_1_0_with_source)


def test_source_change_during_run_is_explicit_and_fails_suite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _runner()
    original = runner._source_tree_ledger
    default_calls = 0

    def changing_ledger(relative_paths=None, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal default_calls
        ledger = original(relative_paths, **kwargs)
        if relative_paths is None:
            default_calls += 1
            if default_calls == 2:
                ledger["sha256"] = "f" * 64
        return ledger

    monkeypatch.setattr(runner, "_source_tree_ledger", changing_ledger)
    report, _directory = runner.run_suite(
        manifest_path=MANIFEST,
        tier="smoke",
        output_root=tmp_path,
        selected_ids=("radial",),
        sample_interval_seconds=0.01,
    )
    assert report["suite_status"] == "configuration_error"
    assert report["source_tree"]["source_changed_during_run"] is True
    assert report["source_tree"]["verified_unchanged_after_run"] is False
    assert any(
        error.startswith("source_changed_during_run:")
        for error in report["configuration_errors"]
    )


def test_runtime_import_mismatch_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _runner()
    monkeypatch.setattr(
        runner,
        "_runtime_import_probe",
        lambda _runtime: {
            "expected_package_root": "src/deapack",
            "resolved_init_path": None,
            "verified": False,
            "error": "outside repository",
        },
    )
    report, _directory = runner.run_suite(
        manifest_path=MANIFEST,
        tier="smoke",
        output_root=tmp_path,
        selected_ids=("radial",),
    )
    assert report["suite_status"] == "configuration_error"
    assert report["cases"] == []
    assert report["source_tree"]["runtime_import"]["verified"] is False
    assert any(
        error.startswith("runtime_import_mismatch:")
        for error in report["configuration_errors"]
    )


def test_require_clean_writes_configuration_error_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _runner()
    monkeypatch.setattr(
        runner,
        "_git_fingerprint",
        lambda: {
            "available": True,
            "revision": "0" * 40,
            "branch": "test",
            "dirty": True,
            "status_entry_count": 1,
        },
    )
    report, directory = runner.run_suite(
        manifest_path=MANIFEST,
        tier="smoke",
        output_root=tmp_path,
        selected_ids=("radial",),
        require_clean=True,
    )
    assert report["suite_status"] == "configuration_error"
    assert report["cases"] == []
    assert report["configuration_errors"]
    assert (directory / "report.json").is_file()
    assert (directory / "report.md").is_file()
