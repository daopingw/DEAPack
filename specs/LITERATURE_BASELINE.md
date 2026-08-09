# Literature Baseline for the Companion Book

This register governs the theoretical provenance and editorial architecture of the
English manuscript. It is a working research document, not a substitute for the
bibliography. A method enters the book only after its defining contribution has been
checked against the original source and reconciled with the notation and computational
contract in `CONVENTIONS.md`.

## Core corpus

### Foundations of production and efficiency measurement

- Debreu (1951), *The Coefficient of Resource Utilization*.
- Koopmans (1951), *An Analysis of Production as an Efficient Combination of
  Activities*.
- Shephard (1953), *Cost and Production Functions*.
- Farrell (1957), *The Measurement of Productive Efficiency*.

These works establish the conceptual separation among productivity, technical
efficiency, allocative efficiency, distance to a technology, and Pareto--Koopmans
efficiency. The book should not begin with the CCR acronym as though efficiency
measurement started in 1978.

### Classical DEA and empirical technologies

- Charnes, Cooper, and Rhodes (1978), the CCR multiplier and envelopment formulations.
- Banker, Charnes, and Cooper (1984), the convex empirical technology, variable returns
  to scale, and the separation of technical and scale inefficiency.
- Charnes et al. (1985), Pareto--Koopmans efficiency and the foundations of DEA
  production functions.
