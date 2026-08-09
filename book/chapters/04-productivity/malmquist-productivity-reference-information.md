# Malmquist Productivity and Reference Information

A hospital can be efficient in every year and still fail to improve its productivity.
Another hospital can remain behind the leaders yet make substantial progress. These
statements are not contradictory. Efficiency describes an organization's position
relative to a benchmark at one point in time; productivity change asks whether its
input--output performance improved between two points in time. Managers need both
pieces of information because they lead to different conversations. A persistent
operating shortfall calls for attention to implementation, while a change in the
sector's best-observed possibilities raises questions about investment, organization,
regulation, and the diffusion of practice.

The Malmquist family provides a disciplined way to organize that conversation. It
compares the same producer in two periods and uses DEA technologies to distinguish a
change in benchmark-relative operating performance from a change in the production
opportunities visible in the data. Caves, Christensen, and Diewert developed the
distance-function foundation of the index {cite:p}`caves1982b`; Färe, Grosskopf,
Norris, and Zhang established the widely used output-oriented constant-returns DEA
formulation {cite:p}`fare1994`.

One decision runs through every Malmquist study: **which observations are allowed to
define the benchmark for each comparison?** The conventional adjacent-period index
uses the two contemporaneous technologies. A global index uses one common technology
built from the full study horizon. These are best understood as two reference-
information policies within the same productivity family. They answer closely related
questions, but the evidence available to the evaluator—and therefore the meaning of
the result—is different.

```{figure} ../../_static/figures/productivity-frontier-motion.svg
:name: fig-merged-malmquist-frontier-motion
:alt: Productivity change divided into a change in benchmark-relative operating performance and a change in best-observed production opportunities
:width: 95%

A productivity result has two distinct managerial readings. One concerns how fully
an organization realizes the opportunities available in its own period. The other
concerns whether the study's best-observed opportunities have become more or less
favorable. Neither component, by itself, identifies the cause of change.
```

## Is a high efficiency score the same as productivity growth?

No. Consider a clinic that lies on the estimated best-practice benchmark in both 2024
and 2025. Its contemporaneous efficiency score is one in both years. If the 2025
benchmark permits more treatments from the same resources, the clinic has nevertheless
experienced productivity growth. Conversely, a clinic can reduce its shortfall from
best practice while the sector's observed opportunities deteriorate. Its
operating performance improves relative to its peers, but its overall productivity
need not rise.

To keep the two dates in a cross-period comparison distinct, let
$z^\sigma=(x^\sigma,y^\sigma)$ denote the organization's operating plan in period
$\sigma$, and let $\mathcal T^\tau$ denote the production possibilities supported by
the observations admitted to reference period $\tau$. The appraisal
$d^\tau(z^\sigma)$ therefore asks how the plan actually operated in period $\sigma$
would perform when judged by the opportunities documented in period $\tau$.
DEAPack uses a common direction for reporting radial performance:

- under input orientation, $d^\tau(z^\sigma)$ is the Farrell input-contraction factor
  $\theta$;
- under output orientation, it is the reciprocal, $1/\phi$, of the Farrell
  output-expansion factor.

For an observation assessed against a technology that contains it,
$0<d^\tau(z^\sigma)\leq1$, and one indicates radial efficiency. This convention
makes the interpretation of change consistent: a ratio above one records improvement. The
reciprocal convention is also common in the literature, so an empirical paper must
state its distance direction before numerical results can be compared.

A static distance is an efficiency level. A Malmquist index is a ratio of distances
and therefore a change measure. It has no meaningful static “efficient or inefficient”
classification of its own. The neutral value is one: an index above one indicates
measured productivity growth, one indicates no change, and a value below one indicates
measured decline.

## Whose best practice is used to judge the two operating plans?

The conventional adjacent-period Malmquist index gives both neighboring periods a
voice. The organization has two observed plans, $z^t$ and $z^{t+1}$, and the study has
two contemporaneous technologies, $\mathcal T^t$ and $\mathcal T^{t+1}$. Four
benchmark evaluations are therefore required.

```{figure} ../../_static/figures/four-distance-matrix.svg
:name: fig-merged-malmquist-four-evaluations
:alt: Four evaluations created by assessing each of two operating plans against each of two contemporaneous reference technologies
:width: 90%

The four appraisals behind the adjacent-period index. The two own-period evaluations
describe contemporaneous operating performance. The two cross-period evaluations make
it possible to separate that performance from a change in best-observed opportunities.
```

