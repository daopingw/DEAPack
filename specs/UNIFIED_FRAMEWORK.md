# DEAPack unified framework

This document is the normative architecture for reasoning about DEA methods.
It sits above individual mathematical programmes, Python classes, book
chapters, and historical model names.

The framework has two purposes:

1. to make a DEA study begin with an economic or managerial question rather
   than with a fashionable model name; and
2. to reuse mathematics and software only when the underlying production
   problem is genuinely the same.

It is informed by the production-economics literature, the major DEA
handbooks and reviews, and the six-phase COOPER process for empirical
non-parametric projects. The COOPER process describes how an empirical project
is conducted. The DEAPack framework complements it by specifying what a
fitted performance model contains and how apparently different DEA models are
related.

Whether a proposed composition is executable is governed by the fail-closed
property contract in `specs/COMPATIBILITY_MATRIX.md`.
Sharing a compiler or an algebraic representation is not enough: the
composition must also preserve the data domain, economic interpretation,
target semantics, reference technology, numerical contract, and any
downstream productivity or inference operator.

## 1. The unit of analysis is a study specification

A complete DEAPack study is an ordered, named record:

$$
\mathcal{S}
=
\left\langle
\mathcal{C},\mathcal{G},\mathcal{D},\mathcal{T},\mathcal{E},
\mathcal{R},\mathcal{M},\mathcal{V},\mathcal{P},\mathcal{A},\mathcal{U}
\right\rangle_{\mathrm{validated}},
$$

where:

- $\mathcal{C}$ is the **decision context**;
- $\mathcal{G}$ is the **production-system graph**;
- $\mathcal{D}$ assigns **economic roles to the data**;
- $\mathcal{T}$ defines the **technology assumptions**;
- $\mathcal{E}$ identifies the **frontier estimator**;
- $\mathcal{R}$ states the **benchmark policy**, separating the comparison
  population from the temporal information set;
- $\mathcal{M}$ defines the **performance criterion**;
- $\mathcal{V}$ states the **valuation or preference information**;
- $\mathcal{P}$ defines the **evaluation protocol**;
- $\mathcal{A}$ is the **analytical operator**; and
- $\mathcal{U}$ states the **uncertainty and inference design**.

The fields are ordered for validation but are neither mathematically
orthogonal nor freely composable. Decision context constrains admissible data
roles; the production graph constrains feasible technologies; technology and
data domain restrict valid measures; and a productivity or inferential
operator can be used only with base estimates for which its identity has been
established. The subscript `validated` denotes those dependency and
compatibility checks.

A historical name such as CCR, network SBM, or global
Malmquist--Luenberger identifies a validated alias, preset, variant, family,
or other partial record over these fields. The registry records which of those
relationships applies. The name is useful for discovery and citation; it is
not the software architecture.

## 2. Layer 1: decision context

The first layer answers the questions that determine whether the numerical
result has a defensible economic meaning:

- What organization, programme, plant, region, or production activity is
  being evaluated?
- Which decisions are controlled by its managers, and which conditions are
  inherited or externally imposed?
- Is the objective to save resources, expand services, improve quality,
  reduce pollution, lower cost, increase revenue, or assess change over time?
- Are units sufficiently comparable to learn from one another?
- Are market prices, policy priorities, damage weights, or managerial
  preferences available?
- Is the analysis descriptive, inferential, diagnostic, or prescriptive?

This layer is recorded in a `DecisionContext`. It does not alter an LP by
itself, but it determines which components are admissible and how results may
be interpreted. A model that cannot answer the declared question should fail
at study validation rather than return an impressive but irrelevant score.

## 3. Layer 2: production-system graph

The production graph describes where transformation takes place.

| Graph | Economic system represented |
|---|---|
| `black_box` | one organization transforms final inputs into final outputs |
| `series` | the output of one stage becomes an input to a later stage |
| `parallel` | several activities use separate or shared resources |
| `general_network` | an arbitrary directed system of processes and links |
| `dynamic_carryover` | current decisions create assets or liabilities carried to later periods |
| `intertemporal` | investment, quasi-fixed capital, adjustment costs, expectations, and terminal conditions jointly determine a multi-period plan |
| `dynamic_network` | both internal links and intertemporal carry-overs matter |
| `hierarchical` | units, sub-units, and higher-level systems overlap or nest |

“Two-stage DEA,” “multi-stage DEA,” and “network DEA” are therefore structural
descriptions, not single efficiency measures. The same series system may be
evaluated with ratio, radial, directional, additive, or slacks-based measures.
Conversely, applying a black-box SBM does not reveal stage-level
performance shortfalls.

Links have explicit accounting semantics:

- `fixed`: the observed link quantity must be respected;
- `free`: the model may choose a feasible internal allocation;
- `shared`: several processes draw from a common resource;
- `effect`: a carry-over is beneficial, harmful, or neutral;
- `control`: its level is endogenous, fixed, or bounded;
- `balance`: exact, at-least, at-most, or a declared transition relation;
- `lag`, `decay`, and initial/terminal policies describe temporal accounting;
- `exogenous`: a process receives an input not produced inside the network.

