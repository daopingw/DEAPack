#!/usr/bin/env python3
"""Localize reviewed human-readable labels inside Chinese Handbook equations."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from babel.messages.pofile import read_po, write_po

_MATH_TEXT = re.compile(r"\\text\{(?P<value>[^{}]*)\}")
_ENGLISH = re.compile(r"[A-Za-z]")
_TRANSLATIONS = {
    "and": "且",
    "as": "当",
    "can jointly produce": "可联合生产",
    "can jointly produce desirable output": "可联合生产合意产出",
    "can produce": "可生产",
    "constant returns supported:": "支持规模报酬不变：",  # noqa: RUF001
    "decreasing returns:": "规模报酬递减：",  # noqa: RUF001
    "for": "对于",
    "for desirable-output shortfall": "表示合意产出不足",
    "for input excess": "表示投入冗余",
    "for undesirable-output excess": "表示非合意产出过量",
    "increasing returns:": "规模报酬递增：",  # noqa: RUF001
    "input saving": "投入节约",
    "output addition": "产出增加",
    "productivity change": "生产率变化",
    "relative-price recovery": "相对价格回收",
    "remaining cost saving": "剩余成本节约",
    "s.t.": "约束条件",
    "satisfies": "满足",
    "some observed": "某个观测",
    "subject to": "约束条件",
    "total cost opportunity": "总成本节约空间",
    "proportional resource saving": "比例性资源节约",
    "under common-factor weak disposal": "在共同因子弱处置下",
    "under its strong-disposal counterpart": "在相应强处置下",
    "and undesirable output": "及非合意产出",
}


def _replace_label(match: re.Match[str], *, used: set[str]) -> str:
    value = match.group("value")
    leading = value[: len(value) - len(value.lstrip())]
    trailing = value[len(value.rstrip()) :]
    key = value.strip()
    if not _ENGLISH.search(key):
        return match.group(0)
    if key not in _TRANSLATIONS:
        raise RuntimeError(f"unreviewed English equation label: {key!r}")
    used.add(key)
    return rf"\text{{{leading}{_TRANSLATIONS[key]}{trailing}}}"


def expected_translation(source: str, current: str, *, used: set[str]) -> str:
    """Localize source-defined math labels inside an existing translation."""

    source_matches = list(_MATH_TEXT.finditer(source))
    target_matches = list(_MATH_TEXT.finditer(current))
    if len(source_matches) != len(target_matches):
        raise RuntimeError(
            "equation-label count changed between source and translation: "
            f"{len(source_matches)} != {len(target_matches)}"
        )
    replacements: list[tuple[int, int, str]] = []
    for source_match, target_match in zip(source_matches, target_matches, strict=True):
        replacement = _replace_label(source_match, used=used)
        replacements.append((target_match.start(), target_match.end(), replacement))
    localized = current
    for start, end, replacement in reversed(replacements):
        localized = f"{localized[:start]}{replacement}{localized[end:]}"
    return localized


def process_catalog(path: Path, *, check: bool, used: set[str]) -> int:
    """Localize or verify one PO catalog and return its changed-message count."""

    with path.open("rb") as stream:
        catalog = read_po(stream, locale="zh_CN")
    changed = 0
    for message in catalog:
        if (
            not message.id
            or not isinstance(message.id, str)
            or "\\text{" not in message.id
        ):
            continue
        if message.string is None or not isinstance(message.string, str):
            raise RuntimeError(f"missing singular translation in {path}")
        expected = expected_translation(message.id, message.string, used=used)
        if not any(
            _ENGLISH.search(match.group("value"))
            for match in _MATH_TEXT.finditer(message.id)
        ):
            continue
        if message.string == expected:
            continue
        if check:
            raise RuntimeError(f"stale equation labels in {path}: {message.id[:80]!r}")
        message.string = expected
        changed += 1
    if changed and not check:
        with path.open("wb") as stream:
            write_po(stream, catalog, width=79, sort_by_file=False)
    return changed


def run(locale_root: Path, *, check: bool) -> tuple[int, int]:
    """Process all catalogs and return ``(catalogs, changed_messages)``."""

    paths = sorted(locale_root.rglob("*.po"))
    if not paths:
        raise RuntimeError(f"no PO catalogs found under {locale_root}")
    used: set[str] = set()
    changed = sum(process_catalog(path, check=check, used=used) for path in paths)
    missing = sorted(set(_TRANSLATIONS).difference(used))
    if missing:
        raise RuntimeError(f"unused equation-label translations: {missing}")
    return len(paths), changed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "locale_root",
        nargs="?",
        type=Path,
        default=Path("book/locale/zh_CN/LC_MESSAGES"),
    )
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    catalogs, changed = run(arguments.locale_root, check=arguments.check)
    action = "verified" if arguments.check else "localized"
    print(
        f"Handbook equation labels {action}: {catalogs} catalogs; "
        f"{changed} changed message(s)"
    )


if __name__ == "__main__":
    main()