| Evaluation | Economic question |
|---|---|
| $d^t(z^t)$ | How fully did the organization realize the opportunities documented in the base period? |
| $d^{t+1}(z^{t+1})$ | How fully did it realize the opportunities documented in the comparison period? |
| $d^t(z^{t+1})$ | How would the later operating plan be judged using the earlier information set? |
| $d^{t+1}(z^t)$ | How would the earlier operating plan be judged using the later information set? |

Holding the base-period technology fixed produces one assessment of productivity
change:

$$
M^t(z^t,z^{t+1})
=\frac{d^t(z^{t+1})}{d^t(z^t)}.
$$

Holding the comparison-period technology fixed produces another:

$$
M^{t+1}(z^t,z^{t+1})
=\frac{d^{t+1}(z^{t+1})}{d^{t+1}(z^t)}.
$$

Neither year is automatically the more legitimate judge. The conventional index gives
the two assessments equal proportional weight through their geometric mean:

$$
M^{t,t+1}
=\left[
\frac{d^t(z^{t+1})}{d^t(z^t)}
\frac{d^{t+1}(z^{t+1})}{d^{t+1}(z^t)}
\right]^{1/2}.
$$

The geometric mean is part of the economic comparison, not a device for hiding two
disagreeing results. Analysts should inspect the underlying evaluations when the
overall index is surprising. A marked difference between the two fixed-benchmark
ratios often signals substantial change in the reference opportunities, weak overlap
between the period samples, or an influential observation.

## Did the organization improve, or did best-observed opportunities change?

The classic two-part decomposition divides measured productivity change into efficiency
change and technical change. Efficiency change is

$$
EC^{t,t+1}
=\frac{d^{t+1}(z^{t+1})}{d^t(z^t)}.
$$

It compares how fully the organization realizes the production opportunities
available in its own period. When $EC>1$, the measured operating shortfall has narrowed
relative to contemporaneous best practice; when $EC<1$, it has widened.
The traditional word *catch-up* describes this change in relative performance, but should not be mistaken for an explanation
of the organizational process that produced it. Better scheduling, staff learning,
lower downtime, a changed case mix, revised records, or a different comparison population
could all move the component. DEA alone cannot decide among them; distinguishing the
explanations requires operational and causal evidence.

The remaining component is conventionally called technical change:

$$
TC^{t,t+1}
=\left[
\frac{d^t(z^{t+1})}{d^{t+1}(z^{t+1})}
\frac{d^t(z^t)}{d^{t+1}(z^t)}
\right]^{1/2}.
$$

It describes whether the best observed combinations of resources and outputs became
more favorable around the organization's two operating plans. A value above one means
that comparable organizations demonstrated an improved production opportunity for
this comparison. It does not show that every service line advanced, nor does it prove
invention or technology adoption. New equipment, regulation, demand conditions,
organizational redesign, data coverage, and sampling variation can all influence the
estimated component.

The qualification “for this comparison” matters. Production opportunities can improve
for one service mix while remaining unchanged, or even becoming less favorable, for
another. A hospital specializing in elective procedures and an emergency hospital may
therefore receive different opportunity-change factors from the same pair of annual
technologies. The component is evaluated around each organization's operating plans;
it is not a single sector-wide rate that can be attached to every producer. A group
summary should preserve that heterogeneity rather than describe the mean component as
if the entire frontier had shifted uniformly.

Nor does an average of organization-level indexes automatically become an industry
productivity measure. An industry account must say how organizations are weighted and
how entry, exit, and movements of activity or resources among them are treated. Under
such an account, shifting activity toward more productive organizations can contribute
to industry productivity even when it is not an improvement within any one continuing
organization. The indexes in this chapter describe organization-level change; their
mean does not separately identify that reallocation contribution
{cite:p}`foster2001aggregate`.

For the classic output-oriented constant-returns construction, the account closes
exactly:

$$
M^{t,t+1}=EC^{t,t+1}\,TC^{t,t+1}.
$$

This identity is useful both substantively and computationally. It tells the reader
how the overall change is allocated and gives the analyst a basic audit: the reported
components should reconstruct the index before rounding. The two factors are an
accounting decomposition, not estimates of separate causal effects. In particular,
$EC$ should not be relabelled “management quality,” and $TC$ should not be relabelled
“innovation” without independent evidence.

Nor does this two-part account contain an implicit decomposition of scale, input mix,
output mix, or allocative performance. Those are different economic questions that
require additional definitions and maintained assumptions. A variable-returns run is
informative as a sensitivity analysis, but it does not automatically turn the two
components above into a complete scale-and-mix ledger.

