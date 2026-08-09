# Review register: static and economic DEA

## Purpose and maintenance rule

This review organizes the static DEA literature by the economic or managerial
question being answered. It is an evidence register for taxonomy, package
design, and the companion book; it is not an API promise and not a list of
acronyms to implement independently.

Every record uses the same fields. `Technology / estimator / inference`
deliberately keeps three different objects apart:

- a **technology** states the maintained production possibilities;
- an **estimator** states how observations construct an empirical boundary;
- **inference** states how sampling uncertainty about an estimator is
  quantified.

A change on one axis does not silently change the others. Unless a record says
otherwise, the estimator is the full empirical DEA estimator and no sampling
inference is implied.

`Evidence status` records whether the formulation is primary-checked,
review-supported, or still registry-provisional, followed by any repository
implementation/property evidence. `Oracle` is kept separate and begins with
exactly one controlled status: `not located`, `candidate`,
`analytically derived`, `reproduced`, or `cross-implemented`. The last three
mean that an automated independent numerical oracle exists, but they make
different evidence claims. An analytically derived oracle requires an exact
certificate and an independently compiled validation path; it does not imply
that published data or results have been reproduced. Oracle status must be
rechecked against `src/deapack/catalog.py` and the test suite before a release.
A source citation establishes provenance; it does not by itself establish
numerical correctness of DEAPack.

## 1. How much can resource use or service delivery improve proportionally?

### `static.radial` — Farrell radial technical efficiency

- **Economic question:** Can the current output commitment be met with a
  proportional reduction in all adjustable inputs, or can all adjustable
  outputs be expanded proportionally with the current inputs?
- **Technology / estimator / inference:** Convex free-disposal technology;
  full empirical DEA estimator; no inference in the base recipe.
- **Measure:** Input- or output-oriented radial distance, followed by an
  explicitly declared slack/target phase.
- **RTS:** CRS, VRS, NIRS, or NDRS are technology choices, not score aliases.
- **Data / time:** Non-negative cross-sectional quantities or a declared
  pooled/reference sample; panel time enters only through a separate reference
  policy or productivity operator.
- **Native score:** Input Farrell contraction factor $\theta_o$ or output
  expansion factor $\phi_o$. For the ordinary self-inclusive internal
  reference, free disposal gives $\theta_o\in(0,1]$ and
  $\phi_o\in[1,\infty)$. An external/custom reference can place the evaluated
  activity beyond the reference boundary, so values may cross those familiar
  bounds and must not be clipped. A reciprocal output efficiency may be
  displayed but is not the native optimum.
- **Exact aliases:** Primal envelopment and multiplier formulations are
  computationally equivalent under matched assumptions; they are not separate
  methods.
- **Distinct variants:** FDH, directional distance, subvector distance,
  hyperbolic measures, additive measures, and non-radial target selectors.
- **Domain:** Quantity variables must respect the selected disposability and
  sign assumptions; orientation must correspond to outcomes management can
  actually adjust.
- **Failures:** Infeasible external references, unbounded multiplier programs,
  zero-denominator display transforms, dimensional sparsity, weakly efficient
  radial projections, and multiple optimal peers.
- **Solver form:** Linear program for convex DEA; an optional second LP can
  complete slacks without changing the radial score.
