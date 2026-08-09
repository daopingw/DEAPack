# DEAPack property and compatibility contract

This document prevents a shared solver kernel from becoming a claim that every
technology, measure, data domain, and downstream analysis can be combined.
It is normative for model registration, public validation, and result
metadata.

## 1. Fail-closed rule

Compatibility is directed and versioned. A composition is permitted only when
the registry says `supported` or when a source-qualified validator establishes
its conditions. Missing evidence means `under_audit`, not “probably
supported.”

The public vocabulary is:

| Status | Meaning |
|---|---|
| `supported` | theory, implementation, and property tests cover the stated domain |
| `conditional` | supported only when recorded conditions hold |
| `unsupported` | the combination contradicts the model definition or result meaning |
| `under_audit` | plausible or published in some form, but not yet certified for this implementation |
| `not_applicable` | the property or downstream operator has no coherent role for this result |

An API must never turn `under_audit` into a silent default.

## 2. Property profile required for every executable leaf

Each executable method or preset declares:

1. **data domain** — finite/nonnegative/strictly positive/signed values,
   admissible zeros, categorical or integer semantics, and denominator/log
   conditions;
2. **unit behavior** — whether independent positive rescaling of each factor
   leaves the score unchanged, and whether directions, prices, weights, or
   material coefficients must co-transform;
3. **translation behavior** — which common or variable-specific shifts, RTS,
   directions, and normalization populations preserve the score;
4. **monotonicity and indication** — what worsening an input/output can do to
   the score and whether the efficient value identifies radial, directional,
   weak, or Pareto--Koopmans efficiency;
5. **target guarantee** — whether targets are feasible, weakly efficient,
   strongly efficient, closest/furthest, or dependent on a secondary phase;
6. **technology/reference compatibility** — convexity, RTS, disposal,
   reference membership, self-exclusion, and graph/link requirements;
7. **operator compatibility** — supported scale, economic, productivity,
   environmental, network, decision, and inference operators;
8. **numerical contract** — solver class, tolerance semantics, multiple-optimum
   policy, and known infeasibility/degeneracy conditions.

These fields describe the actual implementation. A property stated for one
leaf is not inherited by its umbrella family.

## 3. Initial audited profile of implemented static leaves

This table is deliberately conservative. “Conditional” points to the
conditions that must appear in the expanded specification and tests.

| Method | Current data domain | Independent unit changes | Translation | Efficient-value meaning | Strong target |
|---|---|---|---|---|---|
| `static.radial` | nonnegative; positive aggregate input/output as required by orientation | supported | unsupported in general | radial efficiency only | conditional on the slack refinement |
| `static.radial.fdh` | nonnegative; positive aggregate input and output | supported | unsupported in general | radial efficiency on a non-convex hull | conditional on the observed-peer slack refinement |
| `static.additive` | nonnegative with positive observation-level input/output aggregates | conditional on co-transforming declared slack weights; the LP and strong-status tolerance use evaluated-account scales | conditional on VRS and shifts that remain in the public domain | zero unit-weight aggregate slack has an analytical Pareto--Koopmans certificate only for the classic VRS/self-inclusive cross-section; other weights/RTS/reference policies are package extensions | exact source-fixture target certified for the classic profile; strictly positive configurable weights retain a solver-selected strong-target property without inheriting the 1985 source identity |
| `static.ram` | finite signed resource/desirable-service coordinates under one self-inclusive VRS cross section; the source zero-range omission/zero-slack rule is implemented equivalently under the matched range/reference population; a global panel is a package extension | supported for independent positive factor rescaling under the unchanged comparison population | supported for common coordinate translations under the VRS identity and unchanged comparison population | source-certified score one means every recognized resource excess and desirable-service shortfall is zero; it is not a price, cost, welfare, or causal statement | exact positive-range fixture certifies a solver-selected strong target and peer; a separate invariant test closes zero-range equivalence and postsolve account checks |
| `static.bam` | nonnegative with positive aggregate input/output and one frozen global bound/reference population | supported for independent positive factor rescaling | unsupported across the public four-RTS leaf | score one means zero normalized shortfall under the bounded BAM programme | feasible solver-selected target; no claim beyond the declared one-sided bounds |
| `static.sbm.input.tone2001` | strictly positive input and output denominators | supported | unsupported in general | score one certifies zero normalized input slack only; generic strong efficiency is not certified | output-side slack and target are solver-selected; strong target requires a compatible completion protocol |
| `static.sbm.output.tone2001` | strictly positive input and output denominators | supported | unsupported in general | score one certifies zero normalized output slack only; generic strong efficiency is not certified | input-side slack and target are solver-selected; strong target requires a compatible completion protocol |
| `static.sbm.nonoriented.tone2001` | strictly positive input and output denominators | supported | unsupported in general | zero normalized input and output slacks under the fitted technology | conditional on the exact SBM and alternate-optimum formulation |
| `static.directional_distance` | nonnegative in the current public compiler | conditional on co-scaling directions | conditional on direction and technology translation | no further improvement along the declared direction | conditional on the slack refinement |
| `static.generalized_distance.chavas_cox` | nonnegative with positive aggregate input/output; structural zeros require an eligible reference activity that honors zero-input commitments and supplies every required positive output | supported for independent positive factor rescaling; score and row-scaled target selection are invariant | unsupported in general | no stronger multiplicative proportional contract at the declared $\alpha$ | conditional on the row-scaled slack completion; contract, score-stage activity, and completed target remain distinct |
| `static.multiplicative` | ordinary inputs and desirable outputs must be strictly positive; the 1982 source preset further requires every quantity to exceed one and fixes the exponent floor at one; undesirable outputs are excluded | conditional: independent positive coordinate rescaling is supported by the 1983 invariant preset and unsupported by the 1982 original preset | unsupported for additive shifts of physical quantities | score one means every source-native input/output log slack is zero under the selected log technology; it is not a price, profit, elasticity, or causal statement | one solver-selected optimal log-space target; 1983 targets are geometric peer combinations and 1982 targets are log-conic products; log targets remain authoritative if an original-unit transform exceeds float range |

