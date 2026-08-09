# Result contract

Every model returns a `DEAResult`. Native model values are kept separate from
standardized display efficiency.

```python
summary = result.summary()
peers = result.peers("E")
targets = result.targets_for("E")
```

The result contains tidy tables:

- `summary_frame`: one row per evaluated observation;
- `slacks`: variable-level slack values;
- `targets`: observed and projected variable values;
- `intensities`: positive reference intensities;
- `duals`: solver marginals with constraint labels;
- `components`: system, process, or other component scores and score bounds;
- `multipliers`: fitted virtual-value accounts without mislabeling them as duals;
- `links`: internal quantities, feasible link intervals, and selected targets;
- `appraisals`: role-explicit peer or strategic appraisal rows, such as
  appraiser--evaluatee or protected--focal pairs;
- `history`: iteration-by-organization trajectories for algorithms whose
  convergence is part of the result;
- `diagnostics`: statuses, messages, iterations, and residuals;
- `metadata`: all technology, measure, reference, solver, and tolerance choices.

Every built-in result also contains a canonical identity block:

```python
result.metadata["registry_schema_version"]  # 2
result.metadata["method_id"]                # e.g. "static.radial"
result.metadata.get("specialization_id")    # e.g. "static.radial.crs"
result.metadata.get("preset_id")            # e.g. "static.radial.crs.input"
result.metadata["expanded_spec"]
```

`expanded_spec` records eleven compact, JSON-safe parts of the fitted study:
decision context, production graph, data roles, technology, frontier
estimator, reference policy, performance criterion, valuation, evaluation
protocol, analysis, and uncertainty. It contains specifications, not input
rows or solver arrays.
This makes two results comparable by their actual assumptions rather than by a
historical class name alone. `specialization_id` appears when a constructor
fixes a meaningful but partial specialization. `CCR` and `BCC`, for example,
fix CRS and VRS respectively while leaving orientation configurable and
allowing score-only work. Both default to input orientation when it is
omitted, but that convenience default does not turn the partial constructor
into a complete historical recipe.

`preset_id` identifies an explicitly selected complete recipe. `CCRInput`,
`CCROutput`, `BCCInput`, and `BCCOutput` fix RTS, orientation, native-score
convention, and `compute_slacks=True` with DEAPack's row-scaled lexicographic
slack-completion policy. Their result identities are:

| Constructor | `method_id` | Additional identity |
|---|---|---|
| `CCR` | `static.radial` | `specialization_id="static.radial.crs"` |
| `BCC` | `static.radial` | `specialization_id="static.radial.vrs"` |
| `CCRInput` | `static.radial` | `preset_id="static.radial.crs.input"` |
| `CCROutput` | `static.radial` | `preset_id="static.radial.crs.output"` |
| `BCCInput` | `static.radial` | `preset_id="static.radial.vrs.input"` |
| `BCCOutput` | `static.radial` | `preset_id="static.radial.vrs.output"` |

`specialization_id` and `preset_id` are mutually exclusive. A direct
`RadialDEA(orientation="input", returns_to_scale="crs")` call may be
numerically equivalent to `CCRInput()`, but it retains only the family
`method_id`; result construction does not guess a historical identity that
the caller did not select.

The same field can identify a source-defined reporting specialization within
one canonical method. Tone--Tsutsui network SBM retains
`network.sbm.tone_tsutsui_2009` as its `method_id`, while a recipient-
accountable incoming link or supplier-accountable outgoing link records the
corresponding equation (26) or (27) `specialization_id`. This does not create
a duplicate model family: it makes the selected responsibility account
discoverable without hiding the common network technology and compiler.

Material settings are retained without copying the analysis table into every
result. Variable names and their input, desirable-output, undesirable-output,
and pollution-generating roles are explicit. Window bounds are stored
directly. A custom reference subset is represented by its size and a stable
set fingerprint. User-supplied direction arrays and additive weights likewise
carry their scope, shape, variable order, and a stable SHA-256 fingerprint;
named rules such as `observed` or `mean` retain the rule name instead. Small
economic parameter systems, such as material coefficients and aggregation
weights, are recorded directly. These fingerprints distinguish fitted
specifications but are not substitutes for preserving the original analysis
configuration.

