# Environmental Productivity over Time with Adjacent-Period ML

An electricity producer reports more power and less carbon dioxide than it did last
year. A water utility treats more water while discharging fewer residuals. A farm
raises marketable output while reducing nutrient loss. Each sounds like an
environmental productivity improvement, but none can be assessed from the raw changes
alone. Inputs may also have changed, the attainable production--pollution trade-off
may have improved, and each annual plan must be assessed against the production and
pollution-control opportunities observed at both dates.

The Malmquist--Luenberger (ML) index organizes these issues within one model of
production and pollution. It treats desirable and undesirable outputs as joint
consequences of production and asks how an environmental improvement programme changes
over time {cite:p}`chung1997`. Its classic adjacent-period formulation evaluates the
two operating plans against both period-specific technologies.

These are not ordinary productivity indexes with a pollution penalty attached after
estimation. The undesirable-output technology, the assumed possibilities for
pollution reduction, and the improvement programme all determine what
“environmental productivity” means. That is why the ML index remains distinct from a
conventional Malmquist index with a pollution column appended after the fact
{cite:p}`fare1994`.

The central questions are economic and managerial:

- Has an organization reduced the environmental performance shortfall visible in its
  own period?
- Has the best-observed opportunity for producing useful output with
  fewer undesirable consequences become more favorable?
- Can both annual operating plans be supported by the opportunities observed at
  the other date?

The answers are conditional on the data and production assumptions. They describe
benchmark-relative change; identifying the effects of management, investment, or
regulation requires additional evidence.

## Environmental productivity begins by modeling production and pollution together

Let an operating plan in period $\sigma$ be

$$
z^\sigma=(x^\sigma,y^\sigma,b^\sigma),
$$

where $x$ is a vector of inputs, $y$ a vector of desirable outputs, and $b$ a vector
of undesirable outputs. The period-$\tau$ environmental technology
$\mathcal T^\tau$ contains the input--output--residual plans treated as attainable
by the observations admitted to reference period $\tau$. Thus $\sigma$ identifies
when the plant operated, whereas $\tau$ identifies the body of evidence used to judge
that operation. The distinction matters whenever one year's plan is appraised using
another year's production and pollution-control opportunities.

The label $b$ is not merely a minus sign attached to an ordinary output. The
technology must describe why the residual accompanies useful production and under
what conditions it can be reduced. Three choices are especially important.

First, desirable output and pollution are treated as **joint products**. In the
classic formulation, null jointness rules out positive desirable production with no
associated undesirable output. This prevents the frontier from offering pollution-
free production merely because zero emissions would look preferable.

Second, undesirable outputs are **weakly disposable**. A producer cannot freely
delete pollution from an otherwise unchanged activity. Under the common-factor
representation used here, curtailing the joint activity reduces desirable and
undesirable outputs together. This encodes the idea that pollution reduction is
technologically costly unless a cleaner production or abatement activity is actually
observed in the data.

Third, the analyst declares what one unit of environmental improvement means. For the
classic ML programme, inputs remain fixed, desirable outputs expand in their observed
proportions, and undesirable outputs contract in their observed proportions. Starting
from $(x,y,b)$, a programme of size $\beta$ requests

$$
\bigl(x,(1+\beta)y,(1-\beta)b\bigr).
$$

For a plant, $\beta=0.05$ therefore means a simultaneous 5 percent expansion of each
desirable output and a 5 percent contraction of each undesirable
output, without increasing the input vector. This is a demanding joint performance
programme. It is not equivalent to reducing emissions intensity, reducing total
emissions regardless of output, or attaching a monetary damage value to pollution.

More generally, collect the nonnegative direction magnitudes for the period-$\sigma$
plan in $g^\sigma=(0,g^{y,\sigma},g^{b,\sigma})$, where the leading zero holds inputs
fixed. Its directional appraisal against reference technology $\mathcal T^\tau$ is

$$
D^\tau(z^\sigma;g^\sigma)
=\sup\left\{\beta:
\bigl(x^\sigma,y^\sigma+\beta g^{y,\sigma},
b^\sigma-\beta g^{b,\sigma}\bigr)\in\mathcal T^\tau
\right\}.
$$

