# Review register: statistics and uncertainty in DEA

## Purpose: three questions, three layers

“Uncertainty” is not one model switch. This review separates:

1. **Technology:** What production possibilities and uncertainty mechanism are
   maintained?
2. **Estimator:** How does a finite sample construct a frontier or partial
   frontier?
3. **Inference:** Given a data-generating process and an estimator, what can be
   said about bias, sampling variation, confidence sets, or hypotheses?

For example, a convex production technology may be estimated by full-sample
DEA or a conditional estimator. A Simar--Wilson bootstrap may then supply
inference for a supported estimator. In contrast, a chance-constrained model
puts probability inside the feasibility statement; it is not a bootstrap.

The source of uncertainty or dependence is recorded before a method is
chosen:

| Source or structure | Meaning |
|---|---|
| sampling uncertainty | the empirical frontier is estimated from a population sample |
| data or measurement uncertainty | recorded inputs or outputs are noisy, bounded, imprecise, or fuzzy |
| production risk | the feasible outcome depends on a state of nature not known when commitments are made |
| robust scenario uncertainty | performance must hold over a declared uncertainty set or scenario family |
| dependence | observations are spatially, serially, clustered, panel, or network related |

These sources can sometimes be composed, but they are not aliases. Solver
tolerance remains a numerical diagnostic rather than a sixth substantive
source.

Every record uses the same fields. `Evidence status` records
primary-source/review support and any registry or repository implementation
evidence. `Oracle` is separate and begins with exactly one controlled status:
`not located`, `candidate`, `analytically derived`, `reproduced`, or
`cross-implemented`. The last three mean an automated independent numerical
oracle exists; analytical derivation does not claim a published-data
reproduction.

At the time of this review, the public catalog exposes deterministic frontier
methods but no inferential or uncertain-data procedure. Consequently, none of
the records below is a current-edition implementation merely because its base
DEA model exists. They form a next-version evidence queue. A leaf can enter the
public package only after its source protocol freezes the estimator and DGP,
an independent numerical oracle verifies the permitted claims, and a typed
result and failure contract keeps the base estimate, uncertainty statement,
replication diagnostics, and invalid states distinct. Until all three gates
close, a name in this review is a planning identity rather than a callable API
or a Handbook route.

## 1. What is random in a deterministic frontier estimate?

### Statistical foundation for full-sample DEA

- **Economic question:** If observed organizations are a sample from a wider
  production population, how does the empirical frontier relate to the
  underlying best-practice boundary?
- **Technology / estimator / inference:** Convex production technology; full
  empirical DEA estimator; consistency/rate/distribution results only under
  their stated sampling and smoothness assumptions.
- **Measure:** A declared radial, directional, or other supported distance
  estimator.
- **RTS:** Part of both the estimator and its asymptotic assumptions; CRS and
  VRS results are not interchangeable.
- **Data / time:** Usually independent cross-sectional draws with support and
  density conditions near a smooth boundary. Panel, spatial, cluster, and
  serial dependence require separate theory.
- **Native score:** The base measure's native value plus estimator dimension
  and sampling assumptions.
- **Exact aliases:** None between a deterministic DEA optimum and its
  population counterpart. Consistency does not make a finite-sample score an
  observed truth.
- **Distinct variants:** DEA versus FDH, full versus partial frontier, radial
  versus directional distance, and conditional versus unconditional
  estimation.
- **Domain:** Theorems are measure-, dimension-, RTS-, boundary-, and
  data-generating-process specific.
- **Failures:** Treating DMUs as a census while reporting sampling confidence
  intervals, ignoring the curse of dimensionality, assuming iid observations
  in repeated panels, and transferring one asymptotic result to another
  measure.
- **Solver form:** The deterministic LP/FDH estimator plus separate statistical
  computation.
