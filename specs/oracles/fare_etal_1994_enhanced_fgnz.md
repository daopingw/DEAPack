# Färe et al. (1994) enhanced FGNZ analytical oracle

**Current method identity:** `productivity.malmquist.decomposition.fgnz_pure_scale_extension`  
**Source:** Färe, Grosskopf, Norris, and Zhang (1994), *American Economic
Review* 84(1), 66--83, pp. 70--75 and footnotes 14--17  
**Source domain:** output orientation; matched, finite, strictly positive
adjacent panel; one or more inputs and desirable outputs  
**Published reproduction:** no  
**Empirical scope:** OECD/PWT5 application not reproduced  
**Production implementation reused:** no  
**Disposition:** source-qualified; production independently validated and public

## Certificate boundary

The executable certificate is
`tests/test_fare_etal_1994_enhanced_fgnz_source.py`. It imports no `deapack`
module and independently constructs dense output-distance LPs from the source
constraints. It evaluates four CRS tasks and exactly two additional
own-period VRS tasks for each DMU transition.

This oracle certifies the enhanced multiplicative identity on a synthetic
exact panel. It does not reproduce the article's OECD/Penn World Table 5
application, preprocessing, country estimates, rankings, averages, or
published tables. It also does not certify undesirable outputs, input
orientation, unobserved transitions, or arbitrary data containing zeros.

## Six-task source graph

Rows identify the reference period and columns identify the evaluated bundle:

$$
\mathcal D_C=
\begin{bmatrix}
D_C^t(z_t) & D_C^t(z_{t+1})\\
D_C^{t+1}(z_t) & D_C^{t+1}(z_{t+1})
\end{bmatrix}.
$$

The two remaining tasks are the diagonal VRS distances
$D_V^t(z_t)$ and $D_V^{t+1}(z_{t+1})$. There are no VRS cross tasks.

The compiler uses $D_o=1/\max\phi$ and preserves this role order:

1. `base_on_base`: $D_C^t(z_t)$;
2. `comparison_on_base`: $D_C^t(z_{t+1})$;
3. `base_on_comparison`: $D_C^{t+1}(z_t)$; and
4. `comparison_on_comparison`: $D_C^{t+1}(z_{t+1})$.

## Exact discriminating fixture

The fixture strengthens the independent Ray--Desli panel by making DMU D
inefficient under its own-period VRS technology. This prevents a reversed or
hard-coded `PEFFCH` ratio from passing while retaining an exact Ray contrast.

| DMU | $x_t$ | $y_t$ | $x_{t+1}$ | $y_{t+1}$ |
|---|---:|---:|---:|---:|
| A | 1.0 | 1.0 | 1.0 | 1.2 |
| B | 2.0 | 3.0 | 1.5 | 2.4 |
| C | 3.0 | 4.0 | 2.5 | 4.2 |
| D | 4.0 | $7/2$ | 4.0 | 5.0 |

The independently solved primitive distances are:

| DMU | $D_C^t(z_t)$ | $D_C^t(z_{t+1})$ | $D_C^{t+1}(z_t)$ | $D_C^{t+1}(z_{t+1})$ | $D_V^t(z_t)$ | $D_V^{t+1}(z_{t+1})$ |
|---|---:|---:|---:|---:|---:|---:|
| A | $2/3$ | $4/5$ | $25/42$ | $5/7$ | 1 | 1 |
| B | 1 | $16/15$ | $25/28$ | $20/21$ | 1 | 1 |
| C | $8/9$ | $28/25$ | $50/63$ | 1 | 1 | 1 |
| D | $7/12$ | $5/6$ | $25/48$ | $125/168$ | $7/8$ | 1 |

The table is diagnostic in three ways. CRS and VRS own-period distances are
not interchangeable; several CRS cross distances exceed one without being
failures; and all six roles affect at least one asserted component.

## Component oracle and two reconstructions

For each row the compiler calculates

$$
\mathrm{EFFCH}=\frac{D_C^{t+1}(z_{t+1})}{D_C^t(z_t)},\qquad
\mathrm{PEFFCH}=\frac{D_V^{t+1}(z_{t+1})}{D_V^t(z_t)},
$$

$$
\mathrm{TECHCH}_C=
\left[
\frac{D_C^t(z_{t+1})}{D_C^{t+1}(z_{t+1})}
\frac{D_C^t(z_t)}{D_C^{t+1}(z_t)}
\right]^{1/2},
$$