Supplied prices use a stricter confidentiality boundary: result metadata
records their scope, source, currency, numeraire, base period, variable
names, and numerical signatures, but not the price payload. Cost and revenue
results include only the side they actually use; profit and Nerlovian results
record the joint input/output price contract. The original immutable
`PriceData` remains part of the reproducibility record.

Result metadata, including nested mappings and sequences outside the canonical
block, are deeply immutable after fitting. JSON-origin lists retain list-like
equality and encoding behavior but reject mutation. This prevents downstream
plotting or reporting code from silently changing the assumptions attached to
a result.

Appraisal protocols use explicit organizational roles rather than overloading
`dmu_id`. The query helpers accept the relevant identifier column:

```python
# Internal/deferred ordinary cross-efficiency prototype
result.appraisal_rows_for("A", id_column="appraiser_dmu_id")

# Public pair-specific game cross-efficiency
result.appraisal_rows_for("A", id_column="protected_dmu_id")
result.multipliers_for("A", id_column="focal_dmu_id")
result.history_for("A")
```

The default for `appraisal_rows_for` is `evaluatee_dmu_id`; the default for
`multipliers_for` remains the conventional `dmu_id`. If the selected role is
absent, the helper raises `KeyError` and lists the available columns instead
of guessing.

For backward compatibility, third-party code may still construct a
`DEAResult` without this identity block. Consumers should therefore use
`metadata.get("method_id")` when accepting external result providers.

`score` is the model-native quantity. `efficiency` is always higher-is-better
when a valid standardized mapping exists. `distance` is reserved for a native
distance or inefficiency value and can be missing.

Some models retain a finite raw account for audit even when it is not a
defined performance measure for that row. `score_valid` is the explicit
Boolean validity certificate when present; older or criterion-specific
results use `score_status`. Reporting and visualization require both the
measure-specific solver certificate and positive validity evidence before
admitting such a value to a substantive ranking. An excluded raw account
remains visible as a diagnostic rather than being silently erased or treated
as performance.

Validity is claim-specific. `target_valid`, `peer_valid`, and `dual_valid`
govern their corresponding semantic tables when a model exposes them; a valid
headline score does not authorize consumers to infer that every selected
target, thresholded peer account, or dual row was released. Conversely, a
denominator can make a ratio score undefined while a certified value optimum
and target remain auditable. Status fields expose these distinctions without
forcing reporting code to reverse-engineer them from table emptiness.

For the direct cost, revenue, and profit models, postsolve certification is
atomic at the relevant observation or cached price/reference task. An
uncertified LP or economic account retains directly observed monetary values
and raw diagnostics but withholds derived scores and semantic tables.
Certification performs no extra optimization, and the published monetary
account is the same account that was certified—not a separately rounded
display copy.

For a two-stage result, the relevant status need not be the last attempted
solve. Classic radial DEA, for example, binds `score` and `efficiency` to
`primary_solver_status` plus `score_valid`; a failure in the optional
slack-completion phase can therefore leave the certified proportional score
available while `completion_valid`, `target_valid`, and the strong-efficiency
claim fail closed. Consumers of targets or peer accounts must check their own
validity fields instead of inferring them from a finite score.

`is_efficient` has a deliberately narrower meaning than “this model's score
is at its best value.” It is a nullable Pareto--Koopmans status: `True` or
`False` is reported only when a compatible completion task or another
logically sufficient certificate has checked all relevant input excesses and
output shortfalls. Criterion-specific fields such
as `is_radially_efficient`, `is_directionally_efficient`,
`is_cost_efficient`, `is_revenue_efficient`,
`is_allocatively_efficient`, and `is_scale_efficient` retain the native
question. When no strong completion is available, `is_efficient` is missing;
that means “not certified,” not inefficient.

For ordinary radial, DDF, and GDF results, `compute_slacks=True` composes the
released `evaluation.target_completion.pareto_koopmans` protocol. It is a
result-evaluation protocol, not a standalone callable model. Provenance is
explicit:

```python
result.metadata["target_completion_id"]
# "evaluation.target_completion.pareto_koopmans", or None when not composed
```

