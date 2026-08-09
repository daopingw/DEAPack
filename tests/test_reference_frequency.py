import json
import time
from dataclasses import replace
from typing import Any

import numpy as np
import pandas as pd
import pytest

from deapack import (
    BCC,
    CCR,
    DDF,
    FCH,
    FDH,
    FRH,
    RAM,
    SBM,
    AdditiveDEA,
    DEAData,
    DEAResult,
    InputSBM,
    OutputSBM,
    ReferenceFrequencyResult,
    reference_frequency,
)
from deapack.exceptions import ModelSpecificationError


def _data(ids: list[object] | None = None) -> DEAData:
    labels = ["A", "B", "C", "D"] if ids is None else ids
    frame = pd.DataFrame(
        {
            "dmu": labels,
            "x": [1.0, 2.0, 1.5, 3.0],
            "y": [1.0, 1.0, 0.6, 1.2],
        }
    )
    return DEAData.from_frame(frame, dmu="dmu", inputs="x", outputs="y")


def _base_result() -> DEAResult:
    return CCR().fit(_data())


def _mutable_metadata(result: DEAResult) -> dict[str, Any]:
    return json.loads(json.dumps(result.metadata))


def _certified_plan_result(
    ids: list[object],
    edges: list[tuple[object, object, float]],
) -> DEAResult:
    source = _base_result()
    summary = source.summary()
    mapping = dict(zip(summary["dmu_id"], ids, strict=True))
    summary["dmu_id"] = summary["dmu_id"].map(mapping).astype(object)
    intensities = pd.DataFrame(
        {
            "dmu_id": [edge[0] for edge in edges],
            "period": pd.Series([None] * len(edges), dtype=object),
            "reference_dmu_id": [edge[1] for edge in edges],
            "reference_period": pd.Series([None] * len(edges), dtype=object),
            "lambda": [edge[2] for edge in edges],
        }
    )
    return replace(source, summary_frame=summary, intensities=intensities)


def _dictionary_oracle(
    ids: list[object],
    edges: list[tuple[object, object, float]],
) -> pd.DataFrame:
    counts = {identifier: 0 for identifier in ids}
    self_counts = {identifier: 0 for identifier in ids}
    other_counts = {identifier: 0 for identifier in ids}
    for evaluated, reference, intensity in edges:
        assert np.isfinite(intensity) and intensity > 0.0
        counts[reference] += 1
        if evaluated == reference:
            self_counts[reference] += 1
        else:
            other_counts[reference] += 1
    return pd.DataFrame(
        {
            "reference_dmu_id": ids,
            "reference_period": pd.Series([None] * len(ids), dtype=object),
            "reference_frequency": [counts[identifier] for identifier in ids],
            "self_reference_frequency": [self_counts[identifier] for identifier in ids],
            "other_reference_frequency": [
                other_counts[identifier] for identifier in ids
            ],
            "reference_rate": [counts[identifier] / len(ids) for identifier in ids],
            "is_referenced": [counts[identifier] > 0 for identifier in ids],
        }
    )


def test_selected_plan_frequency_matches_independent_dictionary_oracle() -> None:
    ids: list[object] = ["North", "South", "East", "West"]
    edges = [
        ("North", "North", 1.0),
        ("South", "North", 0.4),
        ("South", "East", 0.6),
        ("East", "South", 1.0),
        ("West", "South", 0.5),
        ("West", "West", 0.5),
    ]
    source = _certified_plan_result(ids, list(reversed(edges)))

    output = reference_frequency(source)

    assert isinstance(output, ReferenceFrequencyResult)
    pd.testing.assert_frame_equal(
        output.reference_frame,
        _dictionary_oracle(ids, edges),
    )
    assert output.reference_frame["reference_frequency"].sum() == len(edges)
    np.testing.assert_array_equal(
        output.reference_frame["reference_frequency"],
        output.reference_frame["self_reference_frequency"]
        + output.reference_frame["other_reference_frequency"],
    )
    assert output.metadata["self_edge_count"] == 2
    assert output.metadata["other_edge_count"] == 4


