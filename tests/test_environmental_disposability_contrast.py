from __future__ import annotations

import numpy as np
import pytest

from deapack import (
    SBMNS,
    DEAData,
    NonSeparableUndesirableSBM,
    ToneNonSeparableSBM,
    UndesirableSBM,
    dataset_info,
    load_dataset,
)
from deapack.exceptions import DataValidationError, ModelSpecificationError


def _frame():  # type: ignore[no-untyped-def]
    return load_dataset("environmental_disposability_contrast")


def _data(frame=None) -> DEAData:  # type: ignore[no-untyped-def]
    source = _frame() if frame is None else frame
    roles = dataset_info("environmental_disposability_contrast").roles
    return DEAData.from_frame(
        source,
        dmu=roles["dmu"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
        bad_outputs=roles["bad_outputs"],
    )


def _model(**kwargs):  # type: ignore[no-untyped-def]
    roles = dataset_info("environmental_disposability_contrast").roles
    return ToneNonSeparableSBM(
        nonseparable_outputs=roles["nonseparable_good_outputs"],
        nonseparable_bad_outputs=roles["nonseparable_bad_outputs"],
        alpha_min=0.7,
        **kwargs,
    )


def test_project_disposability_case_closes_both_sbm_contracts() -> None:
    separable = UndesirableSBM(returns_to_scale="vrs").fit(_data())
    nonseparable = _model(returns_to_scale="vrs").fit(_data())
    summary = nonseparable.summary().set_index("dmu_id")
    focal_peers = nonseparable.peers("Focal").set_index("reference_dmu_id")
    focal_targets = nonseparable.targets_for("Focal").set_index(["role", "variable"])

    assert SBMNS is ToneNonSeparableSBM
    assert NonSeparableUndesirableSBM is ToneNonSeparableSBM
    assert separable.summary()["score"].between(0.0, 1.0 + 1e-9).all()
    assert nonseparable.summary()["score"].between(0.0, 1.0 + 1e-9).all()
    assert nonseparable.summary()["alpha"].between(0.7, 1.0 + 1e-9).all()
    assert nonseparable.targets["target"].notna().all()
    assert nonseparable.metadata["nonseparable_projection"] == "alpha_times_source"
    assert summary.loc["Reference", "score"] == pytest.approx(1.0)
    assert summary.loc["Focal", "score"] == pytest.approx(224.0 / 771.0)
    assert summary.loc["Focal", "alpha"] == pytest.approx(7.0 / 10.0)
    assert focal_peers.loc["Reference", "lambda"] == pytest.approx(17.0 / 20.0)
    assert focal_peers.loc["Focal", "lambda"] == pytest.approx(3.0 / 20.0)
    assert focal_targets.loc[("input", "resource_a"), "target"] == pytest.approx(
        13.0 / 5.0
    )
    assert focal_targets.loc[("output", "joint_service"), "target"] == pytest.approx(
        119.0 / 10.0
    )


@pytest.mark.parametrize("returns_to_scale", ["crs", "vrs", "nirs", "ndrs"])
def test_project_disposability_case_supports_declared_rts(
    returns_to_scale: str,
) -> None:
    result = _model(returns_to_scale=returns_to_scale).fit(_data())
    assert set(result.summary()["solver_status"]) == {"optimal"}
    assert set(result.summary()["returns_to_scale"]) == {returns_to_scale}
    assert np.isfinite(result.summary()[["score", "alpha"]]).all().all()


def test_nonseparable_sbm_is_independently_units_invariant() -> None:
    frame = _frame()
    roles = dataset_info("environmental_disposability_contrast").roles
    scaled = frame.copy()
    factors = {
        roles["inputs"][0]: 100.0,
        roles["inputs"][1]: 0.01,
        roles["outputs"][0]: 10.0,
        roles["outputs"][1]: 0.5,
        roles["bad_outputs"][0]: 1_000.0,
        roles["bad_outputs"][1]: 2.0,
    }
    for variable, factor in factors.items():
        scaled[variable] *= factor

    baseline = _model().fit(_data(frame))
    changed = _model().fit(_data(scaled))
    np.testing.assert_allclose(changed.summary()["score"], baseline.summary()["score"])
    np.testing.assert_allclose(changed.summary()["alpha"], baseline.summary()["alpha"])


@pytest.mark.parametrize("alpha_min", [-0.01, 1.01, float("nan"), float("inf")])
def test_nonseparable_sbm_rejects_invalid_alpha(alpha_min: float) -> None:
    roles = dataset_info("environmental_disposability_contrast").roles
    with pytest.raises(ValueError, match=r"finite and lie in \[0, 1\]"):
        ToneNonSeparableSBM(
            nonseparable_outputs=roles["nonseparable_good_outputs"],
            nonseparable_bad_outputs=roles["nonseparable_bad_outputs"],
            alpha_min=alpha_min,
        )


def test_nonseparable_sbm_validates_partition_and_positive_data() -> None:
    roles = dataset_info("environmental_disposability_contrast").roles
    with pytest.raises(ModelSpecificationError, match="at least one"):
        ToneNonSeparableSBM(
            nonseparable_outputs=(),
            nonseparable_bad_outputs=roles["nonseparable_bad_outputs"],
        )

    frame = _frame()
    frame.loc[0, roles["nonseparable_good_outputs"][0]] = 0.0
    with pytest.raises(DataValidationError, match="strictly positive"):
        _model().fit(_data(frame))
