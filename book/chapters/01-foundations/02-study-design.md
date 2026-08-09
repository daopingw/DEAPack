# Designing a Credible DEA Study: Who Can Learn from Whom?

Imagine the first meeting of a regional health authority that wants to compare
hospitals. The spreadsheet appears reassuringly complete: staffing, beds,
treated cases, adverse events, teaching status, emergency obligations, and
characteristics of the local population. It would take only a few lines of
code to turn some of those columns into a DEA score.

Yet the spreadsheet cannot decide what the authority means by performance. A
teaching hospital may appear to use too many resources because its training
mission was omitted. A rural hospital may appear inefficient because travel
time and minimum-service obligations were treated as managerial choices. A
hospital may appear to improve quality because an adverse event was entered as
an ordinary input, even though the study never explained how care and harm are
jointly produced. In each case the arithmetic can be faultless while the
economic comparison is wrong.

The first task is therefore not to choose CCR, BCC, SBM, or another acronym.
It is to define a comparison that an economist, manager, clinician, and data
owner would all recognize as the same study. Cook, Tone, and Zhu describe this
as work that must occur prior to choosing a DEA model; practical DEA protocols
likewise place unit definition, variable choice, comparability, and
sensitivity at the centre of the analysis
{cite:p}`cook2014model,dyson2001`.

Before the first model is fitted, the researcher should be able to explain in
ordinary organizational language what each hospital is responsible for, what
it must preserve, what it could reasonably change over the stated horizon,
and which other hospitals provide relevant evidence. These judgments define
the performance question. The later optimization makes their implications
explicit; it cannot make the judgments on the researcher's behalf.

```{figure} ../../_static/figures/study-composition-map.svg
:name: fig-study-composition-reader
:alt: Purpose and commitments, organizational responsibility and time, and comparable evidence shape a study design that produces a performance finding, operating evidence, and a bounded conclusion
:width: 100%

A defensible study moves from the organization's purpose and production
boundary to an explicit comparison design. Scores and targets emerge from
that design; they cannot substitute for it.
```

## Begin with the decision the organization actually faces

Suppose the authority's immediate question concerns annual resource
stewardship in district general hospitals:

> Could each hospital have delivered its risk-adjusted volume of completed
> care with fewer controllable clinical resources, relative to hospitals with
> a comparable service mandate?

Every phrase in this question restricts the claim the authority will later be
entitled to make.

- The hospital site, rather than an individual department, is provisionally
  the organization whose stewardship is being evaluated.
- Completed care is a service commitment to be protected rather than an amount
  the authority is presently asking hospitals to reduce.
- Clinical resources are treated as quantities that management could adjust
  over the stated horizon.
- The evidence must come from hospitals with comparable service mandates.
- The result is a relative operating benchmark, not an estimate of the effect
  of a management intervention.

Change the board's decision and the study changes. A short-run staffing review
may hold installed beds fixed. A capacity plan may allow staffing to adjust
while asking what those beds could support. A quality programme may seek more
completed care and fewer adverse events together. A service redesign may need
to open the hospital and represent intake, diagnosis, treatment, and follow-up
as connected processes. These are different economic accounts of what the
organization can change and what society asks it to deliver; they are not
alternative wordings of one score.

The decision horizon matters as much as the organizational purpose. Beds may
be fixed during next month's rostering exercise but adjustable in a ten-year
capital plan. A minimum emergency service may be a binding obligation for the
current contract but negotiable in a future commissioning round. Calling a
quantity “controllable” without naming the responsible decision maker and
time horizon leaves the performance question unfinished. DEA does not discover
managerial discretion from the data: it evaluates the discretion that the
study has declared.

## Where does one hospital begin and end?

The decision-making unit, or DMU, is an economic boundary rather than merely a
row label. It identifies the organization, activity, or operating history to
which resources and services will be attributed. Ideally that boundary also
matches a meaningful locus of responsibility: someone should be able to
explain the operating choices represented inside it. For the health authority,
“hospital” could mean at least four different things:

