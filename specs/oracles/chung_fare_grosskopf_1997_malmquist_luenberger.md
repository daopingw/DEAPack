# Chung--Färe--Grosskopf Malmquist--Luenberger analytical oracle

**Method ID:** `productivity.malmquist_luenberger.chung_fare_grosskopf_1997`  
**Validation kind:** `analytically_derived`  
**Published reproduction:** no

This certificate verifies the fixed-input CRS common-factor
Malmquist--Luenberger operator with two exact synthetic panels and linear
programmes compiled independently of DEAPack's production model. The
fixtures are not Swedish pulp-and-paper observations, and this record does
not claim to reproduce the source's published industry averages.

## Source and formulation boundary

The defining source is Chung, Färe, and Grosskopf (1997),
[DOI 10.1006/jema.1997.0146](https://doi.org/10.1006/jema.1997.0146).
The complete equation and source-edition protocol is recorded in
`specs/source_protocols/chung_fare_grosskopf_1997_malmquist_luenberger.md`.

The journal's output-set definition and direction $g=(y,-b)$ hold inputs
fixed, while its printed equation (3.14) contains an input-contraction term.
The predecessor working-paper equation (2.14) prints the fixed-input row.
This oracle tests that fixed-input programme and records the internal source
inconsistency without claiming a formal publisher erratum.

For reference technology $r$, every independent task solves

$$
\begin{aligned}
\max_{\lambda,\beta}\quad &\beta\\
\text{s.t.}\quad
&X^r\lambda\leq x_o,\\
&Y^r\lambda\geq(1+\beta)y_o,\\
&B^r\lambda=(1-\beta)b_o,\\
&\lambda\geq0.
\end{aligned}
$$

There is no intensity-sum equation. $\beta$ is unrestricted in a
cross-period task.

## Exact panel 1: best-practice environmental opportunity improves

One plant is observed in two periods:

| Period | Resource $x$ | Service $y$ | Residual $b$ |
|---|---:|---:|---:|
| $t$ | 1 | 1 | 2 |
| $t+1$ | 1 | 2 | 1 |

Each contemporaneous technology contains its one observation, so

$$
D^t(z^t)=0,
\qquad
D^{t+1}(z^{t+1})=0.
$$

### The newer plan against the older technology

Let $\lambda$ be intensity on the older activity. The bad-output equality is

$$
2\lambda=1-\beta,
\qquad
\lambda=\frac{1-\beta}{2}.
$$

The service requirement is

$$
\lambda\geq2(1+\beta).
$$

Combining the two accounts gives $\beta\leq-3/5$. Equality is feasible at
$\lambda=4/5$, so

$$
D^t(z^{t+1})=-\frac35.
$$

The negative value is evidence that the old opportunity set cannot reproduce
the newer high-service, low-residual plan without reversing part of the
declared programme. It is not clipped to zero.

### The older plan against the newer technology

With intensity $\lambda$ on the newer activity, the residual account gives

$$
\lambda=2(1-\beta).
$$

The service account requires

$$
2\lambda\geq1+\beta.
$$

The upper bound is $\beta\leq3/5$, attained at $\lambda=4/5$, and the input
row is feasible. Therefore

$$
D^{t+1}(z^t)=\frac35.
$$

The four distances, in public result-field order, are

$$
\left(
D^t(z^t),\;
D^t(z^{t+1}),\;
D^{t+1}(z^t),\;
D^{t+1}(z^{t+1})
\right)
=
\left(0,-\frac35,\frac35,0\right).
$$

The four $1+D$ factors are $(1,2/5,8/5,1)$, yielding

$$
ML=2,\qquad EC_{ML}=1,\qquad TC_{ML}=2.
$$

The plant remains on its contemporaneous frontier in both periods, while
the represented best-practice service--residual opportunity improves.

## Exact panel 2: catch-up to an unchanged best-practice opportunity

The second panel contains an unchanged frontier organization $F$ and an
organization $A$ that moves closer to it:

| DMU | Period | Resource $x$ | Service $y$ | Residual $b$ |
|---|---|---:|---:|---:|
| $A$ | $t$ | 1 | 1 | 2 |
| $F$ | $t$ | 1 | 2 | 1 |
| $A$ | $t+1$ | 1 | $3/2$ | $3/2$ |
| $F$ | $t+1$ | 1 | 2 | 1 |

For $A$'s older plan, intensity $4/5$ on $F$ attains
$D=3/5$. For its newer plan, intensity one on $F$ simultaneously satisfies
the input, service, and residual accounts at $D=1/3$.

The result remains the same under both period technologies. To see why the
other $A$ activity cannot improve the cross-period bounds:

- when the newer $A$ is assessed on the older technology, the input and
  combined service--residual accounts force the two reference intensities to
  sum to one; maximizing $\beta$ puts all intensity on $F$ and gives $1/3$;
- when the older $A$ is assessed on the newer technology, $F$ supplies more
  service per unit of the residual score account than the newer $A$ activity,
  so the bound is attained by intensity $4/5$ on $F$ and gives $3/5$.

Thus

$$
\left(
D^t(z_A^t),\;
D^t(z_A^{t+1}),\;
D^{t+1}(z_A^t),\;
D^{t+1}(z_A^{t+1})
\right)
=
\left(\frac35,\frac13,\frac35,\frac13\right).
$$

The four factors are $(8/5,4/3,8/5,4/3)$, so

$$
ML=\frac65,\qquad
EC_{ML}=\frac65,\qquad
TC_{ML}=1.
$$

The measured improvement is entirely catch-up relative to an unchanged
best-practice opportunity in this exact account.

## Independent compilation

`tests/test_cfg_malmquist_luenberger_independent_oracle.py` filters raw panel
rows by technology period and constructs dense `scipy.optimize.linprog`
arrays directly. It does not call:

- the DEAPack reference compiler;
- the environmental DDF problem builder;
- the four-task productivity engine's private helpers; or
- a production fit routine to generate expected values.

For each task, the test independently creates the input and desirable-output
inequalities, the undesirable-output equality, nonnegative intensity bounds,
and an unrestricted distance bound. It then compares all four distances and
the three reconstructed components with the public
`MalmquistLuenbergerProductivityIndex`.

The executable checks cover:

1. exact frontier-shift distances and $(ML,EC,TC)=(2,1,2)$;
2. exact catch-up distances and $(ML,EC,TC)=(6/5,6/5,1)$;
3. retention of the $-3/5$ cross-period distance;
4. exact $ML=EC\times TC$ reconstruction;
5. two compiled contemporaneous reference blocks and one unique solve per
   evaluated-row by technology-period task; and
6. invariance to independent positive changes in resource, service, and
   residual units.

## Claim boundary

| Claim | Evidence | Scope |
|---|---|---|
| four-task CFG distance roles | exact upper bounds and attaining intensities | one input, one desirable output, one undesirable output, two adjacent periods, CRS common-factor weak disposal |
| frontier-opportunity change | exact panel 1 | one matched organization; negative cross-period distance; $TC$ changes while $EC$ is one |
| catch-up change | exact panel 2 | two matched organizations; $EC$ changes while $TC$ is one |
| independent LP compilation | separately constructed dense SciPy/HiGHS arrays | all fixture tasks and public score/component comparison |
| unit invariance | independent positive rescaling of all three roles | observed output--residual directions on panel 1 |

This certificate does **not** cover:

- reproduction of the 39-mill Swedish panel, source Table 2, or Table 3;
- the journal equation (3.14) input-contraction term;
- VRS or activity-specific weak disposal;
- strong disposal, by-production, network, dynamic, global, biennial, or
  slacks-based environmental productivity;
- a common direction replacing the source's observation-scaled direction;
- arbitrary signed, zero, missing, or interval data;
- unique peer portfolios, dual values, shadow prices, inference, welfare,
  damages, abatement costs, or causal policy effects.

The unavailable published empirical replay and every unsupported extension
remain `deferred_to_next_version`.
