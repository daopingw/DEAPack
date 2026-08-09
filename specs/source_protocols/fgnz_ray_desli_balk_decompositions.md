# FGNZ, Ray--Desli, and deferred Balk productivity decompositions

## Readiness record

| Field | State |
|---|---|
| Current-release identities | preset `productivity.malmquist.decomposition.fgnz_core`; methods `productivity.malmquist.decomposition.fgnz_pure_scale_extension` and `productivity.malmquist.decomposition.ray_desli` |
| Deferred identifier | `productivity.malmquist.decomposition.balk` |
| Primary theoretical sources | complete, checksum-audited texts for FGNZ and Ray--Desli; Balk citation identified but no auditable full text retained in the current evidence bundle |
| Original FGNZ empirical panel | `not_frozen` |
| Published preprocessing protocol | `not_frozen` |
| Independent exact numerical oracle | `analytically_derived` for the output-oriented CRS FGNZ core, the six-task enhanced FGNZ account, and the output-oriented one-desirable-output Ray--Desli VRS decomposition; `not_located` for Balk |
| Implementation status | FGNZ core, enhanced FGNZ, and Ray--Desli are independently validated and implemented; Balk remains behind `deferred_source_and_oracle_gate` |
| Release disposition | FGNZ core, enhanced FGNZ, and the narrow one-output Ray--Desli leaf are current/public; Balk is `deferred_to_next_version` |
| Public API | `FGNZMalmquistProductivityIndex` / `FGNZMalmquist`; `FGNZEnhancedMalmquistProductivityIndex` / `FGNZEnhancedMalmquist`; `RayDesliMalmquistProductivityIndex` / `RayDesliMalmquist` |
| Registry status | FGNZ core is a public catalog `preset_id` over the four-task parent; enhanced FGNZ is a separate six-task public `method_id`; Ray--Desli is a separate eight-task public `method_id`. Both decomposition methods share the internal CRS distance engine but retain distinct VRS task graphs, component allocations, and failure contracts |
| Last access audit | 2026-07-31 |

The FGNZ and Ray--Desli primary texts are available in full and have retained
checksums and page-level audits. The Balk citation is known, but no complete
auditable copy is present in the current evidence bundle; its literature gate
therefore remains open. An independent exact four-task oracle closes the
narrow output-oriented CRS FGNZ core account
$M=\mathrm{EFFCH}\times\mathrm{TECHCH}$. That account is a source-qualified
fixed configuration of the already public adjacent geometric Malmquist
operator, so it is registered as a `preset_id`, not as a second solver or a
duplicate machine method. Calling the generic constructor with matching
numerical options does not add this provenance identity.

This closure is deliberately claim-scoped. A separate six-task source-only
oracle now certifies the enhanced FGNZ pure-efficiency/scale account, while a
second independent dense oracle and public-API comparison certify
Ray--Desli's alternative VRS account on its one-desirable-output domain. The
independent evidence does not define or certify a Balk scale/mix account.
Separately, neither the original FGNZ Penn World Table 5 panel nor
the updated Penn World Tables 5.6 panel used by Ray--Desli has been frozen
with its preprocessing. The package therefore does not claim to reproduce
either empirical application.

The current release must not infer any component from a residual or treat
agreement with the parent Malmquist index as evidence that different
decompositions allocate technical and scale change identically.

## 1. Defining sources

The source set is:

1. Rolf Färe, Shawna Grosskopf, Mary Norris, and Zhongyang Zhang (1994),
   “Productivity Growth, Technical Progress, and Efficiency Change in
   Industrialized Countries,” *American Economic Review*, 84(1), 66--83.
   [DOI](https://doi.org/10.2307/2117971).
2. Subhash C. Ray and Evangelia Desli (1997), “Productivity Growth, Technical
   Progress, and Efficiency Change in Industrialized Countries: Comment,”
   *American Economic Review*, 87(5), 1033--1039.
3. Bert M. Balk (2001), “Scale Efficiency and Productivity Change,” *Journal
   of Productivity Analysis*, 15, 159--183.
   [DOI](https://doi.org/10.1023/A:1011117324278). This is a bibliographic
   locator only: the current evidence bundle does not contain a complete
   checksum-audited text, so no equation-level claim below is attributed to
   it.

These papers define related but non-equivalent accounting systems. Their
shared use of distance functions, period technologies, or the word “scale”
does not establish an alias.

## 2. Three identities, not one generic scale decomposition

### 2.1 FGNZ

The core FGNZ account decomposes the output-oriented CRS radial Malmquist
productivity index as

$$
M = \mathrm{EFFCH}\times\mathrm{TECHCH}.
$$

DEAPack exposes this exact configuration through
`productivity.malmquist.decomposition.fgnz_core`, implemented by
`FGNZMalmquistProductivityIndex` (alias `FGNZMalmquist`). The result retains
the shared method identity
`productivity.malmquist.adjacent_geometric` and adds the preset identity; the
four distances, `efficiency_change`, `technical_change`, and reconstruction
residual remain the shared result contract.

The enhanced FGNZ account further separates the operating-performance term
using VRS auxiliary tasks and the source-defined pure-efficiency and
scale-efficiency ratios:

$$
\mathrm{EFFCH}=\mathrm{PEFFCH}\times\mathrm{SCH},
\qquad
M=\mathrm{PEFFCH}\times\mathrm{SCH}\times\mathrm{TECHCH}.
$$

The second identity is not part of the four-task core preset. It is exposed as
the distinct public method
`productivity.malmquist.decomposition.fgnz_pure_scale_extension`, whose four
CRS plus two own-period VRS task graph, exact analytical oracle, and failure
boundary are documented in the
[dedicated protocol](fare_etal_1994_enhanced_fgnz.md). The core identity alone
is not permission to compute every later paper's scale contribution as
`EFFCH / PEFFCH`, nor does it make an arbitrary VRS distance combination a
complete productivity account.

### 2.2 Ray--Desli

Ray--Desli gives an alternative VRS-based account. Its component definitions
and allocation of technical and scale change differ from the FGNZ
pure-efficiency/scale extension. The exact source freeze below is based on
pp. 1034--1037 and equations (4)--(16) of the complete article.

#### 2.2.1 Exact domain and distance convention

The paper develops the geometry for one input and one output, then estimates
its application with two inputs and one desirable output. Footnote 3 on
p. 1034 warns that average productivity does not apply in the
multiple-input, multiple-output case and that the results cannot necessarily
be generalized. The frozen executable domain is therefore:

- a matched adjacent-period panel with the same DMUs and input variables;
- one or more strictly positive inputs and **exactly one** strictly positive
  desirable output;
- output orientation only; and
- separate period technologies under both CRS and VRS.

Arbitrary multiple-output, input-oriented, undesirable-output, unbalanced,
zero-valued, or negative-valued cases are not certified by this source leaf.

Let $z_q=(x_q,y_q)$ denote one DMU's bundle observed in target period
$q\in\{t,t+1\}$. Let $D_C^r(z_q)$ and $D_V^r(z_q)$ be its output distance
from the technology observed in reference period
$r\in\{t,t+1\}$ under CRS and VRS, respectively. These are
reciprocal-expansion Shephard output distances; for a feasible within-period
observation, a larger value means closer to the frontier. They are estimated
as the reciprocal of the maximum radial output expansion:

$$
D_R^r(x_q,y_q)=\frac{1}{\max_{\phi,\lambda}\phi},
$$

subject to

$$
X^r\lambda\le x_q,\qquad
Y^r\lambda\ge\phi y_q,\qquad \lambda\ge0,
$$

with $\mathbf 1^T\lambda=1$ only for $R=V$; CRS has no convexity equation.
The paper states on p. 1037 that the own- and cross-period output distances
are obtained from the corresponding DEA linear programmes. Within-period
distances are positive and no greater than one because the evaluated row is
in its own reference technology. A feasible cross-period distance can exceed
one.

Strictly positive finite data and a positive finite expansion factor are
required because the equations divide and take square roots of distances.
The independent oracle treats any non-optimal CRS task, nonpositive distance,
or invalid denominator as a hard failure.

#### 2.2.2 Eight-task matrix

Each DMU transition requires four target/reference roles under each of two
returns-to-scale assumptions:

| Reference technology | Target $z_t$ | Target $z_{t+1}$ |
|---|---|---|
| period $t$ | `base_on_base` | `comparison_on_base` |
| period $t+1$ | `base_on_comparison` | `comparison_on_comparison` |

The complete numerical evidence must therefore retain these matrices rather
than only their products:

$$
\mathcal D_R=
\begin{bmatrix}
D_R^t(z_t)&D_R^t(z_{t+1})\\
D_R^{t+1}(z_t)&D_R^{t+1}(z_{t+1})
\end{bmatrix},\qquad R\in\{C,V\}.
$$

Calling the account “VRS-based” does not replace the CRS matrix. The
Malmquist index itself remains the geometric mean of the two CRS-reference
comparisons, as Ray--Desli emphasize on pp. 1033--1034. VRS distances define
the alternative allocation between technical, pure-efficiency, and scale
change.

#### 2.2.3 Scale efficiency and the source identity

Equations (8)--(9), written for every reference/target role needed below,
define scale efficiency as

$$
SE^r(z_q)=\frac{D_C^r(z_q)}{D_V^r(z_q)}.
$$

Equations (6)--(7) and their geometric mean give the CRS Malmquist
productivity index

$$
\Pi=
\left[
\frac{D_C^t(z_{t+1})}{D_C^t(z_t)}
\frac{D_C^{t+1}(z_{t+1})}{D_C^{t+1}(z_t)}
\right]^{1/2}.
$$

Ray--Desli then decompose the VRS-distance factor in equation (12). Their
native component labels and equations (14)--(16) are

$$
\operatorname{TECHCH}(v)=
\left[
\frac{D_V^t(z_t)}{D_V^{t+1}(z_t)}
\frac{D_V^t(z_{t+1})}{D_V^{t+1}(z_{t+1})}
\right]^{1/2},
$$

$$
\operatorname{PEFFCH}=
\frac{D_V^{t+1}(z_{t+1})}{D_V^t(z_t)},
$$

and

$$
\operatorname{SCH}(v)=
\left[
\frac{SE^t(z_{t+1})}{SE^t(z_t)}
\frac{SE^{t+1}(z_{t+1})}{SE^{t+1}(z_t)}
\right]^{1/2}.
$$

Equation (13) is the mandatory multiplicative reconstruction:

$$
\Pi=
\operatorname{TECHCH}(v)\times
\operatorname{PEFFCH}\times
\operatorname{SCH}(v).
$$

The source calls the last factor `SCH(v)`, not a generic `SCH` or a residual
`SECH`. It is a Fisher-like geometric mean using both period technologies as
benchmarks. It is not the simple change between the two own-period scale
efficiencies.

All four reported change factors use the greater-than-one-is-improvement
direction: $\Pi>1$ is productivity growth,
$\operatorname{TECHCH}(v)>1$ is technical progress,
$\operatorname{PEFFCH}>1$ is improved pure technical efficiency, and
$\operatorname{SCH}(v)>1$ is a positive scale-efficiency contribution. Values
below one indicate the corresponding regress or deterioration. This
direction must not be reciprocated in storage or presentation.

#### 2.2.4 Cross-period infeasibility and partial accounts

Page 1037 explicitly states that some cross-period VRS programmes can be
infeasible. Table 1 preserves Ireland's CRS Malmquist index and its pure
technical-efficiency index of 1.00000 while printing “infeasible solution”
for technical change and scale efficiency. The source-backed failure account
is therefore component-specific:

- the four feasible CRS tasks still define $\Pi$;
- the two own-period VRS tasks still define `PEFFCH`;
- either missing VRS cross task makes `TECHCH(v)`, `SCH(v)`, and their
  multiplicative reconstruction undefined; and
- an implementation must preserve an explicit infeasible status and must not
  substitute a CRS value, perturb the data, pool periods, or impute one.

The public API exposes this source-backed partial row: it retains the CRS
productivity change and own-period `pure_efficiency_change`, leaves
`vrs_technical_change`, `ray_desli_scale_change`, and reconstruction missing,
and reports `decomposition_status="vrs_cross_infeasible"`. It never returns
fabricated finite values for the two undefined components.

#### 2.2.5 Non-equivalence to FGNZ

Ray--Desli state that `PEFFCH` is the only component identical to the FGNZ
extended decomposition. FGNZ technical change uses the corresponding CRS
frontier-shift ratios, while FGNZ scale change is the own-period ratio
$SE^{t+1}(z_{t+1})/SE^t(z_t)$. Ray--Desli instead use the two VRS formulas
above. Agreement of the final Malmquist product is therefore not evidence of
component equivalence.

The independent source-only oracle in
`tests/test_ray_desli_1997_source_reproduction.py` compiles all eight dense
distance tasks on a strictly positive four-DMU panel, verifies every source
component and reconstruction, and produces values that differ materially
from the FGNZ allocation. Its evidence record is
`specs/oracles/ray_desli_1997_vrs_decomposition.md`. Neither file imports or
calls production DEAPack code.

The Ray--Desli result uses `pure_efficiency_change`,
`vrs_technical_change`, and `ray_desli_scale_change` in its own result
namespace. It does not populate the FGNZ `SCH` field merely because both
accounts discuss returns to scale, and it is not a cosmetic relabeling of the
FGNZ decomposition.

### 2.3 Balk candidate: not source-frozen

Reviews and the bibliographic map identify Balk (2001) as a neighboring
scale/productivity decomposition, but the complete defining text is not
available in the current auditable evidence bundle. DEAPack therefore freezes
no Balk headline index, component formula, task count, RTS assignment, data
domain, failure rule, or result field in this version. In particular, phrases
such as “bottom-up,” “complete,” “scale,” or “mix” are discovery prompts, not
an executable contract.

A future source audit must determine the native identity and component names
before any comparison is made. Until then, no candidate Balk term may be
merged with FGNZ `SCH`, Ray--Desli `SCH(v)`, or a generic `scale_change`
column, and no shared-compiler relation may be inferred from a title or a
secondary summary.

## 3. Current boundary and gated leaves

The current release exposes three identities and leaves Balk for a later
version:

| Leaf | Current disposition and minimum scope |
|---|---|
| `productivity.malmquist.decomposition.fgnz_core` | **Current/public preset:** output orientation, CRS, adjacent contemporaneous references, and the exact $M=\mathrm{EFFCH}\times\mathrm{TECHCH}$ account |
| `productivity.malmquist.decomposition.fgnz_pure_scale_extension` | **Current/public method:** output orientation; four CRS plus two own-period VRS tasks; exact $\mathrm{EFFCH}=\mathrm{PEFFCH}\times\mathrm{SCH}$ and $M=\mathrm{TECHCH}_C\times\mathrm{PEFFCH}\times\mathrm{SCH}$ oracles; a strict-positive matched-panel source certificate plus tested package extensions for partial-zero cells with positive row aggregates and explicit unbalanced `drop`/`raise` policies |
| `productivity.malmquist.decomposition.ray_desli` | **Current/public method:** output orientation, a balanced strictly positive panel with exactly one desirable output, four CRS plus four VRS distance roles, native `TECHCH(v)`, `PEFFCH`, and `SCH(v)`, source-backed partial results under VRS cross infeasibility, and independent source-only and public-API oracles |
| `productivity.malmquist.decomposition.balk` | **Deferred to the next version:** bibliographic candidate only; complete defining text, equation/task freeze, native component names, domain, and independent oracle are unavailable in the current evidence bundle |

The first three rows are public catalog identities; the enhanced FGNZ and
Ray--Desli rows also have their own machine records. The fourth is a deferred
research plan. These leaves must not inherit one generic `scale_change`
schema. FGNZ and Ray--Desli may share period-reference and radial-template
compilation internally, but retain their distinct task, identity, and result
contracts.

## 4. Exact evidence and test obligations

The current FGNZ core satisfies the equation, task, exact-oracle,
reconstruction, domain, and reproducibility obligations below within its
recorded output-oriented CRS scope. Enhanced FGNZ now satisfies items 1--7
through a separate six-task production-free certificate and has independently
passed its production gate. Ray--Desli has frozen equations, all eight tasks, component
identities, failure semantics, and both an independent source-only oracle and
a public-API comparison on its narrower one-desirable-output domain. The full
three-way comparison in item 5 remains a possible later Balk obligation whose
exact form must first be supported by the defining text. Balk must satisfy
items 1--7 before it becomes executable. Item
8 is an additional gate for any claim that an original empirical application
has been reproduced.

1. **Freeze each equation transcription.** Page-check orientations, distance
   conventions, period and reference superscripts, CRS/VRS technology
   choices, geometric means, scale or mix definitions, admissible domains,
   and reciprocal transformations against each primary text.
2. **Build an independent oracle.** Construct a small exact rational panel
   whose component distances and source-defined decompositions can be solved
   by hand or by a separately written equation compiler. A plausible
   ranking, a reconstructed final product alone, or agreement between two
   paths sharing the same compiler is insufficient.
3. **Test the task matrix.** Check every within-period and cross-period
   distance used by a leaf before checking the composite result. Where a
   source uses both CRS and VRS evaluations, both sets must be independently
   asserted.
4. **Test every identity component-wise.** The FGNZ core, enhanced FGNZ, and
   source-only plus public Ray--Desli identities are checked separately. A
   future release must independently verify whatever native Balk identity the
   complete defining text establishes, with no silent residual.
5. **Prove non-equivalence.** If the complete Balk text establishes a
   comparable scale-related account, include at least one discriminating
   panel on which its native quantity differs from enhanced FGNZ and
   Ray--Desli. Tests must fail if distinct source terms are routed into one
   formula or one generic `scale_change` field.
6. **Exercise domain failures.** Cover cross-period infeasibility, zero or
   invalid denominators, unmatched panel observations, missing variables,
   orientation-convention mistakes, and violated completeness assumptions.
   Failures must be reported rather than numerically patched.
7. **Certify reproducibility.** Record solver tolerances, deterministic
   ordering, reconstruction residuals, fixture provenance, and acceptable
   error bounds so that a second implementation can repeat the comparison.
8. **Gate any empirical-reproduction claim.** Preserve an authorized copy
   and checksum of the exact Penn World Table 5 vintage used by FGNZ, identify
   the sample, years, variables, units, missing-data policy, country matching,
   and every transformation from raw records to production observations;
   then reproduce the relevant published table. Without this item the method
   may eventually be source-qualified through items 1--7, but it must not be
   described as reproducing the original application.

Only after these obligations pass **and** a separate production milestone is
authorized should a candidate receive a catalog entry, public class, result
extension, book recipe, or API reference. Enhanced FGNZ and Ray--Desli passed
both gates. Each receives a separate machine record because its executable
composition adds a distinct VRS task graph and allocation rather than merely
naming a fixed parameter preset over the four-task Malmquist core. Balk has
passed neither complete source nor production gates and remains deliberately
absent from the public API and registry. The original OECD/PWT5 empirical
reproductions also remain outside the current claim.
