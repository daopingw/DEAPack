# Tone--Tsutsui (2010) EBM-I-C source protocol

## Readiness record

| Field | State |
|---|---|
| Candidate identifier | `static.ebm.input.tone_tsutsui_2010.crs` |
| Source status | `complete_primary_manuscript_obtained` |
| Equation-freeze status | `input_crs_frozen_with_source_unresolveds` |
| Independent reproduction | `published_chain_reproduced_with_one_source_table_conflict` |
| Full-estimator implementation status | `deferred_no_production_code` |
| Full-estimator release disposition | `deferred_to_next_version` |
| Conditionally admitted evaluator | `static.ebm.input.tone_tsutsui_2010.crs.declared` |
| Declared-evaluator contract | `specs/M13_DECLARED_EBM_IC.md` |
| Last equation audit | 2026-08-04 |

This protocol freezes only the input-oriented, constant-returns-to-scale
epsilon-based measure, denoted EBM-I-C in the source. Three source-level
choices remain unresolved for the paper's automatic affinity/PCA calibration:
the calibration-projection selector, a general selector for a repeated
dominant eigenvalue, and one inconsistent printed projection in the hospital
example. Consequently the full source identity
`static.ebm.input.tone_tsutsui_2010.crs`, the wider `static.ebm` family, and
every automatic-calibration API remain deferred.

M13-C separates those unresolved calibration choices from equations (6)--(8),
which the source explicitly evaluates only after epsilon and input weights
have been supplied. The conditional evaluator
`static.ebm.input.tone_tsutsui_2010.crs.declared` is admitted under
`specs/M13_DECLARED_EBM_IC.md`. It requires immutable user-declared parameters
and provenance and makes no claim that equations (15)--(26) were run or
validated. This narrow exception replaces the earlier blanket prohibition;
it does not reopen any automatic or wider EBM identity.

## 1. Primary source and claim boundary

Kaoru Tone and Miki Tsutsui (2010), “An epsilon-based measure of efficiency
in DEA: A third pole of technical efficiency,” *European Journal of
Operational Research*, 207(3), 1554--1563.

