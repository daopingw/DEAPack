from __future__ import annotations

import pandas as pd
import pytest

from deapack import DEAResult


def _summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "dmu_id": "A",
                "period": None,
                "score": 0.8,
                "efficiency": 0.8,
                "distance": float("nan"),
                "is_efficient": False,
                "solver_status": "optimal",
                "model_family": "test",
            }
        ]
    )


def test_appraisal_rows_preserve_protocol_specific_roles() -> None:
    result = DEAResult(
        summary_frame=_summary(),
        appraisals=pd.DataFrame(
            [
                {
                    "appraiser_dmu_id": "A",
                    "evaluatee_dmu_id": "A",
                    "appraisal": 1.0,
                },
                {
                    "appraiser_dmu_id": "B",
                    "evaluatee_dmu_id": "A",
                    "appraisal": 0.8,
                },
                {
                    "appraiser_dmu_id": "A",
                    "evaluatee_dmu_id": "B",
                    "appraisal": 0.7,
                },
            ]
        ),
    )

    evaluatee = result.appraisal_rows_for("A")
    appraiser = result.appraisal_rows_for("A", id_column="appraiser_dmu_id")

    assert evaluatee["appraisal"].tolist() == [1.0, 0.8]
    assert appraiser["appraisal"].tolist() == [1.0, 0.7]
    with pytest.raises(KeyError, match="protected_dmu_id"):
        result.appraisal_rows_for("A", id_column="protected_dmu_id")


def test_history_for_returns_one_dmu_without_mutating_result() -> None:
    result = DEAResult(
        summary_frame=_summary(),
        history=pd.DataFrame(
            [
                {"iteration": 0, "dmu_id": "A", "score": 0.5},
                {"iteration": 0, "dmu_id": "B", "score": 0.6},
                {"iteration": 1, "dmu_id": "A", "score": 0.7},
            ]
        ),
    )

    history = result.history_for("A")
    history.loc[:, "score"] = -1.0

    assert result.history_for("A")["score"].tolist() == [0.5, 0.7]


def test_multiplier_rows_preserve_pair_specific_roles() -> None:
    result = DEAResult(
        summary_frame=_summary(),
        multipliers=pd.DataFrame(
            [
                {
                    "protected_dmu_id": "A",
                    "focal_dmu_id": "B",
                    "period": None,
                    "variable": "x",
                    "weight": 0.5,
                },
                {
                    "protected_dmu_id": "B",
                    "focal_dmu_id": "A",
                    "period": None,
                    "variable": "x",
                    "weight": 1.0,
                },
            ]
        ),
    )

    protected = result.multipliers_for("A", id_column="protected_dmu_id")
    focal = result.multipliers_for("A", id_column="focal_dmu_id")

    assert protected["focal_dmu_id"].tolist() == ["B"]
    assert focal["protected_dmu_id"].tolist() == ["B"]
    with pytest.raises(KeyError, match="dmu_id"):
        result.multipliers_for("A")


def test_result_metadata_is_deeply_immutable() -> None:
    result = DEAResult(
        summary_frame=_summary(),
        metadata={
            "initialization": {"kind": "source_profile"},
            "audit": [{"certified": True}],
        },
    )

    with pytest.raises(TypeError, match="immutable"):
        result.metadata["initialization"]["kind"] = "changed"
    with pytest.raises(TypeError, match="immutable"):
        result.metadata["audit"][0]["certified"] = False
    with pytest.raises(TypeError, match="immutable"):
        result.metadata["audit"].append({"certified": False})
    assert isinstance(result.metadata["audit"], list)
