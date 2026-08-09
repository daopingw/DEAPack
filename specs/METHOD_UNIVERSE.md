# The DEAPack method universe

This document is the source-backed scope review for DEAPack 2.0. It answers
three questions:

1. Which major DEA-based efficiency and productivity methods belong in the
   project?
2. Which historical names describe the same mechanism?
3. Which methods must remain distinct because they change the production
   system, technology, performance objective, benchmark, or estimator?

It is a map of canonical mechanisms, not a promise to create one Python class
for every published acronym.
The maintained domain reviews in `specs/reviews/` provide the source,
equivalence, failure-domain, solver, oracle, package, and book evidence behind
this compact map.
The cross-domain audit at `specs/METHOD_COVERAGE_AUDIT.md` records the
canonical study grammar, delivery/evidence distinction, current family-level
coverage, and the remaining source-leaf backlog.

Three kinds of completeness are reported separately. **Conceptual
completeness** means that a family and its non-equivalence boundaries are in
the atlas. **Executable completeness** means that a source-qualified leaf has
public code and a frozen result contract. **Validation completeness** means
that the implementation has the appropriate source, property, failure,
oracle, and independent-comparison evidence. No occurrence in this field map
implies the latter two.

## 1. Review policy

### 1.1 Evidence base

The map is anchored in:

- the production-economics foundations of efficiency and distance functions;
- the original papers that define major model families;
- broad retrospective reviews, especially
  [Cook and Seiford (2009)](https://doi.org/10.1016/j.ejor.2008.01.032),
  [Emrouznejad and Yang (2018)](https://doi.org/10.1016/j.seps.2017.01.008),
  and
  [Mergoni, Emrouznejad, and De Witte (2025)](https://doi.org/10.1016/j.ejor.2024.12.049);
- the
  [Handbook on Data Envelopment Analysis](https://doi.org/10.1007/978-1-4419-6151-8)
  and specialist handbooks;
- specialist reviews for environmental, network, dynamic, productivity,
  statistical, robust, and uncertain-data methods.

The
[COOPER framework](https://doi.org/10.1016/j.ejor.2010.07.025)
is used as an empirical-project safeguard. It is complementary to, rather
than replaced by, the compositional model framework specified in
`UNIFIED_FRAMEWORK.md`.

### 1.2 Inclusion test

A family belongs in the package core or an official extension when it:

- estimates or uses a non-parametric production frontier;
- answers a recognized efficiency, productivity, environmental-performance,
  benchmarking, or production-planning question;
- has sufficiently stable definitions for validation against the literature;
  and
- can expose assumptions and diagnostics through the common result contract.

Methods may appear only in the book's comparative appendix when they are
important neighbors but not DEA-based estimators. This includes SFA,
ordinary CNLS/CQR/CER, StoNED, ordinary index-number methods without frontier
estimation, and general machine-learning performance predictors. The
conditional SCNLS representation discussed in Section 13 is exact only on
its proved one-sided sign/shape/loss domain; it does not turn the wider
regression families into DEA aliases.

Names such as “neural DEA,” “ensemble DEA,” or “ML-assisted DEA” do not pass
the inclusion test by themselves. A source-qualified leaf must state whether
machine learning estimates a production boundary, tunes a declared DEA
estimator, predicts a previously fitted score, or merely imitates solver
output. Only the first two can enter the executable DEA atlas, and then only
when the attainable-set assumptions, shape restrictions, extrapolation
policy, targets, and uncertainty contract remain explicit. Unconstrained
score predictors and black-box surrogates belong to the comparative
estimation/prediction neighborhood.

### 1.3 Coverage is by mechanism

The literature contains many rediscoveries, acronyms, orientations,
normalizations, and application-specific labels. DEAPack treats a name as:

- an **alias** when it is algebraically equivalent to a canonical
  specification;
- a **preset** when it fixes several independent options;
- a **variant** when it changes a meaningful objective or normalization while
  sharing most machinery;
- a **family** when it requires a distinct technology, production system, or
  estimator.

The four equivalence levels and proof requirements are normative in
`UNIFIED_FRAMEWORK.md`.

### 1.4 Three benchmark decisions that must not share one name

Every study separates:

- the **comparison population**, which establishes which organizations are
  economically eligible to teach the evaluated organization;
- the **temporal information set**, which establishes which periods of those
  organizations are visible; and
- **evaluation exclusions**, which remove or modify an otherwise eligible
  observation for a named protocol such as super-efficiency.

Only after those decisions does a technology builder form a hull, union, or
other attainable set. Positive-intensity peers and maximal or global
reference sets are fitted results, not input policies. In particular, “all
eligible observations” in a cross section is a population decision, whereas
a global productivity technology is a retrospective all-period information
decision. The word `reference` is never sufficient metadata for both.

## 2. Static black-box production

### 2.1 Empirical technologies

| Canonical mechanism | Historical names and important variants | DEAPack treatment |
|---|---|---|
| convex CRS envelopment | CCR, CRS-DEA, constant-returns activity analysis | one technology; CCR is an RTS specialization, while CCR-I/O are the public `CCRInput`/`CCROutput` recipes over the same radial method |
| convex VRS envelopment | BCC, VRS-DEA, convexity-constrained DEA | one technology; BCC is an RTS specialization, while BCC-I/O are the public `BCCInput`/`BCCOutput` recipes over the same radial method |
| restricted scale technologies | NIRS, NDRS, generalized RTS | NIRS/NDRS are tested `RadialDEA` technology parameters; any standalone source-qualified literature leaf is deferred until its defining source and independent oracle close |
| [non-convex free-disposal technology](https://ideas.repec.org/h/eee/ecocha/2-09.html) | FDH, free disposal hull | distinct compiler; not a CCR/BCC option disguised as orientation |
| [binary-subset free coordination hull](https://doi.org/10.1057/palgrave.jors.2601773) | FCH, free coordination hull, free aggregation hull, historical FAH | implemented/public Green--Cook radial leaf in which a nonempty subset of observed activities may be assembled but each template enters at most once; not FDH, FRH, VRS, or CCR; `FAH` is retained only as source provenance, not a Python alias |
| [integer-replication technology](https://doi.org/10.1007/BF01073473) | FRH, free replicability hull, free replication hull, free disposal and replicability hull, Benchmarking `RTS="add"` | one non-convex additive technology in which whole observed operating templates may be replicated and combined; distinct from FDH, CCR, integer-valued DEA, and additive slack measures |
| [scale-extrapolated non-convex technologies](https://doi.org/10.1016/S0377-2217(97)00428-1) | FDH-CRS, FDH-NIRS, FDH-NDRS | one parameterized non-convex family; activities may be rescaled but never convexly mixed |
| multiplicative envelopment | original C2S2 multiplicative DEA, invariant multiplicative efficiency, piecewise log-linear/Cobb--Douglas envelopment | implemented/public as one `static.multiplicative` family and shared compiler with separate 1982 original log-conic and 1983 invariant log-convex catalog presets; not the CCR multiplier form, ordinary CRS/VRS, or logged-data preprocessing |
| non-disposal or weak-disposal variants | congestion and selected environmental technologies | explicit technology restrictions |

The original CCR and BCC models are historically central, but their reusable
mechanism is ordinary convex envelopment with a scale restriction. Input and
output orientations define different improvement questions; they do not
create separate technologies.

FDH removes convexification and therefore changes which operating plans are
treated as attainable. It shares data and result interfaces with convex DEA,
but not its technology compiler or asymptotic properties.
Standard FDH admits only observed activity scales plus free disposal.

The free replicability hull (FRH) adds a different operational assumption:
whole observed templates may be repeated an integer number of times and
different templates may be assembled into one operating portfolio. A
replication count of two means two complete branches, production lines, or
service modules—not a continuous weight of 200 percent. FRH therefore lies
between standard FDH and continuous CRS envelopment for radial comparisons:
FDH selects one observed template, FRH permits integer addition, and CCR
permits arbitrary nonnegative real intensities. FRH inputs and outputs need
not themselves be integer-valued; the integrality belongs to the activity
replication counts.

The exact public vocabulary may merge `FRH`, “free replicability hull,”
“free replication hull,” and the source-qualified `RTS="add"` spelling.
It must not expose a bare `ADD` class because additive DEA already names a
slack-aggregation performance measure.

FCH instead admits a binary subset of observed templates: more than one
activity may coordinate, but no template can be replicated twice. The
implemented `technology.fch.binary_subset_aggregation` and
`static.radial.fch.green_cook_2004` therefore sit on $T$ and are Level C,
not Level A, relative to FDH and FRH. Under matched additive nonnegative
quantities with positive observation-level input/output aggregates,
cross-sectional comparison population, orientation,
self-membership, and ordinary free disposal,
$T_{FDH}\subseteq T_{FCH}\subseteq T_{FRH}$. FCH and VRS are not generally
nested. Although the same MILP infrastructure can enforce the binary cap,
the direct continuous relaxation of FCH retains
$0\leq\lambda_j\leq1$ and the nonempty-subset constraint; it is not CCR.
The selected coalition is a technically admissible benchmark, not a
recommendation to merge organizations. See
[Green and Cook (2004)](https://doi.org/10.1057/palgrave.jors.2601773) and
[Adler, Olesen, and Volta
(2024)](https://doi.org/10.1287/opre.2022.2348).

The public multiplicative mechanism likewise keeps historical names from
creating duplicate solvers. `static.multiplicative` is one family and one
sparse log-space compiler. Its catalog presets
`static.multiplicative.original.charnes_etal_1982` and
`static.multiplicative.invariant.charnes_etal_1983` preserve, respectively,
the original log-conic model of
[Charnes et al. (1982)](https://doi.org/10.1016/0038-0121(82)90029-5) and the
unit-invariant log-convex model of
[Charnes et al. (1983)](https://doi.org/10.1016/0167-6377(83)90014-7). The
1982 preset requires every ordinary input and desirable output to be strictly
greater than one, fixes the exponent floor at one, and is not invariant to an
independent positive change of units. The 1983 preset requires strict
positivity, imposes `sum(lambda)=1` in log quantities, permits a finite
positive score-power floor, and is invariant when each coordinate and its
reported target are rescaled consistently. Both reject undesirable outputs,
zeros, negatives, and arbitrary epsilon or translation repairs.

These are log-conic and log-convex production accounts, not ordinary CRS and
VRS envelopment applied after taking logs. The transformation changes the
maintained technology, score, slack, target, and exponent account together.
An exact two-DMU analytical oracle and an independently compiled dense source
programme validate both presets, but no published numerical reproduction is
claimed. The historical source profile is a self-inclusive global cross
section; supported panel and non-global reference policies are explicitly
labelled DEAPack extensions rather than promoted to either source identity.

The historical acronym `FAH` is deliberately not public API vocabulary.
[Ray (1997)](https://doi.org/10.1023/A:1007747407212) uses “free
affordability hull” for a distinct cost-indirect technology when normalized
input prices are observed but input quantities are unavailable. The planned
source-qualified proposal
`economic.cost_indirect.free_affordability.ray_1997` occupies $D$ for the
price-without-quantity data role, $T$ for the affordability technology,
$V$ for normalized input prices, and $M/A$ for indirect cost performance.
It is Level C/D relative to Green--Cook FCH/free aggregation hull and is not
implemented.

Extended replication hulls, other finite replication bounds, and
semi-continuous `irs2` technologies remain separate source leaves. See
[Tulkens (1993)](https://doi.org/10.1007/BF01073473),
[Bogetoft (1996)](https://doi.org/10.1287/mnsc.42.3.457), and
[Ehrgott and Tind (2009)](https://doi.org/10.1016/j.omega.2008.08.003).

FDH-CRS, FDH-NIRS, and FDH-NDRS add source-qualified scale extrapolation
without admitting convex mixtures of different observations. They are
neither aliases for standard FDH nor uses of the convex DEA RTS compiler.

### 2.2 Proportional and directional measures

| Canonical measure | Included variants | Relationship |
|---|---|---|
| input Farrell | Debreu--Farrell input efficiency, input Shephard distance under reciprocal convention | exact transformations recorded in native-value metadata |
| output Farrell | output expansion factor, reciprocal output efficiency, output Shephard distance | one solution with explicit score convention |
| standard hyperbolic | proportional input contraction coordinated with reciprocal output expansion | distinct joint adjustment programme |
| generalized hyperbolic paths | source-qualified coordinated input/output paths | separate variants whose path parameters remain explicit |
| Chavas--Cox generalized distance function | parameterized input/output/hyperbolic distance family | distinct family with its own profitability duality; not merely another hyperbolic spelling |
| graph/non-oriented adjustment scope | Russell graph, enhanced Russell graph, SBM, and other measure-specific simultaneous adjustments | an umbrella description of what may change, not one canonical score |
| directional distance | input, output, good/bad, generalized and non-radial directions | one directional engine over compatible technologies |
| directional technology distance | technology-gap and cross-technology comparisons | same measure family with distinct reference policies |
| subvector/component distance | short-run, energy-, labour-, or output-specific efficiency | explicit subset of adjustable variables; not post-hoc slack inspection |

Directional distance functions provide a powerful common language for many
declared improvement programmes. They do not subsume price-based objectives,
fractional slack aggregators, internal network accounting, dynamic
carry-overs, or statistical frontier estimators.

A direction vector and a direction-selection policy are also different
objects. The vocabulary distinguishes `direction.exogenous`,
`direction.observation_scaled`, `direction.range_ideal`, and
`direction.endogenous_value.petersen_2018`. These choices occupy $M$, $V$,
and $P$: an ex-ante declared programme, a current-scale normalization, an
ideal/range construction, and an endogenous value-based selection rule do not
make the same managerial statement. They are Level B when only the measure
changes over one technology and Level D when direction choice becomes a
coupled optimization protocol. Endogenous selection must not be hidden inside
an ordinary numeric direction option or inside $\Theta$. The first public
`direction.range_ideal` composition is the source-fixed 2004 RDM leaf; it does
not make every possible range or ideal-point policy executable. The endogenous
Petersen branch remains planned/evidence only; its initial source audit is
[Petersen (2018)](https://doi.org/10.1287/opre.2017.1711).

Ordinary and environmental hyperbolic models should share one core
hyperbolic $M$ only where the source path equations are proved identical.
Their source presets must still retain $D$, $T$, score convention, and
provenance. Thus reuse is Level B/C, not a Level-A whole-study alias and not
an automatic DDF alias. The planned evidence anchors are
[Färe et al. (1989)](https://doi.org/10.2307/1928055) and
[Färe, Margaritis, Rouse, and Roshdi
(2016)](https://doi.org/10.1016/j.ejor.2016.03.045).

### 2.3 Variable-specific technical measures

| Family | Named members | What remains distinct |
|---|---|---|
| additive | classic VRS unit-weight additive; configurable fixed positive-weight package extension | the classic source identity fixes VRS, unit weights, and a self-inclusive cross-section; other weights, RTS, and reference policies do not inherit that certificate |
| range/bound adjusted | RAM, BAM, enhanced BAM | normalization population, bounds, and score domain |
| Russell | input/output Russell, Russell graph; historical enhanced Russell (ERG/ERGM) name | averaging rule, orientation, and monotonicity for the original Russell measures; standard positive-data ERG is merged with SBM below |
| Hölder distance | $L_1$, $L_2$, $L_\infty$ and other source-qualified norms | distance norm and units of the reported shortfall |
| slacks-based | SBM, weighted SBM, input/output/non-oriented SBM | orientation-specific direct or fractional normalization and variable weights |
| epsilon-based | EBM | calibrated combination of radial and non-radial inefficiency |
| non-radial directional | component-specific directional distances, weighted additive DDF | direction and aggregation rule |
| [multi-directional efficiency analysis](https://doi.org/10.1023/A:1007848222681) | variable-specific ideal improvements followed by a declared aggregation | a multi-step benchmarking workflow, not a generic alias for DDF |
| [range-directional measure](https://doi.org/10.1057/palgrave.jors.2601768) | ideal-point/sample-range directions that remain meaningful with signed variables | the original VRS leaf is implemented; it is a named signed-data measure, not a universal translation of every DEA model |

These measures can share balance matrices and solver utilities. They are not
aliases because they can rank units differently, select different peers and
targets, and attach different economic meaning to a unit of slack.

For the additive family, the current source certificate is deliberately
narrow: Charnes et al. (1985) equations (4.5)--(4.6), VRS, unit weights, one
self-inclusive cross-section, and ordinary nonnegative inputs/desirable
outputs. `WeightedAdditiveDEA` is a discoverability alias for a configurable
DEAPack extension, not a second historical algorithm. Equation (5.7)'s
evaluated-observation normalization and any separately named additive leaf
whose defining literature or independent oracle is unavailable remain
`deferred_to_next_version`.

The initial package teaches radial, additive/RAM/BAM, ERG/SBM, generic
directional, and original range-directional measures in depth. The implemented
2011 BAM leaf fixes one global
normalization/reference population, nonnegative quantities, and explicit
one-sided slack bounds; its 12-DMU VRS/CRS scores agree with an archived
independent implementation. Remaining graph/original Russell formulations,
Enhanced BAM or alternative bound scopes, EBM, hyperbolic, and closest-target
families belong in the comprehensive package and method reference; their book
treatment may be shorter.

One exact conditional equivalence deserves registration: with the standard
strictly positive data domain, the enhanced Russell graph measure has the same
linear-fractional content as Tone's standard SBM after a variable
transformation. That graph-form result does not by itself merge the whole
Russell family. Separately, Tone (2001, p. 507) states that retaining only
the SBM numerator or denominator gives the corresponding input- or
output-oriented Russell measure. Those two conditional representations
require matched technology, positive-data domain, weights, normalization, and
score direction; they do not identify input, output, and graph Russell as one
method. See
[Pastor, Ruiz, and Sirvent (1999)](https://doi.org/10.1016/S0377-2217(98)00098-8)
and
[Tone (2001)](https://doi.org/10.1016/S0377-2217(99)00407-5).

Tone's input-, output-, and non-oriented presets are all implemented and
public on the standard strictly positive input/output domain. They share the
same convex technology, reference policy, and sparse compilation machinery,
but remain Level B distinct measures because management is valuing input
conservation, output expansion, or both sides together. An input-oriented
score of one certifies only the input-slack account; an output-oriented score
of one certifies only the output-slack account. The target on the side omitted
from the objective is one solver-selected primary optimum and is not a
strong-target guarantee. The `sbm_slack_contrast` data reproduce the non-oriented
CRS scores and selected slacks in Tone's Table 2; a published numerical oracle
for either oriented leaf has not been located. Zero- and signed-data
extensions remain separate source-qualified variants rather than silent
translations of these standard models.

A best value under a restricted measure is not automatically
Pareto--Koopmans efficiency. A radial factor of one or a directional distance
of zero can coexist with a variable-specific resource excess or output
shortfall. DEAPack treats lexicographic slack completion, closest-target
selection, and other strong-target procedures as evaluation protocols over a
base measure. Results keep measure efficiency, strong-efficiency status, and
the target guarantee separate; the strong status remains missing when the
required completion task is skipped or unsupported. This distinction follows
the direct dominance/slack test and radial projection in
[Charnes et al. (1985), equations (4.4)--(4.6), (5.3), and
(5.5)](https://doi.org/10.1016/0304-4076(85)90133-2), read with the later
strong/weak-efficiency analysis of
[Charnes, Cooper, and Thrall (1986)](https://doi.org/10.1016/0167-6377(86)90082-9)
and also applies to jointly feasible network targets. The reusable protocol is
registered as `evaluation.target_completion.pareto_koopmans`; it is not a
replacement scalar efficiency measure.

That reusable identity is public only through `compute_slacks=True` on the
ordinary all-discretionary, desirable-output, continuous convex
`static.radial`, `static.directional_distance`, and
`static.generalized_distance.chavas_cox` domains. Both phases retain the same
comparison population, temporal reference, and RTS restriction. The GDF
composition additionally requires a finite fitted score, positive
observation-level input and output aggregates, and a fixed finite nonnegative
path target. Every eligible slack receives a strictly positive weight, and
generic strong status is reported only after an optimal completion and a
certified within-technology evaluation.

The shared ID names the Pareto--Koopmans completion principle and phase-two LP
layout, not identical alternate-optimum weights. DEAPack divides each
physical slack by a positive row scale: radial DEA and DDF anchor the scale to
the evaluated observation, while GDF anchors it to the fixed path target.
Both policies are stable under independent positive unit changes; their
difference can select another strongly efficient target or peer
representation when more than one completion is eligible, but it does not
change the first-stage score or the strong-status logic. Charnes et al.'s
equation (5.7) instead uses the evaluated plan's positive coordinate values
for a source unit-invariant measure. These constructions share an invariance
concern, but the package rules are not the paper's uniquely prescribed target
and no target is claimed unique or management-preferred. The exact
$\alpha=0$ radial/DDF/GDF cross-check is evidence for this completion phase,
not for GDF's interior first-stage equation or numerical search.

Environmental, nondiscretionary, FDH, FCH, and FRH protocol extensions remain
`deferred_to_next_version`. Existing model-specific slack refinements do not
inherit the reusable identity until their dominance order, variable rights,
technology-specific target theorem, and independent exact oracle have been
frozen. The complete boundary is recorded in
[`source_protocols/charnes_etal_1985_pareto_koopmans_completion.md`](source_protocols/charnes_etal_1985_pareto_koopmans_completion.md).

### 2.4 Economic and production-planning measures

| Economic question | Canonical analyses |
|---|---|
| minimum expenditure for required outputs | cost and input allocative efficiency |
| maximum revenue from available inputs | revenue and output allocative efficiency |
| best service or revenue attainable after management may redesign the resource mix within a budget | indirect input/output efficiency under an explicit budget or value constraint |
| maximum net value when both sides may adjust | `economic.profit.maximum`, with shutdown/scale technology declared separately |
| price-normalized profit shortfall along a declared direction | `economic.nerlovian.ccf1998` |
| output value relative to resource expenditure | source-qualified return-to-dollar efficiency |
| profitability shortfall relative to outlay | generalized-distance profitability/decomposition and lost-profit-on-outlay variants |
| unused productive ability | capacity output and capacity-utilization measures |
| whether excess inputs restrict output | congestion under explicitly named definitions |
| value of marginal relaxation | shadow prices, marginal products, marginal abatement costs |
| whether the assessed scale contributes to benchmark-relative shortfall and how nearby proportional expansion would perform | scale efficiency and local returns to scale, reported as distinct diagnostics |
| which operating size is most productive under the maintained technology | deferred MPSS source audit and other source-qualified optimal-scale analyses |
| quantitative response to marginal scale change | left/right scale-elasticity bounds and source-qualified directional scale elasticity |
| maximum TFP at the best feasible scale and mix | technical, scale, mix, and scale-mix TFP efficiency |
| advantage of joint multi-output production | source-qualified economies-of-scope analysis under declared separate-production subtechnologies |

Technical efficiency and economic efficiency must not be conflated. Prices,
budgets, or value functions add information not recoverable from a technical
distance alone. Common versus DMU-specific prices, incomplete price
information, market versus shadow values, and the numeraire are part of the
specification. A technical/allocative product decomposition is exposed only
when its technology, orientation, and price definitions establish it.
`overall_efficiency` is not an admissible unqualified field name.

Indirect economic efficiency asks a different planning question from ordinary
cost or revenue efficiency. Instead of holding the observed input vector or
required output vector fixed, it asks what the organization could attain after
management is allowed to redesign the mix subject to a declared budget or
value constraint. The planned family is `economic.indirect`; its first
source-qualified leaf,
`economic.indirect_output.budget.fare_grosskopf_lovell_1993`, evaluates the
output or service opportunity available from an input budget. It is neither
cost minimization at fixed outputs nor revenue maximization from a fixed input
vector. See
[Färe, Grosskopf, and Lovell (1993)](https://doi.org/10.1017/CBO9780511551710.007).

The Nerlovian measure is not simply a monetary loss. It divides the attainable
profit gap by the price value of a declared direction, so the result contract
must separate the raw monetary gap from the normalized directional
inefficiency. See
[Chambers, Chung, and Färe](https://doi.org/10.1023/A:1022637501082).

Maximum profit itself also requires a technology decision. The VRS simplex
used by `economic.profit.maximum` is finite but does not contain automatic
shutdown: if every observed activity loses money, its maximum may still be
negative. Adding the origin or replacing the convexity equality with an
inequality changes the technology and belongs to
`economic.profit.maximum.shutdown`. Under unconstrained CRS, a single
positive-profit activity creates an unbounded scale ray; a shutdown option
does not impose a capacity limit and therefore cannot cure that ray.

Profit efficiency, normalized Nerlovian inefficiency, return-to-dollar
efficiency, generalized-distance profitability, and lost profit on outlay
are not one executable `profitability` model. Their denominators, price
policies, decompositions, and zero-value domains remain source-qualified even
when they reuse the same cost/revenue/profit optimizers.

The implemented `economic.profitability.return_to_dollar` leaf merges the
exact historical aliases “return to the dollar” and observed profitability
for $p^\top y/(w^\top x)$. `ReturnToDollarEfficiency` and
`ProfitabilityEfficiency` are therefore two API names for one canonical
method, not competing estimators. The leaf reports the observed ratio, the
maximum reference ratio, and their relative efficiency. It does not itself
emit GDF technical, scale, or allocative components. The separately
implemented
`analysis.allocative_decomposition.profitability_gdf.zofio_prieto_2006`
internally composes this value leaf with matched CRS/VRS Chavas--Cox GDF
tasks and preserves all three target accounts.

Nor do all explanations of the same raw profit gap merge. The method atlas
retains radial, Russell, weighted-additive, SBM/ERG, Hölder, CCF-DDF,
modified-DDF/lost-profit-on-outlay, reverse-DDF, and general-direct
decompositions as source-qualified leaves. They may share the maximum-profit
numerator while changing the technical performance criterion, normalization,
target, indication property, or technical/allocative accounting rule.

“Capacity” is an umbrella, not one operator. Short-run physical plant capacity
asks how much output the installed quasi-fixed resources could support when
variable inputs may adjust; capacity utilization compares current output with
that potential. Economic capacity instead uses prices, costs, or revenues to
define the commercially relevant operating level. Unbiased capacity and other
source-qualified corrections impose further conditions. These questions
remain distinct from MPSS and scale efficiency, which change the scale
comparison rather than holding an installed resource base.

The intended defining articles for the physical-capacity candidate
`analysis.capacity.physical.fare_grosskopf_kokkelenberg_1989` and the MPSS
candidate `analysis.mpss.banker_1984` are
[Färe, Grosskopf, and Kokkelenberg (1989)](https://doi.org/10.2307/2526781)
and [Banker (1984)](https://doi.org/10.1016/0377-2217(84)90006-7).
Neither defining full text has been obtained in a form that permits an
equation-level freeze. Both identifiers therefore describe non-public
prototypes with status `deferred_to_next_version`, not source-qualified
public leaves.

The MPSS prototype currently explores a fixed-observed-mix, three-LP
reconstruction supported by later literature. Its exact synthetic checks
establish internal optimization properties only; they do not reproduce a
published Banker (1984) numerical table or close the defining-source gate.
The physical-capacity prototype similarly explores two matched CRS
output-expansion programmes using all-current-input and fixed-resource
limits. Its decomposition and partition checks are property evidence, not
proof that the reconstructed programme and result contract reproduce the
1989 article. Neither prototype appears in the public catalog or public API.
Promotion requires the defining equations, a frozen domain and target
contract, and an independent source-level oracle in a later version. Broader
capacity distinctions are reviewed by
[Ray (2015)](https://doi.org/10.1016/j.ejor.2015.03.024); the planned economic
capacity leaf `analysis.capacity.economic.segerson_squires_1990` remains
separately anchored to
[Segerson and Squires (1990)](https://doi.org/10.1016/0304-4076(90)90063-Y).

Congestion is not merely an input slack: it asks whether excessive input use
suppresses maximum attainable output. The FGL technology comparison and the
Cooper--Deng--Huang--Li one-model route are now explicit non-public audit
locators with status `deferred_to_next_version`: neither defining programme
and numerical oracle is complete enough for implementation. Weak, strong, and
directional congestion remain later-version literature boundaries rather than
public switches. An FGL comparison that changes the maintained
input-disposability technology is not the same estimand as a Cooper-line
additive/slack procedure that locates and allocates congestion, even when both
flag the same observation. These distinctions protect interpretation; they do
not create additional handbook model families.

An IRS/CRS/DRS classification, a scale-efficiency ratio, scale elasticity,
and the deferred MPSS concept are also different results. Scale efficiency is
a matched radial
CRS/VRS score ratio. Local RTS and scale elasticity concern one declared
efficient point and nearby scale changes. The provisional MPSS profile instead
searches globally
along the evaluated organization's fixed input and output proportions for
the operating-size interval with maximum technical average productivity.
None of these is the deferred physical-capacity concept, which holds
quasi-fixed resources in a short-run counterfactual. These distinctions are
retained for field mapping and do not create public implementations. Scale
elasticity may have different left and right values at a kinked empirical
frontier. See
[Førsund and Hjalmarsson
(2004)](https://doi.org/10.1057/palgrave.jors.2601741) and [Podinovski
(2017)](https://doi.org/10.1016/j.ejor.2016.09.029). Directional scale
elasticity permits non-proportional input or output change and therefore
records its direction; see [Yang and Liu
(2017)](https://doi.org/10.1080/03155986.2016.1273024).

At a kinked empirical frontier, one fitted multiplier vector does not
necessarily identify the economic response to one more unit of a resource or
one less unit of an undesirable output. The planned
`analysis.marginal_values.directional_derivatives.podinovski_etal_2016` leaf
therefore evaluates source-qualified one-sided directional derivatives and,
where appropriate, identified ranges for marginal products, substitution or
transformation rates, and scale response. These are local model implications,
not automatically market prices. See
[Podinovski et al. (2016)](https://doi.org/10.1287/opre.2015.1457).

Cross-sectional TFP efficiency is not ordinary Farrell technical efficiency
or the radial scale-efficiency ratio. Under a declared aggregate-quantity
framework, its technical, scale, and mix components can reveal a product or
input-composition loss even when a unit is technically efficient at an
apparently suitable scale. The aggregation assumptions and reconstruction
identity remain explicit.

Economies of scope are not scale efficiency. They compare joint production
with an explicitly constructed separate-production opportunity under
multi-output and separability assumptions; increasing the size of one
black-box technology does not answer that question.

## 3. Preferences, data conditions, and peer appraisal

### 3.1 Restricted or preference-informed weights

The core taxonomy includes:

- assurance-region type I and II restrictions;
- cone-ratio restrictions;
- absolute, relative, and virtual-weight bounds;
- linked or common weights;
- value-judgement and preference-cone formulations;
- value-efficiency analysis based on a declared most-preferred efficient plan;
- weight restrictions compatible with multiplier/envelopment duality.

The distinctions and modeling consequences of these restrictions are reviewed
by [Allen et al.](https://doi.org/10.1023/A:1018968909638).

These methods restrict the trade-offs with which outputs and inputs may be
valued. They are not data cleaning and do not turn technical efficiency into
welfare efficiency unless the restrictions have an explicit welfare basis.
AR-I/absolute/cone restrictions may share a polyhedral multiplier engine.
They remain separate leaf families because their units, homogeneity,
consistency checks, and dual restrictions differ. AR-II links input and
output multipliers across valuation sides. Wong--Beasley virtual-share bounds
instead restrict a factor's share of total virtual input or output and depend
on the evaluated observation. They are not aliases. Production trade-offs
modify the attainable technology, whereas preference restrictions limit
acceptable valuations; their possible dual relationship does not merge their
economic semantics. Every restricted-weight fit also audits feasibility, unit
dependence, and whether the restrictions imply free or unlimited production.

Three preference/appraisal lineages need their own planned source leaves.
`valuation.value_efficiency.halme_etal_1999` starts from a declared
most-preferred efficient plan and its implied value trade-offs
([Halme et al. 1999](https://doi.org/10.1287/mnsc.45.1.103)).
`evaluation.common_weight.roll_cook_golany_1991` asks organizations to accept
one shared valuation system
([Roll, Cook, and Golany 1991](https://doi.org/10.1080/07408179108963835)).
`evaluation.mcdea.li_reeves_1999` instead makes discrimination and other DEA
criteria part of an explicit multiobjective compromise
([Li and Reeves 1999](https://doi.org/10.1016/S0377-2217(98)00130-1)).
Weight restrictions change the feasible valuation set, value efficiency
uses a preferred efficient plan, common weights impose a shared appraisal
rule, and MCDEA selects among several objectives. They can share multiplier
blocks but are not aliases; MCDEA remains an official neighboring extension
unless its variables and objectives retain a defensible production meaning.

Benefit-of-the-doubt models reuse DEA multiplier machinery to construct
endogenous composite-indicator weights, often through a common constant input.
They answer an indicator-aggregation or policy-evaluation question, not a
production-efficiency question unless the indicators have a defensible
production interpretation.  DEAPack therefore treats them as a named
neighboring extension rather than silently reporting their composite score as
technical efficiency. A field introduction is provided by
[Cherchye et al.](https://doi.org/10.1007/s11205-006-9029-7).
The planned `composite.benefit_of_doubt.linear.cherchye_etal_2007` leaf
therefore returns a composite indicator, the selected indicator weights,
normalization and restriction diagnostics, rankings, and sensitivity results;
it does not populate a production-efficiency field.

### 3.2 Study design, variable selection, and deterministic stability

Variable choice defines the represented production process before it affects
any linear programme. The package therefore treats variable selection as a
reported study-design procedure, not a technology and not an optimization
whose default objective is to make the observed sample look more efficient.
The supported map includes:

- production-theory and process-map selection;
- efficiency-contribution or ECM-style procedures;
- regression/test and bootstrap stability procedures;
- PCA or other declared dimension-reduction methods;
- penalized, cardinality-constrained, and all-subsets procedures where their
  validation and computational domains are explicit.

Every procedure records its candidate schema, selection criterion, tuning
path, final variable roles, and stability/sensitivity evidence. Selection on
the same sample changes the statistical problem and must be visible in later
inference. Reviews include
[Nataraja and Johnson](https://doi.org/10.1016/j.ejor.2011.06.045) and
[Peyrache, Rose, and Sicilia](https://doi.org/10.1016/j.ejor.2019.09.028).

Deterministic sensitivity is a separate layer. Allowable perturbations,
stability regions, simultaneous changes, leave-one-out influence, and
assumption-sensitivity fits answer how a fitted conclusion changes when
declared inputs change. They are not bootstrap sampling uncertainty, robust
optimization, or permission to delete an influential observation.

### 3.3 Variables outside the ordinary discretionary continuous case

The eleven-axis grammar is retained, but `data_roles` has a mandatory nested
representation/domain contract. For every modeled field the study records:

| `data_roles.representation` field | Required distinction |
|---|---|
| `measurement_scale` | `cardinal`, `ordinal`, `nominal`, or `ratio` |
| `sign_domain` | `nonnegative` or `signed` |
| `divisibility` | `continuous`, `integer`, or `binary` |
| `observation_status` | `exact`, `interval`, `fuzzy`, or `missing` |
| `controllability` | `discretionary`, `fixed`, or `bounded` |

This substructure does not add a twelfth top-level axis or alter the current
machine schema. It prevents an economic role from silently determining a
mathematical representation: a desirable output may be signed, an
undesirable output may be nonnegative, and a fixed input may be exact or only
interval-observed.

The data/model boundary must support, through named formulations:

- non-discretionary and semi-discretionary inputs/outputs;
- operational quantity bounds and fixed commitments;
- flexible-role factors whose input/output role is selected by an explicit
  model;
- nominal/ordered categorical, ordinal, and qualitative data;
- ratio and percentage variables;
- bounded and integer variables;
- zero and negative observations;
- interval, imprecise, missing, or fuzzy observations;
- uncontrollable contextual conditions;
- undesirable inputs as distinct from undesirable outputs.

There is no universal preprocessing rule. Translation, normalization,
categorical comparability, and denominator validity are properties of the
selected measure.

Capability declarations are paired with executable, source-qualified recipes.
The Banker--Morey (1986) formulation for exogenously fixed inputs/outputs and
their categorical-variable formulation are two such recipes, not a generic
`restricted_data=True` switch. Later formulations receive separate records
when they change admissible peers, managerial target rights, convexification,
or solver form.

In particular:

- non-discretionary variables affect feasible comparison but are not
  managerial targets, while contextual variables may change the relevant
  technology;
- ordinal values cannot be used as ordinary cardinal quantities;
- integer/discrete production generally needs a mixed-integer technology, not
  rounded continuous targets;
- ratio variables need a technology whose convexity has economic meaning;
- negative values are a data-domain issue, not undesirable outputs;
- zero values may invalidate fractional, logarithmic, or observation-scaled
  measures even when the underlying production observation is valid;
- `bounded` must distinguish a physical/operational bound from interval
  uncertainty and from BAM normalization bounds.
- missing observations require an explicit missingness/comparison policy;
  they are not automatically zeros, intervals, or fuzzy quantities.

Ratios and percentages require more than a data-type flag. Treating an
intensity, quality rate, or unit cost as if it were an ordinary additive
quantity can make convex mixtures economically meaningless. The planned
`technology.ratio.olesen_petersen_podinovski_2015` leaf retains the
source-defined relationship between ratio factors and the production
technology, including denominator and convexification conditions. It remains
distinct from `data.ratio`, which only declares what was observed, and from
interval/IDEA models in which a ratio expresses incomplete information. See
[Olesen, Petersen, and Podinovski (2015)](https://doi.org/10.1016/j.ejor.2015.03.013)
and their
[computational treatment](https://doi.org/10.1016/j.ejor.2017.02.021).

Integer DEA therefore receives executable technology/measure recipes and an
optional MILP compiler; `data.integer_discrete` alone is only a semantic
declaration. The source-qualified
`data.integer_discrete.lozano_villa_2006` recipe addresses integer-valued
efficiency targets
([Lozano and Villa](https://doi.org/10.1016/j.cor.2005.02.031)), whereas
`technology.integer_discrete.kuosmanen_kazemi_matin_2009` defines an
integer-valued production technology
([Kuosmanen and Kazemi Matin](https://doi.org/10.1016/j.ejor.2007.09.040)).
They are not aliases: declaring a variable discrete does not by itself define
the attainable integer technology or the target objective.
The bare acronym “IDEA” is never a canonical ID because it is used for both
integer and imprecise-data DEA.

Signed observations require a measure whose direction, translation behavior,
and scale assumptions remain valid on that domain.  The range-directional
approach and source-qualified proportional or slack alternatives therefore
enter as named formulations; DEAPack does not “fix” negative values by adding
an undocumented constant.

For the original RDM, the managerial benchmark is the best observed value in
each account within the exact comparison population. A unit's direction is
the remaining input saving and desirable-output growth available between its
own record and those coordinatewise best values. The coordinatewise ideal is
an aspiration device, not a claim that one peer can jointly deliver every
best value.

The signed-data evidence line is deliberately plural:

- `static.range_directional.portela_thanassoulis_simpson_2004` uses a
  focal-to-coordinatewise-ideal range direction under VRS and is
  implemented/public with native inefficiency $\beta$ and reported efficiency
  $1-\beta$
  ([Portela, Thanassoulis, and Simpson 2004](https://doi.org/10.1057/palgrave.jors.2601768));
- `static.sorm.emrouznejad_anouze_thanassoulis_2010` uses a semi-oriented
  radial account whose boundedness must be checked
  ([Emrouznejad, Anouze, and Thanassoulis 2010](https://doi.org/10.1016/j.ejor.2009.01.001);
  [boundedness analysis](https://doi.org/10.1016/j.ejor.2010.01.032)); and
- `static.msbm.signed` remains a research-only umbrella until one modified
  signed-data SBM formulation, normalizer, and oracle are frozen.

RDM, SORM, inverse RDM, RAM, signed-data SBM variants, radial models fitted
after translating the data, and undesirable-output DDFs are not aliases:
their improvement plans, economic output roles, normalizers, boundedness, and
translation properties differ. The original RDM therefore composes the
generic directional compiler without becoming the generic DDF. A zero is
also not automatically a negative-data case; it may instead invalidate a
denominator, logarithm, or observation-scaled direction. Adjacent signed-data
leaves remain planned until their own defining equations and oracles are
source-frozen.

Role uncertainty has its own boundary. The planned
`data.flexible_role.cook_zhu_2007` selects one common input/output
classification under an explicit model
([Cook and Zhu 2007](https://doi.org/10.1016/j.ejor.2006.03.048)).
`data.dual_role.cook_green_zhu_2006` permits a factor to enter both sides
under a source balance/reallocation account
([Cook, Green, and Zhu 2006](https://doi.org/10.1080/07408170500245570)).
Selecting one role and modeling a simultaneous dual role are distinct
managerial accounts.

Missingness is not another role choice. Source-qualified planned treatments
include fuzzy membership
([Kao and Liu 2000](https://doi.org/10.1057/palgrave.jors.2600056)),
a conservative incomplete-observation policy
([Kuosmanen 2009](https://doi.org/10.1057/jors.2008.132)), and bounded
interval information
([Despotis and Smirlis 2002](https://doi.org/10.1016/S0377-2217(01)00200-4)).
Deletion/comparison policy, imputation, interval information, and fuzzy
membership answer different evidentiary questions and remain separate
leaves.

### 3.4 Ranking, evaluation, and target policy

| Family | Core mechanism |
|---|---|
| super-efficiency | remove or modify self-reference to differentiate frontier units |
| cross-efficiency | apply peer-derived multiplier weights to other units |
| common-weight evaluation | choose a shared valuation system for comparison |
| aggressive/benevolent cross-efficiency | secondary objective for multiple multiplier optima |
| game cross-efficiency | solve the source-qualified protected-peer/focal-player LP system and its simultaneous equilibrium update |
| pessimistic or worst-practice appraisal | judge a unit using least-favourable weights or a source-qualified inefficient frontier |
| double-frontier evaluation | combine declared best- and worst-practice appraisals through a source-qualified ranking rule |
| reference-set analysis | distinguish observed, unary, maximal, and global reference sets |
| closest/furthest targets | choose among efficient operating plans using an explicit distance or priority rule |
| benchmarking tiers | peel, layer, or stratify empirical frontiers |
| selected-plan reference frequency | describe how often an observed unit appears on reported active peer edges in the solver-selected plans; any ranking rule is a separate evaluation protocol |

Super-efficiency is not cross-efficiency. Neither is merely a plotting option.
Infeasibility, instability, multiple optima, and sensitivity diagnostics are
part of their result contracts.

The canonical starting points are
[Andersen and Petersen](https://doi.org/10.1287/mnsc.39.10.1261) for
super-efficiency and
[Sexton, Silkman, and Hogan](https://doi.org/10.1002/ev.1441) for
cross-efficiency.

Leave-one-out infeasibility is not a missing-value convention and cannot be
hidden by switching RTS. The planned diagnostic
`evaluation.super.infeasibility.seiford_zhu_1999` records when and why a
declared super-efficiency programme is infeasible
([Seiford and Zhu 1999](https://doi.org/10.1080/03155986.1999.11732379)).
The planned
`evaluation.super.modified.cook_liang_zha_zhu_2009` is one specific modified
input/output construction for that problem
([Cook et al. 2009](https://doi.org/10.1057/palgrave.jors.2602544)).
Returning `NA`, modifying the technology, changing the direction, or using a
two-stage slack repair are different failure/remedy policies; no one is a
generic fallback for AP, super-SBM, and directional super-efficiency.

The evaluation inventory makes the different questions and release states
explicit:

| Evaluation question | Initial canonical leaves |
|---|---|
| differentiate frontier units | public `evaluation.super.sbm.tone_2002` ([Tone 2002](https://doi.org/10.1016/S0377-2217(01)00324-1)); deferred prototype `evaluation.super.ap_radial`; and public `evaluation.super.directional.ray_2008` ([Ray 2008](https://doi.org/10.1057/palgrave.jors.2602392)) |
| peer appraisal under admissible valuations | public Liang--Wu--Cook--Zhu game protocol; deferred prototype `evaluation.cross.crs`; four deferred Doyle--Green Method II/III aggressive/benevolent candidates ([Doyle and Green 1994](https://doi.org/10.1057/jors.1994.84)); and planned VRS leaf `evaluation.cross.vrs.lim_zhu_2015` ([Lim and Zhu 2015](https://doi.org/10.1057/jors.2014.13)) |
| find the next benchmark tier or a least-change strong target | `evaluation.frontier_tiers.context_dependent.seiford_zhu_2003` ([Seiford and Zhu 2003](https://doi.org/10.1016/S0305-0483(03)00080-X)) and `evaluation.target_selection.closest_strong.aparicio_ruiz_sirvent_2007` ([Aparicio, Ruiz, and Sirvent 2007](https://doi.org/10.1007/s11123-007-0039-5)) |

Context-dependent DEA in this table means evaluation relative to successive
frontier tiers. It is not conditional DEA, in which contextual conditions
alter the estimated opportunity set.

The `evaluation.super.ap_radial` reconstruction remains a non-public
prototype. Its internal implementation removes the evaluated observation
from an otherwise declared comparison population and preserves failed solver
states, but the unavailable defining full text prevents this release from
certifying the original orientation, RTS, data-domain, score, infeasibility,
target, or peer contract. The reopening gate is recorded in its source
protocol rather than filled from later summaries.

The public `evaluation.super.sbm.tone_2002` leaf answers a different
management question. It first uses ordinary non-oriented SBM under the same
RTS assumption to identify strongly efficient observations. Only those rows
enter Tone's self-excluded super-SBM programme; all other rows retain their
screen result and an explicit not-applicable super score. The supported
source surface is deliberately narrow: non-oriented, input-oriented, and
output-oriented CRS, plus non-oriented VRS. Every input and desirable output
must be strictly positive. VRS-oriented, NIRS/NDRS, zero/signed-data, and
undesirable-output variants remain separate future leaves. A larger score
means that the remaining organizations find the focal benchmark harder to
replace through variable-specific resource and service adjustments; it is
not an efficiency percentage.

The deferred ordinary CRS reconstruction applies one solver-selected primary
optimum per appraiser and labels its matrix and ranking as potentially
nonunique. It may store the complete peer-appraisal matrix or stream only its
column summaries. This is internal prototype behavior, not a current public
or source-qualified contract: the defining Sexton--Silkman--Hogan and
Doyle--Green full texts were not obtained. Including or excluding self is a
prototype aggregation policy; no source identity is inferred for either
choice. A secondary objective would require a separately source-frozen leaf.
Doyle--Green Method II and Method III, and their aggressive and benevolent
directions, remain four distinct deferred inventory candidates because their
objectives and aggregation objects have not been equation-frozen. Neutral
rules express still other evaluation choices. Common-weight evaluation
instead asks all units to accept one valuation system.

Game cross-efficiency is not another value of that secondary-objective field.
An ordinary secondary goal selects among one appraiser's primary multiplier
optima while preserving its self-efficiency. The implemented
`evaluation.cross.game_nash.liang_wu_cook_zhu_2008` instead fixes the CRS CCR
multiplier account and, at each synchronous iteration, solves one LP for
every protected DMU $d$ and focal/player DMU $j$. The $(d,j)$ problem
normalizes $j$'s virtual input to one, maximizes $j$'s own score under the
universal CCR inequalities, and adds exactly one floor preventing $d$'s
current score from deteriorating. It does not protect all peers in one
programme.

Writing that optimum as $g_{dj}(\eta_d^{(t)})$, the source update is

$$
\eta_j^{(t+1)}
=
\frac{1}{n}\sum_{d=1}^{n}g_{dj}(\eta_d^{(t)}).
$$

This equal arithmetic mean includes $d=j$ and is the source-native
payoff/update, not a free aggregation setting. All $n^2$ problems use the
same old vector $\eta^{(t)}$ before any score is updated; an asynchronous,
Gauss--Seidel, or damped implementation is a different policy. The resulting
pair table uses rows `protected_dmu_id` and columns `focal_dmu_id`. Because a
different multiplier vector may generate every cell, it is not the ordinary
cross-efficiency matrix whose row applies one appraiser's weights to all
evaluatees.

The source proves alternating bounds—its even iterates are nonincreasing, its
odd iterates are nondecreasing, and the even sequence remains above the odd
sequence—and claims a unique final score vector independent of arbitrary,
aggressive, or benevolent ordinary-cross-efficiency initialization. That is a
score claim, not multiplier uniqueness. The public implementation reports the
adjacent-update residual, recomputes one further complete map to verify the
fixed-point residual, labels a material alternating pattern only as a
suspected two-cycle, and returns no canonical equilibrium score after an LP
failure or maximum-iteration exit.

The current numerical oracle is frozen and automated over the project-created
four-plan `strategic_peer_service` fixture. A test-only dense SciPy compiler
assembles the source multiplier inequalities, focal normalization, and one
protected floor directly; it imports neither the production private compiler
nor its LP wrappers. From the declared $(0.80,0.85,0.95,0.50)$ profile, the
independent map stops after four synchronous iterations at $\epsilon=0.001$
with scores $(0.9793602,0.9761513,1,2/3)$ and passes a fresh-map residual
check. At high precision it reaches $(761/777,41/42,1,2/3)$ and independently
checks the complete protected--focal matrix. This is a `cross_implemented`
oracle and explicitly not a reproduction of the Liang article's observations
or numerical-result table.

The protocol costs $n^2$ LP solves per iteration before any initialization
cost. It belongs mainly to $P$, with players in $C$; the fixed CCR account
remains in $T/E/M/V$, and $A$ begins only with downstream ranking or
reporting. The protocol is Level D rather than an alias of ordinary
tie-breaking. It is implemented/public with a machine-registry record,
independent project-fixture oracle, benchmark, API, and package documentation.
Its machine publication scope is `documentation_only`; it has no current
Handbook chapter. See
[Liang, Wu, Cook, and Zhu
(2008)](https://doi.org/10.1287/opre.1070.0487).

Reference-set analysis must likewise separate an ex-ante benchmark policy
from a fitted result. The planned candidate
`analysis.reference_set.global.mehdiloozad_etal_2015` identifies a global
reference set/minimum face across alternate projections. It occupies $A/P$
and is Level D/non-alias with the all-period information policy
`reference.global` on $R$. See
[Mehdiloozad et al.
(2015)](https://doi.org/10.1016/j.ejor.2015.03.029). No implementation is
asserted.

The implemented `analysis.reference_frequency.selected_plan` is narrower. It
counts reported active peer edges strictly above the source result's
`peer_tolerance` in one complete, certified solver-selected plan from a static
convex global cross-section, separates self from other use, and normalizes
total frequency by the complete evaluated roster. It performs no refit and
does not claim alternate optima, a maximal or
global reference set, influence, outliers, ranking, or inference. Torgersen,
Førsund, and Kittelsen's benchmark-importance procedure
([1996](https://doi.org/10.1007/BF00162048)) and Doyle--Green's reference-count
discussion ([1995](https://doi.org/10.1080/03155986.1995.11732281)) are
historical lineage, not aliases: the current diagnostic does not implement
the former's full slack-adjusted peer-importance/ranking account. Mehdiloozad
et al.'s global/minimum-face procedure remains the distinct planned analysis
above. Reference frequency is therefore a Handbook sensitivity inside study
design, not another evaluation or technology route.

Pessimistic and double-frontier approaches answer another appraisal question.
A least-favourable multiplier programme, a worst-practice empirical envelope,
and a geometric or interval combination of optimistic and pessimistic scores
are not one estimator. Nor is this use of “pessimistic” the adverse data
realization in robust optimization or the aggressive secondary objective used
after a cross-efficiency self-appraisal. Inverted DEA, anti-efficiency, and an
artificial anti-ideal unit become aliases of a worst-practice construction
only when their complete programmes, RTS, orientation, and score transforms
coincide. These methods are retained as
source-qualified ranking procedures rather than presented as a more truthful
production frontier. The discovery records
`evaluation.pessimistic_multiplier`,
`evaluation.worst_practice_frontier`, and `evaluation.double_frontier`
therefore remain separate. A first source-qualified combination leaf is
`evaluation.double_frontier.geometric.wang_chin_yang_2007`; its primary
equations and score convention must be frozen before promotion. A starting
point is
[Wang, Chin, and Yang (2007)](https://doi.org/10.1057/palgrave.jors.2602205);
the wider ranking family is reviewed by
[Aldamak and Zolfaghari (2017)](https://doi.org/10.1016/j.measurement.2017.04.028).

Family names are not executable models by themselves. Tone (2002)
super-SBM is public; radial Andersen--Petersen is a deferred internal
prototype; Ray (2008) directional super-efficiency is public; and other
directional or potential-slack constructions remain separate planned leaves.
The three source-qualified public evaluation leaves are package-
Documentation procedures, not separate current Handbook routes. These
protocols have different objectives, applicability gates, data domains, and
infeasibility policies. Ordinary CRS cross-efficiency is also deferred, and
any future VRS leaf still requires separate treatment because the free
intercept does not transfer mechanically. Every executable composition
records its base measure, reference exclusion, zero/negative policy,
secondary objective, aggregation rule, multiplicity, and stability.
For the Liang--Wu--Cook--Zhu game leaf, the equal mean including self is
recorded as a fixed source protocol component rather than exposed as an
aggregation option.
Super-efficiency is often valuable as an influence or frontier-extremeness
diagnostic; that does not make it a universally valid league-table ranking.

Efficient-facet/EXFA procedures form another advanced target and diagnostic
family. They identify full-dimensional efficient facets for strong targets,
marginal trade-offs, and checks on ill-conditioning or model
misspecification. They are not simply a closest-target norm or the arbitrary
dual hyperplane returned by one solve.

## 4. Undesirable outputs and environmental performance

Environmental DEA is a collection of production accounts and measures, not a
single “bad-output option.” The review literature includes
[Scheel (2001)](https://doi.org/10.1016/S0377-2217(00)00160-0),
[Førsund (2009)](https://doi.org/10.1561/101.00000021), and
[Dakpo, Jeanneaux, and Latruffe (2016)](https://doi.org/10.1016/j.ejor.2015.07.024).

### 4.1 Production accounts

| Account | Economic interpretation | Treatment |
|---|---|---|
| reciprocal/translation transformation | legacy replication device | supported with warnings; not the default theory |
| bad treated as input | burden proxy in selected applications | explicit legacy/sensitivity model |
| strong disposability | bad output can be reduced without a modeled sacrifice | named assumption; potentially defensible when control resources are already modeled |
| weak disposal, single factor | a common abatement proportion reduces the represented activity | distinct empirical technology, not the definition of weak disposability itself |
| weak disposal, activity-specific | reference activities can use different abatement proportions | distinct empirical technology; scale and convexity remain independent |
| generalized/exponential weak disposal | desirable and undesirable outputs may contract at different rates over a source-qualified piecewise Cobb--Douglas environmental technology | advanced nonlinear production account; not an option on a linear weak-disposal hull |
| selective disposability | different pollutants face different control opportunities | pollutant-level strong/weak declarations |
| semi-disposability | part of a residual may be freely reducible before further reduction requires production sacrifice | research-only lineage: the Chen--Wang--Lai account and Chu et al.'s refined 2026 production set remain distinct pending source reconciliation |
| null jointness | no desirable output without associated residual generation under the specified process | independent axiom/test; not implied by weak disposal |
| costly disposability | reducing residuals requires a declared production sacrifice, pollution-control input, or treatment process | environmental technology restriction; not ordinary cost efficiency |
| by-production | intended output and residual generation obey separate but connected technologies with declared pollution-generating inputs and costly disposal | distinct compiler with explicit intersection and coupling/dependence rules |
| joint-input parallel production/pollution | intended production and pollution generation are parallel subtechnologies constrained to use the same target for every jointly consumed pollution-generating input | source-qualified coupled by-production account; not independent component plans, duplicated input use, or shared-resource allocation |
| factorial/multi-equation production | intended output, raw residuals, and end-of-pipe treatment are modeled as connected processes | richer production system with explicit abatement activities |
| material-balance production/treatment network | material coefficients determine primary pollution, the primary flow enters explicit end-of-pipe treatment, and final discharge obeys the residual balance | coefficient-aware serial production account; not weak disposal, material-inflow efficiency, or an unconstrained undesirable link |
| Coelli material-inflow account | material-bearing inputs are minimized for a fixed desirable-output plan; $TE$, $EE$, and physical-content $EAE$ are kept separate with $EE=TE\times EAE$ | named physical efficiency/decomposition; not price allocative efficiency |
| weak-$G$ material-balance technology | material inflow, material retained in products, and residuals obey summing-up restrictions | coefficient-aware technology, not a score normalization |
| natural disposability | resource saving combined with pollution reduction under its named production account | distinct operating-strategy variant |
| managerial disposability | selected environmental inputs may increase to support pollution control | distinct environmental-investment strategy, not an alias for natural disposal |

Weak disposability is an economic axiom, not one unique linear programme.
[Kuosmanen (2005)](https://doi.org/10.1111/j.1467-8276.2005.00788.x)
and
[Pham and Zelenyuk (2019)](https://doi.org/10.1016/j.ejor.2018.09.019)
show why the single common abatement factor and activity-specific
constructions must be identifiable. `null_jointness`, pollutant-level
disposability, convexity, and returns to scale remain separate attributes.

The legacy public selector spelled `weak` selects only
`environmental.formulation.bad_output_directional_equality`. It does **not**
identify either complete weak-disposal technology and must not be cited,
reported, or tested as if it did. The selector is an equality-formulation
compatibility spelling, not a $T$-axis technology claim, and now emits a
deprecation warning while reporting `not_identified`.

Two source-frozen public technologies are separate leaves:

- `environmental.weak_disposal.common_factor.crs.chung_fare_grosskopf_1997`
  uses the CRS equality construction; its generic directional composition is
  `environmental.ddf.weak_disposal.common_factor`, and the fixed observed
  output direction is
  `environmental.ddf.output.chung_fare_grosskopf_1997`;
- `environmental.weak_disposal.activity_specific.vrs.kuosmanen_2005` uses
  the exact $(\mu,\tau)$ convex linearization; its directional composition is
  `environmental.ddf.weak_disposal.activity_specific`.

The two named technologies are not aliases of one another, of strong
disposal, or of the equality-only compatibility formulation. The evidence
boundary follows
[Chung, Färe, and Grosskopf
(1997)](https://doi.org/10.1006/jema.1997.0146),
[Kuosmanen (2005)](https://doi.org/10.1111/j.1467-8276.2005.00788.x), and
[Pham and Zelenyuk
(2019)](https://doi.org/10.1016/j.ejor.2018.09.019).

Generalized weak disposal changes the trade-off path and technology itself
([Roshdi et al.](https://doi.org/10.1016/j.ejor.2017.10.033)).
Semi-disposability is also retained as a research lineage rather than a
generic interpolation flag because its original and refined production sets
are not equivalent
([Chen, Wang, and Lai](https://doi.org/10.1016/j.ejor.2016.12.042);
[Chu et al.](https://doi.org/10.1016/j.ejor.2026.07.013)).

Weak disposal, by-production, and material balance may all use a directional
measure, but they do not describe the same feasible technology. Coelli-style
material-input efficiency, weak-$G$ material-balanced production, and
by-production are likewise different layers:

- the first minimizes material-bearing inputs for required production;
- the second imposes physical conservation restrictions; and
- the third separates intended production from residual generation.

Their special-case relationships must be stated and tested rather than used
as aliases. Core sources include
[Coelli et al.](https://doi.org/10.1007/s11123-007-0052-8),
[Murty, Russell, and Levkoff](https://doi.org/10.1016/j.jeem.2012.02.005),
and
[Rødseth](https://doi.org/10.1007/s10640-015-9974-1).

The source-native `environmental.material_inflow.coelli2007` claim is now
frozen more narrowly than the broad material-flow family. Equations
(23)--(26) of
[CEPA Working Paper 06/2005](https://economics.uq.edu.au/files/5310/WP062005.pdf)
define two ordinary input-envelopment programmes and the $TE$, $EE$, and
$EAE=EE/TE$ account; the source explicitly obtains VRS by adding convexity to
both LPs. The certified composition uses one self-inclusive cross-section,
ordinary nonnegative inputs and desirable outputs, one common vector of known
nonnegative material contents, positive observed inflow, and a fixed
desirable-output commitment. It consumes neither an observed bad-output
column nor an explicit abatement process, and EAE requires no prices or
damage weights.

An independent exact synthetic compiler closes CRS and VRS scores, the
$EE=TE\times EAE$ identity, and the fixed-output material-minimum account.
It does not make the material-minimizing target unique and does not reproduce
the source's unit-level 183-farm observations, which are not supplied. The
source defines weighted multiple pollutants in equations (18)--(21), but that
extension still lacks independent validation. NIRS/NDRS, multi-material
aggregation, heterogeneous or estimated coefficients, panel/custom/external
source equivalence, the farm application, and welfare, causal, damage, or
actual-emission interpretations remain `deferred_to_next_version`.

For by-production, “two frontiers” is not a sufficient model definition. The
compiler records which inputs generate residuals, the good-output and
residual subtechnologies, costly-disposal inequalities, their intersection,
and any dependence or coupling constraints. Omitting one of these changes the
represented production account even when the performance measure is
unchanged.

The public `environmental.by_production.ddf` leaf now freezes the conventional
DDF exactly as Murty--Russell--Levkoff analyze it: CRS in both
subtechnologies, separate intensity systems over one self-inclusive
cross-section, and one nonnegative direction held fixed across
organizations. Their five-DMU equation (5.6) is reproduced and the complete
component vectors are checked by an independent dense compiler. The source
uses BP-DDF to expose weak indication and direction sensitivity; its proposed
response is the distinct FGL index. VRS/NIRS/NDRS, observation-varying
directions, panels, and non-global references remain labelled package
extensions rather than inheriting this certificate.

The public `environmental.by_production.fgl` leaf separately freezes the
authors' proposed response in equations (5.9)--(5.10): coordinatewise
desirable-output expansion and residual contraction, separate component
intensity systems, equal within-component weights, and an equal one-half
aggregation under CRS. The source-printed DMU 2 and 3 scores and the exact
five-DMU consequences are checked by independently compiled scalar
programmes. Its native unit score certifies component output-vector
efficiency, not the absence of input slack; the generic Pareto--Koopmans flag
therefore remains missing. VRS/NIRS/NDRS, temporal or custom references, and
the displayed `1 - efficiency` complement are labelled package extensions.

Making by-production dynamic is not repeated static estimation and is not
obtained by declaring pollution a harmful Tone--Tsutsui carry-over. The
planned/evidence candidate
`dynamic.environmental.by_production.adjustment_cost.dakpo_oude_lansink_2019`
combines intended and residual subtechnologies with investment and adjustment
costs. It occupies $G,D,T,M$ and is Level D relative to static
by-production, the Cuadros weak-disposal electricity model, and ordinary bad
carry-over SBM. No executable leaf is claimed. See
[Dakpo and Oude Lansink
(2019)](https://doi.org/10.1016/j.ejor.2018.12.040).

The joint-input parallel account is one such source-qualified coupling: the
same pollution-generating-input target must enter intended production and
pollution generation. It is not an allocation from a shared resource pool.
A material-balance treatment network instead uses physical coefficients to
create a primary-pollution flow, sends that flow to an explicit treatment
process, and reconciles treatment with final discharge. That serial physical
identity is not obtained by relabeling a by-production bad output as a link.

### 4.2 Environmental measures and analyses

The package scope includes:

- environmental DDF with explicit good expansion, bad contraction, and input
  directions;
- Tone-style separable, strongly disposable undesirable-output SBM;
- Tone's non-separable radial/slack SBM hybrid; source-qualified SBM measures
  over named weak-disposal technologies; directional SBM; and non-radial
  directional/Russell variants as separately named measures;
- enhanced hyperbolic and environmental graph measures;
- by-production radial, directional, and non-radial/FGL-style measures;
- Coelli material-inflow, weak-$G$, and multi-equation material-flow measures;
- pollution-adjusted cost, revenue, and profit measures where prices or
  damage valuations are supplied;
- pollutant-specific shadow prices and marginal abatement-cost indicators;
- energy, carbon, and eco-efficiency indicators with explicit numerator,
  denominator, and aggregation semantics;
- network and dynamic environmental production.

An equal-weight environmental score is not automatically a social-welfare
measure. Shadow prices are local model-based trade-offs, not observed market
prices or causal damage estimates. Since a piecewise-linear frontier may have
multiple supporting prices, the result contract must be able to report a
shadow-price interval or alternative optima rather than only the arbitrary
dual selected by one solver.

### 4.3 Environmental regulation and compliance decisions

Environmental regulation can enter a DEA study in five economically distinct
ways:

| Regulatory role | Model consequence |
|---|---|
| emissions, intensity, or technology standard | restricts the legally feasible operating plans and can create a measurable compliance sacrifice |
| tax, permit price, or damage value | supplies valuation for an environmental cost, revenue, or profit question |
| industry-wide emissions cap | creates a centralized fixed-sum allocation problem across organizations |
| inherited regulatory regime | helps define a group, comparison population, or conditional opportunity set |
| policy intervention whose effect is being studied | requires a separate causal design; a before/after DEA score is not identification |

[Zofío and Prieto (2001)](https://doi.org/10.1016/S0928-7655(00)00030-0)
show how a declared environmental standard can bind production and create a
legislative opportunity cost. A later bounded-variable construction is
provided by
[Bremberger et al. (2015)](https://doi.org/10.1057/jors.2013.176).
Centralized permit reduction and reallocation is a different decision-support
problem; one source-qualified example is
[Wu et al. (2013)](https://doi.org/10.1016/j.mcm.2012.03.008).
None of these is implied merely by labeling an output undesirable.

### 4.4 Important non-equivalences

- A radial Farrell model can be solved as a DDF special case for particular
  observation-scaled directions, but its historical native score and
  orientation remain part of the public specification.
- Environmental hyperbolic measures jointly scale desirable and undesirable
  outputs multiplicatively. They are not globally equivalent to an additive
  DDF.
- Non-radial DDF, weighted additive models, and directional SBM may share
  slack-balance machinery. Tone's fractional SBM is not their universal
  alias. The relationship and subsequent clarification in
  [Färe and Grosskopf](https://doi.org/10.1016/j.ejor.2009.01.031)
  and
  [Färe and Grosskopf](https://doi.org/10.1016/j.ejor.2010.02.033)
  must be retained in equivalence audits.
- Natural disposability generally represents resource reduction together
  with pollution reduction; managerial disposability permits selected
  environmental inputs to increase in order to control pollution. These are
  operating-strategy formulations, not alternative names for weak and strong
  disposal.

## 5. Productivity and performance change

Productivity methods combine repeated static evaluations, reference policies,
and index-number operators. Their interpretation is an accounting
decomposition relative to empirical benchmarks, not a causal diagnosis.

### 5.1 Distance-based productivity families

| Family | Main variants | Canonical decomposition |
|---|---|---|
| Malmquist | input/output, adjacent, chained | efficiency change and change in best-practice opportunities |
| quasi-Malmquist | one-sided non-radial slack comparisons | Grifell--Tatjé--Lovell--Pastor source-qualified change; not a radial MPI alias |
| generalized Malmquist | MPI combined with a scale index | Lovell--Grifell--Tatjé source-qualified output/input quantity-index construction; not global Malmquist or generalized distance |
| FGNZ Malmquist | public output-oriented CRS core preset plus a distinct public six-task CRS/VRS enhanced method | the core reports efficiency and technical change; the enhanced leaf uses two additional own-period VRS tasks to report pure-efficiency change and FGNZ's own-period scale-efficiency change |
| Ray--Desli Malmquist | public output-oriented CRS headline plus four VRS auxiliary tasks on a balanced, strictly positive, one-desirable-output panel | source-native pure-efficiency change, VRS opportunity change, and cross-period scale contribution; valid CRS and own-period VRS components survive VRS cross-task infeasibility |
| Luenberger indicator | input/output/general directional, additive | performance change and change in opportunities |
| configurable environmental directional productivity | deferred four-distance or common-global directional candidate over an explicitly named environmental technology | private numerical orchestration only; no public method or historical ML/GML identity is inferred until a defining source and validation cover the complete configuration domain |
| Chung--Färe--Grosskopf Malmquist--Luenberger | CRS common-factor weak-disposal environmental distance, null jointness, and the observed $(0,y,-b)$ programme | source-qualified environmental performance and opportunity-change components |
| consistent/APZ Malmquist--Luenberger | implemented/public CRS preset combining the 2017 capped-bad-output inequality technology with the standard four-distance adjacent ML account | evaluates the same four contemporaneous own-/cross-period roles on distinct APZ technologies with componentwise reference-period pollutant caps; it is not a reporting convention or a post-processing sign correction |
| global Malmquist | radial distance with a common full-sample reference | global radial performance ratios and optional named decompositions |
| Oh global Malmquist--Luenberger (GML) | CRS common-factor weak-disposal environmental distance with the observed $(0,y,-b)$ programme and one pooled conical full-sample reference | source-qualified $GML=EC\times BPC$ accounting with nonnegative own/global distances, source BPG at most one, fixed-vintage circularity, and retrospective revision; not an acronym for global Malmquist |
| biennial indexes | common two-period reference | adjacent comparison with later-sample stability |
| SBM Malmquist and SBM Malmquist--Luenberger | non-radial slack accounting | source-qualified productivity identities that are not aliases for radial or DDF indexes |
| sequential/window reference designs with a named index | expanding or moving reference | information-vintage-specific comparisons; the reference rule alone is not a productivity index |
| Luenberger--Hicks--Moorsteen | additive total-output and total-input quantity accounting | complete TFP construction distinct from an ordinary directional Luenberger indicator |

The APZ preset is public as
`productivity.malmquist_luenberger.aparicio_pastor_zofio_2013`. Its 2013
theory identifies the consistency problem; the 2017 operational article
closes the executable model in equations (5)--(6). For every reference period
and pollutant, the CRS technology replaces the conventional bad-output
equality by an inequality and caps the projected bad output at that period's
componentwise observed maximum. The direction remains the target
observation's $(0,y,-b)$ programme, and the accounting remains the standard
four-distance geometric ML identity. The short spelling
`productivity.malmquist_luenberger.apz` is a discovery alias only; the full
Aparicio--Pastor--Zofío identifier is retained in machine and result
provenance.

The source-qualified domain requires componentwise strictly positive inputs
and undesirable outputs, nonnegative desirable outputs, two contemporaneous
CRS technologies, and four own-/cross-period roles. APZ substantially reduces
but does not eliminate cross-period infeasibility: a failed required task
leaves the dependent component and headline index unavailable rather than
triggering a substitute benchmark or a sign adjustment. An independent exact
compiler obtains distances $2/5$, $3/11$, $3/5$, and $5/11$ for producer B in
the 2013 Table 1 example, giving $EC=77/80$, $TC=8/7$, and $ML=11/10$. This is
an analytically derived source-fixture certificate, not a reproduction of the
2017 WIOD application. See
`source_protocols/aparicio_pastor_zofio_2013.md` and
`oracles/aparicio_pastor_zofio_2013.md`.

Oh's global benchmark is operationalized as one CRS conical DEA envelope
generated by all observations in the declared sample vintage. The literal
union notation in the source and this pooled conical computation must not be
silently treated as a general set identity. For every source task, the
evaluated plan belongs to both its contemporaneous reference and the global
reference; hence the own/global directional distances are nonnegative. The
source best-practice gap has the efficiency orientation
$BPG^r=(1+D^r)/(1+D^G)\leq1$, while
$BPC^{t,t+1}=BPG^{t+1}/BPG^t$ and
$GML=EC\times BPC$. Oh's pairwise identity is not theoretically limited to
adjacent periods; matched adjacent transitions are the current package
enumeration protocol. The exact analytical certificate covers two- and
three-period fixtures, fixed-vintage circularity, independent dense
compilation, and coherent unit changes. It is not a reconstruction of the
published 26-country application. That empirical replay, literal-union and
non-CRS estimators, alternate directions or environmental technologies,
non-global reference policies, arbitrary nonadjacent API enumeration, and
inference or welfare claims remain `deferred_to_next_version`.

A measured frontier shift may be neutral in size yet favor particular input
or output mixes. The planned
`productivity.malmquist.decomposition.technical_change_bias.fare_etal_1997`
leaf separates the magnitude of technical change from source-defined input-
and output-bias components. This is a productivity-accounting description of
which operating mixes benefited from the shift, not evidence that a policy or
managerial action caused it, and not an alias for variable-specific
productivity indicators. See
[Färe et al. (1997)](https://doi.org/10.1111/1467-9442.00051).

Comparison population, temporal information set, evaluation exclusions, index
formula, orientation/direction, and scale assumptions are stored separately.
A global temporal reference avoids some cross-period infeasibility and
supports circular comparisons, but it is retrospective and can change when
later observations enter the sample. Every pooled information policy also
states whether it envelops raw observations, unions preconstructed period
technologies, or applies another declared hull construction, together with
its convexification and RTS. `global` or `biennial` alone is not a complete
technology specification, and neither says which organizations belong to the
comparison population.

Sequential technology embeds the assumption that previously observed
best-practice opportunities remain available. An absence of measured
technical regress is then partly a design consequence, not an empirical
discovery. Window DEA is first a moving benchmarking design. Repeated window
scores are registered as `analysis.window_efficiency`; they become a
productivity index only when paired with an explicit accounting rule.
Biennial environmental productivity is a supported composition only when a
named ML/SBM-ML accounting rule is paired with the adjacent-pair reference;
the word “biennial” alone is not the operator.

### 5.2 Multiplicatively complete and alternative TFP indexes

The comprehensive scope also includes:

- cross-sectional TFP efficiency and its technical, scale, mix, and
  scale-mix decomposition under a declared aggregate-quantity framework;
- Hicks--Moorsteen indexes;
- Färe--Primont indexes and their efficiency/technology decompositions;
- the Bjurek/Moorsteen historical terminology as part of the
  Hicks--Moorsteen family, rather than a duplicate solver family;
- profitability and price-based productivity decompositions;
- cost Malmquist and other price-informed productivity measures under an
  explicit intertemporal price policy;
- Kumar--Russell non-parametric growth accounting, which separates frontier
  change, operating-performance change, and capital deepening under its own
  path convention;
- input-, output-, and pollutant-specific productivity indicators;
- aggregate, group, and meta-frontier productivity comparisons.

The public `productivity.hicks_moorsteen.bjurek_1996` leaf implements the
adjacent-period Bjurek construction with both input and output quantity
indexes. It retains the eight underlying Shephard-distance tasks and reports
the reconstruction
$\text{TFP change}=\text{output quantity change}/\text{input quantity change}$.
Its analytic and invariance tests do not substitute for a claimed published
numerical oracle.

These indexes are not aliases for Malmquist. They use different aggregator or
index-number constructions and have different completeness, transitivity, and
data requirements. The registry records whether an index is a locally defined
technical-performance indicator or a multiplicatively/additively complete TFP
index under its stated axioms. See
[O'Donnell (2012)](https://doi.org/10.1007/s11123-012-0275-1).

The O'Donnell Färe--Primont source leaf is deferred to the next version. An
author working paper has been located, but the final journal text, complete
executable equation audit, and artificial-data oracle have not yet been
frozen. No public API or machine registration is inferred from this discovery
record; see `source_protocols/odonnell_2012_fare_primont.md`.

Two planned price-informed source leaves make that boundary concrete:
`productivity.profitability_decomposition.odonnell_2010` and
`productivity.profit_ratio_change.zhao_morita_maruyama_2019`. Both occupy
$V/A$, but they retain different price policies and reconstruction
identities. They are Level D relative to technical-only MPI and to each other,
not two names for one price-adjusted score. These are evidence candidates,
not implemented operators; see
[O'Donnell (2010)](https://doi.org/10.1111/j.1467-8489.2010.00512.x) and
[Zhao, Morita, and Maruyama
(2019)](https://doi.org/10.1016/j.omega.2018.09.012).

An ordinary Luenberger indicator and a Luenberger--Hicks--Moorsteen index are
not merged except under the restrictive conditions that make their
aggregators coincide.

The familiar pure-efficiency-change and scale-efficiency-change extensions of
Malmquist are named decompositions, not one uncontested identity. The current
version exposes the output-oriented CRS FGNZ two-component core as
`productivity.malmquist.decomposition.fgnz_core`, a public preset over the
shared adjacent geometric operator. That core certificate covers only the
four-task FGNZ account; the enhanced VRS extension has its own independent
six-task certificate. Neither certificate reproduces the published OECD
application.

The enhanced FGNZ pure-efficiency/scale extension, Ray--Desli, Balk, and
other scale/mix decompositions retain their own component definitions and
reconstruction obligations. Enhanced FGNZ is public as
`productivity.malmquist.decomposition.fgnz_pure_scale_extension`: it fixes
output orientation, uses four CRS tasks plus exactly two own-period VRS tasks,
and closes both $\mathrm{EFFCH}=\mathrm{PEFFCH}\times\mathrm{SCH}$ and the
three-factor productivity identity. Its strict-positive matched-panel source
certificate is narrower than tested package support for partial-zero cells
with positive row aggregates and explicit unbalanced `drop`/`raise` handling.
Ray--Desli has also passed its narrow independent exact-oracle gate and is public as
`productivity.malmquist.decomposition.ray_desli`: it fixes output orientation,
a strictly positive balanced matched panel, one or more inputs, exactly one
desirable output, four CRS plus four VRS tasks, and source-defined partial
components under VRS cross-task infeasibility. It shares the CRS headline and
radial compiler with the adjacent Malmquist operator but is neither an alias
nor the FGNZ scale extension. Balk remains a non-executable discovery record
under `source_protocols/fgnz_ray_desli_balk_decompositions.md`.

### 5.3 Panel-data safeguards

Every productivity operator must declare:

- DMU identifier matching and unbalanced-panel policy;
- adjacent versus non-adjacent comparison;
- benchmark vintage and reference-set membership;
- cross-technology feasibility policy;
- multiplicative (`> 1`) or additive (`> 0`) improvement convention;
- zero/negative-value domain restrictions;
- named components and the identity they are expected to satisfy.

For a directional indicator, directions must be comparable across the
observations and periods being combined. If a direction changes by DMU or
period, the package must either establish a common economic unit or refuse a
decomposition that adds incomparable quantities.

### 5.4 Heterogeneity versus aggregation

Meta-frontier productivity asks how group-specific opportunities, performance
within each group, and the gap to cross-group potential change. Industry or
group aggregation asks how an aggregate changes and whether reallocation
between units contributes. These are separate operators:

- meta-frontier results may include group efficiency change, group
  best-practice change, technology-gap change, and explicitly named
  leadership/best-practice-gap components;
- aggregate productivity requires an aggregation function, economic weights,
  and a statement about whether resources can be reallocated between units.

Neither operator is a generic `group_productivity=True` option.

Aggregation itself also splits into two questions. Economic aggregation of
unit-level productivity indexes requires explicit weights and an aggregation
identity. Group-potential/reallocation analysis instead permits or evaluates
resource movement between units. It can attribute change to allocation even
when no individual-unit index is being averaged; the two operators are not
one `aggregate_reallocation` model.

A meta-technology must also state how group technologies are combined.  A
non-convex union, a pooled convex hull, and another source-qualified
non-convex meta-construction can imply different opportunities and
technology-gap values; “the meta-frontier” is not sufficient metadata.
DEAPack records those production-set choices as
`technology.meta.nonconvex_union` and `technology.meta.pooled_convex`;
`reference.group` records which observations belong to a comparison group,
not how the resulting group technologies are combined. In the current public
surface, `reference.group` and `technology.meta.pooled_convex` are internal
composition labels used by the radial metafrontier leaf, not standalone fitted
operators or constructors. The nonconvex-union label remains a distinct
planned technology rather than an option silently substituted for pooling.
For a canonical firm-level meta-frontier treatment, see
[O'Donnell, Rao, and Battese](https://doi.org/10.1007/s00181-007-0119-4).

The implemented source leaf
`heterogeneity.metafrontier.radial.odonnell_rao_battese_2008` makes this
construction explicit. It estimates the same radial Farrell programme first
against the organization's declared group and then against all declared
groups pooled. Under VRS the pooled meta opportunity set is the
free-disposal convex hull (`pooled_convex`); under CRS it is the corresponding
cone (`pooled_conic`). The conceptual non-convex union of group technologies
is a different attainable set, not another spelling or option alias for this
leaf.

The result answers two management questions without turning either answer
into a causal claim. Within-group efficiency asks how well the organization
operates relative to the opportunities represented within its own group.
The metatechnology ratio (canonical `MTR`, with historical `TGR` retained
only as an alias) asks how close that group's best-practice opportunity
frontier is to the broader meta opportunity frontier at the evaluated mix.
Their exact accounting identity is
$E^{M}=E^{G}\times\mathrm{MTR}$.

## 6. Organizations with internal structure

The specialist network literature, including
[Färe and Grosskopf (2000)](https://doi.org/10.1016/S0038-0121(99)00012-9),
[Kao's review (2014)](https://doi.org/10.1016/j.ejor.2014.02.039), and the
[network DEA handbook](https://doi.org/10.1007/978-1-4899-8068-7),
shows that “network DEA” contains several independent modeling decisions.
[Castelli, Pesenti, and Ukovich
(2010)](https://doi.org/10.1007/s10479-008-0414-2) further distinguishes
network, shared-flow/multi-activity, and multilevel organizational accounts.
These accounts may reuse sparse blocks, but they are not merely three graph
spellings of one technology.

### 6.1 Production graphs

The structural compiler must eventually cover:

- basic series/two-stage systems;
- general multi-stage series systems;
- parallel activities;
- mixed series-parallel and arbitrary directed networks;
- shared inputs, shared outputs, and shared resources;
- partial input--output incidence, where not every resource participates in
  every service or process;
- additional/exogenous inputs entering later stages;
- feedback links where the chosen formulation remains computationally
  well-defined;
- multi-plant, multi-activity, and hierarchical systems;
- undesirable intermediates and final bad outputs.

A canonical `NetworkSpec` records nodes, external variables, directed links,
resource pools, topology, node-specific technologies and scale assumptions,
whether node intensities are shared or independent, link-conservation
conditions, and the system aggregation/governance rule. Series, parallel, and
mixed systems can share a graph compiler without becoming the same production
structure.

The source-qualified discovery leaves make several easily blurred structures
explicit. `network.multi_activity.shared_input.beasley_1995` and
`network.multi_activity.multicomponent_shared_input.cook_hababou_tuenter_2000`
allocate resources shared by activities; they do not create a serial
intermediate-product chain. The Cook--Green core-business leaf additionally
permits overlapping product components and asks a specialization question.
The Cook--Chai--Doyle--Green and Cook--Green hierarchical leaves instead
retain unit- and group-level organizational accounts. They must not be
substituted for `reference.group`, which only determines comparison
eligibility. See
[Beasley (1995)](https://doi.org/10.1057/jors.1995.63),
[Cook, Hababou, and Tuenter
(2000)](https://doi.org/10.1023/A:1026598803764),
[Cook et al. (1998)](https://doi.org/10.1023/A:1018625424184), and
[Cook and Green
(2004)](https://doi.org/10.1016/S0377-2217(03)00298-4).

### 6.2 Link and cooperation policies

Intermediate products may be observed and fixed, endogenously allocated, or
only partially observed. System and divisional technologies may be linked
through equality, inequality, or flow-balance conditions.

Evaluation may be:

- cooperative, with a common system objective;
- leader--follower or Stackelberg;
- non-cooperative or game-theoretic;
- relational, with system efficiency related to divisional efficiencies;
- centralized, decentralized, or bargaining-based.

These are governance and accounting assumptions, not interchangeable
numerical tricks.

Running independent DEA models for two departments is a diagnostic baseline,
not network DEA: its targets need not agree on the intermediate product.
Likewise, a shared resource becomes an allocation decision or constraint, not
merely a topology label. Common versus node-specific intensity vectors define
different empirical technologies.

Some basic two-stage CRS formulations become equivalent under restrictive
conditions on intermediates and coupling. Those results are registered with
their domains; they are not extrapolated to arbitrary networks. See
[Cook, Liang, and Zhu (2010)](https://doi.org/10.1016/j.omega.2009.12.001).

The maintained network review also identifies source-qualified leaves that
broad graph labels do not close:

- ordered propagation through hypothetical sub-units,
  the public forward-quantity slice
  `network.sequential.lewis_sexton_2004.forward_radial`
  ([Lewis and Sexton 2004](https://doi.org/10.1016/S0305-0548(03)00095-9));
- sectoral input--output resource conservation,
  `network.input_output.prieto_zofio_2007`
  ([Prieto and Zofío 2007](https://doi.org/10.1016/j.ejor.2006.01.015));
- general series--parallel and parallel relational accounts,
  `network.relational.general.kao_2009` and
  `network.relational.parallel.kao_2012`
  ([Kao 2009](https://doi.org/10.1016/j.ejor.2007.10.008);
  [Kao 2012](https://doi.org/10.1057/jors.2011.16)); and
- source-fixed centralized/non-cooperative authority,
  `network.governance.two_stage.liang_cook_zhu_2008`
  ([Liang, Cook, and Zhu 2008](https://doi.org/10.1002/nav.20308)).

The Lewis--Sexton forward-quantity radial slice is executable; reverse
quantities, mixed accounts, and site-characteristic adjustments remain
source-qualified gaps. The other entries in this list are evidence/planning
records, not frozen executable leaves.
Sequential propagation is not a simultaneous joint-network solver, physical
input--output conservation is not common virtual valuation, and governance
is not graph topology. Older independently fitted two-stage frontiers remain
`network.legacy.independent_two_stage`, a diagnostic neighbor whose
intermediate targets need not form one attainable system plan.

### 6.3 Measures within a network

Network ratio/radial, additive, directional, SBM, EBM, and economic measures
are distinct measure choices over a production graph. The package must expose
system, process, and link performance without guaranteeing a multiplicative
or additive decomposition unless the selected model proves that identity.
Every target returned by a network model must remain feasible under its link
balances and shared-resource rules.
The planned
`network.projection.frontier_validity.chen_cook_kao_zhu_2013` protocol
checks that claim rather than inheriting black-box Pareto completion.
Multiplier-based divisional efficiency and an envelopment-feasible network
projection can disagree under general network structures
([Chen et al. 2013](https://doi.org/10.1016/j.ejor.2012.11.021)); both the
score account and target technology must therefore remain visible.

[Tone and Tsutsui's network SBM](https://doi.org/10.1016/j.ejor.2008.05.027)
is a canonical preset, not the definition of network DEA as a whole.
It keeps one reference-intensity vector per division and coordinates those
plans through the internal links. Its source `fixed` (`non-discretionary`)
policy reproduces the assessed handoff at both ends; its `free`
(`discretionary`) policy lets management redesign the handoff while requiring
the supplying and receiving plans to agree. The source division weights are
exogenous division-importance weights, not link weights. Input-, output-, and
non-oriented objectives share the network technology, but retain different
aggregation identities; the base objectives score external-variable slacks
rather than silently charging link deviations.
The [Färe--Grosskopf network technology](https://doi.org/10.1016/S0038-0121(99)00012-9),
[Kao--Hwang relational two-stage model](https://doi.org/10.1016/j.ejor.2006.11.041),
and [Chen-et-al. additive two-stage decomposition](https://doi.org/10.1016/j.ejor.2008.05.011)
are separate canonical recipes. Their complete combinations of graph,
link/intensity coupling, performance account, and system-to-stage reporting
differ even where a primary CRS system optimum coincides; a common graph,
compiler, or score alone does not make them aliases.

The executable Färe--Grosskopf slice is deliberately narrower than the
original paper's network programme. `network.radial.fare_grosskopf_2000`
represents the basic two-stage intermediate-products system with separate
upstream and downstream intensity vectors, the disposable-link commitment
$Z\lambda\geq Z\mu$, and one orientation-qualified system score. Input and
output radial programmes share that system technology; the output branch
reports its native expansion factor separately from reciprocal efficiency.
CRS is the source-qualified Färe--Grosskopf account. The VRS option adds one
convexity condition to each process plan following the later explicit
polyhedral statement of
[Podinovski and Bouzdine-Chameeva
(2021)](https://doi.org/10.1007/s11123-021-00610-3); it is not presented as
an original Färe--Grosskopf VRS result.

Output orientation is a parameter inside this same system-radial family. The
open Färe--Grosskopf 1995 working paper, published in 1996, gives the two-node
CRS technology, defines the output distance, and states its inverse-distance
maximization programme. The public closed-series output LP is a documented
restriction of that technology rather than an algebraic mirror inferred from
the input code. Its native factor is reported separately from the harmonized
reciprocal efficiency. The VRS option is labelled as composition of that
measure with the separately sourced two-process convex technology, not as an
original Färe--Grosskopf VRS result.

The evaluated organization's observed intermediate vector is not a fixed
condition in this leaf. “Observed once” means that each handoff variable is
stored once and assigned both its supplying and receiving roles; the
benchmark values $Z\lambda$ and $Z\mu$ remain endogenous. The observed value
is reported for comparison and explicitly labelled non-conditioning. If
small coefficients are suppressed from the displayed peer table, external
targets and link accounts still use the complete solution and the omitted
upstream/downstream coefficient sums are disclosed.

Under the matched closed two-stage CRS graph, identical comparison
population, and the same link-disposal rule, this radial envelopment
programme is strictly dual to the primary centralized Kao--Hwang system
programme and has the same optimal system score. The registry records that
identity at the score level. It does not create a whole-method alias:
Färe--Grosskopf reports no stage efficiencies, shared intermediate
multiplier account, multiplicative decomposition, stage-score ranges, or
Lim--Zhu midpoint selection. Equality of one primary optimum is less
information than equality of a complete result contract.

The `network.additive.cook_zhu_bi_yang_2010` leaf is implemented and public
for the source-checked CRS open-DAG domain: open serial processes, branches,
and links that skip an intermediate process. It provides the weighted
system/process account defined by
[Cook, Zhu, Bi, and Yang (2010)](https://doi.org/10.1016/j.ejor.2010.05.006).
General VRS, frontier projections, cyclic networks, inventories, and temporal
carry-overs are not implemented by that leaf and are not implied by its graph
compiler.

The first three closed-chain executable leaves deliberately share the same
two-stage business process without pretending that they answer the same
reporting question. The Färe--Grosskopf radial leaf asks how far the system's
external-resource commitment can contract while final services and internal
flow feasibility are maintained; it stops at the system score and coordinated
plan. The CRS Kao--Hwang relational preset adds a multiplicative
system/process attribution account. The Chen--Cook--Li--Zhu preset returns a
virtual-resource-share-weighted arithmetic account under CRS or VRS and keeps
the upstream and downstream intermediate projections distinct. Kao--Hwang
and Chen share an intermediate multiplier and process-specific reference
intensities, but their objectives, normalizations, decomposition identities,
secondary selection rules, and projection accounts remain separate compilers
and separate canonical methods. The public
`network.sbm.tone_tsutsui_2009` leaf is another distinct mechanism rather
than a spelling of the radial, relational, or additive leaves.
It uses process-specific peer plans and one continuity condition for every
declared handoff. Its four source link roles are kept inside one compiler
without being collapsed into one meaning. Fixed and free links determine
whether the observed handoff is inherited or jointly redesigned and do not
put link deviation in the base score. Equation (26) instead assigns an
incoming-link excess once to the recipient's input account; equation (27)
assigns an outgoing-link shortfall once to the supplier's output account.
Both accountable roles still require the two endpoint peer plans to agree.
The first is input-oriented, the second output-oriented, and no
non-oriented accountable-link formula is inferred from their visual
symmetry. They are catalog specializations of one canonical method and one
public class, not duplicate model families.

Network scale/returns-to-scale and network productivity also require
source-qualified operators. Black-box scale ratios and static Malmquist
indexes do not automatically survive link balances, intermediate products,
shared resources, or process-specific scale assumptions. The registry keeps
topology and measure orthogonal while documenting supported compositions,
rather than manufacturing a separate solver for every Cartesian pairing.
The generic `network.scale_rts` and `network.productivity` records are
non-executable umbrellas until a named identity specifies graph, system and
process technologies, aggregation, reference periods, and reconstruction.
The first equation/oracle-audit candidates are
`network.scale_rts.two_stage.chen_zhu_2019` for Chen--Zhu two-stage scale
efficiency and `network.productivity.two_stage.kao_hwang_2014` for the
Kao--Hwang common-weight global productivity construction. Their
source-qualified graphs and identities, rather than the umbrella names,
determine whether they can become executable.

The physical graph cannot carry every organizational assumption. A planned
typed
`GovernanceSpec(players, authority, objectives, move_order, information,
solution_concept)` assigns players, rights, and information to $C$, and the
objective ordering and solution concept to $P$; $G$ remains the physical
process topology. Centralized, cooperative, leader--follower,
non-cooperative, and bargaining accounts are Level D unless a defining source
proves a conditional identity. The eleven-axis grammar can fingerprint them
only if $P$ records solution concept rather than treating governance as a
graph label. This is a planned semantic component, not code. Evidence:
[Liang, Cook, and Zhu
(2008)](https://doi.org/10.1002/nav.20308) and
[Kao (2014)](https://doi.org/10.1016/j.ejor.2014.02.039).

## 7. Intertemporal production and carry-overs

Dynamic DEA evaluates a production plan whose current actions affect future
productive ability or obligations. It is distinct from:

- running an ordinary static DEA separately in every year; and
- using static period technologies inside a Malmquist index.

Three mature structuring lines are retained:

1. **Färe--Grosskopf intertemporal production/network technology**, where
   temporally linked activities define the multi-period attainable set;
2. **Nemoto--Goto investment and quasi-fixed-factor technology**, where
   investment, adjustment costs, and intertemporal substitution define the
   producer's decision; and
3. **typed carry-over/network dynamic technology**, where capital, inventory, debt,
   knowledge, customer stocks, or liabilities connect adjacent periods in a
   time-expanded production graph, including the Tone--Tsutsui SBM line.

The dynamic compiler describes carry-overs on independent axes:

- **effect**: beneficial, harmful, or neutral for future production;
- **control**: endogenous, fixed, or bounded;
- **balance**: exact, at least, at most, or a declared transition equation;
- lag, decay, initial-condition, and terminal-condition policies.

Historical desirable, undesirable, free, and fixed carry-over labels remain
discoverability presets over these axes. Productive capital, for example, can
be beneficial but fixed in one study and beneficial but endogenously chosen
in another; one label cannot determine both properties. Typical quantities
also include knowledge, inventory, customers, debt, backlog, and
environmental liabilities.

The dynamic compiler additionally includes:

- quasi-fixed inputs and adjustment relationships;
- terminal-value and initial-condition policies;
- period and system weights;
- dynamic network systems with both process links and temporal links.

An `IntertemporalSpec` additionally records lag and transition rules,
investment/adjustment costs, discount rate, perfect-foresight, ex-post,
rolling, or non-anticipative information, and terminal treatment. Numerical
period-importance weights are not called economic discount factors unless the
objective gives them that meaning.

[Tone and Tsutsui's dynamic SBM](https://doi.org/10.1016/j.omega.2009.07.003)
and
[dynamic network SBM](https://doi.org/10.1016/j.omega.2013.04.002)
are important presets. They do not exhaust dynamic production analysis.
The published dynamic-network preset permits each division to use CRS or VRS;
mixed division-level assumptions are admissible, but an overall system RTS
classification is then not identified. Its period and division weights are
nonnegative and sum to one, so a zero weight excludes an account from the
score without removing its feasibility constraints. All four within-period
link cases retain supplier--recipient continuity. A fixed link reproduces the
observed handoff at both ends; a free link selects one endogenous common
handoff; an as-input link adds an input-style slack balance owned by the
recipient; and an as-output link adds an output-style slack balance owned by
the supplier. The last two rules place the scored link term in one process
without disconnecting the feasible plans of the two processes.

The formal published equations have been checked and are internally
inconsistent at the terminal carry-over index: the data definition stops at
$T-1$, while Eq. (9) and the objective notation range through $T$.
Implementations must therefore expose a named boundary resolution rather than
inventing terminal data or presenting one resolution as the uniquely stated
source model.
Window DEA remains a rolling static benchmark and Malmquist remains an index
of repeated static comparisons. Only an explicit carry-over, state, or
transition relationship makes a model dynamic in this production sense.
Dynamic efficiency and productivity operators must retain that state
accounting; they cannot call a repeated-static index “dynamic productivity.”
The generic `dynamic.efficiency` and `dynamic.productivity` records are
likewise non-executable umbrellas; public leaves require a named state-aware
measure and a tested system/period reconstruction rule.

The next planned/evidence candidates are
`dynamic.productivity.malmquist.intertemporal_fare_grosskopf` and, only after
an equation audit,
`dynamic.productivity.malmquist.dynamic_sbm.tone_tsutsui`. They occupy
$G,T,R,A$: the state transition/carry-over technology must be preserved in
every within- and cross-period task, the temporal information set must be
declared, and the productivity identity must reconstruct. They are Level D
relative to window DEA, repeated-static MPI, and a global pooled reference
without state accounting. No implementation is claimed. Evidence anchors are
[Färe and Grosskopf
(1996)](https://doi.org/10.1007/978-94-009-1816-0),
[Färe and Grosskopf
(2010)](https://doi.org/10.1007/978-1-4419-6151-8_5),
[Tone and Tsutsui
(2014)](https://doi.org/10.1002/9781118946688.ch8), and the review by
[Weber (2016)](https://doi.org/10.1093/oxfordhb/9780190226718.013.5).

Four additional source-qualified lines keep repeated-period and dynamic
mechanisms separate:

- `panel.multiperiod_aggregative.park_park_2009` produces one repeated-period
  rating without a state equation and is now implemented as a strict
  two-phase sparse LP with the source example reproduced
  ([Park and Park 2009](https://doi.org/10.1016/j.ejor.2007.11.028));
- `dynamic.optimal_control.sengupta_1999` evaluates a discounted capital path
  under an economic information contract
  ([Sengupta 1999](https://doi.org/10.1016/S0925-5273(98)00244-8));
- `dynamic.scale_rts.sueyoshi_sekitani_2005` studies scale on a
  quasi-fixed-input intertemporal technology
  ([Sueyoshi and Sekitani 2005](https://doi.org/10.1016/j.ejor.2003.08.055));
  and
- `dynamic.weighted_additive.adjustment_cost.aparicio_kapelko_2019` and
  `dynamic.network_lagged_intermediate.chen_2009` respectively retain
  adjustment-cost slacks and lagged intermediate effects
  ([Aparicio and Kapelko 2019](https://doi.org/10.1016/j.ejor.2018.08.045);
  [Chen 2009](https://doi.org/10.1016/j.ejor.2007.12.025)).

None is a switch on the implemented Tone--Tsutsui carry-over presets. The
remaining three lines are planning records, not public methods.

## 8. Technology heterogeneity and comparison across groups

The method universe includes:

- group-specific frontiers;
- meta-frontier and technology-gap ratios;
- meta-frontier directional and slacks-based measures;
- group/meta productivity decompositions;
- common, clustered, latent-class, or hierarchical comparison designs where
  their estimators are explicit;
- non-homogeneous-DMU technologies where some units structurally lack
  particular inputs, outputs, or specializations;
- contextual/conditional frontiers when operating conditions affect the
  attainable set;
- decomposition of managerial performance from technology-set differences
  without giving either component a causal interpretation.

Group definitions may come from institutions or a defensible statistical
design. A meta-frontier result should not be used to conceal incomparable
outputs, different missions, or poor data harmonization.

Three familiar group comparisons answer different management questions.
`heterogeneity.program_efficiency.ccr_1981` asks whether organizations
operating under declared programmes face systematically different
best-practice opportunities after within-programme managerial performance is
separated. `heterogeneity.frontier_difference.global.asmild_2015` compares
the locations of group frontiers through a source-qualified common
construction. `heterogeneity.metafrontier.radial.odonnell_rao_battese_2008`
compares a unit's performance within its own group's opportunity set with its
gap to a broader meta opportunity set. They are not aliases, and none by
itself identifies a causal programme effect. See
[Charnes, Cooper, and Rhodes (1981)](https://doi.org/10.1287/mnsc.27.6.668),
[Asmild (2015)](https://doi.org/10.1007/978-1-4899-7553-9_16), and
[O'Donnell, Rao, and Battese (2008)](https://doi.org/10.1007/s00181-007-0119-4).

The O'Donnell--Rao--Battese radial leaf is now implemented and public for
input or output orientation under matched VRS or CRS group/meta profiles.
Its group assignments remain ex ante. VRS uses a pooled convex
metafrontier and CRS a pooled conic metafrontier; neither is equivalent to a
non-convex union of the separately estimated group hulls. Validation covers
the published scalar checkpoint, an exact analytic example, and an
independently compiled LP. It does not claim reproduction of the paper's
country application, whose observation-level data are unavailable.
Directional, slacks-based, environmental, latent-group, and group/meta
productivity variants remain distinct source-qualified leaves for later
versions.

Partial incidence and non-homogeneous units also address different design
problems. The source-qualified planned leaf
`technology.partial_incidence.imanirad_cook_aviles_zhu_2015`
declares which resources can contribute to which services inside the
represented production system.
The source-qualified planned leaf
`heterogeneity.nonhomogeneous_dmu.cook_etal_2013` asks how to compare
organizations that do not all undertake the same production activities.
Neither is missing-value repair, and neither follows automatically from a
group label or contextual covariate. See
[Imanirad et al. (2015)](https://doi.org/10.1016/j.ejor.2015.02.002) and
[Cook et al. (2013)](https://doi.org/10.1287/opre.2013.1173).

## 9. Statistical foundations, diagnostics, and uncertainty

DEA scores are estimates constructed from a finite sample. The frontier is
especially sensitive to dimensionality, extreme observations, dependence,
and measurement error.

The method map therefore starts by identifying the source of uncertainty
rather than selecting a procedure by name:

| Source or structure | Required distinction |
|---|---|
| sampling uncertainty | variation of a supported frontier estimator under a declared population-sampling design |
| data or measurement uncertainty | error, intervals, imprecision, or fuzzy membership in recorded quantities |
| production risk | feasibility before a state of nature or stochastic production condition is realized |
| robust scenario uncertainty | a guarantee over a declared uncertainty set or scenario family |
| dependence | spatial, serial, clustered, panel, or network relations that change estimation or inference |

Solver tolerances belong to numerical diagnostics and do not represent any of
these sources.

### 9.1 Diagnostics before inference

The base package should support:

- data-domain and dominance diagnostics;
- dimensionality and sample-size warnings without treating rules of thumb as
  proofs;
- influence, leave-one-out, jackknife, peer-count, and reference-set
  diagnostics;
- outlier and leverage sensitivity;
- multiple-optimum and degeneracy diagnostics;
- scale/convexity and model-assumption sensitivity;
- allowable-perturbation and stability-region analysis;
- solver feasibility, residual, and tolerance reporting.

Diagnostics do not license automatic deletion of inconvenient observations.
An extreme frontier unit may be a genuine technical leader or a data error.
Software flags it for domain review and records any exclusion in provenance.
Super-efficiency is useful as one screening statistic; it is not thereby a
universally reliable ranking method.

The first planned source leaf for deterministic sensitivity is
`diagnostics.deterministic_stability.ccr.seiford_zhu_1998`. It belongs to
$A$: it asks which allowable coefficient/data perturbations preserve a CCR
conclusion. It does not introduce a sampling law, so $U$ remains none, and
it is Level D relative to bootstrap inference, robust optimization, and
partial-frontier robustness. This is an evidence record only; see
[Seiford and Zhu
(1998)](https://doi.org/10.1016/S0377-2217(97)00103-3) and the handbook
synthesis by
[Zhu (2010)](https://doi.org/10.1007/978-1-4419-6151-8_3).

Every model also declares a property/compatibility profile covering data
domain, independent unit changes, translation, monotonicity, efficiency
indication, strong-target guarantees, and supported downstream operators.
Unknown compatibility fails closed. The normative contract is
`specs/COMPATIBILITY_MATRIX.md`.

### 9.2 Sampling inference

All procedures in this subsection remain a next-version evidence queue. None
is executable until a source protocol, independent numerical oracle, and typed
result/failure contract have closed for the exact estimator and claim.

The statistical roadmap includes:

- bootstrap bias assessment and confidence intervals for efficiency;
- bootstrap inference for productivity indicators;
- hypothesis tests for returns to scale, convexity, and technology equality;
- valid second-stage truncated-regression procedures under their stated
  data-generating process;
- separability tests used to choose between a common-frontier second stage and
  a conditional opportunity set;
- inference for directional-distance estimators;
- estimator-specific mean-efficiency and productivity asymptotics/CLTs;
- subsampling or other resampling procedures where theory supports the
  measure, dimension, RTS, sampling, and dependence design.

Two planned named tests keep distributional comparison separate from
technology-assumption checking.
`inference.tests.efficiency_distribution.simar_zelenyuk_2006` asks whether
declared groups have the same efficiency-score distribution under the
source's weighting and dependence conditions; it is not an informal
comparison of sample means.
`inference.tests.technology_structure.kneip_simar_wilson_2016` tests
supported restrictions such as convexity, returns to scale, or group
structure for the specified frontier estimator. It is not a generic bootstrap
switch that can validate any fitted model. See
[Simar and Zelenyuk (2006)](https://doi.org/10.1080/07474930600972582) and
[Kneip, Simar, and Wilson (2016)](https://doi.org/10.1080/07350015.2015.1049747).

Naive OLS or Tobit regression on bounded DEA scores is not a default
inferential workflow. Likewise, naive row-resampling does not become a valid
frontier bootstrap merely because the DEA programme is solved many times.
Boundary-compatible smoothing, subsampling, or another justified
data-generating procedure is required. Foundational references include
[Simar and Wilson (1998)](https://doi.org/10.1287/mnsc.44.1.49),
[Simar and Wilson (2000)](https://doi.org/10.1023/A:1007864806704), and
[Kneip, Simar, and Wilson (2008)](https://doi.org/10.1017/S0266466608080651).

The inference registry is measure-specific. It records whether theory supports
bias/interval estimation for the fitted static measure, productivity index,
directional distance, or structural test. A generic resampling API cannot
confer validity on an arbitrary model composition.

The initial source-qualified leaves distinguish the Simar--Wilson (1998)
static-frontier bootstrap, the Simar--Wilson (1999) Malmquist bootstrap, and
the Simar--Wilson (2002) returns-to-scale test. Their data-generating
processes, task structures, and permitted statements are not interchangeable.
Directional-distance inference is another source-qualified leaf rather than
an automatic reuse of the radial bootstrap; its initial registry source is
[Simar, Vanhems, and Wilson (2012)](https://doi.org/10.1016/j.ejor.2012.02.030)
and its canonical ID is
`inference.bootstrap.directional_distance.simar_vanhems_wilson_2012`.

Modern productivity inference also requires source-specific leaves rather
than extending the 1999 bootstrap name. Planned/evidence candidates include
`inference.productivity.aggregate.pham_simar_zelenyuk_2023` and a
source-frozen finite-sample/CLT leaf after auditing Zelenyuk--Zhao (2025).
They occupy $A/U$ and must bind the exact productivity operator,
aggregation weights, frontier estimator, panel DGP, and dependence design.
They are Level D relative to individual-index smoothed bootstrap and
deterministic aggregation. No executable procedure is claimed. See
[Pham, Simar, and Zelenyuk
(2023)](https://doi.org/10.1287/opre.2022.2424) and
[Zelenyuk and Zhao
(2025)](https://doi.org/10.1017/S1365100525000094).

### 9.3 External operating conditions

Two widely used approaches answer different questions:

- A Simar--Wilson second stage retains a common production technology and,
  under separability, models how external conditions are associated with the
  inefficiency distribution. Its truncated-regression/bootstrap procedure is
  not ordinary OLS/Tobit and does not establish causal effects. The 2007
  Algorithm 1 and Algorithm 2 are distinct recipes because Algorithm 2 adds
  the source-qualified first-stage bias-correction bootstrap.
- Conditional DEA/FDH permits case mix, geography, regulation, or other
  conditions to alter the attainable production opportunities. Kernel or
  nearest-neighbor choices and bandwidth selection are part of the estimator.
- The Fried et al. three-stage procedure first estimates DEA slacks, then uses
  a parametric stochastic-frontier model to divide them into operating
  environment, managerial inefficiency, and noise, adjusts the production
  observations, and finally refits DEA. It therefore changes the data used to
  construct the final frontier.

An efficiency estimate may also be used as an outcome in a policy,
treatment, or difference-in-differences study. That is an external
identification design, not another spelling of two-stage DEA. The causal
estimand, treatment timing, support/overlap, interference assumptions,
counterfactual benchmark construction, and uncertainty from the generated
efficiency outcome must all be declared. A before/after score difference,
conditional association, or significant second-stage coefficient does not by
itself identify a treatment effect. Joint conditional-counterfactual frontier
estimators remain research-only until a source-specific identification and
validation contract is frozen.

The assumption-specific OLS consistency result of
[Banker and Natarajan (2008)](https://doi.org/10.1287/opre.1070.0460)
is retained as the separate
`context.second_stage.banker_natarajan_2008.ols` lineage. It is neither a
generic endorsement of OLS on bounded scores nor an alias for Simar--Wilson,
conditional frontiers, or descriptive fractional-response regression. Its
error, separability, functional-form, and sampling conditions must accompany
any executable recipe.

The recommended empirical sequence is to ask whether the operating condition
changes the opportunity set. If separability is rejected, regressing
unconditional DEA scores does not repair the benchmark; a conditional
technology is required. Core references include
[Cazals, Florens, and Simar (2002)](https://doi.org/10.1016/S0304-4076(01)00080-X),
[Daraio and Simar (2005)](https://doi.org/10.1007/s11123-005-3042-8), and
[Simar and Wilson (2007)](https://doi.org/10.1016/j.jeconom.2005.07.009).

The [Fried et al. (2002)](https://doi.org/10.1023/A:1013548723393)
three-stage procedure remains a source-qualified hybrid extension with strong
distributional and data-adjustment assumptions. It is not a Simar--Wilson
second stage, a conditional frontier, or a generic remedy for environmental
heterogeneity and noise. Results must preserve both the original and adjusted
observations and report the fitted stochastic-frontier assumptions.

### 9.4 Robust and partial frontiers

The package scope includes:

- order-$m$ expected-max frontiers;
- order-$\alpha$ quantile/frontier constructions;
- conditional efficiency and separability assessment;
- robust order-$m$ and conditional partial frontiers;
- outlier-resistant and contamination-aware procedures with named
  assumptions.

These are distinct estimators, not “robust standard errors” for ordinary DEA.
Order-$m$ asks for expected best performance in a random comparison group of
size $m$; order-$\alpha$ uses a dominance-probability boundary. They require
separate sensitivity curves and must not be relabeled as generic quantile
regression. Neither estimator is guaranteed to withstand every contamination
pattern. The registered starting points are `estimator.partial.order_m`,
following
[Cazals, Florens, and Simar (2002)](https://doi.org/10.1016/S0304-4076(01)00080-X),
and `estimator.partial.order_alpha.aragon_daouia_thomas_agnan_2005`,
following
[Aragon, Daouia, and Thomas-Agnan (2005)](https://doi.org/10.1017/S0266466605050206).

### 9.5 Uncertain observations and technologies

Named extensions include:

- state-contingent and event-specific production;
- chance-constrained DEA;
- stochastic-deviation, measurement-error, and stochastic-PPS families;
- robust-optimization counterparts with explicit uncertainty sets;
- interval/IDEA formulations for bounds, order, and ratio information;
- fuzzy DEA and possibility/credibility or membership formulations;
- distributionally robust approaches once definitions and validation cases
  are mature.

The uncertainty representation, probability or membership assumptions,
robustness budget, and resulting score semantics must be part of the public
specification.

These families make different statements:

- state-contingent production treats output delivered in different states of
  nature as different commitments in an ex ante production plan;
- chance-constrained DEA needs a probability model and risk tolerance;
- stochastic-deviation, measurement-error, and stochastic-PPS models attach
  randomness to different parts of the production account and cannot share
  one generic score interpretation;
- interval/IDEA reports the implications of incomplete bounded information;
- fuzzy DEA reports membership or possibility, not frequency confidence;
- robust-optimization DEA protects feasibility/performance over a declared
  uncertainty set and reports the price of robustness;
- Bayesian DEA, retained as an experimental advanced family, requires an
  explicit likelihood, prior, posterior target, and computation diagnostics.

For the default LP backend, box, polyhedral, and budgeted uncertainty sets are
the natural first robust formulations. Ellipsoidal sets generally require a
conic backend and cannot be advertised as base-HiGHS models.

### 9.6 State-contingent and event-specific production

State-contingent technology addresses production risk rather than statistical
sampling variation. Managers commit resources before nature selects a state,
and the commodity description records what can be delivered in each state.
The technology can be defined without probabilities; beliefs and risk
preferences enter a later economic-choice layer. This state of nature is also
not a dynamic state variable, stock, or carry-over.

An event-specific DEA construction uses an observed random condition to
partition the state space and estimate locally relevant opportunities. It
must remain distinct from a full vector of elicited ex ante state-contingent
outputs. Defining sources include
[Chambers, Hailu, and Quiggin (2011)](https://doi.org/10.1111/j.1467-8489.2010.00517.x)
and the technical/environmental DEA construction of
[Serra, Chambers, and Oude Lansink (2014)](https://doi.org/10.1016/j.ejor.2013.12.037).
These families remain advanced planned scope until their state definitions,
data requirements, and numerical oracles have been audited.

### 9.7 Spatial mechanisms

“Spatial DEA” is not one method. Geography can:

- restrict the comparison population to defensible local peers;
- condition the attainable frontier through local operating circumstances;
- create a physical or knowledge spillover in which neighboring activity
  enters the production system;
- induce spatial dependence that changes sampling inference; or
- define a location or accessibility decision rather than a production
  efficiency question.

The local-peer proposal of
[Vidoli and Canello (2016)](https://doi.org/10.1016/j.ejor.2015.10.050)
and the spatially conditioned frontier of
[Ramajo, Márquez, and Hewings (2024)](https://doi.org/10.1111/grow.12711)
already occupy different layers. A cross-unit production spillover would
require an explicit graph or coupling technology, while a spatial bootstrap
requires estimator-specific dependence theory. The comprehensive atlas
records these branches now; executable leaves remain source-qualified
advanced extensions.

### 9.8 Known groups versus statistical context

Meta-frontier analysis uses substantively known technology groups and asks
separately about performance within a group's opportunities and the gap
between group and cross-group opportunities. It is not conditional DEA or a
pooled-score regression.

Group and meta technologies must share economically comparable variable
definitions and units. Radial technology-gap identities do not transfer
mechanically to non-radial targets; nestedness and the direction of every
reported ratio are validated explicitly.

Unknown latent technology classes ordinarily require mixture or latent-class
statistical models and sit outside the DEA core unless a specific
non-parametric estimator is registered.

## 10. Decision support beyond retrospective scoring

Decision support is future scope. Four managerial questions organize the
source-qualified candidate leaves; they do not collapse into one permissive
planning estimator:

| Mother question | Decision question |
|---|---|
| maintained-performance planning / inverse DEA | how must selected inputs or outputs change while a declared base-performance condition is retained? |
| centralized resource planning | how should a legitimate central authority allocate controllable resources or commitments across related units under a declared system objective? |
| fixed-total interdependence / ZSG | how does one unit's gain alter what remains jointly feasible for every other unit when an aggregate quantity is conserved? |
| organizational recombination / merger analysis | what production potential is attainable after a declared change in organizational boundaries? |

Fixed-cost allocation is a distinct documentation leaf adjacent to
centralized planning because assigning a common overhead under fairness
principles is not the same production decision as reallocating controllable
resources. Bargaining and target-selection rules are normative
solution-concept or preference overlays on a declared feasible set. Scenario
analysis is a provenance and task-orchestration layer over source-qualified
estimators, not a generic DEA forecasting model. None of these overlays
creates an additional DEA technology mother model.

The broad families receive named, source-qualified leaves rather than one
permissive planning solver:

- `decision.inverse_dea.wei_zhang_zhang_2000` asks which selected quantities
  may change while a declared efficiency condition is maintained
  ([Wei, Zhang, and Zhang](https://doi.org/10.1016/S0377-2217(99)00007-7));
- `decision.central_allocation.lozano_villa_2004` coordinates resources and
  targets across related units under an explicit system objective and
  conservation rules
  ([Lozano and Villa](https://doi.org/10.1023/B:PROD.0000034748.22820.33));
- `decision.fixed_cost_allocation.cook_kress_1999` characterizes shared-cost
  allocations under efficiency-invariance and Pareto-minimality principles
  ([Cook and Kress](https://doi.org/10.1016/S0377-2217(98)00337-3));
- `decision.fixed_cost_allocation.beasley_2003` and
  `decision.fixed_cost_allocation.cook_zhu_2005` define distinct operational
  allocation procedures rather than optional tie breakers on Cook--Kress
  ([Beasley](https://doi.org/10.1016/S0377-2217(02)00244-8);
  [Cook and Zhu](https://doi.org/10.1016/j.cor.2004.02.007));
- `decision.fixed_sum_zsg.lins_etal_2003` represents settings in which an
  allocation gain for one unit changes what remains feasible for the others
  ([Lins et al.](https://doi.org/10.1016/S0377-2217(02)00687-2));
- `decision.merger_restructuring.bogetoft_wang_2005` evaluates attainable
  gains under declared pre- and post-combination technologies
  ([Bogetoft and Wang](https://doi.org/10.1007/s11123-005-1326-7)); and
- `decision.bargaining.targets.lozano_hinojosa_marmol_2019` selects one
  attainable target under a named bargaining solution rather than hiding
  variable priorities in an arbitrary weighted objective
  ([Lozano, Hinojosa, and Mármol](https://doi.org/10.1016/j.omega.2018.05.015)).

These leaves are all deferred to the next version. The current release adds
no decision API and the current Handbook adds no decision-support chapter.
Their maintained-efficiency rule, system objective,
resource conservation, fairness principle, bargaining solution, or
post-merger technology is part of the method rather than an interchangeable
option. In particular, DEAPack will not expose a generic `Planner`, an
unrestricted planning DSL, or a switchboard estimator that presents these
different authority and value contracts as options of one model. The
maintained source records are in
the repository's
[decision-support review](https://github.com/daopingw/DEAPack/blob/main/specs/reviews/DECISION_SUPPORT.md).

Prescriptive outputs require feasibility and value judgements beyond ordinary
relative-efficiency scoring. They must be labeled as scenario results rather
than causal forecasts.

## 11. Cross-cutting result presentation

Visualization and reporting are not a separate theoretical model family, but
they are part of every empirical workflow. The common result contract must
support:

- score distributions and benchmark tiers;
- observed-versus-target resource and outcome profiles;
- slack and contribution decompositions;
- peer/reference networks;
- scale and congestion diagnostics;
- productivity components and benchmark vintages;
- process and carry-over diagrams for network/dynamic studies;
- environmental trade-off and assumption-sensitivity displays;
- confidence intervals, influence, and robustness displays;
- publication-quality tables with exact assumption footnotes.

Plots must preserve the native meaning of the measure. A DDF value is not
silently plotted as a percentage, a Malmquist ratio is not labeled an
efficiency score, and a model-derived shadow price is not labeled a market
price.

<!-- BOOK-READER-EXCERPT-END -->

## 12. Coverage tiers

“Comprehensive” is implemented in dependency order rather than as an
unverifiable big-bang release.

The tiers describe dependency and intended delivery, not evidence maturity.
Within any tier, a branch is reader-facing **implemented** only when an exact
public leaf exists, **planned** when a source-qualified implementation route
is committed, and **research-only** when the branch belongs in the atlas but
its executable identity, backend, or validation strategy is not yet stable.
Internal prototypes remain planned from a user's perspective. Source evidence
and numerical-oracle status are reported independently.

### Tier 0 — implemented common foundation

- validated cross-sectional/panel data;
- convex CRS/VRS/NIRS/NDRS reference technologies;
- radial input/output DEA;
- non-convex radial input/output FDH;
- non-convex input/output FCH for nonempty binary coordination of distinct
  observed operating templates, with certified mixed-integer solutions and
  explicit coalitions;
- non-convex input/output FRH for integer replication of complete observed
  operating modules, with certified MILP solutions and explicit replication
  plans;
- additive and RAM;
- Tone input-, output-, and non-oriented SBM on the standard positive domain,
  including the exact `InputRussell`, `OutputRussell`, and `ERG`
  discoverability aliases;
- directional distance;
- Chavas--Cox generalized distance under CRS/VRS;
- radial scale efficiency, selected-projection Banker--Thrall local RTS, and
  matched radial VRS scale elasticity;
- common sparse HiGHS-backed results.

The fixed-mix Banker MPSS and Färe--Grosskopf--Kokkelenberg physical-capacity
reconstructions are deliberately excluded from Tier 0. They remain non-public
prototypes with `deferred_to_next_version` status until their defining-source
equations and independent numerical oracles are frozen.

### Tier 1 — implemented environmental and productivity foundation

- price-informed cost and revenue efficiency with matched radial
  technical--allocative decompositions;
- return-to-dollar profitability and the matched Chavas--Cox
  technical--scale--allocative decomposition;
- strong-disposal and bad-output directional-equality environmental DDF formulations,
  with the latter's relationship to named weak-disposal technologies still
  under audit, plus an explicit null-jointness option;
- undesirable-output SBM;
- by-production directional and FGL-style measures;
- Coelli-style material-inflow environmental analysis;
- Malmquist, Luenberger, global and biennial Malmquist, plus the public
  Bjurek Hicks--Moorsteen quantity-index account;
- standard and APZ Malmquist--Luenberger, plus global environmental
  productivity.
- the declared-group O'Donnell--Rao--Battese radial metafrontier account under
  matched CRS/VRS and input/output profiles, with MTR/TGR interpreted as
  opportunity proximity rather than managerial efficiency.

### Tier 2 — first comprehensive release

- remaining graph/original Russell and ERGM-related leaves outside the exact
  positive-data SBM equivalence domain, Enhanced BAM and
  alternative bound scopes, EBM, and the remaining hyperbolic/path and
  economic measures;
- non-convex FDH scale extrapolation and bounded-replication variants of the
  implemented unbounded FRH technology; remaining scale/RTS analyses such as
  directional scale elasticity; remaining economic and environmental
  capacity leaves, congestion, shadow-price, ranking, target, and
  weight-restriction analyses;
- variable-selection reporting, deterministic stability, compatibility
  checks, and efficient-facet diagnostics;
- special/non-discretionary data formulations;
- remaining environmental sensitivity models;
- Luenberger--Hicks--Moorsteen, Färe--Primont, sequential/window and
  meta-frontier productivity;
- cross-sectional TFP efficiency and technical/scale/mix decomposition;
- source-qualified Malmquist decompositions, non-radial/SBM productivity, and
  biennial environmental productivity;
- industry aggregation and reallocation decompositions;
- remaining source-qualified series, parallel, general-network, and dynamic
  leaves beyond the implemented Kao--Hwang, Chen, Cook, Tone--Tsutsui, and
  dynamic-SBM vertical slices;
- network scale/productivity and dynamic efficiency/productivity operators;
- remaining source-qualified metafrontier leaves beyond the implemented
  declared-group radial account, including non-radial, environmental,
  nonconvex-union, latent-group, and group/meta productivity formulations;
- diagnostics, bootstrap, conditional, the source-qualified Fried
  three-stage workflow, order-$m$, and order-$\alpha$;
- stable publication reporting and visualization.

### Tier 3 — advanced official extensions

- alternative or advanced dynamic-network systems and complex hierarchical
  systems;
- non-homogeneous-DMU, partial-incidence, and advanced facet technologies;
- state-contingent/event-specific and source-qualified spatial-frontier
  technologies;
- interval, imprecise, fuzzy, chance-constrained, stochastic, and robust DEA;
- experimental Bayesian DEA with explicit posterior semantics;
- pessimistic, worst-practice, and double-frontier ranking procedures;
- environmental-standard simulation and emissions-permit allocation;
- inverse, centralized, fixed-sum, game, merger, and scenario models;
- specialist mixed-integer and non-linear variants;
- optional high-performance and commercial solver backends.

Methods in later tiers remain part of the architecture now. Their code is
added only after lower-level compilers, reference rules, result semantics,
tests, and teaching examples are stable.

## 13. Where DEA ends

The book compares DEA with neighboring frontier estimators, while the package
does not silently relabel them:

- SFA estimates a parameterized frontier with a composed noise/inefficiency
  error;
- a sign-constrained nonparametric least-squares (SCNLS) construction is an
  exact representation of DEA only under the matched one-sided sign, shape,
  graph, and loss conditions proved by
  [Kuosmanen and Johnson (2010)](https://doi.org/10.1287/opre.1090.0722);
- ordinary CNLS estimates a shape-constrained conditional function through a
  regression loss, and relaxing the DEA-equivalent sign restriction or using
  two-sided residuals changes the estimator
  ([Kuosmanen 2008](https://doi.org/10.1111/j.1368-423X.2008.00239.x));
- convex quantile regression (CQR) and convex expectile regression (CER)
  target conditional quantiles or expectiles through different loss
  functions; they are not order-$\alpha$ partial-frontier or conditional
  DEA aliases
  ([Dai et al. 2023](https://doi.org/10.1016/j.ejor.2023.04.004));
- StoNED combines shape constraints with a stochastic composed-error
  decomposition;
- Bayesian shape-constrained or stochastic frontiers use a likelihood and
  posterior production function.

They may later share a result-adapter protocol for comparison and plotting,
but they are not DEAPack DEA aliases.

## 14. Known naming traps

The following statements are prohibited in code, book, or documentation:

- “CCR and BCC require separate model engines.”
- “Input and output orientation are different production technologies.”
- “Network DEA is one model.”
- “Two-stage regression and two-stage production DEA are related because both
  contain two stages.”
- “Dynamic DEA is a Malmquist index.”
- “All undesirable-output DEA models are sign variants of one programme.”
- “SBM is DDF under another name.”
- “A global index merely changes a plotting baseline.”
- “All eligible cross-sectional observations and a global temporal technology
  are the same reference concept.”
- “A pessimistic ranking frontier is a robust worst-case uncertainty model.”
- “A state of nature is a dynamic carry-over state.”
- “Spatial peers, spatial conditioning, production spillovers, and spatial
  inference are one spatial DEA option.”
- “An environmental regulation flag identifies whether a standard, price,
  allocation rule, operating condition, or causal intervention is intended.”
- “Bootstrap DEA is ordinary DEA repeated many times without an inferential
  design.”
- “Robust DEA, robust order-$m$, and outlier diagnostics mean the same thing.”
- “A common solver matrix makes two measures economically equivalent.”

## 15. Audit questions for every newly proposed model

Before adding a public model or alias, the contributor must answer:

1. What economic or managerial question does it answer?
2. What production-system graph does it assume?
3. What are the economic roles and domains of all variables?
4. Which technology axioms define attainable best practice?
5. Which organizations form the comparison population, which periods form the
   temporal information set, and which evaluation exclusions apply?
6. What improvement plan, aggregator, or price objective defines the measure?
7. What native value does it report, and how should improvement be read?
8. Is it an alias, preset, variant, or genuinely new family under the
   equivalence policy?
9. Which original paper and review establish the formulation?
10. Which published numerical example, invariance property, and failure case
    validate the implementation?
11. Is uncertainty due to sampling, data measurement, production risk, a
    robust scenario set, or dependence, and what identification and
    dimensionality limitations apply?
12. Which result components and plots are substantively meaningful?

If these questions cannot be answered, the method stays in the research
backlog rather than entering the public API.