@pytest.mark.parametrize(
    "model",
    [CCR(), BCC(), AdditiveDEA(), RAM(), SBM(), InputSBM(), OutputSBM(), DDF()],
    ids=["CCR", "BCC", "Additive", "RAM", "SBM", "InputSBM", "OutputSBM", "DDF"],
)
def test_classic_convex_models_integrate_without_another_solve(model: Any) -> None:
    source = model.fit(_data())
    before_summary = source.summary_frame.copy(deep=True)
    before_intensities = source.intensities.copy(deep=True)
    before_solver_calls = source.metadata["solver_calls"]

    output = source.reference_frequency()

    oracle_edges = [
        (row.dmu_id, row.reference_dmu_id, float(row.lambda_))
        for row in source.intensities.rename(columns={"lambda": "lambda_"}).itertuples()
    ]
    oracle = _dictionary_oracle(source.summary()["dmu_id"].tolist(), oracle_edges)
    pd.testing.assert_frame_equal(output.reference_frame, oracle)
    pd.testing.assert_frame_equal(source.summary_frame, before_summary)
    pd.testing.assert_frame_equal(source.intensities, before_intensities)
    assert source.metadata["solver_calls"] == before_solver_calls
    assert output.metadata["additional_solver_calls"] == 0
    assert output.metadata["method_id"] == "analysis.reference_frequency.selected_plan"
    assert output.metadata["source_peer_tolerance"] == source.metadata["peer_tolerance"]
    assert output.metadata["source_expanded_spec"] == source.metadata["expanded_spec"]
    assert (
        output.metadata["source_model_family"]
        == source.summary().loc[0, "model_family"]
    )
    assert output.metadata["frequency_unit"] == (
        "reported_active_solver_selected_peer_edge"
    )
    assert output.metadata["expanded_spec"]["reference"] == {
        "kind": "global",
        "account": (
            "reported_solver_selected_active_peer_edges_strictly_above_"
            "source_peer_tolerance"
        ),
        "peer_reporting_threshold": source.metadata["peer_tolerance"],
    }
    with pytest.raises(TypeError, match="immutable"):
        output.metadata["outlier_claim"] = True


@pytest.mark.parametrize("model", [FDH(), FCH(), FRH()], ids=["FDH", "FCH", "FRH"])
def test_nonconvex_hulls_are_rejected(model: Any) -> None:
    with pytest.raises(ModelSpecificationError, match="continuous-convex full-DEA"):
        reference_frequency(model.fit(_data()))


def test_actual_panel_result_is_rejected_even_under_global_reference() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "A", "B"],
            "year": [2020, 2020, 2021, 2021],
            "x": [1.0, 2.0, 1.1, 2.1],
            "y": [1.0, 1.0, 1.1, 1.1],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        period="year",
        inputs="x",
        outputs="y",
    )

    with pytest.raises(ModelSpecificationError, match="period-indexed summaries"):
        reference_frequency(CCR(reference="global").fit(data))


@pytest.mark.parametrize(
    ("scope", "expected"),
    [
        ("network", "network, staged, and dynamic"),
        ("dynamic", "network, staged, and dynamic"),
        ("productivity", "direct static DEA"),
        ("super", "direct static DEA"),
        ("cross", "direct static DEA"),
        ("partial", "partial, non-DEA, and nonconvex"),
        ("local_reference", "reference policy is not global"),
    ],
)
def test_noncore_analysis_scopes_fail_closed(scope: str, expected: str) -> None:
    source = _base_result()
    metadata = _mutable_metadata(source)
    expanded = metadata["expanded_spec"]
    if scope == "network":
        expanded["graph"]["kind"] = "network"
    elif scope == "dynamic":
        expanded["graph"]["kind"] = "dynamic"
    elif scope == "productivity":
        metadata["method_id"] = "productivity.malmquist.adjacent"
        expanded["analysis"]["kind"] = "productivity_index"
    elif scope == "super":
        metadata["method_id"] = "evaluation.super_efficiency"
    elif scope == "cross":
        metadata["method_id"] = "evaluation.cross_efficiency"
        expanded["evaluation_protocol"]["kind"] = "cross_appraisal"
    elif scope == "partial":
        expanded["estimator"]["kind"] = "partial_frontier"
    elif scope == "local_reference":
        expanded["reference"]["kind"] = "contemporaneous"
    else:  # pragma: no cover - protects the test table itself
        raise AssertionError(scope)

    with pytest.raises(ModelSpecificationError, match=expected):
        reference_frequency(replace(source, metadata=metadata))


@pytest.mark.parametrize("column", ["process_id", "lambda_stage", "intensity_role"])
def test_role_specific_or_multiple_intensity_accounts_are_rejected(column: str) -> None:
    source = _base_result()
    intensities = source.intensities.copy()
    intensities[column] = "stage_1"

    with pytest.raises(ModelSpecificationError, match="role-specific activity"):
        reference_frequency(replace(source, intensities=intensities))


