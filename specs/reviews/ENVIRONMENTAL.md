# Environmental efficiency: production accounts before scores

## Purpose and scope

This review asks a managerial question before it asks for a DEA model:

> How is an unwanted outcome generated, what can the producer control, and
> what sacrifice or pollution-control activity makes a reduction attainable?

An emissions column does not become an environmental technology merely
because it is passed to a solver as a “bad output.” The same observations can
support materially different accounts of production: free disposal,
source-qualified weak disposal, by-production, material conservation, or an
explicit treatment process. A directional, hyperbolic, or slacks-based
measure can then be placed on one of those accounts. Changing the measure
must not silently change the production story.

This document is the source-facing review behind the environmental entries in
[`LITERATURE_BASELINE.md`](../LITERATURE_BASELINE.md),
[`METHOD_UNIVERSE.md`](../METHOD_UNIVERSE.md), and
[`METHODS.md`](../METHODS.md). It is not an API reference and it does not
promote a planned method to implemented status.

## Evidence protocol

Each evidence record uses the same fields so that it can later be moved to a
validated registry without rewriting its substance.

| Field | Meaning |
|---|---|
| **Economic question** | The production, decision, or policy question the model answers. |
| **Technology / estimator** | The attainable production account and its empirical construction. |
| **Measure** | The improvement programme or value criterion applied to the technology. |
| **RTS** | Returns-to-scale assumptions admitted by the evidence record. |
| **Data / time** | Required data roles and whether the record is static or panel based. |
| **Native score** | The source-native value and improvement convention; no convenience transform is silently substituted. |
| **Exact aliases** | Names that denote the same model on a stated domain. |
| **Distinct variants** | Nearby formulations that require another technology, measure, or canonical leaf. |
| **Domain** | Positivity, direction, coefficient, and comparability requirements. |
| **Failures** | Infeasibility, degeneracy, identification, and interpretation failures that software must expose. |
| **Solver form** | The intended computational form, not a guarantee that every variant shares one programme. |
| **Defining source** | Original or authoritative source that fixes the record. |
| **Evidence status** | `primary-checked`, `review-supported`, or `registry-provisional`. |
| **Oracle** | Current numerical-verification state using the review-programme vocabulary: `not located`, `candidate`, `analytically derived`, `reproduced`, or `cross-implemented`. Repository property evidence is stated separately, and analytical derivation does not claim a published-data reproduction. |
| **Package recipe** | Canonical components or method ID expected in DEAPack. |
| **Book location** | One audited status: active core placement, documentation/source review only, or evidence-deferred candidate. Only an exact path in `book/index.md` establishes active placement. |

`primary-checked` means that the defining source has been checked far enough
to identify the production account, measure, native result, and major domain
conditions. It is not a claim that every theorem or empirical table has been
reproduced. `review-supported` is sufficient for inclusion in the method
universe but not for a public executable preset. `registry-provisional`
requires a fresh primary-source audit before implementation.

The oracle labels in this review are deliberately conservative. The current
environmental implementation has synthetic, property, and failure-case tests,
and selected core leaves now have claim-scoped analytical and independently
compiled programmes. The repository still does not claim a published
numerical reproduction or an independent result for every environmental leaf.

## 1. Choosing the production account

### 1.1 Can pollution be reduced without modeling an additional sacrifice?

Strong disposal is sometimes a defensible simplification when all relevant
control resources and treatment activities are already among the inputs. It
is a much stronger claim when abatement is invisible in the data. The
empirical constraint on the bad output must therefore be read together with
the declared data roles; an inequality by itself does not explain why a
cleaner plan is attainable.

