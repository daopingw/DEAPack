# Classical Radial DEA: Resource Stewardship and Service Expansion

A service authority enters its annual planning round with two legitimate but
different responsibilities. The finance team must protect agreed service levels
while testing whether branches need all of their present resources. The operations
team must respect the approved resource envelope while asking whether citizens
could receive more service. A single number cannot answer both questions unless
the report first says which commitment is being held fixed.

Classical radial DEA turns those responsibilities into two transparent performance
questions. One asks what common share of each controllable resource would have been
enough to preserve current services. The other asks how far all desirable services
could rise within the current resource envelope. These questions give boards a
readable first indication of resource stewardship or service capacity without
pretending to diagnose every individual shortfall. Their simplicity is useful only
when a common percentage is plausible for the organization being studied.

The study-design and production-technology chapters have already established the
production story, variable roles, eligible peers, and permissible scale comparisons;
see
{doc}`../01-foundations/02-study-design` and
{doc}`../01-foundations/02-production-frontier`. The present question is how large an
operating shortfall those opportunities reveal. What matters is not the shape of a
diagram but the responsibility assigned to management and the commitment that the
benchmark must protect.

## Orientation begins with what management must protect

Orientation identifies the side of the operation that is treated as a commitment.

- Input orientation protects the represented output commitments and asks how
  much of every controllable input could be saved.
- Output orientation holds the represented input limits fixed and asks how
  much every desirable output could expand.

Returns to scale records which resizing comparisons the benchmark may use.

- Constant returns to scale (CRS) admits proportional replication of observed
  operating patterns. The performance comparison therefore includes whether
  the organization is operating at a productive scale.
- Variable returns to scale (VRS) forms convex combinations without granting
  unrestricted proportional replication. It asks how well resources are used
  under the maintained locally scaled opportunity set.

Crossing these two decisions gives four familiar specifications, all belonging to the
same Farrell radial family {cite:p}`farrell1957,charnes1978,banker1984`:

| Protected commitment and allowed change | Benchmark right | Familiar shorthand | Complete DEAPack preset | Native result |
|---|---|---|---|---|
| Protect outputs; reduce all inputs proportionally | CRS | CCR-I | `CCRInput` | input contraction $\theta$ |
| Hold inputs; expand all outputs proportionally | CRS | CCR-O | `CCROutput` | output expansion $\phi$ |
| Protect outputs; reduce all inputs proportionally | VRS | BCC-I | `BCCInput` | input contraction $\theta$ |
| Hold inputs; expand all outputs proportionally | VRS | BCC-O | `BCCOutput` | output expansion $\phi$ |

CCR and BCC are historically important names, but neither acronym settles the
orientation. CCR identifies the CRS specialization of the parent family; BCC
identifies its VRS specialization. The suffixes I and O complete the contract by
stating which side of the production account management is allowed to change.
Names such as *CCR model*, *BCC model*, *Farrell input measure*, and *radial
envelopment model* therefore describe closely related views or specializations,
not a catalogue of unrelated algorithms.

This unification does not make the choices interchangeable. BCC-I and BCC-O
protect different commitments. CCR-I and BCC-I grant the benchmark different
resizing rights. A defensible study selects both choices before looking at the
ranking and reports them as part of the result's meaning.

## Translate the management question into a benchmark programme

For organization $o$, the input-oriented CRS programme is

$$
\begin{aligned}
\min_{\theta,\lambda}\quad &\theta\\
\text{subject to}\quad
&X\lambda\leq\theta x_o,\\
&Y\lambda\geq y_o,\\
&\lambda\geq0.
\end{aligned}
$$

The reference activity must protect the organization's service commitments
while using no more than the common proportion $\theta$ of every represented
input. Minimizing $\theta$ finds the smallest supported resource-retention
factor. When the observed operation belongs to the reference technology,
$\theta\leq1$ and $1-\theta$ is the supported common proportional saving.
Adding $\mathbf 1^\top\lambda=1$ changes the benchmark from CRS to VRS without
changing the resource-stewardship question.

The output-oriented counterpart is

$$
\begin{aligned}
\max_{\phi,\lambda}\quad &\phi\\
\text{subject to}\quad
&X\lambda\leq x_o,\\
&Y\lambda\geq\phi y_o,\\
&\lambda\geq0,
\end{aligned}
$$

