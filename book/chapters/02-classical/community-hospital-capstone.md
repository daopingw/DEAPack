# From Research Question to Evidence: A Community-Hospital Efficiency Study

A regional health authority is preparing its annual service review. Forty-eight
community hospitals provide broadly similar inpatient and outpatient care, yet
their staffing and operating expenditure differ markedly. The authority does not
want a league table. It wants to know where current services appear to be delivered
with more resources than comparable practice would require, which hospitals offer
useful operational lessons, and which conclusions remain credible when reasonable
study choices are changed.

This chapter follows that question from raw records to a decision-ready result. The
data are synthetic, so no real provider is being judged, but the research choices
are the ones an applied team must make: define the service being studied, decide
who is genuinely comparable, choose quantities that have a defensible production
meaning, estimate a primary model, examine peers and improvement quantities, and
test the findings against plausible alternatives. The primary analysis is
input-oriented BCC. VRS SBM, a broader hospital roster, and the CCR--BCC scale
comparison are used only to learn how dependent the findings are on the first
specification.

## Begin with the decision, not the score

The authority's immediate responsibility is resource stewardship. It must protect
the volume and quality of the services currently supplied while asking whether
staff and non-pay expenditure could be lower. That responsibility leads to an
input-oriented measure. Because community hospitals differ in size and the study
does not assume that every operating pattern can be proportionally replicated,
variable returns to scale is the main assumption. Together these choices lead to
BCC-I {cite:p}`banker1984`.

For hospital $o$, the fitted value $\theta_o$ is the smallest common share of its
three inputs needed to support at least its two current service outputs within the
observed opportunities of the comparison group. A value of 0.90 therefore means
that comparable practice supports the current services with 90 percent of each
input before any remaining input-specific excess is considered. It does not mean
that ten percent of every budget line can be removed tomorrow. Actual savings
depend on clinical constraints, input-specific gaps, local costs, and the ability
to adopt the practices behind the comparison.

The management question fixes the roles of the five production variables:

| Role | Quantity | Why it belongs in the study |
|---|---|---|
| Input | Clinical full-time-equivalent staff | Direct clinical labour committed to service delivery |
| Input | Support full-time-equivalent staff | Operational and administrative labour supporting care |
| Input | Non-pay operating expenditure, £ million | Recurrent supplies and services used during the year |
| Output | Quality-adjusted discharges | Inpatient activity adjusted for case mix and a quality factor |
| Output | Outpatient encounters | Ambulatory services completed during the year |

The quality adjustment is intentionally modest: it prevents a hospital from looking
productive merely because it records many discharges while receiving no recognition
for the quality dimension included in the data. It is still only a summary measure.
A real study would examine coding consistency, risk adjustment, waiting times,
readmissions, and other outcomes before treating these hospitals as comparable.

## Build the comparison group before seeing performance

The source file contains 64 hospitals for one financial year. Some records are
unsuitable for the main study because reporting is incomplete, activity changed
under a structural break, or the hospital has a specialist or teaching-referral
mission. Four district-general hospitals also have a referral share between 15 and
25 percent. They are plausible comparators, but their wider tertiary role may raise
resource needs that are not fully measured. The main study excludes them; a later
sensitivity analysis admits them.

```python
import numpy as np
import pandas as pd
from pathlib import Path

from deapack import (
    BCCInput,
    DEAData,
    SBM,
    dataset_info,
    load_dataset,
    scale_efficiency,
)

dataset_name = "community_hospital_capstone"
raw = load_dataset(dataset_name)
roles = dataset_info(dataset_name).roles
production_columns = (*roles["inputs"], *roles["outputs"])
```

Screening is written as a sequence so that every exclusion can be counted and
reviewed. No efficiency estimate enters these rules.

```python
usable = (
    raw["reporting_complete"]
    & ~raw["structural_break"]
    & np.isfinite(raw.loc[:, production_columns]).all(axis=1)
    & raw.loc[:, production_columns].gt(0.0).all(axis=1)
)
district_general = usable & raw["service_mandate"].eq("district_general")
main_rule = district_general & raw["tertiary_referral_share"].le(0.15)
broad_rule = district_general & raw["tertiary_referral_share"].le(0.25)

screening = pd.Series(
    {
        "Raw hospital records": len(raw),
        "Usable production records": int(usable.sum()),
        "District-general hospitals": int(district_general.sum()),
        "Main comparison group": int(main_rule.sum()),
        "Broad sensitivity group": int(broad_rule.sum()),
    },
    name="hospitals",
)
main_frame = raw.loc[main_rule].reset_index(drop=True)
broad_frame = raw.loc[broad_rule].reset_index(drop=True)
screening
```

