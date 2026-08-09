"""Project-origin datasets promoted for the rights-safe 2.0 catalogue.

The observations below are the independently designed replacement frames from
the rc1 candidate laboratory.  They intentionally use neutral public IDs and
do not preserve any retired source-qualified loader as a data alias.
"""

# ruff: noqa: E501

from __future__ import annotations

from types import MappingProxyType

import pandas as pd


def _frame(rows: list[tuple[object, ...]], columns: tuple[str, ...]) -> pd.DataFrame:
    return pd.DataFrame.from_records(rows, columns=columns)


def _open_service_chain() -> pd.DataFrame:
    columns = (
        "unit",
        "sourcing_hours",
        "platform_units",
        "transport_units",
        "standard_orders",
        "priority_orders",
        "bulk_orders",
        "service_hours",
        "delivered_value",
        "retained_margin",
    )
    base = ("balanced", 4, 3, 2, 6, 3, 2, 3, 10, 4)
    return _frame(
        [
            base,
            ("scale_2", *(2 * value for value in base[1:])),
            ("resource_drag", 6, 4.5, 3, 6, 3, 2, 4.5, 10, 4),
            ("priority_mix", 3, 4, 2, 4, 6, 2, 4, 10, 5),
            ("bulk_mix", 5, 2, 3, 7, 2, 5, 3, 12, 3),
        ],
        columns,
    )


def _three_process_service_chain() -> pd.DataFrame:
    columns = (
        "unit",
        "intake_hours",
        "verified_requests",
        "resolution_hours",
        "same_day_resolutions",
        "scheduled_cases",
        "delivery_hours",
        "completed_services",
    )
    base = ("balanced", 4, 8, 3, 5, 6, 3, 7)
    return _frame(
        [
            base,
            ("scale_2", *(2 * value for value in base[1:])),
            ("resource_drag", 6, 8, 4.5, 5, 6, 4.5, 7),
            ("rapid_resolution", 5, 9, 2, 7, 5, 4, 6),
            ("scheduled_focus", 3, 6, 4, 3, 8, 3, 9),
        ],
        columns,
    )


def _crs_free_link_service_chain() -> pd.DataFrame:
    columns = (
        "unit",
        "intake_hours",
        "verified_requests",
        "resolution_hours",
        "same_day_resolutions",
        "scheduled_cases",
        "delivery_hours",
        "completed_services",
    )
    base = ("hub_base", 2, 5, 2, 3, 4, 2, 5)
    return _frame(
        [
            base,
            ("hub_double", *(2 * value for value in base[1:])),
            ("idle_capacity", 4, 5, 4, 3, 4, 4, 5),
            ("express_mix", 3, 7, 2, 5, 3, 3, 6),
        ],
        columns,
    )


def _two_stage_public_service() -> pd.DataFrame:
    columns = (
        "unit",
        "staff_hours",
        "platform_cost_units",
        "screened_cases",
        "verified_value",
        "timely_closures",
        "public_value",
    )
    base = ("balanced", 4, 2, 8, 6, 7, 5)
    return _frame(
        [
            base,
            ("scale_2", *(2 * value for value in base[1:])),
            ("resource_drag", 6, 3, 8, 6, 7, 5),
            ("conversion_drag", 4, 2, 8, 6, 3.5, 2.5),
            ("digital_first", 3, 4, 10, 5, 8, 4),
        ],
        columns,
    )


def _environmental_recovery_chain() -> pd.DataFrame:
    return _frame(
        [
            ("base", 2, 2, 2, 1),
            ("scale_2", 4, 4, 4, 2),
            ("input_drag", 3, 2, 2, 1),
            ("residual_control", 3, 3, 1, 0.5),
        ],
        (
            "unit",
            "resource_input",
            "sorted_material",
            "recovered_service",
            "residual_load",
        ),
    )


