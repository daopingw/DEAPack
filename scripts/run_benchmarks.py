#!/usr/bin/env python3
"""Run DEAPack's frozen benchmark suite and write release evidence.

The runner deliberately launches each case in a separate process and retains
its raw logs.  It measures the complete public workload rather than importing
benchmark internals into the orchestration process.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import re
import shlex
import signal
import stat
import subprocess
import sys
import time
import unicodedata
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPOSITORY_ROOT / "benchmarks" / "cases.json"
DEFAULT_OUTPUT_ROOT = REPOSITORY_ROOT / "benchmark-results"
REPORT_SCHEMA_VERSION = "1.1"
MANIFEST_SCHEMA_VERSION = "1.0"
SOURCE_TREE_FORMAT_VERSION = "1.0"
SOURCE_TREE_AGGREGATE_FORMAT = "deapack-source-tree-sha256-v1"
_CASE_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_WINDOWS_RESERVED_PATH_CHARACTERS = frozenset('<>:"|?*')
_WINDOWS_RESERVED_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{number}" for number in range(1, 10)}
    | {f"LPT{number}" for number in range(1, 10)}
)
_SOURCE_TREE_EXCLUDED_PARTS = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        "_build",
        "benchmark-results",
        "build",
        "dist",
    }
)
_SOURCE_TREE_EXCLUDED_NAMES = frozenset({".DS_Store"})
_SOURCE_TREE_EXPLICIT_FILES = (
    "pyproject.toml",
    "MANIFEST.in",
    "benchmarks/cases.json",
    "benchmarks/report-schema.json",
    "scripts/run_benchmarks.py",
)
_SOURCE_TREE_OPTIONAL_LOCK_FILES = (
    "constraints.txt",
    "Pipfile",
    "Pipfile.lock",
    "pdm.lock",
    "poetry.lock",
    "requirements-dev.txt",
    "requirements.txt",
    "uv.lock",
)
_SOURCE_TREE_SCOPE = {
    "included": (
        "all regular non-cache files under src/deapack",
        "pyproject.toml, MANIFEST.in, and supported root lock metadata when present",
        "benchmarks/cases.json, benchmarks/report-schema.json, and all "
        "benchmark_*.py scripts",
        "scripts/run_benchmarks.py",
        "all JSON registry records and schemas under specs/registry",
    ),
    "excluded": (
        ".git metadata",
        "build, dist, _build, and benchmark-results trees",
        "Python and tool caches",
        "generated reports and raw benchmark logs",
        "documentation prose, tests, and unrelated specification assets",
    ),
}
_ENVIRONMENT_KEYS = (
    "CI",
    "GITHUB_ACTIONS",
    "GITHUB_RUN_ID",
    "GITHUB_SHA",
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "PYTHONHASHSEED",
)
_CONTROLLED_ENVIRONMENT = {
    "MPLBACKEND": "Agg",
    "MPL_IGNORE_SYSTEM_FONTS": "1",
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "PYTHONHASHSEED": "0",
}


class ManifestError(ValueError):
    """Raised when the frozen benchmark manifest is malformed."""


class SourceSnapshotError(ValueError):
    """Raised when benchmark source evidence cannot be frozen safely."""


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build a JSON object while refusing ambiguous duplicate member names."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ManifestError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_source_path(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise SourceSnapshotError("source ledger paths must be non-empty strings")
    if "\\" in value:
        raise SourceSnapshotError(
            f"source ledger path must use POSIX separators: {value!r}"
        )
    if unicodedata.normalize("NFC", value) != value:
        raise SourceSnapshotError(
            f"source ledger path must use Unicode NFC normalization: {value!r}"
        )
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value:
        raise SourceSnapshotError(
            f"source ledger path is not canonical repository-relative POSIX: {value!r}"
        )
    for part in path.parts:
        if part in {"", ".", ".."}:
            raise SourceSnapshotError(f"source ledger path escapes its root: {value!r}")
        if part[-1:] in {" ", "."} or any(
            character in _WINDOWS_RESERVED_PATH_CHARACTERS or ord(character) < 32
            for character in part
        ):
            raise SourceSnapshotError(
                "source ledger path is not portable across supported systems: "
                f"{value!r}"
            )
        stem = part.split(".", maxsplit=1)[0].upper()
        if stem in _WINDOWS_RESERVED_NAMES:
            raise SourceSnapshotError(
                f"source ledger path uses a reserved platform name: {value!r}"
            )
    return value


def _discover_tree_files(
    root: Path,
    relative_root: str,
    *,
    suffix: str | None = None,
) -> list[str]:
    base = root / relative_root
    if not base.is_dir() or base.is_symlink():
        raise SourceSnapshotError(
            f"source ledger tree must be a real directory: {relative_root!r}"
        )
    discovered: list[str] = []
    for candidate in base.rglob("*"):
        relative = candidate.relative_to(root)
        if (
            _SOURCE_TREE_EXCLUDED_PARTS.intersection(relative.parts)
            or candidate.name in _SOURCE_TREE_EXCLUDED_NAMES
        ):
            continue
        if candidate.is_symlink():
            raise SourceSnapshotError(
                f"source ledger scope contains a symbolic link: {relative.as_posix()!r}"
            )
        information = candidate.lstat()
        if stat.S_ISDIR(information.st_mode):
            continue
        if not stat.S_ISREG(information.st_mode):
            raise SourceSnapshotError(
                "source ledger scope contains a non-regular file: "
                f"{relative.as_posix()!r}"
            )
        if suffix is None or candidate.suffix == suffix:
            discovered.append(relative.as_posix())
    return discovered


def _discover_source_paths(root: Path = REPOSITORY_ROOT) -> list[str]:
    paths = list(_SOURCE_TREE_EXPLICIT_FILES)
    paths.extend(
        name for name in _SOURCE_TREE_OPTIONAL_LOCK_FILES if (root / name).exists()
    )
    paths.extend(_discover_tree_files(root, "src/deapack"))
    paths.extend(_discover_tree_files(root, "specs/registry", suffix=".json"))
    paths.extend(
        path.relative_to(root).as_posix()
        for path in (root / "benchmarks").glob("benchmark_*.py")
    )
    return paths


def _source_file_record(root: Path, relative_path: str) -> dict[str, Any]:
    candidate = root
    parts = PurePosixPath(relative_path).parts
    for position, part in enumerate(parts):
        candidate /= part
        try:
            information = candidate.lstat()
        except OSError as error:
            raise SourceSnapshotError(
                f"cannot inspect source ledger path {relative_path!r}: {error}"
            ) from error
        if stat.S_ISLNK(information.st_mode):
            raise SourceSnapshotError(
                f"source ledger path traverses a symbolic link: {relative_path!r}"
            )
        final = position == len(parts) - 1
        if not final and not stat.S_ISDIR(information.st_mode):
            raise SourceSnapshotError(
                f"source ledger parent is not a directory: {relative_path!r}"
            )
        if final and not stat.S_ISREG(information.st_mode):
            raise SourceSnapshotError(
                f"source ledger path is not a regular file: {relative_path!r}"
            )
    before = candidate.lstat()
    digest = _sha256(candidate)
    after = candidate.lstat()
    identity_fields = ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns")
    if any(
        getattr(before, field) != getattr(after, field) for field in identity_fields
    ):
        raise SourceSnapshotError(
            f"source ledger file changed while it was being hashed: {relative_path!r}"
        )
    return {
        "path": relative_path,
        "bytes": int(after.st_size),
        "sha256": digest,
    }


def _aggregate_source_records(records: Sequence[Mapping[str, Any]]) -> str:
    """Hash canonical length-prefixed UTF-8 path/size/content-digest records."""
    digest = hashlib.sha256()
    digest.update(SOURCE_TREE_AGGREGATE_FORMAT.encode("ascii") + b"\0")
    for record in sorted(records, key=lambda item: item["path"].encode("utf-8")):
        path_bytes = record["path"].encode("utf-8")
        digest.update(len(path_bytes).to_bytes(8, "big"))
        digest.update(path_bytes)
        digest.update(int(record["bytes"]).to_bytes(8, "big"))
        digest.update(bytes.fromhex(record["sha256"]))
    return digest.hexdigest()


def _source_tree_ledger(
    relative_paths: Sequence[str] | None = None,
    *,
    repository_root: Path = REPOSITORY_ROOT,
) -> dict[str, Any]:
    raw_paths = (
        _discover_source_paths(repository_root)
        if relative_paths is None
        else list(relative_paths)
    )
    canonical_paths: list[str] = []
    exact_paths: set[str] = set()
    portable_paths: dict[str, str] = {}
    for raw_path in raw_paths:
        path = _canonical_source_path(raw_path)
        if path in exact_paths:
            raise SourceSnapshotError(f"duplicate source ledger path: {path!r}")
        portable_key = path.casefold()
        if portable_key in portable_paths:
            raise SourceSnapshotError(
                "source ledger paths collide on a case-insensitive filesystem: "
                f"{portable_paths[portable_key]!r}, {path!r}"
            )
        exact_paths.add(path)
        portable_paths[portable_key] = path
        canonical_paths.append(path)
    records = [
        _source_file_record(repository_root, path)
        for path in sorted(canonical_paths, key=lambda value: value.encode("utf-8"))
    ]
    return {
        "format_version": SOURCE_TREE_FORMAT_VERSION,
        "hash_algorithm": "sha256",
        "aggregate_format": SOURCE_TREE_AGGREGATE_FORMAT,
        "sha256": _aggregate_source_records(records),
        "file_count": len(records),
        "total_bytes": sum(record["bytes"] for record in records),
        "source_changed_during_run": False,
        "verified_unchanged_after_run": False,
        "observed_after_run_sha256": None,
        "scope": {
            "included": list(_SOURCE_TREE_SCOPE["included"]),
            "excluded": list(_SOURCE_TREE_SCOPE["excluded"]),
        },
        "runtime_import": {
            "expected_package_root": "src/deapack",
            "resolved_init_path": None,
            "verified": False,
            "error": "runtime import probe has not run",
        },
        "files": records,
    }


def verify_source_tree_ledger(
    ledger: Mapping[str, Any],
    *,
    repository_root: Path = REPOSITORY_ROOT,
) -> None:
    """Verify every recorded file and the aggregate against a repository tree."""
    raw_files = ledger.get("files")
    if not isinstance(raw_files, list) or not raw_files:
        raise SourceSnapshotError("source ledger files must be a non-empty list")
    paths: list[str] = []
    for position, raw_record in enumerate(raw_files):
        if not isinstance(raw_record, Mapping):
            raise SourceSnapshotError(
                f"source ledger record {position} must be an object"
            )
        if set(raw_record) != {"path", "bytes", "sha256"}:
            raise SourceSnapshotError(
                f"source ledger record {position} has unexpected fields"
            )
        paths.append(raw_record["path"])
    rebuilt = _source_tree_ledger(paths, repository_root=repository_root)
    stable_fields = (
        "format_version",
        "hash_algorithm",
        "aggregate_format",
        "sha256",
        "file_count",
        "total_bytes",
        "files",
    )
    if any(ledger.get(field) != rebuilt[field] for field in stable_fields):
        raise SourceSnapshotError("source ledger does not match repository bytes")


def _run_git(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *arguments),
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def _git_fingerprint() -> dict[str, Any]:
    revision = _run_git("rev-parse", "HEAD")
    branch = _run_git("branch", "--show-current")
    status = _run_git("status", "--porcelain", "--untracked-files=all")
    available = revision.returncode == 0 and status.returncode == 0
    entries = tuple(line for line in status.stdout.splitlines() if line)
    return {
        "available": available,
        "revision": revision.stdout.strip() if revision.returncode == 0 else None,
        "branch": branch.stdout.strip() if branch.returncode == 0 else None,
        "dirty": bool(entries) if available else None,
        "status_entry_count": len(entries) if available else None,
    }


def _package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for distribution in ("DEAPack", "numpy", "pandas", "scipy", "psutil"):
        try:
            versions[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            versions[distribution] = None
    return versions


def _load_psutil() -> Any:
    try:
        import psutil
    except ImportError as error:  # pragma: no cover - exercised by CLI environment
        raise RuntimeError(
            "benchmark execution requires psutil; install DEAPack[benchmark]"
        ) from error
    return psutil


def _benchmark_environment(runtime_directory: Path) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(_CONTROLLED_ENVIRONMENT)
    source_root = str(REPOSITORY_ROOT / "src")
    inherited_python_path = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        source_root + os.pathsep + inherited_python_path
        if inherited_python_path
        else source_root
    )
    environment["MPLCONFIGDIR"] = str(runtime_directory / "matplotlib")
    return environment


def _runtime_import_probe(runtime_directory: Path) -> dict[str, Any]:
    """Prove the benchmark interpreter imports the ledger-bound package tree."""
    code = (
        "import json, pathlib, deapack; "
        "print(json.dumps({'init': str(pathlib.Path(deapack.__file__).resolve())}))"
    )
    completed = subprocess.run(
        (sys.executable, "-c", code),
        cwd=REPOSITORY_ROOT,
        env=_benchmark_environment(runtime_directory),
        check=False,
        capture_output=True,
        text=True,
    )
    record: dict[str, Any] = {
        "expected_package_root": "src/deapack",
        "resolved_init_path": None,
        "verified": False,
        "error": None,
    }
    if completed.returncode != 0:
        record["error"] = (
            f"runtime deapack import probe failed with exit code {completed.returncode}"
        )
        return record
    try:
        payload = json.loads(completed.stdout)
        resolved = Path(payload["init"]).resolve(strict=True)
    except (json.JSONDecodeError, KeyError, OSError, TypeError) as error:
        record["error"] = f"runtime deapack import probe was invalid: {error}"
        return record
    expected = (REPOSITORY_ROOT / "src" / "deapack" / "__init__.py").resolve()
    if resolved != expected:
        record["error"] = "runtime deapack import resolved outside src/deapack"
        return record
    record["resolved_init_path"] = "src/deapack/__init__.py"
    record["verified"] = True
    return record


def environment_fingerprint(psutil: Any) -> dict[str, Any]:
    """Return a stable, privacy-bounded execution-environment record."""
    memory = psutil.virtual_memory()
    return {
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor() or None,
        },
        "cpu": {
            "logical_count": psutil.cpu_count(logical=True),
            "physical_count": psutil.cpu_count(logical=False),
        },
        "memory": {"total_bytes": int(memory.total)},
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
        },
        "packages": _package_versions(),
        "solver": {
            "backend": "scipy-highs",
            "version": None,
            "version_note": (
                "SciPy does not expose the bundled HiGHS version through "
                "DEAPack's public backend contract"
            ),
        },
        "environment": {
            key: os.environ[key] for key in _ENVIRONMENT_KEYS if key in os.environ
        },
        "controlled_environment": dict(_CONTROLLED_ENVIRONMENT),
    }


def _expect_mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ManifestError(f"{label} must be a JSON object")
    return value


def _validate_tier(value: object, *, case_id: str, tier: str) -> dict[str, Any]:
    task = _expect_mapping(value, f"case {case_id!r} {tier!r}")
    if set(task) != {"args", "timeout_seconds"}:
        raise ManifestError(
            f"case {case_id!r} {tier!r} must contain only args and timeout_seconds"
        )
    arguments = task["args"]
    if not isinstance(arguments, list) or not all(
        isinstance(item, str) for item in arguments
    ):
        raise ManifestError(f"case {case_id!r} {tier!r} args must be strings")
    timeout = task["timeout_seconds"]
    if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout <= 0:
        raise ManifestError(
            f"case {case_id!r} {tier!r} timeout_seconds must be a positive integer"
        )
    return {"args": tuple(arguments), "timeout_seconds": timeout}


def load_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    """Load and fully validate the frozen benchmark manifest."""
    try:
        raw = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_json_keys,
        )
    except (OSError, json.JSONDecodeError) as error:
        raise ManifestError(
            f"cannot read benchmark manifest {path}: {error}"
        ) from error
    manifest = _expect_mapping(raw, "benchmark manifest")
    required = {"schema_version", "suite_id", "description", "cases"}
    if set(manifest) != required:
        raise ManifestError(f"benchmark manifest fields must be {sorted(required)!r}")
    if manifest["schema_version"] != MANIFEST_SCHEMA_VERSION:
        raise ManifestError(
            f"unsupported manifest schema {manifest['schema_version']!r}"
        )
    if not isinstance(manifest["suite_id"], str) or not manifest["suite_id"]:
        raise ManifestError("suite_id must be a non-empty string")
    if not isinstance(manifest["description"], str) or not manifest["description"]:
        raise ManifestError("description must be a non-empty string")
    if not isinstance(manifest["cases"], list) or not manifest["cases"]:
        raise ManifestError("cases must be a non-empty JSON array")

    cases: list[dict[str, Any]] = []
    identifiers: set[str] = set()
    for position, raw_case in enumerate(manifest["cases"]):
        case = _expect_mapping(raw_case, f"case at position {position}")
        fields = {"id", "script", "blocking", "smoke", "release"}
        if set(case) != fields:
            raise ManifestError(
                f"case at position {position} fields must be {sorted(fields)!r}"
            )
        case_id = case["id"]
        if not isinstance(case_id, str) or _CASE_ID.fullmatch(case_id) is None:
            raise ManifestError(f"invalid benchmark case id {case_id!r}")
        if case_id in identifiers:
            raise ManifestError(f"duplicate benchmark case id {case_id!r}")
        identifiers.add(case_id)
        script = case["script"]
        if not isinstance(script, str):
            raise ManifestError(f"case {case_id!r} script must be a string")
        script_path = Path(script)
        if (
            script_path.is_absolute()
            or script_path.parent != Path("benchmarks")
            or not script_path.match("benchmark_*.py")
            or not (REPOSITORY_ROOT / script_path).is_file()
        ):
            raise ManifestError(
                f"case {case_id!r} does not name an existing benchmark script"
            )
        if not isinstance(case["blocking"], bool):
            raise ManifestError(f"case {case_id!r} blocking must be boolean")
        cases.append(
            {
                "id": case_id,
                "script": script,
                "blocking": case["blocking"],
                "smoke": _validate_tier(case["smoke"], case_id=case_id, tier="smoke"),
                "release": _validate_tier(
                    case["release"], case_id=case_id, tier="release"
                ),
            }
        )

    available_scripts = {
        path.relative_to(REPOSITORY_ROOT).as_posix()
        for path in (REPOSITORY_ROOT / "benchmarks").glob("benchmark_*.py")
    }
    covered_scripts = {case["script"] for case in cases}
    if available_scripts != covered_scripts:
        raise ManifestError(
            "benchmark manifest/script coverage mismatch; "
            f"missing={sorted(available_scripts - covered_scripts)!r}, "
            f"stale={sorted(covered_scripts - available_scripts)!r}"
        )
    return {
        "schema_version": manifest["schema_version"],
        "suite_id": manifest["suite_id"],
        "description": manifest["description"],
        "cases": tuple(cases),
    }


def _create_report_directory(root: Path, tier: str, started: datetime) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    stem = f"{tier}-{started.strftime('%Y%m%dT%H%M%SZ')}"
    candidate = root / stem
    suffix = 1
    while candidate.exists():
        candidate = root / f"{stem}-{suffix}"
        suffix += 1
    candidate.mkdir()
    (candidate / "logs").mkdir()
    (candidate / "runtime").mkdir()
    return candidate


def _sample_rss(process: subprocess.Popen[bytes], psutil: Any) -> int:
    rss = 0
    try:
        root = psutil.Process(process.pid)
        processes = (root, *root.children(recursive=True))
    except (psutil.Error, OSError):
        try:
            processes = (psutil.Process(process.pid),)
        except (psutil.Error, OSError):
            processes = ()
    for member in processes:
        try:
            rss += int(member.memory_info().rss)
        except (psutil.Error, OSError):
            continue
    return rss


def _terminate_process_tree(
    process: subprocess.Popen[bytes],
    psutil: Any,
) -> None:
    descendants = []
    if os.name != "posix":  # pragma: no cover - exercised on Windows CI/users
        try:
            descendants = psutil.Process(process.pid).children(recursive=True)
        except (psutil.Error, OSError):
            descendants = []
    if os.name == "posix":
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(process.pid, signal.SIGTERM)
    else:  # pragma: no cover - exercised on Windows CI/users
        for member in reversed(descendants):
            with contextlib.suppress(psutil.Error):
                member.terminate()
        with contextlib.suppress(OSError):
            process.terminate()
    try:
        process.wait(timeout=5.0)
        return
    except subprocess.TimeoutExpired:
        pass
    for member in descendants:
        with contextlib.suppress(psutil.Error):
            member.kill()
    with contextlib.suppress(OSError):
        process.kill()
    with contextlib.suppress(subprocess.TimeoutExpired):
        process.wait(timeout=5.0)


def _log_record(path: Path, report_directory: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(report_directory).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def run_case(
    case: Mapping[str, Any],
    *,
    tier: str,
    report_directory: Path,
    psutil: Any,
    sample_interval_seconds: float = 0.05,
) -> dict[str, Any]:
    """Run one frozen case, retaining complete process and log evidence."""
    task = case[tier]
    script_path = REPOSITORY_ROOT / case["script"]
    script_sha256 = _sha256(script_path)
    command = [
        sys.executable,
        str(script_path),
        *task["args"],
    ]
    stdout_path = report_directory / "logs" / f"{case['id']}.stdout.log"
    stderr_path = report_directory / "logs" / f"{case['id']}.stderr.log"
    runtime_directory = report_directory / "runtime" / case["id"]
    runtime_directory.mkdir()
    environment = _benchmark_environment(runtime_directory)
    process_options: dict[str, Any] = {}
    if os.name == "posix":
        process_options["start_new_session"] = True
    elif os.name == "nt":  # pragma: no cover - exercised on Windows CI/users
        process_options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

    started = _utc_now()
    started_clock = time.perf_counter()
    timed_out = False
    peak_rss_bytes = 0
    return_code: int | None = None
    runner_error: str | None = None
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        try:
            process = subprocess.Popen(
                command,
                cwd=REPOSITORY_ROOT,
                env=environment,
                stdout=stdout,
                stderr=stderr,
                **process_options,
            )
            deadline = started_clock + task["timeout_seconds"]
            while True:
                peak_rss_bytes = max(
                    peak_rss_bytes,
                    _sample_rss(process, psutil),
                )
                return_code = process.poll()
                if return_code is not None:
                    break
                if time.perf_counter() >= deadline:
                    timed_out = True
                    _terminate_process_tree(process, psutil)
                    return_code = process.poll()
                    break
                time.sleep(sample_interval_seconds)
        except (OSError, psutil.Error) as error:
            runner_error = f"{type(error).__name__}: {error}"

    finished = _utc_now()
    wall_seconds = time.perf_counter() - started_clock
    if runner_error is not None:
        status = "runner_error"
    elif timed_out:
        status = "timeout"
    elif return_code == 0:
        status = "passed"
    else:
        status = "failed"
    return {
        "id": case["id"],
        "script": case["script"],
        "script_sha256": script_sha256,
        "blocking": case["blocking"],
        "tier": tier,
        "status": status,
        "command": command,
        "command_display": shlex.join(command),
        "timeout_seconds": task["timeout_seconds"],
        "started_at": _iso(started),
        "finished_at": _iso(finished),
        "wall_seconds": wall_seconds,
        "peak_rss_bytes": peak_rss_bytes,
        "return_code": return_code,
        "runner_error": runner_error,
        "stdout": _log_record(stdout_path, report_directory),
        "stderr": _log_record(stderr_path, report_directory),
    }


def _write_markdown(report: Mapping[str, Any], path: Path) -> None:
    summary = report["summary"]
    git = report["git"]
    environment = report["environment"]
    source_tree = report["source_tree"]
    lines = [
        f"# DEAPack {report['tier'].title()} Benchmark Report",
        "",
        f"- Suite status: **{report['suite_status']}**",
        f"- Started: `{report['started_at']}`",
        f"- Finished: `{report['finished_at']}`",
        f"- Git revision: `{git['revision'] or 'unavailable'}`",
        f"- Dirty worktree: `{git['dirty']}`",
        (
            f"- Cases: {summary['total']} total; {summary['passed']} passed; "
            f"{summary['failed']} failed; {summary['timed_out']} timed out; "
            f"{summary['runner_errors']} runner errors"
        ),
        "",
        "Absolute timings are observations for this recorded environment, not "
        "cross-machine release thresholds.",
        "",
        "## Source tree",
        "",
        f"- Aggregate SHA-256: `{source_tree['sha256']}`",
        f"- Files / bytes: `{source_tree['file_count']}` / "
        f"`{source_tree['total_bytes']}`",
        f"- Canonical encoding: `{source_tree['aggregate_format']}`",
        f"- Source changed during run: `{source_tree['source_changed_during_run']}`",
        f"- Verified unchanged after run: "
        f"`{source_tree['verified_unchanged_after_run']}`",
        f"- Runtime package import verified: "
        f"`{source_tree['runtime_import']['verified']}` "
        f"(`{source_tree['runtime_import']['resolved_init_path']}`)",
        "",
        "Included scope: " + "; ".join(source_tree["scope"]["included"]) + ".",
        "",
        "Excluded scope: " + "; ".join(source_tree["scope"]["excluded"]) + ".",
        "",
        "### File ledger",
        "",
        "| Repository-relative path | Bytes | SHA-256 |",
        "|---|---:|---|",
        *(
            f"| `{record['path']}` | {record['bytes']} | `{record['sha256']}` |"
            for record in source_tree["files"]
        ),
        "",
        "## Environment",
        "",
        f"- Platform: `{environment['platform']['system']} "
        f"{environment['platform']['release']} ({environment['platform']['machine']})`",
        f"- Python: `{environment['python']['version']}`",
        f"- Logical/physical CPUs: `{environment['cpu']['logical_count']}` / "
        f"`{environment['cpu']['physical_count']}`",
        f"- Total memory: `{environment['memory']['total_bytes']}` bytes",
        f"- Packages: `{json.dumps(environment['packages'], sort_keys=True)}`",
        "",
        "## Cases",
        "",
        "| Case | Gate | Status | Wall (s) | Peak RSS (MiB) | Exit | Logs |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for case in report["cases"]:
        peak_mib = case["peak_rss_bytes"] / (1024.0 * 1024.0)
        gate = "blocking" if case["blocking"] else "informational"
        exit_code = "—" if case["return_code"] is None else str(case["return_code"])
        lines.append(
            f"| `{case['id']}` | {gate} | {case['status']} | "
            f"{case['wall_seconds']:.3f} | {peak_mib:.1f} | {exit_code} | "
            f"[{case['stdout']['path']}]({case['stdout']['path']}), "
            f"[{case['stderr']['path']}]({case['stderr']['path']}) |"
        )
    lines.extend(
        [
            "",
            "## Case script evidence",
            "",
            *(
                f"- `{case['id']}`: `{case['script']}` — "
                f"SHA-256 `{case['script_sha256']}`"
                for case in report["cases"]
            ),
            "",
            "## Frozen commands",
            "",
            *(
                f"- `{case['id']}`: `{case['command_display']}`"
                for case in report["cases"]
            ),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _summary(cases: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    return {
        "total": len(cases),
        "passed": sum(case["status"] == "passed" for case in cases),
        "failed": sum(case["status"] == "failed" for case in cases),
        "timed_out": sum(case["status"] == "timeout" for case in cases),
        "runner_errors": sum(case["status"] == "runner_error" for case in cases),
        "blocking_failures": sum(
            case["blocking"] and case["status"] != "passed" for case in cases
        ),
        "informational_failures": sum(
            not case["blocking"] and case["status"] != "passed" for case in cases
        ),
    }


def run_suite(
    *,
    manifest_path: Path,
    tier: str,
    output_root: Path,
    selected_ids: Sequence[str] = (),
    blocking_only: bool = False,
    require_clean: bool = False,
    sample_interval_seconds: float = 0.05,
) -> tuple[dict[str, Any], Path]:
    """Run selected frozen cases and return the complete report and directory."""
    if tier not in {"smoke", "release"}:
        raise ValueError("tier must be 'smoke' or 'release'")
    if not math.isfinite(sample_interval_seconds) or sample_interval_seconds <= 0:
        raise ValueError("sample_interval_seconds must be positive and finite")
    manifest = load_manifest(manifest_path)
    cases = list(manifest["cases"])
    available_ids = {case["id"] for case in cases}
    unknown = set(selected_ids).difference(available_ids)
    if unknown:
        raise ManifestError(f"unknown benchmark case IDs: {sorted(unknown)!r}")
    if selected_ids:
        wanted = set(selected_ids)
        cases = [case for case in cases if case["id"] in wanted]
    if blocking_only:
        cases = [case for case in cases if case["blocking"]]
    if not cases:
        raise ManifestError("benchmark selection contains no cases")

    source_tree = _source_tree_ledger()
    verify_source_tree_ledger(source_tree)
    psutil = _load_psutil()
    started = _utc_now()
    report_directory = _create_report_directory(output_root, tier, started)
    git = _git_fingerprint()
    environment = environment_fingerprint(psutil)
    configuration_errors: list[str] = []
    source_tree["runtime_import"] = _runtime_import_probe(
        report_directory / "runtime" / "source-import"
    )
    if not source_tree["runtime_import"]["verified"]:
        configuration_errors.append(
            "runtime_import_mismatch: benchmark interpreter did not import "
            "repository src/deapack"
        )
    if require_clean and git["dirty"] is not False:
        configuration_errors.append(
            "--require-clean requested but the Git worktree is dirty or unavailable"
        )

    results: list[dict[str, Any]] = []
    if not configuration_errors:
        for position, case in enumerate(cases, start=1):
            print(
                f"[{position}/{len(cases)}] {case['id']} ({tier})",
                flush=True,
            )
            result = run_case(
                case,
                tier=tier,
                report_directory=report_directory,
                psutil=psutil,
                sample_interval_seconds=sample_interval_seconds,
            )
            results.append(result)
            print(
                f"  {result['status']} in {result['wall_seconds']:.3f}s; "
                f"peak_rss={result['peak_rss_bytes']} bytes",
                flush=True,
            )

    try:
        final_source_tree = _source_tree_ledger()
    except SourceSnapshotError as error:
        source_tree["source_changed_during_run"] = True
        source_tree["verified_unchanged_after_run"] = False
        configuration_errors.append(f"source_changed_during_run: {error}")
    else:
        source_tree["observed_after_run_sha256"] = final_source_tree["sha256"]
        stable_fields = (
            "format_version",
            "hash_algorithm",
            "aggregate_format",
            "sha256",
            "file_count",
            "total_bytes",
            "files",
        )
        source_changed = any(
            source_tree[field] != final_source_tree[field] for field in stable_fields
        )
        source_tree["source_changed_during_run"] = source_changed
        source_tree["verified_unchanged_after_run"] = not source_changed
        if source_changed:
            configuration_errors.append(
                "source_changed_during_run: source-tree ledger differs between "
                "suite start and finish"
            )

    finished = _utc_now()
    summary = _summary(results)
    suite_status = (
        "configuration_error"
        if configuration_errors
        else "failed"
        if summary["blocking_failures"]
        else "passed_with_informational_failures"
        if summary["informational_failures"]
        else "passed"
    )
    resolved_manifest = manifest_path.resolve()
    try:
        report_manifest_path = resolved_manifest.relative_to(REPOSITORY_ROOT).as_posix()
    except ValueError:
        report_manifest_path = str(resolved_manifest)
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "suite_id": manifest["suite_id"],
        "suite_status": suite_status,
        "tier": tier,
        "started_at": _iso(started),
        "finished_at": _iso(finished),
        "manifest": {
            "path": report_manifest_path,
            "schema_version": manifest["schema_version"],
            "sha256": _sha256(manifest_path),
        },
        "source_tree": source_tree,
        "git": git,
        "environment": environment,
        "configuration_errors": configuration_errors,
        "selection": {
            "case_ids": [case["id"] for case in cases],
            "blocking_only": blocking_only,
            "require_clean": require_clean,
        },
        "summary": summary,
        "cases": results,
    }
    json_path = report_directory / "report.json"
    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    _write_markdown(report, report_directory / "report.md")
    return report, report_directory


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tier", choices=("smoke", "release"), default="smoke")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--case",
        dest="case_ids",
        action="append",
        default=[],
        help="run one exact case ID; repeat to select multiple cases",
    )
    parser.add_argument(
        "--blocking-only",
        action="store_true",
        help="exclude the three source-gated prototype-only scripts",
    )
    parser.add_argument(
        "--require-clean",
        action="store_true",
        help="write a configuration-error report instead of running on a dirty tree",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        report, directory = run_suite(
            manifest_path=arguments.manifest.resolve(),
            tier=arguments.tier,
            output_root=arguments.output_dir.resolve(),
            selected_ids=arguments.case_ids,
            blocking_only=arguments.blocking_only,
            require_clean=arguments.require_clean,
        )
    except (RuntimeError, ValueError) as error:
        print(f"benchmark runner error: {error}", file=sys.stderr)
        return 2
    print(f"benchmark report: {directory}")
    successful = {"passed", "passed_with_informational_failures"}
    return 0 if report["suite_status"] in successful else 1


if __name__ == "__main__":
    raise SystemExit(main())