| Possible unit | What lies inside the production account | Question it could support |
|---|---|---|
| complete hospital site | all represented clinical resources and final care outcomes | overall site resource stewardship |
| clinical pathway | intake, diagnosis, treatment, and follow-up for a defined patient group | pathway performance across organizational departments |
| hospital-year | one site's resources and services during one reporting period | contemporaneous efficiency; a linked panel of comparable hospital-years can support productivity change |
| hospital trajectory | several years joined by capacity, waiting lists, or other inherited states | performance of one intertemporally feasible operating history |

The choice determines what counts as an input, output, internal handoff, or
state. A legal entity is not automatically the right production boundary. If
laboratory services are purchased from another organization, their cost or
quantity should not disappear simply because the laboratory is outside the
hospital's legal boundary. If one hospital records referred patients as
completed episodes while another removes them from both resources and
outcomes, their rows do not describe the same production unit.

Good boundaries also prevent double counting. A diagnostic result can be a
final service in a diagnostic-centre study. Inside a complete hospital
pathway it may instead be an intermediate service handed to treatment. A
waiting list can be an undesirable end-of-year burden in one static account,
but when the same cases become next year's opening obligation it is more
naturally represented as a carry-over. The spreadsheet value has not changed;
its economic role has. The same quantity should not be rewarded once as an
internal handoff and again as final care unless the production account can
justify both roles.

For repeated observations, the identity rule must be equally clear. A
hospital merger, split, service transfer, or coding-system change may break
the continuity of the apparent hospital name. A mechanical match of identical
labels can therefore compare different organizational entities. Conversely,
a renamed hospital may remain the same production unit. The researcher needs
an economic continuity rule, not just a text-matching rule.

## A column acquires meaning from the production story

Once the unit is defined, each column must be assigned an economic role within
that boundary and horizon. For hospital $j$, the book writes resources as
$x_j$, desirable services and outcomes as $y_j$, and jointly produced burdens
as $b_j$. These symbols do not classify a column by its name or by whether a
large value looks attractive. They record the role that the study can defend.

Consider the variables available for the hospital study.

| Recorded quantity | Plausible role in the annual study | Question that must be settled first |
|---|---|---|
| clinical staff hours | controllable input | Are agency and contracted hours measured on the same basis at every site? |
| staffed bed-days | input or quasi-fixed resource | Can management alter staffed capacity over the stated horizon? |
| risk-adjusted completed episodes | desirable output | Does the adjustment preserve comparable definitions of severity and completion? |
| avoidable inpatient harm events | undesirable output | Is harm jointly generated within the hospital boundary, and how may it be reduced? |
| teaching mandate | mission or operating condition | Is training itself a measured output, or does the mandate define a different comparison group? |
| population deprivation | contextual condition | Does it change attainable care opportunities, and is it outside hospital control? |
| rural travel time | operating environment | Does remoteness impose a minimum-service configuration or a distinct technology? |
| year-end waiting list | final burden or intertemporal state | Is the study static, or does today's backlog become tomorrow's obligation? |

Four distinctions are especially important.

First, an input is a resource used within the declared production boundary,
not simply a variable that management would like to reduce. A subsidy, a
deprivation index, or a statutory obligation may affect the organization's
opportunities without being a consumed resource. An input-oriented question
also implies that the represented input can be adjusted over the stated
horizon; otherwise the study should preserve it or describe its restricted
role explicitly.

Second, a desirable output is something the production account values as
delivered, not simply a column whose larger numbers look favourable.
Unadjusted treatment counts can reward low-complexity case selection. Quality
indicators and case-mix adjustment need clinical and measurement
justification before they become production quantities. An output should
represent a service or outcome for which the DMU can meaningfully be held
responsible, rather than a distant social outcome driven mainly by forces
outside its boundary.

Third, an undesirable output is not an ordinary input with an inconvenient
sign. Harm occurs with the delivery of care and may require resources,
foregone activity, or process redesign to reduce. A study that includes harm
must choose an explicit undesirable-output production account. Part III
develops several such accounts because different mechanisms imply different
attainable improvements.