The protocol fixes the primary score before, when completion succeeds,
selecting a strongly efficient ordinary input/desirable-output target with
DEAPack's row-scaled secondary rule. That rule is unit stable, but it is not a
claim of a unique, nearest, least-cost, or causally identified management
plan. The shared protocol ID identifies the Pareto--Koopmans completion
principle and LP layout, not identical alternate-optimum weights in every
model: radial DEA and DDF anchor row scales to the evaluated observation,
whereas GDF anchors them to its fixed path target. This distinction can select
a different member of a multiple-optimum set of strong targets; it does not
change the first-stage score or the strong-efficiency certificate. This reusable
Pareto--Koopmans completion protocol does not currently extend to weak-disposal,
non-discretionary, or non-convex technologies.

For example, radial input DEA reports $\theta$ as both `score` and
`efficiency`. Additive DEA reports its weighted slack sum as both `score` and
`distance`, while `efficiency` is missing because raw additive distance is not
bounded or unit invariant. RAM reports bounded range-adjusted efficiency as
`score` and `efficiency`, and preserves its complementary normalized
inefficiency as `distance`. For RAM, also inspect `source_profile_matches`:
the 1999 source profile requires one self-inclusive VRS cross section with
the range and technology populations aligned. A zero-range coordinate is
handled by the source rule: its slack contribution is zero, and the retained
DEAPack balance forces that slack to zero. A pooled panel may run only under
the documented package policy and does not receive the historical
cross-sectional source certificate.

For both direct additive DEA and RAM, the headline, selected operating plan,
displayed peer portfolio, and published dual account are separate claims.
`score_valid` requires the certified source programme plus both raw and
published weighted-slack accounts;
`target_valid` certifies the cleaned original-unit resource/service balances;
`peer_valid` says that the actually displayed, thresholded intensities still
reconstruct that plan; and `dual_valid` governs the complete original-unit
multiplier account. A false peer or dual flag need not erase a certified score
or target. Conversely, `solver_status="optimal"` is only the raw backend
outcome and never overrides a false semantic validity field. Certification
reuses the returned solution, so `additional_solver_calls` remains zero.

Radial FDH follows the same input-$\theta$/output-$\phi$ native-value
convention but evaluates one observed comparator at a time under a non-convex
technology. Tied peer rows are alternative single-activity benchmarks, each
with `lambda=1`; they must not be summed as a convex peer. With a custom
reference that excludes the evaluated unit, the result also reports whether
the observation lies inside that external reference technology before making
an efficiency classification.

The three standard SBM contracts report a native higher-is-better value in
`score` and `efficiency`, with its complement in `distance`.
`InputSBM` uses the retained-input account
$\rho^I=1-\overline{s^-/x_o}$; `OutputSBM` uses the reciprocal
$\rho^O=1/(1+\overline{s^+/y_o})$ and retains
`output_expansion_factor` $=1/\rho^O$; non-oriented `SBM` uses
$\rho=(1-\overline{s^-/x_o})/(1+\overline{s^+/y_o})$.

`is_sbm_efficient` answers only the fitted orientation. A value of one for
input SBM does not rule out output shortfall, and a value of one for output
SBM does not rule out input excess. Consequently, `is_efficient` is missing
for both single-oriented models. Non-oriented SBM includes every ordinary
input and output slack in its objective and can populate the generic
Pareto--Koopmans status.

The summary retains `max_normalized_slack`,
`max_objective_normalized_slack`, and
`max_unoptimized_side_normalized_slack`. These proportional fields are used
for efficiency classification because a single raw tolerance cannot compare
employees, currency, and service counts. Their `max_*_slack` counterparts
remain in original units for operational interpretation. Mean normalized
input/output gaps and variable-level `normalized_slack` values complete the
score audit.

Every SBM target and positive peer row is labeled
`solver_selected_primary_optimum`. In a single orientation, slacks and
targets on the other side make the selected benchmark feasible but do not
optimize a second managerial objective. They may change under another
optimal solution and should not be reported as uniquely prescribed savings
or expansions.

DDF reports native $\beta$ in both `score` and `distance`: it is the attainable
amount of an analyst-declared operating counterfactual under the fitted
technology and direction. The bounded `efficiency` field is retained for API
compatibility as the convenience display transformation $1/(1+\beta)$. It is
not the native DDF quantity and is not a general efficiency measure. Results
should therefore be interpreted from $\beta$, the declared direction, and the
implied variable-level changes.

