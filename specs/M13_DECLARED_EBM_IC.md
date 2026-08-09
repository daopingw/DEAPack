# M13-C admission contract: declared-calibration EBM-I-C

## Decision and identity boundary

This milestone admits one narrowly source-qualified evaluation leaf:

`static.ebm.input.tone_tsutsui_2010.crs.declared`

It evaluates Tone--Tsutsui's input-oriented constant-returns-to-scale EBM
programme in equations (6)--(8) after the analyst has declared the two
parameters that the source says must be supplied before efficiency
measurement. It does not estimate, reproduce, or validate the source's later
affinity/PCA calibration procedure.

The following identities remain deferred and non-executable:

- `static.ebm`, the wider EBM family; and
- `static.ebm.input.tone_tsutsui_2010.crs`, the full source identity that
  includes an internally resolved affinity/PCA calibration chain.

The admitted leaf is therefore a complete conditional evaluator, not a
partial or implicit implementation of automatic calibration.

## Frozen public API

The canonical estimator is `InputOrientedEpsilonBasedDEA`. Construction
requires one immutable `DeclaredEBMCalibration`; there is no default epsilon,
implicit equal weighting, or automatic normalization.

`DeclaredEBMCalibration` contains:

- `epsilon`, a finite scalar in $[0,1]$;
- `input_weights`, an exact name-keyed mapping of finite nonnegative weights
  that is already normalized to sum to one; and
- non-empty `source`, `decision_owner`, `calibration_population`, and
  `validity_period` provenance fields.

The declaration is canonicalized by input name and receives a stable SHA-256
fingerprint binding the parameter values, names, and provenance. Resolution
against data fails closed on missing, extra, or duplicate input names. The
implementation does not silently renormalize relative weights. With one input,
the source calibration identity requires weight one and epsilon zero; any
other declaration is rejected as non-identifying and outside this leaf.

The estimator exposes no orientation, returns-to-scale, reference, or
peer-eligibility option. Its exact domain is:

- one static cross-section;
- the full sample as one self-inclusive reference technology;
- input orientation and CRS;
- strictly positive ordinary inputs and desirable outputs; and
- no undesirable outputs.

Panel data, non-global or external reference populations, undesirable outputs,
VRS/NIRS/NDRS, and other orientations remain separate source tasks.

## Frozen programme and numerical form

For evaluated DMU $o$, declared $\varepsilon\in[0,1]$, and normalized
$w\ge0$, the source programme is

$$
\begin{aligned}
\gamma_o^*=\min_{\theta,\lambda,s^-}\quad
 &\theta-\varepsilon\sum_iw_i\frac{s_i^-}{x_{io}}\\
\text{s.t.}\quad
 &\theta x_o-X\lambda-s^-=0,\\
 &Y\lambda\ge y_o,\qquad \lambda,s^-\ge0,
\end{aligned}
$$

where $\theta$ is mathematically free. Eliminating $s^-$ gives the equivalent
sparse production form

$$
\begin{aligned}
\min_{\lambda,\theta}\quad
 &(1-\varepsilon)\theta
 +\varepsilon\sum_iw_i\frac{(X\lambda)_i}{x_{io}}\\
\text{s.t.}\quad
 &X\lambda\le\theta x_o,\qquad Y\lambda\ge y_o,
 \qquad\lambda\ge0,
\end{aligned}
$$

with a free bound on $\theta$. The implementation must use sparse matrices,
compile the full reference once, perform exactly one primary LP per DMU, and
perform no secondary optimization. Solver rows may be divided by the strictly
positive evaluated quantities, but all released accounts must be reconstructed
and certified in original units.

For $\varepsilon<1$, the positive coefficient on $\theta$ selects the smallest
feasible radial factor for a chosen $\lambda$. At $\varepsilon=1$, the score
does not identify $\theta$. The package therefore applies the zero-solve,
score-preserving endpoint completion

$$
\theta_o=\max_i\frac{(X\lambda)_i}{x_{io}},\qquad
s_o^-=\theta_ox_o-X\lambda,
$$

conditional on the solver-selected primary $\lambda$. This is explicitly
`package_defined_minimum_feasible_theta_given_selected_lambda`, not a source
secondary objective or a uniqueness claim.