Fourth, an uncontrollable environment is not automatically a
non-discretionary input. Deprivation, remoteness, regulation, and teaching
status can affect comparison opportunities without being resources consumed
in production. Entering them mechanically as inputs can reward an
organization for “using more” of an adverse condition and may assert a
monotonic production relation that has no economic basis. Possible responses
include a defensible peer screen, declared groups and a metafrontier,
conditional frontier methods, or a separate contextual analysis. They answer
different questions and should not be chosen after seeing which gives the
preferred ranking. The governing question is whether the condition changes
the attainable opportunity set, the organization's distance from a shared
opportunity set, or only the interpretation of the result. Those claims
require different designs.

Ratios require the same discipline. A harm rate combines a numerator and an
exposure denominator. Treating the rate as though it were a freely disposable
quantity can imply operating plans that do not correspond to any attainable
combination of events and cases. When possible, keep the underlying quantities
and the exposure account visible. Prices, expenditures, and physical
quantities also answer different questions: replacing staff hours with wage
cost, for example, changes a resource-use comparison into a value account that
also reflects local prices.

Measurement comparability is part of economic comparability. Two hospitals do
not supply the same evidence if “completed episode” means discharge at one site
and referral at another, if one resource is a stock and the other an annual
flow, or if nominal expenditure spans years with different price levels. Units,
coverage, accounting period, case-mix adjustment, and missing-data treatment
must be reconciled before the rows can be interpreted as operating plans in a
common production account.

## Comparison eligibility is an institutional claim

DEA learns from represented operating practices. Before asking which
combination of those practices could support a benchmark, the study must
decide which observations are institutionally and economically eligible to
teach the focal hospital. This is not a housekeeping choice. It determines the
opportunity set against which performance will be read.

Consider a separate teaching case. Lakeside is an urban district general
hospital without a tertiary trauma mandate. The authority's first
comparison-eligibility ledger might read:

```{list-table}
:header-rows: 1
:widths: 15 40 45

* - Candidate
  - Institutional and measurement record
  - Eligibility decision
* - Lakeside
  - focal district hospital; standard service contract; common coding protocol
  - include under both declared rules; ordinary self-inclusive DEA retains the
    focal observation
* - North and East
  - district hospitals; same standard contract, service boundary, and coding
    protocol
  - include under both declared rules
* - West
  - district hospital with audited definitions but an integrated urgent-care
    contract
  - include only under the broader district-mission rule, and only if prior
    institutional evidence supports transferability
* - Riverside
  - district hospital serving a remote population under minimum-service
    obligations
  - exclude from both rules; reserve for an environment-sensitivity comparison
* - University
  - tertiary referral, research, teaching, and major-trauma mandates
  - exclude from both district-hospital populations
* - South
  - nominally comparable, but uses an unreconciled episode definition
  - exclude until the data audit is resolved
```

Exclusion is not a judgment that Riverside, University, or South is poorly
managed. It says that these two studies cannot use their records as evidence
of what Lakeside could attain under the declared mandate and measurement
system. Riverside may belong in a grouped or conditional comparison.
University may require teaching and tertiary outputs, or a separate
technology. South presents a data problem, not a technology group. West poses
a different question: does its integrated urgent-care contract change the
production opportunity relevant to Lakeside, or is the difference compatible
with learning across a shared district mission? Institutional evidence, not a
preferred score, must answer that question.

The rules should be stated before scores are inspected. Removing an
inconvenient peer after it creates a demanding benchmark changes the economic
question and the estimated frontier at the same time. A useful study record
therefore retains every observation considered, its eligibility decision, the
reason for that decision, and the institutional or empirical evidence on
which it rests. A sensitivity analysis may compare two defensible rules, but
it should not reverse-engineer a rule from the desired ranking.

Three groups of organizations must now be kept separate. The **candidate
roster** contains every record examined during the data and institutional
audit. The **eligible reference population** contains only the records that
pass the rule declared for the study. The model then selects an **active peer
plan** from that eligible population: only observations with positive fitted
intensities contribute to the selected comparator. Eligibility is therefore
an analyst's prior institutional decision; active peers are a result. An
eligible hospital need not become an active peer, and the optimization cannot
rescue a hospital that the study has already declared ineligible.

