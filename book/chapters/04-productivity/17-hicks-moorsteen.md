# Hicks--Moorsteen Productivity: Output Growth Relative to Resource Growth

A hospital that treats 8 percent more patients after hiring 10 percent more staff has
expanded, but it has not necessarily become more productive. A manufacturer that
reduces output by 2 percent while reducing materials, labor, and capital services by
10 percent may have contracted and still improved productivity. In both cases the
economic question is the same: **did aggregate output quantity change faster or slower
than aggregate input quantity?**

The Hicks--Moorsteen index answers that question through a complete quantity account:

$$
HM^{t,t+1}
=\frac{Q_y^{t,t+1}}{Q_x^{t,t+1}},
$$

where $Q_y^{t,t+1}$ is an aggregate output quantity index and
$Q_x^{t,t+1}$ is an aggregate input quantity index between periods $t$ and
$t+1$. Values above one indicate total-factor-productivity growth, one indicates no
change, and values below one indicate decline.

“Complete” has a precise and limited meaning here. The index compares the aggregate
change in every desirable output included in the study with the aggregate change in
every included productive input. It therefore answers whether output quantity grew
faster than resource use within the chosen organizational boundary. It does not
recover omitted quality, environmental effects, unpaid labor, or unmeasured capital
services. Those omissions narrow the economic meaning of the resulting productivity
change even when the formula is internally complete.

This construction belongs beside, rather than underneath, the conventional Malmquist
index. It uses both output- and input-oriented quantity comparisons so that the final
measure remains visibly “aggregate outputs divided by aggregate inputs.” The
production technology supplies the aggregation rule when observed prices are absent
or unsuitable {cite:p}`bjurek1996`. That makes Hicks--Moorsteen a distinct mainstream
productivity family, not a renamed orientation or a special decomposition of another
index.

```{figure} ../../_static/figures/hicks-moorsteen-accounting.svg
:name: fig-hicks-moorsteen-accounting
:alt: Hicks-Moorsteen total-factor-productivity change from t to t plus 1 is output quantity growth divided by input quantity growth, with both period technologies contributing symmetrically
:width: 96%

The Hicks--Moorsteen production account. Technologies $\mathcal T^t$ and
$\mathcal T^{t+1}$ each provide an output quantity comparison and an input quantity
comparison. The two period views are reconciled symmetrically before total-factor-
productivity change is calculated as $Q_y^{t,t+1}/Q_x^{t,t+1}$.
```

## Why are separate output and input quantity indexes needed?

With one output and one input, productivity change can be described informally as the
change in output divided by the change in input. Real organizations rarely have that
simple a production account. A hospital combines physicians, nurses, beds, equipment,
and purchased services to deliver several kinds of care. Adding those resources or
services in their physical units would be meaningless. Market prices might aggregate
them, but prices may be regulated, missing, endogenous, or unrelated to the public
value of a service.

Hicks--Moorsteen uses the production possibilities represented by comparable
organizations to aggregate these multidimensional quantities. Let
$z^t=(x^t,y^t)$ and $z^{t+1}=(x^{t+1},y^{t+1})$ denote one organization's operating
plans. The input vectors $x^t$ and $x^{t+1}$ record resource quantities; the output
vectors $y^t$ and $y^{t+1}$ record desirable products or services. Let
$\mathcal T^t$ and $\mathcal T^{t+1}$ be the technologies represented by the two
period-specific reference populations.

For a technology $\mathcal T^\tau$, the Shephard output distance
$D_O^\tau(x,y)$ asks how the output bundle compares with producible output while
inputs are held fixed. The Shephard input distance $D_I^\tau(x,y)$ asks how the input
bundle compares with required input while outputs are held fixed. Formally,

$$
D_O^\tau(x,y)=\inf\{\delta>0:(x,y/\delta)\in\mathcal T^\tau\},
\qquad
D_I^\tau(x,y)=\sup\{\delta>0:(x/\delta,y)\in\mathcal T^\tau\}.
$$

