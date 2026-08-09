"""Generate dependency-free conceptual and management figures for the book."""

from __future__ import annotations

from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "_static" / "figures"
WIDTH = 760
HEIGHT = 500
LEFT = 82
RIGHT = 704
TOP = 48
BOTTOM = 438

INK = "#24323d"
GRID = "#dce5e7"
TEAL = "#176b73"
ORANGE = "#d97732"
BLUE = "#356fa3"
PURPLE = "#76528f"
PALE_TEAL = "#dceff0"
PALE_ORANGE = "#f8e8dc"
GRAY = "#687780"

DMUS = {
    "A": (1.0, 1.0),
    "B": (2.0, 2.5),
    "C": (3.0, 3.3),
    "D": (4.0, 3.8),
    "E": (2.0, 1.5),
    "F": (3.0, 2.0),
    "G": (4.0, 2.8),
    "H": (3.5, 3.0),
}


def _point(x: float, y: float, *, xmax: float, ymax: float) -> tuple[float, float]:
    px = LEFT + (RIGHT - LEFT) * x / xmax
    py = BOTTOM - (BOTTOM - TOP) * y / ymax
    return px, py


def _path(points: list[tuple[float, float]]) -> str:
    return " ".join(
        f"{'M' if index == 0 else 'L'} {x:.2f} {y:.2f}"
        for index, (x, y) in enumerate(points)
    )


def _base(title: str, description: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
        f'height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" '
        'aria-labelledby="title description">',
        f'<title id="title">{title}</title>',
        f'<desc id="description">{description}</desc>',
        "<defs>",
        '<marker id="arrow-teal" markerWidth="10" markerHeight="10" '
        'refX="8" refY="3" orient="auto" markerUnits="strokeWidth">'
        f'<path d="M0,0 L0,6 L9,3 z" fill="{TEAL}"/></marker>',
        '<marker id="arrow-orange" markerWidth="10" markerHeight="10" '
        'refX="8" refY="3" orient="auto" markerUnits="strokeWidth">'
        f'<path d="M0,0 L0,6 L9,3 z" fill="{ORANGE}"/></marker>',
        '<marker id="arrow-purple" markerWidth="10" markerHeight="10" '
        'refX="8" refY="3" orient="auto" markerUnits="strokeWidth">'
        f'<path d="M0,0 L0,6 L9,3 z" fill="{PURPLE}"/></marker>',
        '<marker id="axis-arrow" markerWidth="9" markerHeight="9" '
        'refX="8" refY="4" orient="auto">'
        f'<path d="M0,0 L0,8 L8,4 z" fill="{INK}"/></marker>',
        "</defs>",
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="white"/>',
    ]


def _axes(
    parts: list[str],
    *,
    xmax: float,
    ymax: float,
    xlabel: str = "x",
    ylabel: str = "y",
) -> None:
    for x in range(1, int(xmax) + 1):
        px, _ = _point(float(x), 0.0, xmax=xmax, ymax=ymax)
        parts.append(
            f'<line x1="{px:.2f}" y1="{TOP}" x2="{px:.2f}" y2="{BOTTOM}" '
            f'stroke="{GRID}" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{px:.2f}" y="{BOTTOM + 25}" text-anchor="middle" '
            f'font-size="14" fill="{GRAY}">{x}</text>'
        )
    for y in range(1, int(ymax) + 1):
        _, py = _point(0.0, float(y), xmax=xmax, ymax=ymax)
        parts.append(
            f'<line x1="{LEFT}" y1="{py:.2f}" x2="{RIGHT}" y2="{py:.2f}" '
            f'stroke="{GRID}" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{LEFT - 18}" y="{py + 5:.2f}" text-anchor="end" '
            f'font-size="14" fill="{GRAY}">{y}</text>'
        )
    parts.extend(
        [
            f'<line x1="{LEFT}" y1="{BOTTOM}" x2="{RIGHT + 12}" y2="{BOTTOM}" '
            f'stroke="{INK}" stroke-width="2" marker-end="url(#axis-arrow)"/>',
            f'<line x1="{LEFT}" y1="{BOTTOM}" x2="{LEFT}" y2="{TOP - 12}" '
            f'stroke="{INK}" stroke-width="2" marker-end="url(#axis-arrow)"/>',
            f'<text x="{RIGHT + 20}" y="{BOTTOM + 6}" font-size="18" '
            f'font-style="italic" fill="{INK}">{xlabel}</text>',
            f'<text x="{LEFT - 5}" y="{TOP - 22}" font-size="18" '
            f'font-style="italic" fill="{INK}">{ylabel}</text>',
        ]
    )


def _dmu(
    parts: list[str],
    label: str,
    x: float,
    y: float,
    *,
    xmax: float,
    ymax: float,
    fill: str = INK,
    radius: float = 6.0,
    dx: float = 9.0,
    dy: float = -9.0,
) -> None:
    px, py = _point(x, y, xmax=xmax, ymax=ymax)
    parts.append(
        f'<circle cx="{px:.2f}" cy="{py:.2f}" r="{radius}" fill="{fill}" '
        'stroke="white" stroke-width="2"/>'
    )
    parts.append(
        f'<text x="{px + dx:.2f}" y="{py + dy:.2f}" font-size="16" '
        f'font-weight="600" fill="{fill}">{label}</text>'
    )


def frontier_orientations() -> str:
    xmax, ymax = 4.5, 4.2
    parts = _base(
        "Resource-saving and output-expansion benchmarks",
        "Observed DMUs, a VRS frontier, and input- and output-oriented "
        "operating targets for DMU E.",
    )
    _axes(parts, xmax=xmax, ymax=ymax)

    frontier = [_point(*DMUS[name], xmax=xmax, ymax=ymax) for name in "ABCD"]
    feasible_data = [(1.0, 0.0), (4.5, 0.0), (4.5, 3.8)] + [
        DMUS[name] for name in "DCBA"
    ]
    feasible = [_point(*value, xmax=xmax, ymax=ymax) for value in feasible_data]
    parts.append(f'<path d="{_path(feasible)} Z" fill="{PALE_TEAL}" opacity="0.72"/>')
    parts.append(
        f'<path d="{_path(frontier)}" fill="none" stroke="{TEAL}" '
        'stroke-width="4" stroke-linejoin="round"/>'
    )

    for label, (x, y) in DMUS.items():
        _dmu(
            parts,
            label,
            x,
            y,
            xmax=xmax,
            ymax=ymax,
            fill=ORANGE if label == "E" else INK,
            radius=7 if label == "E" else 5.5,
        )

    e_px, e_py = _point(*DMUS["E"], xmax=xmax, ymax=ymax)
    input_target = (1.0 + (1.5 - 1.0) / (2.5 - 1.0), 1.5)
    ix, iy = _point(*input_target, xmax=xmax, ymax=ymax)
    ox, oy = _point(2.0, 2.5, xmax=xmax, ymax=ymax)
    parts.extend(
        [
            f'<line x1="{e_px - 7:.2f}" y1="{e_py:.2f}" x2="{ix + 7:.2f}" '
            f'y2="{iy:.2f}" stroke="{TEAL}" stroke-width="3" '
            'marker-end="url(#arrow-teal)"/>',
            f'<line x1="{e_px:.2f}" y1="{e_py - 7:.2f}" x2="{ox:.2f}" '
            f'y2="{oy + 8:.2f}" stroke="{ORANGE}" stroke-width="3" '
            'marker-end="url(#arrow-orange)"/>',
            f'<circle cx="{ix:.2f}" cy="{iy:.2f}" r="7" fill="white" '
            f'stroke="{TEAL}" stroke-width="3"/>',
            f'<text x="{ix - 10:.2f}" y="{iy - 13:.2f}" text-anchor="end" '
            f'font-size="15" fill="{TEAL}">Eₓ</text>',
            f'<text x="{ox + 13:.2f}" y="{oy + 22:.2f}" font-size="15" '
            f'fill="{ORANGE}">Eᵧ (= B)</text>',
            f'<text x="{e_px + 13:.2f}" y="{(e_py + oy) / 2:.2f}" '
            f'font-size="16" fill="{ORANGE}">y ↑</text>',
            f'<text x="{(e_px + ix) / 2:.2f}" y="{e_py + 23:.2f}" '
            f'text-anchor="middle" font-size="16" fill="{TEAL}">x ↓</text>',
            f'<line x1="{512}" y1="{72}" x2="{558}" y2="{72}" '
            f'stroke="{TEAL}" stroke-width="4"/>',
            f'<text x="{568}" y="{78}" font-size="15" fill="{INK}">VRS</text>',
            f'<rect x="{512}" y="{91}" width="46" height="17" '
            f'fill="{PALE_TEAL}" opacity="0.9"/>',
            f'<text x="{568}" y="{105}" font-size="15" fill="{INK}">T</text>',
        ]
    )
    parts.append("</svg>")
    return "\n".join(parts)


def crs_vrs() -> str:
    xmax, ymax = 4.5, 5.8
    parts = _base(
        "CRS and VRS frontiers",
        "A piecewise VRS frontier and a CRS ray through the most productive "
        "scale point B.",
    )
    _axes(parts, xmax=xmax, ymax=ymax)
    frontier = [_point(*DMUS[name], xmax=xmax, ymax=ymax) for name in "ABCD"]
    origin = _point(0.0, 0.0, xmax=xmax, ymax=ymax)
    crs_end = _point(4.45, 4.45 * 1.25, xmax=xmax, ymax=ymax)
    parts.extend(
        [
            f'<path d="{_path(frontier)}" fill="none" stroke="{TEAL}" '
            'stroke-width="4" stroke-linejoin="round"/>',
            f'<line x1="{origin[0]:.2f}" y1="{origin[1]:.2f}" '
            f'x2="{crs_end[0]:.2f}" y2="{crs_end[1]:.2f}" stroke="{PURPLE}" '
            'stroke-width="4" stroke-dasharray="11 7"/>',
        ]
    )
    for label in "ABCD":
        x, y = DMUS[label]
        _dmu(
            parts,
            label,
            x,
            y,
            xmax=xmax,
            ymax=ymax,
            fill=ORANGE if label == "B" else INK,
            radius=7 if label == "B" else 5.5,
        )
    d_px, d_py = _point(*DMUS["D"], xmax=xmax, ymax=ymax)
    target_x = DMUS["D"][1] / 1.25
    t_px, t_py = _point(target_x, DMUS["D"][1], xmax=xmax, ymax=ymax)
    parts.extend(
        [
            f'<line x1="{d_px - 7:.2f}" y1="{d_py:.2f}" x2="{t_px + 8:.2f}" '
            f'y2="{t_py:.2f}" stroke="{PURPLE}" stroke-width="3" '
            'marker-end="url(#arrow-purple)"/>',
            f'<circle cx="{t_px:.2f}" cy="{t_py:.2f}" r="7" fill="white" '
            f'stroke="{PURPLE}" stroke-width="3"/>',
            f'<text x="{t_px - 10:.2f}" y="{t_py - 12:.2f}" text-anchor="end" '
            f'font-size="15" fill="{PURPLE}">D_CRS</text>',
            f'<line x1="{500}" y1="{72}" x2="{548}" y2="{72}" '
            f'stroke="{TEAL}" stroke-width="4"/>',
            f'<text x="{560}" y="{78}" font-size="15" fill="{INK}">VRS</text>',
            f'<line x1="{500}" y1="{101}" x2="{548}" y2="{101}" '
            f'stroke="{PURPLE}" stroke-width="4" stroke-dasharray="11 7"/>',
            f'<text x="{560}" y="{107}" font-size="15" fill="{INK}">CRS</text>',
        ]
    )
    parts.append("</svg>")
    return "\n".join(parts)


def local_rts_operating_response() -> str:
    parts = _base(
        "Local returns to scale as an operating response",
        "Three cards compare how attainable service capacity responds to a "
        "ten percent proportional resource change near a selected efficient "
        "operating plan.",
    )
    parts.extend(
        [
            f'<text x="{WIDTH / 2}" y="48" text-anchor="middle" '
            f'font-size="20" font-weight="700" fill="{INK}">'
            "Near one selected efficient operating plan</text>",
            f'<text x="{WIDTH / 2}" y="76" text-anchor="middle" '
            f'font-size="15" fill="{GRAY}">'
            "Compare a small proportional change in all resources and services"
            "</text>",
        ]
    )

    cards = [
        (
            38,
            "INCREASING RETURNS",
            PALE_TEAL,
            TEAL,
            "+10%",
            "+15%",
            "Service capacity grows",
            "more than resources",
        ),
        (
            270,
            "CONSTANT RETURNS",
            PALE_ORANGE,
            ORANGE,
            "+10%",
            "+10%",
            "Service capacity and",
            "resources grow together",
        ),
        (
            502,
            "DECREASING RETURNS",
            "#eee8f3",
            PURPLE,
            "+10%",
            "+6%",
            "Service capacity grows",
            "less than resources",
        ),
    ]
    for (
        x,
        label,
        fill,
        accent,
        resource_change,
        service_change,
        interpretation_1,
        interpretation_2,
    ) in cards:
        parts.extend(
            [
                f'<rect x="{x}" y="105" width="220" height="290" rx="18" '
                f'fill="{fill}" stroke="{accent}" stroke-width="2"/>',
                f'<text x="{x + 110}" y="137" text-anchor="middle" '
                f'font-size="14" font-weight="700" fill="{accent}">{label}</text>',
                f'<text x="{x + 22}" y="180" font-size="14" '
                f'fill="{GRAY}">Resources</text>',
                f'<rect x="{x + 22}" y="193" width="132" height="22" rx="5" '
                f'fill="{accent}" opacity="0.32"/>',
                f'<text x="{x + 185}" y="211" text-anchor="end" '
                f'font-size="22" font-weight="700" fill="{accent}">'
                f"{resource_change}</text>",
                f'<text x="{x + 22}" y="250" font-size="14" '
                f'fill="{GRAY}">Attainable services</text>',
                f'<rect x="{x + 22}" y="263" width="132" height="22" rx="5" '
                f'fill="{accent}" opacity="0.7"/>',
                f'<text x="{x + 185}" y="281" text-anchor="end" '
                f'font-size="22" font-weight="700" fill="{accent}">'
                f"{service_change}</text>",
                f'<line x1="{x + 22}" y1="309" x2="{x + 198}" y2="309" '
                f'stroke="{accent}" stroke-width="1.5" opacity="0.55"/>',
                f'<text x="{x + 110}" y="340" text-anchor="middle" '
                f'font-size="15" font-weight="600" fill="{INK}">'
                f"{interpretation_1}</text>",
                f'<text x="{x + 110}" y="363" text-anchor="middle" '
                f'font-size="15" font-weight="600" fill="{INK}">'
                f"{interpretation_2}</text>",
            ]
        )

    parts.extend(
        [
            f'<rect x="96" y="424" width="568" height="48" rx="13" '
            f'fill="white" stroke="{GRID}" stroke-width="2"/>',
            f'<text x="{WIDTH / 2}" y="447" text-anchor="middle" '
            f'font-size="14" font-weight="700" fill="{INK}">'
            "The diagnosis belongs to the selected frontier plan</text>",
            f'<text x="{WIDTH / 2}" y="466" text-anchor="middle" '
            f'font-size="13" fill="{GRAY}">'
            "It does not by itself prescribe expansion, contraction, or investment"
            "</text>",
        ]
    )
    parts.append("</svg>")
    return "\n".join(parts)


def directional_scale_priority_scenarios() -> str:
    """Compare scale response under three declared service-growth scenarios."""

    parts = _base(
        "Directional scale response under three service-growth scenarios",
        "For the same efficient research institute and the same one-percent "
        "increase in staff and research expenditure, three declared output "
        "growth compositions imply different scale-up and scale-down "
        "responses. The scenarios come from Ren et al. and are not evidence "
        "that the institute elicited or adopted them.",
    )
    parts.extend(
        [
            f'<text x="{WIDTH / 2}" y="34" text-anchor="middle" '
            f'font-size="20" font-weight="700" fill="{INK}">'
            "The same resources can support different service-growth accounts"
            "</text>",
            f'<text x="{WIDTH / 2}" y="60" text-anchor="middle" '
            f'font-size="14" fill="{GRAY}">'
            "Ren et al. (2021), DMU 2 · selected efficient operating plan"
            "</text>",
            '<rect x="92" y="82" width="576" height="48" rx="14" '
            f'fill="{PALE_TEAL}" stroke="{TEAL}" stroke-width="1.5"/>',
            '<text x="380" y="102" text-anchor="middle" font-size="13" '
            f'font-weight="700" fill="{TEAL}">DECLARED RESOURCE SCENARIO</text>',
            '<text x="380" y="121" text-anchor="middle" font-size="14" '
            f'fill="{INK}">staff +1% · research expenditure +1%</text>',
        ]
    )

    scenarios = [
        (
            28,
            PALE_TEAL,
            TEAL,
            "PATENT-WEIGHTED",
            ("0.75", "0.75", "1.50"),
            (48, 48, 96),
            "1.41",
            "1.46",
        ),
        (
            273,
            PALE_ORANGE,
            ORANGE,
            "BALANCED",
            ("1.00", "1.00", "1.00"),
            (64, 64, 64),
            "1.23",
            "1.25",
        ),
        (
            518,
            "#eee8f3",
            PURPLE,
            "FUNDING + PUBLICATIONS",
            ("1.25", "1.25", "0.50"),
            (80, 80, 32),
            "1.09",
            "1.11",
        ),
    ]
    output_labels = ("External funding", "Publications", "Patents")
    for (
        x,
        fill,
        accent,
        title,
        rates,
        bar_widths,
        scale_up,
        scale_down,
    ) in scenarios:
        parts.extend(
            [
                f'<rect x="{x}" y="150" width="214" height="263" rx="17" '
                f'fill="{fill}" stroke="{accent}" stroke-width="2"/>',
                f'<text x="{x + 107}" y="178" text-anchor="middle" '
                f'font-size="12.5" font-weight="700" fill="{accent}">'
                f"{title}</text>",
                f'<text x="{x + 18}" y="203" font-size="11.5" '
                f'font-weight="700" fill="{INK}">'
                "Relative service-growth rates</text>",
            ]
        )
        for position, (label, rate, bar_width) in enumerate(
            zip(output_labels, rates, bar_widths, strict=True)
        ):
            y = 227 + position * 37
            parts.extend(
                [
                    f'<text x="{x + 18}" y="{y}" font-size="11.5" '
                    f'fill="{GRAY}">{label}</text>',
                    f'<rect x="{x + 18}" y="{y + 7}" width="100" '
                    f'height="10" rx="5" fill="white" opacity="0.8"/>',
                    f'<rect x="{x + 18}" y="{y + 7}" width="{bar_width}" '
                    f'height="10" rx="5" fill="{accent}" opacity="0.78"/>',
                    f'<text x="{x + 191}" y="{y + 16}" text-anchor="end" '
                    f'font-size="12" font-weight="700" fill="{accent}">'
                    f"{rate}</text>",
                ]
            )
        parts.extend(
            [
                f'<line x1="{x + 18}" y1="342" x2="{x + 196}" y2="342" '
                f'stroke="{accent}" stroke-width="1.5" opacity="0.55"/>',
                f'<text x="{x + 18}" y="367" font-size="12.5" '
                f'font-weight="700" fill="{INK}">Scale up</text>',
                f'<text x="{x + 191}" y="369" text-anchor="end" '
                f'font-size="20" font-weight="700" fill="{accent}">'
                f"{scale_up}</text>",
                f'<text x="{x + 18}" y="397" font-size="12.5" '
                f'font-weight="700" fill="{INK}">Scale down</text>',
                f'<text x="{x + 191}" y="399" text-anchor="end" '
                f'font-size="20" font-weight="700" fill="{accent}">'
                f"{scale_down}</text>",
            ]
        )

    parts.extend(
        [
            f'<rect x="58" y="434" width="644" height="49" rx="13" fill="{INK}"/>',
            '<text x="380" y="455" text-anchor="middle" font-size="13" '
            'font-weight="700" fill="white">'
            "DIRECTION PROVENANCE IS PART OF THE RESULT</text>",
            '<text x="380" y="474" text-anchor="middle" font-size="12" '
            'fill="#d7e2e5">'
            "These are paper-defined scenarios—not evidence of elicited "
            "institutional preferences.</text>",
        ]
    )
    parts.append("</svg>")
    return "\n".join(parts)


def mpss_productivity_profile() -> str:
    """Show MPSS as a management-facing average-productivity profile."""

    chart_left = 96.0
    chart_right = 712.0
    chart_top = 68.0
    chart_bottom = 404.0
    xmax = 5.5
    ymax = 2.2

    def point(x: float, average_productivity: float) -> tuple[float, float]:
        px = chart_left + (chart_right - chart_left) * x / xmax
        py = chart_bottom - ((chart_bottom - chart_top) * average_productivity / ymax)
        return px, py

    parts = _base(
        "Most productive scale size as an average-productivity profile",
        "The best attainable services per resource bundle rise to a maximum "
        "at B, remain at that maximum through C, and then decline. Q operates "
        "within the B to C scale band but below the best attainable result at "
        "the same resource scale.",
    )
    parts.extend(
        [
            f'<text x="{WIDTH / 2}" y="30" text-anchor="middle" '
            f'font-size="20" font-weight="700" fill="{INK}">'
            "Best attainable average productivity by operating scale</text>",
            f'<line x1="{chart_left}" y1="{chart_bottom}" '
            f'x2="{chart_right}" y2="{chart_bottom}" stroke="{INK}" '
            'stroke-width="2"/>',
            f'<line x1="{chart_left}" y1="{chart_bottom}" '
            f'x2="{chart_left}" y2="{chart_top}" stroke="{INK}" '
            'stroke-width="2"/>',
        ]
    )

    for x in range(1, 6):
        px, _ = point(float(x), 0.0)
        parts.extend(
            [
                f'<line x1="{px:.2f}" y1="{chart_top}" x2="{px:.2f}" '
                f'y2="{chart_bottom}" stroke="{GRID}" stroke-width="1"/>',
                f'<text x="{px:.2f}" y="{chart_bottom + 23}" '
                'text-anchor="middle" font-size="13.5" '
                f'fill="{GRAY}">{x}</text>',
            ]
        )
    for value, label in (
        (0.0, "0"),
        (0.5, "0.5"),
        (1.0, "1.0"),
        (1.5, "1.5"),
        (2.0, "2.0"),
    ):
        _, py = point(0.0, value)
        parts.extend(
            [
                f'<line x1="{chart_left}" y1="{py:.2f}" '
                f'x2="{chart_right}" y2="{py:.2f}" stroke="{GRID}" '
                'stroke-width="1"/>',
                f'<text x="{chart_left - 14}" y="{py + 5:.2f}" '
                'text-anchor="end" font-size="13.5" '
                f'fill="{GRAY}">{label}</text>',
            ]
        )

    band_left, _ = point(2.0, 0.0)
    band_right, _ = point(4.0, 0.0)
    parts.extend(
        [
            f'<rect x="{band_left:.2f}" y="{chart_top}" '
            f'width="{band_right - band_left:.2f}" '
            f'height="{chart_bottom - chart_top:.2f}" fill="{PALE_TEAL}" '
            'opacity="0.58"/>',
            f'<text x="{(band_left + band_right) / 2:.2f}" y="58" '
            'text-anchor="middle" font-size="14" font-weight="700" '
            f'fill="{TEAL}">MPSS SCALE BAND: B&#8211;C</text>',
        ]
    )

    profile_values = [
        (1.0, 1.5),
        (1.25, 1.7),
        (1.5, 11.0 / 6.0),
        (1.75, 27.0 / 14.0),
        (2.0, 2.0),
        (3.0, 2.0),
        (4.0, 2.0),
        (4.25, 33.0 / 17.0),
        (4.5, 17.0 / 9.0),
        (4.75, 35.0 / 19.0),
        (5.0, 1.8),
    ]
    profile = [point(x, productivity) for x, productivity in profile_values]
    parts.append(
        f'<path d="{_path(profile)}" fill="none" stroke="{TEAL}" '
        'stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>'
    )

    observations = {
        "A": (1.0, 1.5),
        "B": (2.0, 2.0),
        "C": (4.0, 2.0),
        "D": (5.0, 1.8),
    }
    for label, (x, productivity) in observations.items():
        px, py = point(x, productivity)
        label_dy = 25 if label in {"B", "C"} else -11
        parts.extend(
            [
                f'<circle cx="{px:.2f}" cy="{py:.2f}" r="6.5" '
                f'fill="{INK}" stroke="white" stroke-width="2"/>',
                f'<text x="{px + 10:.2f}" y="{py + label_dy:.2f}" '
                f'font-size="15" font-weight="700" fill="{INK}">{label}</text>',
            ]
        )

    qx, qy = point(3.0, 5.0 / 3.0)
    benchmark_x, benchmark_y = point(3.0, 2.0)
    bracket_x = qx + 16.0
    parts.extend(
        [
            f'<circle cx="{qx:.2f}" cy="{qy:.2f}" r="8" fill="{ORANGE}" '
            'stroke="white" stroke-width="2"/>',
            f'<text x="{qx - 11:.2f}" y="{qy + 25:.2f}" text-anchor="end" '
            f'font-size="15" font-weight="700" fill="{ORANGE}">Q: 5 ÷ 3</text>',
            f'<circle cx="{benchmark_x:.2f}" cy="{benchmark_y:.2f}" r="7" '
            f'fill="white" stroke="{TEAL}" stroke-width="3"/>',
            f'<line x1="{bracket_x:.2f}" y1="{benchmark_y:.2f}" '
            f'x2="{bracket_x:.2f}" y2="{qy:.2f}" stroke="{ORANGE}" '
            'stroke-width="2.5"/>',
            f'<line x1="{bracket_x - 7:.2f}" y1="{benchmark_y:.2f}" '
            f'x2="{bracket_x + 7:.2f}" y2="{benchmark_y:.2f}" '
            f'stroke="{ORANGE}" stroke-width="2.5"/>',
            f'<line x1="{bracket_x - 7:.2f}" y1="{qy:.2f}" '
            f'x2="{bracket_x + 7:.2f}" y2="{qy:.2f}" stroke="{ORANGE}" '
            'stroke-width="2.5"/>',
            f'<text x="{bracket_x + 13:.2f}" '
            f'y="{(benchmark_y + qy) / 2 - 3:.2f}" font-size="13.5" '
            f'font-weight="700" fill="{ORANGE}">same-size</text>',
            f'<text x="{bracket_x + 13:.2f}" '
            f'y="{(benchmark_y + qy) / 2 + 15:.2f}" font-size="13.5" '
            f'font-weight="700" fill="{ORANGE}">operating gap</text>',
            f'<text x="{(chart_left + chart_right) / 2:.2f}" y="474" '
            'text-anchor="middle" font-size="14" font-weight="700" '
            f'fill="{INK}">Operating scale (resource bundles)</text>',
            '<text x="25" y="238" text-anchor="middle" font-size="13.5" '
            f'font-weight="700" fill="{INK}" '
            'transform="rotate(-90 25 238)">'
            "Services per resource bundle</text>",
        ]
    )
    parts.append("</svg>")
    return "\n".join(parts)


