# Productivity change: accounting for performance and opportunity over time

## Purpose and scope

This review begins with the economic question:

> Did a producer obtain more valued output from its resource commitment, and
> how much of the measured change is associated with its position relative to
> best practice, the represented production opportunities, scale and mix, or
> the benchmark information available to the analyst?

DEA-based productivity is not a single model. It composes static production
technologies, within- and cross-period evaluations, a reference-information
policy, an index or indicator, and sometimes a source-specific decomposition.
Those layers determine whether the result is a local technical-performance
indicator, an environmental performance index, or a complete total factor
productivity (TFP) account.

This document reconciles the productivity corpus in
[`LITERATURE_BASELINE.md`](../LITERATURE_BASELINE.md) with the scope in
[`METHOD_UNIVERSE.md`](../METHOD_UNIVERSE.md), the canonical IDs in
[`METHODS.md`](../METHODS.md), and the current publication policy in
[`BOOK_ARCHITECTURE.md`](../BOOK_ARCHITECTURE.md). It does not invent
numerical examples or treat a planned registry entry as implemented.

## Evidence protocol

Every evidence record contains the following fields.

| Field | Meaning |
|---|---|
| **Economic question** | The change question and performance interpretation answered by the operator. |
| **Technology / estimator** | Period and pooled attainable sets and the estimator used to construct them. |
| **Measure** | Radial distance, directional distance, non-radial gap, or aggregate-quantity system used in component tasks. |
| **RTS** | Returns-to-scale assumptions in every component technology. |
| **Data / time** | Panel matching, comparison horizon, reference vintage, quantities, and any prices. |
| **Native score** | Source-native multiplicative index or additive indicator and its improvement convention. |
| **Exact aliases** | Historically different names that are algebraically identical on a stated domain. |
| **Distinct variants** | Nearby operators, reference policies, or decompositions that require another canonical leaf. |
| **Domain** | Positivity, feasibility, direction comparability, aggregation, and panel requirements. |
| **Failures** | Undefined distances, infeasible cross-period tasks, identity failure, and invalid interpretation. |
| **Solver form** | Static task graph and optimization form needed to compute the operator. |
| **Defining source** | Original or authoritative source fixing the formula and interpretation. |
| **Evidence status** | `primary-checked`, `review-supported`, or `registry-provisional`. |
| **Oracle** | Current DEAPack numerical-verification state using `not located`, `candidate`, `analytically derived`, `reproduced`, or `cross-implemented`. Repository property evidence is stated separately; analytical derivation does not claim a published-data reproduction, and no numerical oracle is inferred from a citation alone. |
| **Package recipe** | Canonical operator, reference, measure, and decomposition IDs. |
| **Book location** | One audited status: active core placement, documentation/source review only, or evidence-deferred candidate. Only an exact path in `book/index.md` establishes active placement. |

`primary-checked` confirms the defining identity and principal assumptions,
not reproduction of an empirical table. `review-supported` identifies a
recognized family whose executable leaf still needs a formulation audit.
`registry-provisional` is an advanced scope marker only.

The current public Malmquist, Luenberger, global/biennial Malmquist, standard
and APZ Malmquist--Luenberger, and global environmental productivity
implementations have synthetic, property, and failure-case evidence. The
output-oriented CRS FGNZ core Malmquist preset, the source-qualified enhanced
FGNZ and Ray--Desli decompositions, and the CFG and APZ
Malmquist--Luenberger leaves additionally have independent analytical
certificates. These are not published-data reproductions. Unless a record
states otherwise, a published numerical oracle and independent
cross-implementation check have not been located and certified.

## 1. Measuring change against period-specific best practice

### 1.1 Did operating performance and represented opportunities improve?

The adjacent geometric Malmquist index combines four radial distance tasks:
each of the two observations is evaluated against each period's technology.
Its familiar efficiency-change and technical-change factors are accounting
components relative to empirical benchmarks. They do not establish that
management caused the first component or invention caused the second.

