# DEAPack

DEAPack is being rebuilt as a comprehensive Python toolkit for DEA-based
efficiency, productivity, and environmental-performance analysis.

Version `2.0.0rc1` is the feature-frozen candidate for the first public
release of the redesigned 2.x line. It is a pre-release, not yet a stable
compatibility promise. The historical `0.1.x` source remains in `DEAPack/`
for audit and migration work, but it does not define the new architecture. The
[`legacy audit`](specs/LEGACY_AUDIT.md) records which DEAPack and ProdPack
ideas, data, and behaviors are retained, redesigned, or intentionally rejected.
The package Documentation's
[`migration guide`](docs/getting-started/migration.md) turns that audit into a
manual study-level workflow; the 2.x wheel does not install an uppercase
`DEAPack` forwarding package.

Maintainers can review the candidate's technical status, bilingual publication
work, rights decisions, and external release sequence in the
[`2.0.0rc1 review packet`](RELEASE_REVIEW_2.0.0rc1.md). No local preflight in
that record is presented as evidence of a public tag or hosted release.

## Project scope

DEAPack is developed as three coordinated products:

- a composable numerical package;
- the bilingual English--Chinese book *Data Envelopment Analysis: Efficiency,
  Productivity, and Environmental Performance with Python*, presented as *A
  Unified Handbook of Theory, Methods, and Practice*; English remains the
  canonical source while the Chinese edition is edited as idiomatic Chinese
  scholarly prose through Sphinx gettext catalogs;
- English user, model, API, and developer Documentation for the first public
  release.

They share the notation, model registry, result contract, datasets, and tested
examples in [`specs/`](specs/). See [`ROADMAP.md`](ROADMAP.md) for the staged
implementation plan. The
[`method universe`](specs/METHOD_UNIVERSE.md) reviews the field-wide scope,
while the [`unified framework`](specs/UNIFIED_FRAMEWORK.md) explains how
historical names become compositions rather than duplicate solver classes.
The [book architecture](specs/BOOK_ARCHITECTURE.md) applies a separate
handbook admission gate: public package coverage can include source-exact
specializations, while the book admits only independent, field-level,
transferable mechanisms. Paper-specific directions, weights, normalizations,
and industry accounts remain in package Documentation instead of becoming
extra chapters or appendices.
Nine maintained [`literature reviews`](specs/reviews/INDEX.md), currently
containing 148 evidence cards, turn that scope into an auditable programme
with source, numerical-oracle, package, and book mappings.
The
[`compatibility contract`](specs/COMPATIBILITY_MATRIX.md) prevents
unsupported data, technology, measure, and inference combinations from
becoming silent defaults.
The [contribution guide](CONTRIBUTING.md) applies the same source-first
evidence gate to proposed methods, while the
[benchmark contract](benchmarks/README.md) separates computational evidence
from defining literature and independent numerical oracles.

Suggestions are welcome even without an implementation. Readers and
researchers can propose a model, report a numerical discrepancy, contribute
code or a dataset, add a case or visualization, improve Documentation, or
refine the Chinese Handbook translation through the repository's structured
issue and pull-request routes.