def physical_capacity_account() -> str:
    """Separate operating performance from short-run capacity use."""

    parts = _base(
        "Clinic A short-run physical-capacity account",
        "Three nested service bars distinguish observed visits, the output "
        "attainable under all current input limits, and physical capacity "
        "supported by installed beds when staffing may adjust.",
    )
    parts.extend(
        [
            f'<text x="{WIDTH / 2}" y="34" text-anchor="middle" '
            f'font-size="20" font-weight="700" fill="{INK}">'
            "Clinic A: what explains the service headroom?</text>",
            f'<text x="{WIDTH / 2}" y="60" text-anchor="middle" '
            f'font-size="14" fill="{GRAY}">'
            "One short-run production account · observed visit mix preserved"
            "</text>",
            '<rect x="62" y="82" width="184" height="34" rx="17" '
            f'fill="{PALE_TEAL}" stroke="{TEAL}"/>',
            '<text x="154" y="104" text-anchor="middle" font-size="13" '
            f'font-weight="700" fill="{TEAL}">FIXED · 10 BEDS</text>',
            '<rect x="264" y="82" width="232" height="34" rx="17" '
            f'fill="{PALE_ORANGE}" stroke="{ORANGE}"/>',
            '<text x="380" y="104" text-anchor="middle" font-size="13" '
            f'font-weight="700" fill="{ORANGE}">'
            "MAY ADJUST · STAFF HOURS</text>",
            '<rect x="514" y="82" width="184" height="34" rx="17" '
            'fill="#eee8f3" stroke="#76528f"/>',
            '<text x="606" y="104" text-anchor="middle" font-size="13" '
            'font-weight="700" fill="#76528f">SERVICE · VISITS</text>',
        ]
    )

    labels = [
        (
            146,
            "Observed service",
            "what the clinic delivered",
            240,
            ORANGE,
            "100",
        ),
        (
            238,
            "Current-input potential",
            "better use of beds and current staff hours",
            360,
            TEAL,
            "150",
        ),
        (
            330,
            "Physical capacity",
            "installed beds, with staff hours allowed to adjust",
            480,
            PURPLE,
            "200",
        ),
    ]
    for y, label, explanation, width, color, value in labels:
        parts.extend(
            [
                f'<text x="62" y="{y}" font-size="15" font-weight="700" '
                f'fill="{INK}">{label}</text>',
                f'<text x="62" y="{y + 19}" font-size="11.5" '
                f'fill="{GRAY}">{explanation}</text>',
                f'<rect x="250" y="{y - 17}" width="480" height="31" rx="7" '
                f'fill="{GRID}" opacity="0.58"/>',
                f'<rect x="250" y="{y - 17}" width="{width}" height="31" '
                f'rx="7" fill="{color}" opacity="0.88"/>',
                f'<text x="{250 + width - 13}" y="{y + 5}" '
                'text-anchor="end" font-size="17" font-weight="700" '
                f'fill="white">{value}</text>',
            ]
        )

    parts.extend(
        [
            '<path d="M 490 166 L 490 181 L 610 181 L 610 166" '
            f'fill="none" stroke="{TEAL}" stroke-width="2"/>',
            '<text x="550" y="198" text-anchor="middle" font-size="11.5" '
            f'font-weight="700" fill="{TEAL}">50 visits · operating</text>',
            '<text x="550" y="213" text-anchor="middle" font-size="11.5" '
            f'font-weight="700" fill="{TEAL}">performance headroom</text>',
            '<path d="M 610 258 L 610 273 L 730 273 L 730 258" '
            f'fill="none" stroke="{PURPLE}" stroke-width="2"/>',
            '<text x="670" y="290" text-anchor="middle" font-size="11.5" '
            f'font-weight="700" fill="{PURPLE}">50 visits · additional '
            "use</text>",
            '<text x="670" y="305" text-anchor="middle" font-size="11.5" '
            f'font-weight="700" fill="{PURPLE}">of installed beds</text>',
            '<rect x="58" y="365" width="644" height="65" rx="14" '
            'fill="#f7fafb" stroke="#c8d8db" stroke-width="1.5"/>',
            '<text x="380" y="388" text-anchor="middle" font-size="13" '
            f'font-weight="700" fill="{INK}">ONE AUDITABLE IDENTITY</text>',
            '<text x="380" y="416" text-anchor="middle" font-size="17" '
            f'font-weight="700" fill="{INK}">'
            "Observed utilization 50% = technical efficiency 66.7% &#215; "
            "adjusted utilization 75%</text>",
            f'<rect x="101" y="449" width="558" height="31" rx="15" fill="{INK}"/>',
            '<text x="380" y="470" text-anchor="middle" font-size="12.5" '
            'font-weight="700" fill="white">'
            "Technical benchmark · not a demand, staffing, or investment plan"
            "</text>",
        ]
    )
    parts.append("</svg>")
    return "\n".join(parts)


def convex_combination() -> str:
    xmax, ymax = 4.5, 4.2
    parts = _base(
        "A virtual DMU formed by convex combination",
        "Observed activities A and D connected by a segment with virtual "
        "activity M at their midpoint.",
    )
    _axes(parts, xmax=xmax, ymax=ymax)
    a = DMUS["A"]
    d = DMUS["D"]
    m = ((a[0] + d[0]) / 2, (a[1] + d[1]) / 2)
    a_px = _point(*a, xmax=xmax, ymax=ymax)
    d_px = _point(*d, xmax=xmax, ymax=ymax)
    m_px = _point(*m, xmax=xmax, ymax=ymax)
    parts.extend(
        [
            f'<line x1="{a_px[0]:.2f}" y1="{a_px[1]:.2f}" '
            f'x2="{d_px[0]:.2f}" y2="{d_px[1]:.2f}" stroke="{TEAL}" '
            'stroke-width="4"/>',
            f'<line x1="{m_px[0]:.2f}" y1="{m_px[1]:.2f}" '
            f'x2="{m_px[0]:.2f}" y2="{BOTTOM:.2f}" stroke="{GRAY}" '
            'stroke-width="1.5" stroke-dasharray="5 5"/>',
            f'<line x1="{LEFT:.2f}" y1="{m_px[1]:.2f}" '
            f'x2="{m_px[0]:.2f}" y2="{m_px[1]:.2f}" stroke="{GRAY}" '
            'stroke-width="1.5" stroke-dasharray="5 5"/>',
        ]
    )
    _dmu(parts, "A", *a, xmax=xmax, ymax=ymax, fill=INK, radius=7)
    _dmu(parts, "D", *d, xmax=xmax, ymax=ymax, fill=INK, radius=7)
    _dmu(
        parts,
        "M",
        *m,
        xmax=xmax,
        ymax=ymax,
        fill=ORANGE,
        radius=9,
        dx=12,
        dy=-12,
    )
    parts.extend(
        [
            f'<rect x="{390}" y="{72}" width="260" height="48" rx="8" '
            f'fill="{PALE_ORANGE}"/>',
            f'<text x="{520}" y="{102}" text-anchor="middle" font-size="18" '
            f'fill="{INK}">M = 0.5 A + 0.5 D</text>',
            f'<text x="{m_px[0]:.2f}" y="{BOTTOM + 25}" text-anchor="middle" '
            f'font-size="14" fill="{ORANGE}">2.5</text>',
            f'<text x="{LEFT - 18}" y="{m_px[1] + 5:.2f}" text-anchor="end" '
            f'font-size="14" fill="{ORANGE}">2.4</text>',
        ]
    )
    parts.append("</svg>")
    return "\n".join(parts)


def fdh_vs_convex() -> str:
    xmax, ymax = 4.5, 4.2
    parts = _base(
        "Observed-practice and synthetic-mixture benchmarks",
        "The non-convex FDH benchmark follows observed-practice steps while "
        "the convex VRS benchmark admits interpolated operations. For unit Q, "
        "the FDH output target is lower than the convex target.",
    )
    _axes(parts, xmax=xmax, ymax=ymax)

    frontier_data = [DMUS[name] for name in "ABCD"]
    convex_frontier = [_point(*value, xmax=xmax, ymax=ymax) for value in frontier_data]
    fdh_data = [
        DMUS["A"],
        (DMUS["B"][0], DMUS["A"][1]),
        DMUS["B"],
        (DMUS["C"][0], DMUS["B"][1]),
        DMUS["C"],
        (DMUS["D"][0], DMUS["C"][1]),
        DMUS["D"],
        (xmax, DMUS["D"][1]),
    ]
    fdh_frontier = [_point(*value, xmax=xmax, ymax=ymax) for value in fdh_data]
    q = (2.5, 2.0)
    fdh_target = (q[0], DMUS["B"][1])
    convex_target_y = DMUS["B"][1] + 0.5 * (DMUS["C"][1] - DMUS["B"][1])
    convex_target = (q[0], convex_target_y)
    q_px = _point(*q, xmax=xmax, ymax=ymax)
    fdh_px = _point(*fdh_target, xmax=xmax, ymax=ymax)
    convex_px = _point(*convex_target, xmax=xmax, ymax=ymax)

    parts.extend(
        [
            f'<path d="{_path(convex_frontier)}" fill="none" stroke="{TEAL}" '
            'stroke-width="4" stroke-linejoin="round"/>',
            f'<path d="{_path(fdh_frontier)}" fill="none" stroke="{PURPLE}" '
            'stroke-width="4" stroke-linejoin="miter" stroke-dasharray="10 6"/>',
            f'<line x1="{q_px[0]:.2f}" y1="{q_px[1] - 7:.2f}" '
            f'x2="{fdh_px[0]:.2f}" y2="{fdh_px[1] + 8:.2f}" '
            f'stroke="{PURPLE}" stroke-width="3" '
            'marker-end="url(#arrow-purple)"/>',
            f'<line x1="{fdh_px[0] + 5:.2f}" y1="{fdh_px[1] - 3:.2f}" '
            f'x2="{convex_px[0] + 5:.2f}" y2="{convex_px[1] + 8:.2f}" '
            f'stroke="{TEAL}" stroke-width="3" '
            'marker-end="url(#arrow-teal)"/>',
            f'<circle cx="{fdh_px[0]:.2f}" cy="{fdh_px[1]:.2f}" r="7" '
            f'fill="white" stroke="{PURPLE}" stroke-width="3"/>',
            f'<circle cx="{convex_px[0]:.2f}" cy="{convex_px[1]:.2f}" r="7" '
            f'fill="white" stroke="{TEAL}" stroke-width="3"/>',
            f'<text x="{fdh_px[0] + 14:.2f}" y="{fdh_px[1] + 28:.2f}" '
            f'font-size="15" fill="{PURPLE}">FDH target</text>',
            f'<text x="{convex_px[0] + 14:.2f}" y="{convex_px[1] - 20:.2f}" '
            f'font-size="15" fill="{TEAL}">convex target</text>',
        ]
    )
    for label in "ABCD":
        _dmu(
            parts,
            label,
            *DMUS[label],
            xmax=xmax,
            ymax=ymax,
            fill=INK,
            radius=6.5,
        )
    _dmu(
        parts,
        "Q",
        *q,
        xmax=xmax,
        ymax=ymax,
        fill=ORANGE,
        radius=8,
        dx=12,
        dy=22,
    )
    parts.extend(
        [
            f'<line x1="{480}" y1="{72}" x2="{530}" y2="{72}" '
            f'stroke="{TEAL}" stroke-width="4"/>',
            f'<text x="{542}" y="{78}" font-size="15" fill="{INK}">convex VRS</text>',
            f'<line x1="{480}" y1="{101}" x2="{530}" y2="{101}" '
            f'stroke="{PURPLE}" stroke-width="4" stroke-dasharray="10 6"/>',
            f'<text x="{542}" y="{107}" font-size="15" fill="{INK}">FDH</text>',
        ]
    )
    parts.append("</svg>")
    return "\n".join(parts)


def fdh_frh_crs_replication() -> str:
    """Compare the operating evidence admitted by FDH, FRH, and CRS DEA."""
    parts = _base(
        "From observed units to whole-module replication and divisible activity",
        "The same observed branch templates support one observed unit under "
        "FDH, whole-number copies and combinations under FRH, and fractional "
        "activity shares under continuously divisible CRS DEA.",
    )

    def module(
        x: float,
        y: float,
        label: str,
        color: str,
        *,
        fraction: float = 1.0,
    ) -> None:
        width = 44.0
        height = 52.0
        inner_width = (width - 4) * fraction
        parts.extend(
            [
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" '
                f'height="{height:.1f}" rx="7" fill="white" '
                f'stroke="{color}" stroke-width="2"/>',
                f'<rect x="{x + 2:.1f}" y="{y + 2:.1f}" '
                f'width="{inner_width:.1f}" height="{height - 4:.1f}" '
                f'rx="5" fill="{color}" opacity="0.18"/>',
            ]
        )
        if fraction < 1.0:
            boundary = x + 2 + inner_width
            parts.append(
                f'<line x1="{boundary:.1f}" y1="{y + 5:.1f}" '
                f'x2="{boundary:.1f}" y2="{y + height - 5:.1f}" '
                f'stroke="{color}" stroke-width="1.5" '
                'stroke-dasharray="3 3"/>'
            )
        parts.extend(
            [
                f'<text x="{x + width / 2:.1f}" y="{y + 25:.1f}" '
                'text-anchor="middle" font-size="15" font-weight="700" '
                f'fill="{INK}">{label}</text>',
                f'<circle cx="{x + 12:.1f}" cy="{y + 39:.1f}" r="2.6" fill="{color}"/>',
                f'<circle cx="{x + 22:.1f}" cy="{y + 39:.1f}" r="2.6" fill="{color}"/>',
                f'<circle cx="{x + 32:.1f}" cy="{y + 39:.1f}" r="2.6" fill="{color}"/>',
            ]
        )

    parts.extend(
        [
            '<text x="380" y="27" text-anchor="middle" font-size="15" '
            f'font-weight="700" fill="{INK}">'
            "THE SAME OBSERVATIONS, THREE OPERATING-EVIDENCE RULES</text>",
            '<text x="380" y="49" text-anchor="middle" font-size="12.5" '
            f'fill="{GRAY}">Observed templates A and B represent complete '
            "branch operations</text>",
        ]
    )

    cards = [
        (28, PURPLE, "#f5f0f8", "FDH", "one observed unit"),
        (270, TEAL, "#edf7f6", "FRH", "whole-number modules"),
        (512, BLUE, "#eef5fb", "CRS DEA", "divisible activity"),
    ]
    for x, color, pale, title, subtitle in cards:
        parts.extend(
            [
                f'<rect x="{x}" y="67" width="220" height="329" rx="15" '
                f'fill="{pale}" stroke="{color}" stroke-width="1.8"/>',
                f'<rect x="{x}" y="67" width="220" height="67" rx="15" '
                f'fill="{color}"/>',
                f'<rect x="{x}" y="117" width="220" height="17" fill="{color}"/>',
                f'<text x="{x + 110}" y="96" text-anchor="middle" '
                'font-size="20" font-weight="700" fill="white">'
                f"{title}</text>",
                f'<text x="{x + 110}" y="119" text-anchor="middle" '
                'font-size="12.5" fill="white">'
                f"{subtitle}</text>",
                f'<text x="{x + 110}" y="157" text-anchor="middle" '
                'font-size="11.5" font-weight="700" '
                f'fill="{color}">ADMISSIBLE BENCHMARK</text>',
            ]
        )

    module(67, 174, "A", ORANGE)
    parts.append(
        f'<text x="138" y="206" text-anchor="middle" font-size="12" '
        f'font-weight="700" fill="{GRAY}">OR</text>'
    )
    module(165, 174, "B", TEAL)

    module(286, 174, "A", ORANGE)
    parts.append(
        f'<text x="342" y="206" text-anchor="middle" font-size="16" '
        f'font-weight="700" fill="{GRAY}">+</text>'
    )
    module(354, 174, "B", TEAL)
    parts.append(
        f'<text x="410" y="206" text-anchor="middle" font-size="16" '
        f'font-weight="700" fill="{GRAY}">+</text>'
    )
    module(422, 174, "B", TEAL)

    module(526, 174, "A", ORANGE, fraction=0.4)
    parts.append(
        f'<text x="582" y="206" text-anchor="middle" font-size="16" '
        f'font-weight="700" fill="{GRAY}">+</text>'
    )
    module(594, 174, "B", TEAL)
    module(662, 174, "B", TEAL, fraction=0.5)

    descriptions = [
        (
            138,
            PURPLE,
            "A or B",
            "one observed organization",
            "No aggregation beyond",
            "an observed practice",
            "SINGLE OBSERVATION",
        ),
        (
            380,
            TEAL,
            "A + 2B",
            "complete modules combine",
            "Complete branch templates",
            "can be copied",
            "INTEGER COUNTS",
        ),
        (
            622,
            BLUE,
            "0.4A + 1.5B",
            "fractional shares admitted",
            "Activity is continuously",
            "divisible and scalable",
            "REAL INTENSITIES",
        ),
    ]
    for center, color, formula, explanation, line_one, line_two, tag in descriptions:
        parts.extend(
            [
                f'<text x="{center}" y="250" text-anchor="middle" '
                f'font-size="16" font-weight="700" fill="{color}">'
                f"{formula}</text>",
                f'<text x="{center}" y="270" text-anchor="middle" '
                f'font-size="11.5" fill="{GRAY}">{explanation}</text>',
                f'<line x1="{center - 84}" y1="288" x2="{center + 84}" '
                f'y2="288" stroke="{color}" stroke-width="1" opacity="0.35"/>',
                f'<text x="{center}" y="312" text-anchor="middle" '
                f'font-size="12.5" font-weight="700" fill="{INK}">'
                "WHAT THIS ASSUMES</text>",
                f'<text x="{center}" y="335" text-anchor="middle" '
                f'font-size="12.5" fill="{INK}">{line_one}</text>',
                f'<text x="{center}" y="353" text-anchor="middle" '
                f'font-size="12.5" fill="{INK}">{line_two}</text>',
                f'<rect x="{center - 77}" y="367" width="154" height="20" '
                f'rx="10" fill="{color}"/>',
                f'<text x="{center}" y="381" text-anchor="middle" '
                'font-size="10.5" font-weight="700" fill="white">'
                f"{tag}</text>",
            ]
        )

    parts.extend(
        [
            '<rect x="65" y="410" width="630" height="51" rx="13" '
            'fill="#f7fafb" stroke="#c8d8db" stroke-width="1.5"/>',
            '<text x="183" y="431" text-anchor="middle" font-size="11.5" '
            f'font-weight="700" fill="{GRAY}">MATCHED DATA AND DISPOSAL</text>',
            '<text x="449" y="439" text-anchor="middle" font-size="19" '
            f'font-weight="700" fill="{INK}">'
            '<tspan font-style="italic">T</tspan>'
            '<tspan baseline-shift="sub" font-size="12">FDH</tspan>'
            '<tspan baseline-shift="baseline" font-size="19">  ⊆  </tspan>'
            '<tspan font-style="italic">T</tspan>'
            '<tspan baseline-shift="sub" font-size="12">FRH</tspan>'
            '<tspan baseline-shift="baseline" font-size="19">  ⊆  </tspan>'
            '<tspan font-style="italic">T</tspan>'
            '<tspan baseline-shift="sub" font-size="12">CRS</tspan></text>',
            '<text x="625" y="431" text-anchor="middle" font-size="11.5" '
            f'font-weight="700" fill="{TEAL}">MORE BENCHMARK</text>',
            '<text x="625" y="448" text-anchor="middle" font-size="11.5" '
            f'font-weight="700" fill="{TEAL}">PLANS ADMITTED</text>',
            f'<rect x="42" y="474" width="676" height="26" rx="13" fill="{INK}"/>',
            '<text x="380" y="492" text-anchor="middle" font-size="11.5" '
            'font-weight="700" fill="white">'
            "Replicability is an evidence assumption, not a branch-opening "
            "instruction</text>",
        ]
    )
    parts.append("</svg>")
    return "\n".join(parts)


def fch_coordination_hulls() -> str:
    """Distinguish FDH, FCH, FRH, CCR, and VRS operating rights."""

    parts = _base(
        "Five radial benchmarks from one set of operating observations",
        "For organization E, FDH permits one observed template, FCH permits a "
        "subset of distinct templates, FRH permits repeated whole templates, "
        "CCR permits fractional scalable activity, and VRS permits one convex "
        "average. FCH and VRS are not generally nested.",
    )
    parts.extend(
        [
            '<text x="380" y="27" text-anchor="middle" font-size="16" '
            f'font-weight="700" fill="{INK}">'
            "What may the benchmark combine?</text>",
            '<text x="380" y="49" text-anchor="middle" font-size="12.5" '
            f'fill="{GRAY}">Same observations · organization E = '
            "(resource 10, service 10)</text>",
        ]
    )

    cards = [
        (
            18,
            PURPLE,
            "#f5f0f8",
            "FDH",
            "ONE TEMPLATE",
            "input: E",
            "output: E",
            "θ = 1.00",
            "1/φ = 1.00",
        ),
        (
            201,
            TEAL,
            "#edf7f6",
            "FCH",
            "DISTINCT SUBSET",
            "input: A + B",
            "output: A + B",
            "θ = 0.70",
            "1/φ = 0.909",
        ),
        (
            384,
            ORANGE,
            "#fff4ec",
            "FRH",
            "WHOLE REPEATS",
            "input: 2A",
            "output: 3A",
            "θ = 0.60",
            "1/φ = 0.556",
        ),
        (
            567,
            BLUE,
            "#eef5fb",
            "CCR",
            "FRACTIONAL SCALE",
            "input: 5/3 A",
            "output: 10/3 A",
            "θ = 0.50",
            "1/φ = 0.50",
        ),
    ]
    for (
        x,
        color,
        pale,
        title,
        rule,
        input_plan,
        output_plan,
        input_score,
        output_score,
    ) in cards:
        parts.extend(
            [
                f'<rect x="{x}" y="67" width="175" height="226" rx="14" '
                f'fill="{pale}" stroke="{color}" stroke-width="1.7"/>',
                f'<rect x="{x}" y="67" width="175" height="48" rx="14" '
                f'fill="{color}"/>',
                f'<rect x="{x}" y="99" width="175" height="16" fill="{color}"/>',
                f'<text x="{x + 87.5}" y="98" text-anchor="middle" '
                'font-size="20" font-weight="700" fill="white">'
                f"{title}</text>",
                f'<text x="{x + 87.5}" y="139" text-anchor="middle" '
                f'font-size="10.5" font-weight="700" fill="{color}">{rule}</text>',
                f'<text x="{x + 18}" y="171" font-size="12" fill="{INK}">'
                f"{input_plan}</text>",
                f'<text x="{x + 18}" y="194" font-size="12" fill="{INK}">'
                f"{output_plan}</text>",
                f'<line x1="{x + 18}" y1="211" x2="{x + 157}" y2="211" '
                f'stroke="{color}" stroke-width="1" opacity="0.42"/>',
                f'<text x="{x + 87.5}" y="239" text-anchor="middle" '
                f'font-size="17" font-weight="700" fill="{color}">{input_score}</text>',
                f'<text x="{x + 87.5}" y="266" text-anchor="middle" '
                f'font-size="17" font-weight="700" fill="{color}">'
                f"{output_score}</text>",
            ]
        )

    parts.extend(
        [
            '<text x="380" y="322" text-anchor="middle" font-size="17" '
            f'font-weight="700" fill="{INK}">'
            "FDH  ⊂  FCH  ⊂  FRH  ⊂  CCR</text>",
            '<text x="380" y="341" text-anchor="middle" font-size="11.5" '
            f'fill="{GRAY}">Matched data and ordinary free disposal</text>',
            '<rect x="46" y="357" width="668" height="88" rx="14" '
            'fill="#f7fafb" stroke="#9eb4ba" stroke-width="1.5"/>',
            f'<rect x="62" y="372" width="96" height="57" rx="10" fill="{INK}"/>',
            '<text x="110" y="397" text-anchor="middle" font-size="19" '
            'font-weight="700" fill="white">VRS</text>',
            '<text x="110" y="416" text-anchor="middle" font-size="10.5" '
            'fill="#d7e2e5">one convex average</text>',
            '<text x="181" y="383" font-size="11.5" '
            f'font-weight="700" fill="{GRAY}">NO GENERAL NESTING WITH FCH</text>',
            '<text x="181" y="407" font-size="13" '
            f'fill="{INK}">VRS: θ = 0.75 · 1/φ = 0.818</text>',
            '<text x="181" y="429" font-size="12.5" '
            f'fill="{INK}">FCH is stricter for input saving here; '
            "VRS is stricter for output expansion.</text>",
            f'<rect x="66" y="461" width="628" height="27" rx="13" fill="{INK}"/>',
            '<text x="380" y="479" text-anchor="middle" font-size="11.5" '
            'font-weight="700" fill="white">'
            "These are different operating rights, not solver tuning parameters"
            "</text>",
        ]
    )
    parts.append("</svg>")
    return "\n".join(parts)


def radial_and_slack() -> str:
    xmax, ymax = 5.0, 5.0
    parts = _base(
        "A common resource reduction and a remaining input excess",
        "A common input reduction takes O to R before removing a "
        "variable-specific input excess reaches S.",
    )
    _axes(parts, xmax=xmax, ymax=ymax, xlabel="x₁", ylabel="x₂")
    frontier_data = [
        (1.0, 4.2),
        (1.4, 3.2),
        (1.7, 2.5),
        (2.5, 2.5),
        (3.1, 1.7),
        (4.4, 1.2),
    ]
    frontier = [_point(*value, xmax=xmax, ymax=ymax) for value in frontier_data]
    feasible_data = [
        (1.0, 5.0),
        (5.0, 5.0),
        (5.0, 1.2),
        *reversed(frontier_data),
    ]
    feasible = [_point(*value, xmax=xmax, ymax=ymax) for value in feasible_data]
    parts.extend(
        [
            f'<path d="{_path(feasible)} Z" fill="{PALE_TEAL}" opacity="0.72"/>',
            f'<path d="{_path(frontier)}" fill="none" stroke="{TEAL}" '
            'stroke-width="4" stroke-linejoin="round"/>',
        ]
    )
    origin = _point(0.0, 0.0, xmax=xmax, ymax=ymax)
    observed = (4.0, 4.0)
    radial = (2.5, 2.5)
    strong = (1.7, 2.5)
    o_px = _point(*observed, xmax=xmax, ymax=ymax)
    r_px = _point(*radial, xmax=xmax, ymax=ymax)
    s_px = _point(*strong, xmax=xmax, ymax=ymax)
    parts.extend(
        [
            f'<line x1="{origin[0]:.2f}" y1="{origin[1]:.2f}" '
            f'x2="{o_px[0]:.2f}" y2="{o_px[1]:.2f}" stroke="{GRAY}" '
            'stroke-width="1.5" stroke-dasharray="6 6"/>',
            f'<line x1="{o_px[0] - 7:.2f}" y1="{o_px[1] + 7:.2f}" '
            f'x2="{r_px[0] + 8:.2f}" y2="{r_px[1] - 8:.2f}" '
            f'stroke="{ORANGE}" stroke-width="3" '
            'marker-end="url(#arrow-orange)"/>',
            f'<line x1="{r_px[0] - 7:.2f}" y1="{r_px[1]:.2f}" '
            f'x2="{s_px[0] + 8:.2f}" y2="{s_px[1]:.2f}" '
            f'stroke="{PURPLE}" stroke-width="3" '
            'marker-end="url(#arrow-purple)"/>',
        ]
    )
    _dmu(parts, "O", *observed, xmax=xmax, ymax=ymax, fill=INK, radius=7)
    _dmu(parts, "R", *radial, xmax=xmax, ymax=ymax, fill=ORANGE, radius=8)
    _dmu(parts, "S", *strong, xmax=xmax, ymax=ymax, fill=PURPLE, radius=8)
    parts.extend(
        [
            f'<text x="{(o_px[0] + r_px[0]) / 2 + 14:.2f}" '
            f'y="{(o_px[1] + r_px[1]) / 2 - 11:.2f}" font-size="16" '
            f'fill="{ORANGE}">θx</text>',
            f'<text x="{(r_px[0] + s_px[0]) / 2:.2f}" '
            f'y="{r_px[1] + 24:.2f}" text-anchor="middle" font-size="16" '
            f'fill="{PURPLE}">s₁⁻</text>',
            f'<text x="{RIGHT - 100}" y="{TOP + 25}" font-size="15" '
            f'fill="{INK}">y = yₒ</text>',
        ]
    )
    parts.append("</svg>")
    return "\n".join(parts)


def sbm_relative_slacks() -> str:
    parts = _base(
        "Absolute and relative input slacks",
        "Two normalized bars show the same absolute input slack of ten as "
        "fifty percent for a small DMU and one percent for a large DMU.",
    )
    bar_x = 175
    bar_width = 470
    bar_height = 44
    rows = [
        ("DMU S", 150, 0.50, "x = 20", "s⁻ = 10", "s⁻ / x = 50%"),
        ("DMU L", 315, 0.01, "x = 1000", "s⁻ = 10", "s⁻ / x = 1%"),
    ]
    for label, y, share, observed, slack, ratio in rows:
        target_width = bar_width * (1.0 - share)
        slack_width = bar_width * share
        parts.extend(
            [
                f'<text x="{LEFT}" y="{y + 29}" font-size="20" '
                f'font-weight="600" fill="{INK}">{label}</text>',
                f'<rect x="{bar_x}" y="{y}" width="{bar_width}" '
                f'height="{bar_height}" rx="7" fill="{PALE_TEAL}" '
                f'stroke="{GRID}" stroke-width="2"/>',
                f'<rect x="{bar_x}" y="{y}" width="{target_width:.2f}" '
                f'height="{bar_height}" rx="7" fill="{TEAL}" opacity="0.9"/>',
                f'<rect x="{bar_x + target_width:.2f}" y="{y}" '
                f'width="{max(slack_width, 5):.2f}" height="{bar_height}" '
                f'fill="{ORANGE}"/>',
                f'<text x="{bar_x}" y="{y - 15}" font-size="16" '
                f'fill="{INK}">{observed}</text>',
                f'<text x="{bar_x + bar_width}" y="{y - 15}" '
                f'text-anchor="end" font-size="16" fill="{ORANGE}">{slack}</text>',
                f'<text x="{bar_x + bar_width}" y="{y + 75}" '
                f'text-anchor="end" font-size="18" font-weight="600" '
                f'fill="{ORANGE}">{ratio}</text>',
            ]
        )
    parts.extend(
        [
            f'<rect x="{bar_x}" y="{420}" width="24" height="15" fill="{TEAL}"/>',
            f'<text x="{bar_x + 34}" y="{433}" font-size="15" '
            f'fill="{INK}">x - s⁻</text>',
            f'<rect x="{bar_x + 190}" y="{420}" width="24" height="15" '
            f'fill="{ORANGE}"/>',
            f'<text x="{bar_x + 224}" y="{433}" font-size="15" fill="{INK}">s⁻</text>',
        ]
    )
    parts.append("</svg>")
    return "\n".join(parts)


