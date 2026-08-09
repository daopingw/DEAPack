# Slack-Based Efficiency: From Common Contraction to Specific Operating Gaps

At a hospital performance meeting, a result such as “no further common
percentage reduction in resources” can sound like the end of the efficiency
discussion. Yet the same comparison evidence may show excess diagnostic
capacity in one department and an attainable service gain in another. The
radial result is not wrong. It has answered a deliberately compact question
about one common proportional change; it has not claimed that every
resource--service gap has disappeared.

Slack-based methods shift attention from a common percentage to the particular
resources and services that constrain performance. Diagnostic capacity may be
excessive even when nursing hours are not; one service line may have room to expand
while another already meets best observed practice. The classic additive model, the
range-adjusted measure (RAM), and Tone's slacks-based measure (SBM) form one useful
family for studying such uneven opportunities {cite:p}`charnes1985,cooper1999,tone2001`.
They use the same kinds of feasible benchmark plans and expose the same physical gaps,
but summarize those gaps on different scales.

That distinction is managerial, not merely algebraic. An original-unit gap, a
gap relative to the observed sample range, and a gap relative to the focal
organization's own operation answer different reporting questions. None is a
price, a welfare weight, or a universally valid league-table score. The
physical gaps and the assumptions that make them feasible should therefore be
understood before any aggregate number is interpreted.

Part I established why the economic roles of the variables and the eligibility
of comparators must be settled in the {doc}`../01-foundations/02-study-design`,
and how production assumptions define attainable practice in the
{doc}`../01-foundations/02-production-frontier`. Those choices remain unchanged here.
Normalization merely determines how several physical shortfalls contribute to one
summary measure. It cannot make unlike organizations comparable, turn an irrelevant
column into a legitimate input or output, or give managerial importance to a gap that
the study never justified.

## Begin with one feasible operating plan

Let organization $o$ use inputs $x_o\in\mathbb{R}_{+}^{m}$ to produce
desirable outputs $y_o\in\mathbb{R}_{+}^{s}$. A benchmark assembled from the
eligible reference population has intensity vector $\lambda$. Under the
standard free-disposal account, one feasible comparison plan can be written

$$
X\lambda+s^-=x_o,
\qquad
Y\lambda-s^+=y_o,
\qquad
\lambda,s^-,s^+\geq0,
$$

together with the chosen returns-to-scale restriction. The implied operating
targets are

$$
\widehat x_o=x_o-s^-,
\qquad
\widehat y_o=y_o+s^+.
$$

An input slack $s_i^-$ is a resource saving supported by the maintained
technology while the represented service commitments are protected. An
output slack $s_r^+$ is an attainable service addition without breaching the
represented resource limits. These are properties of a comparison plan, not
yet recommendations to close a ward, reduce a budget, or impose a service
quota.

The balance equations do not dictate how unlike gaps should be aggregated.
They supply a common physical ledger: the eligible comparators, their weights,
the original-unit gaps, and the implied targets. A given feasible plan can be
read with each of the rulers below. When the models are fitted separately,
however, their different objectives can select different feasible plans. The
shared ledger is the conceptual common ground, not a promise that every
dataset will produce identical peers or targets.

## The same gaps under three reporting rulers

The classic additive model maximizes the total physical gap

$$
\delta_o
=\sum_{i=1}^{m}s_i^-+\sum_{r=1}^{s}s_r^+,
$$

subject to the same input and output balances. In its original VRS,
unit-weight form, zero is best: $\delta_o=0$ means that no represented
componentwise improvement remains. A positive optimum implies that at least
one resource excess or service shortfall remains; the associated slack ledger,
not the scalar total, identifies where it lies.

The physical slack table is highly informative, but the scalar sum has no
general percentage interpretation. Ten staff hours, two tonnes of material,
and five units of service do not become economically equivalent merely because
they enter one objective. Changing tonnes to kilograms can change both the
additive value and the selected target. The classic additive account is
therefore most informative as a search for a componentwise-improved feasible
plan and as an original-unit ledger. Its raw total is not a universal ranking
scale.

