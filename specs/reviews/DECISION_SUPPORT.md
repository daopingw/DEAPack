# Review register: DEA decision support and coordinated planning

## Purpose and boundary

Conventional DEA asks how an observed organization performs relative to a
declared set of attainable operating plans. The methods in this review ask a
different question: what coordinated change, allocation, agreement, or
organizational design should be considered next?

That shift from diagnosis to prescription adds authority and value judgements.
Someone must be entitled to change resources, outputs, organizational
boundaries, or other units' opportunities. A conservation equation, fairness
principle, maintained-efficiency condition, or bargaining solution is not a
technical detail; it defines the decision being supported.

Every record below uses the common review contract. `Evidence status` and
`Oracle` remain separate from implementation status. All entries are planned:
none is exposed by the current public catalog. A prescriptive scenario is
conditional on its assumptions and is not a causal forecast of what an
intervention will achieve.

## 1. Planning changes for one organization

### `decision.inverse_dea.wei_zhang_zhang_2000` — maintained-efficiency input/output planning

- **Economic question:** If selected inputs are increased, how much additional
  output can an organization plan while preserving a declared efficiency
  level; or, for a required output increase, how much additional input is
  compatible with that maintained level?
- **Technology / estimator / inference:** A source-matched DEA technology and
  base efficiency estimate feed a deterministic inverse optimization problem;
  no sampling inference is implied.
- **Measure:** A Pareto set or selected solution for the unknown input or
  output changes subject to the maintained-efficiency condition.
- **RTS:** The source discusses CCR, BCC, non-increasing, and other scale
  structures. An executable leaf must retain the base model's exact scale
  assumption rather than offering one generic inverse switch.
- **Data / time:** One evaluated organization, the reference observations,
  known changes to one side of its account, and unknown changes to the other.
  A future-period interpretation requires an explicit policy for whether the
  frontier and comparison population remain fixed.
- **Native score:** The planned quantity vector and its Pareto or
  preference-selected status. The maintained base efficiency is a constraint,
  not a newly estimated improvement score.
- **Exact aliases:** “Inverse DEA” and “reverse DEA” are discovery labels only
  when they refer to the same base model, maintained value, adjusted variables,
  reference update, and multi-objective selection rule.
- **Distinct variants:** Input estimation, output estimation, simultaneous
  changes, non-radial and SBM inverse models, undesirable-output and
  meta-frontier inverse DEA, merger applications, and frontier-changing
  forecasts.
- **Domain:** The base DEA measure must be valid on both the original and
  proposed quantities; the adjusted variables and allowed signs of change
  must be declared.
- **Failures:** An empty or unbounded change set, weak Pareto solutions,
  multiple incomparable plans, silently moving the reference frontier,
  preserving a radial score while ignoring economically material slacks, and
  interpreting feasibility as a forecast.
- **Solver form:** Source-dependent linear or multi-objective optimization;
  scalarization or lexicographic selection is a declared preference rule, not
  a numerical tie-break.
