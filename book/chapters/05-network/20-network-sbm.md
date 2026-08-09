# Network SBM: Managing a Connected Organization

A hospital can use too many resources for the treatments it completes, but that
system-wide fact does not tell management whether the shortfall begins in intake,
diagnostics, treatment, or discharge. A utility can compare total labor and fuel with
electricity delivered, yet still know little about how generation, transmission, and
distribution contribute to the result. The missing information lies inside the
organization.

Analyzing each department separately does not solve the problem. The benchmark chosen
for diagnostics might pass 100 cases to treatment, while the treatment benchmark is
constructed to receive only 70. Both departments could appear efficient on their own,
but their plans could not be implemented by one hospital.

Network slacks-based measurement (network SBM) treats the organization as one
connected production system {cite:p}`tone2009network`. Each process retains its own
resources, outputs, peers, and normalized slack measure. At the same time, the model
requires adjacent process plans to agree on the internal goods or services they pass
between them. The result answers two linked management questions:

> How well does the connected organization perform, and which processes locate
> the resource excesses or service shortfalls in one feasible system plan?

This is the mainstream contribution of network SBM: it preserves internal
responsibility without allowing the parts of the organization to choose mutually
inconsistent targets. More scores are useful only because they illuminate one feasible
organizational plan.

## One organization, several sources of shortfall

Suppose an organization contains processes $k=1,\ldots,K$. Process $k$ uses external
inputs $x_o^k$, produces external outputs $y_o^k$, and has its own reference
intensities $\lambda^k$. For evaluated organization $o$, the external resource
excesses and service shortfalls can be written as

$$
x_o^k=X^k\lambda^k+s_o^{k-},
\qquad
y_o^k=Y^k\lambda^k-s_o^{k+}.
$$

The benchmark process uses no more of a scored external input and produces no less of
a scored external output. Under variable returns to scale (VRS), each process has its
own convexity condition,

$$
\mathbf 1^\top\lambda^k=1.
$$

Under constant returns to scale (CRS), these conditions are omitted. A single
organization-wide convexity equation is not equivalent: different processes can have
different peer mixtures, provided that their shared handoffs remain compatible.

Let $Z^{(k,\ell)}$ denote an intermediate product supplied by process $k$ and used by
process $\ell$. It might be diagnosed patients, approved loans, generated electricity,
unfinished components, or an internal information service. The link equations make
the supplier's target equal the recipient's target. Without this continuity, the
analysis is a set of independent departmental DEA models rather than a model of one
organization.

This distinction changes the meaning of a process score. It is not the efficiency that
the process would necessarily obtain if removed from the network. It is an attribution
from a jointly feasible system solution.

## Link governance defines the management counterfactual

An observed handoff can play two core roles in a performance appraisal. Management
must decide whether the quantity was an inherited commitment or was open to
coordinated redesign by the connected processes.

```{figure} ../../_static/figures/network-sbm-governance.svg
:name: fig-network-sbm-governance
:alt: Two core network SBM link policies preserve supplier-recipient continuity: fixed inherits the observed handoff, while free permits the processes to coordinate one common target
:width: 100%

Two core governance policies for an internal handoff. Both preserve one common
supplier--recipient target; they differ in whether the observed quantity must be
inherited or may be redesigned jointly.
```

### Fixed: inherit the observed commitment

For a fixed link from $k$ to $\ell$,

$$
Z^{(k,\ell)}\lambda^k
=z_o^{(k,\ell)}
=Z^{(k,\ell)}\lambda^\ell.
$$

Both process benchmarks must reproduce the observed handoff. This policy is suitable
when managers could not change the flow during the period: a contracted supply
quantity, a regulated transfer obligation, an inherited referral load, or a service
commitment already accepted by the next department.

“Fixed” is conditional language. It does not claim that the handoff can never change;
it asks how the organization performs while that commitment is protected.

### Free: permit a coordinated redesign

For a free link,

$$
Z^{(k,\ell)}\lambda^k
=Z^{(k,\ell)}\lambda^\ell.
$$