def ddf_directions() -> str:
    xmax, ymax = 4.5, 4.2
    parts = _base(
        "Directional distance paths",
        "Input-only, output-only, and joint directional paths from DMU E "
        "to a VRS frontier.",
    )
    _axes(parts, xmax=xmax, ymax=ymax)
    frontier = [_point(*DMUS[name], xmax=xmax, ymax=ymax) for name in "ABCD"]
    parts.append(
        f'<path d="{_path(frontier)}" fill="none" stroke="{INK}" '
        'stroke-width="4" stroke-linejoin="round"/>'
    )
    e = DMUS["E"]
    input_target = (4.0 / 3.0, 1.5)
    output_target = DMUS["B"]
    joint_target = (14.0 / 9.0, 11.0 / 6.0)
    e_px = _point(*e, xmax=xmax, ymax=ymax)
    targets = [
        (input_target, TEAL, "arrow-teal", "g = (x, 0)", -12, 25),
        (output_target, ORANGE, "arrow-orange", "g = (0, y)", 15, 8),
        (joint_target, PURPLE, "arrow-purple", "g = (x, y)", -20, -15),
    ]
    for target, color, marker, label, dx, dy in targets:
        t_px = _point(*target, xmax=xmax, ymax=ymax)
        parts.extend(
            [
                f'<line x1="{e_px[0]:.2f}" y1="{e_px[1]:.2f}" '
                f'x2="{t_px[0]:.2f}" y2="{t_px[1]:.2f}" '
                f'stroke="{color}" stroke-width="3" '
                f'marker-end="url(#{marker})"/>',
                f'<circle cx="{t_px[0]:.2f}" cy="{t_px[1]:.2f}" r="6" '
                f'fill="white" stroke="{color}" stroke-width="3"/>',
                f'<text x="{(e_px[0] + t_px[0]) / 2 + dx:.2f}" '
                f'y="{(e_px[1] + t_px[1]) / 2 + dy:.2f}" font-size="15" '
                f'fill="{color}">{label}</text>',
            ]
        )
    _dmu(parts, "E", *e, xmax=xmax, ymax=ymax, fill=INK, radius=8)
    for label in "ABCD":
        _dmu(parts, label, *DMUS[label], xmax=xmax, ymax=ymax, fill=INK, radius=5)
    parts.append("</svg>")
    return "\n".join(parts)


def environmental_disposability() -> str:
    parts = _base(
        "Weak and strong disposability of undesirable output",
        "Weak disposability reduces desirable and undesirable outputs "
        "together, whereas strong disposability reduces undesirable output "
        "while holding desirable output fixed.",
    )
    panels = [
        (82, 345, "weak"),
        (415, 678, "strong"),
    ]
    for left, right, label in panels:
        bottom, top = 420, 92
        parts.extend(
            [
                f'<rect x="{left - 20}" y="{top - 34}" '
                f'width="{right - left + 52}" height="{bottom - top + 72}" '
                f'rx="12" fill="{PALE_TEAL}" opacity="0.32"/>',
                f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" '
                f'stroke="{INK}" stroke-width="2" marker-end="url(#axis-arrow)"/>',
                f'<line x1="{left}" y1="{bottom}" x2="{left}" y2="{top}" '
                f'stroke="{INK}" stroke-width="2" marker-end="url(#axis-arrow)"/>',
                f'<text x="{right + 10}" y="{bottom + 7}" font-size="18" '
                f'font-style="italic" fill="{INK}">y</text>',
                f'<text x="{left - 7}" y="{top - 12}" font-size="18" '
                f'font-style="italic" fill="{INK}">b</text>',
                f'<text x="{(left + right) / 2}" y="{top - 12}" '
                f'text-anchor="middle" font-size="19" font-weight="600" '
                f'fill="{INK}">{label}</text>',
            ]
        )

    weak_p = (300, 145)
    weak_target = (190, 282)
    strong_p = (635, 145)
    strong_target = (635, 315)
    parts.extend(
        [
            f'<line x1="{82}" y1="{420}" x2="{weak_p[0]}" y2="{weak_p[1]}" '
            f'stroke="{GRID}" stroke-width="2" stroke-dasharray="7 6"/>',
            f'<line x1="{weak_p[0]}" y1="{weak_p[1]}" '
            f'x2="{weak_target[0]}" y2="{weak_target[1]}" '
            f'stroke="{PURPLE}" stroke-width="4" '
            'marker-end="url(#arrow-purple)"/>',
            f'<circle cx="{weak_p[0]}" cy="{weak_p[1]}" r="8" '
            f'fill="{ORANGE}" stroke="white" stroke-width="2"/>',
            f'<circle cx="{weak_target[0]}" cy="{weak_target[1]}" r="7" '
            f'fill="white" stroke="{PURPLE}" stroke-width="3"/>',
            f'<text x="{weak_p[0] + 11}" y="{weak_p[1] - 9}" font-size="17" '
            f'fill="{ORANGE}">(y, b)</text>',
            f'<text x="{weak_target[0] - 5}" y="{weak_target[1] + 25}" '
            f'text-anchor="middle" font-size="17" fill="{PURPLE}">'
            "&#945;(y, b)</text>",
            f'<line x1="{strong_p[0]}" y1="{strong_p[1]}" '
            f'x2="{strong_target[0]}" y2="{strong_target[1]}" '
            f'stroke="{TEAL}" stroke-width="4" '
            'marker-end="url(#arrow-teal)"/>',
            f'<circle cx="{strong_p[0]}" cy="{strong_p[1]}" r="8" '
            f'fill="{ORANGE}" stroke="white" stroke-width="2"/>',
            f'<circle cx="{strong_target[0]}" cy="{strong_target[1]}" r="7" '
            f'fill="white" stroke="{TEAL}" stroke-width="3"/>',
            f'<text x="{strong_p[0] - 14}" y="{strong_p[1] - 12}" '
            f'text-anchor="end" font-size="17" fill="{ORANGE}">(y, b)</text>',
            f'<text x="{strong_target[0] - 14}" y="{strong_target[1] + 7}" '
            f'text-anchor="end" font-size="17" fill="{TEAL}">'
            "(y, &#945;b)</text>",
        ]
    )
    parts.append("</svg>")
    return "\n".join(parts)


def undesirable_sbm_components() -> str:
    parts = _base(
        "Three relative slack components in undesirable-output SBM",
        "Independent normalized improvements reduce an input, expand a "
        "desirable output, and reduce an undesirable output.",
    )
    rows = [
        ("x", 140, 610, 420, TEAL, "arrow-teal", "s⁻ / x = 20%"),
        ("y", 265, 390, 610, ORANGE, "arrow-orange", "s⁺ / y = 25%"),
        ("b", 390, 610, 455, PURPLE, "arrow-purple", "sᵇ / b = 30%"),
    ]
    for symbol, y, observed_x, target_x, color, marker, formula in rows:
        parts.extend(
            [
                f'<text x="{LEFT}" y="{y + 7}" font-size="25" '
                f'font-style="italic" font-weight="600" fill="{INK}">{symbol}</text>',
                f'<line x1="{175}" y1="{y}" x2="{650}" y2="{y}" '
                f'stroke="{GRID}" stroke-width="6" stroke-linecap="round"/>',
                f'<line x1="{observed_x}" y1="{y}" x2="{target_x}" y2="{y}" '
                f'stroke="{color}" stroke-width="4" '
                f'marker-end="url(#{marker})"/>',
                f'<circle cx="{observed_x}" cy="{y}" r="9" fill="{INK}" '
                f'stroke="white" stroke-width="2"/>',
                f'<circle cx="{target_x}" cy="{y}" r="8" fill="white" '
                f'stroke="{color}" stroke-width="3"/>',
                f'<text x="{(observed_x + target_x) / 2}" y="{y - 22}" '
                f'text-anchor="middle" font-size="18" fill="{color}">{formula}</text>',
            ]
        )
    parts.extend(
        [
            f'<circle cx="{250}" cy="{460}" r="8" fill="{INK}"/>',
            f'<text x="{268}" y="{466}" font-size="16" fill="{INK}">observed</text>',
            f'<circle cx="{455}" cy="{460}" r="8" fill="white" '
            f'stroke="{TEAL}" stroke-width="3"/>',
            f'<text x="{473}" y="{466}" font-size="16" fill="{INK}">target</text>',
        ]
    )
    parts.append("</svg>")
    return "\n".join(parts)


def by_production_intersection() -> str:
    parts = _base(
        "By-production as the intersection of two subtechnologies",
        "The intended-production subtechnology links all inputs to desirable "
        "output with intensity lambda, while the residual-generation "
        "subtechnology links polluting input to undesirable output with a "
        "separate intensity mu.",
    )
    parts.extend(
        [
            f'<rect x="{250}" y="{48}" width="260" height="62" rx="12" '
            f'fill="{PALE_ORANGE}" stroke="{ORANGE}" stroke-width="2"/>',
            f'<text x="{380}" y="{86}" text-anchor="middle" font-size="22" '
            f'font-weight="600" fill="{INK}">DMU (xⁿ, xᵖ, y, b)</text>',
            f'<line x1="{315}" y1="{110}" x2="{218}" y2="{165}" '
            f'stroke="{TEAL}" stroke-width="3" marker-end="url(#arrow-teal)"/>',
            f'<line x1="{445}" y1="{110}" x2="{542}" y2="{165}" '
            f'stroke="{PURPLE}" stroke-width="3" marker-end="url(#arrow-purple)"/>',
            f'<rect x="{70}" y="{175}" width="290" height="174" rx="14" '
            f'fill="{PALE_TEAL}" stroke="{TEAL}" stroke-width="3"/>',
            f'<text x="{215}" y="{213}" text-anchor="middle" font-size="22" '
            f'font-weight="700" fill="{TEAL}">T₁</text>',
            f'<text x="{215}" y="{253}" text-anchor="middle" font-size="20" '
            f'fill="{INK}">(xⁿ, xᵖ) → y</text>',
            f'<text x="{215}" y="{297}" text-anchor="middle" font-size="18" '
            f'fill="{TEAL}">Xλ ≤ x   Yλ ≥ y</text>',
            f'<text x="{215}" y="{330}" text-anchor="middle" font-size="18" '
            f'fill="{INK}">λ</text>',
            f'<rect x="{400}" y="{175}" width="290" height="174" rx="14" '
            f'fill="#eee8f3" stroke="{PURPLE}" stroke-width="3"/>',
            f'<text x="{545}" y="{213}" text-anchor="middle" font-size="22" '
            f'font-weight="700" fill="{PURPLE}">T₂</text>',
            f'<text x="{545}" y="{253}" text-anchor="middle" font-size="20" '
            f'fill="{INK}">xᵖ → b</text>',
            f'<text x="{545}" y="{297}" text-anchor="middle" font-size="18" '
            f'fill="{PURPLE}">Xᵖμ ≥ xᵖ   Bμ ≤ b</text>',
            f'<text x="{545}" y="{330}" text-anchor="middle" font-size="18" '
            f'fill="{INK}">μ</text>',
            f'<line x1="{250}" y1="{350}" x2="{330}" y2="{402}" '
            f'stroke="{TEAL}" stroke-width="3" marker-end="url(#arrow-teal)"/>',
            f'<line x1="{510}" y1="{350}" x2="{430}" y2="{402}" '
            f'stroke="{PURPLE}" stroke-width="3" marker-end="url(#arrow-purple)"/>',
            f'<rect x="{245}" y="{410}" width="270" height="58" rx="12" '
            f'fill="white" stroke="{INK}" stroke-width="2"/>',
            f'<text x="{380}" y="{447}" text-anchor="middle" font-size="23" '
            f'font-weight="600" fill="{INK}">T_BP = T₁ ∩ T₂</text>',
        ]
    )
    parts.append("</svg>")
    return "\n".join(parts)


def bp_ddf_vs_fgl() -> str:
    parts = _base(
        "BP-DDF and BP-FGL aggregation",
        "BP-DDF takes the smaller of two directional distances and can stop "
        "when one is zero, whereas BP-FGL averages two efficiency components "
        "and equals one only when both equal one.",
    )
    panels = [(70, 350, "BP-DDF"), (410, 690, "BP-FGL")]
    for left, right, title in panels:
        parts.extend(
            [
                f'<rect x="{left}" y="{62}" width="{right - left}" '
                f'height="372" rx="14" fill="{PALE_TEAL}" opacity="0.35"/>',
                f'<text x="{(left + right) / 2}" y="{102}" '
                f'text-anchor="middle" font-size="23" font-weight="700" '
                f'fill="{INK}">{title}</text>',
            ]
        )
    parts.extend(
        [
            f'<text x="{105}" y="{160}" font-size="19" fill="{INK}">β¹ = 0.20</text>',
            f'<rect x="{105}" y="{178}" width="190" height="28" rx="5" fill="{GRID}"/>',
            f'<rect x="{105}" y="{178}" width="152" height="28" rx="5" fill="{TEAL}"/>',
            f'<text x="{105}" y="{260}" font-size="19" fill="{INK}">β² = 0.00</text>',
            f'<rect x="{105}" y="{278}" width="190" height="28" rx="5" fill="{GRID}"/>',
            f'<line x1="{120}" y1="{338}" x2="{280}" y2="{338}" '
            f'stroke="{ORANGE}" stroke-width="3" marker-end="url(#arrow-orange)"/>',
            f'<text x="{210}" y="{385}" text-anchor="middle" font-size="22" '
            f'font-weight="700" fill="{ORANGE}">min(β¹, β²) = 0</text>',
            f'<text x="{445}" y="{160}" font-size="19" fill="{INK}">E¹ = 0.70</text>',
            f'<rect x="{445}" y="{178}" width="190" height="28" rx="5" fill="{GRID}"/>',
            f'<rect x="{445}" y="{178}" width="133" height="28" rx="5" fill="{TEAL}"/>',
            f'<text x="{445}" y="{260}" font-size="19" fill="{INK}">E² = 1.00</text>',
            f'<rect x="{445}" y="{278}" width="190" height="28" rx="5" '
            f'fill="{PURPLE}"/>',
            f'<line x1="{460}" y1="{338}" x2="{620}" y2="{338}" '
            f'stroke="{ORANGE}" stroke-width="3" marker-end="url(#arrow-orange)"/>',
            f'<text x="{550}" y="{385}" text-anchor="middle" font-size="22" '
            f'font-weight="700" fill="{ORANGE}">(E¹ + E²) / 2 = 0.85</text>',
        ]
    )
    parts.append("</svg>")
    return "\n".join(parts)


def material_balance_flow() -> str:
    parts = _base(
        "Material balance and efficiency decomposition",
        "Material inflow splits into material retained in desirable output "
        "and residual material, while environmental efficiency decomposes "
        "into technical and environmental allocative efficiency.",
    )
    parts.extend(
        [
            f'<rect x="{65}" y="{112}" width="180" height="86" rx="12" '
            f'fill="{PALE_ORANGE}" stroke="{ORANGE}" stroke-width="3"/>',
            f'<text x="{155}" y="{151}" text-anchor="middle" font-size="20" '
            f'fill="{INK}">inflow</text>',
            f'<text x="{155}" y="{181}" text-anchor="middle" font-size="24" '
            f'font-weight="700" fill="{ORANGE}">a&#8242;x</text>',
            f'<line x1="{245}" y1="{155}" x2="{340}" y2="{155}" '
            f'stroke="{INK}" stroke-width="4" marker-end="url(#axis-arrow)"/>',
            f'<circle cx="{370}" cy="{155}" r="14" fill="{INK}"/>',
            f'<line x1="{382}" y1="{147}" x2="{478}" y2="{95}" '
            f'stroke="{TEAL}" stroke-width="4" marker-end="url(#arrow-teal)"/>',
            f'<line x1="{382}" y1="{163}" x2="{478}" y2="{222}" '
            f'stroke="{PURPLE}" stroke-width="4" marker-end="url(#arrow-purple)"/>',
            f'<rect x="{492}" y="{54}" width="200" height="82" rx="12" '
            f'fill="{PALE_TEAL}" stroke="{TEAL}" stroke-width="3"/>',
            f'<text x="{592}" y="{87}" text-anchor="middle" font-size="18" '
            f'fill="{INK}">retained</text>',
            f'<text x="{592}" y="{117}" text-anchor="middle" font-size="24" '
            f'font-weight="700" fill="{TEAL}">c&#8242;y</text>',
            f'<rect x="{492}" y="{192}" width="200" height="82" rx="12" '
            f'fill="#eee8f3" stroke="{PURPLE}" stroke-width="3"/>',
            f'<text x="{592}" y="{225}" text-anchor="middle" font-size="18" '
            f'fill="{INK}">residual</text>',
            f'<text x="{592}" y="{255}" text-anchor="middle" font-size="24" '
            f'font-weight="700" fill="{PURPLE}">z</text>',
            f'<rect x="{180}" y="{310}" width="400" height="66" rx="12" '
            f'fill="white" stroke="{INK}" stroke-width="2"/>',
            f'<text x="{380}" y="{352}" text-anchor="middle" font-size="26" '
            f'font-weight="600" fill="{INK}">a&#8242;x = c&#8242;y + z</text>',
            f'<line x1="{380}" y1="{377}" x2="{380}" y2="{410}" '
            f'stroke="{ORANGE}" stroke-width="3" marker-end="url(#arrow-orange)"/>',
            f'<text x="{380}" y="{456}" text-anchor="middle" font-size="25" '
            f'font-weight="700" fill="{ORANGE}">EE = TE &#215; EAE</text>',
        ]
    )
    parts.append("</svg>")
    return "\n".join(parts)


def material_balance_management_targets() -> str:
    xmax = ymax = 4.5
    parts = _base(
        "Technical saving and material-mix improvement",
        "Four fixed-output production plans show how DMU D first removes "
        "proportional resource waste at C and then changes the input mix "
        "toward the minimum-material plan B.",
    )
    _axes(parts, xmax=xmax, ymax=ymax, xlabel="x₁", ylabel="x₂")

    feasible_data = [
        (1.0, 3.0),
        (3.0, 1.0),
        (xmax, 1.0),
        (xmax, ymax),
        (1.0, ymax),
    ]
    feasible = [_point(*value, xmax=xmax, ymax=ymax) for value in feasible_data]
    frontier = [
        _point(1.0, 3.0, xmax=xmax, ymax=ymax),
        _point(3.0, 1.0, xmax=xmax, ymax=ymax),
    ]
    parts.extend(
        [
            f'<path d="{_path(feasible)} Z" fill="{PALE_TEAL}" opacity="0.62"/>',
            f'<path d="{_path(frontier)}" fill="none" stroke="{TEAL}" '
            'stroke-width="4" stroke-linecap="round"/>',
        ]
    )

    # Parallel material-content accounts: N = x1 + 3*x2.
    material_lines = (
        (6.0, PURPLE, "N = 6"),
        (8.0, ORANGE, "N = 8"),
        (16.0, GRAY, "N = 16"),
    )
    for material, color, label in material_lines:
        endpoints: list[tuple[float, float]] = []
        for x in (0.0, xmax):
            y = (material - x) / 3.0
            if 0.0 <= y <= ymax:
                endpoints.append((x, y))
        for y in (0.0, ymax):
            x = material - 3.0 * y
            if 0.0 <= x <= xmax:
                endpoints.append((x, y))
        endpoints = sorted(set(endpoints))
        if len(endpoints) < 2:
            continue
        start = _point(*endpoints[0], xmax=xmax, ymax=ymax)
        end = _point(*endpoints[-1], xmax=xmax, ymax=ymax)
        parts.append(
            f'<line x1="{start[0]:.2f}" y1="{start[1]:.2f}" '
            f'x2="{end[0]:.2f}" y2="{end[1]:.2f}" stroke="{color}" '
            'stroke-width="2" stroke-dasharray="8 6"/>'
        )
        label_x = end[0] - 8
        label_y = end[1] - 8
        parts.append(
            f'<text x="{label_x:.2f}" y="{label_y:.2f}" text-anchor="end" '
            f'font-size="14" fill="{color}">{label}</text>'
        )

    plans = {
        "A": (1.0, 3.0),
        "B": (3.0, 1.0),
        "C": (2.0, 2.0),
        "D": (4.0, 4.0),
    }
    for label, (x, y) in plans.items():
        _dmu(
            parts,
            label,
            x,
            y,
            xmax=xmax,
            ymax=ymax,
            fill=(PURPLE if label == "B" else ORANGE if label in {"C", "D"} else INK),
            radius=8 if label in {"B", "C", "D"} else 6,
            dx=-22 if label == "C" else 10,
            dy=-10,
        )

    d_x, d_y = _point(*plans["D"], xmax=xmax, ymax=ymax)
    c_x, c_y = _point(*plans["C"], xmax=xmax, ymax=ymax)
    b_x, b_y = _point(*plans["B"], xmax=xmax, ymax=ymax)
    parts.extend(
        [
            f'<line x1="{d_x - 7:.2f}" y1="{d_y + 7:.2f}" '
            f'x2="{c_x + 8:.2f}" y2="{c_y - 8:.2f}" '
            f'stroke="{ORANGE}" stroke-width="4" '
            'marker-end="url(#arrow-orange)"/>',
            f'<text x="{(d_x + c_x) / 2 + 14:.2f}" '
            f'y="{(d_y + c_y) / 2 - 10:.2f}" font-size="15" '
            f'fill="{ORANGE}">common resource saving</text>',
            f'<text x="{(d_x + c_x) / 2 + 14:.2f}" '
            f'y="{(d_y + c_y) / 2 + 10:.2f}" font-size="15" '
            f'fill="{ORANGE}">TE = 0.50</text>',
            f'<line x1="{c_x + 8:.2f}" y1="{c_y + 8:.2f}" '
            f'x2="{b_x - 8:.2f}" y2="{b_y - 8:.2f}" '
            f'stroke="{PURPLE}" stroke-width="4" '
            'marker-end="url(#arrow-purple)"/>',
            f'<text x="{(c_x + b_x) / 2 + 18:.2f}" '
            f'y="{(c_y + b_y) / 2 - 9:.2f}" font-size="15" '
            f'fill="{PURPLE}">lower-material mix</text>',
            f'<text x="{(c_x + b_x) / 2 + 18:.2f}" '
            f'y="{(c_y + b_y) / 2 + 11:.2f}" font-size="15" '
            f'fill="{PURPLE}">EAE = 0.75</text>',
            f'<rect x="106" y="55" width="222" height="62" rx="10" '
            f'fill="white" stroke="{INK}" stroke-width="2"/>',
            f'<text x="217" y="82" text-anchor="middle" font-size="16" '
            f'fill="{INK}">same output commitment</text>',
            f'<text x="217" y="105" text-anchor="middle" font-size="18" '
            f'font-weight="700" fill="{INK}">EE = 6/16 = 0.375</text>',
            f'<text x="454" y="146" font-size="15" fill="{TEAL}">'
            "feasible production plans</text>",
        ]
    )
    parts.append("</svg>")
    return "\n".join(parts)


def productivity_frontier_motion() -> str:
    xmax, ymax = 4.5, 4.6
    parts = _base(
        "Operating performance and changing best-practice opportunities",
        "A unit's performance relative to its period benchmark changes while "
        "the best-practice opportunities represented by the sample also change.",
    )
    _axes(parts, xmax=xmax, ymax=ymax)
    old_data = [(1.0, 1.5), (2.0, 2.4), (3.0, 3.0), (4.0, 3.4)]
    new_data = [(x, y * 1.15) for x, y in old_data]
    old = [_point(*value, xmax=xmax, ymax=ymax) for value in old_data]
    new = [_point(*value, xmax=xmax, ymax=ymax) for value in new_data]
    z_old = (3.0, 2.1)
    z_new = (3.0, 2.7)
    p_old = _point(*z_old, xmax=xmax, ymax=ymax)
    p_new = _point(*z_new, xmax=xmax, ymax=ymax)
    f_old = _point(3.0, 3.0, xmax=xmax, ymax=ymax)
    f_new = _point(3.0, 3.45, xmax=xmax, ymax=ymax)
    parts.extend(
        [
            f'<path d="{_path(old)}" fill="none" stroke="{TEAL}" stroke-width="4"/>',
            f'<path d="{_path(new)}" fill="none" stroke="{PURPLE}" '
            'stroke-width="4" stroke-dasharray="11 7"/>',
            f'<line x1="{p_old[0]}" y1="{p_old[1]}" x2="{f_old[0]}" '
            f'y2="{f_old[1]}" stroke="{TEAL}" stroke-width="2" '
            'stroke-dasharray="6 5"/>',
            f'<line x1="{p_new[0]}" y1="{p_new[1]}" x2="{f_new[0]}" '
            f'y2="{f_new[1]}" stroke="{PURPLE}" stroke-width="2" '
            'stroke-dasharray="6 5"/>',
            f'<line x1="{p_old[0]}" y1="{p_old[1]}" x2="{p_new[0]}" '
            f'y2="{p_new[1] + 7}" stroke="{ORANGE}" stroke-width="4" '
            'marker-end="url(#arrow-orange)"/>',
            f'<line x1="{f_old[0] + 25}" y1="{f_old[1]}" '
            f'x2="{f_new[0] + 25}" y2="{f_new[1] + 7}" '
            f'stroke="{PURPLE}" stroke-width="3" '
            'marker-end="url(#arrow-purple)"/>',
            f'<circle cx="{p_old[0]}" cy="{p_old[1]}" r="8" fill="{INK}" '
            'stroke="white" stroke-width="2"/>',
            f'<circle cx="{p_new[0]}" cy="{p_new[1]}" r="8" fill="{ORANGE}" '
            'stroke="white" stroke-width="2"/>',
            f'<text x="{p_old[0] + 13}" y="{p_old[1] + 19}" font-size="17" '
            f'fill="{INK}">z(t)</text>',
            f'<text x="{p_new[0] + 13}" y="{p_new[1] - 10}" font-size="17" '
            f'fill="{ORANGE}">z(t+1)</text>',
            f'<text x="{RIGHT - 80}" y="{old[-1][1] + 26}" font-size="17" '
            f'fill="{TEAL}">T(t)</text>',
            f'<text x="{RIGHT - 80}" y="{new[-1][1] - 11}" font-size="17" '
            f'fill="{PURPLE}">T(t+1)</text>',
            f'<rect x="102" y="61" width="318" height="70" rx="9" '
            f'fill="white" stroke="{GRID}" stroke-width="1.5"/>',
            f'<line x1="119" y1="83" x2="143" y2="83" stroke="{ORANGE}" '
            'stroke-width="4"/>',
            f'<text x="153" y="88" font-size="15" fill="{INK}">'
            "operating-performance change</text>",
            f'<line x1="119" y1="110" x2="143" y2="110" stroke="{PURPLE}" '
            'stroke-width="4"/>',
            f'<text x="153" y="115" font-size="15" fill="{INK}">'
            "best-practice-opportunity change</text>",
        ]
    )
    parts.append("</svg>")
    return "\n".join(parts)


