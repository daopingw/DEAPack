# Constructing an Empirical Production Technology

The previous chapter defined the organization, the quantities in its
production account, and the population from which it may credibly learn. The
resulting data record what those organizations did. They do not, by
themselves, say what else could have been done.

Suppose a health authority observes one hospital with a small resource base
and another with a larger one. May a third hospital be compared with a
half-and-half combination of their practices? May the smaller hospital's
operating pattern be replicated at twice its scale? Should a plan that uses
more resources to deliver less care still count as technologically possible?
Each answer changes the opportunities against which management will be
judged.

DEA therefore needs an explicit answer to a question that sits between study
design and efficiency measurement:

> Which operating plans should the observed evidence make available as
> benchmarks, including plans that no single organization has been observed
> to carry out?

This chapter develops that answer as an economic account of production
possibilities. The diagrams make the assumptions visible, but the diagrams
are not the theory. The theory concerns resource commitments, service
capability, organizational divisibility, and the scale over which operating
practices can reasonably be transferred.

## A technology is a claim about attainable operating plans

Let $n$ eligible decision-making units use $m$ inputs to produce $s$
desirable outputs. Following the book's common notation, write

$$
X=[x_1,\ldots,x_n]\in\mathbb R_+^{m\times n},
\qquad
Y=[y_1,\ldots,y_n]\in\mathbb R_+^{s\times n}.
$$

The production technology

$$
\mathcal T=\{(x,y):x\text{ can produce }y\}
$$

collects the resource--service plans treated as attainable for the study.
The word *can* carries every decision made in the preceding chapter: the
organizational boundary, decision horizon, variable meanings, eligible peer
population, and operating conditions. A hospital-year that is attainable in
a long-run regional capacity review need not be attainable in next month's
staffing plan.

The hat in $\widehat{\mathcal T}$ will mark a technology constructed from the
sample. DEA does not recover a timeless engineering law merely by enveloping
the data. It combines observed practice with maintained production
assumptions. The **frontier** is the best-practice edge of that constructed
opportunity set: the operating plans for which the improvement under
consideration has been exhausted. **Technical efficiency** then describes an
organization's position relative to that edge. Both conclusions are
conditional on the opportunity set, not intrinsic grades attached to the
organization {cite:p}`farrell1957,fare1985`.

Every admitted observation must belong to the empirical technology. Otherwise
the model would declare its own evidence infeasible. Observations alone,
however, leave large gaps between operating plans and say nothing about plans
that use more resources or supply fewer services. The next assumptions decide
how those gaps are filled.

## Free disposal: feasibility is not approval

For ordinary inputs and desirable outputs, classical DEA usually assumes
**free disposability**. If $(x,y)$ is attainable, then a plan using at least
as much of every input and delivering no more of every desirable output is
also admitted:

$$
(x,y)\in\mathcal T,\quad \widetilde x\geq x,\quad 0\leq \widetilde y\leq y
\quad\Longrightarrow\quad
(\widetilde x,\widetilde y)\in\mathcal T.
$$

Economically, the assumption says that an organization can leave some
resource capacity idle, waste an input, or withhold part of a desirable
service without making the plan physically impossible. It does **not** say
that waste is costless, that reducing service is acceptable, or that every
quantity is under the evaluated manager's control. An input-oriented study
can still protect the recorded service commitment; free disposal merely says
what belongs to the wider production possibility set.

This apparently modest assumption can fail in important settings. Congestion
may make additional input harmful rather than harmless. A minimum-service
mandate can make some output reductions institutionally unavailable. A
pollutant cannot generally be discarded as though it were an ordinary
desirable service: reducing it may require resources or a simultaneous change
in production. Part III therefore states a different production account for
undesirable outputs instead of changing their signs and carrying on.

## Convexity: may practices be combined?

A second decision concerns plans that were not observed in their entirety.
Let $\lambda\in\mathbb R_+^n$ assign weights to eligible observations. The
quantities

$$
X\lambda\quad\text{and}\quad Y\lambda
$$

describe the resources and services of a reference activity. Nonzero
$\lambda_j$ values identify the observed practices contributing to that
activity. They are evidence weights, not estimates of causal influence and
not literal instructions to merge organizations.

Under **convexity**, any weighted average of feasible activities is also
treated as feasible, with nonnegative weights satisfying
$\mathbf 1^\top\lambda=1$. Before looking at the first diagram, read A and D as two
complete annual operating accounts: two ways of organizing resources and services
whose quantities must remain internally consistent. The orange point M is not a third
observed organization. It describes what the study treats as attainable when capacity
can be divided between those two ways of operating.

