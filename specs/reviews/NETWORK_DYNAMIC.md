# Network and dynamic DEA: performance inside organizations and across time

## Purpose and scope

This review starts from two management questions:

> Where inside an organization are resources converted into intermediate and
> final services, and how is a measured system shortfall attributed across
> processes?

> How should present performance be judged when today's action creates an
> asset, obligation, or production possibility that persists into a later
> period?

A black-box DEA model deliberately suppresses those relations. A network
model opens the organization into connected processes and requires all
intermediate and shared-resource targets to balance. A dynamic model adds a
state, carry-over, investment, or transition relation across periods. Merely
running DEA by department or by year does neither.

This source-facing review reconciles the network and dynamic corpus in
[`LITERATURE_BASELINE.md`](../LITERATURE_BASELINE.md) with the graph,
network, and dynamic entries in
[`METHOD_UNIVERSE.md`](../METHOD_UNIVERSE.md) and
[`METHODS.md`](../METHODS.md), and the network/dynamic chapters of
[`BOOK_ARCHITECTURE.md`](../BOOK_ARCHITECTURE.md). It does not create
executable status from a literature label alone: every public leaf still
requires an equation audit, numerical oracle, implementation, and tests.

## Evidence protocol

Each evidence record uses the following fields.

| Field | Meaning |
|---|---|
| **Economic question** | The internal performance-attribution, coordination, investment, or persistence question. |
| **Technology / estimator** | Process graph, link equations, node technologies, temporal transitions, and empirical estimator. |
| **Measure** | System and process radial, relational, additive, directional, slacks-based, or economic criterion. |
| **RTS** | System- and node-level returns-to-scale assumptions. |
| **Data / time** | External inputs/outputs, intermediates, resource pools, carry-overs, periods, and information structure. |
| **Native score** | Source-native system, process, or intertemporal value and its interpretation. |
| **Exact aliases** | Names that identify the same graph, technology, measure, and aggregation on a stated domain. |
| **Distinct variants** | Nearby topologies, link controls, governance rules, or dynamic lineages requiring another leaf. |
| **Domain** | Link observability, comparability, graph, positivity, state, and boundary-condition requirements. |
| **Failures** | Link imbalance, duplicated resources, nonunique decomposition, infeasibility, and unsupported blame or responsibility claims. |
| **Solver form** | LP, fractional transformation, block programme, bilevel model, or other source-required backend. |
| **Defining source** | Original or authoritative source fixing the record. |
| **Evidence status** | `primary-checked`, `review-supported`, or `registry-provisional`. |
| **Oracle** | Current DEAPack verification state using `not located`, `candidate`, `analytically derived`, `reproduced`, or `cross-implemented`; repository property evidence is stated separately, and analytical derivation does not claim a published-data reproduction. |
| **Package recipe** | Graph, technology, measure, governance, and canonical method ID. |
| **Book location** | One audited status: active core placement, documentation/source review only, or evidence-deferred candidate. Only an exact path in `book/index.md` establishes active placement. |

`primary-checked` means that the source has been checked for its defining
graph, link/transition account, and native performance identity.
`review-supported` maps a recognized family whose executable leaf still
needs a formulation-level audit. `registry-provisional` marks an advanced
family that should not receive a public solver yet.

Executable status is stated record by record. The current public vertical
slices include Färe--Grosskopf two-stage system-radial DEA, relational and
additive two-stage DEA, general open-DAG additive network DEA,
Tone--Tsutsui network SBM, and Tone--Tsutsui dynamic SBM and dynamic-network
SBM. Nearby families remain planned until their own equations and oracles are
audited; sharing a graph compiler is not implementation evidence.

### A mechanism grammar that the historical names do not supply

The literature uses “network DEA,” “multi-stage DEA,” and “dynamic DEA” for
programmes with different feasible sets. A package-level unification can
share graph and sparse-matrix machinery, but it must preserve the following
economic constraints.

For a two-process chain, write $X$, $Z$, and $Y$ for external inputs,
intermediate products, and final outputs. A later explicit VRS statement of
the Färe--Grosskopf intermediate-products technology can be written,
suppressing disposal slacks, as

$$
\begin{aligned}
X\lambda^1&\le x, &
Z\lambda^1&\ge z,\\
Z\lambda^2&\le z, &
Y\lambda^2&\ge y,\\
\mathbf 1^\top\lambda^1&=1, &
\mathbf 1^\top\lambda^2&=1,
\end{aligned}
\qquad
\lambda^1,\lambda^2,z\ge0.
$$

