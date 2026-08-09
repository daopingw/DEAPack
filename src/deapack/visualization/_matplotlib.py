"""Matplotlib rendering for prepared DEAPack visualization data."""

from __future__ import annotations

import math
import textwrap
from typing import Any

import pandas as pd

from ._types import PlotNotAvailableError
from .directional_improvement import DirectionalDDFImprovementPlotData
from .environmental_improvement import EnvironmentalDDFImprovementPlotData
from .frontier import FrontierPlotData
from .metafrontier import MetafrontierPlotData
from .network_process import ProcessAttributionPlotData
from .performance import PerformanceFacet, PerformancePlotData
from .radial_improvement import RadialImprovementPlotData
from .reference_frequency import ReferenceFrequencyPlotData
from .sbm_improvement import SBMImprovementPlotData
from .trajectory import TrajectoryPlotData

_INSTALL_HINT = "pip install 'DEAPack[viz]'"

INK = "#24323d"
GRID = "#dce5e7"
TEAL = "#176b73"
ORANGE = "#d97732"
BLUE = "#356fa3"
GRAY = "#687780"

_CATEGORY_STYLE = {
    "reported": (BLUE, "o", "Valid reported result"),
    "efficient": (TEAL, "o", "Efficient"),
    "inefficient": (ORANGE, "v", "Inefficient"),
    "not_reported": (BLUE, "D", "Efficiency status not reported"),
    "nonoptimal": (GRAY, "x", "Excluded diagnostic row"),
}

_THEME = {
    "axes.edgecolor": INK,
    "axes.labelcolor": INK,
    "axes.titlecolor": INK,
    "axes.facecolor": "white",
    "figure.facecolor": "white",
    "font.size": 10.0,
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "text.color": INK,
    "xtick.color": INK,
    "ytick.color": INK,
}


def _load_matplotlib() -> tuple[Any, Any, Any]:
    try:
        import matplotlib as mpl
        import matplotlib.pyplot as plt
        from matplotlib.lines import Line2D
    except ImportError as error:
        raise ImportError(
            "plotting requires Matplotlib; install the visualization extra with "
            f"{_INSTALL_HINT}"
        ) from error
    return mpl, plt, Line2D


def _ordered_frame(
    facet: PerformanceFacet,
    data: PerformancePlotData,
) -> Any:
    if data.measure.preferred_direction == "signed":
        return facet.frame.sort_values(
            "_deapack_input_order",
            kind="stable",
        ).reset_index(drop=True)
    return facet.frame.sort_values(
        [data.metric, "_deapack_input_order"],
        ascending=[
            data.measure.preferred_direction == "higher",
            True,
        ],
        kind="stable",
    ).reset_index(drop=True)


def _category_masks(frame: Any) -> dict[str, Any]:
    return {
        category: frame["_deapack_measure_class"].eq(category)
        for category in (
            "reported",
            "efficient",
            "inefficient",
            "not_reported",
        )
    }


def _render_points(
    ax: Any,
    facet: PerformanceFacet,
    data: PerformancePlotData,
) -> set[str]:
    metric = data.metric
    frame = _ordered_frame(facet, data)
    positions = list(range(len(frame)))
    present: set[str] = set()
    for category, mask in _category_masks(frame).items():
        if not mask.any():
            continue
        color, marker, _ = _CATEGORY_STYLE[category]
        rows = frame.loc[mask]
        row_positions = [positions[index] for index in rows.index]
        edge_style = {} if marker == "x" else {"edgecolors": "white"}
        ax.scatter(
            rows[metric],
            row_positions,
            color=color,
            marker=marker,
            s=38,
            linewidths=1.4 if marker == "x" else 0.7,
            zorder=3,
            **edge_style,
        )
        present.add(category)

    tick_positions = positions.copy()
    tick_labels = frame["dmu_id"].astype(str).tolist()
    if not facet.diagnostic_frame.empty:
        diagnostics = facet.diagnostic_frame.sort_values(
            "_deapack_input_order",
            kind="stable",
        )
        diagnostic_positions = [-2 - position for position in range(len(diagnostics))]
        ax.scatter(
            diagnostics[metric],
            diagnostic_positions,
            color=GRAY,
            marker="x",
            s=38,
            linewidths=1.4,
            zorder=3,
        )
        tick_positions.extend(diagnostic_positions)
        reasons = diagnostics["_deapack_diagnostic_reason"].astype(str)
        tick_labels.extend(
            f"{dmu} ({reason.removesuffix(' — excluded').casefold()})"
            for dmu, reason in zip(
                diagnostics["dmu_id"].astype(str),
                reasons,
                strict=True,
            )
        )
        ax.axhline(-0.75, color=GRID, linewidth=1.0, zorder=1)
        ax.text(
            0.0,
            -0.95,
            "Diagnostic layer — excluded from ranking",
            transform=ax.get_yaxis_transform(),
            ha="left",
            va="top",
            fontsize=8.5,
            color=GRAY,
        )
        present.add("nonoptimal")

    ax.set_yticks(tick_positions)
    ax.set_yticklabels(tick_labels)
    ax.set_ylabel("DMU")
    ax.grid(axis="x")
    return present


def _render_ecdf(
    ax: Any,
    facet: PerformanceFacet,
    data: PerformancePlotData,
) -> set[str]:
    metric = data.metric
    frame = facet.frame.sort_values(
        [metric, "_deapack_input_order"],
        kind="stable",
    ).reset_index(drop=True)
    cumulative = [(position + 1) / len(frame) for position in range(len(frame))]
    ax.step(
        frame[metric],
        cumulative,
        where="post",
        color=INK,
        linewidth=1.6,
        zorder=2,
    )
    present: set[str] = set()
    for category, mask in _category_masks(frame).items():
        if not mask.any():
            continue
        color, marker, _ = _CATEGORY_STYLE[category]
        rows = frame.loc[mask]
        row_cumulative = [cumulative[index] for index in rows.index]
        edge_style = {} if marker == "x" else {"edgecolors": "white"}
        ax.scatter(
            rows[metric],
            row_cumulative,
            color=color,
            marker=marker,
            s=24,
            linewidths=1.2 if marker == "x" else 0.5,
            alpha=0.82,
            zorder=3,
            **edge_style,
        )
        present.add(category)
    if not facet.diagnostic_frame.empty:
        ax.scatter(
            facet.diagnostic_frame[metric],
            [-0.06] * len(facet.diagnostic_frame),
            color=GRAY,
            marker="x",
            s=24,
            linewidths=1.2,
            zorder=3,
        )
        ax.text(
            0.0,
            -0.075,
            "Diagnostic rows: excluded from ECDF",
            transform=ax.get_yaxis_transform(),
            ha="left",
            va="top",
            fontsize=8.5,
            color=GRAY,
        )
        present.add("nonoptimal")
        ax.set_ylim(-0.12, 1.04)
    else:
        ax.set_ylim(0.0, 1.04)
    ax.set_ylabel("Cumulative share of DMUs")
    ax.grid(axis="both")
    return present


def _provenance_note(data: PerformancePlotData) -> str:
    parts = [data.measure.direction_label]
    if data.measure.benchmark_value is not None:
        benchmark_label = data.measure.benchmark_label or "Benchmark"
        parts.append(f"{benchmark_label}: {data.measure.benchmark_value:g}")
    parts.extend(f"{label}: {value}" for label, value in data.provenance)
    if data.nonoptimal_count:
        parts.append(
            f"{data.nonoptimal_count} non-optimal solver result(s) shown "
            "separately and excluded"
        )
    if data.invalid_metric_count:
        parts.append(
            f"{data.invalid_metric_count} undefined measure value(s) shown "
            "separately and excluded"
        )
    unavailable_note = ""
    if data.omitted_metric_count:
        roster = []
        include_facet = len(data.facets) > 1
        for observation in data.unavailable_observations:
            prefix = (
                f"{_compact_footer_value(observation.facet_label, limit=22)}: "
                if include_facet
                else ""
            )
            evidence = [
                observation.reason,
            ]
            if observation.reason == "solver/certification unavailable":
                evidence.append(
                    f"{_status_evidence_label(observation.certification_status_column)}="
                    f"{_compact_footer_value(observation.certification_status)}"
                )
            elif (
                observation.reason == "measure undefined"
                and observation.validity_status_column is not None
                and observation.validity_status is not None
            ):
                evidence.append(
                    f"{_status_evidence_label(observation.validity_status_column)}="
                    f"{_compact_footer_value(observation.validity_status)}"
                )
            roster.append(
                f"{prefix}{_compact_footer_value(observation.dmu_id, limit=24)} "
                f"({'; '.join(evidence)})"
            )
        overflow = data.unavailable_observation_overflow
        roster_text = "; ".join(roster)
        if overflow:
            roster_text = (
                f"{roster_text}; +{overflow} more"
                if roster_text
                else f"+{overflow} more"
            )
        if data.omitted_metric_count == 1:
            unavailable_note = (
                "1 organization omitted because its headline result is unavailable"
            )
        else:
            unavailable_note = (
                f"{data.omitted_metric_count} organizations omitted because their "
                "headline results are unavailable"
            )
        if roster_text:
            unavailable_note = f"{unavailable_note}: {roster_text}"
    main_note = "  ·  ".join(parts)
    if unavailable_note:
        return f"{main_note}\n{unavailable_note}" if main_note else unavailable_note
    return main_note


def _status_evidence_label(column: str) -> str:
    """Turn a declared evidence-column name into a compact footer label."""
    if column == "solver_status":
        return "solver"
    if column == "score_status":
        return "score"
    if column == "score_valid":
        return "score valid"
    return "cert"


def _compact_footer_value(value: str, *, limit: int = 18) -> str:
    """Apply an additional presentation cap to already sanitized payload text."""
    if len(value) <= limit:
        return value
    return f"{value[: limit - 1]}\u2026"


def _wrap_performance_note(note: str, *, figure_width: float) -> tuple[str, int]:
    """Wrap the footer predictably so its reserved layout matches its content."""
    width = max(68, int(figure_width * 14))
    paragraphs = note.splitlines() or [""]
    lines = [paragraphs[0]]
    line_count = max(1, math.ceil(len(paragraphs[0]) / width))
    for paragraph in paragraphs[1:]:
        wrapped = textwrap.wrap(
            paragraph,
            width=width,
            break_long_words=False,
            break_on_hyphens=False,
        ) or [""]
        lines.extend(wrapped)
        line_count += len(wrapped)
    return "\n".join(lines), line_count