Environmental leaves additionally declare bad-output treatment, null
jointness, pollution-generating inputs, and material/costly-disposal
restrictions. Productivity leaves inherit only the properties certified for
all component tasks and must also certify direction comparability, cross-period
feasibility, panel matching, and the decomposition identity.

### 3.1 Deferred short-run physical-capacity development profile

The row below documents a review-supported internal reconstruction so that
future source work does not lose its intended economic distinctions. The
defining 1989 article has not been equation-frozen and no independent
source-level numerical oracle is available. Consequently the identifier is a
non-public prototype, the row is not a compatibility guarantee, and every
field remains provisional until a next-version source audit closes.

| Deferred prototype | Provisional data and technology domain | Provisional account | Interpretation boundary under review |
|---|---|---|---|
| `analysis.capacity.physical.fare_grosskopf_kokkelenberg_1989` (`deferred_to_next_version`; not in the public API) | reconstructed nonnegative desirable-output profile with a nonempty, disjoint, exhaustive fixed/variable input partition, CRS convex technology, and a matched comparison population | candidate all-input factor $\phi^T$, fixed-input factor $\phi^C$, and the provisional identity $CU^{obs}=TE^O CU^{adj}$ | property tests can examine internal consistency, but they do not establish the defining-paper formulation, a source-native target, or any demand, staffing, economic-capacity, MPSS, congestion, or investment conclusion |

### 3.2 Implemented whole-template replication leaf

This public leaf changes the empirical opportunity set itself. It therefore
remains separate from both ordinary FDH and the continuously divisible CRS
technology even though the three can be compared through nesting checks.

| Method | Data and technology domain | Native account | Target and interpretation guarantee |
|---|---|---|---|
| `static.radial.frh` | nonnegative quantities; full empirical free-replicability hull; one common technology for both orientations; nonnegative integer reference-template counts; ordinary free disposal; no generic RTS switch | input contraction $\theta$ or output expansion $\phi$, integer replication counts, total replications, active templates, disposal residuals, solver status, MIP gap, and integer-optimum certification | radial plan plus one solver-selected integer reference activity; no claim that the activity is unique, that generic strong efficiency is established without completion, or that observed quantities themselves must be integer; FDH, bounded replication, integer-valued DEA, and additive-slack performance remain separate |

### 3.3 Implemented environmental general-network radial leaf

| Method | Data and technology domain | Native account | Target and interpretation guarantee |
|---|---|---|---|
| `network.environmental.weak_activity_specific.kalhor_kazemi_matin_2018` | finite nonnegative process quantities; explicit input, desirable-output, undesirable-output, and ordinary-intermediate economic accounts; for every declared producer process by desirable/undesirable product pair, at least one DMU has a positive final part, without pooling support across producers; corrected activity-specific $\alpha/\beta$ network technology; the VRS primary programme and CRS published oracle are reproduced, while source-described NIRS/NDRS restrictions have package-verification evidence but no claimed published numerical reproduction | one input-radial system factor $h$, process-specific active and complementary intensities, final account targets, and internal supply/requirement accounts | the selected primary plan is certified in the source network technology and rebuilt from unthresholded intensities; score one certifies radial system efficiency only, not process efficiency or Pareto--Koopmans efficiency; unit invariance requires all process-specific columns in one economic product account to be rescaled together; the DDF leaf and Spanish-airport data/result replay remain `deferred_to_next_version` |

