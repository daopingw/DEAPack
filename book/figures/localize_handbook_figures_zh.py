"""Generate reviewed Simplified-Chinese variants of selected Handbook SVGs.

The explicit JSON catalog is the editorial record.  This script only applies
those exact substitutions, validates source hashes and protected tokens, and
writes deterministic SVG variants under ``_static/figures/zh_CN``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from xml.dom import Node, minidom

BOOK_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = Path(__file__).with_name("zh_CN_labels.json")
DEFAULT_SOURCE_DIR = BOOK_ROOT / "_static" / "figures"
DEFAULT_OUTPUT_DIR = DEFAULT_SOURCE_DIR / "zh_CN"
TEXT_ELEMENTS = {"text", "tspan", "title", "desc"}
PROTECTED_PATTERNS = (
    re.compile(r"(?<![\w.])\d+(?:\.\d+)?%?(?![\w.])"),
    re.compile(r"(?<![A-Za-z])(?:DEA|DMU|VRS|CRS|FDH|SBM|DDF|BCC)(?![A-Za-z])"),
    re.compile(
        r"(?<![A-Za-z])(?:Lakeside|North|East|West)(?![A-Za-z])",
        re.IGNORECASE,
    ),
    re.compile(r"(?<![A-Za-z0-9])(?:R/C|R\s*-\s*C|λ|→|↑|↓)(?![A-Za-z0-9])"),
)
FONT_SUBSTITUTIONS = {
    "'DejaVu Sans'": (
        "'Noto Sans CJK SC', 'Source Han Sans SC', 'Microsoft YaHei', "
        "'PingFang SC', 'DejaVu Sans'"
    ),
    "Arial, Helvetica, sans-serif": (
        "Noto Sans CJK SC, Source Han Sans SC, Microsoft YaHei, "
        "PingFang SC, Arial, Helvetica, sans-serif"
    ),
}


class CatalogError(RuntimeError):
    """Raised when source SVGs and the reviewed label catalog disagree."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _protected_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    for pattern in PROTECTED_PATTERNS:
        tokens.extend(match.group(0).casefold() for match in pattern.finditer(text))
    return sorted(tokens)


def _replace_preserving_outer_space(value: str, replacement: str) -> str:
    leading = value[: len(value) - len(value.lstrip())]
    trailing = value[len(value.rstrip()) :]
    return f"{leading}{replacement}{trailing}"


def _load_catalog(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise CatalogError(f"unsupported catalog schema in {path}")
    files = payload.get("files")
    if not isinstance(files, dict) or not files:
        raise CatalogError(f"catalog has no figure records: {path}")
    return payload


def _localize_font_attributes(document: minidom.Document) -> None:
    for element in document.getElementsByTagName("*"):
        for name in tuple(element.attributes.keys()):
            value = element.getAttribute(name)
            localized = value
            for source, target in FONT_SUBSTITUTIONS.items():
                localized = localized.replace(source, target)
            if localized != value:
                element.setAttribute(name, localized)


def _localize_svg(
    source: bytes, record: dict[str, Any], name: str
) -> tuple[bytes, int]:
    document = minidom.parseString(source)
    translations = record.get("translations", {})
    preserve = set(record.get("preserve", []))
    if not isinstance(translations, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in translations.items()
    ):
        raise CatalogError(f"{name}: translations must be a string mapping")
    if not all(isinstance(value, str) for value in preserve):
        raise CatalogError(f"{name}: preserve must contain strings")

    overlap = set(translations) & preserve
    if overlap:
        raise CatalogError(
            f"{name}: labels appear in both translation and preserve: {overlap}"
        )

    used_translations: set[str] = set()
    used_preserve: set[str] = set()
    replacements = 0
    for element in document.getElementsByTagName("*"):
        local_name = element.localName or element.tagName.split(":")[-1]
        if local_name not in TEXT_ELEMENTS:
            continue
        for child in element.childNodes:
            if child.nodeType not in {Node.TEXT_NODE, Node.CDATA_SECTION_NODE}:
                continue
            source_label = child.data.strip()
            if not source_label:
                continue
            if source_label in translations:
                target_label = translations[source_label]
                expected = _protected_tokens(source_label)
                observed = _protected_tokens(target_label)
                if observed != expected:
                    raise CatalogError(
                        f"{name}: protected tokens changed for {source_label!r}: "
                        f"{expected!r} != {observed!r}"
                    )
                child.data = _replace_preserving_outer_space(child.data, target_label)
                used_translations.add(source_label)
                replacements += 1
            elif source_label in preserve:
                used_preserve.add(source_label)
            else:
                raise CatalogError(
                    f"{name}: visible label is neither translated nor preserved: "
                    f"{source_label!r}"
                )

    unused_translations = set(translations) - used_translations
    unused_preserve = preserve - used_preserve
    if unused_translations or unused_preserve:
        raise CatalogError(
            f"{name}: unused catalog labels; "
            f"translations={sorted(unused_translations)!r}, "
            f"preserve={sorted(unused_preserve)!r}"
        )

    _localize_font_attributes(document)
    marker = document.createComment(
        " Generated from the English SVG by figures/localize_handbook_figures_zh.py; "
        "do not edit this file directly. "
    )
    document.insertBefore(marker, document.documentElement)
    rendered = document.toxml(encoding="utf-8")
    if not rendered.endswith(b"\n"):
        rendered += b"\n"
    return rendered, replacements


def generate(
    catalog_path: Path,
    source_dir: Path,
    output_dir: Path,
    *,
    check: bool,
) -> list[tuple[str, int, str]]:
    """Generate or verify every catalogued SVG and return stable diagnostics."""

    payload = _load_catalog(catalog_path)
    records: dict[str, Any] = payload["files"]
    expected_names = sorted(records)
    diagnostics: list[tuple[str, int, str]] = []
    for name in expected_names:
        record = records[name]
        source_path = source_dir / name
        output_path = output_dir / name
        if not source_path.is_file():
            raise CatalogError(f"missing source SVG: {source_path}")
        source = source_path.read_bytes()
        source_hash = _sha256(source)
        if source_hash != record.get("source_sha256"):
            raise CatalogError(
                f"{name}: source changed; expected {record.get('source_sha256')}, "
                f"found {source_hash}. Review labels before updating the catalog hash."
            )
        localized, replacements = _localize_svg(source, record, name)
        localized_hash = _sha256(localized)
        if check:
            if not output_path.is_file():
                raise CatalogError(f"missing generated SVG: {output_path}")
            if output_path.read_bytes() != localized:
                raise CatalogError(f"stale generated SVG: {output_path}")
        else:
            output_dir.mkdir(parents=True, exist_ok=True)
            if not output_path.is_file() or output_path.read_bytes() != localized:
                output_path.write_bytes(localized)
        diagnostics.append((name, replacements, localized_hash))
    return diagnostics


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when a generated SVG is missing or stale; do not write files",
    )
    return parser.parse_args()


def main() -> int:
    arguments = _arguments()
    diagnostics = generate(
        arguments.catalog.resolve(),
        arguments.source_dir.resolve(),
        arguments.output_dir.resolve(),
        check=arguments.check,
    )
    mode = "verified" if arguments.check else "generated"
    for name, replacements, digest in diagnostics:
        print(f"{mode}: {name}: labels={replacements}: sha256={digest}")
    print(f"Chinese Handbook SVGs {mode}: {len(diagnostics)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
