# Additive network DEA: a source audit of process performance attribution

## Purpose

“Additive” has two quite different meanings in the DEA literature. In the
ordinary additive DEA model, the objective adds input and output slacks. In
the network papers reviewed here, the system score is instead a weighted
arithmetic account of **radial process efficiencies**. Treating those two
meanings as aliases would change the managerial question, the units of the
objective, and the targets.

This review fixes the executable Chen--Cook--Li--Zhu two-stage account,
separates it from the broader Cook--Zhu--Bi--Yang network construction, and
records the boundary with relational, network-SBM, and composition models.
It complements the family map in
[`NETWORK_DYNAMIC.md`](NETWORK_DYNAMIC.md); it is deliberately more
formulation-specific.

The primary questions are:

- What virtual-resource account is being optimized?
- Which part of that account is technical technology and which part is an
  endogenous valuation?
- Does the model evaluate a closed two-stage organization, an open
  multistage organization, or a general process graph?
- Are process scores decomposed from a system optimum, or is a system score
  composed after process performance has been chosen?
- Which published numbers can reject an incorrect implementation?

## Source and notation audit

Let $o$ be the assessed organization and $j=1,\ldots,n$ index its
comparison organizations. In the elementary closed series system,

$$
x_j \longrightarrow \text{process 1}
\longrightarrow z_j \longrightarrow \text{process 2}
\longrightarrow y_j ,
$$

$x$ contains external resources, $z$ contains observed intermediate
services, and $y$ contains final outcomes. The symbols used throughout
this review are:

| Symbol | Economic role |
|---|---|
| $v\geq0$ | valuation of external resources |
| $w\geq0$ | one shared valuation of the intermediate service in both processes |
| $u\geq0$ | valuation of final outcomes |
| $\xi_1,\xi_2$ | free process intercepts in the source VRS formulation; zero under CRS |
| $I_o=v^\top x_o$ | valued external resources assigned to process 1 |
| $L_o=w^\top z_o$ | valued intermediate resources assigned to process 2 |
| $F_o=u^\top y_o$ | valued final outcomes |

The common intermediate multiplier is not a harmless computational
shortcut. It makes the two process accounts use the same internal transfer
valuation. Dropping that equality returns two independent process
appraisals.

## 1. The elementary Chen--Cook--Li--Zhu account

### 1.1 How should a closed two-process organization attribute performance?

