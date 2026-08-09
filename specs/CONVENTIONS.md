# DEAPack notation and reporting conventions

This document is the normative notation contract for package code, the book,
package documentation, examples, and figures.

## 1. Indices and dimensions

| Symbol | Code name | Meaning |
|---|---|---|
| $j=1,\ldots,n$ | `dmu` | reference decision-making unit |
| $o$ | `evaluated_dmu` | decision-making unit being evaluated |
| $i=1,\ldots,m$ | `input` | input dimension |
| $r=1,\ldots,s$ | `output` | desirable-output dimension |
| $h=1,\ldots,q$ | `bad_output` | undesirable-output dimension |
| $t=1,\ldots,T$ | `period` | time period |
| $\sigma,\tau\in\{1,\ldots,T\}$ | `evaluated_period`, `technology_period` | evaluated-plan period and reference-technology period in a generic productivity task |
| $k,\ell=1,\ldots,K$ | `process` | internal process, division, or production stage |
| $\kappa=1,\ldots,G$ | `group` | technology group when applicable |

`DMU` is retained in prose because it is standard in the literature. Public
code uses `dmu` for values and `dmu_id` for identifier columns.

In network sections, an ordered pair $(k,\ell)$ denotes a directed internal
flow from supplying process $k$ to receiving process $\ell$. This notation
keeps process indices distinct from $r$, the desirable-output dimension, and
$h$, the undesirable-output dimension.

Source-local notation may be retained only when the corresponding chapter or
model page gives an explicit crosswalk to this core notation.

## 2. Observations and matrices

For DMU $j$ in period $t$:

- $x_j^t\in\mathbb{R}_+^m$: input vector;
- $y_j^t\in\mathbb{R}_+^s$: desirable-output vector;
- $b_j^t\in\mathbb{R}_+^q$: undesirable-output vector.

Reference matrices place DMUs in columns in mathematical expressions:

- $X=[x_1,\ldots,x_n]\in\mathbb{R}^{m\times n}$;
- $Y=[y_1,\ldots,y_n]\in\mathbb{R}^{s\times n}$;
- $B=[b_1,\ldots,b_n]\in\mathbb{R}^{q\times n}$.

Tabular user data place DMUs in rows. The compiler performs the conversion
once; inner solver loops never index pandas objects.

Negative or zero values are not silently shifted. A measure must explicitly
declare whether it supports them and which invariance property justifies the
operation.

## 3. Technology

$\mathcal{T}^t$ denotes the production technology available in period $t$:

$$
\mathcal{T}^t=\{(x,y,b):x\text{ can produce }(y,b)\}.
$$

When undesirable outputs are absent, write $\mathcal{T}^t=\{(x,y)\}$ rather
than retaining an empty $b$ in displayed equations.

$\lambda\in\mathbb{R}_+^n$ denotes the intensity vector. Returns-to-scale
restrictions are named as follows:

| Name | Code | Restriction |
|---|---|---|
| constant returns to scale | `crs` | $\lambda\ge 0$ |
| variable returns to scale | `vrs` | $\mathbf{1}^\top\lambda=1$ |
| non-increasing returns to scale | `nirs` | $\mathbf{1}^\top\lambda\le 1$ |
| non-decreasing returns to scale | `ndrs` | $\mathbf{1}^\top\lambda\ge 1$ |

Convexity, returns to scale, disposability, internal structure, and reference
period are separate technology attributes. A model name must not hide them.

## 4. Radial measures

The input-oriented Farrell efficiency score is $\theta_o$:

$$
\min_{\theta,\lambda}\ \theta
\quad\text{s.t.}\quad
X\lambda\le\theta x_o,\quad
Y\lambda\ge y_o.
$$

The output expansion factor is $\phi_o$:

$$
\max_{\phi,\lambda}\ \phi
\quad\text{s.t.}\quad
X\lambda\le x_o,\quad
Y\lambda\ge\phi y_o.
$$

The standardized output-oriented efficiency is $1/\phi_o$. The package never
labels $\phi_o$ itself as a bounded efficiency score.

`CCR` and `BCC` are discoverability constructors for the CRS and VRS
specializations of the same radial DEA family. `BCC` is the only normative
spelling. The historical DEAPack misspelling `BBC` is not a public or
deprecated alias in 2.0; legacy code must migrate it to `BCC`.

The complete classic presets are `CCRInput`, `CCROutput`, `BCCInput`, and
`BCCOutput`. They retain canonical `method_id="static.radial"` and emit their
own `preset_id`; they fix RTS, orientation, the native $\theta$ or $\phi$
convention, and `compute_slacks=True` with DEAPack's row-scaled
lexicographic slack/target completion. This target selector is a package
policy for alternate radial optima, not a claim that the foundational paper
uniquely prescribed it.

### 4.1 Non-convex radial FDH

The standard free-disposal hull contains one freely disposable orthant for
each observed activity:

$$
\widehat{\mathcal T}_{FDH}
=\{(x,y):\exists j,\ x_j\leq x,\ y_j\geq y\}.
$$

It does not convexify or rescale activities. `FreeDisposalHullDEA`/`FDH`
therefore has no returns-to-scale parameter and uses canonical method ID
`static.radial.fdh`.

For input orientation:

$$
\theta_o^{FDH}
=
\min_{j:y_j\geq y_o,\;x_{ij}=0\ \forall i:x_{io}=0}
\max_{i:x_{io}>0}\frac{x_{ij}}{x_{io}}.
$$

For output orientation:

$$
\phi_o^{FDH}
=
\max_{j:x_j\leq x_o}
\min_{r:y_{ro}>0}\frac{y_{rj}}{y_{ro}}.
$$

Zero denominators are excluded only after imposing their exact feasibility
condition: a zero evaluated input requires a zero peer input, while a zero
evaluated output does not constrain proportional output expansion and may
appear as residual output slack. No epsilon is inserted.

