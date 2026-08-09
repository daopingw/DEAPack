# Range-adjusted measure: independent analytical oracle

**Method ID:** `static.ram`  
**Validation kind:** `analytically_derived`  
**Published reproduction:** no  
**Production compiler reused:** no

This certificate validates the Cooper--Park--Pastor (1999) VRS
range-adjusted measure on a self-inclusive cross section whose every input
and desirable-output coordinate has a positive range. Expected scores,
slacks, targets, and peers are obtained without DEAPack's production LP
builder, reference compiler, range-weight generator, RTS helper, or solver
wrapper.

The equation and interpretation boundary is frozen in
`specs/source_protocols/cooper_park_pastor_1999_ram.md`. The exact values
below are an analytical certificate, not a claim that the defining article
printed this numerical example.

## Source programme

For each organization $o$, the certified task is

$$
\begin{aligned}
\max_{\lambda,s^-,s^+}\quad
&\delta_o^{RAM}
=
\frac{1}{m+s}
\left(
\sum_i\frac{s_i^-}{R_i^x}
+
\sum_r\frac{s_r^+}{R_r^y}
\right)\\
\text{s.t.}\quad
&X\lambda+s^-=x_o,\\
&Y\lambda-s^+=y_o,\\
&\mathbf1^\top\lambda=1,\\
&\lambda,s^-,s^+\geq0,
\end{aligned}
$$

where every $R_i^x$ and $R_r^y$ is the positive maximum-minus-minimum
range in the same full comparison sample. The source efficiency is
$\rho_o^{RAM}=1-\delta_o^{RAM}$.

## Exact fixture and upper bound

| DMU | $x_1$ | $x_2$ | $y$ |
|---|---:|---:|---:|
| A | 7 | 8 | 20 |
| B | 1 | 2 | 5 |
| C | $3/2$ | $3/2$ | 1 |
| D | 10 | 10 | 1 |

The ranges are $(9,17/2;19)$. All four pure VRS reference plans are
feasible for D. Their distances are

$$
\delta_D(A)=\frac{80}{153},\quad
\delta_D(B)=\frac{695}{969},\quad
\delta_D(C)=\frac{35}{54},\quad
\delta_D(D)=0.
$$

The balances make the objective linear in $\lambda$. Because D's feasible
set is the full intensity simplex, the objective at any feasible plan is a
convex combination of these four values. It cannot exceed their maximum,
and the pure B plan attains that upper bound uniquely. Therefore

$$
\delta_D^{RAM}=\frac{695}{969},
\qquad
\rho_D^{RAM}=\frac{274}{969},
$$

with

$$
s_D^-=(9,8),\qquad s_D^+=4,\qquad
(\widehat x_D,\widehat y_D)=(1,2;5),\qquad
\lambda_B=1.
$$

A is the only plan capable of preserving $y=20$, B is the only plan with
$x_1\leq1$, and C is the only plan with $x_2\leq3/2$. Hence those three
organizations are strongly efficient and the complete efficiency vector is

$$
\left(1,1,1,\frac{274}{969}\right).
$$

This is an exact primal upper bound with an attaining plan, not merely the
value of one feasible plan.

## Independent executable compiler

`tests/test_ram_source_oracle.py` writes a dense variable vector
$[\lambda,s^-,s^+]$, the input/output balance blocks, the VRS row, and the
range-normalized objective directly with NumPy, then calls
`scipy.optimize.linprog`. Its primary certificate node is:

`tests/test_ram_source_oracle.py::test_ram_exact_vrs_account_matches_independent_source_compiler`.

The same file separately checks:

- invariance under independent positive unit changes and common coordinate
  translations, including signed observations;
- the exact source-profile label;
- source-equivalent zero-range handling under the matched self-inclusive VRS
  population; and
- rejection of an allegedly optimal but corrupted incumbent before any
  score, slack, target, peer, or dual row is published.

## Claim boundary

| Claim | Evidence | Certified scope |
|---|---|---|
| source-program transcription | defining equations, exact upper bound, attaining plan, and independent dense LP | VRS; all positive coordinate ranges; self-inclusive cross section |
| native score | exact distance and one-minus-distance vector | source fixture only |
| operating account | exact slacks, target, strong status, and unique peer for D | source fixture only; no general uniqueness claim |
| signed-data behavior | exact coordinate translations and positive unit changes | same VRS sample and unchanged economic roles |
| runtime integrity | independent primal/account recomputation and corrupted-incumbent test | package postsolve contract |

The exact four-DMU score/target certificate itself uses positive ranges. A
separate invariant test covers the source's zero-range rule by showing that
the retained matched-population VRS balance forces the zero-weight slack to
zero. The certificate does **not** cover panels, non-global references,
CRS/NIRS/NDRS, bad outputs, networks, dynamic links, super-efficiency,
closest targets, prices, inference, or causal and welfare claims. Those
distinct formulations remain `deferred_to_next_version` until their own
defining sources and executable oracles are closed.
