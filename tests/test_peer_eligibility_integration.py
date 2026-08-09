from __future__ import annotations

import json
from collections.abc import Callable, Sequence

import numpy as np
import pandas as pd
import pytest

from deapack import (
    BCC,
    CCR,
    BCCInput,
    BCCOutput,
    CCRInput,
    CCROutput,
    DEAData,
    PeerEligibility,
    PeerEligibilityProvenance,
    RadialDEA,
    ReferenceSpec,
)
from deapack.exceptions import ModelSpecificationError
from deapack.models import radial as radial_module
from deapack.technology import build_reference_plan
from deapack.technology.peer_eligibility import resolve_peer_eligibility


def _provenance() -> PeerEligibilityProvenance:
    return PeerEligibilityProvenance(
        rule_name="declared institutional comparability",
        source="approved study-design ledger v1",
        comparison_population="eligible service organizations",
        decision_owner="study steering committee",
        validity_period="2020-2024",
    )


def _cross_section(
    order: Sequence[str] = ("A", "B", "C", "D"),
) -> DEAData:
    inputs = {"A": 1.0, "B": 2.0, "C": 3.0, "D": 4.0}
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "unit": list(order),
                "input": [inputs[unit] for unit in order],
                "output": [1.0] * len(order),
            }
        ),
        dmu="unit",
        inputs="input",
        outputs="output",
    )


def _panel(order: Sequence[int] = tuple(range(6))) -> DEAData:
    rows = (
        ("A", 2020, 1.0),
        ("B", 2020, 2.0),
        ("A", 2021, 1.5),
        ("B", 2021, 3.0),
        ("A", 2024, 2.0),
        ("B", 2024, 4.0),
    )
    selected = [rows[position] for position in order]
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "unit": [row[0] for row in selected],
                "year": [row[1] for row in selected],
                "input": [row[2] for row in selected],
                "output": [1.0] * 6,
            }
        ),
        dmu="unit",
        period="year",
        inputs="input",
        outputs="output",
    )


def _same_unit_panel_eligibility() -> PeerEligibility:
    return PeerEligibility.by_row(
        [
            [0, 2, 4],
            [1, 3, 5],
            [0, 2, 4],
            [1, 3, 5],
            [0, 2, 4],
            [1, 3, 5],
        ],
        provenance=_provenance(),
    )


def _keyed_cross_section_eligibility() -> PeerEligibility:
    return PeerEligibility.by_key(
        {
            "A": ("A", "B"),
            "B": ("A",),
            "C": ("A", "C"),
            "D": ("B", "D"),
        },
        provenance=_provenance(),
    )


def _rows(plan: object) -> list[list[int]]:
    return [rows.tolist() for rows in plan.rows_by_observation]  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("reference", "expected_rows", "base_sizes"),
    [
        (
            ReferenceSpec("global"),
            [
                [0, 2, 4],
                [1, 3, 5],
                [0, 2, 4],
                [1, 3, 5],
                [0, 2, 4],
                [1, 3, 5],
            ],
            [6, 6, 6, 6, 6, 6],
        ),
        (
            ReferenceSpec("custom", custom_rows=(0, 1, 2, 3)),
            [[0, 2], [1, 3], [0, 2], [1, 3], [0, 2], [1, 3]],
            [4, 4, 4, 4, 4, 4],
        ),
        (
            ReferenceSpec("contemporaneous"),
            [[0], [1], [2], [3], [4], [5]],
            [2, 2, 2, 2, 2, 2],
        ),
        (
            ReferenceSpec("sequential"),
            [[0], [1], [0, 2], [1, 3], [0, 2, 4], [1, 3, 5]],
            [2, 2, 4, 4, 6, 6],
        ),
        (
            ReferenceSpec("window", window_before=1, window_after=0),
            [[0], [1], [0, 2], [1, 3], [2, 4], [3, 5]],
            [2, 2, 4, 4, 4, 4],
        ),
    ],
    ids=("global", "custom", "contemporaneous", "sequential", "window"),
)
def test_reference_policy_and_peer_eligibility_use_exact_intersection(
    reference: ReferenceSpec,
    expected_rows: list[list[int]],
    base_sizes: list[int],
) -> None:
    data = _panel()
    eligibility = _same_unit_panel_eligibility()

    plan = build_reference_plan(
        data,
        reference,
        peer_eligibility=eligibility,
    )
    result = BCC(
        reference=reference,
        peer_eligibility=eligibility,
        compute_slacks=False,
    ).fit(data)

    assert _rows(plan) == expected_rows
    assert result.summary()["reference_size"].tolist() == [
        len(rows) for rows in expected_rows
    ]
    assert result.summary()["base_reference_size"].tolist() == base_sizes
    assert result.summary()["score_valid"].all()
    assert result.metadata["compiled_reference_sets"] == plan.unique_reference_sets
    assert result.metadata["peer_eligibility"]["composition"] == "intersection"


