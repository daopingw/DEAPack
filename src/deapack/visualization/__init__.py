"""Optional, backend-lazy visualization for unified DEAPack results."""

from __future__ import annotations

from dataclasses import replace
from difflib import get_close_matches
from typing import Any

from ._types import MeasureSpec, PlotInfo, PlotNotAvailableError
from .directional_improvement import (
    DirectionalDDFImprovementPlotData,
    directional_ddf_improvement_plot_applicable,
    directional_ddf_improvement_route,
    prepare_directional_ddf_improvement_data,
)
from .environmental_improvement import (
    EnvironmentalDDFImprovementPlotData,
    environmental_ddf_improvement_plot_applicable,
    environmental_ddf_improvement_route,
    prepare_environmental_ddf_improvement_data,
)
from .frontier import (
    FrontierPlotData,
    frontier_plot_applicable,
    prepare_frontier_data,
)
from .measures import (
    default_measure_spec,
    measure_certification_mask,
    measure_validity_mask,
    plottable_measure_specs,
)
from .metafrontier import (
    MetafrontierPlotData,
    metafrontier_plot_applicable,
    prepare_metafrontier_data,
)
from .network_process import (
    ProcessAttributionPlotData,
    prepare_process_attribution_data,
    process_attribution_plot_applicable,
)
from .performance import prepare_performance_data
from .radial_improvement import (
    RadialImprovementPlotData,
    prepare_radial_improvement_data,
    radial_improvement_plot_applicable,
    radial_improvement_route,
)
from .reference_frequency import (
    ReferenceFrequencyPlotData,
    prepare_reference_frequency_data,
    reference_frequency_plot_applicable,
)
from .sbm_improvement import (
    SBMImprovementPlotData,
    prepare_sbm_improvement_data,
    sbm_improvement_plot_applicable,
)
from .trajectory import (
    TrajectoryPlotData,
    prepare_trajectory_data,
    trajectory_plot_applicable,
)

_PLOTS = (
    PlotInfo(
        kind="performance",
        title="Performance",
        description=(
            "DMU-level values as a ranked point plot or an empirical "
            "cumulative distribution"
        ),
        default_metric="efficiency",
        views=("auto", "points", "ecdf"),
        backend="matplotlib",
        install_hint="pip install 'DEAPack[viz]'",
    ),
    PlotInfo(
        kind="frontier",
        title="Production frontier and targets",
        description=(
            "Observed one-input/one-output operating plans, the fitted CRS or "
            "VRS frontier, and certified moves to DEA targets"
        ),
        default_metric=None,
        views=("auto",),
        backend="matplotlib",
        install_hint="pip install 'DEAPack[viz]'",
    ),
    PlotInfo(
        kind="trajectory",
        title="Observed and selected carry-over trajectory",
        description=(
            "One certified Dynamic-SBM carry-over path, its adjacent-period "
            "inheritance account, and period operating-plan performance"
        ),
        default_metric=None,
        views=("auto",),
        backend="matplotlib",
        install_hint="pip install 'DEAPack[viz]'",
    ),
    PlotInfo(
        kind="process",
        title="Process performance and coordinated handoffs",
        description=(
            "One certified input-oriented Network-SBM system account, its "
            "declared-weight process attribution, and selected fixed/free "
            "internal handoffs"
        ),
        default_metric=None,
        views=("auto",),
        backend="matplotlib",
        install_hint="pip install 'DEAPack[viz]'",
    ),
    PlotInfo(
        kind="improvement",
        title="Variable-specific operating plan",
        description=(
            "One certified original-unit operating account for classic radial "
            "DEA, classic static SBM, separable strongly disposable "
            "environmental SBM, ordinary static DDF, or core CRS common-factor "
            "environmental DDF"
        ),
        default_metric=None,
        views=("auto",),
        backend="matplotlib",
        install_hint="pip install 'DEAPack[viz]'",
    ),
    PlotInfo(
        kind="metafrontier",
        title="Group and metafrontier performance",
        description=(
            "Certified within-group and pooled-opportunity efficiencies joined "
            "for each organization, with their metatechnology ratio"
        ),
        default_metric=None,
        views=("auto",),
        backend="matplotlib",
        install_hint="pip install 'DEAPack[viz]'",
    ),
    PlotInfo(
        kind="references",
        title="Selected-plan peer use",
        description=(
            "Certified reported peer-edge frequency above the fitted threshold "
            "in one solver-selected plan, with self-reference and use by other "
            "organizations kept separate"
        ),
        default_metric=None,
        views=("auto",),
        backend="matplotlib",
        install_hint="pip install 'DEAPack[viz]'",
    ),
)
_PLOT_KINDS = tuple(plot.kind for plot in _PLOTS)


