(radial-scale-analysis)=
# Scale Performance: Separate the Gap from the Response

A hospital board considering regional reorganization needs more than the word
*scale*. One hospital may use its present resources well yet operate at a size
that the comparison population does not support as productive. Another may have
no measured scale gap while still retaining substantial resource waste. A third
may sit at a locally productive scale but face very different service responses
to a small expansion and a small contraction. These findings belong to different
questions; none is automatically a proposal to merge, enlarge, or close a site.

The preceding {doc}`03-classical-radial` chapter separated the common proportional
shortfall from additional resource- or service-specific gaps. Scale analysis asks a
different question: whether the size at which an organization operates changes the
opportunities visible to it. The evidence becomes progressively more local:

| Scale evidence | Management question | Proper conclusion boundary |
|---|---|---|
| Scale efficiency | Does allowing a productive operating pattern to be copied at another organizational size reveal an additional radial performance opportunity? | a matched CRS--VRS performance gap, not a recommended size change |
| Local returns to scale | If the organization changed all resources slightly around the selected efficient plan, would attainable services change by a larger, equal, or smaller proportion? | a supported qualitative response near that plan, not a response magnitude |
| Scale elasticity | How large are the one-sided proportional service responses to a one-percent resource change near that same plan? | a local technical sensitivity, not a demand or financial forecast |

The sequence matters because each result supports a different decision inference.
Scale efficiency compares two matched radial score accounts under CRS and VRS; it
shows how much the permission to replicate operating patterns changes measured
performance. It does not perform slack completion. Local returns and scale elasticity
instead describe the response around a particular Pareto-efficient VRS plan. None of
them values the demand served, the cost and irreversibility of resizing, the effect on
quality or access, or the risks of
reorganization. Those considerations determine whether a technically indicated size
change would create economic or social value.

## Scale efficiency: isolate the additional CRS comparison

Under the same data, orientation, and reference policy, CRS admits all VRS
comparators plus proportional rescaling. Let $TE_o^{CRS}$ and $TE_o^{VRS}$
denote the standardized higher-is-better radial technical efficiencies for the
declared orientation. When the evaluated operation belongs to both reference
technologies, the familiar self-inclusive bounds are

$$
TE_o^{CRS}\leq TE_o^{VRS}\leq1,
$$

and the conventional scale-efficiency ratio is {cite:p}`banker1984`

$$
SE_o=\frac{TE_o^{CRS}}{TE_o^{VRS}}.
$$

An external reference may exclude the evaluated operation, so either
standardized component efficiency can exceed one and the component upper
bound above no longer applies. The matched CRS technology still contains the
matched VRS technology, so a valid positive ratio remains at most one up to
numerical tolerance. What is lost is not that nesting result but the ordinary
self-appraisal interpretation: a ratio of one against an external institution
does not certify conventional scale efficiency. DEAPack therefore retains the
numerical comparison while leaving `is_scale_efficient` missing unless the
evaluated plan belongs to both component technologies.

For input orientation, $TE_o=\theta_o$, so this is
$\theta_o^{CRS}/\theta_o^{VRS}$. For output orientation, the native result is
the expansion factor $\phi_o$ and $TE_o=1/\phi_o$, so the same ratio becomes
$\phi_o^{VRS}/\phi_o^{CRS}$. Writing the ratio in standardized-efficiency form
prevents a contraction factor from being silently mixed with an expansion
factor.

The VRS account asks how the organization compares with a convex opportunity set
that does not grant unrestricted replication. The CRS account also admits scaled
versions of represented operating patterns. Their ratio isolates the additional
radial gap created by that added benchmark right. It is a comparison of two
counterfactual production accounts, not an estimate of the organization's physical
size or the percentage by which it should resize.

This interpretation imposes a strict matching requirement. Dividing a CRS
score for one orientation or peer population by a VRS score for another does
not isolate scale. The data, variable roles, reference membership,
orientation, and period policy must be held fixed.

The `frontier_1x1` case makes the comparison visible:

```python
from deapack import DEAData, load_dataset, scale_efficiency

frame = load_dataset("frontier_1x1")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    inputs="input",
    outputs="output",
)

scale_result = scale_efficiency(data, orientation="input")
scale_result.summary().loc[
    lambda table: table["dmu_id"].isin(["A", "B", "C", "D"]),
    [
        "dmu_id",
        "crs_efficiency",
        "vrs_efficiency",
        "scale_efficiency",
        "is_scale_efficient",
    ],
]

scale_result.plot(
    kind="performance",
    metric="scale_efficiency",
    view="points",
)
```

| DMU | CRS efficiency | VRS efficiency | Scale efficiency |
|---|---:|---:|---:|
| A | 0.800 | 1.000 | 0.800 |
| B | 1.000 | 1.000 | 1.000 |
| C | 0.880 | 1.000 | 0.880 |
| D | 0.760 | 1.000 | 0.760 |

