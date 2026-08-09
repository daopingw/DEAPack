# Communicating performance results

A DEA table is the audit record; a figure helps readers see the operational
pattern in that record. DEAPack therefore plots directly from `DEAResult` and
keeps the fitted method, reference policy, solver status, and reported
efficiency classification attached to the display.

Visualization is optional. Install the Matplotlib backend with:

```bash
python -m pip install 'DEAPack[viz]'
```

The numerical package does not import Matplotlib when a model is fitted or
when plots are discovered. This keeps numerical-only installations light and
lets automated analyses inspect the visualization contract without a graphics
backend.

## Discover what is available

```python
result.available_plots()
```

This returns immutable `PlotInfo` descriptions for plots that can be
constructed faithfully from this particular result. The `performance` kind
provides `points`, `ecdf`, and `auto` views. A result advertises it only when
at least one declared performance measure has a valid finite value from an
optimal solve. Here *valid* means that any measure-specific certification
status and row-level `score_valid` or `score_status` evidence admit the value
to the substantive layer.

The `frontier` kind is narrower. It is advertised for one-input/one-output
CRS or VRS `static.radial` results that retain slack-completed targets. It
uses those fitted target and peer accounts rather than reconstructing a
frontier from a score column. Discovery itself does not require Matplotlib.

The `trajectory` kind is narrower still. It is advertised only when the
classic Tone--Tsutsui Dynamic SBM result contains a certified horizon score,
period accounts, target rows, carry-over links, and explicit score-inclusion
rows. It does not infer dynamic production from a generic panel or repeated
static scores.

The `process` kind is source-specific for the same reason. Its first contract
is advertised only for a certified, input-oriented Tone--Tsutsui Network SBM
with classic fixed/free links. It reconstructs the declared-weight process
account and every internal handoff before rendering. System-radial,
relational, additive, output-oriented, non-oriented, and accountable-link
results keep their own reporting institutions; the plotting layer does not
translate them into input-oriented SBM language.

The `improvement` kind has four deliberately separate preparation contracts.
The radial branch separates the common input or output factor from its
optional Pareto--Koopmans completion. The SBM branch is the variable-level
companion to the three classic static orientations and the exact separable
strong-disposal environmental SBM. A third branch reads the certified
operating programme of ordinary static DDF. The fourth reads the certified
programme of the core CRS common-factor weak-disposal environmental DDF. All
keep resources, desirable services, and undesirable residuals in their
original units, but the radial, SBM, and two directional accounts retain their
own scores and sign conventions. Additive, RAM, range-directional,
non-separable environmental SBM, Network, Dynamic, and specialized results
retain their own reporting institutions.

The `metafrontier` kind is restricted to the certified classic radial
group/metafrontier decomposition. It joins each organization's efficiency
against its declared-group frontier to its efficiency against the pooled
metafrontier and reports the matching metatechnology ratio (MTR). It does not
reinterpret a generic grouped result, an SBM result, or a productivity result
as though it had the same decomposition.

The `references` kind summarizes which organizations appear in the certified
peer plans reported by a supported static DEA fit. It counts one reported
active peer edge when its intensity is strictly above the source result's
`peer_tolerance`; it does not add intensity magnitudes. Self-reference and use
by other organizations remain separate, because they answer different
management questions. This is evidence about one solver-selected collection
of peer plans, not an enumeration of alternate optima or a claim about the
exact mathematical support of the technology.

The lower-level `deapack.visualization.available_plots()` call, with no result
argument, lists registered plot kinds only. It is useful for interface
discovery, but it does not promise that a particular result contains the
measures needed by every listed kind.

## Plot the measure that answers the question

```python
figure = result.plot(
    kind="performance",
    theme="deapack",
    view="auto",
)
figure.savefig("efficiency-performance.png", dpi=200, bbox_inches="tight")
```