def _environmental_circular_chain() -> pd.DataFrame:
    return _frame(
        [
            ("base", 2, 2, 4, 2, 3, 3, 3, 4, 5, 1),
            ("scale_2", 4, 4, 8, 4, 6, 6, 6, 8, 10, 2),
            ("input_drag", 3, 3, 4, 2, 3, 3, 3, 4, 5, 1),
            ("residual_control", 3, 3, 6, 3, 4.5, 4.5, 4.5, 6, 2.5, 0.5),
        ],
        (
            "unit",
            "energy_units",
            "labor_units",
            "material_12",
            "support_12",
            "material_23",
            "support_23",
            "material_34",
            "support_34",
            "circular_service",
            "residual_load",
        ),
    )


def _strategic_peer_service() -> pd.DataFrame:
    return _frame(
        [
            ("reach_specialist", 2, 4, 3, 10, 4),
            ("depth_specialist", 4, 2, 3, 5, 9),
            ("balanced", 3, 3, 2, 8, 7),
            ("resource_drag", 4.5, 4.5, 3, 8, 7),
        ],
        (
            "unit",
            "staff_units",
            "capital_units",
            "coordination_units",
            "service_reach",
            "service_depth",
        ),
    )


def _multiperiod_trajectory_contrast() -> pd.DataFrame:
    plans = {
        "trajectory_01": ((1.0, 12.0), (1.0, 15.0), (1.0, 18.0)),
        "trajectory_02": ((1.5, 9.0), (1.25, 15.0), (1.0, 18.0)),
        "trajectory_03": ((1.0, 12.0), (1.4, 11.0), (1.3, 13.0)),
        "trajectory_04": ((1.5, 8.0), (1.5, 10.0), (1.5, 12.0)),
        "trajectory_05": ((1.4, 9.0), (1.25, 12.0), (1.6, 12.0)),
    }
    return pd.DataFrame.from_records(
        [
            {
                "unit_id": unit_id,
                "period": period,
                "resource_index": resource,
                "service_units": service,
            }
            for unit_id, trajectory in plans.items()
            for period, (resource, service) in enumerate(trajectory, start=1)
        ]
    )


def _dynamic_carryover_portfolio() -> pd.DataFrame:
    plans = {
        "path_01": (
            (8.0, 14.0, 12.0, 2.0, 6.0, 8.0),
            (8.0, 16.0, 13.0, 2.0, 6.0, 8.0),
            (8.0, 18.0, 14.0, 2.0, 6.0, 8.0),
        ),
        "path_02": (
            (10.0, 16.0, 14.0, 3.0, 8.0, 12.0),
            (10.0, 18.0, 15.0, 3.0, 8.0, 12.0),
            (10.0, 20.0, 16.0, 3.0, 8.0, 12.0),
        ),
        "path_03": (
            (10.0, 11.0, 9.0, 4.0, 7.0, 8.0),
            (11.0, 12.0, 9.0, 5.0, 7.0, 8.0),
            (12.0, 13.0, 10.0, 5.0, 7.0, 8.0),
        ),
        "path_04": (
            (9.0, 13.0, 11.0, 3.0, 5.0, 10.0),
            (10.0, 13.0, 10.0, 4.0, 7.0, 10.0),
            (9.0, 17.0, 13.0, 2.0, 6.0, 10.0),
        ),
    }
    value_columns = (
        "operating_input",
        "service_output",
        "capability_stock",
        "unresolved_stock",
        "redeployable_stock",
        "committed_stock",
    )
    return pd.DataFrame.from_records(
        [
            {
                "unit_id": unit_id,
                "period": period,
                **dict(zip(value_columns, values, strict=True)),
            }
            for unit_id, trajectory in plans.items()
            for period, values in enumerate(trajectory, start=1)
        ]
    )