```{figure} ../../_static/figures/community-hospital-screening.svg
:name: fig-community-hospital-screening
:alt: Sixty-four raw hospital records become sixty usable records, fifty-two district-general hospitals, and a forty-eight-hospital main comparison group
:width: 96%

The study population narrows for substantive reasons before performance is
estimated. The four borderline-referral hospitals return only in a pre-planned
sensitivity analysis.
```

This separation between a candidate roster and a comparison group matters
economically. A highly specialized hospital can make a district hospital appear
better or worse for reasons that reflect mission rather than management. More
observations do not automatically improve a DEA study; observations improve the
study only when they supply credible information about attainable practice for the
organizations being assessed.

## Estimate the resource-stewardship comparison

The screened quantities are now assembled into `DEAData`. The resulting table
contains 48 hospitals, three inputs, and two outputs. With five production
dimensions, the sample is large enough for a useful worked example, although no
universal sample-size formula can replace an examination of comparability and
discriminating power.

```python
main_data = DEAData.from_frame(
    main_frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
)
primary_result = BCCInput().fit(main_data)
primary = primary_result.summary().set_index("dmu_id")

primary_overview = pd.Series(
    {
        "Hospitals": len(primary),
        "Mean efficiency": primary["efficiency"].mean(),
        "Median efficiency": primary["efficiency"].median(),
        "Lowest efficiency": primary["efficiency"].min(),
        "Hospitals at one": int(np.isclose(primary["efficiency"], 1.0).sum()),
    }
)
primary_overview
```

```{figure} ../../_static/figures/community-hospital-performance.svg
:name: fig-community-hospital-performance
:alt: Distribution and ordered hospital values for input-oriented BCC efficiency in the forty-eight-hospital main comparison group
:width: 100%

Most hospitals lie relatively near observed best practice, but the variation is
large enough to separate modest review priorities from substantial ones. A value of
one means that this sample and specification reveal no supported input saving; it is
not proof that the hospital has no waste.
```

The median hospital retains 96.3 percent of its input bundle in the common
proportional comparison. Twelve hospitals score one, while the lowest score is 0.831.
This is useful portfolio information: the authority can distinguish hospitals that
warrant an early operational review from those for which the current model finds
little scope. It should not publish the values as an unqualified ranking. Differences
may also reflect omitted case severity, local labour markets, estate constraints, or
measurement error.

## Turn one score into an operational inquiry

Hospital H048 provides a transparent example. Its two service quantities match
H008, while its clinical staff, support staff, and non-pay expenditure are 18, 12,
and 15 percent higher. The BCC-I score is therefore 0.893. H008 is the sole selected
peer, with weight one.

```python
focus = "H048"
focus_score = primary.loc[focus, "efficiency"]
focus_peers = primary_result.peers(focus)
focus_targets = primary_result.targets_for(focus)
focus_slacks = primary_result.slacks.query("dmu_id == @focus")

focus_inputs = (
    focus_targets.query("role == 'input'")
    .assign(supported_reduction=lambda table: 1.0 - table["target"] / table["observed"])
    .loc[:, ["variable", "observed", "target", "supported_reduction"]]
)
focus_score, focus_peers, focus_inputs
```

```{figure} ../../_static/figures/community-hospital-h048-improvement.svg
:name: fig-community-hospital-h048-improvement
:alt: H048 uses H008 as its peer and has supported reductions in clinical staff, support staff, and non-pay operating expenditure while preserving both service quantities
:width: 100%

H048's common proportional resource-retention value is 89.3 percent. Completing the
comparison yields input-specific reductions of 15.3 percent in clinical staff, 10.7
percent in support staff, and 13.0 percent in non-pay expenditure, while both
service quantities are preserved.
```

This result gives the review team a place to start asking questions. It can examine
how H008 organizes rotas, outpatient pathways, procurement, and clinical support;
verify whether the two hospitals face similar case severity and access duties; and
identify which practices are transferable. H008 is evidence that the quantities are
jointly attainable in this dataset, not an instruction to copy its organization.
The target is likewise a feasible benchmark for investigation, not next year's
budget. Staff indivisibilities, safety requirements, adjustment costs, and local
knowledge belong in the decision that follows.

## Learn which conclusions survive alternative readings

A single preferred specification should be accompanied by alternatives that answer
recognizably different but relevant questions. Sensitivity analysis is most useful
when each alternative has a substantive reason; cycling through dozens of models
until one produces an attractive result is not evidence.

### Are the resource gaps uneven across inputs?

The radial score begins with a common percentage reduction. VRS SBM gives more
weight to input- and output-specific gaps relative to each hospital's own quantities
{cite:p}`tone2001`. It is a demanding secondary reading when managers suspect that
excess resources are concentrated rather than proportional.

