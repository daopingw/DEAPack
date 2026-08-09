# Dynamic DEA: Carry-overs, Intertemporal Commitments, and the Efficiency of a Trajectory

A manager can often improve this year's figures by borrowing from next year.
Maintenance can be postponed, difficult cases can remain in a queue, inventory
can be run down, and experienced staff can be reassigned from capability
building to current delivery. An annual efficiency analysis may reward every
one of these choices. The organization that inherits depleted capacity,
unresolved work, or an empty pipeline will judge them differently.

Dynamic data envelopment analysis is designed for this management problem. It
asks whether a sequence of operating plans remains attainable when the assets,
productive capabilities, and obligations passed between periods are treated as part of
production. Tone and Tsutsui's dynamic slacks-based measure (dynamic SBM)
expresses that idea with a non-radial efficiency measure
{cite:p}`tone2010dynamic`.

The unit being appraised is no longer "organization $o$ in year $t$." It is
organization $o$'s complete trajectory over a stated horizon. Period results
remain useful, but they diagnose one jointly feasible plan; they are not scores
from independent annual contests. This change of viewpoint is the defining
idea of the dynamic DEA family.

## A panel becomes dynamic only when the past constrains the future

Several years of observations do not by themselves define a dynamic
technology. A panel is a data structure. It becomes economically dynamic only
when a measured condition left by one period constrains what a later period
can do. Capital capacity, inventories, loan quality, unfinished treatments,
research pipelines, maintenance backlogs, and contractual obligations can all
play this role.

Two questions locate the relevant model family:

| Does the study contain an inherited state? | Does it model processes inside the organization? | Appropriate interpretation |
|---|---|---|
| No | No | Static or panel DEA: years supply repeated observations or different reference populations |
| No | Yes | Network DEA: internal handoffs coordinate processes within a period |
| Yes | No | Dynamic DEA: carry-overs coordinate the organization's plans through time |
| Yes | Yes | A combined structure is required; this book develops its two core ingredients separately |

This table separates production structure from productivity change. A
Malmquist or Luenberger index asks how operating performance or best practice
changes between technologies. Dynamic SBM instead asks whether one complete
history is efficient relative to a technology of feasible histories. The
ratio of two annual or dynamic efficiency scores is not automatically a
productivity index.

Repeated static DEA, window DEA, and dynamic DEA therefore answer different
questions. Repeated static DEA treats each organization-period row as a
separate appraisal. Window DEA changes which rows may serve as comparators.
Neither imposes an accounting identity between what one period leaves and the
next period receives. If no defensible state variable exists, calling a panel
"dynamic" adds a label but not an economic mechanism.

The analysis below follows a **carry-over stock view**. Today's benchmark cannot
promise a closing stock of capacity, inventory, or backlog that is inconsistent with
what tomorrow's operation inherits. This is the appropriate question when management
must make a sequence of operating plans add up across time. A different established
question begins with **quasi-fixed inputs**, such as generation capacity or port
infrastructure, that cannot be moved immediately or costlessly to a desired long-run
level. That approach studies whether investment and input adjustment follow an
efficient path once adjustment costs and intertemporal substitution are recognized
{cite:p}`nemoto1999,nemoto2003`. A capital stock may appear in both approaches, but
the managerial commitments are different. A continuity identity does not by
itself specify investment costs, discounting, or an optimal speed of adjustment.
The carry-over model developed below answers the first question.

## Carry-over as a production commitment

Consider a hospital observed for four years. Each year it uses staff and beds
to provide treatment, and each year it leaves some patients on a waiting list.
The waiting list is not merely another annual input. Cases left unresolved in
year 1 become obligations in year 2. A benchmark that removes them from the
first year's target but lets the second year behave as though they were still
available is not an implementable management plan.

Other sectors have the same accounting logic. A manufacturer carries
productive capacity and warranty obligations; a bank carries performing and
non-performing loans; a university carries knowledge and degree candidates;
and an electricity utility carries generation capacity, fuel inventories, and
maintenance backlogs. In every case, the carry-over records a commitment that
connects current action with future opportunity.

The historical dynamic-SBM formulation uses four carry-over roles. They are
useful contracts between economic interpretation and benchmark treatment:

| Carry-over role | Economic and managerial meaning | Treatment in the benchmark account |
|---|---|---|
| **Good / desirable** | Capacity, knowledge, reputation, or another valuable inherited condition | A shortfall is assessed with output shortfalls |
| **Bad / undesirable** | Backlog, debt, defective work, or another future burden | An excess is assessed with input excesses |
| **Free / discretionary** | Inventory or another state that management may re-plan upward or downward | A signed deviation affects feasibility but does not enter the performance account used here |
| **Fixed / non-discretionary** | A regulated, contractual, or inherited commitment outside current control | The benchmark reproduces the observation |

