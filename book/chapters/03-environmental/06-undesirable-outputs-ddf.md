# Environmental Directional Distance: Producing More with Less Pollution

A power company is rarely asked simply to “be efficient.” It may be asked to supply
more electricity while lowering carbon emissions. A hospital may need to treat more
patients without increasing hazardous waste. A farm may want to maintain food output
while reducing nutrient losses. In each case, managers face a joint operating
programme: improve the service the organization exists to provide and reduce the
residual society would prefer to avoid.

An ordinary output-oriented DEA model cannot express that programme. If emissions are
entered as an ordinary output, producing more of them looks favourable. If they are
entered as an input, they are treated as a resource committed before production, much
like labour or capital. Environmental DEA instead recognizes undesirable outputs as
consequences produced jointly with useful activity. It asks how far service expansion
and burden reduction can proceed together, given what the study assumes about
abatement, foregone output, and the operating practices observed in the comparison
population.

## Pollution is part of the production account

Let $x\in\mathbb{R}^m_+$ denote inputs, $y\in\mathbb{R}^s_+$ desirable outputs, and
$b\in\mathbb{R}^q_+$ undesirable outputs. The environmental technology is

$$
\mathcal T
=\{(x,y,b):x\text{ can jointly produce }(y,b)\}.
$$

For a fixed resource commitment, the feasible output set is

$$
P(x)=\{(y,b):(x,y,b)\in\mathcal T\}.
$$

The word *jointly* carries the economics. Electricity and emissions are not two
unrelated products placed in the same table. They arise from an operating process,
and reducing emissions may require cleaner fuel, abatement activity, lost output, or a
different production plan. The technology must say which of these possibilities the
benchmark comparison is allowed to represent.

### Weak and strong disposal answer different economic questions

The first management question is whether pollution can be reduced
independently while useful output and the represented resource commitment are
preserved, or whether lowering pollution requires curtailing the joint
production activity unless a cleaner process is represented. Weak
disposability adopts the latter view. If $(y,b)\in P(x)$, then

$$
(\alpha y,\alpha b)\in P(x)
\qquad\text{for}\qquad 0\leq\alpha\leq1.
$$

Undesirable output cannot simply be deleted while everything else is held unchanged.
Reducing it is represented as requiring some sacrifice or adjustment in the joint
production plan. This is a natural baseline when pollution control uses resources or
constrains desirable output. Chung, Färe, and Grosskopf combined this production
assumption with a directional distance function to study environmental productivity
{cite:p}`chung1997`.

Here *costly* describes a restriction on the production opportunities represented by
the model. It does not measure a monetary abatement cost, an engineering treatment
cost, or the causal effect of environmental regulation.

Strong disposability instead allows a plan with no more pollution than the observed
plan to be used as a comparator without recording an accompanying sacrifice. In a
classic CRS common-factor joint-envelopment account such as the one used below, the
distinction appears in the bad-output restriction:

$$
B\lambda=b
\quad\text{under common-factor weak disposal},
\qquad
B\lambda\leq b
\quad\text{under its strong-disposal counterpart}.
$$

Strong disposal may be defensible when pollution-control resources and treatment
activities are already measured, or useful as a sensitivity benchmark. It does not
show that removal is costless in money or engineering terms. It says that the model
requires no loss of useful output when the residual falls. If abatement consumes
unmeasured resources, this assumption can overstate the environmental improvement
available to managers and regulators.

```{figure} ../../_static/figures/environmental-disposability.svg
:name: fig-environmental-disposability
:alt: Weak disposability contracts desirable and undesirable outputs together, whereas the strong-disposal account records no accompanying sacrifice when undesirable output falls while desirable output is fixed
:width: 94%

The disposal assumption changes the managerial opportunity set. Weak disposal treats
pollution reduction as costly within the production account; the strong-disposal
account does not represent an accompanying loss of desirable output.
```

Null jointness is a separate assumption:

$$
b=0\quad\Longrightarrow\quad y=0.
$$

It says that the modeled desirable output cannot be produced without generating some
of the residual. That may be reasonable for an unavoidable by-product of combustion,
but not for a sample containing verified zero-emission production, complete capture,
or recycling. Weak disposability and null jointness should therefore be defended from
the production process, not adopted merely because the variable is called pollution.
In the technology used here, null jointness belongs to the weak-disposal account; it
cannot be combined coherently with strong disposal, which permits the residual to be
reduced independently in the represented opportunity set.