## Development quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
make test PYTHON=.venv/bin/python
```

The runnable kernel implements convex input/output radial DEA, non-convex
input/output FDH, binary-subset input/output FCH, integer-replication
input/output FRH,
additive/weighted additive DEA, RAM, BAM, input- and output-oriented SBM,
non-oriented ERG/SBM, a source-qualified input-oriented CRS EBM evaluator
with mandatory declared calibration, directional distance, the VRS
Portela--Thanassoulis--Simpson range directional measure for signed accounts,
environmental DDF, separable and Tone-style non-separable undesirable-output SBM,
the source-reproduced fixed-direction CRS by-production DDF, the distinct
source-reproduced CRS modified by-production FGL measure, and Coelli-style
material-inflow environmental efficiency. The core by-production DDF now
certifies its intended-production and residual-generation accounts separately,
then releases their joint score, directional target, thresholded peer systems,
and original-unit marginals without adding a solver call; the smaller component
is a direction-specific limiting account, not an inferred physical bottleneck.
Kalhor--Kazemi Matin's activity-specific
weak-disposal input-radial leaf adds environmental performance across a
general process network, including final and internal desirable and
undesirable product accounts. Separately, the common-factor DDF and Kuosmanen
VRS activity-specific DDF keep a certified native distance separate from
membership of an external reference technology: a conditional beta-zero
feasibility task gates only the bounded efficiency display and classification.
The separable environmental SBM uses normalized, row-scaled
balances with independent score, target, peer, dual, and external-membership
release gates. The generic environmental DDF, common-factor weak-disposal
DDF, Chung--Färe--Grosskopf DDF, and separable undesirable-output SBM also
accept the same source-neutral `PeerEligibility` declaration as the classical
core. In each case, the declared candidate population intersects the base
reference policy without changing that model's production or disposal
account. A first price-informed layer adds CRS/VRS
minimum-cost efficiency and a matched input-radial
technical--allocative--cost decomposition, with prices kept in a separate,
name- and key-aligned immutable data contract. The same layer now includes
CRS/VRS maximum-revenue efficiency and a matched output-radial
technical--allocative--revenue decomposition, verified against two public
numerical oracles with both equal and unequal output prices. VRS
maximum-profit analysis retains the raw monetary gap without inventing a
profit ratio, and the CCF-1998 Nerlovian model decomposes the price-normalized
gap into directional technical and allocative components. Both reproduce a
fixed public eight-unit cross-implementation oracle and keep profit-maximizing
and operating-improvement plans distinct. Direct cost, revenue, and profit
results now require solver-neutral LP and reconstructed price-account
certificates before releasing scores or semantic tables; score, target, peer,
and dual claims fail closed independently without adding solver calls or
post-certification rounding. The ordinary DDF applies the same trust boundary
to its row-scaled primary programme and optional target completion: native
distance, target, thresholded-peer, and complete-dual claims have explicit
validity, and Nerlovian decomposition accepts only a certified directional
component. Return-to-dollar profitability now
adds a solver-free exact extreme-ratio kernel for CRS/VRS, an unclipped
external-reference contract, and feasible scale-explicit targets. The public
Chavas--Cox generalized-distance model expresses one proportional performance
gap through resource saving, service growth, or both, using exact radial
reductions
for its endpoints and every CRS bearing and a certified LP-feasibility search
for interior VRS bearings. Its matched profitability operator decomposes
return-to-dollar efficiency into CRS/VRS technical, scale, and allocative
components while keeping value-maximizing and technical targets separate.
Both reproduce the fixed Zofío--Prieto five-unit oracle. The productivity
layer now adds a configurable adjacent-period radial Malmquist kernel and a
named `FGNZMalmquistProductivityIndex` preset for the source-qualified
output-oriented CRS efficiency-change/technical-change core. Input-oriented
and non-CRS runs remain explicitly labelled sensitivity paths. The distinct
`FGNZEnhancedMalmquistProductivityIndex` adds exactly two own-period VRS
tasks to the four-task CRS headline and reports pure-efficiency change plus
FGNZ's own-period scale-efficiency change. Its independent exact oracle is
strictly positive and matched; tested partial-zero cells with positive row
aggregates and explicit unbalanced `drop`/`raise` handling are package
extensions, and the original OECD/PWT5 application is not reproduced. The
distinct `RayDesliMalmquistProductivityIndex`
uses four CRS and four VRS distance tasks to allocate the same headline index
among pure-efficiency change, VRS opportunity change, and Ray--Desli's
cross-period scale factor. Its public scope is deliberately narrow: a
balanced, strictly positive panel with one or more inputs and exactly one
desirable output. If a cross-period VRS task is infeasible, the valid CRS
index and own-period pure-efficiency factor remain available rather than
being imputed or discarded. The layer also includes the additive Luenberger
indicator. Its four signed directional-distance programmes and complete
$L=EC_L+TC_L$ account now pass a no-extra-solve, solver-neutral release gate;
one failed task withholds the whole affected transition while preserving raw
diagnostics. The same layer includes the circular Global Malmquist index with
efficiency-change/best-practice-change decomposition. Adjacent comparisons
remain the default, while every forward period pair or an explicit ordered
subset can be reported from the same fixed sample vintage without multiplying
the cached distance-solve count.
The pair-pooled Biennial Malmquist index adds history-stable adjacent
comparisons without cross-period radial programs. Source-qualified
Chung--Färe--Grosskopf Malmquist--Luenberger and Oh Global
Malmquist--Luenberger analyses extend the same panel architecture to desirable
and undesirable outputs using a fixed CRS common-factor weak-disposal
technology. Every environmental distance now passes a row-scaled,
solver-neutral LP and source-production account gate; all four tasks and the
complete ML or GML multiplicative account must certify before a transition is
released. Thresholded peers remain a separate claim, and the checks reuse the
returned solutions without adding solver calls. The CFG index has independent analytical closure of all four
environmental distance roles through exact pure-frontier-shift and
pure-catch-up panels, including a negative cross-period distance. This is not
a reproduction of the published Swedish industry averages; that empirical
branch remains `deferred_to_next_version`. The public
`APZMalmquistLuenbergerProductivityIndex` preset answers the separate APZ
consistency question by combining the 2017 capped-bad-output inequality
technology with the standard four-distance ML account. Its technical
Documentation path uses the shared solver gate but reconstructs its own
bad-output inequality and contemporaneous cap; this does not promote APZ into
the handbook's core route. It fixes CRS, the
target observation's $(0,y,-b)$ programme, strictly positive inputs and bad
outputs, and a componentwise bad-output maximum calculated separately from
each reference period. Its production-free exact oracle gives
$EC=77/80$, $TC=8/7$, and $ML=11/10$ on the 2013 Table 1 fixture and proves
that the result is neither CFG post-processing nor Oh GML. APZ can still have
infeasible cross-period tasks, and the 2017 WIOD application is not
reproduced. Its canonical preset ID is
`productivity.malmquist_luenberger.aparicio_pastor_zofio_2013`; the shorter
`.apz` spelling is only a discovery alias. Oh's GML leaf separately uses four self-contained
own-period/global distances, which are nonnegative by self-inclusion, and one
retrospective pooled CRS conical envelope.
Independent two- and three-period accounts verify $GML=EC\times BPC$, the
source-native $BPG^r=(1+D^r)/(1+D^G)\in(0,1]$, and circularity within one
fixed sample vintage. Adjacent, all-forward-pair, and explicitly selected
forward-pair reports reuse the same fixed-vintage distance cache; a
literal-union estimator, alternate technologies or directions, and the
unsupplied 26-country application replay remain
`deferred_to_next_version`. Broader configurable environmental
productivity operators remain private and `deferred_to_next_version` until a
defining source and independent validation cover their full parameter domains;
changed configurations must not borrow the classic names. The Bjurek
Hicks--Moorsteen index adds a complete bilateral
quantity account: it estimates both output-quantity and input-quantity
change from eight source-defined distance tasks and reports total-factor
productivity change as their ratio. It remains distinct from the ordinary
one-orientation Malmquist index and does not import that index's
decomposition. These models and analyses share independent panel
reference-set builders, compiled period technologies, deduplicated distance
tasks, and sparse HiGHS programs.

The public EBM leaf is deliberately conditional rather than automatic.
`InputOrientedEpsilonBasedDEA` evaluates Tone--Tsutsui's input-oriented CRS
programme only after the analyst supplies an immutable
`DeclaredEBMCalibration` containing epsilon, normalized name-keyed input
weights, and auditable ownership, population, source, and validity-period
provenance. It compiles one sparse full-sample technology and solves one LP per
organization. Automatic affinity/PCA calibration, alternate orientations or
returns to scale, panels, external references, and undesirable outputs remain
separate next-version evidence tasks.

The classic multiplicative DEA family is also public in the development tree.
One shared sparse log-space compiler preserves two source-defined economic
accounts instead of treating their similar names as interchangeable: the 1982
C2S2 log-conic model requires every input and output to exceed one and is not
unit invariant, whereas the 1983 free-intercept log-convex model accepts
strictly positive data and is unit invariant. Both expose their source-native
exponent-floor guarantees. An independent dense source-form oracle checks
scores, targets, peers, floor power, and the contrasting unit behavior; the
classical-foundations benchmark covers compilation and solution. A dedicated
English book chapter, package documentation, and deterministic explanatory
figure use the same notation and public estimators. This is included in the
feature-frozen `2.0.0rc1` candidate. The candidate is not a stable release and
acquires no release claim until its clean-tag gates pass.

The direct additive family now carries its own claim-scoped analytical
certificate. Charnes et al.'s classic identity is limited to VRS, effective
unit slack weights, a self-inclusive cross-section, and ordinary nonnegative
inputs/desirable outputs. A source-displayed two-DMU shortfall and an
independently compiled four-DMU case close exact scores, slacks, strong
status, targets, and peers without claiming a published numerical-table
reproduction. Fixed positive weights, CRS/NIRS/NDRS, and panel or non-global
reference policies remain configurable DEAPack extensions without that
historical identity. VRS balances are reference-anchored before row scaling, so coherent
unit/weight changes and translations cannot silently erase a material slack.
Explicit all-one weights remain algebraically the same source profile; fixed
non-unit weights are the package extension. BAM separately optimizes bounded
normalized slack variables, preventing small physical units from being lost
to an absolute cleanup threshold.

The scale layer keeps the CRS/VRS radial efficiency ratio separate from
Banker--Thrall local returns to scale. `local_returns_to_scale` first selects a
Pareto-efficient VRS target and then reports the complete admissible
support-intercept interval at that target, including unbounded endpoints and
multiple local support types. Its five-organization published oracle prevents
one arbitrary solver dual from being mistaken for an identified IRS/CRS/DRS
classification. `scale_elasticity` reuses that exact target and interval to
quantify separate scale-up and scale-down output responses. Its seven-unit
published oracle includes a frontier kink, an infeasible contraction boundary,
and a feasible scale-up with zero additional output.

`relative_directional_scale_elasticity` extends the operating question without
pretending that every resource and service changes at the same rate. It
requires explicit nonnegative, mean-one relative-rate vectors, never silently
normalizes them, and records them as declared counterfactuals rather than
inferred management preferences. The implementation reproduces all three DMU
2 scenarios in Ren et al. (2021), retains the article's zero-patent boundary
case, and reduces exactly to `scale_elasticity` when both directions contain
only ones.

MPSS and Färe--Grosskopf--Kokkelenberg physical capacity remain non-public
development prototypes in this evidence version. Both are deferred to the next
version, and no public API or source-frozen result interpretation is claimed
here. The required audits are tracked in the
[Banker MPSS source protocol](https://github.com/daopingw/DEAPack/blob/main/specs/source_protocols/banker_1984_mpss.md)
and
[FGK physical-capacity source protocol](https://github.com/daopingw/DEAPack/blob/main/specs/source_protocols/fare_grosskopf_kokkelenberg_1989_capacity.md).

`FreeCoordinationHullDEA` (exact public alias `FCH`) evaluates an organization
against nonempty combinations of distinct observed organizations, with each
reference organization available zero or one time. The binary-subset
technology sits between one-template FDH and integer-replication FRH under
matched data and disposal assumptions, but it is not generally nested with
VRS. Sparse two-phase MILPs report the selected coalition, reference activity,
free-disposal residuals, and componentwise binary/bound/constraint and MIP-gap
certificates. The built-in `coordination_hulls` theory dataset distinguishes
FDH, FCH, FRH, CCR, and VRS in both orientations. The historical name “free
aggregation hull” is retained as provenance, but `FAH` is not exposed as an
API alias because Ray (1997) used the same acronym for a distinct
cost-indirect free-affordability technology.

`FreeReplicabilityHullDEA` (exact alias `FRH`) evaluates organizations against
integer combinations of complete observed operating modules. It uses one
common non-convex technology for input and output orientations, reports the
certified integer replication plan and disposal residuals, and never obtains
FRH by rounding a continuously divisible CRS solution. The project-authored
`integer_coordination_hulls` case checks both orientations and the selected
whole-module portfolios; separate tests enforce the expected FDH--FRH--CRS
nesting. The method documentation retains the relevant literature and
third-party implementation citations without bundling their numerical
examples.

The public bounded-adjusted measure (`BoundedAdjustedDEA`, or `BAM`) reports
each jointly attainable input saving and output increase relative to that
organization's sample-supported one-sided room. It supports
CRS/VRS/NIRS/NDRS, keeps the bounds and frontier on one frozen global sample,
and reproduces a 12-DMU VRS/CRS cross-implementation oracle. The complete
108-utility Aida source table is publicly readable in its article archive but
is In Copyright and contains transcription ambiguities; DEAPack cites it
without bundling or silently repairing the data.

`RangeDirectionalDEA` (exact alias `RDM`) asks what common share of each
organization's remaining observed input-saving and desirable-output-growth
opportunities is jointly feasible. It fixes the source VRS technology, forms
the coordinatewise aspiration and frontier from the same self-inclusive
comparison population, accepts finite signed accounts, and reports native
`beta` alongside `rdm_efficiency = 1 - beta`. A negative desirable-output
observation is not an undesirable output. Phase-one directional targets,
peer activity, and residual slack remain distinct, and an efficiency of one
does not certify strong efficiency. An all-zero active direction is reported
as undefined/unbounded rather than repaired. The exact
`range_directional_signed` oracle is independent of the confidential source
bank sample.

The first source-qualified peer-appraisal layer is public through
`LiangWuCookZhuGameCrossEfficiency`. Each synchronous update solves all
protected-by-focal pair programs, uses the source-fixed equal mean including
self, and releases scores only after an additional complete fixed-point
verification. The ordinary solver-selected CRS cross-efficiency
implementation remains an internal prototype: the defining Sexton--Silkman--
Hogan and Doyle--Green full texts were not obtainable for equation-level
audit, so it has no current public import or catalog identity.

Andersen--Petersen radial super-efficiency is deferred for the same evidence
reason. Its tested leave-one-out implementation is retained internally, but
later sources and numerical agreement do not substitute for the unavailable
defining full text. No public Andersen--Petersen constructor is claimed in
this version.
`RayDirectionalSuperEfficiency` (exact alias
`NerloveLuenbergerSuperEfficiency`) supplies a separately source-qualified
VRS leave-one-out account. It fixes the direction to the evaluated
organization's observed resource--service bundle and reports
`nl_super_efficiency = 1 - beta` as joint peer-replacement exposure, not as an
efficiency percentage. Independent dense LPs reproduce every displayed value
in Ray's ten-organization example and 28-airline application. The published
Austrian case with a score above two keeps its certified scalar for audit but
marks the implied negative service boundary invalid. Sparse execution compiles
one base population and zero-fixes each focal intensity, avoiding one retained
near-global matrix copy per observation.
`ToneSuperSBM` (exact alias `SuperSBM`) adds the source-qualified non-radial
counterfactual. It first admits only strongly efficient ordinary-SBM records,
then asks how difficult each admitted record is for the remaining
organizations to replace when pressures may differ across resources and
services. The public surface reproduces Tone's published seven-unit and
power-plant results, supports the three source CRS orientations and the
source non-oriented VRS formulation, and rejects automatic zero-data,
signed-data, undesirable-output, and unsupported-RTS extensions.

The first operating-environment comparison is also public.
`RadialMetafrontierDEA` (concise exact alias `MetafrontierDEA`) fits
matched radial frontiers for ex ante groups and one pooled meta opportunity
set. It reports group efficiency, meta efficiency, and the metatechnology
ratio (historical MTR/TGR) under
`meta_efficiency = group_efficiency * metatechnology_ratio`. The source
defaults are output orientation and VRS; CRS and input orientation are also
supported. Metadata distinguishes pooled convex/conic construction from a
nonconvex union and records that panel fits pool all study periods at both
levels. The internal `reference.group` and `technology.meta.pooled_convex`
labels describe this composition; neither is a standalone public operator.
The six-organization `metafrontier_groups` oracle is analytically
exact and independently LP-compiled. The decomposition is an accounting
diagnosis, not a causal attribution, and DEAPack does not claim reproduction
of the paper's unavailable observation-level FAO application. Its dedicated
`result.plot(kind="metafrontier")` view connects each certified group
efficiency to pooled-opportunity efficiency and labels the MTR without
promoting a specialized metafrontier variant.

The first internal-production leaves use one two-stage business process to
show why a common graph does not imply a common performance account.
`NetworkData` stores every intermediate once and `TwoStageSeriesSpec`
declares its handoff between processes.
`FareGrosskopfNetworkRadialDEA` asks how far external resources can contract
while final services and one coordinated internal-flow plan are preserved. It
uses separate process intensities, permits disposable intermediate surplus,
and reports one system score rather than inventing stage efficiencies. The
evaluated organization's observed handoff is shown for comparison but is not
fixed as a condition on the coordinated benchmark. Targets always use the
complete intensity solution; if tiny coefficients are omitted from the peer
display, their upstream and downstream sums remain disclosed. CRS
follows the Färe--Grosskopf intermediate-products lineage; the separately
convex VRS option follows the later Podinovski--Bouzdine-Chameeva statement.
Under matched CRS conditions its system score is strictly dual to the
Kao--Hwang primary system score, but the methods are not API aliases.
`KaoHwangRelationalDEA` adds the CRS multiplicative relational stage account.
`ChenCookLiZhuAdditiveDEA` reports the CRS/VRS weighted-arithmetic account in
which stage weights are endogenous virtual-resource shares, not user
importance weights. The relational and additive leaves reproduce the complete
24-insurer score oracles, diagnose nonunique stage attribution, and return
source-qualified Lim--Zhu projections. The additive leaf retains distinct
upstream and downstream intermediate targets instead of replacing them with a
fabricated single flow.
`CookZhuBiYangAdditiveDEA` now carries that weighted-arithmetic
performance-attribution account into source-compatible open acyclic networks:
outside resources and final services may enter or leave at intermediate
processes, and links may branch or skip a stage. Its sparse graph compiler and
published two- and three-stage oracles cover the source CRS programme. Process
shares remain endogenous accounting shares, while nonunique process
decompositions are labelled as such. General-network VRS, cycles, shared
pools, transformed links, and projections are withheld for this additive
leaf because its checked source does not provide a complete numerical
contract for them.
`EnvironmentalNetworkSpec` overlays economic input, desirable-output,
undesirable-output, and ordinary-intermediate product accounts on a declared
process graph without duplicating its quantity matrix.
`KalhorKazemiMatinNetworkDEA` uses the corrected source-specific
activity-specific weak-disposal technology to ask how much external resource
commitment the whole organization could save while preserving final good and
bad commitments. It returns one system factor, process-specific active and
complementary intensities, and coordinated account targets under
CRS/VRS/NIRS/NDRS. The two source examples are independently reproduced; no
process-efficiency or strong-slack claim is inferred, and the separate
directional-distance application remains `deferred_to_next_version`.
`ToneTsutsuiNetworkSBM` supplies the distinct non-radial performance account
for connected process systems. It supports fixed and free internal handoffs
and the two source-qualified accountable-link roles: an input-oriented
incoming-link excess belongs once to the recipient process, while an
output-oriented outgoing-link shortfall belongs once to the supplier
process. Every role retains bilateral handoff continuity. The implementation
also supports CRS/VRS, all three base source orientations,
division-specific peer plans, and sparse compile-once solving. Published VRS
and CRS examples validate the fixed/free base, while exact independent
rational oracles validate equations (26)--(27); no non-oriented
accountable-link formula is inferred.
`LewisSextonSequentialNetworkDEA` asks yet another organizational question:
what happens when solver-selected improvements are passed from process to
process through an acyclic organization? Its public slice supports
nonnegative forward quantities, a global input or output orientation, and
process-specific standard RTS assumptions. The source two-organization
example is reproduced, while reverse quantities, mixed accounts, and site
characteristics remain explicit gaps; the procedure is never presented as a
simultaneous joint-network projection.

`ParkParkMultiperiodAggregativeDEA` (exact alias
`MultiperiodAggregativeDEA`) provides one joint radial appraisal of a
balanced operating record while retaining a separate contemporaneous peer
plan in every period. Its mandatory second phase distinguishes full from
weak efficiency. The source four-organization factors and classifications
are reproduced. Because the method has no carry-over or state equation, it
lives under `panel.*`, not `dynamic.*`, and does not report productivity
change.

The first dynamic-production leaf is also public.
`ToneTsutsuiDynamicSBM` treats one complete balanced DMU trajectory as the
assessed observation and links period-specific operating plans with good,
bad, free, and fixed carry-overs. Input, output, and non-oriented CRS/VRS
programmes share one sparse trajectory compiler. The base free-carry-over
objective and the source's ex-post adjusted reporting specialization remain
explicitly distinct, and the published four-period Table 2 is reproduced.
Window DEA, repeated static scores, Malmquist indexes, and the
free-carry-over MIP are not relabeled as this model.

`ToneTsutsuiDynamicNetworkSBM` is the separate process-by-period leaf for
organizations whose internal handoffs and intertemporal carry-overs both
matter. It preserves supplier--recipient continuity for fixed, free,
as-input, and as-output links, supports division-specific CRS/VRS assumptions,
and compiles the complete sparse system once before fitting trajectories.
Because the published terminal carry-over notation is internally
inconsistent, every fit records the selected boundary-resolution policy
instead of inventing or silently discarding a terminal observation.
Environmental results distinguish strong disposal from the current
bad-output-equality formulation, preserve `"weak"` only as its compatibility
selector, and state the status of any named weak-disposal equivalence.
Separability, null jointness, and pollution-generating inputs likewise remain
visible instead of being hidden behind a generic bad-output switch.

`ZhouAngWangNonCHPEnergyCarbonDEA` (short alias
`NonCHPEnergyCarbonDEA`) is a narrow, source-exact application preset rather
than another foundational family. It requires one strictly positive fossil
input, one electricity output, one CO2 output, CRS, and a self-inclusive
global non-CHP cross-section. Callers must explicitly choose the source's
energy, carbon, or integrated account; there is no hidden default and no
custom direction or weight surface. The raw non-radial distance and the
higher-is-better EPI/CPI/ECPI transformation remain separate. Optional
optimal-face diagnostics bound component steps and transformed indexes
without claiming a unique target or peer plan. Independent dense programmes
and an exact three-system fixture certify all three accounts. In accordance
with the handbook gate, this paper-specific preset is fully covered by the
technical Documentation but is not a book chapter, case, figure, or appendix.

`ToneNonSeparableSBM` (aliases `NonSeparableUndesirableSBM` and `SBMNS`)
implements Tone's distinct 2003 hybrid. Every input stays in the ordinary
input-slack account; users partition only good and bad outputs. A declared
joint-output block shares one retained operating proportion `alpha`, while
the remaining outputs adjust through separate slacks. The source projection
`alpha * observed` is reported separately from reference activity and from
unscored residuals, so neither non-separability nor `alpha` is relabeled as
weak disposal. An independent equation compiler recovers Tone's Table 4 data
and all Table 5 projections and `alpha` values. Several printed Table 5
scores do not agree with equation (30), so this is an analytical certificate,
not a claim to have reproduced the complete published score column. The
separable `UndesirableSBM` independently reproduces the high-resolution
equal-weight 1:1 branch of Tone's Table 2; no claim is transferred to its
unequal-weight columns. Its public combined output account is dimension
weighted when the numbers of desirable and bad outputs differ, and its
original-unit targets and marginals remain coherent under extreme independent
changes of measurement unit.

The current material-inflow model takes named physical input/output
coefficients instead of inferring material surplus from ordinary DEA
variables. Its source-native
[Coelli--Lauwers--Van Huylenbroeck](https://doi.org/10.1007/s11123-007-0052-8)
claim is limited to ordinary nonnegative inputs and desirable outputs, one
common known nonnegative material-content system with positive observed
inflow, a fixed desirable-output commitment, and a self-inclusive
cross-section under CRS or VRS. An independent exact compiler verifies
$TE$, $EE$, physical-content $EAE$, and $EE=TE\times EAE$; EAE needs no
prices. Material-minimizing targets can be nonunique, and the certificate is
not a farm-level reproduction because the source's unit-level 183-farm
observations are not supplied.

The source's equations (18)--(21) discuss weighted multiple pollutants, and
the implementation requires and retains explicit weights when several
materials are aggregated. That aggregate is not included in the current
independent certificate. NIRS/NDRS,
multi-material aggregation, heterogeneous or estimated coefficients,
panel/custom/external source equivalence, the farm application, and welfare,
causal, damage, or actual-emission claims are `deferred_to_next_version`.
Weak-$G$ conservation and multi-equation material-balance technologies remain
separate planned families.

```python
from deapack import BCC, BCCInput, DEAData, load_dataset

