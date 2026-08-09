# M13 comparison rights for core environmental mother models

## Decision and composition boundary

Environmental performance studies often face two separate design questions:

1. what production and residual-generation assumptions describe attainable
   operation; and
2. which observed organizations are institutionally credible suppliers of
   comparison evidence for each evaluated organization.

M13 keeps those questions separate.  For evaluated observation $o$, let
$I_o$ be the rows admitted by the base `ReferenceSpec` and let $P_o$ be the
candidate population declared by `PeerEligibility`.  Every authorized
environmental estimator uses

$$
B_o=I_o\cap P_o.
$$

The intersection changes who may support the benchmark.  It does not change
the environmental direction, input/output roles, bad-output balance,
disposability, null jointness, returns to scale, or efficiency criterion.  It
therefore adds no model identity and makes no categorical, causal, regulatory,
or engineering-feasibility claim.

## Authorized public surface

The first environmental comparison-right release is deliberately limited to
the mainstream black-box mother routes whose complete production accounts and
independent oracles are already certified:

- `EnvironmentalDirectionalDistanceDEA` and `EnvironmentalDDF`;
- `CommonFactorWeakDisposalDDF`;
- the fixed `ChungFareGrosskopfDDF` output-environmental preset; and
- `UndesirableSlacksBasedDEA` and `UndesirableSBM`, the separable strong-
  disposal undesirable-output SBM.

The policy remains unavailable on activity-specific weak disposal,
by-production, modified by-production, material balance, nonseparable hybrid
SBM, non-CHP energy--carbon presets, network, dynamic, productivity, and other
specialist environmental routes.  Sharing a reference compiler or inheriting
from a core class does not authorize these neighbours.  Their feasibility,
normalization, membership, and result accounts require separate audits.

## Production semantics under restricted comparison rights

Each effective reference block preserves its estimator's existing equations:

- the generic environmental DDF retains the declared desirable- and
  undesirable-output balances and its exact strong-disposal or legacy
  directional-equality identity;
- the common-factor and CFG routes retain CRS, the bad-output equality, and
  the existing null-jointness condition;
- the separable undesirable-output SBM retains
  $b_o=B\lambda+s^b$ and its dimension-weighted good/bad output account.

`PeerEligibility` may remove the evaluated observation from $B_o$.  Such a fit
is an external appraisal, not ordinary self-inclusive DEA efficiency.  A
negative environmental directional distance remains a valid signed external
comparison when the constructor explicitly permits it.  When the distance is
constrained nonnegative and the evaluated plan cannot be represented, the
result must report `outside_reference_technology`; it must not clip, impute,
or reinterpret the failure as poor environmental management.

## API, reference planning, and performance

Every authorized constructor accepts only `PeerEligibility | None`, validates
its type before fitting, and passes it separately from `ReferenceSpec` to the
shared reference-plan builder.  The no-policy path preserves the existing
numerical programme and model identity.

For $N$ evaluations, $E$ declared eligibility edges, and $K$ distinct
effective populations:

- the eligibility relation is resolved once without an unconditional dense
  $N\times N$ matrix;
- exactly $K$ environmental reference quantity blocks are compiled;
- the separable undesirable-output SBM requests one primary solve per
  evaluation;
- score-only environmental DDF requests one primary solve per evaluation;
- DDF target completion and conditional membership tasks retain their existing
  documented solve budgets; and
- compact fitted metadata records fingerprints and counts rather than copying
  all $E$ edges.

No reference-specific direction or SBM normalization is inferred from the
eligible population.  Direction vectors and observation denominators retain
their estimator-defined data basis unless a future separately named contract
states otherwise.

## Result, appraisal, and provenance contract

Every authorized summary reports:

- `base_reference_size` before the eligibility intersection;
- effective `reference_size`;
- `self_in_reference`; and
- the estimator's existing environmental account, certification, target,
  slack, peer, marginal, and failure fields.

Fitted metadata derives `evaluation_protocol.kind` from the resolved plan as
`self_appraisal`, `mixed_self_and_external_reference_appraisal`, or
`external_reference_appraisal`.  It retains the base reference kind and adds
the same compact, source-neutral eligibility audit used by the classical core,
including construction mode, exact intersection rule, provenance, edge and
population counts, fingerprints, and
`categorical_interpretation: not_claimed`.

No reported intensity may identify a row outside $B_o$.  Score, target, slack,
peer, marginal, and membership claims continue to pass their existing
solver-neutral LP and original-unit environmental-production certificates.
An eligibility-conditioned result remains ineligible for
`reference_frequency()` until that diagnostic is separately audited.

## Handbook and Documentation placement

M13 creates no new Handbook route.  The environmental DDF and undesirable-
output SBM chapters may each carry one management example showing that the
production account can stay fixed while the credible comparison population
changes.  The example must discuss institutional comparability and sensitivity
of the conclusion, not imply that excluded organizations are invalid or that
eligible peers are transferable best practice.

Constructor signatures, validation, metadata, failure behavior, supported
class matrix, and exact code belong in package Documentation.

## Verification gate

The environmental comparison-right release closes only when automated evidence
establishes:

1. explicit support and rejection on every authorized and adjacent
   unauthorized constructor;
2. exact no-policy regression for each authorized mother route;
3. keyed and positional intersections with global, temporal, and custom base
   references;
4. manual per-observation-reference equivalence for scores, targets, slacks,
   peers, bad-output balances, and certified marginals;
5. self, mixed, and fully external appraisal metadata;
6. valid signed negative external DDF results and fail-closed nonnegative
   external infeasibility;
7. no intensity leakage outside the effective population;
8. identical compact eligibility provenance across the authorized routes;
9. exactly $K$ compilations and the documented solve counts in a governed
   repeated-population benchmark;
10. continued fail-closed reference-frequency behavior; and
11. synchronized registry, Documentation, Handbook cases, changelog, roadmap,
    tests, lint, examples, benchmark tiers, and release builds.
