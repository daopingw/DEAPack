from __future__ import annotations

import inspect
import subprocess
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import ClassVar, get_type_hints

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from deapack import (
    DEAData,
    DEAResult,
    PriceData,
    ReferenceSpec,
    scale_efficiency,
)
from deapack.economics.profit import ProfitEfficiency
from deapack.reporting import (
    ReportNotAvailableError,
    ResultReport,
    create_result_report,
)


def _result(
    *,
    dmus: list[object] | None = None,
    periods: list[object] | None = None,
    efficiencies: list[object] | None = None,
    statuses: list[object] | None = None,
    metadata: dict[str, object] | None = None,
) -> DEAResult:
    values = [0.8, 1.0] if efficiencies is None else efficiencies
    count = len(values)
    summary = pd.DataFrame(
        {
            "dmu_id": (
                [f"DMU-{index + 1}" for index in range(count)] if dmus is None else dmus
            ),
            "period": [None] * count if periods is None else periods,
            "score": values,
            "efficiency": values,
            "distance": [pd.NA] * count,
            "is_efficient": pd.array(
                [
                    pd.NA if pd.isna(value) else bool(float(value) == 1.0)
                    for value in values
                ],
                dtype="boolean",
            ),
            "solver_status": (["optimal"] * count if statuses is None else statuses),
            "model_family": ["test_radial"] * count,
        }
    )
    return DEAResult(
        summary_frame=summary,
        metadata={
            "method_id": "static.radial",
            "expanded_spec": {
                "performance": {"orientation": "input"},
                "technology": {"returns_to_scale": "vrs"},
                "reference": {"kind": "contemporaneous"},
            },
            **({} if metadata is None else metadata),
        },
    )


def test_result_report_is_immutable_and_has_notebook_and_document_html() -> None:
    report = _result().report()

    assert isinstance(report, ResultReport)
    assert report.kind == "brief"
    assert report.metric == "efficiency"
    assert report.observation_count == 2
    assert report.optimal_count == 2
    assert report.nonoptimal_count == 0
    assert report.omitted_metric_count == 0
    assert report.invalid_metric_count == 0
    assert report._repr_html_() == report.to_html(full_document=False)
    assert report.to_html().startswith("<!doctype html>")
    assert '<article class="deapack-report">' in report.to_html()
    with pytest.raises(FrozenInstanceError):
        report.metric = "score"  # type: ignore[misc]


def test_result_report_constructor_cannot_accept_untrusted_html() -> None:
    attack = '<img src=x onerror="alert(1)"><script>alert(2)</script>'

    assert "_body_html" not in inspect.signature(ResultReport).parameters
    with pytest.raises(TypeError, match=r"created by DEAResult\.report"):
        ResultReport()
    with pytest.raises(TypeError):
        ResultReport(_body_html=attack)  # type: ignore[call-arg]


def test_dea_result_report_runtime_type_hint_resolves() -> None:
    assert get_type_hints(DEAResult.report)["return"] is ResultReport


def test_report_does_not_import_matplotlib() -> None:
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
            "DEAResult(frame).report().to_html()",
            "assert not any(name == 'matplotlib' or ",
            "               name.startswith('matplotlib.') ",
            "               for name in sys.modules)",
        )
    )

    subprocess.run([sys.executable, "-c", command], check=True)


def test_report_escapes_result_and_metadata_text_without_active_content() -> None:
    attack = '<script>alert("unsafe")</script>'
    result = _result(
        dmus=[attack],
        efficiencies=[0.8],
        metadata={"method_id": attack},
    )

    html = result.report(dmu_id=attack).to_html()

    assert "<script" not in html
    assert "&lt;script&gt;" in html
    assert "alert(&quot;unsafe&quot;)" in html
    assert "<link" not in html
    assert " href=" not in html
    assert " src=" not in html


def test_report_counts_nonoptimal_and_missing_measure_rows_without_mutation() -> None:
    result = _result(
        efficiencies=[0.8, pd.NA, 0.6],
        statuses=["optimal", "optimal", "limit_reached"],
    )
    before = result.summary()

    report = result.report()

    assert report.observation_count == 3
    assert report.optimal_count == 2
    assert report.nonoptimal_count == 1
    assert report.omitted_metric_count == 1
    assert any("summary solver_status='optimal'" in item for item in report.warnings)
    assert any("missing or non-finite" in item for item in report.warnings)
    assert "Non-optimal — excluded" in report.to_html()
    assert "limit_reached" in report.to_html()
    assert_frame_equal(result.summary(), before)