```{figure} ../../_static/figures/dynamic-sbm-carryovers.svg
:name: fig-dynamic-dea-carryovers
:alt: Four annual management plans are connected by valuable capacity, harmful backlog, discretionary inventory, and fixed commitments, and the entire trajectory enters one performance account
:width: 100%

Carry-overs turn a sequence of annual plans into one operating history. What
the benchmark leaves at the end of one period must be the condition inherited
by the next benchmark plan.
```

The labels should not replace economic reasoning. "Good" and "bad" describe
how a state affects future production; "free" and "fixed" emphasize the scope
for managerial redesign. A fuel stock may be discretionary for a competitive
generator but effectively fixed during an emergency reserve obligation. A
loan portfolio may be valuable as earning capacity while some of its impaired
loans are harmful burdens. The analyst must explain the production role and
decision rights behind every declaration.

### Three tests for a defensible state account

A variable should enter the dynamic model only when it passes three practical
tests. First, it must have an **intertemporal identity**. The closing quantity
in one plan and the inherited quantity in the next must refer to the same
asset, obligation, or productive condition under the same measurement
boundary. "Investment spending this year" and "capital available next year"
may be related, but they are not automatically the same account. If investment
creates capital with a delay, loss, or depreciation rate, the study needs a
transition rule that represents that conversion rather than an equality
borrowed for convenience.

Second, the state must have **production relevance**. Its level must change
what the organization can deliver or what burden it must carry. A variable
recorded in several years is not a carry-over merely because it is persistent.
Regional population, weather, or market conditions may instead describe the
operating environment. Treating them as stocks controlled by management would
confuse inherited production capacity with external circumstances.

Third, its role must match **managerial responsibility**. A maintenance
backlog may be harmful and partly controllable, while a legally mandated
service obligation may be harmful to a narrow cost account but fixed for the
manager being assessed. The classification should reflect the decision level
of the study. A board, a plant manager, and a regulator can face different
control sets even when they observe the same physical quantity.

These tests also guard against double counting. If capital stock is a
carry-over, recording the same stock again as an ordinary annual input can
penalize one condition twice unless the production interpretation clearly
distinguishes capital services from the inherited asset. Similarly, a
waiting-list stock should not also be counted as an annual undesirable output
without explaining how the flow of newly unresolved cases differs from the
closing balance. Dynamic DEA does not remove the need for production
accounting; it makes inconsistencies in that accounting more consequential.

The horizon is part of the state definition. A three-year review may be
appropriate for a service contract but too short for an infrastructure asset.
Beginning the horizon immediately after an unusually large investment, or
ending it just before a backlog must be cleared, can change the apparent
trajectory. Analysts should therefore justify the initial and terminal dates
and examine whether conclusions survive a reasonable alternative horizon.

## One peer plan per period, one feasible trajectory

Suppose $n$ organizations are observed in periods $t=1,\ldots,T$. In period
$t$, $X_t$ contains ordinary inputs, $Y_t$ contains desirable outputs, and
$\lambda^t\in\mathbb{R}_+^n$ selects a peer plan from the cohort of complete
trajectories. For the organization $o$ under review,

$$
x_{ot}=X_t\lambda^t+s_{ot}^{-},
\qquad
y_{ot}=Y_t\lambda^t-s_{ot}^{+}.
$$

The input slack is avoidable resource use relative to the selected period
plan. The output slack is an attainable service shortfall. These balances make
each period feasible on its own, but they do not yet make the periods a
feasible history.

Let $C_t^\alpha$ contain a carry-over account of role $\alpha$. Using $C$ for
states keeps them distinct from within-period network links, which will later
use $Z$. The four period balances are

$$
\begin{aligned}
c_{ot}^{\mathrm{good}}
  &=C_t^{\mathrm{good}}\lambda^t-s_{ot}^{\mathrm{good}},\\
c_{ot}^{\mathrm{bad}}
  &=C_t^{\mathrm{bad}}\lambda^t+s_{ot}^{\mathrm{bad}},\\
c_{ot}^{\mathrm{free}}
  &=C_t^{\mathrm{free}}\lambda^t+s_{ot}^{\mathrm{free}},\\
c_{ot}^{\mathrm{fixed}}
  &=C_t^{\mathrm{fixed}}\lambda^t.
\end{aligned}
$$

