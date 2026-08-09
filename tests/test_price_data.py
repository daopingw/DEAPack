from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import numpy as np
import pandas as pd
import pytest

from deapack import DEAData, PriceData, PriceSpec, ResolvedPrices
from deapack.exceptions import DataValidationError, ModelSpecificationError


def _data(*, panel: bool = False) -> DEAData:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "period": [2020, 2020],
            "labor": [1.0, 2.0],
            "capital": [3.0, 4.0],
            "service": [5.0, 6.0],
        }
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period" if panel else None,
        inputs=["capital", "labor"],
        outputs="service",
    )


def test_common_prices_align_by_quantity_name_and_are_read_only() -> None:
    prices = PriceData.common(
        input_prices={"labor": 20.0, "capital": 2.0},
        output_prices={"service": 7.0},
    )
    resolved = prices.resolve(
        _data(),
        require_inputs=True,
        require_outputs=True,
    )

    assert isinstance(resolved, ResolvedPrices)
    assert resolved.input_names == ("capital", "labor")
    assert resolved.output_names == ("service",)
    np.testing.assert_allclose(
        resolved.input_prices,
        [[2.0, 20.0], [2.0, 20.0]],
    )
    np.testing.assert_allclose(resolved.output_prices, [[7.0], [7.0]])
    assert not resolved.input_prices.flags.writeable
    assert not resolved.output_prices.flags.writeable
    assert resolved.input_prices.strides[0] == 0
    assert resolved.output_prices.strides[0] == 0
    with pytest.raises(ValueError, match="read-only"):
        resolved.input_prices[0, 0] = 99.0


def test_observation_prices_align_by_keys_not_source_row_order() -> None:
    prices = PriceData.from_frame(
        pd.DataFrame(
            {
                "unit": ["B", "A"],
                "w_labor": [40.0, 10.0],
                "w_capital": [4.0, 1.0],
            }
        ),
        input_prices={
            "labor": "w_labor",
            "capital": "w_capital",
        },
        dmu="unit",
    )
    resolved = prices.resolve(_data(), require_inputs=True)
    np.testing.assert_allclose(
        resolved.input_prices,
        [[1.0, 10.0], [4.0, 40.0]],
    )
    assert resolved.spec.scope == "by_observation"


def test_keyed_price_signature_is_invariant_to_source_row_order() -> None:
    first_frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "w": [1.0, 2.0],
        }
    )
    second_frame = first_frame.iloc[::-1].reset_index(drop=True)
    first = PriceData.from_frame(
        first_frame,
        input_prices={"capital": "w"},
        dmu="dmu",
    )
    second = PriceData.from_frame(
        second_frame,
        input_prices={"capital": "w"},
        dmu="dmu",
    )
    assert first.signature == second.signature
    assert (
        first.metadata()["input_price_signature"]["sha256"]
        == second.metadata()["input_price_signature"]["sha256"]
    )


def test_signatures_distinguish_values_variables_and_units() -> None:
    baseline = PriceData.common(input_prices={"capital": 1.0})
    changed_value = PriceData.common(input_prices={"capital": 2.0})
    changed_variable = PriceData.common(input_prices={"labor": 1.0})
    changed_units = PriceData.common(
        input_prices={"capital": 1.0},
        spec=PriceSpec(currency="GBP"),
    )

    assert len({baseline.signature, changed_value.signature}) == 2
    assert len({baseline.signature, changed_variable.signature}) == 2
    assert len({baseline.signature, changed_units.signature}) == 2
    assert (
        PriceData.common(input_prices={"labor": 2.0, "capital": 1.0}).signature
        == PriceData.common(input_prices={"capital": 1.0, "labor": 2.0}).signature
    )