No upper bound is imposed on $\theta$. Input targets may exceed observed
inputs: this is the source's input-mix substitution semantics.

## Endpoint contract

- At $\varepsilon=0$, the EBM score equals the input-oriented CCR score under
  the same CRS full-sample technology. Slacks, peers, and targets remain one
  solver-selected EBM optimum; the leaf does not claim CCR phase-two target
  identity.
- $\varepsilon=1$ alone is not an SBM alias. Standard equal-weight input SBM
  additionally fixes $\theta=1$ and $w_i=1/m$, which restores
  $X\lambda\le x_o$. The admitted EBM programme leaves $\theta$ free and may
  select an input-mix target with one input above its observed value.
- Zero input weights are source-admissible. A zero-weight input excess is not
  priced by the non-radial term, so `is_ebm_input_efficient` must not be
  reinterpreted as Pareto--Koopmans efficiency.

## Public result contract

The result uses `DEAResult` and provides stable summary, slack, target,
intensity, component, dual, and diagnostic schemas on success and failure.

- `score` and `efficiency` are $\gamma_o^*$, higher is better; `distance` is
  $1-\gamma_o^*$ on this self-inclusive source profile.
- `is_efficient` and `is_ebm_input_efficient` mean Definition 1 EBM input
  efficiency only.
- `radial_factor` is the source optimum except for the declared package
  endpoint completion at epsilon one.
- Input slacks are $s^-$. Input targets are $X\lambda$ and may move in either
  direction relative to observations.
- Output targets are $Y\lambda\ge y_o$. The derived output surplus
  $Y\lambda-y_o$ is feasible but unscored.
- Peers, targets, slacks, and output surplus are labelled
  `solver_selected_primary_optimum`; uniqueness is not assessed.
- Components close both source identities:
  $\gamma=\theta-\varepsilon\sum_iw_is_i^-/x_{io}$ and
  $\gamma=(1-\varepsilon)\theta+
  \varepsilon\sum_iw_i(X\lambda)_i/x_{io}$.

Metadata records the exact declared calibration and fingerprint,
`calibration_mode="declared"`, `automatic_affinity_pca_run=False`, fixed CRS
and input orientation, the package endpoint-completion policy, target
selection, one compiled reference, and solver-call counts.

Release is fail-closed through separate claim gates. A score is published only
after a solver-neutral LP certificate plus the original-quantity score account.
Targets and slacks additionally require certified input balance, output
feasibility, nonnegativity, and target reconstruction. Thresholded public peer
intensities are then recertified independently against already-certified public
targets; a peer reconstruction failure withholds peers only, while certified
score, targets, and slacks remain available. Source-dual publication has its
own completeness, feasibility, and strong-duality gate and does not control
the independently certified primal targets.

## Required evidence

The implementation must be checked against the production-free source oracle,
without importing a production helper into that oracle. Required tests cover:

1. all three published input-oriented examples, including hospital D's
   $\theta>1$ and doctor/nurse substitution;
2. the $\varepsilon=0$ CCR score identity;
3. a strict-positive counterexample proving that $\varepsilon=1$ with free
   theta is not generally input SBM;
4. fixed-weight monotonicity in epsilon;
5. independent positive input/output unit changes, DMU row order, and input
   column order with exact name-keyed weight alignment;
6. zero weights, the one-input restriction, invalid domains, invalid
   provenance, and invalid normalized weights;
7. primal, score, target, output-surplus, peer, and failure-schema accounts;
   and
8. one compiled sparse reference, one LP per DMU, zero secondary solves, and
   no dense observation-by-observation allocation.

## Deferred automatic calibration boundary

Equations (15)--(26) remain deferred. This milestone does not choose among ADD,
non-oriented SBM, or raw calibration populations; select among multiple
optimal ADD/SBM projections; invent a general repeated-dominant-root Perron
vector rule; or resolve the hospital-G Table 9/Table 10 discrepancy. Automatic
affinity/PCA calibration, output/non-oriented/VRS EBM, and every environmental,
network, dynamic, super-efficiency, or later EBM variant remain non-public.
