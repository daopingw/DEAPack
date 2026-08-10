# Network SBM: process performance under linked production

## Purpose and source boundary

This review fixes the source meaning of the network slacks-based measure
(NSBM) introduced by Tone and Tsutsui. It answers a management question:
which divisions account for unused resources or missing services when their
plans must agree on the intermediate products passed between them?

The defining evidence is the published article and the authors' openly
available 36-page discussion paper. The latter contains the complete
programmes, proofs, data, and numerical tables. The review deliberately
separates the source model from later models that also use the label
“network SBM.” In particular, the base model does **not** put link deviations
in its objective, and the source's “free” and “discretionary” link are two
names for the same case. The same complete source separately defines
recipient-accountable incoming links in equation (26) and
supplier-accountable outgoing links in equation (27). Those oriented
specializations are not retrofitted into the fixed/free base objective.

For division $k=1,\ldots,K$, let $X^k,Y^k$ contain its external inputs and
outputs, and let $Z^{(k,h)}$ contain the observed products passed from
division $k$ to division $h$. Each division has its own intensity vector
$\lambda^k$. External-input and external-output slacks are
$s_o^{k-}$ and $s_o^{k+}$. Division-importance weights are denoted by
$w^k$, with $\sum_k w^k=1$.

The public implementation is `ToneTsutsuiNetworkSBM`.
`NetworkSBM` is an exact API alias for that class, not a second method or a
second registry entry.

## Evidence cards

### 1. Which connected operating plans are jointly attainable?

The source starts with separate empirical technologies for the divisions and
then makes them one organization by requiring agreement on every internal
handoff. It is therefore neither black-box DEA nor independent DEA by
department.

For the evaluated organization $o$, the external accounts are

$$
x_o^k=X^k\lambda^k+s_o^{k-},\qquad
y_o^k=Y^k\lambda^k-s_o^{k+}.
$$

Under VRS, $\mathbf 1^\top\lambda^k=1$ for every division; omitting these
equalities gives the source CRS variant. The link equations in the next card
complete the joint technology.

