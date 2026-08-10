"""Verify and inventory the protected Python 3.12 release toolchain.

The constraint is intentionally a direct, cross-platform pin set rather than
a platform-specific wheel freeze.  The emitted JSON records the complete
resolved Python environment, copied Documentation asset evidence, and the
rendered Documentation site that produced a release candidate.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import re
import stat
import sys
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONSTRAINT = ROOT / "constraints/release-python312.txt"
SCHEMA = "deapack.release-toolchain-inventory.v1"
MATHJAX_VERSION = "4.0.0"
MATHJAX_URL = f"https://cdn.jsdelivr.net/npm/mathjax@{MATHJAX_VERSION}/tex-mml-chtml.js"

EXPECTED_PINS = {
    "build": "1.5.0",
    "jsonschema": "4.26.0",
    "matplotlib": "3.11.1",
    "myst-parser": "5.1.0",
    "numpy": "2.4.6",
    "packaging": "26.2",
    "pandas": "3.0.3",
    "pip": "25.0.1",
    "psutil": "7.2.2",
    "pydata-sphinx-theme": "0.19.0",
    "pygments": "2.20.0",
    "pytest": "9.1.1",
    "pytest-cov": "7.1.0",
    "ruff": "0.15.18",
    "scipy": "1.18.0",
    "setuptools": "84.0.0",
    "sphinx": "9.1.0",
    "sphinx-autodoc-typehints": "3.11.0",
    "sphinx-intl": "2.3.2",
    "sphinxcontrib-bibtex": "2.7.0",
    "twine": "7.0.0",
}

PROFILES = {
    "package": frozenset({"build", "packaging", "pip", "setuptools", "twine"}),
    "docs": frozenset(
        {
            "matplotlib",
            "myst-parser",
            "numpy",
            "pandas",
            "pip",
            "pydata-sphinx-theme",
            "pygments",
            "scipy",
            "setuptools",
            "sphinx",
            "sphinx-autodoc-typehints",
            "sphinx-intl",
            "sphinxcontrib-bibtex",
        }
    ),
    "release": frozenset(EXPECTED_PINS),
}

INVENTORY_SCOPE = (
    "protected CPython 3.12 release lane; exact direct Python pins, resolved "
    "transitive Python distributions, the complete rendered Documentation "
    "site byte tree, and exact rendered-asset producer evidence"
)
INVENTORY_LIMITATIONS = (
    "This file is a resolved build record, not a hash-locked wheel lock.",
    (
        "Transitive Python packages are recorded but only reviewed direct "
        "pins are constrained."
    ),
    (
        "The exact MathJax CDN URL is external at reader view time; MathJax "
        "bytes are not copied into the generated sites."
    ),
    (
        "Ordinary DEAPack users retain the broader runtime ranges declared "
        "in pyproject.toml."
    ),
)

EXPECTED_MATHJAX_CONFIGURATION = ("docs/conf.py",)
SITE_CONTRACTS: dict[str, tuple[int, str]] = {
    "_site/docs/en": (98, "legal/third-party-notices.html"),
}
SYSTEM_TOOLCHAIN_STATE = "not-required-for-package-documentation"

_NAME_RUN = re.compile(r"[-_.]+")
_VERSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+!-]*\Z")
_MATHJAX_REFERENCE = re.compile(
    r"https://cdn\.jsdelivr\.net/npm/mathjax@[^\"'<>\s]+/tex-mml-chtml\.js"
)
_INVENTORY_KEYS = {
    "schema",
    "state",
    "scope",
    "constraint",
    "profile",
    "runtime",
    "python_distributions",
    "rendered_components",
    "consolidated_notice_source",
    "mathjax_configuration",
    "rendered_sites",
    "system_toolchain",
    "pdf_font_inventories",
    "limitations",
    "generator",
    "inventory_sha256",
}


def _normalise_name(value: str) -> str:
    return _NAME_RUN.sub("-", value).lower()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: object) -> str:
    return _sha256_bytes(
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )


def parse_constraint(path: Path = DEFAULT_CONSTRAINT) -> dict[str, str]:
    """Parse one exact-pin-only constraint and enforce the reviewed pin set."""

    pins: dict[str, str] = {}
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.count("==") != 1:
            raise ValueError(
                f"constraint line {number} is not one exact name==version pin"
            )
        name, version = (item.strip() for item in line.split("==", maxsplit=1))
        normalised = _normalise_name(name)
        if (
            not name
            or not version
            or _VERSION.fullmatch(version) is None
            or normalised in pins
            or any(token in line for token in (";", "@", "#", "[", "]"))
        ):
            raise ValueError(f"constraint line {number} is ambiguous or duplicated")
        pins[normalised] = version
    if pins != EXPECTED_PINS:
        missing = sorted(set(EXPECTED_PINS) - set(pins))
        extra = sorted(set(pins) - set(EXPECTED_PINS))
        drift = sorted(
            name
            for name in set(pins) & set(EXPECTED_PINS)
            if pins[name] != EXPECTED_PINS[name]
        )
        raise ValueError(
            "reviewed release constraint drifted: "
            f"missing={missing}, extra={extra}, version_drift={drift}"
        )
    return pins


def _installed_distributions() -> dict[str, importlib.metadata.Distribution]:
    installed: dict[str, importlib.metadata.Distribution] = {}
    for distribution in importlib.metadata.distributions():
        raw_name = distribution.metadata.get("Name")
        if not raw_name:
            continue
        name = _normalise_name(raw_name)
        previous = installed.get(name)
        if previous is not None and previous.version != distribution.version:
            raise ValueError(f"multiple installed versions found for {name}")
        installed[name] = distribution
    return installed


def verify_installed(
    *,
    profile: str,
    constraint: Path = DEFAULT_CONSTRAINT,
    require_ci_platform: bool = False,
) -> dict[str, importlib.metadata.Distribution]:
    """Require every reviewed direct pin used by a workflow profile."""

    pins = parse_constraint(constraint)
    if profile not in PROFILES:
        raise ValueError(f"unknown release-toolchain profile: {profile}")
    if require_ci_platform and (
        sys.version_info[:2] != (3, 12) or platform.system() != "Linux"
    ):
        raise ValueError("protected release profiles require CPython 3.12 on Linux")
    installed = _installed_distributions()
    violations = []
    for name in sorted(PROFILES[profile]):
        distribution = installed.get(name)
        if distribution is None:
            violations.append(f"{name} is not installed")
        elif distribution.version != pins[name]:
            violations.append(
                f"{name}=={distribution.version} does not match {name}=={pins[name]}"
            )
    if violations:
        raise ValueError(
            "installed release toolchain drifted: " + "; ".join(violations)
        )
    return installed


def _regular_bytes(path: Path, *, limit: int = 16 * 1024 * 1024) -> bytes:
    status = path.stat()
    if not stat.S_ISREG(status.st_mode) or status.st_size > limit:
        raise ValueError(f"toolchain evidence is not a bounded regular file: {path}")
    return path.read_bytes()


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _safe_relative_path(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    path = PurePosixPath(value)
    return (
        path.as_posix() == value
        and not path.is_absolute()
        and not any(part in {"", ".", ".."} for part in path.parts)
    )


def _site_file_records(site: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for path in sorted(site.rglob("*")):
        status = path.lstat()
        if stat.S_ISDIR(status.st_mode):
            continue
        if stat.S_ISLNK(status.st_mode) or not stat.S_ISREG(status.st_mode):
            raise ValueError(f"rendered site contains a non-regular entry: {path}")
        payload = _regular_bytes(path)
        records.append(
            {
                "path": path.relative_to(site).as_posix(),
                "size": len(payload),
                "sha256": _sha256_bytes(payload),
            }
        )
    if not records:
        raise ValueError(f"rendered site contains no regular files: {site}")
    return records


def _license_file_records(
    distribution: importlib.metadata.Distribution,
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for entry in distribution.files or ():
        relative = PurePosixPath(str(entry))
        basename = relative.name.lower()
        if not (
            "licenses" in {part.lower() for part in relative.parts}
            or basename.startswith(("license", "licence", "copying", "notice"))
        ):
            continue
        path = Path(distribution.locate_file(entry))
        try:
            payload = _regular_bytes(path, limit=4 * 1024 * 1024)
        except (OSError, ValueError):
            continue
        records.append(
            {
                "path": relative.as_posix(),
                "sha256": _sha256_bytes(payload),
                "size": len(payload),
            }
        )
    records.sort(key=lambda item: str(item["path"]))
    return records


def _distribution_record(
    name: str,
    distribution: importlib.metadata.Distribution,
    *,
    direct_pins: Mapping[str, str],
) -> dict[str, object]:
    metadata = distribution.metadata
    raw_license = metadata.get("License") or ""
    classifiers = sorted(
        value
        for value in metadata.get_all("Classifier", [])
        if value.startswith("License ::")
    )
    license_files = _license_file_records(distribution)
    record: dict[str, object] = {
        "name": metadata.get("Name") or name,
        "normalised_name": name,
        "version": distribution.version,
        "direct_constraint": name in direct_pins,
        "license_expression": metadata.get("License-Expression"),
        "license_classifiers": classifiers,
        "license_text_sha256": (
            _sha256_bytes(raw_license.encode("utf-8")) if raw_license else None
        ),
        "license_files": license_files,
    }
    if name in direct_pins and not any(
        (
            record["license_expression"],
            classifiers,
            record["license_text_sha256"],
            license_files,
        )
    ):
        raise ValueError(f"direct release pin {name} has no installed license signal")
    return record


def _distribution_file(
    distribution: importlib.metadata.Distribution,
    suffix: str,
) -> tuple[str, bytes]:
    matches = [
        entry
        for entry in distribution.files or ()
        if PurePosixPath(str(entry)).as_posix().endswith(suffix)
    ]
    if len(matches) != 1:
        raise ValueError(
            f"{distribution.metadata.get('Name')} lacks one asset {suffix!r}"
        )
    entry = matches[0]
    path = Path(distribution.locate_file(entry))
    return PurePosixPath(str(entry)).as_posix(), _regular_bytes(path)


def _static_asset_inventory(
    installed: Mapping[str, importlib.metadata.Distribution],
) -> tuple[list[dict[str, object]], dict[str, bytes]]:
    pydata = installed["pydata-sphinx-theme"]
    sphinx = installed["sphinx"]
    pygments = installed["pygments"]
    bootstrap_path, bootstrap_notice = _distribution_file(
        pydata,
        "static/scripts/bootstrap.js.LICENSE.txt",
    )
    fontawesome_path, fontawesome_notice = _distribution_file(
        pydata,
        "static/scripts/fontawesome.js.LICENSE.txt",
    )
    if b"Bootstrap v5.3.3" not in bootstrap_notice:
        raise ValueError("PyData theme Bootstrap asset is not reviewed version 5.3.3")
    if b"Font Awesome Free 7.2.0" not in fontawesome_notice:
        raise ValueError(
            "PyData theme Font Awesome asset is not reviewed version 7.2.0"
        )

    sphinx_licenses = _license_file_records(sphinx)
    pydata_licenses = _license_file_records(pydata)
    pygments_licenses = _license_file_records(pygments)
    if not sphinx_licenses or not pydata_licenses or not pygments_licenses:
        raise ValueError("rendered-asset producer license evidence is incomplete")
    assets = [
        {
            "name": "Sphinx generated HTML assets",
            "version": sphinx.version,
            "license": "BSD-2-Clause",
            "source_distribution": "Sphinx",
            "source_license_files": sphinx_licenses,
        },
        {
            "name": "PyData Sphinx Theme",
            "version": pydata.version,
            "license": "BSD-3-Clause",
            "source_distribution": "pydata-sphinx-theme",
            "source_license_files": pydata_licenses,
        },
        {
            "name": "Bootstrap",
            "version": "5.3.3",
            "license": "MIT",
            "source_distribution": "pydata-sphinx-theme",
            "source_notice_path": bootstrap_path,
            "source_notice_sha256": _sha256_bytes(bootstrap_notice),
        },
        {
            "name": "Font Awesome Free",
            "version": "7.2.0",
            "license": "MIT AND CC-BY-4.0 AND OFL-1.1",
            "source_distribution": "pydata-sphinx-theme",
            "source_notice_path": fontawesome_path,
            "source_notice_sha256": _sha256_bytes(fontawesome_notice),
        },
        {
            "name": "Pygments generated stylesheet",
            "version": pygments.version,
            "license": "BSD-2-Clause",
            "source_distribution": "Pygments",
            "source_license_files": pygments_licenses,
        },
        {
            "name": "MathJax",
            "version": MATHJAX_VERSION,
            "license": "Apache-2.0",
            "delivery": "exact-version CDN reference; not copied into the site",
            "url": MATHJAX_URL,
        },
    ]
    copied_notices = {
        "bootstrap.js.LICENSE.txt": bootstrap_notice,
        "fontawesome.js.LICENSE.txt": fontawesome_notice,
    }
    return assets, copied_notices


def _verify_mathjax_configuration(root: Path) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    expected = f'mathjax_path = "{MATHJAX_URL}"'
    for relative in EXPECTED_MATHJAX_CONFIGURATION:
        path = root / relative
        payload = _regular_bytes(path)
        source = payload.decode("utf-8")
        if source.count(expected) != 1 or "mathjax@4/tex-mml-chtml.js" in source:
            raise ValueError(f"{relative} does not bind the exact MathJax URL")
        records.append({"path": relative, "sha256": _sha256_bytes(payload)})
    return records


def _site_record(
    root: Path,
    site: Path,
    *,
    copied_notices: Mapping[str, bytes],
) -> dict[str, object]:
    site = site.resolve(strict=True)
    if not site.is_dir():
        raise ValueError(f"rendered site is not a directory: {site}")
    try:
        label = site.relative_to(root.resolve()).as_posix()
    except ValueError:
        label = site.as_posix()
    contract = SITE_CONTRACTS.get(label)
    if contract is None:
        raise ValueError(f"rendered site is outside the exact release set: {label}")
    expected_html_count, expected_notice_path = contract
    site_files = _site_file_records(site)
    files_by_path = {str(item["path"]): item for item in site_files}
    notice_hashes: dict[str, str] = {}
    for name, expected in copied_notices.items():
        path = site / "_static/scripts" / name
        payload = _regular_bytes(path)
        if payload != expected:
            raise ValueError(f"rendered site notice drifted: {path}")
        notice_hashes[name] = _sha256_bytes(payload)
    html_files = sorted(site.rglob("*.html"))
    if len(html_files) != expected_html_count:
        raise ValueError(
            f"rendered site HTML count drifted: {label}: "
            f"expected={expected_html_count}, observed={len(html_files)}"
        )
    references: set[str] = set()
    reference_count = 0
    for path in html_files:
        source = path.read_text(encoding="utf-8")
        matches = _MATHJAX_REFERENCE.findall(source)
        references.update(matches)
        reference_count += len(matches)
    if references != {MATHJAX_URL} or reference_count == 0:
        raise ValueError(
            f"rendered site does not exclusively use exact MathJax {MATHJAX_VERSION}: "
            f"{site}"
        )
    notice = site / expected_notice_path
    if not notice.is_file():
        raise ValueError(f"rendered site lacks its consolidated notice page: {notice}")
    notice_payload = _regular_bytes(notice)
    for marker in (
        b"Sphinx 9.1.0",
        b"PyData Sphinx Theme 0.19.0",
        b"Bootstrap 5.3.3",
        b"Font Awesome Free 7.2.0",
        b"MathJax 4.0.0",
    ):
        if marker not in notice_payload:
            raise ValueError(
                f"rendered consolidated notice omits {marker.decode()}: {site}"
            )
    for name, digest in notice_hashes.items():
        record = files_by_path.get(f"_static/scripts/{name}")
        if record is None or record.get("sha256") != digest:
            raise ValueError(f"rendered site tree omits copied notice: {name}")
    notice_record = files_by_path.get(expected_notice_path)
    if notice_record is None or notice_record.get("sha256") != _sha256_bytes(
        notice_payload
    ):
        raise ValueError("rendered site tree omits its consolidated notice")
    return {
        "path": label,
        "html_file_count": len(html_files),
        "mathjax_reference_count": reference_count,
        "mathjax_urls": sorted(references),
        "copied_notice_sha256": notice_hashes,
        "consolidated_notice_path": expected_notice_path,
        "consolidated_notice_sha256": _sha256_bytes(notice_payload),
        "site_files": site_files,
        "site_tree_sha256": _canonical_sha256({"files": site_files}),
    }


def build_inventory(
    *,
    root: Path,
    constraint: Path,
    profile: str,
    require_ci_platform: bool,
    site_roots: Iterable[Path],
) -> dict[str, object]:
    pins = parse_constraint(constraint)
    installed = verify_installed(
        profile=profile,
        constraint=constraint,
        require_ci_platform=require_ci_platform,
    )
    assets, copied_notices = _static_asset_inventory(installed)
    python_records = [
        _distribution_record(name, distribution, direct_pins=pins)
        for name, distribution in sorted(installed.items())
    ]
    site_records = sorted(
        (
            _site_record(root, site, copied_notices=copied_notices)
            for site in site_roots
        ),
        key=lambda item: str(item["path"]),
    )
    inventory: dict[str, object] = {
        "schema": SCHEMA,
        "state": "verified",
        "scope": INVENTORY_SCOPE,
        "constraint": {
            "path": constraint.resolve().relative_to(root.resolve()).as_posix(),
            "sha256": _sha256_file(constraint),
            "direct_pins": [
                {"name": name, "version": version}
                for name, version in sorted(pins.items())
            ],
        },
        "profile": profile,
        "runtime": {
            "python_implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
            "platform_system": platform.system(),
            "platform_release": platform.release(),
            "platform_machine": platform.machine(),
        },
        "python_distributions": python_records,
        "rendered_components": assets,
        "consolidated_notice_source": {
            "path": "THIRD_PARTY_NOTICES.md",
            "sha256": _sha256_file(root / "THIRD_PARTY_NOTICES.md"),
        },
        "mathjax_configuration": _verify_mathjax_configuration(root),
        "rendered_sites": site_records,
        "system_toolchain": {
            "state": SYSTEM_TOOLCHAIN_STATE,
            "packages": [],
            "tools": [],
            "font_sources": [],
        },
        "pdf_font_inventories": [],
        "limitations": list(INVENTORY_LIMITATIONS),
        "generator": {
            "path": "scripts/release_toolchain.py",
            "sha256": _sha256_file(Path(__file__)),
        },
    }
    inventory["inventory_sha256"] = _canonical_sha256(inventory)
    return validate_inventory_payload(inventory)


def verify_inventory(
    inventory_path: Path,
    *,
    root: Path = ROOT,
    constraint: Path = DEFAULT_CONSTRAINT,
) -> dict[str, object]:
    value = json.loads(inventory_path.read_text(encoding="utf-8"))
    value = validate_inventory_payload(value)
    constraint_record = value.get("constraint")
    if not isinstance(constraint_record, Mapping):
        raise ValueError("release-toolchain inventory lacks its constraint binding")
    expected_path = constraint.resolve().relative_to(root.resolve()).as_posix()
    if constraint_record.get("path") != expected_path or constraint_record.get(
        "sha256"
    ) != _sha256_file(constraint):
        raise ValueError("release-toolchain inventory constraint binding drifted")
    notice_record = value.get("consolidated_notice_source")
    notice_path = root / "THIRD_PARTY_NOTICES.md"
    if (
        not isinstance(notice_record, Mapping)
        or notice_record.get("path") != "THIRD_PARTY_NOTICES.md"
        or notice_record.get("sha256") != _sha256_file(notice_path)
    ):
        raise ValueError("release-toolchain consolidated notice source drifted")
    generator = value.get("generator")
    generator_path = root / "scripts/release_toolchain.py"
    if (
        not isinstance(generator, Mapping)
        or generator.get("path") != "scripts/release_toolchain.py"
        or generator.get("sha256") != _sha256_file(generator_path)
    ):
        raise ValueError("release-toolchain generator binding drifted")
    if value.get("mathjax_configuration") != _verify_mathjax_configuration(root):
        raise ValueError("release-toolchain MathJax configuration binding drifted")
    parse_constraint(constraint)
    return value


def validate_inventory_payload(value: object) -> dict[str, object]:
    """Validate a signed inventory without consulting its former environment."""

    if not isinstance(value, Mapping) or set(value) != _INVENTORY_KEYS:
        raise ValueError("release-toolchain inventory keys are invalid")
    parsed = dict(value)
    digest = parsed.pop("inventory_sha256", None)
    if not isinstance(digest, str) or digest != _canonical_sha256(parsed):
        raise ValueError("release-toolchain inventory digest is invalid")
    if parsed.get("schema") != SCHEMA or parsed.get("state") != "verified":
        raise ValueError("release-toolchain inventory schema/state is invalid")
    if parsed.get("scope") != INVENTORY_SCOPE:
        raise ValueError("release-toolchain inventory scope is invalid")
    if parsed.get("profile") != "release":
        raise ValueError("release-toolchain inventory does not use the release profile")
    constraint_record = parsed.get("constraint")
    expected_pins = [
        {"name": name, "version": version}
        for name, version in sorted(EXPECTED_PINS.items())
    ]
    if (
        not isinstance(constraint_record, Mapping)
        or set(constraint_record) != {"path", "sha256", "direct_pins"}
        or constraint_record.get("path") != "constraints/release-python312.txt"
        or not _is_sha256(constraint_record.get("sha256"))
        or constraint_record.get("direct_pins") != expected_pins
    ):
        raise ValueError("release-toolchain inventory direct pins are invalid")

    runtime = parsed.get("runtime")
    if (
        not isinstance(runtime, Mapping)
        or set(runtime)
        != {
            "python_implementation",
            "python_version",
            "platform_system",
            "platform_release",
            "platform_machine",
        }
        or runtime.get("python_implementation") != "CPython"
        or runtime.get("platform_system") != "Linux"
        or re.fullmatch(r"3\.12\.\d+", str(runtime.get("python_version"))) is None
        or not isinstance(runtime.get("platform_release"), str)
        or not runtime.get("platform_release")
        or not isinstance(runtime.get("platform_machine"), str)
        or not runtime.get("platform_machine")
    ):
        raise ValueError("release-toolchain runtime is not CPython 3.12 on Linux")

    distributions = parsed.get("python_distributions")
    if not isinstance(distributions, list) or not distributions:
        raise ValueError("release-toolchain Python distribution inventory is empty")
    if any(not isinstance(item, Mapping) for item in distributions):
        raise ValueError("release-toolchain Python distribution record is invalid")
    names = [item.get("normalised_name") for item in distributions]
    if any(not isinstance(name, str) or not name for name in names) or len(
        set(names)
    ) != len(names):
        raise ValueError("release-toolchain Python distribution names are invalid")
    direct_records = [
        item for item in distributions if item.get("direct_constraint") is True
    ]
    installed_direct = {
        item.get("normalised_name"): item.get("version") for item in direct_records
    }
    if len(direct_records) != len(EXPECTED_PINS) or installed_direct != EXPECTED_PINS:
        raise ValueError("release-toolchain installed direct versions are invalid")
    for item in direct_records:
        license_signal = any(
            (
                item.get("license_expression"),
                item.get("license_classifiers"),
                item.get("license_text_sha256"),
                item.get("license_files"),
            )
        )
        if not license_signal:
            raise ValueError("release-toolchain direct pin lacks license evidence")

    notice_source = parsed.get("consolidated_notice_source")
    if (
        not isinstance(notice_source, Mapping)
        or set(notice_source) != {"path", "sha256"}
        or notice_source.get("path") != "THIRD_PARTY_NOTICES.md"
        or not _is_sha256(notice_source.get("sha256"))
    ):
        raise ValueError("release-toolchain consolidated notice binding is invalid")

    components = parsed.get("rendered_components")
    expected_components = {
        "Sphinx generated HTML assets": "9.1.0",
        "PyData Sphinx Theme": "0.19.0",
        "Bootstrap": "5.3.3",
        "Font Awesome Free": "7.2.0",
        "Pygments generated stylesheet": "2.20.0",
        "MathJax": MATHJAX_VERSION,
    }
    observed_components = (
        {
            item.get("name"): item.get("version")
            for item in components
            if isinstance(item, Mapping)
        }
        if isinstance(components, list)
        else {}
    )
    if (
        not isinstance(components, list)
        or len(components) != len(expected_components)
        or observed_components != expected_components
    ):
        raise ValueError("release-toolchain rendered-component versions are invalid")
    for item in components:
        if not isinstance(item.get("license"), str) or not item.get("license"):
            raise ValueError("release-toolchain rendered-component license is invalid")
        name = item.get("name")
        if name in {
            "Sphinx generated HTML assets",
            "PyData Sphinx Theme",
            "Pygments generated stylesheet",
        }:
            files = item.get("source_license_files")
            if not isinstance(files, list) or not files:
                raise ValueError("rendered component lacks source license files")
            for record in files:
                if (
                    not isinstance(record, Mapping)
                    or not _safe_relative_path(record.get("path"))
                    or not _is_sha256(record.get("sha256"))
                    or not isinstance(record.get("size"), int)
                    or record.get("size", 0) <= 0
                ):
                    raise ValueError("rendered component license file is invalid")
        elif name in {"Bootstrap", "Font Awesome Free"}:
            if not _safe_relative_path(
                item.get("source_notice_path")
            ) or not _is_sha256(item.get("source_notice_sha256")):
                raise ValueError("rendered component source notice is invalid")
        elif name == "MathJax" and (
            item.get("url") != MATHJAX_URL
            or item.get("delivery")
            != "exact-version CDN reference; not copied into the site"
        ):
            raise ValueError("MathJax delivery evidence is invalid")

    mathjax = parsed.get("mathjax_configuration")
    observed_mathjax = (
        {item.get("path"): item for item in mathjax if isinstance(item, Mapping)}
        if isinstance(mathjax, list)
        else {}
    )
    if set(observed_mathjax) != set(EXPECTED_MATHJAX_CONFIGURATION) or len(
        observed_mathjax
    ) != len(EXPECTED_MATHJAX_CONFIGURATION):
        raise ValueError("release-toolchain MathJax configuration is incomplete")
    if any(
        set(item) != {"path", "sha256"} or not _is_sha256(item.get("sha256"))
        for item in observed_mathjax.values()
    ):
        raise ValueError("release-toolchain MathJax configuration is invalid")

    sites = parsed.get("rendered_sites")
    observed_sites = (
        {item.get("path"): item for item in sites if isinstance(item, Mapping)}
        if isinstance(sites, list)
        else {}
    )
    if set(observed_sites) != set(SITE_CONTRACTS) or len(observed_sites) != len(
        SITE_CONTRACTS
    ):
        raise ValueError("release-toolchain rendered-site set is incomplete")
    for path, (expected_count, notice_path) in SITE_CONTRACTS.items():
        site = observed_sites[path]
        if set(site) != {
            "path",
            "html_file_count",
            "mathjax_reference_count",
            "mathjax_urls",
            "copied_notice_sha256",
            "consolidated_notice_path",
            "consolidated_notice_sha256",
            "site_files",
            "site_tree_sha256",
        }:
            raise ValueError("release-toolchain rendered-site record is invalid")
        files = site.get("site_files")
        if not isinstance(files, list) or not files:
            raise ValueError("release-toolchain rendered-site tree is empty")
        file_paths: list[str] = []
        files_by_path: dict[str, Mapping[str, object]] = {}
        for record in files:
            if (
                not isinstance(record, Mapping)
                or set(record) != {"path", "size", "sha256"}
                or not _safe_relative_path(record.get("path"))
                or not isinstance(record.get("size"), int)
                or record.get("size", -1) < 0
                or not _is_sha256(record.get("sha256"))
            ):
                raise ValueError("release-toolchain rendered-site file is invalid")
            relative = str(record["path"])
            file_paths.append(relative)
            files_by_path[relative] = record
        if len(files_by_path) != len(files) or file_paths != sorted(file_paths):
            raise ValueError("release-toolchain rendered-site file paths are invalid")
        if site.get("site_tree_sha256") != _canonical_sha256({"files": files}):
            raise ValueError("release-toolchain rendered-site tree digest is invalid")
        html_count = sum(name.endswith(".html") for name in file_paths)
        if (
            site.get("html_file_count") != expected_count
            or html_count != expected_count
            or not isinstance(site.get("mathjax_reference_count"), int)
            or site.get("mathjax_reference_count", 0) <= 0
            or site.get("mathjax_urls") != [MATHJAX_URL]
            or site.get("consolidated_notice_path") != notice_path
        ):
            raise ValueError("release-toolchain rendered-site contract drifted")
        copied = site.get("copied_notice_sha256")
        if not isinstance(copied, Mapping) or set(copied) != {
            "bootstrap.js.LICENSE.txt",
            "fontawesome.js.LICENSE.txt",
        }:
            raise ValueError("release-toolchain copied site notices are incomplete")
        for name, site_digest in copied.items():
            record = files_by_path.get(f"_static/scripts/{name}")
            if record is None or record.get("sha256") != site_digest:
                raise ValueError("release-toolchain copied site notice is unbound")
        legal_record = files_by_path.get(notice_path)
        if legal_record is None or legal_record.get("sha256") != site.get(
            "consolidated_notice_sha256"
        ):
            raise ValueError("release-toolchain consolidated site notice is unbound")

    expected_system_toolchain = {
        "state": SYSTEM_TOOLCHAIN_STATE,
        "packages": [],
        "tools": [],
        "font_sources": [],
    }
    if parsed.get("system_toolchain") != expected_system_toolchain:
        raise ValueError("release-toolchain system inventory must be empty")

    if parsed.get("pdf_font_inventories") != []:
        raise ValueError("release-toolchain PDF inventory must be empty")

    if parsed.get("limitations") != list(INVENTORY_LIMITATIONS):
        raise ValueError("release-toolchain limitations are incomplete")
    generator = parsed.get("generator")
    if (
        not isinstance(generator, Mapping)
        or set(generator) != {"path", "sha256"}
        or generator.get("path") != "scripts/release_toolchain.py"
        or not _is_sha256(generator.get("sha256"))
    ):
        raise ValueError("release-toolchain generator binding is invalid")
    parsed["inventory_sha256"] = digest
    return parsed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--constraint", type=Path, default=DEFAULT_CONSTRAINT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify = subparsers.add_parser("verify-installed")
    verify.add_argument("--profile", choices=sorted(PROFILES), required=True)
    verify.add_argument("--require-ci-platform", action="store_true")

    emit = subparsers.add_parser("emit-inventory")
    emit.add_argument("--profile", choices=sorted(PROFILES), default="release")
    emit.add_argument("--require-ci-platform", action="store_true")
    emit.add_argument("--site-root", type=Path, action="append", default=[])
    emit.add_argument("--output", type=Path, required=True)

    check = subparsers.add_parser("verify-inventory")
    check.add_argument("--inventory", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    root = arguments.root.resolve()
    constraint = arguments.constraint.resolve()
    try:
        if arguments.command == "verify-installed":
            verify_installed(
                profile=arguments.profile,
                constraint=constraint,
                require_ci_platform=arguments.require_ci_platform,
            )
        elif arguments.command == "emit-inventory":
            output = arguments.output.expanduser()
            if output.exists() or output.is_symlink():
                raise ValueError("release-toolchain inventory output already exists")
            inventory = build_inventory(
                root=root,
                constraint=constraint,
                profile=arguments.profile,
                require_ci_platform=arguments.require_ci_platform,
                site_roots=arguments.site_root,
            )
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                json.dumps(inventory, ensure_ascii=False, sort_keys=True, indent=2)
                + "\n",
                encoding="utf-8",
            )
        elif arguments.command == "verify-inventory":
            verify_inventory(arguments.inventory, root=root, constraint=constraint)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"release toolchain blocked: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