def _directional_super_multivariate_stress() -> pd.DataFrame:
    rows = [
        {
            "case_id": "multivariate_stress",
            "unit_id": "stress_01",
            "input_1": 1.0,
            "input_2": 2.0,
            "input_3": 3.0,
            "input_4": 4.0,
            "output_1": 10.0,
            "output_2": 15.0,
        }
    ]
    for index in range(1, 28):
        rows.append(
            {
                "case_id": "multivariate_stress",
                "unit_id": f"stress_{index + 1:02d}",
                "input_1": float(10 + (3 * index) % 17),
                "input_2": float(12 + (5 * index) % 19),
                "input_3": float(14 + (7 * index) % 23),
                "input_4": float(16 + (11 * index) % 29),
                "output_1": float(18 + (13 * index) % 31),
                "output_2": float(20 + (17 * index) % 37),
            }
        )
    return pd.DataFrame.from_records(rows)


def _sbm_slack_contrast() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "unit_id": ["Anchor", "Balanced", "Uneven"],
            "resource_a": [1.0, 2.0, 2.0],
            "resource_b": [1.0, 2.0, 3.0],
            "core_service": [2.0, 2.0, 2.0],
            "quality_service": [2.0, 2.0, 1.0],
        }
    )


def _super_sbm_peer_replacement() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "unit_id": ["Lean", "Balanced", "Automation", "Lagging"],
            "resource_a": [1.0, 2.0, 6.0, 4.0],
            "resource_b": [5.0, 2.0, 1.0, 4.0],
            "service": [1.0, 1.0, 1.0, 1.0],
        }
    )


def _environmental_disposability_contrast() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "unit_id": ["Reference", "Focal"],
            "resource_a": [2.0, 6.0],
            "resource_b": [3.0, 9.0],
            "joint_service": [11.0, 17.0],
            "joint_residual": [3.0, 9.0],
            "independent_service": [13.0, 7.0],
            "independent_residual": [2.0, 8.0],
        }
    )


def _by_production_component_bottleneck() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "unit_id": ["OutputChampion", "ResidualChampion", "Focal"],
            "process_feed": [2.0, 3.0, 6.0],
            "service": [12.0, 6.0, 24.0],
            "residual": [8.0, 2.0, 9.0],
        }
    )


def _cost_mix_choice() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "unit_id": ["CapitalFrugal", "Balanced", "LaborFrugal", "Focal"],
            "capital": [2.0, 4.0, 9.0, 12.0],
            "labor": [7.0, 4.0, 2.0, 12.0],
            "service": [3.0, 3.0, 3.0, 6.0],
            "price_capital": [5.0] * 4,
            "price_labor": [2.0] * 4,
        }
    )


def _integer_coordination_hulls() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "unit_id": ["Micro", "Large", "Focal"],
            "resource": [3.0, 10.0, 20.0],
            "service": [4.0, 10.0, 13.0],
        }
    )


def _spec(
    builder: object,
    *,
    title: str,
    description: str,
    roles: dict[str, str | tuple[str, ...]],
    teaching_uses: tuple[str, ...],
    source_kind: str = "project_theory",
    content_sha256: str,
) -> MappingProxyType:
    return MappingProxyType(
        {
            "builder": builder,
            "title": title,
            "description": description,
            "roles": MappingProxyType(roles),
            "teaching_uses": teaching_uses,
            "source_kind": source_kind,
            "content_sha256": content_sha256,
        }
    )