| Evidence field | Record |
|---|---|
| **Economic question** | How much service expansion, resource saving, or residual reduction is feasible if reducing the unwanted outcome does not require an additional unobserved sacrifice? |
| **Technology / estimator** | Convex or non-convex joint-production technology with desirable and undesirable outputs recorded separately and strong disposal explicitly selected. Null jointness is an independent restriction. |
| **Measure** | None at the technology level; commonly composed with an environmental DDF or a separable undesirable-output SBM. |
| **RTS** | CRS, VRS, NIRS, or NDRS only when the corresponding envelopment restrictions are stated. RTS is not implied by disposal. |
| **Data / time** | Cross-sectional or panel observations with inputs, desirable outputs, and physical residuals identified; panel work also needs a named reference policy. |
| **Native score** | No technology-level score. The composed measure retains its own native distance or efficiency value. |
| **Exact aliases** | None. “Free disposal,” “strong disposal,” and “natural disposal” are not treated as unconditional aliases because their use in the literature is not uniform. |
| **Distinct variants** | Weak disposal; costly disposal; bad-as-input transformations; by-production; material balance; natural and managerial disposability strategies. |
| **Domain** | Comparable DMUs and physically meaningful bad-output quantities. A bad outcome is not identified by a negative sign or by an unfavorable label alone. |
| **Failures** | Omitted abatement inputs can make attainable pollution reductions implausibly cheap. Zero or negative values can invalidate a fractional measure placed on the technology. Unsupported null-jointness claims can change the frontier. |
| **Solver form** | Sparse LP for a convex envelopment technology; direct dominance or mixed-integer machinery only if a separately declared non-convex estimator requires it. |
| **Defining source** | The environmental taxonomy is reviewed by [Scheel (2001)](https://doi.org/10.1016/S0377-2217(00)00160-0) and [Dakpo, Jeanneaux, and Latruffe (2016)](https://doi.org/10.1016/j.ejor.2015.07.024). |
| **Evidence status** | `review-supported` at the technology level; the public strong-disposal environmental DDF composition is `primary-checked` and has the bounded numerical evidence described next. |
| **Oracle** | `analytically derived` for the public strong-disposal DDF on exact synthetic accounts: an independently assembled dense phase-one programme covers CRS, VRS, NIRS, and NDRS under one fixed joint direction, while a second exact VRS account certifies the row-scaled bad-output slack and target identity. This is not a universal technology-level oracle or a published-data reproduction. See `specs/oracles/environmental-ddf-core-disposal-policies-analytical.md`. |
| **Package recipe** | `environmental.joint_production.envelopment` + `environmental.disposal.strong` + a named measure. |
| **Book location** | **Active core placement:** `book/chapters/03-environmental/06-undesirable-outputs-ddf.md` and `book/chapters/03-environmental/07-undesirable-output-sbm.md`; specialized constructions remain in package documentation. |

### 1.2 Does pollution control proportionally restrict the represented activity?

Weak disposability states an economic relation between desirable production
and residual reduction; it is not one universal equality constraint. The
early joint-production construction applies a common contraction to the
represented activity. Later convex formulations allow observed activities
to carry different abatement intensities. Those technologies can select
different benchmarks even when they use the same direction and RTS label.

| Evidence field | Record |
|---|---|
| **Economic question** | If cleaner operation requires curtailment or abatement, which combinations of desirable output and residual reduction remain attainable? |
| **Technology / estimator** | Source-qualified weak-disposal technology: either a single common abatement factor or activity-specific factors. Pollutant-selective disposal and null jointness are separate axes. |
| **Measure** | None at the technology level; environmental DDF, hyperbolic, radial, and non-radial measures are compatible only where the selected empirical construction proves it. |
| **RTS** | The Chung--Färe--Grosskopf common-factor linear construction is CRS. Kuosmanen's activity-specific convex linearization is VRS with $\mathbf1^\top(\mu+\tau)=1$. “Weak disposal under VRS” is not identified until those restrictions are written. |
| **Data / time** | Inputs, desirable outputs, and one or more physical residuals; cross-section or a declared panel reference. Activity-specific models require enough reference activities to identify heterogeneous abatement. |
| **Native score** | No technology-level score. A common abatement factor, if reported, is a technology parameter and not automatically an efficiency score. |
| **Exact aliases** | None between the single-factor and activity-specific constructions. A bad-output equality can implement part of a named construction but is not itself an exact alias for weak disposability. |
| **Distinct variants** | Common-factor weak disposal; activity-specific weak disposal; pollutant-specific selective disposal; Kuosmanen convex technology; generalized/exponential weak disposal over a piecewise Cobb--Douglas environmental technology; non-convex variants; strong or costly disposal. |
| **Domain** | Nonnegative activity quantities, declared output signs, and a fully specified convexification rule. Null jointness must be empirically meaningful rather than switched on by default. |
| **Failures** | A common factor can impose uniform abatement that the industry does not possess. Activity-specific formulations can be weakly identified. Equality-only implementations may be mislabeled. Infeasibility can arise from directions inconsistent with the selected technology. |
| **Solver form** | Source-specific LP or transformed LP where available. A formulation that leaves products of intensity and abatement variables unresolved requires a documented reformulation or bounded scalar search, not an ad hoc linear approximation. |
| **Defining source** | [Chung, Färe, and Grosskopf (1997)](https://doi.org/10.1006/jema.1997.0146), read with Chung and Färe's [1995 working-paper equation (2.14)](https://econwpa.ub.uni-muenchen.de/econ-wp/mic/papers/9511/9511002.pdf) for the fixed-input programme; [Kuosmanen (2005)](https://doi.org/10.1111/j.1467-8276.2005.00788.x); [Roshdi et al. (2018)](https://doi.org/10.1016/j.ejor.2017.10.033) for generalized weak disposal and the piecewise Cobb--Douglas technology; taxonomy and computational distinctions in [Pham and Zelenyuk (2019)](https://doi.org/10.1016/j.ejor.2018.09.019). |
| **Evidence status** | `primary-checked` and implemented for the CRS common-factor and VRS activity-specific constructions. The fixed-input CFG output preset is source-closed subject to the edition note below. Generalized and network extensions remain separate source-qualified records. |
| **Oracle** | `analytically derived` in three separate claim scopes. The fixed-input CFG output preset has exact pooled and old-only reference results, independent dense LP compilation, unit invariance, and execution accounting. The generic CRS common-factor DDF additionally has an exact, independently compiled non-CFG direction with resource contraction. The activity-specific VRS DDF has an exact three-activity primal--dual certificate, an independently assembled dense compiler for every fixture activity, and a public target check. None is a published empirical reproduction, and no certificate is inherited by another technology, direction policy, or generalized weak-disposal leaf. See `specs/oracles/cfg-environmental-ddf-analytical.md`, `specs/oracles/environmental-ddf-core-disposal-policies-analytical.md`, and `specs/oracles/activity-specific-weak-disposal-analytical.md`. |
| **Package recipe** | `environmental.weak_disposal.common_factor.crs.chung_fare_grosskopf_1997` + (`environmental.ddf.weak_disposal.common_factor` or source preset `environmental.ddf.output.chung_fare_grosskopf_1997`); or `environmental.weak_disposal.activity_specific.vrs.kuosmanen_2005` + `environmental.ddf.weak_disposal.activity_specific`. Generalized weak disposal remains the research-only `environmental.weak_disposal.generalized_piecewise_cobb_douglas.roshdi_etal_2018`. Every composition retains independent `null_jointness`, reference, and measure fields. |
| **Book location** | **Active core placement:** `book/chapters/03-environmental/06-undesirable-outputs-ddf.md`; source-specific technology details remain in package documentation. |

Compatibility boundary: the legacy selector `weak` resolves only to
`environmental.formulation.bad_output_directional_equality`. It is not a
complete common-factor or activity-specific weak-disposal technology and must
not be reported as one. It emits `FutureWarning`, preserves the old numerical
programme, and records `bad_output_disposability=not_identified` plus
`compatibility_alias=weak`. The two implemented source technologies are
separate leaves rather than aliases or silent migrations.

Source-edition boundary: the 1997 journal article's output set $P(x)$ and
signed direction $g=(y,-b)$ hold inputs fixed, but its printed equation
(3.14) places $(1-\beta)x$ in the input constraint. Chung and Färe's 1995
working-paper equation (2.14) prints $X\lambda\leq x$, which is consistent
with the definition and surrounding economic account. DEAPack freezes this
fixed-input programme. The review records the inconsistency but does not
claim that a formal publisher erratum exists.

### 1.3 Are desirable products and residual generation governed by different processes?

By-production treats conventional production and residual generation as
connected but analytically distinct subtechnologies. Its purpose is not to
create “two frontiers” for their own sake. It identifies pollution-generating
inputs, preserves costly disposal in the residual process, and takes the
intersection of plans admitted by both accounts.

| Evidence field | Record |
|---|---|
| **Economic question** | How well does a firm perform when valued-output production and residual generation are represented by different, connected processes? |
| **Technology / estimator** | Intersection of an intended-production technology and a residual-generation technology, with pollution-generating inputs, costly-disposal inequalities, and source-qualified coupling or dependence rules. |
| **Measure** | The conventional DDF applied to by-production, which Murty--Russell--Levkoff use to diagnose weak indication and direction sensitivity, or their distinct proposed FGL-style productive/environmental component account. |
| **RTS** | The source DDF/FGL illustration uses CRS in both subtechnologies. Configurable VRS/NIRS/NDRS paths are package extensions and are declared separately for each relation; a single system RTS label must not conceal inconsistent component scaling. |
| **Data / time** | Inputs partitioned by their production and residual-generation roles, desirable outputs, and bad outputs; currently static or repeated under a named panel reference. An explicit treatment or abatement input requires a separate source-qualified technology. |
| **Native score** | DDF leaf: the minimum of two maximum feasible component steps along one fixed source direction, where a larger distance means more unrealized improvement potential rather than better current performance. `1/(1+\beta)` is a package display transform only. FGL-style leaf: native productive and environmental component efficiencies, for which larger values mean better performance and one denotes component efficiency on the standard positive domain, plus their declared aggregation. Neither is silently converted to a Tone SBM score. |
| **Exact aliases** | None. “By-production DDF” and “FGL efficiency under by-production” share a technology family but not a native measure. |
| **Distinct variants** | Classical independent intensity systems; source-qualified coupled/dependent technologies; factorial treatment systems; material-balance technologies; ordinary joint-production DDF. |
| **Domain** | Pollution-generating inputs must be declared. Every returned target must be feasible in both subtechnologies. Directions and component normalizers require valid nonzero scales. |
| **Failures** | Independently selected component peers can imply an economically incoherent joint benchmark unless the chosen source permits it. Collapsing the subtechnology intensities can also change the technology. Missing pollution-generating input roles makes the residual account unidentified. |
| **Solver form** | Sparse block LP for directional forms; multiple LPs or source-specific non-radial programmes for component analysis. The compiler may share matrix blocks but must retain both intensity systems and any coupling constraints. |
| **Defining source** | [Murty, Russell, and Levkoff (2012)](https://doi.org/10.1016/j.jeem.2012.02.005); review and computational context in [Dakpo, Jeanneaux, and Latruffe (2016)](https://doi.org/10.1016/j.ejor.2015.07.024). |
| **Evidence status** | `primary-checked` for the classical production account; later coupled variants remain source-qualified leaves. |
| **Oracle** | `by_production_component_bottleneck` is a neutral project case. BP-DDF is checked against an independently compiled CRS programme, while two separately compiled scalar CRS programmes verify the FGL component accounts, targets, and peer semantics. The defining equations and paper citation remain; its numerical example is not redistributed. |
| **Package recipe** | `environmental.by_production` + (`environmental.by_production.ddf` or `environmental.by_production.fgl`) + explicit `coupling_policy`. |
| **Book location** | **Active core placement:** the transferable by-production account is consolidated in `book/chapters/03-environmental/06-undesirable-outputs-ddf.md`; FGL and coupling variants remain in package documentation. |

The implementation rule is therefore:

> Separate intensity systems are the classical default and must never be
> silently collapsed. A source that intentionally couples them defines a
> different technology leaf rather than an undocumented optimization shortcut.

### 1.4 Does physical conservation identify where the residual comes from?

Material-balance approaches use information that ordinary joint-production
DEA omits. Their coefficients can represent pollutant content in fuels,
retention in valued outputs, measured residual release, or treatment. That
additional accounting can be decisive, but the three main uses of material
information answer different questions.

| Evidence field | Record |
|---|---|
| **Economic question** | Can the producer reduce the inflow of pollutant-bearing material, or reduce residual release subject to a credible physical conservation account? |
| **Technology / estimator** | One of three named accounts: Coelli-style minimum material inflow for a required output plan; coefficient-aware weak-$G$ material conservation; or a factorial/multi-equation production and treatment system. |
| **Measure** | Material-input technical and allocative efficiency for the Coelli leaf; a separately selected directional, radial, or economic measure for conservation and treatment technologies. |
| **RTS** | The source-native Coelli programmes cover CRS and VRS; the working paper obtains VRS by adding the convexity constraint to both LPs. Conservation equations do not themselves determine returns to scale, and treatment processes may have their own RTS. |
| **Data / time** | The certified Coelli leaf uses a self-inclusive cross-section of ordinary nonnegative inputs and desirable outputs, one common vector of known nonnegative physical material coefficients, positive observed material inflow, and no observed bad-output or explicit abatement account. Prices are **not** required for EAE: “allocative” here means the input mix relative to physical material contents. |
| **Native score** | Coelli leaf: higher-is-better input-radial technical efficiency $TE$, material-inflow environmental efficiency $EE$, and environmental allocative efficiency $EAE=EE/TE$, with $EE=TE\times EAE$. The desirable-output commitment is held fixed. Other production accounts retain their attached measure's native score. |
| **Exact aliases** | None among material-inflow efficiency, weak-$G$ technology, by-production, or multi-equation treatment. |
| **Distinct variants** | Multiple-material aggregation, heterogeneous or estimated coefficients, panel/external-reference comparison, stock accumulation, end-of-pipe treatment, by-production, and mass-balance inequalities reflecting measurement loss are distinct evidence claims. |
| **Domain** | Coefficients must have physical units and provenance, observed inflow must be positive, and the fixed desirable-output commitment must be feasible. Prices, damage weights, actual emissions, and welfare effects cannot be inferred from physical coefficients. Target and peer systems may be nonunique. |
| **Failures** | Accounting residuals, inventory changes, or unmeasured discharges can make a physical interpretation unreliable even when the LP is feasible. Estimated coefficients can create false precision. A material-input ratio is neither a Pareto--Koopmans certificate nor evidence of environmental damage, welfare, causality, or realized abatement. |
| **Solver form** | Two sparse envelopment LPs per observation: source equation (23) for input-radial $TE$ and equation (24) for minimum material inflow, followed by equations (25)--(26) for $EE$ and $EAE$. VRS adds the source convexity constraint to both LPs. |
| **Defining source** | [Coelli, Lauwers, and Van Huylenbroeck (2007)](https://doi.org/10.1007/s11123-007-0052-8), equation-checked against [CEPA Working Paper 06/2005](https://economics.uq.edu.au/files/5310/WP062005.pdf); [Førsund (2009)](https://doi.org/10.1561/101.00000021); [Rødseth (2016)](https://doi.org/10.1016/j.ejor.2015.10.061). |
| **Evidence status** | `primary-checked`; an independent exact synthetic certificate covers the source-native Coelli CRS/VRS programmes and decomposition. The wider weak-$G$/multi-equation atlas remains `review-supported`. |
| **Oracle** | `analytically derived`; an independently compiled fixture checks exact $TE$, $EE$, $EAE$, $EE=TE\times EAE$, fixed-output material targets, and the declared nonuniqueness boundary under CRS and VRS. The source's unit-level 183-farm observations are not supplied, so no farm-level reproduction is claimed. |
| **Package recipe** | `environmental.material_inflow.coelli2007`, `environmental.weak_g_balance`, or `environmental.factorial_multiequation`; never one generic `material_balance=True` switch. |
| **Book location** | **Documentation/source review only.** Material-coefficient and conservation specializations have no current handbook placement. |

The current source-native certificate is intentionally narrower than every
source and software option. The source discusses weighted multiple pollutants
in equations (18)--(21), but their independent validation is not yet closed.
NIRS/NDRS, a multi-material aggregate, heterogeneous or
estimated coefficients, panel/custom/external-reference source equivalence,
reproduction of the 183-farm application, and welfare, causal, damage, or
actual-emission claims are all `deferred_to_next_version`. Existing package
extensions may retain property tests, but they do not inherit this
literature-equivalence claim.

### 1.5 Where does the environmental burden sit in a production graph?

Environmental network and dynamic models require one more distinction before
a score is chosen. An unwanted quantity can leave the modeled organization
now, move between two of its processes, or remain as an obligation that
constrains later operation. Those are different economic roles even when the
same physical pollutant is involved.

| Graph role | Economic interpretation | Required accounting |
|---|---|---|
| **External terminal bad** | A residual, delay, injury, or other unwanted service outcome leaves the modeled system in the current period. | A terminal output balance, a declared disposal technology, and a measure that states who may reduce it and at what sacrifice. |
| **Internal link** | A quantity produced by one process is used, treated, stored, or otherwise received by another process inside the system boundary. | Source and recipient incidence, link conservation or loss, controllability, and one coordinated target. Desirability does not determine the direction of physical flow. |
| **Carry-over state** | A stock, liability, capacity, inventory, or environmental burden survives into a later period and changes future opportunities. | A transition or continuity rule, lag and decay, managerial control, and initial/terminal boundary treatment. A harmful state is not an external bad output merely because both are undesirable. |

The canonical schema therefore records five orthogonal axes:

| Axis | Minimum vocabulary | Boundary rule |
|---|---|---|
| `role` | `external_input`, `external_terminal_output`, `internal_link`, `carryover_state` | Role fixes where a quantity enters or leaves the production graph; it is not inferred from its name or sign. |
| `desirability` | `good`, `bad`, `neutral` | Desirability records the economic effect of more of the quantity, not whether it is an input, output, link, or state. |
| `disposal` | `strong`, `weak_common`, `weak_activity_specific`, `selective`, or a source-qualified costly-disposal rule | Disposal changes the attainable set. It is not an objective flag. |
| `physical_account` | `joint_production`, `by_production`, `joint_input_parallel`, `material_balance_treatment` | The account states how valued production, residual generation, and treatment are connected. |
| `time` | `static`, `dynamic` | Dynamic requires an explicit state, continuity, or transition relationship; repeated static fitting is not enough. |

Link and state `control` and `balance` remain additional attributes rather
than being overloaded into `disposal`. A quantity may occupy more than one
role only through an explicit split or identity. For example, primary
pollution can be an internal input to treatment while untreated discharge is
a terminal bad; installed capacity can be a current input and an
interperiod state. Software must not infer those identities from column names.

[Tone and Tsutsui's dynamic network SBM
(2014)](https://doi.org/10.1016/j.omega.2013.04.002) is the structural
prerequisite for combining within-period process links and between-period
carry-overs. It is not itself a universal environmental technology: terminal
bad outputs, process-specific disposal, joint inputs, and material-flow
identities still require the environmental components below.

#### 1.5.1 Activity-specific weak disposal in a general network

| Evidence field | Record |
|---|---|
| **Economic question** | How much external input could a multi-process organization save while preserving its required final and internal desirable and undesirable products when different reference activities may operate at different abatement intensities? |
| **Technology / estimator** | General network envelopment with one intensity system per process and activity-specific weak disposal. The source linearization separates active and abated portions through activity-level variables while coordinating source and recipient quantities across links. |
| **Measure** | Source input-oriented radial contraction $h$; the environmental technology and the radial measure remain separate registry fields. |
| **RTS** | VRS in the primary audited programme. CRS, NIRS, and NDRS are tested under their declared process-level intensity restrictions on neutral project cases; none is presented as a published numerical reproduction. |
| **Data / time** | Static process-level inputs plus desirable and undesirable products, each partitioned into final and internally used quantities with a declared process incidence. For every producer process by desirable/undesirable product pair, the final part must be positive for at least one DMU; support is checked across DMUs within that pair and is not pooled across producers. |
| **Native score** | Source input-efficiency factor $h$, with one denoting radial input efficiency under the maintained network technology and values below one denoting feasible proportional input saving. |
| **Exact aliases** | “Bad” and “undesirable” are vocabulary aliases only after the same variable role is fixed. The activity-specific technology is not an alias for a common-factor weak-disposal network. |
| **Distinct variants** | Common-factor weak disposal; strong or selective disposal; black-box environmental radial DEA; network DDF or network SBM placed on a different technology. |
| **Domain** | Nonnegative physical quantities, declared process incidence, and consistent final/internal splits. Every internal target must satisfy the source-recipient account. |
| **Failures** | Replacing activity-specific abatement by one system factor changes the hull. Applying the abatement variables symmetrically to every source and recipient term also changes the published technology. Missing final/internal splits make the production account unidentified. |
| **Solver form** | Sparse LP after the source activity-specific linearization; process blocks and graph incidence are reusable, but a conventional network-SBM compiler is not the model. |
| **Defining source** | [Kalhor and Kazemi Matin (2018), “Performance evaluation of general network production processes with undesirable outputs: A DEA approach”](https://doi.org/10.1051/ro/2017022). |
| **Evidence status** | `primary-checked` for the corrected technology, input-radial VRS programme, source-described process-level CRS/NIRS/NDRS restrictions, and common-factor boundary. The DDF leaf and Spanish-airport data/result closure are `deferred_to_next_version`. |
| **Oracle** | An independent dense compiler for equations (3.2)--(3.4) checks `environmental_recovery_chain` and `environmental_circular_chain`, including VRS/CRS scores, process accounts, and target reconstruction. NIRS/NDRS parity is package verification; no source numerical table is redistributed. |
| **Package recipe** | Implemented/public as `network.environmental.weak_activity_specific.kalhor_kazemi_matin_2018`, with explicit environmental product accounts and a source-specific sparse compiler over the general process graph. |
| **Book location** | **Documentation/source review only.** This environmental-network composition has no independent placement in the current handbook. |

#### 1.5.2 Joint-input parallel production and pollution generation

| Evidence field | Record |
|---|---|
| **Economic question** | How efficiently does an organization produce valued output and limit residual generation when the same pollution-generating resource is physically involved in both accounts? |
| **Technology / estimator** | Two parallel subtechnologies: intended production uses non-pollution-generating and pollution-generating inputs to produce desirable outputs, while pollution generation uses the same pollution-generating inputs to produce bad outputs. The target for each joint input is identical across the two processes. |
| **Measure** | Source non-oriented, units-invariant network SBM with system and process performance accounts. |
| **RTS** | Process convexity and scale restrictions must be taken from the frozen source equations. This review does not infer a general CRS/VRS family from the NSBM label. |
| **Data / time** | Static non-pollution-generating inputs, jointly consumed pollution-generating inputs, desirable outputs, and physical bad outputs. |
| **Native score** | Source higher-is-better non-oriented network-SBM system and process efficiencies, with one representing no measured slack inefficiency under the maintained joint-input technology. |
| **Exact aliases** | None with classical independent-intensity by-production, ordinary parallel network DEA, or shared-resource allocation. A joint input is used in both physical accounts; it is neither duplicated without constraint nor split endogenously between them. |
| **Distinct variants** | Classical by-production with separate component plans; allocated shared inputs; ordinary joint-production SBM; explicit end-of-pipe treatment; directional by-production measures. |
| **Domain** | Pollution-generating inputs must be identified economically and measured in identical units in both subtechnologies. Returned component targets must obey the joint-input identity. |
| **Failures** | Allowing each subtechnology to choose a different pollution-generating-input target removes the defining coupling. Treating the joint input as a divisible resource pool answers a different allocation question. |
| **Solver form** | Source linear programme with parallel process blocks, an identity-coupling row for each joint input, and network-SBM normalization. |
| **Defining source** | [Lozano (2015), “A joint-inputs Network DEA approach to production and pollution-generating technologies”](https://doi.org/10.1016/j.eswa.2015.06.023). |
| **Evidence status** | `primary-checked` for the joint-input production account, measure, and non-alias boundary; `registry-provisional` for the exact executable RTS/equation fixture. |
| **Oracle** | `candidate`; the primary article reports applications to 92 coal-fired power plants and 23 EU/OECD countries, but a complete source dataset suitable for a certified numerical oracle has not been located. |
| **Package recipe** | `environmental.by_production.joint_input_parallel` + `network.environmental.joint_input_sbm.lozano_2015`; requires an explicit joint-input identity rather than an ordinary directed link. |
| **Book location** | **Documentation/source review only.** This joint-input network specialization has no independent handbook placement. |

#### 1.5.3 Material-balance production and end-of-pipe treatment

| Evidence field | Record |
|---|---|
| **Economic question** | Is poor environmental performance attributable to the way valued output is produced, to the way primary pollution is treated, or to both? |
| **Technology / estimator** | A serial physical account. Intended production and externally justified material coefficients determine primary pollution; that flow enters an end-of-pipe abatement process using its own resources; final discharge equals primary pollution less the treated amount, subject to the source balance equations. |
| **Measure** | Source environmental-efficiency programme with production- and abatement-efficiency decomposition; it is not a generic network-SBM score. |
| **RTS** | CRS and VRS cases are analyzed in the source. Production and treatment scale assumptions must remain visible rather than being replaced by one undocumented system switch. |
| **Data / time** | Static production inputs and desirable output, pollutant-content or emissions coefficients, primary pollution, treatment inputs/resources, abated quantity, and final discharge within one consistent physical boundary. |
| **Native score** | Source higher-is-better environmental, production, and abatement efficiency values, with one denoting efficiency for the corresponding account. Component interpretation is retained with the source decomposition. |
| **Exact aliases** | None with Coelli material-inflow efficiency, weak-$G$ conservation, weak disposal, by-production, or a generic undesirable-link network. |
| **Distinct variants** | Treatment technologies without a material balance; stock-pollution dynamics; multiple pollutants and treatment routes; mass-balance inequalities for measurement loss; by-production accounts without explicit end-of-pipe treatment. |
| **Domain** | Coefficients require physical units, provenance, and a common system boundary. Primary pollution, treated amount, and final discharge must satisfy the material identity after accounting for any declared loss or retention. |
| **Failures** | An omitted treatment input makes abatement appear costless. Incompatible time or mass units create artificial infeasibility. Replacing the coefficient balance by a freely chosen intermediate destroys the physical interpretation. |
| **Solver form** | Sparse coefficient-aware network LPs and source decomposition solves. This requires a material-flow row generator and treatment-process compiler in addition to ordinary graph incidence. |
| **Defining source** | [Hampf (2014), “Separating Environmental Efficiency into Production and Abatement Efficiency—A Nonparametric Model with Application to U.S. Power Plants”](https://doi.org/10.1007/s11123-013-0357-8); [open working-paper record](https://doi.org/10.26083/tuprints-00004722). |
| **Evidence status** | `primary-checked` for the physical production/treatment account and efficiency decomposition; a complete executable fixture remains to be frozen. |
| **Oracle** | `candidate`; the primary study reports plant-level and aggregate results for 23 U.S. power plants, including a CRS mean environmental efficiency of 0.2739, but the raw application data have not been certified as a repository oracle. |
| **Package recipe** | `environmental.material_balance_treatment` + `network.environmental.material_balance_treatment.hampf_2014`; requires coefficient balances and an explicit treatment node. |
| **Book location** | **Documentation/source review only.** This material-balance treatment specialization has no current handbook placement. |

#### 1.5.4 Dynamic undesirable production as a source-qualified leaf

| Evidence field | Record |
|---|---|
| **Economic question** | How does electricity-sector environmental performance evolve when fossil and non-fossil capacity constrain both current generation and later production opportunities? |
| **Technology / estimator** | Multi-period electricity technology with current inputs and outputs, a source-specific proportional weak-disposal relation between fossil generation and CO2, and installed-capacity quantities that also link adjacent periods. |
| **Measure** | The source maximizes an unnormalized sum of output and CO2 slacks and then computes normalized period scores ex post; it is not Tone--Tsutsui dynamic SBM. |
| **RTS** | CRS in the main source model; VRS is used separately for a Banker-style comparison. |
| **Data / time** | Country panel with GDP, fossil and non-fossil installed capacity, fossil and non-fossil electricity generation, and CO2 emissions over a common study horizon. Capacity has both a current production role and an explicitly linked temporal role. |
| **Native score** | Source period efficiency is an inverse transformation of three normalized slacks and the global value is the arithmetic mean of period efficiencies. The optimization itself uses raw, not normalized, slacks. |
| **Exact aliases** | None with dynamic SBM, dynamic network SBM, a bad carry-over model, or repeated static environmental DEA. Current-period CO2 is a terminal bad; installed capacity is the temporal link. |
| **Distinct variants** | Normalized additive dynamic measures; dynamic environmental SBM; activity-specific weak disposal; harmful pollution-stock carry-overs; process-by-period environmental networks. |
| **Domain** | Complete comparable trajectories and consistent measurement units. The source abatement factor bounds, indexing, and link equations must be frozen before an executable contract is declared. |
| **Failures** | Because raw slacks enter the objective, changing physical units can change the optimizer. The published abatement-factor statement and at least one index expression require equation-level resolution. Missing source panel observations prevent an exact application replay. |
| **Solver form** | Potential sparse multi-period LP only after the source equations, abatement-factor domain, and scaling policy are frozen; no implementation is asserted by this review. |
| **Defining source** | [Cuadros, Rodríguez, and Contreras (2020), “Dynamic Data Envelopment Analysis Model Involving Undesirable Outputs in the Electricity Power Generation Sector”](https://doi.org/10.3390/en13246624). |
| **Evidence status** | `primary-checked` for the economic roles and reported accounting; `registry-provisional` for an executable formulation because the source-freeze and unit-sensitivity audit remain open. |
| **Oracle** | `candidate`; the article reports period and global efficiencies for 24 countries over 2000--2016, but the complete raw panel and an ambiguity-free executable specification have not been certified. |
| **Package recipe** | `dynamic.environmental.additive_weak_disposal.cuadros_etal_2020`; retain the source raw-additive objective and disclose unit sensitivity rather than relabeling it as canonical dynamic environmental SBM. |
| **Book location** | **Documentation/source review only.** This source-qualified dynamic environmental leaf has no current handbook placement. |

#### 1.5.5 Dynamic by-production with adjustment costs

| Evidence field | Record |
|---|---|
| **Economic question** | How should pollution-adjusted inefficiency be assessed when today's investment and adjustment decisions jointly affect future intended production and residual generation? |
| **Technology / estimator** | Dakpo--Oude Lansink's dynamic by-production construction with intended and residual subtechnologies, capital/investment transition, and adjustment-cost terms. |
| **Measure** | Source pollution-adjusted dynamic inefficiency account; its exact normalization and reconstruction must be frozen before implementation. |
| **RTS** | Source-specific component and intertemporal scale restrictions; no RTS inheritance from static by-production or dynamic SBM is assumed. |
| **Data / time** | Panel with pollution-generating inputs, investment/quasi-fixed capital, adjustment costs, desirable outputs, bad outputs, and consistent initial/terminal state policy. |
| **Native score** | Source-native dynamic pollution-adjusted inefficiency and its component/state accounts; no conversion to a Tone--Tsutsui slack score is implied. |
| **Exact aliases** | None with repeated static by-production, Tone--Tsutsui harmful carry-over, or Cuadros--Rodríguez--Contreras weak-disposal electricity DEA. |
| **Distinct variants** | Static by-production; dynamic cost/allocative inefficiency; dynamic material-balance treatment; bad-stock carry-over; dynamic network environmental SBM. |
| **Domain** | Every intended/residual plan must satisfy the intertemporal transition and adjustment-cost account; state and terminal policies are explicit. |
| **Failures** | Fitting each year independently, treating current emissions as the state without the source transition, dropping investment/adjustment costs, or merging component intensities without proof. |
| **Solver form** | Planned source-specific intertemporal block programme; shared by-production or dynamic matrix infrastructure does not certify the composed model. |
| **Defining source** | [Dakpo and Oude Lansink (2019)](https://doi.org/10.1016/j.ejor.2018.12.040). |
| **Evidence status** | `primary-checked` for the mechanism boundary; equation, result-contract, and oracle freezes remain planned. |
| **Oracle** | `not located`. |
| **Package recipe** | Planned/evidence candidate *dynamic.environmental.by_production.adjustment_cost.dakpo_oude_lansink_2019*; axes $G,D,T,M$; Level D relative to the three non-aliases above. No implementation is claimed. |
| **Book location** | **Documentation/source review only.** This dynamic by-production specialization has no current handbook placement. |

### 1.6 Is part of a residual freely reducible before further abatement becomes costly?

Semi-disposability represents a two-region environmental account: some
residual reduction may be attainable within current operating capability,
whereas reduction beyond that region requires a contraction of desirable
production or another modeled sacrifice. This is not the same as assigning
one pollutant strong disposal and another weak disposal. It also remains an
active methodological lineage: the refined 2026 formulation argues that the
2017 production set does not fully encode the freely disposable portion that
motivated the original concept.

| Evidence field | Record |
|---|---|
| **Economic question** | How much of each undesirable output can be reduced within current operating capability, and when does additional reduction require a sacrifice in desirable production? |
| **Technology / estimator** | Chen--Wang--Lai attach a pollutant-specific non-disposal degree to a semi-disposable production account. Chu et al. distinguish semi-disposability from a bounded inefficiency axiom and construct a refined CRS/VRS production set. These are different technology leaves until an exact correspondence is proved. |
| **Measure** | No technology-level score. Each source attaches its own environmental-efficiency programme; a public measure must be frozen separately from the disposal axiom. |
| **RTS** | CRS and VRS are treated in both lineages through source-specific constructions. The same non-disposal degree does not make their attainable sets identical. |
| **Data / time** | Static nonnegative inputs, desirable outputs, undesirable outputs, and a documented non-disposal degree or estimation rule for every affected pollutant. The interval-degree extension is a separate uncertainty specification. |
| **Native score** | No technology-level efficiency value. The non-disposal degree is a production parameter, not an efficiency score or policy preference. Source-specific efficiency and decomposition values retain their own direction and bounds. |
| **Exact aliases** | None between semi-disposability, selective strong/weak disposal, generalized weak disposal, ordinary strong disposal, or ordinary weak disposal. No exact alias is registered between the 2017 and refined 2026 production sets. |
| **Distinct variants** | Chen--Wang--Lai semi-disposability and its reference-point comparison rule; interval non-disposal degrees; Chu et al.'s refined semi-disposability plus bounded inefficiency axiom; pollutant-selective strong/weak disposal; generalized/exponential weak disposal. |
| **Domain** | The economic meaning, admissible range, and provenance of every non-disposal degree must be stated. A degree estimated from the same comparison sample is model-generated information, not an observed engineering limit. |
| **Failures** | Treating the degree as a management preference confuses technology with valuation. The 2026 critique shows that a plausible verbal axiom does not certify the 2017 finite-sample production set. An unconstrained inefficiency axiom can admit physically unbounded bad-output production. |
| **Solver form** | Source-specific mathematical programmes. No generic interpolation between strong- and weak-disposal LP rows is valid. Executable work remains gated on a complete equation freeze, monotonicity audit, and source numerical reproduction. |
| **Defining source** | [Chen, Wang, and Lai (2017)](https://doi.org/10.1016/j.ejor.2016.12.042); refined formulation and critique in [Chu et al. (2026)](https://doi.org/10.1016/j.ejor.2026.07.013). |
| **Evidence status** | `primary-checked` for the conceptual distinction and the explicit 2026 non-equivalence claim; `registry-provisional` and reader-facing research-only for executable leaves while the competing production sets and recent source are reconciled. |
| **Oracle** | `candidate`; both lineages report numerical examples, but neither has been reproduced as a frozen repository oracle. |
| **Package recipe** | Research-only `environmental.semi_disposal.chen_wang_lai_2017` and `environmental.semi_disposal.refined.chu_etal_2026`; never a scalar `disposability_mix` option on an ordinary environmental DDF. |
| **Book location** | **Documentation/source review only.** Graded-disposal variants remain source-review material, not an independent handbook family. |

## 2. Choosing the improvement programme

### 2.1 What joint operating counterfactual is being evaluated?

The directional distance function expresses an analyst-declared operating
counterfactual in the units supplied by its direction. For nonnegative
direction components,

$$
\sup_{\beta}\left\{\beta:
  \left(x-\beta g_x,\;y+\beta g_y,\;b-\beta g_b\right)\in T
\right\}
$$

asks how far a declared package of resource saving, service expansion, and
emissions reduction can be achieved. A direction such as $(0,y,b)$ is not
merely an “arrow”; it evaluates a counterfactual that preserves current inputs
while expanding desirable output and reducing residuals relative to their
observed scales. It becomes a policy or management commitment only when an
authorized institution adopts it.

| Evidence field | Record |
|---|---|
| **Economic question** | How much of a declared resource, service, and pollution-improvement programme is feasible under the maintained production account? |
| **Technology / estimator** | Any explicitly compatible joint-production, weak-disposal, by-production, material-flow, network, or dynamic technology; the technology is not identified by the DDF name. |
| **Measure** | Directional distance with signed roles and an economically interpretable direction vector. |
| **RTS** | Inherited from the selected technology and recorded in every task. |
| **Data / time** | Cross-section or panel. Directions combined over units or periods must have comparable economic units. |
| **Native score** | Directional distance $\beta$: a larger value means that the current plan has more unrealized improvement potential under the declared direction; zero normally denotes directional efficiency. A higher-is-better display requires a separately named transformation and never replaces native $\beta$. |
| **Exact aliases** | Input- or output-oriented Farrell models admit exact score transformations only for matching observation-scaled pure directions, signs, technology, RTS, reference set, and target policy. The historical Farrell score remains native to its own preset. |
| **Distinct variants** | Generalized path measures; hyperbolic measures; non-radial DDF; directional SBM; additive weighted gaps; Nerlovian price-normalized inefficiency. |
| **Domain** | Nonzero active direction components; dimensionally comparable direction construction; translation and unit properties checked for the chosen normalization. |
| **Failures** | Zero directions for all discretionary variables make the problem unidentified. DMU-specific or period-specific directions can make productivity components incomparable. A negative distance under an external or cross-period reference can be valid evidence that the selected technology cannot reproduce a newer clean-output plan; treating it as negative efficiency, a data error, or truncating it to zero destroys that information. |
| **Solver form** | LP for linear technology and linear path; compiled sparse technology with right-hand-side updates across DMUs. |
| **Defining source** | [Chambers, Chung, and Färe (1996)](https://doi.org/10.1006/jeth.1996.0096); environmental application in [Chung, Färe, and Grosskopf (1997)](https://doi.org/10.1006/jema.1997.0146), with the fixed-input source-edition boundary recorded above. |
| **Evidence status** | `primary-checked`; the fixed-input CFG output preset is source-closed and analytically certified, while other environmental DDF compositions retain their own evidence states. |
| **Oracle** | `analytically derived` for `environmental.ddf.output.chung_fare_grosskopf_1997`: the synthetic plans Old $(1,1,2)$ and New $(1,2,1)$ give pooled distances $(3/5,0)$ and an old-only New distance of $-3/5$. Independent dense LP compilation confirms scores, targets, missing convenience efficiency for the negative comparison, unit invariance, and solve/compile accounting. This is not a published numerical reproduction; the unavailable article application evidence is deferred to the next version. Other environmental DDF paths do not inherit this oracle. |
| **Package recipe** | Named technology + `environmental.ddf.joint_production` or `environmental.by_production.ddf` + explicit direction and reference. |
| **Book location** | **Active core placement:** `book/chapters/03-environmental/06-undesirable-outputs-ddf.md`; source-specific direction presets remain in package documentation. |

The exact negative result has a narrow managerial meaning. Old-only evidence
can represent New only by reducing its service from $2$ to $4/5$ and raising
its residual from $1$ to $8/5$, while using $4/5$ of the available resource.
It says the older technology cannot reproduce the newer service-and-pollution
combination; it is not an efficiency below zero or a solver failure. The raw
distance remains available and the convenience efficiency remains missing.

Changing a DDF reference policy only changes the evidence set for that
distance task. It does not construct the four-task source-qualified CFG
Malmquist--Luenberger operator, and a global distance is not Oh's distinct
global Malmquist--Luenberger operator. Alternative temporal compositions
without frozen defining sources, equations, economic interpretation, and
independent validation remain deferred to the next version.

### 2.2 Can fuel saving, service expansion, and carbon reduction proceed at different rates?

A manager may have more scope to improve generation efficiency than to
change the fuel mix, or more scope to reduce carbon intensity than to reduce
total fuel use. A component-specific directional measure represents those
unequal demonstrated opportunities instead of forcing every operating lever
to move by one common percentage. The economic content still comes from the
production account and the named direction; “non-radial” alone does not say
which changes are attainable or desirable.

| Evidence field | Record |
|---|---|
| **Economic question** | For comparable non-CHP electricity systems, how much fossil-energy saving, electricity expansion, and CO2 reduction has the reference population demonstrated when those opportunities may differ by component? |
| **Technology / estimator** | Zhou--Ang--Wang's one-input, one-electricity-output, one-CO2-output $T_1$ technology: CRS intensities, strong disposal of fossil input and electricity in the stated directions, a bad-output equality implementing the source common-factor weak-disposal account, and null jointness on the strictly positive source domain. |
| **Measure** | Source equation (7), maximizing a weighted sum of nonnegative component steps, with three immutable observed-value presets: energy $g=(-F,E,0)$, carbon $g=(0,E,-C)$, and integrated energy--carbon $g=(-F,E,-C)$. |
| **RTS** | CRS only; there is no intensity-sum row. |
| **Data / time** | One self-inclusive, homogeneous, strictly positive cross-section of non-CHP electricity systems. The source uses 2005 country data; custom references and temporal operators are outside the frozen claim. |
| **Native score** | Raw $D^{NR}=w^\top\beta$ is larger-is-more-unrealized-opportunity. Source performance indexes $EPI_1=(1-\beta_F)/(1+\beta_E)$, $CPI_1=(1-\beta_C)/(1+\beta_E)$, and $ECPI_1=[1-(\beta_F+\beta_C)/2]/(1+\beta_E)$ are higher-is-better on the maintained domain. Raw and transformed results remain separate. |
| **Exact aliases** | None with a radial DDF, weighted additive DEA, directional SBM, Tone's separable or non-separable undesirable-output SBM, or Zhou et al.'s earlier non-radial environmental DEA. Algebraically reusable rows do not establish method identity. |
| **Distinct variants** | Arbitrary component directions or weights; additional inputs/outputs/bads; the source $T_2$/CHP branch; VRS and other RTS; strong or activity-specific disposal; generalized weak disposal; panel productivity; and non-radial measures on by-production, network, or treatment technologies. |
| **Domain** | Exactly one finite positive $F$, $E$, and $C$ role; observed-value directions; source weights; nonnegative component steps and intensities; homogeneous non-CHP reference population. Coherent positive unit changes co-scale data and directions. |
| **Failures** | Inactive components must be fixed rather than left free. Component plans, targets, and peers can be nonunique even when the weighted objective is identified. A transformed index must not be labelled unique without an optimal-face check. The printed CHP equation (12) leaves $\beta_{2E}$ unconstrained and is unbounded as written. |
| **Solver form** | One sparse primary LP per organization and frozen source preset, reusing one immutable CRS reference block. Optional optimal-face diagnostics add two LPs per active component; the default leaves plan uniqueness explicitly unassessed rather than paying that cost silently. Component, target, residual, peer, and multiplicity accounts remain visible. |
| **Defining source** | [Zhou, Ang, and Wang (2012), “Energy and CO2 Emission Performance in Electricity Generation: A Non-radial Directional Distance Function Approach”](https://doi.org/10.1016/j.ejor.2012.04.022), equations (4) and (6)--(10), Appendix B.1, and Appendix C. |
| **Evidence status** | `implemented` and `primary-checked` for the narrow non-CHP source preset. Exact analytical values and independently assembled dense programmes agree with the public implementation. The generalized and CHP branches are `deferred_to_next_version`. |
| **Oracle** | `analytically derived`: for the positive reference A $(1,1,1)$, D $(3/2,1,4)$, O $(2,1,4)$ with O assessed, the energy preset gives $(\beta_F,\beta_E,D^{NR},EPI_1)=(0,3/5,3/10,5/8)$; carbon gives $(\beta_E,\beta_C,D^{NR},CPI_1)=(1,1/2,3/4,1/4)$; integrated gives $(\beta_F,\beta_E,\beta_C,D^{NR},ECPI_1)=(0,1,1/2,1/2,3/8)$. Exact derivation, stand-alone dense LP assembly, and public results agree. These are synthetic consequences, not published-country values. The complete 126-country data were not located, so no Appendix C or empirical reproduction is claimed. |
| **Package recipe** | Public preset ID `environmental.directional_nonradial.energy_carbon.zhou_ang_wang_2012_non_chp`; `ZhouAngWangNonCHPEnergyCarbonDEA(account=...)` requires exactly `energy`, `carbon`, or `integrated_energy_carbon` and exposes no custom direction/weight interface. |
| **Book location** | **Documentation/source review only.** This paper-specific account is not promoted into the handbook as an independent family. |

The source protocol and exact oracle are
[`zhou_ang_wang_2012_non_chp_energy_carbon.md`](../source_protocols/zhou_ang_wang_2012_non_chp_energy_carbon.md)
and
[`zhou_ang_wang_2012_non_chp_energy_carbon.md`](../oracles/zhou_ang_wang_2012_non_chp_energy_carbon.md),
respectively. The paper's weights normalize the represented input, good-output,
and bad-output blocks; they are not prices or damage weights. Exposing symbols
called `direction` and `weights` would create a broader method whose source and
oracle gate has not closed.

The $T_2$ branch is excluded rather than silently repaired. Equation (12) and
Appendix model (B.3) both use $\beta_{2H}$ in the electricity row, while
$\beta_{2E}$ retains a positive objective weight and no constraint. Although
equations (11) and (13)--(15) make the likely intended row apparent, no formal
erratum was located. The published CHP and 126-country results therefore do
not certify an inferred implementation.

### 2.3 Should improvements be proportional in percentage terms?

The environmental hyperbolic path contracts inputs and undesirable outputs
while expanding desirable outputs reciprocally. A representative form seeks
the smallest $\theta$ such that
$(\theta x,\theta^{-1}y,\theta b)$ is attainable. It therefore asks a
percentage-like balanced-growth question, not the additive operating-package
question posed by a DDF.

| Evidence field | Record |
|---|---|
| **Economic question** | By what common multiplicative factor can resource use and pollution fall while desirable production expands reciprocally? |
| **Technology / estimator** | A declared environmental production technology; classical applications compare technologies with different bad-output disposal assumptions. |
| **Measure** | One core hyperbolic performance measure where the path equation matches, composed with a source-qualified environmental technology/preset; generalized environmental graph paths remain separate measures. |
| **RTS** | Inherited from the technology; CRS does not make the hyperbolic path globally identical to an additive direction. |
| **Data / time** | Strictly positive variables that enter reciprocal scaling; static or used inside a separately defined temporal operator. |
| **Native score** | Source-native contraction factor, typically with unity denoting hyperbolic efficiency and smaller values indicating more unrealized joint improvement; the exact convention is stored per preset. |
| **Exact aliases** | The ordinary and environmental source lineages may reuse the same core $M$ only after their path equations and native transform are proved identical. Their whole studies are not aliases because $D/T$ differ. There is no general alias with additive environmental DDF. |
| **Distinct variants** | Input-fixed/output hyperbolic paths; generalized hyperbolic paths; environmental graph measures; radial DDF specializations. |
| **Domain** | Positive denominators and a monotone feasible path over a declared bounded search interval. |
| **Failures** | Zeros invalidate reciprocal scaling. Non-monotone or unbounded paths defeat generic scalar search. Reporting $1/\theta$, $1-\theta$, and $\theta$ without the native convention reverses interpretation. |
| **Solver form** | Safeguarded monotone scalar search with a compiled LP feasibility problem for linear technologies; a direct nonlinear backend is a separate implementation choice. |
| **Defining source** | [Färe et al. (1989)](https://doi.org/10.2307/1928055); computation and adaptability in [Färe, Margaritis, Rouse, and Roshdi (2016)](https://doi.org/10.1016/j.ejor.2016.03.045); broader environmental review in [Førsund (2009)](https://doi.org/10.1561/101.00000021). |
| **Evidence status** | `primary-checked` for the classical hyperbolic account; the shared-core design and generalized variants remain planned/`registry-provisional`. |
| **Oracle** | `not located`; no executable DEAPack leaf is currently registered. |
| **Package recipe** | Planned shared core `static.hyperbolic` $M$ + a source-retaining environmental preset with explicit $D/T$, path, and native-score convention. This is Level B/C reuse, not a Level-A alias or implementation claim. |
| **Book location** | **Documentation/source review only.** Environmental hyperbolic paths have no independent placement in the current handbook. |

### 2.4 Which resource, service, and emissions gaps drive performance?

Slacks-based measures answer a variable-specific diagnostic question. Tone's
separable undesirable-output model contracts input excesses and bad-output
excesses while expanding desirable-output shortfalls through a fractional
normalization. Its production account permits the bad-output contraction
slack in a separable, strongly disposable setting. Non-separable slack
accounting and weak disposability are separate choices: the former changes
how selected good and bad outputs enter the performance account, while the latter
changes the represented production technology. Either changes more than the
name of one constraint.

| Evidence field | Record |
|---|---|
| **Economic question** | Which resource excesses, desirable-output shortfalls, and emissions-reduction gaps account for the unit's performance shortfall? |
| **Technology / estimator** | Tone-style separable strongly disposable undesirable-output envelopment for the canonical current preset. |
| **Measure** | Non-oriented fractional SBM with variable-level normalized slacks. |
| **RTS** | VRS or another explicitly supported envelopment restriction; RTS and disposal remain independent. |
| **Data / time** | Positive inputs, desirable outputs, and undesirable outputs for standard normalization; static initially. |
| **Native score** | Tone-style efficiency ratio, normally in $(0,1]$, with one representing no measured slack inefficiency under the selected technology. |
| **Exact aliases** | None with environmental DDF, directional SBM, weak-disposal SBM, or ordinary black-box SBM. The standard ERG/SBM alias result for positive ordinary data does not automatically extend to every undesirable-output formulation. |
| **Distinct variants** | Tone's source-qualified non-separable radial/slack hybrid; SBM composed with a source-qualified weak-disposal technology; directional SBM; weighted or priority SBM; super-efficiency; network and dynamic environmental SBM. |
| **Domain** | Positive normalizers or an explicit zero policy; all data roles and disposal assumptions declared. |
| **Failures** | Zeros can make ratios undefined. Equal slack weights are not social welfare weights. Multiple optimal peers can produce nonunique targets. Replacing bads by reciprocals or negatives changes the model and can distort invariance. |
| **Solver form** | Charnes--Cooper transformed sparse LP for the canonical fractional formulation; alternate variants retain their source-specific transformations. |
| **Defining source** | Base SBM in [Tone (2001)](https://doi.org/10.1016/S0377-2217(99)00407-5); open undesirable-output report in [Tone (2003)](https://doi.org/10.24545/00000955); non-radial equivalence cautions in [Färe and Grosskopf (2009)](https://doi.org/10.1016/j.ejor.2009.01.031) and their [clarification](https://doi.org/10.1016/j.ejor.2010.02.033). |
| **Evidence status** | `primary-checked` and implemented/public for the separable preset. Non-separability and weak-disposal compositions remain distinct method identities rather than switches on this leaf. |
| **Oracle** | An analytical project fixture checks the equal-dimension fractional score, component accounts, targets, peers, unit invariance, and failure closure. The defining equation is retained, but no source numerical table or alternate source-weight column is redistributed. |
| **Package recipe** | `environmental.sbm.separable_strong`; the separate Tone hybrid belongs to `environmental.sbm.nonseparable_hybrid.tone_2003`, while composing an SBM measure with a named `environmental.weak_disposal.*` technology requires its own source-qualified leaf. `environmental.directional_nonradial` remains another distinct measure family. |
| **Book location** | **Active core placement:** `book/chapters/03-environmental/07-undesirable-output-sbm.md`; technology-sensitive variants remain in package documentation. |

### 2.5 Must selected services and their linked residuals retain one common operating share?

Tone's non-separable extension addresses a different production story from
the separable bad-output SBM. Every input remains in the ordinary input-slack
account. Only desirable and undesirable outputs are partitioned. Management
declares which good/bad output block belongs to one joint operating process
and which outputs may be adjusted separately.

The common factor $\alpha$ is best read as the share of that joint process
retained in the source projection. If $\alpha=0.7$, the model retains 70
percent of both the declared desirable service and its linked residual.
That does not recommend that “less good output is better.” It measures how
far the joint activity would be scaled down while separable resource and
output accounts adjust independently. It is also not a general permission to
dispose of pollution freely or weakly.

| Evidence field | Record |
|---|---|
| **Economic question** | When selected desirable services and their linked residuals cannot be credited with independent adjustments, what common retained operating share is attainable, and which resource or separable-output gaps still explain performance? |
| **Technology / estimator** | Inputs keep their ordinary input-slack balance. Separable bad outputs use the strong balance $B^S\lambda+s^{Sb}=b_o^S$. The declared non-separable good/bad outputs share $\alpha$ through $\alpha y_o^{NSg}\leq Y^{NSg}\lambda$ and $Y^{NSb}\lambda\leq\alpha y_o^{NSb}$. The latter is a source projection relation, not a generic weak-disposal axiom. |
| **Measure** | Tone's source score combines normalized input excesses, normalized separable good/bad output gaps, and the common joint-output term $q(1-\alpha)$. Source-to-reference residuals may remain in the non-separable block without entering the score, so score one and Pareto--Koopmans completion are separate claims. |
| **RTS** | The public leaf exposes CRS, VRS, NIRS, and NDRS from the source intensity restriction. The exact project certificate covers the declared VRS case; the other policies have equation, smoke, and property evidence, not a published numerical reproduction. |
| **Data / time** | Strictly positive inputs and outputs, at least one declared non-separable good and bad output, $\alpha_{\min}\in[0,1]$, and a non-overlapping output partition. Under CRS or NIRS, $\alpha_{\min}=0$ with no separable desirable output is rejected because it admits an unanchored zero-activity shutdown; a positive lower bound or a separable desirable output supplies the required operating anchor. |
| **Native score** | Higher $\rho_{NS}\in(0,1]$ means less measured shortfall in the source accounts; $\alpha$ separately reports the retained joint operating share. Neither is converted into a DDF distance or a score from a weak-disposal technology. |
| **Exact aliases** | None with common-factor weak disposal, activity-specific weak disposal, the separable strongly disposable SBM, or a generic non-radial environmental DDF. |
| **Distinct variants** | Alternative non-separable partitions, source-qualified weak-disposal SBM constructions, directional/non-radial SBM, network environmental SBM, and dynamic environmental SBM. |
| **Domain** | Every output belongs to exactly one declared separable or non-separable block. The lower bound on $\alpha$, the source projection, reference activity, and unscored source-to-reference residuals remain visible. |
| **Failures** | Partitioning inputs; calling the shared operating proportion “weak disposal”; interpreting $\alpha<1$ as a preference for lower desirable output; replacing $\alpha$ times the observed output by the reference activity; scoring the remaining non-separable residuals without changing the estimator; or reporting $\rho_{NS}=1$ as unconditional Pareto--Koopmans efficiency. |
| **Solver form** | One sparse Charnes--Cooper LP per evaluated organization, with shared reference compilation. The source projection $\alpha y_o^{NS}$ and reference activity $Y^{NS}\lambda$ are returned separately. |
| **Defining source** | Tone's official GRIPS research report, “Dealing with Undesirable Outputs in DEA: A Slacks-Based Measure (SBM) Approach,” [DOI](https://doi.org/10.24545/00000955), especially equations (29)--(32), Tables 4--5, and the residual definitions in equations (38)--(39). |
| **Evidence status** | `primary-checked`, implemented/public as `ToneNonSeparableSBM`, with exact aliases `NonSeparableUndesirableSBM` and `SBMNS`. |
| **Oracle** | `analytically derived`, not a published-score reproduction. The project-authored `environmental_disposability_contrast` case has a hand-checkable VRS score, retained-share, intensity, target, and residual account; public tests also check unit invariance, declared RTS policies, aliases, and validation failures. No source table or printed-score comparison is retained. |
| **Package recipe** | `ToneNonSeparableSBM(nonseparable_outputs=..., nonseparable_bad_outputs=..., alpha_min=...)`; `alpha_min` is source-native, not a package repair. There is no `weak_nonseparable` switch. |
| **Book location** | **Documentation/source review only.** Tone's non-separable hybrid has no independent placement in the current handbook. |

## 3. Valuing environmental trade-offs

### 3.1 What is the local opportunity cost of a cleaner plan?

Dual multipliers can describe a local supporting trade-off between residual
reduction and valued production. They are not observed permit prices, causal
damage estimates, or universal marginal abatement costs. Piecewise-linear
frontiers can admit many supporting hyperplanes, so a solver-selected dual is
not automatically the unique economic value.

| Evidence field | Record |
|---|---|
| **Economic question** | What local model-implied sacrifice in valued output or resources supports an additional unit of residual reduction at the assessed activity? |
| **Technology / estimator** | A named environmental technology with an economically meaningful dual representation. |
| **Measure** | Shadow abatement value, directional profit/Nerlovian gap, or price-informed cost, revenue, or profit objective. |
| **RTS** | Inherited from the primal technology; intercept and multiplier interpretations change with RTS. |
| **Data / time** | Quantities for shadow values; observed prices, taxes, damage values, or policy weights for valued objectives; any price vintage and normalization must be recorded. |
| **Native score** | Source-specific shadow-price ratio or monetary/direction-normalized gap. No equal-weight technical score is relabeled welfare. |
| **Exact aliases** | None among a dual shadow value, a market price, an emissions tax, a damage value, and a normalized Nerlovian inefficiency score. |
| **Distinct variants** | Directional shadow values; price-constrained multipliers; marginal abatement-cost intervals; pollution-adjusted cost, revenue, and profit; natural and managerial disposability strategies. |
| **Domain** | Valid supporting multipliers, explicit normalization, compatible monetary units and price dates. |
| **Failures** | Dual multiplicity; zero normalizers; unsupported extrapolation away from the local facet; interpreting an endogenous model trade-off as a causal or market valuation. |
| **Solver form** | LP dual recovery plus optional secondary LPs for multiplier intervals; economic objectives remain separate primal programmes where appropriate. |
| **Defining source** | Directional duality in [Chambers, Chung, and Färe (1998)](https://doi.org/10.1023/A:1022637501082); environmental production cautions in [Førsund (2009)](https://doi.org/10.1561/101.00000021). |
| **Evidence status** | `review-supported`; each public valuation leaf requires its own price and normalization audit. |
| **Oracle** | `not located`; no environmental shadow-abatement leaf currently has a certified literature oracle or independent implementation comparison. |
| **Package recipe** | Named technology + `environmental.shadow_abatement` or a price-informed economic objective + alternate-optimum policy. |
| **Book location** | **Documentation/source review only.** Environmental shadow-value leaves have no current handbook placement. |

### 3.2 When does an environmental rule change the feasible operating plan?

An environmental rule is economically meaningful only after its institutional
role is stated. A plant-level emissions standard can restrict the plans that
may legally be chosen. An emissions tax or permit price instead values a
quantity. A sector-wide cap requires allocation across plants. Regulation can
also be an inherited operating condition or a treatment whose causal effect
is studied in a separate empirical design. One generic
`environmental_regulation=True` option would erase these differences.

| Evidence field | Record |
|---|---|
| **Economic question** | How much valued production or resource use must change for an organization to comply with a declared emissions, intensity, or technology standard, and at what standard does the rule become binding or infeasible? |
| **Technology / estimator** | A named environmental production technology intersected with a legally defined compliance set. The baseline and regulated technologies retain identical comparison-population, time, disposal, and RTS assumptions unless the policy design intentionally changes them. |
| **Measure** | Source-qualified compliance opportunity cost, before/after environmental efficiency comparison, or feasibility threshold. A tax-valued loss, centralized permit allocation, and causal policy effect are separate analyses. |
| **RTS** | Inherited from and matched across the baseline and regulated technologies; the regulation does not select RTS. |
| **Data / time** | Inputs, desirable and undesirable outputs, the standard's legal unit and scope, compliance period, covered organizations, exemptions, and policy vintage. Price data are required only for a monetary valuation. |
| **Native score** | Source-specific environmental efficiency and the attainable desirable-output or resource sacrifice induced by the standard; zero sacrifice means non-binding under the maintained technology, not that the policy has no social cost. |
| **Exact aliases** | None among an emissions cap, emissions-intensity standard, technology mandate, emissions tax, tradable permit price, aggregate quota, and observed regulation indicator. |
| **Distinct variants** | Weak- versus strong-disposal compliance technologies; plant versus sector constraints; bounded-variable standards; fixed-sum permit allocation; regulation as a conditional variable; causal policy evaluation. |
| **Domain** | Standard and production quantities must share physical units, covered activities and time horizon. Baseline and compliance sets must be nested in the direction claimed before a loss is interpreted. |
| **Failures** | A rule can be non-binding, infeasible, or outside the empirical support. Treating a permit price as a physical cap, changing the comparison population between scenarios, or calling a score difference causal invalidates the interpretation. |
| **Solver form** | Matched LPs over baseline and compliance-constrained technologies; scalar search is needed only when the policy threshold itself is solved for. Aggregate permit allocation requires a separate centralized or bargaining programme. |
| **Defining source** | Regulatory standards and legislative opportunity costs in [Zofío and Prieto (2001)](https://doi.org/10.1016/S0928-7655(00)00030-0); bounded-variable regulatory-impact construction in [Bremberger et al. (2015)](https://doi.org/10.1057/jors.2013.176); a distinct centralized permit-allocation example in [Wu et al. (2013)](https://doi.org/10.1016/j.mcm.2012.03.008). |
| **Evidence status** | `review-supported`; the roles and merge boundary are established, but each executable standard or allocation leaf still requires a formulation-level primary audit. |
| **Oracle** | `not located`; no published numerical regulatory-standard example has yet been reproduced in repository tests. |
| **Package recipe** | Registry-provisional environmental regulatory-standard analysis composed from a named production account, standard specification, matched baseline, and explicit policy role; no public constructor is asserted. |
| **Book location** | **Documentation/source review only.** Regulatory-standard and permit-allocation leaves have no current handbook placement. |

## 4. Merge boundary

### Safe unification

The following relationships justify shared infrastructure, not necessarily a
shared public method ID:

| Shared mechanism | Safe reuse | Required retained metadata |
|---|---|---|
| Linear environmental envelopment | Sparse technology compiler and per-DMU RHS updates | disposal, null jointness, RTS, reference policy |
| Directional improvement | One DDF measure interface | production account, direction units, signs, native score |
| Fractional slack aggregation | Charnes--Cooper and target reporting | technology, slack weights, zero policy |
| Two connected subtechnologies | Block matrix and target validation | pollution-generating inputs, separate intensities, coupling |
| Material coefficients | Linear balance-row generator | coefficient provenance, system boundary, losses/stocks |
| Hyperbolic path | LP feasibility compiler inside scalar search | exact path, bounds, monotonicity, native score |
| Environmental panel analysis | Deduplicated distance-task graph | time reference, technology vintage, direction comparability |
| Regulatory scenario comparison | Matched baseline/constrained task graph | legal unit, covered population, policy and sample vintage, nesting |

### Never merge silently

- Strong disposal, single-factor weak disposal, activity-specific weak
  disposal, and pollutant-selective disposal define different opportunity
  sets.
- Weak disposal and null jointness are independent assumptions.
- A bad-output equality is a formulation component, not the universal
  definition of weak disposal.
- Environmental DDF, hyperbolic efficiency, and undesirable-output SBM
  describe different operating programmes even on the same technology.
- Zhou--Ang--Wang's three non-CHP component-directional accounts are frozen
  source presets, not evidence for arbitrary directions, weights, dimensions,
  returns to scale, references, or the source's unresolved CHP branch.
- Separable and non-separable SBM accounts are not one unnamed-model toggle,
  and neither account by itself identifies a weak-disposal technology.
- By-production, Coelli material-inflow efficiency, weak-$G$ conservation,
  and explicit treatment networks are different production accounts.
- Separate and coupled by-production intensity systems must not be exchanged
  for computational convenience.
- A local shadow price, observed market price, tax, and environmental damage
  value are different evidence.
- A plant compliance standard, sector-wide emissions allocation, regulation
  as an operating condition, and the causal effect of regulation are different
  analyses.
- Natural and managerial disposability are operating-strategy formulations,
  not aliases for strong and weak disposal.

## 5. Package and book consequences

The maintainable implementation split is:

```text
technology/environmental/
    joint.py
    weak_disposal.py
    by_production.py
    material_balance.py
    treatment.py
measures/
    directional.py
    hyperbolic.py
    sbm.py
analysis/
    environmental_values.py
```

A public convenience preset may retain a historical author/year name, but
every result should expand it into:

```text
production_account
disposal specification
null-jointness specification
pollutant-level roles
RTS and reference
measure and native score
direction or slack normalization
regulatory role, legal unit, coverage, and policy vintage where applicable
solver and verification status
```

The active environmental chapters use cases to show how the answer changes
when the *production account* changes. Named variants, material-balance
specializations, environmental-network compositions, and equivalence proofs
remain in package documentation and this review unless they independently
pass the handbook admission gate.

## 6. Source map

### Defining and structuring sources

- Färe et al. (1989), “Multilateral Productivity Comparisons When Some
  Outputs Are Undesirable,” [DOI](https://doi.org/10.2307/1928055).
- Chambers, Chung, and Färe (1996), “Benefit and Distance Functions,”
  [DOI](https://doi.org/10.1006/jeth.1996.0096).
- Chung, Färe, and Grosskopf (1997), “Productivity and Undesirable Outputs:
  A Directional Distance Function Approach,”
  [DOI](https://doi.org/10.1006/jema.1997.0146).
- Zhou, Ang, and Wang (2012), “Energy and CO2 Emission Performance in
  Electricity Generation: A Non-radial Directional Distance Function
  Approach,” [DOI](https://doi.org/10.1016/j.ejor.2012.04.022).
- Tone (2001), “A Slacks-Based Measure of Efficiency in Data Envelopment
  Analysis,” [DOI](https://doi.org/10.1016/S0377-2217(99)00407-5).
- Tone (2003), “Dealing with Undesirable Outputs in DEA: A Slacks-Based
  Measure (SBM) Approach,” open GRIPS research report,
  [DOI](https://doi.org/10.24545/00000955).
- Kuosmanen (2005), “Weak Disposability in Nonparametric Production
  Analysis with Undesirable Outputs,”
  [DOI](https://doi.org/10.1111/j.1467-8276.2005.00788.x).
- Coelli, Lauwers, and Van Huylenbroeck (2007), material-balance
  environmental efficiency,
  [DOI](https://doi.org/10.1007/s11123-007-0052-8).
- Førsund (2009), “Good Modelling of Bad Outputs,”
  [DOI](https://doi.org/10.1561/101.00000021).
- Murty, Russell, and Levkoff (2012), “On Modeling Pollution-Generating
  Technologies,” [DOI](https://doi.org/10.1016/j.jeem.2012.02.005).
- Tone and Tsutsui (2014), “Dynamic DEA with Network Structure:
  A Slacks-Based Measure Approach,”
  [DOI](https://doi.org/10.1016/j.omega.2013.04.002).
- Hampf (2014), production and end-of-pipe abatement efficiency under a
  material-balance account,
  [DOI](https://doi.org/10.1007/s11123-013-0357-8).
- Lozano (2015), joint-input production and pollution-generating network DEA,
  [DOI](https://doi.org/10.1016/j.eswa.2015.06.023).
- Rødseth (2017), material balance and weak-$G$ disposability,
  [DOI](https://doi.org/10.1007/s10640-015-9974-1).
- Chen, Wang, and Lai (2017), semi-disposability and the non-disposal degree,
  [DOI](https://doi.org/10.1016/j.ejor.2016.12.042).
- Roshdi et al. (2018), generalized weak disposal and the piecewise
  Cobb--Douglas environmental technology,
  [DOI](https://doi.org/10.1016/j.ejor.2017.10.033).
- Kalhor and Kazemi Matin (2018), activity-specific weak disposal in general
  network production,
  [DOI](https://doi.org/10.1051/ro/2017022).
- Cuadros, Rodríguez, and Contreras (2020), dynamic electricity production
  with undesirable outputs,
  [DOI](https://doi.org/10.3390/en13246624).
- Zofío and Prieto (2001), environmental regulatory standards and legislative
  opportunity cost,
  [DOI](https://doi.org/10.1016/S0928-7655(00)00030-0).
- Bremberger et al. (2015), bounded-variable analysis of environmental
  standards,
  [DOI](https://doi.org/10.1057/jors.2013.176).
- Wu et al. (2013), centralized reduction and reallocation of emissions
  permits,
  [DOI](https://doi.org/10.1016/j.mcm.2012.03.008).
- Chu et al. (2026), refined semi-disposability and a bounded bad-output
  inefficiency axiom,
  [DOI](https://doi.org/10.1016/j.ejor.2026.07.013).

### Reviews and boundary audits

- Scheel (2001), undesirable outputs in efficiency measurement,
  [DOI](https://doi.org/10.1016/S0377-2217(00)00160-0).
- Dakpo, Jeanneaux, and Latruffe (2016), pollution-generating technologies,
  [DOI](https://doi.org/10.1016/j.ejor.2015.07.024).
- Pham and Zelenyuk (2019), weak-disposability technologies,
  [DOI](https://doi.org/10.1016/j.ejor.2018.09.019).
