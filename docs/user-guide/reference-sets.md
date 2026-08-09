# Reference technologies

Reference construction is conceptually independent of the efficiency measure.
DEAPack's base candidate-row builder is shared by the audited radial,
Additive/RAM, ordinary SBM, and ordinary DDF routes, as well as several
specialist routes that do not expose this policy. A new comparison policy
becomes public for each model only after its result and failure semantics have
been audited. It is important to distinguish three questions:

1. **Comparison population:** which organizations are economically eligible
   to provide a benchmark?
2. **Temporal information set:** which periods of those organizations are
   visible to the comparison?
3. **Evaluation exclusions:** does a named protocol remove or modify an
   otherwise eligible observation, as in leave-one-out super-efficiency?

Peers with positive fitted intensities and maximal or global reference sets
are model results. They are not any of these three input policies.

## Declare the comparison population at the data boundary

For a cross-sectional study in any supported model, the most transparent
workflow is to keep
the complete candidate ledger and construct `DEAData` only from rows that pass
the named, pre-specified eligibility rule:

```python
from deapack import BCC, DEAData

eligible = (
    frame["mission"].eq("district")
    & frame["operating_environment"].eq("urban")
    & frame["common_measurement_protocol"]
    & frame["service_contract"].eq("standard")
)
study_frame = frame.loc[eligible].copy()

data = DEAData.from_frame(
    study_frame,
    dmu="hospital",
    inputs=("clinical_hours", "staffed_bed_days"),
    outputs="risk_adjusted_episodes",
)
result = BCC(orientation="input", compute_slacks=False).fit(data)
```

`frame` remains the auditable candidate roster; `study_frame` is the eligible
comparison population; and `result.peers(dmu_id)` reports the positive fitted
intensities for one evaluated observation. These are three different objects.
Filtering must be based on institutional and measurement evidence available
before the scores are inspected. Repeating the fit after a defensible
pre-specified alternative rule is a sensitivity analysis; deleting a demanding
observation because it became an active peer is result-driven model selection.

Do not pass operating-environment labels into `inputs` merely to avoid making
an explicit population decision. An external condition is not a consumed
resource unless the production account supplies an economic reason for that
role. Preserve excluded rows and the reasons for exclusion in the study audit
ledger rather than silently dropping them.

```python
from deapack import BCC, ReferenceSpec

model = BCC(reference=ReferenceSpec("sequential"))
```

The current `ReferenceSpec` is a backward-compatible convenience interface.
Its implemented builders primarily encode the temporal information set:

- `auto`: all eligible rows for a cross section and contemporaneous rows for a
  panel;
- `global`: all study periods, viewed retrospectively;
- `contemporaneous`: the evaluated observation's period;
- `sequential`: the evaluated period and all earlier periods;
- `window`: explicit numbers of ordered periods before and after;
- `biennial`: the evaluated period and the following observed period;
- `custom`: one explicit set of global `DEAData` row positions, currently
  combining population and time membership at a low level.

For a cross section, `global` and “all eligible rows” select the same rows,
but they should not be interpreted as the same concept. The former is a
temporal policy that becomes degenerate when there is only one period; the
latter is a comparison-population decision. A group, custom, or future
spatial-eligibility policy can be combined conceptually with any supported
temporal policy.

Period windows operate on the declared order, not arithmetic such as
`year + 1`. This supports gaps, dates, and non-integer labels.

The current custom-reference subset is intentionally low level:

```python
custom = ReferenceSpec("custom", custom_rows=[0, 4, 7])
```

`custom_rows` uses the row order supplied to `DEAData.from_frame`; it must be
non-empty, unique, and nonnegative, and positions are range checked when the
reference plan is built. It is a membership set: DEAPack canonicalizes the
positions in ascending order, so their supplied order cannot encode a peer
preference or change the study identity. The same selected set is used for
every evaluated observation. In panel data, a DMU identifier can occur once
per period, so an identifier alone is not a safe substitute for a global row
position.

## Observation-specific comparison eligibility