## What if one period's benchmark cannot assess the other period's plan?

The two cross-period evaluations ask demanding counterfactual questions. An operating
plan observed in 2025 is not necessarily reproducible within the opportunities
represented by the 2024 sample, and the reverse comparison can also be problematic.
A cross-period efficiency-form distance may exceed one because the evaluated plan
outperforms the comparison technology. Under some non-constant-returns or otherwise
restricted empirical technologies, the linear program may instead be infeasible.
These outcomes reveal something about the comparison; they are not interchangeable
with numerical failure.

An analyst should not replace a missing cross-period evaluation with whichever
one-sided ratio happens to be available. Doing so silently defines a different index
and destroys the stated two-benchmark account. The defensible responses are to report
the affected transition, reconsider whether the period technologies and data are
comparable, or adopt a different reference-information policy for a reason stated in
advance.

This is where the global policy becomes useful. It avoids direct “new plan against old
technology” and “old plan against new technology” programs by evaluating both plans
against one encompassing information set. That advantage changes the question being
asked; it is not a numerical repair applied only to inconvenient rows.

## Should all years share one retrospective benchmark?

For a long-horizon assessment, a ministry or corporate group may want every year's
performance expressed against the same body of observed opportunities. This is a
change in the **reference-information policy**, not a new substantive theory of
productivity. Let $\mathcal T^G$ be the common technology formed from all observations
in a declared study horizon {cite:p}`pastor2005`, and let $d^G(z)$ be the corresponding
efficiency-form distance. “Global” here means full-sample across time. It does not mean
a universal technology beyond the population and years in the dataset.

```{figure} ../../_static/figures/reference-technology-windows.svg
:name: fig-merged-malmquist-reference-information
:alt: Contemporaneous period-specific and full-horizon global reference information policies across three periods
:width: 95%

Reference technologies encode an information policy. A contemporaneous benchmark uses
only practices observed in one period. A global benchmark admits the complete study
horizon. The choice determines which observed practices can define best practice and
therefore what the measured change means.
```

With one common benchmark, the sensitivity comparison is a direct ratio:

$$
GM^{t,t+1}=\frac{d^G(z^{t+1})}{d^G(z^t)}.
$$

The direction is unchanged: $GM>1$ indicates improvement. Because the same information
set judges both plans, no geometric mean across two annual technologies is needed.
The common reference also avoids asking whether the later plan can be represented by
the earlier technology, and vice versa. It therefore avoids the two off-diagonal
programs that can make the adjacent-period index infeasible. That is a consequence of
the declared information policy, not a row-by-row repair for troublesome results.

The choice should follow the reporting purpose:

| Reporting concern | Two contemporaneous technologies | One global technology |
|---|---|---|
| Central question | How did performance change when each neighboring year contributes its own benchmark? | How did performance change relative to one full-horizon benchmark? |
| Information admitted | The two relevant period samples | All periods in the declared study horizon |
| Cross-period assessment | Required | Not required |
| Long-run chaining | Generally path dependent | Circular within a fixed global sample |
| Revision when later years arrive | Mainly through affected period technologies | Potentially all historical global distances |

Neither policy is universally superior. The adjacent account is natural when each
year's institutional environment deserves separate standing. The common reference is
useful when a board wants one retrospective yardstick and internally consistent
long-run chaining. A short comparison of the two is often an informative sensitivity
check; it should not become a second parallel analysis with identically named
components.

### What does circularity buy, and what does it cost?

Suppose the same fixed global technology is used for three periods. Then

$$
GM^{t,t+1}GM^{t+1,t+2}
=\frac{d^G(z^{t+1})}{d^G(z^t)}
 \frac{d^G(z^{t+2})}{d^G(z^{t+1})}
=GM^{t,t+2}.
$$

Adjacent changes compound to the same first-to-last change because the intermediate
distance cancels. This circularity is valuable in dashboards and historical accounts:
the cumulative number does not depend on which intermediate reporting dates were
inserted.

But the qualifier “same fixed global technology” is crucial. A 2020--2025 study and a
2020--2026 study do not use the same information set. If the 2026 observations reveal
stronger production possibilities, earlier global distances—and hence earlier
productivity changes—may be revised. The global index is retrospective. A result
computed with observations from the future relative to the evaluated year should not
be presented as information that managers possessed at that time.