RAM retains the variable-specific ledger but supplies a sample ruler. Write the
observed range of input $i$ as $R_i^x$ and that of output $r$ as $R_r^y$. Under
the VRS balances above, RAM selects the plan that maximizes range-normalized
slack and reports its higher-is-better complement:

$$
\delta_o^{RAM}
=\max_{\lambda,s^-,s^+}\frac{1}{m+s}
\left(
\sum_{i:R_i^x>0}\frac{s_i^-}{R_i^x}
+\sum_{r:R_r^y>0}\frac{s_r^+}{R_r^y}
\right),
\qquad
\rho_o^{RAM}=1-\delta_o^{RAM}.
$$

A contribution of 0.20 means “one fifth of this variable's observed sample
range,” not “a 20-percent cost saving.” The normalization removes physical
units, but the ruler exists only for variables with positive sample ranges. An
extreme observation can change the ruler as well as the estimated production
frontier. RAM is consequently a sample-relative member of the same slack
family, not an independent economic interpretation
{cite:p}`cooper1999,steinmann2001ram,cooper2001ramresponse`.

The named RAM profile uses one self-inclusive VRS comparison and computes each
range from that same reference population. Because translating a quantity
translates the feasible balance without changing its range or slack, RAM can
also accommodate finite signed data. A coordinate with zero range contributes
zero to the normalized objective and, under the matched VRS balance, cannot
carry a nonzero slack. These are properties of the RAM ruler, not permissions
to shift standard SBM data by an arbitrary constant.

SBM supplies an organization-specific ruler. For strictly positive inputs and
outputs, define the average proportional gaps

$$
L_o^x=\frac{1}{m}\sum_{i=1}^{m}\frac{s_i^-}{x_{io}},
\qquad
L_o^y=\frac{1}{s}\sum_{r=1}^{s}\frac{s_r^+}{y_{ro}}.
$$

Each gap is now judged relative to the quantity facing the focal organization.
Suppose two clinics could each release ten employees while maintaining their
services. Ten employees are half of a 20-person workforce but only one percent
of a 1,000-person workforce. An absolute slack records the same physical gap;
SBM records very different proportional burdens.

```{figure} ../../_static/figures/sbm-relative-slacks.svg
:name: fig-sbm-own-observation-normalization
:alt: The same input slack of ten is a large proportional gap for a small unit and a small proportional gap for a large unit
:width: 92%

Own-observation normalization asks how large an operating gap is relative to
the activity that faces it.
```

This normalization is dimensionless and unit invariant. Changing employees to
thousands of employees, or pounds to millions of pounds, scales the observation
and its slack together. It does **not** make one employee, one bed, and one pound
equally valuable in an economic sense. The standard average assigns equal
weight to each represented dimension; variable selection is therefore part of
the performance judgement. This is a measurement convention, not a system of
prices or social values.

For example, suppose a provider has two inputs. Its benchmark identifies a
20-percent staffing excess but no excess in capital. The average proportional
input gap is 10 percent, so its input-oriented score is 0.90. The conclusion is
not “cut every input by 10 percent.” It is that one input has a specific
20-percent gap and the equal-dimension account averages it with a zero gap in
the other input. Whenever management is expected to act, the variable-level
diagnosis must accompany the average.

The three rulers can now be compared without mistaking them for three separate
production technologies:

| Ruler | What a gap is compared with | Main interpretive boundary |
|---|---|---|
| Additive | Its original physical unit and declared weights | Unlike units cannot be added into a universal percentage |
| RAM | Full variation in the declared sample | Scores change when the sample ruler changes |
| SBM | The focal organization's own quantity | Zeros and translations change or invalidate the ratio account |

An additive slack account may use pre-declared positive weights, but they
change how feasible improvements are valued and may change the target. The
standard RAM and SBM accounts used here retain their defining equal-dimension
normalizations. A conversion factor, an observed price, and a stakeholder
priority are not interchangeable. When expenditure, revenue, or profit is the
real question, the price-based economic-efficiency models later in this part
provide the clearer account.

### An advanced bridge: a declared compromise between common change and input mix

