"""Independent dense oracle for Bjurek's bilateral TFP quantity account.

The formula boundary follows Bjurek (1996), as recorded in the repository's
primary-checked review and set out equation by equation in Zelenyuk (2023),
equations (12)--(22).  This module compiles the eight VRS Shephard-distance
programmes directly with NumPy and SciPy.  It imports no production package
and uses only hand-derived exact expectations.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pytest
from scipy.optimize import linprog


@dataclass(frozen=True)
class _HicksMoorsteenAccount:
    distances: dict[str, float]
    output_quantity_t: float
    output_quantity_t1: float
    input_quantity_t: float
    input_quantity_t1: float
    output_quantity: float
    input_quantity: float
    productivity_change: float


_TASKS = (
    ("output_t_xt_yt", "output", 0, 0, 0),
    ("output_t_xt_yt1", "output", 0, 0, 1),
    ("output_t1_xt1_yt", "output", 1, 1, 0),
    ("output_t1_xt1_yt1", "output", 1, 1, 1),
    ("input_t_xt_yt", "input", 0, 0, 0),
    ("input_t_xt1_yt", "input", 0, 1, 0),
    ("input_t1_xt_yt1", "input", 1, 0, 1),
    ("input_t1_xt1_yt1", "input", 1, 1, 1),
)


def _validate_panel(
    x_t: np.ndarray,
    y_t: np.ndarray,
    x_t1: np.ndarray,
    y_t1: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    arrays = tuple(np.asarray(value, dtype=float) for value in (x_t, y_t, x_t1, y_t1))
    xb, yb, xc, yc = arrays
    if any(value.ndim != 2 for value in arrays):
        raise ValueError("source oracle requires two-dimensional panel arrays")
    if xb.shape[0] == 0 or xb.shape[0] != yb.shape[0]:
        raise ValueError("each period requires a nonempty matched reference sample")
    if xc.shape[0] != yc.shape[0] or xb.shape[0] != xc.shape[0]:
        raise ValueError("source oracle requires a matched bilateral panel")
    if xb.shape[1] == 0 or xb.shape[1] != xc.shape[1]:
        raise ValueError("input variables must match across periods")
    if yb.shape[1] == 0 or yb.shape[1] != yc.shape[1]:
        raise ValueError("output variables must match across periods")
    if any(not np.isfinite(value).all() for value in arrays):
        raise ValueError("certified source distances require finite observations")
    if any(np.any(value <= 0.0) for value in arrays):
        raise ValueError("certified source ratios require strictly positive data")
    return xb, yb, xc, yc


def _dense_shephard_distance(
    reference_x: np.ndarray,
    reference_y: np.ndarray,
    target_x: np.ndarray,
    target_y: np.ndarray,
    *,
    orientation: str,
) -> float:
    """Solve one VRS distance programme using dense source-form matrices."""

    n_reference = reference_x.shape[0]
    n_variables = n_reference + 1
    objective = np.zeros(n_variables, dtype=float)
    inequality_rows: list[np.ndarray] = []
    inequality_bounds: list[float] = []

    if orientation == "output":
        objective[-1] = -1.0
        for column in range(reference_x.shape[1]):
            row = np.zeros(n_variables, dtype=float)
            row[:n_reference] = reference_x[:, column]
            inequality_rows.append(row)
            inequality_bounds.append(float(target_x[column]))
        for column in range(reference_y.shape[1]):
            row = np.zeros(n_variables, dtype=float)
            row[:n_reference] = -reference_y[:, column]
            row[-1] = target_y[column]
            inequality_rows.append(row)
            inequality_bounds.append(0.0)
    elif orientation == "input":
        objective[-1] = 1.0
        for column in range(reference_x.shape[1]):
            row = np.zeros(n_variables, dtype=float)
            row[:n_reference] = reference_x[:, column]
            row[-1] = -target_x[column]
            inequality_rows.append(row)
            inequality_bounds.append(0.0)
        for column in range(reference_y.shape[1]):
            row = np.zeros(n_variables, dtype=float)
            row[:n_reference] = -reference_y[:, column]
            inequality_rows.append(row)
            inequality_bounds.append(-float(target_y[column]))
    else:
        raise ValueError("orientation must be 'input' or 'output'")

    convexity = np.zeros((1, n_variables), dtype=float)
    convexity[0, :n_reference] = 1.0
    solution = linprog(
        objective,
        A_ub=np.asarray(inequality_rows, dtype=float),
        b_ub=np.asarray(inequality_bounds, dtype=float),
        A_eq=convexity,
        b_eq=np.ones(1, dtype=float),
        bounds=[(0.0, None)] * n_variables,
        method="highs",
    )
    if not solution.success:
        raise RuntimeError(f"independent source LP failed: {solution.message}")
    radial_factor = float(solution.x[-1])
    if not np.isfinite(radial_factor) or radial_factor <= 0.0:
        raise RuntimeError("source distance has no positive finite radial factor")
    return 1.0 / radial_factor


def _hicks_moorsteen_account(
    x_t: np.ndarray,
    y_t: np.ndarray,
    x_t1: np.ndarray,
    y_t1: np.ndarray,
    *,
    evaluated_row: int = 0,
) -> _HicksMoorsteenAccount:
    xb, yb, xc, yc = _validate_panel(x_t, y_t, x_t1, y_t1)
    references = ((xb, yb), (xc, yc))
    observations = ((xb, yb), (xc, yc))
    if evaluated_row < 0 or evaluated_row >= xb.shape[0]:
        raise ValueError("evaluated_row is outside the matched reference sample")

    distances: dict[str, float] = {}
    for role, orientation, technology, input_period, output_period in _TASKS:
        reference_x, reference_y = references[technology]
        target_x = observations[input_period][0][evaluated_row]
        target_y = observations[output_period][1][evaluated_row]
        distances[role] = _dense_shephard_distance(
            reference_x,
            reference_y,
            target_x,
            target_y,
            orientation=orientation,
        )

    qy_t = distances["output_t_xt_yt1"] / distances["output_t_xt_yt"]
    qy_t1 = distances["output_t1_xt1_yt1"] / distances["output_t1_xt1_yt"]
    qx_t = distances["input_t_xt1_yt"] / distances["input_t_xt_yt"]
    qx_t1 = distances["input_t1_xt1_yt1"] / distances["input_t1_xt_yt1"]
    output_quantity = float(np.sqrt(qy_t * qy_t1))
    input_quantity = float(np.sqrt(qx_t * qx_t1))
    return _HicksMoorsteenAccount(
        distances=distances,
        output_quantity_t=float(qy_t),
        output_quantity_t1=float(qy_t1),
        input_quantity_t=float(qx_t),
        input_quantity_t1=float(qx_t1),
        output_quantity=output_quantity,
        input_quantity=input_quantity,
        productivity_change=output_quantity / input_quantity,
    )


# Unit D is the first row.  The second row is a strictly dominated reference
# activity.  The exact proof in the oracle note shows why it receives zero
# weight in all eight programmes; no expected value below came from production.
_X_T = np.array([[5.0, 4.0], [20.0, 20.0]])
_Y_T = np.array([[4.0, 6.0], [1.0, 1.0]])
_X_T1 = np.array([[6.0, 6.0], [24.0, 24.0]])
_Y_T1 = np.array([[6.0, 15.0], [1.0, 1.0]])


def test_eight_dense_distances_match_the_exact_two_technology_oracle() -> None:
    account = _hicks_moorsteen_account(_X_T, _Y_T, _X_T1, _Y_T1)
    expected = {
        "output_t_xt_yt": 1.0,
        "output_t_xt_yt1": 5 / 2,
        "output_t1_xt1_yt": 2 / 3,
        "output_t1_xt1_yt1": 1.0,
        "input_t_xt_yt": 1.0,
        "input_t_xt1_yt": 6 / 5,
        "input_t1_xt_yt1": 2 / 3,
        "input_t1_xt1_yt1": 1.0,
    }

    assert tuple(account.distances) == tuple(role for role, *_ in _TASKS)
    np.testing.assert_allclose(
        list(account.distances.values()),
        list(expected.values()),
        atol=1e-12,
        rtol=0.0,
    )


def test_exact_quantity_indexes_and_hm_identity() -> None:
    account = _hicks_moorsteen_account(_X_T, _Y_T, _X_T1, _Y_T1)

    assert account.output_quantity_t == pytest.approx(5 / 2, abs=1e-12)
    assert account.output_quantity_t1 == pytest.approx(3 / 2, abs=1e-12)
    assert account.input_quantity_t == pytest.approx(6 / 5, abs=1e-12)
    assert account.input_quantity_t1 == pytest.approx(3 / 2, abs=1e-12)
    assert account.output_quantity == pytest.approx(np.sqrt(15) / 2, abs=1e-12)
    assert account.input_quantity == pytest.approx(3 / np.sqrt(5), abs=1e-12)
    assert account.productivity_change == pytest.approx(
        5 * np.sqrt(3) / 6,
        abs=1e-12,
    )
    assert account.productivity_change == pytest.approx(
        account.output_quantity / account.input_quantity,
        abs=1e-12,
    )


def test_reversing_the_same_bilateral_account_gives_exact_reciprocals() -> None:
    forward = _hicks_moorsteen_account(_X_T, _Y_T, _X_T1, _Y_T1)
    reverse = _hicks_moorsteen_account(_X_T1, _Y_T1, _X_T, _Y_T)

    assert reverse.output_quantity == pytest.approx(
        1.0 / forward.output_quantity,
        abs=1e-12,
    )
    assert reverse.input_quantity == pytest.approx(
        1.0 / forward.input_quantity,
        abs=1e-12,
    )
    assert reverse.productivity_change == pytest.approx(
        1.0 / forward.productivity_change,
        abs=1e-12,
    )


def test_oracle_is_production_free_and_claim_scoped() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    production_imports = [
        node
        for node in ast.walk(tree)
        if (
            isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.startswith("deapack")
        )
        or (
            isinstance(node, ast.Import)
            and any(name.name.startswith("deapack") for name in node.names)
        )
    ]
    assert production_imports == []

    protocol = (
        repository_root / "specs/source_protocols/bjurek_1996_hicks_moorsteen.md"
    ).read_text(encoding="utf-8")
    oracle = (
        repository_root / "specs/oracles/bjurek-1996-hicks-moorsteen-analytical.md"
    ).read_text(encoding="utf-8")
    assert "Source-gate disposition | passed" in protocol
    assert "10.2307/3440861" in protocol
    assert "10.1007/s11123-023-00692-1" in protocol
    assert "**Production implementation reused:** no" in oracle
    assert "\\frac{5\\sqrt3}{6}" in oracle
    assert "No published empirical result is reproduced" in oracle
