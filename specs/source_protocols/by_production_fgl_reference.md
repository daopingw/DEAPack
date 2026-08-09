# By-production FGL source protocol

## Readiness record

| Field | State |
|---|---|
| Public method identity | `environmental.by_production.fgl` |
| Source-qualified runtime profile | `murty_russell_levkoff_2012_eq_4_6_4_8_5_9_5_10` |
| Primary source | first-hand article chapter obtained and equation-checked |
| Published numerical reproduction | not shipped; paper examples remain citations only |
| Independent executable evidence | project-authored case with separate dense component compilers |
| Multi-output evidence | analytical project fixture and certified cutting-plane gap |
| Deferred identities | alternative-weight, input-oriented, coupled, and strong-efficiency variants |

The defining source is S. Murty, R. R. Russell, and S. B. Levkoff (2012),
“On Modeling Pollution-Generating Technologies,” *Journal of Environmental
Economics and Management*,
[DOI 10.1016/j.jeem.2012.02.005](https://doi.org/10.1016/j.jeem.2012.02.005).
The equation audit also used the first-hand chapter in
[Levkoff's University of California dissertation](https://escholarship.org/uc/item/4td2w553).

This is the performance measure proposed after the paper diagnoses the
directional index's weak indication and direction sensitivity. It is not a
display transform of BP-DDF.

## Source-qualified programme

The by-production technology is the intersection of intended-production and
residual-generation subtechnologies with separate intensity vectors. For
desirable output $r$, $\theta_r$ is the share of benchmark service capability
currently realized; for residual $h$, $\gamma_h$ is the share remaining at
the target. The component measures are

$$
E^1_o=\min_{\theta,\lambda}\left\{
\frac1s\sum_r\theta_r:
X\lambda\leq x_o,\ Y\lambda\geq y_o\oslash\theta,
0<\theta\leq\mathbf1,\ \lambda\geq0
\right\},
$$

$$
E^2_o=\min_{\gamma,\mu}\left\{
\frac1q\sum_h\gamma_h:
X^p\mu\geq x_o^p,\ B\mu\leq\gamma\otimes b_o,
0\leq\gamma\leq\mathbf1,\ \mu\geq0
\right\},
$$

and the source baseline is $E_o^{FGL}=\tfrac12(E_o^1+E_o^2)$. Higher values
mean better current performance. The package's displayed complement is not a
distance defined by the source.

For multiple outputs, DEAPack solves the reciprocal objective with certified
tangent under-estimators and releases a result only when the lower/upper gap
meets tolerance. The returned incumbent and its complete component
intensities are separately certified.

## Evidence and boundary

The public project case and independent compiler are documented in
`specs/oracles/by-production-fgl-project-case.md`,
`tests/test_by_production_fgl_source_oracle.py`, and
`tests/test_by_production_fgl.py`. The repository does not contain the
paper's illustrative data or printed numerical results.

Alternative weights, input orientation, coupled intensities, VRS/NIRS/NDRS,
temporal or custom references, material-balance coefficients, inference,
causal claims, and Pareto--Koopmans completion are package extensions or
`deferred_to_next_version`; they do not inherit the source profile.