Some management settings do not want either a purely common contraction or an
equal treatment of every input gap. EBM offers a disciplined compromise: one
term records the common input factor and another records an importance-weighted
input mix {cite:p}`tone2010ebm`. The two terms use one joint peer plan, so the
result is neither an average of a radial score and an SBM score nor a claim
that the same resource adjustment is sensible in every service system.

This book treats that compromise as advanced because the importance calibration
is part of the decision, not a harmless software setting. DEAPack's public EBM
evaluator requires the analyst to declare the calibration and its provenance
before fitting. It can consequently support a transparent question such as:
given a committee's documented view of the relative importance of physician
and nursing inputs, what jointly feasible resource-and-input-mix adjustment is
demonstrated by comparable providers? It does not estimate those priorities
from the data.

This matters for interpretation. The input-oriented source programme allows
substitution: a target can reduce one resource while increasing another and
still preserve the reported service commitments. That is a possible operating
mix under the stated technology, not a recommendation to increase every input.
At its radial endpoint the EBM score agrees with matched CCR input efficiency;
at its other endpoint it is still not automatically an SBM, because the radial
factor remains free. The automatic affinity/PCA calibration discussed in the
original article is deliberately not run in this release. Readers who need
the declared-calibration evaluator and its certificates can use the package
Documentation; it is a supporting advanced tool, not a fourth ruler for the
core comparison above.

### One operating plan, three reporting rulers

The difference among the three rulers is easiest to understand when the
physical benchmark is held fixed.
The durable lesson is not to memorize three historically named recipes. These
appraisals belong in one slack family because they use the same production
account and ask for the same kind of variable-specific improvement; the
substantive difference here is the ruler used to communicate that evidence.

In the `slacks_2x2` teaching data, organization E uses labor and capital to
provide service and quality. The classic additive, RAM, and non-oriented SBM
appraisals all select the same VRS reference activity:

$$
0.25B+0.75C.
$$

That activity supports exactly the same variable-level operating evidence in
all three fits: no labor saving, a capital saving of 1.125, a service gain of
0.600, and a quality gain of 0.260. The common plan lets us change only the
reporting ruler rather than confusing a different score with a different
benchmark.

```python
import pandas as pd

from deapack import (
    RAM,
    SBM,
    AdditiveDEA,
    DEAData,
    load_dataset,
)

data = DEAData.from_frame(
    load_dataset("slacks_2x2"),
    dmu="dmu",
    inputs=("labor", "capital"),
    outputs=("service", "quality"),
)

ruler_results = {
    "Additive": AdditiveDEA(returns_to_scale="vrs").fit(data),
    "RAM": RAM().fit(data),
    "SBM": SBM(returns_to_scale="vrs").fit(data),
}
focus = "E"

reported_scores = pd.Series(
    {
        name: result.summary().set_index("dmu_id").loc[focus, "score"]
        for name, result in ruler_results.items()
    },
    name="reported_score",
)
peers = {name: result.peers(focus) for name, result in ruler_results.items()}
physical_slacks = {
    name: result.slacks.query("dmu_id == @focus")
    for name, result in ruler_results.items()
}

peers, physical_slacks, reported_scores.to_frame()
```

| Model report for E | Value | Best value and direction | What supplies the ruler? |
|---|---:|---|---|
| Additive weighted slack total | 1.985000 | 0; lower is closer | The declared original-unit slack weights |
| RAM efficiency | 0.506250 | 1; higher is closer | Each variable's range in the declared sample |
| SBM efficiency | 0.554763 | 1; higher is closer | E's own observed quantity for each variable |

The arithmetic makes the source of the disagreement visible. With unit
additive weights, the original-unit total is

$$
\delta_E=0+1.125+0.600+0.260=1.985.
$$

The four sample ranges for labor, capital, service, and quality are 2.4, 2.0,
1.0, and 0.32. RAM therefore reports

$$
\rho_E^{RAM}
=1-\frac{1}{4}
\left(
\frac{0}{2.4}+\frac{1.125}{2.0}
+\frac{0.600}{1.0}+\frac{0.260}{0.32}
\right)
=0.506250.
$$