frame = load_dataset("frontier_1x1")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    inputs="input",
    outputs="output",
)

result = BCCInput().fit(data)
print(result.summary())
print(result.peers("E"))

# Notebook-ready, self-contained management brief; no plotting dependency.
brief = result.report()
brief.save("bcc-result-brief.html")

# Complete, deterministic hand-off: HTML, full CSV/JSONL tables, metadata,
# a manifest, and SHA-256 hashes in one atomic archive.
result.export_bundle("bcc-result-audit.zip")
```

`BCCInput` is the complete BCC-I recipe: it fixes VRS, input orientation,
native $\theta$, and DEAPack's slack-completed target policy. The companion
presets are `BCCOutput`, `CCRInput`, and `CCROutput`; configurable `BCC`,
`CCR`, and `RadialDEA` remain available when the research design deliberately
leaves part of that recipe open.

Compatible radial, directional-distance, and generalized-distance fits now
share the embedded
`evaluation.target_completion.pareto_koopmans` protocol. It holds the
first-stage performance result fixed, completes remaining ordinary input and
desirable-output slacks with zero-safe row scaling, and only then reports
generic Pareto--Koopmans status. The selected alternate optimum is package
policy rather than a claim that the foundational papers prescribe one unique
management target; environmental, nondiscretionary, and non-convex completion
extensions remain deferred.

With the optional visualization extra, the same scalar result can draw its
certified VRS frontier and the moves from observed operations to reported DEA
targets:

```python
frontier = result.plot(kind="frontier")
frontier.savefig("bcc-frontier.svg", bbox_inches="tight")
```

The frontier view is deliberately limited to auditable one-input/one-output
CRS or VRS radial results with completed slacks. Multidimensional results use
the general `performance` plot, target tables, and peer accounts rather than a
misleading two-dimensional reconstruction.

Applications can inspect only the methods that are executable in the installed
version without parsing the wider research roadmap:

```python
from deapack import list_methods, method_info