`PeerEligibility` declares **candidate** comparison rights before fitting;
`result.peers(...)` still reports only solver-selected positive intensities
afterward. The same source-neutral contract is available on the audited
classical black-box constructors:

| Family | Constructors and exact aliases | Measure-specific point that remains unchanged |
|---|---|---|
| radial | `RadialDEA`, `CCR`, `BCC`, `CCRInput`, `CCROutput`, `BCCInput`, `BCCOutput` | orientation, RTS, and any fixed slack-completion recipe |
| additive | `AdditiveDEA`, `WeightedAdditiveDEA` | physical slack weights and the unbounded additive distance |
| range adjusted | `RangeAdjustedDEA`, `RAM` | one common full-data range normalization and global base policy |
| slacks based | `SlacksBasedDEA` / `SBM` / `ERG`; `InputOrientedSlacksBasedDEA` / `InputSBM` / `InputRussell`; `OutputOrientedSlacksBasedDEA` / `OutputSBM` / `OutputRussell` | evaluated-value normalization and orientation-specific objective |
| directional | `DirectionalDistanceDEA`, `DDF` | the declared resource-saving and service-gain programme |

The policy is also available on four environmental mother-model routes:

| Environmental production account | Public constructors | What the restriction changes — and what it does not |
|---|---|---|
| joint-production DDF | `EnvironmentalDirectionalDistanceDEA` / `EnvironmentalDDF` | changes only the admitted comparison operations; the declared strong-disposal or legacy equality formulation remains intact |
| common-factor weak-disposal DDF | `CommonFactorWeakDisposalDDF` | retains the CRS common-factor weak-disposal account |
| Chung--Färe--Grosskopf output DDF | `ChungFareGrosskopfDDF` | retains the fixed-resource, observed good/bad-output direction and its signed external-distance interpretation |
| separable strong-disposal SBM | `UndesirableSlacksBasedDEA` / `UndesirableSBM` | retains its independently adjustable desirable- and bad-output slack account |

For these routes, the declared eligible population is intersected with the
chosen temporal/reference policy before the environmental programme is solved.
It does not convert strong disposal into weak disposal, turn a common-factor
technology into an activity-specific one, or alter the meaning of the reported
environmental distance or SBM score.

The policy is not automatically available on activity-specific weak disposal,
by-production, material-balance, non-separable SBM, Zhou--Ang--Wang,
environmental productivity, economic, network, dynamic, non-convex, or other
specialist families. Shared reference-building code does not by itself
authorize a public constructor.

The keyed constructor is the preferred empirical interface. Cross sections
use exact DMU identifiers. Panels use exact `(dmu_id, period)` keys, so no row
position or period is inferred:

```python
import pandas as pd

from deapack import (
    BCC,
    DEAData,
    PeerEligibility,
    PeerEligibilityProvenance,
    ReferenceSpec,
)

frame = pd.DataFrame(
    {
        "branch": ["A", "B", "C", "D"],
        "staff_hours": [12.0, 10.0, 14.0, 9.0],
        "completed_cases": [10.0, 11.0, 12.0, 9.0],
    }
)
data = DEAData.from_frame(
    frame,
    dmu="branch",
    inputs="staff_hours",
    outputs="completed_cases",
)

provenance = PeerEligibilityProvenance(
    rule_name="same_service_contract_v1",
    source="service-contract comparability review dated 2026-07-01",
    comparison_population="four audited community branches",
    decision_owner="regional operations review board",
    validity_period="2026 financial year",
)
eligibility = PeerEligibility.by_key(
    {
        "A": ("A", "B", "C"),
        "B": ("A", "B", "C"),
        "C": ("A", "B", "C"),
        "D": ("A", "B", "C"),
    },
    provenance=provenance,
)

result = BCC(
    orientation="input",
    reference=ReferenceSpec("global"),
    peer_eligibility=eligibility,
    compute_slacks=False,
).fit(data)

result.summary()[
    [
        "dmu_id",
        "base_reference_size",
        "reference_size",
        "self_in_reference",
        "score",
    ]
]
eligibility.audit_frame(data).head()
```