- **Defining source:** Farrell's economic decomposition
  ([Farrell 1957](https://doi.org/10.2307/2343100)); empirical CRS envelopment
  ([Charnes, Cooper, and Rhodes 1978](https://doi.org/10.1016/0377-2217(78)90138-8));
  VRS and scale decomposition
  ([Banker, Charnes, and Cooper 1984](https://doi.org/10.1287/mnsc.30.9.1078)).
- **Evidence status:** primary-checked; implemented/public with property,
  exact analytical, and independent dense-compiler evidence.
- **Oracle:** analytically derived — an exact three-activity certificate covers
  phase-one input and output scores under CRS, VRS, NIRS, and NDRS, plus one
  input- and one output-oriented VRS case with nonzero second-phase slack. A
  separate dense two-phase compiler checks all eight branches with and without
  slack completion without importing the production problem builders. The
  registry records these as separate, data- and reference-bounded claims. See
  `specs/oracles/radial-analytical.md` and
  `tests/test_radial_independent_oracle.py`. This is deliberately not a claim
  of published-data reproduction.
- **Package recipe:** `RadialDEA`; canonical family `static.radial`.
- **Book location:** **Active core placement:** `book/chapters/02-classical/03-classical-radial.md`; dual algebra and historical names remain in package documentation.

### CCR and BCC — partial specializations; CCR-I/O and BCC-I/O are presets

- **Economic question:** Should the benchmark permit replication at any scale
  (CCR/CRS) or compare against locally scaled mixtures of observed activities
  (BCC/VRS)?
- **Technology / estimator / inference:** CCR specializes the convex
  envelopment technology to CRS; BCC specializes it to VRS; both use the full
  DEA estimator; neither name selects an inferential procedure.
- **Measure:** Not fixed by the specialization. Input and output radial
  measures remain separate choices.
- **RTS:** CCR fixes CRS; BCC fixes VRS.
- **Data / time:** Same as the composed radial recipe.
- **Native score:** Not fixed until orientation is selected.
- **Exact aliases:** `CCR` is the package specialization
  `static.radial.crs`; `BCC` is `static.radial.vrs`.
- **Distinct variants:** CCR-I, CCR-O, BCC-I, and BCC-O are complete presets,
  because each additionally fixes orientation, native score, and target/slack
  policy. They must not be treated as aliases of one another. DEAPack fixes
  `compute_slacks=True` and its row-scaled lexicographic slack completion in
  all four named presets. That phase-two target selector is a transparent
  package policy; the package does not attribute one uniquely selected target
  among alternate radial optima to the foundational papers.
- **Domain:** Inherits the radial measure and reference-policy domain.
- **Failures:** Reporting “CCR efficiency” or “BCC efficiency” without
  orientation and score convention leaves the fitted task under-specified.
- **Solver form:** Linear program after the remaining recipe fields are fixed.
- **Defining source:** [Charnes, Cooper, and Rhodes
  1978](https://doi.org/10.1016/0377-2217(78)90138-8);
  [Banker, Charnes, and Cooper
  1984](https://doi.org/10.1287/mnsc.30.9.1078).
- **Evidence status:** primary-checked; CCR and BCC constructors and all four
  named I/O presets are implemented/public over the same radial compiler. They
  inherit the exact CRS/VRS score branches and independent two-phase compiler
  certificate. A separate exact two-input/two-output fixture closes the CRS
  input/output target and slack accounts; the existing one-input/one-output
  cases close the corresponding VRS accounts.
- **Oracle:** analytically derived through the shared `static.radial`
  certificate for the corresponding CRS/VRS branches and through explicit
  preset-to-core regression checks. This is not a published-data
  reproduction, and it does not claim that the source papers prescribed
  DEAPack's phase-two alternate-target selector.
- **Package recipe:** `CCR` and `BCC` remain partial specialization
  constructors. `CCRInput`, `CCROutput`, `BCCInput`, and `BCCOutput` emit,
  respectively, preset IDs `static.radial.crs.input`,
  `static.radial.crs.output`, `static.radial.vrs.input`, and
  `static.radial.vrs.output`, while retaining `static.radial` as the result
  `method_id`. A numerically identical generic `RadialDEA` call does not infer
  a historical preset identity.
- **Book location:** **Active core placement:** `book/chapters/02-classical/03-classical-radial.md`; exact preset and naming rules remain in package documentation.

NIRS and NDRS remain independently checked parameter paths of `RadialDEA`.
They do not receive a standalone `static.radial.restricted_rts` literature
identity in this version. A separately named leaf is deferred until an
original or authoritative source fixes its complete recipe and an independent
leaf-level oracle closes it.

### `static.radial.fdh` — radial free-disposal-hull efficiency

- **Economic question:** What improvement is demonstrated without assuming
  that unobserved averages of different organizations are attainable?
- **Technology / estimator / inference:** Non-convex free-disposal hull; full
  empirical FDH estimator; no inference in the base recipe.
- **Measure:** Input- or output-oriented radial distance to the FDH boundary.
- **RTS:** Standard FDH and scale-extrapolated FDH variants must identify their
  source-specific rescaling rules; CRS-like rescaling does not convexify
  across activities.
- **Data / time:** Cross-sectional or declared reference samples; duplicates
  and dominance ties require deterministic handling.
- **Native score:** Same input contraction/output expansion conventions as the
  radial family.
- **Exact aliases:** `FDH` and `FreeDisposalHullDEA` are package aliases for
  `static.radial.fdh`.
- **Distinct variants:** Convex DEA; scale-extrapolated FDH under CRS, NIRS, or
  NDRS; order-$m$ and order-$\alpha$ partial frontiers.
- **Domain:** Ordinary free-disposal quantity data; no convex combination of
  different observations.
- **Failures:** Combinatorial cost at large $n$, ties, isolated observations,
  and the false claim that an order-$m$ estimator is “robust FDH” with only a
  tuning switch.
- **Solver form:** Dominance scan for standard radial FDH; source-qualified
  rescaling variants may require optimized scans or mathematical programs.
- **Defining source:** [Deprins, Simar, and Tulkens
  1984](https://ideas.repec.org/h/eee/ecocha/2-09.html); scale
  extrapolation [Kerstens and Vanden Eeckaut
  1999](https://doi.org/10.1016/S0377-2217(97)00428-1).
- **Evidence status:** primary-checked; standard radial FDH is
  implemented/public with property and claim-scoped analytical evidence.
  Scale-extrapolated variants are registry-provisional/planned.
- **Oracle:** analytically derived — an exact five-organization certificate
  exhaustively enumerates every eligible single-activity comparison and
  checks both orientations, scores, status, peers, targets, and residual
  slacks through the public API. It is not a published-data reproduction and
  does not certify the separate scale-extrapolated or partial-frontier
  variants; see `specs/oracles/fdh-analytical.md` and
  `tests/test_fdh_independent_oracle.py`.
- **Package recipe:** `FreeDisposalHullDEA` / `FDH`;
  `static.radial.fdh`. Keep `technology.fdh.scale_extrapolation` separate.
- **Book location:** **Active core placement:** FDH is consolidated inside `book/chapters/02-classical/03-classical-radial.md`; partial-frontier extensions remain in package documentation and source review.

### `static.radial.frh` — radial efficiency with whole-unit replication

- **Economic question:** If an organization may reproduce complete operating
  modules but cannot build fractional modules, what input saving or output
  expansion is demonstrated by integer combinations of observed practice?
  A module may be a branch, production line, clinic team, vessel, or other
  indivisible operating template whose resource and service bundle is copied
  as a whole.
- **Technology / estimator / inference:** The free-replicability hull
  $$
  T^{FRH}=\{(x,y):x\ge Xz,\ y\le Yz,\ z\in\mathbb Z_+^n\}
  $$
  with ordinary free disposal and the full empirical FRH estimator; no
  sampling inference in the base recipe. Observed inputs and outputs may be
  continuous quantities—the integrality restriction applies to replication
  counts $z$, not automatically to every data value.
- **Measure:** The input recipe minimizes $\theta$ subject to
  $Xz\le\theta x_o,\ Yz\ge y_o$; the output recipe maximizes $\phi$
  subject to $Xz\le x_o,\ Yz\ge\phi y_o$, with
  $z\in\mathbb Z_+^n$ in both cases. A compatible second phase may complete
  residual input excesses and output shortfalls while holding the native
  radial optimum.
- **RTS:** FRH's additive whole-unit replication is the technology
  assumption. It is not selected through an ordinary CRS/VRS/NIRS/NDRS
  switch. Finite replication limits define
  `technology.frh.bounded_replication`, a different opportunity set.
- **Data / time:** Non-negative cross-sectional quantities or a declared
  comparison population. Panel, group, network, undesirable-output, and
  dynamic structure require separately validated compositions.
- **Native score:** Input contraction $\theta_o$ or output expansion
  $\phi_o$, accompanied by integer `replication_count`, total replications,
  active observed templates, residual disposals, solver termination, MIP gap,
  and whether an integer optimum is certified. Alternate optimal integer
  plans must not be presented as unique.
- **Exact aliases:** Free replicability hull, free replication hull, and free
  disposal and replicability hull are accepted names for the same maintained
  technology. The `RTS="add"` spelling in the R package `Benchmarking`
  is provenance, not a public DEAPack RTS option; the bare word “additive”
  remains too ambiguous for an alias.
- **Distinct variants:** FDH permits one observed template but not combinations;
  FRH permits integer combinations; ordinary CRS DEA permits fractional
  combinations and is the continuous relaxation of the matched FRH
  programme. BCC/VRS is generally non-nested. Elementary-replicability,
  free-coordination, free-affordability, bounded-replication, integer-valued
  production, and additive-slack models retain separate identities.
- **Domain:** The operating-template interpretation must be credible. If a
  plant or service configuration is continuously divisible, imposing integer
  copies answers the wrong economic question; if some rather than all
  templates have limits or indivisibilities, those restrictions require
  their own source-qualified technology.
- **Failures:** MILP time or node limits without an integer optimality
  certificate; overly loose or undocumented computational bounds; infeasible
  external references; mistaken post-solve rounding of a CRS solution;
  reporting LP dual prices for a non-convex integer technology; and confusing
  integer replication counts with integer-valued inputs or outputs.
- **Solver form:** One sparse MILP per evaluated DMU for the radial phase,
  reusing one compiled comparison population. Finite variable bounds may be
  derived for computation from the evaluated resource limits and positive
  reference coefficients; such bounds do not become economic replication
  limits. Column generation is a later large-sample strategy, not part of the
  first public contract.
- **Defining source:** Tulkens' non-convex production discussion
  ([Tulkens 1993](https://doi.org/10.1007/BF01073473)); relaxed-convexity
  axioms and consistent input/output technologies
  ([Bogetoft 1996](https://doi.org/10.1287/mnsc.42.3.457)); computational
  treatment of free replicability
  ([Ehrgott and Tind 2009](https://doi.org/10.1016/j.omega.2008.08.003)).
- **Evidence status:** primary/review source freeze complete;
  implemented/public with analytic, property, failure, and nesting evidence.
- **Oracle:** analytically derived — the neutral
  `integer_coordination_hulls` project case checks both orientations and the
  selected whole-module portfolios. The derivation and claim boundary are in
  [`frh-benchmarking-033.md`](../oracles/frh-benchmarking-033.md); the
  `Benchmarking` documentation remains a method/implementation citation, but
  its numerical example is not redistributed.
- **Package recipe:** `FreeReplicabilityHullDEA` / `FRH`;
  `static.radial.frh`, composed from `technology.frh` and
  `estimator.full.frh`. There is deliberately no public RTS parameter.
- **Book location:** **Documentation/source review only.** Whole-unit
  replication has no independent placement in the current handbook.

### `static.radial.fch.green_cook_2004` — binary-subset coordination

- **Economic question:** What improvement is attainable when several observed
  operating templates may coordinate once each, but no template can be
  fractionally divided or replicated?
- **Technology / estimator / inference:** Implemented
  `technology.fch.binary_subset_aggregation` and `estimator.full.fch`, with a
  nonempty binary selection of distinct reference organizations; no sampling
  inference is implied.
- **Measure:** Source-qualified input/output radial account with optional
  fixed-score free-disposal-residual completion.
- **RTS:** Binary subset aggregation is the technology's scale/combination
  rule; it is not an ordinary CRS/VRS switch.
- **Data / time:** Economically additive nonnegative cross-sectional inputs
  and desirable outputs with positive observation-level input/output
  aggregates and a declared comparison population. An evaluated zero input is
  a hard zero resource budget; an evaluated zero output imposes no
  proportional expansion requirement but remains in reference-activity and
  output-slack accounting. Panel, undesirable-output, or structured uses
  require separate compositions.
- **Native score:** Input contraction $\theta$ or output expansion $\phi$,
  standardized efficiency, selected binary coalition, coalition size,
  radial/reference activities, free-disposal residuals, and binary/MIP-gap
  certification.
- **Exact aliases:** Free coordination hull, free aggregation hull, FCH, and
  historical FAH identify the same Green--Cook technology when the complete
  source recipe matches. Only `FCH` is public Python API: `FAH` is withheld
  because Ray (1997) uses it for a distinct free affordability hull.
- **Distinct variants:** FDH one-template selection; FRH integer replication;
  CCR continuous intensities; finite replication bounds; and Ray's
  price-based free affordability hull.
- **Eleven-axis placement:** $T$ owns binary subset aggregation; $M$ owns
  the radial account; the public expanded specification resolves the
  remaining axes.
- **Equivalence boundary:** Level C versus FDH and FRH. Under matched
  conditions, $T_{FDH}\subseteq T_{FCH}\subseteq T_{FRH}$. FCH and VRS are
  not generally nested. Relaxing FCH's binary variables retains
  $0\leq\lambda_j\leq1$ and the nonempty-subset constraint, so its direct
  LP relaxation is not CCR.
- **Domain:** Coordination must have an operational interpretation and each
  observed template must be usable at most once; extensions with template-
  specific availability are separate technologies.
- **Failures:** Treating FCH as a VRS/CCR option, calling CCR its direct LP
  relaxation, reporting an uncertified binary incumbent, using nonadditive
  ratios as coalition quantities, or interpreting the selected coalition as
  a recommendation to merge organizations.
- **Solver form:** Sparse binary MILP per evaluated DMU with a nonempty-subset
  row, compiled-reference reuse, componentwise binary/bound/constraint checks,
  required certified MIP gap, and optional lexicographic slack completion.
- **Defining source:** [Green and Cook
  (2004)](https://doi.org/10.1057/palgrave.jors.2601773); the exact free
  aggregation hull name is confirmed by
  [Adler, Olesen, and Volta
  (2024)](https://doi.org/10.1287/opre.2022.2348).
- **Evidence status:** `primary-checked`; implemented/public.
- **Oracle:** `analytically derived` — a production-free `Fraction`
  enumerator visits all 15 nonempty binary coalitions of the declared
  four-organization fixture. It proves both oriented scores for every
  organization, the fixture-specific optimal coalitions, radial/reference
  activities, and free-disposal residuals, while separate tests distinguish
  FDH, FCH, FRH, CCR, and VRS and enforce nesting, non-nesting, certification,
  invariance, and failure contracts. No published Green--Cook numerical table
  or independent third-party cross-implementation is claimed.
- **Package recipe:** `FreeCoordinationHullDEA` / `FCH`;
  `static.radial.fch.green_cook_2004`. There is no `FAH` Python alias.
- **Book location:** **Documentation/source review only.** Binary-subset
  coordination has no independent placement in the current handbook.

#### Planned evidence annex: Ray's free affordability hull

- **Planning question:** What cost-indirect benchmark can be constructed when
  normalized input prices are available but physical input quantities are
  not?
- **Technology / estimator:** Ray's price-normalized free affordability
  technology; the exact finite-sample inequalities and estimator contract
  remain to be frozen.
- **Measure:** Source cost-indirect efficiency, not radial binary-subset
  coordination.
- **RTS:** Source-specific and unresolved pending equation audit.
- **Data / time:** Cross-sectional outputs and normalized input prices without
  observed input quantities.
- **Native score:** Source-native indirect-cost result to be frozen; no
  DEAPack score convention is asserted.
- **Exact aliases:** “Free affordability hull” and Ray's historical `FAH`
  only. No alias with Green--Cook FCH/free aggregation hull.
- **Distinct variants:** Ordinary cost DEA with quantities and prices,
  indirect output/budget models, Green--Cook binary coordination, and other
  price-only technologies.
- **Domain:** $D$ records absent input quantities and normalized prices,
  $T$ the affordability technology, $V$ the price normalization, and
  $M/A$ the indirect-cost account.
- **Failures:** Resolving `FAH` without source provenance, substituting prices
  for physical inputs in ordinary DEA, or presenting the proposal as
  implemented.
- **Solver form:** Planned pending a primary equation and backend audit.
- **Defining source:** [Ray
  (1997)](https://doi.org/10.1023/A:1007747407212).
- **Evidence status:** planned/evidence proposal; Level C/D relative to
  Green--Cook FCH because data roles, technology, valuation, and performance
  account differ.
- **Oracle:** not located.
- **Package recipe:** Proposed
  `economic.cost_indirect.free_affordability.ray_1997`; not executable.
- **Book location:** **Evidence-deferred candidate.** No handbook placement is
  reserved before the defining-source, equation, and oracle gates close.

### `evaluation.target_completion.pareto_koopmans` — strong-status and target-completion policy

- **Economic question:** Has the organization exhausted every attainable
  input saving and output gain, or has a proportional improvement merely
  stopped while economically useful component-wise improvements remain?
- **Technology / estimator / inference:** Public only for the ordinary
  black-box, continuous convex, free-disposal technology with all completed
  inputs discretionary and all completed outputs desirable. The comparison
  population, temporal reference, estimator, and declared RTS restriction
  are inherited unchanged from a compatible `static.radial`,
  `static.directional_distance`, or
  `static.generalized_distance.chavas_cox` fit. GDF is limited to its CRS/VRS
  public domain, positive observation-level input and output aggregates, and
  a fixed finite nonnegative path target. No sampling inference is implied.
- **Measure:** A result policy that preserves the base model's native score,
  records weak/radial versus Pareto--Koopmans status, and, when requested,
  completes the projection to a strongly efficient target without worsening
  any input or output.
- **RTS:** Inherited unchanged from the base technology. Strong completion
  must not silently refit under a different scale assumption.
- **Data / time:** The same evaluation and reference data as the base fit,
  plus explicit variable-level control and disposability roles for every
  quantity eligible for target completion.
- **Native score:** The original radial, directional, or generalized-distance
  score plus completion slacks, the completed target, and a strong-status
  flag. The second phase does not retrospectively improve or independently
  certify the first-phase score.
- **Exact aliases:** Zero optimal input and output slacks in the additive
  Charnes--Cooper test characterize Pareto--Koopmans efficiency under the
  same ordinary technology and variable roles. DEAPack's embedded completion
  has the same zero-slack status meaning only on the protocol's stated
  compatibility domain; it is not a second scalar measure.
- **Distinct variants:** Weak/radial efficiency, additive and SBM scalar
  measures, closest-target optimization, efficient-facet selection, and
  alternative positive-weight or priority target policies. They may deliver
  a strong target but are not aliases of this result contract.
- **Domain:** Finite nonnegative ordinary inputs and desirable outputs with
  positive observation-level aggregates; compatible input/output radial or
  nonnegative-direction DDF primary optimum, or a finite CRS/VRS GDF fit with
  a fixed finite nonnegative path target; every completed coordinate
  authorized to improve; positive zero-safe row scales; identical phase-one
  and phase-two
  technology/reference contracts; optimal completion and unthresholded
  target reconstruction. Generic strong status additionally requires that
  the evaluated plan is inside the reference technology.
- **Failures:** Calling a radial projection “fully efficient” when positive
  slacks remain, changing the reference set in the completion phase, using a
  nonpositive weight that can ignore an eligible improvement, inferring
  strong status after a failed/skipped completion, and presenting one
  alternate strong target as uniquely prescribed by management.
- **Solver form:** Strict two-phase lexicographic optimization. Phase one
  fixes the base model's native optimum. Phase two maximizes the sum of
  physical slacks divided by positive input/output row scales. Those scales
  transform with the measurement units and therefore stabilize target
  selection under independent positive unit changes. Radial DEA and DDF
  anchor them to the evaluated observation; GDF anchors them to its fixed
  path target. The shared protocol ID therefore fixes the completion
  principle and LP layout, not one universal alternate-optimum weighting.
- **Defining source:** Pareto--Koopmans empirical production foundations in
  [Charnes et al.
  1985](https://doi.org/10.1016/0304-4076(85)90133-2), equations
  (4.4)--(4.6), (5.3), (5.5), and (5.7), checked against the
  [CMU archival scan](https://iiif.library.cmu.edu/file/Cooper_box00028_fld00020_bdl0001_doc0001/Cooper_box00028_fld00020_bdl0001_doc0001.pdf).
  The source's observed-value normalization in equation (5.7) motivates unit
  invariance but is not DEAPack's zero-safe row-scale rule and does not
  prescribe one uniquely preferred target.
- **Evidence status:** `primary-checked` and implemented/public as an embedded,
  strictly scoped protocol over the three supported base methods.
- **Oracle:** `analytically derived`; the radial and directional independent
  dense compilers verify exact phase-two slacks, targets, strong-status
  separation, all four RTS restrictions, and unit behavior. A separate dense
  VRS completion compiler recovers the same target at the exact $\alpha=0$
  radial/DDF/GDF reduction, while the GDF suite checks an interior
  $\alpha=0.5$ path and unit-covariant completion. The reduction certifies
  only the shared phase-two contract, not GDF's interior first-stage formula
  or search. This is not a published-table reproduction and does not
  establish target uniqueness.
- **Package recipe:** `evaluation.target_completion.pareto_koopmans`, composed
  through `compute_slacks=True` on a compatible `static.radial`,
  `static.directional_distance`, or
  `static.generalized_distance.chavas_cox` fit. It has no standalone API or
  duplicate machine method record. The complete source and evidence boundary
  is frozen in
  [`source_protocols/charnes_etal_1985_pareto_koopmans_completion.md`](../source_protocols/charnes_etal_1985_pareto_koopmans_completion.md).
- **Book location:** **Active core placement:** the Pareto--Koopmans distinction is taught within `book/chapters/02-classical/03-classical-radial.md`, `book/chapters/02-classical/04-sbm.md`, and `book/chapters/02-classical/05-directional-distance.md`; target-policy details remain in package documentation.

Environmental, nondiscretionary, FDH, FCH, and FRH completion identities are
`deferred_to_next_version`. Model-specific slack-refinement code, where
present, does not inherit this reusable protocol claim until its own dominance
order, target theorem, and independent exact oracle are frozen.

## 2. Where are the specific resource excesses and service shortfalls?

### `static.additive` — additive and weighted-additive DEA

- **Economic question:** Which input excesses and output shortfalls can be
  removed simultaneously, and how should heterogeneous shortfalls be valued?
- **Technology / estimator / inference:** The source-qualified direct model is
  a self-inclusive convex VRS free-disposal technology; the reusable package
  family also exposes declared RTS/reference sensitivity configurations.
  It is a full DEA estimator with no inference in the base recipe.
- **Measure:** Charnes et al. (1985) equations (4.5)--(4.6) maximize the unit
  input/output slack sum. Explicit all-one weights are algebraically the same
  profile; fixed positive non-unit user weights are a configurable
  package extension; equation (5.7)'s evaluated-observation normalization is
  not an arbitrary fixed weight vector.
- **RTS:** VRS is part of the classic source profile. CRS/NIRS/NDRS are
  transparent package configurations and do not inherit its certificate.
- **Data / time:** Cross-sectional quantities; weights must state units or
  normalization and must not be mistaken for observed market prices.
- **Native score:** An inefficiency amount with zero best, expressed in the
  units induced by the slack weights.
- **Exact aliases:** Primal and dual representations under the same weights and
  technology.
- **Distinct variants:** RAM, BAM, SBM, Russell measures, congestion-additive
  models, closest-target models, and priority-weighted slacks.
- **Domain:** Additive slacks can accommodate zeros more naturally than ratio
  measures, but translation and unit invariance depend on the weights.
- **Failures:** Arbitrary unit-dependent aggregation, zero sample ranges in
  range weights, alternate optimal targets, and interpreting a weighted sum as
  welfare without a valuation source.
- **Solver form:** Linear program.
- **Defining source:** [Charnes et al.
  1985](https://doi.org/10.1016/0304-4076(85)90133-2), equation-audited from
  the complete archival scan.
- **Evidence status:** primary-checked; implemented/public. The classic
  VRS/unit-weight/self-inclusive cross-section is analytically certified.
- **Oracle:** analytically derived — the source-displayed two-DMU shortfall
  and an exact four-DMU separating fixture are compiled independently of the
  production LP builder. Scores, physical slacks, Pareto--Koopmans status,
  targets, and peers are closed. The paper does not print an additive result
  table, so `published_reproduction=false`. Fixed non-unit weights,
  CRS/NIRS/NDRS, panels/non-global references, equation (5.7), and target
  uniqueness do not inherit this certificate.
- **Package recipe:** `AdditiveDEA` and `WeightedAdditiveDEA`;
  `static.additive`. Runtime metadata distinguishes
  `charnes_etal_1985_eq_4_6` from
  `deapack_configurable_additive_extension`.
- **Book location:** **Active core placement:** additive efficiency is consolidated in `book/chapters/02-classical/04-sbm.md`; weighting and target-selection extensions remain in package documentation.

### `static.ram` and `static.bam` — range/bound-adjusted slack accounts

- **Economic question:** Can variable-specific shortfalls be placed on a
  comparable scale without pretending that they have market prices?
- **Technology / estimator / inference:** Convex envelopment technology and
  full DEA estimator; no inference in the base recipe.
- **Measure:** RAM normalizes each slack by the full observed range. The 2011
  BAM instead uses the evaluated unit's sample-supported one-sided improvement
  room:
  $$
  \delta_o^{BAM}
  =\frac{1}{m+s}\left[
  \sum_i\frac{s_i^-}{x_{io}-\underline{x}_i}
  +\sum_r\frac{s_r^+}{\overline{y}_r-y_{ro}}
  \right],
  \qquad
  \tau_o^{BAM}=1-\delta_o^{BAM},
  $$
  with $0\leq s_i^-\leq x_{io}-\underline{x}_i$ and
  $0\leq s_r^+\leq\overline{y}_r-y_{ro}$. These are empirical
  sample bounds, not automatically engineering or managerial bounds.
- **RTS:** Explicit and matched across comparisons.
- **Data / time:** Both accounts are sample dependent. The first BAM leaf uses
  $\underline{x}_i=\min_jx_{ij}$ and
  $\overline{y}_r=\max_jy_{rj}$ over one frozen global bound population;
  panel, window, group, and custom-reference bound scopes require separate
  policies.
- **Native score:** BAM retains both normalized inefficiency
  $\delta_o^{BAM}\in[0,1]$, lower is better, and efficiency
  $\tau_o^{BAM}=1-\delta_o^{BAM}$, higher is better.
- **Exact aliases:** None between RAM and BAM.
- **Distinct variants:** The 2013 bounded-CRS point-slack correction and the
  2015 Enhanced BAM comprehensive-bound formulation, natural/declared bounds,
  partially bounded variables, ordinary additive, RAM, and SBM are not aliases
  of the 2011 BAM.
- **Domain:** A zero one-sided room forces the corresponding slack to zero and
  contributes zero to the normalized account, as defined by the source. An
  initial nonnegative-data implementation is narrower than the source
  motivation for negative data and must say so.
- **Failures:** Computing weights from a different or future population,
  applying BAM weights without the target bounds, dividing by a zero room,
  silently substituting full RAM ranges, or relabeling Enhanced BAM as the
  original measure.
- **Solver form:** A sparse LP in bounded normalized slack variables. VRS
  quantity balances are reference-anchored before row scaling; other RTS paths retain
  level-scaled balances. This preserves the exact physical target account
  without applying an absolute physical-unit cleanup threshold.
- **Defining source:** RAM [Cooper, Park, and Pastor
  1999](https://doi.org/10.1023/A:1007701304281); BAM [Cooper et al.
  2011](https://doi.org/10.1007/s11123-010-0190-2), with an
  [open author manuscript](https://iiif.library.cmu.edu/file/Cooper_box0010a_fld00015_bdl0001_doc0001/Cooper_box0010a_fld00015_bdl0001_doc0001.pdf);
  the later bounded-measure lineage is summarized in the
  [open bounded-DDF article](https://dspace.umh.es/bitstream/11000/5278/1/13-Pastor2018_Article_BoundedDirectionalDistanceFunc.pdf).
- **Evidence status:** primary-checked; RAM and the 2011 BAM are
  implemented/public. Enhanced BAM remains a separate planned source leaf.
- **Oracle:** `analytically_derived` for the RAM leaf through a separately
  compiled dense VRS programme and an exact four-DMU target/peer certificate;
  no published numerical-table reproduction is claimed. `cross-implemented`
  for the 2011 BAM leaf — the 12-DMU, two-input,
  two-output example in Cooper, Seiford, and Tone (2007, Table 1.5) was solved
  independently with archived GPL-2 `additiveDEA` 1.1/lp_solve and a direct
  SciPy/HiGHS LP. DEAPack matches all VRS and bounded-CRS BAM inefficiencies
  to numerical tolerance. The 2011 article also reports Aida-water-utility
  scores such as DMU16 $(0.385,0.385,0.485,0.485)$ and DMU85
  $(0.529,0.529,1,1)$ under CRS/NIRS/NDRS/VRS. Contrary to the earlier
  audit, the full 108-by-7 source table is publicly readable in Aida et al.
  (1998), Table 2, through the
  [CMU author archive](https://iiif.library.cmu.edu/file/Cooper_box0010c_fld00001_bdl0001_doc0001/Cooper_box0010c_fld00001_bdl0001_doc0001.pdf).
  That item is marked In Copyright, and several scanned/printed cells require
  reconciliation, so DEAPack cites it but does not redistribute the table or
  use an unreviewed transcription as its release fixture.
- **Package recipe:** `RangeAdjustedDEA` / `RAM` for `static.ram`;
  `BoundedAdjustedDEA` / `BAM` for `static.bam`, with one frozen global
  sample-bound/reference population, nonnegative quantities, and no EBAM
  behavior.
- **Book location:** **Active core placement:** RAM is consolidated in `book/chapters/02-classical/04-sbm.md`; BAM equations, result fields, and failure contracts remain in package documentation only.

### `static.russell` — component-wise Russell measures

- **Economic question:** What is the average proportional improvement across
  individual inputs and/or outputs when a common radial rate is too
  restrictive?
- **Technology / estimator / inference:** Convex envelopment technology; full
  DEA estimator; no inference in the base recipe.
- **Measure:** Input Russell, output Russell, or Russell graph measure with
  variable-specific contraction/expansion factors.
- **RTS:** Explicit.
- **Data / time:** Cross-sectional positive quantity data for ratio-based graph
  forms; signed-data extensions require a separate formulation.
- **Native score:** Source-specific average of component contraction or
  expansion factors; score direction must be stored per variant.
- **Exact aliases:** None across input, output, and graph Russell measures.
  Tone (2001, p. 507) nevertheless identifies the matched input and output
  Russell formulations with the corresponding oriented SBM accounts on the
  standard positive domain. That conditional representation does not merge
  the three Russell orientations.
- **Distinct variants:** Enhanced Russell graph (ERG), standard non-oriented
  SBM, and later monotonicity-enhanced Russell formulations.
- **Domain:** Depends on the denominators and monotonicity properties of the
  selected Russell formulation.
- **Failures:** Treating all Russell measures as one formula, silently using
  zero denominators, or calling a graph measure input/output oriented.
- **Solver form:** Linear, fractional, or transformed program depending on the
  source-qualified variant.
- **Defining source:** [Färe and Lovell
  1978](https://doi.org/10.1016/0022-0531(78)90060-1);
  [Färe, Grosskopf, and Lovell
  1985](https://doi.org/10.1007/978-94-015-7721-2).
- **Evidence status:** primary-checked. The classic input and output
  formulations are implemented/public as exact-domain aliases of the matched
  Tone leaves, with repository property evidence; graph Russell remains
  registry-provisional/planned.
- **Oracle:** candidate — source examples have been identified but not
  reproduced in automated repository tests.
- **Package recipe:** Family `static.russell`; `InputRussell` resolves to
  `static.sbm.input.tone2001`, and `OutputRussell` resolves to
  `static.sbm.output.tone2001` under DEAPack's reciprocal output-score
  convention. Graph Russell remains a separate planned leaf.
- **Book location:** **Documentation/source review only.** Russell measures do
  not receive independent placement in the current handbook.

### `static.sbm.nonoriented.tone2001` — standard non-oriented ERG/SBM

- **Economic question:** How much average proportional resource excess and
  service shortfall remains when every variable may improve non-radially?
- **Technology / estimator / inference:** Convex free-disposal technology;
  full DEA estimator; no inference in the base recipe.
- **Measure:** Standard non-oriented fractional slack-based efficiency.
- **RTS:** CRS or VRS is explicit and does not create a new alias.
- **Data / time:** Strictly positive inputs and desirable outputs on the exact
  equivalence domain; reference-sample dependence is retained.
- **Native score:** $\rho_o\in[0,1]$, with one best, for every feasible
  standard fit because normalized slacks are nonnegative. An external/custom
  reference may instead make the task infeasible; its reference status is
  retained. A value of one certifies zero normalized input and output slacks
  in the non-oriented account; target multiplicity remains separate.
- **Exact aliases:** Pastor--Ruiz--Sirvent's standard enhanced Russell graph
  measure and Tone's standard non-oriented SBM are one executable method **only
  on the matched strictly positive domain, technology, weights, and
  normalization**. Package symbols `SBM` and `ERG` therefore resolve to this
  canonical ID rather than two solvers. The exact algebraic relationship is
  confirmed in [Aparicio, Pastor, and Zofío
  2023](https://doi.org/10.1007/s10957-023-02188-2).
- **Distinct variants:** Input- or output-oriented SBM, weighted SBM,
  super-SBM, network SBM, dynamic SBM, undesirable-output SBM, zero/signed-data
  extensions, and nonstandard ERG variants. These alter the measure,
  technology, graph, reference, or domain and are not aliases.
- **Domain:** Strictly positive denominators for the standard ratio
  interpretation. Zeros, negatives, and empty input/output blocks require a
  named extension or fail-closed policy.
- **Failures:** Zero denominators, invalid Charnes--Cooper normalization,
  alternate optimal targets, solver residuals, treating an oriented result as
  this two-sided score, and reporting a transformed score without the native
  numerator and denominator.
- **Solver form:** Linear-fractional program solved by an exact
  Charnes--Cooper linearization.
- **Defining source:** ERG [Pastor, Ruiz, and Sirvent
  1999](https://doi.org/10.1016/S0377-2217(98)00098-8); SBM [Tone
  2001](https://doi.org/10.1016/S0377-2217(99)00407-5).
- **Evidence status:** primary-checked, including the exact-equivalence domain;
  implemented/public with repository property and literature-oracle evidence.
- **Oracle:** `sbm_slack_contrast` is a neutral analytical case that checks the
  non-oriented CRS score, normalized slack accounts, targets, peers, and
  radial-versus-non-radial distinction without redistributing the source
  table.
- **Package recipe:** `SlacksBasedDEA`, `SBM`, and `ERG`;
  `static.sbm.nonoriented.tone2001`.
- **Book location:** **Active core placement:** `book/chapters/02-classical/04-sbm.md`; equivalence proofs and source variants remain in package documentation.

### `static.sbm.input.tone2001` — input-oriented SBM

- **Economic question:** After management removes the greatest average
  normalized input excess compatible with maintaining delivered outputs,
  what average share of observed resource use remains?
- **Technology / estimator / inference:** The same convex free-disposal
  technology, full DEA estimator, eligible references, and deterministic
  inference status as the standard non-oriented leaf.
- **Measure:** Tone's input-oriented normalized resource-retention account,
  $\rho_o^I=1-m^{-1}\sum_i s_i^-/x_{io}$. The removed share is
  $1-\rho_o^I$; $\rho_o^I$ itself is the average share retained after the
  maximal input-excess programme. Output slacks preserve feasibility but do
  not enter the objective.
- **RTS:** Tone (2001) explicitly supplies CRS and VRS. The public package
  also exposes NIRS and NDRS through DEAPack's common convex-envelopment
  restrictions, but those are package extensions and are outside the Tone
  analytical certificate.
- **Data / time:** Cross-sectional or panel quantity data under the selected
  reference policy; every evaluated input and output denominator is strictly
  positive.
- **Native score:** $\rho_o^I\in[0,1]$, higher is better. A score of one
  certifies the input-slack account only. `is_sbm_efficient` has this
  orientation-specific meaning; generic `is_efficient` is not certified.
- **Exact aliases:** `InputRussell` resolves to this canonical leaf when
  technology, RTS, reference population, equal-dimension normalization,
  strictly positive domain, score convention, and target policy match. Tone
  (2001, p. 507) establishes the underlying input Russell identity. There is
  no alias with the non-oriented ERG/SBM or output-oriented SBM; the three
  Tone leaves remain Level B distinct measures.
- **Distinct variants:** Non-oriented and output-oriented Tone SBM; weighted,
  super, environmental, network, dynamic, and source-qualified zero/signed
  SBM formulations.
- **Domain:** Tone's standard strictly positive input/output domain. Zeros,
  negative values, and undocumented translations or epsilon denominators are
  rejected rather than merged.
- **Failures:** Reading score one as Pareto--Koopmans efficiency; treating a
  solver-selected output slack or target as unique, closest, or strongly
  efficient; or importing the non-oriented ERG alias.
- **Solver form:** Shared sparse SBM balance/reference compiler with the
  input-oriented objective and identity normalization; one primary LP per
  evaluated observation.
- **Defining source:** [Tone
  (2001)](https://doi.org/10.1016/S0377-2217(99)00407-5).
- **Evidence status:** primary-checked; implemented/public with an exact VRS
  analytical fixture and an independently compiled CRS/VRS dense-LP check.
- **Oracle:** analytically derived — the synthetic A/B/O fixture gives
  $(\rho_A^I,\rho_B^I,\rho_O^I)=(1,1,3/4)$ under VRS. Tone's Table 2 is the
  non-oriented CRS oracle; no published numerical input-oriented oracle has
  been located, so published reproduction is explicitly false and deferred
  to a later evidence version. NIRS/NDRS, unique peers, individual slacks,
  and unique targets are not certified.
- **Package recipe:** `InputOrientedSlacksBasedDEA` / `InputSBM` /
  `InputRussell`;
  `static.sbm.input.tone2001`. Output-side target rows are labeled
  `solver_selected_primary_optimum`.
- **Book location:** **Active core placement:** `book/chapters/02-classical/04-sbm.md`; orientation-specific score and target contracts remain in package documentation.

### `static.sbm.output.tone2001` — output-oriented SBM

- **Economic question:** How much could management expand delivered services
  on average without requiring more than the observed resources?
- **Technology / estimator / inference:** The same convex free-disposal
  technology, full DEA estimator, eligible references, and deterministic
  inference status as the standard non-oriented leaf.
- **Measure:** The direct output programme optimizes
  $\tau_o^O=1+s^{-1}\sum_r s_r^+/y_{ro}$. DEAPack retains this native
  expansion account as `output_expansion_factor` and reports the reciprocal
  higher-is-better efficiency $\rho_o^O=1/\tau_o^O$. Input slacks preserve
  feasibility but do not enter the objective.
- **RTS:** Tone (2001) explicitly supplies CRS and VRS. The public package
  also exposes NIRS and NDRS through DEAPack's common convex-envelopment
  restrictions, but those are package extensions and are outside the Tone
  analytical certificate.
- **Data / time:** Cross-sectional or panel quantity data under the selected
  reference policy; every evaluated input and output denominator is strictly
  positive.
- **Native score:** $\rho_o^O\in[0,1]$, higher is better. A score of one
  certifies the output-slack account only. `is_sbm_efficient` has this
  orientation-specific meaning; generic `is_efficient` is not certified.
  The result also retains the directly optimized expansion factor
  $\tau_o^O=1/\rho_o^O$ as `output_expansion_factor`.
- **Exact aliases:** `OutputRussell` resolves to this canonical leaf when
  technology, RTS, reference population, equal-dimension normalization,
  strictly positive domain, reciprocal higher-is-better score convention, and
  target policy match. Tone (2001, p. 507) establishes the underlying output
  Russell identity. There is no alias with the non-oriented ERG/SBM or
  input-oriented SBM; the three Tone leaves remain Level B distinct measures.
- **Distinct variants:** Non-oriented and input-oriented Tone SBM; weighted,
  super, environmental, network, dynamic, and source-qualified zero/signed
  SBM formulations.
- **Domain:** Tone's standard strictly positive input/output domain. Zeros,
  negative values, and undocumented translations or epsilon denominators are
  rejected rather than merged.
- **Failures:** Reading score one as Pareto--Koopmans efficiency; treating a
  solver-selected input slack or target as unique, closest, or strongly
  efficient; or importing the non-oriented ERG alias.
- **Solver form:** Shared sparse SBM balance/reference compiler with a direct
  LP maximizing the mean normalized output-expansion factor; the reported
  higher-is-better efficiency is its reciprocal. Charnes--Cooper is required
  only by the non-oriented ratio. The output leaf uses one primary LP per
  evaluated observation.
- **Defining source:** [Tone
  (2001)](https://doi.org/10.1016/S0377-2217(99)00407-5).
- **Evidence status:** primary-checked; implemented/public with an exact VRS
  analytical fixture and an independently compiled CRS/VRS dense-LP check.
- **Oracle:** analytically derived — the synthetic A/B/O fixture gives
  $\tau^O=(1,1,3/2)$ and reported
  $\rho^O=(1,1,2/3)$ under VRS. Tone's Table 2 is the non-oriented CRS
  oracle; no published numerical output-oriented oracle has been located, so
  published reproduction is explicitly false and deferred to a later
  evidence version. NIRS/NDRS, unique peers, individual slacks, and unique
  targets are not certified.
- **Package recipe:** `OutputOrientedSlacksBasedDEA` / `OutputSBM` /
  `OutputRussell`;
  `static.sbm.output.tone2001`. Input-side target rows are labeled
  `solver_selected_primary_optimum`.
- **Book location:** **Active core placement:** `book/chapters/02-classical/04-sbm.md`; orientation-specific score and target contracts remain in package documentation.

### `static.ebm` — epsilon-based measure

- **Economic question:** How can management combine an overall proportional
  improvement programme with variable-specific shortfall information in one
  declared compromise?
- **Technology / estimator / inference:** Convex envelopment technology; full
  DEA estimator; no inference in the base recipe.
- **Measure:** A source-qualified mixture of radial and non-radial components,
  with an estimated or declared epsilon and diversity measure.
- **RTS:** Explicit.
- **Data / time:** Typically non-negative cross-sectional quantities;
  correlation/diversity estimation is sample dependent.
- **Native score:** Source-specific EBM efficiency; retain the fitted epsilon,
  diversity construction, and component slacks.
- **Exact aliases:** None. EBM is not a weighted average of independently
  fitted radial and SBM scores.
- **Distinct variants:** Input/output/non-oriented EBM, network EBM, undesirable
  EBM, and alternative diversity/epsilon estimators.
- **Domain:** Requires a valid diversity matrix and a documented policy for
  constants, collinearity, zeros, and signed values.
- **Failures:** Treating data-derived epsilon as a harmless default, unstable
  diversity weights, nonpositive denominators, and mismatched target phases.
- **Solver form:** Source-dependent nonlinear/fractional program or equivalent
  transformation; implementation must be frozen against the defining paper
  before backend choice.
- **Defining source:** [Tone and Tsutsui
  2010](https://doi.org/10.1016/j.ejor.2010.07.014).
- **Evidence status:** the automatic affinity/PCA family remains
  `deferred_to_next_version`. The source's calibration population, projection
  selector, repeated-dominant-root rule, and one published table lineage do
  not yet define a deterministic estimator. The earlier
  cost-share/parameter-epsilon lineage is not an alias for that procedure.
- **Oracle:** the automatic chain remains a candidate with explicit blockers.
  Separately, the input-oriented CRS equations (6)--(8) and their declared
  parameter evaluator have a production-free published-chain oracle and
  certified public implementation tests.
- **Package recipe:** `static.ebm` and the automatic full identity
  `static.ebm.input.tone_tsutsui_2010.crs` remain deferred. The admitted
  `static.ebm.input.tone_tsutsui_2010.crs.declared` leaf is a conditional,
  source-qualified evaluator: `InputOrientedEpsilonBasedDEA` requires a
  provenance-bound `DeclaredEBMCalibration`, fixes input orientation/CRS/one
  self-inclusive cross-section, leaves theta free, and does not run affinity
  or PCA. It reports one solver-selected input-mix target and never aliases
  epsilon one to SBM.
- **Book location:** a concise advanced bridge appears in
  `book/chapters/02-classical/04-sbm.md`; the calibration and certificate
  contract remains in package Documentation.

## 3. What joint or variable-specific improvement programme is feasible?

### `static.directional_distance` — directional distance function

- **Economic question:** How far can a declared management programme reduce
  selected resources and/or expand selected services at the same time?
- **Technology / estimator / inference:** Declared convex production
  technology; full DEA estimator; inference is separate and
  estimator/direction specific.
- **Measure:** Maximum feasible movement $\beta_o$ along a declared direction
  $g$, with package sign conventions fixed in `CONVENTIONS.md`.
- **RTS:** Explicit.
- **Data / time:** Cross-sectional or cross-period evaluation data; directions
  may be common, observation-specific, policy targets, or economically scaled,
  but their source and units must be stored.
- **Native score:** Directional expansion amount $\beta_o$, normally zero on
  the boundary and larger when more declared improvement is feasible.
- **Exact aliases:** Matching input/output radial scores can be obtained by
  exact transforms only with observation-scaled pure input or pure output
  directions and matched signs, technology, reference, and target policy.
- **Distinct variants:** Environmental DDF, generalized distance,
  multi-directional efficiency analysis, the source-fixed 2004
  range-directional measure, subvector/component distances, and directional
  super-efficiency.
- **Domain:** Direction components and data signs must make the proposed
  movement economically meaningful; a zero direction in every active block is
  invalid.
- **Failures:** Arbitrary direction choice, mixing quantities with incompatible
  units, clipping negative cross-technology distances, and calling a
  constraint on bad outputs a complete environmental technology.
- **Solver form:** Linear program for polyhedral technologies.
- **Defining source:** [Chambers, Chung, and Färe
  1996](https://doi.org/10.1006/jeth.1996.0096).
- **Evidence status:** primary-checked; implemented/public with a
  claim-scoped analytical certificate.
- **Oracle:** analytically derived — a three-activity rational fixture proves
  the three observed-direction programmes under CRS, VRS, NIRS, and NDRS,
  including exact observed-joint slack completions. A separate
  two-input/two-output fixture independently compiles both phases for four
  fixed directions and both execution modes. It uses the same SciPy/HiGHS
  optimizer class and is therefore an independent equation-compilation
  cross-check, not a published-table or independent-solver reproduction.
  Negative distances, custom/external/panel references, undesirable outputs,
  untested direction resolvers, unique peers, and inference remain outside
  the certificate.
- **Package recipe:** `DirectionalDistanceDEA` / `DDF`;
  `static.directional_distance`. The original RDM is a separate public preset
  that composes this compiler under a narrower signed-data contract.
- **Book location:** **Active core placement:** `book/chapters/02-classical/05-directional-distance.md`; environmental compositions and inferential extensions retain their own routes or package documentation.

#### Source-qualified 2004 range-directional composition

[Portela, Thanassoulis, and Simpson
(2004)](https://doi.org/10.1057/palgrave.jors.2601768) replace an arbitrary
analyst-supplied direction with the focal organization's remaining observed
room for improvement: each input is compared with the lowest observed input
in the exact reference population, and each desirable output with the highest
observed output there. The resulting common factor asks what share of those
account-specific opportunities can be realized together. This construction
continues to have an economic interpretation when recorded levels are zero or
negative, provided “less input” and “more desirable output” remain meaningful.

The public `static.range_directional.portela_thanassoulis_simpson_2004` leaf
therefore freezes VRS, identical populations for the extrema and production
technology, focal-unit self-inclusion, and input, output, or non-oriented
programmes. Its native $\beta$ is remaining feasible improvement; the
higher-is-better report is $1-\beta$. An all-zero active range is an
unbounded-direction failure, not an efficiency score. Phase-one targets can
retain residual slack and are not advertised as Pareto efficient.

The implementation is cross-checked against an independent equation
compiler on an exact signed rational fixture and against the source's
published target transcription. Compiler reuse does not make RDM equivalent
to a generic DDF, RAM, SORM, inverse RDM, radial DEA after translation, or an
environmental DDF: those alternatives change the direction rule,
normalization, technology, score, or economic role of an output.

### Planned direction-selection policies

The DDF direction is an economic definition of the improvement programme, not
just solver input. Planned policies distinguish *direction.exogenous*,
*direction.observation_scaled*, *direction.range_ideal*, and
*direction.endogenous_value.petersen_2018*.

- **Eleven-axis placement:** $M$ records the improvement account, $V$ the
  value basis, and $P$ whether the direction is declared ex ante or selected
  by an optimization protocol. Only fixed parameters of an already named
  policy belong in $\Theta$.
- **Equivalence boundary:** Different declared directions are Level B when
  they change the measure over one technology; endogenous value-based
  selection is Level D when it adds a coupled selection protocol. None is a
  Level-A spelling alias.
- **Defining source:** Endogenous value directions in
  [Petersen (2018)](https://doi.org/10.1287/opre.2017.1711).
- **Evidence status:** planned/evidence only. The categories require
  source-specific equation, invariance, target, and oracle audits before
  registration or implementation.
- **Failure:** Choosing a direction after inspecting scores without recording
  the policy creates an undisclosed estimand change.

### `static.subvector_distance` and multi-directional analysis

- **Economic question:** What can a manager improve when only a named subset
  of resources or services is controllable, and what are the attainable
  variable-by-variable potentials?
- **Technology / estimator / inference:** Same declared technology and full
  estimator as the composed DDF/radial task; no automatic inference.
- **Measure:** Subvector/component distance fixes non-adjustable quantities;
  multi-directional efficiency analysis first estimates component potentials,
  then constructs and evaluates a declared ideal direction.
- **RTS:** Explicit and shared across component tasks unless a source requires
  otherwise.
- **Data / time:** Cross-sectional quantities with managerial-control metadata.
- **Native score:** Component distance or source-qualified aggregate of
  attainable component potentials.
- **Exact aliases:** None between subvector distance and post-hoc inspection of
  slacks; none between multi-directional analysis and a single DDF with an
  arbitrary direction.
- **Distinct variants:** Short-run/quasi-fixed-input models, energy-specific
  efficiency, priority targets, and closest-target procedures.
- **Domain:** The adjustable subset and fixed commitments must be declared
  before fitting.
- **Failures:** Granting target rights over non-discretionary quantities,
  combining component distances with incompatible scales, and data-dependent
  direction leakage without provenance.
- **Solver form:** A family of LPs plus a declared aggregation/evaluation step.
- **Defining source:** Component efficiency is grounded in production-distance
  theory in [Färe et al.
  1994](https://doi.org/10.1007/978-94-015-7721-2); multi-directional variants
  require source-qualified leaves rather than one generic citation.
- **Evidence status:** review-supported but `deferred_to_next_version`;
  exact source-qualified leaves remain to be frozen. A zero component in a
  generic DDF direction is not enough to establish the source score or target
  contract.
- **Oracle:** not located — no certified numerical example has been selected.
- **Package recipe:** Deferred `static.subvector_distance` under
  `source_protocols/subvector_distance.md`; no public API or machine record.
  `static.multi_directional_efficiency` remains a separately planned
  procedure and is not inferred from the subvector family.
- **Book location:** **Documentation/source review only.** Subvector and
  multi-directional variants have no independent handbook placement.

### Hyperbolic, generalized-distance, and multiplicative families

- **Economic question:** How should a proportional performance gap be
  expressed through resource saving and service growth, how does that
  technical account connect to profitability, or which piecewise
  Cobb--Douglas production account best envelops a strictly positive
  resource--service plan?
- **Technology / estimator / inference:** Hyperbolic/generalized paths are
  measures over a declared technology; multiplicative DEA also changes the
  maintained technology to a positive-data piecewise log-linear envelope.
  The public multiplicative family uses one full-frontier estimator and one
  shared log-space compiler for its two source variants; no automatic
  inference is attached.
- **Measure:** One core standard hyperbolic distance where source path
  equations match, source-qualified generalized hyperbolic paths,
  Chavas--Cox generalized distance, or multiplicative efficiency.
- **RTS:** The public Chavas--Cox leaf supports CRS and VRS. Under CRS,
  $\delta$ equals the input-radial score for every
  $\alpha\in[0,1]$, although contract multipliers and intensities change.
  Under VRS, $\alpha$ can change the score and comparator mix. Ordinary
  CRS/VRS labels do not describe the multiplicative technology: the 1982
  original is log-conic without a convexity identity, whereas the 1983
  invariant model is log-convex with `sum(lambda)=1` in log quantities.
- **Data / time:** The public GDF leaf supports nonnegative quantities with
  positive aggregate input and output and exact structural-zero feasibility.
  Both multiplicative variants exclude undesirable outputs. The invariant
  1983 model requires every ordinary input and desirable output to be
  strictly positive; the original 1982 source requires each to be strictly
  greater than one. Their source profile is one self-inclusive global cross
  section. Panel and non-global reference rules are supported only as labelled
  package extensions.
- **Native score:** The public GDF score is
  $\delta=\min\{\delta>0:
  (\delta^{1-\alpha}x,\delta^{-\alpha}y)\in T\}$, higher is better.
  Public multiplicative efficiency is
  $\exp(-\text{log_inefficiency})$, also higher is better, while nonnegative
  `log_inefficiency` remains available to avoid losing information to
  exponentiation range limits. The 1982 exponent floor is fixed at one; a
  finite positive 1983 floor is an explicit score-power convention. No common
  generic “hyperbolic score” is assumed.
- **Exact aliases:** Chavas--Cox endpoints recover matched input- and
  output-radial scores. Its $\alpha=1/2$ coordinates match the modern standard
  reciprocal HDF path only conditionally: if $h$ is the direct path factor,
  then $\delta=h^2$. That algebra does not freeze the source-native 1985
  Farrell-graph index, whose printed relationship in Chavas--Cox conflicts
  with the direct substitution and must be resolved from the original pages.
  Ordinary and environmental sources may share the core hyperbolic $M$ only
  after the path and native transform are proved identical; their attached
  $D/T$ remain Level C-distinct source presets. Multiplicative DEA is not an
  alias obtained by merely logging data before ordinary DEA, is neither the
  CCR multiplier form nor ordinary CRS/VRS envelopment, and hyperbolic is not
  a generic DDF alias.
- **Distinct variants:** “Generalized hyperbolic” is not one method name. The
  1985 generalized Farrell graph, Chavas--Cox GDF, Halická--Trnovská--Černý
  direction-vector HDF-g, Wilson's subset-fixed generalized HDF, and the
  generalized multiplicative directional distance over a log-linear
  technology have different paths, technologies, native scores, or adjustable
  subsets and must remain separate source lineages. None is a `variant=` value
  inferred from another. Within the public multiplicative family, the 1982
  original log-conic and 1983 invariant log-convex recipes are catalog presets
  over one compiler, not aliases of one another and not duplicate method
  records.
- **Domain:** The public GDF requires $\alpha\in[0,1]$, CRS/VRS, finite
  nonnegative quantities, and at least one positive input and output per
  observation. Multiplicative data must satisfy the stricter variant-specific
  domains above; zeros, negative values, undesirable outputs, arbitrary
  epsilon repairs, and additive translations are rejected. The invariant
  1983 variant is invariant to independent positive coordinate rescaling;
  the original 1982 variant is not.
- **Failures:** Conflating different path equations, applying logarithms to
  zeros/negatives, claiming profitability duality without its price and
  normalization conditions, treating original-unit target overflow as a
  failed log result, accepting malformed solver marginals, and using a
  nonlinear solver without global or certified optimality checks.
- **Solver form:** Public GDF endpoints reduce exactly to input/output radial
  LPs; every CRS bearing reduces exactly to input-radial DEA; an interior VRS
  bearing uses row-scaled fixed-$\delta$ LP feasibility and certified
  geometric bisection. The public multiplicative family uses one immutable
  sparse log-space LP template per reference set, shared by both variants,
  with primal, target-account, and multiplier certification. It is not an
  ordinary radial compiler fed logged observations. Other leaves may be
  nonlinear, fractional, conic, or transformed LPs.
- **Defining source:** Multiplicative DEA
  ([Charnes et al. 1982](https://doi.org/10.1016/0038-0121(82)90029-5);
  [Charnes et al. 1983](https://doi.org/10.1016/0167-6377(83)90014-7));
  generalized distance [Chavas and Cox
  1999](https://doi.org/10.1002/j.2325-8012.1999.tb00248.x); original
  hyperbolic graph chapter [Färe, Grosskopf, and Lovell
  (1985)](https://doi.org/10.1007/978-94-015-7721-2); later unified HDF and
  HDF-g treatment [Halická, Trnovská, and Černý
  (2024)](https://doi.org/10.1016/j.ejor.2023.06.039); core
  environmental hyperbolic account
  [Färe et al. (1989)](https://doi.org/10.2307/1928055) and exact-computation
  context [Färe, Margaritis, Rouse, and Roshdi
  (2016)](https://doi.org/10.1016/j.ejor.2016.03.045).
- **Evidence status:** `static.generalized_distance.chavas_cox` is
  implemented/public and primary-checked. `static.multiplicative` is also
  implemented/public and primary-checked as one family with two catalog
  preset identities:
  `static.multiplicative.original.charnes_etal_1982` and
  `static.multiplicative.invariant.charnes_etal_1983`. The standard standalone
  hyperbolic leaf is `deferred_to_next_version` under
  `source_protocols/standard_hyperbolic.md`: its modern reciprocal equation,
  conditional `delta = h^2` composition, and seven-DMU oracle are established,
  but the complete 1985 definition, source-native score/power convention,
  zero-coordinate domain, and path-versus-strong-target policy are not frozen.
  Every generalized lineage remains separately planned and must pass its own
  equation, domain, target, and oracle gate.
- **Oracle:** `cross-implemented` for GDF--the fixed
  [DataEnvelopmentAnalysis.jl test](https://github.com/javierbarbero/DataEnvelopmentAnalysis.jl/blob/ca17532cd4de4e47d159cee563c05d9a0db6a61c/test/deaprofitability.jl#L4-L45)
  reproduces the Zofío--Prieto CRS/VRS five-unit vectors. Endpoint, CRS
  invariance, unit, target, structural-zero, and failure properties are also
  automated. `Analytically derived` for multiplicative DEA--an exact two-DMU
  certificate and an independently compiled dense source LP reproduce both
  source variants' scores, log slacks, peers, and targets; separate exact
  accounts check multiplier restoration, unit behavior, and the 1983
  score-power convention. No published numerical reproduction is claimed for
  the multiplicative family. `Cross-implemented and analytically derived` for
  the modern standard HDF convention--the seven-DMU VRS fixture documented in
  CRAN `DJL` 3.9 as reproducing Färe et al. (2016) gives
  $(1,1,1,1,0.518670608516\ldots,0.452035741742\ldots,
  0.863606693226\ldots)$, with the last three values independently recovered
  from exact quadratic frontier intersections. This numerical evidence does
  not resolve the 1985 native score convention or promote the leaf. No oracle
  is claimed for the generalized-hyperbolic lineages.
- **Package recipe:** `GeneralizedDistanceDEA`, `ChavasCoxGDF`, and `GDF`
  are exact API aliases for `static.generalized_distance.chavas_cox`.
  A future `static.hyperbolic.standard_reciprocal` leaf must be a thin,
  source-qualified preset over the matched `alpha=0.5` GDF path if the
  score-transform gate passes; it must not duplicate the solver. Ordinary and
  environmental source presets retain provenance and attached technologies.
  `MultiplicativeDEA` is the shared family API;
  `C2S2MultiplicativeDEA` and `InvariantMultiplicativeDEA` emit the 1982 and
  1983 catalog preset IDs while retaining `static.multiplicative` as their
  result `method_id`. A generic numerically matching call does not infer a
  historical preset identity. Never expose one `path="anything"` solver
  without source-qualified metadata.
- **Book location:** **Documentation/source review only.** Hyperbolic,
  generalized-distance, and multiplicative variants have no independent placement in the current handbook.

## 4. What changes when prices or economically meaningful values are known?

### `economic.cost` — minimum-cost efficiency

- **Economic question:** What is the least expenditure capable of meeting the
  current output commitment, and how much of the observed cost excess is
  technical versus allocative?
- **Technology / estimator / inference:** Convex CRS or VRS quantity
  technology; full DEA estimator; no inference in the current recipe.
- **Measure:** Minimum feasible input cost, observed-minus-minimum cost gap,
  cost efficiency, and matched input-radial technical/allocative decomposition.
- **RTS:** CRS and VRS are implemented and must be reported.
- **Data / time:** Complete finite strictly positive input prices, common or
  unit-specific, aligned to the quantity data; cross-sectional valuation unless
  a base-period price policy is declared.
- **Native score:** $CE_o=C_o^*/C_o$, with one best when the evaluated unit
  belongs to its reference technology; retain $C_o$, $C_o^*$, and the cost
  gap.
- **Exact aliases:** None with radial technical efficiency. Under a matched
  composition, $CE_o=TE_o^I AE_o^C$ is a decomposition identity, not an
  alias.
- **Distinct variants:** Short-run cost with quasi-fixed inputs, indirect cost,
  cost under incomplete/interval prices, environmental cost, and cost
  productivity indexes.
- **Domain:** Price completeness, units, currency, numeraire, scope, and
  quantity-price alignment are mandatory; shutdown and free-disposal policy
  must be explicit.
- **Failures:** Missing/nonpositive prices, zero observed cost, infeasible
  output commitments, unbounded technology, failure to label and retain an
  external-reference ratio above one, and confusing supplied prices with DEA
  multiplier weights.
- **Solver form:** Linear cost-minimization program; matched radial LP for the
  decomposition.
- **Defining source:** Production duality and economic efficiency in [Färe et
  al. 1994](https://doi.org/10.1007/978-94-015-7721-2).
- **Evidence status:** primary-checked; implemented/public with automated
  objective, target, and decomposition tests.
- **Oracle:** `cost_mix_choice` is a neutral analytical case that checks
  minimum-cost targets, observed/minimum cost reconstruction, and the matched
  technical--allocative decomposition. The DEAP guide remains a method
  reference, but its numerical example is not redistributed.
- **Package recipe:** `CostEfficiency` / `economic.cost`; matched
  `AllocativeDecomposition` /
  `analysis.allocative_decomposition.cost_input_radial`.
- **Book location:** **Active core placement:** `book/chapters/02-classical/economic-efficiency-under-prices.md`.

### `economic.revenue` — maximum-revenue efficiency

- **Economic question:** Given available inputs, what output mix has the
  greatest attainable revenue, and is the shortfall due to unused productive
  capacity or the output portfolio?
- **Technology / estimator / inference:** Convex CRS or VRS quantity
  technology; full DEA estimator; no inference in the current recipe.
- **Measure:** Maximum feasible output revenue, maximum-minus-observed gap,
  revenue efficiency, and matched output-radial technical/allocative
  decomposition.
- **RTS:** CRS and VRS are implemented and must be reported.
- **Data / time:** Complete finite strictly positive output prices, common or
  unit-specific, with units, scope, and base-period policy.
- **Native score:** $RE_o=R_o/R_o^*$, with one best for an internal evaluated
  unit; retain $R_o$, $R_o^*$, the expansion ratio, and the revenue gap.
- **Exact aliases:** None with output-radial technical efficiency. Under a
  matched composition, $RE_o=TE_o^O AE_o^R$ is a decomposition identity.
- **Distinct variants:** Revenue with restricted output mix, incomplete
  prices, environmental outputs, network transfer values, and revenue
  productivity.
- **Domain:** Price completeness/alignment and a well-defined positive maximum
  revenue; an output-radial target and a revenue-maximizing activity are
  different plans.
- **Failures:** Zero maximum revenue, infeasible references, failure to label
  and retain an external-reference ratio above one, scale mismatches, and
  reconstructing the optimum from the radial target rather than the revenue
  target.
- **Solver form:** Linear revenue-maximization program; matched radial LP for
  the decomposition.
- **Defining source:** Production duality in [Färe et al.
  1994](https://doi.org/10.1007/978-94-015-7721-2).
- **Evidence status:** primary-checked; implemented/public with automated
  objective, target, and decomposition tests.
- **Oracle:** cross-implemented — automated tests reproduce the eight-unit VRS
  and five-unit unequal-price CRS/VRS results documented by
  [BenchmarkingEconomicEfficiency.jl](https://javierbarbero.github.io/BenchmarkingEconomicEfficiency.jl/stable/revenue/revenue/)
  and
  [DataEnvelopmentAnalysis.jl](https://javierbarbero.github.io/DataEnvelopmentAnalysis.jl/stable/economic/revenue/).
- **Package recipe:** `RevenueEfficiency` / `economic.revenue`; matched
  `RevenueAllocativeDecomposition` /
  `analysis.allocative_decomposition.revenue_output_radial`.
- **Book location:** **Active core placement:** `book/chapters/02-classical/economic-efficiency-under-prices.md`.

### Maximum profit and the raw profit gap

- **Economic question:** If managers may revise both resource use and the
  output portfolio at the prices they face, what is the greatest attainable
  profit and how much profit does the observed plan forgo?
- **Technology / estimator / inference:** Convex quantity technology with
  supplied input and desirable-output prices; full DEA estimator; no
  inferential claim in the base recipe.
- **Measure:** $\Pi_o^*=\max_{(x,y)\in T}\{p_o^\top y-w_o^\top x\}$ and
  `profit_gap` $=\Pi_o^*-\Pi_o$.
- **RTS:** The first executable leaf is VRS, $\mathbf 1^\top\lambda=1$, which is
  finite but excludes shutdown. Under unconstrained CRS any positive-profit
  activity generates an unbounded ray; shutdown does not cure that ray.
- **Data / time:** Complete aligned input and output prices with declared
  scope, currency, numeraire, and, for panels, base period.
- **Native score:** Monetary profit gap, zero best and lower better.
  `efficiency` is missing because observed/maximum profit is not an
  order-preserving ratio when either profit is zero or negative.
- **Exact aliases:** “Maximum-profit shortfall” and “raw profit gap” identify
  this value difference only when prices, technology, reference, RTS, and
  shutdown policy match.
- **Distinct variants:** Shutdown-enabled technology; cost or revenue
  efficiency; profitability/return-to-dollar; CCF Nerlovian normalization;
  radial, Russell, additive, SBM, Hölder, modified/reverse DDF, and general
  direct profit decompositions; environmental profit.
- **Domain:** The current public leaf uses nonnegative quantities, complete
  finite strictly positive prices, desirable outputs only, and a finite VRS
  reference simplex. Observed and maximum profit may be negative.
- **Failures:** Unbounded positive-profit scale rays, silently adding the
  origin, clipping an external-reference negative gap, incomplete prices,
  price/quantity unit mismatch, and presenting a profit ratio as efficiency.
- **Solver form:** Sparse linear profit maximization; with a common reference
  and common prices the complete optimum is reusable across observations.
- **Defining source:** Profit and directional production duality in
  [Chambers, Chung, and Färe
  1998](https://doi.org/10.1023/A:1022637501082); DDF foundations in their
  [Benefit and Distance Functions
  paper](https://doi.org/10.1006/jeth.1996.0096).
- **Evidence status:** primary-checked; `economic.profit.maximum`
  implemented/public on the stated VRS domain.
- **Oracle:** cross-implemented — automated tests reproduce the maximum-profit
  and raw-gap values in the fixed public
  [DataEnvelopmentAnalysis.jl test](https://github.com/javierbarbero/DataEnvelopmentAnalysis.jl/blob/ca17532cd4de4e47d159cee563c05d9a0db6a61c/test/deaprofit.jl#L12-L36),
  whose data are attributed there to [Zofío, Pastor, and Aparicio
  2013](https://doi.org/10.1007/s11123-012-0292-0).
- **Package recipe:** Non-executable discovery family `economic.profit`;
  public `ProfitEfficiency` / `economic.profit.maximum`; planned shutdown
  preset `economic.profit.maximum.shutdown`.
- **Book location:** **Active core placement:** `book/chapters/02-classical/economic-efficiency-under-prices.md`; scale, environmental, and alternative decompositions remain in package documentation.

### CCF Nerlovian profit inefficiency

- **Economic question:** Relative to a declared, economically valued operating
  improvement programme, how large is foregone profit, and how much is
  associated with operating execution rather than input/output choice?
- **Technology / estimator / inference:** The same convex quantity technology,
  reference, RTS, prices, and full DEA estimator are used for maximum profit
  and the directional distance component; no inference in the base recipe.
- **Measure:** With
  $\nu_o=w_o^\top g_o^x+p_o^\top g_o^y>0$,
  $NI_o=(\Pi_o^*-\Pi_o)/\nu_o
  =D_{\mathcal T}(x_o,y_o;g_o^x,g_o^y)+AI_o^N$.
- **RTS:** The first executable composition is VRS and excludes shutdown so
  that both component programs use exactly the same finite technology.
- **Data / time:** Joint prices plus explicit nonnegative input-contraction and
  output-expansion directions. Direction and price provenance accompany every
  result; panel monetary comparisons require a common economic time base.
- **Native score:** `nerlovian_inefficiency`, zero best and lower better;
  `technical_inefficiency` is the DDF value and
  `allocative_inefficiency` is the nonnegative additive residual.
- **Exact aliases:** “Normalized profit inefficiency” is an alias only for the
  exact CCF price-valued direction normalizer and matched technology. A
  discoverability alias does not create a second method ID.
- **Distinct variants:** Endogenous profit-maximizing directions, monetary
  directions, lost-profit-on-outlay/modified DDF, reverse DDF, Hölder,
  Russell, additive, SBM, general-direct, environmental, network, and
  noncompetitive-market formulations.
- **Domain:** $g^x,g^y\ge0$, not both zero, and $\nu_o>0$. The current price
  layer is deliberately narrower than the theory and requires complete
  strictly positive prices. Negative observed profit is valid.
- **Failures:** Comparing scores built from economically incomparable
  directions, changing the direction without recording its scale, unmatched
  profit and DDF technologies, outside-reference observations, negative
  allocative residuals beyond tolerance, and ignoring residual DDF slacks.
- **Solver form:** One linear maximum-profit task per unique
  reference/price pair plus observation-level directional LPs and an optional
  slack-completion phase.
- **Defining source:** [Chambers, Chung, and Färe
  1998](https://doi.org/10.1023/A:1022637501082).
- **Evidence status:** primary-checked;
  `economic.nerlovian.ccf1998` implemented/public on the stated VRS domain.
- **Oracle:** cross-implemented — automated tests reproduce all eight
  economic, directional-technical, and allocative values in the fixed public
  [Julia oracle](https://github.com/javierbarbero/DataEnvelopmentAnalysis.jl/blob/ca17532cd4de4e47d159cee563c05d9a0db6a61c/test/deaprofit.jl#L12-L36);
  every oracle projection has zero residual slack.
- **Package recipe:** Non-executable discovery family `economic.nerlovian`;
  public `NerlovianProfitInefficiency` (alias `NerlovianEfficiency`) /
  `economic.nerlovian.ccf1998`, composing
  `economic.profit.maximum` with `static.directional_distance`.
- **Book location:** **Active core placement:** `book/chapters/02-classical/economic-efficiency-under-prices.md`; direction and decomposition variants remain in package documentation.

### Profitability, return-to-dollar, and alternative profit normalizations

- **Economic question:** What output value can be earned per unit of resource
  expenditure, or how should foregone profit be normalized when the
  denominator is cost, revenue, or another source-defined economic quantity?
- **Technology / estimator / inference:** Source-qualified convex quantity
  technology and economic objective; full DEA estimator in the base families;
  no generic inference.
- **Measure:** Return-to-dollar ratio, Chavas--Cox generalized-distance
  profitability, lost profit on outlay, or a source-qualified alternative
  profit decomposition.
- **RTS:** The ordinary DEA maximum return-to-dollar value is identical under
  CRS and VRS because ray scale cancels, but CRS and VRS targets and all GDF
  components retain their declared scale technology.
- **Data / time:** Complete aligned prices and economically meaningful positive
  denominators with declared currency, numeraire, scope, and time base.
- **Native score:** For the public return-to-dollar leaf,
  `profitability_efficiency = observed_profitability /
  maximum_profitability`, higher is better and one is best under
  self-appraisal. Monetary profit gaps and normalized additive
  inefficiencies do not share that interpretation.
- **Exact aliases:** Profitability and return-to-dollar are aliases only under
  the exact output-value/input-expenditure ratio. They are not profit ratios.
- **Distinct variants:** CCF Nerlovian inefficiency; Zofío--Pastor--Aparicio
  directional profit efficiency; Chavas--Cox generalized distance;
  lost-profit-on-outlay; and radial, Russell, additive, SBM, Hölder,
  modified/reverse-DDF, and general-direct decompositions.
- **Domain:** Every denominator and transformation variable must be positive
  on the declared feasible domain; price and quantity units co-transform.
- **Failures:** Calling revenue/cost a profit ratio, a zero expenditure
  denominator, losing VRS restrictions in a Charnes--Cooper transformation,
  and combining components from different normalizers or technologies.
- **Solver form:** The public return-to-dollar kernel uses the exact maximum
  reference ratio; Charnes--Cooper is an LP audit and future constrained
  extension. Alternative decompositions use source-dependent linear,
  monotone-feasibility, nonlinear, or conic programs.
- **Defining source:** Return-to-dollar in [Zofío and Prieto
  2006](https://doi.org/10.1007/s10108-006-9004-0);
  generalized-distance profitability in [Chavas and Cox
  1999](https://doi.org/10.1002/j.2325-8012.1999.tb00248.x);
  lost profit on outlay in [Aparicio, Pastor, and Ray
  2013](https://doi.org/10.1016/j.ejor.2012.10.028).
- **Evidence status:** `economic.profitability.return_to_dollar` and
  `analysis.allocative_decomposition.profitability_gdf.zofio_prieto_2006`
  are implemented/public and primary-checked. Alternative profit
  normalizers remain planned.
- **Oracle:** cross-implemented — the fixed
  [DataEnvelopmentAnalysis.jl test](https://github.com/javierbarbero/DataEnvelopmentAnalysis.jl/blob/ca17532cd4de4e47d159cee563c05d9a0db6a61c/test/deaprofitability.jl#L4-L45)
  reproduces the Zofío--Prieto five-unit profitability, CRS-GDF, and VRS-GDF
  vectors. Automated tests also compare the closed-form value result with
  Charnes--Cooper LPs and check both decomposition identities.
- **Package recipe:** `ReturnToDollarEfficiency` is the primary API;
  `ProfitabilityEfficiency` is an exact discoverability alias with the same
  canonical ID. `GDFProfitabilityDecomposition` and
  `ProfitabilityDecomposition` are exact aliases for the separately
  registered matched composition. No generic executable profitability switch
  exists.
- **Book location:** **Active core placement:** the transferable profitability distinction is taught in `book/chapters/02-classical/economic-efficiency-under-prices.md`; source-qualified normalizations remain in package documentation.

## 5. Is the shortfall caused by scale, capacity, or congestion?

### Radial scale efficiency and related scale analyses

- **Economic question:** Is an organization operating away from its most
  productive scale, and is that different from unused capacity or local
  returns to scale?
- **Technology / estimator / inference:** Matched CRS and VRS convex
  technologies; full DEA estimators; inference is separate.
- **Measure:** CRS/VRS radial efficiency ratio for scale efficiency; separate
  local RTS and scale-elasticity operators. MPSS and physical capacity remain
  distinct questions, but their current reconstructions are deferred,
  non-public prototypes rather than package operators.
- **RTS:** Scale efficiency requires matched CRS and VRS tasks; local RTS is an
  analysis of a specified frontier point, not another RTS setting.
- **Data / time:** Cross-sectional quantities with the same orientation,
  reference membership, and target policy across compared tasks.
- **Native score:** Radial scale-efficiency ratio in $(0,1]$ for matched
  self-inclusive internal CRS/VRS evaluations; external/custom-reference
  compositions require an explicit interpretation and are not clipped. Other
  scale analyses retain their own labels and units.
- **Exact aliases:** None among scale efficiency, IRS/CRS/DRS classification,
  scale elasticity, or the deferred MPSS and capacity-utilization concepts.
- **Distinct variants:** Directional scale elasticity, non-radial scale/mix
  TFP efficiency, quasi-fixed-input capacity, and network/process scale.
- **Domain:** Both component fits must be feasible and comparable.
- **Failures:** Dividing scores from different orientations/references,
  labeling all residual inefficiency “managerial,” and interpreting unused
  capacity as congestion.
- **Solver form:** Composition of two radial LPs; additional optimization or
  supporting-hyperplane analysis for other scale diagnostics.
- **Defining source:** [Banker, Charnes, and Cooper
  1984](https://doi.org/10.1287/mnsc.30.9.1078); broader production theory in
  [Färe et al. 1994](https://doi.org/10.1007/978-94-015-7721-2).
- **Evidence status:** primary-checked; radial scale efficiency is
  implemented/public with a claim-scoped analytical certificate. The Banker--Thrall
  local-RTS leaf below is implemented/public with a reproduced literature
  oracle. The matched one-sided radial scale-elasticity leaf is also
  implemented/public with a reproduced literature oracle. Fixed-observed-mix
  Banker MPSS and Färe--Grosskopf--Kokkelenberg physical capacity are
  `deferred_to_next_version`: internal reconstructions and property checks are
  retained, but neither defining full text has supported an equation freeze
  or independent source-level oracle. Directional elasticity and other
  capacity families remain separately qualified.
- **Oracle:** analytically derived for the radial scale-efficiency ratio. A
  three-activity rational fixture proves the matched CRS and VRS component
  efficiencies, their ratio, and the different input/output classifications;
  a separate two-input/two-output fixture independently compiles both radial
  component programmes. The certificate covers neither custom/panel
  references nor local RTS, the deferred MPSS/capacity prototypes, scale
  elasticity, targets, or inference, and it is not a published-data
  reproduction. The distinct
  local-RTS leaf reproduces the Banker et al. (2004) five-observation example
  described below, while the radial scale-elasticity leaf reproduces the
  seven-unit Førsund--Hjalmarsson example.
- **Package recipe:** `scale_efficiency` /
  `analysis.scale_efficiency.radial_ratio`; local RTS uses the separate
  `analysis.returns_to_scale.local.banker_thrall_1992` leaf and quantitative
  radial response uses `analysis.scale_elasticity.local.radial_vrs`. There is
  no current public MPSS or physical-capacity recipe; their candidate IDs are
  retained only for deferred source auditing.
- **Book location:** **Active core placement:** `book/chapters/02-classical/scale-performance-management.md`; derivations remain in package documentation.

### `analysis.returns_to_scale.local.banker_thrall_1992`

- **Economic question:** At a specified efficient operating plan, would a
  small proportional expansion of all resources support a more than
  proportional, proportional, or less than proportional expansion of
  services? For an inefficient organization, the answer concerns a declared
  efficient projection, not the observed interior activity itself.
- **Technology / estimator / inference:** Banker--Thrall's source-qualified
  local returns-to-scale analysis on a convex VRS DEA frontier. It examines the
  full set of optimal primal intensities or, equivalently under the source
  conditions, the interval of intercepts of optimal supporting hyperplanes.
  It is a post-estimation frontier diagnostic and adds no sampling inference.
- **Measure:** Set-valued supporting evidence summarized by the minimum and
  maximum admissible optimal intercept (or the source-equivalent optimal
  intensity-sum evidence), followed by an IRS/CRS/DRS classification under an
  explicitly recorded multiplier and orientation convention. This is not an
  efficiency percentage.
- **RTS:** The empirical frontier used for projection is VRS; the operator
  classifies local increasing, constant, or decreasing returns rather than
  accepting one of those labels as an input. Zero lying in the admissible
  supporting interval identifies a locally constant-support case; intervals
  strictly on one side are mapped to IRS or DRS only after applying the
  declared source sign convention.
- **Data / time:** Cross-sectional input and output quantities, the evaluated
  DMU, orientation, efficiency/slack status, and an immutable projection
  policy. If an inefficient DMU has multiple efficient projections, the
  result must either retain all admissible classifications or identify the
  selected projection and selection rule.
- **Native score:** `classification`, the supporting-intercept interval and
  sign convention, the evaluated frontier point, projection and reference
  sets, alternate-optimum status, and a flag for set-valued or projection-
  dependent evidence. A lone categorical label is not the native result.
- **Exact aliases:** The optimal-intercept and optimal-intensity-sum routes are
  exact aliases only under Banker--Thrall's matched normalization, projection,
  efficiency, and alternate-optimum conditions.
- **Distinct variants:** The CRS/VRS radial scale-efficiency ratio,
  NIRS/NDRS comparison tests, the deferred most-productive-scale-size
  question, directional returns to scale, and statistical RTS tests. The
  public radial scale-elasticity leaf
  is a distinct quantitative result but deliberately transforms this same
  selected target and support interval rather than solving a duplicate model.
- **Domain:** The classified activity must be on the relevant efficient
  frontier under the source conditions. Supporting programs must preserve the
  base optimum, and every alternate optimum relevant to the interval must be
  considered within numerical tolerance.
- **Failures:** Reading the sign of one arbitrary dual optimum; classifying an
  inefficient observation without naming its projection; suppressing
  projection-dependent classifications; reversing the intercept sign between
  input- and output-oriented formulations; treating weakly efficient
  slack-bearing points as strongly efficient without a completion rule; and
  reporting near-zero solver noise as substantive IRS or DRS.
- **Solver form:** A VRS radial fit and target-status check, followed by two
  auxiliary LPs that minimize and maximize the supporting intercept while
  fixing the attained optimum and declared projection. The source-equivalent
  CCR intensity-sum route may be exposed only with the same multiplicity
  safeguards.
- **Defining source:** [Banker and Thrall
  (1992)](https://doi.org/10.1016/0377-2217(92)90178-C).
- **Evidence status:** primary-checked and implemented/public for input and
  output orientation at the solver-selected Pareto-efficient VRS projection.
  The public result reports both support endpoints, endpoint statuses, the
  admissible RTS set, the exact sign convention, and that projection
  uniqueness is not assessed. No projection-invariance claim is made.
- **Oracle:** reproduced — Equation (7) and pages 349--351 of [Banker et al.
  (2004)](https://www.deafrontier.net/papers/EJORRTSreview.pdf) give the
  five-observation example used in `tests/test_local_rts.py`. The input
  classification is A IRS, B CRS, C CRS, D DRS, with E projected to
  $(3.5,4.5)$, classified DRS, and assigned the unique normalized intercept
  $2/7$. Tests also retain the published interval multiplicity and
  unbounded-endpoint cases.
- **Package recipe:** `local_returns_to_scale` /
  `analysis.returns_to_scale.local.banker_thrall_1992`; the generic
  `analysis.returns_to_scale.local` remains a non-executable discovery
  operator.
- **Book location:** **Active core placement:** `book/chapters/02-classical/scale-performance-management.md`; source-specific sign and projection contracts remain in package documentation.

### `analysis.scale_elasticity.local.radial_vrs`

- **Economic question:** Near the selected efficient operating plan, by what
  percentage can the maximum service bundle change when all resources change
  by one percent? How does the answer differ between a scale-up decision and a
  scale-down decision?
- **Technology / estimator / inference:** Convex VRS DEA with ordinary free
  disposal, evaluated at the same solver-selected Pareto-efficient radial
  projection and complete support interval used by the public Banker--Thrall
  local-RTS operator. This is a deterministic local frontier analysis; it adds
  no sampling inference.
- **Measure:** For
  $\bar\beta(\alpha)=\max\{\beta\mid(\alpha x_o,\beta y_o)\in T\}$,
  the right response is
  $\epsilon^+=\bar\beta'_+(1)$, the left response is
  $\epsilon^-=\bar\beta'_-(1)$, and
  $\epsilon^+\leq\epsilon^-$. With DEAPack's
  $v^\top x-u^\top y+\delta\geq0$ convention, output normalization gives
  $\epsilon^+=1-\bar\delta$ and
  $\epsilon^-=1-\underline\delta$; input normalization gives
  $1/(1+\bar\delta)$ and $1/(1+\underline\delta)$.
- **RTS:** Increasing returns requires
  $1<\epsilon^+\leq\epsilon^-$, decreasing returns requires
  $\epsilon^+\leq\epsilon^-<1$, and the aggregate Banker--Thrall
  constant-returns case is
  $\epsilon^+\leq1\leq\epsilon^-$. At a kink, the last case may combine a
  less-than-proportional scale-up response with a more-than-proportional loss
  under scale-down; it does not imply one unique elasticity equal to one.
- **Data / time:** Nonnegative inputs and desirable outputs with positive
  radial aggregates. Orientation, reference membership, period policy, and
  projection selection are inherited unchanged from the matched local-RTS
  task. Input and output normalizations agree only when they assess the same
  efficient target.
- **Native score:** `scale_elasticity_right`,
  `scale_elasticity_left`, endpoint uniqueness, separate extended-value and
  one-sided perturbation-existence flags, economically worded scale-up and
  scale-down response labels, aggregate RTS, the selected target, and the
  underlying support interval.
- **Exact aliases:** Input- and output-normalized endpoint formulae are exact
  transforms only at the same target. Under standard convex VRS, one-sided RTS
  labels are thresholded views of these endpoints, not a separate estimator.
- **Distinct variants:** Directional, partial, and mixed elasticities;
  weak-disposability and undesirable-output responses; stage or system
  elasticity in network technologies; non-convex FDH incremental/decremental
  ratios; deferred MPSS target search; and monotone global resizing indexes.
- **Domain:** The target must be Pareto efficient and both support endpoint
  tasks must resolve. A finite right endpoint represents a feasible local
  scale-up response. An extended left value may encode a boundary at which no
  proportional contraction exists and must retain that feasibility flag.
- **Failures:** Averaging kink endpoints; treating an infinite formal endpoint
  as infinite physical productivity; assigning elasticity to an inefficient
  observed interior activity rather than its named projection; comparing
  input- and output-oriented results at different targets; and turning IRS
  into an unconditional recommendation to expand without demand, cost,
  service-obligation, or risk information.
- **Solver form:** No new frontier programme. The operator calls the public
  selected-projection Banker--Thrall kernel once and applies orientation-
  specific endpoint transformations. A successful observation therefore
  retains the same four sparse LP solves as local RTS.
- **Defining source:** One-sided convex-technology formulation and local/global
  relations in [Podinovski
  (2017)](https://doi.org/10.1016/j.ejor.2016.09.029); endpoint calculation
  and numerical examples in [Førsund and Hjalmarsson
  (2004)](https://doi.org/10.1057/palgrave.jors.2601741).
- **Evidence status:** primary-checked and implemented/public for input and
  output normalization at the selected Pareto-efficient VRS projection. No
  projection-invariance, directional-elasticity, deferred-MPSS,
  undesirable-output, or network-stage claim is made.
- **Oracle:** reproduced — the seven efficient one-input/one-output units in
  Førsund and Hjalmarsson give right endpoints
  $(5,15/7,2/3,5/7,3/8,4/9,0)$ and left endpoints
  $(+\infty,15/7,5/3,5/7,3/4,4/9,1/2)$.
  `tests/test_scale_elasticity.py` reproduces every value, the
  maximum-average-productivity kink at unit 3, both boundaries,
  normalization equivalence at the same targets, and unit invariance. This
  does not validate the deferred Banker MPSS prototype.
- **Package recipe:** `scale_elasticity` /
  `analysis.scale_elasticity.local.radial_vrs`. The generic
  `analysis.scale_elasticity` remains a non-executable discovery family, and
  one-sided labels stay fields of this result rather than duplicate public
  methods.
- **Book location:** **Active core placement:** `book/chapters/02-classical/scale-performance-management.md`; derivations and boundary cases remain in package documentation.

#### Directional scale elasticity — source-family and implementation audit

The literature uses *directional scale elasticity* for several related but
non-identical objects. They must not be collapsed behind one direction
argument:

- [Zelenyuk
  (2013)](https://doi.org/10.1016/j.ejor.2013.01.012) defines scale
  elasticity through a directional-distance representation of technology. If
  $D_{\rightarrow}(x,y;d_x,d_y)$ is the directional distance function, the
  elasticity follows the radial boundary path
  $D_{\rightarrow}(\lambda x,\theta y;d_x,d_y)=0$. At a differentiable
  efficient point it is
  $$
  -\frac{\nabla_xD_{\rightarrow}(x,y;d_x,d_y)^\top x}
         {\nabla_yD_{\rightarrow}(x,y;d_x,d_y)^\top y}.
  $$
  Thus $d_x,d_y$ select the distance representation or an inefficient
  unit's route to the frontier; the local scale experiment still changes all
  observed inputs and outputs radially through $\lambda x,\theta y$.
  Equivalence with the input-distance, output-distance, and profit-dual
  elasticities requires the paper's efficient-point, differentiability, and
  nonzero-gradient conditions. This is not an automatic alias of either a DDF
  efficiency score or the non-radial relative-change experiment below.
- [Balk, Färe, and Karagiannis
  (2015)](https://doi.org/10.1007/s11123-014-0399-6) use directional
  derivatives to permit changes in arbitrary input-output directions for a
  chosen functional representation, including directions adapted to weak
  disposability. Additive or translation directions count physical units of
  a reference vector and require their own unit and normalization contract;
  radial, hyperbolic, and translation elasticities are specializations, not
  interchangeable names. The family boundary is primary-checked, but a
  complete nonsmooth DEA programme and a numerical oracle for each
  specialization have not been frozen here. These leaves remain **under
  audit**.
- [Ren et al.
  (2021)](https://doi.org/10.1051/ro/2021131) instead use dimensionless
  component-specific rates. Their input direction $\omega$ says how the
  *composition of marginal resource growth* is distributed, while their
  output direction $\delta$ states the declared *composition of marginal
  service growth*. Such a direction represents management's priorities only
  when those priorities were actually elicited or formally adopted;
  otherwise it is an analyst-defined scenario. This source supplies a
  complete VRS programme, two-sided semantics, public data, and a published
  numerical table. It is the source-qualified leaf implemented in the current
  release; the other source families above remain deferred until their own
  equations and validation paths can be closed.

##### Ren et al. (2021) relative-VRS profile of `analysis.scale_elasticity.directional`

- **Economic question:** At a selected best-practice operating plan, under a
  declared scenario in which different resources expand or contract at
  specified relative rates, what is the largest marginal change in a
  specified mix of services that the benchmark technology can support? Do the
  answers differ for a scale-up and a scale-down decision, and whose
  priorities—if anyone's—does the declared scenario represent?
- **Technology / estimator / inference:** Convex VRS DEA with ordinary free
  disposal, evaluated at a strongly Pareto-efficient observed unit or a named
  strongly efficient projection. It is a deterministic local frontier
  diagnostic and adds no sampling inference. An input- or output-oriented
  radial model may select the projection of an inefficient unit, but that
  preprocessing choice is not the “orientation” of the directional
  elasticity itself.
- **Measure:** For a fixed efficient target $(\widehat x_o,\widehat y_o)$, nonnegative
  relative-rate vectors $\omega\in\mathbb R_+^m$ and
  $\delta\in\mathbb R_+^s$, and componentwise multiplication $\odot$,
  define
  $$
  \begin{aligned}
  x(t)&=(\mathbf 1+t\omega)\odot \widehat x_o,\\
  y(\beta)&=(\mathbf 1+\beta\delta)\odot \widehat y_o,\\
  \beta(t)&=\max\{\beta:(x(t),y(\beta))\in T_{\mathrm{VRS}}\}.
  \end{aligned}
  $$
  The source normalization
  $\sum_i\omega_i=m$ and $\sum_r\delta_r=s$ makes one unit of $t$
  and one unit of $\beta$ one average percentage change. The right and left
  elasticities are
  $\epsilon^+=\beta'_+(0)$ for marginal resource expansion and
  $\epsilon^-=\beta'_-(0)$ for marginal resource contraction. Convex
  piecewise-linear DEA gives $\epsilon^+\leq\epsilon^-$; equality is a
  locally unique response, while a strict interval is economically meaningful
  asymmetry at a frontier kink and must not be averaged away.
- **RTS:** Compare each side separately with one. Values above, equal to, or
  below one indicate increasing, constant, or decreasing directional returns
  for that specific resource/service priority and side. If
  $\epsilon^+<1<\epsilon^-$, scaling up has a less-than-proportional service
  response while scaling down entails a more-than-proportional service loss.
  The native result is that pair of side-specific findings, not a synthetic
  “constant directional RTS” label. VRS remains the maintained technology;
  directional RTS is an output of the analysis, not an RTS input setting.
- **Data / time:** Cross-sectional input and desirable-output quantities,
  with reference membership and projection policy fixed before the local
  experiment. The first executable contract should require strictly positive
  target coordinates, nonnegative mean-one directions of the correct lengths,
  and at least one active component on each side. Zero target coordinates,
  signed directions, undesirable outputs, and panel reference policies need
  separate contracts rather than silent continuation of the relative-change
  formula.
- **Native score:** `scale_elasticity_right`,
  `scale_elasticity_left`, their separate directional-RTS labels, the
  mean-one input and output relative directions, the efficient target and its
  projection provenance, endpoint solver/uniqueness status, support weights,
  reference membership, and explicit `scale_up` / `scale_down` semantics. A
  single elasticity, a single categorical label, or an unrecorded direction
  is incomplete.
- **Exact aliases:** With
  $\omega=\mathbf 1_m$, $\delta=\mathbf 1_s$, the same VRS technology,
  and the same efficient target, this leaf reduces exactly to
  `analysis.scale_elasticity.local.radial_vrs`. Under the output
  normalization $u^\top y^*=1$ and DEAPack's support convention
  $v^\top x-u^\top y+u_0\geq0$, the directional endpoint objectives become
  $\min v^\top x^*=1-\max u_0$ and
  $\max v^\top x^*=1-\min u_0$. This radial specialization is also the only
  case in which the current Banker--Thrall intercept interval directly
  supplies these endpoints. With non-radial directions the support
  normalization and objective change, so neither a radial local-RTS label nor
  one arbitrary intercept identifies the directional response. No equivalence
  is claimed when directions, target, reference set, disposability, or
  normalization differ.
- **Distinct variants:** Zelenyuk's DDF-representation elasticity; the
  absolute level/translation and other functional-representation directions
  of Balk--Färe--Karagiannis; partial or mixed elasticities; weak-disposability
  and undesirable-output responses; network stage or system responses;
  non-convex directional increments/decrements; and global directionally
  optimal scale. In particular, a DDF improvement direction is not a synonym
  for Ren et al.'s relative percentage-change scenario. Radial
  scale efficiency is a global CRS/VRS efficiency-score ratio and may be
  reported for an interior observation; the deferred MPSS profile concerns a
  global search for maximum average productivity along a declared fixed mix.
  Neither is a local
  directional derivative or an alias of this leaf.
- **Domain:** The point assessed must be strongly efficient for the declared
  VRS technology. If an inefficient DMU has multiple strong-efficient
  projections, the implementation must retain all admissible results or name
  the selected projection and must not claim projection invariance. Direction
  normalization is part of the estimand: arbitrary rescaling of $\omega$ or
  $\delta$ changes the parameterization and makes comparison with the
  threshold one invalid unless the source's average-rate correction is
  applied.
- **Failures:** Measuring at an observed interior activity; confusing
  catch-up with scale response; passing directions in physical units to this
  relative-rate model; accepting negative directions under the source ID;
  silently normalizing a user's economic scenario; suppressing alternate
  supporting hyperplanes; replacing one-sided values by a finite-difference
  calculation at an arbitrary step; treating a zero coordinate as capable of
  positive percentage growth; and interpreting directional IRS/DRS as an
  unconditional expansion/contraction recommendation. Equality to one is a
  local directional result and neither validates the deferred MPSS
  reconstruction nor supplies a CRS/VRS scale-efficiency ratio.
- **Solver form:** At a fixed strongly efficient target, solve two sparse
  multiplier LPs:
  $$
  \underset{v,u,u_0}{\operatorname{min/max}}\;
  v^\top(\omega\odot x^*)
  $$
  subject to
  $v^\top x^*-u^\top y^*+u_0=0$,
  $v^\top x_j-u^\top y_j+u_0\geq0$ for every reference unit,
  $u^\top(\delta\odot y^*)=1$, $u,v\geq0$, and $u_0$ free.
  The minimum is $\epsilon^+$ and the maximum is $\epsilon^-$.
  Target fitting/Pareto completion is a separate composed phase. The
  implementation should extend the existing support-endpoint kernel and share
  its selected target, rather than run a perturbation grid or duplicate
  projection work.
- **Defining source:** Definitions (2.6), (2.11)--(2.13), Theorem 3.1, and
  programs (3.7)--(3.8) in [Ren et al.
  (2021)](https://doi.org/10.1051/ro/2021131). The non-alias boundaries are
  checked against [Zelenyuk
  (2013)](https://doi.org/10.1016/j.ejor.2013.01.012) and [Balk, Färe, and
  Karagiannis
  (2015)](https://doi.org/10.1007/s11123-014-0399-6).
- **Evidence status:** primary-checked and implemented/public for the Ren et
  al. relative-rate VRS leaf. Zelenyuk's smooth representation/duality result
  and the broader Balk--Färe--Karagiannis specializations remain deferred for
  source-specific nonsmooth programs, normalization, domains, and numerical
  evidence.
- **Oracle:** reproduced — Table 1 of Ren et al. publishes the complete
  two-input, three-output data for 16 research institutes. DMU 2 is strongly
  efficient and its input-oriented projection is itself:
  $x^*=(442,253.1420)$ and
  $y^*=(295.7381,112,37)$. With
  $\omega=(1,1)$, Table 4 reports
  $(\epsilon^+,\epsilon^-)=(1.41,1.46)$ for
  $\delta=(0.75,0.75,1.50)$,
  $(1.23,1.25)$ for $\delta=(1,1,1)$, and
  $(1.09,1.11)$ for $\delta=(1.25,1.25,0.50)$.
  The bundled source-qualified dataset transcribes all 16 reference rows, and
  `tests/test_directional_scale_elasticity.py` reproduces all three Table 4
  scenarios after the source's two-decimal display rounding while retaining
  unrounded solver values.
- **Package recipe:**
  `analysis.scale_elasticity.directional.relative_vrs.ren_etal_2021`,
  exposed as `relative_directional_scale_elasticity`, with explicit
  `input_relative_direction`, `output_relative_direction`,
  validated mean-one normalization, and an explicit projection policy. The
  generic `analysis.scale_elasticity` record remains a discovery family; no
  generic `direction=` switch silently chooses among the source lineages
  above.
- **Book location:** **Documentation/source review only.** Directional scale
  elasticity has no independent placement in the current handbook.

### `analysis.capacity.physical.fare_grosskopf_kokkelenberg_1989` — deferred source audit

This identifier is retained only for a non-public, review-supported prototype.
The defining full text has not been obtained for equation freezing, so every
programme and field described below is provisional and no current package
recipe is implied.

- **Economic question:** With the existing plant and other quasi-fixed
  resources in place, how much output could the organization produce in the
  short run if variable resources were no longer the binding constraint, and
  how much observed shortfall is ordinary technical inefficiency rather than
  unused physical capacity?
- **Technology / estimator / inference:** A later-literature reconstruction
  associated with Färe--Grosskopf--Kokkelenberg, holding quasi-fixed inputs at
  observed levels while variable inputs adjust. Attribution of the exact
  estimator and variable-input constraints awaits the defining-source audit;
  no inference is attached.
- **Measure:** Candidate capacity output, observed capacity utilization, and
  a technically adjusted component obtained from matched output-distance
  tasks. These are draft prototype semantics, not verified source-native
  fields.
- **RTS:** The prototype uses CRS. Whether this is the complete
  defining-source domain and how variable inputs are treated must be frozen
  before promotion; VRS remains a distinct, unsupported variant.
- **Data / time:** Outputs and inputs partitioned ex ante into quasi-fixed and
  variable blocks for a stated operating horizon; plant availability and
  downtime conventions must be comparable.
- **Native score:** A future source-qualified result would need
  capacity-output expansion and capacity-utilization components sufficient to
  separate technical inefficiency from capacity underuse. No such public
  score contract exists now.
- **Exact aliases:** None with an ordinary output-oriented efficiency score
  unless the quasi-fixed/variable partition and all capacity constraints make
  the two programs identical.
- **Distinct variants:** Input-utilization measures, economic/dual capacity,
  ray versus product-specific multiproduct capacity, dynamic investment
  capacity, congestion, and the separately deferred MPSS profile.
- **Domain:** Quasi-fixed factors must genuinely be unavailable for adjustment
  over the chosen horizon, while the treatment of variable factors must
  describe a physically credible maximum-output exercise.
- **Failures:** Labeling current technical inefficiency as idle plant,
  classifying every input as fixed, allowing an implausible product mix,
  ignoring maintenance or regulatory limits, and comparing utilization ratios
  built from different output directions.
- **Solver form:** The internal prototype uses matched output-distance LPs
  with and without reconstructed variable-input restrictions; this solver
  shape is not yet attributed as the defining paper's exact programme.
- **Defining source:** [Färe, Grosskopf, and Kokkelenberg
  1989](https://doi.org/10.2307/2526781).
- **Evidence status:** `deferred_to_next_version`. The review-supported CRS,
  observed-output-mix implementation is retained only as a non-public
  prototype. Analytical identities, unit invariance, partition failures, and
  component-failure tests show internal consistency but cannot replace an
  equation-frozen defining source.
- **Oracle:** candidate — no published numerical output table from the
  defining article has been independently reproduced; the internal property
  fixture is not a source-level oracle.
- **Package recipe:** None. The candidate identifier remains an audit locator,
  not a catalog entry or public import; the generic `analysis.capacity` family
  also remains non-executable.
- **Book location:** **Evidence-deferred candidate.** Physical capacity has no
  current handbook placement until its source and oracle gates close.

### `analysis.capacity.economic.segerson_squires_1990`

- **Economic question:** Is installed capacity economically underused after
  accounting for output prices, variable-input costs, product mix, and the
  shadow value of quasi-fixed assets, rather than merely asking for the
  largest physically attainable output?
- **Technology / estimator / inference:** Segerson--Squires'
  source-qualified multiproduct economic-capacity framework composed with a
  declared production/cost estimator; the dual and restricted primal
  constructions remain separate; no automatic sampling inference.
- **Measure:** Source-defined dual capacity utilization based on shadow and
  observed quasi-fixed-factor costs, or one of the paper's explicitly
  restricted primal multiproduct capacity measures.
- **RTS:** Inherited from the production representation used to construct the
  economic capacity problem and reported with the homothetic/separability
  conditions required by any primal scalarization.
- **Data / time:** Quantities, output prices, variable-input prices or costs,
  quasi-fixed assets and their shadow/market cost information, all aligned to
  one short-run decision horizon.
- **Native score:** The selected source-native economic-capacity utilization
  ratio plus optimal product mix, shadow values, and the primal/dual branch;
  no generic “capacity percentage” is sufficient.
- **Exact aliases:** None between the scalar dual measure and the paper's
  ray-based or product-specific primal measures except under the source's
  stated regularity and separability conditions.
- **Distinct variants:** Physical engineering capacity, revenue-maximizing
  capacity, minimum-short-run-average-cost capacity, profit efficiency,
  dynamic investment, and the separately deferred physical-capacity and MPSS
  profiles.
- **Domain:** Price and cost vectors must represent the organization's actual
  economic decision, and multiproduct aggregation requires the selected
  duality or separability assumptions rather than an arbitrary output sum.
- **Failures:** Calling maximum physical output “economic capacity,” unstable
  or nonunique shadow prices, unsupported multiproduct scalarization, mixing
  long-run and short-run costs, and attributing demand-constrained output
  entirely to managerial inefficiency.
- **Solver form:** A source-qualified cost, revenue, or profit optimization
  composition and, for dual measures, supporting-price/shadow-value recovery;
  the exact branch determines LP versus other backend needs.
- **Defining source:** [Segerson and Squires
  1990](https://doi.org/10.1016/0304-4076(90)90063-Y).
- **Evidence status:** primary-checked at the source-family level;
  registry-provisional/planned, with executable primal and dual leaves still
  requiring separate equation audits.
- **Oracle:** candidate — the defining paper contains an application, but no
  numerical example has been reproduced in automated repository tests.
- **Package recipe:** Non-executable discovery record
  `analysis.capacity.economic.segerson_squires_1990`; planned executable
  leaves must distinguish `.dual_shadow_cost`, `.primal_ray`, and
  `.primal_product_specific` where supported.
- **Book location:** **Evidence-deferred candidate.** Economic capacity has no
  current handbook placement until its defining formulation and oracle gates close.

### `analysis.mpss.banker_1984` — deferred most-productive-scale-size audit

This identifier is retained only for a non-public prototype. The defining
Banker (1984) full text has not been obtained for equation freezing, so the
technical profile below is a later-literature reconstruction and remains
provisional.

- **Economic question:** Holding one organization's observed resource and
  service proportions fixed, which operating-size interval achieves the
  highest technically attainable average productivity? This is a long-run
  technical benchmark, not a resize instruction.
- **Technology / estimator / inference:** The prototype uses convex VRS
  envelopment with ordinary free disposal, represented through a CRS scale
  envelope for a Charnes--Cooper ratio normalization. The defining-source
  audit must confirm the exact technology, programme, and domain; no sampling
  inference is attached.
- **Measure:** In the provisional reconstruction, for feasible proportional plans
  $(\alpha x_o,\beta y_o)$, maximize
  $\rho_o^{MPSS}=\beta/\alpha$. At the fixed optimum, retain the minimum and
  maximum admissible CRS intensity sums. Their reciprocals reconstruct the
  largest and smallest candidate input/output scale factors and therefore a
  global productive-size interval for the observed mix. This is not yet a
  source-frozen public measure.
- **RTS:** In the prototype, VRS defines the normalized convex reference
  activity, while the CRS
  output normalization linearizes the ratio. It is an internal computation,
  not a public orientation setting. A local IRS/CRS/DRS label concerns a
  declared efficient point and is neither an input nor a dependency of this
  global MPSS search.
- **Data / time:** Nonnegative cross-sectional or panel input/output
  quantities with a strictly positive aggregate input and output for every
  evaluated observation. The observed input and output proportions, reference
  membership, and panel reference policy remain explicit.
- **Native score:** A future result contract would need the
  maximum-productivity ratio, reciprocal efficiency display, current scale
  position, complete endpoint interval, solver statuses, mix-preserving plan,
  and reference weights. Existing internal field names are prototype details,
  not public or source-native semantics.
- **Exact aliases:** Conceptually none with radial scale efficiency, local
  RTS, capacity utilization, scale elasticity, or minimum efficient scale.
  There is no current public `mpss` or `most_productive_scale_size` alias.
- **Distinct variants:** Mix-specific versus global MPSS, non-radial MPSS,
  cost/revenue-optimal size, FDH scale-size analysis, network MPSS, and
  undesirable-output, stochastic, and fuzzy extensions.
- **Domain:** The observed mix must be economically meaningful and supported
  by the declared comparison population. Multiple maximum-productivity sizes
  are a result to report as an interval, not an optimization nuisance to
  suppress. A custom reference that excludes the evaluated observation can
  provide an external fixed-mix benchmark but cannot establish that the
  observed plan belongs to the comparison technology.
- **Failures:** Reporting an MPSS number without its mix, treating VRS
  efficiency or the CRS/VRS radial ratio as MPSS, using a selected VRS
  projection in place of the observed mix, interpreting idle short-run plant
  as wrong long-run scale, and silently selecting one of several productive
  sizes.
- **Solver form:** The internal reconstruction uses three sparse LPs per
  resolved observation over the same comparison population: one
  output-normalized CRS ratio task followed by minimum- and
  maximum-intensity-sum tasks. This useful implementation hypothesis is not
  yet attributed as Banker's exact programme.
- **Defining source:** [Banker
  (1984)](https://doi.org/10.1016/0377-2217(84)90006-7); explicit productive-
  scale target treatment in [Zhu
  (2000)](https://doi.org/10.1057/palgrave.jors.2600893).
- **Evidence status:** `deferred_to_next_version`. The nonnegative
  fixed-observed-mix implementation is retained only as a non-public
  prototype. Its equation shape, three-LP budget, invariance, normalization,
  interval, and failure checks establish internal properties, not defining
  Banker (1984) provenance.
- **Oracle:** candidate — the A--E exact fixture is a derived synthetic check,
  not a numerical table transcribed from the defining article. It therefore
  cannot promote the method.
- **Package recipe:** None. `analysis.mpss.banker_1984` is an audit locator,
  not a public catalog entry or import; the generic family remains
  non-executable.
- **Book location:** **Evidence-deferred candidate.** MPSS has no current
  handbook placement until its source and oracle gates close.

### `analysis.congestion.fgl_1985` — FGL disposability account

- **Economic question:** Are excessive inputs restricting attainable output
  under a production account in which freely reducing all inputs is not
  assumed?
- **Technology / estimator / inference:** Source-qualified strong-versus-weak
  input-disposability technologies; full DEA estimator; no inference in the
  base operator.
- **Measure:** Difference/ratio implied by the Färe--Grosskopf--Lovell
  comparison of maintained input-disposability technologies.
- **RTS:** Must match the defining recipe and comparison.
- **Data / time:** Cross-sectional input/output quantities; any inputs held
  fixed under the law-of-variable-proportions interpretation must be declared.
- **Native score:** Source-native congestion component and supporting
  efficiency quantities, not a generic slack total.
- **Exact aliases:** None with Cooper-line slack congestion except under
  explicitly proven restrictive conditions.
- **Distinct variants:** Cooper additive/slack methods, Tone--Sahoo
  scale-economy account, directional congestion, undesirable-output
  congestion, and network congestion.
- **Domain:** The weak input-disposability technology is substantive and
  cannot be inferred from an ordinary radial model after fitting.
- **Failures:** Confusing ordinary input slack with congestion, comparing
  unmatched technologies, multiple projections, and claiming a congesting
  input without a source-allocation rule.
- **Solver form:** Multiple LPs comparing source-qualified technologies.
- **Defining source:** Production-theory treatment in [Färe, Grosskopf, and
  Lovell 1985/1994](https://doi.org/10.1007/978-94-015-7721-2); distinctions
  surveyed in [Ren et al.
  2021](https://doi.org/10.1016/j.jmse.2021.05.003).
- **Evidence status:** `source_not_frozen` and
  `deferred_to_next_version`. Primary preview pages establish the component
  identities and economic distinction, but the complete weak-disposability
  programme is truncated. See
  `source_protocols/fare_grosskopf_lovell_congestion.md`.
- **Oracle:** not located — the preview exposes only partial result values,
  not the complete source data and programme required for an independent
  reproduction.
- **Package recipe:** None. `analysis.congestion.fgl_1985` is a non-public
  audit locator, not a registry record or import.
- **Book location:** **Conceptual boundary only inside the scale chapter.**
  The FGL formulation receives no named-model section, executable case, or
  independent handbook placement in the current version.

### Cooper-line additive/slack congestion

- **Economic question:** Which particular excessive inputs are associated with
  lost output, and how much of total shortfall is congestion rather than
  ordinary technical/mix inefficiency?
- **Technology / estimator / inference:** Cooper-line source-qualified
  additive technology and projection rules; full DEA estimator; no inference
  in the base operator.
- **Measure:** Slack-based detection, factor attribution, congestion amount,
  and total/technical/congestion decomposition defined by the selected paper.
- **RTS:** Source specific and explicit.
- **Data / time:** Cross-sectional quantities; positive-input assumptions and
  target-selection rules must be recorded.
- **Native score:** Source specific. The 2000 route has its own scalar and
  decomposition account. For the 2002 one-model candidate, the currently
  checked evidence supports physical input-level congestion amounts and an
  existence diagnosis, not a universal scalar index.
- **Exact aliases:** The unified additive and one-model formulations are not
  assumed identical to FGL. Cooper, Seiford, and Zhu establish only
  conditional relationships.
- **Distinct variants:** The 2000 unified additive formulation; the
  Cooper--Deng--Huang--Li one-model formulation; later negative-data and
  multiple-projection corrections.
- **Domain:** Depends on positivity, law-of-variable-proportions, and unique or
  controlled projection assumptions.
- **Failures:** Multiple efficient projections yielding different congestion
  diagnoses, negative data, nonunique source allocation, and interpreting
  every positive input slack as congestion.
- **Solver form:** Additive LP or the exact source's multi-/single-model LP
  sequence.
- **Defining source:** [Cooper, Seiford, and Zhu
  2000](https://doi.org/10.1016/S0038-0121(99)00010-5);
  one-model lineage [Cooper et al.
  2002](https://doi.org/10.1016/S0038-0121(02)00008-3);
  review [Ren et al.
  2021](https://doi.org/10.1016/j.jmse.2021.05.003).
- **Evidence status:** mixed and source-gated. The accessible 2000 primary
  article has been checked at full-text level. For Cooper--Deng--Huang--Li
  (2002), only authoritative metadata, the abstract, and the exposed
  definition have been checked; a later same-author article corroborates the
  programme but cannot replace the defining pages. The 2002 candidate is
  `source_not_frozen` and `deferred_to_next_version`; see
  `source_protocols/cooper_deng_huang_li_2002_congestion.md`.
- **Oracle:** not located for the 2002 candidate — its defining numerical
  table has not been obtained and independently reproduced. A later example
  can serve only as corroboration, not as the published 2002 oracle.
- **Package recipe:** None for the 2002 route. `analysis.congestion.cooper_slack`
  is a non-executable literature umbrella, and
  `analysis.congestion.cooper_deng_huang_li_2002` is a non-public audit
  locator. Later projection policies require their own source qualification.
- **Book location:** **Congestion concept inside the scale/slack discussion
  only.** The 2002 formulation receives no independent chapter, model-family
  section, or executable case.

## 6. Decisions fixed by this review

1. Historical names are retained for discovery, but executable duplication is
   prohibited when an exact equivalence has been established on a declared
   domain.
2. `ERG` and standard non-oriented `SBM` use one canonical implementation on
   the strictly positive matched domain. Domain-changing ERG/SBM variants
   remain distinct.
3. Tone's input-, output-, and non-oriented SBM are implemented Level B
   measures over shared technology/reference/compiler machinery. A best
   oriented score certifies only its objective side; the other side's target
   is solver-selected. Table 2 validates only the non-oriented CRS leaf, while
   oriented published numerical oracles remain not located.
4. `CCR` and `BCC` fix only returns to scale. The public `CCRInput`,
   `CCROutput`, `BCCInput`, and `BCCOutput` presets additionally fix
   orientation, native score, and DEAPack's row-scaled lexicographic
   target/slack policy; that phase-two policy is not attributed as a uniquely
   selected historical target.
5. Cost, revenue, profit, Nerlovian, and profitability measures are economic
   objectives or compositions over a technology; supplied prices are not DEA
   multiplier weights.
6. Congestion is always source qualified. FGL disposability and Cooper-line
   slack accounts are not generic aliases, even when they share LP machinery.
7. Pareto--Koopmans status is a result/target-completion policy over a declared
   technology. Its reusable public identity currently covers only compatible
   ordinary all-discretionary convex radial and desirable-output DDF fits.
   A radial score and a strong-status result are not competing scalar aliases;
   environmental, nondiscretionary, FDH, FCH, and FRH protocol extensions are
   deferred.
8. Physical capacity, economic capacity, MPSS, scale efficiency, and
   congestion answer different operational questions. Physical capacity and
   MPSS currently retain only deferred audit IDs; they are not source-qualified
   public methods.
9. Property tests alone do not close a missing defining-source or independent
   oracle gate. Such reconstructions remain non-public prototypes until the
   complete evidence chain is frozen.