Good- and bad-carry-over slacks are nonnegative. The free-carry-over slack is
signed because management may choose a target above or below the observation.
A fixed carry-over has no slack: the appraisal conditions on the observed
commitment.

The equation that turns these accounts into dynamic production is

$$
C_t^\alpha\lambda^t
=
C_t^\alpha\lambda^{t+1},
\qquad t=1,\ldots,T-1.
$$

Both sides refer to the same transition account. In management language, the
target stock leaving period $t$ equals the stock inherited by the next
benchmark plan. The equation does not say that the organization's observed
stock must remain unchanged. It says that any redesigned path must still be a
path rather than a collection of incompatible annual targets.

Under variable returns to scale, each period has its own convexity condition,

$$
\mathbf 1^\top\lambda^t=1,
\qquad t=1,\ldots,T.
$$

Under constant returns to scale these conditions are omitted. A single
horizon-wide convexity equation would not be equivalent, because every period
has its own peer plan.

```{admonition} The horizon needs an explicit boundary
:class: note

The terminal-period carry-over can enter its period performance account even
though no continuity equation leads to an unobserved period $T+1$. This does
not assign a salvage value, force the terminal stock to zero, or make it
disappear. Studies requiring depreciation, initial stocks, terminal value, or
longer lags need explicitly different transition equations.
```

## The trajectory performance account

Dynamic SBM does more than check whether a history is feasible. It asks how
much avoidable burden and attainable shortfall remain in that history. Let
$m$ be the number of ordinary inputs, $q$ the number of desirable outputs,
$h_b$ the number of bad carry-overs, and $h_g$ the number of good
carry-overs. With equal importance within each account, define

$$
\begin{aligned}
A_{ot}
&=
1-\frac{1}{m+h_b}
\left[
\sum_i\frac{s_{iot}^{-}}{x_{iot}}
+\sum_{v\in\mathcal C_b}
  \frac{s_{vot}^{\mathrm{bad}}}{c_{vot}^{\mathrm{bad}}}
\right],\\
B_{ot}
&=
1+\frac{1}{q+h_g}
\left[
\sum_r\frac{s_{rot}^{+}}{y_{rot}}
+\sum_{v\in\mathcal C_g}
  \frac{s_{vot}^{\mathrm{good}}}{c_{vot}^{\mathrm{good}}}
\right].
\end{aligned}
$$

$A_{ot}$ is a retained-resource account: it falls when the selected plan
reveals avoidable inputs or harmful inherited burdens. $B_{ot}$ is an
output-expansion account: it rises when desirable services or valuable future
conditions fall short of attainable targets.

Let $\omega_t\geq0$ denote declared period importance, normalized so that
$\sum_t\omega_t=1$. The horizon accounts are

$$
A_o=\sum_t\omega_t A_{ot},
\qquad
B_o=\sum_t\omega_t B_{ot}.
$$

The three orientations correspond to three management mandates:

```{list-table}
:header-rows: 1
:widths: 18 60 22

* - Orientation
  - Question
  - Reported trajectory efficiency
* - Input
  - How much ordinary resource use and harmful inherited burden can be avoided
    while commitments are respected?
  - $A_o$
* - Output
  - How much service and valuable inherited capability can be expanded?
  - $1/B_o$
* - Non-oriented
  - What joint resource and result improvement is attainable?
  - $\rho_o=A_o/B_o$
```

Because $B_o$ aggregates expansion accounts, output efficiency is a weighted
harmonic aggregation of period efficiencies $1/B_{ot}$, not their arithmetic
mean. Replacing it with a convenient average changes the measure.

Period weights are management judgments, not prices learned by DEA and not
automatically discount factors. If recent service reliability receives more
weight than an early transition year, the study should state why. Variable
weights within the input and output accounts have the same status: they express
declared importance and require sensitivity analysis.

The horizon score is the result of one joint optimization. Period scores,
slacks, targets, and peers explain one selected optimal trajectory. If several
trajectories attain the same horizon score, these lower-level explanations may
differ. A statement such as "year 3 caused the
inefficiency" is therefore stronger than the evidence. The defensible reading
is: under this jointly optimal plan, the selected diagnosis locates a stated
shortfall in year 3.

## When capacity and backlog enter the same account

A two-organization case makes the management meaning of the two carry-over
roles concrete. `dynamic_capacity_backlog` follows a Prepared organization and
a Strained organization over two periods. They use the same ordinary input and
produce the same ordinary output. What distinguishes them is their operating
position at the end of each period: capacity is valuable for what the
organization can do next, whereas backlog is a burden inherited by the next
managerial period.