These distances do not assign a monetary value to a nurse, a machine, or a treatment.
They aggregate quantities through the trade-offs represented by the reference
technology. The resulting indexes are therefore production-based quantity measures,
not cost, revenue, profit, utility, or welfare indexes.

Their ratio form also protects the substantive result from a coherent change of
measurement units. Recording labor in hours rather than thousands of hours, or energy
in megawatt-hours rather than kilowatt-hours, should not change the productivity
comparison when the conversion is applied consistently to every relevant observation.
This useful invariance does not excuse inconsistent definitions. Reclassifying agency
staff as purchased services in one year, changing the boundary of capital services,
or broadening output coverage alters the production account itself. Unit conversion
and concept revision are economically different operations.

## Why does each period get its own view of quantity change?

Using only $\mathcal T^t$ would make the earlier production possibilities the sole
judge of both periods. Using only $\mathcal T^{t+1}$ would privilege the later
possibilities. Hicks--Moorsteen treats the comparison bilaterally: each technology
supplies one view of output quantity change and one view of input quantity change.

The four constituent comparisons are compactly summarized below. Each is a ratio of
two distances, so together they require four output-distance and four input-distance
evaluations.

| Quantity view | What is held fixed? | Distance comparison |
|---|---|---|
| $Q_y^t$ | Base-period inputs $x^t$ | $D_O^t(x^t,y^{t+1})/D_O^t(x^t,y^t)$ |
| $Q_y^{t+1}$ | Comparison-period inputs $x^{t+1}$ | $D_O^{t+1}(x^{t+1},y^{t+1})/D_O^{t+1}(x^{t+1},y^t)$ |
| $Q_x^t$ | Base-period outputs $y^t$ | $D_I^t(x^{t+1},y^t)/D_I^t(x^t,y^t)$ |
| $Q_x^{t+1}$ | Comparison-period outputs $y^{t+1}$ | $D_I^{t+1}(x^{t+1},y^{t+1})/D_I^{t+1}(x^t,y^{t+1})$ |

The first two rows ask how the output bundle changed when each period's own input
bundle and technology provide the basis for comparison. The next two ask how the input
bundle changed when each period's own output bundle and technology provide the basis.
This pairing is why the eight evaluations are economically necessary. They are not
eight unrelated efficiency exercises: they build two independent quantity accounts,
each seen from both periods.

Neither period view is given final authority. Their geometric means form the bilateral
output and input quantity indexes:

$$
Q_y^{t,t+1}=\left(Q_y^tQ_y^{t+1}\right)^{1/2},
\qquad
Q_x^{t,t+1}=\left(Q_x^tQ_x^{t+1}\right)^{1/2}.
$$

The geometric mean reconciles two proportional comparisons and treats the dates
symmetrically. It also gives the index its time-reversal property: if the same two
periods are compared in reverse order, $Q_y$, $Q_x$, and $HM$ become the reciprocals
of their forward values. A measured 10 percent forward increase is therefore undone
by the corresponding reverse comparison. This is what “bilateral” means here; it does
not imply that the index is automatically consistent across three or more periods.

## How should the three headline numbers be read together?

The output quantity index describes the proportional change in the aggregate desirable
output bundle. Thus $Q_y^{t,t+1}>1$ indicates output quantity growth and a value below
one indicates contraction. The input quantity index has the analogous meaning for the
aggregate resource bundle. A value $Q_x^{t,t+1}>1$ means that resource quantity
increased; it is not an efficiency score and should not be described as “better.”

The productivity conclusion comes from their ratio. Several combinations are possible:

| Output account | Input account | Productivity reading |
|---|---|---|
| $Q_y>1$ and $Q_x=1$ | More output, unchanged aggregate input | Productivity rises |
| $Q_y>1$ and $1<Q_x<Q_y$ | Output and input both grow, but output grows faster | Productivity rises |
| $Q_y<1$ and $Q_x<Q_y$ | Output contracts, but input contracts more | Productivity rises |
| $Q_y>1$ and $Q_x>Q_y$ | Expansion requires proportionally more input | Productivity falls |

