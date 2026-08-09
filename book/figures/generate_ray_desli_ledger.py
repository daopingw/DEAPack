"""Generate the enhanced-FGNZ and Ray--Desli allocation-ledger figure."""

from __future__ import annotations

from pathlib import Path

OUTPUT = (
    Path(__file__).resolve().parents[1]
    / "_static"
    / "figures"
    / "ray-desli-allocation-ledgers.svg"
)

FGNZ = (1.033588257553, 1.06, 1.032001479837)
RAY_DESLI = (1.033588257553, 1.113762846232, 0.982185365878)
PRODUCTIVITY_CHANGE = 1.130664488017


def _factor_card(
    *,
    x: int,
    y: int,
    fill: str,
    stroke: str,
    label: str,
    value: float,
) -> str:
    return "\n".join(
        [
            f'<rect x="{x}" y="{y}" width="156" height="76" rx="12" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>',
            f'<text x="{x + 78}" y="{y + 27}" text-anchor="middle" '
            f'font-size="13" font-weight="650" fill="#24323d">{label}</text>',
            f'<text x="{x + 78}" y="{y + 57}" text-anchor="middle" '
            f'font-size="23" font-weight="750" fill="{stroke}">{value:.4f}</text>',
        ]
    )


def _column_heading(*, x: int, first_line: str, second_line: str) -> str:
    return "\n".join(
        [
            f'<text x="{x}" y="99" text-anchor="middle" font-size="10.5" '
            'font-weight="650" fill="#5c6b74">',
            f'<tspan x="{x}" dy="0">{first_line}</tspan>',
            f'<tspan x="{x}" dy="11">{second_line}</tspan>',
            "</text>",
        ]
    )


def build_svg() -> str:
    fgnz_product = FGNZ[0] * FGNZ[1] * FGNZ[2]
    ray_product = RAY_DESLI[0] * RAY_DESLI[1] * RAY_DESLI[2]
    assert abs(fgnz_product - PRODUCTIVITY_CHANGE) < 1e-10
    assert abs(ray_product - PRODUCTIVITY_CHANGE) < 1e-10

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="500" '
        'viewBox="0 0 1080 500" role="img" '
        'aria-labelledby="title description">',
        '<title id="title">One productivity change, two literature-defined '
        "allocation ledgers</title>",
        '<desc id="description">FGNZ and Ray--Desli allocate the same productivity '
        "change and pure-efficiency change to different opportunity and scale "
        "factors.</desc>",
        '<rect width="1080" height="500" fill="#ffffff"/>',
        '<text x="540" y="38" text-anchor="middle" font-size="24" '
        'font-weight="750" fill="#24323d">One productivity change, two '
        "literature-defined allocation ledgers</text>",
        '<text x="540" y="66" text-anchor="middle" font-size="14.5" '
        'fill="#5c6b74">Organization D, 2020&#8211;2021 · common CRS Malmquist '
        "index = 1.1307</text>",
        '<rect x="28" y="91" width="1024" height="151" rx="16" '
        'fill="#f7fafb" stroke="#aebdc3"/>',
        '<rect x="28" y="257" width="1024" height="151" rx="16" '
        'fill="#f2f9f9" stroke="#79afb4" stroke-width="1.8"/>',
        '<text x="43" y="119" font-size="15" font-weight="750" '
        'fill="#356fa3">ENHANCED FGNZ METHOD</text>',
        '<text x="43" y="139" font-size="12.5" fill="#5c6b74">public '
        "six-task source method</text>",
        '<text x="43" y="285" font-size="15" font-weight="750" '
        'fill="#176b73">RAY&#8211;DESLI METHOD</text>',
        '<text x="43" y="305" font-size="12.5" fill="#5c6b74">public '
        "source-qualified eight-task method</text>",
        _column_heading(
            x=340,
            first_line="PURE OPERATING",
            second_line="PERFORMANCE",
        ),
        _column_heading(
            x=524,
            first_line="REPRESENTED",
            second_line="OPPORTUNITIES",
        ),
        _column_heading(
            x=708,
            first_line="SCALE-RELATED",
            second_line="ACCOUNT",
        ),
        _column_heading(
            x=938,
            first_line="OVERALL",
            second_line="CHANGE",
        ),
    ]

    for y, values, labels in (
        (136, FGNZ, ("PEFFCH", "TECHCH(C)", "own-period SCH")),
        (302, RAY_DESLI, ("PEFFCH", "TECHCH(V)", "SCH(V)")),
    ):
        parts.extend(
            [
                _factor_card(
                    x=262,
                    y=y,
                    fill="#e8f0f8",
                    stroke="#356fa3",
                    label=labels[0],
                    value=values[0],
                ),
                f'<text x="432" y="{y + 48}" text-anchor="middle" '
                'font-size="25" font-weight="650" fill="#5c6b74">&#215;</text>',
                _factor_card(
                    x=446,
                    y=y,
                    fill="#e1f1f1",
                    stroke="#176b73",
                    label=labels[1],
                    value=values[1],
                ),
                f'<text x="616" y="{y + 48}" text-anchor="middle" '
                'font-size="25" font-weight="650" fill="#5c6b74">&#215;</text>',
                _factor_card(
                    x=630,
                    y=y,
                    fill="#f9e9dd",
                    stroke="#ad4f16",
                    label=labels[2],
                    value=values[2],
                ),
                f'<text x="803" y="{y + 48}" text-anchor="middle" '
                'font-size="25" font-weight="650" fill="#5c6b74">=</text>',
                f'<rect x="824" y="{y}" width="210" height="76" rx="12" '
                'fill="#24323d"/>',
                f'<text x="929" y="{y + 27}" text-anchor="middle" '
                'font-size="13" font-weight="650" fill="#d7e2e5">M</text>',
                f'<text x="929" y="{y + 57}" text-anchor="middle" '
                'font-size="23" font-weight="750" fill="#ffffff">1.1307</text>',
            ]
        )

    parts.extend(
        [
            '<rect x="118" y="427" width="844" height="50" rx="12" '
            'fill="#ffffff" stroke="#d6e0e3"/>',
            '<text x="540" y="448" text-anchor="middle" font-size="13.5" '
            'font-weight="700" fill="#24323d">Factors multiply; equal-width '
            "boxes are not additive shares.</text>",
            '<text x="540" y="467" text-anchor="middle" font-size="12.5" '
            'fill="#5c6b74">Both rows are benchmark-conditional accounts, '
            "not causal explanations of management or innovation.</text>",
            "</svg>",
        ]
    )
    return "\n".join(parts)


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build_svg() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