def render_performance(
    data: PerformancePlotData,
    *,
    theme: str = "deapack",
) -> Any:
    """Render prepared performance data and return a Matplotlib Figure."""
    if theme != "deapack":
        raise PlotNotAvailableError(
            f"unknown theme {theme!r}; the available theme is 'deapack'"
        )
    mpl, plt, line_2d = _load_matplotlib()

    facet_count = len(data.facets)
    if facet_count == 1:
        nrows, ncols = 1, 1
    elif facet_count in {2, 3}:
        nrows, ncols = 1, facet_count
    else:
        nrows, ncols = 2, 2
    max_point_rows = max(
        (
            len(facet.frame) + len(facet.diagnostic_frame)
            for facet in data.facets
            if facet.view == "points"
        ),
        default=0,
    )
    height = max(4.2, min(12.0, 2.8 + max_point_rows * 0.22))
    width = 7.2 if ncols == 1 else min(15.0, 6.0 * ncols)

    with mpl.rc_context(rc=_THEME):
        figure, axes = plt.subplots(
            nrows,
            ncols,
            squeeze=False,
            figsize=(width, height if nrows == 1 else max(7.5, height)),
            sharex=False,
        )
        flat_axes = list(axes.flat)
        present_categories: set[str] = set()
        for axis, facet in zip(flat_axes[:facet_count], data.facets, strict=True):
            if facet.view == "points":
                present_categories.update(_render_points(axis, facet, data))
            else:
                present_categories.update(_render_ecdf(axis, facet, data))
            axis.set_xlabel(data.measure.label)
            if data.measure.benchmark_value is not None:
                axis.axvline(
                    data.measure.benchmark_value,
                    color=GRAY,
                    linestyle=":",
                    linewidth=1.0,
                    zorder=1,
                    label=data.measure.benchmark_label,
                )
            if facet_count > 1 or facet.label != "Cross-section":
                axis.set_title(facet.label)
            axis.spines["top"].set_visible(False)
            axis.spines["right"].set_visible(False)

        for unused_axis in flat_axes[facet_count:]:
            figure.delaxes(unused_axis)

        title = f"{data.measure.label} across organizations"
        figure.suptitle(title, fontsize=14, fontweight="bold")
        handles = []
        for category in (
            "reported",
            "efficient",
            "inefficient",
            "not_reported",
            "nonoptimal",
        ):
            if category not in present_categories:
                continue
            color, marker, label = _CATEGORY_STYLE[category]
            handles.append(
                line_2d(
                    [],
                    [],
                    color=color,
                    marker=marker,
                    linestyle="None",
                    markeredgewidth=1.4 if marker == "x" else 0.7,
                    markeredgecolor="white" if marker != "x" else color,
                    label=label,
                )
            )
        if handles:
            figure.legend(
                handles=handles,
                loc="upper center",
                bbox_to_anchor=(0.5, 0.955),
                ncol=min(4, len(handles)),
                frameon=False,
            )

        note = _provenance_note(data)
        rendered_note, note_lines = _wrap_performance_note(
            note,
            figure_width=width,
        )
        bottom = min(0.38, max(0.10, 0.055 + 0.027 * note_lines)) if note else 0.06
        if note:
            figure.text(
                0.01,
                0.015,
                rendered_note,
                ha="left",
                va="bottom",
                fontsize=8.5,
                color=GRAY,
                wrap=True,
            )
        figure.tight_layout(rect=(0.0, bottom, 1.0, 0.90))
    return figure


def _frontier_note(data: FrontierPlotData) -> str:
    if data.orientation == "input":
        question = (
            "Arrows show the reported resource-saving target while protecting "
            "the output commitment"
        )
    else:
        question = (
            "Arrows show the reported output-expansion target within the input "
            "commitment"
        )
    parts = [
        question,
        "targets include the model's compatible slack-completion phase",
        "benchmark opportunities are not causal or prescriptive claims",
    ]
    parts.extend(f"{label}: {value}" for label, value in data.provenance)
    if data.omitted_observation_count:
        parts.append(
            f"{data.omitted_observation_count} uncertified or incomplete "
            "observation(s) omitted"
        )
    return "  ·  ".join(parts)


def _frontier_title(data: FrontierPlotData) -> str:
    if data.orientation == "input":
        return "Resource-saving opportunities on the production frontier"
    return "Service-expansion opportunities on the production frontier"


def render_frontier(
    data: FrontierPlotData,
    *,
    theme: str = "deapack",
) -> Any:
    """Render one prepared scalar production frontier and return its Figure."""
    if theme != "deapack":
        raise PlotNotAvailableError(
            f"unknown theme {theme!r}; the available theme is 'deapack'"
        )
    mpl, plt, line_2d = _load_matplotlib()
    observations = data.observations
    frontier = data.frontier

    with mpl.rc_context(rc=_THEME):
        figure, axis = plt.subplots(figsize=(8.4, 6.0))
        if len(frontier) > 1:
            axis.plot(
                frontier["input"],
                frontier["output"],
                color=INK,
                linewidth=2.2,
                zorder=2,
            )
        else:
            axis.scatter(
                frontier["input"],
                frontier["output"],
                color=INK,
                marker="s",
                s=38,
                zorder=2,
            )

        efficient = observations["is_efficient"]
        inefficient = ~efficient
        if efficient.any():
            axis.scatter(
                observations.loc[efficient, "input_observed"],
                observations.loc[efficient, "output_observed"],
                color=TEAL,
                edgecolors="white",
                marker="o",
                s=58,
                linewidths=0.8,
                zorder=5,
            )
        if inefficient.any():
            axis.scatter(
                observations.loc[inefficient, "input_observed"],
                observations.loc[inefficient, "output_observed"],
                color=ORANGE,
                edgecolors="white",
                marker="v",
                s=62,
                linewidths=0.8,
                zorder=5,
            )

        changed = observations["target_changed"]
        changed_rows = observations.loc[changed]
        for row in changed_rows.itertuples(index=False):
            axis.annotate(
                "",
                xy=(row.input_target, row.output_target),
                xytext=(row.input_observed, row.output_observed),
                arrowprops={
                    "arrowstyle": "-|>",
                    "color": ORANGE,
                    "linewidth": 1.25,
                    "alpha": 0.78,
                    "shrinkA": 5,
                    "shrinkB": 4,
                },
                zorder=3,
            )
        if not changed_rows.empty:
            axis.scatter(
                changed_rows["input_target"],
                changed_rows["output_target"],
                color=INK,
                marker="x",
                s=42,
                linewidths=1.4,
                zorder=6,
            )

        label_rows = observations
        if len(observations) > 24:
            label_rows = (
                changed_rows if len(changed_rows) <= 24 else observations.iloc[0:0]
            )
        for row in label_rows.itertuples(index=False):
            axis.annotate(
                str(row.dmu_id),
                xy=(row.input_observed, row.output_observed),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=8.5,
                color=INK,
                zorder=7,
            )

        x_values = pd.concat(
            [
                observations["input_observed"],
                observations["input_target"],
                frontier["input"],
            ],
            ignore_index=True,
        )
        y_values = pd.concat(
            [
                observations["output_observed"],
                observations["output_target"],
                frontier["output"],
            ],
            ignore_index=True,
        )
        x_max = max(1.0, float(x_values.max()))
        y_max = max(1.0, float(y_values.max()))
        axis.set_xlim(0.0, x_max * 1.08)
        axis.set_ylim(0.0, y_max * 1.10)
        axis.set_xlabel(data.input_name)
        axis.set_ylabel(data.output_name)
        axis.grid(axis="both")
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)

        title = _frontier_title(data)
        if data.period_label != "Cross-section":
            title = f"{title}\n{data.period_label}"
        axis.set_title(title, fontsize=14, fontweight="bold", pad=14)

        rts = data.returns_to_scale.upper()
        handles = [
            line_2d(
                [],
                [],
                color=INK,
                linewidth=2.2,
                label=f"{rts} reference frontier",
            ),
            line_2d(
                [],
                [],
                color=TEAL,
                marker="o",
                linestyle="None",
                markeredgecolor="white",
                label="Certified efficient operation",
            ),
        ]
        if inefficient.any():
            handles.append(
                line_2d(
                    [],
                    [],
                    color=ORANGE,
                    marker="v",
                    linestyle="None",
                    markeredgecolor="white",
                    label="Operation with a benchmark opportunity",
                )
            )
        if changed.any():
            handles.append(
                line_2d(
                    [],
                    [],
                    color=INK,
                    marker="x",
                    linestyle="None",
                    markeredgewidth=1.4,
                    label="Reported DEA target",
                )
            )
        axis.legend(
            handles=handles,
            loc="best",
            frameon=False,
            fontsize=8.8,
        )

        note = _frontier_note(data)
        figure.text(
            0.01,
            0.015,
            note,
            ha="left",
            va="bottom",
            fontsize=8.2,
            color=GRAY,
            wrap=True,
        )
        figure.tight_layout(rect=(0.0, 0.12, 1.0, 1.0))
    return figure


def _trajectory_note(data: TrajectoryPlotData) -> str:
    if data.carryover_score_policy == "fixed_commitment_not_in_reported_score":
        score_note = (
            "this fixed carry-over has no discretionary slack and enters the "
            "plan as a feasibility account, not a scored burden"
        )
    elif data.carryover_score_policy == "feasibility_only_not_in_reported_score":
        score_note = (
            "this carry-over coordinates feasibility but does not enter the "
            "reported score"
        )
    elif data.carryover_score_policy == "included_in_reported_score":
        score_note = "this carry-over enters the reported score in every period"
    else:
        score_note = "reported-score inclusion varies by period and signed adjustment"
    parts = [
        (
            "Outgoing and inherited targets belong to one certified horizon "
            "plan, not independent annual recommendations"
        ),
        (
            "the bars report the complete period operating-plan account, "
            "not an attribution to the selected carry-over"
        ),
        "the terminal period has no fabricated successor",
        score_note,
        "the selected optimum need not be unique",
        "benchmark opportunities are not causal or prescriptive claims",
        f"maximum continuity residual: {data.max_continuity_residual:.2e}",
        f"selection: {data.selection_status}",
    ]
    parts.extend(f"{label}: {value}" for label, value in data.provenance)
    return "  ·  ".join(parts)


