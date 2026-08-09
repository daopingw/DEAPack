# The Luenberger Indicator: Change in Units of a Declared Programme

A hospital board may define next year's improvement programme without ever using a
percentage. It might ask each hospital to hold its staffed capacity constant while
treating 500 additional patients. A manufacturer might commit to saving ten tonnes of
material while delivering 200 additional units of product. A public transport agency
might seek a joint reduction in vehicle-hours and increase in passenger journeys. In
each case, management has described improvement as a **bundle of operational
changes**.

The ordinary Luenberger productivity indicator asks whether the organization realized
more or less of that improvement programme between two periods. It reports change in
the programme's own units. If one unit means “save ten tonnes of material and deliver
200 extra units,” a value of 0.4 corresponds to four tonnes of saving and 80 additional
units along that joint plan. The direction therefore embeds management's chosen
resource--output trade-off and determines what counts as progress. Selecting it after
seeing the ranking would replace the original decision problem with a convenient
retrospective one.

This makes Luenberger measurement useful when proportional expansion or contraction is
not the question of interest. The familiar Malmquist index asks about proportional
productivity change and reports a ratio around one. The Luenberger indicator measures
change additively around zero. Its foundations lie in directional benefit and distance
functions and in exact nonradial productivity measurement {cite:p}`chambers1996,chambers2002`.

An important boundary should be clear from the outset. The ordinary Luenberger
indicator in this chapter is a **directional technical-performance indicator**. It
does not, merely because it is called a productivity indicator, construct a complete
total-factor-productivity account in which an aggregate output quantity index is
compared with an aggregate input quantity index. Its value is nevertheless
economically meaningful: it reports change relative to production opportunities in
the units of a programme that the analyst has made explicit.

## From an operating commitment to a directional distance

Let $\mathcal T^\tau$ denote the production possibilities represented by the
organizations in reference period $\tau$. An operating plan $z=(x,y)$ uses the
resource vector $x$ to
deliver the desirable-output vector $y$. The analyst declares a common programme

$$
g=(g^x,g^y),
$$

where $g^x$ contains planned input savings and $g^y$ contains planned output gains.
Both are written as nonnegative magnitudes. Completing $\beta$ units of the programme
would move the operating plan to

$$
(x-\beta g^x,\;y+\beta g^y).
$$

The directional distance relative to period-$\tau$ opportunities is

$$
D^\tau(z;g)
=\sup\left\{\beta\in\mathbb{R}:
(x-\beta g^x,\;y+\beta g^y)\in\mathcal T^\tau\right\}.
$$

This expression asks how much of the specified resource saving and output gain remains
attainable from plan $z$. If $D^\tau(z;g)=0.6$, comparable practice supports another
0.6 units of the joint programme. A value of zero means that the whole package cannot
be advanced further under that period's observed opportunities, although other
unmeasured or differently composed improvements may still be possible. A smaller
remaining amount indicates that the organization is closer to exhausting this
particular improvement opportunity.

The programme need not change every variable. A health authority interested in
additional treatments at unchanged staffed capacity can set $g^x=0$ and give $g^y$
the physical size of one treatment commitment. A resource-conservation programme can
hold outputs fixed by setting $g^y=0$. A joint programme assigns positive magnitudes
to both sides. Zeros mean that the corresponding quantities are commitments to be held
fixed during this particular appraisal; they do not imply that those quantities are
unimportant to production.

Because the indicator is cardinal, the size of the programme matters. Replacing $g$
with $cg$, for $c>0$, changes the numerical distance according to

$$
D^\tau(z;cg)=\frac{1}{c}D^\tau(z;g).
$$

Doubling the physical size of one programme unit therefore halves the number of
programme units reported. That is not a defect. It is the same reason that 500 metres
and 0.5 kilometres use different numbers to describe the same distance. Trouble
arises only when results measured under different programmes are compared as though
they shared one unit.

## Four appraisals behind one change indicator

Consider one organization observed in adjacent periods $t$ and $t+1$, with plans
$z^t=(x^t,y^t)$ and $z^{t+1}=(x^{t+1},y^{t+1})$. Productivity measurement has to
separate two changes that occur at the same time. The organization may realize more of
the opportunities available to it, and the best-practice opportunities represented by
the comparison population may themselves become more or less favorable.

To distinguish these changes, each plan is appraised against each period's production
opportunities:

| Appraisal | Economic question |
|---|---|
| $D^t(z^t;g)$ | How much of the programme remained unrealized by the old plan under old opportunities? |
| $D^t(z^{t+1};g)$ | How would the new plan have performed under old opportunities? |
| $D^{t+1}(z^t;g)$ | How would the old plan perform under new opportunities? |
| $D^{t+1}(z^{t+1};g)$ | How much remained unrealized by the new plan under new opportunities? |

```{figure} ../../_static/figures/luenberger-programme-ledger.svg
:name: fig-luenberger-programme-ledger
:alt: One common input-saving and output-expansion programme is used to appraise two period-specific operating plans against both period-specific production technologies, producing four directional distances and one additive change account
:width: 96%

One declared programme supplies the common unit for all four appraisals. The two
diagonal cells describe contemporaneous operating shortfalls; the off-diagonal cells
show how each plan would be assessed under the other period's represented
opportunities.
```

Holding the old technology fixed gives one view of performance change:

$$
P^t
=D^t(z^t;g)-D^t(z^{t+1};g).
$$

Holding the new technology fixed gives the other:

$$
P^{t+1}
=D^{t+1}(z^t;g)-D^{t+1}(z^{t+1};g).
$$

In each expression, the old plan's unrealized potential is compared with the new
plan's unrealized potential while the benchmark is held constant. A positive
difference means that the new plan realizes more of the declared programme. Neither
period is given sole authority, so the adjacent-period Luenberger indicator takes the
arithmetic mean:

$$
\begin{aligned}
L^{t,t+1}
&=\frac{1}{2}\left(P^t+P^{t+1}\right)\\
&=\frac{1}{2}\left[
D^t(z^t;g)-D^t(z^{t+1};g)
+D^{t+1}(z^t;g)-D^{t+1}(z^{t+1};g)
\right].
\end{aligned}
$$

The reporting convention in this book is straightforward: $L>0$ indicates measured
improvement, $L=0$ no measured change, and $L<0$ measured decline. These are programme
units, not percentage points. An indicator of 0.25 and a Malmquist index of 1.25 do not
say the same thing, even though both numbers may casually be described as a 25 percent
improvement. Only the latter is a ratio with that percentage interpretation.

## An additive account of two benchmark-relative changes

The four appraisals also support an exact additive decomposition. Define relative
operating-performance change as

$$
EC_L^{t,t+1}
=D^t(z^t;g)-D^{t+1}(z^{t+1};g).
$$

This component compares the programme left unrealized by the organization against the
best-practice opportunities represented in each plan's own period. A positive value
means that the contemporaneous shortfall became smaller. “Catch-up” is often used as
historical shorthand, but the more informative statement is that the organization
realized more of the declared programme relative to its contemporaneous comparison
population.

The component is not proof of better management. A smaller shortfall may accompany
improved scheduling, maintenance, learning, or coordination, but it may also reflect a
different case mix, reporting revision, or comparison population. DEA supplies the
benchmark-relative account; institutional evidence is needed to explain its cause.

The change in represented production opportunities is

$$
TC_L^{t,t+1}
=\frac{1}{2}\left[
D^{t+1}(z^t;g)-D^t(z^t;g)
+D^{t+1}(z^{t+1};g)-D^t(z^{t+1};g)
\right].
$$

This component asks whether the new reference technology supports more of the
programme than the old reference technology, first at the old operating plan and then
at the new one. A positive value means that the best-practice opportunities represented
by the declared samples became more favorable for the plans and programme being
studied. “Frontier shift” is the familiar shorthand, but it should not be mistaken for
evidence that a new invention appeared or diffused. The reference set can change
because of investment, regulation, demand, data coverage, entry and exit, or genuine
technical progress.

The two components reconstruct the overall indicator exactly:

$$
L^{t,t+1}=EC_L^{t,t+1}+TC_L^{t,t+1}.
$$

This identity is the heart of the account. It also imposes discipline on
interpretation. The components are allocations of one measured change under one
programme and one pair of reference technologies. They are not independent causal
effects, and components calculated with different directions cannot legitimately be
added together.

## Why a cross-period distance may be negative

A contemporaneous plan included in its own reference technology normally has
nonnegative unrealized improvement potential. A cross-period plan is different. The
new plan may deliver more than the old technology can reproduce. If the only way to
place that plan inside the old production possibilities is to reverse the declared
programme, its directional distance is negative.