- **Defining source:** Statistical foundation [Banker
  1993](https://doi.org/10.1287/mnsc.39.10.1265); state-of-the-art review
  [Simar and Wilson
  2000](https://doi.org/10.1023/A:1007864806704); asymptotics and bootstrap
  consistency [Kneip, Simar, and Wilson
  2008](https://doi.org/10.1017/S0266466608080651).
- **Evidence status:** primary-checked and review-supported at the theoretical
  level; no repository inferential implementation is asserted.
- **Oracle:** not located — this foundation record is theoretical and no
  automated numerical oracle is claimed.
- **Package recipe:** No generic executable ID. Every inferential result must
  record a base technology ID, estimator ID, measure ID, dimensionality, DGP,
  and inference procedure ID.
- **Book location:** **Documentation/source review only.** No current handbook placement.

### `inference.bootstrap.frontier_efficiency.simar_wilson_1998`

- **Economic question:** How much finite-sample bias and sampling uncertainty
  surrounds an estimated frontier-efficiency score?
- **Technology / estimator / inference:** Declared deterministic production
  technology; supported full-sample DEA/FDH estimator; the source-qualified
  Simar--Wilson smoothed frontier bootstrap.
- **Measure:** Bias estimate, bias-corrected score when admissible, standard
  error, and confidence interval for a supported efficiency/distance measure.
- **RTS:** Must match the bootstrap's maintained estimator and DGP.
- **Data / time:** Cross-sectional sample satisfying the chosen bootstrap's
  independence, support, density, and smoothing assumptions.
- **Native score:** Original estimate remains primary; bias estimate,
  bias-corrected value, interval, bandwidth, replications, random seed, and
  failed-replication count are separate fields.
- **Exact aliases:** None with naive row resampling, ordinary case bootstrap,
  deterministic perturbation analysis, or leave-one-out influence.
- **Distinct variants:** Homogeneous versus heterogeneous smoothing,
  DEA/FDH-specific designs, m-out-of-n/subsampling methods, and
  measure-specific directional procedures.
- **Domain:** Only estimators and DGPs covered by the bootstrap theory;
  bandwidth and boundary treatment are part of the estimator, not hidden
  defaults.
- **Failures:** Invalid naive resampling of an extreme boundary, scores outside
  the measure domain, excessive failed replications, unstable bandwidth,
  dimensional sparsity, and bias correction larger than the original
  estimated distance.
- **Solver form:** Repeated fitting of source-generated pseudo-samples, with
  compiled deterministic tasks reused where mathematically valid.
- **Defining source:** [Simar and Wilson
  1998](https://doi.org/10.1287/mnsc.44.1.49); consistency conditions refined
  in [Kneip, Simar, and Wilson
  2008](https://doi.org/10.1017/S0266466608080651).
- **Evidence status:** primary-checked; registry-provisional/planned with no
  repository inferential implementation.
- **Oracle:** candidate — published illustrations have been identified but not
  reproduced in automated repository tests.
- **Package recipe:** Planned source-qualified leaf
  `inference.bootstrap.frontier_efficiency.simar_wilson_1998` beneath
  registry family `inference.bootstrap.frontier_efficiency`.
- **Book location:** **Documentation/source review only.** No current handbook placement.

### `inference.bootstrap.directional_distance.simar_vanhems_wilson_2012`

- **Economic question:** What sampling uncertainty surrounds a directional
  improvement potential, including cases with undesirable or signed outcomes?
- **Technology / estimator / inference:** Convex technology; DEA estimator of
  a declared directional distance; Simar--Vanhems--Wilson's source-qualified
  asymptotic theory and consistent bootstrap for the DEA directional-distance
  estimator.
- **Measure:** Directional distance estimate, bias/standard error or confidence
  interval, and any hypothesis statistic supported by the source.
- **RTS:** The cited asymptotic results must be matched, including VRS where
  required.
- **Data / time:** Cross-sectional data with the regularity conditions of the
  directional-distance theory; the direction construction must be stored.
- **Native score:** Original $\beta_o$ plus inference results. A transformed
  efficiency score does not replace the native directional quantity.
- **Exact aliases:** A directional procedure is equivalent to radial inference
  only under the exact radial-direction transform and all matched statistical
  assumptions.
- **Distinct variants:** Simar--Vanhems' probabilistic FDH and robust
  directional estimators, observation-specific directions, environmental DDF,
  cross-period directions, conditional directional estimators, and
  directional hypothesis tests.
- **Domain:** Direction and boundary smoothness/support assumptions must hold;
  zero directions and unidentified components are invalid.
- **Failures:** Reusing a radial bootstrap without equivalence proof, changing
  directions across replications without declaring the estimator, and
  suppressing negative cross-technology distances.
- **Solver form:** Repeated directional DEA plus the source's subsampling or
  bootstrap algorithm.
- **Defining source:** [Simar, Vanhems, and Wilson
  2012](https://doi.org/10.1016/j.ejor.2012.02.030).
- **Evidence status:** primary-checked; registry-provisional/planned.
- **Oracle:** candidate — published empirical illustrations have been
  identified but not reproduced in automated repository tests.
- **Package recipe:** Planned
  `inference.bootstrap.directional_distance.simar_vanhems_wilson_2012`,
  requiring `static.directional_distance`, the source-supported convex DEA
  estimator, and explicit direction provenance. FDH, robust, conditional, and
  environmental procedures require their own validated leaves.
- **Book location:** **Documentation/source review only.** No current handbook placement.

## 2. How uncertain is measured productivity change?

### `inference.bootstrap.productivity.simar_wilson_1999`

- **Economic question:** Is an estimated change in productivity, operating
  performance, or best-practice opportunities distinguishable from sampling
  variation?
- **Technology / estimator / inference:** Period-specific production
  technologies; supported DEA estimators; the source-qualified bootstrap for
  a named Malmquist construction.
- **Measure:** Malmquist estimate and decomposition, bootstrap bias/standard
  errors, and confidence intervals or tests supported by the source.
- **RTS:** Must match every component distance and the productivity identity.
- **Data / time:** Matched panel observations and explicitly declared frontier
  samples for both periods; dependence across time and units must follow the
  resampling design.
- **Native score:** The original productivity index and each component remain
  visible beside all bootstrap summaries.
- **Exact aliases:** None between bootstrapping component distances
  independently and bootstrapping the joint productivity construction.
- **Distinct variants:** Adjacent, global, and biennial Malmquist; Luenberger;
  Malmquist--Luenberger; Hicks--Moorsteen; and source-specific panel
  resampling. Validation for one does not transfer automatically.
- **Domain:** All required within- and cross-period distances must be defined;
  balanced/matched-unit policy and frontier-sample policy are part of the
  estimator.
- **Failures:** Broken time pairing, infeasible cross-period evaluations,
  ignoring within-unit dependence, changing reference technologies across
  replications, and attaching independent intervals to a decomposition
  identity.
- **Solver form:** Repeated complete productivity-task graphs, not unrelated
  resampling of four distance columns.
- **Defining source:** [Simar and Wilson
  1999](https://doi.org/10.1016/S0377-2217(97)00450-5).
- **Evidence status:** primary-checked; deterministic DEAPack productivity
  operators have repository property evidence, while the inferential procedure
  is registry-provisional/planned.
- **Oracle:** candidate — the published inferential illustration has been
  identified but not reproduced in automated repository tests.
- **Package recipe:** Planned
  `inference.bootstrap.productivity.simar_wilson_1999`, initially limited to
  the exact supported Malmquist composition. Other indexes require independent
  leaves.
- **Book location:** **Documentation/source review only.** No current handbook placement.

### Planned modern productivity-inference leaves

- **Planning question:** What uncertainty surrounds aggregate productivity
  change, and when do finite-sample or limiting approximations support
  inference for the named index?
- **Technology / estimator / inference:** The exact frontier estimator,
  productivity task graph, aggregation weights, panel DGP, and dependence
  design must be bound together.
- **Eleven-axis placement:** $A$ owns the named productivity and aggregation
  operator; $U$ owns resampling/asymptotic theory and the panel DGP.
- **Equivalence boundary:** Level D versus the 1999 individual-index
  smoothed bootstrap and versus deterministic aggregation.
- **Defining source:** Aggregate productivity inference in
  [Pham, Simar, and Zelenyuk
  (2023)](https://doi.org/10.1287/opre.2022.2424); updated finite-sample/CLT
  evidence in
  [Zelenyuk and Zhao
  (2025)](https://doi.org/10.1017/S1365100525000094).
- **Evidence status:** planned/evidence only. Candidate
  *inference.productivity.aggregate.pham_simar_zelenyuk_2023* may be named
  now; the 2025 leaf remains unnamed until its exact supported operator and
  estimator are frozen. No implementation is claimed.
- **Failure:** Reusing the 1999 bootstrap because both outputs are called
  “Malmquist,” or attaching an aggregate interval without the source weighting
  and dependence contract.

## 3. How should operating conditions enter statistical analysis?

### `context.second_stage.simar_wilson_2007.algorithm1`

- **Economic question:** Under a common production technology, how are
  contextual variables conditionally associated with an estimated inefficiency
  measure?
- **Technology / estimator / inference:** First-stage DEA estimator under
  separability; truncated regression model for the inefficiency outcome;
  Algorithm 1's parametric bootstrap for second-stage inference.
- **Measure:** Regression coefficients and uncertainty, alongside unchanged
  first-stage scores.
- **RTS:** The first-stage RTS is explicit and fixed through the procedure.
- **Data / time:** Cross-sectional units with contextual covariates and the
  paper's iid/distributional assumptions; panels or clusters need a different
  inferential design.
- **Native score:** First-stage score and regression coefficients remain
  separate result objects.
- **Exact aliases:** None with naive Tobit/OLS, Algorithm 2, conditional DEA,
  or Fried's three-stage adjustment.
- **Distinct variants:** Alternative truncation parameterizations, Algorithm
  2, conditional-frontier estimators, and causal second-stage designs.
- **Domain:** Separability/common-technology interpretation, correct score
  orientation/transformation, support for covariates, and a defensible
  truncated-regression specification.
- **Failures:** Treating coefficients as causal without identification,
  plugging scores into ordinary regression with conventional standard errors,
  score-direction errors, and ignoring generated-dependent-variable
  uncertainty.
- **Solver form:** DEA fits + truncated maximum likelihood + parametric
  bootstrap.
- **Defining source:** [Simar and Wilson
  2007](https://doi.org/10.1016/j.jeconom.2005.07.009).
- **Evidence status:** primary-checked; registry-provisional/planned with no
  repository implementation.
- **Oracle:** candidate — published Monte Carlo and empirical material has been
  identified but not reproduced in automated repository tests.
- **Package recipe:** Planned explicit preset
  `context.second_stage.simar_wilson_2007.algorithm1`; do not expose only
  `second_stage="SW"`.
- **Book location:** **Documentation/source review only.** No current handbook placement.

### `context.second_stage.simar_wilson_2007.algorithm2`

- **Economic question:** How does the second-stage association change when the
  first-stage efficiency estimates are also bias corrected using the paper's
  double-bootstrap construction?
- **Technology / estimator / inference:** Same common first-stage technology;
  DEA estimator plus first bootstrap for bias correction, truncated
  regression, and second bootstrap for coefficient inference.
- **Measure:** Original and bias-corrected first-stage scores, regression
  coefficients, and bootstrap uncertainty.
- **RTS:** Explicit and held consistent across both bootstrap layers.
- **Data / time:** Same cross-sectional and distributional scope as the exact
  source algorithm.
- **Native score:** Original score is never overwritten; bias-corrected score
  and regression result are separately labeled.
- **Exact aliases:** None with Algorithm 1. Shared code does not make the
  estimands, number of bootstrap layers, or result contract identical.
- **Distinct variants:** Algorithm 1, alternative boundary bootstraps,
  conditional frontiers, and three-stage DEA--SFA--DEA.
- **Domain:** All first-stage bootstrap and truncated-regression conditions
  must hold.
- **Failures:** Reusing one random stream without nesting metadata, replacing
  original scores, insufficient inner/outer replication diagnostics, and
  applying the algorithm to unsupported measures.
- **Solver form:** Nested/repeated DEA and truncated-regression estimation with
  explicit inner and outer replication controls.
- **Defining source:** [Simar and Wilson
  2007](https://doi.org/10.1016/j.jeconom.2005.07.009).
- **Evidence status:** primary-checked; registry-provisional/planned with no
  repository implementation.
- **Oracle:** candidate — published Monte Carlo and empirical material has been
  identified but not reproduced in automated repository tests.
- **Package recipe:** Planned explicit preset
  `context.second_stage.simar_wilson_2007.algorithm2`.
- **Book location:** **Documentation/source review only.** No current handbook placement.

### `context.second_stage.banker_natarajan_2008.ols`

- **Economic question:** Under the paper's stochastic productivity model, how
  are observed operating conditions associated with latent productivity when
  managers face both one-sided inefficiency and two-sided random noise?
- **Technology / estimator / inference:** Banker--Natarajan's
  source-qualified DEA-based stochastic-frontier framework, first-stage DEA
  productivity estimator, and second-stage OLS procedure under the paper's
  consistency conditions.
- **Measure:** Paper-specified transformed productivity outcome, OLS
  coefficients for contextual variables, conventional or source-supported
  uncertainty, and the unchanged first-stage productivity results.
- **RTS:** The first-stage production technology and RTS are fixed by the
  source-compatible specification and retained in all reporting.
- **Data / time:** Cross-sectional observations satisfying the paper's
  independence and distributional conditions; in particular, contextual
  variables must meet the required relation to inputs, and panels or clusters
  require different theory.
- **Native score:** First-stage DEA productivity estimate and second-stage OLS
  coefficient vector remain separate objects with the dependent-variable
  transformation and sign convention stored.
- **Exact aliases:** None with naïve OLS on arbitrary DEA scores,
  Simar--Wilson Algorithm 1 or 2, Tobit by convenience, or conditional
  DEA/FDH.
- **Distinct variants:** The paper's OLS and maximum-likelihood branches,
  Simar--Wilson truncated-regression bootstraps, conditional-frontier
  estimators, separability tests, and causal contextual designs.
- **Domain:** The exact Banker--Natarajan data-generating process, independence
  restrictions, productivity transformation, distributional assumptions, and
  any prior sign restrictions must be declared and diagnostically assessed.
- **Failures:** Invoking the consistency result outside its assumptions,
  treating coefficients as causal, choosing OLS because it is convenient,
  reversing efficiency/inefficiency signs, using ordinary panel standard
  errors, and hiding first-stage estimation uncertainty.
- **Solver form:** First-stage DEA fits followed by source-specified OLS and
  diagnostic computation; an MLE branch is a separate preset.
- **Defining source:** [Banker and Natarajan
  2008](https://doi.org/10.1287/opre.1070.0460).
- **Evidence status:** primary-checked; registry-provisional/planned with no
  repository implementation.
- **Oracle:** candidate — the paper's Monte Carlo and empirical results have
  been identified but not reproduced in automated repository tests.
- **Package recipe:** Planned
  `context.second_stage.banker_natarajan_2008.ols`; a separately audited
  `.mle` leaf may share infrastructure but not inferential claims.
- **Book location:** **Documentation/source review only.** No current handbook placement.

### `estimator.conditional.dea` and `estimator.conditional.fdh`

- **Economic question:** Does the operating environment change the attainable
  production opportunities against which a unit should be compared?
- **Technology / estimator / inference:** Declared production technology;
  conditional DEA/FDH estimator using local contextual information; inference
  requires a separate conditional-frontier procedure.
- **Measure:** Conditional efficiency/distance and comparison with the
  unconditional estimate under a declared interpretation.
- **RTS:** Explicit; conditional weighting does not select RTS.
- **Data / time:** Quantities plus continuous/discrete contextual variables,
  kernel, metric, bandwidth, boundary correction, and support policy.
- **Native score:** Conditional base score plus effective local sample size,
  bandwidth, weights, and support diagnostics.
- **Exact aliases:** None with stratified DEA, categorical Banker--Morey,
  second-stage regression, metafrontier, or order-$m$.
- **Distinct variants:** Conditional DEA, conditional FDH, conditional
  order-$m$, mixed-data kernels, and separability tests.
- **Domain:** Adequate local support and a bandwidth rule fixed independently
  of favorable efficiency outcomes.
- **Failures:** Empty/local singleton neighborhoods, bandwidth overfit,
  boundary bias, incompatible contextual scales, and causal interpretation of
  a conditional association.
- **Solver form:** Kernel/local-weight construction plus repeated DEA/FDH
  frontier evaluation.
- **Defining source:** Probabilistic conditional frontier [Daraio and Simar
  2005](https://doi.org/10.1007/s11123-005-3042-8).
- **Evidence status:** primary-checked; registry-provisional/planned with no
  repository implementation.
- **Oracle:** candidate — a published illustration has been identified but not
  reproduced in automated repository tests.
- **Package recipe:** Planned `estimator.conditional.dea` and
  `estimator.conditional.fdh`; inference remains a separate composition axis.
- **Book location:** **Documentation/source review only.** No current handbook placement.

## 4. Are apparent leaders genuine best practice or influential extremes?

### `estimator.partial.order_m` — order-$m$ partial frontier

- **Economic question:** What performance is expected relative to the best of a
  random comparison group of size $m$, when full-frontier extremes would
  dominate the managerial story?
- **Technology / estimator / inference:** Maintained free-disposal production
  relation; order-$m$ partial-frontier estimator; inference is separate.
- **Measure:** Expected best attainable input/output performance or associated
  order-$m$ efficiency under the source's orientation.
- **RTS:** Not a simple CCR/BCC toggle; the probabilistic estimator and any
  convexity assumptions must be stated.
- **Data / time:** Cross-sectional sample and declared $m$, integration or
  Monte Carlo policy, random seed, and conditioning variables if used.
- **Native score:** Source-native order-$m$ score plus $m$, simulation
  error, and dominance/support diagnostics.
- **Exact aliases:** None with full FDH, leave-one-out DEA, trimmed DEA,
  super-efficiency, robust optimization, or a standard-error procedure.
- **Distinct variants:** Conditional order-$m$, order-$\alpha$, extreme
  quantile/frontier estimators, and influence diagnostics.
- **Domain:** Requires the source's dominance probabilities and support
  conditions; order-$m$ scores may follow a different boundedness convention
  from full-frontier scores.
- **Failures:** Calling the estimator “outlier-proof,” selecting $m$ to
  maximize favorable results, inadequate Monte Carlo draws, and interpreting
  it as inference around full DEA.
- **Solver form:** Dominance/probability computation and numerical integration
  or Monte Carlo simulation; not necessarily one DEA LP per unit.
- **Defining source:** [Cazals, Florens, and Simar
  2002](https://doi.org/10.1016/S0304-4076(01)00080-X).
- **Evidence status:** primary-checked; registry-provisional/planned with no
  repository implementation.
- **Oracle:** candidate — published illustrations have been identified but not
  reproduced in automated repository tests.
- **Package recipe:** Planned `estimator.partial.order_m`; order-$\alpha$
  is the separate source-qualified recipe below.
- **Book location:** **Documentation/source review only.** No current handbook placement.

### `estimator.partial.order_alpha.aragon_daouia_thomas_agnan_2005`

- **Economic question:** What high-performance conditional benchmark is
  appropriate when management wants a declared fraction of comparable
  observations to lie beyond the benchmark rather than letting the single
  most extreme observation determine the full frontier?
- **Technology / estimator / inference:** Maintained monotone production
  relation; Aragon--Daouia--Thomas-Agnan's conditional-quantile
  order-$\alpha$ partial-frontier estimator; the source's statistical theory
  is specific to that estimator.
- **Measure:** Conditional order-$\alpha$ frontier and associated
  input/output efficiency or distance under the source's orientation.
- **RTS:** Not a CCR/BCC switch. Shape, monotonicity, and any convexification
  are separate assumptions and must not be added silently.
- **Data / time:** Cross-sectional sample, conditioning quantities,
  $\alpha\in(0,1)$, empirical-quantile convention, support policy, and any
  smoothing/isotonization settings.
- **Native score:** Source-native order-$\alpha$ frontier/efficiency plus
  $\alpha$, effective dominance support, quantile convention, and any
  monotonicity diagnostic.
- **Exact aliases:** None with order-$m$, full FDH/DEA, ordinary quantile
  regression, trimmed DEA, super-efficiency, or a confidence bound.
- **Distinct variants:** Empirical versus smooth order-$\alpha$,
  multivariate conditional quantile frontiers, isotonized estimators,
  convexified order-$\alpha$, hyperbolic/directional order-$\alpha$, and
  conditional environmental extensions.
- **Domain:** The source's conditional distribution and support assumptions
  must hold. The partial frontier need not envelop every observation and
  should not be described as the full best-practice boundary.
- **Failures:** Choosing $\alpha$ after inspecting rankings, calling a
  partial frontier “outlier deletion,” assuming monotonicity or concavity not
  delivered by the estimator, quantile-tie ambiguity, sparse dominance
  support, and interpreting $\alpha$ as a confidence level.
- **Solver form:** Empirical conditional-distribution and quantile
  computation; smooth, isotonized, convexified, or directional variants add
  their own numerical procedures.
- **Defining source:** [Aragon, Daouia, and Thomas-Agnan
  2005](https://doi.org/10.1017/S0266466605050206).
- **Evidence status:** primary-checked; registry-provisional/planned with no
  repository implementation.
- **Oracle:** candidate — simulated and French post-office illustrations are
  available but have not been reproduced in automated repository tests.
- **Package recipe:** Planned
  `estimator.partial.order_alpha.aragon_daouia_thomas_agnan_2005`; later smooth,
  isotonized, convexified, or directional estimators require separate leaves.
- **Book location:** **Documentation/source review only.** No current handbook placement.

### Deterministic diagnostics

The current bounded package diagnostic
`analysis.reference_frequency.selected_plan` counts the reported active peer
edges strictly above the source result's `peer_tolerance` in one complete,
certified solver-selected plan from a static convex global cross-section.
Total reference frequency is the sum of self and other use; `reference_rate`
divides that total by the complete number of
evaluated organizations. It performs no refit and makes no higher-is-better,
alternate-optimum, global-reference-set, influence, outlier, deletion, or
sampling-inference claim.

The benchmark-importance/ranking lineage of
[Torgersen, Førsund, and Kittelsen
(1996)](https://doi.org/10.1007/BF00162048) and the reference-count discussion
in [Doyle and Green
(1995)](https://doi.org/10.1080/03155986.1995.11732281) provide historical
context, not an identity claim. In particular, the package diagnostic is not
Torgersen et al.'s full slack-adjusted peer-importance/ranking procedure.
Likewise, the global/minimum-face reference-set analysis of
[Mehdiloozad et al.
(2015)](https://doi.org/10.1016/j.ejor.2015.03.029) explains why one selected
peer plan cannot be relabeled a maximal or global reference set. The package
account is independently checked against a direct dictionary tally rather
than claiming reproduction of any numerical table in those papers.

### Influence, leave-one-out, and data-quality diagnostics

- **Economic question:** Which observations materially determine the frontier,
  and do they warrant data investigation rather than automatic deletion?
- **Technology / estimator / inference:** Repeated fits of the declared
  technology/estimator under a diagnostic exclusion policy; not sampling
  inference unless embedded in a separately justified procedure.
- **Measure:** Change in scores, targets, peers, frontier facets, or aggregate
  summaries after an observation or cluster is excluded.
- **RTS:** Inherited and held fixed.
- **Data / time:** Observation IDs, clusters, time dependence, and exclusion
  units must be declared.
- **Native score:** Baseline and exclusion-run results plus influence deltas;
  original results remain intact.
- **Exact aliases:** None with super-efficiency, jackknife variance estimation,
  order-$m$, or outlier deletion.
- **Distinct variants:** Single-case, cluster, period, frontier-facet, and
  robust-distance diagnostics.
- **Domain:** Exclusion must leave a viable reference set and preserve the
  research population being diagnosed.
- **Failures:** Empty reference sets, cascading infeasibility, deleting a
  legitimate best-practice unit because it is influential, and presenting a
  sensitivity diagnostic as a confidence interval.
- **Solver form:** Batched repeated frontier fits with reusable compiled
  matrices and explicit exclusion keys.
- **Defining source:** No single generic source is assigned here; executable
  diagnostics require a source or an explicitly package-defined diagnostic
  contract.
- **Evidence status:** registry-provisional; no single primary-source
  diagnostic contract has yet been selected.
- **Oracle:** not located — no certified numerical diagnostic example has been
  selected.
- **Package recipe:** Planned `diagnostics.influence`; reference exclusion is
  owned by a reusable reference policy, not duplicated in every model.
- **Book location:** **Documentation/source review only.** No current handbook placement.

### Planned deterministic CCR stability analysis

- **Planning question:** How much can declared coefficients or data change
  before a fitted CCR efficiency conclusion changes?
- **Technology / estimator / inference:** Source-qualified allowable-
  perturbation analysis for a fixed CCR model; it is a deterministic
  diagnostic, not a sampling procedure.
- **Eleven-axis placement:** $A$ owns the stability diagnostic and
  perturbation scope; $U$ remains none.
- **Equivalence boundary:** Level D versus bootstrap inference, robust
  optimization, and partial-frontier robustness.
- **Defining source:** [Seiford and Zhu
  (1998)](https://doi.org/10.1016/S0377-2217(97)00103-3); handbook synthesis
  [Zhu (2010)](https://doi.org/10.1007/978-1-4419-6151-8_3).
- **Evidence status:** planned/evidence only; the candidate
  *diagnostics.deterministic_stability.ccr.seiford_zhu_1998* requires an
  equation fixture and oracle before registration or implementation.
- **Failure:** Presenting a deterministic stability region as a confidence
  interval or an uncertainty-set guarantee.

## 5. What hypotheses can the frontier evidence test?

### `inference.tests.rts.simar_wilson_2002` — bootstrap returns-to-scale test

- **Economic question:** Is a CRS technology adequate, or does the evidence
  support one of the source's admissible alternative scale technologies?
- **Technology / estimator / inference:** Matched frontier estimators under the
  null and supported alternative RTS technologies; Simar--Wilson's
  source-qualified bootstrap test.
- **Measure:** Source-defined distance/efficiency contrast, bootstrap
  calibration, $p$-value, and all restricted/unrestricted component fits.
- **RTS:** The null and alternative are explicit fields; the procedure never
  infers RTS by relabeling a CRS/VRS score ratio.
- **Data / time:** Cross-sectional or dependence-aware samples consistent with
  the test theory.
- **Native score:** Test statistic and decision rule; individual efficiency
  scores remain supporting results.
- **Exact aliases:** None among an RTS label from a supporting hyperplane,
  Simar--Wilson's formal bootstrap test, and a scale-efficiency ratio.
- **Distinct variants:** Banker distributional tests, convexity tests,
  separability tests, group/technology-equality tests, and multiple-testing
  procedures. These remain leaves under the non-executable
  `inference.tests.structure` umbrella.
- **Domain:** The source's null/alternative estimators, DGP, nuisance
  parameters, and regularity conditions must be matched.
- **Failures:** Selecting the test after viewing scores, incompatible
  technologies under null/alternative, naive chi-square references, and
  treating failure to reject as proof of equality.
- **Solver form:** Repeated restricted/unrestricted frontier fits plus the
  source-specific calibration.
- **Defining source:** [Simar and Wilson
  2002](https://doi.org/10.1016/S0377-2217(01)00167-9); broader testing
  context [Banker
  1996](https://doi.org/10.1007/BF00157038).
- **Evidence status:** primary-checked; registry-provisional/planned with no
  repository implementation.
- **Oracle:** candidate — published examples have been identified but not
  reproduced in automated repository tests.
- **Package recipe:** Planned
  `inference.tests.rts.simar_wilson_2002` beneath non-executable procedure
  family `inference.tests.structure`.
- **Book location:** **Documentation/source review only.** No current handbook placement.

## 6. Is randomness part of the production problem itself?

### State-contingent and event-specific production

- **Economic question:** Which resource commitments and state-specific
  deliverables are technically attainable when management acts before a
  mutually exclusive state of nature is known?
- **Technology / estimator / inference:** A state-contingent production
  technology represents outputs as state-indexed commodities in an ex ante
  plan. Event-specific DEA instead uses an observed random condition to
  partition the state space and form event-relevant empirical comparisons.
  Neither construction is sampling inference by itself.
- **Measure:** A source-qualified input, output, technical, or environmental
  efficiency measure over the state-contingent or event-specific technology.
- **RTS:** Explicit in the empirical activity technology; state indexing does
  not select returns to scale.
- **Data / time:** Ex ante state-contingent outputs or an externally observed
  random condition that credibly identifies events, plus the timing of
  commitments and state realization. Probabilities and risk preferences are
  additional data only when an economic-choice analysis needs them.
- **Native score:** Source-native efficiency by state or across the declared
  state-contingent plan, accompanied by the state definition and any
  aggregation rule.
- **Exact aliases:** None between a state of nature, a calendar period, a
  dynamic carry-over state, a scenario in robust optimization, and the random
  error in a frontier estimator.
- **Distinct variants:** Elicited full state-contingent outputs;
  event-specific DEA; state-contingent environmental efficiency; conditional
  order-$m$ under production risk; stochastic-frontier mixtures.
- **Domain:** States must be mutually intelligible, commitments must precede
  realization as claimed, and state-specific quantities must share consistent
  economic units. An observed ex post outcome alone generally does not reveal
  the complete ex ante plan.
- **Failures:** Treating a poor realized state as managerial inefficiency,
  estimating an unobserved state plan without identification, attaching
  arbitrary probabilities, or relabeling panel periods as states of nature.
- **Solver form:** Source-specific activity-analysis LP for observed or
  elicited state-contingent quantities; event construction or conditional
  partial-frontier computation where required.
- **Defining source:** Event-specific DEA in
  [Chambers, Hailu, and Quiggin
  (2011)](https://doi.org/10.1111/j.1467-8489.2010.00517.x);
  technical and environmental state-contingent DEA in
  [Serra, Chambers, and Oude Lansink
  (2014)](https://doi.org/10.1016/j.ejor.2013.12.037).
- **Evidence status:** review-supported; the technology/estimator distinction
  is established, while executable leaves remain registry-provisional pending
  formulation and oracle audits.
- **Oracle:** not located — no published state-contingent or event-specific
  numerical example has been reproduced in repository tests.
- **Package recipe:** Registry-provisional state-contingent technology and
  event-specific estimator families; no public constructor or generic
  “stochastic DEA” alias is asserted.
- **Book location:** **Documentation/source review only.** No current handbook placement.

### `uncertainty.stochastic.chance_constrained` — Land--Lovell--Thore lineage

- **Economic question:** What performance or feasibility can be claimed when
  observed activities or frontier constraints are random and a decision maker
  accepts a declared probability of violation?
- **Technology / estimator / inference:** Probability-model-specific random
  production set or chance-constrained technology; its own estimator; this is
  not bootstrap inference about deterministic DEA.
- **Measure:** Source-specific stochastic efficiency/dominance quantity and
  achieved/reported reliability level.
- **RTS:** Explicit within the chance-constrained technology.
- **Data / time:** Random-variable/distribution parameters, dependence
  structure, estimation sample, and risk tolerance.
- **Native score:** Stochastic efficiency plus violation probability,
  distributional assumptions, and deterministic-equivalent diagnostics.
- **Exact aliases:** A deterministic equivalent is an exact computational form
  only under its stated distribution and dependence assumptions.
- **Distinct variants:** Random deviations, measurement-error DEA, stochastic
  production possibility sets, chance-constrained congestion, SFA, and
  distributionally robust optimization.
- **Domain:** The selected probability model and risk level must be
  empirically and managerially defensible.
- **Failures:** Unknown covariance, invalid normality/independence assumptions,
  numerically unstable quantiles, declaring a chance constraint “confidence,”
  and conflating random inefficiency with random noise.
- **Solver form:** Chance-constrained program or a proven deterministic
  equivalent; may be LP, SOCP, or nonlinear.
- **Defining source:** [Land, Lovell, and Thore
  1993](https://doi.org/10.1002/mde.4090140607); taxonomy/review
  [Olesen and Petersen
  2016](https://doi.org/10.1016/j.ejor.2015.07.058).
- **Evidence status:** primary-checked and review-supported;
  registry-provisional/planned with no repository implementation.
- **Oracle:** candidate — literature examples have been identified but not
  reproduced in automated repository tests.
- **Package recipe:** Planned family
  `uncertainty.stochastic.chance_constrained`, with probability model, risk
  tolerance, and exact source formulation mandatory. A Land--Lovell--Thore
  preset receives a separate canonical leaf only after its formulation and
  oracle are certified.
- **Book location:** **Documentation/source review only.** No current handbook placement.

### Random deviations, measurement error, and stochastic production sets

- **Economic question:** Is observed departure from a frontier caused by
  inefficiency, random noise, measurement error, or a genuinely random
  production opportunity set?
- **Technology / estimator / inference:** Source-specific stochastic mechanism
  and estimator; inference is then conditional on that mechanism.
- **Measure:** Mechanism-specific efficiency, latent frontier, noise/error
  components, or probability of feasibility.
- **RTS:** Explicit and linked to the stochastic frontier/production-set
  definition.
- **Data / time:** Replication, variance/covariance information, distributional
  assumptions, and dependence structure.
- **Native score:** Efficiency and stochastic/noise quantities remain separate.
- **Exact aliases:** None among stochastic DEA, SFA, StoNED, measurement-error
  DEA, CNLS, or a bootstrap of deterministic DEA.
- **Distinct variants:** The three broad stochastic DEA directions reviewed by
  Olesen--Petersen: random deviations, integrated noise/error, and stochastic
  production possibility sets.
- **Domain:** Identifiability of inefficiency versus noise and adequate data
  for distributional parameters.
- **Failures:** Using cross-sectional residuals to identify both noise and
  inefficiency without assumptions, hidden likelihood choices, and
  overclaiming nonparametric status when a parametric error law drives the
  result.
- **Solver form:** Source dependent: LP/QP, likelihood, simulation, or
  stochastic programming.
- **Defining source:** [Olesen and Petersen
  2016](https://doi.org/10.1016/j.ejor.2015.07.058).
- **Evidence status:** review-supported at family level; exact
  primary-source leaves remain registry-provisional.
- **Oracle:** not located — no exact executable leaf and certified numerical
  example have yet been selected.
- **Package recipe:** Planned separate families
  `uncertainty.stochastic.random_deviation`,
  `uncertainty.stochastic.measurement_error`, and
  `uncertainty.stochastic.pps`; neighboring SFA/CNLS/StoNED methods should be
  integrations or clearly labeled neighbors, not renamed DEA presets.
- **Book location:** **Documentation/source review only.** No current handbook placement.

## 7. What if observations are imprecise rather than random?

### `uncertainty.interval_idea` — imprecise/interval DEA

- **Economic question:** What efficiency conclusions follow when inputs,
  outputs, or valuation information are known only through bounds, orders, or
  ratios?
- **Technology / estimator / inference:** Information-set-specific IDEA
  technology/estimator; no sampling inference unless separately composed.
- **Measure:** Lower/upper or classification result under the exact IDEA
  formulation.
- **RTS:** Explicit and compatible with interval/order information.
- **Data / time:** Closed/open bounds, order relations, ratio constraints, and
  provenance of imprecision; not a probability distribution.
- **Native score:** Source-specific bounds/classification plus the witness data
  realization or active information constraints.
- **Exact aliases:** None between interval uncertainty, missing data, fuzzy
  membership, chance constraints, and robust optimization. AR-IDEA is not
  ordinary assurance-region DEA merely because it uses AR constraints.
- **Distinct variants:** IDEA, AR-IDEA, interval efficiency bounds,
  possibility sets, robust uncertain DEA, and imprecise prices.
- **Domain:** Information constraints must be mutually consistent and preserve
  economic roles/units.
- **Failures:** Inconsistent intervals/orders, optimistic selection of data
  values without reporting it, treating bounds as confidence intervals, and
  filling missing values with endpoints.
- **Solver form:** LP, fractional program, or a pair/family of optimization
  problems depending on the exact information set.
- **Defining source:** [Cooper, Park, and Yu
  1999](https://doi.org/10.1287/mnsc.45.4.597).
- **Evidence status:** primary-checked; registry-provisional/planned with no
  repository implementation.
- **Oracle:** candidate — literature examples have been identified but not
  reproduced in automated repository tests.
- **Package recipe:** Planned `uncertainty.interval_idea`, composed with the
  semantic role `data.interval_imprecise`; exact IDEA and AR-IDEA leaves stay
  source qualified.
- **Book location:** **Documentation/source review only.** No current handbook placement.

### `uncertainty.fuzzy` — fuzzy DEA

- **Economic question:** How should performance be described when quantities
  or judgments have graded membership/possibility rather than probabilistic or
  interval-only meaning?
- **Technology / estimator / inference:** Membership/possibility-specific
  technology and estimator; not frequentist sampling inference.
- **Measure:** Possibility/necessity, alpha-cut efficiency interval, fuzzy
  ranking, or another source-native fuzzy quantity.
- **RTS:** Explicit for every alpha-cut or equivalent deterministic program.
- **Data / time:** Membership functions, elicitation source, alpha levels, and
  aggregation/ranking policy.
- **Native score:** Full fuzzy/alpha-cut result plus any defuzzified display;
  a crisp ranking cannot replace the underlying membership result.
- **Exact aliases:** Alpha-cut deterministic programs may be exact
  computational representations of one fuzzy model; fuzzy DEA is not interval
  DEA merely because alpha cuts are intervals.
- **Distinct variants:** Tolerance, possibility, credibility, fuzzy ranking,
  fuzzy SBM, and fuzzy network/environmental models.
- **Domain:** Valid membership functions and a defensible decision
  interpretation.
- **Failures:** Arbitrary membership functions, hidden defuzzification,
  incomparable fuzzy rankings, label “fuzzy” applied to ordinary measurement
  error, and multiplying variants without primary-source validation.
- **Solver form:** A family of LPs/nonlinear programs over alpha levels or the
  exact possibility/credibility formulation.
- **Defining source:** Taxonomy and review [Hatami-Marbini, Emrouznejad, and
  Tavana 2011](https://doi.org/10.1016/j.ejor.2011.02.001). An executable leaf
  must additionally cite its primary formulation.
- **Evidence status:** review-supported at family level; exact primary-source
  package leaves remain registry-provisional.
- **Oracle:** not located — no exact fuzzy formulation and certified numerical
  example have yet been selected.
- **Package recipe:** Planned family `uncertainty.fuzzy`; no generic solver
  until a primary formulation, membership contract, and oracle are selected.
- **Book location:** **Documentation/source review only.** No current handbook placement.

## 8. What performance is guaranteed over an explicit uncertainty set?

### `uncertainty.robust_polyhedral` and `uncertainty.robust_conic`

- **Economic question:** What performance is guaranteed under the worst
  realization in an explicit uncertainty set, or how much uncertainty would
  be needed to alter a unit's classification?
- **Technology / estimator / inference:** Robust counterpart of a declared DEA
  technology/measure; estimator over uncertain observations; no sampling
  inference unless an additional probability calibration is justified.
- **Measure:** Worst-case/best-case robust efficiency, radius to efficiency, or
  source-native uncertainty budget result.
- **RTS:** Explicit and robustified consistently.
- **Data / time:** Nominal quantities plus box, polyhedral, budgeted,
  ellipsoidal, or conic uncertainty set with provenance/calibration.
- **Native score:** Robust score plus uncertainty-set type, radius/budget,
  active worst-case realization, and nominal score.
- **Exact aliases:** A conic/linear robust counterpart is exact only for the
  declared uncertainty set and duality conditions.
- **Distinct variants:** Optimistic versus pessimistic uncertain DEA,
  box/polyhedral/budgeted robust models, ellipsoidal/conic models,
  distributionally robust DEA, chance constraints, and deterministic
  sensitivity analysis.
- **Domain:** Uncertainty sets must respect signs, units, joint feasibility,
  and economic roles.
- **Failures:** An uncertainty set that lets a unit choose favorable data,
  monotone “improvement with uncertainty” misreported as robustness, arbitrary
  radius calibration, infeasible worst cases, and confusing guaranteed
  performance with a confidence level.
- **Solver form:** LP for many polyhedral sets; SOCP/conic or iterative
  first-order algorithms for ellipsoidal/source-specific models.
- **Defining source:** Uncertain/robust DEA formulation [Ehrgott, Holder, and
  Nohadani
  2018](https://doi.org/10.1016/j.ejor.2018.01.005); field review
  [Peykani et al.
  2020](https://doi.org/10.1111/exsy.12534).
- **Evidence status:** primary-checked and review-supported;
  registry-provisional/planned with no repository implementation.
- **Oracle:** candidate — literature case studies have been identified but not
  reproduced in automated repository tests.
- **Package recipe:** Planned `uncertainty.robust_polyhedral` and optional
  `uncertainty.robust_conic`; backend capability is explicit.
- **Book location:** **Documentation/source review only.** No current handbook placement.

### Distributionally robust and Bayesian frontier procedures

- **Economic question:** What conclusions follow when the probability
  distribution itself is uncertain, or when efficiency is represented by a
  posterior distribution under an explicit likelihood and prior?
- **Technology / estimator / inference:** Distributionally robust optimization
  uses an ambiguity set over distributions inside the decision problem;
  Bayesian frontier procedures use a likelihood/prior to obtain posterior
  statements. Neither is a synonym for bootstrap DEA.
- **Measure:** Worst-case expected/source-native robust quantity or posterior
  efficiency distribution.
- **RTS:** Explicit in the underlying frontier/technology.
- **Data / time:** Ambiguity-set calibration or likelihood, prior, dependence,
  and convergence diagnostics.
- **Native score:** Full ambiguity/posterior result plus any summary; retain
  nominal estimates and prior/calibration metadata.
- **Exact aliases:** None with chance-constrained, robust-set, fuzzy,
  bootstrap, SFA, or deterministic DEA.
- **Distinct variants:** Wasserstein/moment ambiguity sets, Bayesian
  nonparametric/frontier models, Bayesian SFA, and posterior predictive
  efficiency.
- **Domain:** Entirely formulation specific; identifiability and computational
  convergence are mandatory.
- **Failures:** Calling a prior-free resampling method Bayesian, using an
  ambiguity radius without calibration, hiding prior sensitivity, and
  presenting posterior credibility as frequentist coverage.
- **Solver form:** Conic/large-scale robust optimization, MCMC, variational
  inference, or other source-specific computation.
- **Defining source:** No canonical executable DEA formulation is selected in
  this review. These remain research families pending a primary-source,
  estimand, and oracle audit.
- **Evidence status:** registry-provisional research scope; no canonical
  primary-source executable leaf or repository implementation is asserted.
- **Oracle:** not located — no certified numerical example has been selected.
- **Package recipe:** `uncertainty.distributionally_robust` and
  `inference.bayesian_dea` remain reader-facing research-only branches.
  Neither receives a public constructor until one source-qualified executable
  leaf and validation contract are frozen.
- **Book location:** **Documentation/source review only.** No current handbook placement.

## 9. Dependence, computation, and reproducibility requirements

### Spatial benchmark, conditioning, spillover, and inference mechanisms

- **Economic question:** Does location determine who is a credible comparator,
  alter the opportunities available to an organization, transmit a productive
  spillover from neighbors, or only create dependence in the statistical
  evidence?
- **Technology / estimator / inference:** Four separate possibilities:
  geographic eligibility restricts the comparison population; a spatial
  condition enters a conditional frontier; an actual cross-unit spillover
  changes the production graph or technology; and spatial dependence changes
  estimator or inference assumptions.
- **Measure:** Inherited from the selected production technology. Spatial
  coordinates or weights do not define a technical-efficiency score by
  themselves.
- **RTS:** Explicit in every local, conditional, or spillover technology.
- **Data / time:** Geocoded organizations, a defensible distance or adjacency
  relation, temporal alignment, and substantive evidence about whether
  proximity means comparability, context, or productive interaction.
- **Native score:** Base efficiency plus the spatial eligibility,
  conditioning, graph, or dependence specification and sensitivity to its
  tuning choices.
- **Exact aliases:** None among local peers, kernel conditioning, physical
  spillovers, a spatial lag of estimated scores, and spatially dependent
  resampling.
- **Distinct variants:** Semivariogram-selected local peers; conditional
  spatial frontiers; network/spillover technologies; spatial second-stage
  models; spatial block or subsampling inference; location/accessibility DEA.
- **Domain:** Sufficient spatial support, non-arbitrary neighborhood
  construction, comparable units within neighborhoods, and estimator-specific
  dependence assumptions.
- **Failures:** Choosing neighbors only because they improve scores, interpreting
  correlation as a production spillover, reusing iid inference, treating a
  spatial weight matrix as causal structure, and concealing weak local sample
  support.
- **Solver form:** Reference-population filtering or conditional-frontier
  estimation for the reviewed nonparametric designs; explicit coupled
  constraints for a true spillover technology; dependence-aware repeated
  estimation only where theory supports it.
- **Defining source:** Local spatial peers in
  [Vidoli and Canello
  (2016)](https://doi.org/10.1016/j.ejor.2015.10.050);
  spatially conditioned nonparametric frontier in
  [Ramajo, Márquez, and Hewings
  (2024)](https://doi.org/10.1111/grow.12711).
- **Evidence status:** review-supported for the mechanism boundary and the two
  cited designs; spillover technologies and dependence-specific inferential
  leaves remain registry-provisional.
- **Oracle:** not located — no spatial numerical example has been certified in
  repository tests.
- **Package recipe:** Separate registry-provisional policies or estimators for
  spatial population eligibility and spatial conditioning; a physical
  spillover requires a separately audited graph technology, and no generic
  spatial option is asserted.
- **Book location:** **Documentation/source review only.** No current handbook placement.

### Dependence-aware resampling and subsampling

- **Economic question:** How should uncertainty be assessed when observations
  are clustered, spatially related, serially dependent, or repeatedly observed
  over time?
- **Technology / estimator / inference:** Any supported base technology and
  estimator; dependence-specific block/cluster/subsampling inference.
- **Measure:** Source-qualified standard error, interval, or hypothesis result
  with effective sample and block diagnostics.
- **RTS:** Inherited and fixed through all resamples.
- **Data / time:** Cluster IDs, panel IDs, time order, spatial graph, missing
  waves, and dependence assumptions.
- **Native score:** Base result plus resampling-unit, block-length, coverage,
  and replication diagnostics.
- **Exact aliases:** None between iid bootstrap, cluster bootstrap, block
  bootstrap, subsampling, and cross-sectional leave-one-out.
- **Distinct variants:** Moving/stationary blocks, cluster resampling,
  dependence-aware subsampling, and source-qualified network inference.
- **Domain:** Requires enough independent clusters/blocks and theory for the
  fitted boundary estimator.
- **Failures:** Resampling rows from a panel as iid, breaking DMU time paths,
  resampling network nodes independently, too few clusters, and using a block
  scheme merely because it is computationally convenient.
- **Solver form:** Batched repeated estimation with deterministic seed streams,
  resumable state, and parallelism that does not alter results.
- **Defining source:** No generic procedure is selected. Each implemented
  dependence design must cite estimator-specific theory; the existence of
  subsampling for one setting does not validate another.
- **Evidence status:** registry-provisional / next-version planning umbrella;
  estimator-specific dependence-aware theory and an executable leaf have not
  yet been selected.
- **Oracle:** not located — no certified numerical example has been selected.
- **Package recipe:** `inference.subsampling` is a non-executable namespace
  umbrella. Every future executable leaf must receive a source-qualified ID
  that binds one estimator, measure, sampling design, and dependence structure.
  Generic parallel execution belongs to infrastructure, not the inferential
  ID.
- **Book location:** **Documentation/source review only.** No current handbook placement.

## 10. Decisions fixed by this review

1. The technology--estimator--inference triad is mandatory in every statistical
   result. A deterministic LP, a partial frontier, and a bootstrap are not
   three interchangeable “models.”
2. `inference.bootstrap.frontier_efficiency.simar_wilson_1998`,
   `inference.bootstrap.productivity.simar_wilson_1999`,
   `inference.tests.rts.simar_wilson_2002`,
   `inference.bootstrap.directional_distance.simar_vanhems_wilson_2012`,
   and `context.second_stage.simar_wilson_2007.algorithm1` /
   `context.second_stage.simar_wilson_2007.algorithm2` remain distinct
   source-qualified recipes.
3. A valid frontier bootstrap is not naive row resampling. Unsupported
   estimators fail closed rather than receiving plausible-looking intervals.
4. Order-$m$ and order-$\alpha$ are partial-frontier estimators, not robust
   standard errors and not generic outlier deletion.
5. Sampling inference, data/measurement uncertainty, state-contingent
   production risk, chance-constrained technology, robust scenarios,
   interval information, fuzzy membership, dependence, distributional
   ambiguity, and Bayesian posterior analysis make different claims and must
   retain separate result contracts.
6. Published examples are not repository oracles until their data,
   parameters, score conventions, and numerical outputs are reproduced in
   automated tests.
7. Banker--Natarajan DEA--OLS, Simar--Wilson truncated-regression bootstraps,
   and conditional DEA/FDH have different data-generating processes,
   estimands, and consistency claims.
8. A state of nature is not a calendar period or carry-over stock. An
   event-specific estimator is not a bootstrap.
9. Spatially eligible peers, spatial conditioning, physical production
   spillovers, and dependence-aware inference belong to different layers and
   cannot share one unqualified spatial-DEA flag.
10. This review authorizes no current-edition inferential API or Handbook
    route. Every future executable leaf must close its source protocol,
    independent numerical oracle, and typed result/failure contract first.
