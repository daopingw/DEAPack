from __future__ import annotations

import hashlib
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import get_type_hints

import pandas as pd
import pytest

from deapack import (
    BCCInput,
    DEAData,
    DEAResult,
    PublicationBundleNotAvailableError,
    publish_result,
)
from deapack.reporting import publish_result as reporting_publish_result
from deapack.solvers.scipy_highs import SciPyHiGHSMILPSolver, SciPyHiGHSSolver


def _radial_result() -> DEAResult:
    frame = pd.DataFrame(
        {
            "dmu": list("ABCDEFGH"),
            "input": [1.0, 2.0, 3.0, 4.0, 2.0, 3.0, 4.0, 3.5],
            "output": [1.0, 2.5, 3.3, 3.8, 1.5, 2.0, 2.8, 3.0],
        }
    )
    data = DEAData.from_frame(frame, dmu="dmu", inputs="input", outputs="output")
    return BCCInput().fit(data)


def _outer_payloads(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def _audit_payloads(outer: dict[str, bytes]) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(outer["audit/result-audit.zip"])) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def _require_matplotlib() -> None:
    pytest.importorskip("matplotlib")


def _panel_result(period_count: int = 5) -> DEAResult:
    periods = list(range(2020, 2020 + period_count))
    values = [0.8 + position * 0.01 for position in range(period_count)]
    return DEAResult(
        pd.DataFrame(
            {
                "dmu_id": ["A"] * period_count,
                "period": periods,
                "score": values,
                "efficiency": values,
                "distance": [pd.NA] * period_count,
                "is_efficient": [False] * period_count,
                "solver_status": ["optimal"] * period_count,
                "model_family": ["test_panel"] * period_count,
            }
        ),
        metadata={"method_id": "test.panel"},
    )


def test_public_api_exports_and_runtime_return_hint() -> None:
    assert publish_result is reporting_publish_result
    assert issubclass(PublicationBundleNotAvailableError, ValueError)
    assert get_type_hints(DEAResult.publish)["return"] is Path
    assert get_type_hints(publish_result)["result"] is object


def test_publication_rejects_result_subclasses_before_calling_extension_hooks(
    tmp_path: Path,
) -> None:
    source = _radial_result()
    calls: list[str] = []

    class ExtensionResult(DEAResult):
        def available_plots(self):  # type: ignore[no-untyped-def]
            calls.append("available_plots")
            raise AssertionError("untrusted extension hook was called")

        def plot(self, *args: object, **kwargs: object):  # type: ignore[no-untyped-def]
            del args, kwargs
            calls.append("plot")
            raise AssertionError("untrusted extension hook was called")

    extension = ExtensionResult(
        summary_frame=source.summary(),
        metadata=source.metadata,
    )

    with pytest.raises(
        PublicationBundleNotAvailableError,
        match="exact built-in DEAResult",
    ):
        publish_result(extension, tmp_path / "extension.zip")

    assert calls == []
    assert not (tmp_path / "extension.zip").exists()


def test_one_call_publication_contains_figures_complete_audit_and_hashes(
    tmp_path: Path,
) -> None:
    _require_matplotlib()
    result = _radial_result()

    destination = result.publish(tmp_path / "study-publication.zip")
    outer = _outer_payloads(destination)
    manifest = json.loads(outer["manifest.json"])
    audit = _audit_payloads(outer)

    assert destination == tmp_path / "study-publication.zip"
    assert {
        "README.txt",
        "index.html",
        "manifest.json",
        "audit/result-audit.zip",
        "figures/performance.svg",
        "figures/frontier.svg",
    }.issubset(outer)
    assert {
        "README.txt",
        "report.html",
        "metadata.json",
        "manifest.json",
        "tables/summary.csv",
        "tables/summary.jsonl",
        "tables/targets.csv",
        "tables/targets.jsonl",
    }.issubset(audit)
    assert manifest["publication_schema_version"] == 1
    assert manifest["audit"]["complete_existing_audit_bundle"] is True
    assert manifest["semantics"] == {
        "additional_solver_calls": 0,
        "additional_solver_calls_scope": (
            "deapack_publication_exporter_on_exact_dearesult"
        ),
        "causal_claim": False,
        "plot_discovery": "DEAResult.available_plots",
        "prescriptive_claim": False,
        "selected_target_uniqueness_claim": False,
        "source": "public_result_snapshot_v1",
        "third_party_result_extensions_supported": False,
        "trusted_result_type": "deapack.results.DEAResult",
    }
    assert manifest["integrity"] == {
        "algorithm": "sha256",
        "authenticity_claim": False,
        "scope": "all_archive_members_except_manifest.json",
    }
    for record in manifest["files"]:
        payload = outer[record["path"]]
        assert record["bytes"] == len(payload)
        assert record["sha256"] == hashlib.sha256(payload).hexdigest()

    audit_manifest = json.loads(audit["manifest.json"])
    for record in audit_manifest["files"]:
        assert record["sha256"] == hashlib.sha256(audit[record["path"]]).hexdigest()


