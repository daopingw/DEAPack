"""Verify and inventory the protected Python 3.12 release toolchain.

The constraint is intentionally a direct, cross-platform pin set rather than
a platform-specific wheel freeze.  The emitted JSON records the complete
resolved Python environment, copied HTML asset evidence, Linux package/tool
versions, and final-PDF font tables that produced a release candidate.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import shutil
import stat
import subprocess
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

APT_PACKAGES = (
    "fontconfig",
    "fonts-dejavu-core",
    "fonts-dejavu-mono",
    "fonts-noto-cjk",
    "fonts-texgyre",
    "latexmk",
    "librsvg2-bin",
    "poppler-utils",
    "tex-gyre",
    "texlive-fonts-recommended",
    "texlive-latex-extra",
    "texlive-latex-recommended",
    "texlive-lang-chinese",
    "texlive-xetex",
)
SYSTEM_TOOLS = (
    "fc-match",
    "fc-query",
    "kpsewhich",
    "latexmk",
    "pdffonts",
    "pdfinfo",
    "rsvg-convert",
    "xelatex",
)

INVENTORY_SCOPE = (
    "protected CPython 3.12 release lane; exact direct Python pins, resolved "
    "transitive Python distributions, complete rendered-site byte trees, "
    "Ubuntu/TeX/font source evidence, and final-PDF font tables"
)
INVENTORY_LIMITATIONS = (
    "This file is a resolved build record, not a hash-locked wheel lock.",
    (
        "Transitive Python packages are recorded but only reviewed direct "
        "pins are constrained."
    ),
    (
        "ubuntu-24.04 apt indexes and TeX/font packages are not "
        "snapshot-pinned; resolved package versions, Debian copyright-file "
        "hashes, executable hashes, resolver-selected font-file hashes, "
        "final PDF hashes, and pdffonts tables are recorded."
    ),
    (
        "The exact MathJax CDN URL is external at reader view time; MathJax "
        "bytes are not copied into the generated sites."
    ),
    (
        "Type 3 PDF glyph programs are recorded as PDF-contained programs; "
        "they have no external font-file resolver path."
    ),
    (
        "Ordinary DEAPack users retain the broader runtime ranges declared "
        "in pyproject.toml."
    ),
)

EXPECTED_MATHJAX_CONFIGURATION = ("docs/conf.py", "book/conf.py")
SITE_CONTRACTS: dict[str, tuple[int, str]] = {
    "_site/book/en": (33, "legal-notices.html"),
    "_site/book/zh_CN": (33, "legal-notices.html"),
    "_site/docs/en": (98, "legal/third-party-notices.html"),
}
PDF_CONTRACTS = (
    "output/review/2.0.0rc1/DEAPack-Handbook-Preview1-EN.pdf",
    "output/review/2.0.0rc1/DEAPack-Handbook-Preview1-ZH.pdf",
)

_FONTCONFIG_FAMILIES: dict[str, dict[str, object]] = {
    "fontconfig:dejavu-sans": {
        "request": "DejaVu Sans",
        "styles": ("regular", "bold", "oblique", "bold-oblique"),
        "license": "Bitstream-Vera",
        "packages": ("fonts-dejavu-core",),
        "notice_marker": "## DejaVu Sans and Sans Mono — retained font notices",
    },
    "fontconfig:dejavu-sans-mono": {
        "request": "DejaVu Sans Mono",
        "styles": ("regular", "bold", "oblique", "bold-oblique"),
        "license": "Bitstream-Vera",
        "packages": ("fonts-dejavu-core", "fonts-dejavu-mono"),
        "notice_marker": "## DejaVu Sans and Sans Mono — retained font notices",
    },
    "fontconfig:noto-sans-cjk-sc": {
        "request": "Noto Sans CJK SC",
        "styles": ("regular", "bold"),
        "license": "OFL-1.1",
        "packages": ("fonts-noto-cjk",),
        "notice_marker": "## Font Awesome webfonts and Noto CJK — SIL OFL 1.1",
    },
    "fontconfig:noto-serif-cjk-sc": {
        "request": "Noto Serif CJK SC",
        "styles": ("regular", "bold"),
        "license": "OFL-1.1",
        "packages": ("fonts-noto-cjk",),
        "notice_marker": "## Font Awesome webfonts and Noto CJK — SIL OFL 1.1",
    },
    "fontconfig:tex-gyre-heros": {
        "request": "TeX Gyre Heros",
        "styles": ("regular", "bold", "italic", "bold-italic"),
        "license": "GUST-FONT-LICENSE-1.0",
        "packages": ("fonts-texgyre", "tex-gyre"),
        "notice_marker": "## TeX Gyre Termes and Heros — GUST Font License",
    },
    "fontconfig:tex-gyre-termes": {
        "request": "TeX Gyre Termes",
        "styles": ("regular", "bold", "italic", "bold-italic"),
        "license": "GUST-FONT-LICENSE-1.0",
        "packages": ("fonts-texgyre", "tex-gyre"),
        "notice_marker": "## TeX Gyre Termes and Heros — GUST Font License",
    },
}

_FONTCONFIG_STYLE_CONTRACTS: dict[str, dict[str, object]] = {
    "regular": {
        "request_style": "Regular",
        "accepted_styles": ("regular", "book", "roman"),
    },
    "bold": {"request_style": "Bold", "accepted_styles": ("bold",)},
    "italic": {"request_style": "Italic", "accepted_styles": ("italic",)},
    "oblique": {"request_style": "Oblique", "accepted_styles": ("oblique",)},
    "bold-italic": {
        "request_style": "Bold Italic",
        "accepted_styles": ("bolditalic",),
    },
    "bold-oblique": {
        "request_style": "Bold Oblique",
        "accepted_styles": ("boldoblique",),
    },
}

FONTCONFIG_SOURCES: dict[str, dict[str, object]] = {
    f"{family_id}:{style_key}": {
        **family,
        "style_key": style_key,
        **_FONTCONFIG_STYLE_CONTRACTS[style_key],
    }
    for family_id, family in _FONTCONFIG_FAMILIES.items()
    for style_key in family["styles"]
}

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
    for relative in ("docs/conf.py", "book/conf.py"):
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


def _command_version(name: str, path: Path) -> str:
    commands = {
        "fc-match": [str(path), "-V"],
        "fc-query": [str(path), "-V"],
        "kpsewhich": [str(path), "--version"],
        "latexmk": [str(path), "-v"],
        "pdffonts": [str(path), "-v"],
        "pdfinfo": [str(path), "-v"],
        "rsvg-convert": [str(path), "--version"],
        "xelatex": [str(path), "--version"],
    }
    completed = subprocess.run(
        commands[name],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "LC_ALL": "C", "LANG": "C"},
    )
    output = "\n".join(item for item in (completed.stdout, completed.stderr) if item)
    first = next((line.strip() for line in output.splitlines() if line.strip()), "")
    if completed.returncode != 0 or not first:
        raise ValueError(f"cannot resolve version for system tool {name}")
    return first


def _package_record(package: str) -> dict[str, object]:
    completed = subprocess.run(
        ["dpkg-query", "-W", "-f=${Version}", package],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "LC_ALL": "C", "LANG": "C"},
    )
    if completed.returncode != 0 or not completed.stdout.strip():
        raise ValueError(f"required Ubuntu release package is missing: {package}")
    copyright_path = Path("/usr/share/doc") / package / "copyright"
    if not copyright_path.is_file():
        raise ValueError(f"Ubuntu package lacks copyright evidence: {package}")
    return {
        "name": package,
        "version": completed.stdout.strip(),
        "copyright_path": copyright_path.as_posix(),
        "copyright_sha256": _sha256_file(copyright_path),
    }


def _dpkg_file_evidence(path: Path) -> dict[str, object]:
    completed = subprocess.run(
        ["dpkg-query", "-S", path.as_posix()],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "LC_ALL": "C", "LANG": "C"},
    )
    candidates = []
    for line in completed.stdout.splitlines():
        if ": " not in line:
            continue
        package, claimed_path = line.split(": ", maxsplit=1)
        if Path(claimed_path).resolve() == path:
            candidates.append(package.split(",", maxsplit=1)[0])
    if completed.returncode != 0 or not candidates:
        raise ValueError(f"font file has no dpkg owner: {path}")
    binary_package = sorted(set(candidates))[0]
    package = binary_package.split(":", maxsplit=1)[0]
    version = subprocess.run(
        ["dpkg-query", "-W", "-f=${Version}", binary_package],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "LC_ALL": "C", "LANG": "C"},
    ).stdout.strip()
    copyright_path = Path("/usr/share/doc") / package / "copyright"
    if not version or not copyright_path.is_file():
        raise ValueError(f"font owner lacks version/copyright evidence: {package}")
    return {
        "package": package,
        "binary_package": binary_package,
        "package_version": version,
        "package_copyright_path": copyright_path.as_posix(),
        "package_copyright_sha256": _sha256_file(copyright_path),
    }


def _notice_binding(
    notice_sha256: str,
    marker: str,
    notice_payload: bytes,
) -> dict[str, str]:
    if marker.encode("utf-8") not in notice_payload:
        raise ValueError(f"consolidated notice lacks font marker: {marker}")
    return {
        "kind": "consolidated-notice",
        "path": "THIRD_PARTY_NOTICES.md",
        "sha256": notice_sha256,
        "marker": marker,
    }


def _fontconfig_source_records(
    *,
    notice_sha256: str,
    notice_payload: bytes,
) -> list[dict[str, object]]:
    fc_match = shutil.which("fc-match")
    fc_query = shutil.which("fc-query")
    if fc_match is None or fc_query is None:
        raise ValueError("fc-match and fc-query are required for font evidence")
    format_string = (
        "%{file}\\t%{index}\\t%{family}\\t%{style}\\t"
        "%{postscriptname}\\t%{fontversion}\\t%{fontformat}\\n"
    )
    records: list[dict[str, object]] = []
    for source_id, contract in sorted(FONTCONFIG_SOURCES.items()):
        request = str(contract["request"])
        request_style = str(contract["request_style"])
        matched = subprocess.run(
            [fc_match, "-f", format_string, f"{request}:style={request_style}"],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, "LC_ALL": "C", "LANG": "C"},
        ).stdout.splitlines()
        if len(matched) != 1:
            raise ValueError(f"fc-match did not select one face for {request}")
        match_fields = matched[0].split("\t")
        if len(match_fields) != 7 or not match_fields[0]:
            raise ValueError(f"fc-match returned incomplete evidence for {request}")
        match_path = Path(match_fields[0])
        realpath = match_path.resolve(strict=True)
        face_index = int(match_fields[1] or "0")
        queried = subprocess.run(
            [
                fc_query,
                "-i",
                str(face_index),
                "-f",
                format_string,
                realpath.as_posix(),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, "LC_ALL": "C", "LANG": "C"},
        ).stdout.splitlines()
        if len(queried) != 1:
            raise ValueError(f"fc-query did not bind one face for {request}")
        query_fields = queried[0].split("\t")
        if len(query_fields) != 7 or not query_fields[0]:
            raise ValueError(f"fc-query returned incomplete evidence for {request}")
        query_realpath = Path(query_fields[0]).resolve(strict=True)
        if query_realpath != realpath or int(query_fields[1] or "0") != face_index:
            raise ValueError(f"fc-match/fc-query disagreed for {request}")
        face_style = re.sub(r"[^a-z]", "", query_fields[3].casefold())
        accepted_styles = tuple(str(item) for item in contract["accepted_styles"])
        if face_style not in accepted_styles:
            raise ValueError(
                f"font {request} style {request_style} resolved to "
                f"unexpected face style {query_fields[3]!r}"
            )
        owner = _dpkg_file_evidence(realpath)
        allowed_packages = tuple(str(item) for item in contract["packages"])
        if owner["package"] not in allowed_packages:
            raise ValueError(
                f"font {request} resolved to unreviewed package {owner['package']}"
            )
        payload = _regular_bytes(realpath, limit=64 * 1024 * 1024)
        records.append(
            {
                "source_id": source_id,
                "resolver": "fontconfig",
                "request": request,
                "fc_match_path": match_path.as_posix(),
                "fc_query_path": Path(query_fields[0]).as_posix(),
                "realpath": realpath.as_posix(),
                "face_index": face_index,
                "family": query_fields[2],
                "style": query_fields[3],
                "postscript_name": query_fields[4],
                "font_version": query_fields[5],
                "format": query_fields[6],
                "size": len(payload),
                "sha256": _sha256_bytes(payload),
                "license": contract["license"],
                **owner,
                "license_binding": _notice_binding(
                    notice_sha256,
                    str(contract["notice_marker"]),
                    notice_payload,
                ),
            }
        )
    return records


def _type1_source_records(
    source_ids: Iterable[str],
    *,
    notice_sha256: str,
    notice_payload: bytes,
) -> list[dict[str, object]]:
    kpsewhich = shutil.which("kpsewhich")
    if kpsewhich is None:
        raise ValueError("kpsewhich is required for Type 1 font evidence")
    records: list[dict[str, object]] = []
    for source_id in sorted(set(source_ids)):
        if not source_id.startswith("kpsewhich:"):
            continue
        query = source_id.removeprefix("kpsewhich:")
        completed = subprocess.run(
            [kpsewhich, query],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, "LC_ALL": "C", "LANG": "C"},
        )
        lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
        if len(lines) != 1:
            raise ValueError(f"kpsewhich did not select one Type 1 file: {query}")
        realpath = Path(lines[0]).resolve(strict=True)
        payload = _regular_bytes(realpath, limit=16 * 1024 * 1024)
        owner = _dpkg_file_evidence(realpath)
        if query.startswith(("qtm", "qhv")):
            if owner["package"] not in {"fonts-texgyre", "tex-gyre"}:
                raise ValueError(
                    "TeX Gyre Type 1 font resolved to unreviewed package "
                    f"{owner['package']}"
                )
            license_name: str | None = "GUST-FONT-LICENSE-1.0"
            license_binding: dict[str, str] = _notice_binding(
                notice_sha256,
                "## TeX Gyre Termes and Heros — GUST Font License",
                notice_payload,
            )
        else:
            license_name = None
            license_binding = {
                "kind": "debian-package-copyright",
                "path": str(owner["package_copyright_path"]),
                "sha256": str(owner["package_copyright_sha256"]),
            }
        records.append(
            {
                "source_id": source_id,
                "resolver": "kpsewhich",
                "query": query,
                "realpath": realpath.as_posix(),
                "size": len(payload),
                "sha256": _sha256_bytes(payload),
                "license": license_name,
                **owner,
                "license_binding": license_binding,
            }
        )
    return records


def _system_inventory(
    *,
    root: Path,
    require: bool,
    pdf_records: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    if platform.system() != "Linux":
        if require:
            raise ValueError("system release-tool inventory requires Linux")
        return {
            "state": "not-collected-on-non-linux",
            "packages": [],
            "tools": [],
            "font_sources": [],
        }

    package_records: list[dict[str, object]] = []
    for package in APT_PACKAGES:
        try:
            package_records.append(_package_record(package))
        except ValueError:
            if require:
                raise

    tool_records: list[dict[str, str]] = []
    for name in SYSTEM_TOOLS:
        resolved = shutil.which(name)
        if resolved is None:
            if require:
                raise ValueError(f"required release tool is missing: {name}")
            continue
        path = Path(resolved).resolve(strict=True)
        tool_records.append(
            {
                "name": name,
                "path": path.as_posix(),
                "version": _command_version(name, path),
                "sha256": _sha256_file(path),
            }
        )
    notice_payload = _regular_bytes(root / "THIRD_PARTY_NOTICES.md")
    notice_sha256 = _sha256_bytes(notice_payload)
    font_sources: list[dict[str, object]] = []
    try:
        font_sources.extend(
            _fontconfig_source_records(
                notice_sha256=notice_sha256,
                notice_payload=notice_payload,
            )
        )
        referenced_source_ids = {
            str(row["source_id"])
            for pdf in pdf_records
            for row in pdf.get("pdffonts_rows", [])
            if isinstance(row, Mapping)
            and isinstance(row.get("source_id"), str)
            and str(row["source_id"]).startswith("kpsewhich:")
        }
        font_sources.extend(
            _type1_source_records(
                referenced_source_ids,
                notice_sha256=notice_sha256,
                notice_payload=notice_payload,
            )
        )
    except (OSError, ValueError, subprocess.SubprocessError):
        if require:
            raise
    return {
        "state": "resolved",
        "packages": package_records,
        "tools": tool_records,
        "font_sources": font_sources,
    }


def _type1_query(base_name: str, family: str) -> str:
    if family in {"tex-gyre-termes", "tex-gyre-heros"}:
        suffix = base_name.rsplit("-", maxsplit=1)[-1].lower()
        bold = "bold" in suffix
        italic = "italic" in suffix or "oblique" in suffix
        prefix = "qtm" if family == "tex-gyre-termes" else "qhv"
        ending = "bi" if bold and italic else "b" if bold else "ri" if italic else "r"
        return f"{prefix}{ending}.pfb"
    return f"{base_name.lower()}.pfb"


def _fontconfig_pdf_source(
    base_name: str,
    *,
    prefix: str,
    family: str,
    source_prefix: str,
) -> tuple[str, str]:
    """Map one PDF face name to its exact fontconfig face contract."""

    if not base_name.casefold().startswith(prefix.casefold()):
        raise ValueError(f"font face {base_name!r} does not match {prefix!r}")
    suffix = base_name[len(prefix) :].lstrip("-_. ")
    token = re.sub(r"[^a-z]", "", suffix.casefold())
    aliases = {
        "": "regular",
        "regular": "regular",
        "book": "regular",
        "roman": "regular",
        "bold": "bold",
        "italic": "italic",
        "oblique": "oblique",
        "bolditalic": "bold-italic",
        "boldoblique": "bold-oblique",
    }
    style_key = aliases.get(token)
    source_id = None if style_key is None else f"{source_prefix}:{style_key}"
    if source_id not in FONTCONFIG_SOURCES:
        raise ValueError(f"final PDF contains an unknown font face: {base_name}")
    return family, source_id


def _pdf_font_source(base_name: str, font_type: str) -> tuple[str, str]:
    folded = base_name.casefold()
    if base_name == "[none]" and font_type == "Type 3":
        return "pdf-contained-type3", "pdf-contained:type3"
    if folded.startswith("notoserifcjk"):
        return _fontconfig_pdf_source(
            base_name,
            prefix="NotoSerifCJKsc",
            family="noto-serif-cjk-sc",
            source_prefix="fontconfig:noto-serif-cjk-sc",
        )
    if folded.startswith("notosanscjk"):
        return _fontconfig_pdf_source(
            base_name,
            prefix="NotoSansCJKsc",
            family="noto-sans-cjk-sc",
            source_prefix="fontconfig:noto-sans-cjk-sc",
        )
    if folded.startswith("dejavusansmono"):
        return _fontconfig_pdf_source(
            base_name,
            prefix="DejaVuSansMono",
            family="dejavu-sans-mono",
            source_prefix="fontconfig:dejavu-sans-mono",
        )
    if folded.startswith("dejavusans"):
        return _fontconfig_pdf_source(
            base_name,
            prefix="DejaVuSans",
            family="dejavu-sans",
            source_prefix="fontconfig:dejavu-sans",
        )
    if folded.startswith("texgyretermes"):
        family = "tex-gyre-termes"
        source = (
            f"kpsewhich:{_type1_query(base_name, family)}"
            if font_type.startswith("Type 1")
            else _fontconfig_pdf_source(
                base_name,
                prefix="TeXGyreTermes",
                family=family,
                source_prefix="fontconfig:tex-gyre-termes",
            )[1]
        )
        return family, source
    if folded.startswith("texgyreheros"):
        family = "tex-gyre-heros"
        source = (
            f"kpsewhich:{_type1_query(base_name, family)}"
            if font_type.startswith("Type 1")
            else _fontconfig_pdf_source(
                base_name,
                prefix="TeXGyreHeros",
                family=family,
                source_prefix="fontconfig:tex-gyre-heros",
            )[1]
        )
        return family, source
    if re.fullmatch(
        r"(?:CM[A-Z]+|MSA[BM]|MSBM|TX[A-Z]*|T1X[A-Z]*|TCX[A-Z]*|SF[A-Z]*)\d*",
        base_name,
        flags=re.IGNORECASE,
    ):
        return "tex-type1-package-font", f"kpsewhich:{_type1_query(base_name, '')}"
    raise ValueError(f"final PDF contains an unknown font family: {base_name}")


def _parse_pdffonts_rows(output: str) -> list[dict[str, object]]:
    lines = [line.rstrip() for line in output.splitlines() if line.strip()]
    data_lines = lines[2:] if len(lines) >= 2 else []
    records: list[dict[str, object]] = []
    for line in data_lines:
        parts = line.split()
        if len(parts) < 9:
            raise ValueError(f"pdffonts returned an unparseable row: {line}")
        name = parts[0]
        font_type = " ".join(parts[1:-6])
        encoding, embedded, subset, unicode_map, object_id, generation = parts[-6:]
        if (
            not font_type
            or embedded != "yes"
            or not object_id.isdigit()
            or not generation.isdigit()
        ):
            raise ValueError(
                f"final PDF contains an unembedded or invalid font row: {line}"
            )
        if subset not in {"yes", "no"} or unicode_map not in {"yes", "no"}:
            raise ValueError(f"pdffonts returned invalid flags: {line}")
        base_name = re.sub(r"^[A-Z]{6}\+", "", name)
        family, source_id = _pdf_font_source(base_name, font_type)
        records.append(
            {
                "name": name,
                "base_name": base_name,
                "type": font_type,
                "encoding": encoding,
                "emb": embedded,
                "sub": subset,
                "uni": unicode_map,
                "object_id": int(object_id),
                "generation": int(generation),
                "family": family,
                "source_id": source_id,
            }
        )
    if not records:
        raise ValueError("final PDF pdffonts inventory is empty")
    return records


def _pdf_font_record(root: Path, path: Path) -> dict[str, object]:
    resolved = path.resolve(strict=True)
    if _regular_bytes(resolved, limit=256 * 1024 * 1024)[:5] != b"%PDF-":
        raise ValueError(f"font inventory input is not a PDF: {path}")
    pdffonts = shutil.which("pdffonts")
    if pdffonts is None:
        raise ValueError("pdffonts is required for final-PDF font inventory")
    completed = subprocess.run(
        [pdffonts, str(resolved)],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
        env={**os.environ, "LC_ALL": "C", "LANG": "C"},
    )
    if completed.returncode != 0 or "name" not in completed.stdout.lower():
        raise ValueError(f"pdffonts could not inspect {path}")
    rows = _parse_pdffonts_rows(completed.stdout)
    try:
        label = resolved.relative_to(root.resolve()).as_posix()
    except ValueError:
        label = resolved.as_posix()
    return {
        "path": label,
        "pdf_sha256": _sha256_file(resolved),
        "pdffonts_output_sha256": _sha256_bytes(completed.stdout.encode("utf-8")),
        "font_families": sorted({str(row["family"]) for row in rows}),
        "font_source_ids": sorted({str(row["source_id"]) for row in rows}),
        "pdffonts_rows": rows,
    }


def build_inventory(
    *,
    root: Path,
    constraint: Path,
    profile: str,
    require_ci_platform: bool,
    require_system_tools: bool,
    site_roots: Iterable[Path],
    pdfs: Iterable[Path],
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
    pdf_records = sorted(
        (_pdf_font_record(root, path) for path in pdfs),
        key=lambda item: str(item["path"]),
    )
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
        "system_toolchain": _system_inventory(
            root=root,
            require=require_system_tools,
            pdf_records=pdf_records,
        ),
        "pdf_font_inventories": pdf_records,
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
    if (
        set(observed_mathjax) != set(EXPECTED_MATHJAX_CONFIGURATION)
        or len(observed_mathjax) != 2
    ):
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
    if set(observed_sites) != set(SITE_CONTRACTS) or len(observed_sites) != 3:
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

    system = parsed.get("system_toolchain")
    if (
        not isinstance(system, Mapping)
        or set(system)
        != {
            "state",
            "packages",
            "tools",
            "font_sources",
        }
        or system.get("state") != "resolved"
    ):
        raise ValueError("release-toolchain system inventory is invalid")
    packages = system.get("packages")
    package_map = (
        {item.get("name"): item for item in packages if isinstance(item, Mapping)}
        if isinstance(packages, list)
        else {}
    )
    if set(package_map) != set(APT_PACKAGES) or len(package_map) != len(APT_PACKAGES):
        raise ValueError("release-toolchain Ubuntu package inventory is incomplete")
    for name, item in package_map.items():
        if (
            not isinstance(item.get("version"), str)
            or not item.get("version")
            or item.get("copyright_path") != f"/usr/share/doc/{name}/copyright"
            or not _is_sha256(item.get("copyright_sha256"))
        ):
            raise ValueError("release-toolchain Ubuntu package evidence is invalid")
    tools = system.get("tools")
    tool_map = (
        {item.get("name"): item for item in tools if isinstance(item, Mapping)}
        if isinstance(tools, list)
        else {}
    )
    if set(tool_map) != set(SYSTEM_TOOLS) or len(tool_map) != len(SYSTEM_TOOLS):
        raise ValueError("release-toolchain system tool inventory is incomplete")
    for item in tool_map.values():
        if (
            not isinstance(item.get("path"), str)
            or not str(item.get("path")).startswith("/")
            or not isinstance(item.get("version"), str)
            or not item.get("version")
            or not _is_sha256(item.get("sha256"))
        ):
            raise ValueError("release-toolchain system tool evidence is invalid")
    font_sources = system.get("font_sources")
    source_map = (
        {
            item.get("source_id"): item
            for item in font_sources
            if isinstance(item, Mapping)
        }
        if isinstance(font_sources, list)
        else {}
    )
    if not set(FONTCONFIG_SOURCES).issubset(source_map) or len(source_map) != len(
        font_sources if isinstance(font_sources, list) else []
    ):
        raise ValueError("release-toolchain font source ledger is incomplete")
    notice_sha256 = str(notice_source["sha256"])
    for source_id, contract in FONTCONFIG_SOURCES.items():
        item = source_map[source_id]
        binding = item.get("license_binding")
        if (
            not {
                "source_id",
                "resolver",
                "request",
                "fc_match_path",
                "fc_query_path",
                "realpath",
                "face_index",
                "family",
                "style",
                "postscript_name",
                "font_version",
                "format",
                "size",
                "sha256",
                "license",
                "package",
                "binary_package",
                "package_version",
                "package_copyright_path",
                "package_copyright_sha256",
                "license_binding",
            }.issubset(item)
            or item.get("resolver") != "fontconfig"
            or item.get("request") != contract["request"]
            or item.get("license") != contract["license"]
            or item.get("package") not in contract["packages"]
            or re.sub(r"[^a-z]", "", str(item.get("style", "")).casefold())
            not in contract["accepted_styles"]
            or not isinstance(item.get("face_index"), int)
            or item.get("face_index", -1) < 0
            or not _is_sha256(item.get("sha256"))
            or not isinstance(item.get("size"), int)
            or item.get("size", 0) <= 0
            or not all(
                isinstance(item.get(field), str) and item.get(field)
                for field in (
                    "fc_match_path",
                    "fc_query_path",
                    "realpath",
                    "family",
                    "style",
                    "format",
                    "binary_package",
                    "package_version",
                    "package_copyright_path",
                )
            )
            or not isinstance(item.get("postscript_name"), str)
            or not isinstance(item.get("font_version"), str)
            or not _is_sha256(item.get("package_copyright_sha256"))
            or not isinstance(binding, Mapping)
            or binding.get("kind") != "consolidated-notice"
            or binding.get("path") != "THIRD_PARTY_NOTICES.md"
            or binding.get("sha256") != notice_sha256
            or binding.get("marker") != contract["notice_marker"]
        ):
            raise ValueError("release-toolchain fontconfig source is invalid")
    for source_id, item in source_map.items():
        if not str(source_id).startswith("kpsewhich:"):
            continue
        binding = item.get("license_binding")
        query = str(source_id).removeprefix("kpsewhich:")
        if (
            not {
                "source_id",
                "resolver",
                "query",
                "realpath",
                "size",
                "sha256",
                "license",
                "package",
                "binary_package",
                "package_version",
                "package_copyright_path",
                "package_copyright_sha256",
                "license_binding",
            }.issubset(item)
            or item.get("resolver") != "kpsewhich"
            or item.get("query") != query
            or not str(item.get("query")).endswith(".pfb")
            or not isinstance(item.get("realpath"), str)
            or not str(item.get("realpath")).startswith("/")
            or not _is_sha256(item.get("sha256"))
            or not isinstance(item.get("size"), int)
            or item.get("size", 0) <= 0
            or not all(
                isinstance(item.get(field), str) and item.get(field)
                for field in (
                    "package",
                    "binary_package",
                    "package_version",
                    "package_copyright_path",
                )
            )
            or not _is_sha256(item.get("package_copyright_sha256"))
            or not isinstance(binding, Mapping)
        ):
            raise ValueError("release-toolchain Type 1 font source is invalid")
        if query.startswith(("qtm", "qhv")):
            if (
                item.get("license") != "GUST-FONT-LICENSE-1.0"
                or item.get("package") not in {"fonts-texgyre", "tex-gyre"}
                or binding.get("kind") != "consolidated-notice"
                or binding.get("path") != "THIRD_PARTY_NOTICES.md"
                or binding.get("sha256") != notice_sha256
                or binding.get("marker")
                != "## TeX Gyre Termes and Heros — GUST Font License"
            ):
                raise ValueError("release-toolchain Type 1 notice binding is invalid")
        elif (
            binding.get("kind") != "debian-package-copyright"
            or binding.get("path") != item.get("package_copyright_path")
            or binding.get("sha256") != item.get("package_copyright_sha256")
        ):
            raise ValueError("release-toolchain Type 1 package binding is invalid")

    pdfs = parsed.get("pdf_font_inventories")
    pdf_map = (
        {item.get("path"): item for item in pdfs if isinstance(item, Mapping)}
        if isinstance(pdfs, list)
        else {}
    )
    if set(pdf_map) != set(PDF_CONTRACTS) or len(pdf_map) != 2:
        raise ValueError("release-toolchain final-PDF inventory set is incomplete")
    for path, pdf in pdf_map.items():
        rows = pdf.get("pdffonts_rows")
        if (
            not _is_sha256(pdf.get("pdf_sha256"))
            or not _is_sha256(pdf.get("pdffonts_output_sha256"))
            or not isinstance(rows, list)
            or not rows
        ):
            raise ValueError("release-toolchain final-PDF font inventory is invalid")
        families: set[str] = set()
        source_ids: set[str] = set()
        for row in rows:
            if not isinstance(row, Mapping) or set(row) != {
                "name",
                "base_name",
                "type",
                "encoding",
                "emb",
                "sub",
                "uni",
                "object_id",
                "generation",
                "family",
                "source_id",
            }:
                raise ValueError("release-toolchain final-PDF font row is incomplete")
            if row.get("emb") != "yes":
                raise ValueError("release-toolchain final-PDF font is not embedded")
            name = row.get("name")
            base_name = row.get("base_name")
            font_type = row.get("type")
            if (
                not isinstance(name, str)
                or not name
                or not isinstance(base_name, str)
                or base_name != re.sub(r"^[A-Z]{6}\+", "", name)
                or not isinstance(font_type, str)
                or not font_type
                or not isinstance(row.get("encoding"), str)
                or not row.get("encoding")
                or row.get("sub") not in {"yes", "no"}
                or row.get("uni") not in {"yes", "no"}
                or not isinstance(row.get("object_id"), int)
                or row.get("object_id", -1) < 0
                or not isinstance(row.get("generation"), int)
                or row.get("generation", -1) < 0
            ):
                raise ValueError("release-toolchain final-PDF font row is invalid")
            family, source_id = _pdf_font_source(base_name, font_type)
            if row.get("family") != family or row.get("source_id") != source_id:
                raise ValueError("release-toolchain final-PDF font mapping is invalid")
            families.add(family)
            source_ids.add(source_id)
        if pdf.get("font_families") != sorted(families) or pdf.get(
            "font_source_ids"
        ) != sorted(source_ids):
            raise ValueError("release-toolchain final-PDF font summary is invalid")
        unresolved = source_ids - set(source_map) - {"pdf-contained:type3"}
        if unresolved:
            raise ValueError(
                f"release-toolchain PDF font sources are unbound: {unresolved}"
            )
        if path.endswith("-EN.pdf") and not any(
            source.startswith("kpsewhich:") for source in source_ids
        ):
            raise ValueError("English PDF lacks kpsewhich Type 1 source evidence")

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
    emit.add_argument("--require-system-tools", action="store_true")
    emit.add_argument("--site-root", type=Path, action="append", default=[])
    emit.add_argument("--pdf", type=Path, action="append", default=[])
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
                require_system_tools=arguments.require_system_tools,
                site_roots=arguments.site_root,
                pdfs=arguments.pdf,
            )
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                json.dumps(inventory, ensure_ascii=False, sort_keys=True, indent=2)
                + "\n",
                encoding="utf-8",
            )
        elif arguments.command == "verify-inventory":
            verify_inventory(arguments.inventory, root=root, constraint=constraint)
    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
        subprocess.SubprocessError,
    ) as error:
        print(f"release toolchain blocked: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