In the unified notation, only eligible observations enter the reference
matrices $X$, $Y$, and, when burdens are represented, $B$. For the focal
hospital $o$, positive values of $\lambda_j$ identify the eligible hospitals
that contribute to the selected comparator plan. A zero $\lambda_j$ does not
mean that hospital $j$ was irrelevant to the study: its presence may still
shape the frontier or become active for another hospital. Nor does a positive
$\lambda_j$ prove that its practices are transferable. It says only that its
represented resource--service bundle contributes to this model-supported
comparison.

The distinction becomes visible if the authority holds Lakeside's recorded
operation fixed and states two policies before fitting the model. A strict
same-contract rule admits Lakeside, North, and East. It gives Lakeside an
input-oriented VRS radial score of 0.9375, with North supplying the selected
active peer evidence. Suppose the authority also adopts a broader
district-mission rule after documenting an ex-ante institutional-comparability
review. That rule admits West. Lakeside's score becomes 0.9028, supported by a
fitted plan combining North and West. Nothing about Lakeside's recorded
resources or completed care changed; the admitted evidence changed. In
management terms, the two scores represent common proportional
resource-saving opportunities of 6.25 percent and 9.72 percent, respectively,
while protecting the recorded completed-care commitment and before any slack
completion.

```{figure} ../../_static/figures/peer-eligibility-sensitivity-result.svg
:name: fig-peer-eligibility-sensitivity
:alt: Lakeside has the same recorded clinical hours, bed-days, and completed episodes under two pre-declared eligibility rules. A same service-contract rule admits three hospitals and gives Lakeside a 6.25 percent common proportional resource-saving opportunity, represented by a radial score of 0.9375, with North as its active peer. A shared district-mission rule also admits West and gives Lakeside a 9.72 percent opportunity, represented by a score of 0.9028, with North and West as active peers. Both opportunities protect 100 completed episodes and precede slack completion. A final box states that the difference is conditional and noncausal.
:width: 100%

Lakeside's observed operation does not change. The common proportional
resource-saving opportunity rises from 6.25 percent to 9.72 percent--a 3.47
percentage-point sensitivity to the pre-declared eligible population. It
neither estimates a causal contract effect nor tests whether West's practices
will transfer or whether Lakeside's management is inferior.
```

Neither rule is automatically correct. The narrow rule asks what Lakeside can
learn from hospitals under the same service contract. The broader rule asks
what it can learn across a shared district mission after the authority has
documented why West is institutionally comparable for this study. That review
must be completed before West's fitted intensity is known; excluding West only
after it becomes a demanding peer would be result-driven design. Whether a
practice will transfer in implementation remains a separate question. The
ordinary BCC account in the figure protects completed episodes but does not
include harm, so it cannot support a quality conclusion. Because the fits
request only the radial score, neither makes a Pareto--Koopmans or
slack-completed target claim.

The difference therefore belongs in a sensitivity analysis, not a table of
causal effects. No contract was assigned to Lakeside and no hospital changed
its behaviour; only the body of evidence admitted to the comparison changed.

### Repeated peer selection is an audit lead, not a trophy

After the eligible population has been fixed, the authority may ask whether
the same organization keeps appearing in the comparator plans chosen for
different hospitals. A recurring peer has **comparative reach** in this sample:
its observed resource--service mix helps the model describe feasible
improvements for several organizations. That makes it a useful place to begin
an audit of data quality and operating practice. It does not make the peer a
winner.

Reference frequency simply counts appearances in the selected comparator
plans. Self-use is shown separately because an efficient organization will
often select itself in ordinary self-inclusive DEA. The more informative
question is how often an organization contributes to plans for *other*
organizations. Adding the fitted intensity values across different plans would
not improve this diagnostic; each intensity belongs to a different comparison
and has no common unit across hospitals.

The eight-organization service case in {numref}`fig-reference-frequency-reader`
uses the book's `slacks_2x2` teaching data and an input-oriented BCC fit.
Organizations A--D lie on the fitted boundary. C appears in its own plan and
in four plans for other organizations; B appears in its own and three others.
D appears once for another organization, while A appears only for itself. B
and C therefore have wider comparative reach in this particular fit. The
count tells the authority where to investigate, not what it will find there.

