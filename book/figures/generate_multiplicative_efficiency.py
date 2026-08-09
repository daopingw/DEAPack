"""Generate the multiplicative-DEA teaching figure for the English book."""

from __future__ import annotations

from html import escape
from math import exp, log
from os import environ
from pathlib import Path
from xml.etree import ElementTree

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

OUTPUT = (
    Path(__file__).resolve().parents[1]
    / "_static"
    / "figures"
    / "multiplicative-technology-and-unit-invariance.svg"
)

INK = "#24323d"
GRAY = "#687780"
GRID = "#dce5e7"
TEAL = "#176b73"
ORANGE = "#d97732"
PALE_TEAL = "#dceff0"

matplotlib.rcParams.update(
    {
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "axes.titlecolor": INK,
        "font.family": "DejaVu Sans",
        "font.size": 10.5,
        "svg.fonttype": "none",
        "svg.hashsalt": "deapack-book-multiplicative-efficiency",
        "text.color": INK,
        "xtick.color": GRAY,
        "ytick.color": GRAY,
    }
)


def _geometric_segment(
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    count: int = 151,
) -> tuple[np.ndarray, np.ndarray]:
    """Return the source-defined geometric combinations of two plans."""
    weight = np.linspace(0.0, 1.0, count)
    x = start[0] ** (1.0 - weight) * end[0] ** weight
    y = start[1] ** (1.0 - weight) * end[1] ** weight
    return x, y


def _add_accessibility(path: Path, *, title: str, description: str) -> None:
    """Add an accessible name and description to Matplotlib's root SVG."""
    svg = path.read_text(encoding="utf-8")
    root_start = svg.index("<svg")
    root_end = svg.index(">", root_start)
    root = svg[root_start : root_end + 1]
    accessible_root = root[:-1] + (
        ' role="img" aria-labelledby="multiplicative-title multiplicative-description">'
    )
    accessibility = (
        f'\n <title id="multiplicative-title">{escape(title)}</title>'
        f'\n <desc id="multiplicative-description">'
        f"{escape(description)}</desc>"
    )
    svg = svg[:root_start] + accessible_root + accessibility + svg[root_end + 1 :]
    path.write_text(svg, encoding="utf-8")


