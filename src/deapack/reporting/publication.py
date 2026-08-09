"""Deterministic illustrated publication bundles for fitted DEAPack results."""

from __future__ import annotations

import html
import io
import os
import re
import tempfile
import zipfile
from collections.abc import Mapping
from os import PathLike
from pathlib import Path, PurePosixPath
from typing import Any

import numpy as np
import pandas as pd

from ..visualization import PlotInfo, PlotNotAvailableError, available_plots
from ..visualization.performance import MAX_AUTO_FACETS
from ._types import ReportNotAvailableError
from .bundle import (
    _EntrySink,
    _json_bytes,
    _json_value,
    _package_version,
    _write_bytes_entry,
    _zip_info,
    export_result_bundle,
)

_PUBLICATION_SCHEMA_VERSION = 1
_SVG_HASH_SALT = "deapack-publication-v1"
_SAFE_KIND = re.compile(r"^[a-z][a-z0-9-]*$")
_DMU_PLOTS = frozenset({"trajectory", "process", "improvement"})
_PERIOD_PLOTS = frozenset({"frontier", "process", "improvement", "metafrontier"})
_CARRYOVER_ROLES = frozenset(
    {"good_carryover", "bad_carryover", "free_carryover", "fixed_carryover"}
)


class PublicationBundleNotAvailableError(ReportNotAvailableError):
    """Raised when an illustrated publication bundle cannot be made safely."""


def _safe_member_path(path: str) -> str:
    member = PurePosixPath(path)
    if (
        not path
        or "\\" in path
        or member.is_absolute()
        or any(part in {"", ".", ".."} for part in member.parts)
    ):
        raise PublicationBundleNotAvailableError(
            f"unsafe publication archive member path: {path!r}"
        )
    return path


def _write_publication_bytes(
    archive: zipfile.ZipFile,
    path: str,
    payload: bytes,
) -> dict[str, Any]:
    return _write_bytes_entry(archive, _safe_member_path(path), payload)


def _stream_publication_file(
    archive: zipfile.ZipFile,
    path: str,
    source: Path,
) -> dict[str, Any]:
    """Stream one file into the archive without holding it all in memory."""
    safe_path = _safe_member_path(path)
    info = _zip_info(safe_path)
    # The nested audit ZIP is already compressed. Storing it avoids an
    # expensive second compression pass while retaining deterministic bytes.
    info.compress_type = zipfile.ZIP_STORED
    with archive.open(info, mode="w", force_zip64=True) as destination:
        sink = _EntrySink(destination, path=safe_path)
        with source.open("rb") as stream:
            while payload := stream.read(1024 * 1024):
                sink.write_bytes(payload)
    return sink.record()


def _summary_frame(result: Any) -> pd.DataFrame:
    from ..results import DEAResult

    try:
        summary = DEAResult.summary(result, copy=True)
    except (AttributeError, TypeError, ValueError) as error:
        raise PublicationBundleNotAvailableError(
            "publication source could not provide summary(copy=True)"
        ) from error
    if not isinstance(summary, pd.DataFrame):
        raise PublicationBundleNotAvailableError(
            "publication source summary must be a pandas DataFrame"
        )
    missing = {"dmu_id", "period"}.difference(summary.columns)
    if missing:
        raise PublicationBundleNotAvailableError(
            f"publication source summary is missing columns: {sorted(missing)!r}"
        )
    if summary.columns.has_duplicates:
        raise PublicationBundleNotAvailableError(
            "publication source summary contains duplicate columns"
        )
    return summary


def _missing_scalar(value: object) -> bool:
    try:
        marker = pd.isna(value)
    except (TypeError, ValueError):
        return False
    return isinstance(marker, (bool, np.bool_)) and bool(marker)


def _same_scalar(left: object, right: object) -> bool:
    if _missing_scalar(left) and _missing_scalar(right):
        return True
    if _missing_scalar(left) or _missing_scalar(right):
        return False
    try:
        marker = left == right
    except (TypeError, ValueError):
        return False
    return isinstance(marker, (bool, np.bool_)) and bool(marker)


def _unique_scalars(values: pd.Series) -> tuple[object, ...]:
    unique: list[object] = []
    for value in values.tolist():
        if not any(_same_scalar(value, existing) for existing in unique):
            unique.append(value)
    return tuple(unique)