The common target may differ from the observed amount. The two processes can redesign
the handoff together, but they cannot choose different quantities. This is appropriate
for integrated planning—for example, when diagnostics and treatment can jointly
redesign referral volume or a supply chain can coordinate production and distribution.

Free does not mean disconnected. Removing the equality would let each process optimize
against an incompatible internal plan.

With all other assumptions held constant, the free-link feasible set contains the
fixed-link feasible set. It can therefore reveal at least as much improvement
potential. Because efficiency is reported on a higher-is-better scale, the free-link
score cannot exceed its fixed-link counterpart. A lower free-link score does not mean
coordination made performance worse; it means that coordination exposed an opportunity
hidden by the inherited-flow constraint.

Fixed and free links govern feasibility but do not add a link slack to the SBM
objective. Source-qualified extensions can instead assign a handoff deviation to one
process's performance account. Because those extensions alter the orientation and
normalization rather than merely switching the link constraint, their detailed
formulations belong in the package Documentation. The mainstream management
comparison remains: inherit the observed commitment or coordinate a redesign.

## Process weights are a governance choice

Top management still needs a declared rule for aggregating the processes. Network SBM
uses exogenous process weights

$$
w_k\ge0,
\qquad
\sum_{k=1}^{K}w_k=1.
$$

They can reflect controllable cost shares, staff-time shares, or an approved strategic
importance policy. They are not flexible DEA multipliers, prices of the intermediate
products, or statistical estimates produced by the model.

The basis matters. Weighting hospital processes by expenditure answers a different
question from weighting them by clinical priority. A credible study should state who
chose the weights and examine plausible alternatives rather than select a policy after
seeing the ranking.

A zero-weight process can still restrict system feasibility through its technology and
links, but its slack account does not enter the objective. Consequently, system
efficiency of one establishes efficiency for every process only when all relevant
processes have strictly positive weights.

### A process map is an economic description

The network should follow responsibility and material or service flow, not simply copy
the organization chart. A process boundary is useful when it separates decisions that
management wants to diagnose and when the handoff crossing that boundary is measured
consistently for both sides.

An internal link is declared once, with one supplier and one recipient. Although the
same variable appears as an output of the supplying process and an input of the
receiving process, it is not an external system output and input counted twice. Its
purpose is to connect the two process technologies through one compatible handoff
target.

The continuity equation also carries a substantive assumption: the quantity leaving
one process is the quantity entering the next. If a handoff undergoes measured loss,
quality conversion, storage, or delay, simple equality may not describe the operation.
Those features should be represented in the data and production account before the
model is fitted. Relabeling a transformed quantity as an ordinary link would create a
precise but economically false target.

Process definitions should therefore remain stable across the organizations being
compared. If one hospital records diagnostics and treatment separately while another
combines them, their process scores do not refer to the same responsibilities. The
system model is only as comparable as the operational map on which it is built.

## Normalized slacks create three performance accounts

SBM compares excesses and shortfalls relative to the observed quantities, allowing
variables with different units to enter one process account. For process $k$, define

$$
A_o^k
=1-\frac{1}{m_k}\sum_{i=1}^{m_k}
\frac{s_{io}^{k-}}{x_{io}^k},
$$

and

$$
B_o^k
=1+\frac{1}{r_k}\sum_{r=1}^{r_k}
\frac{s_{ro}^{k+}}{y_{ro}^k}.
$$

$A_o^k$ is the retained-resource account: it falls as normalized input excesses
increase. $B_o^k$ is the service-expansion account: it rises as normalized output
shortfalls increase. Positive observed quantities are therefore part of the classical
normalization contract.

### Input orientation: conserve resources

The input-oriented process and system scores are

$$
\theta_o^k=A_o^k,
\qquad
\theta_o=\sum_{k=1}^{K}w_k\theta_o^k.
$$

This orientation asks where external resources can be reduced while outputs and
network continuity remain feasible. A score of one says
that the chosen system optimum contains no scored input slack in positively weighted
processes. It does not establish that every output-expansion opportunity has been
exhausted.

### Output orientation: expand services

For process $k$, let

$$
\rho_o^{O,k}=\frac{1}{B_o^k}.
$$

