# Directional Distance Functions

Classical radial models ask for a common percentage reduction in resources or a
common percentage increase in services. Slack-based models reveal where individual
resources or services depart from best observed practice. Many decisions, however,
arrive as a concrete package: “save ten agency-staff hours, release two staffed
bed-days, and complete five additional treatments.” Such a package reflects staffing
constraints, service priorities, and the trade-offs that management is prepared to
consider; it need not resemble a proportional movement in every variable.

The directional distance function (DDF) asks how much of such an
**operating-improvement package** is attainable in light of comparable organizations'
experience. Before the model is fitted, the study must identify which quantities
management is responsible for changing, which service or resource commitments cannot
be breached, what one unit of the programme means in physical terms, and the decision
horizon over which the change could reasonably occur. The direction is therefore an
economic specification of the proposed improvement and must be fixed before the
results are known {cite:p}`chambers1996`.

Specifying the package in advance does not turn an aspiration into a forecast. It
defines the counterfactual against which feasible operating opportunities will be
appraised. A board-approved plan, a regulator's service obligation, or an engineering proposal may
supply the direction; the optimization itself cannot reveal which programme the
organization ought to value. Choosing a direction only after inspecting alternative
rankings would reverse the logic of the exercise.

Hold one recorded operation fixed. Organization E uses 2.00 units of labor and 2.80
units of capital to provide 1.30 units of service and 0.62 units of quality. The same
eligible organizations and the same VRS technology can support three different studies
because the analyst sets three different improvement packages for three
management questions before the model is fitted.

```{figure} ../../_static/figures/ddf-programme-contracts-result.svg
:name: fig-ddf-programme-contracts
:alt: Organization E has the same labor, capital, service, and quality record under three directional improvement programmes specified in advance. One promises proportional resource savings while protecting service commitments, one promises proportional service gains without requiring resource savings, and one requires resource savings and service gains together. Each card reports beta and the corresponding original-unit first-stage commitments, followed by a warning that the three beta values are not a common efficiency ranking.
:width: 78%

One operation, three improvement programmes specified before estimation. In each
card, one programme unit is a physical commitment to save named resources, add named
services, or do both together. The fitted $\beta$ states how much of that
commitment is attainable, and every resulting change remains in the variable's
original unit. The cards report only what this specified programme promises;
additional slack completion is a later and separately identified claim.
```

Read {numref}`fig-ddf-programme-contracts` as three different management decisions,
each with a different operating promise. With
$g=(x_E,0)$, the fitted
$\beta=0.247253$ supports first-stage labor and capital savings of 0.494505
and 0.692308 while protecting the recorded service commitments. Because the
direction is proportional to E's inputs, this is also the statement that the
programme retains $1-\beta=0.752747$ of each recorded input.

With $g=(0,y_E)$, the fitted $\beta=0.419355$ supports additions of 0.545161
service and 0.260000 quality while requiring no resource saving in the
specified package. The resource budget is protected: the benchmark may not use
more than E records, but a later slack-completion step may still identify a
specific resource saving.

With $g=(x_E,y_E)$, $\beta=0.247253$ means that the two resource savings must
be feasible together with additions of 0.321429 service and 0.153297 quality.
The equality between the input-only and joint values in this example does not
make the decisions equivalent. Likewise, the larger output-only value does
not rank that programme as better or E as less efficient. Each $\beta$ counts
units of its own specified package.

A zero direction therefore means “no change required by the first-stage
package,” not “this quantity can never improve.” Once the specified package is
exhausted, a separate completion search may reveal additional
variable-specific opportunities. Those opportunities must not be rewritten
as part of the analyst's original programme specification.

The three programmes also clarify what the word *protected* means. In the input-saving
programme, E's recorded services are minimum commitments; in the service-expansion
programme, its recorded resources are maximum allowances. Protection is thus a
one-sided feasibility promise, not necessarily an instruction to reproduce the
recorded quantity exactly. If a feasible reference plan uses still less of a resource
or supplies still more of a service, that further opportunity appears as slack rather
than as part of the specified package.