`score` reports native $\theta$ or $\phi`; `efficiency` reports $\theta$ or
$1/\phi$ when the reciprocal exists. With self-inclusive references these
standardized efficiencies lie in $[0,1]$. A custom reference may exclude the
evaluated activity; outside-reference comparisons retain their native score
but leave efficiency classifications missing.

Every FDH intensity row is one alternative binary peer with
`lambda=1`. Tied rows are not a convex combination and must not be summed.
When slacks are requested, one radial peer is selected lexicographically by
the maximum unweighted residual improvement and supplies the reported target.

### 4.2 Scale efficiency as a matched score-only composition

For one orientation, quantity system, period policy, and reference population,
scale efficiency is

$$
SE_o=\frac{TE_o^{CRS}}{TE_o^{VRS}}.
$$

The two components are separate score-only radial fits; no slack-completion
phase is part of this ratio. When both certified component efficiencies are
positive, the matched CRS technology contains its VRS counterpart, so
$SE_o\leq1$ up to numerical tolerance even if an external reference makes a
component efficiency exceed one. Conventional `is_scale_efficient`
classification is narrower: it is reported only when the evaluated plan is
certified as belonging to both component technologies. An external
institutional ratio remains numerically visible, but the classification is
missing rather than inferred from $SE_o=1$.

### 4.3 Deferred fixed-mix maximum-average-productivity notation

MPSS remains an economically distinct question about the scale at which a
fixed input--output mix reaches maximum average productivity. The defining
Banker (1984) article has not been obtained in a form that permits an
equation-level freeze, so the formulae in this subsection document only the
review-supported, non-public prototype. They are provisional and are not a
current package score contract. For candidate proportional plans
$(\alpha x_o,\beta y_o)$ in the reconstructed convex VRS account, write

$$
\rho_o^{MPSS}
=
\max_{\alpha,\beta,\mu}\frac{\beta}{\alpha},
\qquad
X\mu\leq\alpha x_o,\quad
Y\mu\geq\beta y_o,\quad
\mathbf 1^\top\mu=1.
$$

If this reconstruction is confirmed under a self-inclusive reference,
$\rho_o^{MPSS}\geq1$ and smaller would be better: one would mean that the
observed proportional plan already attains the reconstructed technology's
maximum average productivity. No current public result field is assigned this
meaning.

The prototype uses an output-CRS Charnes--Cooper normalization. Under that
candidate transformation, if $t=\mathbf 1^\top\lambda$, then
$\alpha=1/t$ and $\beta=\rho_o^{MPSS}/t$; the admissible extrema of $t$
would produce the smallest and largest scale endpoints. The provisional
quantity is never written as a bare $\rho_o$ in cross-method prose:
$\rho_o^{MPSS}$ remains conceptually distinct from non-oriented SBM scores
$\rho_o^{NO}$ and return-to-dollar $\rho_o^{RTD}$. Promotion, exact
attribution, and public field semantics are `deferred_to_next_version`.

### 4.4 Deferred short-run physical-capacity notation

Short-run physical capacity asks what the installed quasi-fixed resource base
could support while variable resources adjust. The defining Färe--Grosskopf--
Kokkelenberg (1989) article has not been equation-frozen, so the two-program
account below is a review-supported reconstruction retained for a non-public
prototype, not a current method convention. It provisionally partitions
inputs before fitting:

$$
x_o=(x_o^f,x_o^v),
$$

where $x_o^f$ is unavailable for adjustment over the declared operating
horizon and $x_o^v$ may adjust. The prototype uses two CRS output-expansion
factors over the same comparison population and output proportions:

$$
\begin{aligned}
\phi_o^T
&=\max\{\phi:X^f\lambda\leq x_o^f,\;
X^v\lambda\leq x_o^v,\;Y\lambda\geq\phi y_o,\;\lambda\geq0\},\\
\phi_o^C
&=\max\{\phi:X^f\lambda\leq x_o^f,\;
Y\lambda\geq\phi y_o,\;\lambda\geq0\}.
\end{aligned}
$$

The superscripts provisionally mean **current technical input limits** and
**physical capacity**, respectively; they are not proposed user
orientations. There is no public source-qualified leaf, RTS switch, or
output-mix switch in the current release.

The reconstructed reporting identity under audit is:

$$
TE_o^O=\frac1{\phi_o^T},\qquad
CU_o^{obs}=\frac1{\phi_o^C},\qquad
CU_o^{adj}=\frac{\phi_o^T}{\phi_o^C},
\qquad
CU_o^{obs}=TE_o^O\,CU_o^{adj}.
$$

The internal prototype has draft fields corresponding to these components,
but none is a public `score`, `efficiency`, target, or
Pareto--Koopmans-status contract. Under the reconstructed programme, the
candidate target preserves evaluated output proportions and holds only the
declared quasi-fixed input limits. A solver-selected variable-input
requirement would be a supporting technical activity, not a unique staffing
plan, demand forecast, economic optimum, or investment instruction.
Physical capacity, economic capacity, MPSS, scale efficiency, and congestion
remain separate conceptual families; public method IDs for the first and
third await their next-version source and oracle gates.

## 5. Additive measures

The source-qualified Charnes et al. (1985) direct additive profile is VRS,
uses one self-inclusive cross-section, and maximizes the unit slack sum:

$$
\delta_o^{A}=\max_{\lambda,s^-,s^+}
\left(\sum_{i=1}^m s_i^-+\sum_{r=1}^s s_r^+\right)
$$

subject to

$$
X\lambda+s^-=x_o,\qquad
Y\lambda-s^+=y_o,
\qquad
\mathbf 1^\top\lambda=1,
$$

and $\lambda,s^-,s^+\ge0$. Only this VRS/unit-weight/full-cross-section
configuration inherits the 1985 equation-(4.6) certificate. An explicitly
declared all-one vector is the same unit-weight configuration; provenance is
recorded without changing the mathematical identity.

DEAPack's configurable extension lets
$\omega_i^x>0$ and $\omega_r^y>0$ denote declared input- and output-slack
weights:

$$
\delta_o=\max_{\lambda,s^-,s^+}
\left(\sum_{i=1}^m\omega_i^x s_i^-
+\sum_{r=1}^s\omega_r^y s_r^+\right)
$$

under an explicitly selected RTS and reference policy. These configurations
use the same optimization engine but do not acquire a separate historical
identity. Charnes et al.'s equation (5.7) instead uses
evaluated-observation reciprocal quantities; it is not an arbitrary fixed
weight vector.

$\delta_o=0$ indicates Pareto--Koopmans efficiency and larger values indicate
more weighted slack. Unless the weights define a named unit-invariant
normalization, $\delta_o$ is not a bounded efficiency score. DEAPack therefore
reports it as both the native `score` and `distance`, while leaving
`efficiency` missing. The exact weights are retained in result metadata and in
the long-form slack table. VRS balances use one reference-set anchor and
reference-deviation scales; the anchored reference matrix is compiled once
per comparison population. Other RTS paths use positive level scales. One
common objective scale preserves the physical weighted-slack objective.
Physical slacks remain unchanged, while `scaled_slack` and
`max_scaled_slack` use maximum reference deviations for a unit- and
VRS-translation-stable strong-status tolerance; solver-variable scaling is
reported separately. Effective solver feasibility tolerances are recorded,
and an objective coefficient too small for the backend fails closed. A
separately named additive leaf without an available defining source and
independent oracle is
`deferred_to_next_version`.

The range-adjusted measure (RAM) is the named VRS normalization:

$$
\delta_o^{RAM}=\frac{1}{m+s}
\left(\sum_i\frac{s_i^-}{R_i^x}
+\sum_r\frac{s_r^+}{R_r^y}\right),
\qquad
\rho_o^{RAM}=1-\delta_o^{RAM},
$$

where $R_i^x=\max_j x_{ij}-\min_j x_{ij}$ and
$R_r^y=\max_j y_{rj}-\min_j y_{rj}$. `score` and `efficiency` report
$\rho_o^{RAM}\in[0,1]$; `distance` reports
$\delta_o^{RAM}\in[0,1]$. Zero-range variables receive zero objective weight
and their VRS balance equations force zero slack. The range population and
zero-range policy must be stored in metadata.

## 6. Slacks-based measure

Tone's standard input-, output-, and non-oriented SBM presets use the same
black-box convex technology, reference set, and balance account:

$$
X\lambda+s^-=x_o,\qquad
Y\lambda-s^+=y_o,
$$

with the selected CRS, VRS, NIRS, or NDRS restriction. Their native
higher-is-better scores are:

$$
\rho_o^I
=1-\frac{1}{m}\sum_i\frac{s_i^-}{x_{io}},
\qquad
\rho_o^O
=\left(1+\frac{1}{s}\sum_r\frac{s_r^+}{y_{ro}}\right)^{-1},
$$

and

$$
\rho_o^{NO}=
\frac{1-\frac{1}{m}\sum_i s_i^-/x_{io}}
{1+\frac{1}{s}\sum_r s_r^+/y_{ro}}.
$$

Tone (2001) writes the base CRS technology and explicitly notes the VRS
convexity restriction. NIRS and NDRS are supported through DEAPack's common
convex-envelopment technology layer and are labelled
`deapack_convex_envelopment_variant` in result metadata rather than attributed
to Tone as separate source presets.

Thus input orientation values only normalized input excess while maintaining
at least the observed outputs; output orientation values only normalized
output expansion while using no more than the observed inputs. The
non-oriented measure values both accounts. Sharing the technology,
reference-plan cache, and sparse balance compiler does not merge these
objectives: they are Level B distinct measures. The input and output
orientations are direct LPs; only the non-oriented ratio requires the
Charnes--Cooper transformation.

For all three presets, `score` and `efficiency` report the orientation-specific
$\rho_o^I$, $\rho_o^O$, or $\rho_o^{NO}$ in $[0,1]$ on the stated
self-inclusive domain, while `distance` reports one minus that score. Output orientation
also reports
$\tau_o^O=1+s^{-1}\sum_r s_r^+/y_{ro}=1/\rho_o^O$ as
`output_expansion_factor`. An input-oriented
score of one certifies the input side only, and an output-oriented score of
one certifies the output side only. Accordingly, `is_sbm_efficient` is
orientation-specific, while the generic Pareto--Koopmans `is_efficient` is
not certified by either single orientation. Slacks and targets on the side
omitted from the objective are feasible values from one solver-selected
primary optimum; their `selection_status` is
`solver_selected_primary_optimum`, not a uniqueness or strong-target claim.
The non-oriented preset can certify zero normalized slacks on both sides, but
its target can still be one of several primary optima.

The implementation requires strictly positive
$x_{io}$ and $y_{ro}$ because they are explicit denominators; zero and
negative-data variants must be selected explicitly rather than created by an
undocumented shift or epsilon.

The summary retains both mean normalized slack accounts, including the side
not optimized by an oriented leaf. The non-oriented linear solver works in
transformed coordinates; public slacks, intensities, and targets from every
orientation are returned on the original scale. The `sbm_slack_contrast` data reproduce Tone
(2001), Table 2's non-oriented CRS scores and selected slacks. No published
numerical oracle has been located for the input- or output-oriented leaf, so
their current validation status is property evidence rather than a
literature oracle.

The separable undesirable-output SBM is:

$$
\rho_o^B=
\frac{1-\frac{1}{m}\sum_i s_i^-/x_{io}}
{1+\frac{1}{s+q}\left(
\sum_r s_r^+/y_{ro}+\sum_h s_h^b/b_{ho}\right)},
$$

subject to:

$$
X\lambda+s^-=x_o,\qquad
Y\lambda-s^+=y_o,\qquad
B\lambda+s^b=b_o.
$$

Here $s^b$ is potential bad-output contraction and the last equality encodes
strong disposability. This Tone-style separable model is exposed as
`UndesirableSlacksBasedDEA`/`UndesirableSBM`; it is not labeled weakly
disposable and does not impose null-jointness. Good- and bad-output normalized
slacks receive equal dimension weights $1/(s+q)$. The implementation requires
strictly positive inputs, good outputs, and bad outputs because all are
explicit denominators. Composing SBM with weak disposal requires a separately
validated production technology. Tone's nonseparable hybrid instead changes
the variable partition and measure/estimator contract. Neither can be hidden
as a sign or label option inside this formula.

For reporting, write

$$
I_o^y=\frac1s\sum_r s_r^+/y_{ro},\qquad
I_o^b=\frac1q\sum_h s_h^b/b_{ho},\qquad
I_o^{yb}=\frac{sI_o^y+qI_o^b}{s+q}.
$$

Thus `output_inefficiency` is a dimension-weighted combination of the good-
and bad-output subaccount means, not their unweighted 1:1 average unless
$s=q$. A certified external SBM balance proves membership of the assessed
plan in the reference technology; infeasibility proves non-membership, while
an uncertified numerical failure leaves membership and classification missing.

## 7. Directional distance

Direction magnitudes $g^x,g^y,g^b$ are nonnegative. Signs are expressed in
the movement, not embedded ambiguously inside the supplied magnitudes:

$$
D_{\mathcal{T}}(x,y,b;g^x,g^y,g^b)
=\sup\{\beta:(x-\beta g^x,\ y+\beta g^y,\ b-\beta g^b)
\in\mathcal{T}\}.
$$

Thus a positive $g^x$ contracts inputs, a positive $g^y$ expands desirable
outputs, and a positive $g^b$ contracts undesirable outputs. Zero components
declare no first-stage movement in the corresponding variables. Their observed
inputs remain feasibility caps and their observed outputs remain feasibility
floors, so a later slack-completion step may still reveal a variable-specific
improvement.

For a self-inclusive reference under the maintained nonnegative-distance
policy, the native DDF value is $\beta_o\ge0$ and larger values represent more
room for improvement. If a bounded display score is needed, DEAPack may
report $1/(1+\beta_o)$ as `efficiency` only when membership of the assessed
plan in the reference technology is certified; it must also retain and
prominently label the native `distance` value. Under equality-based external
appraisal, a positive directional target need not prove membership of the
unchanged assessed plan, so a separate beta-zero feasibility account may be
required before transformation or classification.

This membership rule applies to both the named CRS common-factor equality
technology and the VRS activity-specific equality technology. Structural self
inclusion certifies membership without another optimization task. A certified
negative distance establishes non-membership. Otherwise an external row uses a
beta-zero feasibility programme over the same scaled production balances;
feasibility, infeasibility, and an uncertified numerical outcome mean inside,
outside, and unknown, respectively. The native distance and a separately
certified target do not borrow this gate, but `efficiency` and every efficiency
classification do.

For explicitly requested cross-technology evaluation, a negative $\beta_o$
may be permitted to describe an observation outside the reference technology.
In that case standardized `efficiency` and efficiency classification are
missing rather than extended beyond their meaningful domain.

The first phase maximizes $\beta_o$. An optional lexicographic second phase
fixes $\beta_o$ and maximizes a row-scaled account of the remaining $s^-$ and
$s^+$, so measurement units cannot select the target and directional
efficiency remains distinct from Pareto--Koopmans efficiency. Physical slacks
are converted back to the original units for reporting.

### 7.1 Chavas--Cox generalized distance

For the implemented Chavas--Cox convention, $\alpha\in[0,1]$ states how a
proportional performance gap is expressed between resource saving and service
growth:

$$
D_G(x_o,y_o;\alpha)
=
\min_{\delta>0}
\left\{
\delta:
\left(\delta^{1-\alpha}x_o,\delta^{-\alpha}y_o\right)
\in\mathcal T
\right\}.
$$

The public native score is $\delta$. `score`, `efficiency`, and
`generalized_distance` all report this higher-is-better value. With a
self-inclusive reference technology, $0<\delta\leq1$.

For backward compatibility, the summary retains the legacy-named fields

$$
\texttt{resource_commitment}=\delta^{1-\alpha},
\qquad
\texttt{service_commitment}=\delta^{-\alpha},
$$

as well as one minus the first and the second minus one in
`resource_saving_pct` and `service_growth_pct`. The exact endpoint and
balanced-path transformations are:

$$
\alpha=0:\ \delta=\theta^I,\qquad
\alpha=1:\ \delta=1/\phi^O,\qquad
\alpha=1/2:\ \delta=h^2.
$$

The conditional algebra $h=\sqrt{\delta}$ at $\alpha=1/2$ does not create a
public standard-hyperbolic result field. Until that method's source-native
score and independent oracle are frozen, GDF reports only $\delta$ and its
resource/service path commitments.

Under ordinary CRS, $\delta=\theta^{CRS}$ for every $\alpha$; the
declared operating counterfactual changes target multipliers and peer intensities,
not the total productivity gap. Under VRS, the convexity restriction prevents
free replication, so both the score and the comparator mix may change with
$\alpha$.

GDF is not an alias for the DDF. DDF describes an additive quantity-change
counterfactual with direction units. GDF describes a multiplicative
proportional counterfactual. Their shared technology matrices do not merge
their scores, targets, or economic meanings.

The GDF target table distinguishes:

- `path_target`, the algebraic proportional counterfactual;
- `phase_one_reference_activity`, the feasible peer operation supporting the
  score; and
- `target`, the row-scaled slack-completed peer operation.

`is_gdf_efficient` tests $\delta=1$. `is_efficient` has the stronger
Pareto--Koopmans meaning and is populated only when the optional
slack-completion phase certifies it. The phase-two objective uses positive
row-scaled slack weights so independent positive unit changes do not change
the selected strong-efficiency status or completed target after conversion
back to original units.

### 7.2 Multiplicative DEA

For multiplicative DEA, hats denote coordinatewise logarithms rather than
estimated physical quantities:

$$
\widehat x=\log x,
\qquad
\widehat y=\log y.
$$

The public family retains the native compound account

$$
D_o^{\mathrm{mult}}
=\delta\left(\mathbf1^\top s^-+\mathbf1^\top s^+\right),
\qquad
E_o^{\mathrm{mult}}=\exp(-D_o^{\mathrm{mult}}).
$$

`distance` and `log_inefficiency` report
$D_o^{\mathrm{mult}}\geq0`; `score`, `efficiency`, and
`multiplicative_efficiency` report the higher-is-better
$E_o^{\mathrm{mult}}\in(0,1]$ on a certified self-inclusive task. Log
slacks remain the native dimensionless adjustments; `slack` is their
original-unit resource saving or service increase.

