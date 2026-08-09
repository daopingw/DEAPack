# DEAPack canonical method registry

This is the implementation-facing registry for DEAPack 2.0. It is not the
literature review and it is not the mathematical notation contract.

- [`METHOD_UNIVERSE.md`](METHOD_UNIVERSE.md) defines the source-backed scope of
  the field.
- [`METHOD_COVERAGE_AUDIT.md`](METHOD_COVERAGE_AUDIT.md) provides the
  cross-domain coverage ledger and separates conceptual, executable, and
  validation completeness.
- [`reviews/`](reviews/) maintains domain-level evidence reviews and
  oracle-status audits.
- [`UNIFIED_FRAMEWORK.md`](UNIFIED_FRAMEWORK.md) defines how methods are
  composed and when historical names may be merged.
- this file assigns stable canonical IDs, priorities, implementation states,
  public names, and validation expectations;
- [`CONVENTIONS.md`](CONVENTIONS.md) defines symbols and result-value
  conventions.
- [`ECONOMIC_MODEL_DESIGN.md`](ECONOMIC_MODEL_DESIGN.md) and
  [`PATH_MODEL_DESIGN.md`](PATH_MODEL_DESIGN.md) freeze implementation
  contracts for economic and non-linear/path-based families before their
  public code is admitted.

The registry is maintained in Markdown until the IDs, relationships, and
status vocabulary are stable. It may later become validated YAML, but it will
not become a mathematical modeling language or enter the per-DMU solver hot
path.

## 1. Registry vocabulary

### 1.1 Entry kinds

| Kind | Meaning |
|---|---|
| `family` | a reusable technology, measure, or analysis family |
| `variant` | a substantively distinct member sharing most machinery with a family |
| `specialization` | a named partial parameter choice that does not fix a complete executable study |
| `preset` | a historically recognized fixed composition of components |
| `operator` | an analysis that combines one or more fitted model tasks |
| `procedure` | an inferential, diagnostic, or decision workflow |
| `technology` / `estimator` | a production-set construction or a sampling-boundary construction on its own composition axis |
| `policy` / `protocol` | a reusable reference, valuation, or appraisal rule |
| `assumption` / `restriction` / `formulation` | one declared axiom or constraint component, never a complete model by itself |
| `alias record` | provenance for a historical name merged into one canonical executable entry |
| `neighbor` | an adjacent method or use of DEA machinery that is not a core production-efficiency family |

An API alias is normally a name attached to an entry, not a second executable
entry. `CCR` and `BCC` are specializations because they fix returns to scale
but not orientation or target policy. `CCR-I`, `CCR-O`, `BCC-I`, and `BCC-O`
are complete historical presets once their score and target conventions are
also fixed. A direct Python assignment such as `SBM = SlacksBasedDEA` is an API
alias for one canonical entry.

### 1.2 Priority, release tier, and status

These fields answer different questions:

- **priority**: theoretical/software dependency order (`P0`, `P1`, `P2`);
- **release tier**: intended delivery group (`0` through `3`);
- **implementation**: `planned`, `prototype`, `partial`, `implemented`, or
  `excluded`;
- **API**: `none`, `experimental`, or `public`;
- **verification**: `none`, `synthetic`, `property`,
  `literature_oracle`, or `cross_implementation`;
- **documentation**: `none`, `atlas`, `api`, or `book`.

The public roadmap additionally projects entries into three reader-facing
delivery classes: **implemented** for an exact public leaf, **planned** for a
source-qualified implementation route, and **research-only** for an important
branch whose executable identity, backend, or validation strategy is not yet
stable. This projection does not replace the granular implementation field:
an internal `prototype` remains planned to users, while an implemented leaf
does not promote its whole family. Evidence and oracle status remain
independent of delivery class.

Promotion into the current release is fail-closed. A candidate must have both
an original or authoritative defining source whose equations and economic
semantics are frozen, and an independent numerical oracle or equivalent exact
executable certificate whose claim boundary is explicit. If either side is
not closed, the candidate belongs only in the next-version backlog and source
protocol: implementation convenience, a familiar acronym, a secondary
reconstruction, or agreement with the production implementation's own output
cannot promote it. A development-tree implementation that has not yet passed
this gate is release-audit debt and must either close the evidence or be
demoted before a stable release.

An implemented preset does not imply that its whole family is implemented.
For example, Tone's standard input-, output-, and non-oriented SBM presets are
implemented while weighted, zero/signed-data, and other SBM variants keep the
broader family partial.

### 1.3 Canonical record

Every machine-readable method record contains:

```text
id, kind, base, title, decision_question
composition:
  context, graph, data_roles, technology, estimator, reference,
  performance, valuation, evaluation_protocol, analysis, uncertainty
parameters:
  fixed, defaults, exposed
names:
  historical names, API symbols, spelling aliases, citations
compatibility:
  requires, supports, forbids
result:
  native value, direction, domain, transformations, components
status:
  priority, release tier, implementation, API, publication scope,
  verification, documentation
implementation:
  canonical symbol, module, compiler/backend dependencies
validation:
  defining/review sources, tests, literature oracles, properties,
  failure cases, cross-solver checks, performance benchmarks
relations:
  target, level, relation type, conditions, evidence
```

An equivalence level belongs to a directed relationship between two entries,
not to a method in isolation. Network SBM has a Level C relationship to
black-box SBM along the measure/technology dimension, while its graph
compiler has a Level D relationship to a black-box compiler.

The current shadow release contains 67 machine records and 43 typed relation
records. The machine inventory comprises 63 implemented/public records--62
`method_id` records and the public APZ `preset_id` record--plus four non-public
`method_id` prototypes held behind the source gate. The discovery catalog
contains those 62 public methods, five constructor/reporting
`specialization_id` entries, and eight `preset_id` entries, for 75 catalog
identities. Seven presets remain catalog-only recipes: the four classic radial
constructors, the output-oriented CRS FGNZ Malmquist core, and the 1982
original and 1983 invariant multiplicative recipes. APZ additionally has its
own machine preset record because its capped-bad technology and provenance
must be serialized with the composed public analysis.

## 2. Composition axes

A fitted study expands to eleven composition axes:

1. decision context and managerial control;
2. production-system graph;
3. economic data roles and domains;
4. empirical technology and production restrictions;
5. frontier estimator;
6. benchmark/reference policy;
7. technical improvement plan or economic performance criterion;
8. valuation and preference information;
9. evaluation protocol and alternate-optimum policy;
10. analytical operator;
11. uncertainty and inference design.

Result-value and reporting conventions form a separate output contract over
that composition; they do not add a twelfth study axis to `expanded_spec`.

The third axis has a mandatory nested representation/domain contract.  Each
modeled field records, in addition to its economic role:

```text
data_roles:
  representation:
    measurement_scale: cardinal | ordinal | nominal | ratio
    sign_domain: nonnegative | signed
    divisibility: continuous | integer | binary
    observation_status: exact | interval | fuzzy | missing
    controllability: discretionary | fixed | bounded
```

These are structured subfields of `data_roles`, not a twelfth top-level axis
and not an immediate change to the machine-registry schema.  A leaf may
refine the vocabulary, but it must not leave a relevant property implicit.
Economic role and representation are orthogonal: an undesirable output can
be exact and nonnegative, while a desirable output can be signed or only
interval-observed.

Historical names are recipes over these components. They never justify a
duplicate solver by themselves.

## 3. Technology and structure registry

| Canonical ID | Kind | Economic/structural meaning | Status | Priority / tier |
|---|---|---|---|---|
| `technology.convex_envelopment` | family | convex combinations of observed activities with explicit RTS and ordinary disposal | implemented | P0 / 0 |
| `technology.meta.nonconvex_union` | technology | attainable in at least one declared group technology without cross-group convexification | planned | P1 / 2 |
| `technology.meta.pooled_convex` | technology component | pooled or convexly enveloped group activities under a declared meta-technology construction | implemented internally by the O'Donnell--Rao--Battese radial metafrontier leaf; not a standalone public operator or constructor | P0 / 2 |
| `technology.fdh` | family | observed activities plus free disposal without convexification | implemented/public | P0 / 2 |
| `technology.fdh.scale_extrapolation` | variant | source-qualified CRS/NIRS/NDRS rescaling of individual observed activities without cross-activity convexification | planned | P1 / 2 |
| `technology.fch.binary_subset_aggregation` | technology | any observed operating template may be included at most once in a nonempty coordinated aggregate; unlike FDH, several distinct templates may be combined, but unlike FRH they may not be replicated repeatedly and unlike CCR they may not be fractionally divided | implemented/public through the Green--Cook radial FCH leaf; primary-source formulation, independent exact finite-subset certificate, and separate nesting/non-nesting evidence frozen | P0 / 0 |
| `technology.frh` | technology | nonnegative integer copies of observed operating templates may be combined under free disposal; whole templates are replicable, but arbitrary fractional plants, branches, or service lines are not | implemented/public through the radial FRH leaf; source equations and a project-case analytical certificate are frozen | P0 / 1 |
| `technology.frh.bounded_replication` | variant | source-qualified finite limits on the number of copies of each observed template change the maintained opportunity set | planned as a distinct leaf; never a numerical option on unbounded FRH | P1 / 2 |
| `technology.multiplicative` | family | shared piecewise log-linear/multiplicative envelopment with a 1982 log-conic variant and a 1983 unit-invariant log-convex variant; neither is ordinary CRS/VRS envelopment or preprocessing ordinary DEA by logging its data | implemented through the public `static.multiplicative` family and one shared sparse log-space compiler | P1 / 2 |
| `technology.production_tradeoff` | family | declared marginal/substitution trade-offs enlarge or restrict the attainable production set | planned | P1 / 2 |
| `technology.partial_incidence` | family | a declared input--output incidence/resource-sharing matrix replaces universal input-to-output participation | planned | P2 / 3 |
| `technology.partial_incidence.imanirad_cook_aviles_zhu_2015` | preset | source-qualified partial input--output incidence defining which resources participate in which services | planned | P1 / 2 |
| `technology.ratio.olesen_petersen_podinovski_2015` | technology/preset | ratio and percentage factors embedded in a production technology with compatible convexification rather than treated as ordinary quantities | planned | P1 / 2 |
| `technology.selective_convexity.podinovski_2005` | technology/preset | source-qualified selective convexity for technologies whose declared factors or activities must not all be averaged together | planned | P2 / 3 |
| `technology.integer_discrete.kuosmanen_kazemi_matin_2009` | technology/preset | natural-disposability and natural-divisibility integer production technology with explicit integrality and RTS axioms | planned; requires MILP compiler | P1 / 2 |
| `graph.black_box` | family | one transformation from external inputs to final outputs | implemented | P0 / 0 |
| `graph.series` | family | linked two- or multi-stage processes | implemented/public two-stage subset; broader serial graphs planned | P1 / 2 |
| `graph.parallel` | family | parallel activities with separate or shared resources | planned | P1 / 2 |
| `graph.general_network` | family | directed process graph with explicit link accounting | implemented/public declarations and semantic layout; executable measure subsets expanding | P1 / 2 |
| `graph.dynamic_carryover` | family | desirable, undesirable, free, or fixed quantities connect periods | implemented/public Tone--Tsutsui subset; broader transition systems planned | P1 / 2 |
| `graph.intertemporal_economic` | family | non-executable structural umbrella for investment, quasi-fixed capital, adjustment costs, information, and terminal conditions | planned | P2 / 3 |
| `graph.dynamic_network` | family | internal process links and temporal links jointly constrain the plan | implemented/public Tone--Tsutsui subset; alternative dynamic-network technologies planned | P2 / 3 |
| `graph.hierarchical` | family | nested or overlapping organizational levels | planned | P2 / 3 |
| `graph.shared_flow` | family | activities share inputs, outputs, or other resource flows without thereby becoming a serial intermediate-product network | planned | P1 / 2 |
| `graph.multi_activity` | family | one organization operates several connected or separable activities/plants | planned | P2 / 3 |

`graph.general_network` records nodes, external variables, directed links,
resource pools, node technologies/RTS, common or node-specific intensities,
and link-conservation rules. It describes the production process, not who is
allowed to choose the operating plan. Authority, objectives, move order,
information, and solution concept belong to `evaluation.governance`; system
aggregation belongs to the performance/evaluation contract. “Two-stage” is
not a sufficient model specification.

`graph.intertemporal_economic` is a structural umbrella and never a fitted
result `method_id`. Executable dynamic leaves retain their source-qualified
production, investment, or carry-over lineage.

`technology.meta.pooled_convex` is likewise a composition component rather
than a fitted method. The public radial metafrontier operator invokes it under
VRS (and the corresponding pooled cone under CRS); users do not fit a generic
meta-technology constructor independently. Other meta-technology constructions
remain separate source-qualified candidates.

### 3.1 Frontier estimator registry

| Canonical ID | Kind | Sampling construction | Status | Priority / tier |
|---|---|---|---|---|
| `estimator.full.dea` | estimator | full empirical convex envelopment under the declared technology axioms | implemented/public metadata | P0 / 0 |
| `estimator.full.fdh` | estimator | full empirical non-convex free-disposal hull | implemented/public metadata | P0 / 2 |
| `estimator.full.fch` | estimator | full binary-subset aggregation hull generated by a nonempty zero-or-one selection of observed templates under free disposal | implemented/public through the Green--Cook radial FCH leaf; componentwise binary, bound, constraint, and MIP-gap certification | P0 / 0 |
| `estimator.full.frh` | estimator | full empirical integer-replication hull generated by all nonnegative integer combinations of observed templates under free disposal | implemented/public through the radial FRH leaf; both orientations are checked on the neutral `integer_coordination_hulls` case | P0 / 1 |
| `estimator.partial.order_m` | estimator | expected best performance in a random comparison set of size $m$ | planned | P1 / 2 |
| `estimator.partial.order_alpha` | estimator | dominance-probability partial frontier | planned | P1 / 2 |
| `estimator.partial.order_alpha.aragon_daouia_thomas_agnan_2005` | estimator/preset | source-qualified conditional-quantile order-$\alpha$ frontier with explicit quantile and support policy | planned | P1 / 2 |
| `estimator.conditional.dea` | estimator | conditional convex frontier under declared operating conditions and bandwidth policy | planned | P1 / 2 |
| `estimator.conditional.fdh` | estimator | conditional non-convex frontier under declared operating conditions and bandwidth policy | planned | P1 / 2 |
| `estimator.neighbor.scnls.kuosmanen_johnson_2010` | neighbor/exact representation | sign-constrained nonparametric least-squares representation that coincides with DEA only under the paper's one-sided sign, shape, graph, and loss restrictions | comparison/evidence only; no separate DEA solver | P2 / 3 |
| `estimator.neighbor.cnls.kuosmanen_2008` | neighbor | convex nonparametric least-squares regression with a statistical loss and residual contract not fixed by ordinary DEA | comparison only | P2 / 3 |
| `estimator.neighbor.cqr` | neighbor family | convex/shape-constrained quantile regression frontier with a quantile-loss and conditional-function interpretation | comparison only; source-qualified leaves required | P2 / 3 |
| `estimator.neighbor.cer` | neighbor family | convex/shape-constrained expectile regression frontier with an asymmetric least-squares interpretation | comparison only; source-qualified leaves required | P2 / 3 |

Technology axioms state what production opportunities are maintained;
estimators state how sample observations construct a boundary under those
axioms. Bootstrap and other inference procedures operate on a supported
estimator and do not replace this axis.