SPECS = MappingProxyType(
    {
        "open_service_chain": _spec(
            _open_service_chain,
            title="Open cooperative service chain",
            description="A fictional two-process chain with transparent scale and resource-drag contrasts.",
            roles={
                "dmu": "unit",
                "sourcing_inputs": (
                    "sourcing_hours",
                    "platform_units",
                    "transport_units",
                ),
                "links": ("standard_orders", "priority_orders", "bulk_orders"),
                "service_inputs": ("service_hours",),
                "outputs": ("delivered_value", "retained_margin"),
            },
            teaching_uses=(
                "open network DEA",
                "process decomposition",
                "analytical scale check",
            ),
            content_sha256="7743e3d3efdba20f0297f7feb47378859f9cc5601df35f55a6ff11765e804468",
        ),
        "three_process_service_chain": _spec(
            _three_process_service_chain,
            title="Three-process public-service chain",
            description="A fictional intake, resolution, and delivery network with controlled handoff contrasts.",
            roles={
                "dmu": "unit",
                "external_inputs": (
                    "intake_hours",
                    "resolution_hours",
                    "delivery_hours",
                ),
                "links": ("verified_requests", "scheduled_cases"),
                "outputs": ("same_day_resolutions", "completed_services"),
            },
            teaching_uses=(
                "three-stage network DEA",
                "fixed and free links",
                "process diagnosis",
            ),
            content_sha256="9815ba52ab54336ca3cc0853b9077672b64e3edbcbb259127737eb2105ae9d51",
        ),
        "crs_free_link_service_chain": _spec(
            _crs_free_link_service_chain,
            title="CRS free-link service chain",
            description="A compact three-process chain with an exact proportional twin and an idle-capacity contrast.",
            roles={
                "dmu": "unit",
                "external_inputs": (
                    "intake_hours",
                    "resolution_hours",
                    "delivery_hours",
                ),
                "links": ("verified_requests", "scheduled_cases"),
                "outputs": ("same_day_resolutions", "completed_services"),
            },
            teaching_uses=("CRS network SBM", "free links", "proportionality check"),
            content_sha256="a0855b81e607914d0eeb5fcfa6f326743588b9cc026f1aeeb957e240f1d3de43",
        ),
        "two_stage_public_service": _spec(
            _two_stage_public_service,
            title="Two-stage public-service conversion",
            description="A fictional screening-to-outcome system separating upstream and downstream resource drag.",
            roles={
                "dmu": "unit",
                "inputs": ("staff_hours", "platform_cost_units"),
                "intermediates": ("screened_cases", "verified_value"),
                "outputs": ("timely_closures", "public_value"),
            },
            teaching_uses=(
                "relational network DEA",
                "stage decomposition",
                "scale check",
            ),
            content_sha256="21de69ded29f300acd4aa7fa9c88ecbc8bc78c2ccec4a6a5319031b31fc07210",
        ),
        "environmental_recovery_chain": _spec(
            _environmental_recovery_chain,
            title="Environmental recovery chain",
            description="A fictional two-process recovery ledger with a residual-control contrast.",
            roles={
                "dmu": "unit",
                "inputs": ("resource_input",),
                "intermediates": ("sorted_material",),
                "outputs": ("recovered_service",),
                "bad_outputs": ("residual_load",),
            },
            teaching_uses=(
                "environmental network DEA",
                "weak disposal",
                "target reconstruction",
            ),
            content_sha256="b29eb956318cc2673fc826513800d07e362eca189643d5e7c5ab1fea03a3292b",
        ),
        "environmental_circular_chain": _spec(
            _environmental_circular_chain,
            title="Environmental circular-service chain",
            description="A fictional four-process ledger with two explicitly tracked handoff accounts.",
            roles={
                "dmu": "unit",
                "inputs": ("energy_units", "labor_units"),
                "intermediates": (
                    "material_12",
                    "support_12",
                    "material_23",
                    "support_23",
                    "material_34",
                    "support_34",
                ),
                "outputs": ("circular_service",),
                "bad_outputs": ("residual_load",),
            },
            teaching_uses=(
                "general environmental networks",
                "intermediate accounts",
                "CRS scale check",
            ),
            content_sha256="6829df95a5b472093c29898d42800988d3f9406cd62d4c72ababd88d43a086c8",
        ),
        "strategic_peer_service": _spec(
            _strategic_peer_service,
            title="Strategic peer-service scorecards",
            description="Four fictional service strategies for ordinary and game cross-efficiency appraisal.",
            roles={
                "dmu": "unit",
                "inputs": ("staff_units", "capital_units", "coordination_units"),
                "outputs": ("service_reach", "service_depth"),
            },
            teaching_uses=(
                "cross-efficiency",
                "game cross-efficiency",
                "peer appraisal",
            ),
            content_sha256="81748dcf3917e17ca889a3b5aa7789f366bea28e1dc48273a749629f7284309f",
        ),
        "multiperiod_trajectory_contrast": _spec(
            _multiperiod_trajectory_contrast,
            title="Multi-period trajectory contrast",
            description="Five fictional three-period trajectories separating persistent, catch-up, and uneven performance.",
            roles={
                "dmu": "unit_id",
                "period": "period",
                "inputs": ("resource_index",),
                "outputs": ("service_units",),
            },
            teaching_uses=(
                "multi-period aggregative DEA",
                "period-specific efficiency",
                "trajectory diagnosis",
            ),
            content_sha256="4873e3bd746f3d8fc0ae68604cfc70c32c8cbcbd4a6884e011b3fc0b53283377",
        ),
        "dynamic_carryover_portfolio": _spec(
            _dynamic_carryover_portfolio,
            title="Dynamic carry-over portfolio",
            description="Four fictional operating paths with beneficial, harmful, discretionary, and fixed stocks.",
            roles={
                "dmu": "unit_id",
                "period": "period",
                "inputs": ("operating_input",),
                "outputs": ("service_output",),
                "good_carryovers": ("capability_stock",),
                "bad_carryovers": ("unresolved_stock",),
                "free_carryovers": ("redeployable_stock",),
                "fixed_carryovers": ("committed_stock",),
            },
            teaching_uses=("dynamic SBM", "carry-over roles", "period attribution"),
            source_kind="project_synthetic",
            content_sha256="5189e5cf8c19d197e11539046de63d36a2f2f23998ad7afd3c93bc393e15c939",
        ),
        "directional_super_multivariate_stress": _spec(
            _directional_super_multivariate_stress,
            title="Directional super-efficiency stress case",
            description="Twenty-eight positive non-collinear project plans generated from documented integer schedules.",
            roles={
                "case": "case_id",
                "dmu": "unit_id",
                "inputs": ("input_1", "input_2", "input_3", "input_4"),
                "outputs": ("output_1", "output_2"),
            },
            teaching_uses=(
                "directional super-efficiency",
                "leave-one-out appraisal",
                "dense LP cross-check",
            ),
            content_sha256="3d6b49ffcc975998b8ec53153f9859d3b1c2d2d285c65f9f115dd1557f143bbe",
        ),
        "sbm_slack_contrast": _spec(
            _sbm_slack_contrast,
            title="SBM slack contrast",
            description="A three-plan analytical case separating radial contraction from non-radial slack.",
            roles={
                "dmu": "unit_id",
                "inputs": ("resource_a", "resource_b"),
                "outputs": ("core_service", "quality_service"),
            },
            teaching_uses=(
                "SBM",
                "radial versus non-radial diagnosis",
                "analytical oracle",
            ),
            content_sha256="fb64ce63486e130ecfedfed9cc313dbdcacb16e32f5e7dcefabf9c7ec299578d",
        ),
        "super_sbm_peer_replacement": _spec(
            _super_sbm_peer_replacement,
            title="Super-SBM peer replacement",
            description="Three efficient resource mixes and one dominated plan for self-exclusion diagnostics.",
            roles={
                "dmu": "unit_id",
                "inputs": ("resource_a", "resource_b"),
                "outputs": ("service",),
            },
            teaching_uses=("super-SBM", "peer replacement", "eligibility screening"),
            content_sha256="eba2e104f3ceda0732f03f793221f1910de0d3df3e9988763814df1b353fbe28",
        ),
        "environmental_disposability_contrast": _spec(
            _environmental_disposability_contrast,
            title="Environmental disposability contrast",
            description="One operating table for comparing separable and joint good/bad-output adjustment contracts.",
            roles={
                "dmu": "unit_id",
                "inputs": ("resource_a", "resource_b"),
                "outputs": ("joint_service", "independent_service"),
                "bad_outputs": ("joint_residual", "independent_residual"),
                "nonseparable_good_outputs": ("joint_service",),
                "nonseparable_bad_outputs": ("joint_residual",),
                "separable_good_outputs": ("independent_service",),
                "separable_bad_outputs": ("independent_residual",),
            },
            teaching_uses=(
                "environmental SBM",
                "joint disposability",
                "model-contract sensitivity",
            ),
            content_sha256="20d836060604a9845e63f00f74f10117576bf140233efe689e352edaf530f933",
        ),
        "by_production_component_bottleneck": _spec(
            _by_production_component_bottleneck,
            title="By-production component bottleneck",
            description="A three-plan analytical case with distinct service and residual benchmarks.",
            roles={
                "dmu": "unit_id",
                "inputs": ("process_feed",),
                "polluting_inputs": ("process_feed",),
                "outputs": ("service",),
                "bad_outputs": ("residual",),
            },
            teaching_uses=(
                "by-production DEA",
                "component bottlenecks",
                "directional distance",
            ),
            content_sha256="450c8779c30448ae066243657024a48db7ce01b31bc5e7da67e805f0c0cc5a8b",
        ),
        "cost_mix_choice": _spec(
            _cost_mix_choice,
            title="Cost-efficiency input-mix choice",
            description="A four-plan analytical case separating technical contraction from allocative input choice.",
            roles={
                "dmu": "unit_id",
                "inputs": ("capital", "labor"),
                "outputs": ("service",),
                "input_prices": ("price_capital", "price_labor"),
            },
            teaching_uses=(
                "cost efficiency",
                "technical and allocative decomposition",
                "analytical oracle",
            ),
            content_sha256="ee7f40afa9a318ba12bb2996cb5ad4d5ef26bfe15e8185763cb1c5c5bb0b82ba",
        ),
        "integer_coordination_hulls": _spec(
            _integer_coordination_hulls,
            title="Integer coordination hulls",
            description="Three project plans contrasting indivisible peer choice, integer replication, and continuous relaxation.",
            roles={"dmu": "unit_id", "inputs": ("resource",), "outputs": ("service",)},
            teaching_uses=(
                "FDH/FCH/FRH comparison",
                "integer coordination",
                "continuous relaxation",
            ),
            content_sha256="27cf0c63018cf6b102d86e7ea396d7d18ec58b8a27f35a4ea2463904a382b6a5",
        ),
    }
)


