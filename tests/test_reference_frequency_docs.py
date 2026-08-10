from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs" / "analysis" / "reference-frequency.md"


def test_reference_frequency_documentation_preserves_narrow_claim() -> None:
    text = PAGE.read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    for statement in (
        "which observed organizations recur in the peer plans selected by the solver",
        "result.reference_frequency()",
        "reference_frequency(result)",
        '"reference_frequency"',
        '"self_reference_frequency"',
        '"other_reference_frequency"',
        '"reference_rate"',
        "active edges",
        "$\\tau_{\\mathrm{peer}}$",
        "\\lambda_{oj}>\\tau_{\\mathrm{peer}}",
        "source peer-reporting\nthreshold",
        "not an exact mathematical-support\ncount",
        "does not add $\\lambda_{oj}$ across different evaluated organizations",
        'frequency.metadata["alternate_optima_assessed"]',
        'frequency.metadata["global_reference_set_claim"]',
        'frequency.metadata["outlier_claim"]',
        'frequency.metadata["inference"]',
        'frequency.metadata["additional_solver_calls"]',
        'frequency.metadata["source_peer_tolerance"]',
        'frequency.metadata["reference_rate_denominator"]',
        "10.1007/BF00162048",
        "10.1080/03155986.1995.11732281",
        "10.1016/j.ejor.2015.03.029",
        "implements neither ranking procedure",
        "does not solve their identification problem",
        "FDH, FCH, FRH, panel, network, dynamic",
        "The release gate is atomic",
        "including zero-frequency organizations",
        'result.plot(kind="references")',
        "../user-guide/visualization",
    ):
        assert " ".join(statement.split()) in normalized
    for forbidden in (
        "reference_share",
        "Share of 8 evaluations",
        "identifies the global reference set",
        "proves superior management",
        "detects outliers",
    ):
        assert forbidden not in text


def test_reference_frequency_page_and_generated_api_are_navigable() -> None:
    docs_index = (ROOT / "docs" / "index.md").read_text(encoding="utf-8")
    analysis_landing = (
        ROOT / "docs" / "reference" / "scale-capacity-decomposition.md"
    ).read_text(encoding="utf-8")
    api = (ROOT / "docs" / "api" / "analysis.md").read_text(encoding="utf-8")
    normalized_api = " ".join(api.split())

    assert "reference/index" in docs_index
    assert "/analysis/reference-frequency" in analysis_landing
    assert "{autofunction} deapack.reference_frequency" in api
    assert "{autoclass} deapack.ReferenceFrequencyResult" in api
    assert "{doc}`../analysis/reference-frequency`" in api
    assert "all-optima" in api
    assert "source result's `peer_tolerance`" in normalized_api
    assert "exact mathematical support" in normalized_api