def render_trajectory(
    data: TrajectoryPlotData,
    *,
    theme: str = "deapack",
) -> Any:
    """Render a certified Dynamic-SBM carry-over path and period account."""
    if theme != "deapack":
        raise PlotNotAvailableError(
            f"unknown theme {theme!r}; the available theme is 'deapack'"
        )
    mpl, plt, line_2d = _load_matplotlib()
    quantity = data.quantity
    period_accounts = data.period_accounts
    positions = list(range(data.period_count))
    period_labels = quantity["period"].astype(str).tolist()

    with mpl.rc_context(rc=_THEME):
        figure, (quantity_axis, account_axis) = plt.subplots(
            2,
            1,
            figsize=(9.0, 7.6),
            gridspec_kw={"height_ratios": (1.35, 1.0)},
        )

        quantity_axis.plot(
            positions,
            quantity["observed"],
            color=BLUE,
            marker="o",
            linewidth=1.8,
            markersize=5.5,
            zorder=4,
            label="Observed carry-over",
        )
        quantity_axis.plot(
            positions,
            quantity["outgoing_target"],
            color=ORANGE,
            marker="D",
            linewidth=1.8,
            markersize=5.0,
            zorder=5,
            label="Selected outgoing target",
        )
        inherited = quantity["inherited_target"].notna()
        if inherited.any():
            quantity_axis.scatter(
                [positions[index] for index in quantity.index[inherited]],
                quantity.loc[inherited, "inherited_target"],
                facecolors="white",
                edgecolors=TEAL,
                marker="s",
                s=58,
                linewidths=1.5,
                zorder=7,
                label="Inherited from preceding period",
            )
        for position, transition in enumerate(data.transitions.itertuples(index=False)):
            quantity_axis.annotate(
                "",
                xy=(position + 1, transition.inherited_target),
                xytext=(position, transition.source_target),
                arrowprops={
                    "arrowstyle": "-|>",
                    "color": TEAL,
                    "linestyle": "--",
                    "linewidth": 1.2,
                    "shrinkA": 6,
                    "shrinkB": 6,
                },
                zorder=3,
            )

        quantity_axis.set_xticks(positions)
        quantity_axis.set_xticklabels(period_labels)
        quantity_axis.set_xlabel("Period in the fitted horizon")
        quantity_axis.set_ylabel(f"{data.variable_label} (original units)")
        quantity_axis.set_title(
            "Observed plan, selected outgoing target, and inherited target",
            fontsize=11.5,
            fontweight="bold",
        )
        quantity_axis.grid(axis="both")
        quantity_axis.spines["top"].set_visible(False)
        quantity_axis.spines["right"].set_visible(False)
        quantity_axis.legend(loc="best", frameon=False, fontsize=8.8)

        efficiencies = period_accounts["efficiency"].to_numpy(dtype=float)
        colors = [
            TEAL if abs(value - 1.0) <= 1e-7 else ORANGE for value in efficiencies
        ]
        account_axis.bar(
            positions,
            efficiencies,
            color=colors,
            edgecolor="white",
            linewidth=0.7,
            width=0.64,
            zorder=3,
        )
        account_axis.axhline(
            1.0,
            color=GRAY,
            linestyle=":",
            linewidth=1.1,
            zorder=2,
        )
        account_axis.axhline(
            data.horizon_efficiency,
            color=INK,
            linestyle="--",
            linewidth=1.1,
            zorder=2,
        )
        account_axis.set_xticks(positions)
        account_axis.set_xticklabels(period_labels)
        account_axis.set_xlabel("Period in the fitted horizon")
        account_axis.set_ylabel("Period operating-plan performance")
        account_axis.set_ylim(
            0.0,
            max(1.08, float(efficiencies.max(initial=0.0)) * 1.12),
        )
        account_axis.set_title(
            "Complete period operating-plan account (all scored dimensions)",
            fontsize=11.5,
            fontweight="bold",
        )
        account_axis.grid(axis="y")
        account_axis.spines["top"].set_visible(False)
        account_axis.spines["right"].set_visible(False)
        account_axis.legend(
            handles=[
                line_2d(
                    [],
                    [],
                    color=GRAY,
                    linestyle=":",
                    label="No scored period burden: 1",
                ),
                line_2d(
                    [],
                    [],
                    color=INK,
                    linestyle="--",
                    label=(
                        "Horizon performance "
                        f"{data.horizon_efficiency:.3f} (not a period average)"
                    ),
                ),
            ],
            loc="best",
            frameon=False,
            fontsize=8.7,
        )

        figure.suptitle(
            f"Certified carry-over trajectory for {data.dmu_id}",
            fontsize=14,
            fontweight="bold",
        )
        figure.text(
            0.01,
            0.012,
            _trajectory_note(data),
            ha="left",
            va="bottom",
            fontsize=8.1,
            color=GRAY,
            wrap=True,
        )
        figure.tight_layout(rect=(0.0, 0.135, 1.0, 0.95))
    return figure


def _process_note(data: ProcessAttributionPlotData) -> str:
    policies = set(data.links["link_kind"].astype(str))
    if policies == {"fixed"}:
        governance = "fixed handoff targets preserve the observed commitments"
    elif policies == {"free"}:
        governance = (
            "free handoff targets are selected coordinated values, not unique "
            "management recommendations"
        )
    else:
        governance = "each handoff follows its declared fixed or free governance policy"
    parts = [
        (
            "Process values locate input burden within one solver-selected, "
            "jointly feasible Network-SBM plan"
        ),
        "they are not independent departmental scores or causal contributions",
        "system performance equals the declared-weight process account",
        governance,
        "the selected optimum is not uniqueness-certified or prescriptive",
        f"maximum handoff-continuity residual: {data.max_link_continuity_residual:.2e}",
    ]
    parts.extend(f"{label}: {value}" for label, value in data.provenance[1:])
    return "  ·  ".join(parts)


def _compact_number(value: float) -> str:
    magnitude = abs(value)
    if magnitude != 0.0 and (magnitude >= 10_000 or magnitude < 0.001):
        return f"{value:.3e}"
    return f"{value:,.4f}".rstrip("0").rstrip(".")


def _render_handoff_ledger(axis: Any, data: ProcessAttributionPlotData) -> None:
    links = data.links.reset_index(drop=True)
    row_count = len(links)
    axis.set_xlim(0.0, 1.0)
    axis.set_ylim(-0.75, row_count + 0.9)
    axis.axis("off")
    axis.set_title(
        "Selected internal handoffs in their original units",
        loc="left",
        fontsize=11.5,
        fontweight="bold",
        pad=10,
    )
    headers = (
        (0.02, "Connected processes", "left"),
        (0.39, "Governance", "center"),
        (0.58, "Observed", "right"),
        (0.76, "Selected common target", "center"),
        (0.98, "Change", "right"),
    )
    for position, label, alignment in headers:
        axis.text(
            position,
            row_count + 0.48,
            label,
            ha=alignment,
            va="center",
            fontsize=8.5,
            color=GRAY,
            fontweight="bold",
        )
    axis.axhline(row_count + 0.12, color=GRID, linewidth=1.0)

    for index, row in links.iterrows():
        y = row_count - index - 0.5
        if index % 2 == 0:
            axis.axhspan(y - 0.44, y + 0.44, color="#f5f8f8", zorder=0)
        source = str(row["source_process_id"]).replace("_", " ").title()
        recipient = str(row["recipient_process_id"]).replace("_", " ").title()
        link_label = str(row["link_label"])
        variable_label = str(row["variable_label"])
        axis.text(
            0.02,
            y + 0.10,
            f"{source}  →  {recipient}",
            ha="left",
            va="center",
            fontsize=9.2,
            color=INK,
            fontweight="bold",
        )
        axis.text(
            0.02,
            y - 0.18,
            f"{link_label} · {variable_label}",
            ha="left",
            va="center",
            fontsize=8.0,
            color=GRAY,
        )
        kind = str(row["link_kind"])
        policy_color = BLUE if kind == "fixed" else TEAL
        axis.text(
            0.39,
            y,
            kind.upper(),
            ha="center",
            va="center",
            fontsize=8.0,
            color="white",
            fontweight="bold",
            bbox={
                "boxstyle": "round,pad=0.28",
                "facecolor": policy_color,
                "edgecolor": "none",
            },
        )
        observed = float(row["observed"])
        target = float(row["target"])
        change = float(row["change"])
        axis.text(
            0.58,
            y,
            _compact_number(observed),
            ha="right",
            va="center",
            fontsize=9.2,
            color=BLUE,
        )
        axis.annotate(
            "",
            xy=(0.70, y),
            xytext=(0.62, y),
            arrowprops={
                "arrowstyle": "-|>",
                "color": ORANGE,
                "linewidth": 1.25,
                "shrinkA": 0,
                "shrinkB": 0,
            },
        )
        axis.text(
            0.76,
            y,
            _compact_number(target),
            ha="center",
            va="center",
            fontsize=9.2,
            color=ORANGE,
            fontweight="bold",
        )
        percent = change / observed if observed != 0.0 else float("nan")
        percent_text = f"{percent:+.1%}" if pd.notna(percent) else "n/a"
        axis.text(
            0.98,
            y,
            f"{_compact_number(change)}  ({percent_text})",
            ha="right",
            va="center",
            fontsize=8.5,
            color=INK,
        )
    axis.text(
        0.02,
        -0.52,
        (
            "Rows may use different physical units; arrows express the fitted "
            "supplier-recipient account, not a common numerical scale."
        ),
        ha="left",
        va="center",
        fontsize=8.0,
        color=GRAY,
    )