again with $\mathbf 1^\top\lambda=1$ for VRS. Here the resource limits are
protected and $\phi$ is the largest common service-expansion factor; $\phi-1$
is the supported proportional increase when the observed operation belongs to
the reference technology. The two programmes use the same production account
but hold different quantities fixed. In the ordinary self-inclusive appraisal,
their native values therefore run in opposite numerical directions:
$\theta\leq1$ is better when closer to one, whereas $\phi\geq1$ is better when
closer to one. DEAPack's standardized output efficiency $1/\phi$ is a reporting
transform, not a second performance model.

An external or leave-group-out reference may not contain the evaluated
operation. Then $\theta$ can exceed one or $\phi$ can fall below one: reaching
the external benchmark requires a reverse adjustment rather than revealing an
ordinary saving or expansion from the observed plan. Such values should remain
visible as benchmark-relative comparisons, but they do not inherit the usual
$[0,1]$ efficiency interpretation or a self-inclusive efficiency classification.

The CRS input programme has an equivalent multiplier account:

$$
\begin{aligned}
\max_{u,v}\quad &u^\top y_o\\
\text{subject to}\quad
&v^\top x_o=1,\\
&u^\top Y-v^\top X\leq0,\\
&u,v\geq0.
\end{aligned}
$$

The normalization fixes the unit of account. Organization $o$ receives the
most favorable nonnegative input and output valuations that remain admissible
for every organization in the comparison population. Linear-programming
duality makes this optimum equal to the envelopment score. These multipliers
are endogenous shadow valuations under the model, not observed prices or
estimates of social value. Under VRS, a free intercept accompanies the
convexity constraint and permits local increasing, constant, or decreasing
returns.

The programme is now formally complete, but two institutional questions still
decide whether its benchmark is credible. First, may a favorable valuation give
almost no recognition to a mandated service? Second, may several observed
practices be combined into one attainable operating plan? Both questions qualify
the evidence admitted to the same radial account.

## Ask whether the favorable valuation respects public commitments

Allowing each organization to choose its own multipliers is deliberate. It
lets a hospital, school, or branch be assessed under the most favorable
relative valuation that the observed production evidence will support,
without pretending that reliable market prices exist. The resulting score
therefore answers a conditional question: *can this organization be shown to
perform well under any admissible valuation of the represented resources and
services?* {cite:p}`ray2004`.

That freedom can also expose a weak performance story. A multiplier may be
zero or extremely small because the corresponding variable does not help the
organization's most favorable account. This does not establish that a service
is worthless or that a resource is costless. For example, a hospital might
look strong only when emergency-care quality receives almost no recognition.
The numerical result is then valid for the unrestricted DEA question, but it
may be too narrow for an authority that has an explicit duty to protect both
access and quality.

When credible institutional knowledge exists, the comparison can admit only
valuations consistent with it. Management might require every mandated
service to receive material recognition, bound the relative importance of two
outcomes, or state a feasible production trade-off such as how much additional
staff is normally required to protect an extra unit of service. Such
restrictions should express prior policy, engineering, or professional
knowledge—not be selected after inspecting which bounds produce a preferred
ranking. They can change scores, peers, and targets because they change the
valuation or production statements under which performance is judged
{cite:p}`allen1997,dyson2001,cooper2011handbook`.

Assurance-region and cone-ratio formulations are established ways to encode
these admissible weights or trade-offs. They are governance qualifications to
the parent radial account, not new efficiency families. A defensible report
still names its orientation and scale assumption, states the added value
judgement in substantive units, and shows how the conclusion differs from the
unrestricted appraisal.

