"""Deterministic, complete audit bundles for public DEAPack results."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import math
import os
import tempfile
import zipfile
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from importlib.metadata import PackageNotFoundError, version
from os import PathLike
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pandas.api.types import (
    is_bool_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_timedelta64_dtype,
)

from ._types import ReportNotAvailableError
from .brief import create_result_report

_BUNDLE_SCHEMA_VERSION = 1
_FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
_TABLE_NAMES = (
    "summary",
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
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r", "\n")
_CSV_CHUNK_ROWS = 10_000


class ResultBundleNotAvailableError(ReportNotAvailableError):
    """Raised when a complete, faithful result bundle cannot be written."""


@dataclass(frozen=True, slots=True)
class _BundleReportView:
    """Detached summary and metadata consumed by the trusted report builder."""

    summary_frame: pd.DataFrame
    metadata: Mapping[str, Any]

    def summary(self, *, copy: bool = True) -> pd.DataFrame:
        return self.summary_frame.copy(deep=False) if copy else self.summary_frame


class _EntrySink:
    """Hash uncompressed member bytes while streaming them into a ZIP entry."""

    def __init__(self, stream: Any, *, path: str) -> None:
        self._stream = stream
        self._path = path
        self._hash = hashlib.sha256()
        self._byte_count = 0

    def write_bytes(self, payload: bytes) -> int:
        self._stream.write(payload)
        self._hash.update(payload)
        self._byte_count += len(payload)
        return len(payload)

    def write(self, text: str) -> int:
        try:
            payload = text.encode("utf-8")
        except UnicodeEncodeError as error:
            raise ResultBundleNotAvailableError(
                f"archive member {self._path!r} contains text that cannot be "
                "encoded as UTF-8"
            ) from error
        self.write_bytes(payload)
        return len(text)

    def record(self) -> dict[str, Any]:
        return {
            "path": self._path,
            "bytes": self._byte_count,
            "sha256": self._hash.hexdigest(),
        }


def _package_version() -> str:
    try:
        return version("DEAPack")
    except PackageNotFoundError:
        return "unknown"


def _json_value(value: Any, *, location: str) -> Any:
    """Convert one public value to deterministic, standards-compliant JSON."""
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, Enum):
        return _json_value(value.value, location=location)
    if isinstance(value, np.datetime64):
        if np.isnat(value):
            return None
        return pd.Timestamp(value).isoformat()
    if isinstance(value, np.timedelta64):
        if np.isnat(value):
            return None
        return pd.Timedelta(value).isoformat()
    if isinstance(value, np.generic):
        return _json_value(value.item(), location=location)
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    if isinstance(value, (pd.Timedelta, timedelta)):
        return pd.Timedelta(value).isoformat()
    if isinstance(value, pd.Period):
        return str(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return _json_value(value[()], location=location)
        return [
            _json_value(item, location=f"{location}[{position}]")
            for position, item in enumerate(value)
        ]
    if isinstance(value, pd.Index):
        return [
            _json_value(item, location=f"{location}[{position}]")
            for position, item in enumerate(value)
        ]
    if isinstance(value, bool | int | str):
        return value
    if isinstance(value, float):
        if math.isnan(value):
            return None
        if math.isinf(value):
            return {"__deapack_nonfinite__": "Infinity" if value > 0 else "-Infinity"}
        return value
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            entries = [
                {
                    "key": _json_value(key, location=f"{location}.key"),
                    "value": _json_value(
                        value[key],
                        location=f"{location}.value",
                    ),
                }
                for key in value
            ]
            entries.sort(
                key=lambda item: json.dumps(
                    item,
                    ensure_ascii=False,
                    allow_nan=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
            )
            return {"__deapack_mapping__": entries}
        converted: dict[str, Any] = {}
        for key in sorted(value, key=lambda item: str(item)):
            converted[key] = _json_value(
                value[key],
                location=f"{location}.{key}",
            )
        return converted
    if isinstance(value, (list, tuple)):
        return [
            _json_value(item, location=f"{location}[{position}]")
            for position, item in enumerate(value)
        ]
    if isinstance(value, (set, frozenset)):
        converted = [_json_value(item, location=location) for item in value]
        return sorted(
            converted,
            key=lambda item: json.dumps(
                item,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
                sort_keys=True,
            ),
        )
    try:
        marker = pd.isna(value)
    except (TypeError, ValueError):
        marker = False
    if isinstance(marker, (bool, np.bool_)) and bool(marker):
        return None
    raise ResultBundleNotAvailableError(
        f"{location} contains unsupported value type {type(value).__name__!r}"
    )


def _json_bytes(value: Any) -> bytes:
    try:
        return (
            json.dumps(
                value,
                ensure_ascii=False,
                allow_nan=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
    except UnicodeEncodeError as error:
        raise ResultBundleNotAvailableError(
            "the audit bundle contains text that cannot be encoded as UTF-8"
        ) from error


def _table_frame(
    result: Any,
    name: str,
    *,
    summary_frame: pd.DataFrame,
) -> pd.DataFrame:
    if name == "summary":
        source = summary_frame
    else:
        try:
            source = getattr(result, name)
        except AttributeError as error:
            raise ResultBundleNotAvailableError(
                f"the result bundle source is missing public table {name!r}"
            ) from error
    if not isinstance(source, pd.DataFrame):
        raise ResultBundleNotAvailableError(
            f"public result table {name!r} is not a pandas DataFrame"
        )
    # Serialization is read-only. A shallow detached frame keeps one table at
    # a time without duplicating its full numeric blocks; callers must not
    # mutate result tables concurrently with export.
    frame = source.copy(deep=False)
    if frame.columns.has_duplicates:
        raise ResultBundleNotAvailableError(
            f"public result table {name!r} contains duplicate columns"
        )
    if not all(isinstance(column, str) and column for column in frame.columns):
        raise ResultBundleNotAvailableError(
            f"public result table {name!r} must use non-empty string columns"
        )
    return frame


def _escape_csv_text(value: str) -> str:
    """Neutralize one formula-like spreadsheet cell without changing JSONL."""
    return "'" + value if value.startswith(_FORMULA_PREFIXES) else value


def _safe_csv_columns(frame: pd.DataFrame, *, table_name: str) -> list[str]:
    columns = [_escape_csv_text(column) for column in frame.columns]
    if len(columns) != len(set(columns)):
        raise ResultBundleNotAvailableError(
            f"spreadsheet formula escaping makes {table_name!r} column names ambiguous"
        )
    return columns


def _csv_cell(value: Any, *, location: str) -> Any:
    converted = _json_value(value, location=location)
    if converted is None:
        return pd.NA
    if isinstance(converted, str):
        return _escape_csv_text(converted)
    if isinstance(converted, bool | int | float):
        return converted
    rendered = json.dumps(
        converted,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return _escape_csv_text(rendered)


def _safe_csv_frame(
    frame: pd.DataFrame,
    *,
    table_name: str,
    row_offset: int,
) -> pd.DataFrame:
    """Return one bounded, spreadsheet-safe deterministic CSV chunk."""
    safe = frame.copy(deep=True)
    original_columns = list(frame.columns)
    safe.columns = _safe_csv_columns(frame, table_name=table_name)
    for original, escaped in zip(original_columns, safe.columns, strict=True):
        series = safe[escaped]
        if (
            is_bool_dtype(series.dtype)
            or is_numeric_dtype(series.dtype)
            or is_datetime64_any_dtype(series.dtype)
            or is_timedelta64_dtype(series.dtype)
        ):
            continue
        safe[escaped] = series.astype(object).map(
            lambda value, column=original: _csv_cell(
                value,
                location=(f"tables.{table_name}[{row_offset}:].{column}"),
            )
        )
    return safe


def _write_bytes_entry(
    archive: zipfile.ZipFile,
    path: str,
    payload: bytes,
) -> dict[str, Any]:
    info = _zip_info(path)
    info._compresslevel = 9
    with archive.open(info, mode="w", force_zip64=True) as stream:
        sink = _EntrySink(stream, path=path)
        sink.write_bytes(payload)
    return sink.record()


def _stream_csv_entry(
    archive: zipfile.ZipFile,
    path: str,
    frame: pd.DataFrame,
    *,
    table_name: str,
) -> tuple[dict[str, Any], list[str]]:
    safe_columns = _safe_csv_columns(frame, table_name=table_name)
    info = _zip_info(path)
    info._compresslevel = 9
    with archive.open(info, mode="w", force_zip64=True) as stream:
        sink = _EntrySink(stream, path=path)
        if frame.empty:
            safe = _safe_csv_frame(
                frame,
                table_name=table_name,
                row_offset=0,
            )
            safe.to_csv(
                sink,
                index=False,
                lineterminator="\n",
                na_rep="",
                float_format="%.17g",
                quoting=csv.QUOTE_ALL,
            )
        else:
            for start in range(0, len(frame), _CSV_CHUNK_ROWS):
                safe = _safe_csv_frame(
                    frame.iloc[start : start + _CSV_CHUNK_ROWS],
                    table_name=table_name,
                    row_offset=start,
                )
                safe.to_csv(
                    sink,
                    index=False,
                    header=start == 0,
                    lineterminator="\n",
                    na_rep="",
                    float_format="%.17g",
                    quoting=csv.QUOTE_ALL,
                )
    return sink.record(), safe_columns


def _stream_jsonl_entry(
    archive: zipfile.ZipFile,
    path: str,
    frame: pd.DataFrame,
    *,
    table_name: str,
) -> dict[str, Any]:
    columns = list(frame.columns)
    info = _zip_info(path)
    info._compresslevel = 9
    with archive.open(info, mode="w", force_zip64=True) as stream:
        sink = _EntrySink(stream, path=path)
        for row_number, row in enumerate(frame.itertuples(index=False, name=None)):
            record = {
                column: _json_value(
                    value,
                    location=f"tables.{table_name}[{row_number}].{column}",
                )
                for column, value in zip(columns, row, strict=True)
            }
            sink.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    allow_nan=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
                + "\n"
            )
    return sink.record()


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(filename=name, date_time=_FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    info.flag_bits |= 0x800
    return info


def _readme_bytes() -> bytes:
    return (
        b"DEAPack result audit bundle\n"
        b"===========================\n\n"
        b"report.html is a compact human-readable brief, or a safe audit "
        b"cover when no substantive measure is reportable. The tables directory "
        b"contains every non-empty public result table in JSON Lines and "
        b"spreadsheet-safe CSV form. JSONL preserves string values exactly and "
        b"canonically represents supported structured values. CSV represents "
        b"structured cells as canonical JSON text and prefixes cell values or "
        b"headers beginning with =, +, -, @, tab, carriage return, or line feed "
        b"with an apostrophe to prevent spreadsheet formula execution. "
        b"manifest.json records original and CSV headers, table schemas, and "
        b"SHA-256 hashes for every other archive member. Hashes establish file "
        b"integrity, not publisher authenticity. This bundle is a deterministic "
        b"descriptive audit artifact, not a causal finding or an implementation "
        b"prescription.\n"
    )


def _unavailable_report_bytes(reason: str) -> bytes:
    """Return a safe audit cover when no substantive brief is reportable."""
    escaped_reason = html.escape(reason, quote=True)
    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>DEAPack audit bundle</title>
  <style>
    body {{ color: #172235; font: 16px/1.55 system-ui, sans-serif;
           margin: 3rem auto; max-width: 52rem; padding: 0 1.25rem; }}
    .notice {{ background: #fff7e6; border-left: .35rem solid #b96b00;
               padding: 1rem 1.2rem; }}
    code {{ background: #edf2f7; padding: .1rem .25rem; }}
  </style>
</head>
<body>
  <main>
    <h1>DEAPack result audit bundle</h1>
    <div class="notice">
      <p><strong>No substantive performance brief is available.</strong></p>
      <p>{escaped_reason}</p>
    </div>
    <p>The complete public result tables remain available under
       <code>tables/</code>. Method provenance is in <code>metadata.json</code>,
       and file integrity information is in <code>manifest.json</code>.</p>
    <p>This cover is descriptive. It is not a causal finding or an
       implementation prescription.</p>
  </main>
</body>
</html>
"""
    try:
        return document.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ResultBundleNotAvailableError(
            "the report-unavailability reason cannot be encoded as UTF-8"
        ) from error