- [Published article DOI](https://doi.org/10.1016/j.ejor.2010.07.014)
- [GRIPS repository record for DP09-21](https://grips.repo.nii.ac.jp/records/1021)
- [Complete DP09-21 manuscript](https://grips.repo.nii.ac.jp/record/1021/files/DP09-21.pdf)

Page references below are PDF/printed manuscript pages in DP09-21. The
equation numbers are those printed by the authors.

The source later discusses output-oriented, non-oriented, and VRS
extensions. They are outside this freeze. Undesirable-output, network,
dynamic, super-efficiency, and later EBM variants are also separate methods.
Nothing in this protocol may be generalized to them by changing an option.
GRIPS DP09-13 is an earlier and substantively different epsilon formulation;
it is not an alternative source for this affinity--PCA EBM.

## 2. Data and notation

Section 2 (p. 2) uses $n$ decision-making units (DMUs), $m$ inputs, and
$s$ outputs. Let

$$
X=(x_{ij})\in\mathbb R_{++}^{m\times n},\qquad
Y=(y_{rj})\in\mathbb R_{++}^{s\times n},
$$

and let $x_o$ and $y_o$ denote the observed input and output vectors for
the evaluated DMU. Strict positivity is part of the exact source domain: the
score and calibration both divide by observations, while the affinity index
uses logarithms of ratios. Zero, negative, missing, or non-finite data are not
covered by this leaf.

For EBM-I-C:

- λ is the nonnegative CRS intensity vector;
- θ is a free scalar, not a nonnegative or at-most-one variable;
- $s^-\ge0$ is the vector of input excesses;
- $w^-\ge0$, $\mathbf 1^Tw^-=1$, is the calibrated input-weight vector;
- $\varepsilon_x\in[0,1]$ is the calibrated diversity parameter; and
- $\gamma_o^*$ is the higher-is-better input-efficiency score.

There is no convexity equation in EBM-I-C. Adding
$\mathbf 1^T\lambda=1$ would change CRS to VRS and is out of scope.

## 3. Frozen EBM-I-C programme

### 3.1 Primal equations (6)--(8), pp. 4--5

Once $\varepsilon_x$ and $w^-$ have been calibrated, the source model is
the linear programme

$$
\begin{aligned}
\gamma_o^* = \min_{\theta,\lambda,s^-}\quad
 &\theta-\varepsilon_x\sum_{i=1}^m
    w_i^-\frac{s_i^-}{x_{io}} \tag{6}\\
\text{s.t.}\quad
 &\theta x_o-X\lambda-s^-=0, \tag{7}\\
 &Y\lambda\ge y_o,\quad \lambda\ge0,\quad s^-\ge0. \tag{8}
\end{aligned}
$$

The absence of a bound on θ is deliberate. Page 6 explicitly states that
its optimum can exceed one. A solver adapter must therefore give θ a free
bound; a library default of $\theta\ge0$ would be an unreviewed change even
when it happens not to alter a particular example.

### 3.2 Dual equations (9)--(12), p. 5

The source gives the paired multiplier programme

$$
\begin{aligned}
\gamma_o^*=\max_{v,u}\quad &u^Ty_o \tag{9}\\
\text{s.t.}\quad &v^Tx_o=1, \tag{10}\\
&-v^TX+u^TY\le0, \tag{11}\\
&v_i\ge\varepsilon_x w_i^-/x_{io}\quad(i=1,\ldots,m), \tag{12}\\
&u\ge0.
\end{aligned}
$$

The notation above makes row/column transposes explicit while preserving the
source balances. The admitted declared evaluator reconstructs these source
multipliers from solver marginals and releases them only after feasibility and
strong-duality checks. The independent production-free reproduction remains
primal-only so that it does not reuse the production certificate path.

### 3.3 Equivalent target-variable form (14), p. 6

Introducing $x=\theta x_o-s^-=X\lambda$ yields

$$
\begin{aligned}
\gamma_o^*=\min_{\theta,\lambda,x,s^-}\quad
 &(1-\varepsilon_x)\theta
 +\varepsilon_x\sum_{i=1}^m w_i^-\frac{x_i}{x_{io}}\\
\text{s.t.}\quad
 &x-X\lambda=0,\\
 &x-\theta x_o+s^-=0, \tag{14}\\
 &Y\lambda\ge y_o,\quad\lambda\ge0,\quad s^-\ge0.
\end{aligned}
$$

This is an algebraically equivalent LP, not an average of a separately fitted
CCR score and a separately fitted SBM score. The radial and input-mix terms
are optimized jointly under one peer plan.

### 3.4 Score and endpoint statements

The source establishes the following for EBM-I-C (Propositions 1--6, p. 5):

- $0\le\gamma_o^*\le1$, with unit invariance;
- $\varepsilon_x=0$ reduces the model to input-oriented CCR;
- setting $\theta=1$ and $\varepsilon_x=1$ gives an input-oriented
  slack-based programme;
- a finite optimum is guaranteed for $\varepsilon_x\in[0,1]$;
- $\varepsilon_x>1$ makes the dual infeasible and primal unbounded; and
- the optimum is non-increasing in $\varepsilon_x$.

Definition 1 calls a DMU EBM input-efficient when
$\gamma_o^*=1$. Endpoint tests may claim only these source-qualified
statements. In particular, the SBM statement includes the source condition
on theta; it is not permission to alias all $\varepsilon_x=1$ software calls
to an independently implemented SBM estimator. Algebraically, the standard
equal-weight SBM in equation (3) also requires $w_i^-=1/m$. With theta free,
epsilon one eliminates theta from the objective and does not impose the SBM
componentwise condition $X\lambda\le x_o$. The declared evaluator therefore
never aliases epsilon one to SBM and applies the explicitly package-defined
minimum-feasible-theta completion frozen in `specs/M13_DECLARED_EBM_IC.md`.

The score bound $\gamma_o^*\le1$ uses the paper's full self-inclusive sample:
the evaluated DMU itself supplies the feasible unit-score plan. External or
eligibility-restricted appraisal can exceed one and is outside the admitted
declared evaluator.

## 4. Projection, slack, target, and peer semantics

For any optimal solution $(\theta^*,\lambda^*,s^{-*})$, Definition 2 and
equation (13) on p. 6 define

$$
x_o^*=X\lambda^*=\theta^*x_o-s^{-*},\qquad
y_o^*=Y\lambda^*. \tag{13}
$$

Proposition 7 states that this projected DMU is EBM input-efficient. The
following reporting semantics are therefore frozen:

| Account | Source-equation meaning |
|---|---|
| score | $\gamma_o^*=\theta^*-\varepsilon_x\sum_iw_i^-s_i^{-*}/x_{io}$ |
| radial factor | the free optimum $\theta^*$ |
| input excess | $s_i^{-*}\ge0$ from (7) |
| input target | $x_{io}^*=\theta^*x_{io}-s_i^{-*}=(X\lambda^*)_i$ |
| output target | $y_{ro}^*=(Y\lambda^*)_r\ge y_{ro}$ |
| output surplus | the derived quantity $(Y\lambda^*-y_o)_r$, not an objective term in (6)--(8) |
| peers | indices with a positive component of one returned optimal λ |

Peers, slacks, and targets are optimal-solution attributions. The source does
not supply a secondary objective that makes them unique, so the admitted
evaluator labels them solver-selected and makes no uniqueness claim.

Most importantly, input orientation here does **not** mean componentwise
input contraction. Because θ is free, $x_o^*\nleq x_o$ is possible. The
hospital-D discussion on p. 21 deliberately recommends substituting across
inputs: doctors fall while nurses rise. This is a source-defined feasible
input-mix recommendation, not a geometric artefact or a sign error.

## 5. Frozen affinity--PCA calibration

### 5.1 Calibration population: equations (19)--(22), pp. 9--10

The source's main procedure projects every observation to the VRS-efficient
frontier using either the observation-normalized additive model (ADD) or the
non-oriented SBM. For ADD, DMU $o$ solves

$$
\begin{aligned}
\max_{\lambda,s^-,s^+}\quad
 &\sum_{i=1}^m\frac{s_i^-}{x_{io}}
  +\sum_{r=1}^s\frac{s_r^+}{y_{ro}}\\
\text{s.t.}\quad
 &x_{io}=\sum_{j=1}^n x_{ij}\lambda_j+s_i^-,\\
 &y_{ro}=\sum_{j=1}^n y_{rj}\lambda_j-s_r^+, \tag{19}\\
 &\sum_{j=1}^n\lambda_j=1,
 \quad\lambda,s^-,s^+\ge0.
\end{aligned}
$$

The alternative in equation (20) is the ordinary non-oriented VRS SBM:

$$
\min
\frac{1-\frac1m\sum_i s_i^-/x_{io}}
     {1+\frac1s\sum_r s_r^+/y_{ro}}
\tag{20}
$$

under the same input, output, convexity, and nonnegativity balances. Given an
optimal slack vector from the selected calibration model, equation (21)
defines

$$
\bar x_{io}=x_{io}-s_i^{-*},\qquad
\bar y_{ro}=y_{ro}+s_r^{+*}. \tag{21}
$$

Equation (22) collects the $n$ projected observations in
$(\bar X,\bar Y)$. The source notes that ADD and SBM can yield different
projections, even though both lie on the VRS-efficient frontier. Footnote 1
on p. 9 also permits using the original $(X,Y)$ rather than projected data;
the published examples use projected data, and Examples 1 and 3 name ADD.
The source also notes that the projected population includes CRS-efficient
DMUs along with the VRS-efficient DMUs.

This is not one uniquely specified preprocessing algorithm. The choice among
ADD, SBM, and raw observations is an analyst/package policy. In addition,
ADD or SBM can have multiple optimal projections and the source gives no
lexicographic or minimum-norm selector. A future implementation must expose a
named calibration-population policy and a deterministic projection tie-break
as package policy. It must never silently calibrate from whichever optimum a
solver happens to return.

### 5.2 Diversity and affinity: equations (15)--(18), p. 8

For two strictly positive length-$n$ calibration vectors $a,b$, define

$$
c_j=\log(b_j/a_j),\qquad
\bar c=\frac1n\sum_jc_j,\qquad
c_{\max}=\max_jc_j,\quad c_{\min}=\min_jc_j. \tag{15}
$$

The diversity index is

$$
D(a,b)=
\frac{\sum_j|c_j-\bar c|}{n(c_{\max}-c_{\min})},
\tag{16}
$$

with $D(a,b)=0$ when $c_{\max}=c_{\min}$. The source gives

$$
0\le D(a,b)=D(b,a)\le\tfrac12, \tag{17}
$$

and $D=0$ exactly for proportional vectors. Affinity is

$$
S(a,b)=1-2D(a,b). \tag{18}
$$

It is symmetric, unit-invariant, and lies in $[0,1]$.

### 5.3 Input affinity matrix, epsilon, and weights: equations (23)--(26), p. 11

Let $\bar x_i=(\bar x_{i1},\ldots,\bar x_{in})$ be the observations of
projected input $i$. The input affinity matrix is

$$
\mathcal S_x=(s_{ij})_{m\times m},\qquad
s_{ij}=S(\bar x_i,\bar x_j). \tag{23}
$$

It is symmetric and entrywise nonnegative, has unit diagonal, and satisfies
$0\le s_{ij}\le1$ (24). Let $\rho_x$ be its largest eigenvalue and let
$w_x\ge0$ be an associated nonnegative eigenvector. The source then defines

$$
\varepsilon_x=
\begin{cases}
(m-\rho_x)/(m-1),&m>1,\\
0,&m=1,
\end{cases} \tag{25}
$$

and

$$
w^-=\frac{w_x}{\sum_{i=1}^m w_{xi}}. \tag{26}
$$

For a simple dominant eigenvalue, this normalization removes the scale and
sign ambiguity and is sufficient for the source reproduction. It is **not**
sufficient when the dominant eigenvalue is repeated. Example 2 has
$\mathcal S_x=I_2$, so every nonzero nonnegative vector is a dominant
eigenvector. The source prints $w^-=(0.5,0.5)$, but provides no general tie
rule. A future exact-domain implementation must either require a simple
dominant root or document a new tie policy as package policy. It must not use
an arbitrary vector returned by `eigh` as though the source selected it.

## 6. Published numerical chain and automatic-calibration unresolveds

The independent, production-free reproduction is documented in
`specs/oracles/tone_tsutsui_2010_ebm_ic.md` and executed by
`tests/test_tone_tsutsui_2010_ebm_ic_source.py`.

It verifies:

- Example 1: ADD maps every observation to $(1,1,1)$, the affinity matrix is
  all ones, $\rho_x=2$, $w^-=(0.5,0.5)$,
  $\varepsilon_x=0$, and EBM scores equal the printed CCR scores;
- Example 2: the projected sample produces identity affinity,
  $\varepsilon_x=1$, and the **explicitly printed** equal weights reproduce
  the printed SBM/EBM scores, while the executable oracle rejects the
  repeated root as a general calibration rule; and
- Example 3: the printed Table 10 inputs give
  $D=0.2646990116$, $S=0.4706019769$,
  $\rho_x=1.4706019769$,
  $\varepsilon_x=0.5293980231$, and $w^-=(0.5,0.5)$. Equations (6)--(8)
  then reproduce the Table 13 score, θ, and input-slack columns to their
  printed precision.

The following three calibration items remain unresolved and are release
blockers for automatic affinity/PCA calibration and the reserved full source
identity. They do not block a conditional equations-(6)--(8) evaluation after
epsilon and weights have been declared externally:

1. **Calibration selector.** The source permits ADD, SBM, or raw observations
   and does not select among multiple optimal ADD/SBM projections.
2. **Repeated Perron root.** Example 2 displays equal weights for identity
   affinity but supplies no general eigenvector tie rule.
3. **Hospital Table 10, DMU G.** From the integer observations in Table 9,
   equation (19) returns G itself with inpatient output 88.00. Table 10 prints
   the otherwise unchanged projection with inpatient output 88.04. The exact
   printed vector is infeasible as a VRS combination of the Table 9 rows.
   The downstream affinity and score chain is reproducible when Table 10 is
   treated as the published calibration matrix, but this row cannot be
   derived from the printed raw data without an unavailable precision or
   correction record.

No secondary optimization selects among multiple score-optimal
λ/slack/target accounts. This is a reporting limitation rather than a fourth
calibration blocker: the admitted declared result returns one
`solver_selected_primary_optimum` and does not claim unique peers or targets.

Per the project policy, missing source calibration rules are not invented. The
three automatic-calibration items remain `unresolved` and are deferred to the
next version. The M13-C evaluator bypasses none of them: it records that
automatic calibration was not run and binds the external declaration and its
provenance to the result.

## 7. Gate for later automatic-calibration production work

Production work on `static.ebm.input.tone_tsutsui_2010.crs`, `static.ebm`, or
any automatic-calibration constructor may resume only after a later milestone
explicitly decides or sources all three unresolved calibration items. At
minimum it must then add:

1. named calibration-population and projection-tie policies, clearly marked
   as source-defined or package-defined;
2. a failure-closed dominant-eigenpair domain or a documented eigenvector
   tie policy;
3. a resolution of the hospital-G data discrepancy, or an oracle explicitly
   versioned to corrected/full-precision data;
4. independent primal--dual, unit-rescaling, row-order, residual, and
   non-uniqueness tests; and
5. public result language that identifies input increases as source-defined
   input-mix substitution and labels peer/target attributions honestly.

Until then, `deferred_to_next_version` is the controlling disposition for
`static.ebm.input.tone_tsutsui_2010.crs`, automatic affinity/PCA calibration,
and the wider `static.ebm` family. The only production exception is the
separately identified and governed
`static.ebm.input.tone_tsutsui_2010.crs.declared` conditional evaluator.
