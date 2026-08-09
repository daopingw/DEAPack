from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from deapack import (
    CoelliMaterialBalanceDEA,
    DEAData,
    MaterialBalanceCoefficients,
    MaterialBalanceDEA,
)
from deapack.exceptions import DataValidationError, ModelSpecificationError


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "dmu": ["A", "B", "C", "D"],
            "x1": [1.0, 3.0, 2.0, 4.0],
            "x2": [3.0, 1.0, 2.0, 4.0],
            "y": [1.0, 1.0, 1.0, 1.0],
        }
    )


def _data(frame: pd.DataFrame | None = None) -> DEAData:
    return DEAData.from_frame(
        _frame() if frame is None else frame,
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs=["y"],
    )


def _coefficients(scale: float = 1.0) -> MaterialBalanceCoefficients:
    return MaterialBalanceCoefficients(
        inputs={"phosphorus": {"x1": scale, "x2": 3.0 * scale}},
        outputs={"phosphorus": {"y": scale}},
    )


def test_material_balance_decomposes_environmental_efficiency() -> None:
    result = MaterialBalanceDEA(_coefficients(), returns_to_scale="vrs").fit(_data())
    summary = result.summary().set_index("dmu_id")

    assert summary.loc["C", "technical_efficiency"] == pytest.approx(1.0)
    assert summary.loc["C", "environmental_allocative_efficiency"] == (
        pytest.approx(0.75)
    )
    assert summary.loc["C", "efficiency"] == pytest.approx(0.75)

    assert summary.loc["D", "technical_efficiency"] == pytest.approx(0.5)
    assert summary.loc["D", "environmental_allocative_efficiency"] == (
        pytest.approx(0.75)
    )
    assert summary.loc["D", "efficiency"] == pytest.approx(0.375)
    assert summary.loc["D", "observed_material_inflow"] == pytest.approx(16.0)
    assert summary.loc["D", "minimum_material_inflow"] == pytest.approx(6.0)
    assert summary.loc["D", "observed_material_surplus"] == pytest.approx(15.0)
    assert summary.loc["D", "minimum_material_surplus"] == pytest.approx(5.0)
    assert summary.loc["D", "efficiency"] == pytest.approx(
        summary.loc["D", "technical_efficiency"]
        * summary.loc["D", "environmental_allocative_efficiency"]
    )
    assert not bool(summary.loc["D", "is_material_efficient"])
    assert summary["is_efficient"].isna().all()


def test_material_efficiency_does_not_hide_a_nonmaterial_input_excess() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "material_input": [1.0, 1.0],
            "other_input": [1.0, 2.0],
            "output": [1.0, 1.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["material_input", "other_input"],
        outputs="output",
    )
    coefficients = MaterialBalanceCoefficients(
        inputs={
            "material": {
                "material_input": 1.0,
                "other_input": 0.0,
            }
        },
        outputs={"material": {"output": 0.0}},
    )

    b = (
        MaterialBalanceDEA(coefficients, returns_to_scale="vrs")
        .fit(data)
        .summary()
        .set_index("dmu_id")
        .loc["B"]
    )

    assert bool(b["is_material_efficient"])
    assert pd.isna(b["is_efficient"])


def test_material_minimum_target_and_peers_are_labeled() -> None:
    result = CoelliMaterialBalanceDEA(_coefficients(), returns_to_scale="vrs").fit(
        _data()
    )
    targets = result.targets_for("D")
    material_inputs = targets.loc[
        (targets["target_type"] == "material_minimum") & (targets["role"] == "input")
    ].set_index("variable")

    assert material_inputs.loc["x1", "target"] == pytest.approx(3.0)
    assert material_inputs.loc["x2", "target"] == pytest.approx(1.0)
    surplus = targets.loc[
        (targets["role"] == "material_surplus") & (targets["variable"] == "phosphorus")
    ].iloc[0]
    assert surplus["observed"] == pytest.approx(15.0)
    assert surplus["target"] == pytest.approx(5.0)

    peers = result.peers("D")
    environmental_peer = peers.loc[peers["component"] == "material_minimum"]
    assert environmental_peer["reference_dmu_id"].tolist() == ["B"]
    assert environmental_peer["lambda"].iloc[0] == pytest.approx(1.0)