A DDF number is consequently incomplete on its own. A defensible report must travel
with the production technology, the management responsibility being evaluated, the
quantities protected by that decision, the physical content and normalization of one
programme unit, and the eligible organizations supplying the evidence. If the report
omits those choices, a value labelled “directional efficiency” has no stable operating
meaning.

## What one unit of the improvement programme changes

One unit of the operating-improvement package names a physical commitment: specified
quantities of inputs to save and desirable outputs to add. Let $g_i^x$ be the amount
of input $i$ saved by one unit of that package, and let $g_r^y$ be the amount of
desirable output $r$ added. Collect these nonnegative quantities as
$g=(g^x,g^y)$, with $g^x\in\mathbb R_+^m$ and
$g^y\in\mathbb R_+^s$. The components carry the units of their corresponding
variables *per programme unit*. A nonzero component should therefore belong to the
responsibility and decision horizon defined by the study, not merely be available in
the dataset.

For an observed operation $(x_o,y_o)$ and a feasible technology $\mathcal T$, the DDF
is

$$
D_{\mathcal T}(x_o,y_o;g)
=\sup\left\{
\beta:
(x_o-\beta g^x,\;y_o+\beta g^y)\in\mathcal T
\right\}.
$$

The subtraction of $\beta g^x$ records resource saving; the addition of
$\beta g^y$ records service expansion. The optimized value $\beta_o$ is the largest
number of specified programme units that the technology supports. The quantities with
direct operating meaning are therefore

$$
\text{input saving}=\beta_o g^x,
\qquad
\text{output addition}=\beta_o g^y.
$$

For example, suppose one hospital package means saving 10 agency-staff hours and 2
staffed bed-days while adding 5 completed treatments. If $\beta_o=0.4$, the comparison
evidence supports a coordinated saving of 4 staff hours and 0.8 bed-days together
with 2 additional treatments. The value 0.4 is not a general statement that the
hospital is “40 percent inefficient.” It says that 40 percent of this particular
programme remains attainable relative to the stated benchmark. Only when the
direction is defined from the hospital's observed quantities does $\beta_o$ acquire a
common percentage interpretation.

Nor does $\beta_o$ live on a universal zero-to-one efficiency scale. A value above one
simply means that more than one specified package is shown to be attainable. A
smaller positive value means less of *that same package* remains, but values based on
different packages do not provide a common ranking. The economically interpretable
object is the pair $(\beta_o,g)$, and its operating content is the vector
$\beta_o g$.

This distinction also explains why the unit used to describe the package matters. If
the same package is written $c$ times larger for $c>0$, the number of attainable
packages becomes $1/c$ as large:

$$
D_{\mathcal T}(x,y;cg)
=\frac{1}{c}
D_{\mathcal T}(x,y;g).
$$

The reported distance changes, but the supported physical changes $\beta g$ do not.
This is a change of programme unit, just as reporting a resource quantity in tonnes
rather than kilograms changes the numeral but not the quantity. A second property has
an equally direct reading. If an organization has already completed $\alpha$ units of
the same package, the remaining attainable number falls by $\alpha$, whenever the
adjusted operation remains in the relevant domain:

$$
D_{\mathcal T}
(x-\alpha g^x,y+\alpha g^y;g)
=D_{\mathcal T}(x,y;g)-\alpha.
$$

Consequently, two DDF values are directly comparable only when they refer to
substantively comparable programme definitions and normalizations. A fixed physical
programme can provide a common unit across organizations. A direction proportional to
each organization's own operation instead supports a locally scaled percentage
question, but the physical content of one programme unit then differs across
organizations. These properties connect directional distance to the Luenberger
benefit-function and price-space accounts developed by Chambers, Chung, and Färe
{cite:p}`chambers1996`.

## How the empirical benchmark appraises the programme

Under an empirical DEA technology $\widehat{\mathcal T}$, eligible organizations
supply the reference activities from which the benchmark is formed. For a declared
programme $g$, the unified directional programme is

$$
\begin{aligned}
\max_{\beta,\lambda}\quad &\beta\\
\text{s.t.}\quad
&X\lambda\leq x_o-\beta g^x,\\
&Y\lambda\geq y_o+\beta g^y,\\
&\lambda\geq0,
\end{aligned}
$$

