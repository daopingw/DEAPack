# Visualization

Visualization is attached to the common result contract. Plot discovery is
backend-independent; Matplotlib is imported only when `plot()` renders a
figure. Install the optional backend with
`python -m pip install 'DEAPack[viz]'`.

## Result methods

```{automethod} deapack.DEAResult.available_plots
```

```{automethod} deapack.DEAResult.plot
```

The registered `performance` plot accepts declared result measures, not
arbitrary numeric columns. When `metric` is omitted, DEAPack selects the
safest valid finite native measure. `view="auto"` uses a ranked point plot for
at most 50 **valid reported results** per panel and an ECDF above that
threshold. A result is valid for this display only when its solve is optimal
and any measure-specific certification status plus row-level `score_valid` or
`score_status` evidence admit it to the substantive layer. Results with up to
four periods are faceted; a result with more periods requires an explicit
`period=...`. When every row in one facet carries the same complete
`base_period` and `comparison_period`, the comparison period matches the
selected facet, and the two periods differ, the facet title reports the
evidenced transition as `base → comparison`. Otherwise it retains the
ordinary `Period ...` label rather than guessing a transition from partial
metadata.

The core Hicks--Moorsteen result declares three public performance measures:
the headline `productivity_change` and the descriptive
`output_quantity_index` and `input_quantity_index`. All use one as the
no-change benchmark, but only the headline ratio has “above one indicates
improvement” semantics. Above one for either component means that aggregate
quantity increased. Source-technology-specific calculation components are not
promoted to separate performance plots. Every HM measure binds to the same
all-eight-distance `score_valid` release certificate.

The registered `frontier` plot does not accept `metric`. It uses input and
output quantities in the result's target table and active peers in its
intensity table. The first contract supports at most 200 organizations from
one selected cross-section, exactly one input and one desirable output,
`static.radial`, CRS or VRS, and `compute_slacks=True`. Every displayed row
must have an optimal completion status, `completion_valid=True`,
`target_valid=True`, `peer_valid=True`, finite observed and target coordinates,
and a reported strong-efficiency status. Active peers must belong to the
selected cross-section. These restrictions prevent a scalar drawing from
being advertised as the fitted frontier of a multidimensional, cross-period,
external-reference, or incompletely completed analysis.

The registered `trajectory` plot is restricted to
`dynamic.sbm.tone_tsutsui_2010`. It requires `dmu_id`, accepts one carry-over
`variable`, and rejects `period` because the complete fitted horizon is the
unit of analysis. Preparation requires a valid certified score, both
postsolve certificates, complete period/target/slack/link tables, exact
period order, and certified adjacent-period continuity. Outgoing and inherited
targets are drawn as different roles even when their certified values agree;
the terminal boundary never receives an inferred successor. The lower panel
is the complete period account across all scored production and carry-over
dimensions, not an attribution to the one carry-over selected for the upper
panel.

The registered `process` plot is restricted to the exact base
`network.sbm.tone_tsutsui_2009` contract under input orientation and classic
fixed/free links. It requires `dmu_id`, accepts `period` for a panel result,
and rejects `metric` and `variable`. Preparation cross-checks the independent
LP and network certificates, system and process accounts, declared weights,
expanded graph topology, and every handoff row. System-radial, relational,
additive, output/non-oriented, and accountable-link results are deliberately
not coerced into this reporting account.

The registered `improvement` plot has four independent dispatch branches. The
ordinary radial branch accepts exact `static.radial` results and keeps the
native input or output factor separate from Pareto--Koopmans completion. The
SBM branch accepts exactly the three classic static SBM method IDs and
`environmental.sbm.separable_strong`. The ordinary DDF branch accepts exactly
`static.directional_distance`. The environmental DDF branch accepts the core
CRS common-factor weak-disposal family and its exact equivalent CFG source
preset. All require `dmu_id`, accept `period` for a panel result, and reject
`metric`, `variable`, and non-auto views. Each branch retains its own native
score, sign convention, and production-account certificate; none imitates a
neighboring radial, normalized-gap, or beta account. Range-directional,
non-separable environmental SBM, Network, Dynamic, activity-specific weak-
disposal, by-production, legacy, and specialized results are not coerced into
a neighboring branch.

