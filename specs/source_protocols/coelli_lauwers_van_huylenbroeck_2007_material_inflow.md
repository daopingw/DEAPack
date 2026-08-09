# Coelli--Lauwers--Van Huylenbroeck material-inflow efficiency

## Readiness record

| Field | State |
|---|---|
| Current method ID | `environmental.material_inflow.coelli2007` |
| Primary article | obtained and bibliographically checked |
| Authoritative full equation source | obtained: CEPA Working Paper 06/2005 |
| Source equations frozen | materials balance (2); minimum material inflow (11); DEA programmes (23)--(24); $EE$ and $EAE$ (25)--(26) |
| Current numerical certificate | `analytically_derived` under source-native CRS and source-described VRS |
| Published application reproduction | `not_reproduced`; the unit-level 183-farm observations are not supplied |
| Production compiler reused by oracle | `false` |
| Current API | `MaterialBalanceDEA`; discoverability alias `CoelliMaterialBalanceDEA` |
| Release disposition | admitted only for the claim-scoped domain below |
| Last access audit | 2026-07-31 |

The current claim is narrower than everything that could be built around a
materials-balance identity. It covers one physical material account, known
common nonnegative coefficients, an ordinary nonnegative input/output
cross-section, a self-inclusive comparison population, fixed observed
desirable output, and either CRS or VRS. It does not turn calculated material
surplus into an independently observed bad output, an environmental-damage
measure, or a causal abatement effect.

## 1. Defining sources

The defining journal article is:

- Tim Coelli, Ludwig Lauwers, and Guido Van Huylenbroeck (2007),
  “Environmental Efficiency Measurement and the Materials Balance
  Condition,” *Journal of Productivity Analysis*, 28(1--2), 3--12.
  [DOI](https://doi.org/10.1007/s11123-007-0052-8).

The complete equation audit uses the authors' longer first-hand version:

- Tim Coelli, Ludwig Lauwers, and Guido Van Huylenbroeck (2005),
  “Formulation of Technical, Economic and Environmental Efficiency Measures
  That Are Consistent With the Materials Balance Condition,” CEPA Working
  Paper 06/2005, University of Queensland.
  [Official full PDF](https://economics.uq.edu.au/files/5310/WP062005.pdf).

The [UGent bibliographic record](https://biblio.ugent.be/publication/437435)
independently confirms the journal metadata. The working paper is used for
equation locators because it exposes the full derivation and the explicit
CRS/VRS footnote. This is not a reconstruction from a secondary review.

## 2. Frozen economic account

For a producer using nonnegative inputs $x\in\mathbb{R}_+^m$ to supply
desirable output $y\in\mathbb{R}_+^s$, the source defines material surplus as

$$
z=a'x-b'y,
\qquad a\ge0,\quad b\ge0.
$$

$a'x$ is material entering with inputs, $b'y$ is material retained in useful
output, and $z$ is the residual under the declared system boundary. DEAPack
uses $c$ instead of the source's $b$ for desirable-output contents so that
$b$ remains available for undesirable-output notation elsewhere in the
book:

$$
z_{ho}=a_h'x_o-c_h'y_o.
$$

This is a notational translation only.

Holding $y_o$ fixed makes $c'y_o$ constant. Consequently, minimizing surplus
and minimizing material inflow select the same input plans, although the
ratio of target to observed inflow is not the ratio of target to observed
surplus. The source defines the minimum-inflow plan by equation (11):

$$
x_o^e\in
\arg\min_x\left\{a'x:(x,y_o)\in T\right\}.
$$

The managerial question is therefore: which technically feasible input mix
contains the least declared material while preserving the current service
commitment? It is not automatically the least-cost, profit-maximizing, or
socially optimal plan.

## 3. Source DEA programmes

With observed input matrix $X$, desirable-output matrix $Y$, and evaluated
producer $o$, working-paper equation (23) is the input-radial technical
programme

$$
\begin{aligned}
TE_o=\min_{\theta,\lambda}\quad &\theta\\
\text{s.t.}\quad
&Y\lambda\ge y_o,\\
&X\lambda\le\theta x_o,\\
&\lambda\ge0.
\end{aligned}
$$

Equation (24) is the material-inflow programme

$$
\begin{aligned}
\min_{\lambda,x_o^e}\quad &a'x_o^e\\
\text{s.t.}\quad
&Y\lambda\ge y_o,\\
&X\lambda\le x_o^e,\\
&\lambda\ge0.
\end{aligned}
$$

These displayed programmes are CRS. Footnote 6 states that VRS is obtained
by adding $\mathbf 1'\lambda=1$ to **both** programmes. No equivalent
source statement has been frozen here for NIRS or NDRS, so the current
constructor rejects those two settings.

Working-paper equations (25)--(26) define

$$
EE_o=\frac{a'x_o^e}{a'x_o},
\qquad
EAE_o=\frac{EE_o}{TE_o},
\qquad
EE_o=TE_o\times EAE_o.
$$

`EAE` is “allocative” with respect to physical material-content
relativities. Prices are not an input to this decomposition. A lower-material
mix can lower private cost, leave it unchanged, or cost more.

## 4. Package compilation equivalence

`MaterialBalanceDEA` solves equation (23) directly. For equation (24), it
eliminates the explicit $x_o^e$ variables and solves

$$
\min_{\lambda}\ a'X\lambda
\quad\text{s.t.}\quad
Y\lambda\ge y_o
$$

with the same CRS or VRS intensity restriction. The reduction is valid on the
certified domain because $a\ge0$: for every feasible $\lambda$, choosing
$x_o^e=X\lambda$ is feasible and cannot have a larger objective than any
$x_o^e\ge X\lambda$. This establishes equality of optimal objective values
and supplies one valid minimum-material target.

If some input has zero material content, equation (24) can have multiple
optimal $x_o^e$ vectors or peer portfolios. The package reports one
solver-selected $X\lambda$ plan. It does not claim a unique, closest,
least-cost, or Pareto--Koopmans target. `is_material_efficient` therefore
records only the native material-inflow criterion; it is not promoted to the
generic `is_efficient` field.

Desirable-output contents do not enter the minimum-inflow objective because
$y_o$ is fixed. They remain essential to the reported physical surplus
account. Every coefficient, including zero, must be declared by variable
name, and the observed input content must cover retained output content under
the stated boundary.

## 5. Independent exact certificate

The executable certificate is
`tests/test_material_balance_independent_oracle.py`. Its dense SciPy compiler
does not import DEAPack technology, reference, model-compilation, or LP
construction helpers. In particular, it keeps the source's explicit
$x_o^e$ variables in equation (24), whereas production code eliminates them.

### 5.1 CRS fixture

Three producers use two inputs to supply one output:

| DMU | $x_1$ | $x_2$ | $y$ | $a'x$, with $a=(1,3)$ |
|---|---:|---:|---:|---:|
| A | 1 | 3 | 1 | 10 |
| B | 3 | 1 | 1 | 6 |
| C | 8 | 8 | 2 | 32 |

The desirable output retains two units of material per unit, so
$c=(2)$. The exact account is:

| DMU | $TE$ | minimum inflow | $EE$ | $EAE$ | minimum surplus |
|---|---:|---:|---:|---:|---:|
| A | $1$ | $6$ | $3/5$ | $3/5$ | $4$ |
| B | $1$ | $6$ | $1$ | $1$ | $4$ |
| C | $1/2$ | $12$ | $3/8$ | $3/4$ | $8$ |

For C, the technical peer account uses one copy each of A and B, giving the
radial target $(4,4)$. The material programme uses two copies of B, giving
the input target $(6,2)$ and inflow 12. The independent compiler and public
API agree on every score, component, target, and stated peer intensity.

### 5.2 VRS fixture

The book's fixed-output case adds C $(2,2)$ and D $(4,4)$ to A and B, with
all four producing $y=1$, $a=(1,3)$, and $c=(1)$. VRS gives:

- C: $TE=1$, $EE=EAE=3/4$;
- D: technical target $(2,2)$, $TE=1/2$;
- D: material target $(3,1)$, $EE=3/8$, $EAE=3/4$.

Thus D's common resource waste and its material-bearing input-mix shortfall
are numerically distinct. The exact identity is
$3/8=(1/2)(3/4)$.

### 5.3 Additional obligations

The certificate also checks:

- every public CRS and VRS observation against independently compiled
  equations (23)--(26);
- coherent input- and output-unit changes with reciprocal coefficient
  transformations, including co-transformed targets;
- a zero-content-input fixture in which distinct input plans have the same
  source objective, freezing the nonuniqueness boundary;
- the exact physical-surplus account separately from the inflow ratio.

The ordinary production tests separately cover coefficient domains,
bad-output rejection, the materials identity, solver-selected target labels,
and fail-closed NIRS/NDRS.

## 6. Claim boundary

The current analytical certificate is not a reproduction of the published
Belgian pig-farm application. The working paper reports a representative
cross-section of 183 farms, summary statistics, mean scores, and selected
frontier quantities, but it does not supply the unit-level observations.
DEAPack therefore makes no farm-level or published-table reproduction claim.

The current source-equivalence claim also excludes:

- NIRS and NDRS;
- panel, window, custom, leave-one-out, and external-reference equivalence;
- heterogeneous or estimated material-content coefficients;
- observed bad-output columns or a second pollution account for the same
  residual;
- explicit input-consuming treatment or end-of-pipe abatement;
- inventory accumulation, unmeasured losses, and stock pollutants;
- causal effects, realized discharge, damage, welfare, compliance, or policy
  valuation;
- a unique, closest, least-cost, profit-maximizing, or prescriptive target.

The production implementation can reuse shared reference machinery for
exploratory extensions, but those paths do not inherit the present
source-native certificate.

## 7. Source-described but next-version extensions

The working paper does discuss more than one pollutant. Equations (18)--(21)
show separate material identities and an explicitly weighted aggregate. The
package already requires positive user-supplied weights before combining
unlike material accounts. This feature is not being described as absent from
the source; rather, its own independent analytical promotion is
`deferred_to_next_version`.

The source also discusses social-cost augmentation and possible abatement
outputs. Those passages motivate separate valuation and treatment models;
they do not certify silently adding a price, bad-output, or treatment switch
to the current leaf. Heterogeneous coefficients, explicit treatment,
multiple-material aggregation, and non-cross-sectional reference policies
must each return through the evidence gate with a frozen programme and an
independent executable certificate.

Candidates whose defining material cannot be located remain
`deferred_to_next_version` without a current API. For this method, the source
is available; the deferred status above is claim-specific and records the
additional validation still required.