This creates a practical governance choice. An operational monitoring system can fix
and archive each benchmark vintage, while a retrospective study can recompute the
history using the latest full sample. Every common-reference result should therefore
identify the study horizon and benchmark vintage. Circularity within a vintage does
not imply invariance when the vintage changes.

### Should the report show every possible time horizon?

A board may want more than annual movements. It may ask whether a five-year
transformation agrees with the story told by the intervening annual reports, or
whether a disruption was temporary. Under one fixed global vintage, that is a
legitimate direct comparison: the first and last operating plans are judged by the
same retrospective production benchmark. The endpoint is not a new model, and it does
not attribute change to events between the dates. It is another reporting horizon for
the same production account.

DEAPack therefore keeps consecutive comparisons as the default and makes broader
reporting deliberate. `comparison_pairs="all"` returns every forward date pair;
an explicit selection such as `((2020, 2025),)` returns only the requested horizon.
The latter is usually preferable for an executive figure because the base date cannot
be mistaken for another starting point.

```python
from deapack import GlobalMalmquistDEA

annual_model = GlobalMalmquistDEA(comparison_pairs="adjacent")
all_horizons_model = GlobalMalmquistDEA(comparison_pairs="all")
five_year_model = GlobalMalmquistDEA(
    comparison_pairs=((2020, 2025),),
)
```

The convenience has a visible reporting cost. With $D$ organizations and $P$ dates,
the complete table contains $DP(P-1)/2$ rows rather than $D(P-1)$. The underlying
distance evidence is reused: each operating plan needs at most one own-period and one
global appraisal, so the solve graph remains proportional to $DP$. Yet tables,
diagnostics, and disclosed peers still grow with the number of pairs. All-horizon
output is therefore an opt-in research table, not a harmless default dashboard.

Matching is also a horizon-specific question. If a hospital is present in 2020 and
2021 but not 2025, it can receive the first annual change but not the five-year one.
With `unbalanced="drop"`, only that requested change row is omitted; its valid
observations still help define the common benchmark. With `"raise"`, the selected
pair is rejected so that the missing institutional history must be resolved explicitly.

When every pair has been fitted, a chart should still communicate one horizon at a
time. Filter both dates for a table, or fit a single explicit pair before plotting.
Otherwise several changes ending in 2025 may appear under one comparison-year label
even though they began in different years.

## Who must be observed twice, and who may still shape the benchmark?

Productivity change belongs to an identified organization observed in both periods.
Rows must be matched by the pair `(organization, period)`, never by their order in a
spreadsheet. If a provider appears only in 2024, it cannot have a 2024--2025 change
score. That does not mean its 2024 operation is devoid of technological information.

The **matched transition population** and the **frontier reference population** should
therefore be kept distinct. The former contains organizations observed in both
relevant periods. The latter can include every valid observation admitted by the
study design, including an organization seen in only one period. Deleting unmatched
organizations merely to create a rectangular panel may move a contemporaneous or
global benchmark and alter the results of organizations that remain.

This distinction matters especially under a global policy. A new entrant may not have
its own earlier transition, yet its observed practice can reshape the common benchmark
for every year. The empirical report should state how unmatched identities were
handled, which observations formed each reference technology, and whether entry and
exit are themselves part of the phenomenon under study.

## Make the benchmark choice visible

The project-authored `multiperiod_trajectory_contrast` data provide a compact
way to see why reference policy matters. Five neutral service trajectories are
observed over three periods, with one resource index and one service output.
Some paths improve, some deteriorate, and some change their relative operating
position. The data are designed for teaching policy contrasts rather than for
reproducing a paper table.

Begin with the adjacent-period model that provides the chapter's main
productivity comparison:

```python
from deapack import DEAData, FGNZMalmquist, GlobalMalmquistDEA, dataset_info, load_dataset

frame = load_dataset("multiperiod_trajectory_contrast")
roles = dataset_info("multiperiod_trajectory_contrast").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    period=roles["period"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
)

result = FGNZMalmquist().fit(data)

adjacent = result.summary()[[
    "dmu_id",
    "base_period",
    "comparison_period",
    "productivity_change",
    "efficiency_change",
    "technical_change",
]]
```

Every certified row reconstructs
$M^{t,t+1}=EC^{t,t+1}TC^{t,t+1}$. If a required appraisal is unavailable or
the decomposition fails to close, the transition has no defensible
productivity reading; diagnostic details belong in the DEAPack Documentation.
The operating-performance component locates movement relative to each period's
frontier, while the technical component records movement in represented
best-practice opportunities.

The result plot makes this core adjacent-period answer visible directly.