def test_period_and_dmu_filters_are_applied_before_report_preparation() -> None:
    result = _result(
        dmus=["AlphaOnly", "BetaExcluded", "AlphaOnly", "BetaExcluded"],
        periods=[2020, 2020, 2021, 2021],
        efficiencies=[0.7, 0.8, 0.9, 1.0],
    )

    focused = result.report(period=2021, dmu_id="AlphaOnly")
    all_alpha = result.report(dmu_id="AlphaOnly")

    assert focused.observation_count == 1
    assert "AlphaOnly" in focused.to_html()
    assert "BetaExcluded" not in focused.to_html()
    assert "2021" in focused.to_html()
    assert "2020" not in focused.to_html()
    assert all_alpha.observation_count == 2
    assert "2020" in all_alpha.to_html()
    assert "2021" in all_alpha.to_html()


def test_tuple_dmu_id_is_filtered_as_one_opaque_identifier() -> None:
    result = _result(
        dmus=[("hospital", 1), ("hospital", 2)],
        efficiencies=[0.7, 0.9],
    )

    report = result.report(dmu_id=("hospital", 2))

    assert report.observation_count == 1
    assert "(&#x27;hospital&#x27;, 2)" in report.to_html()
    assert "(&#x27;hospital&#x27;, 1)" not in report.to_html()


def test_missing_period_and_dmu_filters_fail_with_available_values() -> None:
    result = _result(
        dmus=["A", "B"],
        periods=[2020, 2021],
    )

    with pytest.raises(ReportNotAvailableError, match="available periods"):
        result.report(period=2019)
    with pytest.raises(ReportNotAvailableError, match="available DMUs"):
        result.report(period=2021, dmu_id="A")


def test_available_filter_values_are_bounded() -> None:
    result = _result(
        dmus=[f"DMU-{index}" for index in range(12)],
        efficiencies=[0.8] * 12,
    )

    with pytest.raises(ReportNotAvailableError) as captured:
        result.report(dmu_id="missing")

    message = str(captured.value)
    assert "… (+4 more)" in message
    assert "'DMU-11'" not in message


def test_report_save_writes_standalone_html_and_rejects_other_suffixes(
    tmp_path: Path,
) -> None:
    report = _result().report()
    destination = tmp_path / "brief.html"

    returned = report.save(destination)

    assert returned == destination
    assert destination.read_text(encoding="utf-8") == report.to_html()
    with pytest.raises(ReportNotAvailableError, match=r"only \.html or \.htm"):
        report.save(tmp_path / "brief.pdf")


def test_report_save_encodes_before_replacing_an_existing_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "brief.html"
    destination.write_text("existing report", encoding="utf-8")

    monkeypatch.setattr(ResultReport, "to_html", lambda *args, **kwargs: "\ud800")
    with pytest.raises(UnicodeEncodeError):
        _result().report().save(destination)

    assert destination.read_text(encoding="utf-8") == "existing report"


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"kind": "dashboard"}, "unknown report kind"),
        ({"detail": "audit"}, "unknown report detail"),
        ({"theme": "paper"}, "unknown report theme"),
        ({"metric": ""}, "metric must be a non-empty"),
        ({"metric": "made_up"}, "is not present"),
    ],
)
def test_report_rejects_unsupported_or_undeclared_requests(
    kwargs: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ReportNotAvailableError, match=message):
        _result().report(**kwargs)  # type: ignore[arg-type]


def test_report_without_a_valid_measure_degrades_to_audit_coverage() -> None:
    result = _result(efficiencies=[pd.NA, pd.NA])
    report = result.report()

    assert report.metric is None
    assert report.observation_count == 2
    assert report.omitted_metric_count == 0
    assert "No declared valid finite optimal performance measure" in report.to_html()
    assert any("finite optimal" in warning for warning in report.warnings)
    with pytest.raises(ReportNotAvailableError, match="finite optimal"):
        result.report(metric="efficiency")


def test_report_is_not_limited_by_plot_facet_cap_and_samples_periods_fairly() -> None:
    periods = [period for period in range(2020, 2025) for _ in range(10)]
    report = _result(
        dmus=[
            f"{period}-{index}" for period in range(2020, 2025) for index in range(10)
        ],
        periods=periods,
        efficiencies=[0.5 + index / 100 for index in range(50)],
    ).report()
    html = report.to_html()

    assert report.metric == "efficiency"
    assert report.observation_count == 50
    for period in range(2020, 2025):
        assert f"Period {period}" in html


def test_report_keeps_valid_period_when_another_period_is_nonoptimal() -> None:
    result = _result(
        dmus=["infeasible-2020", "certified-2021"],
        periods=[2020, 2021],
        efficiencies=[0.6, 0.9],
        statuses=["infeasible", "optimal"],
    )

    report = result.report()
    html = report.to_html()

    assert report.metric == "efficiency"
    assert "certified-2021" in html
    assert "infeasible-2020" in html
    assert "Non-optimal — excluded" in html


