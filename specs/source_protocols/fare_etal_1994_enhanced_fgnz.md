# Färe et al. (1994) enhanced Malmquist decomposition source protocol

## Readiness record

| Field | State |
|---|---|
| Current method identity | `productivity.malmquist.decomposition.fgnz_pure_scale_extension` |
| Defining source | Färe, Grosskopf, Norris, and Zhang (1994), *American Economic Review* 84(1), 66--83 |
| Full primary text | obtained and visually page-checked |
| Audited PDF SHA-256 | `bfc1fb7b305f91958e34b74fc3e1a49d2efac501c38d88a623f6a005d028dad0` |
| Equation and task semantics | source-frozen on pp. 70--75, including footnotes 14--17 |
| Independent oracle | `analytically_derived`; no production code reused |
| Published empirical reproduction | **no** |
| Source-gate disposition | passed for the narrow six-task account below |
| Production disposition | independently validated, implemented, and public |
| Last source audit | 2026-07-31 |

The primary text is sufficient to close the enhanced decomposition. The
source defines an output-oriented CRS Malmquist account, then uses exactly two
additional own-period VRS programmes to divide CRS efficiency change into
pure-efficiency and scale-efficiency change. No formula has to be inferred
from a secondary source.

This pass does **not** reproduce the article's OECD/Penn World Table 5
application. It certifies the equations and their executable task graph on a
small independent panel. The empirical sample, vintage, transformations,
missing-data decisions, country results, and published tables remain outside
the current-version claim.

## 1. Primary evidence and page audit