The 1982 source preset is `log_conic`, fixes $\delta=1$, requires every
quantity to exceed one, and is not unit invariant. The 1983 source preset is
`log_convex`, adds $\mathbf1^\top\lambda=1$, permits every strictly positive
quantity, and reconstructs geometric peer targets. These labels are not
ordinary physical-space CRS/VRS. A positive unit change is supported as an
invariance only for the 1983 preset; an additive translation of physical
quantities is unsupported for both. The exponent rows are frontier weights,
not prices or causal elasticities.

### 7.3 Relative-directional scale elasticity

Ren et al.'s relative-directional VRS operator is defined at a selected
Pareto-efficient target $(\widehat x_o,\widehat y_o)$. Nonnegative vectors
$\omega\in\mathbb R_+^m$ and $\delta\in\mathbb R_+^s$ describe relative
percentage rates:

$$
x_i(t)=(1+\omega_i t)\widehat x_{io},
\qquad
y_r(\beta)=(1+\delta_r\beta)\widehat y_{ro}.
$$

The public contract requires the source normalization to be supplied rather
than inferred:

$$
\sum_{i=1}^m\omega_i=m,\qquad
\sum_{r=1}^s\delta_r=s.
$$

DEAPack never silently rescales these vectors. A zero target makes that
variable's relative-rate contribution inactive; the operator fails closed
only when the aggregate input or output directional rate base is
nonpositive.