def test_profit_gap_with_undefined_external_reference_is_diagnostic_only() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["reference", "evaluated"],
                "input": [5.0, 1.0],
                "output": [1.0, 5.0],
            }
        ),
        dmu="dmu",
        inputs="input",
        outputs="output",
    )
    prices = PriceData.common(
        input_prices={"input": 1.0},
        output_prices={"output": 1.0},
    )
    result = ProfitEfficiency(
        reference=ReferenceSpec(kind="custom", custom_rows=[0])
    ).fit(data, prices)

    report = result.report()
    html = report.to_html()

    assert report.metric == "profit_gap"
    assert report.invalid_metric_count == 1
    assert "Measure undefined — excluded" in html
    assert "undefined_external_reference" in html
    assert "-8.0" in html


def test_scale_efficiency_is_the_default_report_measure() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "unit": ["A", "B", "C"],
                "input": [1.0, 2.0, 1.0],
                "output": [1.0, 1.0, 0.5],
            }
        ),
        dmu="unit",
        inputs="input",
        outputs="output",
    )

    assert scale_efficiency(data).report().metric == "scale_efficiency"


@pytest.mark.parametrize(
    ("method_id", "identification_field", "expected_warning"),
    [
        (
            "network.sbm.tone_tsutsui_2009",
            "all_division_efficiency_identified_by_system_one",
            "does not establish efficiency for every division",
        ),
        (
            "dynamic.network_sbm.tone_tsutsui_2014",
            "all_account_efficiency_identified_by_system_one",
            "does not establish efficiency for every period and process",
        ),
    ],
)
def test_report_discloses_zero_weight_system_scope(
    method_id: str,
    identification_field: str,
    expected_warning: str,
) -> None:
    result = _result(
        efficiencies=[1.0],
        metadata={
            "method_id": method_id,
            "native_score": "system_efficiency",
            "score_direction": "higher_is_better",
            identification_field: False,
        },
    )
    result.summary_frame["system_efficiency"] = [1.0]

    report = result.report()
    html = report.to_html()

    assert report.metric == "system_efficiency"
    assert any(expected_warning in warning for warning in report.warnings)
    assert expected_warning in html
    assert "positively weighted" in html
    assert "Efficient value" not in html


def test_component_validity_count_is_not_bounded_by_overall_optimal_count() -> None:
    result = _result(
        efficiencies=[0.8, 0.7],
        statuses=["component_failure", "component_failure"],
        metadata={
            "method_id": ("heterogeneity.metafrontier.radial.odonnell_rao_battese_2008")
        },
    )
    result.summary_frame["group_efficiency"] = [0.8, 0.7]
    result.summary_frame["group_solver_status"] = ["optimal", "optimal"]
    result.summary_frame["score_valid"] = [False, False]
    result.summary_frame["group_score_valid"] = [True, False]

    report = result.report()

    assert report.metric == "group_efficiency"
    assert report.optimal_count == 0
    assert report.invalid_metric_count == 1
    assert "Measure undefined — excluded" in report.to_html()


def test_radial_report_retains_a_certified_primary_score_after_completion_failure() -> (
    None
):
    result = _result(
        efficiencies=[0.8, 1.0],
        statuses=["limit_reached", "optimal"],
    )
    result.summary_frame["primary_solver_status"] = ["optimal", "optimal"]
    result.summary_frame["score_valid"] = [True, True]
    result.summary_frame["score_status"] = ["defined", "defined"]

    report = result.report()
    html = report.to_html()

    assert report.metric == "efficiency"
    assert report.optimal_count == 1
    assert report.nonoptimal_count == 1
    assert report.invalid_metric_count == 0
    assert "DMU-1" in html
    assert "Result-status optimal" in html
    assert "separately certified primary measure" in html


def test_invalid_public_summary_schema_fails_as_report_error() -> None:
    class InvalidPublicResult:
        metadata: ClassVar[dict[str, object]] = {}

        def summary(self, *, copy: bool = True) -> pd.DataFrame:
            del copy
            return pd.DataFrame({"dmu_id": ["A"]})

    with pytest.raises(ReportNotAvailableError, match="missing reporting columns"):
        create_result_report(InvalidPublicResult())


def test_builder_uses_only_public_summary_and_metadata_contract() -> None:
    base = _result()

    class PublicResult:
        metadata = base.metadata

        def summary(self, *, copy: bool = True) -> pd.DataFrame:
            return base.summary(copy=copy)

        @property
        def targets(self) -> object:
            raise AssertionError("the brief must not inspect target schemas")

        @property
        def components(self) -> object:
            raise AssertionError("the brief must not inspect component schemas")

        @property
        def links(self) -> object:
            raise AssertionError("the brief must not inspect link schemas")

    report = create_result_report(PublicResult())

    assert report.metric == "efficiency"
    assert report.observation_count == 2