def test_custom_reference_membership_order_has_one_plan_and_fingerprint() -> None:
    data = _cross_section(("A", "B", "C"))
    eligibility = PeerEligibility.by_row(
        [[0, 1], [0, 1], [0, 1]],
        provenance=_provenance(),
    )
    ordered_spec = ReferenceSpec("custom", custom_rows=(0, 1))
    reversed_spec = ReferenceSpec("custom", custom_rows=(1, 0))

    assert ordered_spec == reversed_spec
    assert reversed_spec.custom_rows == (0, 1)

    ordered_plan = build_reference_plan(
        data,
        ordered_spec,
        peer_eligibility=eligibility,
    )
    reversed_plan = build_reference_plan(
        data,
        reversed_spec,
        peer_eligibility=eligibility,
    )
    assert _rows(ordered_plan) == _rows(reversed_plan) == [[0, 1]] * 3
    assert (
        ordered_plan.eligibility_audit.effective_fingerprint
        == reversed_plan.eligibility_audit.effective_fingerprint
    )


def test_custom_reference_rejects_positions_outside_int64() -> None:
    with pytest.raises(ValueError, match=r"signed int64"):
        ReferenceSpec("custom", custom_rows=(2**63,))


def test_empty_effective_intersection_fails_before_any_fit_result() -> None:
    data = _panel()
    eligibility = PeerEligibility.by_row(
        [[2], [1], [2], [3], [4], [5]],
        provenance=_provenance(),
    )

    with pytest.raises(ModelSpecificationError, match=r"empty intersection.*row 0"):
        BCC(
            reference="contemporaneous",
            peer_eligibility=eligibility,
            compute_slacks=False,
        ).fit(data)


def test_singleton_self_only_and_self_excluded_sets_are_not_repaired() -> None:
    data = _cross_section(("A", "B", "C"))
    eligibility = PeerEligibility.by_key(
        {
            "A": ("B",),
            "B": ("A",),
            "C": ("C",),
        },
        provenance=_provenance(),
    )

    result = BCC(peer_eligibility=eligibility, compute_slacks=False).fit(data)
    summary = result.summary().set_index("dmu_id")

    assert summary["reference_size"].tolist() == [1, 1, 1]
    assert summary["base_reference_size"].tolist() == [3, 3, 3]
    assert summary["self_in_reference"].tolist() == [False, False, True]
    assert summary["score"].to_dict() == {"A": 2.0, "B": 0.5, "C": 1.0}
    assert not bool(summary.loc["A", "is_within_reference_technology"])
    assert bool(summary.loc["B", "is_within_reference_technology"])
    assert result.metadata["peer_eligibility"]["singleton_reference_count"] == 3
    assert result.metadata["peer_eligibility"]["self_exclusion_count"] == 2
    assert set(result.peers("A")["reference_dmu_id"]) == {"B"}
    assert set(result.peers("B")["reference_dmu_id"]) == {"A"}
    assert set(result.peers("C")["reference_dmu_id"]) == {"C"}