The registered `metafrontier` plot is restricted to the certified core radial
group/metafrontier decomposition. It displays `group_efficiency`,
`metafrontier_efficiency`, and `metatechnology_ratio` as one account and does
not accept `metric`, `dmu_id`, or `variable`; only `view="auto"` is supported.
A multi-period result requires one explicit `period`. Preparation verifies the
exact method identity, input/output orientation, CRS/VRS construction, fitted
time-information policy, component score certificates, the fitted three-row
component ledger, both phase-one diagnostic certificates, nested bounds, and
the identity $E^M=E^G\times MTR$. Uncertified rows are omitted, but a row that
claims certification while its component evidence, ledger, or identity is
inconsistent causes the selected plot to fail closed.

The registered `references` plot consumes the certified result of
`DEAResult.reference_frequency()` for one supported static convex global
cross-section. It counts reported solver-selected peer edges whose intensity
is strictly above the source result's `peer_tolerance`; it never sums
intensities or invokes a solver. Self-reference and use by other organizations
remain separate. The account does not enumerate alternate optima, identify
exact mathematical support or a global reference set, diagnose influence or
outliers, rank performance, or provide inference. `metric`, `period`,
`dmu_id`, and `variable` must remain omitted, and only `view="auto"` is
supported.

`DEAResult.available_plots()` is result-aware. The module-level
`deapack.visualization.available_plots()` call without a result returns the
global registry of plot kinds and should not be read as an applicability
guarantee for every result.

The renderer does not fall back to `score`, guess the direction of an unknown
column, clip the metric, or silently apply a generic `is_efficient`
classification to another criterion. Finite non-optimal solver rows remain
in a separate diagnostic layer as grey crosses and are excluded from rankings
and ECDFs. Finite rows that fail a declared `score_valid` or `score_status`
contract use the same diagnostic boundary. Missing and non-finite metric
values never receive coordinates. They are counted as unavailable and the
figure note carries a bounded, input-order roster of up to six organization
IDs with the decisive declared certification or validity status; a larger
roster reports the exact remaining count. This availability ledger uses the
selected measure's own certification column, so a component-specific failure
is not overwritten by a result-wide solver label. It remains distinct from
finite non-optimal or undefined values, which continue to appear only as grey
diagnostic crosses.

`rdm_efficiency` has a dedicated declaration: **Range Directional
Efficiency**, higher means less of the remaining range is jointly attainable,
and one means no positive common range-directional improvement. Its
classification column is intentionally absent because RDM efficiency one
does not certify Pareto--Koopmans efficiency. Use
`result.plot(metric="rdm_efficiency")` to select it explicitly.

## Frontier preparation contract

```{autofunction} deapack.visualization.prepare_frontier_data
```

```{autoclass} deapack.visualization.FrontierPlotData
:members:
```

The prepared `observations` table is detached from the result and contains
observed coordinates, reported target coordinates, efficiency status, and a
`target_changed` flag. The `frontier` table contains certified VRS observed
anchors or the displayed CRS frontier ray. The renderer adds arrows only for
nonzero target changes and states explicitly that benchmark opportunities are
not causal or prescriptive conclusions.

## Dynamic trajectory preparation contract

```{autofunction} deapack.visualization.prepare_trajectory_data
```

```{autoclass} deapack.visualization.TrajectoryPlotData
:members:
```

The detached `quantity` table contains observed, outgoing-target, and
inherited-target roles in the selected carry-over's original unit, together
with the result's own score-inclusion flags. `transitions` contains only the
certified nonterminal handoffs. `period_accounts` retains the complete period
performance account from the joint horizon solve. It combines all scored
ordinary inputs, ordinary outputs, good carry-overs, and bad carry-overs; it
is not a contribution from the selected `variable`. `horizon_efficiency`
remains the native intertemporal aggregate rather than a plotting-layer
average.