def luenberger_programme_ledger() -> str:
    """Show the common programme and four directional appraisals."""
    return "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="680" '
            'viewBox="0 0 900 680" role="img" '
            'aria-labelledby="title description">',
            '<title id="title">One declared programme, four benchmark '
            "appraisals</title>",
            '<desc id="description">One common programme of resource saving and '
            "service expansion supplies the unit for appraising an old and a new "
            "operating plan against old and new production opportunities. The four "
            "directional distances enter an additive Luenberger change account.</desc>",
            "<defs>",
            '<filter id="lp-shadow" x="-10%" y="-10%" width="120%" '
            'height="130%"><feDropShadow dx="0" dy="2" stdDeviation="3" '
            'flood-color="#24323d" flood-opacity="0.12"/></filter>',
            "</defs>",
            '<rect width="900" height="680" fill="#ffffff"/>',
            '<g font-family="Arial, sans-serif">',
            '<text x="34" y="38" font-size="24" font-weight="700" '
            'fill="#24323d">One declared programme, four benchmark appraisals</text>',
            '<text x="34" y="66" font-size="15" fill="#5c6b73">'
            "The unit of change is fixed before either period's plan is "
            "compared.</text>",
            '<rect x="34" y="88" width="832" height="92" rx="14" fill="#24323d"/>',
            '<text x="54" y="119" font-size="15" font-weight="700" '
            'fill="#ffffff">ONE COMMON PROGRAMME UNIT  g</text>',
            '<rect x="285" y="103" width="232" height="38" rx="19" fill="#dceff0"/>',
            '<text x="401" y="128" text-anchor="middle" font-size="15" '
            'font-weight="700" fill="#176b73">save g^x resource units</text>',
            '<text x="539" y="129" text-anchor="middle" font-size="20" '
            'font-weight="700" fill="#ffffff">+</text>',
            '<rect x="560" y="103" width="280" height="38" rx="19" fill="#f8e8dc"/>',
            '<text x="700" y="128" text-anchor="middle" font-size="15" '
            'font-weight="700" fill="#d97732">deliver g^y service units</text>',
            '<text x="450" y="163" text-anchor="middle" font-size="14" '
            'fill="#d7e2e5">The physical unit remains unchanged in every '
            "appraisal.</text>",
            '<text x="363" y="216" text-anchor="middle" font-size="15" '
            'font-weight="700" fill="#176b73">OLD OPPORTUNITIES  '
            "&#x1D4AF;^t</text>",
            '<text x="683" y="216" text-anchor="middle" font-size="15" '
            'font-weight="700" fill="#76528f">NEW OPPORTUNITIES  '
            "&#x1D4AF;^(t+1)</text>",
            '<text x="42" y="279" font-size="15" font-weight="700" '
            'fill="#24323d">OLD PLAN  z^t</text>',
            '<text x="42" y="405" font-size="15" font-weight="700" '
            'fill="#24323d">NEW PLAN  z^(t+1)</text>',
            '<rect x="205" y="238" width="316" height="100" rx="12" '
            'fill="#eef7f7" stroke="#176b73" filter="url(#lp-shadow)"/>',
            '<text x="363" y="277" text-anchor="middle" font-size="21" '
            'font-weight="700" fill="#24323d">D^t(z^t; g)</text>',
            '<text x="363" y="309" text-anchor="middle" font-size="14" '
            'fill="#5c6b73">own-period programme shortfall</text>',
            '<rect x="545" y="238" width="316" height="100" rx="12" '
            'fill="#f3eef7" stroke="#76528f" filter="url(#lp-shadow)"/>',
            '<text x="703" y="277" text-anchor="middle" font-size="21" '
            'font-weight="700" fill="#24323d">D^(t+1)(z^t; g)</text>',
            '<text x="703" y="309" text-anchor="middle" font-size="14" '
            'fill="#5c6b73">old plan under new opportunities</text>',
            '<rect x="205" y="364" width="316" height="100" rx="12" '
            'fill="#fff3e9" stroke="#d97732" filter="url(#lp-shadow)"/>',
            '<text x="363" y="403" text-anchor="middle" font-size="21" '
            'font-weight="700" fill="#24323d">D^t(z^(t+1); g)</text>',
            '<text x="363" y="435" text-anchor="middle" font-size="14" '
            'fill="#5c6b73">may be negative beyond old opportunities</text>',
            '<rect x="545" y="364" width="316" height="100" rx="12" '
            'fill="#eef7f7" stroke="#176b73" filter="url(#lp-shadow)"/>',
            '<text x="703" y="403" text-anchor="middle" font-size="21" '
            'font-weight="700" fill="#24323d">D^(t+1)(z^(t+1); g)</text>',
            '<text x="703" y="435" text-anchor="middle" font-size="14" '
            'fill="#5c6b73">own-period programme shortfall</text>',
            '<rect x="52" y="500" width="796" height="104" rx="14" '
            'fill="#f8fafb" stroke="#cfdadd"/>',
            '<text x="76" y="530" font-size="14" font-weight="700" '
            'fill="#176b73">OLD BENCHMARK</text>',
            '<text x="76" y="556" font-size="15" fill="#24323d">'
            "P^t = old plan's D^t - new plan's D^t</text>",
            '<text x="488" y="530" font-size="14" font-weight="700" '
            'fill="#76528f">NEW BENCHMARK</text>',
            '<text x="488" y="556" font-size="15" fill="#24323d">'
            "P^(t+1) = D^(t+1)(old) - D^(t+1)(new)</text>",
            '<text x="450" y="588" text-anchor="middle" font-size="20" '
            'font-weight="700" fill="#d97732">L = 1/2 [P^t + P^(t+1)] '
            "= EC_L + TC_L</text>",
            '<rect x="34" y="624" width="832" height="38" rx="10" fill="#24323d"/>',
            '<text x="450" y="649" text-anchor="middle" font-size="14" '
            'font-weight="700" fill="#ffffff">The account allocates change; it '
            "does not identify management or technology causes.</text>",
            "</g>",
            "</svg>",
        ]
    )


def malmquist_luenberger_frontier_account() -> str:
    """Contrast two exact environmental-productivity change accounts."""
    return "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="650" '
            'viewBox="0 0 900 650" role="img" '
            'aria-labelledby="title description">',
            '<title id="title">Two exact Malmquist-Luenberger change accounts</title>',
            '<desc id="description">The first account holds the relevant '
            "best-practice opportunity fixed while an organization narrows its "
            "operating shortfall. The second contrasts old and new environmental "
            "opportunities while both observed plans remain contemporaneous "
            "benchmarks.</desc>",
            "<defs>",
            '<marker id="mlc-arrow" markerWidth="9" markerHeight="9" refX="8" '
            'refY="4" orient="auto"><path d="M0,0 L0,8 L9,4 z" '
            'fill="#d97732"/></marker>',
            '<filter id="mlc-shadow" x="-10%" y="-10%" width="120%" '
            'height="130%"><feDropShadow dx="0" dy="2" stdDeviation="3" '
            'flood-color="#24323d" flood-opacity="0.10"/></filter>',
            "</defs>",
            '<rect width="900" height="650" fill="#ffffff"/>',
            '<g font-family="Arial, sans-serif">',
            '<text x="32" y="38" font-size="24" font-weight="700" '
            'fill="#24323d">What changed in measured environmental '
            "productivity?</text>",
            '<text x="32" y="66" font-size="15" fill="#5c6b73">'
            "Same resources · more service and less residual define improvement</text>",
            '<rect x="28" y="91" width="414" height="464" rx="15" '
            'fill="#f8fafb" stroke="#d5dee2" filter="url(#mlc-shadow)"/>',
            '<rect x="458" y="91" width="414" height="464" rx="15" '
            'fill="#f8fafb" stroke="#d5dee2" filter="url(#mlc-shadow)"/>',
            '<text x="52" y="122" font-size="18" font-weight="700" '
            'fill="#176b73">A · operating shortfall narrows</text>',
            '<text x="482" y="122" font-size="18" font-weight="700" '
            'fill="#76528f">B · represented opportunity improves</text>',
            '<line x1="78" y1="414" x2="410" y2="414" stroke="#24323d" '
            'stroke-width="2"/>',
            '<line x1="78" y1="414" x2="78" y2="154" stroke="#24323d" '
            'stroke-width="2"/>',
            '<text x="244" y="440" text-anchor="middle" font-size="14" '
            'fill="#24323d">undesirable residual · less is better &#x2190;</text>',
            '<text x="51" y="288" text-anchor="middle" font-size="14" '
            'fill="#24323d" transform="rotate(-90 51 288)">'
            "desirable service · more is better &#x2191;</text>",
            '<line x1="84" y1="404" x2="236" y2="174" stroke="#176b73" '
            'stroke-width="4"/>',
            '<text x="112" y="174" font-size="14" fill="#176b73">'
            "Reference unit F</text>",
            '<line x1="355" y1="360" x2="202" y2="286" stroke="#687780" '
            'stroke-width="2" stroke-dasharray="6 5"/>',
            '<line x1="300" y1="288" x2="224" y2="194" stroke="#687780" '
            'stroke-width="2" stroke-dasharray="6 5"/>',
            '<line x1="355" y1="360" x2="305" y2="292" stroke="#d97732" '
            'stroke-width="3" marker-end="url(#mlc-arrow)"/>',
            '<circle cx="355" cy="360" r="7" fill="#24323d" '
            'stroke="#ffffff" stroke-width="2"/>',
            '<circle cx="300" cy="288" r="7" fill="#d97732" '
            'stroke="#ffffff" stroke-width="2"/>',
            '<text x="276" y="382" font-size="15" fill="#24323d">A(t) · D = 3/5</text>',
            '<text x="266" y="272" font-size="15" fill="#d97732">'
            "A(t+1) · D = 1/3</text>",
            '<text x="247" y="333" font-size="14" fill="#d97732">'
            "more favorable plan</text>",
            '<rect x="52" y="458" width="366" height="76" rx="11" '
            'fill="#dceff0" stroke="#b7d7d9"/>',
            '<text x="235" y="489" text-anchor="middle" font-size="19" '
            'font-weight="700" fill="#176b73">ML = 6/5 = EC 6/5 '
            "&#xD7; TC 1</text>",
            '<text x="235" y="516" text-anchor="middle" font-size="14" '
            'fill="#24323d">The same relevant opportunity determines all '
            "four comparisons.</text>",
            '<line x1="508" y1="414" x2="840" y2="414" stroke="#24323d" '
            'stroke-width="2"/>',
            '<line x1="508" y1="414" x2="508" y2="154" stroke="#24323d" '
            'stroke-width="2"/>',
            '<text x="674" y="440" text-anchor="middle" font-size="14" '
            'fill="#24323d">undesirable residual · less is better &#x2190;</text>',
            '<text x="481" y="288" text-anchor="middle" font-size="14" '
            'fill="#24323d" transform="rotate(-90 481 288)">'
            "desirable service · more is better &#x2191;</text>",
            '<line x1="514" y1="404" x2="682" y2="174" stroke="#76528f" '
            'stroke-width="4"/>',
            '<line x1="514" y1="404" x2="823" y2="360" stroke="#176b73" '
            'stroke-width="4" stroke-dasharray="8 6"/>',
            '<text x="713" y="395" font-size="14" fill="#176b73">'
            "period-t opportunity</text>",
            '<text x="526" y="205" font-size="14" fill="#76528f">'
            "period-(t+1) opportunity</text>",
            '<line x1="823" y1="360" x2="648" y2="221" stroke="#76528f" '
            'stroke-width="2" stroke-dasharray="6 5"/>',
            '<text x="536" y="250" font-size="14" fill="#76528f">'
            "new-opportunity projection · D = 3/5</text>",
            '<line x1="682" y1="174" x2="758" y2="369" stroke="#d97732" '
            'stroke-width="2" stroke-dasharray="6 5" '
            'marker-end="url(#mlc-arrow)"/>',
            '<text x="692" y="282" font-size="14" fill="#d97732">'
            "old-opportunity replay</text>",
            '<text x="714" y="306" font-size="14" fill="#d97732">'
            "D = &#x2212;3/5</text>",
            '<circle cx="823" cy="360" r="7" fill="#176b73" '
            'stroke="#ffffff" stroke-width="2"/>',
            '<circle cx="682" cy="174" r="7" fill="#76528f" '
            'stroke="#ffffff" stroke-width="2"/>',
            '<text x="718" y="350" font-size="14" fill="#176b73">'
            "Plant(t) · D(t) = 0</text>",
            '<text x="692" y="164" font-size="14" fill="#76528f">'
            "Plant(t+1) · D(t+1) = 0</text>",
            '<rect x="482" y="458" width="366" height="76" rx="11" '
            'fill="#eee8f3" stroke="#c6b2d3"/>',
            '<text x="665" y="489" text-anchor="middle" font-size="19" '
            'font-weight="700" fill="#76528f">ML = 2 = EC 1 '
            "&#xD7; TC 2</text>",
            '<text x="665" y="516" text-anchor="middle" font-size="14" '
            'fill="#24323d">Both plans are contemporaneous benchmarks.</text>',
            '<rect x="28" y="581" width="844" height="42" rx="10" fill="#24323d"/>',
            '<text x="450" y="608" text-anchor="middle" font-size="15" '
            'font-weight="700" fill="#ffffff">EC and TC allocate benchmark '
            "change; neither identifies the cause of change.</text>",
            "</g>",
            "</svg>",
        ]
    )


def hicks_moorsteen_accounting() -> str:
    """Show the two bilateral quantity accounts behind Hicks--Moorsteen."""
    return "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="650" '
            'viewBox="0 0 900 650" role="img" '
            'aria-labelledby="title description">',
            '<title id="title">Hicks--Moorsteen total-factor-productivity '
            "accounting</title>",
            '<desc id="description">Hicks--Moorsteen total-factor-productivity '
            "change from t to t+1 is the ratio of a bilateral output quantity "
            "index to a bilateral input quantity index. Each period technology "
            "supplies one output and one input quantity comparison.</desc>",
            "<defs>",
            '<filter id="hm-shadow" x="-10%" y="-10%" width="120%" '
            'height="130%"><feDropShadow dx="0" dy="2" stdDeviation="3" '
            'flood-color="#24323d" flood-opacity="0.12"/></filter>',
            "</defs>",
            '<rect width="900" height="650" fill="#ffffff"/>',
            '<g font-family="Arial, sans-serif">',
            '<text x="450" y="39" text-anchor="middle" font-size="24" '
            'font-weight="700" fill="#24323d">Hicks--Moorsteen '
            "total-factor-productivity change</text>",
            '<rect x="38" y="66" width="824" height="94" rx="15" '
            'fill="#eef6f7" stroke="#176b73" stroke-width="2" '
            'filter="url(#hm-shadow)"/>',
            '<text x="450" y="104" text-anchor="middle" font-size="16" '
            'font-weight="700" fill="#176b73">HM^(t,t+1) = output quantity '
            "index Q_y^(t,t+1) / input quantity index Q_x^(t,t+1)</text>",
            '<text x="450" y="136" text-anchor="middle" font-size="15" '
            'fill="#40515c">Productivity rises when output quantity grows '
            "faster than input quantity.</text>",
            '<rect x="35" y="190" width="405" height="282" rx="16" '
            'fill="#f2f8f8" stroke="#176b73" stroke-width="2.5" '
            'filter="url(#hm-shadow)"/>',
            '<text x="59" y="224" font-size="18" font-weight="700" '
            'fill="#176b73">Base-period perspective: &#x1D4AF;^t</text>',
            '<text x="59" y="250" font-size="14" fill="#40515c">'
            "The base-period opportunities judge both quantity bundles.</text>",
            '<rect x="59" y="272" width="357" height="76" rx="10" '
            'fill="#ffffff" stroke="#9cc8cc"/>',
            '<text x="79" y="303" font-size="17" font-weight="700" '
            'fill="#176b73">Output quantity, Q_y^t</text>',
            '<text x="79" y="330" font-size="14" fill="#40515c">'
            "Hold x^t fixed; compare y^t with y^(t+1)</text>",
            '<rect x="59" y="365" width="357" height="76" rx="10" '
            'fill="#ffffff" stroke="#9cc8cc"/>',
            '<text x="79" y="396" font-size="17" font-weight="700" '
            'fill="#176b73">Input quantity, Q_x^t</text>',
            '<text x="79" y="423" font-size="14" fill="#40515c">'
            "Hold y^t fixed; compare x^t with x^(t+1)</text>",
            '<rect x="460" y="190" width="405" height="282" rx="16" '
            'fill="#f5f1f8" stroke="#76528f" stroke-width="2.5" '
            'filter="url(#hm-shadow)"/>',
            '<text x="484" y="224" font-size="16" font-weight="700" '
            'fill="#76528f">Comparison-period perspective: '
            "&#x1D4AF;^(t+1)</text>",
            '<text x="484" y="250" font-size="14" fill="#40515c">'
            "Later opportunities supply the second bilateral view.</text>",
            '<rect x="484" y="272" width="357" height="76" rx="10" '
            'fill="#ffffff" stroke="#c5b3d2"/>',
            '<text x="504" y="303" font-size="17" font-weight="700" '
            'fill="#76528f">Output quantity, Q_y^(t+1)</text>',
            '<text x="504" y="330" font-size="14" fill="#40515c">'
            "Hold x^(t+1) fixed; compare output bundles</text>",
            '<rect x="484" y="365" width="357" height="76" rx="10" '
            'fill="#ffffff" stroke="#c5b3d2"/>',
            '<text x="504" y="396" font-size="17" font-weight="700" '
            'fill="#76528f">Input quantity, Q_x^(t+1)</text>',
            '<text x="504" y="423" font-size="14" fill="#40515c">'
            "Hold y^(t+1) fixed; compare input bundles</text>",
            '<rect x="68" y="500" width="764" height="126" rx="16" '
            'fill="#fff7ef" stroke="#d97732" stroke-width="2" '
            'filter="url(#hm-shadow)"/>',
            '<text x="450" y="532" text-anchor="middle" font-size="18" '
            'font-weight="700" fill="#9a4d17">Reconcile the two period views '
            "symmetrically</text>",
            '<text x="450" y="565" text-anchor="middle" font-size="15" '
            'fill="#24323d">Q_y^(t,t+1) = &#x221A;(Q_y^t &#xD7; '
            "Q_y^(t+1))</text>",
            '<text x="450" y="591" text-anchor="middle" font-size="15" '
            'fill="#24323d">Q_x^(t,t+1) = &#x221A;(Q_x^t &#xD7; '
            "Q_x^(t+1))</text>",
            '<text x="450" y="616" text-anchor="middle" font-size="16" '
            'font-weight="700" fill="#24323d">HM^(t,t+1) = '
            "Q_y^(t,t+1) / Q_x^(t,t+1)</text>",
            "</g>",
            "</svg>",
        ]
    )


def four_distance_matrix(*, environmental: bool = False) -> str:
    title = (
        "Four environmental benchmark evaluations"
        if environmental
        else "Four cross-period distance evaluations"
    )
    subtitle = (
        "Each operating plan is evaluated against both periods' environmental "
        "production opportunities."
        if environmental
        else "A two-by-two matrix crosses observations from periods t and t plus "
        "one with technologies from the same two periods."
    )
    parts = _base(
        title,
        subtitle,
    )
    x_positions = [280, 505]
    y_positions = [190, 325]
    parts.extend(
        [
            f'<text x="{392}" y="{65}" text-anchor="middle" font-size="20" '
            f'font-weight="600" fill="{INK}">reference technology</text>',
            f'<text x="{x_positions[0] + 82}" y="{112}" text-anchor="middle" '
            f'font-size="21" fill="{TEAL}">T(t)</text>',
            f'<text x="{x_positions[1] + 82}" y="{112}" text-anchor="middle" '
            f'font-size="21" fill="{PURPLE}">T(t+1)</text>',
            f'<text x="{78}" y="{265}" text-anchor="middle" font-size="20" '
            f'font-weight="600" fill="{INK}" transform="rotate(-90 78 265)">'
            "evaluated observation</text>",
            f'<text x="{208}" y="{y_positions[0] + 48}" text-anchor="end" '
            f'font-size="21" fill="{TEAL}">z(t)</text>',
            f'<text x="{208}" y="{y_positions[1] + 48}" text-anchor="end" '
            f'font-size="21" fill="{PURPLE}">z(t+1)</text>',
        ]
    )
    symbol = "D" if environmental else "d"
    labels = [
        [f"{symbol}^t(z^t)", f"{symbol}^(t+1)(z^t)"],
        [f"{symbol}^t(z^(t+1))", f"{symbol}^(t+1)(z^(t+1))"],
    ]
    for row, y in enumerate(y_positions):
        for column, x in enumerate(x_positions):
            diagonal = row == column
            fill = PALE_TEAL if diagonal else PALE_ORANGE
            stroke = TEAL if diagonal else ORANGE
            parts.extend(
                [
                    f'<rect x="{x}" y="{y}" width="165" height="92" rx="12" '
                    f'fill="{fill}" stroke="{stroke}" stroke-width="3"/>',
                    f'<text x="{x + 82.5}" y="{y + 55}" text-anchor="middle" '
                    f'font-size="20" font-weight="600" fill="{INK}">'
                    f"{labels[row][column]}</text>",
                ]
            )
    parts.extend(
        [
            f'<rect x="{270}" y="{444}" width="24" height="16" '
            f'fill="{PALE_TEAL}" stroke="{TEAL}" stroke-width="2"/>',
            f'<text x="{304}" y="{458}" font-size="16" fill="{INK}">same-period</text>',
            f'<rect x="{470}" y="{444}" width="24" height="16" '
            f'fill="{PALE_ORANGE}" stroke="{ORANGE}" stroke-width="2"/>',
            f'<text x="{504}" y="{458}" font-size="16" '
            f'fill="{INK}">cross-period</text>',
        ]
    )
    parts.append("</svg>")
    return "\n".join(parts)


def reference_technology_windows() -> str:
    parts = _base(
        "Contemporaneous and global reference-information policies",
        "A contemporaneous period-specific policy lets each period's "
        "observations define its own best-practice benchmark. A full-horizon "
        "global policy lets "
        "observations from every declared period define one common benchmark.",
    )
    parts.append(
        f'<text x="380" y="31" text-anchor="middle" font-size="22" '
        f'font-weight="700" fill="{INK}">Which observations may define '
        "best practice?</text>"
    )
    x_values = [245, 410, 575]
    for x, label in zip(x_values, ["t", "t+1", "t+2"], strict=True):
        parts.extend(
            [
                f'<line x1="{x}" y1="{82}" x2="{x}" y2="{350}" '
                f'stroke="{GRID}" stroke-width="2" stroke-dasharray="5 6"/>',
                f'<circle cx="{x}" cy="{72}" r="8" fill="{INK}"/>',
                f'<text x="{x}" y="{61}" text-anchor="middle" font-size="18" '
                f'fill="{INK}">{label}</text>',
            ]
        )
    parts.extend(
        [
            f'<text x="24" y="124" font-size="15" font-weight="700" '
            f'fill="{TEAL}">PERIOD-SPECIFIC</text>',
            f'<text x="24" y="146" font-size="15" font-weight="700" '
            f'fill="{TEAL}">POLICY</text>',
            f'<text x="24" y="168" font-size="13" fill="{GRAY}">one benchmark</text>',
            f'<text x="24" y="187" font-size="13" fill="{GRAY}">for each period</text>',
            f'<text x="24" y="249" font-size="15" font-weight="700" '
            f'fill="{PURPLE}">FULL-HORIZON</text>',
            f'<text x="24" y="271" font-size="15" font-weight="700" '
            f'fill="{PURPLE}">GLOBAL POLICY</text>',
            f'<text x="24" y="293" font-size="13" fill="{GRAY}">'
            "one common benchmark</text>",
            f'<text x="24" y="312" font-size="13" fill="{GRAY}">'
            "for the declared horizon</text>",
        ]
    )
    for x, label in zip(x_values, ["T(t)", "T(t+1)", "T(t+2)"], strict=True):
        parts.extend(
            [
                f'<rect x="{x - 66}" y="{105}" width="132" height="80" rx="10" '
                f'fill="{PALE_TEAL}" stroke="{TEAL}" stroke-width="2"/>',
                f'<text x="{x}" y="{140}" text-anchor="middle" font-size="19" '
                f'fill="{TEAL}">{label}</text>',
                f'<text x="{x}" y="{164}" text-anchor="middle" font-size="13" '
                f'fill="{GRAY}">that period only</text>',
            ]
        )
    parts.extend(
        [
            f'<rect x="{179}" y="{230}" width="462" height="88" rx="12" '
            f'fill="#eee8f3" stroke="{PURPLE}" stroke-width="3"/>',
            f'<text x="410" y="267" text-anchor="middle" font-size="21" '
            f'font-weight="700" fill="{PURPLE}">T(G)</text>',
            f'<text x="410" y="293" text-anchor="middle" font-size="14" '
            f'fill="{GRAY}">observations from every declared period</text>',
            f'<line x1="70" y1="378" x2="690" y2="378" '
            f'stroke="{GRID}" stroke-width="2"/>',
            f'<text x="380" y="417" text-anchor="middle" font-size="15" '
            f'font-weight="600" fill="{INK}">The information policy decides '
            "what can define best practice—and what measured change means.</text>",
        ]
    )
    parts.append("</svg>")
    return "\n".join(parts)


def study_composition_map() -> str:
    parts = _base(
        "From a management question to a defensible conclusion",
        "A flow diagram shows purpose and commitments, organizational responsibility, "
        "and comparable evidence entering a comparison contract, which produces a "
        "performance finding, operating evidence, and a bounded conclusion.",
    )
    parts.extend(
        [
            f'<text x="{WIDTH / 2}" y="38" text-anchor="middle" font-size="22" '
            f'font-weight="700" fill="{INK}">A defensible performance study</text>',
            f'<text x="42" y="82" font-size="16" font-weight="700" fill="{TEAL}">'
            "Define the decision</text>",
            f'<text x="292" y="82" font-size="16" font-weight="700" fill="{PURPLE}">'
            "State the comparison</text>",
            f'<text x="570" y="82" font-size="16" font-weight="700" fill="{ORANGE}">'
            "Use the evidence</text>",
        ]
    )

    left_boxes = [
        (102, "Purpose and commitment", "what must remain or improve"),
        (202, "Responsibility and time", "what can change, and when"),
        (302, "Comparable evidence", "who may teach whom"),
    ]
    for y, title, subtitle in left_boxes:
        parts.extend(
            [
                f'<rect x="34" y="{y}" width="206" height="70" rx="10" '
                f'fill="{PALE_TEAL}" stroke="{TEAL}" stroke-width="2"/>',
                f'<text x="52" y="{y + 27}" font-size="16" font-weight="700" '
                f'fill="{INK}">{title}</text>',
                f'<text x="52" y="{y + 50}" font-size="12.5" fill="{GRAY}">'
                f"{subtitle}</text>",
            ]
        )

    parts.extend(
        [
            '<rect x="285" y="102" width="238" height="270" rx="13" '
            'fill="#eee8f3" stroke="#76528f" stroke-width="3"/>',
            f'<text x="404" y="130" text-anchor="middle" font-size="18" '
            f'font-weight="700" fill="{PURPLE}">Comparison contract</text>',
        ]
    )
    middle_rows = [
        (151, "unit and time boundary"),
        (197, "resources, services, harms"),
        (243, "eligible comparison group"),
        (289, "attainable-plan assumptions"),
        (335, "measure and conclusion limits"),
    ]
    for y, label in middle_rows:
        parts.extend(
            [
                f'<rect x="307" y="{y}" width="194" height="34" rx="7" '
                'fill="white" stroke="#cbbbd5" stroke-width="1.5"/>',
                f'<text x="404" y="{y + 22}" text-anchor="middle" font-size="13.5" '
                f'fill="{INK}">{label}</text>',
            ]
        )

    right_boxes = [
        (102, "Performance finding", "defined measure and benchmark"),
        (202, "Operating evidence", "targets, gaps, and peers"),
        (302, "Strength of conclusion", "uncertainty and limits"),
    ]
    for y, title, subtitle in right_boxes:
        parts.extend(
            [
                f'<rect x="566" y="{y}" width="166" height="70" rx="10" '
                f'fill="{PALE_ORANGE}" stroke="{ORANGE}" stroke-width="2"/>',
                f'<text x="582" y="{y + 27}" font-size="14" font-weight="700" '
                f'fill="{INK}">{title}</text>',
                f'<text x="582" y="{y + 50}" font-size="11.5" fill="{GRAY}">'
                f"{subtitle}</text>",
            ]
        )

    for y in (137, 237, 337):
        parts.extend(
            [
                f'<line x1="240" y1="{y}" x2="278" y2="{y}" stroke="{TEAL}" '
                'stroke-width="2.5" marker-end="url(#arrow-teal)"/>',
                f'<line x1="523" y1="{y}" x2="559" y2="{y}" stroke="{ORANGE}" '
                'stroke-width="2.5" marker-end="url(#arrow-orange)"/>',
            ]
        )

    parts.extend(
        [
            f'<rect x="94" y="414" width="572" height="54" rx="11" '
            f'fill="white" stroke="{GRID}" stroke-width="2"/>',
            f'<text x="{WIDTH / 2}" y="437" text-anchor="middle" font-size="14" '
            f'font-weight="700" fill="{INK}">Every result is conditional on the '
            "comparison contract</text>",
            f'<text x="{WIDTH / 2}" y="457" text-anchor="middle" font-size="12.5" '
            f'fill="{GRAY}">Change the contract, and the management question '
            "changes.</text>",
        ]
    )
    parts.append("</svg>")
    return "\n".join(parts)