```{figure} ../../_static/figures/reference-frequency-result.svg
:name: fig-reference-frequency-reader
:alt: Horizontal stacked bars separate self-reference from selection by other organizations for eight service organizations. A appears only in its own plan, B is selected by three others, C by four others, D by one other, and E through H do not appear in the selected plans.
:width: 100%

Repeated selection identifies comparative reach in one fitted sample. It is a
prompt to investigate measurement quality and possible practice
transferability, not a ranking of management quality.
```

The same audit can be reproduced directly from the fitted result:

```python
from deapack import BCC, DEAData, dataset_info, load_dataset

service_frame = load_dataset("slacks_2x2")
service_roles = dataset_info("slacks_2x2").roles
service_data = DEAData.from_frame(
    service_frame,
    dmu=service_roles["dmu"],
    inputs=service_roles["inputs"],
    outputs=service_roles["outputs"],
)

service_result = BCC(
    orientation="input",
    compute_slacks=False,
).fit(service_data)
frequency = service_result.reference_frequency()
frequency.reference_frame[
    [
        "reference_dmu_id",
        "self_reference_frequency",
        "other_reference_frequency",
    ]
]
```

The four boundary organizations all have a radial score of one, yet their
frequencies differ. Frequency is therefore neither another efficiency score
nor a quality-adjusted league table. E--H do not appear in the plans shown, but
they remain eligible evidence and could matter under another defensible model
or another equally good comparator plan. A high count likewise says nothing by
itself about superiority, causation, or whether a practice can be transferred
to a hospital with a different workforce, mission, regulation, or service
obligation.

The sensible next step is investigation rather than an award. Verify the
recurrent organization's data and variable roles, study the practices behind
its resource--service mix, and ask whether they are institutionally comparable
and transferable. Then test whether the substantive finding survives peer and
model sensitivities chosen in advance. Deleting a hospital merely because it
is a demanding recurrent peer would redefine the study after seeing the
answer.

Eligibility also has a dimensional consequence. The full data-role declaration
below contains two inputs, one desirable output, one undesirable output, and
only three same-contract hospitals. The two score comparisons deliberately
leave harm outside the radial account and contain only three or four eligible
hospitals. Neither setup is large enough for a persuasive empirical frontier.
Additional variables often make more observations appear
efficient because each organization gains another dimension in which to
distinguish itself. A larger model is not automatically a richer explanation.
Theory, measurement quality, sample support, and stability should determine
whether a variable remains.

Sample size is therefore not a purely numerical hurdle. The relevant support
comes from comparable observations that occupy informative parts of the
resource--service space. Hundreds of hospital-years do not provide hundreds
of independent organizational comparisons if they repeat a small number of
sites under nearly unchanged conditions. Conversely, a large administrative
database does not repair a thin eligible comparison population for a
specialized hospital.
The empirical question is whether the eligible evidence can support the
frontier and the distinctions the study asks it to make.

At this point the authority should be able to tell one coherent story without
referring to a score: who is accountable, over what period, for which resources
and services; which burdens are jointly produced; which conditions lie beyond
managerial control; how every quantity is measured; and why each eligible
hospital supplies relevant evidence. It should also be able to say what kind
of conclusion the evidence could support. If any answer depends on seeing
which specification produces the most convenient result, the study is not yet
ready to be fitted.

## Make the economic account visible in the data

The following teaching data are deliberately small. They show how the
authority's economic account and eligibility rule become visible in code;
they are not offered as an adequate hospital study. Notice that the complete
candidate roster is retained even though only eligible rows enter the DEA
comparison.