def _available_values(values: pd.Series) -> str:
    unique = _unique_scalars(values)
    displayed = [
        "not reported" if _missing_scalar(value) else repr(value)
        for value in unique[:8]
    ]
    if len(unique) > 8:
        displayed.append(f"… (+{len(unique) - 8} more)")
    return ", ".join(displayed) or "none"


def _validate_selector(
    summary: pd.DataFrame,
    *,
    column: str,
    value: object | None,
) -> None:
    if value is None:
        return
    if not any(_same_scalar(candidate, value) for candidate in summary[column]):
        raise PublicationBundleNotAvailableError(
            f"{column} {value!r} is not present in the result; available values: "
            f"{_available_values(summary[column])}"
        )


def _period_is_unambiguous(summary: pd.DataFrame, period: object | None) -> bool:
    return period is not None or len(_unique_scalars(summary["period"])) <= 1


def _trajectory_needs_variable(result: Any, *, dmu_id: object) -> bool:
    targets = getattr(result, "targets", None)
    if not isinstance(targets, pd.DataFrame):
        return True
    required = {"dmu_id", "role", "variable"}
    if not required.issubset(targets.columns):
        return True
    mask = targets["dmu_id"].map(lambda value: _same_scalar(value, dmu_id))
    selected = targets.loc[mask & targets["role"].isin(_CARRYOVER_ROLES)]
    return len(selected[["role", "variable"]].drop_duplicates()) != 1


def _declared_plots(result: Any) -> tuple[tuple[PlotInfo, ...], tuple[PlotInfo, ...]]:
    from ..results import DEAResult

    try:
        declared = tuple(DEAResult.available_plots(result))
        registry = tuple(available_plots())
    except (AttributeError, TypeError, ValueError) as error:
        raise PublicationBundleNotAvailableError(
            "publication source could not declare available plots"
        ) from error
    for label, values in (("result", declared), ("registry", registry)):
        if not all(isinstance(item, PlotInfo) for item in values):
            raise PublicationBundleNotAvailableError(
                f"{label} available_plots() must return PlotInfo records"
            )
        kinds = [item.kind for item in values]
        if len(kinds) != len(set(kinds)):
            raise PublicationBundleNotAvailableError(
                f"{label} available_plots() contains duplicate kinds"
            )
        if any(not _SAFE_KIND.fullmatch(kind) for kind in kinds):
            raise PublicationBundleNotAvailableError(
                f"{label} available_plots() contains an unsafe plot kind"
            )
    return registry, declared


def _plot_policy(
    info: PlotInfo,
    *,
    declared_kinds: frozenset[str],
    summary: pd.DataFrame,
    result: Any,
    metric: str | None,
    period: object | None,
    dmu_id: object | None,
    variable: str | None,
) -> tuple[bool, str]:
    kind = info.kind
    if kind not in declared_kinds:
        return False, "not_declared_applicable_by_result_available_plots"
    if kind not in {
        "performance",
        "frontier",
        "trajectory",
        "process",
        "improvement",
        "metafrontier",
        "references",
    }:
        return False, "publication_policy_not_declared_for_plot_kind"
    if kind in _DMU_PLOTS and dmu_id is None:
        return False, "requires_explicit_dmu_id"
    if (
        kind == "performance"
        and period is None
        and len(_unique_scalars(summary["period"])) > MAX_AUTO_FACETS
    ):
        return False, "requires_explicit_period"
    if kind in _PERIOD_PLOTS and not _period_is_unambiguous(summary, period):
        return False, "requires_explicit_period"
    if (
        kind == "trajectory"
        and dmu_id is not None
        and variable is None
        and _trajectory_needs_variable(result, dmu_id=dmu_id)
    ):
        return False, "requires_explicit_variable"
    if kind != "performance" and metric is not None:
        # A metric selection governs only the performance figure. Other plots
        # retain their own declared quantity semantics.
        return True, "included_with_independent_declared_quantity_semantics"
    return True, "declared_applicable_and_selection_safe"


