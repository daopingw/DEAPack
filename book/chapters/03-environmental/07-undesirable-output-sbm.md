# Slacks-Based Efficiency with Undesirable Outputs

A power plant can use too much fuel, generate too little electricity, and emit too
much carbon dioxide at the same time. A radial environmental model summarizes a
declared joint improvement programme—for example, increase electricity and reduce
emissions by the same percentage. That is useful when management has adopted such a
programme. It is less informative when the operating gaps differ sharply across
resources, desirable outputs, and pollutants.

Undesirable-output SBM separates these sources of underperformance. It allows fuel
excess, missing electricity, and avoidable emissions to differ rather than forcing
them into one common percentage, and normalizes each gap by the organization's
observed quantity. The result answers a direct management question:

> How large are the variable-specific resource, service, and residual gaps in one
> attainable operating plan, when lower inputs and undesirable outputs and higher
> desirable outputs are all preferred?

This model extends the slacks-based logic of ordinary SBM {cite:p}`tone2001` to a
standard separable undesirable-output account {cite:p}`tone2003bad`. It is a core
environmental DEA model, but its apparent simplicity should not hide the production
assumption it makes: undesirable outputs can be reduced independently of desirable
outputs within the represented technology. That assumption is suitable for some
abatement settings and unsuitable for others.

## Three kinds of operating gap, one feasible benchmark

For organization $o$, let

- $x_o\in\mathbb R_{++}^m$ contain inputs;
- $y_o\in\mathbb R_{++}^s$ contain desirable outputs; and
- $b_o\in\mathbb R_{++}^q$ contain undesirable outputs.

The reference observations are stored in $X$, $Y$, and $B$. A benchmark assembled
with nonnegative intensities $\lambda$ satisfies

$$
X\lambda+s^-=x_o,
$$

$$
Y\lambda-s^+=y_o,
$$

and

$$
B\lambda+s^b=b_o,
$$

where $s^-\ge0$ is input excess, $s^+\ge0$ is desirable-output shortfall, and
$s^b\ge0$ is undesirable-output excess.

These balances produce an operating target

$$
\widehat x_o=x_o-s^-,
\qquad
\widehat y_o=y_o+s^+,
\qquad
\widehat b_o=b_o-s^b.
$$

All three target vectors come from the same reference activity $\lambda$. The model
does not independently choose the most attractive input plan, desirable-output plan,
and emissions plan. It searches for one attainable operation that simultaneously uses
no more inputs, supplies no less desirable output, and generates no more undesirable
output than the evaluated organization.

```{figure} ../../_static/figures/undesirable-sbm-components.svg
:name: fig-mainstream-undesirable-sbm-components
:alt: An undesirable-output SBM account shows input excess, desirable-output shortfall, and undesirable-output excess as separate normalized operating gaps leading to one feasible benchmark
:width: 92%

The standard undesirable-output SBM does not force every quantity to change by a
common percentage. Each resource excess, missing desirable output, and avoidable
undesirable output remains visible in its own physical unit. The diagram is schematic:
its three rows do not share a physical scale.
```

The distinction among variable roles matters. Treating pollution as an ordinary
desirable output rewards larger emissions. Treating it as an ordinary input suggests
that pollution is chosen before production and substitutes for labor, fuel, or capital.
The bad-output balance instead says that the evaluated residual can contain an excess
relative to a feasible production plan.

## The non-radial environmental ratio

Define the average normalized input excess as

$$
I_o^x
=\frac{1}{m}\sum_{i=1}^{m}\frac{s_{io}^-}{x_{io}}.
$$

The retained-resource account is $1-I_o^x$. If $I_o^x=0.20$, the selected benchmark
removes an average of 20 percent across the input dimensions. This does not mean that
every input falls by 20 percent; one may remain unchanged while another falls much
more.

Desirable-output shortfalls and undesirable-output excesses enter one output-side
account:

$$
I_o^{yb}
=\frac{1}{s+q}
\left(
\sum_{r=1}^{s}\frac{s_{ro}^+}{y_{ro}}
+
\sum_{h=1}^{q}\frac{s_{ho}^b}{b_{ho}}
\right).
$$

