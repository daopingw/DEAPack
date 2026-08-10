# Network project cases: independent source-equation cross-implementation

**Method IDs:** `network.additive.chen_etal_2009`,
`network.additive.cook_zhu_bi_yang_2010`, and
`network.relational.kao_hwang_2008`

**Validation kind:** `cross_implemented`

**Published reproduction:** no

**Production compiler reused:** no

This record fixes the validation boundary after the historical empirical
fixtures were removed from the distributable project.  The current
`two_stage_public_service` and `open_service_chain` datasets are
project-authored teaching cases.  They do not reproduce the insurer, supply
chain, or other empirical tables in the defining articles.

The independent checks in
`tests/test_network_panel_project_independent_oracles.py` compile the source
multiplier programmes directly with `scipy.optimize.linprog`.  They do not
call DEAPack's network layout, scaling, sparse LP, certificate, or post-solve
account builders.

For the closed two-stage project case, the independent compiler imposes the
two process inequalities

$$
w z_j-v x_j\leq0,
\qquad
u y_j-w z_j\leq0.
$$

The Kao--Hwang account normalizes $v x_o=1$ and maximizes $u y_o$.  The
Chen--Cook--Li--Zhu account normalizes $v x_o+w z_o=1$ and maximizes
$w z_o+u y_o$.  Each independently computed system optimum is compared with
the public API for every project observation.

The Chen projection check separately compiles the Lim--Zhu CRS primal.  With
upstream intensities $\lambda$, downstream intensities $\mu$, and optimum
$\eta_o$, it verifies

$$
X^\top\lambda\leq\eta_o x_o,
\quad
Z^\top\lambda-Z^\top\mu\geq(1-\eta_o)z_o,
\quad
Y^\top\mu\geq y_o.
$$

The independently optimized $\eta_o$ equals the independently compiled
Chen multiplier optimum.  The public split-link projection is then checked
against the same optimal factor and all three quantity inequalities.  This
certifies projection feasibility and optimality without asserting uniqueness
of the upstream or downstream intensity plan.

For the open Cook--Zhu--Bi--Yang case, the independent compiler assigns one
multiplier to each declared economic product, writes a separate
output-minus-input inequality for every process/reference observation,
normalizes the sum of the evaluated process-input accounts, and maximizes the
sum of the evaluated process-output accounts.  Every public system score is
compared with that dense compiler.

These checks establish equation-level cross-implementation on the stated CRS
project cases.  They do not claim published numerical reproduction, empirical
provenance, general-network VRS, unique process attribution, or unique target
selection.
