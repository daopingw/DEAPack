# Reproducible book figures

Theory and management diagrams are generated without optional plotting dependencies:

```bash
python book/figures/generate_concept_figures.py
```

Generated SVG files live in `book/_static/figures/`. Figure text is limited to
short analytical labels, with the full interpretation in the surrounding
text and caption. The Chinese edition uses reviewed label records in
`zh_CN_labels.json` and deterministic variants under
`book/_static/figures/zh_CN/`:

```bash
python book/figures/localize_handbook_figures_zh.py
python book/figures/localize_handbook_figures_zh.py --check
```

The catalog binds each English SVG by SHA-256 and covers every visible
`text`, `title`, and `desc` node by either an explicit translation or an
explicit preservation decision. A changed source figure must be reviewed; it
cannot silently reuse an older Chinese diagram.

`range-directional-signed-opportunity.svg` is a dependency-free, exact
teaching geometry from `generate_concept_figures.py`. Its three observations
are the project-designed synthetic coordinates $F=(-2,1)$, $N=(-1,5)$, and
$E=(4,0)$, all with one common resource input. The output-oriented range ray
toward $I=(4,5)$ meets the VRS segment at
$T=(1,3)=0.6N+0.4E=F+\tfrac12(I-F)$, so $\beta=1/2$. Neither the numerical
payload nor the layout reproduces a published empirical example or source
figure; the literature citation in the chapter supports only the RDM model
definition.

Package-native case-study figures are generated with the optional
visualization backend:

```bash
MPL_IGNORE_SYSTEM_FONTS=1 \
MPLCONFIGDIR=/tmp/deapack-matplotlib \
python book/figures/generate_result_figures.py
```

`radial-frontier-result.svg`, `radial-improvement-result.svg`,
`sbm-slack-contrast-result.svg`,
`scale-efficiency-performance-result.svg`,
`undesirable-sbm-improvement-result.svg`,
`environmental-ddf-improvement-result.svg`,
`environmental-ml-performance-result.svg`,
`ddf-improvement-result.svg`, `luenberger-performance-result.svg`,
`trajectory-contrast-performance-result.svg`,
`full-horizon-trajectory-contrast-result.svg`,
`hicks-moorsteen-performance-result.svg`,
`network-system-performance-result.svg`, `carryover-portfolio-trajectory-result.svg`,
`dynamic-sbm-scored-backlog-result.svg`,
`three-process-service-account-result.svg`, and
`metafrontier-decomposition-result.svg` are produced through the same
`DEAResult.plot()` calls taught in the corresponding chapters. They therefore
exercise the public target or measure semantics, benchmark geometry,
solver-status policy, and provenance footer rather than recreating package
results in a separate illustration script.

`slack-family-rulers-result.svg` is a different kind of package-driven book
figure. It composes three public result tables after their claims have passed
the applicable release gates; it is not emitted by a new `DEAResult.plot`
kind.

The four `community-hospital-*.svg` figures form one package-driven capstone
rather than a new model or plotting kind. The generator loads the bundled
`community_hospital_capstone` roster, applies the pre-score population rules,
and uses public `BCCInput`, `SBM(returns_to_scale="vrs")`, and
`scale_efficiency(..., orientation="input")` results. The screening figure
shows the 64/60/52/48 population sequence; the performance figure summarizes
the 48-hospital primary BCC-I study; the H048 figure reads its selected H008
peer and variable targets from the fitted result; and the roster-sensitivity
figure compares those same 48 hospitals after four borderline-referral
hospitals enter the eligible population. These are descriptive decision aids.
They do not turn feasible input reductions into automatic staffing or budget
decisions, and they do not interpret the CCR--BCC ratio as a recommendation to
resize a hospital.

`ddf-programme-contracts-result.svg` is likewise a package-driven composite,
not a new model, API, solve route, or `DEAResult.plot()` kind. It holds
organization E's `slacks_2x2` record and the VRS/global technology fixed while
three public ordinary-DDF fits declare observed-input/zero-output,
zero-input/observed-output, and joint observed directions. Each fit passes the
existing `prepare_directional_ddf_improvement_data` contract before the
generator reads its original-unit first-stage commitments. The certified
native values are 0.247253, 0.419355, and 0.247253. The input-only programme
promises labor and capital savings of 0.494505 and 0.692308; the output-only
programme promises service and quality additions of 0.545161 and 0.260000;
the joint programme requires those same resource savings together with
service and quality additions of 0.321429 and 0.153297. The display does not
rank the three beta values. A zero direction requires no change in that role
during the first-stage package: its observed input remains a cap and its
observed output remains a floor, while the separately certified completion may
still reveal variable-specific opportunities. Preparation and rendering add
no solve, and neither the package nor its selected completed target establishes
causation, implementation feasibility, priority, or a unique prescription.

