# Network DEA: Coordinating Processes and Assigning Performance Responsibility

A research institute can be judged as a black box: research staff and budgets
enter, while commercial and social results leave. That comparison may answer
whether the institute as a whole uses more resources than comparable
institutes. It cannot say whether the measured shortfall arises while creating
innovations or while turning those innovations into practical outcomes.

Opening the black box changes the question. Patents and prototypes are results
of research, but they are also commitments handed to the
commercialization process. A credible benchmark must respect both roles at
once. It cannot let the research process promise one quantity while the
commercialization process plans to receive another incompatible quantity.

Network DEA is the family of models built around this connected organizational
question {cite:p}`fare2000network,kao2014,cook2014networkhandbook`. The graph
shows how work is organized. The performance measure then reflects whether the
study needs only an organization-level score, a relational view of linked
process performance, or an additive attribution across processes. Those are
different ways to evaluate a connected production system, not interchangeable
names for one algorithm.

## What is lost when the organization is treated as one box?

Suppose organization $j$ uses external resources $x_j$, creates an internal
handoff $z_j$, and delivers final outcomes $y_j$:

$$
x_j \longrightarrow z_j \longrightarrow y_j.
$$

Three studies can be constructed from these quantities.

| Study | What is modeled | Defensible conclusion |
|---|---|---|
| Black-box DEA | only $x\rightarrow y$ is retained | performance of the complete organization when internal responsibility is deliberately suppressed |
| Separate process models | $x\rightarrow z$ and $z\rightarrow y$ are fitted independently | how each process compares under its own unconstrained plan; the two plans need not form one feasible organization |
| Network DEA | $x\rightarrow z\rightarrow y$ is fitted as a connected system | organization and process evidence under an explicit rule that coordinates the handoff |

The network design is warranted only when
the internal process boundary is meaningful, the handoff is observed
consistently, and the comparison organizations operate sufficiently similar
systems. A variable included merely because it is available in a database does
not become an intermediate product.

The distinction is also unrelated to the statistical use of the phrase
*two-stage analysis*, in which efficiency estimates are later related to
environmental variables. That is an inference design, not a two-process
production network.

## One quantity, two organizational roles

An intermediate is stored once. Its economic role is read from the process
graph:

- it is an **outgoing link** for the process that creates it;
- it is an **incoming link** for the process that receives it; and
- it is not counted as an additional final achievement of the organization
  merely because it appears on both sides of the handoff.

This is more than tidy data management. Duplicating an intermediate into two
unrelated columns would allow the supplier and recipient to be benchmarked
against incompatible quantities. Treating it only as a final output would
ignore the downstream commitment. Treating it only as a downstream input
would erase the upstream work that created it.

For a general process $k$, four roles are enough to describe the basic network
boundary:

| Role at process $k$ | Organizational meaning |
|---|---|
| external input | a resource enters the organization at this process |
| incoming link | work created by another process is received here |
| external output | a result leaves the organization here |
| outgoing link | work remains inside the organization and is handed onward |

A closed two-stage chain places every external resource before the first
process and every final result after the second. Many organizations are open:
a later process receives new staff, an early process releases a final service,
or different internal streams branch and rejoin. The location of those
boundary crossings assigns resources and results to the managers and processes
that actually use or create them {cite:p}`cook2010additive`.

```{figure} ../../_static/figures/closed-vs-open-network.svg
:name: fig-core-closed-vs-open-network
:alt: A closed two-process chain is contrasted with an open network in which resources enter and outcomes leave at several processes while internal links branch, rejoin, or skip a process
:width: 100%

A process graph defines the organizational boundary before performance is
calculated; it is not decoration added after the scores are known.
```

A connection in the graph records an organizational dependence: one process must
deliver something that another process needs in order to operate. If research supplies
a patent to commercialization, the model requires their benchmark plans to agree on
that handoff. It does not establish how long commercialization takes or that the
research manager caused a later sale. The managerial content lies in coordinating the
shared commitment, not in the direction of an arrow on the page.

## Different processes may learn from different peers

Opening the organization does not require every process to imitate the same
reference organization. Let $\lambda$ describe the peer plan for research and
$\mu$ the peer plan for commercialization. When management protects the final
service commitment and asks how much external resource can be released, the
coordinated system model is

$$
X\lambda\leq \theta_o x_o,
\qquad
Z\lambda\geq Z\mu,
\qquad
Y\mu\geq y_o.
$$