def revenue_technical_allocative() -> str:
    """Return the five-unit VRS revenue-decomposition teaching figure."""
    return "\n".join(
        (
            '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="720" vi'
            'ewBox="0 0 1080 720" role="img" aria-labelledby="title description">',
            '  <title id="title">Observed, proportional expansion, and revenue-ma'
            "ximizing output plans</title>",
            '  <desc id="description">For Unit 1 in the five-unit variable-return'
            "s example, the observed output mix is seven units of output one and "
            "four of output two. A common proportional expansion reaches nine and"
            " thirty-six sevenths, while the revenue-maximizing feasible mix at o"
            "utput prices three and two is nine and nine. Parallel equal-revenue "
            "lines show observed revenue twenty-nine and maximum revenue forty-fi"
            "ve.</desc>",
            "  <defs>",
            '    <marker id="axis-arrow-revenue" markerWidth="9" markerHeight="9"'
            ' refX="8" refY="4" orient="auto">',
            '      <path d="M0,0 L0,8 L8,4 z" fill="#24323d"/>',
            "    </marker>",
            '    <marker id="arrow-orange-revenue" markerWidth="10" markerHeight='
            '"10" refX="8" refY="3" orient="auto">',
            '      <path d="M0,0 L0,6 L9,3 z" fill="#d97732"/>',
            "    </marker>",
            '    <marker id="arrow-purple-revenue" markerWidth="10" markerHeight='
            '"10" refX="8" refY="3" orient="auto">',
            '      <path d="M0,0 L0,6 L9,3 z" fill="#76528f"/>',
            "    </marker>",
            '    <filter id="shadow-revenue" x="-15%" y="-15%" width="130%" heigh'
            't="130%">',
            '      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#243'
            '23d" flood-opacity="0.12"/>',
            "    </filter>",
            "  </defs>",
            "",
            '  <rect width="1080" height="720" fill="#ffffff"/>',
            '  <text x="62" y="38" font-family="Arial, sans-serif" font-size="19"'
            ' font-weight="700" fill="#24323d">Unit 1 · fixed input capacity unde'
            "r VRS</text>",
            '  <text x="62" y="64" font-family="Arial, sans-serif" font-size="15"'
            ' fill="#5c6b73">Output prices: p₁ = 3 and p₂ = 2 · one unit of outpu'
            "t 1 earns 50% more</text>",
            "",
            '  <g font-family="Arial, sans-serif">',
            '    <line x1="80" y1="590" x2="612" y2="590" stroke="#24323d" stroke'
            '-width="2" marker-end="url(#axis-arrow-revenue)"/>',
            '    <line x1="80" y1="590" x2="80" y2="84" stroke="#24323d" stroke-w'
            'idth="2" marker-end="url(#axis-arrow-revenue)"/>',
            '    <text x="619" y="598" font-size="18" font-style="italic" fill="#'
            '24323d">output y₁</text>',
            '    <text x="68" y="76" text-anchor="end" font-size="18" font-style='
            '"italic" fill="#24323d">output y₂</text>',
            "",
            '    <g stroke="#e1e8ea" stroke-width="1">',
            '      <line x1="166" y1="106" x2="166" y2="590"/>',
            '      <line x1="252" y1="106" x2="252" y2="590"/>',
            '      <line x1="338" y1="106" x2="338" y2="590"/>',
            '      <line x1="424" y1="106" x2="424" y2="590"/>',
            '      <line x1="510" y1="106" x2="510" y2="590"/>',
            '      <line x1="596" y1="106" x2="596" y2="590"/>',
            '      <line x1="80" y1="498" x2="596" y2="498"/>',
            '      <line x1="80" y1="406" x2="596" y2="406"/>',
            '      <line x1="80" y1="314" x2="596" y2="314"/>',
            '      <line x1="80" y1="222" x2="596" y2="222"/>',
            '      <line x1="80" y1="130" x2="596" y2="130"/>',
            "    </g>",
            "",
            '    <g fill="#65757d" font-size="13">',
            '      <text x="166" y="612" text-anchor="middle">2</text>',
            '      <text x="252" y="612" text-anchor="middle">4</text>',
            '      <text x="338" y="612" text-anchor="middle">6</text>',
            '      <text x="424" y="612" text-anchor="middle">8</text>',
            '      <text x="510" y="612" text-anchor="middle">10</text>',
            '      <text x="596" y="612" text-anchor="middle">12</text>',
            '      <text x="62" y="503" text-anchor="end">2</text>',
            '      <text x="62" y="411" text-anchor="end">4</text>',
            '      <text x="62" y="319" text-anchor="end">6</text>',
            '      <text x="62" y="227" text-anchor="end">8</text>',
            '      <text x="62" y="135" text-anchor="end">10</text>',
            "    </g>",
            "",
            '    <path d="M80 590 L467 590 L467 176 L424 130 L80 130 Z" fill="#e9'
            'f4f3" fill-opacity="0.78"/>',
            '    <text x="110" y="183" font-size="14" fill="#43747a">output plans'
            " attainable with Unit 1's inputs</text>",
            "",
            '    <path d="M424 130 L467 176" fill="none" stroke="#176b73" stroke-'
            'width="5" stroke-linecap="round"/>',
            '    <text x="400" y="108" font-size="14" font-weight="700" fill="#17'
            '6b73">best-practice output menu</text>',
            '    <path d="M467 176 L467 590" fill="none" stroke="#6e9da0" stroke-'
            'width="2" stroke-dasharray="5 5"/>',
            "",
            '    <path d="M209 130 L496 590" fill="none" stroke="#9ba8ae" stroke-'
            'width="2" stroke-dasharray="7 6"/>',
            '    <text x="270" y="232" font-size="13" fill="#687780" transform="r'
            'otate(58 270 232)">observed revenue line: R = 29</text>',
            "",
            '    <path d="M438.3 130 L596 383" fill="none" stroke="#76528f" strok'
            'e-width="2.5" stroke-dasharray="7 5"/>',
            '    <text x="503" y="225" font-size="13" fill="#66427c" transform="r'
            'otate(58 503 225)">maximum revenue line: R* = 45</text>',
            "",
            '    <line x1="80" y1="590" x2="467" y2="353.4" stroke="#d9a276" stro'
            'ke-width="2" stroke-dasharray="6 5"/>',
            '    <line x1="386" y1="399" x2="457" y2="356" stroke="#d97732" strok'
            'e-width="3.5" marker-end="url(#arrow-orange-revenue)"/>',
            '    <line x1="467" y1="341" x2="467" y2="190" stroke="#76528f" strok'
            'e-width="3.5" marker-end="url(#arrow-purple-revenue)"/>',
            "",
            '    <circle cx="381" cy="406" r="9" fill="#24323d" stroke="#ffffff" '
            'stroke-width="3"/>',
            '    <circle cx="467" cy="353.4" r="9" fill="#d97732" stroke="#ffffff'
            '" stroke-width="3"/>',
            '    <circle cx="467" cy="176" r="9" fill="#76528f" stroke="#ffffff" '
            'stroke-width="3"/>',
            '    <circle cx="424" cy="130" r="6" fill="#176b73" stroke="#ffffff" '
            'stroke-width="2"/>',
            '    <text x="365" y="432" font-size="17" font-weight="700" fill="#24'
            '323d">O</text>',
            '    <text x="478" y="359" font-size="17" font-weight="700" fill="#b5'
            '5f23">P</text>',
            '    <text x="478" y="170" font-size="17" font-weight="700" fill="#66'
            '427c">M</text>',
            '    <text x="397" y="148" font-size="12" fill="#176b73">Unit 3</text>',
            "",
            '    <g filter="url(#shadow-revenue)">',
            '      <rect x="674" y="91" width="355" height="135" rx="10" fill="#f'
            '5f7f8" stroke="#cbd5d9"/>',
            '      <rect x="674" y="268" width="355" height="146" rx="10" fill="#'
            'fff7ef" stroke="#e4a46f"/>',
            '      <rect x="674" y="456" width="355" height="153" rx="10" fill="#'
            'f7f1fa" stroke="#a98abb"/>',
            "    </g>",
            "",
            '    <g fill="#24323d">',
            '      <text x="696" y="120" font-size="17" font-weight="700">O · Obs'
            "erved service portfolio</text>",
            '      <text x="696" y="151" font-size="16">(y₁, y₂) = (7, 4)</text>',
            '      <text x="696" y="178" font-size="16">Revenue = 3(7) + 2(4) = 2'
            "9</text>",
            '      <text x="696" y="205" font-size="14" fill="#5c6b73">What the o'
            "rganization currently delivers</text>",
            "",
            '      <text x="696" y="297" font-size="17" font-weight="700" fill="#'
            'a65119">P · Proportional capacity execution</text>',
            '      <text x="696" y="328" font-size="16">(y₁, y₂) = (9, 36/7)</text>',
            '      <text x="696" y="355" font-size="16">φ = 9/7 · TEᴼ = 7/9</text>',
            '      <text x="696" y="382" font-size="14" fill="#7b604a">Same outpu'
            "t mix, expanded in common proportion</text>",
            "",
            '      <text x="696" y="485" font-size="17" font-weight="700" fill="#'
            '66427c">M · Revenue-maximizing activity</text>',
            '      <text x="696" y="516" font-size="16">(y₁, y₂) = (9, 9) · R* = '
            "45</text>",
            '      <text x="696" y="543" font-size="16">RE = 29/45 · AEᴿ = 29/35<'
            "/text>",
            '      <text x="696" y="570" font-size="14" fill="#66556f">Different '
            "mix, chosen at supplied prices</text>",
            '      <text x="696" y="592" font-size="13" fill="#66556f">Technology'
            " and prices jointly determine M</text>",
            "    </g>",
            "",
            '    <text x="80" y="658" font-size="14" fill="#5c6b73">O→P diagnoses'
            " common capacity execution; P→M reveals additional value from nonrad"
            "ial expansion and output reallocation.</text>",
            '    <text x="80" y="684" font-size="13" fill="#687780">The arrows or'
            "ganize the comparison. They are not a required sequence of manageria"
            "l actions.</text>",
            "  </g>",
            "</svg>",
        )
    )


def profit_recovery_bridge() -> str:
    """Return the four-plan VRS profit-recovery teaching figure."""
    return "\n".join(
        (
            '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="680" '
            'viewBox="0 0 1080 680" role="img" '
            'aria-labelledby="title description">',
            '  <title id="title">Plan D profit-recovery bridge</title>',
            '  <desc id="description">Plan D earns profit seven. A feasible '
            "directional operating benchmark earns twenty-three, recovering sixteen "
            "through resource saving and service expansion. The profit-maximizing "
            "Plan B earns twenty-seven, leaving four attributable to the "
            "price-responsive input-output allocation. A stacked bar divides the "
            "total profit gap of twenty into those two components.</desc>",
            "  <defs>",
            '    <filter id="shadow-profit" x="-15%" y="-15%" width="130%" '
            'height="130%">',
            '      <feDropShadow dx="0" dy="2" stdDeviation="3" '
            'flood-color="#24323d" flood-opacity="0.12"/>',
            "    </filter>",
            "  </defs>",
            "",
            '  <rect width="1080" height="680" fill="#ffffff"/>',
            '  <g font-family="Arial, sans-serif">',
            '    <text x="50" y="40" font-size="21" font-weight="700" '
            'fill="#24323d">Where Plan D leaves 20 profit units unrealized</text>',
            '    <text x="50" y="68" font-size="15" fill="#5c6b73">VRS technology · '
            "input price w = 2 · output prices p₁ = 3 and p₂ = 5</text>",
            "",
            '    <g filter="url(#shadow-profit)">',
            '      <rect x="42" y="102" width="300" height="292" rx="12" '
            'fill="#f5f7f8" stroke="#cbd5d9"/>',
            '      <rect x="390" y="102" width="300" height="292" rx="12" '
            'fill="#fff7ef" stroke="#e4a46f"/>',
            '      <rect x="738" y="102" width="300" height="292" rx="12" '
            'fill="#f7f1fa" stroke="#a98abb"/>',
            "    </g>",
            "",
            '    <rect x="42" y="102" width="300" height="58" rx="12" fill="#e9eef0"/>',
            '    <rect x="390" y="102" width="300" height="58" rx="12" '
            'fill="#f8e8dc"/>',
            '    <rect x="738" y="102" width="300" height="58" rx="12" '
            'fill="#eee4f3"/>',
            '    <rect x="42" y="146" width="300" height="14" fill="#e9eef0"/>',
            '    <rect x="390" y="146" width="300" height="14" fill="#f8e8dc"/>',
            '    <rect x="738" y="146" width="300" height="14" fill="#eee4f3"/>',
            "",
            '    <text x="64" y="137" font-size="19" font-weight="700" '
            'fill="#24323d">Current Plan D</text>',
            '    <text x="412" y="137" font-size="19" font-weight="700" '
            'fill="#a65119">Operating benchmark T</text>',
            '    <text x="760" y="137" font-size="19" font-weight="700" '
            'fill="#66427c">Profit-maximizing Plan B</text>',
            "",
            '    <g font-size="16" fill="#24323d">',
            '      <text x="64" y="193">Resource input: 6.0</text>',
            '      <text x="64" y="220">Standard service: 3.0</text>',
            '      <text x="64" y="247">Premium service: 2.0</text>',
            '      <text x="64" y="286">Revenue: 19.0</text>',
            '      <text x="64" y="313">Cost: 12.0</text>',
            "",
            '      <text x="412" y="193">Resource input: 4.4</text>',
            '      <text x="412" y="220">Standard service: 4.6</text>',
            '      <text x="412" y="247">Premium service: 3.6</text>',
            '      <text x="412" y="286">Revenue: 31.8</text>',
            '      <text x="412" y="313">Cost: 8.8</text>',
            "",
            '      <text x="760" y="193">Resource input: 5.0</text>',
            '      <text x="760" y="220">Standard service: 4.0</text>',
            '      <text x="760" y="247">Premium service: 5.0</text>',
            '      <text x="760" y="286">Revenue: 37.0</text>',
            '      <text x="760" y="313">Cost: 10.0</text>',
            "    </g>",
            "",
            '    <text x="64" y="365" font-size="25" font-weight="700" '
            'fill="#24323d">Profit = 7</text>',
            '    <text x="412" y="365" font-size="25" font-weight="700" '
            'fill="#a65119">Profit = 23</text>',
            '    <text x="760" y="365" font-size="25" font-weight="700" '
            'fill="#66427c">Profit = 27</text>',
            "",
            '    <text x="50" y="433" font-size="14" font-weight="700" '
            'fill="#5c6b73">ACCOUNTING BRIDGE — NOT A REQUIRED IMPLEMENTATION '
            "SEQUENCE</text>",
            '    <line x1="190" y1="473" x2="540" y2="473" stroke="#d97732" '
            'stroke-width="7" stroke-linecap="round"/>',
            '    <line x1="540" y1="473" x2="888" y2="473" stroke="#76528f" '
            'stroke-width="7" stroke-linecap="round"/>',
            '    <circle cx="190" cy="473" r="10" fill="#24323d" '
            'stroke="#ffffff" stroke-width="3"/>',
            '    <circle cx="540" cy="473" r="10" fill="#d97732" '
            'stroke="#ffffff" stroke-width="3"/>',
            '    <circle cx="888" cy="473" r="10" fill="#76528f" '
            'stroke="#ffffff" stroke-width="3"/>',
            '    <text x="365" y="458" text-anchor="middle" font-size="16" '
            'font-weight="700" fill="#a65119">+16 operating recovery</text>',
            '    <text x="714" y="458" text-anchor="middle" font-size="16" '
            'font-weight="700" fill="#66427c">+4 allocation recovery</text>',
            '    <text x="190" y="503" text-anchor="middle" font-size="14" '
            'fill="#24323d">7</text>',
            '    <text x="540" y="503" text-anchor="middle" font-size="14" '
            'fill="#a65119">23</text>',
            '    <text x="888" y="503" text-anchor="middle" font-size="14" '
            'fill="#66427c">27</text>',
            "",
            '    <text x="50" y="548" font-size="17" font-weight="700" '
            'fill="#24323d">Total attainable profit recovery = 20</text>',
            '    <rect x="50" y="565" width="784" height="54" rx="8" fill="#d97732"/>',
            '    <path d="M834 565 H1022 Q1030 565 1030 573 V611 '
            'Q1030 619 1022 619 H834 Z" fill="#76528f"/>',
            '    <text x="442" y="598" text-anchor="middle" font-size="17" '
            'font-weight="700" fill="#ffffff">16 technical · 80%</text>',
            '    <text x="932" y="598" text-anchor="middle" font-size="17" '
            'font-weight="700" fill="#ffffff">4 allocative · 20%</text>',
            '    <text x="50" y="652" font-size="14" fill="#5c6b73">One declared '
            "improvement package is worth 10 · Nerlovian profit inefficiency "
            "= 2.0 = 1.6 + 0.4</text>",
            "  </g>",
            "</svg>",
        )
    )


def economic_objectives_management_map() -> str:
    """Return one-case map of the core observed-price efficiency questions."""
    return "\n".join(
        (
            '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="720" '
            'viewBox="0 0 1080 720" role="img" '
            'aria-labelledby="title description">',
            '  <title id="title">One operating plan, three core price-informed '
            "decisions and one directional bridge</title>",
            '  <desc id="description">Observed Plan D uses six resource units '
            "to provide three standard and two premium services. A minimum-cost "
            "comparison preserves its service commitments, a maximum-revenue "
            "comparison preserves its resource capacity, a maximum-profit "
            "comparison chooses both sides jointly. These three core decisions "
            "appear as the primary cards. A smaller secondary directional bridge "
            "then values one declared improvement package against the profit gap. "
            "All accounts use the same four-plan VRS technology.</desc>",
            "  <defs>",
            '    <marker id="arrow-economic-teal" markerWidth="10" '
            'markerHeight="10" refX="8" refY="3" orient="auto" '
            'markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" '
            'fill="#176b73"/></marker>',
            '    <marker id="arrow-economic-orange" markerWidth="10" '
            'markerHeight="10" refX="8" refY="3" orient="auto" '
            'markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" '
            'fill="#d97732"/></marker>',
            '    <marker id="arrow-economic-purple" markerWidth="10" '
            'markerHeight="10" refX="8" refY="3" orient="auto" '
            'markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" '
            'fill="#76528f"/></marker>',
            '    <filter id="shadow-economic" x="-15%" y="-15%" '
            'width="130%" height="130%"><feDropShadow dx="0" dy="2" '
            'stdDeviation="3" flood-color="#24323d" '
            'flood-opacity="0.12"/></filter>',
            "  </defs>",
            '  <rect width="1080" height="720" fill="#ffffff"/>',
            '  <g font-family="Arial, sans-serif">',
            '    <text x="540" y="36" text-anchor="middle" font-size="22" '
            'font-weight="700" fill="#24323d">The objective determines what '
            "counts as an improvement</text>",
            '    <text x="540" y="63" text-anchor="middle" font-size="15" '
            'fill="#5c6b73">Same four-plan VRS technology · w = 2 · '
            "p = (3, 5)</text>",
            "",
            '    <g filter="url(#shadow-economic)">',
            '      <rect x="353" y="82" width="374" height="142" rx="14" '
            'fill="#f5f7f8" stroke="#aebbc1" stroke-width="1.5"/>',
            "    </g>",
            '    <text x="540" y="113" text-anchor="middle" font-size="18" '
            'font-weight="700" fill="#24323d">Observed Plan D</text>',
            '    <text x="540" y="142" text-anchor="middle" font-size="16" '
            'fill="#24323d">resource x = 6 · services y = (3, 2)</text>',
            '    <text x="540" y="170" text-anchor="middle" font-size="16" '
            'fill="#24323d">cost = 12 · revenue = 19 · profit = 7</text>',
            '    <text x="540" y="203" text-anchor="middle" font-size="14" '
            'fill="#5c6b73">Which opportunity matters depends on the decision '
            "question.</text>",
            "",
            '    <path d="M458 224 C390 249 279 254 184 291" fill="none" '
            'stroke="#176b73" stroke-width="3" '
            'marker-end="url(#arrow-economic-teal)"/>',
            '    <path d="M540 224 L540 289" fill="none" stroke="#d97732" '
            'stroke-width="3" marker-end="url(#arrow-economic-orange)"/>',
            '    <path d="M622 224 C690 249 801 254 896 291" fill="none" '
            'stroke="#76528f" stroke-width="3" '
            'marker-end="url(#arrow-economic-purple)"/>',
            '    <text x="272" y="253" text-anchor="middle" font-size="12.5" '
            'font-weight="700" fill="#176b73">preserve service commitments</text>',
            '    <text x="540" y="253" text-anchor="middle" font-size="12.5" '
            'font-weight="700" fill="#a65119">preserve resource capacity</text>',
            '    <text x="808" y="253" text-anchor="middle" font-size="12.5" '
            'font-weight="700" fill="#66427c">choose inputs and outputs jointly</text>',
            "",
            '    <g filter="url(#shadow-economic)">',
            '      <rect x="30" y="300" width="320" height="236" rx="14" '
            'fill="#eef7f7" stroke="#73aeb3"/>',
            '      <rect x="380" y="300" width="320" height="236" rx="14" '
            'fill="#fff7ef" stroke="#e4a46f"/>',
            '      <rect x="730" y="300" width="320" height="236" rx="14" '
            'fill="#f7f1fa" stroke="#a98abb"/>',
            "    </g>",
            '    <rect x="30" y="300" width="320" height="55" rx="14" fill="#dceff0"/>',
            '    <rect x="380" y="300" width="320" height="55" rx="14" '
            'fill="#f8e8dc"/>',
            '    <rect x="730" y="300" width="320" height="55" rx="14" '
            'fill="#eee4f3"/>',
            '    <rect x="30" y="341" width="320" height="14" fill="#dceff0"/>',
            '    <rect x="380" y="341" width="320" height="14" fill="#f8e8dc"/>',
            '    <rect x="730" y="341" width="320" height="14" fill="#eee4f3"/>',
            "",
            '    <text x="190" y="335" text-anchor="middle" font-size="18" '
            'font-weight="700" fill="#176b73">Minimum cost</text>',
            '    <text x="540" y="335" text-anchor="middle" font-size="18" '
            'font-weight="700" fill="#a65119">Maximum revenue</text>',
            '    <text x="890" y="335" text-anchor="middle" font-size="18" '
            'font-weight="700" fill="#66427c">Maximum profit</text>',
            "",
            '    <g font-size="15" fill="#24323d">',
            '      <text x="52" y="391">Target: 0.25B + 0.75C</text>',
            '      <text x="52" y="421">x̂ = 3.5 · ŷ = (4.75, 2)</text>',
            '      <text x="52" y="461">minimum cost = 7</text>',
            '      <text x="52" y="491">cost efficiency = 7/12</text>',
            '      <text x="52" y="521">technical = 7/12 · allocative = 1</text>',
            "",
            '      <text x="402" y="391">Resource envelope: x ≤ 6</text>',
            '      <text x="402" y="421">Target B: x̂ = 5 · ŷ = (4, 5)</text>',
            '      <text x="402" y="461">maximum revenue = 37</text>',
            '      <text x="402" y="491">observed revenue = 19</text>',
            '      <text x="402" y="521">revenue efficiency = 19/37</text>',
            "",
            '      <text x="752" y="391">Inputs and outputs may change</text>',
            '      <text x="752" y="421">Target B: x̂ = 5 · ŷ = (4, 5)</text>',
            '      <text x="752" y="461">maximum profit = 27</text>',
            '      <text x="752" y="491">observed profit = 7</text>',
            '      <text x="752" y="521">profit gap = 20</text>',
            "    </g>",
            "",
            '    <path d="M890 536 C890 557 824 558 824 575" fill="none" '
            'stroke="#9aa8ae" stroke-width="2" stroke-dasharray="5 5" '
            'marker-end="url(#arrow-economic-purple)"/>',
            '    <text x="810" y="558" text-anchor="end" font-size="11.5" '
            'font-weight="700" fill="#687780">interpret part of the profit gap</text>',
            '    <rect x="230" y="579" width="620" height="96" rx="10" '
            'fill="#f6f4f7" stroke="#c9bdcf" stroke-width="1"/>',
            '    <text x="250" y="601" font-size="11" font-weight="700" '
            'letter-spacing="0.8" fill="#687780">SECONDARY INTERPRETIVE BRIDGE</text>',
            '    <text x="250" y="625" font-size="15" font-weight="700" '
            'fill="#66427c">Directional target T: x̂ = 4.4 · ŷ = (4.6, 3.6) '
            "· profit at T = 23</text>",
            '    <text x="250" y="647" font-size="14" fill="#24323d">profit '
            "recovery = 16 technical + 4 allocative · ν = 10</text>",  # noqa: RUF001
            '    <text x="250" y="668" font-size="14" fill="#24323d">'
            "NI = 2.0 = 1.6 + 0.4 programme units</text>",
            "",
            '    <text x="540" y="692" text-anchor="middle" font-size="13" '
            'fill="#5c6b73">Prices convert quantities into value; the technology '
            "still determines which alternatives are feasible.</text>",
            '    <text x="540" y="712" text-anchor="middle" font-size="12" '
            'fill="#687780">These conditional comparisons neither identify the '
            "cause of a gap nor prescribe an implementation path.</text>",
            "  </g>",
            "</svg>",
        )
    )


def profitability_diagnostic_dashboard() -> str:
    """Return an economics-first profitability diagnostic dashboard."""
    cards = (
        {
            "name": "B · best operating model",
            "quantities": "x = 4 · y = (4, 4)",
            "account": "Cost 4 · Revenue 12 · Revenue per £1 = 3.00",
            "score": "1.00",
            "factors": (("Operations", "1.00"), ("Scale", "1.00"), ("Mix", "1.00")),
            "action": "Protect the operating model and learn from it",
            "color": TEAL,
        },
        {
            "name": "A · offering-mix issue",
            "quantities": "x = 4 · y = (6, 1)",
            "account": "Cost 4 · Revenue 8 · Revenue per £1 = 2.00",
            "score": "0.67",
            "factors": (("Operations", "1.00"), ("Scale", "1.00"), ("Mix", "0.67")),
            "action": "Rebalance the service portfolio",
            "color": ORANGE,
        },
        {
            "name": "S · scale issue",
            "quantities": "x = 1 · y = (0.25, 0.25)",
            "account": "Cost 1 · Revenue 0.75 · Revenue per £1 = 0.75",
            "score": "0.25",
            "factors": (("Operations", "1.00"), ("Scale", "0.25"), ("Mix", "1.00")),
            "action": "Revisit footprint, demand, and capacity",
            "color": PURPLE,
        },
        {
            "name": "T · operating-process issue",
            "quantities": "x = 8 · y = (2, 2)",
            "account": "Cost 8 · Revenue 6 · Revenue per £1 = 0.75",
            "score": "0.25",
            "factors": (("Operations", "0.25"), ("Scale", "1.00"), ("Mix", "1.00")),
            "action": "Redesign the operating process",
            "color": BLUE,
        },
    )
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="700" '
        'viewBox="0 0 1080 700" role="img" '
        'aria-labelledby="title description">',
        '  <title id="title">Return-on-cost diagnostic dashboard</title>',
        '  <desc id="description">Four organizations are compared by cost, '
        "revenue per unit of cost, overall profitability efficiency, and "
        "operating, scale, and offering-mix factors. Organizations S and T "
        "both score one quarter overall but require different management "
        "responses.</desc>",
        "  <defs>",
        '    <filter id="shadow-rtd" x="-10%" y="-10%" width="120%" height="125%">',
        '      <feDropShadow dx="0" dy="2" stdDeviation="3" '
        'flood-color="#24323d" flood-opacity="0.12"/>',
        "    </filter>",
        "  </defs>",
        '  <rect width="1080" height="700" fill="#ffffff"/>',
        '  <g font-family="Arial, sans-serif">',
        '    <text x="44" y="42" font-size="22" font-weight="700" '
        'fill="#24323d">The same profitability score can conceal a different '
        "management problem</text>",
        '    <text x="44" y="69" font-size="15" fill="#5c6b73">'
        "One input at w = 1 · two services at p = (1, 2) · best revenue per £1 "
        "= 3.00</text>",
    ]
    for index, card in enumerate(cards):
        column = index % 2
        row = index // 2
        x = 44 + 512 * column
        y = 94 + 252 * row
        color = card["color"]
        parts.extend(
            [
                '    <g filter="url(#shadow-rtd)">',
                f'      <rect x="{x}" y="{y}" width="480" height="222" rx="12" '
                'fill="#f8fafb" stroke="#d5dee2"/>',
                "    </g>",
                f'    <rect x="{x}" y="{y}" width="480" height="50" rx="12" '
                f'fill="{color}" opacity="0.13"/>',
                f'    <rect x="{x}" y="{y + 38}" width="480" height="12" '
                f'fill="{color}" opacity="0.13"/>',
                f'    <text x="{x + 18}" y="{y + 32}" font-size="18" '
                f'font-weight="700" fill="{color}">{card["name"]}</text>',
                f'    <text x="{x + 408}" y="{y + 32}" text-anchor="middle" '
                f'font-size="22" font-weight="700" fill="{color}">'
                f"{card['score']}</text>",
                f'    <text x="{x + 18}" y="{y + 76}" font-size="14" '
                f'fill="#5c6b73">{card["quantities"]}</text>',
                f'    <text x="{x + 18}" y="{y + 101}" font-size="15" '
                f'fill="#24323d">{card["account"]}</text>',
            ]
        )
        for factor_index, (label, value) in enumerate(card["factors"]):
            factor_x = x + 18 + 147 * factor_index
            value_is_issue = value != "1.00"
            fill = color if value_is_issue else "#e8f1f2"
            text_color = "#ffffff" if value_is_issue else TEAL
            parts.extend(
                [
                    f'    <rect x="{factor_x}" y="{y + 121}" width="132" '
                    f'height="48" rx="8" fill="{fill}" '
                    f'opacity="{"0.92" if value_is_issue else "1"}"/>',
                    f'    <text x="{factor_x + 66}" y="{y + 140}" '
                    f'text-anchor="middle" font-size="12" fill="{text_color}">'
                    f"{label}</text>",
                    f'    <text x="{factor_x + 66}" y="{y + 160}" '
                    f'text-anchor="middle" font-size="17" font-weight="700" '
                    f'fill="{text_color}">{value}</text>',
                ]
            )
        parts.extend(
            [
                f'    <text x="{x + 18}" y="{y + 200}" font-size="14" '
                f'font-weight="700" fill="{color}">Action: '
                f"{card['action']}</text>",
            ]
        )
    parts.extend(
        [
            '    <rect x="44" y="610" width="992" height="54" rx="10" fill="#eef3f4"/>',
            '    <text x="540" y="634" text-anchor="middle" font-size="16" '
            'font-weight="700" fill="#24323d">Overall profitability efficiency '
            "= Operations &#215; Scale &#215; Offering mix</text>",
            '    <text x="540" y="654" text-anchor="middle" font-size="13" '
            'fill="#5c6b73">S and T both score 0.25; one needs a scale decision, '
            "the other an operating redesign.</text>",
            "  </g>",
            "</svg>",
        ]
    )
    return "\n".join(parts)


