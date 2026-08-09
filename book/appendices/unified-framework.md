# Choosing a DEA Study: A Reader's Map

DEA has accumulated many model names. Some are genuinely different methods;
others are historical names for the same production assumptions and
performance criterion. Memorizing acronyms is therefore a poor way to design a
study. A better starting point is the economic question: **what comparison
would be credible and useful for the organization being evaluated?**

The map in this appendix begins with the organization rather than the model
catalogue. It asks how work is organized, which operating experiences are credible
benchmarks, what improvement the responsible manager could pursue, and how strong a
conclusion the available evidence can sustain. Those choices determine the economic
comparison; the familiar model name follows from them. This approach complements
established guidance for conducting nonparametric performance studies and the broader
DEA handbook literature
{cite:p}`emrouznejad2010cooper,cooper2011handbook,cook2009`.

```{figure} ../_static/figures/method-atlas-routes.svg
:name: fig-method-atlas-routes
:alt: A performance question branches to one-process production, undesirable outcomes, internal networks, intertemporal state, and productivity change, with valuation, evaluation protocol, and uncertainty treated as cross-cutting choices
:width: 100%

The principal routes through the book begin with the organization's production
story. Valuation, evaluation protocol, and evidentiary design remain visible across
every route; they are not additional model families.
```

## Begin with the production story

The same data table can support different comparisons, so the first choice is
how the organization's production commitments should be represented. The
smallest family that preserves the consequential commitment is usually the
clearest starting point.

| Production story | Principal DEA family | Choice that changes the model |
|---|---|---|
| One organization converts external resources into final desirable outcomes | radial DEA or FDH; additive, SBM, or directional accounts when the improvement criterion requires them | Is proportional adjustment meaningful, are convex mixtures credible, and must variables improve separately? |
| Desirable production jointly creates pollution, failures, or another burden | environmental directional distance or undesirable-output SBM | What production restriction makes burden reduction credible rather than treating the burden as an ordinary input? |
| Several processes exchange intermediate products inside one organization | network DEA or network SBM | Which process creates and receives each handoff, and must its observed quantity be inherited or jointly redesigned? |
| Current decisions create assets, capacity, or obligations for later periods | dynamic DEA or dynamic SBM with explicit carry-overs | What crosses the period boundary, who controls it, and how are the horizon boundaries treated? |
| The research question concerns performance change between periods | Malmquist, Luenberger, environmental-productivity, or Hicks--Moorsteen analysis | Which dated or common information set defines best practice, and what change identity is being reported? |
| Declared groups face different production opportunities | group-frontier and metafrontier analysis | Is the study separating within-group operating performance from a gap between represented opportunity sets? |

Network, dynamic, and environmental are not decorative adjectives. An internal
delivery is not a final social outcome, a carry-over is not an ordinary annual
input, and an undesirable output does not become desirable because its sign is
changed.

## Four groups of questions

### 1. Whose performance, and which operating decisions?

Begin by defining the unit of analysis and its boundary.

- Is the unit a plant, hospital, branch, municipality, programme, or complete
  multi-period history?
- Which resources and outcomes are under managerial control?
- Which quantities are inherited, mandated, quasi-fixed, or determined by the
  operating environment?
- Is the organization adequately represented as one production process, or do
  internal divisions and intertemporal stocks matter?

This first group determines the **decision context**, **production-system
structure**, and **economic roles of the data**. An intermediate delivery
between two hospital departments is not an ordinary final output. A waiting
list carried into next year is not merely another annual input. Treating either
quantity as if its organizational role did not matter changes the question.

### 2. Which production opportunities make a credible benchmark?

Next decide what the observed evidence is allowed to imply.

- May operating practices be divided or combined, making convexity credible?
- Can an activity be proportionally replicated, or should best practice vary
  with operating scale?
- Can undesirable output be reduced freely, or does pollution control require
  foregone production or a separate abatement process?
- Which organizations have sufficiently comparable missions and operating
  environments to serve as references?
- For a panel, should a unit be compared with the same period, all periods
  viewed retrospectively, only information available so far, or an adjacent
  pair?

These choices define the maintained **production technology**, how its boundary
is **estimated from the sample**, and the **comparison population and time
information**. A global reference technology and a contemporaneous technology
may use the same distance formula while answering different intertemporal
questions.

### 3. What kind of improvement or value is being assessed?

An efficiency measure is a statement about what may improve while something
else is protected.

- If outputs are commitments, how much controllable resource use could be
  avoided?
- If resources are fixed, how much service or production could be added?
- Should variables change in a common proportion or by separate amounts?
- Does the question concern physical performance, cost, revenue, profit,
  pollution, or another declared value?
- Are prices, policy priorities, or restrictions on implicit weights available?
- Is the result an ordinary self-appraisal, a system-level diagnosis, or
  another clearly defined evaluation protocol?

This group fixes the **performance criterion**, any **valuation or preference
information**, and the **evaluation rule**. Two models may share every
production constraint yet remain distinct because one conserves resources,
another expands services, and a third maximizes profit.

