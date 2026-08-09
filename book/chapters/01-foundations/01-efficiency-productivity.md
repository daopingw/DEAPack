# Efficiency, Productivity, and Profitability

A hospital board is told that North could have met its treatment commitments with
fewer resources, East delivered the most care per unit of resource,
Central's productivity improved most over the last year, and West obtained the
largest increase in revenue per dollar of expenditure. South, meanwhile, reduced
avoidable harm while preserving access. The chair asks a natural question: *which
hospital performed best?*

There is no defensible answer until the board says what it means by performance. The
five statements use different information and address different responsibilities.
North is judged against feasible operating alternatives at one point in time. East is
described by an aggregate quantity ratio. Central is compared with itself across
periods. West's comparison values quantities at prices. South is evaluated against a
production model in which desirable care and undesirable harm arise jointly. None
of these statements is merely another name for the same ranking.

| Performance concept | Decision question | Information that gives the answer meaning |
|---|---|---|
| Technical efficiency | Could the organization preserve its service commitment with fewer controllable resources, or deliver more with its current resource budget? | A production technology, a credible comparison population, and a clear statement of which quantities management can change |
| Productivity level | How much aggregate output is being delivered per unit of aggregate input at this time? | An explicit rule for aggregating heterogeneous quantities |
| Productivity change | Has aggregate output quantity changed more favorably than aggregate input quantity between two periods? | Comparable quantity definitions across time and a stated temporal reference policy |
| Profitability and price recovery | What financial return do the quantities generate, and how much of its change reflects relative output and input prices? | Observed prices or another explicit valuation system |
| Environmental performance | What useful production and reduction in undesirable outcomes are attainable together? | A joint-production model, disposal assumptions, and an improvement programme specified in advance |

This separation is not terminology for its own sake. A hospital may be technically
efficient because no comparable hospital demonstrates a feasible resource saving at
its scale, yet have a lower productivity level because its mandated service mix is
resource intensive. Productivity may grow while profitability falls if input prices
rise faster than output prices. Emissions may fall because production contracted, not
because environmental performance improved. A ranking that mixes these conclusions
would hide the policy question rather than answer it.

Before calculating anything, a useful performance question therefore names three
things: the commitment to be protected, the resources or outcomes that the responsible
manager can change over the stated horizon, and the comparison evidence accepted as a
feasible alternative. Prices, environmental burdens, and time enter only when the
question requires them.

```{figure} ../../_static/figures/three-performance-accounts-result.svg
:name: fig-three-performance-accounts
:alt: Four operating plans compared separately by technical efficiency, an explicitly equal-count service-throughput measure, and observed revenue per unit of cost
:width: 100%

One dataset, three performance questions. A and B both attain the best input-oriented
VRS radial score. Under the deliberately simple rule that counts a standard and a
premium service equally, A records greater observed physical productivity. At the
supplied prices, B's service mix produces greater revenue per unit of cost and greater
observed profit. The three columns answer different questions; they are not
interchangeable score scales or causal evaluations of management.
```

Read the figure across the columns, not down a league table. The first column asks
whether a feasible benchmark supports further common resource saving. The second uses
a stated equal-count rule to describe service throughput. The third values the
observed mix of standard and premium services. A and B exchange places only when the
question and measurement scale change. The figure contains no temporal comparison and
no undesirable outcome, so it cannot support a conclusion about productivity change
or environmental performance.

In the opening figure, data envelopment analysis (DEA) supplies the first
comparison. It constructs an empirical production comparison for organizations
that use multiple resources to deliver multiple products, services, or outcomes,
without imposing a parametric functional form in advance. Later frontier-based methods use the same
production logic in productivity and environmental analyses. In every case, the
optimization takes its meaning from the economics supplied to it: who is responsible
for which quantities, what must be preserved, and which operating practices are
credible evidence of what could be done.

## Production possibilities and resource responsibility

Let $x\in\mathbb{R}^m_+$ denote a vector of inputs and
$y\in\mathbb{R}^s_+$ a vector of desirable outputs. A production technology is the set

$$
\mathcal{T}=\{(x,y):x\text{ can produce }y\}.
$$

