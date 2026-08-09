# Comparing Organizations across Different Operating Environments

Suppose two hospitals use the same categories of labor, beds, and equipment
to provide the same categories of care. One can recruit from a large labor
market, refer difficult cases to nearby specialists, and rely on mature
transport and digital infrastructure. The other serves a remote population,
has limited referral capacity, and faces persistent staffing constraints.
The hospitals share a mission, but they may not face the same production
opportunities.

A single comparison can then be misleading in either direction. Benchmarking
each hospital only against nearby peers respects its operating environment,
but conceals how far that environment lies from the strongest opportunities
observed elsewhere. Benchmarking every hospital against one common frontier
creates comparability, but risks presenting an opportunity disadvantage as
poor local performance.

Metafrontier analysis retains both standards. The within-group comparison asks how
well an organization uses the opportunities available under its own infrastructure,
mandate, or production system. The broader comparison then asks how those locally
available opportunities compare with the strongest possibilities observed across all
groups. Developed for firms operating under different technologies or production
environments, the decomposition separates an organization's operating shortfall from
an opportunity disadvantage associated with its group
{cite:p}`odonnell2008`.

This is useful whenever groups have an economic meaning established before
estimation: countries with different infrastructures, hospitals with
different service mandates, farms using different production systems, or
plants subject to different regulatory regimes. A group is not simply a
cluster that happened to emerge from the efficiency results. If group labels
are chosen after examining the scores, the decomposition becomes an
explanation constructed from the outcome it is meant to explain.

```{admonition} Known groups are not discovered groups
:class: note

This chapter begins with an institutional classification fixed before the
frontiers are estimated. Clustering instead asks the data to discover groups;
a conditional frontier asks how represented opportunities vary with observed
operating circumstances, which may be continuous. Those designs require their
own estimators and uncertainty accounts. The radial metafrontier used here
does neither: it compares the declared groups without choosing, relabeling, or
statistically conditioning them.
```

## Two standards answer two different questions

For an organization $o$ belonging to group $\kappa$, the analysis asks:

1. **How well does the organization perform relative to attainable practice
   represented within its own group?**
2. **How close is that group's frontier to the broader opportunity frontier
   represented across all groups?**

The first question yields **group efficiency**, denoted $E_o^G$. The same
organization is then evaluated against the metafrontier, yielding **meta
efficiency**, $E_o^M$. Their ratio is the **metatechnology ratio**:

$$
MTR_o=\frac{E_o^M}{E_o^G}.
$$

The literature also calls this the *technology gap ratio* (TGR). A value nearer one
means that the best practice available within the group approaches the broader best
practice observed for the organization's resource and service mix. A lower value
signals a larger opportunity gap at that mix. It does not say that local managers
caused the gap or could remove infrastructure, regulatory, or mandate differences on
their own.

The three quantities obey the accounting identity

$$
E_o^M=E_o^G\times MTR_o.
$$

Consider an organization that uses four units of a resource and delivers two
units of service. At this resource commitment, its group frontier supports
four services, while the metafrontier supports eight. Its group efficiency is
$2/4=0.50$, its meta efficiency is $2/8=0.25$, and its MTR is $4/8=0.50$.

```{figure} ../../_static/figures/metafrontier-management-account.svg
:name: fig-metafrontier-management-account
:alt: An organization using four resource units delivers two services, while its group frontier supports four and the pooled metafrontier supports eight; group efficiency is one half, the metatechnology ratio is one half, and meta efficiency is one quarter
:width: 100%

The same observed operation is assessed against two opportunity standards.
The decomposition distinguishes performance within the declared group from
the proximity of that group's frontier to the broader meta opportunity.
```

The distinction changes the conversation. A process-redesign or maintenance
programme may be relevant when an organization lies behind its group
frontier. Infrastructure investment, regulatory reform, access to capital,
or a change in service mandate may be relevant when the group frontier lies
behind the meta opportunity. The scores organize these questions; they do not
show that any named intervention will cause an improvement.

## The radial metafrontier account

Let organization $o$ use input vector $x_o$ to deliver desirable-output
vector $y_o$. Its declared group is $\kappa$. The matrices $X_\kappa$ and $Y_\kappa$
contain the eligible observations in that group, while $X_M$ and $Y_M$
contain eligible observations from all declared groups. The variables,
measurement units, mission boundary, orientation, returns to scale, and time
information must be the same in the two comparisons. Only the reference
population changes.

For an output-oriented analysis under variable returns to scale, the group
programme is

$$
\begin{aligned}
\phi_o^G=\max_{\phi,\lambda}\quad &\phi\\
\text{subject to}\quad
&X_\kappa\lambda\leq x_o,\\
&Y_\kappa\lambda\geq\phi y_o,\\
&\mathbf 1^\top\lambda=1,\qquad \lambda\geq0.
\end{aligned}
$$

