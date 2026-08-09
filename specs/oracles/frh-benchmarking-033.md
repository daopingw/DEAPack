# Free-replicability hull: project-case oracle

**Method ID:** `static.radial.frh`  
**Validation kind:** `analytically_derived`  
**Published reproduction:** no

This record validates the public FRH implementation with the project-authored
`integer_coordination_hulls` case. It does not redistribute or reproduce the
numerical example from another package. The method boundary remains grounded
in the non-convex production discussion of
[Tulkens (1993)](https://doi.org/10.1007/BF01073473), the free-replicability
treatment of
[Ehrgott and Tind (2009)](https://doi.org/10.1016/j.omega.2008.08.003), and
the independently documented additive-return implementation in
[`Benchmarking`](https://rdrr.io/cran/Benchmarking/man/dea.plot.html).

For an input-oriented assessment, the radial phase is

$$
\min_{\theta,n}\ \theta
\quad\text{such that}\quad
Xn\leq\theta x_o,\quad Yn\geq y_o,\quad
n\in\mathbb Z_+^N.
$$

The output-oriented phase maximizes the corresponding expansion factor under
$Xn\leq x_o$ and $Yn\geq\phi y_o$. Optional slack completion keeps the radial
factor fixed and optimizes ordinary free-disposal residuals. Replication
counts are whole reference modules; they are not rounded continuous
intensities and are not integer-valued input or output observations.

The three-organization project case has hand-enumerable feasible replication
portfolios. `tests/test_frh.py` checks both orientations, the selected integer
portfolios and reciprocal output-score convention, FDH--FRH--CCR nesting,
unit invariance, reference policies, exact certificate diagnostics, and
fail-closed solver behavior.

This certificate covers the project fixture and the stated integer
technology. It does not claim a published numerical reproduction, unique
optimal portfolios, economic divisibility of real organizations, or
statistical inference.
