# M10 mainstream package-versus-Handbook coverage audit

**Status:** package/API, shadow-registry, source-protocol, review, and
Handbook cross-audit completed 3 August 2026. This document authorizes no new
Handbook chapter and implements no method.

## Question and classification rule

This audit tests a deliberately narrow claim: does a familiar DEA topic add a
new field-level performance mechanism, or does it modify a model already
represented in the Handbook? A separate acronym, multiplier programme,
reference window, resampling algorithm, topology, or paper is not by itself a
mother mechanism.

The classifications are:

- **A — retained mother mechanism:** an independent production account,
  performance criterion, organizational account, temporal mechanism,
  valuation institution, comparison institution, or inferential claim needed
  to answer a field-level economic or managerial question. A mechanism can
  still share a chapter with its closest family.
- **B — package-wide capability or teaching decision:** an important
  cross-cutting choice that should compose with one or more A mechanisms. It
  belongs in package Documentation and, where essential for interpretation,
  in the smallest existing Handbook placement.
- **C — named technical leaf or evidence-deferred candidate:** a paper-specific
  formulation, cross-product, convenience operator, or candidate whose
  defining source and independent numerical oracle do not yet support a
  current public claim.

“Package should support” below is a target-scope statement, not evidence that
the current API already does. Public support requires a callable symbol, a
public catalog identity, a source-frozen contract, and independent numerical
evidence. A shadow-registry prototype or benchmark does not satisfy that gate.

## Audited current surface

At this snapshot, `deapack.list_methods()` returns 73 public discovery
identities: 60 `method_id` entries, five `specialization_id` entries, and eight
`preset_id` entries. The shadow registry contains 65 method records and 42
typed relations. Four of those method records are explicitly non-public
prototypes: Banker MPSS, Färe--Grosskopf--Kokkelenberg physical capacity,
ordinary CRS cross-efficiency, and Andersen--Petersen radial
super-efficiency. The registry is therefore an evidence-governance surface,
not a table of contents or proof of public API support.

The current Handbook route contains 18 model or study-design chapters plus
one applied community-hospital capstone. The capstone composes BCC, SBM, scale,
peer, target, sensitivity, and reporting workflows; it is not a nineteenth
model mechanism.

## A — retained mother mechanisms already represented

| Field-level question | Current mother treatment | Why the route remains independent |
|---|---|---|
| What proportional resource saving or service expansion is attainable, and what changes under convex, scalable, or observed-practice technologies? | classical radial DEA with CRS/VRS and FDH inside the technology comparison | establishes the ordinary production frontier and radial performance commitment |
| Does operating size account for a performance gap? | scale efficiency, local returns to scale, and scale elasticity | separates managerial performance from represented operating-size opportunity |
| Which individual resources, services, or residuals have non-proportional shortfalls? | Additive, RAM/Russell, SBM, and undesirable-output SBM consolidated by their reporting rulers | changes the performance criterion from proportional movement to variable-specific shortfall accounting |
| Is a declared joint operating programme attainable? | directional distance functions | evaluates a management-declared joint resource/service programme rather than an orientation alias |
| Did the organization minimize cost or maximize revenue or profit at observed prices? | cost, revenue, profit, allocative, profitability, and Nerlovian accounts | introduces an observed-price valuation institution rather than endogenous DEA weights alone |
| How do undesirable outcomes change the production account? | environmental DDF, disposal alternatives, by-production, material accounts, and environmental SBM | changes the maintained joint-production and disposal rights |
| Why did productivity change, and which information set defines represented best practice? | Malmquist, Luenberger, environmental ML/GML, and Hicks--Moorsteen | retains distinct multiplicative, additive, environmental, and complete quantity-change accounts |
| Where inside a connected organization do intermediate products and process gaps arise? | system/relational/additive network DEA and Network SBM | exposes internal production and responsibility institutions hidden by a black box |
| How do present choices create later assets or obligations? | Dynamic SBM, with other intertemporal technologies kept as conceptual boundaries | introduces state continuity rather than repeated static fitting |
| How do within-group performance and between-opportunity gaps differ? | radial metafrontier | introduces a declared comparison institution linking group and meta opportunities |

This A set is the current Handbook backbone. Cross-products such as
environmental-network, dynamic-network, and meta-SBM do not create additional
mother routes merely by composing two admitted axes.

## B/C evidence matrix for disputed candidates

