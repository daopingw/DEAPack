# Bjurek (1996) Hicks--Moorsteen analytical oracle

**Method ID:** `productivity.hicks_moorsteen.bjurek_1996`

**Evidence status:** `analytically_derived`

**Published reproduction:** no

**Production implementation reused:** no

This certificate verifies the bilateral eight-distance quantity account on
an exact synthetic panel. The dense compiler in
`tests/test_bjurek_1996_hicks_moorsteen_source.py` is written directly from
the distance programmes and does not import the production package.

This production-free oracle and the runtime release certificate have distinct
jobs. The oracle establishes the source-form quantity account independently.
During every fitted result, DEAPack additionally checks the returned primal,
bounds, objective, dual conditions, complementarity, and strong duality for
all eight LPs and reconstructs the complete quantity identity before releasing
a transition. Those no-extra-solve checks are exercised in
`tests/test_hicks_moorsteen_postsolve_certification.py`; they do not turn the
production implementation into its own validation oracle.

## Exact two-period panel

Unit D is the producer being compared. Unit Z is a deliberately dominated
reference activity.

| Period | Unit | Inputs $(x_1,x_2)$ | Desirable outputs $(y_1,y_2)$ |
|---|---|---|---|
| $t$ | D | $(5,4)$ | $(4,6)$ |
| $t$ | Z | $(20,20)$ | $(1,1)$ |
| $t+1$ | D | $(6,6)$ | $(6,15)$ |
| $t+1$ | Z | $(24,24)$ | $(1,1)$ |

Each period uses its own VRS technology. VRS requires the two reference
intensities to sum to one. In an output task, any positive weight on Z raises
inputs above D's fixed input bundle and lowers both outputs. In an input task,
any positive weight on Z lowers both outputs below D's fixed output bundle.
Consequently all eight optima put weight one on the relevant period's D plan
and zero on Z. This proves the active reference without using package output.

## Eight exact distances

With a single active reference plan $(x^r,y^r)$, an output task has

$$
D_O^r(x^r,y)=\max_m\frac{y_m}{y_m^r},
$$

and an input task with the period output held fixed has

$$
D_I^r(x,y^r)=\min_n\frac{x_n}{x_n^r}.
$$

The four output distances are therefore

| Role | Exact distance |
|---|---:|
| $D_O^t(x^t,y^t)$ | $1$ |
| $D_O^t(x^t,y^{t+1})$ | $\max(6/4,15/6)=5/2$ |
| $D_O^{t+1}(x^{t+1},y^t)$ | $\max(4/6,6/15)=2/3$ |
| $D_O^{t+1}(x^{t+1},y^{t+1})$ | $1$ |

The four input distances are

| Role | Exact distance |
|---|---:|
| $D_I^t(x^t,y^t)$ | $1$ |
| $D_I^t(x^{t+1},y^t)$ | $\min(6/5,6/4)=6/5$ |
| $D_I^{t+1}(x^t,y^{t+1})$ | $\min(5/6,4/6)=2/3$ |
| $D_I^{t+1}(x^{t+1},y^{t+1})$ | $1$ |

## Exact quantity and productivity indexes

The two output quantity views are

$$
Q_y^t=\frac52,
\qquad
Q_y^{t+1}=\frac{1}{2/3}=\frac32,
$$

so

$$
Q_y^{t,t+1}
=\sqrt{\frac52\frac32}
=\frac{\sqrt{15}}{2}.
$$

The two input quantity views are

$$
Q_x^t=\frac65,
\qquad
Q_x^{t+1}=\frac{1}{2/3}=\frac32,
$$

so

$$
Q_x^{t,t+1}
=\sqrt{\frac65\frac32}
=\frac{3}{\sqrt5}.
$$

The exact Hicks--Moorsteen change is

$$
HM^{t,t+1}
=\frac{\sqrt{15}/2}{3/\sqrt5}
=\frac{5\sqrt3}{6}.
$$

## Exact time reversal

Reversing the period order swaps the two technologies and inverts each
bilateral quantity comparison. The reverse values are

$$
Q_y^{t+1,t}=\frac{2}{\sqrt{15}},
\qquad
Q_x^{t+1,t}=\frac{\sqrt5}{3},
\qquad
HM^{t+1,t}=\frac{2\sqrt3}{5}.
$$

Thus each reverse value is exactly the reciprocal of its forward value. The
test checks these identities after independently solving the reversed eight
programmes; it does not obtain them by reversing a production result.

No published empirical result is reproduced. This oracle does not certify a
Malmquist efficiency/technical-change decomposition, circularity across more
than two periods, a different reference policy, undesirable outputs, or a
returns-to-scale extension.