Here $\theta_o$ is the proportion of the focal organization's external-resource
commitment required by the coordinated benchmark. The upstream plan may learn
from one set of organizations and the downstream plan from another. What makes
the result one organizational plan is the link condition: research can supply
at least what commercialization requires.

If the current resource commitment is the binding management constraint, the
same system can instead ask how far final services could expand:

$$
X\lambda\leq x_o,
\qquad
Z\lambda\geq Z\mu,
\qquad
Y\mu\geq \phi_o y_o.
$$

The largest feasible $\phi_o$ is the service-expansion factor, and the
higher-is-better output efficiency is $1/\phi_o$. This output-distance formulation
comes from the same intermediate-products network lineage
{cite:p}`fare1996intermediate`; it is an orientation of the same core family,
not another model. Choosing between $\theta_o$ and $\phi_o$ records what
management promises to hold fixed: final services in the first case, or the
external resource commitment in the second.

The difference $Z\lambda-Z\mu$ is a disposable internal surplus under this
particular system technology. It is not automatically waste attributable to
the supplying process. It may reflect timing, quality, risk buffers,
indivisibilities, omitted constraints, or an alternative optimum. Other
network models impose equality or attach a scored responsibility to a link;
the appropriate condition belongs to the technology assumptions and performance
question.

Two principles carry across the family:

1. process-specific peers must coexist in one feasible organization; and
2. common link accounting does not imply common peer coefficients.

## Three reporting institutions over one connected system

The same two-stage graph can support three mainstream questions. Choosing
among them changes what the result is entitled to say.

| Approach | Board-level question | Process attribution | Main warning |
|---|---|---|---|
| System-only radial | How much resource could be released while final services are protected, or how much service could be added within the current resource commitment? | none | peer plans and link surplus are feasibility evidence, not process-efficiency scores |
| Relational product | How do the efficiencies of jointly necessary processes compound into system performance? | selected stage ratios under one shared intermediate valuation | fitted multipliers are not prices, and the selected attribution may be nonunique |
| Additive process attribution | How should system performance be distributed across processes according to their fitted virtual-resource shares? | stage efficiencies and endogenous shares | the shares are not observed budgets, stated priorities, or causal contributions |

### System-only radial performance

The system-radial model reports $\theta_o$ for the resource-saving question
or $\phi_o$ for the service-expansion question. To keep comparisons running in
one direction, the reported system efficiency is $\theta_o$ under input
orientation and $1/\phi_o$ under output orientation. Under a matched
self-inclusive comparison it is ordinarily between zero and one, and larger
values mean better performance. The result can show the upstream peer plan,
downstream peer plan, external targets, and link supply and requirement.

It deliberately does not assign an efficiency score to either process. A
coefficient in the research peer plan describes part of a feasible comparator
activity. It does not measure research management's contribution to the
organization's shortfall.

### Relational product performance

A relational account places nonnegative multipliers $v$, $w$, and $u$ on
external resources, intermediate quantities, and final outcomes. For a closed
two-stage CRS system, the process accounts are

$$
E_o^{(1)}=\frac{w^\top z_o}{v^\top x_o},
\qquad
E_o^{(2)}=\frac{u^\top y_o}{w^\top z_o}.
$$

The same $w$ values the handoff leaving process 1 and entering process 2. This
prevents the two processes from choosing unrelated internal valuations. When
the intermediate virtual value is positive, it cancels from the complete
system account:

$$
E_o
=
\frac{u^\top y_o}{v^\top x_o}
=
E_o^{(1)}E_o^{(2)}.
$$

The product identity is the defining performance account for this closed
relational construction {cite:p}`kao2008`. It is not a universal law for
every network technology. The multiplier $w$ is an endogenous supporting
valuation, not an internal transfer price, a causal marginal product, or a
priority elicited from management.

Under matched CRS assumptions, the primary relational system programme and
the preceding system-radial programme have the same optimal system score.
Their reports are still different. The relational account adds process ratios
and a selection among admissible process attributions; the system-only account
does not make those claims.

### Additive process attribution

An additive network account asks how much each process counts in the fitted
system assessment. Let $A_{ko}$ be the virtual resource account of process
$k$ and $B_{ko}$ its virtual result account. When $A_{ko}>0$, its fitted
process efficiency is

$$
E_{ko}=\frac{B_{ko}}{A_{ko}}.
$$

Normalizing the combined virtual resources gives endogenous process shares