| Period | Organization | Ordinary resource | Desirable service | Capacity | Backlog |
|---:|---|---:|---:|---:|---:|
| 1 | Prepared | 1 | 1 | 2 | 1 |
| 1 | Strained | 1 | 1 | 1 | 2 |
| 2 | Prepared | 1 | 1 | 2 | 1 |
| 2 | Strained | 1 | 1 | 1 | 2 |

Both state variables belong to the same fitted history. Capacity is declared a
good carry-over because a shortfall weakens the future operating position;
backlog is declared a bad carry-over because an excess passes an avoidable
burden forward.

```python
from deapack import (
    CarryOverSpec,
    DynamicData,
    DynamicSBM,
    DynamicSBMSpec,
    PeriodProductionSpec,
    dataset_info,
    dataset_info,
    load_dataset,
)

dataset_name = "dynamic_capacity_backlog"
frame = load_dataset(dataset_name)
roles = dataset_info(dataset_name).roles
spec = DynamicSBMSpec(
    production=PeriodProductionSpec(
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    ),
    carryovers=(
        CarryOverSpec(roles["good_carryovers"][0], kind="good"),
        CarryOverSpec(roles["bad_carryovers"][0], kind="bad"),
    ),
)
data = DynamicData.from_frame(
    frame,
    spec=spec,
    dmu=roles["dmu"],
    period=roles["period"],
)

result = DynamicSBM(
    orientation="non-oriented",
    returns_to_scale="vrs",
).fit(data)

result.summary()[
    [
        "dmu_id",
        "overall_input_account",
        "overall_output_expansion_account",
        "efficiency",
    ]
]
```

| Organization | Retained-resource account $A_o$ | Output-expansion account $B_o$ | Trajectory efficiency $A_o/B_o$ |
|---|---:|---:|---:|
| Prepared | 1.00 | 1.00 | 1.00 |
| Strained | 0.75 | 1.50 | 0.50 |

The Strained organization's selected plan leaves its ordinary input and output
unchanged, raises capacity from 1 to 2, and reduces backlog from 2 to 1 in each
period. Its two period accounts can therefore be reconstructed without a
black-box calculation. With one ordinary input and one bad carry-over,

$$
A_{ot}
=1-\frac{1}{2}\left(\frac{0}{1}+\frac{1}{2}\right)
=0.75.
$$

With one desirable output and one good carry-over,

$$
B_{ot}
=1+\frac{1}{2}\left(\frac{0}{1}+\frac{1}{1}\right)
=1.50,
\qquad
\rho_{ot}=\frac{0.75}{1.50}=0.50.
$$

Equal period importance preserves those same accounts over the two-period
horizon, so $A_o=0.75$, $B_o=1.50$, and $\rho_o=0.50$. Economically, the result
does not say that ordinary production was poor: the two organizations used the
same current resources for the same current service. It says that Strained
ended each period with less useful capacity and more unresolved work than the
represented benchmark history. Improving only today's flow measures would
miss both consequences passed to tomorrow.

The fitted result can display one of those state variables while retaining the
complete performance account:

```python
scored_trajectory = result.plot(
    kind="trajectory",
    dmu_id="Strained",
    variable="backlog",
)
```

```{figure} ../../_static/figures/dynamic-sbm-scored-backlog-result.svg
:name: fig-dynamic-sbm-scored-backlog-result
:alt: The Strained organization's observed backlog is two in both periods and its selected outgoing and inherited target is one; the lower panel reports a period efficiency of one half and a horizon efficiency of one half from the complete scored operating-plan account

One selected plan for the Strained organization. The upper panel follows
backlog in its original units: the selected outgoing target of 1 becomes the
inherited target in period 2. The lower bars are the **complete period
operating-plan account**, combining ordinary inputs and outputs with both the
capacity shortfall and the backlog excess. They are not a backlog attribution,
a causal decomposition, or evidence that backlog alone produced the score of
0.50. The selected targets are benchmark-supported possibilities, not uniquely
optimal management prescriptions.
```

## A project-authored case: following the commitment, not just the score

The `dynamic_carryover_portfolio` dataset contains four neutral service paths
observed over three periods. Each path has an operating input, a service
output, and a free carry-over used to close the interperiod plan. It offers a
small laboratory for the difference between annual comparison and trajectory
management without reproducing a published table.

