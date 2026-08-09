from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime
from fractions import Fraction

import numpy as np
import pandas as pd
import pytest

from deapack import DEAData
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.technology.peer_eligibility import (
    PeerEligibility,
    PeerEligibilityProvenance,
    resolve_peer_eligibility,
)


def _provenance(**overrides: str) -> PeerEligibilityProvenance:
    values = {
        "rule_name": "shared service mandate",
        "source": "approved study protocol v1",
        "comparison_population": "district hospitals",
        "decision_owner": "study steering committee",
        "validity_period": "2020-2024",
        **overrides,
    }
    return PeerEligibilityProvenance(**values)


def _cross_section(order: tuple[str, ...] = ("A", "B", "C")) -> DEAData:
    values = {
        "A": (1.0, 1.0),
        "B": (2.0, 1.5),
        "C": (3.0, 1.2),
    }
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "unit": list(order),
                "x": [values[unit][0] for unit in order],
                "y": [values[unit][1] for unit in order],
            }
        ),
        dmu="unit",
        inputs="x",
        outputs="y",
    )


def _panel() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "unit": ["A", "B", "A", "B"],
                "year": [2020, 2020, 2021, 2021],
                "x": [1.0, 2.0, 1.5, 2.5],
                "y": [1.0, 1.0, 1.2, 1.3],
            }
        ),
        dmu="unit",
        period="year",
        inputs="x",
        outputs="y",
    )


def _key_rule() -> PeerEligibility:
    return PeerEligibility.by_key(
        {
            "A": ("B", "A"),
            "B": ("A", "B"),
            "C": ("C",),
        },
        provenance=_provenance(),
    )


def test_direct_construction_is_rejected_in_favor_of_validated_factories() -> None:
    with pytest.raises(TypeError, match=r"cannot be constructed directly.*by_key"):
        PeerEligibility()


def test_provenance_is_trimmed_frozen_and_detached() -> None:
    provenance = _provenance(rule_name="  institutional mandate  ")

    assert provenance.rule_name == "institutional mandate"
    with pytest.raises(FrozenInstanceError):
        provenance.rule_name = "changed"  # type: ignore[misc]

    metadata = provenance.metadata()
    metadata["rule_name"] = "caller mutation"
    assert provenance.metadata()["rule_name"] == "institutional mandate"


@pytest.mark.parametrize(
    "field_name",
    (
        "rule_name",
        "source",
        "comparison_population",
        "decision_owner",
        "validity_period",
    ),
)
def test_provenance_requires_nonempty_text(field_name: str) -> None:
    with pytest.raises(ValueError, match=field_name):
        _provenance(**{field_name: "  "})


def test_by_row_copies_normalizes_and_content_interns_candidate_sets() -> None:
    supplied = [[1, 0], [0, 1], [2]]
    eligibility = PeerEligibility.by_row(supplied, provenance=_provenance())
    supplied[0][:] = [2]

    resolved = resolve_peer_eligibility(_cross_section(), eligibility)

    assert [rows.tolist() for rows in resolved.rows_by_observation] == [
        [0, 1],
        [0, 1],
        [2],
    ]
    assert resolved.rows_by_observation[0] is resolved.rows_by_observation[1]
    assert resolved.unique_eligibility_sets == 2
    assert resolved.set_id_by_observation.tolist() == [0, 0, 1]
    assert resolved.declared_size_by_observation.tolist() == [2, 2, 1]
    assert resolved.declared_edge_count == 5


def test_resolved_arrays_are_backed_by_immutable_bytes() -> None:
    resolved = resolve_peer_eligibility(_cross_section(), _key_rule())

    for values in (
        *resolved.rows_by_observation,
        *resolved.unique_rows,
        resolved.set_id_by_observation,
        resolved.declared_size_by_observation,
    ):
        assert values.dtype == np.dtype("<i8")
        assert not values.flags.writeable
        with pytest.raises(ValueError, match="WRITEABLE"):
            values.setflags(write=True)


@pytest.mark.parametrize(
    ("rows", "error", "message"),
    [
        ([], ValueError, "cannot be empty"),
        ([[0], []], ValueError, "cannot be empty"),
        ([[True]], TypeError, "integer row positions"),
        ([[0.0]], TypeError, "integer row positions"),
        ([[-1]], ValueError, "negative"),
        ([[2**63]], ValueError, "signed int64"),
        ([[0, 0]], ValueError, "duplicate"),
        ("rows", TypeError, "sequence of row sequences"),
    ],
)
def test_by_row_rejects_ambiguous_declarations(
    rows: object,
    error: type[Exception],
    message: str,
) -> None:
    with pytest.raises(error, match=message):
        PeerEligibility.by_row(rows, provenance=_provenance())  # type: ignore[arg-type]


