"""Immutable public reporting contracts."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field
from html import escape
from os import PathLike
from pathlib import Path


class ReportNotAvailableError(ValueError):
    """Raised when a requested report cannot be constructed faithfully."""


_REPORT_CSS = """
.deapack-report {
  --ink: #24323d;
  --muted: #687780;
  --grid: #dce5e7;
  --teal: #176b73;
  --teal-soft: #e6f1f1;
  --orange: #b95f21;
  --orange-soft: #fff0e5;
  color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.45;
  max-width: 1120px;
}
.deapack-report * { box-sizing: border-box; }
.deapack-report h1 {
  font-size: 1.65rem;
  line-height: 1.2;
  margin: 0 0 .35rem;
}
.deapack-report h2 {
  border-bottom: 1px solid var(--grid);
  font-size: 1.08rem;
  margin: 1.5rem 0 .75rem;
  padding-bottom: .35rem;
}
.deapack-report .subtitle {
  color: var(--muted);
  margin: 0 0 1rem;
}
.deapack-report .cards {
  display: grid;
  gap: .65rem;
  grid-template-columns: repeat(auto-fit, minmax(185px, 1fr));
  margin: .75rem 0;
}
.deapack-report .card {
  background: #f7fafb;
  border: 1px solid var(--grid);
  border-radius: 8px;
  min-height: 76px;
  padding: .7rem .8rem;
}
.deapack-report .card-label {
  color: var(--muted);
  display: block;
  font-size: .76rem;
  letter-spacing: .02em;
  margin-bottom: .25rem;
  text-transform: uppercase;
}
.deapack-report .card-value {
  font-size: 1.08rem;
  font-weight: 650;
  overflow-wrap: anywhere;
}
.deapack-report .measure-note,
.deapack-report .notice,
.deapack-report .warning {
  border-left: 4px solid var(--teal);
  border-radius: 4px;
  margin: .65rem 0;
  padding: .65rem .8rem;
}
.deapack-report .measure-note,
.deapack-report .notice { background: var(--teal-soft); }
.deapack-report .warning {
  background: var(--orange-soft);
  border-left-color: var(--orange);
}
.deapack-report table {
  border-collapse: collapse;
  font-size: .88rem;
  margin: .45rem 0 .8rem;
  width: 100%;
}
.deapack-report th,
.deapack-report td {
  border-bottom: 1px solid var(--grid);
  padding: .42rem .5rem;
  text-align: left;
  vertical-align: top;
}
.deapack-report th {
  background: #f2f6f7;
  font-weight: 650;
}
.deapack-report tbody tr:nth-child(even) { background: #fbfcfc; }
.deapack-report .footnote {
  color: var(--muted);
  font-size: .8rem;
  margin: .35rem 0;
}
""".strip()


@dataclass(frozen=True, slots=True, init=False)
class ResultReport:
    """One immutable, self-contained DEAPack result report.

    The report stores already escaped, deterministic HTML rather than live
    result tables. This prevents later mutation of a ``DEAResult`` or a pandas
    object from changing the report after it has been prepared.
    """

    kind: str
    title: str
    metric: str | None
    observation_count: int
    optimal_count: int
    nonoptimal_count: int
    omitted_metric_count: int
    invalid_metric_count: int
    warnings: tuple[str, ...] = ()
    _body_html: str = field(default="", repr=False, init=False)

    def __init__(self) -> None:
        """Prevent construction with untrusted HTML.

        Reports are created only by :meth:`DEAResult.report`. Keeping the
        raw prepared fragment out of the public constructor preserves the
        escaping boundary promised by ``_repr_html_`` and ``save``.
        """
        raise TypeError("ResultReport objects are created by DEAResult.report()")

    def __post_init__(self) -> None:
        if self.kind != "brief":
            raise ValueError("ResultReport kind must be 'brief'")
        if not self.title.strip():
            raise ValueError("ResultReport title must be non-empty")
        for name in (
            "observation_count",
            "optimal_count",
            "nonoptimal_count",
            "omitted_metric_count",
            "invalid_metric_count",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be nonnegative")
        if self.optimal_count + self.nonoptimal_count != self.observation_count:
            raise ValueError(
                "optimal_count and nonoptimal_count must sum to observation_count"
            )
        if self.omitted_metric_count > self.observation_count:
            raise ValueError("omitted_metric_count cannot exceed observation_count")
        if self.invalid_metric_count > self.observation_count:
            raise ValueError("invalid_metric_count cannot exceed observation_count")
        if not isinstance(self.warnings, tuple) or not all(
            isinstance(item, str) for item in self.warnings
        ):
            raise TypeError("warnings must be an immutable tuple of strings")

    def to_html(self, *, full_document: bool = True) -> str:
        """Return escaped HTML, optionally as a complete standalone document."""
        fragment = (
            f"<style>{_REPORT_CSS}</style>"
            f'<article class="deapack-report">{self._body_html}</article>'
        )
        if not full_document:
            return fragment
        safe_title = escape(self.title, quote=True)
        return (
            "<!doctype html>\n"
            '<html lang="en">\n'
            "<head>\n"
            '<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f"<title>{safe_title}</title>\n"
            "</head>\n"
            f"<body>{fragment}</body>\n"
            "</html>\n"
        )

    def _repr_html_(self) -> str:
        """Return the safe report fragment used by notebook frontends."""
        return self.to_html(full_document=False)

    def save(self, path: str | PathLike[str]) -> Path:
        """Write a standalone HTML report and return the destination path."""
        destination = Path(path)
        if destination.suffix.casefold() not in {".html", ".htm"}:
            raise ReportNotAvailableError(
                "ResultReport.save currently supports only .html or .htm files"
            )
        payload = self.to_html(full_document=True).encode("utf-8")
        temporary_path: Path | None = None
        try:
            descriptor, raw_path = tempfile.mkstemp(
                dir=destination.parent,
                prefix=f".{destination.name}.",
                suffix=".tmp",
            )
            temporary_path = Path(raw_path)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, destination)
            temporary_path = None
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
        return destination


def _prepared_result_report(
    *,
    kind: str,
    title: str,
    metric: str | None,
    observation_count: int,
    optimal_count: int,
    nonoptimal_count: int,
    omitted_metric_count: int,
    invalid_metric_count: int,
    warnings: tuple[str, ...],
    body_html: str,
) -> ResultReport:
    """Build one report from an internally escaped HTML fragment."""
    report = object.__new__(ResultReport)
    values = {
        "kind": kind,
        "title": title,
        "metric": metric,
        "observation_count": observation_count,
        "optimal_count": optimal_count,
        "nonoptimal_count": nonoptimal_count,
        "omitted_metric_count": omitted_metric_count,
        "invalid_metric_count": invalid_metric_count,
        "warnings": tuple(warnings),
        "_body_html": body_html,
    }
    for name, value in values.items():
        object.__setattr__(report, name, value)
    report.__post_init__()
    return report


__all__ = ["ReportNotAvailableError", "ResultReport"]