$$
\alpha_{ko}
=
\frac{A_{ko}}{\sum_{\ell=1}^{K}A_{\ell o}},
\qquad
\sum_{k=1}^{K}\alpha_{ko}=1,
$$

and the system account is

$$
E_o=\sum_{k=1}^{K}\alpha_{ko}E_{ko}.
$$

This is an arithmetic attribution of system performance, not the ordinary
additive DEA model that sums physical input excesses and output shortfalls.
The $\alpha_{ko}$ are fitted virtual-resource shares. A reported share of
0.60 does not mean that a department receives 60 percent of the observed
budget or that executives regard it as 60 percent important
{cite:p}`chen2009additive,cook2010additive`.

The additive principle extends naturally from a closed two-stage chain to an
open directed network: external resources enter the virtual input account of
the process that receives them, external results enter the virtual output
account of the process that creates them, and each internal link retains a
common valuation at its two endpoints.

```{figure} ../../_static/figures/two-stage-accounting-choices.svg
:name: fig-core-network-accounting-choices
:alt: The same research and commercialization chain supports a system-only radial account, a relational product account, and an endogenous-share additive process attribution
:width: 100%

The graph and the performance account answer different questions. A common
chain does not make a board-level radial score, a relational product, and an
additive process attribution interchangeable.
```

## One organization, three management questions

The bundled `network_2stage` data describe eight research organizations.
Research staff and budget create patents and prototypes; those innovations
are handed to commercialization, which produces sales and a commercial-reach
measure. The dataset is deterministic and intended to expose model mechanisms.
In an empirical application, a percentage such as market share is a ratio
variable and must not be treated as freely additive or scalable without a
separate production-account justification.

The organizational graph is declared once. Nothing about the research-to-
commercialization handoff changes when the board changes the reporting
question:

```python
from deapack import (
    FareGrosskopfNetworkRadialDEA,
    KaoHwangRelationalDEA,
    NetworkData,
    TwoStageAdditiveDecompositionDEA,
    TwoStageSeriesSpec,
    load_dataset,
)

frame = load_dataset("network_2stage")
spec = TwoStageSeriesSpec(
    inputs=("research_staff", "research_budget"),
    intermediates=("patents", "prototypes"),
    outputs=("sales", "market_share"),
    stage_names=("research", "commercialization"),
    link_id="innovation_handoff",
)
data = NetworkData.from_frame(frame, dmu="dmu", spec=spec)
```

Start with the board-level resource question. The model permits research and
commercialization to learn from different peer combinations, but it requires
their selected innovation handoff to coexist in one feasible organization:

```python
system = FareGrosskopfNetworkRadialDEA(
    orientation="input",
    returns_to_scale="crs",
).fit(data)

system.summary().query("dmu_id in ['A', 'D']")[[
    "dmu_id",
    "system_efficiency",
]]

system.plot(
    kind="performance",
    metric="system_efficiency",
    view="points",
)
```

```{list-table}
:header-rows: 1
:widths: 18 18 64

* - Organization
  - System efficiency
  - Board-level reading
* - A
  - 0.8333
  - The coordinated benchmark protects final results with 83.33 percent of the
    external resource commitment
* - D
  - 0.7423
  - The represented system-wide resource opportunity is larger
```

The interpretation requires a feasible connected plan: the external resource
and final-service balances must hold, and research and commercialization must
use one compatible innovation handoff. Detailed numerical and reconstruction
checks are available in the DEAPack Documentation.

```{figure} ../../_static/figures/network-system-performance-result.svg
:name: fig-network-system-performance-result
:alt: Input-oriented radial system efficiency for eight connected research organizations, with one marking no represented proportional resource saving
:width: 100%

The system view answers one core question for all eight organizations. A value
closer to one means that less proportional external-resource saving is
represented while final results and the coordinated handoff are protected. It
does not assign the gap to research or commercialization and does not rank the
causes of performance.
```

For A, the reciprocal output-oriented CRS account would describe a 1.20
service-expansion factor. That is a different management commitment, even
though its harmonized higher-is-better efficiency is again 0.8333.

### Same graph, different responsibility accounts

Now keep the organizations, variables, reference population, graph, and CRS
assumption unchanged. Only the board's reporting institution changes. Because
this comparison is about process attribution rather than operating targets,
the two process-account models are fitted without a projection step:

```python
relational = KaoHwangRelationalDEA(
    decomposition="maximize_stage_1",
    projection="none",
).fit(data)

additive = TwoStageAdditiveDecompositionDEA(
    returns_to_scale="crs",
    decomposition="both_priorities",
    projection="none",
).fit(data)
```