`ddf-improvement-result.svg` uses organization E from the bundled
`slacks_2x2` data. The public ordinary-DDF result first supports a common
observed-quantity programme of $\beta=0.247253$: labor and capital contract
to 1.505495 and 2.107692, while service and quality expand to 1.621429 and
0.773297. The selected slack completion then adds 0.031319 service and
0.057253 quality, giving final targets 1.652747 and 0.830549. Before the
public `result.plot(kind="improvement", dmu_id="E")` call, the generator
requires both LP phases and their raw, economic, and published-output
certificates, checks the exact method and direction policy, and independently
reconstructs every $\beta g$, extra slack, positive slack scale, normalized
slack identity, and target. Peer and dual release
are not required because neither claim is displayed. Each variable keeps its
original unit and no common quantity axis is constructed. The selected plan
is conditional and potentially non-unique, not a causal explanation, a
least-cost transition, or a management prescription.

`scale-efficiency-performance-result.svg` uses the same scalar teaching case
as the scale chapter. It shows the additional radial gap admitted when the VRS
comparison is enlarged to proportional replication. The plot deliberately
does not attach an expansion or contraction recommendation to that ratio;
local returns, demand, prices, and adjustment costs require separate evidence.

`three-performance-accounts-result.svg` is a package-driven composite rather
than a new `DEAResult.plot()` kind. It uses the bundled
`economic_efficiency_4` data, a score-only public input-oriented BCC fit, and
the public closed-form `ReturnToDollarEfficiency` fit under the common prices
$w=2$ and $p=(3,5)$. The generator requires all four radial score programmes
and their economic quantity accounts to be certified, independently rebuilds
every observed cost, revenue, return-to-dollar ratio, and relative
profitability score, and verifies that B is the unique ratio maximizer. The
physical middle card is the explicitly declared equal-count level
$(y_{standard}+y_{premium})/x$; it is neither productivity change nor a DEA
productivity index. Its scale is not shared with either fitted score. Plans A
and B both have input-oriented VRS radial score one; this score-only fit makes
no Pareto--Koopmans or slack-completion claim. A has the higher equal-count
physical productivity level, while B earns more revenue per unit of cost and
more observed profit $(R-C)$ because the supplied prices value its
premium-service mix more highly. The displayed $R/C$ ratio is not observed
profit, and none of the three accounts is a causal explanation, quality
judgement, or management prescription. Here observed profit is the operating
surplus reconstructed from the modelled service revenue and resource cost,
not a complete accounting statement.

`peer-eligibility-sensitivity-result.svg` is also a package-driven composite,
not a new `DEAResult.plot()` kind. It reuses the seven-hospital candidate
ledger declared in the study-design chapter and holds Lakeside's recorded 120
clinical hours, 80 staffed bed-days, and 100 risk-adjusted completed episodes
fixed. Two public score-only input-oriented BCC fits differ only in the rows
admitted before fitting. The same-contract rule retains Lakeside, North, and
East; Lakeside's certified radial score is 0.9375 and its selected phase-one
peer evidence is North. The broader district-mission rule also admits West
after an ex-ante institutional-comparability review; Lakeside's score is then
0.902778 and its certified active peer plan is
$(4/9)North+(5/9)West$. The generator freezes the complete candidate
quantities and context labels, both eligible rosters, every public summary row,
both sets of phase-one LP/economic/peer/dual certificates, the exact Lakeside
peer intensities, and both reconstructed peer activities before drawing the
comparison. It requests no slack completion, adds no post-fit solve, and
identifies the 3.47 percentage-point difference as sensitivity to
two pre-declared comparison populations--not a causal contract effect or evidence that
West's practices will transfer or Lakeside's management is inferior. Both
populations are deliberately too small for a persuasive empirical frontier,
and harm remains outside this narrow ordinary-BCC account.

