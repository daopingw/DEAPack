#!/usr/bin/env python3
"""Verify the searchable text and release-critical layout log of the book PDF."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path

_LAYOUT_FAILURES = (
    re.compile(r"Float too large for page by", re.IGNORECASE),
    re.compile(r"There were undefined references", re.IGNORECASE),
    re.compile(r"Citation [`'].+?[`'] on page .+? undefined", re.IGNORECASE),
    re.compile(r"Missing character: There is no", re.IGNORECASE),
)

_PUBLICATION_CONTRACTS = {
    "en": {
        "title": (
            "Data Envelopment Analysis: Efficiency, Productivity, and "
            "Environmental Performance with Python"
        ),
        "required": (
            "Data Envelopment Analysis",
            "Efficiency, Productivity, and Environmental Performance with Python",
            "A Unified Handbook of Theory, Methods, and Practice",
            "Designing a Credible DEA Study",
            "Third-Party Notices",
            "LPPL Version 1.3c",
            "Bitstream Vera Fonts Copyright",
        ),
        "minimum_characters": 50_000,
    },
    "zh_CN": {
        "title": (
            "数据包络分析\N{FULLWIDTH COLON}基于 Python 的效率、生产率与环境绩效分析"
        ),
        "required": (
            "数据包络分析",
            "基于 Python 的效率、生产率与环境绩效分析",
            "理论、方法与实践的统一手册",
            "第三方声明",
            "LPPL Version 1.3c",
            "Bitstream Vera Fonts Copyright",
        ),
        "minimum_characters": 25_000,
    },
}


def _verify_latex_log(pdf: Path) -> None:
    """Reject a compiled manuscript whose LaTeX log records broken output."""

    log = pdf.with_suffix(".log")
    if not log.is_file():
        raise RuntimeError(f"LaTeX compilation log is missing: {log}")
    source = log.read_text(encoding="utf-8", errors="replace")
    failures = sorted(
        {
            line.strip()
            for line in source.splitlines()
            if any(pattern.search(line) for pattern in _LAYOUT_FAILURES)
        }
    )
    if failures:
        sample = "; ".join(failures[:5])
        suffix = f"; plus {len(failures) - 5} more" if len(failures) > 5 else ""
        raise RuntimeError(f"LaTeX release-quality check failed: {sample}{suffix}")
    if "Output written on" not in source:
        raise RuntimeError(f"LaTeX log does not record a completed PDF: {log}")


def _verify_pdf_metadata(
    pdf: Path,
    *,
    language: str,
    inspector: str = "pdfinfo",
) -> None:
    """Require the compiled PDF to expose the canonical bibliographic title."""

    executable = shutil.which(inspector)
    if executable is None:
        raise RuntimeError(
            f"{inspector!r} is required to verify the PDF metadata title; "
            "install poppler-utils (Linux) before running this target"
        )
    completed = subprocess.run(
        [executable, str(pdf)],
        check=True,
        capture_output=True,
        text=True,
    )
    match = re.search(r"^Title:\s*(?P<title>.+?)\s*$", completed.stdout, re.MULTILINE)
    title = match.group("title") if match is not None else None
    expected_title = _PUBLICATION_CONTRACTS[language]["title"]
    if title != expected_title:
        rendered = repr(title) if title is not None else "missing"
        raise RuntimeError(
            "PDF metadata title is incorrect: "
            f"expected {expected_title!r}; found {rendered}"
        )


def verify(
    directory: Path,
    *,
    extractor: str = "pdftotext",
    copy_to: Path | None = None,
    require_latex_log: bool = False,
    language: str = "en",
) -> Path:
    """Validate the single book PDF, its log, and its extracted text layer."""

    if language not in _PUBLICATION_CONTRACTS:
        raise ValueError(f"unsupported Handbook language: {language!r}")
    contract = _PUBLICATION_CONTRACTS[language]
    directory = directory.resolve()
    pdfs = sorted(directory.glob("*.pdf"))
    # Converted figure assets live beside the manuscript during compilation.
    manuscripts = [path for path in pdfs if path.with_suffix(".tex").exists()]
    if len(manuscripts) != 1:
        names = ", ".join(path.name for path in manuscripts) or "none"
        raise RuntimeError(f"expected one manuscript PDF in {directory}; found {names}")
    pdf = manuscripts[0]
    if pdf.stat().st_size < 100_000 or pdf.read_bytes()[:5] != b"%PDF-":
        raise RuntimeError(f"book PDF is missing or unexpectedly small: {pdf}")
    if require_latex_log:
        _verify_latex_log(pdf)

    _verify_pdf_metadata(pdf, language=language)

    executable = shutil.which(extractor)
    if executable is None:
        raise RuntimeError(
            f"{extractor!r} is required to verify the searchable text layer; "
            "install poppler-utils (Linux) before running this target"
        )
    completed = subprocess.run(
        [executable, "-enc", "UTF-8", str(pdf), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    text = re.sub(r"\s+", " ", completed.stdout).strip()
    required = contract["required"]
    missing = [phrase for phrase in required if phrase not in text]
    if len(text) < contract["minimum_characters"] or missing:
        details = f"; missing text: {', '.join(missing)}" if missing else ""
        raise RuntimeError(
            f"PDF text layer is incomplete ({len(text)} extracted characters){details}"
        )
    if copy_to is not None:
        copy_to = copy_to.resolve()
        copy_to.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(pdf, copy_to)
        pdf = copy_to
    print(f"verified searchable PDF: {pdf} ({len(text)} extracted characters)")
    return pdf


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("latex_directory", type=Path)
    parser.add_argument("--copy-to", type=Path)
    parser.add_argument(
        "--language", choices=sorted(_PUBLICATION_CONTRACTS), default="en"
    )
    arguments = parser.parse_args()
    verify(
        arguments.latex_directory,
        copy_to=arguments.copy_to,
        require_latex_log=True,
        language=arguments.language,
    )


if __name__ == "__main__":
    main()