Preparation fails closed above 24 fitted periods. It does not sample or
compress a longer horizon because doing so would hide part of the certified
carry-over account.

## Network process preparation contract

```{autofunction} deapack.visualization.prepare_process_attribution_data
```

```{autoclass} deapack.visualization.ProcessAttributionPlotData
:members:
```

The detached `processes` table retains process performance, declared and
effective reconstruction weights, weighted achieved contribution, attributed
gap, and an explicit `scored` flag. The `links` table retains the fitted
source, recipient, variable, governance role, observation, common target, and
change in original units. `system_efficiency` and `system_gap` are reconstructed
from the process account; the renderer does not infer a causal decomposition
or a unique coordination prescription.

Preparation fails closed above 16 process accounts or 24 declared
link-variable accounts. Larger fitted networks remain available in the public
component and link tables; the dedicated connected display does not silently
omit or compress those accounts.

## Radial improvement preparation contract

```{autofunction} deapack.visualization.prepare_radial_improvement_data
```

```{autoclass} deapack.visualization.RadialImprovementPlotData
:members:
```

The method gate accepts only `static.radial` with an input or output
orientation, one of the supported ordinary RTS policies, and the exact
Pareto--Koopmans completion protocol. The selected observation must be inside
the maintained reference technology and must carry valid primary, completion,
and target claims. Exactly one diagnostic row for each fitted phase must
certify its LP, raw economic, published economic, and published-output
accounts. Peer and dual validity are independent because this figure displays
neither intensities nor marginal values.

For input orientation, the detached ledger reconstructs the phase-one plan as
$x^R=\theta x_o,y^R=y_o$; for output orientation it uses
$x^R=x_o,y^R=\phi y_o$. Every completed input must then satisfy
$x^*=x^R-s^-$ and every completed output must satisfy $y^*=y^R+s^+$. The
public physical slack rows must reproduce the selected summary's physical
maximum-slack account. The public `targets` table contains
the completed plan, so the preparer never presents it as the unlabeled
proportional point. The detached table intentionally does not republish the
scaled-slack magnitude: its exact scale also depends on the fitted reference-
set row maximum, which is not part of this target-only reporting contract.

The detached table retains one original-unit row per variable and never
creates a common quantity axis. Discovery and preparation read fitted result
tables only and add no optimization task. The renderer treats phase one and
completion as separate accounting claims, not an implementation order, and
does not infer target uniqueness, closeness, transition cost, causation, or a
management prescription.

## SBM improvement preparation contract

```{autofunction} deapack.visualization.prepare_sbm_improvement_data
```

```{autoclass} deapack.visualization.SBMImprovementPlotData
:members:
```

The exact method whitelist is
`static.sbm.input.tone2001`, `static.sbm.output.tone2001`,
`static.sbm.nonoriented.tone2001`, and
`environmental.sbm.separable_strong`. The detached `variables` table retains
role, fitted variable order, observed and target quantities, physical and
normalized slack, signed proportional change, equal-dimension weight, and
objective-membership status. Resource saving, desirable-service gain, and
undesirable-residual reduction remain distinct variable roles. For the
environmental method, the prepared input-retention and combined
desirable/bad-output expansion accounts reconstruct the certified native
score; for example, the two-plant case reconstructs
$2/7=(1-1/2)/(1+3/4)$.