with the chosen returns-to-scale restriction. The reference plan
$(X\lambda,Y\lambda)$ must use no more than the resources left after the declared
saving and must deliver at least the services promised after the declared addition.
Maximizing $\beta$ finds the largest common multiple of the whole package. Under VRS
the reference weights also satisfy $\mathbf 1^\top\lambda=1$; under CRS they may
represent proportional replication. As elsewhere in DEA, the active $\lambda_j$
values identify the observed activities supporting the comparison; they are evidence
for feasibility, not literal instructions to combine organizations.

A zero component of $g$ says that the first-stage package claims no required change in
that variable. It does not remove the variable from the production account, and it
does not rule out a further input saving or output gain supported by free disposability
and slack completion. The recorded output remains a minimum commitment and the
recorded input remains a maximum allowance unless the study has specified a different
technology. At least one direction component must be positive; otherwise no
improvement programme has been proposed.

The principal direction choices can now be read as different management contracts and
economic units of account:

| Management task | Input package $g^x$ | Output package $g^y$ | Meaning of $\beta$ |
|---|---|---|---|
| Conserve the current resource bundle proportionally | Observed inputs $x_o$ | Zeros | Common fraction of current inputs saved |
| Expand the current service bundle proportionally | Zeros | Observed outputs $y_o$ | Common fraction of current outputs added |
| Improve both sides proportionally | Observed inputs $x_o$ | Observed outputs $y_o$ | Common fraction saved and added together |
| Evaluate a documented operating programme | Declared physical savings | Declared physical additions | Number of programme units attainable |

Using observed quantities as the direction gives each organization a package relative
to its own operation. If quantities and their directions are converted to new units
together, the resulting $\beta$ is unchanged. A fixed physical package instead asks
every organization to attempt the same quantity changes and may be preferable when a
system-wide plan has already been stated in physical units. Neither choice is neutral:
the first gives organizations different physical packages, whereas the second may be
more demanding for smaller operations.

A direction of ones is merely the special case “one measurement unit of every named
quantity.” It has no automatic economic neutrality, because one employee, one bed-day,
and one unit of service are neither commensurate values nor equally difficult changes.
Likewise, the direction is not a vector of prices or preference weights. It defines a
bundle of quantity changes; monetary value, adjustment cost, and managerial priority
require information outside the technical-efficiency model.

A reproducible study should therefore record every direction component beside the
corresponding variable name and physical unit, explain why the change belongs within
the accountable manager's decision rights and time horizon, and state the substantive
normalization used for comparisons. A vector becomes a policy target, managerial
commitment, or engineering requirement only when evidence outside the optimization
supports that description.

## The range directional measure: construct the package from observed ranges

The ordinary DDF requires the analyst to declare an improvement package. The range
directional measure (RDM) answers a different, sample-dependent question: what common
share of the focal organization's remaining coordinatewise opportunities is jointly
feasible? For each input, “remaining opportunity” is the distance down to the lowest
observed input in the exact comparison population; for each desirable output, it is
the distance up to the highest observed output. The original RDM fixes a VRS
technology and allows finite signed quantities without changing their economic roles
{cite:p}`portela2004`.

A negative value is therefore not automatically an undesirable output. In the
output-oriented illustration below, both signed accounts are desirable and higher is
preferred. Every observation uses the same one-unit resource input. The three
displayed coordinates are project-designed synthetic values:

$$
F=(-2,1),\qquad N=(-1,5),\qquad E=(4,0).
$$

The coordinatewise aspiration is $I=(4,5)$, so the focal unit's output range
direction is $I-F=(6,4)$. The aspiration combines the best value in each account but
need not itself be feasible. The ray from $F$ reaches the VRS frontier at

$$
T=(1,3)=0.6N+0.4E=F+\tfrac{1}{2}(I-F).
$$

Thus the native RDM distance is $\beta_F=1/2$: one half of both remaining
opportunities is attainable together. The corresponding higher-is-better RDM
efficiency is $1-\beta_F=1/2$.