### Weak disposal still leaves a benchmarking choice

The weak-disposal axiom does not by itself determine how observed organizations may be
combined. In the classic constant-returns construction, one common activity account
represents the benchmark:

$$
X\lambda\leq x,\qquad
Y\lambda\geq y,\qquad
B\lambda=b,\qquad
\lambda\geq0.
$$

Because activity can be scaled under constant returns, the represented desirable and
undesirable outputs can be curtailed together. Economically, the benchmark applies a
common proportional adjustment to the whole reference production portfolio. That
common-factor interpretation relies on CRS: simply adding a VRS convexity restriction
to $B\lambda=b$ does not create an identified VRS weak-disposal technology.

Under VRS, a source-qualified alternative lets the reference activities carry
different retention rates {cite:p}`kuosmanen2005`. DEAPack represents each activity by
an active part $\mu_j$, which contributes desirable and undesirable outputs, and a
curtailed part $\eta_j$, which still belongs to the input portfolio. Convexity applies
to the full activity account,

$$
\mathbf 1^\top(\mu+\eta)=1,
$$

while the activity-specific retention rate is
$r_j=\mu_j/(\mu_j+\eta_j)$ whenever that activity has positive weight. This is a
different economic construction, not a cosmetic returns-to-scale switch. An equality
such as $B\lambda=b$ without a coherent scaling or convexification account is retained
only as a legacy numerical formulation; it is not presented as a named weak-disposal
technology.

```{figure} ../../_static/figures/weak-disposal-technologies.svg
:name: fig-weak-disposal-technologies
:alt: An equality alone does not identify weak disposal, whereas the CRS common-factor construction uses one portfolio-wide retention rate and the VRS activity-specific construction permits different retention rates across reference activities
:width: 72%

The weak-disposal axiom admits more than one benchmarking construction. The model must
state how the reference activities are scaled before its environmental comparison has
a defensible production meaning.
```

## The directional distance is a feasible management programme

Environmental performance is not adequately summarized by “less pollution.” The
organization usually has obligations on several margins at once. Let $g^x$, $g^y$,
and $g^b$ be nonnegative quantities describing a proposed reduction in inputs, an
increase in desirable outputs, and a reduction in undesirable outputs. Collect them as
the declared environmental programme $g=(g^x,g^y,g^b)$. The environmental directional
distance is

$$
D_{\mathcal T}
(x_o,y_o,b_o;g)
=\sup\left\{
\beta:
(x_o-\beta g^x,
 y_o+\beta g^y,
 b_o-\beta g^b)
\in\mathcal T
\right\}.
$$

The resulting value $\beta_o=D_{\mathcal T}(x_o,y_o,b_o;g)$ is the largest common
ambition factor that the estimated technology can support. Its operational content is
$\beta_o g$: the associated resource savings, service expansion, and pollution
reduction in the units managers actually observe.

Different choices of $g$ pose different policy questions:

```{list-table}
:header-rows: 1
:widths: 25 15 60

* - Programme
  - Direction
  - Question posed
* - Joint environmental improvement
  - $(0,y_o,b_o)$
  - By what common proportion can desirable output rise and pollution fall
    with the resource budget fixed?
* - Service-expansion programme
  - $(0,y_o,0)$
  - How much desirable output can be added without requiring a pollution
    reduction?
* - Pollution-control improvement
  - $(0,0,b_o)$
  - How much pollution can be reduced while resources and desirable output are
    maintained?
* - Resource–service–residual programme
  - $(x_o,y_o,b_o)$
  - How ambitious can a coordinated conservation, expansion, and abatement
    plan be?
```

These are not alternative labels for the same score. They encode different management
commitments. A direction becomes a target only when it corresponds to an institution's
actual objectives and constraints. At least one direction component must be strictly
positive for every assessed organization; an all-zero direction poses no improvement
question and is therefore undefined.

For the common-factor constant-returns technology, the joint-improvement question is
estimated from