- Charnes, Cooper, Seiford, and Stutz (1982), the original C2S2
  multiplicative efficiency model
  ([doi:10.1016/0038-0121(82)90029-5](https://doi.org/10.1016/0038-0121(82)90029-5)).
- Charnes, Cooper, Seiford, and Stutz (1983), unit-invariant multiplicative
  efficiency and piecewise Cobb--Douglas envelopment
  ([doi:10.1016/0167-6377(83)90014-7](https://doi.org/10.1016/0167-6377(83)90014-7)).
- Färe, Grosskopf, and Lovell (1985), *The Measurement of Efficiency of Production*.
- Kerstens and Vanden Eeckaut (1999), returns to scale under non-convex FDH
  technologies.
- Banker and Morey (1986a), exogenously fixed inputs and outputs
  ([doi:10.1287/opre.34.4.513](https://doi.org/10.1287/opre.34.4.513)).
- Banker and Morey (1986b), categorical variables and admissible peer groups
  ([doi:10.1287/mnsc.32.12.1613](https://doi.org/10.1287/mnsc.32.12.1613)).
- Cooper, Seiford, and Tone (2007), *Data Envelopment Analysis*.
- Ray (2004), *Data Envelopment Analysis: Theory and Techniques for Economics and
  Operations Research*.
- Cook, Tone, and Zhu (2014), “Data Envelopment Analysis: Prior to Choosing a
  Model” ([doi:10.1016/j.omega.2013.09.004](https://doi.org/10.1016/j.omega.2013.09.004)).

The central editorial lesson is to begin with the producer's economic problem: what is
produced, which resources and outputs are discretionary, what information managers
possess, and which comparison population represents attainable practice. The
production possibility set, distance measure, and empirical linear program then
formalize that problem. Multiplier and envelopment forms should be related through
duality, not presented as unrelated models. Historical labels should be retained for
literature search but grouped by mathematical equivalence.
Standard FDH and scale-extrapolated FDH-CRS/NIRS/NDRS remain different
technology specifications: the latter rescale individual observed activities
without admitting the convex mixing used by ordinary DEA.
The two early multiplicative formulations share one historical and
computational family but retain separate source presets. The 1982 model is
conic in log quantities, requires every quantity to exceed one, and is not
unit invariant. The 1983 model adds a free log intercept, equivalently a
sum-to-one intensity identity, admits all strictly positive quantities, and
combines peer practices geometrically. Neither is ordinary physical-space
CRS/VRS or a recipe for logging data before fitting CCR/BCC. Exponents are
frontier weights, not prices, causal elasticities, or marginal products.

### Slacks and nonradial measures

- Charnes et al. (1985), the VRS unit-weight direct additive model in
  equations (4.5)--(4.6), its Pareto--Koopmans empirical frontier, and the
  distinct evaluated-observation normalization in equation (5.7).
- Cooper, Park, and Pastor (1999), RAM and range-normalized additive inefficiency.
- Färe and Lovell (1978), input- and output-specific Russell efficiency.
- Pastor, Ruiz, and Sirvent (1999), the enhanced Russell graph measure
  ([doi:10.1016/S0377-2217(98)00098-8](https://doi.org/10.1016/S0377-2217(98)00098-8)).
- Tone (2001), the direct input/output-oriented and fractional non-oriented
  slacks-based measures
  ([doi:10.1016/S0377-2217(99)00407-5](https://doi.org/10.1016/S0377-2217(99)00407-5)).
- Chambers, Chung, and Färe (1996), directional distance functions and their
  translation and duality properties.
- Bogetoft and Hougaard (1999), potential non-proportional improvements and
  the foundation of multi-directional efficiency analysis.

These methods should not be narrated as cosmetic corrections to a radial score. They
encode different analyst-declared operating counterfactuals. The classic
additive model sums absolute input excess and output shortfall with unit
weights; DEAPack's fixed positive weights are a declared package extension
unless a separate source-qualified leaf is established. RAM evaluates those
adjustments relative to observed sample ranges; SBM evaluates them relative to the
unit's own operating scale; DDF evaluates a declared package of resource savings,
service expansion, or environmental improvement. The associated geometry is useful
for derivation, but the prose must explain what the analyst has specified and whether
a manager, regulator, or other institution has adopted it. Unit invariance,
translation invariance, sample dependence, positivity, and direction scaling must be
derived from the selected normalizer rather than asserted for “nonradial DEA” as a
whole.
On the standard strictly positive domain with matched technology and weights,
the enhanced Russell graph formulation of Pastor, Ruiz, and Sirvent (1999)
and Tone's standard non-oriented SBM are one canonical linear-fractional
model. The book preserves both historical search names but does not create a
second solver or method identity.

Tone's three orientations share an empirical technology and computational
kernel but not a managerial criterion. Input orientation asks how much
normalized resource excess can be removed while maintaining services; output
orientation asks how much normalized service expansion is attainable without
requiring more resources; the non-oriented form values both accounts. A best
single-orientation score certifies only its valued side, while the target on
the other side is solver-selected. Tone's Table 2 supplies the published
five-unit non-oriented CRS score/slack oracle reproduced by
`sbm_slack_contrast`; no published numerical oracle has yet been located for the
input- or output-oriented form. Zero- and signed-data extensions are later
models, not a preprocessing version of Tone's standard positive-data domain.

### Prices, preferences, and non-production uses of DEA machinery

- Chambers, Chung, and Färe (1998), directional profit functions and
  normalized Nerlovian efficiency.
- Fukuyama (2000), DEA returns to scale and quantitative scale elasticity.
- Yang and Liu (2017), directional returns to scale and directional scale
  elasticity.
- Allen et al. (1997), weight restrictions and value judgements in DEA.
- Thompson et al. (1990), AR-II cross-side multiplier restrictions
  ([doi:10.1016/0304-4076(90)90049-Y](https://doi.org/10.1016/0304-4076(90)90049-Y)).
- Wong and Beasley (1990), virtual input/output share restrictions
  ([doi:10.1057/jors.1990.120](https://doi.org/10.1057/jors.1990.120)).
- Podinovski and Bouzdine-Chameeva (2013), consistency and implied
  free/unlimited production under weight restrictions
  ([doi:10.1287/opre.1120.1122](https://doi.org/10.1287/opre.1120.1122)).
- Färe, Grosskopf, and Lovell (1985), congestion through source-qualified
  input-disposability technologies.
- Cooper, Deng, Huang, and Li (2002), one-model slack-based congestion
  ([doi:10.1016/S0038-0121(02)00008-3](https://doi.org/10.1016/S0038-0121(02)00008-3)).
- Cherchye et al. (2007), Benefit-of-the-Doubt composite indicators.

The book separates raw attainable profit gaps from price-normalized
directional inefficiency. It also distinguishes restrictions that express
acceptable valuations from statements that modify attainable production.
Likewise, a qualitative IRS/CRS/DRS label, a scale-efficiency ratio, and a
possibly interval-valued scale elasticity are not interchangeable outputs. A
directional elasticity must report the non-proportional management change
whose response it measures.
Benefit-of-the-Doubt models receive explicit coverage as an indicator
aggregation use of DEA multiplier machinery; without a production
interpretation, their scores are not technical efficiency.

### Broad efficiency and productivity texts

- Coelli, Rao, O'Donnell, and Battese (2005), *An Introduction to Efficiency and
  Productivity Analysis*.
- Fried, Lovell, and Schmidt, eds. (2008), *The Measurement of Productive Efficiency
  and Productivity Change*.
- Daraio and Simar (2007), *Advanced Robust and Nonparametric Methods in Efficiency
  Analysis*.
- Cooper, Seiford, and Zhu, eds. (2011), *Handbook on Data Envelopment Analysis*.
- Cook and Zhu, eds. (2014), *Data Envelopment Analysis: A Handbook of Modeling
  Internal Structure and Network*.
- Mergoni, Emrouznejad, and De Witte (2025), “Fifty years of Data Envelopment
  Analysis.”

These books supply three complementary design principles. First, production economics
and measurement concepts precede individual estimators. Second, diagrams, small
numerical examples, and real applications are used together. Third, advanced material
does not merely add model variants: it addresses data quality, sampling variation,
robust frontiers, statistical inference, and the limits of interpretation.
The original COOPER framework of Emrouznejad and De Witte
([2010](https://doi.org/10.1016/j.ejor.2010.07.025)) and its current synthesis
in Mergoni, Emrouznejad, and De Witte
([2025](https://doi.org/10.1016/j.ejor.2024.12.049)) supply a complementary
empirical-project workflow: concepts and objectives, data structure,
operational model, comparison model, evaluation, and deployment.
The DEAPack unified framework does not replace that workflow; it provides the
compositional grammar for the fitted model inside it.

### Productivity change

- Caves, Christensen, and Diewert (1982), distance-function productivity indexes.
- Färe et al. (1994), DEA computation of the geometric Malmquist index and its
  efficiency-change/technical-change decomposition.
- Chambers (2002), exact nonradial and Luenberger productivity measurement.
- Pastor and Lovell (2005), the global Malmquist index.
- Pastor, Asmild, and Lovell (2011), the biennial Malmquist index.
- O'Donnell (2012), multiplicatively complete productivity indexes and Färe--Primont
  decomposition.
- Aparicio, Pastor, and Zofío (2013), consistency corrections for the
  Malmquist--Luenberger technical-change component.

Every productivity chapter must distinguish the observation being evaluated from the
reference technology. Four-distance indexes, common-reference indexes, and additive
indicators should first be derived from their distance functions; software field names
come afterward. Index properties such as circularity, infeasibility, technical regress,
and sensitivity to adding future observations are part of the estimand, not peripheral
implementation notes.

Malmquist, Hicks--Moorsteen, Färe--Primont, an ordinary Luenberger indicator, and a
Luenberger--Hicks--Moorsteen index are not interchangeable labels. The book must state
whether a quantity is a local technical-performance indicator or a complete TFP index
under declared aggregator axioms. Competing FGNZ, Ray--Desli, Balk, and scale/mix
decompositions retain source-qualified component names.

The same aggregate-quantity theory also supplies a cross-sectional TFP
efficiency account. Its technical, scale, and mix components answer a broader
question than Farrell technical or radial scale efficiency, so they remain a
named operator rather than being inferred from two radial scores.

Their interpretation must remain economic. Efficiency change is a change in a
producer's performance relative to the period-specific best-practice benchmark; it is
not, by itself, proof of better management. Technical change is a change in attainable
production opportunities represented by the benchmark technology; it is not, by
itself, proof of invention or diffusion. “Catch-up” and “frontier shift” may be noted as
historical shorthand, but they must not carry the explanation.

### Undesirable outputs and environmental productivity

- Chambers, Chung, and Färe (1996), directional distance functions.
- Chung, Färe, and Grosskopf (1997), weak disposability, null jointness, the
  environmental directional distance function, and the Malmquist--Luenberger index.
- Oh (2010), the global Malmquist--Luenberger index and best-practice-gap change.
- Murty, Russell, and Levkoff (2012), by-production technologies.
- Coelli, Lauwers, and Van Huylenbroeck (2007), material-balance environmental
  efficiency.
- Scheel (2001), review of undesirable-output modeling.
- Kuosmanen (2005), weak-disposability technology with activity-specific abatement.
- Dakpo, Jeanneaux, and Latruffe (2016), critical review of pollution-generating
  technologies.
- Rødseth (2016), relationships and limits among material-balance approaches.

The environmental part must begin with joint production and the physical or economic
meaning of disposability. A column of emissions cannot be classified mechanically as
an input or an output without changing the technology. Direction choice, bad-output
constraints, null jointness, abatement activity, and material balance must remain
visible in both the model name and the result metadata.

Directional language must be stated as a policy or operating counterfactual. For
example, $(0,y,b)$ asks whether current inputs could support proportionally more
desirable output and less pollution under the maintained technology. Calling it an
“arrow” is not an interpretation; the book must identify the implied production target,
the abatement burden, and the decision-maker for whom that target is meaningful.

The empirical technologies require explicit separation. Weak disposability is an
economic axiom, not one uniquely determined equality: common-factor and
activity-specific constructions can imply different opportunities. Null jointness is a
separate axiom, and pollutant-level selective disposal may be required. Tone's
separable undesirable-output SBM uses a bad-output contraction slack that encodes
strong disposal. By-production, Coelli-style material-input efficiency, weak-$G$
material conservation, and factorial/multi-equation systems describe different
production accounts. They may share data or a directional/additive objective, but one
cannot be obtained by changing the score formula while leaving the production set
unnamed.

### Internal and intertemporal production

- Färe and Grosskopf (2000), network DEA.
- Kao and Hwang (2008), relational efficiency decomposition for a two-stage
  process
  ([doi:10.1016/j.ejor.2006.11.041](https://doi.org/10.1016/j.ejor.2006.11.041)).
- Chen et al. (2009), additive efficiency decomposition for two-stage
  processes
  ([doi:10.1016/j.ejor.2008.05.011](https://doi.org/10.1016/j.ejor.2008.05.011)).
- Tone and Tsutsui (2009), network SBM.
- Kao (2014), systematic review of network DEA.
- Lewis and Sexton (2004), sequential improvement through organizational
  sub-DMUs.
- Park and Park (2009), multi-period aggregative efficiency without a state
  transition.
- Tone and Tsutsui (2010), dynamic SBM with typed carry-overs.
- Tone and Tsutsui (2014), dynamic network SBM.
- Mariz, Almeida, and Aloise (2018), review of dynamic DEA.

“Two-stage,” “network,” and “dynamic” describe production systems, not one universal
score. A network model must state its nodes, intermediate links, shared resources,
node technologies, intensity coupling, link conservation, system aggregator, and
governance. Independent stage models are not network DEA because their targets need
not balance. Dynamic carry-over models and intertemporal capital/investment models
must remain distinct from period-by-period DEA, window analysis, and Malmquist
productivity indexes.

### Statistical status and empirical protocols

- Banker (1993), statistical foundations of DEA estimators.
- Simar and Wilson (1998, 1999), bootstrap inference for DEA scores and Malmquist
  indexes.
- Simar and Wilson (2002), bootstrap tests of returns to scale
  ([doi:10.1016/S0377-2217(01)00167-9](https://doi.org/10.1016/S0377-2217(01)00167-9)).
- Dyson et al. (2001), empirical pitfalls and reporting protocols.
- Cook and Seiford (2009), methodological development after the first three decades of
  DEA.
- Simar, Vanhems, and Wilson (2012), inference for directional-distance estimators.
- Cazals, Florens, and Simar (2002), order-$m$ partial frontiers.
- Daraio and Simar (2005), conditional efficiency with operating conditions.
- Simar and Wilson (2007), the separately registered Algorithm 1 and
  Algorithm 2 second-stage procedures under separability
  ([doi:10.1016/j.jeconom.2005.07.009](https://doi.org/10.1016/j.jeconom.2005.07.009)).
- Fried, Lovell, Schmidt, and Yaisawarng (2002), the source-qualified
  DEA--SFA--DEA three-stage data-adjustment workflow.
- Olesen and Petersen (2016), the three distinct stochastic-DEA branches and
  the boundary among stochastic deviations, integrated noise/error, and
  stochastic production sets
  ([doi:10.1016/j.ejor.2015.07.058](https://doi.org/10.1016/j.ejor.2015.07.058)).
- Cooper, Park, and Yu (1999), imprecise data envelopment analysis under
  explicit bound/order/ratio information
  ([doi:10.1287/mnsc.45.4.597](https://doi.org/10.1287/mnsc.45.4.597)).
- Ehrgott, Holder, and Nohadani (2018), source-qualified robust DEA under
  explicit uncertainty sets
  ([doi:10.1016/j.ejor.2018.01.005](https://doi.org/10.1016/j.ejor.2018.01.005)).

DEA is deterministic conditional on the observed sample but its frontier is an
estimator when data are viewed as sampled. The book must therefore distinguish solver
precision from statistical uncertainty and descriptive second-stage analysis from
causal identification.

The book also distinguishes full-frontier bootstrap, structure tests, Simar--Wilson
second stage, conditional DEA/FDH, order-$m$, order-$\alpha$, influence diagnostics,
chance-constrained DEA, interval/IDEA, fuzzy DEA, robust optimization, and experimental
Bayesian DEA. These methods represent different benchmark constructions, sources of
uncertainty, and permitted claims. A generic resampler, “robust” flag, or confidence
column cannot merge them.

Fried's three-stage workflow is neither a Simar--Wilson second stage nor
conditional DEA. It uses a parametric stochastic frontier to decompose
first-stage slacks, changes the observations used by the final DEA fit, and
therefore requires an explicit distributional specification and a retained
pre-/post-adjustment audit trail. The book presents it as a historically
important but strongly assumption-dependent hybrid, not as a default cure for
operating-environment heterogeneity.

## Thematic review programme

The literature programme is organized as nine maintained review streams:

1. static technical and economic measurement;
2. environmental production and undesirable outcomes;
3. productivity indexes and decompositions;
4. network and dynamic production;
5. additive network performance-attribution accounts;
6. network SBM;
7. weight restrictions, special data, and heterogeneous comparison; and
8. statistical foundations, partial/conditional frontiers, inference, and
   uncertain DEA; and
9. decision support, including inverse DEA, coordinated allocation,
   fixed-sum systems, merger analysis, bargaining, and scenario design.

The cross-domain coverage and gap ledger is maintained separately in
[`METHOD_COVERAGE_AUDIT.md`](METHOD_COVERAGE_AUDIT.md).

The maintained review files live in [`reviews/`](reviews/). Every evidence
row uses the same fields:

```text
economic question
technology and estimator
measure or loss function
returns to scale
data and time structure
native score
exact aliases
distinct variants
data domain
failure modes
solver form
defining source
published numerical oracle
package recipe
book location
```

For every stream, the review must reconcile defining papers with authoritative
handbooks or mature reviews, reproduce at least one published numerical example,
verify claimed properties and known failure domains, and map each supported
formulation to its canonical specification, implementation, tests, book treatment,
and API documentation. This is a prospective and continuously maintained review
programme; the present register does not claim that a completed systematic review
already exists.

## The supplied manuscript and its role

The user-supplied `manuscript.pdf` is the accepted-workflow precursor to Wang, Du, and
Zhang (2022), “Measuring technical efficiency and total factor productivity change
with undesirable outputs in Stata,” *The Stata Journal* 22(1), 103--124,
doi:10.1177/1536867X221083886.

Its strongest reusable design choices are:

- one notation system for inputs, desirable outputs, undesirable outputs, directions,
  and reference intensities;
- a progression from environmental technology to radial/nonradial directional
  distances, efficiency, productivity change, and computation;
- an explicit diagram for alternative directions in good--bad output space;
- a compact visual comparison of contemporaneous, sequential, window, biennial, and
  global reference technologies;
- command examples that expose both overall measures and variable-specific adjustment
  factors;
- an explicit warning that DEA-type estimates are sensitive to sampling variation.

The companion book should retain this theory--program--application closure while going
far beyond a software article. It should give fuller derivations, explain why competing
technologies differ, integrate diagnostics and visualization, and connect each method
to the wider efficiency and productivity literature.

## Editorial consequences for the current draft

The existing draft is readable but not yet handbook quality. The English rewrite will:

1. replace casual or repeated metaphors with precise production-economic language;
2. add the Debreu--Koopmans--Farrell--Shephard lineage before CCR and BCC;
3. distinguish technologies, measures, programs, and reported scores consistently;
4. expand foundational chapters before adding more advanced model families;
5. cite original contributions at the exact point where assumptions or decompositions
   enter;
6. number and cross-reference important technologies, measures, and programs;
7. use figures for production choices and reference technologies, with prose that
   interprets them in economic and managerial terms rather than narrating shapes;
8. turn code examples into reproducible empirical arguments rather than API snippets;
9. add data design, comparability, uncertainty, robustness, and reporting as continuous
   themes rather than a late disclaimer;
10. keep full parameter reference material in the package Documentation.

## Minimum source audit for a new method

Before adding a method, record:

- the original defining source and any materially different later formulation;
- the economic technology and all disposability, convexity, and returns-to-scale
  assumptions;
- the orientation, normalization, value range, and invariance properties of the
  measure;
- known equivalences and historical aliases;
- feasibility conditions, degeneracy, and statistical status;
- the decomposition identity or dual interpretation, if applicable;
- one deterministic dataset with a hand-checkable theoretical result;
- one empirical use case and the assumptions that limit its interpretation.

This audit is deliberately stricter than adding a class and an API page. The book and
package are intended to become a dependable map of the field, so method coverage must
remain subordinate to conceptual accuracy.