| Evidence field | Record |
|---|---|
| **Economic question** | How should an organization combine premium-acquisition and profit-generation performance, or analogous upstream and downstream processes, when both processes share one internal transfer account? |
| **Technology / estimator** | Closed two-node series graph. Process 1 uses only $x$ and produces only $z$; process 2 uses only $z$ and produces only $y$. Both process multiplier restrictions hold jointly and use the same $w$. |
| **Measure** | Higher-is-better radial process efficiencies combined by an endogenous virtual-resource-share-weighted arithmetic mean. This is not an absolute or normalized slack-sum additive measure. |
| **RTS** | The source defines CRS by zero process intercepts and input-oriented VRS by two free process intercepts. NIRS, NDRS, a single black-box VRS intercept, or ad hoc convexity rows are not source aliases. |
| **Data / time** | Nonnegative cross-sectional external inputs, intermediates, and final outputs. A panel may supply a declared reference population, but the source score remains a static network comparison. |
| **Native score** | $E_o=\alpha_{1o}E_o^{(1)}+\alpha_{2o}E_o^{(2)}$, where larger is better and one denotes source-defined system efficiency when both process normalizers are valid. |
| **Exact aliases** | Algebraically equivalent scaled multiplier programmes using the same graph, shared $w$, process intercepts, endogenous shares, and normalization. `TwoStageAdditiveDecompositionDEA` is an API alias of `ChenCookLiZhuAdditiveDEA`; “additive DEA” alone is not an exact alias. |
| **Distinct variants** | Kao--Hwang multiplicative decomposition; independent process DEA; fixed/equal process-importance weights; open multistage additive DEA; ordinary slack-additive DEA; network SBM; cooperative and leader--follower games; composition-first models. |
| **Domain** | The assessed account needs positive $I_o$ and $L_o$ to report both process ratios. The closed-limit system LP permits zero multipliers and zero shares; an undefined zero-share process ratio must remain missing rather than receive an epsilon denominator. |
| **Failures** | Calling the endogenous shares exogenous managerial importance; injecting a positive numerical epsilon; reporting an arbitrary optimal decomposition as unique; using one common intermediate target when the source projection has separate upstream and downstream plans; interpreting a VRS process intercept as a quantity or a causal process effect. |
| **Solver form** | One sparse LP per assessed organization for the system score, plus source-qualified secondary LPs for process-priority attribution. Free VRS intercepts require split variables or a solver with bounded-free-variable support. |
| **Defining source** | [Chen, Cook, Li, and Zhu (2009)](https://doi.org/10.1016/j.ejor.2008.05.011); projection and primal--dual correction in [Lim and Zhu (2019)](https://doi.org/10.1016/j.omega.2018.06.005). |
| **Evidence status** | `primary-checked`: the defining paper's models (11), (13), (15), and (17)--(19), its data, and its CRS/VRS tables were checked against the open article. |
| **Oracle** | The neutral `two_stage_public_service` case checks CRS/VRS system and process reconstruction and certified split-link projections. Source-table observations, named organizations, and disputed printed cells are not redistributed. |
| **Package recipe** | Implemented as `network.additive.chen_etal_2009` over `NetworkData` and `TwoStageSeriesSpec`, with explicit RTS, reference, decomposition, projection, and minimum-share policies. |
| **Book location** | **Active core placement:** `book/chapters/05-network/network-dea-organizations-links-responsibility.md`; source-exact equations and result contracts remain in package documentation. |

For CRS, the exact linear programme after the source's
Charnes--Cooper transformation is

$$
\begin{aligned}
\max_{v,w,u}\quad
&w^\top z_o+u^\top y_o\\
\text{s.t.}\quad
&w^\top z_j-v^\top x_j\leq0,
&&j=1,\ldots,n,\\
&u^\top y_j-w^\top z_j\leq0,
&&j=1,\ldots,n,\\
&v^\top x_o+w^\top z_o=1,\\
&v,w,u\geq0.
\end{aligned}
\tag{C-CRS}
$$

For the source input-oriented VRS construction, the exact programme is

$$
\begin{aligned}
\max_{v,w,u,\xi_1,\xi_2}\quad
&w^\top z_o+\xi_1+u^\top y_o+\xi_2\\
\text{s.t.}\quad
&w^\top z_j+\xi_1-v^\top x_j\leq0,
&&j=1,\ldots,n,\\
&u^\top y_j+\xi_2-w^\top z_j\leq0,
&&j=1,\ldots,n,\\
&v^\top x_o+w^\top z_o=1,\\
&v,w,u\geq0,\qquad \xi_1,\xi_2\text{ free}.
\end{aligned}
\tag{C-VRS}
$$

On the positive-normalizer domain,

$$
E_o^{(1)}=\frac{L_o+\xi_1}{I_o},\qquad
E_o^{(2)}=\frac{F_o+\xi_2}{L_o},
$$

$$
\alpha_{1o}=\frac{I_o}{I_o+L_o},\qquad
\alpha_{2o}=\frac{L_o}{I_o+L_o},
$$

and therefore

$$
E_o=
\frac{L_o+\xi_1+F_o+\xi_2}{I_o+L_o}
=\alpha_{1o}E_o^{(1)}+\alpha_{2o}E_o^{(2)}.
\tag{C-ID}
$$

This identity is the model's management account. The organization receives a
large process weight when the fitted multiplier account assigns that process
a large share of valued component inputs. The shares are DMU-specific
functions of optimal multipliers. They are neither observed cost shares nor
freely chosen constants.

### 1.2 Who chooses how much each process counts?

| Evidence field | Record |
|---|---|
| **Economic question** | Are process weights empirical virtual-resource shares, externally declared governance priorities, or merely a numerical device preventing a process from disappearing? |
| **Technology / estimator** | The Chen technology is unchanged, but its admissible multiplier set changes when lower bounds are imposed on the two endogenous shares. |
| **Measure** | The same weighted arithmetic identity, evaluated over either the closed-limit valuation domain or a restricted minimum-share domain. |
| **RTS** | The valuation restriction is independent of CRS/VRS, although feasibility and sensitivity can differ by RTS. |
| **Data / time** | Same closed two-stage data. Meaningful external importance weights require an independently justified governance source; they are not learned from the quantity table. |
| **Native score** | System and process scores plus $(\alpha_{1o},\alpha_{2o})$. A restricted score is conditional on the declared minimum share and must not be presented as the unrestricted Chen score. |
| **Exact aliases** | A lower bound of zero is the source closed-limit domain. Positive lower bounds are conditional sensitivity policies, not numerical tolerances. |
| **Distinct variants** | Fixed 50--50 weights; fixed organization-wide importance weights; observed expenditure shares; assurance-region restrictions; Cook et al.'s component-size shares on an open graph; composition-first aggregation. |
| **Domain** | With two stages, a common lower bound $a$ must satisfy $0\leq a\leq0.5$. Even an algebraically admissible $a$ can make a particular DMU programme infeasible. |
| **Failures** | Describing endogenous shares as preference-free facts; silently replacing zero by $10^{-6}$; comparing restricted and unrestricted scores without identifying the valuation change; assuming a large share proves a process is economically important. |
| **Solver form** | Add linear share constraints $I_o\geq a(I_o+L_o)$ and $L_o\geq a(I_o+L_o)$ under the source normalization, then run explicit feasibility and sensitivity diagnostics. |
| **Defining source** | The lower-share proposal and infeasibility examples are in [Chen, Cook, Li, and Zhu (2009)](https://doi.org/10.1016/j.ejor.2008.05.011); subsequent bias and aggregation concerns are developed by [Despotis, Koronakos, and Sotiros (2016)](https://doi.org/10.1007/s11123-014-0415-x). |
| **Evidence status** | `primary-checked` for the source lower-bound policy; later interpretation is `review-supported` and does not change the identity of the canonical leaf. |
| **Oracle** | `reproduced` for the unrestricted leaf. Chen et al. report that selected 40% and 50% share restrictions make some insurer programmes infeasible; those statements are useful future sensitivity oracles but are not score tables. |
| **Package recipe** | Keep `minimum_stage_share=0` as the canonical source default. Any positive setting stays inside `network.additive.chen_etal_2009` as an explicit valuation-policy parameter and disables source projections not proved for that restricted programme. |
| **Book location** | **Active core placement:** `book/chapters/05-network/network-dea-organizations-links-responsibility.md`; source-specific valuation details remain in package documentation. |

The source itself notes that an optimal share can be zero. A package should
therefore distinguish three cases:

1. **identified positive account**: both shares and both denominators are
   positive;
2. **closed-limit system account**: the system score is identified, but a
   zero-share process ratio is not;
3. **policy-restricted account**: a declared positive minimum changes the
   valuation domain and possibly feasibility.

These cases must not be collapsed by a solver tolerance.

## 2. Beyond the elementary closed chain

### 2.1 What changes when resources or services enter and leave midstream?

| Evidence field | Record |
|---|---|
| **Economic question** | How should management aggregate process performance when later processes receive new resources, early processes deliver final services, links branch, or an intermediate skips a process? |
| **Technology / estimator** | Open serial or general acyclic process graph with node-specific external inputs, node-specific final outputs, and explicitly incident intermediate links. Each component has one radial ratio restriction; linked services retain the source-defined common transfer valuation. |
| **Measure** | Overall efficiency is a convex combination of component radial efficiencies. Each component's endogenous weight is its valued component input divided by total valued component inputs across the graph. |
| **RTS** | The defining Cook--Zhu--Bi--Yang programmes are presented under CRS; the paper describes a free-intercept VRS extension. A production-network VRS compiler still needs an equation-level graph audit before public implementation. |
| **Data / time** | Static process-level quantities on open serial, branching, and non-immediate-successor networks. Cycles, inventories, loss transformations, shared resource pools, bad links, and carry-overs are outside the checked source graph. |
| **Native score** | Higher-is-better system radial efficiency and component radial efficiencies, with the weighted component identity and all graph-incidence accounts reconstructing exactly. |
| **Exact aliases** | The elementary Chen CRS programme is a closed two-node specialization when its graph, input/output roles, common intermediate valuation, and endogenous size weights coincide. |
| **Distinct variants** | Tone--Tsutsui network SBM; fixed component weights; dynamic networks; cyclic networks; shared-resource allocation; lossy links; multiplicative relational networks; node-independent DEA. |
| **Domain** | Every quantity has one declared node/link role and unit. Each reported component ratio needs positive valued component input. Lower component-share bounds must sum to at most one and may still be infeasible for a specific DMU. |
| **Failures** | Counting one shared resource as a full input at several nodes; silently treating a link as a final output; allowing different source and destination valuations while claiming a coordinated account; applying the closed two-stage projection to an open graph; assuming the source's examples prove arbitrary cyclic-graph support. |
| **Solver form** | Sparse graph-incidence multiplier LP: one component inequality for every node/reference pair, one shared valuation account per declared link, one total-component-input normalization for the assessed DMU, and optional declared share bounds. |
| **Defining source** | [Cook, Zhu, Bi, and Yang (2010)](https://doi.org/10.1016/j.ejor.2010.05.006). |
| **Evidence status** | `primary-checked` for the CRS open serial, branching, and non-immediate-successor constructions; the generic VRS claim remains `review-supported` pending a compiler-level primal/dual audit. |
| **Oracle** | `open_service_chain` and `three_process_service_chain` check unrestricted, declared-share, and three-process system/component accounts on neutral project cases. Solver-selected component weights are not treated as uniqueness oracles. |
| **Package recipe** | Implemented as `network.additive.cook_zhu_bi_yang_2010` through `CookZhuBiYangAdditiveDEA` over a measure-neutral compiled DAG layout. General-network VRS, cycles, shared pools, transformed links, and source projections fail closed. |
| **Book location** | **Active core placement:** `book/chapters/05-network/network-dea-organizations-links-responsibility.md`; the complete source contract remains in package documentation. |

For a graph with process set $\mathcal P$, let $A_{pj}$ be the valued
component inputs to process $p$ and $B_{pj}$ its valued component
outputs, after external and link incidence has been compiled. The source
account has the generic form

$$
B_{pj}\leq A_{pj},
\qquad p\in\mathcal P,\ j=1,\ldots,n,
$$

$$
\sum_{p\in\mathcal P}A_{po}=1,\qquad
\max\sum_{p\in\mathcal P}B_{po}.
\tag{G-ADD}
$$

Whenever all component denominators are positive,

$$
E_{po}=\frac{B_{po}}{A_{po}},\qquad
\alpha_{po}=A_{po},\qquad
E_o=\sum_{p\in\mathcal P}\alpha_{po}E_{po}.
$$

Equation (G-ADD) is a compiler contract, not permission to infer quantity
roles from column names. A link that is an output of one process and an input
of another must be represented through graph incidence and one declared
transfer valuation.

## 3. Decomposition, composition, and targets are separate decisions

### 3.1 Is performance attributed from the system, or composed from processes?

| Evidence field | Record |
|---|---|
| **Economic question** | Should management optimize the organization first and then attribute its score to processes, or select process performance first and only then construct an organization-level summary? |
| **Technology / estimator** | Decomposition-first Chen/Kao models hold a system optimum fixed before selecting process attribution. Composition-first models use a different multiobjective or process-priority estimator and aggregate afterward. |
| **Measure** | Chen uses an endogenous-share arithmetic system objective; Kao--Hwang uses a multiplicative identity; Despotis--Koronakos--Sotiros propose process-first composition with a posteriori aggregation. |
| **RTS** | Source-specific. The checked Chen leaf supports its CRS and VRS programmes; the 2016 reverse approach is not an RTS-toggle specialization of that leaf. |
| **Data / time** | Elementary closed two-stage quantities in the defining comparisons. More stages, open flows, and leader--follower governance require separate source records. |
| **Native score** | Decomposition-first methods identify the system criterion first; composition-first methods identify a process-performance solution first. Similar numerical process scores do not make the estimands identical. |
| **Exact aliases** | None between decomposition-first and composition-first estimators. Choosing the same arithmetic display formula after fitting does not establish equivalence. |
| **Distinct variants** | Multiplicative decomposition, additive decomposition, process-first composition, weak-link/max--min composition, bargaining/game models, and independent process DEA. |
| **Domain** | The organizational decision rule must be declared. “Cooperative” is too broad to identify whether the system or processes have priority. |
| **Failures** | Presenting a lexicographic attribution as unique without solving both source priorities; treating a criticism of one endogenous weighting rule as proof that all additive network models are invalid; choosing an aggregation after seeing favorable rankings without sensitivity disclosure. |
| **Solver form** | Chen: primary system LP plus two source priority LPs. Composition alternatives: their own multiobjective/envelopment programmes and selection rules; they must not reuse Chen's primary objective under a new label. |
| **Defining source** | Additive decomposition in [Chen et al. (2009)](https://doi.org/10.1016/j.ejor.2008.05.011); reverse composition in [Despotis, Koronakos, and Sotiros (2016)](https://doi.org/10.1007/s11123-014-0415-x); multistage composition in [Despotis, Sotiros, and Koronakos (2016)](https://doi.org/10.1016/j.omega.2015.07.005). |
| **Evidence status** | `primary-checked` for the Chen priority programmes; composition families are `review-supported` here and require a separate equation/oracle audit before registration. |
| **Oracle** | `reproduced` for the Chen decomposition leaf; `candidate` for the published composition comparisons, not yet reproduced by DEAPack. |
| **Package recipe** | Keep the implemented `network.additive.chen_etal_2009` estimator distinct. A future composition estimator must receive its own canonical ID, result semantics, and oracle rather than an `aggregation=` option on the Chen class. |
| **Book location** | **Active core placement:** `book/chapters/05-network/network-dea-organizations-links-responsibility.md`; specialized composition variants remain in package documentation and this source review. |

For Chen's CRS attribution, if $E_o$ is the primary optimum, maximizing
process 1 can be written with $v^\top x_o=1$:

$$
\begin{aligned}
\max\quad&w^\top z_o\\
\text{s.t.}\quad
&w^\top z_j-v^\top x_j\leq0,\\
&u^\top y_j-w^\top z_j\leq0,\\
&(1-E_o)w^\top z_o+u^\top y_o=E_o,\\
&v^\top x_o=1,\qquad v,w,u\geq0.
\end{aligned}
\tag{P1}
$$

The corresponding process-2 priority programme uses
$w^\top z_o=1$ and maximizes $u^\top y_o$, while preserving the same
system optimum through the source's transformed equality. Solving only one
priority does not prove attribution uniqueness. The defining paper compares
both priorities; DEAPack reports the comparison and does not manufacture a
stage range that the source programmes did not identify.

### 3.2 Does a multiplier score automatically identify feasible process targets?

| Evidence field | Record |
|---|---|
| **Economic question** | After an organization receives a system and process account, what linked operating plan can managers actually use as a benchmark? |
| **Technology / estimator** | Lim--Zhu's primal--dual projection for the Chen additive model uses separate upstream intensities $\lambda$ and downstream intensities $\mu$, tied by an additive intermediate-disposition inequality. |
| **Measure** | The multiplier efficiency account remains Chen's; the projection is a source-qualified target selector, not another efficiency measure. |
| **RTS** | CRS uses nonnegative activity intensities. VRS additionally requires $\mathbf1^\top\lambda=\mathbf1^\top\mu=1$. |
| **Data / time** | Same closed nonnegative two-stage data and reference population as the fitted score. |
| **Native score** | Input target $X\lambda$, upstream intermediate plan $Z\lambda$, downstream intermediate plan $Z\mu$, final-output target $Y\mu$, and an audited link-disposition account. |
| **Exact aliases** | A projection obtained from certified primary dual marginals is equivalent to resolving the explicit envelopment LP when both satisfy the same primal/dual certificates. |
| **Distinct variants** | Kao--Hwang's relational projection and midpoint display; ordinary black-box radial projection; independently projected process targets; strong Pareto slack completion. |
| **Domain** | Targets require an optimal score, a compatible reference set, and a certified feasible dual/envelopment solution. A positive minimum-share restriction changes the multiplier problem and has no checked source projection here. |
| **Failures** | Collapsing $Z\lambda$ and $Z\mu$ to an invented common handoff; calling their difference waste without economic qualification; trusting solver marginals without correcting row scaling and checking residuals; claiming generic Pareto efficiency from this radial projection. |
| **Solver form** | Solve or recover the sparse envelopment system $X\lambda\leq E_ox_o$, $Z\lambda-Z\mu\geq(1-E_o)z_o$, $Y\mu\geq y_o$, with VRS convexity rows where applicable. |
| **Defining source** | [Lim and Zhu (2019)](https://doi.org/10.1016/j.omega.2018.06.005); the underlying additive account is [Chen et al. (2009)](https://doi.org/10.1016/j.ejor.2008.05.011). |
| **Evidence status** | `primary-checked`. |
| **Oracle** | The neutral `two_stage_public_service` case checks split-link target feasibility and reconstruction in addition to its system/process account. |
| **Package recipe** | `projection="source"` in `network.additive.chen_etal_2009`; preserve upstream and downstream link targets separately in `targets` and `links`. |
| **Book location** | **Active core placement:** `book/chapters/05-network/network-dea-organizations-links-responsibility.md`; the full projection contract remains in package documentation. |

The source projection is

$$
X\lambda\leq E_ox_o,\qquad
Z\lambda-Z\mu\geq(1-E_o)z_o,\qquad
Y\mu\geq y_o.
\tag{LZ}
$$

The link difference is an accounting adjustment under this model. It is not
automatically physical destruction, and the model does not choose a midpoint
between the two plans.

## 4. Non-equivalence boundary

| Compared methods | What they may share | Why they remain different |
|---|---|---|
| Chen additive and Kao--Hwang relational | Closed two-stage graph, shared intermediate valuation, CRS process restrictions | Arithmetic endogenous-share identity versus multiplicative process identity; different system score, attribution, and projection |
| Chen additive and static `AdditiveDEA` | The word “additive” and LP solvability | Weighted radial process efficiencies versus a declared sum of quantity slacks; different units, graph, and targets |
| Chen additive and Tone--Tsutsui network SBM | Joint process evaluation and a system/process report | Radial virtual-resource account versus non-radial normalized slack fractions and source-defined process/link weights |
| Chen additive and independent process DEA | Familiar process ratios | Shared $w$, one joint feasible multiplier account, and system-first optimization disappear under independent fitting |
| Chen additive and Cook general additive network | Endogenous component-input shares and arithmetic aggregation | The Chen CRS primary programme is an exact closed two-node reduction; the general Cook leaf admits open flows, branching, and non-immediate links but does not inherit Chen VRS, secondary attribution, or projection |
| Chen decomposition and process-first composition | Same elementary data and possible arithmetic display | Different optimization priority and therefore a different estimator/estimand |

The appropriate equivalence classification is:

- **Level A**, exact representation: alternative scaling of (C-CRS) or
  (C-VRS) with the same feasible multipliers and recovery map;
- **Level B**, same graph but different measure/aggregation: Chen versus
  Kao--Hwang, or Chen versus network SBM;
- **Exact conditional reduction**, not a global alias: the Chen CRS primary
  system programme on a matched closed two-node graph reduces to Cook's
  general programme, while their broader public contracts remain different;
- **Level D**, different estimator or managerial decision rule:
  decomposition-first versus composition-first, independent, game, or
  leader--follower models.

## 5. Executable vertical-slice contracts

### 5.1 Closed Chen leaf

The implemented closed two-stage leaf should continue to satisfy all of the
following:

1. Accept exactly two processes and one complete series link; reject external
   process-2 inputs, process-1 final outputs, branches, shared pools, cycles,
   and more than two nodes.
2. Store each observed intermediate once and compile its two process roles
   from graph incidence.
3. Support only source-defined CRS and VRS; fail closed on other RTS.
4. Normalize $I_o+L_o=1$, retain one common $w$, and never add a hidden
   positive multiplier floor.
5. Report the system optimum even when a closed-limit process ratio is
   undefined.
6. Treat `none`, process-1 priority, process-2 priority, and both-priorities
   attribution as explicit evaluation policies.
7. Verify (C-ID) for every successful fit and expose the reconstruction
   residual.
8. Keep process intercepts, endogenous shares, multipliers, virtual
   contributions, and selection policy visible.
9. Recover (LZ) only with a primal/dual certificate; otherwise solve the
   explicit envelopment LP.
10. Keep $Z\lambda$ and $Z\mu$ separate, including their residual and
    economic label.
11. Cache the graph/reference block by stable reference-set ID, then update
    only assessed-DMU normalizations and objectives.
12. Make all unsupported graph or valuation extensions explicit new leaves,
    not permissive options that silently change the source model.

### 5.2 Open-DAG Cook leaf

The implemented general additive leaf must:

1. Compile process, link, and external-variable roles from `NetworkSpec`
   without inferring roles from column order or names.
2. Accept source-compatible acyclic open series, branching, and skip-link
   graphs; reject cycles, disconnected declarations, ambiguous roles, shared
   pools, and transformed links.
3. Store each internal quantity once and apply one multiplier to its
   supplier-output and recipient-input accounts.
4. Support only the equation-complete source CRS programme.
5. Compile one sparse process/reference block per distinct reference set and
   solve one primary LP per assessed observation.
6. Normalize total valued process inputs to one and reconstruct the system
   score from the endogenous process-input shares.
7. Treat positive process-share floors as explicit valuation restrictions,
   never hidden numerical epsilons.
8. Preserve a defined system account when an individual zero-weight process
   ratio is undefined.
9. Label process decompositions as solver-selected unless uniqueness has
   actually been certified.
10. Report multiplier and observed-link accounts, but no targets, peers, or
    generic Pareto-efficiency claim without a source-qualified projection.
11. Reproduce the paper's Tables 2, 3, and 7 and keep alternate-optimal
    component weights out of equality tests.
12. Verify the exact Chen CRS system-score reduction on a matched closed
    two-stage graph without claiming equivalence outside that domain.

That Cook et al. CRS slice is now implemented after independent graph-
incidence, component-share, and project-case reconstruction. The generic
VRS claim is still not promoted: free node intercepts, their incidence in an
arbitrary graph, and their envelopment interpretation need a separate proof
and oracle.

## 6. Oracle plan and known risks

### Project oracle A: closed two-stage public service

`two_stage_public_service` is a neutral service-flow case. It checks CRS/VRS
system and process reconstruction, priority variants, and certified split-link
projections through independent primal/dual accounts. The Chen and Lim--Zhu
papers remain the defining citations, but their observations, named units,
printed cells, and projection tables are not bundled.

### Project oracle B: open service chains

`open_service_chain` and `three_process_service_chain` exercise unrestricted,
declared-share, and three-process graph accounts. A separate project fixture
adds an open branch and non-immediate-successor link and verifies the weighted
identity. Component weights are compared only when the optimum is identified;
alternate optimal multiplier accounts with the same system score are not
treated as unique.

### Exact analytic fixture

A small CRS regression can be checked without another implementation. Let
the reference set contain

$$
A:(x,z,y)=(1,1,1),\qquad
B:(x,z,y)=(2,1,0.5).
$$

For assessed unit $B$, (C-CRS) reduces to

$$
\max\; w+0.5u
\quad\text{s.t.}\quad
w\leq v,\quad u\leq w,\quad 2v+w=1.
$$

The optimum is $v=w=u=1/3$. Hence

$$
E_B=0.5,\quad
E_B^{(1)}=0.5,\quad
E_B^{(2)}=0.5,\quad
(\alpha_{1B},\alpha_{2B})=(2/3,1/3).
$$

This fixture detects a wrong normalization, a missing process constraint, or
a broken reconstruction identity. It does not replace the published
multi-input/multi-output oracle.

### Risks that must remain visible

- **Printed-table risk:** three-decimal source tables can hide alternate
  optima and cannot certify uniqueness by themselves.
- **Share-collapse risk:** a zero endogenous share can identify the system
  score while leaving a process ratio undefined.
- **priority risk:** one secondary optimum is a selection, not proof of a
  complete attribution range.
- **VRS risk:** process intercepts can change process scores in ways that do
  not obey a naive “VRS score must rise stage by stage” expectation.
- **projection risk:** multiplier efficiency and envelopment targets are not
  interchangeable without the source primal--dual construction.
- **graph risk:** the Cook general-network algebra does not automatically
  cover cycles, inventories, shared pools, transformations, bad links, or
  dynamic carry-overs.
- **valuation risk:** component shares are fitted virtual-resource shares,
  not observed expenditure shares or causal importance.
- **scale risk:** independent variable scaling should leave scores invariant,
  but a unit-dependent epsilon or incorrectly scaled free intercept can break
  that property.

## Source register

- [Chen, Cook, Li, and Zhu (2009), additive efficiency decomposition in
  two-stage DEA](https://doi.org/10.1016/j.ejor.2008.05.011).
- [Cook, Zhu, Bi, and Yang (2010), additive efficiency decomposition for open
  multistage and network structures](https://doi.org/10.1016/j.ejor.2010.05.006).
- [Lim and Zhu (2019), primal--dual correspondence and frontier
  projections](https://doi.org/10.1016/j.omega.2018.06.005).
- [Despotis, Koronakos, and Sotiros (2016), composition versus
  decomposition](https://doi.org/10.1007/s11123-014-0415-x).
- [Despotis, Sotiros, and Koronakos (2016), series multistage
  composition](https://doi.org/10.1016/j.omega.2015.07.005).
- [Kao (2014), network DEA review](https://doi.org/10.1016/j.ejor.2014.02.039).