$$
\begin{aligned}
\max_{\beta,\lambda}\quad &\beta\\
\text{s.t.}\quad
&X\lambda\leq x_o-\beta g^x,\\
&Y\lambda\geq y_o+\beta g^y,\\
&B\lambda=b_o-\beta g^b,\\
&\lambda\geq0.
\end{aligned}
$$

A positive $\beta$ identifies an attainable directional plan relative to the chosen
reference evidence. A larger value means that more of the declared improvement remains
available; it is not “higher efficiency.” A zero value means that this particular
programme cannot be expanded further. It establishes direction-specific efficiency,
not necessarily Pareto–Koopmans efficiency, because another mix of resource, service,
or residual changes may still be feasible.

When each organization belongs to its own reference set, the unchanged observed plan
is feasible and $\beta\geq0$. External reference sets require more care. A signed
negative distance can be retained when the analyst explicitly requests it; otherwise
the nonnegative programme is reported as infeasible. For the equality-based
common-factor technology, even a positive directional target does not by itself prove
that the original assessed plan belongs to the external reference technology. DEAPack
therefore reports the native $\beta$ whenever its programme is certified, but releases
the display transform $1/(1+\beta)$, efficiency classifications, and improvement plot
only after reference-technology membership is also certified.

The first-stage directional plan is
$({\tilde x}_o,{\tilde y}_o,{\tilde b}_o)=
(x_o-\beta g^x,y_o+\beta g^y,b_o-\beta g^b)$. A second stage may complete that plan by
removing input slack or adding desirable-output slack. Under strong disposal it may
also remove residual slack; under common-factor equality disposal the bad-output
account remains fixed at ${\tilde b}_o$. We reserve hats for the completed target
$({\hat x}_o,{\hat y}_o,{\hat b}_o)$.

A regulator, hospital system, or utility may also have a legitimate reason to
limit who counts as a comparable operating peer: a common service mandate,
permit regime, or accounting boundary, for example. In the generic DDF,
common-factor weak-disposal DDF, and CFG preset, DEAPack lets the study declare
that comparison population explicitly. The declared rule is then intersected
with the chosen time/reference policy before the directional programme is
solved. This is a statement about admissible management evidence, not a new
pollution technology. It never turns strong disposal into weak disposal, and
it does not make a negative external CFG distance disappear. The reported
reference sizes and policy ledger should accompany the distance wherever such a
restriction is used.

## When one production relation hides the pollution mechanism

Weak and strong disposal describe what may happen inside one joint technology. Some
applications need to distinguish the activity that creates desirable output from the
physical relation that generates a residual. A coal-fired plant, for example, draws on
labour, capital, and fuel to produce electricity, but the carbon content of its fuel
has a special connection to emissions. Treating every input as equally responsible
for that residual can obscure the environmental mechanism.

The by-production approach represents the two relationships simultaneously
{cite:p}`murty2012`. Partition inputs as $x=(x^n,x^p)$, where $x^p$ contains those
inputs that physically generate the modeled residual. A common empirical account is

$$
\mathcal T_{BP}=\mathcal T_1\cap\mathcal T_2,
$$

with intended production represented by

$$
\mathcal T_1:\qquad
X\lambda\le x,\qquad Y\lambda\ge y,
$$

and residual generation represented by

$$
\mathcal T_2:\qquad
X^p\mu\ge x^p,\qquad B\mu\le b.
$$

Here $\lambda,\mu\ge0$. As written, these are the constant-returns relations
used in the classical source account. The inequality $B\mu\le b$ should not be
read in isolation as ordinary free disposal. Together with
$X^p\mu\ge x^p$, it says that reducing the represented residual cannot be
separated from the inputs that generate it. This is *costly disposal inside the
residual-generation relation*: an opportunity-set restriction, not a monetary cost,
an observed treatment process, or an engineering abatement technology.

The two reference combinations are deliberately distinct. An electricity producer
may learn about production capacity from one set of plants and about the emissions
associated with fuel use from another. The observed plan must nevertheless pass both
relations.

```{figure} ../../_static/figures/by-production-intersection.svg
:name: fig-environmental-by-production-intersection
:alt: By-production intersects an intended-production relation with a residual-generation relation using separate reference combinations
:width: 95%

By-production separates the intended-production account from the
residual-generation account while requiring the organization to satisfy both.
```