RETIRED_TO_REPLACEMENT = MappingProxyType(
    {
        "coelli_cost": "cost_mix_choice",
        "cook_open_supply_chain": "open_service_chain",
        "cook_three_stage_network": "three_process_service_chain",
        "kalhor_matin_environmental_network_2018_example_1": "environmental_recovery_chain",
        "kalhor_matin_environmental_network_2018_example_2": "environmental_circular_chain",
        "kao_hwang_insurance": "two_stage_public_service",
        "liang_game_cross_2008": "strategic_peer_service",
        "murty_by_production_5dmu": "by_production_component_bottleneck",
        "park_park_multiperiod": "multiperiod_trajectory_contrast",
        "ray_directional_super_10": "directional_super_multivariate_stress",
        "replication_modules": "integer_coordination_hulls",
        "tone_nonseparable_sbm_2003": "environmental_disposability_contrast",
        "tone_sbm_5x2": "sbm_slack_contrast",
        "tone_separable_sbm_2003": "environmental_disposability_contrast",
        "tone_super_sbm": "super_sbm_peer_replacement",
        "tone_tsutsui_dynamic": "dynamic_carryover_portfolio",
        "tone_tsutsui_network": "three_process_service_chain",
        "tone_tsutsui_network_crs4": "crs_free_link_service_chain",
    }
)


__all__ = ["RETIRED_TO_REPLACEMENT", "SPECS"]