print([item.method_id for item in list_methods()])
print(method_info("static.radial.fdh").api_symbols)
```

The discovery catalog is intentionally narrower than the field-wide method
atlas: planned families are documented for design and review, but they are not
reported as runnable methods.

Large score-only jobs can skip the lexicographic slack phase explicitly:

```python
result = BCC(compute_slacks=False).fit(data)
```

In that mode DEAPack reports radial efficiency but does not claim strong DEA
efficiency, because the remaining slacks were not optimized.

## Numerical policy

The default backend uses the HiGHS solver provided through SciPy. It requires
no separately configured optimization executable and accepts sparse matrices.
Model construction is matrix-based; pandas objects are not accessed inside the
per-DMU solver loop. Standard FDH uses a chunked dominance-and-ratio scan and
does not invoke an LP or mixed-integer solver.

## Built-in teaching datasets

```python
from deapack import list_datasets, load_dataset

for info in list_datasets():
    print(info.name, info.teaching_uses)
```

The installed catalog currently contains 33 datasets. Its replacement suite
uses neutral project teaching cases for cost and mix choice,
strategic peer appraisal, multi-period trajectories, dynamic carry-overs,
directional and SBM peer replacement, environmental disposability and
recovery, by-production bottlenecks, integer coordination, and open,
two-stage, or three-process service chains. Small foundation cases, transparent
analytic oracles, deterministic panels, and the complete-study capstone remain
available for classroom workflows. `list_datasets()` is the authoritative
runtime inventory; each entry exposes declared column roles and teaching uses
so examples do not depend on a historical table layout.

All 33 installed datasets have exact content-hash license mappings. The 29
project-origin datasets and the independently selected Zhou equation fixture
use CC BY 4.0 with attribution to Daoping Wang / DEAPack;
`ren_cas_directional_scale` retains its upstream CC BY 4.0 attribution, and
`revenue_5x2` plus `revenue_8x2` retain their upstream MIT notices. Method
pages and specifications continue to cite the defining DEA literature, but a
method citation is not a claim that the paper's numerical table is bundled or
redistributed.

The historical provincial panel from the 0.1.x tree is not installed: its
tracked CSV has been removed from the current 2.0 source tree, no data alias is
provided, and only a non-numerical migration diagnostic is retained.

## Book and documentation

The companion book, [*Data Envelopment Analysis: Efficiency, Productivity, and
Environmental Performance with Python*](book/index.md), is prepared for
publication from one reviewed English source in English and Chinese. The
Chinese rendering uses Sphinx gettext catalogs and a project terminology
guide so that formulas, symbols,
citations, code, and computed values remain aligned while the prose follows
Chinese scholarly usage. The separate [package Documentation](docs/index.md)
is English-only for the first public release. Both products use MyST Markdown
and warning-free Sphinx builds:

```bash
python -m pip install -e '.[docs,viz]'
make -C book html
make -C book html-zh
make -C docs html
```

The release workflow treats both Handbook languages as required publication
artifacts. Package Documentation remains English so API reference work does not
compete with the editorial review of the Chinese teaching text.

Package users can enter through the
[`installation guide`](docs/getting-started/installation.md),
[`method catalog`](docs/user-guide/method-catalog.md), and
[`API reference`](docs/api/index.md). Contributors can use the unified
[`extension guide`](docs/developer/extending.md) and
[`versioning and deprecation policy`](docs/developer/versioning.md) before
changing a solver, model, result, visualization, or reporting contract.

## Development and release lifecycle

The [`contribution guide`](CONTRIBUTING.md) defines the source, oracle,
compatibility, test, performance, and documentation gates for a change. The
[`changelog`](CHANGELOG.md) records user-visible development and release
history. Software packaging, hosted Documentation, and the companion book use
separate publication steps; passing tests in a development checkout is not a
tagged release.

## How to cite

Software and book citations are kept separate. The root
[`CITATION.cff`](CITATION.cff) supplies machine-readable metadata for the
DEAPack software, while [`CITATION.md`](CITATION.md) explains when to cite the
software, the companion book, or both. Release history begins in
[`CHANGELOG.md`](CHANGELOG.md).

This release candidate has no DOI. The repository does not use placeholder
DOIs, ORCIDs, ISBNs, publishers, or publication dates. A future archived
software release will receive its own record; the editorially frozen book
will be deposited separately with its own citation.

## Status

`2.0.0rc1` is a pre-release and is not a drop-in replacement for DEAPack
0.1.x. During the release-candidate cycle, changes are restricted to
correctness, packaging, documentation, and compatibility fixes; new model
families move to the next development cycle. Mathematical and reporting
conventions change only through the shared specification process.

## License

The DEAPack software component uses `GPL-3.0-only`; see [`LICENSE`](LICENSE).
The preserved uppercase `DEAPack/*.py` 0.1.x compatibility source retains its
original 2024 MIT terms in
[`LICENSES/MIT-DEAPack-0.1.x.txt`](LICENSES/MIT-DEAPack-0.1.x.txt) and is not
included in the 2.x package archives.
Project-owned original package Documentation prose uses
`CC-BY-NC-SA-4.0`, while executable examples and code blocks remain GPL
software. Bilingual Handbook Preview 1 is All Rights Reserved and carries
`Copyright © 2026 Daoping Wang`; separately identified third-party material
retains its own terms. The complete component boundary is in
[`COMPONENT_LICENSES.md`](COMPONENT_LICENSES.md).

Dataset content does not inherit the code license automatically.
[`DATA_LICENSES.md`](DATA_LICENSES.md) binds all 33 current fingerprints to
their exact terms: 30 project-created or independently selected fixtures use
`CC-BY-4.0`, `ren_cas_directional_scale` retains upstream `CC-BY-4.0`, and
the two revenue datasets retain upstream `MIT`. The maintainer confirmed that
no DEAPack 2.0 copy was conveyed to a third party under the superseded MIT
development metadata.