`reference-frequency-result.svg` is a package-driven selected-plan case
account, not a new DEA model. It coexists with the public
`DEAResult.plot(kind="references")` renderer: the shared plot applies an
explicit top-N/selected-row readability contract, whereas this eight-row book
case retains the original A--H order so zero-frequency organizations remain
visible. The case fits the bundled `slacks_2x2` data once with the public
score-only input-oriented BCC API and then calls
`result.reference_frequency()`. The generator reads only the resulting public
`reference_frame` and `edge_frame`: it verifies the complete source peer
certificate, the 12 reported edges strictly above the source
`peer_tolerance`, the 1/4/5/2/0/0/0/0 total frequencies, their self/other split,
and the zero-additional-solve ledger before drawing. It makes no exact-support
claim for intensities at or below the reporting threshold. The case retains
A--H rather than sorting the bars into a league table.
Repeated selection is described as comparative reach and an audit lead, not
superior management, service quality, an outlier diagnosis, a causal or
transferability finding, or membership in the union of all optimal reference
sets.

`undesirable-sbm-improvement-result.svg` uses the transparent two-plant
environmental case. Plant C's certified plan separately displays one resource
unit saved, one desirable service unit added, and one undesirable residual
unit reduced. Preparation reconstructs the fitted strong-separable output
account and the score $2/7$; the residual reduction is not relabelled as a
service gain, damage valuation, causal effect, or unique prescription.

`environmental-ddf-improvement-result.svg` comes from the public
`CommonFactorWeakDisposalDDF` result for Central in 2020 in the bundled
`environmental_panel` data. Under weak common-factor disposal, CRS, and a
contemporaneous reference, the certified conditional plan fixes energy and
labour, adds 6.652902 units of electricity, and removes 23.897341 units of
carbon dioxide at $\beta=0.083815$. Before the public
`result.plot(kind="improvement", ...)` call, the generator requires both LP
phases and their raw, economic, and published-output certificates, then
independently reconstructs $\beta$ times every public direction, every extra
slack, and every public target. The case happens to have zero extra slack.
Peer and dual release are not required because neither claim is displayed.
Rows retain their different original units and do not share a quantity axis;
the figure is one feasible benchmark, not a unique plan, engineering design,
causal effect, or cost conclusion.

`environmental-ml-performance-result.svg` uses the public adjacent-period
`MalmquistLuenbergerDEA` result for the bundled `environmental_panel` and the
2020--2021 transition. Before rendering, the generator verifies the exact
six-plant roster, all four LP and environmental quantity certificates for
South, East, Central, and Coastal, and each transition's complete
multiplicative account. North and West are intentionally not plotted as points:
the fitted weak common-factor CRS technology cannot complete one or both
required cross-period reference comparisons. The bounded availability footer
names both plants and retains the decisive infeasible status. Those unavailable
headlines are neither zero productivity changes nor numerical solver
malfunctions. The figure is a benchmark-conditional adjacent-period screen,
not a causal rating. The
full-horizon GML value remains an immediately adjacent reference-information
sensitivity table in the chapter; no second GML result figure is generated.

The two Malmquist performance figures use the same two-period, two-service
panel and the same output-oriented CRS assumptions. The first admits the two
contemporaneous technologies to the comparison; the second uses one
full-horizon technology. Their different positions for organization DMU1 are
therefore evidence about the declared reference-information policy, not two
names for the same opportunity component and not rival causal explanations.

`metafrontier-decomposition-result.svg` uses the six-organization declared-
group oracle. It joins each certified group efficiency to its pooled-
opportunity efficiency and prints the exact MTR, so a reader can distinguish
within-group operating performance from proximity between represented
opportunity sets. Its public preparation contract checks both component
certificates, nestedness, bounds, and the group-efficiency--MTR identity; it
does not assign either comparison to management or a causal environment
effect.

`luenberger-performance-result.svg` uses the handbook's exact two-hospital
CRS programme account. Staff is held fixed and one programme unit means one
additional batch of 100 completed treatments. Hospital A records one unit and
Hospital B two units in 2021; these are absolute programme quantities, so the
second value does not mean that B is twice as productive as A. A point enters
the substantive figure only after all four directional-distance LPs and the
complete additive productivity account have passed their release
certificates.