Using the support convention
$v^\top x_j-u^\top y_j+u_0\geq0$, the right/scale-up and
left/scale-down endpoints are

$$
\epsilon^+
=
\min v^\top(\omega\odot \widehat x_o),
\qquad
\epsilon^-
=
\max v^\top(\omega\odot \widehat x_o),
$$

subject to

$$
v^\top \widehat x_o-u^\top \widehat y_o+u_0=0,\qquad
u^\top(\delta\odot \widehat y_o)=1,\qquad
u,v\geq0,\quad u_0\ \text{free}.
$$

Finite endpoints satisfy $\epsilon^+\leq\epsilon^-$. Values above, equal to,
or below one mean more-than-proportional, proportional, or
less-than-proportional output response to the declared relative resource
change on that side. An extended endpoint and the existence of a feasible
one-sided perturbation are stored separately.

If both relative direction vectors contain only ones, the endpoints reduce
exactly to the matched radial VRS scale elasticities at the same reference
set, projection orientation, selected target, completion policy, and
tolerances. This relative percentage response is not an additive physical-unit
DDF. Its vectors are described as management preferences only when the study
records that responsible decision-makers elicited and adopted them; otherwise
they remain authorized, literature-prescribed, or analyst-defined
counterfactuals.

## 8. Relational two-stage network efficiency

For the basic series system, $x_o$ denotes external resources entering the
organization, $z_o$ denotes results passed from the first process to the
second, and $y_o$ denotes final outcomes. The Kao--Hwang CRS relational
preset uses nonnegative multipliers $v,w,u$ and solves

$$
\begin{aligned}
\max\quad &u^\top y_o\\
\text{s.t.}\quad
&v^\top x_o=1,\\
&w^\top z_j-v^\top x_j\leq0,\\
&u^\top y_j-w^\top z_j\leq0,\qquad j=1,\ldots,n,\\
&v,w,u\geq0.
\end{aligned}
$$

The implementation does not substitute a unit-dependent numerical epsilon
for the last condition. Positive-weight or assurance-region policies, when
added, are separate valuation restrictions.

The native system and process scores are

$$
E_o=u^\top y_o,\qquad
E_o^{(1)}=w^\top z_o,\qquad
E_o^{(2)}=\frac{E_o}{E_o^{(1)}}.
$$

When the intermediate virtual value is positive,
$E_o=E_o^{(1)}E_o^{(2)}$. All three are higher-is-better and have efficient
value one under their supported self-inclusive reference domain. This product
identity belongs to the CRS relational preset. It is not asserted for
additive network DEA, network SBM, VRS extensions, parallel systems, or
general directed networks.

The same $w$ values the intermediate as an upstream result and downstream
resource. The envelopment form nevertheless uses different process
intensities:

$$
X\lambda\leq E_o x_o,\qquad
Z\lambda\geq Z\mu,\qquad
Y\mu\geq y_o.
$$

Thus shared intermediate accounting does not mean shared peers. A feasible
link target satisfies

$$
Z\mu\leq\tilde z_o\leq Z\lambda.
$$

The source-midpoint policy reports
$\tilde z_o=(Z\lambda+Z\mu)/2$, together with both bounds and the disposable
upstream surplus. It never relabels the inequality as exact flow balance.

A unique system score need not identify a unique attribution of fitted
performance between processes. The default secondary rule maximizes
$E_o^{(1)}$ while holding $E_o$ fixed. The optional bounds protocol also
minimizes it and reports the attainable interval for both process scores.
Those values are model-based attributions, not causal contributions.

`is_relationally_efficient` tests the native system score.
`is_stage_1_efficient` and `is_stage_2_efficient` test the selected process
accounts. The current projection has no Pareto slack-completion phase, so the
generic `is_efficient` remains missing.

## 9. Additive two-stage performance attribution

Chen--Cook--Li--Zhu additive network DEA asks a different organizational
question from both the Kao--Hwang relational model and ordinary slack-sum
Additive DEA. It evaluates one coordinated two-stage organization, but
combines the two process-efficiency accounts arithmetically according to the
share of virtual resources entrusted to each process.

Let $v$, $w$, and $u$ value external resources, intermediate
services, and final outcomes. Under VRS, $\xi_1$ and $\xi_2$
are free process intercepts; under CRS they are fixed at zero. The defining
programme is

$$
\begin{aligned}
\max\quad
&w^\top z_o+\xi_1+u^\top y_o+\xi_2\\
\text{s.t.}\quad
&w^\top z_j+\xi_1-v^\top x_j\leq0,\\
&u^\top y_j+\xi_2-w^\top z_j\leq0,
&&j=1,\ldots,n,\\
&v^\top x_o+w^\top z_o=1,\\
&v,w,u\geq0.
\end{aligned}
$$

Write $I_o=v^\top x_o$ and $L_o=w^\top z_o$. When the relevant
denominators are positive, the two process accounts and their aggregation
shares are

$$
E_o^{(1)}=\frac{L_o+\xi_1}{I_o},\qquad
E_o^{(2)}=\frac{u^\top y_o+\xi_2}{L_o},
$$

$$
\alpha_{1o}=\frac{I_o}{I_o+L_o},\qquad
\alpha_{2o}=\frac{L_o}{I_o+L_o}.
$$

The system identity is

$$
E_o=\alpha_{1o}E_o^{(1)}
    +\alpha_{2o}E_o^{(2)}.
$$

The $\alpha$'s are endogenous virtual-resource shares. They describe how
the fitted performance account distributes valued resource shares between
processes; they are not user-supplied importance weights. An
explicit `minimum_stage_share` changes the valuation domain and is recorded
as such. It is never implemented by a hidden numerical epsilon.

A maximum system score may support more than one process-level performance
attribution.
`decomposition="maximize_stage_1"` or `"maximize_stage_2"` holds the system
optimum fixed and applies the corresponding source-qualified secondary
programme. The default `"both_priorities"` solves both accounts, reports
whether the attribution is unique, and uses a deterministic lexicographic
tie-break when one closed-limit account leaves the other process undefined.
`decomposition="none"` reports only the identified system result rather than
presenting arbitrary stage values.

The Lim--Zhu primal--dual projection satisfies

$$
X\lambda\leq E_o x_o,\qquad
Z\lambda-Z\mu\geq(1-E_o)z_o,\qquad
Y\mu\geq y_o,
$$

with $\mathbf1^\top\lambda=\mathbf1^\top\mu=1$ under VRS. The upstream
intermediate plan $Z\lambda$ and downstream plan $Z\mu$ answer different
operational questions and remain separate in `targets` and `links`.
`disposed_quantity` records their difference, while `balance_residual`
audits the defining inequality. Unlike the Kao--Hwang midpoint selection, the
additive model does not manufacture one common intermediate target.

`system_efficiency`, both stage scores, both aggregation shares, both process
intercepts, the additive reconstruction, and its residual remain visible.
`is_additively_efficient` tests the native system criterion. Because the
source projection is not a residual-slack completion, generic
`is_efficient` remains missing.

### General open-network performance accounting

Cook--Zhu--Bi--Yang extends the same resource-share idea to organizations in
which outside resources can enter after the first process, final services can
leave before the last process, and internal products can branch or skip a
nominal stage. For process $k$, let $A_{ko}$ be its valued inputs and
$B_{ko}$ its valued outputs. The source-checked CRS account normalizes

$$
\sum_{k=1}^{K} A_{ko}=1
$$

and maximizes $\sum_{k=1}^{K} B_{ko}$, subject to
$B_{kj}\leq A_{kj}$ for every process and reference organization.
An internal product is observed once and receives one multiplier shared by
its supplying and receiving process. Thus, where $A_{ko}>0$,

$$
E_{ko}=\frac{B_{ko}}{A_{ko}},\qquad
\alpha_{ko}=A_{ko},\qquad
E_o=\sum_{k=1}^{K}\alpha_{ko}E_{ko}.
$$

