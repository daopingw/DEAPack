from __future__ import annotations

import inspect
import json

import numpy as np
import pandas as pd
import pytest

from deapack import (
    ActivitySpecificWeakDisposalDDF,
    ByProductionDirectionalDistanceDEA,
    ByProductionFareGrosskopfLovellDEA,
    ChungFareGrosskopfDDF,
    CommonFactorWeakDisposalDDF,
    DEAData,
    EnvironmentalDirectionalDistanceDEA,
    MaterialBalanceDEA,
    PeerEligibility,
    PeerEligibilityProvenance,
    ReferenceSpec,
    ToneNonSeparableSBM,
    UndesirableSlacksBasedDEA,
    ZhouAngWangNonCHPEnergyCarbonDEA,
)
from deapack.exceptions import ModelSpecificationError


def _provenance() -> PeerEligibilityProvenance:
    return PeerEligibilityProvenance(
        rule_name="licensed-comparison-population",
        source="institutional benchmarking charter",
        comparison_population="declared eligible operating units",
        decision_owner="benchmarking committee",
        validity_period="2025",
    )


def _by_row(rows: list[list[int]]) -> PeerEligibility:
    return PeerEligibility.by_row(rows, provenance=_provenance())


def _by_key(
    candidates: dict[str, list[str]],
) -> PeerEligibility:
    return PeerEligibility.by_key(candidates, provenance=_provenance())


def _cfg_data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["Old", "New"],
                "resource": [1.0, 1.0],
                "service": [1.0, 2.0],
                "residual": [2.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="resource",
        outputs="service",
        bad_outputs="residual",
    )


def _separable_data(*, dominated_second: bool = True) -> DEAData:
    if dominated_second:
        inputs = [1.0, 2.0]
        outputs = [2.0, 1.0]
        bad_outputs = [1.0, 2.0]
    else:
        inputs = [2.0, 1.0]
        outputs = [1.0, 2.0]
        bad_outputs = [2.0, 1.0]
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["Reference", "Assessed"],
                "resource": inputs,
                "service": outputs,
                "residual": bad_outputs,
            }
        ),
        dmu="dmu",
        inputs="resource",
        outputs="service",
        bad_outputs="residual",
    )


def _sorted_targets(result: object) -> pd.DataFrame:
    return (
        result.targets.sort_values(["dmu_id", "role", "variable"])
        .reset_index(drop=True)
        .loc[:, ["dmu_id", "role", "variable", "observed", "target"]]
    )


def _assert_semantic_tables_equal(left: object, right: object) -> None:
    table_keys = {
        "slacks": ["dmu_id", "period", "role", "variable"],
        "targets": ["dmu_id", "period", "role", "variable"],
        "intensities": [
            "dmu_id",
            "period",
            "reference_dmu_id",
            "reference_period",
        ],
        "duals": ["dmu_id", "period", "phase", "constraint_role", "variable"],
    }
    for table_name, preferred_keys in table_keys.items():
        left_table = getattr(left, table_name)
        right_table = getattr(right, table_name)
        keys = [column for column in preferred_keys if column in left_table.columns]
        left_sorted = left_table.sort_values(keys).reset_index(drop=True)
        right_sorted = right_table.sort_values(keys).reset_index(drop=True)
        pd.testing.assert_frame_equal(
            left_sorted,
            right_sorted,
            check_exact=False,
            rtol=1.0e-11,
            atol=1.0e-12,
        )


def test_environmental_routes_validate_the_immutable_policy_type() -> None:
    constructors = (
        lambda: EnvironmentalDirectionalDistanceDEA(
            disposability="strong",
            peer_eligibility=object(),  # type: ignore[arg-type]
        ),
        lambda: CommonFactorWeakDisposalDDF(
            peer_eligibility=object(),  # type: ignore[arg-type]
        ),
        lambda: ChungFareGrosskopfDDF(
            peer_eligibility=object(),  # type: ignore[arg-type]
        ),
        lambda: UndesirableSlacksBasedDEA(
            peer_eligibility=object(),  # type: ignore[arg-type]
        ),
    )

    for constructor in constructors:
        with pytest.raises(TypeError, match=r"peer_eligibility.*PeerEligibility"):
            constructor()