```python
sbm_result = SBM(returns_to_scale="vrs").fit(main_data)
sbm = sbm_result.summary().set_index("dmu_id")
radial_sbm = pd.DataFrame(
    {
        "BCC-I": primary["efficiency"],
        "VRS SBM": sbm["efficiency"],
    }
)
radial_sbm.loc[[focus]], radial_sbm.corr()
```

Across the 48 hospitals, the two readings are strongly associated (correlation
0.905), and the same twelve hospitals score one. Yet H048 falls from 0.893 to 0.852,
because its resource gaps are not uniform. The BCC result remains the primary answer
to the authority's proportional stewardship question; SBM adds a warning that one
percentage alone understates the unevenness of H048's improvement opportunities.

### Does the comparison group change the finding?

The wider roster admits the four district-general hospitals with tertiary referral
shares between 15 and 25 percent. Nothing about the focal 48 hospitals changes; only
the set of practices allowed to inform their comparison becomes wider.

```python
broad_data = DEAData.from_frame(
    broad_frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
)
broad_result = BCCInput().fit(broad_data)
broad = broad_result.summary().set_index("dmu_id")
roster_sensitivity = pd.DataFrame(
    {
        "Main group": primary["efficiency"],
        "Broad group": broad.loc[primary.index, "efficiency"],
    }
)
roster_sensitivity["change"] = (
    roster_sensitivity["Broad group"] - roster_sensitivity["Main group"]
)
roster_sensitivity.loc[[focus]], roster_sensitivity["change"].describe()
```

```{figure} ../../_static/figures/community-hospital-roster-sensitivity.svg
:name: fig-community-hospital-roster-sensitivity
:alt: Main and broad comparison-group BCC efficiency values for the same forty-eight hospitals, with H048 highlighted
:width: 96%

Admitting four hospitals with a larger referral role makes the benchmark more
demanding for 42 of the 48 main hospitals. H048 moves from 0.893 to 0.865. The
direction is informative, but whether the wider result is more credible depends on
whether referral complexity has been adequately measured.
```

The average change is 3.3 percentage points and the largest is 7.8 points. That is
large enough to report. It also sharpens the research priority: collect better
information on tertiary workload before deciding whether those four hospitals
belong in the main comparison. A stricter list is not automatically fairer, and a
wider list is not automatically more informative.

### How much of the gap is associated with scale assumptions?

Finally, the CCR--BCC ratio compares the input-oriented CRS and VRS results. It asks
how much additional shortfall appears when proportional replication is permitted,
beyond the resource-use gap already observed under VRS.

```python
scale_result = scale_efficiency(main_data, orientation="input")
scale = scale_result.summary().set_index("dmu_id")
scale_reading = scale.loc[
    [focus],
    ["crs_efficiency", "vrs_efficiency", "scale_efficiency"],
]
scale_reading
```

For H048, CRS efficiency is 0.860, VRS efficiency is 0.893, and their ratio is
0.963. Across the sample the median ratio is 0.962. These values show that the CRS
assumption adds a material gap for some hospitals. They do not tell management to
expand, merge, or shrink a hospital. Such choices require local returns-to-scale
evidence, demand forecasts, access objectives, fixed costs, and the feasibility of
changing capacity. The scale chapter develops that interpretation in
{doc}`scale-performance-management`.

## Prepare evidence for a management review

The quantitative study should end in a structured review, not in a spreadsheet of
scores. For each priority hospital the authority can assemble:

- the primary score and the service commitments protected by it;
- input-specific quantities, with physical units and realistic adjustment periods;
- selected peers, together with checks on mission, case mix, quality, and local
  operating conditions;
- results under the SBM, wider-roster, and CRS alternatives;
- data-quality concerns and important activities still omitted from the study; and
- questions for managers and clinicians about why practice differs and what can be
  transferred safely.

DEAPack can package the fitted tables and available figures into one reproducible
file. The bundle is useful for review and replication; the surrounding narrative
must still explain the health-service meaning of every result.

```python
publication_file = primary_result.publish(
    Path("community-hospital-efficiency-study.zip"),
    metric="efficiency",
    dmu_id=focus,
)
publication_file.exists()
```

The main conclusion is deliberately conditional. Within a pre-specified group of
48 district-general hospitals, and for the three resources and two services in this
study, observed practice supports meaningful resource-saving opportunities for a
number of providers. H048 is a clear review candidate, but both its score and the
size of its shortfall change under reasonable alternative readings. The responsible
next step is therefore a focused operational investigation and better information
on referral complexity—not an automatic budget reduction.
