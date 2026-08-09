"""Generate the APZ environmental-opportunity account figure."""

from __future__ import annotations

from pathlib import Path

OUTPUT = (
    Path(__file__).resolve().parents[1]
    / "_static"
    / "figures"
    / "apz-consistency-account.svg"
)


def _rounded_box(
    *,
    x: int,
    y: int,
    width: int,
    height: int,
    fill: str,
    stroke: str,
) -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="14" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>'
    )


def build_svg() -> str:
    efficiency_change = 77 / 80
    technical_change = 8 / 7
    productivity_change = 11 / 10
    assert abs(efficiency_change * technical_change - productivity_change) < 1e-12

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="570" '
        'viewBox="0 0 1120 570" role="img" '
        'aria-labelledby="title description">',
        '<title id="title">The same cleaner transition under two environmental '
        "opportunity accounts</title>",
        '<desc id="description">The conventional equality account leaves one '
        "cross-period task unavailable. The APZ bounded inequality account "
        "re-solves all four tasks and reports exact productivity components.</desc>",
        '<rect width="1120" height="570" fill="#ffffff"/>',
        '<text x="560" y="38" text-anchor="middle" font-size="24" '
        'font-weight="750" fill="#24323d">The same cleaner transition, two '
        "environmental opportunity accounts</text>",
        '<text x="560" y="66" text-anchor="middle" font-size="14" '
        'fill="#5c6b74">Unit B: resources 1 &#8594; 1 · service 5 &#8594; 5.5 · '
        "residual 5 &#8594; 3</text>",
        _rounded_box(
            x=32,
            y=94,
            width=286,
            height=402,
            fill="#f7fafb",
            stroke="#aebdc3",
        ),
        '<text x="175" y="126" text-anchor="middle" font-size="15" '
        'font-weight="750" fill="#24323d">WHAT MANAGEMENT OBSERVES</text>',
        '<circle cx="101" cy="206" r="46" fill="#e8f0f8" '
        'stroke="#356fa3" stroke-width="2"/>',
        '<text x="101" y="197" text-anchor="middle" font-size="13" '
        'font-weight="700" fill="#356fa3">EARLIER</text>',
        '<text x="101" y="220" text-anchor="middle" font-size="17" '
        'font-weight="750" fill="#24323d">y=5, b=5</text>',
        '<path d="M151 206 H219" stroke="#176b73" stroke-width="4" '
        'marker-end="url(#arrow)"/>',
        '<circle cx="260" cy="206" r="46" fill="#e1f1f1" '
        'stroke="#176b73" stroke-width="2"/>',
        '<text x="260" y="197" text-anchor="middle" font-size="13" '
        'font-weight="700" fill="#176b73">LATER</text>',
        '<text x="260" y="220" text-anchor="middle" font-size="17" '
        'font-weight="750" fill="#24323d">y=5.5, b=3</text>',
        '<text x="175" y="294" text-anchor="middle" font-size="15" '
        'font-weight="700" fill="#176b73">more service, less residual</text>',
        '<text x="175" y="325" text-anchor="middle" font-size="12.5" '
        'fill="#5c6b74">This is favorable operating evidence.</text>',
        '<text x="175" y="345" text-anchor="middle" font-size="12.5" '
        'fill="#5c6b74">The index still depends on the declared</text>',
        '<text x="175" y="365" text-anchor="middle" font-size="12.5" '
        'fill="#5c6b74">pollution opportunity account.</text>',
        '<rect x="61" y="404" width="228" height="62" rx="10" '
        'fill="#ffffff" stroke="#d6e0e3"/>',
        '<text x="175" y="429" text-anchor="middle" font-size="12.5" '
        'font-weight="700" fill="#24323d">Not yet a causal conclusion</text>',
        '<text x="175" y="450" text-anchor="middle" font-size="11.5" '
        'fill="#5c6b74">No claim about regulation or innovation</text>',
        _rounded_box(
            x=340,
            y=94,
            width=354,
            height=181,
            fill="#fff6f0",
            stroke="#c76b32",
        ),
        '<text x="517" y="126" text-anchor="middle" font-size="15" '
        'font-weight="750" fill="#ad4f16">CONVENTIONAL EQUALITY ACCOUNT</text>',
        '<text x="517" y="154" text-anchor="middle" font-size="13" '
        'fill="#24323d">peer residual = directional residual target</text>',
        '<text x="517" y="184" text-anchor="middle" font-size="12.5" '
        'fill="#5c6b74">One reverse cross-period task cannot be represented.</text>',
        '<rect x="390" y="205" width="254" height="44" rx="9" fill="#ad4f16"/>',
        '<text x="517" y="233" text-anchor="middle" font-size="14" '
        'font-weight="750" fill="#ffffff">complete adjacent ML unavailable</text>',
        _rounded_box(
            x=340,
            y=294,
            width=354,
            height=202,
            fill="#eef8f7",
            stroke="#26858b",
        ),
        '<text x="517" y="326" text-anchor="middle" font-size="15" '
        'font-weight="750" fill="#176b73">APZ BOUNDED INEQUALITY ACCOUNT</text>',
        '<text x="517" y="354" text-anchor="middle" font-size="13" '
        'fill="#24323d">peer residual &#8804; directional target '
        "&#8804; period cap</text>",
        '<text x="517" y="381" text-anchor="middle" font-size="12.5" '
        'fill="#5c6b74">earlier-period cap = 5 · later-period cap = 3</text>',
        '<rect x="390" y="397" width="254" height="78" rx="9" fill="#176b73"/>',
        '<text x="517" y="421" text-anchor="middle" font-size="12.5" '
        'font-weight="700" fill="#d8f1ef">all four tasks re-solved</text>',
        '<text x="517" y="444" text-anchor="middle" font-size="11.5" '
        'font-weight="700" fill="#ffffff">old/old 2/5 · later/old 3/11</text>',
        '<text x="517" y="462" text-anchor="middle" font-size="11.5" '
        'font-weight="700" fill="#ffffff">old/later 3/5 · later/later 5/11</text>',
        '<path d="M710 395 H756" stroke="#176b73" stroke-width="4" '
        'marker-end="url(#arrow)"/>',
        _rounded_box(
            x=760,
            y=94,
            width=328,
            height=402,
            fill="#f5f8fb",
            stroke="#6e8da3",
        ),
        '<text x="924" y="126" text-anchor="middle" font-size="15" '
        'font-weight="750" fill="#24323d">APZ ACCOUNT FOR UNIT B</text>',
        '<rect x="796" y="158" width="256" height="70" rx="12" fill="#24323d"/>',
        '<text x="924" y="184" text-anchor="middle" font-size="12.5" '
        'fill="#d7e2e5">ENVIRONMENTAL PRODUCTIVITY</text>',
        '<text x="924" y="213" text-anchor="middle" font-size="24" '
        'font-weight="750" fill="#ffffff">ML = 1.1000</text>',
        '<rect x="796" y="248" width="120" height="82" rx="11" '
        'fill="#e8f0f8" stroke="#356fa3"/>',
        '<text x="856" y="273" text-anchor="middle" font-size="12" '
        'font-weight="700" fill="#356fa3">OPERATING</text>',
        '<text x="856" y="301" text-anchor="middle" font-size="20" '
        'font-weight="750" fill="#24323d">77/80</text>',
        '<rect x="932" y="248" width="120" height="82" rx="11" '
        'fill="#e1f1f1" stroke="#176b73"/>',
        '<text x="992" y="273" text-anchor="middle" font-size="12" '
        'font-weight="700" fill="#176b73">OPPORTUNITY</text>',
        '<text x="992" y="301" text-anchor="middle" font-size="20" '
        'font-weight="750" fill="#24323d">8/7</text>',
        '<text x="924" y="359" text-anchor="middle" font-size="13.5" '
        'font-weight="700" fill="#24323d">0.9625 &#215; 1.1429 = 1.1000</text>',
        '<text x="924" y="393" text-anchor="middle" font-size="12.5" '
        'fill="#5c6b74">A small widening of the relative operating</text>',
        '<text x="924" y="413" text-anchor="middle" font-size="12.5" '
        'fill="#5c6b74">shortfall is more than offset by a more</text>',
        '<text x="924" y="433" text-anchor="middle" font-size="12.5" '
        'fill="#5c6b74">favorable represented opportunity.</text>',
        '<defs><marker id="arrow" markerWidth="9" markerHeight="9" '
        'refX="8" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 z" '
        'fill="#176b73"/></marker></defs>',
        '<rect x="174" y="522" width="772" height="34" rx="9" '
        'fill="#ffffff" stroke="#d6e0e3"/>',
        '<text x="560" y="544" text-anchor="middle" font-size="12.5" '
        'fill="#5c6b74">APZ changes the represented production opportunity; '
        "it does not re-label a conventional ML result.</text>",
        "</svg>",
    ]
    return "\n".join(parts)


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build_svg() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
