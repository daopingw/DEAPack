#!/usr/bin/env python3
"""Fail closed when bundled dataset rights metadata is not release-ready.

This script audits declarations maintained by DEAPack.  It does not decide
whether a dataset is legally redistributable, interpret a licence, or infer
permission from authorship, citation, publication, or the package licence.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class DatasetDistributionFinding:
    """One bundled dataset whose declared metadata blocks a release."""

    name: str
    source_kind: str
    redistribution_status: str
    license_identifier: str | None
    reasons: tuple[str, ...]

    @property
    def is_published_reproduction(self) -> bool:
        """Return whether the record declares a reproduced published table."""

        return self.source_kind == "published_reproduction"


@dataclass(frozen=True, slots=True)
class DatasetDistributionAudit:
    """Immutable release audit over the complete bundled dataset inventory."""

    dataset_count: int
    findings: tuple[DatasetDistributionFinding, ...]

    @property
    def passed(self) -> bool:
        """Return whether every bundled dataset has affirmative declarations."""

        return not self.findings

    @property
    def published_reproduction_findings(
        self,
    ) -> tuple[DatasetDistributionFinding, ...]:
        """Return blockers declared as published reproductions."""

        return tuple(
            finding for finding in self.findings if finding.is_published_reproduction
        )


def audit_dataset_distribution(
    datasets: Iterable[Any],
) -> DatasetDistributionAudit:
    """Audit declared redistribution and licence metadata without inference.

    A release passes only when every bundled dataset explicitly declares
    ``redistribution_status="cleared"`` and supplies a non-empty
    ``license_identifier``.  ``unknown`` and ``restricted`` both fail closed.
    The function deliberately does not assess whether a declaration is legally
    sufficient or correct.
    """

    records = sorted(tuple(datasets), key=lambda record: str(record.name))
    findings: list[DatasetDistributionFinding] = []
    for record in records:
        provenance = record.provenance
        status = str(provenance.redistribution_status)
        raw_license = provenance.license_identifier
        license_identifier = (
            None if raw_license is None else str(raw_license).strip() or None
        )
        reasons: list[str] = []
        if status != "cleared":
            reasons.append(
                f"redistribution_status={status!r}; expected an explicit 'cleared'"
            )
        if license_identifier is None:
            reasons.append("license_identifier is missing")
        if reasons:
            findings.append(
                DatasetDistributionFinding(
                    name=str(record.name),
                    source_kind=str(provenance.source_kind),
                    redistribution_status=status,
                    license_identifier=license_identifier,
                    reasons=tuple(reasons),
                )
            )
    return DatasetDistributionAudit(
        dataset_count=len(records),
        findings=tuple(findings),
    )


def audit_bundled_datasets() -> DatasetDistributionAudit:
    """Audit the dataset inventory imported from the active DEAPack build."""

    from deapack import list_datasets

    return audit_dataset_distribution(list_datasets())


def format_audit(report: DatasetDistributionAudit) -> str:
    """Render a stable, reviewer-readable release-gate report."""

    disclaimer = (
        "This gate checks declared metadata only; it does not determine legal "
        "rights, validate a licence, or infer permission."
    )
    if report.passed:
        return (
            "release dataset-distribution audit passed: "
            f"{report.dataset_count} bundled dataset record(s) declare "
            "redistribution_status='cleared' and a license_identifier.\n"
            f"{disclaimer}"
        )

    published = report.published_reproduction_findings
    lines = [
        "release dataset-distribution audit FAILED: "
        f"{len(report.findings)} of {report.dataset_count} bundled dataset "
        "record(s) lack release-ready declarations.",
        f"published-reproduction blockers: {len(published)}",
        disclaimer,
    ]
    for finding in report.findings:
        marker = " PUBLISHED-REPRODUCTION" if finding.is_published_reproduction else ""
        lines.append(
            f"- {finding.name} [{finding.source_kind}]{marker}: "
            + "; ".join(finding.reasons)
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Run the audit and return a release-gate-compatible exit status."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    report = audit_bundled_datasets()
    print(format_audit(report))
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