Each element of $\mathcal{T}$ is a feasible production plan. Economically,
$\mathcal{T}$ describes the operating alternatives admitted by the study. It is not a
list of everything management could imagine, and it is not identical to the rows that
happened to be observed. The analyst builds it from those observations using stated
assumptions about comparability, disposability, convexity, and scale. Its efficient
boundary contains the plans for which the available evidence supports no further
improvement in at least one relevant direction.

Consider a plant that uses 2 units of an aggregate resource to produce 1.5 units of
output. That record alone does not reveal whether resources are well managed. It may
be excellent performance under a demanding service obligation or weak performance if
comparable plants demonstrate that the same output is attainable with less resource.
Technical efficiency therefore contains an empirical counterfactual: *what alternative
plan is supported by the study's production technology, for this organization and this decision
horizon?*

Koopmans called a feasible plan efficient when no other feasible plan can use no more
of every input and produce no less of every output, with a strict improvement in at
least one component {cite:p}`koopmans1951`. This componentwise strong-efficiency
criterion considers every input excess and output shortfall. Debreu and Farrell
developed scalar measures of common proportional resource saving
{cite:p}`debreu1951,farrell1957`. Related Shephard distance functions supply the input-
and output-oriented representations used in modern production analysis
{cite:p}`shephard1953,fare1985`. Those contributions precede DEA and remain essential
for interpreting its scores.

The distinction becomes concrete in a one-input, one-output example.

```{figure} ../../_static/figures/frontier-orientations.svg
:name: fig-frontier-orientations
:alt: Eight production units, a VRS best-practice benchmark, and the resource-saving and output-expansion targets of unit E
:width: 95%

An empirical variable-returns-to-scale benchmark. A--D represent best observed
practice under the maintained assumptions. For E, one comparison asks how much input
could be saved while preserving output; the other asks how much output could be
delivered with the current input.
```

A--D supply the best-practice evidence for the variable-returns-to-scale (VRS)
technology in the figure. Read the two labelled comparisons as different management
questions. One holds E's output commitment fixed and asks what resource budget would
suffice. The other protects E's current resource budget and asks what service level it
could support. Neither comparison says that management is free to choose both changes,
or that the indicated plan can be implemented without transition costs.

The shaded region records plans treated as feasible under free disposability of inputs
and desirable outputs. The next two chapters examine who and what may credibly be
compared and then show how observations, convexity, disposability, and returns to scale
create this empirical opportunity set.

Calling A--D “efficient” is conditional. It means that no feasible comparison generated
from this sample and these assumptions dominates them. It does not establish that they
use the best technology available outside the sample, deliver the highest quality, or
maximize social welfare. It also does not make them universal role models: a peer is
evidence under the study's production model, not a verdict on every aspect of the
organization.

## What may management change?

Orientation turns organizational responsibility into a quantitative question.
Farrell's radial measures hold one side of production fixed while changing the other
proportionally. For an observed plan $(x_o,y_o)$, define the input contraction factor
and output expansion factor as

$$
\begin{aligned}
\theta_o
  &=\inf\{\theta>0:(\theta x_o,y_o)\in\mathcal{T}\},\\
\phi_o
  &=\sup\{\phi>0:(x_o,\phi y_o)\in\mathcal{T}\}.
\end{aligned}
$$

Under the standard monotonic technology, $0<\theta_o\leq1$ and
$\phi_o\geq1$. An input-oriented value of $\theta_o=0.80$ says that the
represented technology supports a first-stage common reduction of 20 percent in every
input while outputs are preserved. An output-oriented value of $\phi_o=1.25$ says
that a common 25 percent expansion of every output is represented as attainable with
the current inputs. To compare orientations in a common higher-is-better display, this
book also reports the reciprocal $1/\phi_o$. The expansion factor $\phi_o$ retains
the direct management meaning; its reciprocal is only a bounded presentation.

For unit E in {numref}`fig-frontier-orientations`, the input-oriented benchmark keeps
the output commitment $y_E=1.5$ fixed and requires only $4/3$ units of input. Hence

$$
\theta_E=\frac{4/3}{2}=\frac{2}{3}.
$$

The output-oriented benchmark instead treats $x_E=2$ as the available resource budget
and indicates an attainable output of $2.5$, giving

$$
\phi_E=\frac{2.5}{1.5}=\frac{5}{3},
\qquad
\frac{1}{\phi_E}=0.6.
$$