@pytest.mark.parametrize("invalid_lambda", [0.0, -0.1, np.nan, np.inf, -np.inf])
def test_nonpositive_or_nonfinite_active_intensity_is_rejected(
    invalid_lambda: float,
) -> None:
    source = _base_result()
    intensities = source.intensities.copy()
    intensities.loc[intensities.index[0], "lambda"] = invalid_lambda

    with pytest.raises(ModelSpecificationError, match="finite and strictly positive"):
        reference_frequency(replace(source, intensities=intensities))


def test_string_encoded_intensities_are_rejected_without_coercion() -> None:
    source = _base_result()
    intensities = source.intensities.copy()
    intensities["lambda"] = intensities["lambda"].map(str)

    with pytest.raises(ModelSpecificationError, match="numeric, non-boolean dtype"):
        reference_frequency(replace(source, intensities=intensities))


def test_reported_edges_must_exceed_the_source_peer_reporting_threshold() -> None:
    source = _base_result()
    intensities = source.intensities.copy()
    intensities.loc[intensities.index[0], "lambda"] = (
        float(source.metadata["peer_tolerance"]) / 2.0
    )

    with pytest.raises(ModelSpecificationError, match=r"above.*peer_tolerance"):
        reference_frequency(replace(source, intensities=intensities))


@pytest.mark.parametrize("peer_tolerance", [None, True, -1.0, np.inf, np.nan])
def test_missing_or_invalid_peer_threshold_provenance_fails_closed(
    peer_tolerance: object,
) -> None:
    source = _base_result()
    metadata = _mutable_metadata(source)
    if peer_tolerance is None:
        del metadata["peer_tolerance"]
    else:
        metadata["peer_tolerance"] = peer_tolerance

    with pytest.raises(ModelSpecificationError, match="peer_tolerance"):
        reference_frequency(replace(source, metadata=metadata))


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("missing_column", "missing columns"),
        ("duplicate_edge", "duplicate peer edges"),
        ("unknown_evaluatee", "unevaluated dmu_id"),
        ("unknown_reference", "outside the global sample"),
        ("missing_evaluation", "no certified active peer edge"),
        ("period_edge", "period-indexed peer edges"),
    ],
)
def test_malformed_peer_tables_fail_closed(case: str, expected: str) -> None:
    source = _base_result()
    intensities = source.intensities.copy()
    if case == "missing_column":
        intensities = intensities.drop(columns="reference_period")
    elif case == "duplicate_edge":
        intensities = pd.concat([intensities, intensities.iloc[[0]]], ignore_index=True)
    elif case == "unknown_evaluatee":
        intensities.loc[intensities.index[0], "dmu_id"] = "UNKNOWN"
    elif case == "unknown_reference":
        intensities.loc[intensities.index[0], "reference_dmu_id"] = "UNKNOWN"
    elif case == "missing_evaluation":
        missing = source.summary_frame.iloc[-1]["dmu_id"]
        intensities = intensities.loc[intensities["dmu_id"] != missing]
    elif case == "period_edge":
        intensities.loc[intensities.index[0], "period"] = 2024
    else:  # pragma: no cover - protects the test table itself
        raise AssertionError(case)

    with pytest.raises(ModelSpecificationError, match=expected):
        reference_frequency(replace(source, intensities=intensities))


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("peer_invalid", "peer_valid=True"),
        ("peer_status_missing", "certified peer_status"),
        ("peer_status_uncertified", "certified peer_status"),
        ("solver_nonoptimal", "solver_status='optimal'"),
        ("duplicate_dmu", "exactly one row per dmu_id"),
    ],
)
def test_incomplete_summary_peer_contract_never_changes_denominator(
    case: str,
    expected: str,
) -> None:
    source = _base_result()
    summary = source.summary()
    if case == "peer_invalid":
        summary.loc[summary.index[0], "peer_valid"] = False
    elif case == "peer_status_missing":
        summary.loc[summary.index[0], "peer_status"] = pd.NA
    elif case == "peer_status_uncertified":
        summary.loc[summary.index[0], "peer_status"] = "reported_but_uncertified"
    elif case == "solver_nonoptimal":
        summary.loc[summary.index[0], "solver_status"] = "numerical_error"
    elif case == "duplicate_dmu":
        summary.loc[summary.index[-1], "dmu_id"] = summary.iloc[0]["dmu_id"]
    else:  # pragma: no cover - protects the test table itself
        raise AssertionError(case)

    with pytest.raises(ModelSpecificationError, match=expected):
        reference_frequency(replace(source, summary_frame=summary))


