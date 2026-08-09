# Zhou--Ang--Wang (2012) non-CHP energy--carbon analytical oracle

**Candidate identity:** `environmental.directional_nonradial.energy_carbon.zhou_ang_wang_2012_non_chp`  
**Validation kind:** `analytically_derived`  
**Published reproduction:** no  
**Production cross-implementation:** no production implementation exists

This certificate checks the three non-CHP source presets in Zhou, Ang, and
Wang (2012),
[DOI 10.1016/j.ejor.2012.04.022](https://doi.org/10.1016/j.ejor.2012.04.022),
against one exact synthetic reference population. The formulation and claim
boundary are frozen in
`specs/source_protocols/zhou_ang_wang_2012_non_chp_energy_carbon.md`.

The fixture is not drawn from the article's 126-country application. Its
values are derived from the source equations and corroborated by a dense LP
assembled without any DEAPack production compiler. The certificate therefore
does not use the evidence labels `reproduced` or `cross-implemented`.

## 1. Exact positive fixture

Three comparable non-CHP electricity systems use fossil energy $F$ to
produce electricity $E$ jointly with CO2 $C$:

| Organization | $F$ | $E$ | $C$ |
|---|---:|---:|---:|
| A | $1$ | $1$ | $1$ |
| D | $3/2$ | $1$ | $4$ |
| O | $2$ | $1$ | $4$ |

Organization O is assessed against the self-inclusive CRS reference
population $(A,D,O)$. Write $(a,d,o)$ for its nonnegative reference
intensities. The source technology and observed-value directions give the
dense rows

$$
\begin{aligned}
a+\frac32d+2o+2\beta_F&\leq2,\\
-a-d-o+\beta_E&\leq-1,\\
a+4d+4o+4\beta_C&=4.
\end{aligned}
$$

For a preset that does not activate one component, the corresponding
$\beta$ is fixed at zero. Maximizing the source objective is equivalent to
minimizing its negative. Thus an independent dense compiler can use variable
order

$$
v=(a,d,o,\beta_F,\beta_E,\beta_C)
$$

with nonnegative bounds, the three rows above, an inactive-component
zero-bound where required, and one of the objective vectors

$$
-(0,0,0,1/2,1/2,0),\quad
-(0,0,0,0,1/2,1/2),\quad
-(0,0,0,1/3,1/3,1/3).
$$

These arrays contain all model coefficients; no production technology,
reference, RTS, direction, target, or LP helper is needed to construct them.

## 2. Energy preset

For $g=(-F_O,E_O,0)$ and $w=(1/2,1/2,0)$, the carbon row fixes

$$
a=4-4d-4o.
$$

The fossil-energy and electricity rows imply

$$
\beta_F\leq-1+\frac54d+o,
\qquad
\beta_E\leq3-3d-3o.
$$

Therefore

$$
\beta_F+\beta_E\leq2-\frac74d-2o.
$$

Nonnegativity of $\beta_F$ requires $5d/4+o\geq1$. Meeting that
requirement with $d$ is less costly in the displayed upper bound than meeting
it with $o$, so the maximum is attained at

$$
(a,d,o)=\left(\frac45,\frac45,0\right),
\qquad
(\beta_F,\beta_E)=\left(0,\frac35\right).
$$

The exact source results are

$$
D^{NR}_{energy}
=\frac12\left(0+\frac35\right)
=\frac3{10},
$$

$$
EPI_1=\frac{1-0}{1+3/5}=\frac58,
$$

and the target is

$$
(F^*,E^*,C^*)=\left(2,\frac85,4\right).
$$

This is a distinguishing non-radial plan: the demonstrated opportunity
expands electricity by $3/5$ while it does not contract fossil energy. A
single common radial step cannot represent that component plan.

## 3. Carbon preset

For $g=(0,E_O,-C_O)$ and $w=(0,1/2,1/2)$, fossil input remains capped at
two. The carbon and electricity rows imply

$$
\beta_C=1-\frac14a-d-o,
\qquad
\beta_E\leq a+d+o-1.
$$

Consequently

$$
\beta_E+\beta_C\leq\frac34a.
$$

The fossil-input row gives $a+3d/2+2o\leq2$, hence $a\leq2$ and
$\beta_E+\beta_C\leq3/2$. The bound is attained by

$$
(a,d,o)=(2,0,0),
\qquad
(\beta_E,\beta_C)=\left(1,\frac12\right).
$$

The exact source results are

$$
D^{NR}_{carbon}
=\frac12\left(1+\frac12\right)
=\frac34,
$$

$$
CPI_1=\frac{1-1/2}{1+1}=\frac14,
$$

and

$$
(F^*,E^*,C^*)=(2,2,2).
$$

## 4. Integrated energy--carbon preset

For $g=(-F_O,E_O,-C_O)$ and equal component weights, the three target
rows imply

$$
\begin{aligned}
\beta_F&\leq1-\frac12a-\frac34d-o,\\
\beta_E&\leq a+d+o-1,\\
\beta_C&=1-\frac14a-d-o.
\end{aligned}
$$

Adding them gives

$$
\beta_F+\beta_E+\beta_C
\leq1+\frac14a-\frac34d-o
\leq\frac32,
$$

where the last inequality follows from the fossil-input row and nonnegative
variables. The same intensity plan $(a,d,o)=(2,0,0)$ attains the bound at

$$
(\beta_F,\beta_E,\beta_C)=\left(0,1,\frac12\right).
$$

Therefore

$$
D^{NR}_{integrated}
=\frac13\left(0+1+\frac12\right)
=\frac12,
$$

$$
ECPI_1
=\frac{1-(0+1/2)/2}{1+1}
=\frac38,
$$

with target

$$
(F^*,E^*,C^*)=(2,2,2).
$$

## 5. Oracle vector

The complete exact result for organization O is:

| Preset | Active component steps | Peer intensities $(a,d,o)$ | $D^{NR}$ | Performance index | Target $(F^*,E^*,C^*)$ |
|---|---|---|---:|---:|---|
| energy | $(\beta_F,\beta_E)=(0,3/5)$ | $(4/5,4/5,0)$ | $3/10$ | $EPI_1=5/8$ | $(2,8/5,4)$ |
| carbon | $(\beta_E,\beta_C)=(1,1/2)$ | $(2,0,0)$ | $3/4$ | $CPI_1=1/4$ | $(2,2,2)$ |
| integrated | $(\beta_F,\beta_E,\beta_C)=(0,1,1/2)$ | $(2,0,0)$ | $1/2$ | $ECPI_1=3/8$ | $(2,2,2)$ |

Substitution reconstructs every source row exactly. In particular, the bad-
output equality is never relaxed to an inequality, and no intensity-sum row
is added.

## 6. Independent dense-LP corroboration

During the source audit, the arrays in Section 1 were constructed directly
and solved with `scipy.optimize.linprog(method="highs")`. The numerical
solutions matched every rational value in the oracle vector. This was an
independent formulation check: it did not import or call a DEAPack production
compiler, model, reference builder, or result transformation.

The evidence level nevertheless remains `analytically_derived` because:

1. the fixture is synthetic rather than published by Zhou, Ang, and Wang;
2. no production implementation exists for a public-versus-independent
   comparison; and
3. the complete 126-country reference observations required to reproduce the
   article's empirical results have not been located in an auditable bundle.

A future executable oracle should reproduce these exact values with a dense
compiler local to its test module. Using the same HiGHS backend as production
would still establish independent problem compilation, not an
independent-solver reproduction.

## 7. Required invariance and failure checks

For each source preset, multiplying all evaluated and reference $F$, $E$, or
$C$ quantities by its own positive unit factor co-scales the observed-value
direction and the corresponding LP row. The feasible $(a,d,o,\beta)$ set is
unchanged. A future executable certificate must therefore retain component
steps, peer intensities, $D^{NR}$, and the performance index while co-scaling
the relevant target quantities.

It must also establish that:

- inactive components are fixed at zero rather than left free;
- a non-optimal or unbounded solve yields no score or target;
- the raw objective and transformed index are reported separately;
- target and peer uniqueness are not inferred from score uniqueness; and
- the printed CHP equation (12) is not executed under this candidate.

## 8. Claim boundary

| Claim | Evidence | Scope |
|---|---|---|
| source equation (7) compilation | exact row construction and substitution | one positive input, one positive good output, one positive bad output; CRS $T_1$ |
| three source presets | exact component upper bounds and attaining plans | self-inclusive cross-section; observed-value directions and published weights only |
| score and target reconstruction | rational oracle vector | organization O against the three-organization reference population |
| independent LP assembly | stand-alone dense SciPy/HiGHS check | formulation corroboration only; no production parity claim |
| coherent unit invariance | row co-scaling argument | independent positive changes to $F$, $E$, and $C$ units with directions co-scaled |

This certificate does **not** cover:

- the 82-country non-CHP application, the full 126-country study, Appendix C,
  or any reported country mean, rank, frontier membership, or test statistic;
- the $T_2$/CHP programme or any inferred correction to equation (12);
- arbitrary directions or weights, additional variables, or another score
  transform;
- VRS/NIRS/NDRS, external/custom/leave-one-out/panel references, productivity,
  or cross-period comparisons;
- zero, negative, missing, or interval data;
- strong or activity-specific disposal, by-production, material balance,
  treatment, network, dynamic, SBM, or hyperbolic technology/measure claims;
  or
- unique peers or targets, prices, damages, welfare, engineering feasibility,
  causal effects, or policy prescriptions.

Every excluded branch remains `deferred_to_next_version` until its own source
and oracle gate closes.