def render_process_attribution(
    data: ProcessAttributionPlotData,
    *,
    theme: str = "deapack",
) -> Any:
    """Render one certified input-oriented Network-SBM process account."""
    if theme != "deapack":
        raise PlotNotAvailableError(
            f"unknown theme {theme!r}; the available theme is 'deapack'"
        )
    mpl, plt, _ = _load_matplotlib()
    processes = data.processes.reset_index(drop=True)
    colors = (TEAL, BLUE, ORANGE, "#7b6aa8", "#5b8c5a", "#b56576")
    process_colors = [colors[index % len(colors)] for index in range(len(processes))]
    height = max(
        7.7,
        5.8 + 0.42 * len(processes) + 0.45 * len(data.links),
    )

    with mpl.rc_context(rc=_THEME):
        figure = plt.figure(figsize=(11.2, height))
        grid = figure.add_gridspec(
            2,
            2,
            height_ratios=(1.15, max(0.9, 0.22 * len(data.links) + 0.55)),
            hspace=0.42,
            wspace=0.28,
        )
        process_axis = figure.add_subplot(grid[0, 0])
        system_axis = figure.add_subplot(grid[0, 1])
        handoff_axis = figure.add_subplot(grid[1, :])

        positions = list(range(len(processes)))
        for position, row, color in zip(
            positions,
            processes.itertuples(index=False),
            process_colors,
            strict=True,
        ):
            scored = bool(row.scored)
            process_axis.barh(
                position,
                row.efficiency,
                color=color if scored else "white",
                edgecolor=color,
                hatch=None if scored else "///",
                linewidth=1.0,
                height=0.62,
                zorder=3,
            )
            suffix = f"w={row.declared_weight:.2f}" if scored else "unscored: w=0"
            if row.efficiency <= 0.72:
                label_position = row.efficiency + 0.02
                label_alignment = "left"
                label_color = INK
            else:
                label_position = row.efficiency - 0.02
                label_alignment = "right"
                label_color = "white" if scored else INK
            process_axis.text(
                label_position,
                position,
                f"{row.efficiency:.3f}  ·  {suffix}",
                ha=label_alignment,
                va="center",
                fontsize=8.5,
                color=label_color,
            )
        process_axis.axvline(
            data.system_efficiency,
            color=INK,
            linestyle="--",
            linewidth=1.2,
            zorder=2,
        )
        process_axis.axvline(
            1.0,
            color=GRAY,
            linestyle=":",
            linewidth=1.0,
            zorder=2,
        )
        process_axis.set_yticks(positions)
        process_axis.set_yticklabels(processes["process_label"].tolist())
        process_axis.invert_yaxis()
        process_axis.set_xlim(0.0, 1.02)
        process_axis.set_xlabel("Input-oriented process performance")
        process_axis.set_title(
            "Where the joint plan locates input burden",
            loc="left",
            fontsize=11.5,
            fontweight="bold",
        )
        process_axis.grid(axis="x")
        process_axis.spines["top"].set_visible(False)
        process_axis.spines["right"].set_visible(False)
        process_axis.text(
            data.system_efficiency,
            0.97,
            f" system {data.system_efficiency:.3f}",
            ha="left",
            va="top",
            fontsize=8.2,
            color=INK,
            transform=process_axis.get_xaxis_transform(),
        )

        left = 0.0
        for row, color in zip(
            processes.itertuples(index=False), process_colors, strict=True
        ):
            system_axis.barh(
                0.55,
                row.weighted_contribution,
                left=left,
                color=color,
                edgecolor="white",
                linewidth=0.7,
                height=0.32,
                zorder=3,
            )
            if row.weighted_contribution >= 0.045:
                system_axis.text(
                    left + row.weighted_contribution / 2.0,
                    0.55,
                    f"{row.weighted_contribution:.3f}",
                    ha="center",
                    va="center",
                    fontsize=7.6,
                    color="white",
                    fontweight="bold",
                )
            left += row.weighted_contribution
        left = data.system_efficiency
        for row, color in zip(
            processes.itertuples(index=False), process_colors, strict=True
        ):
            system_axis.barh(
                0.55,
                row.attributed_gap,
                left=left,
                color=color,
                alpha=0.22,
                edgecolor=color,
                hatch="///",
                linewidth=0.7,
                height=0.32,
                zorder=2,
            )
            left += row.attributed_gap
        system_axis.axvline(
            data.system_efficiency,
            color=INK,
            linestyle="--",
            linewidth=1.2,
            zorder=4,
        )
        system_axis.text(
            data.system_efficiency / 2.0,
            0.83,
            f"Achieved account  {data.system_efficiency:.3f}",
            ha="center",
            va="center",
            fontsize=9.0,
            color=INK,
            fontweight="bold",
        )
        system_axis.text(
            data.system_efficiency + data.system_gap / 2.0,
            0.83,
            f"Attributed gap  {data.system_gap:.3f}",
            ha="center",
            va="center",
            fontsize=9.0,
            color=GRAY,
        )
        formula = " + ".join(
            f"{row.declared_weight:.2f} x {row.efficiency:.3f}"
            for row in processes.itertuples(index=False)
        )
        system_axis.text(
            0.5,
            0.17,
            f"{formula} = {data.system_efficiency:.3f}",
            ha="center",
            va="center",
            fontsize=8.7,
            color=INK,
            wrap=True,
        )
        system_axis.set_xlim(0.0, 1.0)
        system_axis.set_ylim(-0.05, 1.05)
        system_axis.set_yticks([])
        system_axis.set_xlabel("Declared-weight system account")
        system_axis.set_title(
            "How the system score is formed",
            loc="left",
            fontsize=11.5,
            fontweight="bold",
        )
        system_axis.grid(axis="x")
        system_axis.spines["top"].set_visible(False)
        system_axis.spines["right"].set_visible(False)
        system_axis.spines["left"].set_visible(False)

        _render_handoff_ledger(handoff_axis, data)

        period_suffix = "" if data.period is None else f" · period {data.period}"
        title = (
            f"Certified connected-organization account for {data.dmu_id}{period_suffix}"
        )
        figure.suptitle(
            title,
            fontsize=14,
            fontweight="bold",
        )
        figure.text(
            0.01,
            0.012,
            _process_note(data),
            ha="left",
            va="bottom",
            fontsize=8.0,
            color=GRAY,
            wrap=True,
        )
        figure.subplots_adjust(
            left=0.08,
            right=0.98,
            top=0.89,
            bottom=0.17,
            hspace=0.42,
            wspace=0.28,
        )
    return figure


_SBM_ROLE_PRESENTATION = {
    "input": ("Resource", BLUE, "saving"),
    "output": ("Service", TEAL, "service gain"),
    "bad_output": ("Undesirable residual", ORANGE, "residual reduction"),
}


def _sbm_role_presentation(role: object) -> tuple[str, str, str]:
    try:
        return _SBM_ROLE_PRESENTATION[str(role)]
    except KeyError as error:
        raise PlotNotAvailableError(
            f"unsupported SBM improvement variable role {role!r}"
        ) from error


def _sbm_mandate(orientation: str, *, has_bad_output: bool) -> str:
    if has_bad_output:
        return (
            "Fitted resource-service-residual account under separable strong disposal"
        )
    if orientation == "input":
        return "Resource-conservation mandate"
    if orientation == "output":
        return "Service-expansion mandate"
    return "Joint resource-and-service redesign"