`plot()` returns a Matplotlib `Figure` and does not display or save it. This
makes the same call usable in a notebook, a report pipeline, or a test.
When `metric` is omitted, DEAPack chooses the safest declared native measure
for that result. For example, it selects a weighted slack sum for the
classical additive model, the directional distance rather than a convenience
efficiency transform for DDF models, system efficiency for a network model, a
profit gap for the profit model, and productivity change for a Malmquist or
Luenberger result.

Pass `metric=...` when the study has more than one relevant account. The name
must identify a measure whose interpretation is declared by the result
contract:

- `efficiency` is the standardized higher-is-better measure when the fitted
  method defines one;
- `rdm_efficiency` is the source higher-is-better $1-\beta$ account for
  RDM. Its benchmark at one means no positive common range-directional
  improvement, not certified strong efficiency;
- `performance_index` is the higher-is-better EPI, CPI, or ECPI for the
  paper-specific Zhou--Ang--Wang non-CHP source preset, while
  `directional_nonradial_distance` is its lower-preferred raw opportunity
  measure because larger distance means more unrealized improvement;
- a method-specific field can be more informative, such as
  `technically_adjusted_capacity_utilization`;
- `profit_gap` and `nerlovian_inefficiency` are lower-is-better shortfall
  accounts with zero as their no-gap benchmark;
- `productivity_change` has a neutral value of one for multiplicative indexes
  and zero for additive indicators;
- the core Hicks--Moorsteen result additionally declares
  `output_quantity_index` and `input_quantity_index` as descriptive
  quantity-change measures with a no-change value of one. Above one means the
  named aggregate quantity increased; input growth is not relabelled as an
  improvement. The headline `productivity_change` remains the default;
- `score` is available only when metadata declares the native criterion and
  its direction.

For the ordinary Luenberger indicator, `productivity_change` is additive with
a neutral value of zero. Its measure axis is expressed in the absolute units
of the declared common programme, not in percentages and not as a ratio around
one. In the two-hospital example in {doc}`../analysis/luenberger`, values of 1
and 2 mean one and two additional treatment-batch programme units at unchanged
staff input; 2 does not mean “twice as productive.” The result can be plotted
directly with:

```python
figure = result.plot(
    kind="performance",
    metric="productivity_change",
    period=2021,
    view="points",
)
```

A Luenberger transition enters the substantive layer only when all four
directional-distance LPs and the complete additive account are certified.
The published row exposes `score_valid=True` and
`score_status="defined"`, and the common plot gate consumes the explicit
`score_valid` certificate. An uncertified distance or failed
$L=EC_L+TC_L$ reconstruction cannot be promoted by an `optimal` backend
label.

DEAPack never substitutes `score` when the requested metric is absent, and it
does not infer semantics from an arbitrary numeric column. Inspect
`result.available_plots()[0].measures` to see each available measure's label,
preferred direction, benchmark, criterion-specific classification field, and
any row-level validity contract.
The renderer also does not clip values to the interval from zero to one. This
is important for external results, super-efficiency values, expansion
factors, and other measures whose valid domain may extend beyond one. A
missing, non-numeric, or infinite metric value is omitted and counted in
the figure note. For a small unavailable set, the note also names the affected
organizations and states whether the selected measure's declared
solver/certification evidence is unavailable, the measure is undefined, or
the metric itself is missing or non-finite. The roster is bounded and reports
an exact overflow count; an unavailable row is never drawn at zero or promoted
to a diagnostic point. A finite value whose `score_valid` or `score_status`
evidence says that the measure is undefined is excluded from the substantive
layer. If no valid finite optimal value remains, plotting stops with a clear
error.

Common-reference productivity summaries may retain a `technical_change`
column solely as a compatibility alias for their source-native
`best_practice_change`. Result-bound plot discovery lists the source-native
component once. Existing code may still request the alias explicitly, but the
figure labels it **Best-Practice Change** rather than implying a distinct
technical-change account. Adjacent-period Malmquist, Malmquist--Luenberger,
and Luenberger results retain their genuine technical-change component and
label.