For a plan observed in period $\sigma$, the classic observation-scaled choice is
$g^\sigma=(0,y^\sigma,b^\sigma)$. DEAPack stores the desirable- and undesirable-output
components as nonnegative magnitudes; the contraction of bad outputs is supplied by
the model. Entering negative bad-output directions would reverse that meaning a second
time.

A positive distance says that some of the chosen improvement remains attainable
relative to the reference technology. A value near zero says that the plan is already
a benchmark for this programme. Neither statement establishes efficiency under every
possible mix change or every environmental technology.

### Why the assumptions change the estimand

The classic ML formulation used here adopts a constant-returns-to-scale
(CRS), common-factor weak-disposal technology with null jointness and the
observation-scaled programme $(0,y,b)$. These choices give the index a precise meaning:

| Modeling choice | Meaning of the comparison |
|---|---|
| Inputs held fixed | Improvement is sought without expanding the stated resource commitment |
| Desirable direction $g^y=y$ | All desirable outputs expand in their observed proportions |
| Undesirable direction $g^b=b$ | All undesirable outputs contract in their observed proportions |
| Weak disposal and joint production | Pollution cannot be erased independently of observed production activity |
| CRS | Activities may be proportionally replicated; the index does not isolate scale effects |

Changing any row changes the question, not merely the numerical technique. If a
facility has a separately observed scrubber, recycling process, or treatment stage,
common-factor weak disposal may be too restrictive. If physical material balance is
central, a mass-conserving technology may be needed. If reducing one pollutant while
another increases is a realistic programme, the proportional direction may be
inappropriate. Those production accounts belong in the environmental-efficiency
analysis that precedes the temporal index; they should not be selected after seeing
which specification gives a preferred trend.

The practical lesson is simple: define the pollution-generating process before
measuring its change. The chapter on
{doc}`../03-environmental/06-undesirable-outputs-ddf` develops the underlying
technology choices in more detail.

## Adjacent-period ML uses four evaluations

Suppose an organization is observed in adjacent periods $t$ and $t+1$. Write
$D_\sigma^\tau=D^\tau(z^\sigma;g^\sigma)$ for the directional distance of the plan
observed in period $\sigma$ when it is evaluated against the technology supported by
reference period $\tau$. Four questions are required:

| Evaluation | Management question |
|---|---|
| $D_t^t$ | How much of the old plan's improvement programme remains attainable under old-period opportunities? |
| $D_{t+1}^{t+1}$ | How much remains attainable for the new plan under new-period opportunities? |
| $D_{t+1}^t$ | How would the new plan compare with the opportunities observed in the old period? |
| $D_t^{t+1}$ | How would the old plan compare with the opportunities observed in the new period? |

The diagonal comparisons describe each plan relative to its contemporaneous
environment. The off-diagonal comparisons ask whether one period's operation can be
supported by the other period's production and emissions opportunities.

```{figure} ../../_static/figures/environmental-four-distance-matrix.svg
:name: fig-environmental-productivity-four-evaluations
:alt: A two-by-two matrix crosses old and new operating plans with old and new environmental production opportunities, producing two contemporaneous and two cross-period evaluations
:width: 88%

The four evaluations behind adjacent-period ML. Using both period technologies avoids
making the measured transition depend solely on choosing the old or the new benchmark.
```

Two change ratios can be formed, one under each reference period:

$$
R^t
=\frac{1+D_t^t}{1+D_{t+1}^t},
\qquad
R^{t+1}
=\frac{1+D_t^{t+1}}{1+D_{t+1}^{t+1}}.
$$

The adjacent-period ML index takes their geometric mean:

$$
ML^{t,t+1}
=\left[
\frac{1+D_t^t}{1+D_{t+1}^t}
\frac{1+D_t^{t+1}}{1+D_{t+1}^{t+1}}
\right]^{1/2}.
$$