```python
import pandas as pd

from deapack import DEAData

hospital_frame = pd.DataFrame(
    {
        "hospital": [
            "Lakeside",
            "North",
            "East",
            "West",
            "Riverside",
            "University",
            "South",
        ],
        "clinical_hours": [120, 110, 130, 105, 115, 240, 108],
        "staffed_bed_days": [80, 75, 85, 70, 82, 160, 74],
        "risk_adjusted_episodes": [100, 105, 112, 96, 98, 210, 101],
        "avoidable_harm_events": [6, 4, 5, 3, 7, 8, 5],
        "mission": [
            "district",
            "district",
            "district",
            "district",
            "district",
            "tertiary",
            "district",
        ],
        "service_contract": [
            "standard",
            "standard",
            "standard",
            "integrated_urgent_care",
            "minimum_service",
            "tertiary_referral",
            "standard",
        ],
        "operating_environment": [
            "urban",
            "urban",
            "urban",
            "urban",
            "remote",
            "urban",
            "urban",
        ],
        "common_episode_definition": [
            True,
            True,
            True,
            True,
            True,
            True,
            False,
        ],
    }
)

district_mission_eligible = (
    hospital_frame["mission"].eq("district")
    & hospital_frame["operating_environment"].eq("urban")
    & hospital_frame["common_episode_definition"]
)
same_contract_eligible = (
    district_mission_eligible
    & hospital_frame["service_contract"].eq("standard")
)
same_contract_frame = hospital_frame.loc[same_contract_eligible].copy()

role_declared_data = DEAData.from_frame(
    same_contract_frame,
    dmu="hospital",
    inputs=["clinical_hours", "staffed_bed_days"],
    outputs="risk_adjusted_episodes",
    bad_outputs="avoidable_harm_events",
)

(
    role_declared_data.input_names,
    role_declared_data.output_names,
    role_declared_data.bad_output_names,
)
```

The declaration makes several conceptual mistakes harder to hide. Each
organization must have a unique identity, its production quantities must be
measured consistently, and one quantity cannot simultaneously play
conflicting economic roles. Keeping the role names visible also helps managers
connect later results to the original resource, service, and harm account.

It does not complete the study. The data declaration cannot decide whether
harm is strongly or weakly disposable, whether inputs should contract,
whether VRS or CRS is credible, or why the retained hospitals may be
compared. `same_contract_eligible` records an explicit research decision made
before performance is calculated; it is not an active-peer result learned
from favourable scores. The context columns remain in `hospital_frame` so
that the institutional explanation for inclusion and exclusion stays visible,
rather than being silently converted into production inputs.

`role_declared_data` contains avoidable harm by design. An ordinary `BCC` fit
will stop with a specification error rather than silently decide how that harm
can be disposed. The next block deliberately constructs a narrower
resource--service account for the ordinary BCC comparison. It leaves harm
outside that score; it does not turn harm into an input or authorize a quality
conclusion.

The figure's two narrow resource accounts can be reproduced without turning
mission or environment into inputs. Each declared population gets its own
`DEAData` object, while the complete candidate roster remains available for
substantive review:

```python
from deapack import BCC

quantity_columns = [
    "hospital",
    "clinical_hours",
    "staffed_bed_days",
    "risk_adjusted_episodes",
]


def fit_declared_population(eligible):
    comparison_frame = hospital_frame.loc[eligible, quantity_columns].copy()
    comparison_data = DEAData.from_frame(
        comparison_frame,
        dmu="hospital",
        inputs=["clinical_hours", "staffed_bed_days"],
        outputs="risk_adjusted_episodes",
    )
    return BCC(
        orientation="input",
        compute_slacks=False,
    ).fit(comparison_data)


same_contract_result = fit_declared_population(same_contract_eligible)
district_mission_result = fit_declared_population(district_mission_eligible)

same_contract_result.summary().set_index("dmu_id").loc["Lakeside", "score"]
district_mission_result.summary().set_index("dmu_id").loc["Lakeside", "score"]
district_mission_result.peers("Lakeside")
```

The two fitted comparisons return 0.9375 for Lakeside under the same-contract
population and 0.902778 under the district-mission population. For this
input-oriented radial account, the score is the common resource-retention
factor. Its complement therefore translates the first result into a 6.25
percent common proportional resource-saving opportunity and the second into a
9.72 percent opportunity, in both cases while protecting completed episodes.
These are phase-one opportunities before slack completion, not instructions
to cut either resource by that amount.

