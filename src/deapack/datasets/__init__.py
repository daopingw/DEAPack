"""Deterministic teaching and validation datasets.

The small theoretical datasets are designed to make frontiers and model
properties visible. They contain no random draws, so figures and regression
tests remain reproducible across releases.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from numbers import Integral, Real
from types import MappingProxyType
from typing import Literal

import numpy as np
import pandas as pd

from ._replacement_cases import RETIRED_TO_REPLACEMENT
from ._replacement_cases import SPECS as _REPLACEMENT_SPECS

DatasetSourceKind = Literal[
    "project_theory",
    "project_synthetic",
    "published_reproduction",
    "source_derived_theory",
    "external_implementation_example",
    "unknown",
]
DatasetCitationStatus = Literal["identified", "none", "unknown"]
DatasetRedistributionStatus = Literal["cleared", "restricted", "unknown"]
DatasetOracleStatus = Literal[
    "analytical",
    "published_reproduction",
    "cross_implementation",
    "source_equation",
    "teaching_only",
    "unknown",
]
DatasetUnitStatus = Literal["declared", "unitless", "not_applicable", "unspecified"]
DatasetDefinitionStatus = Literal["declared", "self_describing", "unspecified"]

_SOURCE_KINDS = frozenset(
    {
        "project_theory",
        "project_synthetic",
        "published_reproduction",
        "source_derived_theory",
        "external_implementation_example",
        "unknown",
    }
)
_CITATION_STATUSES = frozenset({"identified", "none", "unknown"})
_REDISTRIBUTION_STATUSES = frozenset({"cleared", "restricted", "unknown"})
_ORACLE_STATUSES = frozenset(
    {
        "analytical",
        "published_reproduction",
        "cross_implementation",
        "source_equation",
        "teaching_only",
        "unknown",
    }
)
_UNIT_STATUSES = frozenset({"declared", "unitless", "not_applicable", "unspecified"})
_DEFINITION_STATUSES = frozenset({"declared", "self_describing", "unspecified"})
_CITATION_PREFIXES = ("bibkey:", "doi:", "software:")


@dataclass(frozen=True, slots=True)
class DatasetProvenance:
    """Immutable scholarly provenance for one bundled dataset.

    ``redistribution_status`` and ``license_identifier`` describe the dataset
    content, not merely the Python package containing it.  ``"unknown"`` is a
    deliberate fail-closed value: it must not be interpreted as permission to
    redistribute a source table independently of DEAPack.
    """

    source_kind: DatasetSourceKind
    citation_status: DatasetCitationStatus
    citation_identifiers: tuple[str, ...]
    redistribution_status: DatasetRedistributionStatus
    license_identifier: str | None
    oracle_status: DatasetOracleStatus

    def __post_init__(self) -> None:
        if self.source_kind not in _SOURCE_KINDS:
            raise ValueError(f"unsupported dataset source kind: {self.source_kind!r}")
        if self.citation_status not in _CITATION_STATUSES:
            raise ValueError(
                f"unsupported dataset citation status: {self.citation_status!r}"
            )
        if self.redistribution_status not in _REDISTRIBUTION_STATUSES:
            raise ValueError(
                "unsupported dataset redistribution status: "
                f"{self.redistribution_status!r}"
            )
        if self.oracle_status not in _ORACLE_STATUSES:
            raise ValueError(
                f"unsupported dataset oracle status: {self.oracle_status!r}"
            )
        identifiers = tuple(str(value).strip() for value in self.citation_identifiers)
        if any(not value for value in identifiers):
            raise ValueError("citation identifiers must be non-empty strings")
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("citation identifiers must be unique")
        if any(not value.startswith(_CITATION_PREFIXES) for value in identifiers):
            raise ValueError(
                "citation identifiers must use a bibkey:, doi:, or software: prefix"
            )
        if self.citation_status == "identified" and not identifiers:
            raise ValueError("identified citation status requires an identifier")
        if self.citation_status == "none" and identifiers:
            raise ValueError("citation status 'none' cannot carry identifiers")
        if self.license_identifier is not None and not self.license_identifier.strip():
            raise ValueError("license identifier must be non-empty when supplied")
        object.__setattr__(self, "citation_identifiers", identifiers)


@dataclass(frozen=True, slots=True)
class DatasetVariableInfo:
    """Immutable unit and meaning metadata for one physical data column."""

    name: str
    unit_status: DatasetUnitStatus
    unit: str | None
    definition_status: DatasetDefinitionStatus
    definition: str | None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("dataset variable name must be non-empty")
        if self.unit_status not in _UNIT_STATUSES:
            raise ValueError(f"unsupported dataset unit status: {self.unit_status!r}")
        if self.definition_status not in _DEFINITION_STATUSES:
            raise ValueError(
                f"unsupported dataset definition status: {self.definition_status!r}"
            )
        if self.unit_status == "declared":
            if self.unit is None or not self.unit.strip():
                raise ValueError("declared unit status requires a unit")
        elif self.unit is not None:
            raise ValueError("unit text is allowed only when unit_status is 'declared'")
        if self.definition_status == "declared":
            if self.definition is None or not self.definition.strip():
                raise ValueError("declared definition status requires a definition")
        elif self.definition_status == "self_describing":
            if self.definition is None or not self.definition.strip():
                raise ValueError(
                    "self-describing definition status requires explanatory text"
                )
        elif self.definition is not None:
            raise ValueError(
                "definition text requires declared or self-describing status"
            )


_UNKNOWN_PROVENANCE = DatasetProvenance(
    source_kind="unknown",
    citation_status="unknown",
    citation_identifiers=(),
    redistribution_status="unknown",
    license_identifier=None,
    oracle_status="unknown",
)


@dataclass(frozen=True, slots=True)
class DatasetInfo:
    """Deeply immutable metadata for a bundled research or teaching dataset.

    ``roles`` preserves the original public role mapping.  ``column_roles`` is
    its machine-verifiable subset whose values are actual DataFrame columns;
    process names and other graph labels live separately in ``topology``.
    """

    name: str
    title: str
    description: str
    roles: Mapping[str, str | tuple[str, ...]]
    teaching_uses: tuple[str, ...]
    provenance: DatasetProvenance = _UNKNOWN_PROVENANCE
    column_roles: Mapping[str, str | tuple[str, ...]] = MappingProxyType({})
    topology: Mapping[str, str | tuple[str, ...]] = MappingProxyType({})
    variables: Mapping[str, DatasetVariableInfo] = MappingProxyType({})
    content_sha256: str | None = None
    fingerprint_schema: str = "deapack.dataset-content.v1"

    def __post_init__(self) -> None:
        if (
            not self.name.strip()
            or not self.title.strip()
            or not self.description.strip()
        ):
            raise ValueError("dataset name, title, and description must be non-empty")
        if not isinstance(self.provenance, DatasetProvenance):
            raise ValueError("dataset provenance must be DatasetProvenance")
        if not self.fingerprint_schema.strip():
            raise ValueError("fingerprint schema must be non-empty")
        teaching_uses = tuple(str(value).strip() for value in self.teaching_uses)
        if not teaching_uses or any(not value for value in teaching_uses):
            raise ValueError("teaching uses must contain non-empty strings")
        roles = _freeze_role_mapping(self.roles, field="roles")
        column_roles = _freeze_role_mapping(self.column_roles, field="column_roles")
        topology = _freeze_role_mapping(self.topology, field="topology")
        variables = {str(name): value for name, value in self.variables.items()}
        if any(not name for name in variables):
            raise ValueError("dataset variable metadata keys must be non-empty")
        if any(
            not isinstance(value, DatasetVariableInfo) or value.name != name
            for name, value in variables.items()
        ):
            raise ValueError(
                "dataset variable metadata must be DatasetVariableInfo keyed by name"
            )
        digest = self.content_sha256
        if digest is not None and (
            len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise ValueError("content_sha256 must be a lowercase SHA-256 digest")
        object.__setattr__(self, "roles", roles)
        object.__setattr__(self, "column_roles", column_roles)
        object.__setattr__(self, "topology", topology)
        object.__setattr__(self, "variables", MappingProxyType(variables))
        object.__setattr__(self, "teaching_uses", teaching_uses)


def _freeze_role_mapping(
    values: Mapping[str, str | tuple[str, ...]],
    *,
    field: str,
) -> Mapping[str, str | tuple[str, ...]]:
    frozen: dict[str, str | tuple[str, ...]] = {}
    for raw_key, raw_value in values.items():
        key = str(raw_key).strip()
        if not key:
            raise ValueError(f"{field} keys must be non-empty")
        if isinstance(raw_value, str):
            value: str | tuple[str, ...] = raw_value.strip()
            if not value:
                raise ValueError(f"{field}[{key!r}] must be non-empty")
        else:
            value = tuple(str(item).strip() for item in raw_value)
            if not value or any(not item for item in value):
                raise ValueError(f"{field}[{key!r}] must contain non-empty labels")
        frozen[key] = value
    return MappingProxyType(frozen)


def _frontier_1x1() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "dmu": ["A", "B", "C", "D", "E", "F", "G", "H"],
            "input": [1.0, 2.0, 3.0, 4.0, 2.0, 3.0, 4.0, 3.5],
            "output": [1.0, 2.5, 3.3, 3.8, 1.5, 2.0, 2.8, 3.0],
        }
    )


def _slacks_2x2() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "dmu": ["A", "B", "C", "D", "E", "F", "G", "H"],
            "labor": [1.0, 1.4, 2.2, 3.0, 2.0, 2.8, 3.4, 2.5],
            "capital": [3.0, 2.2, 1.5, 1.0, 2.8, 2.4, 1.8, 2.0],
            "service": [1.2, 1.6, 2.0, 2.2, 1.3, 1.7, 1.8, 1.6],
            "quality": [0.70, 0.82, 0.90, 0.94, 0.62, 0.72, 0.78, 0.68],
        }
    )


def _clinic_capacity() -> pd.DataFrame:
    """Theory-led short-run physical-capacity example."""
    return pd.DataFrame(
        {
            "clinic": ["A", "B", "C", "D"],
            "beds": [10.0, 10.0, 20.0, 20.0],
            "staff_hours": [100.0, 200.0, 100.0, 200.0],
            "visits": [100.0, 200.0, 200.0, 300.0],
        }
    )


def _community_hospital_capstone() -> pd.DataFrame:
    """Return the deterministic raw roster for the hospital-study capstone.

    The fixture is wholly synthetic.  It represents one financial-year roster,
    not observations from a real health system.  A fixed PCG64 stream with seed
    ``20260803`` generates hospital size, service mix, case mix, quality, and
    resource needs.  Uniform values are derived directly from the PCG64 integer
    stream, normal values use a fixed Box--Muller transform, and Beta(5, 2)
    values are the fifth order statistic of six uniforms.  Continuous fields
    are rounded before packaging so the data and its content fingerprint remain
    stable across supported platforms.  For hospital ``i`` the generated
    service volumes are::

        discharges_i = round(8200 * size_i * mix_i)
        outpatients_i = round(42000 * size_i * (1.20 - 0.20 * mix_i))
        adjusted_discharges_i = discharges_i * case_mix_i * quality_i

    Three positive resource requirements are affine functions of the two
    service outputs::

        clinical_requirement_i = 115 + 0.052 * adjusted_discharges_i
                                     + 0.0048 * outpatients_i
        support_requirement_i = 55 + 0.015 * adjusted_discharges_i
                                   + 0.0025 * outpatients_i
        nonpay_requirement_i = 2.8 + 0.00055 * adjusted_discharges_i
                                  + 0.00011 * outpatients_i

    Observed resources equal those requirements divided by a latent operating
    efficiency factor ``0.72 + 0.28 * Beta(5, 2)`` and multiplied by an
    item-specific excess ``1 + abs(Normal(0, 0.03))``.  Six deliberately
    efficient reference hospitals have no generated excess.  Four borderline
    referral hospitals receive resource-mix adjustments chosen in advance so
    that readers can examine sensitivity to the comparison population.

    ``H048`` is an exact validation case: it has the same service outputs as
    anchor ``H008`` and 1.18, 1.12, and 1.15 times H008's three inputs.  The
    input-oriented VRS radial score is therefore exactly ``1 / 1.12`` with
    H008 as its unit-weight peer.  Two incomplete records and two structural-
    break records are outside the district-general comparison population but
    remain in the raw roster so a study can preserve its exclusion ledger.
    """

    bit_generator = np.random.PCG64(20260803)

    def uniform(shape: int | tuple[int, ...]) -> np.ndarray:
        """Map the stable PCG64 integer stream to open float64 uniforms."""

        dimensions = (shape,) if isinstance(shape, int) else shape
        count = int(np.prod(dimensions, dtype=np.int64))
        raw = np.asarray(bit_generator.random_raw(count), dtype=np.uint64)
        mantissa = (raw >> np.uint64(11)).astype(np.float64)
        values = (mantissa + 0.5) / float(1 << 53)
        return values.reshape(dimensions)

    def normal(shape: int | tuple[int, ...]) -> np.ndarray:
        """Generate standard normals through one fixed Box--Muller mapping."""

        dimensions = (shape,) if isinstance(shape, int) else shape
        count = int(np.prod(dimensions, dtype=np.int64))
        pair_count = (count + 1) // 2
        draws = uniform((pair_count, 2))
        radius = np.sqrt(-2.0 * np.log(draws[:, 0]))
        angle = 2.0 * np.pi * draws[:, 1]
        values = np.empty(pair_count * 2, dtype=np.float64)
        values[0::2] = radius * np.cos(angle)
        values[1::2] = radius * np.sin(angle)
        return values[:count].reshape(dimensions)

    n_hospitals = 64
    positions = np.arange(n_hospitals)
    hospital_ids = [f"H{position:03d}" for position in range(1, n_hospitals + 1)]

    service_mandate = np.where(
        positions < 52,
        "district_general",
        np.where(positions < 58, "teaching_referral", "specialist"),
    )
    size = np.round(np.clip(np.exp(0.36 * normal(n_hospitals)), 0.55, 1.85), 8)
    service_mix = np.round(0.75 + 0.50 * uniform(n_hospitals), 8)
    case_mix_index = np.round(0.88 + 0.34 * uniform(n_hospitals), 8)
    quality_index = np.round(0.94 + 0.09 * uniform(n_hospitals), 8)

    raw_discharges = np.rint(8200.0 * size * service_mix)
    outpatient_encounters = np.rint(42000.0 * size * (1.20 - 0.20 * service_mix))
    adjusted_discharges = np.round(
        raw_discharges * case_mix_index * quality_index,
        6,
    )

    requirements = np.column_stack(
        (
            115.0 + 0.052 * adjusted_discharges + 0.0048 * outpatient_encounters,
            55.0 + 0.015 * adjusted_discharges + 0.0025 * outpatient_encounters,
            2.8 + 0.00055 * adjusted_discharges + 0.00011 * outpatient_encounters,
        )
    )
    requirements = np.round(requirements, 6)
    beta_5_2 = np.sort(uniform((n_hospitals, 6)), axis=1)[:, 4]
    latent_efficiency = np.round(0.72 + 0.28 * beta_5_2, 8)
    anchors = np.asarray([0, 7, 15, 23, 31, 39], dtype=np.int64)
    latent_efficiency[anchors] = 1.0
    item_excess = np.round(
        1.0 + np.abs(0.03 * normal((n_hospitals, 3))),
        8,
    )
    item_excess[anchors] = 1.0
    resources = np.round(
        requirements / latent_efficiency[:, None] * item_excess,
        6,
    )

    resources[48:52] = np.round(
        requirements[48:52]
        * np.asarray(
            (
                (0.94, 1.00, 0.96),
                (1.00, 0.93, 0.96),
                (0.96, 0.96, 0.92),
                (0.93, 0.98, 1.00),
            )
        ),
        6,
    )

    raw_discharges[47] = raw_discharges[7]
    outpatient_encounters[47] = outpatient_encounters[7]
    case_mix_index[47] = case_mix_index[7]
    quality_index[47] = quality_index[7]
    adjusted_discharges[47] = adjusted_discharges[7]
    resources[47] = resources[7] * np.asarray((1.18, 1.12, 1.15))

    tertiary_referral_share = np.round(
        np.concatenate(
            (
                0.02 + 0.12 * uniform(48),
                0.18 + 0.06 * uniform(4),
                0.28 + 0.17 * uniform(6),
                0.05 + 0.15 * uniform(6),
            )
        ),
        6,
    )
    reporting_complete = np.ones(n_hospitals, dtype=bool)
    reporting_complete[[54, 60]] = False
    structural_break = np.zeros(n_hospitals, dtype=bool)
    structural_break[[55, 61]] = True

    frame = pd.DataFrame(
        {
            "hospital_id": hospital_ids,
            "financial_year": ["2025/26"] * n_hospitals,
            "service_mandate": service_mandate,
            "tertiary_referral_share": tertiary_referral_share,
            "reporting_complete": reporting_complete,
            "structural_break": structural_break,
            "clinical_fte": resources[:, 0],
            "support_fte": resources[:, 1],
            "nonpay_operating_spend_gbp_m": resources[:, 2],
            "raw_inpatient_discharges": raw_discharges,
            "case_mix_index": case_mix_index,
            "quality_index": quality_index,
            "quality_adjusted_discharges": adjusted_discharges,
            "outpatient_encounters": outpatient_encounters,
        }
    )
    frame.loc[54, "nonpay_operating_spend_gbp_m"] = np.nan
    frame.loc[60, "outpatient_encounters"] = np.nan
    return frame


def _coordination_hulls() -> pd.DataFrame:
    """Theory-led oracle separating FDH, FCH, FRH, CCR, and VRS."""
    return pd.DataFrame(
        {
            "organization": ["A", "B", "C", "E"],
            "resource": [3.0, 4.0, 12.0, 10.0],
            "service": [6.0, 5.0, 14.0, 10.0],
        }
    )


def _ren_cas_directional_scale() -> pd.DataFrame:
    """Ren et al. (2021) directional-scale example, Table 1."""
    return pd.DataFrame(
        {
            "dmu": [f"DMU {value}" for value in range(1, 17)],
            "staff": [
                327,
                442,
                2589,
                1472,
                1338,
                449,
                609,
                321,
                1105,
                276,
                793,
                327,
                63,
                473,
                476,
                919,
            ],
            "research_expenditure": [
                296.6066,
                253.1420,
                1485.7362,
                1218.8277,
                780.1315,
                365.3578,
                629.1216,
                376.2365,
                741.7895,
                257.3831,
                498.1555,
                365.9673,
                58.1003,
                676.5251,
                239.0912,
                559.3781,
            ],
            "external_funding": [
                67.1469,
                295.7381,
                922.1845,
                424.3740,
                193.3859,
                77.5895,
                306.1235,
                324.9000,
                534.8300,
                41.1500,
                141.8561,
                152.7000,
                12.4700,
                967.1305,
                5.5200,
                108.3900,
            ],
            "high_sci_publications": [
                183,
                112,
                432,
                298,
                204,
                90,
                783,
                428,
                253,
                67,
                303,
                74,
                71,
                429,
                4,
                66,
            ],
            "granted_patents": [
                10,
                37,
                336,
                60,
                49,
                66,
                236,
                153,
                48,
                2,
                109,
                12,
                0,
                75,
                13,
                38,
            ],
        }
    )


def _zhou_ang_wang_non_chp_3() -> pd.DataFrame:
    """Analytical non-CHP energy--carbon source-equation fixture."""
    return pd.DataFrame(
        {
            "dmu": ["A", "D", "O"],
            "fossil_energy": [1.0, 1.5, 2.0],
            "electricity": [1.0, 1.0, 1.0],
            "co2": [1.0, 4.0, 4.0],
        }
    )


def _metafrontier_groups() -> pd.DataFrame:
    """Exact two-group radial metafrontier oracle."""
    return pd.DataFrame(
        {
            "dmu": list("ABCDEF"),
            "technology_group": [
                "group_1",
                "group_1",
                "group_1",
                "group_2",
                "group_2",
                "group_2",
            ],
            "resource": [2.0, 4.0, 4.0, 1.0, 2.0, 4.0],
            "service": [2.0, 4.0, 2.0, 2.0, 4.0, 8.0],
        }
    )


def _range_directional_signed() -> pd.DataFrame:
    """Exact signed-data range-directional oracle."""
    return pd.DataFrame(
        {
            "dmu": ["A", "B", "C"],
            "input": [-2.0, 2.0, 2.0],
            "output": [2.0, 6.0, -2.0],
        }
    )


def _productivity_panel() -> pd.DataFrame:
    units = ("A", "B", "C", "D", "E")
    periods = (2020, 2021, 2022, 2023)
    base_inputs = {
        "A": (1.0, 3.0),
        "B": (2.0, 2.0),
        "C": (3.0, 1.0),
        "D": (2.4, 2.4),
        "E": (3.0, 3.0),
    }
    technology = {2020: 1.00, 2021: 1.06, 2022: 1.13, 2023: 1.21}
    efficiency = {
        "A": (1.00, 1.00, 1.00, 1.00),
        "B": (1.00, 1.00, 1.00, 1.00),
        "C": (1.00, 1.00, 1.00, 1.00),
        "D": (0.75, 0.80, 0.86, 0.92),
        "E": (0.65, 0.72, 0.80, 0.88),
    }

    rows = []
    for period_position, period in enumerate(periods):
        input_growth = 1.0 + 0.02 * period_position
        for unit in units:
            base_capital, base_labor = base_inputs[unit]
            k = base_capital * input_growth
            labor_value = base_labor * input_growth
            frontier_output = technology[period] * (k * labor_value) ** 0.5
            rows.append(
                {
                    "dmu": unit,
                    "period": period,
                    "capital": round(k, 4),
                    "labor": round(labor_value, 4),
                    "output": round(
                        frontier_output * efficiency[unit][period_position], 4
                    ),
                }
            )
    return pd.DataFrame(rows)


def _environmental_panel() -> pd.DataFrame:
    plants = ("North", "South", "East", "West", "Central", "Coastal")
    periods = (2020, 2021, 2022, 2023)
    scale = {
        "North": 1.00,
        "South": 1.20,
        "East": 1.45,
        "West": 0.90,
        "Central": 1.10,
        "Coastal": 1.35,
    }
    management = {
        "North": 0.90,
        "South": 0.95,
        "East": 1.00,
        "West": 0.82,
        "Central": 0.88,
        "Coastal": 0.98,
    }
    emission_factor = {
        "North": 1.12,
        "South": 1.00,
        "East": 0.86,
        "West": 1.25,
        "Central": 1.08,
        "Coastal": 0.78,
    }

    rows = []
    for position, period in enumerate(periods):
        technical_progress = 1.0 + 0.055 * position
        decarbonization = 1.0 - 0.07 * position
        for plant in plants:
            energy = 100.0 * scale[plant] * (1.0 + 0.02 * position)
            labor = 50.0 * scale[plant] * (1.0 - 0.01 * position)
            electricity = 82.0 * scale[plant] * management[plant] * technical_progress
            co2 = 2.4 * energy * emission_factor[plant] * decarbonization
            rows.append(
                {
                    "dmu": plant,
                    "period": period,
                    "energy": round(energy, 3),
                    "labor": round(labor, 3),
                    "electricity": round(electricity, 3),
                    "co2": round(co2, 3),
                }
            )
    return pd.DataFrame(rows)


def _network_2stage() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "dmu": ["A", "B", "C", "D", "E", "F", "G", "H"],
            "research_staff": [20, 24, 28, 34, 38, 42, 46, 50],
            "research_budget": [30, 33, 40, 45, 52, 56, 62, 68],
            "patents": [12, 16, 20, 21, 28, 27, 31, 36],
            "prototypes": [7, 9, 12, 11, 15, 14, 16, 19],
            "sales": [42, 56, 69, 61, 88, 76, 91, 112],
            "market_share": [4.2, 5.0, 6.1, 5.4, 7.3, 6.6, 7.8, 9.1],
        }
    )


def _dynamic_capacity_backlog() -> pd.DataFrame:
    """Theory-led good/bad carry-over account for dynamic SBM."""
    return pd.DataFrame(
        [
            {
                "organization": organization,
                "period": period,
                "resource": 1.0,
                "service": 1.0,
                "capacity": capacity,
                "backlog": backlog,
            }
            for period in (1, 2)
            for organization, capacity, backlog in (
                ("Prepared", 2.0, 1.0),
                ("Strained", 1.0, 2.0),
            )
        ]
    )


def _dynamic_network_power_demo() -> pd.DataFrame:
    """Theory-led utility panel for dynamic-network teaching and figures.

    The observations are deterministic and synthetic.  They are not the
    anonymous utilities used by Tone and Tsutsui (2014), whose raw panel was
    not published.
    """
    utilities = {
        "North": (1.00, 0.96, 1.02),
        "South": (1.20, 0.91, 1.07),
        "East": (1.45, 1.00, 0.98),
        "West": (0.90, 0.84, 1.14),
        "Central": (1.10, 0.89, 1.09),
        "Coastal": (1.35, 0.98, 1.00),
        "Metro": (1.55, 0.94, 1.04),
        "Rural": (0.78, 0.82, 1.18),
    }
    rows: list[dict[str, float | int | str]] = []
    for position, period in enumerate((2021, 2022, 2023, 2024)):
        technical_progress = 1.0 + 0.035 * position
        for utility, (scale, management, burden) in utilities.items():
            gross_power = 82.0 * scale * management * technical_progress
            delivered_power = gross_power * (0.91 + 0.06 * management)
            rows.append(
                {
                    "dmu": utility,
                    "period": period,
                    "fuel": round(
                        105.0 * scale * burden * (1.0 + 0.012 * position),
                        4,
                    ),
                    "generation_labor": round(
                        24.0 * scale * burden * (1.0 - 0.006 * position),
                        4,
                    ),
                    "gross_power": round(gross_power, 4),
                    "generation_reliability": round(
                        88.0 + 9.0 * management + 0.35 * position,
                        4,
                    ),
                    "grid_labor": round(
                        14.0 * scale * burden * (1.0 - 0.004 * position),
                        4,
                    ),
                    "delivered_power": round(delivered_power, 4),
                    "grid_reliability": round(
                        86.0 + 10.0 * management + 0.45 * position,
                        4,
                    ),
                    "service_labor": round(
                        11.0 * scale * burden * (1.0 - 0.003 * position),
                        4,
                    ),
                    "customers_served": round(
                        9.6 * scale * management * (1.0 + 0.028 * position),
                        4,
                    ),
                    "service_quality": round(
                        77.0 + 18.0 * management + 0.55 * position,
                        4,
                    ),
                    "generation_capacity": round(
                        92.0 * scale * management * (1.0 + 0.025 * position),
                        4,
                    ),
                    "maintenance_backlog": round(
                        6.5 * scale * burden * (1.0 - 0.035 * position * management),
                        4,
                    ),
                    "fuel_inventory": round(
                        13.0
                        * scale
                        * (1.0 + 0.018 * position)
                        * (1.04 - 0.04 * management),
                        4,
                    ),
                    "service_obligation": round(
                        7.5 * scale * (1.0 + 0.015 * position),
                        4,
                    ),
                }
            )
    return pd.DataFrame(rows)


def _economic_efficiency_4() -> pd.DataFrame:
    """Theory-led common case for cost, revenue, profit, and Nerlovian accounts."""
    return pd.DataFrame(
        {
            "plan": ["A", "B", "C", "D"],
            "resource": [4.0, 5.0, 3.0, 6.0],
            "standard_service": [6.0, 4.0, 5.0, 3.0],
            "premium_service": [2.0, 5.0, 1.0, 2.0],
            "price_resource": [2.0] * 4,
            "price_standard_service": [3.0] * 4,
            "price_premium_service": [5.0] * 4,
        }
    )


def _revenue_8x2() -> pd.DataFrame:
    """Eight-unit VRS revenue example from Pastor, Aparicio, and Zofío."""
    return pd.DataFrame(
        {
            "dmu": [str(value) for value in range(1, 9)],
            "input": [1.0] * 8,
            "output_1": [7.0, 4.0, 8.0, 3.0, 3.0, 8.0, 6.0, 1.5],
            "output_2": [7.0, 8.0, 4.0, 5.0, 3.0, 2.0, 4.0, 5.0],
            "price_output_1": [1.0] * 8,
            "price_output_2": [1.0] * 8,
        }
    )


def _revenue_5x2() -> pd.DataFrame:
    """Five-unit economic-efficiency example from Zofío and Prieto."""
    return pd.DataFrame(
        {
            "dmu": [str(value) for value in range(1, 6)],
            "input_1": [5.0, 2.0, 4.0, 4.0, 7.0],
            "input_2": [3.0, 4.0, 2.0, 8.0, 9.0],
            "output_1": [7.0, 10.0, 8.0, 5.0, 3.0],
            "output_2": [4.0, 8.0, 10.0, 4.0, 6.0],
            "price_input_1": [2.0] * 5,
            "price_input_2": [1.0] * 5,
            "price_output_1": [3.0] * 5,
            "price_output_2": [2.0] * 5,
        }
    )


_BUILDERS: dict[str, Callable[[], pd.DataFrame]] = {
    "clinic_capacity": _clinic_capacity,
    "community_hospital_capstone": _community_hospital_capstone,
    "coordination_hulls": _coordination_hulls,
    "dynamic_network_power_demo": _dynamic_network_power_demo,
    "economic_efficiency_4": _economic_efficiency_4,
    "frontier_1x1": _frontier_1x1,
    "metafrontier_groups": _metafrontier_groups,
    "range_directional_signed": _range_directional_signed,
    "zhou_ang_wang_non_chp_3": _zhou_ang_wang_non_chp_3,
    "ren_cas_directional_scale": _ren_cas_directional_scale,
    "slacks_2x2": _slacks_2x2,
    "dynamic_capacity_backlog": _dynamic_capacity_backlog,
    "productivity_panel": _productivity_panel,
    "revenue_5x2": _revenue_5x2,
    "revenue_8x2": _revenue_8x2,
    "environmental_panel": _environmental_panel,
    "network_2stage": _network_2stage,
}

_BUILDERS.update(
    {
        name: specification["builder"]
        for name, specification in _REPLACEMENT_SPECS.items()
    }
)

_BASE_INFO = {
    "clinic_capacity": DatasetInfo(
        name="clinic_capacity",
        title="Short-run clinic capacity",
        description=(
            "A four-clinic theory-led example that separates current operating "
            "performance from physical capacity supported by installed beds "
            "when staffing may adjust."
        ),
        roles={
            "dmu": "clinic",
            "fixed_inputs": ("beds",),
            "variable_inputs": ("staff_hours",),
            "outputs": ("visits",),
        },
        teaching_uses=(
            "physical capacity",
            "capacity-utilization decomposition",
            "technical performance versus unused installed capacity",
            "synthetic theory-led example",
        ),
    ),
    "community_hospital_capstone": DatasetInfo(
        name="community_hospital_capstone",
        title="Community hospital efficiency study",
        description=(
            "A deterministic 64-hospital synthetic raw roster for a complete "
            "efficiency-study workflow. Explicit reporting, structural-break, "
            "service-mandate, and referral-share fields produce 60 data-valid "
            "records, 52 broadly comparable district hospitals, and a "
            "48-hospital main comparison population before scores are viewed."
        ),
        roles={
            "dmu": "hospital_id",
            "inputs": (
                "clinical_fte",
                "support_fte",
                "nonpay_operating_spend_gbp_m",
            ),
            "outputs": (
                "quality_adjusted_discharges",
                "outpatient_encounters",
            ),
            "eligibility_fields": (
                "service_mandate",
                "tertiary_referral_share",
                "reporting_complete",
                "structural_break",
            ),
            "audit_fields": (
                "financial_year",
                "raw_inpatient_discharges",
                "case_mix_index",
                "quality_index",
            ),
        },
        teaching_uses=(
            "complete empirical-study workflow",
            "data-quality and peer-eligibility ledger",
            "input-oriented BCC efficiency",
            "SBM and peer-population sensitivity",
            "targets, peers, and result publication",
            "deterministic synthetic capstone",
        ),
    ),
    "economic_efficiency_4": DatasetInfo(
        name="economic_efficiency_4",
        title="Unified economic-efficiency operating plans",
        description=(
            "A four-plan theory-led case with one resource, two services, and "
            "common prices for comparing cost, revenue, profit, allocative, "
            "and Nerlovian performance accounts without changing the data."
        ),
        roles={
            "dmu": "plan",
            "inputs": ("resource",),
            "outputs": ("standard_service", "premium_service"),
            "input_prices": ("price_resource",),
            "output_prices": (
                "price_standard_service",
                "price_premium_service",
            ),
        },
        teaching_uses=(
            "cost efficiency",
            "revenue efficiency",
            "profit gap",
            "technical and allocative decomposition",
            "Nerlovian profit inefficiency",
            "exact analytic teaching case",
        ),
    ),
    "coordination_hulls": DatasetInfo(
        name="coordination_hulls",
        title="Distinct-organization coordination benchmark",
        description=(
            "A four-organization theory-led example that separates learning "
            "from one observed organization, coordinating a subset of "
            "distinct organizations, repeating complete operating templates, "
            "and continuously divisible scale assumptions."
        ),
        roles={
            "dmu": "organization",
            "inputs": ("resource",),
            "outputs": ("service",),
        },
        teaching_uses=(
            "free coordination hull",
            "binary subset aggregation",
            "FDH--FCH--FRH--CCR--VRS comparison",
            "synthetic theory-led oracle",
        ),
    ),
    "frontier_1x1": DatasetInfo(
        name="frontier_1x1",
        title="One-input, one-output frontier",
        description=(
            "A concave frontier with interior organizations for visual "
            "explanations of resource saving, output expansion, and scale."
        ),
        roles={"dmu": "dmu", "inputs": ("input",), "outputs": ("output",)},
        teaching_uses=("CCR/BCC", "frontier plots", "targets", "scale efficiency"),
    ),
    "metafrontier_groups": DatasetInfo(
        name="metafrontier_groups",
        title="Declared-group metafrontier oracle",
        description=(
            "A six-organization theory-led example with two declared "
            "technology groups. It separates performance within a group's "
            "opportunity set from proximity to the pooled metafrontier."
        ),
        roles={
            "dmu": "dmu",
            "group": "technology_group",
            "inputs": ("resource",),
            "outputs": ("service",),
        },
        teaching_uses=(
            "radial metafrontier",
            "group efficiency",
            "metatechnology ratio",
            "technology-gap-ratio alias",
            "exact analytic oracle",
        ),
    ),
    "range_directional_signed": DatasetInfo(
        name="range_directional_signed",
        title="Signed range-directional exact oracle",
        description=(
            "A three-organization rational theory example with negative input "
            "and desirable-output observations. It separates the focal-to-ideal "
            "directional target from the phase-one peer activity."
        ),
        roles={
            "dmu": "dmu",
            "inputs": ("input",),
            "outputs": ("output",),
        },
        teaching_uses=(
            "Portela--Thanassoulis--Simpson range directional measure",
            "signed finite production data",
            "translation invariance under VRS",
            "exact analytic oracle",
        ),
    ),
    "slacks_2x2": DatasetInfo(
        name="slacks_2x2",
        title="Two-input, two-output slack example",
        description=(
            "A small service-production example with radial and non-radial gaps."
        ),
        roles={
            "dmu": "dmu",
            "inputs": ("labor", "capital"),
            "outputs": ("service", "quality"),
        },
        teaching_uses=("slacks", "SBM", "peers", "target heatmaps"),
    ),
    "zhou_ang_wang_non_chp_3": DatasetInfo(
        name="zhou_ang_wang_non_chp_3",
        title="Non-CHP energy--carbon analytical account",
        description=(
            "A three-system, strictly positive teaching fixture derived from "
            "the non-CHP source equations in Zhou, Ang, and Wang (2012). It is "
            "not the article's unavailable country-level application data."
        ),
        roles={
            "dmu": "dmu",
            "inputs": ("fossil_energy",),
            "outputs": ("electricity",),
            "bad_outputs": ("co2",),
        },
        teaching_uses=(
            "non-radial directional energy and carbon accounts",
            "analytically derived oracle",
            "source-equation target reconstruction",
        ),
    ),
    "dynamic_capacity_backlog": DatasetInfo(
        name="dynamic_capacity_backlog",
        title="Dynamic capacity and backlog account",
        description=(
            "A theory-led synthetic two-organization, two-period account for "
            "good capacity and bad backlog carry-overs. The values are designed "
            "for exact hand reconstruction and are not published observations."
        ),
        roles={
            "dmu": "organization",
            "period": "period",
            "inputs": ("resource",),
            "outputs": ("service",),
            "good_carryovers": ("capacity",),
            "bad_carryovers": ("backlog",),
        },
        teaching_uses=(
            "scored good and bad carry-over management",
            "exact dynamic SBM account reconstruction",
            "adjacent-period continuity and terminal boundaries",
            "synthetic theory-led example",
        ),
    ),
    "productivity_panel": DatasetInfo(
        name="productivity_panel",
        title="Productivity change in operating performance and best practice",
        description=(
            "A deterministic balanced panel with changing production opportunities "
            "and unit-level operating performance."
        ),
        roles={
            "dmu": "dmu",
            "period": "period",
            "inputs": ("capital", "labor"),
            "outputs": ("output",),
        },
        teaching_uses=("Malmquist", "Luenberger", "EC/TC decomposition"),
    ),
    "ren_cas_directional_scale": DatasetInfo(
        name="ren_cas_directional_scale",
        title="Ren et al. CAS directional-scale example",
        description=(
            "The published 2016 cross-section of 16 basic research institutes "
            "in the Chinese Academy of Sciences, with staff in FTE, research "
            "expenditure and external funding in RMB million, and publication "
            "and patent counts."
        ),
        roles={
            "dmu": "dmu",
            "inputs": ("staff", "research_expenditure"),
            "outputs": (
                "external_funding",
                "high_sci_publications",
                "granted_patents",
            ),
        },
        teaching_uses=(
            "directional scale elasticity",
            "declared output-priority scenarios",
            "right- and left-hand directional returns to scale",
            "published numerical oracle",
        ),
    ),
    "revenue_5x2": DatasetInfo(
        name="revenue_5x2",
        title="CRS/VRS revenue-efficiency example",
        description=(
            "A five-unit, two-input, two-output example with unequal output "
            "prices that separates returns-to-scale and output-mix effects."
        ),
        roles={
            "dmu": "dmu",
            "inputs": ("input_1", "input_2"),
            "outputs": ("output_1", "output_2"),
            "input_prices": ("price_input_1", "price_input_2"),
            "output_prices": ("price_output_1", "price_output_2"),
        },
        teaching_uses=(
            "revenue efficiency",
            "return-to-dollar profitability",
            "CRS and VRS comparison",
            "radial projection versus revenue-maximizing activity",
            "cross-implementation numerical oracle",
        ),
    ),
    "revenue_8x2": DatasetInfo(
        name="revenue_8x2",
        title="VRS revenue-efficiency example",
        description=(
            "The eight-unit, two-output example used for the radial revenue "
            "decomposition in Pastor, Aparicio, and Zofío."
        ),
        roles={
            "dmu": "dmu",
            "inputs": ("input",),
            "outputs": ("output_1", "output_2"),
            "output_prices": ("price_output_1", "price_output_2"),
        },
        teaching_uses=(
            "revenue efficiency",
            "output technical and allocative decomposition",
            "cross-implementation numerical oracle",
        ),
    ),
    "environmental_panel": DatasetInfo(
        name="environmental_panel",
        title="Power plants with declining emissions intensity",
        description="A deterministic panel with good electricity and undesirable CO2.",
        roles={
            "dmu": "dmu",
            "period": "period",
            "inputs": ("energy", "labor"),
            "outputs": ("electricity",),
            "bad_outputs": ("co2",),
        },
        teaching_uses=("environmental DDF", "undesirable SBM", "green productivity"),
    ),
    "dynamic_network_power_demo": DatasetInfo(
        name="dynamic_network_power_demo",
        title="Synthetic multi-process utility trajectories",
        description=(
            "A deterministic four-period utility panel with generation, grid, "
            "and customer-service processes, two internal handoffs, and four "
            "economically distinct carry-over roles. It is theory-led teaching "
            "data, not the unpublished Tone--Tsutsui electricity sample."
        ),
        roles={
            "dmu": "dmu",
            "period": "period",
            "generation_inputs": ("fuel", "generation_labor"),
            "generation_outputs": ("generation_reliability",),
            "generation_to_grid": ("gross_power",),
            "grid_inputs": ("grid_labor",),
            "grid_outputs": ("grid_reliability",),
            "grid_to_service": ("delivered_power",),
            "service_inputs": ("service_labor",),
            "service_outputs": ("customers_served", "service_quality"),
            "good_carryovers": ("generation_capacity",),
            "bad_carryovers": ("maintenance_backlog",),
            "free_carryovers": ("fuel_inventory",),
            "fixed_carryovers": ("service_obligation",),
        },
        teaching_uses=(
            "Tone--Tsutsui dynamic network SBM",
            "within-period process coordination",
            "intertemporal performance attribution",
            "system, period, and process score visualization",
            "synthetic theory-led example",
        ),
    ),
    "network_2stage": DatasetInfo(
        name="network_2stage",
        title="Research commercialization network",
        description="Inputs create innovations, which become market outcomes.",
        roles={
            "dmu": "dmu",
            "stage_1_inputs": ("research_staff", "research_budget"),
            "intermediates": ("patents", "prototypes"),
            "stage_2_outputs": ("sales", "market_share"),
        },
        teaching_uses=("two-stage network DEA", "stage decomposition", "network plots"),
    ),
}

_BASE_INFO.update(
    {
        name: DatasetInfo(
            name=name,
            title=specification["title"],
            description=specification["description"],
            roles=specification["roles"],
            teaching_uses=specification["teaching_uses"],
        )
        for name, specification in _REPLACEMENT_SPECS.items()
    }
)


@dataclass(frozen=True, slots=True)
class _ResearchRecord:
    source_kind: DatasetSourceKind
    citation_identifiers: tuple[str, ...]
    oracle_status: DatasetOracleStatus


def _research(
    source_kind: DatasetSourceKind,
    *citation_identifiers: str,
    oracle_status: DatasetOracleStatus,
) -> _ResearchRecord:
    return _ResearchRecord(
        source_kind=source_kind,
        citation_identifiers=tuple(citation_identifiers),
        oracle_status=oracle_status,
    )


_RESEARCH = {
    "clinic_capacity": _research(
        "project_synthetic",
        oracle_status="teaching_only",
    ),
    "community_hospital_capstone": _research(
        "project_synthetic",
        oracle_status="teaching_only",
    ),
    "coordination_hulls": _research(
        "project_theory",
        oracle_status="analytical",
    ),
    "dynamic_capacity_backlog": _research(
        "project_theory",
        oracle_status="analytical",
    ),
    "dynamic_network_power_demo": _research(
        "project_synthetic",
        oracle_status="teaching_only",
    ),
    "economic_efficiency_4": _research(
        "project_theory",
        oracle_status="analytical",
    ),
    "environmental_panel": _research(
        "project_synthetic",
        oracle_status="teaching_only",
    ),
    "frontier_1x1": _research(
        "project_theory",
        oracle_status="analytical",
    ),
    "metafrontier_groups": _research(
        "project_theory",
        oracle_status="analytical",
    ),
    "network_2stage": _research(
        "project_synthetic",
        oracle_status="teaching_only",
    ),
    "productivity_panel": _research(
        "project_synthetic",
        oracle_status="teaching_only",
    ),
    "range_directional_signed": _research(
        "project_theory",
        oracle_status="analytical",
    ),
    "ren_cas_directional_scale": _research(
        "published_reproduction",
        "bibkey:ren2021directionalscale",
        "doi:10.1051/ro/2021131",
        oracle_status="published_reproduction",
    ),
    "revenue_5x2": _research(
        "external_implementation_example",
        "bibkey:zofio2006",
        "software:DataEnvelopmentAnalysis.jl@ca17532cd4de4e47d159cee563c05d9a0db6a61c",
        oracle_status="cross_implementation",
    ),
    "revenue_8x2": _research(
        "external_implementation_example",
        "bibkey:pastor2022benchmarking",
        "software:BenchmarkingEconomicEfficiency.jl@e98ca05217aeb74197fd51b89a4f7f2a3792ef87",
        oracle_status="cross_implementation",
    ),
    "slacks_2x2": _research(
        "project_theory",
        oracle_status="analytical",
    ),
    "zhou_ang_wang_non_chp_3": _research(
        "source_derived_theory",
        "doi:10.1016/j.ejor.2012.04.022",
        oracle_status="source_equation",
    ),
}

_RESEARCH.update(
    {
        name: _research(
            specification["source_kind"],
            oracle_status="analytical",
        )
        for name, specification in _REPLACEMENT_SPECS.items()
    }
)


_CLEARED_EXTERNAL_DATA_LICENSES: Mapping[str, tuple[str, str]] = MappingProxyType(
    {
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
)


# These project-origin approvals are deliberately independent of
# ``_EXPECTED_CONTENT_SHA256``.  Updating a builder and its expected regression
# hash therefore cannot silently carry the CC BY 4.0 approval to new content.
_CLEARED_PROJECT_DATA_LICENSES: Mapping[str, tuple[str, str]] = MappingProxyType(
    {
        "clinic_capacity": (
            "2326276b495c7fe6709ccca6214c2adf412917e9b5de11e22ed3848f00ccd346",
            "CC-BY-4.0",
        ),
        "community_hospital_capstone": (
            "f36aff2e248c2f3d08c042897c63154318e97df78ca5e9a9197944f074cd5463",
            "CC-BY-4.0",
        ),
        "coordination_hulls": (
            "765b52cd368e1966573553fb15620a9052ac2a4da846213936765f820eb62b26",
            "CC-BY-4.0",
        ),
        "dynamic_capacity_backlog": (
            "3ae253341568a3254d2249a2113974075c3f911b7f28a66ef836cf15a290816e",
            "CC-BY-4.0",
        ),
        "dynamic_network_power_demo": (
            "e0f40a1a3851aa0bfb72614a43ce232fda65d0d10d4498316c7e921f60759d20",
            "CC-BY-4.0",
        ),
        "economic_efficiency_4": (
            "7f47b5908b1b6dfa5c1cfcbbe8ad36ddd6e04dbd613e1e74de9434276597ebb8",
            "CC-BY-4.0",
        ),
        "environmental_panel": (
            "78c8d1abfd9208d8eb692e14cebd87f93e90c9a12f4669c6157a6249e35d4222",
            "CC-BY-4.0",
        ),
        "frontier_1x1": (
            "bd99da0c10379eefbc6873018cee9d9ffe836a778b14ad3c822829218d8273d4",
            "CC-BY-4.0",
        ),
        "metafrontier_groups": (
            "84dc9ce6d69e2be32e96045054ce3f1f15b4a0a72134aa290aaab067d82ae2c6",
            "CC-BY-4.0",
        ),
        "network_2stage": (
            "c68308be70ff56b86aac1761dfda6f3e744ab20df79783cdf5775fd9da5073a8",
            "CC-BY-4.0",
        ),
        "productivity_panel": (
            "ad465d73815cdb0291799ef7fadccaf29658f64b4a5a44819a79498d7f0243e1",
            "CC-BY-4.0",
        ),
        "range_directional_signed": (
            "c564f08eb1ef0a0f32c2d9f48a9433bb8adee5cae0e07641d914bc86090e64aa",
            "CC-BY-4.0",
        ),
        "slacks_2x2": (
            "14fd86d328c2088c32d0b3eb4afe5fa76ad01301e2524660c74efa705cf0c33d",
            "CC-BY-4.0",
        ),
        "zhou_ang_wang_non_chp_3": (
            "60b3e674708f7ad94cb9589d0480647c42871ed90bcd4af40681866b00478c19",
            "CC-BY-4.0",
        ),
        "open_service_chain": (
            "7743e3d3efdba20f0297f7feb47378859f9cc5601df35f55a6ff11765e804468",
            "CC-BY-4.0",
        ),
        "three_process_service_chain": (
            "9815ba52ab54336ca3cc0853b9077672b64e3edbcbb259127737eb2105ae9d51",
            "CC-BY-4.0",
        ),
        "crs_free_link_service_chain": (
            "a0855b81e607914d0eeb5fcfa6f326743588b9cc026f1aeeb957e240f1d3de43",
            "CC-BY-4.0",
        ),
        "two_stage_public_service": (
            "21de69ded29f300acd4aa7fa9c88ecbc8bc78c2ccec4a6a5319031b31fc07210",
            "CC-BY-4.0",
        ),
        "environmental_recovery_chain": (
            "b29eb956318cc2673fc826513800d07e362eca189643d5e7c5ab1fea03a3292b",
            "CC-BY-4.0",
        ),
        "environmental_circular_chain": (
            "6829df95a5b472093c29898d42800988d3f9406cd62d4c72ababd88d43a086c8",
            "CC-BY-4.0",
        ),
        "strategic_peer_service": (
            "81748dcf3917e17ca889a3b5aa7789f366bea28e1dc48273a749629f7284309f",
            "CC-BY-4.0",
        ),
        "multiperiod_trajectory_contrast": (
            "4873e3bd746f3d8fc0ae68604cfc70c32c8cbcbd4a6884e011b3fc0b53283377",
            "CC-BY-4.0",
        ),
        "dynamic_carryover_portfolio": (
            "5189e5cf8c19d197e11539046de63d36a2f2f23998ad7afd3c93bc393e15c939",
            "CC-BY-4.0",
        ),
        "directional_super_multivariate_stress": (
            "3d6b49ffcc975998b8ec53153f9859d3b1c2d2d285c65f9f115dd1557f143bbe",
            "CC-BY-4.0",
        ),
        "sbm_slack_contrast": (
            "fb64ce63486e130ecfedfed9cc313dbdcacb16e32f5e7dcefabf9c7ec299578d",
            "CC-BY-4.0",
        ),
        "super_sbm_peer_replacement": (
            "eba2e104f3ceda0732f03f793221f1910de0d3df3e9988763814df1b353fbe28",
            "CC-BY-4.0",
        ),
        "environmental_disposability_contrast": (
            "20d836060604a9845e63f00f74f10117576bf140233efe689e352edaf530f933",
            "CC-BY-4.0",
        ),
        "by_production_component_bottleneck": (
            "450c8779c30448ae066243657024a48db7ce01b31bc5e7da67e805f0c0cc5a8b",
            "CC-BY-4.0",
        ),
        "cost_mix_choice": (
            "ee7f40afa9a318ba12bb2996cb5ad4d5ef26bfe15e8185763cb1c5c5bb0b82ba",
            "CC-BY-4.0",
        ),
        "integer_coordination_hulls": (
            "27cf0c63018cf6b102d86e7ea396d7d18ec58b8a27f35a4ea2463904a382b6a5",
            "CC-BY-4.0",
        ),
    }
)

_CLEARED_DATA_LICENSES: Mapping[str, tuple[str, str]] = MappingProxyType(
    {
        **_CLEARED_PROJECT_DATA_LICENSES,
        **_CLEARED_EXTERNAL_DATA_LICENSES,
    }
)


_TOPOLOGY_ROLES: Mapping[str, Mapping[str, str | tuple[str, ...]]] = {}


def _declared_variable(
    name: str,
    *,
    unit: str,
    definition: str,
) -> DatasetVariableInfo:
    return DatasetVariableInfo(
        name=name,
        unit_status="declared",
        unit=unit,
        definition_status="declared",
        definition=definition,
    )


def _described_variable(
    name: str,
    *,
    unit_status: DatasetUnitStatus,
    definition: str,
) -> DatasetVariableInfo:
    return DatasetVariableInfo(
        name=name,
        unit_status=unit_status,
        unit=None,
        definition_status="declared",
        definition=definition,
    )


_VARIABLE_OVERRIDES: Mapping[str, Mapping[str, DatasetVariableInfo]] = {
    "community_hospital_capstone": {
        "hospital_id": _described_variable(
            "hospital_id",
            unit_status="not_applicable",
            definition="Synthetic identifier of one hospital record.",
        ),
        "financial_year": _described_variable(
            "financial_year",
            unit_status="not_applicable",
            definition="Financial-year label shared by the cross-section.",
        ),
        "service_mandate": _described_variable(
            "service_mandate",
            unit_status="not_applicable",
            definition=(
                "Synthetic institutional classification used to identify "
                "hospitals with a comparable district-general service role."
            ),
        ),
        "tertiary_referral_share": _described_variable(
            "tertiary_referral_share",
            unit_status="unitless",
            definition=(
                "Synthetic proportion of activity attributed to tertiary "
                "referral work; the main roster requires at most 0.15."
            ),
        ),
        "reporting_complete": _described_variable(
            "reporting_complete",
            unit_status="not_applicable",
            definition=(
                "Boolean indicating whether the annual production return is "
                "complete enough for the data-valid roster."
            ),
        ),
        "structural_break": _described_variable(
            "structural_break",
            unit_status="not_applicable",
            definition=(
                "Boolean indicating an organizational break that prevents the "
                "record from reflecting a stable full-year operating situation."
            ),
        ),
        "clinical_fte": _declared_variable(
            "clinical_fte",
            unit="full-time-equivalent persons",
            definition="Synthetic annual average clinical workforce input.",
        ),
        "support_fte": _declared_variable(
            "support_fte",
            unit="full-time-equivalent persons",
            definition="Synthetic annual average support workforce input.",
        ),
        "nonpay_operating_spend_gbp_m": _declared_variable(
            "nonpay_operating_spend_gbp_m",
            unit="GBP million in constant synthetic 2025 prices per financial year",
            definition="Synthetic non-pay operating expenditure input.",
        ),
        "raw_inpatient_discharges": _declared_variable(
            "raw_inpatient_discharges",
            unit="discharges per financial year",
            definition=(
                "Generated inpatient-discharge count before case-mix and "
                "quality adjustment."
            ),
        ),
        "case_mix_index": _described_variable(
            "case_mix_index",
            unit_status="unitless",
            definition=(
                "Generated relative case-complexity index used only to "
                "construct the adjusted inpatient output."
            ),
        ),
        "quality_index": _described_variable(
            "quality_index",
            unit_status="unitless",
            definition=(
                "Generated service-quality index used only to construct the "
                "adjusted inpatient output."
            ),
        ),
        "quality_adjusted_discharges": _declared_variable(
            "quality_adjusted_discharges",
            unit="adjusted discharge equivalents per financial year",
            definition=(
                "Raw inpatient discharges multiplied by the generated "
                "case-mix and quality indexes."
            ),
        ),
        "outpatient_encounters": _declared_variable(
            "outpatient_encounters",
            unit="completed encounters per financial year",
            definition="Generated annual completed outpatient service output.",
        ),
    },
    "ren_cas_directional_scale": {
        "staff": _declared_variable(
            "staff",
            unit="full-time-equivalent persons",
            definition="Research staff employed by the institute.",
        ),
        "research_expenditure": _declared_variable(
            "research_expenditure",
            unit="RMB million",
            definition="Research expenditure reported for the institute.",
        ),
        "external_funding": _declared_variable(
            "external_funding",
            unit="RMB million",
            definition="External research funding obtained by the institute.",
        ),
        "high_sci_publications": _declared_variable(
            "high_sci_publications",
            unit="count",
            definition="Count of high-SCI publications.",
        ),
        "granted_patents": _declared_variable(
            "granted_patents",
            unit="count",
            definition="Count of granted patents.",
        ),
    },
}


_EXPECTED_CONTENT_SHA256: Mapping[str, str] = {
    "clinic_capacity": (
        "2326276b495c7fe6709ccca6214c2adf412917e9b5de11e22ed3848f00ccd346"
    ),
    "community_hospital_capstone": (
        "f36aff2e248c2f3d08c042897c63154318e97df78ca5e9a9197944f074cd5463"
    ),
    "coordination_hulls": (
        "765b52cd368e1966573553fb15620a9052ac2a4da846213936765f820eb62b26"
    ),
    "dynamic_capacity_backlog": (
        "3ae253341568a3254d2249a2113974075c3f911b7f28a66ef836cf15a290816e"
    ),
    "dynamic_network_power_demo": (
        "e0f40a1a3851aa0bfb72614a43ce232fda65d0d10d4498316c7e921f60759d20"
    ),
    "economic_efficiency_4": (
        "7f47b5908b1b6dfa5c1cfcbbe8ad36ddd6e04dbd613e1e74de9434276597ebb8"
    ),
    "environmental_panel": (
        "78c8d1abfd9208d8eb692e14cebd87f93e90c9a12f4669c6157a6249e35d4222"
    ),
    "frontier_1x1": (
        "bd99da0c10379eefbc6873018cee9d9ffe836a778b14ad3c822829218d8273d4"
    ),
    "metafrontier_groups": (
        "84dc9ce6d69e2be32e96045054ce3f1f15b4a0a72134aa290aaab067d82ae2c6"
    ),
    "network_2stage": (
        "c68308be70ff56b86aac1761dfda6f3e744ab20df79783cdf5775fd9da5073a8"
    ),
    "productivity_panel": (
        "ad465d73815cdb0291799ef7fadccaf29658f64b4a5a44819a79498d7f0243e1"
    ),
    "range_directional_signed": (
        "c564f08eb1ef0a0f32c2d9f48a9433bb8adee5cae0e07641d914bc86090e64aa"
    ),
    "ren_cas_directional_scale": (
        "b187f3a441416e38534a3f527543dabf9d1f13fb5d53c24dce956907f9c99f21"
    ),
    "revenue_5x2": ("227cad33f14bc4ea78e2c3851c51ed5bd73e0ea1f49414db2b7c9bb171a57b4c"),
    "revenue_8x2": ("ec2703511209e49a4b5da53222b6a45ef7dab963925358019dedd475ab9b91a9"),
    "slacks_2x2": ("14fd86d328c2088c32d0b3eb4afe5fa76ad01301e2524660c74efa705cf0c33d"),
    "zhou_ang_wang_non_chp_3": (
        "60b3e674708f7ad94cb9589d0480647c42871ed90bcd4af40681866b00478c19"
    ),
}

_EXPECTED_CONTENT_SHA256 = MappingProxyType(
    {
        **_EXPECTED_CONTENT_SHA256,
        **{
            name: specification["content_sha256"]
            for name, specification in _REPLACEMENT_SPECS.items()
        },
    }
)


def _canonical_cell(value: object) -> list[str]:
    if value is None or value is pd.NA or value is pd.NaT:
        return ["null", ""]
    if isinstance(value, bool):
        return ["bool", "true" if value else "false"]
    if isinstance(value, Integral):
        return ["int", str(int(value))]
    if isinstance(value, Real):
        number = float(value)
        if pd.isna(number):
            return ["null", ""]
        return ["float", number.hex()]
    if isinstance(value, str):
        return ["str", value]
    raise TypeError(
        "built-in dataset fingerprints support only scalar strings, numbers, "
        f"booleans, and missing values; received {type(value).__name__!r}"
    )


def _content_sha256(frame: pd.DataFrame) -> str:
    if frame.columns.has_duplicates or not all(
        isinstance(column, str) and column for column in frame.columns
    ):
        raise ValueError("built-in datasets require unique non-empty string columns")
    payload = {
        "schema": "deapack.dataset-content.v1",
        "columns": list(frame.columns),
        "rows": [
            [_canonical_cell(value) for value in row]
            for row in frame.itertuples(index=False, name=None)
        ],
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _default_variable_info(
    name: str, *, roles: Mapping[str, object]
) -> DatasetVariableInfo:
    role_names = {
        role_name
        for role_name in ("dmu", "period", "group")
        if roles.get(role_name) == name
    }
    if "dmu" in role_names:
        return DatasetVariableInfo(
            name=name,
            unit_status="not_applicable",
            unit=None,
            definition_status="self_describing",
            definition="Identifier of the evaluated organization or operating unit.",
        )
    if "period" in role_names:
        return DatasetVariableInfo(
            name=name,
            unit_status="not_applicable",
            unit=None,
            definition_status="self_describing",
            definition="Label identifying the observation period.",
        )
    if "group" in role_names:
        return DatasetVariableInfo(
            name=name,
            unit_status="not_applicable",
            unit=None,
            definition_status="self_describing",
            definition="Declared operating-technology group label.",
        )
    return DatasetVariableInfo(
        name=name,
        unit_status="unspecified",
        unit=None,
        definition_status="unspecified",
        definition=None,
    )


def _finalize_dataset_info(name: str, base: DatasetInfo) -> DatasetInfo:
    frame = _BUILDERS[name]()
    if base.name != name:
        raise ValueError(f"dataset registry key {name!r} disagrees with metadata name")
    topology = _TOPOLOGY_ROLES.get(name, {})
    column_roles = {
        role: values for role, values in base.roles.items() if role not in topology
    }
    columns = set(frame.columns)
    for role, values in column_roles.items():
        names = (values,) if isinstance(values, str) else values
        missing = set(names).difference(columns)
        if missing:
            raise ValueError(
                f"dataset {name!r} column role {role!r} references missing "
                f"columns {sorted(missing)!r}"
            )
    if set(base.roles) != set(column_roles) | set(topology):
        raise ValueError(f"dataset {name!r} roles are not fully classified")
    variables = {
        column: _default_variable_info(column, roles=base.roles)
        for column in frame.columns
    }
    overrides = _VARIABLE_OVERRIDES.get(name, {})
    unknown_overrides = set(overrides).difference(columns)
    if unknown_overrides:
        raise ValueError(
            f"dataset {name!r} has metadata for absent variables "
            f"{sorted(unknown_overrides)!r}"
        )
    variables.update(overrides)
    digest = _content_sha256(frame)
    expected_digest = _EXPECTED_CONTENT_SHA256.get(name)
    if expected_digest is not None and digest != expected_digest:
        raise ValueError(
            f"dataset {name!r} content changed: expected {expected_digest}, "
            f"got {digest}"
        )
    record = _RESEARCH[name]
    approved_license = _CLEARED_DATA_LICENSES.get(name)
    license_identifier = (
        approved_license[1]
        if approved_license is not None and approved_license[0] == digest
        else None
    )
    provenance = DatasetProvenance(
        source_kind=record.source_kind,
        citation_status=("identified" if record.citation_identifiers else "none"),
        citation_identifiers=record.citation_identifiers,
        # Clearance is bound to the independent exact-hash maps above.  A
        # change to a builder and its expected regression hash does not update
        # those rights mappings automatically.
        redistribution_status=(
            "cleared" if license_identifier is not None else "unknown"
        ),
        license_identifier=license_identifier,
        oracle_status=record.oracle_status,
    )
    return replace(
        base,
        provenance=provenance,
        column_roles=column_roles,
        topology=topology,
        variables=variables,
        content_sha256=digest,
    )


if (
    set(_BUILDERS) != set(_BASE_INFO)
    or set(_BUILDERS) != set(_RESEARCH)
    or set(_BUILDERS) != set(_EXPECTED_CONTENT_SHA256)
):
    raise ValueError(
        "dataset builders, base metadata, research provenance, and expected "
        "content fingerprints must use exactly the same registry keys"
    )


_INFO: Mapping[str, DatasetInfo] = MappingProxyType(
    {name: _finalize_dataset_info(name, _BASE_INFO[name]) for name in _BUILDERS}
)


def list_datasets() -> tuple[DatasetInfo, ...]:
    """Return metadata for built-in deterministic datasets."""
    return tuple(_INFO[name] for name in _BUILDERS)


def dataset_info(name: str) -> DatasetInfo:
    """Return metadata for one built-in dataset."""
    try:
        return _INFO[name]
    except KeyError as error:
        replacement = RETIRED_TO_REPLACEMENT.get(name)
        if replacement is not None:
            raise KeyError(
                f"dataset {name!r} was retired for the rights-safe 2.0 "
                f"catalogue; use {replacement!r}. No data alias is provided."
            ) from error
        choices = ", ".join(_BUILDERS)
        raise KeyError(f"unknown dataset {name!r}; choose from: {choices}") from error


def load_dataset(name: str) -> pd.DataFrame:
    """Return a fresh DataFrame for a built-in deterministic dataset."""
    try:
        return _BUILDERS[name]().copy()
    except KeyError as error:
        replacement = RETIRED_TO_REPLACEMENT.get(name)
        if replacement is not None:
            raise KeyError(
                f"dataset {name!r} was retired for the rights-safe 2.0 "
                f"catalogue; use {replacement!r}. No data alias is provided."
            ) from error
        choices = ", ".join(_BUILDERS)
        raise KeyError(f"unknown dataset {name!r}; choose from: {choices}") from error


def retired_dataset_migrations() -> Mapping[str, str]:
    """Return the immutable retired-ID to replacement-ID migration map."""

    return RETIRED_TO_REPLACEMENT


__all__ = [
    "DatasetInfo",
    "DatasetProvenance",
    "DatasetVariableInfo",
    "dataset_info",
    "list_datasets",
    "load_dataset",
    "retired_dataset_migrations",
]