def multiplicative_efficiency_figure() -> None:
    """Compare geometric benchmarking and the two source unit properties."""
    plans = {
        "A": (1.0, 2.0),
        "B": (2.0, 5.0),
        "C": (6.0, 9.0),
        "O": (4.0, 5.0),
    }
    left_x_1, left_y_1 = _geometric_segment(plans["A"], plans["B"])
    left_x_2, left_y_2 = _geometric_segment(plans["B"], plans["C"])

    # The source-exact two-organization unit test used in the right panel.
    log_two = log(2.0)
    score_1982 = np.array([exp(-2.0 * log_two), exp(-log_two)])
    score_1983 = np.array([exp(-log_two), exp(-log_two)])
    assert np.allclose(score_1982, [0.25, 0.5], atol=1e-14)
    assert np.allclose(score_1983, [0.5, 0.5], atol=1e-14)
    assert np.allclose(
        [left_x_1[0], left_y_1[0], left_x_1[-1], left_y_1[-1]],
        [*plans["A"], *plans["B"]],
        atol=1e-14,
    )
    assert np.allclose(
        [left_x_2[0], left_y_2[0], left_x_2[-1], left_y_2[-1]],
        [*plans["B"], *plans["C"]],
        atol=1e-14,
    )

    figure, (technology, units) = plt.subplots(
        1,
        2,
        figsize=(12.2, 5.7),
        gridspec_kw={"width_ratios": [1.18, 0.82], "wspace": 0.28},
    )
    figure.patch.set_facecolor("white")
    figure.suptitle(
        "Multiplicative DEA changes the benchmark account, not merely the data scale",
        fontsize=15,
        fontweight="bold",
        color=INK,
        y=0.975,
    )

    # Panel A remains entirely in original quantity units.  The dashed lines
    # are deliberately a contrast technology, not an alternative log display.
    technology.plot(
        np.r_[left_x_1, left_x_2[1:]],
        np.r_[left_y_1, left_y_2[1:]],
        color=TEAL,
        linewidth=3.0,
        label="1983 geometric-combination boundary",
        zorder=3,
    )
    technology.plot(
        [plans[name][0] for name in ("A", "B", "C")],
        [plans[name][1] for name in ("A", "B", "C")],
        color=GRAY,
        linestyle=(0, (5, 4)),
        linewidth=2.0,
        label="Ordinary arithmetic VRS — contrast only",
        zorder=2,
    )

    for name in ("A", "B", "C"):
        x, y = plans[name]
        technology.scatter(
            x,
            y,
            s=62,
            color=INK,
            edgecolor="white",
            linewidth=1.2,
            zorder=5,
        )
        technology.annotate(
            name,
            (x, y),
            xytext=(6, 7),
            textcoords="offset points",
            fontsize=10.5,
            fontweight="bold",
        )

    observed = plans["O"]
    target = plans["B"]
    technology.scatter(
        *observed,
        s=78,
        color=ORANGE,
        edgecolor="white",
        linewidth=1.3,
        zorder=6,
    )
    technology.annotate(
        "O",
        observed,
        xytext=(7, 7),
        textcoords="offset points",
        color=ORANGE,
        fontsize=10.5,
        fontweight="bold",
    )
    technology.annotate(
        "",
        xy=target,
        xytext=observed,
        arrowprops={
            "arrowstyle": "-|>",
            "color": ORANGE,
            "linewidth": 2.2,
            "shrinkA": 8,
            "shrinkB": 8,
        },
        zorder=4,
    )
    technology.text(
        3.0,
        4.62,
        r"target factor: $x^*/x_O=1/2$",
        color=ORANGE,
        fontsize=10,
        ha="center",
    )
    technology.set(
        title="A  Original quantity space: different attainable combinations",
        xlabel="Resource quantity, x",
        ylabel="Service quantity, y",
        xlim=(0.7, 6.5),
        ylim=(1.2, 9.7),
    )
    technology.grid(color=GRID, linewidth=0.8, alpha=0.78)
    technology.set_axisbelow(True)
    technology.legend(
        loc="lower right",
        frameon=True,
        framealpha=0.96,
        facecolor="white",
        edgecolor=GRID,
        fontsize=9.1,
    )

    # Panel B reproduces the exact unit-recoding implication from the two
    # source variants: A=(2,4), B=(4,4), with B assessed against A.
    positions = np.array([0.0, 1.0])
    units.plot(
        positions,
        score_1982,
        color=ORANGE,
        marker="o",
        markersize=8,
        linewidth=2.5,
        label="Original 1982 variant",
        zorder=4,
    )
    units.plot(
        positions,
        score_1983,
        color=TEAL,
        marker="s",
        markerfacecolor="white",
        markeredgewidth=2.0,
        markersize=9,
        linewidth=2.8,
        label="Unit-invariant 1983 variant",
        zorder=3,
    )
    # Redraw the coincident 1982 endpoint so both source implications remain
    # visible rather than silently hiding one another.
    units.scatter(
        [1.0],
        [score_1982[1]],
        color=ORANGE,
        s=33,
        zorder=5,
    )
    units.annotate(
        r"1982: $E$ changes $1/4\;\to\;1/2$",
        xy=(0.48, 0.37),
        color=ORANGE,
        ha="center",
        fontsize=10,
        fontweight="bold",
    )
    units.annotate(
        r"1983: $E=1/2$ in both reports",
        xy=(0.5, 0.5),
        xytext=(0.5, 0.64),
        textcoords="data",
        color=TEAL,
        ha="center",
        fontsize=10,
        fontweight="bold",
        arrowprops={
            "arrowstyle": "-[,widthB=5.0,lengthB=0.7",
            "color": TEAL,
            "linewidth": 1.4,
        },
    )
    units.text(
        0.5,
        0.16,
        "Same physical resource; only its reporting unit changes",
        transform=units.transAxes,
        ha="center",
        va="center",
        fontsize=9.4,
        color=GRAY,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": PALE_TEAL,
            "edgecolor": "none",
        },
    )
    units.text(
        0.5,
        0.075,
        r"1983 target co-scales: $x^*: 2\;\to\;4$",
        transform=units.transAxes,
        ha="center",
        va="center",
        fontsize=9.4,
        color=TEAL,
    )
    units.set(
        title="B  Unit recoding should not rewrite performance",
        ylabel="Multiplicative efficiency, E",
        xlim=(-0.18, 1.18),
        ylim=(0.0, 1.0),
        xticks=positions,
        xticklabels=(
            "Reported x",
            "Same resource\n" r"recoded $x^{\prime}=2x$",
        ),
    )
    units.set_yticks(np.linspace(0.0, 1.0, 5))
    units.grid(axis="y", color=GRID, linewidth=0.8, alpha=0.78)
    units.set_axisbelow(True)
    units.legend(
        loc="upper center",
        frameon=True,
        framealpha=0.96,
        facecolor="white",
        edgecolor=GRID,
        fontsize=9.1,
    )

    for axis in (technology, units):
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)

    figure.text(
        0.5,
        0.018,
        "Logs linearize the source-defined weighted-product technology; "
        "they are not a preprocessing recipe for ordinary DEA.",
        ha="center",
        va="bottom",
        fontsize=10.2,
        fontweight="bold",
        color=INK,
    )
    figure.subplots_adjust(top=0.84, bottom=0.19, left=0.075, right=0.975)

    title = "Multiplicative DEA technology and unit invariance"
    description = (
        "Two panels in original quantity units. The left panel contrasts a "
        "curved 1983 geometric-combination boundary through organizations A, "
        "B, and C with straight ordinary arithmetic VRS chords shown only for "
        "comparison; inefficient organization O moves to B with an input "
        "target factor of one half. The right panel shows the same physical "
        "resource recoded at twice its reported quantity: the original 1982 "
        "multiplicative efficiency changes from one quarter to one half, while "
        "the 1983 efficiency stays at one half and its input target co-scales "
        "from two to four. A footer states that logs linearize the "
        "source-defined weighted-product technology and are not a preprocessing "
        "recipe for ordinary DEA."
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(
        OUTPUT,
        format="svg",
        metadata={"Title": title, "Description": description, "Date": None},
    )
    if preview := environ.get("DEAPACK_FIGURE_PREVIEW"):
        figure.savefig(preview, format="png", dpi=160)
    plt.close(figure)
    _add_accessibility(OUTPUT, title=title, description=description)

    root = ElementTree.parse(OUTPUT).getroot()
    assert root.attrib.get("role") == "img"
    assert root.attrib.get("aria-labelledby") == (
        "multiplicative-title multiplicative-description"
    )


def main() -> None:
    multiplicative_efficiency_figure()


if __name__ == "__main__":
    main()
