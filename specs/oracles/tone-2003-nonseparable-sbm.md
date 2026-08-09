# Non-separable undesirable-output SBM: project-case oracle

**Method ID:** `environmental.sbm.nonseparable_hybrid.tone_2003`  
**Validation kind:** `analytically_derived`  
**Published reproduction:** no

This certificate checks the public implementation on the project-authored
`environmental_disposability_contrast` case. It does not redistribute or
reproduce a numerical table from the literature. The defining model remains
Kaoru Tone's *Dealing with Undesirable Outputs in DEA: A Slacks-based Measure
(SBM) Approach* ([repository record](https://doi.org/10.24545/00000955)).

## Model account

For evaluated organization $o$, let $x_o$ be inputs, let
$y_o^{Sg},y_o^{Sb}$ be separable good and bad outputs, and let
$y_o^{NSg},y_o^{NSb}$ be the declared non-separable block. Under VRS, the
programme minimizes

$$
\rho_o=
\frac{1-\frac1m\sum_i s_i^-/x_{io}}
{1+\frac1s\left(
\sum_r s_r^{Sg}/y_{ro}^{Sg}+
\sum_r s_r^{Sb}/y_{ro}^{Sb}+
q(1-\alpha)
\right)},
$$

subject to

$$
\begin{aligned}
x_o &= X\lambda+s^-, &
y_o^{Sg} &= Y^{Sg}\lambda-s^{Sg},\\
y_o^{Sb} &= Y^{Sb}\lambda+s^{Sb}, &
\alpha y_o^{NSg} &\leq Y^{NSg}\lambda,\\
\alpha y_o^{NSb} &\geq Y^{NSb}\lambda, &
\mathbf e^\mathsf T\lambda&=1,
\end{aligned}
$$

with nonnegative intensities and separable slacks and with the declared lower
bound on $\alpha$. The source projection for the non-separable block is
$\alpha y_o^{NS}$; the difference from $Y^{NS}\lambda$ is reported as an
unscored reference residual.

## Independent project certificate

The two-organization project case is small enough for a hand account. For the
focal organization, direct substitution gives $\alpha=7/10$, intensity
weights $17/20$ and $3/20$, and score $224/771$. The test independently checks
those values, reconstructs every reported target from the source equations,
and confirms that the remaining non-separable residual is not included in the
fractional objective. It also checks unit invariance, all declared public RTS
policies, aliases, validation failures, and result metadata.

## Claim boundary

The certificate covers only the project-authored, strictly positive,
cross-sectional fixture and the declared separable/non-separable partition.
It validates the source equation, the Charnes--Cooper result account, target
semantics, and unit invariance. It does not claim a published-table
reproduction, unique peers, statistical inference, arbitrary output
partitions, or a general weak-disposal interpretation.
