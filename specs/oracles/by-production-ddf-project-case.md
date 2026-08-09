# By-production DDF project-case oracle

**Method ID:** `environmental.by_production.ddf`  
**Validation kind:** independent problem compilation on project-authored data  
**Published numerical payload shipped:** no

This certificate validates the CRS directional-distance programme for the
by-production technology described by Murty, Russell, and Levkoff (2012). The
paper and its equations remain the method authority; the numerical fixture is
the public DEAPack case `by_production_component_bottleneck`, not a copied
paper table.

For an evaluated organization $o$, the independent test compiles

$$
\max\ \beta
\quad\text{s.t.}\quad
X\lambda\leq x_o,\quad
-Y\lambda+g^y\beta\leq-y_o,\quad
\lambda,\beta\geq0,
$$

and, with a separate intensity vector,

$$
\max\ \beta
\quad\text{s.t.}\quad
-X^p\mu\leq-x_o^p,\quad
B\mu+g^b\beta\leq b_o,\quad
\mu,\beta\geq0.
$$

The joint value is independently formed as the minimum of the two component
optima. The oracle imports neither the production compiler nor its LP builder.

Executable evidence is in
`tests/test_by_production_source_oracle.py::test_bp_ddf_matches_independent_compiler_on_project_case`.
It checks component and joint values, targets, peer accounts, certification,
fixed-direction scope, and the boundary separating the source CRS
cross-section from configurable package extensions.

This certificate does not reproduce or redistribute the paper's illustrative
observations or printed results. It also does not certify VRS/NIRS/NDRS,
observation-varying directions, panel references, uniqueness, causal claims,
engineering feasibility, or the distinct FGL measure.

Source: S. Murty, R. R. Russell, and S. B. Levkoff, “On Modeling
Pollution-Generating Technologies,” *Journal of Environmental Economics and
Management* (2012),
[DOI 10.1016/j.jeem.2012.02.005](https://doi.org/10.1016/j.jeem.2012.02.005).