Suppose one programme unit means adding five treatment batches with resources held
fixed. A new plan delivers ten batches more than the old reference technology can
support. Relative to the old opportunities, the plan must surrender two programme
units before it becomes reproducible, so its cross-period distance is $-2$. This is not
“negative efficiency.” It is a signed statement about the position of one period's
plan relative to another period's represented opportunities.

Allowing the sign is essential. Replacing a negative cross-period value by zero would
erase evidence that the later plan exceeded the earlier opportunities. It would also
distort the measured change in represented opportunities and generally break the
additive identity. A valid negative value should therefore be explained, not repaired.
It is conceptually distinct from a comparison that cannot be formed under the declared
technology and data assumptions.

## A hospital programme with an explicit common direction

Consider two hospitals observed in 2020 and 2021. Inputs are measured in standardized
staff bundles and outputs in batches of 100 completed treatments. In 2020, the observed
best-practice rate is one treatment batch per staff bundle. In 2021, both hospitals
demonstrate two treatment batches per staff bundle.

The authority's programme is deliberately simple: **hold staff input constant and add
one treatment batch**. Thus every hospital and every period is evaluated with the same
direction, $g^x=0$ and $g^y=1$.

```python
import pandas as pd

from deapack import DEAData, LuenbergerProductivityIndicator

frame = pd.DataFrame(
    {
        "hospital": ["A", "B", "A", "B"],
        "year": [2020, 2020, 2021, 2021],
        "staff_bundles": [1.0, 2.0, 1.0, 2.0],
        "treatment_batches": [1.0, 2.0, 2.0, 4.0],
    }
)

data = DEAData.from_frame(
    frame,
    dmu="hospital",
    period="year",
    inputs="staff_bundles",
    outputs="treatment_batches",
)

account = LuenbergerProductivityIndicator(
    input_direction={"staff_bundles": 0.0},
    output_direction={"treatment_batches": 1.0},
    returns_to_scale="crs",
).fit(data)

account.summary()[[
    "dmu_id",
    "base_period",
    "comparison_period",
    "productivity_change",
    "efficiency_change",
    "technical_change",
]]

figure = account.plot(
    kind="performance",
    metric="productivity_change",
    period=2021,
    view="points",
)
```

```{figure} ../../_static/figures/luenberger-performance-result.svg
:name: fig-luenberger-performance-result
:alt: A point plot reports one additional treatment-batch programme unit for Hospital A and two for Hospital B between 2020 and 2021, with zero as the no-change benchmark
:width: 88%

The plot compares the two hospitals in **absolute programme
units**. Hospital A records 1 and Hospital B records 2 because one unit always
means one additional treatment batch at unchanged staff input. B's value of 2
does **not** mean that B is twice as productive as A; neither value is a ratio
or percentage.
```

For Hospital A, the four appraisals have transparent values:

| Appraisal | Value | Meaning |
|---|---:|---|
| $D^{2020}(z^{2020};g)$ | 0 | The 2020 plan is on the 2020 benchmark. |
| $D^{2020}(z^{2021};g)$ | $-1$ | The 2021 plan exceeds 2020 opportunities by one programme unit. |
| $D^{2021}(z^{2020};g)$ | 1 | Under 2021 opportunities, the old plan could add one treatment batch. |
| $D^{2021}(z^{2021};g)$ | 0 | The 2021 plan is on the 2021 benchmark. |

The overall change is therefore

$$
L^{2020,2021}
=\frac{1}{2}\{[0-(-1)]+[1-0]\}=1.
$$

Hospital A remains on its contemporaneous benchmark in both years, so
$EC_L^{2020,2021}=0$. The represented production opportunities become more favorable
by one programme unit at the hospital's scale, so $TC_L^{2020,2021}=1$. The account is
$1=0+1$: with the same staff bundle, the hospital delivers one additional batch of 100
treatments, and the measured change is associated with changed sector opportunities
rather than a smaller contemporaneous operating shortfall.

Hospital B receives $L=2$ because the same physical programme unit is applied to an
operation twice as large. This does not mean that B is “twice as productive” as A. It
means that B realizes two additional batches under an absolute programme measured in
treatment batches. If the policy question concerns proportional rather than absolute
change, the analyst needs a proportional measure or a different, explicitly justified
common normalization. Changing the programme after seeing the result would change the
question, not merely its presentation.

