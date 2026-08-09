from dataclasses import FrozenInstanceError
from pathlib import Path

import numpy as np
import pytest

import deapack.datasets as datasets_module
from deapack import (
    BCCInput,
    DatasetProvenance,
    DatasetVariableInfo,
    DEAData,
    dataset_info,
    list_datasets,
    load_dataset,
    retired_dataset_migrations,
)

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_DATASETS = {
    "clinic_capacity",
    "community_hospital_capstone",
    "coordination_hulls",
    "cost_mix_choice",
    "crs_free_link_service_chain",
    "directional_super_multivariate_stress",
    "dynamic_capacity_backlog",
    "dynamic_carryover_portfolio",
    "dynamic_network_power_demo",
    "economic_efficiency_4",
    "environmental_circular_chain",
    "environmental_disposability_contrast",
    "environmental_panel",
    "environmental_recovery_chain",
    "frontier_1x1",
    "integer_coordination_hulls",
    "metafrontier_groups",
    "multiperiod_trajectory_contrast",
    "network_2stage",
    "open_service_chain",
    "productivity_panel",
    "range_directional_signed",
    "ren_cas_directional_scale",
    "revenue_5x2",
    "revenue_8x2",
    "sbm_slack_contrast",
    "slacks_2x2",
    "strategic_peer_service",
    "super_sbm_peer_replacement",
    "three_process_service_chain",
    "two_stage_public_service",
    "by_production_component_bottleneck",
    "zhou_ang_wang_non_chp_3",
}


def test_theoretical_datasets_are_deterministic_and_fresh() -> None:
    first = load_dataset("frontier_1x1")
    second = load_dataset("frontier_1x1")

    assert first.equals(second)
    first.loc[0, "input"] = 999
    assert second.loc[0, "input"] == 1.0


def test_dataset_registries_have_exactly_the_same_complete_inventory() -> None:
    public = {item.name for item in list_datasets()}

    assert len(public) == 33
    assert public == EXPECTED_DATASETS
    assert set(datasets_module._BUILDERS) == EXPECTED_DATASETS
    assert set(datasets_module._BASE_INFO) == EXPECTED_DATASETS
    assert set(datasets_module._RESEARCH) == EXPECTED_DATASETS
    assert set(datasets_module._EXPECTED_CONTENT_SHA256) == EXPECTED_DATASETS


def test_community_hospital_capstone_rosters_metadata_and_fingerprint() -> None:
    name = "community_hospital_capstone"
    first = load_dataset(name)
    second = load_dataset(name)
    info = dataset_info(name)
    production = (*info.roles["inputs"], *info.roles["outputs"])

    finite_positive = np.isfinite(first.loc[:, production]).all(axis=1) & first.loc[
        :, production
    ].gt(0.0).all(axis=1)
    data_valid = (
        first["reporting_complete"] & ~first["structural_break"] & finite_positive
    )
    comparable = data_valid & first["service_mandate"].eq("district_general")
    main = comparable & first["tertiary_referral_share"].le(0.15)

    assert first.shape == (64, 14)
    assert int(data_valid.sum()) == 60
    assert int(comparable.sum()) == 52
    assert int(main.sum()) == 48
    assert first.equals(second)
    assert info.provenance.source_kind == "project_synthetic"
    assert info.provenance.citation_status == "none"
    assert info.provenance.oracle_status == "teaching_only"
    assert info.content_sha256 == (
        "f36aff2e248c2f3d08c042897c63154318e97df78ca5e9a9197944f074cd5463"
    )
    assert info.content_sha256 == datasets_module._content_sha256(first)
    assert all(
        variable.definition_status == "declared" for variable in info.variables.values()
    )
    assert info.variables["clinical_fte"].unit == "full-time-equivalent persons"
    assert info.variables["tertiary_referral_share"].unit_status == "unitless"

    with pytest.raises(TypeError):
        info.roles["inputs"] = ("changed",)  # type: ignore[index]
    with pytest.raises(TypeError):
        info.variables["clinical_fte"] = info.variables[  # type: ignore[index]
            "support_fte"
        ]
    with pytest.raises(FrozenInstanceError):
        info.variables["clinical_fte"].unit = "changed"  # type: ignore[misc]