For Hicks--Moorsteen, a substantive point also requires the complete
eight-distance release account to be valid. An uncertified component LP or a
failed $HM=Q_y/Q_x$ reconstruction sets `score_valid=False`; the generic plot
cannot promote the row merely because a backend returned the word `optimal`.

## Points for individual units, a distribution for larger studies

With `view="auto"`, each panel uses:

- a ranked point plot for at most 50 finite observations; or
- an empirical cumulative distribution (ECDF) for more than 50.

The point view keeps DMU labels because managers can still inspect individual
units. The ECDF instead answers population questions: what share of units lies
at or below a given result, how dispersed performance is, and whether a small
tail drives the overall impression. Set `view="points"` or `view="ecdf"` when
the reporting purpose calls for a fixed presentation.

The plot reports observations; it does not manufacture classifications.
Only a measure's own declared classification field is used. Thus a capacity
utilization, profit-gap, or productivity plot does not inherit the generic
`is_efficient` flag merely because that column is present. When a relevant
classification is nullable, a missing value is labeled **Efficiency status
not reported** rather than being treated as efficient or inefficient.

Rows with a finite value but a non-optimal solver status remain visible as
grey crosses in a separate diagnostic layer. The same is true of finite
audit accounts that fail the result's explicit validity contract. Both are
excluded from the substantive ranking and from the ECDF. This preserves
evidence that a unit was attempted without allowing an uncertified or
economically undefined numerical value to alter the reported performance
distribution.

## Compare within-group performance with pooled opportunities

A radial metafrontier result has three linked quantities, so its dedicated
view is more informative than plotting the MTR alone:

```python
figure = result.plot(kind="metafrontier")
```

Each row represents one certified organization and retains its declared group.
The group-efficiency marker shows performance against opportunities represented
inside that group; the metafrontier-efficiency marker shows performance against
the pooled opportunity set. The connector identifies the two results as
belonging to the same organization; it is not itself a decomposition term.
The row annotation reports their ratio, the MTR. The figure therefore keeps
the identity

$$
E_o^M=E_o^G\times MTR_o
$$

visible without turning either component into a causal attribution of
management or operating environment.

For a multi-period panel, select exactly one reporting period:

```python
figure = result.plot(kind="metafrontier", period=2025)
```

The fitted metafrontier may still pool all study periods as its retrospective
reference technology; `period` selects the organization-period rows displayed,
not a new contemporaneous frontier. A cross-sectional result rejects `period`.
The dedicated view also rejects `metric`, `dmu_id`, and `variable`, and it
supports only `view="auto"`, because all three decomposition quantities belong
to the same reporting account.

Preparation checks the exact classic radial method identity, orientation, RTS,
pooled construction, time-information policy, component score certificates,
the fitted three-row component ledger, both phase-one diagnostic certificates,
nestedness, bounds, and the decomposition identity. Rows that do not claim a
certified decomposition are omitted and counted in the figure note. A row that
claims certification while lacking component evidence, disagrees with the
ledger, or fails the bounded identity causes the selected plot to fail closed.
If no certified row remains, no figure is produced.

The connected three-part view is intentionally limited to 60 certified
organizations. Above that limit, it fails closed instead of shrinking labels
or silently dropping rows; use the component-specific performance ECDFs or
tables for a larger study.

The generic performance plot remains available when the reporting question
concerns only one measure. For example:

```python
mtr_figure = result.plot(
    kind="performance",
    metric="metatechnology_ratio",
)
```

Use `group_efficiency` or `metafrontier_efficiency` instead when one of those
single indicators is the intended ranked-point or ECDF display. See
{doc}`../analysis/metafrontier` for the fitted production and reference-policy
contract.

## See which organizations are used as reported peers