DEAPack's package Documentation gives one source-qualified implementation of
that idea: the [finite input-oriented CRS polyhedral cone-ratio
leaf](https://deapack.readthedocs.io/en/latest/models/polyhedral-cone-ratio.html).
It requires declared generator provenance and keeps transformed cone residuals
separate from ordinary input excesses, output shortfalls, and managerial
targets. That technical leaf supports an audit of a valuation policy; it does
not turn every historical weight restriction into another option of the
classical radial model developed here.

## Ask whether complete practices or mixtures can teach

The same radial performance question can rest on a different learning right.
Convex VRS treats mixtures of observed organizations as attainable when capacity
is divisible, service designs can be combined, or portfolios can be rebalanced.
The free-disposal hull (FDH) withholds that averaging right and lets one complete
observed practice support a benchmark at a time {cite:p}`deprins1984`. This may be
more credible when a municipality must adopt a whole waste-treatment design or a
hospital must compare indivisible care pathways.

Nothing about this choice changes what input or output orientation protects. It
changes the evidence allowed to support the operating comparison. Under FDH the
focal organization must be dominated by a complete observed practice; under convex
VRS it may also be dominated by a supported mixture. That is why FDH belongs in
the same classical radial discussion without being relabelled as another BCC
option.

```{figure} ../../_static/figures/fdh-vs-convex.svg
:name: fig-classical-radial-fdh-vs-convex
:alt: FDH follows observed-practice steps while convex VRS joins observations and can support a more demanding synthetic target
:width: 95%

The same evidence under two learning assumptions. FDH asks whether a complete
observed practice dominates the focal operation. Convex VRS also admits
intermediate mixtures and can therefore set a more demanding benchmark.
```

The distinction is easy to reproduce on the one-input, one-output teaching
data:

```python
from deapack import BCC, DEAData, FDH, load_dataset

frame = load_dataset("frontier_1x1")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    inputs="input",
    outputs="output",
)

fdh = FDH(orientation="output").fit(data)
vrs = BCC(orientation="output").fit(data)

comparison = {
    "FDH": fdh.summary().set_index("dmu_id").loc["H", "efficiency"],
    "convex VRS": vrs.summary().set_index("dmu_id").loc["H", "efficiency"],
}
```

For branch H, output efficiency is about 0.909 under FDH and 0.845 under
convex VRS. H is compared with a less demanding observed-practice step under
FDH; VRS additionally treats a mixture of observed practices as attainable.
The difference is not evidence that one calculation is wrong. It measures how
much of H's assessed shortfall depends on the claim that practices can be
combined.

FDH is thus a principal alternative benchmark technology inside the classical
radial family, not a new orientation and not “BCC with an option switched
off.” It has no ordinary CRS/VRS toggle: removing convexification is the point
of the comparison. If several observations tie, they are alternative observed
comparators rather than weights in one synthetic peer. A credible study should
say why complete observed practices or convex mixtures provide the more
defensible evidence and use the other construction as a sensitivity check
when both are plausible.

## Read the movement as an operating comparison

Consider eight branches using one standardized measure of staff capacity to
deliver one standardized service. Under an input-oriented VRS comparison,
branches inside the best-practice boundary are connected to operating plans
that protect their recorded service while using less staff capacity.

A complete radial fit carries two claims even when a two-dimensional picture
makes them look like one movement. Phase one reports the common proportional
commitment: use at most $\theta x_o$ under input orientation, or supply at
least $\phi y_o$ under output orientation. Phase two holds that fitted factor
fixed and asks whether any individual resource can still be saved or any
individual service can still be added. Thus `score` and
`is_radially_efficient` describe the proportional claim; `slacks`, `targets`,
and `is_efficient` describe the selected completed plan. Completion may change
the reported target, but it never revises $\theta$ or $\phi$.

The result is easiest to govern as a layered operating account:

| Evidence | What it can support | What it cannot establish by itself |
|---|---|---|
| Native $\theta$ or $\phi$ | the minimized retained-input share or maximized output multiple under the declared orientation | variable-specific gaps, a causal explanation, or an implementation order |
| Phase-one radial plan | the quantities implied by that common movement | a Pareto--Koopmans complete plan when slacks remain |
| Slacks and completed target | additional represented input savings or service gains after the radial optimum is held fixed | the unique, cheapest, or politically feasible transition plan |
| Peer intensities | the observed activities that support the selected comparison | proof that peer management caused the result or should be copied literally |

This hierarchy prevents a concise score from being asked to carry evidence that
only the completion and peer accounts contain.

The public peer rows belong to the selected slack-completed target when that
completion is requested. The phase-one score establishes that at least one
radial comparison supports $\theta$ or $\phi$; it does not make the peers of a
later selected target the unique intensity solution to the phase-one programme.

```{figure} ../../_static/figures/radial-frontier-result.svg
:name: fig-classical-radial-operating-targets
:alt: Eight service branches are compared under a variable-returns technology, with input-oriented plans for interior branches preserving recorded service while requiring less staff capacity
:width: 94%

An input-oriented BCC comparison. Each interior branch is compared with a
feasible operating plan that preserves its recorded service while requiring
less staff capacity. The plan is a benchmark opportunity, not a causal
diagnosis or an implementation order. In this scalar case no additional
variable-specific improvement remains after the proportional resource saving,
so the proportional and completed plans happen to coincide.
```

For branch E, input orientation asks what resource commitment is sufficient
for its recorded service. Output orientation instead keeps E's resource
budget and asks what service level that budget could support. Changing the
orientation changes what is protected and what is allowed to move; it is not
a robustness switch to be chosen after inspecting the scores.

Changing CRS to VRS asks a different question. CRS treats a productive
operating pattern as proportionally replicable at other scales. VRS does not
grant that right. A lower CRS than VRS efficiency can therefore reflect the
additional scale comparison admitted by CRS. It does not by itself reveal
whether an organization should expand or contract. The dedicated
{doc}`scale-performance-management` chapter separates scale efficiency, local
returns to scale, and radial elasticity. The first compares matched CRS and VRS
performance accounts; the latter two describe the response near a selected
efficient plan. Those quantities should not be collapsed into one interpretation.

## Fit the four complete contracts

The deterministic `frontier_1x1` data make the two decisions visible without
hiding them inside a large application:

```python
import pandas as pd

from deapack import (
    BCCInput,
    BCCOutput,
    CCRInput,
    CCROutput,
    DEAData,
    load_dataset,
)

frame = load_dataset("frontier_1x1")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    inputs="input",
    outputs="output",
)

models = {
    "CCR-I": CCRInput(),
    "CCR-O": CCROutput(),
    "BCC-I": BCCInput(),
    "BCC-O": BCCOutput(),
}
fitted = {name: model.fit(data) for name, model in models.items()}

comparison = pd.concat(
    [
        result.summary()
        .query("dmu_id == 'E'")
        .assign(recipe=name)
        for name, result in fitted.items()
    ],
    ignore_index=True,
)[
    [
        "recipe",
        "score",
        "efficiency",
        "is_radially_efficient",
        "is_efficient",
    ]
]
comparison
```

| Contract | Native score | Standardized efficiency | Radially efficient? | Strongly efficient? |
|---|---:|---:|---|---|
| CCR-I | 0.6000 | 0.6000 | no | no |
| CCR-O | 1.6667 | 0.6000 | no | no |
| BCC-I | 0.6667 | 0.6667 | no | no |
| BCC-O | 1.6667 | 0.6000 | no | no |

For the two input-oriented contracts, `score` is the retained resource factor
$\theta$. Thus $\theta_E=0.60$ under CCR-I means that the CRS benchmark uses
60 percent of E's represented inputs while protecting its outputs: the
proportional resource-saving opportunity is 40 percent. Input-oriented
`efficiency` reports the same $\theta$.

For the two output-oriented contracts, `score` is the native expansion factor
$\phi$. A value $\phi_E=1.6667$ means that the benchmark supports about 1.667
times E's represented outputs with its inputs held fixed. DEAPack reports the
reciprocal $1/\phi_E=0.60$ in `efficiency`, so the standardized efficiency
field remains higher-is-better in both orientations.

The distinction between `score` and `efficiency` should remain visible in an
audit trail. Comparing the native `score` columns across orientations would
mix a contraction factor with an expansion factor. In this scalar case the
harmonized CRS efficiencies coincide, but the input- and output-oriented
experiments still protect different quantities.

## When a score of one does not close the operating account

A radial score tests one deliberately simple operating rule: change every
represented input, or every represented output, by the same percentage. That
rule can be exhausted because one protected quantity prevents a further
common movement, even though another resource or service still has a
separately attainable improvement.

Three branches make the distinction exact. A uses one resource unit to supply
one service unit. B uses two resource units for the same service. C uses one
resource unit but supplies only one half unit of service. The input-oriented
VRS question for C asks whether its *resource* can fall while its recorded
service is protected. It does not initially ask whether service could rise.

```{figure} ../../_static/figures/radial-improvement-result.svg
:name: fig-classical-radial-improvement
:alt: Branch C uses one resource unit to provide half a service unit. Its input-oriented VRS radial factor is theta equal to one, so the phase-one proportional target remains one resource and one-half service. A separately supported completion holds theta fixed and raises service by one-half to the selected final target of one resource and one service. C is radially efficient but not strongly efficient.
:width: 100%

One observed operation, two supported conclusions. The proportional programme finds
no common resource saving for C; the completion account still finds a service
opportunity of 0.5. The final target is conditional on the fitted technology
and completion rule, not an implementation sequence or management order.
```

For C, $\theta_C=1$ leaves the phase-one plan at resource $1$ and service
$0.5$. The statement is precise but narrow: no common input contraction is
represented as feasible. Branch A nevertheless shows that the same resource
can support service $1$. Holding the radial optimum fixed, phase two therefore
records zero additional resource saving, a service slack of $0.5$, and the
completed target $(1,1)$. C is radially efficient but not strongly efficient.

The operating account for a general input-oriented fit is

$$
x_o^{R}=\theta_o x_o,
\qquad y_o^{R}=y_o,
\qquad
\widehat x_o=x_o^{R}-s_o^-,
\qquad \widehat y_o=y_o^{R}+s_o^+.
$$

The superscript $R$ denotes the phase-one proportional plan; a hat denotes the
selected completed plan. The `targets` table reports the hatted plan, not
an unlabeled copy of $\theta_o x_o,y_o$. The accompanying operating ledger
reconstructs and labels the intermediate radial plan so that a reader cannot
silently attribute the later service gain to the radial percentage.

The exact account is reproducible through the complete BCC-I preset:

```python
import pandas as pd

from deapack import BCCInput, DEAData

frame = pd.DataFrame(
    {
        "branch": ["A", "B", "C"],
        "resource": [1.0, 2.0, 1.0],
        "service": [1.0, 1.0, 0.5],
    }
)
data = DEAData.from_frame(
    frame,
    dmu="branch",
    inputs="resource",
    outputs="service",
)
result = BCCInput().fit(data)
figure = result.plot(kind="improvement", dmu_id="C")
```

Under output orientation the same accounting logic reverses roles: phase one
holds the input caps and scales every represented output by $\phi$; completion
may then expose an additional input saving or output gain without changing
$\phi$.

This is the distinction between radial efficiency and Pareto--Koopmans strong
efficiency {cite:p}`koopmans1951,charnes1985`. A plan is strongly efficient
under the declared technology when no other feasible plan uses no more of
every eligible input and supplies no less of every desirable output, with a
strict improvement in at least one quantity. Thus $\theta=1$ establishes only
that no common input reduction remains; it does not establish that every
individual resource excess and service shortfall is zero. The analogous warning
applies when an output-oriented expansion factor reaches one.

DEAPack's complete radial presets preserve the common-percentage result and,
when the evidence supports it, supply a slack-completed target such as C's
$(1,1)$ plan. The completion does not revise the radial score or create a
different efficiency model; it makes the remaining operating gaps visible. If
the evidence does not support a completed target, only the radial conclusion
has been established. An absent target or slack ledger is not evidence that
every remaining improvement is zero.

## What a slack-completed target does—and does not—mean

A slack-completed target is one strongly efficient operating plan under the
declared technology and completion rule. It is not necessarily the closest
target, the cheapest transition, or the only optimal target. “Strong” refers
to the absence of a further represented input saving or desirable-output gain;
it does not mean that the plan is uniquely best for management.

Peer intensities have the same boundary. They show which observed activities
support the selected benchmark. A positive intensity is evidence used by the
model, not a finding that the peer's management practice caused its
performance or that the evaluated organization should imitate it literally.
Convex combinations are operationally persuasive only when divisible
capacity, time sharing, or portfolio mixing makes those combinations
credible.

The presets do not settle other parts of the study. The analyst must still
declare the variables, eligible reference observations, period policy,
measurement quality, and whether CRS or VRS is economically defensible.
Ordinary radial DEA also does not guess how an undesirable output may be
reduced. A study containing pollution, adverse events, or another jointly
produced burden must move to an explicit environmental production account.

This completion claim is deliberately narrow: ordinary adjustable inputs and
desirable outputs in the declared convex free-disposal technology. Pollution,
fixed commitments, and non-convex benchmark rights require their own
production accounts; the existence of a quantity called a target does not make
their dominance conditions identical.

## Report the question, not only the percentage

A responsible finding keeps the comparison contract attached. CCR and BCC remain
useful shorthand for CRS and VRS, and the I or O suffix states what management
protects. The software constructors preserve those complete historical labels,
but the report should lead with the operating meaning. For example:

> Relative to the eligible branches and the declared convex VRS technology,
> branch E has an input-oriented radial efficiency of 0.667. The fitted
> benchmark preserves E's recorded service while using two-thirds of its
> represented controllable resource. This is a model-supported operating
> opportunity, not a causal estimate or an instruction to remove one-third of
> the branch's budget.

That sentence names the reference population, scale assumption, orientation,
score meaning, and conclusion boundary. Targets, slacks, and peers can then
show why the model supports the comparison.

The FDH section above changes benchmark rights while retaining the radial
performance question. The following {doc}`scale-performance-management`
chapter separates a CRS--VRS scale gap from local operating response. Readers
interested in variable-specific resource excesses and output shortfalls can
continue directly to {doc}`04-sbm`. When desirable production is inseparable from an
undesirable outcome, begin instead with the environmental production question
in {doc}`../03-environmental/06-undesirable-outputs-ddf`.