For DDF, `score_valid` certifies the primary directional programme and its
production account. `completion_valid` and `target_valid` refer to the
optional residual-slack stage, while `peer_valid` and `dual_valid` govern
their respective tables. A certified primary score may therefore coexist with
a withheld secondary target. This is deliberate: failure of an optional
target-selection programme must not turn a verified directional distance into
a missing value, and it must not make an unverified activity plan look valid.

GDF reports its bounded Chavas--Cox value $\delta$ in `score`, `efficiency`,
and `generalized_distance`; `distance` is missing because no complementary
distance is defined by this result contract. `resource_commitment` and
`service_commitment` translate the declared `alpha` into operating
multipliers. `is_gdf_efficient` tests only the common proportional contract,
while nullable `is_efficient` also requires row-scaled slack completion.
Targets keep the algebraic `path_target`, the score-stage peer activity, and
the completed strong target separate. Interior-VRS results additionally
retain certified search bounds, gap, solve count, and convergence status.

Environmental DDF retains the same native-distance convention and records the
exact production account rather than relying on a generic “bad output” label.
Common-factor results identify the source CRS technology; activity-specific
results identify the Kuosmanen VRS technology and expose active, complementary,
total, and retention-rate intensity accounts. The deprecated `weak` selector
records only the legacy equality, reports disposal as `not_identified`, and
retains `compatibility_alias="weak"`. Every result also records null
jointness, directions, the exact bad-output constraint, and whether each
bad-output target permits residual slack.

Undesirable-output SBM reports its native $\rho^B$ as `score` and
`efficiency`, with $1-\rho^B$ as `distance`. Its summary separates input,
desirable-output, and bad-output normalized inefficiency while retaining the
joint $1/(s+q)$ output aggregation used by the objective. Metadata identifies
the current model as separable and strongly disposable.

BP-DDF reports the native joint distance in `score` and `distance`, plus
`intended_distance` and the residual-generation component stored under the
stable field name `environmental_distance`. The joint value is the smaller
component distance. `is_directionally_efficient` tests this native joint
commitment. The current BP-DDF implementation does not run a residual-
slack completion over both subtechnologies, so `is_efficient` remains missing
even when both component distances are zero. Intensities and diagnostics
identify their `subtechnology`. The source profile uses CRS in both
subtechnologies, one fixed direction, and a full self-inclusive cross-section;
metadata marks other RTS, observation-varying directions, and temporal
references as package extensions. The reported `1/(1+distance)` efficiency is
a display transform rather than the source-native value.

`score_valid` requires independently certified intended-production and
residual-generation LP and quantity accounts. The same two-account gate
controls `target_valid`; `peer_valid` separately checks both intensity systems
after reporting thresholds, and `dual_valid` requires both original-unit
component marginal accounts to be complete. A failed component therefore
cannot leak a partial joint target, peer system, or dual table. Component
solver diagnostics remain available to explain which account failed.

By-production FGL reports overall higher-is-better efficiency in `score` and
`efficiency`, its DEAPack display complement in `distance`, and the two components
`productive_efficiency` and `environmental_efficiency`. Intended-production
diagnostics include a certified cutting-plane lower bound, feasible upper
bound, `optimality_gap`, and a post-solve certificate for the actual returned
incumbent; peer rows retain the two subtechnologies.
`is_fgl_efficient` records whether both native components attain one.
That is the source's output-vector criterion; input slack can remain. Because
the condition is not a Pareto--Koopmans input-and-output completion,
`is_efficient` remains missing.
The default source profile is CRS/CRS over one full self-inclusive
cross-section. Metadata labels alternative RTS and temporal/custom references
as package extensions.

Materials-balance DEA reports Coelli--Lauwers--Van Huylenbroeck environmental
efficiency in `score` and `efficiency`, with $1-EE$ in `distance`. The summary
also retains `technical_efficiency`, `environmental_allocative_efficiency`,
weighted observed/minimum material inflow, and weighted observed/minimum
surplus. Targets distinguish `technical_radial` from `material_minimum`, while
peer rows identify their `component`. Per-material inflow and surplus targets
remain separate even when an explicit weighted aggregate defines the score.
`is_material_efficient` records the native material criterion; the generic
strong-efficiency status is missing because a zero-content input or an
unmodeled output opportunity can lie outside that criterion.