```{figure} ../../_static/figures/range-directional-signed-opportunity.svg
:name: fig-range-directional-signed-opportunity
:alt: A project-designed three-unit signed-output example. Focus F is at minus two and one, North N is at minus one and five, and East E is at four and zero. The coordinatewise aspiration I is four and five. The ray from F toward I meets the VRS segment between N and E at T equals one and three, exactly halfway along the opportunity vector. A calculation panel verifies that T equals 0.6 N plus 0.4 E, beta equals one half, and RDM efficiency equals one half.
:width: 96%

An exact output-oriented RDM account built from original synthetic teaching values.
The plot layout and observations were created for this Handbook; no published
empirical records or source figure are reproduced. The literature citation supports
the model definition, not the illustrative coordinates.
```

The same account is reproducible directly with the public Python API; it does not
depend on a bundled dataset:

```python
import pandas as pd

from deapack import DEAData, RDM

frame = pd.DataFrame(
    {
        "dmu": ["Focus", "North", "East"],
        "resource": [1, 1, 1],
        "account_1": [-2, -1, 4],
        "account_2": [1, 5, 0],
    }
)
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    inputs="resource",
    outputs=["account_1", "account_2"],
)
result = RDM(orientation="output").fit(data)

result.summary()[["dmu_id", "beta", "rdm_efficiency"]]
result.peers("Focus")[["reference_dmu_id", "lambda"]]
```

For Focus, the selected frontier witness assigns $0.6$ to North and $0.4$ to
East. Those lambdas establish feasibility inside the fitted VRS technology; they are
not implementation weights or causal contributions. The value $\beta=1/2$ is a
share of the *remaining opportunity vector*, not 50 percent of either signed level.
Changing the comparison population can change the coordinatewise aspiration, the
direction, and the score at once. RDM should therefore travel with the admitted
population and the input/output roles, just as an analyst-declared DDF must travel
with its direction and units.

## Radial measures as special cases

The radial models from the opening of Part II are not rival technologies. They are
directional programmes whose content is tied to the focal organization's observed
bundle. For input orientation, one programme unit means saving 100 percent of each
recorded input while requiring no first-stage output addition. Setting
$g^x=x_o$ and $g^y=0$ gives

$$
x_o-\beta_o x_o=(1-\beta_o)x_o,
\qquad
\theta_o=1-\beta_o.
$$

Thus $\beta_o$ is the common share of recorded inputs that can be saved and
$\theta_o$ is the share retained. For output orientation, one programme unit means
adding 100 percent of every recorded desirable output while requiring no first-stage
input saving. Setting $g^x=0$ and $g^y=y_o$ gives

$$
y_o+\beta_o y_o=(1+\beta_o)y_o,
\qquad
\phi_o=1+\beta_o.
$$

Here $\beta_o$ is the common output addition relative to the recorded bundle and
$\phi_o$ is the corresponding expansion factor. These identities explain why one
directional framework can represent several historically named radial programmes
{cite:p}`farrell1957,chambers1996`. They also expose the limits of the equivalence.
The input case maps to $\theta_o=1-\beta_o$, whereas the bounded display of the output
case is $1/\phi_o=1/(1+\beta_o)$. A joint programme with
$g=(x_o,y_o)$ requires input savings and output additions together; it is not either
one-sided Farrell programme and has no generic Farrell-score transformation.

The native DDF quantity remains $\beta_o$: the attainable amount of the declared
improvement programme. Re-expressing one radial special case on a bounded scale does
not license the same transformation for every direction. Empirical reports should
therefore state $\beta_o$, the full direction, and the resulting original-unit changes
before presenting any convenience rescaling. This keeps a familiar historical name
from obscuring the management contract it represents.

## A joint resource-and-service operating counterfactual

The `slacks_2x2` dataset illustrates a direction proportional to every observed input
and output. For each organization, one programme unit is normalized to its full
recorded resource bundle and its full recorded service bundle. That normalization
makes $\beta$ a common percentage within the organization's own account; it does not
claim that eliminating 100 percent of resources while adding 100 percent of services
would be a literal implementation plan. The attainable fraction and its original-unit
components remain the quantities to interpret.

