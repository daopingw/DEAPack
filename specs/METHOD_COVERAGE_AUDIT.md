# DEA method coverage audit and canonical grammar

This document is the cross-domain audit ledger for the DEAPack method
universe. It records what “comprehensive” means, where each major branch of
DEA belongs in the unified framework, how delivery status differs from
literature evidence, and which gaps still require source-level work.

It does not replace:

- [`METHOD_UNIVERSE.md`](METHOD_UNIVERSE.md), the reader-facing field map;
- [`UNIFIED_FRAMEWORK.md`](UNIFIED_FRAMEWORK.md), the normative semantic
  framework;
- [`METHODS.md`](METHODS.md), the implementation-facing canonical registry;
- [`reviews/`](reviews/), the equation, source, failure-domain, and oracle
  evidence layer; or
- the machine-readable shadow ontology in [`registry/`](registry/).

The snapshot was audited on 2026-07-31 against the current repository,
classic defining papers, specialist reviews, and major handbooks. It is a
coverage claim at the **family and source-leaf level**, not a claim that every
reviewed method is implemented.

## 1. Audit conclusion

The audit previously treated free-replicability-hull (FRH) models as the sole
material production-technology omission and treated the remaining umbrella
map as closed. That conclusion was too strong. FRH is
now source-frozen and implemented, but a second review identified several
mechanism-level and protocol-level gaps that broad family labels did not
resolve: the free coordination hull (FCH, also historically the free
aggregation hull), complete weak-disposal
technologies, game cross-efficiency, direction-selection policy, dynamic
by-production, state-aware dynamic productivity, governance solution
concepts, fitted global reference sets, deterministic stability analysis,
price/profitability productivity, and modern productivity inference.

The reader-facing atlas still spans the major field headings listed below,
but **heading coverage is not method coverage**. The corrected conclusion is
therefore that the atlas is a strong top-level map whose source-leaf closure
remains open and falsifiable:

- classical convex and non-convex DEA;
- observed-unit, whole-template-replication, and continuously divisible
  empirical technologies;
- proportional, directional, additive, Russell, range/bound-adjusted,
  slacks-based, epsilon-based, and related non-radial measures;
- scale, congestion, capacity, economic, allocative, ranking, and preference
  analyses;
- undesirable-output and environmental production accounts;
- productivity indexes, benchmark vintages, and source-qualified
  decompositions;
- series, parallel, general-network, multi-stage, dynamic, and
  dynamic-network production;
- group frontiers, meta-frontiers, and technology gaps;
- bootstrap and asymptotic inference, contextual analysis, conditional and
  partial frontiers;
- stochastic, chance-constrained, interval/imprecise, fuzzy, robust,
  distributionally robust, and Bayesian branches; and
- inverse, allocation, fixed-sum, merger, bargaining, and scenario uses of
  DEA.

The remaining work is nevertheless large. Coverage is uneven at three
different levels:

1. **conceptual coverage** — the family and its non-equivalence boundaries are
   known;
2. **executable coverage** — a source-qualified leaf has public code and a
   result contract; and
3. **validation coverage** — equations, failure cases, numerical oracles,
   invariance properties, and independent comparisons support the
   implementation.

These levels must never be summarized by one word such as “supported.”

### 1.1 Source-qualified gaps found in the second audit

The following ledger mixes recently implemented closures with planning and
evidence records. Every first-column label states its delivery status;
candidate IDs are proposals for source review and do not imply Python
implementation. Equivalence levels use the normative definitions in
`UNIFIED_FRAMEWORK.md`: A exact representation, B shared technology with a
different measure, C shared measure with a different technology/benchmark,
and D a distinct system, estimator, protocol, or inferential design.

