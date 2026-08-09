from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_verifier() -> ModuleType:
    path = ROOT / "scripts" / "verify_book_pdf.py"
    specification = importlib.util.spec_from_file_location("verify_book_pdf", path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules["verify_book_pdf"] = module
    specification.loader.exec_module(module)
    return module


def _manuscript(directory: Path, log: str | None) -> Path:
    pdf = directory / "handbook.pdf"
    pdf.write_bytes(b"%PDF-" + b"0" * 100_000)
    pdf.with_suffix(".tex").write_text("generated", encoding="utf-8")
    if log is not None:
        pdf.with_suffix(".log").write_text(log, encoding="utf-8")
    return pdf


def test_release_pdf_rejects_missing_latex_log(tmp_path: Path) -> None:
    module = _load_verifier()
    _manuscript(tmp_path, None)

    with pytest.raises(RuntimeError, match="compilation log is missing"):
        module.verify(tmp_path, require_latex_log=True)


@pytest.mark.parametrize(
    "warning",
    (
        "LaTeX Warning: Float too large for page by 36.18pt on input line 88.",
        "LaTeX Warning: There were undefined references.",
        "LaTeX Warning: Citation `missing' on page 2 undefined on input line 10.",
        "Missing character: There is no Ω in font cmr10!",
    ),
)
def test_release_pdf_rejects_broken_latex_output(
    tmp_path: Path,
    warning: str,
) -> None:
    module = _load_verifier()
    _manuscript(tmp_path, f"{warning}\nOutput written on handbook.pdf (2 pages).\n")

    with pytest.raises(RuntimeError, match="release-quality check failed"):
        module.verify(tmp_path, require_latex_log=True)


def test_release_pdf_accepts_clean_completed_log_and_searchable_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_verifier()
    pdf = _manuscript(
        tmp_path,
        "Output written on handbook.pdf (211 pages, 5000000 bytes).\n",
    )
    monkeypatch.setattr(module.shutil, "which", lambda name: f"/fake/{name}")
    extracted = " ".join(
        (
            "Data Envelopment Analysis",
            "Efficiency, Productivity, and Environmental Performance with Python",
            "A Unified Handbook of Theory, Methods, and Practice",
            "Designing a Credible DEA Study",
            "Third-Party Notices",
            "LPPL Version 1.3c",
            "Bitstream Vera Fonts Copyright",
            "account " * 10_000,
        )
    )

    def fake_run(command, **_kwargs):
        if command[0] == "/fake/pdfinfo":
            return SimpleNamespace(
                stdout=(
                    "Title:           Data Envelopment Analysis: Efficiency, "
                    "Productivity, and Environmental Performance with Python\n"
                )
            )
        return SimpleNamespace(stdout=extracted)

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    assert module.verify(tmp_path, require_latex_log=True) == pdf


def test_release_pdf_rejects_incorrect_metadata_title(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_verifier()
    _manuscript(tmp_path, "Output written on handbook.pdf (2 pages).\n")
    monkeypatch.setattr(module.shutil, "which", lambda name: f"/fake/{name}")
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(stdout="Title: Old title\n"),
    )

    with pytest.raises(RuntimeError, match="PDF metadata title is incorrect"):
        module.verify(tmp_path, require_latex_log=True)


def test_release_pdf_accepts_chinese_metadata_and_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_verifier()
    pdf = _manuscript(
        tmp_path,
        "Output written on handbook.pdf (211 pages, 5000000 bytes).\n",
    )
    monkeypatch.setattr(module.shutil, "which", lambda name: f"/fake/{name}")
    extracted = " ".join(
        (
            "数据包络分析",
            "基于 Python 的效率、生产率与环境绩效分析",
            "理论、方法与实践的统一手册",
            "第三方声明",
            "LPPL Version 1.3c",
            "Bitstream Vera Fonts Copyright",
            "绩效分析 " * 10_000,
        )
    )

    def fake_run(command, **_kwargs):
        if command[0] == "/fake/pdfinfo":
            return SimpleNamespace(
                stdout=(
                    "Title:           "
                    f"{module._PUBLICATION_CONTRACTS['zh_CN']['title']}\n"
                )
            )
        return SimpleNamespace(stdout=extracted)

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    assert module.verify(tmp_path, require_latex_log=True, language="zh_CN") == pdf