def _plot_kwargs(
    kind: str,
    *,
    metric: str | None,
    period: object | None,
    dmu_id: object | None,
    variable: str | None,
    theme: str,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"theme": theme}
    if kind == "performance":
        kwargs.update(metric=metric, period=period)
    elif kind in {"frontier", "metafrontier"}:
        kwargs["period"] = period
    elif kind in {"process", "improvement"}:
        kwargs.update(dmu_id=dmu_id, period=period)
    elif kind == "trajectory":
        kwargs.update(dmu_id=dmu_id, variable=variable)
    return kwargs


def _load_matplotlib() -> tuple[Any, Any]:
    try:
        import matplotlib as mpl
        import matplotlib.pyplot as plt
    except ImportError as error:
        raise PublicationBundleNotAvailableError(
            "illustrated publication bundles require Matplotlib; install the "
            "visualization extra with pip install 'DEAPack[viz]'"
        ) from error
    return mpl, plt


def _render_svg(
    result: Any,
    info: PlotInfo,
    *,
    metric: str | None,
    period: object | None,
    dmu_id: object | None,
    variable: str | None,
    theme: str,
    mpl: Any,
    plt: Any,
) -> bytes:
    from ..results import DEAResult

    existing_figures = set(plt.get_fignums())
    figure: Any | None = None
    try:
        with mpl.rc_context(rc={"svg.hashsalt": _SVG_HASH_SALT}):
            figure = DEAResult.plot(
                result,
                info.kind,
                **_plot_kwargs(
                    info.kind,
                    metric=metric,
                    period=period,
                    dmu_id=dmu_id,
                    variable=variable,
                    theme=theme,
                ),
            )
            if not callable(getattr(figure, "savefig", None)):
                raise PublicationBundleNotAvailableError(
                    f"plot {info.kind!r} did not return a Matplotlib Figure"
                )
            buffer = io.BytesIO()
            figure.savefig(
                buffer,
                format="svg",
                metadata={"Creator": "DEAPack", "Date": None},
            )
            payload = buffer.getvalue()
    except ImportError as error:
        raise PublicationBundleNotAvailableError(
            "illustrated publication bundles require Matplotlib; install the "
            "visualization extra with pip install 'DEAPack[viz]'"
        ) from error
    finally:
        if figure is not None:
            plt.close(figure)
        for number in set(plt.get_fignums()).difference(existing_figures):
            plt.close(number)
    if b"<dc:date>" in payload:
        raise PublicationBundleNotAvailableError(
            f"plot {info.kind!r} SVG unexpectedly contains a generated date"
        )
    return payload


def _html_text(value: object) -> str:
    return html.escape(str(value), quote=True)


