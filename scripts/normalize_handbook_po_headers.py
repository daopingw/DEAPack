#!/usr/bin/env python3
"""Replace placeholder gettext metadata with a deterministic project header."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

_COMMENT = """# Simplified Chinese translation catalog for the DEAPack Handbook.
# Copyright (C) 2026, Daoping Wang and contributors
# The Handbook component license is pending maintainer approval; this catalog
# does not grant permission to redistribute otherwise uncleared material.
# Translation contributions remain credited in repository history.
#
"""


def _literal(value: str, path: Path) -> str:
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError) as error:
        raise ValueError(f"invalid PO header string in {path}: {value!r}") from error
    if not isinstance(parsed, str):
        raise ValueError(f"non-string PO header value in {path}")
    return parsed


def normalize(path: Path, *, revision_date: str) -> bool:
    """Normalize one catalog and return whether its bytes changed."""

    text = path.read_text(encoding="utf-8")
    marker = 'msgid ""\nmsgstr ""\n'
    start = text.find(marker)
    if start < 0:
        raise ValueError(f"gettext header not found in {path}")
    header_start = start + len(marker)
    lines = text[header_start:].splitlines(keepends=True)
    fragments: list[str] = []
    index = 0
    while index < len(lines) and lines[index].startswith('"'):
        fragments.append(_literal(lines[index].rstrip("\r\n"), path))
        index += 1
    if not fragments:
        raise ValueError(f"gettext metadata fields not found in {path}")

    fields: dict[str, str] = {}
    for line in "".join(fragments).splitlines():
        if ":" not in line:
            raise ValueError(f"malformed gettext metadata in {path}: {line!r}")
        key, value = line.split(":", maxsplit=1)
        fields[key] = value.lstrip()

    fields.update(
        {
            "Project-Id-Version": "DEAPack Handbook Preview 1",
            "Report-Msgid-Bugs-To": "https://github.com/daopingw/DEAPack/issues",
            "PO-Revision-Date": revision_date,
            "Last-Translator": "DEAPack contributors",
            "Language": "zh_CN",
            "Language-Team": "DEAPack Chinese Handbook contributors",
        }
    )
    order = (
        "Project-Id-Version",
        "Report-Msgid-Bugs-To",
        "POT-Creation-Date",
        "PO-Revision-Date",
        "Last-Translator",
        "Language",
        "Language-Team",
        "Plural-Forms",
        "MIME-Version",
        "Content-Type",
        "Content-Transfer-Encoding",
        "Generated-By",
    )
    missing = [key for key in order if key not in fields]
    if missing:
        raise ValueError(f"missing gettext metadata in {path}: {missing}")
    unknown = sorted(set(fields).difference(order))
    if unknown:
        raise ValueError(f"unreviewed gettext metadata in {path}: {unknown}")

    rendered_header = "".join(
        json.dumps(f"{key}: {fields[key]}\n", ensure_ascii=False) + "\n"
        for key in order
    )
    remainder = "".join(lines[index:])
    normalized = _COMMENT + marker + rendered_header + remainder
    if normalized == text:
        return False
    path.write_text(normalized, encoding="utf-8")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "locale_root",
        nargs="?",
        type=Path,
        default=Path("book/locale/zh_CN/LC_MESSAGES"),
    )
    parser.add_argument(
        "--revision-date",
        required=True,
        help="Reviewed PO-Revision-Date, including time-zone offset",
    )
    arguments = parser.parse_args()
    paths = sorted(arguments.locale_root.rglob("*.po"))
    if not paths:
        raise RuntimeError(f"no PO catalogs found under {arguments.locale_root}")
    changed = sum(
        normalize(path, revision_date=arguments.revision_date) for path in paths
    )
    print(f"normalized {changed} of {len(paths)} Handbook catalog header(s)")


if __name__ == "__main__":
    main()