def test_manifest_records_every_registered_plot_and_selection_reason(
    tmp_path: Path,
) -> None:
    _require_matplotlib()
    result = _radial_result()

    default = _outer_payloads(result.publish(tmp_path / "default.zip"))
    selected = _outer_payloads(result.publish(tmp_path / "selected.zip", dmu_id="E"))
    default_plots = {
        item["kind"]: item for item in json.loads(default["manifest.json"])["plots"]
    }
    selected_plots = {
        item["kind"]: item for item in json.loads(selected["manifest.json"])["plots"]
    }

    assert set(default_plots) == {
        "performance",
        "frontier",
        "trajectory",
        "process",
        "improvement",
        "metafrontier",
        "references",
    }
    assert default_plots["performance"]["included"] is True
    assert default_plots["improvement"] == {
        "backend": "matplotlib",
        "description": default_plots["improvement"]["description"],
        "included": False,
        "kind": "improvement",
        "path": None,
        "reason": "requires_explicit_dmu_id",
        "skipped": True,
        "title": "Variable-specific operating plan",
    }
    assert selected_plots["improvement"]["included"] is True
    assert selected_plots["improvement"]["path"] == "figures/improvement.svg"


def test_publication_uses_only_result_declared_available_plots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _require_matplotlib()
    result = _radial_result()
    performance = next(
        info for info in result.available_plots() if info.kind == "performance"
    )
    monkeypatch.setattr(DEAResult, "available_plots", lambda self: (performance,))

    payloads = _outer_payloads(result.publish(tmp_path / "declared-only.zip"))
    manifest = json.loads(payloads["manifest.json"])

    assert "figures/performance.svg" in payloads
    assert not any(
        name.startswith("figures/") and name != "figures/performance.svg"
        for name in payloads
    )
    for record in manifest["plots"]:
        if record["kind"] != "performance":
            assert record["included"] is False
            assert record["reason"] == (
                "not_declared_applicable_by_result_available_plots"
            )


def test_multi_period_performance_requires_a_period_only_beyond_safe_facets(
    tmp_path: Path,
) -> None:
    _require_matplotlib()
    result = _panel_result()

    default = json.loads(
        _outer_payloads(result.publish(tmp_path / "panel-default.zip"))["manifest.json"]
    )
    selected_path = result.publish(tmp_path / "panel-2024.zip", period=2024)
    selected = json.loads(_outer_payloads(selected_path)["manifest.json"])
    default_performance = next(
        record for record in default["plots"] if record["kind"] == "performance"
    )
    selected_performance = next(
        record for record in selected["plots"] if record["kind"] == "performance"
    )

    assert default_performance["included"] is False
    assert default_performance["reason"] == "requires_explicit_period"
    assert selected_performance["included"] is True
    assert "figures/performance.svg" in _outer_payloads(selected_path)


def test_publication_is_byte_deterministic_has_fixed_zip_metadata_and_closes_figures(
    tmp_path: Path,
) -> None:
    _require_matplotlib()
    import matplotlib.pyplot as plt

    result = _radial_result()
    before = set(plt.get_fignums())
    first = result.publish(tmp_path / "first.zip")
    second = result.publish(tmp_path / "second.zip")

    assert first.read_bytes() == second.read_bytes()
    assert set(plt.get_fignums()) == before
    with zipfile.ZipFile(first) as archive:
        assert archive.namelist()[-1] == "manifest.json"
        assert all(
            info.date_time == (1980, 1, 1, 0, 0, 0) for info in archive.infolist()
        )
        for name in archive.namelist():
            member = PurePosixPath(name)
            assert not member.is_absolute()
            assert ".." not in member.parts
            assert "\\" not in name
        for name in archive.namelist():
            if name.endswith(".svg"):
                svg = archive.read(name)
                assert b"<dc:date>" not in svg


