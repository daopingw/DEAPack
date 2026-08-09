"""Independent dense oracle for Ray--Desli's 1997 VRS decomposition.

The compiler below is written directly from the output-distance task graph in
Ray and Desli (1997), equations (4)--(16).  It deliberately imports no
``deapack`` code and is not a production implementation.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest
from scipy.optimize import linprog

_ROLES = {
    "base_on_base": (0, 0),
    "comparison_on_base": (0, 1),
    "base_on_comparison": (1, 0),
    "comparison_on_comparison": (1, 1),
}


@dataclass(frozen=True)
class _DistanceTasks:
    crs: np.ndarray
    vrs: np.ndarray


@dataclass(frozen=True)
class _RayDesliAccount:
    productivity_change: float
    pure_efficiency_change: float
    technical_change_vrs: float | None
    scale_efficiency_change_vrs: float | None
    reconstruction_residual: float | None


def _validate_pair(
    x_base: np.ndarray,
    y_base: np.ndarray,
    x_comparison: np.ndarray,
    y_comparison: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    arrays = tuple(
        np.asarray(value, dtype=float)
        for value in (x_base, y_base, x_comparison, y_comparison)
    )
    xb, yb, xc, yc = arrays
    if any(value.ndim != 2 for value in arrays):
        raise ValueError("source oracle requires two-dimensional panel arrays")
    if xb.shape[0] != xc.shape[0] or yb.shape[0] != yc.shape[0]:
        raise ValueError("source oracle requires a matched adjacent panel")
    if xb.shape[0] != yb.shape[0] or xc.shape[0] != yc.shape[0]:
        raise ValueError("input and output rows must identify the same DMUs")
    if xb.shape[1] != xc.shape[1]:
        raise ValueError("input variables must match across periods")
    if yb.shape[1] != 1 or yc.shape[1] != 1:
        raise ValueError("frozen Ray--Desli source domain has one desirable output")
    if any(not np.isfinite(value).all() for value in arrays):
        raise ValueError("source distances require finite observations")
    if any(np.any(value <= 0.0) for value in arrays):
        raise ValueError("source ratios and distance inversions require positive data")
    return xb, yb, xc, yc


def _output_distance(
    reference_x: np.ndarray,
    reference_y: np.ndarray,
    target_x: np.ndarray,
    target_y: np.ndarray,
    *,
    vrs: bool,
) -> float | None:
    """Return D_o=1/max(phi), or None for source-noted VRS infeasibility."""

    n, m = reference_x.shape
    # Dense variable order: lambda[0:n], output expansion phi.
    objective = np.concatenate([np.zeros(n), -np.ones(1)])
    inequalities: list[np.ndarray] = []
    bounds: list[float] = []
    for i in range(m):
        inequalities.append(np.concatenate([reference_x[:, i], np.zeros(1)]))
        bounds.append(float(target_x[i]))
    inequalities.append(np.concatenate([-reference_y[:, 0], np.asarray([target_y[0]])]))
    bounds.append(0.0)

    convexity = np.concatenate([np.ones(n), np.zeros(1)])[None, :] if vrs else None
    result = linprog(
        objective,
        A_ub=np.asarray(inequalities),
        b_ub=np.asarray(bounds),
        A_eq=convexity,
        b_eq=np.ones(1) if vrs else None,
        bounds=[(0.0, None)] * (n + 1),
        method="highs",
    )
    if result.status == 2:
        return None
    if not result.success:
        raise RuntimeError(f"source distance LP failed: {result.message}")
    expansion = float(result.x[-1])
    if not np.isfinite(expansion) or expansion <= 0.0:
        raise RuntimeError("source distance has no positive finite expansion factor")
    return 1.0 / expansion


def _compile_eight_tasks(
    x_base: np.ndarray,
    y_base: np.ndarray,
    x_comparison: np.ndarray,
    y_comparison: np.ndarray,
) -> _DistanceTasks:
    xb, yb, xc, yc = _validate_pair(x_base, y_base, x_comparison, y_comparison)
    references = ((xb, yb), (xc, yc))
    targets = ((xb, yb), (xc, yc))
    n = xb.shape[0]
    crs = np.full((n, 2, 2), np.nan)
    vrs = np.full((n, 2, 2), np.nan)
    for dmu in range(n):
        for reference_period, (reference_x, reference_y) in enumerate(references):
            for target_period, (target_x, target_y) in enumerate(targets):
                for use_vrs, destination in ((False, crs), (True, vrs)):
                    value = _output_distance(
                        reference_x,
                        reference_y,
                        target_x[dmu],
                        target_y[dmu],
                        vrs=use_vrs,
                    )
                    if value is not None:
                        destination[dmu, reference_period, target_period] = value
    return _DistanceTasks(crs=crs, vrs=vrs)


def _ray_desli_accounts(tasks: _DistanceTasks) -> list[_RayDesliAccount]:
    accounts: list[_RayDesliAccount] = []
    for crs, vrs in zip(tasks.crs, tasks.vrs, strict=True):
        if not np.isfinite(crs).all() or np.any(crs <= 0.0):
            raise ValueError("all four CRS distances must be positive and finite")
        if not np.isfinite([vrs[0, 0], vrs[1, 1]]).all():
            raise ValueError("own-period VRS distances must be feasible")

        productivity = float(np.sqrt((crs[0, 1] / crs[0, 0]) * (crs[1, 1] / crs[1, 0])))
        pure_efficiency = float(vrs[1, 1] / vrs[0, 0])
        if not np.isfinite(vrs).all():
            accounts.append(
                _RayDesliAccount(
                    productivity_change=productivity,
                    pure_efficiency_change=pure_efficiency,
                    technical_change_vrs=None,
                    scale_efficiency_change_vrs=None,
                    reconstruction_residual=None,
                )
            )
            continue

        technical_change = float(
            np.sqrt((vrs[0, 0] / vrs[1, 0]) * (vrs[0, 1] / vrs[1, 1]))
        )
        scale_efficiency = crs / vrs
        scale_change = float(
            np.sqrt(
                (scale_efficiency[0, 1] / scale_efficiency[0, 0])
                * (scale_efficiency[1, 1] / scale_efficiency[1, 0])
            )
        )
        reconstructed = pure_efficiency * technical_change * scale_change
        accounts.append(
            _RayDesliAccount(
                productivity_change=productivity,
                pure_efficiency_change=pure_efficiency,
                technical_change_vrs=technical_change,
                scale_efficiency_change_vrs=scale_change,
                reconstruction_residual=float(productivity - reconstructed),
            )
        )
    return accounts


def _fgnz_contrast(
    crs: np.ndarray,
    vrs: np.ndarray,
) -> tuple[float, float]:
    """Return only the two source-contrasted FGNZ factors, not a package API."""

    technical_change = float(np.sqrt((crs[0, 0] / crs[1, 0]) * (crs[0, 1] / crs[1, 1])))
    scale_efficiency = crs / vrs
    scale_change = float(scale_efficiency[1, 1] / scale_efficiency[0, 0])
    return technical_change, scale_change


_X_BASE = np.array([[1.0], [2.0], [3.0], [4.0]])
_Y_BASE = np.array([[1.0], [3.0], [4.0], [4.5]])
_X_COMPARISON = np.array([[1.0], [1.5], [2.5], [4.0]])
_Y_COMPARISON = np.array([[1.2], [2.4], [4.2], [5.0]])


def test_eight_dense_distance_tasks_match_exact_fixture_oracle() -> None:
    assert _ROLES == {
        "base_on_base": (0, 0),
        "comparison_on_base": (0, 1),
        "base_on_comparison": (1, 0),
        "comparison_on_comparison": (1, 1),
    }
    tasks = _compile_eight_tasks(
        _X_BASE,
        _Y_BASE,
        _X_COMPARISON,
        _Y_COMPARISON,
    )
    expected_crs = np.array(
        [
            [[2 / 3, 4 / 5], [25 / 42, 5 / 7]],
            [[1, 16 / 15], [25 / 28, 20 / 21]],
            [[8 / 9, 28 / 25], [50 / 63, 1]],
            [[3 / 4, 5 / 6], [75 / 112, 125 / 168]],
        ]
    )
    expected_vrs = np.array(
        [
            [[1, 6 / 5], [5 / 6, 1]],
            [[1, 6 / 5], [10 / 11, 1]],
            [[1, 6 / 5], [60 / 67, 1]],
            [[1, 10 / 9], [9 / 10, 1]],
        ]
    )
    np.testing.assert_allclose(tasks.crs, expected_crs, atol=1e-12)
    np.testing.assert_allclose(tasks.vrs, expected_vrs, atol=1e-12)


def test_ray_desli_identity_reconstructs_and_differs_from_fgnz() -> None:
    tasks = _compile_eight_tasks(
        _X_BASE,
        _Y_BASE,
        _X_COMPARISON,
        _Y_COMPARISON,
    )
    accounts = _ray_desli_accounts(tasks)

    expected_productivity = np.array([6 / 5, 16 / 15, 63 / 50, 10 / 9])
    expected_technical = np.array([6 / 5, np.sqrt(33) / 5, np.sqrt(67 / 50), 10 / 9])
    expected_scale = expected_productivity / expected_technical
    np.testing.assert_allclose(
        [account.productivity_change for account in accounts],
        expected_productivity,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        [account.pure_efficiency_change for account in accounts],
        np.ones(4),
        atol=1e-12,
    )
    np.testing.assert_allclose(
        [account.technical_change_vrs for account in accounts],
        expected_technical,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        [account.scale_efficiency_change_vrs for account in accounts],
        expected_scale,
        atol=1e-12,
    )
    assert (
        max(abs(account.reconstruction_residual or 0.0) for account in accounts) < 1e-12
    )

    fgnz = [
        _fgnz_contrast(crs, vrs) for crs, vrs in zip(tasks.crs, tasks.vrs, strict=True)
    ]
    np.testing.assert_allclose([item[0] for item in fgnz], np.full(4, 28 / 25))
    np.testing.assert_allclose(
        [item[1] for item in fgnz],
        [15 / 14, 20 / 21, 9 / 8, 125 / 126],
        atol=1e-12,
    )
    assert accounts[1].technical_change_vrs != pytest.approx(fgnz[1][0])
    assert accounts[1].scale_efficiency_change_vrs != pytest.approx(fgnz[1][1])
    assert accounts[1].technical_change_vrs > 1.0
    assert accounts[1].scale_efficiency_change_vrs < 1.0


def test_vrs_cross_infeasibility_preserves_only_source_defined_partial_account() -> (
    None
):
    tasks = _compile_eight_tasks(
        np.array([[1.0], [2.0]]),
        np.array([[1.0], [2.0]]),
        np.array([[0.5], [1.5]]),
        np.array([[1.1], [2.5]]),
    )
    assert np.isfinite(tasks.crs).all()
    assert np.isnan(tasks.vrs[0, _ROLES["comparison_on_base"][0], 1])

    account = _ray_desli_accounts(tasks)[0]
    assert account.productivity_change == pytest.approx(2.2, abs=1e-12)
    assert account.pure_efficiency_change == pytest.approx(1.0, abs=1e-12)
    assert account.technical_change_vrs is None
    assert account.scale_efficiency_change_vrs is None
    assert account.reconstruction_residual is None


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (lambda value: value * 0.0, "positive data"),
        (lambda value: value[:-1], "matched adjacent panel"),
    ],
)
def test_source_oracle_fails_closed_on_invalid_domain(mutator, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _compile_eight_tasks(
            _X_BASE,
            _Y_BASE,
            mutator(_X_COMPARISON),
            _Y_COMPARISON,
        )