An additional desirable service and a reduction in an undesirable residual both
count as favorable changes. Their normalized gaps enter symmetrically, one term per
declared output dimension. The expansion account is $1+I_o^{yb}$.

It is often clearer in a results table to retain the desirable and undesirable
subaccounts separately:

$$
I_o^y=\frac{1}{s}\sum_{r=1}^{s}\frac{s_{ro}^+}{y_{ro}},
\qquad
I_o^b=\frac{1}{q}\sum_{h=1}^{q}\frac{s_{ho}^b}{b_{ho}}.
$$

The combined account is a dimension-weighted average,

$$
I_o^{yb}=\frac{sI_o^y+qI_o^b}{s+q},
$$

not the unweighted average of the two subaccount means unless $s=q$. DEAPack reports
the three means as `desirable_output_inefficiency`, `bad_output_inefficiency`, and
`output_inefficiency`; `output_account_factor` is the denominator term
$1+I_o^{yb}$.

The standard non-oriented undesirable-output SBM score is

$$
\rho_o^B
=\frac{1-I_o^x}{1+I_o^{yb}}.
$$

Higher is better. With certified membership in the reference technology and the
standard positive data domain,

$$
0<\rho_o^B\le1.
$$

A score of one requires every scored input, desirable-output, and undesirable-output
slack to be zero. It therefore certifies strong efficiency under this particular
separable technology. A score below one combines resource retention and output-side
improvement in a fractional account.

The score is not an emissions-reduction percentage, a cost-benefit ratio, or a measure
of social welfare. For example, $\rho^B=0.60$ does not imply that emissions can fall by
40 percent. The variable-level target and slack tables contain that information. Nor
does the equal-dimension average say that a tonne of carbon dioxide causes the same
damage as a tonne of another pollutant. The model has normalized technical gaps, not
monetized environmental consequences.

## What separability and strong disposability mean

The bad-output equation implies

$$
B\lambda\le b_o.
$$

It permits the comparison plan to generate less undesirable output while maintaining
or expanding desirable outputs. In this sense the standard model treats undesirable
outputs as separable and strongly disposable. A lower residual can be represented
without requiring a proportional reduction in the desirable outputs of the same
operation.

This can be credible when the sample contains independently adjustable abatement:
better sorting, verified capture, an end-of-pipe treatment unit, improved leakage
control, or a production practice that lowers a residual without sacrificing the
recorded service. The observed reference activities then provide evidence for the
cleaner plan.

The assumption is not credible merely because lower pollution is preferred. If an
undesirable output is an unavoidable joint product and reducing it requires curtailing
the associated desirable output, the standard SBM can overstate environmental
improvement opportunity. A weak-disposal environmental technology or another explicit
joint-production model is then needed {cite:p}`chung1997`. Changing the word
`strong` to `weak` while retaining the same balance equations would not change the
technology.

Null jointness is also not imposed by this model. The estimated technology does not
state that zero undesirable output necessarily implies zero desirable output. If the
research question requires that physical relationship, it must be represented by an
environmental technology designed for joint production.

The decision should be made from engineering and institutional knowledge:

| Operational evidence | More defensible starting point |
|---|---|
| Pollutants or residuals can be reduced independently within the study horizon | Standard undesirable-output SBM |
| Pollution reduction necessarily curtails a jointly produced desirable output | Weak-disposal environmental DDF |
| A regulator has declared one specific combination of output expansion and pollution reduction | Environmental DDF with that direction |

These choices define different estimands. They should not be treated as robustness
switches chosen after examining which model gives the preferred ranking.

## Positive normalization is part of the model

Every term in $\rho_o^B$ divides a slack by the evaluated organization's observed
quantity. Inputs, desirable outputs, and undesirable outputs must therefore be finite
and strictly positive.

A genuine zero does not mean “perfect performance” in that dimension. It makes the
relative gap undefined. Replacing zero with an arbitrarily small epsilon can give that
variable enormous influence and make rankings depend on a number with no economic
meaning. Negative quantities are equally outside the standard ratio account. When
zeros or signed data are substantively real, the analyst needs a measure whose
normalization is defined on that domain.

The ratio is invariant to coherent positive changes of measurement units. If every
carbon-dioxide observation is changed from tonnes to kilograms, both the bad-output
slack and its denominator are multiplied by 1,000, leaving their ratio and the score
unchanged. The same holds for inputs and desirable outputs.