The common $z$ coordinates the two process plans, but free disposal permits
the upstream benchmark to produce at least what is transferred and the
downstream benchmark to require no more than that amount. This is not the
same feasible set as an exact-handoff model. Färe and Grosskopf's
[original network paper](https://doi.org/10.1016/S0038-0121(99)00012-9)
develops a broader family containing intermediate-product, fixed-factor
allocation, and dynamic constructions. The two separate convexity equations
above are attributed to equations (34e)--(34f) of the later polyhedral
statement by
[Podinovski and Bouzdine-Chameeva
(2021)](https://doi.org/10.1007/s11123-021-00610-3), not retroactively to the
original paper. Removing those two equations gives the CRS cone used in the
public Färe--Grosskopf radial leaf.

An exact linked plan instead imposes, for a link from process $k$ to process
$h$,

$$
Z^{(k,h)}\lambda^k=Z^{(k,h)}\lambda^h.
$$

A fixed-observed link additionally equates that common value to
$z_o^{(k,h)}$; a bounded or transformed link changes the row again.
Imposing one common peer mixture
$\lambda^1=\cdots=\lambda^K$ is another restriction. It is not an
implementation shortcut for a model whose processes have separate
intensities.

A shared resource is not an intermediate. If $a_o^k$ is the amount assigned
to eligible activity $k$ from one organizational pool $\bar a_o$, the
minimum conservation account is

$$
\sum_{k\in\mathcal K(a)}a_o^k\le \bar a_o,\qquad a_o^k\ge0.
$$

Equality, observed allocation, transfer loss, and allocation bounds are
separate policies. Copying $\bar a_o$ into every process would manufacture
resources that the organization does not possess.

Time adds a different incidence relation. Tone--Tsutsui adjacent-period
continuity uses the same observed carry-over account on both sides,

$$
\sum_j z_{ijt}^{\alpha}\lambda_j^t
=
\sum_j z_{ijt}^{\alpha}\lambda_j^{t+1},
$$

where $\alpha$ is one source carry-over category. An investment technology
may instead contain a stock law such as

$$
k_{t+1}=(1-\delta)k_t+I_t
$$

together with adjustment costs and an intertemporal objective. Exact
carry-over balance and an investment transition are not aliases even though
both can be compiled on a time-expanded graph.

Finally, the graph does not determine the performance account. Under the
source conditions, a serial relational system may satisfy
$E_o=\prod_k E_o^k$, whereas a parallel relational account may satisfy
$E_o=\sum_k\omega_{ko}E_o^k$, with weights induced by the source virtual
resource account. Additive, radial, directional, and SBM measures impose
other identities. These equations are therefore typed components of a study,
not a universal “network score.”

## 1. Opening the organizational black box

### 1.1 Does the organization have one process or connected processes?

Färe and Grosskopf's network production approach makes intermediate products
part of the attainable system rather than hiding them inside one input-output
boundary. A series, parallel, mixed, or general network can be represented by
a directed process graph, but topology alone does not identify the
technology. The graph must also specify link conservation, process inputs
and outputs, resource pools, intensity coupling, and process RTS.

| Evidence field | Record |
|---|---|
| **Economic question** | Which connected processes transform external resources into final services, and what system plans are jointly attainable once intermediate flows must balance? |
| **Technology / estimator** | Directed production graph with nodes, external variables, intermediate links, resource pools, node technologies, link-balance rules, and common or node-specific activity intensities. |
| **Measure** | None at the graph level; relational, radial, additive, directional, SBM, EBM, or economic objectives can be composed only when link and aggregation semantics are supported. |
| **RTS** | Declared by node and, where meaningful, for the system. A black-box CRS/VRS switch does not automatically define network scale behavior. |
| **Data / time** | Cross-sectional process-level inputs, final outputs, and intermediates; shared-resource totals and incidence; optional panel periods for a separately defined network-productivity operator. |
| **Native score** | No graph-level score. The attached measure supplies system, process, and possibly link values. |
| **Exact aliases** | “Two-stage” is an exact topology alias for a two-node series graph only when the direction of the intermediate and all link semantics match. It is not an alias for general network DEA. |
| **Distinct variants** | Series, parallel, series-parallel, arbitrary directed, feedback, hierarchical, multi-plant, partial-incidence, environmental, and dynamic networks. |
| **Domain** | Every intermediate has declared source and destination roles; shared inputs have one resource-pool account; process observations are comparable. Cycles require a well-defined simultaneous-flow formulation. |
| **Failures** | Running independent node models yields incompatible intermediate targets. Duplicating a shared input overstates resource availability. Treating missing process data as zero changes the graph. Unconstrained cycles can make the system ill posed. |
| **Solver form** | Sparse block graph compiler. Cooperative linear measures yield LPs; fractional measures require a valid transformation; non-cooperative or feedback variants can require different backends. |
| **Defining source** | [Färe and Grosskopf (2000)](https://doi.org/10.1016/S0038-0121(99)00012-9); systematic scope in [Kao (2014)](https://doi.org/10.1016/j.ejor.2014.02.039) and the [Network DEA Handbook](https://doi.org/10.1007/978-1-4899-8068-7). |
| **Evidence status** | `primary-checked` for the network-technology principle; broad graph variants are `review-supported`. |
| **Oracle** | `not located` at the graph level because a structure alone has no numerical score. The general-network declaration and several source-qualified network measures are public, but a generic graph does not imply that every attached measure or topology is implemented. |
| **Package recipe** | `graph.series`, `graph.parallel`, or `graph.general_network` + `NetworkSpec(nodes, links, resource_pools, intensity_policy)` + a named measure and governance policy. |
| **Book location** | **Active core placement:** `book/chapters/05-network/network-dea-organizations-links-responsibility.md`; graph variants and incidence contracts remain in package documentation. |

The minimum link specification is:

```text
source node
target node
economic role
observed/fixed, endogenous, or bounded control
exact, at-least, at-most, loss, or transformation balance
unit and timing
```

The minimum resource-pool specification names the total available resource,
the eligible processes, and whether allocation is observed, fixed, or chosen
by the model. Copying the pool's total into every process is not a harmless
data transformation.

### 1.2 Which frontier construction sits behind the graph?

Three early lines all open the black box, but they do not estimate the same
technology. Färe and Grosskopf assemble subtechnologies and connect them
through intermediate products, fixed-factor allocations, or time links.
Lewis and Sexton first solve node DEA programmes, construct hypothetical
sub-DMUs, and pass upstream results through an acyclic organization.
Prieto and Zofío represent an economy as an input--output network in which
sector technologies, primary resources, intermediate production, and final
demand are optimized jointly. The differences concern who may be a peer,
what can be reallocated, and whether the organization receives one jointly
feasible plan.

| Evidence field | Record |
|---|---|
| **Economic question** | Is management benchmarking one integrated production plan, improving a sequence of organizational nodes, or reallocating primary and intermediate resources across an input--output system? |
| **Technology / estimator** | Färe--Grosskopf: connected convex subtechnologies with a common intermediate decision and source disposal inequalities. Lewis--Sexton: an acyclic network of hypothetical sub-DMUs constructed from node-specific DEA results and propagated in network order. Prieto--Zofío: a multi-sector input--output activity system with sector subtechnologies, resource allocation, intermediate production, and final demand. |
| **Measure** | Source radial/distance measure for the connected technology; source sequential organizational and node efficiencies for Lewis--Sexton; source potential resource savings or final-output gains for the input--output network. |
| **RTS** | Färe--Grosskopf scale restrictions are attached to each subtechnology. Lewis--Sexton permits the standard RTS assumptions by sub-DMU. Prieto--Zofío retains the scale assumptions of its sector activity model. These are not one system-wide toggle. |
| **Data / time** | Respectively: process inputs/intermediates/outputs; an acyclic sub-DMU graph with node data and site characteristics; or comparable national/sector input--output tables with primary inputs and final demand. |
| **Native score** | Source-specific system and component values. The public Färe--Grosskopf intermediate-products slice reports one orientation-qualified system factor and a harmonized efficiency, but no stage score. No transformation makes the three lineages' complete result contracts identical because their target plans and peer constructions differ. |
| **Exact aliases** | The phrase “network DEA” is only a discovery umbrella. No exact alias exists among these three source constructions. “Multi-stage” identifies a topology, not an estimator. |
| **Distinct variants** | Independent stage DEA; common-intensity network envelopment; exact versus disposable links; relational decomposition; shared-resource allocation; feedback and cyclic networks. |
| **Domain** | Homogeneous process definitions and valid link units. Lewis--Sexton requires an acyclic ordering. Input--output DEA requires consistent sector accounts and resource conservation. |
| **Failures** | Treating a sequential node optimum as one joint frontier projection; replacing disposable intermediate coordination by exact equality; applying national input--output reallocation to a firm whose divisions cannot exchange resources; reporting one node's peer set as the organization's unique peer set. |
| **Solver form** | Joint sparse LP for a fixed Färe--Grosskopf recipe; an ordered set of node LPs for Lewis--Sexton; a source-specific multi-sector activity LP for Prieto--Zofío. |
| **Defining source** | [Färe and Grosskopf (2000)](https://doi.org/10.1016/S0038-0121(99)00012-9); [Lewis and Sexton (2004)](https://doi.org/10.1016/S0305-0548(03)00095-9); [Prieto and Zofío (2007)](https://doi.org/10.1016/j.ejor.2006.01.015). |
| **Evidence status** | `primary-checked` for the Färe--Grosskopf and Lewis--Sexton executable boundaries. Prieto--Zofío's economic question is confirmed from primary metadata and introductory text, but its programme is `source_not_frozen`, `blocked_on_primary_source`, and deferred to the next version under `source_protocols/prieto_zofio_2007.md`. |
| **Oracle** | For `network.radial.fare_grosskopf_2000`, the input-CRS branch has a `cross-implemented` system-score check against the independently compiled Kao--Hwang primary programme. The output branch has an independent dense source-equation compiler and exact disposal and VRS orientation-separation cases; no published Färe--Grosskopf numerical table is claimed. For `network.sequential.lewis_sexton_2004.forward_radial`, the defining two-organization, three-node example is reproduced: initial inverse process-efficiency vectors $(2,1,1)$ and $(1,2,1)$ yield organizational inverse efficiency $4/3$ and reported efficiency $0.75$ for both organizations. Multi-endpoint min/max aggregation, graph order, invariance, and fail-closed states are also tested. No executable numerical oracle is claimed for Prieto--Zofío. |
| **Package recipe** | Basic intermediate-products slice: `graph.series` + separate process intensities + disposable-surplus link balance + `network.radial.fare_grosskopf_2000`, with input or output orientation inside the same family. Sequential slice: `NetworkData` + an acyclic `NetworkSpec` + `LewisSextonSequentialNetworkDEA`, with nonnegative forward quantities, one global orientation, process-specific standard RTS, and ordered hypothetical-quantity propagation. Reverse quantities, mixed accounts, site-characteristic adjustments, and cross-process aggregation of the same endpoint type are not yet public. No Prieto--Zofío recipe is registered in this version. |
| **Book location** | **Documentation/source review only.** The source-specific Lewis--Sexton sequence and Prieto--Zofío candidate have no independent placement in the current handbook. |

### 1.3 Can management benchmark the connected system without assigning stage scores?

The public Färe--Grosskopf leaf isolates a question that stage-decomposition
models can obscure: what external-resource commitment or final-service
commitment is jointly attainable for the organization as one connected
operating system? It preserves the internal product in the production
opportunity set but does not turn that product into a divisional performance
ratio.

| Evidence field | Record |
|---|---|
| **Economic question** | With internal coordination retained, how far can management contract external resources while preserving final services, or expand final services while preserving the external-resource commitment? |
| **Technology / estimator** | Closed two-process series envelopment with separate upstream $\lambda$ and downstream $\mu$ intensities and $Z\lambda\geq Z\mu$. Input orientation uses $X\lambda\leq\theta x_o$ and $Y\mu\geq y_o$; output orientation uses $X\lambda\leq x_o$ and $Y\mu\geq\phi y_o$. |
| **Measure** | One native system factor: input contraction $\theta_o$ or final-output expansion $\phi_o$. Harmonized efficiency is $\theta_o$ or $1/\phi_o$ respectively; no stage performance measure is attached. |
| **RTS** | CRS for the Färe--Grosskopf source slice. VRS adds $\mathbf1^\top\lambda=\mathbf1^\top\mu=1$ following equations (34)--(35) of Podinovski--Bouzdine-Chameeva (2021); that extension has separate provenance. |
| **Data / time** | Nonnegative external stage-1 inputs, intermediate products stored once, and final stage-2 outputs for homogeneous two-process organizations. “Stored once” prevents duplicate data roles; the evaluated organization's observed intermediate vector is not a fixed condition on its coordinated benchmark. |
| **Native score** | The input branch reports $\theta_o$ and the output branch reports $\phi_o$ as their native factors. Harmonized system efficiency remains higher-is-better on the usual $[0,1]$ self-inclusive domain and equals one when neither the declared resource contraction nor service expansion is available. |
| **Exact aliases** | None at the whole-method level. Under matched CRS roles, reference membership, separate process intensities, and disposable link balance, the system optimum equals the Kao--Hwang primary system optimum by strict primal--dual correspondence. |
| **Distinct variants** | Kao--Hwang stage decomposition; Chen weighted-additive attribution; exact-handoff network SBM; independent stage DEA; general Färe--Grosskopf allocation and dynamic constructions. |
| **Domain** | Exactly two series processes and one link; first-process outputs and second-process inputs coincide with the intermediates; positive aggregate external input/final output and positive reference support; CRS or the separately sourced VRS convexification. |
| **Failures** | Treating the evaluated $z_o$ as a fixed handoff; obtaining the output programme by reciprocating the input optimum; reporting $\lambda$ or $\mu$ as a unique peer account when the optimum is nonunique; reconstructing targets from a thresholded peer display; calling disposable surplus a common link target; deriving stage efficiency from the two intensity vectors; extending the input-CRS Kao--Hwang score identity to output orientation, VRS, or another graph. |
| **Solver form** | One sparse envelopment LP per organization and one compiled quantity block per distinct reference set, followed by independent primal, bound, objective, dual, and reconstructed economic-constraint certification. |
| **Defining source** | Two-node CRS technology and output-distance programme in [Färe and Grosskopf (1996)](https://doi.org/10.1016/0165-1765(95)00729-6); CRS network lineage in [Färe and Grosskopf (2000)](https://doi.org/10.1016/S0038-0121(99)00012-9); explicit VRS polyhedral programme in [Podinovski and Bouzdine-Chameeva (2021)](https://doi.org/10.1007/s11123-021-00610-3). |
| **Evidence status** | `primary-checked`; `implemented/public` as `FareGrosskopfNetworkRadialDEA`. |
| **Oracle** | The conditional input-CRS score identity is checked on the neutral `two_stage_public_service` case against the independently compiled Kao--Hwang primary programme. Output orientation has an independent dense source-equation compiler, exact disposal and VRS orientation-separation cases, and shared implementation/property/failure checks. No published numerical table is redistributed. |
| **Package recipe** | `NetworkData` + `TwoStageSeriesSpec` + `FareGrosskopfNetworkRadialDEA(orientation="input" or "output", returns_to_scale="crs" or "vrs")`; result contract includes one native system factor, harmonized efficiency, one system component, process-specific intensities, complete-intensity external/link targets, link endpoints/surplus, observed-handoff conditioning flags, omitted-intensity sums, and diagnostics, but no stage efficiencies. |
| **Book location** | **Active core placement:** `book/chapters/05-network/network-dea-organizations-links-responsibility.md`. |

Output orientation is exposed inside this same core family, not as another
handbook model. Färe and Grosskopf's open 1995 working paper, published in
1996, freezes the two-node CRS technology, output-distance definition, and
inverse-distance maximization programme. The public closed-series output LP is
a stated restriction of those equations, with a production-independent dense
compiler and analytical oracles. The VRS path composes the output distance
with the separately sourced two-process convex technology and is not
attributed to the CRS paper. The dedicated
`source_protocols/fare_grosskopf_2000_network_output_orientation.md` record
holds the complete source and non-equivalence boundary.

## 2. Sharing credit in linked stages

### 2.1 Should system efficiency be the product of divisional efficiencies?

The basic Kao--Hwang relational model evaluates a two-stage series process
under a common multiplier account. Its defining attraction is an internally
consistent relation between system and stage efficiencies. That product
identity is not a universal law of network production; it follows from the
specific CRS ratio structure and treatment of the intermediate.

| Evidence field | Record |
|---|---|
| **Economic question** | How should overall efficiency and divisional performance accounts be related when one stage's output is the next stage's input? |
| **Technology / estimator** | Basic two-stage series CRS relational technology with a linked intermediate and shared multiplier restrictions. |
| **Measure** | Ratio/relational system efficiency with stage efficiencies constructed under the source normalization. |
| **RTS** | CRS in the canonical Kao--Hwang preset; VRS extensions are distinct formulations. |
| **Data / time** | Cross-sectional external inputs, intermediate products, and final outputs for homogeneous two-stage systems. |
| **Native score** | System efficiency and source-defined stage efficiencies, typically on $[0,1]$, where one denotes efficiency and larger values indicate better measured performance, with the system-stage product identity on the approved domain. |
| **Exact aliases** | Only algebraically identical envelopment/multiplier forms under the same normalization and intermediate treatment. “Two-stage DEA” and “relational DEA” alone are not exact aliases. |
| **Distinct variants** | Independent stage DEA; additive decomposition; centralized radial envelopment; leader--follower models; VRS relational variants; multi-stage networks. |
| **Domain** | Positive or otherwise valid ratio normalizers, one correctly linked intermediate account, and the source's CRS assumptions. |
| **Failures** | Zero denominators; multiplier nonuniqueness; nonunique stage attribution despite a fixed system score; extrapolating the product identity to VRS, shared resources, or general graphs. |
| **Solver form** | Source-normalized multiplier LP or its proven envelopment equivalent; secondary programmes may be required to identify stage-score ranges. |
| **Defining source** | [Kao and Hwang (2008)](https://doi.org/10.1016/j.ejor.2006.11.041). |
| **Evidence status** | `primary-checked`. |
| **Oracle** | The neutral `two_stage_public_service` case checks the system/stage identity, decomposition choices, and feasible split-link projection without retaining a published observation table. |
| **Package recipe** | Implemented as `KaoHwangRelationalDEA` over `NetworkData` and `TwoStageSeriesSpec`: one shared intermediate multiplier account, process-specific intensities, source-qualified stage selection/bounds, and a certified Lim--Zhu dual projection. |
| **Book location** | **Active core placement:** `book/chapters/05-network/network-dea-organizations-links-responsibility.md`; source algebra remains in package documentation. |

### 2.2 Can one relational account cover series and parallel processes?

Kao's general relational construction uses series and parallel composition
rules rather than pretending that every directed graph has one elementary
two-stage identity. Dummy processes can transform a source-admissible network
into serial stages whose members operate in parallel. The accounting
relations then reflect how the organization is composed: serial stage
efficiencies multiply, while a parallel system efficiency is a
virtual-resource-share-weighted average of component efficiencies.

| Evidence field | Record |
|---|---|
| **Economic question** | How should a common organizational performance account be decomposed when some processes follow one another and others provide parallel missions or services? |
| **Technology / estimator** | CRS relational network model with common virtual valuations for the same factor, source dummy-process transformation, serial stages, and parallel components. Kao's later parallel leaf also supplies a source VRS extension. |
| **Measure** | Relational ratio measure. For serial composition the source identity has product form $E_o=\prod_h E_o^h$; for parallel composition it has weighted-average form $E_o=\sum_k\omega_{ko}E_o^k$, where the weights arise from the fitted virtual-resource shares and sum to one on the approved domain. |
| **RTS** | CRS for the general 2009 construction. The 2012 parallel paper develops its own VRS relation; adding free process intercepts to another relational programme is not an equivalent VRS extension. |
| **Data / time** | Cross-sectional process graph with valid input, intermediate, and final-output incidence; factors appearing in several processes must retain the source common-multiplier rule. |
| **Native score** | Higher-is-better system, stage, and process efficiencies plus fitted aggregation shares and reconstruction residuals. A process attribution may be nonunique even when the system value is fixed. |
| **Exact aliases** | The basic Kao--Hwang CRS two-stage series mechanism is a restricted topology in this lineage when normalization, intermediate valuation, and stage definition agree. The general and parallel leaves are not aliases for the current two-stage API merely because that reduction exists. |
| **Distinct variants** | Additive decomposition; Tone--Tsutsui network SBM; Färe--Grosskopf connected envelopment; independent process DEA; shared-resource allocation without a common virtual-value account; VRS formulations with different intercept placement. |
| **Domain** | Positive ratio normalizers, source-admissible series/parallel transformation, consistent factor identities, and a defensible common valuation when one factor appears in several processes. |
| **Failures** | Treating fitted virtual shares as observed physical allocations; using the serial product identity for parallel activities; assuming one VRS construction inherits the CRS decomposition; hiding multiple component decompositions. A later primary critique shows that the 2012 VRS parallel formula can yield negative component values, so no VRS public leaf should be promoted without a domain or corrected score contract. |
| **Solver form** | Source-normalized relational multiplier LP, with secondary range programmes for nonunique process values; the VRS parallel branch requires its own audited formulation. |
| **Defining source** | General series--parallel relation in [Kao (2009)](https://doi.org/10.1016/j.ejor.2007.10.008); parallel CRS/VRS account in [Kao (2012)](https://doi.org/10.1057/jors.2011.16); VRS boundary counterexample in [Peyrache and Silva (2024)](https://doi.org/10.1016/j.omega.2024.103084). |
| **Evidence status** | `primary-checked` for the source composition identities and the VRS warning; equation and numerical-oracle audits remain open. |
| **Oracle** | `not located` for a general-network or parallel executable leaf. |
| **Package recipe** | Current atlas coverage stops at `network.relational.two_stage` and `network.relational.kao_hwang_2008`. Candidate gaps are `network.relational.general.kao_2009` and `network.relational.parallel.kao_2012`, with the VRS branch quarantined until its score-domain issue is resolved. |
| **Book location** | **Evidence-deferred / next version.** The implemented Kao--Hwang two-stage account remains inside the active connected-organization route, but the general-series/parallel candidates have no independent Handbook placement until their equation and numerical-oracle audits close. |

### 2.3 Should divisional shortfalls add to a system shortfall?

The Chen--Cook--Li--Zhu additive approach constructs an overall efficiency
decomposition as a weighted combination of stage performance. It answers a
different attribution question from the relational product model.
Weights and intermediate accounting are part of the identity, not optional
presentation choices.

| Evidence field | Record |
|---|---|
| **Economic question** | How can stage-specific inefficiencies be combined additively into a system account while preserving the intermediate link? |
| **Technology / estimator** | Source-defined two-stage series technology with intermediate balance and the weighting restrictions required by the additive decomposition. |
| **Measure** | Weighted additive/radial stage efficiency account. |
| **RTS** | CRS and the source-defined VRS process-intercept formulation are implemented in the same canonical preset; NIRS/NDRS and other VRS constructions are distinct. |
| **Data / time** | Cross-sectional or statically referenced panel rows with external stage-1 inputs, observed intermediate products, and final stage-2 outputs. Exogenous later-stage inputs require a different additive-network leaf. |
| **Native score** | Source-defined higher-is-better system efficiency, normally with one denoting efficiency, as a weighted average or additive composition of stage efficiencies; components reconstruct the system value under the source identity. |
| **Exact aliases** | None with the Kao--Hwang multiplicative relational identity or Tone--Tsutsui network SBM. |
| **Distinct variants** | Alternative stage weights; centralized versus decentralized allocation; exogenous later-stage inputs; multi-stage additive networks; slack-based additive accounts. |
| **Domain** | Closed nonnegative two-stage series data with positive external-input and intermediate normalizers and reference support. Endogenous virtual-resource shares may reach zero unless an explicit sensitivity restriction is declared. |
| **Failures** | Arbitrary weights masquerading as technical facts; stage targets that fail link balance; using a product decomposition while reporting an additive score; nonunique stage allocations. |
| **Solver form** | Sparse source-normalized multiplier LP with free VRS process intercepts, optional source secondary stage-priority LPs, deterministic weighted-sum reconstruction, and the certified Lim--Zhu primal--dual split-link projection. |
| **Defining source** | [Chen, Cook, Li, and Zhu (2009)](https://doi.org/10.1016/j.ejor.2008.05.011); primal--dual projection and complete corrected numerical account in [Lim and Zhu (2019)](https://doi.org/10.1016/j.omega.2018.06.005). |
| **Evidence status** | `primary-checked`. |
| **Oracle** | The neutral `two_stage_public_service` case checks CRS/VRS system and process reconstruction plus certified split-link projections. The defining papers remain cited for the formulation; their numerical tables and named organizations are not redistributed. |
| **Package recipe** | Implemented as `ChenCookLiZhuAdditiveDEA` over `NetworkData` and `TwoStageSeriesSpec`: one shared intermediate value account, endogenous virtual-resource shares, CRS/VRS process intercepts, process-specific intensities, source-qualified priority selection, and split upstream/downstream link targets. |
| **Book location** | **Active core placement:** `book/chapters/05-network/network-dea-organizations-links-responsibility.md`; the formal source contract remains in package documentation. |

### 2.4 Which process-level slacks prevent the whole system from operating efficiently?

Tone and Tsutsui's network SBM measures input excesses and output shortfalls
inside processes while preserving network links. It is a canonical general
network preset, not the definition of network DEA. Its fractional
normalization and link treatment differ from both relational and additive
radial models.

| Evidence field | Record |
|---|---|
| **Economic question** | Which process-specific resource excesses and output shortfalls account for the organization's system shortfall when adjacent process plans must agree on internal handoffs? |
| **Technology / estimator** | Source-defined network technology with process nodes and link constraints; system and divisional feasibility are solved jointly. |
| **Measure** | Network slacks-based measure with source-defined exogenous process weights. Fixed and free links govern feasibility; the base objective does not score link deviations. |
| **RTS** | Source-qualified CRS/VRS network variants; node and system convexity assumptions remain explicit. |
| **Data / time** | Cross-sectional process inputs, outputs, and links; positive normalizers or an explicit zero policy. |
| **Native score** | Source-native higher-is-better system network-SBM efficiency and process efficiencies, ordinarily with one representing no measured slack inefficiency. |
| **Exact aliases** | None with black-box Tone SBM, relational two-stage DEA, or additive network DEA. |
| **Distinct variants** | Recipient- or supplier-accountable link-scoring specializations; undesirable-link/environmental network SBM; dynamic network SBM; network EBM; directional network models. |
| **Domain** | Valid process/link normalization and a feasible connected graph. All reported targets satisfy the same balances used to score the system. |
| **Failures** | Zero external-account denominators; arbitrary process weights; nonunique process decomposition; reporting independently projected node targets; claiming that the fixed/free base score measures link inefficiency; treating black-box and network scores as directly interchangeable. |
| **Solver form** | Sparse block linear-fractional programme transformed by the source-compatible Charnes--Cooper construction; secondary optimization for alternate stage targets where required. |
| **Defining source** | [Tone and Tsutsui (2009)](https://doi.org/10.1016/j.ejor.2008.05.027). |
| **Evidence status** | `primary-checked`. |
| **Oracle** | `three_process_service_chain` and `crs_free_link_service_chain` check VRS fixed/free and CRS free-link accounts, while project hand fixtures check accountable links and joint target feasibility without claiming one unique LP basis. |
| **Package recipe** | Implemented as `ToneTsutsuiNetworkSBM` (`NetworkSBM`) over `NetworkData`: general connected graph, division-specific intensities, CRS/VRS, input/output/non-oriented accounts, fixed/free continuity, named division weights, one sparse compilation per reference cohort, and solver-selected alternate optima disclosed. |
| **Book location** | **Active core placement:** `book/chapters/05-network/20-network-sbm.md`; the formal programme remains in package documentation. |

## 3. Coordinating internal activities, levels, and shared resources

### 3.1 Which kind of internal structure is the organization managing?

Castelli, Pesenti, and Ukovich organize the early internal-structure
literature around three different departures from an elementary
multi-activity organization. In a shared-flow model, activities compete for
or jointly produce an aggregate resource or service whose internal
allocation is not observed. In a multilevel model, units are nested and the
parent can have quantities that do not belong to any child. In a network
model, an output of one process becomes an input of another. These are
economic distinctions about resource authority, organizational scope, and
production handoffs; they are not three names for the same graph.

| Evidence field | Record |
|---|---|
| **Economic question** | Does the performance account need to represent competition for common resources, nested organizational levels, operational dependence through intermediate production, or a combination of them? |
| **Technology / estimator** | Source taxonomy over an elementary organization of component activities. Shared flow relaxes exclusive component ownership of external inputs or outputs; multilevel structure admits parent-level quantities not assigned to children; network structure admits intermediate output-to-input flows between processes. The taxonomy classifies a study before a measure is attached. |
| **Measure** | None at the classification level. Each branch retains its source-qualified aggregate and component measure; the taxonomy does not supply a generic “internal DEA score.” |
| **RTS** | No common RTS rule. The review's elementary formulations are often introduced under CRS, but shared-flow, multilevel, and network extensions must retain their own system- and component-level scale assumptions. |
| **Data / time** | Component inputs and outputs plus, as applicable, shared-flow totals and allocation status, parent-only quantities and membership, or directed intermediate flows. The classification is cross-sectional; adding time requires a separately specified dynamic structure. |
| **Native score** | No native numerical score. A classification result records the selected structural family, the data roles that justified it, any hybrid roles, and the measure that will determine the eventual result contract. |
| **Exact aliases** | “Shared flow,” “multi-activity,” and “multicomponent” are useful discovery terms for overlapping parts of the literature, and “multilevel” and “hierarchical” are often paired. They are not exact executable aliases without the same allocation, peer, weighting, and aggregation rules. |
| **Distinct variants** | Pure shared flow; pure multilevel hierarchy; intermediate-product network; and hybrids that contain more than one relation. A layered diagram alone does not distinguish a hierarchy from a serial network. |
| **Domain** | Comparable organizations have a defensible component map, and every non-component quantity is declared as a shared flow, a parent-level account, or an intermediate transfer. One observed variable cannot silently play several roles. |
| **Failures** | Treating a shared budget as an intermediate product invents production; copying it into every activity double counts resources. Treating parent-only policy or capacity as a child input changes the managerial scope. Treating a handoff as a freely allocated common resource breaks supplier--recipient feasibility. |
| **Solver form** | No optimizer: this is a validated structural classification and routing protocol. Only the selected source-qualified estimator determines LP, nonlinear, mixed-integer, or multi-step solution requirements. |
| **Defining source** | [Castelli, Pesenti, and Ukovich (2010)](https://doi.org/10.1007/s10479-008-0414-2). |
| **Evidence status** | `primary-checked` for the three-way taxonomy and its structural conditions; individual executable leaves retain their own evidence status. |
| **Oracle** | `not located`; a numerical oracle is not appropriate for the taxonomy itself, and classification examples do not certify any attached estimator. |
| **Package recipe** | Route shared external accounts to `graph.shared_flow`, nested parent--child accounts to `graph.hierarchical`, and intermediate transfers to `graph.general_network`; retain `graph.multi_activity` as the organizational discovery view, and permit an explicit hybrid rather than forcing one label. |
| **Book location** | **Documentation/source review only.** The taxonomy helps route future models, but shared-flow and multilevel mechanisms have no active Handbook placement or executable family merely because the connected-network chapter exists. |

### 3.2 How should a university department share resources between teaching and research?

Beasley's university application is an early shared-input, multi-activity
model. Teaching and research are parallel functions of one department:
general and equipment expenditure are divided between them, while
activity-specific inputs and outputs remain attached to their functions.
There is no teaching output that must become a research input, so the model
is not a two-stage network.

| Evidence field | Record |
|---|---|
| **Economic question** | How efficiently does a department perform its teaching and research missions when the two activities draw on the same expenditure, and what resource split supports the reported mission-level performance? |
| **Technology / estimator** | Two-activity shared-input DEA with activity-specific quantities, endogenous shares of common inputs, and source assurance-region restrictions representing admissible value judgments about allocations and virtual valuations. |
| **Measure** | Source-defined aggregate department efficiency linked to teaching and research efficiency accounts and to the weighted-input shares used in aggregation. |
| **RTS** | The 1995 construction is one source-qualified model, not a generic RTS family. Later VRS shared-flow formulations are distinct leaves and must not be obtained by adding an unverified convexity switch. |
| **Data / time** | Cross-sectional departments in the same discipline, with teaching and research outputs, dedicated inputs, shared expenditure totals, and declared bounds or assurance regions. |
| **Native score** | Higher-is-better source aggregate, teaching, and research efficiency values together with the common-input allocation and binding value restrictions. A result must disclose all four accounts rather than return only the department scalar. |
| **Exact aliases** | None with black-box university DEA, independent teaching and research DEA, Cook--Hababou--Tuenter's component-specific shared-input valuation, a parallel network with duplicated inputs, or a serial teaching-to-research technology. |
| **Distinct variants** | Unrestricted versus assurance-region valuations; fixed observed versus endogenous resource shares; later VRS formulations; shared outputs; more than two activities; physical versus virtual allocation interpretation. |
| **Domain** | Activities and shared totals are defined consistently across departments; allocation shares exhaust each common input; assurance regions have an external substantive basis; denominators satisfy the source normalization. |
| **Failures** | Extreme unrestricted virtual valuations; presenting an optimizer-selected virtual share as observed staff or cash allocation; nonunique teaching/research attribution; double counting the common expenditure; calling parallel missions stages of production. |
| **Solver form** | Source nonlinear DEA programme with resource-share and multiplier interactions plus assurance-region restrictions. It must not be silently replaced by a generic LP or by independently fitted activity models. |
| **Defining source** | [Beasley (1995)](https://doi.org/10.1057/jors.1995.63). |
| **Evidence status** | `review-supported`; the primary problem statement and the source-qualified taxonomy have been checked, while an equation-level implementation audit remains open. |
| **Oracle** | `not located`; no published table has yet been reproduced independently in DEAPack. |
| **Package recipe** | `graph.multi_activity` + `graph.shared_flow` + `network.multi_activity.shared_input.beasley_1995`, retaining activity-specific quantities, common-input shares, assurance regions, aggregate/component values, and allocation multiplicity. |
| **Book location** | **Evidence-deferred / next version.** The shared-resource question is economically distinct, but this source leaf has no active Handbook placement, frozen executable equation contract, or reproduced numerical oracle. |

### 3.3 Should the same shared input carry different values in different bank activities?

Cook, Hababou, and Tuenter study sales and service as components of a bank
branch. Their extension permits the same shared input to receive a different
virtual valuation in each component and uses a change of variables to obtain
a linear model under the source restrictions. That mechanism is more
specific than merely saying that a branch has common staff.

| Evidence field | Record |
|---|---|
| **Economic question** | How well does a branch perform its sales and service functions when both use common resources but may value the operational contribution of those resources differently? |
| **Technology / estimator** | Multicomponent shared-input technology with dedicated component quantities, endogenous common-input allocation, component-specific weights on shared inputs, and the source change of variables linking shares and valuations. |
| **Measure** | Source overall branch performance and component performance accounts under the shared-input reconstruction. |
| **RTS** | Source-qualified scale assumptions only. The component-specific valuation and linearization do not license a generic CRS/VRS toggle. |
| **Data / time** | Cross-sectional branches, sales and service outputs, component-specific inputs, common inputs, and any externally imposed ratio or value restrictions. |
| **Native score** | Source higher-is-better branch, sales, and service values plus transformed shared-input accounts. The result contract also retains recovered allocations where identified, valuation restrictions, and reconstruction residuals. |
| **Exact aliases** | None with Beasley's nonlinear assurance-region model, Cook--Hababou's later additive minimax objective, Cook--Green's overlapping-component/core-business selection, or serial network DEA. |
| **Distinct variants** | Common versus component-specific shared-input valuations; unrestricted versus value-restricted models; ratio versus additive/minimax objective; shared outputs; observed versus endogenous allocation. |
| **Domain** | Component roles and shared-input totals are comparable; the source variable transformation is invertible or its non-identification is reported; added value restrictions remain compatible with the transformation. |
| **Failures** | Treating transformed virtual accounts as unique physical allocations; assuming the linearization survives arbitrary assurance-region constraints; suppressing alternate component decompositions; duplicating common staff in both activities. |
| **Solver form** | Source-transformed multiplier LP when only the audited shared-input restrictions are present. Additional value-judgment constraints can reintroduce nonlinearity and therefore require a separately declared backend. |
| **Defining source** | [Cook, Hababou, and Tuenter (2000)](https://doi.org/10.1023/A:1026598803764). |
| **Evidence status** | `review-supported`; the source mechanism and linearization boundary are checked through the defining source record and the Castelli--Pesenti--Ukovich audit, but no implementation equation audit has been signed off. |
| **Oracle** | `not located`; the Canadian branch application has not been reproduced independently in DEAPack. |
| **Package recipe** | `graph.multi_activity` + `graph.shared_flow` + `network.multi_activity.multicomponent_shared_input.cook_hababou_tuenter_2000`, with component-specific shared-input valuations, transformed accounts, recovery status, and alternate-optimum ranges in the result. |
| **Book location** | **Documentation/source review only.** This shared-input valuation leaf has no independent handbook placement. |

### 3.4 Which business components should each plant retain as its core?

Cook and Green move from measuring several activities to a corporate
specialization decision. Product groupings can overlap: the same observed
output can qualify for more than one business component because each
component can produce it, not because several components jointly create one
indivisible output. Shared inputs are therefore allocated to outputs, and
binary assignment choices identify core-business components across plants.

| Evidence field | Record |
|---|---|
| **Economic question** | Which product groups are genuine operating strengths of each plant, and how might a multi-plant firm specialize locations while ensuring that every plant and every business component remains represented? |
| **Technology / estimator** | Multicomponent shared-input DEA with potentially overlapping output sets, output-level allocation of common inputs, and source assignment restrictions linking plants to selected core-business components. |
| **Measure** | Aggregate and component performance accounts followed by the source core-business selection criterion. Selection is a decision-support layer, not a technical projection onto a serial production frontier. |
| **RTS** | The source develops the model from the CRS DEA setting. A VRS core-business model would require its own assignment and aggregation audit rather than inheritance from the black-box BCC model. |
| **Data / time** | Cross-sectional plants under a common corporate umbrella, dedicated and shared inputs, output-to-component incidence that may overlap, and admissible plant--component assignments. |
| **Native score** | Plant and component performance values, selected core-business assignments, output-level shared-input accounts, assignment coverage, and alternate optimal selections. No single plant score is a complete result. |
| **Exact aliases** | None with Cook--Hababou--Tuenter's non-overlapping sales/service components, a synergistically shared output, a network intermediate, a merger model, or generic portfolio optimization. |
| **Distinct variants** | Performance diagnosis without selection; disjoint versus overlapping components; exogenous versus chosen component incidence; minimum/maximum assignment coverage; specialization with relocation or transition costs. |
| **Domain** | Component definitions reflect corporate strategy; overlap means one output legitimately belongs to several product groupings; common inputs are counted once; every required plant and component satisfies the source coverage rules. |
| **Failures** | Dividing an overlapping output as if it were jointly produced; counting the full shared input in every component; presenting a selected component as causally optimal; ignoring multiple assignment optima or omitted restructuring costs. |
| **Solver form** | Source DEA ratio structure coupled to binary plant--component assignment indicators and coverage constraints. The executable leaf must reproduce the source solution procedure or a proven equivalent mixed-integer reformulation; it is not certified as a plain LP. |
| **Defining source** | [Cook and Green (2004)](https://doi.org/10.1016/S0377-2217(03)00298-4). |
| **Evidence status** | `review-supported`; the primary scope, overlapping-component semantics, and binary selection role are checked, while the full computational formulation still requires an equation audit. |
| **Oracle** | `not located`; neither a published selection table nor an independent implementation has been reproduced in DEAPack. |
| **Package recipe** | `graph.multi_activity` + `graph.shared_flow` + `network.multi_activity.core_business_multiplant.cook_green_2004`, with output incidence, output-level resource allocation, component/plant accounts, assignment decisions, and multiplicity retained. |
| **Book location** | **Documentation/source review only.** Component-selection variants have no current handbook placement. |

### 3.5 How should unit ratings reflect the performance of their organizational groups?

Cook, Chai, Doyle, and Green address organizations in which operating units
belong to districts, plants, hospitals, or other higher-level groups.
Quantities can exist only at the parent level, and a unit can receive
different ratings under alternative groupings. Their hierarchy adjusts and
aggregates level-specific ratings; it does not claim that a parent produces
an intermediate consumed by a child.

| Evidence field | Record |
|---|---|
| **Economic question** | How should a local unit be appraised when its operating conditions and measured performance are partly local and partly inherited from the group to which it belongs? |
| **Technology / estimator** | Source hierarchical/group DEA with homogeneous units within declared comparison groups, higher-level groups treated as units at their own level, level-specific quantities, cross-level score adjustment, and aggregation across alternative groupings. |
| **Measure** | Source ratio efficiency ratings at unit and group levels plus the stated adjustment and grouping-aggregation rules. |
| **RTS** | Source-qualified at each comparison level. Parent and child RTS are not inferred from one another, and a black-box convexity equation does not define hierarchy-wide scale behavior. |
| **Data / time** | Cross-sectional group membership, unit-level quantities, group-level quantities that need not belong to any unit, and alternative groupings where the same unit is appraised in several organizational views. |
| **Native score** | Raw unit and group ratings, adjusted unit ratings, grouping-specific ratings and their source aggregate, with memberships, peer sets, and adjustment factors preserved. |
| **Exact aliases** | “Hierarchical” and “multilevel” identify this broad organizational question, but this leaf is not an exact alias for Cook--Green's simultaneous hierarchy, a shared-input allocation model, categorical/meta-frontier DEA, or a serial network. |
| **Distinct variants** | Sequential versus simultaneous level appraisal; one versus alternative/overlapping groupings; parent-only variables versus allocatable parent resources; fixed versus endogenous aggregation weights. |
| **Domain** | Membership and comparison groups are institutionally meaningful; units compared within a level perform comparable missions; parent-only quantities are not arbitrarily pushed down to children. |
| **Failures** | Comparing nonhomogeneous children; using a high group score as proof that every child is well managed; treating adjustment factors as technical-efficiency decompositions; losing the grouping that generated a unit rating. |
| **Solver form** | Source sequence of normalized multiplier DEA programmes with explicit cross-level adjustment and aggregation stages. It is not one generic network LP, and alternative-grouping aggregation remains part of the protocol. |
| **Defining source** | [Cook, Chai, Doyle, and Green (1998)](https://doi.org/10.1023/A:1018625424184). |
| **Evidence status** | `review-supported`; the primary abstract and source-qualified multilevel formulation map are checked, but an equation-by-equation implementation audit is pending. |
| **Oracle** | `not located`; the source power-plant/group examples have not been independently reproduced in DEAPack. |
| **Package recipe** | `graph.hierarchical` + `network.hierarchical.groups.cook_chai_doyle_green_1998`, retaining the level graph, comparison sets, every raw and adjusted rating, grouping aggregation, and score provenance. |
| **Book location** | **Documentation/source review only.** Hierarchical adjustment variants have no current handbook placement. |

### 3.6 Can plant and generating-unit performance be assessed in one hierarchy?

Cook and Green's power-plant model optimizes performance at the plant level
while producing measures for the generating units that make up each plant.
The simultaneous top-level objective and its allocation of plant-level
quantities distinguish it from the earlier sequential adjustment of group
and unit ratings. It remains an organizational hierarchy, not an
intermediate-product network.

| Evidence field | Record |
|---|---|
| **Economic question** | Which plants perform well as integrated operating entities, which generating units account for the measured result, and how are plant-level quantities represented in the unit accounts? |
| **Technology / estimator** | Two-level source hierarchy with plants as top-level assessed units, generating units as components, a highest-level objective, level-specific factors, and source-defined allocation of plant-level quantities to component accounts. |
| **Measure** | Simultaneously determined plant performance and component-unit performance under the source hierarchy identity. The component values are outputs of the same top-level optimization, not scores from independent unit DEA. |
| **RTS** | Source-qualified hierarchy assumptions. A plant RTS label does not automatically classify every generating unit, and an arbitrary per-level `rts` vector would define another model. |
| **Data / time** | Cross-sectional plants and their generating units, fixed parent--child membership, unit quantities, plant-level quantities, and the source allocation/weighting information. |
| **Native score** | Top-level plant value, every component-unit value, allocated plant-level accounts, common or level-specific virtual valuations, reconstruction residual, and alternate-optimum disclosure. |
| **Exact aliases** | None with the Cook--Chai--Doyle--Green sequential group adjustment, black-box plant DEA, separate unit DEA, Beasley shared-input performance, or a two-stage network. |
| **Distinct variants** | More than two levels; sequential versus simultaneous hierarchy; observed versus endogenous parent allocation; hierarchy with parent-only nonallocatable factors; alternative top-level objectives. |
| **Domain** | Parent--child membership and level-specific quantities are known; the allocation of plant-level accounts has the source meaning; component measures are interpreted as attribution within the optimized plant account, not causal effects. |
| **Failures** | Optimizing units independently and attaching their scores to the plant; forcing all parent quantities into child accounts; confusing organizational nesting with production flow; reporting one arbitrary component decomposition as unique. |
| **Solver form** | Source-normalized simultaneous hierarchy multiplier programme. Before implementation, the equation audit must retain the exact allocation--valuation coupling and establish whether a source-valid reformulation yields an LP or whether a nonlinear backend is required. |
| **Defining source** | [Cook and Green (2005)](https://doi.org/10.1016/j.cor.2003.08.019). |
| **Evidence status** | `review-supported`; the primary simultaneous top-level/component contract is checked, while the complete equations and numerical example remain to be independently audited. |
| **Oracle** | `not located`; no source table has yet been reproduced in DEAPack. |
| **Package recipe** | `graph.hierarchical` + `network.hierarchical.simultaneous.cook_green_2005`, returning the expanded level map, plant and unit accounts from the same solve, parent allocation, reconstruction, and multiplicity. |
| **Book location** | **Documentation/source review only.** This hierarchical source leaf has no current handbook placement. |

### 3.7 Can a divisional appraisal also be used as a feasible network target?

Chen, Cook, Kao, and Zhu show that the familiar multiplier--envelopment
duality from black-box DEA does not automatically carry over to general
network constructions. A multiplier model can provide meaningful
divisional appraisal while its divisional values or implied plan are
infeasible for an envelopment network technology. A target-setting workflow
must therefore certify the production plan rather than relabel multiplier
components as projections.

| Evidence field | Record |
|---|---|
| **Economic question** | Is the reported divisional performance account only an appraisal of where measured shortfall is located, or does it also describe a jointly attainable operating target for the organization? |
| **Technology / estimator** | Diagnostic protocol comparing a source multiplier-based network appraisal with a source envelopment production-possibility model under the same declared graph and data roles; the two are not presumed to be primal and dual formulations of one estimator. |
| **Measure** | Multiplier-based system/divisional efficiency accounts for appraisal, and envelopment-based frontier membership and projection for feasible target setting. |
| **RTS** | Each compared formulation retains its own declared RTS construction. Matching the text label “CRS” or “VRS” is not evidence that their network frontiers coincide. |
| **Data / time** | Cross-sectional general-network inputs, outputs, intermediates, and division map, with enough information to test every projected external and link account. |
| **Native score** | A paired diagnostic result: multiplier system/division values; envelopment frontier/projection result; all projected links and external quantities; feasibility and reconstruction residuals; and an explicit statement of which quantities are appraisal-only. |
| **Exact aliases** | None between the multiplier divisional-appraisal model and the envelopment frontier model under a general network. Standard black-box DEA duality is not an alias certificate. |
| **Distinct variants** | Graphs and restrictions for which an equivalence theorem is proved; divisional-score range analysis; closest versus radial envelopment projections; link-fixed versus endogenous targets. |
| **Domain** | Both formulations are fully specified and evaluated on the same units and variable roles; any claimed equivalence includes its graph, measure, normalization, RTS, and link-control domain. |
| **Failures** | Publishing infeasible divisional targets; calling an envelopment system value a divisional efficiency; assuming a multiplier optimum identifies a unique projection; mixing links or peer systems between the two checks. |
| **Solver form** | Run the source multiplier appraisal and envelopment projection as separate optimization tasks, then certify every network balance and external target. No software-level dual conversion is allowed without a source-backed equivalence proof. |
| **Defining source** | [Chen, Cook, Kao, and Zhu (2013)](https://doi.org/10.1016/j.ejor.2012.11.021). |
| **Evidence status** | `primary-checked` for the non-equivalence result and the appraisal-versus-projection protocol; executable examples still require an independent numerical audit. |
| **Oracle** | `not located`; the paper's counterexamples have not yet been reproduced in DEAPack, so structural property tests cannot be presented as a numerical oracle. |
| **Package recipe** | Apply `network.projection.frontier_validity.chen_cook_kao_zhu_2013` to a named multiplier leaf and a named envelopment leaf over the same expanded graph; retain both result identities, projection targets, link-feasibility certificate, and any non-equivalence finding. |
| **Book location** | **Documentation/source review only.** Target-construction details remain in package documentation and this source review. |

### 3.8 Are intermediates observed commitments or endogenous coordination choices?

An observed intermediate can be fixed at its realized level, constrained
within a range, or allowed to change jointly with upstream and downstream
targets. These choices alter the feasible set. Fixed-link evaluation asks
how well the organization performed given the observed handoff; endogenous
evaluation asks how well it could perform after internal coordination.

| Evidence field | Record |
|---|---|
| **Economic question** | Is the intermediate handoff inherited, partly negotiable, or fully coordinated by the organization? |
| **Technology / estimator** | A series or general network with link controllability (`fixed`, `bounded`, or `endogenous`) and balance (`exact`, inequalities, loss, or transformation) specified separately. |
| **Measure** | Any supported network measure; link-control semantics belong to the technology rather than the objective. |
| **RTS** | Node-specific and system assumptions explicit. Link controllability does not determine RTS. |
| **Data / time** | Observed link quantities, bounds or transformation coefficients where applicable, and external process inputs/outputs. |
| **Native score** | Inherited from the attached network measure; targets include feasible link quantities and any allocation change. |
| **Exact aliases** | None among fixed, bounded, and endogenous intermediates. Equality of numerical results in one dataset is not model equivalence. |
| **Distinct variants** | Fixed-link diagnostic; centralized endogenous coordination; exogenous second-stage inputs; lossy or quality-adjusted links; undesirable intermediates. |
| **Domain** | Link units and direction are known; transformation/loss parameters are externally justified; bounds are not inferred from the assessed unit alone. |
| **Failures** | Endogenous links can create implausible internal reallocation; fixed links can attribute inherited constraints to stage management; missing link observations can make process attribution unidentified. |
| **Solver form** | Additional sparse link rows and variables in a cooperative LP; discrete or nonlinear transformations require a separate backend. |
| **Defining source** | Taxonomy in [Kao (2014)](https://doi.org/10.1016/j.ejor.2014.02.039); restrictive two-stage equivalence domains in [Cook, Liang, and Zhu (2010)](https://doi.org/10.1016/j.omega.2009.12.001). |
| **Evidence status** | `review-supported`; every public leaf requires its exact source formulation. |
| **Oracle** | `not located`. |
| **Package recipe** | `LinkSpec(source, target, role, controllability, balance, transform)` inside a named graph and measure. |
| **Book location** | **Bounded active comparison.** The source-qualified fixed/free handoff choice is taught inside `book/chapters/05-network/20-network-sbm.md`; bounded, lossy, transformed, and other link-policy candidates remain Documentation-only or evidence-deferred according to their own source gates. |

### 3.9 How should common resources be allocated across parallel processes?

Parallel activities often draw on one staff, capital, budget, or energy pool.
The pool can be observed as a fixed allocation or optimized subject to a
total commitment. In either case, it is counted once. Common versus
node-specific intensity vectors create another independent distinction:
common intensities enforce an integrated peer mix, whereas node-specific
intensities permit different process peers subject to links and resource
balances.

| Evidence field | Record |
|---|---|
| **Economic question** | Could the organization perform better by coordinating shared resources across parallel services, and which processes would receive them? |
| **Technology / estimator** | Parallel or general graph with an explicit resource pool, incidence set, allocation constraints, and common or node-specific intensity policy. |
| **Measure** | Supported system/process radial, additive, directional, SBM, or economic objective. |
| **RTS** | Declared by process; resource pooling can create system scale effects that are not captured by a black-box scale-efficiency ratio. |
| **Data / time** | Total shared-resource commitment, observed allocations if available, eligible processes, process-specific inputs and outputs, and any transfer costs. |
| **Native score** | Attached measure's system score plus one feasible allocation and process targets; allocation or process scores may be interval-valued under alternate optima. |
| **Exact aliases** | None between common and node-specific intensity systems, or between observed and endogenous resource allocation. A common virtual multiplier for one factor in Kao's parallel relational account is not an alias for a physical allocation of that factor. |
| **Distinct variants** | Beasley-style endogenous shared-input allocation; Kao-style parallel relational decomposition; shared output; common budget; joint production; hierarchical allocation; partial input--output incidence; and multi-plant networks. |
| **Domain** | Resource totals and incidence are known; allocations sum to the pool; transferability and process eligibility are economically defensible. |
| **Failures** | Double counting; free transfer across units that cannot exchange the resource; arbitrary allocation selected from multiple optima; process scores based on incompatible peer mixes. |
| **Solver form** | Sparse block LP with pool-balance variables; secondary lexicographic or range LPs for allocation multiplicity; nonconvex allocation rules require a separate solver. |
| **Defining source** | Physical shared-input allocation in [Beasley (1995)](https://doi.org/10.1057/jors.1995.63); common-valuation parallel decomposition in [Kao (2012)](https://doi.org/10.1057/jors.2011.16); general classification in [Kao (2014)](https://doi.org/10.1016/j.ejor.2014.02.039) and the [Network DEA Handbook](https://doi.org/10.1007/978-1-4899-8068-7). |
| **Evidence status** | `primary-checked` for the allocation-versus-common-valuation boundary; individual executable leaves remain `review-supported`. |
| **Oracle** | `not located`; `network.shared_resource` is planned. |
| **Package recipe** | `graph.parallel` or `graph.general_network` + `network.shared_resource` + `ResourcePoolSpec` + `intensity_policy`. The planned Beasley source leaf names one shared-input lineage; a Kao parallel relational leaf is a separate atlas gap. |
| **Book location** | **Evidence-deferred / next version.** `ResourcePoolSpec` and an executable shared-resource family are planned; the current Handbook does not claim this programme as part of its connected-network route. |

### 3.10 Who has authority to choose the linked plan?

Centralized cooperation, leader--follower control, bargaining, and
non-cooperative behavior describe different governance institutions. They
can select different targets over the same physical graph. A governance rule
therefore belongs in the study specification and can change the mathematical
programme, not merely the label on a chart.

| Evidence field | Record |
|---|---|
| **Economic question** | Who controls intermediate quantities and shared resources, and how are conflicting divisional objectives reconciled? |
| **Technology / estimator** | One declared physical production graph combined with centralized, cooperative, Stackelberg, bargaining, or non-cooperative decision rights. |
| **Measure** | System objective, leader/follower objectives, Nash or bargaining solution, or another source-qualified governance criterion. |
| **RTS** | Inherited from the physical node technologies; governance does not repair an unidentified RTS account. |
| **Data / time** | Process quantities plus priorities, reservation values, transfer valuations, or move order required by the governance model. |
| **Native score** | Source-native system/divisional efficiency or bargaining/governance outcome; no universal efficiency interval applies to every game form. |
| **Exact aliases** | None among centralized, cooperative, leader--follower, bargaining, and non-cooperative evaluations in general. Under Liang--Cook--Zhu's closed two-stage source domain with exactly one intermediate measure, their centralized and non-cooperative models reduce to the separately fitted stage results and give a unique decomposition. That equality is not guaranteed when there are multiple intermediates. |
| **Distinct variants** | Common-weight relational models; decentralized transfer pricing; Nash bargaining; Stackelberg stage leadership; fixed-priority lexicographic coordination. |
| **Domain** | Decision rights and preference/valuation information are substantively justified; equilibria or bargaining solutions exist under the selected formulation. |
| **Failures** | Multiple or nonexistent equilibria; arbitrary priorities; calling a planner optimum decentralized behavior; hiding normative bargaining weights inside technical efficiency; extending the one-intermediate equivalence to several intermediates, where the centralized decomposition may be multiple even when the non-cooperative construction selects one. |
| **Solver form** | Liang--Cook--Zhu's source two-stage game models are linear. Other cooperative problems can be LPs where objectives align; bilevel, complementarity, iterative, or mixed-integer/nonlinear formulations remain necessary where the defining governance model requires them. |
| **Defining source** | Two-stage centralized/non-cooperative game construction and conditional equivalence in [Liang, Cook, and Zhu (2008)](https://doi.org/10.1002/nav.20308); taxonomy and relationship audit in [Cook, Liang, and Zhu (2010)](https://doi.org/10.1016/j.omega.2009.12.001); wider governance families in [Kao (2014)](https://doi.org/10.1016/j.ejor.2014.02.039). |
| **Evidence status** | `primary-checked` for the Liang--Cook--Zhu mechanism and its conditional equivalence; other game-theoretic leaves remain `registry-provisional`. |
| **Oracle** | `not located`. |
| **Package recipe** | Physical `NetworkSpec` + `network.governance` + source-qualified objective, move order, and solution concept. `network.governance.two_stage.liang_cook_zhu_2008` is a candidate source leaf missing from the current atlas, not an alias for the implemented Kao--Hwang preset. |
| **Book location** | **Evidence-deferred / next version.** Governance mechanisms remain source candidates and planned semantic vocabulary; they have no active Handbook placement or public network-governance API. |

## 4. Judging present decisions whose effects persist

### 4.1 Is today's intermediate also tomorrow's productive state?

Färe and Grosskopf's intertemporal production framework links activities
over time through intermediate stocks or flows. It defines a multi-period
attainable plan and can support technical or economic objectives. This is
genuine dynamic production because changing a current link changes future
feasibility.

| Evidence field | Record |
|---|---|
| **Economic question** | Which multi-period production plans are attainable when current production creates or consumes quantities needed in later periods? |
| **Technology / estimator** | Intertemporal production technology represented as a time-linked activity network with explicit temporal intermediates and boundary conditions. |
| **Measure** | Source-compatible input/output distance, revenue, cost, profit, or multi-period efficiency criterion. |
| **RTS** | Declared for period activities and the intertemporal technology; source examples do not justify one universal dynamic RTS. |
| **Data / time** | Multi-period quantities, temporal links, initial stock/state, terminal treatment, and any period valuations. |
| **Native score** | Source-specific multi-period technical or economic performance value; no universal dynamic efficiency ratio. |
| **Exact aliases** | A time-expanded network is an internal representation, not an exact public alias for static network DEA. |
| **Distinct variants** | Nemoto--Goto investment model; Tone--Tsutsui carry-over SBM; dynamic network SBM; ordinary window DEA; repeated static productivity indexes. |
| **Domain** | Temporal link units match across periods; initial and terminal states are defined; the time horizon and information set are explicit. |
| **Failures** | Omitting initial stocks; leaving terminal assets valueless; double-counting temporal links as both external and internal quantities; retrospective perfect foresight mislabeled as an ex-ante plan. |
| **Solver form** | Sparse time-expanded block LP for linear technologies/objectives; alternative economic objectives can require a source-specific convex programme. |
| **Defining source** | [Färe and Grosskopf (1996), *Intertemporal Production Frontiers*](https://doi.org/10.1007/978-94-009-1816-0). |
| **Evidence status** | `metadata_confirmed / equation_not_frozen / deferred_to_next_version`. The official monograph record and limited preview confirm the dynamic-production lineage, but the complete defining chapter was not obtainable; the controlling boundary is `source_protocols/fare_grosskopf_1996_intertemporal.md`. |
| **Oracle** | `not located`; accessible applications freeze narrower technologies but provide neither the complete defining account nor a reproducible observation-level oracle for the umbrella family. |
| **Package recipe** | No current recipe or public API. The candidate composition remains an explicit intertemporal technology + temporal links + boundary policy + source-qualified measure and information set. |
| **Book location** | **Active conceptual lineage only:** the existing dynamic chapter teaches why a state-dependent path differs from repeated annual comparisons, but presents no Färe--Grosskopf equations or executable recipe. |

### 4.2 Does investment change quasi-fixed productive capacity?

Nemoto and Goto model investment, quasi-fixed inputs, adjustment costs, and
intertemporal substitution. The relevant managerial question is not simply
whether capital is a “good carry-over.” It is whether the firm chose an
intertemporal path of investment and variable inputs efficiently once
changing productive capacity is costly.

| Evidence field | Record |
|---|---|
| **Economic question** | Did the firm choose investment and variable-input paths efficiently when capital adjusts gradually and today's investment changes tomorrow's production possibilities? |
| **Technology / estimator** | Dynamic production/investment technology with quasi-fixed capital, investment transition, adjustment costs, and intertemporal first-order or frontier conditions. |
| **Measure** | Source-defined dynamic productive inefficiency or intertemporal economic performance criterion. |
| **RTS** | Source-specific production and adjustment technology assumptions; not inferred from a static capital-input DEA. |
| **Data / time** | Panel of outputs, variable inputs, quasi-fixed stocks, investment, adjustment-cost information, prices/discounting where required, and initial capital. |
| **Native score** | Source-native dynamic inefficiency or objective gap; it is not a Tone dynamic-SBM score. |
| **Exact aliases** | None with a beneficial carry-over SBM, capacity utilization, or period-by-period cost efficiency. |
| **Distinct variants** | Alternative adjustment-cost functions; imperfect foresight; irreversible investment; depreciation; Färe--Grosskopf intertemporal activity technology. |
| **Domain** | Identified stock transition and adjustment technology; economically meaningful horizon, discounting, and information assumptions. |
| **Failures** | Treating investment and capital stock as interchangeable; ignoring depreciation or terminal capital; confusing numerical period weights with discount factors; insufficient data to identify adjustment costs. |
| **Solver form** | Source-specific multi-period optimization; LP only when the production and adjustment representation admits it, otherwise a documented convex/nonlinear backend. |
| **Defining source** | [Nemoto and Goto (1999)](https://doi.org/10.1016/S0165-1765(99)00070-1). |
| **Evidence status** | `primary-checked` only at the economic-lineage level. The 1999 and 2003 defining texts were not obtainable for a complete equation audit; the executable route is `deferred_to_next_version` under `source_protocols/nemoto_goto_dynamic_investment.md`. |
| **Oracle** | `not located`; no source-form numerical account is available in the audited environment. |
| **Package recipe** | No current recipe or public API. The candidate composition remains `dynamic.investment.nemoto_goto` + stock transition + adjustment-cost form + information/discount policy. |
| **Book location** | **Active conceptual boundary only:** the existing dynamic chapter distinguishes quasi-fixed capital adjustment from carry-over continuity, but presents no Nemoto--Goto equations or executable recipe. |

### 4.3 Does one overall multi-period rating imply dynamic production?

No. Park and Park construct an aggregative efficiency measure from a DMU's
time-series input and output account. That is a legitimate joint appraisal
of several periods, but it does not introduce a stock, carry-over, or
transition that makes an action in period $t$ constrain feasible production
in period $t+1$. It belongs beside, rather than inside, the dynamic
production technologies.

| Evidence field | Record |
|---|---|
| **Economic question** | How can a board obtain one defensible rating for several observed operating periods without averaging unrelated annual efficiency scores? |
| **Technology / estimator** | Source multi-period extension of Debreu--Farrell appraisal over time-indexed inputs and outputs. Period-specific composite weights are unknown positive DEA weights estimated by the base programme; the source model has no interperiod state equation and does not expose time-preference or assurance-region options. |
| **Measure** | One common input- or output-oriented radial factor across all contemporaneous period technologies, followed by a strict lexicographic phase that fixes the factor and maximizes the source's unnormalized sum of input and output slacks. |
| **RTS** | The base model places one VRS convexity equation on each period-specific peer plan. The source CRS variant deletes every one of those equations. Mixed period RTS, NIRS, and NDRS are not part of the 2009 preset. |
| **Data / time** | Complete balanced trajectories for the same organizations over at least two periods, with stable input and output definitions. Every period has a separate contemporaneous peer plan; no carry-over observation is required. |
| **Native score** | Output orientation natively reports $\phi\geq1$ with smaller values better; a harmonized package score is $1/\phi$. Input orientation reports $\theta\leq1$. Period-indexed targets and slacks explain the joint rating, but they are not separate period efficiencies or productivity-change components. |
| **Exact aliases** | None with the arithmetic or user-weighted average of annual DEA scores; the source explicitly develops a joint production appraisal because those simple summaries need not retain DEA feasibility. |
| **Distinct variants** | Window DEA; pooled-panel DEA; Malmquist productivity; Tone--Tsutsui dynamic SBM; Färe--Grosskopf temporal links; adjustment-cost dynamic efficiency. |
| **Domain** | Nonnegative finite traditional inputs and desirable outputs, complete balanced DMU--period trajectories, positive orientation normalizers, stable variable meanings, and a defensible contemporaneous comparison population in every period. Bad outputs and pooled-across-period reference technologies are outside this source leaf. |
| **Failures** | Calling one multi-period scalar a dynamic production score; treating the endogenous multiplier weights as time preference or discounting; omitting the second phase and thereby confusing radial and strong efficiency; treating aggregate efficiency as technical change; presenting a unit-dependent farthest-slack target or one alternate peer basis as uniquely easiest to implement. |
| **Solver form** | Source linear programme after the stated multi-period radial construction, followed by the source slack phase. Explicit time preferences and assurance-region restrictions are mentioned as future research rather than options in the 2009 base model. |
| **Defining source** | [Park and Park (2009)](https://doi.org/10.1016/j.ejor.2007.11.028). |
| **Evidence status** | `primary-equation-checked` and implemented/public: Eqs. (14) and (16), the per-period VRS/CRS construction, two-phase objective, no-transition boundary, and pp. 568--580 interpretation have been checked. |
| **Oracle** | `multiperiod_trajectory_contrast` checks the VRS output-oriented factors, full/weak/inefficient classifications, period slack accounts, and projection identities while deliberately not basis-locking alternate peers or individual slacks. |
| **Package recipe** | Public `panel.multiperiod_aggregative.park_park_2009`, exposed as `ParkParkMultiperiodAggregativeDEA` and exact alias `MultiperiodAggregativeDEA`, with explicit input/output orientation, uniform CRS/VRS choice, contemporaneous period technologies, strict two-phase solution, and fail-closed certification. |
| **Book location** | **Documentation/source review only.** This multiperiod aggregation protocol has no current handbook placement. |

### 4.4 Is persistence best represented as a typed carry-over?

Tone and Tsutsui's dynamic SBM links adjacent periods through carry-overs and
uses slacks to evaluate the whole horizon. The historical labels desirable,
undesirable, free, and fixed are valuable for discovery. For a general
compiler they should be expanded into independent economic properties:

```text
effect  = beneficial | harmful | neutral
control = endogenous | fixed | bounded
balance = exact | at_least | at_most | transition
lag, decay, initial_policy, terminal_policy
```

This prevents one historical word from determining both whether a stock
helps future production and whether management can change it.

| Evidence field | Record |
|---|---|
| **Economic question** | How efficient is the operating plan over the full horizon when assets, knowledge, inventory, debt, backlog, customers, or environmental liabilities persist between periods? |
| **Technology / estimator** | Time-expanded process technology with adjacent-period carry-over balance and the source's desirable, undesirable, free, and fixed categories. |
| **Measure** | Tone--Tsutsui dynamic slacks-based measure with overall and period performance. |
| **RTS** | Source CRS removes every period convexity equation; source VRS imposes one convexity equation for every period-specific peer plan. One horizon-wide convexity equation is not equivalent. |
| **Data / time** | Complete balanced trajectories with positive period inputs/outputs, carry-over quantities and types, explicit period order, one common trajectory cohort, source boundary policy, and optional positive period/item importance weights. The base preset has no pre-sample initial condition or inferred terminal value. |
| **Native score** | Source-native higher-is-better overall dynamic-SBM efficiency and period efficiencies, normally with one representing no measured horizon-wide slack inefficiency. |
| **Exact aliases** | Historical Tone--Tsutsui carry-over labels are preset names over the exact source formulation. They are not exact aliases for every modern `effect/control/balance` combination. |
| **Distinct variants** | Färe--Grosskopf intertemporal technology; Nemoto--Goto investment model; dynamic directional/radial models; dynamic network SBM; harmful stock with endogenous versus fixed control. |
| **Domain** | Strictly positive slack normalizers; complete balanced period sequence; same peer membership in every period; exact same-$Z_t$ adjacent continuity; source terminal balance and declared boundary policy. |
| **Failures** | Treating repeated static or window scores as dynamic production; replacing same-$Z_t$ continuity by a different transition equation; arbitrary terminal treatment; categorizing a harmful fixed liability as an endogenous “bad link”; period weights interpreted as discount factors without an economic objective; multiple optimal period targets; confusing base, ex-post adjusted, and mixed-integer free-carry-over scores. |
| **Solver form** | One compiled sparse time-block LP for input/output orientations and the Charnes--Cooper form of the non-oriented model; one primary solve per trajectory. Period-range analysis and the source free-carry-over MIP are separate future procedures. |
| **Defining source** | [Tone and Tsutsui (2010)](https://doi.org/10.1016/j.omega.2009.07.003). |
| **Evidence status** | `primary-checked`; the open discussion-paper text and published source boundaries were reconciled, and the later critique remains a distinct method leaf. |
| **Oracle** | `dynamic_carryover_portfolio` checks overall and period accounts for the named ex-post free-carry-over adjustment, with project hand cases for all three orientations and all four carry-over roles. |
| **Package recipe** | Implemented as `ToneTsutsuiDynamicSBM` (`DynamicSBM`) over `DynamicData`, `DynamicSBMSpec`, `PeriodProductionSpec`, and typed `CarryOverSpec`; CRS/VRS, three orientations, base and named ex-post adjustment, fixed external accounts, full result tables, and source-qualified metadata are public. |
| **Book location** | **Active core placement:** `book/chapters/06-dynamic/dynamic-dea-carryovers-trajectories.md`; the exact source contract remains in package documentation. |

### 4.5 Should a dynamic shortfall count adjustment-cost slacks?

An investment model and a carry-over SBM can both be non-radial without
becoming the same method. Aparicio and Kapelko attach a weighted-additive
shortfall to an adjustment-cost technology in the full
$(x,I,y,k)$ input--investment--output--capital space. In compact notation
its native account has the form

$$
WA_o^D
=
\max\left\{
\sum_i w_i^x s_{io}^x
+\sum_r w_r^y s_{ro}^y
+\sum_\ell w_\ell^I s_{\ell o}^I
:\ (s^x,s^y,s^I)\text{ satisfy the dynamic investment technology}
\right\}.
$$

The capital stock is connected through the investment constraints; it is not
silently scored as another ordinary input slack.

| Evidence field | Record |
|---|---|
| **Economic question** | Which specific resource, service, and investment gaps explain dynamic underperformance when changing quasi-fixed capacity itself consumes organizational resources? |
| **Technology / estimator** | Nonparametric adjustment-cost production technology with variable inputs, desirable outputs, gross investment, quasi-fixed capital, and an explicit stock/investment relation. |
| **Measure** | Dynamic weighted-additive technical inefficiency in the full adjustment space. |
| **RTS** | Source technology only; static additive-model RTS labels and Tone--Tsutsui period convexity rules do not transfer automatically. |
| **Data / time** | Firm panel with variable inputs, outputs, investment, quasi-fixed stocks, valid transition timing, and declared slack weights. |
| **Native score** | Nonnegative additive dynamic inefficiency in the chosen units/normalization, decomposed by input, output, and investment item. It is not a bounded higher-is-better SBM efficiency. |
| **Exact aliases** | None with Tone--Tsutsui dynamic SBM, static weighted-additive DEA, or a directional dynamic distance unless an explicit source transformation and matched weights are proved. |
| **Distinct variants** | Radial and directional adjustment-cost measures; dynamic cost and allocative inefficiency; input indivisibilities; by-production/environmental dynamic technologies. |
| **Domain** | Identified timing and stock transition, economically defensible investment quantities, admissible weights, and the paper's convex dynamic technology. |
| **Failures** | Scoring capital twice; confusing gross investment with the stock; omitting depreciation or boundary stocks; reporting a unit-dependent additive value as a universal percentage; importing Tone carry-over categories into adjustment-cost theory. |
| **Solver form** | Source weighted-additive LP over a compiled adjustment-cost technology. |
| **Defining source** | [Aparicio and Kapelko (2019)](https://doi.org/10.1016/j.ejor.2018.08.045), which explicitly separates the carry-over/network and adjustment-cost lineages before constructing the measure. |
| **Evidence status** | `primary-checked` for the lineage, variable roles, and native objective; equation-level package freeze and oracle reproduction remain open. |
| **Oracle** | `candidate`: the article's dairy-manufacturing application is published, but no independent DEAPack reproduction exists. |
| **Package recipe** | `dynamic.investment.nemoto_goto`-compatible adjustment technology + candidate `dynamic.weighted_additive.adjustment_cost.aparicio_kapelko_2019`. The current atlas has the technology umbrella but not this measure leaf. |
| **Book location** | **Documentation/source review only.** This adjustment-cost slack leaf has no current handbook placement. |

### 4.6 Do internal processes and temporal states matter simultaneously?

Dynamic network SBM combines within-period process links with between-period
carry-overs. It is not obtained by fitting a static network separately in
every period and averaging the scores. Every system, process, and temporal
target must be feasible in one integrated plan.

| Evidence field | Record |
|---|---|
| **Economic question** | Where and when is performance lost when both internal process coordination and persistent assets or obligations constrain the organization? |
| **Technology / estimator** | Time-expanded general production graph containing process links within periods and carry-over links across periods. Every within-period link preserves supplier--recipient continuity; link kind changes observed-value commitment and slack-account ownership, not whether the two process plans remain connected. |
| **Measure** | Source-defined dynamic network SBM with system, division, and period accounts. |
| **RTS** | Source CRS/VRS choice by division. Division-specific mixed CRS/VRS is permitted, but the published source states that overall system RTS cannot be decided in the mixed case. |
| **Data / time** | Process-level multi-period quantities, within-period intermediates, cross-period carry-overs, and explicit boundary data/policy. Source period and division weights are nonnegative and sum to one; a zero weight removes an account from the score, not from feasibility. |
| **Native score** | Source-native higher-is-better overall, divisional, and period dynamic-network efficiencies, normally with one denoting efficiency under the canonical preset; all components obey the source identity. |
| **Exact aliases** | None with static network SBM, dynamic black-box SBM, window DEA, or Malmquist productivity. |
| **Distinct variants** | Environmental dynamic networks; parallel dynamic networks; alternative carry-over controls; directional or economic dynamic-network objectives; Chen's lagged influence of intermediates on later process outputs. |
| **Domain** | Complete graph and time indexing; valid link/carry-over normalizers; source--recipient continuity for every within-period link; jointly feasible and explicitly named boundary conditions. |
| **Failures** | Fitting each period independently; compiling as-input or as-output as a one-ended feasible link; incompatible within-period and temporal targets; double counting a carry-over; requiring strictly positive source weights; reporting overall RTS under mixed division-level CRS/VRS; inventing or silently dropping a terminal carry-over; component weights that do not reconstruct the system score; severe block-size growth. |
| **Solver form** | Large sparse block linear-fractional programme with time/process structure; Charnes--Cooper transformation for the canonical SBM preset. |
| **Defining source** | [Tone and Tsutsui (2014)](https://doi.org/10.1016/j.omega.2013.04.002). A distinct lagged-intermediate dynamic-network account is defined by [Chen (2009)](https://doi.org/10.1016/j.ejor.2007.12.025). |
| **Evidence status** | `primary-checked`; the formal link equations and their continuity statement have been checked, the terminal carry-over index is confirmed internally inconsistent in the published notation, and the implemented resolution is named explicitly. |
| **Oracle** | `analytically derived` for one deliberately joint non-oriented CRS fixture: an independently assembled 23-variable/19-equality dense Charnes--Cooper programme has matching exact rational primal and dual objectives of $2/3$, public link/carry-over targets and period-process accounts reconstruct the same result, and deleting either continuity mechanism changes the optimum. This is not a reproduction of the anonymous electricity application and does not inherit to other directions, RTS, weights, roles, or boundary rules. |
| **Package recipe** | `graph.dynamic_network` + `dynamic.network_sbm.tone_tsutsui_2014` + process links + typed carry-overs + a named boundary resolution and weight policies. `dynamic.network_lagged_intermediate.chen_2009` is a candidate atlas gap, not an option on the Tone--Tsutsui preset. |
| **Book location** | **Documentation/source review only.** Dynamic-network SBM is an intersection of two core families, not an independent handbook chapter. |

For a link from supplier $k$ to recipient $h$, all four source cases keep
the coordination condition

$$
Z^{(k,h)}\lambda^k=Z^{(k,h)}\lambda^h.
$$

A fixed link additionally makes both endpoints reproduce the observed
handoff, whereas a free link chooses their common handoff endogenously. An
as-input link adds the recipient's input-style account
$Z^{(k,h)}\lambda^h+s^-=z_o^{(k,h)}$; an as-output link adds the supplier's
output-style account
$Z^{(k,h)}\lambda^k-s^+=z_o^{(k,h)}$. Thus as-input and as-output place
the scored link term in one division while retaining bilateral
feasibility. The open network-SBM discussion paper states the same structure
in Eqs. (5c)--(5d); these roles must not be implemented as a recipient-only or
supplier-only technology.

The formal published equations have been checked and contain a terminal-index
inconsistency that must remain visible. The data definition describes
carry-over observations for $t=1,\ldots,T-1$, whereas Eq. (9) and the
objective notation include carry-over terms indexed through $T$. This
review does not repair the source by assumption. An executable leaf must name
its initial/terminal boundary resolution, state which observed quantities
exist, and identify any source extension separately.

The dynamic literature review by
[Mariz, Almeida, and Aloise (2018)](https://doi.org/10.1111/itor.12468)
supports keeping the Färe--Grosskopf, investment/quasi-fixed-factor, and
typed carry-over lineages separately discoverable.

## 5. Scale and productivity in structured organizations

### 5.1 Can black-box scale and productivity results be reused?

Link balances, process-specific RTS, shared resources, and carry-overs alter
the attainable comparison. Consequently, a ratio of black-box CRS and VRS
scores is not automatically network scale efficiency, and an ordinary
Malmquist index over final outputs is not automatically network or dynamic
productivity.

| Evidence field | Record |
|---|---|
| **Economic question** | Did structured-system performance change because processes improved, links were coordinated differently, scale changed, or the network/dynamic opportunities changed? |
| **Technology / estimator** | One source-qualified network or dynamic technology retained in every scale and cross-period component task. A broad graph plus the word “Malmquist” does not identify an estimator. |
| **Measure** | One source-defined network scale/RTS operator or network/dynamic productivity operator with a proven system/process identity. The generic labels below are discovery families, not measures. |
| **RTS** | Node, system, and temporal scale assumptions explicitly defined; no automatic inheritance from black-box DEA and no generic `rts=` switch across structured measures. |
| **Data / time** | Process-level panel, stable graph or an explicit graph-change policy, links/carry-overs, and resource pools. |
| **Native score** | Source-specific scale classification/ratio or multiplicative/additive network productivity result with system/process reconstruction. Chen--Zhu scale efficiency and Kao--Hwang common-weight global MPI retain their own component identities. |
| **Exact aliases** | None with black-box scale efficiency, window DEA, ordinary MPI, or an average of period network scores. |
| **Distinct variants** | Chen--Zhu two-stage scale efficiency; two-stage scale elasticity/RTS; Kao--Hwang common-weight global MPI; distance-based network Malmquist; Sueyoshi--Sekitani RTS for the Nemoto--Goto quasi-fixed-input technology; Sengupta's discounted-cost optimal-control model; dynamic efficiency change; carry-over productivity; changing-topology productivity. They may share graph blocks but not a public executable ID. |
| **Domain** | Same process mission and link semantics across compared periods, or a source-defined mapping between changing graphs; all cross-period structured tasks feasible. |
| **Failures** | Ignoring intermediate quantities in productivity; comparing stage scores whose aggregation changed; attributing topology redesign to technical change without disclosure; using repeated static averages as dynamic productivity. |
| **Solver form** | Source specific: Chen--Zhu's two-stage scale transformation requires conic-capable optimization, while Kao--Hwang's common-weight multi-period construction requires its linked multiplier programs and productivity reconstruction. A generic task DAG is infrastructure only. |
| **Defining source** | Two-stage scale efficiency in [Chen and Zhu (2019)](https://doi.org/10.1080/01605682.2017.1421850); common-weight two-stage MPI in [Kao and Hwang (2014)](https://doi.org/10.1016/j.ejor.2013.07.030); dynamic RTS in [Sueyoshi and Sekitani (2005)](https://doi.org/10.1016/j.ejor.2003.08.055); discounted-cost and capital adjustment in [Sengupta (1999)](https://doi.org/10.1016/S0925-5273(98)00244-8); intertemporal production in [Färe and Grosskopf (1996)](https://doi.org/10.1007/978-94-009-1816-0) and [their handbook chapter](https://doi.org/10.1007/978-1-4419-6151-8_5); dynamic-SBM chapter in [Tone and Tsutsui (2014)](https://doi.org/10.1002/9781118946688.ch8); scope and competing formulations in [Kao (2014)](https://doi.org/10.1016/j.ejor.2014.02.039); dynamic-family reviews in [Mariz, Almeida, and Aloise (2018)](https://doi.org/10.1111/itor.12468) and [Weber (2016)](https://doi.org/10.1093/oxfordhb/9780190226718.013.5). |
| **Evidence status** | `primary-checked` for the four named candidate leaves and `review-supported` for the merge boundary; the generic umbrellas remain `registry-provisional` and non-executable. |
| **Oracle** | `not located`. |
| **Package recipe** | Non-executable discovery families: `network.scale_rts`, `network.productivity`, `dynamic.efficiency`, and `dynamic.productivity`. Candidate leaves for equation/oracle audit are `network.scale_rts.two_stage.chen_zhu_2019`, `network.productivity.two_stage.kao_hwang_2014`, `dynamic.scale_rts.sueyoshi_sekitani_2005`, `dynamic.optimal_control.sengupta_1999`, *dynamic.productivity.malmquist.intertemporal_fare_grosskopf*, and, after equation audit, *dynamic.productivity.malmquist.dynamic_sbm.tone_tsutsui*. Each fixes its technology, measure, information set, reference, aggregation, and decomposition. These names are proposals, not current registry assignments or implementations. |
| **Book location** | **Documentation/source review only.** Source-qualified network/dynamic scale and productivity leaves require their own admission decisions. |

Sueyoshi and Sekitani inherit the Nemoto--Goto economic account in which a
quasi-fixed quantity produced or retained now becomes an input to the next
period. Their contribution is a dynamic RTS classification for that linked
technology. It is therefore an analysis operator on a particular dynamic
technology, not a generic `rts=` option for every carry-over or dynamic
network model. Sengupta instead studies the time path of capital inputs that
minimizes discounted input costs under price change, risk, and adjustment
cost. Its management question is intertemporal capacity choice, not the
reconstruction of a Tone--Tsutsui slack score.

The two proposed dynamic-productivity leaves occupy $G,T,R,A$ and are
Level D relative to repeated-static MPI, window DEA, and a global pooled
reference without a state transition. Every component task must preserve
capital/carry-over state accounting and the source system/period
reconstruction. Sharing static distance code cannot establish that identity.

## 6. Atlas coverage audit: what is present and what is still missing

The current atlas has useful structural umbrellas and several implemented
vertical slices, but an umbrella is not evidence that every historical
method bearing the same family name is covered. The following ledger records
the source-qualified gaps without inflating the public method count.

| Management question | Source-qualified mechanism | Current atlas position | Registration decision |
|---|---|---|---|
| Can connected departments choose one jointly attainable plan? | Färe--Grosskopf two-stage intermediate-products technology with separate process intensities and disposable intermediate coordination | Implemented/public as `network.radial.fare_grosskopf_2000`; broader original-paper constructions remain under the non-executable `network.fare_grosskopf_2000` source grouping | Retain the system-only result contract, input/output orientations inside one family, separate CRS/original and VRS/later provenance, the input-CRS Kao--Hwang score-duality test, and the independent dense output compiler without claiming a published numerical table. |
| Should improvement be propagated through an acyclic organizational sequence? | Lewis--Sexton node DEA followed by hypothetical sub-DMUs and ordered propagation | Public `network.sequential.lewis_sexton_2004.forward_radial` for nonnegative forward quantities | Preserve it as a separate procedure; add reverse quantities, mixed accounts, and site-characteristic adjustments only as source-qualified extensions, never as options on a simultaneous joint-network solver. |
| Can an economy reallocate primary resources and intermediate production across sectors? | Prieto--Zofío input--output network technology | Deferred to the next version; complete primary equations and a numerical oracle were not available | Do not register or implement from secondary descriptions; reopen `source_protocols/prieto_zofio_2007.md` only after the full primary source is obtained. |
| How should serial and parallel missions share one relational performance account? | Kao general series--parallel and parallel relational constructions | Atlas covers the basic two-stage Kao--Hwang leaf, not these constructions | Add candidates `network.relational.general.kao_2009` and `network.relational.parallel.kao_2012`; quarantine the 2012 VRS decomposition until its interpretation and nonnegativity contract are resolved. |
| What did the older independent two-stage studies measure? | Separate stage frontiers or stage-first assessments, including Wang et al. and Seiford--Zhu | No clearly named historical-neighbour record | Register them as diagnostic or legacy neighbours of network DEA, not as exact aliases of a jointly coordinated technology. |
| Who controls the intermediate plan? | Liang--Cook--Zhu centralized and non-cooperative two-stage programmes | `network.governance` is only an umbrella | Add candidate `network.governance.two_stage.liang_cook_zhu_2008`; preserve solution concept, move order, and alternate-optimum policy. |
| Is a common input physically allocated or only valued consistently? | Beasley resource allocation versus Kao parallel common virtual valuation | Shared-resource structures exist, but the semantic boundary is not a source leaf | Reserve a future `ResourcePoolSpec` for physical conservation; add common-valuation behaviour only inside a separately source-qualified relational measure. |
| Does a board need one rating for several periods without a state equation? | Park--Park multi-period aggregative efficiency | Implemented/public with the source four-DMU oracle reproduced | Retain `panel.multiperiod_aggregative.park_park_2009` outside `dynamic.*`; do not expose time preferences or assurance regions as source options. |
| Is management choosing a discounted capital path under price and adjustment risk? | Sengupta optimal-control dynamic efficiency | No source leaf | Add candidate `dynamic.optimal_control.sengupta_1999`; it requires an economic-information contract, not only quantities. |
| What are returns to scale when quasi-fixed inputs connect consecutive periods? | Sueyoshi--Sekitani extension of the Nemoto--Goto technology | the base `dynamic.investment.nemoto_goto` family is `deferred_to_next_version`; no RTS leaf | Retain `dynamic.scale_rts.sueyoshi_sekitani_2005` only as a later candidate after the base source gate closes. |
| Which input, output, and investment slacks explain dynamic underperformance? | Aparicio--Kapelko weighted-additive measure over an adjustment-cost technology | Dynamic investment umbrella exists; measure leaf absent | Add candidate `dynamic.weighted_additive.adjustment_cost.aparicio_kapelko_2019`; retain its unit-dependent inefficiency result. |
| Do current intermediates affect later process output? | Chen lagged-intermediate dynamic network | No source leaf | Add candidate `dynamic.network_lagged_intermediate.chen_2009`; do not implement it as a carry-over-role switch on Network SBM. |
| Are persistent quantities governed by typed adjacent-period accounts? | Tone--Tsutsui dynamic SBM | Implemented public vertical slice with reproduced source values | Retain the source preset and continue to expose generalized carry-over semantics only as separately identified extensions. |
| Must internal links and temporal carry-overs be feasible together? | Tone--Tsutsui dynamic network SBM | Implemented structure with published-equation checks, exact reductions, and a claim-scoped independent joint primal--dual oracle in which both continuity mechanisms bind; the anonymous published application is not reproduced | Retain the public Documentation-only leaf and its explicit terminal-boundary resolution; do not generalize the analytical fixture to other directions, RTS, link/carry-over roles, or a new Handbook chapter. |

### Equivalence ledger

Historical names may be consolidated only at a stated level. A topology
alias, an equality of optimal scores, and equality of the entire feasible
set and result contract are different claims.

| Claim | Classification | Package consequence |
|---|---|---|
| “Two-stage” and “two-node series” | Exact only as a graph description when link direction and variable roles agree | One topology constructor; no automatic method alias. |
| Färe--Grosskopf two-stage input-radial CRS score and Kao--Hwang primary centralized CRS system score | Conditional identity transform under the same external/intermediate/final roles, separate process intensities, disposable-link inequality, CRS, and comparison population | Store a Level-B `exact_score_transform` relation and regression test. Do not import Kao--Hwang stage efficiencies, shared multiplier valuation, product identity, score ranges, or midpoint target into the Färe--Grosskopf result. |
| Kao--Hwang basic CRS model and the matching special case of Kao's general relational construction | Conditional reduction under the same normalization, multiplier restrictions, intermediate treatment, and CRS domain | Store a directed equivalence record with its preconditions; do not generalize it to VRS or arbitrary graphs. |
| Liang--Cook--Zhu centralized, non-cooperative, and separate-stage results with one intermediate | Source-qualified conditional equality of the stage-efficiency outcome; not a universal equality of governance procedures | Test the one-intermediate reduction, while retaining distinct governance IDs and diagnostics. |
| Static Network SBM obtained by collapsing the time dimension of Dynamic Network SBM | Exact reduction only after all temporal accounts, weights, and boundaries disappear and the source network preset is recovered | Use a reduction test, not a public alias. |
| Dynamic SBM obtained by collapsing the process dimension of Dynamic Network SBM | Exact reduction only when the remaining carry-over and weight rules reproduce the source dynamic-SBM preset | Use a reduction test, not a public alias. |
| Färe--Grosskopf disposable intermediate coordination and Tone-style exact handoff | Distinct feasible sets | Reuse link-constraint infrastructure but retain separate balance policies and method leaves. |
| Common process intensity and node-specific intensities | Distinct empirical technologies | Make intensity policy explicit and fingerprint it in every study. |
| Physical allocation of a shared resource and a common virtual multiplier | Distinct economic constraints | Compile the former as resource conservation and the latter as a measure-side valuation restriction. |
| Adjacent-period carry-over equality and a depreciating stock transition | Distinct temporal technologies | Share time indexing only; retain transition equations, controllability, and boundary policies. |
| Multi-period aggregation and dynamic production | Distinct management questions and feasible sets | Place the former in a panel-appraisal namespace and reserve `dynamic.*` for explicit interperiod dependence. |

## 7. Merge boundary

### Safe unification

| Shared mechanism | Safe reuse | Information that must remain visible |
|---|---|---|
| Series, parallel, and general networks | Directed graph compiler | topology, node roles, link directions and balances |
| Shared resources | Resource-pool constraint generator | total commitment, eligibility, control, transfer rules |
| Node technologies | Reusable sparse envelopment blocks | node RTS, disposal, estimator, intensity policy |
| Network measures | System/process result schema | aggregation identity, weights, native score |
| Dynamic carry-overs | Time-expanded graph compiler | effect, control, balance, lag, decay, boundaries |
| Dynamic network | Cartesian block indexing and sparse assembly | within-period links versus temporal links |
| Repeated structured tasks | Fingerprinted task DAG | graph vintage, reference, state and link feasibility |

### Never merge silently

- Independent stage DEA is not network DEA because its intermediate targets
  need not balance.
- Fixed, bounded, and endogenous intermediate products define different
  feasible systems.
- Exact balance, inequality balance, loss, and transformation links are not
  aliases.
- A shared resource pool must not be copied into every process.
- Common and node-specific intensity vectors define different empirical
  technologies.
- Shared-flow, multilevel, and intermediate-product network structures answer
  different organizational questions; a layered drawing is not an
  equivalence proof.
- Beasley shared-input allocation, Cook--Hababou--Tuenter
  component-specific shared-input valuation, and Cook--Green
  overlapping-component selection have different variables and result
  contracts.
- Cook--Chai--Doyle--Green sequential group adjustment and Cook--Green
  simultaneous hierarchy are not aliases.
- A multiplier divisional appraisal is not automatically an
  envelopment-feasible frontier projection.
- Kao--Hwang relational, Chen et al. additive, and Tone--Tsutsui network SBM
  use different system-stage identities.
- Cooperative, centralized, leader--follower, bargaining, and
  non-cooperative governance can choose different plans over the same
  physical graph.
- A time-expanded compiler does not make static network DEA and dynamic DEA
  public aliases.
- Färe--Grosskopf intertemporal production, Nemoto--Goto
  investment/adjustment, and Tone--Tsutsui carry-over SBM are separate
  economic lineages.
- Desirable/undesirable and fixed/free carry-over properties should not be
  collapsed into one internal enum; effect and controllability are
  independent.
- Window DEA and Malmquist compare repeated static technologies. They are not
  dynamic production without an explicit state or transition equation.
- Static network SBM, dynamic SBM, and dynamic network SBM are distinct
  presets.
- Black-box scale and productivity decompositions do not automatically
  survive network links or temporal states.

Some elementary two-stage CRS formulations have exact or score-transform
relationships under restrictive intermediate and coupling assumptions.
Those relations should be stored as directed, source-backed equivalence
records with their domains. They must not be generalized to arbitrary VRS,
shared-resource, environmental, or dynamic networks.

## 8. Package and book consequences

The following is a long-run design sketch, not the current public package
layout or a Milestone-5 delivery commitment:

```text
structure/
    graph.py
    links.py
    resources.py
    network.py
    temporal.py
    carryover.py
measures/network/
    relational.py
    additive.py
    directional.py
    sbm.py
analysis/
    network_scale.py
    network_productivity.py
    dynamic.py
```

Potential future specifications, each subject to its own source and oracle
gate, are:

```text
ProductionGraph(nodes, links, resource_pools, intensity_policy)
LinkSpec(source, target, role, controllability, balance, transform)
ResourcePoolSpec(total, eligible_nodes, control, transfer_policy)
CarryOverSpec(effect, control, balance, lag, decay, initial, terminal)
GovernanceSpec(
    players,
    authority,
    objectives,
    move_order,
    information,
    solution_concept,
)
IntertemporalSpec(information_set, discount_policy, terminal_policy)
```

Every name in the preceding sketch is planned vocabulary unless it is already
documented in the public API. In particular, `GovernanceSpec`,
`ResourcePoolSpec`, and the displayed `ProductionGraph` signature are not
implemented public classes.
Players, authority, and information belong to $C$; objectives, move order,
and solution concept belong to $P$. Physical process topology remains in
$G$. Centralized, cooperative, leader--follower, non-cooperative, and
bargaining accounts are therefore Level D unless a source proves a
conditional identity. Without the $P$-axis solution concept, the eleven-axis
fingerprint cannot distinguish the governance mechanisms. The evidence
anchors are
[Liang, Cook, and Zhu
(2008)](https://doi.org/10.1002/nav.20308) and
[Kao (2014)](https://doi.org/10.1016/j.ejor.2014.02.039).

Every network or dynamic result should retain:

```text
expanded graph and graph version
node technologies and RTS
link/resource/carry-over specifications
common or node-specific intensity policy
system measure and aggregation identity
governance and alternate-optimum policy
system, process, link, period, and state targets
component reconstruction residuals
solver and oracle status
```

The active network and dynamic chapters begin with operational process maps
rather than block matrices. Source-specific graph variants, equivalence
conditions, shared-resource programmes, and block-matrix algebra remain in
package documentation and this review; this ledger does not reserve an
additional handbook chapter or appendix for them.

## 9. Source map

### Internal structure, shared flows, and hierarchies

- Castelli, Pesenti, and Ukovich (2010), classification of shared-flow,
  multilevel, and network DEA,
  [DOI](https://doi.org/10.1007/s10479-008-0414-2).
- Beasley (1995), teaching and research efficiency with shared inputs,
  [DOI](https://doi.org/10.1057/jors.1995.63).
- Cook, Hababou, and Tuenter (2000), multicomponent bank-branch performance
  with shared inputs,
  [DOI](https://doi.org/10.1023/A:1026598803764).
- Cook, Chai, Doyle, and Green (1998), groups and hierarchical DEA,
  [DOI](https://doi.org/10.1023/A:1018625424184).
- Cook and Green (2004), overlapping business components and core-business
  selection across plants,
  [DOI](https://doi.org/10.1016/S0377-2217(03)00298-4).
- Cook and Green (2005), simultaneous plant and generating-unit hierarchy,
  [DOI](https://doi.org/10.1016/j.cor.2003.08.019).
- Chen, Cook, Kao, and Zhu (2013), divisional appraisal and frontier
  projection pitfalls,
  [DOI](https://doi.org/10.1016/j.ejor.2012.11.021).

### Network production and measures

- Färe and Grosskopf (2000), “Network DEA,”
  [DOI](https://doi.org/10.1016/S0038-0121(99)00012-9).
- Podinovski and Bouzdine-Chameeva (2021), multiplier interpretation for
  polyhedral technologies, including a Färe--Grosskopf two-stage example,
  [DOI](https://doi.org/10.1007/s11123-021-00610-3).
- Lewis and Sexton (2004), organizational network efficiency through
  hypothetical sub-DMUs,
  [DOI](https://doi.org/10.1016/S0305-0548(03)00095-9).
- Prieto and Zofío (2007), input--output network efficiency,
  [DOI](https://doi.org/10.1016/j.ejor.2006.01.015).
- Kao and Hwang (2008), relational two-stage efficiency,
  [DOI](https://doi.org/10.1016/j.ejor.2006.11.041).
- Kao (2009), general series--parallel relational decomposition,
  [DOI](https://doi.org/10.1016/j.ejor.2007.10.008).
- Kao (2012), relational efficiency decomposition for parallel systems,
  [DOI](https://doi.org/10.1057/jors.2011.16).
- Peyrache and Silva (2024), directional decomposition and the
  interpretation problem in VRS parallel relational models,
  [DOI](https://doi.org/10.1016/j.omega.2024.103084).
- Chen, Cook, Li, and Zhu (2009), additive two-stage decomposition,
  [DOI](https://doi.org/10.1016/j.ejor.2008.05.011).
- Tone and Tsutsui (2009), network SBM,
  [DOI](https://doi.org/10.1016/j.ejor.2008.05.027).
- Liang, Cook, and Zhu (2008), centralized and non-cooperative governance
  in two-stage DEA,
  [DOI](https://doi.org/10.1002/nav.20308).
- Seiford and Zhu (1999), independent profitability and marketability
  stage assessment,
  [DOI](https://doi.org/10.1287/mnsc.45.9.1270).
- Wang, Gopal, and Zionts (1997), independent two-stage appraisal of
  information-technology impact,
  [DOI](https://doi.org/10.1023/A:1018977111455).
- Cook, Liang, and Zhu (2010), two-stage models and restrictive
  relationships, [DOI](https://doi.org/10.1016/j.omega.2009.12.001).
- Kao (2014), network DEA review,
  [DOI](https://doi.org/10.1016/j.ejor.2014.02.039).
- Cook and Zhu, eds. (2014), network DEA handbook,
  [DOI](https://doi.org/10.1007/978-1-4899-8068-7).

### Intertemporal and dynamic production

- Färe and Grosskopf (1996), *Intertemporal Production Frontiers: With
  Dynamic DEA*, [DOI](https://doi.org/10.1007/978-94-009-1816-0).
- Nemoto and Goto (1999), dynamic DEA with intertemporal behavior and
  quasi-fixed factors,
  [DOI](https://doi.org/10.1016/S0165-1765(99)00070-1).
- Sengupta (1999), discounted-cost and capital-path dynamic efficiency,
  [DOI](https://doi.org/10.1016/S0925-5273(98)00244-8).
- Sueyoshi and Sekitani (2005), returns to scale in the
  quasi-fixed-input dynamic technology,
  [DOI](https://doi.org/10.1016/j.ejor.2003.08.055).
- Park and Park (2009), multi-period aggregative efficiency without a
  transition equation,
  [DOI](https://doi.org/10.1016/j.ejor.2007.11.028).
- Chen (2009), dynamic effects of intermediates in production networks,
  [DOI](https://doi.org/10.1016/j.ejor.2007.12.025).
- Tone and Tsutsui (2010), dynamic SBM with carry-overs,
  [DOI](https://doi.org/10.1016/j.omega.2009.07.003).
- Aparicio and Kapelko (2019), dynamic weighted-additive inefficiency with
  adjustment costs,
  [DOI](https://doi.org/10.1016/j.ejor.2018.08.045).
- Tone and Tsutsui (2014), dynamic network SBM,
  [DOI](https://doi.org/10.1016/j.omega.2013.04.002).
- Mariz, Almeida, and Aloise (2018), dynamic DEA review,
  [DOI](https://doi.org/10.1111/itor.12468).