A certified static result can turn its complete peer ledger into a compact
management account:

```python
figure = result.plot(kind="references")
```

Each bar counts how many evaluated organizations used the named organization
as a reported active peer. The bar separates self-reference from use by other
organizations, so an organization that benchmarks only itself is not confused
with one that repeatedly informs other operating plans. The corresponding
`reference_rate` is the total count divided by the number of evaluated
organizations; it is not an intensity share and need not sum to one across
potential references.

The account is deliberately narrow. It reads
`result.reference_frequency()`, verifies its source method, fitted
cross-section, certification, and peer-reporting threshold, and adds no solve.
It counts peer edges whose reported intensity is strictly greater than the
source result's `peer_tolerance`. It therefore describes one certified
solver-selected plan for every evaluated organization. It does not establish
that the selected plan is unique, enumerate alternative optima, identify a
global reference set, diagnose influential observations or outliers, or
provide statistical inference.

For readability, the figure draws at most 30 nonzero-frequency references,
ranked first by use by other organizations and then by total use. Its note
reports the number shown, the complete number of selected references, any
selected references omitted by the top-30 rule, every zero-frequency
potential reference not drawn, the active-edge count, and the fitted
threshold. Thus a compact figure does not silently turn an unshown
organization into missing data. Inspect the complete summary returned by
`result.reference_frequency()` when all organizations are needed.

`metric`, `period`, `dmu_id`, and `variable` remain omitted because the plot
uses the complete fitted cross-section and its peer account. Only
`view="auto"` is supported.

## Connect operating plans to their targets

For a scalar teaching case or a genuinely one-input/one-output study, the
frontier view joins each certified operating plan to its fitted DEA target:

```python
from deapack import DEAData, RadialDEA, dataset_info, load_dataset

frame = load_dataset("frontier_1x1")
roles = dataset_info("frontier_1x1").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
)
result = RadialDEA(
    orientation="input",
    returns_to_scale="vrs",
).fit(data)

figure = result.plot(kind="frontier")
```

Efficient observed operations form the displayed VRS frontier; a CRS result
instead shows its certified frontier ray. Arrows run from observed quantities
to the result's reported targets. They answer the fitted resource-saving or
service-expansion question and include the compatible slack-completion phase.
They are benchmark opportunities, not diagnoses of managerial effort and not
implementation orders.

The plot fails closed when any of the following would make the picture
misleading:

- the result is not the classical black-box `static.radial` method;
- there is more than one input or desirable output;
- RTS is neither CRS nor VRS;
- `compute_slacks=False`, so target and strong-efficiency accounts were not
  completed;
- active peers come from outside the selected comparison cross-section;
- the selected period has no optimal, finite, strongly certified target rows;
  or
- more than 200 organizations would make the all-unit target view unreadable.

For panel results, select one contemporaneous technology with
`result.plot(kind="frontier", period=...)`. The plot refuses to join
cross-period peers into a picture labeled as one period. `metric` remains
omitted because the axes are declared input and output quantities, not a
chosen result measure. Multidimensional studies should use performance plots,
target tables, peer accounts, or explicitly declared partial views rather
than presenting a two-dimensional projection as the complete frontier.

## Separate the radial factor from target completion

The existing `improvement` kind can read a certified ordinary radial result
without pretending that its final target is only the proportional point:

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

For C, phase one reports $\theta=1$: its resource cannot fall in a common
input-oriented contraction while service $0.5$ is protected. Phase two holds
that factor fixed and finds a service slack of $0.5$, so the selected completed
plan is resource $1$, service $1$. The figure therefore keeps

```text
observed operation -> phase-one radial target -> completed target
```

in separate columns. `score` and `is_radially_efficient` support the first
claim; `slacks`, `targets`, and `is_efficient` support the second. In this case
C is radially efficient and not strongly efficient. Under output orientation,
the same route reconstructs the native $\phi$ expansion first and then any
remaining input saving or output gain.

