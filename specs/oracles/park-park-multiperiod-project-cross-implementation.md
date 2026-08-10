# Park--Park multiperiod project case: independent cross-implementation

**Method ID:** `panel.multiperiod_aggregative.park_park_2009`

**Validation kind:** `cross_implemented`

**Published reproduction:** no

**Production compiler reused:** no

The `multiperiod_trajectory_contrast` panel is project-authored teaching data.
It is not the empirical dataset or a numerical table from Park and Park
(2009).

`tests/test_network_panel_project_independent_oracles.py` builds a dense
source-equation programme directly with `scipy.optimize.linprog`.  For each
organization it creates one independent intensity vector for every period
and one common radial factor across the complete trajectory.  Under VRS it
adds a separate convexity equation in every period; under CRS it adds none.
It compiles both source orientations:

- input: minimize the common $\theta$ subject to
  $X_t\lambda_t\leq\theta x_{ot}$ and
  $Y_t\lambda_t\geq y_{ot}$ for every period; and
- output: maximize the common $\phi$ subject to
  $X_t\lambda_t\leq x_{ot}$ and
  $Y_t\lambda_t\geq\phi y_{ot}$ for every period.

The independent factor is compared with the public API for every project
trajectory under input/output orientation and CRS/VRS.  No DEAPack panel
compiler, scaling routine, solver wrapper, or result reconstruction helper is
used to form the oracle.

This closes the common-factor and period-specific-technology claims as a
cross-implementation.  The existing public tests separately govern phase-two
slack completion, classification, result tables, and failure closure.  This
record does not claim reproduction of a published numerical table or
uniqueness of the phase-two target plan.