The SCNLS entry records a conditional exact representation, not a blanket
merger of DEA with CNLS.  Relaxing the one-sided sign restriction, introducing
two-sided regression residuals, or changing to quantile/expectile loss changes
the estimator and inferential target.  See
[Kuosmanen (2008)](https://doi.org/10.1111/j.1368-423X.2008.00239.x),
[Kuosmanen and Johnson (2010)](https://doi.org/10.1287/opre.1090.0722),
and the CQR/CER analysis in
[Dai et al. (2023)](https://doi.org/10.1016/j.ejor.2023.04.004).

## 4. Static technical-performance registry

| Canonical ID | Kind | Public/historical names | Status | Priority / tier |
|---|---|---|---|---|
| `static.radial` | family | Farrell radial DEA | implemented/public core; exact phase-one certificates cover input/output orientation under CRS/VRS/NIRS/NDRS, exact phase-two cases cover CRS and VRS input/output slack semantics, and an independent dense compiler cross-checks all eight branches in score-only/slack-completion execution; optional source-neutral observation-specific peer eligibility is public on `RadialDEA`, `CCR`, `BCC`, and the four fixed `CCRInput`/`CCROutput`/`BCCInput`/`BCCOutput` recipes, where its declared candidates intersect rather than replace the base `ReferenceSpec`; fitted appraisal is reported from actual self-membership; the policy infers no category and creates no Banker--Morey identity; each claim is explicitly bounded to its fixture and reference contract; no published-data reproduction claimed; extensions remain separate | P0 / 0 |
| `static.radial.fdh` | variant | input/output radial FDH; API symbols `FreeDisposalHullDEA` and `FDH` | implemented/public | P0 / 2 |
| `static.radial.fch.green_cook_2004` | variant | input/output radial efficiency on the Green--Cook free coordination/free aggregation hull, where several distinct observed templates may be coordinated but each is available at most once; API symbols `FreeCoordinationHullDEA` and `FCH`; historical `FAH` is provenance only and is not exposed because it also means Ray's distinct free affordability hull | implemented/public; primary-source formulation plus an independent exact finite-subset certificate for both orientations on the four-organization fixture, FDH--FCH--FRH--CCR nesting, FCH/VRS non-nesting, nonnegative-component/positive-aggregate domain, zero-component semantics, unit-invariance, targets, and fail-closed binary-solution evidence; no published numerical-table reproduction or third-party cross-implementation claimed | P0 / 0 |
| `static.radial.frh` | variant | input/output radial efficiency on the free-replicability hull; API symbols `FreeReplicabilityHullDEA` and `FRH`; replication counts are integer reference activities, not rounded convex weights | implemented/public; analytic, property, failure, nesting, and project-case integer-portfolio evidence | P0 / 1 |
| `static.radial.crs` | specialization | CCR constructor fixing CRS but not orientation or target policy | implemented/public | P0 / 0 |
| `static.radial.vrs` | specialization | BCC constructor fixing VRS but not orientation or target policy | implemented/public | P0 / 0 |
| `static.radial.crs.input` | preset | complete CCR-I recipe; API symbol `CCRInput`; fixes CRS, input orientation, native $\theta$, and `compute_slacks=True` with DEAPack's row-scaled lexicographic slack/target completion | implemented/public catalog preset over `static.radial`; accepts the family's optional source-neutral peer-eligibility policy; the phase-two target selector is an explicit package policy, not a claim that the historical paper uniquely selected this target | P0 / 0 |
| `static.radial.crs.output` | preset | complete CCR-O recipe; API symbol `CCROutput`; fixes CRS, output orientation, native $\phi$ with displayed efficiency $1/\phi$, and `compute_slacks=True` with DEAPack's row-scaled lexicographic slack/target completion | implemented/public catalog preset over `static.radial`; accepts the family's optional source-neutral peer-eligibility policy; the phase-two target selector is an explicit package policy, not a claim that the historical paper uniquely selected this target | P0 / 0 |
| `static.radial.vrs.input` | preset | complete BCC-I recipe; API symbol `BCCInput`; fixes VRS, input orientation, native $\theta$, and `compute_slacks=True` with DEAPack's row-scaled lexicographic slack/target completion | implemented/public catalog preset over `static.radial`; accepts the family's optional source-neutral peer-eligibility policy; the phase-two target selector is an explicit package policy, not a claim that the historical paper uniquely selected this target | P0 / 0 |
| `static.radial.vrs.output` | preset | complete BCC-O recipe; API symbol `BCCOutput`; fixes VRS, output orientation, native $\phi$ with displayed efficiency $1/\phi$, and `compute_slacks=True` with DEAPack's row-scaled lexicographic slack/target completion | implemented/public catalog preset over `static.radial`; accepts the family's optional source-neutral peer-eligibility policy; the phase-two target selector is an explicit package policy, not a claim that the historical paper uniquely selected this target | P0 / 0 |
| `static.radial.restricted_rts` | deferred literature-leaf candidate | NIRS/NDRS remain tested technology-parameter paths of the public `static.radial` core; this ID would instead denote a separately source-qualified historical recipe | no standalone public constructor, catalog identity, or machine method record; an original or authoritative source fixing the independent leaf and its oracle has not been frozen, so the leaf is deferred to the next version | — |
| `performance.hyperbolic` | family | one canonical multiplicative adjustment path coordinating input contraction and output expansion; data roles and technology determine whether the application is ordinary or environmental | non-executable discovery family; source-qualified leaves required | P1 / 2 |
| `static.hyperbolic` | recipe family | `performance.hyperbolic` composed with ordinary productive inputs, desirable outputs, and a declared static technology | deferred family boundary; no duplicate core solver | — |
| `static.hyperbolic.standard_reciprocal` | deferred candidate | standard reciprocal resource-contraction/service-expansion path, conditionally an exact score transform of Chavas--Cox GDF at `alpha=0.5` | defining source-native score, domain, target policy, and independent hyperbolic oracle are not frozen; deferred to next version with no public API or machine record | — |
| `static.hyperbolic.generalized_path` | variant | source-qualified generalized hyperbolic adjustment paths | planned | P1 / 2 |
| `static.generalized_distance.chavas_cox` | family | Chavas--Cox proportional resource/service contract; API symbols `GeneralizedDistanceDEA`, `ChavasCoxGDF`, and `GDF` | implemented/public for CRS/VRS; exact radial reductions plus certified interior-VRS feasibility search; fixed cross-implementation oracle | P1 / 2 |
| `static.multiplicative` | family | shared positive-data multiplicative-efficiency family; API symbol `MultiplicativeDEA`; one sparse log-space compiler serves the source-frozen 1982 original and 1983 invariant variants | implemented/public; strictly positive ordinary inputs/desirable outputs only, with the stricter 1982 greater-than-one domain and no undesirable outputs; the 1983 variant is invariant to independent positive unit rescaling whereas the 1982 variant is not; an independent dense source compiler and exact two-DMU analytical oracle certify both variants, but no published numerical reproduction is claimed; global cross-section is the source profile and panel/non-global references are labelled package extensions | P1 / 2 |
| `static.multiplicative.original.charnes_etal_1982` | preset | original C2S2 log-conic recipe; API symbol `C2S2MultiplicativeDEA`; no convexity identity, all input/output quantities strictly greater than one, and exponent floor fixed at one | implemented/public catalog preset over `static.multiplicative`; unit-dependent source identity, not an ordinary CRS label and not a separate compiler or machine method record | P1 / 2 |
| `static.multiplicative.invariant.charnes_etal_1983` | preset | invariant log-convex piecewise Cobb--Douglas recipe; API symbol `InvariantMultiplicativeDEA`; `sum(lambda)=1`, strictly positive inputs/outputs, and a positive exponent-floor score-power convention | implemented/public catalog preset over `static.multiplicative`; invariant to independent positive coordinate rescaling and not a VRS alias, separate compiler, or machine method record | P1 / 2 |
| `static.directional_distance` | family | DDF, directional input/output distance | implemented/public; optional source-neutral peer eligibility intersects the base reference plan, preserves the declared direction policy, reports actual self/mixed/external appraisal, and creates no environmental or categorical identity | P0 / 0 |
| `static.subvector_distance` | deferred family candidate | component-specific adjustment rights; source-qualified input/output, short-run, and energy leaves remain distinct | exact primary programmes, target semantics, and a numerical oracle are not frozen; deferred to next version with no public API or machine record | — |
| `static.multi_directional_efficiency` | procedure | MEA workflow: variable-specific potential tasks, ideal-direction construction, reference policy, and declared aggregation | planned | P1 / 2 |
| `static.range_directional` | family | ideal-point/sample-range directional measures for compatible signed data | partial; the original 2004 RDM leaf is implemented/public, while adjacent signed-data formulations remain separate | P1 / 2 |
| `static.additive` | family | classic VRS unit-weight additive DEA plus configurable fixed positive slack weights over declared RTS/reference policies; `WeightedAdditiveDEA` is a discoverability alias, not a separate historical method | implemented/public; Charnes et al. (1985) analytical certificate is limited to equations (4.5)--(4.6), a self-inclusive cross-section, VRS, unit weights, ordinary nonnegative inputs/desirable outputs, and exact scores/slacks/targets/peers; fixed non-unit weights, CRS/NIRS/NDRS, panel/non-global references, and a restricted peer-eligibility population are package extensions without that source identity; the latter intersects the base reference plan and reports actual self/mixed/external appraisal; equation (5.7), separately named unsupported leaves, and published numerical reproduction are `deferred_to_next_version` | P0 / 0 |
| `static.ram` | preset | Cooper--Park--Pastor VRS range-adjusted measure; API symbols `RangeAdjustedDEA` and `RAM` | implemented/public; equations (17), (18), and (20)--(23) are frozen for one self-inclusive cross section and finite signed resource/desirable-service data; the source's zero-range omission/zero-slack rule is implemented equivalently by a zero weight plus the matched-population VRS balance; optional peer eligibility retains one full-data, pre-eligibility range normalization while the effective VRS comparison population is the global base population intersected with the declared candidates, and this restricted case is labelled `deapack_ram_extension`; an independent dense LP plus exact upper-bound fixture certifies the source profile; temporal/custom base references and other RTS, environmental, network, dynamic, super-efficiency, and economic interpretations remain deferred | P0 / 0 |
| `static.bam` | family | 2011 bounded-adjusted measure with DMU-specific one-sided sample-range weights, explicit slack bounds, and CRS/VRS/NIRS/NDRS; API symbols `BoundedAdjustedDEA` / `BAM`; Enhanced BAM remains a separate leaf | implemented/public; primary equations checked and 12-DMU VRS/CRS scores cross-implemented with archived `additiveDEA` and an independent SciPy/HiGHS LP | P1 / 2 |
| `static.russell` | family | input/output/graph Russell; the classic input and output formulations are publicly discoverable as `InputRussell` and `OutputRussell`, exact aliases of the matched oriented Tone leaves only under the same strictly positive domain, technology, RTS, reference, equal-dimension normalization, reciprocal output-score, and target policy; graph Russell remains distinct and planned | partial: input/output merged into implemented canonical leaves; graph planned | P1 / 2 |
| `static.erg` | alias record | enhanced Russell graph (ERG/ERGM) | merged into `static.sbm.nonoriented.tone2001` on the standard positive-data domain; public alias `ERG` | P0 / 0 |
| `static.sbm` | family | slacks-based measures | partial | P0 / 0 |
| `static.sbm.nonoriented.tone2001` | canonical preset | standard non-oriented ERG/SBM formulation; API aliases `SBM` and `ERG`; Pastor--Ruiz--Sirvent and Tone lineages retained in provenance | implemented/public; optional source-neutral peer eligibility intersects the base reference plan and records the actual self/mixed/external appraisal | P0 / 0 |
| `static.sbm.input.tone2001` | preset | input-oriented Tone SBM: normalized input-excess account with outputs maintained; API symbols `InputOrientedSlacksBasedDEA`, `InputSBM`, and exact-domain historical alias `InputRussell`; score one certifies the input side only and the output-side target is solver-selected | implemented/public with optional source-neutral peer eligibility and actual self/mixed/external appraisal; property evidence present, published oriented numerical oracle not located | P0 / 1 |
| `static.sbm.output.tone2001` | preset | output-oriented Tone SBM: reciprocal normalized output-expansion account with inputs maintained; API symbols `OutputOrientedSlacksBasedDEA`, `OutputSBM`, and exact-domain historical alias `OutputRussell`; the direct Russell expansion optimum remains `output_expansion_factor`, score one certifies the output side only, and the input-side target is solver-selected | implemented/public with optional source-neutral peer eligibility and actual self/mixed/external appraisal; property evidence present, published oriented numerical oracle not located | P0 / 1 |
| `static.ebm` | deferred family boundary | Tone--Tsutsui epsilon-based measures; orientation leaves and the earlier cost-share epsilon lineage remain distinct | the broad automatic-calibration family remains deferred: no affinity/PCA calibration, tie rule, projection selector, or wider orientation/RTS identity is exposed | — |
| `static.ebm.input.tone_tsutsui_2010.crs` | deferred full source identity | input-oriented CRS Tone--Tsutsui EBM with the source affinity/PCA calibration chain | automatic calibration remains deferred to the next version; the executable declared evaluator below never claims this full identity | — |
| `static.ebm.input.tone_tsutsui_2010.crs.declared` | source-qualified preset | declared-calibration EBM-I-C; API symbols `InputOrientedEpsilonBasedDEA` and `DeclaredEBMCalibration` | implemented/public conditional evaluator for one strictly positive ordinary-input/output cross-section, CRS, input orientation, and one full self-inclusive reference technology; analyst-declared normalized weights, epsilon, and provenance are mandatory; theta remains free, targets are solver-selected, epsilon zero matches the matched CCR score, epsilon one is not SBM, and automatic affinity/PCA calibration is explicitly not run | P1 / 1 |
| `static.holder_distance` | family | Hölder/$L_p$ distance measures | planned | P1 / 2 |
| `analysis.facet_exfa` | procedure | full-dimensional efficient-facet identification for targets, marginal trade-offs, and model diagnostics | planned | P2 / 3 |

Input/output orientation, direction, adjustable subvector, returns to scale,
and reference membership are parameters or composition fields. They are not
stand-alone technologies.

The three Tone SBM presets share the same production technology, reference
plan, balance rows, and sparse compiler. Their objectives, valuation sides,
and target guarantees differ, so the oriented leaves have Level B
`variant_of` relationships to the non-oriented leaf rather than alias or exact
score-transform relationships.

## 5. Economic objectives, scale, and operations

| Canonical ID | Kind | Decision question | Status | Priority / tier |
|---|---|---|---|---|
| `economic.cost` | family | minimum input expenditure for required outputs; API symbol `CostEfficiency` | implemented/public with CRS/VRS and complete strictly positive input prices | P1 / 2 |
| `economic.revenue` | family | maximum output revenue from available inputs; API symbol `RevenueEfficiency` | implemented/public with CRS/VRS and complete strictly positive output prices | P1 / 2 |
| `economic.indirect` | family | budget- or revenue-constrained re-optimization when management may change the input or output mix before assessing technical opportunity | planned | P1 / 2 |
| `economic.cost_indirect.free_affordability.ray_1997` | proposed preset | Ray's free-affordability-hull cost-indirect technology for settings with normalized input prices but unavailable input quantities; historical acronym `FAH`, which is not Green--Cook binary-subset coordination | planned/evidence proposal only; source DOI `10.1023/A:1007747407212`, equations and oracle not yet frozen | P2 / 3 |
| `economic.indirect_output.budget.fare_grosskopf_lovell_1993` | preset | maximum attainable output/service account under a declared input budget; distinct from cost minimization at fixed outputs and revenue maximization at a fixed input vector | planned | P1 / 2 |
| `economic.profit` | family | non-executable discovery umbrella for maximum net value and source-qualified profit decompositions | partial; maximum-profit leaf public | P1 / 2 |
| `economic.profit.maximum` | operator | maximum net value when both inputs and outputs may change; raw profit gap with no profit ratio; API symbol `ProfitEfficiency` | implemented/public for finite VRS convex hull with shutdown excluded | P1 / 2 |
| `economic.profit.maximum.shutdown` | preset | maximum profit on a technology that explicitly admits inactivity/origin; not the ordinary VRS simplex | planned | P2 / 3 |
| `economic.profit.decomposition` | family | non-executable umbrella for source-qualified technical/allocative explanations of a common raw profit gap | partial; CCF leaf public | P1 / 2 |
| `economic.profit.decomposition.radial` | family | radial technical component with its source-qualified profit decomposition and normalization | planned | P2 / 3 |
| `economic.profit.decomposition.russell` | family | Russell technical component with matched profit decomposition | planned | P2 / 3 |
| `economic.profit.decomposition.weighted_additive.cooper_etal_2011` | preset | weighted-additive technical shortfall and source-defined profit decomposition | planned | P2 / 3 |
| `economic.profit.decomposition.sbm.aparicio_ortiz_pastor_2017` | preset | SBM/ERG technical component with the paper's profit decomposition | planned | P2 / 3 |
| `economic.profit.decomposition.holder.briec_lesourd_1999` | family | metric/Hölder distance and profit-duality decomposition under a declared norm | planned; nonlinear/SOS backend may be required by norm | P2 / 3 |
| `economic.profit.decomposition.modified_ddf.lost_profit_on_outlay.aparicio_pastor_ray_2013` | preset | modified directional normalization expressing lost profit relative to declared outlay/earnings | planned | P2 / 3 |
| `economic.profit.decomposition.reverse_ddf.pastor_etal_2016` | preset | source-qualified reverse-DDF profit decomposition | planned | P2 / 3 |
| `economic.profit.decomposition.general_direct.pastor_zofio_aparicio_pastor_2023` | preset | direct profit decomposition based on a declared technical projection rather than an inferred generic duality | planned | P2 / 3 |
| `economic.nerlovian` | family | non-executable umbrella for maximum-profit shortfalls normalized by a price-valued direction | partial; CCF leaf public | P1 / 2 |
| `economic.nerlovian.ccf1998` | preset | Chambers--Chung--Färe normalized profit shortfall with matched DDF technical term and additive allocative residual; API symbols `NerlovianProfitInefficiency`, `NerlovianEfficiency` | implemented/public for finite VRS convex hull; cross-implementation oracle | P1 / 2 |
| `economic.profit.directional.endogenous.zofio_pastor_aparicio_2013` | preset | endogenous profit-maximizing direction and its either-technical-or-allocative accounting rule | planned; distinct from an exogenous CCF direction | P2 / 3 |
| `economic.profitability` | family | non-executable umbrella for source-qualified return relative to expenditure | partial; return-to-dollar leaf and matched GDF decomposition public | P1 / 2 |
| `economic.profitability.return_to_dollar` | operator | observed and maximum output value per unit of input expenditure, with relative profitability efficiency; API symbols `ReturnToDollarEfficiency`, `ProfitabilityEfficiency` | implemented/public for CRS/VRS, complete positive prices, and positive candidate costs/revenues; direct extreme-ratio kernel and cross-implementation oracle | P1 / 2 |
| `economic.profitability.generalized_distance` | discovery alias | historical profitability/GDF wording; executable technical GDF and economic decomposition keep separate canonical IDs | discovery alias only; never a generic executable switch | P1 / 2 |
| `economic.profitability.lost_profit_on_outlay` | discovery alias | historical profitability-normalization wording for the source-qualified modified-DDF method | points to `economic.profit.decomposition.modified_ddf.lost_profit_on_outlay.aparicio_pastor_ray_2013`; planned | P2 / 3 |
| `analysis.allocative_decomposition.profitability_gdf.zofio_prieto_2006` | operator | $PE=TE^{CRS}_{GDF}AE=TE^{VRS}_{GDF}SE\,AE$ under one matched Chavas--Cox bearing parameter and reference policy; API symbols `GDFProfitabilityDecomposition`, `ProfitabilityDecomposition` | implemented/public; internally fits return-to-dollar plus CRS/VRS GDF, preserves three target components, and reproduces the fixed Zofío--Prieto oracle | P1 / 2 |
| `analysis.allocative_decomposition` | operator | non-executable umbrella for technical versus price/choice adaptation under a supported identity | partial | P1 / 2 |
| `analysis.allocative_decomposition.cost_input_radial` | operator | matched input-radial technical, cost-allocative, and cost efficiency with $CE=TE^I AE^C$; API symbol `AllocativeDecomposition` | implemented/public | P1 / 2 |
| `analysis.allocative_decomposition.revenue_output_radial` | operator | matched output-radial technical, revenue-allocative, and revenue efficiency with $RE=TE^O AE^R$; API symbol `RevenueAllocativeDecomposition` | implemented/public | P1 / 2 |
| `analysis.scale_rts` | family | scale and returns-to-scale analyses sharing fitted technologies | partial/public | P0 / 0 |
| `analysis.scale_efficiency.radial_ratio` | operator | CRS/VRS radial efficiency ratio under matched data and orientation | implemented/public | P0 / 0 |
| `analysis.returns_to_scale.local` | operator | non-executable umbrella for local RTS classification under a named test or supporting-hyperplane rule | partial; Banker--Thrall leaf public | P1 / 2 |
| `analysis.returns_to_scale.local.banker_thrall_1992` | operator | Banker--Thrall local RTS classification with interval-valued supporting-hyperplane evidence at the selected Pareto-efficient VRS projection; API symbol `local_returns_to_scale` | implemented/public; published five-observation oracle reproduced | P1 / 2 |
| `analysis.scale_elasticity` | family | non-executable umbrella for quantitative scale response under a declared proportional or directional operating counterfactual | partial; radial VRS and Ren relative-directional VRS leaves public | P1 / 2 |
| `analysis.scale_elasticity.local.radial_vrs` | operator | left/right proportional output response at the same selected Pareto-efficient VRS target and full support interval used by local RTS; API symbol `scale_elasticity` | implemented/public; Førsund--Hjalmarsson seven-unit oracle reproduced, including kink and extended-boundary cases | P1 / 2 |
| `analysis.scale_elasticity.directional` | family | non-executable umbrella for quantitative scale response under explicit non-proportional input/output directions | partial; Ren relative-directional VRS leaf public | P1 / 2 |
| `analysis.scale_elasticity.directional.relative_vrs.ren_etal_2021` | operator | one-sided local output response to a declared relative-rate change in the input mix at a selected Pareto-efficient VRS plan; input and output directions must be nonnegative and already mean-one normalized; API symbol `relative_directional_scale_elasticity` | implemented/public; all three Ren et al. Table 4 DMU 2 scenarios reproduced and all-one directions exactly reduce to the matched radial operator | P1 / 2 |
| `analysis.mpss` | family | non-executable umbrella for most productive scale size under a declared measure and mix policy | planned; current reconstruction is source-gated | P1 / 2 |
| `analysis.mpss.banker_1984` | operator | candidate fixed-observed-mix maximum-average-productivity and scale-interval reconstruction | prototype/non-public; `deferred_to_next_version` because the defining 1984 full text is not available for equation-level audit; later-source support and internal property evidence do not close that gate | P1 / 2 |
| `analysis.tfp_efficiency.scale_mix` | operator | technical, scale, mix, and scale-mix TFP efficiency under a declared aggregate-quantity framework | planned | P1 / 2 |
| `analysis.capacity` | family | non-executable umbrella for source-qualified physical, utilization, unbiased, and economic capacity concepts | planned; current physical-capacity reconstruction is source-gated | P1 / 2 |
| `analysis.capacity.physical.fare_grosskopf_kokkelenberg_1989` | operator | candidate short-run physical-capacity reconstruction with quasi-fixed and variable inputs declared separately | prototype/non-public; `deferred_to_next_version` because the defining 1989 full text is not available for equation-level audit; review support and internal property evidence do not close that gate | P1 / 2 |
| `analysis.capacity.economic.segerson_squires_1990` | family | source-qualified dual/primal multiproduct economic-capacity concepts using prices, costs, quasi-fixed assets, and supporting values | planned; executable leaves require branch-specific audits | P2 / 3 |
| `analysis.congestion` | literature umbrella | non-executable organizer for whether excess inputs suppress attainable output under a named production account | source-gated; no public implementation currently authorized | — |
| `analysis.congestion.fgl_1985` | audit locator | Färe--Grosskopf--Lovell weak-versus-strong input-disposability comparison under its source-qualified technology | `source_not_frozen`; `deferred_to_next_version`; non-public and absent from the executable registry | — |
| `analysis.congestion.cooper_slack` | literature umbrella | Cooper-line slack-based detection, source attribution, and amount of congestion | non-executable; individual source routes require separate evidence gates | — |
| `analysis.congestion.cooper_deng_huang_li_2002` | audit locator | source-gated candidate for the Cooper--Deng--Huang--Li one-model slack-congestion recipe | `source_not_frozen`; `deferred_to_next_version`; defining full text, published oracle, and projection policy unresolved; non-public and absent from the executable registry | — |
| `analysis.congestion.strong` | literature boundary | source-qualified strong-congestion concepts; never a generic boolean inherited by every congestion model | later-version source review only; no current public implementation plan | — |
| `analysis.congestion.weak` | literature boundary | source-qualified weak-congestion concepts, distinct from strong congestion | later-version source review only; no current public implementation plan | — |
| `analysis.congestion.directional` | literature boundary | congestion relative to a declared input/output direction and native directional units | specialist Documentation or later version only; no handbook placement | — |
| `analysis.scope_economies` | family | whether joint multi-output production dominates declared separate-production subtechnologies | planned | P2 / 3 |
| `analysis.shadow_value` | operator | local supporting valuations and marginal trade-offs | planned | P1 / 2 |
| `analysis.marginal_values.directional_derivatives.podinovski_etal_2016` | operator | one-sided directional derivatives and identified intervals for marginal values, substitution/transformation rates, and scale response at frontier kinks | planned | P1 / 2 |

`overall_efficiency` is prohibited as an unqualified public result name.
Cost, revenue, profit, Nerlovian, network-system, and environmental results
use source-qualified fields.

The congestion locators are not aliases or current implementation promises.
The FGL lineage defines congestion through a change in the maintained
input-disposability technology; the Cooper-line formulations diagnose and
allocate non-radial input slacks. Their scores, targets, and congestion amounts
may differ even on the same data. If a later version closes either source gate,
its result must store the source-qualified definition rather than expose a
generic `is_congested` switch. See
`source_protocols/fare_grosskopf_lovell_congestion.md` and
`source_protocols/cooper_deng_huang_li_2002_congestion.md`.

## 6. Valuation and evaluation protocols

| Canonical ID | Kind | Scope | Status | Priority / tier |
|---|---|---|---|---|
| `valuation.weight_restriction` | family | non-executable umbrella for restrictions on admissible valuations | planned | P1 / 2 |
| `valuation.weight_restriction.ar1` | deferred candidate | AR-I relative multiplier restrictions with declared units | `source_not_frozen` and `blocked_on_primary_source`; deferred to the next version with no public API or machine method record | — |
| `valuation.weight_restriction.ar2_cross_side` | deferred candidate | AR-II restrictions linking input and output multipliers across the two valuation sides | `source_not_frozen` and `blocked_on_primary_source`; deferred to the next version with no public API or machine method record | — |
| `valuation.weight_restriction.absolute_relative` | family | source-qualified absolute or relative multiplier bounds | planned | P1 / 2 |
| `valuation.weight_restriction.cone_ratio` | family | non-executable umbrella for cone-ratio valuation restrictions and source-qualified dual representations | planned; one finite input-oriented CRS sum-form child is source-frozen below | P1 / 2 |
| `valuation.weight_restriction.cone_ratio.polyhedral_crs.charnes_etal_1990` | source-qualified preset | finite-DMU input-oriented CRS cone-ratio CCR with exogenous nonnegative sum-form input/output generator matrices, reconstructed multipliers, and cone-residual rather than ordinary-slack semantics | implemented/public as `PolyhedralConeRatioDEA`; typed restriction provenance, sparse one-LP-per-DMU compiler, layered primal/dual result validity, identity-cone CCR reduction, and independent Example 2 multiplier/envelopment oracle are automated; Example 3/Table 2 remains an excluded unresolved 2-of-17 source conflict; no AR-I/II, common-weight, VRS/output, half-space conversion, trade-off, or ordinary-target claim; see `source_protocols/charnes_cooper_huang_sun_1990_polyhedral_cone_ratio.md` and `oracles/charnes_cooper_huang_sun_1990_cone_ratio.md` | P1 / 2 |
| `valuation.weight_restriction.virtual_share.wong_beasley` | deferred candidate | observation-dependent bounds on each factor's share of total virtual input or output | `source_not_frozen` and `deferred_to_next_version`; complete primary equations, denominator/zero policy, and independent oracle are not frozen; no public API or machine method record | — |
| `diagnostics.weight_restriction_consistency` | procedure | feasibility, unit dependence, and implied free/unlimited-production audit for declared weight restrictions | planned | P1 / 2 |
| `valuation.value_efficiency` | family | preference induced by a declared most-preferred efficient plan | planned | P1 / 2 |
| `valuation.value_efficiency.halme_etal_1999` | preset | source-qualified value-efficiency appraisal anchored by a declared most-preferred efficient plan and its implied value trade-offs | planned; primary source selected, equations/oracle pending freeze | P1 / 2 |
| `valuation.price_policy` | policy | market/administered/accounting source, common versus unit-specific values, currency, numeraire, and base period | partial/public for complete strictly positive prices through `PriceSpec` and `PriceData`; interval/incomplete policies planned | P1 / 2 |
| `direction.policy` | policy family | how a movement direction is generated, authorized, scaled, and kept comparable across units or periods; never inferred to be a management preference merely because an analyst supplied it | partial; explicit exogenous directions public in DDF/GDF-related APIs, source-qualified selection policies planned | P0 / 1 |
| `direction.exogenous` | policy | a direction declared before fitting, with provenance recorded as elicited, institutionally authorized, literature-prescribed, or analyst-defined | partial/public; provenance vocabulary and stronger validation expanding | P0 / 1 |
| `direction.observation_scaled` | policy | a common proportional rule applied to each observation's own quantities, with zero-component and intertemporal comparability policies retained | partial/public in compatible radial/DDF reductions | P1 / 2 |
| `direction.range_ideal` | policy | direction generated from declared sample ranges or an ideal-point construction, with sample dependence and signed-data domain retained | partial/public through the source-fixed 2004 RDM policy; other range/ideal policies remain planned | P1 / 2 |
| `direction.endogenous_value.petersen_2018` | policy/operator | choose a direction through a source-qualified cost, revenue, or profit value relation rather than treating it as an ordinary numeric option | planned; belongs jointly to performance, valuation, and evaluation protocol | P1 / 2 |
| `evaluation.governance` | protocol family | `GovernanceSpec(players, authority, objectives, move_order, information, solution_concept)` determines who may choose a plan on a separately declared production graph | planned framework contract | P1 / 2 |
| `evaluation.governance.centralized` | protocol | one coordinating authority optimizes a declared system objective | planned | P1 / 2 |
| `evaluation.governance.leader_follower` | protocol | sequential authority and response under a source-qualified Stackelberg or bilevel solution concept | planned | P2 / 3 |
| `evaluation.governance.noncooperative` | protocol | strategic players choose under a named equilibrium and convergence rule | planned | P2 / 3 |
| `evaluation.governance.bargaining` | protocol | feasible performance or targets are selected by a named bargaining solution and disagreement point | planned | P2 / 3 |
| `evaluation.super` | recipe family | compatible base measure + `reference.leave_one_out` + source-qualified applicability, infeasibility, and score policy | partial/public through Tone super-SBM and Ray directional super-efficiency; Andersen--Petersen radial remains a non-public deferred prototype | P1 / 2 |
| `evaluation.super.ap_radial` | deferred prototype | candidate Andersen--Petersen radial super-efficiency reconstruction with explicit RTS/orientation, leave-one-out reference membership, higher-is-better display transform, and fail-closed infeasibility policy | `deferred_to_next_version`; tested internal code and later-source numerical checks are retained, but the defining 1993 full text was not obtained, so no public API or catalog identity and no original-programme, data-domain, failure, target, or peer claim is released | P1 / 2 |
| `evaluation.super.sbm` | family | source-qualified super-SBM formulations separated by orientation, RTS, data domain, applicability screen, and zero/bad-output policy | partial/public through the Tone (2002) strictly positive desirable-quantity leaf | P1 / 2 |
| `evaluation.super.sbm.tone_2002` | preset | Tone's same-RTS strong-SBM-screened super-SBM: CRS non-oriented/input/output and VRS non-oriented only, with strict positivity, row-level self-exclusion, source-native score, and fail-closed applicability/solve states | implemented/public as `ToneSuperSBM` with exact alias `SuperSBM`; the neutral `super_sbm_peer_replacement` case checks eligibility, orientation, VRS, and peer-replacement accounts without redistributing a source table | P1 / 2 |
| `evaluation.super.directional` | family | source-qualified directional super-efficiency under a declared direction and reference-exclusion protocol | partial/public through Ray's fixed observed-direction VRS leaf; no generic arbitrary-direction constructor | P1 / 2 |
| `evaluation.super.directional.ray_2008` | preset | Ray's row-level leave-one-out VRS programme with fixed observed-bundle direction $(-x_o,y_o)$, unrestricted $\beta$, and $NL=1-\beta$ as peer-replacement exposure rather than an efficiency percentage | implemented/public as `RayDirectionalSuperEfficiency` with exact alias `NerloveLuenbergerSuperEfficiency`; the neutral `directional_super_multivariate_stress` case is checked against an independent dense compiler, including invalid-projection diagnostics | P0 / 1 |
| `evaluation.super.infeasibility.seiford_zhu_1999` | diagnostic | source-qualified necessary/sufficient infeasibility analysis for leave-one-out super-efficiency under declared RTS and orientation | planned; diagnostic evidence leaf, not a score-repair method | P1 / 2 |
| `evaluation.super.modified.cook_liang_zha_zhu_2009` | preset | source-qualified modified input/output super-efficiency construction for VRS infeasibility, retaining its own technology, score, and target contract | planned; not a generic fallback for every super measure | P1 / 2 |
| `evaluation.cross` | protocol family | peer appraisal with matrix roles, valuation-selection policy, aggregation rule, multiplicity diagnostics, and failure semantics kept explicit | partial/public through the Liang--Wu--Cook--Zhu game leaf; ordinary CRS remains a non-public deferred prototype | P1 / 2 |
| `evaluation.cross.crs` | deferred prototype | candidate ordinary CRS appraiser--evaluatee matrix using one solver-selected primary CCR optimum per appraiser | `deferred_to_next_version`; robust internal compiler and multiplicity tests are retained, but the defining Sexton--Silkman--Hogan and Doyle--Green full texts and a source-native independent oracle were not obtained; no public API or catalog identity | P1 / 2 |
| `evaluation.cross.crs.doyle_green_1994` | deferred source family | Doyle--Green secondary-selection lineage; non-executable grouping because Method II/III and aggressive/benevolent objectives are not one switch | `deferred_to_next_version`; defining full text and executable oracle not frozen | P1 / 2 |
| `evaluation.cross.crs.doyle_green_1994.method_ii.aggressive` | deferred preset | candidate primary-score-preserving Method-II aggressive secondary appraisal | `deferred_to_next_version`; exact objective, normalization, zero-weight rules, and published oracle not frozen | P1 / 2 |
| `evaluation.cross.crs.doyle_green_1994.method_ii.benevolent` | deferred preset | candidate primary-score-preserving Method-II benevolent secondary appraisal | `deferred_to_next_version`; exact objective, normalization, zero-weight rules, and published oracle not frozen | P1 / 2 |
| `evaluation.cross.crs.doyle_green_1994.method_iii.aggressive` | deferred preset | candidate Method-III aggressive composite-peer appraisal | `deferred_to_next_version`; exact ratio construction, normalization, and published oracle not frozen | P1 / 2 |
| `evaluation.cross.crs.doyle_green_1994.method_iii.benevolent` | deferred preset | candidate Method-III benevolent composite-peer appraisal | `deferred_to_next_version`; exact ratio construction, normalization, and published oracle not frozen | P1 / 2 |
| `evaluation.cross.vrs` | family | VRS cross-efficiency with explicit treatment of the free intercept | planned | P1 / 2 |
| `evaluation.cross.vrs.lim_zhu_2015` | preset | source-qualified VRS cross-efficiency retaining intercept, denominator, and entry-validity diagnostics | planned | P1 / 2 |
| `evaluation.cross.secondary` | family | aggressive, benevolent, neutral, or another declared tie-break over one evaluator's primary multiplier-optimal face | planned | P1 / 2 |
| `evaluation.cross.game_nash.liang_wu_cook_zhu_2008` | protocol | fixed-CRS game cross-appraisal: each synchronous iteration solves $n^2$ protected-$d$ by focal-$j$ multiplier LPs, each normalizing $j$'s virtual input, maximizing $j$'s score, and preserving one $d$-specific score floor; $\eta_j^{t+1}=n^{-1}\sum_d g_{dj}(\eta_d^t)$, including self, is the source-native payoff/update rather than a free aggregation choice | implemented/public; API symbols `LiangWuCookZhuGameCrossEfficiency` and `GameCrossEfficiency`, with the neutral `strategic_peer_service` case covering synchronous-map, fixed-point, streamed-storage, and failure contracts | P1 / 2 |
| `evaluation.pessimistic_multiplier` | family | least-favourable multiplier appraisal under a source-defined normalization; not an empirical worst-practice technology | planned | P2 / 3 |
| `evaluation.worst_practice_frontier` | family | envelopment appraisal relative to a source-defined inefficient empirical boundary; not merely unfavourable multiplier selection | planned | P2 / 3 |
| `evaluation.double_frontier` | family | paired best- and worst-appraisal values plus a source-defined normalization and combination rule | planned | P2 / 3 |
| `evaluation.double_frontier.geometric.wang_chin_yang_2007` | preset | source-qualified optimistic/pessimistic geometric appraisal retaining both component values and the combined ranking quantity | planned; primary equations/oracle pending freeze | P2 / 3 |
| `evaluation.common_weight` | protocol | one valuation system shared across units | planned | P1 / 2 |
| `evaluation.common_weight.roll_cook_golany_1991` | deferred candidate | proposed common-set-of-weights appraisal retaining the shared valuation constraints, objective, normalization, and comparison rule | `source_not_frozen`, `blocked_on_primary_source`, and `deferred_to_next_version`; accessible metadata confirms the topic but the complete shared programme, tie policy, and numerical oracle are not frozen; no public API or machine method record | — |
| `evaluation.mcdea.li_reeves_1999` | neighbor/protocol | multiple-criteria DEA compromise among efficiency and discrimination objectives; reports the chosen multiobjective rule rather than pretending it is an ordinary technical-efficiency measure | planned official extension; source-qualified, not a weight-restriction alias | P2 / 3 |
| `evaluation.target_selection` | protocol | closest, furthest, priority, or multiple-target policy | planned | P1 / 2 |
| `evaluation.target_selection.closest_strong.aparicio_ruiz_sirvent_2007` | preset | source-qualified closest Pareto-efficient target that jointly defines the performance distance and target-selection protocol, with an alternate-target policy | planned; requires MILP/complementarity capability for the canonical formulation | P1 / 2 |
| `evaluation.target_completion.pareto_koopmans` | protocol | on an ordinary continuous convex black-box technology with all completed inputs discretionary and outputs desirable, hold the compatible radial/DDF primary optimum or fixed finite nonnegative GDF path target, maximize a strictly positive zero-safe row-scaled slack account, reconstruct the selected target, and only then report generic Pareto--Koopmans status | implemented/public as an embedded `compute_slacks=True` protocol of `static.radial`, `static.directional_distance`, and `static.generalized_distance.chavas_cox`; Charnes et al. (1985) equations and exact dense phase-two evidence frozen; radial/DDF scales anchor to the evaluated observation while GDF anchors to its fixed path target, a distinction that affects only alternate strong-target selection; no standalone API or duplicate machine record | P0 / 1 |
| `evaluation.target_completion.pareto_koopmans.environmental` | deferred protocol candidate | source-qualified strong-status and completion rule whose dominance order retains desirable/undesirable roles and the selected disposal technology | `deferred_to_next_version`; environmental dominance, disposal-specific target theorem, and independent exact completion oracle are not frozen; no standalone API, catalog identity, or machine record | — |
| `evaluation.target_completion.pareto_koopmans.nondiscretionary` | deferred protocol candidate | retain nondiscretionary quantities in comparison while excluding unauthorized adjustments under a source-qualified equality/inequality contract | `deferred_to_next_version`; the general variable-rights contract and independent exact target oracle are not frozen; no standalone API, catalog identity, or machine record | — |
| `evaluation.target_completion.pareto_koopmans.fdh` | deferred protocol candidate | strong-status completion on a source-qualified single-template/free-disposal nonconvex technology | `deferred_to_next_version`; the nonconvex target theorem, alternate-peer policy, and independent exact completion oracle are not frozen; no standalone API, catalog identity, or machine record | — |
| `evaluation.target_completion.pareto_koopmans.fch` | deferred protocol candidate | strong-status completion on the binary free-coordination technology | `deferred_to_next_version`; the mixed-integer target identity, alternate optimum, and independent exact completion oracle are not frozen; no standalone API, catalog identity, or machine record | — |
| `evaluation.target_completion.pareto_koopmans.frh` | deferred protocol candidate | strong-status completion with integer replication activities | `deferred_to_next_version`; the integer target identity, alternate optimum, and independent exact completion oracle are not frozen; no standalone API, catalog identity, or machine record | — |
| `evaluation.frontier_tiers` | protocol | peeling/context-dependent benchmark layers | planned | P1 / 2 |
| `evaluation.frontier_tiers.context_dependent.seiford_zhu_2003` | preset | iterative performance tiers plus source-defined attractiveness/progress contexts | planned | P1 / 2 |
| `evaluation.benchmark_frequency` | non-executable discovery umbrella | reference-frequency and peer-network summaries whose graph, peer-plan, multiplicity, and denominator contracts remain explicit | partial through the public selected-plan leaf `analysis.reference_frequency.selected_plan`; graph-aware and alternate-optimum leaves remain planned | P1 / 2 |
| `analysis.reference_set` | procedure | observed, maximal, global, unary, and reference-frequency diagnostics without silently changing the fitted technology | planned | P1 / 2 |
| `analysis.reference_set.global.mehdiloozad_etal_2015` | procedure | source-qualified global reference set and minimum-face diagnostics across alternate optimal projections; unrelated to the temporal pooled-hull policy `reference.global` | planned | P1 / 2 |
| `composite.benefit_of_doubt` | neighbor | endogenous indicator aggregation using DEA multiplier machinery; not production efficiency without a production interpretation | planned official extension | P2 / 3 |
| `composite.benefit_of_doubt.linear.cherchye_etal_2007` | preset | linear benefit-of-the-doubt composite-indicator weighting with one normalized aggregate, indicator weights/restrictions, ranking, and sensitivity retained as non-production outputs | planned official extension | P2 / 3 |

Super-efficiency, cross-efficiency, common weights, and strong-target
completion are not aliases. A best radial, directional, or
generalized-distance value establishes only measure efficiency until a
compatible completion phase certifies the strong target. Alternate
multiplier, peer, or target optima require a stored secondary
objective/tie-breaking rule and multiplicity diagnostics.
The public completion boundary is equation-checked against
[Charnes et al. (1985)](https://doi.org/10.1016/0304-4076(85)90133-2) and
recorded in
[`source_protocols/charnes_etal_1985_pareto_koopmans_completion.md`](source_protocols/charnes_etal_1985_pareto_koopmans_completion.md).
The source's observed-value normalization and DEAPack's zero-safe row-scale
selectors are related unit-invariance constructions, not identical target
rules. The shared protocol ID fixes one Pareto--Koopmans completion principle
and LP layout; radial/DDF use evaluated-observation anchors and GDF uses its
fixed path target, so it does not promise identical alternate-optimum weights.

The production graph and governance protocol are orthogonal. The same
two-stage process may be operated by one coordinating authority, a
leader--follower hierarchy, strategic divisions, or a bargaining procedure;
those studies have different objectives and solution concepts even when all
physical link equations are identical. Likewise, Liang--Wu--Cook--Zhu game
cross-efficiency is not a spelling of aggressive or benevolent
cross-efficiency. An ordinary cross-efficiency row applies one appraiser's
selected weights across evaluatees. The game protocol instead solves a
separate LP for every protected $d$--focal $j$ pair, updates all focal
scores simultaneously using the source's equal mean over $d$, including
self, and seeks the source-defined Nash score vector. Its rows therefore mean
`protected_dmu_id`, not ordinary `appraiser_id`, and `game` cannot be accepted
as a `secondary_goal` or aggregation option. The protocol has a Level D
relationship to an ordinary secondary-objective recipe.

## 7. Study design and deterministic robustness

| Canonical ID | Kind | Permitted claim | Status | Priority / tier |
|---|---|---|---|---|
| `study_design.variable_selection` | procedure | theory-led and source-qualified statistical variable selection with tuning path, selected schema, and stability record | planned | P0 / 2 |
| `diagnostics.deterministic_stability` | family | allowable perturbations or stability regions for observations, bounds, weights, and rankings | planned | P1 / 2 |
| `diagnostics.deterministic_stability.ccr.seiford_zhu_1998` | procedure | source-qualified stability region for a declared CCR efficiency result under deterministic data perturbations; no sampling-probability interpretation | planned | P1 / 2 |
| `diagnostics.model_sensitivity` | procedure | declared comparison across technology, RTS, reference, direction, or valuation assumptions | planned | P0 / 2 |
| `diagnostics.property_compatibility` | procedure | machine-check data-domain, invariance, monotonicity, indication, target, and operator compatibility before fitting | partial specification | P0 / 1 |
| `reference.peer_eligibility` | source-neutral study-design policy | declare each observation's candidate comparison population before fitting and intersect it with the rows admitted by the base `ReferenceSpec`; fitted positive-intensity peers remain results | implemented/public through `PeerEligibility` and `PeerEligibilityProvenance` on the ordinary radial family and four fixed radial recipes, Additive/Weighted Additive, RAM, ordinary input/output/non-oriented SBM aliases, and ordinary DDF; no standalone fit, catalog method identity, category inference, Banker--Morey claim, or automatic environmental/specialist-family support | P0 / 1 |

Variable selection is part of research design, not a technology or an
efficiency-maximizing preprocessing trick. Theory/process mapping, ECM,
bootstrap, PCA/dimension reduction, penalized/cardinality, and other
source-qualified procedures remain distinct strategies under one reporting
contract. Deterministic perturbation stability is not sampling inference,
robust optimization, or leave-one-out influence, even when the same model is
solved repeatedly. Source-neutral peer eligibility is likewise a comparison-
right policy, not a new frontier estimator: if $I_o$ is the base
`ReferenceSpec` population and $P_o$ is the declared candidate population,
the effective population for every authorized classical black-box fit is
exactly $I_o\cap P_o$. RAM alone retains one global base information rule and
computes its common range scale from the full data before this intersection.

The normative property vocabulary and fail-closed compatibility rules are in
[`COMPATIBILITY_MATRIX.md`](COMPATIBILITY_MATRIX.md).

## 8. Special data semantics

These are capability declarations that may activate a technology, measure, or
mixed-integer compiler; they are not one `restricted_data=True` switch.

| Canonical ID | Meaning | Status | Priority / tier |
|---|---|---|---|
| `data.nondiscretionary` | affects feasible comparison but is not a managerial adjustment target | planned | P1 / 2 |
| `data.semi_discretionary` | bounded managerial adjustment with source-qualified target restrictions | planned | P1 / 2 |
| `data.categorical_nominal` | determines admissible comparison groups | planned | P1 / 2 |
| `data.categorical_ordered` | ordered categories without ordinary cardinal convexification | planned | P1 / 2 |
| `data.ordinal` | rank-only information | planned | P1 / 2 |
| `data.ratio` | ratio/percentage variable requiring compatible convexity | planned | P1 / 2 |
| `data.integer_discrete` | indivisible production quantities and targets | planned | P1 / 2 |
| `data.operational_bounds` | physical or institutional quantity bounds, distinct from interval uncertainty and BAM normalization | planned | P1 / 2 |
| `data.flexible_role` | a factor's input/output role is selected by an explicit model rather than preprocessing | planned | P2 / 3 |
| `data.flexible_role.cook_zhu_2007` | source-qualified flexible-measure recipe that chooses a factor's common role under explicit multiplier and consistency rules | planned | P2 / 3 |
| `data.dual_role.cook_green_zhu_2006` | source-qualified dual-role recipe in which a factor may simultaneously enter both valuation sides under the source balance/reallocation account | planned; not a flexible-role classification alias | P2 / 3 |
| `data.missing` | missingness and admissible comparison policy; never automatic zero filling or interval-DEA substitution | planned | P1 / 2 |
| `data.missing.fuzzy_kao_liu_2000` | missing-observation treatment using the source fuzzy-efficiency construction and membership statement | planned; distinct from imputation and interval information | P2 / 3 |
| `data.missing.conservative_kuosmanen_2009` | conservative source-qualified comparison policy for incomplete input/output observations | planned; distinct from zero filling and fuzzy membership | P1 / 2 |
| `data.missing.interval_idea` | interval-information treatment for unobserved quantities with declared bounds and order semantics | planned umbrella; exact source leaf and oracle still required | P2 / 3 |
| `data.negative` | signed values with measure-specific translation/domain rules | partial/public through the original RDM leaf; no generic signed-data switch | P1 / 2 |
| `data.zero_nonpositive` | denominator/log/direction domain policy | partial validation only | P0 / 0 |
| `data.interval_imprecise` | incomplete bounded/order/ratio information | planned | P2 / 3 |
| `data.fuzzy` | membership/possibility-valued information | planned | P2 / 3 |
| `data.contextual` | operating condition for conditional or separable analysis | planned | P1 / 2 |
| `static.radial.nondiscretionary.banker_morey_1986` | executable radial recipe whose exogenously fixed inputs/outputs shape comparison but receive no unauthorized managerial target | deferred candidate; complete primary text, source equations, and numerical oracle are not frozen; no public API or machine record | — |
| `static.radial.categorical.banker_morey_1986` | provisional umbrella for the source's categorical formulations; final controllable/uncontrollable leaf split remains unresolved | deferred candidate; complete primary text, defining equations, `dea3` schema, and numerical oracle are not frozen; no public API or machine record | — |
| `data.integer_discrete.lozano_villa_2006` | source-qualified mixed-integer DEA recipe retaining integer-feasible targets and the matched continuous relaxation | planned; requires MILP compiler | P1 / 2 |
| `static.range_directional.portela_thanassoulis_simpson_2004` | original VRS range-directional signed-data measure using focal-to-coordinatewise-ideal ranges, exact reference/extrema matching, input/output/non-oriented programmes, native $\beta$, and efficiency $1-\beta$ | implemented/public as `RangeDirectionalDEA` / `RDM`; primary equations and target transcription checked, exact signed oracle cross-implemented; source phase one only | P1 / 2 |
| `static.sorm.emrouznejad_anouze_thanassoulis_2010` | semi-oriented radial measure that partitions the signed-data adjustment under its own boundedness conditions | deferred candidate; the original SORM is frozen, but the complete source boundedness note and theorem-level zero-boundary contract are unavailable; no public API or machine record | — |
| `static.msbm.signed` | modified signed-data slacks-based family with source-specific normalizers and score domain | research-only umbrella until one defining formulation and oracle are frozen | P2 / 3 |

A negative good output is not an undesirable output. A contextual condition
is not automatically a non-discretionary input. Continuous solutions to an
integer technology are not rounded after fitting. Ordered categories encode
admissible order/comparison, whereas ordinal data contain rank information
without ordinary cardinal arithmetic. `data.interval_imprecise` declares the
information available; `uncertainty.interval_idea` is a fitted estimator that
uses it.

The `data.*` records declare semantics only. They become executable through a
source-qualified named measure/technology recipe. Both provisional
Banker--Morey leaves above are deferred discovery identities, not executable
recipes in the current release. The public source-neutral
`reference.peer_eligibility` policy neither defines a categorical data role
nor supplies either named model. Later non-discretionary and categorical formulations are registered as
variants when they change admissible peers, target rights, convexification, or
solver form; they are not silently routed through the 1986 presets.

The implemented RDM is not an alias for SORM, inverse RDM, RAM, signed-data
SBM variants, radial DEA after translating the observations, or an
undesirable-output DDF. They change the improvement plan, economic output
role, normalization, boundedness, or invariance contract. Flexible-role
classification chooses one common role;
dual-role accounting permits simultaneous use on both sides.  Missingness,
imputation, interval information, and fuzzy membership likewise remain
separate semantics.

## 9. Environmental technology and measure registry

| Canonical ID | Kind | Economic production account | Status | Priority / tier |
|---|---|---|---|---|
| `environmental.legacy_transform` | family | reciprocal/translation/negative transformations or bad-as-input replication | planned with warnings | P1 / 2 |
| `environmental.joint_production.envelopment` | technology | black-box joint production of desirable services and residuals under fully declared disposal/null-jointness assumptions | implemented/public subset | P0 / 1 |
| `environmental.disposal.strong` | assumption | bad can be reduced without a modeled production sacrifice | implemented in selected models | P0 / 1 |
| `environmental.formulation.bad_output_directional_equality` | formulation | compatibility DDF task constraint `B lambda + beta g_b = b_o`; insufficient by itself to identify a named weak-disposal technology | implemented/public compatibility path; selector spelling `weak` emits `FutureWarning`, preserves old numbers, and reports disposability as `not_identified` rather than claiming weak disposal | P0 / 1 |
| `environmental.weak_disposal.common_factor` | technology family | one common proportional curtailment factor on the represented activity | implemented CRS source-qualified subset | P0 / 1 |
| `environmental.weak_disposal.common_factor.crs.chung_fare_grosskopf_1997` | technology/preset | Chung--Färe--Grosskopf CRS output set; bad-output equality is a complete common-factor weak-disposal construction because CRS scaling preserves input feasibility | implemented/public through common-factor DDF and the source direction preset; null jointness remains separately declared | P0 / 1 |
| `environmental.ddf.weak_disposal.common_factor` | family | directional operating programme composed with the CRS common-factor technology | implemented/public; direction exposed, RTS fixed to CRS | P0 / 1 |
| `environmental.ddf.output.chung_fare_grosskopf_1997` | preset | CRS common-factor weak-disposal DDF with fixed observed direction `(0, y_o, b_o)` and null-jointness validation | implemented/public; source-edition inconsistency documented; fixed-input formulation has an exact analytical certificate and independent dense compiler | P0 / 1 |
| `environmental.weak_disposal.activity_specific` | technology family | reference activities can carry different weak-disposal factors while total activity remains a convex portfolio | implemented VRS source-qualified subset | P0 / 1 |
| `environmental.weak_disposal.activity_specific.vrs.kuosmanen_2005` | technology/preset | Kuosmanen convex VRS construction with `X(mu+tau)<=x`, `Y mu>=y`, `B mu=b`, and `1'(mu+tau)=1` | implemented/public; exact linearization and distinguishing regression test | P0 / 1 |
| `environmental.ddf.weak_disposal.activity_specific` | family | directional operating programme composed with the Kuosmanen VRS technology | implemented/public; direction exposed, RTS fixed to VRS | P0 / 1 |
| `environmental.weak_disposal.generalized_piecewise_cobb_douglas.roshdi_etal_2018` | technology/preset | generalized/exponential weak disposal with unequal good--bad trade-off rates over the source piecewise Cobb--Douglas environmental technology | planned; reader-facing research-only until source equations and oracle are frozen | P2 / 3 |
| `environmental.selective_disposal` | technology | pollutant-level strong/weak declarations | planned | P1 / 2 |
| `environmental.semi_disposal.chen_wang_lai_2017` | technology/preset | pollutant-specific non-disposal degree intended to distinguish a freely reducible region from reductions requiring proportional production sacrifice | planned; reader-facing research-only after the 2026 production-set critique | P2 / 3 |
| `environmental.semi_disposal.refined.chu_etal_2026` | technology/preset | refined semi-disposability plus a compliance-bounded bad-output inefficiency axiom under source-specific CRS/VRS constructions | planned; reader-facing research-only while recent equations and oracle are audited | P2 / 3 |
| `environmental.null_jointness` | restriction | no desirable production without associated residual generation | implemented as explicit option | P0 / 1 |
| `environmental.costly_disposal` | restriction | reducing residuals requires a declared sacrifice or pollution-control resource/process; not ordinary cost efficiency | implemented inside the current by-production residual subtechnology | P0 / 1 |
| `environmental.ddf.joint_production` | family | declared resource/service/emission improvement programme | implemented/public | P0 / 1 |
| `environmental.sbm.separable_strong` | preset | Tone-style undesirable-output SBM | implemented/public | P0 / 1 |
| `environmental.sbm.nonseparable` | family | discovery grouping for source-qualified non-separable good/bad-output SBM accounts; inputs retain their ordinary slack account, and any weak-disposal technology is declared separately | non-executable umbrella; Tone's 2003 preset is public | P1 / 2 |
| `environmental.sbm.nonseparable_hybrid.tone_2003` | preset | Tone's operating account keeps every input in the ordinary input-slack balance, applies one retained operating share `alpha` to declared jointly changing good and bad outputs, and adjusts the remaining good/bad outputs through separate slacks; API symbols `ToneNonSeparableSBM`, `NonSeparableUndesirableSBM`, and `SBMNS` | implemented/public; equations (29)--(32), the project-authored `environmental_disposability_contrast` account, target reconstruction, and unit invariance are checked without redistributing the source tables | P0 / 1 |
| `environmental.directional_nonradial` | family | directional SBM/Russell/non-radial DDF | planned | P1 / 2 |
| `environmental.directional_nonradial.energy_carbon.zhou_ang_wang_2012_non_chp` | specialized source preset / application specialization | Zhou--Ang--Wang's CRS non-CHP electricity account with exactly one strictly positive fossil-fuel input, electricity output, and CO2 output; one public `ZhouAngWangNonCHPEnergyCarbonDEA` class (alias `NonCHPEnergyCarbonDEA`) requires an explicit `account` selector among `energy`, `carbon`, and `integrated_energy_carbon`, retaining each source-fixed observed-value direction, block-normalization weights, component steps, and EPI/CPI/ECPI transformation. It is not a foundational environmental-model family | implemented/public with a source-only analytical certificate and independent dense compilation; global self-inclusive cross section, bad-output equality/common-factor construction, null jointness, and CRS are fixed. The raw distance rises with unrealized opportunity, while lower values rank as better current performance. This is not a published 126-country reproduction. Arbitrary directions, weights, references, RTS, more variables, and the printed unbounded CHP branch are rejected or deferred; no book placement is claimed | P1 / 2 |
| `environmental.hyperbolic` | source-preset family | `performance.hyperbolic` composed with desirable/undesirable output roles and a source-qualified environmental technology; the measure path does not create a second hyperbolic solver | planned | P1 / 2 |
| `environmental.by_production` | technology | intersection of intended-production and residual-generation subtechnologies with explicit pollution-generating inputs, costly disposal, and source-qualified coupling/dependence rules | implemented/public subset | P0 / 1 |
| `environmental.by_production.joint_input_parallel` | technology | parallel intended-production and pollution-generation subtechnologies coupled by the same target for each jointly consumed pollution-generating input; not a shared-resource allocation or the independent-intensity default | planned | P1 / 2 |
| `environmental.by_production.ddf` | preset | conventional common directional programme on the by-production technology; the source uses it to diagnose weak indication and direction sensitivity rather than as its proposed preferred measure | implemented/public; CRS/fixed-direction/source cross-section reproduced, configurable extensions labelled | P0 / 1 |
| `environmental.by_production.fgl` | preset | Murty--Russell--Levkoff modified FGL account: coordinatewise service expansion and residual contraction are assessed in separate by-production components and combined with equal weight | implemented/public; the CRS equations are checked on `by_production_component_bottleneck` with independently compiled component programmes and labelled configurable extensions | P0 / 1 |
| `environmental.factorial_multiequation` | technology | intended output, raw residual, and explicit treatment processes | planned | P2 / 3 |
| `environmental.material_balance_treatment` | technology | coefficient-generated primary residual enters an explicit end-of-pipe treatment process and final discharge obeys a material-balance identity | planned | P1 / 2 |
| `environmental.material_inflow` | family | minimum material-bearing inputs for an output commitment | partial | P0 / 1 |
| `environmental.material_inflow.coelli2007` | preset | Coelli source-native input-radial $TE$, minimum-material-inflow $EE$, and physical-content $EAE=EE/TE$ for a fixed desirable-output commitment; no prices, observed bad-output column, or explicit abatement account | implemented/public under CRS/VRS; the exact certificate covers ordinary nonnegative inputs/desirable outputs, common known nonnegative coefficients for one material, positive observed inflow, and a self-inclusive cross-section, closing $TE$, $EE$, $EAE$, and $EE=TE\times EAE$ without claiming a unique target or farm-level reproduction | P0 / 1 |
| `environmental.weak_g_balance` | technology | material conservation/summing-up restrictions | planned | P1 / 2 |
| `environmental.disposability_strategy` | family | source-qualified operating strategies that alter resource and pollution priorities | planned | P2 / 3 |
| `environmental.natural_disposability` | variant | resource saving combined with pollution reduction under the named natural-disposability account | planned | P2 / 3 |
| `environmental.managerial_disposability` | variant | selected environmental inputs may increase to support pollution control under the named managerial-disposability account | planned | P2 / 3 |
| `environmental.shadow_abatement` | operator | local pollutant shadow values and marginal abatement-cost intervals | planned | P1 / 2 |

Weak disposal and null jointness are independent. Weak disposal does not
identify one unique empirical technology. By-production, Coelli-style
material-input efficiency, weak-$G$ material balance, and factorial
multi-equation production remain distinct even when they reuse a directional
or additive engine. A by-production compiler must retain the declared
pollution-generating inputs, the intended and residual technologies, their
intersection, costly-disposal inequalities, and any coupling/dependence
constraints; a generic two-frontier label is insufficient.

For the Coelli preset, “environmental allocative” means selecting an input mix
against physical material-content coefficients; it is not price allocative
efficiency and requires no valuation data. CEPA Working Paper 06/2005
equations (23)--(26) and its explicit VRS convexity note delimit the certified
CRS/VRS programme. The source also defines weighted multiple pollutants in
equations (18)--(21), but their independent validation remains open.
NIRS/NDRS, multi-material aggregation, heterogeneous or
estimated coefficients, panel/custom/external-reference source equivalence,
the 183-farm empirical reproduction, and welfare, causal, damage, or
actual-emission claims are `deferred_to_next_version`.

The backward-compatible selector spelling `weak` must not be interpreted as
a technology claim. In the current public directional task it selects a
bad-output equality only. A study may report weak disposal only after choosing
one of the source-qualified common-factor, activity-specific, or generalized
technologies above and satisfying that leaf's own production-set contract.

## 10. Productivity and change registry

| Canonical ID | Kind | Native accounting rule | Status | Priority / tier |
|---|---|---|---|---|
| `productivity.malmquist.adjacent_geometric` | operator | four radial within/cross-period tasks; multiplicative change | implemented/public | P0 / 1 |
| `productivity.malmquist.decomposition` | family | non-executable umbrella for source-qualified decompositions | partial | P1 / 2 |
| `productivity.quasi_malmquist.grifell_lovell_pastor_1998` | operator | one-sided non-radial slack-based quasi-Malmquist change | planned | P1 / 2 |
| `productivity.generalized_malmquist.lovell_grifell_1999` | operator | source-qualified generalized Malmquist combining an MPI with a scale index, equivalently an output/input quantity-index ratio under its assumptions | planned | P1 / 2 |
| `productivity.malmquist.decomposition.fgnz_core` | preset | output-oriented CRS FGNZ core account $M=\mathrm{EFFCH}\times\mathrm{TECHCH}$ over adjacent contemporaneous technologies; API symbols `FGNZMalmquistProductivityIndex` and `FGNZMalmquist` | implemented/public catalog preset over `productivity.malmquist.adjacent_geometric`; exact four-distance frontier-shift and operating-performance-change accounts verified by an independent dense compiler; no published PWT reproduction claimed | P0 / 0 |
| `productivity.malmquist.decomposition.fgnz_pure_scale_extension` | operator | output-oriented enhanced FGNZ account $M=\mathrm{TECHCH}_C\times\mathrm{PEFFCH}\times\mathrm{SCH}$ and $\mathrm{EFFCH}=\mathrm{PEFFCH}\times\mathrm{SCH}$ using four CRS tasks plus two own-period VRS tasks; API symbols `FGNZEnhancedMalmquistProductivityIndex` and `FGNZEnhancedMalmquist` | implemented/public with an independent exact six-task oracle on a strictly positive matched panel; tested package extensions admit nonnegative partial-zero cells with positive row aggregates and explicit unbalanced `drop`/`raise` handling; an own-period VRS failure preserves the valid CRS core by software dependency policy; original OECD/PWT5 application not reproduced | P0 / 1 |
| `productivity.malmquist.decomposition.ray_desli` | operator | Ray--Desli output-oriented decomposition of the CRS Malmquist index into VRS pure-efficiency change, VRS opportunity change, and a cross-period scale factor; API symbols `RayDesliMalmquistProductivityIndex` and `RayDesliMalmquist` | implemented/public on a strictly positive matched panel with one or more inputs and exactly one desirable output; eight-task independent analytical oracle, source-defined partial-component behavior under VRS cross-task infeasibility, and no Penn World Table 5.6 reproduction claim | P0 / 1 |
| `productivity.malmquist.decomposition.balk` | deferred bibliographic candidate | neighboring scale/productivity decomposition whose native headline, components, and executable identity must be determined from the defining text | complete checksum-audited primary text, page-level equation/task freeze, and independent oracle are unavailable in the current evidence bundle; deferred to next version with no public API or machine record | — |
| `productivity.malmquist.decomposition.odonnell_scale_mix` | operator | O'Donnell source-qualified scale/mix and completeness accounting | planned | P1 / 2 |
| `productivity.malmquist.decomposition.technical_change_bias.fare_etal_1997` | operator | technical-change magnitude plus input- and output-bias components under the source Malmquist technology account | planned | P1 / 2 |
| `productivity.luenberger` | operator | additive directional performance-change indicator | implemented/public | P0 / 1 |
| `productivity.luenberger_hicks_moorsteen` | operator | additive complete output/input quantity accounting | planned | P1 / 2 |
| `productivity.luenberger_hicks_moorsteen.briec_kerstens_2004` | preset | Briec--Kerstens source-qualified additive output-minus-input quantity account with declared directions and completeness conditions | planned | P1 / 2 |
| `productivity.sbm_malmquist` | family | non-radial slacks-based productivity accounting; not a radial Malmquist alias | planned | P1 / 2 |
| `productivity.environmental_directional.adjacent_geometric` | deferred candidate | configurable four-distance environmental directional productivity account beyond the exact CFG source leaf | `deferred_to_next_version`; no defining source covers the complete configuration domain, so there is no public API or machine record; see `source_protocols/generic_environmental_directional_productivity.md` | — |
| `productivity.environmental_directional.global_ratio` | deferred candidate | configurable common-full-sample environmental directional productivity account beyond the exact Oh source leaf | `deferred_to_next_version`; no defining source covers the complete configuration domain, so there is no public API or machine record; see `source_protocols/generic_environmental_directional_productivity.md` | — |
| `productivity.malmquist_luenberger.chung_fare_grosskopf_1997` | operator | source-qualified CRS common-factor weak-disposal ML index with $g=(0,y,-b)$ and null jointness | implemented/public; exact four-distance frontier-shift and catch-up accounts verified by an independent dense compiler; published Swedish application not reproduced | P0 / 1 |
| `productivity.malmquist_luenberger.aparicio_pastor_zofio_2013` | preset | Aparicio--Pastor--Zofío bounded-bad-output CRS technology from the 2017 operational equations (5)--(6), composed with the standard four-distance adjacent Malmquist--Luenberger account; the observed programme is $g=(0,y,-b)$ and every pollutant has a componentwise, reference-period-specific observed maximum | implemented/public through `APZMalmquistLuenbergerProductivityIndex` (alias `APZMalmquistLuenbergerDEA`) on the source-qualified strictly positive input/bad-output domain; an independent exact compiler verifies all four contemporaneous roles and $ML=EC\times TC$ on the 2013 Table 1 fixture; cross-period infeasibility remains possible and the 2017 WIOD application is not reproduced | P0 / 1 |
| `productivity.malmquist_luenberger.apz` | discovery alias | short lookup spelling for `productivity.malmquist_luenberger.aparicio_pastor_zofio_2013` | discovery only; never serialized as a machine, preset, or result-provenance identity | — |
| `productivity.sbm_malmquist_luenberger` | family | slacks-based environmental productivity with source-qualified accounting identity | planned | P1 / 2 |
| `productivity.global_malmquist` | operator | Pastor--Lovell common full-sample radial benchmark with $GM=EC_G\times BPC_G$ under one fixed global vintage | implemented/public; output-oriented CRS source contract has an independent exact three-period certificate and production-free dense LP compiler covering all own/global tasks, peer provenance, decomposition, unit invariance, and circularity; non-CRS and input-oriented settings remain sensitivity extensions, and the published application is not reproduced | P0 / 1 |
| `productivity.biennial_malmquist` | operator | common adjacent-pair radial benchmark | implemented/public; independent exact CRS/output certificates separate contemporaneous distances, pair-pooled distances, cross-reference EC/BPC/TFP reconstruction, and raw adjacent-pair membership, including behaviorally active unmatched members and exclusion of a stronger outside-period frontier; no published application reproduction claimed | P0 / 1 |
| `productivity.global_malmquist_luenberger.oh_2010` | operator | Oh source-qualified CRS global environmental account: four nonnegative self-contained own/global distances, source BPG bounded above by one, and $GML=EC\times BPC$ over one fixed retrospective vintage | implemented/public; analytically derived exact two-/three-period accounts and independent dense compilation; published 26-country application not reproduced | P0 / 1 |
| `productivity.biennial_malmquist_luenberger` | preset | environmental ML accounting composed with an adjacent-pair pooled reference technology | planned | P1 / 2 |
| `analysis.window_efficiency` | operator | repeated static efficiency under a declared rolling reference window; no productivity-change identity implied | planned over implemented reference builder | P1 / 2 |
| `reference.sequential` | policy | current and prior practices only | implemented/public reference builder | P0 / 1 |
| `reference.window` | policy | rolling static benchmark window | implemented/public reference builder | P0 / 1 |
| `reference.global` | policy | full-study pooled benchmark | implemented/public reference builder | P0 / 1 |
| `reference.biennial` | policy | adjacent-pair pooled benchmark | implemented/public reference builder | P0 / 1 |
| `reference.contemporaneous` | policy | same-period comparison set | implemented/public | P0 / 0 |
| `reference.group` | policy component | comparison within a declared technology group | implemented internally by the O'Donnell--Rao--Battese radial metafrontier leaf; not a standalone public reference-policy operator | P0 / 2 |
| `reference.custom` | policy | explicitly supplied reference membership | implemented/public subset | P0 / 0 |
| `reference.leave_one_out` | policy | evaluated observation excluded from an otherwise declared comparison population | partial/public through Tone super-SBM; Andersen--Petersen radial remains an internal deferred prototype | P1 / 2 |
| `productivity.hicks_moorsteen` | operator | total-output quantity index divided by total-input quantity index | partial/public through the Bjurek adjacent-period leaf | P1 / 2 |
| `productivity.hicks_moorsteen.bjurek_1996` | preset | Bjurek source-qualified adjacent-period geometric output/input quantity-index ratio over two contemporaneous reference technologies, retaining all eight component distances | implemented/public; independent dense VRS analytical oracle for the exact bilateral eight-distance account, plus reciprocal-time, invariance, and failure-state evidence; no published empirical reproduction claimed | P0 / 1 |
| `productivity.fare_primont` | operator | fixed-reference multilateral input/output aggregators | planned | P1 / 2 |
| `productivity.fare_primont.odonnell_2012` | deferred candidate | O'Donnell source-qualified fixed-reference, transitive multilateral input/output aggregators and complete TFP account; author working paper located, final article/equations and numerical vector not yet frozen | deferred to next version; no public API or machine record | — |
| `productivity.cost_malmquist` | family | price-informed cost productivity under a source-qualified intertemporal identity | planned | P2 / 3 |
| `productivity.price_quantity_complete` | family | complete price/quantity productivity accounting with explicit price policy | planned | P2 / 3 |
| `productivity.profitability_decomposition.odonnell_2010` | operator | source-qualified decomposition of profitability change that keeps quantity-based productivity change and relative price recovery/terms-of-trade effects distinct | planned; requires matched quantity aggregators and intertemporal price policy | P1 / 2 |
| `productivity.profit_ratio_change.zhao_morita_maruyama_2019` | operator | source-qualified profit-ratio change and its technical, allocative, scale, and price-related components under the paper's identity | planned; components must reconstruct the native profit-ratio change | P2 / 3 |
| `productivity.growth_accounting.kumar_russell` | operator | non-parametric frontier change, operating-performance change, and capital-deepening decomposition | planned | P2 / 3 |
| `productivity.metafrontier` | operator | group performance/opportunity and technology-gap change | planned | P1 / 2 |
| `productivity.aggregate_mpi` | operator | economically weighted aggregation of unit-level productivity indexes | planned | P1 / 2 |
| `productivity.group_reallocation` | operator | group production potential and change attributable to between-unit resource reallocation | planned | P1 / 2 |

The Bjurek/Moorsteen terminology is registered inside the
Hicks--Moorsteen family rather than as a duplicate solver. Ordinary
Luenberger and Luenberger--Hicks--Moorsteen remain distinct. Window design is
a reference policy until paired with an index. Sequential reference embeds a
no-loss-of-past-best-practice assumption. Global, sequential, biennial, and
window results additionally retain the pooled-hull construction,
convexification rule, and RTS; a time-scope label alone does not identify the
attainable set.

All directional productivity results require economically comparable
directions across observations and periods. All decomposition component names
are source-qualified and tested against their reconstruction identity.

`reference.group` records the declared membership used by a composed analysis.
It is implemented inside the public radial metafrontier operator, but there is
no standalone public `reference.group` constructor or fitted result. Group
membership alone also does not define how the meta opportunity set is formed.
`productivity.malmquist.decomposition` is never directly executable: every
result stores a leaf `decomposition_id`, completeness statement, component
semantics, and reconstruction residual.

Oh's source theory compares any two periods using the same global information
set. The current package enumerates matched adjacent transitions; adjacency is
an evaluation and reporting protocol, not a restriction of the GML ratio.
For the named CRS leaf, all observations are pooled in one conical DEA
envelope. This is not a claim that the literal union notation printed in the
paper is set-theoretically identical to its conical hull. Each evaluated plan
belongs to its own-period and global references, so all four source distances
are nonnegative. The source best-practice gap is
$BPG^r=(1+D^r)/(1+D^G)\leq1$, and
$BPC^{t,t+1}=BPG^{t+1}/BPG^t$, preserving
$GML=EC\times BPC$. Changing the global sample vintage requires
retrospective recomputation. Reproduction of the 26-country application,
non-CRS scale accounts, alternative directions or environmental
technologies, literal-union estimation, other temporal references,
arbitrary-nonadjacent API enumeration, and inferential or welfare claims
remain `deferred_to_next_version`.

## 11. Network and dynamic presets

| Canonical ID | Kind | Composition | Status | Priority / tier |
|---|---|---|---|---|
| `network.relational.two_stage` | family | basic series graph + relational system/division efficiency | implemented/public subset through the Kao--Hwang CRS leaf | P1 / 2 |
| `network.relational.kao_hwang_2008` | preset | two-stage series graph + shared intermediate multiplier, process-specific intensities, multiplicative system/division identity, and Lim--Zhu projection | implemented/public | P0 / 0 |
| `network.radial_ratio` | family | graph-compatible radial/ratio measure whose result contract must state whether process efficiencies or only a system score are defined | implemented/public subset through the Färe--Grosskopf two-stage input/output-radial leaf | P1 / 2 |
| `network.radial.fare_grosskopf_2000` | preset | two-stage intermediate-products network + separate upstream/downstream intensities + disposable-surplus link inequality + one input- or output-radial system score; the evaluated organization's observed handoff is retained for comparison but does not condition the coordinated benchmark; CRS output orientation is the closed-series reduction of Färe--Grosskopf's 1995/1996 network output distance, while VRS composes that measure with the later separately convex Podinovski--Bouzdine-Chameeva technology; API symbol `FareGrosskopfNetworkRadialDEA`; no stage efficiencies are defined | implemented/public; primary source equations, independent dense output compiler, exact analytical input/output cases, conditional CRS Kao--Hwang system-score duality, and property/failure evidence; no original Färe--Grosskopf numerical table is claimed | P0 / 1 |
| `network.additive` | family | graph-compatible additive system/process accounting with the weight origin and link technology kept explicit | implemented/public subsets through the closed Chen leaf and the CRS open-DAG Cook leaf | P1 / 2 |
| `network.additive.chen_etal_2009` | preset | closed two-stage series graph + shared intermediate valuation, endogenous virtual-resource shares, CRS/VRS process intercepts, weighted arithmetic system identity, and Lim--Zhu split-link projection | implemented/public | P0 / 0 |
| `network.additive.cook_zhu_bi_yang_2010` | preset | source-checked CRS open serial, branching, or skip-link DAG + shared link valuations, endogenous component-input shares, and a weighted arithmetic system identity | implemented/public; general VRS, cycles, and source projection explicitly unsupported | P0 / 0 |
| `network.fare_grosskopf_2000` | source grouping | provenance grouping for the original paper's broader intermediate-product, fixed-factor-allocation, and dynamic network constructions; the executable basic series radial leaf is `network.radial.fare_grosskopf_2000`, while the paper's other constructions require separately frozen leaves | non-executable source grouping; not an alias for the implemented leaf or for all network DEA | P1 / 2 |
| `network.sequential.lewis_sexton_2004` | source grouping | Lewis--Sexton ordered hypothetical-sub-DMU lineage, including forward and reverse quantities and site-characteristic adjustments | partial/public through the forward-quantity radial leaf; not an alias for one simultaneous joint-network solve | P1 / 2 |
| `network.sequential.lewis_sexton_2004.forward_radial` | procedure/preset | input- or output-oriented forward nonnegative quantities, process-specific standard RTS, ordered node evaluation, and propagated hypothetical quantities over an acyclic organization | implemented/public; defining two-DMU oracle, multi-endpoint aggregation, invariance, graph-order, and fail-closed evidence | P1 / 2 |
| `network.input_output.prieto_zofio_2007` | preset | sectoral input--output network technology with primary resources, intermediate production, final demand, and fixed observed trade roles; exact account equations remain unfrozen | deferred to the next version because the complete primary source and numerical oracle are unavailable; no public API or machine method record | P2 / 3 |
| `network.relational.general.kao_2009` | preset | source-qualified relational account for general series--parallel systems | planned/evidence | P1 / 2 |
| `network.relational.parallel.kao_2012` | preset | source-qualified parallel relational decomposition with common valuation; VRS interpretation/nonnegativity requires an explicit compatibility policy | planned/evidence | P2 / 3 |
| `network.legacy.independent_two_stage` | neighbor family | historically important separately fitted stage frontiers that need not return a jointly feasible intermediate plan | comparison/diagnostic only; source-specific leaves may follow | P2 / 3 |
| `network.sbm.tone_tsutsui_2009` | preset | general network + division-specific intensities, source CRS/VRS, per-link fixed-observed, free-coordinated, recipient-accountable incoming, or supplier-accountable outgoing roles, exogenous division weights, and orientation-qualified SBM accounts; every link preserves bilateral continuity and every accountable slack is counted once | implemented/public; neutral service-chain cases check fixed/free links, system/process accounts, and equations (26)--(27) without redistributing the source tables | P0 / 0 |
| `network.sbm.tone_tsutsui_2009.accountable_input_link` | specialization | input-oriented equation (26): an incoming link is normalized and counted once inside its recipient process input account while the supplier and recipient peer plans remain equal | implemented/public discovery specialization through `ToneTsutsuiNetworkSBM(link_kinds=...)`; exact $5/8$ analytical system oracle, unit invariance, responsibility, continuity, and sparse accounting checks | P0 / 0 |
| `network.sbm.tone_tsutsui_2009.accountable_output_link` | specialization | output-oriented equation (27): an outgoing link is normalized and counted once inside its supplier process output account while the supplier and recipient peer plans remain equal | implemented/public discovery specialization through `ToneTsutsuiNetworkSBM(link_kinds=...)`; exact $4/7$ analytical system oracle, unit invariance, responsibility, continuity, and sparse accounting checks | P0 / 0 |
| `network.ebm` | family | network epsilon-based measure under a declared link and aggregation rule | planned | P2 / 3 |
| `network.directional` | family | process graph + directional measure | planned | P1 / 2 |
| `network.economic` | family | cost/revenue/profit objective over a process graph with explicit internal transfer valuation | planned | P2 / 3 |
| `network.environmental` | family | undesirable intermediate/final outputs + explicit disposal | planned | P1 / 2 |
| `network.environmental.weak_activity_specific.kalhor_kazemi_matin_2018` | preset | general process graph + external/internal desirable and undesirable products + process-specific intensities + activity-specific weak-disposal linearization + source input-radial measure | implemented/public; corrected source technology is checked by an independent dense compiler on `environmental_recovery_chain` and `environmental_circular_chain` | P0 / 1 |
| `network.environmental.joint_input_sbm.lozano_2015` | preset | parallel intended-production/pollution-generation graph + identity-coupled pollution-generating inputs + source non-oriented network SBM and process accounts | planned; application tables located, raw-data oracle not certified | P1 / 2 |
| `network.environmental.material_balance_treatment.hampf_2014` | preset | intended production + coefficient-based primary-pollution balance + explicit end-of-pipe treatment + production/abatement efficiency decomposition | planned; application tables located, raw-data oracle not certified | P1 / 2 |
| `network.shared_resource` | family | endogenous shared-resource allocation | planned | P1 / 2 |
| `network.multi_activity.shared_input.beasley_1995` | preset | multiple organizational activities with an explicit shared-input allocation rather than duplicated resource use | planned | P0 / 2 |
| `network.multi_activity.multicomponent_shared_input.cook_hababou_tuenter_2000` | preset | component-level and aggregate performance with an endogenous split of inputs shared across bank-branch activities | planned | P1 / 2 |
| `network.multi_activity.core_business_multiplant.cook_green_2004` | preset | overlapping business components, shared resources, component performance, and source-defined core-business identification across plants | planned | P2 / 3 |
| `network.hierarchical.groups.cook_chai_doyle_green_1998` | preset | group- and unit-level ratings with source-defined cross-level adjustment and aggregation across alternative groupings | planned | P1 / 2 |
| `network.hierarchical.simultaneous.cook_green_2005` | preset | simultaneous top-level plant and component-unit performance account with level-specific factors and explicit allocation of plant-level quantities | planned | P1 / 2 |
| `network.projection.frontier_validity.chen_cook_kao_zhu_2013` | procedure | distinguish multiplier-based divisional appraisal from envelopment-feasible network frontier projection and certify link-feasible targets | planned | P0 / 1 |
| `network.governance` | discovery grouping | historical network-governance wording resolves to a declared process graph composed with `evaluation.governance`; it is not a graph topology or executable method by itself | merged into the evaluation-protocol framework | P1 / 2 |
| `network.governance.two_stage.liang_cook_zhu_2008` | preset | centralized and non-cooperative two-stage plans with source-fixed authority, objective, move order, and solution concept | planned/evidence; not a topology switch | P2 / 3 |
| `network.scale_rts` | family | non-executable umbrella for system and process scale/RTS under a source-qualified network decomposition | planned | P2 / 3 |
| `network.scale_rts.two_stage.chen_zhu_2019` | preset | source-qualified two-stage system/process scale-efficiency construction using the paper's nonlinear-to-second-order-cone transformation under declared CRS/VRS tasks | planned; requires conic-capable compiler/backend | P2 / 3 |
| `network.productivity` | family | non-executable umbrella for productivity change with intermediate-product and graph accounting retained | planned | P2 / 3 |
| `network.productivity.two_stage.kao_hwang_2014` | preset | source-qualified multi-period two-stage common-weight global Malmquist construction with system, period, and process identities retained | planned | P2 / 3 |
| `panel.multiperiod_aggregative.park_park_2009` | operator/preset | one common input- or output-radial rating across separate contemporaneous period technologies, followed by source raw-slack completion, without a state transition or carry-over technology; API symbols `ParkParkMultiperiodAggregativeDEA`, `MultiperiodAggregativeDEA` | implemented/public; `multiperiod_trajectory_contrast` checks factors, classifications, slacks, and result identities; explicitly outside `dynamic.*` | P1 / 2 |
| `dynamic.intertemporal.fare_grosskopf` | family | intertemporal production technology with explicit temporal links | deferred to next version; defining dynamic chapter, unique source leaf, and numerical oracle unavailable | P2 / 3 |
| `dynamic.investment.nemoto_goto` | family | investment, quasi-fixed capital, adjustment cost, and intertemporal substitution | deferred to next version; defining full texts and numerical oracle unavailable | P2 / 3 |
| `dynamic.optimal_control.sengupta_1999` | preset | discounted capital-path and operating-cost dynamic efficiency under a source economic-information contract | planned/evidence | P2 / 3 |
| `dynamic.scale_rts.sueyoshi_sekitani_2005` | operator/preset | returns-to-scale analysis for the source quasi-fixed-input intertemporal technology | planned/evidence | P2 / 3 |
| `dynamic.weighted_additive.adjustment_cost.aparicio_kapelko_2019` | preset | input, output, and investment slack account over a source adjustment-cost technology | planned/evidence; unit-dependent native inefficiency retained | P1 / 2 |
| `dynamic.network_lagged_intermediate.chen_2009` | preset | network technology in which current intermediate production affects later process output | planned/evidence; not a carry-over-role switch on network SBM | P2 / 3 |
| `dynamic.sbm.tone_tsutsui_2010` | preset | complete trajectory cohort + period-specific intensities + same-$Z_t$ continuity + source CRS/VRS + good/bad/free/fixed carry-overs + input/output/non-oriented dynamic-SBM accounts | implemented/public; `dynamic_carryover_portfolio` checks the named carry-over roles, trajectory accounts, and the ex-post free-carry-over specialization | P0 / 0 |
| `dynamic.network_sbm.tone_tsutsui_2014` | preset | Tone--Tsutsui process-by-period graph + four within-period link roles with continuity in every case + typed interperiod carry-overs + division-level CRS/VRS + nonnegative normalized period/division weights + source system/division/period SBM aggregation + named terminal-boundary resolution | implemented/public with sparse compilation, exact static-network/dynamic reductions, and an independent joint two-period/two-process CRS non-oriented primal--dual certificate in which both link and carry-over continuity change the optimum; formal equations checked and terminal index confirmed internally inconsistent; no published application reproduction claimed | P0 / 1 |
| `dynamic.environmental.additive_weak_disposal.cuadros_etal_2020` | preset | multi-period electricity technology + current-period fossil-generation/CO2 weak-disposal pair + capacity links + source raw-additive slack objective and ex-post period score | planned only after source freeze; unit-scaling risk and incomplete oracle data recorded | P2 / 3 |
| `dynamic.environmental.by_production.adjustment_cost.dakpo_oude_lansink_2019` | preset | intertemporal by-production technology linking intended output, pollution generation, investment, quasi-fixed state, and adjustment costs; not a repeated static environmental frontier or an undesirable carry-over relabel | planned; primary equations and an independent numerical oracle must be frozen before implementation | P1 / 2 |
| `dynamic.efficiency` | family | source-qualified multi-period efficiency retaining carry-over/state feasibility | planned | P2 / 3 |
| `dynamic.productivity` | family | productivity change over a dynamic technology rather than repeated static frontiers | planned | P2 / 3 |
| `dynamic.productivity.malmquist.intertemporal_fare_grosskopf` | operator family | source-qualified Malmquist change whose distance tasks retain the intertemporal production technology, state feasibility, and boundary conditions | planned; exact source leaf and reconstruction identity under audit | P1 / 2 |
| `dynamic.productivity.malmquist.dynamic_sbm.tone_tsutsui` | operator family | productivity change derived from a dynamic-SBM technology with carry-over continuity and source period/system aggregation preserved | planned; exact source leaf and reconstruction identity under audit | P1 / 2 |

Independent stage-by-stage DEA is not network DEA. Window DEA and Malmquist
are not dynamic production technologies. Only explicit link/state/transition
constraints earn the network/dynamic labels.

The Färe--Grosskopf, Kao--Hwang, Chen-et-al., and Tone--Tsutsui records are
canonical recipes, not four spellings of “network DEA.” They need not differ
on every axis: under a matched closed two-stage CRS domain, the
Färe--Grosskopf input-radial programme is strictly dual to the Kao--Hwang
primary centralized programme and the two return the same system score. That
conditional identity does not make the full methods aliases.
`network.radial.fare_grosskopf_2000` stops at one system score and a
solver-selected coordinated operating plan; it defines no stage efficiency,
shared intermediate multiplier account, product decomposition, stage range,
or midpoint target. The Kao--Hwang leaf adds those valuation, attribution,
and projection contracts. The VRS option of
`FareGrosskopfNetworkRadialDEA` is separately attributed to
Podinovski--Bouzdine-Chameeva (2021), not to Färe--Grosskopf (2000). Other
network leaves differ through their graph, intensity/link coupling, system
aggregation, native score, and process-account rules. The graph compiler may
be shared, but each result must retain the expanded recipe and any alternate
optimum policy.

In that radial leaf, “intermediate observed once” is a data-storage rule, not
a constraint that fixes the evaluated organization's realized handoff
$z_o$. The coordinated benchmark chooses its upstream supply and downstream
requirement endogenously from the reference technology. The link table keeps
$z_o$ only as a comparison value and marks it as non-conditioning. Peer
display thresholds likewise do not alter targets: targets use the complete
intensity vectors, while the summary discloses the upstream and downstream
coefficient mass omitted from the displayed peer table.
In the Tone--Tsutsui source preset, `fixed` and `non-discretionary` links are
exact naming aliases, as are `free` and `discretionary` links. The two link
policies are not aliases of each other: fixed links reproduce the assessed
organization's observed handoff, whereas free links choose one coordinated
handoff shared by the supplying and receiving divisions. Its exogenous
division-importance weights are not link weights, and the base objectives do
not score link deviations directly. The dynamic-network preset additionally
retains source `as_input` and `as_output` link roles. The recipient owns the
input-style slack in the first case and the supplier owns the output-style
slack in the second, but both cases still impose supplier--recipient
intensity continuity. One-sided score attribution is not a one-sided feasible
technology.
The implemented Tone--Tsutsui dynamic leaf likewise treats exact historical
names as API aliases only within the source equations: `good`/`desirable`,
`bad`/`undesirable`, `free`/`discretionary`, and
`fixed`/`non-discretionary`. These labels do not collapse economic effect,
managerial control, lag, decay, transition, or boundary policy in the general
framework. The base free-carry-over LP and
`dynamic.sbm.tone_tsutsui_2010.free_adjusted_post` share one optimized
technology but retain different reporting contracts; the source
free-carry-over MIP is a future genuinely mixed-integer leaf.
The implemented Kao--Hwang leaf is intentionally narrower than the family: it
accepts the basic two-node CRS series graph, never infers a VRS extension, and
does not turn its product identity into a rule for additive, SBM, parallel, or
general-network models. Its optional bounds solve distinguishes a fixed
system score from a potentially nonunique attribution of performance across
the two stages.

## 12. Heterogeneity, diagnostics, and statistical procedures

| Canonical ID | Kind | Permitted claim | Status | Priority / tier |
|---|---|---|---|---|
| `heterogeneity.metafrontier` | non-executable family umbrella | performance within known group opportunities and gap to meta opportunities | one implemented/public radial leaf; all other family members are next-version candidates | P1 / 2 |
| `heterogeneity.metafrontier.radial.odonnell_rao_battese_2008` | operator | matched group- and pooled-meta radial efficiency, canonical metatechnology ratio (`MTR`; historical `TGR` alias), and exact reconstruction identity | implemented / public | P0 / 2 |
| `heterogeneity.program_efficiency.ccr_1981` | procedure | performance difference associated with declared programmes after separating within-programme managerial efficiency | planned | P1 / 2 |
| `heterogeneity.frontier_difference.global.asmild_2015` | procedure | global comparison of group frontier locations under a source-qualified common technology construction | planned | P1 / 2 |
| `heterogeneity.nonhomogeneous_dmu` | family | structurally different factor availability or specialization under an explicit comparability technology; not missing-data repair | planned | P2 / 3 |
| `heterogeneity.nonhomogeneous_dmu.cook_etal_2013` | preset | source-qualified technology for units that do not all undertake the same production activities | planned | P1 / 2 |
| `analysis.reference_frequency.selected_plan` | procedure | frequency with which each observed organization appears through a reported active peer edge strictly above the source `peer_tolerance` in one certified solver-selected plan from a static convex global cross-section; total count equals self plus other use, and `reference_rate` divides that total by all evaluated organizations | implemented/public as `reference_frequency`; source threshold provenance, zero additional solves, and complete-account fail closure; no alternate-optimum, global-reference-set, influence, outlier, ranking, or inference claim; `handbook_sensitivity` inside study design | P0 / 1 |
| `diagnostics.influence` | procedure | observations that materially determine benchmarks; audit, never automatic deletion | planned | P1 / 2 |
| `inference.bootstrap.frontier_efficiency` | procedure family | non-executable umbrella for supported bias/SE/confidence statements under a boundary-compatible DGP | planned | P1 / 2 |
| `inference.bootstrap.frontier_efficiency.simar_wilson_1998` | procedure | source-qualified smoothed bootstrap for supported full-frontier efficiency estimators | planned | P1 / 2 |
| `inference.bootstrap.directional_distance.simar_vanhems_wilson_2012` | procedure | source-qualified consistent bootstrap/asymptotic inference for a supported convex directional-distance estimator and declared direction | planned | P1 / 2 |
| `inference.bootstrap.productivity` | procedure family | non-executable umbrella for sampling uncertainty of named productivity operators | planned | P1 / 2 |
| `inference.bootstrap.productivity.simar_wilson_1999` | procedure | source-qualified bootstrap for the declared Malmquist index, components, panel structure, and frontier estimators | planned | P1 / 2 |
| `inference.tests.structure` | procedure family | non-executable umbrella for RTS, convexity, group, and technology hypotheses | planned | P1 / 2 |
| `inference.tests.rts.simar_wilson_2002` | procedure | bootstrap test of CRS versus supported alternative scale technologies under a declared estimator and DGP | planned | P1 / 2 |
| `inference.tests.separability.daraio_simar_wilson` | procedure | test whether operating conditions can be separated from frontier formation before a second-stage design is chosen | planned | P1 / 2 |
| `inference.tests.efficiency_distribution.simar_zelenyuk_2006` | procedure | weighted test of equality between declared efficiency-score distributions with estimator and dependence assumptions retained | planned | P1 / 2 |
| `inference.tests.technology_structure.kneip_simar_wilson_2016` | procedure | source-qualified tests of convexity, returns to scale, and group or technology restrictions for supported frontier estimators | planned | P1 / 2 |
| `inference.asymptotic.mean_efficiency` | procedure | estimator-, dimension-, RTS-, and DGP-specific asymptotic/CLT statement for aggregate efficiency | planned | P2 / 3 |
| `inference.asymptotic.productivity` | procedure | estimator-specific CLT for a named productivity index and decomposition | planned | P2 / 3 |
| `inference.productivity.aggregate.pham_simar_zelenyuk_2023` | procedure | source-qualified inference for an economically weighted aggregate productivity measure with the unit index, aggregation weights, frontier estimator, and sampling design fixed together | planned | P1 / 2 |
| `inference.subsampling` | non-executable procedure-family umbrella | reserves a namespace for measure-, estimator-, sampling-, and dependence-specific subsampling leaves; it makes no generic inferential claim | next-version planning only; no executable generic procedure | P2 / 3 |
| `context.second_stage.simar_wilson` | procedure family | non-executable umbrella for truncated-regression association with inefficiency under separability | planned | P1 / 2 |
| `context.second_stage.simar_wilson_2007.algorithm1` | procedure | single-bootstrap truncated-regression inference using the source's supported efficiency-score convention | planned | P1 / 2 |
| `context.second_stage.simar_wilson_2007.algorithm2` | procedure | double-bootstrap procedure including the source-qualified first-stage bias correction before truncated regression | planned | P1 / 2 |
| `context.second_stage.banker_natarajan_2008.ols` | procedure | source-qualified DEA productivity/OLS contextual analysis under the paper's stochastic, separability, independence, and transformation conditions | planned | P1 / 2 |
| `context.operating_conditions` | data/context role | observed conditions may alter attainable opportunities or score distributions under a declared empirical design | planned | P1 / 2 |
| `context.three_stage.fried2002` | procedure | DEA-slack, parametric SFA decomposition, observation adjustment, and DEA refit under explicit distributional assumptions | planned with strong-assumption warning | P1 / 2 |
| `uncertainty.stochastic` | family | probability-model-specific random-data or stochastic-technology semantics | planned | P2 / 3 |
| `uncertainty.stochastic.random_deviation` | family | source-qualified stochastic deviations from frontier constraints | planned | P2 / 3 |
| `uncertainty.stochastic.measurement_error` | family | explicit measurement-error model and resulting efficiency statement | planned | P2 / 3 |
| `uncertainty.stochastic.pps` | family | stochastic production-possibility-set semantics under a declared probability model | planned | P2 / 3 |
| `uncertainty.stochastic.chance_constrained` | family | probability-model/risk-tolerance-specific feasibility | planned | P2 / 3 |
| `uncertainty.interval_idea` | family | implications of bounded/ordered/ratio incomplete information | planned | P2 / 3 |
| `uncertainty.fuzzy` | family | membership/possibility statements | planned | P2 / 3 |
| `uncertainty.robust_polyhedral` | family | worst-case performance over box/polyhedral/budgeted sets | planned | P2 / 3 |
| `uncertainty.robust_conic` | family | ellipsoidal/conic uncertainty with optional backend | planned | P2 / 3 |
| `uncertainty.distributionally_robust` | family | worst-case distributional statement over an ambiguity set | planned / research-only until an ambiguity set, identification claim, and oracle contract are frozen | P2 / 3 |
| `inference.bayesian_dea` | procedure | likelihood/prior-specific posterior efficiency statement | planned / research-only until a likelihood, prior, posterior object, and validation contract are frozen | P2 / 3 |

The 2025 finite-sample/CLT work of
[Zelenyuk and Zhao](https://doi.org/10.1017/S1365100525000094) remains a
bibliographic evidence candidate. It has no canonical method ID until its
supported productivity operator, source protocol, independent numerical
oracle, and typed result contract are frozen. The same rule prevents
`inference.subsampling` from becoming an executable catch-all: every future
subsampling leaf must be named and validated for one estimator, measure,
sampling design, and dependence structure.

Bootstrap is not a generic “repeat any model” decorator. Simar--Wilson second
stage, conditional DEA, and Fried's DEA--SFA--DEA adjustment workflow are not
variants of one algorithm. The last changes the observations used to fit the
final frontier and must preserve its parametric noise assumptions and
pre-/post-adjustment data. Order-$m$ and
order-$\alpha$ are not a single parameterized estimator. Robust statistics,
robust optimization, chance constraints, intervals, fuzzy membership, and
Bayesian posterior uncertainty are different claims.

The Simar--Wilson 2007 Algorithm 1 and Algorithm 2 leaves are separately
registered because the second adds a first-stage bias-correction bootstrap.
They are not a toggle on an ordinary OLS regression, and neither supplies a
causal interpretation of operating conditions.

The namespaces reflect distinct layers. `context.operating_conditions`
identifies conditioning information; `estimator.conditional.*` and
`estimator.partial.*` change frontier estimation; `uncertainty.stochastic.*` uses a
probability model to define random-data or feasibility statements;
`uncertainty.robust_*` protects against a declared uncertainty set; and
`inference.*` quantifies uncertainty about a supported estimator. Sharing an
LP backend does not merge these claims.

## 13. Decision-support procedures

| Canonical ID | Kind | Scope | Status | Priority / tier |
|---|---|---|---|---|
| `decision.inverse_dea` | procedure | required input/output changes at a maintained efficiency condition | planned | P2 / 3 |
| `decision.inverse_dea.wei_zhang_zhang_2000` | preset | source-qualified inverse DEA adjustment preserving a declared efficiency condition while selected quantities change | planned | P2 / 3 |
| `decision.central_allocation` | procedure | coordinated resources and targets across related units | planned | P2 / 3 |
| `decision.central_allocation.lozano_villa_2004` | preset | centralized reallocation of resources and production targets under the source system objective and conservation constraints | planned | P2 / 3 |
| `decision.fixed_cost_allocation` | procedure | equitable allocation of a common cost or indivisible overhead under declared efficiency and fairness principles | planned | P2 / 3 |
| `decision.fixed_cost_allocation.cook_kress_1999` | preset | Cook--Kress characterization of shared-cost allocations using efficiency invariance and Pareto minimality | planned | P2 / 3 |
| `decision.fixed_cost_allocation.beasley_2003` | preset | joint fixed-cost/resource allocation and output-target procedure based on a declared average-efficiency objective and source tie-breaking phases | planned | P2 / 3 |
| `decision.fixed_cost_allocation.cook_zhu_2005` | preset | executable equitable shared-cost allocation extending the Cook--Kress principles under source-defined orientation and scale conditions | planned | P2 / 3 |
| `decision.fixed_sum_zsg` | family | one unit's gain changes others' feasible outcomes | planned | P2 / 3 |
| `decision.fixed_sum_zsg.lins_etal_2003` | preset | source-qualified zero-sum-gains technology in which reassignment to one unit changes the opportunities of the others | planned | P2 / 3 |
| `decision.merger_restructuring` | procedure | attainable performance after organizational recombination | planned | P2 / 3 |
| `decision.merger_restructuring.bogetoft_wang_2005` | preset | source-qualified gains-from-merger and restructuring account over declared pre- and post-combination technologies | planned | P2 / 3 |
| `decision.game` | family | source-qualified cooperative or non-cooperative strategic interaction | planned | P2 / 3 |
| `decision.bargaining` | family | negotiated allocation under a declared bargaining solution | planned | P2 / 3 |
| `decision.bargaining.targets.lozano_hinojosa_marmol_2019` | preset | variable-level DEA target selection under a declared Nash, Kalai--Smorodinsky, egalitarian, or utilitarian bargaining solution | planned | P2 / 3 |
| `decision.bargaining.fixed_sum.lozano_2023` | preset | Nash-bargaining targets over a fixed-sum DEA technology with variable-level players | planned | P2 / 3 |
| `decision.scenario_forecast` | procedure | declared future technology/constraint scenarios | planned | P2 / 3 |

These results are prescriptive scenarios conditional on stated values and
constraints. They are not causal forecasts.

## 14. Typed relationship registry

A–D compares two complete executable study specifications. It is not used for
dependency edges such as `composes` or `requires`.

| Source | Target | Relation | Difference axis | Full-study level | Conditions |
|---|---|---|---|---|---|
| `static.radial.crs` | `static.radial` | `specialization_of` | technology/RTS | A | `rts=crs`; orientation and target policy remain explicit |
| `static.radial.vrs` | `static.radial` | `specialization_of` | technology/RTS | A | `rts=vrs`; orientation and target policy remain explicit |
| `static.radial.crs.input` | `static.radial` | `preset_of` | technology, performance, evaluation protocol | A | explicit `CCRInput`; CRS, input orientation, native $\theta$, and DEAPack row-scaled lexicographic slack completion are fixed |
| `static.radial.crs.output` | `static.radial` | `preset_of` | technology, performance, evaluation protocol | A | explicit `CCROutput`; CRS, output orientation, native $\phi$ with displayed $1/\phi$, and DEAPack row-scaled lexicographic slack completion are fixed |
| `static.radial.vrs.input` | `static.radial` | `preset_of` | technology, performance, evaluation protocol | A | explicit `BCCInput`; VRS, input orientation, native $\theta$, and DEAPack row-scaled lexicographic slack completion are fixed |
| `static.radial.vrs.output` | `static.radial` | `preset_of` | technology, performance, evaluation protocol | A | explicit `BCCOutput`; VRS, output orientation, native $\phi$ with displayed $1/\phi$, and DEAPack row-scaled lexicographic slack completion are fixed |
| `productivity.malmquist.decomposition.fgnz_core` | `productivity.malmquist.adjacent_geometric` | `preset_of` | technology, performance, analysis | A | explicit `FGNZMalmquistProductivityIndex`; output orientation, CRS, adjacent contemporaneous references, four Farrell distance roles, and the source core $\mathrm{EFFCH}\times\mathrm{TECHCH}$ identity are fixed; the enhanced $\mathrm{PEFFCH}\times\mathrm{SCH}$ account is excluded |
| `productivity.malmquist.decomposition.fgnz_pure_scale_extension` | `productivity.malmquist.adjacent_geometric` | `shares_compiler` | technology, evaluation protocol, analysis | — | reuses the common output-oriented CRS four-distance headline and radial task compiler, then adds exactly two own-period VRS tasks for FGNZ's $\mathrm{EFFCH}=\mathrm{PEFFCH}\times\mathrm{SCH}$ allocation; it is a distinct method, not another preset name for the core |
| `productivity.malmquist.decomposition.fgnz_pure_scale_extension` | `productivity.malmquist.decomposition.ray_desli` | `contrasts_with` | data roles, technology, reference, evaluation protocol, analysis | D | the methods share the CRS headline and own-period pure-efficiency ratio on their matched domain, but enhanced FGNZ uses two VRS-own tasks and retains CRS `TECHCH`, whereas Ray--Desli uses four VRS own/cross tasks and allocates a VRS opportunity-change term plus a different scale factor; component aliases are forbidden |
| `productivity.malmquist.decomposition.ray_desli` | `productivity.malmquist.adjacent_geometric` | `shares_compiler` | technology, evaluation protocol, analysis | — | reuses the common CRS four-distance headline and radial task compiler, then adds four VRS tasks and Ray--Desli's distinct $\mathrm{PEFFCH}\times\mathrm{TECHCH}(v)\times\mathrm{SCH}(v)$ account; this is neither an alias nor the FGNZ scale extension |
| `static.radial.fch.green_cook_2004` | `static.radial.fdh` | `contrasts_with` | technology/activity combination | C | under matched additive nonnegative quantities with positive observation-level input/output aggregates, cross-sectional comparison population, orientation, self-membership, and ordinary free disposal, $T_{FDH}\subseteq T_{FCH}$; hence $\theta^{FCH}\leq\theta^{FDH}$ and $\phi^{FCH}\geq\phi^{FDH}$; no VRS nesting follows |
| `static.radial.frh` | `static.radial.fch.green_cook_2004` | `contrasts_with` | technology/replication bounds | C | under the same matched conditions, $T_{FCH}\subseteq T_{FRH}$; hence $\theta^{FRH}\leq\theta^{FCH}$ and $\phi^{FRH}\geq\phi^{FCH}$; relaxing FCH binary selections yields bounded $0\leq\lambda_j\leq1$ intensities with a nonempty constraint, not CCR |
| `static.radial.frh` | `static.radial.fdh` | `contrasts_with` | technology/activity combination | D | FDH selects one observed template; FRH may combine nonnegative integer copies of several templates |
| `static.radial.frh` | matching CRS `static.radial` recipe | `contrasts_with` | technology/integrality | D | the CRS convex programme is the continuous relaxation of the matched FRH programme, but fractional reference activities are economically inadmissible under FRH |
| `technology.frh` | matching `technology.convex_envelopment` under CRS | `contrasts_with` | technology/integrality | D | replacing $z\in\mathbb Z_+^n$ by $z\in\mathbb R_+^n$, with matched data and disposal, gives the ordinary CRS convex technology; this is an informative continuous relaxation, not an exact method reduction or alias |
| `technology.frh` | `technology.integer_discrete.kuosmanen_kazemi_matin_2009` | `contrasts_with` | integrality locus | D | FRH makes replication counts integer while observed quantities may be continuous; integer/discrete DEA gives declared production variables their own natural-divisibility semantics |
| `static.radial.frh` | `static.additive` | `contrasts_with` | technology versus performance criterion | D | FRH changes which operating plans are attainable; an additive measure changes how input excesses and output shortfalls are valued on a separately declared technology |
| matching radial recipe | `static.directional_distance` | `exact_score_transform` | measure/path | A | observation-scaled pure input or output direction; matching signs, RTS, reference, and target phase |
| `static.range_directional.portela_thanassoulis_simpson_2004` | `static.directional_distance` | `composes` | data roles/technology/reference/performance/evaluation protocol | — | reuses the VRS input-contraction/output-expansion directional programme but fixes finite signed desirable data, a focal-to-coordinatewise-ideal range direction, exact extrema/technology reference matching with self-inclusion, three orientations, and the $1-\beta$ efficiency report; compiler reuse is not semantic equivalence |
| `static.generalized_distance.chavas_cox` at $\alpha=0$ | `static.radial` input orientation | `exact_score_transform` | measure/path | A | same data, CRS/VRS technology, reference, and slack policy; $\delta=\theta^I$ |
| `static.generalized_distance.chavas_cox` at $\alpha=1$ | `static.radial` output orientation | `exact_score_transform` | measure/path | A | same data, CRS/VRS technology, reference, and slack policy; $\delta=1/\phi^O$ |
| `static.generalized_distance.chavas_cox` at $\alpha=1/2$ | future `static.hyperbolic.standard_reciprocal` | `conditional_candidate_transform` | measure/path | — | only if a complete source freeze later establishes the same observation, reference, technology, RTS, disposal, target policy, and bounded reciprocal score $h$; then $\delta=h^2$. No current Level-A or public-method claim is made |
| `static.generalized_distance.chavas_cox` | `static.directional_distance` | `contrasts_with` | measure/path | B | GDF is a multiplicative proportional resource/service contract; DDF is an additive quantity-change contract with explicit direction units |
| historical `static.erg` | `static.sbm.nonoriented.tone2001` | `alias` | none on approved domain | A | standard strictly positive non-oriented data, matched technology and weights |
| `static.sbm.input.tone2001` | `static.sbm.nonoriented.tone2001` | `variant_of` | performance/valuation/evaluation protocol | B | matched strictly positive data, technology, RTS, and reference; only input slacks enter the oriented score |
| `static.sbm.output.tone2001` | `static.sbm.nonoriented.tone2001` | `variant_of` | performance/valuation/evaluation protocol | B | matched strictly positive data, technology, RTS, and reference; only output slacks enter the oriented score |
| `static.sbm.nonoriented.tone2001` | `static.radial` | `contrasts_with` | measure | B | same data, estimator, technology, RTS, and reference |
| `economic.cost` | `static.radial` | `shares_compiler` | measure/valuation | B | same quantities, estimator, RTS, and reference; input prices enter only the cost objective |
| `analysis.allocative_decomposition.cost_input_radial` | `economic.cost` | `composes` | analysis | — | internally fits the matched input-radial component |
| `economic.revenue` | `static.radial` | `shares_compiler` | measure/valuation | B | same quantities, estimator, RTS, and reference; output prices enter only the revenue objective |
| `analysis.allocative_decomposition.revenue_output_radial` | `economic.revenue` | `composes` | analysis | — | internally fits the matched output-radial component |
| `economic.profit.maximum` | `economic.cost` | `contrasts_with` | decision context/valuation | B | profit permits both input and output choice; cost holds the output commitment |
| `economic.profit.maximum` | `economic.revenue` | `contrasts_with` | decision context/valuation | B | profit permits both input and output choice; revenue holds input capacity |
| `economic.profit.maximum` | shared economic LP compiler | `shares_compiler` | objective/constraints | — | profit has no observation-specific input-capacity or output-commitment rows; VRS finite-value and shutdown policies remain explicit |
| `economic.nerlovian.ccf1998` | `economic.profit.maximum` | `composes` | measure/valuation | — | uses the matched raw profit gap and divides it by the price value of the declared direction |
| `economic.nerlovian.ccf1998` | `static.directional_distance` | `composes` | measure/analysis | — | the same data, convex technology, RTS, reference, solver policy, and direction supply the directional technical component |
| `economic.profitability.return_to_dollar` | `economic.profit.maximum` | `contrasts_with` | measure/normalization/RTS | B | revenue divided by positive input expenditure is scale invariant; maximum profit is an additive net-value level that may be negative or unbounded |
| `economic.profitability.return_to_dollar` | CRS/VRS convex envelopment | `exact_reduction` | solver | A | with positive candidate costs, any combined ratio is a cost-weighted average of reference ratios, so the maximum is an extreme reference ratio |
| `analysis.allocative_decomposition.profitability_gdf.zofio_prieto_2006` | `economic.profitability.return_to_dollar` | `composes` | analysis | — | adds matched CRS/VRS Chavas--Cox GDF and scale/allocative factors; the value optimizer alone does not emit them |
| `analysis.allocative_decomposition.profitability_gdf.zofio_prieto_2006` | `static.generalized_distance.chavas_cox` | `composes` | measure/analysis | — | uses one declared bearing parameter and preserves distinct profitability-maximizing and GDF targets |
| `economic.profit.directional.endogenous.zofio_pastor_aparicio_2013` | `economic.nerlovian.ccf1998` | `contrasts_with` | direction/measure/analysis | D | the endogenous profit-maximizing direction and either-technical-or-allocative rule are not an option spelling for an exogenous CCF direction |
| `economic.profit.decomposition.modified_ddf.lost_profit_on_outlay.aparicio_pastor_ray_2013` | `economic.nerlovian.ccf1998` | `contrasts_with` | normalization/measure | B | cost- or revenue-based economic normalization is not the CCF value of an arbitrary declared direction |
| `economic.profit.decomposition.general_direct.pastor_zofio_aparicio_pastor_2023` | `economic.nerlovian.ccf1998` | `contrasts_with` | analysis/duality | B | a direct decomposition anchored to a declared technical projection is not inferred from CCF directional duality |
| `analysis.scale_elasticity.local.radial_vrs` | `analysis.returns_to_scale.local.banker_thrall_1992` | `requires` | analysis/performance | — | the same fixed selected target and complete support interval are transformed into quantitative left/right elasticities; one-sided response labels are thresholds, not another solver |
| `analysis.scale_elasticity.directional.relative_vrs.ren_etal_2021` | `analysis.scale_elasticity.local.radial_vrs` | `exact_reduction` | performance/analysis/evaluation protocol | — | both relative direction vectors contain only ones, VRS technology, reference set, projection orientation, slack-completion policy, target, tolerance, and solver policy are matched |
| `analysis.scale_elasticity.directional.relative_vrs.ren_etal_2021` | `static.directional_distance` | `contrasts_with` | performance/analysis/direction semantics | D | Ren's operator measures a local relative percentage response at a selected efficient plan; a DDF measures an additive feasible adjustment in the physical units of its declared direction |
| `analysis.mpss.banker_1984` | `analysis.returns_to_scale.local` | `contrasts_with` | analysis/scope/target | D | MPSS globally maximizes average productivity along the observed input/output mix and reports a scale interval; local RTS diagnoses one-sided response at a declared efficient point, with no computational dependency between the operators |
| `analysis.returns_to_scale.local.banker_thrall_1992` | `analysis.scale_efficiency.radial_ratio` | `contrasts_with` | analysis/target/multiplicity | D | a local supporting-hyperplane RTS interval at a declared projection is not the CRS/VRS radial score ratio |
| `analysis.capacity.physical.fare_grosskopf_kokkelenberg_1989` | `analysis.capacity.economic.segerson_squires_1990` | `contrasts_with` | analysis/valuation | D | physical short-run output potential is not a price-conditioned economic capacity concept |
| `analysis.capacity.physical.fare_grosskopf_kokkelenberg_1989` | `analysis.mpss.banker_1984` | `contrasts_with` | analysis/decision context | D | quasi-fixed short-run capacity is not the long-run most productive scale size |
| `analysis.tfp_efficiency.scale_mix` | `analysis.scale_efficiency.radial_ratio` | `contrasts_with` | measure/analysis | B | requires declared TFP aggregators and reconstruction |
| `evaluation.target_completion.pareto_koopmans` | compatible ordinary `static.radial`, `static.directional_distance`, or `static.generalized_distance.chavas_cox` fit | `composes` | evaluation/target status | — | same ordinary all-discretionary convex technology, comparison population, temporal reference, and declared RTS in both phases; preserve the radial/DDF optimum or fixed finite nonnegative GDF path target, maximize strictly positive zero-safe DEAPack row-scaled slacks, reconstruct from complete intensities, and fail closed before reporting Pareto--Koopmans status; radial/DDF scales anchor to the evaluated observation and GDF scales to its fixed path target, which can change only alternate strong-target selection and is not a uniquely source-prescribed target |
| `evaluation.target_selection.closest_strong.aparicio_ruiz_sirvent_2007` | `evaluation.target_completion.pareto_koopmans` | `contrasts_with` | evaluation/target selection | D | a generic strong completion does not identify the closest strongly efficient target |
| `evaluation.super.directional.ray_2008` | `static.directional_distance` | `composes` | reference/performance/evaluation protocol | — | reuses directional envelopment rows only under Ray's fixed observed-bundle direction, VRS, exact row-level self-exclusion, unrestricted $\beta$, and $NL=1-\beta$ reporting; it is not a generic DDF alias |
| `evaluation.cross.game_nash.liang_wu_cook_zhu_2008` | `evaluation.cross.secondary` | `contrasts_with` | evaluation protocol/governance solution concept | D | the source game solves $n^2$ one-protected-peer/focal-player LPs per synchronous iteration and applies its fixed equal mean including self; its protected--focal table is not an ordinary appraiser--evaluatee matrix, whereas a secondary objective only selects multipliers on one evaluator's primary optimum face |
| `evaluation.pessimistic_multiplier` | `evaluation.worst_practice_frontier` | `contrasts_with` | evaluation/technology/normalization | D | least-favourable admissible valuations do not construct the same boundary as a source-defined inefficient empirical envelope |
| `evaluation.double_frontier` | `evaluation.pessimistic_multiplier` | `composes` | evaluation/aggregation | — | a double-frontier leaf retains a named pessimistic component together with a compatible optimistic component and combination rule |
| `evaluation.double_frontier` | `evaluation.worst_practice_frontier` | `contrasts_with` | evaluation/technology/aggregation | D | a paired-score protocol is not itself a universal worst-practice technology |
| `composite.benefit_of_doubt.linear.cherchye_etal_2007` | production-efficiency DEA | `contrasts_with` | decision context/data roles/result | D | endogenous composite-indicator weights and rankings are not technical production efficiency without a production interpretation |
| `environmental.ddf.joint_production` | `static.directional_distance` | `variant_of` | technology/data roles | C | explicit residual production account |
| `environmental.weak_disposal.single_factor.fare_etal_1989` | `environmental.weak_disposal.single_factor` | `variant_of` | technology/source | — | source-qualified common-factor construction |
| `environmental.weak_disposal.activity_specific.kuosmanen_2005` | `environmental.weak_disposal.activity_specific` | `variant_of` | technology/source | — | source-qualified convex activity-specific construction |
| `environmental.sbm.nonseparable_hybrid.tone_2003` | `environmental.sbm.nonseparable` | `variant_of` | measure/output partition/source | — | source-qualified leaf whose declared good/bad-output block shares one retained operating proportion |
| `environmental.sbm.nonseparable_hybrid.tone_2003` | `environmental.sbm.separable_strong` | `variant_of` | data roles/performance/evaluation protocol | D | the common retained share, unscored source-to-reference residuals, and `alpha`-times-observed target contract differ from independently adjusted separable output slacks |
| `environmental.sbm.nonseparable_hybrid.tone_2003` | `environmental.ddf.weak_disposal.common_factor` | `contrasts_with` | technology/performance/evaluation protocol | D | Tone's `alpha` belongs to a measure path for a declared joint-output block; it neither declares common-factor weak disposal nor creates a directional-distance technology |
| `environmental.directional_nonradial.energy_carbon.zhou_ang_wang_2012_non_chp` | `environmental.ddf.weak_disposal.common_factor` | `contrasts_with` | performance/valuation/evaluation protocol | D | both can retain the matched CRS common-factor bad-output equality and null jointness, but the specialized electricity preset uses separate fossil/electricity/carbon component steps, source-fixed block-normalization weights, and account-specific EPI/CPI/ECPI transformations. These are not aliases of one configurable common directional step or its $1/(1+\beta)$ display transform, even when a numerical value happens to coincide |
| `environmental.sbm.nonseparable` | `environmental.weak_disposal.single_factor` | `contrasts_with` | measure/technology | D | non-separable good/bad slack accounting does not identify the common-factor weak-disposal production set |
| `environmental.sbm.nonseparable` | `environmental.weak_disposal.activity_specific` | `contrasts_with` | measure/technology | D | measure coupling and activity-specific abatement variables are independent identity-changing choices |
| `environmental.weak_disposal.generalized_piecewise_cobb_douglas.roshdi_etal_2018` | `environmental.weak_disposal.activity_specific` | `contrasts_with` | technology/path/convexification | C | unequal exponential good--bad trade-off rates and a piecewise Cobb--Douglas envelope are not an activity-specific linear abatement-factor formulation |
| `environmental.semi_disposal.chen_wang_lai_2017` | `environmental.selective_disposal` | `contrasts_with` | technology/parameter semantics | C | a pollutant-specific partly free reduction region is not a binary assignment of strong or weak disposal by pollutant |
| `dynamic.environmental.by_production.adjustment_cost.dakpo_oude_lansink_2019` | `environmental.by_production` | `variant_of` | graph/technology/analysis | C | the dynamic leaf retains intended/residual subtechnologies while adding state, investment, adjustment-cost, and boundary equations |
| `dynamic.environmental.by_production.adjustment_cost.dakpo_oude_lansink_2019` | `dynamic.sbm.tone_tsutsui_2010` | `contrasts_with` | technology/environmental production account/performance | D | dynamic by-production models pollution generation and adjustment-cost mechanisms; a bad carry-over in dynamic SBM is a different production account |
| `environmental.semi_disposal.refined.chu_etal_2026` | `environmental.semi_disposal.chen_wang_lai_2017` | `variant_of` | technology/axiom/feasible set | C | the refined source replaces the earlier finite-sample account after arguing that it does not fully represent the intended freely disposable portion and separately bounds bad-output inefficiency |
| `environmental.by_production.ddf` | `environmental.ddf.joint_production` | `contrasts_with` | graph/technology | C | same direction does not imply the same attainable set |
| `network.environmental.weak_activity_specific.kalhor_kazemi_matin_2018` | `environmental.ddf.weak_disposal.activity_specific` | `contrasts_with` | graph/data roles/technology/performance/evaluation protocol | D | both use active plus complementary activity variables, but the network leaf adds process incidence and source-specific internal-product balances and reports an input-radial system score rather than a black-box directional distance |
| `technology.fdh.scale_extrapolation` | `technology.fdh` | `variant_of` | technology/RTS | C | rescale one activity without cross-activity convexification |
| `technology.meta.nonconvex_union` | `reference.group` | `composes` | technology/reference | — | group membership determines eligible observations while the non-convex union determines which group technologies are attainable |
| `technology.meta.pooled_convex` | `technology.meta.nonconvex_union` | `contrasts_with` | technology/convexification | D | cross-group convexification admits activities that a union of separately estimated group technologies need not admit |
| `heterogeneity.metafrontier.radial.odonnell_rao_battese_2008` | `static.radial` | `composes` | context/reference/analysis | — | each observation receives one matched radial fit against its declared group and one against all declared groups pooled; VRS uses `pooled_convex`, CRS uses `pooled_conic`, and neither construction is equivalent to the non-convex union of estimated group technologies |
| `technology.integer_discrete.kuosmanen_kazemi_matin_2009` | `technology.convex_envelopment` | `contrasts_with` | technology/data domain | D | integer feasibility and natural divisibility cannot be recovered by rounding a continuous convex solution |
| `network.sbm.tone_tsutsui_2009` | `static.sbm.nonoriented.tone2001` | `variant_of` | graph/technology | C | network links and balances active |
| `network.radial.fare_grosskopf_2000` | `network.relational.kao_hwang_2008` | `exact_score_transform` | performance/valuation/evaluation/analysis | B | identity transform for the primary system optimum only under the matched closed two-stage CRS graph, link-balance rule, and comparison population; the Färe--Grosskopf leaf defines no stage account and is not a whole-method alias |
| `network.relational.kao_hwang_2008` | `network.additive.chen_etal_2009` | `contrasts_with` | measure/aggregation | B | matched two-stage graph does not equalize system/stage accounting |
| `network.additive.chen_etal_2009` | `network.additive.cook_zhu_bi_yang_2010` | `exact_reduction` | graph/technology/evaluation/analysis | — | the Chen CRS primary system programme is the matched closed two-node reduction of Cook; Chen VRS, secondary attribution, and Lim--Zhu projection are not inherited by the general leaf |
| `network.additive.chen_etal_2009` | `static.additive` | `contrasts_with` | graph/performance/valuation/target | D | the former combines radial process efficiencies using endogenous virtual-resource shares; the latter maximizes a declared weighted sum of input/output slacks |
| `network.projection.frontier_validity.chen_cook_kao_zhu_2013` | multiplier-based divisional appraisal | `contrasts_with` | evaluation/target | D | a divisional multiplier score need not define a link-feasible envelopment projection under a general network technology |
| `graph.shared_flow` | `graph.series` | `contrasts_with` | graph/resource accounting | D | sharing a resource or output across activities is not the same production account as passing an intermediate product through serial stages |
| `graph.hierarchical` | hierarchical comparison groups | `contrasts_with` | graph/reference/estimator | D | nested organizational components are not the same object as grouping otherwise black-box units for comparison |
| `evaluation.cross.secondary` | `network.governance` | `contrasts_with` | evaluation/decision rights | D | a secondary selection among multiplier optima is not a rule allocating authority among internal processes |
| `evaluation.cross.secondary` | `decision.game` | `contrasts_with` | evaluation/decision context | D | game cross-efficiency is a peer-appraisal selection protocol, not a generic inter-unit strategic game |
| `network.governance` | `decision.game` | `contrasts_with` | graph/decision context | D | internal process control and strategic interaction among separate decision-making units require different players, feasible sets, and solution concepts |
| `decision.fixed_cost_allocation.cook_kress_1999` | `decision.fixed_cost_allocation.beasley_2003` | `contrasts_with` | system objective/allocation policy | D | efficiency-invariance characterization is not the average-efficiency allocation and target-setting procedure |
| `decision.fixed_cost_allocation.cook_kress_1999` | `decision.fixed_cost_allocation.cook_zhu_2005` | `variant_of` | allocation policy/orientation/RTS | C | Cook--Zhu operationalizes and extends the source principles but retains its own feasibility and selection conditions |
| `decision.fixed_cost_allocation` | `decision.central_allocation` | `contrasts_with` | decision context/conservation/objective | D | assigning a common overhead under a fairness rule is not generic productive-resource reallocation across units |
| `network.scale_rts.two_stage.chen_zhu_2019` | `analysis.scale_efficiency.radial_ratio` | `contrasts_with` | graph/technology/solver | D | the two-stage construction retains process coupling and uses a source-qualified conic reformulation |
| `network.productivity.two_stage.kao_hwang_2014` | `productivity.global_malmquist` | `variant_of` | graph/valuation/aggregation | C | common weights and the two-stage system/process productivity identities remain active |
| `graph.general_network` | `graph.black_box` | `contrasts_with` | graph | D | internal process structure and link feasibility are modeled |
| `analysis.window_efficiency` | `reference.window` | `composes` | analysis | — | base static measure and rolling benchmark width remain explicit |
| `analysis.window_efficiency` | named productivity operator | `contrasts_with` | analysis/operator | B | repeated static scores have no change identity by themselves |
| `productivity.global_malmquist` | `productivity.malmquist.adjacent_geometric` | `contrasts_with` | reference/operator | C | shared radial task compiler |
| `productivity.hicks_moorsteen.bjurek_1996` | `productivity.malmquist.adjacent_geometric` | `contrasts_with` | operator/completeness | D | a complete output-quantity/input-quantity ratio is not an alternative spelling of an oriented Malmquist index |
| `productivity.fare_primont.odonnell_2012` | `productivity.hicks_moorsteen.bjurek_1996` | `contrasts_with` | aggregator/reference/operator | D | the fixed-reference multilateral Färe--Primont aggregator has a different reference and transitivity account |
| `productivity.luenberger_hicks_moorsteen.briec_kerstens_2004` | `productivity.luenberger` | `contrasts_with` | operator/completeness/units | D | the complete additive output-minus-input account is not an ordinary one-sided Luenberger change indicator |
| `productivity.malmquist_luenberger.aparicio_pastor_zofio_2013` | `productivity.malmquist_luenberger.chung_fare_grosskopf_1997` | `shares_compiler` | technology | — | both use the four-role adjacent ML executor, but APZ replaces the conventional bad-output equality by the 2017 capped-bad inequality technology and recompiles all four distances; shared orchestration does not make them aliases or post-processing equivalents |
| `productivity.malmquist_luenberger.aparicio_pastor_zofio_2013` | `productivity.global_malmquist_luenberger.oh_2010` | `contrasts_with` | technology/reference/operator | D | APZ uses four own-/cross-period contemporaneous roles and reference-period caps; Oh uses own/global roles and one retrospective pooled CRS benchmark |
| `productivity.malmquist_luenberger.apz` | `productivity.malmquist_luenberger.aparicio_pastor_zofio_2013` | `alias` | identifier | A | discovery-only short spelling; the full Aparicio--Pastor--Zofío identifier remains canonical in results and registry records |
| `estimator.partial.order_m` | `estimator.full.fdh` | `contrasts_with` | estimator | D | random partial frontier versus full empirical hull |
| `estimator.partial.order_alpha.aragon_daouia_thomas_agnan_2005` | `estimator.partial.order_m` | `contrasts_with` | estimator/tuning semantics | D | a conditional-quantile frontier indexed by $\alpha$ is not an expected extremum from a comparison set of size $m$ |
| `context.three_stage.fried2002` | `estimator.conditional.dea` | `contrasts_with` | estimator/data adjustment | D | parametric SFA slack decomposition and DEA refit |
| `inference.bootstrap.frontier_efficiency.simar_wilson_1998` | supported deterministic estimator | `requires` | inference | — | registered boundary-compatible DGP and score convention |
| `inference.bootstrap.directional_distance.simar_vanhems_wilson_2012` | supported convex directional-distance estimator | `requires` | inference | — | declared direction, boundary regularity conditions, native sign, and source-qualified resampling algorithm |
| `context.second_stage.simar_wilson_2007.algorithm2` | `context.second_stage.simar_wilson_2007.algorithm1` | `variant_of` | inference/data adjustment | D | adds source-qualified first-stage bias correction |
| `context.second_stage.banker_natarajan_2008.ols` | `context.second_stage.simar_wilson` | `contrasts_with` | stochastic assumptions/inference | D | the Banker--Natarajan productivity/OLS argument has its own transformation and stochastic conditions and is not a Simar--Wilson algorithm preset |

Valid relation types are `alias`, `exact_score_transform`,
`specialization_of`, `preset_of`, `variant_of`, `composes`, `requires`,
`shares_compiler`, `incompatible`, and `contrasts_with`. Every relation
records its difference axis. Every Level A relationship additionally requires
proof of feasible-set and objective/value correspondence, target/peer
correspondence, parameter domain, and regression tests. Equal rankings or
shared matrices are insufficient.

## 15. Current implementation and evidence snapshot

Implemented public foundations include:

- radial input/output DEA with scale presets, plus source-neutral
  observation-specific peer eligibility on the generic, CRS/VRS-specialized,
  and four fixed-orientation radial recipes, composed as an intersection with
  the base `ReferenceSpec` and carrying no categorical or Banker--Morey
  identity;
- input/output radial FDH with direct dominance scanning, alternative
  single-observation peers, and no convexification or MILP dependency;
- additive/weighted additive, RAM, BAM, Tone input-, output-, and non-oriented
  SBM, and DDF; source-neutral peer eligibility is also public on every item in
  that list except BAM, with RAM retaining its full-data pre-eligibility range
  scale and labelling restricted fits as a DEAPack extension; BAM reproduces a
  12-DMU cross-implementation oracle under VRS
  and bounded CRS, while the non-oriented CRS SBM leaf is checked on the
  neutral `sbm_slack_contrast` case and the two oriented leaves retain their
  equation/property certificates;
- Chavas--Cox generalized distance under CRS/VRS, with exact radial endpoint
  and CRS reductions, certified interior-VRS feasibility search, and a fixed
  five-DMU cross-implementation oracle;
- strong-disposal and bad-output directional-equality environmental DDF formulations,
  with the latter's relationship to named weak-disposal technologies under
  audit, plus an explicit null-jointness option;
- separable undesirable-output SBM;
- by-production DDF and FGL-style analysis;
- Coelli-style material-inflow analysis under a source-native CRS/VRS,
  self-inclusive cross-sectional one-material certificate boundary, with an exact
  independent $TE$--$EE$--$EAE$ decomposition certificate and no
  published-farm reproduction claim;
- minimum-cost efficiency and the matched input-radial
  technical--allocative decomposition, verified against Coelli's DEAP 2.1
  Example 3;
- maximum-revenue efficiency and the matched output-radial
  technical--allocative decomposition, verified against two independent
  public numerical examples that distinguish VRS, CRS, and unequal prices;
- VRS maximum-profit gaps and the CCF-1998 Nerlovian
  technical--allocative decomposition, including negative-profit cases and
  an eight-unit fixed cross-implementation oracle;
- return-to-dollar profitability and its matched Chavas--Cox
  technical--scale--allocative decomposition, including the Zofío--Prieto
  five-unit fixed cross-implementation oracle;
- Malmquist, Luenberger, global/biennial Malmquist, standard
  Malmquist--Luenberger, the APZ bounded-bad-output Malmquist--Luenberger
  preset, and global environmental productivity;
- Färe--Grosskopf CRS/VRS two-stage input- and output-radial system
  performance, with separate process intensities, disposable intermediate
  surplus, certified system plans, an independent dense output-programme
  oracle, and a conditional input-CRS score-only cross-implementation check
  against the Kao--Hwang primary programme;
- Kao--Hwang CRS relational and Chen--Cook--Li--Zhu CRS/VRS additive
  closed two-stage network accounts, each with the complete 24-insurer score
  oracle and source-qualified Lim--Zhu projections;
- Cook--Zhu--Bi--Yang CRS additive accounting for open DAGs, with the
  published seller--buyer and three-stage oracles;
- Tone--Tsutsui network SBM under CRS/VRS and fixed/free link control, with
  all three source orientations, published input-oriented Tables 3, 4, and 6,
  and exact hand oracles for output and non-oriented accounting;
- O'Donnell--Rao--Battese radial metafrontier analysis under matched VRS or
  CRS group/meta programmes, with ex ante groups, a pooled convex or conic
  meta opportunity set, the canonical MTR decomposition, and separate
  group/meta target and peer accounts when optional slack completion is
  requested;
- common result objects, sparse SciPy/HiGHS solving, and basic scale analysis.

The current tests provide substantial analytical, reproduced,
cross-implementation, property, and failure-case evidence. Every
implemented/public machine record now has at least one independently checked,
claim-scoped numerical path classified as `analytically_derived`,
`reproduced`, or `cross_implemented`. This does not mean that every record
reproduces a published table or a third-party implementation: an analytical
certificate remains confined to its named parameters, results, reference
population, and fixture. A family is promoted to a literature-reproduction or
cross-implementation label only when that particular evidence exists.

The installed package exposes this executable subset through the immutable
`list_methods()` and `method_info()` discovery API. The catalog currently
contains 62 result `method_id` entries, five `specialization_id` entries, and
eight `preset_id` entries, for 75 identities. The machine registry contains
67 records: 63 implemented/public records--the 62 public method records and
APZ's public preset record--and four non-public source-gated prototypes. The
seven catalog-only presets are the four complete CCR/BCC input/output radial
recipes, the output-oriented CRS FGNZ Malmquist core, and the original-1982
and invariant-1983 multiplicative recipes; APZ is the remaining catalog preset
and has a machine record for its distinct capped-bad technology/composition.
Enhanced FGNZ and Ray--Desli are separate methods because their respective
six- and eight-task evaluations and component/failure contracts are distinct.
The specializations are CCR, BCC, the dynamic-SBM ex-post free-carry-over
adjustment, and the Tone--Tsutsui recipient-accountable input-link and
supplier-accountable output-link accounts. The catalog deliberately excludes
every planned or prototype registry entry, so appearing in this atlas is
never itself a claim that a model can be fitted.

Every implemented/public `method_id` now links to at least one benchmark that
directly executes the complete public API, and every benchmark script resolves
back to a machine method record. This closes execution-path and performance
coverage for the current catalog. A benchmark does not itself establish the
separate numerical-oracle matrix, replace a defining source, or turn an
internal reconstruction identity into independent validation; the zero public
`not_located` count is supported by the claim-scoped evidence described above.

`static.radial.fdh` currently has `property` verification: hand-calculated
examples, positive-unit invariance, the expected FDH--VRS score ordering,
zero-denominator policies, reference-set failures, tie semantics, and a
moderate-sample direct-scan test. A published numerical oracle and an
independent implementation comparison remain release evidence to add.

`static.radial.fch.green_cook_2004` has an `analytically_derived` numerical
certificate and a primary-checked formulation from
[Green and Cook (2004)](https://doi.org/10.1057/palgrave.jors.2601773).
An independent `Fraction`-based enumerator visits all 15 nonempty binary
coalitions of the synthetic four-organization fixture without importing the
production compiler, mixed-integer solver, NumPy, or SciPy. It proves the
input and output scores for every organization, the fixture-specific unique
coalitions, radial and reference activities, and free-disposal residuals. The
same example distinguishes FDH, FCH, FRH, CCR, and VRS in both orientations;
separate tests enforce
$T_{FDH}\subseteq T_{FCH}\subseteq T_{FRH}$, reject any general FCH--VRS
ordering, certify every binary incumbent component and MIP gap, preserve
unit invariance, and fail closed on invalid domains or incomplete solves.
The reported coalition is a technically admissible benchmark, not a
recommendation to merge the selected organizations.
The exact certificate is deliberately limited to its declared strictly
positive, one-input, one-output, self-inclusive cross section. No published
Green--Cook numerical values or independent third-party cross-implementation
are claimed.
[Adler, Olesen, and Volta
(2024)](https://doi.org/10.1287/opre.2022.2348) confirms that “free
aggregation hull” and its historical `FAH` acronym name the same Green--Cook
technology. DEAPack does not expose `FAH` as Python API because
[Ray (1997)](https://doi.org/10.1023/A:1007747407212) uses it for the
distinct free affordability hull, a planned cost-indirect technology for
normalized input prices without observed input quantities.

`static.radial.frh` has an analytical project-case certificate. Its input and
output scores and integer reference portfolios are hand-checkable on
`integer_coordination_hulls`, while separate tests enforce FDH--FRH--CRS
nesting, integer certification, failure closure, target accounting, and
positive-unit invariance. The `Benchmarking` page remains an implementation
citation, not a redistributed numerical oracle.

`heterogeneity.metafrontier.radial.odonnell_rao_battese_2008` also has
`cross_implementation` verification. Its source scalar checkpoint
($E^M=0.60$, $E^G=0.80$, $\mathrm{MTR}=0.75$), an exact six-organization
analytic case, and an independently compiled direct LP verify both
orientations and CRS/VRS. The default source profile performs only the
$2n$ radial group/meta solves; target and peer refinement is opt-in. The
published 485-row agricultural application is not claimed as reproduced
because its observation-level data and DEAP control files are unavailable.
Within-group efficiency is an operating-performance comparison against the
declared group's opportunities. MTR describes how close that opportunity
frontier lies to the broader meta opportunity frontier; neither component is
a causal attribution.

Every result created by the current public model and analysis paths now
includes:

```text
registry_schema_version
method_id
specialization_id  # optional partial parameter specialization
preset_id          # optional complete validated recipe
expanded_spec
```

`method_id` is always canonical. `specialization_id` records a named partial
parameter specialization such as CRS without implying that orientation and
target policy are fixed. `preset_id` is reserved for a complete validated
recipe. Direct Python symbol aliases cannot reliably reveal which spelling
the caller typed.