def _entry_html(
    *,
    metadata: Mapping[str, Any],
    plot_records: list[dict[str, Any]],
) -> bytes:
    method = metadata.get("method_id") or metadata.get("model_family") or "Not reported"
    model = metadata.get("model_family") or "Not reported"
    included = [record for record in plot_records if record["included"]]
    skipped = [record for record in plot_records if record["skipped"]]
    figures = "".join(
        (
            '<section class="figure-card">'
            f"<h2>{_html_text(record['title'])}</h2>"
            f"<p>{_html_text(record['description'])}</p>"
            f'<a href="{_html_text(record["path"])}">'
            f'<img src="{_html_text(record["path"])}" '
            f'alt="{_html_text(record["title"])}"></a>'
            '<p class="caption">Reusable SVG · '
            f"{_html_text(record['reason'].replace('_', ' '))}</p>"
            "</section>"
        )
        for record in included
    )
    if not figures:
        figures = (
            '<section class="notice"><h2>No safely selectable figure</h2>'
            "<p>The fitted result remains fully available in the audit archive. "
            "No chart was manufactured without declared plotting semantics or "
            "a required analyst selection.</p></section>"
        )
    omitted = "".join(
        "<li><strong>"
        f"{_html_text(record['title'])}</strong> — "
        f"{_html_text(record['reason'].replace('_', ' '))}</li>"
        for record in skipped
    )
    omitted_section = (
        "<details><summary>Plots not included in this bundle</summary>"
        f"<ul>{omitted}</ul></details>"
        if omitted
        else ""
    )
    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>DEAPack illustrated result publication</title>
  <style>
    :root {{ --ink:#21313b; --muted:#647780; --teal:#176b73;
            --paper:#ffffff; --wash:#eef5f5; --line:#d7e3e5; --amber:#a5531d; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; color:var(--ink); background:#f4f7f7;
            font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif; }}
    header {{ color:white; background:linear-gradient(130deg,#153f47,#176b73);
              padding:3.5rem max(1.3rem,calc((100% - 1120px)/2)); }}
    header p {{ color:#dceced; max-width:52rem; }}
    main {{ max-width:1120px; margin:0 auto; padding:2rem 1.3rem 4rem; }}
    .cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr));
              gap:.8rem; margin-top:-3.2rem; }}
    .card,.figure-card,.notice,details {{ background:var(--paper);
      border:1px solid var(--line); border-radius:12px; box-shadow:0 8px 24px #16353b12;
      padding:1rem 1.15rem; }}
    .label {{ color:var(--muted); font-size:.76rem; letter-spacing:.05em;
              text-transform:uppercase; }}
    .value {{ display:block; font-size:1.05rem; font-weight:650;
              overflow-wrap:anywhere; }}
    .figure-card {{ margin-top:1.4rem; padding:1.25rem; }}
    .figure-card h2 {{ margin:.1rem 0 .35rem; }}
    .figure-card img {{ display:block; width:100%; height:auto; margin:1rem auto;
                        border:1px solid var(--line); border-radius:8px; }}
    .caption {{ color:var(--muted); font-size:.86rem; }}
    .notice {{ border-left:.4rem solid var(--amber); margin:1.4rem 0; }}
    .audit {{ background:var(--wash); border-left:.4rem solid var(--teal);
              margin:1.5rem 0; padding:1rem 1.2rem; }}
    a {{ color:var(--teal); font-weight:650; }}
    details {{ margin-top:1.4rem; }}
    footer {{ color:var(--muted); font-size:.86rem; margin-top:2rem; }}
  </style>
</head>
<body>
  <header>
    <h1>Illustrated DEA result publication</h1>
    <p>A reader-first view of the fitted efficiency or productivity account,
       accompanied by its complete reproducible audit record.</p>
  </header>
  <main>
    <section class="cards">
      <div class="card"><span class="label">Method</span>
        <span class="value">{_html_text(method)}</span></div>
      <div class="card"><span class="label">Model family</span>
        <span class="value">{_html_text(model)}</span></div>
      <div class="card"><span class="label">Figures</span>
        <span class="value">{len(included)} included ·
          {len(skipped)} skipped</span></div>
    </section>
    <section class="notice">
      <strong>Interpretation boundary.</strong> These figures describe performance
      relative to the declared DEA technology and fitted reference account. They
      do not identify causes, establish managerial preferences, or prescribe an
      implementation plan. A displayed target or peer plan may be one selected
      optimum unless the audit record explicitly certifies uniqueness.
    </section>
    {figures}
    {omitted_section}
    <section class="audit">
      <h2>Complete audit record</h2>
      <p><a href="audit/result-audit.zip">Download the nested audit bundle</a>.
      It contains every non-empty public result table, metadata, its own HTML
      brief, and a separate SHA-256 manifest. The publication layer adds no solve.</p>
    </section>
    <footer>Generated by DEAPack. Integrity hashes verify archive bytes, not
      publisher authenticity.</footer>
  </main>
