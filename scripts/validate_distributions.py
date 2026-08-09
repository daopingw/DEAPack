#!/usr/bin/env python3
"""Validate the structure and safety of built DEAPack distributions."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import sys
import tarfile
import zipfile
from email import policy
from email.parser import BytesParser
from pathlib import Path, PurePosixPath
from types import ModuleType

FORBIDDEN_PARTS = {
    "__pycache__",
    "_build",
    ".DS_Store",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
}
FORBIDDEN_SUFFIXES = {".mo", ".pyc", ".pyo"}
ROOT = Path(__file__).resolve().parents[1]
EXPECTED_LICENSE_EXPRESSION = "GPL-3.0-only AND CC-BY-4.0 AND MIT"
EXPECTED_LICENSE_FILES = frozenset(
    {
        "DATA_LICENSES.md",
        "LICENSE",
        "LICENSES/CC-BY-4.0.txt",
        "LICENSES/MIT-BenchmarkingEconomicEfficiency.jl.txt",
        "LICENSES/MIT-DataEnvelopmentAnalysis.jl.txt",
        "NOTICE",
    }
)


def _safe_member(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        raise RuntimeError(f"unsafe archive member: {name}")
    if FORBIDDEN_PARTS.intersection(path.parts) or path.suffix in FORBIDDEN_SUFFIXES:
        raise RuntimeError(f"generated or private file leaked into archive: {name}")
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_core_metadata(payload: bytes, *, label: str) -> None:
    message = BytesParser(policy=policy.default).parsebytes(payload)
    expression = message.get("License-Expression")
    if expression != EXPECTED_LICENSE_EXPRESSION:
        raise RuntimeError(
            f"{label} has License-Expression={expression!r}; expected "
            f"{EXPECTED_LICENSE_EXPRESSION!r}"
        )
    license_files = frozenset(message.get_all("License-File", []))
    if license_files != EXPECTED_LICENSE_FILES:
        raise RuntimeError(
            f"{label} has License-File records {sorted(license_files)!r}; "
            f"expected {sorted(EXPECTED_LICENSE_FILES)!r}"
        )


def _expected_license_payload(name: str) -> bytes:
    return (ROOT / name).read_bytes()


def _validate_wheel(path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = tuple(member.filename for member in infos)
        members = tuple(_safe_member(name) for name in names)
        required = (
            PurePosixPath("deapack/__init__.py"),
            PurePosixPath("deapack/_registry.py"),
            PurePosixPath("deapack/datasets/__init__.py"),
        )
        for member in required:
            if member not in members:
                raise RuntimeError(f"wheel is missing {member}")
        metadata = [
            (info, member)
            for info, member in zip(infos, members, strict=True)
            if member.parts[-1] == "METADATA"
            and member.parent.name.endswith(".dist-info")
        ]
        if len(metadata) != 1:
            raise RuntimeError(
                "wheel must contain exactly one dist-info/METADATA record"
            )
        metadata_info, metadata_path = metadata[0]
        _validate_core_metadata(
            archive.read(metadata_info), label=f"wheel {metadata_path}"
        )
        dist_info = metadata_path.parent
        for name in sorted(EXPECTED_LICENSE_FILES):
            expected_path = dist_info / "licenses" / name
            matching = [
                info
                for info, member in zip(infos, members, strict=True)
                if member == expected_path
            ]
            if len(matching) != 1:
                raise RuntimeError(f"wheel is missing exactly one {expected_path}")
            if archive.read(matching[0]) != _expected_license_payload(name):
                raise RuntimeError(
                    f"wheel {expected_path} differs from repository {name}"
                )


def _validate_sdist(path: Path) -> None:
    with tarfile.open(path, mode="r:gz") as archive:
        infos = archive.getmembers()
        members = tuple(_safe_member(info.name) for info in infos)
        if any(info.issym() or info.islnk() for info in infos):
            raise RuntimeError("sdist must not contain symbolic or hard links")
        roots = {member.parts[0] for member in members if member.parts}
        if len(roots) != 1:
            raise RuntimeError(
                f"sdist must have one top-level directory; found {sorted(roots)}"
            )
        root = next(iter(roots))
        relative_pairs = tuple(
            (info, PurePosixPath(*member.parts[1:]))
            for info, member in zip(infos, members, strict=True)
        )
        relative = {member for _, member in relative_pairs}
        required = {
            PurePosixPath("pyproject.toml"),
            PurePosixPath("PYPI_README.md"),
            PurePosixPath("README.md"),
            PurePosixPath("PKG-INFO"),
            PurePosixPath("CITATION.cff"),
            PurePosixPath("CHANGELOG.md"),
            PurePosixPath("CITATION.md"),
            PurePosixPath("RELEASE_NOTES_2.0.0.md"),
            PurePosixPath("src/deapack/__init__.py"),
            PurePosixPath("src/deapack/_registry.py"),
            PurePosixPath("src/deapack/datasets/__init__.py"),
        } | {PurePosixPath(name) for name in EXPECTED_LICENSE_FILES}
        missing = sorted(str(member) for member in required.difference(relative))
        if missing:
            raise RuntimeError(f"sdist {root!r} is missing: {', '.join(missing)}")

        by_path = {member: info for info, member in relative_pairs if info.isfile()}
        metadata_stream = archive.extractfile(by_path[PurePosixPath("PKG-INFO")])
        if metadata_stream is None:
            raise RuntimeError("sdist PKG-INFO is not a regular readable file")
        _validate_core_metadata(metadata_stream.read(), label="sdist PKG-INFO")
        for name in sorted(EXPECTED_LICENSE_FILES):
            relative_name = PurePosixPath(name)
            stream = archive.extractfile(by_path[relative_name])
            if stream is None or stream.read() != _expected_license_payload(name):
                raise RuntimeError(f"sdist {name} differs from repository {name}")

        forbidden_source_prefixes = tuple(
            PurePosixPath(prefix)
            for prefix in (
                ".github",
                "benchmarks",
                "book",
                "docs",
                "scripts",
                "specs",
                "tests",
            )
        )
        for prefix in forbidden_source_prefixes:
            if any(
                member.parts[: len(prefix.parts)] == prefix.parts for member in relative
            ):
                raise RuntimeError(
                    f"generated or inactive tree leaked into sdist: {prefix}"
                )


def _load_release_dataset_audit() -> ModuleType:
    """Load the sibling audit script in CLI and import-based test contexts."""

    module_name = "_deapack_release_dataset_audit"
    loaded = sys.modules.get(module_name)
    if loaded is not None:
        return loaded
    path = Path(__file__).with_name("audit_release_datasets.py")
    specification = importlib.util.spec_from_file_location(module_name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load release dataset audit from {path}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[module_name] = module
    specification.loader.exec_module(module)
    return module


def _run_release_dataset_audit() -> str:
    """Run the fail-closed source metadata gate and return its report."""

    module = _load_release_dataset_audit()
    report = module.audit_bundled_datasets()
    rendered = module.format_audit(report)
    if not report.passed:
        raise RuntimeError(rendered)
    return rendered


def validate(directory: Path, *, release: bool = False) -> tuple[Path, Path]:
    """Validate exactly one wheel and one gzipped source distribution."""

    directory = directory.resolve()
    wheels = sorted(directory.glob("*.whl"))
    sdists = sorted(directory.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise RuntimeError(
            f"expected one wheel and one sdist in {directory}; "
            f"found {len(wheels)} wheel(s) and {len(sdists)} sdist(s)"
        )
    wheel, sdist = wheels[0], sdists[0]
    _validate_wheel(wheel)
    _validate_sdist(sdist)
    if release:
        print(_run_release_dataset_audit())
    for path in (wheel, sdist):
        print(
            f"validated {path.name}: {path.stat().st_size} bytes sha256={_sha256(path)}"
        )
    return wheel, sdist


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", type=Path, default=Path("dist"))
    parser.add_argument(
        "--release",
        action="store_true",
        help=(
            "enable release-only gates, including fail-closed bundled dataset "
            "redistribution and licence declarations"
        ),
    )
    arguments = parser.parse_args()
    try:
        validate(arguments.directory, release=arguments.release)
    except RuntimeError as error:
        parser.exit(status=1, message=f"{error}\n")


if __name__ == "__main__":
    main()