The two bounded efficiencies differ because they answer different management
questions. Input orientation is defensible when outputs are contractual or policy
commitments and the responsible manager can adjust resources. Output orientation is
defensible when the resource budget is fixed over the relevant horizon and service or
production can expand. A hospital may face the first question in an annual budget
review and the second during a short-run access programme. Under VRS these
counterfactuals need not identify the same proportional performance gap. When neither
describes the feasible decision rights, a nonradial or directional measure may be more
appropriate.

A proportional benchmark also does not guarantee Pareto--Koopmans efficiency. After
the common percentage adjustment has been exhausted, a particular resource may still
be used in excess or a particular service may remain below attainable practice. These
variable-specific opportunities are reported as slacks and motivate the additive,
RAM, and slacks-based measures developed later in the book. They should be read as
benchmark evidence to investigate, not automatic budgets or production quotas.

## Productivity level is a quantity account

With one input and one output, observed physical productivity can be written as the
ratio

$$
AP_j=\frac{y_j}{x_j}.
$$

This average product is a property of the observed plan under an unambiguous quantity
ratio. It answers “how much output per unit of input?”, not “how much improvement is
supported by comparable practice?”. Technical efficiency requires the latter
benchmark comparison. In {numref}`fig-frontier-orientations`, B has productivity
$2.5/2=1.25$ and E has productivity $1.5/2=0.75$. Under constant returns to scale
(CRS), B's operating pattern may be replicated proportionally, so E's radial
efficiency happens to equal the ratio $0.75/1.25=0.6$. That equality is a special
one-input, one-output CRS result, not a definition of technical efficiency.

Under VRS, A, C, and D can all represent best observed practice even though their
average productivities differ from B's. Each may use its represented opportunities
well at its own scale without operating at the scale that delivers the largest output
per unit of input. This is why a change from CRS to VRS changes the benchmark and can
separate technical performance at the observed scale from scale performance; it does
not alter the observed ratio $y_j/x_j$.

The distinction becomes more important with multiple inputs and outputs. Nurse hours,
bed-days, capital services, emergency visits, and elective procedures cannot be added
merely because they occupy adjacent spreadsheet columns. There is no unique physical
productivity ratio until quantities are aggregated by an explicit quantity index.
Such an index may use declared quantity weights, price information within a consistent
index-number formula, or production-based quantity comparisons
{cite:p}`caves1982,coelli2005`. The middle account in
{numref}`fig-three-performance-accounts` deliberately counts its two service types
equally:

$$
AP_j^{eq}
=\frac{y_{j,\mathrm{standard}}+y_{j,\mathrm{premium}}}{x_j}.
$$

The superscript $eq$ records the equal-count rule. It gives $AP_A^{eq}=2$ and
$AP_B^{eq}=1.8$. The account is transparent and useful for the teaching comparison,
but it is not a unique multi-output productivity measure supplied by DEA. A different
defensible aggregation rule could reverse the ordering. A policymaker who values
premium and standard service differently is not correcting the DEA score; that person
is defining a different productivity or value account.

A productivity level also remains silent about *why* one organization has a larger
ratio. Case mix, operating scale, inherited capital, quality, and the production
opportunities available to different groups may all matter. It is a descriptive
quantity account until the study supplies an identification strategy for a causal
claim.

## Productivity change is a temporal account

Across time, the question changes from “what is this period's output per unit of
input?” to “did aggregate output quantity change more favorably than aggregate input
quantity?”. Let $Q_{y,o}^{t,t+1}$ and $Q_{x,o}^{t,t+1}$ denote declared output- and
input-quantity indexes for organization $o$. One complete multiplicative
total-factor-productivity account is the Hicks--Moorsteen index:

$$
HM_o^{t,t+1}
=\frac{Q_{y,o}^{t,t+1}}{Q_{x,o}^{t,t+1}}.
$$

A value above one means that aggregate output quantity grew relative to aggregate
input quantity; one means no change; and a value below one means decline. This
statement requires stable organizational boundaries and quantity definitions across
the two periods. More patients recorded after a coding change, or a lower labor input
after contracted work is moved outside the accounting boundary, is not automatically
productivity growth.