Preparation accepts only the exact ordinary `static.radial` family, supported
orientation and RTS semantics, a selected observation inside its reference
technology, and two certified solve phases under the declared
Pareto--Koopmans completion protocol. Every final target must reconstruct from
the native radial factor plus the public physical slack, and the physical and
maximum-slack ledger must agree with the summary. The detached original-unit
table does not republish per-variable scaled-slack magnitudes whose exact scale
also depends on the selected reference set's row maximum. Peer and dual
publication are not prerequisites because this plot displays neither claim.
Discovery and preparation consume only fitted result tables and add no solver
call.

The columns are accounting stages, not an implementation timetable. The
selected target is not claimed to be unique, closest, least-cost, causal, or a
management prescription.

## Read a multidimensional SBM plan without flattening it

Classic SBM is designed for variable-specific gaps, so its result view does
not force a multidimensional operation onto a two-dimensional frontier:

```python
from deapack import DEAData, SBM, dataset_info, load_dataset

frame = load_dataset("sbm_slack_contrast")
roles = dataset_info("sbm_slack_contrast").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
)
result = SBM(returns_to_scale="crs").fit(data)

figure = result.plot(
    kind="improvement",
    dmu_id="A",
)
```

The proportional panel answers where the selected plan locates resource
excesses and service shortfalls relative to the focal operation. The ledger
answers the operational follow-up: what current and selected benchmark
quantities generated those percentages? Rows can use different physical
units, so their original quantities remain separate rather than being added
on a common axis.

`InputSBM` colors only resource rows as part of the fitted performance
account; `OutputSBM` colors only service rows; joint `SBM` includes both.
Any hatched row is feasible in the solver-selected plan but was not valued by
that orientation's objective. A score of one under one orientation therefore
does not acquire a false strong-efficiency interpretation from the figure.

Preparation fails closed unless the exact classic method identity,
orientation, declared variable roles, summary validity, LP certificate,
economic certificate, target/slack identities, and score reconstruction all
agree. For panel data, add `period=...` when a DMU has more than one row.
`metric`, `variable`, and non-auto views are rejected because this display
reads the fitted operating ledger rather than choosing a generic numeric
column. The target remains one feasible solver-selected optimum, not a budget,
forecast, causal diagnosis, or unique recommendation.

### Add the undesirable residual without changing the plot kind

The exact separable environmental SBM uses the same call while preserving a
third variable role:

```python
import pandas as pd

from deapack import DEAData, UndesirableSBM

environmental_frame = pd.DataFrame(
    {
        "plant": ["A", "C"],
        "resource": [1.0, 2.0],
        "service": [2.0, 1.0],
        "residual": [1.0, 2.0],
    }
)
environmental_data = DEAData.from_frame(
    environmental_frame,
    dmu="plant",
    inputs="resource",
    outputs="service",
    bad_outputs="residual",
)
environmental_result = UndesirableSBM(
    returns_to_scale="vrs",
).fit(environmental_data)

figure = environmental_result.plot(
    kind="improvement",
    dmu_id="C",
)
```

Plant C's selected plan saves 50 percent of its resource, doubles its desirable
service, and reduces its undesirable residual by 50 percent. These remain
three distinct rows because their physical units are not additive. The
resource-retention factor is $1-1/2$, while the combined output expansion
factor is $1+3/4$; the figure therefore reconstructs
$2/7=(1-1/2)/(1+3/4)$ rather than presenting the score as a uniform reduction
rate.

