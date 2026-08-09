from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import subprocess
import sys
import zipfile
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

import deapack.reporting.bundle as bundle_module
from deapack import BCCInput, DEAData, DEAResult, dataset_info, load_dataset
from deapack.reporting import (
    ReportNotAvailableError,
    ResultBundleNotAvailableError,
    export_result_bundle,
)


def _radial_result() -> DEAResult:
    frame = load_dataset("frontier_1x1")
    roles = dataset_info("frontier_1x1").roles
    data = DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )
    return BCCInput().fit(data)


def _archive_payloads(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def test_bundle_table_contract_tracks_every_dea_result_dataframe() -> None:
    result_fields = tuple(DEAResult.__dataclass_fields__)
    expected = (
        "summary",
        *(name for name in result_fields if name not in {"summary_frame", "metadata"}),
    )

    assert expected == bundle_module._TABLE_NAMES


def test_export_bundle_contains_complete_hashed_public_audit(tmp_path: Path) -> None:
    result = _radial_result()
    before = {
        "summary": result.summary(),
        "slacks": result.slacks.copy(deep=True),
        "targets": result.targets.copy(deep=True),
        "intensities": result.intensities.copy(deep=True),
        "diagnostics": result.diagnostics.copy(deep=True),
    }

    destination = result.export_bundle(tmp_path / "radial-audit.zip")
    payloads = _archive_payloads(destination)

    assert destination == tmp_path / "radial-audit.zip"
    assert {
        "README.txt",
        "manifest.json",
        "metadata.json",
        "report.html",
        "tables/summary.csv",
        "tables/summary.jsonl",
        "tables/slacks.csv",
        "tables/slacks.jsonl",
        "tables/targets.csv",
        "tables/targets.jsonl",
        "tables/intensities.csv",
        "tables/intensities.jsonl",
        "tables/diagnostics.csv",
        "tables/diagnostics.jsonl",
    }.issubset(payloads)

    manifest = json.loads(payloads["manifest.json"])
    assert manifest["bundle_schema_version"] == 1
    assert manifest["method_id"] == "static.radial"
    assert manifest["report"]["included"] is True
    assert manifest["report"]["substantive_brief"] is True
    assert manifest["semantics"] == {
        "additional_solver_calls": 0,
        "additional_solver_calls_scope": "deapack_exporter",
        "brief_truncation_affects_bundle_tables": False,
        "causal_claim": False,
        "prescriptive_claim": False,
        "report_builder": "trusted_internal_from_detached_summary",
        "source": "public_result_snapshot_v1",
    }
    assert manifest["integrity"] == {
        "algorithm": "sha256",
        "authenticity_claim": False,
        "scope": "all_archive_members_except_manifest.json",
    }
    table_rows = {item["name"]: item["rows"] for item in manifest["tables"]}
    assert table_rows["summary"] == len(result.summary())
    assert table_rows["targets"] == len(result.targets)
    assert table_rows["intensities"] == len(result.intensities)

    for item in manifest["files"]:
        payload = payloads[item["path"]]
        assert len(payload) == item["bytes"]
        assert hashlib.sha256(payload).hexdigest() == item["sha256"]

    for name, frame in before.items():
        current = result.summary() if name == "summary" else getattr(result, name)
        assert_frame_equal(current, frame)


def test_export_bundle_is_byte_deterministic_and_uses_fixed_zip_metadata(
    tmp_path: Path,
) -> None:
    result = _radial_result()
    first = result.export_bundle(tmp_path / "first.zip")
    second = result.export_bundle(tmp_path / "second.zip")

    assert first.read_bytes() == second.read_bytes()
    with zipfile.ZipFile(first) as archive:
        assert archive.namelist()[-1] == "manifest.json"
        assert archive.namelist()[:3] == [
            "README.txt",
            "metadata.json",
            "report.html",
        ]
        assert all(
            info.date_time == (1980, 1, 1, 0, 0, 0) for info in archive.infolist()
        )


def test_bundle_covers_every_public_dea_result_table(tmp_path: Path) -> None:
    source = _radial_result()
    table_names = (
        "slacks",
        "targets",
        "intensities",
        "duals",
        "components",
        "multipliers",
        "links",
        "diagnostics",
        "appraisals",
        "history",
    )
    result = DEAResult(
        summary_frame=source.summary(),
        metadata=source.metadata,
        **{
            name: pd.DataFrame({"public_table": [name], "row_number": [1]})
            for name in table_names
        },
    )

    payloads = _archive_payloads(result.export_bundle(tmp_path / "all-tables.zip"))
    manifest = json.loads(payloads["manifest.json"])

    assert {item["name"] for item in manifest["tables"]} == {
        "summary",
        *table_names,
    }
    for name in ("summary", *table_names):
        assert f"tables/{name}.csv" in payloads
        assert f"tables/{name}.jsonl" in payloads


def test_bundle_csv_neutralizes_formulas_while_jsonl_preserves_exact_strings(
    tmp_path: Path,
) -> None:
    summary = pd.DataFrame(
        {
            "dmu_id": ["=cmd|' /C calc'!A0", "+unsafe", "ordinary"],
            "period": [None, None, None],
            "score": [0.8, 0.9, 1.0],
            "efficiency": [0.8, 0.9, 1.0],
            "distance": [pd.NA, pd.NA, pd.NA],
            "is_efficient": [False, False, True],
            "solver_status": ["optimal", "optimal", "optimal"],
            "model_family": ["test", "test", "test"],
        }
    )
    formula_values = [
        "=CATEGORY",
        "+PLUS",
        "-MINUS",
        "@AT",
        "\t=TAB",
        "\r=RETURN",
        "\n=NEWLINE",
        "ordinary",
    ]
    diagnostics = pd.DataFrame(
        {
            "=UNTRUSTED_HEADER": pd.Categorical(formula_values),
            "string_values": pd.Series(formula_values, dtype="string"),
            "object_values": pd.Series(formula_values, dtype=object),
        }
    )
    result = DEAResult(
        summary_frame=summary,
        diagnostics=diagnostics,
        metadata={"method_id": "test", "nested": {2024: ("A", "B")}},
    )

    path = result.export_bundle(tmp_path / "safe.zip")
    payloads = _archive_payloads(path)
    csv_text = payloads["tables/summary.csv"].decode("utf-8")
    records = [
        json.loads(line)
        for line in payloads["tables/summary.jsonl"].decode("utf-8").splitlines()
    ]
    metadata = json.loads(payloads["metadata.json"])
    diagnostic_csv = list(
        csv.reader(
            io.StringIO(
                payloads["tables/diagnostics.csv"].decode("utf-8"),
                newline="",
            )
        )
    )
    diagnostic_jsonl = [
        json.loads(line)
        for line in payloads["tables/diagnostics.jsonl"].decode("utf-8").splitlines()
    ]
    manifest = json.loads(payloads["manifest.json"])

    assert "'=cmd|' /C calc'!A0" in csv_text
    assert "'+unsafe" in csv_text
    assert records[0]["dmu_id"] == "=cmd|' /C calc'!A0"
    assert records[1]["dmu_id"] == "+unsafe"
    assert metadata["nested"]["__deapack_mapping__"][0]["key"] == 2024
    assert diagnostic_csv[0] == [
        "'=UNTRUSTED_HEADER",
        "string_values",
        "object_values",
    ]
    for source, row in zip(formula_values, diagnostic_csv[1:], strict=True):
        expected = "'" + source if source != "ordinary" else source
        assert row == [expected, expected, expected]
    assert diagnostic_jsonl[0]["=UNTRUSTED_HEADER"] == "=CATEGORY"
    assert diagnostic_jsonl[6]["=UNTRUSTED_HEADER"] == "\n=NEWLINE"
    diagnostic_manifest = next(
        item for item in manifest["tables"] if item["name"] == "diagnostics"
    )
    assert diagnostic_manifest["columns"][0] == "=UNTRUSTED_HEADER"
    assert diagnostic_manifest["csv"]["columns"][0] == "'=UNTRUSTED_HEADER"


def test_bundle_encodes_missing_and_nonfinite_values_without_invalid_json(
    tmp_path: Path,
) -> None:
    result = _radial_result()
    summary = result.summary()
    summary.loc[0, "distance"] = float("inf")
    summary.loc[1, "distance"] = float("-inf")
    summary.loc[2, "distance"] = float("nan")
    altered = DEAResult(
        summary_frame=summary,
        slacks=result.slacks,
        targets=result.targets,
        intensities=result.intensities,
        diagnostics=result.diagnostics,
        metadata=result.metadata,
    )

    path = altered.export_bundle(tmp_path / "nonfinite.zip")
    rows = [
        json.loads(line)
        for line in _archive_payloads(path)["tables/summary.jsonl"]
        .decode("utf-8")
        .splitlines()
    ]

    assert rows[0]["distance"] == {"__deapack_nonfinite__": "Infinity"}
    assert rows[1]["distance"] == {"__deapack_nonfinite__": "-Infinity"}
    assert rows[2]["distance"] is None


def test_bundle_preserves_numpy_and_python_time_semantics(tmp_path: Path) -> None:
    source = _radial_result()
    diagnostics = pd.DataFrame(
        {
            "temporal_value": pd.Series(
                [
                    np.datetime64("2024-01-02T03:04:05.000000000"),
                    np.timedelta64(2, "D"),
                    timedelta(hours=3),
                ],
                dtype=object,
            )
        }
    )
    result = DEAResult(
        summary_frame=source.summary(),
        diagnostics=diagnostics,
        metadata=source.metadata,
    )

    rows = [
        json.loads(line)
        for line in _archive_payloads(
            result.export_bundle(tmp_path / "time-values.zip")
        )["tables/diagnostics.jsonl"]
        .decode("utf-8")
        .splitlines()
    ]

    assert rows[0]["temporal_value"] == "2024-01-02T03:04:05"
    assert rows[1]["temporal_value"].startswith("P2D")
    assert rows[2]["temporal_value"].startswith("P0DT3H")


def test_bundle_rejects_wrong_suffix_and_unsupported_metadata_without_writing(
    tmp_path: Path,
) -> None:
    result = _radial_result()
    with pytest.raises(ResultBundleNotAvailableError, match=r"\.zip"):
        result.export_bundle(tmp_path / "audit.xlsx")

    invalid = DEAResult(
        summary_frame=result.summary(),
        metadata={"method_id": "test", "unsupported": object()},
    )
    destination = tmp_path / "invalid.zip"
    with pytest.raises(ResultBundleNotAvailableError, match="unsupported value type"):
        invalid.export_bundle(destination)
    assert not destination.exists()


def test_bundle_keeps_a_safe_html_cover_when_no_substantive_brief_exists(
    tmp_path: Path,
) -> None:
    summary = pd.DataFrame(
        {
            "dmu_id": ["<Clinic A>"],
            "period": [None],
            "score": [pd.NA],
            "efficiency": [pd.NA],
            "distance": [pd.NA],
            "is_efficient": [False],
            "solver_status": ["infeasible"],
            "model_family": ["test"],
        }
    )
    result = DEAResult(summary_frame=summary, metadata={"method_id": "test"})

    payloads = _archive_payloads(result.export_bundle(tmp_path / "failed-fit.zip"))
    manifest = json.loads(payloads["manifest.json"])
    cover = payloads["report.html"].decode("utf-8")

    assert manifest["report"]["included"] is True
    assert manifest["report"]["substantive_brief"] is False
    assert manifest["report"]["kind"] == "brief"
    assert "no declared measure with a valid finite optimal value" in cover
    assert "<Clinic A>" not in cover
    assert "tables/summary.jsonl" in payloads


def test_bundle_uses_internal_report_builder_and_never_calls_extension_report(
    tmp_path: Path,
) -> None:
    class ExtensionResult:
        def __init__(self) -> None:
            self.metadata = {"method_id": "extension.test"}
            self.summary_calls = 0
            self.report_calls = 0
            for table in (
                "slacks",
                "targets",
                "intensities",
                "duals",
                "components",
                "multipliers",
                "links",
                "diagnostics",
                "appraisals",
                "history",
            ):
                setattr(self, table, pd.DataFrame())

        def summary(self, *, copy: bool = True) -> pd.DataFrame:
            self.summary_calls += 1
            return _radial_result().summary(copy=copy)

        def report(self) -> object:
            self.report_calls += 1
            return type(
                "UnsafeReport",
                (),
                {"to_html": lambda self, **kwargs: "<script>unsafe()</script>"},
            )()

    result = ExtensionResult()
    payloads = _archive_payloads(
        export_result_bundle(result, tmp_path / "extension.zip")
    )
    manifest = json.loads(payloads["manifest.json"])
    report = payloads["report.html"].decode("utf-8")

    assert manifest["report"]["substantive_brief"] is True
    assert manifest["semantics"]["report_builder"] == (
        "trusted_internal_from_detached_summary"
    )
    assert "<script>" not in report
    assert result.summary_calls == 1
    assert result.report_calls == 0


def test_bundle_escapes_internal_report_unavailability_reason(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unavailable(result: object) -> None:
        del result
        raise ReportNotAvailableError("unsafe <script>alert(1)</script>")

    monkeypatch.setattr(bundle_module, "create_result_report", unavailable)
    payloads = _archive_payloads(
        _radial_result().export_bundle(tmp_path / "unavailable.zip")
    )
    manifest = json.loads(payloads["manifest.json"])
    cover = payloads["report.html"].decode("utf-8")

    assert manifest["report"]["substantive_brief"] is False
    assert manifest["report"]["kind"] == "unavailable_cover"
    assert "<script>" not in cover
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in cover


def test_bundle_rejects_unencodable_public_text_before_touching_destination(
    tmp_path: Path,
) -> None:
    result = _radial_result()
    summary = result.summary()
    summary.loc[0, "dmu_id"] = "bad-\ud800-label"
    altered = DEAResult(summary_frame=summary, metadata=result.metadata)
    destination = tmp_path / "unencodable.zip"
    destination.write_bytes(b"existing-audit")

    with pytest.raises(ResultBundleNotAvailableError, match="encoded as UTF-8"):
        altered.export_bundle(destination)
    assert destination.read_bytes() == b"existing-audit"


def test_bundle_rejects_ambiguous_escaped_headers_atomically(
    tmp_path: Path,
) -> None:
    source = _radial_result()
    diagnostics = pd.DataFrame([[1, 2]], columns=["=risk", "'=risk"])
    result = DEAResult(
        summary_frame=source.summary(),
        diagnostics=diagnostics,
        metadata=source.metadata,
    )
    destination = tmp_path / "ambiguous.zip"
    destination.write_bytes(b"existing-audit")

    with pytest.raises(ResultBundleNotAvailableError, match="column names ambiguous"):
        result.export_bundle(destination)
    assert destination.read_bytes() == b"existing-audit"


def test_bundle_replace_failure_preserves_destination_and_cleans_temp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "replace-failure.zip"
    destination.write_bytes(b"existing-audit")

    def fail_replace(source: object, target: object) -> None:
        del source, target
        raise OSError("simulated replace failure")

    monkeypatch.setattr(bundle_module.os, "replace", fail_replace)
    with pytest.raises(ResultBundleNotAvailableError, match="replace failure"):
        _radial_result().export_bundle(destination)

    assert destination.read_bytes() == b"existing-audit"
    assert not list(tmp_path.glob(".replace-failure.zip.*.tmp"))


def test_bundle_missing_extension_table_fails_with_typed_error(
    tmp_path: Path,
) -> None:
    class IncompleteExtension:
        def __init__(self) -> None:
            self.metadata = {"method_id": "extension.incomplete"}

        def summary(self, *, copy: bool = True) -> pd.DataFrame:
            return _radial_result().summary(copy=copy)

    destination = tmp_path / "incomplete.zip"
    with pytest.raises(ResultBundleNotAvailableError, match="public table 'slacks'"):
        export_result_bundle(IncompleteExtension(), destination)
    assert not destination.exists()


def test_bundle_complex_cells_are_canonical_across_hash_seeds(
    tmp_path: Path,
) -> None:
    script = "\n".join(
        (
            "import sys",
            "import pandas as pd",
            "from deapack import DEAResult",
            "summary = pd.DataFrame({",
            "    'dmu_id': ['A'], 'period': [None], 'score': [1.0],",
            "    'efficiency': [1.0], 'distance': [0.0],",
            "    'is_efficient': [True], 'solver_status': ['optimal'],",
            "    'model_family': ['test'],",
            "})",
            "diagnostics = pd.DataFrame({'structured': [{",
            "    'set': {'gamma', 'alpha', 'beta'},",
            "    'tuple': ('z', 'a'),",
            "    'mapping': {3: 'three', 1: 'one'},",
            "}]})",
            "DEAResult(summary, diagnostics=diagnostics,",
            "          metadata={'method_id': 'test'}).export_bundle(sys.argv[1])",
        )
    )
    paths = [tmp_path / "seed-1.zip", tmp_path / "seed-2.zip"]
    for seed, path in zip(("1", "2"), paths, strict=True):
        subprocess.run(
            [sys.executable, "-c", script, str(path)],
            check=True,
            env={**os.environ, "PYTHONHASHSEED": seed},
        )

    assert paths[0].read_bytes() == paths[1].read_bytes()
    payloads = _archive_payloads(paths[0])
    csv_rows = list(
        csv.reader(
            io.StringIO(
                payloads["tables/diagnostics.csv"].decode("utf-8"),
                newline="",
            )
        )
    )
    json_record = json.loads(
        payloads["tables/diagnostics.jsonl"].decode("utf-8").strip()
    )
    assert json.loads(csv_rows[1][0])["set"] == ["alpha", "beta", "gamma"]
    assert json_record["structured"]["set"] == ["alpha", "beta", "gamma"]


def test_streaming_chunks_preserve_exact_archive_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _radial_result()
    ordinary = result.export_bundle(tmp_path / "ordinary.zip")

    monkeypatch.setattr(bundle_module, "_CSV_CHUNK_ROWS", 2)
    chunked = result.export_bundle(tmp_path / "chunked.zip")

    assert ordinary.read_bytes() == chunked.read_bytes()


def test_streaming_bundle_preserves_every_row_across_multiple_chunks(
    tmp_path: Path,
) -> None:
    row_count = 20_005
    identifiers = pd.Series(range(row_count), dtype="int64")
    summary = pd.DataFrame(
        {
            "dmu_id": identifiers,
            "period": pd.Series([None] * row_count, dtype=object),
            "score": pd.Series(1.0, index=range(row_count), dtype="float64"),
            "efficiency": pd.Series(
                1.0,
                index=range(row_count),
                dtype="float64",
            ),
            "distance": pd.Series(0.0, index=range(row_count), dtype="float64"),
            "is_efficient": pd.Series(
                True,
                index=range(row_count),
                dtype="bool",
            ),
            "solver_status": pd.Series(
                "optimal",
                index=range(row_count),
                dtype="string",
            ),
            "model_family": pd.Series(
                "streaming_test",
                index=range(row_count),
                dtype="string",
            ),
        }
    )
    result = DEAResult(summary, metadata={"method_id": "test.streaming"})

    payloads = _archive_payloads(result.export_bundle(tmp_path / "multi-chunk.zip"))
    manifest = json.loads(payloads["manifest.json"])
    summary_manifest = next(
        item for item in manifest["tables"] if item["name"] == "summary"
    )

    assert summary_manifest["rows"] == row_count
    assert payloads["tables/summary.jsonl"].count(b"\n") == row_count
    assert payloads["tables/summary.csv"].count(b"\n") == row_count + 1


def test_bundle_export_does_not_import_matplotlib(tmp_path: Path) -> None:
    destination = tmp_path / "subprocess.zip"
    command = "\n".join(
        (
            "import sys",
            "import pandas as pd",
            "from deapack import DEAResult",
            "frame = pd.DataFrame({",
            "    'dmu_id': ['A'], 'period': [None], 'score': [0.8],",
            "    'efficiency': [0.8], 'distance': [pd.NA],",
            "    'is_efficient': [False], 'solver_status': ['optimal'],",
            "    'model_family': ['test'],",
            "})",
            f"DEAResult(frame).export_bundle({str(destination)!r})",
            "assert not any(name == 'matplotlib' or name.startswith('matplotlib.')",
            "               for name in sys.modules)",
        )
    )

    subprocess.run([sys.executable, "-c", command], check=True)
    assert destination.exists()