### 3.4 Implemented Tone--Tsutsui static network-SBM leaf

| Method | Data and technology domain | Native account | Target and interpretation guarantee |
|---|---|---|---|
| `network.sbm.tone_tsutsui_2009` | strictly positive external and link quantities on one declared connected graph; source CRS or process-specific VRS; every link explicitly classified as fixed, free, as-input, or as-output; as-input is valid only with input orientation, as-output only with output orientation, and neither supplies a non-oriented accountable-link formula | higher-is-better orientation-specific system and process SBM accounts with exogenous nonnegative division weights summing to one; fixed/free links change feasibility without link slacks, while equation (26) counts an incoming slack once in the recipient input dimension and equation (27) counts an outgoing slack once in the supplier output dimension | every returned link target satisfies supplier--recipient continuity; fixed targets reproduce observation, free targets are jointly selected, and accountable targets additionally satisfy the named owner's slack balance; process accounts, slacks, peers, and targets are solver-selected attributions unless uniqueness is separately established; independent positive rescaling of each complete external or link variable preserves scores |

## 4. Initial audited profile of implemented economic leaves

Prices are valuation information, not production quantities or DEA
multipliers. The first executable economic slice is intentionally narrow:

| Method | Quantity and price domain | Technology/reference | Native result | Target and decomposition guarantee |
|---|---|---|---|---|
| `economic.cost` | nonnegative quantities with positive aggregate input/output; complete, finite, strictly positive input prices aligned by exact names and observation keys | convex CRS or VRS; every implemented reference policy; external references may be infeasible or yield a ratio above one | $CE=C^*/C_o$, higher is better; no clipping outside self-inclusive appraisal | one solver-selected cost-minimizing activity; target uniqueness unknown; input changes are economic choices, not technical slacks |
| `analysis.allocative_decomposition.cost_input_radial` | the cost domain above and a positive input-radial technical score | cost and technical components are fitted internally with identical data, RTS, reference, solver policy, and input orientation | $AE^C=CE/TE^I$, higher is better | records and tests $CE=TE^I AE^C$; refuses unmatched user-supplied component results |
| `economic.revenue` | nonnegative quantities with positive observed desirable output; complete, finite, strictly positive output prices aligned by exact names and observation keys | convex CRS or VRS; every implemented reference policy; zero-input positive-output activities are rejected by the current public domain; external references may be infeasible, yield zero maximum revenue, or yield a ratio above one | $RE=R_o/R_o^*$, higher is better; native expansion $R_o^*/R_o$ retained; no clipping outside self-inclusive appraisal | one solver-selected revenue-maximizing activity; target uniqueness unknown; unused input capacity and output-mix changes are economic choices, not technical slacks |
| `analysis.allocative_decomposition.revenue_output_radial` | the revenue domain above, positive maximum revenue, and a positive output-radial expansion factor | revenue and technical components are fitted internally with identical data, RTS, reference, solver policy, and output orientation | $AE^R=RE/TE^O$, with $TE^O=1/\phi$, higher is better | records and tests $RE=TE^O AE^R$; distinguishes the radial plan from the revenue-maximizing activity and fails closed for invalid denominators |
| `economic.profit.maximum` | nonnegative quantities; complete, finite, strictly positive aligned input and desirable-output prices; zero and negative observed/maximum profit are valid | finite VRS convex reference simplex only; shutdown excluded; external-reference monetary gaps retained but the efficiency score fails closed | raw $G^\Pi=\Pi^*-\Pi_o$, lower is better; no profit ratio or generic efficiency transform | one solver-selected profit-maximizing activity; target uniqueness unknown; a self-inclusive zero gap certifies Pareto--Koopmans efficiency under strictly positive prices, while a positive gap does not certify technical inefficiency |
| `economic.nerlovian.ccf1998` | the profit domain above plus nonnegative input-contraction/output-expansion directions, not both zero, with $\nu=w^\top g^x+p^\top g^y$ above tolerance | profit and DDF components share data, finite VRS technology, reference, solver policy, and direction; DDF phase one certifies reference membership | $NI=(\Pi^*-\Pi_o)/\nu=D_{\mathcal T}+AI^N$, lower is better; raw gap and all normalized components retained separately | profit-maximizing, direct directional, and slack-completed activities remain distinct; identity residual and residual-slack status are reported; no arbitrary $1/(1+NI)$ transform |
| `economic.profitability.return_to_dollar` | nonnegative quantities with positive aggregate input/output; complete, finite, strictly positive aligned input and desirable-output prices; every evaluated and candidate cost/revenue exceeds the denominator tolerance | ordinary convex CRS or VRS and every implemented reference policy; the maximum ratio is RTS-invariant on this domain; external-reference scores are retained unclipped | $PE=(R_o/C_o)/\max_j(R_j/C_j)$, higher is better; `return_to_dollar` is the observed ratio, not the relative score or a profit ratio | exact extreme-ratio kernel; VRS returns the selected reference plan, CRS scales it to observed cost; ratio ties and scale non-uniqueness are reported; the value leaf itself emits no GDF components or fabricated duals |
| `analysis.allocative_decomposition.profitability_gdf.zofio_prieto_2006` | intersection of the return-to-dollar and GDF domains; complete strictly positive aligned input/output prices and $\alpha\in[0,1]$ | internally matched ordinary CRS and VRS convex technologies, data, reference policy, price regime, solver, $\alpha$, and tolerances | $AE_{GDF}=PE/TE^{CRS}_{GDF}$, higher is better, with $SE_{GDF}=TE^{CRS}_{GDF}/TE^{VRS}_{GDF}$ | records $PE=TE^{CRS}_{GDF}AE_{GDF}=TE^{VRS}_{GDF}SE_{GDF}AE_{GDF}$; value, CRS-GDF, and VRS-GDF targets remain separate; generic Pareto--Koopmans status is missing |

