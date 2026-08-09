# Separable undesirable-output SBM: analytical project oracle

**Method ID:** `environmental.sbm.separable_strong`  
**Validation kind:** `analytically_derived`  
**Published reproduction:** no

This certificate uses a project-authored two-organization fixture. It keeps
the defining source citation while excluding all published numerical tables:
Kaoru Tone, *Dealing with Undesirable Outputs in DEA: A Slacks-based Measure
(SBM) Approach* ([repository record](https://doi.org/10.24545/00000955)).

With separable good and bad outputs, the score is

$$
\rho_o=
\frac{1-\frac1m\sum_i s_i^-/x_{io}}
{1+\frac1{s_g+s_b}\left(
\sum_r s_r^g/y_{ro}^g+\sum_r s_r^b/y_{ro}^b
\right)},
$$

subject to

$$
x_o=X\lambda+s^-,\qquad
y_o^g=Y^g\lambda-s^g,\qquad
y_o^b=Y^b\lambda+s^b,
$$

plus the selected returns-to-scale restriction and nonnegativity. The
bad-output equality is a variable-specific strong-disposal account; it is not
a weak-disposal shortcut.

For the project fixture, the reference activity exactly closes the focal
organization's input, desirable-output, and undesirable-output balances. A
hand substitution yields the score and targets asserted in
`tests/test_undesirable_sbm.py::test_undesirable_sbm_fractional_score_and_components`.
The surrounding tests cover dimension weighting, unit invariance, external
reference membership, return-to-scale transformations, panel references,
certification, and failure closure.

The certificate is limited to the stated project fixture and equal-dimension
weighting. It does not reproduce any source table, certify unique peers, or
extend to non-separable blocks, generic weak disposal, or statistical
inference.