The system output efficiency is

$$
\rho_o^O
=\frac{1}{\sum_{k=1}^{K}w_kB_o^k}
=\frac{1}{\sum_{k=1}^{K}w_k/\rho_o^{O,k}}.
$$

It is a weighted harmonic aggregation of process efficiencies, not the arithmetic mean
$\sum_k w_k\rho_o^{O,k}$. This orientation asks where external services can be expanded
within one connected operating plan. Input slacks can remain feasible but unscored.

### Non-orientation: redesign both sides

With fixed or free links, the selected process ratio is

$$
\rho_o^k=\frac{A_o^k}{B_o^k},
$$

and the system score is

$$
\rho_o
=\frac{\sum_{k=1}^{K}w_kA_o^k}
       {\sum_{k=1}^{K}w_kB_o^k}.
$$

This is generally not the arithmetic weighted average of the process ratios. It can be
reconstructed as

$$
\rho_o=\sum_{k=1}^{K}\omega_o^k\rho_o^k,
\qquad
\omega_o^k
=\frac{w_kB_o^k}{\sum_{\ell=1}^{K}w_\ell B_o^\ell}.
$$

The $\omega_o^k$ are denominator-adjusted reconstruction weights from the selected
solution. They do not replace the declared management weights $w_k$. Reporting the two
as though they were the same would misstate how the system result is formed.

The three orientations therefore answer different operating questions. Their scores
should not be mixed in a league table without naming the resource-conservation,
service-expansion, or joint-redesign account behind them.

## System performance is primary; process performance is attribution

Every process score is produced by the optimization of the complete connected system.
Its peer mixture must coexist with adjacent peer mixtures and satisfy the link policy.
A low process score locates a shortfall in one feasible system account; it does not
prove that the process manager caused the organization's performance.

The distinction is especially important when a policy changes. A treatment process
that looks strong under fixed referrals may receive a different attribution when the
referral mix becomes redesignable. The model changed the feasible management problem,
not merely the display of the same result.

Network linear programs can also have alternate optima. The primary system score may
be unique while process scores, slacks, peer intensities, and free-link targets vary
across equally good system plans. For a selected optimum,

$$
x_o^{k*}=x_o^k-s_o^{k-*},
\qquad
y_o^{k*}=y_o^k+s_o^{k+*},
$$

and every internal target remains continuous between supplier and recipient. But that
target need not be the only system-optimal one.

Managers should therefore read process values as **attributions within one selected
optimum** unless uniqueness or admissible ranges have been established. If an operational plan
depends on one exact handoff target, a documented secondary selection criterion or an
alternate-optimum analysis is more informative than treating the first solution as a
unique prescription.

## A three-process service chain in DEAPack

The bundled `three_process_service_chain` data describe a neutral service system with three connected
processes. Stage 1 supplies the first handoff to stage 2; stage 2 produces an external
service and passes a second handoff to stage 3; stage 3 produces the final external
service. The following compact workflow asks how much scored external input could be
conserved under VRS when both handoffs can be coordinated freely.

```python
from deapack import (
    LinkSpec,
    NetworkData,
    NetworkSBM,
    NetworkSpec,
    ProcessSpec,
    load_dataset,
)

frame = load_dataset("three_process_service_chain")
spec = NetworkSpec(
    processes=(
        ProcessSpec(
            "stage_1",
            inputs="intake_hours",
            outputs="verified_requests",
        ),
        ProcessSpec(
            "stage_2",
            inputs=("verified_requests", "resolution_hours"),
            outputs=("same_day_resolutions", "scheduled_cases"),
        ),
        ProcessSpec(
            "stage_3",
            inputs=("scheduled_cases", "delivery_hours"),
            outputs="completed_services",
        ),
    ),
    links=(
        LinkSpec(
            "handoff_1_2",
            source="stage_1",
            target="stage_2",
            variables="verified_requests",
        ),
        LinkSpec(
            "handoff_2_3",
            source="stage_2",
            target="stage_3",
            variables="scheduled_cases",
        ),
    ),
)
data = NetworkData.from_frame(frame, dmu="unit", spec=spec)

result = NetworkSBM(
    orientation="input",
    returns_to_scale="vrs",
    link_control="free",
    division_weights={
        "stage_1": 0.4,
        "stage_2": 0.2,
        "stage_3": 0.4,
    },
).fit(data)

system = result.summary().set_index("dmu_id").loc[["resource_drag"], ["efficiency"]]
processes = result.components_for("resource_drag").query(
    "component_kind == 'process'"
)[["process_id", "efficiency", "division_weight"]]
handoffs = result.links_for("resource_drag")[[
    "link_id", "observed", "target", "continuity_residual"
]]

figure = result.plot(kind="process", dmu_id="resource_drag")
```