| Candidate topic | A/B/C classification | Independent mother mechanism? | Current package/API state | Smallest Handbook position | Source/oracle state | Current-versus-next-version conclusion |
|---|---|---|---|---|---|---|
| Assurance regions, weight restrictions, and production trade-offs | **B mechanism; C named leaves** | **No: valuation/technology-constraint layer.** AR restricts admissible supporting valuations; production trade-offs alter technology. Neither changes the base performance criterion, and they must not share one generic `restrictions=` identity. | The narrow finite sum-form input-oriented CRS polyhedral cone-ratio leaf is implemented/public through `PolyhedralConeRatioDEA`. There remains no public AR-I, AR-II, generic weight-restriction, production-trade-off, or consistency-diagnostic API. | One conceptual treatment in the classical radial chapter, bridged to the exact package Documentation; no new Handbook chapter. | Charnes--Cooper--Huang--Sun cone-ratio has complete page-frozen primary sources, an automated independent Example 2 multiplier/envelopment oracle, identity-cone CCR reduction, and fail-closed result tests. Thompson AR-I/II remain `source_not_frozen`, blocked on primary source, oracle `not_located`, and next-version. Production trade-offs are primary-checked with only a candidate oracle. | The narrow cone-ratio leaf is current and public within its exact sum-form/input/CRS boundary. Keep general AR and trade-off families next-version; do not broaden this implementation into a generic restriction API or a new book route. |
| Nondiscretionary quantities | **B semantic role; C static leaf** | **No: managerial-control and target-right layer.** The question is what management is allowed to change, not a new score family. | No public static Banker--Morey API or catalog entry. Dynamic SBM has its own source-qualified nondiscretionary input/output roles, but that does not establish a generic static contract. | Study design, with at most one radial illustration after evidence closure. | Banker--Morey static leaf: full defining text not obtained, equations not frozen, oracle `not_located`; a reported printed-equation issue makes secondary reconstruction unsafe. | Preserve the semantic role in the method universe, but defer the static executable leaf to the next version. Do not infer it from zero direction components or Dynamic SBM. |
| Categorical variables and admissible peers | **B semantic role; C static leaf** | **No: comparison-right layer.** Categories govern who may be compared; they are not ordinary quantities or a new efficiency criterion. | Public `PeerEligibility` and `PeerEligibilityProvenance` provide a source-neutral comparison-right policy on the audited ordinary radial, Additive/RAM, ordinary SBM, and ordinary DDF classical black-box surface: declared observation-specific candidates intersect the base `ReferenceSpec`. There is still no public categorical role, compiler, or Banker--Morey source leaf, and environmental/specialist neighbors remain outside this capability audit. | Study design and one source-neutral classical comparison-population example; not a named model chapter. | Publisher metadata and abstract are checked, and OR-Library's raw `dea3` file is located, but the defining equations, source-table schema, and numerical results are unavailable. The 69-by-6 unlabelled file is not an oracle. | The generic policy is current but claims `categorical_interpretation: not_claimed`. The named leaf remains `deferred_to_next_version` under `source_protocols/banker_morey_1986_categorical.md`; do not simulate it by one-hot encoding or separate-group DEA. |
| Congestion, MPSS, and physical capacity | **B scale/capacity questions; C named estimators** | **No: family of distinct scale/capacity diagnostics, not one mother model.** Congestion asks whether excess input suppresses attainable output; MPSS asks about maximum fixed-mix average productivity; physical capacity holds quasi-fixed resources while releasing variable-resource limits. They are not aliases of scale efficiency or of one another. | Scale efficiency, local RTS, and scale elasticity are public. MPSS and physical-capacity code, machine records, tests, and benchmarks are non-public prototypes; their root symbols and public catalog IDs are absent. No congestion implementation or public record exists. | One unnamed congestion boundary and short MPSS/capacity contrasts inside the scale chapter. Named estimators remain Documentation only if later released. | Banker MPSS and FGK capacity defining articles are not fully frozen and have only later-source/derived property checks. FGL congestion has an incomplete defining weak-disposability programme and no oracle. Cooper--Deng--Huang--Li equations are not frozen from the defining source and no oracle is located. | All named leaves remain next-version. Prototype execution and performance benchmarks do not close literature identity. No separate MPSS, congestion, or capacity chapter. |
| Window and sequential reference policies | **B current policy; C convenience operator** | **No: reference-information layer.** They determine which observed practices are admitted to each fit; repeated window scores do not themselves form a productivity-change identity. | `ReferenceSpec("sequential")` and `ReferenceSpec("window", ...)` are public and the reference builder is implemented. `analysis.window_efficiency` is planned and absent as a public operator. Sequential network propagation is a different Documentation-only production mechanism and must not be confused with a temporal reference policy. | Reference-information decision inside the Malmquist/productivity chapter, plus a short contrast with dynamic production in the dynamic chapter. | Sequential/global/biennial distinctions have primary-source support; window variants are review-supported. Window and sequential builders have implementation coverage, but no certified literature oracle for a standalone window-efficiency or productivity operator. | Current support is the explicit reference policy composed with a supported estimator. A convenience window-efficiency operator is next-version/Documentation only after its exact reporting and oracle contract closes. No window-model chapter. |
| Frontier bootstrap and statistical tests | **B current-edition safeguard; potential A inferential institution; C executable leaves** | **Yes as an independent inferential layer, not as another DEA performance mother model.** It changes the permitted sampling claim, not the underlying deterministic optimum. | The public catalog exposes deterministic frontier methods but no bootstrap or statistical-testing procedure. Planned IDs in `METHODS.md` are not callable APIs. | Conceptual sampling-uncertainty and second-stage safeguards in study design. A later inference treatment requires a coherent estimator/DGP/result contract; no current chapter is authorized. | Simar--Wilson frontier, productivity, RTS-test, and directional procedures are primary-checked or review-supported, but published illustrations remain candidate oracles and none is reproduced in automated repository tests. | Entire executable inference layer remains next-version. Naive row resampling is not an admissible substitute. No present Handbook expansion. |
| Partial and conditional frontiers | **B current-edition boundary; C executable estimators** | **Yes as distinct estimator/comparison mechanisms, but not new performance criteria.** Full DEA, order-$m$/order-$\alpha$, and conditional DEA/FDH estimate different frontiers. | No public partial- or conditional-frontier estimator. Metafrontier and reference filtering do not implement continuous conditioning. | Study design and the metafrontier boundary: discrete declared groups versus continuous operating environments. | Core papers are primary-checked and candidate numerical illustrations are identified; no independent automated oracle or typed failure-safe result contract exists. | Next-version estimator queue. Do not relabel trimming, outlier deletion, separate-group DEA, or a metafrontier as conditional DEA. |
| Contextual second-stage procedures | **B procedure layer; C named procedures** | **No: statistical procedure layer composed with a base estimator.** Simar--Wilson Algorithms 1/2, Banker--Natarajan DEA--OLS, and conditional frontiers have different DGPs and are not interchangeable. | No public second-stage contextual API. `data.contextual` and the named procedures are planning identities only. | Study-design safeguards and, where relevant, the metafrontier/continuous-environment contrast. | Defining sources are primary-checked; Monte Carlo or empirical illustrations are candidate oracles, not automated reproductions. | Next-version. No generic `second_stage=True`, ordinary OLS/Tobit shortcut, causal claim, or standalone current chapter. |
| Ordinary cross-efficiency and super-efficiency | **B appraisal layer; C non-equivalent named leaves** | **No:** they ask how records withstand peer valuations or self-exclusion; they do not redefine the ordinary production mother family. Named cross and super constructions remain non-equivalent leaves. | Ordinary CRS cross-efficiency and Andersen--Petersen radial super-efficiency are internal prototypes with non-public machine records, tests, and benchmarks; their public symbols/catalog IDs are absent. Source-qualified Liang--Wu--Cook--Zhu game cross-efficiency, Ray directional super-efficiency, and Tone super-SBM are public `documentation_only` leaves. | No current Handbook route. If evidence later justifies reader treatment, consolidate the appraisal question rather than create one chapter per named leaf. | Ordinary cross: defining/secondary full texts not obtained and no current raw-matrix oracle. AP radial: defining article not obtained; later-source and derived checks do not establish the 1993 source profile. The three public specialized leaves have literature oracles for their own narrower contracts only. | Keep public specialized leaves in Documentation. Ordinary cross and AP radial remain next-version; do not generalize evidence from the game, directional, or SBM leaves. |
| Färe--Primont productivity | **Potential A productivity account; C in the current evidence state** | **Yes at the productivity-account level:** it adds fixed-reference, transitive multilateral input/output aggregators and a complete TFP level comparison. It still belongs inside the productivity family rather than automatically receiving a new chapter. | No public API, catalog identity, or machine record. Reusable radial-distance infrastructure is not an implementation of the aggregate-quantity account. | Existing productivity part, after source closure; compare with Hicks--Moorsteen and Malmquist rather than create a paper-title chapter. | Author working paper and artificial-data numerical vector are located; final primary source is not frozen, the equation audit is incomplete, and the vector has not been independently reproduced. | Important next-version candidate, but not one of the current source/oracle-closable gaps. No provisional equations or chapter. |
| Parallel and general network topology | **B topology/attribution layer; C named leaves** | **No new mother mechanism:** graph/topology and attribution choices sit inside the admitted network family. A parallel relational account and physical shared-resource allocation are themselves non-equivalent technical leaves. | Public network coverage includes source-qualified two-stage/system, relational, additive, Network-SBM, and selected general-network paths. `graph.parallel`, Kao general series--parallel, Kao parallel relational, and a generic `ResourcePoolSpec` are not public. | Existing two network chapters; topology and governance choices are taught there only when the executable evidence closes. | Kao 2009/2012 sources support the distinction, but no independent general/parallel executable oracle is located. The 2012 VRS interpretation also has a documented component-nonnegativity problem. | Next-version technical leaves. Do not promote every topology or network cross-product to a chapter. |
| Large-$n$ and parallel execution | **B current engineering; no model-level C identity** | **No: computational-engineering layer.** It changes how an admitted estimator is executed, not its economic estimand or feasible set. | Sparse compilers, reference reuse, score-only paths, deduplicated productivity task graphs, bounded streaming exports, FDH `chunk_size`, and governed family benchmarks are current. Serial execution is the correctness baseline; there is no generic public `n_jobs` execution contract. | Package performance/developer Documentation only. Cases may report scale, memory, and solve counts, but the Handbook gains no method route. | Literature source/oracle gates are inapplicable. The controlling evidence is exact equivalence to the serial unscreened estimator, deterministic scheduling, solve-count/certificate tests, memory-bounded behavior, and release benchmarks. | Continue current engineering. Future parallelism, screening, column generation, or approximation must be opt-in and method-specific; none is a DEA model or book chapter. |

