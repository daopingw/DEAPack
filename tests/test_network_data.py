from __future__ import annotations

from dataclasses import FrozenInstanceError

import numpy as np
import pandas as pd
import pytest

from deapack import (
    LinkSpec,
    NetworkData,
    NetworkSpec,
    ProcessSpec,
    TwoStageSeriesSpec,
)
from deapack.exceptions import DataValidationError, ModelSpecificationError


def test_two_stage_series_stores_each_intermediate_once() -> None:
    frame = pd.DataFrame(
        {
            "company": ["A", "B"],
            "resources": [2.0, 3.0],
            "cases": [4.0, 5.0],
            "outcomes": [6.0, 8.0],
        }
    )
    specification = TwoStageSeriesSpec(
        inputs="resources",
        intermediates="cases",
        outputs="outcomes",
        stage_names=("intake", "resolution"),
    )
    data = NetworkData.from_frame(frame, dmu="company", spec=specification)

    assert data.variable_names == ("resources", "cases", "outcomes")
    assert data.values.shape == (2, 3)
    assert data.network_spec.processes[0].outputs == ("cases",)
    assert data.network_spec.processes[1].inputs == ("cases",)
    assert data.network_spec.links[0].variables == ("cases",)
    assert len(data.graph_fingerprint) == 64
    assert data.graph_fingerprint == specification.as_network_spec().fingerprint
    assert not data.values.flags.writeable
    with pytest.raises(ValueError):
        data.values[0, 0] = 99
    with pytest.raises(FrozenInstanceError):
        data.variable_names = ("changed",)  # type: ignore[misc]


def test_network_data_validates_keys_period_order_and_columns() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "A"],
            "period": [2021, 2021],
            "x": [1.0, 2.0],
            "z": [1.0, 2.0],
            "y": [1.0, 2.0],
        }
    )
    specification = TwoStageSeriesSpec(inputs="x", intermediates="z", outputs="y")

    with pytest.raises(DataValidationError, match="keys must be unique"):
        NetworkData.from_frame(
            frame,
            dmu="dmu",
            period="period",
            spec=specification,
        )
    with pytest.raises(DataValidationError, match="missing network variable"):
        NetworkData.from_frame(
            frame.drop(columns="z").drop_duplicates("dmu"),
            dmu="dmu",
            spec=specification,
        )


def test_graph_rejects_unaccounted_or_misconnected_link_variables() -> None:
    with pytest.raises(ModelSpecificationError, match="outputs of its source"):
        NetworkSpec(
            processes=(
                ProcessSpec("upstream", inputs=("x",), outputs=("z",)),
                ProcessSpec("downstream", inputs=("other_z",), outputs=("y",)),
            ),
            links=(
                LinkSpec(
                    "handoff",
                    source="upstream",
                    target="downstream",
                    variables=("z",),
                ),
            ),
        )


def test_two_stage_roles_must_use_distinct_observed_columns() -> None:
    with pytest.raises(ModelSpecificationError, match="distinct data columns"):
        TwoStageSeriesSpec(
            inputs=("shared",),
            intermediates=("shared",),
            outputs=("outcome",),
        )


def test_matrix_returns_requested_semantic_order_as_read_only() -> None:
    frame = pd.DataFrame({"x": [1.0], "z": [2.0], "y1": [3.0], "y2": [4.0]})
    data = NetworkData.from_frame(
        frame,
        spec=TwoStageSeriesSpec(
            inputs="x",
            intermediates="z",
            outputs=("y1", "y2"),
        ),
    )

    matrix = data.matrix(("y2", "x"))
    np.testing.assert_allclose(matrix, [[4.0, 1.0]])
    assert not matrix.flags.writeable
    with pytest.raises(KeyError, match="unknown network variables"):
        data.matrix(("missing",))