def available_plots(result: Any | None = None) -> tuple[PlotInfo, ...]:
    """Return immutable plot descriptions applicable to a result.

    Passing no result preserves registry-level discovery. Result-bound
    discovery advertises ``performance`` only when at least one declared
    measure has a valid finite optimal value, advertises ``frontier`` only
    when the scalar radial target contract is present, and advertises
    ``trajectory`` only when a certified classic Dynamic-SBM carry-over
    account can be reconstructed, and advertises ``process`` only for a
    certified classic input-oriented Network-SBM process account. The
    ``improvement`` requires one reconstructable certified account from
    classic input- or output-oriented radial DEA with its two-stage target
    completion, the three classic static SBM orientations, the certified
    separable strongly disposable environmental SBM, ordinary static DDF, or
    the core CRS common-factor environmental DDF family (including its exact
    CFG source preset).
    ``metafrontier`` requires the
    certified core radial group/meta identity. ``references`` requires the
    complete certified selected-plan peer account for a supported static
    convex global cross-section; it counts reported peer edges above the
    fitted source threshold without invoking a solver and does not claim
    alternate-optimum or global-reference-set coverage. This function never
    imports Matplotlib.
    """
    if result is None:
        return _PLOTS
    available: list[PlotInfo] = []
    measures = plottable_measure_specs(result)
    if measures:
        default = default_measure_spec(result, candidates=measures)
        available.append(
            replace(
                _PLOTS[0],
                default_metric=default.column,
                measures=measures,
            )
        )
    if frontier_plot_applicable(result):
        available.append(_PLOTS[1])
    if trajectory_plot_applicable(result):
        available.append(_PLOTS[2])
    if process_attribution_plot_applicable(result):
        available.append(_PLOTS[3])
    if (
        radial_improvement_plot_applicable(result)
        or sbm_improvement_plot_applicable(result)
        or environmental_ddf_improvement_plot_applicable(result)
        or directional_ddf_improvement_plot_applicable(result)
    ):
        available.append(_PLOTS[4])
    if metafrontier_plot_applicable(result):
        available.append(_PLOTS[5])
    if reference_frequency_plot_applicable(result):
        available.append(_PLOTS[6])
    return tuple(available)


def _unknown_kind(kind: object) -> PlotNotAvailableError:
    normalized = str(kind).strip().casefold()
    matches = get_close_matches(normalized, _PLOT_KINDS, n=1, cutoff=0.5)
    suggestion = f"; did you mean {matches[0]!r}?" if matches else ""
    return PlotNotAvailableError(
        f"unknown visualization kind {kind!r}{suggestion}; "
        f"available kinds: {', '.join(_PLOT_KINDS)}"
    )