```python
result.plot(
    kind="performance",
    metric="productivity_change",
    period=2,
    view="points",
)
```

```{figure} ../../_static/figures/trajectory-contrast-performance-result.svg
:name: fig-merged-malmquist-performance-result
:alt: Adjacent-period productivity change across five project-authored service trajectories, shown relative to the no-change benchmark of one
:width: 92%

The chart separates improvements, declines, and no-change cases without
attributing frontier-relative movement to management. Each point is released
only when its four-appraisal account is certified.
```

As a deliberately brief sensitivity check, judge the same plans against one
full-horizon technology:

```python
global_result = GlobalMalmquistDEA(
    orientation="output",
    returns_to_scale="crs",
).fit(data)

global_account = global_result.summary()[[
    "dmu_id",
    "base_period",
    "comparison_period",
    "productivity_change",
    "efficiency_change",
    "best_practice_change",
]]
```

The global account uses one common retrospective information base. Two global
distances, $d^G(z^t)$ and $d^G(z^{t+1})$, form the headline change. The two
own-period distances retain the operating-performance comparison
$EC_G=d^{t+1}(z^{t+1})/d^t(z^t)$. Each global distance divided by its
own-period counterpart gives a best-practice gap; the change between those
gaps is $BPC_G$, and $GM=EC_G BPC_G$. Comparing `adjacent` with
`global_account` is therefore an interpretable sensitivity analysis, not a
race to select whichever policy gives the preferred number.

Neither answer is a computational mistake. The difference shows that the substantive
conclusion depends on whether each annual opportunity set receives its own standing
or both plans are judged on one retrospective information base. Constructor options,
returned fields, and diagnostic details belong in the separate DEAPack Documentation.

## Which modeling assumptions travel with the result?

The widely used classic account is output oriented and assumes constant returns to
scale (CRS) {cite:p}`fare1994`. Output orientation asks how much desirable output could
be proportionally expanded with the observed inputs. CRS permits proportional
replication of observed activities and makes input- and output-oriented radial indexes
coincide in theory. These assumptions may be reasonable for some sector-level studies,
but they are not harmless defaults.

Variable returns to scale (VRS) restricts comparisons to a convex scale range and can
be appropriate when organizations cannot freely replicate operations. Under VRS,
input and output orientations can tell different stories, and cross-period feasibility
can be more fragile. A VRS calculation can show whether conclusions depend on the
scale representation; it should be reported as such, not treated as a complete
decomposition into pure efficiency, scale, mix, and technical effects.

Reference populations also carry economic assumptions. If hospitals in different
regulatory regimes cannot reasonably learn from or be compared with one another, a
single pooled benchmark may exaggerate the opportunities available to management. If
quality is omitted, an apparent output gain may represent faster but worse care. If
capital is measured only at book value, changes in valuation may appear as production
change. The Malmquist calculation cannot repair a weak definition of inputs, outputs,
organizational comparability, or time.

The model in this chapter concerns desirable outputs. Pollution, adverse events, and
other undesirable outputs require an explicitly environmental production technology,
including assumptions about disposability and joint production. Adding an emissions
column to the ordinary desirable-output matrix does not create an environmental
productivity index.

Finally, all DEA productivity measures are sample-dependent frontier estimates.
Outliers, measurement error, and sampling variation can change both the organization's
distance and the benchmark against which it is measured. Statistical procedures for
Malmquist indexes address part of this uncertainty {cite:p}`simar1999`; tighter
numerical precision is not a substitute for inference.

## What should a decision maker be told?

A useful report begins with the decision question, not the model's acronym. It states
whether the aim is a neighboring-year comparison under two contemporaneous
technologies or a retrospective history under one full-horizon technology. It then
reports the overall change beside the appropriate two-part decomposition and explains
the components as benchmark-relative operating change and best-observed-opportunity
change.

The report should also make visible the orientation, returns to scale, period order,
matched transition population, frontier reference population, handling of infeasible
comparisons, study horizon, and—when a global technology is used—benchmark vintage.
These details determine what information management was assumed to face. They are not
software footnotes.

Most importantly, the conclusion must stop where the method stops. A Malmquist result
can show that an organization's observed input--output performance changed, that its
shortfall relative to contemporaneous best practice changed, and that the opportunities
supported by the reference data changed. It cannot, without complementary evidence,
attribute those changes to managerial skill, innovation, policy, competition, or
investment. Used with that discipline, the family turns repeated efficiency scores
into a coherent account of organizational progress while keeping the information
behind the benchmark open to scrutiny.