The three objects above form a compact management report: one system result,
one declared-weight process account, and two supplier--recipient handoff
checks. Their values are computed from the project case rather than copied
from a publication.

```{figure} ../../_static/figures/three-process-service-account-result.svg
:name: fig-network-sbm-process-result
:alt: A project service plan's network SBM result, with three process input-performance bars, a declared-weight system reconstruction, and two observed-to-selected handoff accounts
:width: 100%

One connected management account for a project-authored service plan. The
process values locate input burden inside the jointly feasible plan, the
middle account reconstructs the system result from the declared weights, and
the handoff ledger preserves the supplier--recipient responsibility chain.
These are selected attributions and coordinated targets, not causal
departmental effects or uniquely prescribed instructions.
```

Reading across the figure is more informative than ranking the three process numbers.
The left panel shows that all three selected process accounts contain a similar
normalized input burden. The upper-right panel then makes the governance arithmetic
visible: each process result contributes only through its declared weight, so stage 2
has a smaller effect on the system account because management assigned it a weight of
0.2 rather than 0.4. The lower ledger returns to operational units. Each row has its
own unit and compares the observed handoff with the one common supplier--recipient
target selected by the fitted plan; the arrows do not put different physical flows on
one artificial scale.

The declared-weight arithmetic mean of the three process accounts reconstructs the
system result. Both supplier--recipient continuity residuals are at numerical zero, so
the selected handoff targets form one implementable network plan rather than three
independent process projections.

The management interpretation requires one feasible connected plan: external
resource and service balances must hold, and each supplier--recipient pair
must share the same handoff target. Here both continuity residuals are at
numerical zero, so the process accounts and handoff ledger describe one
coherent organization. Detailed numerical checks belong in the DEAPack
Documentation.

The system score summarizes a normalized scored-input account under the
declared technology and governance policy. It must not be reported as the
same removable percentage for every physical input. SBM averages
variable-specific proportional slacks, and the target table—not one aggregate
percentage—shows the selected changes in original units.

Nor should the three process values be described as causal contributions. They locate
the slack account within the selected coordinated optimum. Another system-optimal
solution may support different process or handoff details while preserving the
same primary score.

## Reading the result as a management argument

A useful network-SBM report is short but explicit. It identifies the process map,
orientation, returns to scale, link governance, and process-weight policy; then it
presents the system score together with process attributions and common handoff
targets. Before those targets are discussed operationally, the analyst should confirm
that the appraisal succeeded and that supplier and recipient quantities agree.

The model supports claims such as:

- the connected organization contains a specified normalized resource or service
  shortfall relative to the observed reference system;
- the selected system optimum assigns more of that shortfall to some process accounts
  than others;
- treating a handoff as fixed or redesignable changes the attainable coordinated
  benchmark; and
- supplier and recipient targets agree under the chosen governance rule.

It does not establish that a process manager caused the shortfall, that a declared
weight is objectively correct, or that the selected peers can be copied without
transition costs. It also does not infer inventories, losses, quality transformations,
shared system budgets, or movements through time unless those mechanisms are explicitly
modeled.

The central discipline is continuity. Black-box DEA hides internal responsibility;
separate process DEA can create incompatible plans. Network SBM occupies the useful
middle ground: one system objective, process-level normalized slack accounts, and a
declared governance rule for every internal handoff. That combination lets managers
locate performance opportunities without pretending that the organization is either a
single undifferentiated box or a collection of independent departments.