and

$$
\mathrm{SCH}=
\frac{D_C^{t+1}(z_{t+1})/D_V^{t+1}(z_{t+1})}
{D_C^t(z_t)/D_V^t(z_t)}.
$$

The exact results are:

| DMU | $M$ | `EFFCH` | `TECHCH(C)` | `PEFFCH` | FGNZ `SCH` |
|---|---:|---:|---:|---:|---:|
| A | $6/5$ | $15/14$ | $28/25$ | 1 | $15/14$ |
| B | $16/15$ | $20/21$ | $28/25$ | 1 | $20/21$ |
| C | $63/50$ | $9/8$ | $28/25$ | 1 | $9/8$ |
| D | $10/7$ | $125/98$ | $28/25$ | $8/7$ | $125/112$ |

For every DMU, the executable certificate separately requires

$$
\left|\mathrm{EFFCH}-\mathrm{PEFFCH}\times\mathrm{SCH}\right|<10^{-12}
$$

and

$$
\left|M-\mathrm{TECHCH}_C\times\mathrm{PEFFCH}\times\mathrm{SCH}\right|
<10^{-12}.
$$

Checking only the final product would not detect a swapped CRS/VRS task or a
misallocated technical/scale factor, so every component is asserted first.

## Non-equivalence certificate against Ray--Desli

On the same fixture, the Ray--Desli source oracle allocates the common
productivity index as follows:

| DMU | FGNZ `TECHCH(C)` | FGNZ `SCH` | Ray `TECHCH(v)` | Ray `SCH(v)` |
|---|---:|---:|---:|---:|
| A | 1.120000000 | 1.071428571 | 1.200000000 | 1.000000000 |
| B | 1.120000000 | 0.952380952 | 1.148912529 | 0.928414165 |
| C | 1.120000000 | 1.125000000 | 1.157583690 | 1.088474216 |
| D | 1.120000000 | 1.116071429 | 1.250000000 | 1.000000000 |

All eight displayed technical/scale values differ across the two accounts,
while the common `PEFFCH` values and reconstructed $M$ agree. DMU D has
`PEFFCH=8/7`, so the fixture also fails if the own-period VRS ratio is
reciprocated or fixed at one. The test fails if FGNZ is routed through the Ray
VRS cross-period formulas or if Ray's scale factor is substituted for FGNZ's
own-period scale-efficiency ratio.

## Domain and failure oracle

The source notes that some zero inputs or outputs are possible in the general
approach, but it does not provide a blanket guarantee that every zero pattern
leaves all ratios defined. The exact fixture and source-only compiler
therefore use finite, strictly positive matched data. The tests reject:

- a DMU missing from either adjacent period;
- inconsistent input or output variables;
- nonfinite quantities;
- zero or negative quantities outside the certified domain; and
- any unavailable, nonpositive, or nonfinite CRS primitive distance.

The current production validation contract accepts finite nonnegative data
when every DMU-period row has positive aggregate input and output. A complete
result still requires positive finite solved distances. Unbalanced data must
use an explicit `raise` or `drop` policy, and a missing adjacent observation
never receives an imputed index.

An unavailable CRS task invalidates the CRS core. If the four CRS tasks remain
valid but one own-period VRS task is unavailable, the dependency-preserving
software account retains $M$, `EFFCH`, and `TECHCH(C)` and leaves `PEFFCH`,
`SCH`, and the enhanced reconstruction undefined. The test certifies that
boundary and never manufactures a missing factor from a residual. This is a
software failure policy, not a source-reported empirical partial result.

The oracle does not request VRS cross-period tasks, so the cross-VRS
infeasibility noted in source footnote 15 is not part of this six-task method's
result contract.

## Gate verdict

The defining text closes the distance direction, six task roles, CRS/VRS
assignments, both component identities, economic direction, matched-panel
rule, and the certified positive domain. The independent compiler reproduces
the exact task and component tables without production code and distinguishes
the FGNZ allocation from Ray--Desli.

The source gate therefore passes for this narrow analytical leaf. The separate
production milestone has also passed, without reusing this oracle's compiler,
and the method is now public. Production additionally supports tested
nonnegative partial-zero cells with positive row aggregates and explicit
unbalanced-panel `drop`/`raise` handling; those are package extensions rather
than claims made by this strict-positive matched-panel certificate. The
original OECD/PWT5 empirical reproduction remains explicitly postponed to a
later version.
