# Dataset utilities

```{autoclass} deapack.DatasetInfo
:members:
```

```{autoclass} deapack.DatasetProvenance
:members:
```

```{autoclass} deapack.DatasetVariableInfo
:members:
```

```{autofunction} deapack.load_dataset
```

```{autofunction} deapack.list_datasets
```

```{autofunction} deapack.dataset_info
```

## Research metadata contract

Every built-in dataset exposes deeply immutable metadata alongside a fresh
DataFrame. The original `roles` mapping remains available for existing code,
while two non-overlapping views make it machine-verifiable:

- `column_roles` contains only role assignments whose values are actual
  DataFrame columns; and
- `topology` contains process names or other graph labels that are not data
  columns.

The `variables` mapping has exactly one `DatasetVariableInfo` for every
physical column. A known source unit is recorded with
`unit_status="declared"`. Identifiers use `"not_applicable"`; a quantity whose
unit or definition has not been established from maintained evidence uses the
controlled value `"unspecified"`. DEAPack does not infer a unit from a column
name.

```python
from deapack import dataset_info, load_dataset

info = dataset_info("ren_cas_directional_scale")
frame = load_dataset(info.name)

assert set(info.variables) == set(frame.columns)
assert info.variables["staff"].unit == "full-time-equivalent persons"
assert info.column_roles["inputs"] == ("staff", "research_expenditure")
```

`provenance.source_kind` distinguishes project theory data, project synthetic
data, published reproductions, source-derived theory fixtures, and examples
transcribed from an external implementation. `citation_status="none"` is an
explicit statement for project-created data without a source-data citation;
`"identified"` requires at least one stable `bibkey:`, `doi:`, or software
identifier. `oracle_status` describes the evidential use of the fixture, not
the strength of every model that might be fitted to it.

Dataset-content licensing is kept separate from the Python package license.
All 33 current records have exact content-hash mappings: the 30
project-created or independently selected fixtures and the Ren dataset use
`CC-BY-4.0`, while `revenue_5x2` and `revenue_8x2` retain upstream `MIT`.
See the repository `DATA_LICENSES.md` for exact fingerprints, origins,
attribution, and modification statements. A changed fingerprint requires a
new review rather than inheriting an earlier clearance.

`content_sha256` is a checked repository fingerprint of the ordered column
names and typed cell values under `fingerprint_schema`. It detects accidental
changes to a bundled fixture; it does not authenticate the original publisher
or replace a citation. Dataset metadata objects, their role mappings,
provenance, and variable records reject in-place mutation.

## Community-hospital study capstone

`community_hospital_capstone` is a deterministic, wholly synthetic raw roster
for teaching a complete cross-sectional efficiency study. It is not drawn from
or calibrated to a real health system. A NumPy `PCG64` stream with seed
`20260803` generates 64 hospital records for financial year 2025/26. The
builder maps the raw PCG64 integer stream through fixed uniform, Box--Muller,
and order-statistic transformations, then rounds continuous fields so the
fixture remains stable across supported platforms. It documents the complete
service and resource formula, six efficient reference hospitals, and four
fixed borderline-referral resource-mix adjustments.

For each hospital, size is a clipped lognormal draw, service mix is drawn from
`U(0.75, 1.25)`, case mix from `U(0.88, 1.22)`, and quality from
`U(0.94, 1.03)`. If `D` is raw inpatient discharges and `O` is outpatient
encounters, the two production outputs are
`Y1 = D * case_mix_index * quality_index` and `Y2 = O`. Their generated
resource requirements are:

```text
clinical = 115 + 0.052 Y1 + 0.0048 Y2
support  =  55 + 0.015 Y1 + 0.0025 Y2
non-pay  = 2.8 + 0.00055 Y1 + 0.00011 Y2
```

Ordinary records inflate each requirement by a common latent operating burden
and a small item-specific excess. The private builder docstring records the
remaining anchor and sensitivity overrides next to their executable code.

The raw roster deliberately preserves eligibility evidence rather than
returning only solver-ready observations. The following pre-score rules give
three auditable populations:

- complete reporting, no structural break, and finite positive production
  quantities give 60 data-valid records;
- retaining the `district_general` service mandate gives 52 broadly comparable
  hospitals; and