```{figure} ../../_static/figures/convex-virtual-dmu.svg
:name: fig-convex-virtual-dmu
:alt: Observed activities A and D form the unobserved composite reference activity M through a convex combination
:width: 88%

Convexity admits the composite activity
$M=0.5A+0.5D=(2.5,2.4)$ even though M was not observed. Economically, the
assumption says that half of the activity can be organized as A operates and half as
D operates, without losing the resources or services recorded in either share.
```

The line between A and D is credible when capacity is divisible, operating
practices can be used for fractions of the year, or a portfolio organization
can allocate activity across sites. A regional provider, for example, might assign
half of its workload and capacity according to clinic A's practice and the remainder
according to clinic D's. In that setting M is a feasible aggregate plan even if no
individual clinic has reported exactly those quantities. Convexity does not allow a
manager to take A's resource requirement while claiming D's service outcome; the
resource and service commitments of each activity travel together.

Convexity is much stronger when production depends on indivisible assets,
threshold effects, or a tightly integrated process. A hospital cannot install
half of one emergency department and half of another; a treatment pathway may
fail if its component practices are separated. In such cases M is arithmetically
well defined but may not be managerially attainable. A virtual combination
also says nothing about *how* to implement the plan. It supports a benchmark
quantity account, not a causal recipe for organizational change.

With free disposal and convexity, the familiar variable-returns-to-scale
empirical technology is

$$
\widehat{\mathcal T}_{VRS}
=\left\{(x,y):
X\lambda\leq x,
\;Y\lambda\geq y,
\;\mathbf 1^\top\lambda=1,
\;\lambda\geq0
\right\}.
$$

The inequalities incorporate free disposal: the reference activity may use
no more than $x$ and supply at least $y$. The equality makes
$X\lambda,Y\lambda$ a weighted average of represented operations. This
convex envelopment is the production account underlying the BCC models
{cite:p}`banker1984`.

### FDH when only complete observed practices may teach

Convexity is not required for an empirical frontier. The free-disposal hull
(FDH) admits free disposal around each observation but does not fill the gaps
between observations:

$$
\widehat{\mathcal T}_{FDH}
=\left\{(x,y):
\text{some observed }j\text{ satisfies }x_j\leq x,
\;y_j\geq y
\right\}.
$$

An FDH comparison therefore asks whether one complete observed practice
demonstrates a better resource--service plan. Convex VRS asks the broader
question of whether a weighted combination of observed practices does so
{cite:p}`deprins1984,tulkens1993`.

FDH can be more persuasive when operating systems are indivisible or when an
implementation discussion needs an observed organizational counterpart. It
is not automatically safer or more realistic. In a sparse sample, the
observed-practice steps can leave many organizations on the frontier simply
because no single comparator dominates them. Convex VRS usually produces a
more demanding opportunity set because it also admits intermediate plans;
that extra discipline is warranted only when those plans have a credible
production interpretation.

The right comparison is thus not “modern versus old” or “strict versus
lenient.” It is a choice between two learning claims. The next chapter keeps
one service-branch dataset fixed and compares DEAPack's
`FDH(orientation="output")` with `BCC(orientation="output")`, so the change
in the result can be read as sensitivity to this claim rather than as a
difference between unrelated efficiency concepts.

## Returns to scale: may an operating pattern be replicated?

Convexity asks whether practices can be mixed. **Returns to scale** asks
whether an operating pattern can be proportionally enlarged or reduced. The
questions are related but not interchangeable.

Under constant returns to scale (CRS), any nonnegative multiple of a feasible
activity is also feasible. The empirical technology is

$$
\widehat{\mathcal T}_{CRS}
=\left\{(x,y):
X\lambda\leq x,
\;Y\lambda\geq y,
\;\lambda\geq0
\right\}.
$$

Without the restriction $\mathbf 1^\top\lambda=1$, the total weight may
be below or above one. An observed operating pattern can therefore be
contracted or replicated while preserving its input--output proportions. The
CCR model uses this constant-returns production account
{cite:p}`charnes1978`.

CRS is a demanding economic assumption, not merely a tougher scoring option.
It can be credible for a long-run question when facilities and teams are
replicable, inputs and outputs are sufficiently divisible, markets can absorb
the service, and organizations face comparable operating conditions. It is
harder to defend when fixed assets, minimum staffing, demand limits,
geography, regulation, or coordination costs make a twofold operation more or
less than two copies of the original.