SBM replaces those sample ranges by E's own observed quantities:

$$
\rho_E^{NO}
=\frac{
1-\frac{1}{2}\left(\frac{0}{2.0}+\frac{1.125}{2.8}\right)
}{
1+\frac{1}{2}\left(\frac{0.600}{1.3}+\frac{0.260}{0.62}\right)
}
=0.554763.
$$

No new production opportunity enters these calculations. The denominators
change what the same four gaps mean in the final report.

The comparison is meaningful because all three selected plans are feasible
under the same VRS technology and each observed--slack--target identity closes.
The figure also confirms that the three models select the same physical plan
in this example. The exact numerical checks are documented separately in the
DEAPack Documentation.

```{figure} ../../_static/figures/slack-family-rulers-result.svg
:name: fig-slack-family-rulers-result
:alt: Organization E has the same VRS peers, original-unit slacks, and selected targets under Additive DEA, RAM, and SBM, while three separate score cards show their different model-specific rulers, best values, and directions
:width: 100%

One selected operating plan viewed through three reporting rulers. The ledger
keeps unlike resources and services in their original units. The separate
cards deliberately avoid a common score axis because the additive total, RAM
efficiency, and SBM efficiency do not measure distance on one interchangeable
scale.
```

This agreement should not be promoted into a theorem. The three objectives can
select different optimal plans in another dataset, and alternate optima can
support the same score. Here the shared plan isolates the transferable
lesson: **1.985, 0.506250, and 0.554763 are three model-specific reports of the
same physical evidence, not competing estimates of one universal efficiency
percentage.** They cannot be compared as if the larger number always indicated
the better organization, and their difference is not a robustness ranking.

The management report should therefore lead with the common capital saving and
service and quality gains. It should add the score whose ruler matches the
study purpose and state that ruler explicitly. The additive total preserves a
declared weighted physical-gap account, RAM locates gaps relative to the
sample's spread, and SBM locates them relative to E's own operation. None of
those normalizations turns the selected plan into a budget instruction or a
causal explanation.

## One SBM family, three management mandates

Once the own-operation ruler has been chosen, orientation determines which
gaps define the formal performance account. All three mainstream orientations
use the same production technology and the same kind of feasible balance, but
they encode different assignments of managerial responsibility:

| Management mandate | Resources | Services | DEAPack estimator |
|---|---|---|---|
| Conserve resources | May fall separately | May not fall | `InputSBM` |
| Expand services | May not rise | May rise separately | `OutputSBM` |
| Redesign operations jointly | May fall separately | May rise separately | `SBM` |

Several historical names collapse into these same contracts on the standard
strictly positive, equal-dimension-weighted domain: the input Russell measure
is input-oriented SBM, the output Russell expansion account is reported
through the reciprocal output-oriented SBM score, and the enhanced Russell
graph (ERG) measure is non-oriented SBM. These are conditional aliases, not
additional model families; other Russell graph, weighted, closest-target, or
signed-data formulations require separate definitions and remain in the
technical Documentation {cite:p}`tone2001`.

```{figure} ../../_static/figures/sbm-management-questions.svg
:name: fig-sbm-three-mandates
:alt: Three management mandates use the same production technology to conserve resources, expand services, or redesign both sides jointly
:width: 100%

Orientation is a statement about decision authority. It determines which
operating improvements define performance; it is not merely a computational
setting.
```

An input orientation is appropriate when service obligations must be
maintained and management is accountable for resource stewardship. An output
orientation fits a capacity-constrained provider asked to increase delivery.
The non-oriented model fits an operational redesign in which both sides may
change. Their feasible plans come from one production account, but their
objectives need not select the same plan. Estimating all three can show whether
a conclusion depends on the mandate; it should not become a search for the
orientation that produces the most convenient ranking.

### Input-oriented SBM: how much resource burden can be released?

The input-oriented score is

$$
\rho_o^I=1-L_o^x
=1-\frac{1}{m}\sum_i\frac{s_i^-}{x_{io}}.
$$