The conventional BP-DDF implemented here holds ordinary inputs fixed and declares
$g^{BP}=(0,g^y,g^b)$. On the same directional scale, its two accounts ask for

$$
\begin{aligned}
\beta_o^1&=\sup\{\beta:X\lambda\le x_o,\ 
Y\lambda\ge y_o+\beta g^y\},\\
\beta_o^2&=\sup\{\beta:X^p\mu\ge x_o^p,\ 
B\mu\le b_o-\beta g^b\}.
\end{aligned}
$$

The classical source profile holds the nonnegative output and residual directions
fixed across the compared organizations. Thus $\beta_o^1$ and $\beta_o^2$ are
commensurable ambitions, not distances computed under two unrelated management
programmes. A common programme constrained by both accounts has

$$
\beta_o^{BP}=\min\{\beta_o^1,\beta_o^2\}.
$$

Both direction blocks must pose a substantive question: at least one desirable-output
direction component must be positive and at least one residual direction component
must be positive. The minimum also creates an important interpretive limit. If
$\beta_o^{BP}=0$, only one component account needs to be at its directional limit; the
other may still contain substantial improvement potential. Zero therefore does not
establish componentwise efficiency, and still less strong efficiency of the whole
operation.

The smaller component is the *direction-specific limiting account*. Reporting both
components shows whether the intended-production relation or the residual-generation
relation limits this declared common programme. It does not, by itself, identify a
physical bottleneck, a causal management constraint, or an emissions-control process.
That interpretation depends on identifying $x^p$ from scientific or engineering
knowledge; a statistical column name cannot establish which inputs physically
generate a residual.

Because the conclusion depends on the intersection of two production relations, both
accounts must reproduce their quantity commitments before the common distance, target,
or peer comparison has an economic interpretation. If either account cannot be
reconstructed, the evidence is insufficient to support the joint environmental
conclusion. Satisfying both accounts still does not turn the directional target into a
strongly efficient engineering design. By-production remains a useful alternative
production account within environmental directional analysis, not a universally
preferable pollution score, a chemical mass-balance model, or a detailed account of
capture, treatment, and recycling.

### Reading the two accounts in practice

The five-organization teaching example from Murty, Russell, and Levkoff makes the
minimum rule visible without adding another model family {cite:p}`murty2012`:

```python
from deapack import ByProductionDDF, DEAData, dataset_info, load_dataset

frame = load_dataset("by_production_component_bottleneck")
roles = dataset_info("by_production_component_bottleneck").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    polluting_inputs=roles["polluting_inputs"],
    outputs=roles["outputs"],
    bad_outputs=roles["bad_outputs"],
)

bp_result = ByProductionDDF().fit(data)
bp_result.summary().loc[
    lambda table: table["dmu_id"].eq("DMU 3"),
    ["intended_distance", "environmental_distance", "distance",
     "limiting_subtechnology"],
]
bp_result.targets_for("DMU 3")
```

For DMU 3, the intended-production account supports
$\beta^1=4/3$, while the residual-generation account supports $\beta^2=1$.
The joint programme is therefore limited by the residual-generation relation and
$\beta^{BP}=1$. Starting from
$(x^p,y,b)=(1,2/3,2)$, the common directional target is
$(1,5/3,1)$. The intended account alone could support $y=2$, but that endpoint is not
the joint operating plan. The peer tables make the separation equally concrete: DMU 1
supports the intended-production account, whereas DMU 2 supports the residual account.
This is exactly why the two component distances and two peer systems should accompany
the minimum rather than disappear behind one headline number.

## From environmental performance to productivity change

Evaluating an operation against another period's technology can produce a signed
cross-technology distance, but one such comparison is not itself a productivity
index. Part IV develops the required combinations of contemporaneous and
cross-period environmental distances in
{doc}`../04-productivity/environmental-productivity-ml-common-reference`.

## A contemporaneous power-plant comparison

The `environmental_panel` teaching data contain energy, labour, electricity, and
carbon dioxide for several plants over four periods. Suppose the immediate management
question is: with each plant's current energy and labour commitment, how much can
electricity rise while carbon dioxide falls in the same proportion? A contemporaneous
reference means that each plant is compared with operating practices observed in its
own year.