This display is available only for the exact
`environmental.sbm.separable_strong` contract. Its lower-residual target is
conditional on independent bad-output contraction under the fitted separable,
strong-disposal technology. The selected row must have certified membership in
that reference technology and a valid certified primary-program target.
Membership may come from self inclusion or from the reconstructed balance of a
feasible external SBM appraisal; an outside or uncertified row is not drawn.
Peer and dual release remain independent because this figure displays neither.
The same `kind` continues to reject
non-separable and weak-disposal *SBM* specifications, Network SBM, and Dynamic
SBM. The common-factor weak-disposal DDF described later enters through its own
directional preparer rather than through this SBM account. A displayed gap is
not evidence of its cause, the residual bar is not a monetary damage valuation,
and the selected target is not claimed to be the unique optimal plan.

## Read one declared directional programme in original units

Ordinary DDF asks how much of one declared package of resource saving and
service expansion is jointly attainable. A scalar beta answers how many
package units fit; the operating ledger answers what that commitment means for
each recorded quantity:

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

figure = result.plot(
    kind="improvement",
    dmu_id="E",
)
```

For E, beta is 0.247253. Labor moves from 2.000000 to its declared-programme
target 1.505495, and capital moves from 2.800000 to 2.107692. Their completed
targets do not change further. Service first moves from 1.300000 to 1.621429
under `beta * direction`, then to 1.652747 after an additional 0.031319 slack.
Quality similarly moves from 0.620000 to 0.773297 and then to 0.830549 after
an additional 0.057253 slack. The display therefore keeps

```text
observed -> declared directional target -> slack-completed target
```

separate instead of calling the whole change a uniform 24.7 percent
adjustment. Each row retains its own physical unit; the renderer never adds
labor, capital, service, and quality on one quantity scale.

The route is exact to `static.directional_distance`, requires both fitted
phases and their public production accounts to certify, reconstructs every
directional move and slack-completed target, and performs no optimization.
Peer and dual publication are independent claims and are not required for
this target-only display. The selected target is conditional on the sample,
technology, direction, and completion rule. It is not evidence of why a gap
exists, a causal effect, a uniquely preferred plan, an implementation order,
or a least-cost recommendation.

## Read one common environmental programme in original units

The core common-factor environmental DDF answers a different management
question from SBM: how far can one declared programme ambition be raised while
resources contract as specified, desirable services expand, and undesirable
residuals fall? The same `improvement` call selects its independent DDF ledger:

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

figure = result.plot(
    kind="improvement",
    dmu_id="Central",
    period=2020,
)
```

For Central in 2020, the certified programme has
$\beta=0.083815$. Energy and labour are fixed by the declared zero input
direction. Electricity rises from 79.376 to 86.028902, a declared programme
move of 6.652902, while carbon dioxide falls from 285.120 to 261.222659, a
move of 23.897341. Each row is a separate original-unit ledger; the figure
does not place energy, labour, electricity, and carbon dioxide on a common
quantity axis. A zero observed coordinate is therefore safe and is labelled
as held fixed when its declared move is zero.

Beta is a common programme ambition, not an SBM slack ratio and not, for a
general direction, a percentage efficiency score. The result also retains
the convenience transform $1/(1+\beta)$, but the DDF improvement figure keeps
the native beta visible. The declared beta-scaled move and the subsequent
slack-completion adjustment occupy separate columns. Consequently, a resource
reduction found only in the completion phase is not misreported as part of
the declared programme.

Preparation accepts the family-level method
`environmental.ddf.weak_disposal.common_factor` and its exact equivalent CFG
source preset only. It verifies the joint black-box CRS common-factor
bad-output equality, declared roles and reference policy, a nonnegative
certified beta, certified membership of the assessed plan in the reference
technology, at least one positive direction component, the certified phase-one
and phase-two accounts, every public target/slack identity, and the summary
maximum-slack ledgers. `zeros`, `ones`,
and `observed` directions are checked directly. `mean`, `custom_global`, and
`custom_by_observation` policies are reconstructed in stable fitted-observation
order; custom values must reproduce their immutable expanded-spec numeric
fingerprints. Mixed or external reference policies are allowed when the
selected row has a certified nonnegative beta, target, and membership account.
For an equality-based external appraisal, that account may appear as an
additional phase-zero feasibility certificate. A negative cross-reference beta
or a positive beta for a plan outside the reference technology is not drawn as
an improvement.