### 4. What analysis is required, and how strong is the evidence?

Finally state what will be calculated from the fitted comparison and what claim
the data can support.

- Is the goal a static diagnosis, a scale assessment, a productivity-change
  account, an environmental comparison, an organizational or intertemporal
  diagnosis, or a metafrontier comparison?
- Are targets and divisional decompositions unique, or does the optimum support
  several equally valid accounts?
- How sensitive are results to variables, peers, weights, and reference periods?
- Does the study describe the observed sample, make a population inference, or
  provide a worst-case operational guarantee?
- What sampling, measurement, production-risk, or dependence assumptions are
  required?

This group determines the **follow-on analysis** and the **uncertainty and
inference design**. A tightly solved linear program can still rest on a
sampling-sensitive frontier. A change in a productivity component is an
accounting attribution, not by itself a causal effect of management,
investment, or regulation.

## How familiar model names fit the map

The following examples show why a historical label is useful shorthand but not
a substitute for the study design.

```{list-table}
:header-rows: 1
:widths: 17 26 27 30

* - Familiar label
  - Decision and production story
  - Benchmark and performance question
  - Essential qualification
* - CCR input-oriented DEA
  - one production process; controllable inputs and desirable outputs;
    proportional replication admitted
  - reduce every input in a common proportion while preserving outputs
  - input orientation and CRS define the classical recipe, but the comparison
    population and data roles must still be declared {cite:p}`charnes1978`
* - Environmental DDF
  - inputs jointly produce desirable and undesirable outputs
  - evaluate an explicitly stated bundle of resource saving, desirable-output
    growth, and bad-output reduction
  - the direction, disposability construction, null jointness, and time
    reference determine the meaning {cite:p}`chambers1996,chung1997`
* - Dynamic SBM
  - one organization operates over linked periods
  - locate variable-specific shortfalls while inherited assets, obligations,
    or burdens form one feasible trajectory
  - carry-over roles, period weights, scale assumptions, and terminal policy
    are part of the model {cite:p}`tone2010dynamic`
```

The first row becomes a complete empirical specification only when orientation,
scale, score convention, target policy, and comparator population are fixed
together. “Environmental DDF” and “dynamic SBM” likewise describe families
until their production and evaluation choices are supplied.

## Similar mathematics does not always mean the same method

Model names should be combined only when the economic comparison is genuinely
the same.

| Relationship | What is common? | What must remain visible? |
|---|---|---|
| Exact alternative name or representation | the attainable set and performance measure, possibly after an exact score transformation | historical citation and native reporting convention |
| Same technology, different performance criterion | production constraints and reference data | the improvement plan, normalization, score, and interpretation |
| Same criterion, different production account or benchmark | parts of the measure calculation | production assumptions, eligible comparators, time information, targets, and result name |
| Different estimator or evidentiary design | parts of the observed data description | the estimand, uncertainty assumptions, diagnostics, and permitted claim |

For example, CCR input DEA and input-oriented radial DEA under CRS are two names
for the same basic specification. Radial DEA and SBM can use the same VRS
technology but value improvement differently. Black-box SBM and network SBM
share a slacks-based idea but represent different organizations. A bootstrap
procedure adds an inferential design; it is not another name for the fitted DEA
frontier.

Equal rankings in one dataset do not establish equivalence. Nor does sharing
some constraints or numerical ingredients. Two names describe exact
alternatives only when they imply the same feasible production plans,
objective or exact score transformation, treatment of scale and
disposability, and correspondence of targets on the stated data domain.

## A short model-choice narrative

Consider a hospital system whose board wants to compare resource use across
sites. If each site is treated as one process, annual staffing and beds are
controllable inputs, case-adjusted treatments are committed outputs, and only
same-year hospitals with comparable mandates are eligible references, an
input-oriented VRS model may answer the question.

Change one substantive fact and the design may change:

- if diagnostic and treatment departments require separate performance accounts,
  the production system becomes a network;
- if waiting lists connect one year to the next, the assessed unit becomes a
  trajectory;
- if treatment quality can improve while resources fall by different amounts,
  a directional or nonradial criterion may be more appropriate;
- if reimbursement values determine the objective, a revenue or profit model
  is required; and
- if the board wants population-level confidence statements, an inference
  design must be added to the deterministic comparison.

The value of the map is not that it chooses a model automatically. It makes the
reason for each choice visible and prevents a familiar acronym from deciding
the economic question by default.

## From the reader's map to a defensible empirical study

A published study should explain, in language that a domain expert can challenge,
where the organization begins and ends, which quantities represent resources or
outcomes, who provides a credible comparison, what improvement is being valued, and
which conclusions remain outside the evidence. The formal production assumptions and
reference-period policy then make that explanation reproducible. DEAPack preserves
these choices with the calculation, while the separate Documentation explains their
software representation. The map has done its job when readers can understand the
economic comparison before they inspect an acronym or an API call.