Translation is different. Adding a constant to every observation changes the
denominators without preserving proportional gaps. A shift used merely to eliminate
zeros or negative values therefore changes the estimand. Unit invariance should not be
confused with translation invariance.

The equal averages also embed a value judgment. Each input receives weight $1/m$ in
the resource account, and every desirable and undesirable output receives weight
$1/(s+q)$ in the output-side account. Adding a second measure of the same pollutant can
double-count one environmental burden. Combining many pollutants can also reduce the
relative influence of each desirable output. Variable selection and aggregation must
therefore follow the production question, not data availability alone.

## Returns to scale and the comparison population

Under variable returns to scale, the benchmark intensities satisfy

$$
\mathbf1^\top\lambda=1.
$$

The target is a convex combination of represented operations. Under constant returns
to scale this restriction is omitted, allowing proportional replication of reference
activities. The two technologies can support different slack patterns and scores, so
returns to scale must be chosen from the operating context.

VRS is often a natural starting point when plants, hospitals, or municipalities cannot
freely replicate their full operation. CRS can be useful when the production account
supports proportional scaling or when the study deliberately combines scale and
operating performance. Neither is a numerical repair for an inconvenient result.

Reference membership is equally substantive. A contemporaneous comparison asks what
the organizations observed in the same period demonstrate. A pooled retrospective
comparison may allow later, cleaner practices to benchmark earlier operations. A group
restriction can protect mission or regulatory comparability. In every case, the score
describes the opportunities admitted by that reference policy.

For the separable strong-disposal SBM, an analyst can make that comparability
rule observation-specific: a plant may be benchmarked only by facilities under
the same permit, service obligation, or reporting boundary. DEAPack intersects
this declared population with the chosen time/reference policy before it solves
the SBM account. The restriction changes the evidence available to the plant;
it does not change the model's interpretation of independently adjustable
desirable service and residual gaps. A careful report therefore gives the
eligible population alongside the base and effective reference sizes, rather
than calling a restricted score an unconditional environmental ranking.

Self-inclusion normally guarantees that the observed plan is feasible with zero
slacks. An external reference set may fail to represent it under the maintained
input, desirable-output, and bad-output inequalities. Such infeasibility is evidence
about the chosen benchmark; it should not be hidden by changing the disposal
assumption after estimation.

DEAPack records this distinction rather than treating every fit as self-appraisal.
For an externally evaluated plant, the fitted SBM balances must establish that its
recorded operation belongs to the comparison technology. If they do, the plant can
receive an interpretable score even though it was not allowed to benchmark itself.
If the external technology cannot represent the operation, no efficiency
classification is reported. The package Documentation gives the corresponding
diagnostic fields for researchers auditing that distinction.

## A two-plant operating account

Consider two plants using one resource to produce one desirable service with one
undesirable residual:

| Plant | Resource $x$ | Service $y$ | Residual $b$ |
|---|---:|---:|---:|
| A | 1 | 2 | 1 |
| C | 2 | 1 | 2 |

Plant A uses less resource, supplies more service, and generates less residual than C.
Under the VRS separable technology, A is a feasible benchmark for C. The complete
calculation is:

```python
import pandas as pd

from deapack import DEAData, UndesirableSBM

frame = pd.DataFrame(
    {
        "plant": ["A", "C"],
        "resource": [1.0, 2.0],
        "service": [2.0, 1.0],
        "residual": [1.0, 2.0],
    }
)
data = DEAData.from_frame(
    frame,
    dmu="plant",
    inputs="resource",
    outputs="service",
    bad_outputs="residual",
)

result = UndesirableSBM(
    returns_to_scale="vrs",
).fit(data)

summary = result.summary().set_index("dmu_id")
summary.loc[
    ["A", "C"],
    [
        "efficiency",
        "input_inefficiency",
        "desirable_output_inefficiency",
        "bad_output_inefficiency",
        "output_inefficiency",
        "output_account_factor",
    ],
]

result.targets_for("C")[[
    "role", "variable", "observed", "target"
]]
result.slacks.query("dmu_id == 'C'")[[
    "role", "variable", "slack", "normalized_slack"
]]

improvement_figure = result.plot(kind="improvement", dmu_id="C")
```