- **Defining source:** [Wei, Zhang, and Zhang
  (2000)](https://doi.org/10.1016/S0377-2217(99)00007-7).
- **Evidence status:** primary source abstract and formulation scope checked;
  source-level equation and numerical-oracle freeze remains planned.
- **Oracle:** candidate — the published article contains numerical material,
  but no repository fixture has been reconciled to one complete source leaf.
- **Package recipe:** Planned
  `decision.inverse_dea.wei_zhang_zhang_2000`, composed with an explicit base
  method and solution-selection policy.
- **Book location:** **Documentation/source review only.** No current handbook
  placement; the review must not reserve an appendix for this planned method.

## 2. Coordinating resources across organizations

### `decision.central_allocation.lozano_villa_2004` — organization-wide resource allocation

- **Economic question:** How should a central authority reallocate resources
  or production commitments across units so that the organization improves as
  a whole while every proposed unit plan remains technologically attainable?
- **Technology / estimator / inference:** A common empirical DEA technology is
  used inside one centralized planning problem; the base formulation is
  deterministic and contains no sampling inference.
- **Measure:** Source models minimize aggregate input consumption, radially or
  through declared input-specific preferences, while aggregate output is not
  reduced and all units receive frontier targets.
- **RTS:** The source formulation and later BCC extensions are distinct. The
  system objective, conservation conditions, and unit technologies must be
  audited together under the selected RTS.
- **Data / time:** Comparable units under one authority, transferable
  quantities, fixed or bounded organizational totals, and explicit
  controllability. Planning additional or reduced future resources is a later
  variant, not part of the original observed-resource reallocation by default.
- **Native score:** Aggregate resource saving or output gain plus every unit's
  allocation and attainable target. A system optimum need not make one
  distribution uniquely fair.
- **Exact aliases:** None with ordinary unit-by-unit DEA. A virtual aggregate
  DMU is an exact dual interpretation only under the source's matched
  assumptions.
- **Distinct variants:** Radial versus input-specific preferences, CRS versus
  BCC centralized models, fixed versus changed organizational totals,
  transferable versus non-transferable quantities, price-based allocation,
  and bilevel fairness constraints.
- **Domain:** The central authority must actually control the quantities being
  pooled, units must use comparable technologies, and transfers must respect
  indivisibility, geography, regulation, and adjustment limits where relevant.
- **Failures:** Treating non-transferable resources as a common pool,
  suppressing distributional consequences behind an aggregate gain, multiple
  allocations with the same system value, and calling a centrally imposed
  plan voluntary unit behavior.
- **Solver form:** One coordinated LP in the source family; later fairness,
  indivisibility, or hierarchical variants can require multi-objective,
  bilevel, or mixed-integer programs.
- **Defining source:** [Lozano and Villa
  (2004)](https://doi.org/10.1023/B:PROD.0000034748.22820.33).
- **Evidence status:** primary source abstract and managerial contract checked;
  full equation and oracle reconciliation remains planned.
- **Oracle:** candidate — published numerical results exist, but no exact
  repository reproduction has been certified.
- **Package recipe:** Planned
  `decision.central_allocation.lozano_villa_2004`; transferability and system
  objective are mandatory fields rather than permissive flags.
- **Book location:** **Documentation/source review only.** No current handbook
  placement under the key-model admission gate.

### `decision.fixed_cost_allocation.cook_kress_1999` — equitable shared-cost characterization

- **Economic question:** Which allocations of a common overhead across
  comparable units satisfy a declared concept of equity without arbitrarily
  changing their relative performance?
- **Technology / estimator / inference:** A DEA multiplier technology supports
  a deterministic characterization of allocations; no inferential claim is
  made.
- **Measure:** A set of allocations satisfying efficiency invariance and
  Pareto-minimality in the source account, rather than a new technical
  efficiency measure.
- **RTS:** The source's multiplier construction and normalization must be
  retained. CCR, BCC, common-weight, and network extensions are distinct
  allocation procedures.
- **Data / time:** Comparable units with ordinary inputs and outputs plus one
  shared cost or common resource total. The accounting period, currency, cost
  scope, and allocation base must be common.
- **Native score:** Allocated cost shares and evidence that the declared
  invariance/minimality conditions hold. The admissible set can contain
  alternate allocations and should not be reported as one uniquely “fair”
  answer.
- **Exact aliases:** None with centralized resource reallocation or ZSG DEA:
  allocating an overhead as an additional input is not the same as moving
  productive resources or redistributing a fixed output total.
- **Distinct variants:** Cook--Zhu practical allocation, average-efficiency,
  common-weight, cross-efficiency, cooperative-game, two-stage/network, fixed
  revenue, and inequality-aversion procedures.
- **Domain:** The shared amount is genuinely common and conserved, the chosen
  fairness principles are accepted by the decision maker, and allocated costs
  have comparable economic meaning across units.
- **Failures:** Nonunique allocations presented as objective fairness,
  infeasible invariance restrictions, zero or arbitrary multiplier weights,
  mixing monetary overhead with physical inputs without a unit policy, and
  ignoring who bears the allocation.
- **Solver form:** Source multiplier programs and allocation
  characterization; later uniqueness or fairness rules may require secondary
  optimization or game-theoretic solution concepts.
- **Defining source:** [Cook and Kress
  (1999)](https://doi.org/10.1016/S0377-2217(98)00337-3).
- **Evidence status:** primary article and source principles checked;
  executable formulation and alternate-optimum policy remain planned.
- **Oracle:** candidate — the source numerical example is available, but no
  automated repository reproduction is certified.
- **Package recipe:** Planned
  `decision.fixed_cost_allocation.cook_kress_1999`; later allocation rules
  receive separate IDs.
- **Book location:** **Documentation/source review only.** No current handbook
  placement under the key-model admission gate.

### `decision.fixed_sum_zsg.lins_etal_2003` — interdependent fixed-total outcomes

- **Economic question:** How should performance and attainable reallocations
  be assessed when one unit can gain an output or quota only by reducing what
  remains available to other units?
- **Technology / estimator / inference:** A BCC-based empirical technology is
  coupled across units by a constant aggregate output account; the base source
  is deterministic.
- **Measure:** Source zero-sum-gains efficiency under a declared redistribution
  strategy and the resulting jointly feasible output allocation.
- **RTS:** The original Olympic application develops a VRS/BCC construction.
  CRS, hybrid-scale, environmental, and other extensions are separate leaves.
- **Data / time:** Comparable units, at least one interdependent quantity with
  a defensible fixed total, and a redistribution rule specifying which units
  bear each gain. Panel or policy-vintage totals require an explicit period
  account.
- **Native score:** ZSG efficiency and the complete post-redistribution vector.
  A unit's target cannot be interpreted without the offsetting changes imposed
  on the other units.
- **Exact aliases:** “Constant-sum output DEA” is an alias only when the same
  BCC technology, total, redistribution strategy, and target algorithm are
  used.
- **Distinct variants:** Equal, proportional, and minimum-reduction
  strategies; input versus output fixed sums; undesirable-output quotas;
  multiple fixed-sum variables; bargaining allocations; and ordinary DEA with
  independent outputs.
- **Domain:** The aggregate total is institutionally or physically fixed over
  the decision horizon. Market growth, storage, imports, or unmodeled outside
  units can invalidate the zero-sum account.
- **Failures:** Declaring an approximately scarce quantity exactly fixed,
  evaluating units independently after coupling them, convergence or
  path-dependence in iterative target construction, and efficiency-only quota
  allocations that ignore equity or legal entitlements.
- **Solver form:** Coupled or iterative DEA programs under the selected
  redistribution rule; termination, tolerances, and joint conservation
  residuals must be reported.
- **Defining source:** [Lins, Gomes, Soares de Mello, and Soares de Mello
  (2003)](https://doi.org/10.1016/S0377-2217(02)00687-2).
- **Evidence status:** primary article and constant-sum mechanism checked;
  equation freeze for a first executable redistribution strategy remains
  planned.
- **Oracle:** candidate — the Olympic dataset and published results are
  potential source fixtures but have not been reproduced in the repository.
- **Package recipe:** Planned
  `decision.fixed_sum_zsg.lins_etal_2003`; redistribution strategy and
  conservation diagnostics are required result metadata.
- **Book location:** **Documentation/source review only.** No current handbook
  placement under the key-model admission gate.

## 3. Changing organizational boundaries

### `decision.merger_restructuring.bogetoft_wang_2005` — potential gains from merger

- **Economic question:** Could a proposed combination of organizations save
  resources, and how much of the potential comes from better individual
  practice, a more favorable input/output mix, or a different operating size?
- **Technology / estimator / inference:** Pre-merger observations estimate a
  non-parametric production technology used to assess hypothetical aggregated
  plans; the base procedure is deterministic and ex ante.
- **Measure:** An input-oriented merger index decomposed into technical
  learning, harmony/mix, and size/scale components under the source
  construction.
- **RTS:** CRS and non-CRS technologies change the size component and must be
  reported. Scale assumptions cannot be inferred from the word “merger.”
- **Data / time:** Candidate organizations with additive or otherwise
  explicitly aggregable input/output accounts and a common production scope.
  Transaction costs, service obligations, geographic constraints, and
  post-merger demand must be added if they matter.
- **Native score:** Overall potential merger gain and its multiplicative
  technical, harmony, and size components. A value indicates attainable
  potential under the represented technology, not realized synergy.
- **Exact aliases:** “Harmony,” “scope,” and “mix” are source-proximate
  descriptions only within the same decomposition. They are not an
  unconditional measure of economies of scope.
- **Distinct variants:** Alternative decomposition orders, cost and network
  merger models, horizontal versus vertical merger technologies, merger
  target selection, inverse-DEA merger planning, and ex-post causal evaluation.
- **Domain:** Inputs and outputs can be aggregated meaningfully, the candidate
  units share a relevant technology, and the hypothetical merged plan respects
  institutional and physical constraints.
- **Failures:** Reading potential as forecast profit, ignoring integration and
  transaction costs, attributing decomposition components causally, combining
  incompatible services, and comparing alternate decompositions as if their
  component labels were identical.
- **Solver form:** A source-defined sequence of DEA programs for the observed,
  technically improved, harmonized, and rescaled plans.
- **Defining source:** [Bogetoft and Wang
  (2005)](https://doi.org/10.1007/s11123-005-1326-7).
- **Evidence status:** primary formulation, managerial interpretation, and
  decomposition identity checked; implementation and source-table oracle
  remain planned.
- **Oracle:** candidate — the Danish extension-office application and public
  numerical material can support a future source fixture.
- **Package recipe:** Planned
  `decision.merger_restructuring.bogetoft_wang_2005`; alternative merger
  decompositions require distinct operator IDs.
- **Book location:** **Documentation/source review only.** No current handbook
  placement under the key-model admission gate.

## 4. Negotiating among competing improvement claims

### `decision.bargaining.targets.lozano_hinojosa_marmol_2019` — bargaining-based target selection

- **Economic question:** When input savings and output gains compete, which
  efficient target represents an explicit agreement among those dimensions
  rather than the analyst's arbitrary weighted sum?
- **Technology / estimator / inference:** The declared DEA feasible set becomes
  the bargaining set; each adjustable input or output dimension is a player
  with a stated utility and disagreement value. No sampling inference is part
  of the base method.
- **Measure:** A target selected by a named Nash, lexicographic
  Kalai--Smorodinsky, weighted lexicographic egalitarian, or normalized
  utilitarian solution.
- **RTS:** Inherited from the DEA technology used to define feasible targets;
  the bargaining solution does not select or justify RTS.
- **Data / time:** One evaluated unit, its feasible improvement set, adjustable
  variables, utility normalizations, disagreement point, and any bargaining
  weights. Intertemporal or network bargaining requires a different feasible
  set and player definition.
- **Native score:** The agreed target, variable-level utility gains, solution
  concept, and disagreement/reference values. Different bargaining solutions
  are normative alternatives, not numerical solvers for one score.
- **Exact aliases:** None among Nash, Kalai--Smorodinsky, egalitarian, and
  utilitarian solutions, even when one dataset yields the same target.
- **Distinct variants:** Closest-target DEA, direction or slack weights,
  interactive multi-objective planning, process-level network bargaining,
  common-weight bargaining, and fixed-sum bargaining.
- **Domain:** Player and utility definitions have managerial meaning, utility
  scales are comparable under the selected solution, and the disagreement
  point is feasible and defensible.
- **Failures:** Calling mathematical variables actual stakeholders, hiding
  value judgements in normalizations, nonunique or undefined solutions,
  selecting a solution because it gives a preferred ranking, and describing
  agreement without participation or delegated authority.
- **Solver form:** Named linear, lexicographic, or nonlinear bargaining
  programs over the DEA feasible set; backend and global-optimality
  requirements depend on the selected solution.
- **Defining source:** [Lozano, Hinojosa, and Mármol
  (2019)](https://doi.org/10.1016/j.omega.2018.05.015).
- **Evidence status:** primary article's player, disagreement, and four-solution
  structure checked; executable equations and oracles remain planned.
- **Oracle:** candidate — the container-shipping application is a possible
  source fixture but has not been reproduced.
- **Package recipe:** Planned
  `decision.bargaining.targets.lozano_hinojosa_marmol_2019`, with solution
  concept stored as method identity rather than an undocumented option.
- **Book location:** **Documentation/source review only.** No current handbook
  placement under the key-model admission gate.

### `decision.bargaining.fixed_sum.lozano_2023` — bargaining under a conserved total

- **Economic question:** How can units negotiate efficient targets when every
  improvement in a fixed-sum input, desirable output, or undesirable output
  changes what remains available to the others?
- **Technology / estimator / inference:** A centralized fixed-sum DEA
  technology defines the feasible bargaining set; each variable of each unit
  is treated as a player in the source Nash construction.
- **Measure:** Nash bargaining target allocation followed by the source's
  modified enhanced-Russell performance account.
- **RTS:** Explicit in the underlying fixed-sum technology; alternate scale
  structures are not inferred from the Nash solution.
- **Data / time:** Multiple units, one or more variables with conserved totals,
  utility and disagreement definitions, and a common decision horizon.
- **Native score:** Complete joint targets, conservation residuals, player
  utility gains, Nash objective, and the associated modified ERM scores.
- **Exact aliases:** None with the earlier iterative ZSG model or ordinary
  variable-level bargaining. The feasible set and performance measure both
  differ.
- **Distinct variants:** Other bargaining solutions, unit-level rather than
  variable-level players, environmental quotas, multiple periods, networks,
  and legal or equity constraints.
- **Domain:** Fixed totals and central coordination are credible; utilities
  reflect the direction and scale of desirable change; every affected unit is
  represented in the system boundary.
- **Failures:** Omitting outside claimants, treating legal entitlements as
  freely negotiable, satisfying the bargaining objective while violating
  conservation numerically, and calling Nash's axioms universal fairness.
- **Solver form:** Centralized nonlinear bargaining model, with any
  reformulation and global-optimality certificate stated explicitly.
- **Defining source:** [Lozano
  (2023)](https://doi.org/10.1016/j.omega.2022.102728).
- **Evidence status:** primary article's fixed-sum, player, Nash, and modified
  ERM structure checked; equation-level implementation audit remains planned.
- **Oracle:** candidate — source validation datasets exist, but no repository
  reproduction is certified.
- **Package recipe:** Planned
  `decision.bargaining.fixed_sum.lozano_2023`; it composes neither by a generic
  `bargaining=True` flag nor by post-processing ZSG scores.
- **Book location:** **Documentation/source review only.** No current handbook
  placement under the key-model admission gate.

## 5. Exploring futures without pretending to predict them

### `decision.scenario_forecast` — declared future technology and constraint scenarios

- **Economic question:** How would attainable performance or planning targets
  change under an explicitly hypothesized future comparison set, technology,
  price system, regulation, resource budget, or organizational structure?
- **Technology / estimator / inference:** A scenario builder changes one or
  more declared study axes before refitting a source-qualified DEA method.
  There is no generic DEA forecasting estimator and no automatic uncertainty
  statement.
- **Measure:** Scenario-specific efficiency, target, allocation, or
  productivity results plus differences from a named baseline; each native
  measure retains its original interpretation.
- **RTS:** Declared separately for every scenario. Changing scale assumptions
  is a sensitivity experiment, not evidence that returns to scale will change.
- **Data / time:** Versioned baseline data, scenario assumptions, units,
  provenance, horizon, and immutable transformations. Estimated future data
  must retain the forecasting model and its uncertainty outside the DEA
  result.
- **Native score:** A tidy scenario panel containing baseline and alternative
  native results, assumption deltas, feasibility, and comparability flags.
- **Exact aliases:** None with prediction, causal counterfactual analysis,
  stress testing, inverse DEA, robust optimization, or a confidence interval.
- **Distinct variants:** Deterministic what-if analysis, forecast-then-DEA,
  robust worst-case planning, technology-vintage simulation, policy
  constraints, and optimization that chooses a scenario.
- **Domain:** Every altered assumption is economically interpretable and
  comparable with the baseline; the analyst distinguishes exogenous scenario
  inputs from endogenous target choices.
- **Failures:** Calling a favorable possibility a forecast, double-using
  estimated future values as certain observations, comparing non-nested
  technologies without a bridge, data leakage, and omitting infeasible or
  adverse scenarios.
- **Solver form:** A reproducible task graph over existing source-qualified
  estimators; the scenario layer itself should not introduce an unrestricted
  optimization language.
- **Defining source:** No single paper defines a generic DEA scenario or
  forecasting procedure. Each future-data model and each composed DEA leaf
  requires its own source and validation record.
- **Evidence status:** registry-provisional; no single generic source or
  canonical executable DEA formulation is selected.
- **Oracle:** not located — an oracle is meaningful only after one complete
  forecast/scenario composition is frozen.
- **Package recipe:** Planned discovery procedure
  `decision.scenario_forecast`; no public generic `future=True` switch.
- **Book location:** **Documentation/source review only.** No current handbook
  placement under the key-model admission gate.

## 6. Merge boundary and implementation consequences

Safe software reuse is narrower than the common word *allocation* suggests:

- inverse DEA reuses a base technology but adds a maintained-performance
  condition for one changing unit;
- centralized allocation couples all unit plans under one authority and
  aggregate objective;
- fixed-cost allocation assigns a common overhead under fairness principles;
- ZSG fixes an aggregate quantity and makes units' opportunities
  interdependent;
- merger analysis changes the organizational boundary and decomposes
  production potential; and
- bargaining selects an agreement from a feasible improvement set under a
  named normative solution.

These methods can share sparse technology blocks, result tables, scenario
provenance, and visualization infrastructure. They must not share one
unrestricted “planner” estimator. Before any public implementation, DEAPack
must freeze:

1. who controls each decision and which parties bear its consequences;
2. the exact system boundary and conservation equations;
3. the performance condition or system objective;
4. the fairness, priority, utility, or bargaining principle;
5. unit-level and system-level feasibility diagnostics;
6. alternate-optimum and solution-selection policy;
7. whether the result is diagnostic, prescriptive, predictive, or causal; and
8. a published or independent numerical oracle.

## 7. Source map

Core source-qualified leaves:

- Wei, Zhang, and Zhang (2000), inverse input/output planning,
  <https://doi.org/10.1016/S0377-2217(99)00007-7>;
- Cook and Kress (1999), equitable shared-cost characterization,
  <https://doi.org/10.1016/S0377-2217(98)00337-3>;
- Lozano and Villa (2004), centralized resource allocation,
  <https://doi.org/10.1023/B:PROD.0000034748.22820.33>;
- Lins et al. (2003), zero-sum-gains DEA,
  <https://doi.org/10.1016/S0377-2217(02)00687-2>;
- Bogetoft and Wang (2005), potential gains from mergers,
  <https://doi.org/10.1007/s11123-005-1326-7>;
- Lozano, Hinojosa, and Mármol (2019), bargaining-based DEA targets,
  <https://doi.org/10.1016/j.omega.2018.05.015>; and
- Lozano (2023), Nash bargaining over fixed-sum variables,
  <https://doi.org/10.1016/j.omega.2022.102728>.

A recent field-wide allocation review confirms that fixed-cost and productive
resource allocation have developed into a substantial literature, but it does
not make their competing fairness and system objectives interchangeable:
[Hazhir and Foroughi
(2025)](https://doi.org/10.1016/j.seps.2025.102275).