def test_material_efficiency_is_invariant_to_coefficient_units() -> None:
    base = MaterialBalanceDEA(_coefficients(), returns_to_scale="vrs").fit(_data())
    scaled = MaterialBalanceDEA(
        _coefficients(scale=1000.0), returns_to_scale="vrs"
    ).fit(_data())

    np.testing.assert_allclose(
        base.summary()["efficiency"],
        scaled.summary()["efficiency"],
    )


def test_multiple_materials_require_and_retain_explicit_weights() -> None:
    with pytest.raises(ValueError, match="aggregation weights"):
        MaterialBalanceCoefficients(
            inputs={
                "phosphorus": {"x1": 1.0, "x2": 3.0},
                "nitrogen": {"x1": 3.0, "x2": 1.0},
            },
            outputs={
                "phosphorus": {"y": 1.0},
                "nitrogen": {"y": 1.0},
            },
        )

    coefficients = MaterialBalanceCoefficients(
        inputs={
            "phosphorus": {"x1": 1.0, "x2": 3.0},
            "nitrogen": {"x1": 3.0, "x2": 1.0},
        },
        outputs={
            "phosphorus": {"y": 1.0},
            "nitrogen": {"y": 1.0},
        },
        weights={"phosphorus": 0.75, "nitrogen": 0.25},
    )
    result = MaterialBalanceDEA(coefficients, returns_to_scale="vrs").fit(_data())
    summary = result.summary().set_index("dmu_id")

    assert summary.loc["C", "efficiency"] == pytest.approx(0.875)
    assert result.metadata["material_weights"] == {
        "phosphorus": 0.75,
        "nitrogen": 0.25,
    }
    material_rows = result.targets_for("C").query("role == 'material_surplus'")
    assert set(material_rows["variable"]) == {"phosphorus", "nitrogen"}


def test_material_balance_uses_panel_reference_plan() -> None:
    panel = pd.concat(
        [
            _frame().assign(period=2020),
            _frame().assign(period=2021),
        ],
        ignore_index=True,
    )
    data = DEAData.from_frame(
        panel,
        dmu="dmu",
        period="period",
        inputs=["x1", "x2"],
        outputs=["y"],
    )
    result = MaterialBalanceDEA(
        _coefficients(),
        returns_to_scale="vrs",
        reference="contemporaneous",
    ).fit(data)

    assert set(result.summary()["reference_size"]) == {4}
    assert result.metadata["compiled_reference_sets"] == 2


def test_material_balance_validates_coefficients_and_physical_identity() -> None:
    incomplete = MaterialBalanceCoefficients(
        inputs={"phosphorus": {"x1": 1.0}},
        outputs={"phosphorus": {"y": 1.0}},
    )
    with pytest.raises(ModelSpecificationError, match="explicitly match"):
        MaterialBalanceDEA(incomplete).fit(_data())

    with pytest.raises(ValueError, match="finite and nonnegative"):
        MaterialBalanceCoefficients(
            inputs={"phosphorus": {"x1": -1.0, "x2": 3.0}},
            outputs={"phosphorus": {"y": 1.0}},
        )

    physically_invalid = _frame().copy()
    physically_invalid.loc[0, ["x1", "x2"]] = [0.1, 0.1]
    with pytest.raises(DataValidationError, match="input content to cover"):
        MaterialBalanceDEA(_coefficients()).fit(_data(physically_invalid))


def test_material_balance_rejects_observed_bad_outputs() -> None:
    frame = _frame().assign(emissions=[1.0, 1.0, 1.0, 1.0])
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs=["y"],
        bad_outputs=["emissions"],
    )

    with pytest.raises(ModelSpecificationError, match="does not consume"):
        MaterialBalanceDEA(_coefficients()).fit(data)


@pytest.mark.parametrize("returns_to_scale", ["nirs", "ndrs"])
def test_source_unsupported_restricted_returns_fail_closed(
    returns_to_scale: str,
) -> None:
    with pytest.raises(ModelSpecificationError, match="only CRS and VRS"):
        MaterialBalanceDEA(
            _coefficients(),
            returns_to_scale=returns_to_scale,
        )