def render_sbm_improvement(
    data: SBMImprovementPlotData,
    *,
    theme: str = "deapack",
) -> Any:
    """Render one certified classic or strong-separable environmental SBM plan."""
    if theme != "deapack":
        raise PlotNotAvailableError(
            f"unknown theme {theme!r}; the available theme is 'deapack'"
        )
    mpl, plt, line_2d = _load_matplotlib()
    variables = data.variables.sort_values("order", kind="stable").reset_index(
        drop=True
    )
    has_bad_output = variables["role"].eq("bad_output").any()
    # A handbook figure is normally rendered in a single 600 px text column.
    # Stack the change account and original-unit ledger so neither panel is
    # squeezed to half of an over-wide canvas.
    height = max(9.4, 7.2 + 0.55 * len(variables))

    with mpl.rc_context(rc=_THEME):
        figure = plt.figure(figsize=(8.2, height))
        grid = figure.add_gridspec(2, 1, height_ratios=(1.0, 1.08), hspace=0.58)
        change_axis = figure.add_subplot(grid[0, 0])
        ledger_axis = figure.add_subplot(grid[1, 0])

        values = variables["signed_proportional_change"].astype(float)
        largest = max(float(values.abs().max()), 0.10)
        limit = max(largest * 1.28, 0.18)
        positions = list(range(len(variables)))
        for position, row in enumerate(variables.itertuples(index=False)):
            scored = bool(row.included_in_objective)
            _, base_color, _ = _sbm_role_presentation(row.role)
            change_axis.barh(
                position,
                row.signed_proportional_change,
                color=base_color if scored else "white",
                edgecolor=base_color if scored else GRAY,
                hatch=None if scored else "///",
                linewidth=1.0,
                height=0.60,
                zorder=3,
            )
            if abs(row.signed_proportional_change) <= 1e-14:
                change_axis.scatter(
                    [0.0],
                    [position],
                    marker="D",
                    s=25,
                    color=base_color if scored else GRAY,
                    zorder=4,
                )
            label = f"{row.signed_proportional_change:+.1%}"
            offset = 0.025 * limit
            x = (
                row.signed_proportional_change + offset
                if row.signed_proportional_change >= 0.0
                else row.signed_proportional_change - offset
            )
            change_axis.text(
                x,
                position,
                label,
                ha="left" if row.signed_proportional_change >= 0.0 else "right",
                va="center",
                fontsize=9.5,
                color=INK,
            )

        labels = [
            f"{_sbm_role_presentation(row.role)[0]} · {row.variable_label}"
            for row in variables.itertuples(index=False)
        ]
        change_axis.axvline(0.0, color=INK, linewidth=1.0, zorder=2)
        change_axis.set_xlim(-limit, limit)
        change_axis.set_yticks(positions)
        change_axis.set_yticklabels(labels)
        change_axis.invert_yaxis()
        change_axis.xaxis.set_major_formatter(mpl.ticker.PercentFormatter(1.0))
        change_axis.set_xlabel(
            "Change from current operation\n"
            "(resource/residual reduction ←  |  → service increase)"
            if has_bad_output
            else "Change from current operation\n(saving ←  |  → additional service)"
        )
        change_axis.set_title(
            "Where the selected plan locates operating gaps",
            loc="left",
            fontsize=12.0,
            fontweight="bold",
        )
        change_axis.grid(axis="x")
        change_axis.spines["top"].set_visible(False)
        change_axis.spines["right"].set_visible(False)
        legend_handles = [
            line_2d(
                [],
                [],
                color=INK,
                marker="s",
                markerfacecolor=INK,
                linestyle="None",
                label="Included in the performance account",
            )
        ]
        if (~variables["included_in_objective"]).any():
            legend_handles.append(
                line_2d(
                    [],
                    [],
                    color=GRAY,
                    marker="s",
                    markerfacecolor="white",
                    linestyle="None",
                    label="Feasibility-only side of this orientation",
                )
            )
        change_axis.legend(
            handles=legend_handles,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.24),
            frameon=False,
            fontsize=9.5,
            ncol=len(legend_handles),
        )

        ledger_axis.set_axis_off()
        ledger_axis.set_xlim(0.0, 1.0)
        ledger_axis.set_ylim(-0.08, 1.0)
        ledger_axis.set_title(
            "Current quantities and one feasible benchmark plan",
            loc="left",
            fontsize=12.0,
            fontweight="bold",
        )
        ledger_axis.text(
            0.00,
            0.935,
            "Variable",
            ha="left",
            va="center",
            fontsize=9.5,
            color=GRAY,
            fontweight="bold",
        )
        for x, label in (
            (0.40, "Current"),
            (0.62, "Target"),
            (0.98, "Benchmark gap"),
        ):
            ledger_axis.text(
                x,
                0.935,
                label,
                ha="right",
                va="center",
                fontsize=9.5,
                color=GRAY,
                fontweight="bold",
            )
        ledger_axis.plot([0.0, 1.0], [0.902, 0.902], color=GRID, linewidth=1.0)
        row_step = min(0.135, 0.68 / max(len(variables), 1))
        start_y = 0.82
        for position, row in enumerate(variables.itertuples(index=False)):
            y = start_y - position * row_step
            role, role_color, gap_kind = _sbm_role_presentation(row.role)
            ledger_axis.text(
                0.00,
                y,
                f"{row.variable_label}\n{role}",
                ha="left",
                va="center",
                fontsize=9.5,
                linespacing=1.25,
            )
            ledger_axis.text(
                0.40,
                y,
                _compact_number(row.observed),
                ha="right",
                va="center",
                fontsize=9.7,
            )
            ledger_axis.text(
                0.62,
                y,
                _compact_number(row.target),
                ha="right",
                va="center",
                fontsize=9.7,
                color=role_color,
                fontweight="bold",
            )
            plan = f"{gap_kind} {_compact_number(row.slack)}"
            if not row.included_in_objective:
                plan += "*"
            ledger_axis.text(
                0.98,
                y,
                plan,
                ha="right",
                va="center",
                fontsize=9.5,
                color=INK if row.included_in_objective else GRAY,
            )
            ledger_axis.plot(
                [0.0, 1.0],
                [y - row_step / 2.0, y - row_step / 2.0],
                color=GRID,
                linewidth=0.65,
            )

        account_y = max(0.13, start_y - len(variables) * row_step - 0.035)
        ledger_axis.text(
            0.00,
            account_y,
            f"Input-retention account  {data.input_account:.3f}",
            ha="left",
            va="center",
            fontsize=9.5,
            color=BLUE,
            fontweight="bold",
        )
        ledger_axis.text(
            0.00,
            account_y - 0.07,
            (
                "Service-gain/residual-reduction account"
                if has_bad_output
                else "Output-expansion account"
            )
            + f"  {data.output_expansion_account:.3f}",
            ha="left",
            va="center",
            fontsize=9.5,
            color=INK if has_bad_output else TEAL,
            fontweight="bold",
        )
        if (~variables["included_in_objective"]).any():
            ledger_axis.text(
                0.00,
                0.005,
                "* Feasible in this selected optimum, but not valued by the "
                "orientation's performance objective.",
                ha="left",
                va="bottom",
                fontsize=9.5,
                color=GRAY,
                wrap=True,
            )

        label = str(data.dmu_id)
        if data.period is not None:
            label = f"{label} · {data.period}"
        figure.suptitle(
            f"Selected variable-specific operating plan for {label}",
            x=0.01,
            y=0.985,
            ha="left",
            fontsize=14.0,
            fontweight="bold",
        )
        figure.text(
            0.01,
            0.935,
            f"{_sbm_mandate(data.orientation, has_bad_output=has_bad_output)}  ·  "
            "SBM efficiency "
            f"{data.efficiency:.3f}",
            ha="left",
            va="top",
            fontsize=10.0,
            color=GRAY,
        )
        interpretation_note = (
            "This fitted account assumes separability and strong disposability; "
            "residual reduction is a feasible benchmark opportunity, not a damage "
            "valuation, causal conclusion, or prescription."
            if has_bad_output
            else "Benchmark opportunities are evidence of feasibility, not causal or "
            "prescriptive claims."
        )
        note = (
            "One certified solver-selected optimum; alternative peers or targets "
            "may fit the same score. Quantities may use different physical units.\n"
            f"{interpretation_note}  ·  "
            + "  ·  ".join(f"{key}: {value}" for key, value in data.provenance)
        )
        figure.text(
            0.01,
            0.012,
            note,
            ha="left",
            va="bottom",
            fontsize=9.5,
            color=GRAY,
            wrap=True,
        )
        figure.subplots_adjust(
            left=0.24,
            right=0.97,
            top=0.84,
            bottom=0.18,
        )
    return figure


_RADIAL_ROLE_PRESENTATION = {
    "input": ("Resource", BLUE),
    "output": ("Desirable service", TEAL),
}


def _radial_role_presentation(role: object) -> tuple[str, str]:
    try:
        return _RADIAL_ROLE_PRESENTATION[str(role)]
    except KeyError as error:
        raise PlotNotAvailableError(
            f"unsupported radial variable role {role!r}"
        ) from error


def _radial_score_account(orientation: str) -> tuple[str, str]:
    if orientation == "input":
        return (
            "\N{GREEK SMALL LETTER THETA}",
            "is the fitted common resource-use factor; 1 \N{MINUS SIGN} "
            "\N{GREEK SMALL LETTER THETA} is the proportional resource-saving "
            "opportunity before variable-specific completion",
        )
    if orientation == "output":
        return (
            "\N{GREEK SMALL LETTER PHI}",
            "is the fitted common service-expansion factor; "
            "\N{GREEK SMALL LETTER PHI} \N{MINUS SIGN} 1 is the proportional "
            "service-gain opportunity before variable-specific completion",
        )
    raise PlotNotAvailableError(f"unsupported radial orientation {orientation!r}")


def _radial_stage_one_label(row: Any, orientation: str) -> str:
    change = float(row.radial_change)
    amount = f"{change:,.6f}"
    if orientation == "input":
        if row.role == "output":
            return "Service maintained\n(common resource phase)"
        if change == 0.0:
            return "No common resource saving"
        return f"Common resource saving\n\N{MINUS SIGN}{amount}"
    if orientation == "output":
        if row.role == "input":
            return "Resource maintained\n(common service phase)"
        if change == 0.0:
            return "No common service gain"
        return f"Common service gain\n+{amount}"
    raise PlotNotAvailableError(f"unsupported radial orientation {orientation!r}")


def _radial_completion_label(row: Any) -> str:
    slack = float(row.slack_completion)
    if slack == 0.0:
        return "No phase-two completion"
    if row.role == "input":
        return f"Phase-two resource saving\n\N{MINUS SIGN}{slack:,.6f}"
    return f"Phase-two service gain\n+{slack:,.6f}"


def _radial_status_interpretation(data: RadialImprovementPlotData) -> str:
    if data.is_efficient:
        return (
            "The fitted account reports neither a common-factor opportunity nor "
            "a certified variable-specific completion."
        )
    if data.is_radially_efficient:
        return (
            "The common percentage rule has stopped, but at least one "
            "variable-specific benchmark gap remains."
        )
    return (
        "A common percentage opportunity remains before any variable-specific "
        "completion is recorded."
    )


def _radial_quantity(value: float) -> str:
    if abs(value - round(value)) <= 5e-10:
        return f"{value:,.0f}"
    return f"{value:,.6f}"