def test_full_population_policy_preserves_environmental_numerics() -> None:
    cfg_data = _cfg_data()
    cfg_policy = _by_row([[0, 1], [0, 1]])

    route_pairs = (
        (
            EnvironmentalDirectionalDistanceDEA(
                disposability="strong",
                null_jointness=False,
            ),
            EnvironmentalDirectionalDistanceDEA(
                disposability="strong",
                null_jointness=False,
                peer_eligibility=cfg_policy,
            ),
        ),
        (
            CommonFactorWeakDisposalDDF(),
            CommonFactorWeakDisposalDDF(peer_eligibility=cfg_policy),
        ),
    )
    for baseline_model, restricted_model in route_pairs:
        baseline = baseline_model.fit(cfg_data)
        restricted = restricted_model.fit(cfg_data)
        np.testing.assert_allclose(
            restricted.summary()["distance"],
            baseline.summary()["distance"],
        )
        _assert_semantic_tables_equal(restricted, baseline)

    cfg_baseline = ChungFareGrosskopfDDF().fit(cfg_data)
    cfg_restricted = ChungFareGrosskopfDDF(peer_eligibility=cfg_policy).fit(cfg_data)

    np.testing.assert_allclose(
        cfg_restricted.summary()["distance"],
        cfg_baseline.summary()["distance"],
    )
    pd.testing.assert_frame_equal(
        _sorted_targets(cfg_restricted),
        _sorted_targets(cfg_baseline),
    )
    _assert_semantic_tables_equal(cfg_restricted, cfg_baseline)
    assert (
        cfg_restricted.metadata["expanded_spec"]["evaluation_protocol"]["kind"]
        == "self_appraisal"
    )

    sbm_data = _separable_data()
    sbm_policy = _by_row([[0, 1], [0, 1]])
    sbm_baseline = UndesirableSlacksBasedDEA().fit(sbm_data)
    sbm_restricted = UndesirableSlacksBasedDEA(peer_eligibility=sbm_policy).fit(
        sbm_data
    )

    np.testing.assert_allclose(
        sbm_restricted.summary()["score"],
        sbm_baseline.summary()["score"],
    )
    pd.testing.assert_frame_equal(
        _sorted_targets(sbm_restricted),
        _sorted_targets(sbm_baseline),
    )
    _assert_semantic_tables_equal(sbm_restricted, sbm_baseline)


@pytest.mark.parametrize(
    "constructor",
    [CommonFactorWeakDisposalDDF, ChungFareGrosskopfDDF],
)
def test_common_factor_routes_match_manual_reference_and_keep_signed_distance(
    constructor: type[CommonFactorWeakDisposalDDF],
) -> None:
    data = _cfg_data()
    eligibility = _by_row([[0], [0]])
    restricted = constructor(
        peer_eligibility=eligibility,
        allow_negative_distance=True,
    ).fit(data)
    manual = constructor(
        reference=ReferenceSpec(kind="custom", custom_rows=[0]),
        allow_negative_distance=True,
    ).fit(data)

    np.testing.assert_allclose(
        restricted.summary()["distance"],
        manual.summary()["distance"],
    )
    pd.testing.assert_frame_equal(_sorted_targets(restricted), _sorted_targets(manual))
    _assert_semantic_tables_equal(restricted, manual)
    summary = restricted.summary().set_index("dmu_id")
    assert summary.loc["New", "distance"] == pytest.approx(-3.0 / 5.0)
    assert not bool(summary.loc["New", "self_in_reference"])
    assert not bool(summary.loc["New", "is_within_reference_technology"])
    assert summary.loc["New", "membership_status"] == ("outside_reference_technology")
    assert summary["base_reference_size"].tolist() == [2, 2]
    assert summary["reference_size"].tolist() == [1, 1]
    assert restricted.metadata["expanded_spec"]["evaluation_protocol"]["kind"] == (
        "mixed_self_and_external_reference_appraisal"
    )
    assert set(restricted.intensities["reference_dmu_id"]) <= {"Old"}
    assert restricted.metadata["null_jointness"] is True


def test_cfg_reports_fully_external_appraisal_and_external_infeasibility() -> None:
    data = _cfg_data()
    external = ChungFareGrosskopfDDF(
        peer_eligibility=_by_row([[1], [0]]),
        compute_slacks=False,
    ).fit(data)

    assert not external.summary()["self_in_reference"].any()
    assert external.metadata["expanded_spec"]["evaluation_protocol"]["kind"] == (
        "external_reference_appraisal"
    )

    nonnegative_only = ChungFareGrosskopfDDF(
        peer_eligibility=_by_row([[0], [0]]),
        allow_negative_distance=False,
        compute_slacks=False,
    ).fit(data)
    assessed = nonnegative_only.summary().set_index("dmu_id").loc["New"]
    assert assessed["solver_status"] == "infeasible"
    assert assessed["score_status"] == "outside_reference_technology"
    assert assessed["membership_status"] == "outside_reference_technology"
    assert not bool(assessed["score_valid"])