def test_equal_effective_populations_compile_once_and_bound_every_active_peer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = _cross_section()
    eligibility = PeerEligibility.by_key(
        {
            "A": ("A", "B"),
            "B": ("A", "B"),
            "C": ("C", "D"),
            "D": ("C", "D"),
        },
        provenance=_provenance(),
    )
    compile_calls: list[tuple[int, ...]] = []
    original = radial_module.compile_reference

    def counted_compile(data: DEAData, rows: np.ndarray):
        compile_calls.append(tuple(int(row) for row in rows))
        return original(data, rows)

    monkeypatch.setattr(radial_module, "compile_reference", counted_compile)

    result = BCC(peer_eligibility=eligibility, compute_slacks=False).fit(data)

    assert compile_calls == [(0, 1), (2, 3)]
    assert result.metadata["compiled_reference_sets"] == 2
    assert result.metadata["phase_one_template_compilations"] == 2
    assert result.metadata["phase_one_task_bindings"] == data.n_dmus
    assert result.metadata["phase_one_solver_calls"] == data.n_dmus
    allowed = {
        "A": {"A", "B"},
        "B": {"A", "B"},
        "C": {"C", "D"},
        "D": {"C", "D"},
    }
    for row in result.intensities.itertuples(index=False):
        assert row.reference_dmu_id in allowed[row.dmu_id]


def test_observation_specific_fit_matches_independent_custom_reference_fits() -> None:
    data = _cross_section()
    rows_by_dmu = {
        "A": (0, 1),
        "B": (0,),
        "C": (0, 2),
        "D": (1, 3),
    }
    eligibility = _keyed_cross_section_eligibility()

    joint = BCC(peer_eligibility=eligibility, compute_slacks=False).fit(data)
    joint_scores = joint.summary().set_index("dmu_id")["score"]
    independent_scores: dict[str, float] = {}
    for dmu_id, rows in rows_by_dmu.items():
        independent = BCC(
            reference=ReferenceSpec("custom", custom_rows=rows),
            compute_slacks=False,
        ).fit(data)
        independent_scores[dmu_id] = float(
            independent.summary().set_index("dmu_id").loc[dmu_id, "score"]
        )

    np.testing.assert_allclose(
        joint_scores.loc[list(rows_by_dmu)].to_numpy(dtype=np.float64),
        np.asarray([independent_scores[dmu] for dmu in rows_by_dmu]),
        rtol=0.0,
        atol=1e-12,
    )


def test_public_radial_and_bcc_parameters_preserve_compact_registry_provenance() -> (
    None
):
    data = _cross_section()
    eligibility = _keyed_cross_section_eligibility()

    radial = RadialDEA(
        orientation="input",
        returns_to_scale="vrs",
        peer_eligibility=eligibility,
        compute_slacks=False,
    ).fit(data)
    preset = BCC(peer_eligibility=eligibility, compute_slacks=False).fit(data)

    np.testing.assert_allclose(
        radial.summary()["score"],
        preset.summary()["score"],
        rtol=0.0,
        atol=1e-12,
    )
    metadata = preset.metadata["peer_eligibility"]
    expanded = preset.metadata["expanded_spec"]["reference"]["peer_eligibility"]
    assert json.loads(json.dumps(metadata)) == json.loads(json.dumps(expanded))
    assert metadata["schema"] == "deapack.peer-eligibility-plan.v1"
    assert metadata["mode"] == "key"
    assert metadata["key_schema"] == ["dmu_id"]
    assert metadata["categorical_interpretation"] == "not_claimed"
    assert metadata["provenance"] == _provenance().metadata()
    assert len(metadata["declared_fingerprint"]) == 64
    assert len(metadata["effective_fingerprint"]) == 64
    assert preset.metadata["method_id"] == "static.radial"
    assert "banker" not in json.dumps(preset.metadata).lower()
    serialized = json.dumps(metadata)
    assert "rows_by_observation" not in serialized
    assert "reference_dmu_id" not in serialized
    assert preset.summary()["reference_size"].tolist() == [2, 1, 2, 2]
    assert preset.summary()["base_reference_size"].tolist() == [4, 4, 4, 4]