For environmental networks, link incidence and economic product identity are
separate declarations. Several process-specific final or internal quantities
may belong to one desirable or undesirable product account, and several
producer--recipient flows may belong to one ordinary-intermediate product
account. Unit conversion and source balance rows operate on the complete
account; a column name or the mere fact that a quantity is a link cannot
infer its environmental role.

The graph compiler records these roles without deciding how performance is
measured. For example, the same closed seller--buyer chain can feed a
multiplicative relational account, an endogenous-share additive account, or
a slacks-based divisional account. Conversely, Cook--Zhu--Bi--Yang's additive
measure can be compiled over an open acyclic chain, a branching organization,
or a graph with a skip link. Reusing the graph layout removes duplicate code;
it does not merge the economic questions or their result contracts.

## 4. Layer 3: economic data roles

Variables are not classified merely by which side of a spreadsheet they
occupy.

| Role | Meaning |
|---|---|
| discretionary input | a resource the evaluated manager can reduce |
| non-discretionary input | an inherited requirement or environmental condition |
| desirable output | a valued service, product, or outcome |
| undesirable output | a jointly produced burden such as emissions or failures |
| intermediate product | an output of one process and input of another |
| carry-over | a stock or obligation connecting periods |
| price | an opportunity cost, revenue, or valuation used in an economic objective |
| contextual variable | an external condition used for heterogeneity or conditional analysis |
| group | a technology class used in group/meta-frontier comparison |
| identifier | a unit, period, process, geography, or scenario key |

A physical quantity may play different roles in different studies. Energy can
be a discretionary input, a fixed requirement, or an intermediate product.
The role must be declared; DEAPack never infers it from a sign transformation.

Special data restrictions are also declared here: categorical, ordinal,
ratio, bounded, integer, interval, imprecise, zero-valued, or negative-valued.
A measure is valid only if its denominator, translation, and units are
compatible with the declared data domain.

These declarations are not interchangeable. A negative desirable output is a
data-domain issue, not an undesirable output. A non-discretionary input helps
define feasible comparison while remaining outside the manager's adjustment
plan; a contextual variable may instead change which organizations are
comparable. Ratio variables cannot automatically be convexified like volume
variables, and integer targets generally require a discrete technology rather
than post-solution rounding.

## 5. Layer 4: technology assumptions

The technology describes which operating plans are treated as attainable.
It is compiled independently of the performance measure.

### 5.1 Deterministic empirical construction

- `convex_envelopment`: convex combinations of observed activities;
- `free_disposal_hull`: observed activities and free disposal without
  convexification;