Under this convention, $ML>1$ denotes environmental productivity improvement,
$ML=1$ no measured change, and $ML<1$ decline. “Improvement” means that the later plan
performs better under the specified useful-output-expansion and bad-output-contraction
programme, averaged over the two period-specific reference policies.

The added 1 is part of the classic multiplicative construction. Because the direction
determines the units and scale of $D$, changing the improvement programme can change
the index. Direction choice is therefore an empirical commitment, not a harmless
normalization.

## Two change stories inside the ML index

The index can be decomposed into a change in contemporaneous operating performance
and a change in best-observed production opportunity.

The operating-performance component is

$$
EC_{ML}
=\frac{1+D_t^t}{1+D_{t+1}^{t+1}}.
$$

When $EC_{ML}>1$, the later operation leaves a smaller shortfall relative to its own
period's benchmark. When it is below one, the contemporaneous shortfall has widened.
This is often called efficiency change. In management language, it records whether
the organization realizes more or less of the environmental production potential
observed around it at each date.

The best-practice-opportunity component is

$$
TC_{ML}
=\left[
\frac{1+D_t^{t+1}}{1+D_t^t}
\frac{1+D_{t+1}^{t+1}}{1+D_{t+1}^t}
\right]^{1/2},
$$

with the exact identity

$$
ML=EC_{ML}\times TC_{ML}.
$$

$TC_{ML}>1$ means that the best-observed trade-off among inputs,
desirable outputs, and undesirable outputs became more favorable for the two plans
being compared. A value below one records a less favorable observed opportunity.
Although software often calls this technical change, it is safer to report it as
**best-practice-opportunity change**. The component does not reveal why the benchmark
changed.

```{figure} ../../_static/figures/malmquist-luenberger-frontier-account.svg
:name: fig-environmental-productivity-two-change-stories
:alt: Two environmental productivity stories contrast an organization narrowing its contemporaneous operating shortfall with a change in the best-observed useful-output and undesirable-output opportunity
:width: 100%

Environmental productivity can grow because an organization realizes more of the
opportunity observed in its period, because the best-observed opportunity improves,
or because both occur. It is an accounting description rather than a causal allocation
of responsibility.
```

The distinction matters for management. A narrowing contemporaneous shortfall may be
consistent with better maintenance, fuel management, capacity use, or operating
discipline. A favorable opportunity change may be consistent with cleaner equipment,
learning, altered production mix, or new environmental practice among benchmark
units. But the index does not observe those mechanisms directly. Data revisions,
weather, case mix, fuel quality, regulation, and changes in measurement can produce
similar patterns.

The two components can also move in opposite directions. A plant may improve relative
to its contemporaries while the system's best-observed opportunity becomes less
favorable, or lose relative ground while best practice improves. Reporting only the
headline ML value can hide that strategically important difference.

## A signed cross-technology distance can carry economic information

The evaluated plan is always included in its own-period technology in an ordinary
self-inclusive analysis, so a zero contemporaneous improvement is feasible and the
diagonal distance is nonnegative. A cross-period plan need not belong to the other
period's technology. Its optimal directional distance can therefore be negative.

A negative $D_{t+1}^t$ says that the later plan is beyond what the old technology can
represent in the declared favorable programme. To make it compatible with the old
reference, the comparison would have to move in the unfavorable direction—less
desirable output, more undesirable output, or the corresponding combination defined
by the programme. This can be evidence of a meaningful change in represented
opportunity.

Three empirical outcomes must remain separate:

| Outcome | Interpretation | Appropriate treatment |
|---|---|---|
| A valid comparison gives $D<0$ and $1+D>0$ | The plan lies beyond the other period's opportunity in the declared programme | Retain the signed distance in ML |
| No feasible comparison exists | No admissible reference activity represents the plan under the maintained environmental technology | Leave the transition undefined and investigate the technology and data |
| A valid comparison gives $1+D\le0$ | The multiplicative factor needed by ML is not admissible | Preserve the appraisal record but do not report a finite index |

Truncating a valid negative distance to zero removes information and changes the
index. Infeasibility, by contrast, means that no solution exists under the maintained
joint-production and bad-output constraints. It cannot be repaired by assigning a
large or zero distance.