Common positive scaling of all relevant prices changes monetary values but
not cost/revenue/profitability efficiency, Nerlovian components, or the
selected optimum. A priced quantity-unit change is permitted only when its
supplied price is inversely converted.
Panel monetary analysis requires an explicit currency and base period;
DEAPack does not silently deflate, convert, or impute. Undesirable outputs,
incomplete or interval prices, zero/negative prices, signed netputs, and
environmental economic objectives remain unsupported by these initial leaves.

Model-derived output-commitment marginals are labeled shadow values. They are
not observed output prices and cannot populate `PriceData`.

## 5. Composition checks before solving

The eventual registry validator evaluates at least these directed checks:

| Proposed composition | Required evidence |
|---|---|
| signed data + measure | a signed-domain formulation with proved translation/unit behavior; no undocumented shift |
| zero data + fractional/log measure | denominator/log policy for every evaluated component |
| custom direction + DDF/productivity | sign, shape, units, stable parameter identity, and cross-task comparability |
| weak disposal + environmental measure | source-qualified empirical technology; an equality alone is not universal weak disposal |
| by-production + measure | pollution-generating input roles, both subtechnologies, costly disposal, intersection/coupling, and feasible joint targets |
| network graph + measure | link/resource accounting and a supported system/process aggregation rule |
| dynamic graph + productivity | state/carry-over feasibility retained in every component task |
| super/cross protocol + base measure | executable leaf, exclusion rule, infeasibility/zero policy, secondary objective, and multiplicity diagnostics |
| target completion + base measure | primary optimum held exactly within tolerance, positive slack/priority weights, strong-target theorem, and alternate-optimum diagnostics |
| whole-template replication + radial measure | common input/output FRH technology, integer replication counts in the optimization itself, certified MILP termination/gap, finite computational-bound derivation, and no LP-dual claim |
| integer/discrete roles + technology | source-qualified integrality semantics, MILP backend, relaxation/gap diagnostics, and no post-solve rounding |
| bootstrap/CLT/subsampling + estimator | estimator-, dimension-, RTS-, DGP-, and dependence-specific inferential theory |
| deterministic sensitivity + fitted result | perturbation set and conclusion being tested; no confidence-language claim |
| robust optimization + uncertainty set | uncertainty geometry/backend and worst-case result semantics |

## 6. Validation requirements

Promotion from `under_audit` requires, in proportion to risk:

- a defining or authoritative source;
- an explicit property statement and counterexample outside its domain;
- synthetic and failure-case tests;
- invariance, monotonicity, indication, and target tests where applicable;
- at least one published numerical oracle or independent implementation for a
  release-quality leaf;
- decomposition reconstruction and cross-task unit checks for operators;
- performance evidence on the intended sample/graph scale.

The matrix will later be generated from machine-readable registry records.
Until then, this file and `METHODS.md` are the normative compatibility source.