For organization A, the connected plans are feasible and each requested
process decomposition closes. The three reports then read as follows:

```{list-table}
:header-rows: 1
:widths: 23 14 13 18 32

* - Reporting institution
  - System efficiency
  - Research
  - Commercialization
  - How the system account closes
* - System-only radial
  - 0.8333
  - not applicable
  - not applicable
  - no process-efficiency decomposition is claimed
* - Relational product
  - 0.8333
  - 0.8333
  - 1.0000
  - $0.8333\times1.0000=0.8333$
* - Additive process attribution
  - 0.9091
  - 0.8333
  - 1.0000
  - $0.5455\times0.8333+0.4545\times1.0000=0.9091$
```

The first two system numbers coincide here because the closed two-stage CRS
radial and primary relational programmes represent the same system
opportunity under these matched assumptions. Their claims nevertheless differ:
the radial result deliberately stops at the organization, whereas the
relational result selects stage ratios that satisfy a shared intermediate-
valuation account.

The additive result is not a correction to either score. It answers a different
question by forming an arithmetic account with fitted virtual-resource shares;
for A those shares are 0.5455 for research and 0.4545 for commercialization.
Even though the two process efficiencies happen to agree across the relational
and additive reports in this example, that agreement does not make their system
measures interchangeable. Full parameter choices, alternative-optimum bounds,
target construction, and reconstruction diagnostics belong in the DEAPack
Documentation. Choose the responsibility claim before choosing the network
estimator.

## The same organizational account can describe an open graph

A closed chain places all external resources before the first process and all
final results after the last. Real organizations are often open: a later
process may receive new staff or capital, an early process may release a final
service, and internal streams may branch, rejoin, or skip a process. These are
changes in the economic boundary of the organization, not cosmetic changes to
a diagram.

The study should therefore declare every process, every external boundary
crossing, and every internal handoff before fitting the model. A quantity that
enters at a later process belongs to that process's resource account; a result
that leaves early belongs to the process that creates it; and an internal link
must retain one compatible meaning at both endpoints. The package
Documentation shows how to encode such open graphs. The graph must represent
the organization that managers can actually coordinate.

## A system result may not identify one process story

Optimization can determine the best system account while leaving several
equally good multiplier systems, peer plans, process scores, process shares,
or link targets. This is an identification issue, not merely a numerical detail.

The practical reporting hierarchy is:

1. the system score and the production question it answers;
2. the selected process attribution and its aggregation identity;
3. the process-specific peers and coordinated link evidence;
4. any ranges or secondary selection rule used to assess alternative optima;
5. the target policy and whether it identifies one endpoint or merely a
   feasible interval.

If the process ranges are wide, the evidence may support an organization-level
conclusion more strongly than a divisional one. A report should say that a
displayed optimum *assigns* a particular process account, not that it has
discovered a department's true contribution.

The same restraint applies to fitted multipliers and shares. They support the
chosen DEA comparison. Without additional price, preference, governance, or
causal information, they are not transfer prices, strategic priorities,
budget entitlements, or estimates of managerial quality.

## Reading network evidence as a management account

A defensible network study should make five decisions visible in ordinary
organizational language:

- why the black-box boundary hides a decision that matters;
- what each process receives from outside, creates for the outside, and hands
  to another represented process;
- whether each handoff is inherited, redesignable, or subject to another
  explicit coordination rule;
- whether the board needs only a system opportunity or also a relational or
  additive process attribution; and
- how alternate optima limit process-level claims.

Package results should then be read in layers. `summary()` is the board-level
decision table. Component evidence records the selected process account.
Link evidence records upstream supply, downstream requirement, and balance.
Target and peer evidence describe one technically admissible comparator plan.
None of those tables, by itself, is an implementation schedule.

The central lesson is simple. Network DEA becomes useful when it prevents an
organization from looking efficient through a collection of mutually
incompatible departmental stories. Its graph keeps internal work connected;
its performance account says what the board wants to learn from that
connection; and the supporting evidence shows where the data do and do not support a
stable responsibility account.

The next family-level question is different again. When management wants to
locate variable-specific resource excesses and service shortfalls inside the
connected organization, network SBM replaces process ratio accounts with a
coordinated non-radial slack account. That change deserves its own chapter
because it changes the performance measure, aggregation, link responsibility,
and target semantics rather than merely adding another graph label.