def test_price_metadata_is_immutable_json_safe_and_has_no_payload() -> None:
    prices = PriceData.common(
        input_prices={"capital": 123.456789, "labor": 987.654321},
        spec=PriceSpec(
            source="market",
            currency="GBP",
            numeraire="2025_pounds",
            base_period=2025,
        ),
    )
    metadata = prices.metadata()
    serialized = json.dumps(metadata, allow_nan=False)

    assert metadata["scope"] == "common"
    assert metadata["source"] == "market"
    assert metadata["input_variables"] == ("capital", "labor")
    assert metadata["signature"] == prices.signature
    assert "123.456789" not in serialized
    assert "987.654321" not in serialized
    assert '"input_prices":' not in serialized
    with pytest.raises(TypeError, match="immutable"):
        metadata["source"] = "changed"
    with pytest.raises(TypeError, match="immutable"):
        metadata["input_price_signature"]["sha256"] = "changed"


def test_side_metadata_excludes_unused_prices_from_model_identity() -> None:
    inputs_only = PriceData.common(input_prices={"capital": 1.0, "labor": 2.0})
    both_sides = PriceData.common(
        input_prices={"capital": 1.0, "labor": 2.0},
        output_prices={"service": 500.0},
    )

    baseline = inputs_only.metadata(side="input")
    selected = both_sides.metadata(side="input")
    assert selected == baseline
    assert selected["price_side"] == "input"
    assert "output_variables" not in selected
    assert "output_price_signature" not in selected
    with pytest.raises(TypeError, match="immutable"):
        selected["price_side"] = "output"

    with pytest.raises(ValueError, match="side must be"):
        both_sides.metadata(side="bad")
    with pytest.raises(DataValidationError, match="no output prices"):
        inputs_only.metadata(side="output")


@pytest.mark.parametrize("value", [0.0, -1.0, np.nan, np.inf, -np.inf])
def test_prices_must_be_finite_and_strictly_positive(value: float) -> None:
    with pytest.raises(DataValidationError):
        PriceData.common(input_prices={"capital": value})


def test_price_names_must_match_every_quantity_name_exactly() -> None:
    data = _data()
    missing = PriceData.common(input_prices={"capital": 1.0})
    extra = PriceData.common(input_prices={"capital": 1.0, "labor": 2.0, "land": 3.0})

    with pytest.raises(DataValidationError, match="exactly match"):
        missing.resolve(data, require_inputs=True)
    with pytest.raises(DataValidationError, match="exactly match"):
        extra.resolve(data, require_inputs=True)


def test_required_price_side_fails_before_model_optimization() -> None:
    inputs_only = PriceData.common(input_prices={"capital": 1.0, "labor": 2.0})
    with pytest.raises(DataValidationError, match="requires output prices"):
        inputs_only.resolve(_data(), require_outputs=True)

    outputs_only = PriceData.common(output_prices={"service": 3.0})
    with pytest.raises(DataValidationError, match="requires input prices"):
        outputs_only.resolve(_data(), require_inputs=True)

    with pytest.raises(DataValidationError, match="at least one price side"):
        PriceData.common()


def test_by_observation_keys_must_match_exactly_and_be_unique() -> None:
    with pytest.raises(DataValidationError, match="keys must be unique"):
        PriceData.from_frame(
            pd.DataFrame(
                {
                    "dmu": ["A", "A"],
                    "w_capital": [1.0, 2.0],
                    "w_labor": [3.0, 4.0],
                }
            ),
            input_prices={
                "capital": "w_capital",
                "labor": "w_labor",
            },
            dmu="dmu",
        )

    missing_and_extra = PriceData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "C"],
                "w_capital": [1.0, 2.0],
                "w_labor": [3.0, 4.0],
            }
        ),
        input_prices={
            "capital": "w_capital",
            "labor": "w_labor",
        },
        dmu="dmu",
    )
    with pytest.raises(DataValidationError, match="exactly match DEA data"):
        missing_and_extra.resolve(_data(), require_inputs=True)