The complete local source audited for this record is Färe, Grosskopf, Norris,
and Zhang, "Productivity Growth, Technical Progress, and Efficiency Change in
Industrialized Countries," *American Economic Review* 84(1), 66--83,
[DOI 10.2307/2117971](https://doi.org/10.2307/2117971).

The relevant pages were rendered and inspected at full-page resolution:

| Source location | Evidence frozen here |
|---|---|
| p. 70, equations (4)--(6) | output-oriented distance convention and geometric CRS Malmquist index |
| p. 71, equation (7) | CRS efficiency-change and technical-change factors, their product identity, and the greater-than-one direction |
| p. 73, equations (14)--(15), footnotes 14--15 | CRS reference technology, optional NIRS/VRS restrictions, positive empirical data, zero-value qualification, unmatched observations, and cross-period VRS feasibility warning |
| pp. 74--75 | purpose of the enhanced decomposition and scale efficiency as the CRS/VRS distance ratio |
| p. 75, footnote 16 | `TECHCH × PEFFCH × SCH` and `EFFCH = PEFFCH × SCH` |
| p. 75, footnote 17 | exactly two additional VRS programmes, both own-period |

The article attributes the enhanced decomposition to Färe et al. (1994) and
then states the complete identity, the two additional programmes, the RTS
assignments, and the component definitions needed for this executable leaf.
Those statements close the present task graph without importing a formula
from a secondary source.

## 2. Frozen distance convention and task graph

Let $z_q=(x_q,y_q)$ be the observation in period $q$, and let
$D_R^r(z_q)$ be its output distance relative to period-$r$ technology under
returns-to-scale regime $R$. The regimes used here are $C$ for CRS and $V$
for VRS. The independent compiler follows equations (16)--(17):

$$
D_R^r(x_q,y_q)=\frac{1}{\max \phi}
$$

subject to input feasibility, proportional expansion of every desirable
output, nonnegative intensities, and, only for VRS,
$\sum_k\lambda_k=1$.

For one matched transition, the four CRS tasks are

$$
\mathcal D_C=
\begin{bmatrix}
D_C^t(z_t) & D_C^t(z_{t+1})\\
D_C^{t+1}(z_t) & D_C^{t+1}(z_{t+1})
\end{bmatrix}.
$$

The enhanced account adds only

$$
D_V^t(z_t),\qquad D_V^{t+1}(z_{t+1}).
$$

Thus one DMU transition has six primitive tasks: four CRS own/cross tasks plus
two own-period VRS tasks. It has no VRS cross-period task. This is the
source-defined distinction from the eight-task Ray--Desli allocation.

## 3. Component equations

The four CRS distances define the Malmquist productivity index

$$
M=
\left[
\frac{D_C^t(z_{t+1})}{D_C^t(z_t)}
\frac{D_C^{t+1}(z_{t+1})}{D_C^{t+1}(z_t)}
\right]^{1/2}.
$$

Its original two-factor account is

$$
\mathrm{EFFCH}=
\frac{D_C^{t+1}(z_{t+1})}{D_C^t(z_t)},
$$

$$
\mathrm{TECHCH}_C=
\left[
\frac{D_C^t(z_{t+1})}{D_C^{t+1}(z_{t+1})}
\frac{D_C^t(z_t)}{D_C^{t+1}(z_t)}
\right]^{1/2},
$$

with $M=\mathrm{EFFCH}\times\mathrm{TECHCH}_C$.

The two VRS own-period distances define

$$
\mathrm{PEFFCH}=
\frac{D_V^{t+1}(z_{t+1})}{D_V^t(z_t)}.
$$

Scale efficiency in each period is the source-stated CRS/VRS ratio,

$$
SE^r(z_r)=\frac{D_C^r(z_r)}{D_V^r(z_r)},
$$

so scale-efficiency change is

$$
\mathrm{SCH}=
\frac{SE^{t+1}(z_{t+1})}{SE^t(z_t)}.
$$

The two independently checked identities are therefore

$$
\mathrm{EFFCH}=\mathrm{PEFFCH}\times\mathrm{SCH},
$$

$$
M=\mathrm{TECHCH}_C\times\mathrm{PEFFCH}\times\mathrm{SCH}.
$$

These are multiplicative accounts, not additive shares. `SCH` is an
own-period scale-efficiency ratio. It must not be replaced by the geometric
scale term in Ray and Desli (1997), even though both decompositions reproduce
the same CRS Malmquist index.

## 4. Economic and managerial direction

The source uses values above one for improvement. In this account:

- $M>1$ records productivity growth between the two operating periods;
- $\mathrm{EFFCH}>1$ records improved operating performance relative to the
  CRS benchmark;
- $\mathrm{PEFFCH}>1$ records improved performance after separating scale
  conditions, the source's pure-efficiency change;
- $\mathrm{SCH}>1$ records a favorable change in the scale-efficiency part of
  operating performance; and
- $\mathrm{TECHCH}_C>1$ records favorable movement in best-practice
  production possibilities under the CRS account.

A factor below one records deterioration in that component. Components can
move in opposite directions, so a productivity gain does not imply that each
factor exceeds one. These are descriptive benchmark accounts; the source
identity alone does not establish a causal explanation.

## 5. Certified data domain

The article's technology permits multiple inputs and multiple desirable
outputs with strong disposability. Its empirical setup states that each
observation is strictly positive and that the number of observations remains
constant across years. Footnote 14 also says the general approach admits zero
values for **some** inputs and outputs, and that an unbalanced panel may be
used although an index is undefined for a missing observation.

The exact executable certificate deliberately freezes the smaller domain that
can be checked without guessing which zero patterns preserve every ratio:

- output orientation;
- one or more inputs and one or more desirable outputs;
- finite, strictly positive quantities;
- the same variables in the two periods;
- a matched adjacent panel with each evaluated DMU observed in both periods;
- CRS for all four Malmquist tasks; and
- VRS only for the two own-period pure-efficiency tasks.

The tested production contract is slightly broader and follows footnote 14:
quantities may be finite and nonnegative,
provided every DMU-period row has positive aggregate input and positive
aggregate desirable output. Every solved primitive distance must still be
positive and finite before it can enter a ratio. Individual zeros can
therefore pass validation without implying that every zero pattern yields a
complete account. The strictly positive fixture remains the analytical
certificate and is not broadened by those package tests.

For an unbalanced panel, production must expose an explicit policy:
`unbalanced="raise"` rejects missing adjacent observations, while
`unbalanced="drop"` excludes unmatched DMU transitions. Neither policy
imputes a missing bundle, and no productivity index is reported for a DMU
without both adjacent observations.

No undesirable output, weak-disposal technology, input orientation, NIRS
decomposition, missing-DMU imputation, or silent panel balancing belongs to
this certificate. The article's qualified permission for some zeros is
recorded but is not generalized into an all-zero-pattern guarantee. Any
further zero-pattern guarantee must identify its admissible patterns and
independently test every denominator; otherwise it remains deferred to a later
version.

## 6. Failure semantics

Every complete enhanced account requires all six distances to be positive and
finite. The source-only compiler and current production contract therefore
follow these rules:

1. the source-only compiler rejects quantities outside its strictly positive
   certified domain; production rejects negative quantities or rows without
   positive input and output aggregates; both reject inconsistent variables
   and nonfinite values, while unmatched rows follow production's explicit
   `drop`/`raise` policy;
2. an unavailable, nonpositive, or nonfinite CRS primitive makes the CRS core
   account undefined; no factor is filled by a residual or by one;
3. if all four CRS tasks remain valid but an own-period VRS task is
   unavailable, $M$, `EFFCH`, and `TECHCH(C)` remain valid, while `PEFFCH`,
   `SCH`, and the enhanced reconstruction are undefined;
4. solver infeasibility is kept distinct from other numerical failure; and
5. no VRS cross-period result is requested or reported.

Footnote 15 warns that VRS **cross-period** evaluation can be infeasible. That
warning matters for methods that request VRS cross tasks, including
Ray--Desli, but it does not add two more tasks to enhanced FGNZ. The two FGNZ
VRS evaluations are own-period tasks whose evaluated observations belong to
their own reference data by construction. The dependency-preserving partial
result in item 3 is a software contract, not an empirical partial-result rule
stated by Färe et al. It must not be presented as analogous source evidence to
the Ray--Desli VRS-cross case. A numerical failure is still reported rather
than patched.

## 7. Evidence gate and release boundary

The independent certificate is
`tests/test_fare_etal_1994_enhanced_fgnz_source.py`. It compiles all six dense
LPs directly with NumPy/SciPy, imports no `deapack` code, asserts every
primitive distance on an exact rational fixture, checks both reconstruction
identities DMU by DMU, and proves that the FGNZ and Ray--Desli allocations are
not aliases.

This source gate is closed only for the equations, orientation, RTS choices,
six-task graph, certified data domain, and fail-closed semantics stated above.
Any claim not closed by the defining text and an independent oracle is
postponed rather than inferred. In particular, arbitrary zero patterns and
the original OECD/PWT5 empirical reproduction remain for a later version.
The independent production milestone has now passed. The source-qualified leaf
is public as `FGNZEnhancedMalmquistProductivityIndex` (alias
`FGNZEnhancedMalmquist`) and has its own registry record. Its broader tested
production support for nonnegative partial-zero cells with positive row
aggregates and explicit unbalanced-panel `drop`/`raise` handling is a package
extension, not part of this strict-positive matched-panel source certificate.
The OECD/PWT5 empirical reproduction remains postponed to a later version.