Every ratio in the table rests on two available production comparisons. The
CRS and VRS accounts must each describe a feasible, internally consistent
benchmark before their ratio supports a scale interpretation. If either
account lacks that support, an apparently plausible ratio is not sufficient
evidence for the management comparison or the figure.

D lies on the VRS frontier, but CRS compares it with a proportionally scaled
version of B's more productive pattern. Its scale efficiency of 0.76 says that
admitting continuous replication creates a 24-percent radial gap relative to
the VRS appraisal. It does not say that D should become 24 percent smaller or
that B's organization can be copied without cost.

Only B has scale efficiency one in this view. That statement is deliberately
narrow: admitting proportional replication creates no additional radial gap
for B. It does not prove that every input excess and output shortfall has
disappeared. If both CRS and VRS efficiencies were 0.5, their ratio would also
be one even though the organization retained a large operating shortfall.

Scale efficiency also does not identify whether an organization lies in a
region of increasing or decreasing returns. That requires local information
about the selected efficient plan {cite:p}`banker1984,fare1985`.

```{figure} ../../_static/figures/scale-efficiency-performance-result.svg
:name: fig-scale-efficiency-performance-result
:alt: Scale efficiency for organizations A through D, showing B at one and the other organizations below one
:width: 100%

The display compares the extra radial gap admitted by proportional replication.
It does not recommend a new operating size: the same point plot cannot show
whether a nearby expansion or contraction has increasing or decreasing local
returns, and it contains no evidence about demand or adjustment cost.
```

## Local returns to scale: what happens near the selected plan?

Scale efficiency compares two matched score-only technology appraisals. It
does not itself select a strongly efficient operating target. Local returns to
scale instead begins from a separately selected Pareto-efficient VRS target and
asks how attainable service capacity responds to a small proportional change
in organizational size near that plan
{cite:p}`banker1992,banker2004rts`.

```{figure} ../../_static/figures/local-rts-operating-response.svg
:name: fig-local-rts-operating-response
:alt: Three cards show a ten percent resource increase associated with a larger, equal, or smaller percentage increase in attainable services under increasing, constant, and decreasing local returns
:width: 100%

Local returns describe a benchmark-conditioned operating response. They do not
include demand, prices, adjustment costs, investment constraints, or a decision
to change scale.
```

The three categories have direct operating meanings:

- **increasing returns**: a small proportional increase in all resources can
  support a more than proportional increase in all services;
- **constant returns**: proportional replication is locally supportable; and
- **decreasing returns**: attainable services rise less than resources near
  the selected plan.

These statements concern a coordinated proportional change in the represented
resource and service bundles. Increasing returns does not mean that every service
line benefits equally, and decreasing returns does not prove that bureaucracy or
congestion caused the weaker response. The classification describes what the
maintained production evidence supports; explaining *why* requires organizational
evidence outside the DEA account.

An inefficient observation is not itself assigned a local technology label.
It is first connected to an efficient target under a declared orientation and
target-selection policy. The local-returns statement belongs to that target.
Another orientation can select a different target and therefore answer a
different planning question.

At some efficient plans, the evidence does not support one unique local scale
label. More than one supporting account, and therefore more than one supported
local response, can be consistent with the same selected operating plan. That
is a limitation of the available evidence: management should receive the
supported set rather than a falsely precise single label.

Classical presentations sometimes express this evidence through supporting
hyperplanes and sometimes, under the matched Banker--Thrall conditions, through
optimal intensity sums. Those are alternative representations of the local
production evidence, not different managerial scale outcomes. NIRS or NDRS
technology comparisons are separate categorical procedures and should not be
silently substituted for the selected-plan analysis used here.

In the piecewise DEA technology this ambiguity can occur at a kink. Treating
whichever supporting account happens to be returned first as the only
economically admissible one can create a false classification. The
Banker--Thrall procedure therefore retains the interval of admissible
normalized intercepts; if zero lies in that interval, constant returns belongs
to the supported set even when other supports indicate increasing or
decreasing returns. In DEAPack's stated supporting-valuation convention, a
negative scale term supports increasing returns, zero supports constant returns,
and a positive term supports decreasing returns {cite:p}`banker1992,banker2004rts`.

The five-organization example makes the distinction reproducible:

```python
import pandas as pd

from deapack import DEAData, local_returns_to_scale

scale_frame = pd.DataFrame(
    {
        "unit": ["A", "B", "C", "D", "E"],
        "input": [1.0, 1.5, 3.0, 4.0, 4.0],
        "output": [1.0, 2.0, 4.0, 5.0, 4.5],
    }
)
scale_data = DEAData.from_frame(
    scale_frame,
    dmu="unit",
    inputs="input",
    outputs="output",
)

local_rts = local_returns_to_scale(scale_data, orientation="input")
local_rts.summary()[
    [
        "dmu_id",
        "rts_classification",
        "support_rts_set",
        "support_intercept_lower",
        "support_intercept_upper",
    ]
]
```