| Evidence field | Record |
|---|---|
| **Economic question** | How did radial productive performance change between two periods, and how did the producer's position relative to period best practice and the represented opportunities contribute? |
| **Technology / estimator** | Two contemporaneous empirical technologies plus within- and cross-period evaluations. The estimator, reference membership, convexity, and disposal assumptions are identical within a declared recipe. |
| **Measure** | Input- or output-oriented radial distance; the geometric form combines the two period-reference comparisons symmetrically. |
| **RTS** | Classical DEA TFP interpretation normally uses CRS. VRS distances can support source-qualified decompositions but do not automatically produce a complete TFP index. |
| **Data / time** | At least two periods with stable DMU identifiers, comparable variable definitions, and an explicit unbalanced-panel policy. Adjacent and non-adjacent comparisons are different tasks. |
| **Native score** | Multiplicative index with $M>1$ denoting improvement under the package convention; components multiply to the reported index only for the selected decomposition identity. |
| **Exact aliases** | The public preset `productivity.malmquist.decomposition.fgnz_core` is the output-oriented CRS FGNZ core configuration of this shared operator, not a duplicate method. Enhanced FGNZ shares the four CRS headline tasks but is a separate method because it adds two own-period VRS tasks and a nested pure-efficiency/scale identity. Ray--Desli is also separate: it adds four VRS tasks, a different three-factor allocation, and source-defined partial-component semantics. “MPI” alone is not an exact alias because orientation, distance convention, RTS, period pairing, and formula are often omitted. |
| **Distinct variants** | Input versus output orientation; arithmetic rather than geometric constructions; global or biennial reference; quasi-Malmquist; generalized Malmquist; cost Malmquist; environmental ML; Hicks--Moorsteen. |
| **Domain** | Required component distances exist and use consistent score transforms. Inputs and outputs have stable meaning and units over time. |
| **Failures** | Cross-period infeasibility under some technologies; zeros in multiplicative ratios; lost DMU matches; orientation-dependent conclusions outside restrictive conditions; calling an incomplete VRS indicator TFP. |
| **Solver form** | Deduplicated graph of four radial LP tasks per DMU-period pair, with compiled period technologies and batched right-hand-side updates. |
| **Defining source** | Index-number foundation in [Caves, Christensen, and Diewert (1982)](https://doi.org/10.2307/1913388); DEA computation and classical decomposition in [Färe et al. (1994)](https://doi.org/10.2307/2117971). |
| **Evidence status** | `primary-checked`. |
| **Oracle** | `analytically derived` for the output-oriented CRS FGNZ core claim: an independent dense four-task compiler verifies exact frontier-shift and operating-performance-change panels, every distance role, both components, and reconstruction. `published_reproduction=false`; the original FGNZ empirical application is not reproduced. Input-oriented and non-CRS configurations retain property evidence rather than inheriting this certificate. |
| **Package recipe** | Shared method `productivity.malmquist.adjacent_geometric` + `reference.contemporaneous` + radial orientation + explicit RTS. Use `productivity.malmquist.decomposition.fgnz_core` (`FGNZMalmquistProductivityIndex`; alias `FGNZMalmquist`) for the fixed output-oriented CRS core identity. |
| **Book location** | **Active core placement:** `book/chapters/04-productivity/malmquist-productivity-reference-information.md`; source-specific task algebra remains in package documentation. |

### 1.2 Which decomposition identity is being claimed?

There is no source-free list called “the Malmquist components.” FGNZ,
Ray--Desli, Balk, and O'Donnell place scale, mix, technical efficiency, and
changes in best-practice opportunity into different identities. The same
component label can therefore have a different formula and residual.

| Evidence field | Record |
|---|---|
| **Economic question** | Which economically defined sources reconstruct the selected productivity change: operating-performance change, opportunity change, scale, input/output mix, or scale-mix efficiency? |
| **Technology / estimator** | The period/reference technologies required by the defining decomposition, including CRS and VRS auxiliary technologies where the source uses both. |
| **Measure** | Radial distances for FGNZ and Ray--Desli. Balk and O'Donnell remain discovery leaves whose native measures must be frozen from their own defining texts before implementation. |
| **RTS** | Fixed by each identity. CRS and VRS distances cannot be interchanged because their ratios define different components. |
| **Data / time** | Same panel requirements as the parent index; scale/mix and complete decompositions may require additional aggregate-quantity structure or prices. |
| **Native score** | Source-named multiplicative components plus `reconstruction_residual`. The shared parent may expose the neutral algebraic fields `efficiency_change` and `technical_change` for a configurable four-distance sensitivity run, but its `decomposition_id` is null; source-named pure-efficiency, scale, or mix fields require their own non-null decomposition identity. |
| **Exact aliases** | The FGNZ core preset is an exact fixed configuration of the shared adjacent geometric Malmquist operator. Enhanced FGNZ and Ray--Desli are proven non-aliases. No alias claim is made for the unfrozen Balk or O'Donnell candidates; a component becomes an alias only if its formula and parent identity are algebraically identical on a documented domain. |
| **Distinct variants** | FGNZ pure-efficiency/scale-efficiency extension; Ray--Desli VRS account; a Balk bibliographic candidate whose native account is not yet source-frozen; O'Donnell technical/scale/mix and scale-mix efficiency; environmental and meta-frontier decompositions. |
| **Domain** | A complete decomposition requires every component task to be feasible and the multiplicative components to reconstruct the parent index within tolerance. Enhanced FGNZ's source certificate covers output orientation and a strictly positive matched panel with one or more inputs and desirable outputs. Production additionally tests nonnegative partial-zero cells with positive row aggregates and explicit unbalanced `drop`/`raise` policies; those are package extensions. The public Ray--Desli leaf is narrower: output orientation, a strictly positive balanced matched panel, one or more inputs, exactly one desirable output, and ordinary CRS/VRS technologies. |
| **Failures** | Double-counting scale effects; relabeling components across papers; using a VRS component inside a CRS identity; suppressing a nonzero reconstruction residual; causal language unsupported by the accounting design. In enhanced FGNZ, any CRS failure removes the headline and composites; an own-period VRS failure preserves only the valid CRS core and leaves enhanced components undefined as a software dependency policy, not a published partial account. Ray--Desli preserves a valid CRS headline and own-period `PEFFCH` when a VRS cross task is infeasible, while leaving `TECHCH(v)`, `SCH(v)`, and reconstruction undefined. |
| **Solver form** | Task DAG over the required CRS/VRS evaluations with a deterministic identity check after solving. Enhanced FGNZ uses four CRS plus exactly two own-period VRS tasks and no VRS cross tasks; Ray--Desli uses four CRS plus four VRS own/cross tasks. |
| **Defining source** | [Färe et al. (1994)](https://doi.org/10.2307/2117971); [Ray and Desli (1997)](https://file.lianxh.cn/Refs/TE/Zhang/Ray_Desli_1997.pdf); [Balk (2001)](https://doi.org/10.1023/A:1011117324278), bibliographic locator only until a complete auditable text is retained; [O'Donnell (2012)](https://doi.org/10.1007/s11123-012-0275-1). |
| **Evidence status** | `primary-checked` for the output-oriented CRS FGNZ core, enhanced FGNZ, and the narrow Ray--Desli leaf; all three are current/public and independently certified. Balk is only a bibliographic candidate because its complete checksum-audited defining text and equation/task freeze are not present in the current evidence bundle, so it remains `deferred_to_next_version`. O'Donnell retains its own source gate. Neither the original FGNZ OECD/PWT5 panel nor the Ray--Desli Penn World Table 5.6 panel and preprocessing are frozen, so no empirical-reproduction claim is available. |
| **Oracle** | `analytically derived` separately for the FGNZ core, enhanced FGNZ, and Ray--Desli. Enhanced FGNZ's production-free dense compiler closes four CRS plus two own-period VRS distances, verifies both nested identities component-wise, and proves its allocation is not Ray--Desli's. Ray--Desli's separate compiler closes four CRS plus four VRS distances and verifies the source's VRS-cross-infeasibility partial account. Balk's defining-text freeze and oracle, and O'Donnell's oracle, remain `not located`. |
| **Package recipe** | Non-executable umbrella `productivity.malmquist.decomposition`; public FGNZ preset `productivity.malmquist.decomposition.fgnz_core` over the shared machine method; distinct public enhanced operator `productivity.malmquist.decomposition.fgnz_pure_scale_extension` (`FGNZEnhancedMalmquistProductivityIndex`; alias `FGNZEnhancedMalmquist`); distinct public Ray--Desli operator `productivity.malmquist.decomposition.ray_desli` (`RayDesliMalmquistProductivityIndex`; alias `RayDesliMalmquist`). Balk remains a separate deferred leaf under `source_protocols/fgnz_ray_desli_balk_decompositions.md`. |
| **Book location** | **Active core placement:** the conventional decomposition idea is taught in `book/chapters/04-productivity/malmquist-productivity-reference-information.md`; source-specific decompositions remain in package documentation. |

The terminology in reports should therefore be:

- **operating-performance change**: movement relative to the selected
  period-specific best-practice benchmark, not proof of management quality;
- **change in represented opportunities**: movement of the estimated
  attainable set along the selected measure, not proof of invention;
- **scale or mix component**: only the exact source-defined contribution, not
  a residual label.

### 1.3 Do non-radial gaps or scale corrections belong in the index itself?

Two historically important extensions alter the parent index rather than
merely decomposing it. The quasi-Malmquist index replaces radial efficiency
with a one-sided non-radial slack measure. The generalized Malmquist index
combines an MPI with a Malmquist scale index and can be represented as an
output quantity index divided by an input quantity index under its source
conditions.

| Evidence field | Record |
|---|---|
| **Economic question** | Should productivity change incorporate all one-sided slacks, or explicitly include the scale contribution omitted from a radial Malmquist account? |
| **Technology / estimator** | Source-defined period technologies for the quasi- or generalized construction; neither is identified by changing an output column in the ordinary MPI code. |
| **Measure** | One-sided non-radial slack measure for quasi-Malmquist; paired Malmquist output/input quantity and scale indexes for generalized Malmquist. |
| **RTS** | Fixed by the defining source and component identities; not inherited from a generic MPI default. |
| **Data / time** | Comparable panel quantities; positive or otherwise valid normalizers for the non-radial leaf. |
| **Native score** | Source-native multiplicative quasi-Malmquist or generalized Malmquist index, with values above one denoting improvement under the recorded source convention and with its own reconstruction terms. |
| **Exact aliases** | None with radial MPI, global Malmquist, global ML, SBM Malmquist, or a “generalized distance function.” |
| **Distinct variants** | Quasi-Malmquist; Lovell--Grifell-Tatjé generalized Malmquist; source-qualified SBM Malmquist; generalized hyperbolic/path productivity. |
| **Domain** | One-sided slack programme and component indexes are well defined; all denominators and cross-period tasks are valid. |
| **Failures** | Treating “non-radial” as a universal SBM alias; confusing “generalized” with “global”; importing the ordinary MPI decomposition without proving it reconstructs the modified index. |
| **Solver form** | Multiple non-radial LPs for quasi-Malmquist; radial input/output and scale task graph for generalized Malmquist. |
| **Defining source** | [Grifell-Tatjé, Lovell, and Pastor (1998)](https://doi.org/10.1023/A:1018329930629); [Lovell and Grifell-Tatjé (1999)](https://doi.org/10.1007/BF02564713). |
| **Evidence status** | `primary-checked` at the identity and measure-family level. |
| **Oracle** | `not located`; both canonical operators are planned. |
| **Package recipe** | `productivity.quasi_malmquist.grifell_lovell_pastor_1998` or `productivity.generalized_malmquist.lovell_grifell_1999`. |
| **Book location** | **Documentation/source review only.** Quasi- and generalized-Malmquist variants have no independent placement in the current handbook. |

## 2. Choosing the benchmark information set

### 2.1 Which opportunities were available to the comparison?

Temporal reference policy is an economic information assumption, not a
cosmetic software option. It determines whether the analyst compares a
producer with same-period practice, all practice visible to a retrospective
study, only past practice, an adjacent pair, or a rolling local window. It is
applied after the comparison population has determined whose experience is
economically admissible and before any evaluation protocol excludes an
otherwise eligible row.

| Evidence field | Record |
|---|---|
| **Economic question** | Which periods of the economically eligible comparison population should count as visible production opportunities for the time comparison? |
| **Technology / estimator** | Contemporaneous $T^t$; sequential $T^{1:t}$; global pooled $T^G$; biennial pooled $T^{t,t+1}$; or a declared rolling window. Every pooled reference additionally fixes raw-observation versus preconstructed-technology pooling, convexification, disposal, and RTS. |
| **Measure** | None at the policy level; the reference is composed with Malmquist, Luenberger, environmental, non-radial, or another named operator. |
| **RTS** | Explicit for every pooled hull. “Global VRS” and “global CRS” are different technologies. |
| **Data / time** | Panel with stable periods, DMU identifiers, an independently declared comparison population, benchmark vintage, temporal membership rules, and evaluation exclusions. Window length and endpoint policy are data-design parameters. |
| **Native score** | No reference-policy score. The attached operator retains its native multiplicative or additive convention. |
| **Exact aliases** | None among contemporaneous, sequential, global, biennial, and window policies. “Pooled” is not an exact alias for global until membership and hull construction are fixed. |
| **Distinct variants** | Fixed-base reference; rolling origin; leave-one-out pooled reference; group/meta reference; non-convex union versus pooled convex meta-technology. |
| **Domain** | All observations use comparable definitions across the reference horizon. The analyst can defend which information is assumed available. |
| **Failures** | Sequential references embed persistence of past practice and can retain outliers indefinitely. Global results are retrospective and may revise when future data are appended. Biennial indexes need not be circular over a long chain. Windows create horizon and endpoint sensitivity. Calling all cross-sectional rows “global” confuses population eligibility with temporal information. |
| **Solver form** | Reference builder plus fingerprinted compiled technology; pooled observations are deduplicated and reused across component tasks. |
| **Defining source** | Sequential comparison in [Tulkens and Vanden Eeckaut (1995)](https://doi.org/10.1016/0377-2217(94)00132-V); global Malmquist in [Pastor and Lovell (2005)](https://doi.org/10.1016/j.econlet.2005.02.013); biennial Malmquist in [Pastor, Asmild, and Lovell (2011)](https://doi.org/10.1016/j.seps.2010.09.001); window analysis lineage in [Charnes et al.](https://doi.org/10.1007/BF01874734). |
| **Evidence status** | `primary-checked` for global, biennial, and sequential distinctions; window variants are `review-supported`. |
| **Oracle** | The Pastor--Lovell global operator has an analytically derived exact three-period certificate and a production-free dense CRS output compiler. Biennial Malmquist has separate exact CRS/output certificates for the two contemporaneous distances, the two adjacent-pair pooled distances, EC/BPC/TFP reconstruction, and raw pair membership; public three-period cases make both unmatched pair members behaviorally active and exclude a stronger outside-period frontier. Neither certificate reproduces the defining article's empirical application. Sequential and window builders retain implementation coverage without a certified productivity literature oracle. |
| **Package recipe** | One of `reference.contemporaneous`, `.sequential`, `.global`, `.biennial`, or `.window`, plus an executable productivity operator. |
| **Book location** | **Active core placement:** the reference-information decision is taught in `book/chapters/04-productivity/malmquist-productivity-reference-information.md`; specialized windows remain in package documentation. |

A reference policy becomes a productivity result only after an accounting
operator is attached. Window DEA alone is rolling static benchmarking, and a
sequential frontier alone is an expanding attainable set.

The complete candidate set for observation $o$ is the intersection of its
comparison population and temporal information set, followed by any
evaluation exclusion. A group restriction can therefore be combined with a
contemporaneous, sequential, global, biennial, or window policy. A
meta-technology then states how selected group technologies are combined; it
is not merely another temporal row selector. Positive-intensity peers and
maximal or global reference sets are fitted outputs and do not replace these
design declarations.

### 2.2 Can a common reference simplify time comparisons?

Global and biennial Malmquist indexes use common-reference technologies to
reduce cross-period infeasibility and change the comparison's information
vintage. They share the radial task compiler with adjacent Malmquist but do
not share its estimand.

| Evidence field | Record |
|---|---|
| **Economic question** | Can two or more observations be compared against one declared benchmark so that the change is not driven by switching reference technologies? |
| **Technology / estimator** | Full-study global pooled technology or adjacent-pair biennial technology, with construction and RTS frozen. |
| **Measure** | Radial distance ratios under the common reference. |
| **RTS** | Explicit common-reference RTS. |
| **Data / time** | Balanced or explicitly supported unbalanced panel; global sample-vintage and biennial pair membership stored in results. |
| **Native score** | Multiplicative productivity index with values above one denoting improvement under the package convention. |
| **Exact aliases** | None between global and biennial indexes, or between either and adjacent four-distance MPI. |
| **Distinct variants** | Global environmental ML; global Hicks--Moorsteen/Färe--Primont constructions; sequential or window indexes; meta-frontier common references. |
| **Domain** | Both observations are evaluable in the common technology; the pooled-hull construction is economically meaningful. |
| **Failures** | Future observations revise global historical scores; a global outlier affects all periods; pairwise biennial chaining lacks full-sample circularity; VRS and CRS common references can yield different interpretations. |
| **Solver form** | Two common-reference radial tasks per pair after one compiled pooled technology; cache by reference fingerprint. |
| **Defining source** | [Pastor and Lovell (2005)](https://doi.org/10.1016/j.econlet.2005.02.013); [Pastor, Asmild, and Lovell (2011)](https://doi.org/10.1016/j.seps.2010.09.001). |
| **Evidence status** | `primary-checked`. |
| **Oracle** | `analytically derived` for both operators within their named scopes. The global certificate covers an exact three-period account, production-free dense LP compilation, public-API comparison, decomposition reconstruction, unit checks, and fixed-vintage circularity. The biennial certificate uses rational CRS/output bounds and attaining witnesses, separates own-period and pair-pooled distance roles, reconstructs EC/BPC/TFP exactly, and verifies through the public API that the reference is the raw adjacent-period union rather than the comparison period alone or a whole-sample global pool. Neither is a published empirical reproduction. |
| **Package recipe** | `productivity.global_malmquist` + `reference.global`, or `productivity.biennial_malmquist` + `reference.biennial`. |
| **Book location** | **Active core placement:** conventional and global reference policies are consolidated in `book/chapters/04-productivity/malmquist-productivity-reference-information.md`; biennial details remain in package documentation. |

## 3. Measuring a declared change in additive units

### 3.1 How much of a management improvement programme was achieved?

The Luenberger indicator uses directional distances and additive accounting.
Its unit is inherited from the direction. It is especially useful when a
managerial programme is naturally stated as a joint increment or decrement,
but that advantage disappears if directions change across observations
without a common economic scale.

| Evidence field | Record |
|---|---|
| **Economic question** | By how much did performance change in the units of a declared input-saving, output-expansion, or joint operating programme? |
| **Technology / estimator** | Period-specific or named common-reference technologies evaluated through DDF tasks. |
| **Measure** | Directional distance; arithmetic combination of period-reference change indicators in the source-defined Luenberger operator. |
| **RTS** | Inherited by every component technology and retained in results. |
| **Data / time** | Panel plus directions comparable over units and periods; the direction's scaling and vintage are recorded. |
| **Native score** | Additive indicator with $L>0$ denoting improvement under the package convention; additive components sum to the parent indicator. |
| **Exact aliases** | None with a Malmquist ratio, Luenberger--Hicks--Moorsteen indicator, Bennet price index, or an environmental ML index. |
| **Distinct variants** | Input, output, and graph directions; alternative period averaging; non-radial Luenberger; environmental Luenberger; LHM complete indicator. |
| **Domain** | Directions have an economically comparable unit; every cross-period directional task is feasible and bounded. |
| **Failures** | Incomparable DMU-specific directions; infeasible directional tasks; treating an additive technical-performance indicator as multiplicatively complete TFP; component sums that fail reconstruction. |
| **Solver form** | DDF task DAG with compiled period/reference technologies; deterministic additive reconstruction check. |
| **Defining source** | The four-task indicator and additive decomposition are explicit in equations (8)--(10) of [Chambers, Färe, and Grosskopf (1996)](https://doi.org/10.1111/j.1468-0106.1996.tb00184.x); the later exact-indicator treatment is [Chambers (2002)](https://doi.org/10.1007/s001990100231). |
| **Evidence status** | `primary-checked`. |
| **Oracle** | `analytically derived`; two production-independent dense CRS fixtures verify all four tasks, pure represented-opportunity change, pure relative operating improvement, the exact negative cross-period distance, and $L=EC_L+TC_L$. No published numerical application is claimed. |
| **Package recipe** | `productivity.luenberger` + named reference + DDF direction policy + source-defined decomposition leaf. |
| **Book location** | **Active core placement:** `book/chapters/04-productivity/12-luenberger.md`; source-task details remain in package documentation. |

## 4. Counting unwanted outcomes in productivity

### 4.1 Did performance improve when desirable and undesirable outcomes are assessed jointly?

The Malmquist--Luenberger index applies environmental directional distances
to period and cross-period technologies. Its direction is a policy statement
about desirable-output expansion and residual reduction. The named
Chung--Färe--Grosskopf leaf freezes its source technology. Its reusable
four-distance orchestration remains private implementation machinery rather
than a second public method. Strong disposal, activity-specific weak disposal,
and by-production do not become equivalent because the same temporal formula
is used.

| Evidence field | Record |
|---|---|
| **Economic question** | Did joint desirable-output and emissions performance improve, and how did relative operating performance and represented environmental opportunities contribute? |
| **Technology / estimator** | Chung--Färe--Grosskopf CRS common-factor weak-disposal period technologies, with null jointness retained in every component task. |
| **Measure** | Environmental DDF with the observed programme $g=(0,y,-b)$ in signed notation, combined through the source multiplicative ML formula. |
| **RTS** | CRS in the named source leaf. A different scale technology requires a separately sourced and qualified variant. |
| **Data / time** | Panel with inputs, desirable outputs, bad outputs, stable units, matched DMUs, and directions comparable over periods. |
| **Native score** | Multiplicative ML index, conventionally using ratios involving $1+D$, with values above one denoting improvement under the package convention. |
| **Exact aliases** | None with ordinary MPI, an additive environmental Luenberger indicator, SBM Malmquist--Luenberger, or GML. |
| **Distinct variants** | APZ consistency-corrected composition; global or biennial ML; sequential environmental index; by-production productivity; slacks-based environmental productivity. |
| **Domain** | Valid environmental directions, positive ratio terms, and feasible cross-period environmental tasks. |
| **Failures** | Cross-period infeasibility; inconsistent technical-change sign interpretation; changing environmental technology across component tasks; incomparable directions; treating measured opportunity change as causal eco-innovation. |
| **Solver form** | Four environmental DDF tasks per adjacent pair, deduplicated across DMUs and components. |
| **Defining source** | [Chung, Färe, and Grosskopf (1997)](https://doi.org/10.1006/jema.1997.0146). |
| **Evidence status** | `primary-checked`. |
| **Oracle** | `analytically derived`: an independent dense LP compiler closes all four CFG tasks for exact frontier-shift and pure-catch-up panels, including a negative cross-period distance, unit invariance, and exact $ML=EC\times TC$ reconstruction. This does not reproduce the Swedish mill panel or the published industry averages; that empirical branch remains `deferred_to_next_version`. |
| **Package recipe** | `productivity.malmquist_luenberger.chung_fare_grosskopf_1997`. The broader configurable candidate is `deferred_to_next_version` with no public API or machine record; see `source_protocols/generic_environmental_directional_productivity.md`. |
| **Book location** | **Active core placement:** `book/chapters/04-productivity/environmental-productivity-ml-common-reference.md`; source-specific technology details remain in package documentation. |

### 4.2 Can a different pollution opportunity account resolve the APZ consistency problem?

APZ changes the production account, not the arithmetic after an index has
been calculated. The 2013 article explains why the conventional technology
can attach a counterintuitive technical-change sign to an observed move that
raises desirable output and lowers pollution. The 2017 article makes the
alternative operational: projected undesirable output may exceed the peer
combination only within a pollutant-specific empirical cap. All four
directional distances are then estimated again on that technology before the
ordinary ML ratios are formed.

| Evidence field | Record |
|---|---|
| **Economic question** | Did joint desirable-output and pollution performance improve when represented opportunities satisfy the APZ bounded bad-output postulate? |
| **Technology / estimator** | The 2017 equation (5) CRS technology: $Y^sz\ge y$, $B^sz\le b$, $X^sz\le x$, and $b_i\le\bar b_i^s$, where $\bar b_i^s=\max_k b_{ki}^s$ is calculated separately for each pollutant and reference period. |
| **Measure** | The standard four-distance geometric Malmquist--Luenberger account evaluated on APZ technologies, with the target observation's $g=(0,y,-b)$ direction. APZ does not alter a CFG component after solving. |
| **RTS** | CRS. Adding a convexity equation defines an unsupported variant and does not inherit this certificate. |
| **Data / time** | Matched environmental panel; componentwise strictly positive inputs and undesirable outputs, nonnegative desirable outputs, and two distinct contemporaneous technologies with their own cap vectors. |
| **Native score** | $ML=EC\times TC$, with values above one denoting improvement under the recorded convention; all four distance roles and the reconstruction residual remain visible. |
| **Exact aliases** | `productivity.malmquist_luenberger.apz` is a discovery-only lookup alias for the full canonical preset ID. APZ is not an alias for CFG ML, Oh GML, unrestricted bad-output disposal, or a sequential/biennial reference. |
| **Distinct variants** | Conventional CFG ML; Oh GML; alternative environmental technologies; VRS; global, sequential, or biennial references; slacks-based environmental productivity. |
| **Domain** | Every directional factor used by the multiplicative identity is positive and every required own-/cross-period APZ task is optimal. The period-$s$ peer data and cap must come from the same reference period. |
| **Failures** | Cross-period infeasibility is reduced, not eliminated; failed required tasks leave dependent components unavailable. Other invalid implementations include pooling caps across periods, collapsing several pollutants to one scalar cap, substituting a global reference, constraining the distance to be nonnegative, or applying a sign correction to CFG output. |
| **Solver form** | Four contemporaneous roles per adjacent transition: $d_t^t$, $d_t^{t+1}$, $d_{t+1}^t$, and $d_{t+1}^{t+1}$, each compiled with 2017 equation (6) and a free distance variable. |
| **Defining source** | Theory: [Aparicio, Pastor, and Zofío (2013)](https://doi.org/10.1016/j.ejor.2013.03.031). Operational equations: [Aparicio, Barbero, Kapelko, Pastor, and Zofío (2017)](https://doi.org/10.1016/j.jenvman.2017.03.007). |
| **Evidence status** | `primary-checked` for the 2013 consistency argument and 2017 equations (5)--(6); implemented/public on the source-qualified CRS domain. |
| **Oracle** | `analytically derived`: a production-free compiler gives exact Table 1 distances $2/5$, $3/11$, $3/5$, and $5/11$, hence $EC=77/80$, $TC=8/7$, and $ML=11/10$. The ordinary CFG reverse cross-task is infeasible on the same fixture, proving non-equivalence. This is not a reproduction of the 2017 WIOD country application. |
| **Package recipe** | `productivity.malmquist_luenberger.aparicio_pastor_zofio_2013`; public symbols `APZMalmquistLuenbergerProductivityIndex` and `APZMalmquistLuenbergerDEA`; source and oracle boundaries in `source_protocols/aparicio_pastor_zofio_2013.md` and `oracles/aparicio_pastor_zofio_2013.md`. |
| **Book location** | **Documentation/source review only.** The APZ source-qualified leaf does not receive independent handbook placement. |

#### A distinct question: when is one retrospective environmental benchmark appropriate?

Oh's GML solves a different problem. It uses a common full-sample
environmental technology, changing the information set and producing a
common-benchmark index. It does not use APZ's capped-bad technology or its
four off-diagonal contemporaneous roles.

| Evidence field | Record |
|---|---|
| **Economic question** | Did environmental performance improve relative to one fixed retrospective benchmark, and how did the own-period best-practice gap change? |
| **Technology / estimator** | CRS common-factor weak-disposal technology with null jointness and one full-sample pooled conical DEA envelope; this does not claim that a literal union equals its conical hull. |
| **Measure** | Four self-contained own/global distances; $BPG^r=(1+D^r)/(1+D^G)\leq1$, $BPC=BPG^{t+1}/BPG^t$, and $GML=EC\times BPC$. |
| **RTS** | CRS in the named Oh leaf. Non-CRS scale accounts do not inherit this certificate. |
| **Data / time** | Comparable environmental panel and one immutable retrospective full-sample vintage. Oh's identity is pairwise within that vintage; the package enumerates matched adjacent transitions. |
| **Native score** | GML, efficiency change, best-practice gaps, and best-practice change; values above one denote improvement under the recorded convention. |
| **Exact aliases** | None with APZ, standard ML, global ordinary Malmquist, or a biennial environmental index. |
| **Distinct variants** | Standard or APZ ML; literal-union estimation; biennial or sequential environmental productivity; alternative technologies or directions. |
| **Domain** | Global directions and pooled observations remain comparable; every own/global task is self-inclusive and nonnegative. |
| **Failures** | Calling GML “global Malmquist”; reporting the reciprocal $F^G/F^r$ as source BPG; treating adjacency as a theoretical restriction; equating a literal union with the pooled CRS cone; splicing results across global vintages; or importing APZ/CFG components. |
| **Solver form** | Four roles per transition: two own-period and two common-global DDF tasks, with no off-diagonal cross-period task. |
| **Defining source** | [Oh (2010)](https://doi.org/10.1007/s11123-010-0178-y). |
| **Evidence status** | `primary-checked`; bounded synthetic claims are `analytically derived`. |
| **Oracle** | An independent dense source-programme compiler and exact two-/three-period derivations close the four roles, nonnegative domain, BPG/BPC account, $GML=EC\times BPC$, fixed-vintage circularity, and coherent unit changes. The 26-country application is not reproduced. |
| **Package recipe** | `productivity.global_malmquist_luenberger.oh_2010`. The broader configurable global candidate remains deferred under `source_protocols/generic_environmental_directional_productivity.md`. |
| **Book location** | **Active core placement:** the common-reference environmental productivity policy is taught in `book/chapters/04-productivity/environmental-productivity-ml-common-reference.md`; source algebra remains in package documentation. |

An adjacent-pair environmental reference can be composed with a named
ML/SBM-ML operator, but `biennial` alone is not an environmental productivity
formula.

The current Oh certificate does not promote an arbitrary global environmental
productivity kernel. Literal-union estimation, VRS/NIRS/NDRS and scale
decompositions, alternative directions or bad-output technologies,
sequential/biennial/rolling/prospective references, arbitrary nonadjacent API
enumeration, signed or incomplete panels, and inferential, shadow-price,
welfare, abatement-cost, or causal claims remain
`deferred_to_next_version`.

## 5. Distinguishing technical-performance indicators from complete TFP

### 5.1 `productivity.hicks_moorsteen.bjurek_1996` — Is output quantity growth keeping ahead of input quantity growth?

Bjurek's index joins an output quantity comparison and an input quantity
comparison into a complete TFP ratio. It is often called Hicks--Moorsteen or
Moorsteen--Bjurek in later work. The source title's phrase “Malmquist total
factor productivity index” does not make it the ordinary one-orientation
Malmquist index.

| Evidence field | Record |
|---|---|
| **Economic question** | How much did total output quantity change relative to total input quantity between two observations, without treating an output-oriented distance alone as complete TFP? |
| **Technology / estimator** | Bjurek's source-defined input and output Malmquist quantity-index constructions over matched production-reference technologies; a DEA implementation estimates their component distance functions, while sampling inference remains separate. |
| **Measure** | Hicks--Moorsteen TFP index: the source-defined output quantity index divided by the source-defined input quantity index. |
| **RTS** | The component technologies and their reference convention are fixed by the source recipe and reported for every task. The output-over-input construction is intended for general production structures; completeness does not arise from silently imposing CRS or VRS. |
| **Data / time** | Two comparable multi-input/multi-output observations, normally from a panel with stable DMU identity and variable definitions; matched reference technologies and strictly valid component distance ratios. |
| **Native score** | Multiplicatively complete TFP index, output quantity index, input quantity index, reference-task metadata, and `reconstruction_residual`; values above one denote TFP improvement under the package convention. |
| **Exact aliases** | “Bjurek Malmquist TFP,” “Moorsteen--Bjurek,” and “Hicks--Moorsteen” are aliases only when they reproduce the same output-index/input-index formula, averaging, reference technologies, and score convention. Generic “Malmquist index” is not an alias. |
| **Distinct variants** | Caves/FGNZ oriented Malmquist; Lovell--Grifell-Tatjé generalized Malmquist; Färe--Primont; price-based Fisher or Törnqvist TFP; additive Luenberger--Hicks--Moorsteen. |
| **Domain** | Every input and output distance used by both component quantity indexes must be finite and strictly positive, and the two components must concern the same observation pair and compatible reference technologies. |
| **Failures** | Reporting one oriented Malmquist index as complete TFP; mixing input and output components from different reference policies; claiming transitivity for a bilateral chain without proof; importing an ordinary MPI decomposition; or averaging unit indexes into an industry index without an aggregation identity. |
| **Solver form** | Deduplicated graph of radial input- and output-distance LPs required by Bjurek's two quantity indexes, followed by deterministic ratio and reconstruction checks. |
| **Defining source** | [Bjurek (1996)](https://doi.org/10.2307/3440861); the distinction from the ordinary Malmquist index is reinforced by [Färe, Grosskopf, and Roos (1996)](https://doi.org/10.1016/S0165-1765(96)00929-9). |
| **Evidence status** | `primary-checked` and `implemented/public`; the executable leaf retains both contemporaneous technologies, all eight distance roles, the two quantity indexes, and the exact reconstruction identity. |
| **Oracle** | `analytically derived`; an independent dense VRS compiler imports no production package and checks all eight distances, both period-specific quantity views, $Q_y$, $Q_x$, $HM=Q_y/Q_x$, and reciprocal time reversal on an exact two-input/two-output fixture. No published empirical vector is claimed; see `source_protocols/bjurek_1996_hicks_moorsteen.md`. |
| **Package recipe** | `HicksMoorsteenProductivityIndex` (aliases `MoorsteenBjurekProductivityIndex`, `HicksMoorsteenDEA`, and `MoorsteenBjurekDEA`) as `productivity.hicks_moorsteen.bjurek_1996`; the source averaging rule, both reference technologies, component quantity indexes, and reconstruction metadata are retained. |
| **Book location** | **Active core placement:** `book/chapters/04-productivity/17-hicks-moorsteen.md`. |

### 5.2 `productivity.fare_primont.odonnell_2012` — How can TFP be compared consistently across many firms and periods?

The Färe--Primont construction uses fixed-reference input and output
aggregators. That common anchor supports multilateral and multi-period
comparisons and a source-specific efficiency decomposition. It is not a
transitive spelling of Hicks--Moorsteen.

| Evidence field | Record |
|---|---|
| **Economic question** | How can organizations and periods be placed on one consistent TFP scale, and how can differences be accounted for by source-defined technical, scale, and mix-efficiency terms without changing the benchmark between comparisons? |
| **Technology / estimator** | O'Donnell's aggregate-quantity framework instantiated with Färe--Primont input and output aggregator functions evaluated against one declared reference technology and fixed representative input/output vectors; a DEA implementation supplies the required distance estimates, with inference kept separate. |
| **Measure** | Fixed-reference output quantity index divided by the corresponding fixed-reference input quantity index, yielding a multiplicatively complete and transitive Färe--Primont TFP index under the source conditions. |
| **RTS** | Returns-to-scale assumptions for the reference technology and any auxiliary efficiency frontiers are explicit parts of the leaf. Transitivity comes from the common aggregator reference, not from choosing VRS or CRS as a display option. |
| **Data / time** | Comparable multi-input/multi-output observations across firms and periods, one immutable sample vintage, reference technology, reference period where used, and representative input/output vectors shared by all comparisons. Prices are not required for this quantity-index leaf. |
| **Native score** | Färe--Primont TFP level/index, output and input quantity indexes, fixed-reference identifiers, source-named technical/scale/mix efficiency components when requested, and a reconstruction residual. |
| **Exact aliases** | Only formulations using the same Färe--Primont aggregators, fixed reference, normalizations, and decomposition identity. Hicks--Moorsteen, ordinary or global Malmquist, Lowe, Fisher, and an arbitrary fixed-base ratio are not aliases. |
| **Distinct variants** | Alternative representative vectors or reference vintages; Hicks--Moorsteen; Lowe and price-based complete indexes; O'Donnell aggregate-industry measures; meta-frontier Färe--Primont; stochastic rather than DEA estimation. |
| **Domain** | The fixed reference must be admissible for every comparison, all required distance functions must be finite and positive, variable meanings and units must remain comparable, and every decomposition must reconstruct its parent index within tolerance. |
| **Failures** | Re-selecting the anchor for each pair while claiming transitivity; omitting reference-vintage metadata; treating optimized multipliers as observed market prices; reusing a Hicks--Moorsteen decomposition; averaging firm indexes into aggregate TFP; or attaching causal labels to accounting components. |
| **Solver form** | Compile the declared reference technology once, cache fixed-reference input and output distance tasks for all observations, construct the two aggregate quantity indexes, and apply only the source-qualified decomposition with an identity check. |
| **Defining source** | [O'Donnell (2012)](https://doi.org/10.1007/s11123-012-0275-1). |
| **Evidence status** | `final_primary_not_frozen`: an author working paper is available, but it has not been checked page-by-page against the final journal article and the complete executable equations/reference choices are not frozen. |
| **Oracle** | `located_not_reproduced`: the artificial-data example has been identified, but its full Färe--Primont vector has not been independently recomputed; DPIN feature descriptions are not a transparent task-level oracle. |
| **Package recipe** | Deferred to the next version with no public API or machine record; see `source_protocols/odonnell_2012_fare_primont.md`. `productivity.fare_primont` remains a discovery operator, not an executable promise. |
| **Book location** | **Evidence-deferred candidate.** Färe--Primont has no current handbook placement until its final-source, executable-formulation, and independent-oracle gates close. |

### 5.3 `productivity.luenberger_hicks_moorsteen.briec_kerstens_2004` — Can complete productivity change be expressed additively?

The Luenberger--Hicks--Moorsteen indicator combines output and input quantity
change in an additive account. It is not the ordinary Luenberger indicator
with a longer name: the input and output components and their common
directional units are part of its definition.

| Evidence field | Record |
|---|---|
| **Economic question** | By how much did aggregate output improvement exceed aggregate input growth in the units of a declared directional quantity account? |
| **Technology / estimator** | Briec--Kerstens source-defined directional output and input quantity constructions over matched reference technologies; DEA directional-distance estimators can supply the component tasks, while sampling inference remains separate. |
| **Measure** | Difference-based Luenberger--Hicks--Moorsteen indicator: the source output quantity indicator minus the corresponding input quantity-change account. |
| **RTS** | The reference technologies and any homotheticity conditions used for comparisons with other indicators are recorded explicitly. Equality with an ordinary one-sided Luenberger indicator cannot be obtained by changing a generic RTS option. |
| **Data / time** | Comparable multi-input/multi-output observations and reference technologies, plus input and output directions whose units and scaling make the two additive accounts economically interpretable. |
| **Native score** | Additively complete LHM indicator, separate output and input quantity-change components, direction/reference metadata, and an additive reconstruction residual; positive values denote productivity improvement under the recorded convention. |
| **Exact aliases** | None with ordinary Luenberger, Hicks--Moorsteen ratio, Bennet indicator, or Malmquist. The source establishes relationships and approximations, not unconditional identity. |
| **Distinct variants** | Ordinary input- or output-oriented Luenberger; environmental LHM; alternative base/reference symmetrizations; price-normalized Bennet/Luenberger accounts; ratio-based Hicks--Moorsteen. |
| **Domain** | Both directional quantity components must be determinate and finite, their directions must be comparable across observations and time, and the output-minus-input reconstruction must hold in declared units. |
| **Failures** | Adding components expressed under different directions or reference technologies; omitting one side of the complete account; treating the approximation to the logarithm of Hicks--Moorsteen as equality; claiming equivalence with ordinary Luenberger outside the source conditions; or suppressing a reconstruction residual. |
| **Solver form** | Paired directional input and output task graph under the source reference policy, followed by deterministic additive reconstruction and determinateness checks. |
| **Defining source** | [Briec and Kerstens (2004)](https://doi.org/10.1007/s00199-003-0403-2); later determinateness comparison in [Briec and Kerstens (2011)](https://doi.org/10.1111/j.1467-9957.2010.02169.x). |
| **Evidence status** | `primary-checked` for the additive output-minus-input identity and its distinction from ordinary Luenberger and Hicks--Moorsteen; registry-provisional/planned pending an executable formulation audit. |
| **Oracle** | `not located` — no published numerical vector or independent implementation has been certified as an automated DEAPack oracle. |
| **Package recipe** | Planned `productivity.luenberger_hicks_moorsteen.briec_kerstens_2004`, with compatible input/output directions, source reference policy, completeness metadata, and reconstruction diagnostics. |
| **Book location** | **Documentation/source review only.** The Luenberger--Hicks--Moorsteen extension has no independent placement in the current handbook. |

### 5.4 Do prices make the question profitability rather than technical productivity?

Cost, revenue, profit, and profitability change use valuation information
that a technical distance does not contain. A price vector determines how
heterogeneous inputs and outputs are aggregated and which substitution is
valuable. Price deflation, base period, common versus firm-specific prices,
and observed versus normative values are therefore part of the estimand.

| Evidence field | Record |
|---|---|
| **Economic question** | Did the producer create more economic value per resource cost, and how much change is associated with quantities, prices, technical performance, or allocative choices? |
| **Technology / estimator** | Period/reference production technologies combined with explicit input and output price policies. |
| **Measure** | Cost Malmquist, revenue/profit productivity, profitability change, or another source-qualified complete price/quantity identity. |
| **RTS** | Explicit in every technical component; economic optimum and scale interpretation may differ under CRS and VRS. |
| **Data / time** | Quantity panel plus price vectors, currency/deflator, price vintage, tax/subsidy treatment, and common versus DMU-specific valuation policy. |
| **Native score** | Source-defined monetary or multiplicative profitability/productivity index and its price/quantity components. |
| **Exact aliases** | None between technical productivity, profit change, and profitability change. |
| **Distinct variants** | Cost Malmquist; Bennet price/quantity indicators; O'Donnell profitability decomposition; Zhao--Morita--Maruyama profit-ratio change; profit and revenue productivity; price-index-number decompositions. |
| **Domain** | Comparable monetary units and economically admissible prices; zero or negative profits require a source-compatible non-ratio formulation. |
| **Failures** | Mixing nominal prices across periods; using shadow prices as observed prices; undefined ratios for zero/negative value; calling allocative change technical change. |
| **Solver form** | Cost/revenue/profit LP task graph plus external price-index accounting; exact form is source specific. |
| **Defining source** | Index-number foundation in [Caves, Christensen, and Diewert (1982)](https://doi.org/10.2307/1913388); directional exact measurement in [Chambers (2002)](https://doi.org/10.1007/s001990100231); profitability decomposition in [O'Donnell (2010)](https://doi.org/10.1111/j.1467-8489.2010.00512.x); profit-ratio change in [Zhao, Morita, and Maruyama (2019)](https://doi.org/10.1016/j.omega.2018.09.012); broader complete framework in [O'Donnell (2012)](https://doi.org/10.1007/s11123-012-0275-1). |
| **Evidence status** | `review-supported`; the O'Donnell and Zhao--Morita--Maruyama source leaves are planned/evidence candidates, and each executable economic productivity leaf requires its own primary-source identity. |
| **Oracle** | `not located`; current static cost/revenue oracles do not certify an intertemporal productivity operator. |
| **Package recipe** | Planned `productivity.cost_malmquist` or `productivity.price_quantity_complete` + explicit price policy and decomposition leaf. Initial evidence candidates are *productivity.profitability_decomposition.odonnell_2010* and *productivity.profit_ratio_change.zhao_morita_maruyama_2019*; both occupy $V/A$, are Level D versus technical MPI and each other, and do not claim implementation. |
| **Book location** | **Documentation/source review only.** Price-based productivity leaves have no current handbook placement. |

### 5.5 When must productivity retain productive state?

The planned candidates
*dynamic.productivity.malmquist.intertemporal_fare_grosskopf* and, after
equation audit,
*dynamic.productivity.malmquist.dynamic_sbm.tone_tsutsui* preserve
capital/carry-over state in every component task. They occupy $G,T,R,A$ and
are Level D versus repeated-static MPI, window efficiency, and a global
reference technology with no transition equation. A source-specific
system/period reconstruction is mandatory; no implementation is claimed.
Evidence begins with
[Färe and Grosskopf
(1996)](https://doi.org/10.1007/978-94-009-1816-0),
[Färe and Grosskopf
(2010)](https://doi.org/10.1007/978-1-4419-6151-8_5),
[Tone and Tsutsui
(2014)](https://doi.org/10.1002/9781118946688.ch8), and
[Weber (2016)](https://doi.org/10.1093/oxfordhb/9780190226718.013.5).

## 6. Moving from firms to groups, industries, and technology gaps

### 6.1 Is the question heterogeneity, aggregation, or reallocation?

Meta-frontier productivity compares group-specific opportunities with a
cross-group meta-technology. Aggregate productivity asks how group output and
input quantities change under an aggregation identity. Reallocation analysis
asks what could change if resources move between firms. These questions may
use some common distance tasks but they do not share one group-productivity
score.

| Evidence field | Record |
|---|---|
| **Economic question** | Did productivity change because group opportunities changed, because the gap to a meta-technology changed, because the aggregate input/output mix changed, or because resources were reallocated between units? |
| **Technology / estimator** | Group technologies plus a declared non-convex union, pooled convex, or other source-qualified meta-technology; alternatively an aggregate production and resource-allocation technology. |
| **Measure** | Technology-gap/productivity decomposition, economically weighted aggregate index, or group-potential/reallocation operator. |
| **RTS** | Declared for group, meta, and aggregate technologies separately. |
| **Data / time** | Panel with stable group membership or an explicit transition policy; aggregation weights and resource-transfer assumptions; common variables and prices where required. |
| **Native score** | Source-specific group/meta multiplicative components, aggregate productivity index, or reallocation contribution. No simple average is promoted to the native aggregate by default. |
| **Exact aliases** | None among meta-frontier productivity, weighted index aggregation, and reallocation potential. |
| **Distinct variants** | Non-convex union versus pooled convex meta-technology; fixed versus changing groups; geometric versus economic aggregation; unrestricted versus constrained reallocation; Kumar--Russell growth accounting. |
| **Domain** | Comparable missions and variables across groups; identified aggregation weights; defensible resource mobility; decomposition reconstructs its parent quantity. |
| **Failures** | Convexifying across incompatible groups without disclosure; interpreting a geometric mean of unit indexes as aggregate productivity; attributing hypothetical reallocation gains to observed management; unstable group definitions. |
| **Solver form** | Group/meta task DAG; aggregation algebra; potentially a separate allocation LP for reallocation potential. |
| **Defining source** | Firm-level meta-frontier in [O'Donnell, Rao, and Battese (2008)](https://doi.org/10.1007/s00181-007-0119-4); complete aggregate-quantity framework in [O'Donnell (2012)](https://doi.org/10.1007/s11123-012-0275-1). |
| **Evidence status** | `review-supported`; source-qualified decomposition and reallocation leaves remain to be frozen. |
| **Oracle** | `not located`; no current aggregate/meta/reallocation operator has a certified DEAPack literature oracle. |
| **Package recipe** | `productivity.metafrontier`, `productivity.aggregate_mpi`, or `productivity.group_reallocation`, never one `group_productivity=True` flag. |
| **Book location** | **Active core placement:** the transferable group/meta-technology distinction is taught in `book/chapters/07-heterogeneity/23-metafrontier.md`; productivity decompositions, aggregation, and reallocation remain in package documentation and source review. |

## 7. Merge boundary

### Safe unification

| Shared mechanism | Safe reuse | Information that must remain visible |
|---|---|---|
| Repeated static evaluation | One distance-task DAG | evaluated observation, reference technology, orientation/direction, RTS |
| Period technologies | Fingerprinted compiled sparse matrices | sample vintage, hull construction, disposal, estimator |
| Adjacent radial indexes | Radial component-task compiler | index formula, input/output orientation, decomposition leaf |
| Common-reference indexes | Pooled-reference builder and distance cache | global versus biennial membership and retrospective status |
| Directional indicators | DDF task compiler | direction units, additive versus multiplicative operator |
| Complete quantity indexes | Input/output aggregator tasks | aggregator identity, reference, completeness conditions |
| Decompositions | Common reconstruction checker | exact source component names and algebra |

### Never merge silently

- Adjacent Malmquist, global Malmquist, and biennial Malmquist use different
  reference information and are not aliases.
- `global`, `sequential`, `biennial`, and `window` identify reference
  policies, not standalone productivity formulas.
- comparison population, temporal information set, evaluation exclusions,
  and fitted peer/reference sets are four different objects.
- “Generalized Malmquist” is the Lovell--Grifell-Tatjé scale/quantity-index
  construction; it is not global Malmquist or a generalized distance.
- Quasi-Malmquist and SBM Malmquist are not generic names for any non-radial
  change measure.
- The FGNZ core is a fixed output-oriented CRS preset of the shared adjacent
  Malmquist operator; its enhanced pure-efficiency/scale extension,
  Ray--Desli, Balk, and O'Donnell retain distinct components and
  reconstruction identities.
- Ordinary Luenberger is an additive directional performance indicator;
  Luenberger--Hicks--Moorsteen is a separate complete output-minus-input
  construction.
- Malmquist and Hicks--Moorsteen coincide only under restrictive conditions;
  neither is an unconditional alias for Färe--Primont.
- Standard ML, APZ, Oh GML, biennial ML, and SBM-ML differ in technology,
  reference, measure, or accounting rule.
- Technical change, profitability change, group technology-gap change, and
  resource-reallocation change are different economic claims.
- An arithmetic or geometric average of firm indexes is not aggregate
  productivity without an aggregation identity.

## 8. Package and book consequences

The productivity implementation should be an orchestration layer over static
measures:

```text
analysis/productivity/
    task_graph.py
    references.py
    malmquist.py
    directional.py
    environmental.py
    complete.py
    decompositions.py
    aggregate.py
```

Every result should store:

```text
observation periods and pairing
reference policy and exact hull construction
technology, estimator, RTS, and disposal
measure, orientation/direction, and native score
operator ID and completeness status
decomposition leaf ID and reconstruction residual
sample vintage and unbalanced-panel policy
verification/oracle status
```

The active handbook route develops its retained core families gradually:
conventional reference-information comparisons, the additive Luenberger
account, environmental productivity, and Hicks--Moorsteen. This review does
not reserve space for the remaining source leaves. Their algebra,
decompositions, and validation records remain in package documentation and
source-review materials unless they later pass the handbook admission gate.

## 9. Source map

### Distance-based and reference-based change

- Caves, Christensen, and Diewert (1982), economic theory of input, output,
  and productivity indexes, [DOI](https://doi.org/10.2307/1913388).
- Färe, Grosskopf, Norris, and Zhang (1994), DEA Malmquist computation and
  decomposition, [DOI](https://doi.org/10.2307/2117971).
- Chambers (2002), exact non-radial and directional productivity
  measurement, [DOI](https://doi.org/10.1007/s001990100231).
- Pastor and Lovell (2005), global Malmquist,
  [DOI](https://doi.org/10.1016/j.econlet.2005.02.013).
- Pastor, Asmild, and Lovell (2011), biennial Malmquist,
  [DOI](https://doi.org/10.1016/j.seps.2010.09.001).

### Competing decompositions and complete accounts

- Ray and Desli (1997), source-qualified VRS decomposition,
  [authoritative PDF](https://file.lianxh.cn/Refs/TE/Zhang/Ray_Desli_1997.pdf).
- Balk (2001), scale and mix decomposition,
  [DOI](https://doi.org/10.1023/A:1011117324278).
- Grifell-Tatjé, Lovell, and Pastor (1998), quasi-Malmquist,
  [DOI](https://doi.org/10.1023/A:1018329930629).
- Lovell and Grifell-Tatjé (1999), generalized Malmquist,
  [DOI](https://doi.org/10.1007/BF02564713).
- Bjurek (1996), source-defined output-quantity/input-quantity TFP ratio,
  [DOI](https://doi.org/10.2307/3440861).
- Briec and Kerstens (2004), Luenberger--Hicks--Moorsteen,
  [DOI](https://doi.org/10.1007/s00199-003-0403-2).
- O'Donnell (2012), fixed-reference Färe--Primont within the multiplicatively
  complete aggregate-quantity framework and its decompositions,
  [DOI](https://doi.org/10.1007/s11123-012-0275-1).

### Environmental productivity

- Chung, Färe, and Grosskopf (1997), Malmquist--Luenberger,
  [DOI](https://doi.org/10.1006/jema.1997.0146).
- Oh (2010), global Malmquist--Luenberger,
  [DOI](https://doi.org/10.1007/s11123-010-0178-y).
- Aparicio, Pastor, and Zofío (2013), consistency correction,
  [DOI](https://doi.org/10.1016/j.ejor.2013.03.031).
- Aparicio, Barbero, Kapelko, Pastor, and Zofío (2017), operational APZ
  technology and feasibility tests,
  [DOI](https://doi.org/10.1016/j.jenvman.2017.03.007).