All four observations are evaluated. The global base policy initially admits
four candidates, while the declared comparison rule leaves three. D is not
silently reinserted into its own comparison population, so
`self_in_reference=False` for that row. A singleton population is permitted
and disclosed; an empty intersection fails before any optimization call.

The same `eligibility` object can be passed to any compatible constructor in
the table above. That consistency holds the institutional evidence rule fixed
while the analyst asks a different management question. It does not make a
radial score, an additive distance, an SBM score, and a directional distance
interchangeable.

For low-level generated designs,
`PeerEligibility.by_row(rows_by_observation, provenance=...)` uses exact global
row positions. Its outer sequence must contain one set per evaluated row, and
its meaning is deliberately bound to the `DEAData` row order. Both constructors
copy and freeze their inputs, reject unknown or duplicate candidates, and
provide `audit_frame(data)` without duplicating the full edge relation into
every fitted result.

Key alignment is deliberately type-strict. Portable built-in strings,
Booleans, integers, finite floats, dates, datetimes, exact pandas timestamps,
and tuples of those values have distinct encodings; for example, integer
`2020` is not silently equated with float `2020.0`. Common NumPy string,
Boolean, integer, and floating scalars are normalized to those built-in forms.
Ambiguous application objects, arbitrary real-number classes, and NumPy
`datetime64`/`timedelta64` keys fail closed. Use `by_row` when identifiers
cannot be represented by the portable keyed schema.

The result's `peer_eligibility` metadata contains the declared rule provenance,
edge and population counts, composition rule, and domain-separated
fingerprints. It also states `categorical_interpretation="not_claimed"`.
Supplying nominal or ordered labels, fitting separate groups, or building this
mapping does not by itself implement a named categorical DEA model.

Every authorized summary reports the size of the base information set as
`base_reference_size`, the effective intersection as `reference_size`, and
whether self remains admissible as `self_in_reference`. Metadata classifies a
fit as self, mixed, or fully external appraisal from the actual effective
populations. Reference-frequency analysis for eligibility-conditioned fits
has not yet completed its separate estimand and validation audit, so
`result.reference_frequency()` fails closed for every such result in this
release. This remains true when a particular declaration happens to be
all-to-all: removing a nontrivial rule after fitting could change selected-plan
frequency and would no longer describe the fitted study design.

RAM requires one additional distinction. Its ranges are calculated once from
the complete `DEAData` admitted by the global base policy, before eligibility
is applied; they are not recalculated for each observation's restricted
population. Metadata labels this scope
`base_global_data_before_peer_eligibility`. A restricted RAM fit is therefore
a configurable package extension rather than the exact full self-inclusive
source profile, and RAM continues to reject contemporaneous, window, and
custom base policies.

## How the three policies compose

For evaluated observation $o$, let $P_o$ be the rows admitted by the
comparison-population policy, $I_o$ the rows admitted by the temporal policy,
and $X_o$ any rows removed by the evaluation protocol. The technology is
built from

$$
B_o=(P_o\cap I_o)\setminus X_o.
$$

The hull construction is a further decision. Enveloping the selected raw
observations, taking a non-convex union of group technologies, and
convexifying that union need not produce the same opportunities. Accordingly:

- group eligibility is not itself a meta-frontier;
- a meta-technology is not merely a row filter;
- leave-one-out is not a new temporal information set;
- a global temporal benchmark is not a “global reference set” in the
  alternate-optima literature.

The authorized classical core and the four environmental routes listed above
separate $P_o$ and $I_o$ through `PeerEligibility` and `ReferenceSpec`.
Evaluation exclusions remain part of source-qualified protocols, and other
model families have not automatically inherited the public policy. Every
empirical report should still state the comparison population, time rule,
exclusions, hull construction, and sample vintage explicitly rather than
relying on the word “reference.” Inspect the exact eligibility audit and each
fitted peer plan separately rather than removing the declared rule after
fitting.

Location needs the same care. Geographic proximity can restrict the eligible
population, enter a conditional frontier as an operating condition, represent
a genuine production spillover between neighboring organizations, or induce
dependence that changes statistical inference. These are different designs,
not interchangeable meanings of a future `spatial` option.