def test_public_ccr_parameter_matches_equivalent_radial_crs_fit() -> None:
    data = _cross_section()
    eligibility = _keyed_cross_section_eligibility()

    radial = RadialDEA(
        orientation="input",
        returns_to_scale="crs",
        peer_eligibility=eligibility,
        compute_slacks=False,
    ).fit(data)
    specialization = CCR(
        orientation="input",
        peer_eligibility=eligibility,
        compute_slacks=False,
    ).fit(data)

    pd.testing.assert_series_equal(
        radial.summary()["score"],
        specialization.summary()["score"],
    )
    assert specialization.metadata["method_id"] == "static.radial"
    assert specialization.metadata["specialization_id"] == "static.radial.crs"
    assert (
        specialization.metadata["peer_eligibility"]
        == radial.metadata["peer_eligibility"]
    )


@pytest.mark.parametrize(
    ("constructor", "equivalent"),
    (
        (
            CCRInput,
            lambda policy: CCR(
                orientation="input",
                peer_eligibility=policy,
            ),
        ),
        (
            CCROutput,
            lambda policy: CCR(
                orientation="output",
                peer_eligibility=policy,
            ),
        ),
        (
            BCCInput,
            lambda policy: BCC(
                orientation="input",
                peer_eligibility=policy,
            ),
        ),
        (
            BCCOutput,
            lambda policy: BCC(
                orientation="output",
                peer_eligibility=policy,
            ),
        ),
    ),
)
def test_fixed_orientation_recipes_support_peer_eligibility_and_match_specialization(
    constructor: type[RadialDEA],
    equivalent: Callable[[PeerEligibility], RadialDEA],
) -> None:
    data = _cross_section()
    eligibility = _keyed_cross_section_eligibility()

    fixed = constructor(peer_eligibility=eligibility).fit(data)
    specialized = equivalent(eligibility).fit(data)

    pd.testing.assert_frame_equal(fixed.summary(), specialized.summary())
    pd.testing.assert_frame_equal(fixed.slacks, specialized.slacks)
    pd.testing.assert_frame_equal(fixed.targets, specialized.targets)
    pd.testing.assert_frame_equal(fixed.intensities, specialized.intensities)
    pd.testing.assert_frame_equal(fixed.duals, specialized.duals)
    assert (
        fixed.metadata["peer_eligibility"] == (specialized.metadata["peer_eligibility"])
    )
    assert json.loads(
        json.dumps(fixed.metadata["expanded_spec"]["reference"]["peer_eligibility"])
    ) == json.loads(json.dumps(fixed.metadata["peer_eligibility"]))


def test_model_constructor_rejects_noneligibility_objects() -> None:
    with pytest.raises(TypeError, match=r"peer_eligibility.*PeerEligibility"):
        BCC(peer_eligibility=object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match=r"peer_eligibility.*PeerEligibility"):
        RadialDEA(peer_eligibility=object())  # type: ignore[arg-type]


def test_all_candidate_key_rule_preserves_legacy_scores_and_selected_peers() -> None:
    data = _cross_section()
    all_ids = tuple(data.dmu_ids.tolist())
    eligibility = PeerEligibility.by_key(
        {dmu_id: all_ids for dmu_id in all_ids},
        provenance=_provenance(),
    )

    baseline = BCC(compute_slacks=False).fit(data)
    restricted = BCC(
        peer_eligibility=eligibility,
        compute_slacks=False,
    ).fit(data)

    pd.testing.assert_series_equal(
        baseline.summary()["score"],
        restricted.summary()["score"],
    )
    pd.testing.assert_frame_equal(baseline.intensities, restricted.intensities)
    assert "peer_eligibility" not in baseline.metadata
    assert "peer_eligibility" in restricted.metadata


