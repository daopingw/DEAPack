import pandas as pd
import pytest

from deapack import DEAData
from deapack.exceptions import DataValidationError


def test_from_frame_builds_read_only_solver_arrays() -> None:
    frame = pd.DataFrame(
        {
            "unit": ["A", "B"],
            "year": [2020, 2020],
            "labor": [1.0, 2.0],
            "output": [1.0, 1.0],
        }
    )

    data = DEAData.from_frame(
        frame,
        dmu="unit",
        period="year",
        inputs=["labor"],
        outputs=["output"],
    )

    assert data.n_dmus == 2
    assert data.input_names == ("labor",)
    assert data.inputs.flags.c_contiguous
    assert not data.inputs.flags.writeable
    assert data.period_order == (2020,)


def test_polluting_inputs_are_an_explicit_subset_of_inputs() -> None:
    frame = pd.DataFrame(
        {"energy": [1.0], "labor": [2.0], "output": [3.0], "co2": [4.0]}
    )

    data = DEAData.from_frame(
        frame,
        inputs=["energy", "labor"],
        polluting_inputs="energy",
        outputs="output",
        bad_outputs="co2",
    )

    assert data.polluting_input_names == ("energy",)
    assert data.polluting_input_indices == (0,)


def test_duplicate_panel_keys_are_rejected() -> None:
    frame = pd.DataFrame(
        {
            "unit": ["A", "A"],
            "year": [2020, 2020],
            "x": [1.0, 2.0],
            "y": [1.0, 2.0],
        }
    )

    with pytest.raises(DataValidationError, match="keys must be unique"):
        DEAData.from_frame(
            frame,
            dmu="unit",
            period="year",
            inputs="x",
            outputs="y",
        )


def test_variable_roles_cannot_overlap() -> None:
    frame = pd.DataFrame({"x": [1.0], "y": [1.0]})

    with pytest.raises(DataValidationError, match="more than one variable role"):
        DEAData.from_frame(frame, inputs=["x", "y"], outputs=["y"])
