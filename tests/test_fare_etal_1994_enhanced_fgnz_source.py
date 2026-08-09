"""Production-free source oracle for Färe et al.'s enhanced decomposition.

The dense compiler is transcribed from Färe et al. (1994), pp. 70--75,
especially equation (7) and footnotes 16--17.  It imports no ``deapack``
module.  Four CRS distance programmes define the Malmquist account and two
additional own-period VRS programmes separate pure efficiency and scale.
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
class _SixDistanceTasks:
    crs: np.ndarray
    vrs_own: np.ndarray


@dataclass(frozen=True)
class _EnhancedFGNZAccount:
    productivity_change: float
    efficiency_change: float
    technical_change_crs: float
    core_residual: float
    pure_efficiency_change: float | None
    scale_efficiency_change: float | None
    productivity_residual: float | None
    efficiency_residual: float | None
    decomposition_defined: bool
    decomposition_status: str


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
    if xb.shape[0] == 0 or yb.shape[0] == 0:
        raise ValueError("source oracle requires at least one matched DMU")
    if xb.shape[0] != xc.shape[0] or yb.shape[0] != yc.shape[0]:
        raise ValueError("source oracle requires a matched adjacent panel")
    if xb.shape[0] != yb.shape[0] or xc.shape[0] != yc.shape[0]:
        raise ValueError("input and output rows must identify the same DMUs")
    if xb.shape[1] == 0 or xb.shape[1] != xc.shape[1]:
        raise ValueError("at least one common input variable is required")
    if yb.shape[1] == 0 or yb.shape[1] != yc.shape[1]:
        raise ValueError("at least one common output variable is required")
    if any(not np.isfinite(value).all() for value in arrays):
        raise ValueError("certified source distances require finite observations")
    if any(np.any(value <= 0.0) for value in arrays):
        raise ValueError("certified source ratios require strictly positive data")
    return xb, yb, xc, yc


def _output_distance(
    reference_x: np.ndarray,
    reference_y: np.ndarray,
    target_x: np.ndarray,
    target_y: np.ndarray,
    *,
    vrs: bool,
) -> float | None:
    """Return ``D_o=1/max(phi)`` from an independently compiled dense LP."""

    n_reference, n_inputs = reference_x.shape
    n_variables = n_reference + 1
    objective = np.zeros(n_variables, dtype=float)
    objective[-1] = -1.0
    inequalities: list[np.ndarray] = []
    bounds: list[float] = []

    for input_index in range(n_inputs):
        row = np.zeros(n_variables, dtype=float)
        row[:n_reference] = reference_x[:, input_index]
        inequalities.append(row)
        bounds.append(float(target_x[input_index]))

    for output_index in range(reference_y.shape[1]):
        row = np.zeros(n_variables, dtype=float)
        row[:n_reference] = -reference_y[:, output_index]
        row[-1] = target_y[output_index]
        inequalities.append(row)
        bounds.append(0.0)

    convexity = None
    convexity_bound = None
    if vrs:
        convexity = np.zeros((1, n_variables), dtype=float)
        convexity[0, :n_reference] = 1.0
        convexity_bound = np.ones(1, dtype=float)

    result = linprog(
        objective,
        A_ub=np.asarray(inequalities, dtype=float),
        b_ub=np.asarray(bounds, dtype=float),
        A_eq=convexity,
        b_eq=convexity_bound,
        bounds=[(0.0, None)] * n_variables,
        method="highs",
    )
    if result.status == 2:
        return None
    if not result.success:
        raise RuntimeError(f"source distance LP failed: {result.message}")
    expansion = float(result.x[-1])
    if not np.isfinite(expansion) or expansion <= 0.0:
        return None
    return 1.0 / expansion


def _compile_six_tasks(
    x_base: np.ndarray,
    y_base: np.ndarray,
    x_comparison: np.ndarray,
    y_comparison: np.ndarray,
) -> _SixDistanceTasks:
    xb, yb, xc, yc = _validate_pair(x_base, y_base, x_comparison, y_comparison)
    references = ((xb, yb), (xc, yc))
    targets = ((xb, yb), (xc, yc))
    n_dmus = xb.shape[0]
    crs = np.full((n_dmus, 2, 2), np.nan)
    vrs_own = np.full((n_dmus, 2), np.nan)

    for dmu in range(n_dmus):
        for reference_period, (reference_x, reference_y) in enumerate(references):
            for target_period, (target_x, target_y) in enumerate(targets):
                value = _output_distance(
                    reference_x,
                    reference_y,
                    target_x[dmu],
                    target_y[dmu],
                    vrs=False,
                )
                if value is not None:
                    crs[dmu, reference_period, target_period] = value

            own_x, own_y = targets[reference_period]
            value = _output_distance(
                reference_x,
                reference_y,
                own_x[dmu],
                own_y[dmu],
                vrs=True,
            )
            if value is not None:
                vrs_own[dmu, reference_period] = value

    return _SixDistanceTasks(crs=crs, vrs_own=vrs_own)


def _enhanced_fgnz_accounts(
    tasks: _SixDistanceTasks,
) -> list[_EnhancedFGNZAccount]:
    accounts: list[_EnhancedFGNZAccount] = []
    for crs, vrs_own in zip(tasks.crs, tasks.vrs_own, strict=True):
        if not np.isfinite(crs).all() or np.any(crs <= 0.0):
            raise ValueError(
                "all four CRS source distances must be positive and finite"
            )

        d_base_base = crs[0, 0]
        d_comparison_base = crs[0, 1]
        d_base_comparison = crs[1, 0]
        d_comparison_comparison = crs[1, 1]

        productivity = float(
            np.sqrt(
                (d_comparison_base / d_base_base)
                * (d_comparison_comparison / d_base_comparison)
            )
        )
        efficiency = float(d_comparison_comparison / d_base_base)
        technical = float(
            np.sqrt(
                (d_comparison_base / d_comparison_comparison)
                * (d_base_base / d_base_comparison)
            )
        )
        core_residual = productivity - efficiency * technical
        if not np.isfinite(vrs_own).all() or np.any(vrs_own <= 0.0):
            accounts.append(
                _EnhancedFGNZAccount(
                    productivity_change=productivity,
                    efficiency_change=efficiency,
                    technical_change_crs=technical,
                    core_residual=core_residual,
                    pure_efficiency_change=None,
                    scale_efficiency_change=None,
                    productivity_residual=None,
                    efficiency_residual=None,
                    decomposition_defined=False,
                    decomposition_status="vrs_own_unavailable",
                )
            )
            continue

        pure_efficiency = float(vrs_own[1] / vrs_own[0])
        scale_efficiency_base = float(d_base_base / vrs_own[0])
        scale_efficiency_comparison = float(d_comparison_comparison / vrs_own[1])
        scale_change = scale_efficiency_comparison / scale_efficiency_base
        reconstructed_efficiency = pure_efficiency * scale_change
        reconstructed_productivity = technical * reconstructed_efficiency
        accounts.append(
            _EnhancedFGNZAccount(
                productivity_change=productivity,
                efficiency_change=efficiency,
                technical_change_crs=technical,
                core_residual=core_residual,
                pure_efficiency_change=pure_efficiency,
                scale_efficiency_change=scale_change,
                productivity_residual=productivity - reconstructed_productivity,
                efficiency_residual=efficiency - reconstructed_efficiency,
                decomposition_defined=True,
                decomposition_status="complete",
            )
        )
    return accounts


_X_BASE = np.array([[1.0], [2.0], [3.0], [4.0]])
_Y_BASE = np.array([[1.0], [3.0], [4.0], [7 / 2]])
_X_COMPARISON = np.array([[1.0], [1.5], [2.5], [4.0]])
_Y_COMPARISON = np.array([[1.2], [2.4], [4.2], [5.0]])


def test_six_source_tasks_match_exact_discriminating_fixture() -> None:
    assert _ROLES == {
        "base_on_base": (0, 0),
        "comparison_on_base": (0, 1),
        "base_on_comparison": (1, 0),
        "comparison_on_comparison": (1, 1),
    }
    tasks = _compile_six_tasks(
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
            [[7 / 12, 5 / 6], [25 / 48, 125 / 168]],
        ]
    )
    np.testing.assert_allclose(tasks.crs, expected_crs, atol=1e-12, rtol=0.0)
    expected_vrs_own = np.array([[1, 1], [1, 1], [1, 1], [7 / 8, 1]])
    np.testing.assert_allclose(tasks.vrs_own, expected_vrs_own, atol=1e-12)
    assert tasks.crs.size + tasks.vrs_own.size == 24
    assert tasks.crs.shape[1:] == (2, 2)
    assert tasks.vrs_own.shape[1] == 2


def test_component_identities_hold_individually_for_every_dmu() -> None:
    tasks = _compile_six_tasks(
        _X_BASE,
        _Y_BASE,
        _X_COMPARISON,
        _Y_COMPARISON,
    )
    accounts = _enhanced_fgnz_accounts(tasks)
    expected_productivity = np.array([6 / 5, 16 / 15, 63 / 50, 10 / 7])
    expected_efficiency = np.array([15 / 14, 20 / 21, 9 / 8, 125 / 98])
    expected_pure_efficiency = np.array([1, 1, 1, 8 / 7])
    expected_scale_change = np.array([15 / 14, 20 / 21, 9 / 8, 125 / 112])

    np.testing.assert_allclose(
        [account.productivity_change for account in accounts],
        expected_productivity,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        [account.efficiency_change for account in accounts],
        expected_efficiency,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        [account.technical_change_crs for account in accounts],
        np.full(4, 28 / 25),
        atol=1e-12,
    )
    np.testing.assert_allclose(
        [account.pure_efficiency_change for account in accounts],
        expected_pure_efficiency,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        [account.scale_efficiency_change for account in accounts],
        expected_scale_change,
        atol=1e-12,
    )
    assert all(account.decomposition_defined for account in accounts)
    assert {account.decomposition_status for account in accounts} == {"complete"}
    assert max(abs(account.core_residual) for account in accounts) < 1e-12
    assert max(abs(account.efficiency_residual) for account in accounts) < 1e-12
    assert max(abs(account.productivity_residual) for account in accounts) < 1e-12


def test_same_exact_fixture_proves_fgnz_and_ray_allocations_are_not_aliases() -> None:
    tasks = _compile_six_tasks(
        _X_BASE,
        _Y_BASE,
        _X_COMPARISON,
        _Y_COMPARISON,
    )
    fgnz = _enhanced_fgnz_accounts(tasks)
    productivity = np.array([account.productivity_change for account in fgnz])
    fgnz_technical = np.array([account.technical_change_crs for account in fgnz])
    fgnz_pure = np.array([account.pure_efficiency_change for account in fgnz])
    fgnz_scale = np.array([account.scale_efficiency_change for account in fgnz])

    # Independently frozen Ray--Desli values for the same rational fixture.
    ray_technical = np.array([6 / 5, np.sqrt(33) / 5, np.sqrt(67 / 50), 5 / 4])
    ray_pure = np.array([1, 1, 1, 8 / 7])
    ray_scale = productivity / (ray_technical * ray_pure)

    assert np.all(np.abs(fgnz_technical - ray_technical) > 1e-6)
    assert np.all(np.abs(fgnz_scale - ray_scale) > 1e-6)
    np.testing.assert_allclose(
        fgnz_technical * fgnz_pure * fgnz_scale,
        productivity,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        ray_technical * ray_pure * ray_scale,
        productivity,
        atol=1e-12,
    )


def test_compiler_keeps_the_source_multi_input_multi_output_domain() -> None:
    baseline = _compile_six_tasks(
        _X_BASE,
        _Y_BASE,
        _X_COMPARISON,
        _Y_COMPARISON,
    )
    duplicated = _compile_six_tasks(
        np.column_stack([_X_BASE, 2.0 * _X_BASE]),
        np.column_stack([_Y_BASE, 3.0 * _Y_BASE]),
        np.column_stack([_X_COMPARISON, 2.0 * _X_COMPARISON]),
        np.column_stack([_Y_COMPARISON, 3.0 * _Y_COMPARISON]),
    )
    np.testing.assert_allclose(duplicated.crs, baseline.crs, atol=1e-12)
    np.testing.assert_allclose(duplicated.vrs_own, baseline.vrs_own, atol=1e-12)


@pytest.mark.parametrize(
    ("x_comparison", "y_comparison", "message"),
    [
        (_X_COMPARISON[:-1], _Y_COMPARISON, "matched adjacent panel"),
        (_X_COMPARISON, _Y_COMPARISON * 0.0, "strictly positive data"),
        (
            _X_COMPARISON,
            np.array([[1.2], [2.4], [np.nan], [5.0]]),
            "finite observations",
        ),
        (
            _X_COMPARISON,
            np.column_stack([_Y_COMPARISON, _Y_COMPARISON]),
            "common output variable",
        ),
    ],
)
def test_certified_domain_rejects_unmatched_zero_or_nonfinite_data(
    x_comparison: np.ndarray,
    y_comparison: np.ndarray,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        _compile_six_tasks(
            _X_BASE,
            _Y_BASE,
            x_comparison,
            y_comparison,
        )


def test_unavailable_crs_primitive_fails_closed() -> None:
    tasks = _compile_six_tasks(
        _X_BASE,
        _Y_BASE,
        _X_COMPARISON,
        _Y_COMPARISON,
    )
    crs = tasks.crs.copy()
    crs[0, 0, 1] = 0.0

    with pytest.raises(ValueError, match="all four CRS source distances"):
        _enhanced_fgnz_accounts(_SixDistanceTasks(crs=crs, vrs_own=tasks.vrs_own))


def test_unavailable_vrs_own_task_preserves_only_the_crs_core_account() -> None:
    tasks = _compile_six_tasks(
        _X_BASE,
        _Y_BASE,
        _X_COMPARISON,
        _Y_COMPARISON,
    )
    vrs_own = tasks.vrs_own.copy()
    vrs_own[0, 1] = np.nan

    account = _enhanced_fgnz_accounts(
        _SixDistanceTasks(crs=tasks.crs, vrs_own=vrs_own)
    )[0]
    assert account.productivity_change == pytest.approx(6 / 5, abs=1e-12)
    assert account.efficiency_change == pytest.approx(15 / 14, abs=1e-12)
    assert account.technical_change_crs == pytest.approx(28 / 25, abs=1e-12)
    assert account.core_residual == pytest.approx(0.0, abs=1e-12)
    assert account.pure_efficiency_change is None
    assert account.scale_efficiency_change is None
    assert account.productivity_residual is None
    assert account.efficiency_residual is None
    assert not account.decomposition_defined
    assert account.decomposition_status == "vrs_own_unavailable"