```python
from deapack import DDF, DEAData, load_dataset

frame = load_dataset("slacks_2x2")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    inputs=["labor", "capital"],
    outputs=["service", "quality"],
)

result = DDF(
    input_direction="observed",
    output_direction="observed",
    returns_to_scale="vrs",
).fit(data)

result.summary()[
    ["dmu_id", "distance", "max_slack"]
]
```

```{figure} ../../_static/figures/ddf-improvement-result.svg
:name: fig-ddf-improvement-result
:alt: Four original-unit operating accounts for organization E, each proceeding from the observed quantity to the target promised by beta times the declared direction and then to the selected slack-completed target
:width: 96%

Organization E's joint resource-saving and service-expansion account. Each row keeps
the variable's original unit: it first records what the common declared programme
delivers and then identifies any additional variable-specific opportunity in the
selected completed plan. The rows deliberately do not share a quantity axis.
```

The same fitted account can be displayed without estimating another model:

```python
result.plot(kind="improvement", dmu_id="E")
```

The three entries form a benchmark accounting sequence, not a claim that any change
has already been implemented. The observed quantity is the baseline. The directional
target shows exactly what $\beta_E g$ promises under the analyst's declared package.
The slack-completed target records the additional variable-specific saving or service
gain in one selected strongly efficient benchmark plan. Keeping those stages separate
preserves the distinction between the programme management chose to appraise and the
residual opportunities the empirical benchmark subsequently revealed. The account
retains $\beta$ rather than replacing it with a convenience transformation, because
its management meaning is the attainable number of declared resource-and-service
packages.

For E, $\beta_E=0.247253$. Under the analyst's chosen operating counterfactual, the
same proportional amount of each observed input can be saved while the same
proportional amount of each observed output can be added: about 24.7 percent in both
cases. The benchmark also reveals variable-specific service and quality opportunities
after that common package has been exhausted within the fitted technology:

| Role | Variable | Observed | Target under $\beta g$ | Extra slack | Completed target |
|---|---|---:|---:|---:|---:|
| Input | Labor | 2.000000 | 1.505495 | 0.000000 | 1.505495 |
| Input | Capital | 2.800000 | 2.107692 | 0.000000 | 2.107692 |
| Output | Service | 1.300000 | 1.621429 | 0.031319 | 1.652747 |
| Output | Quality | 0.620000 | 0.773297 | 0.057253 | 0.830549 |

The table displays each quantity independently to six decimal places, so an
addition performed on the printed entries can differ from the printed target
by one unit in the last decimal. DEAPack reconstructs and certifies the
account at full numerical precision before rounding it for the reader.

Service and quality retain additional output shortfalls of 0.031319 and 0.057253 after
the joint percentage improvement. The complete operating target is consequently not
obtained from $y_o+\beta g^y$ alone.

```python
result.targets_for("E")[[
    "role",
    "variable",
    "observed",
    "direction",
    "directional_change",
    "target",
]]
```

The target table retains the direction and $\beta g$ so a saved result remains
interpretable without reconstructing the original model call.

This is a conditional benchmark, not evidence that the observed gaps were caused by
management. The completion stage selects one feasible strong target; it does not show
that the target is unique, least costly, operationally preferred, or prescriptive.
Prices, adjustment costs, service obligations, and evidence about causal constraints
belong in the decision process before this benchmark is adopted as a plan.

## After the declared improvement package is exhausted

When $\beta_o=0$, no positive amount of the whole declared package remains feasible.
The organization is therefore **directionally efficient for that particular
counterfactual**. The qualification matters. A hospital may be unable to deliver any
more of a joint “save 5 percent of every input and add 5 percent of every service”
package while still being able to save energy alone or expand one clinic alone. The
package can be exhausted even though a componentwise improvement remains.

Strong efficiency makes the additional claim that no ordinary input excess or
desirable-output shortfall remains. Holding the optimal $\beta_o$ fixed, a completion
search can select a feasible plan that removes such residual slacks. This is where the
preceding slack chapter and the DDF account meet, but their roles should not be merged.
In SBM, variable-specific proportional slacks define the performance measure. Here,
slacks complete a target *after* the declared directional measure has been optimized.
They do not revise $\beta_o$, change $g$, or retroactively enlarge the management
programme.