def gdf_management_contracts() -> str:
    """Show three operating counterfactuals for one CRS productivity gap."""
    cards = (
        {
            "alpha": "&#945; = 0",
            "name": "Services held fixed",
            "resource": "Resources (x₁, x₂): (1, 2)",
            "service": "Services (y₁, y₂): (5, 4)",
            "burden": "Save 75% of every resource",
            "color": TEAL,
        },
        {
            "alpha": "&#945; = 0.5",
            "name": "Both margins assessed",
            "resource": "Resources (x₁, x₂): (2, 4)",
            "service": "Services (y₁, y₂): (10, 8)",
            "burden": "Halve resources and double services",
            "color": ORANGE,
        },
        {
            "alpha": "&#945; = 1",
            "name": "Resources held fixed",
            "resource": "Resources (x₁, x₂): (4, 8)",
            "service": "Services (y₁, y₂): (20, 16)",
            "burden": "Keep resources and quadruple services",
            "color": PURPLE,
        },
    )
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="650" '
        'viewBox="0 0 1080 650" role="img" '
        'aria-labelledby="title description">',
        '  <title id="title">Three operating counterfactuals for one productivity '
        "gap</title>",
        '  <desc id="description">DMU 4 has the same CRS generalized-distance '
        "score of one quarter under three alpha settings. The settings divide "
        "the assessed adjustment differently between resource saving and service "
        "growth.</desc>",
        "  <defs>",
        '    <filter id="shadow-gdf-contract" x="-10%" y="-10%" width="120%" '
        'height="125%">',
        '      <feDropShadow dx="0" dy="2" stdDeviation="3" '
        'flood-color="#24323d" flood-opacity="0.12"/>',
        "    </filter>",
        "  </defs>",
        '  <rect width="1080" height="650" fill="#ffffff"/>',
        '  <g font-family="Arial, sans-serif">',
        '    <text x="44" y="42" font-size="23" font-weight="700" '
        'fill="#24323d">One productivity gap, three operating counterfactuals</text>',
        '    <text x="44" y="70" font-size="15" fill="#5c6b73">DMU 4 today: '
        "resources (4, 8) · services (5, 4) · CRS technology</text>",
        '    <rect x="44" y="96" width="992" height="82" rx="12" '
        'fill="#eef3f4" stroke="#d5dee2"/>',
        '    <text x="68" y="126" font-size="14" font-weight="700" '
        'fill="#5c6b73">COMMON DIAGNOSIS</text>',
        '    <text x="68" y="157" font-size="22" font-weight="700" '
        'fill="#24323d">CRS productivity efficiency δ = 0.25</text>',
        '    <text x="1010" y="145" text-anchor="end" font-size="16" '
        'fill="#5c6b73">&#945; changes where the adjustment is recorded — not the '
        "total gap</text>",
    ]
    for index, card in enumerate(cards):
        x = 44 + 336 * index
        color = card["color"]
        parts.extend(
            [
                '    <g filter="url(#shadow-gdf-contract)">',
                f'      <rect x="{x}" y="212" width="320" height="314" rx="12" '
                'fill="#f8fafb" stroke="#d5dee2"/>',
                "    </g>",
                f'    <rect x="{x}" y="212" width="320" height="62" rx="12" '
                f'fill="{color}" opacity="0.14"/>',
                f'    <rect x="{x}" y="258" width="320" height="16" '
                f'fill="{color}" opacity="0.14"/>',
                f'    <text x="{x + 20}" y="240" font-size="21" '
                f'font-weight="700" fill="{color}">{card["alpha"]}</text>',
                f'    <text x="{x + 20}" y="263" font-size="14" '
                f'font-weight="700" fill="{color}">{card["name"]}</text>',
                f'    <text x="{x + 20}" y="315" font-size="15" '
                f'fill="#24323d">{card["resource"]}</text>',
                f'    <text x="{x + 20}" y="348" font-size="15" '
                f'fill="#24323d">{card["service"]}</text>',
                f'    <line x1="{x + 20}" y1="378" x2="{x + 300}" y2="378" '
                'stroke="#d5dee2"/>',
                f'    <text x="{x + 20}" y="410" font-size="13" '
                'font-weight="700" fill="#5c6b73">ASSESSED CHANGE</text>',
                f'    <text x="{x + 20}" y="444" font-size="17" '
                f'font-weight="700" fill="{color}">{card["burden"]}</text>',
                f'    <rect x="{x + 20}" y="474" width="280" height="30" '
                f'rx="15" fill="{color}" opacity="0.12"/>',
                f'    <text x="{x + 160}" y="495" text-anchor="middle" '
                f'font-size="14" font-weight="700" fill="{color}">δ = 0.25</text>',
            ]
        )
    parts.extend(
        [
            '    <rect x="44" y="560" width="992" height="55" rx="10" fill="#24323d"/>',
            '    <text x="540" y="584" text-anchor="middle" font-size="16" '
            'font-weight="700" fill="#ffffff">Choose &#945; to represent the '
            "study&apos;s adjustment path</text>",
            '    <text x="540" y="604" text-anchor="middle" font-size="13" '
            'fill="#dce5e7">Treat them as analyst-declared counterfactuals unless '
            "an institution has adopted one.</text>",
            "  </g>",
            "</svg>",
        ]
    )
    return "\n".join(parts)


def gdf_scale_assumptions() -> str:
    """Contrast CRS score invariance with VRS path-sensitive comparators."""
    rows = (
        {
            "alpha": "&#945; = 0",
            "contract": "Hold services fixed",
            "vrs": "0.750",
            "mix": "12.50% DMU 2 + 87.50% DMU 3",
        },
        {
            "alpha": "&#945; = 0.5",
            "contract": "Assess both margins",
            "vrs": "0.682",
            "mix": "23.86% DMU 2 + 76.14% DMU 3",
        },
        {
            "alpha": "&#945; = 1",
            "contract": "Hold resources fixed",
            "vrs": "0.778",
            "mix": "50.00% DMU 2 + 50.00% DMU 3",
        },
    )
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="650" '
        'viewBox="0 0 1080 650" role="img" '
        'aria-labelledby="title description">',
        '  <title id="title">Scale assumptions change the performance '
        "benchmark</title>",
        '  <desc id="description">For DMU 1, every alpha setting has the same '
        "CRS score of 0.636. Under VRS, scores and comparator mixes differ "
        "because observed operating scale cannot be freely replicated.</desc>",
        "  <defs>",
        '    <filter id="shadow-gdf-scale" x="-10%" y="-10%" width="120%" '
        'height="125%">',
        '      <feDropShadow dx="0" dy="2" stdDeviation="3" '
        'flood-color="#24323d" flood-opacity="0.12"/>',
        "    </filter>",
        "  </defs>",
        '  <rect width="1080" height="650" fill="#ffffff"/>',
        '  <g font-family="Arial, sans-serif">',
        '    <text x="44" y="42" font-size="23" font-weight="700" '
        'fill="#24323d">Scale policy determines whether &#945; changes the '
        "score</text>",
        '    <text x="44" y="70" font-size="15" fill="#5c6b73">DMU 1 in the '
        "five-unit example · three declared adjustment paths</text>",
        '    <g filter="url(#shadow-gdf-scale)">',
        '      <rect x="44" y="104" width="300" height="438" rx="12" '
        'fill="#eef7f7" stroke="#b7d7d9"/>',
        '      <rect x="372" y="104" width="664" height="438" rx="12" '
        'fill="#f8fafb" stroke="#d5dee2"/>',
        "    </g>",
        '    <text x="68" y="142" font-size="20" font-weight="700" '
        'fill="#176b73">CRS · scale can adjust</text>',
        '    <text x="396" y="142" font-size="20" font-weight="700" '
        'fill="#76528f">VRS · observed scale is binding</text>',
        '    <text x="68" y="181" font-size="14" fill="#5c6b73">One total '
        "productivity gap.</text>",
        '    <text x="68" y="202" font-size="14" fill="#5c6b73">Three '
        "operating counterfactuals.</text>",
        '    <rect x="68" y="220" width="252" height="110" rx="10" fill="#176b73"/>',
        '    <text x="194" y="259" text-anchor="middle" font-size="15" '
        'font-weight="700" fill="#dceff0">ALL THREE &#945; SETTINGS</text>',
        '    <text x="194" y="300" text-anchor="middle" font-size="34" '
        'font-weight="700" fill="#ffffff">δ = 0.636</text>',
        '    <text x="68" y="375" font-size="15" fill="#24323d">&#945; '
        "divides the measured adjustment</text>",
        '    <text x="68" y="397" font-size="15" fill="#24323d">between '
        "resources and services.</text>",
        '    <text x="68" y="432" font-size="15" fill="#24323d">CRS total '
        "productivity efficiency</text>",
        '    <text x="68" y="454" font-size="15" fill="#24323d">does not '
        "change.</text>",
        '    <text x="396" y="181" font-size="14" fill="#5c6b73">The path '
        "changes the diagnosed gap</text>",
        '    <text x="396" y="202" font-size="14" fill="#5c6b73">and the '
        "feasible peer mix.</text>",
        '    <text x="396" y="220" font-size="12" font-weight="700" '
        'fill="#5c6b73">ADJUSTMENT PATH</text>',
        '    <text x="680" y="220" font-size="12" font-weight="700" '
        'fill="#5c6b73">VRS SCORE</text>',
        '    <text x="796" y="220" font-size="12" font-weight="700" '
        'fill="#5c6b73">COMPARATOR MIX</text>',
    ]
    for index, row in enumerate(rows):
        y = 242 + 92 * index
        fill = "#ffffff" if index % 2 == 0 else "#f2f5f6"
        parts.extend(
            [
                f'    <rect x="396" y="{y}" width="616" height="76" rx="8" '
                f'fill="{fill}" stroke="#e0e7e9"/>',
                f'    <text x="414" y="{y + 25}" font-size="18" '
                f'font-weight="700" fill="#76528f">{row["alpha"]}</text>',
                f'    <text x="414" y="{y + 51}" font-size="14" '
                f'fill="#24323d">{row["contract"]}</text>',
                f'    <text x="722" y="{y + 45}" text-anchor="middle" '
                f'font-size="23" font-weight="700" fill="#76528f">'
                f"{row['vrs']}</text>",
                f'    <text x="804" y="{y + 43}" font-size="14" '
                f'fill="#24323d">{row["mix"]}</text>',
            ]
        )
    parts.extend(
        [
            '    <rect x="44" y="575" width="992" height="42" rx="9" fill="#24323d"/>',
            '    <text x="540" y="601" text-anchor="middle" font-size="15" '
            'font-weight="700" fill="#ffffff">A score is meaningful only after '
            "the scale policy and improvement contract are declared.</text>",
            "  </g>",
            "</svg>",
        ]
    )
    return "\n".join(parts)


def two_stage_responsibility_chain() -> str:
    """Show a linked production account before introducing network algebra."""
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="650" '
        'viewBox="0 0 1080 650" role="img" '
        'aria-labelledby="title description">',
        '  <title id="title">Two-stage organizational performance chain</title>',
        '  <desc id="description">External expenses support premium acquisition, '
        "premium measures are handed to profit generation under one shared "
        "internal value account, and final profits leave the system. Upstream "
        "and downstream stages may use different peer practices while their "
        "intermediate targets remain coordinated.</desc>",
        "  <defs>",
        '    <marker id="network-arrow" markerWidth="10" markerHeight="10" '
        'refX="9" refY="4" orient="auto">',
        '      <path d="M0,0 L0,8 L9,4 z" fill="#176b73"/>',
        "    </marker>",
        '    <filter id="shadow-network" x="-10%" y="-10%" width="120%" height="130%">',
        '      <feDropShadow dx="0" dy="2" stdDeviation="3" '
        'flood-color="#24323d" flood-opacity="0.12"/>',
        "    </filter>",
        "  </defs>",
        '  <rect width="1080" height="650" fill="#ffffff"/>',
        '  <g font-family="Arial, sans-serif">',
        '    <text x="40" y="42" font-size="23" font-weight="700" '
        'fill="#24323d">One organization, one connected production account</text>',
        '    <text x="40" y="70" font-size="15" fill="#5c6b73">The handoff is '
        "observed once, valued consistently, and benchmarked jointly.</text>",
        '    <rect x="40" y="91" width="1000" height="52" rx="10" fill="#24323d"/>',
        '    <text x="540" y="124" text-anchor="middle" font-size="20" '
        'font-weight="700" fill="#ffffff">System account: E = E₁ &#215; E₂</text>',
        '    <g filter="url(#shadow-network)">',
        '      <rect x="40" y="176" width="174" height="135" rx="12" '
        'fill="#eef3f4" stroke="#cfdadd"/>',
        '      <rect x="254" y="176" width="178" height="135" rx="12" '
        'fill="#eef7f7" stroke="#9fc8cb"/>',
        '      <rect x="472" y="176" width="176" height="135" rx="12" '
        'fill="#fff4e9" stroke="#e5b58f"/>',
        '      <rect x="688" y="176" width="178" height="135" rx="12" '
        'fill="#f3eef7" stroke="#c6b2d3"/>',
        '      <rect x="906" y="176" width="134" height="135" rx="12" '
        'fill="#eef3f4" stroke="#cfdadd"/>',
        "    </g>",
        '    <text x="127" y="204" text-anchor="middle" font-size="12" '
        'font-weight="700" fill="#687780">EXTERNAL RESOURCES</text>',
        '    <text x="62" y="239" font-size="15" fill="#24323d">Operation '
        "expenses</text>",
        '    <text x="62" y="270" font-size="15" fill="#24323d">Insurance '
        "expenses</text>",
        '    <text x="343" y="207" text-anchor="middle" font-size="12" '
        'font-weight="700" fill="#176b73">STAGE 1 · E₁</text>',
        '    <text x="343" y="247" text-anchor="middle" font-size="19" '
        'font-weight="700" fill="#176b73">Premium</text>',
        '    <text x="343" y="272" text-anchor="middle" font-size="19" '
        'font-weight="700" fill="#176b73">acquisition</text>',
        '    <text x="560" y="204" text-anchor="middle" font-size="12" '
        'font-weight="700" fill="#d97732">ONE HANDOFF · z</text>',
        '    <text x="494" y="239" font-size="15" fill="#24323d">Written '
        "premiums</text>",
        '    <text x="494" y="270" font-size="15" fill="#24323d">Reinsurance '
        "premiums</text>",
        '    <text x="777" y="207" text-anchor="middle" font-size="12" '
        'font-weight="700" fill="#76528f">STAGE 2 · E₂</text>',
        '    <text x="777" y="247" text-anchor="middle" font-size="19" '
        'font-weight="700" fill="#76528f">Profit</text>',
        '    <text x="777" y="272" text-anchor="middle" font-size="19" '
        'font-weight="700" fill="#76528f">generation</text>',
        '    <text x="973" y="204" text-anchor="middle" font-size="12" '
        'font-weight="700" fill="#687780">FINAL OUTCOMES</text>',
        '    <text x="925" y="239" font-size="14" fill="#24323d">Underwriting</text>',
        '    <text x="925" y="258" font-size="14" fill="#24323d">profit</text>',
        '    <text x="925" y="289" font-size="14" fill="#24323d">Investment '
        "profit</text>",
    ]
    for x1, x2 in ((214, 254), (432, 472), (648, 688), (866, 906)):
        parts.append(
            f'    <line x1="{x1}" y1="244" x2="{x2 - 8}" y2="244" '
            'stroke="#176b73" stroke-width="3" '
            'marker-end="url(#network-arrow)"/>'
        )
    parts.extend(
        [
            '    <rect x="218" y="346" width="644" height="94" rx="12" '
            'fill="#fffaf5" stroke="#e5b58f"/>',
            '    <text x="540" y="375" text-anchor="middle" font-size="12" '
            'font-weight="700" fill="#d97732">SHARED INTERMEDIATE ACCOUNT</text>',
            '    <text x="540" y="407" text-anchor="middle" font-size="20" '
            'font-weight="700" fill="#24323d">the same wᵀz records the upstream '
            "result and downstream commitment</text>",
            '    <text x="540" y="428" text-anchor="middle" font-size="13" '
            'fill="#687780">Shared valuation coordinates the two accounts; it is '
            "not a market price.</text>",
            '    <g filter="url(#shadow-network)">',
            '      <rect x="98" y="480" width="350" height="82" rx="11" '
            'fill="#eef7f7" stroke="#9fc8cb"/>',
            '      <rect x="632" y="480" width="350" height="82" rx="11" '
            'fill="#f3eef7" stroke="#c6b2d3"/>',
            "    </g>",
            '    <text x="273" y="510" text-anchor="middle" font-size="17" '
            'font-weight="700" fill="#176b73">λ · upstream peer practices</text>',
            '    <text x="273" y="539" text-anchor="middle" font-size="14" '
            'fill="#24323d">What the acquisition process can supply: Zλ</text>',
            '    <text x="807" y="510" text-anchor="middle" font-size="17" '
            'font-weight="700" fill="#76528f">μ · downstream peer practices</text>',
            '    <text x="807" y="539" text-anchor="middle" font-size="14" '
            'fill="#24323d">What the profit process requires: Zμ</text>',
            '    <line x1="448" y1="521" x2="622" y2="521" '
            'stroke="#d97732" stroke-width="3" marker-end="url(#network-arrow)"/>',
            '    <rect x="476" y="498" width="128" height="46" rx="23" '
            'fill="#fff4e9" stroke="#e5b58f"/>',
            '    <text x="540" y="527" text-anchor="middle" font-size="17" '
            'font-weight="700" fill="#d97732">Zλ ≥ Zμ</text>',
            '    <rect x="40" y="590" width="1000" height="38" rx="9" fill="#24323d"/>',
            '    <text x="540" y="614" text-anchor="middle" font-size="14" '
            'font-weight="700" fill="#ffffff">Common accounting does not require '
            "common peers, and stage attribution is not causal attribution.</text>",
            "  </g>",
            "</svg>",
        ]
    )
    return "\n".join(parts)


def two_stage_accounting_choices() -> str:
    """Contrast three family-level reports over one connected organization."""
    return "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="690" '
            'viewBox="0 0 1080 690" role="img" '
            'aria-labelledby="title description">',
            '  <title id="title">Three performance accounts for one connected '
            "organization</title>",
            '  <desc id="description">The same research and commercialization '
            "chain supports a system-only radial account, a relational product "
            "account, or an endogenous-share additive process attribution. The "
            "three reports answer different management questions even though "
            "they coordinate the same internal handoff.</desc>",
            "  <defs>",
            '    <marker id="choice-arrow" markerWidth="10" markerHeight="10" '
            'refX="9" refY="4" orient="auto">',
            '      <path d="M0,0 L0,8 L9,4 z" fill="#176b73"/>',
            "    </marker>",
            '    <filter id="choice-shadow" x="-10%" y="-10%" width="120%" '
            'height="130%">',
            '      <feDropShadow dx="0" dy="2" stdDeviation="3" '
            'flood-color="#24323d" flood-opacity="0.12"/>',
            "    </filter>",
            "  </defs>",
            '  <rect width="1080" height="690" fill="#ffffff"/>',
            '  <g font-family="Arial, sans-serif">',
            '    <text x="40" y="42" font-size="23" font-weight="700" '
            'fill="#24323d">One organizational chain can support different '
            "performance accounts</text>",
            '    <text x="40" y="70" font-size="15" fill="#5c6b73">The graph '
            "describes how work is organized; the reporting institution says "
            "what the board wants to learn.</text>",
            '    <g filter="url(#choice-shadow)">',
            '      <rect x="60" y="104" width="230" height="84" rx="12" '
            'fill="#eef7f7" stroke="#9fc8cb"/>',
            '      <rect x="425" y="104" width="230" height="84" rx="12" '
            'fill="#fff4e9" stroke="#e5b58f"/>',
            '      <rect x="790" y="104" width="230" height="84" rx="12" '
            'fill="#f3eef7" stroke="#c6b2d3"/>',
            "    </g>",
            '    <text x="175" y="135" text-anchor="middle" font-size="12" '
            'font-weight="700" fill="#176b73">PROCESS 1</text>',
            '    <text x="175" y="166" text-anchor="middle" font-size="19" '
            'font-weight="700" fill="#176b73">Research</text>',
            '    <text x="540" y="135" text-anchor="middle" font-size="12" '
            'font-weight="700" fill="#d97732">INTERNAL HANDOFF</text>',
            '    <text x="540" y="166" text-anchor="middle" font-size="19" '
            'font-weight="700" fill="#d97732">Innovations z</text>',
            '    <text x="905" y="135" text-anchor="middle" font-size="12" '
            'font-weight="700" fill="#76528f">PROCESS 2</text>',
            '    <text x="905" y="166" text-anchor="middle" font-size="19" '
            'font-weight="700" fill="#76528f">Commercialization</text>',
            '    <line x1="290" y1="146" x2="415" y2="146" '
            'stroke="#176b73" stroke-width="3" '
            'marker-end="url(#choice-arrow)"/>',
            '    <line x1="655" y1="146" x2="780" y2="146" '
            'stroke="#176b73" stroke-width="3" '
            'marker-end="url(#choice-arrow)"/>',
            '    <text x="540" y="222" text-anchor="middle" font-size="14" '
            'font-weight="700" fill="#5c6b73">SAME GRAPH AND HANDOFF · '
            "DIFFERENT REPORTING QUESTION</text>",
            '    <g filter="url(#choice-shadow)">',
            '      <rect x="30" y="250" width="320" height="300" rx="14" '
            'fill="#eef7f7" stroke="#9fc8cb"/>',
            '      <rect x="380" y="250" width="320" height="300" rx="14" '
            'fill="#fff7ef" stroke="#e5b58f"/>',
            '      <rect x="730" y="250" width="320" height="300" rx="14" '
            'fill="#f3eef7" stroke="#c6b2d3"/>',
            "    </g>",
            '    <text x="54" y="284" font-size="13" font-weight="700" '
            'fill="#176b73">SYSTEM-ONLY RADIAL</text>',
            '    <text x="54" y="326" font-size="27" font-weight="700" '
            'fill="#24323d">E</text>',
            '    <text x="54" y="362" font-size="15" fill="#24323d">How much '
            "external resource</text>",
            '    <text x="54" y="386" font-size="15" fill="#24323d">does one '
            "coordinated plan require?</text>",
            '    <rect x="54" y="418" width="272" height="94" rx="9" '
            'fill="#ffffff" stroke="#cfe0e2"/>',
            '    <text x="190" y="445" text-anchor="middle" font-size="13" '
            'font-weight="700" fill="#176b73">BOARD-LEVEL REPORT</text>',
            '    <text x="190" y="473" text-anchor="middle" font-size="14" '
            'fill="#24323d">process-specific peers</text>',
            '    <text x="190" y="495" text-anchor="middle" font-size="14" '
            'font-weight="700" fill="#5c6b73">no process score</text>',
            "",
            '    <text x="404" y="284" font-size="13" font-weight="700" '
            'fill="#a65119">RELATIONAL PRODUCT</text>',
            '    <text x="404" y="326" font-size="27" font-weight="700" '
            'fill="#24323d">E = E₁ &#215; E₂</text>',
            '    <text x="404" y="362" font-size="15" fill="#24323d">How do '
            "jointly necessary</text>",
            '    <text x="404" y="386" font-size="15" fill="#24323d">process '
            "ratios compound?</text>",
            '    <rect x="404" y="418" width="272" height="94" rx="9" '
            'fill="#ffffff" stroke="#ead0b9"/>',
            '    <text x="540" y="445" text-anchor="middle" font-size="13" '
            'font-weight="700" fill="#a65119">SHARED LINK VALUATION</text>',
            '    <text x="540" y="473" text-anchor="middle" font-size="14" '
            'fill="#24323d">selected process ratios</text>',
            '    <text x="540" y="495" text-anchor="middle" font-size="14" '
            'font-weight="700" fill="#5c6b73">not a transfer price</text>',
            "",
            '    <text x="754" y="284" font-size="13" font-weight="700" '
            'fill="#76528f">ADDITIVE PROCESS ATTRIBUTION</text>',
            '    <text x="754" y="326" font-size="27" font-weight="700" '
            'fill="#24323d">E = &#945;₁E₁ + &#945;₂E₂</text>',
            '    <text x="754" y="362" font-size="15" fill="#24323d">How is '
            "system performance</text>",
            '    <text x="754" y="386" font-size="15" fill="#24323d">assigned '
            "across processes?</text>",
            '    <rect x="754" y="418" width="272" height="94" rx="9" '
            'fill="#ffffff" stroke="#d9cde2"/>',
            '    <text x="890" y="445" text-anchor="middle" font-size="13" '
            'font-weight="700" fill="#76528f">FITTED RESOURCE SHARES</text>',
            '    <text x="890" y="473" text-anchor="middle" font-size="14" '
            'fill="#24323d">arithmetic attribution</text>',
            '    <text x="890" y="495" text-anchor="middle" font-size="14" '
            'font-weight="700" fill="#5c6b73">not a budget or priority</text>',
            "",
            '    <rect x="40" y="582" width="1000" height="60" rx="12" '
            'fill="#24323d"/>',
            '    <text x="540" y="607" text-anchor="middle" font-size="14" '
            'font-weight="700" fill="#ffffff">The link is stored once and '
            "coordinated at both endpoints.</text>",
            '    <text x="540" y="629" text-anchor="middle" font-size="13" '
            'fill="#d7e2e5">Different accounts need not produce comparable '
            "scores, unique process stories, or causal explanations.</text>",
            '    <text x="540" y="671" text-anchor="middle" font-size="13" '
            'fill="#687780">Choose the account from the decision question—not '
            "from whichever score is highest.</text>",
            "  </g>",
            "</svg>",
        ]
    )