def test_generic_strong_disposal_keeps_technology_semantics_under_policy() -> None:
    data = _separable_data()
    eligibility = _by_row([[0], [0]])
    restricted = EnvironmentalDirectionalDistanceDEA(
        disposability="strong",
        null_jointness=False,
        peer_eligibility=eligibility,
    ).fit(data)
    manual = EnvironmentalDirectionalDistanceDEA(
        disposability="strong",
        null_jointness=False,
        reference=ReferenceSpec(kind="custom", custom_rows=[0]),
    ).fit(data)

    np.testing.assert_allclose(
        restricted.summary()["distance"],
        manual.summary()["distance"],
    )
    assert restricted.metadata["bad_output_constraint"] == "less_than_or_equal"
    assert restricted.metadata["bad_output_disposability"] == "strong"
    assert restricted.metadata["null_jointness"] is False
    assert (
        restricted.metadata["environmental_technology"]
        == (manual.metadata["environmental_technology"])
    )


def test_separable_undesirable_sbm_matches_manual_external_appraisal() -> None:
    data = _separable_data()
    eligibility = _by_row([[0], [0]])
    restricted = UndesirableSlacksBasedDEA(peer_eligibility=eligibility).fit(data)
    manual = UndesirableSlacksBasedDEA(
        reference=ReferenceSpec(kind="custom", custom_rows=[0])
    ).fit(data)

    np.testing.assert_allclose(
        restricted.summary()["score"],
        manual.summary()["score"],
    )
    pd.testing.assert_frame_equal(_sorted_targets(restricted), _sorted_targets(manual))
    _assert_semantic_tables_equal(restricted, manual)
    summary = restricted.summary().set_index("dmu_id")
    assessed = summary.loc["Assessed"]
    assert assessed["score"] == pytest.approx(2.0 / 7.0)
    assert not bool(assessed["self_in_reference"])
    assert bool(assessed["is_within_reference_technology"])
    assert assessed["membership_status"] == "certified_by_sbm_balance_account"
    assert summary["base_reference_size"].tolist() == [2, 2]
    assert summary["reference_size"].tolist() == [1, 1]
    assert set(restricted.intensities["reference_dmu_id"]) <= {"Reference"}


def test_separable_undesirable_sbm_fails_closed_outside_effective_technology() -> None:
    data = _separable_data(dominated_second=False)
    result = UndesirableSlacksBasedDEA(peer_eligibility=_by_row([[0], [0]])).fit(data)
    assessed = result.summary().set_index("dmu_id").loc["Assessed"]

    assert not bool(assessed["self_in_reference"])
    assert not bool(assessed["is_within_reference_technology"])
    assert assessed["membership_status"] == "outside_reference_technology"
    assert assessed["score_status"] == "outside_reference_technology"
    assert not bool(assessed["score_valid"])
    assert np.isnan(assessed["score"])


def test_temporal_reference_and_eligibility_use_exact_intersection_and_reuse() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "A", "B"],
                "year": [2020, 2020, 2021, 2021],
                "resource": [1.0, 2.0, 1.0, 2.0],
                "service": [2.0, 1.0, 2.0, 1.0],
                "residual": [1.0, 2.0, 1.0, 2.0],
            }
        ),
        dmu="dmu",
        period="year",
        inputs="resource",
        outputs="service",
        bad_outputs="residual",
    )
    eligibility = _by_row([[0, 2], [0, 2], [0, 2], [0, 2]])
    result = UndesirableSlacksBasedDEA(
        reference="contemporaneous",
        peer_eligibility=eligibility,
    ).fit(data)

    summary = result.summary()
    assert summary["base_reference_size"].tolist() == [2, 2, 2, 2]
    assert summary["reference_size"].tolist() == [1, 1, 1, 1]
    assert summary["self_in_reference"].tolist() == [True, False, True, False]
    assert result.metadata["compiled_reference_sets"] == 2
    assert result.metadata["primary_solver_calls"] == 4
    assert result.metadata["solver_calls"] == 4

    audit = result.metadata["peer_eligibility"]
    assert audit["composition"] == "intersection"
    assert audit["declared_edge_count"] == 8
    assert audit["effective_edge_count"] == 4
    assert audit["base_unique_reference_sets"] == 2
    assert audit["effective_unique_reference_sets"] == 2
    assert audit["self_exclusion_count"] == 2
    assert json.loads(
        json.dumps(result.metadata["expanded_spec"]["reference"]["peer_eligibility"])
    ) == json.loads(json.dumps(audit))
    assert result.metadata["expanded_spec"]["evaluation_protocol"]["kind"] == (
        "mixed_self_and_external_reference_appraisal"
    )

    peers = result.intensities.loc[
        :, ["dmu_id", "period", "reference_dmu_id", "reference_period"]
    ]
    assert (peers["period"] == peers["reference_period"]).all()


