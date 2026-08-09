#!/usr/bin/env python3
"""Audit Handbook gettext catalogs without changing their translations."""

from __future__ import annotations

import argparse
import ast
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

_CITATION = re.compile(r"\{cite(?::[a-z]+)?\}`(?P<value>[^`]+)`")
_DOC_ROLE = re.compile(r"\{doc\}`(?P<value>[^`]+)`")
_INLINE_CODE = re.compile(r"(?<!`)`(?!`)(?P<value>[^`\n]+)(?<!`)`(?!`)")
_INLINE_MATH = re.compile(r"(?<!\$)\$(?!\$)(?P<value>.+?)(?<!\$)\$(?!\$)")
_URL = re.compile(r"https?://[^\s>)]+")
_CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
_ENGLISH_WORD = re.compile(r"\b[A-Za-z][A-Za-z'-]{2,}\b")
_LATEX_COMMAND = re.compile(r"\\[A-Za-z]+\*?")
_MATH_TEXT = re.compile(r"\\text\{(?P<value>[^{}]*)\}")
_HEADER_PLACEHOLDERS = (
    "SOME DESCRIPTIVE TITLE",
    "FIRST AUTHOR",
    "EMAIL@ADDRESS",
    "YEAR-MO-DA",
    "FULL NAME",
    "LL@li.org",
    "same license as",
)
_DISPLAY_MATH_COMMAND = re.compile(
    r"\\(?:begin|end|qquad|quad|mathcal|widehat|frac|sum|prod|geq|leq|in|top|left|right)\b"
)


@dataclass(frozen=True)
class POMessage:
    path: Path
    line: int
    msgid: str
    msgstr: str
    fuzzy: bool


@dataclass(frozen=True)
class TranslationReport:
    catalogs: int
    messages: int
    translated: int
    untranslated: int
    fuzzy: int
    header_errors: int
    invariant_errors: int
    prose_errors: int
    source_sync_errors: int

    @property
    def complete(self) -> bool:
        return not (
            self.untranslated
            or self.fuzzy
            or self.header_errors
            or self.invariant_errors
            or self.prose_errors
            or self.source_sync_errors
        )


def _po_literal(value: str, *, path: Path, line: int) -> str:
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError) as error:
        raise ValueError(f"invalid PO string at {path}:{line}: {value!r}") from error
    if not isinstance(parsed, str):
        raise ValueError(f"non-string PO value at {path}:{line}")
    return parsed


def _consume_field(
    lines: list[str],
    index: int,
    field: str,
    *,
    path: Path,
) -> tuple[str, int]:
    line = lines[index]
    prefix = f"{field} "
    if not line.startswith(prefix):
        raise ValueError(f"expected {field!r} at {path}:{index + 1}")
    fragments = [_po_literal(line[len(prefix) :], path=path, line=index + 1)]
    index += 1
    while index < len(lines) and lines[index].startswith('"'):
        fragments.append(_po_literal(lines[index], path=path, line=index + 1))
        index += 1
    return "".join(fragments), index


def parse_po(path: Path) -> list[POMessage]:
    """Parse the singular-message subset emitted by Sphinx/Babel."""

    lines = path.read_text(encoding="utf-8").splitlines()
    messages: list[POMessage] = []
    flags: set[str] = set()
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("#,"):
            flags.update(part.strip() for part in line[2:].split(","))
            index += 1
            continue
        if not line.startswith("msgid "):
            if not line.strip() and flags:
                flags.clear()
            index += 1
            continue

        start = index + 1
        msgid, index = _consume_field(lines, index, "msgid", path=path)
        if index >= len(lines) or not lines[index].startswith("msgstr "):
            raise ValueError(f"missing msgstr after {path}:{start}")
        msgstr, index = _consume_field(lines, index, "msgstr", path=path)
        if msgid:
            messages.append(
                POMessage(
                    path=path,
                    line=start,
                    msgid=msgid,
                    msgstr=msgstr,
                    fuzzy="fuzzy" in flags,
                )
            )
        flags.clear()
    return messages