def closed_vs_open_network() -> str:
    """Contrast a closed series chain with an open, branching organization."""
    return "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="720" '
            'viewBox="0 0 1080 720" role="img" '
            'aria-labelledby="title description">',
            '  <title id="title">Closed production chain and open branching '
            "network</title>",
            '  <desc id="description">The closed chain receives all external '
            "resources before its first process and releases all final outcomes "
            "after its last. The open network lets resources enter and outcomes "
            "leave at several processes, with distinct internal links branching, "
            "rejoining, or skipping a process.</desc>",
            "  <defs>",
            '    <marker id="flow-input" markerWidth="10" markerHeight="10" '
            'refX="9" refY="4" orient="auto">',
            '      <path d="M0,0 L0,8 L9,4 z" fill="#176b73"/>',
            "    </marker>",
            '    <marker id="flow-link" markerWidth="10" markerHeight="10" '
            'refX="9" refY="4" orient="auto">',
            '      <path d="M0,0 L0,8 L9,4 z" fill="#d97732"/>',
            "    </marker>",
            '    <marker id="flow-output" markerWidth="10" markerHeight="10" '
            'refX="9" refY="4" orient="auto">',
            '      <path d="M0,0 L0,8 L9,4 z" fill="#76528f"/>',
            "    </marker>",
            '    <filter id="open-shadow" x="-10%" y="-10%" width="120%" '
            'height="130%">',
            '      <feDropShadow dx="0" dy="2" stdDeviation="3" '
            'flood-color="#24323d" flood-opacity="0.12"/>',
            "    </filter>",
            "  </defs>",
            '  <rect width="1080" height="720" fill="#ffffff"/>',
            '  <g font-family="Arial, sans-serif">',
            '    <text x="40" y="42" font-size="23" font-weight="700" '
            'fill="#24323d">Where work enters and leaves changes the '
            "performance account</text>",
            '    <text x="40" y="70" font-size="15" fill="#5c6b73">A network '
            "graph records organizational boundaries—not merely the order of "
            "boxes in a diagram.</text>",
            '    <line x1="48" y1="101" x2="90" y2="101" stroke="#176b73" '
            'stroke-width="4" marker-end="url(#flow-input)"/>',
            '    <text x="102" y="106" font-size="13" fill="#24323d">'
            "external resource enters</text>",
            '    <line x1="291" y1="101" x2="333" y2="101" stroke="#d97732" '
            'stroke-width="4" marker-end="url(#flow-link)"/>',
            '    <text x="345" y="106" font-size="13" fill="#24323d">'
            "internal link</text>",
            '    <line x1="466" y1="101" x2="508" y2="101" stroke="#76528f" '
            'stroke-width="4" marker-end="url(#flow-output)"/>',
            '    <text x="520" y="106" font-size="13" fill="#24323d">'
            "result leaves the system</text>",
            '    <rect x="40" y="133" width="374" height="514" rx="16" '
            'fill="#f7f9fa" stroke="#cfdadd"/>',
            '    <rect x="438" y="133" width="602" height="514" rx="16" '
            'fill="#fffaf5" stroke="#e5b58f"/>',
            '    <text x="65" y="170" font-size="14" font-weight="700" '
            'fill="#5c6b73">CLOSED SERIES CHAIN</text>',
            '    <text x="65" y="195" font-size="15" fill="#24323d">All '
            "resources enter first; all outcomes leave last.</text>",
            '    <g filter="url(#open-shadow)">',
            '      <rect x="77" y="228" width="132" height="50" rx="25" '
            'fill="#eef7f7" stroke="#9fc8cb"/>',
            '      <rect x="236" y="218" width="142" height="70" rx="11" '
            'fill="#ffffff" stroke="#9fc8cb"/>',
            '      <rect x="236" y="352" width="142" height="70" rx="11" '
            'fill="#ffffff" stroke="#e5b58f"/>',
            '      <rect x="236" y="486" width="142" height="70" rx="11" '
            'fill="#ffffff" stroke="#c6b2d3"/>',
            '      <rect x="77" y="496" width="132" height="50" rx="25" '
            'fill="#f3eef7" stroke="#c6b2d3"/>',
            "    </g>",
            '    <text x="143" y="258" text-anchor="middle" font-size="14" '
            'font-weight="700" fill="#176b73">all resources</text>',
            '    <text x="307" y="248" text-anchor="middle" font-size="12" '
            'font-weight="700" fill="#176b73">PROCESS 1</text>',
            '    <text x="307" y="271" text-anchor="middle" font-size="15" '
            'fill="#24323d">create handoff</text>',
            '    <text x="307" y="382" text-anchor="middle" font-size="12" '
            'font-weight="700" fill="#d97732">ONE LINK</text>',
            '    <text x="307" y="405" text-anchor="middle" font-size="15" '
            'fill="#24323d">intermediate z</text>',
            '    <text x="307" y="516" text-anchor="middle" font-size="12" '
            'font-weight="700" fill="#76528f">PROCESS 2</text>',
            '    <text x="307" y="539" text-anchor="middle" font-size="15" '
            'fill="#24323d">deliver outcome</text>',
            '    <text x="143" y="526" text-anchor="middle" font-size="14" '
            'font-weight="700" fill="#76528f">all outcomes</text>',
            '    <line x1="209" y1="253" x2="226" y2="253" stroke="#176b73" '
            'stroke-width="3" marker-end="url(#flow-input)"/>',
            '    <line x1="307" y1="288" x2="307" y2="342" stroke="#d97732" '
            'stroke-width="3" marker-end="url(#flow-link)"/>',
            '    <line x1="307" y1="422" x2="307" y2="476" stroke="#d97732" '
            'stroke-width="3" marker-end="url(#flow-link)"/>',
            '    <line x1="236" y1="521" x2="219" y2="521" stroke="#76528f" '
            'stroke-width="3" marker-end="url(#flow-output)"/>',
            '    <rect x="66" y="584" width="322" height="42" rx="9" fill="#24323d"/>',
            '    <text x="227" y="610" text-anchor="middle" font-size="13" '
            'font-weight="700" fill="#ffffff">Useful—but too restrictive for '
            "many organizations.</text>",
            '    <text x="463" y="170" font-size="14" font-weight="700" '
            'fill="#d97732">OPEN DAG · BRANCHES AND SKIP LINKS</text>',
            '    <text x="463" y="195" font-size="15" fill="#24323d">'
            "Resources and results cross the boundary where they belong.</text>",
            '    <g filter="url(#open-shadow)">',
            '      <rect x="650" y="220" width="178" height="68" rx="11" '
            'fill="#ffffff" stroke="#9fc8cb"/>',
            '      <rect x="500" y="358" width="178" height="68" rx="11" '
            'fill="#ffffff" stroke="#e5b58f"/>',
            '      <rect x="800" y="358" width="178" height="68" rx="11" '
            'fill="#ffffff" stroke="#e5b58f"/>',
            '      <rect x="650" y="514" width="178" height="68" rx="11" '
            'fill="#ffffff" stroke="#c6b2d3"/>',
            "    </g>",
            '    <text x="739" y="247" text-anchor="middle" font-size="12" '
            'font-weight="700" fill="#176b73">ORIGIN PROCESS</text>',
            '    <text x="739" y="270" text-anchor="middle" font-size="15" '
            'fill="#24323d">creates several flows</text>',
            '    <text x="589" y="385" text-anchor="middle" font-size="12" '
            'font-weight="700" fill="#d97732">BRANCH A</text>',
            '    <text x="589" y="408" text-anchor="middle" font-size="15" '
            'fill="#24323d">uses new resources</text>',
            '    <text x="889" y="385" text-anchor="middle" font-size="12" '
            'font-weight="700" fill="#d97732">BRANCH B</text>',
            '    <text x="889" y="408" text-anchor="middle" font-size="15" '
            'fill="#24323d">releases a result</text>',
            '    <text x="739" y="541" text-anchor="middle" font-size="12" '
            'font-weight="700" fill="#76528f">FINISH PROCESS</text>',
            '    <text x="739" y="564" text-anchor="middle" font-size="15" '
            'fill="#24323d">rejoins the work</text>',
            '    <rect x="470" y="229" width="126" height="48" rx="24" '
            'fill="#eef7f7" stroke="#9fc8cb"/>',
            '    <text x="533" y="258" text-anchor="middle" font-size="13" '
            'font-weight="700" fill="#176b73">initial resource</text>',
            '    <line x1="596" y1="253" x2="640" y2="253" stroke="#176b73" '
            'stroke-width="3" marker-end="url(#flow-input)"/>',
            '    <rect x="456" y="366" width="34" height="52" rx="17" '
            'fill="#eef7f7" stroke="#9fc8cb"/>',
            '    <text x="473" y="392" text-anchor="middle" font-size="18" '
            'font-weight="700" fill="#176b73">+</text>',
            '    <line x1="484" y1="392" x2="496" y2="392" stroke="#176b73" '
            'stroke-width="3" marker-end="url(#flow-input)"/>',
            '    <path d="M690 288 C650 318 622 329 592 348" fill="none" '
            'stroke="#d97732" stroke-width="3" '
            'marker-end="url(#flow-link)"/>',
            '    <path d="M788 288 C828 318 856 329 886 348" fill="none" '
            'stroke="#d97732" stroke-width="3" '
            'marker-end="url(#flow-link)"/>',
            '    <path d="M624 426 C645 469 677 484 711 504" fill="none" '
            'stroke="#d97732" stroke-width="3" '
            'marker-end="url(#flow-link)"/>',
            '    <path d="M854 426 C833 469 801 484 767 504" fill="none" '
            'stroke="#d97732" stroke-width="3" '
            'marker-end="url(#flow-link)"/>',
            '    <path d="M815 278 C1004 305 1015 490 828 535" fill="none" '
            'stroke="#d97732" stroke-width="2.5" stroke-dasharray="7 5" '
            'marker-end="url(#flow-link)"/>',
            '    <text x="1000" y="432" text-anchor="middle" font-size="12" '
            'font-weight="700" fill="#d97732">skip link</text>',
            '    <rect x="985" y="365" width="34" height="52" rx="17" '
            'fill="#f3eef7" stroke="#c6b2d3"/>',
            '    <text x="1002" y="396" text-anchor="middle" font-size="18" '
            'font-weight="700" fill="#76528f">↗</text>',
            '    <line x1="978" y1="392" x2="985" y2="392" stroke="#76528f" '
            'stroke-width="3" marker-end="url(#flow-output)"/>',
            '    <rect x="850" y="519" width="152" height="48" rx="24" '
            'fill="#f3eef7" stroke="#c6b2d3"/>',
            '    <text x="926" y="548" text-anchor="middle" font-size="13" '
            'font-weight="700" fill="#76528f">final outcome</text>',
            '    <line x1="828" y1="548" x2="840" y2="548" stroke="#76528f" '
            'stroke-width="3" marker-end="url(#flow-output)"/>',
            '    <text x="470" y="455" font-size="12" fill="#176b73">new '
            "resource enters</text>",
            '    <text x="930" y="455" font-size="12" fill="#76528f">result '
            "leaves early</text>",
            '    <rect x="463" y="598" width="552" height="28" rx="8" fill="#24323d"/>',
            '    <text x="739" y="617" text-anchor="middle" font-size="12.5" '
            'font-weight="700" fill="#ffffff">Each boundary crossing belongs '
            "to the process that receives or creates it.</text>",
            '    <rect x="40" y="672" width="1000" height="30" rx="8" fill="#24323d"/>',
            '    <text x="540" y="692" text-anchor="middle" font-size="13" '
            'font-weight="700" fill="#ffffff">Open means organizationally open: '
            "it does not mean open data, open source, or an unbounded model.</text>",
            "  </g>",
            "</svg>",
        ]
    )


def network_sbm_governance() -> str:
    """Show the two core fixed/free within-period link policies."""
    return "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="580" '
            'viewBox="0 0 1080 580" role="img" '
            'aria-labelledby="title description">',
            '  <title id="title">Two core link policies in network SBM</title>',
            '  <desc id="description">Two panels contrast a fixed observed '
            "handoff with a freely coordinated handoff. Both require the "
            "supplier and recipient peer plans to use one compatible target.</desc>",
            "  <defs>",
            '    <marker id="nsbm-arrow" markerWidth="10" markerHeight="10" '
            'refX="9" refY="4" orient="auto">',
            '      <path d="M0,0 L0,8 L9,4 z" fill="#d97732"/>',
            "    </marker>",
            '    <filter id="nsbm-shadow" x="-10%" y="-10%" width="120%" '
            'height="130%">',
            '      <feDropShadow dx="0" dy="2" stdDeviation="3" '
            'flood-color="#24323d" flood-opacity="0.12"/>',
            "    </filter>",
            "  </defs>",
            '  <rect width="1080" height="580" fill="#ffffff"/>',
            '  <g font-family="Arial, sans-serif">',
            '    <text x="40" y="42" font-size="23" font-weight="700" '
            'fill="#24323d">One handoff, two core governance questions</text>',
            '    <text x="40" y="70" font-size="15" fill="#5c6b73">'
            "Both policies keep the supplier and recipient plans consistent; "
            "the difference is whether management may redesign the flow.</text>",
            '    <g filter="url(#nsbm-shadow)">',
            '      <rect x="40" y="104" width="486" height="354" rx="16" '
            'fill="#f7f9fa" stroke="#cfdadd"/>',
            '      <rect x="554" y="104" width="486" height="354" rx="16" '
            'fill="#fffaf5" stroke="#e5b58f"/>',
            "    </g>",
            '    <text x="66" y="142" font-size="14" font-weight="700" '
            'fill="#5c6b73">FIXED · INHERIT THE COMMITMENT</text>',
            '    <text x="580" y="142" font-size="14" font-weight="700" '
            'fill="#d97732">FREE · COORDINATE A REDESIGN</text>',
            '    <text x="66" y="174" font-size="14" fill="#24323d">'
            "Both divisions must reproduce the observed flow.</text>",
            '    <text x="580" y="174" font-size="14" fill="#24323d">'
            "Both divisions choose one common feasible flow.</text>",
            '    <g fill="#ffffff" stroke-width="1.5">',
            '      <rect x="68" y="218" width="142" height="70" rx="10" '
            'stroke="#9fc8cb"/>',
            '      <rect x="356" y="218" width="142" height="70" rx="10" '
            'stroke="#c6b2d3"/>',
            '      <rect x="582" y="218" width="142" height="70" rx="10" '
            'stroke="#9fc8cb"/>',
            '      <rect x="870" y="218" width="142" height="70" rx="10" '
            'stroke="#c6b2d3"/>',
            "    </g>",
            '    <g font-size="12" font-weight="700">',
            '      <text x="139" y="244" text-anchor="middle" '
            'fill="#176b73">SUPPLIER</text>',
            '      <text x="427" y="244" text-anchor="middle" '
            'fill="#76528f">RECIPIENT</text>',
            '      <text x="653" y="244" text-anchor="middle" '
            'fill="#176b73">SUPPLIER</text>',
            '      <text x="941" y="244" text-anchor="middle" '
            'fill="#76528f">RECIPIENT</text>',
            "    </g>",
            '    <g font-size="13" fill="#24323d">',
            '      <text x="139" y="272" text-anchor="middle">&#955; supplier</text>',
            '      <text x="427" y="272" text-anchor="middle">&#955; recipient</text>',
            '      <text x="653" y="272" text-anchor="middle">&#955; supplier</text>',
            '      <text x="941" y="272" text-anchor="middle">&#955; recipient</text>',
            "    </g>",
            '    <g stroke="#d97732" stroke-width="4" marker-end="url(#nsbm-arrow)">',
            '      <line x1="210" y1="253" x2="346" y2="253"/>',
            '      <line x1="724" y1="253" x2="860" y2="253"/>',
            "    </g>",
            '    <g font-size="16" font-weight="700" fill="#24323d">',
            '      <text x="283" y="334" text-anchor="middle">'
            "Z&#955; supplier = z observed = Z&#955; recipient</text>",
            '      <text x="797" y="334" text-anchor="middle">'
            "Z&#955; supplier = Z&#955; recipient = z*</text>",
            "    </g>",
            '    <g font-size="13.5" fill="#5c6b73">',
            '      <text x="283" y="374" text-anchor="middle">'
            "Management conditions on the inherited quantity.</text>",
            '      <text x="283" y="400" text-anchor="middle">'
            "The common target cannot move away from observation.</text>",
            '      <text x="797" y="374" text-anchor="middle">'
            "Management may redesign the quantity jointly.</text>",
            '      <text x="797" y="400" text-anchor="middle">'
            "The two processes still cannot choose different targets.</text>",
            "    </g>",
            '    <rect x="40" y="488" width="1000" height="62" rx="13" '
            'fill="#24323d"/>',
            '    <text x="540" y="515" text-anchor="middle" font-size="14" '
            'font-weight="700" fill="#ffffff">ONE ORGANIZATION, ONE HANDOFF '
            "TARGET</text>",
            '    <text x="540" y="538" text-anchor="middle" font-size="13.5" '
            'fill="#ffffff">Fixed protects the observed commitment; free reveals '
            "what coordinated redesign could make attainable.</text>",
            "  </g>",
            "</svg>",
        ]
    )


def dynamic_network_management_map() -> str:
    """Show one organization connected across both processes and periods."""
    periods = (
        (305, "Period 1", "W₁"),
        (575, "Period 2", "W₂"),
        (845, "Period 3", "W₃"),
    )
    processes = (
        (202, "GENERATION", "capacity", "#176b73", "#eef7f7", "teal"),
        (370, "GRID", "maintenance backlog", "#d97732", "#fff3e9", "orange"),
        (
            538,
            "CUSTOMER SERVICE",
            "service obligation",
            "#76528f",
            "#f3eef7",
            "purple",
        ),
    )
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="760" '
        'viewBox="0 0 1080 760" role="img" '
        'aria-labelledby="title description">',
        '<title id="title">A production network connected through time</title>',
        '<desc id="description">Generation, grid, and customer-service '
        "processes exchange two internal handoffs in each period. Capacity, "
        "maintenance backlog, and service obligations connect the same "
        "process across periods. Every process-period peer plan enters one "
        "jointly feasible system appraisal.</desc>",
        "<defs>",
        '<marker id="dn-link" markerWidth="10" markerHeight="10" refX="9" '
        'refY="4" orient="auto"><path d="M0,0 L0,8 L9,4 z" '
        'fill="#d97732"/></marker>',
        '<marker id="dn-state-teal" markerWidth="10" markerHeight="10" refX="9" '
        'refY="4" orient="auto"><path d="M0,0 L0,8 L9,4 z" '
        'fill="#176b73"/></marker>',
        '<marker id="dn-state-orange" markerWidth="10" markerHeight="10" '
        'refX="9" refY="4" orient="auto"><path d="M0,0 L0,8 L9,4 z" '
        'fill="#d97732"/></marker>',
        '<marker id="dn-state-purple" markerWidth="10" markerHeight="10" '
        'refX="9" refY="4" orient="auto"><path d="M0,0 L0,8 L9,4 z" '
        'fill="#76528f"/></marker>',
        '<filter id="dn-shadow" x="-10%" y="-10%" width="120%" height="130%">'
        '<feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#24323d" '
        'flood-opacity="0.12"/></filter>',
        "</defs>",
        '<rect width="1080" height="760" fill="#ffffff"/>',
        '<g font-family="Arial, sans-serif">',
        '<text x="40" y="42" font-size="23" font-weight="700" '
        'fill="#24323d">The benchmark must work as an organization and as a '
        "history</text>",
        '<text x="40" y="70" font-size="14.5" fill="#5c6b73">'
        "Within-period handoffs coordinate departments. Carry-overs prevent "
        "today's target from contradicting</text>",
        '<text x="40" y="90" font-size="14.5" fill="#5c6b73">'
        "tomorrow's inherited position.</text>",
        '<rect x="38" y="106" width="1004" height="548" rx="18" '
        'fill="#f8fafb" stroke="#cfdadd"/>',
    ]
    for x, label, weight in periods:
        parts.extend(
            [
                f'<rect x="{x - 105}" y="122" width="210" height="42" rx="10" '
                'fill="#24323d"/>',
                f'<text x="{x}" y="141" text-anchor="middle" font-size="15" '
                f'font-weight="700" fill="#ffffff">{label}</text>',
                f'<text x="{x}" y="158" text-anchor="middle" font-size="11.5" '
                f'fill="#d7e2e5">importance {weight}</text>',
            ]
        )
    for y, label, state, color, fill, marker in processes:
        parts.extend(
            [
                f'<text x="52" y="{y + 5}" font-size="12" font-weight="700" '
                f'fill="{color}">{label}</text>',
                f'<text x="52" y="{y + 24}" font-size="11.5" '
                f'fill="#5c6b73">state: {state}</text>',
            ]
        )
        for x, _, _ in periods:
            parts.extend(
                [
                    f'<rect x="{x - 92}" y="{y - 28}" width="184" height="76" '
                    f'rx="12" fill="{fill}" stroke="{color}" '
                    'filter="url(#dn-shadow)"/>',
                    f'<text x="{x}" y="{y - 2}" text-anchor="middle" '
                    f'font-size="14" font-weight="700" fill="{color}">'
                    f"{label.title()}</text>",
                    f'<text x="{x}" y="{y + 22}" text-anchor="middle" '
                    'font-size="14" fill="#24323d">joint benchmark plan</text>',
                    f'<text x="{x}" y="{y + 40}" text-anchor="middle" '
                    'font-size="11.5" fill="#5c6b73">resources → results</text>',
                ]
            )
        for left, right in ((397, 483), (667, 753)):
            parts.extend(
                [
                    f'<line x1="{left}" y1="{y + 1}" x2="{right}" '
                    f'y2="{y + 1}" stroke="{color}" stroke-width="3" '
                    f'stroke-dasharray="8 5" marker-end="url(#dn-state-{marker})"/>',
                    f'<rect x="{left + 12}" y="{y - 23}" width="62" '
                    f'height="21" rx="10" fill="#ffffff" stroke="{color}"/>',
                    f'<text x="{left + 43}" y="{y - 8}" text-anchor="middle" '
                    f'font-size="10.5" font-weight="700" fill="{color}">'
                    "inherit</text>",
                ]
            )
    for x, _, _ in periods:
        parts.extend(
            [
                f'<line x1="{x}" y1="250" x2="{x}" y2="330" '
                'stroke="#d97732" stroke-width="4" '
                'marker-end="url(#dn-link)"/>',
                f'<rect x="{x - 66}" y="276" width="132" height="25" rx="12" '
                'fill="#ffffff" stroke="#e5b58f"/>',
                f'<text x="{x}" y="293" text-anchor="middle" font-size="11.5" '
                'font-weight="700" fill="#d97732">power handoff</text>',
                f'<line x1="{x}" y1="418" x2="{x}" y2="498" '
                'stroke="#d97732" stroke-width="4" '
                'marker-end="url(#dn-link)"/>',
                f'<rect x="{x - 72}" y="444" width="144" height="25" rx="12" '
                'fill="#ffffff" stroke="#e5b58f"/>',
                f'<text x="{x}" y="461" text-anchor="middle" font-size="11.5" '
                'font-weight="700" fill="#d97732">delivered energy</text>',
            ]
        )
    parts.extend(
        [
            '<rect x="92" y="594" width="896" height="42" rx="11" '
            'fill="#ffffff" stroke="#9fc8cb"/>',
            '<text x="540" y="611" text-anchor="middle" font-size="13.5" '
            'font-weight="700" fill="#176b73">ONE JOINT OPERATING PLAN</text>',
            '<text x="540" y="629" text-anchor="middle" font-size="12.5" '
            'fill="#24323d">Every handoff balances, every inherited state '
            "agrees, and every process-period target is attainable together."
            "</text>",
            '<rect x="38" y="676" width="1004" height="56" rx="13" fill="#24323d"/>',
            '<text x="540" y="698" text-anchor="middle" font-size="14" '
            'font-weight="700" fill="#ffffff">SYSTEM EFFICIENCY IS A '
            "WEIGHTED PERFORMANCE ACCOUNT</text>",
            '<text x="540" y="719" text-anchor="middle" font-size="12.5" '
            'fill="#d7e2e5">Process and period scores explain one selected '
            "joint optimum; they are not independent rankings or causal "
            "effects.</text>",
            "</g>",
            "</svg>",
        ]
    )
    return "\n".join(parts)