These $\alpha_{ko}$ values are endogenous shares in the fitted accounting
system, not management's ex ante importance weights. Optional
`minimum_process_share` bounds are declared valuation restrictions and may
change the score. The primary system optimum can support several multiplier
accounts, so process scores and shares are labelled
`solver_selected_not_uniqueness_certified`.

The public `CookZhuBiYangAdditiveDEA` contract is deliberately CRS and
acyclic. The defining paper gives a complete CRS programme and numerical
tables, but not an equation-complete general-network VRS, projection, or peer
contract. Consequently, the package reports multiplier and observed-link
accounts but leaves generic targets, intensities, and `is_efficient`
undefined. It does not extend the closed Chen projection merely because the
two primary CRS programmes coincide on a matched two-node chain.

### Sequential network propagation

The Lewis--Sexton procedure first evaluates every process in an acyclic
organization and then passes solver-selected hypothetical quantities through
the network. Output orientation propagates improved upstream supplies
forward; input orientation propagates reduced downstream requirements
backward. The initial and propagated programmes use process-specific
intensity vectors and may support nonunique target quantities.

For an output-oriented organization, the source organizational inverse
factor is the bottleneck proportional gain across its external outputs:

$$
\Phi_k
=
\min_r
\frac{\sum_s z^*_{ksr}}{\sum_s z_{ksr}},
\qquad
E_k^O=\frac{1}{\Phi_k}.
$$

For an input-oriented organization, the organizational efficiency is the
least demanding common resource-saving account across external inputs:

$$
E_k^I
=
\max_i
\frac{\sum_s x^*_{ksi}}{\sum_s x_{ksi}}.
$$

The public `NetworkSpec` assigns each external variable type to one process,
so the sums over process owners reduce exactly to the recorded endpoint
target/observed ratios. `system_efficiency` is higher-is-better with
efficient value one; `is_sequentially_efficient` and
`is_measure_efficient` record that source-measure status. Generic
`is_efficient` remains missing because ordered radial propagation is not a
Pareto--Koopmans completion of one simultaneous joint-network technology.
Reverse quantities, mixed forward/reverse accounts, site-characteristic
adjustments, and cross-process aggregation of the same external endpoint type
are outside this public leaf.

## 10. Environmental directional technology

For undesirable outputs, positive $g^b$ always denotes contraction:

$$
(x_o-\beta g^x,\ y_o+\beta g^y,\ b_o-\beta g^b).
$$

Bad-output disposability must be explicit. The first environmental kernel
supports:

| Assumption | Code | DEA constraint |
|---|---|---|
| bad-output equality (legacy selector) | `weak` | $B\lambda=b_o-\beta g^b$ |
| strong disposability | `strong` | $B\lambda\le b_o-\beta g^b$ |

The equality prevents independent residual slack, but equality alone does not
establish equivalence to every common-factor, activity-specific, or other
empirical weak-disposal technology. The `weak` spelling is retained for one
compatibility cycle, emits `FutureWarning`, and is recorded with formulation
ID `environmental.formulation.bad_output_directional_equality`,
`bad_output_disposability=not_identified`, and compatibility alias `weak`.
It is not itself registered as a weak-disposal technology.

The named CRS common-factor construction is

$$
X\lambda\le x_o-\beta g^x,\quad
Y\lambda\ge y_o+\beta g^y,\quad
B\lambda=b_o-\beta g^b,\quad \lambda\ge0.
$$

It has no convexity equation. The named Kuosmanen VRS activity-specific
construction is

$$
X(\mu+\eta)\le x_o-\beta g^x,\quad
Y\mu\ge y_o+\beta g^y,\quad
B\mu=b_o-\beta g^b,\quad
\mathbf1^\top(\mu+\eta)=1,
$$

with $\mu,\eta\ge0$. For positive total activity, the retained activity rate
is written $r_j=\mu_j/(\mu_j+\eta_j)$; $r$ is used here to avoid collision with
the Farrell input score $\theta$. The complement $\eta$ is a weak-disposal
activity component, not an observed monetary, energy, or physical abatement cost.
Under strong
disposability, a second phase may identify additional bad-output contraction through
$B\lambda+s^b=b_o-\beta g^b$.

When null-jointness is imposed, $b=0\Rightarrow y=0$. For a nonnegative
observed-activity technology, DEAPack validates that any observation with zero
total bad output also has zero total good output. Strong free contraction of
bad output is incompatible with null-jointness in this technology and is
rejected rather than silently combining contradictory assumptions.

Every environmental result records its exact technology identity, bad-output
formulation and disposability claim, null jointness, direction, and whether
bad-output slack is permitted. Activity-specific results additionally expose
$\mu$, $\eta$, total intensity, and the recovered retention rate where the
total intensity is positive. The stable result-field label `abatement_tau`
predates this book-wide notation contract; it stores the quantity denoted by
$\eta$ here and is not a period. They use the shared
`self_in_reference`, `is_within_reference_technology`, `membership_status`, and
`efficiency_denominator_valid` fields. Conditional external membership
programmes are counted separately as `membership_solver_calls`; postsolve
certificates themselves never add an optimization task. The explicit metadata
field `certificate_extra_solver_calls` records that latter count, while
`solver_calls` includes any required membership programme.

### By-production technology

By-production distinguishes all inputs $x=(x^n,x^p)$ from the subset
$x^p$ that triggers residual generation. Code declares that subset through
`polluting_inputs`; a polluting input remains part of the ordinary input
matrix. The overall technology is the intersection:

$$
\mathcal{T}_{BP}=\mathcal{T}_1\cap\mathcal{T}_2,
$$

with two independent intensity vectors:

$$
\mathcal{T}_1:\quad X\lambda\le x,\quad Y\lambda\ge y,
$$

$$
\mathcal{T}_2:\quad X^p\mu\ge x^p,\quad B\mu\le b.
$$

$\mathcal{T}_1$ is the intended-production technology. $\mathcal{T}_2$ is
nature's residual-generation technology: increasing pollution-generating
inputs or pollution is feasible, so their inequalities have the opposite
direction from ordinary free input/output disposal. Classical
Murty--Russell--Levkoff specifications keep $\lambda$ and $\mu$ as separate
intensity systems; they must never be silently collapsed. A source-qualified
variant that couples them is a distinct technology and must state and test
that coupling explicitly. Returns to scale are recorded separately for the
two subtechnologies.

The output-oriented BP-DDF reports:

$$
\beta_o^1=\sup\{\beta:X\lambda\le x_o,\quad
Y\lambda\ge y_o+\beta g^y\},
$$

$$
\beta_o^2=\sup\{\beta:X^p\mu\ge x_o^p,\quad
B\mu\le b_o-\beta g^b\},
\qquad
\beta_o^{BP}=\min(\beta_o^1,\beta_o^2).
$$

Joint directional efficiency ($\beta_o^{BP}=0$) is distinct from
componentwise efficiency ($\beta_o^1=\beta_o^2=0$). Results retain both
component distances, identify the limiting subtechnology, and label
$1/(1+\beta_o^{BP})$ only as a display transform. BP-DDF is not merged with
the FGL index: the latter uses a different non-radial aggregation and must be
implemented and reported separately.

The Murty--Russell--Levkoff source profile uses CRS in both relations, one
nonnegative direction held fixed across the compared observations, and one
self-inclusive cross-section. The source applies BP-DDF to demonstrate its
weak indication and direction sensitivity, then proposes the distinct FGL
index. Runtime metadata must therefore separate this fixed-direction CRS
identity from VRS/NIRS/NDRS, observation-varying directions, and temporal or
non-global references, and must not describe BP-DDF as the authors'
preferred measure.

The output-oriented by-production Färe--Grosskopf--Lovell index is:

$$
E_{FGL}(x,y,b;\mathcal{T}_{BP})=
\frac{1}{2}\left(E_{FGL}^{1}+E_{FGL}^{2}\right),
$$

where

$$
E_{FGL}^{1}=
\min_{\theta,\lambda}
\left\{\frac{1}{s}\sum_r\theta_r:
X\lambda\le x_o,\quad
Y\lambda\ge y_o\oslash\theta,\quad 0<\theta\le\mathbf{1}\right\},
$$

and

$$
E_{FGL}^{2}=
\min_{\gamma,\mu}
\left\{\frac{1}{q}\sum_h\gamma_h:
X^p\mu\ge x_o^p,\quad
B\mu\le\gamma\otimes b_o,\quad
0\le\gamma\le\mathbf{1}\right\}.
$$