The environmental display is conditional on the exact separable,
strong-disposal technology. Its selected row must also carry certified
reference-technology membership and a valid certified primary-program target;
a finite score or an `optimal` backend label alone is insufficient. Structural
self inclusion and a certified external SBM balance are both admissible
membership routes. Peer and dual validity are independent because neither
claim appears in this target ledger. Preparation fails closed for a
non-separable or weak-disposal environmental *SBM* and for Network or Dynamic
SBM; familiar target and slack column names do not expand the whitelist. The core weak-
disposal DDF uses the separate contract below. Rendering does not estimate a
new plan, infer the cause of a gap, monetize undesirable-output damage, claim
target uniqueness, or treat unlike physical units as one common quantity
scale.

## Ordinary DDF improvement contract

```{autofunction} deapack.visualization.prepare_directional_ddf_improvement_data
```

```{autoclass} deapack.visualization.DirectionalDDFImprovementPlotData
:members:
```

The method gate accepts only `static.directional_distance`. It verifies the
direct black-box convex technology, native beta account, input-contraction and
desirable-output-expansion sign convention, declared direction policies, and
the Pareto--Koopmans slack-completion policy. A preset or specialization, a
range-directional method, an environmental DDF, or a familiar target-table
schema does not inherit this route.

The selected row must retain a finite nonnegative beta satisfying
`score == distance`, a valid primary result, an optimal certified optional
completion, and a certified completed target. Exactly one phase-one and one
phase-two diagnostic row must certify their solver-neutral LP, raw economic,
published economic, and published-output accounts. Peer and dual validity are
not prerequisites because this figure displays neither intensities nor
marginal values.

For every declared input and desirable output, the detached `variables` table
keeps the observed quantity, fitted direction, `beta * direction`, the
directional target, any additional physical and scaled completion slack, and
the final target. Every slack row retains its positive `slack_scale` and must
reconstruct `scaled_slack = slack / slack_scale`. Input rows reconstruct
`target = observed - beta * direction - slack`; output rows reconstruct
`target = observed + beta * direction + slack`. The maximum physical and
scaled slacks must reproduce the selected summary row. Rendering uses one
original-unit card per variable and presents the sequence as a conditional
benchmark account, not a common quantity axis, causal diagnosis, unique
target, implementation order, or least-cost plan. Discovery and preparation
are backend-lazy and never invoke a solver. Organization, period, and variable
display labels are control-stripped and bounded before rendering; original
identifiers remain available in the detached payload.

## Common-factor environmental DDF improvement contract

```{autofunction} deapack.visualization.prepare_environmental_ddf_improvement_data
```

```{autoclass} deapack.visualization.EnvironmentalDDFImprovementPlotData
:members:
```

The method gate accepts
`environmental.ddf.weak_disposal.common_factor` and the exact
`environmental.ddf.output.chung_fare_grosskopf_1997` source preset. The latter
must retain its source preset ID, zero input direction, observed desirable- and
undesirable-output directions, CRS common-factor technology, and null
jointness. A non-null `specialization_id`, a legacy compatibility alias, or a
strong-disposal, activity-specific, by-production, Network, or Dynamic method
fails closed.

The selected summary row must have an optimal, defined, valid, finite,
nonnegative beta; certified membership in the fitted reference technology; at
least one positive fitted direction component; an optimal certified slack
completion; a certified completed target; and finite nonnegative `max_slack`
and `max_scaled_slack` accounts. There must be exactly one phase-one and one
phase-two diagnostic row, and both must certify the LP, raw economic, published
economic, and published-output accounts. An external equality-based appraisal
may also carry one certified phase-zero reference-membership diagnostic. Peer
and dual validity are intentionally not consulted because the figure displays
neither claim.

The detached `variables` table keeps observed quantity, fitted direction,
beta-scaled programme change, quantity after that declared programme, physical
and scaled slack completion, and final target as separate fields. Inputs must
reconstruct
`target = observed - directional_change - slack`; desirable outputs must
reconstruct
`target = observed + directional_change + slack`; and common-factor bad
outputs must reconstruct
`target = observed - directional_change` with `slack_allowed=False` and no
bad-output slack row. The physical and scaled slack maxima must reproduce the
two summary aggregate accounts.