This table prevents a common managerial error: equating expansion with productivity.
An organization can grow by consuming resources faster than it expands services. It
can also become more productive while deliberately reducing its scale of operation.
The output and input indexes reveal which economic pattern lies behind the headline
ratio.

Because the account is multiplicative, percentage-point subtraction is only an
approximation. If output quantity rises by 15.33 percent and input quantity rises by
2.00 percent, productivity change is $1.1533/1.0200=1.1307$, or about 13.07 percent.
The exact statement is a ratio of quantity indexes.

## What does the account say about Unit D?

The `productivity_panel` dataset follows five organizations using capital and labor to
produce one desirable service. The following case estimates the adjacent-period
Hicks--Moorsteen account under variable returns to scale, so the reference technology
does not presume that every observed activity can be proportionally replicated at any
size.

```python
from deapack import DEAData, HicksMoorsteenDEA, load_dataset

frame = load_dataset("productivity_panel")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    period="period",
    inputs=["capital", "labor"],
    outputs="output",
)

result = HicksMoorsteenDEA(returns_to_scale="vrs").fit(data)
unit_d = result.summary().query(
    "dmu_id == 'D' and comparison_period == 2021"
)[[
    "output_quantity_index",
    "input_quantity_index",
    "productivity_change",
]]

print(unit_d.round(4).to_string(index=False))

comparison_figure = result.plot(
    kind="performance",
    metric="productivity_change",
    period=2021,
    view="points",
)
```

| Unit D, 2020--2021 | Value | Production-account interpretation |
|---|---:|---|
| $Q_y^{2020,2021}$ | 1.1533 | Aggregate output quantity increased by about 15.33 percent |
| $Q_x^{2020,2021}$ | 1.0200 | Aggregate input quantity increased by about 2.00 percent |
| $HM^{2020,2021}$ | 1.1307 | Output quantity grew about 13.07 percent faster per unit of aggregate input |

```{figure} ../../_static/figures/hicks-moorsteen-performance-result.svg
:name: fig-hicks-moorsteen-performance-result
:alt: Hicks-Moorsteen productivity change from 2020 to 2021 for five organizations, with a vertical line at one indicating no productivity change and Unit D reported at approximately 1.1307
:width: 100%

The fitted 2020--2021 Hicks--Moorsteen changes across the five organizations.
The points are a screening view of the headline ratio: Unit D's position at
about 1.1307 is meaningful only together with its output-quantity index 1.1533
and input-quantity index 1.0200. A point is displayed only when its complete
eight-distance quantity account is internally consistent. The figure is not a
ranking of causes or managerial merit.
```

Unit D expanded rather than economized on total resource quantity. Its productivity
improvement comes from output quantity increasing proportionally more than input
quantity. That is a useful management statement: growth was not achieved simply by a
still larger proportional expansion of the measured resource bundle.

It is not yet a causal statement. The account does not establish whether the change
came from scheduling, staff skills, capital renewal, case mix, demand, regulation, or
measurement revision. Those explanations require institutional evidence and, where
appropriate, a separate causal design. The DEA result supplies a structured outcome
to explain; it does not identify the explanation.

## Why is this not the usual Malmquist decomposition?

The conventional Malmquist index builds one oriented productivity comparison and is
often expressed as efficiency change multiplied by technical change. Hicks--Moorsteen
instead builds a complete output quantity index and a complete input quantity index,
then divides the former by the latter. Its eight distance evaluations serve that
quantity-accounting identity.

It is therefore invalid to copy “efficiency change,” “technical change,” or “catch-up”
from a conventional Malmquist result and attach them to $HM^{t,t+1}$. Those components
need not reconstruct the Hicks--Moorsteen index and do not inherit an interpretation
merely because both families use distance functions. A study that requires scale,
mix, or technical-efficiency components must adopt a decomposition defined for its own
native productivity measure and state the additional assumptions. The residual from
$HM-Q_y/Q_x$ is not an undiscovered economic component; the identity already defines
HM exactly.