def render_radial_improvement(
    data: RadialImprovementPlotData,
    *,
    theme: str = "deapack",
) -> Any:
    """Render one certified two-stage radial performance account."""
    if theme != "deapack":
        raise PlotNotAvailableError(
            f"unknown theme {theme!r}; the available theme is 'deapack'"
        )
    mpl, plt, _ = _load_matplotlib()
    variables = data.variables.sort_values("order", kind="stable").reset_index(
        drop=True
    )
    height = max(7.2, 3.75 + 1.18 * len(variables))
    score_symbol, score_account = _radial_score_account(data.orientation)

    with mpl.rc_context(rc=_THEME):
        figure, axis = plt.subplots(figsize=(8.2, height))
        axis.set_xlim(0.0, 1.0)
        axis.set_ylim(-0.5, len(variables) + 2.0)
        axis.axis("off")

        axis.text(
            0.02,
            len(variables) + 1.62,
            "DEA-certified two-stage radial performance account",
            ha="left",
            va="center",
            fontsize=13.0,
            fontweight="bold",
            color=INK,
        )
        axis.text(
            0.02,
            len(variables) + 1.23,
            f"{score_symbol} = {data.native_score:.6f}",
            ha="left",
            va="center",
            fontsize=18.0,
            fontweight="bold",
            color=ORANGE,
        )
        axis.text(
            0.25,
            len(variables) + 1.23,
            textwrap.fill(score_account, width=68),
            ha="left",
            va="center",
            fontsize=10.5,
            color=INK,
        )

        radial_status = "YES" if data.is_radially_efficient else "NO"
        strong_status = "YES" if data.is_efficient else "NO"
        axis.text(
            0.02,
            len(variables) + 0.82,
            f"Radially efficient: {radial_status}",
            ha="left",
            va="center",
            fontsize=10.5,
            fontweight="bold",
            color=TEAL if data.is_radially_efficient else ORANGE,
            bbox={
                "boxstyle": "round,pad=0.28",
                "facecolor": "white",
                "edgecolor": GRID,
            },
        )
        axis.text(
            0.29,
            len(variables) + 0.82,
            f"Strongly efficient (score + slacks): {strong_status}",
            ha="left",
            va="center",
            fontsize=10.5,
            fontweight="bold",
            color=TEAL if data.is_efficient else ORANGE,
            bbox={
                "boxstyle": "round,pad=0.28",
                "facecolor": "white",
                "edgecolor": GRID,
            },
        )
        axis.text(
            0.02,
            len(variables) + 0.52,
            f"Reported radial efficiency index: {data.efficiency:.6f}",
            ha="left",
            va="center",
            fontsize=9.5,
            color=GRAY,
        )
        axis.text(
            0.02,
            len(variables) + 0.29,
            _radial_status_interpretation(data),
            ha="left",
            va="center",
            fontsize=10.0,
            color=GRAY,
        )

        for x, label in (
            (0.24, "Observed operation"),
            (0.53, "Phase-one radial target"),
            (0.84, "Selected completed target"),
        ):
            axis.text(
                x,
                len(variables) + 0.04,
                label,
                ha="center",
                va="center",
                fontsize=10.0,
                fontweight="bold",
                color=GRAY,
            )

        for position, row in enumerate(variables.itertuples(index=False)):
            y = len(variables) - position - 0.55
            role_label, role_color = _radial_role_presentation(row.role)
            card = mpl.patches.FancyBboxPatch(
                (0.015, y - 0.45),
                0.97,
                0.88,
                boxstyle="round,pad=0.012,rounding_size=0.018",
                facecolor="white",
                edgecolor=GRID,
                linewidth=1.0,
                zorder=1,
            )
            axis.add_patch(card)
            axis.plot(
                [0.135, 0.135],
                [y - 0.38, y + 0.36],
                color=role_color,
                linewidth=3.2,
                solid_capstyle="round",
                zorder=2,
            )
            axis.text(
                0.03,
                y + 0.11,
                row.variable_label,
                ha="left",
                va="center",
                fontsize=10.5,
                fontweight="bold",
                color=INK,
            )
            axis.text(
                0.03,
                y - 0.17,
                role_label,
                ha="left",
                va="center",
                fontsize=9.5,
                color=role_color,
            )
            for x, value in (
                (0.24, row.observed),
                (0.53, row.radial_target),
                (0.84, row.target),
            ):
                axis.text(
                    x,
                    y - 0.04,
                    _radial_quantity(float(value)),
                    ha="center",
                    va="center",
                    fontsize=11.5,
                    fontweight="bold" if x == 0.84 else "normal",
                    color=INK,
                )
            axis.annotate(
                "",
                xy=(0.44, y - 0.04),
                xytext=(0.33, y - 0.04),
                arrowprops={
                    "arrowstyle": "-|>",
                    "color": role_color,
                    "linewidth": 1.3,
                    "shrinkA": 2,
                    "shrinkB": 2,
                },
                zorder=3,
            )
            axis.text(
                0.385,
                y + 0.25,
                _radial_stage_one_label(row, data.orientation),
                ha="center",
                va="center",
                fontsize=9.5,
                color=role_color,
            )
            axis.annotate(
                "",
                xy=(0.75, y - 0.04),
                xytext=(0.63, y - 0.04),
                arrowprops={
                    "arrowstyle": "-|>",
                    "color": GRAY,
                    "linewidth": 1.15,
                    "linestyle": "--",
                    "shrinkA": 2,
                    "shrinkB": 2,
                },
                zorder=3,
            )
            axis.text(
                0.69,
                y + 0.25,
                _radial_completion_label(row),
                ha="center",
                va="center",
                fontsize=9.5,
                color=GRAY,
            )

        period_suffix = (
            ""
            if data.period_label is None
            else f" \N{MIDDLE DOT} period {data.period_label}"
        )
        figure.suptitle(
            f"Radial performance account for {data.dmu_label}{period_suffix}",
            fontsize=15.0,
            fontweight="bold",
            y=0.975,
        )
        provenance = "  \N{MIDDLE DOT}  ".join(
            f"{label}: {value}" for label, value in data.provenance
        )
        note = (
            "Each card retains the variable's original physical unit; no common "
            "quantity axis or geometric distance is constructed  \N{MIDDLE DOT}  "
            "phase-two completion records variable-specific slack at the same "
            f"fitted radial score; it never changes {score_symbol}  "
            "\N{MIDDLE DOT}  the arrows are a performance account, not an "
            "implementation sequence  \N{MIDDLE DOT}  the selected completed "
            "target is one solver-selected feasible benchmark under the fitted "
            "technology, not necessarily unique, closest, least-cost, causal, or "
            "prescriptive  \N{MIDDLE DOT}  target status: "
            f"{data.target_status.replace('_', ' ')}  \N{MIDDLE DOT}  maximum "
            "reconstruction residual: "
            f"{data.max_reconstruction_residual:.2e}  \N{MIDDLE DOT}  {provenance}"
        )
        figure.text(
            0.012,
            0.012,
            note,
            ha="left",
            va="bottom",
            fontsize=9.5,
            color=GRAY,
            wrap=True,
        )
        figure.subplots_adjust(left=0.04, right=0.98, top=0.91, bottom=0.20)
    return figure


_ENVIRONMENTAL_DDF_ROLE_PRESENTATION = {
    "input": ("Resource", BLUE),
    "output": ("Desirable service", TEAL),
    "bad_output": ("Undesirable residual", ORANGE),
}


_DIRECTIONAL_DDF_ROLE_PRESENTATION = {
    "input": ("Resource", BLUE),
    "output": ("Desirable service", TEAL),
}


def _directional_ddf_move_label(row: Any) -> str:
    amount = f"{float(row.directional_change):,.6f}"
    if row.role == "input":
        if float(row.directional_change) == 0.0:
            return "Resource protected\n(no declared saving)"
        return f"Declared resource saving\n\N{MINUS SIGN}{amount}"
    if float(row.directional_change) == 0.0:
        return "Service protected\n(no declared addition)"
    return f"Declared service addition\n+{amount}"


def _directional_ddf_completion_label(row: Any) -> str:
    slack = float(row.slack_completion)
    sign = "\N{MINUS SIGN}" if row.role == "input" else "+"
    if slack == 0.0:
        return "Slack completion\n0"
    return f"Slack completion\n{sign}{slack:,.6f}"


def render_directional_ddf_improvement(
    data: DirectionalDDFImprovementPlotData,
    *,
    theme: str = "deapack",
) -> Any:
    """Render one DEA-certified ordinary directional benchmark account."""
    if theme != "deapack":
        raise PlotNotAvailableError(
            f"unknown theme {theme!r}; the available theme is 'deapack'"
        )
    mpl, plt, _ = _load_matplotlib()
    variables = data.variables.sort_values("order", kind="stable").reset_index(
        drop=True
    )
    height = max(7.0, 3.35 + 1.17 * len(variables))

    with mpl.rc_context(rc=_THEME):
        figure, axis = plt.subplots(figsize=(12.4, height))
        axis.set_xlim(0.0, 1.0)
        axis.set_ylim(-0.4, len(variables) + 1.85)
        axis.axis("off")

        axis.text(
            0.02,
            len(variables) + 1.46,
            "DEA-certified benchmark account for a declared programme",
            ha="left",
            va="center",
            fontsize=12.0,
            fontweight="bold",
            color=INK,
        )
        axis.text(
            0.02,
            len(variables) + 1.10,
            f"β = {data.beta:.6f}",
            ha="left",
            va="center",
            fontsize=18.0,
            fontweight="bold",
            color=ORANGE,
        )
        axis.text(
            0.19,
            len(variables) + 1.10,
            "is the largest multiple represented as feasible by the fitted DEA "
            "technology; βg is reported below in each variable's original unit",
            ha="left",
            va="center",
            fontsize=9.8,
            color=INK,
        )
        input_rows = variables.loc[variables["role"].eq("input")]
        output_rows = variables.loc[variables["role"].eq("output")]
        resource_mandate = (
            "Resources protected"
            if input_rows["directional_change"].eq(0.0).all()
            else "Resource contraction"
        )
        service_mandate = (
            "Services protected"
            if output_rows["directional_change"].eq(0.0).all()
            else "Desirable-service expansion"
        )
        axis.text(
            0.02,
            len(variables) + 0.72,
            f"{resource_mandate}  ·  {service_mandate}",
            ha="left",
            va="center",
            fontsize=9.2,
            color=GRAY,
        )

        for x, label in (
            (0.23, "Observed operation"),
            (0.52, "Target promised by βg"),
            (0.83, "Selected completed target"),
        ):
            axis.text(
                x,
                len(variables) + 0.30,
                label,
                ha="center",
                va="center",
                fontsize=8.4,
                fontweight="bold",
                color=GRAY,
            )

        for position, row in enumerate(variables.itertuples(index=False)):
            y = len(variables) - position - 0.35
            try:
                role_label, role_color = _DIRECTIONAL_DDF_ROLE_PRESENTATION[row.role]
            except KeyError as error:
                raise PlotNotAvailableError(
                    f"unsupported directional DDF variable role {row.role!r}"
                ) from error
            card = mpl.patches.FancyBboxPatch(
                (0.015, y - 0.45),
                0.97,
                0.88,
                boxstyle="round,pad=0.012,rounding_size=0.018",
                facecolor="white",
                edgecolor=GRID,
                linewidth=1.0,
                zorder=1,
            )
            axis.add_patch(card)
            axis.plot(
                [0.135, 0.135],
                [y - 0.38, y + 0.36],
                color=role_color,
                linewidth=3.2,
                solid_capstyle="round",
                zorder=2,
            )
            axis.text(
                0.03,
                y + 0.11,
                row.variable_label,
                ha="left",
                va="center",
                fontsize=9.3,
                fontweight="bold",
                color=INK,
            )
            axis.text(
                0.03,
                y - 0.17,
                role_label,
                ha="left",
                va="center",
                fontsize=8.0,
                color=role_color,
            )
            for x, value in (
                (0.23, row.observed),
                (0.52, row.directional_target),
                (0.83, row.target),
            ):
                axis.text(
                    x,
                    y,
                    _directional_quantity(float(value)),
                    ha="center",
                    va="center",
                    fontsize=10.2,
                    fontweight="bold" if x == 0.87 else "normal",
                    color=INK,
                )
            axis.annotate(
                "",
                xy=(0.43, y),
                xytext=(0.32, y),
                arrowprops={
                    "arrowstyle": "-|>",
                    "color": role_color,
                    "linewidth": 1.3,
                    "shrinkA": 2,
                    "shrinkB": 2,
                },
                zorder=3,
            )
            axis.text(
                0.375,
                y + 0.26,
                _directional_ddf_move_label(row),
                ha="center",
                va="center",
                fontsize=7.3,
                color=role_color,
            )
            axis.annotate(
                "",
                xy=(0.74, y),
                xytext=(0.62, y),
                arrowprops={
                    "arrowstyle": "-|>",
                    "color": GRAY,
                    "linewidth": 1.15,
                    "linestyle": "--",
                    "shrinkA": 2,
                    "shrinkB": 2,
                },
                zorder=3,
            )
            axis.text(
                0.68,
                y + 0.26,
                _directional_ddf_completion_label(row),
                ha="center",
                va="center",
                fontsize=7.3,
                color=GRAY,
            )

        period_suffix = (
            "" if data.period_label is None else f" · period {data.period_label}"
        )
        figure.suptitle(
            f"Directional benchmark account for {data.dmu_label}{period_suffix}",
            fontsize=14.0,
            fontweight="bold",
            y=0.975,
        )
        provenance = "  ·  ".join(
            f"{label}: {value}" for label, value in data.provenance
        )
        note = (
            "Each card keeps the variable's original unit; no common quantity axis "
            "is constructed  ·  β counts attainable units of the declared package, "
            "conditional on the fitted DEA technology, not a generic inefficiency "
            "percentage  ·  slack completion "
            "records additional variable-specific slack after βg  ·  the target is "
            "one solver-selected feasible benchmark under the fitted technology, "
            "not a unique plan, engineering prescription, causal explanation, or "
            f"least-cost plan  ·  maximum reconstruction residual: "
            f"{data.max_reconstruction_residual:.2e}  ·  {provenance}"
        )
        figure.text(
            0.012,
            0.012,
            note,
            ha="left",
            va="bottom",
            fontsize=8.0,
            color=GRAY,
            wrap=True,
        )
        figure.subplots_adjust(left=0.04, right=0.98, top=0.91, bottom=0.15)
    return figure