| Evidence field | Record |
|---|---|
| **Economic question** | Which combinations of divisional resource use, services, and internal handoffs can the organization attain as one coordinated production system? |
| **Technology / estimator** | Full-sample DEA envelopment with a division-specific intensity vector $\lambda^k$, external input/output balances for every division, and one continuity account for every directed link. |
| **Measure** | No score at the technology level; the source composes input-, output-, or non-oriented weighted SBM objectives with this technology. |
| **RTS** | Common source switch: VRS imposes $\mathbf1^\top\lambda^k=1$ separately for every division; CRS omits all such equalities. This is not an independently identified “system RTS.” |
| **Data / time** | Cross-sectional comparable DMUs; division-specific external inputs and outputs; observed intermediate products stored once per directed link. Every process needs a nonempty external-input block when inputs are scored, a nonempty external-output block when outputs are scored, and both blocks in the non-oriented model. |
| **Native score** | Supplied by the selected orientation; all system and division scores are higher-is-better with one denoting efficiency on the positive source domain. |
| **Exact aliases** | Envelopment programmes obtained by algebraically rearranging the same balances are exact representations. “NSBM,” “network SBM,” and “weighted network SBM” identify this source family only when graph, link policy, objective, RTS, and division weights also agree. |
| **Distinct variants** | Black-box SBM, independently estimated divisional SBM, common-intensity network DEA, relational DEA, additive network DEA, dynamic SBM, and dynamic network SBM. |
| **Domain** | All non-vacant observed variables used as SBM normalizers are strictly positive in the canonical source preset; every link has declared source and recipient divisions; DMUs share the same graph and variable roles. |
| **Failures** | Duplicating a link as unrelated upstream output and downstream input permits inconsistent targets. Treating missing division data as zero changes the technology. Calling separate departmental frontiers a network does not enforce organizational feasibility. |
| **Solver form** | Sparse block LP for the oriented models; sparse linear-fractional programme and source-compatible Charnes--Cooper transformation for the non-oriented model. |
| **Defining source** | [Tone and Tsutsui (2009)](https://doi.org/10.1016/j.ejor.2008.05.027), with complete working-paper formulation in [Tone and Tsutsui (2007)](https://doi.org/10.24545/00000978). |
| **Evidence status** | `primary-checked`. |
| **Oracle** | `analytically derived` for the source equation-(26) accountable-input and equation-(27) accountable-output optima, with exact rational system, process, slack, target, and continuity accounts. `three_process_service_chain`, `crs_free_link_service_chain`, and the all-orientation hand cases provide additional bounded property checks. |
| **Package recipe** | `graph.general_network` + `network.sbm.tone_tsutsui_2009` + orientation + RTS + link-control policy + exogenous division weights. |
| **Book location** | **Active core placement:** `book/chapters/05-network/20-network-sbm.md`; complete block programmes remain in package documentation. |

### 2. Is an internal handoff inherited, redesignable, or assigned to one process?

The public 2009-compatible slice exposes all four source link cases. In the
fixed case, both adjacent division plans must reproduce the observed handoff:

$$
Z^{(k,h)}\lambda^k=z_o^{(k,h)}
=Z^{(k,h)}\lambda^h.
$$

In the free case, the common handoff is endogenous:

$$
Z^{(k,h)}\lambda^k=Z^{(k,h)}\lambda^h.
$$

Thus “free” means discretionary in this paper: it may rise or fall from the
observed amount but must still be supplied and used consistently. It does not
mean that continuity is removed.

The open source formulation also records as-input and as-output cases. They
add one divisional performance account without disconnecting the two
plans. For an as-input link, the recipient $h$ carries the input-style
balance,

$$
Z^{(k,h)}\lambda^h+s_o^{(k,h)-}=z_o^{(k,h)},
\qquad
Z^{(k,h)}\lambda^k=Z^{(k,h)}\lambda^h.
$$

For an as-output link, the supplier $k$ carries the output-style balance,

$$
Z^{(k,h)}\lambda^k-s_o^{(k,h)+}=z_o^{(k,h)},
\qquad
Z^{(k,h)}\lambda^k=Z^{(k,h)}\lambda^h.
$$

Score attribution is therefore unilateral, but organizational feasibility is
bilateral in all four cases.

| Evidence field | Record |
|---|---|
| **Economic question** | Should the benchmark hold the observed handoff fixed, redesign it jointly, or place its scored excess/shortfall in the recipient/supplier performance account while both plans remain coordinated? |
| **Technology / estimator** | `fixed`: both reference plans equal the observed link. `free`: both plans equal one endogenous target. `as_input`: recipient input-style slack balance plus supplier--recipient continuity. `as_output`: supplier output-style slack balance plus the same continuity. |
| **Measure** | Fixed/free alter feasibility without directly scoring link deviation in the base objective. As-input/as-output provide the additional process performance accounts used by the source's oriented link-scoring extensions. |
| **RTS** | Fixed, free, and the two oriented accountable-link cases retain the selected source CRS or process-specific VRS constraints. |
| **Data / time** | All cases require the observed link matrix across peers. Fixed and accountable-link cases additionally use the evaluated DMU's observed link in endpoint or slack balances. |
| **Native score** | With identical orientation, weights, RTS, and sample, the fixed-link score is at least the free-link score because the fixed feasible set is tighter and lower scores denote more measured inefficiency. |
| **Exact aliases** | In this source, “fixed link” = “non-discretionary link,” and “free link” = “discretionary link.” These are naming aliases within their respective equations, not aliases of each other. |
| **Distinct variants** | Bounded links, lossy/transformed links, good/bad/free/fixed temporal carry-overs, dual-role link accounts, and unlinked intermediate models. |
| **Domain** | Every link quantity has the same physical unit at both ends and exactly one observed organizational account. Endogenous targets or slacks never remove equality between supplying and receiving reference plans. |
| **Failures** | Calling a free link “unconstrained”; treating as-input as a recipient-only technology or as-output as a supplier-only technology; calling a fixed link merely “observed” while allowing its target to change; or merging the four temporal carry-over effects with these within-period score-attribution roles. |
| **Solver form** | Fixed links add two observed-value equality blocks; free links add one cross-division equality block; as-input/as-output each add their accountable endpoint balance and the cross-division continuity block. |
| **Defining source** | Tone and Tsutsui's equations (5a)--(5d) in the [open discussion paper](https://doi.org/10.24545/00000978), the published [2009 article](https://doi.org/10.1016/j.ejor.2008.05.027), and the formal four-case continuity statement in the later [dynamic-network article](https://doi.org/10.1016/j.omega.2013.04.002). |
| **Evidence status** | `primary-checked`. |
| **Oracle** | `analytically derived` for equations (26)--(27): independent exact project fixtures certify owner, slack, target, dimension count, continuity, and system/process optima. The neutral VRS fixed/free service-chain comparisons remain additional property checks. |
| **Package recipe** | `link_control="fixed"|"free"` preserves the uniform compatibility path. `link_kinds={link_id: kind}` classifies every link explicitly as `fixed`, `free`, `as_input`, or `as_output`; accountable kinds retain both endpoint continuity and named single-process score ownership. |
| **Book location** | **Active core placement:** `book/chapters/05-network/20-network-sbm.md`. |

### 3. Which divisional resource excesses should be removed?

The input-oriented source model minimizes

$$
\theta_o^*=\min\sum_{k=1}^K w^k
\left(1-\frac{1}{m_k}\sum_{i=1}^{m_k}
\frac{s_{io}^{k-}}{x_{io}^k}\right).
$$

The term in parentheses is division $k$'s input-oriented efficiency
$\theta_o^k$, so the system score is its weighted arithmetic mean.

| Evidence field | Record |
|---|---|
| **Economic question** | How much observed external resource use could each division avoid while maintaining its services and all required internal handoffs? |
| **Technology / estimator** | Joint source network technology with either fixed or free links and the selected CRS/VRS constraints. |
| **Measure** | Weighted input-oriented SBM over external-input slacks only. Link-flow slacks are absent from the base objective. |
| **RTS** | Source CRS and VRS variants are both defined; the selected RTS applies to every divisional intensity block. |
| **Data / time** | Positive evaluated external inputs provide the slack normalizers; output and link data constrain the benchmark plan. |
| **Native score** | Division: $\theta_o^k=1-m_k^{-1}\sum_i s_{io}^{k-}/x_{io}^k$. System: $\theta_o^*=\sum_k w^k\theta_o^k$. Both lie in $[0,1]$ on the canonical domain and larger is better. |
| **Exact aliases** | The weighted arithmetic reconstruction is an identity for this input orientation. It is not the non-oriented or output-oriented aggregation identity. |
| **Distinct variants** | Radial input contraction, unweighted slack sums, input-oriented models that score incoming link excess, and closest-target selection. |
| **Domain** | $x_{io}^k>0$ for every scored external input; admissible division weights; self-inclusive reference; feasible link equations. |
| **Failures** | Reading $1-$average proportional slack as a radial contraction; including link deviations without changing the method ID; comparing division scores without noting different numbers and types of variables. |
| **Solver form** | LP; no fractional transformation is needed. |
| **Defining source** | Tone and Tsutsui's equations (7)--(9) in the [open source manuscript](https://doi.org/10.24545/00000978), published as [Tone and Tsutsui (2009)](https://doi.org/10.1016/j.ejor.2008.05.027). |
| **Evidence status** | `primary-checked`. |
| **Oracle** | `analytically derived` for the equation-(26) accountable-input specialization. The broader VRS/fixed, VRS/free, and CRS/free input cases are bounded reconstruction and feasibility checks rather than a published-table reproduction or a claim of unique optima. |
| **Package recipe** | `network.sbm.tone_tsutsui_2009` with `orientation="input"` and declared weights, RTS, and link policy. `as_input` activates the separately discoverable `accountable_input_link` specialization and revises the recipient's dimension count exactly as in equation (26). |
| **Book location** | **Active core placement:** `book/chapters/05-network/20-network-sbm.md`; orientation-specific formulae remain in package documentation. |

### 4. Which divisional service shortfalls should be closed?

The output-oriented model first maximizes the weighted proportional
expansion account,

$$
\frac{1}{\tau_o^*}=\max\sum_{k=1}^K w^k
\left(1+\frac{1}{r_k}\sum_{r=1}^{r_k}
\frac{s_{ro}^{k+}}{y_{ro}^k}\right).
$$

The reported system efficiency is its reciprocal.

| Evidence field | Record |
|---|---|
| **Economic question** | How much additional external service could the divisions deliver with the organization's observed resources and consistent internal handoffs? |
| **Technology / estimator** | The same source joint network technology, with output slacks optimized and either fixed or free links. |
| **Measure** | Weighted output-oriented SBM; the system efficiency is the reciprocal of the weighted output-expansion terms. |
| **RTS** | Source CRS and VRS variants. |
| **Data / time** | Positive evaluated external outputs provide normalizers; inputs and internal links constrain expansion. |
| **Native score** | Division $\tau_o^k=[1+r_k^{-1}\sum_r s_{ro}^{k+}/y_{ro}^k]^{-1}$. System $1/\tau_o^*=\sum_k w^k/\tau_o^k$: a weighted harmonic mean of division efficiencies, in $(0,1]$ on the positive domain. |
| **Exact aliases** | Reciprocal LP objectives that report $\tau_o^*$, rather than its expansion factor, are exact score transforms when metadata retain both directions. |
| **Distinct variants** | Radial output expansion, output-oriented models that score outgoing-link shortfalls, and the input/non-oriented NSBM objectives. |
| **Domain** | $y_{ro}^k>0$ for every scored external output; valid weights, link equations, and reference membership. |
| **Failures** | Reporting the maximized expansion account as higher-is-better efficiency; reconstructing the system score by an arithmetic mean; silently treating internal links as final services. |
| **Solver form** | LP for the expansion account followed by a deterministic reciprocal transformation. |
| **Defining source** | Tone and Tsutsui's equations (10)--(12) in the [open source manuscript](https://doi.org/10.24545/00000978) and [published article](https://doi.org/10.1016/j.ejor.2008.05.027). |
| **Evidence status** | `primary-checked`. |
| **Oracle** | `analytically derived` for the equation-(27) accountable-output specialization, including the exact reciprocal system account, process efficiencies, link slack, and common target. The general output-orientation hand case is an additional property check; no published numerical table is used. |
| **Package recipe** | `network.sbm.tone_tsutsui_2009` with `orientation="output"` and explicit score/expansion-factor labels. `as_output` activates the separately discoverable `accountable_output_link` specialization and revises the supplier's dimension count exactly as in equation (27). |
| **Book location** | **Active core placement:** `book/chapters/05-network/20-network-sbm.md`; orientation-specific formulae remain in package documentation. |

### 5. How should resource excesses and service shortfalls be judged together?

The non-oriented NSBM is

$$
\rho_o^*=\min
\frac{\sum_k w^k\left(1-\frac{1}{m_k}
\sum_i s_{io}^{k-}/x_{io}^k\right)}
{\sum_k w^k\left(1+\frac{1}{r_k}
\sum_r s_{ro}^{k+}/y_{ro}^k\right)}.
$$

It combines division accounts through a ratio of weighted sums. It is not
the arithmetic mean of division SBM ratios.

| Evidence field | Record |
|---|---|
| **Economic question** | What is the organization's joint shortfall when every division may both conserve external resources and improve external services? |
| **Technology / estimator** | Source network envelopment with external input/output slacks, selected link control, and division-specific intensities. |
| **Measure** | Non-oriented weighted network SBM: ratio of the weighted input-conservation terms to the weighted output-expansion terms. |
| **RTS** | Source VRS or CRS applied consistently to all divisional intensity vectors. |
| **Data / time** | Positive external input and output normalizers; positive source-domain link data; one cross-section. |
| **Native score** | System $\rho_o^*\in[0,1]$, higher is better, one is efficient. Division $\rho_o^k$ is its own input term divided by its output term. The system score is a denominator-adjusted weighted mean, neither the source arithmetic nor harmonic mean. |
| **Exact aliases** | Its Charnes--Cooper LP is an exact computational representation on the valid positive-denominator domain. |
| **Distinct variants** | Black-box Tone SBM, an arithmetic mean of separately computed division SBMs, Kao's later slack-based decomposition, directional network measures, and link-scoring extensions. |
| **Domain** | Strictly positive external normalizers, admissible weights, feasible network, and a positive fractional denominator. |
| **Failures** | Averaging division ratios using the original $w^k$; forgetting the transformed normalization; claiming a multiplicative system-stage identity; merging it with static SBM because the objective has a similar fraction. |
| **Solver form** | Linear-fractional programme transformed by a single source-compatible Charnes--Cooper scale; sparse block LP after transformation. |
| **Defining source** | Tone and Tsutsui's equations (13)--(14) in the [open source manuscript](https://doi.org/10.24545/00000978), corresponding to [Tone and Tsutsui (2009)](https://doi.org/10.1016/j.ejor.2008.05.027). |
| **Evidence status** | `primary-checked`. |
| **Oracle** | `reproduced by exact hand oracle`: an exactly solvable two-stage case verifies the fractional score, Charnes--Cooper scale, and denominator-adjusted reconstruction. The published empirical tables are input-oriented and are not claimed as non-oriented evidence. |
| **Package recipe** | Default orientation of `network.sbm.tone_tsutsui_2009`; retain numerator, denominator, transformed scale, and reconstruction residual. |
| **Book location** | **Active core placement:** `book/chapters/05-network/20-network-sbm.md`; the transformation proof remains in package documentation and this source review. |

### 6. Who determines the importance of each division?

The $w^k$ are not DEA multipliers and are not link weights. They are
exogenous statements of divisional importance. Tone and Tsutsui suggest cost
shares as one possible basis and use $0.4,0.2,0.4$ only for illustration.

| Evidence field | Record |
|---|---|
| **Economic question** | How should top management translate different divisional responsibilities into one organizational performance account? |
| **Technology / estimator** | The frontier and link balances are unchanged; a valuation policy supplies $w^k\ge0$, $\sum_k w^k=1$. |
| **Measure** | Orientation-specific weighted SBM aggregation; the weights apply to whole division accounts, not individual links. |
| **RTS** | Independent of the CRS/VRS choice, although the resulting optimal slacks and scores depend on RTS. |
| **Data / time** | Weights may be policy shares or externally observed cost shares; their source, period, and normalization must be retained. |
| **Native score** | The score remains in the source interval. The strong statement “overall efficient iff every division is efficient” requires every accountable division to receive strictly positive weight. |
| **Exact aliases** | Equal division weights are a parameter specialization. Dimension weights inside a division and cost-share division weights are not aliases merely because both sum to one. |
| **Distinct variants** | Endogenous/benevolent weights, assurance regions, link-specific weights, size weights, common-weight cross-efficiency, and bargaining/governance objectives. |
| **Domain** | Nonnegative weights summing to one; strictly positive weights for all-division efficiency identification; economically documented rather than tuned for rankings. |
| **Failures** | Describing $w^k$ as technical facts, optimizing them without changing the method, confusing them with SBM's equal averaging across variables, or interpreting a zero-weight division as certified efficient. |
| **Solver form** | Fixed coefficients in the LP or fractional objective; sensitivity runs over declared weight scenarios require separate fits. |
| **Defining source** | The weight definition and cost-share example appear in [Tone and Tsutsui (2007)](https://doi.org/10.24545/00000978), based on weighted SBM and published in [Tone and Tsutsui (2009)](https://doi.org/10.1016/j.ejor.2008.05.027). |
| **Evidence status** | `primary-checked`. |
| **Oracle** | `candidate` for arbitrary declared-weight sensitivity: project scenarios require the fitted division-weight account to reconstruct every reported system score, but the analytical certificate is limited to the equation-(26)/(27) fixtures and does not certify all weight choices. No source-table weight vector is bundled. |
| **Package recipe** | Declared division-importance valuation inside `network.sbm.tone_tsutsui_2009`; weights are mandatory fitted-result metadata. |
| **Book location** | **Active core placement:** `book/chapters/05-network/20-network-sbm.md`. |

### 7. What do the CRS and VRS variants actually guarantee?

The source proves more limited divisional-frontier results than a generic
“network DEA behaves like ordinary DEA” claim. Under VRS, every division has
at least one divisionally efficient observed DMU. Under CRS this also holds
for fixed links. Under CRS with free links it can fail: the authors construct
a case where no observed DMU is efficient in one division.

| Evidence field | Record |
|---|---|
| **Economic question** | Does every division have an observed exemplar, and what does its absence say about organizational design rather than one manager's performance? |
| **Technology / estimator** | Source VRS or CRS process technologies crossed with fixed or free link control. |
| **Measure** | The existence theorem applies to the source input-, output-, and non-oriented divisional efficiencies; it is a frontier property, not a new score. |
| **RTS** | VRS: divisional exemplar exists for either link case. CRS + fixed: exemplar exists and reference DMUs are divisionally efficient. CRS + free: an entire division may have no efficient observed DMU. |
| **Data / time** | Same positive cross-sectional network data; no temporal interpretation. |
| **Native score** | Division and system scores retain their orientation-specific ranges. Lack of a division score equal to one under CRS/free is permitted, not a numerical solver failure. |
| **Exact aliases** | Omitting every $\mathbf1^\top\lambda^k=1$ equality is the source CRS specialization; retaining one system-level convexity equality is not equivalent. |
| **Distinct variants** | Node-specific mixed RTS, system RTS decomposition, scale efficiency, nonconvex FDH networks, and dynamic returns-to-scale models. |
| **Domain** | The source's connected graph and feasible fixed/free link equations; theorem-specific RTS conditions. |
| **Failures** | Promising an observed efficient peer in every CRS/free division, interpreting absence as infeasibility, or inferring a system scale property from division-level convexity equations. |
| **Solver form** | Same LP/fractional family; diagnostics count efficient observed DMUs per division after solving the complete sample. |
| **Defining source** | Theorems 2--3, Corollary 1, and the CRS/free counterexample in [Tone and Tsutsui (2007)](https://doi.org/10.24545/00000978); published source [Tone and Tsutsui (2009)](https://doi.org/10.1016/j.ejor.2008.05.027). |
| **Evidence status** | `primary-checked`. |
| **Oracle** | `candidate` for this CRS/free theorem-level claim. `crs_free_link_service_chain` supplies a bounded project regression for the system and division account, while the record's analytical certificate is limited to equations (26)--(27) and is not inherited by this branch. |
| **Package recipe** | One source preset with explicit `returns_to_scale` and `link_control`; property tests are conditional on their combination. |
| **Book location** | **Active core placement:** `book/chapters/05-network/20-network-sbm.md`. |

### 8. Which benchmark plan should managers receive?

For any optimal solution, external targets are
$x_o^{k*}=x_o^k-s_o^{k-*}$ and
$y_o^{k*}=y_o^k+s_o^{k+*}$. Fixed links remain observed. A free link's
target is $Z^{(k,h)}\lambda^{k*}=Z^{(k,h)}\lambda^{h*}$. The source proves
the complete projected organization is overall efficient. It also explicitly
warns that divisional scores need not be unique.

| Evidence field | Record |
|---|---|
| **Economic question** | Which coordinated operating plan should be reported as the organization's improvement target, and how stable is its performance attribution across divisions? |
| **Technology / estimator** | Targets use the same division intensities and link equations that produced the score; reference sets are division-specific positive-intensity peers. |
| **Measure** | Orientation-specific source slacks and link target; the projection theorem establishes overall efficiency of a selected optimum. |
| **RTS** | Projection result is stated for source oriented and non-oriented models; reference-set properties remain conditional on RTS/link case as in the previous card. |
| **Data / time** | One projected vector for each external variable and one organizational target for every free link; fixed links reproduce observations. |
| **Native score** | The optimum system score can be unique while division scores, slacks, intensities, references, and link targets are not. A solver-selected attribution is therefore not automatically identified. |
| **Exact aliases** | Alternative optimal bases producing the same complete target are computational aliases; different optimal targets are admissible alternatives, not identical estimates. |
| **Distinct variants** | Closest targets, lexicographic slack completion, min/max division attribution, peer sparsity, and bargaining-based target selection. |
| **Domain** | Finite optimum, valid fractional normalization where applicable, and exact satisfaction of the selected fixed/free link equations. |
| **Failures** | Returning independently projected division targets, suppressing alternate optima, labeling one division responsible solely because the solver selected one basis, or reporting a free-link target that upstream and downstream plans do not share. |
| **Solver form** | Primary LP plus optional secondary LPs at the fixed system optimum for target, score, and attribution ranges. |
| **Defining source** | Projection equations (15)--(16), reference equation (17), Theorem 4, and the nonuniqueness warning in [Tone and Tsutsui (2007)](https://doi.org/10.24545/00000978); later two-stage projection analysis in [Chen et al. (2016)](https://doi.org/10.1016/j.ejor.2015.09.031). |
| **Evidence status** | `primary-checked` for source targets and nonuniqueness; secondary selection policies are `review-supported`. |
| **Oracle** | `candidate` for a general target-selection oracle. Project-case tests require returned input/output targets and free-link plans to be jointly feasible without fixing one optimal basis; exact analytical target claims remain limited to the accountable-link equation-(26)/(27) fixtures. |
| **Package recipe** | Result contract must include external targets, one link target, division intensities/references, reconstruction residuals, and explicit alternate-optimum policy. |
| **Book location** | **Active core placement:** `book/chapters/05-network/20-network-sbm.md`. |

### 9. Should deviations in the links themselves count as inefficiency?

In the base fixed/free models, link flows do not appear in the objective.
The open source later supplies the oriented objectives for the accountable
link cases introduced in Eqs. (5c)--(5d): an incoming-link excess can enter
the recipient division's input account, or an outgoing-link shortfall can
enter the supplier division's output account. These extensions change the
normalization and score; they are not hidden options of the base programme.
Neither extension removes supplier--recipient continuity. The paper also
studies common intensities and a connectivity restriction between divisional
intensity vectors.

| Evidence field | Record |
|---|---|
| **Economic question** | Is a changed handoff merely a coordinated means to improve final operations, or itself a resource excess/service shortfall for which a division is accountable? |
| **Technology / estimator** | Base model: fixed/free link technology. Source accountable-link extension: retain source--recipient equality, add a slack balance on the declared receiving-input or supplying-output side, and include that slack in the owner's oriented average. Separate extension: common or bounded-difference intensity vectors. |
| **Measure** | Base NSBM scores only external-variable slacks. Equations (26)--(27) define distinct input- and output-oriented link-scoring measures. No corresponding canonical non-oriented link-scoring formula is supplied there. |
| **RTS** | Extension must separately retain source CRS/VRS constraints; common intensities can collapse the process-specific benchmark structure toward an aggregated DEA with link equalities. |
| **Data / time** | Link-scoring requires a defensible economic role and positive link normalizer; connectivity restrictions require an interpretable cross-division benchmark-coupling policy. |
| **Native score** | Source-oriented extension remains higher-is-better and bounded on its valid domain, but its score is not the base fixed/free NSBM score. |
| **Exact aliases** | “Free link” and “link slack scored as input/output” are not aliases. Equal division intensities are only the zero-connectivity specialization of the paper's intensity-coupling extension. |
| **Distinct variants** | Dual-role link models, loss/transformation links, undesirable intermediates, common-intensity black-box-like models, and later generalized network SBM formulations. |
| **Domain** | Each scored link has one declared economic side; no double counting as both input excess and output shortfall unless a new source-qualified measure establishes that account. |
| **Failures** | Claiming the base NSBM measures link inefficiency directly, dropping continuity when adding an accountable link slack, adding link slacks to both sides opportunistically, or presenting common intensities as a harmless performance optimization. |
| **Solver form** | Oriented LP with revised dimension counts and objective coefficients; common/bounded intensity coupling adds sparse cross-division rows. |
| **Defining source** | Sections 6.1--6.2 and equations (26)--(32) of [Tone and Tsutsui (2007)](https://doi.org/10.24545/00000978); later link-inefficiency critique in [Shamsijamkhaneh (2018)](https://doi.org/10.1155/2018/9470236). |
| **Evidence status** | `primary-checked` for the source extensions; later generalized formulations are `review-supported`. |
| **Oracle** | Claim-scoped `analytical_certificate` for equations (26)--(27) on a record whose fixed/free base status remains `reproduced`: independent exact fixtures prove matching objective bounds and score A at $5/8$ under input/as-input, with recipient link-input slack 1 and target 1, and at $4/7$ under output/as-output, with supplier link-output slack 1 and target 2. These claims are explicitly **not** published reproductions. A dedicated source numerical table for equations (26)--(32) is `not located`, so the base utility tables are not borrowed. Unit invariance, single-count ownership, bilateral continuity, invalid combinations, and sparse solve accounting are executable checks. |
| **Package recipe** | `network.sbm.tone_tsutsui_2009.accountable_input_link` and `.accountable_output_link` are public discovery specializations of the same sparse compiler and class. Common-intensity and bounded-connectivity equations (28)--(32) remain outside the public API because this milestone does not supply their independent executable validation. |
| **Book location** | **Documentation/source review only.** Link-slack descendants have no independent placement in the current handbook. |

### 10. Which public tables certify this implementation, and which descendants remain separate?

The authors' open manuscript supplies two unusually useful validation cases,
and both source datasets have now been transcribed and solved. The first has
ten 1994 U.S. vertically integrated electric utilities with generation,
transmission, and distribution divisions, two links, weights
$(0.4,0.2,0.4)$, and VRS input-oriented results for fixed and free links.
Tables 3 and 4 certify those two link policies. The second is a four-DMU
CRS/free counterexample: Table 6 certifies its system and division scores,
while Table 7 supplies one selected set of targets for a problem that can
have multiple optima.

| Evidence field | Record |
|---|---|
| **Economic question** | What independent numerical evidence can distinguish a faithful source implementation from a plausible-looking network score? |
| **Technology / estimator** | Case A: three-division series network, VRS, input orientation, fixed and free links. Case B: same topology, CRS, input orientation, free link. |
| **Measure** | Source input-oriented weighted NSBM with reported overall/division scores, references, link ratios, and selected targets. |
| **RTS** | Candidate A verifies VRS under both link controls; Candidate B verifies the exceptional CRS/free divisional-frontier property. |
| **Data / time** | Case A uses ten U.S. power companies in 1994; Case B is a hand-sized synthetic four-DMU dataset. Later dynamic/network models add time or undesirable roles and cannot share this oracle unchanged. |
| **Native score** | Exact source orientation and reconstruction: system score is the declared weighted arithmetic mean of the three division input efficiencies. |
| **Exact aliases** | The 2007 discussion-paper programmes are the openly auditable antecedent of the 2009 published preset; exact table/version differences must be recorded rather than assumed. |
| **Distinct variants** | Kao's slack-based efficiency decomposition, Chen et al.'s two-stage projection/decomposition, dynamic SBM, dynamic network SBM, undesirable/network SBM, super-network SBM, and generalized link-slack models all require their own records and oracles. |
| **Domain** | Exact source data/version, graph, weights, orientation, RTS, link policy, reference membership, and rounding convention; no manual “repair” of values without provenance. |
| **Failures** | Matching only rankings, using the fixed table to validate free links, treating Table 7's solver-selected projection as uniquely identified, or claiming a later descendant implements the Tone--Tsutsui preset merely because both say NSBM. |
| **Solver form** | Oracle harness should compare system/division scores, reconstruction identities, reference/link feasibility, fixed-versus-free ordering, projections, unit rescaling, and the CRS/free counterexample. |
| **Defining source** | Open tables in [Tone and Tsutsui (2007)](https://doi.org/10.24545/00000978), published method in [Tone and Tsutsui (2009)](https://doi.org/10.1016/j.ejor.2008.05.027); family boundaries reviewed by [Kao (2014)](https://doi.org/10.1016/j.ejor.2014.02.039). |
| **Evidence status** | `primary-checked` and `reproduced` for the applicable score tables; descendant map is `review-supported`. |
| **Oracle** | `analytically derived` only for the claim-scoped equation-(26)/(27) accountable-link optima. Neutral fixed/free-link cases supply reconstruction and joint-feasibility property checks; the retired source-table reproduction is not claimed, and no nonunique optimum is basis-locked. |
| **Package recipe** | Public `ToneTsutsuiNetworkSBM`, with `NetworkSBM` retained only as its exact API alias. The source empirical oracles cover input orientation; exact hand cases cover output and non-oriented programmes. |
| **Book location** | **Documentation/source review only.** Reproducibility tables and descendant audits remain outside the handbook. |

## Merge and implementation decisions

- The source input, output, and non-oriented objectives share one technology
  compiler but retain their orientation-specific aggregation identities.
- Fixed/non-discretionary and free/discretionary are two link-control
  specializations of the source preset. They are never inferred from data.
- Equation (26) is a named input-oriented specialization: the recipient owns
  an incoming-link excess once, while supplier and recipient peer plans
  remain equal. Equation (27) is its output-oriented counterpart: the
  supplier owns an outgoing-link shortfall once. Neither supplies a
  non-oriented accountable-link formula.
- Division weights are exogenous valuation inputs. The base source has no
  independently chosen “link weights.”
- The base fixed/free objective excludes link slacks. Equations (26)--(27)
  are public named specializations with exact independent oracles. Common
  intensities, bounded intensity connectivity, undesirable intermediates,
  dynamic carry-overs, and super-efficiency still require their own source
  and validation gates.
- The public implementation accepts connected general networks, including
  cycles; it does not impose an unreported DAG restriction. Quantities must
  be positive on the source domain, and every scored process must have the
  external block required by its orientation.
- A fitted result labels its division scores, slacks, intensities, references,
  free-link targets, and projections as solver-selected where appropriate.
  A unique optimum value is insufficient evidence for a unique
  divisional performance-attribution account.
- `network.sbm.tone_tsutsui_2009` is implemented and public through
  `ToneTsutsuiNetworkSBM`. `NetworkSBM` is an API alias, not a second
  canonical method.