def test_mixed_labels_and_input_row_order_do_not_corrupt_accounts() -> None:
    ids: list[object] = ["Clinic Z", 17, "医院-β", "DMU 02"]
    edges = [
        ("DMU 02", "DMU 02", 0.2),
        (17, "医院-β", 0.3),
        ("Clinic Z", 17, 1.0),
        ("DMU 02", "Clinic Z", 0.8),
        ("医院-β", "医院-β", 1.0),
        (17, "Clinic Z", 0.7),
    ]
    source = _certified_plan_result(ids, edges)

    output = reference_frequency(source)

    assert output.reference_frame["reference_dmu_id"].tolist() == ids
    expected_pairs = [
        ("Clinic Z", 17),
        (17, "Clinic Z"),
        (17, "医院-β"),
        ("医院-β", "医院-β"),
        ("DMU 02", "Clinic Z"),
        ("DMU 02", "DMU 02"),
    ]
    assert (
        list(
            output.edge_frame[["dmu_id", "reference_dmu_id"]].itertuples(
                index=False,
                name=None,
            )
        )
        == expected_pairs
    )
    pd.testing.assert_frame_equal(
        output.reference_frame,
        _dictionary_oracle(ids, edges),
    )


def test_duplicate_frontier_observations_disclose_selected_plan_limit() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C"],
            "x": [1.0, 1.0, 2.0],
            "y": [1.0, 1.0, 1.0],
        }
    )
    source = BCC().fit(DEAData.from_frame(frame, dmu="dmu", inputs="x", outputs="y"))

    output = reference_frequency(source)

    assert output.metadata["alternate_optima_assessed"] is False
    assert output.metadata["global_reference_set_claim"] is False
    assert output.metadata["outlier_claim"] is False
    assert output.metadata["inference"] == "none"
    assert (
        output.metadata["expanded_spec"]["evaluation_protocol"][
            "alternate_optima_assessed"
        ]
        is False
    )
    assert output.metadata["expanded_spec"]["analysis"]["claim"] == (
        "one_certified_solver_selected_plan"
    )


def test_large_edge_account_is_vectorized_and_keeps_zero_solve_contract() -> None:
    n_observations = 5_000
    peers_per_observation = 20
    identifiers = np.arange(n_observations, dtype=np.int64)
    evaluation_ids = np.repeat(identifiers, peers_per_observation)
    offsets = np.tile(np.arange(peers_per_observation), n_observations)
    reference_ids = (evaluation_ids + offsets) % n_observations
    summary = pd.DataFrame(
        {
            "dmu_id": identifiers,
            "period": pd.Series([None] * n_observations, dtype=object),
            "score": np.ones(n_observations),
            "efficiency": np.ones(n_observations),
            "distance": np.zeros(n_observations),
            "is_efficient": np.ones(n_observations, dtype=bool),
            "solver_status": np.repeat("optimal", n_observations),
            "model_family": np.repeat("radial", n_observations),
            "peer_valid": np.ones(n_observations, dtype=bool),
            "peer_status": np.repeat(
                "certified_primary_program",
                n_observations,
            ),
        }
    )
    intensities = pd.DataFrame(
        {
            "dmu_id": evaluation_ids,
            "period": pd.Series([None] * len(evaluation_ids), dtype=object),
            "reference_dmu_id": reference_ids,
            "reference_period": pd.Series(
                [None] * len(evaluation_ids),
                dtype=object,
            ),
            "lambda": np.full(
                len(evaluation_ids),
                1.0 / peers_per_observation,
            ),
        }
    )
    source = replace(
        _base_result(),
        summary_frame=summary,
        intensities=intensities,
    )

    started = time.perf_counter()
    output = reference_frequency(source)
    elapsed = time.perf_counter() - started

    assert len(output.edge_frame) == n_observations * peers_per_observation
    assert (output.reference_frame["reference_frequency"] == 20).all()
    assert (output.reference_frame["self_reference_frequency"] == 1).all()
    assert (output.reference_frame["other_reference_frequency"] == 19).all()
    assert output.metadata["additional_solver_calls"] == 0
    assert elapsed < 5.0


def test_non_result_input_is_rejected_before_table_access() -> None:
    with pytest.raises(TypeError, match="result must be a DEAResult"):
        reference_frequency(object())  # type: ignore[arg-type]