Within the current one-material source certificate,
`environmental_allocative_efficiency` is physical-content $EAE=EE/TE$ and
requires no prices. The exact evidence is limited to self-inclusive
cross-sectional CRS/VRS with common known nonnegative coefficients, positive
observed inflow, and a fixed desirable-output commitment.
Material-minimizing targets and peers can be nonunique. The source-defined
multi-material aggregation and panel/custom/external source equivalence
remain outside that independent certificate.

Cost DEA reports `cost_efficiency` in both `score` and `efficiency`, with
`observed_cost`, `minimum_cost`, and `cost_gap` retained beside it.
`distance` is missing. Its targets are cost-minimizing activities, not
technical slacks, and its duals are explicitly labeled model-derived
output-commitment shadow values. Under an external reference, a ratio above
one is retained rather than clipped. `is_cost_efficient` records the economic
criterion; `is_efficient` remains missing because a least-cost optimum alone
does not certify Pareto--Koopmans efficiency.

The matched cost allocative operator uses `allocative_efficiency` as its
generic `score` and `efficiency`, while retaining `technical_efficiency` and
`cost_efficiency`. `reconstruction_residual` audits the identity
`cost_efficiency = technical_efficiency * allocative_efficiency`.
Its criterion-specific status is `is_allocatively_efficient`; it does not
populate the generic strong-efficiency status.

Revenue DEA reports higher-is-better `revenue_efficiency` in `score` and
`efficiency`, while retaining `observed_revenue`, `maximum_revenue`,
`revenue_gap`, and the native `revenue_expansion_ratio`. Its targets are
revenue-maximizing activities, which may change the output mix and leave input
capacity unused. Under an external reference, a ratio above one is retained;
if maximum revenue is zero, the ratio is missing and `score_status` records
the invalid denominator. `is_revenue_efficient` records the value criterion;
unused reducible inputs are one reason that this flag is not copied into
`is_efficient`.

The matched revenue allocative operator uses `allocative_efficiency` as its
generic score and retains `technical_expansion_factor`,
`technical_efficiency`, and `revenue_efficiency`.
`reconstruction_residual` audits
`revenue_efficiency = technical_efficiency * allocative_efficiency`.
`decomposition_defined`, component solver statuses, and denominator-validity
fields prevent a zero output expansion factor from becoming a fabricated
decomposition. `is_allocatively_efficient` is criterion-specific;
`is_efficient` remains missing.

Maximum-profit DEA reports the monetary `profit_gap` in `score`, with lower
values better. `efficiency` and `distance` are missing because profit ratios
are not order preserving with zero or negative profit. Targets are labeled
`profit_maximizing_activity`. With a self-inclusive reference and complete
strictly positive prices, a zero gap itself certifies Pareto--Koopmans
efficiency; a positive gap can be purely allocative, so it leaves
`is_efficient` missing. External-reference raw gaps are retained while the
score and status fail closed.

Return-to-dollar analysis reports the higher-is-better
`profitability_efficiency` in both `score` and `efficiency`. It retains
`observed_cost`, `observed_revenue`, `return_to_dollar`,
`observed_profitability`, `maximum_profitability`, and
`profitability_gap`. `return_to_dollar` and `observed_profitability` are exact
field aliases for output revenue divided by input expenditure; they are not
the relative efficiency score and are not profit ratios.

The maximum ratio is the exact largest reference-activity ratio under the
supported positive-cost CRS/VRS technologies. VRS targets use the selected
reference plan; CRS targets scale that plan to the evaluated unit's observed
input expenditure. `target_scale_policy`, `maximizer_count`, and
`target_uniqueness` make those choices visible. A self-inclusive score of one
provides positive Pareto--Koopmans evidence under complete strictly positive
prices; a lower score leaves generic `is_efficient` missing. External
reference scores remain unclipped, may exceed one, and carry
`score_status="defined_external_comparison"`. The closed-form backend returns
empty duals rather than fabricating solver marginals.