def plot_result(
    result: Any,
    *,
    kind: str,
    metric: str | None = None,
    period: object | None = None,
    dmu_id: object | None = None,
    variable: str | None = None,
    theme: str = "deapack",
    view: str = "auto",
) -> Any:
    """Dispatch one supported result plot and return its Figure."""
    if not isinstance(kind, str):
        raise _unknown_kind(kind)
    normalized_kind = kind.strip().casefold()
    if normalized_kind not in _PLOT_KINDS:
        raise _unknown_kind(kind)
    if theme != "deapack":
        raise PlotNotAvailableError(
            f"unknown theme {theme!r}; the available theme is 'deapack'"
        )

    if normalized_kind == "performance":
        if dmu_id is not None or variable is not None:
            raise PlotNotAvailableError(
                "performance plotting does not accept dmu_id or variable; "
                "use its period and metric controls"
            )
        prepared = prepare_performance_data(
            result,
            metric=metric,
            period=period,
            view=view,
        )
        from ._matplotlib import render_performance

        return render_performance(prepared, theme=theme)

    if normalized_kind == "trajectory":
        if metric is not None or period is not None:
            raise PlotNotAvailableError(
                "trajectory plotting uses one complete fitted horizon; metric "
                "and period must remain omitted"
            )
        if view != "auto":
            raise PlotNotAvailableError(
                "trajectory plotting currently supports only view='auto'"
            )
        if dmu_id is None:
            raise PlotNotAvailableError(
                "trajectory plotting requires dmu_id for one fitted organization"
            )
        prepared = prepare_trajectory_data(
            result,
            dmu_id=dmu_id,
            variable=variable,
        )
        from ._matplotlib import render_trajectory

        return render_trajectory(prepared, theme=theme)

    if normalized_kind == "process":
        if metric is not None or variable is not None:
            raise PlotNotAvailableError(
                "process plotting uses the fitted system, process, and link "
                "accounts; metric and variable must remain omitted"
            )
        if view != "auto":
            raise PlotNotAvailableError(
                "process plotting currently supports only view='auto'"
            )
        if dmu_id is None:
            raise PlotNotAvailableError(
                "process plotting requires dmu_id for one fitted organization"
            )
        prepared = prepare_process_attribution_data(
            result,
            dmu_id=dmu_id,
            period=period,
        )
        from ._matplotlib import render_process_attribution

        return render_process_attribution(prepared, theme=theme)

    if normalized_kind == "improvement":
        if metric is not None or variable is not None:
            raise PlotNotAvailableError(
                "improvement plotting uses a fitted radial, variable-level SBM, "
                "or directional operating-plan account; metric and variable "
                "must remain omitted"
            )
        if view != "auto":
            raise PlotNotAvailableError(
                "improvement plotting currently supports only view='auto'"
            )
        if dmu_id is None:
            raise PlotNotAvailableError(
                "improvement plotting requires dmu_id for one fitted organization"
            )
        if radial_improvement_route(result):
            prepared_radial = prepare_radial_improvement_data(
                result,
                dmu_id=dmu_id,
                period=period,
            )
            from ._matplotlib import render_radial_improvement

            return render_radial_improvement(prepared_radial, theme=theme)
        if environmental_ddf_improvement_route(result):
            prepared_ddf = prepare_environmental_ddf_improvement_data(
                result,
                dmu_id=dmu_id,
                period=period,
            )
            from ._matplotlib import render_environmental_ddf_improvement

            return render_environmental_ddf_improvement(prepared_ddf, theme=theme)
        if directional_ddf_improvement_route(result):
            prepared_directional = prepare_directional_ddf_improvement_data(
                result,
                dmu_id=dmu_id,
                period=period,
            )
            from ._matplotlib import render_directional_ddf_improvement

            return render_directional_ddf_improvement(
                prepared_directional,
                theme=theme,
            )
        prepared_sbm = prepare_sbm_improvement_data(
            result,
            dmu_id=dmu_id,
            period=period,
        )
        from ._matplotlib import render_sbm_improvement

        return render_sbm_improvement(prepared_sbm, theme=theme)

    if normalized_kind == "metafrontier":
        if metric is not None or dmu_id is not None or variable is not None:
            raise PlotNotAvailableError(
                "metafrontier plotting uses the certified group/meta account; "
                "metric, dmu_id, and variable must remain omitted"
            )
        if view != "auto":
            raise PlotNotAvailableError(
                "metafrontier plotting currently supports only view='auto'"
            )
        prepared = prepare_metafrontier_data(result, period=period)
        from ._matplotlib import render_metafrontier

        return render_metafrontier(prepared, theme=theme)

    if normalized_kind == "references":
        if (
            metric is not None
            or period is not None
            or dmu_id is not None
            or variable is not None
        ):
            raise PlotNotAvailableError(
                "references plotting uses the complete certified fitted "
                "cross-section; metric, period, dmu_id, and variable must "
                "remain omitted"
            )
        if view != "auto":
            raise PlotNotAvailableError(
                "references plotting currently supports only view='auto'"
            )
        prepared_references = prepare_reference_frequency_data(result)
        from ._matplotlib import render_reference_frequency

        return render_reference_frequency(prepared_references, theme=theme)

    if metric is not None or dmu_id is not None or variable is not None:
        raise PlotNotAvailableError(
            "frontier plotting uses observed and target quantities; metric must "
            "remain omitted, and dmu_id and variable are unsupported"
        )
    if view != "auto":
        raise PlotNotAvailableError(
            "frontier plotting currently supports only view='auto'"
        )
    frontier = prepare_frontier_data(result, period=period)
    from ._matplotlib import render_frontier

    return render_frontier(frontier, theme=theme)


__all__ = [
    "DirectionalDDFImprovementPlotData",
    "EnvironmentalDDFImprovementPlotData",
    "FrontierPlotData",
    "MeasureSpec",
    "MetafrontierPlotData",
    "PlotInfo",
    "PlotNotAvailableError",
    "ProcessAttributionPlotData",
    "RadialImprovementPlotData",
    "ReferenceFrequencyPlotData",
    "SBMImprovementPlotData",
    "TrajectoryPlotData",
    "available_plots",
    "directional_ddf_improvement_plot_applicable",
    "environmental_ddf_improvement_plot_applicable",
    "measure_certification_mask",
    "measure_validity_mask",
    "metafrontier_plot_applicable",
    "plot_result",
    "prepare_directional_ddf_improvement_data",
    "prepare_environmental_ddf_improvement_data",
    "prepare_frontier_data",
    "prepare_metafrontier_data",
    "prepare_performance_data",
    "prepare_process_attribution_data",
    "prepare_radial_improvement_data",
    "prepare_reference_frequency_data",
    "prepare_sbm_improvement_data",
    "prepare_trajectory_data",
    "process_attribution_plot_applicable",
    "radial_improvement_plot_applicable",
    "radial_improvement_route",
    "reference_frequency_plot_applicable",
    "sbm_improvement_plot_applicable",
    "trajectory_plot_applicable",
]