Frontier-based measures use observed production possibilities to construct the
needed quantity comparisons. A Malmquist analysis may separate productivity change
into a change in how fully the organization used the opportunities available in each
period and a change in the best-practice opportunities documented by the data
{cite:p}`fare1994,coelli2005,fried2008`. The first component is often called
*efficiency change* or *catch-up*. For management, it says whether the operating
shortfall relative to current peers narrowed or widened. It does not establish that
managers copied leaders, learned faster, or implemented a particular reform. The
second component says whether the best observed resource--output possibilities became
more or less favorable around the organization's operating plans; by itself it is not
a causal estimate of innovation.

Different mainstream productivity families use different scales. Malmquist and
Hicks--Moorsteen indexes are multiplicative and use one as the no-change value.
Luenberger indicators are additive and use zero. Their numbers cannot be pooled into
one ranking merely by labeling all of them “productivity change”. Nor is a high static
efficiency level the same as productivity growth: an organization can remain close to
best practice while the represented technology contracts, or improve relative
performance while total productivity still falls.

## Profitability and price recovery value the account

Quantity performance does not determine financial performance. Let $w_o$ contain the
input prices and $p_o$ the output prices applied to organization $o$. For its observed
plan $(x_o,y_o)$, define cost, revenue, profit, and return-to-dollar profitability as

$$
C_o=w_o^\top x_o,\qquad
R_o=p_o^\top y_o,\qquad
\Pi_o=R_o-C_o,\qquad
\rho_o^{RTD}=\frac{R_o}{C_o}.
$$

Profit is a monetary difference; $\rho_o^{RTD}$ is return-to-dollar
profitability, or revenue per unit of expenditure. Neither is a
technical-efficiency score. A large organization can earn more total profit while
earning less revenue per dollar of expenditure, so profit and profitability should not
be used as synonyms. Both depend on the valuation system as well as the physical
production plan.

The distinction becomes especially important across time. Under an internally
consistent quantity--price index system, revenue and cost change can be written as

$$
\frac{R_o^{t+1}}{R_o^t}
=P_{y,o}^{t,t+1}Q_{y,o}^{t,t+1},
\qquad
\frac{C_o^{t+1}}{C_o^t}
=P_{x,o}^{t,t+1}Q_{x,o}^{t,t+1},
$$

where $P_y$ and $P_x$ are output- and input-price indexes. It follows that the change
in return-to-dollar profitability has the accounting decomposition

$$
\frac{\rho_o^{RTD,t+1}}{\rho_o^{RTD,t}}
=\underbrace{\frac{Q_{y,o}^{t,t+1}}{Q_{x,o}^{t,t+1}}}_{\text{productivity change}}
\underbrace{\frac{P_{y,o}^{t,t+1}}{P_{x,o}^{t,t+1}}}_{\text{relative-price recovery}}.
$$

Relative-price recovery asks whether output prices moved favorably compared with input
prices. It can improve while the organization's physical quantities remain unchanged;
productivity can improve while unfavorable price movements reduce profitability. The
decomposition is an accounting identity only when the quantity and price indexes are
constructed consistently {cite:p}`odonnell2010profitability`.
It does not say that management caused a tariff change, wage settlement, exchange-rate
movement, or regulated reimbursement decision.

The four plans in {numref}`fig-three-performance-accounts` use one resource, a
standard service, and a premium service. At prices $w=2$ and $p=(3,5)$, A earns
$28/8=3.5$ units of revenue per unit of cost and a profit of 20. B earns
$37/10=3.7$ per unit of cost and a profit of 27. A nevertheless has the greater
equal-count physical throughput, while both A and B have input-oriented VRS radial
efficiency of one. Because this opening comparison does not request slack completion,
that score is not promoted to a Pareto--Koopmans efficiency claim. This is the
practical reason to keep the three accounts separate.

Observed prices also do not necessarily measure social value. A public hospital's
administered tariff, a utility's regulated price, or an emissions permit price may be
important for financial responsibility without representing the full benefit or harm
to society. Profitability, allocative efficiency, and welfare therefore require their
own declared valuation questions.

## Environmental performance keeps undesirable outcomes visible

Some organizations jointly produce services society wants and residuals it wants to
reduce. A power plant supplies electricity and emits carbon dioxide; a hospital treats
patients and may generate avoidable harm; a farm produces food and nutrient runoff.
Calling the residual an ordinary input misstates its production role, while treating
it as a desirable output rewards more of it. The relevant technology records the joint
account explicitly:

$$
\mathcal T
=\{(x,y,b):x\text{ can jointly produce desirable output }y
\text{ and undesirable output }b\}.
$$

Environmental performance then asks what combination of useful-output expansion,
resource saving, and undesirable-output reduction is attainable under this production
account. The answer depends on the declared programme and on assumptions about joint
production and disposability {cite:p}`murty2012`. A regulator asking a plant to
maintain electricity while
reducing emissions poses a different question from a planner asking how much
electricity can expand while emissions and fuel are held fixed. Directional and
slacks-based environmental models later in the book make those commitments explicit
{cite:p}`chung1997,tone2003bad`.

Several tempting shortcuts answer other questions. Total emissions describe a burden
but ignore useful production; emissions per unit of output are an intensity ratio but
do not construct a multidimensional feasible alternative. A technical-efficiency model
that omits pollution can reward resource saving while remaining silent about
environmental performance. Conversely, an environmental score does not attach a
monetary damage to emissions or establish social welfare. Across time,
environmentally adjusted productivity change requires a complete set of temporal
comparisons; a single cross-period environmental-efficiency value is not itself a
productivity index.

The five accounts can now be kept in their proper places. Technical efficiency asks
about represented operating opportunity. Productivity level and change aggregate
physical quantities, at one time and between times respectively. Profitability and
price recovery value those quantities. Environmental performance changes the
production account by retaining undesirable outcomes. They can illuminate one another,
but they do not share a measurement scale and should not be collapsed into a universal
performance ranking.

## Reproducing the opening accounts with DEAPack

DEAPack can reproduce the comparison without treating endogenous DEA multipliers as
observed prices:

```python
from deapack import (
    BCC,
    DEAData,
    PriceData,
    ReturnToDollarEfficiency,
    dataset_info,
    load_dataset,
)

frame = load_dataset("economic_efficiency_4")
roles = dataset_info("economic_efficiency_4").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
)

technical = BCC(orientation="input", compute_slacks=False).fit(data)
prices = PriceData.common(
    input_prices={"resource": 2.0},
    output_prices={"standard_service": 3.0, "premium_service": 5.0},
)
profitability = ReturnToDollarEfficiency(
    returns_to_scale="vrs",
).fit(data, prices)

physical_productivity = (
    frame["standard_service"] + frame["premium_service"]
) / frame["resource"]
```

The profitability model also compares each observed $\rho_j^{RTD}$ with the best
return-to-dollar ratio available from the declared reference set. That relative
comparison is useful, but it does not convert profitability into technical efficiency.
Nor does a DEA multiplier chosen to support a technical-efficiency score become a
market price, a social value, or a willingness to pay. The observed-price chapter
returns to these distinctions with cost, revenue, and profit objectives; the
productivity chapters later show what must remain stable for comparisons through time.
The environmental chapters use separate data roles and production assumptions because
the teaching dataset in this opening comparison contains no undesirable outcome.

## How DEA turns observed practice into comparative evidence

Farrell's central contribution was to measure productive performance relative to an
attainable standard rather than infer it from one average-product ratio
{cite:p}`farrell1957`. The original CCR formulation made that comparison operational
for organizations using several inputs to produce several outputs
{cite:p}`charnes1978`. Banker, Charnes, and Cooper then introduced the VRS technology,
allowing performance at the organization's observed scale to be distinguished from the
additional question of scale performance {cite:p}`banker1984`.

“Nonparametric” does not mean assumption-free. A DEA estimate depends on the units in
the reference sample, their comparability, the selected variables, disposability,
convexity, returns to scale, orientation, and any weight or assurance-region
restrictions. DEA avoids specifying a smooth functional form such as Cobb--Douglas, but
it replaces that choice with an explicit set of production assumptions. Those
assumptions state which observed practices may count as evidence and how they may be
combined. Changing them changes the economic comparison, not merely a technical
setting.

The operating plans in {numref}`fig-frontier-orientations` are distributed with
DEAPack as the deterministic `frontier_1x1` dataset. The following analysis reproduces
three appraisals of E. Holding E's record fixed makes the source of each difference
visible: the first two change what the organization is asked to adjust, while the third
changes whether represented operating patterns may be replicated proportionally
across scale.