Minimizing $\rho_o^I$ finds the greatest average proportional input saving
while the benchmark continues to produce at least the observed outputs. A
score of 0.80 means that the selected plan retains, on average, 80 percent of
the observed inputs after identified excesses are removed. It does not mean
that every input should be cut by 20 percent.

Output slacks may be feasible, but they do not define this score. The model is
answering a resource-stewardship question, not simultaneously optimizing a
service-expansion programme.

### Output-oriented SBM: how much service remains attainable?

The output-oriented model uses the expansion account $1+L_o^y$ and reports its
higher-is-better reciprocal:

$$
\rho_o^O
=\frac{1}{1+L_o^y}
=\frac{1}{1+\frac{1}{s}\sum_r s_r^+/y_{ro}}.
$$

A score below one indicates that outputs can expand separately without using
more of any input. Because the denominator averages variable-specific gains,
this is not a common radial expansion factor. Input savings may occur in a
feasible solution, but they do not define the output-oriented score.

### Non-oriented SBM: what joint redesign is attainable?

When both resource conservation and service expansion belong to the mandate,
SBM combines the two accounts:

$$
\rho_o^{NO}
=\frac{1-L_o^x}{1+L_o^y}
=\frac{
1-\frac{1}{m}\sum_i s_i^-/x_{io}
}{
1+\frac{1}{s}\sum_r s_r^+/y_{ro}
}.
$$

The numerator and denominator should still be reported separately. A joint
score of 0.80 is not simply 20 percent too much input, 20 percent too little
output, or a 20 percent profit loss. It can combine a modest resource excess
with a larger service shortfall.

With a self-inclusive reference population and the standard positive-data
technology, the non-oriented score equals one exactly when all input and output
slacks are zero. It can therefore certify strong, Pareto--Koopmans efficiency
for this account. A one-sided score of one certifies only the mandate that was
optimized.

## Keep radial, slack, and directional claims distinct

The three model families can use the same empirical production technology
while describing different operating commitments. The
{doc}`03-classical-radial` asks for one common proportional contraction or
expansion and then may complete the selected plan with variable-specific
slacks. Additive, RAM, and SBM make those separate gaps the primary performance
evidence. A radial factor can therefore be one even when a slack-based
comparison still identifies a particular resource saving or service gain
{cite:p}`farrell1957,charnes1978`.

The {doc}`05-directional-distance` instead asks how many units of a
**pre-declared** resource-saving and service-expansion package are feasible.
Its single $\beta$ forces the first-stage changes in that package to move
together in the proportions specified by the direction. Non-oriented SBM does
something different: its input and output gaps may vary separately, and its score
combines their average own-operation proportions. Even when a DDF direction is
constructed from the observed quantities, the resulting $\beta$ is not a
relabelled SBM score {cite:p}`chambers1996,tone2001`.

The practical choice follows the decision. Use a radial account when a common
percentage change is the relevant commitment, a DDF when management has
declared a bundled improvement programme, and a slack account when the study
must diagnose uneven opportunities across represented resources and services.
These are different estimands, not competing algorithms in a race to produce
the lowest or highest score.

## Why orientation changes the conclusion

The bundled `sbm_slack_contrast` dataset contains project-authored neutral
service plans with two inputs and two outputs. One compact workflow fits the
three mandates to the same CRS technology. Tone's equations define the method
{cite:p}`tone2001`; the package example does not reproduce his table:

```python
import pandas as pd

from deapack import (
    DEAData,
    InputSBM,
    OutputSBM,
    SBM,
    dataset_info,
    load_dataset,
)

frame = load_dataset("sbm_slack_contrast")
roles = dataset_info("sbm_slack_contrast").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
)

results = {
    "input": InputSBM(returns_to_scale="crs").fit(data),
    "output": OutputSBM(returns_to_scale="crs").fit(data),
    "joint": SBM(returns_to_scale="crs").fit(data),
}
scores = pd.concat(
    {
        name: result.summary().set_index("dmu_id")["score"]
        for name, result in results.items()
    },
    axis=1,
)
```