`hicks-moorsteen-performance-result.svg` uses the same VRS
`productivity_panel` result as the handbook's complete quantity account. The
points compare certified 2020--2021 headline changes across organizations;
they do not replace the accompanying output-quantity and input-quantity
indexes or convert physical productivity into profitability, welfare, or a
causal explanation.

`sbm-slack-contrast-result.svg` uses the neutral uneven service plan from the
teaching case. It places each resource saving and service gain on the focal
organization's own proportional ruler, while the adjacent ledger retains the
observed and selected quantities in their original units. Its public
preparation contract independently reconstructs the certified SBM score and
rejects environmental, network, dynamic, and non-SBM result institutions.

`slack-family-rulers-result.svg` uses organization E from the bundled
`slacks_2x2` data to isolate the reporting ruler from the physical benchmark.
Public Additive DEA, RAM, and SBM fits must all select the VRS plan
$0.25B+0.75C$, the same four original-unit slacks, and the same targets before
the figure is rendered. Each displayed score and plan claim must pass its
applicable post-solution release contract. The right-hand score cards have no
shared axis: the unit-dependent additive total, sample-range RAM efficiency,
and own-operation SBM efficiency are native reports with different neutral
values and directions, not interchangeable rankings. The composition is a
book figure built from public result tables; it does not add a model, result
measure, or `DEAResult.plot` kind.

`carryover-portfolio-trajectory-result.svg` uses a neutral carry-over path from the
four-period Dynamic-SBM sample. It distinguishes observed discretionary
carry-over, the selected outgoing target, and the value inherited next period;
the lower panel retains the four period accounts and the native horizon result.
Its public preparation contract checks both postsolve certificates, all three
adjacent-period handoffs, the score-inclusion flags, and the source terminal
boundary before rendering.

`dynamic-sbm-scored-backlog-result.svg` uses the transparent two-organization
capacity-and-backlog case. Its upper panel follows the Strained organization's
backlog in original units, while its lower panel retains the complete period
operating-plan account formed from ordinary inputs and outputs together with
both scored carry-overs. The bars are therefore neither a backlog attribution
nor a causal decomposition. Preparation reconstructs the exact account
($A_o=0.75$, $B_o=1.50$, and $\rho_o=0.50$), verifies adjacent-period
inheritance, and confirms from the fitted result that the bad carry-over enters
the reported score.

`three-process-service-account-result.svg` uses a neutral service plan from the
three-process Tone--Tsutsui sample. It displays the selected process input
accounts, reconstructs the system result from the declared 0.4/0.2/0.4
weights, and keeps the two observed and selected free-link handoffs in their
original units. Its public preparation contract rejects other Network DEA
reporting institutions and independently checks the graph topology,
certificates, process accounts, weights, and handoff continuity before
rendering.

`radial-frontier-result.svg` uses the eight-unit scalar teaching data. The VRS
frontier is formed only from certified strongly efficient observations, and
arrows end at the result's own slack-completed targets. Its footer states that
benchmark opportunities are neither causal explanations nor prescriptions.

`radial-improvement-result.svg` uses the exact three-branch public BCC-I case.
Branch C records resource 1 and service 0.5. Its certified phase-one factor is
$\theta=1$, so the reconstructed radial plan remains resource 1 and service
0.5; the separate completion account retains zero resource slack, adds 0.5
service, and reaches the public final target $(1,1)$. Before the public
`result.plot(kind="improvement", dmu_id="C")` call, the generator verifies the
complete preset identity, data roster, $3+3=6$ fitted solve count, both LP/raw-
economic/published-economic/output-account certificates, summary validity,
and every target/slack identity. The plot's radial-specific preparer repeats
the family-level semantic and row reconstruction gates from fitted public
tables. Peer and dual publication are not required because neither claim is
displayed. Preparation and rendering add no solve. The three columns are
accounting claims, not an implementation order, and the selected target is not
claimed to be unique, closest, least-cost, causal, or prescriptive.

`local-rts-operating-response.svg` translates increasing, constant, and
decreasing local returns into proportional resource and attainable-service
responses around one selected efficient operating plan. It deliberately
separates that diagnosis from a recommendation to expand or contract.

