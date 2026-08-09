# M12 unified comparison rights for the classical black-box core

## Decision and evidence boundary

M12 extends the source-neutral comparison-population policy introduced in M11
across the classical black-box mother models. It adds no DEA model identity,
categorical role, source-named peer-restriction method, or generic restriction
language.

For evaluated observation $o$, let $I_o$ be the rows admitted by the base
`ReferenceSpec` and let $P_o$ be the comparison population declared before
fitting. Every authorized M12 estimator uses the same effective population

$$
B_o = I_o \cap P_o.
$$

The policy can remove an observation from the base information set but cannot
restore one excluded by the temporal or custom-reference rule. Positive fitted
intensities inside $B_o$ remain selected peer evidence, not declared inputs.

No remaining named mother-model candidate is source-ready at this checkpoint.
Färe--Primont, frontier-bootstrap inference, Banker--Morey categorical and
nondiscretionary leaves, ordinary cross-efficiency, Andersen--Petersen radial
super-efficiency, congestion, MPSS, and physical capacity retain their recorded
next-version or non-public status. Extending a source-neutral composition axis
does not weaken those gates.

## Explicitly authorized public surface

M12 authorizes `peer_eligibility` on these classical black-box constructors:

- the fixed radial recipes `CCRInput`, `CCROutput`, `BCCInput`, and
  `BCCOutput`, in addition to the existing `RadialDEA`, `CCR`, and `BCC`;
- `AdditiveDEA`, its exact alias `WeightedAdditiveDEA`, and
  `RangeAdjustedDEA` / `RAM`;
- `SlacksBasedDEA` / `SBM` / `ERG`,
  `InputOrientedSlacksBasedDEA` / `InputSBM` / `InputRussell`, and
  `OutputOrientedSlacksBasedDEA` / `OutputSBM` / `OutputRussell`; and
- `DirectionalDistanceDEA` / `DDF`.

The policy remains unavailable on undesirable-output SBM, environmental DDFs,
BAM, generalized and range-directional measures, multiplicative DEA, FDH/FRH/
FCH, economic, productivity, evaluation, network, panel-specific, and dynamic
families.
Shared access to `build_reference_plan` does not authorize a constructor. Each
later family requires its own feasibility, result-account, and provenance
audit.

In particular, `UndesirableSlacksBasedDEA` keeps an explicit constructor that
does not accept `peer_eligibility`; M12 must not enable it accidentally through
inheritance from `SlacksBasedDEA`.

## API and compilation contract

Every authorized constructor accepts only `PeerEligibility | None`, validates
the type before fitting, and passes the immutable declaration separately to
`build_reference_plan`. The policy does not become a field of `ReferenceSpec`:
the base information rule and the comparison-right decision remain distinct
composition axes.

The no-policy path must preserve all existing numerical results, semantic
tables, solve counts, and interpretation. The new common summary fields and
the corrected appraisal/membership metadata are deliberate schema additions,
not a claim of byte-identical tables.
With a policy, all families reuse the existing content-deduplicated
`ReferencePlan` set IDs. For $N$ evaluations, $E$ declared edges, and $K$
distinct effective populations:

- the relation is resolved once and no unconditional Boolean $N\times N$
  matrix is materialized;
- each family compiles exactly $K$ reference quantity blocks;
- Additive and SBM request exactly $N$ primary solves;
- score-only DDF requests exactly $N$ primary solves, and DDF with target
  completion requests at most $2N$ solves under its existing contract; and
- the full $O(E)$ relation is not copied into fitted metadata.

RAM retains its canonical global base information rule and its one common
full-data range normalization. Under eligibility, those ranges are explicitly
labelled `base_global_data_before_peer_eligibility`; they are not recomputed
separately for each $B_o$. A restricted fit is a configurable DEAPack RAM
extension rather than the exact full self-inclusive Cooper--Park--Pastor
source profile. Recomputing local ranges after self exclusion could destroy
the common normalization and the bounded score contract. RAM therefore still
rejects temporal and custom base `ReferenceSpec` policies.

## Result, failure, and provenance contract

Every authorized fitted summary reports:

- `base_reference_size`, before the comparison-right intersection;
- effective `reference_size`; and
- `self_in_reference`.

The fitted registry reference axis and top-level metadata retain the base
`ReferenceKind` and add the same compact M11 eligibility audit only when a
policy is supplied. That audit records the construction mode, exact
intersection rule, provenance, edge and population counts, distinct base and
effective set counts, fingerprints, and
`categorical_interpretation: not_claimed`.

The machine records retain the existing `static.radial`, `static.additive`,
`static.ram`, three ordinary `static.sbm.*.tone2001`, and
`static.directional_distance` identities. Their reference axes expose the
same optional policy and their result contracts expose the common base/effective
population, self-membership, technology-membership, and compact-provenance
fields. This composition axis creates no new method or preset identity.

`evaluation_protocol.kind` must describe the actual fitted design:
`self_appraisal`, `mixed_self_and_external_reference_appraisal`, or
`external_reference_appraisal`. It may not remain hard-coded to self appraisal
after self exclusion. The static machine record therefore describes a
reference-set-dependent appraisal and records that its fitted kind is derived
from the resolved `ReferencePlan`.

For each family:

- no published intensity may identify a row outside $B_o$;
- score, target, slack, peer, and dual claims retain the family's existing
  solver-neutral and economic postsolve certificates;
- a certified external comparison is not relabelled as ordinary self
  efficiency;
- an infeasible programme with `self_in_reference=False` is reported as
  `outside_reference_technology`, not as an unexplained backend failure; and
- an uncertified or failed solve continues to withhold semantic tables.

`reference_frequency` remains fail-closed for all eligibility-conditioned
results until its diagnostic contract is separately audited. A comparison
population can change selected-plan frequency, and removing the policy after
fitting would change the estimand.

## Handbook and Documentation boundary

M12 adds no Handbook route. The study-design chapter and the existing applied
capstone may show one declared institutional comparison rule used consistently
across radial, additive/slacks-based, and directional accounts. The prose must
explain why the conclusions differ by management question while the admitted
evidence population remains fixed. It may not describe geometric arrows,
categorical DEA, causal effects, superiority, or transferable practice.

Exact constructor signatures, validation, summary fields, metadata, and code
belong in package Documentation. The Handbook remains a theory-to-practice
book, not a duplicated API manual.

## Verification gate

M12 closes only when automated evidence covers:

1. explicit constructor signatures and rejection on every unauthorized
   environmental or specialist neighbor;
2. no-policy regression for all newly authorized families;
3. exact keyed and positional intersection with global, temporal, and custom
   base policies across compatible models, while RAM retains its explicit
   global-only base policy;
4. manual custom-reference score, target, slack, peer, and dual equivalence for
   each mother family;
5. empty, singleton, self-only, mixed, and fully self-excluded populations;
6. correct external-infeasibility and uncertified-solve failure semantics;
7. absence of intensity leakage outside the effective population;
8. compact and identical policy provenance across authorized families;
9. $K$-population compilation and exact solve-count assertions in a governed
   repeated-cohort benchmark;
10. continued fail-closed reference-frequency behavior; and
11. strict tests, lint, Documentation examples, English Handbook figure/HTML/
    PDF, distribution, and source-bound benchmark gates.