</body>
</html>
"""
    return document.encode("utf-8")


def _readme_bytes() -> bytes:
    return (
        b"DEAPack illustrated result publication\n"
        b"======================================\n\n"
        b"Extract this ZIP and open index.html. Reusable SVG figures are under "
        b"figures/. audit/result-audit.zip is the complete, unmodified DEAPack "
        b"audit bundle with all public result tables, metadata, and its own "
        b"integrity manifest. manifest.json describes every declared plot as "
        b"included or skipped and records the reason, selectors, SHA-256 hashes, "
        b"and the exporter-scoped zero-additional-solve contract. Publication is "
        b"restricted to the exact built-in DEAResult type; extension plot methods "
        b"are not called. Figures are descriptive views "
        b"of the fitted DEA account; they are not causal findings or management "
        b"prescriptions. Hashes establish file integrity, not authenticity.\n"
    )


def publish_result(
    result: object,
    path: str | PathLike[str],
    *,
    metric: str | None = None,
    period: object | None = None,
    dmu_id: object | None = None,
    variable: str | None = None,
    theme: str = "deapack",
) -> Path:
    """Atomically write one deterministic illustrated ``.zip`` publication.

    Plot discovery is delegated to ``result.available_plots()``. The exporter
    renders only declared plots that are safe under the supplied selectors,
    performs no optimization, and embeds the complete ordinary audit bundle.
    Matplotlib remains lazy and is required only when a figure is rendered.
    """
    from ..results import DEAResult

    if type(result) is not DEAResult:
        raise PublicationBundleNotAvailableError(
            "illustrated publication requires the exact built-in DEAResult type; "
            "third-party result extensions are not a trusted zero-solve source"
        )
    destination = Path(path)
    if destination.suffix.casefold() != ".zip":
        raise PublicationBundleNotAvailableError(
            "illustrated publication bundles require a .zip destination"
        )
    if theme != "deapack":
        raise PublicationBundleNotAvailableError(
            f"unknown publication theme {theme!r}; available theme: 'deapack'"
        )
    if metric is not None and (not isinstance(metric, str) or not metric.strip()):
        raise PublicationBundleNotAvailableError(
            "publication metric must be a non-empty string when supplied"
        )
    if variable is not None and (not isinstance(variable, str) or not variable.strip()):
        raise PublicationBundleNotAvailableError(
            "publication variable must be a non-empty string when supplied"
        )
    if variable is not None and dmu_id is None:
        raise PublicationBundleNotAvailableError(
            "publication variable selection requires dmu_id for one organization"
        )

    summary = _summary_frame(result)
    _validate_selector(summary, column="period", value=period)
    _validate_selector(summary, column="dmu_id", value=dmu_id)
    registry, declared = _declared_plots(result)
    declared_by_kind = {item.kind: item for item in declared}
    declared_kinds = frozenset(declared_by_kind)
    if metric is not None and "performance" not in declared_kinds:
        raise PublicationBundleNotAvailableError(
            "metric was supplied but performance is not declared by available_plots()"
        )
    if variable is not None and "trajectory" not in declared_kinds:
        raise PublicationBundleNotAvailableError(
            "variable was supplied but trajectory is not declared by available_plots()"
        )
    if dmu_id is not None and not declared_kinds.intersection(_DMU_PLOTS):
        raise PublicationBundleNotAvailableError(
            "dmu_id was supplied but no declared plot accepts an organization selection"
        )

    plot_records: list[dict[str, Any]] = []
    render_queue: list[tuple[PlotInfo, dict[str, Any]]] = []
    for registry_info in registry:
        info = declared_by_kind.get(registry_info.kind, registry_info)
        include, reason = _plot_policy(
            info,
            declared_kinds=declared_kinds,
            summary=summary,
            result=result,
            metric=metric,
            period=period,
            dmu_id=dmu_id,
            variable=variable,
        )
        record: dict[str, Any] = {
            "kind": info.kind,
            "title": info.title,
            "description": info.description,
            "included": False,
            "skipped": not include,
            "reason": reason,
            "path": None,
            "backend": info.backend,
        }
        plot_records.append(record)
        if include:
            render_queue.append((info, record))

    svg_payloads: list[tuple[str, bytes]] = []
    if render_queue:
        mpl, plt = _load_matplotlib()
        for info, record in render_queue:
            try:
                svg = _render_svg(
                    result,
                    info,
                    metric=metric,
                    period=period,
                    dmu_id=dmu_id,
                    variable=variable,
                    theme=theme,
                    mpl=mpl,
                    plt=plt,
                )
            except PlotNotAvailableError as error:
                if info.kind == "performance" and metric is not None:
                    raise PublicationBundleNotAvailableError(
                        f"requested publication metric is not plot available: {error}"
                    ) from error
                if info.kind == "trajectory" and variable is not None:
                    raise PublicationBundleNotAvailableError(
                        f"requested publication variable is not plot available: {error}"
                    ) from error
                record.update(
                    skipped=True,
                    reason=f"selected_account_not_plot_available: {error}",
                )
                continue
            except PublicationBundleNotAvailableError:
                raise
            except (
                AttributeError,
                OSError,
                RuntimeError,
                TypeError,
                ValueError,
            ) as error:
                raise PublicationBundleNotAvailableError(
                    f"could not render publication plot {info.kind!r}: {error}"
                ) from error
            member = _safe_member_path(f"figures/{info.kind}.svg")
            record.update(
                included=True,
                skipped=False,
                path=member,
            )
            svg_payloads.append((member, svg))

    metadata_source = getattr(result, "metadata", None)
    if not isinstance(metadata_source, Mapping):
        raise PublicationBundleNotAvailableError(
            "publication source metadata must be mapping-like"
        )
    metadata = _json_value(metadata_source, location="metadata")
    if not isinstance(metadata, dict):
        raise PublicationBundleNotAvailableError(
            "publication source metadata could not be represented as JSON"
        )
    selectors = _json_value(
        {
            "metric": metric,
            "period": period,
            "dmu_id": dmu_id,
            "variable": variable,
            "theme": theme,
        },
        location="publication.selectors",
    )

    audit_path: Path | None = None
    temporary_path: Path | None = None
    descriptor: int | None = None
    try:
        audit_descriptor, raw_audit_path = tempfile.mkstemp(
            dir=destination.parent,
            prefix=f".{destination.name}.audit.",
            suffix=".zip",
        )
        os.close(audit_descriptor)
        audit_path = Path(raw_audit_path)
        try:
            export_result_bundle(result, audit_path)
        except ReportNotAvailableError as error:
            raise PublicationBundleNotAvailableError(
                f"could not create the nested audit bundle: {error}"
            ) from error

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
                    _write_publication_bytes(archive, "README.txt", _readme_bytes())
                )
                file_manifest.append(
                    _write_publication_bytes(
                        archive,
                        "index.html",
                        _entry_html(metadata=metadata, plot_records=plot_records),
                    )
                )
                for member, payload in svg_payloads:
                    file_manifest.append(
                        _write_publication_bytes(archive, member, payload)
                    )
                audit_record = _stream_publication_file(
                    archive,
                    "audit/result-audit.zip",
                    audit_path,
                )
                file_manifest.append(audit_record)
                file_manifest.sort(key=lambda item: item["path"])
                manifest = {
                    "publication_schema_version": _PUBLICATION_SCHEMA_VERSION,
                    "package": {"name": "DEAPack", "version": _package_version()},
                    "method_id": metadata.get("method_id"),
                    "model_family": metadata.get("model_family"),
                    "selectors": selectors,
                    "plots": plot_records,
                    "audit": {
                        **audit_record,
                        "complete_existing_audit_bundle": True,
                        "nested_manifest": "manifest.json",
                    },
                    "files": file_manifest,
                    "integrity": {
                        "algorithm": "sha256",
                        "scope": "all_archive_members_except_manifest.json",
                        "authenticity_claim": False,
                    },
                    "semantics": {
                        "source": "public_result_snapshot_v1",
                        "trusted_result_type": "deapack.results.DEAResult",
                        "third_party_result_extensions_supported": False,
                        "plot_discovery": "DEAResult.available_plots",
                        "additional_solver_calls": 0,
                        "additional_solver_calls_scope": (
                            "deapack_publication_exporter_on_exact_dearesult"
                        ),
                        "causal_claim": False,
                        "prescriptive_claim": False,
                        "selected_target_uniqueness_claim": False,
                    },
                }
                _write_publication_bytes(
                    archive,
                    "manifest.json",
                    _json_bytes(manifest),
                )
            temporary_stream.flush()
            os.fsync(temporary_stream.fileno())
        os.replace(temporary_path, destination)
        temporary_path = None
    except PublicationBundleNotAvailableError:
        raise
    except (
        OSError,
        TypeError,
        ValueError,
        zipfile.BadZipFile,
        zipfile.LargeZipFile,
    ) as error:
        raise PublicationBundleNotAvailableError(
            f"could not write illustrated publication bundle: {error}"
        ) from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        if audit_path is not None:
            audit_path.unlink(missing_ok=True)
    return destination


__all__ = ["PublicationBundleNotAvailableError", "publish_result"]