The distinction matters even when two indexes happen to produce the same number in a
simple dataset. Numerical agreement can arise under special technologies or data
patterns. It does not make the underlying production questions equivalent.

## Can bilateral changes be chained into a long-run history?

Not without qualification. Hicks--Moorsteen is symmetric for a pair of periods, but
bilateral symmetry is different from circularity. With three periods, it is generally
possible that

$$
HM^{t,t+1}HM^{t+1,t+2}\neq HM^{t,t+2}.
$$

The adjacent changes use different pairs of technologies, while the direct comparison
uses the first and last technologies. The cumulative result can therefore depend on
the path through time. This is not a computational defect; it follows from allowing
each bilateral comparison to use its own two-period information.

For year-to-year operational reporting, that local bilateral interpretation may be
exactly what is wanted. For a long historical series in which every date must share a
fixed basis and adjacent changes must multiply to a unique first-to-last result, the
research design needs a multilateral or fixed-reference quantity index. That is a
different information policy, not a switch to be applied after seeing that a chain is
inconvenient. Reports should say whether a displayed cumulative value is a chain of
bilateral indexes or a comparison under a common multilateral reference.

## What assumptions limit the management interpretation?

The quantity indexes inherit every substantive choice used to construct
$\mathcal T^t$ and $\mathcal T^{t+1}$. Under constant returns to scale, observed
activities can be proportionally replicated; under variable returns to scale,
comparisons remain within a convex scale range represented by the data. The choice can
change both $Q_y$ and $Q_x$, especially when organizations operate at very different
sizes. Returns to scale is therefore part of the economic specification, not an
afterthought.

The reference population must also represent feasible comparison opportunities. A
national teaching hospital, a rural clinic, and an outpatient center may not belong in
one unrestricted technology. Changes in sample composition can move the quantity
indexes even when an organization's own records do not change. Organizations must be
matched by identity across the two periods, while observations that lack a match may
still contain information relevant to a period's production possibilities. The study
should distinguish the population receiving change estimates from the population
allowed to define the benchmark.

Data definitions must be stable over time. A reported increase in treatments is not a
genuine output quantity increase if coding coverage changed. Capital expenditure is
not automatically a capital-service quantity, and headcount is not always an adequate
measure of labor input. Quality changes require explicit representation rather than a
verbal adjustment after estimation.

The account developed here uses desirable outputs. If pollution, complications, or
other undesirable outcomes are central to the production question, their treatment
requires an environmental technology with declared assumptions about joint production
and disposability. They should not be inserted as ordinary desirable outputs merely to
retain the same formula.

Finally, Hicks--Moorsteen is a quantity productivity index, not a profitability or
welfare measure. It does not show whether output growth was valuable enough to justify
its cost, whether an input mix minimized expenditure, or whether social benefits
exceeded environmental harm. Prices, preferences, and policy objectives answer those
questions. The aggregate-quantity interpretation should remain separate from them
{cite:p}`odonnell2008quantity`. An organization can become more productive yet less
profitable when output prices move against it or input prices rise; favorable price
movements can likewise improve profitability without a physical productivity gain.
In a quantity-price account, profitability change combines total-factor-productivity
change with relative-price recovery. Hicks--Moorsteen supplies the quantity part of
that management account, not the price part {cite:p}`odonnell2010profitability`.

## The production account to carry forward

A clear Hicks--Moorsteen report keeps three numbers together:
$Q_y^{t,t+1}$, $Q_x^{t,t+1}$, and $HM^{t,t+1}$. It identifies the two period
technologies, returns-to-scale assumption, input and output definitions, reference
populations, and period pairing. It describes the result as a bilateral quantity
account and does not promise circularity for a chain of adjacent comparisons.

The economic message is then simple without being simplistic. Output quantity may
grow or contract; input quantity may grow or contract; productivity rises when the
first changes more favorably than the second. The eight distance evaluations make
that multidimensional comparison possible, but the conclusion remains a transparent
ratio of aggregate outputs to aggregate inputs. That transparency is the reason to
treat Hicks--Moorsteen as an independent total-factor-productivity family.