This interpretation requires all four appraisals to be available under the same
programme and to close the account $L=EC_L+TC_L$. If either condition fails, there is
no productivity conclusion for that transition. The detailed implementation evidence
belongs in the DEAPack Documentation.

## Choosing a direction that can support a decision

A defensible direction begins with the purpose of the study. A regulator may derive it
from a stated service obligation. A firm's operating plan may supply target reductions
in labor-hours, energy, and materials together with desired gains in output. A clinical
study may hold resources fixed because its question concerns attainable service. The
direction should use stable variable definitions and physical units and should be
declared before the resulting rankings are interpreted.

Comparability is especially important over time. The same $g$ must give “one programme
unit” the same meaning in all four appraisals. If every organization receives a
different direction proportional to its own current operation, its indicator is
measured in its own private unit; additive comparisons across organizations and periods
then lose their immediate meaning. Such directions may answer legitimate local
questions, but they do not automatically form the common cardinal account developed in
this chapter.

Unit conversion is harmless when the data and the direction are converted together.
Expressing both treatments and the treatment component of $g$ in individual cases
rather than hundreds of cases leaves the underlying programme unchanged. By contrast,
changing only $g$, using a future-expanded sample to redefine a historical direction,
or assigning a new programme to each period alters the estimand. A useful sensitivity
analysis can compare several substantively defensible common programmes, but each
scenario should retain its own label and unit.

The direction is not a vector of prices and does not reveal willingness to trade one
resource or service for another. It states a physical operating commitment. If the
research question is about cost, revenue, profit, or welfare, observed prices and the
corresponding economic-efficiency model are needed. Directional productivity and
price-based economic performance are complementary accounts, not substitutes.

## Which change question matches the decision?

Several prominent productivity accounts use distance functions. The practical choice
begins with the decision question, not with the model name.

| Decision account | Question the analysis answers | Reporting form and neutral value | Required production comparison |
|---|---|---|---|
| Proportional productivity change | How did proportional productivity change relative to period-specific production opportunities? | Multiplicative ratio; no change at 1 | Radial input or output comparison |
| Change in a declared operating programme | How many more units of the programme were realized? | Additive indicator; no change at 0 | One common input-saving/output-expansion direction |
| Joint desirable-output and residual performance | How did performance change when useful production and undesirable residuals are modeled jointly? | Multiplicative environmental index; no change at 1 | Environmental technology, disposability assumptions, and a pollution-reduction direction |
| Complete output--input quantity change | Did aggregate output quantity grow faster than aggregate input quantity? | Multiplicative complete TFP ratio; no change at 1 | Output quantity index divided by input quantity index |

The proportional account is developed in the
{doc}`Malmquist chapter <malmquist-productivity-reference-information>`, the joint
production-and-residual account in the
{doc}`environmental productivity chapter <environmental-productivity-ml-common-reference>`,
and the complete quantity account in the
{doc}`Hicks--Moorsteen chapter <17-hicks-moorsteen>`.

Ordinary Luenberger is not Malmquist written with subtraction signs. It changes both
the unit of measurement and the operating adjustment being evaluated. It is also not
an environmental model merely because the direction could conceptually include a
reduction. Undesirable outputs require a joint environmental production technology and
explicit assumptions about how desirable production and residual generation are
linked. Those assumptions belong to the environmental productivity family.

Nor is ordinary Luenberger the Hicks--Moorsteen index. Hicks--Moorsteen constructs a
complete quantity account by dividing aggregate output change by aggregate input
change. Ordinary Luenberger reports technical-performance change along one declared
programme. Source-defined hybrid indicators are not enumerated here: a shared word in
their names does not make them aliases of the four core decision accounts.

The practical choice follows the decision question. Use ordinary Luenberger when the
organization or policy maker can state a meaningful common programme in physical
units, especially when inputs are to fall while outputs rise together. Use Malmquist
when proportional radial change is the intended account. Use an environmental measure
when undesirable production is part of the technology, and use a complete quantity
index when the claim concerns total output quantity relative to total input quantity.

A careful empirical conclusion might therefore read: “Between 2020 and 2021, Hospital
A realized one additional unit of the declared programme of unchanged staffed capacity
and 100 additional treatments. Its contemporaneous operating shortfall did not change;
the measured gain was allocated to more favorable production opportunities represented
by the two comparison samples.” That statement records what was measured, in what
unit, and relative to which economic opportunities. It does not turn a benchmark
account into a claim about managerial effort or the cause of sector change.