- `free_coordination_hull`: in
  [Green and Cook (2004)](https://doi.org/10.1057/palgrave.jors.2601773), a
  binary subset of distinct observed activities may be added, but each
  observed organizational unit enters at most once;
- `free_replicability_hull`: nonnegative integer copies of observed
  activities may be added, while fractional activity copies remain
  inadmissible;
- `multiplicative_envelopment`: a source-qualified piecewise log-linear
  production construction rather than the multiplier representation of
  ordinary CCR/BCC.

The word “non-convex” is not sufficiently precise. Every empirical technology
also records two orthogonal construction fields:

```text
activity_combination =
    convex_mixture
  | single_observation
  | binary_subset_aggregation
  | integer_replication
  | selective_convexity

scale_extrapolation =
    none
  | continuous_crs
  | continuous_nirs
  | continuous_ndrs
  | integer_additivity
  | bounded_replication
  | local_band
  | bounded_intensity
```

The familiar technologies then become transparent compositions:

| Technology | Activity combination | Scale extrapolation |
|---|---|---|
| BCC/VRS | `convex_mixture` | `none` |
| CCR/CRS | `convex_mixture` | `continuous_crs` |
| standard FDH | `single_observation` | `none` |
| FCH | `binary_subset_aggregation` | `none` |
| FRH | `integer_replication` | `integer_additivity` |

This representation prevents several invalid mergers. FDH selects one
observed activity. FCH can coordinate several *distinct* observed
organizations, each at most once. FRH can repeat the same complete template,
while CCR additionally admits fractional activity. Thus, under matched
nonnegative volume data and ordinary free disposal,
$T_{FDH}\subseteq T_{FCH}\subseteq T_{FRH}\subseteq T_{CCR}$.
FCH and FRH are not generally nested with the VRS convex hull. None of these
relations turns one production assumption into a solver option on another.

FCH also requires quantities that are economically additive across
organizations; ratios, percentages, prices, or averages do not become
additive because binary activity variables are available. FRH is not
integer-valued DEA because the observed quantities may be continuous while
only activity replication counts are integral. A finite replication bound
changes the maintained FRH technology and therefore uses
`bounded_replication`; a bound derived solely to make an exact MILP finite is
computational metadata, not a production assumption.

Conditional and partial frontiers change how a statistical benchmark is
formed and are specified on the estimator layer. Stochastic technologies and
robust-optimization counterparts alter feasibility using, respectively, a
probability model or an uncertainty set. They therefore compose with a base
production account but remain explicit uncertainty specifications rather
than ordinary choices of empirical hull.

State-contingent production is different again. It represents an ex ante plan
whose deliverables are indexed by mutually exclusive states of nature. The
technology can be defined without assigning probabilities to those states;
beliefs, risk preferences, and expected value enter only when the analyst asks
an additional economic-choice question. An event-specific DEA estimator may
use an observed random condition to partition the state space, but neither
construction is a bootstrap, a chance constraint, or a dynamic carry-over
model. See
[Chambers, Hailu, and Quiggin (2011)](https://doi.org/10.1111/j.1467-8489.2010.00517.x)
and
[Serra, Chambers, and Oude Lansink (2014)](https://doi.org/10.1016/j.ejor.2013.12.037).

### 5.2 Scale assumptions

CRS, VRS, NIRS, and NDRS are technology restrictions. CCR and BCC are named
CRS and VRS specializations of radial DEA because neither name alone fixes
orientation or target policy. CCR-I/O and BCC-I/O become complete historical
presets once those remaining conventions are fixed. DEAPack exposes those
presets as `CCRInput`, `CCROutput`, `BCCInput`, and `BCCOutput`; each uses the
shared `static.radial` method and fixes the package's row-scaled
lexicographic slack/target completion. That alternate-target selector is an
explicit package policy rather than a target uniquely prescribed by the
foundational paper. None is an independent solver family. Scale efficiency,
local returns to scale, most productive scale size, and congestion are
analyses of specified technologies, not synonyms for the technology itself.

### 5.3 Disposability and joint production

Ordinary good-output DEA commonly permits unused inputs and foregone desirable
outputs. Undesirable outputs require a substantive account of pollution or
quality failure:

- strong disposal of the bad;
- weak disposal and its abatement trade-off;
- null jointness;
- separate intended-production and residual-generation sub-technologies
  (by-production);
- explicit material-balance constraints;
- named natural/managerial disposability systems.

These assumptions are not interchangeable options for changing the sign of a
variable. They represent different accounts of how production and abatement
work.

Environmental regulation also has no universal technology switch. An
emissions or intensity standard may restrict the operating plans that are
legally feasible; a tax or permit price supplies valuation information; an
industry-wide cap creates a centralized allocation problem; and regulation
may instead be an inherited condition used to define fair comparison. Asking
whether regulation *caused* a later performance change requires an additional
identification design. These roles must be declared separately. The
regulatory-standard construction of
[Zofío and Prieto (2001)](https://doi.org/10.1016/S0928-7655(00)00030-0),
for example, measures the attainable production sacrifice associated with a
declared standard; it is not a causal estimate of the standard's policy
effect.

### 5.4 Structural restrictions

Source-qualified production trade-offs impose declared marginal or
substitution relationships on attainable quantities. They change or extend
the empirical technology. A dual formulation may resemble a restriction on
multiplier weights, but that algebraic relationship does not turn a statement
about production possibilities into a preference statement.

For network and dynamic systems the compiler adds process-specific
technologies, link balances, shared-resource constraints, carry-over balances,
and, when appropriate, divisional scale assumptions. These restrictions
belong to the production graph and technology, not to a special “network
score.”

## 6. Layer 5: frontier estimator

Technology assumptions describe the maintained production possibilities:
convexity, returns to scale, disposability, production links, and dynamic
state accounting. The estimator states how the boundary is constructed from
sample information under those assumptions.

The initial estimator registry distinguishes:

- full-sample convex DEA envelopment;
- full-sample non-convex FDH;
- full-sample non-convex integer-replication FRH;
- order-$m$ and order-$\alpha$ partial-frontier estimators;
- conditional DEA/FDH estimators with an explicit conditioning design; and
- future source-qualified statistical or shape-constrained frontier
  estimators.

An inference procedure is not an estimator. A bootstrap acts on a declared
estimator under a compatible data-generating process; it does not turn
full-frontier DEA into order-$m$. Conversely, selecting a partial or
conditional frontier changes the estimand even before confidence intervals
are considered.

## 7. Layer 6: benchmark policy

A benchmark policy answers two independent questions before any evaluation
exclusion is applied:

1. **Comparison population:** whose experience is substantively admissible?
2. **Temporal information set:** which periods of that experience are visible
   to the comparison?

For an evaluated observation $o$, let $\mathcal P_o$ denote rows belonging
to eligible organizations and $\mathcal I_o$ the visible time rows. An
evaluation protocol may then remove rows $\mathcal X_o$, for example the
evaluated observation in a super-efficiency recipe. The candidate
observations are

$$
\mathcal B_o
=
(\mathcal P_o \cap \mathcal I_o)\setminus\mathcal X_o .
$$

The selected technology compiler then constructs an attainable set from
$\mathcal B_o$. A pooled convex hull, a non-convex union, and an envelope of
already constructed group technologies can therefore differ even when they
start from the same candidate rows.

| Comparison-population policy | Benchmark question |
|---|---|
| all eligible | which organizations have comparable missions, boundaries, variables, and units? |
| group | which organizations belong to a declared technology group? |
| custom | which explicitly selected organizations may serve as candidates? |
| spatial peers | is geographic proximity a defensible eligibility rule for this study? |

| Temporal-information policy | Benchmark question |
|---|---|
| contemporaneous | what was attainable in the same period? |
| sequential | what had become visible using information available up to that period? |
| global | what appears attainable when all study periods are viewed retrospectively? |
| biennial | what is attainable in the two periods being compared? |
| window | what is attainable within a moving local time window? |

Changing either axis can change the empirical question without changing the
distance function. Malmquist, global Malmquist, and biennial Malmquist reuse
distance engines but use different temporal information sets. A group
comparison and a pooled comparison can share a period rule while using
different populations. In a cross section, “all eligible observations” is a
population choice; it should not be called a global temporal technology merely
because every row is used.

Meta-frontier construction belongs to the technology/estimator composition
that follows population and time selection. Leave-one-out belongs to the
evaluation protocol. Positive-intensity peers, unary reference sets, and
maximal or global reference sets are results of a fitted model, not input
policies. Every pooled temporal policy additionally records sample vintage,
`hull_construction`, convexification, and returns to scale.

Spatial information can enter other layers and must not be reduced to the
spatial-peers population rule. Location may be a contextual condition in a
conditional frontier, neighboring activities may create a genuine
cross-organization production spillover, or spatial dependence may require a
special inferential design. These mechanisms answer different questions; see
[Vidoli and Canello (2016)](https://doi.org/10.1016/j.ejor.2015.10.050)
and
[Ramajo, Márquez, and Hewings (2024)](https://doi.org/10.1111/grow.12711).

## 8. Layer 7: performance measure

A performance criterion defines the improvement plan or economic objective
used to compare an observation with the selected technology.

### 8.1 Proportional plans

Input- and output-oriented Farrell measures ask for a common proportional
resource saving or output expansion. Their CCR/BCC labels identify scale
assumptions. Hyperbolic and graph measures define coordinated proportional
changes on more than one side of production.

Multiplicative DEA constructs a piecewise log-linear/multiplicative
technology. It is not the multiplier representation of CCR and requires its
own technology/measure audit.

### 8.2 Directional plans

A directional distance function declares a vector of resource reductions,
service expansions, and undesirable-output reductions. It reports the
largest feasible implementation rate of that declared plan. Directional
distance is a broad measure family, but it does not by itself determine the
technology, network, benchmark period, or statistical estimator.

The numerical vector is accompanied by a **direction policy**. An exogenous
direction may be elicited from responsible decision-makers, authorized by a
budget or service mandate, prescribed by a defining source, or constructed by
the analyst for sensitivity analysis. Observation-scaled, sample-range,
ideal-point, common-direction, and value-optimized directions answer different
questions. An endogenous cost/revenue/profit direction changes the valuation
and evaluation protocol as well as the numbers passed to a performance
compiler; it is not an ordinary parameter alias.

Direction provenance limits the interpretation. A vector supplied by an
analyst is a declared counterfactual, not evidence of management preference.
Relative-directional scale elasticity likewise uses input and output
percentage-rate scenarios at a selected efficient plan. It reduces to radial
scale elasticity for all-one relative rates, but it is not a physical-unit
DDF merely because both constructions use the word “direction.”

DEAPack preserves the useful unification achieved by the directional
formulation: compatible input- and output-radial programmes, joint
good/bad-output programmes, and many cross-technology evaluations can reuse a
directional performance compiler after the exact direction and score
transformation are declared. That reuse stops at the boundary of the
performance criterion. A fractional SBM, an FDH technology, a network
production account, a Malmquist aggregation rule, and a bootstrap estimator
do not become DDF aliases merely because a directional task can appear inside
their derivation or computation.

### 8.3 Variable-specific plans

Additive, weighted additive, RAM, BAM, Russell/ERM, Hölder-distance, SBM, and
EBM are canonical measure families that allow variable-specific improvements.
They often share balance constraints and sparse matrices, but their
aggregation, normalization, units, monotonicity, and target-selection
properties differ. Each implemented leaf remains a separate public measure
even when one compiler serves several families.

Under the standard strictly positive data domain, the enhanced Russell graph
measure and Tone's standard SBM have an exact transformed representation.
That conditional equivalence is registered explicitly; it does not merge the
whole Russell family. Tone (2001, p. 507) provides two further conditional
representations: input-oriented SBM coincides with the matched input Russell
measure, and output-oriented SBM with the matched output Russell measure.
DEAPack has frozen the standard positive-data technology, weighting,
normalization, and score conventions for those two identities and exposes
`InputRussell` and `OutputRussell` as discoverability aliases of the matched
oriented SBM leaves. Russell formulations outside that equivalence domain
still require separate source-qualified records. None of these results makes
input, output, and graph Russell mutually interchangeable.

Tone's three standard orientations illustrate why compiler reuse is not model
equivalence. Input-, output-, and non-oriented SBM use the same black-box
technology, eligible references, balance equations, and sparse compiler, but
their objectives and normalized accounts answer different operating
questions. They are Level B distinct measures. A best input-oriented score
certifies only that no normalized input excess remains in that objective; the
feasible output slack and output target are solver-selected. The output case
has the symmetric limitation. Only the non-oriented score values both sides
in its primary objective, and even then alternate target selection remains an
evaluation-protocol issue. These statements apply to Tone's strictly positive
domain; zero- or signed-data SBM requires a separately validated formulation.

Subvector or component efficiency declares which particular resources or
outcomes management may adjust. It represents a short-run, energy-specific,
labour-specific, or other partial-control question; it is not obtained by
fitting an unrestricted model and inspecting one slack afterward.

### 8.4 Economic objectives

Cost, revenue, profit, and Nerlovian efficiency use prices or value functions.
They answer different producer decisions:

- cost efficiency minimizes expenditure while meeting an output commitment;
- revenue efficiency maximizes receipts with the available inputs;
- profit efficiency permits input and output changes to maximize net value;
- Nerlovian efficiency normalizes a maximum profit shortfall by the value of
  a declared input--output direction.  The normalization makes the result a
  directional efficiency measure; the unnormalized profit gap remains the
  monetary quantity.

Technical/allocative decompositions are reported only when the price,
orientation, and technology definitions support the identity. “Producer
allocative efficiency” describes adaptation to the supplied prices; it is not
unqualified welfare-economic allocative efficiency. The field name
`overall_efficiency` is prohibited unless a source-qualified meaning is
declared.

Capacity utilization asks what output is attainable when quasi-fixed inputs
are held and variable inputs may adjust. Congestion asks whether excessive
inputs reduce maximum attainable output. Neither is scale efficiency or an
ordinary input slack, and competing congestion definitions retain source
qualified names.

## 9. Layer 8: valuation and preferences

Assurance regions, cone-ratio restrictions, virtual-weight bounds, common
weights, and value-efficiency analysis supply information beyond the observed
input/output quantities.

Preference restrictions limit acceptable implicit valuations. AR-I,
AR-II cross-side bounds, absolute/relative bounds, cone-ratio restrictions,
and Wong--Beasley virtual-share restrictions remain separate executable
leaves. Virtual shares depend on the evaluated observation's data; AR-II has
a different cross-side multiplier meaning. Production trade-offs belong to
the technology layer even when a dual representation resembles a weight
restriction. Consistency, unit dependence, and implied free-production
diagnostics accompany every restriction family.

## 10. Layer 9: evaluation protocol

The evaluation protocol states how observations and alternate optima are used:

- ordinary self-appraisal;
- observation exclusion or modification for a source-qualified
  super-efficiency recipe;
- cross-appraisal with neutral, aggressive, benevolent, or another declared
  secondary objective;
- source-qualified strategic cross-appraisal with named protected/focal roles,
  player set, subproblem family, update order, native payoff, equilibrium
  concept, convergence criterion, and initialization policy;
- common-weight evaluation;
- pessimistic or worst-practice appraisal and a source-qualified rule for
  combining best- and worst-practice results;
- frontier peeling or context-dependent tiers;
- selected-plan benchmark-frequency evidence on the analysis layer, with any
  ranking rule declared separately as an evaluation protocol;
- closest/furthest target selection;
- tie-breaking and multiple-peer/target enumeration.

Comparison-population and time policies establish the eligible candidate
rows; evaluation exclusions operate on that declared base. A historical
super-efficiency method is a recipe composing a compatible base measure, an
observation-exclusion rule, and explicit infeasibility/score policies.

Ranking is an additional social-evaluation protocol, not a more “true”
technical efficiency. Super-efficiency and cross-efficiency are not aliases.
Every result stores the secondary objective, tie-breaking rule, and
multiple-optimum diagnostics that can affect the ranking.

An ordinary cross-efficiency secondary objective selects one multiplier
solution on an evaluator's primary optimum face. [Liang--Wu--Cook--Zhu game
cross-efficiency](https://doi.org/10.1287/opre.1070.0487) instead fixes a CRS
protocol with two semantic indices. For every protected DMU $d$ and
focal/player DMU $j$, one LP normalizes $j$'s virtual input, maximizes
$j$'s score, and enforces one floor preserving $d$'s current score. One
synchronous iteration solves all $n^2$ protected--focal problems from the
same old score vector and then applies
$$
\eta_j^{(t+1)}
=
\frac{1}{n}\sum_d g_{dj}(\eta_d^{(t)}).
$$
The equal mean includes self and is the protocol's native payoff/update; it
does not belong to a free $A$-axis aggregation selector. $P$ owns the
paired LP family, simultaneous update, stopping and equilibrium claims, while
$C$ owns the participating players and $T/E/M/V$ retain the fixed CCR
account. Any later league-table or sensitivity analysis belongs to $A$.

The pair table has rows `protected_dmu_id` and columns `focal_dmu_id`. It is
not an ordinary appraiser--evaluatee cross-efficiency matrix: every cell may
have different weights rather than one appraiser's weights being reused
across a row. Implementations must retain initialization and update history,
distinguish source-claimed score uniqueness from multiplier uniqueness,
verify a fresh fixed-point residual after the adjacent-iterate stopping test,
and treat a two-cycle, failed subproblem, or maximum-iteration exit as
non-equilibrium. These protocols may reuse multiplier kernels, but they are
Level D distinct and cannot share an unqualified `secondary="game"`,
`secondary_goal="game"`, or freely chosen aggregation spelling.

Governance is also an evaluation protocol rather than a production-graph
edge. DEAPack represents it as
`GovernanceSpec(players, authority, objectives, move_order, information,
solution_concept)`. The same physical series or network graph may be run by a
single coordinator, a leader--follower hierarchy, non-cooperative divisions,
or a bargaining procedure. Those choices can change objectives, constraints,
action order, and solver form without changing any material handoff. The
graph therefore stores transformation and link balance; governance stores who
may choose the joint plan and by what solution concept.

Nor is a pessimistic multiplier appraisal automatically a production
frontier. Worst-practice envelopes, least-favourable multiplier weights, and
double-frontier combinations are source-qualified ranking mechanisms. They
are also unrelated to a robust-optimization model that evaluates uncertain
data under an adverse realization. See
[Wang, Chin, and Yang (2007)](https://doi.org/10.1057/palgrave.jors.2602205).

### 10.1 A best measure value is not automatically strong efficiency

The fitted measure and the operational status of its target are reported
separately. A radial factor of one means that no further common proportional
change is available. A directional distance of zero means that no further
amount of the declared improvement programme is available. Either result can
coexist with a resource excess or output shortfall outside that restricted
plan.

DEAPack therefore distinguishes:

- **measure efficiency**, defined by the native radial, directional,
  additive, SBM, or other criterion;
- **Pareto--Koopmans efficiency**, which requires that no feasible plan uses
  no more of every input and produces no less of every output while improving
  at least one component; and
- **target status**, including whether the returned plan is feasible, weakly
  or strongly efficient, closest/furthest under a declared norm, or merely
  one member of a multiple-optimum set.

A lexicographic slack-completion phase is an evaluation protocol, not a new
distance measure. If that phase is skipped or is not valid for the composed
technology, the strong-efficiency field remains unspecified rather than
inheriting the best native score. Network and dynamic results apply the same
rule jointly: process, link, and carry-over targets must satisfy the system
account before strong system or component efficiency is claimed.

## 11. Layer 10: analytical operator

The operator determines what is calculated from one or more fitted
technology/measure combinations:

- static efficiency, slacks, peers, and targets;
- scale efficiency, returns to scale, capacity, or congestion;
- ranking, cross-appraisal, and super-efficiency;
- marginal valuations and abatement-cost indicators;
- productivity indexes and named decompositions;
- group/meta-frontier gaps;
- resource allocation, merger, inverse-DEA, fixed-sum, or bargaining
  scenarios;
- sensitivity, influence, and robustness analysis.

Productivity is therefore not a special subclass of a static DEA model. It is
an operator that requests a controlled set of within- and cross-period
evaluations and combines their native values according to a named index.

## 12. Layer 11: uncertainty and inference

Ordinary DEA conditions on the observed sample and is deterministic. It does
not make sampling uncertainty disappear. Five distinct sources or structures
must be identified before a procedure is selected:

| Source or structure | Question answered |
|---|---|
| sampling uncertainty | how would the estimated boundary or score vary under a justified population-sampling design? |
| data or measurement uncertainty | what follows when recorded inputs and outputs are noisy, bounded, interval-valued, or fuzzy? |
| production risk | which plans are feasible before the state of nature or another stochastic production condition is realized? |
| robust scenario uncertainty | what performance or feasibility is guaranteed over a declared uncertainty set or scenario family? |
| dependence | how must estimation or inference change when observations are spatially, serially, clustered, or network dependent? |

Bootstrap bias correction, confidence intervals, structure tests,
chance-constrained technologies, state-contingent technologies, interval and
fuzzy formulations, robust counterparts, and dependence-aware resampling are
therefore separate procedures. A numerical solver tolerance is not an
uncertainty model. These methods change the evidentiary basis, uncertainty
model, or permitted inferential claim and must retain distinct result metadata
and diagnostics. Conditional DEA/FDH, order-$m$, and order-$\alpha$ belong to
the estimator axis in Layer 5; they appear below only to make compatibility
between estimators and inference explicit.

An uncertainty specification has four independent parts:

1. **Benchmark formation**: full DEA/FDH frontier, order-$m$,
   order-$\alpha$, conditional frontier, group frontier, or meta-frontier.
2. **Source of variation**: sampling, influential/error-contaminated
   observations, operating environment, known technology groups, random
   measurement, interval information, fuzzy information, production states,
   a declared uncertainty set, or cross-observation dependence.
3. **Permitted claim**: sample description, population confidence statement,
   conditional association, posterior statement, or worst-case operational
   guarantee.
4. **Managerial control**: which quantities can be changed, which conditions
   define fair comparison, and which quantities represent uncertainty rather
   than improvement targets.

This prevents several damaging mergers:

- a full-frontier bootstrap is not repeated naive row resampling;
- a Simar--Wilson second stage under separability is not conditional DEA,
  which allows operating conditions to alter attainable opportunities;
- order-$m$ and order-$\alpha$ are different partial-frontier estimators;
- influence diagnostics identify observations for audit, not automatic
  deletion;
- state-contingent production is not measurement error, a dynamic stock, or a
  chance constraint;
- spatial peer eligibility, spatial conditioning, physical spillovers, and
  spatially dependent inference are not one “spatial DEA” model;
- chance constraints, interval data, fuzzy membership, robust optimization,
  and Bayesian posterior uncertainty make different claims.

Every inferential procedure declares the data-generating assumptions and the
model/measure combinations for which its validity has been established. A
generic resampler must not imply that inference is valid for every new DEA
variant.

## 13. Four levels of equivalence

Historical names are merged only after an equivalence audit.
An equivalence level belongs to a directed relationship between two
specifications along a stated dimension; it is not an intrinsic label attached
to one method forever. The same network-SBM entry can have a Level C
relationship to black-box SBM because it reuses a measure over a different
technology, and its network graph compiler can have a Level D relationship to
a black-box compiler because the production system is structurally distinct.
Each registered relationship therefore has a target, conditions, dimension,
and evidence.

The relationship itself is typed as `alias`, `exact_score_transform`,
`specialization_of`, `preset_of`, `variant_of`, `composes`, `requires`,
`shares_compiler`, `incompatible`, or `contrasts_with`. A–D applies only when
two complete executable study specifications are being compared. Dependency
edges such as a decomposition `composes` a cost model, or a bootstrap
`requires` a supported estimator, do not receive a manufactured equivalence
level.

### Level A — exact alias or representation

Two labels use the same feasible set and objective, possibly after an exact
parameter or score transformation. They share one canonical implementation.

Examples:

- CCR input DEA = CRS input-oriented radial DEA;
- BCC output DEA = VRS output-oriented radial DEA;
- envelopment and multiplier forms are primal/dual representations when all
  restrictions correspond exactly;
- Farrell output expansion $\phi$ and its bounded display efficiency
  $1/\phi$ are representations of the same solution, not two models.

Aliases retain their historical citation and native score convention.

### Level B — shared technology, distinct measure

The attainable set is the same, but the performance criterion, operating
counterfactual, normalization, or economic objective differs. The technology
compiler is shared; public measures and interpretation remain distinct.

Examples: radial DEA, additive DEA, RAM, EBM, Russell measures, cost
efficiency, and Tone's input-, output-, and non-oriented SBM fitted to the
same VRS observations. A local RTS classification and quantitative
scale-elasticity bounds can also use the same fitted technology while
answering different questions.

### Level C — shared measure, distinct technology or benchmark

The objective has the same algebraic form, but the account of attainability or
the comparison population differs. The measure engine may be reused, while
the fitted study and result name remain distinct.

Examples:

- a DDF under ordinary weak disposability versus a DDF under by-production;
- black-box SBM versus network SBM;
- contemporaneous versus global directional distances;
- group-frontier versus meta-frontier efficiency;
- standard FDH versus a scale-extrapolated FDH technology that still forbids
  convex mixing of activities.

### Level D — distinct system, estimator, or inferential design

The production system, data-generating process, or estimator changes
fundamentally. A separate compiler or analysis family is required.

Examples include convex DEA versus FDH; FDH versus integer-replication FRH;
FRH versus its continuous CCR relaxation; black-box versus general-network
technologies; static versus dynamic carry-over systems; a full frontier
versus order-$m$ or conditional frontier estimators; a deterministic
technology versus a stochastic or robust counterpart; and an uncorrected
point estimate versus a supported bootstrap inferential procedure. Fried's
DEA--SFA--DEA adjustment workflow is likewise not an alias for either a
Simar--Wilson second stage or conditional DEA because it changes the
observations used in the final frontier fit under a parametric noise model.

### 13.1 Required equivalence evidence

A proposed alias must document:

1. equality of the feasible technologies;
2. equality of the objective or the exact value transformation;
3. correspondence of optimal targets and peers;
4. identical treatment of scale, disposability, and the reference set;
5. the domain on which the equivalence holds;
6. regression or property tests against both formulations.

Equal rankings in one dataset are not evidence of model equivalence.
Similarly, sharing an LP matrix does not make two economic measures the same.

A conditional reduction is narrower than an alias. On a matched closed
two-process CRS graph, the Chen--Cook--Li--Zhu primary system programme is an
exact reduction of the Cook--Zhu--Bi--Yang general additive programme. That
fact supports one shared mathematical kernel and a regression identity. It
does not transfer Chen's VRS process intercepts, secondary stage-attribution
selection, or Lim--Zhu projection to an arbitrary open graph, so the two
source-qualified public methods remain distinct.

## 14. Historical labels as compositions

The following examples show how familiar labels map into the framework. A row
is a preset only when the historical definition fixes a sufficiently complete
composition. Generic labels such as SBM, environmental DDF, and bootstrap DEA
remain a family or procedure until their technology, measure, reference, and
other required choices are supplied.

| Historical label | Canonical composition |
|---|---|
| CCR-I | black box + ordinary convex CRS technology + contemporaneous reference + input radial measure + static analysis |
| BCC-O | black box + ordinary convex VRS technology + contemporaneous reference + output radial measure + static analysis |
| FDH-I | black box + non-convex free-disposal technology + input radial measure + static analysis |
| RAM | black box + convex VRS technology + range-normalized additive measure |
| SBM | selected technology + fractional slacks-based measure |
| environmental DDF | joint good/bad technology + declared resource/service/emission programme + static analysis |
| by-production DDF | intended/residual subtechnologies with separate intensities + minimum common improvement step + fixed-direction CRS source profile; other RTS/direction/reference settings are labelled extensions |
| Kalhor--Kazemi Matin environmental network radial DEA | general process graph + external/internal desirable and undesirable product accounts + producer-specific ordinary-intermediate balances + activity-specific weak-disposal technology + input-radial system measure |
| network SBM | process graph + link balances + process technologies + slacks-based system/division measure |
| general additive network DEA | declared open-DAG process graph + shared link valuation + CRS process restrictions + endogenous virtual-process-input-share aggregation |
| dynamic SBM | temporal graph + typed carry-overs + intertemporal slacks-based measure |
| Malmquist | period technologies + within/cross-period radial distance tasks + named multiplicative operator |
| global ML | global environmental technology + environmental directional tasks + named productivity operator |
| meta-frontier efficiency | group and meta technologies + chosen measure + technology-gap operator |
| bootstrap DEA | base DEA estimator + resampling design + bias/inference operator |

The registry may expose a historical constructor for convenience, but every
result stores the expanded canonical composition.

## 15. Software consequences

The package is organized around reusable compilers, not one class per paper:

```text
DecisionContext
      +
ProductionGraph + DataRoles
      |
      v
TechnologyCompiler -- EstimatorCompiler -- ReferencePolicy
      |
      v
PerformanceCompiler + ValuationSpec
      |
      v
EvaluationProtocol
      |
      v
TaskBatch -- SolverBackend
      |
      v
DEAResult -- AnalysisOperator -- UncertaintyProcedure
```

Reused components must preserve sparse matrices and avoid per-observation
Python reconstruction. A compiled technology is cached by its structural
fingerprint; comparison-population and temporal-information policies generate
stable candidate subsets; evaluation exclusions operate on those subsets; a
performance criterion supplies DMU-specific objectives and right-hand sides;
valuation and evaluation protocols add declared restrictions or secondary
tasks; an analytical operator batches the necessary evaluations.

Composition is fail-closed. A requested combination is rejected unless its
property profile is marked supported or its stated conditions have been
satisfied. The normative compatibility and promotion rules are maintained in
`specs/COMPATIBILITY_MATRIX.md`.

The public result records at least:

- the expanded study specification;
- the historical preset/alias, if one was requested;
- native and standardized values without conflating them;
- targets, slacks, peers, intensities, duals, and component results where
  meaningful;
- comparison-population membership, temporal information set, evaluation
  exclusions, fitted peers, and benchmark vintage;
- solver, feasibility, and numerical diagnostics;
- statistical uncertainty and resampling provenance where applicable.

## 16. Book and documentation consequences

The book is organized by economic and managerial questions:

1. what performance means and how a credible comparison is designed;
2. how current operations can save resources or expand valued outcomes;
3. how prices, priorities, quality, and scale change the assessment;
4. how joint production and undesirable outcomes are represented;
5. how performance and production opportunities change over time;
6. how performance shortfalls are attributed inside networks and across periods;
7. how heterogeneity and sampling uncertainty affect claims;
8. how results support planning without being mistaken for causal evidence.

The book teaches the principal, transferable model families deeply. The
package Documentation and source registry provide the exhaustive preset and
API catalogue. A paper-specific direction, weight, normalization, reference
window, decomposition, application constraint, or other technical variation
does not enter the book merely because it has a stable name or a reproducible
implementation. Such leaves remain in the source-backed technical catalogue;
the handbook appendix is not an overflow catalogue for them.

Every chapter and model-reference page begins with:

- the decision question;
- the required production story and data roles;
- the assumptions defining attainable best practice;
- the improvement plan or economic objective;
- the claims the result does and does not support.

Geometry and optimization explain the formal machinery after the economic
question and production account are clear; they do not supply the substantive
interpretation.