def _environmental_ddf_role_presentation(role: object) -> tuple[str, str]:
    try:
        return _ENVIRONMENTAL_DDF_ROLE_PRESENTATION[str(role)]
    except KeyError as error:
        raise PlotNotAvailableError(
            f"unsupported environmental DDF variable role {role!r}"
        ) from error


def _environmental_ddf_move_label(row: Any) -> str:
    amount = f"{float(row.directional_change):,.6f}"
    if row.role == "input":
        if float(row.directional_change) == 0.0:
            return "Fixed resource\n(no declared change)"
        return f"Declared resource saving\n\N{MINUS SIGN}{amount}"
    if row.role == "output":
        if float(row.directional_change) == 0.0:
            return "Service held fixed\n(no declared change)"
        return f"Declared service expansion\n+{amount}"
    if float(row.directional_change) == 0.0:
        return "Residual held fixed\n(no declared change)"
    return f"Declared residual reduction\n\N{MINUS SIGN}{amount}"


def _environmental_ddf_completion_label(row: Any) -> str:
    if not bool(row.slack_allowed):
        return "No residual slack permitted\n(common-factor equality)"
    slack = float(row.slack_completion)
    sign = "\N{MINUS SIGN}" if row.role == "input" else "+"
    if slack == 0.0:
        return "Slack completion\n0"
    return f"Slack completion\n{sign}{slack:,.6f}"


def _directional_quantity(value: float) -> str:
    if abs(value - round(value)) <= 5e-10:
        return f"{value:,.0f}"
    return f"{value:,.6f}"


def render_environmental_ddf_improvement(
    data: EnvironmentalDDFImprovementPlotData,
    *,
    theme: str = "deapack",
) -> Any:
    """Render one certified common-factor environmental DDF plan."""
    if theme != "deapack":
        raise PlotNotAvailableError(
            f"unknown theme {theme!r}; the available theme is 'deapack'"
        )
    mpl, plt, _ = _load_matplotlib()
    variables = data.variables.sort_values("order", kind="stable").reset_index(
        drop=True
    )
    # Keep the programme account and the original-unit ledger vertically
    # stacked for a handbook column.  The narrower canvas prevents a nominal
    # 9-point label from becoming unreadably small when embedded at 600 px.
    height = max(9.3, 6.0 + 0.78 * len(variables))

    with mpl.rc_context(rc=_THEME):
        figure = plt.figure(figsize=(8.2, height))
        grid = figure.add_gridspec(2, 1, height_ratios=(0.78, 3.22), hspace=0.12)
        programme_axis = figure.add_subplot(grid[0, 0])
        ledger_axis = figure.add_subplot(grid[1, 0])
        for axis in (programme_axis, ledger_axis):
            axis.set_xlim(0.0, 1.0)
            axis.axis("off")
        programme_axis.set_ylim(0.0, 1.0)
        ledger_axis.set_ylim(-0.18, len(variables) + 0.82)

        programme_axis.text(
            0.00,
            0.92,
            "Certified common directional programme",
            ha="left",
            va="top",
            fontsize=12.0,
            fontweight="bold",
            color=INK,
        )
        programme_axis.text(
            0.00,
            0.61,
            f"β = {data.beta:.6f}",
            ha="left",
            va="center",
            fontsize=18.0,
            fontweight="bold",
            color=ORANGE,
        )
        programme_axis.text(
            0.34,
            0.61,
            (
                "sets one common ambition level across the declared commitments\n"
                f"1 / (1 + β) = {data.efficiency:.6f}"
            ),
            ha="left",
            va="center",
            fontsize=10.0,
            color=INK,
            linespacing=1.35,
        )
        resource_mandate = (
            "Fixed resources"
            if variables.loc[variables["role"].eq("input"), "directional_change"]
            .eq(0.0)
            .all()
            else "Resource contraction"
        )
        service_mandate = (
            "Fixed desirable services"
            if variables.loc[variables["role"].eq("output"), "directional_change"]
            .eq(0.0)
            .all()
            else "Desirable-service expansion"
        )
        residual_mandate = (
            "Fixed undesirable residuals"
            if variables.loc[variables["role"].eq("bad_output"), "directional_change"]
            .eq(0.0)
            .all()
            else "Undesirable-residual reduction"
        )
        programme_axis.text(
            0.00,
            0.13,
            f"{resource_mandate}  ·  {service_mandate}\n{residual_mandate}",
            ha="left",
            va="bottom",
            fontsize=9.5,
            color=GRAY,
            linespacing=1.35,
        )

        for x, label in (
            (0.29, "Current operation"),
            (0.58, "After declared programme"),
            (0.87, "Certified target"),
        ):
            ledger_axis.text(
                x,
                len(variables) + 0.50,
                label,
                ha="center",
                va="center",
                fontsize=9.2,
                fontweight="bold",
                color=GRAY,
            )

        for position, row in enumerate(variables.itertuples(index=False)):
            y = len(variables) - position - 0.20
            role_label, role_color = _environmental_ddf_role_presentation(row.role)
            role_display = (
                "Undesirable\nresidual" if row.role == "bad_output" else role_label
            )
            card = mpl.patches.FancyBboxPatch(
                (0.00, y - 0.39),
                0.99,
                0.76,
                boxstyle="round,pad=0.012,rounding_size=0.018",
                facecolor="white",
                edgecolor=GRID,
                linewidth=1.0,
                zorder=1,
            )
            ledger_axis.add_patch(card)
            ledger_axis.plot(
                [0.17, 0.17],
                [y - 0.32, y + 0.30],
                color=role_color,
                linewidth=3.2,
                solid_capstyle="round",
                zorder=2,
            )
            ledger_axis.text(
                0.015,
                y + 0.10,
                row.variable_label,
                ha="left",
                va="center",
                fontsize=9.7,
                fontweight="bold",
                color=INK,
            )
            ledger_axis.text(
                0.015,
                y - 0.15,
                role_display,
                ha="left",
                va="center",
                fontsize=9.2,
                color=role_color,
                linespacing=1.15,
            )
            for x, value in (
                (0.29, row.observed),
                (0.58, row.directional_target),
                (0.87, row.target),
            ):
                ledger_axis.text(
                    x,
                    y - 0.08,
                    _directional_quantity(float(value)),
                    ha="center",
                    va="center",
                    fontsize=10.2,
                    fontweight="bold" if x == 0.83 else "normal",
                    color=INK,
                )
            ledger_axis.annotate(
                "",
                xy=(0.49, y - 0.08),
                xytext=(0.38, y - 0.08),
                arrowprops={
                    "arrowstyle": "-|>",
                    "color": role_color,
                    "linewidth": 1.3,
                    "shrinkA": 2,
                    "shrinkB": 2,
                },
                zorder=3,
            )
            ledger_axis.text(
                0.435,
                y + 0.18,
                _environmental_ddf_move_label(row),
                ha="center",
                va="center",
                fontsize=9.2,
                color=role_color,
                linespacing=1.2,
            )
            ledger_axis.annotate(
                "",
                xy=(0.78, y - 0.08),
                xytext=(0.67, y - 0.08),
                arrowprops={
                    "arrowstyle": "-|>",
                    "color": GRAY,
                    "linewidth": 1.15,
                    "linestyle": "--",
                    "shrinkA": 2,
                    "shrinkB": 2,
                },
                zorder=3,
            )
            ledger_axis.text(
                0.725,
                y + 0.18,
                _environmental_ddf_completion_label(row),
                ha="center",
                va="center",
                fontsize=9.2,
                color=GRAY,
                linespacing=1.2,
            )

        period_suffix = "" if data.period is None else f" · period {data.period}"
        figure.suptitle(
            f"Environmental directional improvement for {data.dmu_id}{period_suffix}",
            fontsize=14.0,
            fontweight="bold",
            y=0.975,
        )
        provenance = "  ·  ".join(
            f"{label}: {value}" for label, value in data.provenance
        )
        note = (
            "Each card uses the variable's original unit; no common quantity axis "
            "is constructed. β is a common programme ambition, not an SBM score.\n"
            "Targets are one selected feasible benchmark under the fitted DEA "
            "technology, not a unique plan, engineering implementation, causal "
            "explanation, or cost conclusion.\n"
            f"Maximum reconstruction residual: "
            f"{data.max_reconstruction_residual:.2e}  ·  {provenance}"
        )
        figure.text(
            0.012,
            0.012,
            note,
            ha="left",
            va="bottom",
            fontsize=9.2,
            color=GRAY,
            wrap=True,
        )
        figure.subplots_adjust(
            left=0.055,
            right=0.965,
            top=0.91,
            bottom=0.17,
        )
    return figure