- requiring `tertiary_referral_share <= 0.15` gives the 48-hospital main roster.

The production model has three inputs (`clinical_fte`,
`support_fte`, and `nonpay_operating_spend_gbp_m`) and two outputs
(`quality_adjusted_discharges` and `outpatient_encounters`). Every raw column
has a declared meaning and unit status. The two intentionally incomplete
records remain outside the data-valid roster and must be screened before
constructing `DEAData`.

H048 is a built-in validation case. It has the same two outputs as H008 and
1.18, 1.12, and 1.15 times H008's inputs. On the 48-hospital main roster,
input-oriented BCC therefore reports efficiency `1 / 1.12`, with H008 as the
unit-weight peer. This known result helps verify the workflow; it is not a
claim about real hospital performance.

```python
import numpy as np

from deapack import BCCInput, DEAData, dataset_info, load_dataset

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

data = DEAData.from_frame(
    main,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
)
result = BCCInput().fit(data)
```

`economic_efficiency_4` is the deterministic, theory-led common case used to
compare cost, revenue, profit, technical--allocative, and Nerlovian accounts
without changing quantities or prices. Its metadata declares one input, two
outputs, and both price roles; it is an analytic teaching fixture rather than
a published-data reproduction.

`dynamic_capacity_backlog` is a deterministic two-organization, two-period
teaching account for the existing classic Dynamic SBM implementation. Its
metadata declares one ordinary resource, one service, good capacity, and bad
backlog. Under non-oriented VRS, Prepared scores one and Strained scores
exactly $0.5$, with input account $0.75$, output-expansion account $1.5$,
capacity target 2, and backlog target 1. It is a theory-led synthetic fixture,
not organizational observations or a published-data reproduction.

`dynamic_network_power_demo` is the deterministic synthetic teaching panel
for the public Tone--Tsutsui dynamic-network SBM. Its metadata distinguishes
process inputs and outputs, two internal handoffs, and good, bad, free, and
fixed carry-overs. It is not the unpublished raw utility panel from the
article.

`clinic_capacity` is a deterministic four-clinic research fixture retained
for the deferred short-run physical-capacity prototype. Its metadata declares
fixed inputs, variable inputs, and outputs separately, but the fixture is
neither a reproduction of the defining 1989 application nor evidence for a
public method. No physical-capacity API or tutorial is exposed in the current
release; the source equation audit and independent oracle are deferred to the
next version.

`metafrontier_groups` is the deterministic six-organization, two-group
analytic oracle for `MetafrontierDEA`. Its metadata declares the group column,
one resource input, and one desirable service output. It verifies group
efficiency, meta efficiency, MTR/TGR, and their reconstruction identity; it is
not the unpublished observation-level FAO application from O'Donnell, Rao,
and Battese (2008).

`range_directional_signed` is the three-organization exact rational oracle
for `RangeDirectionalDEA`. Its metadata declares one signed input and one
signed desirable output. For C, the non-oriented VRS result is
`beta=2/3`, `rdm_efficiency=1/3`, with peer weights `lambda_A=2/3` and
`lambda_B=1/3`. It is an independent theory dataset, not the confidential
bank-branch sample in Portela, Thanassoulis, and Simpson (2004).

`integer_coordination_hulls` is a three-plan neutral illustration for the
free-replicability hull. Its metadata identifies one resource input and one
service output and records its FDH--FRH--CCR comparison role.

`coordination_hulls` is a deterministic four-organization theory dataset for
the Green--Cook free-coordination-hull example. Its single additive resource
and service make the FDH--FCH--FRH--CCR nesting and the absence of a general
FCH--VRS ordering reproducible by hand.

`strategic_peer_service` is a neutral four-plan scorecard with three inputs
and two outputs. It is a teaching case for ordinary and game cross-efficiency
appraisal, not a paper-table reproduction.

`ren_cas_directional_scale` reproduces the 16 observations in Ren et al.
(2021), Table 1. Its metadata separates staff and research expenditure from
external funding, high-SCI publications, and granted patents, and records its
relative-directional scale-elasticity teaching and oracle role.

`environmental_recovery_chain` and `environmental_circular_chain` are neutral
environmental-network teaching cases. Their metadata separates external
inputs, intermediates, desirable outputs, undesirable outputs, and process
identities for structural and target checks.