VRS withdraws the right of unrestricted proportional replication. It allows
productivity to differ with operating scale and restricts convex reference
plans to the scales represented by weighted averages of the sample. This does
not mean that a VRS comparator must be the same size as the focal
organization, nor does VRS by itself control for mission or environment. It
means only that scale adjustment must be supported by combinations of the
represented operations rather than by free replication.

The second diagram shows the practical consequence of the scale assumption. Branch D
is compared first with similarly scaled combinations of observed practice under VRS.
CRS then asks a more demanding question: if B's resource-to-service pattern could be
replicated continuously, how much of D's resource budget would still be needed to
honour D's service commitment? The horizontal movement records that additional
resource-saving opportunity; it is not a recommendation to copy B literally.

```{figure} ../../_static/figures/crs-vrs-frontiers.svg
:name: fig-crs-vrs-frontiers
:alt: The same observations generate a piecewise VRS frontier and a CRS ray through the most productive activity
:width: 95%

All four branches lie on the VRS boundary in this illustration. Branch B also
supports the strongest continuously scalable pattern under CRS. The arrow
from D to $D_{CRS}$ records the additional resource-saving opportunity created
by granting that replication right.
```

Under VRS, D is not required to operate as a multiple of B and is efficient
relative to the represented convex opportunities at its scale. Under CRS,
B's resource--service ratio may be carried to D's service commitment, making
$D_{CRS}$ an admissible and more demanding plan. The gap between the two
accounts is conditional evidence that D's assessed performance depends on the
scale assumption. It is not proof that D should contract, that B caused the
gap, or that B's organization can be copied without transition costs.

The picture uses one input and one output, but the same economic question
survives when no honest two-axis drawing is possible. A higher-dimensional
reference plan may draw on several organizations, and the strongest CRS
benchmark need not be an observed unit. What matters is still the production
claim: which combinations and replications could management plausibly make
available over the stated decision horizon?

## Orientation identifies the commitment to protect

The technology determines which plans count as attainable. **Orientation**
does not alter that set; it states which commitment is protected while the
organization is compared with it. An input-oriented account preserves the
represented service commitments and examines controllable resource saving. An
output-oriented account respects the represented resource limits and examines
service expansion {cite:p}`farrell1957,charnes1978,banker1984`.

Moving between these questions does not turn CRS into VRS, remove convexity,
or create a new peer population. It changes the responsibility being assessed.
Input orientation is difficult to defend when most resources are fixed over
the decision horizon; output orientation is difficult when demand, service
obligations, or quality constraints rule out common expansion.

The first chapter introduced the corresponding contraction and expansion
factors. Part II turns them into the four classical radial programmes. When a
decision instead requires resource saving and service expansion together, or
variable-specific changes, later slack-based and directional accounts provide
different measures on a declared technology. None of these comparisons is a
causal promise that management can implement the reported change without
operational evidence, prices, and adjustment costs.

## Efficiency is conditional evidence, not a verdict

An organization is efficient only relative to a declared technology and a
declared improvement question. A score of one under input-oriented VRS means
that the represented convex technology offers no further common proportional
input saving while the output commitments are protected. It does not, by
itself, establish that

- every individual input excess and output shortfall has disappeared;
- the organization minimizes cost or maximizes profit;
- service quality, environmental harm, or unmeasured mission is satisfactory;
- the current scale is most productive under CRS; or
- the selected benchmark would cause the organization to improve.

This conditional reading also explains why results change when credible
assumptions change. FDH and convex VRS admit different learning opportunities.
CRS and VRS grant different replication rights. Input and output orientation
protect different commitments. A changed score is therefore evidence about
the consequence of a changed production statement, not evidence that one of
the calculations must be wrong.

Before fitting a model, the analyst should be able to defend four propositions
in the language of the organization: ordinary resources and desirable
services are disposable in the stated sense; virtual combinations are or are
not attainable; proportional replication is or is not credible over the
decision horizon; and the chosen orientation matches the decision-maker's
commitment. Those propositions are more informative than a model acronym.

The next chapter turns them into the four classical radial recipes:
{doc}`../02-classical/03-classical-radial`. Its `CCRInput`, `CCROutput`,
`BCCInput`, and `BCCOutput` examples keep the production account visible while
changing orientation and scale. The purpose is not to memorize four model
names, but to see how a resource or service question becomes a reproducible
DEA comparison.