When completion succeeds, the selected plan is strongly efficient under the same
technology: no feasible plan can use no more of every eligible input and provide no
less of every desirable output while improving at least one. The selection rule
prevents a change of measurement unit from deciding which benchmark is chosen, while
the reported targets remain in their original units. The worked calculation requests
this completion because it reports a strong target. A distance-only study may omit the
extra search when that stronger claim is neither needed nor made.

The evidence supporting the two stages should also remain visible. The selected
reference activities must reproduce the resource savings and service additions
represented by $\beta_o$ under the stated scale assumption. If that account cannot be
reproduced, the study has no supported directional-performance result. If only the
optional completion lacks sufficient support, the study may still report how many
programme units are attainable, but it should not report a strong target or detailed
peer plan.

Completion does not settle implementation. Multiple strong targets may exist, and the
selected one is not necessarily the nearest plan, the least costly transition, or the
organization's preferred design. Neither directional nor Pareto--Koopmans efficiency
shows that a gap was caused by management or that closing it would increase profit or
social value. Prices, adjustment costs, institutional constraints, and causal evidence
must enter a subsequent decision appraisal.

This logic applies here to ordinary adjustable inputs and desirable outputs under the
declared convex free-disposal technology. Weakly disposable quantities, fixed or
non-discretionary variables, and non-convex reference technologies require their own
dominance and target-selection rules. A similar-looking target table does not make
those economic assumptions interchangeable.

## Negative cross-technology distances

For a contemporaneous, self-inclusive comparison, the evaluated plan belongs to the
technology by construction. Doing none of the programme, $\beta=0$, is feasible, so
the estimated distance cannot be negative. Positive $\beta_o$ means that some of the
declared programme remains attainable; zero means that the plan is on the relevant
programme boundary.

Cross-technology appraisal asks a different economic question. Productivity analysis,
for example, may evaluate a current operating plan against an earlier reference
technology, denoted here by $\mathcal T^R$. The plan need not belong to
$\mathcal T^R$. If it performs beyond what that reference technology can reproduce,
feasibility may require a *reversal* of part of the declared programme. Algebraically,
$\beta_o<0$ replaces $(x_o,y_o)$ by

$$
(x_o+|\beta_o|g^x,\;y_o-|\beta_o|g^y).
$$

Suppose one common programme unit saves ten staff hours and adds five treatments. A
cross-technology value of $-0.2$ says that the reference opportunities could reproduce
the assessed plan only after allowing two more staff hours and one fewer treatment.
It does not say that the organization has “negative inefficiency.” Nor, by itself,
does it prove better management: the difference may reflect changed technology,
service mix, environment, measurement, or the composition of the eligible reference
population.

The sign is therefore a reference-feasibility account. Positive means that further
improvement is represented as attainable from the assessed plan; zero places the plan
on the relevant boundary; negative means that the assessed plan lies beyond that
technology in the declared programme's terms. Comparisons retain this meaning only
when the direction, units, variable definitions, and reference populations are held
substantively consistent across technologies.

The standalone DDF defaults to `allow_negative_distance=False`, which is appropriate
for its ordinary contemporaneous use. Internal cross-period Luenberger and
Malmquist--Luenberger calculations enable signed distances where their definitions
require them. Truncating a negative value at zero would erase the reverse adjustment
needed for cross-technology feasibility and generally break the productivity
decomposition. Once signed distance is permitted, zero is a reference boundary rather
than the bottom of a generic better-to-worse ranking.

The same improvement-programme logic carries into the later productivity and
environmental chapters. Luenberger indicators compare the remaining programme across
periods; environmental models add a specified reduction in undesirable outputs
{cite:p}`chung1997`; and dual multipliers can support shadow-price analysis under
additional regularity and normalization. Each application must retain the technology,
direction vector, units, and sign convention as part of the reported result. The
economic meaning lies in the resource and service commitments built into the programme
and in the production evidence used to judge how much of it is attainable.
