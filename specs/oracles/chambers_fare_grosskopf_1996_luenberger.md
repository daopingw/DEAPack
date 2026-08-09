# Chambers--Färe--Grosskopf ordinary Luenberger analytical oracle

**Method ID:** `productivity.luenberger`  
**Validation kind:** `analytically_derived`  
**Published reproduction:** no

This certificate verifies the narrow adjacent-period CRS Luenberger
operator frozen in
`specs/source_protocols/chambers_fare_grosskopf_1996_luenberger.md`. It uses
two exact synthetic panels and dense linear programmes compiled independently
of DEAPack's production code. It does not claim to reproduce the APEC country
tables in the source article.

## Independent task

For each evaluated plan $(x_o,y_o)$, reference-period observations
$(X^r,Y^r)$, and the common direction $g=(0,1)$, the independent compiler
solves

$$
\begin{aligned}
\max_{\lambda,\beta}\quad &\beta\\
\text{s.t.}\quad
&X^r\lambda\le x_o,\\
&Y^r\lambda\ge y_o+\beta,\\
&\lambda\ge0,\qquad\beta\in\mathbb R.
\end{aligned}
$$

The dense test arrays are constructed directly for SciPy/HiGHS. No package
reference compiler, DDF programme builder, private productivity helper, or
production result is used to create the expected values.

## Exact panel 1: pure change in represented opportunities

One hospital is observed under two period technologies:

| Period | Resource $x$ | Service $y$ |
|---|---:|---:|
| $t$ | 1 | 1 |
| $t+1$ | 1 | 2 |

Each technology contains its one observed CRS activity. With the reference
activity $(1,a_r)$, the input constraint gives $\lambda\le1$, while the output
constraint gives $\beta\le a_r\lambda-y_o$. The bound is attained at
$\lambda=1$. Hence every task has the exact solution
$\vec D^r(x_o,y_o;0,1)=a_r-y_o$, and

$$
\left(
D_{t\mid t},D_{t+1\mid t},D_{t\mid t+1},D_{t+1\mid t+1}
\right)
=(0,-1,1,0).
$$

The value $D_{t+1\mid t}=-1$ is feasible and optimal. It records that the
new plan exceeds the old represented opportunity by one programme unit; it
must not be truncated to zero. The additive account is

$$
L=\frac12\{[0-(-1)]+[1-0]\}=1,
$$

$$
EC_L=0-0=0,
\qquad
TC_L=\frac12\{(0-(-1))+(1-0)\}=1.
$$

Thus the exact identity is $1=0+1$. The hospital is on its contemporaneous
benchmark in both periods; all measured change is allocated to more favorable
represented opportunities.

## Exact panel 2: pure relative operating-performance improvement

The second panel holds the best-practice activity fixed while organization A
removes its contemporaneous service shortfall:

| DMU | Period | Resource $x$ | Service $y$ |
|---|---|---:|---:|
| A | $t$ | 1 | $1/2$ |
| Frontier | $t$ | 1 | 1 |
| A | $t+1$ | 1 | 1 |
| Frontier | $t+1$ | 1 | 1 |

Both period technologies have the same CRS boundary $y=x$. At $x=1$, A's
old plan can add exactly $1/2$ unit of service, whereas its new plan is on the
boundary. Therefore

$$
\left(
D_{t\mid t},D_{t+1\mid t},D_{t\mid t+1},D_{t+1\mid t+1}
\right)
=\left(\frac12,0,\frac12,0\right).
$$

The account is

$$
L=\frac12,
\qquad
EC_L=\frac12,
\qquad
TC_L=0,
$$

and $1/2=1/2+0$. The represented opportunity does not change; all measured
improvement is allocated to a smaller contemporaneous operating shortfall.

## Executable verification

`tests/test_luenberger_independent_oracle.py` independently compiles all four
dense LPs for both panels, proves the exact fixture values before consulting
the public model, and then compares the public four distances and additive
components with those independent results.

The tests certify:

1. the four evaluated-plan/reference-technology roles;
2. pure represented-opportunity change $(L,EC_L,TC_L)=(1,0,1)$;
3. pure relative operating improvement
   $(L,EC_L,TC_L)=(1/2,1/2,0)$;
4. retention of the exact negative cross-period distance $-1$; and
5. exact reconstruction $L=EC_L+TC_L$ in both cases.

## Runtime release certificate

The analytical oracle fixes the expected economics independently of the
production compiler. At runtime, DEAPack applies a second and distinct gate to
every fitted transition. Each of the four signed directional-distance LPs must
pass solver-neutral checks of primal rows, variable bounds, the reported
objective, row and bound dual conditions, complementarity, and strong duality.
The released distance must also reconstruct the LP identity
$c'z=-\beta$. Finally, the two reference-period changes, $L$, $EC_L$, $TC_L$,
and $L=EC_L+TC_L$ are reconstructed from the four certified distances.

If any task or the additive account fails, the raw task diagnostics remain
available but the transition's four distances, peer intensities, components,
and headline indicator are withheld together. Certification uses the four
original solver responses and adds no optimization task. The clean, forged,
backend-failure, and transition-isolation cases are executable in
`tests/test_luenberger_postsolve_certification.py`.

## Claim boundary

The fixtures contain one input, one desirable output, two adjacent periods,
and the common direction $g=(0,1)$. They certify the source's CRS
four-distance arithmetic operator. They do not certify a published numerical
application, non-CRS technology, a different or observation-specific
direction, undesirable outputs, global or biennial references, complete TFP,
scale or mix decompositions, statistical inference, unique peers, prices,
welfare, or causal effects.