def test_keyed_policy_intersects_a_custom_environmental_reference() -> None:
    data = _separable_data()
    eligibility = _by_key(
        {
            "Reference": ["Reference", "Assessed"],
            "Assessed": ["Reference", "Assessed"],
        }
    )
    restricted = UndesirableSlacksBasedDEA(
        reference=ReferenceSpec(kind="custom", custom_rows=[0]),
        peer_eligibility=eligibility,
    ).fit(data)
    manual = UndesirableSlacksBasedDEA(
        reference=ReferenceSpec(kind="custom", custom_rows=[0])
    ).fit(data)

    np.testing.assert_allclose(
        restricted.summary()["score"],
        manual.summary()["score"],
    )
    _assert_semantic_tables_equal(restricted, manual)
    summary = restricted.summary()
    assert summary["base_reference_size"].tolist() == [1, 1]
    assert summary["reference_size"].tolist() == [1, 1]
    audit = restricted.metadata["peer_eligibility"]
    assert audit["mode"] == "key"
    assert audit["declared_edge_count"] == 4
    assert audit["effective_edge_count"] == 2


def test_environmental_ddf_compiles_each_repeated_population_once() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C", "D"],
                "resource": [1.0, 2.0, 1.0, 2.0],
                "service": [2.0, 1.0, 2.0, 1.0],
                "residual": [1.0, 2.0, 1.0, 2.0],
            }
        ),
        dmu="dmu",
        inputs="resource",
        outputs="service",
        bad_outputs="residual",
    )
    result = EnvironmentalDirectionalDistanceDEA(
        disposability="strong",
        null_jointness=False,
        compute_slacks=False,
        peer_eligibility=_by_row([[0, 1], [0, 1], [2, 3], [2, 3]]),
    ).fit(data)

    assert result.metadata["planned_reference_sets"] == 2
    assert result.metadata["compiled_reference_sets"] == 2
    assert result.metadata["phase_one_solver_calls"] == 4
    assert result.metadata["phase_two_solver_calls"] == 0
    assert result.metadata["membership_solver_calls"] == 0
    assert result.metadata["solver_calls"] == 4


def test_environmental_families_share_compact_source_neutral_provenance() -> None:
    data = _cfg_data()
    eligibility = _by_row([[0], [0]])
    results = (
        EnvironmentalDirectionalDistanceDEA(
            disposability="strong",
            null_jointness=False,
            peer_eligibility=eligibility,
        ).fit(data),
        CommonFactorWeakDisposalDDF(
            peer_eligibility=eligibility,
            allow_negative_distance=True,
        ).fit(data),
        ChungFareGrosskopfDDF(peer_eligibility=eligibility).fit(data),
        UndesirableSlacksBasedDEA(peer_eligibility=eligibility).fit(data),
    )

    audits = [result.metadata["peer_eligibility"] for result in results]
    assert all(audit == audits[0] for audit in audits[1:])
    audit = audits[0]
    assert audit["categorical_interpretation"] == "not_claimed"
    assert audit["provenance"] == _provenance().metadata()
    assert "rows_by_observation" not in audit
    assert "eligible_by_observation" not in audit


def test_empty_environmental_intersection_is_rejected_before_fitting() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "A", "B"],
                "year": [2020, 2020, 2021, 2021],
                "resource": [1.0, 2.0, 1.0, 2.0],
                "service": [2.0, 1.0, 2.0, 1.0],
                "residual": [1.0, 2.0, 1.0, 2.0],
            }
        ),
        dmu="dmu",
        period="year",
        inputs="resource",
        outputs="service",
        bad_outputs="residual",
    )
    eligibility = _by_row([[2], [2], [0], [0]])

    with pytest.raises(ModelSpecificationError, match="empty intersection"):
        UndesirableSlacksBasedDEA(
            reference="contemporaneous",
            peer_eligibility=eligibility,
        ).fit(data)


def test_reference_frequency_remains_fail_closed_for_environmental_results() -> None:
    eligibility = _by_row([[0], [0]])
    results = (
        ChungFareGrosskopfDDF(peer_eligibility=eligibility).fit(_cfg_data()),
        UndesirableSlacksBasedDEA(peer_eligibility=eligibility).fit(_cfg_data()),
    )

    for result in results:
        with pytest.raises(ModelSpecificationError):
            result.reference_frequency()


@pytest.mark.parametrize(
    "constructor",
    [
        ActivitySpecificWeakDisposalDDF,
        ByProductionDirectionalDistanceDEA,
        ByProductionFareGrosskopfLovellDEA,
        MaterialBalanceDEA,
        ToneNonSeparableSBM,
        ZhouAngWangNonCHPEnergyCarbonDEA,
    ],
)
def test_specialist_environmental_routes_do_not_accept_peer_eligibility(
    constructor: type[object],
) -> None:
    assert "peer_eligibility" not in inspect.signature(constructor).parameters