def _doc_targets(text: str) -> Counter[str]:
    targets: Counter[str] = Counter()
    for match in _DOC_ROLE.finditer(text):
        value = match.group("value")
        if "<" in value and value.endswith(">"):
            value = value.rsplit("<", maxsplit=1)[1][:-1]
        targets[value] += 1
    return targets


def _invariant_contract(text: str) -> dict[str, Counter[str]]:
    without_roles = _CITATION.sub("", _DOC_ROLE.sub("", text))
    return {
        "citation": Counter(match.group("value") for match in _CITATION.finditer(text)),
        "document target": _doc_targets(text),
        "inline code": Counter(
            match.group("value") for match in _INLINE_CODE.finditer(without_roles)
        ),
        "inline math": Counter(
            _math_skeleton(match.group("value"))
            for match in _INLINE_MATH.finditer(text)
        ),
        "URL": Counter(_URL.findall(text)),
    }


def invariant_errors(message: POMessage) -> list[str]:
    """Return markup, citation, code, and mathematics preservation errors."""

    if not message.msgstr:
        return []
    errors: list[str] = []
    expected = _invariant_contract(message.msgid)
    observed = _invariant_contract(message.msgstr)
    for label, values in expected.items():
        if observed[label] != values:
            errors.append(f"{label} changed")
    if _is_display_math(message.msgid) and _math_skeleton(
        message.msgstr
    ) != _math_skeleton(message.msgid):
        errors.append("displayed mathematics changed outside text labels")
    source_labels = _MATH_TEXT.findall(message.msgid)
    target_labels = _MATH_TEXT.findall(message.msgstr)
    if len(source_labels) != len(target_labels):
        errors.append("mathematical text-label count changed")
    for source_label, target_label in zip(source_labels, target_labels, strict=False):
        if _ENGLISH_WORD.search(source_label) and source_label == target_label:
            errors.append(f"mathematical text label untranslated: {source_label!r}")
    return errors


def _math_skeleton(text: str) -> str:
    """Remove only human-readable ``\\text{...}`` labels from LaTeX."""

    return _MATH_TEXT.sub(r"\\text{__HANDBOOK_LABEL__}", text)


def _is_display_math(text: str) -> bool:
    """Recognize Sphinx-extracted display equations without source comments.

    Gettext catalogs do not retain the directive type as structured data.  A
    display equation is therefore identified conservatively from its LaTeX
    shape: an explicit environment, or a multiline expression beginning with
    a control sequence or containing several mathematical control sequences.
    Prose containing one inline command is intentionally not classified here.
    """

    source = text.strip()
    if "\\begin{" in source:
        return True
    commands = _DISPLAY_MATH_COMMAND.findall(source)
    if source.startswith("\\") and commands:
        return True
    return "\n" in source and len(commands) >= 2


def _requires_chinese_prose(message: POMessage) -> bool:
    source = message.msgid.strip()
    if _is_display_math(source) or source.startswith(("http://", "https://")):
        return False
    source = _CITATION.sub("", source)
    source = _DOC_ROLE.sub("", source)
    source = _INLINE_CODE.sub("", source)
    source = _INLINE_MATH.sub("", source)
    source = _LATEX_COMMAND.sub("", source)
    return len(_ENGLISH_WORD.findall(source)) >= 4


def source_sync_failures(
    locale_root: Path,
    template_root: Path,
) -> list[tuple[Path, str]]:
    """Compare active English gettext templates with maintained catalogs."""

    templates = sorted(template_root.rglob("*.pot"))
    if not templates:
        raise RuntimeError(f"no gettext templates found under {template_root}")

    failures: list[tuple[Path, str]] = []
    expected_catalogs: set[Path] = set()
    for template in templates:
        relative = template.relative_to(template_root).with_suffix(".po")
        catalog = locale_root / relative
        expected_catalogs.add(catalog.resolve())
        if not catalog.is_file():
            failures.append((catalog, "catalog missing for current English source"))
            continue

        template_ids = Counter(message.msgid for message in parse_po(template))
        catalog_ids = Counter(message.msgid for message in parse_po(catalog))
        missing = template_ids - catalog_ids
        stale = catalog_ids - template_ids
        for msgid, count in missing.items():
            failures.append(
                (catalog, f"missing current source message x{count}: {msgid[:90]!r}")
            )
        for msgid, count in stale.items():
            failures.append(
                (
                    catalog,
                    "active catalog message absent from source "
                    f"x{count}: {msgid[:90]!r}",
                )
            )

    allowed_extra = {(locale_root / "sphinx.po").resolve()}
    for catalog in sorted(locale_root.rglob("*.po")):
        resolved = catalog.resolve()
        if resolved not in expected_catalogs and resolved not in allowed_extra:
            failures.append((catalog, "catalog has no current English source template"))
    return failures