The matched GDF profitability decomposition uses `allocative_efficiency` as
its generic `score` and `efficiency`. It retains
`profitability_efficiency`, `crs_technical_efficiency`,
`vrs_technical_efficiency`, and `scale_efficiency`, together with residuals
for both multiplicative reconstruction identities. Long tables label the
profitability-maximizing, CRS-GDF, and VRS-GDF components; the latter two
retain their score-stage and slack-completed stages. Because
`is_allocatively_efficient` answers only the priced mix question, the
composite result leaves generic `is_efficient` missing.

Kao--Hwang relational network analysis reports
`system_efficiency`, `stage_1_efficiency`, and `stage_2_efficiency`.
`reconstruction_residual` audits the source-specific product identity. The
long `components` table can additionally retain the complete interval of
stage attributions when the system optimum does not identify one unique
division of the fitted performance account. `multipliers` stores each intermediate weight
once and labels it as shared by the upstream output and downstream input
accounts.

The two processes retain separate intensities in `intensities`; shared
intermediate weights do not imply shared peers. `links` records downstream
requirement $Z\mu$, upstream supply $Z\lambda$, their feasible target
interval, and the declared midpoint selection. Because the current
source-qualified projection is not a residual-slack completion,
`is_relationally_efficient` and the stage-specific flags are available while
generic `is_efficient` remains missing. Stage scores are performance
attributions under the fitted accounting policy, not causal contributions or
assignments of managerial blame.

Chen--Cook--Li--Zhu additive network analysis reports the same three
higher-is-better system and process fields, but its
`weighted_stage_sum` reconstructs the system score as an arithmetic mean.
`stage_1_weight` and `stage_2_weight` are endogenous virtual-resource shares;
they are not declared importance weights. `components` retains each share,
its origin, the corresponding virtual input and output, the VRS process
intercept, and the selected stage-priority policy. If the optimum supports
several performance accounts, `decomposition_unique` remains false rather
than presenting one solver vertex as uniquely identified.

The additive projection also keeps the upstream plan $Z\lambda$ and the
downstream plan $Z\mu$ separate. `links.source_target`,
`links.target_target`, `disposed_quantity`, and `balance_residual` expose the
full Lim--Zhu account; no midpoint is inserted. The two processes retain
separate intensity rows. `is_additively_efficient` and stage-specific flags
answer the native source questions, while generic `is_efficient` remains
missing because the projection is not a Pareto slack completion.

Cook--Zhu--Bi--Yang general additive analysis reports
`system_efficiency`, `weighted_process_sum`, and
`reconstruction_residual` for each open-network organization. Its
`components` table has one system row and one row per declared process.
Process rows expose `efficiency`, the endogenous `aggregation_weight`, valued
process inputs and outputs, and the weight origin
`endogenous_virtual_process_input_share`. These shares describe the fitted
resource-aggregation account; they are not externally supplied managerial
importance weights.

The source CRS primary optimum need not identify a unique multiplier or
process decomposition. The result therefore uses
`decomposition_status="solver_selected_not_uniqueness_certified"` and leaves
`decomposition_unique` missing. `multipliers` records external and shared-link
valuations, while `links` records each observed internal product once with its
supplier and recipient. The source-checked programme defines no general-DAG
projection, so `targets` and `intensities` are empty,
`target_status="not_available_in_source_contract"`, and generic
`is_efficient` remains missing. A system score should not be interpreted as a
Pareto-complete operating plan.

CCF Nerlovian analysis reports `nerlovian_inefficiency` in both `score` and
`distance`; lower is better and `efficiency` is missing. It retains the raw
profit gap and `direction_value`, plus `technical_inefficiency`,
`allocative_inefficiency`, `decomposition_defined`, and
`reconstruction_residual`. Targets and peers distinguish the profit maximum
from the direct directional programme and optional slack-completed activity.
`decomposition_slack_status` says whether residual slacks were absent,
present, unchecked, or not certified because completion failed.

Malmquist analysis uses one summary row per matched adjacent-period
transition. `score` and `productivity_change` contain the multiplicative
productivity index; `efficiency` and `is_efficient` are missing because a
transition is not a bounded efficiency level. `efficiency_change` measures
the change in the observation's operating shortfall relative to each period's
declared benchmark. “Catch-up” is only a historical label for a decrease in
that measured shortfall; it is neither a causal finding nor an attribution to
management. `technical_change` measures the change in production
opportunities represented by the declared period-specific reference
technologies. “Frontier shift” is historical shorthand, not evidence of
innovation or adoption. These components satisfy
`productivity_change = efficiency_change * technical_change`. Four explicitly
named cross-period distance columns, diagnostics, and peer systems make the
decomposition auditable. Both components are conditional on reference-sample
construction and the remaining study design. `period` is the comparison period
and `base_period` remains explicit.