```{figure} ../../_static/figures/undesirable-sbm-improvement-result.svg
:name: fig-undesirable-sbm-improvement-result
:alt: Plant C's environmental SBM improvement account separates resource saving, desirable service gain, and undesirable residual reduction, then reports their observed and target quantities
:width: 100%

Plant C's selected environmental improvement account under the maintained
technology. The display keeps the
50 percent resource saving, 100 percent desirable-service gain, and 50 percent
undesirable-residual reduction in distinct operational rows. Together they reconstruct
$2/7=(1-1/2)/(1+3/4)$. This opportunity is conditional on the separable,
strong-disposal technology: the figure neither identifies what caused the gaps, assigns
a damage value to the residual, nor says that this is the only feasible improvement
plan.
```

The results are:

| Plant | Efficiency | Input excess account | Desirable-output shortfall account | Bad-output excess account |
|---|---:|---:|---:|---:|
| A | 1 | 0 | 0 | 0 |
| C | $2/7\approx0.286$ | $1/2$ | $1$ | $1/2$ |

For C, the target is $(\widehat x,\widehat y,\widehat b)=(1,2,1)$. In original
units, it releases one resource unit, adds one service unit, and reduces the residual
by one unit.

The normalized resource account is

$$
I_C^x=\frac{2-1}{2}=\frac12.
$$

The output-side account averages a 100 percent desirable-output shortfall and a
50 percent undesirable-output excess:

$$
I_C^{yb}
=\frac12\left(\frac{2-1}{1}+\frac{2-1}{2}\right)
=\frac34.
$$

Consequently,

$$
\rho_C^B
=\frac{1-1/2}{1+3/4}
=\frac{2}{7}.
$$

The low score is not itself a recommendation to cut every variable by $5/7$. It is a
fractional summary of three different gaps. The target table gives the actionable
quantities, while the peer evidence shows that Plant A supports the comparison.

The case is intentionally transparent. In a larger dataset, a target can be a convex
combination of several plants, and multiple peer combinations can generate the same
optimal score. A stable efficiency value does not guarantee a unique operational
recipe.

## From score to environmental management evidence

A useful result table begins with the efficiency score but does not end there. It
should retain the three component accounts and the important physical targets. For a
plant with several fuels, services, and pollutants, management needs to know whether
the selected opportunity is concentrated in fuel use, service capacity, carbon
dioxide, local air pollution, or several dimensions together.

Peers provide comparative evidence, not engineering instructions. A cleaner peer may
use different equipment, fuel quality, weather conditions, product mix, or regulatory
technology. Before a target becomes an investment or operating plan, specialists must
assess whether those omitted differences make the comparison transferable.

Alternate optima deserve the same caution. The fractional objective can support more
than one peer combination or slack allocation with the same score. If a decision
depends on one exact emissions target, the analyst should investigate target ranges or
apply a justified secondary selection rule rather than treating the first optimal
solution as uniquely optimal.

A concise empirical report should state:

- which variables are inputs, desirable outputs, and undesirable outputs;
- why independent reduction of the undesirable outputs is technologically credible;
- the returns-to-scale and reference-population assumptions;
- the score together with resource, desirable-output, and bad-output gap accounts;
- key targets in their original units and the peers supporting them; and
- the treatment of infeasible observations, zeros, and alternate optima.

The analysis can support a statement such as:

> Relative to the VRS comparison technology, Plant C has an undesirable-output SBM
> score of $2/7$. One optimal plan uses one less resource unit, supplies one additional
> service unit, and generates one less residual unit.

It cannot, without further evidence, establish that management caused the gap, that
adopting a peer's practice will cause the predicted improvement, or that the
environmental benefit exceeds its implementation cost. It does not attach damage
values to pollutants, measure profit, or estimate the effect of regulation.

The standard undesirable-output SBM is powerful precisely because its claim is
focused. It converts a feasible environmental comparison into a transparent account
of variable-specific resource excesses, desirable-output shortfalls, and undesirable-
output excesses. When its separability and positivity assumptions match the operating
system, that account is more informative than a single proportional adjustment. When
they do not, a different environmental technology—not a relabeled option—is required.