```python
from deapack import (
    CarryOverSpec,
    DynamicData,
    DynamicSBM,
    DynamicSBMSpec,
    PeriodProductionSpec,
    dataset_info,
    load_dataset,
)

dataset_name = "dynamic_carryover_portfolio"
frame = load_dataset(dataset_name)
roles = dataset_info(dataset_name).roles
spec = DynamicSBMSpec(
    production=PeriodProductionSpec(
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    ),
    carryovers=(
        CarryOverSpec(roles["free_carryovers"][0], kind="free"),
    ),
)
data = DynamicData.from_frame(
    frame,
    spec=spec,
    dmu=roles["dmu"],
    period=roles["period"],
)

result = DynamicSBM(
    orientation="input",
    returns_to_scale="crs",
).fit(data)

result.summary()[["dmu_id", "efficiency"]]
```

The summary distinguishes complete-horizon performance from its period
accounts. The fitted result can turn the same evidence into one auditable
management picture:

```python
trajectory = result.plot(
    kind="trajectory",
    dmu_id="path_04",
    variable=roles["free_carryovers"][0],
)
```

```{figure} ../../_static/figures/carryover-portfolio-trajectory-result.svg
:name: fig-dynamic-sbm-trajectory-result
:alt: A project service path's observed and selected free carry-over values are connected across three periods, with a separate panel for period operating-plan accounts and the horizon result

One selected horizon plan for a project-authored service path. The upper panel distinguishes
what the organization actually carried, what the fitted plan leaves at the end
of each period, and what the next period inherits. The lower panel reports the
complete period operating-plan account from the jointly selected plan; it is
not an attribution to the carry-over displayed above. Its horizon line is the
model's intertemporal result, not an arithmetic average imposed by the chart.
```

The targets are not unrelated annual recommendations. Every selected outgoing
carry-over must equal the quantity inherited by the next period; the final
period has no invented successor. In this input-oriented specification the
free carry-over coordinates the feasible path but does not enter the reported
score. The figure reads that distinction from the fitted result rather than
guessing from a variable name. That implementable path is the evidence an
average of annual scores cannot supply.

The trajectory is economically coherent only when the horizon and period
plans are feasible and every outgoing carry-over target equals the quantity
inherited by the next period within numerical tolerance. A broken carry-over
chain cannot support an intertemporal recommendation. Detailed numerical and
reconstruction checks are available in the DEAPack Documentation.

The computation should preserve this distinction in two linked accounts. A
period account shows where the selected trajectory contains avoidable burdens;
a carry-over account places the outgoing and inherited targets side by side so
that their agreement can be checked. A credible report should present the
trajectory score, the economically important targets, and any material failure
of the production or continuity balances.

The sequence from score to action matters. Begin with the horizon result,
because that is what the model optimizes. Next inspect the period accounts to
locate when the selected plan finds avoidable burdens. Then read targets in
their original units: a recommendation to reduce a backlog by 200 cases is
more useful to management than its normalized slack alone. Finally inspect the
peer intensities and residuals. Peers show which complete histories support
the target, while residuals establish that the reported history really closes
its intertemporal accounts.

Sensitivity analysis should follow the same economic order. Reconsider the
carry-over role when decision rights are uncertain; vary period importance
when the planning mandate does not establish unique weights; and compare CRS
with VRS when scale assumptions are contestable. Ranking stability under
extra decimal places is not a substitute for these specification checks. The
main uncertainty in a dynamic study often lies in what the state means, not in
the last decimal place of the computed optimum.

```{admonition} When both processes and periods matter
:class: note

Some organizations require both within-period process coordination and
between-period carry-over continuity. That intersection is developed in the
package Documentation rather than as another core model here. The intertemporal
requirement remains the same: today's selected operating plan and tomorrow's
selected plan must agree about every inherited state.
```

## What the result can and cannot claim

A dynamic efficiency score supports a specific economic statement: relative
to the declared cohort, returns-to-scale assumption, carry-over roles,
weights, and horizon boundary, the organization's complete trajectory has a
stated amount of avoidable burden or attainable result. The score becomes
managerially useful when its targets describe commitments that could actually
be implemented.

It does not show that a low-scoring period caused the system shortfall. It does
not value future stocks unless a valuation model has been supplied. It does
not turn missing histories into valid transitions, and it does not measure
productivity growth. Productivity analysis requires explicit cross-period
technologies and an index identity; ordinary panel analysis requires an
explicit policy for which observations may benchmark which others.

The practical discipline is simple. First identify what today's plan leaves
for tomorrow. Then decide whether that state is valuable, burdensome,
redesignable, or fixed. Only after those economic commitments are declared
should the analyst estimate the frontier. When current performance can be
purchased by weakening the future operating position, the trajectory---not
the annual row---is the meaningful unit of appraisal.