| Coverage item | Eleven-axis placement | Equivalence boundary | Primary source |
|---|---|---|---|
| Implemented FCH binary subset aggregation; `technology.fch.binary_subset_aggregation` and `static.radial.fch.green_cook_2004` | $T$: nonempty binary activity-combination technology; $M$: input/output radial measure; all remaining axes are frozen in the public expanded specification | Level C versus FDH and FRH. Under matched conditions $T_{FDH}\subseteq T_{FCH}\subseteq T_{FRH}$; there is no general VRS nesting, and FCH's direct continuous relaxation is bounded-intensity rather than CCR | [Green and Cook (2004)](https://doi.org/10.1057/palgrave.jors.2601773); free-aggregation-hull name confirmed by [Adler, Olesen, and Volta (2024)](https://doi.org/10.1287/opre.2022.2348) |
| Implemented radial DEA metafrontier; `heterogeneity.metafrontier.radial.odonnell_rao_battese_2008` | $C/R/A$: ex ante groups, one within-group and one pooled-meta comparison per observation, and the identity $E^M=E^G\times\mathrm{MTR}$; $T$: `pooled_convex` under VRS and `pooled_conic` under CRS; $M$: matched input/output Farrell radial efficiency | Composes the implemented radial programme with two nested comparison populations; at the component level the changed benchmark is Level C. The complete two-fit operator is not an alias of `static.radial`, and its pooled convex/conic meta technology is not equivalent to the non-convex union of estimated group hulls | [O'Donnell, Rao, and Battese (2008)](https://doi.org/10.1007/s00181-007-0119-4) |
| Implemented two-stage intermediate-products radial network leaf; `network.radial.fare_grosskopf_2000` | $G,T$: closed two-process series technology with separate process intensities, endogenous coordinated benchmark handoffs, and disposable intermediate surplus; the evaluated $z_o$ is reported but does not condition the benchmark. $M$: input contraction or final-output expansion, reported as one orientation-qualified system factor plus harmonized efficiency. $P/A$: one primary system plan, no stage-attribution account, complete-intensity target reconstruction, and omitted coefficient-mass disclosure when peers are thresholded for display | Level B score identity with the Kao--Hwang primary centralized programme applies only to the matched input-CRS graph, link, endogenous-handoff policy, reference, and role domain. The full methods are not aliases: the radial leaf defines no stage efficiency, multiplier valuation, product decomposition, range, or midpoint target. Its separately convex VRS option is later provenance, not an original-paper claim | Two-node CRS technology and output-distance programme in [Färe and Grosskopf (1996)](https://doi.org/10.1016/0165-1765(95)00729-6); network lineage in [Färe and Grosskopf (2000)](https://doi.org/10.1016/S0038-0121(99)00012-9); VRS polyhedral statement in [Podinovski and Bouzdine-Chameeva (2021)](https://doi.org/10.1007/s11123-021-00610-3); input-score dual in [Kao and Hwang (2008)](https://doi.org/10.1016/j.ejor.2006.11.041) and [Lim and Zhu (2016)](https://doi.org/10.1016/j.ejor.2015.06.050) |
| Implemented activity-specific weak-disposal environmental general-network leaf; `network.environmental.weak_activity_specific.kalhor_kazemi_matin_2018` | $G/D$: process graph with external inputs, ordinary intermediates, and final/internal desirable and undesirable product accounts; $T$: corrected process-specific $\alpha/\beta$ weak-disposal technology with producer-specific intermediate balances; $M$: one input-radial system factor $h$; $P/A$: no inferred process efficiencies or slack completion | Level D versus the black-box activity-specific DDF despite a shared active-plus-complementary activity mechanism: process incidence, internal-product balances, score, RTS domain, and evaluation protocol differ. It is also not an environmental relabeling of the Färe--Grosskopf two-stage technology | [Kalhor and Kazemi Matin (2018)](https://doi.org/10.1051/ro/2017022); the corrected Tables 1--4 are reproduced by an independent dense compiler |
| Complete weak-disposal technology, separated from the legacy `weak` selector | $T$: common-factor CRS or activity-specific VRS disposal construction; $D$: desirable/bad roles; $M$: separately attached measure | Implemented as distinct Chung--Färe--Grosskopf common-factor and Kuosmanen activity-specific leaves. The deprecated directional-equality selector preserves old numbers but reports no weak-disposal identity and has no Level-A alias claim | [Chung, Färe, and Grosskopf (1997)](https://doi.org/10.1006/jema.1997.0146); [Kuosmanen (2005)](https://doi.org/10.1111/j.1467-8276.2005.00788.x); [Pham and Zelenyuk (2019)](https://doi.org/10.1016/j.ejor.2018.09.019) |
| Implemented Liang--Wu--Cook--Zhu game cross-efficiency; `evaluation.cross.game_nash.liang_wu_cook_zhu_2008` | $C$: participating players; $T/E/M/V$: fixed CRS CCR multiplier account; $P$: $n^2$ one-protected-$d$/focal-$j$ LPs per synchronous iteration, source equal mean over $d$ including self, stopping and Nash claim; $A$: downstream ranking only | Level D versus an aggressive, benevolent, or neutral secondary tie-break. The protected--focal table is not an ordinary appraiser--evaluatee matrix; the source mean is not a free aggregation option and `game` is not a `secondary_goal` | Source equations in [Liang, Wu, Cook, and Zhu (2008)](https://doi.org/10.1287/opre.1070.0487); independent dense LP/fixed-point cross-implementation over the project-created four-plan fixture, with no published observations or numerical-result table reproduced |
| Direction-selection policy; candidates `direction.exogenous`, `direction.observation_scaled`, `direction.range_ideal`, and `direction.endogenous_value.petersen_2018` | $M$: improvement account; $V$: value basis; $P$: ex-ante or endogenous selection rule; policy parameters remain in $\Theta$ only after the rule is named | Level B when a different declared direction changes the measure over one technology; Level D when an endogenous optimization protocol selects the direction | [Petersen (2018)](https://doi.org/10.1287/opre.2017.1711) |
| Dynamic by-production with adjustment cost; candidate `dynamic.environmental.by_production.adjustment_cost.dakpo_oude_lansink_2019` | $G$: intertemporal system; $D$: pollution-generating inputs, investment, bads; $T$: coupled dynamic by-production; $M$: source inefficiency account | Level D versus Tone--Tsutsui bad carry-over, repeated static by-production, and the Cuadros weak-disposal electricity model | [Dakpo and Oude Lansink (2019)](https://doi.org/10.1016/j.ejor.2018.12.040) |
| State-aware dynamic productivity; candidates `dynamic.productivity.malmquist.intertemporal_fare_grosskopf` and, after equation audit, `dynamic.productivity.malmquist.dynamic_sbm.tone_tsutsui` | $G,T$: explicit state/carry-over technology; $R$: temporal information set; $A$: dynamic productivity identity | Level D versus window DEA, repeated-static MPI, and a global pooled reference lacking a state transition | [Färe and Grosskopf (1996)](https://doi.org/10.1007/978-94-009-1816-0); [Färe and Grosskopf (2010)](https://doi.org/10.1007/978-1-4419-6151-8_5); [Tone and Tsutsui (2014)](https://doi.org/10.1002/9781118946688.ch8) |
| `GovernanceSpec(players, authority, objectives, move_order, information, solution_concept)` | $C$: players, rights, and information; $P$: objectives, move order, and solution concept; physical topology remains in $G$ | Level D across centralized, cooperative, leader--follower, non-cooperative, and bargaining protocols unless a source proves a conditional identity | [Liang, Cook, and Zhu (2008)](https://doi.org/10.1002/nav.20308); [Kao (2014)](https://doi.org/10.1016/j.ejor.2014.02.039) |
| Fitted global reference set/minimum face; candidate `analysis.reference_set.global.mehdiloozad_etal_2015` | $A$: fitted peer/facet analysis; $P$: projection and alternate-optimum policy | Level D/non-alias with $R$'s temporal `reference.global`: one is a fitted face, the other is an ex-ante all-period information policy | [Mehdiloozad et al. (2015)](https://doi.org/10.1016/j.ejor.2015.03.029) |
| Deterministic stability; candidate `diagnostics.deterministic_stability.ccr.seiford_zhu_1998` | $A$: allowable-perturbation/stability diagnostic; $U$ remains none because no sampling or data-generating uncertainty is introduced | Level D versus bootstrap inference, robust optimization, and partial-frontier robustness | [Seiford and Zhu (1998)](https://doi.org/10.1016/S0377-2217(97)00103-3); handbook synthesis [Zhu (2010)](https://doi.org/10.1007/978-1-4419-6151-8_3) |
| Price/profitability productivity; candidates `productivity.profitability_decomposition.odonnell_2010` and `productivity.profit_ratio_change.zhao_morita_maruyama_2019` | $V$: prices/value aggregation; $A$: source productivity and decomposition identity; $T,R$ remain explicit in component tasks | Level D versus technical-only MPI and between the two source accounting systems | [O'Donnell (2010)](https://doi.org/10.1111/j.1467-8489.2010.00512.x); [Zhao, Morita, and Maruyama (2019)](https://doi.org/10.1016/j.omega.2018.09.012) |
| Ray free affordability hull; proposed `economic.cost_indirect.free_affordability.ray_1997` | $D$: normalized input prices with unavailable input quantities; $T$: affordability technology; $V$: price normalization; $M/A$: cost-indirect account | Level C/D versus Green--Cook FCH/free aggregation hull; the shared historical `FAH` acronym is not an alias because data roles, technology, valuation, and measure differ | [Ray (1997)](https://doi.org/10.1023/A:1007747407212) |
| Modern productivity inference; candidates `inference.productivity.aggregate.pham_simar_zelenyuk_2023` and a source-frozen finite-sample/CLT leaf after the 2025 audit | $A$: named productivity/aggregation operator; $U$: estimator, panel DGP, resampling or asymptotic law; aggregation weights are explicit | Level D versus the 1999 individual-index bootstrap and deterministic aggregation | [Pham, Simar, and Zelenyuk (2023)](https://doi.org/10.1287/opre.2022.2424); [Zelenyuk and Zhao (2025)](https://doi.org/10.1017/S1365100525000094) |
| One core hyperbolic performance measure with source presets | $M$: common hyperbolic adjustment account; $D,T$: ordinary versus environmental roles and technologies; source path conventions remain in $\Theta$/preset metadata | Level B/C: reuse the core measure where equations match, but environmental technologies remain Level C-distinct and no whole-study or DDF alias is claimed | [Färe et al. (1989)](https://doi.org/10.2307/1928055); [Färe, Margaritis, Rouse, and Roshdi (2016)](https://doi.org/10.1016/j.ejor.2016.03.045) |
| Implemented multiplicative DEA family; `static.multiplicative` with 1982 original and 1983 invariant catalog presets | $D$: strictly positive ordinary inputs/desirable outputs and no undesirable outputs, tightened to greater than one for the 1982 source; $T$: original log-conic versus invariant log-convex technology; $R$: source-global cross section with labelled panel/non-global extensions; $M/V$: log inefficiency, multiplicative efficiency, log slacks/targets, and positive source exponents; $P$: one shared compiler with preset provenance | The two source recipes share one family/compiler but are not aliases: only the 1983 log-convex identity is invariant to independent positive unit rescaling. Neither recipe is ordinary CRS/VRS envelopment, the CCR multiplier form, or logged-data preprocessing. An exact analytical oracle exists; no published numerical reproduction is claimed | [Charnes et al. (1982)](https://doi.org/10.1016/0038-0121(82)90029-5); [Charnes et al. (1983)](https://doi.org/10.1016/0167-6377(83)90014-7) |
| Implemented original range-directional measure; planned SORM and future source-frozen signed SBM leaves | $D$: finite signed desirable inputs/outputs and explicit zero-active-direction failure; $T$: source VRS; $R$: extrema and technology populations match and include the focal unit; $M$: focal-to-coordinatewise-ideal ranges, three orientations, native $\beta$, and $1-\beta$ efficiency | RDM composes the generic DDF compiler but is not its alias. It is also non-equivalent to RAM, SORM, inverse RDM, radial translation, signed SBM, and undesirable-output DDF; `static.msbm.signed` remains an umbrella rather than a frozen leaf | [Portela, Thanassoulis, and Simpson (2004)](https://doi.org/10.1057/palgrave.jors.2601768); [Emrouznejad, Anouze, and Thanassoulis (2010)](https://doi.org/10.1016/j.ejor.2009.01.001); [SORM boundedness](https://doi.org/10.1016/j.ejor.2010.01.032) |
| Flexible role, dual role, and missing observations | $D$: role selection versus simultaneous role, plus exact/interval/fuzzy/missing status; $P/T$: source comparison or balance rule | Flexible-role classification is not dual-role accounting. Deletion/comparison, imputation, interval information, and fuzzy membership are not aliases | [Cook and Zhu (2007)](https://doi.org/10.1016/j.ejor.2006.03.048); [Cook, Green, and Zhu (2006)](https://doi.org/10.1080/07408170500245570); [Kao and Liu (2000)](https://doi.org/10.1057/palgrave.jors.2600056); [Kuosmanen (2009)](https://doi.org/10.1057/jors.2008.132) |
| Value efficiency, common weights, and multiple-criteria DEA | $V$: preferred plan or shared valuation; $P/A$: appraisal or multiobjective compromise | Weight restrictions, value efficiency, common-weight appraisal, and MCDEA are different mechanisms; MCDEA is a neighboring extension absent a production interpretation | [Halme et al. (1999)](https://doi.org/10.1287/mnsc.45.1.103); [Roll, Cook, and Golany (1991)](https://doi.org/10.1080/07408179108963835); [Li and Reeves (1999)](https://doi.org/10.1016/S0377-2217(98)00130-1) |
| Super-efficiency infeasibility diagnostic and source remedy | $R/P$: leave-one-out reference, infeasibility diagnosis, and source-fixed modification; base $T/M$ remains explicit | A diagnostic is not a repair. Returning missing, changing RTS/technology, using a directional repair, and the Cook--Liang--Zha--Zhu modification are different policies | [Seiford and Zhu (1999)](https://doi.org/10.1080/03155986.1999.11732379); [Cook et al. (2009)](https://doi.org/10.1057/palgrave.jors.2602544) |
| SCNLS exact representation versus CNLS/CQR/CER neighbors | $E$: one-sided sign-constrained representation versus regression/quantile/expectile losses; $U$: estimator-specific statistical claim | SCNLS and DEA coincide only under proved restrictions. Ordinary CNLS, CQR, and CER are not DEA, order-$\alpha$, or conditional-DEA aliases | [Kuosmanen (2008)](https://doi.org/10.1111/j.1368-423X.2008.00239.x); [Kuosmanen and Johnson (2010)](https://doi.org/10.1287/opre.1090.0722); [Dai et al. (2023)](https://doi.org/10.1016/j.ejor.2023.04.004) |

The RDM closure also promotes the already-public
`static.directional_distance` family into the machine registry so that the
new `composes` edge has a resolvable dependency target. This is ontology
completion, not a second DDF implementation or a new catalog entry. Signed
methods whose defining equations or independent oracles are not yet frozen
remain planned for a later release rather than being reconstructed by analogy.

The audit also found five cross-domain governance gaps:

1. the repository needed one compact coverage ledger joining the otherwise
   strong domain reviews;
2. “planned” did not visibly distinguish a committed implementation leaf
   from a research-only branch whose executable contract is not yet stable;
3. cross-products of implemented components could be mistaken for validated
   methods even though composition is not closed automatically;
4. decision-support methods had canonical entries but no dedicated maintained
   review stream; and
5. the literature-baseline documentation described too few review streams
   after the programme had expanded.

This document, the review index, and
[`reviews/DECISION_SUPPORT.md`](reviews/DECISION_SUPPORT.md) close all five
governance gaps. Source-level and executable coverage within each stream
remains governed by the delivery and evidence statuses below.

## 2. Canonical study grammar

A fitted DEA study is represented by the semantic product

$$
\mathfrak S
=
\langle
C,G,D,T,E,R,M,V,P,A,U;\Theta
\rangle ,
$$

where:

| Symbol | Registry axis | Question resolved |
|---|---|---|
| $C$ | `context` | Whose decision, mission, control rights, and information are being evaluated? |
| $G$ | `graph` | Is production a black box, series, parallel, general network, temporal system, or dynamic network? |
| $D$ | `data_roles` | Which quantities are inputs, valued outputs, residuals, links, carry-overs, prices, contextual conditions, or restricted decisions, and how is each quantity represented? |
| $T$ | `technology` | Which operating plans are attainable under the declared convexity, scale, disposal, coupling, and physical-account assumptions? |
| $E$ | `estimator` | How does the observed sample construct the boundary: full DEA/FDH, partial frontier, conditional frontier, or another supported estimator? |
| $R$ | `reference` | Which organizations and periods may teach the evaluated unit, and which observations are excluded by the benchmark policy? |
| $M$ | `performance` | What improvement, distance, slack account, ratio, or economic opportunity is measured? |
| $V$ | `valuation` | Which market prices, shadow values, stakeholder restrictions, or process weights value the account? |
| $P$ | `evaluation_protocol` | How are alternate optima, strong targets, ranking, super-efficiency, or cross-appraisal handled? |
| $A$ | `analysis` | Is the fitted task used inside scale, productivity, decomposition, allocation, or another analytical operator? |
| $U$ | `uncertainty` | Is uncertainty about sampling, measurement, production states, probability, fuzzy membership, or a robustness set? |
| $\Theta$ | fixed/exposed parameters | Orientation, RTS, direction, normalization, bandwidth, risk level, weights, boundary policy, and other leaf parameters. |

The grammar is intentionally economic before it is computational. Solver
form, sparse layout, Charnes--Cooper transformation, and backend are
implementation metadata. They can establish an exact representation but do
not define the economic identity of a method.

The eleven axes and machine schema remain unchanged. Within $D$, however,
every relevant variable has a mandatory nested representation/domain record:

| `data_roles.representation` | Controlled values |
|---|---|
| `measurement_scale` | `cardinal`, `ordinal`, `nominal`, `ratio` |
| `sign_domain` | `nonnegative`, `signed` |
| `divisibility` | `continuous`, `integer`, `binary` |
| `observation_status` | `exact`, `interval`, `fuzzy`, `missing` |
| `controllability` | `discretionary`, `fixed`, `bounded` |

This is a semantic substructure, not a twelfth axis. It prevents the same
spreadsheet sign or missing marker from being mistaken for an economic role,
and it makes special-data compatibility fail closed.

### 2.1 Family, leaf, preset, and operator

A **family** leaves at least one identity-changing choice unresolved. It is a
discovery and software-reuse node, not a complete fitted-study identity. A
public family estimator may expose those unresolved choices as validated
arguments, but the family name or `method_id` alone never identifies the
resulting study.

A **leaf** resolves every axis required for its decision question and freezes
the domain, score convention, target meaning, and failure policy. A fitted
result is therefore a leaf identified by its canonical `method_id`, any
`specialization_id` or `preset_id`, and its complete `expanded_spec`.
`method_id` may name the reusable family, variant, preset, or operator that
supplies the implementation; it is not treated as the whole semantic identity
when runtime arguments still resolve an axis.

A **preset** is a historically recognized, sufficiently complete leaf or
partial recipe. CCR and BCC alone are scale specializations; CCR-I, CCR-O,
BCC-I, and BCC-O become complete radial presets only after orientation,
native-value convention, and target policy are fixed.

An **operator** combines one or more fitted leaves under a tested identity.
Malmquist productivity, allocative decompositions, meta-frontier technology
gaps, and industry reallocation are operators, not alternative spellings of a
base DEA score.

### 2.2 Historical names resolve conditionally

A historical label is represented as:

```text
historical label
    --[equivalence domain and provenance]-->
canonical family, specialization, preset, or leaf
    --[expanded axes and parameters]-->
fitted result
```

An alias is therefore never an unconditional string replacement. The domain
can include positivity, matched RTS and reference membership, a fixed score
transformation, and identical target/peer semantics.

### 2.3 Composition is fail-closed

The existence of two reviewed or implemented components does not certify
their cross-product. In particular:

- environmental DDF plus dynamic SBM does not establish a dynamic
  environmental DDF;
- network SBM plus a leave-one-out reference does not establish a valid
  super-network SBM;
- a bootstrap for radial DEA does not establish inference for SBM, network,
  dynamic, or meta-frontier scores;
- a robust counterpart of one CCR formulation does not establish robust
  versions of every model sharing its matrix blocks; and
- a general graph compiler does not establish a system/process aggregation
  identity for every network measure;
- using an efficiency estimate as an outcome in DID, treatment, or policy
  analysis does not identify a causal effect without a separate
  counterfactual design; and
- a neural, ensemble, or other machine-learning surrogate does not inherit
  the production technology, extrapolation rules, or interpretability of the
  DEA estimator it approximates.

Every cross-family composition must pass its own compatibility, score,
failure, and validation audit.

## 3. Delivery status and evidence are independent

### 3.1 Reader-facing delivery classes

The field-wide roadmap uses three positive delivery classes:

| Delivery class | Meaning |
|---|---|
| **implemented** | At least one exact public leaf has code, canonical metadata, tests, and documentation. It does not promote every member of the surrounding family. |
| **planned** | A source-qualified leaf and intended dependency path are sufficiently clear for implementation, but the public contract is incomplete. Internal prototypes remain planned from a user's perspective. |
| **research-only** | The branch belongs in the atlas, but identification, formulation choice, backend, data domain, or validation evidence is not stable enough to promise an executable leaf. |

`excluded` is reserved for methods outside the package boundary, such as an
ordinary machine-learning performance predictor without a registered
production-frontier role. Neighboring SFA, CNLS, and StoNED estimators remain
visible for comparison but are not relabeled DEA.

The shadow ontology retains the more granular internal lifecycle states
`planned`, `prototype`, `partial`, and `implemented`. The reader-facing
classes above are a projection:

```text
implemented + public leaf       -> implemented
planned/prototype/partial leaf  -> planned
provisional branch, no release commitment -> research-only
excluded/non-DEA                -> excluded or neighbor
```

The current shadow release contains 62 machine records and 37 typed relation
records. Its 58 implemented/public records comprise 57 `method_id` entries
and the APZ `preset_id`; four additional source-gated `method_id` prototypes
remain non-public. The discovery catalog contains those 57 methods, five
named constructor/reporting `specialization_id` contracts, and eight presets,
for 70 identities. APZ is the only public preset with a machine record in this
snapshot; the other seven presets--four radial recipes, the FGNZ core, and the
two multiplicative source recipes--compose already-registered methods without
duplicating their machine leaves.

### 3.2 Literature and numerical evidence

Delivery status is not an evidence grade. Source evidence remains:

| Evidence status | Permitted claim |
|---|---|
| `primary-checked` | Defining equations and their stated domain were checked against a primary source. |
| `review-supported` | A reputable review or handbook supports the family boundary, but an executable leaf still needs a defining-source audit. |
| `registry-provisional` | The branch belongs in the atlas, but important formulation or provenance questions remain open. |

Numerical verification remains separate:

| Oracle status | Meaning |
|---|---|
| `not located` | No suitable published or independent numerical oracle has been identified. |
| `candidate` | A source table or implementation may be usable after data and convention reconciliation. |
| `analytically derived` | Exact values are derived independently from a frozen source fixture and programme; this certifies the stated mathematical branch but is not a published-results reproduction. |
| `reproduced` | DEAPack reproduces a source-qualified numerical example within a stated tolerance. |
| `cross-implemented` | An independent implementation agrees on a frozen fixture and convention. |

Synthetic tests, property tests, source oracles, and independent
cross-implementation answer different questions and are reported separately.
A method with property evidence only must say so; a source equation does not
certify software, and matching one table does not establish a whole family.
For the current release, executable validation may be either a reproduced
published/independent oracle or an exact synthetic fixture whose expected
values are derived independently from the implementation. A solver checking
its own reconstructed identities is supporting evidence, not an independent
oracle.

### 3.3 Promotion gate

An executable family, variant, preset, or operator path can move from planned
to implemented/public only after every exposed leaf has:

1. a primary-source equation freeze and economic interpretation;
2. all eleven semantic axes resolved or explicitly marked not applicable;
3. a fixed data/invariance domain and fail-closed compatibility rules;
4. a native score, improvement direction, target guarantee, and
   alternate-optimum policy;
5. backend requirements and numerical scaling policy;
6. hand-checkable tests, property/failure tests, and honest oracle status;
7. one canonical package symbol and no duplicate acronym solver;
8. aligned book placement and complete API documentation; and
9. benchmarks proportional to the expected sample and block size.

If the complete defining source, the source-native equations and economic
semantics, or an independent executable validation path cannot be closed, the
leaf is `deferred_to_next_version`. It may retain a source protocol and a
place in the field map, but it receives no guessed programme, public API, or
executable claim in the book. A pre-existing code-bearing reconstruction may
retain a `prototype/api-none` machine record solely for evidence governance;
that inventory record is not a release identity. Missing original
empirical data blocks a claim of reproducing that application; it does not by
itself block a later theory release when an exact independent synthetic
oracle is available.

## 4. Cross-domain coverage ledger

“Implemented foundation” below means that one or more public leaves exist.
It never means that all variants in the row are executable.

| Branch | Identity-changing choices retained | Delivery snapshot | Evidence home |
|---|---|---|---|
| Convex empirical technology | CRS/VRS/NIRS/NDRS, disposal, convexity, comparison population | implemented foundation; observation-specific source-neutral peer eligibility intersects the base `ReferenceSpec` population and is public on the audited ordinary radial, Additive/RAM, ordinary SBM, and ordinary DDF classical black-box surface; actual self/mixed/external appraisal and base/effective population sizes are retained | `STATIC_ECONOMIC.md`, `M11_PEER_ELIGIBILITY.md`, `M12_CORE_PEER_ELIGIBILITY.md` |
| Non-convex empirical technology | standard FDH, binary-subset FCH, integer-replication FRH, CRS/NIRS/NDRS FDH scale extrapolation, and bounded replication | standard FDH, Green--Cook FCH, and unbounded whole-template FRH implemented/public; extrapolated and bounded variants remain planned/evidence candidates | `STATIC_ECONOMIC.md` |
| Classical radial measurement | input versus output orientation, native Farrell/Shephard convention, target completion | implemented foundation | `STATIC_ECONOMIC.md` |
| Hyperbolic and generalized proportional paths | coordinated multiplicative adjustment path, path parameters, positivity, score convention, and attached technology/data roles | Chavas--Cox GDF implemented; the standard reciprocal hyperbolic leaf is deferred to the next version until its source-native score/domain/target contract and independent oracle are frozen | `STATIC_ECONOMIC.md`, `ENVIRONMENTAL.md`, `PATH_MODEL_DESIGN.md`, `source_protocols/standard_hyperbolic.md` |
| Multiplicative technology | original-1982 log-conic versus invariant-1983 log-convex construction, strict source domains, exponent-floor convention, unit behavior, source/global versus extension references, and native log/exponentiated results | implemented/public as one `static.multiplicative` family and shared compiler with two catalog preset identities; exact two-DMU analytical oracle and independent dense source compiler, but no published numerical reproduction. Both variants exclude undesirable outputs; 1982 requires every ordinary quantity greater than one and is unit-dependent, while 1983 requires strict positivity and is invariant to independent positive rescaling. Panel/non-global references remain labelled package extensions, not source reproductions | `STATIC_ECONOMIC.md`, `PATH_MODEL_DESIGN.md`, `source_protocols/charnes_etal_1982_1983_multiplicative.md`, `oracles/multiplicative-analytical.md` |
| Additive and range/bound adjustment | classic VRS unit slack sum versus configurable fixed weights/RTS/reference policy, plus RAM/BAM normalizer and population | additive, RAM, and the frozen-global nonnegative BAM leaf implemented. The direct additive analytical certificate covers only Charnes et al. (1985) equations (4.5)--(4.6), unit weights, VRS, and one self-inclusive cross-section; fixed non-unit weights, other RTS/reference policies, and restricted peer-eligibility populations are package extensions without that source identity. RAM freezes its full-data range population before eligibility and labels a restricted effective comparison population as `deapack_ram_extension`; BAM remains outside the peer-eligibility surface. Equation (5.7), separately named unsupported additive leaves, Enhanced BAM, and alternative bound scopes remain deferred/planned | `STATIC_ECONOMIC.md`, `source_protocols/charnes_etal_1985_additive.md`, `M12_CORE_PEER_ELIGIBILITY.md` |
| Russell, SBM, EBM, and Hölder families | adjustable components, orientation, fractional or norm aggregation, positivity | standard Tone SBM and its exact-domain input/output Russell aliases are implemented. The declared-calibration input-oriented CRS Tone--Tsutsui EBM-I-C conditional evaluator is implemented/public with mandatory epsilon, normalized input weights, and provenance; the full automatic affinity/PCA calibration identity and wider EBM family remain deferred. Graph Russell and Hölder variants remain planned | `STATIC_ECONOMIC.md`, `M13_DECLARED_EBM_IC.md`, `source_protocols/tone_tsutsui_2010_ebm.md` |
| Directional and variable-specific measures | direction provenance, exogenous/observation-scaled/range-ideal/endogenous selection policy, scale, subvector, aggregation, ideal-point construction | generic DDF and the original VRS RDM leaf are implemented/public; RDM fixes focal-to-coordinatewise-ideal ranges and exact reference/extrema matching. Subvector/component distance is deferred to the next version until exact source leaves and target semantics are frozen; other direction-policy leaves and MEA remain planned/evidence only | `STATIC_ECONOMIC.md`, `source_protocols/subvector_distance.md` |
| Economic efficiency | cost, revenue, maximum profit, shutdown, profitability, Nerlovian normalization, price-only/free-affordability and other indirect accounts | major cost/revenue/profit/Nerlovian/profitability leaves implemented; Ray free affordability and other indirect/specialist decompositions planned/evidence | `STATIC_ECONOMIC.md` |
| Scale, capacity, congestion, scope, and shadow values | qualitative RTS, scale ratio, elasticity, fixed-mix global average productivity, quasi-fixed resources, disposability definition, joint-production counterfactual | radial scale ratio, selected-projection Banker--Thrall local RTS, and matched one-sided radial VRS scale elasticity implemented; fixed-observed-mix Banker MPSS and classical CRS physical capacity retained only as non-public prototypes with `deferred_to_next_version` status; directional elasticity, economic/environmental capacity, congestion, and scope leaves planned | `STATIC_ECONOMIC.md` |
| Weight, preference, and shared-valuation designs | AR-I/AR-II, cone ratio, virtual shares, production trade-offs, preferred plans/value efficiency, common weights, and MCDEA compromise objectives | the finite input-oriented CRS Charnes--Cooper--Huang--Sun polyhedral cone-ratio sum-form leaf is source-frozen and implemented/public: 1990 Example 2 is independently reproducible through source-only multiplier and envelopment oracles, while Example 3/Table 2 retains an unresolved two-row source conflict and is excluded. Its dedicated production API and machine registry record do not open a generic restrictions interface. Thompson AR-I/AR-II, Wong--Beasley virtual shares, and Roll--Cook--Golany common weights remain source-incomplete and deferred; Halme value efficiency remains planned; Li--Reeves MCDEA is a neighboring extension rather than an alias | `WEIGHTS_SPECIAL_DATA_HETEROGENEITY.md`, `source_protocols/charnes_cooper_huang_sun_1990_polyhedral_cone_ratio.md`, `oracles/charnes_cooper_huang_sun_1990_cone_ratio.md` |
| Ranking and target protocols | super-efficiency base measure and applicability gate, ordinary cross-appraisal primary/secondary selection, protected--focal game/Nash protocol, common weights, closest/strong target, frontier tiers | Tone's strongly SBM-efficient super-SBM leaf and the distinct Liang--Wu--Cook--Zhu game protocol are implemented/public. Andersen--Petersen radial leave-one-out and ordinary solver-selected CRS cross-efficiency remain tested non-public prototypes because their defining full texts were not obtained; their later-source and property evidence does not pass the current release gate. Tone's leaf strictly separates the same-RTS ordinary non-oriented SBM screen from CRS non-oriented/input/output or VRS non-oriented peer-replacement appraisal, rejects zero/signed/bad-output data, and reproduces the source oracles. The source-checked Pareto--Koopmans completion protocol is public only as an embedded phase-two composition of ordinary convex radial DEA, nonnegative-policy DDF, and finite-nonnegative-path CRS/VRS GDF with positive observation-level aggregates; evaluated-observation versus fixed-path zero-safe row-scale anchors are disclosed alternate-target policies, and environmental, nondiscretionary, FDH/FCH/FRH extensions are deferred. Directional super-efficiency, later super-SBM variants, Doyle--Green Method II/III, VRS cross-appraisal, common weights, closest targets, and most other target/ranking protocols remain planned | `WEIGHTS_SPECIAL_DATA_HETEROGENEITY.md`, `STATIC_ECONOMIC.md`, `source_protocols/charnes_etal_1985_pareto_koopmans_completion.md`, `source_protocols/andersen_petersen_1993_super_efficiency.md`, `source_protocols/ordinary_crs_cross_efficiency.md` |
| Fitted peer/facet analysis | unary/maximal/global reference sets, minimum face, projection multiplicity, alternate support | broad diagnostics exist; the Mehdiloozad et al. global-reference-set leaf is planned/evidence only and is not temporal `reference.global` | `STATIC_ECONOMIC.md`, `WEIGHTS_SPECIAL_DATA_HETEROGENEITY.md` |
| Deterministic stability analysis | allowable perturbations, protected status, coefficient/data scope, one- versus simultaneous-change policy | planned/evidence only; not a bootstrap or robust-optimization claim | `STATISTICS_UNCERTAINTY.md` |
| Pessimistic and double-frontier appraisal | least-favourable valuation, inefficient empirical boundary, inverted/anti-ideal construction, component normalization, combination rule | separate planned discovery families; Wang--Chin--Yang geometric leaf awaits equation/oracle freeze | `WEIGHTS_SPECIAL_DATA_HETEROGENEITY.md` |
| Special and restricted data | mandatory representation/domain fields plus non-discretionary/categorical/ordinal/ratio/integer, flexible versus dual role, signed/zero, and missing/interval/fuzzy semantics | validation foundations remain partial; the original RDM is implemented/public. Source-neutral peer eligibility is implemented on the audited ordinary radial, Additive/RAM, ordinary SBM, and ordinary DDF classical black-box surface as the intersection of a declared observation-specific candidate population with the base `ReferenceSpec`; it infers no categories and implements neither Banker--Morey model. Undesirable-output SBM and other environmental or specialist neighbors remain outside this milestone. Both provisional Banker--Morey static leaves and SORM are deferred to the next version under separate source gates. The categorical audit located only publisher metadata/abstract and an unlabelled raw data file, not defining equations or an oracle. Signed SBM remains an umbrella and missing-data treatments remain policy-specific | `M11_PEER_ELIGIBILITY.md`, `M12_CORE_PEER_ELIGIBILITY.md`, `WEIGHTS_SPECIAL_DATA_HETEROGENEITY.md`, `source_protocols/banker_morey_1986_categorical.md`, `source_protocols/banker_morey_1986_nondiscretionary.md`, `source_protocols/emrouznejad_anouze_thanassoulis_2010_sorm.md` |
| Environmental production accounts | joint production, common/activity-specific/generalized/selective/semi-disposal, null jointness, by-production, joint-input, material balance, treatment | strong disposal, legacy directional equality, Chung--Färe--Grosskopf common-factor CRS, Kuosmanen activity-specific VRS, by-production, material-inflow subsets, and the APZ capped-bad inequality technology inside its public productivity preset are implemented; the legacy `weak` selector remains explicitly unidentified and deprecated; generalized/selective/semi-disposal remain research or planned leaves | `ENVIRONMENTAL.md`, `PRODUCTIVITY.md` |
| Environmental measures | DDF, hyperbolic, separable/non-separable SBM, directional non-radial, shadow abatement | DDF and separable SBM foundations implemented; Tone's non-separable radial/slack hybrid and other source-qualified leaves planned | `ENVIRONMENTAL.md` |
| Static productivity and benchmark vintages | Malmquist/Luenberger, global/biennial/sequential/window reference, environmental direction, complete versus local TFP account | core radial/directional and environmental operators, the APZ capped-bad-output ML preset, and the adjacent-period Bjurek Hicks--Moorsteen complete output/input quantity account are implemented. APZ composes the 2017 equations (5)--(6) CRS technology with four contemporaneous ML roles, strictly positive inputs/bads, componentwise reference-period caps, and an independent exact oracle; it neither post-processes CFG nor uses Oh's global reference. Required cross-task infeasibility remains explicit, and no WIOD empirical reproduction is claimed. Färe--Primont, additive-complete, and other advanced non-radial indexes remain planned or deferred under their own gates | `PRODUCTIVITY.md`, `source_protocols/aparicio_pastor_zofio_2013.md`, `source_protocols/odonnell_2012_fare_primont.md` |
| Productivity decomposition | FGNZ, Ray--Desli, Balk, scale/mix, bias, aggregation, reallocation, price/profitability identities | the output-oriented CRS FGNZ two-component core is an implemented/public preset with an independent exact oracle. The distinct enhanced FGNZ operator is implemented/public with four CRS plus two own-period VRS tasks and its own exact component oracle; its strict-positive matched-panel source certificate is kept separate from tested partial-zero and unbalanced-panel package extensions. The distinct Ray--Desli operator is implemented/public on its strictly positive, balanced, one-desirable-output source domain with four CRS plus four VRS tasks and partial-component preservation under VRS cross infeasibility. Balk remains a next-version bibliographic candidate because no complete checksum-audited defining text, equation/task freeze, or independent oracle is present in the current evidence bundle. O'Donnell (2010) and Zhao--Morita--Maruyama (2019) remain evidence candidates, not implemented operators | `PRODUCTIVITY.md`, `source_protocols/fgnz_ray_desli_balk_decompositions.md` |
| Series and multi-stage networks | radial/relational/additive/SBM measure, intermediate valuation/control, process intensities, stage attribution | Färe--Grosskopf two-stage system-radial, Kao--Hwang relational, Chen additive, Cook open-DAG, and Tone--Tsutsui network-SBM leaves implemented; the Färe--Grosskopf leaf intentionally has no stage-efficiency account | `NETWORK_DYNAMIC.md`, `NETWORK_ADDITIVE.md`, `NETWORK_SBM.md` |
| Parallel, shared-resource, and general networks | resource-pool allocation, incidence, topology, cycles, governance, system aggregation, sequential propagation, sector input--output conservation, and relational series--parallel accounting | graph foundation, selected general-network leaves, and the Lewis--Sexton nonnegative forward-quantity sequential radial slice are implemented; reverse/mixed sequential accounts, Kao general/parallel, and Liang--Cook--Zhu governance remain source-qualified gaps; Prieto--Zofío is deferred to the next version because its primary equations and oracle could not be frozen | `NETWORK_DYNAMIC.md`, `source_protocols/prieto_zofio_2007.md` |
| Repeated-period and dynamic production | Park--Park aggregation without state; intertemporal technology, optimal control, investment/quasi-fixed capital, typed carry-over, scale, lagged intermediates, transition and boundary policy, dynamic by-production and adjustment cost | Park--Park multi-period aggregation and Tone--Tsutsui dynamic SBM are implemented as distinct method identities; Sengupta, Sueyoshi--Sekitani, Chen, Aparicio--Kapelko, dynamic by-production, and other lineages remain planned/evidence only | `NETWORK_DYNAMIC.md`, `ENVIRONMENTAL.md` |
| Dynamic network production | within-period link kind, temporal carry-over kind, process RTS, weights, boundary policy | canonical Tone--Tsutsui leaf implemented/public with exact reductions and a claim-scoped independent joint non-oriented CRS primal--dual certificate; the published anonymous application is not reproduced and advanced variants remain planned | `NETWORK_DYNAMIC.md` |
| Network/dynamic productivity | graph/state-aware scale, efficiency change, productivity identity, changing topology | planned; intertemporal Malmquist and dynamic-SBM productivity candidates require state-preserving reconstruction and are not repeated-static MPI | `NETWORK_DYNAMIC.md`, `PRODUCTIVITY.md` |
| Known-group heterogeneity and nonhomogeneous activity coverage | group frontier, meta-technology construction, technology-gap measure, group/meta productivity, structurally absent activities, and partial input--output incidence | the O'Donnell--Rao--Battese radial group/pooled-meta account is implemented/public and is the sole current Handbook route; `reference.group` and `technology.meta.pooled_convex` are internal composition labels, not standalone operators. Group/meta productivity, non-radial and nonconvex metafrontiers, Cook et al. (2013) nonhomogeneous-DMU, and Imanirad et al. (2015) partial-incidence leaves remain next-version/source-qualified, and neither structural branch is missing-data repair | `WEIGHTS_SPECIAL_DATA_HETEROGENEITY.md`, `PRODUCTIVITY.md` |
| Full-frontier sampling inference | estimator/DGP-specific bias, confidence interval, structure test, individual and aggregate productivity inference | planned; the 2023 aggregate and 2025 finite-sample/CLT sources are evidence candidates, not executable claims | `STATISTICS_UNCERTAINTY.md`, `PRODUCTIVITY.md` |
| Operating conditions | separability, Simar--Wilson Algorithms 1/2, Banker--Natarajan, conditional DEA/FDH, Fried three-stage adjustment | planned as distinct procedures/estimators | `STATISTICS_UNCERTAINTY.md`, `WEIGHTS_SPECIAL_DATA_HETEROGENEITY.md` |
| Partial frontiers and influence | order-$m$, order-$\alpha$, trimming, influence, outlier audit | planned | `STATISTICS_UNCERTAINTY.md` |
| Production risk and stochastic DEA | state-contingent production, random deviations, measurement error, stochastic PPS, chance constraints | planned advanced branch | `STATISTICS_UNCERTAINTY.md` |
| Imprecise and fuzzy information | interval/IDEA information order, membership/possibility rule, optimization semantics | planned advanced branch | `STATISTICS_UNCERTAINTY.md` |
| Robust optimization | box/polyhedral/budgeted versus ellipsoidal/conic sets, price of robustness | planned source-qualified leaves; generic robust flag prohibited | `STATISTICS_UNCERTAINTY.md` |
| Distributional ambiguity and Bayesian frontier analysis | ambiguity set or likelihood/prior, posterior object, identification, computation | research-only | `STATISTICS_UNCERTAINTY.md` |
| Spatial mechanisms | spatial benchmark eligibility, contextual conditioning, production spillover, dependence-aware inference | planned source leaves; generic spatial switch research-only | `STATISTICS_UNCERTAINTY.md` |
| Causal and policy designs using efficiency outcomes | estimand, treatment timing, interference, support, counterfactual frontier, generated-outcome uncertainty | external identification layer or research-only joint estimator; never an alias for ordinary second-stage regression | `METHOD_UNIVERSE.md`, `STATISTICS_UNCERTAINTY.md` |
| ML-assisted, ensemble, and neural frontier methods | technology preservation, shape restrictions, training target, extrapolation, uncertainty, interpretability | neighboring estimation/prediction branch; only source-qualified leaves that retain an explicit production technology may enter the executable atlas | `METHOD_UNIVERSE.md`, `STATISTICS_UNCERTAINTY.md` |
| Decision support | inverse DEA, centralized allocation, fixed/shared-cost allocation, fixed-sum/ZSG, merger, bargaining, target/scenario planning | canonical planned entries and dedicated evidence stream; equations and oracles remain planned | `DECISION_SUPPORT.md`, `METHOD_UNIVERSE.md`, `METHODS.md` |
| Neighboring frontier estimators | SFA, ordinary CNLS, CQR, CER, StoNED, shape-constrained and Bayesian stochastic frontiers | comparison only; the restricted SCNLS representation may coincide with DEA on its proved domain, but no blanket CNLS/CQR/CER alias follows | `STATISTICS_UNCERTAINTY.md` |

## 5. Merge ledger

### 5.1 Safe aliases and exact representations

The following are safe only on their recorded domains:

| Historical names or forms | Canonical treatment | Required domain |
|---|---|---|
| CCR / CRS DEA; BCC / VRS DEA | scale specializations of convex radial DEA | orientation and score/target convention remain unresolved until a preset is selected |
| CCR-I/O and BCC-I/O | complete public radial presets `CCRInput`, `CCROutput`, `BCCInput`, and `BCCOutput`, all retaining `method_id="static.radial"` | matched technology, orientation, native score convention, and `compute_slacks=True` under DEAPack's row-scaled lexicographic target policy; that phase-two selector is package policy rather than a uniquely source-prescribed target |
| envelopment and multiplier programmes | primal/dual representations | every technology, valuation restriction, scale condition, and sign convention corresponds |
| output expansion $\phi$ and displayed efficiency $1/\phi$ | exact value transform of one fitted solution | $\phi>0$, native value retained |
| input/output Russell and the matched oriented Tone accounts | exact aliases of the corresponding oriented SBM leaves | strictly positive data, matched technology, RTS, reference, equal-dimension normalization, score convention, and target policy; graph Russell is excluded |
| standard positive-data ERG/ERGM and non-oriented Tone SBM | one canonical fractional slack measure | matched positive domain, technology, weights, normalizers, reference, and score direction |
| DEA and the Kuosmanen--Johnson SCNLS representation | exact estimator representation only on the source's matched sign-constrained, shape-constrained, one-sided-loss graph domain | relaxing the sign/loss restriction or changing the conditional-function target exits the equivalence domain |
| good/desirable, bad/undesirable, free/discretionary, fixed/non-discretionary carry-over labels | provenance aliases inside the Tone--Tsutsui dynamic-SBM preset | same source equations and boundary policy; effect/control axes do not merge generally |
| free/discretionary and fixed/non-discretionary network-link labels | provenance aliases inside the source Tone--Tsutsui network-SBM preset | same link balance and endpoint policy |
| return-to-dollar efficiency and the current `ProfitabilityEfficiency` API spelling | one canonical implemented value-ratio leaf | matched prices, positive candidate values, and reference policy |

### 5.2 Variants that must never be merged silently

- input, output, and non-oriented measures when their objectives and target
  guarantees differ;
- radial, additive, Russell, SBM, EBM, directional, hyperbolic, and economic
  objectives over one technology;
- convex DEA, one-template FDH, binary-subset FCH, integer-combination FRH,
  partial frontiers, and conditional frontiers;
- whole-template replication, integer-valued production quantities,
  additive-slack performance, free coordination, and bounded replication;
- range-directional, SORM, signed-data SBM, and translation-based treatments
  of signed observations;
- flexible-role classification, simultaneous dual-role accounting, structural
  absence, and genuinely missing observations;
- missing-observation comparison/deletion, imputation, interval information,
  and fuzzy-membership treatment;
- standard, pooled-convex, and non-convex-union meta-technologies;
- black-box, independently fitted stages, jointly linked network, dynamic,
  and dynamic-network technologies;
- physical network topology and governance protocols such as centralized,
  cooperative, leader--follower, non-cooperative, or bargaining solutions;
- fixed, free, as-input, and as-output internal links;
- beneficial, harmful, neutral/free, and fixed carry-over roles;
- common-factor and activity-specific weak-disposal technologies;
- the legacy bad-output directional-equality selector and any complete named
  weak-disposal technology;
- strong disposal, by-production, joint-input parallel production,
  material-inflow, and material-balance treatment accounts;
- Malmquist, Luenberger, Hicks--Moorsteen, Färe--Primont, window efficiency,
  and state-aware dynamic productivity;
- technical productivity, price/profitability productivity, and distinct
  source accounting systems for profit-ratio change;
- Green--Cook free coordination/free aggregation hull and Ray's cost-indirect
  free affordability hull, despite their shared historical `FAH` acronym;
- super-efficiency, cross-efficiency, common-weight appraisal, and
  strong-target completion;
- super-efficiency infeasibility diagnosis, a missing-result policy, and each
  source-qualified technology/directional/slack repair;
- ordinary cross-efficiency secondary tie-breaks and coupled
  game/Nash cross-efficiency;
- least-favourable multiplier appraisal, worst-practice frontier estimation,
  aggressive cross-efficiency, pessimistic uncertainty scenarios, and
  double-frontier score composition;
- group frontiers, meta-frontiers, conditional frontiers, and categorical
  peer restrictions;
- weight restrictions, value efficiency, common-weight appraisal, and
  multiple-criteria DEA compromise;
- bootstrap inference, partial-frontier robustness, robust optimization,
  chance constraints, stochastic production, interval information, and fuzzy
  membership;
- deterministic allowable-perturbation stability, sampling inference, and
  uncertainty-set robustness;
- fitted global reference sets/minimum faces and the ex-ante all-period
  `reference.global` productivity policy;
- exogenously declared, observation-scaled, range/ideal, and endogenously
  selected directions unless their complete measure/protocol identity is
  proved;
- descriptive/contextual association, causal treatment identification, and
  counterfactual frontier estimation;
- empirical DEA technologies and unconstrained neural, ensemble, or
  machine-learning score predictors; and
- DEA-equivalent SCNLS on its proved domain, ordinary CNLS, convex quantile
  regression, convex expectile regression, order-$\alpha$, and conditional
  DEA outside any separately proved identity; and
- two-stage production networks, second-stage contextual regression, and
  three-stage DEA--SFA--DEA data adjustment.

The ordinary and environmental hyperbolic source lineages are handled
differently from the prohibitions above. Where their path equation is
identical they may share one core $M$ implementation after proof, but their
source presets retain the attached $D$, $T$, score convention, and
provenance. This is measure reuse at Level B/C, not a Level-A alias between
whole studies and not an automatic alias to DDF.

## 6. Concrete gaps and corrections

### 6.1 Evidence gaps, not missing acronyms

The broad families are present. The most important unresolved leaves are:

1. **Empirical-technology closure:** FRH and the Green--Cook FCH are now
   implemented/public. FCH retains nonempty binary subset intensities, a
   synthetic four-plan independent exact analytical certificate, certified
   MILP termination, and
   the matched $T_{FDH}\subseteq T_{FCH}\subseteq T_{FRH}$ boundary. Its
   direct continuous relaxation has bounded intensities and is not CCR; FCH
   and VRS are not generally nested. “Free aggregation hull” and historical
   `FAH` are exact names for this Green--Cook technology, but `FAH` is not a
   public Python alias because Ray's distinct free affordability hull uses
   the same acronym.
2. **Classic measure closure:** input/output Russell now resolve to the
   implemented oriented Tone leaves on their exact equivalence domain. Graph
   Russell and EBM, standard/generalized hyperbolic, Enhanced BAM or
   alternative BAM-bound scopes, and source-qualified signed/zero-data
   measures still need equation freezes and oracles. Multiplicative DEA is now
   closed as one shared public family/compiler with separate 1982 original
   log-conic and 1983 invariant log-convex catalog presets, strict source
   domains, explicit unit behavior, an independent exact analytical oracle,
   no published numerical reproduction claim, and labelled panel/non-global
   extensions. The 2011 frozen-global nonnegative BAM leaf is implemented
   with a 12-DMU cross-implementation oracle. Hyperbolic work should implement
   one proven core measure while retaining ordinary/environmental source
   presets and their different technologies.
3. **Direction policy:** storing a direction vector is not enough. Exogenous,
   observation-scaled, range/ideal, and endogenous value-based selection
   require named $M/V/P$ policies; endogenous selection must not be hidden
   as an ordinary parameter in $\Theta$.
4. **Evaluation protocols:** super-efficiency and ordinary cross-efficiency
   require base-measure-specific infeasibility, alternate-weight, and
   VRS-intercept policies; one generic ranking wrapper would be incorrect.
   The implemented Liang--Wu--Cook--Zhu game leaf is equation- and
   oracle-frozen: for every protected $d$ and focal $j$, one CRS LP
   normalizes $j$'s virtual input, maximizes $j$'s score, and protects only
   $d$'s current floor; all $n^2$ LPs use the same old vector before the
   equal mean over $d$, including self, updates $j$. The project-created
   four-plan `strategic_peer_service` fixture is compiled independently with
   dense SciPy LPs, without importing the production compiler. From the
   declared $(0.80,0.85,0.95,0.50)$ profile it stops after four iterations at
   $\epsilon=0.001$ with
   $(0.9793602,0.9761513,1,2/3)$; its high-precision fixed point is
   $(761/777,41/42,1,2/3)$ and the complete protected--focal matrix is checked
   independently. No observations or numerical-result table from the Liang
   article are reproduced. The protected--focal table is not an ordinary
   appraiser--evaluatee matrix, the mean is not a free aggregation rule, and
   `game` is not a `secondary_goal`. The public contract fails closed on
   subproblem failure or maximum iterations, verifies a fresh fixed-point
   residual, reports a suspected two-cycle without treating finite-window
   evidence as a proof, and distinguishes the source's final-score uniqueness
   claim from pairwise multiplier
   uniqueness.
5. **Scale and operations:** selected-projection local RTS and its matched
   one-sided radial VRS scale elasticity are implemented. The fixed-mix Banker
   MPSS and classical CRS physical-capacity reconstructions remain non-public
   prototypes: their three-LP and two-program structures have property checks,
   but the defining full texts, source-native contracts, and independent
   oracles are not frozen. Both are `deferred_to_next_version` and provide no
   public result contract. Directional elasticity, other capacity concepts,
   congestion, scope, and marginal values still need separate result
   contracts even where they reuse convex technology tasks.
6. **Environmental technology:** the source-frozen common-factor CRS and
   activity-specific VRS weak-disposal leaves are now implemented and remain
   distinct. Selective disposal, joint-input, treatment networks, and dynamic
   by-production are separate planned leaves. The legacy `weak` selector is
   only a deprecated bad-output directional equality and must not be cited or
   documented as a complete weak-disposal technology.
7. **Structured governance and productivity:** `GovernanceSpec` must place
   players/authority/information in $C$ and objectives/move order/solution
   concept in $P$, leaving physical topology in $G$. Network and
   state-aware dynamic productivity need source-specific reconstruction
   identities; ordinary black-box Malmquist code cannot be reused by naming
   alone.
8. **Reference and stability diagnostics:** the implemented selected-plan
   frequency diagnostic counts reported active peer edges strictly above the
   source result's peer tolerance and reports self, other, total, and
   total-per-evaluated-organization accounts. It describes the particular
   plans returned by that solve; it is neither a global/maximal reference set,
   a minimum-face result, an influence or outlier diagnostic, nor a ranking
   rule. Those fitted global-reference and minimum-face analyses still need a
   named $A/P$ identity distinct from temporal `reference.global`, while
   influence remains planned. Deterministic stability belongs to $A$, not
   $U$, and must not be reported as sampling or robust-optimization
   uncertainty.
9. **Price and profitability productivity:** the O'Donnell (2010) and
   Zhao--Morita--Maruyama (2019) accounts need separate $V/A$ identities,
   price policies, reconstruction checks, and oracles; neither is an alias
   for technical MPI or for the other.
10. **Statistical implementation:** bootstrap, conditional/partial
   frontiers, second-stage procedures, and structure tests need a statistical
   kernel, deterministic random-state contract, and dimension/DGP warnings.
   Modern productivity inference must bind the exact index/operator,
   aggregation weights, estimator, and panel DGP rather than extending the
   1999 bootstrap by name.
11. **Decision support:** the dedicated review now separates inverse,
   centralized, shared-cost, fixed-sum, merger, bargaining, and scenario
   mechanisms; every executable leaf still needs an equation freeze and
   numerical oracle before public implementation.
12. **Advanced uncertainty:** distributionally robust and Bayesian branches
   remain research-only until an executable leaf, identification claim,
   backend, and validation strategy are frozen.

### 6.2 Dynamic-network source boundaries

The published Tone--Tsutsui dynamic-network source permits a CRS/VRS choice
for each division. Mixed division-level scale assumptions are therefore
source-valid, but the source also states that an overall system RTS
classification cannot be decided in the mixed case. Period and division
weights are nonnegative and sum to one; a zero weight removes an account from
the score, not from the feasibility system.

Every within-period link case preserves supplier--recipient continuity.
`fixed` reproduces the observed handoff at both endpoints; `free` chooses an
endogenous common handoff; `as_input` adds a scored input-style balance owned
by the recipient; and `as_output` adds a scored output-style balance owned by
the supplier. The last two cases assign the scored link term unilaterally inside a
bilaterally coordinated technology. They must not be compiled as
recipient-only or supplier-only feasible sets.

The published equations have also been checked and are internally
inconsistent at the terminal carry-over index: the data definition describes
carry-over observations through $T-1$, while Eq. (9) and the objective
notation index carry-over terms through $T$. The evidence status is therefore
**published-equation-checked**, not unverified. An executable leaf must record
a named boundary resolution, cannot invent a terminal observation or silently
discard a printed term, and must label any resolution as an implementation
policy rather than as an unambiguous source equation.

The domain review's local gap ledger is now promoted to the global audit.
Most records below remain source-qualified **planned/evidence** entries. The
Lewis--Sexton row records the boundary of its now-public forward-quantity
slice and the remaining source scope:

| Candidate | Boundary that must survive implementation |
|---|---|
| `network.sequential.lewis_sexton_2004.forward_radial` | implemented ordered hypothetical-subunit propagation for nonnegative forward quantities, not a simultaneous joint-network solve; reverse quantities, mixed accounts, and site-characteristic adjustments remain gaps |
| `network.input_output.prieto_zofio_2007` | deferred to the next version; sector and intermediate-flow accounts require the unavailable complete primary equations and cannot be inferred from a generic graph label |
| `network.relational.general.kao_2009` / `network.relational.parallel.kao_2012` | source system/process identity and common valuation; the parallel VRS interpretation requires its own guard |
| `network.legacy.independent_two_stage` | diagnostic historical neighbor; stage targets need not be jointly feasible |
| `network.governance.two_stage.liang_cook_zhu_2008` | authority, move order, objective, and solution concept, not topology |
| `panel.multiperiod_aggregative.park_park_2009` | implemented two-phase repeated-period aggregation without a state equation; outside `dynamic.*` |
| `dynamic.optimal_control.sengupta_1999` | discounted capital-path information and objective |
| `dynamic.scale_rts.sueyoshi_sekitani_2005` | source quasi-fixed intertemporal technology |
| `dynamic.weighted_additive.adjustment_cost.aparicio_kapelko_2019` | adjustment-cost and investment slacks with the source units |
| `dynamic.network_lagged_intermediate.chen_2009` | lagged intermediate effect, not a carry-over-role switch on network SBM |

The source DOI ledger is maintained in `reviews/NETWORK_DYNAMIC.md`; the
global presence here closes the planning-visibility gap, not the equation or
oracle gaps.

### 6.3 Book and documentation gap

[`BOOK_ARCHITECTURE.md`](BOOK_ARCHITECTURE.md) fixes the current English
handbook at an 18-chapter route through the principal DEA model families. It
is not a mirror of this source-leaf coverage ledger. A reviewed or implemented
method enters that route only after it passes the independent field-level,
transferability, pedagogical-necessity, and evidence-readiness gates. Adding
an atlas, registry, or API entry therefore does not justify a placeholder
chapter, case, figure, or appendix.

Every public executable leaf needs complete package documentation stating its
constructor, parameters, data contract, score fields, diagnostics, errors,
complexity, examples, and source boundary. The book has a different duty: it
explains the economic question, assumptions, interpretation, evidence, and a
selected DEAPack laboratory for admitted core families. Paper-specific
directions, weights, reference windows, decompositions, combinations, and
application accounts remain in package Documentation even when their code and
validation are complete.

The reader-facing guide in `book/notation.md` presents only the recurring
symbols needed to enter the book; `specs/CONVENTIONS.md` remains the normative
symbol and reporting contract for contributors. Future chapters and API pages
must reference that contract and give an explicit crosswalk whenever a
source-local symbol is retained, rather than creating an unexplained local
notation dialect.

## 7. Dependency-aware review and implementation roadmap

### Wave 0 — identity and evidence discipline

- keep the coverage ledger, registry, reviews, book plan, and public catalog
  synchronized;
- finish source audits before writing model-name classes;
- make compatibility fail closed for unvalidated cross-family compositions;
- retain source, oracle, and implementation status as separate metadata; and
- maintain the decision-support review stream alongside the other domains.

### Wave 1 — close the classical teaching core

Wave 1 is executed as the dependency sequence below rather than as one
acronym batch. An item is not promoted merely because a neighboring compiler
already exists.

| Batch | Capability | Required gate before public code |
|---|---|---|
| **1A — empirical technology closure (completed foundation)** | whole-template FRH radial input/output models before bounded-replication or neighboring non-convex constructions | delivered with one technology for both orientations; integer replication rather than rounded convex weights; FDH/FRH/CRS nesting checks; certified MILP termination, gap and finite-bound policy; independent `Benchmarking` and analytic integer-plan oracles |
| **1B — exact identity closure** | completed input/output Russell aliases; graph Russell remains a separate leaf | an equation-level equivalence proof plus matched technology, domain, reference, score, and target policy |
| **1C — scale, productive size, and short-run capacity** | selected-projection local RTS and matched one-sided radial VRS scale elasticity implemented; fixed-observed-mix Banker MPSS and classical CRS physical capacity removed from the current public wave and retained only as non-public prototypes; both are `deferred_to_next_version`; directional elasticity and congestion remain separate | local RTS and elasticity retain one immutable projection rule, alternate-support interval policy, source sign convention, and shared four-LP kernel with reproduced published oracles. MPSS and physical capacity may be reconsidered only after their defining full texts support an equation freeze and an independent source-level oracle; current synthetic/property checks do not satisfy that gate |
| **1D — bounded and hybrid slack accounts** | 2011 BAM completed for one frozen global nonnegative sample; a declared-calibration input-oriented CRS EBM-I-C evaluator is also completed as a distinct conditional leaf; Enhanced BAM, alternative bound scopes, graph Russell, automatic-calibration EBM, and the wider EBM family remain separate | BAM retains frozen equations, explicit normalization/domain/score/target semantics, and a 12-DMU cross-implementation oracle. The admitted EBM leaf requires an immutable analyst declaration, reproduces all three published examples, and does not claim the unresolved affinity/PCA calibration chain; later leaves require their own evidence |
| **1E — valuation and appraisal protocols** | Tone (2002) super-SBM, the source-frozen Liang--Wu--Cook--Zhu game protocol, the strictly scoped ordinary Pareto--Koopmans completion phase, and the finite input-oriented CRS polyhedral cone-ratio sum-form leaf are delivered. The cone-ratio leaf reproduces 1990 Example 2 through independent source-only multiplier and envelopment oracles; the unresolved Example 3 conflict is recorded but excluded. Andersen--Petersen radial and ordinary CRS cross-efficiency remain deferred internal prototypes. Thompson AR-I/AR-II, Wong--Beasley virtual shares, Roll--Cook--Golany common weights, Doyle--Green Method II/III, and closest or otherwise preference-qualified strong targets remain next-version or source-incomplete leaves | Tone's leaf retains the same-RTS strong-SBM applicability screen, strict positive desirable-quantity domain, CRS three-orientation/VRS-non-oriented boundary, source fractional transformation, published Table 1 scores with source-feasible solver-selected replacement accounts, and missing scores for ineligible or failed rows. The public game protocol retains protected--focal roles, $n^2$ synchronous updates, source-fixed self-inclusive mean, a project-created four-plan dense-LP cross-implementation oracle with no published-table reproduction, fixed-point/suspected-cycle/failure diagnostics, and no `secondary_goal="game"`. Prototype AP and ordinary cross behavior must not be cited as current source-qualified contracts. The public cone-ratio leaf remains input CRS, direct sum form, unit-covariant, and distinct from ordinary slacks or general half-space conversion. Pareto--Koopmans completion remains an embedded radial/DDF/GDF phase-two identity with model-specific scale-anchor disclosure rather than a standalone method or unique management target; later leaves require their own correspondence and failure policy, not a generic wrapper |
| **1F — restricted and unusual data roles** | both provisional Banker--Morey leaves are deferred pending complete defining texts; no source-named implementation is currently queued ahead of integer, interval, zero, or signed-data extensions | reopen only with frozen equations, explicit comparison/technology and target-right effects, translation and invariance domains, optional-backend capability checks, and an independent source oracle |
| **1G — remaining proportional paths** | multiplicative DEA delivered as one shared family/compiler with separate original-1982 and invariant-1983 catalog presets; standard/generalized hyperbolic leaves remain | the multiplicative gate is closed by checked source equations, strict domains, exact analytical/dense-compiler evidence, unit-behavior tests, and explicit source-profile extensions, without a published numerical reproduction claim; remaining hyperbolic leaves still require a source-native value convention, positivity domain, exact relation to GDF/radial endpoints, and an independent nonlinear-transform oracle |

This order closes the questions most readers encounter before specialist
environmental, network, or statistical work while keeping source review,
software reuse, and public claims separate.

### Wave 2 — complete structured production and productivity

- process-link and dynamic-network SBM foundations;
- activity-specific environmental networks, joint-input pollution
  production, and material-balance treatment;
- parallel/shared-resource/general-network measures;
- source-qualified network scale and productivity;
- state-aware dynamic efficiency/productivity; and
- non-radial, environmental, and group/meta productivity extensions of the
  now-delivered O'Donnell--Rao--Battese radial metafrontier operator.

The delivered radial leaf is deliberately narrow: within-group efficiency
means operating performance relative to the declared group's opportunities,
while MTR measures proximity of that group frontier to the broader meta
opportunity frontier. `TGR` is retained only as a historical alias for MTR.
The result is an accounting decomposition, not a causal attribution.

### Wave 3 — next-version statistical foundation

Every executable leaf in this wave first requires a frozen source protocol,
an independent numerical oracle, and a typed result/failure contract. The
items below are review identities, not current public capabilities:

- frontier-compatible bootstrap infrastructure;
- Simar--Wilson Algorithms 1 and 2 as separate procedures;
- conditional DEA/FDH and order-$m$/order-$\alpha$ estimators;
- influence and structure tests; and
- reproducible resampling, parallelism, and uncertainty visualization.

### Wave 4 — advanced and research-only extensions

- interval/IDEA, fuzzy, stochastic, chance-constrained, and robust leaves only
  after one source formulation is frozen for each claim;
- generalized weak-disposal and semi-disposal environmental technologies only
  after their production sets, monotonicity, and competing source claims are
  reconciled;
- optional MILP, conic, and nonlinear backend capability gates;
- inverse, central-allocation, fixed-sum, merger, and bargaining procedures;
  and
- distributionally robust, Bayesian, spatial, and changing-topology methods
  as research-only until their contracts and validation evidence mature.

## 8. Evidence anchors

The audit is anchored by:

- [Charnes, Cooper, and Rhodes (1978)](https://doi.org/10.1016/0377-2217(78)90138-8)
  for the original empirical DEA programme;
- [Cook and Seiford (2009)](https://doi.org/10.1016/j.ejor.2008.01.032)
  for the major classical development streams;
- [Cook, Tone, and Zhu
  (2014)](https://doi.org/10.1016/j.omega.2013.09.004) for the
  study-design choices that must be resolved before a model label is selected;
- [Tone (2001)](https://doi.org/10.1016/S0377-2217(99)00407-5)
  for the standard SBM and its stated relationships;
- [Kao (2014)](https://doi.org/10.1016/j.ejor.2014.02.039)
  for the distinction among network structures and measures;
- [Tone and Tsutsui (2014)](https://doi.org/10.1016/j.omega.2013.04.002)
  for the process-by-period dynamic-network SBM;
- [O'Donnell, Rao, and Battese (2008)](https://doi.org/10.1007/s00181-007-0119-4)
  for group/meta-frontier efficiency and technology ratios;
- [Simar and Wilson (2007)](https://doi.org/10.1016/j.jeconom.2005.07.009)
  for the non-equivalence of the two source bootstrap second-stage
  procedures; and
- [Olesen and Petersen (2016)](https://doi.org/10.1016/j.ejor.2015.07.058)
  for the distinct stochastic-DEA branches.

The broader current check follows
[Mergoni, Emrouznejad, and De Witte (2025)](https://doi.org/10.1016/j.ejor.2024.12.049).
Individual executable leaves continue to require their own defining sources;
a survey is not a substitute for an equation audit.

### 8.1 Top-down handbook triangulation

The leaf-by-leaf source audit is checked from the opposite direction against
four broad reference works. This table is a coverage test, not an authority
for merging models:

| Reference work | Major branches used as audit prompts | DEAPack evidence homes |
|---|---|---|
| [Cooper, Seiford, and Zhu, *Handbook on Data Envelopment Analysis* (2nd ed.)](https://doi.org/10.1007/978-1-4419-6151-8) | basic models and interpretation; RTS; sensitivity; weights; Malmquist; qualitative data; congestion; SBM; chance constraints; bootstrap and statistical tests; internal structure | `STATIC_ECONOMIC.md`, `PRODUCTIVITY.md`, `WEIGHTS_SPECIAL_DATA_HETEROGENEITY.md`, `STATISTICS_UNCERTAINTY.md`, and the network reviews |
| [Zhu, *Data Envelopment Analysis: A Handbook of Models and Methods*](https://doi.org/10.1007/978-1-4899-7553-9) | distance/value duality; cross appraisal; integer data and technologies; weight restrictions and trade-offs; facets; scale elasticity; benchmarking; fuzzy data; non-homogeneous units; partial incidence; super-efficiency; undesirable measures; translation; stochastic envelopment; global indexes | all nine domain reviews, with identity boundaries recorded in `METHODS.md` |
| [Cook and Zhu, *A Handbook of Modeling Internal Structure and Network*](https://doi.org/10.1007/978-1-4899-8068-7) | two-stage decomposition and pitfalls; series, parallel, shared-resource, hierarchical, multistage, and dynamic structures; network scale; bargaining; SBM; open networks; undesirable outcomes | `NETWORK_DYNAMIC.md`, `NETWORK_ADDITIVE.md`, `NETWORK_SBM.md`, `ENVIRONMENTAL.md`, and `DECISION_SUPPORT.md` |
| [Sickles and Zelenyuk, *Measurement of Productivity and Efficiency*](https://doi.org/10.1017/9781139565981) | primal and dual production economics; efficiency; productivity indexes and aggregation; envelopment estimators; DEA/FDH statistical foundations; dynamic models; measurement and software | `UNIFIED_FRAMEWORK.md`, `PRODUCTIVITY.md`, `STATISTICS_UNCERTAINTY.md`, the result contract, and performance policy |

The triangulation supports the present umbrella coverage, but it also makes
the remaining depth gaps visible: facet and multiplier diagnostics,
directional scale and congestion, broader structured production,
complete-productivity accounts, and estimator-compatible inference still need
source-qualified executable leaves.