In the latter fit, the positive intensities are $4/9$ for North and $5/9$ for
West. Those intensities identify the selected phase-one comparator; they do
not establish a completed target, prove that West's contract has no
operational consequence, or prescribe copying either hospital. Scores from
the two eligibility rules should be reported side by side, not averaged into
a supposedly more robust number. The side-by-side account preserves the
substantive reason the estimates differ.

In a real project, the variable record should also retain units, time basis,
source system, transformations, missing-data policy, quality checks, and the
managerial owner of each quantity. “Staff” is not a sufficient definition if
one hospital reports paid full-time equivalents and another reports worked
hours including agency staff. Nor is “annual” sufficient if financial years,
calendar years, and rolling twelve-month windows are mixed.

## Only then choose the method family

Once the boundary, roles, horizon, and eligible population are credible, the
board's question can be matched to a model. Orientation should protect the
declared commitment and place adjustment on quantities the responsible manager
can change. Returns to scale state whether proportional replication is treated
as attainable and whether managers are being held responsible for operating
scale. Neither choice should be made because it produces a more appealing
league table.

If the study excludes harm and asks how much controllable resource could be
saved while preserving completed care, an input-oriented radial or nonradial
model may be a natural starting point. The next chapter shows how eligible
observations become an empirical production technology under assumptions
about mixing, disposal, and scale.

Keep the strict same-contract rule fixed and the board can ask several useful
questions without changing who is allowed to supply evidence. A radial account
asks whether Lakeside could reduce both controllable resources at one common
rate while protecting completed care. A slacks-based account asks whether the
shortfall is uneven--perhaps bed-days can be reduced more than clinical hours,
or an additional service gain remains after one resource has stopped
improving. A directional account asks whether a programme agreed in advance,
such as saving a stated number of clinical hours and bed-days while adding a
stated number of completed episodes, is attainable as a package. Lakeside,
North, and East remain the admitted evidence in all three accounts; the model
may select different active comparator plans because the operating commitments
differ.

These are not three votes on one hidden notion of performance. The radial
finding concerns a common percentage, the slacks-based finding concerns
resource- and service-specific gaps, and the directional finding concerns the
declared programme. Holding the comparison-right rule constant helps the board
see that differences come from the management question rather than an
unannounced change of comparison population. None of the three findings proves
that an admitted hospital is superior, that its practices caused the gap, or
that its operating arrangements can be transferred to Lakeside.

If harm remains part of the conclusion, an ordinary BCC technology is not the
same study with one extra column. The analysis must move to Part III and
declare how desirable care and harm are jointly attainable and reducible. If
diagnosis, treatment, and discharge must agree on internal patient flows, a
network model in Part V represents that organizational structure. If waiting
lists, capacity, or obligations connect years, Part VI treats the hospital as
an operating history. If rural and urban hospitals face distinct opportunity
sets, Part VII separates within-group performance from the gap between
represented group opportunities.

This is not an automatic model selector. The production story still has to
justify the maintained assumptions. The map simply helps prevent a technical
setting from silently changing the management question.

## Read the eventual score inside its comparison contract

Suppose a later model reports that Lakeside could retain only 90 percent of
its controllable resources while preserving completed care. A
responsible statement would identify the conditions:

> Relative to the eligible district hospitals measured under the common
> episode definition, and under an input-oriented VRS production
> technology, Lakeside's benchmark supports a ten-percent common reduction in
> controllable resources while preserving its recorded
> risk-adjusted completed-care commitment.

The sentence is intentionally narrower than “Lakeside should cut its budget by
ten percent.” DEA has not priced the transition, established a causal
management failure, measured unrecorded aspects of care quality, or shown that
the comparator plan can be implemented locally. Peers explain why the model
treats a plan as attainable and may point toward organizational learning; they
are not instructions to imitate every practice.

Targets require the same caution. A target may combine several hospitals'
activities under convexity. That combination is evidence about attainable
resource--service quantities only when divisibility or portfolio mixing is
credible. It is not a literal proposal to merge hospitals. Several optimal
targets may support the same score, and engineering, workforce, legal, and
political constraints can distinguish an implementable plan from a
model-supported benchmark. DEA can identify the size and composition of a
benchmark opportunity; implementation analysis asks how, at what cost, and
under whose authority it could be pursued.

