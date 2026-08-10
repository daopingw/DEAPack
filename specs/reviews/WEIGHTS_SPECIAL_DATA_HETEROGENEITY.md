# Review register: weights, special data, and heterogeneity

## Purpose and classification rule

This review covers three questions that are often mixed together in software:

1. **Whose values should govern the comparison?** This is a valuation or
   preference question.
2. **What may management change, and what information do the observations
   contain?** This is a data-role and control question.
3. **Who genuinely faces comparable opportunities?** This is a reference,
   technology, or frontier-estimator question.

The package must not answer all three with one `restrictions=` argument.
Multiplier restrictions constrain supporting valuations; production trade-offs
change attainable possibilities; non-discretionary variables change target
rights; categorical variables change admissible comparisons; environmental
conditions may change either the comparison population or the estimated
frontier.

Every record uses the same evidence fields. `Technology / estimator /
inference` preserves the technology--estimator--inference triad. `Evidence
status` records primary-source/review support and registry or repository
implementation evidence. `Oracle` is separate and begins with exactly one
controlled status: `not located`, `candidate`, `analytically derived`,
`reproduced`, or `cross-implemented`. The last three mean an automated
independent numerical oracle exists; analytical derivation does not claim a
published-data reproduction.

All families reviewed below are planned unless a record explicitly says
otherwise.

## 1. Which valuations are admissible?

### `valuation.weight_restriction.ar1` — Assurance Region Type I

- **Economic question:** What relative importance bounds between inputs, or
  between outputs, are defensible from policy, prices, expert judgment, or
  prior evidence?
- **Technology / estimator / inference:** The quantity technology and frontier
  estimator remain those of the base DEA model; AR-I restricts admissible
  multiplier valuations; no inference is added.
