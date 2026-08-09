# APZ consistency oracle: 2013 example and 2017 operational LP

**Canonical preset identity:**
`productivity.malmquist_luenberger.aparicio_pastor_zofio_2013`  
**Evidence status:** `analytically_derived`  
**Published reproduction:** no  
**Production implementation reused:** no  
**Defining source:** Aparicio, Pastor, and Zofío (2013), author working paper,
internal pp. 5--15, especially equations (1)--(8), Table 1, and Figures 1
and 3  
**Operational source:** Aparicio, Barbero, Kapelko, Pastor, and Zofío (2017),
*Journal of Environmental Management* 196, 148--160, especially pp. 152--153,
equations (5)--(6) and Proposition 1  
**Certified scope:** the paper's one-input, one-good-output,
one-bad-output, two-period Table 1 example under CRS  

## 1. What the source does and does not publish

Both source artifacts were inspected page by page. The 2013 author working
paper has 19 PDF pages and SHA-256
`6d339b20b00356577f51dd9ef3a772aa3080bbedfafb31128a51d9a00400bf11`.
The 2017 published article has 13 PDF pages and SHA-256
`e1fdb6f414e67dc2de5da27acf21e1830d1613c300f21841e8050fc14b636dba`.
Table 1 of the 2013 paper provides every quantity needed to recompile its
example:

| Observation | $x$ | $y$ | $b$ |
|---|---:|---:|---:|
| $A^t$ | $1$ | $7$ | $2$ |
| $B^t$ | $1$ | $5$ | $5$ |
| $A^{t+1}$ | $1$ | $8$ | $1$ |
| $B^{t+1}$ | $1$ | $11/2$ | $3$ |

Equation (6) supplies the ordinary CRS DEA technology, and equation (1)
supplies the observation-specific direction $(y,-b)$. The article itself
prints only the two own-period zeros, the sign $MLTECH^t<1$, the reverse
cross-period infeasibility, and the corrected sign $MLTECH_t^{t+1}>1$. It
does **not** print a numerical vector of the four distances or a table of the
corrected components. The exact fractions below are therefore independently
derived consequences of the published example, not a reproduction of a
published numerical table.

The 2017 follow-up article closes an important operational gap left by the
2013 paper. Its equations (5)--(6) give the general CRS DEA production set and
directional-distance programme for the APZ postulate, including a
coordinatewise cap for multiple bad outputs. The formal LP in this oracle and
its test is transcribed from that published programme, rather than inferred
from Figure 3 or copied from production software.

The 2017 paper also publishes empirical values: Table 3 reports country-level
CFG and APZ indices for three transitions, while Tables 4--7 report programme,
failure, inconsistency, and distribution-test counts. Those tables are not
independently reproducible from the PDF alone. The prepared 39-country,
1995--2007 unit-level panel is not printed; Table 2 contains aggregate
descriptive statistics only. Reproduction would additionally require the
exact WIOD/World Bank vintage, country-level transformations, pollutant
combinations, and prepared panel used by the authors. None is reconstructed
here.

This distinction matters for release governance. The oracle closes the scalar
2013 Table 1 branch under the 2017 formal LP and proves non-equivalence to the
conventional technology. It does not reproduce either paper's published
empirical results, compare the final 2013 EJOR typesetting, certify the full
multi-bad empirical domain or reproduce the published WIOD application. The
public preset therefore carries an analytical, not published-empirical,
verification claim.

## 2. Frozen distance convention

For reference period $s$ and evaluated observation from period $q$, write

$$
d_s^q=\vec D_o^s(x^q,y^q,b^q;y^q,-b^q).
$$

For the Table 1 CRS technology, each ordinary task independently solves

$$
\begin{aligned}
\max_{z_A,z_B,\beta}\quad &\beta\\
\text{s.t.}\quad
&x_A^s z_A+x_B^s z_B\le x^q,\\
&y_A^s z_A+y_B^s z_B\ge (1+\beta)y^q,\\
&b_A^s z_A+b_B^s z_B=(1-\beta)b^q,\\
&z_A,z_B\ge0,
\end{aligned}
$$

with $\beta$ free. There is no convexity equation. An infeasible task remains
infeasible; it is not clipped, imputed, or replaced by a global reference.

The 2013 postulate is labelled A7 in its full axiom list. The 2017 operational
paper relabels the same bounded bad-output expansion postulate A2 after
highlighting compactness as A1. For period $s$, its equation (5) defines