Cross-period infeasibility is often economically informative. A bad-output equality
or weak-disposal relation may be unable to reproduce a plan from another year because
the observed pollution mix has changed sharply. Before changing the estimator, ask
whether pollutant definitions, measurement methods, treatment activities, or the
assumed disposal relation changed. If a different environmental technology is
substantively justified, all four evaluations should be recomputed under that one
coherent production account.

## One plant transition, with one benchmark sensitivity check

The bundled `environmental_panel` follows six electricity producers from 2020 to
2023. Inputs are energy and labor, electricity is desirable output, and carbon dioxide
is undesirable output. Consider Central between 2020 and 2021:

| Year | Energy | Labor | Electricity | CO$_2$ |
|---|---:|---:|---:|---:|
| 2020 | 110.0 | 55.00 | 79.376 | 285.120 |
| 2021 | 112.2 | 54.45 | 83.742 | 270.465 |

Electricity rises and carbon dioxide falls, while the two inputs move in different
directions. The index evaluates the complete plan rather than declaring improvement
from either raw output change alone.

Fit the adjacent-period ML account first:

```python
from deapack import (
    DEAData,
    GlobalMalmquistLuenbergerDEA,
    MalmquistLuenbergerDEA,
    load_dataset,
)

frame = load_dataset("environmental_panel")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    period="period",
    inputs=["energy", "labor"],
    outputs="electricity",
    bad_outputs="co2",
)

ml = MalmquistLuenbergerDEA().fit(data)

ml.summary().query(
    "dmu_id == 'Central' and comparison_period == 2021"
)[[
    "productivity_change",
    "efficiency_change",
    "technical_change",
]]
```

The same fitted result provides one screen of every reportable 2020--2021
transition:

```python
ml.plot(
    kind="performance",
    metric="productivity_change",
    period=2021,
    view="points",
)
```

| Plant | Environmental productivity change | Operating-performance change | Best-observed-opportunity change |
|---|---:|---:|---:|
| Central | 1.045057 | 1.000014 | 1.045043 |

Central's contemporaneous operating shortfall is essentially unchanged. Adjacent ML
records about 4.51 percent environmental productivity growth. The decomposition places
that change in a more favorable opportunity across the two period-specific technologies.

The adjacent result also illustrates a valid signed cross-period distance. The
underlying comparison is feasible and $D_{2021}^{2020}\approx-0.004534$, so
$1+D_{2021}^{2020}>0$. Central's 2021 plan is slightly beyond the opportunity
supported by the 2020 reference under the chosen programme. The negative value is
retained as part of the period-specific opportunity change.

```{figure} ../../_static/figures/environmental-ml-performance-result.svg
:name: fig-environmental-ml-performance-result
:alt: Four available 2020 to 2021 adjacent-period environmental productivity changes are plotted for South, East, Central, and Coastal, while North and West are listed separately because their required cross-period comparisons are infeasible
:width: 94%

Four plants have all four appraisals needed for an adjacent-period comparison.
Each point therefore compares operating performance and observed production
opportunities under the weak common-factor CRS technology. North and West are
listed separately because at least one required cross-period comparison is
infeasible. Their absence is not zero productivity change or evidence of poor
management. The reported differences remain conditional production comparisons,
not causal ratings of management, investment, or regulation.
```

The two unavailable transitions have different reference boundaries. North's
2020 plan cannot be represented by the 2021 technology under the maintained
production assumptions. For West, neither period's plan can be represented by the
other period's technology. Both transitions therefore remain unavailable rather
than being turned into zero change or a poor-performance score.

As a robustness check, the same transition can be re-evaluated against one
full-horizon technology, often called GML {cite:p}`oh2010`. This changes the admitted
reference information rather than repairing missing adjacent comparisons:

```python
gml = GlobalMalmquistLuenbergerDEA().fit(data)

gml.summary().query(
    "dmu_id == 'Central' and comparison_period == 2021"
)[["productivity_change"]]
```