Luenberger analysis has the same transition keys and four-distance audit trail
but uses additive directional distances. `score` and `productivity_change` are
positive for improvement, negative for decline, and zero for no change.
`efficiency_change` and `technical_change` satisfy
`productivity_change = efficiency_change + technical_change`. Diagnostics may
contain negative cross-period directional distances; these are meaningful
when an observation lies beyond the other period's frontier and are never
clipped to zero. The two component names carry the same noncausal,
reference-conditional interpretation as in the Malmquist result.

The four directional-distance programmes are release inputs, not trustworthy
results merely because a backend labels them `optimal`. Every programme must
pass the solver-neutral LP certificate, and the four released distances must
reconstruct both fixed-reference changes, $L$, $EC_L$, $TC_L$, and
$L=EC_L+TC_L$. A released transition therefore has `score_valid=True`,
`score_status="defined"`, and both LP and economic certificate summaries. If
one task or the additive account fails, the four distances, peer intensities,
components, and headline value are withheld for that transition while the raw
role diagnostics remain available. Other transitions in the same fit remain
independent, and these checks add no solver call.

Global Malmquist analysis uses two global and two contemporaneous distances
per transition, with no cross-period radial program. `productivity_change`
satisfies
`productivity_change = efficiency_change * best_practice_change`.
`technical_change` mirrors `best_practice_change` for the common decomposition
schema, while the explicit field preserves the Pastor--Lovell interpretation.
Here best-practice change means a change in the gap between the declared
global and contemporaneous reference technologies, not a causal claim about
innovation. The summary retains base/comparison global efficiencies and
best-practice gaps; diagnostics and peers label `global` versus
`contemporaneous` references.

Oh Global Malmquist--Luenberger analysis uses the analogous four result roles
under its fixed-input CRS common-factor environmental technology:
`base_on_base`, `comparison_on_comparison`, `base_on_global`, and
`comparison_on_global`. Each task is self-inclusive, so its directional
distance is nonnegative up to numerical tolerance; there are no off-diagonal
cross-period distance roles. `efficiency_change` records change in the
contemporaneous operating shortfall. The source-native
`base_best_practice_gap` and `comparison_best_practice_gap` equal
$(1+D^{r})/(1+D^G)\in(0,1]$; a value closer to one means the contemporaneous
opportunity is closer to the retrospective global benchmark.
`best_practice_change` is comparison gap divided by base gap.
`technical_change` mirrors it only for the common result schema: it is not the
conventional Chung--Färe--Grosskopf technical-change component and is not a
causal claim about innovation or policy. Results enumerate matched adjacent
transitions, while metadata records the fixed global sample vintage on which
their circular chaining depends.

Both the adjacent CFG ML and Oh GML routes treat their four environmental
distance programmes as release inputs. Every task must pass the solver-neutral
LP certificate plus its source production-account reconstruction, and the
published factors must pass the relevant complete multiplicative account.
`score_valid`, `score_status`, `postsolve_certified`,
`economic_postsolve_certified`, and `multiplicative_account_certified` expose
those gates. A failed task withholds the headline, components, four published
distances, and transition-level peer rows without affecting another transition.
`peer_valid` is independent: a reporting threshold can invalidate the displayed
peer reconstruction while leaving a certified productivity account available.
Role diagnostics preserve raw backend evidence, and metadata records that these
checks add zero solver calls.

Biennial Malmquist uses the same pooled-reference result schema, but each
transition pools only its base and comparison periods. The explicit component
is `biennial_gap_change`; it is also available as `best_practice_change` and
`technical_change`. Base/comparison `biennial_gap` and `biennial_efficiency`
fields make the identity auditable. It describes the opportunity-set comparison
created by that declared two-period reference construction. Diagnostics attach
the exact two-element `technology_periods` tuple to every biennial solve.