def range_directional_signed_opportunity() -> str:
    """Build an original exact RDM geometry from three synthetic observations.

    The focal observation F=(-2, 1) and the coordinatewise aspiration I=(4, 5)
    define the output range direction (6, 4).  The ray meets the VRS segment
    between N=(-1, 5) and E=(4, 0) at T=(1, 3), because
    T=0.6N+0.4E=F+0.5(I-F).  The values and layout were designed for this
    Handbook and do not reproduce the empirical example or a figure from the
    source literature.
    """

    width, height = 1000, 650
    plot_left, plot_right = 72.0, 625.0
    plot_top, plot_bottom = 102.0, 514.0
    x_min, x_max = -3.0, 5.0
    y_min, y_max = -1.0, 6.0

    def point(x_value: float, y_value: float) -> tuple[float, float]:
        x = plot_left + (x_value - x_min) * (plot_right - plot_left) / (x_max - x_min)
        y = plot_bottom - (y_value - y_min) * (plot_bottom - plot_top) / (y_max - y_min)
        return x, y

    focus = (-2.0, 1.0)
    north = (-1.0, 5.0)
    east = (4.0, 0.0)
    aspiration = (4.0, 5.0)
    target = (1.0, 3.0)

    parts = _conceptual_base(
        width=width,
        height=height,
        title="RDM geometry from a project-designed signed example",
        description=(
            "Three synthetic observations define an output-oriented range "
            "directional measure. The focal observation F is minus two and "
            "one, the coordinatewise aspiration is four and five, and the "
            "ray reaches the VRS frontier at T after one half of the remaining "
            "opportunity vector."
        ),
    )
    parts.extend(
        [
            _conceptual_text(
                500,
                35,
                "RDM geometry from a project-designed signed example",
                size=24,
                weight=700,
                anchor="middle",
            ),
            _conceptual_text(
                500,
                63,
                (
                    "Every unit uses one common resource unit; both displayed "
                    "accounts are desirable (higher is preferred)."
                ),
                size=15,
                fill=GRAY,
                anchor="middle",
            ),
            f'<rect x="{plot_left:g}" y="{plot_top:g}" '
            f'width="{plot_right - plot_left:g}" '
            f'height="{plot_bottom - plot_top:g}" rx="12" fill="#fbfcfd" '
            'stroke="#cbd8de"/>',
        ]
    )

    for x_value in range(-2, 5):
        x, _ = point(float(x_value), y_min)
        parts.extend(
            [
                f'<line x1="{x:.2f}" y1="{plot_top:g}" x2="{x:.2f}" '
                f'y2="{plot_bottom:g}" stroke="{GRID}" stroke-width="1"/>',
                _conceptual_text(
                    x,
                    plot_bottom + 23,
                    str(x_value),
                    size=15,
                    fill=GRAY,
                    anchor="middle",
                ),
            ]
        )
    for y_value in range(0, 6):
        _, y = point(x_min, float(y_value))
        parts.extend(
            [
                f'<line x1="{plot_left:g}" y1="{y:.2f}" '
                f'x2="{plot_right:g}" y2="{y:.2f}" stroke="{GRID}" '
                'stroke-width="1"/>',
                _conceptual_text(
                    plot_left - 13,
                    y + 5,
                    str(y_value),
                    size=15,
                    fill=GRAY,
                    anchor="end",
                ),
            ]
        )

    axis_y = point(x_min, 0.0)[1]
    axis_x = point(0.0, y_min)[0]
    parts.extend(
        [
            f'<line x1="{plot_left:g}" y1="{axis_y:.2f}" '
            f'x2="{plot_right:g}" y2="{axis_y:.2f}" stroke="{INK}" '
            'stroke-width="2"/>',
            f'<line x1="{axis_x:.2f}" y1="{plot_top:g}" '
            f'x2="{axis_x:.2f}" y2="{plot_bottom:g}" stroke="{INK}" '
            'stroke-width="2"/>',
            _conceptual_text(
                350,
                568,
                "Signed account a₁",
                size=16,
                weight=700,
                anchor="middle",
            ),
            '<text x="25" y="308" text-anchor="middle" font-size="16" '
            f'font-weight="700" fill="{INK}" transform="rotate(-90 25 308)">'
            "Signed account a₂</text>",
        ]
    )

    feasible_values = [
        (x_min, y_min),
        (east[0], y_min),
        east,
        north,
        (x_min, north[1]),
    ]
    feasible_points = [point(*value) for value in feasible_values]
    frontier_points = [point(*north), point(*east)]
    parts.extend(
        [
            f'<path d="{_path(feasible_points)} Z" fill="{PALE_TEAL}" opacity="0.82"/>',
            f'<path d="{_path(frontier_points)}" fill="none" '
            f'stroke="{TEAL}" stroke-width="4"/>',
            _conceptual_text(
                103,
                486,
                "feasible set under output free disposability",
                size=15,
                fill=TEAL,
            ),
            _conceptual_text(
                278,
                190,
                "VRS frontier: mixtures of N and E",
                size=15,
                weight=700,
                fill=TEAL,
            ),
        ]
    )

    fx, fy = point(*focus)
    nx, ny = point(*north)
    ex, ey = point(*east)
    ix, iy = point(*aspiration)
    tx, ty = point(*target)
    parts.extend(
        [
            f'<line x1="{fx:.2f}" y1="{fy:.2f}" x2="{ix:.2f}" '
            f'y2="{iy:.2f}" stroke="#8f9da8" stroke-width="3" '
            'stroke-dasharray="9 7"/>',
            f'<line x1="{fx:.2f}" y1="{fy:.2f}" x2="{tx:.2f}" '
            f'y2="{ty:.2f}" stroke="{ORANGE}" stroke-width="5"/>',
            f'<path d="M {tx - 12:.2f} {ty + 1:.2f} L {tx + 3:.2f} '
            f'{ty:.2f} L {tx - 6:.2f} {ty + 12:.2f} Z" fill="{ORANGE}"/>',
            f'<circle cx="{fx:.2f}" cy="{fy:.2f}" r="8" fill="{BLUE}" '
            'stroke="white" stroke-width="3"/>',
            f'<circle cx="{nx:.2f}" cy="{ny:.2f}" r="8" fill="{TEAL}" '
            'stroke="white" stroke-width="3"/>',
            f'<circle cx="{ex:.2f}" cy="{ey:.2f}" r="8" fill="{TEAL}" '
            'stroke="white" stroke-width="3"/>',
            f'<circle cx="{tx:.2f}" cy="{ty:.2f}" r="10" fill="{ORANGE}" '
            'stroke="white" stroke-width="3"/>',
            f'<rect x="{ix - 8:.2f}" y="{iy - 8:.2f}" width="16" '
            'height="16" fill="#ffffff" stroke="#76528f" '
            'stroke-width="3" transform="rotate(45 '
            f'{ix:.2f} {iy:.2f})"/>',
            _conceptual_text(fx - 8, fy + 29, "F  (-2, 1)", size=15, weight=700),
            _conceptual_text(nx + 12, ny - 11, "N  (-1, 5)", size=15, weight=700),
            _conceptual_text(ex - 8, ey + 29, "E  (4, 0)", size=15, weight=700),
            _conceptual_text(tx + 13, ty + 6, "T  (1, 3)", size=15, weight=700),
            _conceptual_text(ix - 12, iy - 15, "I  (4, 5)", size=15, weight=700),
            _conceptual_text(fx - 8, fy + 50, "observed focus", size=15, fill=BLUE),
            _conceptual_text(
                ix - 12,
                iy - 37,
                "coordinatewise aspiration (outside the set)",
                size=15,
                fill=PURPLE,
                anchor="end",
            ),
            '<rect x="249" y="322" width="257" height="32" rx="16" '
            f'fill="{PALE_ORANGE}" stroke="#e4b38f"/>',
            _conceptual_text(
                378,
                344,
                "β = 1/2 of the opportunity vector",
                size=15,
                weight=700,
                fill=ORANGE,
                anchor="middle",
            ),
        ]
    )

    parts.extend(
        [
            '<rect x="652" y="102" width="316" height="412" rx="12" '
            'fill="#fbfcfd" stroke="#cbd8de"/>',
            _conceptual_text(
                678,
                132,
                "SYNTHETIC COMPARISON",
                size=15,
                weight=700,
                fill=GRAY,
            ),
            _conceptual_text(681, 163, "Unit", size=15, weight=700),
            _conceptual_text(846, 163, "a₁", size=15, weight=700, anchor="middle"),
            _conceptual_text(922, 163, "a₂", size=15, weight=700, anchor="middle"),
        ]
    )
    for y, unit, a1, a2 in (
        (192, "Focus F", "-2", "1"),
        (222, "North N", "-1", "5"),
        (252, "East E", "4", "0"),
    ):
        parts.extend(
            [
                f'<line x1="676" y1="{y - 20}" x2="944" y2="{y - 20}" '
                f'stroke="{GRID}"/>',
                _conceptual_text(681, y, unit, size=15),
                _conceptual_text(846, y, a1, size=15, anchor="middle"),
                _conceptual_text(922, y, a2, size=15, anchor="middle"),
            ]
        )
    parts.extend(
        [
            _conceptual_text(
                678,
                292,
                "RANGE ACCOUNT FOR F",
                size=15,
                weight=700,
                fill=GRAY,
            ),
            _conceptual_text(
                678,
                326,
                "I - F = (4 - (-2), 5 - 1) = (6, 4)",
                size=15,
                weight=700,
            ),
            _conceptual_text(
                678,
                358,
                "T = F + 1/2(I - F) = (1, 3)",
                size=15,
                weight=700,
                fill=ORANGE,
            ),
            _conceptual_text(
                678,
                390,
                "T = 0.6N + 0.4E",
                size=15,
                weight=700,
                fill=TEAL,
            ),
            '<rect x="676" y="414" width="268" height="48" rx="10" '
            'fill="#eee8f3" stroke="#cbb8d7"/>',
            _conceptual_text(
                810,
                444,
                "RDM efficiency = 1 - β = 1/2",
                size=16,
                weight=700,
                fill=PURPLE,
                anchor="middle",
            ),
            _conceptual_text(
                678,
                489,
                "Interpret β as a common feasible share,",
                size=15,
                fill=GRAY,
            ),
            _conceptual_text(
                678,
                508,
                "not as a percentage of either signed level.",
                size=15,
                fill=GRAY,
            ),
            '<rect x="72" y="588" width="896" height="42" rx="10" '
            'fill="#f5f7f9" stroke="#d3dde3"/>',
            _conceptual_text(
                520,
                606,
                (
                    "All coordinates and the layout are original synthetic "
                    "teaching material; no published empirical"
                ),
                size=15,
                fill=GRAY,
                anchor="middle",
            ),
            _conceptual_text(
                520,
                623,
                "observations or source figure are reproduced.",
                size=15,
                fill=GRAY,
                anchor="middle",
            ),
            "</g>",
            "</svg>",
        ]
    )
    return "\n".join(parts)


def _conceptual_base(
    *,
    width: int,
    height: int,
    title: str,
    description: str,
) -> list[str]:
    """Open one accessible, dependency-free management-account SVG."""
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" role="img" '
        'aria-labelledby="title description">',
        f'<title id="title">{title}</title>',
        f'<desc id="description">{description}</desc>',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        '<g font-family="Arial, Helvetica, sans-serif">',
    ]


def _conceptual_text(
    x: float,
    y: float,
    value: str,
    *,
    size: float = 15,
    weight: int = 400,
    fill: str = INK,
    anchor: str = "start",
) -> str:
    return (
        f'<text x="{x:g}" y="{y:g}" text-anchor="{anchor}" '
        f'font-size="{size:g}" font-weight="{weight}" fill="{fill}">'
        f"{value}</text>"
    )


def sbm_management_questions() -> str:
    """Show the three distinct managerial mandates of classic static SBM."""
    width, height = 1050, 500
    parts = _conceptual_base(
        width=width,
        height=height,
        title="Three management questions answered by slacks-based measures",
        description=(
            "Input-oriented SBM values resource conservation, output-oriented "
            "SBM values service expansion, and non-oriented SBM values both."
        ),
    )
    parts.append(
        _conceptual_text(
            525,
            38,
            "Same production account, three management mandates",
            size=24,
            weight=700,
            anchor="middle",
        )
    )
    cards = (
        {
            "x": 25,
            "color": TEAL,
            "soft": PALE_TEAL,
            "title": "Conserve resources",
            "model": "Input-oriented SBM",
            "input": "SAVE",
            "output": "PROTECT",
            "score": "resource retention ρᴵ",
            "line1": "Resource shortfalls drive the score;",
            "line2": "service slack is feasibility-only.",
        },
        {
            "x": 365,
            "color": "#3b7f5f",
            "soft": "#e8f2ec",
            "title": "Expand services",
            "model": "Output-oriented SBM",
            "input": "PROTECT",
            "output": "EXPAND",
            "score": "expansion τᴼ; efficiency ρᴼ=1/τᴼ",
            "line1": "Service shortfalls drive the score;",
            "line2": "resource slack is feasibility-only.",
        },
        {
            "x": 705,
            "color": PURPLE,
            "soft": "#f2edf6",
            "title": "Redesign operations",
            "model": "Non-oriented SBM",
            "input": "SAVE",
            "output": "EXPAND",
            "score": "ρᴺᴼ = (1\N{MINUS SIGN}Lˣ)/(1+Lʸ)",
            "line1": "Every valued resource saving and",
            "line2": "service gain enters the account.",
        },
    )
    for card in cards:
        x = int(card["x"])
        color = str(card["color"])
        soft = str(card["soft"])
        parts.extend(
            [
                f'<rect x="{x}" y="68" width="320" height="398" rx="16" '
                'fill="#ffffff" stroke="#cbdadd" stroke-width="2"/>',
                f'<path d="M{x + 16} 68 H{x + 304} Q{x + 320} 68 '
                f'{x + 320} 84 V134 H{x} V84 Q{x} 68 {x + 16} 68" '
                f'fill="{color}"/>',
                _conceptual_text(
                    x + 160,
                    98,
                    str(card["title"]),
                    size=20,
                    weight=700,
                    fill="#ffffff",
                    anchor="middle",
                ),
                _conceptual_text(
                    x + 160,
                    121,
                    str(card["model"]),
                    size=14,
                    fill="#ffffff",
                    anchor="middle",
                ),
                _conceptual_text(x + 80, 166, "RESOURCES", size=13, weight=700),
                _conceptual_text(x + 235, 166, "SERVICES", size=13, weight=700),
                f'<rect x="{x + 48}" y="187" width="115" height="44" rx="8" '
                f'fill="{soft}" stroke="{color}" stroke-width="2"/>',
                f'<rect x="{x + 203}" y="187" width="115" height="44" rx="8" '
                f'fill="{soft}" stroke="{color}" stroke-width="2"/>',
                _conceptual_text(
                    x + 105,
                    215,
                    str(card["input"]),
                    size=14,
                    weight=700,
                    fill=color,
                    anchor="middle",
                ),
                _conceptual_text(
                    x + 260,
                    215,
                    str(card["output"]),
                    size=14,
                    weight=700,
                    fill=color,
                    anchor="middle",
                ),
                _conceptual_text(
                    x + 160,
                    285,
                    "Score-driving account",
                    size=15,
                    anchor="middle",
                ),
                _conceptual_text(
                    x + 160,
                    318,
                    str(card["score"]),
                    size=17,
                    weight=700,
                    fill=color,
                    anchor="middle",
                ),
                _conceptual_text(
                    x + 160,
                    375,
                    str(card["line1"]),
                    size=14,
                    fill=GRAY,
                    anchor="middle",
                ),
                _conceptual_text(
                    x + 160,
                    397,
                    str(card["line2"]),
                    size=14,
                    fill=GRAY,
                    anchor="middle",
                ),
                f'<rect x="{x + 49}" y="425" width="222" height="22" rx="11" '
                f'fill="{soft}"/>',
                _conceptual_text(
                    x + 160,
                    441,
                    "one selected attainable plan",
                    size=12.5,
                    weight=700,
                    fill=color,
                    anchor="middle",
                ),
            ]
        )
    parts.extend(["</g>", "</svg>"])
    return "\n".join(parts)


def dynamic_sbm_carryovers() -> str:
    """Show how four carry-over roles join period operating accounts."""
    width, height = 1080, 760
    parts = _conceptual_base(
        width=width,
        height=height,
        title="One operating trajectory joined by four kinds of carry-over",
        description=(
            "Four period operating plans are joined by beneficial capacity, "
            "harmful backlog, discretionary inventory, and fixed commitments."
        ),
    )
    parts.extend(
        [
            _conceptual_text(
                42,
                44,
                "Today\N{RIGHT SINGLE QUOTATION MARK}s operating plan becomes "
                "part of tomorrow\N{RIGHT SINGLE QUOTATION MARK}s opportunity",
                size=24,
                weight=700,
            ),
            _conceptual_text(
                42,
                73,
                "Dynamic SBM appraises one connected trajectory—not four scorecards.",
                size=17,
                fill=GRAY,
            ),
            '<rect x="42" y="102" width="996" height="178" rx="18" '
            'fill="#f6f9fa" stroke="#cfdadd"/>',
            _conceptual_text(
                66,
                132,
                "OPERATING ACCOUNTS IN EACH PERIOD",
                size=15,
                weight=700,
                fill=TEAL,
            ),
        ]
    )
    for period, x in enumerate((72, 320, 568, 816), start=1):
        parts.extend(
            [
                f'<rect x="{x}" y="158" width="194" height="86" rx="12" '
                'fill="#ffffff" stroke="#9fc8cb"/>',
                _conceptual_text(
                    x + 97,
                    186,
                    f"Period {period}",
                    size=18,
                    weight=700,
                    anchor="middle",
                ),
                _conceptual_text(
                    x + 97,
                    214,
                    "resources → services",
                    size=15,
                    fill=GRAY,
                    anchor="middle",
                ),
                _conceptual_text(
                    x + 97,
                    234,
                    f"peer plan λ{period}",
                    size=13,
                    fill=TEAL,
                    anchor="middle",
                ),
            ]
        )
    parts.extend(
        [
            '<rect x="42" y="306" width="996" height="356" rx="18" '
            'fill="#fffdf9" stroke="#e2d6c7"/>',
            _conceptual_text(
                66,
                338,
                "CARRY-OVERS CONNECT ADJACENT MANAGEMENT PLANS",
                size=15,
                weight=700,
                fill="#8c642f",
            ),
        ]
    )
    carryovers = (
        ("GOOD · BENEFICIAL", "capacity, know-how, trust", "#237a57", "#edf7f1"),
        ("BAD · HARMFUL", "backlog, debt, pollution stock", "#b84a3a", "#fbefed"),
        ("FREE · REPLANNABLE", "inventory, liquid balances", BLUE, "#edf4fa"),
        ("FIXED · INHERITED", "regulated or contracted stock", PURPLE, "#f4eff8"),
    )
    for index, (label, example, color, soft) in enumerate(carryovers):
        y = 363 + 71 * index
        parts.extend(
            [
                f'<rect x="69" y="{y}" width="206" height="54" rx="10" '
                f'fill="{soft}" stroke="{color}"/>',
                _conceptual_text(88, y + 22, label, size=15, weight=700, fill=color),
                _conceptual_text(88, y + 42, example, size=13, fill=GRAY),
                f'<line x1="293" y1="{y + 27}" x2="990" y2="{y + 27}" '
                f'stroke="{color}" stroke-width="5"/>',
                f'<path d="M990 {y + 19} L1008 {y + 27} L990 {y + 35} z" '
                f'fill="{color}"/>',
            ]
        )
        for x in (417, 665, 913):
            parts.append(
                f'<circle cx="{x}" cy="{y + 27}" r="8" fill="#ffffff" '
                f'stroke="{color}" stroke-width="3"/>'
            )
    parts.extend(
        [
            f'<rect x="42" y="687" width="996" height="48" rx="12" fill="{INK}"/>',
            _conceptual_text(
                540,
                708,
                "ONE HORIZON-WIDE PERFORMANCE ACCOUNT",
                size=16,
                weight=700,
                fill="#ffffff",
                anchor="middle",
            ),
            _conceptual_text(
                540,
                727,
                "Carry-over continuity makes the selected operating plan attainable.",
                size=14,
                fill="#d7e2e5",
                anchor="middle",
            ),
            "</g>",
            "</svg>",
        ]
    )
    return "\n".join(parts)


def metafrontier_management_account() -> str:
    """Show the economic account behind the radial metafrontier identity."""
    width, height = 1200, 720
    parts = _conceptual_base(
        width=width,
        height=height,
        title="The management account behind a radial metafrontier decomposition",
        description=(
            "One organization produces two services with four resources. Its "
            "group opportunity supports four services and the pooled opportunity "
            "supports eight, yielding group efficiency one half, MTR one half, "
            "and metafrontier efficiency one quarter."
        ),
    )
    parts.extend(
        [
            '<rect width="1200" height="720" fill="#f7fafc"/>',
            _conceptual_text(
                60,
                58,
                "One organization, three performance accounts",
                size=30,
                weight=700,
            ),
            _conceptual_text(
                60,
                88,
                "The operation stays fixed; only the represented opportunity "
                "set changes.",
                size=17,
                fill=GRAY,
            ),
        ]
    )
    cards = (
        (55, "Observed operation", "Organization C · Group 1", 2, "actual", GRAY),
        (450, "Group opportunity", "Best practice within Group 1", 4, "0.50", TEAL),
        (
            845,
            "Pooled meta opportunity",
            "Best practice across groups",
            8,
            "0.25",
            BLUE,
        ),
    )
    for x, title, subtitle, services, account, color in cards:
        service_height = 22 * services
        service_y = 340 - service_height
        parts.extend(
            [
                f'<rect x="{x}" y="130" width="300" height="300" rx="18" '
                f'fill="#ffffff" stroke="{color}" stroke-width="2"/>',
                _conceptual_text(x + 30, 172, title, size=21, weight=700),
                _conceptual_text(x + 30, 200, subtitle, size=15, fill=GRAY),
                f'<line x1="{x + 30}" y1="340" x2="{x + 270}" y2="340" '
                'stroke="#e2e8f0"/>',
                f'<rect x="{x + 50}" y="252" width="70" height="88" rx="6" '
                f'fill="{ORANGE}"/>',
                f'<rect x="{x + 175}" y="{service_y}" width="70" '
                f'height="{service_height}" rx="6" fill="{color}"/>',
                _conceptual_text(x + 68, 241, "4", size=24, weight=700),
                _conceptual_text(
                    x + 197,
                    service_y - 12,
                    str(services),
                    size=24,
                    weight=700,
                ),
                _conceptual_text(x + 40, 370, "Resource units", size=15),
                _conceptual_text(x + 175, 370, "Services", size=15),
            ]
        )
        if account == "actual":
            parts.append(
                _conceptual_text(
                    x + 30,
                    404,
                    "What the organization actually delivered",
                    size=14,
                    fill=GRAY,
                )
            )
        else:
            label = "Group efficiency" if account == "0.50" else "Meta efficiency"
            parts.append(
                _conceptual_text(
                    x + 30,
                    404,
                    f"{label} = 2 ÷ {services} = {account}",
                    size=15,
                    weight=700,
                    fill=color,
                )
            )
    for x in (365, 760):
        parts.extend(
            [
                f'<line x1="{x}" y1="245" x2="{x + 62}" y2="245" '
                f'stroke="{GRAY}" stroke-width="3"/>',
                f'<path d="M{x + 62} 238 L{x + 76} 245 L{x + 62} 252 z" '
                f'fill="{GRAY}"/>',
            ]
        )
    parts.extend(
        [
            '<rect x="170" y="475" width="860" height="105" rx="20" fill="#1e3a8a"/>',
            _conceptual_text(
                600,
                520,
                "0.25 meta efficiency = 0.50 group efficiency "
                "\N{MULTIPLICATION SIGN} 0.50 MTR",
                size=23,
                weight=700,
                fill="#ffffff",
                anchor="middle",
            ),
            _conceptual_text(
                600,
                551,
                "A larger MTR means closer proximity to represented pooled "
                "opportunities.",
                size=15,
                fill="#dbeafe",
                anchor="middle",
            ),
            '<rect x="85" y="615" width="1030" height="68" rx="14" '
            'fill="#fff7ed" stroke="#fdba74" stroke-width="2"/>',
            _conceptual_text(
                115,
                645,
                "This is an accounting decomposition—not a causal attribution.",
                size=15,
                weight=700,
                fill="#7c2d12",
            ),
            _conceptual_text(
                115,
                668,
                "A pooled VRS benchmark may be a virtual cross-group combination.",
                size=15,
                weight=700,
                fill="#7c2d12",
            ),
            "</g>",
            "</svg>",
        ]
    )
    return "\n".join(parts)


def weak_disposal_technologies() -> str:
    """Distinguish equality-only, common-factor, and activity-specific accounts."""
    width, height = 600, 960
    parts = _conceptual_base(
        width=width,
        height=height,
        title="Three distinct bad-output formulations",
        description=(
            "A bad-output equality alone leaves scale and convexity unspecified. "
            "A common-factor CRS account uses one retention rate, while an "
            "activity-specific VRS account permits reference-specific rates."
        ),
    )
    blocks = (
        (30, 270, "Equality only", "#f2f4f5", "#8d9aa0"),
        (330, 270, "Common factor (CRS)", "#e9f4f5", TEAL),
        (630, 300, "Activity-specific (VRS)", "#f2edf6", PURPLE),
    )
    for y, block_height, title, soft, color in blocks:
        parts.extend(
            [
                f'<rect x="24" y="{y}" width="552" height="{block_height}" '
                f'rx="16" fill="{soft}" stroke="{color}" stroke-width="2"/>',
                _conceptual_text(48, y + 40, title, size=23, weight=700),
            ]
        )
    parts.extend(
        [
            '<rect x="48" y="94" width="190" height="72" rx="10" '
            'fill="#ffffff" stroke="#8d9aa0" stroke-width="2"/>',
            _conceptual_text(143, 120, "Bad-output account", size=16, anchor="middle"),
            _conceptual_text(143, 150, "Bλ = b̂", size=22, weight=700, anchor="middle"),
            '<line x1="255" y1="130" x2="328" y2="130" stroke="#8d9aa0" '
            'stroke-width="3" stroke-dasharray="7 6"/>',
            '<circle cx="374" cy="130" r="31" fill="#d97732"/>',
            _conceptual_text(
                374,
                141,
                "?",
                size=30,
                weight=700,
                fill="#ffffff",
                anchor="middle",
            ),
            _conceptual_text(
                48,
                207,
                "Scale and convexity are still unspecified.",
                size=17,
            ),
            _conceptual_text(
                48,
                235,
                "Equality does not, by itself, identify a named",
                size=17,
            ),
            _conceptual_text(48, 263, "weak-disposal technology.", size=17),
        ]
    )
    for index, name in enumerate(("Plant A", "Plant B", "Plant C")):
        x = 48 + 110 * index
        parts.extend(
            [
                f'<rect x="{x}" y="395" width="95" height="75" rx="8" '
                f'fill="#ffffff" stroke="{TEAL}" stroke-width="2"/>',
                _conceptual_text(
                    x + 47,
                    423,
                    name,
                    size=16,
                    weight=700,
                    anchor="middle",
                ),
                f'<rect x="{x + 21}" y="440" width="53" height="16" rx="4" '
                f'fill="{TEAL}"/>',
            ]
        )
    parts.extend(
        [
            f'<rect x="429" y="394" width="123" height="77" rx="10" fill="{TEAL}"/>',
            _conceptual_text(
                490,
                421,
                "one retention",
                size=16,
                weight=700,
                fill="#ffffff",
                anchor="middle",
            ),
            _conceptual_text(
                490,
                447,
                "rate r",
                size=18,
                weight=700,
                fill="#ffffff",
                anchor="middle",
            ),
            _conceptual_text(
                48,
                515,
                "Every represented activity is retained at",
                size=17,
            ),
            _conceptual_text(
                48,
                543,
                "the same rate within the CRS portfolio.",
                size=17,
            ),
            _conceptual_text(
                48,
                574,
                "The linear source identity relies on CRS.",
                size=16,
                fill=TEAL,
            ),
        ]
    )
    rates = (".9", ".5", ".7")
    for index, (name, rate) in enumerate(
        zip(("Plant A", "Plant B", "Plant C"), rates, strict=True)
    ):
        x = 48 + 110 * index
        height_value = 25 - 6 * index if index < 2 else 19
        parts.extend(
            [
                f'<rect x="{x}" y="695" width="95" height="103" rx="8" '
                f'fill="#ffffff" stroke="{PURPLE}" stroke-width="2"/>',
                _conceptual_text(
                    x + 47,
                    723,
                    name,
                    size=16,
                    weight=700,
                    anchor="middle",
                ),
                f'<rect x="{x + 21}" y="{765 - height_value}" width="53" '
                f'height="{height_value}" rx="4" fill="{PURPLE}"/>',
                _conceptual_text(
                    x + 47,
                    787,
                    f"retention = {rate}",
                    size=13,
                    anchor="middle",
                ),
            ]
        )
    parts.extend(
        [
            f'<rect x="429" y="701" width="123" height="90" rx="10" fill="{PURPLE}"/>',
            _conceptual_text(
                490,
                729,
                "different",
                size=16,
                weight=700,
                fill="#ffffff",
                anchor="middle",
            ),
            _conceptual_text(
                490,
                754,
                "retention rates",
                size=16,
                weight=700,
                fill="#ffffff",
                anchor="middle",
            ),
            _conceptual_text(
                490,
                779,
                "rj",
                size=18,
                weight=700,
                fill="#ffffff",
                anchor="middle",
            ),
            _conceptual_text(
                48,
                840,
                "Reference activities may carry different",
                size=17,
            ),
            _conceptual_text(
                48,
                868,
                "rates inside one VRS convex portfolio.",
                size=17,
            ),
            _conceptual_text(
                48,
                901,
                "The convex linearization retains VRS.",
                size=16,
                fill=PURPLE,
            ),
            "</g>",
            "</svg>",
        ]
    )
    return "\n".join(parts)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    figures = {
        "frontier-orientations.svg": frontier_orientations(),
        "crs-vrs-frontiers.svg": crs_vrs(),
        "local-rts-operating-response.svg": local_rts_operating_response(),
        "directional-scale-priority-scenarios.svg": (
            directional_scale_priority_scenarios()
        ),
        "mpss-productivity-profile.svg": mpss_productivity_profile(),
        "physical-capacity-account.svg": physical_capacity_account(),
        "convex-virtual-dmu.svg": convex_combination(),
        "fdh-vs-convex.svg": fdh_vs_convex(),
        "fdh-frh-crs-replication.svg": fdh_frh_crs_replication(),
        "fch-coordination-hulls.svg": fch_coordination_hulls(),
        "radial-and-slack.svg": radial_and_slack(),
        "sbm-relative-slacks.svg": sbm_relative_slacks(),
        "ddf-directions.svg": ddf_directions(),
        "environmental-disposability.svg": environmental_disposability(),
        "undesirable-sbm-components.svg": undesirable_sbm_components(),
        "by-production-intersection.svg": by_production_intersection(),
        "bp-ddf-vs-fgl.svg": bp_ddf_vs_fgl(),
        "material-balance-flow.svg": material_balance_flow(),
        "material-balance-management-targets.svg": (
            material_balance_management_targets()
        ),
        "productivity-frontier-motion.svg": productivity_frontier_motion(),
        "luenberger-programme-ledger.svg": luenberger_programme_ledger(),
        "malmquist-luenberger-frontier-account.svg": (
            malmquist_luenberger_frontier_account()
        ),
        "hicks-moorsteen-accounting.svg": hicks_moorsteen_accounting(),
        "four-distance-matrix.svg": four_distance_matrix(),
        "environmental-four-distance-matrix.svg": four_distance_matrix(
            environmental=True
        ),
        "reference-technology-windows.svg": reference_technology_windows(),
        "study-composition-map.svg": study_composition_map(),
        "economic-objectives-management-map.svg": (
            economic_objectives_management_map()
        ),
        "revenue-technical-allocative.svg": revenue_technical_allocative(),
        "profit-recovery-bridge.svg": profit_recovery_bridge(),
        "profitability-diagnostic-dashboard.svg": (
            profitability_diagnostic_dashboard()
        ),
        "gdf-management-contracts.svg": gdf_management_contracts(),
        "gdf-scale-assumptions.svg": gdf_scale_assumptions(),
        "two-stage-responsibility-chain.svg": two_stage_responsibility_chain(),
        "two-stage-accounting-choices.svg": two_stage_accounting_choices(),
        "closed-vs-open-network.svg": closed_vs_open_network(),
        "network-sbm-governance.svg": network_sbm_governance(),
        "dynamic-sbm-carryovers.svg": dynamic_sbm_carryovers(),
        "metafrontier-management-account.svg": metafrontier_management_account(),
        "sbm-management-questions.svg": sbm_management_questions(),
        "weak-disposal-technologies.svg": weak_disposal_technologies(),
        "dynamic-network-management-map.svg": dynamic_network_management_map(),
        "range-directional-signed-opportunity.svg": (
            range_directional_signed_opportunity()
        ),
    }
    for filename, content in figures.items():
        (OUTPUT_DIR / filename).write_text(content + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