The three columns apply distinct resource, service, and joint mandates to the
same observations. Inspect `scores` rather than expecting identical rankings:
a plan can have no supported input saving while retaining an output shortfall,
or the reverse. The non-oriented account combines both sides through the SBM
fraction defined above.

The result can turn that account into a single management-facing display:

```python
figure = results["joint"].plot(
    kind="improvement",
    dmu_id="Uneven",
)
```

```{figure} ../../_static/figures/sbm-slack-contrast-result.svg
:name: fig-sbm-improvement-result
:alt: The uneven service plan's selected SBM account displays variable-specific resource savings and service gains together with original and target quantities
:width: 100%

The selected plan places each operating gap on its own proportional ruler,
while the ledger keeps quantities in their original units. The figure reports
one selected feasible benchmark plan, not a causal diagnosis or a management
order.
```

The left panel makes unlike dimensions comparable without pretending that
they share physical units. The right panel returns to observed and target
quantities that a manager can audit. Reading both panels together prevents a
common mistake: a dimensionless score is useful for comparison, but
operational interpretation still belongs at the variable level.

There is no contradiction when the three orientations classify a plan
differently. Input orientation asks only whether resources can be reduced
while services are maintained; output orientation asks the corresponding
service-expansion question. A one-sided score of one must not be reported as
an unconditional claim of strong efficiency.

The joint result exposes the operational evidence directly:

```python
selected_targets = results["joint"].targets_for("Uneven")
selected_slacks = results["joint"].slacks.query("dmu_id == 'Uneven'")[
    ["role", "variable", "slack", "normalized_slack"]
]
```

Those original-unit values are usually more useful to a manager than the
aggregate score alone. They also let the reader reconstruct the input and
output accounts instead of trusting a black-box ranking.

The table also warns against treating orientation as a robustness race. The
input, output, and joint columns need not preserve the same ranking because
they value different improvements. A ranking change is evidence that the
managerial mandate matters, not evidence that one formulation must be
discarded.

## Targets are evidence, not prescriptions

An SBM score can be well determined while several peer combinations or targets
attain it. Software returns one optimal plan; another equally good plan may
identify different peers or distribute improvements differently. The risk is
greatest on the side omitted from an oriented objective, but alternative
optima can also affect objective-side targets.

A careful report therefore separates the score from the selected plan. Report
the orientation, the proportional input and output accounts relevant to it,
the most important original-unit targets, and whether alternative optima were
examined. A target is evidence that a plan is feasible under the fitted
technology. It is not automatically a budget, quota, forecast, or causal
effect of a management intervention. Peer weights describe a benchmark
construction; they do not prove that copying a named peer will produce the
same outcome.

## Conditions that keep the comparison meaningful

Standard SBM requires strictly positive inputs and outputs because observed
values appear in the denominators. A zero makes relative slack undefined, and
a negative denominator reverses the interpretation of improvement. Adding a
small constant or translating a column changes the estimand and may change
rankings. SBM is unit invariant, but it is not translation invariant.

Returns to scale and the reference population are substantive choices for the
Additive and SBM accounts. CRS allows proportional scaling of observed
activities; VRS compares convex combinations at represented operating scales.
Neither is universally more conservative, so the analyst should choose from
the production setting and report the choice. The named RAM account above is
the deliberate exception: its source profile is VRS and its range population
matches its reference population.

Likewise, the frontier represents only the observations declared eligible as
comparators. Removing the evaluated unit, restricting comparison to a group,
or using another period can change feasibility as well as the score. In the
standard non-oriented positive-data account, a feasible score of one implies
zero normalized slacks algebraically. An external reference can nevertheless
change whether the observed plan belongs to the technology, whether the
comparison is feasible, and what an efficiency classification means. Those
conditions must be re-established rather than borrowed from a self-inclusive
appraisal.

Finally, ordinary SBM assumes desirable outputs and the standard convex
production account. Undesirable outputs, networks, signed data,
super-efficiency, and productivity change require their own technologies or
measures. Keeping those boundaries explicit lets SBM do what it does best:
translate uneven resource excesses and service shortfalls into an auditable
operating-performance account matched to management's actual mandate.