## Package gaps eligible for priority work

This audit originally ranked **two**, not three, bounded package candidates.
M10-E completed Priority 1 within its frozen boundary. The post-ranking access
audit then found that Priority 2 lacks the complete defining text, source-table
schema, and numerical oracle required for implementation, so it is deferred to
the next version. The ranking itself did not authorize implementation inside
the earlier M10-B audit task.

### Priority 1 — finite sum-form CRS polyhedral cone-ratio DEA

Implemented leaf:
`valuation.weight_restriction.cone_ratio.polyhedral_crs.charnes_etal_1990`.
The complete primary sources and finite programme are page-frozen, 1990
Example 2 is independently reproduced, and the direct multiplier versus
transformed-envelopment cross-form check is automated independently of the
production compiler. M10-E closes the previously bounded work with malformed
input and solver-evidence gates, identity-cone reduction, unit covariance,
typed provenance, a dedicated result schema, and only the audited
CRS/input/sum-form implementation.

It does not justify a Handbook chapter because it constrains the valuations
supporting the already admitted radial CRS performance account. Its
transferable lesson is the provenance and consequence of value restrictions;
the exact cone recipe belongs in Documentation.

### Priority 2 — Banker--Morey categorical peer restriction

Candidate: `static.radial.categorical.banker_morey_1986`. The post-ranking
access audit located publisher metadata and abstract plus OR-Library's raw
`dea3` file, but not the complete defining article. The unlabelled 69-by-6
numeric file cannot be aligned to source tables or expected results without
that article. Defining equations, variant boundaries, data schema, and an
independent oracle therefore remain unfrozen, and the named candidate is
`deferred_to_next_version` under
`source_protocols/banker_morey_1986_categorical.md`.

