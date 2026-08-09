# Oh (2010) global Malmquist--Luenberger analytical oracle

**Method ID:** `productivity.global_malmquist_luenberger.oh_2010`

**Validation kind:** `analytically_derived`

**Published reproduction:** no

**Production compiler reused:** false

This certificate verifies Oh's fixed-vintage CRS global
Malmquist--Luenberger account with exact synthetic observations and
inequalities derived independently of DEAPack's production implementation.
It is not a reproduction of the paper's 26-country application, and no
production fit, reference compiler, or private LP builder was used to obtain
the expected values.

## Source and formulation boundary

The defining source is Oh (2010),
[10.1007/s11123-010-0178-y](https://doi.org/10.1007/s11123-010-0178-y).
The source and economic freeze is
`specs/source_protocols/oh_2010_global_malmquist_luenberger.md`.

For a contemporaneous or pooled global CRS reference $R$, each distance in
this certificate solves

$$
\begin{aligned}
\max_{\lambda,\beta}\quad &\beta\\
\text{s.t.}\quad
&X^R\lambda\leq x_o,\\
&Y^R\lambda\geq(1+\beta)y_o,\\
&B^R\lambda=(1-\beta)b_o,\\
&\lambda\geq0.
\end{aligned}
$$

The evaluated plan supplies its own direction $(0,y_o,b_o)$. Every
own-period and global reference includes that plan, so $\beta=0$ is feasible
and the optimal distance is nonnegative. No cross-period contemporaneous
distance is part of this GML oracle.

## Exact panel 1: environmental best practice improves

One plant is observed in two periods:

| Period | Resource $x$ | Service $y$ | Residual $b$ |
|---|---:|---:|---:|
| $t$ | 1 | 1 | 2 |
| $t+1$ | 1 | 2 | 1 |

The later plan represents twice the service with half the residual at the
same resource commitment. The question is how this change is recorded when
both plans are judged against one retrospective environmental benchmark.

### Contemporaneous distances

The period-$t$ technology contains only its own activity. Its residual
account gives

$$
2\lambda=2(1-\beta),
\qquad
\lambda=1-\beta.
$$

The service account requires $\lambda\geq1+\beta$, hence
$1-\beta\geq1+\beta$ and $\beta\leq0$. The self plan
$(\lambda,\beta)=(1,0)$ is feasible, so

$$
D^t(z^t)=0.
$$

For the period-$t+1$ plan, the residual and service rows similarly give
$\lambda=1-\beta$ and $\lambda\geq1+\beta$. Therefore

$$
D^{t+1}(z^{t+1})=0.
$$

The plant operates on its period-specific environmental frontier in both
periods. Its efficiency-change component will therefore be one.

### The older plan against the pooled global benchmark

Let $\lambda_0$ and $\lambda_1$ denote intensities on the older and newer
activities. The global task is

$$
\begin{aligned}
\lambda_0+\lambda_1&\leq1,\\
\lambda_0+2\lambda_1&\geq1+\beta,\\
2\lambda_0+\lambda_1&=2(1-\beta),\\
\lambda_0,\lambda_1&\geq0.
\end{aligned}
$$

The residual account gives

$$
\beta=1-\lambda_0-\frac12\lambda_1.
$$

Substitution in the service account yields

$$
2\lambda_0+\frac52\lambda_1\geq2.
$$

Because

$$
2\lambda_0+\frac52\lambda_1
\leq
5\left(\lambda_0+\frac12\lambda_1\right),
$$

every feasible plan satisfies

$$
\lambda_0+\frac12\lambda_1\geq\frac25,
\qquad
\beta\leq\frac35.
$$

The intensity plan $\lambda_0=0$, $\lambda_1=4/5$ respects the resource
limit and attains both the service and residual requirements at equality.
Consequently,

$$
D^G(z^t)=\frac35.
$$

Economically, the old plant plan still had a 60% observation-scaled joint
service-growth and residual-reduction programme available when judged using
the best opportunities revealed over the complete two-period horizon.

### The newer plan against the pooled global benchmark

For the newer plan, the global task is

$$
\begin{aligned}
\lambda_0+\lambda_1&\leq1,\\
\lambda_0+2\lambda_1&\geq2(1+\beta),\\
2\lambda_0+\lambda_1&=1-\beta.
\end{aligned}
$$

Now $\beta=1-2\lambda_0-\lambda_1$. Substitution in the service row gives

$$
5\lambda_0+4\lambda_1\geq4.
$$

Since

$$
5\lambda_0+4\lambda_1
\leq
4(2\lambda_0+\lambda_1),
$$

feasibility requires $2\lambda_0+\lambda_1\geq1$, so $\beta\leq0$.
The self plan $\lambda_0=0$, $\lambda_1=1$ attains $\beta=0$. Hence

$$
D^G(z^{t+1})=0.
$$

### Exact index and decomposition

The four source distances are

$$
\left(
D^t(z^t),\;
D^{t+1}(z^{t+1}),\;
D^G(z^t),\;
D^G(z^{t+1})
\right)
=
\left(0,\;0,\;\frac35,\;0\right).
$$

Thus

$$
\begin{aligned}
GML^{t,t+1}
&=\frac{1+3/5}{1+0}=\frac85,\\
EC^{t,t+1}
&=\frac{1+0}{1+0}=1,\\
BPG^t&=\frac{1+0}{1+3/5}=\frac58,\\
BPG^{t+1}&=\frac{1+0}{1+0}=1,\\
BPC^{t,t+1}
&=\frac{1}{5/8}=\frac85.
\end{aligned}
$$

The identity is exact:

$$
GML^{t,t+1}
=
EC^{t,t+1}BPC^{t,t+1}
=
1\cdot\frac85
=
\frac85.
$$

The plant does not catch up relative to its own period because it is already
on both contemporaneous frontiers. The measured improvement comes entirely
from the newer period's environmental best practice closing the gap to the
full-sample benchmark.

For comparison, the source-qualified conventional ML oracle on the same
two observations gives $ML=2$ because it uses two additional off-diagonal
period-to-period distances. The exact $8/5$ result therefore guards against
silently implementing conventional ML under the GML name.

## Exact panel 2: fixed-vintage circularity

One plant is now observed over three periods:

| Period | Resource $x$ | Service $y$ | Residual $b$ |
|---|---:|---:|---:|
| $t_0$ | 1 | 1 | 4 |
| $t_1$ | 1 | 2 | 2 |
| $t_2$ | 1 | 4 | 1 |

Each plan is the only member of its contemporaneous technology. The same
argument as in panel 1 gives

$$
D^{t_0}(z^{t_0})
=D^{t_1}(z^{t_1})
=D^{t_2}(z^{t_2})
=0.
$$

Let $(\lambda_0,\lambda_1,\lambda_2)$ be global intensities and define

$$
S=4\lambda_0+2\lambda_1+\lambda_2,
\qquad
G=\lambda_0+2\lambda_1+4\lambda_2.
$$

For an evaluated plan with quantities $(y_r,b_r)$, the residual equality
gives

$$
\beta=1-\frac{S}{b_r}.
$$

The service requirement is equivalently

$$
G+\frac{y_r}{b_r}S\geq2y_r.
$$

Maximizing $\beta$ means minimizing $S$. The resource constraint is
$\lambda_0+\lambda_1+\lambda_2\leq1$.

### Period $t_0$

Here $y_0/b_0=1/4$. The service-residual opportunity supplied per unit of
$(\lambda_0,\lambda_1,\lambda_2)$ is respectively

$$
2,\qquad \frac52,\qquad \frac{17}{4},
$$

while its contribution to $S$ is $(4,2,1)$. The newest activity has the
strictly lowest residual cost per unit of the required opportunity. Setting
$\lambda_2=8/17$ reaches the right-hand side $2$, respects the resource
limit, and gives

$$
D^G(z^{t_0})
=1-\frac{(8/17)}4
=\frac{15}{17}.
$$

### Period $t_1$

Here $y_1/b_1=1$. The opportunity coefficients are $(5,4,5)$ and the
residual costs remain $(4,2,1)$. Again the newest activity is strictly best.
The attaining intensity is $\lambda_2=4/5$, so

$$
D^G(z^{t_1})
=1-\frac{(4/5)}2
=\frac35.
$$

### Period $t_2$

Here $y_2/b_2=4$. The opportunity coefficients are $(17,10,8)`. Intensity
$\lambda_2=1$ is optimal and gives

$$
D^G(z^{t_2})=0.
$$

The exact global distance factors are therefore

$$
\left(
1+D^G(z^{t_0}),\;
1+D^G(z^{t_1}),\;
1+D^G(z^{t_2})
\right)
=
\left(\frac{32}{17},\;\frac85,\;1\right).
$$

Because every contemporaneous distance factor is one, Oh's Eq. (9) gives
the following source-native best-practice gaps:

$$
\left(
BPG^{t_0},\;
BPG^{t_1},\;
BPG^{t_2}
\right)
=
\left(\frac{17}{32},\;\frac58,\;1\right).
$$

The adjacent and endpoint indexes are

$$
GML^{t_0,t_1}
=\frac{32/17}{8/5}
=\frac{20}{17},
\qquad
BPC^{t_0,t_1}
=\frac{5/8}{17/32}
=\frac{20}{17},
$$

$$
GML^{t_1,t_2}
=\frac{8/5}{1}
=\frac85,
\qquad
BPC^{t_1,t_2}
=\frac{1}{5/8}
=\frac85,
\qquad
GML^{t_0,t_2}
=\frac{32/17}{1}
=\frac{32}{17}.
$$

They satisfy Oh's fixed-vintage circularity exactly:

$$
GML^{t_0,t_1}GML^{t_1,t_2}
=
\frac{20}{17}\frac85
=
\frac{32}{17}
=
GML^{t_0,t_2}.
$$

All contemporaneous distances are zero, so $EC=1$ on both transitions and
each BPC equals its GML value. This telescoping result relies on the same
three-period global reference. Adding another period may alter all three
global distances and requires a new vintage calculation.

## Independent derivation boundary

The expected values above come from exact inequalities and explicit
attaining intensity plans. This certificate:

- does not call the DEAPack reference compiler;
- does not call the production environmental DDF problem builder;
- does not call the production GML fit routine;
- does not use a production result to generate expected values.

`Production compiler reused: false` therefore describes the derivation
itself. The executable companion,
`tests/test_oh_global_malmquist_luenberger_independent_oracle.py`,
constructs dense SciPy linear programmes directly from the fixture rows. It
does not use a DEAPack reference compiler or private LP builder to obtain the
expected distances. It then compares those independently compiled values
with the public API. The production call is the object being checked, not
the source of the oracle values.

## Claim boundary

| Claim | Evidence | Scope |
|---|---|---|
| four source distance roles | exact upper bounds and attaining intensities | self-inclusive contemporaneous and pooled global CRS references |
| global environmental opportunity improvement | exact panel 1 | one input, one desirable output, one undesirable output, two periods |
| $GML=EC\times BPC$ | exact factors in panel 1 | Oh's observation-scaled direction and common global vintage |
| source-native BPG orientation | exact $(5/8,1)$ and $(17/32,5/8,1)$ accounts | own-period factor divided by global factor; values in $(0,1]$ |
| distinction from conventional ML | exact $GML=8/5$ versus sibling oracle's $ML=2$ | panel 1 only |
| nonnegative own/global distances | explicit self feasibility and exact optima | source task graph only; no off-diagonal cross-period task |
| fixed-vintage circularity | exact panel 2 telescoping account | one plant, three periods, unchanged global reference membership |
| production independence | symbolic inequalities and attaining plans | no production compiler, solver, or fit result reused |

This certificate does **not** cover:

- reproduction of the 26-country, 1990--2003 application;
- a literal non-enveloped union of period technologies;
- VRS or any scale decomposition;
- a direction other than $(0,y,b)$;
- another bad-output production account;
- sequential, biennial, rolling, network, dynamic, or nonradial indexes;
- arbitrary multi-input, multi-output, signed, missing, or interval panels;
- unique peers outside the displayed fixtures;
- inference, shadow prices, welfare, abatement cost, or causal policy effects.

The published country-year rows needed to rebuild Oh's DEA reference sets
are unavailable in the article. Published reproduction and every extension
outside the claims above remain `deferred_to_next_version`.