$$
P^s(x)=\left\{(y,b):
\sum_k z_k y_{km}^s\ge y_m,\quad
\sum_k z_k b_{ki}^s\le b_i,\quad
\sum_k z_k x_{kn}^s\le x_n,\quad
b_i\le\bar b_i^s(x),\quad z_k\ge0
\right\}.
$$

Proposition 1 fixes the empirical cap, coordinate by coordinate, as

$$
\bar b_i^s(x)=\max_{k=1,\ldots,K}\{b_{ki}^s\}
$$

for the strictly positive source domain. Equation (6) then evaluates an
observation from period $q$ against period-$s$ references by solving

$$
\begin{aligned}
\max_{z,\beta}\quad &\beta\\
\text{s.t.}\quad
&\sum_kz_ky_{km}^s\ge y_m^q+\beta y_m^q,&&m=1,\ldots,M,\\
&\sum_kz_kb_{ki}^s\le b_i^q-\beta b_i^q,&&i=1,\ldots,I,\\
&\sum_kz_kx_{kn}^s\le x_n^q,&&n=1,\ldots,N,\\
&b_i^q-\beta b_i^q\le\bar b_i^s(x^q),&&i=1,\ldots,I,\\
&z_k\ge0.
\end{aligned}
$$

Thus the standard bad-output equality is replaced by an inequality, and a
second inequality bounds the directional target. For the 2013 Table 1 data,
the 2017 reference-period caps are $\bar b^t=5$ and
$\bar b^{t+1}=3$. The independent compiler uses these two distinct caps.

The source ratios are

$$
ML^s=\frac{1+d_s^t}{1+d_s^{t+1}},
\qquad
MLEFFCH=\frac{1+d_t^t}{1+d_{t+1}^{t+1}},
$$

$$
MLTECH^t=\frac{1+d_{t+1}^{t+1}}{1+d_t^{t+1}},
\qquad
MLTECH^{t+1}=\frac{1+d_{t+1}^{t}}{1+d_t^t}.
$$

The adjacent index and technical-change account are the geometric means of
their two reference-period factors. Every one of the four distances must be
available before those geometric means are defined.

## 3. Task graph

The ordinary and APZ-A2 accounts use the same four economic roles, but they are
four newly compiled tasks under different technologies. The corrected account
is not a transformation of the ordinary results.

```text
Table 1 observations
    |
    +-- ordinary A1--A6 technology in t
    |       +-- d_t^t
    |       `-- d_t^(t+1)
    |
    +-- ordinary A1--A6 technology in t+1
    |       +-- d_(t+1)^t
    |       `-- d_(t+1)^(t+1)
    |
    `-- replace both technologies by the 2017 equations (5)--(6)
            +-- calculate reference-period caps 5 and 3
            +-- recompile all four APZ-A2 distances
            +-- form ML^t and ML^(t+1)
            +-- form MLEFFCH, MLTECH^t, and MLTECH^(t+1)
            `-- verify ML = MLEFFCH x sqrt(MLTECH^t x MLTECH^(t+1))
```

For the scalar example, the 2017 APZ LP specializes to

$$
b_A^s z_A+b_B^s z_B
\le(1-\beta)b^q
\le\bar b^s,
\qquad
(\bar b^t,\bar b^{t+1})=(5,3).
$$

This is the formal operational rule. It must not be replaced by unrestricted
bad-output disposal, by treating bad outputs as ordinary inputs without the
cap, by pooling all periods into a global technology, or by changing a
standard ML component after solving it. The common adjacent-pair cap $5$ used
in the 2013 Figure 3 nesting illustration is conceptually informative, but the
oracle compiler follows the later published equations (5)--(6), whose caps
are reference-period specific. The exact Table 1 optima below satisfy both
formulations; their target bad-output levels do not violate the tighter
period-$t+1$ cap of $3$.

## 4. Exact ordinary-technology certificate

The independently compiled ordinary tasks are

| Task | Exact distance | Exact peer intensities | Status |
|---|---:|---:|---|
| $d_t^t$ | $0$ | $(z_A,z_B)=(0,1)$ | optimal |
| $d_t^{t+1}$ | $5/21$ | $(19/21,2/21)$ | optimal |
| $d_{t+1}^t$ | -- | -- | infeasible |
| $d_{t+1}^{t+1}$ | $0$ | $(0,1)$ | optimal |

The nontrivial finite optimum follows without floating-point arithmetic. On
the period-$t$ frontier between $A^t$ and $B^t$,

$$
y=\frac{25-2b}{3}.
$$