`productive_efficiency`, `environmental_efficiency`, and their equally
weighted overall `efficiency` are higher-is-better values in $(0,1]$ under
the positive-output, self-inclusive source profile. Efficiency equals one if
and only if neither component output vector admits a further coordinatewise
improvement. The output-oriented programme can retain input slack, so the
native flag does not certify Pareto--Koopmans efficiency. The current package
domain requires strictly positive good outputs, bad outputs, and every
declared pollution-generating input. The source technology formally permits
nonnegative inputs; the executable release uses the narrower domain because
zero pollution-generating input boundary cases are not covered by its oracle.

With $\phi_r=1/\theta_r$, the intended component minimizes the convex
separable objective $s^{-1}\sum_r1/\phi_r$ over linear technology
constraints. The default solver uses sparse LP tangent cuts. Every master LP
objective is a valid lower bound and every feasible $\phi$ gives an upper
bound; diagnostics retain both and their final gap. The effective
certification tolerance cannot be smaller than the package's declared
numerical tolerance. FGL targets, factors, and two peer systems remain
separate from BP-DDF results. CRS in both component technologies and one
self-inclusive cross-section define the source-qualified runtime profile;
other RTS or reference policies remain explicit package extensions.
`distance = 1 - efficiency` is a DEAPack display complement rather than a
source-defined distance.

### Materials-balance environmental efficiency

For material or pollutant $h$, let $a_h\in\mathbb{R}_+^m$ contain the
material content of inputs and $c_h\in\mathbb{R}_+^s$ the material retained
in desirable outputs. The physical surplus is calculated rather than treated
as an independently disposable observed output:

$$
z_{ho}=a_h^\top x_o-c_h^\top y_o\ge0.
$$

Coefficient names and units are explicit. Every input and output variable
must have a declared coefficient, including zero. With multiple materials,
positive user-supplied weights $v_h$ define the aggregate coefficients
$a=\sum_hv_ha_h$ and $c=\sum_hv_hc_h$; unlike materials are never added
without a stated weighting system.

For the Coelli--Lauwers--Van Huylenbroeck measure, desirable output is held
fixed and the lowest feasible material inflow is:

$$
N(y_o;a)=\min_{x^e,\lambda}\ a^\top x^e
\quad\text{s.t.}\quad
Y\lambda\ge y_o,\quad x^e\ge X\lambda,
$$

plus the selected returns-to-scale restriction. Because $a\ge0$, DEAPack
eliminates $x^e$ and solves the equivalent sparse LP
$\min_\lambda a^\top X\lambda$. Input-oriented technical efficiency is estimated
on the same reference technology:

$$
TE_o=\min_{\theta,\lambda}\{\theta:
X\lambda\le\theta x_o,\ Y\lambda\ge y_o\}.
$$

The reported higher-is-better measures are:

$$
EE_o=\frac{a^\top x_o^e}{a^\top x_o},\qquad
EAE_o=\frac{EE_o}{TE_o},\qquad
EE_o=TE_o\times EAE_o.
$$

`EE` uses material **inflow**, not the ratio of target to observed surplus.
The retained output content $c^\top y_o$ is fixed, so minimizing inflow also
minimizes surplus; both inflow and surplus remain visible in targets and the
summary. Observed bad-output columns are rejected to prevent this physical
coefficient model from being silently mixed with a disposable bad-output
technology. Explicit end-of-pipe control lies outside the classic measure
unless abatement is represented as a declared desirable output with its own
material coefficient.

## 11. Slacks, peers, and targets

- $s^-\in\mathbb{R}_+^m$: input excesses;
- $s^+\in\mathbb{R}_+^s$: desirable-output shortfalls;
- $s^b\in\mathbb{R}_+^q$: undesirable-output excesses;
- $\hat{x}_o,\hat{y}_o,\hat{b}_o$: target vectors;
- $\mathcal P_o=\{j:\lambda_j^*>0\}$: active peer/reference set.

Numerical peer membership uses a documented tolerance rather than exact
floating-point comparison with zero.

## 12. Native values and standardized reporting

Every result distinguishes the literature-native quantity from a convenient
standardized display value:

| Field | Direction | Meaning |
|---|---|---|
| `score` | model-specific | native primary quantity ($\theta$, $\phi$, $\rho$, etc.) |
| `efficiency` | higher is better | bounded $[0,1]$ value when a valid mapping exists |
| `distance` | higher means farther | native distance/inefficiency when applicable |
| `is_efficient` | nullable boolean | Pareto--Koopmans efficiency only when a compatible completion task certifies it |

No transformation is applied without storing its name in result metadata.
Tables and figures must identify whether they display `score`, `efficiency`,
or `distance`. A quantity-space frontier figure instead names the displayed
input and output variables, draws only result-certified target accounts, and
states its orientation, RTS, and reference policy. It must not reconstruct a
two-dimensional "frontier" from a multidimensional score.

The non-public radial leave-one-out prototype currently uses the provisional
display mapping

$$
E_o^{AP,I}=\theta_o,\qquad E_o^{AP,O}=\frac{1}{\phi_o}.
$$

These fields describe internal reconstruction behavior only. The complete
Andersen--Petersen (1993) text was not obtained for this release, so the
orientation, RTS, score normalization, applicability, failure, target, and
peer contracts have not been frozen as Andersen--Petersen source semantics.
`evaluation.super.ap_radial` is therefore `deferred_to_next_version`, absent
from the public API and catalog, and must not be cited as a current public AP
leaf. Its provisional values above one are not percentages of
Pareto--Koopmans efficiency, and its generic `is_efficient` field remains
missing because the prototype performs no strong slack-completion task.

Every criterion that has its own optimum keeps a criterion-specific status,
such as `is_radially_efficient`, `is_directionally_efficient`,
`is_cost_efficient`, `is_revenue_efficient`, `is_allocatively_efficient`, or
`is_scale_efficient`. These fields answer different economic questions and
must not be copied into `is_efficient`. If the fitted method does not test all
admissible input reductions, desirable-output increases, and relevant
undesirable-output reductions, the generic status remains missing. A missing
status means “not certified,” not inefficient.

## 13. Productivity

For a generic productivity task, $z^\sigma=(x^\sigma,y^\sigma)$ denotes the
plan from evaluated period $\sigma$, while $d^\tau(z^\sigma)$ denotes its
efficiency-form distance against reference technology $\mathcal T^\tau$:
output orientation uses $1/\phi$ and input orientation uses $\theta$.
Within-period values are bounded by one when the evaluated observation belongs
to the reference technology; cross-period values can exceed one. Source papers
that use $r$ and $s$ as period labels are crosswalked here to $t,t+1$ or to
$\sigma,\tau$ when the evaluated-plan and reference-technology roles differ;
$r$ remains DEAPack's desirable-output index and $s$ its dimension.

The project unifies productivity methods by their **economic account**, not
by making their scores interchangeable:

| Retained account | Organizational question | Task value | Reference information | Change arithmetic |
|---|---|---|---|---|
| Radial Malmquist | Did proportional productive performance improve, and how did benchmark-relative operating performance and represented opportunities contribute? | Farrell efficiency-form distances | Two contemporaneous technologies, or one explicitly declared common-reference policy | Multiplicative; no change at 1 |
| Ordinary Luenberger | How did the attainable amount of one declared improvement programme change? | Directional distances in the common programme units | Two contemporaneous technologies | Additive; no change at 0 |
| Environmental Malmquist--Luenberger | Did useful output relative to resource use and undesirable residuals improve under the declared environmental production account? | One plus a source-qualified environmental directional distance | CFG adjacent technologies; Oh's full-horizon technology only as the declared sensitivity policy | Multiplicative; no change at 1 |
| Hicks--Moorsteen | Did aggregate output quantity grow faster than aggregate input quantity? | Paired Shephard output and input distances | Two bilateral contemporaneous technologies | Multiplicative output-quantity over input-quantity ratio; no change at 1 |

They may share compiled references, task caches, solver certificates, panel
matching, and result tables. They must retain different quantity accounts,
score units, neutral values, and decomposition identities. A reference policy
such as global or biennial changes the information admitted to an operator;
it does not by itself create a new economic theory of productivity.

Every public productivity result therefore records `change_calculus`,
`no_change_value`, `improvement_rule`, `reference_information_policy`,
`distance_task_convention`, and `transition_release_policy`, in addition to
its method identity, period pairing, technology, direction or orientation,
RTS, panel policy, and exact decomposition or quantity identity. Each claimed
transition account is released only when every task required by that account
and its complete reconstruction are certified; a method that permits partial
component release declares that policy explicitly. Peer accounts have their
own release gate and may be withheld without erasing a valid productivity
score.