def test_community_hospital_capstone_h048_bcc_oracle() -> None:
    frame = load_dataset("community_hospital_capstone")
    roles = dataset_info("community_hospital_capstone").roles
    production = (*roles["inputs"], *roles["outputs"])
    main = frame.loc[
        frame["reporting_complete"]
        & ~frame["structural_break"]
        & np.isfinite(frame.loc[:, production]).all(axis=1)
        & frame.loc[:, production].gt(0.0).all(axis=1)
        & frame["service_mandate"].eq("district_general")
        & frame["tertiary_referral_share"].le(0.15)
    ].reset_index(drop=True)
    rows = main.set_index("hospital_id")

    assert rows.loc["H048", list(roles["outputs"])].to_numpy() == pytest.approx(
        rows.loc["H008", list(roles["outputs"])].to_numpy()
    )
    assert (
        rows.loc["H048", list(roles["inputs"])].to_numpy()
        / rows.loc["H008", list(roles["inputs"])].to_numpy()
    ) == pytest.approx((1.18, 1.12, 1.15))

    data = DEAData.from_frame(
        main,
        dmu=roles["dmu"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )
    result = BCCInput().fit(data)
    summary = result.summary().set_index("dmu_id")
    peers = result.peers("H048")

    assert summary.loc["H048", "solver_status"] == "optimal"
    assert summary.loc["H048", "score_valid"]
    assert summary.loc["H048", "efficiency"] == pytest.approx(1.0 / 1.12)
    assert peers["reference_dmu_id"].tolist() == ["H008"]
    assert peers["lambda"].tolist() == pytest.approx([1.0])


def test_dataset_metadata_is_deeply_immutable() -> None:
    info = dataset_info("frontier_1x1")

    with pytest.raises(TypeError):
        info.roles["dmu"] = "changed"  # type: ignore[index]
    with pytest.raises(TypeError):
        info.column_roles["dmu"] = "changed"  # type: ignore[index]
    with pytest.raises(TypeError):
        info.topology["processes"] = ("changed",)  # type: ignore[index]
    with pytest.raises(TypeError):
        info.variables["input"] = info.variables["output"]  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        info.variables["input"].unit = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        info.provenance.source_kind = "unknown"  # type: ignore[misc]

    assert dataset_info("frontier_1x1").roles["dmu"] == "dmu"


def test_every_dataset_has_valid_scholarly_metadata_and_stable_content_hash() -> None:
    external = {
        "ren_cas_directional_scale": (
            "b187f3a441416e38534a3f527543dabf9d1f13fb5d53c24dce956907f9c99f21",
            "CC-BY-4.0",
        ),
        "revenue_5x2": (
            "227cad33f14bc4ea78e2c3851c51ed5bd73e0ea1f49414db2b7c9bb171a57b4c",
            "MIT",
        ),
        "revenue_8x2": (
            "ec2703511209e49a4b5da53222b6a45ef7dab963925358019dedd475ab9b91a9",
            "MIT",
        ),
    }
    assert dict(datasets_module._CLEARED_EXTERNAL_DATA_LICENSES) == external
    assert len(datasets_module._CLEARED_PROJECT_DATA_LICENSES) == 30
    approved = dict(datasets_module._CLEARED_DATA_LICENSES)
    assert len(approved) == 33
    for info in list_datasets():
        frame = load_dataset(info.name)
        assert isinstance(info.provenance, DatasetProvenance)
        assert info.provenance.source_kind != "unknown"
        assert info.provenance.citation_status in {"identified", "none"}
        assert bool(info.provenance.citation_identifiers) is (
            info.provenance.citation_status == "identified"
        )
        approved_record = approved.get(info.name)
        expected_license = None if approved_record is None else approved_record[1]
        assert info.provenance.redistribution_status == (
            "cleared" if expected_license is not None else "unknown"
        )
        assert info.provenance.license_identifier == expected_license
        assert info.provenance.oracle_status != "unknown"
        assert info.fingerprint_schema == "deapack.dataset-content.v1"
        assert info.content_sha256 == datasets_module._content_sha256(frame)
        assert (
            info.content_sha256 == datasets_module._EXPECTED_CONTENT_SHA256[info.name]
        )
        assert set(info.variables) == set(frame.columns)
        for name, variable in info.variables.items():
            assert isinstance(variable, DatasetVariableInfo)
            assert variable.name == name
            assert variable.unit_status in {
                "declared",
                "unitless",
                "not_applicable",
                "unspecified",
            }
            assert variable.definition_status in {
                "declared",
                "self_describing",
                "unspecified",
            }

    license_map = (ROOT / "DATA_LICENSES.md").read_text(encoding="utf-8")
    for name, (content_sha256, license_identifier) in approved.items():
        row_start = f"| `{name}` | `{content_sha256}` |"
        rows = [line for line in license_map.splitlines() if line.startswith(row_start)]
        assert len(rows) == 1
        assert f"| `{license_identifier}` |" in rows[0]


def test_changed_content_loses_clearance_even_if_registry_hash_is_updated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    name = "revenue_5x2"
    changed = load_dataset(name)
    changed.loc[0, "input_1"] += 1.0
    changed_digest = datasets_module._content_sha256(changed)

    monkeypatch.setitem(datasets_module._BUILDERS, name, lambda: changed.copy())
    monkeypatch.setattr(
        datasets_module,
        "_EXPECTED_CONTENT_SHA256",
        {
            **datasets_module._EXPECTED_CONTENT_SHA256,
            name: changed_digest,
        },
    )
    info = datasets_module._finalize_dataset_info(
        name,
        datasets_module._BASE_INFO[name],
    )

    assert info.content_sha256 == changed_digest
    assert info.provenance.redistribution_status == "unknown"
    assert info.provenance.license_identifier is None


def test_column_roles_and_topology_labels_are_separate_and_verifiable() -> None:
    for info in list_datasets():
        columns = set(load_dataset(info.name).columns)
        assert set(info.roles) == set(info.column_roles) | set(info.topology)
        assert set(info.column_roles).isdisjoint(info.topology)
        for values in info.column_roles.values():
            names = (values,) if isinstance(values, str) else values
            assert set(names) <= columns

    assert dataset_info("environmental_recovery_chain").topology == {}


def test_known_units_are_declared_and_unconfirmed_units_remain_unspecified() -> None:
    ren = dataset_info("ren_cas_directional_scale")
    assert ren.variables["staff"].unit == "full-time-equivalent persons"
    assert ren.variables["research_expenditure"].unit == "RMB million"
    assert ren.variables["high_sci_publications"].unit == "count"

    frontier = dataset_info("frontier_1x1")
    assert frontier.variables["dmu"].unit_status == "not_applicable"
    assert frontier.variables["input"].unit_status == "unspecified"
    assert frontier.variables["input"].unit is None


def test_scholarly_metadata_rejects_values_outside_controlled_vocabularies() -> None:
    with pytest.raises(ValueError, match="source kind"):
        DatasetProvenance(
            source_kind="invented",  # type: ignore[arg-type]
            citation_status="none",
            citation_identifiers=(),
            redistribution_status="unknown",
            license_identifier=None,
            oracle_status="teaching_only",
        )

    with pytest.raises(ValueError, match="bibkey:, doi:, or software:"):
        DatasetProvenance(
            source_kind="published_reproduction",
            citation_status="identified",
            citation_identifiers=("unqualified-reference",),
            redistribution_status="unknown",
            license_identifier=None,
            oracle_status="published_reproduction",
        )

    with pytest.raises(ValueError, match="unit status"):
        DatasetVariableInfo(
            name="output",
            unit_status="assumed",  # type: ignore[arg-type]
            unit=None,
            definition_status="unspecified",
            definition=None,
        )


def test_dataset_registry_exposes_roles_and_teaching_uses() -> None:
    names = {item.name for item in list_datasets()}

    assert names == EXPECTED_DATASETS
    capacity = dataset_info("clinic_capacity")
    assert capacity.roles["fixed_inputs"] == ("beds",)
    assert capacity.roles["variable_inputs"] == ("staff_hours",)
    assert "capacity-utilization decomposition" in capacity.teaching_uses

    coordination = dataset_info("coordination_hulls")
    assert coordination.roles["dmu"] == "organization"
    assert coordination.roles["inputs"] == ("resource",)

    cost = dataset_info("cost_mix_choice")
    assert cost.roles["input_prices"] == ("price_capital", "price_labor")
    assert load_dataset("cost_mix_choice").shape == (4, 6)

    network = dataset_info("open_service_chain")
    assert network.roles["links"] == (
        "standard_orders",
        "priority_orders",
        "bulk_orders",
    )
    assert load_dataset("open_service_chain").shape == (5, 10)

    dynamic = dataset_info("dynamic_carryover_portfolio")
    assert dynamic.roles["good_carryovers"] == ("capability_stock",)
    assert dynamic.roles["bad_carryovers"] == ("unresolved_stock",)
    assert load_dataset("dynamic_carryover_portfolio").shape == (12, 8)

    environmental = dataset_info("environmental_disposability_contrast")
    assert environmental.roles["nonseparable_bad_outputs"] == ("joint_residual",)
    assert load_dataset("environmental_disposability_contrast").shape == (2, 7)

    stress = dataset_info("directional_super_multivariate_stress")
    assert stress.roles["inputs"] == ("input_1", "input_2", "input_3", "input_4")
    assert load_dataset("directional_super_multivariate_stress").shape == (28, 8)


def test_retired_dataset_ids_have_diagnostics_but_no_data_aliases() -> None:
    migrations = retired_dataset_migrations()

    assert len(migrations) == 18
    assert set(migrations.values()) <= EXPECTED_DATASETS
    with pytest.raises(TypeError):
        migrations["retired"] = "replacement"  # type: ignore[index]
    for retired, replacement in migrations.items():
        assert retired not in EXPECTED_DATASETS
        with pytest.raises(KeyError, match=f"use {replacement!r}"):
            load_dataset(retired)
        with pytest.raises(KeyError, match="No data alias is provided"):
            dataset_info(retired)


def test_ren_directional_scale_dataset_matches_published_table_1() -> None:
    frame = load_dataset("ren_cas_directional_scale")

    assert frame.columns.tolist() == [
        "dmu",
        "staff",
        "research_expenditure",
        "external_funding",
        "high_sci_publications",
        "granted_patents",
    ]
    assert list(frame.itertuples(index=False, name=None)) == [
        ("DMU 1", 327, 296.6066, 67.1469, 183, 10),
        ("DMU 2", 442, 253.1420, 295.7381, 112, 37),
        ("DMU 3", 2589, 1485.7362, 922.1845, 432, 336),
        ("DMU 4", 1472, 1218.8277, 424.3740, 298, 60),
        ("DMU 5", 1338, 780.1315, 193.3859, 204, 49),
        ("DMU 6", 449, 365.3578, 77.5895, 90, 66),
        ("DMU 7", 609, 629.1216, 306.1235, 783, 236),
        ("DMU 8", 321, 376.2365, 324.9000, 428, 153),
        ("DMU 9", 1105, 741.7895, 534.8300, 253, 48),
        ("DMU 10", 276, 257.3831, 41.1500, 67, 2),
        ("DMU 11", 793, 498.1555, 141.8561, 303, 109),
        ("DMU 12", 327, 365.9673, 152.7000, 74, 12),
        ("DMU 13", 63, 58.1003, 12.4700, 71, 0),
        ("DMU 14", 473, 676.5251, 967.1305, 429, 75),
        ("DMU 15", 476, 239.0912, 5.5200, 4, 13),
        ("DMU 16", 919, 559.3781, 108.3900, 66, 38),
    ]


def test_panel_datasets_have_unique_dmu_period_keys() -> None:
    for name in (
        "productivity_panel",
        "environmental_panel",
        "dynamic_network_power_demo",
    ):
        frame = load_dataset(name)
        assert not frame.duplicated(["dmu", "period"]).any()

    for name in ("multiperiod_trajectory_contrast", "dynamic_carryover_portfolio"):
        frame = load_dataset(name)
        assert not frame.duplicated(["unit_id", "period"]).any()

    capacity_backlog = load_dataset("dynamic_capacity_backlog")
    assert not capacity_backlog.duplicated(["organization", "period"]).any()


def test_dynamic_capacity_backlog_loader_returns_fresh_frames() -> None:
    first = load_dataset("dynamic_capacity_backlog")
    first.loc[0, "capacity"] = 999.0

    second = load_dataset("dynamic_capacity_backlog")
    assert second.loc[0, "capacity"] == 2.0