The most useful management interpretation therefore keeps four layers
visible:

- the study design--unit boundary, horizon, eligible comparison population,
  variable roles, and production assumptions;
- the performance finding--the defined measure, its direction, and the
  comparison it supports;
- the operating evidence--targets, shortfalls, peers, and any alternative
  optima; and
- the conclusion boundary--what remains unmeasured, uncertain, or outside
  managerial control.

## From a sample benchmark to a research conclusion

Suppose Lakeside's score is available to ten decimal places. Those decimals
describe the comparison defined by these hospitals, variables, and production
assumptions. They do not establish that the same frontier would appear in
another credible sample, after a measurement revision, or in the wider
population of hospitals. DEA constructs its frontier from a finite set of
observed practices, so sampling variation and the identity of the eligible
reference population remain part of the evidence
{cite:p}`simar1998,simar2000,kneip2008`.

An unusually strong hospital may therefore have considerable influence on
many results. Influence is not proof of error: the hospital may demonstrate a
genuinely transferable practice. Nor should an inconvenient observation be
removed merely because it creates demanding targets. The sensible response is
to check its source data and units, reconsider its eligibility against the
study design chosen in advance, and then show how important conclusions
change under defensible alternative eligible populations. If one valid hospital
determines much of the frontier, the study should describe that sparse support
rather than conceal it behind extra decimal places. If the record is erroneous
or institutionally incomparable, its correction or exclusion is a data or
design decision and should be explained as such {cite:p}`dyson2001`.

It helps to distinguish four levels of claim:

| Claim | What the study needs |
|---|---|
| **Conditional sample benchmark** | a correctly specified DEA comparison and a fully stated study design |
| **Stable empirical finding** | data-quality checks and pre-specified sensitivity to influential observations, variables, and the eligible comparison population |
| **Population statement** | an explicit sampling model and an inferential procedure valid for the chosen frontier estimator |
| **Causal management statement** | a separate identification design showing what would happen under an intervention |

The last two levels do not follow automatically from the first. Bootstrap
methods can quantify particular forms of sampling uncertainty and
finite-sample bias, but only under a stated data-generating process and
conditions appropriate to the estimator. They are not a universal resampling
switch, and their confidence intervals do not absorb coding errors, omitted
outcomes, or an indefensible peer definition.

Contextual conditions require one further distinction. Deprivation or rural
remoteness may change the production opportunities available to a hospital;
alternatively, hospitals may share one opportunity set while such conditions
are associated with how close they operate to it. The first account calls for
a design that changes or conditions the frontier--for example, justified peer
groups, a metafrontier, or a conditional frontier. A second-stage analysis
addresses a different question and relies on a separability assumption that
the contextual variables do not themselves alter the attainable boundary
{cite:p}`daraio2005,simar2007`.

For this reason, regressing estimated DEA scores mechanically on contextual
variables with ordinary least squares or Tobit is unsafe. The scores are
jointly generated by the same estimated frontier, have finite-sample bias,
and are not made into independent observations merely because they lie in a
bounded interval. A statistically coherent second stage must state its data-
generating process and justify its inferential procedure. Even then, an
association between remoteness and efficiency is not the causal effect of
remoteness, funding, or management. Causal language requires assumptions and
evidence beyond the DEA comparison.

Sensitivity analysis should vary defensible assumptions, not search for a
preferred conclusion. For the hospital study, the authority might compare a
core urban cohort with a pre-specified environment-sensitive design, examine
whether bed-days are adjustable over alternative horizons, and test whether
the result survives justified case-mix and quality definitions. Each version
should retain its own interpretation; averaging their scores would not remove
the underlying disagreement.

The next chapter begins where this design work ends. Given a set of eligible
organizations and production quantities, it asks which additional
operating plans the observed evidence should make attainable. Convexity,
disposability, and returns to scale will turn the eligibility ledger into an
empirical production technology--and will make clear why choosing the
comparison population was already part of the economic model.