Direction policies are checked against public fitted evidence. `zeros`,
`ones`, and `observed` are reconstructed row by row. For `mean`,
`custom_global`, and `custom_by_observation`, preparation forms each
role-by-variable array once in stable summary observation order. Mean values
must equal the public observed-coordinate means; custom arrays must reproduce
the immutable numeric parameter fingerprint in `expanded_spec`. If required
public rows are missing, the result cannot prove that complex direction and
fails explicitly. Self, mixed, and external reference-appraisal policies are
accepted; negative beta is rejected for the selected row rather than by
forbidding the fitted reference policy.

Result-bound discovery first removes summary rows that cannot possibly satisfy
these release conditions with one vector operation. Only surviving candidates
enter the complete row-level reconstruction. The common `zeros`/`ones`/
`observed` preparation path copies only the selected plan; full ledgers are
assembled once per role only when `mean` or custom directions require them.

Rendering uses original-unit row cards and no shared quantity axis. It states
that beta is a common programme ambition rather than an SBM score, separates
the declared move from slack completion, labels zero moves as fixed, and
describes the target as one selected feasible benchmark rather than a unique,
causal, engineering, or cost conclusion. Discovery and preparation are
backend-lazy and never invoke a solver.

## Radial metafrontier preparation contract

```{autofunction} deapack.visualization.prepare_metafrontier_data
```

```{autoclass} deapack.visualization.MetafrontierPlotData
:members:
```

The detached `observations` table contains one row per certified organization
and selected period, with its declared group, group efficiency, metafrontier
efficiency, and MTR. The payload also records the number of omitted uncertified
rows, the maximum reconstruction residual, orientation, RTS, period label, and
fitted provenance. It does not treat the plotted difference between efficiency
markers as an additional decomposition term, and it does not mutate or repair
the source result.

For panel results, `period` selects the displayed organization-period rows; it
does not change the fitted all-period reference policy. A multi-period result
without `period`, an unknown period, a forged certification claim, a failed
bounded decomposition identity, a mismatch with the fitted component ledger or
primary diagnostics, or a selection with no certified rows raises
`PlotNotAvailableError`.

The connected-point view also fails closed above 60 certified organizations.
For a larger selection, use the registered component-specific performance
distribution or the public tables rather than an unreadable all-organization
display.

The general `performance` plot remains available for a single registered
metafrontier measure such as `metatechnology_ratio`, `group_efficiency`, or
`metafrontier_efficiency`. It is not a substitute for the dedicated three-part
decomposition when the relationship among those quantities is the reporting
question.

## Selected-plan reference-frequency preparation contract

```{autofunction} deapack.visualization.prepare_reference_frequency_data
```

```{autoclass} deapack.visualization.ReferenceFrequencyPlotData
:members:
```

The detached `references` table contains at most 30 nonzero-frequency rows,
ranked by reported use by other organizations, total reported use, and stable
fitted input order. The payload separately records the full potential-reference
count, the selected-reference count, selected rows omitted by the top-30
readability rule, zero-frequency rows not drawn, active peer edges, source
threshold, and zero-additional-solve provenance. The renderer discloses these
counts in the figure note; limiting the display therefore does not alter the
complete analysis returned by `DEAResult.reference_frequency()`.

Preparation validates the analysis identity, source method and expanded
specification, cross-sectional roster, fitted `peer_tolerance`, complete
certified selected-plan diagnostics, and exact count identities. Any mismatch
raises `PlotNotAvailableError`. It does not reconstruct peer use from a score
column or from unverified intensity rows.

## Plot descriptions and errors

```{autoclass} deapack.visualization.PlotInfo
:members:
```

```{autoclass} deapack.visualization.MeasureSpec
:members:
```

```{autoclass} deapack.visualization.PlotNotAvailableError
```

An unknown plot kind, theme, view, period, or metric raises
`PlotNotAvailableError`. A missing Matplotlib installation raises
`ImportError` with the visualization-extra installation command.