For $z^t=(x^t,y^t)$ and $z^{t+1}=(x^{t+1},y^{t+1})$:

$$
M^{t,t+1}=
\left[
\frac{d^t(z^{t+1})}{d^t(z^t)}
\frac{d^{t+1}(z^{t+1})}{d^{t+1}(z^t)}
\right]^{1/2}.
$$

The Färe--Grosskopf--Norris--Zhang decomposition is:

$$
EC^{t,t+1}=\frac{d^{t+1}(z^{t+1})}{d^t(z^t)},
$$

$$
TC^{t,t+1}=
\left[
\frac{d^t(z^{t+1})}{d^{t+1}(z^{t+1})}
\frac{d^t(z^t)}{d^{t+1}(z^t)}
\right]^{1/2},
\qquad M=EC\times TC.
$$

`productivity_change`, `efficiency_change`, and `technical_change` name these
three quantities. `score` contains productivity change, while `efficiency`
and `is_efficient` remain missing because a productivity transition is not a
bounded efficiency level.

For the Luenberger indicator, let $D^\tau(z^\sigma;g)$ be the directional
distance for a period-$\sigma$ plan under period-$\tau$ technology and one
declared directional scale $g$. Its adjacent-period productivity change is:

$$
L^{t,t+1}=\frac{1}{2}\left[
D^t(z^t;g)-D^t(z^{t+1};g)
+D^{t+1}(z^t;g)-D^{t+1}(z^{t+1};g)
\right].
$$

The additive decomposition is:

$$
EC_L^{t,t+1}=D^t(z^t;g)-D^{t+1}(z^{t+1};g),
$$

$$
TC_L^{t,t+1}=\frac{1}{2}\left[
D^{t+1}(z^t;g)-D^t(z^t;g)
+D^{t+1}(z^{t+1};g)-D^t(z^{t+1};g)
\right],
\qquad L=EC_L+TC_L.
$$

The Pastor--Lovell Global Malmquist index uses one pooled technology
$\mathcal{T}^G$ containing every sample period. With the same Farrell
efficiency-form distance convention:

$$
GM^{t,t+1}=\frac{d^G(z^{t+1})}{d^G(z^t)}.
$$

Define the best-practice gap for an observation in period $\tau$ as
$BPG^\tau(z^\tau)=d^G(z^\tau)/d^\tau(z^\tau)$. Because the global technology
contains each
contemporaneous technology, $BPG\in(0,1]$ up to numerical tolerance. Then:

$$
EC_G^{t,t+1}=\frac{d^{t+1}(z^{t+1})}{d^t(z^t)},\qquad
BPC_G^{t,t+1}=\frac{BPG^{t+1}(z^{t+1})}{BPG^t(z^t)},\qquad
GM=EC_G\times BPC_G.
$$

`best_practice_change` is the primary name for $BPC_G$;
`technical_change` mirrors it only to support the common decomposition table.
The index is circular within one fixed global sample and uses no cross-period
radial solves. Adding periods changes $\mathcal{T}^G$, so every global distance
must be recomputed and historical values may change.

For adjacent periods $t,t+1$, the Pastor--Asmild--Lovell biennial technology
$\mathcal{T}^{B(t,t+1)}$ pools observations from exactly those two periods.
The Biennial Malmquist index and its gap decomposition are:

$$
BM^{t,t+1}=\frac{d^{B(t,t+1)}(z^{t+1})}
{d^{B(t,t+1)}(z^t)},
$$

$$
BG^\tau=\frac{d^{B(t,t+1)}(z^\tau)}{d^\tau(z^\tau)},
\quad \tau\in\{t,t+1\},\qquad
BPC_B^{t,t+1}=\frac{BG^{t+1}}{BG^t},\qquad
BM=EC_B\times BPC_B.
$$

The pair-specific pool contains both evaluated observations, so no
cross-period radial solve is needed. Adding a later period does not alter an
existing pair's technology, but consecutive biennial indexes are not generally
circular because their pooled references differ. `biennial_gap_change` names
$BPC_B$ explicitly; `best_practice_change` and `technical_change` retain the
shared result-schema mappings.

For the Bjurek Hicks--Moorsteen leaf, the total-factor-productivity account
uses both output and input quantity indexes:

$$
Q^{t,t+1}
=
\left[
\frac{D_O^t(x^t,y^{t+1})}{D_O^t(x^t,y^t)}
\frac{D_O^{t+1}(x^{t+1},y^{t+1})}
{D_O^{t+1}(x^{t+1},y^t)}
\right]^{1/2},
$$

$$
X^{t,t+1}
=
\left[
\frac{D_I^t(x^{t+1},y^t)}{D_I^t(x^t,y^t)}
\frac{D_I^{t+1}(x^{t+1},y^{t+1})}
{D_I^{t+1}(x^t,y^{t+1})}
\right]^{1/2},
\qquad
HM^{t,t+1}=\frac{Q^{t,t+1}}{X^{t,t+1}}.
$$

`productivity_change`, `output_quantity_index`, and
`input_quantity_index` store $HM$, $Q$, and $X$. All eight underlying
Shephard-distance tasks retain their technology, input-period, and
output-period roles. The public leaf reports no ordinary Malmquist
efficiency-change/technical-change decomposition, no scale/mix
decomposition, and no transitivity claim for a chained bilateral series.

For environmental observations $z^\sigma=(x^\sigma,y^\sigma,b^\sigma)$,
write $D^\tau(z^\sigma)$ for the directional distance of a period-$\sigma$
plan against period-$\tau$ technology. The Chung--Färe--Grosskopf
Malmquist--Luenberger index uses these distances and the classic observed
direction $(g^x,g^y,g^b)=(0,y,b)$ under DEAPack's positive-magnitude
convention. Its source-qualified production account is the CRS common-factor
weak-disposal technology with null jointness:

$$
ML^{t,t+1}=\left[
\frac{1+D^t(z^t)}{1+D^t(z^{t+1})}
\frac{1+D^{t+1}(z^t)}{1+D^{t+1}(z^{t+1})}
\right]^{1/2}=EC_{ML}\times TC_{ML}.
$$

Cross-period environmental directional distances are unrestricted and may be
negative; every $1+D$ factor must remain strictly positive. The named
`productivity.malmquist_luenberger.chung_fare_grosskopf_1997` leaf freezes
the technology, direction, and scale assumption. A different configuration
defines another temporal method and must not inherit the historical name. The
generic candidate is `deferred_to_next_version` until a defining source and
independent validation cover its complete parameter domain.

Oh's Global Malmquist--Luenberger index uses one environmental technology
$\mathcal{T}^G$ containing all sample periods and retains the same classic
environmental technology and direction:

$$
GML^{t,t+1}=\frac{1+D^G(z^t)}{1+D^G(z^{t+1})}
=EC_G\times BPC_G.
$$

In Oh's source orientation,
$BPG^\tau=(1+D^\tau(z^\tau))/(1+D^G(z^\tau))\in(0,1]$ and
$BPC_G=BPG^{t+1}/BPG^t$. The package operationalizes the global reference as
one pooled CRS conical envelope; it does not claim that this envelope is
identical to a literal set union. Every own-period and global task is
self-inclusive, so its distance is nonnegative up to numerical tolerance.
GML is circular within one fixed global sample and requires no off-diagonal
cross-period directional solve. Adding periods or observations can change
the global technology and therefore requires every global distance to be
recomputed. Configured alternatives are likewise deferred rather than being
reported under Oh's historical name.

Positive Luenberger values indicate improvement. Cross-period directional
distances are allowed to be negative: an observation beyond an earlier
frontier must not be clipped to zero. Because additive distances are cardinal
in $g$, every result records whether directions are common (`mean`, `ones`, or
a global vector) or observation-specific. The stable default is one
full-sample column-mean direction, which preserves results under changes of
variable units when the direction is rescaled with the data.

Multiplicative productivity indexes use:

- $P_o^{t,t+1}>1$: productivity improvement;
- $P_o^{t,t+1}=1$: no change;
- $P_o^{t,t+1}<1$: productivity decline.

Additive productivity indicators use positive values for improvement and zero
for no change. Components use explicit names such as `efficiency_change`,
`technical_change`, `scale_efficiency_change`, and `mix_efficiency_change`.
The ambiguous abbreviations `prod_ch`, `eff_ch`, and `te_ch` are accepted only
in the legacy compatibility layer.

