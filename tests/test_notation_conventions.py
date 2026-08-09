from __future__ import annotations

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CONVENTIONS_PATH = REPOSITORY_ROOT / "specs" / "CONVENTIONS.md"


def _productivity_section() -> str:
    content = CONVENTIONS_PATH.read_text(encoding="utf-8")
    return content.split("## 13. Productivity", maxsplit=1)[1].split(
        "## 14. Prices and economic quantities",
        maxsplit=1,
    )[0]


def test_productivity_period_roles_respect_the_core_index_contract() -> None:
    content = CONVENTIONS_PATH.read_text(encoding="utf-8")
    productivity = _productivity_section()

    assert r"| $r=1,\ldots,s$ | `output` | desirable-output dimension |" in content
    assert r"$\sigma,\tau\in\{1,\ldots,T\}$" in content
    assert "`evaluated_period`, `technology_period`" in content
    assert r"$d^\tau(z^\sigma)$" in productivity
    assert r"$D^\tau(z^\sigma;g)$" in productivity
    assert r"$D^\tau(z^\sigma)$" in productivity
    assert r"\vec D" not in productivity
    assert r"BPG^\tau(z^\tau)" in productivity
    assert r"BG^\tau=" in productivity

    forbidden_period_notation = (
        r"d^r(z",
        r"\vec D^r",
        r"D_O^r",
        r"D_I^r",
        r"BPG^r",
        r"BG^r",
        r"period-$r$",
        r"period $r$",
        r"Q^{s,t}",
        r"X^{s,t}",
        r"HM^{s,t}",
    )
    for notation in forbidden_period_notation:
        assert notation not in productivity


def test_productivity_keeps_named_time_and_reference_notation() -> None:
    productivity = _productivity_section()

    for index in (
        "M",
        "L",
        "GM",
        "BM",
        "HM",
        "ML",
        "GML",
    ):
        assert rf"{index}^{{t,t+1}}" in productivity

    assert r"\mathcal{T}^G" in productivity
    assert r"\mathcal{T}^{B(t,t+1)}" in productivity
    assert "use $r$ and $s$ as period labels are crosswalked" in productivity