Peer and dual publication are independent claims and are not prerequisites
for this target-ledger view. Plot discovery, preparation, and rendering read
the fitted result only and make no additional solver call; any required
membership programme has already run during model fitting. Discovery uses a
vector summary prefilter, and ordinary zero/one/observed directions do not
require copying the full fitted target table. The displayed
target is one selected feasible benchmark, not a unique plan, engineering
implementation, causal explanation, or cost conclusion.

Method-specific declarations also prevent familiar column names from erasing
the fitted question. Scale analysis defaults to `scale_efficiency` and its
own classification field. Only methods on the current public surface receive
a documented visualization recipe; deferred internal prototypes are not
presented as supported plotting workflows.

## Read one connected organization without breaking it into separate departments

An input-oriented Network-SBM result can turn one fitted organization into a
connected management account:

```python
figure = result.plot(
    kind="process",
    dmu_id="A",
)
```

The first panel locates normalized input burden in the process accounts from
one jointly feasible system optimum. These are not the efficiencies that the
departments would necessarily receive if each were evaluated alone. The
system panel makes the aggregation policy auditable by reconstructing

$$
E_o=\sum_k w_k E_o^k.
$$

The weights are the fitted result's declared governance weights; the figure
does not estimate new weights or reinterpret them as prices. A zero-weight
process remains visible as unscored because it can still constrain the joint
network plan without contributing to the reported objective.

The handoff ledger then returns to the original units of each internal flow.
It distinguishes observed quantities from selected common supplier--recipient
targets and labels every link as fixed or free. Different link variables are
not placed on one common numerical axis. A fixed target must preserve the
observed commitment. A free target may differ, but it belongs to one
solver-selected optimum and is neither uniqueness-certified nor automatically
an operational recommendation.

Preparation fails closed unless all of the following agree:

- the exact base method identity, input orientation, and fixed/free link
  institution;
- one valid summary row and one independent primary LP/economic certificate;
- the fitted process order, declared weights, process input accounts, and
  weighted system reconstruction;
- independent graph topology and one complete row for every declared
  link-variable pair;
- supplier--recipient continuity, fixed-observation commitments, and absence
  of accountable-link fields; and
- the fitted numerical tolerance, score status, attribution status, and target
  selection status.

For a panel network result, pass `period=...` together with `dmu_id`; omitting
the period when the same organization appears more than once is treated as an
ambiguous management account. `metric` and `variable` remain omitted because
the figure reads the model's system, process, and link tables rather than a
single score column.

The connected display is limited to 16 process accounts and 24 declared
link-variable accounts. A larger fitted network remains available through its
public component and link tables, but this figure fails closed rather than
compressing a governance account until process or handoff labels become
unreadable.

## Read one carry-over as an intertemporal commitment

A Dynamic-SBM trajectory joins what one period leaves to what the next period
inherits. Select one organization and one carry-over so unrelated quantities
in different units are not normalized onto a misleading common axis:

```python
figure = result.plot(
    kind="trajectory",
    dmu_id="E",
    variable="free_carryover",
)
```

The upper panel keeps three quantities distinct: the observed carry-over, the
selected outgoing target, and the value inherited from the preceding period.
Dashed arrows use the fitted `links` account to test each adjacent-period
handoff. They are not inferred by comparing neighboring rows in `targets`.
The final period has no successor, and the renderer leaves it that way.