```python
import pandas as pd

from deapack import BCC, CCR, DEAData, load_dataset

frame = load_dataset("frontier_1x1")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    inputs="input",
    outputs="output",
)

models = {
    "VRS input-oriented": BCC(orientation="input"),
    "VRS output-oriented": BCC(orientation="output"),
    "CRS input-oriented": CCR(orientation="input"),
}

fitted = {name: model.fit(data) for name, model in models.items()}
comparison = pd.concat(
    [
        result.summary()
        .query("dmu_id == 'E'")
        .assign(specification=name)
        for name, result in fitted.items()
    ],
    ignore_index=True,
)[["specification", "score", "efficiency"]]
comparison
```

| Management comparison | Contraction or expansion factor | Higher-is-better display |
|---|---:|---:|
| VRS input-oriented | 0.6667 | 0.6667 |
| VRS output-oriented | 1.6667 | 0.6000 |
| CRS input-oriented | 0.6000 | 0.6000 |

For the output-oriented appraisal, 1.6667 is the expansion factor $\phi_E$ and 0.6000
is its reciprocal. The shared value of 0.6000 in the last column does not make the VRS
output and CRS input comparisons the same question. Under CRS, E's input target is 1.2
rather than the VRS target of $4/3$ because proportional replication of the most
productive activity is admitted. Inspecting the associated targets turns each score
into an operating account:

```python
targets = pd.concat(
    [
        result.targets.query("dmu_id == 'E'").assign(specification=name)
        for name, result in fitted.items()
    ],
    ignore_index=True,
)
targets[["specification", "role", "variable", "observed", "target"]]
```

The target table should be read with the decision contract in view. It records plans
supported by the maintained technology, not forecasts of what E will achieve or
instructions that ignore adjustment cost, quality, and institutional constraints.
Later chapters add variable-specific excesses and shortfalls, the organizations
supporting a benchmark, and the components of productivity change. Those quantities
often carry more management information than a rank based on the headline score.

## What a performance statement can support

A defensible technical-efficiency conclusion names its question and benchmark. For
this example, one may say that E's represented resource-use efficiency is 0.667 when
its output commitment is preserved, relative to the eight observed units and the VRS,
convex, freely disposable technology. Saying only that “E is 66.7 percent efficient”
discards the service commitment, decision rights, comparison population, scale
assumption, and production account that define the estimand.

The corresponding claims for other accounts use different language. A productivity
level names the quantity aggregator. Productivity change names both periods, the
quantity index, and the reference-information policy. A profitability result names the
prices and distinguishes revenue per expenditure from profit. An environmental result
names the undesirable outcome, joint-production and disposal assumptions, and the
improvement programme. None should borrow the percentage or rank of another account.

Comparability is especially important. Hospitals with different case severity,
teaching obligations, or emergency mandates may not share one production technology
even when their columns have the same labels. Adding variables indiscriminately is not
a remedy: with a fixed sample, a higher-dimensional technology often places more units
on sparsely supported parts of the frontier. Protocols for DEA applications therefore
treat DMU definition, variable selection, isotonicity, sample size, and sensitivity
analysis as core modeling decisions {cite:p}`dyson2001`.

Finally, numerical precision and empirical certainty are different. A score may be
calculated very accurately while the estimated opportunities remain sensitive to
sampling variation, measurement error, and outliers. Bootstrap and robust-frontier
methods address aspects of that uncertainty {cite:p}`simar1998,daraio2007`; DEA scores
alone do not identify causal effects. More fundamentally, no statistical refinement
can repair a production account that assigns the wrong responsibilities, omits a
binding service commitment, or compares organizations that cannot credibly learn from
one another.

The next chapter asks which organizations and quantities belong in a credible
comparison. The chapter after it constructs the CRS and VRS empirical technologies,
showing how observed activities, convex combinations, free disposability, and returns
to scale turn a finite dataset into the opportunity set used here. Part II then brings
orientation and scale together in the four classical radial formulations in
{doc}`../02-classical/03-classical-radial`. The later productivity, observed-price, and
environmental parts return to the other questions introduced here without treating
them as alternative labels for technical efficiency.
