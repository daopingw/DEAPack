# By-production FGL project-case oracle

**Method ID:** `environmental.by_production.fgl`  
**Validation kind:** independent problem compilation on project-authored data  
**Published numerical payload shipped:** no

This certificate validates the scalar CRS FGL programmes on the
by-production technology of Murty, Russell, and Levkoff (2012). The public
fixture is DEAPack's `by_production_component_bottleneck`; it is not the
paper's illustrative table.

For one desirable output, the independent test solves

$$
\max\ \phi
\quad\text{s.t.}\quad
X\lambda\leq x_o,\quad
-Y\lambda+y_o\phi\leq0,\quad
\lambda\geq0,\quad\phi\geq1,
$$

and sets $E_o^1=1/\phi_o$. It separately solves

$$
\min\ \gamma
\quad\text{s.t.}\quad
-X^p\mu\leq-x_o^p,\quad
B\mu-b_o\gamma\leq0,\quad
\mu\geq0,\quad0\leq\gamma\leq1,
$$

then forms $E_o^{FGL}=(E_o^1+E_o^2)/2$. Separate intensities preserve the
economic distinction between intended production and residual generation.

Executable evidence is in
`tests/test_by_production_fgl_source_oracle.py::test_bp_fgl_matches_independent_compiler_on_project_case`
and `tests/test_by_production_fgl.py`. The tests cover independent component
values, targets, peers, project-case closure, cutting-plane certification,
unit invariance, failure handling, and extension boundaries.

This certificate does not redistribute the paper's observations or printed
results. It does not certify alternative top-level weights, input-oriented
FGL, coupled intensities, VRS/NIRS/NDRS, panel references, causal claims, or
Pareto--Koopmans completion.

Source: S. Murty, R. R. Russell, and S. B. Levkoff, “On Modeling
Pollution-Generating Technologies,” *Journal of Environmental Economics and
Management* (2012),
[DOI 10.1016/j.jeem.2012.02.005](https://doi.org/10.1016/j.jeem.2012.02.005).