def test_publication_never_calls_a_solver(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _require_matplotlib()
    result = _radial_result()

    def unexpected_solve(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise AssertionError("publication attempted an additional solver call")

    monkeypatch.setattr(SciPyHiGHSSolver, "solve", unexpected_solve)
    monkeypatch.setattr(SciPyHiGHSMILPSolver, "solve", unexpected_solve)

    path = result.publish(tmp_path / "zero-solve.zip", dmu_id="E")

    assert path.exists()
    manifest = json.loads(_outer_payloads(path)["manifest.json"])
    assert manifest["semantics"]["additional_solver_calls"] == 0


def test_publication_missing_matplotlib_is_typed_and_actionable(tmp_path: Path) -> None:
    command = "\n".join(
        (
            "import builtins, pandas as pd, pathlib, sys",
            "from deapack import DEAResult",
            "from deapack.reporting import PublicationBundleNotAvailableError",
            "frame = pd.DataFrame({",
            " 'dmu_id':['A'], 'period':[None], 'score':[0.8],",
            " 'efficiency':[0.8], 'distance':[None], 'is_efficient':[False],",
            " 'solver_status':['optimal'], 'model_family':['test']})",
            "result = DEAResult(frame, metadata={'method_id':'static.radial'})",
            "original = builtins.__import__",
            "def blocked(name, *args, **kwargs):",
            "    if name == 'matplotlib' or name.startswith('matplotlib.'):",
            "        raise ImportError('blocked for test')",
            "    return original(name, *args, **kwargs)",
            "builtins.__import__ = blocked",
            "try:",
            "    result.publish(sys.argv[1])",
            "except PublicationBundleNotAvailableError as error:",
            "    text = str(error)",
            "    assert 'Matplotlib' in text and \"DEAPack[viz]\" in text",
            "else:",
            "    raise AssertionError('typed dependency error was not raised')",
            "assert not pathlib.Path(sys.argv[1]).exists()",
        )
    )
    destination = tmp_path / "missing-viz.zip"

    subprocess.run([sys.executable, "-c", command, str(destination)], check=True)


def test_publication_escapes_untrusted_text_in_html_svg_and_audit(
    tmp_path: Path,
) -> None:
    _require_matplotlib()
    attack = '<script>alert("unsafe")</script>'
    summary = pd.DataFrame(
        {
            "dmu_id": [attack],
            "period": [None],
            "score": [0.8],
            "efficiency": [0.8],
            "distance": [pd.NA],
            "is_efficient": [False],
            "solver_status": ["optimal"],
            "model_family": ["test"],
        }
    )
    result = DEAResult(summary, metadata={"method_id": attack})

    outer = _outer_payloads(result.publish(tmp_path / "escaped.zip"))
    audit = _audit_payloads(outer)

    for payload in (
        outer["index.html"],
        outer["figures/performance.svg"],
        audit["report.html"],
    ):
        text = payload.decode("utf-8")
        assert "<script>" not in text
    assert "&lt;script&gt;" in outer["index.html"].decode("utf-8")
    assert "&lt;script&gt;" in audit["report.html"].decode("utf-8")


def test_publication_errors_are_typed_and_failure_preserves_existing_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _require_matplotlib()
    result = _radial_result()
    with pytest.raises(PublicationBundleNotAvailableError, match=r"\.zip"):
        result.publish(tmp_path / "publication.html")
    with pytest.raises(PublicationBundleNotAvailableError, match="theme"):
        result.publish(tmp_path / "publication.zip", theme="unknown")
    with pytest.raises(PublicationBundleNotAvailableError, match="available values"):
        result.publish(tmp_path / "publication.zip", dmu_id="missing")
    with pytest.raises(PublicationBundleNotAvailableError, match="metric"):
        result.publish(tmp_path / "publication.zip", metric="undeclared_measure")

    destination = tmp_path / "existing.zip"
    destination.write_bytes(b"existing publication")

    def fail_plot(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise RuntimeError("renderer failed")

    monkeypatch.setattr(DEAResult, "plot", fail_plot)
    with pytest.raises(PublicationBundleNotAvailableError, match="could not render"):
        result.publish(destination)

    assert destination.read_bytes() == b"existing publication"
    assert not list(tmp_path.glob(".existing.zip.*"))