The expansion factor $\phi_o^G$ asks how much all recorded outputs could be
increased together while inputs remain fixed. Reporting
$E_o^G=1/\phi_o^G$ places group efficiency on the familiar higher-is-better
scale from zero to one. The meta programme has the same form but replaces the
group matrices with the pooled matrices:

$$
\begin{aligned}
\phi_o^M=\max_{\phi,\lambda}\quad &\phi\\
\text{subject to}\quad
&X_M\lambda\leq x_o,\\
&Y_M\lambda\geq\phi y_o,\\
&\mathbf 1^\top\lambda=1,\qquad \lambda\geq0.
\end{aligned}
$$

Thus $E_o^M=1/\phi_o^M$ and

$$
MTR_o=\frac{E_o^M}{E_o^G}
     =\frac{\phi_o^G}{\phi_o^M}.
$$

Because the pooled comparison population contains the organization's own
group, it cannot offer fewer represented opportunities than the matched
group comparison. With valid nested technologies,

$$
0<E_o^M\leq E_o^G\leq1,
\qquad
0<MTR_o\leq1.
$$

An input-oriented analysis protects the observed output commitments and asks
how far inputs could contract. If $\theta_o^G$ and $\theta_o^M$ are the
corresponding input efficiencies, then

$$
MTR_o=\frac{\theta_o^M}{\theta_o^G}.
$$

The orientation should follow the organization's decision problem. An
output orientation may suit a hospital expected to serve more patients with
a largely fixed estate; an input orientation may suit a programme required
to deliver a fixed service obligation at lower resource cost. Under constant
returns to scale, matched input- and output-oriented radial efficiencies
coincide. Under variable returns to scale they need not, so orientation is
not a harmless presentational choice.

The scale assumption also has substantive content. Variable returns to scale
compares an organization with convex combinations at a comparable scale.
Constant returns to scale admits proportional replication of observed
activities. A study should choose between them from its account of the
sector, not from whichever version produces a preferred ranking.

## A pooled frontier is not merely a union of group frontiers

There are two ideas that are easy to confuse. At the conceptual level, the
meta opportunity can be described as the union of the opportunities available
to the separate groups. Such a union need not be convex: an activity feasible
under one institutional regime and another activity feasible under a
different regime do not automatically imply that every mixture of the two is
feasible.

The radial DEA estimator used here instead pools all eligible observations
and, under VRS, takes their common convex hull. It can therefore construct a
meta benchmark by combining observations from different groups. A rural
hospital and an urban hospital, for example, may jointly define a virtual
comparator even though no real institution has exactly that configuration.
Under CRS the analogous pooled technology is conic rather than convex.

This distinction matters because the pooled hull is generally at least as
expansive as the nonconvex union of separately estimated group hulls. It can
therefore produce a lower meta efficiency and MTR. That is not a computational
quirk; it follows from the maintained assumption that cross-group mixtures
describe relevant opportunities. The assumption may be defensible when
groups differ in degree but share transferable practices. It is harder to
defend when regulations, production systems, or missions make the mixed plan
institutionally impossible.

Accordingly, the MTR is always conditional on how the meta opportunity has
been constructed. Researchers should examine which groups contribute to
important meta benchmarks and explain whether the associated practices can
be combined, transferred, or approached. A meta target may describe a useful
long-run opportunity without being an immediately adoptable operating plan.

## A six-organization laboratory

The `metafrontier_groups` dataset isolates the decomposition with one input
and one output:

| Organization | Declared group | Resource | Service |
|---|---|---:|---:|
| A | group 1 | 2 | 2 |
| B | group 1 | 4 | 4 |
| C | group 1 | 4 | 2 |
| D | group 2 | 1 | 2 |
| E | group 2 | 2 | 4 |
| F | group 2 | 4 | 8 |

Group 1 demonstrates one service per resource unit, whereas group 2
demonstrates two. Organization C also has a within-group shortfall because B
delivers twice as much service with the same resource commitment. The case
therefore separates weak operating performance within a group from a gap
between represented group opportunities.

The complete calculation requires only the dataset roles and the declared
orientation and scale assumption:

```python
from deapack import DEAData, MetafrontierDEA, dataset_info, load_dataset

frame = load_dataset("metafrontier_groups")
roles = dataset_info("metafrontier_groups").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    group=roles["group"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
)

result = MetafrontierDEA(
    orientation="output",
    returns_to_scale="vrs",
).fit(data)

figure = result.plot(kind="metafrontier")

print(result.summary()[
    ["dmu_id", "group_efficiency", "meta_efficiency",
     "metatechnology_ratio"]
])
```

The results are exact:

| Organization | Group efficiency | Meta efficiency | MTR/TGR |
|---|---:|---:|---:|
| A | 1.00 | 0.50 | 0.50 |
| B | 1.00 | 0.50 | 0.50 |
| C | 0.50 | 0.25 | 0.50 |
| D | 1.00 | 1.00 | 1.00 |
| E | 1.00 | 1.00 | 1.00 |
| F | 1.00 | 1.00 | 1.00 |

```{figure} ../../_static/figures/metafrontier-decomposition-result.svg
:name: fig-metafrontier-decomposition-result
:alt: Connected points compare each organization's output efficiency against its declared-group frontier and the pooled metafrontier; organizations A and B have no within-group shortfall but remain one half as efficient against pooled opportunities, organization C has both shortfalls, and organizations D through F attain both represented frontiers

Within-group performance and pooled-opportunity comparison. The hollow diamond
records efficiency against declared-group best practice; the orange point
records efficiency against pooled best practice. The MTR label gives their
ratio. A connector links the two benchmark results for the same organization;
its length is not another decomposition component, and it does not assign the
difference to management, technology, or the operating environment.
```

A and B reach the best practice represented within group 1, but their meta
efficiencies are only one half. Asking them simply to “catch up with local
best practice” cannot close this part of the shortfall: they are already on
their group frontier. Their result directs attention toward the difference
between represented opportunity sets, while leaving open what produced that
difference and whether it can be changed.

C faces both dimensions. At four resource units, its service would rise from
two to four at the group frontier and to eight at the pooled metafrontier. Its
meta efficiency is therefore

$$
0.25=0.50\times0.50.
$$

D, E, and F attain both frontiers at their operating mixes. Their MTR of one
does not prove that the two group technologies are identical everywhere; it
only says that the matched group and meta boundaries coincide at those
evaluations.

As in any radial DEA analysis, a score of one concerns proportional movement
in the chosen orientation. It should not be silently enlarged into a claim
that every individual input excess or output shortfall has disappeared.

## Time is part of the comparison policy

Panel data add a second source of heterogeneity: the information available at
each date. The radial metafrontier account used here pools all eligible study
periods at both levels. Each group has one time-invariant frontier formed from
all of its observations, and the meta account has one time-invariant frontier
formed from all groups and periods.

This is a retrospective question: how close was each organization to the
strongest practice observed anywhere in the complete study window? It can be
valuable for ex post benchmarking, but it allows a later organization-period
to benchmark an earlier one. That is an intentional information policy, not
evidence that the earlier manager could have known or adopted the later
practice.

A contemporaneous frontier would answer a different question, as would any
other time-scoped information policy. Nor does a change in efficiency against
the all-period frontier identify technological progress. Measuring frontier
movement requires a productivity analysis with an explicitly dated reference
technology. The temporal policy should therefore appear in the study design
and reporting, not be left implicit in the data layout.

## Reporting the decomposition responsibly

Reporting only meta efficiency throws away the main analytical benefit. A
useful table places $E_o^G$, $E_o^M$, and $MTR_o$ side by side. Figure
{numref}`fig-metafrontier-decomposition-result` displays group and meta
efficiency as connected points and prints the exact MTR beside each
organization. This makes the two benchmark comparisons visible without
turning the MTR into a league table of managerial quality.

The caption and accompanying methods statement should identify the declared
groups, input or output orientation, returns to scale, pooled construction,
comparison population, and study-period information policy. Important cases
should be interpreted with their group and meta benchmarks, especially when
the pooled frontier depends on cross-group combinations. The decomposition
identity should hold to numerical precision, and the estimated meta
opportunity should never be less expansive than the matched group
opportunity.

The labels attached to the two components require particular care. Group
efficiency is sometimes described informally as managerial efficiency and
the MTR as an environmental or technology effect. Those names overstate what
the model establishes. Both quantities are deterministic, sample-relative
comparisons. Unmeasured service quality, demand, case mix, capital vintage,
measurement error, and selection into groups can affect either component.
Group membership may itself summarize several institutional differences that
the decomposition cannot disentangle.

For the laboratory case, a defensible statement is:

> Organization C delivered one half of the output supported by its declared
> group frontier at the observed resource commitment. At that operating mix,
> the group frontier supported one half of the output represented by the
> pooled VRS metafrontier. Its resulting meta efficiency was one quarter.

It would not be defensible to conclude that management caused half of C's
shortfall and the operating environment caused the other half. The
multiplication is an efficiency account, not a causal decomposition. Claims
about causes, treatment effects, or the gains from a policy intervention need
a separate identification strategy and evidence about transition costs and
institutional feasibility.

Finally, the six-organization dataset is a theory-led laboratory rather than
evidence about an actual sector. In an empirical study, comparable missions,
harmonized quantities, defensible ex ante groups, and institutional knowledge
are part of the analysis itself. Metafrontier DEA is most informative when it
preserves that context: it allows organizations to be compared on a common
scale without pretending that all of them began with the same opportunities.