| Organization | Reported local RTS | Admissible support types | Intercept interval |
|---|---|---|---:|
| A | increasing | increasing | $[-1,-1/2]$ |
| B | constant | increasing, constant | $[-1/3,0]$ |
| C | constant | constant, decreasing | $[0,1/3]$ |
| D | decreasing | decreasing | $[1/4,+\infty)$ |
| E | decreasing | decreasing | $[2/7,2/7]$ |

E's observed plan $(4,4.5)$ is first compared with the input-oriented VRS
target $(3.5,4.5)$. The decreasing-returns diagnosis therefore belongs to
that target, not to an unqualified point called “E.” A management report
should name both the projection rule and the local classification.

For all five organizations, the production evidence supports the reported
intercept interval. D's positive upper endpoint is unbounded, but that does
**not** mean infinite physical productivity. It means that the selected plan
admits no finite largest normalized supporting intercept; because every
admissible intercept is still positive, the decreasing-returns classification
remains identified. This extended boundary supports an economic conclusion
only when the production evidence also establishes the relevant recession
behavior. Without that evidence, neither the interval nor the classification
is justified by a numerical finding of unboundedness alone.

## Why an RTS category is not a response magnitude

“Increasing,” “constant,” and “decreasing” summarize the direction of a local
scale response; they do not say how large that response is. Two hospitals can
both face decreasing returns while one loses very little productivity as it
expands and the other loses a great deal. If that difference matters to a
planning decision, the analyst can estimate a local scale elasticity: the
percentage change in the largest attainable service bundle associated with a
one-percent proportional change in resources
{cite:p}`forsund2004scale,podinovski2017rts`.

At the selected efficient target $(\widehat x_o,\widehat y_o)$, let

$$
\bar\beta_o(\alpha)
=\max\{\beta:(\alpha \widehat x_o,\beta \widehat y_o)\in\mathcal T\},
\qquad \bar\beta_o(1)=1.
$$

$\alpha$ describes a common proportional change in the represented resources,
while $\bar\beta_o(\alpha)$ records the largest supported proportional service
bundle at that resource scale. The scale-up and scale-down responses are the two
one-sided derivatives

$$
\epsilon_o^+=\bar\beta'_{o,+}(1),
\qquad
\epsilon_o^-=\bar\beta'_{o,-}(1),
\qquad
\epsilon_o^+\leq\epsilon_o^-.
$$

An expansion response of $0.8$, for example, says that a one-percent increase in
all represented resources supports approximately $0.8$ percent more of the same
proportional service bundle near that target. It is not an estimate of revenue,
profit, demand, or the productivity of an additional employee considered alone.

DEA frontiers are piecewise linear, so scale-up and scale-down may have
different one-sided responses at the same efficient target. A constant-returns
classification can therefore be supported even when neither response equals
exactly one: one side of the target may be below proportional and the other
above proportional. This is why an RTS label should not be converted into an
assumed percentage effect.

The relationship between the qualitative and quantitative accounts is

$$
\begin{aligned}
\text{increasing returns:}&\quad 1<\epsilon_o^+\leq\epsilon_o^-,\\
\text{decreasing returns:}&\quad \epsilon_o^+\leq\epsilon_o^-<1,\\
\text{constant returns supported:}&\quad
\epsilon_o^+\leq1\leq\epsilon_o^-.
\end{aligned}
$$

The last line is especially important at a kink: *constant supported* need not
mean one unique elasticity equal to one. It means that zero belongs to the
admissible support interval, so a constant-returns supporting account is
consistent with the target even when the two one-sided responses differ.

Scale elasticity remains a local technical sensitivity. It is not a demand
forecast, a financial return, or evidence that management should change size.
DEAPack's `scale_elasticity` transforms the same selected target and complete
support interval used by `local_returns_to_scale`; it does not invent a second
target to obtain a more convenient response. The package documentation provides
the orientation-specific transformations and boundary conventions. A core
management report can usually stop after stating scale efficiency, the projected
target, and its supported RTS classification; the two elasticities belong in the
report when the magnitude or the asymmetry of a local response matters.

## What a scale result can support

These scale assessments describe represented production opportunities.
Expansion or contraction decisions additionally require demand, prices and
costs, quasi-fixed resources, service obligations, risk, transition capacity,
and implementation constraints. A local response is not a forecast, and a
scale gap is not a business case.

Most productive scale size, congestion, and short-run physical capacity ask
additional questions and require additional maintained quantities. In
particular, congestion asks whether reducing a particular excessive input can
raise attainable output. That claim requires a different production or
disposability account: decreasing returns merely describes a weaker
proportional response to expansion, while an ordinary input slack shows only
that a resource can fall without reducing output. Neither one, and neither the
CRS--VRS scale ratio, establishes congestion. Any analysis of these concepts
must state its production assumptions and evidence separately rather than turn
a scale-efficiency result into a broader management claim.

The next chapter changes the focus from common proportional gaps and local
scale response to variable-specific resource excesses and service shortfalls:
{doc}`04-sbm`.