Source-neutral comparison-population infrastructure is now implemented only
for `RadialDEA`, `CCR`, and `BCC` through `PeerEligibility` and
`PeerEligibilityProvenance`. For each evaluated observation it intersects the
declared candidate population with the rows admitted by the base
`ReferenceSpec`; it cannot add a row excluded by that base policy. This generic
policy has no standalone catalog method identity, must not be presented as the
Banker--Morey technology, and does not authorize a categorical data role or
machine method record.

It does not justify a Handbook chapter because it changes the comparison
population while retaining the admitted radial criterion. The reader lesson
belongs in study design, followed by at most one radial example; the full
contract belongs in Documentation.

There is deliberately no third priority. Generic AR-I/II, nondiscretionary
static DEA, congestion, MPSS, physical capacity, ordinary cross-efficiency,
Andersen--Petersen radial super-efficiency, executable inference, and
Färe--Primont all still lack a defining-source or independent-oracle gate
required for an immediate implementation queue. Window efficiency and generic
parallel execution are useful engineering conveniences, but they do not outrank
the two originally ranked scientific gaps above.

## Binding editorial and release decision

No new Handbook chapter is authorized by this M10 audit. The current 18-route
backbone already represents the admitted mother mechanisms. B topics enter the
smallest existing chapter only when needed to prevent a substantive
misinterpretation; executable recipes and variants go to package
Documentation. C candidates remain non-public or Documentation-only until
their own source, oracle, API, failure, and performance gates close.

The method catalog, machine registry, package Documentation, and Handbook are
therefore intentionally asymmetric. Completeness means that important choices
are represented at the correct layer, not that every name receives a callable
function or a chapter.