def test_row_resolution_checks_outer_count_and_candidate_range() -> None:
    data = _cross_section()
    wrong_count = PeerEligibility.by_row([[0], [1]], provenance=_provenance())
    outside = PeerEligibility.by_row([[0], [1], [3]], provenance=_provenance())

    with pytest.raises(ModelSpecificationError, match="one candidate set"):
        resolve_peer_eligibility(data, wrong_count)
    with pytest.raises(ModelSpecificationError, match="outside DEAData"):
        resolve_peer_eligibility(data, outside)


def test_by_key_is_order_insensitive_and_resolves_in_data_order() -> None:
    first = _key_rule()
    second = PeerEligibility.by_key(
        {
            "C": ("C",),
            "B": ("B", "A"),
            "A": ("A", "B"),
        },
        provenance=_provenance(),
    )

    first_resolved = resolve_peer_eligibility(_cross_section(), first)
    second_resolved = resolve_peer_eligibility(_cross_section(), second)

    assert first.declared_fingerprint == second.declared_fingerprint
    assert [rows.tolist() for rows in first_resolved.rows_by_observation] == [
        [0, 1],
        [0, 1],
        [2],
    ]
    assert [rows.tolist() for rows in second_resolved.rows_by_observation] == [
        [0, 1],
        [0, 1],
        [2],
    ]


@pytest.mark.parametrize(
    ("mapping", "error", "message"),
    [
        ([], TypeError, "must be a mapping"),
        ({}, ValueError, "cannot be empty"),
        ({"A": "A"}, TypeError, "sequence of observation keys"),
        ({"A": ()}, ValueError, "cannot be empty"),
        ({"A": ("A", "A")}, ValueError, "duplicate"),
        ({"A": (None,)}, DataValidationError, "cannot be missing"),
        ({"A": (["A"],)}, DataValidationError, "hashable"),
    ],
)
def test_by_key_rejects_ambiguous_declarations(
    mapping: object,
    error: type[Exception],
    message: str,
) -> None:
    with pytest.raises(error, match=message):
        PeerEligibility.by_key(mapping, provenance=_provenance())  # type: ignore[arg-type]


def test_by_key_rejects_nonportable_custom_identifier() -> None:
    class Identifier:
        pass

    with pytest.raises(DataValidationError, match="portable scalar"):
        PeerEligibility.by_key(
            {"A": (Identifier(),)},
            provenance=_provenance(),
        )


@pytest.mark.parametrize(
    "key",
    (
        Fraction(1, 10),
        np.datetime64("2020-01-01T00:00:00.000000000", "ns"),
    ),
)
def test_by_key_rejects_scalar_coercions_that_can_alias_distinct_keys(
    key: object,
) -> None:
    with pytest.raises(DataValidationError, match=r"portable scalar"):
        PeerEligibility.by_key(
            {key: (key,)},  # type: ignore[dict-item]
            provenance=_provenance(),
        )


def test_by_key_rejects_datetime_subclasses_with_overridable_encoding() -> None:
    class ApplicationDatetime(datetime):
        pass

    key = ApplicationDatetime(2020, 1, 1)
    with pytest.raises(DataValidationError, match=r"portable scalar"):
        PeerEligibility.by_key(
            {key: (key,)},
            provenance=_provenance(),
        )


def test_panel_key_tokens_do_not_coerce_period_numeric_types() -> None:
    eligibility = PeerEligibility.by_key(
        {
            ("A", 2020.0): (("A", 2020.0),),
            ("B", 2020.0): (("B", 2020.0),),
            ("A", 2021.0): (("A", 2021.0),),
            ("B", 2021.0): (("B", 2021.0),),
        },
        provenance=_provenance(),
    )

    with pytest.raises(ModelSpecificationError, match=r"exactly match"):
        resolve_peer_eligibility(_panel(), eligibility)


def test_key_resolution_requires_exact_evaluatee_and_candidate_keys() -> None:
    data = _cross_section()
    missing_evaluatee = PeerEligibility.by_key(
        {"A": ("A",), "B": ("B",)},
        provenance=_provenance(),
    )
    unknown_candidate = PeerEligibility.by_key(
        {"A": ("A",), "B": ("B",), "C": ("unknown",)},
        provenance=_provenance(),
    )

    with pytest.raises(ModelSpecificationError, match="exactly match"):
        resolve_peer_eligibility(data, missing_evaluatee)
    with pytest.raises(ModelSpecificationError, match="outside DEAData"):
        resolve_peer_eligibility(data, unknown_candidate)


def test_panel_key_schema_requires_exact_dmu_period_pairs() -> None:
    data = _panel()
    exact = PeerEligibility.by_key(
        {
            ("A", 2020): (("A", 2020), ("B", 2020)),
            ("B", 2020): (("A", 2020), ("B", 2020)),
            ("A", 2021): (("A", 2021),),
            ("B", 2021): (("B", 2021),),
        },
        provenance=_provenance(),
    )
    dmu_only = PeerEligibility.by_key(
        {"A": ("A",), "B": ("B",)},
        provenance=_provenance(),
    )

    resolved = resolve_peer_eligibility(data, exact)

    assert resolved.key_schema == ("dmu_id", "period")
    assert [rows.tolist() for rows in resolved.rows_by_observation] == [
        [0, 1],
        [0, 1],
        [2],
        [3],
    ]
    with pytest.raises(ModelSpecificationError, match="expected_schema"):
        resolve_peer_eligibility(data, dmu_only)