Cross-period matching is always by stable `dmu_id` and `period`, never by row
position or an assumption that periods are consecutive integers. Adjacent
means adjacent in the declared `period_order`. The first period has no
predecessor and therefore contributes no transition row. Unbalanced panels
use an explicit `drop` or `raise` policy; no cross-period failure is replaced
silently by a one-sided index.

## 14. Prices and economic quantities

- $w_o\in\mathbb{R}_{++}^m$: strictly positive input prices faced by observation $o$;
- $p_o\in\mathbb{R}_{++}^s$: strictly positive desirable-output prices faced by observation $o$;
- $C_o=w_o^\top x_o$: observed cost;
- $R_o=p_o^\top y_o$: observed revenue;
- $\Pi_o=R_o-C_o$: observed profit.

The first public cost implementation requires complete, finite, strictly
positive input prices. It defines

$$
C_o^*=\min_{\lambda\in\Lambda_{\mathrm{RTS}}}
w_o^\top X\lambda
\quad\text{s.t.}\quad Y\lambda\ge y_o,
\qquad
CE_o=\frac{C_o^*}{C_o}.
$$

Here `observed_cost` is $C_o$, `minimum_cost` is $C_o^*$,
`cost_gap` is $C_o-C_o^*$, and `cost_efficiency` is $CE_o$.
`score` and `efficiency` also report $CE_o$; higher is better and `distance`
is missing.

With the matched input-oriented Farrell score $TE_o^I$, cost allocative
efficiency is

$$
AE_o^C=\frac{CE_o}{TE_o^I},
\qquad
CE_o=TE_o^I AE_o^C.
$$

`AllocativeDecomposition` uses `allocative_efficiency` as its generic
`score` and `efficiency`, retains both component columns, and records
`reconstruction_residual`. Both programs use identical data, RTS, reference,
and input orientation. Price changes never enter the radial technical
program.

Prices are external valuation data aligned by exact quantity names and
observation keys. They are not production quantities and are not the
endogenous multiplier or constraint-marginal values returned by a DEA
program. Every price record states scope, source, currency, numeraire, and,
for panel monetary comparison, a base period. Numerical price payloads enter
result provenance only through stable signatures. Each fitted economic model
records only the price side it uses.

The public revenue implementation defines

$$
R_o^*=\max_{\lambda\in\Lambda_{\mathrm{RTS}}}
p_o^\top Y\lambda
\quad\text{s.t.}\quad X\lambda\le x_o,
\qquad
RE_o=\frac{R_o}{R_o^*}.
$$

Here `observed_revenue` is $R_o$, `maximum_revenue` is $R_o^*$,
`revenue_gap` is $R_o^*-R_o$, and `revenue_expansion_ratio` is
$R_o^*/R_o$. `revenue_efficiency`, `score`, and `efficiency` report $RE_o$.
Under an external reference, values above one are retained rather than
clipped. If $R_o^*$ is zero, the optimization result is retained but the
efficiency ratio is undefined.

Let $\phi_o$ be the matched native output-radial expansion factor and
$TE_o^O=1/\phi_o$. Revenue allocative efficiency is

$$
AE_o^R=\frac{RE_o}{TE_o^O}
      =\frac{\phi_oR_o}{R_o^*},
\qquad
RE_o=TE_o^O AE_o^R.
$$

`RevenueAllocativeDecomposition` retains both $\phi_o$ and $TE_o^O$, reports
`allocative_efficiency` as its generic score, and fails closed when either
denominator or component solve is invalid. The radial output plan
$\phi_o y_o$ and the revenue-maximizing activity $Y\lambda^*$ are distinct
managerial counterfactuals and are never silently interchanged.

Maximum-profit analysis allows both inputs and outputs to change:

$$
\Pi_o^*=\max_{\lambda\in\Lambda_{\mathrm{RTS}}}
\left(p_o^\top Y\lambda-w_o^\top X\lambda\right),
\qquad
G_o^\Pi=\Pi_o^*-\Pi_o.
$$

Here `maximum_profit` is $\Pi_o^*$ and `profit_gap` is $G_o^\Pi$.
`ProfitEfficiency` reports the gap as its native `score`, with
`score_direction="lower_is_better"`, while generic `efficiency` and
`distance` are missing. Observed or maximum profit may be negative; the
package never fabricates an observed/maximum profit ratio. The initial
`economic.profit.maximum` leaf is VRS with $\mathbf 1^\top\lambda=1$: its
reference simplex is finite but excludes shutdown. An origin or
$\mathbf 1^\top\lambda\le1$ shutdown technology is a separate preset. An
unconstrained CRS positive-profit activity creates an unbounded ray.

Under self-inclusive appraisal with complete strictly positive prices,
`profit_gap == 0` certifies Pareto--Koopmans efficiency: any strict dominance
would raise profit. A positive gap does not prove technical inefficiency,
because a technically efficient organization may choose the wrong resource
or output mix; generic `is_efficient` is therefore missing rather than
`False`. External-reference gaps are retained as monetary comparisons but
the public profit score and efficiency statuses fail closed until membership
in the reference technology is certified.

For the CCF direction convention
$(x_o-\beta g_o^x,y_o+\beta g_o^y)$, define

$$
\nu_o=w_o^\top g_o^x+p_o^\top g_o^y>0,
\qquad
NI_o=\frac{\Pi_o^*-\Pi_o}{\nu_o}
    =D_{\mathcal T}(x_o,y_o;g_o^x,g_o^y)+AI_o^N.
$$

`NerlovianProfitInefficiency` reports `direction_value` $\nu_o$,
`nerlovian_inefficiency` $NI_o$, `technical_inefficiency` $D_{\mathcal T}$, and
`allocative_inefficiency` $AI_o^N$, with an explicit
`reconstruction_residual`. Its generic `score` and `distance` are $NI_o$,
zero best and lower better; generic `efficiency` remains missing. The profit
maximum, the direct directional operating programme, and any
slack-completed directional activity are different target kinds.

Directions are nonnegative magnitudes: input components describe resource
contraction and output components describe desirable-service expansion.
Multiplying every direction component by $a>0$ divides $NI_o$, $D_{\mathcal T}$, and
$AI_o^N$ by $a$ while leaving the monetary profit gap unchanged. Multiplying
all relevant prices by a common positive constant multiplies the raw gap and
$\nu_o$ by that constant but leaves all three normalized components unchanged.
Cross-unit or cross-period comparisons are conditional on common economic
units and a comparable direction policy.

Return-to-dollar profitability uses

$$
\rho_o^{RTD}=\frac{R_o}{C_o},
\qquad
\Gamma_o^*=
\max_{(x,y)\in T,\;w_o^\top x>0}\frac{p_o^\top y}{w_o^\top x},
\qquad
PE_o=\frac{\rho_o^{RTD}}{\Gamma_o^*}.
$$

Prose may abbreviate $\rho_o^{RTD}$ to $\rho_o$ only within an explicitly
profitability-labeled section; the superscript distinguishes it from RAM,
SBM, and other established $\rho$ scores in the global notation. Result
fields `return_to_dollar` and `observed_profitability` are exact aliases for
$\rho_o^{RTD}$. `maximum_profitability` is $\Gamma_o^*$.
`profitability_efficiency`, `score`, and `efficiency` are $PE_o$, higher is
better. They are never labeled profit efficiency or a profit ratio.

For the supported positive-cost ordinary DEA technology,
$\Gamma_o^*$ is the maximum reference-activity ratio and is numerically
identical under CRS and VRS. The target-scale convention remains explicit:
VRS uses the selected reference activity, whereas CRS scales that activity
to the evaluated unit's observed input expenditure. An equal-ratio
accounting point, a profitability-maximizing activity, and a Chavas--Cox GDF
path point are distinct target kinds.

External-reference $PE_o$ values are retained without clipping and may exceed
one; criterion-specific and generic efficiency flags are then missing. Under
self-inclusive appraisal, $PE_o=1$ with complete strictly positive prices
certifies Pareto--Koopmans efficiency, while $PE_o<1$ does not by itself prove
technical inefficiency.

Environmental shadow prices and marginal abatement costs state their
numeraire, units, sign convention, and normalization.

## 15. Language and naming

English API identifiers are canonical. Chinese and English prose terms are
maintained in a shared terminology table during the documentation phase.
Public enum-like values are lowercase ASCII strings (`vrs`, `input`,
`global`); display labels are localized separately.