```python
from deapack import CommonFactorWeakDisposalDDF, DEAData, load_dataset

frame = load_dataset("environmental_panel")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    period="period",
    inputs=["energy", "labor"],
    outputs="electricity",
    bad_outputs="co2",
)

result = CommonFactorWeakDisposalDDF(
    input_direction="zeros",
    output_direction="observed",
    bad_output_direction="observed",
    reference="contemporaneous",
).fit(data)
```

The fitted account can display the supported variable-level plan directly:

```python
result.plot(kind="improvement", dmu_id="Central", period=2020)

central = result.summary().query("dmu_id == 'Central' and period == 2020")
central_plan = result.targets_for("Central", period=2020)
central_slacks = result.slacks.query(
    "dmu_id == 'Central' and period == 2020"
)
```

Writing the directions explicitly keeps the economic promise visible: ordinary
inputs are protected, desirable electricity expands in proportion to its
observed level, and undesirable carbon dioxide contracts in proportion to its
observed level. The technology is the family-level CRS common-factor weak-
disposal account introduced above; a historical source label is not needed to
define another model.

For Central in 2020, $\beta=0.083815$. Conditional on the observed comparison group
and the common-factor constant-returns technology, its resource commitment supports a
coordinated plan with approximately 8.38 percent more electricity and 8.38 percent
less carbon dioxide.

| Role | Quantity | Observed | Benchmark plan | Change |
|---|---|---:|---:|---:|
| Input | Energy | 110.000 | 110.000 | 0.000 |
| Input | Labour | 55.000 | 55.000 | 0.000 |
| Desirable output | Electricity | 79.376 | 86.028902 | +6.652902 |
| Undesirable output | Carbon dioxide | 285.120 | 261.222659 | -23.897341 |

```{figure} ../../_static/figures/environmental-ddf-improvement-result.svg
:name: fig-environmental-ddf-improvement-result
:alt: Central's conditional 2020 environmental improvement account keeps energy and labour fixed, expands electricity by 6.652902, and reduces carbon dioxide by 23.897341 under a common directional programme with no additional slack
:width: 96%

Central's conditional plan under weak common-factor disposal, CRS, and a
contemporaneous reference. The declared direction contributes the
electricity gain of 6.652902 and carbon-dioxide reduction of 23.897341 while
energy and labour remain fixed; the subsequent completion contributes no
additional slack in this case. Each quantity retains its own original unit, so
the rows do not share a quantity axis. This is one selected feasible benchmark,
not a unique operating plan, engineering implementation, causal effect, or cost
conclusion.
```

The distinction between the common directional commitment and additional slack
matters. Here the completion step finds zero extra slack, so the whole displayed
change comes from the programme Central asked the benchmark to support. Other
organizations or directions may require a second, variable-specific adjustment.
Input and desirable-output slacks are available under both disposal accounts;
additional bad-output slack belongs only to strong disposal. Under common-factor
equality disposal, the residual target is fixed by the declared directional move.

The benchmark is a conditional performance comparison. It does not establish that
Central can adopt the plan without investment, identify a particular abatement
technology, estimate compliance cost, or predict a causal response. Those claims
would require engineering and economic information beyond the observed production
quantities.

Here the contemporaneous reference answers a static annual benchmarking question.
Part IV treats alternative time-information policies as components of environmental
productivity analysis rather than as additional environmental DDF model families.

## Sensitivity should follow the production story

A useful sensitivity analysis varies economically defensible assumptions and asks why
conclusions change:

- Does free scaling create benchmark plans that are implausible for the organization?
- Does strong disposal obtain its improvement because the production account records
  no accompanying sacrifice for pollution reduction?
- Does the identity of the limiting production relation change under by-production?
- Do the organizations identified as priorities for intervention remain the same?

The main specification should reflect the production and regulatory setting. The
alternatives show how much the conclusion depends on contestable assumptions. Merely
reporting a correlation between score columns hides the mechanism that produced the
difference.

Environmental directional distance is thus best read as a disciplined statement
about feasible joint improvement: *given these observed practices, this production
account, this reference policy, and this management programme, how far can the
organization proceed?* It remains distinct from undesirable-output SBM, which uses a
non-radial slack account, and from productivity indexes, which combine multiple
distance evaluations through time.