def audit(
    locale_root: Path,
    *,
    template_root: Path | None = None,
    require_complete: bool = False,
) -> TranslationReport:
    """Audit every Chinese Handbook catalog and print actionable failures."""

    paths = sorted(locale_root.rglob("*.po"))
    if not paths:
        raise RuntimeError(f"no PO catalogs found under {locale_root}")

    messages = [message for path in paths for message in parse_po(path)]
    header_failures = [
        (path, marker)
        for path in paths
        for marker in _HEADER_PLACEHOLDERS
        if marker in path.read_text(encoding="utf-8")
    ]
    untranslated = [message for message in messages if not message.msgstr]
    fuzzy = [message for message in messages if message.fuzzy]
    sync_failures = (
        []
        if template_root is None
        else source_sync_failures(locale_root, template_root)
    )
    preservation: list[tuple[POMessage, str]] = []
    prose: list[POMessage] = []
    for message in messages:
        preservation.extend((message, error) for error in invariant_errors(message))
        if (
            message.msgstr
            and _requires_chinese_prose(message)
            and _CJK.search(message.msgstr) is None
        ):
            prose.append(message)

    report = TranslationReport(
        catalogs=len(paths),
        messages=len(messages),
        translated=len(messages) - len(untranslated),
        untranslated=len(untranslated),
        fuzzy=len(fuzzy),
        header_errors=len(header_failures),
        invariant_errors=len(preservation),
        prose_errors=len(prose),
        source_sync_errors=len(sync_failures),
    )
    print(
        "Handbook zh_CN catalogs: "
        f"{report.catalogs} files; {report.translated}/{report.messages} translated; "
        f"{report.fuzzy} fuzzy; {report.header_errors} header errors; "
        f"{report.invariant_errors} invariant errors; "
        f"{report.prose_errors} untranslated-prose errors; "
        f"{report.source_sync_errors} source-sync errors"
    )
    for message in untranslated[:20]:
        print(f"UNTRANSLATED {message.path}:{message.line}: {message.msgid[:90]!r}")
    for message in fuzzy[:20]:
        print(f"FUZZY {message.path}:{message.line}: {message.msgid[:90]!r}")
    for path, marker in header_failures[:20]:
        print(f"HEADER {path}: placeholder or license inference {marker!r}")
    for message, error in preservation[:20]:
        print(f"INVARIANT {message.path}:{message.line}: {error}")
    for message in prose[:20]:
        print(f"NO-CHINESE-PROSE {message.path}:{message.line}: {message.msgid[:90]!r}")
    for path, error in sync_failures[:20]:
        print(f"SOURCE-SYNC {path}: {error}")

    if require_complete and not report.complete:
        raise RuntimeError("Chinese Handbook translation gate failed")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "locale_root",
        nargs="?",
        type=Path,
        default=Path("book/locale/zh_CN/LC_MESSAGES"),
    )
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument(
        "--template-root",
        type=Path,
        help="gettext POT tree built from the current canonical English source",
    )
    parser.add_argument("--json", type=Path, dest="json_path")
    arguments = parser.parse_args()
    report = audit(
        arguments.locale_root,
        template_root=arguments.template_root,
        require_complete=arguments.require_complete,
    )
    if arguments.json_path is not None:
        arguments.json_path.parent.mkdir(parents=True, exist_ok=True)
        arguments.json_path.write_text(
            json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
