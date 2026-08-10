"""Independent dense source-equation checks for project-authored fixtures.

The compilers in this module deliberately use ``scipy.optimize.linprog``
directly.  They do not import or call DEAPack's LP builders, sparse compiler,
or post-solve reconstruction helpers.  The fixtures are project-authored and
therefore support cross-implementation claims, not published-table
reproduction claims.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import linprog

from deapack import (
    ChenCookLiZhuAdditiveDEA,
    CookZhuBiYangAdditiveDEA,
    DEAData,
    KaoHwangRelationalDEA,
    LinkSpec,
    NetworkData,
    NetworkSpec,
    ParkParkMultiperiodAggregativeDEA,
    ProcessSpec,
    TwoStageSeriesSpec,
    dataset_info,
    load_dataset,
)


def _solve_dense(
    objective: np.ndarray,
    *,
    maximize: bool,
    a_ub: np.ndarray,
    b_ub: np.ndarray,
    a_eq: np.ndarray | None = None,
    b_eq: np.ndarray | None = None,
) -> tuple[float, np.ndarray]:
    result = linprog(
        -objective if maximize else objective,
        A_ub=a_ub,
        b_ub=b_ub,
        A_eq=a_eq,
        b_eq=b_eq,
        bounds=(0.0, None),
        method="highs",
    )
    assert result.success, result.message
    value = -float(result.fun) if maximize else float(result.fun)
    return value, np.asarray(result.x, dtype=np.float64)


def _two_stage_project() -> tuple[pd.DataFrame, NetworkData]:
    frame = load_dataset("two_stage_public_service").rename(
        columns={
            "unit": "dmu",
            "staff_hours": "x_1",
            "platform_cost_units": "x_2",
            "screened_cases": "z_1",
            "verified_value": "z_2",
            "timely_closures": "y_1",
            "public_value": "y_2",
        }
    )
    return frame, NetworkData.from_frame(
        frame,
        dmu="dmu",
        spec=TwoStageSeriesSpec(
            inputs=("x_1", "x_2"),
            intermediates=("z_1", "z_2"),
            outputs=("y_1", "y_2"),
        ),
    )


def _dense_two_stage_multiplier_scores(
    x: np.ndarray,
    z: np.ndarray,
    y: np.ndarray,
    *,
    additive: bool,
) -> np.ndarray:
    n, m = x.shape
    q = z.shape[1]
    s = y.shape[1]
    stage_1 = np.hstack([-x, z, np.zeros((n, s))])
    stage_2 = np.hstack([np.zeros((n, m)), -z, y])
    a_ub = np.vstack([stage_1, stage_2])
    b_ub = np.zeros(2 * n, dtype=np.float64)
    scores = []
    for position in range(n):
        normalization = np.zeros(m + q + s, dtype=np.float64)
        normalization[:m] = x[position]
        objective = np.zeros(m + q + s, dtype=np.float64)
        objective[m + q :] = y[position]
        if additive:
            normalization[m : m + q] = z[position]
            objective[m : m + q] = z[position]
        score, _ = _solve_dense(
            objective,
            maximize=True,
            a_ub=a_ub,
            b_ub=b_ub,
            a_eq=normalization.reshape(1, -1),
            b_eq=np.ones(1, dtype=np.float64),
        )
        scores.append(score)
    return np.asarray(scores, dtype=np.float64)


def _dense_chen_projection(
    x: np.ndarray,
    z: np.ndarray,
    y: np.ndarray,
    position: int,
) -> tuple[float, np.ndarray, np.ndarray]:
    """Compile the CRS Lim--Zhu primal without DEAPack LP helpers."""

    n = x.shape[0]
    eta_column = 2 * n
    rows: list[np.ndarray] = []
    bounds: list[float] = []
    for column in range(x.shape[1]):
        row = np.zeros(2 * n + 1, dtype=np.float64)
        row[:n] = x[:, column]
        row[eta_column] = -x[position, column]
        rows.append(row)
        bounds.append(0.0)
    for column in range(z.shape[1]):
        row = np.zeros(2 * n + 1, dtype=np.float64)
        row[:n] = -z[:, column]
        row[n : 2 * n] = z[:, column]
        row[eta_column] = -z[position, column]
        rows.append(row)
        bounds.append(-z[position, column])
    for column in range(y.shape[1]):
        row = np.zeros(2 * n + 1, dtype=np.float64)
        row[n : 2 * n] = -y[:, column]
        rows.append(row)
        bounds.append(-y[position, column])

    objective = np.zeros(2 * n + 1, dtype=np.float64)
    objective[eta_column] = 1.0
    eta, primal = _solve_dense(
        objective,
        maximize=False,
        a_ub=np.vstack(rows),
        b_ub=np.asarray(bounds, dtype=np.float64),
    )
    return eta, primal[:n], primal[n : 2 * n]


def test_chen_score_and_projection_match_independent_dense_compilers() -> None:
    frame, data = _two_stage_project()
    x = frame[["x_1", "x_2"]].to_numpy(dtype=np.float64)
    z = frame[["z_1", "z_2"]].to_numpy(dtype=np.float64)
    y = frame[["y_1", "y_2"]].to_numpy(dtype=np.float64)
    expected = _dense_two_stage_multiplier_scores(x, z, y, additive=True)

    result = ChenCookLiZhuAdditiveDEA(
        returns_to_scale="crs",
        decomposition="none",
    ).fit(data)
    summary = result.summary().set_index("dmu_id")
    np.testing.assert_allclose(
        summary.loc[frame["dmu"], "system_efficiency"],
        expected,
        atol=2e-9,
        rtol=0,
    )

    for position, dmu_id in enumerate(frame["dmu"]):
        eta, lambdas, mus = _dense_chen_projection(x, z, y, position)
        assert eta == pytest.approx(expected[position], abs=2e-9)

        targets = result.targets_for(dmu_id)
        inputs = (
            targets.loc[targets["role"].eq("external_input")]
            .set_index("variable")
            .loc[["x_1", "x_2"], "target"]
            .to_numpy(dtype=np.float64)
        )
        outputs = (
            targets.loc[targets["role"].eq("final_output")]
            .set_index("variable")
            .loc[["y_1", "y_2"], "target"]
            .to_numpy(dtype=np.float64)
        )
        links = result.links_for(dmu_id).set_index("variable")
        upstream = links.loc[["z_1", "z_2"], "source_target"].to_numpy(dtype=np.float64)
        downstream = links.loc[["z_1", "z_2"], "target_target"].to_numpy(
            dtype=np.float64
        )

        # The independently optimized plan and the published plan may choose
        # different alternate intensities.  Both must attain the same optimum
        # and satisfy the source quantity account.
        assert np.all(x.T @ lambdas <= eta * x[position] + 2e-9)
        assert np.all(y.T @ mus >= y[position] - 2e-9)
        assert np.all(z.T @ lambdas - z.T @ mus >= (1.0 - eta) * z[position] - 2e-9)
        assert np.all(inputs <= eta * x[position] + 2e-9)
        assert np.all(outputs >= y[position] - 2e-9)
        assert np.all(upstream - downstream >= (1.0 - eta) * z[position] - 2e-9)


def test_kao_hwang_system_scores_match_independent_dense_compiler() -> None:
    frame, data = _two_stage_project()
    x = frame[["x_1", "x_2"]].to_numpy(dtype=np.float64)
    z = frame[["z_1", "z_2"]].to_numpy(dtype=np.float64)
    y = frame[["y_1", "y_2"]].to_numpy(dtype=np.float64)
    expected = _dense_two_stage_multiplier_scores(x, z, y, additive=False)

    result = KaoHwangRelationalDEA(
        decomposition="none",
        projection="none",
    ).fit(data)
    summary = result.summary().set_index("dmu_id")
    np.testing.assert_allclose(
        summary.loc[frame["dmu"], "system_efficiency"],
        expected,
        atol=2e-9,
        rtol=0,
    )


def _open_chain_project() -> tuple[pd.DataFrame, NetworkData]:
    frame = load_dataset("open_service_chain").rename(
        columns={
            "unit": "dmu",
            "sourcing_hours": "seller_labor",
            "platform_units": "operating_cost",
            "transport_units": "shipping_cost",
            "standard_orders": "product_a",
            "priority_orders": "product_b",
            "bulk_orders": "product_c",
            "service_hours": "buyer_labor",
            "delivered_value": "sales",
            "retained_margin": "profit",
        }
    )
    seller = ProcessSpec(
        "seller",
        inputs=("seller_labor", "operating_cost", "shipping_cost"),
        outputs=("product_a", "product_b", "product_c"),
    )
    buyer = ProcessSpec(
        "buyer",
        inputs=("product_a", "product_b", "product_c", "buyer_labor"),
        outputs=("sales", "profit"),
    )
    return frame, NetworkData.from_frame(
        frame,
        dmu="dmu",
        spec=NetworkSpec(
            processes=(seller, buyer),
            links=(
                LinkSpec(
                    "products",
                    source="seller",
                    target="buyer",
                    variables=("product_a", "product_b", "product_c"),
                ),
            ),
        ),
    )


def _dense_general_additive_scores(
    values: np.ndarray,
    process_columns: Sequence[tuple[Sequence[int], Sequence[int]]],
) -> np.ndarray:
    n, n_variables = values.shape
    constraints = []
    for input_columns, output_columns in process_columns:
        block = np.zeros((n, n_variables), dtype=np.float64)
        block[:, list(input_columns)] -= values[:, list(input_columns)]
        block[:, list(output_columns)] += values[:, list(output_columns)]
        constraints.append(block)
    a_ub = np.vstack(constraints)
    b_ub = np.zeros(a_ub.shape[0], dtype=np.float64)

    scores = []
    for position in range(n):
        normalization = np.zeros(n_variables, dtype=np.float64)
        objective = np.zeros(n_variables, dtype=np.float64)
        for input_columns, output_columns in process_columns:
            normalization[list(input_columns)] += values[position, list(input_columns)]
            objective[list(output_columns)] += values[position, list(output_columns)]
        score, _ = _solve_dense(
            objective,
            maximize=True,
            a_ub=a_ub,
            b_ub=b_ub,
            a_eq=normalization.reshape(1, -1),
            b_eq=np.ones(1, dtype=np.float64),
        )
        scores.append(score)
    return np.asarray(scores, dtype=np.float64)


def test_cook_general_additive_scores_match_independent_dense_compiler() -> None:
    frame, data = _open_chain_project()
    columns = [
        "seller_labor",
        "operating_cost",
        "shipping_cost",
        "product_a",
        "product_b",
        "product_c",
        "buyer_labor",
        "sales",
        "profit",
    ]
    values = frame[columns].to_numpy(dtype=np.float64)
    expected = _dense_general_additive_scores(
        values,
        process_columns=(
            ((0, 1, 2), (3, 4, 5)),
            ((3, 4, 5, 6), (7, 8)),
        ),
    )
    result = CookZhuBiYangAdditiveDEA().fit(data)
    summary = result.summary().set_index("dmu_id")
    np.testing.assert_allclose(
        summary.loc[frame["dmu"], "system_efficiency"],
        expected,
        atol=2e-9,
        rtol=0,
    )


def _multiperiod_project() -> tuple[pd.DataFrame, DEAData]:
    dataset_id = "multiperiod_trajectory_contrast"
    roles = dataset_info(dataset_id).roles
    frame = load_dataset(dataset_id).rename(
        columns={
            roles["dmu"]: "dmu",
            roles["period"]: "period",
            roles["inputs"][0]: "x",
            roles["outputs"][0]: "y",
        }
    )
    return frame, DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs="x",
        outputs="y",
    )


def _dense_multiperiod_factor(
    frame: pd.DataFrame,
    dmu_id: str,
    *,
    orientation: str,
    returns_to_scale: str,
) -> float:
    dmu_ids = list(dict.fromkeys(frame["dmu"].tolist()))
    periods = list(dict.fromkeys(frame["period"].tolist()))
    n = len(dmu_ids)
    n_lambda = n * len(periods)
    factor_column = n_lambda
    rows: list[np.ndarray] = []
    bounds: list[float] = []
    equality_rows: list[np.ndarray] = []
    for period_index, period in enumerate(periods):
        reference = frame.loc[frame["period"].eq(period)].set_index("dmu").loc[dmu_ids]
        evaluated = reference.loc[dmu_id]
        block = slice(period_index * n, (period_index + 1) * n)

        input_row = np.zeros(n_lambda + 1, dtype=np.float64)
        input_row[block] = reference["x"].to_numpy(dtype=np.float64)
        output_row = np.zeros(n_lambda + 1, dtype=np.float64)
        output_row[block] = -reference["y"].to_numpy(dtype=np.float64)
        if orientation == "input":
            input_row[factor_column] = -float(evaluated["x"])
            rows.extend([input_row, output_row])
            bounds.extend([0.0, -float(evaluated["y"])])
        else:
            output_row[factor_column] = float(evaluated["y"])
            rows.extend([input_row, output_row])
            bounds.extend([float(evaluated["x"]), 0.0])

        if returns_to_scale == "vrs":
            convexity = np.zeros(n_lambda + 1, dtype=np.float64)
            convexity[block] = 1.0
            equality_rows.append(convexity)

    objective = np.zeros(n_lambda + 1, dtype=np.float64)
    objective[factor_column] = 1.0
    factor, _ = _solve_dense(
        objective,
        maximize=orientation == "output",
        a_ub=np.vstack(rows),
        b_ub=np.asarray(bounds, dtype=np.float64),
        a_eq=np.vstack(equality_rows) if equality_rows else None,
        b_eq=np.ones(len(equality_rows), dtype=np.float64) if equality_rows else None,
    )
    return factor


@pytest.mark.parametrize("orientation", ["input", "output"])
@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs"])
def test_park_park_common_factor_matches_independent_dense_compiler(
    orientation: str,
    returns_to_scale: str,
) -> None:
    frame, data = _multiperiod_project()
    result = ParkParkMultiperiodAggregativeDEA(
        orientation=orientation,
        returns_to_scale=returns_to_scale,
    ).fit(data)
    summary = result.summary().set_index("dmu_id")
    expected = np.asarray(
        [
            _dense_multiperiod_factor(
                frame,
                dmu_id,
                orientation=orientation,
                returns_to_scale=returns_to_scale,
            )
            for dmu_id in summary.index
        ],
        dtype=np.float64,
    )
    np.testing.assert_allclose(summary["score"], expected, atol=2e-9, rtol=0)
