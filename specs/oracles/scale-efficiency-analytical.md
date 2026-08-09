# Radial scale efficiency: independent analytical oracle

**Method ID:** `analysis.scale_efficiency.radial_ratio`  
**Validation kind:** `analytically_derived`  
**Published reproduction:** no

This certificate validates the matched CRS/VRS radial scale-efficiency
operator on exact and independently compiled fixtures. It is not a
transcription of a published Banker--Charnes--Cooper result table and makes
no published-reproduction claim.

## Economic account

For one orientation, comparison population, data specification, and
evaluation protocol, radial scale efficiency is

$$
SE_o=\frac{TE_o^{CRS}}{TE_o^{VRS}}.
$$

The ratio compares an organization's performance under a technology that
permits unrestricted proportional replication with its performance under a
convex variable-returns technology. It does not create a third production
technology, identify the direction of local returns to scale, or certify
Pareto--Koopmans efficiency. The package consequently reports
`is_scale_efficient` for the ratio but leaves the generic `is_efficient`
field missing.

## Exact fixture

The fixture contains one input and one desirable output:

| Organization | Input | Output |
|---|---:|---:|
| A | $1$ | $1$ |
| B | $2$ | $1$ |
| C | $1$ | $1/2$ |

Every observed activity satisfies $y_j\leq x_j$, while A attains equality.
Under CRS, input-oriented feasibility therefore implies
$\theta_o\geq y_o/x_o$, attained with $\lambda_A=y_o$. Output-oriented
feasibility implies $\phi_o\leq x_o/y_o$, attained with
$\lambda_A=x_o$. Thus the standardized CRS efficiency is
$TE_o^{CRS}=\theta_o=1/\phi_o$ and equals $(1,1/2,1/2)$ for A, B, and C.

Under VRS, $\sum_j\lambda_j=1$. Because every reference input is at least
one, input-oriented feasibility adds $\theta_o x_o\geq1$. Because every
reference output is at most one, output-oriented feasibility adds
$\phi_o y_o\leq1$. A-only or self-reference plans attain the resulting
bounds.

| Orientation | Component | A | B | C |
|---|---|---:|---:|---:|
| Input | $TE^{CRS}=\theta^{CRS}$ | $1$ | $1/2$ | $1/2$ |
| Input | $TE^{VRS}=\theta^{VRS}$ | $1$ | $1/2$ | $1$ |
| Input | $SE=TE^{CRS}/TE^{VRS}$ | $1$ | $1$ | $1/2$ |
| Output | $TE^{CRS}=1/\phi^{CRS}$ | $1$ | $1/2$ | $1/2$ |
| Output | $TE^{VRS}=1/\phi^{VRS}$ | $1$ | $1$ | $1/2$ |
| Output | $SE=TE^{CRS}/TE^{VRS}$ | $1$ | $1/2$ | $1$ |

The fixture separates scale efficiency from strong technical efficiency.
For example, B's input-oriented CRS and VRS efficiencies are both $1/2$, so
its scale-efficiency ratio is one even though both component technologies
identify a radial input shortfall. This is why the operator must not map
`is_scale_efficient` into the generic `is_efficient` field.

## Executable checks

`tests/test_scale_independent_oracle.py` performs two checks:

1. it compares both exact component vectors, both exact scale-efficiency
   vectors, the ratio identity, and the scale-efficiency classification with
   the public `scale_efficiency` API; and
2. on a separate six-organization, two-input, two-output fixture, it
   hand-compiles dense CRS and VRS radial programmes for both orientations
   with `scipy.optimize.linprog`, then forms the ratio independently of the
   production radial compiler and scale operator.

The dense cross-check uses the same SciPy/HiGHS optimizer class as the package
configuration under test. It is independent problem compilation, not an
independent-solver reproduction. Execution-count and shared-compilation
contracts are tested separately in `tests/test_scale.py` and
`benchmarks/benchmark_classical_foundations.py`.

## Claim boundary

| Claim | Evidence | Parameter and result scope |
|---|---|---|
| exact matched ratio | analytical bounds plus feasible reference plans | input and output orientations; exact CRS efficiency, VRS efficiency, scale-efficiency ratio, ratio identity, scale classification, and missing generic-efficiency semantics for all three fixture organizations |
| independent component compilation | separately hand-compiled numerical cross-check using the same SciPy/HiGHS optimizer class | input and output orientations on one six-organization, two-input, two-output fixture; component efficiencies, ratio, classification, diagnostics, and execution accounting |

All certified runs use strictly positive cross-sectional inputs and desirable
outputs, the same score-only protocol for both components, and a
self-inclusive full eligible sample requested through `auto` and resolved to
`global`.

The certificate does **not** extend to:

- custom, external, leave-one-out, group, or panel reference policies;
- undesirable outputs, signed quantities, zero component aggregates, or
  failed component fits;
- slack completion, targets, peers, dual values, or a claim of
  Pareto--Koopmans efficiency;
- local returns-to-scale classification, MPSS, scale elasticity, capacity,
  congestion, or any non-radial scale measure; or
- sampling inference, uncertainty quantification, or a published-data
  reproduction.