`cfg-cross-period-reference.svg` turns the exact Old/New environmental-DDF
fixture into a cross-period management account. New combines more service
with less residual than the old fixed-input technology can reproduce; the
reverse arrow reaches the exact old-reference target and labels
$\beta=-3/5$ as a signed reference gap, not a better-or-worse ranking.

`malmquist-luenberger-frontier-account.svg` places the two independently
compiled CFG productivity fixtures side by side. One panel records a smaller
contemporaneous operating shortfall against the same relevant reference
opportunity; the other records more favorable represented environmental
opportunities while both plans remain own-period benchmarks. Observation-
scaled directions, the admissible $-3/5$ cross-period distance, both exact
factorizations, and the noncausal interpretation boundary are frozen in the
figure.

`environmental-four-distance-matrix.svg` specializes the two-plan,
two-technology comparison matrix for environmental directional distances. It
uses uppercase $D$ consistently with the ML chapter while leaving the
lowercase radial matrix available to the ordinary productivity chapters.

`luenberger-programme-ledger.svg` gives ordinary Luenberger productivity its
own directional-distance account. One input-saving/output-expansion programme
supplies the physical unit for all four old-plan/new-plan and old-opportunity/
new-opportunity appraisals; the ledger then combines the two fixed-benchmark
changes additively and warns that the allocation is not causal.

`hicks-moorsteen-accounting.svg` keeps the complete quantity account visible.
Each period technology contributes one output-quantity and one input-quantity
comparison; the two period views are reconciled symmetrically before the
output index is divided by the input index. It is generated with the two other
Part IV teaching ledgers, and all three retain at least 9 px effective text at
a 600 px handbook column width.

Historical source-table diagrams for non-separable SBM and cost decomposition
are not generated or distributed. The maintained chapters use neutral
project-authored examples; the cited papers remain the authority for their
method equations.

`material-balance-management-targets.svg` freezes the four-plan VRS teaching
case. For the same output commitment, D first removes common resource waste
at C and then changes the input mix toward B, separating $TE=0.5$ from
physical-content $EAE=0.75$ while preserving $EE=6/16=0.375$. Parallel
material-inflow lines make clear that the second comparison concerns the
resource mix, not another radial contraction or a least-cost recommendation.

`revenue-technical-allocative.svg` is generated deterministically by
`revenue_technical_allocative()`. Its coordinates reproduce Unit 1 in the
five-unit VRS revenue example: observed mix $(7,4)$, proportional plan
$(9,36/7)$, and revenue-maximizing mix $(9,9)$ at $p=(3,2)$. The generator
also fixes the equal-revenue lines at $R=29$ and $R^*=45$.

`economic-objectives-management-map.svg` keeps Plan D from the shared
`economic_efficiency_4` teaching dataset fixed while changing the managerial
question. It records the exact minimum-cost, maximum-revenue and
maximum-profit, and directional Nerlovian targets from the package tests. The
diagram makes the family-level lesson visible: prices value feasible operating
plans, but the declared objective determines which opportunity is relevant.

`two-stage-responsibility-chain.svg` presents the Kao--Hwang insurance example
as an organizational production account. It shows the external-resource,
premium-acquisition, premium-handoff, profit-generation, and final-outcome
roles; the shared intermediate value account; and the distinct upstream and
downstream peer systems. The diagram is deliberately managerial rather than
geometric: shared multiplier accounting coordinates the handoff without
claiming common peers or causal stage effects.

`two-stage-accounting-choices.svg` holds one research--commercialization chain
fixed and contrasts three family-level reporting institutions: system-only
radial performance, a relational product, and endogenous-share additive
process attribution. It deliberately replaces paper and industry labels with
the economic question each account answers, and states what the reported
process quantities cannot be interpreted as.

`closed-vs-open-network.svg` contrasts a closed series chain with an open
directed acyclic network. External resources can enter the process that uses
them, external results can leave the process that creates them, and distinct
internal links may branch, rejoin, or skip a process. The figure uses
organizational boundary crossings rather than geometric frontier language.

`network-sbm-governance.svg` contrasts the two core link-governance questions
used in the handbook. A fixed link protects the observed handoff, while a free
link permits the connected processes to choose one coordinated target. Both
panels preserve supplier--recipient continuity; source-qualified link-scoring
extensions remain in the package Documentation.