The lower panel reports the complete period operating-plan account from the
one jointly optimized horizon. It combines every scored ordinary input,
ordinary output, good carry-over, and bad carry-over in that period. It is
therefore not a contribution assigned to the carry-over selected in the upper
panel: changing `variable=` changes the displayed path, but not this complete
account. The dashed horizon value comes directly from `summary()`;
it is labeled **not a period average** because output-oriented and
non-oriented Dynamic SBM use different intertemporal aggregation accounts.
For good, bad, and free carry-overs, the figure reads
`included_in_reported_score` from the selected carry-over's slack rows and
validates those flags against the source orientation, score variant, and slack
sign. A discretionary carry-over may coordinate feasibility without entering
the base score, while the source-qualified adjusted reporting variant treats
its signed deviation differently. A fixed carry-over has no discretionary
slack row; the plot represents it explicitly as a feasibility account that
does not enter the reported burden score.

Trajectory plotting fails closed unless all of the following agree:

- `score_valid=True`, a defined score, and an optimal backend status;
- the solver-neutral LP and dynamic economic-account certificates;
- the fitted `period_order` and numerical tolerance;
- one complete, nonduplicated target, period-component, and link account, plus
  either explicit slack-score rows or the source-defined no-slack fixed account;
- reconstruction of every period efficiency and the horizon result from the
  published input, output-expansion, and effective-weight accounts;
- agreement between each target's observed quantity and the corresponding link
  account;
- equality of each outgoing carry-over target and the next period's inherited
  value; and
- an explicit terminal-boundary row with no fabricated next period.

`period=...` is rejected because removing one year would break the horizon
account. The selected path is a certified solver-selected optimum, not a
uniqueness claim, causal explanation, or implementation order.

The trajectory view is limited to 24 fitted periods. A longer horizon fails
closed; the plotting layer does not sample years or visually compress away an
intertemporal commitment. Fit a declared shorter study horizon for this view,
or use the complete public period and link tables.

### RDM: choose the management-facing account explicitly

RDM retains both the native feasible improvement share `beta` and the
higher-is-better `rdm_efficiency = 1 - beta`. The native beta can remain the
default because it is the estimator's direct optimization result. For a
management-facing efficiency display, name the complementary account:

```python
from deapack import DEAData, RDM, dataset_info, load_dataset

frame = load_dataset("range_directional_signed")
roles = dataset_info("range_directional_signed").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
)
result = RDM().fit(data)

figure = result.plot(metric="rdm_efficiency")
```

The RDM measure specification intentionally has no classification column.
An RDM efficiency of one exhausts the common focal-to-ideal direction but
does not rule out residual or non-proportional improvement. The plot
therefore shows reported values without marking them strongly efficient.

## Periods are compared deliberately

For panel data, omit `period` to create one panel per period when the result
contains no more than four periods:

```python
figure = result.plot(metric="efficiency")
```

When there are more than four periods, select one explicitly:

```python
figure = result.plot(metric="efficiency", period=2025)
```

The four-panel limit prevents a dashboard from becoming an unreadable wall of
small plots. Selecting a period filters the result before the automatic
point-versus-ECDF rule is applied. For change over time, use the appropriate
productivity or change measure rather than interpreting separate efficiency
panels as a productivity index.

For a genuine change result, `period=` continues to select the comparison
period. If every selected row records one complete and coherent
`base_period`--`comparison_period` pair, the panel title displays that pair as
`base → comparison`. A partial pair, a mixture of base periods, a
comparison period inconsistent with the selected facet, or a same-period pair
falls back to the ordinary period title. The plotting layer does not infer a
transition that the result table cannot prove.

## Reading the figure responsibly

A performance plot is a comparative summary under the fitted study design. A
low result can motivate investigation, but the figure alone does not identify
managerial effort, causal responsibility, an implementable target, or the
economic desirability of change. Before circulating it, check the reference
population, input and output definitions, time window, orientation or
direction, returns-to-scale assumption, and solver diagnostics retained in
the result.

The figure footer carries available provenance from the result metadata,
including the method, orientation, returns to scale, and reference design.
That provenance is a compact reminder, not a substitute for reporting the
full fitted specification.

See the {doc}`../api/visualization` for exact method signatures and exception
types.