| Reference-information policy | Environmental productivity change |
|---|---:|
| Two contemporaneous technologies | 1.045057 |
| One full-horizon technology | 1.004603 |

Central's full-horizon value remains above one but is smaller; it is only a
sensitivity result, not a replacement for adjacent-period ML, and it must be
recomputed when the admitted information horizon changes.

The common benchmark also lets a decision maker ask a direct longer-horizon
question. Suppose the plant's transition plan spans 2020 to 2023. A GML endpoint
compares those two complete production-and-emissions plans against the same
retrospective opportunity set. It does not assume that the annual path was smooth,
nor does it identify which investment, operating decision, or regulation produced
the change. It simply makes the start and end of the declared management horizon
comparable under one fixed information vintage.

Consecutive reporting remains the default. A study can request every forward pair or
name only the horizon it needs:

```python
gml_all_horizons = GlobalMalmquistLuenbergerDEA(
    comparison_pairs="all",
).fit(data)

gml_2020_2023 = GlobalMalmquistLuenbergerDEA(
    comparison_pairs=((2020, 2023),),
).fit(data)
```

The all-horizon table has $DP(P-1)/2$ rows for $D$ plants and $P$ periods, so its
results, diagnostics, and disclosed peers grow quadratically with the number of
dates. The production appraisals do not: each plant-period plan needs at most one
contemporaneous and one global solve, and those appraisals are reused across horizons.
This distinction makes a complete research table computationally disciplined while
still too large to treat as a default management display.

If a plant is absent from one selected date, matching is handled for that pair alone.
Dropping the unavailable change does not erase its other observations from the global
environmental benchmark. Raising on the mismatch instead forces the researcher to
resolve the missing institutional history. In either case, pair selection changes the
reported horizons, not the full-sample technology.

For a figure, fit the one endpoint that the caption will name:

```python
gml_2020_2023.plot(
    kind="performance",
    metric="productivity_change",
    period=2023,
    view="points",
)
```

Plotting all pairs under the ending year alone would hide whether each point began in
2020, 2021, or 2022. A reader should never have to infer the base year of an
environmental productivity statement from context.

The adjacent interpretation requires four meaningful appraisals that reconstruct the
headline change and its two components under one consistent treatment of resources,
services, residuals, and reference periods. If a comparison is unavailable or the
decomposition does not close, the transition has no defensible productivity statement.
Detailed numerical diagnostics are available in the DEAPack Documentation; substantive
production assumptions still require economic and institutional justification.

## What should a decision maker be told?

Adjacent-period ML should be reported only when both neighboring operating
environments deserve symmetric standing and all four evaluations are substantively
meaningful. A missing cross-period comparison is part of that evidence and must remain
visible rather than being replaced with a convenient finite number.

A defensible report should state:

1. which variables are inputs, desirable outputs, and undesirable outputs;
2. how joint production and undesirable-output disposability are modeled;
3. what one unit of the environmental improvement programme means;
4. which returns-to-scale assumption defines the opportunity set;
5. which two annual technologies define the four benchmark evaluations; and
6. whether negative distances, infeasibilities, or inadmissible factors occurred.

Results near one need numerical tolerances and honest recognition of uncertainty in
pollution measurement. ML can describe a change in contemporaneous environmental
shortfall, a change in best-observed opportunity, or a plan lying beyond another
period's technology. Without further evidence, the following remain outside its
claim:

- the causal effect of regulation, innovation, investment, ownership, or management;
- the monetary value of pollution damage, abatement expenditure, profit, or social
  welfare;
- whether the benchmark can be adopted given engineering, finance, demand, and local
  regulatory constraints;
- that observed prices or preferences favor the same improvement programme; or
- that another defensible environmental technology or direction would preserve the
  ranking.

Environmental productivity is a production comparison, not a complete policy
evaluation. Once joint production, undesirable-output disposability, and the
improvement programme are explicit, adjacent-period ML offers an intelligible view of
changing operating performance, best-observed practice, and the evidence behind the
benchmark. A causal or welfare evaluation requires a different research design.