def _metafrontier_note(data: MetafrontierPlotData) -> str:
    parts = [
        "Meta efficiency = group efficiency \N{MULTIPLICATION SIGN} MTR",
        (
            "the connector links the same organization's two benchmark results; "
            "MTR is their ratio"
        ),
        "neither component identifies causes or assigns management blame",
        f"maximum identity residual: {data.max_reconstruction_residual:.2e}",
    ]
    parts.extend(f"{label}: {value}" for label, value in data.provenance)
    if data.omitted_observation_count:
        parts.append(
            f"{data.omitted_observation_count} uncertified decomposition row(s) omitted"
        )
    return "  ·  ".join(parts)


def render_metafrontier(
    data: MetafrontierPlotData,
    *,
    theme: str = "deapack",
) -> Any:
    """Render one certified radial group/metafrontier decomposition."""
    if theme != "deapack":
        raise PlotNotAvailableError(
            f"unknown theme {theme!r}; the available theme is 'deapack'"
        )
    mpl, plt, line_2d = _load_matplotlib()
    observations = data.observations.reset_index(drop=True)
    positions = list(range(len(observations)))
    height = max(4.9, min(12.0, 3.4 + 0.43 * len(observations)))

    with mpl.rc_context(rc=_THEME):
        figure, axis = plt.subplots(figsize=(9.5, height))
        for position, row in enumerate(observations.itertuples(index=False)):
            axis.plot(
                [row.metafrontier_efficiency, row.group_efficiency],
                [position, position],
                color=GRAY,
                linewidth=2.0,
                alpha=0.72,
                solid_capstyle="round",
                zorder=2,
            )
            axis.text(
                1.035,
                position,
                f"MTR {row.metatechnology_ratio:.2f}",
                ha="left",
                va="center",
                fontsize=8.4,
                color=INK,
            )

        axis.scatter(
            observations["group_efficiency"],
            positions,
            facecolors="white",
            edgecolors=TEAL,
            marker="D",
            s=76,
            linewidths=1.7,
            zorder=5,
        )
        axis.scatter(
            observations["metafrontier_efficiency"],
            positions,
            color=ORANGE,
            edgecolors="white",
            marker="o",
            s=46,
            linewidths=0.7,
            zorder=6,
        )

        group_labels = observations["group_label"].astype(str).tolist()
        group_orders = observations["_deapack_group_order"].tolist()
        for position in range(1, len(observations)):
            if group_orders[position] != group_orders[position - 1]:
                axis.axhline(
                    position - 0.5,
                    color=GRID,
                    linewidth=1.0,
                    zorder=1,
                )

        tick_labels = [
            f"{dmu}  ·  {group}"
            for dmu, group in zip(
                observations["dmu_id"].astype(str),
                group_labels,
                strict=True,
            )
        ]
        axis.set_yticks(positions)
        axis.set_yticklabels(tick_labels)
        axis.invert_yaxis()
        x_min = min(
            0.0,
            float(observations["metafrontier_efficiency"].min()),
            float(observations["group_efficiency"].min()),
        )
        axis.set_xlim(x_min, 1.19)
        axis.axvline(
            1.0,
            color=GRAY,
            linestyle=":",
            linewidth=1.1,
            zorder=1,
        )
        axis.set_xlabel(
            "Efficiency against the represented benchmark (higher is closer to 1)"
        )
        axis.set_ylabel("Organization and declared group")
        axis.grid(axis="x")
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)

        title = "Within-group performance and pooled-opportunity comparison"
        if data.period_label != "Cross-section":
            title = f"{title}\n{data.period_label}"
        axis.set_title(title, fontsize=14, fontweight="bold", pad=58)
        axis.legend(
            handles=[
                line_2d(
                    [],
                    [],
                    color=TEAL,
                    marker="D",
                    markerfacecolor="white",
                    linestyle="None",
                    label="Declared-group efficiency",
                ),
                line_2d(
                    [],
                    [],
                    color=ORANGE,
                    marker="o",
                    markeredgecolor="white",
                    linestyle="None",
                    label="Pooled-frontier efficiency",
                ),
                line_2d(
                    [],
                    [],
                    color=GRAY,
                    linewidth=2.0,
                    label="Link between benchmark results",
                ),
            ],
            loc="lower center",
            bbox_to_anchor=(0.5, 1.005),
            ncol=3,
            frameon=False,
            fontsize=8.5,
        )

        figure.text(
            0.01,
            0.012,
            _metafrontier_note(data),
            ha="left",
            va="bottom",
            fontsize=8.1,
            color=GRAY,
            wrap=True,
        )
        figure.tight_layout(rect=(0.0, 0.16, 1.0, 0.96))
    return figure


def _reference_frequency_note(data: ReferenceFrequencyPlotData) -> str:
    scope = (
        "Counts are reported selected-plan peer edges strictly above the fitted "
        f"source threshold ({data.source_peer_tolerance:g}) in one certified "
        "solver-selected plan; self-reference and use by other organizations "
        "remain separate. This thresholded account does not identify exact "
        "mathematical support. It does not enumerate alternate optima, identify "
        "a global reference set, diagnose outliers, or provide statistical "
        "inference."
    )
    coverage = (
        f"Showing {data.displayed_reference_count} of "
        f"{data.selected_reference_count} selected references from "
        f"{data.total_reference_count} potential organizations; ranked first "
        "by use by other organizations, then total use"
    )
    if data.omitted_selected_reference_count:
        coverage = (
            f"{coverage}; {data.omitted_selected_reference_count} selected "
            f"references omitted by the explicit top-{data.display_limit} "
            "readability rule"
        )
    else:
        coverage = f"{coverage}; no selected references omitted"
    accounting = (
        f"{data.zero_frequency_count} zero-frequency potential organizations "
        f"not drawn; {data.active_edge_count} reported edges across "
        f"{data.observation_count} evaluated organizations; "
        "zero additional solver calls"
    )
    provenance = "  ·  ".join(f"{label}: {value}" for label, value in data.provenance)
    return "\n".join((scope, f"{coverage}. {accounting}.", provenance))


def render_reference_frequency(
    data: ReferenceFrequencyPlotData,
    *,
    theme: str = "deapack",
) -> Any:
    """Render certified selected-plan peer-use frequency as stacked bars."""

    if theme != "deapack":
        raise PlotNotAvailableError(
            f"unknown theme {theme!r}; the available theme is 'deapack'"
        )
    mpl, plt, _line_2d = _load_matplotlib()
    references = data.references
    positions = list(range(len(references)))
    height = max(4.8, min(12.0, 2.8 + 0.31 * len(references)))

    with mpl.rc_context(rc=_THEME):
        figure, axis = plt.subplots(figsize=(9.5, height))
        other = references["other_reference_frequency"].to_numpy(dtype=float)
        self_use = references["self_reference_frequency"].to_numpy(dtype=float)
        axis.barh(
            positions,
            other,
            color=BLUE,
            edgecolor="white",
            linewidth=0.7,
            height=0.66,
            label="Selected by other organizations",
            zorder=3,
        )
        axis.barh(
            positions,
            self_use,
            left=other,
            color=TEAL,
            edgecolor="white",
            linewidth=0.7,
            height=0.66,
            label="Self-reference",
            zorder=3,
        )
        totals = other + self_use
        annotation_offset = max(0.08, float(totals.max(initial=0.0)) * 0.012)
        for position, total in zip(positions, totals, strict=True):
            axis.text(
                total + annotation_offset,
                position,
                f"{int(total)}",
                ha="left",
                va="center",
                fontsize=8.2,
                color=INK,
            )

        axis.set_yticks(positions)
        axis.set_yticklabels(references["display_label"].tolist())
        axis.invert_yaxis()
        axis.set_xlabel("Reported selected-plan peer edges above source threshold")
        axis.set_ylabel("Potential reference organization")
        axis.xaxis.set_major_locator(mpl.ticker.MaxNLocator(integer=True))
        axis.grid(axis="x")
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.set_title(
            "Use of organizations in one certified selected peer plan",
            fontsize=14,
            fontweight="bold",
            pad=14,
        )
        axis.legend(loc="lower right", frameon=False, fontsize=8.8)

        note = _reference_frequency_note(data)
        wrapped = "\n".join(
            textwrap.fill(
                paragraph,
                width=118,
                break_long_words=False,
                break_on_hyphens=False,
            )
            for paragraph in note.splitlines()
        )
        note_lines = len(wrapped.splitlines())
        bottom = min(0.30, 0.055 + 0.025 * note_lines)
        figure.text(
            0.01,
            0.012,
            wrapped,
            ha="left",
            va="bottom",
            fontsize=8.1,
            color=GRAY,
        )
        figure.tight_layout(rect=(0.0, bottom, 1.0, 1.0))
    return figure


__all__ = [
    "render_directional_ddf_improvement",
    "render_environmental_ddf_improvement",
    "render_frontier",
    "render_metafrontier",
    "render_performance",
    "render_process_attribution",
    "render_radial_improvement",
    "render_reference_frequency",
    "render_sbm_improvement",
    "render_trajectory",
]