The $B^{t+1}$ directional path is
$y=\tfrac{11}{2}(1+\beta)$ and $b=3(1-\beta)$. Equating the path and frontier
gives

$$
\frac{11}{2}(1+\beta)
=\frac{25-6(1-\beta)}{3}
\quad\Longrightarrow\quad
\beta=\frac5{21}.
$$

At that value, $b=16/7$, $y=143/21$, and the intensities
$(19/21,2/21)$ attain both quantities exactly. Thus

$$
ML^t=MLTECH^t
=\frac{1}{1+5/21}
=\frac{21}{26}<1,
\qquad MLEFFCH=1.
$$

The reverse task cannot be repaired by allowing a negative distance. For the
period-$t+1$ frontier segment with $1\le b\le3$, feasibility of the $B^t$ path
requires $\beta\ge8/5$, while nonnegative target bad output requires
$\beta\le1$. On the ray with $0\le b\le1$, the path requires simultaneously
$\beta\ge4/5$ and $\beta\le7/9$. Both regions are empty. Therefore
$d_{t+1}^t$ is infeasible, $ML^{t+1}$ is unavailable, and neither the standard
adjacent ML geometric mean nor its complete technical-change geometric mean
exists for unit $B$.

## 5. Exact APZ-A2 certificate under the 2017 LP

Under equation (6), the period-$t$ and period-$t+1$ upper frontiers are
horizontal at $y=7$ and $y=8$ over the relevant target bad-output ranges. The
respective caps are $5$ and $3$. All four tasks are feasible and have the
following exact solutions:

| Task | Exact distance | Exact peer intensities |
|---|---:|---:|
| $\bar d_t^t$ | $2/5$ | $(1,0)$ |
| $\bar d_t^{t+1}$ | $3/11$ | $(1,0)$ |
| $\bar d_{t+1}^t$ | $3/5$ | $(1,0)$ |
| $\bar d_{t+1}^{t+1}$ | $5/11$ | $(1,0)$ |

For example, $5(1+\beta)=7$ gives $\bar d_t^t=2/5$, and
$\tfrac{11}{2}(1+\beta)=8$ gives
$\bar d_{t+1}^{t+1}=5/11$. The bad-output targets remain between the active
peer's bad output and the applicable reference-period cap, so A2 makes each
candidate feasible. Since no input-one combination produces more than $7$ in
period $t$ or more than $8$ in period $t+1$, these candidates also meet exact
upper bounds.

The resulting account is

| Quantity | Exact value |
|---|---:|
| $\overline{ML}^t$ | $11/10$ |
| $\overline{ML}^{t+1}$ | $11/10$ |
| $\overline{MLEFFCH}$ | $77/80$ |
| $\overline{MLTECH}^t$ | $8/7$ |
| $\overline{MLTECH}^{t+1}$ | $8/7$ |
| $\overline{MLTECH}_t^{t+1}$ | $8/7$ |
| $\overline{ML}_t^{t+1}$ | $11/10$ |

The exact reconstruction is

$$
\frac{77}{80}\times\frac87=\frac{11}{10}.
$$

This independently sharpens the 2013 paper's printed sign result: the 2017
bounded APZ technology records technical progress, $8/7>1$, while the
conventional period-$t$ component records $21/26<1$ and its reverse task is
infeasible.

## 6. Non-equivalence and evidence boundary

The numerical certificate rules out an alias or post-processing
implementation:

1. APZ-A2 changes the feasible production set and therefore changes even the two
   own-period distances from $0,0$ to $2/5,5/11$.
2. The conventional four-task account contains one infeasible task; the APZ
   account contains four finite tasks.
3. The conventional finite technical-change factor is $21/26<1$; the two APZ
   factors are both $8/7>1$.
4. The APZ headline $11/10$ depends on re-solving all four LPs. It cannot be
   obtained by changing the sign, reciprocal, or label of the conventional
   output.

The test compiler in
`tests/test_aparicio_pastor_zofio_2013_source.py` imports no DEAPack module and
shares no production LP builder. It uses a direct dense transcription of the
2013 ordinary equation (6), the 2017 APZ equations (5)--(6), and exact rational
targets and frontier checks. The certified result is intentionally narrow:
one input, one desirable output, one undesirable output, CRS, the Table 1
observations, observation-specific directions, the two reference-period caps
$5$ and $3$, and the two adjacent periods. Multiple undesirable outputs,
unbalanced panels, alternative directions or returns to scale, slack
completion, and any public API remain outside this oracle.
