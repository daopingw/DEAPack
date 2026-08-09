"""Keep M13 environmental comparison rights public, bounded, and auditable."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
METHODS = ROOT / "specs" / "registry" / "methods" / "environmental"
AUTHORIZED = (
    "environmental.ddf.joint_production",
    "environmental.ddf.weak_disposal.common_factor",
    "environmental.ddf.output.chung_fare_grosskopf_1997",
    "environmental.sbm.separable_strong",
)


@pytest.mark.parametrize("method_id", AUTHORIZED)
def test_authorized_environmental_records_publish_the_same_policy_contract(
    method_id: str,
) -> None:
    record = json.loads((METHODS / f"{method_id}.json").read_text(encoding="utf-8"))
    reference = record["composition"]["reference"]

    assert reference["defaults"]["peer_eligibility"] == {
        "kind": "none",
        "composition_when_supplied": "intersection_with_base_reference_policy",
        "categorical_interpretation": "not_claimed",
    }
    assert "peer_eligibility" in reference["exposed"]
    assert (
        "observation_specific_peer_eligibility_intersection"
        in record["implementation"]["backend_capabilities"]
    )
    assert (
        "content_deduplicated_reference_compilation"
        in record["implementation"]["backend_capabilities"]
    )
    assert {
        "base_reference_size",
        "reference_size",
        "self_in_reference",
        "peer_eligibility_provenance_when_supplied",
    } <= set(record["result_contract"]["components"])
    assert (
        "tests/test_m13_environmental_peer_eligibility.py"
        in record["validation"]["tests"]["locators"]
    )


def test_docs_name_authorized_routes_and_preserve_exclusions() -> None:
    reference_sets = (ROOT / "docs" / "user-guide" / "reference-sets.md").read_text(
        encoding="utf-8"
    )
    directional = (ROOT / "docs" / "models" / "environmental-directional.md").read_text(
        encoding="utf-8"
    )
    undesirable_sbm = (ROOT / "docs" / "models" / "undesirable-sbm.md").read_text(
        encoding="utf-8"
    )

    for constructor in (
        "EnvironmentalDirectionalDistanceDEA",
        "CommonFactorWeakDisposalDDF",
        "ChungFareGrosskopfDDF",
        "UndesirableSlacksBasedDEA",
    ):
        assert constructor in reference_sets
    for excluded in (
        "activity-specific weak disposal",
        "by-production",
        "material-balance",
        "non-separable SBM",
        "Zhou--Ang--Wang",
        "environmental productivity",
    ):
        assert excluded in reference_sets
    assert (
        "The restriction changes evidence, not the production account." in directional
    )
    assert "The non-separable hybrid is not included in this extension." in " ".join(
        undesirable_sbm.split()
    )


def test_handbook_keeps_comparison_rights_as_management_evidence() -> None:
    ddf = (
        ROOT
        / "book"
        / "chapters"
        / "03-environmental"
        / "06-undesirable-outputs-ddf.md"
    ).read_text(encoding="utf-8")
    sbm = (
        ROOT / "book" / "chapters" / "03-environmental" / "07-undesirable-output-sbm.md"
    ).read_text(encoding="utf-8")

    assert "admissible management evidence, not a new\npollution technology" in ddf
    assert "does not make a negative external CFG distance disappear" in ddf
    assert "restriction changes the evidence available to the plant" in sbm
    assert "unconditional environmental ranking" in sbm