def test_keyed_relation_fingerprint_is_data_permutation_invariant() -> None:
    eligibility = _key_rule()
    first_data = _cross_section(("A", "B", "C"))
    second_data = _cross_section(("C", "A", "B"))
    first = resolve_peer_eligibility(first_data, eligibility)
    second = resolve_peer_eligibility(second_data, eligibility)

    first_fingerprint = first.relation_fingerprint(
        first_data,
        first.rows_by_observation,
        domain="declared candidate relation",
    )
    second_fingerprint = second.relation_fingerprint(
        second_data,
        second.rows_by_observation,
        domain="declared candidate relation",
    )

    assert first_fingerprint == second_fingerprint
    assert first_fingerprint != first.relation_fingerprint(
        first_data,
        first.rows_by_observation,
        domain="effective reference relation",
    )


def test_positional_relation_fingerprint_binds_ordered_roster() -> None:
    eligibility = PeerEligibility.by_row(
        [[0, 1], [0, 1], [2]],
        provenance=_provenance(),
    )
    first_data = _cross_section(("A", "B", "C"))
    second_data = _cross_section(("C", "A", "B"))
    first = resolve_peer_eligibility(first_data, eligibility)
    second = resolve_peer_eligibility(second_data, eligibility)

    assert first.relation_fingerprint(
        first_data,
        first.rows_by_observation,
        domain="declared candidate relation",
    ) != second.relation_fingerprint(
        second_data,
        second.rows_by_observation,
        domain="declared candidate relation",
    )


def test_relation_fingerprint_rejects_malformed_external_rows() -> None:
    data = _cross_section()
    resolved = resolve_peer_eligibility(data, _key_rule())

    with pytest.raises(ModelSpecificationError, match="one reference set"):
        resolved.relation_fingerprint(
            data,
            resolved.rows_by_observation[:2],
            domain="effective",
        )
    malformed = (
        np.asarray([], dtype=np.int64),
        *resolved.rows_by_observation[1:],
    )
    with pytest.raises(ModelSpecificationError, match="cannot be empty"):
        resolved.relation_fingerprint(data, malformed, domain="effective")
    with pytest.raises(ValueError, match="domain"):
        resolved.relation_fingerprint(
            data,
            resolved.rows_by_observation,
            domain=" ",
        )


def test_fingerprint_binds_provenance_and_key_mode() -> None:
    keyed = _key_rule()
    changed_provenance = PeerEligibility.by_key(
        {"A": ("A", "B"), "B": ("A", "B"), "C": ("C",)},
        provenance=_provenance(source="approved study protocol v2"),
    )
    positional = PeerEligibility.by_row(
        [[0, 1], [0, 1], [2]],
        provenance=_provenance(),
    )

    assert keyed.declared_fingerprint != changed_provenance.declared_fingerprint
    assert keyed.declared_fingerprint != positional.declared_fingerprint
    assert len(keyed.declared_fingerprint) == 64


def test_metadata_is_compact_json_safe_and_detached() -> None:
    resolved = resolve_peer_eligibility(_cross_section(), _key_rule())

    metadata = resolved.metadata()

    assert metadata == {
        "schema": "deapack.peer-eligibility.v1",
        "scope": "by_observation",
        "mode": "key",
        "key_schema": ["dmu_id"],
        "observation_count": 3,
        "declared_edge_count": 5,
        "unique_declared_sets": 2,
        "declared_fingerprint": resolved.declared_fingerprint,
        "provenance": _provenance().metadata(),
    }
    metadata["provenance"]["rule_name"] = "caller mutation"
    assert resolved.metadata()["provenance"]["rule_name"] == "shared service mandate"


def test_audit_frame_discloses_every_declared_candidate_edge() -> None:
    data = _cross_section()
    eligibility = _key_rule()

    audit = eligibility.audit_frame(data)

    assert list(audit.columns) == [
        "observation_row",
        "dmu_id",
        "period",
        "reference_row",
        "reference_dmu_id",
        "reference_period",
        "self_reference",
        "selection",
        "rule_name",
        "declared_fingerprint",
    ]
    assert len(audit) == 5
    assert audit["period"].isna().all()
    assert audit["reference_period"].isna().all()
    assert audit["self_reference"].sum() == 3
    assert set(audit["selection"]) == {"declared_eligible_reference_candidate"}
    assert set(audit["declared_fingerprint"]) == {eligibility.declared_fingerprint}


def test_resolution_requires_peer_eligibility_instance() -> None:
    with pytest.raises(TypeError, match="PeerEligibility"):
        resolve_peer_eligibility(_cross_section(), object())  # type: ignore[arg-type]