def test_cross_section_and_panel_key_schemas_cannot_be_mixed() -> None:
    cross_section_prices = PriceData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "w_capital": [1.0, 2.0],
                "w_labor": [3.0, 4.0],
            }
        ),
        input_prices={
            "capital": "w_capital",
            "labor": "w_labor",
        },
        dmu="dmu",
        spec=PriceSpec(
            scope="by_observation",
            currency="GBP",
            base_period=2020,
        ),
    )
    with pytest.raises(DataValidationError, match="key schemas differ"):
        cross_section_prices.resolve(_data(panel=True), require_inputs=True)


def test_panel_prices_require_base_period_and_explicit_currency() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "period": [2020, 2020],
            "w_capital": [1.0, 2.0],
            "w_labor": [3.0, 4.0],
        }
    )
    with pytest.raises(ModelSpecificationError, match="base_period"):
        PriceData.from_frame(
            frame,
            input_prices={
                "capital": "w_capital",
                "labor": "w_labor",
            },
            dmu="dmu",
            period="period",
        )

    unspecified_currency = PriceData.from_frame(
        frame,
        input_prices={
            "capital": "w_capital",
            "labor": "w_labor",
        },
        dmu="dmu",
        period="period",
        spec=PriceSpec(scope="by_observation", base_period=2020),
    )
    with pytest.raises(DataValidationError, match="explicit currency"):
        unspecified_currency.resolve(_data(panel=True), require_inputs=True)

    valid = PriceData.from_frame(
        frame.iloc[::-1],
        input_prices={
            "capital": "w_capital",
            "labor": "w_labor",
        },
        dmu="dmu",
        period="period",
        spec=PriceSpec(
            scope="by_observation",
            currency="GBP",
            base_period=2020,
        ),
    )
    resolved = valid.resolve(_data(panel=True), require_inputs=True)
    np.testing.assert_allclose(
        resolved.input_prices,
        [[1.0, 3.0], [2.0, 4.0]],
    )


def test_common_panel_prices_also_require_currency_and_base_period() -> None:
    data = _data(panel=True)
    with pytest.raises(DataValidationError, match="base_period"):
        PriceData.common(input_prices={"capital": 1.0, "labor": 2.0}).resolve(
            data, require_inputs=True
        )

    prices = PriceData.common(
        input_prices={"capital": 1.0, "labor": 2.0},
        spec=PriceSpec(currency="GBP", base_period=2020),
    )
    assert prices.resolve(data, require_inputs=True).n_observations == 2


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"scope": "regional"}, "scope must be"),
        ({"missing_policy": "drop"}, "missing_policy"),
        ({"sign_policy": "nonnegative"}, "sign_policy"),
        ({"denominator_tolerance": 0.0}, "denominator_tolerance"),
        ({"monetary_tolerance": np.inf}, "monetary_tolerance"),
        ({"source": ""}, "source"),
        ({"currency": ""}, "currency"),
    ],
)
def test_price_spec_rejects_unsupported_or_ambiguous_policies(
    kwargs: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ModelSpecificationError, match=message):
        PriceSpec(**kwargs)


def test_price_objects_are_deeply_immutable_at_the_array_boundary() -> None:
    prices = PriceData.common(input_prices={"capital": 1.0, "labor": 2.0})
    with pytest.raises(FrozenInstanceError):
        prices.spec = PriceSpec()  # type: ignore[misc]
    assert prices.input_prices is not None
    assert not prices.input_prices.flags.writeable
    with pytest.raises(ValueError, match="read-only"):
        prices.input_prices[0] = 9.0


def test_duplicate_dataframe_columns_are_rejected_explicitly() -> None:
    frame = pd.DataFrame(
        [["A", 1.0, 2.0]],
        columns=["dmu", "w", "w"],
    )
    with pytest.raises(DataValidationError, match="duplicate input price column"):
        PriceData.from_frame(
            frame,
            input_prices={"capital": "w"},
            dmu="dmu",
        )
