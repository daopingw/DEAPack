# M11 source-neutral peer eligibility

> **Historical checkpoint.** This specification freezes the first radial-only
> delivery slice. The current public classical black-box support surface is
> governed by [`M12_CORE_PEER_ELIGIBILITY.md`](M12_CORE_PEER_ELIGIBILITY.md);
> the radial-only API statements below describe M11 at the time it closed and
> are not the current constructor inventory.

## Release boundary

M11 adds one study-design mechanism to the public classical radial route. It
does not add a DEA model family or a categorical-method identity.

For evaluated observation $o$, let $I_o$ be the rows admitted by the existing
`ReferenceSpec` information policy and let $P_o$ be the comparison population
declared before scores are inspected. The effective radial reference rows are

$$
B_o = I_o \cap P_o.
$$

The policy can remove a row admitted by `ReferenceSpec`; it cannot add a row
that the time or custom-reference policy excludes. Solver-selected peers are
the positive intensities within $B_o$ and remain results, not inputs.

This first public slice is supported only by `RadialDEA`, `CCR`, and `BCC`.
The fixed-orientation convenience classes do not accept `peer_eligibility`,
and other models continue to accept only their existing `ReferenceSpec`
interface. Enabling the mechanism on any additional constructor requires a
later method-specific result, target, failure, and registry audit; shared
access to the reference builder is not sufficient authorization.

## Public objects

`PeerEligibilityProvenance` records the named rule, its evidence source, the
candidate population to which it applies, the decision owner, and its validity
period. Every field is required and non-empty. This makes a comparison-right
decision auditable rather than hiding it behind a Boolean mask.

`PeerEligibility` is immutable and has two explicit construction modes:

- `by_key(mapping, provenance=...)` uses exact DMU keys in a cross section and
  exact `(dmu_id, period)` keys in a panel. It is the preferred reader-facing
  mode because it is independent of mapping insertion order and data-row
  permutation.
- `by_row(rows_by_observation, provenance=...)` is a low-level positional
  mode. The outer position identifies the assessed row and each inner sequence
  identifies its eligible candidates in the supplied `DEAData` row order.

There is no inferred union, category column, automatic group semantics, or
implicit use of `DEAData.groups`. A future source-qualified method may compile
categories into this mechanism, but the generic object does not decide how a
nominal, ordered, controllable, or uncontrollable category should operate.

## Validation and failure semantics

All declarations are copied into immutable internal representations before a
fit. The builder rejects:

- missing, unhashable, unknown, duplicate, or schema-incompatible keys;
- keyed scalar types that cannot be encoded losslessly under the portable,
  type-strict key schema, including arbitrary real classes and NumPy
  `datetime64`/`timedelta64` values;
- Boolean, non-integral, negative, duplicate, or out-of-range row positions;
- keyed mappings that do not cover every evaluated observation exactly once;
- an outer positional sequence whose length differs from the data; and
- any effective $B_o$ that is empty after intersection.

A singleton effective population is permitted and disclosed. Self-exclusion
is also permitted and disclosed; the compiler never silently inserts the
evaluated row. These are valid generic external-comparison designs even though
future source-named leaves may impose stricter domain rules.

## Compilation and scalability contract

The no-eligibility path retains the existing reference-builder behaviour.
With eligibility, the builder resolves the declaration once, intersects it
with each base information set, and content-deduplicates equal effective row
vectors. Effective arrays and observation-to-set identifiers are backed by
private immutable storage. Dense plan IDs remain the cache keys used by the
radial quantity compiler and phase-one template cache.

For $N$ observations, $E$ declared eligibility edges, and $K$ distinct
effective populations, the planning path should be proportional to the
material base-set representation plus $E$, not to an unconditional $N^2$
membership matrix. A repeated-cohort benchmark must observe $K$ reference and
phase-one-template compilations, $N$ task bindings, and $N$ score-only solves.
Dense all-to-all eligibility remains an $O(N^2)$ declaration and must be
reported as such rather than hidden by the API.

## Result and provenance contract

The radial summary distinguishes:

- `base_reference_size`: candidates admitted by `ReferenceSpec` before the
  comparison-population decision;
- `reference_size`: candidates remaining in the effective population; and
- `self_in_reference`: whether the evaluated observation is itself admitted.

When eligibility is supplied, compact metadata records the construction mode,
composition rule (`intersection`), required provenance, declared and effective
edge counts, population-size range, singleton and self-exclusion counts,
distinct base/effective set counts, and domain-separated fingerprints. The
full $O(E)$ relation is not duplicated into every result. An explicit audit
frame is available from the immutable eligibility object.

The canonical registry reference axis retains the ordinary base
`ReferenceKind` and adds an eligibility block only when the policy is present.
It must state `categorical_interpretation: not_claimed`. The top-level
`reference_kind` therefore continues to describe the temporal/custom base
policy, not a source-named categorical technology.

## Evidence boundary

The separate Banker--Morey categorical discovery candidate remains
`deferred_to_next_version` under
`source_protocols/banker_morey_1986_categorical.md`. M11 must include tests
that no public catalog record, class, alias, or metadata identity claims that
method. Generic eligibility results may not cite the 1986 article as defining
their optimization programme.

## Verification gate

The milestone closes only when automated checks cover:

1. legacy radial results with no eligibility policy;
2. keyed and positional validation, immutability, and audit export;
3. global, custom, contemporaneous, sequential, and window intersections;
4. empty, singleton, self-only, and self-excluded effective populations;
5. content deduplication and compile/cache counts for repeated populations;
6. manual per-observation custom-reference score equivalence;
7. fingerprint domain separation, input-order invariance for keyed mappings,
   and positional row-order binding;
8. absence of fitted intensities outside the effective population;
9. compact registry/result provenance; and
10. strict Documentation, Handbook figure, formatting, and full test gates.