def export_result_bundle(
    result: Any,
    path: str | PathLike[str],
) -> Path:
    """Atomically write one deterministic, complete ``.zip`` audit bundle.

    The bundle uses only public result tables. It never refits a model and
    never imports a plotting backend. The HTML brief may truncate its reading
    table, but the CSV and JSONL tables in the same archive remain complete.
    """
    destination = Path(path)
    if destination.suffix.casefold() != ".zip":
        raise ResultBundleNotAvailableError(
            "result audit bundles require a .zip destination"
        )

    metadata_source = getattr(result, "metadata", None)
    if not isinstance(metadata_source, Mapping):
        raise ResultBundleNotAvailableError(
            "result.metadata must be mapping-like for an audit bundle"
        )
    metadata = _json_value(metadata_source, location="metadata")
    if not isinstance(metadata, dict):
        raise ResultBundleNotAvailableError(
            "result.metadata could not be represented as a JSON object"
        )

    summary_method = getattr(result, "summary", None)
    if not callable(summary_method):
        raise ResultBundleNotAvailableError(
            "the result bundle source must provide summary(copy=True)"
        )
    try:
        raw_summary = summary_method(copy=True)
    except (AttributeError, TypeError, ValueError) as error:
        raise ResultBundleNotAvailableError(
            "the result bundle source could not provide summary(copy=True)"
        ) from error
    summary_frame = _table_frame(
        result,
        "summary",
        summary_frame=raw_summary,
    )

    try:
        report = create_result_report(
            _BundleReportView(
                summary_frame=summary_frame,
                metadata=metadata,
            )
        )
        try:
            report_payload = report.to_html(full_document=True).encode("utf-8")
        except UnicodeEncodeError as error:
            raise ResultBundleNotAvailableError(
                "the HTML brief contains text that cannot be encoded as UTF-8"
            ) from error
        report_status: dict[str, Any] = {
            "included": True,
            "substantive_brief": report.metric is not None,
            "kind": report.kind,
            "metric": report.metric,
            "observation_count": report.observation_count,
            "omitted_metric_count": report.omitted_metric_count,
            "invalid_metric_count": report.invalid_metric_count,
        }
    except ResultBundleNotAvailableError:
        raise
    except ReportNotAvailableError as error:
        report_payload = _unavailable_report_bytes(str(error))
        report_status = {
            "included": True,
            "substantive_brief": False,
            "kind": "unavailable_cover",
            "reason": str(error),
        }

    temporary_path: Path | None = None
    descriptor: int | None = None
    try:
        descriptor, raw_path = tempfile.mkstemp(
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
        )
        temporary_path = Path(raw_path)
        with os.fdopen(descriptor, "w+b") as temporary_stream:
            descriptor = None
            with zipfile.ZipFile(
                temporary_stream,
                mode="w",
                compression=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            ) as archive:
                file_manifest: list[dict[str, Any]] = []
                file_manifest.append(
                    _write_bytes_entry(archive, "README.txt", _readme_bytes())
                )
                file_manifest.append(
                    _write_bytes_entry(
                        archive,
                        "metadata.json",
                        _json_bytes(metadata),
                    )
                )
                file_manifest.append(
                    _write_bytes_entry(archive, "report.html", report_payload)
                )

                table_manifest: list[dict[str, Any]] = []
                for name in _TABLE_NAMES:
                    frame = _table_frame(
                        result,
                        name,
                        summary_frame=summary_frame,
                    )
                    if name != "summary" and frame.empty:
                        continue
                    csv_path = f"tables/{name}.csv"
                    jsonl_path = f"tables/{name}.jsonl"
                    csv_record, csv_columns = _stream_csv_entry(
                        archive,
                        csv_path,
                        frame,
                        table_name=name,
                    )
                    jsonl_record = _stream_jsonl_entry(
                        archive,
                        jsonl_path,
                        frame,
                        table_name=name,
                    )
                    file_manifest.extend((csv_record, jsonl_record))
                    table_manifest.append(
                        {
                            "name": name,
                            "rows": len(frame),
                            "columns": list(frame.columns),
                            "dtypes": {
                                column: str(frame[column].dtype) for column in frame
                            },
                            "csv": {
                                **csv_record,
                                "columns": csv_columns,
                                "spreadsheet_formula_escape": (
                                    "apostrophe_prefix_cells_and_headers"
                                ),
                                "quoting": "all_fields",
                                "structured_value": "canonical_json_text",
                            },
                            "jsonl": {
                                **jsonl_record,
                                "missing_value": "null",
                                "nonfinite_value": "tagged_object",
                                "structured_value": "canonical_json",
                            },
                        }
                    )

                file_manifest.sort(key=lambda item: item["path"])
                manifest = {
                    "bundle_schema_version": _BUNDLE_SCHEMA_VERSION,
                    "package": {"name": "DEAPack", "version": _package_version()},
                    "method_id": metadata.get("method_id"),
                    "model_family": metadata.get("model_family"),
                    "solver": metadata.get("solver"),
                    "report": report_status,
                    "tables": table_manifest,
                    "files": file_manifest,
                    "integrity": {
                        "algorithm": "sha256",
                        "scope": "all_archive_members_except_manifest.json",
                        "authenticity_claim": False,
                    },
                    "semantics": {
                        "source": "public_result_snapshot_v1",
                        "report_builder": "trusted_internal_from_detached_summary",
                        "additional_solver_calls": 0,
                        "additional_solver_calls_scope": "deapack_exporter",
                        "causal_claim": False,
                        "prescriptive_claim": False,
                        "brief_truncation_affects_bundle_tables": False,
                    },
                }
                _write_bytes_entry(
                    archive,
                    "manifest.json",
                    _json_bytes(manifest),
                )
            temporary_stream.flush()
            os.fsync(temporary_stream.fileno())
        os.replace(temporary_path, destination)
        temporary_path = None
    except ResultBundleNotAvailableError:
        raise
    except (
        OSError,
        TypeError,
        ValueError,
        zipfile.BadZipFile,
        zipfile.LargeZipFile,
    ) as error:
        raise ResultBundleNotAvailableError(
            f"could not write result audit bundle: {error}"
        ) from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return destination


__all__ = [
    "ResultBundleNotAvailableError",
    "export_result_bundle",
]