def test_keyed_fit_and_fingerprints_are_invariant_to_data_row_permutation() -> None:
    eligibility = _keyed_cross_section_eligibility()
    first = BCC(peer_eligibility=eligibility, compute_slacks=False).fit(
        _cross_section(("A", "B", "C", "D"))
    )
    second = BCC(peer_eligibility=eligibility, compute_slacks=False).fit(
        _cross_section(("D", "B", "A", "C"))
    )

    first_scores = first.summary().set_index("dmu_id")["score"].sort_index()
    second_scores = second.summary().set_index("dmu_id")["score"].sort_index()

    pd.testing.assert_series_equal(first_scores, second_scores)
    for field in ("declared_fingerprint", "effective_fingerprint"):
        assert (
            first.metadata["peer_eligibility"][field]
            == second.metadata["peer_eligibility"][field]
        )


def test_panel_keyed_fingerprints_are_permutation_invariant() -> None:
    keys = (
        ("A", 2020),
        ("B", 2020),
        ("A", 2021),
        ("B", 2021),
        ("A", 2024),
        ("B", 2024),
    )
    eligibility = PeerEligibility.by_key(
        {
            evaluatee: tuple(key for key in keys if key[0] == evaluatee[0])
            for evaluatee in keys
        },
        provenance=_provenance(),
    )
    first_data = _panel()
    second_data = _panel((5, 2, 0, 4, 1, 3))
    first_resolved = resolve_peer_eligibility(first_data, eligibility)
    second_resolved = resolve_peer_eligibility(second_data, eligibility)

    first_relation = first_resolved.relation_fingerprint(
        first_data,
        first_resolved.rows_by_observation,
        domain="declared panel relation",
    )
    second_relation = second_resolved.relation_fingerprint(
        second_data,
        second_resolved.rows_by_observation,
        domain="declared panel relation",
    )
    first_plan = build_reference_plan(
        first_data,
        ReferenceSpec("sequential"),
        peer_eligibility=eligibility,
    )
    second_plan = build_reference_plan(
        second_data,
        ReferenceSpec("sequential"),
        peer_eligibility=eligibility,
    )

    assert first_relation == second_relation
    assert first_plan.eligibility_audit is not None
    assert second_plan.eligibility_audit is not None
    assert (
        first_plan.eligibility_audit.effective_fingerprint
        == second_plan.eligibility_audit.effective_fingerprint
    )


def test_positional_effective_fingerprint_binds_data_row_order() -> None:
    eligibility = PeerEligibility.by_row(
        [[0, 1], [0], [0, 2], [1, 3]],
        provenance=_provenance(),
    )
    first = BCC(peer_eligibility=eligibility, compute_slacks=False).fit(
        _cross_section(("A", "B", "C", "D"))
    )
    second = BCC(peer_eligibility=eligibility, compute_slacks=False).fit(
        _cross_section(("D", "B", "A", "C"))
    )

    first_metadata = first.metadata["peer_eligibility"]
    second_metadata = second.metadata["peer_eligibility"]
    assert (
        first_metadata["declared_fingerprint"]
        == second_metadata["declared_fingerprint"]
    )
    assert (
        first_metadata["effective_fingerprint"]
        != second_metadata["effective_fingerprint"]
    )


def test_reference_frequency_fails_closed_for_observation_specific_population() -> None:
    result = BCC(
        reference="global",
        peer_eligibility=_keyed_cross_section_eligibility(),
        compute_slacks=False,
    ).fit(_cross_section())

    with pytest.raises(
        ModelSpecificationError,
        match=(
            r"eligibility-conditioned fitted results has not been independently "
            r"audited"
        ),
    ):
        result.reference_frequency()