- **Measure:** Base multiplier/envelopment efficiency under within-side ratio
  bounds such as $L_{ii'}\le v_i/v_{i'}\le U_{ii'}$ or their output-side
  counterparts.
- **RTS:** Inherited from the base model; restrictions involving the VRS
  intercept need a separate source-qualified treatment.
- **Data / time:** Quantities plus bounds with units, provenance, population,
  stakeholder, and validity period.
- **Native score:** The base model's native score, accompanied by binding
  restrictions and feasible valuation ranges.
- **Exact aliases:** Multiplier-ratio inequalities and their exactly derived
  dual cone restrictions are two forms of the same declared AR-I set.
- **Distinct variants:** AR-II cross-side restrictions, absolute multiplier
  bounds, cone-ratio restrictions, virtual-share bounds, production
  trade-offs, and common-weight evaluation.
- **Domain:** Denominators and units must make ratios meaningful; bounds must
  be jointly feasible and scale compatible.
- **Failures:** Inconsistent cycles of ratios, unit dependence, zero-valued
  denominators, inadvertently permitting free/unlimited production, and
  presenting normative bounds as observed prices.
- **Solver form:** Linear program after ratio bounds are written as linear
  homogeneous inequalities; feasibility/consistency audit precedes fitting.
- **Defining source:** Assurance regions in [Thompson et al.
  1990](https://doi.org/10.1016/0304-4076(90)90049-Y); field review in
  [Allen et al.
  1997](https://doi.org/10.1023/A:1018968909638).
- **Evidence status:** `source_not_frozen`,
  `blocked_on_primary_source`, and `deferred_to_next_version`. Accessible
  metadata and review descriptions do not close the source equations or
  establish implementation readiness.
- **Oracle:** not located — no complete primary numerical example has passed
  an independent reproduction audit.
- **Package recipe:** Deferred `valuation.weight_restriction.ar1`; there is no
  current public API or machine method record. Reopen only through
  `source_protocols/assurance_region.md`.
- **Book location:** **Documentation/source review only.** No current handbook placement.

### `valuation.weight_restriction.ar2_cross_side` — Assurance Region Type II

- **Economic question:** What restrictions are defensible between the marginal
  valuation of an input and the marginal valuation of an output?
- **Technology / estimator / inference:** Base technology and estimator are
  unchanged; AR-II links the input and output sides of the multiplier system;
  no inference is added.
- **Measure:** Base efficiency subject to declared cross-side linear
  inequalities.
- **RTS:** Inherited from the base model; normalization and any free intercept
  must be included in the equivalence audit.
- **Data / time:** Quantities plus cross-side bounds whose units and numeraire
  are explicitly recorded.
- **Native score:** Base native score plus binding cross-side constraints and
  valuation diagnostics.
- **Exact aliases:** Only an algebraically identical normalized/dual
  representation with matched units and feasible set.
- **Distinct variants:** AR-I within-side ratios and Wong--Beasley virtual
  shares. AR-II is **not** the Wong--Beasley method.
- **Domain:** Cross-side ratios require a coherent value unit; arbitrary bounds
  on input and output multipliers can be meaningless under unit conversion.
- **Failures:** Silent dependence on the multiplier normalization, infeasible
  cross-side bounds, missing numeraire, and treating the restrictions as
  market prices.
- **Solver form:** Linear multiplier program with a separate feasibility and
  unit-sensitivity audit.
- **Defining source:** Classification and cautions in [Allen et al.
  1997](https://doi.org/10.1023/A:1018968909638), with the Thompson assurance
  region lineage [Thompson et al.
  1990](https://doi.org/10.1016/0304-4076(90)90049-Y).
- **Evidence status:** `source_not_frozen`,
  `blocked_on_primary_source`, and `deferred_to_next_version`. The review
  classification does not substitute for a complete primary equation freeze.
- **Oracle:** not located — no complete primary numerical example has passed
  an independent reproduction audit.
- **Package recipe:** Deferred
  `valuation.weight_restriction.ar2_cross_side`; there is no current public API
  or machine method record. Reopen only through
  `source_protocols/assurance_region.md`.
- **Book location:** **Documentation/source review only.** No current handbook placement.

### `valuation.weight_restriction.cone_ratio.polyhedral_crs.charnes_etal_1990`

- **Economic question:** Which organizations remain favourable when their
  input and output self-appraisal multipliers must belong to separate,
  substantively declared polyhedral valuation cones?
- **Technology / estimator / inference:** Charnes--Cooper--Huang--Sun's
  finite-DMU cone-ratio CCR estimator. The observed comparison population is
  retained, while supporting valuations are restricted to exogenous input and
  output generator cones; the paired envelopment uses the corresponding polar
  dominance order. No statistical inference is added.
- **Measure:** Input-oriented CRS radial cone-ratio score from
  $V=\{A^\top\alpha:\alpha\ge0\}$ and
  $U=\{B^\top\gamma:\gamma\ge0\}$, equivalently ordinary input CCR on
  $X'=AX$ and $Y'=BY$.
- **RTS:** CRS only. There is no convexity equation or free VRS intercept.
- **Data / time:** One finite self-inclusive cross section of nonnegative
  ordinary inputs and desirable outputs, with strictly positive transformed
  observations. The nonnegative sum-form matrices $A,B$ require variable
  units, elicitation source, stakeholder, comparison population, and validity
  period.
- **Native score:** The source radial factor, reconstructed generator
  coefficients and original-coordinate multipliers, peer intensities,
  original peer composites, and transformed cone residuals. Score equality
  and source interior-multiplier efficiency status remain separate.
- **Exact aliases:** The direct finite-generator programme and ordinary input
  CCR fitted to the declared transformed data are exact computational forms
  of this source leaf. $A=I_m,B=I_s$ is an exact ordinary-CCR reduction.
- **Distinct variants:** Thompson AR-I and AR-II, absolute bounds,
  Wong--Beasley virtual shares, production trade-offs, common weights,
  output-oriented/VRS cone-ratio extensions, and automatic expert-DMU
  generator elicitation.
- **Domain:** Generator matrices are finite, dimensionally conformable, and
  nonnegative, with no zero generator or nonpositive transformed observation.
  Unit recoding must transform generator columns inversely; fixed numerical
  generators under new quantity units represent a different valuation cone.
- **Failures:** Infeasible or degenerate cones, rank/interior overclaims,
  unit-blind restrictions, treating implicit valuations as market prices,
  calling cone residuals ordinary componentwise slacks, and deriving
  generators from solver-selected alternate CCR multipliers without a source
  selection rule.
- **Solver form:** One sparse input-oriented CRS LP per focal organization
  after one $X'=AX,Y'=BY$ compilation per reference set, with a separately
  assembled direct-multiplier oracle and primal--dual certificate.
- **Defining sources:** General cone model [Charnes et al.
  (1989)](https://doi.org/10.1080/00207728908910197), finite polyhedral
  operational model [Charnes et al.
  (1990)](https://doi.org/10.1016/0304-4076(90)90048-X), and exact
  representation conditions [Charnes et al.
  (1991)](https://doi.org/10.1080/00207729108910773).
- **Evidence status:** `implemented` and `public` for this finite sum-form
  leaf only; equations, data domain, unit covariance, non-equivalence
  boundaries, dedicated result semantics, machine registry, and automated
  source-only tests are closed.
- **Oracle:** reproduced — the printed Example 2 scores for DMU3 and DMU10
  were independently reproduced as $85/86=0.9884$ and
  $42/43=0.9767$. Direct multiplier and transformed envelopment programmes
  agree over all 17 rows to $9.55\times10^{-15}$ in the source audit and are
  independently automated in the repository. Example 3/Table 2 is explicitly excluded: its printed
  data and matrix disagree with 2 of 17 published scores.
- **Package recipe:** Public `PolyhedralConeRatioDEA` with required typed
  `ConeRestrictionProvenance`, controlled by
  `source_protocols/charnes_cooper_huang_sun_1990_polyhedral_cone_ratio.md`
  and
  `oracles/charnes_cooper_huang_sun_1990_cone_ratio.md`. No generic
  restriction interface or historical-method alias is implied.
- **Book location:** **Documentation/source review only.** Implementation would
  not itself qualify this source leaf for handbook admission.

### `valuation.weight_restriction.virtual_share.wong_beasley`

- **Economic question:** How much of an evaluated unit's total virtual input
  or virtual output may any one factor account for?
- **Technology / estimator / inference:** Base technology and estimator are
  unchanged; the method restricts observation-specific virtual shares; no
  inference is added.
- **Measure:** Base multiplier efficiency subject to lower/upper bounds on
  $v_i x_{io}/\sum_k v_k x_{ko}$ and/or
  $u_r y_{ro}/\sum_s u_s y_{so}$.
- **RTS:** Inherited from the base model; VRS-intercept treatment must follow
  the chosen multiplier formulation.
- **Data / time:** Quantity data plus share bounds, their stakeholder source,
  and the evaluated observation $o$; bounds may be common but the shares are
  observation dependent.
- **Native score:** Base native score plus realized virtual shares for every
  evaluated unit.
- **Exact aliases:** The corresponding cross-multiplied inequalities are exact
  only when their virtual-input/output denominator and normalization conditions
  are valid.
- **Distinct variants:** AR-I, AR-II, Sarrico--Dyson virtual-weight
  restrictions, common weights, and benefit-of-doubt indicator models.
- **Domain:** Total virtual input/output denominator must be valid; zeros and
  omitted factors need an explicit rule.
- **Failures:** Reusing one unit's shares for another, mistaking share bounds
  for multiplier ratios, infeasible lower bounds that sum above one, and
  calling virtual shares observed cost/revenue shares.
- **Solver form:** Observation-indexed linear multiplier LP after valid
  cross-multiplication.
- **Defining source:** [Wong and Beasley
  1990](https://doi.org/10.1057/jors.1990.120); later virtual-weight treatment
  [Sarrico and Dyson
  2004](https://doi.org/10.1016/S0377-2217(03)00402-8).
- **Evidence status:** `source_not_frozen` and
  `deferred_to_next_version`. The publisher abstract and later accounts do
  not replace a page-checked primary programme, zero/denominator policy, or
  complete source example.
- **Oracle:** not located — no complete primary numerical example has passed
  an independent reproduction audit.
- **Package recipe:** Deferred
  `valuation.weight_restriction.virtual_share.wong_beasley`, with
  eventual per-observation diagnostics. It must remain separate from
  `valuation.weight_restriction.ar2_cross_side` and the source-frozen
  polyhedral cone-ratio leaf.
- **Book location:** **Documentation/source review only.** No current handbook placement.

### `evaluation.common_weight.roll_cook_golany_1991`

- **Economic question:** What comparative appraisal results when all
  organizations must be judged by one shared valuation system rather than
  choosing separate favourable self-appraisal multipliers?
- **Technology / estimator / inference:** A shared-valuation evaluation
  protocol, not a new quantity frontier and not statistical inference. The
  exact source objective and comparison rule are not yet frozen.
- **Measure:** Deferred. A common set of weights can require an explicit
  compromise, discrimination, deviation, or goal objective; no generic
  `common=True` score is source qualified.
- **RTS:** Deferred with the source normalization. CRS cannot be inferred
  solely because the underlying multiplier constraints are homogeneous.
- **Data / time:** A declared common comparison population plus shared
  valuation provenance. Time aggregation and panel use require separate
  rules.
- **Native score:** Deferred pending the defining article's common-weight
  objective, normalization, unit policy, ties, and organization-level
  comparison formula.
- **Exact aliases:** None with cone-ratio self-appraisal, AR-I/AR-II,
  cross-efficiency, average DEA multipliers, or equal weights.
- **Distinct variants:** Later compromise, minimax, goal-programming,
  cross-efficiency, benefit-of-the-doubt, and common-weight ranking models.
- **Domain:** Joint feasibility, dimensional consistency, normalization, and
  the substantive legitimacy of one valuation system must all be explicit.
- **Failures:** Calling a convenient average of separate multipliers a common
  optimum, omitting the joint objective or tie policy, and presenting shared
  normative valuations as observed prices.
- **Solver form:** Not frozen. A common-weight model generally couples
  organizations in one appraisal problem and is not one independent CCR LP
  per focal row.
- **Defining source:** [Roll, Cook, and Golany
  (1991)](https://doi.org/10.1080/07408179108963835).
- **Evidence status:** `source_not_frozen`,
  `blocked_on_primary_source`, and `deferred_to_next_version`. The accessible
  primary abstract confirms bounds and examination of a common set of
  weights, but does not expose the full shared programme or numerical example.
- **Oracle:** not located — no source-native shared-weight result has passed
  an independent reproduction audit.
- **Package recipe:** Deferred
  `evaluation.common_weight.roll_cook_golany_1991`; no public API or machine
  method record. It is not implemented through the public cone-ratio leaf.
- **Book location:** **Documentation/source review only.** No chapter is reserved by this source-review gate.

### `composite.benefit_of_doubt.linear.cherchye_etal_2007`

- **Economic question:** How can several achievement indicators be summarized
  when stakeholders agree on the dimensions to assess but do not agree on one
  set of aggregation weights, while still giving each country or organization
  the most favourable admissible weighting?
- **Technology / estimator / inference:** Cherchye--Moesen--Rogge--Van
  Puyenbroeck's linear benefit-of-the-doubt (BoD) aggregator. Each entity has
  one common dummy input normalized to one, and its positively oriented
  sub-indicators occupy the output side of DEA multiplier machinery. This is a
  relative composite-indicator estimator, not an estimated production
  technology or sampling-inference procedure.
- **Measure:** For each entity $o$, maximize
  $\sum_r u_{ro}y_{ro}$ subject to
  $\sum_r u_{ro}y_{rj}\leq 1$ for every comparison entity $j$,
  non-negative weights, and any declared weight or sub-indicator-share
  restrictions. The dummy-one normalization fixes the comparison scale; it
  does not represent a resource consumed in production.
- **RTS:** No production returns to scale are estimated. The formal
  dummy-input representation matches the homogeneous CCR multiplier form;
  adding a VRS intercept would change the admissible aggregation rule and
  therefore requires a separate source-qualified BoD variant rather than an
  interchangeable `rts=` option.
- **Data / time:** Positively oriented achievement indicators for a declared
  comparison population and vintage, plus transformations for indicators
  where lower values are preferred and provenance for every expert or policy
  restriction. Longitudinal use requires a separately declared reference and
  chaining policy.
- **Native score:** Entity-specific BoD composite score, favourable weights,
  unit-free virtual contributions and percentage shares, active restrictions,
  peers, ties and ranking. The result contract also retains unrestricted versus
  restricted comparisons and sensitivity results for indicator inclusion,
  comparison-set membership, transformations, and weight/share bounds; no
  bare score vector is sufficient.
- **Exact aliases:** The dummy-input-one DEA multiplier representation and the
  linear BoD composite-indicator program are exact representations of this
  leaf when the normalization, monotonicity, comparison set, and restrictions
  coincide. “DEA efficiency” and “technical efficiency” are not aliases.
- **Distinct variants:** Multiplicative, pessimistic, robust order-$m$,
  conditional, dynamic, and common-weight BoD; principal-component and equal-
  weight composite indicators; production DEA with observed resource inputs;
  AR-I/II and Wong--Beasley restrictions applied to a production model.
- **Domain:** Indicators must express a coherent construct, have the declared
  favourable direction, and admit non-negative aggregation. The comparison
  set and every weight/share restriction must be substantively defensible and
  jointly feasible; unit invariance of the score does not make raw weights
  comparable across measurement units.
- **Failures:** Calling a favourable composite score productive efficiency;
  interpreting endogenous weights as revealed preferences; allowing zero
  weights to erase essential dimensions without disclosure; ranking entities
  without tie and sensitivity policies; applying a lower-is-better indicator
  without a documented transformation; and reporting unit-dependent raw
  weights as importance shares.
- **Solver form:** One observation-indexed linear multiplier LP per entity,
  with a shared compiled constraint matrix where possible, followed by
  deterministic contribution, ranking, tie, and sensitivity reconstruction.
- **Defining source:** [Cherchye, Moesen, Rogge, and Van Puyenbroeck
  (2007)](https://doi.org/10.1007/s11205-006-9029-7).
- **Evidence status:** primary-checked for the linear dummy-one formulation,
  unit invariance, favourable entity-specific weighting, and sub-indicator
  share restrictions; registry-provisional/planned with no repository
  implementation.
- **Oracle:** candidate — the paper reports a Technology Achievement Index
  illustration, but DEAPack has not reproduced its numerical tables in an
  automated test.
- **Package recipe:** Planned
  `composite.benefit_of_doubt.linear.cherchye_etal_2007`; its result schema
  preserves scores, weights, contributions, restrictions, rankings, ties, and
  named sensitivity scenarios under a non-production decision context.
- **Book location:** **Documentation/source review only.** No current handbook placement.

### Production trade-offs and weight-restriction consistency

- **Economic question:** Is a stated relation a value judgment about acceptable
  weights, or a technological claim that one feasible activity can be traded
  for another?
- **Technology / estimator / inference:** Production trade-offs modify the
  technology; multiplier restrictions modify admissible supporting
  valuations; the base estimator remains explicit; no inference is added.
- **Measure:** Any compatible base distance or economic objective evaluated on
  the augmented/restricted technology.
- **RTS:** The trade-off construction and RTS must be jointly closed under the
  exact source conditions.
- **Data / time:** Quantity data plus trade-off vectors or weight bounds, each
  with units, source, scope, and validity period.
- **Native score:** Base native score plus a report of active trade-offs or
  weight bounds and the resulting feasible-set change.
- **Exact aliases:** Dual representations may be exact under documented
  regularity and closure conditions; conceptual duality never licenses
  dropping the technology-versus-valuation distinction.
- **Distinct variants:** AR-I/II, cone-ratio restrictions, absolute bounds,
  linked production trade-offs, and price-based economic models.
- **Domain:** Trade-off vectors must be technologically meaningful and
  dimensionally consistent; multiplier restrictions must pass feasibility,
  unit, and production-implication audits.
- **Failures:** Free or unlimited production implied by inconsistent
  restrictions, unboundedness, infeasibility, and normative constraints
  disguised as empirical technology.
- **Solver form:** Linear/conic DEA program plus a pre-fit closure and
  consistency audit.
- **Defining source:** Production trade-offs [Podinovski
  2004](https://doi.org/10.1057/palgrave.jors.2601794); free-production
  implications [Podinovski and Bouzdine
  2013](https://doi.org/10.1287/opre.1120.1122); consistency conditions
  [Podinovski
  2015](https://doi.org/10.1016/j.ejor.2015.01.037).
- **Evidence status:** primary-checked; registry-provisional/planned.
- **Oracle:** candidate — literature examples have been identified but not
  reproduced in automated repository tests.
- **Package recipe:** Planned `technology.production_tradeoff` and separate
  `diagnostics.weight_restriction_consistency`; do not hide both inside one
  multiplier-bounds object.
- **Book location:** **Documentation/source review only.** No current handbook placement.

## 2. What may management change?

### `static.radial.nondiscretionary.banker_morey_1986`

- **Economic question:** How should an organization be benchmarked when some
  observed resources, obligations, or services affect feasible comparison but
  are not legitimate management targets?
- **Technology / estimator / inference:** Banker--Morey's source-qualified
  radial technology with fixed/non-discretionary components; full DEA
  estimator; no inference in the base recipe.
- **Measure:** Input- or output-radial efficiency applied only to the
  discretionary block while non-discretionary quantities enter the comparison
  constraints according to the defining formulation.
- **RTS:** Explicit; VRS and CRS versions must not be assumed equivalent.
- **Data / time:** Quantity data plus a variable-level managerial-control role
  (`discretionary` or `nondiscretionary`) and its institutional justification.
- **Native score:** Radial score for the adjustable block, with targets
  reported only where adjustment rights exist.
- **Exact aliases:** None with contextual variables, quasi-fixed capital,
  missing data, or simply setting a direction component to zero unless the
  entire feasible set and target contract are proven identical.
- **Distinct variants:** Later non-/semi-discretionary models, short-run cost
  and capacity models, bounded adjustment, and non-controllable undesirable
  factors.
- **Domain:** Every variable's economic role and target right must be declared
  before fitting; a variable can be quantitatively observed yet not
  controllable.
- **Failures:** Issuing unauthorized targets, treating an inherited condition
  as an input management can reduce, misclassifying fixed commitments as
  missing observations, and orientation-specific constraint errors.
- **Solver form:** Linear envelopment program with separate discretionary and
  non-discretionary blocks.
- **Defining source:** [Banker and Morey
  1986, nondiscretionary variables](https://doi.org/10.1287/opre.34.4.513).
- **Evidence status:** `source_not_frozen` and
  `deferred_to_next_version`. The complete primary article was not available
  in the source audit, and a reported issue in the printed CRS formulation
  makes reconstruction from secondary accounts especially unsafe.
- **Oracle:** not located — neither a complete primary numerical example nor
  an independently frozen exact oracle has passed the release gate.
- **Package recipe:** Deferred
  `static.radial.nondiscretionary.banker_morey_1986`, eventually composed from
  the semantic role `data.nondiscretionary`. There is no current public API
  or machine method record; the controlling evidence record is
  `source_protocols/banker_morey_1986_nondiscretionary.md`.
- **Book location:** **Documentation/source review only.** No current handbook placement.

### Semi-discretionary and bounded-control quantities

- **Economic question:** What improvement is feasible when a quantity can
  change, but only within operational, contractual, or regulatory bounds?
- **Technology / estimator / inference:** Source-qualified target-bounded
  technology; full estimator unless otherwise declared; no automatic
  inference.
- **Measure:** Compatible radial, directional, or slack measure over the
  bounded target set.
- **RTS:** Explicit.
- **Data / time:** Quantity data plus lower/upper target bounds, adjustment
  horizon, owner, and provenance.
- **Native score:** Base score plus bound activity and the feasible target
  interval.
- **Exact aliases:** None with fully non-discretionary variables, interval
  measurement uncertainty, or BAM normalization bounds.
- **Distinct variants:** Quasi-fixed-input short-run models, integer targets,
  capacity models, and goal/priority target selection.
- **Domain:** Bounds must be physically and temporally compatible with the
  evaluation horizon.
- **Failures:** Using measurement-error intervals as operating bounds, rounding
  continuous targets after fitting, or reporting a theoretically efficient
  target that violates the bounds.
- **Solver form:** LP or MILP depending on whether quantities are continuous or
  indivisible.
- **Defining source:** No single canonical formulation is assigned here;
  each executable leaf requires a source audit. The Banker--Morey
  nondiscretionary paper is not used as a catch-all citation.
- **Evidence status:** registry-provisional; exact primary-source executable
  leaves have not yet been selected.
- **Oracle:** not located — no certified numerical example has been selected.
- **Package recipe:** Semantic records `data.semi_discretionary` and
  `data.operational_bounds`, followed by source-qualified executable leaves.
- **Book location:** **Documentation/source review only.** No current handbook placement.

## 3. What kind of comparison is meaningful for special data?

**Current source-neutral observation-specific peer-eligibility policy.**

- **Economic question:** Which candidate organizations did the study admit as
  potentially credible comparators for each evaluated organization before any
  score or fitted peer was observed?
- **Technology / estimator / inference:** This is a reusable comparison-right
  policy over the authorized classical black-box estimators, not a new
  technology, performance measure, categorical model, or inferential
  procedure.
- **Composition:** If $I_o$ is the population admitted by the base
  `ReferenceSpec` and $P_o$ is the declared candidate population, every
  authorized programme uses exactly $I_o\cap P_o$. The policy can remove a
  base candidate but cannot add one.
- **Current package boundary:** Public `PeerEligibility` and
  `PeerEligibilityProvenance` are accepted by the ordinary radial family and
  four fixed radial recipes, Additive/Weighted Additive, RAM, ordinary input-,
  output-, and non-oriented SBM aliases, and ordinary DDF. Undesirable-output
  SBM, environmental DDFs, BAM, range-directional and generalized measures,
  and the economic, productivity, evaluation, network, panel-specific, and
  dynamic families remain outside this audited surface.
- **RAM normalization boundary:** A restricted RAM fit keeps one global
  full-data range population frozen before eligibility is applied. Its
  effective VRS comparison population may vary by observation, and the fit is
  labelled `deapack_ram_extension` rather than the exact full self-inclusive
  Cooper--Park--Pastor source profile.
- **Native result:** Positive-intensity peers are selected inside the effective
  population and remain fitted outputs. Result provenance distinguishes base
  and effective population sizes and states
  `categorical_interpretation: not_claimed`.
- **Non-equivalence:** The policy does not inspect category columns, infer
  nominal or ordered semantics, use `DEAData.groups`, fit separate category
  frontiers, or implement either Banker--Morey (1986) formulation.
- **Package recipe:** `reference.peer_eligibility`, composed only with the
  audited classical black-box support surface above. It has no standalone fit
  or public catalog method identity.
- **Book location:** Study-design concept and source-neutral radial example;
  no named model chapter.

### `static.radial.categorical.banker_morey_1986`

- **Readiness boundary:** This identifier is a provisional discovery umbrella,
  not a frozen executable leaf. The full defining article was not obtained,
  so the controllable/uncontrollable split and any nominal/ordered distinction
  remain unresolved.
- **Economic question:** Which organizations are admissible peers when a
  service class, facility type, mission, or other category changes the
  comparison set?
- **Technology / estimator / inference:** Proposed source-qualified
  categorical comparison technology; exact programmes, estimator split, and
  inference boundary are not source-frozen.
- **Measure:** Expected to contain radial performance accounts, but the exact
  peer relation and any distinct categorical-output objective are unverified.
- **RTS:** Technical and scale inefficiency are mentioned in the publisher
  abstract; their equations and conditions are not frozen.
- **Data / time:** OR-Library's `dea3` is a raw 69-by-6 unlabelled numeric file.
  Its roles, units, category coding, and source-table alignment are unknown.
- **Native score:** Not frozen. Any score, categorical target, or admissible
  population reported by the source must be transcribed before implementation.
- **Exact aliases:** None with running separate DEA models by category,
  one-hot encoding categories as ordinary quantities, or conditioning a
  frontier nonparametrically on continuous environmental variables.
- **Distinct variants:** Nominal versus ordered categories, hierarchical
  categories, group-specific frontiers, metafrontiers, and conditional
  frontiers.
- **Domain:** Not source-frozen. Categories would still require an economically
  credible meaning, but nominal, ordered, controllable, and uncontrollable
  domains must not be inferred from the abstract.
- **Failures:** Source behaviour for ties, unknown labels, empty or singleton
  populations, infeasibility, and non-unique solutions is unknown.
- **Solver form:** Not source-frozen; do not infer a continuous LP for every
  formulation from the abstract.
- **Defining source:** [Banker and Morey
  1986, categorical variables](https://doi.org/10.1287/mnsc.32.12.1613).
- **Evidence status:** `primary_metadata_and_abstract_located_full_text_not_obtained`;
  `deferred_to_next_version`; no repository implementation or machine record.
- **Oracle:** not located. `dea3` lacks headings, category codes, variable
  roles, and expected results and therefore is not independently executable.
- **Package recipe:** Deferred provisional identifier
  `static.radial.categorical.banker_morey_1986`; final leaf split is unresolved.
  The controlling evidence record is
  `source_protocols/banker_morey_1986_categorical.md`. The implemented
  source-neutral radial policy above does not implement this method.
- **Book location:** **Documentation/source review only.** No current handbook placement.

### Ordinal, ratio, integer, flexible-role, negative, and missing data

- **Economic question:** What can the evidence support when a recorded field
  is not an unrestricted non-negative continuous quantity?
- **Technology / estimator / inference:** Data semantics select a compatible
  technology/compiler; the estimator and inference remain separate choices.
- **Measure:** Only a measure whose invariance, denominator, and target
  properties are compatible with the declared data type.
- **RTS:** Explicit; ratio and integer technologies may require alternative
  convexity/replication axioms.
- **Data / time:** Each field declares economic role, numerical information,
  controllability, missingness mechanism/policy, units, and time coverage.
- **Native score:** Base native score plus data-treatment provenance and any
  interval, integrality, or role-selection result.
- **Exact aliases:** None among ordinal, categorical, ratio, integer, flexible
  input/output role, negative, zero, missing, interval, and fuzzy data.
- **Distinct variants:** Source-qualified ordinal DEA, ratio-variable
  technologies, integer DEA, flexible measures, translation-invariant signed
  data models including the original RDM, pairwise-deletion/reference
  policies, IDEA, and fuzzy DEA.
- **Domain:** Defined by the exact leaf. The original RDM permits finite signed
  inputs and finite signed desirable outputs, fixes VRS, requires the focal
  unit in the exact population used for both extrema and technology, and
  fails when every active focal-to-ideal range is zero. A negative desirable
  output remains a signed desirable output; it does not become an undesirable
  output.
- **Failures:** Zero filling missing observations, rounding continuous DEA
  targets, treating ranks as cardinal values, applying log/ratio models to
  nonpositive values, and selecting a favorable input/output role without
  reporting it.
- **Solver form:** LP, MILP, or nonlinear/robust program depending on the exact
  semantic combination.
- **Defining source:** Broad source map in [Zhu and Cook
  2007](https://doi.org/10.1007/978-0-387-71607-7). The implemented signed-data
  leaf is [Portela, Thanassoulis, and Simpson
  (2004)](https://doi.org/10.1057/palgrave.jors.2601768). Exact executable
  leaves require their own primary sources; the handbook is not evidence of
  equivalence.
- **Evidence status:** review-supported at the generic-group level. The
  original RDM is primary-checked and implemented/public; other exact data
  types remain registry-provisional until their own equations and failure
  domains are frozen.
- **Oracle:** cross-implemented — the original RDM's exact signed rational
  fixture is solved both through the package and an independent equation
  compiler, with an additional transcription check against the defining
  paper's published target. This does not validate the other heterogeneous
  leaves in the card.
- **Package recipe:** `RangeDirectionalDEA` / `RDM` for
  `static.range_directional.portela_thanassoulis_simpson_2004`; semantic IDs
  under `data.*`; no generic `special_data=True`. Other executable recipes are
  promoted one source-qualified combination at a time.
- **Book location:** **Documentation/source review only.** Signed-data and other
  special-data formulations have no independent placement in the current handbook.

## 4. How should leaders be ranked and operational targets selected?

### `evaluation.super.ap_radial` — deferred Andersen--Petersen candidate

- **Economic question:** Which frontier organizations remain most distinctive
  when each is compared with what its peers can attain without using that
  organization as its own benchmark?
- **Technology / estimator / inference:** The internal reconstruction uses a
  radial DEA technology with the evaluated row excluded from its otherwise
  declared reference set. The defining full text has not been obtained, so
  this is prototype behavior rather than a source-qualified current-release
  estimator; no inference is attached.
- **Measure:** Candidate radial leave-one-out super-efficiency. The defining
  source's exact orientation, RTS, objective hierarchy, applicability, and
  score normalization remain unfrozen.
- **RTS:** The prototype exposes CRS, VRS, NIRS, and NDRS for internal testing.
  None is attributed to Andersen--Petersen (1993) in this release. A failed
  VRS solve is preserved rather than repaired by silently changing RTS.
- **Data / time:** Cross-sectional quantities and one immutable observation
  identifier per evaluated unit; duplicates and panels require a declared
  exclusion unit.
- **Native score:** The prototype reports input-oriented $\theta$ or
  output-oriented $1/\phi$ on a provisional higher-is-better scale, together
  with feasibility, reference exclusion, peers, and a solver-selected target.
  These are package reconstruction fields, not frozen source-native AP fields.
  Values beyond the ordinary self-inclusive efficiency bound are not “more
  than 100 percent technically efficient.”
- **Exact aliases:** Primal and multiplier forms only when orientation, RTS,
  exclusion, normalization, and score convention match.
- **Distinct variants:** Super-SBM, directional super-efficiency, VRS
  feasibility repairs, leave-group-out influence, cross-efficiency, and
  statistical outlier diagnostics.
- **Domain:** Each leave-one-out reference set must remain economically
  comparable and capable of supporting the selected orientation. Zero and
  signed data follow the base model's domain.
- **Failures:** Infeasible or unbounded programs, unstable extreme rankings,
  treating the result as proof of quality, excluding only one row of a
  duplicated organization, and comparing scores from different RTS or
  orientation conventions.
- **Solver form:** One radial LP per evaluation unit with self-exclusion and
  explicit infeasible/unbounded result states.
- **Defining source:** [Andersen and Petersen
  1993](https://doi.org/10.1287/mnsc.39.10.1261). A complete authorized copy
  was not obtained in the audited environment.
- **Evidence status:** `review-supported`, prototype/non-public, and
  `deferred_to_next_version`. Later Xue--Harker and Lu--Lo checks cannot
  replace page-level verification of the defining article. The controlling
  boundary and reopening gate are in
  [`source_protocols/andersen_petersen_1993_super_efficiency.md`](../source_protocols/andersen_petersen_1993_super_efficiency.md).
- **Oracle:** candidate property and later-source evidence only. A derived
  one-input/one-output CRS ratio check, a later input-VRS example, and an
  indirect reprint exercise the internal compiler, but no defining-source
  numerical reproduction or independent source-equation compiler is claimed.
- **Package recipe:** Candidate ID `evaluation.super.ap_radial`; internal
  prototype module `deapack.evaluation.super_efficiency`; public API none.
- **Book location:** **Evidence-deferred candidate.** The mainstream AP family
  has no current handbook placement until its defining-source and independent-oracle gates close.

### `evaluation.super.sbm.tone_2002` — Tone (2002) super-SBM

- **Economic question:** How can strongly efficient organizations be
  discriminated when their individual input excesses and output shortfalls,
  rather than a common proportional change, define how exposed they are to
  peer replacement?
- **Technology / estimator / inference:** Tone's source-qualified
  self-excluded convex technology and fractional/linearized super-SBM
  estimator, preceded by an ordinary non-oriented SBM strong-efficiency
  screen under the same RTS; inference remains separate.
- **Measure:** Source-native non-oriented, input-oriented, or output-oriented
  super-SBM under CRS, and non-oriented super-SBM under VRS. Only rows that
  pass the strong-efficiency screen receive a super score.
- **RTS:** CRS for all three supported orientations; VRS only for the
  non-oriented source formulation. VRS-oriented, NIRS, and NDRS variants are
  not inferred from neighboring models.
- **Data / time:** Strictly positive input and desirable-output quantities,
  immutable row IDs, and a declared reference policy in which the evaluated
  row belongs to the ordinary screen population before it is removed from a
  nonempty super-efficiency population.
- **Native score:** `score`/`super_sbm_score` is higher when the remaining
  organizations find the focal benchmark harder to replace through
  variable-specific resource and service adjustments. The result also keeps
  `sbm_screen_score`, `is_sbm_eligible`, applicability, exclusion, target,
  adjustment/slack, peer, and solve evidence. The score is not an efficiency
  percentage.
- **Exact aliases:** None with Andersen--Petersen radial super-efficiency even
  when both remove the same row and happen to rank one data set alike.
- **Distinct variants:** VRS-oriented super-SBM, undesirable-output
  super-SBM, structural/incidental-zero semantics, negative-data extensions,
  additive or directional super-efficiency, and later composite,
  nearest-point, or infeasibility-repair variants.
- **Domain:** Every input and desirable output is strictly positive. The
  source's discussion of structural and incidental zeros does not authorize
  an automatic zero classifier or an epsilon repair in this leaf; bad outputs
  and signed data are excluded.
- **Failures:** Screen failure, a non-strongly-efficient row presented as
  having a super score, a missing focal row or empty peer-only reference,
  infeasibility/unboundedness, invalid fractional normalization or
  back-transformation, silently changing the RTS/orientation/data model, and
  interpreting exposure as managerial superiority.
- **Solver form:** One ordinary non-oriented SBM screen under the declared RTS
  for every row, followed only for eligible rows by Tone's source fractional
  program and its Charnes--Cooper linearization; diagnostics distinguish
  `sbm_screen` from `super_sbm`.
- **Defining source:** [Tone
  2002](https://doi.org/10.1016/S0377-2217(01)00324-1).
- **Evidence status:** primary-checked and implemented/public on the bounded
  source surface above; unsupported orientation/RTS/data variants fail before
  optimization.
- **Oracle:** analytically derived — an exact two-organization VRS fixture
  certifies the peer-replacement score, targets, and intensity, while an
  independently assembled dense Charnes--Cooper programme checks both units.
  Broader project cases retain eligibility, domain, invariance, and failure
  checks; no source numerical table is redistributed or claimed.
- **Package recipe:** `ToneSuperSBM` with exact alias `SuperSBM` as
  `evaluation.super.sbm.tone_2002`; extensions receive separate
  source-qualified leaves.
- **Book location:** **Documentation/source review only.** This Super-SBM leaf
  does not stand in for the evidence-deferred mainstream AP family.

### `evaluation.super.directional.ray_2008`

- **Economic question:** Relative to the peer frontier that remains after a
  leader is removed, how exposed is that leader along a managerially declared
  joint input--output adjustment programme?
- **Technology / estimator / inference:** Ray's self-excluded convex
  technology with a declared directional-distance super-efficiency
  formulation; full estimator; no sampling inference in the base ranking.
- **Measure:** Source-qualified directional super-efficiency along
  $(g_x,g_y)$, retaining the paper's sign and display convention.
- **RTS:** The selected source formulation fixes the scale technology; later
  CRS/VRS or infeasibility-repair variants are distinct leaves.
- **Data / time:** Cross-sectional quantities, immutable unit IDs, and a
  direction with recorded units, provenance, controllability, and zero
  components.
- **Native score:** Signed/source-native directional super-distance plus the
  direction, peer frontier, target, and any display transform. No universal
  “larger is better” convention is imposed across directional variants.
- **Exact aliases:** Radial Andersen--Petersen super-efficiency only under a
  proven radial direction/score transformation and matched exclusion,
  technology, and target policy.
- **Distinct variants:** Alternative direction choices, non-radial
  super-efficiency, undesirable-output directions, super-SBM, range
  directions, and modified models designed to repair infeasibility.
- **Domain:** The direction must define a feasible and economically meaningful
  comparison after self-exclusion; scale and translation behavior depend on
  its construction.
- **Failures:** Ranking units under different directions, concealing
  infeasibility, changing the direction after seeing results, sign reversals
  in reported performance, and treating directional extremity as statistical
  evidence against an observation.
- **Solver form:** Self-excluded directional LP with direction and feasibility
  diagnostics stored per unit.
- **Defining source:** [Ray
  2008](https://doi.org/10.1057/palgrave.jors.2602392).
- **Evidence status:** primary-checked and implemented/public for the fixed VRS
  observed-bundle-direction protocol; other direction or feasibility rules
  require named variants.
- **Oracle:** analytically derived — an exact two-organization fixture proves
  the directional beta bound, reported score, target, and peer intensity, and
  an independently assembled dense equation-(8) programme checks both units.
  The multivariate project case adds stress and failure checks; no application
  observations, organization labels, or source score vector are bundled.
- **Package recipe:** `RayDirectionalSuperEfficiency` with exact alias
  `NerloveLuenbergerSuperEfficiency` under
  `evaluation.super.directional.ray_2008`.
- **Book location:** **Documentation/source review only.** No current handbook placement.

### `evaluation.cross.crs` (deferred prototype)

- **Economic question:** How does each organization perform when its peers'
  admissible valuations, rather than only its own most favorable valuations,
  are used for appraisal?
- **Technology / estimator / inference:** The internal reconstruction uses
  input-normalized CRS multiplier DEA. Each appraiser contributes one
  solver-selected primary optimum; no secondary preference rule or sampling
  inference is attached. This is prototype behavior, not a source-frozen
  current-release contract.
- **Measure:** The prototype forms a cross-efficiency matrix whose row is
  generated by one appraiser's selected admissible values, followed by an
  explicitly declared column aggregation. Its default is the equal mean
  including self. Summarizing the same matrix without its diagonal is a
  package experiment whose historical source identity has not been frozen.
- **RTS:** CRS in this canonical leaf. A VRS intercept changes peer-appraisal
  behavior and belongs to a separate formulation.
- **Data / time:** The prototype accepts cross-sectional desirable-output
  data with strictly positive input components, positive aggregate output,
  and stable appraiser/evaluatee IDs. The strict componentwise positivity
  rule is an engineering safeguard, not a verified universal source rule.
  Panel aggregation requires a separate time policy.
- **Native score:** Prototype fields include self-efficiency, a selected
  multiplier vector, the complete appraiser--evaluatee row, an aggregate peer
  score, aggregation count, and dispersion/disagreement diagnostics. Their
  exact correspondence to source-native EROW, ECOL, EBAR, and maverick
  definitions remains open.
- **Exact aliases:** The internal implementation retains
  `CRSCrossEfficiency` and `CrossEfficiency` as compatibility aliases. Neither
  is a current public API symbol. There is no exact alias between raw,
  aggressive, and benevolent cross-efficiency unless all primary multiplier
  optima yield the same peer row.
- **Distinct variants:** Doyle--Green's aggressive and benevolent secondary
  Method II and Method III programmes, neutral/minimax/common-weight rules,
  game cross-efficiency,
  interval/robust cross-efficiency, and VRS cross-efficiency.
- **Domain:** The prototype requires every peer denominator to be positive.
  Each primary solve and every derived ratio must pass independent
  primal--dual and dimensional certification before the appraiser contributes
  to an aggregate. These fail-closed rules describe package code and are not
  attributed to the unavailable defining source.
- **Failures:** Nonunique multiplier rows, zero denominators, rank reversal
  from an undisclosed secondary goal, averaging incomparable or invalid
  entries, and presenting peer consensus as an objective production fact.
- **Solver form:** One primary multiplier LP per appraiser, followed by
  dimensionless matrix assembly or streamed column summaries.
- **Defining sources:** [Sexton, Silkman, and Hogan
  (1986)](https://doi.org/10.1002/ev.1441) is the defining chapter and
  [Doyle and Green
  (1994)](https://doi.org/10.1057/jors.1994.84) is the principal
  secondary-goal source. Complete copies were not obtained in the audited
  environment. The complete later [Liang, Wu, Cook, and Zhu
  (2008)](https://doi.org/10.1287/opre.1070.0487) article supports an
  input-normalized CRS account and equal self-inclusive mean but does not
  replace the missing defining-source audit.
- **Evidence status:** `review-supported`, prototype/non-public, and
  `deferred_to_next_version`. The controlling boundary and reopening gate are
  in
  [`source_protocols/ordinary_crs_cross_efficiency.md`](../source_protocols/ordinary_crs_cross_efficiency.md).
- **Oracle:** candidate property evidence only. The neutral project-designed
  `strategic_peer_service` frame supplies a CCR diagonal, while unit rescaling
  and materialized/streamed-summary checks exercise internal consistency. No
  published observation or result table is reproduced. The production
  implementation is not an independent source-equation compiler; its raw
  off-diagonal matrix and ranking are solver selected and have no unique
  literature oracle.
- **Package recipe:** Candidate ID `evaluation.cross.crs`; internal prototype
  module `deapack.evaluation.cross_efficiency`; public API none.
- **Book location:** **Evidence-deferred candidate.** Ordinary cross-efficiency
  has no current handbook placement until its defining-source and independent-oracle gates close.

### Deferred Doyle--Green secondary cross-efficiency candidates

Doyle and Green's secondary programmes must not be collapsed into one
interchangeable `secondary_goal` switch. The review inventory currently names
four possible future leaves:

- `evaluation.cross.crs.doyle_green_1994.method_ii.aggressive`;
- `evaluation.cross.crs.doyle_green_1994.method_ii.benevolent`;
- `evaluation.cross.crs.doyle_green_1994.method_iii.aggressive`; and
- `evaluation.cross.crs.doyle_green_1994.method_iii.benevolent`.

Later literature indicates that Method II and Method III use materially
different secondary constructions and that aggressive and benevolent
directions remain separate. The complete 1994 source has not been obtained,
so this review does not freeze their exact objectives, normalizations, epsilon
or delta policies, zero-data boundaries, or numerical examples. The four
identifiers above are inventory labels only: they have no machine records, no
implementation, and no public API. Method I and every Method II/III candidate
are `deferred_to_next_version` under the ordinary cross-efficiency source
protocol.

### `evaluation.cross.game_nash.liang_wu_cook_zhu_2008`

- **Economic question:** In a competitive peer-appraisal setting, what
  performance profile is stable when a focal organization may choose a
  defensible CRS valuation that improves its own appraisal only while
  preserving one protected peer's current performance floor?
- **Technology / estimator / inference:** The source fixes the input-normalized
  CRS CCR multiplier system. At every synchronous iteration it solves
  $n^2$ distinct LPs, one for each protected DMU $d$ and focal/player DMU
  $j$. The $(d,j)$ LP maximizes $j$'s own score, normalizes $j$'s
  virtual input to one, imposes universal CCR feasibility, and adds one
  no-deterioration floor for $d$. It does not protect every DMU in one LP,
  and it adds no sampling inference.
- **Measure:** If $g_{dj}(\eta_d^{(t)})$ is the optimal focal-$j$ score
  from that one-floor LP, the source update/payoff is
  $$
  \eta_j^{(t+1)}
  =\frac{1}{n}\sum_{d=1}^n g_{dj}(\eta_d^{(t)}).
  $$
  The equal arithmetic mean over every $d$, including $d=j$, is part of
  the Liang--Wu--Cook--Zhu protocol. It is not a separately selectable
  aggregation policy.
- **RTS:** CRS is fixed by the source's CCR feasibility inequalities and
  focal-$j$ virtual-input normalization. A VRS intercept or any alternative
  base model is a separate source leaf.
- **Data / time:** Cross-sectional nonnegative input/output quantities with
  stable player IDs and valid focal virtual-input normalizations. A panel,
  changing player set, or repeated game requires a separately defined temporal
  protocol.
- **Native score:** The average game cross-efficiency vector
  $\eta^\star$, the protected--focal appraisal table, iteration history,
  adjacent-update and independently recomputed fixed-point residuals,
  termination reason, and multiplicity diagnostics. Table rows are
  `protected_dmu_id` $d$, columns are `focal_dmu_id` $j$, and every cell
  may use a different multiplier vector. It is therefore not the ordinary
  cross-efficiency matrix in which one appraiser's weights generate a whole
  row of evaluatee scores. The public implementation reports
  `score_uniqueness=source_claimed_not_computationally_certified` and
  `multiplier_uniqueness=not_assessed`.
- **Eleven-axis placement:** $C$ records the participating players;
  $T/E/M/V$ retain the fixed CRS CCR multiplier account; and $P$ owns the
  protected--focal LP family, simultaneous update, equal mean including self,
  stopping rule, and Nash claim. $A$ begins only with a downstream ranking
  or reporting analysis; it does not own the source mean.
- **Exact aliases:** None with aggressive, benevolent, neutral, minimax, or
  other secondary tie-breaks.
- **Distinct variants:** Alternative game cross-efficiency equilibria,
  asynchronous/Gauss--Seidel or damped updates, bargaining/cooperative
  appraisal, common-weight evaluation, ordinary secondary-goal
  cross-efficiency, the later VRS game model, network game cross-efficiency,
  and SBM/undesirable-output game models.
- **Equivalence boundary:** Level D. Ordinary secondary goals select among
  alternate optima of one appraiser's primary LP; the game couples DMUs and
  repeatedly changes the protected score floors. The protected--focal table
  also has different cell semantics from an ordinary appraiser--evaluatee
  matrix.
- **Domain:** Every initial score must be finite, nonnegative, and no larger
  than the corresponding CCR self-efficiency; the source's arbitrary,
  aggressive, and benevolent profiles are reproducible named examples. Every
  one of the
  $n^2$ LPs must return a finite certified optimum at each iteration. The
  source claims a unique final score vector independent of arbitrary,
  aggressive, or benevolent ordinary-cross-efficiency initialization; that
  claim does not establish unique pair-specific multipliers.
- **Failures:** Hiding initialization or iteration policy; replacing the
  source's simultaneous/Jacobi update with an asynchronous or damped update
  without creating a distinct policy; dropping self from the mean; exposing
  a free aggregation switch; treating a protected--focal table as an ordinary
  cross-efficiency matrix; calling a two-cycle, a maximum-iteration exit, or
  an LP failure a Nash result; or storing `game` as a `secondary_goal` value.
- **Solver form:** For every $(d,j)$, solve
  $$
  \begin{aligned}
  g_{dj}(\eta_d)&=\max_{u^{dj},v^{dj}\geq0}(u^{dj})^\top y_j\\
  \text{s.t.}\quad
  &(v^{dj})^\top x_\ell-(u^{dj})^\top y_\ell\geq0
    &&(\ell=1,\ldots,n),\\
  &(v^{dj})^\top x_j=1,\\
  &(u^{dj})^\top y_d
    \geq\eta_d(v^{dj})^\top x_d .
  \end{aligned}
  $$
  All $n^2$ problems use the same $\eta^{(t)}$ before the source mean
  produces $\eta^{(t+1)}$. Thus one iteration costs $n^2$ LP solves;
  retaining the pair table costs $O(n^2)$, while score history costs
  $O(Tn)$. A future implementation should compile one sparse structural
  template, stream column sums when pair details are not requested, and avoid
  retaining all pair-specific weights by default. The implementation compiles
  one constraint template per protected organization and follows that storage
  policy. After the source
  adjacent-iterate tolerance is met, it must evaluate the map once more and
  certify $\|F(\eta)-\eta\|_\infty$; a detected
  $\eta^{(t)}\approx\eta^{(t-2)}$ with a material adjacent gap is reported
  as a suspected two-cycle, not an equilibrium. Maximum-iteration and subproblem
  failures retain diagnostics/history but no canonical Nash score.
- **Defining source:** [Liang, Wu, Cook, and Zhu
  (2008)](https://doi.org/10.1287/opre.1070.0487).
- **Evidence status:** `primary-checked`; the CRS equations, double-indexed
  synchronous algorithm, convergence and result semantics are frozen. The
  leaf is implemented/public with
  a machine record, independent project-fixture cross-implementation,
  dedicated API, failure-closed certification, package Documentation, and a
  benchmark. Its current publication scope is `documentation_only`; it has no
  Handbook chapter.
- **Oracle:** cross-implemented — `strategic_peer_service` supplies a neutral protected--focal
  appraisal case. Tests independently verify the synchronous map, fixed-point
  residual, starting-policy invariance, streamed-storage path, suspected-cycle
  diagnostics, and failure closure without retaining a source observation or
  result table.
- **Package recipe:**
  `evaluation.cross.game_nash.liang_wu_cook_zhu_2008` as a dedicated
  evaluation protocol, not an option on ordinary cross-efficiency. It has no
  generic orientation, RTS, aggregation, or `secondary_goal` parameter. API
  symbols are `LiangWuCookZhuGameCrossEfficiency` and
  `GameCrossEfficiency`.
- **Book location:** **Documentation/source review only.** The game
  cross-efficiency leaf does not independently qualify the deferred parent family.

### `evaluation.cross.vrs.lim_zhu_2015`

- **Economic question:** How should peer appraisal be conducted when
  organizations operate at different scales and the CRS valuation system is
  not a credible description of their opportunities?
- **Technology / estimator / inference:** Lim--Zhu's source-qualified VRS
  cross-efficiency construction, including its treatment of the BCC intercept
  and peer evaluations; no sampling inference.
- **Measure:** Source-defined VRS cross-efficiency matrix and aggregate, not a
  CCR matrix with an unconstrained intercept pasted into each ratio.
- **RTS:** VRS by construction; CRS cross-efficiency remains a separate
  canonical leaf.
- **Data / time:** Cross-sectional quantities meeting the source's
  normalization conditions, stable IDs, and explicit scale/intercept
  treatment.
- **Native score:** VRS self-efficiency, selected valuation/intercept
  solution, cross-appraisal row, aggregate, and validity diagnostics for every
  matrix entry.
- **Exact aliases:** None with standard CRS cross-efficiency or a naïve BCC
  multiplier substitution.
- **Distinct variants:** Alternative VRS cross-efficiency definitions,
  aggressive/benevolent secondary goals, entropy/common-weight aggregation,
  scale-normalized cross-appraisal, and game procedures.
- **Domain:** The source's intercept and denominator conditions must make peer
  scores interpretable; translation and negativity behavior must be checked
  rather than inherited from CRS.
- **Failures:** Negative or otherwise invalid peer scores under naïve VRS
  ratios, nonunique intercept/weight solutions, hidden secondary objectives,
  and averaging entries that have different economic normalizations.
- **Solver form:** Source-defined VRS multiplier programs plus secondary
  optimization and cross-efficiency matrix assembly.
- **Defining source:** [Lim and Zhu
  2015](https://doi.org/10.1057/jors.2014.13).
- **Evidence status:** primary-checked; registry-provisional/planned with no
  repository implementation.
- **Oracle:** candidate — the defining source contains numerical analysis but
  no repository reproduction exists.
- **Package recipe:** Planned
  `evaluation.cross.vrs.lim_zhu_2015`; it must not be exposed as
  `rts="vrs"` on the Doyle--Green CRS preset without a proven formulation map.
- **Book location:** **Documentation/source review only.** No current handbook placement.

### Planned fitted global reference-set analysis

*analysis.reference_set.global.mehdiloozad_etal_2015* is a proposed analysis
leaf for identifying the global reference set/minimum face across alternate
optimal projections.

- **Eleven-axis placement:** $A$ owns the fitted peer/facet analysis and
  $P$ owns projection and alternate-optimum policy.
- **Equivalence boundary:** Level D/non-alias with $R$'s temporal
  `reference.global`. A fitted global reference set is an output of a model;
  the temporal global reference is an ex-ante all-period eligibility policy.
- **Use:** Interpret peers and targets for measures such as RAM/SBM and
  support projection-sensitive RTS analysis without pretending the
  solver-returned peer set is unique.
- **Defining source:** [Mehdiloozad et al.
  (2015)](https://doi.org/10.1016/j.ejor.2015.03.029).
- **Evidence status:** planned/evidence only; equations and an oracle must be
  frozen before registration or implementation.

### Pessimistic, worst-practice, and double-frontier appraisal

- **Economic question:** How should organizations be ranked when the analyst
  wants to retain both their most favourable best-practice appraisal and a
  declared least-favourable or worst-practice appraisal?
- **Technology / estimator / inference:** Source-qualified multiplier or
  envelopment appraisal relative to an inefficient/worst-practice boundary,
  followed, for double-frontier methods, by a declared combination rule. The
  construction is an evaluation protocol and carries no sampling inference by
  itself.
- **Measure:** Optimistic score, pessimistic score, and a source-specific
  interval, normalized, geometric, or other combined ranking value. Each
  remains visible rather than being replaced by the aggregate.
- **RTS:** Explicit for each best- and worst-practice programme; a matching RTS
  label does not establish that two pessimistic formulations are equivalent.
- **Data / time:** Comparable nonnegative quantities under the defining
  normalization, stable identifiers, and one frozen comparison-population and
  temporal-information policy for both appraisals.
- **Native score:** Source-native optimistic and pessimistic values with their
  direction and range, plus the declared double-frontier combination and rank.
- **Exact aliases:** None among least-favourable multiplier weights, an
  empirical worst-practice envelope, inverted DEA, anti-efficiency,
  double-frontier geometric efficiency, and interval efficiency unless the
  complete programmes and score transforms coincide.
- **Distinct variants:** CRS/VRS multiplier programmes; radial, slack, network,
  undesirable-output, interval-data, and non-convex worst-practice models;
  arithmetic, geometric, and normalized combinations; aggressive
  cross-efficiency as a secondary peer-weight rule; and pessimistic
  interval/fuzzy/robust data scenarios as uncertainty mechanisms.
- **Domain:** Both appraisals require well-defined denominators and comparable
  score conventions. The worst-practice boundary must exist and the
  combination rule must preserve the interpretation claimed.
- **Failures:** Treating the worst-practice boundary as an attainable
  best-practice production frontier, hiding one component behind a rank,
  combining incompatible scales, nonunique multiplier solutions, and
  presenting discrimination power as technical-efficiency validity. The word
  “pessimistic” never establishes equivalence across valuation, frontier,
  cross-appraisal, and uncertainty mechanisms.
- **Solver form:** Paired source-specific multiplier or envelopment programmes
  plus transparent score normalization and aggregation; alternate optima may
  require secondary programmes.
- **Defining source:** Optimistic/pessimistic geometric appraisal in
  [Wang, Chin, and Yang
  (2007)](https://doi.org/10.1057/palgrave.jors.2602205);
  inefficient-frontier methods as a separate ranking category in
  [Aldamak and Zolfaghari
  (2017)](https://doi.org/10.1016/j.measurement.2017.04.028).
- **Evidence status:** review-supported at the family and ranking-boundary
  level; individual executable formulations remain registry-provisional.
- **Oracle:** not located — no published optimistic/pessimistic numerical
  example has been reproduced in repository tests.
- **Package recipe:** Registry-provisional worst-practice appraisal family and
  source-qualified double-frontier presets; no public constructor or universal
  pessimistic score convention is asserted.
- **Book location:** **Documentation/source review only.** No current handbook placement.

### `evaluation.frontier_tiers.context_dependent.seiford_zhu_2003`

- **Economic question:** How far is an organization from the next credible
  performance tier, how attractive is it relative to poorer tiers, and what
  progress is required toward better tiers?
- **Technology / estimator / inference:** Seiford--Zhu's iterative
  context-dependent DEA procedure, which constructs successive empirical
  performance levels from a declared base technology; no sampling inference.
- **Measure:** Tier membership plus source-defined attractiveness and progress
  measures relative to selected poorer or better evaluation contexts.
- **RTS:** Inherited consistently in every tier-extraction and contextual fit;
  changing RTS between levels creates a different procedure.
- **Data / time:** Cross-sectional quantities and stable unit IDs; ties,
  duplicate frontier observations, and the stopping rule are explicit.
- **Native score:** Ordered performance level, contextual score, chosen
  evaluation context, and target/peer information for attractiveness or
  progress.
- **Exact aliases:** None with super-efficiency, quantile/partial frontiers,
  clustering, metafrontiers, or conditional DEA.
- **Distinct variants:** Value-judgement extensions, alternative layer-peeling
  rules, context-dependent SBM, dynamic tiers, and two-step reachable
  benchmarking.
- **Domain:** Successive reference sets must remain viable and economically
  comparable; a tier is relative to the sample and technology, not a universal
  quality grade.
- **Failures:** Empty later tiers, arbitrary tie removal, treating tier numbers
  as cardinal distances, comparing tiers across changed samples without a
  mapping, and interpreting attractiveness as causal demand.
- **Solver form:** Iterative DEA fits with deterministic frontier extraction,
  tier bookkeeping, and contextual re-evaluation.
- **Defining source:** [Seiford and Zhu
  2003](https://doi.org/10.1016/S0305-0483(03)00080-X).
- **Evidence status:** primary-checked; registry-provisional/planned with no
  repository implementation.
- **Oracle:** candidate — the paper's illustrations have been identified but
  not reproduced in automated repository tests.
- **Package recipe:** Planned
  `evaluation.frontier_tiers.context_dependent.seiford_zhu_2003`; tier
  extraction and
  attractiveness/progress contexts are mandatory result metadata.
- **Book location:** **Documentation/source review only.** No current handbook placement.

### `evaluation.target_selection.closest_strong.aparicio_ruiz_sirvent_2007`

- **Economic question:** Which strongly efficient operating plan requires the
  least managerially meaningful change from current practice, rather than
  whichever target happens to be returned by a radial or slack optimum?
- **Technology / estimator / inference:** Declared convex production
  technology and full DEA estimator followed by the
  Aparicio--Ruiz--Sirvent source-qualified closest-target selector over the
  Pareto-efficient frontier; no inference.
- **Measure:** Minimum distance to a strongly efficient target under an
  explicitly chosen similarity norm/criterion.
- **RTS:** Inherited unchanged from the base technology and encoded in the
  strong-frontier selection program.
- **Data / time:** Cross-sectional quantities, scaling/normalization for every
  distance component, controllability roles, and any operational bounds.
- **Native score:** Minimum target distance, strong target, reference peers,
  active efficient face, and reconstruction/strong-efficiency diagnostics;
  the base efficiency score remains separately available.
- **Exact aliases:** None with slack maximization, arbitrary second-phase
  projection, nearest observed peer, or minimum radial distance.
- **Distinct variants:** $L_1$, $L_\infty$, weighted, lexicographic, and
  goal-adjusted closest targets; furthest targets; efficient-facet approaches;
  bounded, integer, and context-dependent reachable targets.
- **Domain:** Distance weights and units must encode a defensible adjustment
  burden, and the selected target must be Pareto--Koopmans efficient under the
  same technology and authorized variables.
- **Failures:** Unit-dependent “closeness,” weakly efficient targets,
  unsupported big-$M$ values, multiple equidistant targets hidden as unique,
  and recommending a mathematically close but operationally infeasible plan.
- **Solver form:** Source-defined mathematical program; common strong-facet
  formulations require MILP/complementarity machinery and deterministic
  alternate-target handling.
- **Defining source:** [Aparicio, Ruiz, and Sirvent
  2007](https://doi.org/10.1007/s11123-007-0039-5).
- **Evidence status:** primary-checked; registry-provisional/planned with no
  repository implementation.
- **Oracle:** candidate — published illustrations are available but have not
  been reproduced in automated repository tests.
- **Package recipe:** Planned
  `evaluation.target_selection.closest_strong.aparicio_ruiz_sirvent_2007`
  beneath the non-executable `evaluation.target_selection` family.
- **Book location:** **Documentation/source review only.** No current handbook placement.

### `data.integer_discrete.lozano_villa_2006`

- **Economic question:** What efficiency score and actionable target should be
  reported when staff, vehicles, facilities, cases, or other operating
  quantities can change only in whole units and continuous-target rounding can
  reverse feasibility or dominance?
- **Technology / estimator / inference:** Lozano--Villa's source-qualified
  integer-valued DEA formulation over a declared continuous base technology;
  mixed-integer estimator; no inference.
- **Measure:** Source-defined radial efficiency and integer-feasible
  input/output targets, with continuous and integer variable blocks retained.
- **RTS:** The exact returns-to-scale version is part of the recipe; alternative
  integer RTS axioms are distinct from changing one convexity row.
- **Data / time:** Variables explicitly marked integer or continuous, with
  measurement units, minimum increments, bounds, and operational horizon.
- **Native score:** Source-native efficiency, integer-feasible target,
  component slacks, and integrality gap relative to the comparable continuous
  relaxation.
- **Exact aliases:** None with fitting continuous DEA and rounding its targets.
- **Distinct variants:** Kuosmanen--Kazemi Matin's axiomatic integer
  technology, alternative RTS axioms, bounded integer outputs, integer SBM,
  binary/categorical decisions, and mixed-integer network targets.
- **Domain:** An integer role must represent a genuinely indivisible
  production quantity at the stated unit and horizon; large counts may be
  better modeled continuously.
- **Failures:** Infeasible rounded targets, arbitrary unit rescaling that
  changes integrality, confusing categorical labels with counts, weak
  relaxations, large branch-and-bound cost, and omitted target bounds.
- **Solver form:** Source-defined MILP plus a matched continuous relaxation for
  diagnostics.
- **Defining source:** [Lozano and Villa
  2006](https://doi.org/10.1016/j.cor.2005.02.031).
- **Evidence status:** primary-checked; registry-provisional/planned with no
  repository implementation.
- **Oracle:** candidate — the source includes numerical analysis, but no
  example has been reproduced in automated repository tests.
- **Package recipe:** Planned
  `data.integer_discrete.lozano_villa_2006`, composed only with the exact base
  technology supported by the source.
- **Book location:** **Documentation/source review only.** No current handbook placement.

### `technology.integer_discrete.kuosmanen_kazemi_matin_2009`

- **Economic question:** What is the smallest empirically justified production
  set when some quantities are naturally indivisible, so that benchmark plans
  and their scale extrapolations respect integer production theory rather than
  merely imposing integer target variables?
- **Technology / estimator / inference:** Kuosmanen--Kazemi Matin's
  source-qualified integer production technology based on natural
  disposability and natural divisibility; mixed-integer empirical estimator;
  no inference.
- **Measure:** Compatible source-defined radial efficiency and integer target
  over the axiomatized integer technology.
- **RTS:** The 2009 base axioms and any alternative RTS-axiom extensions are
  separate source-qualified technologies.
- **Data / time:** Integer and continuous quantity blocks, natural unit,
  bounds, and replication/divisibility interpretation declared for each
  variable.
- **Native score:** Source-native efficiency and integer target plus the active
  natural-disposability/divisibility and RTS axioms.
- **Exact aliases:** None with the Lozano--Villa MILP unless feasible sets and
  score/target mappings are proven equal for the declared dataset and domain.
- **Distinct variants:** Lozano--Villa integer targets, alternative RTS axioms,
  bounded-output integer technology, mixed binary decisions, integer network
  technologies, and continuous DEA relaxations.
- **Domain:** The natural divisibility and disposability axioms must be
  credible for the counted activities; they cannot be inferred solely because
  recorded observations contain no decimals.
- **Failures:** Minimum-extrapolation violations, implausible replication of
  indivisible units, sensitivity to measurement unit, infeasible MILPs,
  solver gaps, and presenting the continuous relaxation as the integer result.
- **Solver form:** Source-derived MILP with explicit integrality, RTS, optimality
  gap, and relaxation diagnostics.
- **Defining source:** [Kuosmanen and Kazemi Matin
  2009](https://doi.org/10.1016/j.ejor.2007.09.040).
- **Evidence status:** primary-checked; registry-provisional/planned with no
  repository implementation.
- **Oracle:** candidate — the university-department application has been
  identified but not reproduced in automated repository tests.
- **Package recipe:** Planned
  `technology.integer_discrete.kuosmanen_kazemi_matin_2009`; it remains
  distinct from `data.integer_discrete.lozano_villa_2006`.
- **Book location:** **Documentation/source review only.** No current handbook placement.

## 5. Do organizations face the same opportunities?

The comparison population answers who is eligible to teach whom. It is
separate from the temporal information set, which answers which periods of
those organizations are visible, and from an evaluation exclusion such as
leave-one-out. A group population can therefore be evaluated
contemporaneously, sequentially, globally, or within a window. The resulting
positive-intensity peers are fitted outputs, not the comparison-population
definition.

### Group frontiers and `heterogeneity.metafrontier`

- **Economic question:** How much of a unit's performance gap is internal to
  its known group, and how much reflects a gap between the group's
  opportunities and a broader meta-technology?
- **Implemented source leaf:** The public
  `heterogeneity.metafrontier.radial.odonnell_rao_battese_2008` operator fits
  the same Farrell radial programme against the unit's declared group and
  against all declared groups pooled. It is narrower than the non-executable
  umbrella family.
- **Technology / estimator / inference:** Under VRS, the meta opportunity set
  is the free-disposal pooled convex hull (`pooled_convex`); under CRS it is
  the pooled cone (`pooled_conic`). The group and meta fits use the same
  orientation, RTS, quantities, units, and temporal rule. Sampling inference
  is not supplied by this deterministic operator.
- **Measure:** `group_efficiency` describes operating performance relative to
  the opportunities represented within the declared group.
  `metafrontier_efficiency` describes performance relative to the broader
  opportunity set. Their ratio is the canonical metatechnology ratio
  (`MTR`), which describes how close the group frontier lies to the broader
  meta frontier at the evaluated mix.
- **RTS:** Matched `vrs` or `crs` at both levels; VRS is the source-profile
  default.
- **Data / time:** Nonnegative resources and desirable services plus exactly
  one ex ante group label per observation and at least two nonempty groups.
  For panel input, all study periods are pooled at both levels in this source
  profile.
- **Native score:** MTR is higher-is-closer and satisfies
  `metafrontier_efficiency = group_efficiency * metatechnology_ratio` after
  certified matched solves.
- **Exact aliases:** `technology_gap_ratio` and `TGR` are historical aliases
  of MTR; $1-\mathrm{MTR}$ must not be called the source TGR. A pooled convex
  or conic frontier is not an alias for the non-convex union of group
  technologies.
- **Distinct variants:** Radial/non-radial metafrontiers, group productivity,
  environmental metafrontiers, latent-group models, club frontiers, and
  conditional frontiers require separate source-qualified leaves.
- **Domain:** Groups require comparable missions and common variable meanings;
  nestedness must hold for the reported technology-gap interpretation.
- **Failures:** Choosing groups from the resulting scores, pooled
  convexification that creates implausible cross-group mixtures, identity
  failure, empty groups, and interpreting an opportunity gap as managerial
  inefficiency.
- **Solver form:** The default runs exactly one group and one pooled-meta
  radial LP per observation. Slack-completed targets and peers are an opt-in
  refinement and keep the group and meta accounts separate.
- **Defining source:** [O'Donnell, Rao, and Battese
  2008](https://doi.org/10.1007/s00181-007-0119-4).
- **Evidence status:** Primary-checked, implemented, and public with
  `cross_implementation` verification.
- **Oracle:** Cross-implemented — the source scalar checkpoint
  ($E^M=0.60$, $E^G=0.80$, $\mathrm{MTR}=0.75$), an exact
  six-organization analytic example, and an independently compiled direct LP
  are automated. The paper's 485 observation rows and DEAP control files are
  unavailable, so the agricultural application is not claimed as reproduced.
- **Package recipe:** `RadialMetafrontierDEA` with the concise alias
  `MetafrontierDEA`; both resolve to the same method ID. Results always store
  the comparison populations, temporal policy, and pooled hull construction.
- **Management interpretation:** Within-group efficiency and opportunity
  proximity are complementary accounting components. A low value in either
  component does not identify managerial blame, regulatory causation, or the
  feasibility and cost of adopting a meta-frontier benchmark.
- **Book location:** **Active core placement:** `book/chapters/07-heterogeneity/23-metafrontier.md`; the package reference is `docs/analysis/metafrontier.md`.

### `heterogeneity.nonhomogeneous_dmu`

- **Economic question:** Can units with structurally different service
  portfolios, resource availability, or specialization still be compared
  without pretending that absent activities are zeros?
- **Technology / estimator / inference:** Explicit comparability/incidence
  technology, possibly multi-activity or partial input--output relations;
  declared estimator; separate inference.
- **Measure:** Compatible radial, directional, slack, or system measure with
  the comparability structure active.
- **RTS:** Declared for each relevant activity/system level.
- **Data / time:** Quantities plus activity availability, structural absence,
  mission, and incidence metadata.
- **Native score:** Base/system score plus the active-variable and admissible
  peer structure.
- **Exact aliases:** None with missing-data repair, categorical DEA,
  metafrontier, or network DEA unless the graph and feasible set are exactly
  matched.
- **Distinct variants:** Partial input--output relations, multi-activity DEA,
  non-homogeneous DMU models, categorical restrictions, and group frontiers.
- **Domain:** Missions and common output meanings must remain comparable; a
  structurally absent service is not numerically zero production.
- **Failures:** Artificially favorable scores from unavailable activities,
  empty comparison sets, incompatible denominators, and hidden cross-activity
  resource sharing.
- **Solver form:** Structured LP or MILP depending on activity incidence and
  peer selection.
- **Defining source:** The generic family remains under source audit; no single
  paper is declared canonical in this review. Every executable leaf must cite
  its exact incidence and aggregation formulation.
- **Evidence status:** registry-provisional; a canonical primary-source leaf
  has not yet been selected.
- **Oracle:** not located — no certified numerical example has been selected.
- **Package recipe:** Planned `heterogeneity.nonhomogeneous_dmu` plus explicit
  `technology.partial_incidence` or `graph.multi_activity`.
- **Book location:** **Documentation/source review only.** Nonhomogeneous-DMU
  variants have no independent placement in the current handbook.

### Operating environment: second stage, conditional frontier, and three-stage adjustment

- **Economic question:** Is an operating condition merely associated with
  estimated inefficiency, does it change attainable opportunities, or should
  observed quantities be adjusted under a parametric noise/environment model?
- **Technology / estimator / inference:** Three distinct designs:
  Simar--Wilson uses a common first-stage technology and a truncated
  second-stage model with a tailored bootstrap; conditional DEA/FDH changes
  the frontier estimator using local environmental information; Fried's
  DEA--SFA--DEA workflow adjusts observations under a parametric decomposition
  and refits the frontier.
- **Measure:** First-stage efficiency plus design-specific regression,
  conditional efficiency, or pre/post-adjustment efficiency.
- **RTS:** Declared for every fitted frontier; not determined by the
  environmental-variable method.
- **Data / time:** Quantities plus contextual conditions; bandwidth and kernel
  policy for conditional estimators; distributional and panel/dependence
  assumptions where relevant.
- **Native score:** All component scores and models are retained; a coefficient
  on an inefficiency outcome is not an efficiency score.
- **Exact aliases:** None among the three designs. They answer different
  questions and make different assumptions.
- **Distinct variants:** Simar--Wilson Algorithms 1 and 2, conditional DEA and
  conditional FDH, separability tests, location-scale models, and Fried's
  three-stage variants.
- **Domain:** Requires a defensible causal/associational estimand, support in
  the contextual variables, and a separability decision. Causal claims require
  assumptions beyond DEA.
- **Failures:** Naive OLS/Tobit on estimated scores, bandwidth collapse,
  boundary/support bias, double use of data, unrecorded pre/post adjustment,
  and treating correlation as managerial causation.
- **Solver form:** DEA/FDH plus truncated regression and bootstrap;
  conditional kernel computation; or DEA + stochastic-frontier estimation +
  DEA.
- **Defining source:** Two-stage inference [Simar and Wilson
  2007](https://doi.org/10.1016/j.jeconom.2005.07.009); conditional frontier
  [Daraio and Simar
  2005](https://doi.org/10.1007/s11123-005-3042-8); three-stage adjustment
  [Fried et al.
  2002](https://doi.org/10.1023/A:1013548723393).
- **Evidence status:** primary-checked; the three designs are
  registry-provisional/planned with no repository implementation.
- **Oracle:** candidate — literature examples have been identified but not
  reproduced in automated repository tests.
- **Package recipe:** Planned, distinct
  `context.second_stage.simar_wilson`,
  `estimator.conditional.dea` / `estimator.conditional.fdh`, and
  `context.three_stage.fried2002`. Algorithms 1 and 2 require separate preset
  metadata even if they share code.
- **Book location:** **Documentation/source review only.** Operating-environment
  estimators have no current handbook placement.

## 6. Decisions fixed by this review

1. The finite input-oriented CRS polyhedral cone-ratio sum-form leaf is
   implemented/public as the only current weight-restriction leaf. Its 1990
   Example 2 is independently reproducible; Example 3/Table 2 has an
   unresolved two-row source conflict and is not an oracle. This leaf is not
   implemented boundary does not open a generic restrictions API.
2. AR-I constrains ratios within the input side or within the output side.
   AR-II links input and output multiplier sides. Wong--Beasley constrains
   observation-specific virtual shares, while common weights impose one
   joint appraisal system. These remain distinct recipes and deferred source
   gates; none is an alias of the public sum-form cone-ratio leaf.
3. Production trade-offs act on the technology; assurance regions act on
   valuations. A dual relationship does not erase that semantic boundary.
4. Banker--Morey nondiscretionary and categorical models describe distinct
   executable special-data recipes rather than preprocessing tricks or
   generic contextual estimators. Both named leaves are deferred to the next
   version under separate source protocols. The public source-neutral radial
   eligibility policy is neither leaf and carries no categorical
   interpretation.
5. Data semantics such as `nondiscretionary` or `categorical` do not by
   themselves identify a solver. They must compose with a named technology and
   measure.
6. A pooled frontier, a group frontier, a metafrontier, and a conditional
   frontier are not interchangeable responses to heterogeneity.
7. Simar--Wilson second stage, conditional DEA/FDH, and Fried's three-stage
   workflow remain separate in code, metadata, evidence claims, and the book.
8. Andersen--Petersen, super-SBM, and directional super-efficiency are
   distinct self-excluded measures. Only Tone's bounded super-SBM leaf is
   public in the current release; the AP reconstruction is deferred and the
   directional family remains planned. Super-efficiency is a discrimination
   and sensitivity result, not “efficiency above 100 percent.”
9. Ordinary cross-efficiency is conceptually a matrix-valued peer-appraisal
   procedure, but its CRS reconstruction is deferred until the defining-source
   gate closes. CRS and VRS formulations and every secondary-goal policy
   remain visible as distinct inventory choices. The public
   Liang--Wu--Cook--Zhu game cross-efficiency leaf is a separate fixed-CRS
   protocol: $n^2$ protected--focal LPs, a simultaneous update, and the equal
   mean including self remain source-fixed rather than entering
   `secondary_goal` or aggregation selectors.
10. Context-dependent tiers, closest strong targets, and integer-feasible
   targets answer different benchmarking questions and cannot be implemented
   as display options on one radial fit.
11. Lozano--Villa's integer recipe and Kuosmanen--Kazemi Matin's axiomatic
    integer technology retain separate source-qualified IDs.
12. Least-favourable weights, worst-practice envelopes, double-frontier
    combinations, and robust worst-case uncertain data are different
    mechanisms. None is a more “true” technical-efficiency score by default.
